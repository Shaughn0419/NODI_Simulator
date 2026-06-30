#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random
import re
import subprocess
import sys
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)
from tools.audits import (  # noqa: E402
    build_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate as gate30_31,
)


DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"

EXPECTED_GATE33_36_DISPOSITION = (
    "NODI_GATE33_36_SIDEWALL_PACKAGE_C_REFLECTION_PROOF_AUTHORIZATION_DESIGN_READY_NO_PROOF_REGISTRATION"
)
DISPOSITION = (
    "NODI_GATE37_SIDEWALL_PACKAGE_C_REFLECTION_METRIC_HARDENING_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
ARTIFACT_ID = "GATE37_PACKAGE_C_REFLECTION_METRIC_HARDENING_CANDIDATE_20260630"
CLAIM_BOUNDARY = (
    "candidate_metric_hardening_not_package_c_proof_registered_not_validated_solver_output"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

ALLOWED_USE = (
    "Package C reflection metric hardening candidate;reviewer-friendly raw metric expansion;"
    "future proof-registration evidence design;no-proof-registration"
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

GATE30_31_RAW_METRICS = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_RAW_METRICS_20260630.json"
GATE30_31_SUMMARY_METRICS = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_SUMMARY_METRICS_20260630.json"
GATE33_36_STATUS = OUTPUT_DIR / "NODI_COMSOL_GATE33_36_SIDEWALL_STATUS_20260630.json"
GATE33_36_BACKLOG = OUTPUT_DIR / "NODI_COMSOL_GATE33_36_SIDEWALL_PROOF_HARDENING_BACKLOG_20260630.csv"
GATE33_36_THRESHOLDS = OUTPUT_DIR / "NODI_COMSOL_GATE33_36_SIDEWALL_THRESHOLD_MATRIX_20260630.csv"
GATE33_36_FIREWALL = OUTPUT_DIR / "NODI_COMSOL_GATE33_36_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv"

EXACT_ATOM_EPS_NM = 1.0e-9
NEAR_BAND_EPS_NM = 1.0e-3
PILEUP_FIRST_BAND_NM = 1.0
PILEUP_SECOND_BAND_NM = 2.0
BOUNDARY_SAMPLE_COUNT = 384
ONE_WALL_SAMPLE_COUNT = 4096
CORNER_SAMPLE_COUNT = 768
EXTRA_DT_S = 6.25e-6
WORST_CASE_COUNT = 10

SOURCE_FILES = {
    "gate30_31_raw_metrics": GATE30_31_RAW_METRICS,
    "gate30_31_summary_metrics": GATE30_31_SUMMARY_METRICS,
    "gate33_36_status": GATE33_36_STATUS,
    "gate33_36_backlog": GATE33_36_BACKLOG,
    "gate33_36_thresholds": GATE33_36_THRESHOLDS,
    "gate33_36_no_proof_firewall": GATE33_36_FIREWALL,
    "cross_section_geometry": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
    "trajectory": PROJECT_ROOT / "nodi_simulator/trajectory.py",
    "gate37_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate37_sidewall_package_c_metric_hardening_candidate.py",
    "gate37_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_gate37_sidewall_package_c_metric_hardening_candidate.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}

REPORTS = {
    "496": "GATE37A_BOUNDARY_ATOM_AND_HISTOGRAM_HARDENING",
    "497": "GATE37B_ONE_WALL_NEGATIVE_CONTROL_AND_DT_REFINEMENT",
    "498": "GATE37C_CORNER_HEATMAP_AND_FIREWALL",
    "499": "GATE37_REFLECTION_METRIC_HARDENING_CANDIDATE_MASTER_REPORT",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Gate37 Package C reflection metric hardening candidate artifacts."
    )
    parser.add_argument(
        "--confirm-gate37-package-c-metric-hardening-candidate",
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


def rel(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def raw_url(path: Path) -> str:
    return f"{GITHUB_RAW_BASE}/{rel(path)}"


def blob_url(path: Path) -> str:
    return f"{GITHUB_BLOB_BASE}/{rel(path)}"


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def _open_rows(raw_payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in raw_payload.get("scenario_metrics", [])
        if row.get("runtime_candidate_status") == "candidate_open"
    ]


def _scenario_parameters(scenario_id: str) -> tuple[float, float, float]:
    match = re.fullmatch(r"theta([0-9.]+)_D([0-9.]+)_r([0-9.]+)", scenario_id)
    if not match:
        raise ValueError(f"Unexpected scenario_id: {scenario_id}")
    theta, depth_nm, radius_nm = match.groups()
    return float(theta), float(depth_nm), float(radius_nm)


def _simulate_points(
    *,
    theta_deg: float,
    depth_nm: float,
    radius_nm: float,
    dt_s: float,
    seed: int,
    n_samples: int,
) -> list[dict[str, Any]]:
    geom = gate30_31._geom(theta_deg, depth_nm)
    radius_m = gate30_31._m(radius_nm)
    sigma_m = math.sqrt(2.0 * gate30_31.DIFFUSION_COEFFICIENT_GRID_M2_S[0] * dt_s)
    rng = random.Random(seed)
    points: list[dict[str, Any]] = []
    for _ in range(n_samples):
        x0, u0 = geom.sample_particle_center_uniform(rng.random(), rng.random(), radius_m)
        result = geom.reflect_particle_center_step_with_diagnostics(
            x0 + rng.gauss(0.0, sigma_m),
            u0 + rng.gauss(0.0, sigma_m),
            radius_m,
            max_iterations=gate30_31.MAX_REFLECTION_ITERATIONS,
            tolerance_m=gate30_31.TOLERANCE_M,
        )
        diagnostics = geom.particle_wall_gap_diagnostics_m(result.x_m, result.u_m, radius_m)
        min_gap_nm = gate30_31._nm(float(diagnostics["surface_gap_for_particle_m"]))
        x_norm = gate30_31._x_local_norm(geom, result.x_m, result.u_m, radius_m)
        u_cdf = gate30_31._u_accessible_cdf(geom, result.u_m, radius_m)
        points.append(
            {
                "surface_gap_nm": min_gap_nm,
                "x_local_norm": x_norm,
                "u_accessible_cdf": u_cdf,
                "active_wall_count": len(set(result.active_wall_ids)),
                "reflection_iteration_count": result.iteration_count,
                "nearest_wall_id": str(diagnostics["nearest_wall_id"]),
            }
        )
    return points


def _fraction(count: int, total: int) -> float:
    return round(count / max(total, 1), 9)


def boundary_atom_split_rows(raw_payload: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_row in _open_rows(raw_payload):
        theta, depth_nm, radius_nm = _scenario_parameters(str(source_row["scenario_id"]))
        points = _simulate_points(
            theta_deg=theta,
            depth_nm=depth_nm,
            radius_nm=radius_nm,
            dt_s=float(source_row["dt_s"]),
            seed=int(source_row["rng_seed"]),
            n_samples=BOUNDARY_SAMPLE_COUNT,
        )
        exact_count = sum(abs(point["surface_gap_nm"]) <= EXACT_ATOM_EPS_NM for point in points)
        near_count = sum(0.0 <= point["surface_gap_nm"] <= NEAR_BAND_EPS_NM for point in points)
        first_band = sum(0.0 <= point["surface_gap_nm"] < PILEUP_FIRST_BAND_NM for point in points)
        second_band = sum(
            PILEUP_FIRST_BAND_NM <= point["surface_gap_nm"] < PILEUP_SECOND_BAND_NM
            for point in points
        )
        pileup_ratio = (first_band + 0.5) / (second_band + 0.5)
        candidate_interpretation = (
            "exact_atom_split_checked_no_exact_atoms_observed_not_proof_registered"
            if exact_count == 0
            else "exact_atom_split_checked_exact_atoms_observed_candidate_review_required_not_proof_registered"
        )
        rows.append(
            {
                "scenario_id": str(source_row["scenario_id"]),
                "dt_s": str(source_row["dt_s"]),
                "rng_seed": str(source_row["rng_seed"]),
                "n_samples": str(BOUNDARY_SAMPLE_COUNT),
                "exact_boundary_atom_eps_nm": str(EXACT_ATOM_EPS_NM),
                "near_boundary_band_eps_nm": str(NEAR_BAND_EPS_NM),
                "exact_boundary_atom_fraction": str(_fraction(exact_count, BOUNDARY_SAMPLE_COUNT)),
                "near_boundary_band_fraction": str(_fraction(near_count, BOUNDARY_SAMPLE_COUNT)),
                "first_gap_band_fraction": str(_fraction(first_band, BOUNDARY_SAMPLE_COUNT)),
                "adjacent_gap_band_fraction": str(_fraction(second_band, BOUNDARY_SAMPLE_COUNT)),
                "wall_pileup_ratio": str(round(pileup_ratio, 9)),
                "candidate_interpretation": candidate_interpretation,
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def histogram_rows(raw_payload: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    x_edges = [round(-1.0 + 0.2 * idx, 9) for idx in range(11)]
    u_edges = [round(0.1 * idx, 9) for idx in range(11)]
    for source_row in _open_rows(raw_payload):
        for basis, edges, values in (
            ("x_local_norm", x_edges, source_row["x_local_norm_histogram"]),
            ("u_accessible_cdf", u_edges, source_row["u_accessible_cdf_histogram"]),
        ):
            rows.append(
                {
                    "scenario_id": str(source_row["scenario_id"]),
                    "dt_s": str(source_row["dt_s"]),
                    "rng_seed": str(source_row["rng_seed"]),
                    "histogram_basis": basis,
                    "bin_edges_json": json.dumps(edges),
                    "bin_probability_json": json.dumps(values),
                    "n_samples": str(source_row["n_samples"]),
                    "reviewer_use": "raw_distribution_inspection_not_proof_registration",
                    "claim_boundary": CLAIM_BOUNDARY,
                    "allowed_use": ALLOWED_USE,
                    "blocked_use": BLOCKED_USE,
                }
            )
    return rows


def ess_proxy_rows(raw_payload: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_row in _open_rows(raw_payload):
        rows.append(
            {
                "scenario_id": str(source_row["scenario_id"]),
                "dt_s": str(source_row["dt_s"]),
                "rng_seed": str(source_row["rng_seed"]),
                "raw_sample_count": str(source_row["n_samples"]),
                "effective_sample_size_proxy": str(source_row["n_samples"]),
                "ess_method": "independent_one_step_samples_no_timeseries_autocorrelation_available",
                "burn_in_steps": "0",
                "sample_stride": "not_applicable_one_step_candidate",
                "autocorrelation_status": "not_a_timeseries_proof_artifact",
                "proof_gap": "future proof artifact must bind timeseries ESS if long-run equilibrium trajectories are used",
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _reflecting_one_wall_cdf(r: float, d_over_sigma: float) -> float:
    if r < 0.0:
        return 0.0
    return min(
        max(
            _normal_cdf(r - d_over_sigma) + _normal_cdf(r + d_over_sigma) - 1.0,
            0.0,
        ),
        1.0,
    )


def _ks_distance(samples: list[float], cdf: Callable[[float], float]) -> float:
    ordered = sorted(samples)
    n = len(ordered)
    max_delta = 0.0
    for idx, sample in enumerate(ordered, start=1):
        empirical_hi = idx / n
        empirical_lo = (idx - 1) / n
        expected = cdf(sample)
        max_delta = max(max_delta, abs(empirical_hi - expected), abs(empirical_lo - expected))
    return round(max_delta, 9)


def one_wall_suite_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    rng = random.Random(37037)
    d_grid = (0.0, 0.25, 0.5, 1.0, 2.0, 4.0)
    for d_over_sigma in d_grid:
        normals = [rng.gauss(0.0, 1.0) for _ in range(ONE_WALL_SAMPLE_COUNT)]
        tangential = [rng.gauss(0.0, 1.0) for _ in range(ONE_WALL_SAMPLE_COUNT)]
        mirror_samples = [abs(d_over_sigma + z) for z in normals]
        clamp_samples = [max(d_over_sigma + z, 0.0) for z in normals]
        rejection_samples: list[float] = []
        for z in normals:
            value = d_over_sigma + z
            while value < 0.0:
                value = d_over_sigma + rng.gauss(0.0, 1.0)
            rejection_samples.append(value)
        tangential_mean = sum(tangential) / len(tangential)
        tangential_var = sum((value - tangential_mean) ** 2 for value in tangential) / len(
            tangential
        )
        for method, samples, expected in (
            ("folded_normal_mirror_positive_control", mirror_samples, "candidate_pass"),
            ("projection_clamp_negative_control", clamp_samples, "expected_fail_boundary_atom"),
            ("rejection_resampling_negative_control", rejection_samples, "expected_fail_transition_kernel"),
        ):
            exact_atom_fraction = _fraction(
                sum(abs(sample) <= 1.0e-15 for sample in samples), ONE_WALL_SAMPLE_COUNT
            )
            rows.append(
                {
                    "method": method,
                    "d_over_sigma": str(d_over_sigma),
                    "n_samples": str(ONE_WALL_SAMPLE_COUNT),
                    "ks_distance_to_reflecting_kernel": str(
                        _ks_distance(
                            samples,
                            lambda value, d=d_over_sigma: _reflecting_one_wall_cdf(value, d),
                        )
                    ),
                    "exact_boundary_atom_fraction": str(exact_atom_fraction),
                    "tangential_variance_error_abs": str(round(abs(tangential_var - 1.0), 9)),
                    "expected_status": expected,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "allowed_use": ALLOWED_USE,
                    "blocked_use": BLOCKED_USE,
                }
            )
    return rows


def worst_case_dt_refinement_rows(raw_payload: dict[str, Any]) -> list[dict[str, str]]:
    scenario_rows = _open_rows(raw_payload)
    by_key = {
        (str(row["scenario_id"]), str(row["dt_s"])): row
        for row in scenario_rows
    }
    dt_rows = sorted(
        raw_payload.get("dt_halving", []),
        key=lambda row: float(row["dt_halving_max_distribution_delta"]),
        reverse=True,
    )[:WORST_CASE_COUNT]
    rows: list[dict[str, str]] = []
    for dt_row in dt_rows:
        scenario_id = str(dt_row["scenario_id"])
        theta, depth_nm, radius_nm = _scenario_parameters(scenario_id)
        baseline = by_key.get((scenario_id, str(min(gate30_31.DT_GRID_S))))
        if baseline is None:
            continue
        extra = gate30_31._reflect_diffusive_steps(
            gate30_31._geom(theta, depth_nm),
            gate30_31._m(radius_nm),
            dt_s=EXTRA_DT_S,
            diffusion_m2_s=gate30_31.DIFFUSION_COEFFICIENT_GRID_M2_S[0],
            seed=int(baseline["rng_seed"]),
            n_samples=int(baseline["n_samples"]),
        )
        delta = max(
            gate30_31._hist_l1(
                baseline["x_local_norm_histogram"], extra["x_local_norm_histogram"]
            ),
            gate30_31._hist_l1(
                baseline["u_accessible_cdf_histogram"],
                extra["u_accessible_cdf_histogram"],
            ),
            abs(float(baseline["wall_gap_p50_nm"]) - float(extra["wall_gap_p50_nm"]))
            / 100.0,
        )
        rows.append(
            {
                "scenario_id": scenario_id,
                "prior_dt_halving_max_distribution_delta": str(
                    dt_row["dt_halving_max_distribution_delta"]
                ),
                "baseline_dt_s": str(baseline["dt_s"]),
                "extra_dt_s": str(EXTRA_DT_S),
                "extra_dt_distribution_delta_vs_baseline_min_dt": str(round(delta, 9)),
                "extra_dt_support_violation_count": str(extra["support_violation_count"]),
                "extra_dt_boundary_atom_fraction": str(extra["boundary_atom_fraction"]),
                "candidate_status": "candidate_metric_only_not_proof",
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def corner_heatmap_rows(raw_payload: dict[str, Any]) -> list[dict[str, str]]:
    candidates = sorted(
        _open_rows(raw_payload),
        key=lambda row: float(row.get("corner_active_set_rate", 0.0)),
        reverse=True,
    )[:WORST_CASE_COUNT]
    rows: list[dict[str, str]] = []
    for source_row in candidates:
        theta, depth_nm, radius_nm = _scenario_parameters(str(source_row["scenario_id"]))
        points = _simulate_points(
            theta_deg=theta,
            depth_nm=depth_nm,
            radius_nm=radius_nm,
            dt_s=float(source_row["dt_s"]),
            seed=int(source_row["rng_seed"]),
            n_samples=CORNER_SAMPLE_COUNT,
        )
        bins = {
            "top_left": 0,
            "top_right": 0,
            "bottom_left": 0,
            "bottom_right": 0,
        }
        active_multiwall = sum(point["active_wall_count"] >= 2 for point in points)
        max_iterations = max(int(point["reflection_iteration_count"]) for point in points)
        for point in points:
            x_norm = float(point["x_local_norm"])
            u_cdf = float(point["u_accessible_cdf"])
            if u_cdf < 0.1 and x_norm < -0.8:
                bins["top_left"] += 1
            elif u_cdf < 0.1 and x_norm > 0.8:
                bins["top_right"] += 1
            elif u_cdf > 0.9 and x_norm < -0.8:
                bins["bottom_left"] += 1
            elif u_cdf > 0.9 and x_norm > 0.8:
                bins["bottom_right"] += 1
        expected_fraction = 0.01
        for corner_id, count in bins.items():
            occupancy_fraction = count / CORNER_SAMPLE_COUNT
            rows.append(
                {
                    "scenario_id": str(source_row["scenario_id"]),
                    "dt_s": str(source_row["dt_s"]),
                    "corner_id": corner_id,
                    "n_samples": str(CORNER_SAMPLE_COUNT),
                    "occupancy_fraction": str(round(occupancy_fraction, 9)),
                    "accessible_area_expectation_fraction": str(expected_fraction),
                    "corner_occupancy_ratio_to_expected": str(
                        round(occupancy_fraction / expected_fraction, 9)
                    ),
                    "active_multiwall_rate": str(_fraction(active_multiwall, CORNER_SAMPLE_COUNT)),
                    "max_reflection_iterations": str(max_iterations),
                    "candidate_status": "candidate_metric_only_not_proof",
                    "claim_boundary": CLAIM_BOUNDARY,
                    "allowed_use": ALLOWED_USE,
                    "blocked_use": BLOCKED_USE,
                }
            )
    return rows


def source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for label, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_label": label,
                "path": rel(path),
                "exists": bool_text(exists),
                "sha256": sha256_file(path) if exists else "",
                "github_raw_url": raw_url(path),
                "github_blob_url": blob_url(path),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def no_proof_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_status": "PASS_GATE37_METRIC_HARDENING_CANDIDATE_NO_PROOF_REGISTRATION",
            "package_c_proof_artifact_registered": "false",
            "proof_registration_authorized": "false",
            "package_c_validation_status_pass_authorized": "false",
            "runtime_configuration_authorized": "false",
            "sidewall_prs_eas_numeric_output_authorized": "false",
            "nodi_runtime_recomputation_authorized": "false",
            "comsol_launch_authorized": "false",
            "mph_load_authorized": "false",
            "validated_brownian_solver_output_authorized": "false",
            "hindered_diffusion_claim_authorized": "false",
            "trapezoid_flow_solver_claim_authorized": "false",
            "electrokinetic_solver_claim_authorized": "false",
            "optical_solver_claim_authorized": "false",
            "true_w_eff_authorized": "false",
            "wet_claim_authorized": "false",
            "route_score_authorized": "false",
            "winner_authorized": "false",
            "yield_authorized": "false",
            "detection_probability_authorized": "false",
            "production_ingestion_authorized": "false",
        }
    ]


def build_payload() -> dict[str, Any]:
    raw_payload = read_json(GATE30_31_RAW_METRICS)
    gate33_36_summary = read_json(GATE33_36_STATUS).get("summary", {})
    boundary_rows = boundary_atom_split_rows(raw_payload)
    histogram = histogram_rows(raw_payload)
    ess = ess_proxy_rows(raw_payload)
    one_wall = one_wall_suite_rows()
    dt_extra = worst_case_dt_refinement_rows(raw_payload)
    corner = corner_heatmap_rows(raw_payload)
    source_rows = source_lock_rows()
    firewall = no_proof_firewall_rows()
    max_exact_atom = max(
        (float(row["exact_boundary_atom_fraction"]) for row in boundary_rows),
        default=0.0,
    )
    max_near_band = max(
        (float(row["near_boundary_band_fraction"]) for row in boundary_rows),
        default=0.0,
    )
    max_pileup = max((float(row["wall_pileup_ratio"]) for row in boundary_rows), default=0.0)
    max_one_wall_positive_ks = max(
        (
            float(row["ks_distance_to_reflecting_kernel"])
            for row in one_wall
            if row["method"] == "folded_normal_mirror_positive_control"
        ),
        default=0.0,
    )
    max_projection_atom = max(
        (
            float(row["exact_boundary_atom_fraction"])
            for row in one_wall
            if row["method"] == "projection_clamp_negative_control"
        ),
        default=0.0,
    )
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "gate37_build_head": safe_git_head(),
        "gate33_36_disposition": gate33_36_summary.get("disposition", ""),
        "gate33_36_expected_disposition": EXPECTED_GATE33_36_DISPOSITION,
        "scenario_metric_rows_inherited": len(raw_payload.get("scenario_metrics", [])),
        "boundary_atom_split_rows": len(boundary_rows),
        "histogram_rows": len(histogram),
        "ess_proxy_rows": len(ess),
        "one_wall_suite_rows": len(one_wall),
        "worst_case_dt_refinement_rows": len(dt_extra),
        "corner_heatmap_rows": len(corner),
        "source_lock_rows": len(source_rows),
        "source_missing_rows": sum(row["exists"] != "true" for row in source_rows),
        "max_exact_boundary_atom_fraction": max_exact_atom,
        "max_near_boundary_band_fraction": max_near_band,
        "max_wall_pileup_ratio": round(max_pileup, 9),
        "max_one_wall_positive_control_ks": max_one_wall_positive_ks,
        "max_projection_negative_control_exact_atom_fraction": max_projection_atom,
        "boundary_atom_split_status": (
            "candidate_review_required_exact_atoms_observed"
            if max_exact_atom > 1.0e-5
            else "candidate_pass_not_proof"
        ),
        "one_wall_positive_control_status": (
            "candidate_pass_not_proof"
            if max_one_wall_positive_ks <= 0.02
            else "candidate_review_required"
        ),
        "projection_negative_control_status": (
            "expected_fail_observed"
            if max_projection_atom > 0.0
            else "candidate_review_required_negative_control_too_weak"
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
        "source_locks": source_rows,
        "boundary_atom_split": boundary_rows,
        "raw_histograms": histogram,
        "ess_proxy": ess,
        "one_wall_suite": one_wall,
        "worst_case_dt_refinement": dt_extra,
        "corner_heatmap": corner,
        "no_proof_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "Gate33/36 disposition": s["gate33_36_disposition"] == EXPECTED_GATE33_36_DISPOSITION,
        "Source lock complete": s["source_missing_rows"] == 0,
        "Scenario metrics inherited": s["scenario_metric_rows_inherited"] >= 200,
        "Boundary split rows present": s["boundary_atom_split_rows"] >= 100,
        "Histogram rows present": s["histogram_rows"] >= 300,
        "ESS proxy rows present": s["ess_proxy_rows"] >= 100,
        "One-wall suite rows present": s["one_wall_suite_rows"] == 18,
        "Worst-case dt rows present": s["worst_case_dt_refinement_rows"] == WORST_CASE_COUNT,
        "Corner heatmap rows present": s["corner_heatmap_rows"] == WORST_CASE_COUNT * 4,
        "One-wall positive control passes candidate threshold": s[
            "one_wall_positive_control_status"
        ]
        == "candidate_pass_not_proof",
        "Projection negative control fails as expected": s["projection_negative_control_status"]
        == "expected_fail_observed",
        "No proof registration": s["proof_registration_authorized"] is False,
        "No Package C pass": s["package_c_validation_status_pass_authorized"] is False,
        "No runtime": s["runtime_allowed"] is False,
        "No numeric PRS/EAS": s["numeric_prs_eas_allowed"] is False,
        "No COMSOL launch": s["comsol_launch_allowed"] is False,
        "No mph load": s["mph_load_allowed"] is False,
    }
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            checks[f"Firewall false: {key}"] = value == "false"
    return [label for label, ok in checks.items() if not ok]


def artifact_manifest_rows(
    paths: list[Path],
    *,
    self_manifest_path: Path | None = None,
) -> list[dict[str, str]]:
    rows = [
        {
            "artifact": path.name,
            "path": rel(path),
            "sha256": sha256_file(path) if path.exists() else "",
            "disposition": DISPOSITION,
            "policy_impact": "metric_hardening_candidate_only_no_proof_registration",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for path in paths
    ]
    if self_manifest_path is not None:
        rows.append(
            {
                "artifact": self_manifest_path.name,
                "path": rel(self_manifest_path),
                "sha256": SELF_MANIFEST_SHA256,
                "disposition": DISPOSITION,
                "policy_impact": "manifest_self_row_no_recursive_sha_no_proof_registration",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def write_outputs(
    payload: dict[str, Any],
    *,
    output_dir: Path | None = None,
    report_dir: Path | None = None,
) -> dict[str, Path]:
    active_output_dir = output_dir or OUTPUT_DIR
    active_report_dir = report_dir or REPORT_DIR
    active_output_dir.mkdir(parents=True, exist_ok=True)
    active_report_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    csv_specs = {
        "NODI_COMSOL_GATE37_SIDEWALL_SOURCE_LOCK_20260630.csv": payload["source_locks"],
        "NODI_COMSOL_GATE37_SIDEWALL_BOUNDARY_ATOM_SPLIT_20260630.csv": payload[
            "boundary_atom_split"
        ],
        "NODI_COMSOL_GATE37_SIDEWALL_RAW_HISTOGRAMS_20260630.csv": payload[
            "raw_histograms"
        ],
        "NODI_COMSOL_GATE37_SIDEWALL_ESS_PROXY_20260630.csv": payload["ess_proxy"],
        "NODI_COMSOL_GATE37_SIDEWALL_ONE_WALL_FOLDED_NORMAL_SUITE_20260630.csv": payload[
            "one_wall_suite"
        ],
        "NODI_COMSOL_GATE37_SIDEWALL_WORST_CASE_DT_REFINEMENT_20260630.csv": payload[
            "worst_case_dt_refinement"
        ],
        "NODI_COMSOL_GATE37_SIDEWALL_CORNER_HEATMAP_20260630.csv": payload[
            "corner_heatmap"
        ],
        "NODI_COMSOL_GATE37_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv": payload[
            "no_proof_firewall"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    report_path = active_output_dir / "NODI_COMSOL_GATE37_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(report_path, {"summary": payload["summary"], "outputs": [p.name for p in generated]})
    generated.append(report_path)

    status_path = active_output_dir / "NODI_COMSOL_GATE37_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(
        status_path,
        {
            "disposition": DISPOSITION,
            "summary": payload["summary"],
            "proof_registration_authorized": False,
            "package_c_validation_status_pass_authorized": False,
            "runtime_allowed": False,
            "numeric_prs_eas_allowed": False,
            "comsol_launch_allowed": False,
            "mph_load_allowed": False,
        },
    )
    generated.append(status_path)

    master_md = active_output_dir / "NODI_COMSOL_GATE37_SIDEWALL_METRIC_HARDENING_CANDIDATE_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate37 Sidewall Metric Hardening Candidate",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Boundary split rows: {payload['summary']['boundary_atom_split_rows']}.",
            f"- Raw histogram rows: {payload['summary']['histogram_rows']}.",
            f"- ESS proxy rows: {payload['summary']['ess_proxy_rows']}.",
            f"- One-wall suite rows: {payload['summary']['one_wall_suite_rows']}.",
            f"- Worst-case dt refinement rows: {payload['summary']['worst_case_dt_refinement_rows']}.",
            f"- Corner heatmap rows: {payload['summary']['corner_heatmap_rows']}.",
            f"- Boundary atom split status: `{payload['summary']['boundary_atom_split_status']}`.",
            "- Boundary: metric hardening candidate only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no numeric PRS/EAS, no route/yield/detection/wet/fab/production claims.",
        ],
    )
    generated.append(master_md)

    for number, title in REPORTS.items():
        path = active_report_dir / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate37 disposition: `{DISPOSITION}`",
                f"- Source head: `{payload['summary']['gate37_build_head']}`",
                f"- Boundary atom split status: `{payload['summary']['boundary_atom_split_status']}`",
                f"- One-wall positive control status: `{payload['summary']['one_wall_positive_control_status']}`",
                f"- Projection negative control status: `{payload['summary']['projection_negative_control_status']}`",
                "- Boundary: metric hardening candidate only; proof registration and Package C pass remain unauthorized.",
                f"- Machine-readable support: `{rel(active_output_dir)}`.",
            ],
        )
        generated.append(path)

    manifest_path = active_output_dir / "NODI_COMSOL_GATE37_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(
        manifest_path,
        artifact_manifest_rows(generated, self_manifest_path=manifest_path),
    )
    return {
        "status": status_path,
        "report": report_path,
        "manifest": manifest_path,
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate37_package_c_metric_hardening_candidate:
        parser.error("--confirm-gate37-package-c-metric-hardening-candidate is required")
    payload = build_payload()
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE37_SIDEWALL_PACKAGE_C_METRIC_HARDENING_CANDIDATE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
