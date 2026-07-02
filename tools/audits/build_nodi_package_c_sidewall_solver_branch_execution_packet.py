#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows, write_json_atomic  # noqa: E402
from nodi_simulator.sidewall_solver_branch_execution_packet import (  # noqa: E402
    SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_CLAIM_BOUNDARY,
    SOLVER_BRANCH_EXECUTION_PACKET_READY_STATUS,
    build_solver_branch_execution_packet,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_READY_BRANCHES_GUARDED"
)
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_CLAIM_BOUNDARY

POLICY_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_LEDGER_STATUS_20260701.json"
)
POLICY_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_LEDGER_POLICY_ROWS_20260701.csv"
)
FLOW_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_STATUS_20260701.json"
)
FLOW_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_SOLVER_ROWS_20260701.csv"
)
REFERENCE_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_STATUS_20260701.json"
)
REFERENCE_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_SURROGATE_ROWS_20260701.csv"
)
OPTICAL_CALIBRATION_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_STATUS_20260701.json"
)
OPTICAL_CALIBRATION_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_READINESS_ROWS_20260701.csv"
)
WET_OPTICAL_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_STATUS_20260701.json"
)
WET_OPTICAL_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_EVIDENCE_CONTEXT_ROWS_20260701.csv"
)
READINESS_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_STATUS_20260701.json"
)
READINESS_BOARD_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_BOARD_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "sidewall solver/wet/route branch execution packet;authorized branch preparation;"
    "candidate/context evidence inventory;next execution prioritization"
)
BLOCKED_USE = (
    "final solver claim;formal q_ch weighting;route_score;winner;JRC;yield;"
    "detection_probability;wet_pass_probability;clogging_rate;time_to_clog;recovery;"
    "COMSOL launch without branch packet;.mph load without branch packet;"
    "fabrication release;production ingestion"
)

SOURCE_FILES = {
    "authorization_policy_status": POLICY_STATUS,
    "authorization_policy_rows": POLICY_ROWS,
    "trapezoid_flow_status": FLOW_STATUS,
    "trapezoid_flow_rows": FLOW_ROWS,
    "reference_surrogate_status": REFERENCE_STATUS,
    "reference_surrogate_rows": REFERENCE_ROWS,
    "optical_calibration_status": OPTICAL_CALIBRATION_STATUS,
    "optical_calibration_rows": OPTICAL_CALIBRATION_ROWS,
    "wet_optical_status": WET_OPTICAL_STATUS,
    "wet_optical_rows": WET_OPTICAL_ROWS,
    "route_readiness_status": READINESS_STATUS,
    "route_readiness_rows": READINESS_BOARD_ROWS,
    "solver_branch_packet_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_solver_branch_execution_packet.py",
    "solver_branch_packet_tests": PROJECT_ROOT
    / "tests/test_sidewall_solver_branch_execution_packet.py",
    "solver_branch_packet_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_solver_branch_execution_packet.py",
    "solver_branch_packet_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_solver_branch_execution_packet.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_solver_branch_execution_packet.py",
    "tests/test_sidewall_solver_branch_execution_packet.py",
    "tools/audits/build_nodi_package_c_sidewall_solver_branch_execution_packet.py",
    "tests/test_nodi_package_c_sidewall_solver_branch_execution_packet.py",
}

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sidewall solver branch execution packet."
    )
    parser.add_argument(
        "--confirm-sidewall-solver-branch-execution-packet",
        action="store_true",
    )
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


def git_branch() -> str:
    return run_git(["branch", "--show-current"])


def git_status_lines() -> list[str]:
    out = run_git(["status", "--short"])
    return [line for line in out.splitlines() if line.strip()]


def git_path_from_status_line(line: str) -> str:
    return line[2:].strip().replace("\\", "/") if len(line) > 2 else line


def display_path(path: Path) -> str:
    if path.is_relative_to(PROJECT_ROOT):
        return path.relative_to(PROJECT_ROOT).as_posix()
    return str(path)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def release_scoped_path(path: str) -> bool:
    source_paths = {
        display_path(source_path)
        for source_path in SOURCE_FILES.values()
        if source_path.exists()
    }
    return (
        path in source_paths
        or path in BUILD_EDIT_PATHS
        or path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_"
        )
        or path == "reports/556_NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_20260701.md"
    )


def source_locked_path(path: str) -> bool:
    return path in {
        display_path(source_path)
        for source_path in SOURCE_FILES.values()
        if source_path.exists()
    }


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "solver_branch_packet_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_"
        ) or path == (
            "reports/556_NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_20260701.md"
        ):
            classification = "solver_branch_packet_output"
            release_decision = "included_or_rewritten_by_solver_branch_packet"
        elif source_locked_path(path):
            classification = "source_locked_upstream_dirty_context"
            release_decision = "source_locked_current_workspace_not_in_commit_scope"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_solver_branch_execution_packet"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_solver_branch_packet_not_source_locked"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_id, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_id": source_id,
                "path": display_path(path) if exists else str(path),
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else "",
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "branch_rows": payload["branch_rows"],
        "claim_guard_rows": payload["claim_guard_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    policy_status = load_json(POLICY_STATUS)
    flow_status = load_json(FLOW_STATUS)
    reference_status = load_json(REFERENCE_STATUS)
    optical_status = load_json(OPTICAL_CALIBRATION_STATUS)
    wet_status = load_json(WET_OPTICAL_STATUS)
    readiness_status = load_json(READINESS_STATUS)
    branch_rows, guard_rows = build_solver_branch_execution_packet(
        policy_rows=read_csv_rows(POLICY_ROWS),
        flow_status=flow_status,
        reference_status=reference_status,
        optical_calibration_status=optical_status,
        wet_optical_status=wet_status,
        readiness_board_status=readiness_status,
    )
    branch_dicts = [row.to_dict() for row in branch_rows]
    guard_dicts = [row.to_dict() for row in guard_rows]
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and policy_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_LEDGER_READY_CLAIMS_GUARDED"
        and flow_status.get("disposition")
        == "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_READY_NOT_QCH"
        and reference_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_READY_NOT_OPTICAL_SOLVER"
        and optical_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_READY_SEED_ONLY"
        and wet_status.get("disposition")
        == "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_READY_NOT_FINAL"
        and readiness_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_READY_INPUTS_NOT_CLAIMS"
        and len(branch_dicts) == 6
        and len(guard_dicts) == 8
        and all(row["authorized_to_prepare"] is True for row in branch_dicts)
        and all(row["final_solver_claim_current"] is False for row in branch_dicts)
        and all(row["q_ch_weighting_current"] is False for row in branch_dicts)
        and all(row["route_score_current"] is False for row in branch_dicts)
        and all(row["yield_current"] is False for row in branch_dicts)
        and all(row["detection_probability_current"] is False for row in branch_dicts)
        and all(row["claim_promotion_allowed_now"] is False for row in guard_dicts)
        and all(row["comsol_launch_allowed_now"] is False for row in branch_dicts)
        and all(row["mph_load_allowed_now"] is False for row in branch_dicts)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "packet_status": SOLVER_BRANCH_EXECUTION_PACKET_READY_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_policy_disposition": policy_status.get("disposition", ""),
        "source_flow_disposition": flow_status.get("disposition", ""),
        "source_reference_disposition": reference_status.get("disposition", ""),
        "source_optical_calibration_disposition": optical_status.get("disposition", ""),
        "source_wet_optical_disposition": wet_status.get("disposition", ""),
        "source_readiness_disposition": readiness_status.get("disposition", ""),
        "branch_rows": len(branch_dicts),
        "claim_guard_rows": len(guard_dicts),
        "authorized_prepare_rows": sum(row["authorized_to_prepare"] for row in branch_dicts),
        "authorized_execute_when_packet_passes_rows": sum(
            row["authorized_to_execute_when_packet_passes"] for row in branch_dicts
        ),
        "candidate_evidence_current_rows": sum(
            row["candidate_evidence_current"] for row in branch_dicts
        ),
        "candidate_output_rows_total": sum(row["candidate_output_rows"] for row in branch_dicts),
        "blocked_rows_total": sum(row["blocked_rows"] for row in branch_dicts),
        "final_solver_claim_current_rows": sum(
            row["final_solver_claim_current"] for row in branch_dicts
        ),
        "q_ch_weighting_current_rows": sum(
            row["q_ch_weighting_current"] for row in branch_dicts
        ),
        "route_score_current_rows": sum(row["route_score_current"] for row in branch_dicts),
        "winner_current_rows": sum(row["winner_current"] for row in branch_dicts),
        "yield_current_rows": sum(row["yield_current"] for row in branch_dicts),
        "detection_probability_current_rows": sum(
            row["detection_probability_current"] for row in branch_dicts
        ),
        "wet_pass_claim_current_rows": sum(
            row["wet_pass_claim_current"] for row in branch_dicts
        ),
        "comsol_launch_allowed_rows": sum(
            row["comsol_launch_allowed_now"] for row in branch_dicts
        ),
        "mph_load_allowed_rows": sum(row["mph_load_allowed_now"] for row in branch_dicts),
        "production_ingestion_current_rows": sum(
            row["production_ingestion_current"] for row in branch_dicts
        ),
        "claim_promotion_allowed_guard_rows": sum(
            row["claim_promotion_allowed_now"] for row in guard_dicts
        ),
        "flow_candidate_rows": sum(
            row["branch_id"] == "trapezoid_flow_solver"
            and row["candidate_evidence_current"]
            for row in branch_dicts
        ),
        "electrokinetic_preflight_rows": sum(
            row["branch_id"] == "electrokinetic_solver" for row in branch_dicts
        ),
        "optical_candidate_rows": sum(
            row["branch_id"] == "optical_reference_solver"
            and row["candidate_evidence_current"]
            for row in branch_dicts
        ),
        "wet_context_rows": sum(
            row["branch_id"] == "wet_optical_detection_evidence"
            and row["candidate_evidence_current"]
            for row in branch_dicts
        ),
        "route_decision_rows": sum(
            row["branch_id"] == "route_yield_detection_decision" for row in branch_dicts
        ),
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "source_locked_upstream_dirty_context_rows": sum(
            row["classification"] == "source_locked_upstream_dirty_context"
            for row in dirty_context
        ),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context" for row in dirty_context
        ),
        "release_scoped_dirty_blocker_rows": release_dirty_blockers,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "branch_rows": branch_dicts,
        "claim_guard_rows": guard_dicts,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    checks = {
        "disposition pass": s["disposition"] == DISPOSITION,
        "source lock complete": s["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": s["release_scoped_dirty_blocker_rows"] == 0,
        "six branch rows": s["branch_rows"] == 6,
        "eight claim guard rows": s["claim_guard_rows"] == 8,
        "all prepare authorized": s["authorized_prepare_rows"] == 6,
        "all execute authorized": s["authorized_execute_when_packet_passes_rows"] == 6,
        "candidate evidence exists": s["candidate_evidence_current_rows"] >= 4,
        "flow candidate present": s["flow_candidate_rows"] == 1,
        "electrokinetic preflight present": s["electrokinetic_preflight_rows"] == 1,
        "optical candidate present": s["optical_candidate_rows"] == 1,
        "wet context present": s["wet_context_rows"] == 1,
        "route decision present": s["route_decision_rows"] == 1,
        "no final solver claims": s["final_solver_claim_current_rows"] == 0,
        "no q_ch weighting": s["q_ch_weighting_current_rows"] == 0,
        "no route score": s["route_score_current_rows"] == 0,
        "no winner": s["winner_current_rows"] == 0,
        "no yield": s["yield_current_rows"] == 0,
        "no detection probability": s["detection_probability_current_rows"] == 0,
        "no wet pass": s["wet_pass_claim_current_rows"] == 0,
        "no comsol launch now": s["comsol_launch_allowed_rows"] == 0,
        "no mph load now": s["mph_load_allowed_rows"] == 0,
        "no production": s["production_ingestion_current_rows"] == 0,
        "no guard promotion": s["claim_promotion_allowed_guard_rows"] == 0,
    }
    for row in payload["branch_rows"]:
        checks[f"branch guarded {row['branch_row_id']}"] = (
            row["claim_boundary"] == CLAIM_BOUNDARY
            and row["final_solver_claim_current"] is False
            and row["route_score_current"] is False
            and row["yield_current"] is False
            and row["detection_probability_current"] is False
        )
    for row in payload["claim_guard_rows"]:
        checks[f"claim guard false {row['guard_row_id']}"] = (
            row["claim_promoted_current"] is False
            and row["claim_promotion_allowed_now"] is False
            and row["claim_boundary"] == CLAIM_BOUNDARY
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    csv_payloads = {
        f"{PREFIX}_BRANCH_ROWS_20260701.csv": payload["branch_rows"],
        f"{PREFIX}_CLAIM_GUARD_ROWS_20260701.csv": payload["claim_guard_rows"],
        f"{PREFIX}_SOURCE_LOCK_20260701.csv": payload["source_lock"],
        f"{PREFIX}_DIRTY_CONTEXT_20260701.csv": payload["dirty_context"],
    }
    for filename, rows in csv_payloads.items():
        path = OUTPUT_DIR / filename
        write_csv_rows(path, rows)
        paths.append(path)

    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(status_path, {"disposition": DISPOSITION, "summary": payload["summary"]})
    paths.append(status_path)

    report_path = OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_path, payload)
    paths.append(report_path)

    public_report = (
        REPORT_DIR
        / "556_NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_20260701.md"
    )
    public_report.write_text(report_markdown(payload), encoding="utf-8", newline="\n")
    paths.append(public_report)

    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv"
    write_csv_rows(manifest_path, manifest_rows(paths, manifest_path))
    paths.append(manifest_path)
    return paths


def report_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Sidewall Solver Branch Execution Packet",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Branch rows: `{s['branch_rows']}`.",
            f"- Claim guard rows: `{s['claim_guard_rows']}`.",
            f"- Candidate-evidence rows current: `{s['candidate_evidence_current_rows']}`.",
            f"- Candidate output rows total: `{s['candidate_output_rows_total']}`.",
            f"- Flow candidate rows: `{s['flow_candidate_rows']}`.",
            f"- Optical candidate rows: `{s['optical_candidate_rows']}`.",
            f"- Wet context rows: `{s['wet_context_rows']}`.",
            f"- Final solver claim rows current: `{s['final_solver_claim_current_rows']}`.",
            f"- q_ch weighting rows current: `{s['q_ch_weighting_current_rows']}`.",
            f"- route/yield/detection current rows: `{s['route_score_current_rows']}` / `{s['yield_current_rows']}` / `{s['detection_probability_current_rows']}`.",
            f"- COMSOL launch / .mph load rows now allowed: `{s['comsol_launch_allowed_rows']}` / `{s['mph_load_allowed_rows']}`.",
            "- The packet authorizes branch preparation and records existing candidate/context evidence; branch-specific packets must supply hashes before solver, q_ch, route, yield, detection, wet-pass, fabrication, or production claims can be true.",
            "",
        ]
    )


def manifest_rows(paths: list[Path], manifest_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "artifact": path.name,
                "path": display_path(path),
                "sha256": sha256_file(path),
                "disposition": DISPOSITION,
                "policy_impact": "solver_branch_execution_packet_not_claim",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    rows.append(
        {
            "artifact": manifest_path.name,
            "path": display_path(manifest_path),
            "sha256": SELF_MANIFEST_SHA256,
            "disposition": DISPOSITION,
            "policy_impact": "manifest_self_row_no_recursive_sha",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_sidewall_solver_branch_execution_packet:
        parser.error("--confirm-sidewall-solver-branch-execution-packet is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
