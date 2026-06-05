from __future__ import annotations

import copy
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.realism_v2_io import read_csv_rows


R5_DIR = rv2.DEFAULT_R5_FULL_GRID_V2_DIR


def _csv_rows(path: Path) -> list[dict[str, str]]:
    return read_csv_rows(path)


def test_R5_1_plan_is_plan_only_and_selects_interpretation_lane():
    plan = rv2.validate_R5_1_route_role_stability_plan()
    boundary = plan["authorization_boundary"]

    assert plan["stage"] == "R5_1_route_role_stability_interpretation_plan_only"
    assert plan["prior_gate"] == "PASS_R5_RESULTS_PREPARE_NEXT_STAGE_PLAN_ONLY"
    assert (
        plan["selected_next_stage_lane"]
        == "R5_1_route_role_stability_interpretation_report_only"
    )
    assert boundary["next_stage_plan_preparation_authorized_by_prior_gate"] is True
    assert boundary["R5_1_interpretation_execution_authorized"] is False
    assert boundary["R6_plan_preparation_authorized"] is False
    assert boundary["R6_execution_authorized"] is False
    assert boundary["R5_followup_expansion_authorized"] is False
    assert boundary["context_route_promotion_authorized"] is False
    assert boundary["main_660_redefinition_authorized"] is False
    assert boundary["external_review_required_before_R5_1_execution"] is True


def test_R5_1_plan_consumes_clean_R5_results_without_authorizing_expansion():
    plan = rv2.validate_R5_1_route_role_stability_plan()
    evidence = plan["R5_evidence_carryforward"]

    assert evidence["accepted_gate"] == "PASS_R5_RESULTS_PREPARE_NEXT_STAGE_PLAN_ONLY"
    assert evidence["R5_full_grid_v2_run"] is True
    assert evidence["R5_case_rows"] == 256256
    assert evidence["v1_source_rows"] == 32032
    assert evidence["route_identity_count"] == 572
    assert evidence["named_scenario_bundle_count"] == 8
    assert evidence["stochastic_seed_count"] == 0
    assert evidence["R5_cap_respected"] is True
    assert evidence["R5_followup_expansion_authorized"] is False
    assert evidence["claim_boundaries_all_rows_blocked"] is True
    assert evidence["legacy_SNR_headers_absent"] is True


def test_R5_1_route_role_targets_match_R5_artifacts_and_do_not_promote():
    plan = rv2.validate_R5_1_route_role_stability_plan()
    targets = plan["route_role_interpretation_targets"]
    role_rows = {
        row["route_role"]: row
        for row in _csv_rows(R5_DIR / "route_role_stability_full_grid_v2.csv")
    }
    context_rows = _csv_rows(R5_DIR / "context_route_no_promotion_summary.csv")

    assert targets["main_660_route_identity_locked"] is True
    assert targets["weak_reference_control_requires_interpretation"] is True
    assert targets["context_route_high_score_warning_requires_interpretation"] is True
    assert targets["context_route_promotion_authorized"] is False
    assert targets["main_660_redefinition_authorized"] is False

    assert float(role_rows["weak_reference_control"]["mean_detectability_relative_prior_score"]) > (
        float(role_rows["main_660"]["mean_detectability_relative_prior_score"])
    )
    top_context = max(
        context_rows,
        key=lambda row: float(row["mean_detectability_relative_prior_score"]),
    )
    assert top_context["route_id"] == "660_500x1500"
    assert top_context["context_route_promotion_authorized"] == "False"
    assert top_context["route_promotion_eligible"] == "False"


def test_R5_1_scope_is_zero_new_case_rows_and_existing_artifacts_only():
    plan = rv2.validate_R5_1_route_role_stability_plan()
    scope = plan["analysis_scope"]

    assert scope["uses_existing_R5_artifacts_only"] is True
    assert scope["new_case_rows_authorized"] == 0
    assert scope["new_scenario_bundle_authorized"] is False
    assert scope["new_stochastic_seed_authorized"] is False
    assert scope["new_solver_case_authorized"] is False
    assert scope["new_experiment_authorized"] is False


def test_R5_1_required_outputs_and_future_recommendations_are_plan_only():
    plan = rv2.validate_R5_1_route_role_stability_plan()
    outputs = set(plan["required_outputs_if_authorized_after_future_review"])
    recommendations = set(plan["allowed_future_recommendation_classes"])

    assert outputs == rv2.R5_1_REQUIRED_OUTPUTS_IF_AUTHORIZED
    assert "R5_1_next_stage_options_matrix.csv" in outputs
    assert "R5_1_route_role_stability_interpretation_report.md" in outputs
    assert recommendations == rv2.R5_1_ALLOWED_NEXT_STAGE_RECOMMENDATIONS
    assert all("execution" not in recommendation for recommendation in recommendations)


def test_R5_1_stop_gates_and_claim_boundaries_are_complete():
    plan = rv2.validate_R5_1_route_role_stability_plan()
    stop_gates = set(plan["stop_gates"])
    claims = plan["claim_boundaries"]

    assert rv2.R5_1_REQUIRED_STOP_GATES.issubset(stop_gates)
    assert "R6_execution_started" in stop_gates
    assert "R5_followup_expansion_started" in stop_gates
    assert "context_route_promotion_attempted" in stop_gates
    assert "legacy_detector_SNR_output_header_emitted" in stop_gates
    assert "legacy_calibrated_detector_SNR_output_header_emitted" in stop_gates
    assert claims["SNR_claim_level"] == "absolute_blocked"
    assert claims["event_probability_claim_level"] == "absolute_blocked"
    assert claims["p_detect_mapping_claim_level"] == "relative_with_priors"
    assert claims["calibrated_SNR_claim_authorized"] is False
    assert claims["calibrated_event_probability_claim_authorized"] is False
    assert claims["absolute_LOD_claim_authorized"] is False
    assert claims["biological_specificity_claim_authorized"] is False


def test_R5_1_provenance_freeze_matches_current_R5_artifacts():
    plan = rv2.validate_R5_1_route_role_stability_plan()
    provenance = plan["provenance_freeze"]
    expected = {
        "R5_case_manifest_checksum": rv2.sha256_file(
            R5_DIR / "full_grid_v2_case_manifest.csv"
        ),
        "R5_summary_checksum": rv2.sha256_file(R5_DIR / "full_grid_v2_summary.csv"),
        "R5_route_role_stability_checksum": rv2.sha256_file(
            R5_DIR / "route_role_stability_full_grid_v2.csv"
        ),
        "R5_main660_summary_checksum": rv2.sha256_file(
            R5_DIR / "main_660_full_grid_v2_stability_summary.csv"
        ),
        "R5_context_no_promotion_checksum": rv2.sha256_file(
            R5_DIR / "context_route_no_promotion_summary.csv"
        ),
        "R5_scenario_sensitivity_checksum": rv2.sha256_file(
            R5_DIR / "scenario_bundle_sensitivity_summary.csv"
        ),
        "R5_cost_estimate_checksum": rv2.sha256_file(R5_DIR / "full_grid_v2_cost_estimate.csv"),
        "R5_run_manifest_checksum": rv2.run_manifest_provenance_checksum(
            R5_DIR / "run_manifest.json"
        ),
    }

    assert set(provenance["required_R5_checksum_fields"]) == (
        rv2.R5_1_REQUIRED_PROVENANCE_FIELDS
    )
    for key, value in expected.items():
        assert provenance[key] == value


@pytest.mark.parametrize(
    ("section", "key", "value", "match"),
    [
        (
            "authorization_boundary",
            "R6_execution_authorized",
            True,
            "R6_execution_authorized=false",
        ),
        (
            "authorization_boundary",
            "context_route_promotion_authorized",
            True,
            "context_route_promotion_authorized=false",
        ),
        (
            "R5_evidence_carryforward",
            "R5_followup_expansion_authorized",
            True,
            "R5_followup_expansion_authorized",
        ),
        (
            "route_role_interpretation_targets",
            "main_660_redefinition_authorized",
            True,
            "main_660 redefinition",
        ),
    ],
)
def test_R5_1_validation_fails_closed_for_forbidden_authority(section, key, value, match):
    broken = copy.deepcopy(rv2.load_R5_1_route_role_stability_plan())
    broken[section][key] = value

    with pytest.raises(ValueError, match=match):
        rv2.validate_R5_1_route_role_stability_plan(broken)


def test_R5_1_missing_required_stop_gate_fails_closed():
    for gate in rv2.R5_1_REQUIRED_STOP_GATES:
        broken = copy.deepcopy(rv2.load_R5_1_route_role_stability_plan())
        broken["stop_gates"] = [
            existing for existing in broken["stop_gates"] if existing != gate
        ]

        with pytest.raises(ValueError, match="stop gates are incomplete"):
            rv2.validate_R5_1_route_role_stability_plan(broken)


def test_R5_1_rejects_new_case_or_experiment_scope():
    broken = copy.deepcopy(rv2.load_R5_1_route_role_stability_plan())
    broken["analysis_scope"]["new_case_rows_authorized"] = 1
    with pytest.raises(ValueError, match="new case rows"):
        rv2.validate_R5_1_route_role_stability_plan(broken)

    broken = copy.deepcopy(rv2.load_R5_1_route_role_stability_plan())
    broken["analysis_scope"]["new_experiment_authorized"] = True
    with pytest.raises(ValueError, match="new_experiment_authorized=false"):
        rv2.validate_R5_1_route_role_stability_plan(broken)
