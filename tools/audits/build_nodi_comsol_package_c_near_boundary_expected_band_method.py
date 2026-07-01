#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

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
    build_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate as gate30,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"

DISPOSITION = "NODI_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_METHOD_CANDIDATE_READY_NO_PROOF_REGISTRATION"
ARTIFACT_ID = "PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_METHOD_20260701"
CLAIM_BOUNDARY = "near_boundary_expected_band_method_candidate_not_package_c_proof_registered_not_runtime"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
GITHUB_VISIBILITY_STATUS = "local_worktree_pre_commit_urls_valid_after_publish"

ALLOWED_USE = (
    "Package C near-boundary expected-band method candidate;statistical method binding;"
    "no-proof-registration"
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

WALL_PILEUP_ROWS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_WALL_PILEUP_20260701.csv"
)
WALL_PILEUP_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_STATUS_20260701.json"
)
GATE37_BOUNDARY_SPLIT = (
    PROJECT_ROOT
    / "reports/joint_interface_20260630/NODI_COMSOL_GATE37_SIDEWALL_BOUNDARY_ATOM_SPLIT_20260630.csv"
)
THRESHOLD_TABLE = OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_TABLE_20260701.csv"

SOURCE_FILES = {
    "one_wall_wall_pileup_rows": WALL_PILEUP_ROWS,
    "one_wall_wall_pileup_status": WALL_PILEUP_STATUS,
    "gate37_boundary_split": GATE37_BOUNDARY_SPLIT,
    "proof_threshold_table": THRESHOLD_TABLE,
    "cross_section_geometry": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
    "near_boundary_expected_band_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_package_c_near_boundary_expected_band_method.py",
    "near_boundary_expected_band_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_package_c_near_boundary_expected_band_method.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}

Z_HARD_LINE = 3.0
RATIO_HARD_LINE = 1.25


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Package C near-boundary expected-band method artifacts."
    )
    parser.add_argument(
        "--confirm-package-c-near-boundary-expected-band-method",
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


def read_json_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("summary", {})


def scenario_parameters(scenario_id: str) -> tuple[float, float, float]:
    match = re.fullmatch(r"theta([0-9.]+)_D([0-9.]+)_r([0-9.]+)", scenario_id)
    if not match:
        raise ValueError(f"Unexpected scenario_id: {scenario_id}")
    theta, depth_nm, radius_nm = match.groups()
    return float(theta), float(depth_nm), float(radius_nm)


def wilson_ci(count: int, n: int, *, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return 0.0, 0.0
    phat = count / n
    denom = 1.0 + z * z / n
    center = (phat + z * z / (2.0 * n)) / denom
    half = z * math.sqrt((phat * (1.0 - phat) + z * z / (4.0 * n)) / n) / denom
    return max(0.0, center - half), min(1.0, center + half)


def expected_band_fraction(
    *,
    theta_deg: float,
    depth_nm: float,
    radius_nm: float,
    band_low_nm: float,
    band_high_nm: float,
) -> float:
    geom = gate30._geom(theta_deg, depth_nm)
    radius_m = gate30._m(radius_nm)
    area_base = geom.center_accessible_area_m2(radius_m)
    if area_base <= 0.0:
        return 0.0
    area_low = geom.center_accessible_area_m2(radius_m + gate30._m(band_low_nm))
    area_high = geom.center_accessible_area_m2(radius_m + gate30._m(band_high_nm))
    return max(area_low - area_high, 0.0) / area_base


def expected_band_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_row in read_csv_rows(WALL_PILEUP_ROWS):
        theta, depth_nm, radius_nm = scenario_parameters(source_row["scenario_id"])
        band_edges_nm = json.loads(source_row["band_edges_nm_json"])
        band_counts = json.loads(source_row["band_counts_json"])
        n_samples = int(source_row["n_samples"])
        for idx, count in enumerate(band_counts[:2]):
            low_nm = float(band_edges_nm[idx])
            high_nm = float(band_edges_nm[idx + 1])
            expected = expected_band_fraction(
                theta_deg=theta,
                depth_nm=depth_nm,
                radius_nm=radius_nm,
                band_low_nm=low_nm,
                band_high_nm=high_nm,
            )
            observed = count / n_samples
            se = math.sqrt(max(expected * (1.0 - expected) / n_samples, 1.0e-30))
            z_abs = abs(observed - expected) / se
            ci_low, ci_high = wilson_ci(int(count), n_samples)
            rows.append(
                {
                    "scenario_id": source_row["scenario_id"],
                    "dt_s": source_row["dt_s"],
                    "rng_seed": source_row["rng_seed"],
                    "band_low_nm": str(low_nm),
                    "band_high_nm": str(high_nm),
                    "band_count": str(count),
                    "n_samples": str(n_samples),
                    "observed_band_fraction": str(round(observed, 12)),
                    "expected_area_band_fraction": str(round(expected, 12)),
                    "expected_count": str(round(expected * n_samples, 6)),
                    "binomial_se": str(round(se, 12)),
                    "abs_z_to_expected": str(round(z_abs, 9)),
                    "observed_ci95_low": str(round(ci_low, 12)),
                    "observed_ci95_high": str(round(ci_high, 12)),
                    "method_formula": (
                        "expected_fraction=(area(radius+a)-area(radius+b))/area(radius)"
                    ),
                    "candidate_status": (
                        "candidate_expected_band_method_bound_not_proof_registered"
                        if z_abs <= Z_HARD_LINE
                        else "candidate_expected_band_method_review_required"
                    ),
                    "claim_boundary": CLAIM_BOUNDARY,
                    "allowed_use": ALLOWED_USE,
                    "blocked_use": BLOCKED_USE,
                }
            )
    return rows


def legacy_sparse_context_rows() -> list[dict[str, str]]:
    gate37_rows = read_csv_rows(GATE37_BOUNDARY_SPLIT)
    max_row = max(
        gate37_rows,
        key=lambda row: float(row.get("near_boundary_band_fraction", "0") or 0.0),
    )
    n_samples = int(max_row["n_samples"])
    eps_nm = float(max_row["near_boundary_band_eps_nm"])
    observed = float(max_row["near_boundary_band_fraction"])
    expected = expected_band_fraction(
        theta_deg=scenario_parameters(max_row["scenario_id"])[0],
        depth_nm=scenario_parameters(max_row["scenario_id"])[1],
        radius_nm=scenario_parameters(max_row["scenario_id"])[2],
        band_low_nm=0.0,
        band_high_nm=eps_nm,
    )
    return [
        {
            "legacy_source": "GATE37_BOUNDARY_ATOM_SPLIT_20260630",
            "scenario_id": max_row["scenario_id"],
            "dt_s": max_row["dt_s"],
            "near_boundary_band_eps_nm": str(eps_nm),
            "n_samples": str(n_samples),
            "observed_near_boundary_band_fraction": str(observed),
            "expected_area_band_fraction": str(round(expected, 12)),
            "expected_count": str(round(expected * n_samples, 9)),
            "interpretation": (
                "underpowered_sparse_context_superseded_by_65536_sample_expected_band_method"
            ),
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


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
            "firewall_status": "PASS_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_METHOD_NO_PROOF_REGISTRATION",
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


def build_payload() -> dict[str, Any]:
    rows = expected_band_rows()
    legacy = legacy_sparse_context_rows()
    sources = source_lock_rows()
    firewall = no_proof_firewall_rows()
    first_band_rows = [row for row in rows if row["band_low_nm"] == "0.0"]
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "build_head": safe_git_head(),
        "expected_band_rows": len(rows),
        "legacy_sparse_context_rows": len(legacy),
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(row["exists"] != "true" for row in sources),
        "max_abs_z_to_expected": max(float(row["abs_z_to_expected"]) for row in rows),
        "max_first_band_abs_z_to_expected": max(
            float(row["abs_z_to_expected"]) for row in first_band_rows
        ),
        "max_observed_first_band_fraction": max(
            float(row["observed_band_fraction"]) for row in first_band_rows
        ),
        "max_expected_first_band_fraction": max(
            float(row["expected_area_band_fraction"]) for row in first_band_rows
        ),
        "z_hard_line": Z_HARD_LINE,
        "ratio_hard_line": RATIO_HARD_LINE,
        "near_boundary_expected_band_method_status": (
            "candidate_method_bound_not_proof_registered"
            if all(float(row["abs_z_to_expected"]) <= Z_HARD_LINE for row in rows)
            else "candidate_method_review_required"
        ),
        "proof_readiness_impact": (
            "near_boundary_expected_band_method_bound_as_candidate_no_proof_registration"
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
        "expected_band_rows": rows,
        "legacy_sparse_context_rows": legacy,
        "source_locks": sources,
        "no_proof_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "Expected band rows": s["expected_band_rows"] == 24,
        "Legacy sparse context row": s["legacy_sparse_context_rows"] == 1,
        "Source lock complete": s["source_missing_rows"] == 0,
        "Z line met": s["max_abs_z_to_expected"] <= Z_HARD_LINE,
        "Method status": s["near_boundary_expected_band_method_status"]
        == "candidate_method_bound_not_proof_registered",
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
            "policy_impact": "near_boundary_expected_band_method_no_proof_registration",
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


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


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
        "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_ROWS_20260701.csv": payload[
            "expected_band_rows"
        ],
        "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_LEGACY_CONTEXT_20260701.csv": payload[
            "legacy_sparse_context_rows"
        ],
        "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_SOURCE_LOCK_20260701.csv": payload[
            "source_locks"
        ],
        "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_NO_PROOF_FIREWALL_20260701.csv": payload[
            "no_proof_firewall"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    status_path = (
        active_output_dir / "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_STATUS_20260701.json"
    )
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
        active_output_dir / "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_REPORT_20260701.md"
    )
    write_md(
        active_report,
        "NODI COMSOL Package C Near-Boundary Expected-Band Method",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Expected-band rows: `{payload['summary']['expected_band_rows']}`.",
            f"- Max abs z to expected: `{payload['summary']['max_abs_z_to_expected']}`.",
            f"- Method status: `{payload['summary']['near_boundary_expected_band_method_status']}`.",
            "- Boundary: method-binding candidate only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no numeric PRS/EAS, no route/yield/detection/wet/fab/production claims.",
        ],
    )
    generated.append(active_report)

    public_report = (
        active_report_dir
        / "513_NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_METHOD_20260701.md"
    )
    write_md(
        public_report,
        "NODI COMSOL Package C Near-Boundary Expected-Band Method",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Source head: `{payload['summary']['build_head']}`",
            "- Formula: `expected_fraction=(Area(radius+a)-Area(radius+b))/Area(radius)` over the center-accessible geometry.",
            f"- Expected-band rows: `{payload['summary']['expected_band_rows']}`; legacy sparse context rows: `{payload['summary']['legacy_sparse_context_rows']}`.",
            f"- Max abs z to expected: `{payload['summary']['max_abs_z_to_expected']}` against candidate line `{payload['summary']['z_hard_line']}`.",
            f"- Method status: `{payload['summary']['near_boundary_expected_band_method_status']}`.",
            f"- GitHub visibility: `{payload['summary']['github_visibility_status']}`.",
            "- Boundary: this is method-binding evidence only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no numeric PRS/EAS, no route/yield/detection/wet/fab/production claims.",
            f"- Machine-readable support: `{rel(active_output_dir)}`.",
        ],
    )
    generated.append(public_report)

    manifest_path = (
        active_output_dir / "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_MANIFEST_20260701.csv"
    )
    report_path = (
        active_output_dir / "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_REPORT_20260701.json"
    )
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
    if not args.confirm_package_c_near_boundary_expected_band_method:
        parser.error("--confirm-package-c-near-boundary-expected-band-method is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_METHOD")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
