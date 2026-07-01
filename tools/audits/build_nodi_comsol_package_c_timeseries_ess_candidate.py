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

EXPECTED_CONSOLIDATION_DISPOSITION = (
    "NODI_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
DISPOSITION = "NODI_PACKAGE_C_TIMESERIES_ESS_CANDIDATE_READY_NO_PROOF_REGISTRATION"
ARTIFACT_ID = "PACKAGE_C_TIMESERIES_ESS_CANDIDATE_20260701"
CLAIM_BOUNDARY = (
    "timeseries_ess_candidate_not_package_c_proof_registered_not_runtime"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

ALLOWED_USE = (
    "Package C long-run timeseries ESS/autocorrelation candidate;proof-gap hardening design;"
    "substep guard planning;no-proof-registration"
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

CONSOLIDATION_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_STATUS_20260701.json"
)
CONSOLIDATION_EVIDENCE_INDEX = (
    OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_EVIDENCE_INDEX_20260701.csv"
)
CONSOLIDATION_READINESS = (
    OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_READINESS_CRITERIA_20260701.csv"
)
CONSOLIDATION_FIREWALL = (
    OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_NO_PROOF_FIREWALL_20260701.csv"
)

SOURCE_FILES = {
    "consolidation_status": CONSOLIDATION_STATUS,
    "consolidation_evidence_index": CONSOLIDATION_EVIDENCE_INDEX,
    "consolidation_readiness_criteria": CONSOLIDATION_READINESS,
    "consolidation_no_proof_firewall": CONSOLIDATION_FIREWALL,
    "cross_section_geometry": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
    "gate30_31_metric_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate.py",
    "timeseries_ess_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_package_c_timeseries_ess_candidate.py",
    "timeseries_ess_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_package_c_timeseries_ess_candidate.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}

SCENARIOS = (
    {"scenario_id": "rect_limit_theta90_D900_r20", "theta": 90.0, "depth": 900.0, "radius": 20.0, "seed": 42101},
    {"scenario_id": "moderate_theta85_D900_r110", "theta": 85.0, "depth": 900.0, "radius": 110.0, "seed": 42102},
    {"scenario_id": "deep_tail_theta85_D1200_r150", "theta": 85.0, "depth": 1200.0, "radius": 150.0, "seed": 42103},
    {"scenario_id": "steep_theta80_D900_r75", "theta": 80.0, "depth": 900.0, "radius": 75.0, "seed": 42104},
    {"scenario_id": "stress_theta70_D900_r20", "theta": 70.0, "depth": 900.0, "radius": 20.0, "seed": 42105},
    {"scenario_id": "narrow_tail_theta70_D900_r150", "theta": 70.0, "depth": 900.0, "radius": 150.0, "seed": 42106},
)

N_STEPS = 65536
BURN_IN_STEPS = 8192
SAMPLE_STRIDE = 8
DT_S = 2.5e-5
DIFFUSION_M2_S = 4.0e-12
MAX_AUTOCORR_LAG = 128
AUTOCORR_LAGS = (1, 2, 4, 8, 16, 32, 64, 128)
EXACT_ATOM_EPS_NM = 1.0e-9
EQUILIBRIUM_L1_CANDIDATE_THRESHOLD = 0.30
MIN_ESS_CANDIDATE_FLOOR = 20.0
SUBSTEP_RMS_OVER_GAP_REVIEW_LINE = 1.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Package C timeseries ESS/autocorrelation candidate artifacts."
    )
    parser.add_argument(
        "--confirm-package-c-timeseries-ess-candidate",
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


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    return sum((value - mean) ** 2 for value in values) / len(values)


def _autocorrelation(values: list[float], lag: int) -> float:
    if lag <= 0 or lag >= len(values):
        return 0.0
    mean = _mean(values)
    denom = sum((value - mean) ** 2 for value in values)
    if denom <= 0.0:
        return 0.0
    numer = sum(
        (values[idx] - mean) * (values[idx + lag] - mean)
        for idx in range(len(values) - lag)
    )
    return numer / denom


def _ess(values: list[float]) -> tuple[float, float, int, float]:
    if len(values) < 4 or _variance(values) <= 0.0:
        return float(len(values)), 1.0, 0, 0.0
    rho_sum = 0.0
    last_positive_lag = 0
    lag1 = _autocorrelation(values, 1)
    for lag in range(1, min(MAX_AUTOCORR_LAG, len(values) - 1) + 1):
        rho = _autocorrelation(values, lag)
        if rho <= 0.0:
            break
        rho_sum += rho
        last_positive_lag = lag
    integrated_autocorr_time = max(1.0 + 2.0 * rho_sum, 1.0)
    return (
        len(values) / integrated_autocorr_time,
        integrated_autocorr_time,
        last_positive_lag,
        lag1,
    )


def _l1_to_uniform(histogram: list[float]) -> float:
    expected = 1.0 / len(histogram) if histogram else 0.0
    return sum(abs(value - expected) for value in histogram)


def _simulate_timeseries(scenario: dict[str, Any]) -> dict[str, Any]:
    geom = gate30_31._geom(float(scenario["theta"]), float(scenario["depth"]))
    radius_m = gate30_31._m(float(scenario["radius"]))
    rng = random.Random(int(scenario["seed"]))
    x_m, u_m = geom.sample_particle_center_uniform(rng.random(), rng.random(), radius_m)
    sigma_m = math.sqrt(2.0 * DIFFUSION_M2_S * DT_S)

    support_violations = 0
    exact_atoms = 0
    nonconverged = 0
    reflected_steps = 0
    multiwall_steps = 0
    iteration_counts: list[int] = []
    reflection_displacements_nm: list[float] = []
    surface_gaps_nm: list[float] = []
    retained = {
        "u_accessible_cdf": [],
        "x_local_norm": [],
        "surface_gap_nm": [],
    }

    for step_idx in range(N_STEPS):
        trial_x = x_m + rng.gauss(0.0, sigma_m)
        trial_u = u_m + rng.gauss(0.0, sigma_m)
        result = geom.reflect_particle_center_step_with_diagnostics(
            trial_x,
            trial_u,
            radius_m,
            max_iterations=gate30_31.MAX_REFLECTION_ITERATIONS,
            tolerance_m=gate30_31.TOLERANCE_M,
        )
        x_m = result.x_m
        u_m = result.u_m
        if not result.converged:
            nonconverged += 1
        if result.reflection_displacement_m > 0.0:
            reflected_steps += 1
        if len(set(result.active_wall_ids)) >= 2:
            multiwall_steps += 1
        iteration_counts.append(result.iteration_count)
        reflection_displacements_nm.append(gate30_31._nm(result.reflection_displacement_m))
        if not geom.contains_particle_center(
            x_m,
            u_m,
            radius_m,
            tolerance_m=gate30_31.TOLERANCE_M,
        ):
            support_violations += 1
        diagnostics = geom.particle_wall_gap_diagnostics_m(x_m, u_m, radius_m)
        surface_gap_nm = gate30_31._nm(float(diagnostics["surface_gap_for_particle_m"]))
        surface_gaps_nm.append(surface_gap_nm)
        if abs(surface_gap_nm) <= EXACT_ATOM_EPS_NM:
            exact_atoms += 1
        if step_idx >= BURN_IN_STEPS and (step_idx - BURN_IN_STEPS) % SAMPLE_STRIDE == 0:
            retained["u_accessible_cdf"].append(
                gate30_31._u_accessible_cdf(geom, u_m, radius_m)
            )
            retained["x_local_norm"].append(gate30_31._x_local_norm(geom, x_m, u_m, radius_m))
            retained["surface_gap_nm"].append(surface_gap_nm)

    u_hist = gate30_31._histogram(retained["u_accessible_cdf"], 10, 0.0, 1.0)
    x_hist = gate30_31._histogram(retained["x_local_norm"], 10, -1.0, 1.0)
    scenario_summary = {
        "scenario_id": str(scenario["scenario_id"]),
        "theta_deg_comsol": str(scenario["theta"]),
        "depth_nm": str(scenario["depth"]),
        "particle_radius_nm": str(scenario["radius"]),
        "rng_seed": str(scenario["seed"]),
        "n_steps": str(N_STEPS),
        "burn_in_steps": str(BURN_IN_STEPS),
        "sample_stride": str(SAMPLE_STRIDE),
        "retained_samples": str(len(retained["u_accessible_cdf"])),
        "dt_s": str(DT_S),
        "diffusion_m2_s": str(DIFFUSION_M2_S),
        "brownian_rms_step_nm": str(round(gate30_31._nm(sigma_m), 9)),
        "support_violation_count": str(support_violations),
        "exact_boundary_atom_fraction_all_steps": str(round(exact_atoms / N_STEPS, 9)),
        "nonconverged_reflection_count": str(nonconverged),
        "reflected_step_fraction": str(round(reflected_steps / N_STEPS, 9)),
        "multiwall_active_set_fraction": str(round(multiwall_steps / N_STEPS, 9)),
        "reflection_iteration_count_p99": str(round(_quantile(iteration_counts, 0.99), 9)),
        "reflection_displacement_nm_p99": str(round(_quantile(reflection_displacements_nm, 0.99), 9)),
        "surface_gap_nm_p05": str(round(_quantile(surface_gaps_nm, 0.05), 9)),
        "surface_gap_nm_p50": str(round(_quantile(surface_gaps_nm, 0.50), 9)),
        "u_accessible_cdf_l1_to_uniform": str(round(_l1_to_uniform(u_hist), 9)),
        "x_local_norm_l1_to_uniform": str(round(_l1_to_uniform(x_hist), 9)),
        "u_accessible_cdf_histogram_json": json.dumps(u_hist),
        "x_local_norm_histogram_json": json.dumps(x_hist),
        "timeseries_candidate_status": "candidate_metric_only_not_proof",
        "claim_boundary": CLAIM_BOUNDARY,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    ess_rows: list[dict[str, str]] = []
    autocorr_rows: list[dict[str, str]] = []
    for observable, values in retained.items():
        ess, tau, last_lag, lag1 = _ess(values)
        ess_rows.append(
            {
                "scenario_id": str(scenario["scenario_id"]),
                "observable": observable,
                "retained_samples": str(len(values)),
                "effective_sample_size": str(round(ess, 9)),
                "ess_fraction": str(round(ess / max(len(values), 1), 9)),
                "integrated_autocorrelation_time": str(round(tau, 9)),
                "last_positive_autocorrelation_lag": str(last_lag),
                "lag1_autocorrelation": str(round(lag1, 9)),
                "ess_method": "initial_positive_autocorrelation_sequence_candidate",
                "autocorrelation_status": "timeseries_candidate_metric_not_proof",
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
        for lag in AUTOCORR_LAGS:
            autocorr_rows.append(
                {
                    "scenario_id": str(scenario["scenario_id"]),
                    "observable": observable,
                    "lag": str(lag),
                    "autocorrelation": str(round(_autocorrelation(values, lag), 9)),
                    "retained_samples": str(len(values)),
                    "claim_boundary": CLAIM_BOUNDARY,
                    "allowed_use": ALLOWED_USE,
                    "blocked_use": BLOCKED_USE,
                }
            )
    surface_gap_p05 = float(scenario_summary["surface_gap_nm_p05"])
    rms_nm = float(scenario_summary["brownian_rms_step_nm"])
    ratio = rms_nm / surface_gap_p05 if surface_gap_p05 > 0.0 else float("inf")
    if ratio > SUBSTEP_RMS_OVER_GAP_REVIEW_LINE:
        guard_status = "future_runtime_substep_or_smaller_dt_review_required"
    else:
        guard_status = "future_runtime_no_substep_trigger_from_candidate"
    substep_row = {
        "scenario_id": str(scenario["scenario_id"]),
        "brownian_rms_step_nm": scenario_summary["brownian_rms_step_nm"],
        "surface_gap_nm_p05": scenario_summary["surface_gap_nm_p05"],
        "rms_step_over_surface_gap_p05": str(round(ratio, 9)),
        "substep_guard_candidate_status": guard_status,
        "substep_policy_scope": "design_guard_only_not_runtime",
        "runtime_policy_authorized": "false",
        "claim_boundary": CLAIM_BOUNDARY,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    return {
        "scenario_summary": scenario_summary,
        "ess_rows": ess_rows,
        "autocorr_rows": autocorr_rows,
        "substep_row": substep_row,
    }


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
            "firewall_status": "PASS_PACKAGE_C_TIMESERIES_ESS_CANDIDATE_NO_PROOF_REGISTRATION",
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
    consolidation_summary = read_json(CONSOLIDATION_STATUS).get("summary", {})
    scenario_rows: list[dict[str, str]] = []
    ess_rows: list[dict[str, str]] = []
    autocorr_rows: list[dict[str, str]] = []
    substep_rows: list[dict[str, str]] = []
    for scenario in SCENARIOS:
        result = _simulate_timeseries(scenario)
        scenario_rows.append(result["scenario_summary"])
        ess_rows.extend(result["ess_rows"])
        autocorr_rows.extend(result["autocorr_rows"])
        substep_rows.append(result["substep_row"])
    source_rows = source_lock_rows()
    firewall = no_proof_firewall_rows()
    min_ess = min((float(row["effective_sample_size"]) for row in ess_rows), default=0.0)
    max_u_l1 = max((float(row["u_accessible_cdf_l1_to_uniform"]) for row in scenario_rows), default=0.0)
    max_x_l1 = max((float(row["x_local_norm_l1_to_uniform"]) for row in scenario_rows), default=0.0)
    max_exact_atom = max(
        (float(row["exact_boundary_atom_fraction_all_steps"]) for row in scenario_rows),
        default=0.0,
    )
    substep_review_rows = sum(
        row["substep_guard_candidate_status"]
        == "future_runtime_substep_or_smaller_dt_review_required"
        for row in substep_rows
    )
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "build_head": safe_git_head(),
        "consolidation_disposition": consolidation_summary.get("disposition", ""),
        "scenario_rows": len(scenario_rows),
        "observable_ess_rows": len(ess_rows),
        "autocorrelation_rows": len(autocorr_rows),
        "substep_policy_rows": len(substep_rows),
        "source_lock_rows": len(source_rows),
        "source_missing_rows": sum(row["exists"] != "true" for row in source_rows),
        "n_steps_per_scenario": N_STEPS,
        "burn_in_steps": BURN_IN_STEPS,
        "sample_stride": SAMPLE_STRIDE,
        "retained_samples_per_scenario": (N_STEPS - BURN_IN_STEPS + SAMPLE_STRIDE - 1)
        // SAMPLE_STRIDE,
        "min_effective_sample_size": round(min_ess, 9),
        "max_u_accessible_cdf_l1_to_uniform": round(max_u_l1, 9),
        "max_x_local_norm_l1_to_uniform": round(max_x_l1, 9),
        "max_exact_boundary_atom_fraction_all_steps": round(max_exact_atom, 9),
        "support_violation_rows": sum(
            int(row["support_violation_count"]) > 0 for row in scenario_rows
        ),
        "nonconverged_reflection_rows": sum(
            int(row["nonconverged_reflection_count"]) > 0 for row in scenario_rows
        ),
        "substep_review_rows": substep_review_rows,
        "timeseries_ess_candidate_status": "candidate_artifact_complete_not_proof",
        "proof_readiness_impact": "timeseries_ess_gap_reduced_but_not_proof_registered",
        "stationarity_review_required": True,
        "substep_policy_review_required": substep_review_rows > 0,
        "reviewed_commit_binding_status": "pending_future_authorization_not_clean_head_bound",
        "github_visibility_status": "artifact_generated_from_local_worktree_pre_commit",
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
        "scenario_summary": scenario_rows,
        "observable_ess": ess_rows,
        "autocorrelation": autocorr_rows,
        "substep_policy": substep_rows,
        "source_locks": source_rows,
        "no_proof_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "Consolidation disposition": s["consolidation_disposition"]
        == EXPECTED_CONSOLIDATION_DISPOSITION,
        "Scenario count": s["scenario_rows"] == len(SCENARIOS),
        "ESS row count": s["observable_ess_rows"] == len(SCENARIOS) * 3,
        "Autocorrelation row count": s["autocorrelation_rows"]
        == len(SCENARIOS) * 3 * len(AUTOCORR_LAGS),
        "Substep rows": s["substep_policy_rows"] == len(SCENARIOS),
        "Source lock complete": s["source_missing_rows"] == 0,
        "Support invariant": s["support_violation_rows"] == 0,
        "Reflection convergence": s["nonconverged_reflection_rows"] == 0,
        "No exact atoms": s["max_exact_boundary_atom_fraction_all_steps"] == 0.0,
        "ESS finite": s["min_effective_sample_size"] >= MIN_ESS_CANDIDATE_FLOOR,
        "Stationarity review remains required": s["stationarity_review_required"] is True,
        "Substep review remains required": s["substep_policy_review_required"] is True,
        "Clean commit binding pending": s["reviewed_commit_binding_status"]
        == "pending_future_authorization_not_clean_head_bound",
        "U marginal candidate distance": s["max_u_accessible_cdf_l1_to_uniform"]
        <= EQUILIBRIUM_L1_CANDIDATE_THRESHOLD,
        "X local norm candidate distance": s["max_x_local_norm_l1_to_uniform"]
        <= EQUILIBRIUM_L1_CANDIDATE_THRESHOLD,
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
            "policy_impact": "timeseries_ess_candidate_only_no_proof_registration",
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
        "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_SCENARIO_SUMMARY_20260701.csv": payload[
            "scenario_summary"
        ],
        "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_OBSERVABLE_ESS_20260701.csv": payload[
            "observable_ess"
        ],
        "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_AUTOCORRELATION_20260701.csv": payload[
            "autocorrelation"
        ],
        "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_SUBSTEP_POLICY_20260701.csv": payload[
            "substep_policy"
        ],
        "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_SOURCE_LOCK_20260701.csv": payload[
            "source_locks"
        ],
        "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_NO_PROOF_FIREWALL_20260701.csv": payload[
            "no_proof_firewall"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    status_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_STATUS_20260701.json"
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

    active_report = (
        active_output_dir / "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_REPORT_20260701.md"
    )
    write_md(
        active_report,
        "NODI COMSOL Package C Timeseries ESS Candidate",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Scenario rows: {payload['summary']['scenario_rows']}; observable ESS rows: {payload['summary']['observable_ess_rows']}.",
            f"- Autocorrelation rows: {payload['summary']['autocorrelation_rows']}; substep policy rows: {payload['summary']['substep_policy_rows']}.",
            f"- Min ESS: `{payload['summary']['min_effective_sample_size']}`.",
            f"- Max u L1-to-uniform: `{payload['summary']['max_u_accessible_cdf_l1_to_uniform']}`; max x-local L1-to-uniform: `{payload['summary']['max_x_local_norm_l1_to_uniform']}`.",
            f"- Substep review rows: `{payload['summary']['substep_review_rows']}`.",
            f"- Stationarity review required: `{payload['summary']['stationarity_review_required']}`; substep policy review required: `{payload['summary']['substep_policy_review_required']}`.",
            f"- Reviewed commit binding: `{payload['summary']['reviewed_commit_binding_status']}`.",
            "- Boundary: timeseries ESS candidate only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no numeric PRS/EAS, no route/yield/detection/wet/fab/production claims.",
        ],
    )
    generated.append(active_report)

    public_report = active_report_dir / "505_NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_CANDIDATE_20260701.md"
    write_md(
        public_report,
        "NODI COMSOL Package C Timeseries ESS Candidate",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Source head: `{payload['summary']['build_head']}`",
            "- This packet reduces the consolidation `timeseries_ess` proof gap with long-chain autocorrelation and ESS candidate evidence.",
            f"- Scenario rows: {payload['summary']['scenario_rows']}; observable ESS rows: {payload['summary']['observable_ess_rows']}; autocorrelation rows: {payload['summary']['autocorrelation_rows']}.",
            f"- Min effective sample size: `{payload['summary']['min_effective_sample_size']}`.",
            f"- Max exact boundary atom fraction across all steps: `{payload['summary']['max_exact_boundary_atom_fraction_all_steps']}`.",
            f"- Substep guard review rows: `{payload['summary']['substep_review_rows']}`; this is a design guard only, not runtime policy.",
            f"- Stationarity review required: `{payload['summary']['stationarity_review_required']}`; reviewed commit binding status: `{payload['summary']['reviewed_commit_binding_status']}`.",
            "- Boundary: this is not a Package C proof/pass registration and does not authorize runtime, numeric PRS/EAS, COMSOL, .mph, solver, wet, route, yield, detection, fabrication, or production claims.",
            f"- Machine-readable support: `{rel(active_output_dir)}`.",
        ],
    )
    generated.append(public_report)

    manifest_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_MANIFEST_20260701.csv"
    report_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_REPORT_20260701.json"
    report_outputs = [path.name for path in generated] + [report_path.name, manifest_path.name]
    write_json_atomic(
        report_path,
        {"summary": payload["summary"], "outputs": report_outputs},
    )
    generated.append(report_path)
    write_csv_rows(
        manifest_path,
        artifact_manifest_rows(generated, self_manifest_path=manifest_path),
    )
    return {"status": status_path, "report": report_path, "manifest": manifest_path}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_package_c_timeseries_ess_candidate:
        parser.error("--confirm-package-c-timeseries-ess-candidate is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_PACKAGE_C_TIMESERIES_ESS_CANDIDATE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
