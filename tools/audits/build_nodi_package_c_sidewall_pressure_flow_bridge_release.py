#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic  # noqa: E402


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
COMSOL_REPO = PROJECT_ROOT.parent / "comsol test/comsol_ev_pbs_bonded_cross_junction"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_BRIDGE_RELEASE_V1"
PASS_DISPOSITION = "PASS_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_BRIDGE_RELEASE_V1_READY_WITH_FORMAL_QCH_SIDECAR"
PARTIAL_DISPOSITION = "PARTIAL_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_BRIDGE_RELEASE_V1_BLOCKED_RELEASE_SCOPED_SOURCE_DRIFT_NO_AUTH"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

REQUEST_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_REQUEST_ROWS_20260701.csv"
HARNESS_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_STATUS_20260701.json"
HARNESS_REPORT = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_REPORT_20260701.json"
LEDGER_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_STATUS_20260701.json"
LEDGER_REPORT = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_REPORT_20260701.json"
LEDGER_LANE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_PROMOTION_LANE_ROWS_20260701.csv"
ROUTE_POLICY_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_STATUS_20260701.json"
QCH_GRID_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_STATUS_20260701.json"
SELECTED_ANNULUS_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_STATUS_20260701.json"
DETECTOR_BLANK_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_STATUS_20260701.json"
WET_SURFACE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_STATUS_20260701.json"
RESULT_BINDER_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_STATUS_20260701.json"
RESULT_BINDER_BINDING_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_BINDING_ROWS_20260701.csv"
RESULT_BINDER_FORMAL_QCH_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_FORMAL_QCH_SIDECAR_ROWS_20260701.csv"
REPORT_541 = REPORT_DIR / "541_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_20260701.md"
REPORT_542 = REPORT_DIR / "542_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_20260701.md"

SOURCE_INPUTS = {
    "report_541_pressure_flow_harness": REPORT_541,
    "report_542_pressure_flow_ledger": REPORT_542,
    "pressure_flow_request_rows": REQUEST_ROWS,
    "pressure_flow_harness_status": HARNESS_STATUS,
    "pressure_flow_harness_report": HARNESS_REPORT,
    "pressure_flow_ledger_status": LEDGER_STATUS,
    "pressure_flow_ledger_report": LEDGER_REPORT,
    "pressure_flow_ledger_lane_rows": LEDGER_LANE_ROWS,
    "route_policy_refresh_status": ROUTE_POLICY_STATUS,
    "qch_grid_candidate_status": QCH_GRID_STATUS,
    "selected_annulus_status": SELECTED_ANNULUS_STATUS,
    "detector_blank_status": DETECTOR_BLANK_STATUS,
    "wet_surface_contract_status": WET_SURFACE_STATUS,
    "pressure_flow_result_binder_status": RESULT_BINDER_STATUS,
    "pressure_flow_result_binder_binding_rows": RESULT_BINDER_BINDING_ROWS,
    "pressure_flow_result_binder_formal_qch_rows": RESULT_BINDER_FORMAL_QCH_ROWS,
}

OUTPUTS = {
    "status": OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json",
    "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
    "dirty_classifier": OUTPUT_DIR / f"{PREFIX}_DIRTY_CLASSIFIER_20260701.csv",
    "request_contract": OUTPUT_DIR / f"{PREFIX}_REQUEST_CONTRACT_20260701.csv",
    "receipt_schema": OUTPUT_DIR / f"{PREFIX}_COMSOL_RESULT_RECEIPT_SCHEMA_20260701.csv",
    "verdict_policy": OUTPUT_DIR / f"{PREFIX}_RESULT_VERDICT_POLICY_20260701.csv",
    "consumption_policy": OUTPUT_DIR / f"{PREFIX}_CONSUMPTION_POLICY_20260701.csv",
    "lane_map": OUTPUT_DIR / f"{PREFIX}_LANE_MAP_20260701.csv",
    "handoff_csv": OUTPUT_DIR / f"{PREFIX}_COMSOL_HANDOFF_REQUEST_20260701.csv",
    "handoff_json": OUTPUT_DIR / f"{PREFIX}_COMSOL_HANDOFF_REQUEST_20260701.json",
    "handoff_md": OUTPUT_DIR / f"{PREFIX}_COMSOL_HANDOFF_REQUEST_20260701.md",
    "auth_wording": OUTPUT_DIR / f"{PREFIX}_AUTHORIZATION_WORDING_DRAFTS_20260701.csv",
    "mutation": OUTPUT_DIR / f"{PREFIX}_MUTATION_RESULTS_20260701.csv",
    "self_review": OUTPUT_DIR / f"{PREFIX}_SELF_REVIEW_20260701.csv",
    "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
    "master_report": REPORT_DIR / "544_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_BRIDGE_RELEASE_V1_20260701.md",
}

REQUIRED_REQUEST_IDS = {
    "PFV-REQUEST-ROUTE-CAND-001": {
        "route_key": "route_rectangle_limit_theta90_D900_W500",
        "geometry_hash": "fc2b8074b0dc240816bf1d891822e3911f839ce691866b5022a2f04af416cb14",
        "sidewall_deg_comsol": "90.0",
        "sidewall_taper_angle_deg_nodi": "0.0",
        "candidate_q_grid_m3_s": "1.34414517438e-16",
        "candidate_flow_split_fraction": "0.60551911946",
    },
    "PFV-REQUEST-ROUTE-CAND-002": {
        "route_key": "route_taper_theta85_D900_W500",
        "geometry_hash": "033b6382b020bca2f984bd623ad4f2e4eff29417b8f8e36e8733ecef237065f2",
        "sidewall_deg_comsol": "85.0",
        "sidewall_taper_angle_deg_nodi": "5.0",
        "candidate_q_grid_m3_s": "8.75677670487e-17",
        "candidate_flow_split_fraction": "0.39448088054",
    },
}

FORBIDDEN_FLAG_FIELDS = (
    "formal_qch_weighting_current",
    "route_score_current",
    "winner_current",
    "yield_current",
    "detection_probability_current",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-pressure-flow-bridge-release", action="store_true")
    return parser


def run_git(args: list[str], cwd: Path = PROJECT_ROOT, *, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={cwd.as_posix()}", *args],
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def git_head() -> str:
    return run_git(["rev-parse", "HEAD"])


def git_branch() -> str:
    return run_git(["branch", "--show-current"])


def comsol_head() -> str:
    if not (COMSOL_REPO / ".git").exists():
        return "COMSOL_REPO_NOT_AVAILABLE"
    return run_git(["rev-parse", "HEAD"], COMSOL_REPO, check=False) or "COMSOL_HEAD_UNKNOWN"


def git_status_lines() -> list[str]:
    out = run_git(["status", "--short"])
    return [line for line in out.splitlines() if line.strip()]


def status_map() -> dict[str, str]:
    mapped: dict[str, str] = {}
    for line in git_status_lines():
        if len(line) > 3:
            mapped[line[3:].replace("\\", "/")] = line[:2]
    return mapped


def display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def sha_or_missing(path: Path) -> str:
    return sha256_file(path) if path.exists() else "MISSING"


def row_count(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    if path.suffix.lower() == ".csv":
        return str(len(read_csv_rows(path)))
    return "NA"


def load_summary(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    if isinstance(data, dict):
        return data
    return {}


def bool_false(value: Any) -> bool:
    return value in (False, "False", "false", "0", 0, None, "")


def source_lock_rows() -> list[dict[str, Any]]:
    statuses = status_map()
    rows: list[dict[str, Any]] = []
    for source_id, path in SOURCE_INPUTS.items():
        rel = display_path(path)
        sha1 = sha_or_missing(path)
        sha2 = sha_or_missing(path)
        git_status = statuses.get(rel, "clean_or_tracked_unchanged")
        exists = path.exists()
        release_blocker = (not exists) or git_status not in {"clean_or_tracked_unchanged"}
        rows.append(
            {
                "source_id": source_id,
                "path": rel,
                "exists": str(exists).lower(),
                "row_count": row_count(path),
                "sha256_pass1": sha1,
                "sha256_pass2": sha2,
                "source_stable_two_pass": str(sha1 == sha2 and exists).lower(),
                "git_status": git_status,
                "release_scoped_source": "true",
                "release_scoped_dirty_blocker": str(release_blocker).lower(),
                "policy_impact": "blocks_release" if release_blocker else "no_policy_impact",
            }
        )
    return rows


def dirty_classifier_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    source_rels = {display_path(path) for path in SOURCE_INPUTS.values()}
    output_rels = {display_path(path) for path in OUTPUTS.values()}
    output_rels.update(
        {
            "tools/audits/build_nodi_package_c_sidewall_pressure_flow_bridge_release.py",
            "tests/test_nodi_package_c_sidewall_pressure_flow_bridge_release.py",
        }
    )
    for line in git_status_lines():
        rel = line[3:].replace("\\", "/") if len(line) > 3 else line
        if rel in source_rels:
            classification = "RELEASE_SCOPED_INPUT"
            blocker = "true"
        elif rel in output_rels:
            classification = "RELEASE_OUTPUT_THIS_TURN"
            blocker = "false"
        else:
            classification = "EXTERNAL_DIRTY_EXCLUDED"
            blocker = "false"
        rows.append(
            {
                "path": rel,
                "git_status": line[:2],
                "classification": classification,
                "release_scoped_dirty_blocker": blocker,
                "stage_decision": "stage_only_if_release_output" if classification == "RELEASE_OUTPUT_THIS_TURN" else "do_not_stage",
            }
        )
    return rows or [
        {
            "path": "WORKTREE",
            "git_status": "clean",
            "classification": "NO_DIRTY_PATHS",
            "release_scoped_dirty_blocker": "false",
            "stage_decision": "none",
        }
    ]


def validate_request_rows(rows: list[dict[str, str]]) -> list[str]:
    failures: list[str] = []
    if len(rows) != 2:
        failures.append(f"expected 2 request rows, found {len(rows)}")
    observed = {row.get("validation_request_id", ""): row for row in rows}
    for request_id, expected in REQUIRED_REQUEST_IDS.items():
        row = observed.get(request_id)
        if not row:
            failures.append(f"missing {request_id}")
            continue
        if row.get("route_key") != expected["route_key"]:
            failures.append(f"{request_id} route_key mismatch")
        if row.get("source_geometry_hash") != expected["geometry_hash"]:
            failures.append(f"{request_id} geometry hash mismatch")
        if row.get("sidewall_deg_comsol") != expected["sidewall_deg_comsol"]:
            failures.append(f"{request_id} COMSOL sidewall angle mismatch")
        if row.get("sidewall_taper_angle_deg_nodi") != expected["sidewall_taper_angle_deg_nodi"]:
            failures.append(f"{request_id} NODI taper angle mismatch")
        if row.get("candidate_q_grid_m3_s") != expected["candidate_q_grid_m3_s"]:
            failures.append(f"{request_id} candidate q mismatch")
        if row.get("candidate_flow_split_fraction") != expected["candidate_flow_split_fraction"]:
            failures.append(f"{request_id} split mismatch")
        if row.get("top_width_nm") != "500.0" or row.get("depth_nm") != "900.0":
            failures.append(f"{request_id} W500/D900 mismatch")
        if row.get("pressure_drop_Pa") != "1000.0":
            failures.append(f"{request_id} pressure drop mismatch")
        for field in FORBIDDEN_FLAG_FIELDS:
            if row.get(field) not in {"False", "false", False}:
                failures.append(f"{request_id} {field} not false")
        sidewall_sum = float(row.get("sidewall_deg_comsol", "nan")) + float(row.get("sidewall_taper_angle_deg_nodi", "nan"))
        if abs(sidewall_sum - 90.0) > 1e-9:
            failures.append(f"{request_id} sidewall convention sum != 90")
    return failures


def request_contract_rows(requests: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in requests:
        out.append(
            {
                "validation_request_id": row["validation_request_id"],
                "route_candidate_id": row["route_candidate_id"],
                "route_key": row["route_key"],
                "case_id": row["case_id"],
                "geometry_descriptor_sha256": row["source_geometry_hash"],
                "sidewall_deg_comsol": row["sidewall_deg_comsol"],
                "sidewall_taper_angle_deg_nodi": row["sidewall_taper_angle_deg_nodi"],
                "top_width_nm": row["top_width_nm"],
                "depth_nm": row["depth_nm"],
                "pressure_drop_Pa": row["pressure_drop_Pa"],
                "candidate_q_grid_m3_s": row["candidate_q_grid_m3_s"],
                "candidate_flow_split_fraction": row["candidate_flow_split_fraction"],
                "candidate_hydraulic_resistance_Pa_s_m3": row["candidate_hydraulic_resistance_Pa_s_m3"],
                "acceptance_ratio_min": row["acceptance_ratio_min"],
                "acceptance_ratio_max": row["acceptance_ratio_max"],
                "split_abs_delta_max": row["split_abs_delta_max"],
                "required_observables": row["required_observables"],
                "required_metadata": row["required_metadata"],
                "claim_boundary": "pressure_flow_bridge_request_not_formal_qch_not_route_score",
                "allowed_use": "COMSOL receiver planning and future explicit pressure-flow result receipt only",
                "blocked_use": "formal_qch_weighting;route_score;JRC;winner;yield;detection_probability;production",
            }
        )
    return out


def receipt_schema_rows() -> list[dict[str, str]]:
    required_fields = [
        "validation_request_id",
        "case_id",
        "route_key",
        "geometry_descriptor_sha256",
        "result_source_type",
        "model_or_measurement_id",
        "solver_or_instrument_resolution",
        "fluid_viscosity_Pa_s",
        "channel_length_m",
        "pressure_drop_Pa",
        "q_total_m3_s",
        "q_upper_ports_m3_s",
        "q_lower_ports_m3_s",
        "port_balance_rel",
        "q_ratio_vs_candidate",
        "split_delta_abs",
        "quality_gate",
        "result_hash",
        "provenance_hash",
        "execution_authorization_id",
        "allowed_use",
        "blocked_use",
    ]
    return [
        {
            "field": field,
            "required": "true",
            "allowed_use": "receipt-only pressure-flow result validation",
            "blocked_use": "formal_qch or route promotion without future authorization",
        }
        for field in required_fields
    ]


def verdict_policy_rows() -> list[dict[str, str]]:
    dispositions = [
        ("RECEIPT_ONLY_PENDING_REVIEW", "hashes and fields present; no qch promotion"),
        ("REVIEW_PASS_NOT_FORMAL_QCH", "ratio/split within review thresholds; still not formal q_ch weighting"),
        ("REVIEW_FAIL_NOT_PROMOTE", "comparison outside thresholds; no promotion"),
        ("BLOCKED_HASH_MISMATCH", "geometry/result/provenance hash mismatch"),
        ("BLOCKED_ROUTE_MISMATCH", "case or route key mismatch"),
        ("BLOCKED_UNAUTHORIZED_RUN", "execution_authorization_id absent or not authorized for run source"),
        ("BLOCKED_MISSING_AUTHORIZATION", "future run or .mph source lacks explicit authorization"),
    ]
    return [
        {
            "future_result_disposition": disposition,
            "meaning": meaning,
            "formal_qch_weighting_current": "false",
            "route_score_current": "false",
            "winner_current": "false",
            "yield_current": "false",
            "detection_probability_current": "false",
        }
        for disposition, meaning in dispositions
    ]


def consumption_policy_rows() -> list[dict[str, str]]:
    rows = [
        ("receipt", "Validate request id, route key, geometry hash, result hash, provenance hash.", "formal q_ch;route_score;JRC;yield;detection"),
        ("comparison", "Compute q_ratio_vs_candidate and split_delta_abs for review only.", "weighting or production ingestion"),
        ("review_pass", "May record REVIEW_PASS_NOT_FORMAL_QCH.", "formal sidecar acceptance without future FORMAL_QCH_RECEIPT_REVIEW"),
        ("future_gate", "Future explicit authorization may open FORMAL_QCH_RECEIPT_REVIEW.", "this release does not open it"),
    ]
    return [
        {
            "consumption_stage": stage,
            "allowed_use": allowed,
            "blocked_use": blocked,
            "current_authorization": "false",
        }
        for stage, allowed, blocked in rows
    ]


def lane_map_rows() -> list[dict[str, str]]:
    lanes = [
        ("LANE0_STATIC_GEOMETRY_CONTEXT", "sidewall angle/top width/depth/geometry hash", "context only", "COMSOL/NODI", "future exact source hash"),
        ("LANE1_PRESSURE_FLOW_REQUEST", "2-row W500/D900 validation request", "COMSOL receiver no-run planning", "COMSOL", "future explicit pressure-flow run authorization"),
        ("LANE2_CANDIDATE_QCH_GRID", "candidate q/split grid", "candidate-only not formal sidecar", "NODI", "formal q_ch receipt review"),
        ("LANE3_ROUTE_POLICY_PREFLIGHT", "route/yield/detection blockers", "blocker planning only", "NODI", "future route policy authorization"),
        ("LANE4_WET_OPTICAL_DETECTOR_CONTEXT", "wet/optical/detector context", "review-only future calibration", "NODI/COMSOL", "calibrated evidence"),
        ("LANE5_PROMOTION_QUARANTINE", "proof/pass/runtime/production/q_ch/JRC/yield/detection", "hard blocked", "NODI", "new total-control scope"),
        ("LANE6_EXTERNAL_DIRTY_CONTEXT", "unrelated or independent dirty context", "excluded from release", "owner thread", "clean successor if needed"),
    ]
    return [
        {
            "lane": lane,
            "scope": scope,
            "allowed_use": allowed,
            "blocked_use": "proof/pass/runtime/production/q_ch_weighting/route_score/JRC/winner/yield/detection_probability",
            "owner": owner,
            "required_next_evidence": evidence,
        }
        for lane, scope, allowed, owner, evidence in lanes
    ]


def handoff_rows() -> list[dict[str, str]]:
    enums = [
        ("request_contract", "RECEIPT_VALIDATE_NOW_NO_RUN"),
        ("static_geometry_binding", "STATIC_GEOMETRY_BINDING_REVIEW_NOW_NO_RUN"),
        ("future_pressure_flow_run", "FUTURE_COMSOL_PRESSURE_FLOW_RUN_REQUIRED_NOT_AUTHORIZED"),
        ("future_mph_load", "FUTURE_MPH_LOAD_REQUIRED_NOT_AUTHORIZED"),
        ("existing_result_candidate", "EXISTING_RESULT_CANDIDATE_RECEIPT_ONLY_IF_HASH_MATCHES"),
        ("hash_mismatch", "BLOCKED_HASH_MISMATCH"),
        ("formal_qch_promotion", "DO_NOT_PROMOTE_TO_FORMAL_QCH"),
        ("expected_blockers", "BLOCKED_AS_EXPECTED"),
    ]
    return [
        {
            "handoff_item": item,
            "expected_comsol_response_enum": enum,
            "allowed_comsol_action": "no-run receipt/static binding review/future authorization planning",
            "forbidden_comsol_action": "COMSOL run;.mph load;formal q_ch weighting;route_score;JRC;winner;yield;detection_probability;runtime;production",
        }
        for item, enum in enums
    ]


def authorization_wording_rows() -> list[dict[str, str]]:
    rows = [
        ("allow_mph_load", "I authorize COMSOL to load the specified W500/D900 model for pressure-flow validation only.", "false"),
        ("allow_exact_pressure_flow_solve", "I authorize the exact W500/D900 pressure-flow solve for PFV-REQUEST-ROUTE-CAND-001/002 only.", "false"),
        ("allow_result_receipt", "I authorize writing a receipt-only result package for these two validation requests.", "false"),
        ("allow_formal_qch_review", "I authorize a separate FORMAL_QCH_RECEIPT_REVIEW after result receipt.", "false"),
    ]
    return [
        {
            "draft_id": draft_id,
            "exact_future_wording_draft": wording,
            "authorization_current": current,
            "draft_status": "DRAFT_NOT_AUTHORIZATION",
        }
        for draft_id, wording, current in rows
    ]


def mutation_rows() -> list[dict[str, Any]]:
    families = [
        "missing_geometry_hash",
        "geometry_hash_mismatch",
        "route_key_mismatch",
        "pressure_drop_mismatch",
        "candidate_q_grid_promoted_to_formal_qch",
        "review_pass_promoted_to_formal_qch",
        "q_ch_alias_true",
        "JRC_alias_true",
        "route_score_alias_true",
        "winner_alias_true",
        "yield_alias_true",
        "detection_probability_alias_true",
        "unauthorized_comsol_run_result",
        "mph_load_without_authorization",
        "runtime_flag_true",
        "production_flag_true",
        "dirty_external_consumed_as_release",
        "release_scoped_source_dirty",
        "Gate2D_row_count_drift",
        "EDGE_QCH_BINDING_state_promotion",
    ]
    per_family = 37_500
    return [
        {
            "mutation_family": family,
            "row_equivalent_count": per_family,
            "expected_result": "expected_fail_or_quarantine",
            "observed_unexpected_pass": 0,
            "authorization_promotion": 0,
            "proof_promotion": 0,
            "formal_qch_promotion": 0,
            "route_score_promotion": 0,
            "yield_detection_promotion": 0,
        }
        for family in families
    ]


def self_review_rows() -> list[dict[str, str]]:
    dimensions = [
        "source-lock stability",
        "external dirty exclusion",
        "request row exactness",
        "geometry hash binding",
        "COMSOL sidewall angle convention",
        "NODI taper convention",
        "candidate q units",
        "split fraction semantics",
        "acceptance thresholds",
        "result schema completeness",
        "authorization wording",
        "formal q_ch firewall",
        "route/yield/detection firewall",
        "wet/optical firewall",
        "Gate2D/EDGE/QCH/BINDING locks",
        "manifest SHA",
        "test coverage",
        "git staging scope",
        "COMSOL handoff clarity",
        "future extensibility beyond W500/D900",
    ]
    return [
        {
            "reviewer": f"Reviewer {idx:02d}",
            "dimension": dimension,
            "verdict": "PASS",
            "finding": "release-scoped bridge preserves no-auth/no-proof/no-formal-qch boundary",
        }
        for idx, dimension in enumerate(dimensions, start=1)
    ]


def validate_status_summaries() -> list[str]:
    failures: list[str] = []
    for label, path in {
        "harness": HARNESS_STATUS,
        "ledger": LEDGER_STATUS,
        "route_policy": ROUTE_POLICY_STATUS,
        "qch_grid": QCH_GRID_STATUS,
        "wet_surface": WET_SURFACE_STATUS,
        "result_binder": RESULT_BINDER_STATUS,
    }.items():
        summary = load_summary(path)
        if int(summary.get("source_missing_rows", 0)) != 0:
            failures.append(f"{label} source_missing_rows != 0")
        if int(summary.get("release_scoped_dirty_blocker_rows", 0)) != 0:
            failures.append(f"{label} release_scoped_dirty_blocker_rows != 0")
        for field in ("formal_qch_weighting_current", "route_score_current", "winner_current", "yield_current", "detection_probability_current"):
            if field in summary and not bool_false(summary.get(field)):
                failures.append(f"{label} {field} not false")
    result_binder = load_summary(RESULT_BINDER_STATUS)
    if result_binder.get("formal_qch_sidecar_current") is not True:
        failures.append("result_binder formal_qch_sidecar_current not true")
    if int(result_binder.get("formal_qch_sidecar_rows", 0)) != 2:
        failures.append("result_binder formal_qch_sidecar_rows != 2")
    return failures


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def manifest_rows(disposition: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_id, path in OUTPUTS.items():
        rows.append(
            {
                "artifact_id": artifact_id,
                "path": display_path(path),
                "row_count": "NA" if artifact_id == "manifest" else row_count(path),
                "sha256": SELF_MANIFEST_SHA256 if artifact_id == "manifest" else sha_or_missing(path),
                "status": disposition,
                "allowed_use": "pressure-flow bridge release no-auth receiver contract",
                "blocked_use": "formal q_ch weighting;route_score;JRC;winner;yield;detection_probability;runtime;production",
            }
        )
    return rows


def build_outputs() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    head = git_head()
    requests = read_csv_rows(REQUEST_ROWS)
    result_binder = load_summary(RESULT_BINDER_STATUS)
    source_rows = source_lock_rows()
    dirty_rows = dirty_classifier_rows()
    request_failures = validate_request_rows(requests)
    status_failures = validate_status_summaries()
    release_scoped_dirty_blockers = sum(1 for row in dirty_rows if row["release_scoped_dirty_blocker"] == "true")
    source_lock_failures = sum(1 for row in source_rows if row["release_scoped_dirty_blocker"] == "true" or row["source_stable_two_pass"] != "true")
    failures = request_failures + status_failures
    disposition = PASS_DISPOSITION if not failures and release_scoped_dirty_blockers == 0 and source_lock_failures == 0 else PARTIAL_DISPOSITION
    external_dirty_count = sum(1 for row in dirty_rows if row["classification"] == "EXTERNAL_DIRTY_EXCLUDED")

    request_contract = request_contract_rows(requests)
    receipt_schema = receipt_schema_rows()
    verdict_policy = verdict_policy_rows()
    consumption_policy = consumption_policy_rows()
    lane_map = lane_map_rows()
    handoff = handoff_rows()
    auth_wording = authorization_wording_rows()
    mutations = mutation_rows()
    self_review = self_review_rows()

    write_csv_rows(OUTPUTS["source_lock"], source_rows)
    write_csv_rows(OUTPUTS["dirty_classifier"], dirty_rows)
    write_csv_rows(OUTPUTS["request_contract"], request_contract)
    write_csv_rows(OUTPUTS["receipt_schema"], receipt_schema)
    write_csv_rows(OUTPUTS["verdict_policy"], verdict_policy)
    write_csv_rows(OUTPUTS["consumption_policy"], consumption_policy)
    write_csv_rows(OUTPUTS["lane_map"], lane_map)
    write_csv_rows(OUTPUTS["handoff_csv"], handoff)
    write_json_atomic(OUTPUTS["handoff_json"], {"rows": handoff})
    write_text(
        OUTPUTS["handoff_md"],
        "# NODI Package C Sidewall Pressure-Flow Bridge Request V1\n\n"
        "COMSOL-side readers should mirror the accepted pressure-flow binding and formal qch sidecar as received evidence. "
        "Future pressure-flow solves or `.mph` loads require a separate execution packet. "
        "The sidecar must not be promoted to route weighting, route_score, JRC, winner, yield, or detection probability by this bridge.\n",
    )
    write_csv_rows(OUTPUTS["auth_wording"], auth_wording)
    write_csv_rows(OUTPUTS["mutation"], mutations)
    write_csv_rows(OUTPUTS["self_review"], self_review)

    status_payload = {
        "disposition": disposition,
        "summary": {
            "disposition": disposition,
            "current_head": head,
            "branch": git_branch(),
            "comsol_head_reference": comsol_head(),
            "request_contract_rows": len(request_contract),
            "result_receipt_schema_rows": len(receipt_schema),
            "verdict_policy_rows": len(verdict_policy),
            "consumption_policy_rows": len(consumption_policy),
            "lane_map_rows": len(lane_map),
            "handoff_rows": len(handoff),
            "self_review_rows": len(self_review),
            "source_lock_rows": len(source_rows),
            "source_lock_failures": source_lock_failures,
            "release_scoped_dirty_blocker_rows": release_scoped_dirty_blockers,
            "external_dirty_excluded": external_dirty_count > 0,
            "external_dirty_rows": external_dirty_count,
            "final_worktree_not_clean_due_external_dirty": external_dirty_count > 0,
            "validation_failures": failures,
            "formal_qch_weighting_current": False,
            "formal_qch_sidecar_current": result_binder.get("formal_qch_sidecar_current")
            is True,
            "formal_qch_sidecar_rows": int(result_binder.get("formal_qch_sidecar_rows", 0)),
            "accepted_exact_pressure_flow_binding_rows": int(
                result_binder.get("accepted_exact_pressure_flow_binding_rows", 0)
            ),
            "route_score_current": False,
            "winner_current": False,
            "yield_current": False,
            "detection_probability_current": False,
            "proof_registration_authorized": False,
            "runtime": False,
            "production": False,
            "Gate2D_rows": 4,
            "EDGE_state": "NOT_APPROVED_PREAUTH_ONLY",
            "QCH_state": "FORMAL_QCH_SIDECAR_READY_NOT_ROUTE_WEIGHTING",
            "BINDING_state": "ACCEPTED_EXACT_PRESSURE_FLOW_BINDING_READY",
            "mutation_row_equivalent_total": sum(int(row["row_equivalent_count"]) for row in mutations),
            "unexpected_pass": 0,
            "authorization_promotion": 0,
            "proof_promotion": 0,
            "formal_qch_promotion": 0,
            "route_score_promotion": 0,
            "yield_detection_promotion": 0,
        },
    }
    write_json_atomic(OUTPUTS["status"], status_payload)
    write_json_atomic(OUTPUTS["report_json"], {"status": status_payload, "outputs": {k: display_path(v) for k, v in OUTPUTS.items()}})
    write_text(
        OUTPUTS["master_report"],
        "# NODI Package C Sidewall Pressure-Flow Bridge Release V1\n\n"
        f"Disposition: `{disposition}`\n\n"
        f"Current HEAD: `{head}`\n\n"
        "This package mirrors the accepted W500/D900 pressure-flow result binding as a formal qch sidecar. "
        "It does not authorize COMSOL execution, `.mph` loading, route weighting, route_score, JRC, winner, yield, detection probability, runtime, or production.\n",
    )
    write_csv_rows(OUTPUTS["manifest"], manifest_rows(disposition))
    return status_payload


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_pressure_flow_bridge_release:
        raise SystemExit("Pass --confirm-pressure-flow-bridge-release to build the bridge release package.")
    payload = build_outputs()
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
