"""P4 bounded solver dry-run preflight helpers.

This module instantiates P3 pilot-design schemas as dry-run preflight manifests.
It does not run a solver, generate a mesh, export an operator, ingest measured
data, or promote routes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .post_v2_bounded_solver_authorization_pilot_design import (
    P3_PILOT_ARTIFACT_MANIFEST,
    P3_PILOT_LANE_ID,
    P3_PILOT_ROUTE_SUBSET_MANIFEST,
    P3_PILOT_SCHEMA_MANIFEST,
    validate_artifact_manifest as validate_p3_artifact_manifest,
    validate_route_subset_manifest as validate_p3_route_subset_manifest,
    validate_schema_manifest as validate_p3_schema_manifest,
)
from .realism_v2 import load_json_yaml
from .realism_v2_io import sha256_file, write_json_atomic
from .review_package import (
    PROJECT_ROOT,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)


P4_PREFLIGHT_DIR = Path("results/post_v2_bounded_solver_dry_run_preflight")
P4_PREFLIGHT_REGISTRY = "configs/realism_v2/bounded_solver_dry_run_preflight_registry.yaml"
P4_PREFLIGHT_PLAN = "reports/101_EV_NODI_P4_bounded_solver_dry_run_preflight_plan.md"
P4_PREFLIGHT_README = P4_PREFLIGHT_DIR / "README.md"
P4_P3_BINDING_MANIFEST = (
    P4_PREFLIGHT_DIR / "bounded_solver_dry_run_preflight_p3_binding_manifest.json"
)
P4_INPUT_MANIFEST = (
    P4_PREFLIGHT_DIR / "full_wave_green_tensor_minimal_pilot_input_manifest.json"
)
P4_MESH_PREFLIGHT_MANIFEST = (
    P4_PREFLIGHT_DIR / "full_wave_green_tensor_mesh_boundary_unit_preflight_manifest.json"
)
P4_EXECUTION_AUTHORIZATION_RECORD = (
    P4_PREFLIGHT_DIR / "full_wave_green_tensor_execution_authorization_record.json"
)
P4_ARTIFACT_MANIFEST = (
    P4_PREFLIGHT_DIR / "bounded_solver_dry_run_preflight_artifact_manifest.json"
)
P4_TEXT_PATHS: tuple[str, ...] = (
    P4_PREFLIGHT_REGISTRY,
    P4_PREFLIGHT_PLAN,
    P4_PREFLIGHT_README.as_posix(),
    "docs/schemas/bounded_solver_dry_run_preflight_p3_binding_manifest_schema.md",
    "docs/schemas/bounded_solver_dry_run_preflight_input_manifest_schema.md",
    "docs/schemas/bounded_solver_dry_run_preflight_mesh_boundary_unit_preflight_manifest_schema.md",
    "docs/schemas/bounded_solver_dry_run_preflight_execution_authorization_record_schema.md",
    "docs/schemas/bounded_solver_dry_run_preflight_artifact_manifest_schema.md",
)

P4_PREFLIGHT_STAGE = "P4_bounded_solver_dry_run_preflight_complete"
P4_PREFLIGHT_SCHEMA_VERSION = "ev_nodi_p4_bounded_solver_dry_run_preflight_registry_v1"
P4_PREFLIGHT_LANE_ID = "full_wave_green_tensor_spot_check_dry_run_preflight"

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
        "dry_run_preflight_authorized",
        "p3_binding_manifest_generation_authorized",
        "solver_input_manifest_generation_authorized",
        "mesh_boundary_unit_preflight_manifest_generation_authorized",
        "execution_authorization_record_generation_authorized",
        "artifact_manifest_generation_authorized",
        "verifier_authorized",
    }
)

ALLOWED_INTERPRETABILITY_FAMILIES: frozenset[str] = frozenset(
    {"rank", "rank_percentile", "pairwise_inversion"}
)


def load_preflight_registry(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return load_json_yaml(project_root / P4_PREFLIGHT_REGISTRY)


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
    if claims.get("allowed_claim_level") != "bounded_solver_dry_run_preflight_only":
        raise ValueError(f"{context} claim level drifted")


def _validate_interpretability(mapping: dict[str, Any], context: str) -> None:
    if set(mapping["allowed_interpretability_families"]) != ALLOWED_INTERPRETABILITY_FAMILIES:
        raise ValueError(f"{context} interpretability families drifted")
    if mapping["raw_arbitrary_unit_magnitude_final_gate_allowed"] is not False:
        raise ValueError(f"{context} raw arbitrary-unit final gate drifted")
    if mapping["solver_native_raw_magnitude_final_gate_allowed"] is not False:
        raise ValueError(f"{context} solver-native raw final gate drifted")


def validate_preflight_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema_version") != P4_PREFLIGHT_SCHEMA_VERSION:
        raise ValueError("unexpected P4 preflight registry schema")
    if registry.get("stage") != P4_PREFLIGHT_STAGE:
        raise ValueError("unexpected P4 preflight stage")
    if registry.get("preflight_role") != "dry_run_preflight_only_no_solver_execution":
        raise ValueError("P4 preflight role drifted")
    _require_false(registry, TOP_LEVEL_FALSE_FIELDS, "P4 registry")
    _require_true(registry, TOP_LEVEL_TRUE_FIELDS, "P4 registry")

    authority = registry["implementation_authority"]
    for key, value in authority.items():
        if key in ALLOWED_TRUE_AUTHORITY_FIELDS:
            if value is not True:
                raise ValueError(f"P4 dry-run authority missing: {key}")
            continue
        if value is not False:
            raise ValueError(f"P4 execution authority drifted: {key}")

    _validate_claim_boundary(registry["claim_governance"], "P4 registry")
    _validate_interpretability(registry["interpretability_governance"], "P4 registry")

    p3_binding = registry["p3_pilot_design_binding"]
    if p3_binding["route_subset_manifest_path"] != P3_PILOT_ROUTE_SUBSET_MANIFEST.as_posix():
        raise ValueError("P4 must bind the P3 route subset manifest")
    if p3_binding["schema_manifest_path"] != P3_PILOT_SCHEMA_MANIFEST.as_posix():
        raise ValueError("P4 must bind the P3 schema manifest")
    if p3_binding["artifact_manifest_path"] != P3_PILOT_ARTIFACT_MANIFEST.as_posix():
        raise ValueError("P4 must bind the P3 artifact manifest")
    _require_false(p3_binding, TOP_LEVEL_FALSE_FIELDS, "P4 P3 binding")
    _require_true(p3_binding, TOP_LEVEL_TRUE_FIELDS, "P4 P3 binding")

    lanes = registry["preflight_lanes"]
    if len(lanes) != 1 or lanes[0]["lane_id"] != P4_PREFLIGHT_LANE_ID:
        raise ValueError("P4 must contain exactly the dry-run full-wave lane")
    lane = lanes[0]
    if lane["p3_lane_id"] != P3_PILOT_LANE_ID:
        raise ValueError("P4 lane must preserve the P3 pilot lane binding")
    if lane["lane_status"] != "dry_run_preflight_only_not_executable":
        raise ValueError("P4 lane status drifted")
    _require_false(lane, TOP_LEVEL_FALSE_FIELDS, lane["lane_id"])
    _require_true(lane, TOP_LEVEL_TRUE_FIELDS, lane["lane_id"])
    for key, value in lane["execution_authority"].items():
        if value is not False:
            raise ValueError(f"P4 lane execution authority drifted: {lane['lane_id']} {key}")
    _validate_claim_boundary(lane["claim_boundary"], lane["lane_id"])
    _validate_interpretability(lane["interpretability_requirement"], lane["lane_id"])
    if lane["input_manifest_contract"]["manifest_path"] != P4_INPUT_MANIFEST.as_posix():
        raise ValueError("P4 input manifest path drifted")
    if lane["mesh_boundary_unit_preflight_contract"]["manifest_path"] != P4_MESH_PREFLIGHT_MANIFEST.as_posix():
        raise ValueError("P4 mesh preflight manifest path drifted")
    if lane["execution_authorization_record_contract"]["manifest_path"] != P4_EXECUTION_AUTHORIZATION_RECORD.as_posix():
        raise ValueError("P4 execution authorization record path drifted")
    if lane["execution_authorization_record_contract"]["execution_authorization_decision"] != "not_authorized_phase4_dry_run_only":
        raise ValueError("P4 execution authorization decision drifted")

    schema = registry["artifact_manifest_schema"]
    required = set(schema["required_artifact_fields"])
    for field in (*TOP_LEVEL_FALSE_FIELDS, *TOP_LEVEL_TRUE_FIELDS):
        if field not in required:
            raise ValueError(f"P4 artifact schema missing guard field: {field}")
    for artifact in registry["planned_artifacts"]:
        if not required.issubset(artifact):
            raise ValueError(f"P4 artifact missing schema fields: {artifact['artifact_id']}")
        _require_false(artifact, TOP_LEVEL_FALSE_FIELDS, artifact["artifact_id"])
        _require_true(artifact, TOP_LEVEL_TRUE_FIELDS, artifact["artifact_id"])
    return registry


def _load_p3_route_subset(project_root: Path) -> dict[str, Any]:
    return validate_p3_route_subset_manifest(
        _load_json_file(project_root / P3_PILOT_ROUTE_SUBSET_MANIFEST)
    )


def _load_p3_schema_manifest(project_root: Path) -> dict[str, Any]:
    return validate_p3_schema_manifest(
        _load_json_file(project_root / P3_PILOT_SCHEMA_MANIFEST)
    )


def _load_p3_artifact_manifest(project_root: Path) -> dict[str, Any]:
    return validate_p3_artifact_manifest(
        _load_json_file(project_root / P3_PILOT_ARTIFACT_MANIFEST),
        project_root,
    )


def build_p3_binding_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_preflight_registry(load_preflight_registry(project_root))
    route_subset = _load_p3_route_subset(project_root)
    schema_manifest = _load_p3_schema_manifest(project_root)
    artifact_manifest = _load_p3_artifact_manifest(project_root)
    return {
        "schema_version": "ev_nodi_p4_bounded_solver_dry_run_preflight_p3_binding_manifest_v1",
        "stage": P4_PREFLIGHT_STAGE,
        "manifest_role": "p3_pilot_design_binding_no_solver_execution",
        "p3_route_subset_manifest_path": P3_PILOT_ROUTE_SUBSET_MANIFEST.as_posix(),
        "p3_route_subset_manifest_sha256": sha256_file(project_root / P3_PILOT_ROUTE_SUBSET_MANIFEST),
        "p3_route_subset_schema_version": route_subset["schema_version"],
        "p3_schema_manifest_path": P3_PILOT_SCHEMA_MANIFEST.as_posix(),
        "p3_schema_manifest_sha256": sha256_file(project_root / P3_PILOT_SCHEMA_MANIFEST),
        "p3_schema_manifest_schema_version": schema_manifest["schema_version"],
        "p3_artifact_manifest_path": P3_PILOT_ARTIFACT_MANIFEST.as_posix(),
        "p3_artifact_manifest_sha256": sha256_file(project_root / P3_PILOT_ARTIFACT_MANIFEST),
        "p3_artifact_manifest_schema_version": artifact_manifest["schema_version"],
        "selected_route_count": route_subset["selected_route_count"],
        "selected_route_ids": [row["candidate_id"] for row in route_subset["selected_routes"]],
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "p2_readiness_scope_preserved": True,
        "p3_pilot_design_scope_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "calibration_data_ingest_authorized": False,
        "new_mesh_generation_authorized": False,
        "operator_export_generation_authorized": False,
        "solver_output_generated": False,
        "route_promotion_authorized": False,
    }


def validate_p3_binding_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p4_bounded_solver_dry_run_preflight_p3_binding_manifest_v1"
    ):
        raise ValueError("unexpected P4 P3 binding manifest schema")
    if manifest["p3_route_subset_manifest_path"] != P3_PILOT_ROUTE_SUBSET_MANIFEST.as_posix():
        raise ValueError("P4 P3 binding route subset path drifted")
    if manifest["p3_schema_manifest_path"] != P3_PILOT_SCHEMA_MANIFEST.as_posix():
        raise ValueError("P4 P3 binding schema path drifted")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P4 P3 binding manifest")
    _require_true(manifest, TOP_LEVEL_TRUE_FIELDS, "P4 P3 binding manifest")
    if manifest["selected_route_count"] != 3:
        raise ValueError("P4 P3 binding selected route count drifted")
    return manifest


def build_input_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_preflight_registry(load_preflight_registry(project_root))
    route_subset = _load_p3_route_subset(project_root)
    selected_routes = [
        {
            "candidate_id": row["candidate_id"],
            "route_key": row["route_key"],
            "comparison_stratum": row["comparison_stratum"],
            "route_role_final": row["route_role_final"],
            "full_wave_green_tensor_pairwise_inversion_flag": row[
                "full_wave_green_tensor_pairwise_inversion_flag"
            ],
        }
        for row in route_subset["selected_routes"]
    ]
    return {
        "schema_version": "ev_nodi_p4_full_wave_green_tensor_minimal_pilot_input_manifest_v1",
        "stage": P4_PREFLIGHT_STAGE,
        "manifest_role": "dry_run_solver_input_manifest_no_execution",
        "lane_id": P4_PREFLIGHT_LANE_ID,
        "p3_lane_id": P3_PILOT_LANE_ID,
        "p3_route_subset_manifest_path": P3_PILOT_ROUTE_SUBSET_MANIFEST.as_posix(),
        "p3_route_subset_manifest_sha256": sha256_file(project_root / P3_PILOT_ROUTE_SUBSET_MANIFEST),
        "selected_route_count": len(selected_routes),
        "selected_route_ids": [row["candidate_id"] for row in selected_routes],
        "selected_routes": selected_routes,
        "geometry_source_binding": "p2_route_geometry_keys_via_p3_subset_no_new_cases",
        "material_model_placeholder_id": "phase4_dry_run_material_placeholder_no_material_solution",
        "wavelength_nm_source": "route_key_wavelength_component_from_p2_subset",
        "unit_registry_binding": {
            "length_unit": "nm",
            "wavelength_unit": "nm",
            "solver_field_unit": "not_generated_no_solver_output",
            "detector_unit": "not_available_no_detector_prediction",
        },
        "mesh_boundary_unit_preflight_manifest_path": P4_MESH_PREFLIGHT_MANIFEST.as_posix(),
        "execution_authorization_record_path": P4_EXECUTION_AUTHORIZATION_RECORD.as_posix(),
        "rank_pairwise_interpretability_declared": True,
        "allowed_interpretability_families": sorted(ALLOWED_INTERPRETABILITY_FAMILIES),
        "raw_arbitrary_unit_magnitude_final_gate_allowed": False,
        "solver_native_raw_magnitude_final_gate_allowed": False,
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "p2_readiness_scope_preserved": True,
        "p3_pilot_design_scope_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "calibration_data_ingest_authorized": False,
        "new_mesh_generation_authorized": False,
        "operator_export_generation_authorized": False,
        "solver_output_generated": False,
        "route_promotion_authorized": False,
    }


def validate_input_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p4_full_wave_green_tensor_minimal_pilot_input_manifest_v1"
    ):
        raise ValueError("unexpected P4 input manifest schema")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P4 input manifest")
    _require_true(manifest, TOP_LEVEL_TRUE_FIELDS, "P4 input manifest")
    _validate_interpretability(manifest, "P4 input manifest")
    if manifest["p3_route_subset_manifest_path"] != P3_PILOT_ROUTE_SUBSET_MANIFEST.as_posix():
        raise ValueError("P4 input manifest lost P3 subset binding")
    if manifest["mesh_boundary_unit_preflight_manifest_path"] != P4_MESH_PREFLIGHT_MANIFEST.as_posix():
        raise ValueError("P4 input manifest preflight path drifted")
    if manifest["execution_authorization_record_path"] != P4_EXECUTION_AUTHORIZATION_RECORD.as_posix():
        raise ValueError("P4 input manifest authorization record path drifted")
    if manifest["selected_route_count"] != 3 or len(manifest["selected_route_ids"]) != 3:
        raise ValueError("P4 input manifest selected route count drifted")
    for row in manifest["selected_routes"]:
        if any(
            key.startswith("raw_") and key != "raw_arbitrary_unit_magnitude_final_gate_allowed"
            for key in row
        ):
            raise ValueError(f"P4 input manifest must not carry raw proxy fields: {row['candidate_id']}")
    return manifest


def build_mesh_preflight_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_preflight_registry(load_preflight_registry(project_root))
    return {
        "schema_version": "ev_nodi_p4_full_wave_green_tensor_mesh_boundary_unit_preflight_manifest_v1",
        "stage": P4_PREFLIGHT_STAGE,
        "manifest_role": "mesh_boundary_unit_preflight_no_mesh_generation",
        "lane_id": P4_PREFLIGHT_LANE_ID,
        "coordinate_system": "route_geometry_key_only_no_mesh_coordinates_generated",
        "length_unit": "nm",
        "wavelength_unit": "nm",
        "material_index_unit_convention": "future_contract_only_no_material_solution",
        "boundary_condition_family": "future_full_wave_or_green_tensor_contract_only_no_boundary_solve",
        "normalization_convention": "rank_pairwise_interpretability_only",
        "mesh_manifest_path": None,
        "mesh_manifest_sha256": None,
        "mesh_manifest_status": "not_generated_no_mesh_generation",
        "unit_registry_binding": {
            "length_unit": "nm",
            "wavelength_unit": "nm",
            "field_unit": "not_generated_no_solver_output",
        },
        "v1_bfp_to_angle_jacobian_applied": False,
        "audit_bfp_jacobian_applied": True,
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "p2_readiness_scope_preserved": True,
        "p3_pilot_design_scope_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "calibration_data_ingest_authorized": False,
        "new_mesh_generation_authorized": False,
        "operator_export_generation_authorized": False,
        "solver_output_generated": False,
        "route_promotion_authorized": False,
    }


def validate_mesh_preflight_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p4_full_wave_green_tensor_mesh_boundary_unit_preflight_manifest_v1"
    ):
        raise ValueError("unexpected P4 mesh preflight manifest schema")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P4 mesh preflight manifest")
    _require_true(manifest, TOP_LEVEL_TRUE_FIELDS, "P4 mesh preflight manifest")
    if manifest["mesh_manifest_path"] is not None or manifest["mesh_manifest_sha256"] is not None:
        raise ValueError("P4 must not declare a generated mesh manifest")
    if manifest["mesh_manifest_status"] != "not_generated_no_mesh_generation":
        raise ValueError("P4 mesh manifest status drifted")
    if manifest["v1_bfp_to_angle_jacobian_applied"] is not False:
        raise ValueError("P4 v1 Jacobian source flag drifted")
    if manifest["audit_bfp_jacobian_applied"] is not True:
        raise ValueError("P4 audit Jacobian sidecar flag drifted")
    return manifest


def build_execution_authorization_record(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_preflight_registry(load_preflight_registry(project_root))
    return {
        "schema_version": "ev_nodi_p4_full_wave_green_tensor_execution_authorization_record_v1",
        "stage": P4_PREFLIGHT_STAGE,
        "record_role": "execution_authorization_record_denies_execution",
        "lane_id": P4_PREFLIGHT_LANE_ID,
        "execution_authorization_decision": "not_authorized_phase4_dry_run_only",
        "explicit_later_phase_required": True,
        "later_phase_minimum_required_artifacts": [
            "reviewed_solver_input_manifest",
            "reviewed_mesh_boundary_unit_preflight_manifest",
            "separate_execution_authorization_record",
            "separate_solver_output_claim_boundary_review",
        ],
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "p2_readiness_scope_preserved": True,
        "p3_pilot_design_scope_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "calibration_data_ingest_authorized": False,
        "new_mesh_generation_authorized": False,
        "operator_export_generation_authorized": False,
        "solver_output_generated": False,
        "route_promotion_authorized": False,
    }


def validate_execution_authorization_record(manifest: dict[str, Any]) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p4_full_wave_green_tensor_execution_authorization_record_v1"
    ):
        raise ValueError("unexpected P4 execution authorization record schema")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P4 execution authorization record")
    _require_true(manifest, TOP_LEVEL_TRUE_FIELDS, "P4 execution authorization record")
    if manifest["execution_authorization_decision"] != "not_authorized_phase4_dry_run_only":
        raise ValueError("P4 execution authorization decision drifted")
    if manifest["explicit_later_phase_required"] is not True:
        raise ValueError("P4 must require a later phase for execution")
    return manifest


def _artifact_entry(project_root: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    relpath = artifact["path"]
    path = project_root / relpath
    is_self_manifest = relpath == P4_ARTIFACT_MANIFEST.as_posix()
    return {
        **artifact,
        "path_exists": True if is_self_manifest else path.is_file(),
        "sha256": None if is_self_manifest else sha256_file(path) if path.is_file() else None,
        "hash_role": "self_hash_excluded" if is_self_manifest else "content_sha256",
    }


def build_artifact_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_preflight_registry(load_preflight_registry(project_root))
    artifacts = [_artifact_entry(project_root, artifact) for artifact in registry["planned_artifacts"]]
    return {
        "schema_version": "ev_nodi_p4_bounded_solver_dry_run_preflight_artifact_manifest_v1",
        "stage": P4_PREFLIGHT_STAGE,
        "manifest_role": "dry_run_preflight_artifact_manifest_no_solver_execution",
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "p2_readiness_scope_preserved": True,
        "p3_pilot_design_scope_preserved": True,
        "physical_solver_execution_authorized": False,
        "measured_data_ingest_authorized": False,
        "calibration_data_ingest_authorized": False,
        "new_mesh_generation_authorized": False,
        "operator_export_generation_authorized": False,
        "solver_output_generated": False,
        "route_promotion_authorized": False,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "claim_boundary": {
            key: False for key in CLAIM_BOUNDARY_FALSE_FIELDS
        }
        | {"allowed_claim_level": "bounded_solver_dry_run_preflight_only"},
    }


def validate_artifact_manifest(
    manifest: dict[str, Any],
    project_root: Path = PROJECT_ROOT,
    *,
    allow_missing_self_manifest: bool = False,
) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p4_bounded_solver_dry_run_preflight_artifact_manifest_v1"
    ):
        raise ValueError("unexpected P4 artifact manifest schema")
    _require_false(manifest, TOP_LEVEL_FALSE_FIELDS, "P4 artifact manifest")
    _require_true(manifest, TOP_LEVEL_TRUE_FIELDS, "P4 artifact manifest")
    _validate_claim_boundary(manifest["claim_boundary"], "P4 artifact manifest")
    if manifest["artifact_count"] <= 0:
        raise ValueError("P4 artifact manifest must not be empty")
    for artifact in manifest["artifacts"]:
        _require_false(artifact, TOP_LEVEL_FALSE_FIELDS, artifact["artifact_id"])
        _require_true(artifact, TOP_LEVEL_TRUE_FIELDS, artifact["artifact_id"])
        is_self_manifest = artifact["path"] == P4_ARTIFACT_MANIFEST.as_posix()
        if (
            not (project_root / artifact["path"]).is_file()
            and not (allow_missing_self_manifest and is_self_manifest)
        ):
            raise ValueError(f"P4 artifact missing: {artifact['path']}")
        if artifact["hash_role"] == "content_sha256" and not artifact["sha256"]:
            raise ValueError(f"P4 artifact hash missing: {artifact['path']}")
    return manifest


def write_p3_binding_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_p3_binding_manifest(build_p3_binding_manifest(project_root))
    output_path = project_root / P4_P3_BINDING_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_input_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_input_manifest(build_input_manifest(project_root))
    output_path = project_root / P4_INPUT_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_mesh_preflight_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_mesh_preflight_manifest(
        build_mesh_preflight_manifest(project_root)
    )
    output_path = project_root / P4_MESH_PREFLIGHT_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_execution_authorization_record(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_execution_authorization_record(
        build_execution_authorization_record(project_root)
    )
    output_path = project_root / P4_EXECUTION_AUTHORIZATION_RECORD
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_artifact_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_artifact_manifest(
        build_artifact_manifest(project_root),
        project_root,
        allow_missing_self_manifest=True,
    )
    output_path = project_root / P4_ARTIFACT_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_preflight_package(project_root: Path = PROJECT_ROOT) -> list[Path]:
    return [
        write_p3_binding_manifest(project_root),
        write_input_manifest(project_root),
        write_mesh_preflight_manifest(project_root),
        write_execution_authorization_record(project_root),
        write_artifact_manifest(project_root),
    ]


def _assert_manifest_current(path: Path, expected: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    actual = _load_json_file(path)
    if actual != expected:
        raise ValueError(f"stale {label}: regenerate P4 dry-run preflight manifests")


def verify_preflight_package(project_root: Path = PROJECT_ROOT) -> list[str]:
    validate_preflight_registry(load_preflight_registry(project_root))
    p3_binding = validate_p3_binding_manifest(build_p3_binding_manifest(project_root))
    _assert_manifest_current(
        project_root / P4_P3_BINDING_MANIFEST,
        p3_binding,
        "P4 P3 binding manifest",
    )
    input_manifest = validate_input_manifest(build_input_manifest(project_root))
    _assert_manifest_current(
        project_root / P4_INPUT_MANIFEST,
        input_manifest,
        "P4 input manifest",
    )
    mesh_preflight = validate_mesh_preflight_manifest(
        build_mesh_preflight_manifest(project_root)
    )
    _assert_manifest_current(
        project_root / P4_MESH_PREFLIGHT_MANIFEST,
        mesh_preflight,
        "P4 mesh preflight manifest",
    )
    authorization_record = validate_execution_authorization_record(
        build_execution_authorization_record(project_root)
    )
    _assert_manifest_current(
        project_root / P4_EXECUTION_AUTHORIZATION_RECORD,
        authorization_record,
        "P4 execution authorization record",
    )
    artifact_manifest = validate_artifact_manifest(
        build_artifact_manifest(project_root),
        project_root,
    )
    _assert_manifest_current(
        project_root / P4_ARTIFACT_MANIFEST,
        artifact_manifest,
        "P4 artifact manifest",
    )

    lexicon = load_forbidden_claims_lexicon(project_root)
    for relpath in P4_TEXT_PATHS:
        text = (project_root / relpath).read_text(encoding="utf-8")
        if not claim_text_passes(text, lexicon):
            raise ValueError(f"P4 dry-run preflight claim language drifted: {relpath}")

    return [
        "PASS bounded_solver_dry_run_preflight_registry",
        "PASS bounded_solver_dry_run_preflight_p3_binding_manifest_current",
        "PASS bounded_solver_dry_run_preflight_input_manifest_current",
        "PASS bounded_solver_dry_run_preflight_mesh_preflight_manifest_current",
        "PASS bounded_solver_dry_run_preflight_execution_authorization_record_current",
        "PASS bounded_solver_dry_run_preflight_artifact_manifest_current",
        "PASS bounded_solver_dry_run_preflight_solver_execution_blocked",
        "PASS bounded_solver_dry_run_preflight_mesh_generation_blocked",
        "PASS bounded_solver_dry_run_preflight_solver_output_absent",
        "PASS bounded_solver_dry_run_preflight_claim_boundaries",
    ]
