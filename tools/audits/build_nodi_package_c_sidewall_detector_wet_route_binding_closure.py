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
from nodi_simulator.sidewall_detector_wet_route_binding_closure import (  # noqa: E402
    SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_CLAIM_BOUNDARY,
    SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_STATUS,
    build_detector_wet_route_binding_closure,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_READY_ACCEPTED_ROWS_REQUIRED"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_CLAIM_BOUNDARY

STATE_UPDATE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_STATUS_20260701.json"
STATE_UPDATE_ROUTE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_ROUTE_EVIDENCE_STATE_ROWS_20260701.csv"
ROUTE_CANDIDATE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_STATUS_20260701.json"
SELECTED_ANNULUS_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_STATUS_20260701.json"
DETECTOR_EXECUTION_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_STATUS_20260701.json"
DETECTOR_VALIDATION_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_STATUS_20260701.json"
WET_EXECUTION_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_STATUS_20260701.json"
WET_VALIDATION_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_STATUS_20260701.json"

ALLOWED_USE = (
    "detector/wet route-binding closure harness;accepted-evidence gap consolidation;"
    "route/yield/detection formula-binding precondition table"
)
BLOCKED_USE = (
    "route_score;winner;JRC;yield;detection_probability;wet_pass_probability;"
    "clogging_rate;time_to_clog;recovery;production ingestion"
)

SOURCE_FILES = {
    "mainline_state_update_status": STATE_UPDATE_STATUS,
    "mainline_route_evidence_state_rows": STATE_UPDATE_ROUTE_ROWS,
    "route_candidate_status": ROUTE_CANDIDATE_STATUS,
    "selected_annulus_status": SELECTED_ANNULUS_STATUS,
    "detector_execution_status": DETECTOR_EXECUTION_STATUS,
    "detector_validation_status": DETECTOR_VALIDATION_STATUS,
    "wet_execution_status": WET_EXECUTION_STATUS,
    "wet_validation_status": WET_VALIDATION_STATUS,
    "closure_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_detector_wet_route_binding_closure.py",
    "closure_tests": PROJECT_ROOT
    / "tests/test_sidewall_detector_wet_route_binding_closure.py",
    "closure_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_detector_wet_route_binding_closure.py",
    "closure_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_detector_wet_route_binding_closure.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_detector_wet_route_binding_closure.py",
    "tests/test_sidewall_detector_wet_route_binding_closure.py",
    "tools/audits/build_nodi_package_c_sidewall_detector_wet_route_binding_closure.py",
    "tests/test_nodi_package_c_sidewall_detector_wet_route_binding_closure.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sidewall detector/wet route-binding closure harness."
    )
    parser.add_argument(
        "--confirm-sidewall-detector-wet-route-binding-closure",
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
        "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_"
    )
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "detector_wet_closure_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == (
            "reports/565_NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_20260701.md"
        ):
            classification = "detector_wet_closure_output"
            release_decision = "included_or_rewritten_by_detector_wet_closure"
        elif path in source_paths:
            classification = "source_locked_upstream_dirty_context"
            release_decision = "source_locked_current_workspace_not_in_commit_scope"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_detector_wet_closure"
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
                "closure_rows": payload["closure_rows"],
                "guard_rows": payload["guard_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    rows, guards = build_detector_wet_route_binding_closure(
        route_evidence_state_rows=read_csv_rows(STATE_UPDATE_ROUTE_ROWS),
        route_candidate_status=load_status(ROUTE_CANDIDATE_STATUS),
        selected_annulus_status=load_status(SELECTED_ANNULUS_STATUS),
        detector_execution_status=load_status(DETECTOR_EXECUTION_STATUS),
        detector_validation_status=load_status(DETECTOR_VALIDATION_STATUS),
        wet_execution_status=load_status(WET_EXECUTION_STATUS),
        wet_validation_status=load_status(WET_VALIDATION_STATUS),
    )
    closure_rows = [row.to_dict() for row in rows]
    guard_rows = [row.to_dict() for row in guards]
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    status = (
        DISPOSITION
        if source_missing == 0
        and len(closure_rows) == 2
        and len(guard_rows) == 5
        and all(row["route_formula_binding_authorized"] for row in closure_rows)
        and sum(row["route_score_current"] for row in closure_rows) == 0
        and sum(row["activation_allowed_now"] for row in guard_rows) == 0
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "closure_status": SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_state_update_disposition": str(load_status(STATE_UPDATE_STATUS).get("disposition", "")),
        "closure_rows": len(closure_rows),
        "guard_rows": len(guard_rows),
        "route_formula_binding_authorized_rows": sum(
            row["route_formula_binding_authorized"] for row in closure_rows
        ),
        "route_formula_binding_ready_rows": sum(
            row["route_formula_binding_status"]
            == "route_formula_binding_inputs_ready_for_candidate_values"
            for row in closure_rows
        ),
        "qch_ready_rows": sum(row["qch_route_input_ready"] for row in closure_rows),
        "selected_annulus_ready_rows": sum(
            row["selected_annulus_context_ready"] for row in closure_rows
        ),
        "runtime_guard_ready_rows": sum(
            row["runtime_substep_guard_ready"] for row in closure_rows
        ),
        "profile_grid_candidate_ready_rows": sum(
            row["profile_grid_candidate_ready"] for row in closure_rows
        ),
        "detector_validator_hardened_rows": sum(
            row["detector_validator_hardened"] for row in closure_rows
        ),
        "wet_validator_hardened_rows": sum(row["wet_validator_hardened"] for row in closure_rows),
        "detector_accepted_transfer_rows_total": sum(
            row["detector_accepted_transfer_rows"] for row in closure_rows
        ),
        "wet_accepted_observation_rows_total": sum(
            row["wet_accepted_observation_rows"] for row in closure_rows
        ),
        "route_score_current_rows": sum(row["route_score_current"] for row in closure_rows),
        "yield_current_rows": sum(row["yield_current"] for row in closure_rows),
        "detection_probability_current_rows": sum(
            row["detection_probability_current"] for row in closure_rows
        ),
        "activation_allowed_guard_rows": sum(
            row["activation_allowed_now"] for row in guard_rows
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
        "closure_rows": closure_rows,
        "guard_rows": guard_rows,
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
        "two closure rows": s["closure_rows"] == 2,
        "five guards": s["guard_rows"] == 5,
        "binding authorized": s["route_formula_binding_authorized_rows"] == 2,
        "binding not ready": s["route_formula_binding_ready_rows"] == 0,
        "qch ready": s["qch_ready_rows"] == 2,
        "selected annulus ready": s["selected_annulus_ready_rows"] == 2,
        "runtime guard ready": s["runtime_guard_ready_rows"] == 2,
        "profile grid ready": s["profile_grid_candidate_ready_rows"] == 2,
        "detector validator hardened": s["detector_validator_hardened_rows"] == 2,
        "wet validator hardened": s["wet_validator_hardened_rows"] == 2,
        "no detector accepted": s["detector_accepted_transfer_rows_total"] == 0,
        "no wet accepted": s["wet_accepted_observation_rows_total"] == 0,
        "no route score": s["route_score_current_rows"] == 0,
        "no yield": s["yield_current_rows"] == 0,
        "no detection": s["detection_probability_current_rows"] == 0,
        "no activation": s["activation_allowed_guard_rows"] == 0,
    }
    for row in payload["closure_rows"]:
        checks[f"closure guarded {row['closure_row_id']}"] = (
            row["claim_boundary"] == CLAIM_BOUNDARY
            and row["route_formula_binding_status"]
            == "blocked_accepted_detector_blank_and_wet_rows_required"
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_CLOSURE_ROWS_20260701.csv": payload["closure_rows"],
        f"{PREFIX}_GUARD_ROWS_20260701.csv": payload["guard_rows"],
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
    public_report = REPORT_DIR / "565_NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_20260701.md"
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
            "# NODI Package C Sidewall Detector/Wet Route-Binding Closure",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Closure rows: `{s['closure_rows']}`; guard rows: `{s['guard_rows']}`.",
            f"- Ready inputs q_ch/selected-annulus/runtime/profile-grid: `{s['qch_ready_rows']}` / `{s['selected_annulus_ready_rows']}` / `{s['runtime_guard_ready_rows']}` / `{s['profile_grid_candidate_ready_rows']}`.",
            f"- Accepted detector/wet rows: `{s['detector_accepted_transfer_rows_total']}` / `{s['wet_accepted_observation_rows_total']}`.",
            f"- route/yield/detection current rows: `{s['route_score_current_rows']}` / `{s['yield_current_rows']}` / `{s['detection_probability_current_rows']}`.",
            "",
            "This closure harness consolidates detector/blank, wet observation, selected-annulus, q_ch, runtime, and profile-grid prerequisites for both rectangle and trapezoid route candidates. It is formula-binding ready as a harness, but candidate values remain blocked until accepted detector/blank and wet observation rows exist.",
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
                "policy_impact": "detector_wet_route_binding_closure_harness",
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
    if not args.confirm_sidewall_detector_wet_route_binding_closure:
        parser.error("--confirm-sidewall-detector-wet-route-binding-closure is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
