from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


def _headers(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return set(next(csv.reader(handle)))


def test_R5_plan_is_plan_only_and_requires_future_review():
    plan = rv2.validate_R5_full_grid_v2_plan()
    boundary = plan["authorization_boundary"]

    assert plan["stage"] == "R5_full_grid_v2_plan_only"
    assert plan["prior_gate"] == "PASS_R4_2_RESULTS_PREPARE_R5_PLAN_ONLY"
    assert boundary["R5_plan_preparation_authorized_by_prior_gate"] is True
    assert boundary["R5_full_grid_v2_execution_authorized"] is False
    assert boundary["R5_full_grid_v2_run"] is False
    assert boundary["external_review_required_before_R5_execution"] is True


def test_R5_plan_consumes_R4_2_pass_without_promoting_coarse_screen():
    plan = rv2.validate_R5_full_grid_v2_plan()
    evidence = plan["R4_2_evidence_carryforward"]

    assert evidence["accepted_gate"] == "PASS_R4_2_RESULTS_PREPARE_R5_PLAN_ONLY"
    assert evidence["fine_confirm_main660_fraction"] == 1.0
    assert evidence["fine_confirm_sign_reliable_subset_fraction"] == 1.0
    assert evidence["review_refined_main660_fraction"] == 1.0
    assert evidence["fine_confirm_agrees_with_review_refined"] == 1.0
    assert evidence["R4_2_gate_met"] is True
    assert evidence["coarse_screen_role"] == "screening_only_warning"
    assert evidence["coarse_screen_can_confirm_or_demote_routes"] is False


def test_R5_source_inventory_uses_v1_read_only_full_grid_identity():
    plan = rv2.validate_R5_full_grid_v2_plan()
    source = plan["source_inventory"]
    source_path = rv2.PROJECT_ROOT / source["v1_source_summary_path"]

    assert source["v1_source_row_count"] == rv2.R5_V1_SOURCE_ROW_COUNT == 32032
    assert source["v1_route_identity_count"] == rv2.R5_V1_SOURCE_ROUTE_COUNT == 572
    assert source["v1_particle_name_count"] == rv2.R5_V1_SOURCE_PARTICLE_NAME_COUNT == 56
    assert source["v1_events_per_case_source_metadata"] == 10000
    assert source["v1_full_grid_overwrite_allowed"] is False
    assert source["v1_source_is_read_only_inventory"] is True
    assert source["legacy_detector_SNR_output_header_present"] is False
    assert source["legacy_calibrated_detector_SNR_output_header_present"] is False
    if source_path.exists():
        assert "detector_SNR" not in _headers(source_path)
        assert "calibrated_detector_SNR" not in _headers(source_path)


def test_R5_cost_cap_is_named_bundle_only_and_fails_closed_for_expansion():
    plan = rv2.validate_R5_full_grid_v2_plan()
    cost = rv2.estimate_R5_full_grid_v2_plan_cost()

    assert cost["case_row_count"] == 32032 * 8 == 256256
    assert cost["under_R5_review_cap"] is True
    assert cost["R5_execution_authorized_by_this_plan"] is False
    assert plan["cost_cap"]["planned_case_rows"] == 256256
    assert plan["cost_cap"]["max_R5_full_grid_v2_case_rows_before_review"] == 256256
    assert rv2.estimate_R5_full_grid_v2_plan_cost(n_named_scenario_bundles=9)[
        "under_R5_review_cap"
    ] is False
    assert rv2.estimate_R5_full_grid_v2_plan_cost(n_stochastic_seeds=3)[
        "under_R5_review_cap"
    ] is False


def test_R5_scenario_policy_blocks_cartesian_and_seed_expansion():
    plan = rv2.validate_R5_full_grid_v2_plan()
    scenario_policy = plan["scenario_policy"]

    assert set(scenario_policy["named_scenario_bundle_ids"]) == (
        rv2.R5_REQUIRED_SCENARIO_BUNDLE_IDS
    )
    assert scenario_policy["named_scenario_bundle_count"] == 8
    assert scenario_policy["cartesian_uncertainty_expansion_authorized"] is False
    assert scenario_policy["stochastic_seed_expansion_authorized"] is False
    assert scenario_policy["stochastic_seeds"] == []
    assert scenario_policy["relative_prior_scoring_only"] is True


def test_R5_route_governance_keeps_main_660_locked_and_blocks_promotion():
    plan = rv2.validate_R5_full_grid_v2_plan()
    governance = plan["route_governance"]
    main_routes = {
        (row["wavelength_nm"], row["width_nm"], row["depth_nm"])
        for row in governance["locked_main_660_routes"]
    }

    assert main_routes == rv2.R5_MAIN_660_LOCKED_ROUTES
    assert governance["main_660_route_role_locked"] is True
    assert governance["context_routes_can_be_promoted"] is False
    assert governance["optional_660_900x1400_can_redefine_main_660"] is False
    assert governance["selected_annulus_replaces_all_crossing_ranking"] is False
    assert governance["route_specific_manual_sign_flips_allowed"] is False
    assert governance["coarse_screen_ranking_role"] == "warning_only_not_rank_gate"


def test_R5_required_outputs_are_future_only_and_guarded():
    plan = rv2.validate_R5_full_grid_v2_plan()
    outputs = set(plan["required_outputs_if_executed_after_future_review"])
    future_dir = rv2.PROJECT_ROOT / plan["future_output_directory_if_authorized"]

    assert outputs == rv2.R5_REQUIRED_OUTPUTS_IF_EXECUTED_AFTER_REVIEW
    assert "full_grid_v2_summary.csv" in outputs
    assert "context_route_no_promotion_summary.csv" in outputs
    assert "R4_2_validation_grade_carryforward_summary.csv" in outputs
    assert "coarse_screen_warning_carryforward_summary.csv" in outputs
    assert plan["plan_only_no_R5_result_directory_created_by_this_bundle"] is True
    if future_dir.exists():
        manifest = json.loads((future_dir / "run_manifest.json").read_text(encoding="utf-8"))
        assert (
            manifest["R5_full_grid_v2_execution_authorization"]
            == "PASS_TO_R5_FULL_GRID_V2_EXECUTION_ONLY"
        )
        assert manifest["R5_followup_expansion_authorized"] is False


def test_R5_stop_gates_and_claim_boundaries_are_complete():
    plan = rv2.validate_R5_full_grid_v2_plan()
    stop_gates = set(plan["stop_gates"])
    claims = plan["claim_boundaries"]

    assert rv2.R5_REQUIRED_STOP_GATES.issubset(stop_gates)
    assert "legacy_detector_SNR_output_header_emitted" in stop_gates
    assert "legacy_calibrated_detector_SNR_output_header_emitted" in stop_gates
    assert "route_specific_manual_sign_flip_attempted" in stop_gates
    assert "optional_660_900x1400_redefines_main_660" in stop_gates
    assert claims["SNR_claim_level"] == "absolute_blocked"
    assert claims["event_probability_claim_level"] == "absolute_blocked"
    assert claims["p_detect_mapping_claim_level"] == "relative_with_priors"
    assert claims["calibrated_SNR_claim_authorized"] is False
    assert claims["calibrated_event_probability_claim_authorized"] is False
    assert claims["absolute_LOD_claim_authorized"] is False
    assert claims["biological_specificity_claim_authorized"] is False


def test_R5_provenance_freeze_has_source_checksums_and_future_plan_checksum_requirements():
    plan = rv2.validate_R5_full_grid_v2_plan()
    provenance = plan["provenance_freeze"]

    assert set(provenance["required_checksum_fields"]) == (
        rv2.R5_REQUIRED_SOURCE_CHECKSUM_FIELDS
    )
    assert set(provenance["future_execution_manifest_required_checksum_fields"]) == (
        rv2.R5_REQUIRED_FUTURE_PLAN_CHECKSUM_FIELDS
    )
    for field in rv2.R5_REQUIRED_SOURCE_CHECKSUM_FIELDS:
        assert len(provenance[field]) == 64


def test_R5_manifest_expectations_keep_prior_run_flags_clean():
    plan = rv2.validate_R5_full_grid_v2_plan()
    manifest = plan["manifest_expectations"]

    assert manifest["R4_2_main660_nearwall_mesh_adjudication_run"] is True
    assert manifest["R5_plan_preparation_started"] is False
    assert manifest["R5_full_grid_v2_run"] is False
    assert manifest["v1_full_grid_overwritten"] is False
    assert manifest["Tsuyama_paper_fit_continued"] is False
    assert manifest["selected_annulus_bounds_changed"] is False
    assert manifest["context_route_promotion_authorized"] is False
    assert manifest["main_660_redefinition_authorized"] is False
    assert manifest["route_specific_manual_sign_flips_authorized"] is False
    assert manifest["calibrated_SNR_claim_emitted"] is False


@pytest.mark.parametrize(
    ("section", "key", "value", "match"),
    [
        (
            "authorization_boundary",
            "R5_full_grid_v2_execution_authorized",
            True,
            "R5_full_grid_v2_execution_authorized=false",
        ),
        (
            "authorization_boundary",
            "context_route_promotion_authorized",
            True,
            "context_route_promotion_authorized=false",
        ),
        (
            "authorization_boundary",
            "route_specific_manual_sign_flips_authorized",
            True,
            "route_specific_manual_sign_flips_authorized=false",
        ),
        (
            "R4_2_evidence_carryforward",
            "coarse_screen_can_confirm_or_demote_routes",
            True,
            "coarse_screen decision-grade",
        ),
    ],
)
def test_R5_validation_fails_closed_for_boundary_and_evidence(section, key, value, match):
    broken = copy.deepcopy(rv2.load_R5_full_grid_v2_plan())
    broken[section][key] = value

    with pytest.raises(ValueError, match=match):
        rv2.validate_R5_full_grid_v2_plan(broken)


def test_R5_validation_fails_if_seed_expansion_or_extra_scenarios_are_added():
    broken = copy.deepcopy(rv2.load_R5_full_grid_v2_plan())
    broken["scenario_policy"]["stochastic_seeds"] = [42, 43, 44]
    with pytest.raises(ValueError, match="stochastic seeds"):
        rv2.validate_R5_full_grid_v2_plan(broken)

    broken = copy.deepcopy(rv2.load_R5_full_grid_v2_plan())
    broken["scenario_policy"]["named_scenario_bundle_ids"].append("unreviewed_new_bundle")
    broken["scenario_policy"]["named_scenario_bundle_count"] = 9
    broken["cost_cap"]["planned_case_rows"] = 288288
    broken["cost_cap"]["max_R5_full_grid_v2_case_rows_before_review"] = 288288
    with pytest.raises(ValueError, match="scenario bundle panel mismatch"):
        rv2.validate_R5_full_grid_v2_plan(broken)


def test_R5_missing_required_stop_gate_fails_closed():
    for gate in rv2.R5_REQUIRED_STOP_GATES:
        broken = copy.deepcopy(rv2.load_R5_full_grid_v2_plan())
        broken["stop_gates"] = [
            existing for existing in broken["stop_gates"] if existing != gate
        ]

        with pytest.raises(ValueError, match="stop gates are incomplete"):
            rv2.validate_R5_full_grid_v2_plan(broken)
