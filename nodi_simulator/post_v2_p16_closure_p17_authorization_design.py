"""P16 closure and P17 next-gate authorization-design helpers.

This module records the external P16 review result and creates the next
authorization-design gate. It does not run a solver, generate new solver output,
generate meshes, export operators, ingest measured/calibration data, or promote
routes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .post_v2_sixth_bounded_solver_lane_execution import (
    P16_ARTIFACT_MANIFEST,
    P16_EXECUTION_STAGE,
    P16_SOLVER_OUTPUT_MANIFEST,
    validate_artifact_manifest as validate_p16_artifact_manifest,
    validate_solver_output_manifest as validate_p16_solver_output_manifest,
)
from .realism_v2 import load_json_yaml
from .realism_v2_io import sha256_file, write_json_atomic
from .review_package import PROJECT_ROOT, claim_text_passes, load_forbidden_claims_lexicon


P16_CLOSURE_DIR = Path("results/post_v2_sixth_bounded_solver_lane_closure")
P16_CLOSURE_REGISTRY = "configs/realism_v2/sixth_bounded_solver_lane_closure_registry.yaml"
P16_CLOSURE_REPORT = "reports/118_EV_NODI_P16_sixth_bounded_solver_lane_closure_note.md"
P16_CLOSURE_README = P16_CLOSURE_DIR / "README.md"
P16_CLOSURE_REVIEW_RECORD = P16_CLOSURE_DIR / "p16_claude_review_closure_record.json"
P16_CLOSURE_ARTIFACT_MANIFEST = P16_CLOSURE_DIR / "p16_closure_artifact_manifest.json"

P17_DESIGN_DIR = Path("results/post_v2_seventh_bounded_lane_authorization_design")
P17_DESIGN_REGISTRY = "configs/realism_v2/seventh_bounded_lane_authorization_design_registry.yaml"
P17_DESIGN_REPORT = "reports/119_EV_NODI_P17_seventh_bounded_lane_authorization_design_plan.md"
P17_DESIGN_README = P17_DESIGN_DIR / "README.md"
P17_P16_CLOSURE_BINDING_MANIFEST = P17_DESIGN_DIR / "p17_p16_closure_binding_manifest.json"
P17_NEXT_AUTHORIZATION_GATE_RECORD = P17_DESIGN_DIR / "p17_next_authorization_gate_record.json"
P17_DESIGN_ARTIFACT_MANIFEST = P17_DESIGN_DIR / "p17_next_authorization_design_artifact_manifest.json"

P16_CLOSURE_STAGE = "P16_sixth_bounded_solver_lane_review_closure_complete"
P17_DESIGN_STAGE = "P17_seventh_bounded_lane_authorization_design_complete"
P16_CLOSURE_SCHEMA_VERSION = "ev_nodi_p16_sixth_bounded_solver_lane_closure_registry_v1"
P17_DESIGN_SCHEMA_VERSION = "ev_nodi_p17_seventh_bounded_lane_authorization_design_registry_v1"
P16_REVIEW_VERDICT = "NO P16 BLOCKERS FOUND"
P17_REQUIRED_FUTURE_AUTHORIZATION_PHRASE = "authorize seventh bounded solver lane execution"
P17_RANK_INSTABILITY_OBSERVATION = "bounded_lane_rank_instability_recurrence_trace_only"
P17_RANK_INSTABILITY_DELTA_VECTOR: tuple[int, ...] = (-1, 1, 0)
P17_RANK_INSTABILITY_ROLE = "record_recurring_rank_instability_not_route_preference"
P17_REPORT_NUMBERING_NOTE = "stage_p17_uses_report_119_under_current_sequential_report_numbering"

P16_CLOSURE_TEXT_PATHS: tuple[str, ...] = (
    P16_CLOSURE_REGISTRY,
    P16_CLOSURE_REPORT,
    P16_CLOSURE_README.as_posix(),
    "docs/schemas/p16_closure_review_record_schema.md",
    "docs/schemas/p16_closure_artifact_manifest_schema.md",
)

P17_DESIGN_TEXT_PATHS: tuple[str, ...] = (
    P17_DESIGN_REGISTRY,
    P17_DESIGN_REPORT,
    P17_DESIGN_README.as_posix(),
    "docs/schemas/p17_next_authorization_gate_record_schema.md",
    "docs/schemas/p17_next_authorization_design_artifact_manifest_schema.md",
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
    "p14_closure_scope_preserved",
    "p15_authorization_design_scope_preserved",
    "p16_sixth_bounded_execution_scope_preserved",
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
        "instability_observation": P17_RANK_INSTABILITY_OBSERVATION,
        "rank_delta_vector": list(P17_RANK_INSTABILITY_DELTA_VECTOR),
        "recurrence_events": [
            {
                "event_id": "p12_to_p14_main_660_swap",
                "rank_delta_vector": list(P17_RANK_INSTABILITY_DELTA_VECTOR),
                "interpretation_role": "trace_only_not_route_preference",
            },
            {
                "event_id": "p14_to_p16_main_660_swap",
                "rank_delta_vector": list(P17_RANK_INSTABILITY_DELTA_VECTOR),
                "interpretation_role": "trace_only_not_route_preference",
            },
        ],
        "governance_role": P17_RANK_INSTABILITY_ROLE,
        "interpretation_boundary": "trace_only_recurring_instability_not_route_promotion_or_preference",
        **_guard_payload(),
    }


def _validate_rank_instability_governance(mapping: dict[str, Any], context: str) -> None:
    if mapping.get("instability_observation") != P17_RANK_INSTABILITY_OBSERVATION:
        raise ValueError(f"{context} rank instability observation drifted")
    if mapping.get("rank_delta_vector") != list(P17_RANK_INSTABILITY_DELTA_VECTOR):
        raise ValueError(f"{context} rank instability delta drifted")
    events = mapping.get("recurrence_events")
    if not isinstance(events, list) or len(events) != 2:
        raise ValueError(f"{context} rank instability recurrence events drifted")
    if [event.get("event_id") for event in events] != [
        "p12_to_p14_main_660_swap",
        "p14_to_p16_main_660_swap",
    ]:
        raise ValueError(f"{context} rank instability recurrence event ids drifted")
    for event in events:
        if event.get("rank_delta_vector") != list(P17_RANK_INSTABILITY_DELTA_VECTOR):
            raise ValueError(f"{context} rank instability recurrence delta drifted")
        if event.get("interpretation_role") != "trace_only_not_route_preference":
            raise ValueError(f"{context} rank instability recurrence role drifted")
    if mapping.get("governance_role") != P17_RANK_INSTABILITY_ROLE:
        raise ValueError(f"{context} rank instability role drifted")
    if (
        mapping.get("interpretation_boundary")
        != "trace_only_recurring_instability_not_route_promotion_or_preference"
    ):
        raise ValueError(f"{context} rank instability interpretation boundary drifted")
    _validate_guard_fields(mapping, context)


def _report_numbering_payload() -> dict[str, Any]:
    return {
        "note_id": P17_REPORT_NUMBERING_NOTE,
        "stage": "P17",
        "report_path": P17_DESIGN_REPORT,
        "numbering_role": "sequential_report_numbering_not_stage_numbering",
        **_guard_payload(),
    }


def _validate_report_numbering_governance(mapping: dict[str, Any], context: str) -> None:
    if mapping.get("note_id") != P17_REPORT_NUMBERING_NOTE:
        raise ValueError(f"{context} report numbering note drifted")
    if mapping.get("stage") != "P17":
        raise ValueError(f"{context} report numbering stage drifted")
    if mapping.get("report_path") != P17_DESIGN_REPORT:
        raise ValueError(f"{context} report numbering path drifted")
    if mapping.get("numbering_role") != "sequential_report_numbering_not_stage_numbering":
        raise ValueError(f"{context} report numbering role drifted")
    _validate_guard_fields(mapping, context)


def load_p16_closure_registry(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return load_json_yaml(project_root / P16_CLOSURE_REGISTRY)


def load_p17_design_registry(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return load_json_yaml(project_root / P17_DESIGN_REGISTRY)


def validate_p16_closure_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema_version") != P16_CLOSURE_SCHEMA_VERSION:
        raise ValueError("unexpected P16 closure registry schema")
    if registry.get("stage") != P16_CLOSURE_STAGE:
        raise ValueError("unexpected P16 closure stage")
    if registry.get("closure_role") != "review_closure_only_no_new_execution":
        raise ValueError("P16 closure role drifted")
    if registry["review_evidence"]["claude_review_verdict"] != P16_REVIEW_VERDICT:
        raise ValueError("P16 review verdict drifted")
    if registry["review_evidence"]["p16_execution_stage"] != P16_EXECUTION_STAGE:
        raise ValueError("P16 execution stage binding drifted")
    _validate_guard_fields(registry, "P16 closure registry")
    _validate_guard_fields(registry["review_evidence"], "P16 closure review evidence")
    _validate_claim_boundary(registry["claim_governance"], "P16 closure registry", "p16_review_closure_only")
    for artifact in registry["planned_artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
    return registry


def validate_p17_design_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema_version") != P17_DESIGN_SCHEMA_VERSION:
        raise ValueError("unexpected P17 design registry schema")
    if registry.get("stage") != P17_DESIGN_STAGE:
        raise ValueError("unexpected P17 design stage")
    if registry.get("design_role") != "next_authorization_design_only_no_solver_execution":
        raise ValueError("P17 design role drifted")
    _validate_guard_fields(registry, "P17 design registry")
    _validate_claim_boundary(registry["claim_governance"], "P17 design registry", "next_authorization_design_only")
    gate = registry["future_authorization_gate_contract"]
    if gate["required_future_authorization_phrase"] != P17_REQUIRED_FUTURE_AUTHORIZATION_PHRASE:
        raise ValueError("P17 future authorization phrase drifted")
    if gate["future_authorization_phrase_already_received"] is not False:
        raise ValueError("P17 future authorization phrase must not be already received")
    if gate["authorization_gate_decision"] != "not_authorized_pending_explicit_future_request":
        raise ValueError("P17 authorization gate decision drifted")
    _validate_guard_fields(gate, "P17 future authorization gate")
    _validate_rank_instability_governance(
        registry["rank_instability_governance"],
        "P17 rank instability governance",
    )
    _validate_report_numbering_governance(
        registry["report_numbering_governance"],
        "P17 report numbering governance",
    )
    binding = registry["p16_closure_binding_contract"]
    if binding["p16_closure_record_path"] != P16_CLOSURE_REVIEW_RECORD.as_posix():
        raise ValueError("P17 P16 closure record path drifted")
    _validate_guard_fields(binding, "P17 P16 closure binding")
    for artifact in registry["planned_artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
    return registry


def build_p16_closure_review_record(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_p16_closure_registry(load_p16_closure_registry(project_root))
    validate_p16_solver_output_manifest(_load_json_file(project_root / P16_SOLVER_OUTPUT_MANIFEST))
    validate_p16_artifact_manifest(_load_json_file(project_root / P16_ARTIFACT_MANIFEST), project_root)
    return {
        "schema_version": "ev_nodi_p16_claude_review_closure_record_v1",
        "stage": P16_CLOSURE_STAGE,
        "record_role": "p16_review_closure_record",
        "claude_review_verdict": P16_REVIEW_VERDICT,
        "p16_execution_stage": P16_EXECUTION_STAGE,
        "p16_solver_output_manifest_path": P16_SOLVER_OUTPUT_MANIFEST.as_posix(),
        "p16_solver_output_manifest_sha256": sha256_file(project_root / P16_SOLVER_OUTPUT_MANIFEST),
        "p16_artifact_manifest_path": P16_ARTIFACT_MANIFEST.as_posix(),
        "p16_artifact_manifest_sha256": sha256_file(project_root / P16_ARTIFACT_MANIFEST),
        "closure_decision": "p16_closed_no_blockers_no_scope_expansion",
        **_guard_payload(),
    }


def validate_p16_closure_review_record(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("schema_version") != "ev_nodi_p16_claude_review_closure_record_v1":
        raise ValueError("unexpected P16 closure review record schema")
    if record["claude_review_verdict"] != P16_REVIEW_VERDICT:
        raise ValueError("P16 closure review verdict drifted")
    if record["p16_solver_output_manifest_path"] != P16_SOLVER_OUTPUT_MANIFEST.as_posix():
        raise ValueError("P16 closure output manifest path drifted")
    if record["p16_artifact_manifest_path"] != P16_ARTIFACT_MANIFEST.as_posix():
        raise ValueError("P16 closure artifact manifest path drifted")
    if record["closure_decision"] != "p16_closed_no_blockers_no_scope_expansion":
        raise ValueError("P16 closure decision drifted")
    _validate_guard_fields(record, "P16 closure review record")
    return record


def build_p17_p16_closure_binding_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_p17_design_registry(load_p17_design_registry(project_root))
    record = validate_p16_closure_review_record(_load_json_file(project_root / P16_CLOSURE_REVIEW_RECORD))
    return {
        "schema_version": "ev_nodi_p17_p16_closure_binding_manifest_v1",
        "stage": P17_DESIGN_STAGE,
        "manifest_role": "p16_closure_binding_for_next_authorization_design",
        "p16_closure_record_path": P16_CLOSURE_REVIEW_RECORD.as_posix(),
        "p16_closure_record_sha256": sha256_file(project_root / P16_CLOSURE_REVIEW_RECORD),
        "p16_review_verdict": record["claude_review_verdict"],
        "p16_execution_stage": record["p16_execution_stage"],
        **_guard_payload(),
    }


def validate_p17_p16_closure_binding_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p17_p16_closure_binding_manifest_v1":
        raise ValueError("unexpected P17 P16 closure binding manifest schema")
    if manifest["p16_closure_record_path"] != P16_CLOSURE_REVIEW_RECORD.as_posix():
        raise ValueError("P17 P16 closure record path drifted")
    if manifest["p16_review_verdict"] != P16_REVIEW_VERDICT:
        raise ValueError("P17 P16 review verdict drifted")
    _validate_guard_fields(manifest, "P17 P16 closure binding manifest")
    return manifest


def build_p17_next_authorization_gate_record(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_p17_design_registry(load_p17_design_registry(project_root))
    return {
        "schema_version": "ev_nodi_p17_next_authorization_gate_record_v1",
        "stage": P17_DESIGN_STAGE,
        "record_role": "future_seventh_bounded_lane_authorization_gate_record",
        "authorization_gate_decision": "not_authorized_pending_explicit_future_request",
        "required_future_authorization_phrase": P17_REQUIRED_FUTURE_AUTHORIZATION_PHRASE,
        "future_authorization_phrase_already_received": False,
        "explicit_next_execution_request_required": True,
        "minimum_later_phase_requirements": [
            "new user request containing the exact future authorization phrase",
            "separate branch or commit for any next execution lane",
            "bounded route/lane selection review before any output generation",
            "claim-boundary review before interpreting any generated solver output",
            "carry forward recurring bounded-lane rank instability as trace-only governance",
        ],
        "rank_instability_governance": _rank_instability_payload(),
        "report_numbering_governance": _report_numbering_payload(),
        **_guard_payload(),
    }


def validate_p17_next_authorization_gate_record(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("schema_version") != "ev_nodi_p17_next_authorization_gate_record_v1":
        raise ValueError("unexpected P17 next authorization gate record schema")
    if record["required_future_authorization_phrase"] != P17_REQUIRED_FUTURE_AUTHORIZATION_PHRASE:
        raise ValueError("P17 next authorization phrase drifted")
    if record["future_authorization_phrase_already_received"] is not False:
        raise ValueError("P17 future authorization phrase already received drifted")
    if record["authorization_gate_decision"] != "not_authorized_pending_explicit_future_request":
        raise ValueError("P17 next authorization gate decision drifted")
    _validate_rank_instability_governance(
        record["rank_instability_governance"],
        "P17 next authorization gate rank instability governance",
    )
    _validate_report_numbering_governance(
        record["report_numbering_governance"],
        "P17 next authorization gate report numbering governance",
    )
    _validate_guard_fields(record, "P17 next authorization gate record")
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


def build_p16_closure_artifact_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_p16_closure_registry(load_p16_closure_registry(project_root))
    artifacts = [
        _artifact_entry(project_root, artifact, P16_CLOSURE_ARTIFACT_MANIFEST)
        for artifact in registry["planned_artifacts"]
    ]
    return {
        "schema_version": "ev_nodi_p16_closure_artifact_manifest_v1",
        "stage": P16_CLOSURE_STAGE,
        "manifest_role": "p16_closure_artifact_manifest",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "claim_boundary": {key: False for key in CLAIM_BOUNDARY_FALSE_FIELDS}
        | {"allowed_claim_level": "p16_review_closure_only"},
        **_guard_payload(),
    }


def validate_p16_closure_artifact_manifest(
    manifest: dict[str, Any],
    project_root: Path = PROJECT_ROOT,
    *,
    allow_missing_self_manifest: bool = False,
) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p16_closure_artifact_manifest_v1":
        raise ValueError("unexpected P16 closure artifact manifest schema")
    _validate_guard_fields(manifest, "P16 closure artifact manifest")
    _validate_claim_boundary(manifest["claim_boundary"], "P16 closure artifact manifest", "p16_review_closure_only")
    for artifact in manifest["artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
        is_self_manifest = artifact["path"] == P16_CLOSURE_ARTIFACT_MANIFEST.as_posix()
        if (
            not (project_root / artifact["path"]).is_file()
            and not (allow_missing_self_manifest and is_self_manifest)
        ):
            raise ValueError(f"P16 closure artifact missing: {artifact['path']}")
    return manifest


def build_p17_design_artifact_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_p17_design_registry(load_p17_design_registry(project_root))
    artifacts = [
        _artifact_entry(project_root, artifact, P17_DESIGN_ARTIFACT_MANIFEST)
        for artifact in registry["planned_artifacts"]
    ]
    return {
        "schema_version": "ev_nodi_p17_next_authorization_design_artifact_manifest_v1",
        "stage": P17_DESIGN_STAGE,
        "manifest_role": "p17_next_authorization_design_artifact_manifest",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "claim_boundary": {key: False for key in CLAIM_BOUNDARY_FALSE_FIELDS}
        | {"allowed_claim_level": "next_authorization_design_only"},
        "rank_instability_governance": _rank_instability_payload(),
        "report_numbering_governance": _report_numbering_payload(),
        **_guard_payload(),
    }


def validate_p17_design_artifact_manifest(
    manifest: dict[str, Any],
    project_root: Path = PROJECT_ROOT,
    *,
    allow_missing_self_manifest: bool = False,
) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p17_next_authorization_design_artifact_manifest_v1":
        raise ValueError("unexpected P17 design artifact manifest schema")
    _validate_guard_fields(manifest, "P17 design artifact manifest")
    _validate_claim_boundary(manifest["claim_boundary"], "P17 design artifact manifest", "next_authorization_design_only")
    _validate_rank_instability_governance(
        manifest["rank_instability_governance"],
        "P17 design artifact manifest rank instability governance",
    )
    _validate_report_numbering_governance(
        manifest["report_numbering_governance"],
        "P17 design artifact manifest report numbering governance",
    )
    for artifact in manifest["artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
        is_self_manifest = artifact["path"] == P17_DESIGN_ARTIFACT_MANIFEST.as_posix()
        if (
            not (project_root / artifact["path"]).is_file()
            and not (allow_missing_self_manifest and is_self_manifest)
        ):
            raise ValueError(f"P17 design artifact missing: {artifact['path']}")
    return manifest


def write_p16_closure_package(project_root: Path = PROJECT_ROOT) -> list[Path]:
    record = validate_p16_closure_review_record(build_p16_closure_review_record(project_root))
    record_path = project_root / P16_CLOSURE_REVIEW_RECORD
    write_json_atomic(record_path, record, sort_keys=True)
    manifest = validate_p16_closure_artifact_manifest(
        build_p16_closure_artifact_manifest(project_root),
        project_root,
        allow_missing_self_manifest=True,
    )
    manifest_path = project_root / P16_CLOSURE_ARTIFACT_MANIFEST
    write_json_atomic(manifest_path, manifest, sort_keys=True)
    return [record_path, manifest_path]


def write_p17_design_package(project_root: Path = PROJECT_ROOT) -> list[Path]:
    binding = validate_p17_p16_closure_binding_manifest(
        build_p17_p16_closure_binding_manifest(project_root)
    )
    binding_path = project_root / P17_P16_CLOSURE_BINDING_MANIFEST
    write_json_atomic(binding_path, binding, sort_keys=True)
    gate = validate_p17_next_authorization_gate_record(
        build_p17_next_authorization_gate_record(project_root)
    )
    gate_path = project_root / P17_NEXT_AUTHORIZATION_GATE_RECORD
    write_json_atomic(gate_path, gate, sort_keys=True)
    manifest = validate_p17_design_artifact_manifest(
        build_p17_design_artifact_manifest(project_root),
        project_root,
        allow_missing_self_manifest=True,
    )
    manifest_path = project_root / P17_DESIGN_ARTIFACT_MANIFEST
    write_json_atomic(manifest_path, manifest, sort_keys=True)
    return [binding_path, gate_path, manifest_path]


def write_closure_and_design_packages(project_root: Path = PROJECT_ROOT) -> list[Path]:
    return [*write_p16_closure_package(project_root), *write_p17_design_package(project_root)]


def _assert_current(path: Path, expected: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    if _load_json_file(path) != expected:
        raise ValueError(f"stale {label}: regenerate P16 closure/P17 design package")


def verify_closure_and_design_packages(project_root: Path = PROJECT_ROOT) -> list[str]:
    record = validate_p16_closure_review_record(build_p16_closure_review_record(project_root))
    _assert_current(project_root / P16_CLOSURE_REVIEW_RECORD, record, "P16 closure review record")
    closure_manifest = validate_p16_closure_artifact_manifest(
        build_p16_closure_artifact_manifest(project_root),
        project_root,
    )
    _assert_current(project_root / P16_CLOSURE_ARTIFACT_MANIFEST, closure_manifest, "P16 closure artifact manifest")

    binding = validate_p17_p16_closure_binding_manifest(
        build_p17_p16_closure_binding_manifest(project_root)
    )
    _assert_current(project_root / P17_P16_CLOSURE_BINDING_MANIFEST, binding, "P17 P16 closure binding manifest")
    gate = validate_p17_next_authorization_gate_record(
        build_p17_next_authorization_gate_record(project_root)
    )
    _assert_current(project_root / P17_NEXT_AUTHORIZATION_GATE_RECORD, gate, "P17 next authorization gate record")
    design_manifest = validate_p17_design_artifact_manifest(
        build_p17_design_artifact_manifest(project_root),
        project_root,
    )
    _assert_current(project_root / P17_DESIGN_ARTIFACT_MANIFEST, design_manifest, "P17 design artifact manifest")

    lexicon = load_forbidden_claims_lexicon(project_root)
    for relpath in (*P16_CLOSURE_TEXT_PATHS, *P17_DESIGN_TEXT_PATHS):
        text = (project_root / relpath).read_text(encoding="utf-8")
        if not claim_text_passes(text, lexicon):
            raise ValueError(f"P16/P17 claim language drifted: {relpath}")

    return [
        "PASS p16_closure_review_record_current",
        "PASS p16_closure_artifact_manifest_current",
        "PASS p17_p16_closure_binding_manifest_current",
        "PASS p17_next_authorization_gate_record_current",
        "PASS p17_next_authorization_design_artifact_manifest_current",
        "PASS p16_closure_p17_design_no_new_execution",
        "PASS p16_closure_p17_design_claim_boundaries",
    ]
