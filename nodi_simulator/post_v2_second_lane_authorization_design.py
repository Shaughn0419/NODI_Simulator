"""P7 second-lane bounded solver authorization-design helpers.

This module is design/governance only. It binds P6 trace artifacts as prior
evidence, but it does not run a solver, generate solver output, generate meshes,
export operators, ingest measured/calibration data, or promote routes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .post_v2_minimal_bounded_solver_execution import (
    P6_ARTIFACT_MANIFEST,
    P6_P5_BINDING_MANIFEST,
    P6_SOLVER_OUTPUT_CSV,
    P6_SOLVER_OUTPUT_MANIFEST,
    validate_artifact_manifest as validate_p6_artifact_manifest,
    validate_p5_binding_manifest as validate_p6_p5_binding_manifest,
    validate_solver_output_manifest as validate_p6_solver_output_manifest,
)
from .realism_v2 import load_json_yaml
from .realism_v2_io import sha256_file, write_json_atomic
from .review_package import (
    PROJECT_ROOT,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)


P7_DESIGN_DIR = Path("results/post_v2_second_lane_authorization_design")
P7_DESIGN_REGISTRY = "configs/realism_v2/second_lane_authorization_design_registry.yaml"
P7_DESIGN_PLAN = "reports/104_EV_NODI_P7_second_lane_authorization_design_plan.md"
P7_DESIGN_README = P7_DESIGN_DIR / "README.md"
P7_P6_EVIDENCE_BINDING_MANIFEST = (
    P7_DESIGN_DIR / "second_lane_authorization_design_p6_evidence_binding_manifest.json"
)
P7_AUTHORIZATION_GATE_RECORD = (
    P7_DESIGN_DIR / "second_lane_authorization_design_authorization_gate_record.json"
)
P7_CANDIDATE_LANE_CONTRACT_MANIFEST = (
    P7_DESIGN_DIR / "second_lane_authorization_design_candidate_lane_contract_manifest.json"
)
P7_ARTIFACT_MANIFEST = (
    P7_DESIGN_DIR / "second_lane_authorization_design_artifact_manifest.json"
)

P7_TEXT_PATHS: tuple[str, ...] = (
    P7_DESIGN_REGISTRY,
    P7_DESIGN_PLAN,
    P7_DESIGN_README.as_posix(),
    "docs/schemas/second_lane_authorization_design_p6_evidence_binding_manifest_schema.md",
    "docs/schemas/second_lane_authorization_design_authorization_gate_record_schema.md",
    "docs/schemas/second_lane_authorization_design_candidate_lane_contract_schema.md",
    "docs/schemas/second_lane_authorization_design_artifact_manifest_schema.md",
)

P7_DESIGN_STAGE = "P7_second_lane_authorization_design_complete"
P7_DESIGN_SCHEMA_VERSION = "ev_nodi_p7_second_lane_authorization_design_registry_v1"
P7_CANDIDATE_LANE_ID = "second_bounded_solver_lane_candidate_design_only"
P7_REQUIRED_FUTURE_AUTHORIZATION_PHRASE = "authorize second bounded solver lane execution"
P7_MINIMUM_LATER_PHASE_REQUIREMENTS: tuple[str, ...] = (
    "new user request containing only the required future authorization phrase for the next execution lane",
    "separate execution branch or commit that changes the execution authorization decision",
    "bounded route/lane selection review before any output generation",
    "claim-boundary review before interpreting any generated solver output",
)

P6_REQUIRED_EVIDENCE_PATHS: tuple[str, ...] = (
    P6_P5_BINDING_MANIFEST.as_posix(),
    P6_SOLVER_OUTPUT_CSV.as_posix(),
    P6_SOLVER_OUTPUT_MANIFEST.as_posix(),
    P6_ARTIFACT_MANIFEST.as_posix(),
)

TOP_LEVEL_FALSE_FIELDS: tuple[str, ...] = (
    "calibrated_claim_allowed",
    "p0_release_conclusion_changed",
    "physical_solver_execution_authorized",
    "second_bounded_solver_lane_execution_authorized",
    "solver_output_generated",
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
)

TOP_LEVEL_TRUE_FIELDS: tuple[str, ...] = (
    "p1_surrogate_risk_role_preserved",
    "p2_readiness_scope_preserved",
    "p3_pilot_design_scope_preserved",
    "p4_dry_run_preflight_scope_preserved",
    "p5_authorization_gate_scope_preserved",
    "p6_minimal_execution_scope_preserved",
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

ALLOWED_TRUE_AUTHORITY_FIELDS: frozenset[str] = frozenset(
    {
        "p6_evidence_binding_manifest_generation_authorized",
        "authorization_gate_record_generation_authorized",
        "candidate_lane_contract_manifest_generation_authorized",
        "artifact_manifest_generation_authorized",
        "verifier_authorized",
    }
)

REQUIRED_FALSE_AUTHORITY_FIELDS: frozenset[str] = frozenset(
    {
        "physical_solver_execution_authorized",
        "second_bounded_solver_lane_execution_authorized",
        "solver_output_generation_authorized",
        "full_wave_solver_execution_authorized",
        "vector_solver_execution_authorized",
        "roughness_leakage_simulation_authorized",
        "transport_residence_time_simulation_authorized",
        "new_mesh_generation_authorized",
        "operator_export_generation_authorized",
        "measured_data_ingest_authorized",
        "calibration_data_ingest_authorized",
        "route_promotion_authorized",
        "main_660_redefinition_authorized",
        "optional_660_W900_D1400_redefines_main_660",
    }
)

REQUIRED_AUTHORITY_FIELDS = ALLOWED_TRUE_AUTHORITY_FIELDS | REQUIRED_FALSE_AUTHORITY_FIELDS


def load_design_registry(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return load_json_yaml(project_root / P7_DESIGN_REGISTRY)


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


def _validate_guard_fields(mapping: dict[str, Any], context: str) -> None:
    _require_false(mapping, TOP_LEVEL_FALSE_FIELDS, context)
    _require_true(mapping, TOP_LEVEL_TRUE_FIELDS, context)


def _validate_claim_boundary(claims: dict[str, Any], context: str) -> None:
    _require_false(claims, CLAIM_BOUNDARY_FALSE_FIELDS, context)
    if claims.get("allowed_claim_level") != "second_lane_authorization_design_only":
        raise ValueError(f"{context} claim level drifted")


def _validate_implementation_authority(authority: dict[str, Any]) -> None:
    if set(authority) != REQUIRED_AUTHORITY_FIELDS:
        raise ValueError("P7 implementation authority field set drifted")
    for key, value in authority.items():
        expected = key in ALLOWED_TRUE_AUTHORITY_FIELDS
        if value is not expected:
            raise ValueError(f"P7 implementation authority drifted: {key}")


def _validate_future_authorization_gate(gate: dict[str, Any], context: str) -> None:
    if gate.get("required_future_authorization_phrase") != P7_REQUIRED_FUTURE_AUTHORIZATION_PHRASE:
        raise ValueError(f"{context} future authorization phrase drifted")
    if gate.get("future_authorization_phrase_already_received") is not False:
        raise ValueError(f"{context} must keep future_authorization_phrase_already_received=false")
    if gate.get("current_prompt_authorizes_second_lane_execution") is not False:
        raise ValueError(f"{context} must keep current_prompt_authorizes_second_lane_execution=false")
    if gate.get("explicit_second_lane_execution_request_required") is not True:
        raise ValueError(f"{context} must require explicit second-lane execution request")
    if gate.get("authorization_gate_decision") != "not_authorized_pending_explicit_future_request":
        raise ValueError(f"{context} authorization gate decision drifted")
    _validate_guard_fields(gate, context)


def _validate_p6_evidence_use_contract(contract: dict[str, Any], context: str) -> None:
    if contract.get("p6_trace_output_role") != (
        "prior_trace_only_rank_pairwise_order_evidence_not_calibration_or_promotion"
    ):
        raise ValueError(f"{context} P6 trace output role drifted")
    for key in (
        "p6_trace_used_as_calibrated_prediction",
        "p6_trace_used_as_physical_calibration",
        "p6_trace_used_as_route_promotion_evidence",
        "p6_trace_used_as_snr_lod_concentration_specificity_evidence",
    ):
        if contract.get(key) is not False:
            raise ValueError(f"{context} must keep {key}=false")
    _validate_guard_fields(contract, context)


def validate_design_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema_version") != P7_DESIGN_SCHEMA_VERSION:
        raise ValueError("unexpected P7 design registry schema")
    if registry.get("stage") != P7_DESIGN_STAGE:
        raise ValueError("unexpected P7 design stage")
    if registry.get("design_role") != "authorization_design_only_no_solver_execution":
        raise ValueError("P7 design role drifted")
    _validate_guard_fields(registry, "P7 registry")
    _validate_implementation_authority(registry["implementation_authority"])
    _validate_claim_boundary(registry["claim_governance"], "P7 registry")

    p6_binding = registry["p6_evidence_binding_contract"]
    if tuple(p6_binding["required_p6_artifact_paths"]) != P6_REQUIRED_EVIDENCE_PATHS:
        raise ValueError("P7 required P6 evidence path set drifted")
    _validate_p6_evidence_use_contract(p6_binding, "P7 P6 evidence binding")

    lane = registry["candidate_lane_contract"]
    if lane.get("lane_id") != P7_CANDIDATE_LANE_ID:
        raise ValueError("P7 candidate lane id drifted")
    if lane.get("lane_status") != "candidate_design_only_not_selected_for_execution":
        raise ValueError("P7 candidate lane status drifted")
    _validate_future_authorization_gate(lane, "P7 candidate lane contract")

    gate = registry["future_authorization_gate_contract"]
    _validate_future_authorization_gate(gate, "P7 future authorization gate")

    schema = registry["artifact_manifest_schema"]
    required = set(schema["required_artifact_fields"])
    for field in (*TOP_LEVEL_FALSE_FIELDS, *TOP_LEVEL_TRUE_FIELDS):
        if field not in required:
            raise ValueError(f"P7 artifact schema missing guard field: {field}")
    for artifact in registry["planned_artifacts"]:
        if not required.issubset(artifact):
            raise ValueError(f"P7 artifact missing schema fields: {artifact['artifact_id']}")
        _validate_guard_fields(artifact, artifact["artifact_id"])
    return registry


def _load_validated_p6_evidence(project_root: Path) -> dict[str, dict[str, Any]]:
    return {
        P6_P5_BINDING_MANIFEST.as_posix(): validate_p6_p5_binding_manifest(
            _load_json_file(project_root / P6_P5_BINDING_MANIFEST)
        ),
        P6_SOLVER_OUTPUT_MANIFEST.as_posix(): validate_p6_solver_output_manifest(
            _load_json_file(project_root / P6_SOLVER_OUTPUT_MANIFEST)
        ),
        P6_ARTIFACT_MANIFEST.as_posix(): validate_p6_artifact_manifest(
            _load_json_file(project_root / P6_ARTIFACT_MANIFEST),
            project_root,
        ),
    }


def _guard_payload() -> dict[str, bool]:
    return {key: False for key in TOP_LEVEL_FALSE_FIELDS} | {
        key: True for key in TOP_LEVEL_TRUE_FIELDS
    }


def build_p6_evidence_binding_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_design_registry(load_design_registry(project_root))
    p6_manifests = _load_validated_p6_evidence(project_root)
    evidence = []
    for relpath in P6_REQUIRED_EVIDENCE_PATHS:
        path = project_root / relpath
        if not path.is_file():
            raise ValueError(f"P7 P6 evidence missing: {relpath}")
        schema_version = p6_manifests.get(relpath, {}).get("schema_version")
        evidence.append(
            {
                "path": relpath,
                "sha256": sha256_file(path),
                "schema_version": schema_version,
                "evidence_role": "p6_prior_trace_or_manifest_evidence_not_calibration",
                **_guard_payload(),
            }
        )
    return {
        "schema_version": "ev_nodi_p7_second_lane_authorization_design_p6_evidence_binding_manifest_v1",
        "stage": P7_DESIGN_STAGE,
        "manifest_role": "p6_evidence_binding_for_second_lane_authorization_design",
        "bound_p6_artifact_count": len(evidence),
        "evidence": evidence,
        "p6_trace_output_role": (
            "prior_trace_only_rank_pairwise_order_evidence_not_calibration_or_promotion"
        ),
        "p6_trace_used_as_calibrated_prediction": False,
        "p6_trace_used_as_physical_calibration": False,
        "p6_trace_used_as_route_promotion_evidence": False,
        "p6_trace_used_as_snr_lod_concentration_specificity_evidence": False,
        **_guard_payload(),
    }


def validate_p6_evidence_binding_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != (
        "ev_nodi_p7_second_lane_authorization_design_p6_evidence_binding_manifest_v1"
    ):
        raise ValueError("unexpected P7 P6 evidence binding manifest schema")
    if manifest.get("stage") != P7_DESIGN_STAGE:
        raise ValueError("P7 P6 evidence binding stage drifted")
    _validate_guard_fields(manifest, "P7 P6 evidence binding manifest")
    _validate_p6_evidence_use_contract(manifest, "P7 P6 evidence binding manifest")
    paths = tuple(entry["path"] for entry in manifest["evidence"])
    if paths != P6_REQUIRED_EVIDENCE_PATHS:
        raise ValueError("P7 P6 evidence binding path set drifted")
    for entry in manifest["evidence"]:
        _validate_guard_fields(entry, f"P7 P6 evidence entry {entry['path']}")
        if entry.get("evidence_role") != "p6_prior_trace_or_manifest_evidence_not_calibration":
            raise ValueError(f"P7 P6 evidence role drifted: {entry['path']}")
        if not entry.get("sha256"):
            raise ValueError(f"P7 P6 evidence hash missing: {entry['path']}")
    return manifest


def build_authorization_gate_record(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_design_registry(load_design_registry(project_root))
    return {
        "schema_version": "ev_nodi_p7_second_lane_authorization_design_gate_record_v1",
        "stage": P7_DESIGN_STAGE,
        "record_role": "future_second_lane_execution_authorization_gate_record",
        "authorization_gate_decision": "not_authorized_pending_explicit_future_request",
        "explicit_second_lane_execution_request_required": True,
        "required_future_authorization_phrase": P7_REQUIRED_FUTURE_AUTHORIZATION_PHRASE,
        "future_authorization_phrase_already_received": False,
        "current_prompt_authorizes_second_lane_execution": False,
        "minimum_later_phase_requirements": list(P7_MINIMUM_LATER_PHASE_REQUIREMENTS),
        **_guard_payload(),
    }


def validate_authorization_gate_record(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("schema_version") != "ev_nodi_p7_second_lane_authorization_design_gate_record_v1":
        raise ValueError("unexpected P7 authorization gate record schema")
    _validate_future_authorization_gate(record, "P7 authorization gate record")
    if tuple(record["minimum_later_phase_requirements"]) != P7_MINIMUM_LATER_PHASE_REQUIREMENTS:
        raise ValueError("P7 later-phase requirements drifted")
    return record


def build_candidate_lane_contract_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_design_registry(load_design_registry(project_root))
    lane = registry["candidate_lane_contract"]
    return {
        "schema_version": "ev_nodi_p7_second_lane_authorization_design_candidate_lane_contract_v1",
        "stage": P7_DESIGN_STAGE,
        "manifest_role": "second_lane_candidate_contract_design_only",
        "lane_id": P7_CANDIDATE_LANE_ID,
        "lane_status": "candidate_design_only_not_selected_for_execution",
        "candidate_lane_constraints": lane["candidate_lane_constraints"],
        "required_future_authorization_phrase": P7_REQUIRED_FUTURE_AUTHORIZATION_PHRASE,
        "future_authorization_phrase_already_received": False,
        "current_prompt_authorizes_second_lane_execution": False,
        "authorization_gate_decision": "not_authorized_pending_explicit_future_request",
        "explicit_second_lane_execution_request_required": True,
        **_guard_payload(),
    }


def validate_candidate_lane_contract_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != (
        "ev_nodi_p7_second_lane_authorization_design_candidate_lane_contract_v1"
    ):
        raise ValueError("unexpected P7 candidate lane contract schema")
    if manifest.get("lane_id") != P7_CANDIDATE_LANE_ID:
        raise ValueError("P7 candidate lane manifest id drifted")
    if manifest.get("lane_status") != "candidate_design_only_not_selected_for_execution":
        raise ValueError("P7 candidate lane manifest status drifted")
    _validate_future_authorization_gate(manifest, "P7 candidate lane contract manifest")
    return manifest


def _artifact_entry(project_root: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    relpath = artifact["path"]
    path = project_root / relpath
    is_self_manifest = relpath == P7_ARTIFACT_MANIFEST.as_posix()
    return {
        **artifact,
        "path_exists": True if is_self_manifest else path.is_file(),
        "sha256": None if is_self_manifest else sha256_file(path) if path.is_file() else None,
        "hash_role": "self_hash_excluded" if is_self_manifest else "content_sha256",
    }


def build_artifact_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_design_registry(load_design_registry(project_root))
    artifacts = [_artifact_entry(project_root, artifact) for artifact in registry["planned_artifacts"]]
    return {
        "schema_version": "ev_nodi_p7_second_lane_authorization_design_artifact_manifest_v1",
        "stage": P7_DESIGN_STAGE,
        "manifest_role": "second_lane_authorization_design_artifact_manifest",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "claim_boundary": {
            key: False for key in CLAIM_BOUNDARY_FALSE_FIELDS
        }
        | {"allowed_claim_level": "second_lane_authorization_design_only"},
        **_guard_payload(),
    }


def validate_artifact_manifest(
    manifest: dict[str, Any],
    project_root: Path = PROJECT_ROOT,
    *,
    allow_missing_self_manifest: bool = False,
) -> dict[str, Any]:
    if manifest.get("schema_version") != (
        "ev_nodi_p7_second_lane_authorization_design_artifact_manifest_v1"
    ):
        raise ValueError("unexpected P7 artifact manifest schema")
    _validate_guard_fields(manifest, "P7 artifact manifest")
    _validate_claim_boundary(manifest["claim_boundary"], "P7 artifact manifest")
    for artifact in manifest["artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
        is_self_manifest = artifact["path"] == P7_ARTIFACT_MANIFEST.as_posix()
        if (
            not (project_root / artifact["path"]).is_file()
            and not (allow_missing_self_manifest and is_self_manifest)
        ):
            raise ValueError(f"P7 artifact missing: {artifact['path']}")
        if artifact["hash_role"] == "content_sha256" and not artifact["sha256"]:
            raise ValueError(f"P7 artifact hash missing: {artifact['path']}")
    return manifest


def write_p6_evidence_binding_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_p6_evidence_binding_manifest(
        build_p6_evidence_binding_manifest(project_root)
    )
    output_path = project_root / P7_P6_EVIDENCE_BINDING_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_authorization_gate_record(project_root: Path = PROJECT_ROOT) -> Path:
    record = validate_authorization_gate_record(build_authorization_gate_record(project_root))
    output_path = project_root / P7_AUTHORIZATION_GATE_RECORD
    write_json_atomic(output_path, record, sort_keys=True)
    return output_path


def write_candidate_lane_contract_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_candidate_lane_contract_manifest(
        build_candidate_lane_contract_manifest(project_root)
    )
    output_path = project_root / P7_CANDIDATE_LANE_CONTRACT_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_artifact_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_artifact_manifest(
        build_artifact_manifest(project_root),
        project_root,
        allow_missing_self_manifest=True,
    )
    output_path = project_root / P7_ARTIFACT_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_design_package(project_root: Path = PROJECT_ROOT) -> list[Path]:
    p6_binding = write_p6_evidence_binding_manifest(project_root)
    gate_record = write_authorization_gate_record(project_root)
    candidate_contract = write_candidate_lane_contract_manifest(project_root)
    artifact_manifest = write_artifact_manifest(project_root)
    return [p6_binding, gate_record, candidate_contract, artifact_manifest]


def _assert_manifest_current(path: Path, expected: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    actual = _load_json_file(path)
    if actual != expected:
        raise ValueError(f"stale {label}: regenerate P7 authorization design manifests")


def verify_design_package(project_root: Path = PROJECT_ROOT) -> list[str]:
    validate_design_registry(load_design_registry(project_root))

    p6_binding = validate_p6_evidence_binding_manifest(
        build_p6_evidence_binding_manifest(project_root)
    )
    _assert_manifest_current(
        project_root / P7_P6_EVIDENCE_BINDING_MANIFEST,
        p6_binding,
        "P7 P6 evidence binding manifest",
    )

    gate_record = validate_authorization_gate_record(
        build_authorization_gate_record(project_root)
    )
    _assert_manifest_current(
        project_root / P7_AUTHORIZATION_GATE_RECORD,
        gate_record,
        "P7 authorization gate record",
    )

    candidate_contract = validate_candidate_lane_contract_manifest(
        build_candidate_lane_contract_manifest(project_root)
    )
    _assert_manifest_current(
        project_root / P7_CANDIDATE_LANE_CONTRACT_MANIFEST,
        candidate_contract,
        "P7 candidate lane contract manifest",
    )

    artifact_manifest = validate_artifact_manifest(
        build_artifact_manifest(project_root),
        project_root,
    )
    _assert_manifest_current(
        project_root / P7_ARTIFACT_MANIFEST,
        artifact_manifest,
        "P7 artifact manifest",
    )

    lexicon = load_forbidden_claims_lexicon(project_root)
    for relpath in P7_TEXT_PATHS:
        text = (project_root / relpath).read_text(encoding="utf-8")
        if not claim_text_passes(text, lexicon):
            raise ValueError(f"P7 authorization design claim language drifted: {relpath}")

    return [
        "PASS second_lane_authorization_design_registry",
        "PASS second_lane_authorization_design_p6_evidence_binding_manifest_current",
        "PASS second_lane_authorization_design_future_gate_not_authorized",
        "PASS second_lane_authorization_design_candidate_lane_contract_current",
        "PASS second_lane_authorization_design_artifact_manifest_current",
        "PASS second_lane_authorization_design_no_solver_execution_or_output",
        "PASS second_lane_authorization_design_claim_boundaries",
    ]
