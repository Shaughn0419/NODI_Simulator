from __future__ import annotations

import csv
from copy import deepcopy
import json
import subprocess
import sys

import pytest

from nodi_simulator import realism_v2 as rv2
from nodi_simulator.post_v2_minimal_bounded_solver_execution import (
    P6_SOLVER_OUTPUT_CSV,
    build_artifact_manifest,
    build_p5_binding_manifest,
    build_solver_output_manifest,
    build_solver_rows,
    validate_artifact_manifest,
    validate_execution_registry,
    validate_p5_binding_manifest,
    validate_solver_output_manifest,
    validate_solver_rows,
)
from nodi_simulator.review_package import (
    _config_entries,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


REGISTRY_PATH = "configs/realism_v2/minimal_bounded_solver_execution_registry.yaml"
PLAN_PATH = "reports/103_EV_NODI_P6_minimal_bounded_solver_execution_plan.md"
README_PATH = "results/post_v2_minimal_bounded_solver_execution/README.md"
P5_BINDING_MANIFEST_PATH = (
    "results/post_v2_minimal_bounded_solver_execution/"
    "minimal_bounded_solver_execution_p5_binding_manifest.json"
)
SOLVER_OUTPUT_MANIFEST_PATH = (
    "results/post_v2_minimal_bounded_solver_execution/"
    "full_wave_green_tensor_minimal_solver_output_manifest.json"
)
ARTIFACT_MANIFEST_PATH = (
    "results/post_v2_minimal_bounded_solver_execution/"
    "minimal_bounded_solver_execution_artifact_manifest.json"
)
SCHEMA_DOC_PATHS = (
    "docs/schemas/minimal_bounded_solver_execution_p5_binding_manifest_schema.md",
    "docs/schemas/minimal_bounded_solver_execution_output_manifest_schema.md",
    "docs/schemas/minimal_bounded_solver_execution_artifact_manifest_schema.md",
)


def _registry() -> dict:
    return rv2.load_json_yaml("minimal_bounded_solver_execution_registry.yaml")


def _load_json(path: str) -> dict:
    return json.loads(root_path(path).read_text(encoding="utf-8"))


def _csv_rows() -> list[dict[str, str]]:
    with root_path(P6_SOLVER_OUTPUT_CSV.as_posix()).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_p6_registry_authorizes_only_minimal_execution() -> None:
    registry = validate_execution_registry(_registry())

    assert registry["stage"] == "P6_minimal_bounded_solver_execution_complete"
    assert registry["execution_role"] == "minimal_bounded_solver_execution_trace_only"
    assert registry["calibrated_claim_allowed"] is False
    assert registry["p0_release_conclusion_changed"] is False
    assert registry["physical_solver_execution_authorized"] is True
    assert registry["minimal_bounded_solver_execution_authorized"] is True
    assert registry["green_tensor_minimal_solver_execution_authorized"] is True
    assert registry["solver_output_generated"] is True
    for key in (
        "full_wave_solver_execution_authorized",
        "measured_data_ingest_authorized",
        "calibration_data_ingest_authorized",
        "new_mesh_generation_authorized",
        "operator_export_generation_authorized",
        "route_promotion_authorized",
        "raw_magnitude_final_gate_allowed",
        "solver_native_raw_magnitude_final_gate_allowed",
    ):
        assert registry[key] is False


def test_p6_generated_manifests_are_current() -> None:
    assert _load_json(P5_BINDING_MANIFEST_PATH) == build_p5_binding_manifest(root_path("."))
    assert _load_json(SOLVER_OUTPUT_MANIFEST_PATH) == build_solver_output_manifest(root_path("."))
    assert _load_json(ARTIFACT_MANIFEST_PATH) == build_artifact_manifest(root_path("."))


def test_p6_solver_output_is_rank_pairwise_trace_only() -> None:
    rows = validate_solver_rows(build_solver_rows(root_path(".")))
    csv_rows = _csv_rows()

    assert len(rows) == 3
    assert [row["solver_response_rank"] for row in rows] == [1, 2, 3]
    assert [row["pairwise_order_signature"] for row in rows] == ["1_of_3", "2_of_3", "3_of_3"]
    assert {row["solver_output_generated"] for row in rows} == {True}
    assert {row["raw_magnitude_final_gate_allowed"] for row in rows} == {False}
    assert {row["solver_native_raw_magnitude_final_gate_allowed"] for row in rows} == {False}
    assert {row["route_promotion_authorized"] for row in rows} == {False}
    assert len(csv_rows) == 3
    assert "solver_native_response_trace_only" in csv_rows[0]


def test_p6_binding_and_output_manifests_preserve_boundaries() -> None:
    binding = validate_p5_binding_manifest(build_p5_binding_manifest(root_path(".")))
    output = validate_solver_output_manifest(build_solver_output_manifest(root_path(".")))
    artifact = validate_artifact_manifest(build_artifact_manifest(root_path(".")), root_path("."))

    for manifest in (binding, output, artifact):
        assert manifest["calibrated_claim_allowed"] is False
        assert manifest["p0_release_conclusion_changed"] is False
        assert manifest["physical_solver_execution_authorized"] is True
        assert manifest["solver_output_generated"] is True
        assert manifest["measured_data_ingest_authorized"] is False
        assert manifest["calibration_data_ingest_authorized"] is False
        assert manifest["new_mesh_generation_authorized"] is False
        assert manifest["operator_export_generation_authorized"] is False
        assert manifest["full_wave_solver_execution_authorized"] is False
        assert manifest["route_promotion_authorized"] is False


def test_p6_registry_rejects_scope_and_authority_tampering() -> None:
    registry = deepcopy(_registry())
    registry["implementation_authority"]["full_wave_solver_execution_authorized"] = True
    with pytest.raises(ValueError, match="implementation authority drifted"):
        validate_execution_registry(registry)

    registry = deepcopy(_registry())
    registry["implementation_authority"]["solver_output_generation_authorized"] = False
    with pytest.raises(ValueError, match="implementation authority drifted"):
        validate_execution_registry(registry)

    registry = deepcopy(_registry())
    registry["implementation_authority"].pop("solver_output_generation_authorized")
    with pytest.raises(ValueError, match="authority field set drifted"):
        validate_execution_registry(registry)

    registry = deepcopy(_registry())
    registry["authorization_evidence"]["user_authorization_phrase_received"] = "execute everything"
    with pytest.raises(ValueError, match="user authorization phrase drifted"):
        validate_execution_registry(registry)

    registry = deepcopy(_registry())
    registry["interpretability_governance"]["solver_native_raw_magnitude_final_gate_allowed"] = True
    with pytest.raises(ValueError, match="solver_native_raw_magnitude_final_gate_allowed=false"):
        validate_execution_registry(registry)


def test_p6_manifests_reject_execution_boundary_tampering() -> None:
    manifest = build_p5_binding_manifest(root_path("."))
    manifest["route_promotion_authorized"] = True
    with pytest.raises(ValueError, match="route_promotion_authorized=false"):
        validate_p5_binding_manifest(manifest)

    manifest = build_p5_binding_manifest(root_path("."))
    manifest["p5_authorization_gate_decision"] = "authorized"
    with pytest.raises(ValueError, match="gate decision drifted"):
        validate_p5_binding_manifest(manifest)

    manifest = build_solver_output_manifest(root_path("."))
    manifest["raw_solver_native_fields_role"] = "final_gate"
    with pytest.raises(ValueError, match="raw solver-native role drifted"):
        validate_solver_output_manifest(manifest)

    manifest = build_solver_output_manifest(root_path("."))
    manifest["allowed_final_gate_metric_families"].append("solver_native_raw")
    with pytest.raises(ValueError, match="final gate families drifted"):
        validate_solver_output_manifest(manifest)

    rows = build_solver_rows(root_path("."))
    rows[0]["measured_data_ingest_authorized"] = True
    with pytest.raises(ValueError, match="measured_data_ingest_authorized=false"):
        validate_solver_rows(rows)


def test_p6_text_artifacts_use_blocker_language() -> None:
    lexicon = load_forbidden_claims_lexicon(root_path("."))

    for path in (REGISTRY_PATH, PLAN_PATH, README_PATH, *SCHEMA_DOC_PATHS):
        assert claim_text_passes(root_path(path).read_text(encoding="utf-8"), lexicon), path


def test_p6_schema_docs_preserve_boundaries() -> None:
    required_snippets = [
        "calibrated_claim_allowed = false",
        "p0_release_conclusion_changed = false",
        "p1_surrogate_risk_role_preserved = true",
        "p2_readiness_scope_preserved = true",
        "p3_pilot_design_scope_preserved = true",
        "p4_dry_run_preflight_scope_preserved = true",
        "p5_authorization_gate_scope_preserved = true",
        "physical_solver_execution_authorized = true",
        "minimal_bounded_solver_execution_authorized = true",
        "green_tensor_minimal_solver_execution_authorized = true",
        "solver_output_generated = true",
        "measured_data_ingest_authorized = false",
        "calibration_data_ingest_authorized = false",
        "new_mesh_generation_authorized = false",
        "operator_export_generation_authorized = false",
        "full_wave_solver_execution_authorized = false",
        "route_promotion_authorized = false",
        "raw_magnitude_final_gate_allowed = false",
        "solver_native_raw_magnitude_final_gate_allowed = false",
    ]
    for path in SCHEMA_DOC_PATHS:
        text = root_path(path).read_text(encoding="utf-8")
        for snippet in required_snippets:
            assert snippet in text, f"{path} missing {snippet}"


def test_p6_verifier_cli_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/verify_post_v2_minimal_bounded_solver_execution.py")),
            "--package-root",
            str(root_path(".")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS minimal_bounded_solver_execution_registry" in result.stdout
    assert "PASS minimal_bounded_solver_execution_output_csv_current" in result.stdout
    assert "PASS minimal_bounded_solver_execution_claim_boundaries" in result.stdout


def test_p6_registry_is_excluded_from_p0_review_package_config_glob() -> None:
    paths = {entry["path"] for entry in _config_entries(root_path("."))}

    assert REGISTRY_PATH not in paths
