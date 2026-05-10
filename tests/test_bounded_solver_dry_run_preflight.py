from __future__ import annotations

from copy import deepcopy
import json
import subprocess
import sys

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.post_v2_bounded_solver_dry_run_preflight import (
    P4_PREFLIGHT_LANE_ID,
    build_artifact_manifest,
    build_execution_authorization_record,
    build_input_manifest,
    build_mesh_preflight_manifest,
    build_p3_binding_manifest,
    validate_execution_authorization_record,
    validate_input_manifest,
    validate_mesh_preflight_manifest,
    validate_p3_binding_manifest,
    validate_preflight_registry,
)
from nodi_simulator.review_package import (
    _config_entries,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


REGISTRY_PATH = "configs/realism_v2/bounded_solver_dry_run_preflight_registry.yaml"
PLAN_PATH = "reports/101_EV_NODI_P4_bounded_solver_dry_run_preflight_plan.md"
README_PATH = "results/post_v2_bounded_solver_dry_run_preflight/README.md"
P3_BINDING_MANIFEST_PATH = (
    "results/post_v2_bounded_solver_dry_run_preflight/"
    "bounded_solver_dry_run_preflight_p3_binding_manifest.json"
)
INPUT_MANIFEST_PATH = (
    "results/post_v2_bounded_solver_dry_run_preflight/"
    "full_wave_green_tensor_minimal_pilot_input_manifest.json"
)
MESH_PREFLIGHT_MANIFEST_PATH = (
    "results/post_v2_bounded_solver_dry_run_preflight/"
    "full_wave_green_tensor_mesh_boundary_unit_preflight_manifest.json"
)
EXECUTION_AUTHORIZATION_RECORD_PATH = (
    "results/post_v2_bounded_solver_dry_run_preflight/"
    "full_wave_green_tensor_execution_authorization_record.json"
)
ARTIFACT_MANIFEST_PATH = (
    "results/post_v2_bounded_solver_dry_run_preflight/"
    "bounded_solver_dry_run_preflight_artifact_manifest.json"
)
P3_ROUTE_SUBSET_MANIFEST_PATH = (
    "results/post_v2_bounded_solver_authorization_pilot_design/"
    "bounded_solver_authorization_pilot_design_route_subset_manifest.json"
)
P3_SCHEMA_MANIFEST_PATH = (
    "results/post_v2_bounded_solver_authorization_pilot_design/"
    "bounded_solver_authorization_pilot_design_schema_manifest.json"
)


def _registry() -> dict:
    return rv2.load_json_yaml("bounded_solver_dry_run_preflight_registry.yaml")


def _load_json(path: str) -> dict:
    return json.loads(root_path(path).read_text(encoding="utf-8"))


def test_p4_registry_is_dry_run_preflight_only() -> None:
    registry = validate_preflight_registry(_registry())

    assert registry["schema_version"] == "ev_nodi_p4_bounded_solver_dry_run_preflight_registry_v1"
    assert registry["stage"] == "P4_bounded_solver_dry_run_preflight_complete"
    assert registry["calibrated_claim_allowed"] is False
    assert registry["p0_release_conclusion_changed"] is False
    assert registry["p1_surrogate_risk_role_preserved"] is True
    assert registry["p2_readiness_scope_preserved"] is True
    assert registry["p3_pilot_design_scope_preserved"] is True
    for key in (
        "physical_solver_execution_authorized",
        "measured_data_ingest_authorized",
        "calibration_data_ingest_authorized",
        "new_mesh_generation_authorized",
        "operator_export_generation_authorized",
        "solver_output_generated",
        "route_promotion_authorized",
    ):
        assert registry[key] is False


def test_p4_authority_blocks_execution_mesh_output_and_claims() -> None:
    registry = _registry()
    authority = registry["implementation_authority"]
    claims = registry["claim_governance"]
    interpretability = registry["interpretability_governance"]

    for key in (
        "physical_solver_execution_authorized",
        "full_wave_solver_execution_authorized",
        "green_tensor_solver_execution_authorized",
        "new_mesh_generation_authorized",
        "operator_export_generation_authorized",
        "measured_data_ingest_authorized",
        "calibration_data_ingest_authorized",
        "solver_output_generation_authorized",
        "route_promotion_authorized",
    ):
        assert authority[key] is False
    for key in (
        "calibrated_snr_claim_allowed",
        "absolute_lod_claim_allowed",
        "true_ev_concentration_claim_allowed",
        "biological_specificity_claim_allowed",
        "detector_voltage_prediction_claim_allowed",
        "sample_count_claim_allowed",
        "measured_blank_safety_claim_allowed",
        "route_promotion_authorized",
    ):
        assert claims[key] is False
    assert set(interpretability["allowed_interpretability_families"]) == {
        "rank",
        "rank_percentile",
        "pairwise_inversion",
    }
    assert interpretability["raw_arbitrary_unit_magnitude_final_gate_allowed"] is False
    assert interpretability["solver_native_raw_magnitude_final_gate_allowed"] is False


def test_p4_generated_manifests_are_current() -> None:
    assert _load_json(P3_BINDING_MANIFEST_PATH) == build_p3_binding_manifest(root_path("."))
    assert _load_json(INPUT_MANIFEST_PATH) == build_input_manifest(root_path("."))
    assert _load_json(MESH_PREFLIGHT_MANIFEST_PATH) == build_mesh_preflight_manifest(
        root_path(".")
    )
    assert _load_json(EXECUTION_AUTHORIZATION_RECORD_PATH) == build_execution_authorization_record(
        root_path(".")
    )
    assert _load_json(ARTIFACT_MANIFEST_PATH) == build_artifact_manifest(root_path("."))


def test_p4_p3_binding_preserves_p3_subset_and_schema() -> None:
    manifest = validate_p3_binding_manifest(build_p3_binding_manifest(root_path(".")))

    assert manifest["p3_route_subset_manifest_path"] == P3_ROUTE_SUBSET_MANIFEST_PATH
    assert manifest["p3_schema_manifest_path"] == P3_SCHEMA_MANIFEST_PATH
    assert manifest["selected_route_count"] == 3
    assert set(manifest["selected_route_ids"]) == {
        "main_660_W800_D1400",
        "main_660_W800_D1500",
        "probe_404_W600_D1300",
    }
    assert manifest["physical_solver_execution_authorized"] is False
    assert manifest["solver_output_generated"] is False


def test_p4_input_manifest_is_dry_run_only() -> None:
    manifest = validate_input_manifest(build_input_manifest(root_path(".")))

    assert manifest["lane_id"] == P4_PREFLIGHT_LANE_ID
    assert manifest["p3_route_subset_manifest_path"] == P3_ROUTE_SUBSET_MANIFEST_PATH
    assert manifest["mesh_boundary_unit_preflight_manifest_path"] == MESH_PREFLIGHT_MANIFEST_PATH
    assert manifest["execution_authorization_record_path"] == EXECUTION_AUTHORIZATION_RECORD_PATH
    assert manifest["rank_pairwise_interpretability_declared"] is True
    assert set(manifest["selected_route_ids"]) == {
        "main_660_W800_D1400",
        "main_660_W800_D1500",
        "probe_404_W600_D1300",
    }
    assert manifest["physical_solver_execution_authorized"] is False
    assert manifest["new_mesh_generation_authorized"] is False
    assert manifest["operator_export_generation_authorized"] is False
    assert manifest["solver_output_generated"] is False
    assert manifest["route_promotion_authorized"] is False
    assert manifest["solver_native_raw_magnitude_final_gate_allowed"] is False


def test_p4_mesh_preflight_declares_no_mesh_generation() -> None:
    manifest = validate_mesh_preflight_manifest(build_mesh_preflight_manifest(root_path(".")))

    assert manifest["mesh_manifest_path"] is None
    assert manifest["mesh_manifest_sha256"] is None
    assert manifest["mesh_manifest_status"] == "not_generated_no_mesh_generation"
    assert manifest["new_mesh_generation_authorized"] is False
    assert manifest["operator_export_generation_authorized"] is False
    assert manifest["physical_solver_execution_authorized"] is False
    assert manifest["solver_output_generated"] is False
    assert manifest["v1_bfp_to_angle_jacobian_applied"] is False
    assert manifest["audit_bfp_jacobian_applied"] is True


def test_p4_execution_authorization_record_denies_execution() -> None:
    manifest = validate_execution_authorization_record(
        build_execution_authorization_record(root_path("."))
    )

    assert manifest["execution_authorization_decision"] == "not_authorized_phase4_dry_run_only"
    assert manifest["explicit_later_phase_required"] is True
    assert manifest["physical_solver_execution_authorized"] is False
    assert manifest["new_mesh_generation_authorized"] is False
    assert manifest["operator_export_generation_authorized"] is False
    assert manifest["solver_output_generated"] is False
    assert manifest["route_promotion_authorized"] is False


def test_p4_registry_rejects_execution_mesh_and_output_tampering() -> None:
    registry = deepcopy(_registry())
    registry["implementation_authority"]["green_tensor_solver_execution_authorized"] = True
    with pytest.raises(ValueError, match="execution authority drifted"):
        validate_preflight_registry(registry)

    registry = deepcopy(_registry())
    registry["implementation_authority"]["new_mesh_generation_authorized"] = True
    with pytest.raises(ValueError, match="execution authority drifted"):
        validate_preflight_registry(registry)

    registry = deepcopy(_registry())
    registry["solver_output_generated"] = True
    with pytest.raises(ValueError, match="solver_output_generated=false"):
        validate_preflight_registry(registry)


def test_p4_manifests_reject_drift_toward_execution_or_outputs() -> None:
    manifest = build_input_manifest(root_path("."))
    manifest["solver_native_raw_magnitude_final_gate_allowed"] = True
    with pytest.raises(ValueError, match="solver-native raw final gate drifted"):
        validate_input_manifest(manifest)

    manifest = build_mesh_preflight_manifest(root_path("."))
    manifest["mesh_manifest_path"] = "results/generated_mesh.json"
    with pytest.raises(ValueError, match="must not declare a generated mesh"):
        validate_mesh_preflight_manifest(manifest)

    manifest = build_execution_authorization_record(root_path("."))
    manifest["execution_authorization_decision"] = "authorized"
    with pytest.raises(ValueError, match="authorization decision drifted"):
        validate_execution_authorization_record(manifest)


def test_p4_text_artifacts_use_blocker_language() -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))

    for path in (REGISTRY_PATH, PLAN_PATH, README_PATH):
        assert claim_text_passes(root_path(path).read_text(encoding="utf-8"), lexicon), path


def test_p4_verifier_cli_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/verify_post_v2_bounded_solver_dry_run_preflight.py")),
            "--package-root",
            str(root_path(".")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS bounded_solver_dry_run_preflight_registry" in result.stdout
    assert "PASS bounded_solver_dry_run_preflight_input_manifest_current" in result.stdout
    assert "PASS bounded_solver_dry_run_preflight_mesh_generation_blocked" in result.stdout
    assert "PASS bounded_solver_dry_run_preflight_solver_output_absent" in result.stdout


def test_p4_registry_is_excluded_from_p0_review_package_config_glob() -> None:
    paths = {entry["path"] for entry in _config_entries(root_path("."))}

    assert REGISTRY_PATH not in paths
