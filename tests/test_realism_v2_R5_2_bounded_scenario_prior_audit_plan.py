from __future__ import annotations

import copy
import csv
from collections import Counter
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


R5_DIR = rv2.DEFAULT_R5_FULL_GRID_V2_DIR
R5_1_DIR = rv2.DEFAULT_R5_1_INTERPRETATION_DIR


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_R5_2_plan_is_plan_only_and_consumes_R5_1_gate():
    plan = rv2.validate_R5_2_bounded_scenario_prior_audit_plan()
    boundary = plan["authorization_boundary"]

    assert plan["stage"] == "R5_2_bounded_scenario_prior_audit_plan_only"
    assert (
        plan["prior_gate"]
        == "PASS_R5_1_RESULTS_PREPARE_BOUNDED_SCENARIO_PRIOR_AUDIT_PLAN_ONLY"
    )
    assert (
        plan["selected_next_stage_lane"]
        == "bounded_additional_scenario_prior_audit_plan_only"
    )
    assert boundary["bounded_audit_plan_preparation_authorized_by_prior_gate"] is True
    assert boundary["bounded_scenario_prior_audit_execution_authorized"] is False
    assert boundary["R6_plan_preparation_authorized"] is False
    assert boundary["R6_execution_authorized"] is False
    assert boundary["R5_followup_expansion_authorized"] is False
    assert boundary["new_scenario_bundle_authorized"] is False
    assert boundary["new_stochastic_seed_authorized"] is False
    assert boundary["new_solver_case_authorized"] is False
    assert boundary["new_experiment_authorized"] is False
    assert boundary["external_review_required_before_audit_execution"] is True


def test_R5_2_carryforward_preserves_R5_1_warning_signal_without_promotion():
    plan = rv2.validate_R5_2_bounded_scenario_prior_audit_plan()
    carry = plan["R5_1_evidence_carryforward"]
    manifest = _csv_rows(R5_1_DIR / "R5_1_route_role_stability_interpretation_manifest.csv")[0]
    weak = _csv_rows(R5_1_DIR / "R5_1_weak_reference_control_interpretation.csv")[0]
    decision = {
        row["decision_subject"]: row
        for row in _csv_rows(R5_1_DIR / "R5_1_route_role_stability_decision_table.csv")
    }

    assert carry["R5_1_interpretation_run"] is True
    assert carry["R5_case_rows_interpreted"] == 256256
    assert carry["selected_future_recommendation_class"] == (
        "prepare_bounded_additional_scenario_prior_audit_plan_only"
    )
    assert carry["weak_reference_control_exceeds_main_660"] is True
    assert carry["context_routes_exceeding_main_660_mean"] == 20
    assert carry["top_context_warning_route"] == "660_500x1500"
    assert carry["R6_plan_preparation_authorized"] is False
    assert carry["context_route_promotion_authorized"] is False
    assert carry["main_660_redefinition_authorized"] is False

    assert manifest["selected_future_recommendation_class"] == (
        carry["selected_future_recommendation_class"]
    )
    assert weak["weak_reference_exceeds_main_660"] == "True"
    assert decision["context_route_high_score_warnings"][
        "route_promotion_authorized"
    ] == "False"


def test_R5_2_audit_design_is_posthoc_existing_R5_only_and_capped():
    plan = rv2.validate_R5_2_bounded_scenario_prior_audit_plan()
    design = plan["audit_design"]

    assert design["audit_execution_type"] == "posthoc_existing_R5_artifact_audit_only"
    assert design["uses_existing_R5_artifacts_only"] is True
    assert design["deterministic_no_stochastic_seeds"] is True
    assert design["new_case_rows_authorized"] == 0
    assert design["new_scenario_bundle_authorized"] is False
    assert design["new_stochastic_seed_authorized"] is False
    assert design["new_solver_case_authorized"] is False
    assert design["new_experiment_authorized"] is False
    assert design["audit_route_id_count"] == rv2.R5_2_AUDIT_ROUTE_COUNT
    assert design["audit_existing_R5_source_row_cap"] == (
        rv2.R5_2_EXISTING_R5_AUDIT_ROW_CAP
    )
    assert design["audit_existing_R5_source_row_cap"] == 14784
    assert set(design["scenario_bundle_ids"]) == rv2.R5_REQUIRED_SCENARIO_BUNDLE_IDS
    assert design["stochastic_seed_count"] == 0


def test_R5_2_route_set_matches_all_above_main_context_routes_and_controls():
    plan = rv2.validate_R5_2_bounded_scenario_prior_audit_plan()
    route_set = plan["audit_route_set"]
    context_rows = _csv_rows(R5_DIR / "context_route_no_promotion_summary.csv")
    role_rows = {
        row["route_role"]: row
        for row in _csv_rows(R5_DIR / "route_role_stability_full_grid_v2.csv")
    }
    main_mean = float(role_rows["main_660"]["mean_detectability_relative_prior_score"])
    actual_above_main = {
        row["route_id"]
        for row in context_rows
        if float(row["mean_detectability_relative_prior_score"]) > main_mean
    }
    planned_above_main = {
        row["route_id"] for row in route_set["above_main_context_routes"]
    }
    planned_routes = {
        row["route_id"] for rows in route_set.values() for row in rows
    }

    assert planned_above_main == actual_above_main
    assert planned_above_main == rv2.R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS
    assert planned_routes == rv2.R5_2_AUDIT_ROUTE_IDS
    assert len(planned_routes) == 33
    assert all(
        row["route_promotion_authorized"] is False
        for rows in route_set.values()
        for row in rows
    )


def test_R5_2_planned_route_rows_match_R5_summary_counts():
    plan = rv2.validate_R5_2_bounded_scenario_prior_audit_plan()
    planned = {
        row["route_id"]: row["expected_existing_R5_rows"]
        for rows in plan["audit_route_set"].values()
        for row in rows
    }
    counts: Counter[str] = Counter()
    with (R5_DIR / "full_grid_v2_summary.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["route_id"] in planned:
                counts[row["route_id"]] += 1

    assert set(counts) == set(planned)
    assert sum(counts.values()) == rv2.R5_2_EXISTING_R5_AUDIT_ROW_CAP
    assert all(counts[route_id] == expected for route_id, expected in planned.items())


def test_R5_2_required_outputs_stop_gates_and_claim_boundaries_are_complete():
    plan = rv2.validate_R5_2_bounded_scenario_prior_audit_plan()
    claims = plan["claim_boundaries"]

    assert set(plan["required_outputs_if_authorized_after_future_review"]) == (
        rv2.R5_2_REQUIRED_OUTPUTS_IF_AUTHORIZED
    )
    assert "R5_2_context_route_above_main_audit.csv" in (
        plan["required_outputs_if_authorized_after_future_review"]
    )
    assert rv2.R5_2_REQUIRED_STOP_GATES.issubset(set(plan["stop_gates"]))
    assert "new_scenario_bundle_added" in plan["stop_gates"]
    assert "new_stochastic_seed_added" in plan["stop_gates"]
    assert "legacy_calibrated_detector_SNR_output_header_emitted" in plan["stop_gates"]
    assert claims["SNR_claim_level"] == "absolute_blocked"
    assert claims["event_probability_claim_level"] == "absolute_blocked"
    assert claims["p_detect_mapping_claim_level"] == "relative_with_priors"
    assert claims["calibrated_SNR_claim_authorized"] is False
    assert claims["calibrated_event_probability_claim_authorized"] is False
    assert claims["absolute_LOD_claim_authorized"] is False
    assert claims["biological_specificity_claim_authorized"] is False


def test_R5_2_provenance_freeze_matches_current_R5_and_R5_1_artifacts():
    plan = rv2.validate_R5_2_bounded_scenario_prior_audit_plan()
    provenance = plan["provenance_freeze"]
    expected = {
        "R5_1_manifest_checksum": rv2.sha256_file(
            R5_1_DIR / "R5_1_route_role_stability_interpretation_manifest.csv"
        ),
        "R5_1_decision_table_checksum": rv2.sha256_file(
            R5_1_DIR / "R5_1_route_role_stability_decision_table.csv"
        ),
        "R5_1_context_warning_table_checksum": rv2.sha256_file(
            R5_1_DIR / "R5_1_context_route_high_score_warning_table.csv"
        ),
        "R5_1_weak_reference_checksum": rv2.sha256_file(
            R5_1_DIR / "R5_1_weak_reference_control_interpretation.csv"
        ),
        "R5_1_next_stage_options_checksum": rv2.sha256_file(
            R5_1_DIR / "R5_1_next_stage_options_matrix.csv"
        ),
        "R5_1_run_manifest_checksum": rv2.sha256_file(R5_1_DIR / "run_manifest.json"),
        "R5_case_manifest_checksum": rv2.sha256_file(
            R5_DIR / "full_grid_v2_case_manifest.csv"
        ),
        "R5_summary_checksum": rv2.sha256_file(R5_DIR / "full_grid_v2_summary.csv"),
        "R5_context_no_promotion_checksum": rv2.sha256_file(
            R5_DIR / "context_route_no_promotion_summary.csv"
        ),
        "R5_route_role_stability_checksum": rv2.sha256_file(
            R5_DIR / "route_role_stability_full_grid_v2.csv"
        ),
        "R5_scenario_sensitivity_checksum": rv2.sha256_file(
            R5_DIR / "scenario_bundle_sensitivity_summary.csv"
        ),
        "R5_run_manifest_checksum": rv2.sha256_file(R5_DIR / "run_manifest.json"),
    }

    assert set(provenance["required_checksum_fields"]) == (
        rv2.R5_2_REQUIRED_PROVENANCE_FIELDS
    )
    for key, value in expected.items():
        assert provenance[key] == value


@pytest.mark.parametrize(
    ("section", "key", "value", "match"),
    [
        (
            "authorization_boundary",
            "bounded_scenario_prior_audit_execution_authorized",
            True,
            "bounded_scenario_prior_audit_execution_authorized=false",
        ),
        (
            "authorization_boundary",
            "R6_plan_preparation_authorized",
            True,
            "R6_plan_preparation_authorized=false",
        ),
        (
            "authorization_boundary",
            "new_scenario_bundle_authorized",
            True,
            "new_scenario_bundle_authorized=false",
        ),
        (
            "authorization_boundary",
            "context_route_promotion_authorized",
            True,
            "context_route_promotion_authorized=false",
        ),
    ],
)
def test_R5_2_validation_fails_closed_for_forbidden_authority(
    section,
    key,
    value,
    match,
):
    broken = copy.deepcopy(rv2.load_R5_2_bounded_scenario_prior_audit_plan())
    broken[section][key] = value

    with pytest.raises(ValueError, match=match):
        rv2.validate_R5_2_bounded_scenario_prior_audit_plan(broken)


def test_R5_2_validation_fails_closed_for_route_scope_or_stop_gate_drift():
    broken = copy.deepcopy(rv2.load_R5_2_bounded_scenario_prior_audit_plan())
    broken["audit_design"]["audit_existing_R5_source_row_cap"] += 448
    with pytest.raises(ValueError, match="source row cap"):
        rv2.validate_R5_2_bounded_scenario_prior_audit_plan(broken)

    broken = copy.deepcopy(rv2.load_R5_2_bounded_scenario_prior_audit_plan())
    broken["audit_route_set"]["above_main_context_routes"].pop()
    with pytest.raises(ValueError, match="route set mismatch"):
        rv2.validate_R5_2_bounded_scenario_prior_audit_plan(broken)

    for gate in rv2.R5_2_REQUIRED_STOP_GATES:
        broken = copy.deepcopy(rv2.load_R5_2_bounded_scenario_prior_audit_plan())
        broken["stop_gates"] = [
            existing for existing in broken["stop_gates"] if existing != gate
        ]
        with pytest.raises(ValueError, match="stop gates are incomplete"):
            rv2.validate_R5_2_bounded_scenario_prior_audit_plan(broken)
