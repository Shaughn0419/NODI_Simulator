from __future__ import annotations

from copy import deepcopy
import json
import subprocess
import sys

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.post_v2_bounded_solver_authorization_gate import (
    MINIMUM_LATER_PHASE_REQUIREMENTS,
    REQUIRED_P4_PATHS,
    REQUIRED_NEXT_AUTHORIZATION_PHRASE,
    build_artifact_manifest,
    build_authorization_gate_record,
    build_p4_binding_manifest,
    validate_authorization_gate_record,
    validate_gate_registry,
    validate_p4_binding_manifest,
)
from nodi_simulator.review_package import (
    _config_entries,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


REGISTRY_PATH = "configs/realism_v2/bounded_solver_authorization_gate_registry.yaml"
PLAN_PATH = "reports/102_EV_NODI_P5_bounded_solver_authorization_gate_plan.md"
README_PATH = "results/post_v2_bounded_solver_authorization_gate/README.md"
P4_BINDING_MANIFEST_PATH = (
    "results/post_v2_bounded_solver_authorization_gate/"
    "bounded_solver_authorization_gate_p4_binding_manifest.json"
)
AUTHORIZATION_GATE_RECORD_PATH = (
    "results/post_v2_bounded_solver_authorization_gate/"
    "bounded_solver_authorization_gate_record.json"
)
ARTIFACT_MANIFEST_PATH = (
    "results/post_v2_bounded_solver_authorization_gate/"
    "bounded_solver_authorization_gate_artifact_manifest.json"
)
SCHEMA_DOC_PATHS = (
    "docs/schemas/bounded_solver_authorization_gate_p4_binding_manifest_schema.md",
    "docs/schemas/bounded_solver_authorization_gate_record_schema.md",
    "docs/schemas/bounded_solver_authorization_gate_artifact_manifest_schema.md",
)


def _registry() -> dict:
    return rv2.load_json_yaml("bounded_solver_authorization_gate_registry.yaml")


def _load_json(path: str) -> dict:
    return json.loads(root_path(path).read_text(encoding="utf-8"))


def test_p5_registry_is_authorization_gate_only() -> None:
    registry = validate_gate_registry(_registry())

    assert registry["schema_version"] == "ev_nodi_p5_bounded_solver_authorization_gate_registry_v1"
    assert registry["stage"] == "P5_bounded_solver_authorization_gate_complete"
    assert registry["gate_role"] == "authorization_gate_only_no_solver_execution"
    assert registry["calibrated_claim_allowed"] is False
    assert registry["p0_release_conclusion_changed"] is False
    assert registry["p1_surrogate_risk_role_preserved"] is True
    assert registry["p2_readiness_scope_preserved"] is True
    assert registry["p3_pilot_design_scope_preserved"] is True
    assert registry["p4_dry_run_preflight_scope_preserved"] is True
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


def test_p5_authority_and_claims_block_execution_and_calibration() -> None:
    registry = _registry()
    authority = registry["implementation_authority"]
    claims = registry["claim_governance"]

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


def test_p5_generated_manifests_are_current() -> None:
    assert _load_json(P4_BINDING_MANIFEST_PATH) == build_p4_binding_manifest(root_path("."))
    assert _load_json(AUTHORIZATION_GATE_RECORD_PATH) == build_authorization_gate_record(
        root_path(".")
    )
    assert _load_json(ARTIFACT_MANIFEST_PATH) == build_artifact_manifest(root_path("."))


def test_p5_p4_binding_manifest_binds_all_p4_manifests() -> None:
    manifest = validate_p4_binding_manifest(build_p4_binding_manifest(root_path(".")))

    assert manifest["bound_manifest_count"] == len(REQUIRED_P4_PATHS)
    assert tuple(binding["path"] for binding in manifest["bindings"]) == REQUIRED_P4_PATHS
    for binding in manifest["bindings"]:
        assert binding["sha256"]
        assert binding["physical_solver_execution_authorized"] is False
        assert binding["solver_output_generated"] is False
        assert binding["route_promotion_authorized"] is False


def test_p5_authorization_gate_record_denies_execution_until_explicit_request() -> None:
    manifest = validate_authorization_gate_record(
        build_authorization_gate_record(root_path("."))
    )

    assert (
        manifest["authorization_gate_decision"]
        == "not_authorized_pending_explicit_later_phase_execution_request"
    )
    assert manifest["explicit_solver_execution_request_required"] is True
    assert (
        manifest["required_next_authorization_phrase"]
        == REQUIRED_NEXT_AUTHORIZATION_PHRASE
    )
    assert tuple(manifest["minimum_later_phase_requirements"]) == MINIMUM_LATER_PHASE_REQUIREMENTS
    assert manifest["physical_solver_execution_authorized"] is False
    assert manifest["new_mesh_generation_authorized"] is False
    assert manifest["operator_export_generation_authorized"] is False
    assert manifest["solver_output_generated"] is False
    assert manifest["route_promotion_authorized"] is False


def test_p5_registry_rejects_execution_and_scope_tampering() -> None:
    registry = deepcopy(_registry())
    registry["implementation_authority"]["green_tensor_solver_execution_authorized"] = True
    with pytest.raises(ValueError, match="execution authority drifted"):
        validate_gate_registry(registry)

    registry = deepcopy(_registry())
    registry["p4_dry_run_preflight_scope_preserved"] = False
    with pytest.raises(ValueError, match="p4_dry_run_preflight_scope_preserved=true"):
        validate_gate_registry(registry)

    registry = deepcopy(_registry())
    registry["authorization_gate_record_contract"][
        "authorization_gate_decision"
    ] = "authorized"
    with pytest.raises(ValueError, match="authorization gate decision drifted"):
        validate_gate_registry(registry)

    registry = deepcopy(_registry())
    registry["authorization_gate_record_contract"][
        "required_next_authorization_phrase"
    ] = "authorize minimal bounded solver execution and calibrate"
    with pytest.raises(ValueError, match="registry authorization phrase drifted"):
        validate_gate_registry(registry)


def test_p5_manifests_reject_execution_and_binding_tampering() -> None:
    manifest = build_authorization_gate_record(root_path("."))
    manifest["physical_solver_execution_authorized"] = True
    with pytest.raises(ValueError, match="physical_solver_execution_authorized=false"):
        validate_authorization_gate_record(manifest)

    manifest = build_authorization_gate_record(root_path("."))
    manifest["required_next_authorization_phrase"] = (
        "authorize minimal bounded solver execution and calibrate"
    )
    with pytest.raises(ValueError, match="authorization phrase drifted"):
        validate_authorization_gate_record(manifest)

    manifest = build_authorization_gate_record(root_path("."))
    manifest["minimum_later_phase_requirements"] = []
    with pytest.raises(ValueError, match="later-phase requirements drifted"):
        validate_authorization_gate_record(manifest)

    manifest = build_p4_binding_manifest(root_path("."))
    manifest["bindings"][0]["path"] = "results/other.json"
    with pytest.raises(ValueError, match="binding path set drifted"):
        validate_p4_binding_manifest(manifest)


def test_p5_text_artifacts_use_blocker_language() -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))

    for path in (REGISTRY_PATH, PLAN_PATH, README_PATH, *SCHEMA_DOC_PATHS):
        assert claim_text_passes(root_path(path).read_text(encoding="utf-8"), lexicon), path


def test_p5_schema_docs_preserve_boundaries() -> None:
    required_snippets = [
        "calibrated_claim_allowed = false",
        "p0_release_conclusion_changed = false",
        "p1_surrogate_risk_role_preserved = true",
        "p2_readiness_scope_preserved = true",
        "p3_pilot_design_scope_preserved = true",
        "p4_dry_run_preflight_scope_preserved = true",
        "physical_solver_execution_authorized = false",
        "measured_data_ingest_authorized = false",
        "calibration_data_ingest_authorized = false",
        "new_mesh_generation_authorized = false",
        "operator_export_generation_authorized = false",
        "solver_output_generated = false",
        "route_promotion_authorized = false",
    ]
    for path in SCHEMA_DOC_PATHS:
        text = root_path(path).read_text(encoding="utf-8")
        for snippet in required_snippets:
            assert snippet in text, f"{path} missing {snippet}"


def test_p5_verifier_cli_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/verify_post_v2_bounded_solver_authorization_gate.py")),
            "--package-root",
            str(root_path(".")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS bounded_solver_authorization_gate_registry" in result.stdout
    assert "PASS bounded_solver_authorization_gate_record_current" in result.stdout
    assert "PASS bounded_solver_authorization_gate_execution_blocked" in result.stdout
    assert "PASS bounded_solver_authorization_gate_explicit_later_phase_required" in result.stdout


def test_p5_registry_is_excluded_from_p0_review_package_config_glob() -> None:
    paths = {entry["path"] for entry in _config_entries(root_path("."))}

    assert REGISTRY_PATH not in paths
