"""P5 bounded solver authorization-gate helpers.

This module creates a review gate after P4 dry-run preflight. It does not run a
solver, generate meshes, export operators, ingest measured/calibration data, or
promote routes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .post_v2_bounded_solver_dry_run_preflight import (
    P4_ARTIFACT_MANIFEST,
    P4_EXECUTION_AUTHORIZATION_RECORD,
    P4_INPUT_MANIFEST,
    P4_MESH_PREFLIGHT_MANIFEST,
    P4_P3_BINDING_MANIFEST,
    validate_artifact_manifest as validate_p4_artifact_manifest,
    validate_execution_authorization_record as validate_p4_execution_authorization_record,
    validate_input_manifest as validate_p4_input_manifest,
    validate_mesh_preflight_manifest as validate_p4_mesh_preflight_manifest,
    validate_p3_binding_manifest as validate_p4_p3_binding_manifest,
)
from .realism_v2 import load_json_yaml
from .realism_v2_io import sha256_file, write_json_atomic
from .review_package import (
    PROJECT_ROOT,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)


P5_GATE_DIR = Path("results/post_v2_bounded_solver_authorization_gate")
P5_GATE_REGISTRY = "configs/realism_v2/bounded_solver_authorization_gate_registry.yaml"
P5_GATE_PLAN = "reports/102_EV_NODI_P5_bounded_solver_authorization_gate_plan.md"
P5_GATE_README = P5_GATE_DIR / "README.md"
P5_P4_BINDING_MANIFEST = P5_GATE_DIR / "bounded_solver_authorization_gate_p4_binding_manifest.json"
P5_AUTHORIZATION_GATE_RECORD = P5_GATE_DIR / "bounded_solver_authorization_gate_record.json"
P5_ARTIFACT_MANIFEST = P5_GATE_DIR / "bounded_solver_authorization_gate_artifact_manifest.json"

P5_TEXT_PATHS: tuple[str, ...] = (
    P5_GATE_REGISTRY,
    P5_GATE_PLAN,
    P5_GATE_README.as_posix(),
    "docs/schemas/bounded_solver_authorization_gate_p4_binding_manifest_schema.md",
    "docs/schemas/bounded_solver_authorization_gate_record_schema.md",
    "docs/schemas/bounded_solver_authorization_gate_artifact_manifest_schema.md",
)

P5_GATE_STAGE = "P5_bounded_solver_authorization_gate_complete"
P5_GATE_SCHEMA_VERSION = "ev_nodi_p5_bounded_solver_authorization_gate_registry_v1"
REQUIRED_NEXT_AUTHORIZATION_PHRASE = "authorize minimal bounded solver execution"
MINIMUM_LATER_PHASE_REQUIREMENTS: tuple[str, ...] = (
    "explicit user request to authorize minimal bounded solver execution",
    "separate branch or commit that changes execution_authorization_decision",
    "solver runtime implementation review",
    "claim-boundary review before any generated solver output is interpreted",
)

TOP_LEVEL_FALSE_FIELDS: tuple[str, ...] = (
    "calibrated_claim_allowed",
    "p0_release_conclusion_changed",
    "physical_solver_execution_authorized",
    "measured_data_ingest_authorized",
    "calibration_data_ingest_authorized",
    "new_mesh_generation_authorized",
    "operator_export_generation_authorized",
    "solver_output_generated",
    "route_promotion_authorized",
)

TOP_LEVEL_TRUE_FIELDS: tuple[str, ...] = (
    "p1_surrogate_risk_role_preserved",
    "p2_readiness_scope_preserved",
    "p3_pilot_design_scope_preserved",
    "p4_dry_run_preflight_scope_preserved",
)

CLAIM_BOUNDARY_FALSE_FIELDS: tuple[str, ...] = (
    "calibrated_snr_claim_allowed",
    "absolute_lod_claim_allowed",
    "true_ev_concentration_claim_allowed",
    "biological_specificity_claim_allowed",
    "detector_voltage_prediction_claim_allowed",
    "absolute_event_probability_claim_allowed",
    "sample_count_claim_allowed",
    "measured_blank_safety_claim_allowed",
    "route_promotion_authorized",
)

ALLOWED_TRUE_AUTHORITY_FIELDS: frozenset[str] = frozenset(
    {
        "authorization_gate_record_generation_authorized",
        "p4_binding_manifest_generation_authorized",
        "artifact_manifest_generation_authorized",
        "verifier_authorized",
    }
)

REQUIRED_P4_PATHS: tuple[str, ...] = (
    P4_P3_BINDING_MANIFEST.as_posix(),
    P4_INPUT_MANIFEST.as_posix(),
    P4_MESH_PREFLIGHT_MANIFEST.as_posix(),
    P4_EXECUTION_AUTHORIZATION_RECORD.as_posix(),
    P4_ARTIFACT_MANIFEST.as_posix(),
)


def load_gate_registry(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return load_json_yaml(project_root / P5_GATE_REGISTRY)


def _load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_false(mapping: dict[str, Any], keys: tuple[str, ...], context: str) -> None:
    for key in keys:
        if mapping.get(key) is not False:
            raise ValueError(f"{context} must keep {key}=false")


def _require_true(mapping: dict[str, Any], keys: tuple[str, ...], context: str) -> None:
    for key in keys:
        if mapping.get(key) is not True:
            raise ValueError(f"{context} must keep {key}=true")


def _validate_claim_boundary(claims: dict[str, Any], context: str) -> None:
    _require_false(claims, CLAIM_BOUNDARY_FALSE_FIELDS, context)
    if claims.get("allowed_claim_level") != "bounded_solver_authorization_gate_only":
        raise ValueError(f"{context} claim level drifted")


def validate_gate_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema_version") != P5_GATE_SCHEMA_VERSION:
        raise ValueError("unexpected P5 gate registry schema")
    if registry.get("stage") != P5_GATE_STAGE:
        raise ValueError("unexpected P5 gate stage")
    if registry.get("gate_role") != "authorization_gate_only_no_solver_execution":
        raise ValueError("P5 gate role drifted")
    _require_false(registry, TOP_LEVEL_FALSE_FIELDS, "P5 registry")
    _require_true(registry, TOP_LEVEL_TRUE_FIELDS, "P5 registry")

    authority = registry["implementation_authority"]
    for key, value in authority.items():
        if key in ALLOWED_TRUE_AUTHORITY_FIELDS:
            if value is not True:
                raise ValueError(f"P5 gate authority missing: {key}")
            continue
        if value is not False:
            raise ValueError(f"P5 execution authority drifted: {key}")

    _validate_claim_boundary(registry["claim_governance"], "P5 registry")
    binding = registry["p4_dry_run_preflight_binding"]
    if tuple(binding["required_manifest_paths"]) != REQUIRED_P4_PATHS:
        raise ValueError("P5 required P4 manifest path set drifted")
    _require_false(binding, TOP_LEVEL_FALSE_FIELDS, "P5 P4 binding")
    _require_true(binding, TOP_LEVEL_TRUE_FIELDS, "P5 P4 binding")

    record = registry["authorization_gate_record_contract"]
    if record["authorization_gate_decision"] != "not_authorized_pending_explicit_later_phase_execution_request":
        raise ValueError("P5 authorization gate decision drifted")
    if record["explicit_solver_execution_request_required"] is not True:
        raise ValueError("P5 must require an explicit solver execution request")
    if record["required_next_authorization_phrase"] != REQUIRED_NEXT_AUTHORIZATION_PHRASE:
        raise ValueError("P5 registry authorization phrase drifted")
    _require_false(record, TOP_LEVEL_FALSE_FIELDS, "P5 authorization record contract")
    _require_true(record, TOP_LEVEL_TRUE_FIELDS, "P5 authorization record contract")

    schema = registry["artifact_manifest_schema"]
    required = set(schema["required_artifact_fields"])
    for field in (*TOP_LEVEL_FALSE_FIELDS, *TOP_LEVEL_TRUE_FIELDS):
        if field not in required:
            raise ValueError(f"P5 artifact schema missing guard field: {field}")
    for artifact in registry["planned_artifacts"]:
        if not required.issubset(artifact):
            raise ValueError(f"P5 artifact missing schema fields: {artifact['artifact_id']}")
        _require_false(artifact, TOP_LEVEL_FALSE_FIELDS, artifact["artifact_id"])
        _require_true(artifact, TOP_LEVEL_TRUE_FIELDS, artifact["artifact_id"])
    return registry


def _load_validated_p4_manifests(project_root: Path) -> dict[str, dict[str, Any]]:
    return {
        P4_P3_BINDING_MANIFEST.as_posix(): validate_p4_p3_binding_manifest(
            _load_json_file(project_root / P4_P3_BINDING_MANIFEST)
        ),
        P4_INPUT_MANIFEST.as_posix(): validate_p4_input_manifest(
            _load_json_file(project_root / P4_INPUT_MANIFEST)
        ),
        P4_MESH_PREFLIGHT_MANIFEST.as_posix(): validate_p4_mesh_preflight_manifest(
            _load_json_file(project_root / P4_MESH_PREFLIGHT_MANIFEST)
        ),
        P4_EXECUTION_AUTHORIZATION_RECORD.as_posix(): validate_p4_execution_authorization_record(
            _load_json_file(project_root / P4_EXECUTION_AUTHORIZATION_RECORD)
        ),
        P4_ARTIFACT_MANIFEST.as_posix(): validate_p4_artifact_manifest(
            _load_json_file(project_root / P4_ARTIFACT_MANIFEST),
            project_root,
        ),
    }


def build_p4_binding_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_gate_registry(load_gate_registry(project_root))
    p4_manifests = _load_validated_p4_manifests(project_root)
    bindings = []
    for relpath in REQUIRED_P4_PATHS:
        manifest = p4_manifests[relpath]
        bindings.append(
            {
                "path": relpath,
                "sha256": sha256_file(project_root / relpath),
                "schema_version": manifest["schema_version"],
                "calibrated_claim_allowed": False,
                "p0_release_conclusion_changed": False,
                "p1_surrogate_risk_role_preserved": True,
                "p2_readiness_scope_preserved": True,
                "p3_pilot_design_scope_preserved": True,
                "p4_dry_run_preflight_scope_preserved": True,
                "physical_solver_execution_authorized": False,
                "measured_data_ingest_authorized": False,
                "calibration_data_ingest_authorized": False,
                "new_mesh_generation_authorized": False,
                "operator_export_generation_authorized": False,
                "solver_output_generated": False,
                "route_promotion_authorized": False,
            }
        )
    return {
        "schema_version": "ev_nodi_p5_bounded_solver_authorization_gate_p4_binding_manifest_v1",
        "stage": P5_GATE_STAGE,
        "manifest_role": "p4_dry_run_preflight_binding_no_solver_execution",
        "bound_manifest_count": len(bindings),
        "bindings": bindings,
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "p2_readiness_scope_preserved": True,
        "p3_pilot_design_scope_preserved": True,
        "p4_dry_run_preflight_scope_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "calibration_data_ingest_authorized": False,
        "new_mesh_generation_authorized": False,
        "operator_export_generation_authorized": False,
        "solver_output_generated": False,
        "route_promotion_authorized": False,
    }


def validate_p4_binding_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p5_bounded_solver_authorization_gate_p4_binding_manifest_v1"
    ):
        raise ValueError("unexpected P5 P4 binding manifest schema")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P5 P4 binding manifest")
    _require_true(manifest, TOP_LEVEL_TRUE_FIELDS, "P5 P4 binding manifest")
    if manifest["bound_manifest_count"] != len(REQUIRED_P4_PATHS):
        raise ValueError("P5 P4 binding manifest count drifted")
    if tuple(binding["path"] for binding in manifest["bindings"]) != REQUIRED_P4_PATHS:
        raise ValueError("P5 P4 binding path set drifted")
    for binding in manifest["bindings"]:
        _require_false(binding, TOP_LEVEL_FALSE_FIELDS, binding["path"])
        _require_true(binding, TOP_LEVEL_TRUE_FIELDS, binding["path"])
    return manifest


def build_authorization_gate_record(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_gate_registry(load_gate_registry(project_root))
    p4_binding = build_p4_binding_manifest(project_root)
    return {
        "schema_version": "ev_nodi_p5_bounded_solver_authorization_gate_record_v1",
        "stage": P5_GATE_STAGE,
        "record_role": "authorization_gate_record_denies_execution_until_explicit_later_phase",
        "authorization_gate_decision": "not_authorized_pending_explicit_later_phase_execution_request",
        "explicit_solver_execution_request_required": True,
        "required_next_authorization_phrase": REQUIRED_NEXT_AUTHORIZATION_PHRASE,
        "p4_binding_manifest_path": P5_P4_BINDING_MANIFEST.as_posix(),
        "bound_p4_manifest_count": p4_binding["bound_manifest_count"],
        "minimum_later_phase_requirements": list(MINIMUM_LATER_PHASE_REQUIREMENTS),
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "p2_readiness_scope_preserved": True,
        "p3_pilot_design_scope_preserved": True,
        "p4_dry_run_preflight_scope_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "calibration_data_ingest_authorized": False,
        "new_mesh_generation_authorized": False,
        "operator_export_generation_authorized": False,
        "solver_output_generated": False,
        "route_promotion_authorized": False,
    }


def validate_authorization_gate_record(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p5_bounded_solver_authorization_gate_record_v1":
        raise ValueError("unexpected P5 authorization gate record schema")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P5 authorization gate record")
    _require_true(manifest, TOP_LEVEL_TRUE_FIELDS, "P5 authorization gate record")
    if manifest["authorization_gate_decision"] != "not_authorized_pending_explicit_later_phase_execution_request":
        raise ValueError("P5 authorization gate decision drifted")
    if manifest["explicit_solver_execution_request_required"] is not True:
        raise ValueError("P5 explicit solver execution request requirement drifted")
    if manifest["required_next_authorization_phrase"] != REQUIRED_NEXT_AUTHORIZATION_PHRASE:
        raise ValueError("P5 authorization phrase drifted")
    if tuple(manifest["minimum_later_phase_requirements"]) != MINIMUM_LATER_PHASE_REQUIREMENTS:
        raise ValueError("P5 later-phase requirements drifted")
    return manifest


def _artifact_entry(project_root: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    relpath = artifact["path"]
    path = project_root / relpath
    is_self_manifest = relpath == P5_ARTIFACT_MANIFEST.as_posix()
    return {
        **artifact,
        "path_exists": True if is_self_manifest else path.is_file(),
        "sha256": None if is_self_manifest else sha256_file(path) if path.is_file() else None,
        "hash_role": "self_hash_excluded" if is_self_manifest else "content_sha256",
    }


def build_artifact_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_gate_registry(load_gate_registry(project_root))
    artifacts = [_artifact_entry(project_root, artifact) for artifact in registry["planned_artifacts"]]
    return {
        "schema_version": "ev_nodi_p5_bounded_solver_authorization_gate_artifact_manifest_v1",
        "stage": P5_GATE_STAGE,
        "manifest_role": "authorization_gate_artifact_manifest_no_solver_execution",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "claim_boundary": dict.fromkeys(CLAIM_BOUNDARY_FALSE_FIELDS, False)
        | {"allowed_claim_level": "bounded_solver_authorization_gate_only"},
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "p2_readiness_scope_preserved": True,
        "p3_pilot_design_scope_preserved": True,
        "p4_dry_run_preflight_scope_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "calibration_data_ingest_authorized": False,
        "new_mesh_generation_authorized": False,
        "operator_export_generation_authorized": False,
        "solver_output_generated": False,
        "route_promotion_authorized": False,
    }


def validate_artifact_manifest(
    manifest: dict[str, Any],
    project_root: Path = PROJECT_ROOT,
    *,
    allow_missing_self_manifest: bool = False,
) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p5_bounded_solver_authorization_gate_artifact_manifest_v1":
        raise ValueError("unexpected P5 artifact manifest schema")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P5 artifact manifest")
    _require_true(manifest, TOP_LEVEL_TRUE_FIELDS, "P5 artifact manifest")
    _validate_claim_boundary(manifest["claim_boundary"], "P5 artifact manifest")
    for artifact in manifest["artifacts"]:
        _require_false(artifact, TOP_LEVEL_FALSE_FIELDS, artifact["artifact_id"])
        _require_true(artifact, TOP_LEVEL_TRUE_FIELDS, artifact["artifact_id"])
        is_self_manifest = artifact["path"] == P5_ARTIFACT_MANIFEST.as_posix()
        if (
            not (project_root / artifact["path"]).is_file()
            and not (allow_missing_self_manifest and is_self_manifest)
        ):
            raise ValueError(f"P5 artifact missing: {artifact['path']}")
        if artifact["hash_role"] == "content_sha256" and not artifact["sha256"]:
            raise ValueError(f"P5 artifact hash missing: {artifact['path']}")
    return manifest


def write_p4_binding_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_p4_binding_manifest(build_p4_binding_manifest(project_root))
    output_path = project_root / P5_P4_BINDING_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_authorization_gate_record(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_authorization_gate_record(
        build_authorization_gate_record(project_root)
    )
    output_path = project_root / P5_AUTHORIZATION_GATE_RECORD
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_artifact_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_artifact_manifest(
        build_artifact_manifest(project_root),
        project_root,
        allow_missing_self_manifest=True,
    )
    output_path = project_root / P5_ARTIFACT_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_gate_package(project_root: Path = PROJECT_ROOT) -> list[Path]:
    return [
        write_p4_binding_manifest(project_root),
        write_authorization_gate_record(project_root),
        write_artifact_manifest(project_root),
    ]


def _assert_manifest_current(path: Path, expected: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    actual = _load_json_file(path)
    if actual != expected:
        raise ValueError(f"stale {label}: regenerate P5 authorization gate manifests")


def verify_gate_package(project_root: Path = PROJECT_ROOT) -> list[str]:
    validate_gate_registry(load_gate_registry(project_root))
    p4_binding = validate_p4_binding_manifest(build_p4_binding_manifest(project_root))
    _assert_manifest_current(
        project_root / P5_P4_BINDING_MANIFEST,
        p4_binding,
        "P5 P4 binding manifest",
    )
    gate_record = validate_authorization_gate_record(
        build_authorization_gate_record(project_root)
    )
    _assert_manifest_current(
        project_root / P5_AUTHORIZATION_GATE_RECORD,
        gate_record,
        "P5 authorization gate record",
    )
    artifact_manifest = validate_artifact_manifest(
        build_artifact_manifest(project_root),
        project_root,
    )
    _assert_manifest_current(
        project_root / P5_ARTIFACT_MANIFEST,
        artifact_manifest,
        "P5 artifact manifest",
    )

    lexicon = load_forbidden_claims_lexicon(project_root)
    for relpath in P5_TEXT_PATHS:
        text = (project_root / relpath).read_text(encoding="utf-8")
        if not claim_text_passes(text, lexicon):
            raise ValueError(f"P5 authorization gate claim language drifted: {relpath}")

    return [
        "PASS bounded_solver_authorization_gate_registry",
        "PASS bounded_solver_authorization_gate_p4_binding_manifest_current",
        "PASS bounded_solver_authorization_gate_record_current",
        "PASS bounded_solver_authorization_gate_artifact_manifest_current",
        "PASS bounded_solver_authorization_gate_execution_blocked",
        "PASS bounded_solver_authorization_gate_explicit_later_phase_required",
        "PASS bounded_solver_authorization_gate_claim_boundaries",
    ]
