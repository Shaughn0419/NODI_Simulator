import copy
import csv
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


R7_1_DIR = rv2.DEFAULT_R7_1_OPERATOR_ARTIFACT_VALIDATION_DIR


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_R7_2_plan_is_plan_only_after_R7_1_gate():
    plan = rv2.validate_R7_2_operator_artifact_gap_register_plan()

    assert plan["schema_version"] == rv2.R7_2_PLAN_SCHEMA_VERSION
    assert plan["stage"] == "R7_2_operator_artifact_gap_register_plan_only"
    assert plan["prior_gate"] == (
        "PASS_R7_1_RESULTS_PREPARE_OPERATOR_ARTIFACT_GAP_REGISTER_ONLY"
    )
    assert plan["selected_next_stage_lane"] == "operator_artifact_gap_register_plan_only"

    boundary = plan["authorization_boundary"]
    assert boundary["R7_2_plan_artifact_created"] is True
    for key in (
        "operator_artifact_acquisition_authorized",
        "bench_measurement_authorized",
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


def test_R7_2_carries_R7_1_protocol_result_without_acquisition():
    plan = rv2.validate_R7_2_operator_artifact_gap_register_plan()
    carry = plan["R7_1_evidence_carryforward"]
    r7_1_manifest = _csv_rows(
        R7_1_DIR / "R7_1_operator_artifact_validation_manifest.csv"
    )[0]

    assert carry["R7_1_operator_artifact_validation_protocol_generation_run"] is True
    assert carry["generation_type"] == "protocol_artifact_requirements_only_no_measurement"
    assert carry["evidence_module_count"] == int(r7_1_manifest["evidence_module_count"])
    assert carry["required_artifact_field_count"] == int(
        r7_1_manifest["required_artifact_field_count"]
    )
    assert carry["selected_future_recommendation_class"] == (
        "prepare_operator_artifact_gap_register_plan_only"
    )
    for key in (
        "operator_artifact_acquisition_started",
        "experimental_validation_started",
        "R8_plan_preparation_authorized",
        "R8_execution_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
    ):
        assert carry[key] is False


def test_R7_2_artifact_registry_maps_protocols_and_remains_not_started():
    plan = rv2.validate_R7_2_operator_artifact_gap_register_plan()
    design = plan["R7_2_plan_design"]
    registry = plan["artifact_gap_registry"]

    assert design["plan_execution_type"] == "plan_only_artifact_gap_register_no_acquisition"
    assert design["uses_existing_R7_1_protocol_outputs_only"] is True
    assert design["defines_artifact_gap_register_not_acquisition"] is True
    assert design["artifact_id_count"] == len(rv2.R7_2_REQUIRED_ARTIFACT_IDS)
    assert design["required_artifact_field_count"] == 30
    assert design["new_case_rows_authorized"] == 0
    assert set(design["artifact_ids"]) == rv2.R7_2_REQUIRED_ARTIFACT_IDS
    assert set(design["forbidden_actions"]) == rv2.R7_2_FORBIDDEN_ACTIONS

    assert {row["artifact_id"] for row in registry} == rv2.R7_2_REQUIRED_ARTIFACT_IDS
    assert {row["source_protocol_module_id"] for row in registry} == (
        rv2.R7_1_REQUIRED_EVIDENCE_MODULE_IDS
    )
    assert sum(row["required_field_count"] for row in registry) == 30
    for row in registry:
        assert row["gap_status"] == "registered_no_acquisition"
        assert row["gap_resolution_authorized"] is False
        assert row["bench_measurement_authorized"] is False
        assert row["experiment_authorized"] is False
        assert row["solver_case_authorized"] is False
        assert row["route_promotion_authorized"] is False
        assert row["main_660_redefinition_authorized"] is False
        assert row["uses_source_v1_relative_score_as_physical_input"] is False
        assert row["allows_route_specific_multiplier"] is False
        assert row["allows_particle_specific_fit"] is False
        assert row["claim_level"] in {"artifact_gap_register", "diagnostic_only"}


def test_R7_2_outputs_stop_gates_and_claims_are_fail_closed():
    plan = rv2.validate_R7_2_operator_artifact_gap_register_plan()

    assert set(plan["required_outputs_if_future_self_review_authorizes"]) == (
        rv2.R7_2_REQUIRED_OUTPUTS_IF_AUTHORIZED
    )
    assert set(plan["stop_gates"]) >= rv2.R7_2_FORBIDDEN_ACTIONS

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


def test_R7_2_provenance_freeze_matches_current_R7_1_artifacts():
    plan = rv2.validate_R7_2_operator_artifact_gap_register_plan()
    provenance = plan["provenance_freeze"]

    expected = {
        "R7_1_manifest_checksum": rv2.sha256_file(
            R7_1_DIR / "R7_1_operator_artifact_validation_manifest.csv"
        ),
        "R7_1_reference_protocol_checksum": rv2.sha256_file(
            R7_1_DIR / "R7_1_reference_operating_band_artifact_protocol.csv"
        ),
        "R7_1_BFP_protocol_checksum": rv2.sha256_file(
            R7_1_DIR / "R7_1_BFP_slit_ROI_alignment_operator_artifact_protocol.csv"
        ),
        "R7_1_fabrication_protocol_checksum": rv2.sha256_file(
            R7_1_DIR / "R7_1_fabrication_metrology_margin_artifact_protocol.csv"
        ),
        "R7_1_wall_transport_protocol_checksum": rv2.sha256_file(
            R7_1_DIR / "R7_1_wall_PEG_transport_proxy_validation_protocol.csv"
        ),
        "R7_1_particle_residual_protocol_checksum": rv2.sha256_file(
            R7_1_DIR / "R7_1_particle_stratum_residual_validation_protocol.csv"
        ),
        "R7_1_optional_900_protocol_checksum": rv2.sha256_file(
            R7_1_DIR / "R7_1_optional_900_governance_protocol.csv"
        ),
        "R7_1_claim_guardrail_checksum": rv2.sha256_file(
            R7_1_DIR / "R7_1_claim_boundary_guardrail_summary.csv"
        ),
        "R7_1_stop_gate_checksum": rv2.sha256_file(
            R7_1_DIR / "R7_1_stop_gate_summary.csv"
        ),
        "R7_1_next_stage_matrix_checksum": rv2.sha256_file(
            R7_1_DIR / "R7_1_next_stage_recommendation_matrix.csv"
        ),
        "R7_1_run_manifest_checksum": rv2.run_manifest_provenance_checksum(
            R7_1_DIR / "run_manifest.json"
        ),
    }

    assert set(provenance["required_checksum_fields"]) == (
        rv2.R7_2_REQUIRED_PROVENANCE_FIELDS
    )
    for key, value in expected.items():
        assert provenance[key] == value


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("authorization_boundary", "operator_artifact_acquisition_authorized"), True),
        (("authorization_boundary", "R8_execution_authorized"), True),
        (("R7_2_plan_design", "new_case_rows_authorized"), 1),
        (("claim_boundaries", "calibrated_event_probability_claim_authorized"), True),
    ],
)
def test_R7_2_validation_fails_closed_for_forbidden_authority(path, value):
    broken = copy.deepcopy(rv2.load_R7_2_operator_artifact_gap_register_plan())
    broken[path[0]][path[1]] = value
    with pytest.raises(ValueError):
        rv2.validate_R7_2_operator_artifact_gap_register_plan(broken)


def test_R7_2_validation_fails_closed_for_artifact_or_fit_drift():
    broken = copy.deepcopy(rv2.load_R7_2_operator_artifact_gap_register_plan())
    broken["artifact_gap_registry"].pop()
    with pytest.raises(ValueError):
        rv2.validate_R7_2_operator_artifact_gap_register_plan(broken)

    broken = copy.deepcopy(rv2.load_R7_2_operator_artifact_gap_register_plan())
    broken["artifact_gap_registry"][0]["gap_resolution_authorized"] = True
    with pytest.raises(ValueError):
        rv2.validate_R7_2_operator_artifact_gap_register_plan(broken)

    broken = copy.deepcopy(rv2.load_R7_2_operator_artifact_gap_register_plan())
    broken["artifact_gap_registry"][0][
        "uses_source_v1_relative_score_as_physical_input"
    ] = True
    with pytest.raises(ValueError):
        rv2.validate_R7_2_operator_artifact_gap_register_plan(broken)

    broken = copy.deepcopy(rv2.load_R7_2_operator_artifact_gap_register_plan())
    broken["R7_2_plan_design"]["forbidden_actions"].remove("route_promotion")
    with pytest.raises(ValueError):
        rv2.validate_R7_2_operator_artifact_gap_register_plan(broken)
