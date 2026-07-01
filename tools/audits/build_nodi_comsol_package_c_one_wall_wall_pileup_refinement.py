#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
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
    build_nodi_comsol_gate37_sidewall_package_c_metric_hardening_candidate as gate37,
    build_nodi_comsol_gate38_sidewall_wall_pileup_refinement_candidate as gate38,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"

DISPOSITION = (
    "NODI_PACKAGE_C_ONE_WALL_WALL_PILEUP_REFINEMENT_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
ARTIFACT_ID = "PACKAGE_C_ONE_WALL_WALL_PILEUP_REFINEMENT_20260701"
CLAIM_BOUNDARY = (
    "one_wall_wall_pileup_refinement_candidate_not_package_c_proof_registered_not_runtime"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
GITHUB_VISIBILITY_STATUS = "local_worktree_pre_commit_urls_valid_after_publish"

ALLOWED_USE = (
    "Package C one-wall and wall-pileup refinement candidate;"
    "proof-threshold gap reduction evidence;no-proof-registration"
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

STATIONARITY_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_STATUS_20260701.json"
)
GATE37_ONE_WALL = (
    PROJECT_ROOT
    / "reports/joint_interface_20260630/NODI_COMSOL_GATE37_SIDEWALL_ONE_WALL_FOLDED_NORMAL_SUITE_20260630.csv"
)
GATE38_WALL_PILEUP = (
    OUTPUT_DIR / "NODI_COMSOL_GATE38_SIDEWALL_WALL_PILEUP_REFINEMENT_20260701.csv"
)
PROOF_THRESHOLD_TABLE = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_TABLE_20260701.csv"
)

SOURCE_FILES = {
    "stationarity_status": STATIONARITY_STATUS,
    "gate37_one_wall_suite": GATE37_ONE_WALL,
    "gate38_wall_pileup_refinement": GATE38_WALL_PILEUP,
    "proof_threshold_table": PROOF_THRESHOLD_TABLE,
    "cross_section_geometry": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
    "gate37_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate37_sidewall_package_c_metric_hardening_candidate.py",
    "gate38_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate38_sidewall_wall_pileup_refinement_candidate.py",
    "one_wall_wall_pileup_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_package_c_one_wall_wall_pileup_refinement.py",
    "one_wall_wall_pileup_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_package_c_one_wall_wall_pileup_refinement.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}

D_OVER_SIGMA_GRID = (0.0, 0.25, 0.5, 1.0, 2.0, 4.0)
ONE_WALL_SAMPLE_COUNT = 65536
ONE_WALL_PROOF_KS_HARD_LINE = 0.01
WALL_PILEUP_SAMPLE_COUNT = 65536
WALL_PILEUP_PROOF_RATIO_HARD_LINE = 1.25


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Package C one-wall and wall-pileup proof-threshold refinement artifacts."
    )
    parser.add_argument(
        "--confirm-package-c-one-wall-wall-pileup-refinement",
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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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
            "firewall_status": "PASS_PACKAGE_C_ONE_WALL_WALL_PILEUP_NO_PROOF_REGISTRATION",
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


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _variance(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = _mean(values)
    return sum((value - mean) ** 2 for value in values) / len(values)


def one_wall_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for d_over_sigma in D_OVER_SIGMA_GRID:
        rng = random.Random(512370 + int(round(d_over_sigma * 1000.0)))
        normals = [rng.gauss(0.0, 1.0) for _ in range(ONE_WALL_SAMPLE_COUNT)]
        tangential = [rng.gauss(0.0, 1.0) for _ in range(ONE_WALL_SAMPLE_COUNT)]
        samples = [abs(d_over_sigma + z_value) for z_value in normals]
        ks_distance = gate37._ks_distance(
            samples,
            lambda value, d=d_over_sigma: gate37._reflecting_one_wall_cdf(value, d),
        )
        exact_atom_fraction = sum(abs(sample) <= 1.0e-15 for sample in samples) / len(samples)
        tangential_variance_error = abs(_variance(tangential) - 1.0)
        rows.append(
            {
                "method": "folded_normal_mirror_positive_control",
                "d_over_sigma": fmt(d_over_sigma),
                "n_samples": str(ONE_WALL_SAMPLE_COUNT),
                "ks_distance_to_reflecting_kernel": fmt(ks_distance),
                "proof_ks_hard_line": fmt(ONE_WALL_PROOF_KS_HARD_LINE),
                "exact_boundary_atom_fraction": fmt(exact_atom_fraction),
                "tangential_variance_error_abs": fmt(tangential_variance_error),
                "candidate_status": (
                    "candidate_and_proof_threshold_met_not_registered"
                    if ks_distance <= ONE_WALL_PROOF_KS_HARD_LINE and exact_atom_fraction == 0.0
                    else "candidate_proof_threshold_review_required"
                ),
                "source_control_note": "negative controls inherited from Gate37 source artifact",
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def wall_pileup_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    source_rows = read_csv(GATE38_WALL_PILEUP)
    for source_row in source_rows:
        scenario_id = source_row["scenario_id"]
        theta, depth_nm, radius_nm = gate38._scenario_parameters(scenario_id)
        points = gate37._simulate_points(
            theta_deg=theta,
            depth_nm=depth_nm,
            radius_nm=radius_nm,
            dt_s=float(source_row["dt_s"]),
            seed=int(source_row["rng_seed"]) + 512,
            n_samples=WALL_PILEUP_SAMPLE_COUNT,
        )
        counts: list[int] = []
        for low_nm, high_nm in zip(gate38.BAND_EDGES_NM[:-1], gate38.BAND_EDGES_NM[1:]):
            counts.append(
                sum(low_nm <= float(point["surface_gap_nm"]) < high_nm for point in points)
            )
        first_count = counts[0]
        adjacent_count = counts[1]
        ratio, ci_low, ci_high = gate38._ratio_ci(first_count, adjacent_count)
        rows.append(
            {
                "scenario_id": scenario_id,
                "dt_s": source_row["dt_s"],
                "rng_seed": str(int(source_row["rng_seed"]) + 512),
                "n_samples": str(WALL_PILEUP_SAMPLE_COUNT),
                "band_edges_nm_json": json.dumps(gate38.BAND_EDGES_NM),
                "band_counts_json": json.dumps(counts),
                "first_gap_band_count": str(first_count),
                "adjacent_gap_band_count": str(adjacent_count),
                "first_vs_adjacent_gap_band_smoothed_ratio": fmt(ratio),
                "ratio_ci95_low": fmt(ci_low),
                "ratio_ci95_high": fmt(ci_high),
                "proof_ratio_hard_line": fmt(WALL_PILEUP_PROOF_RATIO_HARD_LINE),
                "source_gate38_ratio": source_row["expanded_wall_pileup_ratio"],
                "candidate_status": (
                    "candidate_and_proof_threshold_met_not_registered"
                    if ratio <= WALL_PILEUP_PROOF_RATIO_HARD_LINE
                    and ci_high <= WALL_PILEUP_PROOF_RATIO_HARD_LINE
                    else "candidate_proof_threshold_review_required"
                ),
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def build_payload() -> dict[str, Any]:
    one_wall = one_wall_rows()
    pileup = wall_pileup_rows()
    sources = source_lock_rows()
    firewall = no_proof_firewall_rows()
    max_ks = max(float(row["ks_distance_to_reflecting_kernel"]) for row in one_wall)
    max_ratio = max(float(row["first_vs_adjacent_gap_band_smoothed_ratio"]) for row in pileup)
    max_ratio_ci_high = max(float(row["ratio_ci95_high"]) for row in pileup)
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "build_head": safe_git_head(),
        "one_wall_rows": len(one_wall),
        "wall_pileup_rows": len(pileup),
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(row["exists"] != "true" for row in sources),
        "one_wall_sample_count": ONE_WALL_SAMPLE_COUNT,
        "wall_pileup_sample_count": WALL_PILEUP_SAMPLE_COUNT,
        "max_one_wall_positive_control_ks": max_ks,
        "one_wall_proof_ks_hard_line": ONE_WALL_PROOF_KS_HARD_LINE,
        "max_wall_pileup_ratio": max_ratio,
        "max_wall_pileup_ratio_ci95_high": max_ratio_ci_high,
        "wall_pileup_proof_ratio_hard_line": WALL_PILEUP_PROOF_RATIO_HARD_LINE,
        "one_wall_wall_pileup_status": (
            "candidate_numeric_thresholds_met_not_proof_registered"
            if (
                max_ks <= ONE_WALL_PROOF_KS_HARD_LINE
                and max_ratio <= WALL_PILEUP_PROOF_RATIO_HARD_LINE
                and max_ratio_ci_high <= WALL_PILEUP_PROOF_RATIO_HARD_LINE
            )
            else "candidate_threshold_review_required"
        ),
        "proof_readiness_impact": (
            "one_wall_and_wall_pileup_proof_threshold_gaps_reduced_by_expanded_sampling_candidate"
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
        "one_wall_rows": one_wall,
        "wall_pileup_rows": pileup,
        "source_locks": sources,
        "no_proof_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "One-wall rows": s["one_wall_rows"] == len(D_OVER_SIGMA_GRID),
        "Wall-pileup rows": s["wall_pileup_rows"] >= 10,
        "Source lock complete": s["source_missing_rows"] == 0,
        "One-wall KS proof line": s["max_one_wall_positive_control_ks"]
        <= ONE_WALL_PROOF_KS_HARD_LINE,
        "Wall-pileup ratio proof line": s["max_wall_pileup_ratio"]
        <= WALL_PILEUP_PROOF_RATIO_HARD_LINE,
        "Wall-pileup CI high proof line": s["max_wall_pileup_ratio_ci95_high"]
        <= WALL_PILEUP_PROOF_RATIO_HARD_LINE,
        "Status no proof": s["one_wall_wall_pileup_status"].endswith(
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
            "policy_impact": "one_wall_wall_pileup_refinement_no_proof_registration",
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
        "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_ONE_WALL_20260701.csv": payload[
            "one_wall_rows"
        ],
        "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_WALL_PILEUP_20260701.csv": payload[
            "wall_pileup_rows"
        ],
        "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_SOURCE_LOCK_20260701.csv": payload[
            "source_locks"
        ],
        "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_NO_PROOF_FIREWALL_20260701.csv": payload[
            "no_proof_firewall"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    status_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_STATUS_20260701.json"
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

    active_report = active_output_dir / "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_REPORT_20260701.md"
    write_md(
        active_report,
        "NODI COMSOL Package C One-Wall and Wall-Pileup Refinement",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- One-wall rows: `{payload['summary']['one_wall_rows']}`.",
            f"- Wall-pileup rows: `{payload['summary']['wall_pileup_rows']}`.",
            f"- Max one-wall KS: `{payload['summary']['max_one_wall_positive_control_ks']}`.",
            f"- Max wall-pileup ratio: `{payload['summary']['max_wall_pileup_ratio']}`.",
            f"- Max wall-pileup CI95 high: `{payload['summary']['max_wall_pileup_ratio_ci95_high']}`.",
            f"- Candidate status: `{payload['summary']['one_wall_wall_pileup_status']}`.",
            "- Boundary: expanded-sampling candidate evidence only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no numeric PRS/EAS, no route/yield/detection/wet/fab/production claims.",
        ],
    )
    generated.append(active_report)

    public_report = active_report_dir / "512_NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_REFINEMENT_20260701.md"
    write_md(
        public_report,
        "NODI COMSOL Package C One-Wall and Wall-Pileup Refinement",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Source head: `{payload['summary']['build_head']}`",
            "- This packet expands the two remaining proof-threshold-gap diagnostics: one-wall folded-normal positive control and first-vs-adjacent wall-gap-band pileup ratio.",
            f"- One-wall sample count: `{payload['summary']['one_wall_sample_count']}`; max KS: `{payload['summary']['max_one_wall_positive_control_ks']}`.",
            f"- Wall-pileup sample count: `{payload['summary']['wall_pileup_sample_count']}`; max ratio: `{payload['summary']['max_wall_pileup_ratio']}`; max CI95 high: `{payload['summary']['max_wall_pileup_ratio_ci95_high']}`.",
            f"- Candidate status: `{payload['summary']['one_wall_wall_pileup_status']}`.",
            f"- GitHub visibility: `{payload['summary']['github_visibility_status']}`.",
            "- Boundary: this is proof-threshold gap reduction evidence only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no numeric PRS/EAS, no route/yield/detection/wet/fab/production claims.",
            f"- Machine-readable support: `{rel(active_output_dir)}`.",
        ],
    )
    generated.append(public_report)

    manifest_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_MANIFEST_20260701.csv"
    report_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_REPORT_20260701.json"
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
    if not args.confirm_package_c_one_wall_wall_pileup_refinement:
        parser.error("--confirm-package-c-one-wall-wall-pileup-refinement is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_PACKAGE_C_ONE_WALL_WALL_PILEUP_REFINEMENT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
