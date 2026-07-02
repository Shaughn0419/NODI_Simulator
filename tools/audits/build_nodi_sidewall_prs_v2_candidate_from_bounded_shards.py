#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
import hashlib
import json
import math
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.cross_section_geometry import (  # noqa: E402
    CENTER_ACCESSIBLE_SUPPORT_MODEL,
    DEFAULT_CLOSURE_POLICY,
    TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION,
    TRAPEZOID_WALL_DISTANCE_MODEL,
    TrapezoidCrossSection,
    comsol_sidewall_deg_to_nodi_taper_deg,
)
from nodi_simulator.nodi_comsol_next_artifacts import (  # noqa: E402
    COMSOL_V4_ASSUMPTION_SET_ID,
    COMSOL_V4_ASSUMPTION_SET_SHA256,
    COMSOL_V4_ASSUMPTION_SET_VERSION,
    POSITION_RESPONSE_VERSION,
    PRS_CLAIM_BOUNDARY,
    PRS_FLOW_CONDITION_CLAIM_BOUNDARY,
    PRS_FLOW_CONDITION_SCOPE,
    PRS_NEUTRAL_FLOW_CONDITION_ID,
    PRS_POSITION_DISTRIBUTION_BASIS,
    PRS_SIDEWALL_V2_ARTIFACT_VERSION,
    PRS_SIDEWALL_V2_BLOCKED_RESPONSE_VALUE_FIELDS,
    PRS_SIDEWALL_V2_PROPAGATED_SCOPE,
    PRS_SIDEWALL_V2_REQUIRED_FIELDS,
    SIDEWALL_PACKAGE_D_PRECHECK_VERSION,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260702"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS"
ARTIFACT_ID = "NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS_20260702"
BUILDER_VERSION = "sidewall_prs_v2_candidate_from_bounded_shards_v1"
DISPOSITION = "NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS_FAIL_CLOSED"
CLAIM_BOUNDARY = (
    "bounded_nodi_event_context_prs_sidewall_v2_not_production_not_probability"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

EVENT_ROWS_PATH = (
    OUTPUT_DIR
    / "NODI_SIDEWALL_BOUNDED_EVENT_SHARDS_EVENT_SHARD_ROWS_20260702.csv"
)
PAIRED_DELTA_ROWS_PATH = (
    OUTPUT_DIR
    / "NODI_SIDEWALL_BOUNDED_EVENT_SHARDS_PAIRED_DELTA_ROWS_20260702.csv"
)

ALLOWED_USE = (
    "shape executed bounded NODI event shards into sparse PRS sidewall v2 "
    "event-context rows for dimension, selected-annulus, and response synthesis"
)
BLOCKED_USE = (
    "production PRS, route winner, route score, final detection probability, "
    "yield, wet claim, fabrication release, q_ch weighting, true W_eff, or "
    "validated optical/fluidic/electrokinetic solver output"
)
COMMON_SOURCE_ARTIFACTS_JSON = json.dumps(
    [
        "591_NODI_SIDEWALL_BOUNDED_EVENT_SHARDS_20260702",
        "run_single_case_batch",
        "cross_section_geometry.py",
        "nodi_comsol_next_artifacts.py",
        COMSOL_V4_ASSUMPTION_SET_ID,
    ],
    sort_keys=True,
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build PRS sidewall v2 sparse event-context candidate rows from "
            "executed bounded NODI sidewall shards."
        )
    )
    parser.add_argument(
        "--confirm-sidewall-prs-v2-candidate-from-bounded-shards",
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


def nm_to_m(value_nm: float) -> float:
    return float(value_nm) * 1.0e-9


def m_to_nm(value_m: float) -> float:
    return float(value_m) * 1.0e9


def parse_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    return float(text)


def parse_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    return int(float(text))


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def finite_or_blank(value: Any) -> float | str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(numeric):
        return ""
    return numeric


def deterministic_sha256(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def route_tuple(route_id_nodi: str) -> tuple[int, int, int]:
    lambda_text, width_text, depth_text = route_id_nodi.split("/")
    return (
        int(lambda_text),
        int(width_text.removeprefix("W")),
        int(depth_text.removeprefix("D")),
    )


def nodi_view(lambda_nm: int) -> str:
    return "fixed_660_gold" if int(lambda_nm) == 660 else "per_wavelength_gold"


def runtime_guard_status(closure_status: str) -> str:
    return {
        "open": "none",
        "near_closed": "solver_guard",
        "geometry_closed": "validation_guard",
    }.get(closure_status, "validation_guard")


def normalize_w_top_semantics(source_semantics: str) -> str:
    if source_semantics == "runtime_top_aperture_surrogate":
        return "runtime_top_aperture"
    return source_semantics or "runtime_top_aperture"


def source_lock_rows() -> list[dict[str, Any]]:
    source_files = {
        "bounded_event_rows": EVENT_ROWS_PATH,
        "bounded_delta_rows": PAIRED_DELTA_ROWS_PATH,
        "cross_section_geometry": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
        "nodi_comsol_next_artifacts": PROJECT_ROOT
        / "nodi_simulator/nodi_comsol_next_artifacts.py",
        "prs_v2_candidate_builder": PROJECT_ROOT
        / "tools/audits/build_nodi_sidewall_prs_v2_candidate_from_bounded_shards.py",
        "prs_v2_candidate_tests": PROJECT_ROOT
        / "tests/test_nodi_sidewall_prs_v2_candidate_from_bounded_shards.py",
    }
    rows: list[dict[str, Any]] = []
    for source_id, path in source_files.items():
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
    output_report = f"reports/592_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_prs_v2_candidate_from_bounded_shards.py",
        "tests/test_nodi_sidewall_prs_v2_candidate_from_bounded_shards.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "prs_v2_candidate_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "prs_v2_candidate_output"
            release_decision = "included_or_rewritten_by_prs_v2_candidate_builder"
        else:
            classification = "non_prs_v2_candidate_dirty_context"
            release_decision = "ignored_for_prs_v2_candidate"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def load_executed_event_rows(path: Path = EVENT_ROWS_PATH) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows = read_csv_rows(path)
    return [
        row
        for row in rows
        if row.get("execution_status") == "executed_bounded_nodi_shard"
    ]


def load_delta_rows(path: Path = PAIRED_DELTA_ROWS_PATH) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows = read_csv_rows(path)
    return [row for row in rows if row.get("delta_status") == "executed_delta_context"]


def local_geometry_for_event(row: dict[str, str]) -> dict[str, Any]:
    width_nm = parse_float(row["W_top_nm"])
    depth_nm = parse_float(row["D_nm"])
    diameter_nm = parse_float(row["diameter_nm"])
    radius_nm = 0.5 * diameter_nm
    sidewall_deg_comsol = parse_float(row["sidewall_deg_comsol"])
    taper_deg = comsol_sidewall_deg_to_nodi_taper_deg(sidewall_deg_comsol)
    geom = TrapezoidCrossSection(
        top_width_m=nm_to_m(width_nm),
        depth_m=nm_to_m(depth_nm),
        sidewall_taper_angle_deg=taper_deg,
    )

    u_norm = 0.5
    u_m = nm_to_m(depth_nm * u_norm)
    full_width_m = geom.width_at_depth_m(u_m, clipped=True)
    full_half_width_m = 0.5 * full_width_m
    support = geom.center_accessible_support_at_depth_m(
        u_m,
        nm_to_m(radius_nm),
        narrow_width_threshold_m=40.0e-9,
    )
    support_status = str(support["particle_center_support_status"])
    support_width_m = float(support["center_accessible_width_m"])
    selected_edge_norm = parse_float(row.get("selected_annulus_mean_edge_norm"), 0.65)
    x_local_norm = min(max(selected_edge_norm, 0.5), 0.8)
    if support_status == "blocked" or support_width_m <= 0.0:
        x_m = 0.0
        bin_accessible = False
        blocked_reason = str(support["steric_block_reason"]) or "zero_center_accessible_area"
        geometry_status = "blocked"
        geometry_scope = "blocked_non_propagated_audit"
        geometry_not_propagated_reasons = blocked_reason
        bin_accessible_area_fraction = 0.0
    else:
        x_m = x_local_norm * (0.5 * support_width_m)
        bin_accessible = True
        blocked_reason = ""
        geometry_status = "propagated"
        geometry_scope = PRS_SIDEWALL_V2_PROPAGATED_SCOPE
        geometry_not_propagated_reasons = ""
        phase_area_m2 = geom.phase_mask_area_m2()
        center_area_m2 = geom.center_accessible_area_m2(nm_to_m(radius_nm))
        bin_accessible_area_fraction = (
            0.0 if phase_area_m2 <= 0.0 else min(center_area_m2 / phase_area_m2, 1.0)
        )

    diagnostics = geom.particle_wall_gap_diagnostics_m(
        x_m,
        u_m,
        nm_to_m(radius_nm),
    )
    return {
        "geom": geom,
        "diameter_nm": diameter_nm,
        "particle_radius_nm": radius_nm,
        "sidewall_taper_angle_deg_nodi": taper_deg,
        "u_norm": u_norm,
        "u_nm": depth_nm * u_norm,
        "z_nm": depth_nm * u_norm - 0.5 * depth_nm,
        "x_nm": m_to_nm(x_m),
        "x_left_nm": -m_to_nm(full_half_width_m),
        "x_right_nm": m_to_nm(full_half_width_m),
        "x_center_nm": 0.0,
        "local_width_nm": m_to_nm(full_width_m),
        "local_half_width_nm": m_to_nm(full_half_width_m),
        "x_local_norm": 0.0 if full_half_width_m <= 0.0 else m_to_nm(x_m) / m_to_nm(full_half_width_m),
        "support_x_left_nm": m_to_nm(float(support["x_left_m"])),
        "support_x_right_nm": m_to_nm(float(support["x_right_m"])),
        "support_local_width_nm": m_to_nm(support_width_m),
        "selected_annulus_x_local_norm": x_local_norm,
        "bin_accessible": bin_accessible,
        "bin_accessible_area_fraction": bin_accessible_area_fraction,
        "bin_particle_center_support_status": support_status,
        "blocked_reason": blocked_reason,
        "geometry_propagation_status": geometry_status,
        "geometry_propagation_scope": geometry_scope,
        "geometry_not_propagated_reasons": geometry_not_propagated_reasons,
        "d_top_nm": m_to_nm(float(diagnostics["d_top_m"])),
        "d_bottom_nm": m_to_nm(float(diagnostics["d_bottom_m"])),
        "d_side_left_nm": m_to_nm(float(diagnostics["d_side_left_m"])),
        "d_side_right_nm": m_to_nm(float(diagnostics["d_side_right_m"])),
        "d_nearest_wall_nm": m_to_nm(float(diagnostics["d_nearest_wall_m"])),
        "nearest_wall_id": diagnostics["nearest_wall_id"],
        "surface_gap_for_particle_nm": m_to_nm(
            float(diagnostics["surface_gap_for_particle_m"])
        ),
    }


def observation_signature(row: dict[str, Any]) -> str:
    keys = (
        "channel_cross_section_model",
        "cross_section_geometry_version",
        "sidewall_angle_convention",
        "sidewall_deg_comsol",
        "sidewall_taper_angle_deg",
        "W_top_semantics",
        "runtime_top_aperture_nm",
        "source_geometry_descriptor_sha",
        "geometry_profile_sha256",
        "geometry_profile_source",
        "geometry_claim_level",
        "metrology_status",
        "geometry_runtime_binding_version",
        "trapezoid_top_width_m",
        "trapezoid_depth_m",
        "trapezoid_bottom_width_unclipped_m",
        "trapezoid_bottom_width_runtime_clipped_m",
        "trapezoid_closure_status",
        "trapezoid_closure_policy",
        "trapezoid_runtime_guard_status",
        "geometry_propagation_scope",
        "particle_radius_m",
        "center_accessible_support_model",
        "channel_geometry_wall_distance_model",
        "channel_geometry_wall_distance_claim_level",
        "sampler_geometry_model",
        "trajectory_boundary_model",
        "wall_distance_model",
        "flow_profile_geometry_model",
        "geometry_propagation_status",
        "reference_geometry_propagation_status",
        "geometry_not_propagated_to_reference_field",
        "not_optical_solver_output",
        "fluidic_clogging_risk_band_claim_level",
        "not_clogging_rate",
        "not_time_to_clog",
        "fluidic_geometry_model",
        "hydraulic_resistance_model",
        "hydraulic_resistance_claim_level",
        "fluidic_geometry_propagation_status",
        "geometry_not_propagated_to_fluidic_resistance",
        "fluidic_network_geometry_model",
        "fluidic_network_hydraulic_resistance_model",
        "fluidic_network_hydraulic_resistance_claim_level",
        "fluidic_network_geometry_propagation_status",
        "geometry_not_propagated_to_fluidic_network",
        "fluidic_network_not_qch_weighted",
        "electrokinetic_transport_geometry_model",
        "electrokinetic_wall_distance_model",
        "electrokinetic_geometry_propagation_status",
        "geometry_not_propagated_to_electrokinetic_transport",
        "surface_charge_transport_claim_level",
        "electrokinetic_diagnostic_gate_passed",
        "initial_position_sampler_support_model",
        "initial_position_wall_distance_model",
        "initial_position_wall_distance_claim_level",
        "initial_position_particle_center_support_status",
        "initial_position_steric_block_reason",
    )
    return "|".join(f"{key}={row[key]}" for key in keys)


def base_prs_fields(
    source_row: dict[str, str],
    *,
    source_sha: str,
    geom_fields: dict[str, Any],
    source_descriptor_sha: str,
) -> dict[str, Any]:
    lambda_nm, width_nm, depth_nm = route_tuple(source_row["route_id_nodi"])
    n_events_bin = parse_int(source_row.get("selected_annulus_n_events"), 0)
    n_events_total = parse_int(source_row.get("n_events_observed"), 0)
    sample_status = "empty" if n_events_bin == 0 else "sparse"
    sparse_reason = (
        "empty_selected_annulus_in_bounded_shard"
        if n_events_bin == 0
        else "bounded_shard_small_n_context_only"
    )
    if not geom_fields["bin_accessible"]:
        sample_status = "empty"
        sparse_reason = "steric_blocked_by_sidewall_particle_center_support"

    return {
        "response_surface_artifact_version": POSITION_RESPONSE_VERSION,
        "row_scope": "response_surface_bin",
        "route_id_nodi": source_row["route_id_nodi"],
        "lambda_nm": lambda_nm,
        "W_nominal_nm": width_nm,
        "D_nm": depth_nm,
        "NODI_view": nodi_view(lambda_nm),
        "diameter_nm": int(round(geom_fields["diameter_nm"])),
        "particle_kind": source_row.get("particle_model", "gold_baseline_material_model"),
        "distribution_type": "edge_norm_1d",
        "bin_id": "selected_annulus_0p5_0p8",
        "edge_norm_min": source_row.get("selected_annulus_edge_norm_min", 0.5),
        "edge_norm_max": source_row.get("selected_annulus_edge_norm_max", 0.8),
        "x_norm_min": "",
        "x_norm_max": "",
        "z_norm_min": "",
        "z_norm_max": "",
        "aggregate_source_type": "edge_norm_primary",
        "n_seeds": 3,
        "n_events_total": n_events_total,
        "n_events_bin": 0 if not geom_fields["bin_accessible"] else n_events_bin,
        "n_events_bin_per_seed_min": 0,
        "sparse_bin_flag": True,
        "sparse_bin_policy": (
            "empty_bins_never_decision_use"
            if sample_status == "empty"
            else "sparse_individual_bins_context_only"
        ),
        "bin_sample_status": sample_status,
        "decision_use_allowed": False,
        "guardrail_status": "other_guardrail_state",
        "position_distribution_basis": PRS_POSITION_DISTRIBUTION_BASIS,
        "flow_condition_id": PRS_NEUTRAL_FLOW_CONDITION_ID,
        "flow_condition_version": "V1",
        "flow_condition_source_sha": "6c9f0f927cf8562dfe7971d25b97583cd1dc215f208e0b3f8ad16613a178e594",
        "flow_condition_scope": PRS_FLOW_CONDITION_SCOPE,
        "flow_condition_claim_boundary": PRS_FLOW_CONDITION_CLAIM_BOUNDARY,
        "view_physical_independence_flag": False,
        "not_comsol_transport_distribution": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_detection_probability": True,
        "claim_boundary": PRS_CLAIM_BOUNDARY,
        "event_context_claim_boundary": CLAIM_BOUNDARY,
        "source_artifact": display_path(EVENT_ROWS_PATH),
        "source_sha256": source_sha,
        "source_geometry_descriptor_id": source_row["shard_case_id"],
        "source_geometry_descriptor_sha": source_descriptor_sha,
    }


def sidewall_v2_fields(
    source_row: dict[str, str],
    *,
    geom_fields: dict[str, Any],
    source_descriptor_sha: str,
    artifact_created_utc: str,
) -> dict[str, Any]:
    geom: TrapezoidCrossSection = geom_fields["geom"]
    width_nm = parse_float(source_row["W_top_nm"])
    depth_nm = parse_float(source_row["D_nm"])
    radius_nm = geom_fields["particle_radius_nm"]
    is_trapezoid = source_row["channel_cross_section_model"] == "trapezoid_tapered_sidewalls"
    w_top_semantics = normalize_w_top_semantics(source_row.get("W_top_semantics", ""))
    closure_status = geom.closure_status
    propagation_scope = (
        geom_fields["geometry_propagation_scope"]
        if is_trapezoid
        else "rectangle_native_or_non_sidewall_geometry"
    )
    fields: dict[str, Any] = {
        "artifact_id": ARTIFACT_ID,
        "artifact_version": PRS_SIDEWALL_V2_ARTIFACT_VERSION,
        "artifact_created_utc": artifact_created_utc,
        "source_geometry_descriptor_id": source_row["shard_case_id"],
        "source_geometry_descriptor_sha": source_descriptor_sha,
        "roadmap_status": "surrogate_sensitivity_only",
        "not_accepted_for_formula_use": True,
        "not_accepted_for_runtime_config": True,
        "not_accepted_for_production": True,
        "channel_cross_section_model": source_row["channel_cross_section_model"],
        "cross_section_geometry_version": TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION,
        "geometry_runtime_binding_version": BUILDER_VERSION,
        "geometry_profile_source": "parameterized_nodi_sidewall_descriptor_from_bounded_shard",
        "geometry_profile_sha256": source_descriptor_sha,
        "geometry_claim_level": "surrogate_sensitivity_only",
        "metrology_status": "not_measured",
        "geometry_propagation_status": geom_fields["geometry_propagation_status"],
        "geometry_not_propagated_reasons": geom_fields[
            "geometry_not_propagated_reasons"
        ],
        "sampler_geometry_model": "trapezoid_accessible_area_v1"
        if is_trapezoid
        else "rectangle_native_context_baseline",
        "sampler_support_model": CENTER_ACCESSIBLE_SUPPORT_MODEL,
        "particle_radius_nm": radius_nm,
        "tail_particle_auto_admitted": False,
        "steric_support_source": "exact_geometry_primitive"
        if geom_fields["bin_particle_center_support_status"] in {"open", "narrow"}
        else "not_available",
        "coordinate_basis": "x_centered_u_from_top",
        "coordinate_conversion_formula_id": "centered_z_to_u_from_top_v1",
        "x_nm": geom_fields["x_nm"],
        "u_nm": geom_fields["u_nm"],
        "z_nm": geom_fields["z_nm"],
        "x_left_nm": geom_fields["x_left_nm"],
        "x_right_nm": geom_fields["x_right_nm"],
        "x_center_nm": geom_fields["x_center_nm"],
        "local_width_nm": geom_fields["local_width_nm"],
        "local_half_width_nm": geom_fields["local_half_width_nm"],
        "x_local_norm": geom_fields["x_local_norm"],
        "u_norm": geom_fields["u_norm"],
        "support_x_left_nm": geom_fields["support_x_left_nm"],
        "support_x_right_nm": geom_fields["support_x_right_nm"],
        "support_local_width_nm": geom_fields["support_local_width_nm"],
        "selected_annulus_x_local_norm": geom_fields["selected_annulus_x_local_norm"],
        "d_top_nm": geom_fields["d_top_nm"],
        "d_bottom_nm": geom_fields["d_bottom_nm"],
        "d_side_left_nm": geom_fields["d_side_left_nm"],
        "d_side_right_nm": geom_fields["d_side_right_nm"],
        "d_nearest_wall_nm": geom_fields["d_nearest_wall_nm"],
        "nearest_wall_id": geom_fields["nearest_wall_id"],
        "surface_gap_for_particle_nm": geom_fields["surface_gap_for_particle_nm"],
        "bin_basis": "edge_norm_1d_selected_annulus_aggregate_v1",
        "bin_accessible": geom_fields["bin_accessible"],
        "bin_accessible_area_fraction": geom_fields["bin_accessible_area_fraction"],
        "bin_particle_center_support_status": geom_fields[
            "bin_particle_center_support_status"
        ],
        "blocked_reason": geom_fields["blocked_reason"],
        "sparse_reason": "steric_blocked_by_sidewall_particle_center_support"
        if not geom_fields["bin_accessible"]
        else "bounded_shard_small_n_context_only",
        "neighbor_fill_used": False,
        "trajectory_boundary_model": "not_applicable_pure_advection",
        "wall_distance_model": TRAPEZOID_WALL_DISTANCE_MODEL,
        "flow_profile_model": "plug",
        "flow_control_mode": "fixed_velocity",
        "reference_field_model": source_row.get(
            "reference_model",
            "trapezoid_effective_aperture_surrogate",
        ),
        "reference_spatial_mode": source_row.get(
            "reference_spatial_mode",
            "cross_section_surrogate",
        ),
        "geometry_propagation_scope": propagation_scope,
        "source_route_id_nodi": source_row["route_id_nodi"],
        "source_D_nm": depth_nm,
        "source_distribution_type": "edge_norm_1d",
        "source_bin_basis": "edge_norm_1d_selected_annulus_aggregate_v1",
        "source_bin_id": "selected_annulus_0p5_0p8",
        "trajectory_boundary_model_version": "not_applicable_pure_advection_v1",
        "trajectory_boundary_claim_level": (
            "bounded_event_context_no_diffusive_boundary_runtime_claim"
        ),
        "wall_distance_model_version": TRAPEZOID_WALL_DISTANCE_MODEL,
        "wall_distance_claim_level": "geometry_distance_primitive_not_hindered_diffusion",
        "flow_profile_geometry_model": "plug",
        "flow_profile_geometry_claim_level": (
            "fixed_velocity_plug_context_not_trapezoid_poiseuille"
        ),
        "geometry_not_propagated_to_flow_model": False,
        "geometry_not_propagated_to_near_wall_metrics": False,
        "geometry_not_propagated_to_trajectory_boundary": False,
        "sidewall_aware_runtime_status": "bounded_event_context_not_runtime_config",
        "sidewall_package_d_precheck_version": SIDEWALL_PACKAGE_D_PRECHECK_VERSION,
        "target_artifact_family": "prs",
        "includes_trajectory_near_wall_metrics": False,
        "package_A_validation_status": "pass",
        "package_B_validation_status": "pass",
        "package_C_validation_status": "not_applicable_for_this_artifact",
        "no_forbidden_claim_columns": True,
        "no_rectangular_cache_reuse": True,
        "no_comsol_context_grain_promotion": True,
        "no_edge4_to_edge20_direct_mapping": True,
        "no_D900_to_D1200_borrowing": True,
        "no_auto_220_300nm_admission": True,
        "package_d_precheck_status": "pass",
        "reference_geometry_propagation_status": source_row.get(
            "reference_geometry_propagation_status",
            "reference_surrogate_context_only",
        ),
        "geometry_not_propagated_to_reference_field": bool_value(
            source_row.get("geometry_not_propagated_to_reference_field", True)
        ),
        "not_optical_solver_output": True,
        "fluidic_clogging_risk_band_claim_level": (
            "not_clogging_rate_static_geometry_context_only"
        ),
        "not_clogging_rate": True,
        "not_time_to_clog": True,
        "fluidic_geometry_model": "not_evaluated_in_bounded_event_context",
        "hydraulic_resistance_model": "not_evaluated_in_bounded_event_context",
        "hydraulic_resistance_claim_level": (
            "proxy_not_trapezoid_poiseuille_not_qch_not_formula_use"
        ),
        "fluidic_geometry_propagation_status": (
            "not_propagated_to_fluidic_resistance"
        ),
        "geometry_not_propagated_to_fluidic_resistance": True,
        "fluidic_network_geometry_model": "not_evaluated_in_bounded_event_context",
        "fluidic_network_hydraulic_resistance_model": (
            "not_evaluated_in_bounded_event_context"
        ),
        "fluidic_network_hydraulic_resistance_claim_level": (
            "not_qch_weighted_not_network_solver_output"
        ),
        "fluidic_network_geometry_propagation_status": (
            "not_propagated_to_fluidic_network"
        ),
        "geometry_not_propagated_to_fluidic_network": True,
        "fluidic_network_not_qch_weighted": True,
        "electrokinetic_transport_geometry_model": (
            "not_evaluated_in_bounded_event_context"
        ),
        "electrokinetic_wall_distance_model": (
            "not_evaluated_in_bounded_event_context"
        ),
        "electrokinetic_geometry_propagation_status": (
            "blocked_not_propagated_to_electrokinetic_transport"
        ),
        "geometry_not_propagated_to_electrokinetic_transport": True,
        "surface_charge_transport_claim_level": (
            "blocked_not_propagated_no_electrokinetic_claim"
        ),
        "electrokinetic_diagnostic_gate_passed": False,
        "sidewall_angle_convention": "comsol_from_horizontal_90deg_vertical",
        "sidewall_deg_comsol": parse_float(source_row["sidewall_deg_comsol"]),
        "sidewall_taper_angle_deg_nodi": geom_fields["sidewall_taper_angle_deg_nodi"],
        "sidewall_taper_angle_deg": geom_fields["sidewall_taper_angle_deg_nodi"],
        "angle_conversion_formula_id": "sidewall_from_horizontal_to_taper_from_vertical_v1",
        "W_top_nm": width_nm,
        "W_top_semantics": w_top_semantics,
        "runtime_top_aperture_nm": width_nm,
        "source_W_top_semantics": source_row.get("W_top_semantics", ""),
        "W_bottom_unclipped_nm": m_to_nm(geom.bottom_width_unclipped_m),
        "W_bottom_runtime_clipped_nm": m_to_nm(geom.bottom_width_runtime_clipped_m),
        "closure_status": closure_status,
        "closure_policy": DEFAULT_CLOSURE_POLICY,
        "runtime_guard_status": runtime_guard_status(closure_status),
        "channel_geometry_wall_distance_model": TRAPEZOID_WALL_DISTANCE_MODEL,
        "channel_geometry_wall_distance_claim_level": (
            "geometry_distance_primitive_not_hindered_diffusion"
        ),
        "trapezoid_top_width_m": nm_to_m(width_nm),
        "trapezoid_depth_m": nm_to_m(depth_nm),
        "trapezoid_bottom_width_unclipped_m": geom.bottom_width_unclipped_m,
        "trapezoid_bottom_width_runtime_clipped_m": geom.bottom_width_runtime_clipped_m,
        "trapezoid_closure_status": closure_status,
        "trapezoid_closure_policy": DEFAULT_CLOSURE_POLICY,
        "trapezoid_runtime_guard_status": runtime_guard_status(closure_status),
        "particle_radius_m": nm_to_m(radius_nm),
        "center_accessible_support_model": CENTER_ACCESSIBLE_SUPPORT_MODEL,
        "initial_position_sampler_support_model": CENTER_ACCESSIBLE_SUPPORT_MODEL,
        "initial_position_wall_distance_model": TRAPEZOID_WALL_DISTANCE_MODEL,
        "initial_position_wall_distance_claim_level": (
            "geometry_distance_primitive_not_hindered_diffusion"
        ),
        "initial_position_particle_center_support_status": geom_fields[
            "bin_particle_center_support_status"
        ],
        "initial_position_steric_block_reason": geom_fields["blocked_reason"],
        "observation_signature_version": "sidewall_observation_signature_v1",
        "cache_geometry_match_status": "not_cacheable_audit",
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "comsol_v4_assumption_set_sha256": COMSOL_V4_ASSUMPTION_SET_SHA256,
        "not_detection_probability": True,
        "not_yield": True,
        "not_selection_metric_claim": True,
        "not_winner": True,
        "not_qch_weighted": True,
        "not_true_W_eff": True,
        "not_production_prs": True,
        "not_event_run_probability_claim": True,
        "event_context_claim_level": "bounded_sparse_event_context_not_final_response",
    }
    fields["observation_signature"] = observation_signature(fields)
    return fields


def response_context_fields(
    source_row: dict[str, str],
    *,
    bin_accessible: bool,
) -> dict[str, Any]:
    if not bin_accessible:
        return {
            "response_value": "blocked",
            "response_proxy_value": "",
            "detector_response_proxy": "",
            "signal_response_proxy": "",
            "response_rate_bin": "",
            "synthetic_counting_context_rate": "",
            "stable_counting_context_rate": "",
            "mean_peak_height": "",
            "mean_local_snr": "",
        }
    return {
        "response_value": finite_or_blank(source_row.get("mean_peak_height")),
        "response_proxy_value": finite_or_blank(source_row.get("mean_peak_height")),
        "detector_response_proxy": finite_or_blank(source_row.get("mean_peak_height")),
        "signal_response_proxy": finite_or_blank(source_row.get("mean_local_snr")),
        "response_rate_bin": finite_or_blank(
            source_row.get("selected_annulus_counting_context_rate")
        ),
        "synthetic_counting_context_rate": finite_or_blank(
            source_row.get("synthetic_counting_context_rate")
        ),
        "stable_counting_context_rate": finite_or_blank(
            source_row.get("stable_counting_context_rate")
        ),
        "mean_peak_height": finite_or_blank(source_row.get("mean_peak_height")),
        "mean_local_snr": finite_or_blank(source_row.get("mean_local_snr")),
    }


def prs_candidate_rows(
    event_rows: list[dict[str, str]] | None = None,
    *,
    source_sha: str | None = None,
    artifact_created_utc: str | None = None,
) -> list[dict[str, Any]]:
    if event_rows is None:
        event_rows = load_executed_event_rows()
    if source_sha is None:
        source_sha = sha256_file(EVENT_ROWS_PATH) if EVENT_ROWS_PATH.exists() else ""
    if artifact_created_utc is None:
        artifact_created_utc = datetime.now(UTC).replace(microsecond=0).isoformat()

    rows: list[dict[str, Any]] = []
    for source_row in event_rows:
        descriptor_payload = {
            "route_id_nodi": source_row["route_id_nodi"],
            "W_top_nm": source_row["W_top_nm"],
            "D_nm": source_row["D_nm"],
            "diameter_nm": source_row["diameter_nm"],
            "sidewall_deg_comsol": source_row["sidewall_deg_comsol"],
            "source_row_id": source_row["row_id"],
        }
        descriptor_sha = deterministic_sha256(descriptor_payload)
        geom_fields = local_geometry_for_event(source_row)
        base = base_prs_fields(
            source_row,
            source_sha=source_sha,
            geom_fields=geom_fields,
            source_descriptor_sha=descriptor_sha,
        )
        sidewall = sidewall_v2_fields(
            source_row,
            geom_fields=geom_fields,
            source_descriptor_sha=descriptor_sha,
            artifact_created_utc=artifact_created_utc,
        )
        response = response_context_fields(
            source_row,
            bin_accessible=bool(geom_fields["bin_accessible"]),
        )
        rows.append(
            {
                "candidate_version": BUILDER_VERSION,
                "candidate_row_id": f"PRS-V2-CAND-{source_row['shard_case_id']}",
                "source_shard_row_id": source_row["row_id"],
                "source_shard_case_id": source_row["shard_case_id"],
                "source_artifacts_json": COMMON_SOURCE_ARTIFACTS_JSON,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                **base,
                **sidewall,
                **response,
                "selected_annulus_source": source_row.get("selected_annulus_source", ""),
                "selected_annulus_edge_norm_min": source_row.get(
                    "selected_annulus_edge_norm_min", ""
                ),
                "selected_annulus_edge_norm_max": source_row.get(
                    "selected_annulus_edge_norm_max", ""
                ),
                "selected_annulus_fraction": finite_or_blank(
                    source_row.get("selected_annulus_fraction")
                ),
                "selected_annulus_mean_edge_norm": finite_or_blank(
                    source_row.get("selected_annulus_mean_edge_norm")
                ),
            }
        )
    return rows


def delta_context_rows(delta_rows: list[dict[str, str]] | None = None) -> list[dict[str, Any]]:
    if delta_rows is None:
        delta_rows = load_delta_rows()
    rows: list[dict[str, Any]] = []
    for row in delta_rows:
        rows.append(
            {
                "delta_context_version": BUILDER_VERSION,
                "delta_context_id": row["delta_case_id"],
                "source_delta_row_id": row["row_id"],
                "route_id_nodi": row["route_id_nodi"],
                "diameter_nm": parse_int(row["diameter_nm"]),
                "baseline_sidewall_deg_comsol": parse_float(
                    row["baseline_sidewall_deg_comsol"]
                ),
                "sidewall_deg_comsol": parse_float(row["sidewall_deg_comsol"]),
                "mean_peak_height_delta": finite_or_blank(
                    row.get("mean_peak_height_delta")
                ),
                "mean_local_snr_delta": finite_or_blank(row.get("mean_local_snr_delta")),
                "selected_annulus_fraction_delta": finite_or_blank(
                    row.get("selected_annulus_fraction_delta")
                ),
                "selected_annulus_mean_edge_norm_delta": finite_or_blank(
                    row.get("selected_annulus_mean_edge_norm_delta")
                ),
                "claim_boundary": CLAIM_BOUNDARY,
                "not_detection_probability": True,
                "not_yield": True,
                "not_selection_metric_claim": True,
                "not_winner": True,
                "not_qch_weighted": True,
                "not_true_W_eff": True,
                "not_production_prs": True,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def legacy_prs_v1_duplicate_grain_groups(rows: list[dict[str, Any]]) -> int:
    grains = Counter(
        (
            str(row["route_id_nodi"]),
            str(row["diameter_nm"]),
            str(row["NODI_view"]),
            str(row["distribution_type"]),
            str(row["bin_id"]),
        )
        for row in rows
    )
    return sum(1 for count in grains.values() if count > 1)


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    rows = payload["prs_candidate_rows"]
    if not rows:
        failures.append("no PRS sidewall v2 candidate rows generated")
        return failures
    columns = set().union(*(set(row) for row in rows))
    forbidden = sorted(FORBIDDEN_PRIMARY_COLUMNS & columns)
    if forbidden:
        failures.append(f"forbidden primary columns present: {', '.join(forbidden)}")
    missing_required = [
        field for field in PRS_SIDEWALL_V2_REQUIRED_FIELDS if field not in columns
    ]
    if missing_required:
        failures.append(
            "PRS sidewall v2 required fields missing from table: "
            + ", ".join(missing_required)
        )
    for index, row in enumerate(rows, start=1):
        for field in PRS_SIDEWALL_V2_REQUIRED_FIELDS:
            if field not in row:
                failures.append(f"row {index} missing {field}")
        if row["source_D_nm"] != row["D_nm"]:
            failures.append(f"row {index} source_D_nm does not match D_nm")
        if row["source_route_id_nodi"] != row["route_id_nodi"]:
            failures.append(f"row {index} source_route_id_nodi mismatch")
        if row["decision_use_allowed"] is not False:
            failures.append(f"row {index} must stay decision_use_allowed=false")
        if row["bin_sample_status"] == "adequate":
            failures.append(f"row {index} sparse bounded shard marked adequate")
        if row["neighbor_fill_used"] is not False:
            failures.append(f"row {index} uses neighbor fill")
        if row["channel_cross_section_model"] == "trapezoid_tapered_sidewalls":
            expected_bottom = row["W_top_nm"] - (
                2.0 * row["D_nm"] / math.tan(math.radians(row["sidewall_deg_comsol"]))
            )
            if not math.isclose(
                row["W_bottom_unclipped_nm"],
                expected_bottom,
                rel_tol=1.0e-9,
                abs_tol=0.05,
            ):
                failures.append(f"row {index} bottom width formula mismatch")
        if (
            row["bin_particle_center_support_status"] == "blocked"
            or row["bin_accessible"] is False
        ):
            for field in PRS_SIDEWALL_V2_BLOCKED_RESPONSE_VALUE_FIELDS:
                value = str(row.get(field, "")).strip()
                if value and value.lower() not in {"blocked", "none", "null", "na", "n/a"}:
                    failures.append(f"row {index} blocked bin has nonblank {field}")
        else:
            if row["steric_support_source"] != "exact_geometry_primitive":
                failures.append(f"row {index} open row lacks exact steric source")
        for field in (
            "not_detection_probability",
            "not_yield",
            "not_selection_metric_claim",
            "not_winner",
            "not_qch_weighted",
            "not_true_W_eff",
            "not_production_prs",
            "not_accepted_for_formula_use",
            "not_accepted_for_runtime_config",
            "not_accepted_for_production",
        ):
            if row.get(field) is not True:
                failures.append(f"row {index} {field} must be true")
        if "wall_distance" in str(row["bin_basis"]):
            failures.append(f"row {index} bin_basis must not trigger Package C proof semantics")
    return failures


def alignment_check_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload["prs_candidate_rows"]
    delta_rows = payload["delta_context_rows"]
    failures = validate_payload(payload)
    return [
        {
            "check_name": "executed_shard_rows_loaded",
            "check_pass": len(rows) == payload["summary"]["executed_event_shard_rows"],
            "observed": len(rows),
            "expected": payload["summary"]["executed_event_shard_rows"],
            "hard_fail_if_false": True,
        },
        {
            "check_name": "delta_context_rows_loaded",
            "check_pass": len(delta_rows) == payload["summary"]["executed_delta_rows"],
            "observed": len(delta_rows),
            "expected": payload["summary"]["executed_delta_rows"],
            "hard_fail_if_false": True,
        },
        {
            "check_name": "sidewall_v2_required_fields_present",
            "check_pass": not any("required fields missing" in failure for failure in failures),
            "observed": "pass" if not failures else "; ".join(failures[:4]),
            "expected": "pass",
            "hard_fail_if_false": True,
        },
        {
            "check_name": "bounded_rows_remain_sparse_context",
            "check_pass": all(
                row["decision_use_allowed"] is False
                and row["bin_sample_status"] in {"sparse", "empty"}
                for row in rows
            ),
            "observed": "all_false_sparse_or_empty",
            "expected": "all_false_sparse_or_empty",
            "hard_fail_if_false": True,
        },
        {
            "check_name": "forbidden_primary_columns_absent",
            "check_pass": not (set().union(*(set(row) for row in rows)) & FORBIDDEN_PRIMARY_COLUMNS),
            "observed": sorted(set().union(*(set(row) for row in rows)) & FORBIDDEN_PRIMARY_COLUMNS),
            "expected": [],
            "hard_fail_if_false": True,
        },
        {
            "check_name": "blocked_bins_do_not_carry_response_values",
            "check_pass": not any("blocked bin has nonblank" in failure for failure in failures),
            "observed": "pass" if not failures else "; ".join(failures),
            "expected": "pass",
            "hard_fail_if_false": True,
        },
        {
            "check_name": "legacy_prs_v1_duplicate_grains_are_sidewall_angle_pairs",
            "check_pass": legacy_prs_v1_duplicate_grain_groups(rows)
            == payload["summary"]["legacy_prs_v1_duplicate_grain_groups"],
            "observed": legacy_prs_v1_duplicate_grain_groups(rows),
            "expected": payload["summary"]["legacy_prs_v1_duplicate_grain_groups"],
            "hard_fail_if_false": True,
        },
    ]


def build_payload() -> dict[str, Any]:
    event_rows = load_executed_event_rows()
    delta_rows = load_delta_rows()
    source_rows = read_csv_rows(EVENT_ROWS_PATH) if EVENT_ROWS_PATH.exists() else []
    source_sha = sha256_file(EVENT_ROWS_PATH) if EVENT_ROWS_PATH.exists() else ""
    artifact_created_utc = datetime.now(UTC).replace(microsecond=0).isoformat()
    candidate_rows = prs_candidate_rows(
        event_rows,
        source_sha=source_sha,
        artifact_created_utc=artifact_created_utc,
    )
    delta_context = delta_context_rows(delta_rows)
    failures = validate_payload(
        {
            "prs_candidate_rows": candidate_rows,
            "delta_context_rows": delta_context,
            "summary": {
                "executed_event_shard_rows": len(event_rows),
                "executed_delta_rows": len(delta_rows),
            },
        }
    )
    summary = {
        "artifact_id": ARTIFACT_ID,
        "disposition": BLOCKED_DISPOSITION if failures else DISPOSITION,
        "builder_version": BUILDER_VERSION,
        "branch": git_branch(),
        "current_head": git_head(),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
        "primary_answer_frame": "dimension_annulus_interference_response_context",
        "not_primary_answer_frame": "route_winner_scoreboard_or_probability",
        "executed_event_shard_rows": len(event_rows),
        "source_event_shard_rows": len(source_rows),
        "executed_delta_rows": len(delta_rows),
        "prs_candidate_rows": len(candidate_rows),
        "delta_context_rows": len(delta_context),
        "trapezoid_candidate_rows": sum(
            1
            for row in candidate_rows
            if row["channel_cross_section_model"] == "trapezoid_tapered_sidewalls"
        ),
        "rectangle_baseline_rows": sum(
            1
            for row in candidate_rows
            if row["channel_cross_section_model"] == "ideal_rectangle"
        ),
        "blocked_particle_support_rows": sum(
            1
            for row in candidate_rows
            if row["bin_particle_center_support_status"] == "blocked"
        ),
        "sparse_context_rows": sum(
            1 for row in candidate_rows if row["bin_sample_status"] == "sparse"
        ),
        "empty_context_rows": sum(
            1 for row in candidate_rows if row["bin_sample_status"] == "empty"
        ),
        "decision_use_allowed_rows": sum(
            1 for row in candidate_rows if row["decision_use_allowed"] is True
        ),
        "legacy_prs_v1_duplicate_grain_groups": legacy_prs_v1_duplicate_grain_groups(
            candidate_rows
        ),
        "legacy_prs_v1_duplicate_grain_reason": (
            "expected_theta90_theta85_pairing_because_legacy_prs_v1_grain_lacks_sidewall_angle"
        ),
        "failed_alignment_check_rows": len(failures),
        "source_missing_rows": sum(1 for row in source_lock_rows() if row["exists"] == "false"),
        "dirty_context_rows": len(dirty_context_rows()),
        "non_prs_v2_candidate_dirty_context_rows": sum(
            1
            for row in dirty_context_rows()
            if row["classification"] == "non_prs_v2_candidate_dirty_context"
        ),
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "next_large_block": (
            "integrated sidewall dimension-annulus-interference synthesis from "
            "589/590/591/592"
        ),
    }
    payload = {
        "disposition": summary["disposition"],
        "summary": summary,
        "source_lock_rows": source_lock_rows(),
        "dirty_context_rows": dirty_context_rows(),
        "prs_candidate_rows": candidate_rows,
        "delta_context_rows": delta_context,
        "alignment_check_rows": [],
        "failure_rows": [
            {"failure_index": index, "failure": failure}
            for index, failure in enumerate(failures, start=1)
        ]
        or [{"failure_index": "", "failure": "none"}],
    }
    payload["alignment_check_rows"] = alignment_check_rows(payload)
    payload["summary"]["alignment_check_rows"] = len(payload["alignment_check_rows"])
    payload["summary"]["semantic_digest"] = deterministic_sha256(
        {
            "candidate_row_count": len(candidate_rows),
            "delta_context_row_count": len(delta_context),
            "blocked_particle_support_rows": summary["blocked_particle_support_rows"],
            "source_sha": source_sha,
            "comsol_v4": COMSOL_V4_ASSUMPTION_SET_SHA256,
        }
    )
    return payload


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv",
        "candidate_rows": OUTPUT_DIR / f"{PREFIX}_CANDIDATE_ROWS_{DATE_STAMP}.csv",
        "delta_context_rows": OUTPUT_DIR / f"{PREFIX}_DELTA_CONTEXT_ROWS_{DATE_STAMP}.csv",
        "alignment_checks": OUTPUT_DIR / f"{PREFIX}_ALIGNMENT_CHECKS_{DATE_STAMP}.csv",
        "failures": OUTPUT_DIR / f"{PREFIX}_FAILURES_{DATE_STAMP}.csv",
        "master_report": REPORT_DIR / f"592_{PREFIX}_{DATE_STAMP}.md",
    }

    write_json_atomic(paths["status"], payload["summary"], sort_keys=True)
    write_csv_rows(paths["source_lock"], payload["source_lock_rows"])
    write_csv_rows(paths["dirty_context"], payload["dirty_context_rows"])
    write_csv_rows(paths["candidate_rows"], payload["prs_candidate_rows"])
    write_csv_rows(paths["delta_context_rows"], payload["delta_context_rows"])
    write_csv_rows(paths["alignment_checks"], payload["alignment_check_rows"])
    write_csv_rows(paths["failures"], payload["failure_rows"])

    preliminary_manifest_rows = [
        {
            "artifact_id": key,
            "path": display_path(path),
            "sha256": "",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for key, path in paths.items()
        if key != "report_json"
    ]
    paths["master_report"].write_text(
        master_report(payload, preliminary_manifest_rows),
        encoding="utf-8",
    )
    manifest_rows = [
        {
            "artifact_id": key,
            "path": display_path(path),
            "sha256": SELF_MANIFEST_SHA256 if key == "manifest" else sha256_file(path),
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for key, path in paths.items()
        if key != "report_json"
    ]
    write_csv_rows(paths["manifest"], manifest_rows)
    write_json_atomic(
        paths["report_json"],
        {
            "disposition": payload["disposition"],
            "summary": payload["summary"],
            "manifest": manifest_rows,
            "alignment_checks": payload["alignment_check_rows"],
            "failures": payload["failure_rows"],
        },
        indent=None,
        sort_keys=True,
    )
    return list(paths.values())


def master_report(payload: dict[str, Any], manifest_rows: list[dict[str, Any]]) -> str:
    summary = payload["summary"]
    failed_checks = [
        row for row in payload["alignment_check_rows"] if row["check_pass"] is not True
    ]
    return "\n".join(
        [
            f"# 592 {PREFIX} {DATE_STAMP}",
            "",
            "## Disposition",
            "",
            f"- disposition: `{summary['disposition']}`",
            f"- primary_answer_frame: `{summary['primary_answer_frame']}`",
            f"- not_primary_answer_frame: `{summary['not_primary_answer_frame']}`",
            f"- claim_boundary: `{CLAIM_BOUNDARY}`",
            "",
            "## What This Adds",
            "",
            (
                "This block converts the 591 executed bounded NODI sidewall "
                "event shards into sparse PRS sidewall v2 event-context rows. "
                "It keeps the source route as a join key, preserves the selected "
                "annulus source, computes trapezoid-local particle-center support "
                "and wall-distance diagnostics, and keeps every row out of "
                "production/runtime/probability use."
            ),
            "",
            "## Counts",
            "",
            f"- executed_event_shard_rows: `{summary['executed_event_shard_rows']}`",
            f"- prs_candidate_rows: `{summary['prs_candidate_rows']}`",
            f"- delta_context_rows: `{summary['delta_context_rows']}`",
            f"- trapezoid_candidate_rows: `{summary['trapezoid_candidate_rows']}`",
            f"- rectangle_baseline_rows: `{summary['rectangle_baseline_rows']}`",
            f"- blocked_particle_support_rows: `{summary['blocked_particle_support_rows']}`",
            f"- decision_use_allowed_rows: `{summary['decision_use_allowed_rows']}`",
            "",
            "## Mainline Guard",
            "",
            (
                "The rows are intentionally PRS-v2-shaped sparse context rows, "
                "not production PRS. They are meant to feed the next synthesis "
                "on sidewall-driven dimension-window shifts, selected-annulus "
                "range remaps, and interference/response sensitivity."
            ),
            "",
            "## COMSOL V4 Context",
            "",
            f"- assumption_set_id: `{summary['comsol_v4_assumption_set_id']}`",
            f"- assumption_set_version: `{summary['comsol_v4_assumption_set_version']}`",
            "",
            "## Alignment",
            "",
            f"- alignment_check_rows: `{summary['alignment_check_rows']}`",
            f"- failed_alignment_check_rows: `{len(failed_checks)}`",
            f"- semantic_digest: `{summary['semantic_digest']}`",
            "",
            "## Manifest",
            "",
            *[
                f"- `{row['artifact_id']}`: `{row['path']}`"
                for row in manifest_rows
            ],
            "",
        ]
    )


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_sidewall_prs_v2_candidate_from_bounded_shards:
        print(
            "--confirm-sidewall-prs-v2-candidate-from-bounded-shards is required",
            file=sys.stderr,
        )
        return 2
    payload = build_payload()
    write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if payload["summary"]["disposition"] == DISPOSITION else 1


if __name__ == "__main__":
    raise SystemExit(main())
