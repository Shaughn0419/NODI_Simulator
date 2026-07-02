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
from nodi_simulator.realism_v2_io import (  # noqa: E402
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260702"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_GEOMETRY_EFFECTS_IMPACT_MATRIX"
ARTIFACT_ID = "NODI_SIDEWALL_GEOMETRY_EFFECTS_IMPACT_MATRIX_20260702"
IMPACT_MATRIX_VERSION = "sidewall_geometry_effects_impact_matrix_v1"
DISPOSITION = "NODI_SIDEWALL_GEOMETRY_EFFECTS_IMPACT_MATRIX_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_GEOMETRY_EFFECTS_IMPACT_MATRIX_FAIL_CLOSED"
CLAIM_BOUNDARY = (
    "sidewall_angle_effect_matrix_for_dimensions_annulus_and_interference_only"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

WIDTH_NM_GRID = (500,)
DEPTH_NM_GRID = (900, 1200)
SIDEWALL_DEG_COMSOL_GRID = (90.0, 89.0, 87.0, 85.0, 83.0, 80.0, 70.0)
PARTICLE_DIAMETER_NM_GRID = (40.0, 60.0, 100.0, 150.0, 220.0, 300.0)
U_NORM_GRID = (0.15, 0.35, 0.50, 0.65, 0.85)
ANNULUS_EDGE_MIN = 0.50
ANNULUS_EDGE_MAX = 0.80
WAVELENGTH_NM_GRID = (404, 660)

SOURCE_FILES = {
    "mainline_refocus_status": OUTPUT_DIR
    / "NODI_SIDEWALL_MAINLINE_REFOCUS_LOCK_STATUS_20260702.json",
    "comsol_v4_upper_alignment_status": OUTPUT_DIR
    / "NODI_COMSOL_V4_UPPER_ASSUMPTION_ALIGNMENT_STATUS_20260702.json",
    "comsol_v4_alignment_extension_status": OUTPUT_DIR
    / "NODI_COMSOL_V4_ALIGNMENT_EXTENSION_STATUS_20260702.json",
    "cross_section_geometry": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
    "selected_annulus_context": PROJECT_ROOT
    / "nodi_simulator/sidewall_selected_annulus_context.py",
    "reference_surrogate_candidate": PROJECT_ROOT
    / "nodi_simulator/sidewall_reference_surrogate_candidate.py",
    "optical_reference_smoke": PROJECT_ROOT
    / "nodi_simulator/sidewall_optical_reference_smoke.py",
    "reference_field": PROJECT_ROOT / "nodi_simulator/reference_field.py",
    "impact_matrix_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_geometry_effects_impact_matrix.py",
    "impact_matrix_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_geometry_effects_impact_matrix.py",
}

ALLOWED_USE = (
    "evaluate how sidewall angle changes NODI dimension windows, selected-annulus "
    "coordinates, and interference-response surrogates before larger simulations"
)
BLOCKED_USE = (
    "route selection, scalar scoreboard, production recommendation, wet claim, "
    "full optical solver claim, q_ch weighting, or final detection/yield conclusion"
)
COMMON_SOURCE_ARTIFACTS_JSON = json.dumps(
    [
        "588_NODI_SIDEWALL_MAINLINE_REFOCUS_LOCK_20260702",
        "cross_section_geometry.py",
        "sidewall_selected_annulus_context.py",
        "sidewall_reference_surrogate_candidate.py",
        "reference_field.py",
    ],
    sort_keys=True,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sidewall geometry-effects impact matrix artifacts."
    )
    parser.add_argument(
        "--confirm-sidewall-geometry-effects-impact-matrix",
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
    output_report = f"reports/589_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_geometry_effects_impact_matrix.py",
        "tests/test_nodi_sidewall_geometry_effects_impact_matrix.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "geometry_effects_impact_matrix_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "geometry_effects_impact_matrix_output"
            release_decision = "included_or_rewritten_by_impact_matrix_builder"
        else:
            classification = "non_geometry_effects_dirty_context"
            release_decision = "ignored_for_geometry_effects_impact_matrix"
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


def build_geometry(width_nm: float, depth_nm: float, theta_comsol: float) -> TrapezoidCrossSection:
    return TrapezoidCrossSection(
        top_width_m=nm_to_m(width_nm),
        depth_m=nm_to_m(depth_nm),
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(theta_comsol),
    )


def attach_common_fields(
    rows: list[dict[str, Any]],
    *,
    matrix_axis: str,
    id_key: str,
) -> list[dict[str, Any]]:
    for row in rows:
        row.setdefault("impact_matrix_version", IMPACT_MATRIX_VERSION)
        row.setdefault("row_id", str(row[id_key]))
        row.setdefault("matrix_axis", matrix_axis)
        row.setdefault("geometry_case_id", str(row[id_key]))
        row.setdefault("source_artifacts_json", COMMON_SOURCE_ARTIFACTS_JSON)
        row.setdefault("allowed_use", ALLOWED_USE)
        row.setdefault("blocked_use", BLOCKED_USE)
        row.setdefault("not_detection_probability", True)
        row.setdefault("not_winner", True)
        row.setdefault("not_yield", True)
        row.setdefault("not_qch_weighted", True)
        row.setdefault("not_true_W_eff", True)
        row.setdefault("not_optical_solver_output", True)
    return rows


def rectangle_baseline_area_nm2(width_nm: float, depth_nm: float, radius_nm: float) -> float:
    accessible_width_nm = max(float(width_nm) - 2.0 * float(radius_nm), 0.0)
    accessible_depth_nm = max(float(depth_nm) - 2.0 * float(radius_nm), 0.0)
    return accessible_width_nm * accessible_depth_nm


def drift_class(
    *,
    closure_status: str,
    area_ratio: float,
    particle_diameter_nm: float,
) -> str:
    if closure_status == "geometry_closed":
        return "geometry_closed_candidate"
    if area_ratio <= 0.0:
        return "particle_tail_blocked_candidate"
    if float(particle_diameter_nm) >= 220.0 and area_ratio < 0.25:
        return "particle_tail_blocked_candidate"
    if area_ratio < 0.55:
        return "width_band_shift_candidate"
    if area_ratio < 0.85:
        return "narrowed_window_candidate"
    return "unchanged_candidate"


def dimension_recommendation_drift_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for width_nm in WIDTH_NM_GRID:
        for depth_nm in DEPTH_NM_GRID:
            for theta in SIDEWALL_DEG_COMSOL_GRID:
                geometry = build_geometry(width_nm, depth_nm, theta)
                baseline_by_particle = {
                    particle_nm: rectangle_baseline_area_nm2(
                        width_nm, depth_nm, particle_nm / 2.0
                    )
                    for particle_nm in PARTICLE_DIAMETER_NM_GRID
                }
                for particle_nm in PARTICLE_DIAMETER_NM_GRID:
                    radius_nm = float(particle_nm) / 2.0
                    area_nm2 = m_to_nm(1.0) ** 2 * geometry.center_accessible_area_m2(
                        nm_to_m(radius_nm)
                    )
                    baseline_area_nm2 = baseline_by_particle[particle_nm]
                    area_ratio = (
                        area_nm2 / baseline_area_nm2
                        if baseline_area_nm2 > 0.0
                        else 0.0
                    )
                    support_status = "open" if area_nm2 > 0.0 else "blocked"
                    rows.append(
                        {
                            "dimension_case_id": (
                                f"DIM-W{int(width_nm)}-D{int(depth_nm)}-"
                                f"TH{theta:g}-P{particle_nm:g}"
                            ),
                            "paired_baseline_case_id": (
                                f"DIM-W{int(width_nm)}-D{int(depth_nm)}-TH90-P{particle_nm:g}"
                            ),
                            "baseline_pair_required": True,
                            "baseline_pair_status": "self_baseline"
                            if math.isclose(theta, 90.0)
                            else "paired_rectangle_baseline_present",
                            "channel_cross_section_model": "ideal_rectangle"
                            if math.isclose(theta, 90.0)
                            else "trapezoid_tapered_sidewalls",
                            "W_top_nm": float(width_nm),
                            "depth_nm": float(depth_nm),
                            "sidewall_angle_convention": "comsol_from_horizontal",
                            "sidewall_deg_comsol": float(theta),
                            "sidewall_taper_angle_deg_nodi": (
                                comsol_sidewall_deg_to_nodi_taper_deg(theta)
                            ),
                            "k_taper": geometry.k_taper,
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
                            "particle_diameter_nm": float(particle_nm),
                            "particle_radius_nm": radius_nm,
                            "center_accessible_support_model": (
                                CENTER_ACCESSIBLE_SUPPORT_MODEL
                            ),
                            "center_accessible_area_nm2": area_nm2,
                            "rectangle_baseline_area_nm2": baseline_area_nm2,
                            "center_accessible_area_fraction_vs_rectangle": area_ratio,
                            "center_accessible_area_delta_vs_rectangle": area_ratio - 1.0,
                            "particle_center_support_status": support_status,
                            "tail_particle_support_delta": "tail_particle_sensitive"
                            if float(particle_nm) >= 220.0
                            and (support_status == "blocked" or area_ratio < 0.55)
                            else "not_tail_sensitive",
                            "dimension_recommendation_drift_class": drift_class(
                                closure_status=geometry.closure_status,
                                area_ratio=area_ratio,
                                particle_diameter_nm=particle_nm,
                            ),
                            "dimension_band_shift_context": (
                                "sidewall_reduces_center_accessible_area"
                                if area_ratio < 0.98
                                else "rectangle_limit_or_negligible_area_delta"
                            ),
                            "baseline_scope_not_extrapolated": True,
                            "qch_transport_input_only": True,
                            "qch_eta_current": False,
                            "yield_current": False,
                            "not_route_selection_claim": True,
                            "not_production_recommendation": True,
                            "claim_boundary": CLAIM_BOUNDARY,
                        }
                    )
    return attach_common_fields(
        rows,
        matrix_axis="dimension_recommendation_sensitivity",
        id_key="dimension_case_id",
    )


def annulus_remap_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rectangle_half_center_width_nm = (WIDTH_NM_GRID[0] - 2.0 * 50.0) / 2.0
    for depth_nm in DEPTH_NM_GRID:
        for theta in SIDEWALL_DEG_COMSOL_GRID:
            geometry = build_geometry(WIDTH_NM_GRID[0], depth_nm, theta)
            for particle_nm in (100.0, 220.0, 300.0):
                radius_nm = particle_nm / 2.0
                for u_norm in U_NORM_GRID:
                    u_nm = float(depth_nm) * u_norm
                    support = geometry.center_accessible_support_at_depth_m(
                        nm_to_m(u_nm),
                        nm_to_m(radius_nm),
                    )
                    width_nm = m_to_nm(float(support["center_accessible_width_m"]))
                    local_half_nm = width_nm / 2.0
                    bin_accessible = support["particle_center_support_status"] != "blocked"
                    mapping_delta = (
                        (local_half_nm - rectangle_half_center_width_nm)
                        / rectangle_half_center_width_nm
                        if rectangle_half_center_width_nm > 0.0
                        else 0.0
                    )
                    sample_x_nm = local_half_nm * ANNULUS_EDGE_MIN if bin_accessible else 0.0
                    wall_diag = geometry.particle_wall_gap_diagnostics_m(
                        nm_to_m(sample_x_nm),
                        nm_to_m(u_nm),
                        nm_to_m(radius_nm),
                    )
                    rows.append(
                        {
                            "annulus_case_id": (
                                f"ANN-D{int(depth_nm)}-TH{theta:g}-"
                                f"P{particle_nm:g}-U{u_norm:.2f}"
                            ),
                            "paired_baseline_case_id": (
                                f"ANN-D{int(depth_nm)}-TH90-P{particle_nm:g}-U{u_norm:.2f}"
                            ),
                            "baseline_pair_required": True,
                            "baseline_pair_status": "self_baseline"
                            if math.isclose(theta, 90.0)
                            else "paired_rectangle_baseline_present",
                            "old_rectangle_basis": "rectangular_edge_norm_0p50_to_0p80",
                            "new_trapezoid_annulus_basis": (
                                "trapezoid_local_width_x_norm_plus_wall_normal_distance"
                            ),
                            "selected_annulus_basis": (
                                "rectangular_edge_norm_to_trapezoid_local_wall_distance_remap"
                            ),
                            "selection_basis": "selected_annulus_edge_norm_context",
                            "selection_source_system": "NODI_synthetic_context",
                            "edge_norm_definition": "max_abs_xz_norm_legacy_rectangle",
                            "annulus_edge_norm_min": ANNULUS_EDGE_MIN,
                            "annulus_edge_norm_max": ANNULUS_EDGE_MAX,
                            "bin_schema": "u_norm_by_x_local_norm_trapezoid_remap_v1",
                            "coordinate_frame_id": "trapezoid_x_u_from_top",
                            "coordinate_frame_version": "trapezoid_local_width_v1",
                            "channel_cross_section_model": "ideal_rectangle"
                            if math.isclose(theta, 90.0)
                            else "trapezoid_tapered_sidewalls",
                            "W_top_nm": float(WIDTH_NM_GRID[0]),
                            "depth_nm": float(depth_nm),
                            "sidewall_deg_comsol": float(theta),
                            "sidewall_taper_angle_deg_nodi": (
                                comsol_sidewall_deg_to_nodi_taper_deg(theta)
                            ),
                            "particle_diameter_nm": float(particle_nm),
                            "particle_radius_nm": radius_nm,
                            "u_norm": float(u_norm),
                            "u_nm": u_nm,
                            "x_local_norm_min": ANNULUS_EDGE_MIN,
                            "x_local_norm_max": ANNULUS_EDGE_MAX,
                            "local_center_accessible_width_nm": width_nm,
                            "local_half_width_nm": local_half_nm,
                            "wall_distance_model": TRAPEZOID_WALL_DISTANCE_MODEL,
                            "d_nearest_wall_nm": m_to_nm(
                                float(wall_diag["d_nearest_wall_m"])
                            ),
                            "surface_gap_for_particle_nm": m_to_nm(
                                float(wall_diag["surface_gap_for_particle_m"])
                            ),
                            "nearest_wall_id": str(wall_diag["nearest_wall_id"]),
                            "bin_accessible": bin_accessible,
                            "bin_particle_center_support_status": str(
                                support["particle_center_support_status"]
                            ),
                            "blocked_reason": str(support["steric_block_reason"]),
                            "annulus_mapping_delta_vs_rectangle": mapping_delta,
                            "annulus_range_shift": "blocked_at_this_slice"
                            if not bin_accessible
                            else (
                                "local_annulus_narrowed"
                                if mapping_delta < -0.05
                                else "local_annulus_rectangle_like"
                            ),
                            "mapping_status": "blocked_bin_no_neighbor_fill"
                            if not bin_accessible
                            else "mapped_to_trapezoid_local_width",
                            "selection_status": "context_remap_only_not_recommendation",
                            "blocked_bins": 0 if bin_accessible else 1,
                            "annulus_impact_status": "annulus_slice_blocked"
                            if not bin_accessible
                            else (
                                "annulus_range_shift_candidate"
                                if mapping_delta < -0.05
                                else "annulus_rectangle_like_candidate"
                            ),
                            "no_neighbor_fill_for_blocked_bins": True,
                            "small_n_context_not_recommendation": True,
                            "not_route_selection_claim": True,
                            "claim_boundary": CLAIM_BOUNDARY,
                        }
                    )
    return attach_common_fields(
        rows,
        matrix_axis="selected_annulus_sidewall_remap",
        id_key="annulus_case_id",
    )


def aperture_factor(width_nm: float, depth_nm: float, theta: float) -> float:
    geometry = build_geometry(width_nm, depth_nm, theta)
    bottom = max(m_to_nm(geometry.bottom_width_unclipped_m), 0.0)
    return 0.5 * (float(width_nm) + bottom) / max(float(width_nm), 1.0e-30)


def annulus_accessible_fraction(rows: list[dict[str, Any]], *, theta: float, depth_nm: float, particle_nm: float) -> float:
    selected = [
        row
        for row in rows
        if math.isclose(float(row["sidewall_deg_comsol"]), theta)
        and math.isclose(float(row["depth_nm"]), depth_nm)
        and math.isclose(float(row["particle_diameter_nm"]), particle_nm)
    ]
    if not selected:
        return 0.0
    return sum(1 for row in selected if row["bin_accessible"]) / len(selected)


def interference_response_sensitivity_rows(
    dimension_rows: list[dict[str, Any]],
    annulus_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    dim_lookup = {
        (
            float(row["depth_nm"]),
            float(row["sidewall_deg_comsol"]),
            float(row["particle_diameter_nm"]),
        ): row
        for row in dimension_rows
        if float(row["W_top_nm"]) == float(WIDTH_NM_GRID[0])
    }
    for depth_nm in DEPTH_NM_GRID:
        for theta in SIDEWALL_DEG_COMSOL_GRID:
            for particle_nm in (100.0, 220.0, 300.0):
                dim_row = dim_lookup[(float(depth_nm), float(theta), particle_nm)]
                area_fraction = float(
                    dim_row["center_accessible_area_fraction_vs_rectangle"]
                )
                ap_factor = aperture_factor(WIDTH_NM_GRID[0], depth_nm, theta)
                baseline_annulus_fraction = annulus_accessible_fraction(
                    annulus_rows,
                    theta=90.0,
                    depth_nm=float(depth_nm),
                    particle_nm=particle_nm,
                )
                current_annulus_fraction = annulus_accessible_fraction(
                    annulus_rows,
                    theta=float(theta),
                    depth_nm=float(depth_nm),
                    particle_nm=particle_nm,
                )
                annulus_delta = current_annulus_fraction - baseline_annulus_fraction
                for wavelength_nm in WAVELENGTH_NM_GRID:
                    ref_delta = ap_factor - 1.0
                    a_ref_baseline = 1.0
                    a_ref_sidewall = ap_factor
                    g_ref_baseline = 1.0
                    g_ref_sidewall = ap_factor
                    response_delta = (
                        0.45 * (area_fraction - 1.0)
                        + 0.45 * ref_delta
                        + 0.10 * annulus_delta
                    )
                    if math.isclose(theta, 90.0):
                        solver_flags = "rectangle_limit_no_sidewall_solver_delta"
                    elif abs(ref_delta) > 0.05 or abs(annulus_delta) > 0.20:
                        solver_flags = "sidewall_reference_response_solver_needed_for_quantitative_claim"
                    else:
                        solver_flags = "sidewall_surrogate_delta_below_solver_trigger_band"
                    rows.append(
                        {
                            "response_case_id": (
                                f"RESP-D{int(depth_nm)}-TH{theta:g}-"
                                f"P{particle_nm:g}-WL{wavelength_nm}"
                            ),
                            "paired_baseline_case_id": (
                                f"RESP-D{int(depth_nm)}-TH90-P{particle_nm:g}-WL{wavelength_nm}"
                            ),
                            "baseline_pair_required": True,
                            "baseline_pair_status": "self_baseline"
                            if math.isclose(theta, 90.0)
                            else "paired_rectangle_baseline_present",
                            "response_map_basis": (
                                "position_distribution_reference_aperture_annulus_surrogate_v1"
                            ),
                            "reference_field_model": (
                                "trapezoid_effective_aperture_surrogate_not_full_solver"
                            ),
                            "detector_operator_id": (
                                "tsuyama_counting_context_operator_not_probability"
                            ),
                            "particle_position_distribution": (
                                "center_accessible_area_uniform_surrogate"
                            ),
                            "W_top_nm": float(WIDTH_NM_GRID[0]),
                            "depth_nm": float(depth_nm),
                            "sidewall_deg_comsol": float(theta),
                            "sidewall_taper_angle_deg_nodi": (
                                comsol_sidewall_deg_to_nodi_taper_deg(theta)
                            ),
                            "particle_diameter_nm": float(particle_nm),
                            "wavelength_nm": int(wavelength_nm),
                            "position_distribution_effect_delta": area_fraction - 1.0,
                            "reference_aperture_surrogate_factor": ap_factor,
                            "reference_field_effect_delta": ref_delta,
                            "detector_overlap_annulus_effect_delta": annulus_delta,
                            "interference_response_surrogate_delta": response_delta,
                            "response_value_status": (
                                "surrogate_delta_only_not_detector_validation"
                            ),
                            "A_ref_surrogate_baseline": a_ref_baseline,
                            "A_ref_surrogate_sidewall": a_ref_sidewall,
                            "A_ref_surrogate_delta": a_ref_sidewall - a_ref_baseline,
                            "A_ref_surrogate_ratio": a_ref_sidewall
                            / max(a_ref_baseline, 1.0e-30),
                            "g_ref_surrogate_baseline": g_ref_baseline,
                            "g_ref_surrogate_sidewall": g_ref_sidewall,
                            "g_ref_surrogate_delta": g_ref_sidewall - g_ref_baseline,
                            "g_ref_surrogate_ratio": g_ref_sidewall
                            / max(g_ref_baseline, 1.0e-30),
                            "phi_ref_rad": 0.0,
                            "phi_ref_source": "surrogate_zero_phase_not_measured",
                            "phi_ref_confidence": "synthetic_context_only",
                            "enhancement_delta_proxy": response_delta,
                            "enhancement_delta_relative": response_delta,
                            "enhancement_delta_map_status": (
                                "candidate_response_changed"
                                if abs(response_delta) > 0.05
                                else "candidate_response_rectangle_like"
                            ),
                            "near_wall_response_shift": (
                                "sidewall_annulus_or_reference_delta_present"
                                if abs(annulus_delta) > 0.0 or abs(ref_delta) > 0.0
                                else "rectangle_limit"
                            ),
                            "annulus_response_delta": annulus_delta,
                            "reference_field_solver_needed_flags": solver_flags,
                            "reference_field_solver_needed_reason": solver_flags,
                            "interference_impact_status": (
                                "interference_proxy_shift_candidate"
                                if abs(response_delta) > 0.05
                                else "interference_proxy_rectangle_like_candidate"
                            ),
                            "true_W_eff_not_claimed": True,
                            "optical_solver_output_current": False,
                            "not_detection_probability_current": True,
                            "not_route_selection_claim": True,
                            "not_production_recommendation": True,
                            "claim_boundary": CLAIM_BOUNDARY,
                        }
                    )
    return attach_common_fields(
        rows,
        matrix_axis="interference_enhancement_sidewall_sensitivity",
        id_key="response_case_id",
    )


def axis_synthesis_rows(
    dimension_rows: list[dict[str, Any]],
    annulus_rows: list[dict[str, Any]],
    response_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    drift_classes = {str(row["dimension_recommendation_drift_class"]) for row in dimension_rows}
    blocked_annulus = sum(not row["bin_accessible"] for row in annulus_rows)
    response_changed = sum(
        row["enhancement_delta_map_status"] == "candidate_response_changed"
        for row in response_rows
    )
    return [
        {
            "axis_id": "AXIS-001",
            "axis_name": "dimension_recommendation_sensitivity",
            "impact_matrix_status": "sidewall_changes_dimension_window_candidate"
            if drift_classes - {"unchanged_candidate"}
            else "rectangle_like_candidate",
            "evidence_rows": len(dimension_rows),
            "key_observation": ";".join(sorted(drift_classes)),
            "next_large_block": (
                "expand width/depth grid and promote candidate drift bands into "
                "dimension-window simulation inputs"
            ),
            "not_route_selection_claim": True,
        },
        {
            "axis_id": "AXIS-002",
            "axis_name": "selected_annulus_sidewall_remap",
            "impact_matrix_status": "annulus_remap_required"
            if blocked_annulus > 0
            else "annulus_rectangle_like_candidate",
            "evidence_rows": len(annulus_rows),
            "key_observation": f"blocked_or_invalid_slice_rows={blocked_annulus}",
            "next_large_block": (
                "replace rectangular edge-norm annulus with trapezoid local-width "
                "and wall-normal distance bins in PRS-style response maps"
            ),
            "not_route_selection_claim": True,
        },
        {
            "axis_id": "AXIS-003",
            "axis_name": "interference_enhancement_sidewall_sensitivity",
            "impact_matrix_status": "interference_response_surrogate_changes_candidate"
            if response_changed > 0
            else "interference_response_surrogate_rectangle_like_candidate",
            "evidence_rows": len(response_rows),
            "key_observation": f"changed_response_rows={response_changed}",
            "next_large_block": (
                "run response-map expansion over the accepted geometry grid and "
                "separate position, reference, and detector-overlap effects"
            ),
            "not_route_selection_claim": True,
        },
    ]


def paired_baseline_check(rows: list[dict[str, Any]], id_key: str) -> bool:
    ids = {str(row[id_key]) for row in rows}
    for row in rows:
        baseline_id = str(row.get("paired_baseline_case_id", ""))
        if baseline_id and baseline_id not in ids:
            return False
    return True


def alignment_check_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    dimension_rows = payload["dimension_recommendation_drift_rows"]
    annulus_rows = payload["selected_annulus_remap_rows"]
    response_rows = payload["interference_response_sensitivity_rows"]
    forbidden_exact_columns = {
        "winner",
        "route_score",
        "rank",
        "recommended_candidate",
        "detection_probability",
        "W_eff",
    }
    all_columns = set()
    for rows in (dimension_rows, annulus_rows, response_rows):
        for row in rows:
            all_columns.update(row)
    checks = [
        (
            "dimension_rows_have_paired_rectangle_baselines",
            paired_baseline_check(dimension_rows, "dimension_case_id"),
            str(len(dimension_rows)),
        ),
        (
            "annulus_rows_have_paired_rectangle_baselines",
            paired_baseline_check(annulus_rows, "annulus_case_id"),
            str(len(annulus_rows)),
        ),
        (
            "response_rows_have_paired_rectangle_baselines",
            paired_baseline_check(response_rows, "response_case_id"),
            str(len(response_rows)),
        ),
        (
            "dimension_matrix_covers_tail_particles_and_depths",
            {220.0, 300.0}.issubset(
                {float(row["particle_diameter_nm"]) for row in dimension_rows}
            )
            and {900.0, 1200.0}.issubset(
                {float(row["depth_nm"]) for row in dimension_rows}
            ),
            "tail particles and D900/D1200 present",
        ),
        (
            "bottom_width_preserves_unclipped_negative_values",
            any(float(row["W_bottom_unclipped_nm"]) < 0.0 for row in dimension_rows),
            "negative bottom width retained in descriptor space",
        ),
        (
            "annulus_remap_has_wall_distance_basis",
            all(
                row["new_trapezoid_annulus_basis"]
                == "trapezoid_local_width_x_norm_plus_wall_normal_distance"
                for row in annulus_rows
            ),
            "trapezoid local width plus wall distance",
        ),
        (
            "interference_rows_split_position_reference_detector_terms",
            all(
                "position_distribution_effect_delta" in row
                and "reference_field_effect_delta" in row
                and "detector_overlap_annulus_effect_delta" in row
                for row in response_rows
            ),
            "response decomposition present",
        ),
        (
            "forbidden_primary_columns_absent",
            forbidden_exact_columns.isdisjoint(all_columns),
            ",".join(sorted(forbidden_exact_columns & all_columns)),
        ),
        (
            "not_route_selection_claim_guards_present",
            all(row.get("not_route_selection_claim") is True for row in response_rows),
            "response rows guarded",
        ),
    ]
    return [
        {
            "check_id": f"GEOMETRY-EFFECTS-CHECK-{index:03d}",
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
                "dimension_recommendation_drift_rows": payload[
                    "dimension_recommendation_drift_rows"
                ],
                "selected_annulus_remap_rows": payload["selected_annulus_remap_rows"],
                "interference_response_sensitivity_rows": payload[
                    "interference_response_sensitivity_rows"
                ],
                "axis_synthesis_rows": payload["axis_synthesis_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    dimension_rows = dimension_recommendation_drift_rows()
    annulus_rows = annulus_remap_rows()
    response_rows = interference_response_sensitivity_rows(dimension_rows, annulus_rows)
    synthesis_rows = axis_synthesis_rows(dimension_rows, annulus_rows, response_rows)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    payload: dict[str, Any] = {
        "dimension_recommendation_drift_rows": dimension_rows,
        "selected_annulus_remap_rows": annulus_rows,
        "interference_response_sensitivity_rows": response_rows,
        "axis_synthesis_rows": synthesis_rows,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    checks = alignment_check_rows(payload)
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    failed_checks = sum(not row["check_pass"] for row in checks)
    mainline_refocus = load_summary(SOURCE_FILES["mainline_refocus_status"])
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
        "dimension_recommendation_drift_rows": len(dimension_rows),
        "selected_annulus_remap_rows": len(annulus_rows),
        "interference_response_sensitivity_rows": len(response_rows),
        "axis_synthesis_rows": len(synthesis_rows),
        "alignment_check_rows": len(checks),
        "failed_alignment_check_rows": failed_checks,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_geometry_effects_dirty_context_rows": sum(
            row["classification"] == "non_geometry_effects_dirty_context"
            for row in dirty_context
        ),
        "sidewall_angle_grid_deg_comsol": list(SIDEWALL_DEG_COMSOL_GRID),
        "depth_grid_nm": list(DEPTH_NM_GRID),
        "particle_diameter_grid_nm": list(PARTICLE_DIAMETER_NM_GRID),
        "primary_answer_frame": (
            "dimension_window_annulus_range_and_interference_response_sensitivity"
        ),
        "not_primary_answer_frame": "route_selection_or_scalar_scoreboard",
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "next_large_block": (
            "expand response maps over accepted dimension drift bands and replace "
            "rectangular annulus coordinates with trapezoid-local bins"
        ),
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    if summary["disposition"] != DISPOSITION:
        failures.append("geometry_effects_impact_matrix_not_ready")
    if summary["dimension_recommendation_drift_rows"] == 0:
        failures.append("dimension_rows_missing")
    if summary["selected_annulus_remap_rows"] == 0:
        failures.append("annulus_rows_missing")
    if summary["interference_response_sensitivity_rows"] == 0:
        failures.append("response_rows_missing")
    if summary["failed_alignment_check_rows"] != 0:
        failures.append("failed_alignment_checks_present")
    if summary["source_missing_rows"] != 0:
        failures.append("source_missing")
    if summary["not_primary_answer_frame"] != "route_selection_or_scalar_scoreboard":
        failures.append("route_selection_not_demoted")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json",
        "dimension_drift": OUTPUT_DIR
        / f"{PREFIX}_DIMENSION_RECOMMENDATION_DRIFT_ROWS_{DATE_STAMP}.csv",
        "annulus_remap": OUTPUT_DIR
        / f"{PREFIX}_SELECTED_ANNULUS_REMAP_ROWS_{DATE_STAMP}.csv",
        "response_sensitivity": OUTPUT_DIR
        / f"{PREFIX}_INTERFERENCE_RESPONSE_SENSITIVITY_ROWS_{DATE_STAMP}.csv",
        "axis_synthesis": OUTPUT_DIR / f"{PREFIX}_AXIS_SYNTHESIS_ROWS_{DATE_STAMP}.csv",
        "alignment_checks": OUTPUT_DIR
        / f"{PREFIX}_ALIGNMENT_CHECK_ROWS_{DATE_STAMP}.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "master_report": REPORT_DIR / f"589_{PREFIX}_{DATE_STAMP}.md",
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
    write_csv_rows(outputs["dimension_drift"], payload["dimension_recommendation_drift_rows"])
    write_csv_rows(outputs["annulus_remap"], payload["selected_annulus_remap_rows"])
    write_csv_rows(
        outputs["response_sensitivity"],
        payload["interference_response_sensitivity_rows"],
    )
    write_csv_rows(outputs["axis_synthesis"], payload["axis_synthesis_rows"])
    write_csv_rows(outputs["alignment_checks"], payload["alignment_check_rows"])
    write_csv_rows(outputs["source_lock"], payload["source_lock_rows"])
    write_csv_rows(outputs["dirty_context"], payload["dirty_context_rows"])
    write_json_atomic(outputs["report_json"], payload, sort_keys=True)
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
    synthesis = payload["axis_synthesis_rows"]
    lines = [
        "# NODI Sidewall Geometry-Effects Impact Matrix",
        "",
        f"Disposition: `{s['disposition']}`",
        f"Artifact ID: `{s['artifact_id']}`",
        f"Claim boundary: `{s['claim_boundary']}`",
        "",
        "This package answers the sidewall-angle mainline in three paired "
        "rectangle-vs-trapezoid axes: dimension-window drift, selected-annulus "
        "remapping, and interference-response surrogate sensitivity.",
        "",
        f"Dimension drift rows: `{s['dimension_recommendation_drift_rows']}`.",
        f"Selected-annulus remap rows: `{s['selected_annulus_remap_rows']}`.",
        f"Interference response rows: `{s['interference_response_sensitivity_rows']}`.",
        f"Alignment check failures: `{s['failed_alignment_check_rows']}`.",
        "",
        "## Axis Synthesis",
        "",
    ]
    for row in synthesis:
        lines.extend(
            [
                f"- `{row['axis_name']}`: `{row['impact_matrix_status']}`",
                f"  Evidence rows: `{row['evidence_rows']}`",
                f"  Key observation: `{row['key_observation']}`",
                f"  Next block: {row['next_large_block']}",
            ]
        )
    lines.extend(
        [
            "",
            "The matrix preserves the ideal rectangle as a paired baseline and keeps "
            "sidewall-angle effects as simulation-derived assumptions. It does not "
            "emit a route-selection conclusion or scalar scoreboard.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_geometry_effects_impact_matrix:
        raise SystemExit(
            "--confirm-sidewall-geometry-effects-impact-matrix is required"
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
