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

from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows, write_json_atomic  # noqa: E402
from tools.audits import (  # noqa: E402
    build_nodi_comsol_gate37_sidewall_package_c_metric_hardening_candidate as gate37,
)


DATE_STAMP = "20260701"
SOURCE_DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
SOURCE_OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{SOURCE_DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"

EXPECTED_GATE37_DISPOSITION = (
    "NODI_GATE37_SIDEWALL_PACKAGE_C_REFLECTION_METRIC_HARDENING_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
DISPOSITION = (
    "NODI_GATE38_SIDEWALL_WALL_PILEUP_REFINEMENT_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
ARTIFACT_ID = "GATE38_SIDEWALL_WALL_PILEUP_REFINEMENT_CANDIDATE_20260701"
CLAIM_BOUNDARY = (
    "wall_pileup_refinement_candidate_not_package_c_proof_registered_not_runtime"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

EXPANDED_SAMPLE_COUNT = 8192
TOP_PILEUP_ROW_COUNT = 12
BAND_EDGES_NM = (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 10.0)
ALGORITHM_PILEUP_RATIO_HARD_LINE = 1.5
ALGORITHM_PILEUP_LOWER_CI_HARD_LINE = 1.25
INTERPRETABLE_ADJACENT_COUNT_MIN = 5
INTERPRETABLE_GAP_BAND_TOTAL_MIN = 20

ALLOWED_USE = (
    "wall-pileup diagnostic refinement;Gate37 sparse proxy triage;"
    "future metric hardening design;no-proof-registration"
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

GATE37_STATUS = SOURCE_OUTPUT_DIR / "NODI_COMSOL_GATE37_SIDEWALL_STATUS_20260630.json"
GATE37_BOUNDARY_SPLIT = SOURCE_OUTPUT_DIR / "NODI_COMSOL_GATE37_SIDEWALL_BOUNDARY_ATOM_SPLIT_20260630.csv"
GATE37_CORNER_HEATMAP = SOURCE_OUTPUT_DIR / "NODI_COMSOL_GATE37_SIDEWALL_CORNER_HEATMAP_20260630.csv"
GATE37_FIREWALL = SOURCE_OUTPUT_DIR / "NODI_COMSOL_GATE37_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv"

SOURCE_FILES = {
    "gate37_status": GATE37_STATUS,
    "gate37_boundary_atom_split": GATE37_BOUNDARY_SPLIT,
    "gate37_corner_heatmap": GATE37_CORNER_HEATMAP,
    "gate37_no_proof_firewall": GATE37_FIREWALL,
    "gate37_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate37_sidewall_package_c_metric_hardening_candidate.py",
    "gate38_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate38_sidewall_wall_pileup_refinement_candidate.py",
    "gate38_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_gate38_sidewall_wall_pileup_refinement_candidate.py",
    "cross_section_geometry": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}

REPORTS = {
    "500": "GATE38A_WALL_PILEUP_REFINEMENT_COUNTS",
    "501": "GATE38B_SPARSE_PROXY_TRIAGE",
    "502": "GATE38C_NO_PROOF_FIREWALL",
    "503": "GATE38_WALL_PILEUP_REFINEMENT_CANDIDATE_MASTER_REPORT",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Gate38 sidewall wall-pileup refinement candidate artifacts."
    )
    parser.add_argument(
        "--confirm-gate38-wall-pileup-refinement-candidate",
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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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


def _scenario_parameters(scenario_id: str) -> tuple[float, float, float]:
    match = re.fullmatch(r"theta([0-9.]+)_D([0-9.]+)_r([0-9.]+)", scenario_id)
    if not match:
        raise ValueError(f"Unexpected scenario_id: {scenario_id}")
    theta, depth_nm, radius_nm = match.groups()
    return float(theta), float(depth_nm), float(radius_nm)


def _ratio_ci(first_count: int, adjacent_count: int) -> tuple[float, float, float]:
    ratio = (first_count + 0.5) / (adjacent_count + 0.5)
    se = math.sqrt(1.0 / (first_count + 0.5) + 1.0 / (adjacent_count + 0.5))
    lower = math.exp(math.log(ratio) - 1.96 * se)
    upper = math.exp(math.log(ratio) + 1.96 * se)
    return round(ratio, 9), round(lower, 9), round(upper, 9)


def _source_count_summary(
    source_row: dict[str, str],
) -> tuple[int, int, int, str, str]:
    first_count = round(
        float(source_row["first_gap_band_fraction"]) * int(source_row["n_samples"])
    )
    adjacent_count = round(
        float(source_row["adjacent_gap_band_fraction"]) * int(source_row["n_samples"])
    )
    total_count = first_count + adjacent_count
    denominator_zero = bool_text(adjacent_count == 0)
    if adjacent_count <= 1 or total_count < 10:
        sparse_status = "sparse_proxy_uninterpretable"
    else:
        sparse_status = "count_supported_proxy"
    return first_count, adjacent_count, total_count, denominator_zero, sparse_status


def _dt_consistency_status(
    scenario_id: str,
    all_source_rows: list[dict[str, str]],
) -> str:
    same_scenario = [row for row in all_source_rows if row["scenario_id"] == scenario_id]
    interpretable_high = 0
    sparse_high = 0
    for row in same_scenario:
        first_count, adjacent_count, total_count, _, sparse_status = _source_count_summary(row)
        ratio = (first_count + 0.5) / (adjacent_count + 0.5)
        if ratio >= 3.0 and sparse_status == "count_supported_proxy":
            interpretable_high += 1
        elif ratio >= 3.0:
            sparse_high += 1
    if interpretable_high >= 2:
        return "reproduced_interpretable_high_ratio"
    if sparse_high:
        return "high_ratio_only_in_sparse_proxy_rows"
    return "not_reproduced_as_high_ratio"


def _expanded_sparse_status(first_count: int, adjacent_count: int) -> tuple[int, str, str]:
    total_count = first_count + adjacent_count
    denominator_zero = bool_text(adjacent_count == 0)
    if adjacent_count < INTERPRETABLE_ADJACENT_COUNT_MIN or total_count < INTERPRETABLE_GAP_BAND_TOTAL_MIN:
        sparse_status = "expanded_sparse_proxy_uninterpretable"
    else:
        sparse_status = "expanded_count_supported_proxy"
    return total_count, denominator_zero, sparse_status


def wall_pileup_refinement_rows() -> list[dict[str, str]]:
    all_source_rows = read_csv(GATE37_BOUNDARY_SPLIT)
    source_rows = sorted(
        all_source_rows,
        key=lambda row: float(row["wall_pileup_ratio"]),
        reverse=True,
    )[:TOP_PILEUP_ROW_COUNT]
    rows: list[dict[str, str]] = []
    for source_row in source_rows:
        scenario_id = source_row["scenario_id"]
        theta, depth_nm, radius_nm = _scenario_parameters(scenario_id)
        points = gate37._simulate_points(
            theta_deg=theta,
            depth_nm=depth_nm,
            radius_nm=radius_nm,
            dt_s=float(source_row["dt_s"]),
            seed=int(source_row["rng_seed"]),
            n_samples=EXPANDED_SAMPLE_COUNT,
        )
        counts: list[int] = []
        for low_nm, high_nm in zip(BAND_EDGES_NM[:-1], BAND_EDGES_NM[1:]):
            counts.append(
                sum(low_nm <= float(point["surface_gap_nm"]) < high_nm for point in points)
            )
        first_count = counts[0]
        adjacent_count = counts[1]
        ratio, ratio_lower, ratio_upper = _ratio_ci(first_count, adjacent_count)
        (
            original_first_count,
            original_adjacent_count,
            original_total_count,
            original_denominator_zero,
            original_sparse_status,
        ) = _source_count_summary(source_row)
        expanded_total_count, expanded_denominator_zero, expanded_sparse_status = (
            _expanded_sparse_status(first_count, adjacent_count)
        )
        dt_consistency = _dt_consistency_status(scenario_id, all_source_rows)
        algorithmic_signal = (
            ratio > ALGORITHM_PILEUP_RATIO_HARD_LINE
            and ratio_lower > ALGORITHM_PILEUP_LOWER_CI_HARD_LINE
            and expanded_sparse_status == "expanded_count_supported_proxy"
            and dt_consistency == "reproduced_interpretable_high_ratio"
        )
        if algorithmic_signal:
            status = "candidate_review_required_possible_algorithmic_pileup"
        elif original_adjacent_count < 5:
            status = "sparse_gate37_proxy_artifact_no_algorithmic_signal"
        else:
            status = "expanded_sampling_no_algorithmic_signal"
        rows.append(
            {
                "scenario_id": scenario_id,
                "dt_s": source_row["dt_s"],
                "rng_seed": source_row["rng_seed"],
                "gate37_sample_count": source_row["n_samples"],
                "expanded_sample_count": str(EXPANDED_SAMPLE_COUNT),
                "gate37_wall_pileup_ratio": source_row["wall_pileup_ratio"],
                "gate37_first_band_count": str(original_first_count),
                "gate37_adjacent_band_count": str(original_adjacent_count),
                "gate37_gap_band_total_count": str(original_total_count),
                "gate37_ratio_denominator_zero": original_denominator_zero,
                "gate37_sparse_denominator_status": original_sparse_status,
                "band_edges_nm_json": json.dumps(BAND_EDGES_NM),
                "expanded_band_counts_json": json.dumps(counts),
                "expanded_first_band_count": str(first_count),
                "expanded_adjacent_band_count": str(adjacent_count),
                "expanded_gap_band_total_count": str(expanded_total_count),
                "expanded_ratio_denominator_zero": expanded_denominator_zero,
                "expanded_sparse_denominator_status": expanded_sparse_status,
                "expanded_first_band_fraction": str(round(first_count / EXPANDED_SAMPLE_COUNT, 9)),
                "expanded_adjacent_band_fraction": str(
                    round(adjacent_count / EXPANDED_SAMPLE_COUNT, 9)
                ),
                "expanded_first_vs_adjacent_gap_band_smoothed_ratio": str(ratio),
                "expanded_first_vs_adjacent_gap_band_ratio_ci95_low": str(ratio_lower),
                "expanded_first_vs_adjacent_gap_band_ratio_ci95_high": str(ratio_upper),
                "expanded_wall_pileup_ratio": str(ratio),
                "expanded_wall_pileup_ratio_ci95_low": str(ratio_lower),
                "expanded_wall_pileup_ratio_ci95_high": str(ratio_upper),
                "dt_consistency_status": dt_consistency,
                "algorithmic_pileup_signal": bool_text(algorithmic_signal),
                "refinement_status": status,
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
            "firewall_status": "PASS_GATE38_WALL_PILEUP_REFINEMENT_NO_PROOF_REGISTRATION",
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
    gate37_summary = read_json(GATE37_STATUS).get("summary", {})
    refinement = wall_pileup_refinement_rows()
    source_rows = source_lock_rows()
    firewall = no_proof_firewall_rows()
    algorithmic_rows = [
        row for row in refinement if row["algorithmic_pileup_signal"] == "true"
    ]
    sparse_rows = [
        row
        for row in refinement
        if row["refinement_status"] == "sparse_gate37_proxy_artifact_no_algorithmic_signal"
    ]
    max_ratio = max(
        (
            float(row["expanded_first_vs_adjacent_gap_band_smoothed_ratio"])
            for row in refinement
        ),
        default=0.0,
    )
    max_ratio_ci_low = max(
        (
            float(row["expanded_first_vs_adjacent_gap_band_ratio_ci95_low"])
            for row in refinement
        ),
        default=0.0,
    )
    max_ratio_ci_high = max(
        (
            float(row["expanded_first_vs_adjacent_gap_band_ratio_ci95_high"])
            for row in refinement
        ),
        default=0.0,
    )
    max_interpretable_ratio = max(
        (
            float(row["expanded_first_vs_adjacent_gap_band_smoothed_ratio"])
            for row in refinement
            if row["expanded_sparse_denominator_status"] == "expanded_count_supported_proxy"
        ),
        default=0.0,
    )
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "gate38_build_head": safe_git_head(),
        "gate37_disposition": gate37_summary.get("disposition", ""),
        "gate37_expected_disposition": EXPECTED_GATE37_DISPOSITION,
        "gate37_max_wall_pileup_ratio": gate37_summary.get("max_wall_pileup_ratio"),
        "refined_top_pileup_rows": len(refinement),
        "expanded_sample_count": EXPANDED_SAMPLE_COUNT,
        "algorithmic_pileup_signal_rows": len(algorithmic_rows),
        "sparse_gate37_proxy_artifact_rows": len(sparse_rows),
        "max_expanded_first_vs_adjacent_gap_band_smoothed_ratio": round(max_ratio, 9),
        "max_expanded_first_vs_adjacent_gap_band_ratio_ci95_low": round(
            max_ratio_ci_low, 9
        ),
        "max_expanded_first_vs_adjacent_gap_band_ratio_ci95_high": round(
            max_ratio_ci_high, 9
        ),
        "max_interpretable_expanded_gap_band_smoothed_ratio": round(
            max_interpretable_ratio, 9
        ),
        "max_expanded_wall_pileup_ratio": round(max_ratio, 9),
        "max_expanded_wall_pileup_ratio_ci95_low": round(max_ratio_ci_low, 9),
        "max_expanded_wall_pileup_ratio_ci95_high": round(max_ratio_ci_high, 9),
        "wall_pileup_refinement_status": (
            "candidate_review_required_possible_algorithmic_pileup"
            if algorithmic_rows
            else "sparse_gate37_proxy_artifact_no_algorithmic_pileup_signal"
        ),
        "source_lock_rows": len(source_rows),
        "source_missing_rows": sum(row["exists"] != "true" for row in source_rows),
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
        "wall_pileup_refinement": refinement,
        "source_locks": source_rows,
        "no_proof_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "Gate37 disposition": s["gate37_disposition"] == EXPECTED_GATE37_DISPOSITION,
        "Refinement row count": s["refined_top_pileup_rows"] == TOP_PILEUP_ROW_COUNT,
        "Expanded sample count": s["expanded_sample_count"] == EXPANDED_SAMPLE_COUNT,
        "No algorithmic pileup signal": s["algorithmic_pileup_signal_rows"] == 0,
        "Sparse proxy artifacts identified": s["sparse_gate37_proxy_artifact_rows"] >= 1,
        "Source lock complete": s["source_missing_rows"] == 0,
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
            "policy_impact": "wall_pileup_refinement_candidate_only_no_proof_registration",
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
        "NODI_COMSOL_GATE38_SIDEWALL_WALL_PILEUP_REFINEMENT_20260701.csv": payload[
            "wall_pileup_refinement"
        ],
        "NODI_COMSOL_GATE38_SIDEWALL_SOURCE_LOCK_20260701.csv": payload["source_locks"],
        "NODI_COMSOL_GATE38_SIDEWALL_NO_PROOF_FIREWALL_20260701.csv": payload[
            "no_proof_firewall"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    report_path = active_output_dir / "NODI_COMSOL_GATE38_SIDEWALL_REPORT_20260701.json"
    write_json_atomic(report_path, {"summary": payload["summary"], "outputs": [p.name for p in generated]})
    generated.append(report_path)

    status_path = active_output_dir / "NODI_COMSOL_GATE38_SIDEWALL_STATUS_20260701.json"
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

    master_md = active_output_dir / "NODI_COMSOL_GATE38_SIDEWALL_WALL_PILEUP_REFINEMENT_REPORT_20260701.md"
    write_md(
        master_md,
        "NODI COMSOL Gate38 Sidewall Wall-Pileup Refinement",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Gate37 max wall-pileup proxy ratio: `{payload['summary']['gate37_max_wall_pileup_ratio']}`.",
            f"- Refined rows: {payload['summary']['refined_top_pileup_rows']}.",
            f"- Expanded sample count per row: {payload['summary']['expanded_sample_count']}.",
            f"- Algorithmic pile-up signal rows: {payload['summary']['algorithmic_pileup_signal_rows']}.",
            f"- Sparse Gate37 proxy artifact rows: {payload['summary']['sparse_gate37_proxy_artifact_rows']}.",
            "- Max expanded first-vs-adjacent gap-band smoothed proxy ratio: "
            f"{payload['summary']['max_expanded_first_vs_adjacent_gap_band_smoothed_ratio']}.",
            f"- Refinement status: `{payload['summary']['wall_pileup_refinement_status']}`.",
            "- Boundary: refinement candidate only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no numeric PRS/EAS, no route/yield/detection/wet/fab/production claims.",
        ],
    )
    generated.append(master_md)

    for number, title in REPORTS.items():
        path = active_report_dir / f"{number}_NODI_COMSOL_{title}_20260701.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate38 disposition: `{DISPOSITION}`",
                f"- Source head: `{payload['summary']['gate38_build_head']}`",
                f"- Refinement status: `{payload['summary']['wall_pileup_refinement_status']}`",
                f"- Algorithmic signal rows: {payload['summary']['algorithmic_pileup_signal_rows']}.",
                f"- Sparse proxy artifact rows: {payload['summary']['sparse_gate37_proxy_artifact_rows']}.",
                "- Ratio naming: first-vs-adjacent gap-band smoothed proxy, not a physical pile-up claim.",
                "- Boundary: wall-pileup refinement candidate only; proof registration and Package C pass remain unauthorized.",
                f"- Machine-readable support: `{rel(active_output_dir)}`.",
            ],
        )
        generated.append(path)

    manifest_path = active_output_dir / "NODI_COMSOL_GATE38_SIDEWALL_MANIFEST_20260701.csv"
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
    if not args.confirm_gate38_wall_pileup_refinement_candidate:
        parser.error("--confirm-gate38-wall-pileup-refinement-candidate is required")
    payload = build_payload()
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE38_SIDEWALL_WALL_PILEUP_REFINEMENT_CANDIDATE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
