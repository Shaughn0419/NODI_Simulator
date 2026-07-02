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
from nodi_simulator.sidewall_authorization_execution_policy_ledger import (  # noqa: E402
    POLICY_LEDGER_READY_STATUS,
    SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_CLAIM_BOUNDARY,
    build_authorization_execution_policy_ledger,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_LEDGER"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_LEDGER_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_LEDGER_READY_CLAIMS_GUARDED"
)
BLOCKED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_LEDGER_FAIL_CLOSED"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_CLAIM_BOUNDARY

USER_AUTH_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_STATUS_20260701.json"
)
USER_AUTH_SCOPES = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_SCOPES_20260701.csv"
)
MAINLINE_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_STATUS_20260701.json"
)
MAINLINE_QUEUE = (
    OUTPUT_DIR / "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_EXECUTION_QUEUE_20260701.csv"
)
PROMOTION_CONTRACT = (
    OUTPUT_DIR / "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_PROMOTION_CONTRACT_20260701.csv"
)
RUNTIME_PACKET_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_STATUS_20260701.json"
)
READINESS_BOARD_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_STATUS_20260701.json"
)
READINESS_BOARD_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_BOARD_ROWS_20260701.csv"
)
READINESS_BLOCKER_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_BLOCKER_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "Package C authorization-to-execution policy ledger;branch execution prioritization;"
    "runtime/substep, solver, wet, route/yield/detection claim-guard mapping"
)
BLOCKED_USE = (
    "route_score;winner;JRC;yield;detection_probability;wet_pass_probability;"
    "clogging_rate;time_to_clog;recovery;q_ch_weighting;sidewall_prs_eas_numeric_output;"
    "COMSOL launch;.mph load;fabrication release;production ingestion"
)

SOURCE_FILES = {
    "user_authorization_status": USER_AUTH_STATUS,
    "user_authorization_scopes": USER_AUTH_SCOPES,
    "authorized_mainline_status": MAINLINE_STATUS,
    "authorized_mainline_queue": MAINLINE_QUEUE,
    "authorized_mainline_promotion_contract": PROMOTION_CONTRACT,
    "runtime_substep_execution_packet_status": RUNTIME_PACKET_STATUS,
    "readiness_board_status": READINESS_BOARD_STATUS,
    "readiness_board_rows": READINESS_BOARD_ROWS,
    "readiness_blocker_rows": READINESS_BLOCKER_ROWS,
    "authorization_execution_policy_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_authorization_execution_policy_ledger.py",
    "authorization_execution_policy_tests": PROJECT_ROOT
    / "tests/test_sidewall_authorization_execution_policy_ledger.py",
    "authorization_execution_policy_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_authorization_execution_policy_ledger.py",
    "authorization_execution_policy_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_authorization_execution_policy_ledger.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_authorization_execution_policy_ledger.py",
    "tests/test_sidewall_authorization_execution_policy_ledger.py",
    "tools/audits/build_nodi_package_c_sidewall_authorization_execution_policy_ledger.py",
    "tests/test_nodi_package_c_sidewall_authorization_execution_policy_ledger.py",
    "reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
}

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sidewall authorization execution policy ledger."
    )
    parser.add_argument(
        "--confirm-sidewall-authorization-execution-policy-ledger",
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
            "NODI_PACKAGE_C_SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_LEDGER_"
        )
        or path
        == "reports/555_NODI_PACKAGE_C_SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_LEDGER_20260701.md"
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
            classification = "authorization_execution_policy_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_LEDGER_"
        ) or path == (
            "reports/555_NODI_PACKAGE_C_SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_LEDGER_20260701.md"
        ):
            classification = "authorization_execution_policy_output"
            release_decision = "included_or_rewritten_by_authorization_execution_policy"
        elif source_locked_path(path):
            classification = "source_locked_upstream_dirty_context"
            release_decision = "source_locked_current_workspace_not_in_commit_scope"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_authorization_execution_policy"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_authorization_execution_policy_not_source_locked"
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
        "policy_rows": payload["policy_rows"],
        "claim_guard_rows": payload["claim_guard_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    user_status = load_json(USER_AUTH_STATUS)
    mainline_status = load_json(MAINLINE_STATUS)
    runtime_status = load_json(RUNTIME_PACKET_STATUS)
    readiness_status = load_json(READINESS_BOARD_STATUS)
    policy_rows, guard_rows = build_authorization_execution_policy_ledger(
        authorization_scope_rows=read_csv_rows(USER_AUTH_SCOPES),
        execution_queue_rows=read_csv_rows(MAINLINE_QUEUE),
        promotion_contract_rows=read_csv_rows(PROMOTION_CONTRACT),
        readiness_board_rows=read_csv_rows(READINESS_BOARD_ROWS),
        readiness_blocker_rows=read_csv_rows(READINESS_BLOCKER_ROWS),
        runtime_packet_status=runtime_status,
    )
    policy_dicts = [row.to_dict() for row in policy_rows]
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
        and user_status.get("disposition")
        == "NODI_PACKAGE_C_USER_AUTHORIZATION_LEDGER_ACCEPTED_NO_RESULT_PROMOTION"
        and mainline_status.get("disposition")
        == "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_READY_FOR_EXECUTION_PACKETS"
        and runtime_status.get("disposition")
        == "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_READY_WITH_GUARDED_SMOKE"
        and readiness_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_READY_INPUTS_NOT_CLAIMS"
        and len(policy_dicts) == 8
        and len(guard_dicts) == 8
        and all(row["authorized_to_prepare"] is True for row in policy_dicts)
        and all(row["claim_promotion_allowed_now"] is False for row in policy_dicts)
        and all(row["claim_promotion_allowed_now"] is False for row in guard_dicts)
        and all(row["comsol_launch_allowed_now"] is False for row in policy_dicts)
        and all(row["mph_load_allowed_now"] is False for row in policy_dicts)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "ledger_status": POLICY_LEDGER_READY_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_user_authorization_disposition": user_status.get("disposition", ""),
        "source_mainline_disposition": mainline_status.get("disposition", ""),
        "source_runtime_packet_disposition": runtime_status.get("disposition", ""),
        "source_readiness_board_disposition": readiness_status.get("disposition", ""),
        "policy_rows": len(policy_dicts),
        "claim_guard_rows": len(guard_dicts),
        "authorized_prepare_rows": sum(row["authorized_to_prepare"] for row in policy_dicts),
        "authorized_execute_when_packet_passes_rows": sum(
            row["authorized_to_execute_when_packet_passes"] for row in policy_dicts
        ),
        "runtime_smoke_packet_passed_rows": sum(
            row["execution_packet_status"]
            == "runtime_substep_execution_packet_passed_candidate_only"
            for row in policy_dicts
        ),
        "nodi_runtime_recomputation_allowed_rows": sum(
            row["nodi_runtime_recomputation_allowed_now"] for row in policy_dicts
        ),
        "comsol_launch_allowed_rows": sum(
            row["comsol_launch_allowed_now"] for row in policy_dicts
        ),
        "mph_load_allowed_rows": sum(row["mph_load_allowed_now"] for row in policy_dicts),
        "sidewall_prs_eas_numeric_allowed_rows": sum(
            row["sidewall_prs_eas_numeric_allowed_now"] for row in policy_dicts
        ),
        "claim_promotion_allowed_policy_rows": sum(
            row["claim_promotion_allowed_now"] for row in policy_dicts
        ),
        "claim_promotion_allowed_guard_rows": sum(
            row["claim_promotion_allowed_now"] for row in guard_dicts
        ),
        "wet_branch_rows": sum(
            row["branch_id"] == "wet_ev_evidence" for row in policy_dicts
        ),
        "route_decision_rows": sum(
            row["branch_id"] == "route_yield_detection_decision" for row in policy_dicts
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
        "policy_rows": policy_dicts,
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
        "eight policy rows": s["policy_rows"] == 8,
        "eight guard rows": s["claim_guard_rows"] == 8,
        "all prepare authorized": s["authorized_prepare_rows"] == 8,
        "all execute authorized": s["authorized_execute_when_packet_passes_rows"] == 8,
        "runtime smoke row present": s["runtime_smoke_packet_passed_rows"] == 1,
        "one guarded nodi runtime row": s["nodi_runtime_recomputation_allowed_rows"] == 1,
        "no comsol launch now": s["comsol_launch_allowed_rows"] == 0,
        "no mph load now": s["mph_load_allowed_rows"] == 0,
        "no prs/eas numeric now": s["sidewall_prs_eas_numeric_allowed_rows"] == 0,
        "no policy claim promotion": s["claim_promotion_allowed_policy_rows"] == 0,
        "no guard claim promotion": s["claim_promotion_allowed_guard_rows"] == 0,
        "wet branch present": s["wet_branch_rows"] == 1,
        "route decision branch present": s["route_decision_rows"] == 1,
    }
    for row in payload["policy_rows"]:
        checks[f"policy row guarded {row['policy_row_id']}"] = (
            row["claim_promotion_allowed_now"] is False
            and row["claim_promoted_by_this_task"] is False
            and row["claim_boundary"] == CLAIM_BOUNDARY
        )
    for row in payload["claim_guard_rows"]:
        checks[f"claim guard false {row['guard_row_id']}"] = (
            row["claim_promotion_allowed_now"] is False
            and row["claim_promoted_current"] is False
            and row["claim_boundary"] == CLAIM_BOUNDARY
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    csv_payloads = {
        f"{PREFIX}_POLICY_ROWS_20260701.csv": payload["policy_rows"],
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
        / "555_NODI_PACKAGE_C_SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_LEDGER_20260701.md"
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
            "# NODI Package C Sidewall Authorization Execution Policy Ledger",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Policy rows: `{s['policy_rows']}`.",
            f"- Claim guard rows: `{s['claim_guard_rows']}`.",
            f"- Authorized prepare rows: `{s['authorized_prepare_rows']}`.",
            f"- Guarded NODI runtime rows now allowed: `{s['nodi_runtime_recomputation_allowed_rows']}`.",
            f"- COMSOL launch rows now allowed: `{s['comsol_launch_allowed_rows']}`.",
            f"- Claim-promotion rows now allowed: `{s['claim_promotion_allowed_policy_rows']}`.",
            "- User authorization is bound to execution paths, not final claims.",
            "- Runtime smoke remains candidate-only; COMSOL launch, `.mph` load, sidewall PRS/EAS numeric output, route score, winner/JRC, yield, detection probability, wet pass, fabrication release, and production ingestion remain guarded.",
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
                "policy_impact": "authorization_execution_policy_ledger_not_claim",
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
    if not args.confirm_sidewall_authorization_execution_policy_ledger:
        parser.error("--confirm-sidewall-authorization-execution-policy-ledger is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_LEDGER")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
