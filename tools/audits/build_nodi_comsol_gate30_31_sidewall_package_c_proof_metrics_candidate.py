#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random
import subprocess
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.cross_section_geometry import (  # noqa: E402
    TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION,
    TrapezoidCrossSection,
    comsol_sidewall_deg_to_nodi_taper_deg,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)
from tools.audits.build_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight import (  # noqa: E402
    REQUIRED_PROOF_CONTRACT_FIELDS,
)


DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

DISPOSITION = (
    "NODI_GATE30_31_SIDEWALL_PACKAGE_C_PROOF_METRICS_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
ARTIFACT_ID = "GATE30_31_PACKAGE_C_REFLECTION_PROOF_METRICS_CANDIDATE_20260630"
METRIC_SCHEMA_VERSION = "package_c_reflection_metric_candidate_v1"
CLAIM_BOUNDARY = (
    "candidate_only_finite_step_reflection_surrogate_not_package_c_proof_registered"
)
PENDING_REVIEWED_COMMIT_SHA = ""
PENDING_EXTERNAL_REVIEW_SHA = ""
ALLOWED_USE = (
    "Package C proof-metrics candidate;external proof-registration review support;"
    "fail-closed manifest candidate;no-proof-registration"
)
BLOCKED_USE = (
    "Package C proof/pass registration;package_C_validation_status pass;runtime configuration;"
    "sidewall PRS/EAS numeric output;NODI runtime recomputation;COMSOL launch;.mph load;"
    "validated Brownian solver output;validated hindered diffusion;trapezoid Poiseuille solver output;"
    "fixed-pressure q_ch output;flux-weighted sampling;electrokinetic grid output;optical solver output;"
    "true W_eff;reference strength claim;detector response claim;sidewall scattering claim;"
    "route_score;winner;JRC;q_ch weighting;yield;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;production ingestion"
)

TOP_WIDTH_NM = 500.0
SIDEWALL_ANGLE_GRID_DEG_COMSOL = (90.0, 89.0, 87.0, 85.0, 83.0, 80.0, 70.0)
DEPTH_GRID_NM = (900.0, 1200.0)
PARTICLE_RADIUS_GRID_NM = (20.0, 30.0, 50.0, 75.0, 110.0, 150.0)
DT_GRID_S = (5.0e-5, 2.5e-5, 1.25e-5)
DIFFUSION_COEFFICIENT_GRID_M2_S = (4.0e-12,)
RNG_SEEDS = (31031, 31032, 31033)
TOLERANCE_M = 1.0e-18
MAX_REFLECTION_ITERATIONS = 64
BOUNDARY_ATOM_EPS_M = 1.0e-12
BOUNDARY_ATOM_THRESHOLD = 0.005
EQUILIBRIUM_DISTANCE_THRESHOLD = 0.06
CORNER_BIAS_THRESHOLD = 0.12
RECTANGLE_LIMIT_TOLERANCE = 1.0e-18
ONE_WALL_LIMIT_TOLERANCE = 1.0e-18
SAMPLES_PER_SCENARIO = 768

GATE29_STATUS = OUTPUT_DIR / "NODI_COMSOL_GATE29_SIDEWALL_STATUS_20260630.json"
GATE29_REPORT = OUTPUT_DIR / "NODI_COMSOL_GATE29_SIDEWALL_REPORT_20260630.json"
GATE29_SOURCE_LOCK = OUTPUT_DIR / "NODI_COMSOL_GATE29_SIDEWALL_SOURCE_LOCK_20260630.csv"
GATE29_FIREWALL = OUTPUT_DIR / "NODI_COMSOL_GATE29_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv"
GATE29_REVIEW_CAPTURE = OUTPUT_DIR / "NODI_COMSOL_GATE29_SIDEWALL_EXTERNAL_REVIEW_CAPTURE_20260630.md"
GATE27_PROOF_CONTRACT = OUTPUT_DIR / "NODI_COMSOL_GATE27_SIDEWALL_PROOF_ARTIFACT_CONTRACT_20260630.csv"

SOURCE_FILES = {
    "gate29_status": GATE29_STATUS,
    "gate29_report": GATE29_REPORT,
    "gate29_source_lock": GATE29_SOURCE_LOCK,
    "gate29_no_proof_firewall": GATE29_FIREWALL,
    "gate29_external_review_capture": GATE29_REVIEW_CAPTURE,
    "gate27_proof_contract": GATE27_PROOF_CONTRACT,
    "cross_section_geometry": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
    "trajectory": PROJECT_ROOT / "nodi_simulator/trajectory.py",
    "next_artifacts_contract": PROJECT_ROOT / "nodi_simulator/nodi_comsol_next_artifacts.py",
    "gate30_31_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate.py",
    "gate30_31_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}

REPORTS = {
    "480": "GATE30_31A_PACKAGE_C_REFLECTION_RAW_METRICS_CANDIDATE",
    "481": "GATE30_31B_PACKAGE_C_REFLECTION_SUMMARY_METRICS_CANDIDATE",
    "482": "GATE30_31C_PACKAGE_C_PROOF_CANDIDATE_MANIFEST",
    "483": "GATE30_31D_NO_PROOF_REGISTRATION_FIREWALL",
    "484": "GATE30_31_SIDEWALL_PACKAGE_C_PROOF_METRICS_CANDIDATE_MASTER_REPORT",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Gate30/31 Package C proof-metrics candidate artifacts."
    )
    parser.add_argument(
        "--confirm-gate30-31-package-c-proof-metrics-candidate",
        action="store_true",
    )
    return parser


def run_git(args: list[str], cwd: Path = PROJECT_ROOT) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={cwd.as_posix()}", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def safe_git_head(path: Path = PROJECT_ROOT) -> str:
    try:
        return run_git(["rev-parse", "HEAD"], cwd=path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN_COMMIT_READONLY_REFERENCE"


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def _m(value_nm: float) -> float:
    return value_nm * 1.0e-9


def _nm(value_m: float) -> float:
    return value_m * 1.0e9


def _geom(theta_deg_comsol: float, depth_nm: float) -> TrapezoidCrossSection:
    return TrapezoidCrossSection(
        top_width_m=_m(TOP_WIDTH_NM),
        depth_m=_m(depth_nm),
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(theta_deg_comsol),
    )


def _round_float(value: float, digits: int = 12) -> float:
    return round(float(value), digits)


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _histogram(values: list[float], bins: int, low: float, high: float) -> list[float]:
    counts = [0] * bins
    if not values:
        return [0.0] * bins
    width = (high - low) / bins
    for value in values:
        index = int((min(max(value, low), math.nextafter(high, low)) - low) / width)
        counts[min(max(index, 0), bins - 1)] += 1
    total = float(len(values))
    return [count / total for count in counts]


def _hist_l1(a: list[float], b: list[float]) -> float:
    return sum(abs(x - y) for x, y in zip(a, b))


def _u_accessible_cdf(
    geom: TrapezoidCrossSection,
    u_m: float,
    radius_m: float,
) -> float:
    bounds = geom.center_accessible_u_bounds_m(radius_m)
    if bounds is None:
        return 0.0
    u_low, u_high = bounds
    u = min(max(u_m, u_low), u_high)
    side_exclusion_m = radius_m * math.sqrt(1.0 + geom.k_taper**2)
    available_top_m = geom.top_width_m - 2.0 * side_exclusion_m
    if geom.k_taper <= 0.0:
        return (u - u_low) / (u_high - u_low)
    area_to_u = available_top_m * (u - u_low) - geom.k_taper * (u**2 - u_low**2)
    total_area = geom.center_accessible_area_m2(radius_m)
    return min(max(area_to_u / total_area, 0.0), 1.0) if total_area > 0.0 else 0.0


def _x_local_norm(
    geom: TrapezoidCrossSection,
    x_m: float,
    u_m: float,
    radius_m: float,
) -> float:
    left, right = geom.center_accessible_x_bounds_at_depth_m(u_m, radius_m)
    half_width = 0.5 * (right - left)
    if half_width <= 0.0:
        return 0.0
    return min(max(x_m / half_width, -1.0), 1.0)


def _reflect_diffusive_steps(
    geom: TrapezoidCrossSection,
    radius_m: float,
    *,
    dt_s: float,
    diffusion_m2_s: float,
    seed: int,
    n_samples: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    sigma_m = math.sqrt(2.0 * diffusion_m2_s * dt_s)
    support_violations = 0
    boundary_atoms = 0
    corner_active_set_count = 0
    sidewall_hit_count = 0
    reflected_count = 0
    iteration_counts: list[int] = []
    reflection_displacements_nm: list[float] = []
    wall_gaps_nm: list[float] = []
    x_norms: list[float] = []
    u_cdfs: list[float] = []
    left_count = 0
    right_count = 0
    nearest_wall_counts = {"top": 0, "bottom": 0, "left_side": 0, "right_side": 0}

    for _ in range(n_samples):
        x0, u0 = geom.sample_particle_center_uniform(rng.random(), rng.random(), radius_m)
        trial_x = x0 + rng.gauss(0.0, sigma_m)
        trial_u = u0 + rng.gauss(0.0, sigma_m)
        result = geom.reflect_particle_center_step_with_diagnostics(
            trial_x,
            trial_u,
            radius_m,
            max_iterations=MAX_REFLECTION_ITERATIONS,
            tolerance_m=TOLERANCE_M,
        )
        if not geom.contains_particle_center(
            result.x_m,
            result.u_m,
            radius_m,
            tolerance_m=1.0e-15,
        ):
            support_violations += 1
        diagnostics = geom.particle_wall_gap_diagnostics_m(
            result.x_m,
            result.u_m,
            radius_m,
        )
        min_gap_m = float(diagnostics["surface_gap_for_particle_m"])
        if abs(min_gap_m) <= BOUNDARY_ATOM_EPS_M:
            boundary_atoms += 1
        active_set = set(result.active_wall_ids)
        if len(active_set) >= 2:
            corner_active_set_count += 1
        if active_set & {"left_side", "right_side"}:
            sidewall_hit_count += 1
        if result.iteration_count > 0:
            reflected_count += 1
        iteration_counts.append(result.iteration_count)
        reflection_displacements_nm.append(_nm(result.reflection_displacement_m))
        wall_gaps_nm.append(_nm(min_gap_m))
        x_norm = _x_local_norm(geom, result.x_m, result.u_m, radius_m)
        x_norms.append(x_norm)
        u_cdfs.append(_u_accessible_cdf(geom, result.u_m, radius_m))
        if result.x_m < 0.0:
            left_count += 1
        elif result.x_m > 0.0:
            right_count += 1
        nearest_wall_counts[str(diagnostics["nearest_wall_id"])] += 1

    x_mean = sum(x_norms) / len(x_norms)
    x_var = sum((value - x_mean) ** 2 for value in x_norms) / len(x_norms)
    u_mean = sum(u_cdfs) / len(u_cdfs)
    u_var = sum((value - u_mean) ** 2 for value in u_cdfs) / len(u_cdfs)
    equilibrium_distance = max(abs(x_mean), abs(x_var - 1.0 / 3.0), abs(u_mean - 0.5), abs(u_var - 1.0 / 12.0))
    total_lr = max(left_count + right_count, 1)
    left_right_balance_abs = abs(left_count - right_count) / total_lr

    return {
        "dt_s": dt_s,
        "diffusion_coefficient_m2_s": diffusion_m2_s,
        "rng_seed": seed,
        "n_samples": n_samples,
        "brownian_rms_step_nm": _round_float(_nm(sigma_m), 9),
        "support_violation_count": support_violations,
        "boundary_atom_fraction": _round_float(boundary_atoms / n_samples, 9),
        "corner_active_set_rate": _round_float(corner_active_set_count / n_samples, 9),
        "sidewall_hit_rate": _round_float(sidewall_hit_count / n_samples, 9),
        "reflected_step_rate": _round_float(reflected_count / n_samples, 9),
        "reflection_iteration_count_p50": _round_float(_quantile(iteration_counts, 0.50), 9),
        "reflection_iteration_count_p99": _round_float(_quantile(iteration_counts, 0.99), 9),
        "reflection_displacement_p99_nm": _round_float(_quantile(reflection_displacements_nm, 0.99), 9),
        "wall_gap_p01_nm": _round_float(_quantile(wall_gaps_nm, 0.01), 9),
        "wall_gap_p50_nm": _round_float(_quantile(wall_gaps_nm, 0.50), 9),
        "x_local_norm_histogram": _histogram(x_norms, 10, -1.0, 1.0),
        "u_accessible_cdf_histogram": _histogram(u_cdfs, 10, 0.0, 1.0),
        "x_local_norm_mean": _round_float(x_mean, 9),
        "x_local_norm_variance_delta": _round_float(abs(x_var - 1.0 / 3.0), 9),
        "u_accessible_cdf_mean_delta": _round_float(abs(u_mean - 0.5), 9),
        "u_accessible_cdf_variance_delta": _round_float(abs(u_var - 1.0 / 12.0), 9),
        "equilibrium_uniformity_distance": _round_float(equilibrium_distance, 9),
        "left_right_balance_abs": _round_float(left_right_balance_abs, 9),
        "nearest_wall_counts": nearest_wall_counts,
    }


def _scenario_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for theta in SIDEWALL_ANGLE_GRID_DEG_COMSOL:
        for depth_nm in DEPTH_GRID_NM:
            geom = _geom(theta, depth_nm)
            for radius_nm in PARTICLE_RADIUS_GRID_NM:
                radius_m = _m(radius_nm)
                area_m2 = geom.center_accessible_area_m2(radius_m)
                bounds = geom.center_accessible_u_bounds_m(radius_m)
                runtime_status = "candidate_open"
                if geom.closure_status == "geometry_closed":
                    runtime_status = "blocked_geometry_closed"
                elif geom.closure_status == "near_closed":
                    runtime_status = "blocked_near_closed_resource_guard"
                elif area_m2 <= 0.0 or bounds is None:
                    runtime_status = "blocked_zero_center_accessible_support"

                base_row: dict[str, Any] = {
                    "scenario_id": f"theta{theta:g}_D{depth_nm:g}_r{radius_nm:g}",
                    "sidewall_deg_comsol": theta,
                    "sidewall_taper_angle_deg_nodi": _round_float(
                        comsol_sidewall_deg_to_nodi_taper_deg(theta), 9
                    ),
                    "depth_nm": depth_nm,
                    "particle_radius_nm": radius_nm,
                    "top_width_nm": TOP_WIDTH_NM,
                    "bottom_width_unclipped_nm": _round_float(
                        _nm(geom.bottom_width_unclipped_m), 9
                    ),
                    "bottom_width_runtime_clipped_nm": _round_float(
                        _nm(geom.bottom_width_runtime_clipped_m), 9
                    ),
                    "closure_status": geom.closure_status,
                    "runtime_candidate_status": runtime_status,
                    "center_accessible_area_nm2": _round_float(area_m2 * 1.0e18, 6),
                    "cross_section_geometry_version": TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION,
                }
                if runtime_status != "candidate_open":
                    row = dict(base_row)
                    row.update(
                        {
                            "dt_s": "",
                            "diffusion_coefficient_m2_s": "",
                            "rng_seed": "",
                            "n_samples": "0",
                            "support_violation_count": "0",
                            "boundary_atom_fraction": "",
                            "corner_active_set_rate": "",
                            "sidewall_hit_rate": "",
                            "reflected_step_rate": "",
                            "reflection_iteration_count_p99": "",
                            "wall_gap_p01_nm": "",
                            "equilibrium_uniformity_distance": "",
                            "left_right_balance_abs": "",
                        }
                    )
                    rows.append(row)
                    continue
                for dt_s in DT_GRID_S:
                    metrics = _reflect_diffusive_steps(
                        geom,
                        radius_m,
                        dt_s=dt_s,
                        diffusion_m2_s=DIFFUSION_COEFFICIENT_GRID_M2_S[0],
                        seed=RNG_SEEDS[0] + int(theta * 10.0) + int(depth_nm) + int(radius_nm),
                        n_samples=SAMPLES_PER_SCENARIO,
                    )
                    row = dict(base_row)
                    row.update(metrics)
                    rows.append(row)
    return rows


def _dt_halving_rows(open_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_scenario: dict[str, list[dict[str, Any]]] = {}
    for row in open_rows:
        by_scenario.setdefault(str(row["scenario_id"]), []).append(row)
    for scenario_id, scenario_rows in sorted(by_scenario.items()):
        scenario_rows = sorted(scenario_rows, key=lambda item: float(item["dt_s"]))
        if len(scenario_rows) != len(DT_GRID_S):
            continue
        distances = []
        for left, right in zip(scenario_rows, scenario_rows[1:]):
            distances.append(
                max(
                    _hist_l1(left["x_local_norm_histogram"], right["x_local_norm_histogram"]),
                    _hist_l1(left["u_accessible_cdf_histogram"], right["u_accessible_cdf_histogram"]),
                    abs(float(left["wall_gap_p50_nm"]) - float(right["wall_gap_p50_nm"])) / 100.0,
                )
            )
        rows.append(
            {
                "scenario_id": scenario_id,
                "dt_grid_s": json.dumps(DT_GRID_S),
                "dt_halving_max_distribution_delta": _round_float(max(distances), 9),
                "dt_halving_status": "candidate_pass"
                if max(distances) <= 0.75
                else "candidate_review_required",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def _one_wall_limit_metrics() -> dict[str, Any]:
    geom = _geom(85.0, 900.0)
    radius_m = _m(60.0)
    boundary_u_m = _m(240.0)
    _, boundary_x_m = geom.center_accessible_x_bounds_at_depth_m(boundary_u_m, radius_m)
    normal_x, normal_u = geom.wall_inward_unit_normals()["right_side"]
    max_error_m = 0.0
    for overshoot_nm in (6.0, 12.0, 24.0, 36.0):
        overshoot_m = _m(overshoot_nm)
        trial_x_m = boundary_x_m - overshoot_m * normal_x
        trial_u_m = boundary_u_m - overshoot_m * normal_u
        result = geom.reflect_particle_center_step_with_diagnostics(
            trial_x_m,
            trial_u_m,
            radius_m,
        )
        expected_x_m = trial_x_m + 2.0 * overshoot_m * normal_x
        expected_u_m = trial_u_m + 2.0 * overshoot_m * normal_u
        max_error_m = max(
            max_error_m,
            abs(result.x_m - expected_x_m),
            abs(result.u_m - expected_u_m),
        )
    return {
        "one_wall_limit_max_error_m": max_error_m,
        "one_wall_limit_status": "candidate_pass"
        if max_error_m <= ONE_WALL_LIMIT_TOLERANCE
        else "candidate_review_required",
    }


def _rectangle_limit_metrics() -> dict[str, Any]:
    geom = _geom(90.0, 900.0)
    max_area_delta_m2 = 0.0
    max_reflection_error_m = 0.0
    for radius_nm in PARTICLE_RADIUS_GRID_NM:
        radius_m = _m(radius_nm)
        expected_area_m2 = max(geom.top_width_m - 2.0 * radius_m, 0.0) * max(
            geom.depth_m - 2.0 * radius_m,
            0.0,
        )
        max_area_delta_m2 = max(
            max_area_delta_m2,
            abs(geom.center_accessible_area_m2(radius_m) - expected_area_m2),
        )
        x_right = geom.top_width_m / 2.0 - radius_m
        trial_x = x_right + _m(12.0)
        trial_u = geom.depth_m / 2.0
        result = geom.reflect_particle_center_step_with_diagnostics(trial_x, trial_u, radius_m)
        expected_x = x_right - _m(12.0)
        max_reflection_error_m = max(max_reflection_error_m, abs(result.x_m - expected_x))
    max_delta = max(max_area_delta_m2, max_reflection_error_m)
    return {
        "rectangle_limit_max_delta": max_delta,
        "rectangle_limit_status": "candidate_pass"
        if max_delta <= RECTANGLE_LIMIT_TOLERANCE
        else "candidate_review_required",
    }


def _mutation_metrics() -> dict[str, Any]:
    radius_m = _m(60.0)
    bottom_values = []
    area_values = []
    status_values = []
    for theta in SIDEWALL_ANGLE_GRID_DEG_COMSOL:
        for depth_nm in DEPTH_GRID_NM:
            geom = _geom(theta, depth_nm)
            bottom_values.append(round(_nm(geom.bottom_width_unclipped_m), 6))
            area_values.append(round(geom.center_accessible_area_m2(radius_m) * 1.0e18, 6))
            status_values.append(geom.closure_status)
    return {
        "angle_depth_mutation_unique_bottom_widths": len(set(bottom_values)),
        "angle_depth_mutation_unique_accessible_areas": len(set(area_values)),
        "angle_depth_mutation_closure_statuses": sorted(set(status_values)),
        "angle_depth_mutation_status": "candidate_pass"
        if len(set(bottom_values)) > 3 and len(set(area_values)) > 3
        else "candidate_review_required",
    }


def _corner_probe_metrics() -> dict[str, Any]:
    geom = _geom(85.0, 900.0)
    radius_m = _m(60.0)
    bottom_u_m = geom.depth_m - radius_m
    _, right_x_m = geom.center_accessible_x_bounds_at_depth_m(bottom_u_m, radius_m)
    iteration_counts: list[int] = []
    failures = 0
    for overshoot_nm in (8.0, 16.0, 24.0, 32.0, 40.0, 48.0):
        result = geom.reflect_particle_center_step_with_diagnostics(
            right_x_m + _m(overshoot_nm),
            bottom_u_m + _m(overshoot_nm),
            radius_m,
        )
        iteration_counts.append(result.iteration_count)
        if not geom.contains_particle_center(result.x_m, result.u_m, radius_m):
            failures += 1
    p99_iterations = _quantile(iteration_counts, 0.99)
    return {
        "corner_active_set_probe_count": len(iteration_counts),
        "corner_active_set_failure_count": failures,
        "corner_active_set_iteration_p99": _round_float(p99_iterations, 9),
        "corner_active_set_status": "candidate_pass"
        if failures == 0 and p99_iterations <= MAX_REFLECTION_ITERATIONS
        else "candidate_review_required",
    }


def _environment_lock() -> dict[str, str]:
    return {
        "python_version": sys.version.replace("\n", " "),
        "platform": sys.platform,
        "git_head": safe_git_head(),
        "metric_schema_version": METRIC_SCHEMA_VERSION,
    }


def _source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for label, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_label": label,
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "exists": bool_text(exists),
                "sha256": sha256_file(path) if exists else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def _parameter_matrix_rows() -> list[dict[str, str]]:
    rows = []
    for theta in SIDEWALL_ANGLE_GRID_DEG_COMSOL:
        for depth_nm in DEPTH_GRID_NM:
            for radius_nm in PARTICLE_RADIUS_GRID_NM:
                for dt_s in DT_GRID_S:
                    rows.append(
                        {
                            "sidewall_angle_deg_comsol": str(theta),
                            "sidewall_taper_angle_deg_nodi": str(
                                comsol_sidewall_deg_to_nodi_taper_deg(theta)
                            ),
                            "depth_nm": str(depth_nm),
                            "particle_radius_nm": str(radius_nm),
                            "dt_s": str(dt_s),
                            "diffusion_coefficient_m2_s": str(
                                DIFFUSION_COEFFICIENT_GRID_M2_S[0]
                            ),
                            "claim_boundary": CLAIM_BOUNDARY,
                        }
                    )
    return rows


def _seed_matrix_rows() -> list[dict[str, str]]:
    return [
        {
            "seed_id": f"G3031-SEED-{idx:03d}",
            "rng_seed": str(seed),
            "use": "deterministic proof-metrics candidate sampling",
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for idx, seed in enumerate(RNG_SEEDS, start=1)
    ]


def _firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_status": "PASS_GATE30_31_CANDIDATE_GENERATED_NO_PROOF_REGISTRATION",
            "package_c_proof_artifact_registered": "false",
            "package_c_validation_status_pass_authorized": "false",
            "proof_registry_update_authorized": "false",
            "runtime_configuration_authorized": "false",
            "sidewall_prs_eas_numeric_output_authorized": "false",
            "nodi_runtime_recomputation_authorized": "false",
            "comsol_launch_authorized": "false",
            "mph_load_authorized": "false",
            "hindered_diffusion_claim_authorized": "false",
            "trapezoid_flow_solver_claim_authorized": "false",
            "electrokinetic_solver_claim_authorized": "false",
            "optical_solver_claim_authorized": "false",
            "validated_brownian_solver_output_authorized": "false",
            "wet_claim_authorized": "false",
            "wet_pass_probability_authorized": "false",
            "clogging_rate_authorized": "false",
            "time_to_clog_authorized": "false",
            "recovery_authorized": "false",
            "route_score_authorized": "false",
            "winner_authorized": "false",
            "yield_authorized": "false",
            "detection_probability_authorized": "false",
        }
    ]


def _artifact_evidence_rows(
    raw_metrics_path: Path,
    summary_metrics_path: Path,
    parameter_matrix_path: Path,
    seed_matrix_path: Path,
    source_lock_path: Path,
) -> list[dict[str, str]]:
    summary_sha = sha256_file(summary_metrics_path)
    raw_sha = sha256_file(raw_metrics_path)
    return [
        {
            "evidence_field": "required_test_result_artifact_sha256",
            "candidate_sha256": summary_sha,
            "candidate_artifact": summary_metrics_path.name,
            "candidate_status": "candidate_generated_not_registered",
        },
        {
            "evidence_field": "dt_convergence_evidence_sha256",
            "candidate_sha256": summary_sha,
            "candidate_artifact": summary_metrics_path.name,
            "candidate_status": "candidate_generated_not_registered",
        },
        {
            "evidence_field": "equilibrium_uniformity_evidence_sha256",
            "candidate_sha256": raw_sha,
            "candidate_artifact": raw_metrics_path.name,
            "candidate_status": "candidate_generated_not_registered",
        },
        {
            "evidence_field": "no_boundary_atom_evidence_sha256",
            "candidate_sha256": raw_sha,
            "candidate_artifact": raw_metrics_path.name,
            "candidate_status": "candidate_generated_not_registered",
        },
        {
            "evidence_field": "corner_active_set_evidence_sha256",
            "candidate_sha256": summary_sha,
            "candidate_artifact": summary_metrics_path.name,
            "candidate_status": "candidate_generated_not_registered",
        },
        {
            "evidence_field": "angle_depth_mutation_evidence_sha256",
            "candidate_sha256": summary_sha,
            "candidate_artifact": summary_metrics_path.name,
            "candidate_status": "candidate_generated_not_registered",
        },
        {
            "evidence_field": "rectangle_limit_evidence_sha256",
            "candidate_sha256": summary_sha,
            "candidate_artifact": summary_metrics_path.name,
            "candidate_status": "candidate_generated_not_registered",
        },
        {
            "evidence_field": "rng_seed_matrix_sha256",
            "candidate_sha256": sha256_file(seed_matrix_path),
            "candidate_artifact": seed_matrix_path.name,
            "candidate_status": "candidate_generated_not_registered",
        },
        {
            "evidence_field": "test_parameter_matrix_sha256",
            "candidate_sha256": sha256_file(parameter_matrix_path),
            "candidate_artifact": parameter_matrix_path.name,
            "candidate_status": "candidate_generated_not_registered",
        },
        {
            "evidence_field": "test_environment_lock_sha256",
            "candidate_sha256": sha256_file(source_lock_path),
            "candidate_artifact": source_lock_path.name,
            "candidate_status": "candidate_generated_not_registered",
        },
    ]


def _candidate_manifest_rows(values: dict[str, str]) -> list[dict[str, str]]:
    return [
        {
            "required_field": field,
            "candidate_value": values.get(field, ""),
            "candidate_value_status": "candidate_only_not_registered",
            "registration_status": "not_registered",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for field in sorted(REQUIRED_PROOF_CONTRACT_FIELDS)
    ]


def _artifact_manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    return [
        {
            "artifact": path.name,
            "path": path.relative_to(PROJECT_ROOT).as_posix(),
            "sha256": sha256_file(path) if path.exists() else "",
            "disposition": DISPOSITION,
            "policy_impact": "candidate_only_no_proof_registration",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for path in paths
    ]


def build_metric_payload() -> dict[str, Any]:
    scenario_rows = _scenario_rows()
    open_rows = [row for row in scenario_rows if row["runtime_candidate_status"] == "candidate_open"]
    blocked_rows = [row for row in scenario_rows if row["runtime_candidate_status"] != "candidate_open"]
    dt_rows = _dt_halving_rows(open_rows)
    one_wall = _one_wall_limit_metrics()
    rectangle = _rectangle_limit_metrics()
    mutation = _mutation_metrics()
    corner = _corner_probe_metrics()
    boundary_atom_fractions = [
        float(row["boundary_atom_fraction"])
        for row in open_rows
        if row.get("boundary_atom_fraction") != ""
    ]
    equilibrium_distances = [
        float(row["equilibrium_uniformity_distance"])
        for row in open_rows
        if row.get("equilibrium_uniformity_distance") != ""
    ]
    support_violations = sum(int(row["support_violation_count"]) for row in open_rows)
    max_dt_delta = max(
        (float(row["dt_halving_max_distribution_delta"]) for row in dt_rows),
        default=0.0,
    )
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "metric_schema_version": METRIC_SCHEMA_VERSION,
        "claim_boundary": CLAIM_BOUNDARY,
        "gate30_31_build_base_commit_sha": safe_git_head(),
        "gate30_31_candidate_worktree_state": (
            "candidate_may_include_uncommitted_changes_not_reviewed_commit_binding"
        ),
        "scenario_metric_rows": len(scenario_rows),
        "open_candidate_metric_rows": len(open_rows),
        "blocked_candidate_rows": len(blocked_rows),
        "dt_halving_rows": len(dt_rows),
        "support_violation_count": support_violations,
        "max_boundary_atom_fraction": max(boundary_atom_fractions, default=0.0),
        "max_equilibrium_uniformity_distance": max(equilibrium_distances, default=0.0),
        "dt_halving_max_distribution_delta": max_dt_delta,
        "boundary_atom_status": "candidate_pass"
        if max(boundary_atom_fractions, default=0.0) <= BOUNDARY_ATOM_THRESHOLD
        else "candidate_review_required",
        "support_invariance_status": "candidate_pass"
        if support_violations == 0
        else "candidate_review_required",
        "equilibrium_uniformity_status": "candidate_pass"
        if max(equilibrium_distances, default=0.0) <= EQUILIBRIUM_DISTANCE_THRESHOLD
        else "candidate_review_required",
        "dt_halving_status": "candidate_pass"
        if max_dt_delta <= 0.75
        else "candidate_review_required",
        "corner_active_set_status": corner["corner_active_set_status"],
        "one_wall_limit_status": one_wall["one_wall_limit_status"],
        "rectangle_limit_status": rectangle["rectangle_limit_status"],
        "angle_depth_mutation_status": mutation["angle_depth_mutation_status"],
        "closed_geometry_guard_rows": sum(
            row["runtime_candidate_status"] == "blocked_geometry_closed"
            for row in blocked_rows
        ),
        "near_closed_guard_rows": sum(
            row["runtime_candidate_status"] == "blocked_near_closed_resource_guard"
            for row in blocked_rows
        ),
        "proof_registration_authorized": False,
        "package_c_validation_status_pass_authorized": False,
        "runtime_allowed": False,
        "numeric_prs_eas_allowed": False,
        "comsol_launch_allowed": False,
        "mph_load_allowed": False,
        "candidate_only": True,
        "no_auth": True,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    return {
        "summary": summary,
        "scenario_metrics": scenario_rows,
        "dt_halving": dt_rows,
        "one_wall_limit": one_wall,
        "rectangle_limit": rectangle,
        "angle_depth_mutation": mutation,
        "corner_active_set": corner,
        "environment_lock": _environment_lock(),
        "parameter_grid": {
            "sidewall_angle_grid_deg_comsol": SIDEWALL_ANGLE_GRID_DEG_COMSOL,
            "depth_grid_nm": DEPTH_GRID_NM,
            "particle_radius_grid_nm": PARTICLE_RADIUS_GRID_NM,
            "dt_grid_s": DT_GRID_S,
            "diffusion_coefficient_grid_m2_s": DIFFUSION_COEFFICIENT_GRID_M2_S,
            "rng_seeds": RNG_SEEDS,
        },
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    checks = {
        "support invariance candidate pass": summary["support_invariance_status"] == "candidate_pass",
        "boundary atom candidate pass": summary["boundary_atom_status"] == "candidate_pass",
        "one-wall candidate pass": summary["one_wall_limit_status"] == "candidate_pass",
        "rectangle-limit candidate pass": summary["rectangle_limit_status"] == "candidate_pass",
        "corner candidate pass": summary["corner_active_set_status"] == "candidate_pass",
        "angle/depth mutation candidate pass": summary["angle_depth_mutation_status"] == "candidate_pass",
        "closed geometry guard present": summary["closed_geometry_guard_rows"] > 0,
        "no proof registration": summary["proof_registration_authorized"] is False,
        "no package C validation pass": summary["package_c_validation_status_pass_authorized"] is False,
        "no runtime": summary["runtime_allowed"] is False,
        "no numeric PRS/EAS": summary["numeric_prs_eas_allowed"] is False,
        "no COMSOL launch": summary["comsol_launch_allowed"] is False,
        "no mph load": summary["mph_load_allowed"] is False,
        "candidate only": summary["candidate_only"] is True,
    }
    return [label for label, ok in checks.items() if not ok]


def _external_review_prompt_text(summary: dict[str, Any]) -> str:
    return f"""# Gate30/31 External Proof-Metrics Candidate Review Prompt

Please review the GitHub-visible Gate30/31 Package C proof-metrics candidate.

Scope:
- This is candidate evidence only: `{DISPOSITION}`.
- It is not Package C proof/pass registration.
- It is not runtime authorization, PRS/EAS numeric output, COMSOL launch, `.mph`
  load, route/yield/detection/wet/fabrication/production authorization.

What to review:
- Whether the finite-step active-set normal reflection metrics are sufficient
  as a future proof-registration candidate package.
- Whether the raw/summary metrics, dt-halving rows, no-boundary-atom check,
  equilibrium uniformity proxy, corner active-set probe, one-wall limit,
  rectangle limit, and angle/depth mutation evidence are correctly scoped.
- Whether the 52-field candidate manifest is safe as `candidate_only_not_registered`.

Current summary:
- support_invariance_status: `{summary['support_invariance_status']}`
- boundary_atom_status: `{summary['boundary_atom_status']}`
- equilibrium_uniformity_status: `{summary['equilibrium_uniformity_status']}`
- dt_halving_status: `{summary['dt_halving_status']}`
- corner_active_set_status: `{summary['corner_active_set_status']}`
- one_wall_limit_status: `{summary['one_wall_limit_status']}`
- rectangle_limit_status: `{summary['rectangle_limit_status']}`
- angle_depth_mutation_status: `{summary['angle_depth_mutation_status']}`

Required answer:
- Verdict: READY_FOR_PROOF_REGISTRATION_AUTHORIZATION_DESIGN_REVIEW_ONLY,
  NEEDS_MORE_CANDIDATE_EVIDENCE, or BLOCKED_CLAIM_PROMOTION.
- State whether any claim boundary, test threshold, telemetry field, or manifest
  value could be misread as proof/pass registration.
- State what must be added before a future, separately authorized proof registry
  update.
"""


def write_outputs(payload: dict[str, Any]) -> dict[str, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    raw_metrics_path = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_RAW_METRICS_20260630.json"
    write_json_atomic(raw_metrics_path, payload)
    generated.append(raw_metrics_path)

    summary_metrics = {
        "summary": payload["summary"],
        "dt_halving": payload["dt_halving"],
        "one_wall_limit": payload["one_wall_limit"],
        "rectangle_limit": payload["rectangle_limit"],
        "angle_depth_mutation": payload["angle_depth_mutation"],
        "corner_active_set": payload["corner_active_set"],
        "environment_lock": payload["environment_lock"],
        "parameter_grid": payload["parameter_grid"],
    }
    summary_metrics_path = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_SUMMARY_METRICS_20260630.json"
    write_json_atomic(summary_metrics_path, summary_metrics)
    generated.append(summary_metrics_path)

    parameter_matrix_path = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_TEST_PARAMETER_MATRIX_20260630.csv"
    write_csv_rows(parameter_matrix_path, _parameter_matrix_rows())
    generated.append(parameter_matrix_path)

    seed_matrix_path = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_RNG_SEED_MATRIX_20260630.csv"
    write_csv_rows(seed_matrix_path, _seed_matrix_rows())
    generated.append(seed_matrix_path)

    source_lock_path = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_SOURCE_LOCK_20260630.csv"
    write_csv_rows(source_lock_path, _source_lock_rows())
    generated.append(source_lock_path)

    evidence_path = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_CANDIDATE_EVIDENCE_MAP_20260630.csv"
    evidence_rows = _artifact_evidence_rows(
        raw_metrics_path,
        summary_metrics_path,
        parameter_matrix_path,
        seed_matrix_path,
        source_lock_path,
    )
    write_csv_rows(evidence_path, evidence_rows)
    generated.append(evidence_path)

    evidence_by_field = {row["evidence_field"]: row["candidate_sha256"] for row in evidence_rows}
    candidate_values = {
        "package_C_proof_artifact_id": ARTIFACT_ID,
        "package_C_proof_artifact_sha256": sha256_file(summary_metrics_path),
        "package_C_proof_artifact_status": "candidate_only_not_registered",
        "package_C_proof_artifact_scope": "Package C finite-step active-set normal-reflection metrics candidate",
        "package_C_proof_claim_boundary": CLAIM_BOUNDARY,
        "external_review_artifact_sha256": PENDING_EXTERNAL_REVIEW_SHA,
        "implementation_commit_sha": PENDING_REVIEWED_COMMIT_SHA,
        "required_test_result_artifact_sha256": evidence_by_field["required_test_result_artifact_sha256"],
        "dt_convergence_evidence_sha256": evidence_by_field["dt_convergence_evidence_sha256"],
        "equilibrium_uniformity_evidence_sha256": evidence_by_field["equilibrium_uniformity_evidence_sha256"],
        "no_boundary_atom_evidence_sha256": evidence_by_field["no_boundary_atom_evidence_sha256"],
        "corner_active_set_evidence_sha256": evidence_by_field["corner_active_set_evidence_sha256"],
        "angle_depth_mutation_evidence_sha256": evidence_by_field["angle_depth_mutation_evidence_sha256"],
        "rectangle_limit_evidence_sha256": evidence_by_field["rectangle_limit_evidence_sha256"],
        "authorization_supersedes_no_auth_ledger_sha256": "",
        "reflection_metric_schema_version": METRIC_SCHEMA_VERSION,
        "reflection_algorithm_source_sha256": sha256_file(PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py"),
        "reflection_test_script_sha256": sha256_file(PROJECT_ROOT / "tests/test_cross_section_geometry.py"),
        "test_environment_lock_sha256": evidence_by_field["test_environment_lock_sha256"],
        "dependency_lock_sha256": sha256_file(PROJECT_ROOT / "pyproject.toml"),
        "rng_seed_matrix_sha256": evidence_by_field["rng_seed_matrix_sha256"],
        "test_parameter_matrix_sha256": evidence_by_field["test_parameter_matrix_sha256"],
        "dt_grid_s": json.dumps(DT_GRID_S),
        "diffusion_coefficient_grid_m2_s": json.dumps(DIFFUSION_COEFFICIENT_GRID_M2_S),
        "particle_radius_grid_nm": json.dumps(PARTICLE_RADIUS_GRID_NM),
        "sidewall_angle_grid_deg_comsol": json.dumps(SIDEWALL_ANGLE_GRID_DEG_COMSOL),
        "depth_grid_nm": json.dumps(DEPTH_GRID_NM),
        "tolerance_m": str(TOLERANCE_M),
        "max_reflection_iterations": str(MAX_REFLECTION_ITERATIONS),
        "substep_policy": "none_candidate_metrics_only_future_runtime_must_substep_or_fail",
        "boundary_atom_threshold": str(BOUNDARY_ATOM_THRESHOLD),
        "equilibrium_test_method": "u_accessible_cdf_and_x_local_norm_histogram_candidate",
        "equilibrium_test_threshold": str(EQUILIBRIUM_DISTANCE_THRESHOLD),
        "corner_bias_test_threshold": str(CORNER_BIAS_THRESHOLD),
        "rectangle_limit_tolerance": str(RECTANGLE_LIMIT_TOLERANCE),
        "one_wall_limit_tolerance": str(ONE_WALL_LIMIT_TOLERANCE),
        "raw_metric_artifact_sha256": sha256_file(raw_metrics_path),
        "summary_metric_artifact_sha256": sha256_file(summary_metrics_path),
        "independent_reviewer_id_or_artifact_sha256": "",
        "package_C_proof_manifest_schema_version": "package_c_proof_manifest_candidate_v1",
        "package_C_proof_evidence_claim_level": CLAIM_BOUNDARY,
        "package_C_proof_required_test_matrix_status": "candidate_metrics_generated_not_proof_pass",
        "package_C_proof_external_review_status": "pending_external_review",
        "package_C_proof_authorization_status": "not_authorized_no_proof_registration",
        "authorization_supersedes_no_auth_ledger_id": "",
        "package_C_proof_no_hindered_diffusion_claim": "true",
        "package_C_proof_no_trapezoid_flow_solver_claim": "true",
        "package_C_proof_no_electrokinetic_solver_claim": "true",
        "package_C_proof_no_optical_solver_claim": "true",
        "package_C_proof_no_wet_claim": "true",
        "package_C_proof_no_prs_eas_numeric_output": "true",
        "package_C_proof_no_route_yield_detection_claim": "true",
    }

    candidate_manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_CANDIDATE_MANIFEST_20260630.csv"
    candidate_rows = _candidate_manifest_rows(candidate_values)
    write_csv_rows(candidate_manifest_path, candidate_rows)
    generated.append(candidate_manifest_path)

    candidate_manifest_json = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_CANDIDATE_MANIFEST_20260630.json"
    write_json_atomic(
        candidate_manifest_json,
        {
            "disposition": DISPOSITION,
            "candidate_only": True,
            "registration_status": "not_registered",
            "values": candidate_values,
        },
    )
    generated.append(candidate_manifest_json)

    firewall_path = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv"
    write_csv_rows(firewall_path, _firewall_rows())
    generated.append(firewall_path)

    review_prompt_path = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_EXTERNAL_REVIEW_PROMPT_20260630.md"
    review_prompt_path.write_text(_external_review_prompt_text(payload["summary"]), encoding="utf-8")
    generated.append(review_prompt_path)

    report_path = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(
        report_path,
        {
            "summary": payload["summary"],
            "candidate_manifest_rows": len(candidate_rows),
            "evidence_rows": len(evidence_rows),
            "outputs": [path.name for path in generated],
        },
    )
    generated.append(report_path)

    status_path = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(
        status_path,
        {
            "disposition": DISPOSITION,
            "summary": payload["summary"],
            "candidate_only": True,
            "no_auth": True,
            "proof_registration_authorized": False,
            "package_c_validation_status_pass_authorized": False,
        },
    )
    generated.append(status_path)

    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_METRICS_CANDIDATE_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate30/31 Sidewall Package C Proof Metrics Candidate",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Candidate artifact id: `{ARTIFACT_ID}`",
            f"- Scenario/open/blocked rows: {payload['summary']['scenario_metric_rows']}/{payload['summary']['open_candidate_metric_rows']}/{payload['summary']['blocked_candidate_rows']}.",
            f"- Support/boundary/equilibrium/dt statuses: `{payload['summary']['support_invariance_status']}`, `{payload['summary']['boundary_atom_status']}`, `{payload['summary']['equilibrium_uniformity_status']}`, `{payload['summary']['dt_halving_status']}`.",
            f"- One-wall/rectangle/corner/mutation statuses: `{payload['summary']['one_wall_limit_status']}`, `{payload['summary']['rectangle_limit_status']}`, `{payload['summary']['corner_active_set_status']}`, `{payload['summary']['angle_depth_mutation_status']}`.",
            "- Boundary: candidate only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection/wet/fab/production claims.",
        ],
    )
    generated.append(master_md)

    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate30/31 disposition: `{DISPOSITION}`",
                f"- Candidate artifact id: `{ARTIFACT_ID}`",
                f"- Candidate manifest fields: {len(candidate_rows)}/{len(REQUIRED_PROOF_CONTRACT_FIELDS)}.",
                f"- Evidence rows: {len(evidence_rows)}.",
                "- Boundary: candidate only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection/wet/fab/production claims.",
                f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
            ],
        )
        generated.append(path)

    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, _artifact_manifest_rows(generated))
    generated.append(manifest_path)

    return {
        "raw_metrics": raw_metrics_path,
        "summary_metrics": summary_metrics_path,
        "candidate_manifest": candidate_manifest_path,
        "candidate_manifest_json": candidate_manifest_json,
        "report": report_path,
        "status": status_path,
        "manifest": manifest_path,
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate30_31_package_c_proof_metrics_candidate:
        parser.error("--confirm-gate30-31-package-c-proof-metrics-candidate is required")
    payload = build_metric_payload()
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE30_31_SIDEWALL_PACKAGE_C_PROOF_METRICS_CANDIDATE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
