from __future__ import annotations

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.review_package import claim_text_passes, load_forbidden_claims_lexicon

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


REGISTRY_PATH = "configs/realism_v2/physical_ceiling_extension_registry.yaml"
REPORT_PATH = "reports/92_EV_NODI_P1_physical_ceiling_extensions_plan.md"
FULL_WAVE_CONTRACT_PATH = (
    "configs/realism_v2/full_wave_green_tensor_diagnostic_contract.yaml"
)
FULL_WAVE_REPORT_PATH = (
    "reports/93_EV_NODI_P1_full_wave_green_tensor_diagnostic_contract.md"
)
VECTOR_CONTRACT_PATH = (
    "configs/realism_v2/vector_jones_polarization_diagnostic_contract.yaml"
)
VECTOR_REPORT_PATH = (
    "reports/94_EV_NODI_P1_vector_jones_polarization_diagnostic_contract.md"
)
ROUGHNESS_CONTRACT_PATH = "configs/realism_v2/roughness_leakage_diagnostic_contract.yaml"
ROUGHNESS_REPORT_PATH = "reports/95_EV_NODI_P1_roughness_leakage_diagnostic_contract.md"
TRANSPORT_CONTRACT_PATH = (
    "configs/realism_v2/transport_residence_time_diagnostic_contract.yaml"
)
TRANSPORT_REPORT_PATH = (
    "reports/96_EV_NODI_P1_transport_residence_time_diagnostic_contract.md"
)
CONTRACT_MANIFEST_PATH = (
    "results/post_v2_physical_ceiling/physical_ceiling_contract_manifest.json"
)
SCHEMA_MANIFEST_PATH = (
    "results/post_v2_physical_ceiling/physical_ceiling_diagnostic_schema_manifest.json"
)
INPUT_BINDING_MANIFEST_PATH = (
    "results/post_v2_physical_ceiling/physical_ceiling_input_binding_manifest.json"
)
ROUTE_COVERAGE_MANIFEST_PATH = (
    "results/post_v2_physical_ceiling/physical_ceiling_route_coverage_manifest.json"
)
PHYSICAL_CEILING_README_PATH = "results/post_v2_physical_ceiling/README.md"
FULL_WAVE_DIAGNOSTIC_PATH = (
    "results/post_v2_physical_ceiling/full_wave_green_tensor_diagnostic.csv"
)
VECTOR_DIAGNOSTIC_PATH = (
    "results/post_v2_physical_ceiling/vector_jones_polarization_diagnostic.csv"
)
ROUGHNESS_DIAGNOSTIC_PATH = (
    "results/post_v2_physical_ceiling/roughness_leakage_diagnostic.csv"
)
TRANSPORT_DIAGNOSTIC_PATH = (
    "results/post_v2_physical_ceiling/transport_residence_time_diagnostic.csv"
)
PHYSICAL_CEILING_VERIFIER_PATH = "tools/verify_post_v2_physical_ceiling_contracts.py"
CONTRACT_MANIFEST_SCHEMA_DOC = "docs/schemas/physical_ceiling_contract_manifest_schema.md"
DIAGNOSTIC_SCHEMA_MANIFEST_SCHEMA_DOC = (
    "docs/schemas/physical_ceiling_diagnostic_schema_manifest_schema.md"
)
INPUT_BINDING_MANIFEST_SCHEMA_DOC = (
    "docs/schemas/physical_ceiling_input_binding_manifest_schema.md"
)
ROUTE_COVERAGE_MANIFEST_SCHEMA_DOC = (
    "docs/schemas/physical_ceiling_route_coverage_manifest_schema.md"
)
COMPLETION_NOTE_PATH = (
    "reports/97_EV_NODI_P1_physical_ceiling_contract_manifest_completion_note.md"
)


def _registry() -> dict:
    return rv2.load_json_yaml("physical_ceiling_extension_registry.yaml")


def _contract_paths() -> tuple[str, ...]:
    return (
        FULL_WAVE_CONTRACT_PATH,
        VECTOR_CONTRACT_PATH,
        ROUGHNESS_CONTRACT_PATH,
        TRANSPORT_CONTRACT_PATH,
    )


def test_physical_ceiling_registry_is_no_solver_diagnostic_complete() -> None:
    registry = _registry()

    assert registry["schema_version"] == "ev_nodi_physical_ceiling_extension_registry_v1"
    assert (
        registry["stage"]
        == "P1_physical_ceiling_extensions_no_solver_rank_diagnostics_complete"
    )
    assert registry["p0_release_conclusion_changed"] is False
    assert registry["calibrated_claim_allowed"] is False
    assert registry["physical_ceiling_role"] == "surrogate_risk_reduction_only"

    authority = registry["implementation_authority"]
    assert authority["planning_schema_and_risk_register_authorized"] is True
    assert authority["no_solver_rank_diagnostic_generation_authorized"] is True
    for key in (
        "heavy_physics_solver_execution_authorized",
        "new_full_wave_case_generation_authorized",
        "new_vector_solver_case_generation_authorized",
        "new_roughness_or_leakage_simulation_authorized",
        "new_transport_simulation_authorized",
        "v1_event_count_expansion_authorized",
        "route_promotion_authorized",
        "main_660_redefinition_authorized",
        "optional_660_W900_D1400_redefines_main_660",
    ):
        assert authority[key] is False


def test_physical_ceiling_registry_declares_all_claims_blocked() -> None:
    claims = _registry()["claim_governance"]

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


def test_physical_ceiling_score_and_jacobian_governance_stay_relative() -> None:
    registry = _registry()
    score = registry["score_governance"]
    jacobian = registry["jacobian_governance"]

    assert score["raw_arbitrary_unit_magnitude_final_gate_allowed"] is False
    assert score["raw_arbitrary_unit_magnitude_role"] == "diagnostic_only_not_final_gate"
    assert set(score["final_gate_metric_family"]) == {
        "rank",
        "rank_percentile",
        "pairwise_inversion",
    }
    assert score["comparison_stratum_primary"] == "all_ranked_routes"

    assert jacobian["v1_bfp_to_angle_jacobian_applied"] is False
    assert jacobian["audit_bfp_jacobian_applied"] is True


def test_physical_ceiling_lanes_are_split_and_fail_closed() -> None:
    registry = _registry()
    lanes = registry["extension_lanes"]

    assert {lane["lane_id"] for lane in lanes} == {
        "full_wave_green_tensor_physical_ceiling_diagnostic",
        "vector_jones_polarization_diagnostic",
        "roughness_leakage_diagnostic",
        "transport_residence_time_diagnostic",
    }

    for lane in lanes:
        assert lane["phase_1_status"] == "complete"
        assert lane["phase_2_status"] == "generated_no_solver_rank_diagnostic_no_heavy_solver"
        assert lane["inputs"], lane
        assert lane["outputs"], lane
        assert lane["required_tests"], lane
        boundary = lane["claim_boundary"]
        assert boundary["calibrated_claim_allowed"] is False
        assert boundary["p0_release_conclusion_changed"] is False
        assert boundary["physical_ceiling_role"] == "surrogate_risk_reduction_only"
        assert boundary["route_promotion_authorized"] is False


def test_physical_ceiling_artifact_manifest_schema_requires_guard_fields() -> None:
    registry = _registry()
    schema = registry["artifact_manifest_schema"]

    assert schema["schema_name"] == "ev_nodi_physical_ceiling_p1_artifact_manifest_v1"
    assert set(schema["required_false_fields"]) == {
        "calibrated_claim_allowed",
        "p0_release_conclusion_changed",
        "raw_magnitude_final_gate_allowed",
    }
    assert schema["required_role_value"] == "surrogate_risk_reduction_only"

    artifacts = registry["planned_artifacts"]
    assert {artifact["path"] for artifact in artifacts} == {
        REGISTRY_PATH,
        REPORT_PATH,
        FULL_WAVE_CONTRACT_PATH,
        FULL_WAVE_REPORT_PATH,
        VECTOR_CONTRACT_PATH,
        VECTOR_REPORT_PATH,
        ROUGHNESS_CONTRACT_PATH,
        ROUGHNESS_REPORT_PATH,
        TRANSPORT_CONTRACT_PATH,
        TRANSPORT_REPORT_PATH,
        CONTRACT_MANIFEST_PATH,
        SCHEMA_MANIFEST_PATH,
        INPUT_BINDING_MANIFEST_PATH,
        ROUTE_COVERAGE_MANIFEST_PATH,
        PHYSICAL_CEILING_README_PATH,
        FULL_WAVE_DIAGNOSTIC_PATH,
        VECTOR_DIAGNOSTIC_PATH,
        ROUGHNESS_DIAGNOSTIC_PATH,
        TRANSPORT_DIAGNOSTIC_PATH,
        PHYSICAL_CEILING_VERIFIER_PATH,
        CONTRACT_MANIFEST_SCHEMA_DOC,
        DIAGNOSTIC_SCHEMA_MANIFEST_SCHEMA_DOC,
        INPUT_BINDING_MANIFEST_SCHEMA_DOC,
        ROUTE_COVERAGE_MANIFEST_SCHEMA_DOC,
        COMPLETION_NOTE_PATH,
    }
    for artifact in artifacts:
        assert set(schema["required_artifact_fields"]).issubset(artifact)
        assert artifact["calibrated_claim_allowed"] is False
        assert artifact["p0_release_conclusion_changed"] is False
        assert artifact["physical_ceiling_role"] == "surrogate_risk_reduction_only"
        assert artifact["rank_evidence_required"] is True
        assert artifact["raw_magnitude_final_gate_allowed"] is False


def test_physical_ceiling_report_exists_and_uses_blocker_language() -> None:
    report = root_path(REPORT_PATH)
    text = report.read_text(encoding="utf-8")
    lexicon = load_forbidden_claims_lexicon(root_path("."))

    assert report.is_file()
    assert "no-solver rank diagnostics complete" in text
    assert "surrogate_risk_reduction_only" in text
    assert "`calibrated_claim_allowed` | `false`" in text
    assert "`p0_release_conclusion_changed` | `false`" in text
    assert claim_text_passes(text, lexicon)


def test_all_physical_ceiling_lane_contracts_are_registered_and_no_solver_outputs_exist() -> None:
    registry = _registry()
    artifact_paths = {artifact["path"] for artifact in registry["planned_artifacts"]}

    for contract_path in _contract_paths():
        assert contract_path in artifact_paths
        contract = rv2.load_json_yaml(root_path(contract_path))
        output_path = root_path(contract["output_schema"]["planned_output_path"])

        assert contract["calibrated_claim_allowed"] is False
        assert contract["p0_release_conclusion_changed"] is False
        assert contract["physical_ceiling_role"] == "surrogate_risk_reduction_only"
        assert (
            contract["output_schema"]["artifact_status"]
            == "generated_no_solver_rank_diagnostic"
        )
        assert output_path.exists(), contract["output_schema"]["planned_output_path"]

        claims = contract["claim_boundary"]
        for key in (
            "calibrated_snr_claim_allowed",
            "absolute_lod_claim_allowed",
            "true_ev_concentration_claim_allowed",
            "biological_specificity_claim_allowed",
            "detector_voltage_prediction_claim_allowed",
            "absolute_event_probability_claim_allowed",
        ):
            assert claims[key] is False

        gate = contract["gate_policy"]
        assert gate["raw_arbitrary_unit_magnitude_final_gate_allowed"] is False
        assert gate["decision_authority"] == "diagnostic_flag_only_no_route_promotion"
