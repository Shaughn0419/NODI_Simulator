"""P6 minimal bounded solver execution helpers.

This module executes only a deterministic minimal Green-kernel spot-check for
the three P4/P5-bound routes. It does not run a heavy full-wave solver, generate
meshes, export operators, ingest measured/calibration data, or promote routes.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from .post_v2_bounded_solver_authorization_gate import (
    P5_AUTHORIZATION_GATE_RECORD,
    P5_P4_BINDING_MANIFEST,
    REQUIRED_NEXT_AUTHORIZATION_PHRASE,
    validate_authorization_gate_record as validate_p5_authorization_gate_record,
    validate_p4_binding_manifest as validate_p5_p4_binding_manifest,
)
from .post_v2_bounded_solver_dry_run_preflight import (
    P4_INPUT_MANIFEST,
    validate_input_manifest as validate_p4_input_manifest,
)
from .realism_v2 import load_json_yaml
from .realism_v2_io import sha256_file, write_json_atomic
from .review_package import (
    PROJECT_ROOT,
    claim_text_passes,
    load_forbidden_claims_lexicon,
)


P6_EXECUTION_DIR = Path("results/post_v2_minimal_bounded_solver_execution")
P6_EXECUTION_REGISTRY = "configs/realism_v2/minimal_bounded_solver_execution_registry.yaml"
P6_EXECUTION_PLAN = "reports/103_EV_NODI_P6_minimal_bounded_solver_execution_plan.md"
P6_EXECUTION_README = P6_EXECUTION_DIR / "README.md"
P6_P5_BINDING_MANIFEST = P6_EXECUTION_DIR / "minimal_bounded_solver_execution_p5_binding_manifest.json"
P6_SOLVER_OUTPUT_CSV = P6_EXECUTION_DIR / "full_wave_green_tensor_minimal_solver_output.csv"
P6_SOLVER_OUTPUT_MANIFEST = P6_EXECUTION_DIR / "full_wave_green_tensor_minimal_solver_output_manifest.json"
P6_ARTIFACT_MANIFEST = P6_EXECUTION_DIR / "minimal_bounded_solver_execution_artifact_manifest.json"

P6_TEXT_PATHS: tuple[str, ...] = (
    P6_EXECUTION_REGISTRY,
    P6_EXECUTION_PLAN,
    P6_EXECUTION_README.as_posix(),
    "docs/schemas/minimal_bounded_solver_execution_p5_binding_manifest_schema.md",
    "docs/schemas/minimal_bounded_solver_execution_output_manifest_schema.md",
    "docs/schemas/minimal_bounded_solver_execution_artifact_manifest_schema.md",
)

P6_EXECUTION_STAGE = "P6_minimal_bounded_solver_execution_complete"
P6_EXECUTION_SCHEMA_VERSION = "ev_nodi_p6_minimal_bounded_solver_execution_registry_v1"
P6_LANE_ID = "full_wave_green_tensor_minimal_bounded_execution"

FALSE_FIELDS: tuple[str, ...] = (
    "calibrated_claim_allowed",
    "p0_release_conclusion_changed",
    "measured_data_ingest_authorized",
    "calibration_data_ingest_authorized",
    "new_mesh_generation_authorized",
    "operator_export_generation_authorized",
    "full_wave_solver_execution_authorized",
    "route_promotion_authorized",
    "raw_magnitude_final_gate_allowed",
    "solver_native_raw_magnitude_final_gate_allowed",
)

TRUE_FIELDS: tuple[str, ...] = (
    "p1_surrogate_risk_role_preserved",
    "p2_readiness_scope_preserved",
    "p3_pilot_design_scope_preserved",
    "p4_dry_run_preflight_scope_preserved",
    "p5_authorization_gate_scope_preserved",
    "physical_solver_execution_authorized",
    "minimal_bounded_solver_execution_authorized",
    "green_tensor_minimal_solver_execution_authorized",
    "solver_output_generated",
)

ALLOWED_TRUE_AUTHORITY_FIELDS: frozenset[str] = frozenset(
    {
        "physical_solver_execution_authorized",
        "minimal_bounded_solver_execution_authorized",
        "green_tensor_minimal_solver_execution_authorized",
        "solver_output_generation_authorized",
        "p5_binding_manifest_generation_authorized",
        "solver_output_manifest_generation_authorized",
        "artifact_manifest_generation_authorized",
        "verifier_authorized",
    }
)

REQUIRED_FALSE_AUTHORITY_FIELDS: frozenset[str] = frozenset(
    {
        "full_wave_solver_execution_authorized",
        "vector_solver_execution_authorized",
        "roughness_leakage_simulation_authorized",
        "transport_residence_time_simulation_authorized",
        "new_solver_case_generation_authorized",
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

OUTPUT_FIELDS: tuple[str, ...] = (
    "candidate_id",
    "route_key",
    "comparison_stratum",
    "route_role_final",
    "solver_execution_role",
    "wavelength_nm",
    "width_nm",
    "depth_nm",
    "dimensionless_width_over_wavelength",
    "dimensionless_depth_over_wavelength",
    "solver_native_real_trace_only",
    "solver_native_imag_trace_only",
    "solver_native_response_trace_only",
    "solver_response_rank",
    "solver_response_rank_percentile",
    "pairwise_order_signature",
    "calibrated_claim_allowed",
    "p0_release_conclusion_changed",
    "p1_surrogate_risk_role_preserved",
    "p2_readiness_scope_preserved",
    "p3_pilot_design_scope_preserved",
    "p4_dry_run_preflight_scope_preserved",
    "p5_authorization_gate_scope_preserved",
    "physical_solver_execution_authorized",
    "minimal_bounded_solver_execution_authorized",
    "green_tensor_minimal_solver_execution_authorized",
    "full_wave_solver_execution_authorized",
    "measured_data_ingest_authorized",
    "calibration_data_ingest_authorized",
    "new_mesh_generation_authorized",
    "operator_export_generation_authorized",
    "solver_output_generated",
    "raw_magnitude_final_gate_allowed",
    "solver_native_raw_magnitude_final_gate_allowed",
    "route_promotion_authorized",
)


def load_execution_registry(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return load_json_yaml(project_root / P6_EXECUTION_REGISTRY)


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
    if claims.get("allowed_claim_level") != "minimal_bounded_solver_trace_only":
        raise ValueError(f"{context} claim level drifted")


def _validate_implementation_authority(authority: dict[str, Any]) -> None:
    if set(authority) != REQUIRED_AUTHORITY_FIELDS:
        raise ValueError("P6 implementation authority field set drifted")
    for key, value in authority.items():
        expected = key in ALLOWED_TRUE_AUTHORITY_FIELDS
        if value is not expected:
            raise ValueError(f"P6 implementation authority drifted: {key}")


def validate_execution_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema_version") != P6_EXECUTION_SCHEMA_VERSION:
        raise ValueError("unexpected P6 execution registry schema")
    if registry.get("stage") != P6_EXECUTION_STAGE:
        raise ValueError("unexpected P6 execution stage")
    if registry.get("execution_role") != "minimal_bounded_solver_execution_trace_only":
        raise ValueError("P6 execution role drifted")
    _require_false(registry, FALSE_FIELDS, "P6 registry")
    _require_true(registry, TRUE_FIELDS, "P6 registry")
    _validate_implementation_authority(registry["implementation_authority"])

    authorization = registry["authorization_evidence"]
    if authorization["required_next_authorization_phrase"] != REQUIRED_NEXT_AUTHORIZATION_PHRASE:
        raise ValueError("P6 authorization phrase drifted")
    if authorization["user_authorization_phrase_received"] != REQUIRED_NEXT_AUTHORIZATION_PHRASE:
        raise ValueError("P6 user authorization phrase drifted")
    if authorization["p5_authorization_gate_record_path"] != P5_AUTHORIZATION_GATE_RECORD.as_posix():
        raise ValueError("P6 P5 authorization gate path drifted")
    _require_true(authorization, TRUE_FIELDS, "P6 authorization evidence")
    _require_false(authorization, FALSE_FIELDS, "P6 authorization evidence")

    _validate_claim_boundary(registry["claim_governance"], "P6 registry")
    interpretability = registry["interpretability_governance"]
    if set(interpretability["allowed_final_gate_metric_families"]) != {
        "rank",
        "rank_percentile",
        "pairwise_inversion",
    }:
        raise ValueError("P6 final gate families drifted")
    _require_false(interpretability, FALSE_FIELDS, "P6 interpretability")

    solver = registry["solver_contract"]
    if solver["lane_id"] != P6_LANE_ID:
        raise ValueError("P6 solver lane drifted")
    if solver["solver_runtime"] != "deterministic_minimal_green_kernel_v1":
        raise ValueError("P6 solver runtime drifted")
    if solver["selected_route_count"] != 3:
        raise ValueError("P6 selected route count drifted")
    _require_true(solver, TRUE_FIELDS, "P6 solver contract")
    _require_false(solver, FALSE_FIELDS, "P6 solver contract")

    schema = registry["artifact_manifest_schema"]
    required = set(schema["required_artifact_fields"])
    for field in (*FALSE_FIELDS, *TRUE_FIELDS):
        if field not in required:
            raise ValueError(f"P6 artifact schema missing guard field: {field}")
    for artifact in registry["planned_artifacts"]:
        if not required.issubset(artifact):
            raise ValueError(f"P6 artifact missing schema fields: {artifact['artifact_id']}")
        _require_false(artifact, FALSE_FIELDS, artifact["artifact_id"])
        _require_true(artifact, TRUE_FIELDS, artifact["artifact_id"])
    return registry


def _load_p5_record(project_root: Path) -> dict[str, Any]:
    return validate_p5_authorization_gate_record(
        _load_json_file(project_root / P5_AUTHORIZATION_GATE_RECORD)
    )


def _load_p5_binding(project_root: Path) -> dict[str, Any]:
    return validate_p5_p4_binding_manifest(
        _load_json_file(project_root / P5_P4_BINDING_MANIFEST)
    )


def _load_p4_input(project_root: Path) -> dict[str, Any]:
    return validate_p4_input_manifest(_load_json_file(project_root / P4_INPUT_MANIFEST))


def _parse_route_key(route_key: str) -> tuple[int, int, int]:
    wavelength, width, depth = route_key.split("/")
    return int(wavelength), int(width.removeprefix("W")), int(depth.removeprefix("D"))


def _green_kernel_trace(wavelength_nm: int, width_nm: int, depth_nm: int) -> tuple[float, float, float]:
    width_ratio = width_nm / wavelength_nm
    depth_ratio = depth_nm / wavelength_nm
    attenuation = 1.0 / (1.0 + width_ratio**2 + 0.5 * depth_ratio)
    phase = 2.0 * math.pi * depth_ratio
    real = attenuation * math.cos(phase)
    imag = attenuation * math.sin(phase)
    response = math.hypot(real, imag)
    return real, imag, response


def build_solver_rows(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    validate_execution_registry(load_execution_registry(project_root))
    p4_input = _load_p4_input(project_root)
    rows = []
    for route in p4_input["selected_routes"]:
        wavelength_nm, width_nm, depth_nm = _parse_route_key(route["route_key"])
        real, imag, response = _green_kernel_trace(wavelength_nm, width_nm, depth_nm)
        rows.append(
            {
                "candidate_id": route["candidate_id"],
                "route_key": route["route_key"],
                "comparison_stratum": route["comparison_stratum"],
                "route_role_final": route["route_role_final"],
                "solver_execution_role": "minimal_bounded_green_kernel_trace_only",
                "wavelength_nm": wavelength_nm,
                "width_nm": width_nm,
                "depth_nm": depth_nm,
                "dimensionless_width_over_wavelength": round(width_nm / wavelength_nm, 9),
                "dimensionless_depth_over_wavelength": round(depth_nm / wavelength_nm, 9),
                "solver_native_real_trace_only": round(real, 12),
                "solver_native_imag_trace_only": round(imag, 12),
                "solver_native_response_trace_only": round(response, 12),
            }
        )
    rows.sort(key=lambda row: (-row["solver_native_response_trace_only"], row["candidate_id"]))
    denominator = max(len(rows) - 1, 1)
    for index, row in enumerate(rows, start=1):
        row["solver_response_rank"] = index
        row["solver_response_rank_percentile"] = round((index - 1) / denominator, 9)
        row["pairwise_order_signature"] = f"{index}_of_{len(rows)}"
        row.update(
            {
                "calibrated_claim_allowed": False,
                "p0_release_conclusion_changed": False,
                "p1_surrogate_risk_role_preserved": True,
                "p2_readiness_scope_preserved": True,
                "p3_pilot_design_scope_preserved": True,
                "p4_dry_run_preflight_scope_preserved": True,
                "p5_authorization_gate_scope_preserved": True,
                "physical_solver_execution_authorized": True,
                "minimal_bounded_solver_execution_authorized": True,
                "green_tensor_minimal_solver_execution_authorized": True,
                "full_wave_solver_execution_authorized": False,
                "measured_data_ingest_authorized": False,
                "calibration_data_ingest_authorized": False,
                "new_mesh_generation_authorized": False,
                "operator_export_generation_authorized": False,
                "solver_output_generated": True,
                "raw_magnitude_final_gate_allowed": False,
                "solver_native_raw_magnitude_final_gate_allowed": False,
                "route_promotion_authorized": False,
            }
        )
    return rows


def validate_solver_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(rows) != 3:
        raise ValueError("P6 solver output must contain exactly three routes")
    if [row["solver_response_rank"] for row in rows] != [1, 2, 3]:
        raise ValueError("P6 solver ranks drifted")
    for row in rows:
        for field in OUTPUT_FIELDS:
            if field not in row:
                raise ValueError(f"P6 solver row missing field: {field}")
        _require_false(row, FALSE_FIELDS, row["candidate_id"])
        _require_true(row, TRUE_FIELDS, row["candidate_id"])
        if row["solver_execution_role"] != "minimal_bounded_green_kernel_trace_only":
            raise ValueError(f"P6 solver role drifted: {row['candidate_id']}")
    return rows


def write_solver_output_csv(project_root: Path = PROJECT_ROOT) -> Path:
    rows = validate_solver_rows(build_solver_rows(project_root))
    output_path = project_root / P6_SOLVER_OUTPUT_CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(OUTPUT_FIELDS))
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def _read_solver_output_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    parsed = []
    for row in rows:
        parsed.append(
            {
                **row,
                "wavelength_nm": int(row["wavelength_nm"]),
                "width_nm": int(row["width_nm"]),
                "depth_nm": int(row["depth_nm"]),
                "dimensionless_width_over_wavelength": float(row["dimensionless_width_over_wavelength"]),
                "dimensionless_depth_over_wavelength": float(row["dimensionless_depth_over_wavelength"]),
                "solver_native_real_trace_only": float(row["solver_native_real_trace_only"]),
                "solver_native_imag_trace_only": float(row["solver_native_imag_trace_only"]),
                "solver_native_response_trace_only": float(row["solver_native_response_trace_only"]),
                "solver_response_rank": int(row["solver_response_rank"]),
                "solver_response_rank_percentile": float(row["solver_response_rank_percentile"]),
                **{
                    key: row[key] == "True"
                    for key in (*FALSE_FIELDS, *TRUE_FIELDS)
                    if key in row
                },
            }
        )
    return parsed


def build_p5_binding_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_execution_registry(load_execution_registry(project_root))
    p5_record = _load_p5_record(project_root)
    p5_binding = _load_p5_binding(project_root)
    return {
        "schema_version": "ev_nodi_p6_minimal_bounded_solver_execution_p5_binding_manifest_v1",
        "stage": P6_EXECUTION_STAGE,
        "manifest_role": "p5_authorization_gate_binding_for_minimal_execution",
        "p5_authorization_gate_record_path": P5_AUTHORIZATION_GATE_RECORD.as_posix(),
        "p5_authorization_gate_record_sha256": sha256_file(project_root / P5_AUTHORIZATION_GATE_RECORD),
        "p5_authorization_gate_decision": p5_record["authorization_gate_decision"],
        "required_next_authorization_phrase": p5_record["required_next_authorization_phrase"],
        "user_authorization_phrase_received": REQUIRED_NEXT_AUTHORIZATION_PHRASE,
        "p5_p4_binding_manifest_path": P5_P4_BINDING_MANIFEST.as_posix(),
        "p5_p4_binding_manifest_sha256": sha256_file(project_root / P5_P4_BINDING_MANIFEST),
        "bound_p4_manifest_count": p5_binding["bound_manifest_count"],
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "p2_readiness_scope_preserved": True,
        "p3_pilot_design_scope_preserved": True,
        "p4_dry_run_preflight_scope_preserved": True,
        "p5_authorization_gate_scope_preserved": True,
        "physical_solver_execution_authorized": True,
        "minimal_bounded_solver_execution_authorized": True,
        "green_tensor_minimal_solver_execution_authorized": True,
        "solver_output_generated": True,
        "measured_data_ingest_authorized": False,
        "calibration_data_ingest_authorized": False,
        "new_mesh_generation_authorized": False,
        "operator_export_generation_authorized": False,
        "full_wave_solver_execution_authorized": False,
        "route_promotion_authorized": False,
        "raw_magnitude_final_gate_allowed": False,
        "solver_native_raw_magnitude_final_gate_allowed": False,
    }


def validate_p5_binding_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p6_minimal_bounded_solver_execution_p5_binding_manifest_v1"
    ):
        raise ValueError("unexpected P6 P5 binding manifest schema")
    if manifest["p5_authorization_gate_record_path"] != P5_AUTHORIZATION_GATE_RECORD.as_posix():
        raise ValueError("P6 P5 binding gate record path drifted")
    if manifest["p5_p4_binding_manifest_path"] != P5_P4_BINDING_MANIFEST.as_posix():
        raise ValueError("P6 P5 binding P4 manifest path drifted")
    if (
        manifest["p5_authorization_gate_decision"]
        != "not_authorized_pending_explicit_later_phase_execution_request"
    ):
        raise ValueError("P6 P5 binding gate decision drifted")
    if manifest["required_next_authorization_phrase"] != REQUIRED_NEXT_AUTHORIZATION_PHRASE:
        raise ValueError("P6 P5 binding phrase drifted")
    if manifest["user_authorization_phrase_received"] != REQUIRED_NEXT_AUTHORIZATION_PHRASE:
        raise ValueError("P6 user authorization phrase missing")
    _require_false(manifest, FALSE_FIELDS, "P6 P5 binding manifest")
    _require_true(manifest, TRUE_FIELDS, "P6 P5 binding manifest")
    return manifest


def build_solver_output_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    rows = validate_solver_rows(_read_solver_output_csv(project_root / P6_SOLVER_OUTPUT_CSV))
    return {
        "schema_version": "ev_nodi_p6_minimal_bounded_solver_execution_output_manifest_v1",
        "stage": P6_EXECUTION_STAGE,
        "manifest_role": "minimal_bounded_solver_output_manifest_trace_only",
        "output_path": P6_SOLVER_OUTPUT_CSV.as_posix(),
        "output_sha256": sha256_file(project_root / P6_SOLVER_OUTPUT_CSV),
        "output_row_count": len(rows),
        "selected_route_ids": [row["candidate_id"] for row in rows],
        "allowed_final_gate_metric_families": [
            "rank",
            "rank_percentile",
            "pairwise_inversion",
        ],
        "raw_solver_native_fields_role": "trace_only_not_final_gate",
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "p2_readiness_scope_preserved": True,
        "p3_pilot_design_scope_preserved": True,
        "p4_dry_run_preflight_scope_preserved": True,
        "p5_authorization_gate_scope_preserved": True,
        "physical_solver_execution_authorized": True,
        "minimal_bounded_solver_execution_authorized": True,
        "green_tensor_minimal_solver_execution_authorized": True,
        "solver_output_generated": True,
        "measured_data_ingest_authorized": False,
        "calibration_data_ingest_authorized": False,
        "new_mesh_generation_authorized": False,
        "operator_export_generation_authorized": False,
        "full_wave_solver_execution_authorized": False,
        "route_promotion_authorized": False,
        "raw_magnitude_final_gate_allowed": False,
        "solver_native_raw_magnitude_final_gate_allowed": False,
    }


def validate_solver_output_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if (
        manifest.get("schema_version")
        != "ev_nodi_p6_minimal_bounded_solver_execution_output_manifest_v1"
    ):
        raise ValueError("unexpected P6 solver output manifest schema")
    _require_false(manifest, FALSE_FIELDS, "P6 solver output manifest")
    _require_true(manifest, TRUE_FIELDS, "P6 solver output manifest")
    if manifest["output_row_count"] != 3:
        raise ValueError("P6 solver output row count drifted")
    if manifest["output_path"] != P6_SOLVER_OUTPUT_CSV.as_posix():
        raise ValueError("P6 solver output path drifted")
    if set(manifest["allowed_final_gate_metric_families"]) != {
        "rank",
        "rank_percentile",
        "pairwise_inversion",
    }:
        raise ValueError("P6 solver output final gate families drifted")
    if manifest["raw_solver_native_fields_role"] != "trace_only_not_final_gate":
        raise ValueError("P6 raw solver-native role drifted")
    return manifest


def _artifact_entry(project_root: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    relpath = artifact["path"]
    path = project_root / relpath
    is_self_manifest = relpath == P6_ARTIFACT_MANIFEST.as_posix()
    return {
        **artifact,
        "path_exists": True if is_self_manifest else path.is_file(),
        "sha256": None if is_self_manifest else sha256_file(path) if path.is_file() else None,
        "hash_role": "self_hash_excluded" if is_self_manifest else "content_sha256",
    }


def build_artifact_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    registry = validate_execution_registry(load_execution_registry(project_root))
    artifacts = [_artifact_entry(project_root, artifact) for artifact in registry["planned_artifacts"]]
    return {
        "schema_version": "ev_nodi_p6_minimal_bounded_solver_execution_artifact_manifest_v1",
        "stage": P6_EXECUTION_STAGE,
        "manifest_role": "minimal_bounded_solver_execution_artifact_manifest",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "claim_boundary": {
            key: False for key in CLAIM_BOUNDARY_FALSE_FIELDS
        }
        | {"allowed_claim_level": "minimal_bounded_solver_trace_only"},
        "calibrated_claim_allowed": False,
        "p0_release_conclusion_changed": False,
        "p1_surrogate_risk_role_preserved": True,
        "p2_readiness_scope_preserved": True,
        "p3_pilot_design_scope_preserved": True,
        "p4_dry_run_preflight_scope_preserved": True,
        "p5_authorization_gate_scope_preserved": True,
        "physical_solver_execution_authorized": True,
        "minimal_bounded_solver_execution_authorized": True,
        "green_tensor_minimal_solver_execution_authorized": True,
        "solver_output_generated": True,
        "measured_data_ingest_authorized": False,
        "calibration_data_ingest_authorized": False,
        "new_mesh_generation_authorized": False,
        "operator_export_generation_authorized": False,
        "full_wave_solver_execution_authorized": False,
        "route_promotion_authorized": False,
        "raw_magnitude_final_gate_allowed": False,
        "solver_native_raw_magnitude_final_gate_allowed": False,
    }


def validate_artifact_manifest(
    manifest: dict[str, Any],
    project_root: Path = PROJECT_ROOT,
    *,
    allow_missing_self_manifest: bool = False,
) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p6_minimal_bounded_solver_execution_artifact_manifest_v1":
        raise ValueError("unexpected P6 artifact manifest schema")
    _require_false(manifest, FALSE_FIELDS, "P6 artifact manifest")
    _require_true(manifest, TRUE_FIELDS, "P6 artifact manifest")
    _validate_claim_boundary(manifest["claim_boundary"], "P6 artifact manifest")
    for artifact in manifest["artifacts"]:
        _require_false(artifact, FALSE_FIELDS, artifact["artifact_id"])
        _require_true(artifact, TRUE_FIELDS, artifact["artifact_id"])
        is_self_manifest = artifact["path"] == P6_ARTIFACT_MANIFEST.as_posix()
        if (
            not (project_root / artifact["path"]).is_file()
            and not (allow_missing_self_manifest and is_self_manifest)
        ):
            raise ValueError(f"P6 artifact missing: {artifact['path']}")
        if artifact["hash_role"] == "content_sha256" and not artifact["sha256"]:
            raise ValueError(f"P6 artifact hash missing: {artifact['path']}")
    return manifest


def write_p5_binding_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_p5_binding_manifest(build_p5_binding_manifest(project_root))
    output_path = project_root / P6_P5_BINDING_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_solver_output_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_solver_output_manifest(build_solver_output_manifest(project_root))
    output_path = project_root / P6_SOLVER_OUTPUT_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_artifact_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_artifact_manifest(
        build_artifact_manifest(project_root),
        project_root,
        allow_missing_self_manifest=True,
    )
    output_path = project_root / P6_ARTIFACT_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_execution_package(project_root: Path = PROJECT_ROOT) -> list[Path]:
    p5_binding = write_p5_binding_manifest(project_root)
    solver_output = write_solver_output_csv(project_root)
    solver_manifest = write_solver_output_manifest(project_root)
    artifact_manifest = write_artifact_manifest(project_root)
    return [p5_binding, solver_output, solver_manifest, artifact_manifest]


def _assert_manifest_current(path: Path, expected: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    actual = _load_json_file(path)
    if actual != expected:
        raise ValueError(f"stale {label}: regenerate P6 execution manifests")


def verify_execution_package(project_root: Path = PROJECT_ROOT) -> list[str]:
    validate_execution_registry(load_execution_registry(project_root))
    expected_rows = validate_solver_rows(build_solver_rows(project_root))
    actual_rows = validate_solver_rows(_read_solver_output_csv(project_root / P6_SOLVER_OUTPUT_CSV))
    if actual_rows != expected_rows:
        raise ValueError("stale P6 solver output CSV: regenerate execution package")
    p5_binding = validate_p5_binding_manifest(build_p5_binding_manifest(project_root))
    _assert_manifest_current(
        project_root / P6_P5_BINDING_MANIFEST,
        p5_binding,
        "P6 P5 binding manifest",
    )
    solver_output_manifest = validate_solver_output_manifest(
        build_solver_output_manifest(project_root)
    )
    _assert_manifest_current(
        project_root / P6_SOLVER_OUTPUT_MANIFEST,
        solver_output_manifest,
        "P6 solver output manifest",
    )
    artifact_manifest = validate_artifact_manifest(
        build_artifact_manifest(project_root),
        project_root,
    )
    _assert_manifest_current(
        project_root / P6_ARTIFACT_MANIFEST,
        artifact_manifest,
        "P6 artifact manifest",
    )

    lexicon = load_forbidden_claims_lexicon(project_root)
    for relpath in P6_TEXT_PATHS:
        text = (project_root / relpath).read_text(encoding="utf-8")
        if not claim_text_passes(text, lexicon):
            raise ValueError(f"P6 execution claim language drifted: {relpath}")

    return [
        "PASS minimal_bounded_solver_execution_registry",
        "PASS minimal_bounded_solver_execution_p5_binding_manifest_current",
        "PASS minimal_bounded_solver_execution_output_csv_current",
        "PASS minimal_bounded_solver_execution_output_manifest_current",
        "PASS minimal_bounded_solver_execution_artifact_manifest_current",
        "PASS minimal_bounded_solver_execution_no_mesh_or_operator_export",
        "PASS minimal_bounded_solver_execution_claim_boundaries",
    ]
