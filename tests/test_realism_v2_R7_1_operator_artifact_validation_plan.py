import copy
import csv
from pathlib import Path

import pytest

import realism_v2 as rv2


PROJECT_ROOT = Path(__file__).resolve().parents[1]
R7_DIR = rv2.DEFAULT_R7_ROUTE_PRIOR_MECHANISTIC_DECOMPOSITION_DIR


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_R7_1_plan_is_plan_only_after_R7_self_review_gate():
    plan = rv2.validate_R7_1_operator_artifact_validation_plan()

    assert plan["schema_version"] == rv2.R7_1_PLAN_SCHEMA_VERSION
    assert plan["stage"] == "R7_1_operator_artifact_validation_plan_only"
    assert plan["prior_gate"] == (
        "PASS_R7_RESULTS_PREPARE_OPERATOR_ARTIFACT_GAP_REGISTER_PLAN_ONLY"
    )
    assert plan["selected_next_stage_lane"] == (
        "operator_artifact_gap_register_plan_only"
    )

    boundary = plan["authorization_boundary"]
    assert boundary["R7_1_plan_artifact_created"] is True
    for key in (
        "operator_artifact_execution_authorized",
        "experimental_validation_execution_authorized",
        "R8_plan_preparation_authorized",
        "R8_execution_authorized",
        "new_experiment_authorized",
        "new_solver_case_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "score_derived_physical_prior_authorized",
    ):
        assert boundary[key] is False


def test_R7_1_carries_R7_results_without_promoting_or_executing():
    plan = rv2.validate_R7_1_operator_artifact_validation_plan()
    carry = plan["R7_evidence_carryforward"]
    r7_manifest = _csv_rows(R7_DIR / "R7_mechanistic_decomposition_manifest.csv")[0]

    assert carry["R7_route_prior_mechanistic_decomposition_audit_run"] is True
    assert carry["existing_R5_rows_interpreted"] == int(
        r7_manifest["existing_R5_rows_interpreted"]
    )
    assert carry["mechanistic_candidate_count"] == int(
        r7_manifest["mechanistic_candidate_count"]
    )
    assert carry["executable_existing_artifact_mechanistic_candidate_count"] == int(
        r7_manifest["executable_existing_artifact_mechanistic_candidate_count"]
    )
    assert carry["physical_operator_artifact_gap_count"] == int(
        r7_manifest["physical_operator_artifact_gap_count"]
    )
    assert carry["selected_future_recommendation_class"] == (
        "prepare_operator_artifact_gap_register_plan_only"
    )
    for key in (
        "R8_plan_preparation_authorized",
        "R8_execution_authorized",
        "new_experiment_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
    ):
        assert carry[key] is False


def test_R7_1_evidence_modules_are_protocols_not_measurements():
    plan = rv2.validate_R7_1_operator_artifact_validation_plan()
    design = plan["R7_1_plan_design"]
    modules = plan["evidence_module_registry"]

    assert design["plan_execution_type"] == "plan_only_no_operator_or_experiment_execution"
    assert design["uses_existing_R7_outputs_only"] is True
    assert design["defines_evidence_requirements_not_measurements"] is True
    assert design["new_case_rows_authorized"] == 0
    assert set(design["required_evidence_module_ids"]) == (
        rv2.R7_1_REQUIRED_EVIDENCE_MODULE_IDS
    )
    assert set(design["forbidden_actions"]) == rv2.R7_1_FORBIDDEN_ACTIONS

    assert {row["module_id"] for row in modules} == rv2.R7_1_REQUIRED_EVIDENCE_MODULE_IDS
    for row in modules:
        assert row["authorizes_measurement"] is False
        assert row["authorizes_experiment"] is False
        assert row["authorizes_solver_case"] is False
        assert row["authorizes_route_promotion"] is False
        assert row["authorizes_main_660_redefinition"] is False
        assert row["uses_source_v1_relative_score_as_physical_input"] is False
        assert row["allows_route_specific_multiplier"] is False
        assert row["allows_particle_specific_fit"] is False
        assert row["claim_level"] in {"artifact_requirement", "diagnostic_only"}


def test_R7_1_outputs_stop_gates_and_claims_are_fail_closed():
    plan = rv2.validate_R7_1_operator_artifact_validation_plan()

    assert set(plan["required_outputs_if_future_self_review_authorizes"]) == (
        rv2.R7_1_REQUIRED_OUTPUTS_IF_AUTHORIZED
    )
    assert set(plan["stop_gates"]) >= rv2.R7_1_FORBIDDEN_ACTIONS

    claims = plan["claim_boundaries"]
    assert claims["SNR_claim_level"] == "absolute_blocked"
    assert claims["event_probability_claim_level"] == "absolute_blocked"
    assert claims["p_detect_mapping_claim_level"] == "relative_with_priors"
    for key in (
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_claim_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
        "legacy_detector_SNR_output_header_authorized",
        "legacy_calibrated_detector_SNR_output_header_authorized",
    ):
        assert claims[key] is False


def test_R7_1_provenance_freeze_matches_current_R7_artifacts():
    plan = rv2.validate_R7_1_operator_artifact_validation_plan()
    provenance = plan["provenance_freeze"]

    expected = {
        "R7_manifest_checksum": rv2.sha256_file(
            R7_DIR / "R7_mechanistic_decomposition_manifest.csv"
        ),
        "R7_candidate_registry_checksum": rv2.sha256_file(
            R7_DIR / "R7_candidate_mechanistic_prior_registry.csv"
        ),
        "R7_accepted_width_band_checksum": rv2.sha256_file(
            R7_DIR / "R7_accepted_width_prior_band_summary.csv"
        ),
        "R7_width_900_caution_checksum": rv2.sha256_file(
            R7_DIR / "R7_width_quad_900_over_severe_caution_summary.csv"
        ),
        "R7_factor_schema_checksum": rv2.sha256_file(
            R7_DIR / "R7_mechanistic_prior_factor_schema.csv"
        ),
        "R7_particle_residual_top_checksum": rv2.sha256_file(
            R7_DIR / "R7_particle_stratum_residual_top_routes.csv"
        ),
        "R7_particle_residual_by_family_checksum": rv2.sha256_file(
            R7_DIR / "R7_particle_stratum_residual_by_family.csv"
        ),
        "R7_gold_vs_EV_residual_checksum": rv2.sha256_file(
            R7_DIR / "R7_gold_anchor_vs_EV_residual_comparison.csv"
        ),
        "R7_optional_900_checksum": rv2.sha256_file(
            R7_DIR / "R7_optional_900_governance_diagnostic.csv"
        ),
        "R7_non_width_requirement_checksum": rv2.sha256_file(
            R7_DIR / "R7_non_width_prior_input_requirement_summary.csv"
        ),
        "R7_claim_guardrail_checksum": rv2.sha256_file(
            R7_DIR / "R7_claim_boundary_guardrail_summary.csv"
        ),
        "R7_stop_gate_checksum": rv2.sha256_file(R7_DIR / "R7_stop_gate_summary.csv"),
        "R7_next_stage_matrix_checksum": rv2.sha256_file(
            R7_DIR / "R7_next_stage_recommendation_matrix.csv"
        ),
        "R7_run_manifest_checksum": rv2.sha256_file(R7_DIR / "run_manifest.json"),
    }

    assert set(provenance["required_checksum_fields"]) == (
        rv2.R7_1_REQUIRED_PROVENANCE_FIELDS
    )
    for key, value in expected.items():
        assert provenance[key] == value


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("authorization_boundary", "R8_execution_authorized"), True),
        (("R7_1_plan_design", "new_case_rows_authorized"), 1),
        (("claim_boundaries", "calibrated_SNR_claim_authorized"), True),
    ],
)
def test_R7_1_validation_fails_closed_for_forbidden_authority(path, value):
    broken = copy.deepcopy(rv2.load_R7_1_operator_artifact_validation_plan())
    broken[path[0]][path[1]] = value
    with pytest.raises(ValueError):
        rv2.validate_R7_1_operator_artifact_validation_plan(broken)


def test_R7_1_validation_fails_closed_for_missing_module_or_fit_drift():
    broken = copy.deepcopy(rv2.load_R7_1_operator_artifact_validation_plan())
    broken["evidence_module_registry"].pop()
    with pytest.raises(ValueError):
        rv2.validate_R7_1_operator_artifact_validation_plan(broken)

    broken = copy.deepcopy(rv2.load_R7_1_operator_artifact_validation_plan())
    broken["evidence_module_registry"][0][
        "uses_source_v1_relative_score_as_physical_input"
    ] = True
    with pytest.raises(ValueError):
        rv2.validate_R7_1_operator_artifact_validation_plan(broken)

    broken = copy.deepcopy(rv2.load_R7_1_operator_artifact_validation_plan())
    broken["R7_1_plan_design"]["forbidden_actions"].remove("route_promotion")
    with pytest.raises(ValueError):
        rv2.validate_R7_1_operator_artifact_validation_plan(broken)
