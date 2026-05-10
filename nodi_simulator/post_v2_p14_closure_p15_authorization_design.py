"""P14 closure and P15 next-gate authorization-design helpers.

This module records the external P14 review result and creates the next
authorization-design gate. It does not run a solver, generate new solver output,
generate meshes, export operators, ingest measured/calibration data, or promote
routes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .post_v2_fifth_bounded_solver_lane_execution import (
    P14_ARTIFACT_MANIFEST,
    P14_EXECUTION_STAGE,
    P14_SOLVER_OUTPUT_MANIFEST,
    validate_artifact_manifest as validate_p14_artifact_manifest,
    validate_solver_output_manifest as validate_p14_solver_output_manifest,
)
from .realism_v2 import load_json_yaml
from .realism_v2_io import sha256_file, write_json_atomic
from .review_package import PROJECT_ROOT, claim_text_passes, load_forbidden_claims_lexicon


P14_CLOSURE_DIR = Path("results/post_v2_fifth_bounded_solver_lane_closure")
P14_CLOSURE_REGISTRY = "configs/realism_v2/fifth_bounded_solver_lane_closure_registry.yaml"
P14_CLOSURE_REPORT = "reports/115_EV_NODI_P14_fifth_bounded_solver_lane_closure_note.md"
P14_CLOSURE_README = P14_CLOSURE_DIR / "README.md"
P14_CLOSURE_REVIEW_RECORD = P14_CLOSURE_DIR / "p14_claude_review_closure_record.json"
P14_CLOSURE_ARTIFACT_MANIFEST = P14_CLOSURE_DIR / "p14_closure_artifact_manifest.json"

P15_DESIGN_DIR = Path("results/post_v2_sixth_bounded_lane_authorization_design")
P15_DESIGN_REGISTRY = "configs/realism_v2/sixth_bounded_lane_authorization_design_registry.yaml"
P15_DESIGN_REPORT = "reports/116_EV_NODI_P15_sixth_bounded_lane_authorization_design_plan.md"
P15_DESIGN_README = P15_DESIGN_DIR / "README.md"
P15_P14_CLOSURE_BINDING_MANIFEST = P15_DESIGN_DIR / "p15_p14_closure_binding_manifest.json"
P15_NEXT_AUTHORIZATION_GATE_RECORD = P15_DESIGN_DIR / "p15_next_authorization_gate_record.json"
P15_DESIGN_ARTIFACT_MANIFEST = P15_DESIGN_DIR / "p15_next_authorization_design_artifact_manifest.json"

P14_CLOSURE_STAGE = "P14_fifth_bounded_solver_lane_review_closure_complete"
P15_DESIGN_STAGE = "P15_sixth_bounded_lane_authorization_design_complete"
P14_CLOSURE_SCHEMA_VERSION = "ev_nodi_p14_fifth_bounded_solver_lane_closure_registry_v1"
P15_DESIGN_SCHEMA_VERSION = "ev_nodi_p15_sixth_bounded_lane_authorization_design_registry_v1"
P14_REVIEW_VERDICT = "NO P14 BLOCKERS FOUND"
P15_REQUIRED_FUTURE_AUTHORIZATION_PHRASE = "authorize sixth bounded solver lane execution"
P15_RANK_INSTABILITY_OBSERVATION = "p12_to_p14_rank_swap_trace_only"
P15_RANK_INSTABILITY_DELTA_VECTOR: tuple[int, ...] = (-1, 1, 0)
P15_RANK_INSTABILITY_ROLE = "record_as_rank_instability_not_route_preference"

P14_CLOSURE_TEXT_PATHS: tuple[str, ...] = (
    P14_CLOSURE_REGISTRY,
    P14_CLOSURE_REPORT,
    P14_CLOSURE_README.as_posix(),
    "docs/schemas/p14_closure_review_record_schema.md",
    "docs/schemas/p14_closure_artifact_manifest_schema.md",
)

P15_DESIGN_TEXT_PATHS: tuple[str, ...] = (
    P15_DESIGN_REGISTRY,
    P15_DESIGN_REPORT,
    P15_DESIGN_README.as_posix(),
    "docs/schemas/p15_next_authorization_gate_record_schema.md",
    "docs/schemas/p15_next_authorization_design_artifact_manifest_schema.md",
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
    "p9_authorization_design_scope_preserved",
    "p10_third_bounded_execution_scope_preserved",
    "p10_closure_scope_preserved",
    "p11_authorization_design_scope_preserved",
    "p12_fourth_bounded_execution_scope_preserved",
    "p12_closure_scope_preserved",
    "p13_authorization_design_scope_preserved",
    "p14_fifth_bounded_execution_scope_preserved",
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


def _rank_instability_payload() -> dict[str, Any]:
    return {
        "instability_observation": P15_RANK_INSTABILITY_OBSERVATION,
        "rank_delta_vector": list(P15_RANK_INSTABILITY_DELTA_VECTOR),
        "governance_role": P15_RANK_INSTABILITY_ROLE,
        "interpretation_boundary": "trace_only_instability_not_route_promotion_or_preference",
        **_guard_payload(),
    }


def _validate_rank_instability_governance(mapping: dict[str, Any], context: str) -> None:
    if mapping.get("instability_observation") != P15_RANK_INSTABILITY_OBSERVATION:
        raise ValueError(f"{context} rank instability observation drifted")
    if mapping.get("rank_delta_vector") != list(P15_RANK_INSTABILITY_DELTA_VECTOR):
        raise ValueError(f"{context} rank instability delta drifted")
    if mapping.get("governance_role") != P15_RANK_INSTABILITY_ROLE:
        raise ValueError(f"{context} rank instability role drifted")
    if (
        mapping.get("interpretation_boundary")
        != "trace_only_instability_not_route_promotion_or_preference"
    ):
        raise ValueError(f"{context} rank instability interpretation boundary drifted")
    _validate_guard_fields(mapping, context)


def load_p14_closure_registry(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return load_json_yaml(project_root / P14_CLOSURE_REGISTRY)


def load_p15_design_registry(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return load_json_yaml(project_root / P15_DESIGN_REGISTRY)


def validate_p14_closure_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema_version") != P14_CLOSURE_SCHEMA_VERSION:
        raise ValueError("unexpected P14 closure registry schema")
    if registry.get("stage") != P14_CLOSURE_STAGE:
        raise ValueError("unexpected P14 closure stage")
    if registry.get("closure_role") != "review_closure_only_no_new_execution":
        raise ValueError("P14 closure role drifted")
    if registry["review_evidence"]["claude_review_verdict"] != P14_REVIEW_VERDICT:
        raise ValueError("P14 review verdict drifted")
    if registry["review_evidence"]["p14_execution_stage"] != P14_EXECUTION_STAGE:
        raise ValueError("P14 execution stage binding drifted")
    _validate_guard_fields(registry, "P14 closure registry")
    _validate_guard_fields(registry["review_evidence"], "P14 closure review evidence")
    _validate_claim_boundary(registry["claim_governance"], "P14 closure registry", "p14_review_closure_only")
    for artifact in registry["planned_artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
    return registry


def validate_p15_design_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema_version") != P15_DESIGN_SCHEMA_VERSION:
        raise ValueError("unexpected P15 design registry schema")
    if registry.get("stage") != P15_DESIGN_STAGE:
        raise ValueError("unexpected P15 design stage")
    if registry.get("design_role") != "next_authorization_design_only_no_solver_execution":
        raise ValueError("P15 design role drifted")
    _validate_guard_fields(registry, "P15 design registry")
    _validate_claim_boundary(registry["claim_governance"], "P15 design registry", "next_authorization_design_only")
    gate = registry["future_authorization_gate_contract"]
    if gate["required_future_authorization_phrase"] != P15_REQUIRED_FUTURE_AUTHORIZATION_PHRASE:
        raise ValueError("P15 future authorization phrase drifted")
    if gate["future_authorization_phrase_already_received"] is not False:
        raise ValueError("P15 future authorization phrase must not be already received")
    if gate["authorization_gate_decision"] != "not_authorized_pending_explicit_future_request":
        raise ValueError("P15 authorization gate decision drifted")
    _validate_guard_fields(gate, "P15 future authorization gate")
    _validate_rank_instability_governance(
        registry["rank_instability_governance"],
        "P15 rank instability governance",
    )
    binding = registry["p14_closure_binding_contract"]
    if binding["p14_closure_record_path"] != P14_CLOSURE_REVIEW_RECORD.as_posix():
        raise ValueError("P15 P14 closure record path drifted")
    _validate_guard_fields(binding, "P15 P14 closure binding")
    for artifact in registry["planned_artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
    return registry


def build_p14_closure_review_record(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_p14_closure_registry(load_p14_closure_registry(project_root))
    validate_p14_solver_output_manifest(_load_json_file(project_root / P14_SOLVER_OUTPUT_MANIFEST))
    validate_p14_artifact_manifest(_load_json_file(project_root / P14_ARTIFACT_MANIFEST), project_root)
    return {
        "schema_version": "ev_nodi_p14_claude_review_closure_record_v1",
        "stage": P14_CLOSURE_STAGE,
        "record_role": "p14_review_closure_record",
        "claude_review_verdict": P14_REVIEW_VERDICT,
        "p14_execution_stage": P14_EXECUTION_STAGE,
        "p14_solver_output_manifest_path": P14_SOLVER_OUTPUT_MANIFEST.as_posix(),
        "p14_solver_output_manifest_sha256": sha256_file(project_root / P14_SOLVER_OUTPUT_MANIFEST),
        "p14_artifact_manifest_path": P14_ARTIFACT_MANIFEST.as_posix(),
        "p14_artifact_manifest_sha256": sha256_file(project_root / P14_ARTIFACT_MANIFEST),
        "closure_decision": "p14_closed_no_blockers_no_scope_expansion",
        **_guard_payload(),
    }


def validate_p14_closure_review_record(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("schema_version") != "ev_nodi_p14_claude_review_closure_record_v1":
        raise ValueError("unexpected P14 closure review record schema")
    if record["claude_review_verdict"] != P14_REVIEW_VERDICT:
        raise ValueError("P14 closure review verdict drifted")
    if record["p14_solver_output_manifest_path"] != P14_SOLVER_OUTPUT_MANIFEST.as_posix():
        raise ValueError("P14 closure output manifest path drifted")
    if record["p14_artifact_manifest_path"] != P14_ARTIFACT_MANIFEST.as_posix():
        raise ValueError("P14 closure artifact manifest path drifted")
    if record["closure_decision"] != "p14_closed_no_blockers_no_scope_expansion":
        raise ValueError("P14 closure decision drifted")
    _validate_guard_fields(record, "P14 closure review record")
    return record


def build_p15_p14_closure_binding_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_p15_design_registry(load_p15_design_registry(project_root))
    record = validate_p14_closure_review_record(_load_json_file(project_root / P14_CLOSURE_REVIEW_RECORD))
    return {
        "schema_version": "ev_nodi_p15_p14_closure_binding_manifest_v1",
        "stage": P15_DESIGN_STAGE,
        "manifest_role": "p14_closure_binding_for_next_authorization_design",
        "p14_closure_record_path": P14_CLOSURE_REVIEW_RECORD.as_posix(),
        "p14_closure_record_sha256": sha256_file(project_root / P14_CLOSURE_REVIEW_RECORD),
        "p14_review_verdict": record["claude_review_verdict"],
        "p14_execution_stage": record["p14_execution_stage"],
        **_guard_payload(),
    }


def validate_p15_p14_closure_binding_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p15_p14_closure_binding_manifest_v1":
        raise ValueError("unexpected P15 P14 closure binding manifest schema")
    if manifest["p14_closure_record_path"] != P14_CLOSURE_REVIEW_RECORD.as_posix():
        raise ValueError("P15 P14 closure record path drifted")
    if manifest["p14_review_verdict"] != P14_REVIEW_VERDICT:
        raise ValueError("P15 P14 review verdict drifted")
    _validate_guard_fields(manifest, "P15 P14 closure binding manifest")
    return manifest


def build_p15_next_authorization_gate_record(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_p15_design_registry(load_p15_design_registry(project_root))
    return {
        "schema_version": "ev_nodi_p15_next_authorization_gate_record_v1",
        "stage": P15_DESIGN_STAGE,
        "record_role": "future_sixth_bounded_lane_authorization_gate_record",
        "authorization_gate_decision": "not_authorized_pending_explicit_future_request",
        "required_future_authorization_phrase": P15_REQUIRED_FUTURE_AUTHORIZATION_PHRASE,
        "future_authorization_phrase_already_received": False,
        "explicit_next_execution_request_required": True,
        "minimum_later_phase_requirements": [
            "new user request containing the exact future authorization phrase",
            "separate branch or commit for any next execution lane",
            "bounded route/lane selection review before any output generation",
            "claim-boundary review before interpreting any generated solver output",
            "carry forward P12-to-P14 rank instability as trace-only governance",
        ],
        "rank_instability_governance": _rank_instability_payload(),
        **_guard_payload(),
    }


def validate_p15_next_authorization_gate_record(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("schema_version") != "ev_nodi_p15_next_authorization_gate_record_v1":
        raise ValueError("unexpected P15 next authorization gate record schema")
    if record["required_future_authorization_phrase"] != P15_REQUIRED_FUTURE_AUTHORIZATION_PHRASE:
        raise ValueError("P15 next authorization phrase drifted")
    if record["future_authorization_phrase_already_received"] is not False:
        raise ValueError("P15 future authorization phrase already received drifted")
    if record["authorization_gate_decision"] != "not_authorized_pending_explicit_future_request":
        raise ValueError("P15 next authorization gate decision drifted")
    _validate_rank_instability_governance(
        record["rank_instability_governance"],
        "P15 next authorization gate rank instability governance",
    )
    _validate_guard_fields(record, "P15 next authorization gate record")
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


def build_p14_closure_artifact_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_p14_closure_registry(load_p14_closure_registry(project_root))
    artifacts = [
        _artifact_entry(project_root, artifact, P14_CLOSURE_ARTIFACT_MANIFEST)
        for artifact in registry["planned_artifacts"]
    ]
    return {
        "schema_version": "ev_nodi_p14_closure_artifact_manifest_v1",
        "stage": P14_CLOSURE_STAGE,
        "manifest_role": "p14_closure_artifact_manifest",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "claim_boundary": {key: False for key in CLAIM_BOUNDARY_FALSE_FIELDS}
        | {"allowed_claim_level": "p14_review_closure_only"},
        **_guard_payload(),
    }


def validate_p14_closure_artifact_manifest(
    manifest: dict[str, Any],
    project_root: Path = PROJECT_ROOT,
    *,
    allow_missing_self_manifest: bool = False,
) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p14_closure_artifact_manifest_v1":
        raise ValueError("unexpected P14 closure artifact manifest schema")
    _validate_guard_fields(manifest, "P14 closure artifact manifest")
    _validate_claim_boundary(manifest["claim_boundary"], "P14 closure artifact manifest", "p14_review_closure_only")
    for artifact in manifest["artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
        is_self_manifest = artifact["path"] == P14_CLOSURE_ARTIFACT_MANIFEST.as_posix()
        if (
            not (project_root / artifact["path"]).is_file()
            and not (allow_missing_self_manifest and is_self_manifest)
        ):
            raise ValueError(f"P14 closure artifact missing: {artifact['path']}")
    return manifest


def build_p15_design_artifact_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_p15_design_registry(load_p15_design_registry(project_root))
    artifacts = [
        _artifact_entry(project_root, artifact, P15_DESIGN_ARTIFACT_MANIFEST)
        for artifact in registry["planned_artifacts"]
    ]
    return {
        "schema_version": "ev_nodi_p15_next_authorization_design_artifact_manifest_v1",
        "stage": P15_DESIGN_STAGE,
        "manifest_role": "p15_next_authorization_design_artifact_manifest",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "claim_boundary": {key: False for key in CLAIM_BOUNDARY_FALSE_FIELDS}
        | {"allowed_claim_level": "next_authorization_design_only"},
        "rank_instability_governance": _rank_instability_payload(),
        **_guard_payload(),
    }


def validate_p15_design_artifact_manifest(
    manifest: dict[str, Any],
    project_root: Path = PROJECT_ROOT,
    *,
    allow_missing_self_manifest: bool = False,
) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p15_next_authorization_design_artifact_manifest_v1":
        raise ValueError("unexpected P15 design artifact manifest schema")
    _validate_guard_fields(manifest, "P15 design artifact manifest")
    _validate_claim_boundary(manifest["claim_boundary"], "P15 design artifact manifest", "next_authorization_design_only")
    _validate_rank_instability_governance(
        manifest["rank_instability_governance"],
        "P15 design artifact manifest rank instability governance",
    )
    for artifact in manifest["artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
        is_self_manifest = artifact["path"] == P15_DESIGN_ARTIFACT_MANIFEST.as_posix()
        if (
            not (project_root / artifact["path"]).is_file()
            and not (allow_missing_self_manifest and is_self_manifest)
        ):
            raise ValueError(f"P15 design artifact missing: {artifact['path']}")
    return manifest


def write_p14_closure_package(project_root: Path = PROJECT_ROOT) -> list[Path]:
    record = validate_p14_closure_review_record(build_p14_closure_review_record(project_root))
    record_path = project_root / P14_CLOSURE_REVIEW_RECORD
    write_json_atomic(record_path, record, sort_keys=True)
    manifest = validate_p14_closure_artifact_manifest(
        build_p14_closure_artifact_manifest(project_root),
        project_root,
        allow_missing_self_manifest=True,
    )
    manifest_path = project_root / P14_CLOSURE_ARTIFACT_MANIFEST
    write_json_atomic(manifest_path, manifest, sort_keys=True)
    return [record_path, manifest_path]


def write_p15_design_package(project_root: Path = PROJECT_ROOT) -> list[Path]:
    binding = validate_p15_p14_closure_binding_manifest(
        build_p15_p14_closure_binding_manifest(project_root)
    )
    binding_path = project_root / P15_P14_CLOSURE_BINDING_MANIFEST
    write_json_atomic(binding_path, binding, sort_keys=True)
    gate = validate_p15_next_authorization_gate_record(
        build_p15_next_authorization_gate_record(project_root)
    )
    gate_path = project_root / P15_NEXT_AUTHORIZATION_GATE_RECORD
    write_json_atomic(gate_path, gate, sort_keys=True)
    manifest = validate_p15_design_artifact_manifest(
        build_p15_design_artifact_manifest(project_root),
        project_root,
        allow_missing_self_manifest=True,
    )
    manifest_path = project_root / P15_DESIGN_ARTIFACT_MANIFEST
    write_json_atomic(manifest_path, manifest, sort_keys=True)
    return [binding_path, gate_path, manifest_path]


def write_closure_and_design_packages(project_root: Path = PROJECT_ROOT) -> list[Path]:
    return [*write_p14_closure_package(project_root), *write_p15_design_package(project_root)]


def _assert_current(path: Path, expected: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    if _load_json_file(path) != expected:
        raise ValueError(f"stale {label}: regenerate P14 closure/P15 design package")


def verify_closure_and_design_packages(project_root: Path = PROJECT_ROOT) -> list[str]:
    record = validate_p14_closure_review_record(build_p14_closure_review_record(project_root))
    _assert_current(project_root / P14_CLOSURE_REVIEW_RECORD, record, "P14 closure review record")
    closure_manifest = validate_p14_closure_artifact_manifest(
        build_p14_closure_artifact_manifest(project_root),
        project_root,
    )
    _assert_current(project_root / P14_CLOSURE_ARTIFACT_MANIFEST, closure_manifest, "P14 closure artifact manifest")

    binding = validate_p15_p14_closure_binding_manifest(
        build_p15_p14_closure_binding_manifest(project_root)
    )
    _assert_current(project_root / P15_P14_CLOSURE_BINDING_MANIFEST, binding, "P15 P14 closure binding manifest")
    gate = validate_p15_next_authorization_gate_record(
        build_p15_next_authorization_gate_record(project_root)
    )
    _assert_current(project_root / P15_NEXT_AUTHORIZATION_GATE_RECORD, gate, "P15 next authorization gate record")
    design_manifest = validate_p15_design_artifact_manifest(
        build_p15_design_artifact_manifest(project_root),
        project_root,
    )
    _assert_current(project_root / P15_DESIGN_ARTIFACT_MANIFEST, design_manifest, "P15 design artifact manifest")

    lexicon = load_forbidden_claims_lexicon(project_root)
    for relpath in (*P14_CLOSURE_TEXT_PATHS, *P15_DESIGN_TEXT_PATHS):
        text = (project_root / relpath).read_text(encoding="utf-8")
        if not claim_text_passes(text, lexicon):
            raise ValueError(f"P14/P15 claim language drifted: {relpath}")

    return [
        "PASS p14_closure_review_record_current",
        "PASS p14_closure_artifact_manifest_current",
        "PASS p15_p14_closure_binding_manifest_current",
        "PASS p15_next_authorization_gate_record_current",
        "PASS p15_next_authorization_design_artifact_manifest_current",
        "PASS p14_closure_p15_design_no_new_execution",
        "PASS p14_closure_p15_design_claim_boundaries",
    ]
