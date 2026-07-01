#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
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


DATE_STAMP = "20260701"
GATE37_DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
GATE37_OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{GATE37_DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"

EXPECTED_GATE37_DISPOSITION = (
    "NODI_GATE37_SIDEWALL_PACKAGE_C_REFLECTION_METRIC_HARDENING_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
EXPECTED_GATE38_DISPOSITION = (
    "NODI_GATE38_SIDEWALL_WALL_PILEUP_REFINEMENT_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
DISPOSITION = (
    "NODI_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
ARTIFACT_ID = "PACKAGE_C_METRIC_HARDENING_CONSOLIDATION_20260701"
CLAIM_BOUNDARY = (
    "consolidated_metric_hardening_candidate_not_package_c_proof_registered_not_runtime"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

ALLOWED_USE = (
    "Package C metric-hardening consolidation;single review entrypoint for Gate37/Gate38 "
    "candidate evidence;future proof-readiness planning;no-proof-registration"
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

GATE37_STATUS = GATE37_OUTPUT_DIR / "NODI_COMSOL_GATE37_SIDEWALL_STATUS_20260630.json"
GATE37_BOUNDARY_SPLIT = (
    GATE37_OUTPUT_DIR / "NODI_COMSOL_GATE37_SIDEWALL_BOUNDARY_ATOM_SPLIT_20260630.csv"
)
GATE37_RAW_HISTOGRAMS = (
    GATE37_OUTPUT_DIR / "NODI_COMSOL_GATE37_SIDEWALL_RAW_HISTOGRAMS_20260630.csv"
)
GATE37_ESS_PROXY = GATE37_OUTPUT_DIR / "NODI_COMSOL_GATE37_SIDEWALL_ESS_PROXY_20260630.csv"
GATE37_ONE_WALL = (
    GATE37_OUTPUT_DIR / "NODI_COMSOL_GATE37_SIDEWALL_ONE_WALL_FOLDED_NORMAL_SUITE_20260630.csv"
)
GATE37_DT_REFINEMENT = (
    GATE37_OUTPUT_DIR / "NODI_COMSOL_GATE37_SIDEWALL_WORST_CASE_DT_REFINEMENT_20260630.csv"
)
GATE37_CORNER_HEATMAP = (
    GATE37_OUTPUT_DIR / "NODI_COMSOL_GATE37_SIDEWALL_CORNER_HEATMAP_20260630.csv"
)
GATE37_FIREWALL = (
    GATE37_OUTPUT_DIR / "NODI_COMSOL_GATE37_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv"
)
GATE38_STATUS = OUTPUT_DIR / "NODI_COMSOL_GATE38_SIDEWALL_STATUS_20260701.json"
GATE38_REFINEMENT = (
    OUTPUT_DIR / "NODI_COMSOL_GATE38_SIDEWALL_WALL_PILEUP_REFINEMENT_20260701.csv"
)
GATE38_FIREWALL = OUTPUT_DIR / "NODI_COMSOL_GATE38_SIDEWALL_NO_PROOF_FIREWALL_20260701.csv"

SOURCE_FILES = {
    "gate37_status": GATE37_STATUS,
    "gate37_boundary_atom_split": GATE37_BOUNDARY_SPLIT,
    "gate37_raw_histograms": GATE37_RAW_HISTOGRAMS,
    "gate37_ess_proxy": GATE37_ESS_PROXY,
    "gate37_one_wall_folded_normal_suite": GATE37_ONE_WALL,
    "gate37_worst_case_dt_refinement": GATE37_DT_REFINEMENT,
    "gate37_corner_heatmap": GATE37_CORNER_HEATMAP,
    "gate37_no_proof_firewall": GATE37_FIREWALL,
    "gate38_status": GATE38_STATUS,
    "gate38_wall_pileup_refinement": GATE38_REFINEMENT,
    "gate38_no_proof_firewall": GATE38_FIREWALL,
    "gate37_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate37_sidewall_package_c_metric_hardening_candidate.py",
    "gate38_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate38_sidewall_wall_pileup_refinement_candidate.py",
    "consolidation_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_package_c_metric_hardening_consolidation.py",
    "consolidation_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_package_c_metric_hardening_consolidation.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the consolidated Package C metric-hardening candidate packet."
    )
    parser.add_argument(
        "--confirm-package-c-metric-hardening-consolidation",
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


def _rows(path: Path) -> list[dict[str, str]]:
    return read_csv_rows(path) if path.exists() else []


def _max_float(rows: list[dict[str, str]], key: str) -> float:
    return max((float(row[key]) for row in rows if row.get(key) not in {"", None}), default=0.0)


def _count(rows: list[dict[str, str]], key: str, value: str) -> int:
    return sum(row.get(key) == value for row in rows)


def evidence_index_rows(
    *,
    gate37_summary: dict[str, Any],
    gate38_summary: dict[str, Any],
    boundary_rows: list[dict[str, str]],
    histogram_rows: list[dict[str, str]],
    ess_rows: list[dict[str, str]],
    one_wall_rows: list[dict[str, str]],
    dt_rows: list[dict[str, str]],
    corner_rows: list[dict[str, str]],
    refinement_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    positive_one_wall = [
        row
        for row in one_wall_rows
        if row.get("method") == "folded_normal_mirror_positive_control"
    ]
    projection_negative = [
        row
        for row in one_wall_rows
        if row.get("method") == "projection_clamp_negative_control"
    ]
    rejection_negative = [
        row
        for row in one_wall_rows
        if row.get("method") == "rejection_resampling_negative_control"
    ]
    return [
        {
            "evidence_id": "exact_boundary_atom_split",
            "source_artifact": rel(GATE37_BOUNDARY_SPLIT),
            "row_count": str(len(boundary_rows)),
            "status": "candidate_satisfied_not_proof",
            "primary_metric": "max_exact_boundary_atom_fraction",
            "primary_value": str(gate37_summary.get("max_exact_boundary_atom_fraction", "")),
            "interpretation": "no exact boundary atoms observed in Gate37 split",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "evidence_id": "near_boundary_band_split",
            "source_artifact": rel(GATE37_BOUNDARY_SPLIT),
            "row_count": str(len(boundary_rows)),
            "status": "candidate_satisfied_not_proof",
            "primary_metric": "max_near_boundary_band_fraction",
            "primary_value": str(gate37_summary.get("max_near_boundary_band_fraction", "")),
            "interpretation": "near-band mass is separated from exact atom diagnostics",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "evidence_id": "raw_histograms",
            "source_artifact": rel(GATE37_RAW_HISTOGRAMS),
            "row_count": str(len(histogram_rows)),
            "status": "candidate_satisfied_not_proof",
            "primary_metric": "histogram_bases",
            "primary_value": ",".join(sorted({row.get("histogram_basis", "") for row in histogram_rows})),
            "interpretation": "reviewer-facing x_local_norm and u_accessible_cdf histograms are available",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "evidence_id": "ess_proxy",
            "source_artifact": rel(GATE37_ESS_PROXY),
            "row_count": str(len(ess_rows)),
            "status": "candidate_caveat_not_proof_ready",
            "primary_metric": "autocorrelation_status",
            "primary_value": "not_a_timeseries_proof_artifact",
            "interpretation": "ESS proxy is useful metadata but proof-level long-run ESS remains missing",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "evidence_id": "one_wall_folded_normal_positive_control",
            "source_artifact": rel(GATE37_ONE_WALL),
            "row_count": str(len(positive_one_wall)),
            "status": "candidate_satisfied_not_proof",
            "primary_metric": "max_positive_control_ks",
            "primary_value": str(_max_float(positive_one_wall, "ks_distance_to_reflecting_kernel")),
            "interpretation": "single-wall folded-normal sanity check remains within candidate threshold",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "evidence_id": "projection_clamp_negative_control",
            "source_artifact": rel(GATE37_ONE_WALL),
            "row_count": str(len(projection_negative)),
            "status": "expected_fail_observed",
            "primary_metric": "max_projection_exact_atom_fraction",
            "primary_value": str(
                _max_float(projection_negative, "exact_boundary_atom_fraction")
            ),
            "interpretation": "projection clamp remains detectable as a bad boundary treatment",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "evidence_id": "rejection_resampling_negative_control",
            "source_artifact": rel(GATE37_ONE_WALL),
            "row_count": str(len(rejection_negative)),
            "status": "expected_fail_observed",
            "primary_metric": "max_rejection_kernel_ks",
            "primary_value": str(_max_float(rejection_negative, "ks_distance_to_reflecting_kernel")),
            "interpretation": "rejection/resampling transition kernel remains separated from reflected Brownian target",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "evidence_id": "worst_case_dt_refinement",
            "source_artifact": rel(GATE37_DT_REFINEMENT),
            "row_count": str(len(dt_rows)),
            "status": "candidate_satisfied_not_proof",
            "primary_metric": "max_extra_dt_distribution_delta_vs_baseline_min_dt",
            "primary_value": str(
                _max_float(dt_rows, "extra_dt_distribution_delta_vs_baseline_min_dt")
            ),
            "interpretation": "Gate37 adds 6.25e-6 s stress rows for selected worst cases",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "evidence_id": "corner_heatmap",
            "source_artifact": rel(GATE37_CORNER_HEATMAP),
            "row_count": str(len(corner_rows)),
            "status": "candidate_satisfied_not_proof",
            "primary_metric": "max_corner_occupancy_ratio_to_expected",
            "primary_value": str(_max_float(corner_rows, "corner_occupancy_ratio_to_expected")),
            "interpretation": "corner bins are exposed for review, not promoted to proof",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "evidence_id": "wall_pileup_refinement",
            "source_artifact": rel(GATE38_REFINEMENT),
            "row_count": str(len(refinement_rows)),
            "status": "candidate_satisfied_not_proof",
            "primary_metric": "algorithmic_pileup_signal_rows",
            "primary_value": str(gate38_summary.get("algorithmic_pileup_signal_rows", "")),
            "interpretation": "Gate38 resolves Gate37 sparse wall-pileup proxy without an algorithmic pileup signal",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
    ]


def readiness_criteria_rows(
    *,
    gate37_summary: dict[str, Any],
    gate38_summary: dict[str, Any],
    evidence_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    evidence_status_by_id = {row["evidence_id"]: row["status"] for row in evidence_rows}
    return [
        {
            "criterion_id": "exact_boundary_atoms_zero",
            "candidate_status": "satisfied",
            "proof_status": "candidate_evidence_only",
            "threshold_or_requirement": "max_exact_boundary_atom_fraction == 0",
            "current_value": str(gate37_summary.get("max_exact_boundary_atom_fraction", "")),
            "blocking_gap": "proof artifact still needs reviewed clean-commit binding and authorization",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "criterion_id": "near_boundary_band_separated",
            "candidate_status": "satisfied",
            "proof_status": "partial",
            "threshold_or_requirement": "exact atoms and near-band mass must be reported separately",
            "current_value": str(gate37_summary.get("max_near_boundary_band_fraction", "")),
            "blocking_gap": "future proof should compare near-band mass to area expectation and standard error",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "criterion_id": "one_wall_positive_negative_controls",
            "candidate_status": "satisfied",
            "proof_status": "candidate_evidence_only",
            "threshold_or_requirement": "positive control KS <= 0.02 and negative controls fail as expected",
            "current_value": evidence_status_by_id.get("projection_clamp_negative_control", ""),
            "blocking_gap": "proof-level threshold should tighten to 0.01 with raw CDF/histogram binding",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "criterion_id": "dt_refinement_present",
            "candidate_status": "satisfied",
            "proof_status": "partial",
            "threshold_or_requirement": "6.25e-6 s rows for worst cases are present",
            "current_value": evidence_status_by_id.get("worst_case_dt_refinement", ""),
            "blocking_gap": "future proof needs fixed proof-level dt hard line and worst-case expansion policy",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "criterion_id": "corner_heatmap_present",
            "candidate_status": "satisfied",
            "proof_status": "partial",
            "threshold_or_requirement": "corner occupancy rows and active-set metrics are reviewable",
            "current_value": evidence_status_by_id.get("corner_heatmap", ""),
            "blocking_gap": "future proof needs corner area normalization and long-run bias criteria",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "criterion_id": "wall_pileup_sparse_proxy_resolved",
            "candidate_status": "satisfied",
            "proof_status": "candidate_evidence_only",
            "threshold_or_requirement": "algorithmic_pileup_signal_rows == 0 after expanded sampling",
            "current_value": str(gate38_summary.get("algorithmic_pileup_signal_rows", "")),
            "blocking_gap": "do not use bare wall_pileup_ratio as proof evidence",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "criterion_id": "timeseries_ess",
            "candidate_status": "not_satisfied_for_proof",
            "proof_status": "missing",
            "threshold_or_requirement": "long-run equilibrium proof must bind ESS/autocorrelation or equivalent independence proof",
            "current_value": "ess_proxy_only",
            "blocking_gap": "current Gate37 ESS rows are one-step proxy metadata, not timeseries proof",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "criterion_id": "reviewed_clean_commit_binding",
            "candidate_status": "not_satisfied_for_proof",
            "proof_status": "missing",
            "threshold_or_requirement": "reviewed clean commit/source lock must be bound before proof authorization",
            "current_value": "not_bound_by_this_consolidation",
            "blocking_gap": "manual proof authorization packet must bind reviewed commit and source tree",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "criterion_id": "manual_authorization_ledger",
            "candidate_status": "not_satisfied_for_proof",
            "proof_status": "missing",
            "threshold_or_requirement": "explicit authorization must supersede no-auth ledger",
            "current_value": "proof_registration_authorized=false",
            "blocking_gap": "authorization ledger remains empty by design",
            "claim_boundary": CLAIM_BOUNDARY,
        },
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
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def no_proof_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_status": "PASS_PACKAGE_C_METRIC_HARDENING_CONSOLIDATION_NO_PROOF_REGISTRATION",
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
    gate38_summary = read_json(GATE38_STATUS).get("summary", {})
    boundary_rows = _rows(GATE37_BOUNDARY_SPLIT)
    histogram_rows = _rows(GATE37_RAW_HISTOGRAMS)
    ess_rows = _rows(GATE37_ESS_PROXY)
    one_wall_rows = _rows(GATE37_ONE_WALL)
    dt_rows = _rows(GATE37_DT_REFINEMENT)
    corner_rows = _rows(GATE37_CORNER_HEATMAP)
    refinement_rows = _rows(GATE38_REFINEMENT)
    evidence_rows = evidence_index_rows(
        gate37_summary=gate37_summary,
        gate38_summary=gate38_summary,
        boundary_rows=boundary_rows,
        histogram_rows=histogram_rows,
        ess_rows=ess_rows,
        one_wall_rows=one_wall_rows,
        dt_rows=dt_rows,
        corner_rows=corner_rows,
        refinement_rows=refinement_rows,
    )
    readiness_rows = readiness_criteria_rows(
        gate37_summary=gate37_summary,
        gate38_summary=gate38_summary,
        evidence_rows=evidence_rows,
    )
    source_rows = source_lock_rows()
    firewall = no_proof_firewall_rows()
    proof_blocked = [
        row for row in readiness_rows if row["proof_status"] in {"missing", "partial"}
    ]
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "build_head": safe_git_head(),
        "gate37_disposition": gate37_summary.get("disposition", ""),
        "gate38_disposition": gate38_summary.get("disposition", ""),
        "evidence_index_rows": len(evidence_rows),
        "readiness_criteria_rows": len(readiness_rows),
        "source_lock_rows": len(source_rows),
        "source_missing_rows": sum(row["exists"] != "true" for row in source_rows),
        "boundary_atom_split_rows": len(boundary_rows),
        "raw_histogram_rows": len(histogram_rows),
        "ess_proxy_rows": len(ess_rows),
        "one_wall_suite_rows": len(one_wall_rows),
        "worst_case_dt_refinement_rows": len(dt_rows),
        "corner_heatmap_rows": len(corner_rows),
        "wall_pileup_refinement_rows": len(refinement_rows),
        "max_exact_boundary_atom_fraction": gate37_summary.get(
            "max_exact_boundary_atom_fraction"
        ),
        "max_near_boundary_band_fraction": gate37_summary.get(
            "max_near_boundary_band_fraction"
        ),
        "max_one_wall_positive_control_ks": gate37_summary.get(
            "max_one_wall_positive_control_ks"
        ),
        "projection_negative_control_status": gate37_summary.get(
            "projection_negative_control_status"
        ),
        "gate37_max_wall_pileup_ratio_superseded": gate37_summary.get(
            "max_wall_pileup_ratio"
        ),
        "wall_pileup_refinement_status": gate38_summary.get(
            "wall_pileup_refinement_status"
        ),
        "algorithmic_pileup_signal_rows": gate38_summary.get(
            "algorithmic_pileup_signal_rows"
        ),
        "max_expanded_first_vs_adjacent_gap_band_smoothed_ratio": gate38_summary.get(
            "max_expanded_first_vs_adjacent_gap_band_smoothed_ratio"
        ),
        "proof_readiness_status": (
            "not_ready_missing_timeseries_ess_clean_commit_and_authorization"
        ),
        "candidate_metric_hardening_status": "consolidated_candidate_ready",
        "proof_blocking_criteria_rows": len(proof_blocked),
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
        "evidence_index": evidence_rows,
        "readiness_criteria": readiness_rows,
        "source_locks": source_rows,
        "no_proof_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    evidence_ids = {row["evidence_id"] for row in payload["evidence_index"]}
    criteria_ids = {row["criterion_id"] for row in payload["readiness_criteria"]}
    exact_atom_value = s["max_exact_boundary_atom_fraction"]
    checks = {
        "Gate37 disposition": s["gate37_disposition"] == EXPECTED_GATE37_DISPOSITION,
        "Gate38 disposition": s["gate38_disposition"] == EXPECTED_GATE38_DISPOSITION,
        "Source lock complete": s["source_missing_rows"] == 0,
        "Evidence index complete": evidence_ids
        == {
            "exact_boundary_atom_split",
            "near_boundary_band_split",
            "raw_histograms",
            "ess_proxy",
            "one_wall_folded_normal_positive_control",
            "projection_clamp_negative_control",
            "rejection_resampling_negative_control",
            "worst_case_dt_refinement",
            "corner_heatmap",
            "wall_pileup_refinement",
        },
        "Readiness criteria complete": criteria_ids
        == {
            "exact_boundary_atoms_zero",
            "near_boundary_band_separated",
            "one_wall_positive_negative_controls",
            "dt_refinement_present",
            "corner_heatmap_present",
            "wall_pileup_sparse_proxy_resolved",
            "timeseries_ess",
            "reviewed_clean_commit_binding",
            "manual_authorization_ledger",
        },
        "Boundary split rows inherited": s["boundary_atom_split_rows"] >= 100,
        "Raw histogram rows inherited": s["raw_histogram_rows"] >= 300,
        "ESS rows inherited": s["ess_proxy_rows"] >= 100,
        "One-wall rows inherited": s["one_wall_suite_rows"] == 18,
        "Worst-case dt rows inherited": s["worst_case_dt_refinement_rows"] == 10,
        "Corner heatmap rows inherited": s["corner_heatmap_rows"] == 40,
        "Wall-pileup rows inherited": s["wall_pileup_refinement_rows"] == 12,
        "No exact atoms": exact_atom_value is not None and float(exact_atom_value) == 0.0,
        "Projection negative control": s["projection_negative_control_status"]
        == "expected_fail_observed",
        "No algorithmic pileup signal": s["algorithmic_pileup_signal_rows"] == 0,
        "Proof status stays not ready": s["proof_readiness_status"]
        == "not_ready_missing_timeseries_ess_clean_commit_and_authorization",
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
            "policy_impact": "consolidated_metric_hardening_candidate_only_no_proof_registration",
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
        "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_EVIDENCE_INDEX_20260701.csv": payload[
            "evidence_index"
        ],
        "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_READINESS_CRITERIA_20260701.csv": payload[
            "readiness_criteria"
        ],
        "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_SOURCE_LOCK_20260701.csv": payload[
            "source_locks"
        ],
        "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_NO_PROOF_FIREWALL_20260701.csv": payload[
            "no_proof_firewall"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    status_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_STATUS_20260701.json"
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

    master_md = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_REPORT_20260701.md"
    )
    write_md(
        master_md,
        "NODI COMSOL Package C Metric-Hardening Consolidation",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Evidence index rows: {payload['summary']['evidence_index_rows']}.",
            f"- Readiness criteria rows: {payload['summary']['readiness_criteria_rows']}.",
            f"- Exact boundary atom max: `{payload['summary']['max_exact_boundary_atom_fraction']}`.",
            f"- Gate37 wall-pileup proxy superseded: `{payload['summary']['gate37_max_wall_pileup_ratio_superseded']}`.",
            f"- Gate38 wall-pileup refinement status: `{payload['summary']['wall_pileup_refinement_status']}`.",
            f"- Proof readiness: `{payload['summary']['proof_readiness_status']}`.",
            "- Boundary: consolidated candidate only; no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no numeric PRS/EAS, no route/yield/detection/wet/fab/production claims.",
        ],
    )
    generated.append(master_md)

    public_report = (
        active_report_dir
        / "504_NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATION_20260701.md"
    )
    write_md(
        public_report,
        "NODI COMSOL Package C Metric Hardening Consolidation",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Source head: `{payload['summary']['build_head']}`",
            "- This packet folds Gate37 metric expansion and Gate38 wall-pileup refinement into one Package C evidence entrypoint.",
            f"- Evidence index rows: {payload['summary']['evidence_index_rows']}; readiness criteria rows: {payload['summary']['readiness_criteria_rows']}.",
            f"- Exact atom max: `{payload['summary']['max_exact_boundary_atom_fraction']}`; near-band max: `{payload['summary']['max_near_boundary_band_fraction']}`.",
            f"- One-wall positive-control max KS: `{payload['summary']['max_one_wall_positive_control_ks']}`; projection negative control: `{payload['summary']['projection_negative_control_status']}`.",
            f"- Gate37 wall-pileup ratio `{payload['summary']['gate37_max_wall_pileup_ratio_superseded']}` is superseded by Gate38 expanded-sampling diagnostics; algorithmic pile-up signal rows: `{payload['summary']['algorithmic_pileup_signal_rows']}`.",
            f"- Proof readiness remains `{payload['summary']['proof_readiness_status']}` because long-run timeseries ESS, reviewed clean-commit binding, and manual authorization are still missing.",
            "- Boundary: this is not a Package C proof/pass registration and does not authorize runtime, numeric PRS/EAS, COMSOL, .mph, solver, wet, route, yield, detection, fabrication, or production claims.",
            f"- Machine-readable support: `{rel(active_output_dir)}`.",
        ],
    )
    generated.append(public_report)

    manifest_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_MANIFEST_20260701.csv"
    )
    report_path = (
        active_output_dir
        / "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_REPORT_20260701.json"
    )
    report_outputs = [path.name for path in generated] + [
        report_path.name,
        manifest_path.name,
    ]
    write_json_atomic(
        report_path,
        {"summary": payload["summary"], "outputs": report_outputs},
    )
    generated.append(report_path)
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
    if not args.confirm_package_c_metric_hardening_consolidation:
        parser.error("--confirm-package-c-metric-hardening-consolidation is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_PACKAGE_C_METRIC_HARDENING_CONSOLIDATION")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
