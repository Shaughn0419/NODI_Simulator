from __future__ import annotations

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.review_package import claim_text_passes, load_forbidden_claims_lexicon

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


CONTRACT_PATH = "configs/realism_v2/roughness_leakage_diagnostic_contract.yaml"
REPORT_PATH = "reports/95_EV_NODI_P1_roughness_leakage_diagnostic_contract.md"


def _contract() -> dict:
    return rv2.load_json_yaml("roughness_leakage_diagnostic_contract.yaml")


def test_roughness_leakage_contract_is_contract_only_and_preserves_p0() -> None:
    contract = _contract()

    assert (
        contract["schema_version"]
        == "ev_nodi_p1_roughness_leakage_diagnostic_contract_v1"
    )
    assert contract["stage"] == "P1_roughness_leakage_diagnostic_contract_only"
    assert contract["lane_id"] == "roughness_leakage_diagnostic"
    assert contract["calibrated_claim_allowed"] is False
    assert contract["p0_release_conclusion_changed"] is False
    assert contract["physical_ceiling_role"] == "surrogate_risk_reduction_only"

    authority = contract["execution_authority"]
    assert authority["contract_artifact_created"] is True
    for key in (
        "roughness_simulation_authorized",
        "leakage_simulation_authorized",
        "new_roughness_case_generation_authorized",
        "new_leakage_case_generation_authorized",
        "measured_data_ingest_authorized",
        "blank_trace_ingest_authorized",
        "v1_event_count_expansion_authorized",
        "route_promotion_authorized",
        "p0_release_reinterpretation_authorized",
        "main_660_redefinition_authorized",
        "optional_660_W900_D1400_redefines_main_660",
    ):
        assert authority[key] is False


def test_roughness_leakage_contract_claim_boundary_blocks_blank_safety_and_calibration() -> None:
    claims = _contract()["claim_boundary"]

    for key in (
        "calibrated_snr_claim_allowed",
        "absolute_lod_claim_allowed",
        "true_ev_concentration_claim_allowed",
        "biological_specificity_claim_allowed",
        "detector_voltage_prediction_claim_allowed",
        "absolute_event_probability_claim_allowed",
        "measured_blank_safety_claim_allowed",
    ):
        assert claims[key] is False
    assert claims["allowed_claim_level"] == "relative_candidate_audit_diagnostic_only"
    assert claims["allowed_interpretation"] == (
        "roughness_leakage_ceiling_may_flag_surrogate_fragility_only"
    )
    assert "roughness_or_leakage_response_as_blank_safety" in claims[
        "forbidden_interpretations"
    ]


def test_roughness_leakage_contract_inputs_are_p0_and_governance_sources_only() -> None:
    contract = _contract()
    sources = contract["input_contract"]["required_sources"]

    assert {source["path"] for source in sources} == {
        "results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv",
        "results/post_v2_mandatory_audit/top_candidate_pairwise_rank_inversion.csv",
        "configs/realism_v2/r7_2_operator_artifact_gap_register_plan.yaml",
    }
    assert "raw_leakage_amplitude_as_final_gate" in contract["input_contract"][
        "forbidden_inputs"
    ]
    assert contract["input_contract"][
        "future_optional_sources_require_separate_authorization"
    ] == [
        "bounded_fabrication_roughness_manifest",
        "bounded_leakage_perturbation_manifest",
        "bounded_wall_or_bfp_alignment_operator_export",
    ]


def test_roughness_leakage_contract_output_schema_is_fail_closed() -> None:
    output = _contract()["output_schema"]

    assert output["planned_output_path"] == (
        "results/post_v2_physical_ceiling/roughness_leakage_diagnostic.csv"
    )
    assert output["artifact_status"] == "generated_no_solver_rank_diagnostic"
    assert set(output["required_false_columns"]) == {
        "raw_magnitude_final_gate_allowed",
        "measured_blank_safety_claim_allowed",
        "calibrated_claim_allowed",
        "p0_release_conclusion_changed",
    }
    assert output["required_role_column_value"] == "surrogate_risk_reduction_only"
    assert set(output["required_false_columns"]).issubset(output["required_columns"])
    assert "roughness_leakage_pairwise_inversion_flag" in output["required_columns"]
    assert "raw_leakage_proxy_diagnostic_only" in output["required_columns"]


def test_roughness_leakage_contract_gate_policy_uses_rank_not_raw_magnitude() -> None:
    gate = _contract()["gate_policy"]

    assert gate["raw_arbitrary_unit_magnitude_final_gate_allowed"] is False
    assert gate["raw_leakage_proxy_role"] == "diagnostic_trace_only"
    assert gate["decision_authority"] == "diagnostic_flag_only_no_route_promotion"
    assert set(gate["primary_gate_metrics"]) == {
        "roughness_leakage_rank_percentile_in_stratum",
        "roughness_leakage_vs_v1_rank_percentile_delta",
        "roughness_leakage_pairwise_inversion_flag",
    }


def test_roughness_leakage_contract_preserves_jacobian_layering() -> None:
    jacobian = _contract()["jacobian_layering"]

    assert jacobian["v1_bfp_to_angle_jacobian_applied"] is False
    assert jacobian["audit_bfp_jacobian_applied"] is True
    assert jacobian["roughness_contract_must_not_rewrite_v1_jacobian_flag"] is True
    assert jacobian["roughness_contract_may_reference_audit_jacobian_provenance"] is True


def test_roughness_leakage_contract_and_report_claim_language_pass() -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))
    contract_text = root_path(CONTRACT_PATH).read_text(encoding="utf-8")
    report_text = root_path(REPORT_PATH).read_text(encoding="utf-8")

    assert claim_text_passes(contract_text, lexicon)
    assert claim_text_passes(report_text, lexicon)
    assert "no-solver rank diagnostic; no roughness or leakage simulation" in report_text
