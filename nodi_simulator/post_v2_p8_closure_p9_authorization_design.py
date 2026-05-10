"""P8 closure and P9 next-gate authorization-design helpers.

This module records the external P8 review result and creates the next
authorization-design gate. It does not run a solver, generate new solver output,
generate meshes, export operators, ingest measured/calibration data, or promote
routes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .post_v2_second_bounded_solver_lane_execution import (
    P8_ARTIFACT_MANIFEST,
    P8_EXECUTION_STAGE,
    P8_SOLVER_OUTPUT_MANIFEST,
    validate_artifact_manifest as validate_p8_artifact_manifest,
    validate_solver_output_manifest as validate_p8_solver_output_manifest,
)
from .realism_v2 import load_json_yaml
from .realism_v2_io import sha256_file, write_json_atomic
from .review_package import PROJECT_ROOT, claim_text_passes, load_forbidden_claims_lexicon


P8_CLOSURE_DIR = Path("results/post_v2_second_bounded_solver_lane_closure")
P8_CLOSURE_REGISTRY = "configs/realism_v2/second_bounded_solver_lane_closure_registry.yaml"
P8_CLOSURE_REPORT = "reports/106_EV_NODI_P8_second_bounded_solver_lane_closure_note.md"
P8_CLOSURE_README = P8_CLOSURE_DIR / "README.md"
P8_CLOSURE_REVIEW_RECORD = P8_CLOSURE_DIR / "p8_claude_review_closure_record.json"
P8_CLOSURE_ARTIFACT_MANIFEST = P8_CLOSURE_DIR / "p8_closure_artifact_manifest.json"

P9_DESIGN_DIR = Path("results/post_v2_next_bounded_lane_authorization_design")
P9_DESIGN_REGISTRY = "configs/realism_v2/next_bounded_lane_authorization_design_registry.yaml"
P9_DESIGN_REPORT = "reports/107_EV_NODI_P9_next_bounded_lane_authorization_design_plan.md"
P9_DESIGN_README = P9_DESIGN_DIR / "README.md"
P9_P8_CLOSURE_BINDING_MANIFEST = P9_DESIGN_DIR / "p9_p8_closure_binding_manifest.json"
P9_NEXT_AUTHORIZATION_GATE_RECORD = P9_DESIGN_DIR / "p9_next_authorization_gate_record.json"
P9_DESIGN_ARTIFACT_MANIFEST = P9_DESIGN_DIR / "p9_next_authorization_design_artifact_manifest.json"

P8_CLOSURE_STAGE = "P8_second_bounded_solver_lane_review_closure_complete"
P9_DESIGN_STAGE = "P9_next_bounded_lane_authorization_design_complete"
P8_CLOSURE_SCHEMA_VERSION = "ev_nodi_p8_second_bounded_solver_lane_closure_registry_v1"
P9_DESIGN_SCHEMA_VERSION = "ev_nodi_p9_next_bounded_lane_authorization_design_registry_v1"
P8_REVIEW_VERDICT = "NO P8 BLOCKERS FOUND"
P9_REQUIRED_FUTURE_AUTHORIZATION_PHRASE = "authorize third bounded solver lane execution"

P8_CLOSURE_TEXT_PATHS: tuple[str, ...] = (
    P8_CLOSURE_REGISTRY,
    P8_CLOSURE_REPORT,
    P8_CLOSURE_README.as_posix(),
    "docs/schemas/p8_closure_review_record_schema.md",
    "docs/schemas/p8_closure_artifact_manifest_schema.md",
)

P9_DESIGN_TEXT_PATHS: tuple[str, ...] = (
    P9_DESIGN_REGISTRY,
    P9_DESIGN_REPORT,
    P9_DESIGN_README.as_posix(),
    "docs/schemas/p9_next_authorization_gate_record_schema.md",
    "docs/schemas/p9_next_authorization_design_artifact_manifest_schema.md",
)

FALSE_FIELDS: tuple[str, ...] = (
    "calibrated_claim_allowed",
    "p0_release_conclusion_changed",
    "measured_data_ingest_authorized",
    "calibration_data_ingest_authorized",
    "new_mesh_generation_authorized",
    "operator_export_generation_authorized",
    "full_wave_solver_execution_authorized",
    "vector_solver_execution_authorized",
    "roughness_leakage_simulation_authorized",
    "transport_residence_time_simulation_authorized",
    "route_promotion_authorized",
    "raw_magnitude_final_gate_allowed",
    "solver_native_raw_magnitude_final_gate_allowed",
    "additional_solver_execution_authorized",
    "additional_solver_output_generated",
)

TRUE_FIELDS: tuple[str, ...] = (
    "p1_surrogate_risk_role_preserved",
    "p2_readiness_scope_preserved",
    "p3_pilot_design_scope_preserved",
    "p4_dry_run_preflight_scope_preserved",
    "p5_authorization_gate_scope_preserved",
    "p6_minimal_execution_scope_preserved",
    "p7_authorization_design_scope_preserved",
    "p8_second_bounded_execution_scope_preserved",
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
    "main_660_redefinition_authorized",
    "optional_660_W900_D1400_redefines_main_660",
)


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


def _guard_payload() -> dict[str, bool]:
    return {key: False for key in FALSE_FIELDS} | {key: True for key in TRUE_FIELDS}


def _validate_guard_fields(mapping: dict[str, Any], context: str) -> None:
    _require_false(mapping, FALSE_FIELDS, context)
    _require_true(mapping, TRUE_FIELDS, context)


def _validate_claim_boundary(claims: dict[str, Any], context: str, expected_level: str) -> None:
    _require_false(claims, CLAIM_BOUNDARY_FALSE_FIELDS, context)
    if claims.get("allowed_claim_level") != expected_level:
        raise ValueError(f"{context} claim level drifted")


def load_p8_closure_registry(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return load_json_yaml(project_root / P8_CLOSURE_REGISTRY)


def load_p9_design_registry(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return load_json_yaml(project_root / P9_DESIGN_REGISTRY)


def validate_p8_closure_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema_version") != P8_CLOSURE_SCHEMA_VERSION:
        raise ValueError("unexpected P8 closure registry schema")
    if registry.get("stage") != P8_CLOSURE_STAGE:
        raise ValueError("unexpected P8 closure stage")
    if registry.get("closure_role") != "review_closure_only_no_new_execution":
        raise ValueError("P8 closure role drifted")
    if registry["review_evidence"]["claude_review_verdict"] != P8_REVIEW_VERDICT:
        raise ValueError("P8 review verdict drifted")
    if registry["review_evidence"]["p8_execution_stage"] != P8_EXECUTION_STAGE:
        raise ValueError("P8 execution stage binding drifted")
    _validate_guard_fields(registry, "P8 closure registry")
    _validate_guard_fields(registry["review_evidence"], "P8 closure review evidence")
    _validate_claim_boundary(
        registry["claim_governance"],
        "P8 closure registry",
        "p8_review_closure_only",
    )
    for artifact in registry["planned_artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
    return registry


def validate_p9_design_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema_version") != P9_DESIGN_SCHEMA_VERSION:
        raise ValueError("unexpected P9 design registry schema")
    if registry.get("stage") != P9_DESIGN_STAGE:
        raise ValueError("unexpected P9 design stage")
    if registry.get("design_role") != "next_authorization_design_only_no_solver_execution":
        raise ValueError("P9 design role drifted")
    _validate_guard_fields(registry, "P9 design registry")
    _validate_claim_boundary(
        registry["claim_governance"],
        "P9 design registry",
        "next_authorization_design_only",
    )
    gate = registry["future_authorization_gate_contract"]
    if gate["required_future_authorization_phrase"] != P9_REQUIRED_FUTURE_AUTHORIZATION_PHRASE:
        raise ValueError("P9 future authorization phrase drifted")
    if gate["future_authorization_phrase_already_received"] is not False:
        raise ValueError("P9 future authorization phrase must not be already received")
    if gate["authorization_gate_decision"] != "not_authorized_pending_explicit_future_request":
        raise ValueError("P9 authorization gate decision drifted")
    _validate_guard_fields(gate, "P9 future authorization gate")
    p8_binding = registry["p8_closure_binding_contract"]
    if p8_binding["p8_closure_record_path"] != P8_CLOSURE_REVIEW_RECORD.as_posix():
        raise ValueError("P9 P8 closure record path drifted")
    _validate_guard_fields(p8_binding, "P9 P8 closure binding")
    for artifact in registry["planned_artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
    return registry


def build_p8_closure_review_record(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_p8_closure_registry(load_p8_closure_registry(project_root))
    validate_p8_solver_output_manifest(_load_json_file(project_root / P8_SOLVER_OUTPUT_MANIFEST))
    validate_p8_artifact_manifest(_load_json_file(project_root / P8_ARTIFACT_MANIFEST), project_root)
    return {
        "schema_version": "ev_nodi_p8_claude_review_closure_record_v1",
        "stage": P8_CLOSURE_STAGE,
        "record_role": "p8_review_closure_record",
        "claude_review_verdict": P8_REVIEW_VERDICT,
        "p8_execution_stage": P8_EXECUTION_STAGE,
        "p8_solver_output_manifest_path": P8_SOLVER_OUTPUT_MANIFEST.as_posix(),
        "p8_solver_output_manifest_sha256": sha256_file(project_root / P8_SOLVER_OUTPUT_MANIFEST),
        "p8_artifact_manifest_path": P8_ARTIFACT_MANIFEST.as_posix(),
        "p8_artifact_manifest_sha256": sha256_file(project_root / P8_ARTIFACT_MANIFEST),
        "closure_decision": "p8_closed_no_blockers_no_scope_expansion",
        **_guard_payload(),
    }


def validate_p8_closure_review_record(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("schema_version") != "ev_nodi_p8_claude_review_closure_record_v1":
        raise ValueError("unexpected P8 closure review record schema")
    if record["claude_review_verdict"] != P8_REVIEW_VERDICT:
        raise ValueError("P8 closure review verdict drifted")
    if record["p8_solver_output_manifest_path"] != P8_SOLVER_OUTPUT_MANIFEST.as_posix():
        raise ValueError("P8 closure output manifest path drifted")
    if record["p8_artifact_manifest_path"] != P8_ARTIFACT_MANIFEST.as_posix():
        raise ValueError("P8 closure artifact manifest path drifted")
    if record["closure_decision"] != "p8_closed_no_blockers_no_scope_expansion":
        raise ValueError("P8 closure decision drifted")
    _validate_guard_fields(record, "P8 closure review record")
    return record


def build_p9_p8_closure_binding_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_p9_design_registry(load_p9_design_registry(project_root))
    record = validate_p8_closure_review_record(_load_json_file(project_root / P8_CLOSURE_REVIEW_RECORD))
    return {
        "schema_version": "ev_nodi_p9_p8_closure_binding_manifest_v1",
        "stage": P9_DESIGN_STAGE,
        "manifest_role": "p8_closure_binding_for_next_authorization_design",
        "p8_closure_record_path": P8_CLOSURE_REVIEW_RECORD.as_posix(),
        "p8_closure_record_sha256": sha256_file(project_root / P8_CLOSURE_REVIEW_RECORD),
        "p8_review_verdict": record["claude_review_verdict"],
        "p8_execution_stage": record["p8_execution_stage"],
        **_guard_payload(),
    }


def validate_p9_p8_closure_binding_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p9_p8_closure_binding_manifest_v1":
        raise ValueError("unexpected P9 P8 closure binding manifest schema")
    if manifest["p8_closure_record_path"] != P8_CLOSURE_REVIEW_RECORD.as_posix():
        raise ValueError("P9 P8 closure record path drifted")
    if manifest["p8_review_verdict"] != P8_REVIEW_VERDICT:
        raise ValueError("P9 P8 review verdict drifted")
    _validate_guard_fields(manifest, "P9 P8 closure binding manifest")
    return manifest


def build_p9_next_authorization_gate_record(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_p9_design_registry(load_p9_design_registry(project_root))
    return {
        "schema_version": "ev_nodi_p9_next_authorization_gate_record_v1",
        "stage": P9_DESIGN_STAGE,
        "record_role": "future_third_bounded_lane_authorization_gate_record",
        "authorization_gate_decision": "not_authorized_pending_explicit_future_request",
        "required_future_authorization_phrase": P9_REQUIRED_FUTURE_AUTHORIZATION_PHRASE,
        "future_authorization_phrase_already_received": False,
        "explicit_next_execution_request_required": True,
        "minimum_later_phase_requirements": [
            "new user request containing the exact future authorization phrase",
            "separate branch or commit for any next execution lane",
            "bounded route/lane selection review before any output generation",
            "claim-boundary review before interpreting any generated solver output",
        ],
        **_guard_payload(),
    }


def validate_p9_next_authorization_gate_record(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("schema_version") != "ev_nodi_p9_next_authorization_gate_record_v1":
        raise ValueError("unexpected P9 next authorization gate record schema")
    if record["required_future_authorization_phrase"] != P9_REQUIRED_FUTURE_AUTHORIZATION_PHRASE:
        raise ValueError("P9 next authorization phrase drifted")
    if record["future_authorization_phrase_already_received"] is not False:
        raise ValueError("P9 future authorization phrase already received drifted")
    if record["authorization_gate_decision"] != "not_authorized_pending_explicit_future_request":
        raise ValueError("P9 next authorization gate decision drifted")
    _validate_guard_fields(record, "P9 next authorization gate record")
    return record


def _artifact_entry(project_root: Path, artifact: dict[str, Any], self_manifest: Path) -> dict[str, Any]:
    relpath = artifact["path"]
    path = project_root / relpath
    is_self_manifest = relpath == self_manifest.as_posix()
    return {
        **artifact,
        "path_exists": True if is_self_manifest else path.is_file(),
        "sha256": None if is_self_manifest else sha256_file(path) if path.is_file() else None,
        "hash_role": "self_hash_excluded" if is_self_manifest else "content_sha256",
    }


def build_p8_closure_artifact_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_p8_closure_registry(load_p8_closure_registry(project_root))
    artifacts = [
        _artifact_entry(project_root, artifact, P8_CLOSURE_ARTIFACT_MANIFEST)
        for artifact in registry["planned_artifacts"]
    ]
    return {
        "schema_version": "ev_nodi_p8_closure_artifact_manifest_v1",
        "stage": P8_CLOSURE_STAGE,
        "manifest_role": "p8_closure_artifact_manifest",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "claim_boundary": {
            key: False for key in CLAIM_BOUNDARY_FALSE_FIELDS
        }
        | {"allowed_claim_level": "p8_review_closure_only"},
        **_guard_payload(),
    }


def validate_p8_closure_artifact_manifest(
    manifest: dict[str, Any],
    project_root: Path = PROJECT_ROOT,
    *,
    allow_missing_self_manifest: bool = False,
) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p8_closure_artifact_manifest_v1":
        raise ValueError("unexpected P8 closure artifact manifest schema")
    _validate_guard_fields(manifest, "P8 closure artifact manifest")
    _validate_claim_boundary(manifest["claim_boundary"], "P8 closure artifact manifest", "p8_review_closure_only")
    for artifact in manifest["artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
        is_self_manifest = artifact["path"] == P8_CLOSURE_ARTIFACT_MANIFEST.as_posix()
        if (
            not (project_root / artifact["path"]).is_file()
            and not (allow_missing_self_manifest and is_self_manifest)
        ):
            raise ValueError(f"P8 closure artifact missing: {artifact['path']}")
    return manifest


def build_p9_design_artifact_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_p9_design_registry(load_p9_design_registry(project_root))
    artifacts = [
        _artifact_entry(project_root, artifact, P9_DESIGN_ARTIFACT_MANIFEST)
        for artifact in registry["planned_artifacts"]
    ]
    return {
        "schema_version": "ev_nodi_p9_next_authorization_design_artifact_manifest_v1",
        "stage": P9_DESIGN_STAGE,
        "manifest_role": "p9_next_authorization_design_artifact_manifest",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "claim_boundary": {
            key: False for key in CLAIM_BOUNDARY_FALSE_FIELDS
        }
        | {"allowed_claim_level": "next_authorization_design_only"},
        **_guard_payload(),
    }


def validate_p9_design_artifact_manifest(
    manifest: dict[str, Any],
    project_root: Path = PROJECT_ROOT,
    *,
    allow_missing_self_manifest: bool = False,
) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p9_next_authorization_design_artifact_manifest_v1":
        raise ValueError("unexpected P9 design artifact manifest schema")
    _validate_guard_fields(manifest, "P9 design artifact manifest")
    _validate_claim_boundary(manifest["claim_boundary"], "P9 design artifact manifest", "next_authorization_design_only")
    for artifact in manifest["artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
        is_self_manifest = artifact["path"] == P9_DESIGN_ARTIFACT_MANIFEST.as_posix()
        if (
            not (project_root / artifact["path"]).is_file()
            and not (allow_missing_self_manifest and is_self_manifest)
        ):
            raise ValueError(f"P9 design artifact missing: {artifact['path']}")
    return manifest


def write_p8_closure_package(project_root: Path = PROJECT_ROOT) -> list[Path]:
    record = validate_p8_closure_review_record(build_p8_closure_review_record(project_root))
    record_path = project_root / P8_CLOSURE_REVIEW_RECORD
    write_json_atomic(record_path, record, sort_keys=True)
    manifest = validate_p8_closure_artifact_manifest(
        build_p8_closure_artifact_manifest(project_root),
        project_root,
        allow_missing_self_manifest=True,
    )
    manifest_path = project_root / P8_CLOSURE_ARTIFACT_MANIFEST
    write_json_atomic(manifest_path, manifest, sort_keys=True)
    return [record_path, manifest_path]


def write_p9_design_package(project_root: Path = PROJECT_ROOT) -> list[Path]:
    binding = validate_p9_p8_closure_binding_manifest(
        build_p9_p8_closure_binding_manifest(project_root)
    )
    binding_path = project_root / P9_P8_CLOSURE_BINDING_MANIFEST
    write_json_atomic(binding_path, binding, sort_keys=True)
    gate = validate_p9_next_authorization_gate_record(
        build_p9_next_authorization_gate_record(project_root)
    )
    gate_path = project_root / P9_NEXT_AUTHORIZATION_GATE_RECORD
    write_json_atomic(gate_path, gate, sort_keys=True)
    manifest = validate_p9_design_artifact_manifest(
        build_p9_design_artifact_manifest(project_root),
        project_root,
        allow_missing_self_manifest=True,
    )
    manifest_path = project_root / P9_DESIGN_ARTIFACT_MANIFEST
    write_json_atomic(manifest_path, manifest, sort_keys=True)
    return [binding_path, gate_path, manifest_path]


def write_closure_and_design_packages(project_root: Path = PROJECT_ROOT) -> list[Path]:
    return [*write_p8_closure_package(project_root), *write_p9_design_package(project_root)]


def _assert_current(path: Path, expected: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    if _load_json_file(path) != expected:
        raise ValueError(f"stale {label}: regenerate P8 closure/P9 design package")


def verify_closure_and_design_packages(project_root: Path = PROJECT_ROOT) -> list[str]:
    record = validate_p8_closure_review_record(build_p8_closure_review_record(project_root))
    _assert_current(project_root / P8_CLOSURE_REVIEW_RECORD, record, "P8 closure review record")
    closure_manifest = validate_p8_closure_artifact_manifest(
        build_p8_closure_artifact_manifest(project_root),
        project_root,
    )
    _assert_current(project_root / P8_CLOSURE_ARTIFACT_MANIFEST, closure_manifest, "P8 closure artifact manifest")

    binding = validate_p9_p8_closure_binding_manifest(
        build_p9_p8_closure_binding_manifest(project_root)
    )
    _assert_current(project_root / P9_P8_CLOSURE_BINDING_MANIFEST, binding, "P9 P8 closure binding manifest")
    gate = validate_p9_next_authorization_gate_record(
        build_p9_next_authorization_gate_record(project_root)
    )
    _assert_current(project_root / P9_NEXT_AUTHORIZATION_GATE_RECORD, gate, "P9 next authorization gate record")
    design_manifest = validate_p9_design_artifact_manifest(
        build_p9_design_artifact_manifest(project_root),
        project_root,
    )
    _assert_current(project_root / P9_DESIGN_ARTIFACT_MANIFEST, design_manifest, "P9 design artifact manifest")

    lexicon = load_forbidden_claims_lexicon(project_root)
    for relpath in (*P8_CLOSURE_TEXT_PATHS, *P9_DESIGN_TEXT_PATHS):
        text = (project_root / relpath).read_text(encoding="utf-8")
        if not claim_text_passes(text, lexicon):
            raise ValueError(f"P8/P9 claim language drifted: {relpath}")

    return [
        "PASS p8_closure_review_record_current",
        "PASS p8_closure_artifact_manifest_current",
        "PASS p9_p8_closure_binding_manifest_current",
        "PASS p9_next_authorization_gate_record_current",
        "PASS p9_next_authorization_design_artifact_manifest_current",
        "PASS p8_closure_p9_design_no_new_execution",
        "PASS p8_closure_p9_design_claim_boundaries",
    ]
