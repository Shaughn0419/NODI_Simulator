"""P16 sixth bounded solver lane execution helpers.

This module runs only the user-authorized sixth bounded trace lane for the
three P4/P6/P8/P10/P12/P14-bound routes. It does not run full-wave/vector/roughness/
transport solvers, generate meshes, export operators, ingest measured or
calibration data, or promote routes.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from .post_v2_bounded_solver_dry_run_preflight import (
    P4_INPUT_MANIFEST,
    validate_input_manifest as validate_p4_input_manifest,
)
from .post_v2_p14_closure_p15_authorization_design import (
    P15_NEXT_AUTHORIZATION_GATE_RECORD,
    P15_P14_CLOSURE_BINDING_MANIFEST,
    P15_REQUIRED_FUTURE_AUTHORIZATION_PHRASE,
    validate_p15_next_authorization_gate_record,
    validate_p15_p14_closure_binding_manifest,
)
from .post_v2_fifth_bounded_solver_lane_execution import (
    P14_SOLVER_OUTPUT_CSV,
    P14_SOLVER_OUTPUT_MANIFEST,
    validate_solver_output_manifest as validate_p14_solver_output_manifest,
    validate_solver_rows as validate_p14_solver_rows,
)
from .realism_v2 import load_json_yaml
from .realism_v2_io import sha256_file, write_json_atomic
from .review_package import PROJECT_ROOT, claim_text_passes, load_forbidden_claims_lexicon


P16_EXECUTION_DIR = Path("results/post_v2_sixth_bounded_solver_lane_execution")
P16_EXECUTION_REGISTRY = "configs/realism_v2/sixth_bounded_solver_lane_execution_registry.yaml"
P16_EXECUTION_PLAN = "reports/117_EV_NODI_P16_sixth_bounded_solver_lane_execution_plan.md"
P16_EXECUTION_README = P16_EXECUTION_DIR / "README.md"
P16_P15_AUTHORIZATION_BINDING_MANIFEST = (
    P16_EXECUTION_DIR / "sixth_bounded_solver_lane_execution_p15_authorization_binding_manifest.json"
)
P16_SOLVER_OUTPUT_CSV = P16_EXECUTION_DIR / "sixth_bounded_solver_lane_trace_output.csv"
P16_SOLVER_OUTPUT_MANIFEST = P16_EXECUTION_DIR / "sixth_bounded_solver_lane_trace_output_manifest.json"
P16_ARTIFACT_MANIFEST = P16_EXECUTION_DIR / "sixth_bounded_solver_lane_execution_artifact_manifest.json"

P16_EXECUTION_STAGE = "P16_sixth_bounded_solver_lane_execution_complete"
P16_EXECUTION_SCHEMA_VERSION = "ev_nodi_p16_sixth_bounded_solver_lane_execution_registry_v1"
P16_LANE_ID = "sixth_bounded_phase_curvature_residual_trace_execution"
P16_SOLVER_RUNTIME = "deterministic_bounded_phase_curvature_residual_kernel_v1"

P16_TEXT_PATHS: tuple[str, ...] = (
    P16_EXECUTION_REGISTRY,
    P16_EXECUTION_PLAN,
    P16_EXECUTION_README.as_posix(),
    "docs/schemas/sixth_bounded_solver_lane_execution_p15_authorization_binding_manifest_schema.md",
    "docs/schemas/sixth_bounded_solver_lane_execution_output_manifest_schema.md",
    "docs/schemas/sixth_bounded_solver_lane_execution_artifact_manifest_schema.md",
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
    "physical_solver_execution_authorized",
    "sixth_bounded_solver_lane_execution_authorized",
    "solver_output_generated",
)

ALLOWED_TRUE_AUTHORITY_FIELDS: frozenset[str] = frozenset(
    {
        "physical_solver_execution_authorized",
        "sixth_bounded_solver_lane_execution_authorized",
        "sixth_lane_trace_output_generation_authorized",
        "p15_authorization_binding_manifest_generation_authorized",
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
    "main_660_redefinition_authorized",
    "optional_660_W900_D1400_redefines_main_660",
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
    "p14_fifth_lane_response_rank",
    "p14_fifth_lane_pairwise_order_signature",
    "solver_native_phase_residual_trace_only",
    "solver_native_curvature_residual_trace_only",
    "solver_native_sixth_lane_response_trace_only",
    "sixth_lane_response_rank",
    "sixth_lane_response_rank_percentile",
    "sixth_lane_pairwise_order_signature",
    "sixth_lane_vs_p14_rank_delta",
    "calibrated_claim_allowed",
    "p0_release_conclusion_changed",
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
    "physical_solver_execution_authorized",
    "sixth_bounded_solver_lane_execution_authorized",
    "full_wave_solver_execution_authorized",
    "vector_solver_execution_authorized",
    "roughness_leakage_simulation_authorized",
    "transport_residence_time_simulation_authorized",
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
    return load_json_yaml(project_root / P16_EXECUTION_REGISTRY)


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
    return dict.fromkeys(FALSE_FIELDS, False) | dict.fromkeys(TRUE_FIELDS, True)


def _validate_guard_fields(mapping: dict[str, Any], context: str) -> None:
    _require_false(mapping, FALSE_FIELDS, context)
    _require_true(mapping, TRUE_FIELDS, context)


def _validate_claim_boundary(claims: dict[str, Any], context: str) -> None:
    _require_false(claims, CLAIM_BOUNDARY_FALSE_FIELDS, context)
    if claims.get("allowed_claim_level") != "sixth_bounded_solver_lane_trace_only":
        raise ValueError(f"{context} claim level drifted")


def _validate_implementation_authority(authority: dict[str, Any]) -> None:
    if set(authority) != REQUIRED_AUTHORITY_FIELDS:
        raise ValueError("P16 implementation authority field set drifted")
    for key, value in authority.items():
        expected = key in ALLOWED_TRUE_AUTHORITY_FIELDS
        if value is not expected:
            raise ValueError(f"P16 implementation authority drifted: {key}")


def validate_execution_registry(registry: dict[str, Any]) -> dict[str, Any]:
    if registry.get("schema_version") != P16_EXECUTION_SCHEMA_VERSION:
        raise ValueError("unexpected P16 execution registry schema")
    if registry.get("stage") != P16_EXECUTION_STAGE:
        raise ValueError("unexpected P16 execution stage")
    if registry.get("execution_role") != "sixth_bounded_solver_lane_execution_trace_only":
        raise ValueError("P16 execution role drifted")
    _validate_guard_fields(registry, "P16 registry")
    _validate_implementation_authority(registry["implementation_authority"])

    authorization = registry["authorization_evidence"]
    if authorization["p15_authorization_gate_record_path"] != P15_NEXT_AUTHORIZATION_GATE_RECORD.as_posix():
        raise ValueError("P16 P15 gate record path drifted")
    if authorization["p15_p14_closure_binding_manifest_path"] != P15_P14_CLOSURE_BINDING_MANIFEST.as_posix():
        raise ValueError("P16 P15 closure binding path drifted")
    if authorization["required_future_authorization_phrase"] != P15_REQUIRED_FUTURE_AUTHORIZATION_PHRASE:
        raise ValueError("P16 authorization phrase drifted")
    if authorization["user_authorization_phrase_received"] != P15_REQUIRED_FUTURE_AUTHORIZATION_PHRASE:
        raise ValueError("P16 user authorization phrase drifted")
    _validate_guard_fields(authorization, "P16 authorization evidence")
    _validate_claim_boundary(registry["claim_governance"], "P16 registry")

    interpretability = registry["interpretability_governance"]
    if set(interpretability["allowed_final_gate_metric_families"]) != {
        "rank",
        "rank_percentile",
        "pairwise_inversion",
    }:
        raise ValueError("P16 final gate families drifted")
    if interpretability["raw_solver_native_fields_role"] != "trace_only_not_final_gate":
        raise ValueError("P16 raw solver-native role drifted")
    _validate_guard_fields(interpretability, "P16 interpretability")

    solver = registry["solver_contract"]
    if solver["lane_id"] != P16_LANE_ID:
        raise ValueError("P16 solver lane drifted")
    if solver["solver_runtime"] != P16_SOLVER_RUNTIME:
        raise ValueError("P16 solver runtime drifted")
    if solver["selected_route_count"] != 3:
        raise ValueError("P16 selected route count drifted")
    if solver["route_subset_binding_path"] != P4_INPUT_MANIFEST.as_posix():
        raise ValueError("P16 route subset binding path drifted")
    if solver["p14_trace_context_path"] != P14_SOLVER_OUTPUT_CSV.as_posix():
        raise ValueError("P16 P14 trace context path drifted")
    _validate_guard_fields(solver, "P16 solver contract")

    required = set(registry["artifact_manifest_schema"]["required_artifact_fields"])
    for field in (*FALSE_FIELDS, *TRUE_FIELDS):
        if field not in required:
            raise ValueError(f"P16 artifact schema missing guard field: {field}")
    for artifact in registry["planned_artifacts"]:
        if not required.issubset(artifact):
            raise ValueError(f"P16 artifact missing schema fields: {artifact['artifact_id']}")
        _validate_guard_fields(artifact, artifact["artifact_id"])
    return registry


def _read_p14_solver_output_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    parsed = [
        {
            **row,
            "wavelength_nm": int(row["wavelength_nm"]),
            "width_nm": int(row["width_nm"]),
            "depth_nm": int(row["depth_nm"]),
            "dimensionless_width_over_wavelength": float(row["dimensionless_width_over_wavelength"]),
            "dimensionless_depth_over_wavelength": float(row["dimensionless_depth_over_wavelength"]),
            "p12_fourth_lane_response_rank": int(row["p12_fourth_lane_response_rank"]),
            "solver_native_phase_residual_trace_only": float(
                row["solver_native_phase_residual_trace_only"]
            ),
            "solver_native_curvature_residual_trace_only": float(
                row["solver_native_curvature_residual_trace_only"]
            ),
            "solver_native_fifth_lane_response_trace_only": float(
                row["solver_native_fifth_lane_response_trace_only"]
            ),
            "fifth_lane_response_rank": int(row["fifth_lane_response_rank"]),
            "fifth_lane_response_rank_percentile": float(row["fifth_lane_response_rank_percentile"]),
            "fifth_lane_vs_p12_rank_delta": int(row["fifth_lane_vs_p12_rank_delta"]),
            **{
                key: row[key] == "True"
                for key in row
                if key.endswith(
                    ("_authorized", "_allowed", "_generated", "_preserved")
                )
                or key == "p0_release_conclusion_changed"
            },
        }
        for row in rows
    ]
    return validate_p14_solver_rows(parsed)


def _load_p4_input(project_root: Path) -> dict[str, Any]:
    return validate_p4_input_manifest(_load_json_file(project_root / P4_INPUT_MANIFEST))


def _sixth_lane_kernel(
    wavelength_nm: int,
    width_nm: int,
    depth_nm: int,
    p14_response: float,
) -> tuple[float, float, float]:
    width_ratio = width_nm / wavelength_nm
    depth_ratio = depth_nm / wavelength_nm
    phase_residual = math.sin(math.pi * width_ratio / (1.0 + depth_ratio)) - math.cos(
        math.pi * depth_ratio / (1.0 + width_ratio)
    )
    curvature_residual = (width_ratio * depth_ratio) / (1.0 + width_ratio**2 + depth_ratio**2)
    response = abs(phase_residual) * (1.0 + curvature_residual) / (1.0 + p14_response)
    return phase_residual, curvature_residual, response


def build_solver_rows(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    validate_execution_registry(load_execution_registry(project_root))
    p4_input = _load_p4_input(project_root)
    validate_p14_solver_output_manifest(_load_json_file(project_root / P14_SOLVER_OUTPUT_MANIFEST))
    p14_rows = {
        row["candidate_id"]: row
        for row in _read_p14_solver_output_csv(project_root / P14_SOLVER_OUTPUT_CSV)
    }
    if set(p14_rows) != set(p4_input["selected_route_ids"]):
        raise ValueError("P16 P14/P4 selected route set drifted")
    rows: list[dict[str, Any]] = []
    for route in p4_input["selected_routes"]:
        p14_row = p14_rows[route["candidate_id"]]
        phase_residual, curvature_residual, response = _sixth_lane_kernel(
            p14_row["wavelength_nm"],
            p14_row["width_nm"],
            p14_row["depth_nm"],
            p14_row["solver_native_fifth_lane_response_trace_only"],
        )
        rows.append(
            {
                "candidate_id": route["candidate_id"],
                "route_key": route["route_key"],
                "comparison_stratum": route["comparison_stratum"],
                "route_role_final": route["route_role_final"],
                "solver_execution_role": "sixth_bounded_phase_curvature_residual_trace_only",
                "wavelength_nm": p14_row["wavelength_nm"],
                "width_nm": p14_row["width_nm"],
                "depth_nm": p14_row["depth_nm"],
                "dimensionless_width_over_wavelength": p14_row["dimensionless_width_over_wavelength"],
                "dimensionless_depth_over_wavelength": p14_row["dimensionless_depth_over_wavelength"],
                "p14_fifth_lane_response_rank": p14_row["fifth_lane_response_rank"],
                "p14_fifth_lane_pairwise_order_signature": p14_row["fifth_lane_pairwise_order_signature"],
                "solver_native_phase_residual_trace_only": round(phase_residual, 12),
                "solver_native_curvature_residual_trace_only": round(curvature_residual, 12),
                "solver_native_sixth_lane_response_trace_only": round(response, 12),
            }
        )
    rows.sort(key=lambda row: (-row["solver_native_sixth_lane_response_trace_only"], row["candidate_id"]))
    denominator = max(len(rows) - 1, 1)
    for index, row in enumerate(rows, start=1):
        row["sixth_lane_response_rank"] = index
        row["sixth_lane_response_rank_percentile"] = round((index - 1) / denominator, 9)
        row["sixth_lane_pairwise_order_signature"] = f"{index}_of_{len(rows)}"
        row["sixth_lane_vs_p14_rank_delta"] = (
            row["sixth_lane_response_rank"] - row["p14_fifth_lane_response_rank"]
        )
        row.update(_guard_payload())
    return rows


def validate_solver_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(rows) != 3:
        raise ValueError("P16 solver output must contain exactly three routes")
    if [row["sixth_lane_response_rank"] for row in rows] != [1, 2, 3]:
        raise ValueError("P16 solver ranks drifted")
    for row in rows:
        for field in OUTPUT_FIELDS:
            if field not in row:
                raise ValueError(f"P16 solver row missing field: {field}")
        _validate_guard_fields(row, row["candidate_id"])
        if row["solver_execution_role"] != "sixth_bounded_phase_curvature_residual_trace_only":
            raise ValueError(f"P16 solver role drifted: {row['candidate_id']}")
    return rows


def write_solver_output_csv(project_root: Path = PROJECT_ROOT) -> Path:
    rows = validate_solver_rows(build_solver_rows(project_root))
    output_path = project_root / P16_SOLVER_OUTPUT_CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(OUTPUT_FIELDS))
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def _read_solver_output_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [
        {
            **row,
            "wavelength_nm": int(row["wavelength_nm"]),
            "width_nm": int(row["width_nm"]),
            "depth_nm": int(row["depth_nm"]),
            "dimensionless_width_over_wavelength": float(row["dimensionless_width_over_wavelength"]),
            "dimensionless_depth_over_wavelength": float(row["dimensionless_depth_over_wavelength"]),
            "p14_fifth_lane_response_rank": int(row["p14_fifth_lane_response_rank"]),
            "solver_native_phase_residual_trace_only": float(row["solver_native_phase_residual_trace_only"]),
            "solver_native_curvature_residual_trace_only": float(row["solver_native_curvature_residual_trace_only"]),
            "solver_native_sixth_lane_response_trace_only": float(row["solver_native_sixth_lane_response_trace_only"]),
            "sixth_lane_response_rank": int(row["sixth_lane_response_rank"]),
            "sixth_lane_response_rank_percentile": float(row["sixth_lane_response_rank_percentile"]),
            "sixth_lane_vs_p14_rank_delta": int(row["sixth_lane_vs_p14_rank_delta"]),
            **{key: row[key] == "True" for key in (*FALSE_FIELDS, *TRUE_FIELDS) if key in row},
        }
        for row in rows
    ]


def build_p15_authorization_binding_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    validate_execution_registry(load_execution_registry(project_root))
    p15_gate = validate_p15_next_authorization_gate_record(
        _load_json_file(project_root / P15_NEXT_AUTHORIZATION_GATE_RECORD)
    )
    validate_p15_p14_closure_binding_manifest(
        _load_json_file(project_root / P15_P14_CLOSURE_BINDING_MANIFEST)
    )
    p4_input = _load_p4_input(project_root)
    return {
        "schema_version": "ev_nodi_p16_sixth_bounded_solver_lane_execution_p15_authorization_binding_manifest_v1",
        "stage": P16_EXECUTION_STAGE,
        "manifest_role": "p15_authorization_binding_for_sixth_bounded_execution",
        "p15_authorization_gate_record_path": P15_NEXT_AUTHORIZATION_GATE_RECORD.as_posix(),
        "p15_authorization_gate_record_sha256": sha256_file(project_root / P15_NEXT_AUTHORIZATION_GATE_RECORD),
        "p15_p14_closure_binding_manifest_path": P15_P14_CLOSURE_BINDING_MANIFEST.as_posix(),
        "p15_p14_closure_binding_manifest_sha256": sha256_file(
            project_root / P15_P14_CLOSURE_BINDING_MANIFEST
        ),
        "p15_gate_prior_decision": p15_gate["authorization_gate_decision"],
        "required_future_authorization_phrase": p15_gate["required_future_authorization_phrase"],
        "user_authorization_phrase_received": P15_REQUIRED_FUTURE_AUTHORIZATION_PHRASE,
        "route_subset_binding_path": P4_INPUT_MANIFEST.as_posix(),
        "route_subset_binding_sha256": sha256_file(project_root / P4_INPUT_MANIFEST),
        "p14_trace_context_path": P14_SOLVER_OUTPUT_CSV.as_posix(),
        "p14_trace_context_sha256": sha256_file(project_root / P14_SOLVER_OUTPUT_CSV),
        "bound_route_count": p4_input["selected_route_count"],
        "bound_route_ids": p4_input["selected_route_ids"],
        **_guard_payload(),
    }


def validate_p15_authorization_binding_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != (
        "ev_nodi_p16_sixth_bounded_solver_lane_execution_p15_authorization_binding_manifest_v1"
    ):
        raise ValueError("unexpected P16 P15 authorization binding manifest schema")
    if manifest["p15_authorization_gate_record_path"] != P15_NEXT_AUTHORIZATION_GATE_RECORD.as_posix():
        raise ValueError("P16 P15 authorization gate path drifted")
    if manifest["p15_p14_closure_binding_manifest_path"] != P15_P14_CLOSURE_BINDING_MANIFEST.as_posix():
        raise ValueError("P16 P15 closure binding path drifted")
    if manifest["required_future_authorization_phrase"] != P15_REQUIRED_FUTURE_AUTHORIZATION_PHRASE:
        raise ValueError("P16 authorization phrase drifted")
    if manifest["user_authorization_phrase_received"] != P15_REQUIRED_FUTURE_AUTHORIZATION_PHRASE:
        raise ValueError("P16 user authorization phrase missing")
    if manifest["p15_gate_prior_decision"] != "not_authorized_pending_explicit_future_request":
        raise ValueError("P16 P15 prior gate decision drifted")
    if manifest["route_subset_binding_path"] != P4_INPUT_MANIFEST.as_posix():
        raise ValueError("P16 route subset binding path drifted")
    if manifest["p14_trace_context_path"] != P14_SOLVER_OUTPUT_CSV.as_posix():
        raise ValueError("P16 P14 trace context path drifted")
    if manifest["bound_route_count"] != 3:
        raise ValueError("P16 bound route count drifted")
    _validate_guard_fields(manifest, "P16 P15 authorization binding manifest")
    return manifest


def build_solver_output_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    rows = validate_solver_rows(_read_solver_output_csv(project_root / P16_SOLVER_OUTPUT_CSV))
    return {
        "schema_version": "ev_nodi_p16_sixth_bounded_solver_lane_execution_output_manifest_v1",
        "stage": P16_EXECUTION_STAGE,
        "manifest_role": "sixth_bounded_solver_lane_output_manifest_trace_only",
        "output_path": P16_SOLVER_OUTPUT_CSV.as_posix(),
        "output_sha256": sha256_file(project_root / P16_SOLVER_OUTPUT_CSV),
        "output_row_count": len(rows),
        "selected_route_ids": [row["candidate_id"] for row in rows],
        "allowed_final_gate_metric_families": ["rank", "rank_percentile", "pairwise_inversion"],
        "raw_solver_native_fields_role": "trace_only_not_final_gate",
        "p14_trace_role": "prior_trace_context_not_calibration_or_promotion",
        **_guard_payload(),
    }


def validate_solver_output_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p16_sixth_bounded_solver_lane_execution_output_manifest_v1":
        raise ValueError("unexpected P16 solver output manifest schema")
    _validate_guard_fields(manifest, "P16 solver output manifest")
    if manifest["output_row_count"] != 3:
        raise ValueError("P16 solver output row count drifted")
    if manifest["output_path"] != P16_SOLVER_OUTPUT_CSV.as_posix():
        raise ValueError("P16 solver output path drifted")
    if set(manifest["allowed_final_gate_metric_families"]) != {"rank", "rank_percentile", "pairwise_inversion"}:
        raise ValueError("P16 solver output final gate families drifted")
    if manifest["raw_solver_native_fields_role"] != "trace_only_not_final_gate":
        raise ValueError("P16 raw solver-native role drifted")
    if manifest["p14_trace_role"] != "prior_trace_context_not_calibration_or_promotion":
        raise ValueError("P16 P14 trace role drifted")
    return manifest


def _artifact_entry(project_root: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    relpath = artifact["path"]
    path = project_root / relpath
    is_self_manifest = relpath == P16_ARTIFACT_MANIFEST.as_posix()
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
        "schema_version": "ev_nodi_p16_sixth_bounded_solver_lane_execution_artifact_manifest_v1",
        "stage": P16_EXECUTION_STAGE,
        "manifest_role": "sixth_bounded_solver_lane_execution_artifact_manifest",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "claim_boundary": dict.fromkeys(CLAIM_BOUNDARY_FALSE_FIELDS, False)
        | {"allowed_claim_level": "sixth_bounded_solver_lane_trace_only"},
        **_guard_payload(),
    }


def validate_artifact_manifest(
    manifest: dict[str, Any],
    project_root: Path = PROJECT_ROOT,
    *,
    allow_missing_self_manifest: bool = False,
) -> dict[str, Any]:
    if manifest.get("schema_version") != "ev_nodi_p16_sixth_bounded_solver_lane_execution_artifact_manifest_v1":
        raise ValueError("unexpected P16 artifact manifest schema")
    _validate_guard_fields(manifest, "P16 artifact manifest")
    _validate_claim_boundary(manifest["claim_boundary"], "P16 artifact manifest")
    for artifact in manifest["artifacts"]:
        _validate_guard_fields(artifact, artifact["artifact_id"])
        is_self_manifest = artifact["path"] == P16_ARTIFACT_MANIFEST.as_posix()
        if (
            not (project_root / artifact["path"]).is_file()
            and not (allow_missing_self_manifest and is_self_manifest)
        ):
            raise ValueError(f"P16 artifact missing: {artifact['path']}")
        if artifact["hash_role"] == "content_sha256" and not artifact["sha256"]:
            raise ValueError(f"P16 artifact hash missing: {artifact['path']}")
    return manifest


def write_p15_authorization_binding_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_p15_authorization_binding_manifest(
        build_p15_authorization_binding_manifest(project_root)
    )
    output_path = project_root / P16_P15_AUTHORIZATION_BINDING_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_solver_output_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_solver_output_manifest(build_solver_output_manifest(project_root))
    output_path = project_root / P16_SOLVER_OUTPUT_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_artifact_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    manifest = validate_artifact_manifest(
        build_artifact_manifest(project_root),
        project_root,
        allow_missing_self_manifest=True,
    )
    output_path = project_root / P16_ARTIFACT_MANIFEST
    write_json_atomic(output_path, manifest, sort_keys=True)
    return output_path


def write_execution_package(project_root: Path = PROJECT_ROOT) -> list[Path]:
    p15_binding = write_p15_authorization_binding_manifest(project_root)
    solver_output = write_solver_output_csv(project_root)
    solver_manifest = write_solver_output_manifest(project_root)
    artifact_manifest = write_artifact_manifest(project_root)
    return [p15_binding, solver_output, solver_manifest, artifact_manifest]


def _assert_manifest_current(path: Path, expected: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {label}: {path}")
    actual = _load_json_file(path)
    if actual != expected:
        raise ValueError(f"stale {label}: regenerate P16 execution package")


def verify_execution_package(project_root: Path = PROJECT_ROOT) -> list[str]:
    validate_execution_registry(load_execution_registry(project_root))
    expected_rows = validate_solver_rows(build_solver_rows(project_root))
    actual_rows = validate_solver_rows(_read_solver_output_csv(project_root / P16_SOLVER_OUTPUT_CSV))
    if actual_rows != expected_rows:
        raise ValueError("stale P16 solver output CSV: regenerate execution package")
    p15_binding = validate_p15_authorization_binding_manifest(
        build_p15_authorization_binding_manifest(project_root)
    )
    _assert_manifest_current(
        project_root / P16_P15_AUTHORIZATION_BINDING_MANIFEST,
        p15_binding,
        "P16 P15 authorization binding manifest",
    )
    output_manifest = validate_solver_output_manifest(build_solver_output_manifest(project_root))
    _assert_manifest_current(project_root / P16_SOLVER_OUTPUT_MANIFEST, output_manifest, "P16 solver output manifest")
    artifact_manifest = validate_artifact_manifest(build_artifact_manifest(project_root), project_root)
    _assert_manifest_current(project_root / P16_ARTIFACT_MANIFEST, artifact_manifest, "P16 artifact manifest")

    lexicon = load_forbidden_claims_lexicon(project_root)
    for relpath in P16_TEXT_PATHS:
        text = (project_root / relpath).read_text(encoding="utf-8")
        if not claim_text_passes(text, lexicon):
            raise ValueError(f"P16 execution claim language drifted: {relpath}")

    return [
        "PASS sixth_bounded_solver_lane_execution_registry",
        "PASS sixth_bounded_solver_lane_execution_p15_authorization_binding_manifest_current",
        "PASS sixth_bounded_solver_lane_execution_output_csv_current",
        "PASS sixth_bounded_solver_lane_execution_output_manifest_current",
        "PASS sixth_bounded_solver_lane_execution_artifact_manifest_current",
        "PASS sixth_bounded_solver_lane_execution_no_mesh_or_operator_export",
        "PASS sixth_bounded_solver_lane_execution_claim_boundaries",
    ]
