#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.cross_section_geometry import (  # noqa: E402
    CENTER_ACCESSIBLE_SUPPORT_MODEL,
    TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION,
    TRAPEZOID_WALL_DISTANCE_MODEL,
    TrapezoidCrossSection,
    comsol_sidewall_deg_to_nodi_taper_deg,
)
from nodi_simulator.nodi_comsol_next_artifacts import (  # noqa: E402
    PRS_APPROVED_DIAMETERS_NM,
    PRS_APPROVED_ROUTE_MATRIX,
    PRS_NEUTRAL_FLOW_CONDITION_ID,
    PRS_POSITION_DISTRIBUTION_BASIS,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260702"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_MULTIWIDTH_RESPONSE_EXPANSION"
ARTIFACT_ID = "NODI_SIDEWALL_MULTIWIDTH_RESPONSE_EXPANSION_20260702"
EXPANSION_VERSION = "sidewall_multiwidth_response_expansion_v1"
DISPOSITION = "NODI_SIDEWALL_MULTIWIDTH_RESPONSE_EXPANSION_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_MULTIWIDTH_RESPONSE_EXPANSION_FAIL_CLOSED"
CLAIM_BOUNDARY = (
    "multiwidth_sidewall_dimension_annulus_response_expansion_not_route_score"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

SIDEWALL_DEG_COMSOL_GRID = (90.0, 89.0, 87.0, 85.0, 83.0, 80.0, 70.0)
FOCUS_RESPONSE_PARTICLE_DIAMETERS_NM = (40, 100, 220, 300)
U_NORM_GRID = (0.15, 0.35, 0.50, 0.65, 0.85)
X_BIN_SPECS = (
    ("near_center_0p0_0p5", 0.25, 0.0, 0.5),
    ("selected_annulus_0p5_0p8", 0.65, 0.5, 0.8),
    ("near_wall_0p8_1p0", 0.90, 0.8, 1.0),
)

SOURCE_FILES = {
    "mainline_refocus_status": OUTPUT_DIR
    / "NODI_SIDEWALL_MAINLINE_REFOCUS_LOCK_STATUS_20260702.json",
    "geometry_effects_status": OUTPUT_DIR
    / "NODI_SIDEWALL_GEOMETRY_EFFECTS_IMPACT_MATRIX_STATUS_20260702.json",
    "geometry_effects_dimension_rows": OUTPUT_DIR
    / "NODI_SIDEWALL_GEOMETRY_EFFECTS_IMPACT_MATRIX_DIMENSION_RECOMMENDATION_DRIFT_ROWS_20260702.csv",
    "cross_section_geometry": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
    "nodi_comsol_next_artifacts": PROJECT_ROOT
    / "nodi_simulator/nodi_comsol_next_artifacts.py",
    "response_expansion_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_multiwidth_response_expansion.py",
    "response_expansion_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_multiwidth_response_expansion.py",
}

ALLOWED_USE = (
    "expand sidewall-angle sensitivity across PRS-approved width/depth/wavelength "
    "routes and produce trapezoid-local response-bin simulation context"
)
BLOCKED_USE = (
    "route winner, route score, fabrication release, production recommendation, "
    "true W_eff, detection probability, wet yield, q_ch weighting, or full optical solver"
)
COMMON_SOURCE_ARTIFACTS_JSON = json.dumps(
    [
        "589_NODI_SIDEWALL_GEOMETRY_EFFECTS_IMPACT_MATRIX_20260702",
        "PRS_APPROVED_ROUTE_MATRIX",
        "PRS_APPROVED_DIAMETERS_NM",
        "cross_section_geometry.py",
        "nodi_comsol_next_artifacts.py",
    ],
    sort_keys=True,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sidewall multiwidth response expansion artifacts."
    )
    parser.add_argument(
        "--confirm-sidewall-multiwidth-response-expansion",
        action="store_true",
    )
    return parser


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={PROJECT_ROOT.as_posix()}", *args],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def git_head() -> str:
    return run_git(["rev-parse", "HEAD"])


def git_branch() -> str:
    return run_git(["branch", "--show-current"])


def git_status_lines() -> list[str]:
    out = run_git(["status", "--short"])
    return [line for line in out.splitlines() if line.strip()]


def git_path_from_status_line(line: str) -> str:
    return line[2:].strip().replace("\\", "/") if len(line) > 2 else line


def display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def load_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def source_lock_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_id": source_id,
                "path": display_path(path) if exists else str(path),
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def dirty_context_rows() -> list[dict[str, str]]:
    output_prefix = f"reports/joint_interface_{DATE_STAMP}/{PREFIX}_"
    output_report = f"reports/590_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_multiwidth_response_expansion.py",
        "tests/test_nodi_sidewall_multiwidth_response_expansion.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "multiwidth_response_expansion_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "multiwidth_response_expansion_output"
            release_decision = "included_or_rewritten_by_response_expansion_builder"
        else:
            classification = "non_multiwidth_response_expansion_dirty_context"
            release_decision = "ignored_for_multiwidth_response_expansion"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def nm_to_m(value_nm: float) -> float:
    return float(value_nm) * 1.0e-9


def m_to_nm(value_m: float) -> float:
    return float(value_m) * 1.0e9


def route_id(lambda_nm: int, width_nm: int, depth_nm: int) -> str:
    return f"{int(lambda_nm)}/W{int(width_nm)}/D{int(depth_nm)}"


def parse_route_id(route: str) -> tuple[int, int, int]:
    lambda_text, width_text, depth_text = str(route).split("/")
    return int(lambda_text), int(width_text.removeprefix("W")), int(
        depth_text.removeprefix("D")
    )


def build_geometry(width_nm: float, depth_nm: float, theta_comsol: float) -> TrapezoidCrossSection:
    return TrapezoidCrossSection(
        top_width_m=nm_to_m(width_nm),
        depth_m=nm_to_m(depth_nm),
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(theta_comsol),
    )


def rectangle_baseline_area_nm2(width_nm: float, depth_nm: float, radius_nm: float) -> float:
    return max(width_nm - 2.0 * radius_nm, 0.0) * max(
        depth_nm - 2.0 * radius_nm,
        0.0,
    )


def aperture_factor(width_nm: float, depth_nm: float, theta: float) -> float:
    geometry = build_geometry(width_nm, depth_nm, theta)
    bottom_nm = max(m_to_nm(geometry.bottom_width_unclipped_m), 0.0)
    return 0.5 * (float(width_nm) + bottom_nm) / max(float(width_nm), 1.0e-30)


def common_fields(row_id: str, matrix_axis: str) -> dict[str, Any]:
    return {
        "expansion_version": EXPANSION_VERSION,
        "row_id": row_id,
        "matrix_axis": matrix_axis,
        "source_artifacts_json": COMMON_SOURCE_ARTIFACTS_JSON,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "not_detection_probability": True,
        "not_winner": True,
        "not_yield": True,
        "not_qch_weighted": True,
        "not_true_W_eff": True,
        "not_optical_solver_output": True,
        "not_route_score": True,
        "not_comsol_transport_distribution": True,
        "not_route_selection_claim": True,
        "not_production_recommendation": True,
        "route_scope": "prs_approved_route_matrix",
        "route_source": "nodi_comsol_next_artifacts.PRS_APPROVED_ROUTE_MATRIX",
        "candidate_universe_context_only": False,
        "sidewall_wall_distance_context_only": True,
        "package_C_validation_status": "not_claiming_trajectory_or_near_wall_runtime",
        "claim_boundary": CLAIM_BOUNDARY,
    }


def dimension_window_class(
    *,
    closure_status: str,
    area_ratio: float,
    particle_diameter_nm: float,
) -> str:
    if closure_status == "geometry_closed":
        return "avoid_depth_angle_pair_candidate"
    if area_ratio <= 0.0:
        return "particle_center_blocked_candidate"
    if particle_diameter_nm >= 220.0 and area_ratio < 0.35:
        return "large_particle_tail_blocked_candidate"
    if area_ratio < 0.65:
        return "increase_top_width_candidate"
    if area_ratio < 0.90:
        return "narrower_dimension_window_candidate"
    return "rectangle_like_dimension_window_candidate"


def dimension_window_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lambda_nm, width_nm, depth_nm in sorted(PRS_APPROVED_ROUTE_MATRIX):
        for theta in SIDEWALL_DEG_COMSOL_GRID:
            geometry = build_geometry(width_nm, depth_nm, theta)
            ap_factor = aperture_factor(width_nm, depth_nm, theta)
            for diameter_nm in sorted(PRS_APPROVED_DIAMETERS_NM):
                radius_nm = float(diameter_nm) / 2.0
                area_nm2 = m_to_nm(1.0) ** 2 * geometry.center_accessible_area_m2(
                    nm_to_m(radius_nm)
                )
                baseline_area_nm2 = rectangle_baseline_area_nm2(
                    width_nm,
                    depth_nm,
                    radius_nm,
                )
                area_ratio = (
                    area_nm2 / baseline_area_nm2 if baseline_area_nm2 > 0.0 else 0.0
                )
                effective_depth_nm = max(float(depth_nm) - 2.0 * radius_nm, 1.0)
                width_compensation_nm = max(
                    0.0,
                    (baseline_area_nm2 - area_nm2) / effective_depth_nm,
                )
                row_id = (
                    f"MWDIM-{route_id(lambda_nm, width_nm, depth_nm).replace('/', '_')}"
                    f"-TH{theta:g}-P{diameter_nm}"
                )
                row = {
                    **common_fields(row_id, "multiwidth_dimension_window"),
                    "dimension_window_case_id": row_id,
                    "route_id_nodi_join_key": route_id(lambda_nm, width_nm, depth_nm),
                    "route_id_nodi_role": "join_key_only_not_selection",
                    "lambda_nm": int(lambda_nm),
                    "W_nominal_nm": int(width_nm),
                    "W_top_nm": int(width_nm),
                    "W_top_semantics": "runtime_top_aperture_surrogate",
                    "D_nm": int(depth_nm),
                    "depth_nm": int(depth_nm),
                    "diameter_nm": int(diameter_nm),
                    "channel_cross_section_model": "ideal_rectangle"
                    if math.isclose(theta, 90.0)
                    else "trapezoid_tapered_sidewalls",
                    "sidewall_angle_convention": "comsol_from_horizontal",
                    "sidewall_deg_comsol": float(theta),
                    "sidewall_taper_angle_deg_nodi": (
                        comsol_sidewall_deg_to_nodi_taper_deg(theta)
                    ),
                    "cross_section_geometry_version": (
                        TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION
                    ),
                    "W_bottom_unclipped_nm": m_to_nm(
                        geometry.bottom_width_unclipped_m
                    ),
                    "W_bottom_runtime_clipped_nm": m_to_nm(
                        geometry.bottom_width_runtime_clipped_m
                    ),
                    "closure_status": geometry.closure_status,
                    "closure_depth_nm": m_to_nm(geometry.closure_depth_m)
                    if math.isfinite(geometry.closure_depth_m)
                    else "inf",
                    "center_accessible_support_model": CENTER_ACCESSIBLE_SUPPORT_MODEL,
                    "center_accessible_area_nm2": area_nm2,
                    "rectangle_baseline_area_nm2": baseline_area_nm2,
                    "center_accessible_area_fraction_vs_rectangle": area_ratio,
                    "top_width_compensation_proxy_nm": width_compensation_nm,
                    "reference_aperture_surrogate_factor": ap_factor,
                    "dimension_window_shift_candidate": dimension_window_class(
                        closure_status=geometry.closure_status,
                        area_ratio=area_ratio,
                        particle_diameter_nm=float(diameter_nm),
                    ),
                    "tail_particle_status": "tail_particle_sensitive"
                    if int(diameter_nm) >= 220 and area_ratio < 0.65
                    else "not_tail_sensitive",
                    "not_production_recommendation": True,
                }
                rows.append(row)
    return rows


def response_bin_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lambda_nm, width_nm, depth_nm in sorted(PRS_APPROVED_ROUTE_MATRIX):
        for theta in SIDEWALL_DEG_COMSOL_GRID:
            geometry = build_geometry(width_nm, depth_nm, theta)
            ap_factor = aperture_factor(width_nm, depth_nm, theta)
            baseline_ap_factor = aperture_factor(width_nm, depth_nm, 90.0)
            for diameter_nm in FOCUS_RESPONSE_PARTICLE_DIAMETERS_NM:
                radius_nm = float(diameter_nm) / 2.0
                for u_norm in U_NORM_GRID:
                    u_nm = float(depth_nm) * float(u_norm)
                    support = geometry.center_accessible_support_at_depth_m(
                        nm_to_m(u_nm),
                        nm_to_m(radius_nm),
                    )
                    local_width_nm = m_to_nm(float(support["center_accessible_width_m"]))
                    local_half_width_nm = local_width_nm / 2.0
                    for bin_id, x_center_norm, edge_min, edge_max in X_BIN_SPECS:
                        bin_accessible = (
                            support["particle_center_support_status"] != "blocked"
                            and local_half_width_nm > 0.0
                        )
                        x_local_norm = min(float(x_center_norm), 0.999)
                        x_nm = x_local_norm * local_half_width_nm if bin_accessible else 0.0
                        wall_diag = geometry.particle_wall_gap_diagnostics_m(
                            nm_to_m(x_nm),
                            nm_to_m(u_nm),
                            nm_to_m(radius_nm),
                        )
                        wall_factor = 1.0 + 0.18 * abs(x_local_norm) + 0.08 * abs(
                            2.0 * float(u_norm) - 1.0
                        )
                        size_factor = (float(diameter_nm) / 100.0) ** 3
                        proxy = size_factor * ap_factor * wall_factor
                        baseline_proxy = size_factor * baseline_ap_factor * wall_factor
                        if not bin_accessible:
                            proxy_value: float | None = None
                            delta_value: float | None = None
                            response_status = "blocked_bin_no_response_value"
                        else:
                            proxy_value = proxy
                            delta_value = proxy - baseline_proxy
                            response_status = "conditional_surrogate_response_value"
                        row_id = (
                            f"MWRESP-{route_id(lambda_nm, width_nm, depth_nm).replace('/', '_')}"
                            f"-TH{theta:g}-P{diameter_nm}-U{u_norm:.2f}-{bin_id}"
                        )
                        row = {
                            **common_fields(row_id, "trapezoid_local_response_bins"),
                            "response_surface_artifact_version": (
                                "NODI_POSITION_RESPONSE_SIDEWALL_V2_CONTEXT_EXPANSION"
                            ),
                            "row_scope": "response_surface_bin",
                            "route_id_nodi": route_id(lambda_nm, width_nm, depth_nm),
                            "route_id_nodi_role": "join_key_only_not_selection",
                            "lambda_nm": int(lambda_nm),
                            "W_nominal_nm": int(width_nm),
                            "W_top_nm": int(width_nm),
                            "W_top_semantics": "runtime_top_aperture_surrogate",
                            "D_nm": int(depth_nm),
                            "depth_nm": int(depth_nm),
                            "NODI_view": "per_wavelength_gold",
                            "diameter_nm": int(diameter_nm),
                            "distribution_type": "xz_norm_2d",
                            "bin_id": bin_id,
                            "selected_annulus_rectangular_v1": (
                                "edge_norm_0p5_to_0p8"
                                if bin_id == "selected_annulus_0p5_0p8"
                                else ""
                            ),
                            "selected_annulus_trapezoid_wall_distance_v1": (
                                "trapezoid_local_width_plus_wall_distance"
                                if bin_id == "selected_annulus_0p5_0p8"
                                else ""
                            ),
                            "edge_norm_min": float(edge_min),
                            "edge_norm_max": float(edge_max),
                            "x_local_norm_min": float(edge_min),
                            "x_local_norm_max": float(edge_max),
                            "x_norm_min": -float(edge_max),
                            "x_norm_max": float(edge_max),
                            "z_norm_min": max(float(u_norm) - 0.10, 0.0),
                            "z_norm_max": min(float(u_norm) + 0.10, 1.0),
                            "channel_cross_section_model": "ideal_rectangle"
                            if math.isclose(theta, 90.0)
                            else "trapezoid_tapered_sidewalls",
                            "sidewall_angle_convention": "comsol_from_horizontal",
                            "sidewall_deg_comsol": float(theta),
                            "sidewall_taper_angle_deg_nodi": (
                                comsol_sidewall_deg_to_nodi_taper_deg(theta)
                            ),
                            "W_bottom_unclipped_nm": m_to_nm(
                                geometry.bottom_width_unclipped_m
                            ),
                            "W_bottom_runtime_clipped_nm": m_to_nm(
                                geometry.bottom_width_runtime_clipped_m
                            ),
                            "closure_status": geometry.closure_status,
                            "closure_depth_nm": m_to_nm(geometry.closure_depth_m)
                            if math.isfinite(geometry.closure_depth_m)
                            else "inf",
                            "cross_section_geometry_version": (
                                TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION
                            ),
                            "geometry_runtime_binding_version": (
                                "sidewall_v2_context_expansion_not_runtime_config"
                            ),
                            "geometry_propagation_status": "propagated"
                            if bin_accessible
                            else "blocked",
                            "sampler_geometry_model": "trapezoid_accessible_area_v1",
                            "sampler_support_model": CENTER_ACCESSIBLE_SUPPORT_MODEL,
                            "particle_radius_nm": radius_nm,
                            "coordinate_basis": "x_centered_u_from_top",
                            "coordinate_conversion_formula_id": (
                                "centered_z_to_u_from_top_v1"
                            ),
                            "x_nm": x_nm,
                            "u_nm": u_nm,
                            "z_nm": u_nm - float(depth_nm) / 2.0,
                            "x_left_nm": m_to_nm(float(support["x_left_m"])),
                            "x_right_nm": m_to_nm(float(support["x_right_m"])),
                            "x_center_nm": 0.0,
                            "local_width_nm": local_width_nm,
                            "local_half_width_nm": local_half_width_nm,
                            "x_local_norm": x_local_norm if bin_accessible else "",
                            "u_norm": float(u_norm),
                            "d_top_nm": m_to_nm(float(wall_diag["d_top_m"])),
                            "d_bottom_nm": m_to_nm(float(wall_diag["d_bottom_m"])),
                            "d_side_left_nm": m_to_nm(float(wall_diag["d_side_left_m"])),
                            "d_side_right_nm": m_to_nm(float(wall_diag["d_side_right_m"])),
                            "d_nearest_wall_nm": m_to_nm(
                                float(wall_diag["d_nearest_wall_m"])
                            ),
                            "nearest_wall_id": str(wall_diag["nearest_wall_id"]),
                            "surface_gap_for_particle_nm": m_to_nm(
                                float(wall_diag["surface_gap_for_particle_m"])
                            ),
                            "bin_basis": "xz_norm_2d_trapezoid_local_width_v1",
                            "bin_accessible": bin_accessible,
                            "bin_accessible_area_fraction": 1.0 if bin_accessible else 0.0,
                            "bin_particle_center_support_status": str(
                                support["particle_center_support_status"]
                            ),
                            "blocked_reason": str(support["steric_block_reason"]),
                            "sparse_reason": "synthetic_grid_no_event_count",
                            "neighbor_fill_used": False,
                            "flow_condition_id": PRS_NEUTRAL_FLOW_CONDITION_ID,
                            "flow_condition_scope": (
                                "fixed_velocity_plug_context_not_transport_distribution"
                            ),
                            "position_distribution_basis": PRS_POSITION_DISTRIBUTION_BASIS,
                            "n_events_bin": 0,
                            "bin_sample_status": "synthetic_grid_no_events",
                            "decision_use_allowed": False,
                            "decision_use_allowed_role": "prs_bin_use_not_route_decision",
                            "decision_use_allowed_prs_bin": False,
                            "response_value_status": response_status,
                            "response_proxy_value": proxy_value,
                            "signal_response_proxy": proxy_value,
                            "response_proxy_delta_vs_rectangle": delta_value,
                            "A_ref_surrogate_baseline": baseline_ap_factor,
                            "A_ref_surrogate_sidewall": ap_factor,
                            "A_ref_surrogate_delta": ap_factor - baseline_ap_factor,
                            "g_ref_surrogate_baseline": baseline_ap_factor,
                            "g_ref_surrogate_sidewall": ap_factor,
                            "g_ref_surrogate_delta": ap_factor - baseline_ap_factor,
                            "phi_ref_rad": 0.0,
                            "phi_ref_source": "surrogate_zero_phase_not_measured",
                            "phi_ref_confidence": "synthetic_context_only",
                            "reference_field_model": (
                                "trapezoid_effective_aperture_surrogate_not_full_solver"
                            ),
                            "reference_spatial_mode": "cross_section_surrogate",
                            "reference_geometry_propagation_status": (
                                "trapezoid_geometry_propagated_to_effective_aperture_reference_surrogate"
                            ),
                            "geometry_not_propagated_to_reference_field": False,
                            "reference_uses_rectangular_width_depth_surrogate": False,
                            "near_wall_response_shift": "near_wall_bin"
                            if bin_id == "near_wall_0p8_1p0"
                            else "not_near_wall_bin",
                            "annulus_response_delta": delta_value
                            if bin_id == "selected_annulus_0p5_0p8"
                            else "",
                            "enhancement_delta_proxy": delta_value,
                            "interference_impact_status": "blocked"
                            if not bin_accessible
                            else (
                                "sidewall_response_shift_candidate"
                                if delta_value is not None and abs(delta_value) > 0.05
                                else "rectangle_like_response_candidate"
                            ),
                        }
                        rows.append(row)
    return rows


def selected_annulus_expansion_rows(response_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in response_rows:
        if row["bin_id"] != "selected_annulus_0p5_0p8":
            continue
        key = (
            row["route_id_nodi"],
            row["sidewall_deg_comsol"] if "sidewall_deg_comsol" in row else "",
            row["diameter_nm"],
        )
        grouped.setdefault(key, []).append(row)

    rows: list[dict[str, Any]] = []
    for (route, theta, diameter_nm), group in sorted(grouped.items(), key=lambda item: str(item[0])):
        lambda_nm, width_nm, depth_nm = parse_route_id(str(route))
        accessible = [row for row in group if row["bin_accessible"]]
        shifts = [
            float(row["annulus_response_delta"])
            for row in accessible
            if row["annulus_response_delta"] not in {"", None}
        ]
        row_id = f"MWANN-{route.replace('/', '_')}-TH{theta}-P{diameter_nm}"
        rows.append(
            {
                **common_fields(row_id, "selected_annulus_expansion"),
                "annulus_expansion_case_id": row_id,
                "route_id_nodi": route,
                "route_id_nodi_role": "join_key_only_not_selection",
                "lambda_nm": lambda_nm,
                "W_nominal_nm": width_nm,
                "W_top_nm": width_nm,
                "W_top_semantics": "runtime_top_aperture_surrogate",
                "D_nm": depth_nm,
                "depth_nm": depth_nm,
                "NODI_view": "per_wavelength_gold",
                "sidewall_deg_comsol": theta,
                "sidewall_angle_convention": "comsol_from_horizontal",
                "sidewall_taper_angle_deg_nodi": (
                    comsol_sidewall_deg_to_nodi_taper_deg(float(theta))
                ),
                "diameter_nm": diameter_nm,
                "selection_basis": "selected_annulus_edge_norm_context",
                "selection_source_system": "NODI_sidewall_multiwidth_expansion",
                "edge_norm_definition": "max_abs_xz_norm_legacy_rectangle",
                "annulus_edge_norm_min": 0.5,
                "annulus_edge_norm_max": 0.8,
                "new_trapezoid_annulus_basis": (
                    "trapezoid_local_width_x_norm_plus_wall_normal_distance"
                ),
                "coordinate_frame_id": "trapezoid_x_u_from_top",
                "coordinate_frame_version": "trapezoid_local_width_v1",
                "u_slice_rows": len(group),
                "accessible_u_slice_rows": len(accessible),
                "blocked_u_slice_rows": len(group) - len(accessible),
                "selected_annulus_accessible_fraction": (
                    len(accessible) / len(group) if group else 0.0
                ),
                "annulus_response_delta_mean": (
                    sum(shifts) / len(shifts) if shifts else ""
                ),
                "annulus_mapping_status": "blocked_or_partial"
                if len(accessible) < len(group)
                else "mapped_all_slices",
                "annulus_impact_status": "annulus_shift_candidate"
                if shifts and abs(sum(shifts) / len(shifts)) > 0.05
                else "annulus_rectangle_like_or_blocked_context",
                "no_neighbor_fill_for_blocked_bins": True,
                "small_n_synthetic_context": False,
            }
        )
    return rows


def axis_synthesis_rows(
    dimension_rows: list[dict[str, Any]],
    response_rows: list[dict[str, Any]],
    annulus_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    dimension_shift_rows = [
        row
        for row in dimension_rows
        if row["dimension_window_shift_candidate"]
        != "rectangle_like_dimension_window_candidate"
    ]
    blocked_response_rows = [
        row for row in response_rows if row["response_value_status"].startswith("blocked")
    ]
    response_shift_rows = [
        row
        for row in response_rows
        if row["interference_impact_status"] == "sidewall_response_shift_candidate"
    ]
    annulus_shift_rows = [
        row for row in annulus_rows if row["annulus_impact_status"] == "annulus_shift_candidate"
    ]
    return [
        {
            "axis_id": "AXIS-001",
            "axis_name": "multiwidth_dimension_window",
            "expansion_status": "dimension_window_shift_present",
            "evidence_rows": len(dimension_rows),
            "changed_rows": len(dimension_shift_rows),
            "key_observation": (
                "PRS-approved route matrix shows sidewall-dependent area loss and "
                "top-width compensation needs"
            ),
            "next_large_block": "feed changed dimension bands into full event-run planning",
        },
        {
            "axis_id": "AXIS-002",
            "axis_name": "selected_annulus_expansion",
            "expansion_status": "selected_annulus_remap_present",
            "evidence_rows": len(annulus_rows),
            "changed_rows": len(annulus_shift_rows),
            "key_observation": (
                f"blocked_or_partial_response_bin_rows={len(blocked_response_rows)}"
            ),
            "next_large_block": (
                "promote trapezoid-local annulus bins into PRS sidewall v2 candidate rows"
            ),
        },
        {
            "axis_id": "AXIS-003",
            "axis_name": "interference_response_expansion",
            "expansion_status": "interference_response_shift_present",
            "evidence_rows": len(response_rows),
            "changed_rows": len(response_shift_rows),
            "key_observation": (
                "response proxy separates particle-size, reference aperture, "
                "near-wall, and selected-annulus terms"
            ),
            "next_large_block": (
                "run bounded NODI event shards on the shifted dimension/annulus grid"
            ),
        },
    ]


def alignment_check_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    dimension_rows = payload["dimension_window_rows"]
    response_rows = payload["trapezoid_local_response_bin_rows"]
    annulus_rows = payload["selected_annulus_expansion_rows"]
    forbidden_exact_columns = {
        "winner",
        "route_score",
        "rank",
        "recommended_candidate",
        "detection_probability",
        "W_eff",
        "yield",
        "q_ch_eta",
    }
    all_columns: set[str] = set()
    for table in (dimension_rows, response_rows, annulus_rows):
        for row in table:
            all_columns.update(row)
    route_set = {
        (
            int(row["lambda_nm"]),
            int(row["W_nominal_nm"]),
            int(row["D_nm"]),
        )
        for row in dimension_rows
    }
    blocked_response_rows = [
        row for row in response_rows if row["response_value_status"].startswith("blocked")
    ]
    checks = [
        (
            "route_matrix_matches_prs_approved_routes",
            route_set == set(PRS_APPROVED_ROUTE_MATRIX),
            str(sorted(route_set)),
        ),
        (
            "diameter_grid_matches_prs_approved_diameters",
            {int(row["diameter_nm"]) for row in dimension_rows}
            == set(PRS_APPROVED_DIAMETERS_NM),
            str(sorted({int(row["diameter_nm"]) for row in dimension_rows})),
        ),
        (
            "all_trapezoid_rows_have_rectangle_baseline_angle",
            all(theta in {row["sidewall_deg_comsol"] for row in dimension_rows} for theta in (90.0, 85.0, 70.0)),
            "theta90/theta85/theta70 present",
        ),
        (
            "blocked_response_bins_have_blank_proxy_values",
            all(row["response_proxy_value"] is None for row in blocked_response_rows),
            str(len(blocked_response_rows)),
        ),
        (
            "selected_annulus_rows_present",
            len(annulus_rows) > 0
            and any(row["annulus_mapping_status"] == "blocked_or_partial" for row in annulus_rows),
            str(len(annulus_rows)),
        ),
        (
            "response_rows_include_prs_sidewall_v2_geometry_fields",
            all(
                "cross_section_geometry_version" in row
                and "x_local_norm" in row
                and "d_nearest_wall_nm" in row
                and "bin_particle_center_support_status" in row
                for row in response_rows
            ),
            str(len(response_rows)),
        ),
        (
            "forbidden_primary_columns_absent",
            forbidden_exact_columns.isdisjoint(all_columns),
            ",".join(sorted(forbidden_exact_columns & all_columns)),
        ),
    ]
    return [
        {
            "check_id": f"MULTIWIDTH-EXPANSION-CHECK-{index:03d}",
            "check_name": name,
            "check_pass": bool(passed),
            "check_detail": detail,
            "hard_fail_if_false": True,
        }
        for index, (name, passed, detail) in enumerate(checks, start=1)
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "dimension_window_rows": payload["dimension_window_rows"],
                "selected_annulus_expansion_rows": payload[
                    "selected_annulus_expansion_rows"
                ],
                "axis_synthesis_rows": payload["axis_synthesis_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    dimension_rows = dimension_window_rows()
    response_rows = response_bin_rows()
    annulus_rows = selected_annulus_expansion_rows(response_rows)
    synthesis_rows = axis_synthesis_rows(dimension_rows, response_rows, annulus_rows)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    payload: dict[str, Any] = {
        "dimension_window_rows": dimension_rows,
        "trapezoid_local_response_bin_rows": response_rows,
        "selected_annulus_expansion_rows": annulus_rows,
        "axis_synthesis_rows": synthesis_rows,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    checks = alignment_check_rows(payload)
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    failed_checks = sum(not row["check_pass"] for row in checks)
    mainline_refocus = load_summary(SOURCE_FILES["mainline_refocus_status"])
    geometry_effects = load_summary(SOURCE_FILES["geometry_effects_status"])
    disposition = DISPOSITION
    if source_missing or failed_checks:
        disposition = BLOCKED_DISPOSITION
    payload["alignment_check_rows"] = checks
    payload["summary"] = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "mainline_refocus_disposition": mainline_refocus.get("disposition", ""),
        "geometry_effects_disposition": geometry_effects.get("disposition", ""),
        "prs_approved_route_count": len(PRS_APPROVED_ROUTE_MATRIX),
        "prs_approved_diameter_count": len(PRS_APPROVED_DIAMETERS_NM),
        "dimension_window_rows": len(dimension_rows),
        "trapezoid_local_response_bin_rows": len(response_rows),
        "selected_annulus_expansion_rows": len(annulus_rows),
        "axis_synthesis_rows": len(synthesis_rows),
        "alignment_check_rows": len(checks),
        "failed_alignment_check_rows": failed_checks,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_multiwidth_response_expansion_dirty_context_rows": sum(
            row["classification"] == "non_multiwidth_response_expansion_dirty_context"
            for row in dirty_context
        ),
        "primary_answer_frame": (
            "multiwidth_dimension_window_annulus_and_interference_response_expansion"
        ),
        "not_primary_answer_frame": "route_selection_or_scalar_scoreboard",
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "next_large_block": (
            "run bounded NODI event shards over changed dimension/annulus bins"
        ),
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    if summary["disposition"] != DISPOSITION:
        failures.append("multiwidth_response_expansion_not_ready")
    if summary["dimension_window_rows"] == 0:
        failures.append("dimension_window_rows_missing")
    if summary["trapezoid_local_response_bin_rows"] == 0:
        failures.append("response_bin_rows_missing")
    if summary["selected_annulus_expansion_rows"] == 0:
        failures.append("annulus_expansion_rows_missing")
    if summary["failed_alignment_check_rows"] != 0:
        failures.append("failed_alignment_checks_present")
    if summary["source_missing_rows"] != 0:
        failures.append("source_missing")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json",
        "dimension_windows": OUTPUT_DIR / f"{PREFIX}_DIMENSION_WINDOW_ROWS_{DATE_STAMP}.csv",
        "response_bins": OUTPUT_DIR
        / f"{PREFIX}_TRAPEZOID_LOCAL_RESPONSE_BIN_ROWS_{DATE_STAMP}.csv",
        "selected_annulus": OUTPUT_DIR
        / f"{PREFIX}_SELECTED_ANNULUS_EXPANSION_ROWS_{DATE_STAMP}.csv",
        "axis_synthesis": OUTPUT_DIR / f"{PREFIX}_AXIS_SYNTHESIS_ROWS_{DATE_STAMP}.csv",
        "alignment_checks": OUTPUT_DIR / f"{PREFIX}_ALIGNMENT_CHECK_ROWS_{DATE_STAMP}.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "master_report": REPORT_DIR / f"590_{PREFIX}_{DATE_STAMP}.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv",
    }
    write_json_atomic(
        outputs["status"],
        {
            "disposition": payload["summary"]["disposition"],
            "summary": payload["summary"],
        },
        sort_keys=True,
    )
    write_csv_rows(outputs["dimension_windows"], payload["dimension_window_rows"])
    write_csv_rows(outputs["response_bins"], payload["trapezoid_local_response_bin_rows"])
    write_csv_rows(outputs["selected_annulus"], payload["selected_annulus_expansion_rows"])
    write_csv_rows(outputs["axis_synthesis"], payload["axis_synthesis_rows"])
    write_csv_rows(outputs["alignment_checks"], payload["alignment_check_rows"])
    write_csv_rows(outputs["source_lock"], payload["source_lock_rows"])
    write_csv_rows(outputs["dirty_context"], payload["dirty_context_rows"])
    write_json_atomic(outputs["report_json"], payload, indent=None, sort_keys=True)
    outputs["master_report"].write_text(render_markdown(payload), encoding="utf-8")
    write_csv_rows(outputs["manifest"], manifest_rows(outputs))
    return list(outputs.values())


def manifest_rows(outputs: dict[str, Path]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_id": artifact_id,
            "path": display_path(path),
            "sha256": SELF_MANIFEST_SHA256
            if artifact_id == "manifest"
            else sha256_file(path),
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for artifact_id, path in outputs.items()
    ]


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    lines = [
        "# NODI Sidewall Multiwidth Response Expansion",
        "",
        f"Disposition: `{s['disposition']}`",
        f"Artifact ID: `{s['artifact_id']}`",
        f"Claim boundary: `{s['claim_boundary']}`",
        "",
        "This package expands the sidewall-angle matrix onto the PRS-approved "
        "width/depth/wavelength route matrix and emits trapezoid-local response "
        "bins for selected-annulus and near-wall sensitivity.",
        "",
        f"PRS-approved routes: `{s['prs_approved_route_count']}`.",
        f"PRS-approved diameters: `{s['prs_approved_diameter_count']}`.",
        f"Dimension window rows: `{s['dimension_window_rows']}`.",
        f"Trapezoid-local response bin rows: `{s['trapezoid_local_response_bin_rows']}`.",
        f"Selected-annulus expansion rows: `{s['selected_annulus_expansion_rows']}`.",
        f"Alignment check failures: `{s['failed_alignment_check_rows']}`.",
        "",
        "## Axis Synthesis",
        "",
    ]
    for row in payload["axis_synthesis_rows"]:
        lines.extend(
            [
                f"- `{row['axis_name']}`: `{row['expansion_status']}`",
                f"  Evidence rows: `{row['evidence_rows']}`",
                f"  Changed rows: `{row['changed_rows']}`",
                f"  Key observation: `{row['key_observation']}`",
                f"  Next block: {row['next_large_block']}",
            ]
        )
    lines.extend(
        [
            "",
            "The expansion keeps route ids as join keys only. It does not emit a "
            "route score, winner, production recommendation, true W_eff, detection "
            "probability, wet yield, q_ch weighting, or full optical solver claim.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_multiwidth_response_expansion:
        raise SystemExit(
            "--confirm-sidewall-multiwidth-response-expansion is required"
        )
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
