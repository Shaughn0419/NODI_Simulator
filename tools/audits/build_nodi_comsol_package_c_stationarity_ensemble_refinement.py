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

from nodi_simulator.realism_v2_io import (  # noqa: E402
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)
from tools.audits import (  # noqa: E402
    build_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate as gate30_31,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"

DISPOSITION = (
    "NODI_PACKAGE_C_STATIONARITY_ENSEMBLE_REFINEMENT_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
ARTIFACT_ID = "PACKAGE_C_STATIONARITY_ENSEMBLE_REFINEMENT_20260701"
CLAIM_BOUNDARY = "stationarity_ensemble_candidate_not_package_c_proof_registered_not_runtime"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
GITHUB_VISIBILITY_STATUS = "local_worktree_pre_commit_urls_valid_after_publish"

ALLOWED_USE = (
    "Package C independent-ensemble stationarity refinement candidate;"
    "proof-gap reduction evidence;no-proof-registration"
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

EXTERNAL_RESEARCH_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_STATUS_20260701.json"
)
THRESHOLD_TABLE = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_TABLE_20260701.csv"
)

SOURCE_FILES = {
    "external_research_status": EXTERNAL_RESEARCH_STATUS,
    "proof_threshold_table": THRESHOLD_TABLE,
    "cross_section_geometry": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
    "gate30_31_metric_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate.py",
    "stationarity_ensemble_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_package_c_stationarity_ensemble_refinement.py",
    "stationarity_ensemble_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_package_c_stationarity_ensemble_refinement.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}

SCENARIOS = (
    {"scenario_id": "rect_limit_theta90_D900_r20", "theta": 90.0, "depth": 900.0, "radius": 20.0},
    {"scenario_id": "moderate_theta85_D900_r110", "theta": 85.0, "depth": 900.0, "radius": 110.0},
    {"scenario_id": "deep_tail_theta85_D1200_r150", "theta": 85.0, "depth": 1200.0, "radius": 150.0},
    {"scenario_id": "steep_theta80_D900_r75", "theta": 80.0, "depth": 900.0, "radius": 75.0},
    {"scenario_id": "stress_theta70_D900_r20", "theta": 70.0, "depth": 900.0, "radius": 20.0},
    {"scenario_id": "narrow_tail_theta70_D900_r150", "theta": 70.0, "depth": 900.0, "radius": 150.0},
)
SEEDS = (53101, 53102, 53103)
N_INDEPENDENT_SAMPLES_PER_SEED = 32768
DT_S = 2.5e-5
DIFFUSION_M2_S = 4.0e-12
HISTOGRAM_BINS = 10
EXACT_ATOM_EPS_M = 1.0e-18
PROOF_L1_HARD_LINE = 0.04
PROOF_L1_TARGET = 0.03
PROOF_MIN_INDEPENDENT_SAMPLE_SIZE = 5000


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Package C independent-ensemble stationarity refinement artifacts."
    )
    parser.add_argument(
        "--confirm-package-c-stationarity-ensemble-refinement",
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


def rel(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def raw_url(path: Path) -> str:
    return f"{GITHUB_RAW_BASE}/{rel(path)}"


def blob_url(path: Path) -> str:
    return f"{GITHUB_BLOB_BASE}/{rel(path)}"


def fmt(value: float, digits: int = 12) -> str:
    return f"{value:.{digits}g}"


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


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
                "github_visibility_status": GITHUB_VISIBILITY_STATUS,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def no_proof_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_status": "PASS_PACKAGE_C_STATIONARITY_ENSEMBLE_NO_PROOF_REGISTRATION",
            "package_c_proof_artifact_registered": "false",
            "proof_registration_authorized": "false",
            "package_c_validation_status_pass_authorized": "false",
            "runtime_configuration_authorized": "false",
            "substep_runtime_policy_authorized": "false",
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


def _histogram(values: list[float], bins: int, low: float, high: float) -> list[float]:
    counts = [0] * bins
    if not values:
        return [0.0] * bins
    span = high - low
    for value in values:
        idx = int((value - low) / span * bins)
        idx = max(0, min(bins - 1, idx))
        counts[idx] += 1
    return [count / len(values) for count in counts]


def _l1_to_uniform(histogram: list[float]) -> float:
    expected = 1.0 / len(histogram) if histogram else 0.0
    return sum(abs(value - expected) for value in histogram)


def _histogram_l1(left: list[float], right: list[float]) -> float:
    return sum(abs(l_value - r_value) for l_value, r_value in zip(left, right))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _sample_stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def _ci_row(
    scenario_id: str,
    basis: str,
    values: list[float],
    *,
    proof_line: float,
) -> dict[str, str]:
    mean = _mean(values)
    stdev = _sample_stdev(values)
    se = stdev / math.sqrt(len(values)) if values else 0.0
    half_width = 1.96 * se
    ci_upper = mean + half_width
    return {
        "scenario_id": scenario_id,
        "basis": basis,
        "seed_count": str(len(values)),
        "mean_l1": fmt(mean),
        "sample_stdev_l1": fmt(stdev),
        "standard_error_l1": fmt(se),
        "ci95_half_width_l1": fmt(half_width),
        "ci95_upper_l1": fmt(ci_upper),
        "proof_l1_hard_line": fmt(proof_line),
        "ci_status": (
            "candidate_ci_upper_within_current_proof_line_not_registered"
            if ci_upper <= proof_line
            else "candidate_ci_upper_exceeds_current_proof_line_review_required"
        ),
        "claim_boundary": CLAIM_BOUNDARY,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }


def _wall_min_constraint_m(geom: Any, x_m: float, u_m: float, radius_m: float) -> float:
    return min(geom.wall_constraint_values_m(x_m, u_m, radius_m).values())


def _simulate_scenario_seed(
    scenario: dict[str, float | str],
    seed: int,
) -> tuple[dict[str, str], list[dict[str, str]]]:
    geom = gate30_31._geom(float(scenario["theta"]), float(scenario["depth"]))
    radius_m = gate30_31._m(float(scenario["radius"]))
    rng = random.Random(seed)
    sigma_m = math.sqrt(2.0 * DIFFUSION_M2_S * DT_S)

    initial_u: list[float] = []
    initial_x: list[float] = []
    final_u: list[float] = []
    final_x: list[float] = []
    support_violations = 0
    exact_boundary_atoms = 0
    nonconverged = 0
    reflected_steps = 0
    multiwall_steps = 0
    iteration_counts: list[int] = []
    reflection_displacement_nm: list[float] = []

    for _ in range(N_INDEPENDENT_SAMPLES_PER_SEED):
        x_m, u_m = geom.sample_particle_center_uniform(rng.random(), rng.random(), radius_m)
        initial_u.append(gate30_31._u_accessible_cdf(geom, u_m, radius_m))
        initial_x.append(gate30_31._x_local_norm(geom, x_m, u_m, radius_m))

        trial_x = x_m + rng.gauss(0.0, sigma_m)
        trial_u = u_m + rng.gauss(0.0, sigma_m)
        result = geom.reflect_particle_center_step_with_diagnostics(
            trial_x,
            trial_u,
            radius_m,
            max_iterations=64,
            tolerance_m=1.0e-15,
        )
        if not result.converged:
            nonconverged += 1
        if not geom.contains_particle_center(result.x_m, result.u_m, radius_m):
            support_violations += 1
        if _wall_min_constraint_m(geom, result.x_m, result.u_m, radius_m) <= EXACT_ATOM_EPS_M:
            exact_boundary_atoms += 1
        if result.active_wall_ids:
            reflected_steps += 1
        if len(result.active_wall_ids) > 1:
            multiwall_steps += 1
        iteration_counts.append(result.iteration_count)
        reflection_displacement_nm.append(result.reflection_displacement_m * 1.0e9)
        final_u.append(gate30_31._u_accessible_cdf(geom, result.u_m, radius_m))
        final_x.append(gate30_31._x_local_norm(geom, result.x_m, result.u_m, radius_m))

    initial_u_hist = _histogram(initial_u, HISTOGRAM_BINS, 0.0, 1.0)
    initial_x_hist = _histogram(initial_x, HISTOGRAM_BINS, -1.0, 1.0)
    final_u_hist = _histogram(final_u, HISTOGRAM_BINS, 0.0, 1.0)
    final_x_hist = _histogram(final_x, HISTOGRAM_BINS, -1.0, 1.0)

    scenario_id = str(scenario["scenario_id"])
    seed_id = f"{scenario_id}_seed{seed}"
    metric_row = {
        "scenario_seed_id": seed_id,
        "scenario_id": scenario_id,
        "seed": str(seed),
        "theta_comsol_deg": fmt(float(scenario["theta"])),
        "depth_nm": fmt(float(scenario["depth"])),
        "particle_radius_nm": fmt(float(scenario["radius"])),
        "n_independent_samples": str(N_INDEPENDENT_SAMPLES_PER_SEED),
        "dt_s": fmt(DT_S),
        "diffusion_m2_s": fmt(DIFFUSION_M2_S),
        "brownian_sigma_nm": fmt(sigma_m * 1.0e9),
        "initial_u_accessible_cdf_l1_to_uniform": fmt(_l1_to_uniform(initial_u_hist)),
        "initial_x_local_norm_l1_to_uniform": fmt(_l1_to_uniform(initial_x_hist)),
        "final_u_accessible_cdf_l1_to_uniform": fmt(_l1_to_uniform(final_u_hist)),
        "final_x_local_norm_l1_to_uniform": fmt(_l1_to_uniform(final_x_hist)),
        "final_vs_initial_u_hist_l1": fmt(_histogram_l1(final_u_hist, initial_u_hist)),
        "final_vs_initial_x_hist_l1": fmt(_histogram_l1(final_x_hist, initial_x_hist)),
        "support_violation_count": str(support_violations),
        "exact_boundary_atom_count": str(exact_boundary_atoms),
        "nonconverged_reflection_count": str(nonconverged),
        "reflected_step_fraction": fmt(reflected_steps / N_INDEPENDENT_SAMPLES_PER_SEED),
        "multiwall_step_fraction": fmt(multiwall_steps / N_INDEPENDENT_SAMPLES_PER_SEED),
        "max_reflection_iterations": str(max(iteration_counts) if iteration_counts else 0),
        "max_reflection_displacement_nm": fmt(max(reflection_displacement_nm) if reflection_displacement_nm else 0.0),
        "independent_ensemble_ess": str(N_INDEPENDENT_SAMPLES_PER_SEED),
        "ess_method": "independent_uniform_initial_ensemble_no_autocorrelation",
        "transition_invariance_status": "candidate_transition_invariance_not_proof",
        "claim_boundary": CLAIM_BOUNDARY,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    histogram_rows: list[dict[str, str]] = []
    histogram_specs = (
        ("initial", "u_accessible_cdf", 0.0, 1.0, initial_u_hist),
        ("initial", "x_local_norm", -1.0, 1.0, initial_x_hist),
        ("final_after_one_reflected_step", "u_accessible_cdf", 0.0, 1.0, final_u_hist),
        ("final_after_one_reflected_step", "x_local_norm", -1.0, 1.0, final_x_hist),
    )
    bin_widths = {
        "u_accessible_cdf": 1.0 / HISTOGRAM_BINS,
        "x_local_norm": 2.0 / HISTOGRAM_BINS,
    }
    lows = {"u_accessible_cdf": 0.0, "x_local_norm": -1.0}
    for stage, basis, _low, _high, hist in histogram_specs:
        for bin_idx, fraction in enumerate(hist):
            low = lows[basis] + bin_idx * bin_widths[basis]
            high = low + bin_widths[basis]
            histogram_rows.append(
                {
                    "scenario_seed_id": seed_id,
                    "scenario_id": scenario_id,
                    "seed": str(seed),
                    "stage": stage,
                    "basis": basis,
                    "bin_index": str(bin_idx),
                    "bin_low": fmt(low),
                    "bin_high": fmt(high),
                    "fraction": fmt(fraction),
                    "expected_uniform_fraction": fmt(1.0 / HISTOGRAM_BINS),
                    "claim_boundary": CLAIM_BOUNDARY,
                    "allowed_use": ALLOWED_USE,
                    "blocked_use": BLOCKED_USE,
                }
            )
    return metric_row, histogram_rows


def stationarity_rows() -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
]:
    scenario_seed_rows: list[dict[str, str]] = []
    histogram_rows: list[dict[str, str]] = []
    for scenario_idx, scenario in enumerate(SCENARIOS):
        for seed in SEEDS:
            scenario_seed = seed + scenario_idx * 1000
            metric_row, metric_histograms = _simulate_scenario_seed(scenario, scenario_seed)
            scenario_seed_rows.append(metric_row)
            histogram_rows.extend(metric_histograms)

    ci_rows: list[dict[str, str]] = []
    for scenario in SCENARIOS:
        scenario_id = str(scenario["scenario_id"])
        subset = [row for row in scenario_seed_rows if row["scenario_id"] == scenario_id]
        ci_rows.append(
            _ci_row(
                scenario_id,
                "u_accessible_cdf",
                [float(row["final_u_accessible_cdf_l1_to_uniform"]) for row in subset],
                proof_line=PROOF_L1_HARD_LINE,
            )
        )
        ci_rows.append(
            _ci_row(
                scenario_id,
                "x_local_norm",
                [float(row["final_x_local_norm_l1_to_uniform"]) for row in subset],
                proof_line=PROOF_L1_HARD_LINE,
            )
        )
    return scenario_seed_rows, histogram_rows, ci_rows


def build_payload() -> dict[str, Any]:
    scenario_seed_rows, histogram_rows, ci_rows = stationarity_rows()
    sources = source_lock_rows()
    firewall = no_proof_firewall_rows()
    max_final_u_l1 = max(
        float(row["final_u_accessible_cdf_l1_to_uniform"]) for row in scenario_seed_rows
    )
    max_final_x_l1 = max(
        float(row["final_x_local_norm_l1_to_uniform"]) for row in scenario_seed_rows
    )
    max_ci_upper = max(float(row["ci95_upper_l1"]) for row in ci_rows)
    min_independent_ess = min(float(row["independent_ensemble_ess"]) for row in scenario_seed_rows)
    support_violations = sum(int(row["support_violation_count"]) for row in scenario_seed_rows)
    exact_atoms = sum(int(row["exact_boundary_atom_count"]) for row in scenario_seed_rows)
    nonconverged = sum(int(row["nonconverged_reflection_count"]) for row in scenario_seed_rows)
    stationarity_status = (
        "candidate_numeric_stationarity_lines_met_not_proof_registered"
        if (
            max_final_u_l1 <= PROOF_L1_HARD_LINE
            and max_final_x_l1 <= PROOF_L1_HARD_LINE
            and min_independent_ess >= PROOF_MIN_INDEPENDENT_SAMPLE_SIZE
            and support_violations == 0
            and nonconverged == 0
        )
        else "candidate_stationarity_review_required"
    )
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "build_head": safe_git_head(),
        "scenario_seed_rows": len(scenario_seed_rows),
        "scenario_group_rows": len(SCENARIOS),
        "histogram_rows": len(histogram_rows),
        "confidence_interval_rows": len(ci_rows),
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(row["exists"] != "true" for row in sources),
        "n_independent_samples_per_seed": N_INDEPENDENT_SAMPLES_PER_SEED,
        "seed_count_per_scenario": len(SEEDS),
        "total_independent_samples": N_INDEPENDENT_SAMPLES_PER_SEED
        * len(SEEDS)
        * len(SCENARIOS),
        "min_independent_ensemble_ess": min_independent_ess,
        "max_final_u_accessible_cdf_l1_to_uniform": max_final_u_l1,
        "max_final_x_local_norm_l1_to_uniform": max_final_x_l1,
        "max_ci95_upper_l1": max_ci_upper,
        "proof_l1_hard_line": PROOF_L1_HARD_LINE,
        "proof_l1_target": PROOF_L1_TARGET,
        "support_violation_count": support_violations,
        "exact_boundary_atom_count": exact_atoms,
        "nonconverged_reflection_count": nonconverged,
        "stationarity_ensemble_status": stationarity_status,
        "proof_readiness_impact": (
            "stationarity_ess_and_u_x_uniformity_gaps_reduced_by_independent_ensemble_candidate"
        ),
        "reviewed_commit_binding_status": "pending_future_authorization_not_clean_head_bound",
        "github_visibility_status": GITHUB_VISIBILITY_STATUS,
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
        "scenario_seed_rows": scenario_seed_rows,
        "histogram_rows": histogram_rows,
        "confidence_interval_rows": ci_rows,
        "source_locks": sources,
        "no_proof_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "Scenario rows": s["scenario_seed_rows"] == len(SCENARIOS) * len(SEEDS),
        "Histogram rows": s["histogram_rows"]
        == len(SCENARIOS) * len(SEEDS) * 4 * HISTOGRAM_BINS,
        "CI rows": s["confidence_interval_rows"] == len(SCENARIOS) * 2,
        "Source lock complete": s["source_missing_rows"] == 0,
        "Independent ESS line": s["min_independent_ensemble_ess"]
        >= PROOF_MIN_INDEPENDENT_SAMPLE_SIZE,
        "u L1 line": s["max_final_u_accessible_cdf_l1_to_uniform"] <= PROOF_L1_HARD_LINE,
        "x L1 line": s["max_final_x_local_norm_l1_to_uniform"] <= PROOF_L1_HARD_LINE,
        "Support invariant": s["support_violation_count"] == 0,
        "No exact boundary atoms": s["exact_boundary_atom_count"] == 0,
        "No nonconvergence": s["nonconverged_reflection_count"] == 0,
        "Status no proof": s["stationarity_ensemble_status"].endswith(
            "_not_proof_registered"
        ),
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
            "policy_impact": "stationarity_ensemble_refinement_no_proof_registration",
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
        "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_SCENARIO_METRICS_20260701.csv": payload[
            "scenario_seed_rows"
        ],
        "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_HISTOGRAMS_20260701.csv": payload[
            "histogram_rows"
        ],
        "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_CONFIDENCE_INTERVALS_20260701.csv": payload[
            "confidence_interval_rows"
        ],
        "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_SOURCE_LOCK_20260701.csv": payload[
            "source_locks"
        ],
        "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_NO_PROOF_FIREWALL_20260701.csv": payload[
            "no_proof_firewall"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    status_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_STATUS_20260701.json"
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

    active_report = active_output_dir / "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_REPORT_20260701.md"
    write_md(
        active_report,
        "NODI COMSOL Package C Stationarity Ensemble Refinement",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Scenario-seed rows: `{payload['summary']['scenario_seed_rows']}`.",
            f"- Total independent samples: `{payload['summary']['total_independent_samples']}`.",
            f"- Max final u L1: `{payload['summary']['max_final_u_accessible_cdf_l1_to_uniform']}`.",
            f"- Max final x-local L1: `{payload['summary']['max_final_x_local_norm_l1_to_uniform']}`.",
            f"- Stationarity ensemble status: `{payload['summary']['stationarity_ensemble_status']}`.",
            "- Boundary: independent-ensemble candidate evidence only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no numeric PRS/EAS, no route/yield/detection/wet/fab/production claims.",
        ],
    )
    generated.append(active_report)

    public_report = active_report_dir / "511_NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_REFINEMENT_20260701.md"
    write_md(
        public_report,
        "NODI COMSOL Package C Stationarity Ensemble Refinement",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Source head: `{payload['summary']['build_head']}`",
            "- This packet checks one-step transition invariance from analytically uniform particle-center support using independent ensemble samples.",
            f"- Scenario-seed rows: `{payload['summary']['scenario_seed_rows']}`.",
            f"- Total independent samples: `{payload['summary']['total_independent_samples']}`.",
            f"- Min independent ensemble ESS: `{payload['summary']['min_independent_ensemble_ess']}`.",
            f"- Max final u-accessible-CDF L1 to uniform: `{payload['summary']['max_final_u_accessible_cdf_l1_to_uniform']}`.",
            f"- Max final x-local-norm L1 to uniform: `{payload['summary']['max_final_x_local_norm_l1_to_uniform']}`.",
            f"- Max CI95 upper L1: `{payload['summary']['max_ci95_upper_l1']}`.",
            f"- Stationarity ensemble status: `{payload['summary']['stationarity_ensemble_status']}`.",
            f"- GitHub visibility: `{payload['summary']['github_visibility_status']}`.",
            "- Boundary: this is proof-gap reduction evidence only, not Package C proof registration or runtime authorization.",
            f"- Machine-readable support: `{rel(active_output_dir)}`.",
        ],
    )
    generated.append(public_report)

    manifest_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_MANIFEST_20260701.csv"
    report_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_REPORT_20260701.json"
    report_outputs = [path.name for path in generated] + [report_path.name, manifest_path.name]
    write_json_atomic(report_path, {"summary": payload["summary"], "outputs": report_outputs})
    generated.append(report_path)
    write_csv_rows(
        manifest_path,
        artifact_manifest_rows(generated, self_manifest_path=manifest_path),
    )
    return {"status": status_path, "report": report_path, "manifest": manifest_path}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_package_c_stationarity_ensemble_refinement:
        parser.error("--confirm-package-c-stationarity-ensemble-refinement is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_PACKAGE_C_STATIONARITY_ENSEMBLE_REFINEMENT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
