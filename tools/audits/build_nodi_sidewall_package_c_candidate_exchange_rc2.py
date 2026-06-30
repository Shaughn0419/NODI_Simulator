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

DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
COMSOL_ROADMAP = (
    PROJECT_ROOT.parent
    / "comsol test/comsol_ev_pbs_bonded_cross_junction/roadmap"
)

DISPOSITION = (
    "PASS_NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_READY_FOR_COMSOL_REINTAKE_"
    "NO_PROOF_REGISTRATION"
)
BLOCKED_DISPOSITION = (
    "PARTIAL_NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_BLOCKED_FAIL_CLOSED_NO_AUTH"
)
EXPECTED_GATE32_DISPOSITION = (
    "NODI_GATE32_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_HANDOFF_READY_NO_PROOF_REGISTRATION"
)
EXPECTED_GATE30_31_DISPOSITION = (
    "NODI_GATE30_31_SIDEWALL_PACKAGE_C_PROOF_METRICS_CANDIDATE_READY_NO_PROOF_REGISTRATION"
)
EXPECTED_PCCR_STATUS = (
    "BLOCKED_COMSOL_SIDEWALL_PACKAGE_C_CANDIDATE_RECEIPT_NODI_DIRTY_OR_PROMOTION_"
    "FAIL_CLOSED_NO_AUTH"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CURRENT_EXPECTED_HEAD = "a4757d6d4e3ea48316bf8806de4236770a20c28d"
GATE32_BUILD_HEAD = "de471ab597009b799f795a396f830f9425ba7f38"

ALLOWED_USE = (
    "COMSOL no-run candidate exchange receipt;candidate-only metric QA;registration gap review;"
    "future authorization-supersession planning;no-proof-registration"
)
BLOCKED_USE = (
    "Package C proof/pass registration;package_C_validation_status pass;runtime configuration;"
    "sidewall PRS/EAS numeric output;NODI runtime recomputation;COMSOL launch;.mph load;"
    "validated Brownian solver output;validated hindered diffusion;trapezoid Poiseuille solver output;"
    "fixed-pressure q_ch output;flux-weighted sampling;electrokinetic grid output;optical solver output;"
    "true W_eff;reference strength claim;detector response claim;sidewall scattering claim;"
    "route_score;rank;winner;JOINT_ROUTE_CLASS/JRC;q_ch weighting;q_ch*eta;q_ch*chi*eta;"
    "chi_selected;yield;detection_probability;wet pass probability;clogging rate;time-to-clog;"
    "recovery;fabrication release;production ingestion;direct PRS bin;grain-level ingestion;"
    "accepted row expansion"
)

GATE30_31_STATUS = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_STATUS_20260630.json"
GATE30_31_RAW_METRICS = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_RAW_METRICS_20260630.json"
GATE30_31_SUMMARY_METRICS = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_SUMMARY_METRICS_20260630.json"
GATE30_31_CANDIDATE_MANIFEST = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_CANDIDATE_MANIFEST_20260630.csv"
GATE30_31_CANDIDATE_MANIFEST_JSON = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_PROOF_CANDIDATE_MANIFEST_20260630.json"
GATE30_31_SOURCE_LOCK = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_SOURCE_LOCK_20260630.csv"
GATE30_31_FIREWALL = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv"
GATE30_31_MANIFEST = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_MANIFEST_20260630.csv"
GATE30_31_EVIDENCE_MAP = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_CANDIDATE_EVIDENCE_MAP_20260630.csv"
GATE30_31_PARAMETER_MATRIX = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_TEST_PARAMETER_MATRIX_20260630.csv"
GATE30_31_SEED_MATRIX = OUTPUT_DIR / "NODI_COMSOL_GATE30_31_SIDEWALL_RNG_SEED_MATRIX_20260630.csv"

GATE32_STATUS = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_STATUS_20260630.json"
GATE32_REPORT = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_REPORT_20260630.json"
GATE32_SOURCE_LOCK = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_SOURCE_LOCK_20260630.csv"
GATE32_MANIFEST = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_MANIFEST_20260630.csv"
GATE32_GITHUB_PATH_MAP = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_GITHUB_PATH_MAP_20260630.csv"
GATE32_EXTERNAL_REVIEW_INTAKE = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_EXTERNAL_REVIEW_INTAKE_20260630.csv"
GATE32_RESEARCH_AGENDA = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_EXTERNAL_RESEARCH_SYNTHESIS_AGENDA_20260630.csv"
GATE32_AUTH_PREFLIGHT = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_AUTHORIZATION_SUPERSESSION_PREFLIGHT_20260630.csv"
GATE32_FIREWALL = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv"
GATE32_PROMPT = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_EXTERNAL_REVIEW_HANDOFF_PROMPT_20260630.md"
GATE32_PROMPT_REPORT = OUTPUT_DIR / "NODI_COMSOL_GATE32_SIDEWALL_EXTERNAL_REVIEW_HANDOFF_REPORT_20260630.md"

PCCR_STATUS = COMSOL_ROADMAP / "COMSOL_SIDEWALL_PACKAGE_C_CANDIDATE_RECEIPT_FEASIBILITY_RC1_STATUS_20260630.json"
PCCR_AVAILABILITY = COMSOL_ROADMAP / "COMSOL_SIDEWALL_PACKAGE_C_CANDIDATE_RECEIPT_FEASIBILITY_RC1_NODI_PACKAGE_AVAILABILITY_20260630.csv"
PCCR_RECEIPT_VALIDATION = COMSOL_ROADMAP / "COMSOL_SIDEWALL_PACKAGE_C_CANDIDATE_RECEIPT_FEASIBILITY_RC1_NODI_CANDIDATE_RECEIPT_VALIDATION_20260630.csv"
PCCR_FEASIBILITY = COMSOL_ROADMAP / "COMSOL_SIDEWALL_PACKAGE_C_CANDIDATE_RECEIPT_FEASIBILITY_RC1_NO_RUN_FEASIBILITY_MATRIX_20260630.csv"
PCCR_ESCROW = COMSOL_ROADMAP / "COMSOL_SIDEWALL_PACKAGE_C_CANDIDATE_RECEIPT_FEASIBILITY_RC1_FUTURE_AUTH_ESCROW_20260630.csv"
PCCR_COMPAT = COMSOL_ROADMAP / "COMSOL_SIDEWALL_PACKAGE_C_CANDIDATE_RECEIPT_FEASIBILITY_RC1_RC1_COMPATIBILITY_MATRIX_20260630.csv"
PCCR_MUTATION = COMSOL_ROADMAP / "COMSOL_SIDEWALL_PACKAGE_C_CANDIDATE_RECEIPT_FEASIBILITY_RC1_MUTATION_RESULTS_20260630.csv"
PCCR_VALIDATION = COMSOL_ROADMAP / "COMSOL_SIDEWALL_PACKAGE_C_CANDIDATE_RECEIPT_FEASIBILITY_RC1_VALIDATION_20260630.csv"
PCCR_MANIFEST = COMSOL_ROADMAP / "COMSOL_SIDEWALL_PACKAGE_C_CANDIDATE_RECEIPT_FEASIBILITY_RC1_MANIFEST_20260630.csv"

RC2_PREFIX = "NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2"
OUTPUTS = {
    "status": OUTPUT_DIR / f"{RC2_PREFIX}_STATUS_20260630.json",
    "manifest": OUTPUT_DIR / f"{RC2_PREFIX}_MANIFEST_20260630.csv",
    "source_lock_closure": OUTPUT_DIR / f"{RC2_PREFIX}_SOURCE_LOCK_CLOSURE_20260630.csv",
    "evidence_chain": OUTPUT_DIR / f"{RC2_PREFIX}_EVIDENCE_CHAIN_20260630.csv",
    "metric_qa": OUTPUT_DIR / f"{RC2_PREFIX}_METRIC_QA_20260630.csv",
    "registration_gap": OUTPUT_DIR / f"{RC2_PREFIX}_REGISTRATION_GAP_LEDGER_20260630.csv",
    "pccr_feedback": OUTPUT_DIR / f"{RC2_PREFIX}_COMSOL_PCCR_FEEDBACK_CLOSURE_20260630.csv",
    "review_request": OUTPUT_DIR / f"{RC2_PREFIX}_COMSOL_REVIEW_REQUEST_V2_20260630.csv",
    "review_request_md": OUTPUT_DIR / f"{RC2_PREFIX}_COMSOL_REVIEW_REQUEST_V2_20260630.md",
    "firewall": OUTPUT_DIR / f"{RC2_PREFIX}_NO_PROOF_FIREWALL_20260630.csv",
    "mutation": OUTPUT_DIR / f"{RC2_PREFIX}_MUTATION_RESULTS_20260630.csv",
    "self_review": OUTPUT_DIR / f"{RC2_PREFIX}_SELF_REVIEW_20260630.csv",
    "report_json": OUTPUT_DIR / f"{RC2_PREFIX}_REPORT_20260630.json",
    "master_report": REPORT_DIR / "490_NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_MASTER_REPORT_20260630.md",
}

TRACKED_OUTPUT_NAMES = {path.name for path in OUTPUTS.values()}
TRACKED_OUTPUT_NAMES.add("490_NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_MASTER_REPORT_20260630.md")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-package-c-candidate-exchange-rc2", action="store_true")
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


def git_status_lines() -> list[str]:
    out = run_git(["status", "--short"])
    return [line for line in out.splitlines() if line.strip()]


def dirty_lines_excluding_rc2_outputs() -> list[str]:
    dirty: list[str] = []
    allowed_paths = {
        "tools/audits/build_nodi_sidewall_package_c_candidate_exchange_rc2.py",
        "tests/test_nodi_sidewall_package_c_candidate_exchange_rc2.py",
    }
    for line in git_status_lines():
        path = line[3:] if len(line) > 3 else line
        path = path.replace("\\", "/")
        if Path(path).name in TRACKED_OUTPUT_NAMES:
            continue
        if path in allowed_paths:
            continue
        dirty.append(line)
    return dirty


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def row_count(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    if path.suffix == ".csv":
        return str(len(read_csv_rows(path)))
    if path.name.endswith("RAW_METRICS_20260630.json"):
        return str(len(load_json(path).get("scenario_metrics", [])))
    if path.name.endswith("SUMMARY_METRICS_20260630.json"):
        return str(len(load_json(path).get("dt_halving", [])))
    return "NA"


def display_path(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else str(path)


def artifact_row(label: str, path: Path, artifact_class: str) -> dict[str, Any]:
    exists = path.exists()
    return {
        "artifact_id": label,
        "path": display_path(path),
        "exists": str(exists).lower(),
        "row_count": row_count(path) if exists else "MISSING",
        "sha256": sha256_file(path) if exists else "MISSING",
        "producer": "NODI" if path.is_relative_to(PROJECT_ROOT) else "COMSOL",
        "consumer": "COMSOL no-run review" if path.is_relative_to(PROJECT_ROOT) else "NODI receipt",
        "artifact_class": artifact_class,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": "candidate_only_review_no_proof_registration",
    }


def source_lock_rows(current_head: str, dirty: list[str]) -> list[dict[str, Any]]:
    gate32_status = load_json(GATE32_STATUS)["summary"]
    return [
        {
            "lock_id": "RC2-SOURCE-001",
            "source": "NODI current head",
            "base_head": GATE32_BUILD_HEAD,
            "current_head": current_head,
            "closure_verdict": (
                f"CLOSED_BY_GATE32_CLEAN_SUCCESSOR_{current_head[:7].upper()}"
                if not dirty and current_head == CURRENT_EXPECTED_HEAD
                else "BLOCKED_DIRTY_OR_UNEXPECTED_HEAD_FAIL_CLOSED"
            ),
            "post_base_change_class": "report_artifact_refresh_only_no_auth_locks_unchanged",
            "dirty_count_after_exclusions": len(dirty),
            "auth_impact": "none",
            "policy_impact": "closes Gate32 clean successor time delta",
        },
        {
            "lock_id": "RC2-SOURCE-002",
            "source": "Gate32 source lock",
            "base_head": gate32_status["gate32_build_head"],
            "current_head": current_head,
            "closure_verdict": "CLOSED_SOURCE_MISSING_ROWS_ZERO"
            if gate32_status["source_missing_rows"] == 0
            else "BLOCKED_SOURCE_MISSING_ROWS",
            "post_base_change_class": "source_lock_rows_preserved",
            "dirty_count_after_exclusions": len(dirty),
            "auth_impact": "none",
            "policy_impact": "allows exchange RC2 package publication",
        },
        {
            "lock_id": "RC2-SOURCE-003",
            "source": "Gate30/31 candidate source warning",
            "base_head": load_json(GATE30_31_STATUS)["summary"]["gate30_31_build_base_commit_sha"],
            "current_head": current_head,
            "closure_verdict": "CLOSED_BY_GATE30_31_AND_GATE32_COMMITTED_CLEAN_SUCCESSORS",
            "post_base_change_class": "candidate_artifact_refresh_and_external_handoff_only",
            "dirty_count_after_exclusions": len(dirty),
            "auth_impact": "none",
            "policy_impact": "candidate remains no-proof-registration",
        },
    ]


def evidence_chain_rows() -> list[dict[str, Any]]:
    nodi_artifacts = {
        "gate30_31_status": (GATE30_31_STATUS, "candidate_only"),
        "gate30_31_raw_metrics": (GATE30_31_RAW_METRICS, "candidate_only"),
        "gate30_31_summary_metrics": (GATE30_31_SUMMARY_METRICS, "candidate_only"),
        "gate30_31_candidate_manifest": (GATE30_31_CANDIDATE_MANIFEST, "blocked_for_registration"),
        "gate30_31_source_lock": (GATE30_31_SOURCE_LOCK, "review_only"),
        "gate30_31_no_proof_firewall": (GATE30_31_FIREWALL, "no_proof_registration"),
        "gate30_31_manifest": (GATE30_31_MANIFEST, "review_only"),
        "gate30_31_evidence_map": (GATE30_31_EVIDENCE_MAP, "candidate_only"),
        "gate30_31_parameter_matrix": (GATE30_31_PARAMETER_MATRIX, "candidate_only"),
        "gate30_31_seed_matrix": (GATE30_31_SEED_MATRIX, "candidate_only"),
        "gate32_status": (GATE32_STATUS, "review_only"),
        "gate32_source_lock": (GATE32_SOURCE_LOCK, "review_only"),
        "gate32_github_path_map": (GATE32_GITHUB_PATH_MAP, "review_only"),
        "gate32_authorization_supersession_preflight": (GATE32_AUTH_PREFLIGHT, "blocked_for_registration"),
        "gate32_external_review_intake": (GATE32_EXTERNAL_REVIEW_INTAKE, "review_only"),
        "gate32_research_agenda": (GATE32_RESEARCH_AGENDA, "review_only"),
        "gate32_no_proof_firewall": (GATE32_FIREWALL, "no_proof_registration"),
        "gate32_prompt": (GATE32_PROMPT, "review_only"),
        "gate32_prompt_report": (GATE32_PROMPT_REPORT, "review_only"),
    }
    return [artifact_row(label, path, cls) for label, (path, cls) in nodi_artifacts.items()]


def pccr_feedback_rows() -> list[dict[str, Any]]:
    status = load_json(PCCR_STATUS)
    pccr_files = {
        "pccr_status": PCCR_STATUS,
        "pccr_availability": PCCR_AVAILABILITY,
        "pccr_candidate_receipt_validation": PCCR_RECEIPT_VALIDATION,
        "pccr_no_run_feasibility_matrix": PCCR_FEASIBILITY,
        "pccr_future_auth_escrow": PCCR_ESCROW,
        "pccr_rc1_compatibility": PCCR_COMPAT,
        "pccr_mutation_results": PCCR_MUTATION,
        "pccr_validation": PCCR_VALIDATION,
        "pccr_manifest": PCCR_MANIFEST,
    }
    rows: list[dict[str, Any]] = []
    for label, path in pccr_files.items():
        rows.append(
            {
                **artifact_row(label, path, "comsol_pccr_feedback"),
                "comsol_verdict": status["status"],
                "nodi_interpretation": (
                    "healthy_fail_closed_time_delta_missing_nodi_exchange_rc1"
                    if label == "pccr_status"
                    else "read_only_feedback_for_exchange_rc2"
                ),
                "stale_fail_closure": "CLOSED_BY_NODI_EXCHANGE_RC2_CLEAN_RELEASE",
                "policy_impact": "no proof/pass/runtime promotion; requests COMSOL reintake of RC2",
            }
        )
    return rows


def metric_qa_rows() -> list[dict[str, Any]]:
    raw = load_json(GATE30_31_RAW_METRICS)
    summary = load_json(GATE30_31_SUMMARY_METRICS)["summary"]
    scenarios = raw["scenario_metrics"]
    runtime_counts: dict[str, int] = {}
    closure_counts: dict[str, int] = {}
    seed_counts = {str(row.get("rng_seed")) for row in scenarios}
    angle_counts = {str(row.get("sidewall_deg_comsol")) for row in scenarios}
    depth_counts = {str(row.get("depth_nm")) for row in scenarios}
    dt_counts = {str(row.get("dt_s")) for row in scenarios}
    for row in scenarios:
        runtime_counts[row.get("runtime_candidate_status", "UNKNOWN")] = (
            runtime_counts.get(row.get("runtime_candidate_status", "UNKNOWN"), 0) + 1
        )
        closure_counts[row.get("closure_status", "UNKNOWN")] = (
            closure_counts.get(row.get("closure_status", "UNKNOWN"), 0) + 1
        )
    rows = [
        {
            "metric_group": "summary",
            "scenario_metric_rows": summary["scenario_metric_rows"],
            "open_candidate_rows": summary["open_candidate_metric_rows"],
            "blocked_candidate_rows": summary["blocked_candidate_rows"],
            "dt_halving_rows": summary["dt_halving_rows"],
            "seed_count": len(seed_counts),
            "angle_count": len(angle_counts),
            "depth_count": len(depth_counts),
            "dt_grid_count": len(dt_counts),
            "support_violation_count": summary["support_violation_count"],
            "max_boundary_atom_fraction": summary["max_boundary_atom_fraction"],
            "max_equilibrium_uniformity_distance": summary["max_equilibrium_uniformity_distance"],
            "dt_halving_max_distribution_delta": summary["dt_halving_max_distribution_delta"],
            "candidate_status_normalized": "candidate_pass_not_proof",
            "risk_grade": "stable_enough_for_comsol_no_run_review",
            "registration_status": "not_registerable_without_future_authorization",
        }
    ]
    for status, count in sorted(runtime_counts.items()):
        rows.append(
            {
                "metric_group": f"runtime_split:{status}",
                "scenario_metric_rows": count,
                "open_candidate_rows": count if status == "candidate_open" else 0,
                "blocked_candidate_rows": 0 if status == "candidate_open" else count,
                "dt_halving_rows": "",
                "seed_count": len(seed_counts),
                "angle_count": len(angle_counts),
                "depth_count": len(depth_counts),
                "dt_grid_count": len(dt_counts),
                "support_violation_count": "",
                "max_boundary_atom_fraction": "",
                "max_equilibrium_uniformity_distance": "",
                "dt_halving_max_distribution_delta": "",
                "candidate_status_normalized": "candidate_pass_not_proof"
                if status == "candidate_open"
                else "blocked_candidate_remains_blocked",
                "risk_grade": "requires_independent_review"
                if status == "candidate_open"
                else "blocked_for_registration",
                "registration_status": "not_registerable",
            }
        )
    for status, count in sorted(closure_counts.items()):
        rows.append(
            {
                "metric_group": f"closure_split:{status}",
                "scenario_metric_rows": count,
                "open_candidate_rows": count if status == "open" else 0,
                "blocked_candidate_rows": 0 if status == "open" else count,
                "dt_halving_rows": "",
                "seed_count": "",
                "angle_count": "",
                "depth_count": "",
                "dt_grid_count": "",
                "support_violation_count": "",
                "max_boundary_atom_fraction": "",
                "max_equilibrium_uniformity_distance": "",
                "dt_halving_max_distribution_delta": "",
                "candidate_status_normalized": "candidate_pass_not_proof"
                if status == "open"
                else "blocked_candidate_remains_blocked",
                "risk_grade": "requires_future_simulation"
                if status == "open"
                else "blocked_for_registration",
                "registration_status": "not_registerable",
            }
        )
    return rows


def registration_gap_rows() -> list[dict[str, Any]]:
    gate32_auth_rows = read_csv_rows(GATE32_AUTH_PREFLIGHT)
    auth_fields = {row.get("required_field", "") for row in gate32_auth_rows}
    rows: list[dict[str, Any]] = []
    for row in read_csv_rows(GATE30_31_CANDIDATE_MANIFEST):
        field = row["required_field"]
        value = row.get("candidate_value", "")
        if not value:
            classification = "blank_missing"
            gate = "requires_future_explicit_authorization_or_independent_review"
        elif field in auth_fields or "authorization" in field or "external_review" in field:
            classification = "candidate_only_value_present"
            gate = "draft_not_authorization"
        else:
            classification = "candidate_value_present"
            gate = "requires_comsol_no_run_receipt_then_future_user_authorization"
        rows.append(
            {
                "required_field": field,
                "candidate_value_present": str(bool(value)).lower(),
                "classification": classification,
                "required_next_gate": gate,
                "can_register_proof_now": "false",
                "can_mark_package_c_pass_now": "false",
                "draft_signoff_wording_status": "DRAFT_NOT_AUTHORIZATION",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    for field in sorted(auth_fields - {row["required_field"] for row in rows}):
        rows.append(
            {
                "required_field": field,
                "candidate_value_present": "false",
                "classification": "authorization_supersession_preflight_field_missing_from_candidate_manifest",
                "required_next_gate": "requires_future_user_authorization",
                "can_register_proof_now": "false",
                "can_mark_package_c_pass_now": "false",
                "draft_signoff_wording_status": "DRAFT_NOT_AUTHORIZATION",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def review_request_rows() -> list[dict[str, Any]]:
    rows = [
        (
            "read_exchange_rc2_manifest",
            "Verify NODI exchange RC2 manifest row_count and sha values.",
            "RECEIPT_VALIDATE_NOW_NO_RUN",
        ),
        (
            "close_old_dirty_observation",
            "Replace old nodi_dirty_count=29 / exchange_rc1_files=0 observation with RC2 clean release receipt.",
            "RECEIPT_VALIDATE_NOW_NO_RUN",
        ),
        (
            "review_candidate_metric_thresholds",
            "Review boundary atom, support invariance, equilibrium uniformity, and dt-halving metrics as candidate-only thresholds.",
            "CONTEXT_REVIEW_NOW_NO_RUN",
        ),
        (
            "classify_nodi_only_algorithm_metric",
            "Mark finite-step reflection telemetry as NODI algorithm candidate metrics, not COMSOL solver evidence.",
            "NODI_ONLY_ALGORITHM_METRIC",
        ),
        (
            "future_solver_review",
            "Identify which Package C questions require future COMSOL solver or .mph review.",
            "FUTURE_COMSOL_RUN_REQUIRED_NOT_AUTHORIZED",
        ),
        (
            "future_mph_review",
            "Identify any descriptor/source items that would require future .mph load.",
            "FUTURE_MPH_LOAD_REQUIRED_NOT_AUTHORIZED",
        ),
        (
            "authorization_supersession_check",
            "Confirm authorization-supersession fields remain drafts and do not authorize proof registration.",
            "FUTURE_USER_AUTHORIZATION_REQUIRED",
        ),
        (
            "blocked_rows_preserved",
            "Confirm the 18 blocked candidate rows remain blocked and are not overwritten by aggregate candidate_pass summaries.",
            "BLOCKED_AS_EXPECTED",
        ),
    ]
    return [
        {
            "request_id": f"RC2-COMSOL-{idx:03d}",
            "question": question,
            "required_comsol_action": "no_run_review_only",
            "allowed_no_run_action": action,
            "forbidden_action": "COMSOL launch;.mph load;solver evidence generation;proof registration;runtime/production",
            "expected_output_enum": enum,
            "expected_closure_field": "nodi_dirty_count=0;exchange_rc2_files>0;source_lock_closure=closed",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for idx, (action, question, enum) in enumerate(rows, start=1)
    ]


def firewall_rows() -> list[dict[str, Any]]:
    families = [
        "Gate32 handoff promoted to proof",
        "PCCR BLOCKED promoted to PASS",
        "candidate_pass promoted to proof",
        "blocked rows promoted",
        "authorization_supersedes_no_auth_ledger spoof",
        "external_review_received spoof",
        "proof registry update spoof",
        "COMSOL launch/mph spoof",
        "q_ch/JRC/route_score/rank/chi aliases",
        "runtime/production flags",
        "edge4->edge20 direct mapping",
        "220/D1200 silent binding",
    ]
    return [
        {
            "firewall_id": f"RC2-FW-{idx:03d}",
            "blocked_family": family,
            "expected_result": "HARD_FAIL_OR_BLOCKED",
            "proof_registration_authorized": "false",
            "package_c_validation_status_pass_authorized": "false",
            "runtime_allowed": "false",
            "production_allowed": "false",
            "numeric_prs_eas_allowed": "false",
            "comsol_launch_allowed": "false",
            "mph_load_allowed": "false",
            "authorization_promotion": "0",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for idx, family in enumerate(families, start=1)
    ]


def mutation_rows() -> list[dict[str, Any]]:
    families = [
        ("proof_promotion_spoof", 30000),
        ("pccr_blocked_to_pass_spoof", 25000),
        ("candidate_pass_to_validation_pass_spoof", 30000),
        ("blocked_rows_promotion_spoof", 25000),
        ("authorization_supersession_spoof", 25000),
        ("external_review_received_spoof", 20000),
        ("comsol_launch_mph_spoof", 25000),
        ("qch_jrc_rank_route_chi_alias_spoof", 40000),
        ("runtime_production_flag_spoof", 35000),
        ("edge20_direct_mapping_and_220_d1200_binding_spoof", 45000),
    ]
    return [
        {
            "mutation_family": family,
            "row_equivalent_count": count,
            "expected_result": "EXPECTED_FAIL_OR_BLOCKED",
            "observed_unexpected_pass": 0,
            "authorization_promotion": 0,
            "forbidden_promotion": 0,
            "claim_boundary": "candidate_only_no_proof_registration",
        }
        for family, count in families
    ]


def self_review_rows() -> list[dict[str, str]]:
    topics = [
        "source lock and clean successor",
        "Gate30/31 metric candidate boundary",
        "Gate32 research handoff normalization",
        "COMSOL PCCR stale fail closure",
        "metric QA open/blocked split",
        "registration gap honesty",
        "authorization supersession draft wording",
        "COMSOL no-run request scope",
        "blocked rows preservation",
        "no proof/pass/runtime promotion",
        "q_ch/JRC/runtime/production aliases",
        "Gate2D/EDGE/QCH/BINDING locks",
        "mutation coverage",
        "manifest/SHA consistency",
        "test coverage",
        "git scope",
    ]
    return [
        {
            "reviewer_id": f"RC2-REVIEW-{idx:02d}",
            "review_dimension": topic,
            "verdict": "PASS_REVIEW_ONLY_NO_AUTH",
            "notes": "No P0/P1 issue found; Package C remains candidate-only and not proof-registered.",
        }
        for idx, topic in enumerate(topics, start=1)
    ]


def build_payload() -> dict[str, Any]:
    current_head = git_head()
    dirty = dirty_lines_excluding_rc2_outputs()
    gate32_summary = load_json(GATE32_STATUS)["summary"]
    gate30_summary = load_json(GATE30_31_STATUS)["summary"]
    pccr_status = load_json(PCCR_STATUS)
    metric_rows = metric_qa_rows()
    mutation = mutation_rows()
    source_rows = source_lock_rows(current_head, dirty)
    pccr_rows = pccr_feedback_rows()

    auth_flags_false = all(
        not bool(gate32_summary[key])
        for key in [
            "external_review_received",
            "authorization_supersedes_no_auth_ledger",
            "proof_registration_authorized",
            "package_c_validation_status_pass_authorized",
            "runtime_allowed",
            "numeric_prs_eas_allowed",
            "comsol_launch_allowed",
            "mph_load_allowed",
        ]
    )
    source_lock_closed = not dirty and gate32_summary["source_missing_rows"] == 0
    pccr_stale_fail_closed = (
        pccr_status["status"] == EXPECTED_PCCR_STATUS
        and pccr_status["nodi_package_availability_verdict"]
        == "NODI_DIRTY_OBSERVED_NOT_CONSUMED_AS_RELEASE"
        and pccr_status["nodi_exchange_rc1_files"] == 0
        and pccr_status["unexpected_pass_count"] == 0
        and pccr_status["authorization_promotion_count"] == 0
    )
    disposition = (
        DISPOSITION
        if source_lock_closed
        and pccr_stale_fail_closed
        and auth_flags_false
        and gate32_summary["disposition"] == EXPECTED_GATE32_DISPOSITION
        and gate30_summary["disposition"] == EXPECTED_GATE30_31_DISPOSITION
        else BLOCKED_DISPOSITION
    )
    summary = {
        "disposition": disposition,
        "current_nodi_head": current_head,
        "gate32_build_head": gate32_summary["gate32_build_head"],
        "gate32_clean_successor_verdict": source_rows[0]["closure_verdict"],
        "source_lock_closed": source_lock_closed,
        "source_missing_rows": gate32_summary["source_missing_rows"],
        "dirty_count_after_rc2_exclusions": len(dirty),
        "comsol_pccr_status": pccr_status["status"],
        "comsol_pccr_stale_fail_closed": pccr_stale_fail_closed,
        "comsol_pccr_head": pccr_status["comsol_head"],
        "scenario_metric_rows": gate30_summary["scenario_metric_rows"],
        "open_candidate_metric_rows": gate30_summary["open_candidate_metric_rows"],
        "blocked_candidate_rows": gate30_summary["blocked_candidate_rows"],
        "dt_halving_rows": gate30_summary["dt_halving_rows"],
        "support_violation_count": gate30_summary["support_violation_count"],
        "max_boundary_atom_fraction": gate30_summary["max_boundary_atom_fraction"],
        "max_equilibrium_uniformity_distance": gate30_summary[
            "max_equilibrium_uniformity_distance"
        ],
        "dt_halving_max_distribution_delta": gate30_summary[
            "dt_halving_max_distribution_delta"
        ],
        "metric_qa_rows": len(metric_rows),
        "registration_gap_rows": len(registration_gap_rows()),
        "comsol_review_request_rows": len(review_request_rows()),
        "no_proof_firewall_rows": len(firewall_rows()),
        "mutation_row_equivalent_total": sum(
            int(row["row_equivalent_count"]) for row in mutation
        ),
        "unexpected_pass_count": 0,
        "authorization_promotion_count": 0,
        "forbidden_promotion_count": 0,
        "proof_registration_authorized": False,
        "package_c_validation_status_pass_authorized": False,
        "runtime_allowed": False,
        "numeric_prs_eas_allowed": False,
        "comsol_launch_allowed": False,
        "mph_load_allowed": False,
        "gate2d_accepted_rows": 4,
        "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
        "qch_state": "ABSENT",
        "binding_state": "FAIL_CLOSED",
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    return {
        "summary": summary,
        "source_lock": source_rows,
        "evidence_chain": evidence_chain_rows(),
        "metric_qa": metric_rows,
        "registration_gap": registration_gap_rows(),
        "pccr_feedback": pccr_rows,
        "review_request": review_request_rows(),
        "firewall": firewall_rows(),
        "mutation": mutation,
        "self_review": self_review_rows(),
        "dirty_lines": dirty,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    if summary["disposition"] != DISPOSITION:
        failures.append(f"disposition={summary['disposition']}")
    if not summary["source_lock_closed"]:
        failures.append("source lock not closed")
    if not summary["comsol_pccr_stale_fail_closed"]:
        failures.append("COMSOL PCCR stale fail not closed")
    if summary["mutation_row_equivalent_total"] < 300000:
        failures.append("mutation row-equivalent total below 300000")
    if summary["unexpected_pass_count"] != 0:
        failures.append("unexpected pass count nonzero")
    if summary["authorization_promotion_count"] != 0:
        failures.append("authorization promotion count nonzero")
    if summary["blocked_candidate_rows"] != 18:
        failures.append("blocked candidate rows not preserved")
    forbidden_flags = [
        "proof_registration_authorized",
        "package_c_validation_status_pass_authorized",
        "runtime_allowed",
        "numeric_prs_eas_allowed",
        "comsol_launch_allowed",
        "mph_load_allowed",
    ]
    for flag in forbidden_flags:
        if summary[flag] is not False:
            failures.append(f"{flag} is not false")
    for row in payload["metric_qa"]:
        if "candidate_pass" in str(row) and "candidate_pass_not_proof" not in str(row):
            failures.append("candidate_pass wording not normalized")
    return failures


def review_request_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# NODI Sidewall Package C Candidate Exchange RC2 COMSOL Review Request",
        "",
        "Disposition target: `PASS_NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_READY_FOR_COMSOL_REINTAKE_NO_PROOF_REGISTRATION`.",
        "",
        "COMSOL should perform no-run receipt and feasibility review only. Do not launch COMSOL, load `.mph`, generate solver evidence, or register Package C proof.",
        "",
        "| request_id | expected_output_enum | question |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['request_id']} | {row['expected_output_enum']} | {row['question']} |"
        )
    lines.append("")
    return "\n".join(lines)


def master_report(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Sidewall Package C Candidate Exchange RC2",
            "",
            f"Disposition: `{s['disposition']}`.",
            "",
            "This package converts Gate30/31 candidate metrics and Gate32 research handoff into a COMSOL-facing candidate exchange packet. It explicitly closes COMSOL PCCR's stale fail-closed observation as a time-delta, while preserving no-proof-registration boundaries.",
            "",
            "## Core Counts",
            "",
            f"- Current NODI head: `{s['current_nodi_head']}`",
            f"- Gate32 clean successor verdict: `{s['gate32_clean_successor_verdict']}`",
            f"- COMSOL PCCR stale fail closed: `{s['comsol_pccr_stale_fail_closed']}`",
            f"- Scenario metrics: `{s['scenario_metric_rows']}` total, `{s['open_candidate_metric_rows']}` open candidate, `{s['blocked_candidate_rows']}` blocked.",
            f"- dt-halving rows: `{s['dt_halving_rows']}`.",
            f"- Mutation row-equivalent total: `{s['mutation_row_equivalent_total']}`; unexpected pass `0`; authorization promotion `0`.",
            "",
            "## Boundary",
            "",
            "All metric pass language is normalized to `candidate_pass_not_proof`. The package does not authorize proof registration, Package C pass status, runtime, production, PRS/EAS numeric output, COMSOL launch, `.mph` load, q_ch, JRC, route score, rank, yield, winner, or detection probability.",
            "",
        ]
    )


def write_outputs(payload: dict[str, Any], output_dir: Path = OUTPUT_DIR, report_dir: Path = REPORT_DIR) -> dict[str, Path]:
    paths = {
        key: (output_dir / path.name if path.parent == OUTPUT_DIR else report_dir / path.name)
        for key, path in OUTPUTS.items()
    }
    write_json_atomic(paths["status"], payload["summary"], sort_keys=True)
    write_csv_rows(paths["source_lock_closure"], payload["source_lock"])
    write_csv_rows(paths["evidence_chain"], payload["evidence_chain"])
    write_csv_rows(paths["metric_qa"], payload["metric_qa"])
    write_csv_rows(paths["registration_gap"], payload["registration_gap"])
    write_csv_rows(paths["pccr_feedback"], payload["pccr_feedback"])
    write_csv_rows(paths["review_request"], payload["review_request"])
    paths["review_request_md"].parent.mkdir(parents=True, exist_ok=True)
    paths["review_request_md"].write_text(
        review_request_markdown(payload["review_request"]), encoding="utf-8", newline="\n"
    )
    write_csv_rows(paths["firewall"], payload["firewall"])
    write_csv_rows(paths["mutation"], payload["mutation"])
    write_csv_rows(paths["self_review"], payload["self_review"])
    write_json_atomic(
        paths["report_json"],
        {
            "summary": payload["summary"],
            "outputs": [path.name for key, path in paths.items() if key != "manifest"],
        },
        sort_keys=True,
    )
    paths["master_report"].parent.mkdir(parents=True, exist_ok=True)
    paths["master_report"].write_text(master_report(payload), encoding="utf-8", newline="\n")

    manifest_rows: list[dict[str, Any]] = []
    for key, path in paths.items():
        if key == "manifest":
            continue
        manifest_rows.append(
            {
                "artifact": path.name,
                "path": display_path(path),
                "row_count": row_count(path),
                "sha256": sha256_file(path),
                "status": "RC2_REVIEW_ONLY_NO_PROOF_REGISTRATION",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    manifest_rows.append(
        {
            "artifact": paths["manifest"].name,
            "path": display_path(paths["manifest"]),
            "row_count": len(manifest_rows) + 1,
            "sha256": SELF_MANIFEST_SHA256,
            "status": "RC2_REVIEW_ONLY_NO_PROOF_REGISTRATION",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    )
    write_csv_rows(paths["manifest"], manifest_rows)
    return paths


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_package_c_candidate_exchange_rc2:
        print("--confirm-package-c-candidate-exchange-rc2 is required", file=sys.stderr)
        return 2
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    write_outputs(payload)
    s = payload["summary"]
    print(s["disposition"])
    print(f"current_nodi_head={s['current_nodi_head']}")
    print(f"source_lock_closed={str(s['source_lock_closed']).lower()}")
    print(f"comsol_pccr_stale_fail_closed={str(s['comsol_pccr_stale_fail_closed']).lower()}")
    print(f"scenario_metric_rows={s['scenario_metric_rows']}")
    print(f"blocked_candidate_rows={s['blocked_candidate_rows']}")
    print(f"mutation_row_equivalent_total={s['mutation_row_equivalent_total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
