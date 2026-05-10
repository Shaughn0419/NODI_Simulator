from __future__ import annotations

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.review_package import claim_text_passes, load_forbidden_claims_lexicon

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


CONTRACT_PATH = "configs/realism_v2/full_wave_green_tensor_diagnostic_contract.yaml"
REPORT_PATH = "reports/93_EV_NODI_P1_full_wave_green_tensor_diagnostic_contract.md"


def _contract() -> dict:
    return rv2.load_json_yaml("full_wave_green_tensor_diagnostic_contract.yaml")


def test_full_wave_contract_is_contract_only_and_preserves_p0() -> None:
    contract = _contract()

    assert (
        contract["schema_version"]
        == "ev_nodi_p1_full_wave_green_tensor_diagnostic_contract_v1"
    )
    assert contract["stage"] == "P1_full_wave_green_tensor_diagnostic_contract_only"
    assert contract["lane_id"] == "full_wave_green_tensor_physical_ceiling_diagnostic"
    assert contract["calibrated_claim_allowed"] is False
    assert contract["p0_release_conclusion_changed"] is False
    assert contract["physical_ceiling_role"] == "surrogate_risk_reduction_only"

    authority = contract["execution_authority"]
    assert authority["contract_artifact_created"] is True
    for key in (
        "solver_execution_authorized",
        "new_full_wave_case_generation_authorized",
        "new_green_tensor_mesh_authorized",
        "measured_data_ingest_authorized",
        "v1_event_count_expansion_authorized",
        "route_promotion_authorized",
        "p0_release_reinterpretation_authorized",
        "main_660_redefinition_authorized",
        "optional_660_W900_D1400_redefines_main_660",
    ):
        assert authority[key] is False


def test_full_wave_contract_claim_boundary_blocks_calibration_and_absolute_claims() -> None:
    claims = _contract()["claim_boundary"]

    for key in (
        "calibrated_snr_claim_allowed",
        "absolute_lod_claim_allowed",
        "true_ev_concentration_claim_allowed",
        "biological_specificity_claim_allowed",
        "detector_voltage_prediction_claim_allowed",
        "absolute_event_probability_claim_allowed",
    ):
        assert claims[key] is False
    assert claims["allowed_claim_level"] == "relative_candidate_audit_diagnostic_only"
    assert claims["allowed_interpretation"] == (
        "green_tensor_ceiling_may_flag_surrogate_fragility_only"
    )


def test_full_wave_contract_inputs_are_p0_relative_audit_sources_only() -> None:
    contract = _contract()
    sources = contract["input_contract"]["required_sources"]

    assert {source["path"] for source in sources} == {
        "results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv",
        "results/post_v2_mandatory_audit/top_candidate_pairwise_rank_inversion.csv",
        "results/post_v2_mandatory_audit/bfp_roi_operator_summary.csv",
    }
    assert "raw_arbitrary_unit_magnitude_as_final_gate" in contract["input_contract"][
        "forbidden_inputs"
    ]
    assert contract["input_contract"][
        "future_optional_sources_require_separate_authorization"
    ] == [
        "bounded_green_tensor_solver_config",
        "bounded_green_tensor_mesh_manifest",
        "bounded_green_tensor_operator_export",
    ]


def test_full_wave_contract_output_schema_is_fail_closed() -> None:
    output = _contract()["output_schema"]

    assert output["planned_output_path"] == (
        "results/post_v2_physical_ceiling/full_wave_green_tensor_diagnostic.csv"
    )
    assert output["artifact_status"] == "generated_no_solver_rank_diagnostic"
    assert set(output["required_false_columns"]) == {
        "raw_magnitude_final_gate_allowed",
        "calibrated_claim_allowed",
        "p0_release_conclusion_changed",
    }
    assert output["required_role_column_value"] == "surrogate_risk_reduction_only"
    assert set(output["required_false_columns"]).issubset(output["required_columns"])
    assert "green_tensor_pairwise_inversion_flag" in output["required_columns"]


def test_full_wave_contract_gate_policy_uses_rank_not_raw_magnitude() -> None:
    contract = _contract()
    gate = contract["gate_policy"]

    assert gate["raw_arbitrary_unit_magnitude_final_gate_allowed"] is False
    assert gate["raw_complex_field_proxy_role"] == "diagnostic_trace_only"
    assert gate["decision_authority"] == "diagnostic_flag_only_no_route_promotion"
    assert set(gate["primary_gate_metrics"]) == {
        "green_tensor_rank_percentile_in_stratum",
        "green_tensor_vs_v1_rank_percentile_delta",
        "green_tensor_pairwise_inversion_flag",
    }


def test_full_wave_contract_preserves_jacobian_layering() -> None:
    jacobian = _contract()["jacobian_layering"]

    assert jacobian["v1_bfp_to_angle_jacobian_applied"] is False
    assert jacobian["audit_bfp_jacobian_applied"] is True
    assert jacobian["green_tensor_contract_must_not_rewrite_v1_jacobian_flag"] is True
    assert jacobian["green_tensor_contract_may_reference_audit_jacobian_provenance"] is True


def test_full_wave_contract_and_report_claim_language_pass() -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))
    contract_text = root_path(CONTRACT_PATH).read_text(encoding="utf-8")
    report_text = root_path(REPORT_PATH).read_text(encoding="utf-8")

    assert claim_text_passes(contract_text, lexicon)
    assert claim_text_passes(report_text, lexicon)
    assert "no-solver rank diagnostic; no solver execution" in report_text
