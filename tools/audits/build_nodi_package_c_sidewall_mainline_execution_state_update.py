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
from nodi_simulator.sidewall_mainline_execution_state_update import (  # noqa: E402
    SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_CLAIM_BOUNDARY,
    SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_STATUS,
    build_mainline_execution_state_update,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_READY_RUNTIME_PROFILE_GRID_INTEGRATED"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_CLAIM_BOUNDARY

WORK_ORDER_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_STATUS_20260701.json"
WORK_ORDER_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_WORK_ORDER_ROWS_20260701.csv"
WORK_ORDER_REGISTER = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_ROUTE_EVIDENCE_REGISTER_ROWS_20260701.csv"
RUNTIME_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_STATUS_20260701.json"
PROFILE_GRID_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_STATUS_20260701.json"
FLOW_SOLVER_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_STATUS_20260701.json"
COMSOL_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_COMSOL_LAUNCH_PRECONDITION_STATUS_20260701.json"
DETECTOR_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_STATUS_20260701.json"
WET_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_STATUS_20260701.json"
ROUTE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_STATUS_20260701.json"

ALLOWED_USE = (
    "current sidewall mainline state update;runtime substep smoke integration;"
    "profile-grid candidate integration;next evidence prioritization"
)
BLOCKED_USE = (
    "route_score;winner;JRC;yield;detection_probability;COMSOL launch without target binding;"
    "wet claim without accepted wet rows;production ingestion"
)

SOURCE_FILES = {
    "mainline_work_order_status": WORK_ORDER_STATUS,
    "mainline_work_order_rows": WORK_ORDER_ROWS,
    "mainline_route_evidence_register": WORK_ORDER_REGISTER,
    "runtime_substep_execution_status": RUNTIME_STATUS,
    "electrokinetic_profile_grid_status": PROFILE_GRID_STATUS,
    "trapezoid_flow_solver_status": FLOW_SOLVER_STATUS,
    "comsol_precondition_status": COMSOL_STATUS,
    "detector_blank_status": DETECTOR_STATUS,
    "wet_observation_status": WET_STATUS,
    "route_decision_status": ROUTE_STATUS,
    "mainline_state_update_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_mainline_execution_state_update.py",
    "mainline_state_update_tests": PROJECT_ROOT
    / "tests/test_sidewall_mainline_execution_state_update.py",
    "mainline_state_update_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_mainline_execution_state_update.py",
    "mainline_state_update_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_mainline_execution_state_update.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_mainline_execution_state_update.py",
    "tests/test_sidewall_mainline_execution_state_update.py",
    "tools/audits/build_nodi_package_c_sidewall_mainline_execution_state_update.py",
    "tests/test_nodi_package_c_sidewall_mainline_execution_state_update.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sidewall mainline execution current-state update."
    )
    parser.add_argument(
        "--confirm-sidewall-mainline-execution-state-update",
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


def load_status(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    source_paths = {
        display_path(source_path)
        for source_path in SOURCE_FILES.values()
        if source_path.exists()
    }
    output_prefix = (
        "reports/joint_interface_20260701/"
        "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_"
    )
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "mainline_state_update_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == (
            "reports/564_NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_20260701.md"
        ):
            classification = "mainline_state_update_output"
            release_decision = "included_or_rewritten_by_mainline_state_update"
        elif path in source_paths:
            classification = "source_locked_upstream_dirty_context"
            release_decision = "source_locked_current_workspace_not_in_commit_scope"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_mainline_state_update"
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
    return hashlib.sha256(
        json.dumps(
            {
                "work_order_state_rows": payload["work_order_state_rows"],
                "route_evidence_state_rows": payload["route_evidence_state_rows"],
                "state_guard_rows": payload["state_guard_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    work_rows, route_rows, guards = build_mainline_execution_state_update(
        work_order_rows=read_csv_rows(WORK_ORDER_ROWS),
        route_evidence_register_rows=read_csv_rows(WORK_ORDER_REGISTER),
        runtime_status=load_status(RUNTIME_STATUS),
        profile_grid_status=load_status(PROFILE_GRID_STATUS),
        flow_solver_status=load_status(FLOW_SOLVER_STATUS),
        comsol_status=load_status(COMSOL_STATUS),
        detector_status=load_status(DETECTOR_STATUS),
        wet_status=load_status(WET_STATUS),
        route_status=load_status(ROUTE_STATUS),
    )
    work_dicts = [row.to_dict() for row in work_rows]
    route_dicts = [row.to_dict() for row in route_rows]
    guard_dicts = [row.to_dict() for row in guards]
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    completed_lanes = {
        "candidate_profile_grid_available_not_solver",
        "guarded_runtime_smoke_available_stress_blocked",
    }
    status = (
        DISPOSITION
        if source_missing == 0
        and len(work_dicts) == 8
        and len(route_dicts) == 14
        and len(guard_dicts) == 5
        and sum(row["current_state"] in completed_lanes for row in work_dicts) == 2
        and sum(row["activation_allowed_now"] for row in guard_dicts) == 0
        and sum(row["may_satisfy_route_formula_now"] for row in route_dicts) == 0
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "state_update_status": SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "work_order_state_rows": len(work_dicts),
        "route_evidence_state_rows": len(route_dicts),
        "state_guard_rows": len(guard_dicts),
        "profile_grid_integrated_rows": sum(
            row["current_state"] == "candidate_profile_grid_available_not_solver"
            for row in work_dicts
        ),
        "runtime_substep_integrated_rows": sum(
            row["current_state"] == "guarded_runtime_smoke_available_stress_blocked"
            for row in work_dicts
        ),
        "candidate_profile_grid_route_rows": sum(
            row["evidence_lane"] == "electrokinetic_profile_grid"
            and row["evidence_class"] == "candidate"
            for row in route_dicts
        ),
        "guarded_runtime_smoke_route_rows": sum(
            row["evidence_lane"] == "runtime_substep_guard"
            for row in route_dicts
        ),
        "flow_solver_candidate_route_rows": sum(
            row["evidence_lane"] == "flow_solver_candidate"
            and row["evidence_class"] == "candidate"
            for row in route_dicts
        ),
        "comsol_launch_activation_rows": sum(
            row["claim_target"] == "comsol_launch" and row["activation_allowed_now"]
            for row in guard_dicts
        ),
        "route_score_activation_rows": sum(
            row["claim_target"] == "route_score_winner_JRC"
            and row["activation_allowed_now"]
            for row in guard_dicts
        ),
        "yield_activation_rows": sum(
            row["claim_target"] == "yield" and row["activation_allowed_now"]
            for row in guard_dicts
        ),
        "detection_activation_rows": sum(
            row["claim_target"] == "detection_probability"
            and row["activation_allowed_now"]
            for row in guard_dicts
        ),
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "source_locked_upstream_dirty_context_rows": sum(
            row["classification"] == "source_locked_upstream_dirty_context"
            for row in dirty_context
        ),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context"
            for row in dirty_context
        ),
        "release_scoped_dirty_blocker_rows": 0,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "work_order_state_rows": work_dicts,
        "route_evidence_state_rows": route_dicts,
        "state_guard_rows": guard_dicts,
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
        "eight work order states": s["work_order_state_rows"] == 8,
        "fourteen route evidence states": s["route_evidence_state_rows"] == 14,
        "five guards": s["state_guard_rows"] == 5,
        "profile grid integrated": s["profile_grid_integrated_rows"] == 1,
        "runtime integrated": s["runtime_substep_integrated_rows"] == 1,
        "profile route rows updated": s["candidate_profile_grid_route_rows"] == 2,
        "runtime route rows added": s["guarded_runtime_smoke_route_rows"] == 2,
        "trapezoid flow candidate added": s["flow_solver_candidate_route_rows"] == 1,
        "no comsol activation": s["comsol_launch_activation_rows"] == 0,
        "no route activation": s["route_score_activation_rows"] == 0,
        "no yield activation": s["yield_activation_rows"] == 0,
        "no detection activation": s["detection_activation_rows"] == 0,
    }
    for row in payload["route_evidence_state_rows"]:
        checks[f"route evidence guarded {row['evidence_state_row_id']}"] = (
            row["claim_boundary"] == CLAIM_BOUNDARY
            and row["may_satisfy_route_formula_now"] is False
            and row["may_satisfy_yield_now"] is False
            and row["may_satisfy_detection_now"] is False
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_WORK_ORDER_STATE_ROWS_20260701.csv": payload["work_order_state_rows"],
        f"{PREFIX}_ROUTE_EVIDENCE_STATE_ROWS_20260701.csv": payload["route_evidence_state_rows"],
        f"{PREFIX}_STATE_GUARD_ROWS_20260701.csv": payload["state_guard_rows"],
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
    public_report = REPORT_DIR / "564_NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_20260701.md"
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
            "# NODI Package C Sidewall Mainline Execution State Update",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Work-order state rows: `{s['work_order_state_rows']}`.",
            f"- Route-evidence state rows: `{s['route_evidence_state_rows']}`.",
            f"- Integrated profile-grid rows: `{s['profile_grid_integrated_rows']}`.",
            f"- Integrated runtime/substep rows: `{s['runtime_substep_integrated_rows']}`.",
            f"- Route activation rows: `{s['route_score_activation_rows']}`; yield/detection activation rows: `{s['yield_activation_rows']}` / `{s['detection_activation_rows']}`.",
            "",
            "The current mainline now has both profile-aware electrokinetic grid candidate evidence and guarded runtime/substep smoke evidence integrated into the route evidence register. The remaining route/yield/detection blockers are accepted detector/blank transfer rows, accepted wet observation rows, and COMSOL target binding.",
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
                "policy_impact": "mainline_execution_state_update",
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
    if not args.confirm_sidewall_mainline_execution_state_update:
        parser.error("--confirm-sidewall-mainline-execution-state-update is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
