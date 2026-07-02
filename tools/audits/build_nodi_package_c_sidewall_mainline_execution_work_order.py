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
from nodi_simulator.sidewall_mainline_execution_work_order import (  # noqa: E402
    SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_CLAIM_BOUNDARY,
    SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_STATUS,
    build_mainline_execution_work_order,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_READY_LARGE_BLOCKS_PRIORITIZED"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_CLAIM_BOUNDARY

SOLVER_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_STATUS_20260701.json"
EK_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_STATUS_20260701.json"
COMSOL_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_COMSOL_LAUNCH_PRECONDITION_STATUS_20260701.json"
DETECTOR_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_STATUS_20260701.json"
WET_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_STATUS_20260701.json"
ROUTE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_STATUS_20260701.json"
ROUTE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_READINESS_ROWS_20260701.csv"

ALLOWED_USE = (
    "sidewall Package C large-block execution work order;"
    "authorized implementation sequencing;evidence-gated claim activation"
)
BLOCKED_USE = (
    "claim activation without accepted evidence;COMSOL launch without target binding;"
    "route_score;winner;JRC;yield;detection_probability;production ingestion"
)

SOURCE_FILES = {
    "solver_branch_status": SOLVER_STATUS,
    "electrokinetic_preflight_status": EK_STATUS,
    "comsol_precondition_status": COMSOL_STATUS,
    "detector_blank_status": DETECTOR_STATUS,
    "wet_observation_status": WET_STATUS,
    "route_decision_status": ROUTE_STATUS,
    "route_decision_rows": ROUTE_ROWS,
    "mainline_work_order_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_mainline_execution_work_order.py",
    "mainline_work_order_tests": PROJECT_ROOT
    / "tests/test_sidewall_mainline_execution_work_order.py",
    "mainline_work_order_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_mainline_execution_work_order.py",
    "mainline_work_order_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_mainline_execution_work_order.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_mainline_execution_work_order.py",
    "tests/test_sidewall_mainline_execution_work_order.py",
    "tools/audits/build_nodi_package_c_sidewall_mainline_execution_work_order.py",
    "tests/test_nodi_package_c_sidewall_mainline_execution_work_order.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the sidewall Package C mainline execution work order."
    )
    parser.add_argument(
        "--confirm-sidewall-mainline-execution-work-order",
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
        "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_"
    )
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "mainline_work_order_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == (
            "reports/562_NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_20260701.md"
        ):
            classification = "mainline_work_order_output"
            release_decision = "included_or_rewritten_by_mainline_work_order"
        elif path in source_paths:
            classification = "source_locked_upstream_dirty_context"
            release_decision = "source_locked_current_workspace_not_in_commit_scope"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_mainline_work_order"
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
                "work_order_rows": payload["work_order_rows"],
                "claim_guard_rows": payload["claim_guard_rows"],
                "route_evidence_register_rows": payload["route_evidence_register_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    rows, guards, register = build_mainline_execution_work_order(
        solver_status=load_status(SOLVER_STATUS),
        electrokinetic_status=load_status(EK_STATUS),
        comsol_status=load_status(COMSOL_STATUS),
        detector_status=load_status(DETECTOR_STATUS),
        wet_status=load_status(WET_STATUS),
        route_status=load_status(ROUTE_STATUS),
        route_rows=read_csv_rows(ROUTE_ROWS),
    )
    work_order_rows = [row.to_dict() for row in rows]
    guard_rows = [row.to_dict() for row in guards]
    register_rows = [row.to_dict() for row in register]
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    route_geometry_scope = ";".join(
        sorted({str(row["route_geometry_scope"]) for row in work_order_rows})
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and len(work_order_rows) == 8
        and len(guard_rows) == 7
        and len(register_rows) == 10
        and route_geometry_scope == "ideal_rectangle;trapezoid_tapered_sidewalls"
        and all(row["implementation_authorized"] is True for row in work_order_rows)
        and all(row["codex_can_execute_next"] is True for row in work_order_rows)
        and sum(row["claim_activation_allowed_now"] for row in work_order_rows) == 0
        and sum(row["activation_allowed_now"] for row in guard_rows) == 0
        and sum(row["may_satisfy_route_formula_now"] for row in register_rows) == 0
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "work_order_status": SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "work_order_rows": len(work_order_rows),
        "claim_guard_rows": len(guard_rows),
        "route_evidence_register_rows": len(register_rows),
        "route_geometry_scope": route_geometry_scope,
        "implementation_authorized_rows": sum(row["implementation_authorized"] for row in work_order_rows),
        "codex_can_execute_next_rows": sum(row["codex_can_execute_next"] for row in work_order_rows),
        "external_or_lab_input_required_rows": sum(row["external_or_lab_input_required"] for row in work_order_rows),
        "claim_activation_allowed_work_order_rows": sum(row["claim_activation_allowed_now"] for row in work_order_rows),
        "claim_activation_allowed_guard_rows": sum(row["activation_allowed_now"] for row in guard_rows),
        "route_evidence_may_satisfy_formula_rows": sum(row["may_satisfy_route_formula_now"] for row in register_rows),
        "route_evidence_ready_input_rows": sum(row["evidence_class"] == "ready_route_input" for row in register_rows),
        "route_evidence_fixture_or_context_rows": sum(
            row["evidence_class"].startswith("fixture_or") for row in register_rows
        ),
        "route_evidence_current_accepted_claim_rows": sum(
            row["evidence_class"] == "current_accepted_claim_evidence" for row in register_rows
        ),
        "accepted_detector_transfer_rows": _status_int(DETECTOR_STATUS, "current_accepted_transfer_rows_total"),
        "accepted_wet_observation_rows": _status_int(WET_STATUS, "current_accepted_observation_rows_total"),
        "profile_aware_grid_rows": _status_int(EK_STATUS, "profile_aware_grid_current_rows"),
        "comsol_target_bound_rows": _status_int(COMSOL_STATUS, "target_model_bound_rows"),
        "comsol_command_hash_bound_rows": _status_int(COMSOL_STATUS, "launch_command_hash_bound_rows"),
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
        "work_order_rows": work_order_rows,
        "claim_guard_rows": guard_rows,
        "route_evidence_register_rows": register_rows,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def _status_int(path: Path, key: str) -> int:
    value = load_status(path).get(key, 0)
    if value is None or str(value).strip() == "":
        return 0
    return int(float(str(value)))


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    checks = {
        "disposition pass": s["disposition"] == DISPOSITION,
        "source lock complete": s["source_missing_rows"] == 0,
        "eight work orders": s["work_order_rows"] == 8,
        "seven guards": s["claim_guard_rows"] == 7,
        "ten route evidence rows": s["route_evidence_register_rows"] == 10,
        "rectangle and trapezoid scope": s["route_geometry_scope"]
        == "ideal_rectangle;trapezoid_tapered_sidewalls",
        "all authorized": s["implementation_authorized_rows"] == 8,
        "all executable next": s["codex_can_execute_next_rows"] == 8,
        "no activation now": s["claim_activation_allowed_work_order_rows"] == 0,
        "no guard activation now": s["claim_activation_allowed_guard_rows"] == 0,
        "no route evidence formula now": s["route_evidence_may_satisfy_formula_rows"] == 0,
        "ready qch input rows": s["route_evidence_ready_input_rows"] == 2,
        "no accepted claim evidence rows": s["route_evidence_current_accepted_claim_rows"] == 0,
        "detector still absent": s["accepted_detector_transfer_rows"] == 0,
        "wet still absent": s["accepted_wet_observation_rows"] == 0,
    }
    for row in payload["work_order_rows"]:
        checks[f"row guarded {row['work_order_id']}"] = (
            row["implementation_authorized"] is True
            and row["claim_boundary"] == CLAIM_BOUNDARY
            and row["route_geometry_scope"] == "ideal_rectangle;trapezoid_tapered_sidewalls"
        )
    for row in payload["route_evidence_register_rows"]:
        checks[f"register guarded {row['register_row_id']}"] = (
            row["claim_boundary"] == CLAIM_BOUNDARY
            and row["route_geometry_family"]
            in {"ideal_rectangle", "trapezoid_tapered_sidewalls"}
            and row["evidence_class"]
            in {
                "ready_route_input",
                "fixture_or_context_available_no_accepted_claim_evidence",
                "fixture_or_contract_available_no_accepted_claim_evidence",
                "preflight_requirement",
                "precondition_only",
                "candidate",
                "current_accepted_claim_evidence",
            }
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_WORK_ORDER_ROWS_20260701.csv": payload["work_order_rows"],
        f"{PREFIX}_CLAIM_GUARD_ROWS_20260701.csv": payload["claim_guard_rows"],
        f"{PREFIX}_ROUTE_EVIDENCE_REGISTER_ROWS_20260701.csv": payload["route_evidence_register_rows"],
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
    public_report = REPORT_DIR / "562_NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_20260701.md"
    public_report.write_text(report_markdown(payload), encoding="utf-8", newline="\n")
    paths.append(public_report)
    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv"
    write_csv_rows(manifest_path, manifest_rows(paths, manifest_path))
    paths.append(manifest_path)
    return paths


def report_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    top_rows = sorted(payload["work_order_rows"], key=lambda row: row["priority"])[:8]
    lines = [
        "# NODI Package C Sidewall Mainline Execution Work Order",
        "",
        f"- Disposition: `{s['disposition']}`.",
        f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
        f"- Geometry scope: `{s['route_geometry_scope']}`.",
        f"- Work orders: `{s['work_order_rows']}`; claim guards: `{s['claim_guard_rows']}`.",
        f"- Route evidence register rows: `{s['route_evidence_register_rows']}`.",
        f"- Authorized implementation rows: `{s['implementation_authorized_rows']}`.",
        f"- Current claim activation rows: `{s['claim_activation_allowed_work_order_rows']}`.",
        f"- Accepted detector/wet evidence: `{s['accepted_detector_transfer_rows']}` / `{s['accepted_wet_observation_rows']}`.",
        "",
        "## Ordered Work",
        "",
    ]
    for row in top_rows:
        lines.append(
            f"- `{row['work_order_id']}` `{row['lane']}` -> `{row['intended_next_artifact']}`; "
            f"blocker: {row['current_blocker']}."
        )
    lines.extend(
        [
            "",
            "This packet treats solver, wet, route, yield, and detection work as authorized "
            "implementation lanes. Claim activation remains evidence-gated: missing detector/blank "
            "and wet rows are execution inputs to collect, not reasons to stop the mainline.",
            "",
        ]
    )
    return "\n".join(lines)


def manifest_rows(paths: list[Path], manifest_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "artifact": path.name,
                "path": display_path(path),
                "sha256": sha256_file(path),
                "disposition": DISPOSITION,
                "policy_impact": "mainline_execution_work_order",
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
    if not args.confirm_sidewall_mainline_execution_work_order:
        parser.error("--confirm-sidewall-mainline-execution-work-order is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
