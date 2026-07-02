#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
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

from nodi_simulator.nodi_comsol_next_artifacts import (  # noqa: E402
    COMSOL_V4_ASSUMPTION_SET_ID,
    COMSOL_V4_ASSUMPTION_SET_SHA256,
    COMSOL_V4_ASSUMPTION_SET_VERSION,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_headers,
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260703"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_COMSOL_CROSS_SECTION_DISTRIBUTION_BRIDGE"
ARTIFACT_ID = "NODI_SIDEWALL_COMSOL_CROSS_SECTION_DISTRIBUTION_BRIDGE_20260703"
SYNTHESIS_VERSION = "sidewall_comsol_cross_section_distribution_bridge_v1"
DISPOSITION = "NODI_SIDEWALL_COMSOL_CROSS_SECTION_DISTRIBUTION_BRIDGE_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_COMSOL_CROSS_SECTION_DISTRIBUTION_BRIDGE_FAIL_CLOSED"
CLAIM_BOUNDARY = "distribution_bridge_and_recompute_queue_not_final_probability_result"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

COMSOL_PROJECT_ROOT = (
    PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
)
COMSOL_DWG = COMSOL_PROJECT_ROOT / "full_chip" / "dwg_analysis"
COMSOL_TRANSPORT_220 = COMSOL_DWG / (
    "ev_pbs_v4_normal_transport_frozenflow_smoke_20260630/"
    "stage119_sw085p0_d1p2_biasp000p0nm_ch70_d220nm/"
    "EV_PBS_V4_NORMAL_NANOCHANNEL_TRANSPORT_FROZENFLOW_SMOKE_20260630_"
    "RESULTS_stage119_sw085p0_d1p2_biasp000p0nm_ch70_d220nm.csv"
)
COMSOL_TRANSPORT_300 = COMSOL_DWG / (
    "ev_pbs_v4_normal_transport_frozenflow_smoke_20260630/"
    "stage119_sw085p0_d1p2_biasp000p0nm_ch70_d300nm/"
    "EV_PBS_V4_NORMAL_NANOCHANNEL_TRANSPORT_FROZENFLOW_SMOKE_20260630_"
    "RESULTS_stage119_sw085p0_d1p2_biasp000p0nm_ch70_d300nm.csv"
)
COMSOL_NEAR_WALL = COMSOL_DWG / (
    "ev_pbs_v4_normal_near_wall_shell_extraction_smoke_20260630/"
    "stage119_sw085p0_d1p2_biasp000p0nm/"
    "EV_PBS_V4_NORMAL_NANOCHANNEL_NEAR_WALL_SHELL_EXTRACTION_SMOKE_20260630_"
    "RESULTS_stage119_sw085p0_d1p2_biasp000p0nm.csv"
)
COMSOL_TARGETED_FIELD = COMSOL_DWG / (
    "ev_pbs_v4_normal_targeted_field_extraction_smoke_20260630/"
    "stage119_sw085p0_d1p2_biasp000p0nm/"
    "EV_PBS_V4_NORMAL_NANOCHANNEL_TARGETED_FIELD_EXTRACTION_SMOKE_20260630_"
    "RESULTS_stage119_sw085p0_d1p2_biasp000p0nm.csv"
)

SOURCE_FILES = {
    "result_lock_status_604": OUTPUT_DIR
    / "NODI_SIDEWALL_THREE_QUESTION_RESULT_LOCK_STATUS_20260703.json",
    "result_lock_route_rows_604": OUTPUT_DIR
    / "NODI_SIDEWALL_THREE_QUESTION_RESULT_LOCK_ROUTE_RESULT_ROWS_20260703.csv",
    "result_lock_question_rows_604": OUTPUT_DIR
    / "NODI_SIDEWALL_THREE_QUESTION_RESULT_LOCK_QUESTION_RESULT_ROWS_20260703.csv",
    "result_lock_next_action_rows_604": OUTPUT_DIR
    / "NODI_SIDEWALL_THREE_QUESTION_RESULT_LOCK_NEXT_ACTION_ROWS_20260703.csv",
    "followup_status_603": OUTPUT_DIR
    / "NODI_SIDEWALL_FOLLOWUP_WINDOW_HIGHER_EVENT_SWEEP_STATUS_20260703.json",
    "followup_event_rows_603": OUTPUT_DIR
    / "NODI_SIDEWALL_FOLLOWUP_WINDOW_HIGHER_EVENT_SWEEP_EVENT_ROWS_20260703.csv",
    "followup_window_summary_rows_603": OUTPUT_DIR
    / "NODI_SIDEWALL_FOLLOWUP_WINDOW_HIGHER_EVENT_SWEEP_ROUTE_WINDOW_SUMMARY_ROWS_20260703.csv",
    "comsol_v4_transport_frozenflow_220nm_context": COMSOL_TRANSPORT_220,
    "comsol_v4_transport_frozenflow_300nm_context": COMSOL_TRANSPORT_300,
    "comsol_v4_near_wall_shell_context": COMSOL_NEAR_WALL,
    "comsol_v4_targeted_field_context": COMSOL_TARGETED_FIELD,
    "distribution_bridge_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_comsol_cross_section_distribution_bridge.py",
    "distribution_bridge_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_comsol_cross_section_distribution_bridge.py",
}

ALLOWED_USE = (
    "bridge the 604 sidewall dimension/annulus/interference result lock to "
    "COMSOL-v4-aligned cross-section distribution weighting and full NODI "
    "recompute planning"
)
BLOCKED_USE = (
    "treating COMSOL descriptor rows as an exact P(x,u) probability grid, "
    "final route conclusion, final yield/detection result, q_ch weighting, "
    "true W_eff, or production runtime ingestion from this bridge artifact"
)
FORBIDDEN_PRIMARY_COLUMNS = {
    "winner",
    "route_score",
    "rank",
    "detection_probability",
    "yield",
    "W_eff",
    "q_ch_eta",
    "rank_under_surrogate",
    "not_route_score",
}
EXACT_PROBABILITY_GRID_REQUIRED_COLUMNS = {
    "x_nm",
    "u_nm",
    "particle_diameter_nm",
    "probability_mass",
    "probability_density",
    "coordinate_basis",
    "geometry_profile_sha256",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build NODI sidewall COMSOL cross-section distribution bridge."
    )
    parser.add_argument(
        "--confirm-sidewall-comsol-cross-section-distribution-bridge",
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


def fnum(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        numeric = float(text)
    except ValueError:
        return default
    return numeric if math.isfinite(numeric) else default


def deterministic_sha256(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def common_guard_fields(row_id: str) -> dict[str, Any]:
    return {
        "synthesis_version": SYNTHESIS_VERSION,
        "row_id": row_id,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_final_probability_result": True,
        "not_detection_probability": True,
        "not_yield": True,
        "not_selection_metric_claim": True,
        "not_winner": True,
        "not_qch_weighted": True,
        "not_true_W_eff": True,
        "not_production_recommendation": True,
        "decision_use_allowed": False,
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "comsol_v4_assumption_set_sha256": COMSOL_V4_ASSUMPTION_SET_SHA256,
    }


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
    output_report = f"reports/605_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_comsol_cross_section_distribution_bridge.py",
        "tests/test_nodi_sidewall_comsol_cross_section_distribution_bridge.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "distribution_bridge_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "distribution_bridge_output"
            release_decision = "included_or_rewritten_by_distribution_bridge_builder"
        else:
            classification = "non_distribution_bridge_dirty_context"
            release_decision = "ignored_for_distribution_bridge"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def load_rows(source_id: str) -> list[dict[str, str]]:
    path = SOURCE_FILES[source_id]
    return read_csv_rows(path) if path.exists() else []


def csv_headers(path: Path) -> list[str]:
    if not path.exists():
        return []
    return read_csv_headers(path)


def csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


def sum_column(rows: list[dict[str, str]], column: str) -> float:
    return sum(fnum(row.get(column)) for row in rows)


def classify_comsol_source(
    source_id: str, path: Path, descriptor_family: str
) -> dict[str, Any]:
    headers = csv_headers(path)
    rows = read_csv_rows(path) if path.exists() else []
    missing_exact = sorted(EXACT_PROBABILITY_GRID_REQUIRED_COLUMNS.difference(headers))
    has_exact_grid = not missing_exact
    has_edge_bins = {"bin_idx", "edge_norm_min", "edge_norm_max"}.issubset(headers)
    has_transport_fractions = {
        "outlet_flux_fraction",
        "residence_fraction",
    }.issubset(headers)
    has_shell_volume = "shell_volume_fraction" in headers
    has_field = "q_enclosed_m3_s" in headers and "speed_mean_m_s" in headers

    if has_exact_grid:
        distribution_status = "exact_comsol_cross_section_probability_grid_available"
        bridge_use = "direct_probability_weight_candidate_after_loader_validation"
    elif has_edge_bins and has_transport_fractions:
        distribution_status = (
            "comsol_transport_edge_bin_descriptor_not_cross_section_probability_grid"
        )
        bridge_use = "606_transport_bin_reweighting_surrogate_context"
    elif has_shell_volume:
        distribution_status = "comsol_near_wall_shell_descriptor_not_particle_probability_grid"
        bridge_use = "near_wall_shell_context_for_annulus_bias_sensitivity"
    elif has_field:
        distribution_status = "comsol_targeted_field_descriptor_not_particle_probability_grid"
        bridge_use = "field_context_for_flux_surrogate_sensitivity"
    else:
        distribution_status = "not_classified_as_cross_section_probability_grid"
        bridge_use = "source_lock_only"

    return {
        **common_guard_fields(f"COMSOL-SOURCE-{source_id}"),
        "source_id": source_id,
        "path": display_path(path) if path.exists() else str(path),
        "exists": path.exists(),
        "sha256": sha256_file(path) if path.exists() else "",
        "descriptor_family": descriptor_family,
        "row_count": len(rows),
        "column_count": len(headers),
        "columns_json": json.dumps(headers, ensure_ascii=True),
        "has_exact_probability_grid_required_columns": has_exact_grid,
        "missing_exact_probability_grid_columns_json": json.dumps(
            missing_exact, ensure_ascii=True
        ),
        "has_edge_norm_transport_bins": has_edge_bins,
        "has_transport_fraction_columns": has_transport_fractions,
        "outlet_flux_fraction_sum": sum_column(rows, "outlet_flux_fraction"),
        "residence_fraction_sum": sum_column(rows, "residence_fraction"),
        "has_near_wall_shell_volume_fraction": has_shell_volume,
        "has_targeted_field_descriptor": has_field,
        "distribution_status": distribution_status,
        "selection_status": "context_source_not_route_selection",
        "mapping_status": (
            "exact_pxu_grid_mapping_available"
            if has_exact_grid
            else "descriptor_mapping_not_exact_cross_section_probability"
        ),
        "probability_grid_available": has_exact_grid,
        "edge4_exact_annulus_mapping_status": (
            "not_exact_0p5_0p8_annulus_mapping"
            if has_edge_bins
            else "not_edge_binned_source"
        ),
        "edge20_or_0p8_split_required_for_exact_annulus": has_edge_bins,
        "bridge_use": bridge_use,
        "exact_pxu_grid_accepted_now": has_exact_grid,
    }


def comsol_source_inventory_rows() -> list[dict[str, Any]]:
    return [
        classify_comsol_source(
            "transport_frozenflow_220nm_ch70_sw085_d1200",
            COMSOL_TRANSPORT_220,
            "transport_frozenflow_edge_bin_descriptor",
        ),
        classify_comsol_source(
            "transport_frozenflow_300nm_ch70_sw085_d1200",
            COMSOL_TRANSPORT_300,
            "transport_frozenflow_edge_bin_descriptor",
        ),
        classify_comsol_source(
            "near_wall_shell_sw085_d1200",
            COMSOL_NEAR_WALL,
            "near_wall_shell_descriptor",
        ),
        classify_comsol_source(
            "targeted_field_sw085_d1200",
            COMSOL_TARGETED_FIELD,
            "targeted_field_descriptor",
        ),
    ]


def distribution_model_rows() -> list[dict[str, Any]]:
    required_cols = json.dumps(
        sorted(EXACT_PROBABILITY_GRID_REQUIRED_COLUMNS), ensure_ascii=True
    )
    rows = [
        {
            **common_guard_fields("DIST-MODEL-RECTANGLE-UNIFORM"),
            "distribution_basis_id": "rectangle_uniform_accessible_baseline_v1",
            "channel_cross_section_model": "ideal_rectangle",
            "sidewall_deg_comsol": 90.0,
            "sidewall_taper_angle_deg_nodi": 0.0,
            "angle_geometry_alignment": "rectangle_baseline_90deg_comsol_0deg_nodi_taper",
            "probability_source": "nodi_uniform_accessible_area",
            "current_availability": "available_runtime_baseline",
            "selection_status": "baseline_context_not_route_selection",
            "mapping_status": "native_rectangle_baseline",
            "probability_grid_available": False,
            "feeds_full_nodi_recompute": True,
            "exact_comsol_probability_grid_required": False,
            "required_exact_grid_columns_json": "[]",
            "interpretation": "preserve idealized rectangle baseline for before/after sidewall comparison",
        },
        {
            **common_guard_fields("DIST-MODEL-TRAPEZOID-UNIFORM"),
            "distribution_basis_id": "trapezoid_uniform_accessible_surrogate_v1",
            "channel_cross_section_model": "trapezoid_tapered_sidewalls",
            "sidewall_deg_comsol": 85.0,
            "sidewall_taper_angle_deg_nodi": 5.0,
            "angle_geometry_alignment": "trapezoid_sidewall_85deg_comsol_5deg_nodi_taper",
            "probability_source": "nodi_uniform_accessible_area_over_trapezoid_center_support",
            "current_availability": "available_runtime_surrogate",
            "selection_status": "sidewall_context_not_route_selection",
            "mapping_status": "nodi_trapezoid_uniform_accessible_support",
            "probability_grid_available": False,
            "feeds_full_nodi_recompute": True,
            "exact_comsol_probability_grid_required": False,
            "required_exact_grid_columns_json": "[]",
            "interpretation": "current sidewall-aware NODI branch without COMSOL cross-section probability weighting",
        },
        {
            **common_guard_fields("DIST-MODEL-TRAPEZOID-COMSOL-BIN"),
            "distribution_basis_id": "trapezoid_comsol_v4_transport_bin_reweighted_surrogate_v1",
            "channel_cross_section_model": "trapezoid_tapered_sidewalls",
            "sidewall_deg_comsol": 85.0,
            "sidewall_taper_angle_deg_nodi": 5.0,
            "angle_geometry_alignment": "trapezoid_sidewall_85deg_comsol_5deg_nodi_taper",
            "probability_source": "comsol_v4_transport_edge_norm_bin_descriptor",
            "current_availability": "available_context_for_606_surrogate_reweighting",
            "selection_status": "shadow_context_not_route_selection",
            "mapping_status": "edge4_descriptor_reweighting_not_exact_annulus",
            "probability_grid_available": False,
            "feeds_full_nodi_recompute": True,
            "exact_comsol_probability_grid_required": False,
            "required_exact_grid_columns_json": "[]",
            "interpretation": "use COMSOL transport bin fractions as a distribution surrogate, not exact P(x,u)",
        },
        {
            **common_guard_fields("DIST-MODEL-TRAPEZOID-COMSOL-PXU"),
            "distribution_basis_id": "comsol_v4_cross_section_probability_grid_exact_required_v1",
            "channel_cross_section_model": "trapezoid_tapered_sidewalls",
            "sidewall_deg_comsol": 85.0,
            "sidewall_taper_angle_deg_nodi": 5.0,
            "angle_geometry_alignment": "trapezoid_sidewall_85deg_comsol_5deg_nodi_taper",
            "probability_source": "comsol_v4_particle_cross_section_probability_grid",
            "current_availability": "not_available_in_current_source_inventory",
            "selection_status": "pending_source_not_route_selection",
            "mapping_status": "requires_exact_pxu_or_edge20_or_explicit_0p8_split",
            "probability_grid_available": False,
            "feeds_full_nodi_recompute": False,
            "exact_comsol_probability_grid_required": True,
            "required_exact_grid_columns_json": required_cols,
            "interpretation": "future exact P(x,u) branch; no current descriptor source may be silently promoted to it",
        },
    ]
    return rows


def route_distribution_binding_rows() -> list[dict[str, Any]]:
    route_rows = load_rows("result_lock_route_rows_604")
    inventory = comsol_source_inventory_rows()
    exact_grid_available = any(row["exact_pxu_grid_accepted_now"] for row in inventory)
    available_context = [
        row["descriptor_family"] for row in inventory if row.get("exists") is True
    ]
    rows: list[dict[str, Any]] = []
    for route in route_rows:
        row_id = route["row_id"].replace("RESULT-", "DIST-BIND-")
        rows.append(
            {
                **common_guard_fields(row_id),
                "source_route_id_nodi": route["source_route_id_nodi"],
                "candidate_envelope_route_id_nodi": route[
                    "candidate_envelope_route_id_nodi"
                ],
                "route_id_role": "distribution_binding_context_not_selection",
                "source_W_nominal_nm": route["source_W_nominal_nm"],
                "candidate_envelope_W_top_nm": route[
                    "candidate_envelope_W_top_nm"
                ],
                "candidate_envelope_top_width_delta_nm": route[
                    "candidate_envelope_top_width_delta_nm"
                ],
                "dimension_result_context_604": route["dimension_result_context"],
                "followup_window_set_json": route["followup_window_set_json"],
                "annulus_change_context_604": (
                    "annulus_context_changed"
                    if fnum(route["noncanonical_windows_with_annulus_change_context"]) > 0
                    else "annulus_context_not_changed"
                ),
                "response_context_604": (
                    "response_context_changed"
                    if fnum(route["noncanonical_windows_with_response_positive_context"]) > 0
                    else "response_context_not_changed"
                ),
                "current_604_probability_weighting_status": (
                    "not_comsol_cross_section_probability_weighted"
                ),
                "current_604_position_distribution_basis": (
                    "nodi_synthetic_initial_position_event_diagnostics"
                ),
                "selection_status": "context_binding_not_route_selection",
                "mapping_status": "604_nodi_only_until_606_distribution_bridge",
                "probability_grid_available": exact_grid_available,
                "comsol_exact_cross_section_probability_grid_available_now": (
                    exact_grid_available
                ),
                "edge20_or_0p8_split_required_for_exact_annulus": True,
                "comsol_v4_context_descriptor_families_json": json.dumps(
                    sorted(available_context), ensure_ascii=True
                ),
                "bridge_required_before_comsol_weighted_answer": True,
                "full_nodi_recompute_required_after_trapezoid_geometry": True,
                "preserve_rectangle_baseline": True,
                "next_recompute_queue_scope": (
                    "rectangle_baseline_plus_trapezoid_uniform_plus_comsol_descriptor_reweighted"
                ),
            }
        )
    return rows


def question_impact_rows(
    route_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            **common_guard_fields("QUESTION-IMPACT-DIMENSION"),
            "question_id": "size_recommendation_delta_after_sidewall",
            "current_604_answer_status": (
                "dimension_envelope_changed_under_trapezoid_sidewall"
            ),
            "comsol_distribution_gap": (
                "604_not_weighted_by_comsol_particle_cross_section_probability"
            ),
            "route_rows_affected": len(route_rows),
            "required_next_step": (
                "606_distribution_weighted_recompute_then_compare_recommended_width_envelope"
            ),
        },
        {
            **common_guard_fields("QUESTION-IMPACT-ANNULUS"),
            "question_id": "selected_annulus_range_delta_after_sidewall",
            "current_604_answer_status": (
                "annulus_window_context_changed_under_trapezoid_sidewall"
            ),
            "comsol_distribution_gap": (
                "604_selected_annulus_fraction_is_nodi_event_diagnostic_not_comsol_probability"
            ),
            "route_rows_affected": len(route_rows),
            "required_next_step": (
                "606_reweight_or_recompute_annulus_occupancy_using_distribution_basis"
            ),
        },
        {
            **common_guard_fields("QUESTION-IMPACT-INTERFERENCE"),
            "question_id": "interference_response_delta_after_sidewall",
            "current_604_answer_status": (
                "peak_height_and_local_snr_context_changed_for_noncanonical_windows"
            ),
            "comsol_distribution_gap": (
                "604_mean_response_not_integrated_over_comsol_cross_section_probability"
            ),
            "route_rows_affected": len(route_rows),
            "required_next_step": (
                "606_distribution_weighted_response_surface_then_607_full_nodi_recompute"
            ),
        },
    ]


def recompute_queue_rows(route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    phases = [
        {
            "phase_id": "rectangle_baseline_relock",
            "queue_order": 1,
            "channel_cross_section_model": "ideal_rectangle",
            "distribution_basis_id": "rectangle_uniform_accessible_baseline_v1",
            "queue_action": "preserve_or_recompute_rectangle_reference_baseline",
            "execution_readiness": "ready_after_605",
            "comparison_role": "before_sidewall_baseline",
        },
        {
            "phase_id": "trapezoid_uniform_accessible_recompute",
            "queue_order": 2,
            "channel_cross_section_model": "trapezoid_tapered_sidewalls",
            "distribution_basis_id": "trapezoid_uniform_accessible_surrogate_v1",
            "queue_action": "full_nodi_recompute_under_trapezoid_uniform_accessible_support",
            "execution_readiness": "ready_after_605",
            "comparison_role": "sidewall_geometry_only_branch",
        },
        {
            "phase_id": "trapezoid_comsol_transport_bin_reweighted",
            "queue_order": 3,
            "channel_cross_section_model": "trapezoid_tapered_sidewalls",
            "distribution_basis_id": "trapezoid_comsol_v4_transport_bin_reweighted_surrogate_v1",
            "queue_action": "distribution_weighted_nodi_response_using_comsol_transport_bin_context",
            "execution_readiness": "ready_for_606_bridge_reweighting",
            "comparison_role": "sidewall_geometry_plus_comsol_v4_distribution_surrogate",
        },
        {
            "phase_id": "trapezoid_exact_comsol_pxu_pending",
            "queue_order": 4,
            "channel_cross_section_model": "trapezoid_tapered_sidewalls",
            "distribution_basis_id": "comsol_v4_cross_section_probability_grid_exact_required_v1",
            "queue_action": "future_exact_comsol_probability_grid_loader_and_recompute",
            "execution_readiness": "requires_exact_pxu_grid_source",
            "comparison_role": "future_exact_comsol_probability_branch",
        },
    ]
    rows: list[dict[str, Any]] = []
    for route in route_rows:
        for phase in phases:
            phase_id = phase["phase_id"]
            rows.append(
                {
                    **common_guard_fields(
                        f"RECOMPUTE-{route['source_route_id_nodi'].replace('/', '_')}-{phase_id}"
                    ),
                    "source_route_id_nodi": route["source_route_id_nodi"],
                    "candidate_envelope_route_id_nodi": route[
                        "candidate_envelope_route_id_nodi"
                    ],
                    "route_id_role": "recompute_queue_context_not_selection",
                    "candidate_envelope_W_top_nm": route[
                        "candidate_envelope_W_top_nm"
                    ],
                    "candidate_envelope_top_width_delta_nm": route[
                        "candidate_envelope_top_width_delta_nm"
                    ],
                    "followup_window_set_json": route["followup_window_set_json"],
                    "phase_id": phase_id,
                    "queue_order": phase["queue_order"],
                    "channel_cross_section_model": phase[
                        "channel_cross_section_model"
                    ],
                    "distribution_basis_id": phase["distribution_basis_id"],
                    "queue_action": phase["queue_action"],
                    "execution_readiness": phase["execution_readiness"],
                    "comparison_role": phase["comparison_role"],
                    "selection_status": "queued_context_not_route_selection",
                    "mapping_status": (
                        "exact_mapping_pending_source"
                        if phase_id == "trapezoid_exact_comsol_pxu_pending"
                        else "runnable_surrogate_or_baseline_mapping"
                    ),
                    "probability_grid_available": False,
                    "uses_604_result_as_input_context": True,
                    "requires_full_nodi_recompute": phase_id
                    != "trapezoid_exact_comsol_pxu_pending",
                    "requires_exact_comsol_pxu_grid": phase_id
                    == "trapezoid_exact_comsol_pxu_pending",
                }
            )
    return rows


def validation_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        rows.append(
            {
                "check_id": check_id,
                "status": "pass" if passed else "fail",
                "detail": detail,
            }
        )

    route_rows = payload["route_distribution_binding_rows"]
    queue_rows = payload["recompute_queue_rows"]
    inventory = payload["comsol_source_inventory_rows"]
    model_rows = payload["distribution_model_rows"]
    question_rows = payload["question_impact_rows"]

    add(
        "604_route_binding_covers_six_routes",
        len(route_rows) == 6,
        f"route_distribution_binding_rows={len(route_rows)}",
    )
    add(
        "current_604_marked_not_comsol_probability_weighted",
        all(
            row["current_604_probability_weighting_status"]
            == "not_comsol_cross_section_probability_weighted"
            for row in route_rows
        ),
        "604 result lock remains NODI event diagnostic until 606 weighting",
    )
    add(
        "comsol_sources_not_silently_promoted_to_exact_pxu_grid",
        all(row["exact_pxu_grid_accepted_now"] is False for row in inventory),
        "current COMSOL CSVs are descriptor/bin/shell/field context, not exact P(x,u)",
    )
    add(
        "distribution_models_include_baseline_trapezoid_and_comsol_context",
        {
            row["distribution_basis_id"] for row in model_rows
        }
        == {
            "rectangle_uniform_accessible_baseline_v1",
            "trapezoid_uniform_accessible_surrogate_v1",
            "trapezoid_comsol_v4_transport_bin_reweighted_surrogate_v1",
            "comsol_v4_cross_section_probability_grid_exact_required_v1",
        },
        "four explicit distribution bases prevent rectangle/trapezoid/COMSOL mixing",
    )
    add(
        "recompute_queue_has_four_phases_per_route",
        len(queue_rows) == 24
        and all(
            sum(
                1
                for row in queue_rows
                if row["source_route_id_nodi"] == route["source_route_id_nodi"]
            )
            == 4
            for route in route_rows
        ),
        f"recompute_queue_rows={len(queue_rows)}",
    )
    add(
        "question_impacts_cover_three_user_questions",
        {
            row["question_id"] for row in question_rows
        }
        == {
            "size_recommendation_delta_after_sidewall",
            "selected_annulus_range_delta_after_sidewall",
            "interference_response_delta_after_sidewall",
        },
        "dimension, annulus, and interference-response all carry distribution gap",
    )
    add(
        "v4_assumption_hash_bound",
        all(
            row["comsol_v4_assumption_set_sha256"] == COMSOL_V4_ASSUMPTION_SET_SHA256
            for table in (
                route_rows,
                queue_rows,
                inventory,
                model_rows,
                question_rows,
            )
            for row in table
        ),
        COMSOL_V4_ASSUMPTION_SET_SHA256,
    )
    add(
        "no_forbidden_primary_columns",
        no_forbidden_primary_columns(payload),
        "bridge outputs avoid score/winner/yield/detection/W_eff/q_ch primary columns",
    )
    return rows


def no_forbidden_primary_columns(payload: dict[str, Any]) -> bool:
    for table_name in (
        "comsol_source_inventory_rows",
        "distribution_model_rows",
        "route_distribution_binding_rows",
        "question_impact_rows",
        "recompute_queue_rows",
    ):
        rows = payload[table_name]
        columns = set().union(*(set(row) for row in rows)) if rows else set()
        if FORBIDDEN_PRIMARY_COLUMNS.intersection(columns):
            return False
    return True


def manifest_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.append(
            {
                "artifact_id": ARTIFACT_ID,
                "path": display_path(path),
                "sha256": sha256_file(path) if path.exists() else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_payload() -> dict[str, Any]:
    route_rows_604 = load_rows("result_lock_route_rows_604")
    event_rows_603 = load_rows("followup_event_rows_603")
    inventory = comsol_source_inventory_rows()
    model_rows = distribution_model_rows()
    route_rows = route_distribution_binding_rows()
    question_rows = question_impact_rows(route_rows)
    queue_rows = recompute_queue_rows(route_rows)
    source_rows = source_lock_rows()
    dirty_rows = dirty_context_rows()
    payload: dict[str, Any] = {
        "artifact_id": ARTIFACT_ID,
        "synthesis_version": SYNTHESIS_VERSION,
        "date_stamp": DATE_STAMP,
        "disposition": DISPOSITION,
        "claim_boundary": CLAIM_BOUNDARY,
        "git_head": git_head(),
        "git_branch": git_branch(),
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "comsol_v4_assumption_set_sha256": COMSOL_V4_ASSUMPTION_SET_SHA256,
        "summary": {
            "route_rows_604": len(route_rows_604),
            "followup_event_rows_603": len(event_rows_603),
            "comsol_source_inventory_rows": len(inventory),
            "distribution_model_rows": len(model_rows),
            "route_distribution_binding_rows": len(route_rows),
            "question_impact_rows": len(question_rows),
            "recompute_queue_rows": len(queue_rows),
            "current_604_comsol_cross_section_probability_weighted": False,
            "exact_comsol_cross_section_probability_grid_available_now": any(
                row["exact_pxu_grid_accepted_now"] for row in inventory
            ),
            "next_executable_block": (
                "606_distribution_weighted_nodi_response_surface_and_full_recompute"
            ),
        },
        "comsol_source_inventory_rows": inventory,
        "distribution_model_rows": model_rows,
        "route_distribution_binding_rows": route_rows,
        "question_impact_rows": question_rows,
        "recompute_queue_rows": queue_rows,
        "source_lock_rows": source_rows,
        "dirty_context_rows": dirty_rows,
    }
    validation = validation_rows(payload)
    payload["validation_rows"] = validation
    payload["summary"]["failed_validation_rows"] = sum(
        1 for row in validation if row["status"] != "pass"
    )
    if payload["summary"]["failed_validation_rows"]:
        payload["disposition"] = BLOCKED_DISPOSITION
    payload["payload_sha256"] = deterministic_sha256(
        {
            key: value
            for key, value in payload.items()
            if key not in {"payload_sha256", "dirty_context_rows"}
        }
    )
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for row in payload["validation_rows"]:
        if row["status"] != "pass":
            failures.append(f"{row['check_id']}: {row['detail']}")
    return failures


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# NODI sidewall COMSOL cross-section distribution bridge",
        "",
        "## Route lock",
        "",
        (
            "This artifact keeps the 604 sidewall result lock in scope while "
            "making the missing COMSOL cross-section probability axis explicit."
        ),
        "",
        "- Rectangle baseline is preserved.",
        "- Trapezoid sidewall branch remains a separate recompute branch.",
        "- Current 604 rows are marked `not_comsol_cross_section_probability_weighted`.",
        "- Current COMSOL v4 CSVs are accepted only as descriptor/bin/shell/field context unless an exact `P(x,u)` grid is present.",
        "",
        "## Counts",
        "",
        f"- 604 route rows: {summary['route_rows_604']}",
        f"- 603 follow-up event rows: {summary['followup_event_rows_603']}",
        f"- COMSOL source inventory rows: {summary['comsol_source_inventory_rows']}",
        f"- distribution models: {summary['distribution_model_rows']}",
        f"- recompute queue rows: {summary['recompute_queue_rows']}",
        f"- failed validation rows: {summary['failed_validation_rows']}",
        "",
        "## Next block",
        "",
        (
            "`606_distribution_weighted_nodi_response_surface_and_full_recompute` "
            "should consume the queue emitted here and compare dimension envelope, "
            "selected annulus occupancy, and interference-response under the "
            "rectangle baseline, trapezoid uniform-accessible branch, and COMSOL "
            "transport-bin reweighted surrogate branch."
        ),
        "",
    ]
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json"
    report_json_path = OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json"
    inventory_path = OUTPUT_DIR / f"{PREFIX}_COMSOL_SOURCE_INVENTORY_{DATE_STAMP}.csv"
    model_path = OUTPUT_DIR / f"{PREFIX}_DISTRIBUTION_MODEL_ROWS_{DATE_STAMP}.csv"
    route_path = OUTPUT_DIR / f"{PREFIX}_ROUTE_DISTRIBUTION_BINDING_ROWS_{DATE_STAMP}.csv"
    question_path = OUTPUT_DIR / f"{PREFIX}_QUESTION_IMPACT_ROWS_{DATE_STAMP}.csv"
    queue_path = OUTPUT_DIR / f"{PREFIX}_RECOMPUTE_QUEUE_ROWS_{DATE_STAMP}.csv"
    validation_path = OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv"
    source_lock_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv"
    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv"
    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv"
    report_md_path = REPORT_DIR / f"605_{PREFIX}_{DATE_STAMP}.md"

    status_payload = {
        key: payload[key]
        for key in (
            "artifact_id",
            "synthesis_version",
            "date_stamp",
            "disposition",
            "claim_boundary",
            "git_head",
            "git_branch",
            "comsol_v4_assumption_set_id",
            "comsol_v4_assumption_set_version",
            "comsol_v4_assumption_set_sha256",
            "summary",
            "payload_sha256",
        )
    }
    write_json_atomic(status_path, status_payload, sort_keys=True)
    write_json_atomic(report_json_path, payload, sort_keys=True)
    write_csv_rows(inventory_path, payload["comsol_source_inventory_rows"])
    write_csv_rows(model_path, payload["distribution_model_rows"])
    write_csv_rows(route_path, payload["route_distribution_binding_rows"])
    write_csv_rows(question_path, payload["question_impact_rows"])
    write_csv_rows(queue_path, payload["recompute_queue_rows"])
    write_csv_rows(validation_path, payload["validation_rows"])
    write_csv_rows(source_lock_path, payload["source_lock_rows"])
    write_csv_rows(dirty_path, payload["dirty_context_rows"] or [{"path": "", "git_status": "", "classification": "clean", "release_decision": "none"}])

    paths = [
        status_path,
        report_json_path,
        inventory_path,
        model_path,
        route_path,
        question_path,
        queue_path,
        validation_path,
        source_lock_path,
        dirty_path,
        report_md_path,
    ]
    report_md_path.write_text(render_report(payload), encoding="utf-8", newline="\n")
    write_csv_rows(manifest_path, manifest_rows(paths))
    paths.append(manifest_path)
    return paths


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_sidewall_comsol_cross_section_distribution_bridge:
        print(
            "--confirm-sidewall-comsol-cross-section-distribution-bridge is required",
            file=sys.stderr,
        )
        return 2
    payload = build_payload()
    failures = validate_payload(payload)
    paths = write_outputs(payload)
    print(json.dumps(payload["summary"], sort_keys=True))
    for path in paths:
        print(display_path(path))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
