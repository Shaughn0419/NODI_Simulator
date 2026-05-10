"""P3 bounded solver authorization and minimal pilot-design helpers.

This module records phase-1 authorization planning and pilot-design contracts
only. It does not run a solver, generate a mesh, ingest measured data, or
promote routes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .post_v2_bounded_physical_solver_readiness import (
    P2_READINESS_ROUTE_UNIVERSE_MANIFEST,
    validate_readiness_route_universe_manifest,
)
from .realism_v2 import load_json_yaml
from .realism_v2_io import sha256_file, write_json_atomic
from .review_package import (
    PROJECT_ROOT,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)


P3_PILOT_DIR = Path("results/post_v2_bounded_solver_authorization_pilot_design")
P3_PILOT_REGISTRY = (
    "configs/realism_v2/bounded_solver_authorization_pilot_design_registry.yaml"
)
P3_PILOT_PLAN = (
    "reports/100_EV_NODI_P3_bounded_solver_authorization_pilot_design_plan.md"
)
P3_PILOT_README = P3_PILOT_DIR / "README.md"
P3_PILOT_ROUTE_SUBSET_MANIFEST = (
    P3_PILOT_DIR / "bounded_solver_authorization_pilot_design_route_subset_manifest.json"
)
P3_PILOT_P2_BINDING_MANIFEST = (
    P3_PILOT_DIR / "bounded_solver_authorization_pilot_design_p2_route_binding_manifest.json"
)
P3_PILOT_SCHEMA_MANIFEST = (
    P3_PILOT_DIR / "bounded_solver_authorization_pilot_design_schema_manifest.json"
)
P3_PILOT_ARTIFACT_MANIFEST = (
    P3_PILOT_DIR / "bounded_solver_authorization_pilot_design_artifact_manifest.json"
)
P3_PILOT_TEXT_PATHS: tuple[str, ...] = (
    P3_PILOT_REGISTRY,
    P3_PILOT_PLAN,
    P3_PILOT_README.as_posix(),
    "docs/schemas/bounded_solver_authorization_pilot_design_schema_manifest_schema.md",
    "docs/schemas/bounded_solver_authorization_pilot_design_route_subset_manifest_schema.md",
    "docs/schemas/bounded_solver_authorization_pilot_design_p2_route_binding_manifest_schema.md",
    "docs/schemas/bounded_solver_authorization_pilot_design_artifact_manifest_schema.md",
)

P3_PILOT_LANE_ID = "full_wave_green_tensor_spot_check_minimal_pilot_design"
P3_PILOT_STAGE = "P3_bounded_solver_authorization_pilot_design_phase1"
P3_PILOT_SCHEMA_VERSION = (
    "ev_nodi_p3_bounded_solver_authorization_pilot_design_registry_v1"
)
P2_ROUTE_UNIVERSE_SCHEMA_VERSION = (
    "ev_nodi_p2_bounded_physical_solver_readiness_route_universe_manifest_v1"
)

TOP_LEVEL_FALSE_FIELDS: tuple[str, ...] = (
    "calibrated_claim_allowed",
    "p0_release_conclusion_changed",
    "physical_solver_execution_authorized",
    "measured_data_ingest_authorized",
    "solver_output_generated",
)

TOP_LEVEL_TRUE_FIELDS: tuple[str, ...] = (
    "p1_surrogate_risk_role_preserved",
    "p2_readiness_scope_preserved",
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
        "authorization_planning_authorized",
        "minimal_pilot_design_authorized",
        "p2_route_universe_binding_manifest_generation_authorized",
        "route_subset_design_manifest_generation_authorized",
        "schema_manifest_generation_authorized",
        "artifact_manifest_generation_authorized",
        "verifier_authorized",
    }
)

ALLOWED_GATE_METRIC_FAMILIES: frozenset[str] = frozenset(
    {"rank", "rank_percentile", "pairwise_inversion"}
)

SELECTED_ROUTE_FIELDS: tuple[str, ...] = (
    "candidate_id",
    "route_key",
    "comparison_stratum",
    "route_role_final",
    "final_audit_decision",
    "required_next_artifact_priority",
    "full_wave_green_tensor_surrogate_risk_label",
    "full_wave_green_tensor_pairwise_inversion_flag",
    "any_p1_high_surrogate_risk",
    "any_p1_pairwise_inversion_flag",
)


def load_pilot_registry(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return load_json_yaml(project_root / P3_PILOT_REGISTRY)


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
    if claims.get("allowed_claim_level") != "bounded_solver_authorization_pilot_design_only":
        raise ValueError(f"{context} claim level drifted")


def _validate_gate_policy(policy: dict[str, Any], context: str) -> None:
    if set(policy["allowed_gate_metric_families"]) != ALLOWED_GATE_METRIC_FAMILIES:
        raise ValueError(f"{context} gate metric families drifted")
    if policy["raw_arbitrary_unit_magnitude_final_gate_allowed"] is not False:
        raise ValueError(f"{context} raw arbitrary-unit final gate drifted")
    if policy["solver_native_raw_magnitude_final_gate_allowed"] is not False:
        raise ValueError(f"{context} solver-native raw final gate drifted")
    if policy["decision_authority"] != "pilot_design_only_no_route_promotion":
        raise ValueError(f"{context} decision authority drifted")


def validate_pilot_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema_version") != P3_PILOT_SCHEMA_VERSION:
        raise ValueError("unexpected P3 pilot registry schema")
    if registry.get("stage") != P3_PILOT_STAGE:
        raise ValueError("unexpected P3 pilot stage")
    if registry.get("pilot_design_role") != "authorization_planning_and_minimal_pilot_design_only":
        raise ValueError("P3 pilot role drifted")
    _require_false(registry, TOP_LEVEL_FALSE_FIELDS, "P3 registry")
    _require_true(registry, TOP_LEVEL_TRUE_FIELDS, "P3 registry")

    authority = registry["implementation_authority"]
    for key, value in authority.items():
        if key in ALLOWED_TRUE_AUTHORITY_FIELDS:
            if value is not True:
                raise ValueError(f"P3 pilot authority missing: {key}")
            continue
        if value is not False:
            raise ValueError(f"P3 execution authority drifted: {key}")

    _validate_claim_boundary(registry["claim_governance"], "P3 registry")
    _validate_gate_policy(registry["score_governance"], "P3 registry")

    jacobian = registry["jacobian_governance"]
    if jacobian["v1_bfp_to_angle_jacobian_applied"] is not False:
        raise ValueError("v1 Jacobian source flag drifted")
    if jacobian["audit_bfp_jacobian_applied"] is not True:
        raise ValueError("audit Jacobian sidecar flag drifted")

    p2_binding = registry["p2_route_universe_binding"]
    if p2_binding["source_manifest_path"] != P2_READINESS_ROUTE_UNIVERSE_MANIFEST.as_posix():
        raise ValueError("P3 pilot must reference the P2 route-universe manifest")
    if p2_binding["source_manifest_schema_version_required"] != P2_ROUTE_UNIVERSE_SCHEMA_VERSION:
        raise ValueError("P3 P2 route-universe schema-version requirement drifted")
    if p2_binding["binding_role"] != "future_solver_preflight_scope_only":
        raise ValueError("P2 route-universe binding role drifted")
    _require_false(p2_binding, TOP_LEVEL_FALSE_FIELDS, "P3 P2 binding")
    _require_true(p2_binding, TOP_LEVEL_TRUE_FIELDS, "P3 P2 binding")

    lanes = registry["pilot_design_lanes"]
    if len(lanes) != 1 or lanes[0]["lane_id"] != P3_PILOT_LANE_ID:
        raise ValueError("P3 phase 1 must contain exactly the minimal full-wave lane")
    lane = lanes[0]
    if lane["lane_status"] != "phase1_pilot_design_only_not_executable":
        raise ValueError("P3 pilot lane status drifted")
    _require_false(lane, TOP_LEVEL_FALSE_FIELDS, lane["lane_id"])
    _require_true(lane, TOP_LEVEL_TRUE_FIELDS, lane["lane_id"])
    for key, value in lane["execution_authority"].items():
        if value is not False:
            raise ValueError(f"P3 lane execution authority drifted: {lane['lane_id']} {key}")
    _validate_claim_boundary(lane["claim_boundary"], lane["lane_id"])
    _validate_gate_policy(lane["gate_policy"], lane["lane_id"])

    rule = lane["route_subset_selection_rule"]
    if rule["source_manifest_path"] != P2_READINESS_ROUTE_UNIVERSE_MANIFEST.as_posix():
        raise ValueError("P3 route subset must be selected from the P2 route universe")
    if rule["raw_proxy_fields_allowed"] is not False:
        raise ValueError("P3 route subset raw proxy fields drifted")
    if rule["route_promotion_evidence_allowed"] is not False:
        raise ValueError("P3 route subset promotion evidence drifted")
    if rule["subset_size_target"] != 3:
        raise ValueError("P3 minimal pilot subset target drifted")

    input_schema = lane["solver_input_manifest_schema"]
    if input_schema["schema_role"] != "future_input_contract_only_no_solver_execution":
        raise ValueError("P3 solver input schema role drifted")
    _require_false(input_schema, TOP_LEVEL_FALSE_FIELDS, "P3 solver input schema")
    if input_schema["raw_magnitude_final_gate_allowed"] is not False:
        raise ValueError("P3 solver input schema raw final gate drifted")
    if input_schema["source_manifest_path_required"] != P2_READINESS_ROUTE_UNIVERSE_MANIFEST.as_posix():
        raise ValueError("P3 solver input schema must require the P2 route universe")

    preflight = lane["mesh_boundary_unit_preflight_schema"]
    if preflight["schema_role"] != "future_preflight_contract_only_no_mesh_generation":
        raise ValueError("P3 preflight schema role drifted")
    for key, value in preflight["execution_authority"].items():
        if value is not False:
            raise ValueError(f"P3 preflight authority drifted: {key}")
    if preflight["v1_bfp_to_angle_jacobian_applied"] is not False:
        raise ValueError("P3 preflight v1 Jacobian source flag drifted")
    if preflight["audit_bfp_jacobian_applied"] is not True:
        raise ValueError("P3 preflight audit Jacobian flag drifted")

    output_schema = lane["output_schema_placeholder"]
    if output_schema["artifact_status"] != "output_schema_placeholder_no_solver_output":
        raise ValueError("P3 output schema status drifted")
    _require_false(output_schema, TOP_LEVEL_FALSE_FIELDS, "P3 output schema placeholder")
    if output_schema["raw_magnitude_final_gate_allowed"] is not False:
        raise ValueError("P3 output schema raw final gate drifted")
    if set(output_schema["allowed_interpretability_families"]) != ALLOWED_GATE_METRIC_FAMILIES:
        raise ValueError("P3 output schema interpretability families drifted")
    if output_schema["allowed_claim_level"] != "pilot_design_output_schema_placeholder_only":
        raise ValueError("P3 output schema claim level drifted")

    schema = registry["artifact_manifest_schema"]
    required = set(schema["required_artifact_fields"])
    for field in (
        *TOP_LEVEL_FALSE_FIELDS,
        "p1_surrogate_risk_role_preserved",
        "p2_readiness_scope_preserved",
    ):
        if field not in required:
            raise ValueError(f"P3 artifact schema missing guard field: {field}")
    for artifact in registry["planned_artifacts"]:
        if not required.issubset(artifact):
            raise ValueError(f"P3 artifact missing schema fields: {artifact['artifact_id']}")
        _require_false(artifact, TOP_LEVEL_FALSE_FIELDS, artifact["artifact_id"])
        _require_true(artifact, TOP_LEVEL_TRUE_FIELDS, artifact["artifact_id"])
    return registry


def _p2_route_universe(project_root: Path) -> dict[str, Any]:
    return validate_readiness_route_universe_manifest(
        _load_json_file(project_root / P2_READINESS_ROUTE_UNIVERSE_MANIFEST)
    )


def _route_sort_key(row: dict[str, Any]) -> tuple[str, str]:
    return (row["route_key"], row["candidate_id"])


def _select_pilot_routes(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    main_rows = sorted(
        [row for row in routes if row["route_role_final"] == "relative_main_candidate"],
        key=_route_sort_key,
    )[:2]
    main_ids = {row["candidate_id"] for row in main_rows}
    stress_rows = sorted(
        [
            row
            for row in routes
            if row["full_wave_green_tensor_pairwise_inversion_flag"] is True
            and row["candidate_id"] not in main_ids
        ],
        key=_route_sort_key,
    )[:1]
    selected = main_rows + stress_rows
    if len(selected) != 3:
        raise ValueError("P3 minimal pilot route subset could not select 3 routes")
    return selected


def build_p2_route_binding_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_pilot_registry(load_pilot_registry(project_root))
    p2_manifest_path = project_root / P2_READINESS_ROUTE_UNIVERSE_MANIFEST
    p2_manifest = _p2_route_universe(project_root)
    binding = registry["p2_route_universe_binding"]
    if binding["source_manifest_schema_version_required"] != p2_manifest["schema_version"]:
        raise ValueError("P3 P2 route-universe schema-version binding drifted")
    return {
        "schema_version": (
            "ev_nodi_p3_bounded_solver_authorization_pilot_design_p2_route_binding_manifest_v1"
        ),
        "stage": P3_PILOT_STAGE,
        "manifest_role": "p2_route_universe_binding_no_solver_execution",
        "bound_source_manifest_path": binding["source_manifest_path"],
        "bound_source_manifest_sha256": sha256_file(p2_manifest_path),
        "bound_source_manifest_schema_version": p2_manifest["schema_version"],
        "bound_source_manifest_stage": p2_manifest["stage"],
        "bound_route_universe_row_count": p2_manifest["route_universe_row_count"],
        "bound_comparison_strata": p2_manifest["comparison_strata"],
        "binding_role": binding["binding_role"],
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "p2_readiness_scope_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "solver_output_generated": False,
        "route_promotion_authorized": False,
        "required_false_fields": [
            *TOP_LEVEL_FALSE_FIELDS,
            "route_promotion_authorized",
        ],
    }


def validate_p2_route_binding_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p3_bounded_solver_authorization_pilot_design_p2_route_binding_manifest_v1"
    ):
        raise ValueError("unexpected P3 P2 route binding manifest schema")
    if manifest.get("bound_source_manifest_path") != P2_READINESS_ROUTE_UNIVERSE_MANIFEST.as_posix():
        raise ValueError("P3 pilot must bind the P2 route-universe manifest")
    if manifest.get("bound_source_manifest_schema_version") != P2_ROUTE_UNIVERSE_SCHEMA_VERSION:
        raise ValueError("P3 P2 route binding schema version drifted")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P3 P2 route binding manifest")
    _require_true(manifest, TOP_LEVEL_TRUE_FIELDS, "P3 P2 route binding manifest")
    if manifest["route_promotion_authorized"] is not False:
        raise ValueError("P3 P2 route binding route promotion drifted")
    if manifest["bound_route_universe_row_count"] <= 0:
        raise ValueError("P3 P2 route binding row count empty")
    return manifest


def build_route_subset_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_pilot_registry(load_pilot_registry(project_root))
    lane = registry["pilot_design_lanes"][0]
    p2_manifest = _p2_route_universe(project_root)
    selected_routes = []
    for row in _select_pilot_routes(p2_manifest["routes"]):
        selected_routes.append(
            {
                **{field: row[field] for field in SELECTED_ROUTE_FIELDS},
                "selection_source": P2_READINESS_ROUTE_UNIVERSE_MANIFEST.as_posix(),
                "selection_role": "minimal_future_spot_check_design_only",
                "calibrated_claim_allowed": False,
                "p0_release_conclusion_changed": False,
                "p1_surrogate_risk_role_preserved": True,
                "p2_readiness_scope_preserved": True,
                "physical_solver_execution_authorized": False,
                "measured_data_ingest_authorized": False,
                "solver_output_generated": False,
                "raw_magnitude_final_gate_allowed": False,
                "route_promotion_authorized": False,
            }
        )
    return {
        "schema_version": (
            "ev_nodi_p3_bounded_solver_authorization_pilot_design_route_subset_manifest_v1"
        ),
        "stage": P3_PILOT_STAGE,
        "manifest_role": "minimal_pilot_route_subset_design_no_solver_execution",
        "lane_id": P3_PILOT_LANE_ID,
        "source_manifest_path": P2_READINESS_ROUTE_UNIVERSE_MANIFEST.as_posix(),
        "source_manifest_sha256": sha256_file(project_root / P2_READINESS_ROUTE_UNIVERSE_MANIFEST),
        "selection_rule": lane["route_subset_selection_rule"],
        "selected_route_count": len(selected_routes),
        "selected_routes": selected_routes,
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "p2_readiness_scope_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "solver_output_generated": False,
        "raw_magnitude_final_gate_allowed": False,
        "route_promotion_authorized": False,
        "required_false_fields": [
            *TOP_LEVEL_FALSE_FIELDS,
            "raw_magnitude_final_gate_allowed",
            "route_promotion_authorized",
        ],
    }


def validate_route_subset_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p3_bounded_solver_authorization_pilot_design_route_subset_manifest_v1"
    ):
        raise ValueError("unexpected P3 route subset manifest schema")
    if manifest["source_manifest_path"] != P2_READINESS_ROUTE_UNIVERSE_MANIFEST.as_posix():
        raise ValueError("P3 route subset must reference the P2 route-universe manifest")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P3 route subset manifest")
    _require_true(manifest, TOP_LEVEL_TRUE_FIELDS, "P3 route subset manifest")
    if manifest["raw_magnitude_final_gate_allowed"] is not False:
        raise ValueError("P3 route subset raw final gate drifted")
    if manifest["route_promotion_authorized"] is not False:
        raise ValueError("P3 route subset promotion drifted")
    if manifest["selected_route_count"] != 3:
        raise ValueError("P3 minimal pilot subset size drifted")
    selected_ids = [row["candidate_id"] for row in manifest["selected_routes"]]
    if len(set(selected_ids)) != len(selected_ids):
        raise ValueError("P3 minimal pilot subset contains duplicate routes")
    if not any(row["route_role_final"] == "relative_main_candidate" for row in manifest["selected_routes"]):
        raise ValueError("P3 minimal pilot subset lost main-candidate coverage")
    if not any(
        row["full_wave_green_tensor_pairwise_inversion_flag"] is True
        for row in manifest["selected_routes"]
    ):
        raise ValueError("P3 minimal pilot subset lost pairwise-inversion stress coverage")
    for row in manifest["selected_routes"]:
        _require_false(row, TOP_LEVEL_FALSE_FIELDS, row["candidate_id"])
        _require_true(row, TOP_LEVEL_TRUE_FIELDS, row["candidate_id"])
        if row["raw_magnitude_final_gate_allowed"] is not False:
            raise ValueError(f"P3 route raw final gate drifted: {row['candidate_id']}")
        if row["route_promotion_authorized"] is not False:
            raise ValueError(f"P3 route promotion drifted: {row['candidate_id']}")
        if row["selection_source"] != P2_READINESS_ROUTE_UNIVERSE_MANIFEST.as_posix():
            raise ValueError(f"P3 route selection source drifted: {row['candidate_id']}")
        if any(
            key.startswith("raw_") and key != "raw_magnitude_final_gate_allowed"
            for key in row
        ):
            raise ValueError(f"P3 route subset must not carry raw proxy fields: {row['candidate_id']}")
    return manifest


def build_schema_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_pilot_registry(load_pilot_registry(project_root))
    lane = registry["pilot_design_lanes"][0]
    return {
        "schema_version": (
            "ev_nodi_p3_bounded_solver_authorization_pilot_design_schema_manifest_v1"
        ),
        "stage": P3_PILOT_STAGE,
        "manifest_role": "pilot_design_schema_manifest_no_solver_execution",
        "lane_id": P3_PILOT_LANE_ID,
        "solver_input_manifest_schema": lane["solver_input_manifest_schema"],
        "mesh_boundary_unit_preflight_schema": lane[
            "mesh_boundary_unit_preflight_schema"
        ],
        "output_schema_placeholder": lane["output_schema_placeholder"],
        "rank_pairwise_interpretability_requirement": lane[
            "rank_pairwise_interpretability_requirement"
        ],
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "p2_readiness_scope_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "solver_output_generated": False,
        "required_false_fields": list(TOP_LEVEL_FALSE_FIELDS),
        "required_gate_metric_families": sorted(ALLOWED_GATE_METRIC_FAMILIES),
    }


def validate_schema_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p3_bounded_solver_authorization_pilot_design_schema_manifest_v1"
    ):
        raise ValueError("unexpected P3 schema manifest schema")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P3 schema manifest")
    _require_true(manifest, TOP_LEVEL_TRUE_FIELDS, "P3 schema manifest")
    input_schema = manifest["solver_input_manifest_schema"]
    if input_schema["source_manifest_path_required"] != P2_READINESS_ROUTE_UNIVERSE_MANIFEST.as_posix():
        raise ValueError("P3 schema manifest input schema lost P2 binding")
    _require_false(input_schema, TOP_LEVEL_FALSE_FIELDS, "P3 schema manifest input schema")
    if input_schema["raw_magnitude_final_gate_allowed"] is not False:
        raise ValueError("P3 schema manifest raw final gate drifted")
    preflight = manifest["mesh_boundary_unit_preflight_schema"]
    for key, value in preflight["execution_authority"].items():
        if value is not False:
            raise ValueError(f"P3 schema manifest preflight authority drifted: {key}")
    output_schema = manifest["output_schema_placeholder"]
    _require_false(output_schema, TOP_LEVEL_FALSE_FIELDS, "P3 schema manifest output schema")
    if output_schema["raw_magnitude_final_gate_allowed"] is not False:
        raise ValueError("P3 schema manifest output raw final gate drifted")
    if output_schema["allowed_claim_level"] != "pilot_design_output_schema_placeholder_only":
        raise ValueError("P3 schema manifest output claim level drifted")
    if set(manifest["required_gate_metric_families"]) != ALLOWED_GATE_METRIC_FAMILIES:
        raise ValueError("P3 schema manifest gate families drifted")
    return manifest


def _artifact_entry(project_root: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    relpath = artifact["path"]
    path = project_root / relpath
    is_self_manifest = relpath == P3_PILOT_ARTIFACT_MANIFEST.as_posix()
    return {
        **artifact,
        "path_exists": True if is_self_manifest else path.is_file(),
        "sha256": None if is_self_manifest else sha256_file(path) if path.is_file() else None,
        "hash_role": "self_hash_excluded" if is_self_manifest else "content_sha256",
    }


def build_artifact_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_pilot_registry(load_pilot_registry(project_root))
    artifacts = [
        _artifact_entry(project_root, artifact)
        for artifact in registry["planned_artifacts"]
    ]
    return {
        "schema_version": (
            "ev_nodi_p3_bounded_solver_authorization_pilot_design_artifact_manifest_v1"
        ),
        "stage": P3_PILOT_STAGE,
        "manifest_role": "pilot_design_artifact_manifest_no_solver_execution",
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "p2_readiness_scope_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "solver_output_generated": False,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "required_false_fields": list(TOP_LEVEL_FALSE_FIELDS),
        "claim_boundary": {
            key: False for key in CLAIM_BOUNDARY_FALSE_FIELDS
        }
        | {"allowed_claim_level": "bounded_solver_authorization_pilot_design_only"},
    }


def validate_artifact_manifest(
    manifest: dict[str, Any],
    project_root: Path = PROJECT_ROOT,
    *,
    allow_missing_self_manifest: bool = False,
) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p3_bounded_solver_authorization_pilot_design_artifact_manifest_v1"
    ):
        raise ValueError("unexpected P3 artifact manifest schema")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P3 artifact manifest")
    _require_true(manifest, TOP_LEVEL_TRUE_FIELDS, "P3 artifact manifest")
    _validate_claim_boundary(manifest["claim_boundary"], "P3 artifact manifest")
    if manifest["artifact_count"] <= 0:
        raise ValueError("P3 artifact manifest must not be empty")
    for artifact in manifest["artifacts"]:
        _require_false(artifact, TOP_LEVEL_FALSE_FIELDS, artifact["artifact_id"])
        _require_true(artifact, TOP_LEVEL_TRUE_FIELDS, artifact["artifact_id"])
        is_self_manifest = artifact["path"] == P3_PILOT_ARTIFACT_MANIFEST.as_posix()
        if (
            not (project_root / artifact["path"]).is_file()
            and not (allow_missing_self_manifest and is_self_manifest)
        ):
            raise ValueError(f"P3 artifact missing: {artifact['path']}")
        if artifact["hash_role"] == "content_sha256" and not artifact["sha256"]:
            raise ValueError(f"P3 artifact hash missing: {artifact['path']}")
    return manifest


def write_p2_route_binding_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_p2_route_binding_manifest(
        build_p2_route_binding_manifest(project_root)
    )
    output_path = project_root / P3_PILOT_P2_BINDING_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_route_subset_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_route_subset_manifest(build_route_subset_manifest(project_root))
    output_path = project_root / P3_PILOT_ROUTE_SUBSET_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_schema_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_schema_manifest(build_schema_manifest(project_root))
    output_path = project_root / P3_PILOT_SCHEMA_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_artifact_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_artifact_manifest(
        build_artifact_manifest(project_root),
        project_root,
        allow_missing_self_manifest=True,
    )
    output_path = project_root / P3_PILOT_ARTIFACT_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_pilot_design_package(project_root: Path = PROJECT_ROOT) -> list[Path]:
    return [
        write_p2_route_binding_manifest(project_root),
        write_route_subset_manifest(project_root),
        write_schema_manifest(project_root),
        write_artifact_manifest(project_root),
    ]


def _assert_manifest_current(path: Path, expected: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    actual = _load_json_file(path)
    if actual != expected:
        raise ValueError(f"stale {label}: regenerate P3 pilot design manifests")


def verify_pilot_design_package(project_root: Path = PROJECT_ROOT) -> list[str]:
    validate_pilot_registry(load_pilot_registry(project_root))
    p2_route_binding_manifest = validate_p2_route_binding_manifest(
        build_p2_route_binding_manifest(project_root)
    )
    _assert_manifest_current(
        project_root / P3_PILOT_P2_BINDING_MANIFEST,
        p2_route_binding_manifest,
        "P3 P2 route binding manifest",
    )
    route_subset_manifest = validate_route_subset_manifest(
        build_route_subset_manifest(project_root)
    )
    _assert_manifest_current(
        project_root / P3_PILOT_ROUTE_SUBSET_MANIFEST,
        route_subset_manifest,
        "P3 route subset manifest",
    )
    schema_manifest = validate_schema_manifest(build_schema_manifest(project_root))
    _assert_manifest_current(
        project_root / P3_PILOT_SCHEMA_MANIFEST,
        schema_manifest,
        "P3 schema manifest",
    )
    artifact_manifest = validate_artifact_manifest(
        build_artifact_manifest(project_root),
        project_root,
    )
    _assert_manifest_current(
        project_root / P3_PILOT_ARTIFACT_MANIFEST,
        artifact_manifest,
        "P3 artifact manifest",
    )

    p2_manifest = _p2_route_universe(project_root)
    selected_ids = {
        row["candidate_id"] for row in route_subset_manifest["selected_routes"]
    }
    p2_ids = {row["candidate_id"] for row in p2_manifest["routes"]}
    if not selected_ids.issubset(p2_ids):
        raise ValueError("P3 selected routes are not a subset of the P2 route universe")

    lexicon = load_forbidden_claims_lexicon(project_root)
    for relpath in P3_PILOT_TEXT_PATHS:
        text = (project_root / relpath).read_text(encoding="utf-8")
        if not claim_text_passes(text, lexicon):
            raise ValueError(f"P3 pilot design claim language drifted: {relpath}")

    return [
        "PASS bounded_solver_authorization_pilot_design_registry",
        "PASS bounded_solver_authorization_pilot_design_p2_route_binding_manifest_current",
        "PASS bounded_solver_authorization_pilot_design_route_subset_manifest_current",
        "PASS bounded_solver_authorization_pilot_design_schema_manifest_current",
        "PASS bounded_solver_authorization_pilot_design_artifact_manifest_current",
        "PASS bounded_solver_authorization_pilot_design_execution_blocked",
        "PASS bounded_solver_authorization_pilot_design_measured_data_ingest_blocked",
        "PASS bounded_solver_authorization_pilot_design_solver_output_absent",
        "PASS bounded_solver_authorization_pilot_design_claim_boundaries",
    ]
