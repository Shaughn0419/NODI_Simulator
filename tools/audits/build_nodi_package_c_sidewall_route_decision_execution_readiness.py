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
from nodi_simulator.sidewall_route_decision_execution_readiness import (  # noqa: E402
    ROUTE_DECISION_EXECUTION_READINESS_STATUS,
    SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_CLAIM_BOUNDARY,
    build_route_decision_execution_readiness,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_READY_BRANCH_STATUSES_NOT_CLAIMS"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_CLAIM_BOUNDARY

BOARD_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_STATUS_20260701.json"
BOARD_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_BOARD_ROWS_20260701.csv"
SOLVER_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_STATUS_20260701.json"
EK_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_STATUS_20260701.json"
COMSOL_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_COMSOL_LAUNCH_PRECONDITION_STATUS_20260701.json"
DETECTOR_WET_ACTIVATION_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_STATUS_20260701.json"
ROUTE_FORMULA_DRY_RUN_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_STATUS_20260701.json"
ROUTE_FORMULA_DRY_RUN_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_DRY_RUN_ROWS_20260701.csv"

ALLOWED_USE = "route/yield/detection execution readiness integration;rectangle plus trapezoid route status"
BLOCKED_USE = "route_score;winner;JRC;yield;detection_probability;production ingestion;fabrication release"

SOURCE_FILES = {
    "readiness_board_status": BOARD_STATUS,
    "readiness_board_rows": BOARD_ROWS,
    "solver_branch_status": SOLVER_STATUS,
    "electrokinetic_preflight_status": EK_STATUS,
    "comsol_precondition_status": COMSOL_STATUS,
    "detector_wet_activation_status": DETECTOR_WET_ACTIVATION_STATUS,
    "route_formula_dry_run_status": ROUTE_FORMULA_DRY_RUN_STATUS,
    "route_formula_dry_run_rows": ROUTE_FORMULA_DRY_RUN_ROWS,
    "route_decision_execution_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_route_decision_execution_readiness.py",
    "route_decision_execution_tests": PROJECT_ROOT
    / "tests/test_sidewall_route_decision_execution_readiness.py",
    "route_decision_execution_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_route_decision_execution_readiness.py",
    "route_decision_execution_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_route_decision_execution_readiness.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_route_decision_execution_readiness.py",
    "tests/test_sidewall_route_decision_execution_readiness.py",
    "tools/audits/build_nodi_package_c_sidewall_route_decision_execution_readiness.py",
    "tests/test_nodi_package_c_sidewall_route_decision_execution_readiness.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build route decision execution readiness packet.")
    parser.add_argument("--confirm-sidewall-route-decision-execution-readiness", action="store_true")
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


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    source_paths = {
        display_path(source_path)
        for source_path in SOURCE_FILES.values()
        if source_path.exists()
    }
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "route_decision_execution_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_"
        ) or path == (
            "reports/561_NODI_PACKAGE_C_SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_20260701.md"
        ):
            classification = "route_decision_execution_output"
            release_decision = "included_or_rewritten_by_route_decision_execution"
        elif path in source_paths:
            classification = "source_locked_upstream_dirty_context"
            release_decision = "source_locked_current_workspace_not_in_commit_scope"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_route_decision_execution"
        rows.append({"path": path, "git_status": line[:2], "classification": classification, "release_decision": release_decision})
    return rows


def source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_id, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append({
            "source_id": source_id,
            "path": display_path(path) if exists else str(path),
            "exists": str(exists).lower(),
            "sha256": sha256_file(path) if exists else "",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        })
    return rows


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {"readiness_rows": payload["readiness_rows"], "claim_guard_rows": payload["claim_guard_rows"]},
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    rows, guards = build_route_decision_execution_readiness(
        readiness_board_rows=read_csv_rows(BOARD_ROWS),
        solver_packet_status=load_json(SOLVER_STATUS),
        electrokinetic_status=load_json(EK_STATUS),
        comsol_precondition_status=load_json(COMSOL_STATUS),
        detector_blank_status=load_json(DETECTOR_WET_ACTIVATION_STATUS),
        wet_observation_status=load_json(DETECTOR_WET_ACTIVATION_STATUS),
        route_formula_dry_run_status=load_json(ROUTE_FORMULA_DRY_RUN_STATUS),
        route_formula_dry_run_rows=read_csv_rows(ROUTE_FORMULA_DRY_RUN_ROWS),
    )
    readiness_dicts = [row.to_dict() for row in rows]
    guard_dicts = [row.to_dict() for row in guards]
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    status = (
        DISPOSITION
        if source_missing == 0
        and len(readiness_dicts) == 2
        and len(guard_dicts) == 5
        and {row["route_geometry_family"] for row in readiness_dicts}
        == {"ideal_rectangle", "trapezoid_tapered_sidewalls"}
        and all(row["rectangle_baseline_preserved"] is True for row in readiness_dicts)
        and all(row["sidewall_trapezoid_route_present"] is True for row in readiness_dicts)
        and all(row["route_score_current"] is False for row in readiness_dicts)
        and all(row["claim_promotion_allowed_now"] is False for row in guard_dicts)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "execution_status": ROUTE_DECISION_EXECUTION_READINESS_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "readiness_rows": len(readiness_dicts),
        "claim_guard_rows": len(guard_dicts),
        "route_geometry_families": ";".join(sorted({row["route_geometry_family"] for row in readiness_dicts})),
        "rectangle_baseline_rows": sum(row["route_geometry_family"] == "ideal_rectangle" for row in readiness_dicts),
        "trapezoid_route_rows": sum(row["route_geometry_family"] == "trapezoid_tapered_sidewalls" for row in readiness_dicts),
        "detector_accepted_transfer_rows_total": sum(row["detector_accepted_transfer_rows"] for row in readiness_dicts),
        "wet_accepted_observation_rows_total": sum(row["wet_accepted_observation_rows"] for row in readiness_dicts),
        "route_formula_component_vector_ready_rows": sum(row["route_formula_component_vector_ready"] for row in readiness_dicts),
        "route_score_current_rows": sum(row["route_score_current"] for row in readiness_dicts),
        "winner_current_rows": sum(row["winner_current"] for row in readiness_dicts),
        "yield_current_rows": sum(row["yield_current"] for row in readiness_dicts),
        "detection_probability_current_rows": sum(row["detection_probability_current"] for row in readiness_dicts),
        "production_ingestion_current_rows": sum(row["production_ingestion_current"] for row in readiness_dicts),
        "claim_promotion_allowed_guard_rows": sum(row["claim_promotion_allowed_now"] for row in guard_dicts),
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "source_locked_upstream_dirty_context_rows": sum(row["classification"] == "source_locked_upstream_dirty_context" for row in dirty_context),
        "non_release_dirty_context_rows": sum(row["classification"] == "non_release_dirty_context" for row in dirty_context),
        "release_scoped_dirty_blocker_rows": 0,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "readiness_rows": readiness_dicts,
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
        "two readiness rows": s["readiness_rows"] == 2,
        "five guard rows": s["claim_guard_rows"] == 5,
        "rectangle and trapezoid": s["route_geometry_families"] == "ideal_rectangle;trapezoid_tapered_sidewalls",
        "no route score": s["route_score_current_rows"] == 0,
        "no winner": s["winner_current_rows"] == 0,
        "no yield": s["yield_current_rows"] == 0,
        "no detection": s["detection_probability_current_rows"] == 0,
        "no production": s["production_ingestion_current_rows"] == 0,
        "no guard promotion": s["claim_promotion_allowed_guard_rows"] == 0,
    }
    for row in payload["readiness_rows"]:
        checks[f"route guarded {row['readiness_row_id']}"] = (
            row["claim_boundary"] == CLAIM_BOUNDARY
            and row["execution_readiness_status"] in {
                "blocked_detector_blank_and_wet_observation_evidence_required",
                "blocked_route_formula_component_vector_required",
                "branch_evidence_and_formula_components_ready_for_route_policy_review",
            }
            and row["rectangle_baseline_preserved"] is True
            and row["sidewall_trapezoid_route_present"] is True
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_READINESS_ROWS_20260701.csv": payload["readiness_rows"],
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
    public_report = REPORT_DIR / "561_NODI_PACKAGE_C_SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_20260701.md"
    public_report.write_text(report_markdown(payload), encoding="utf-8", newline="\n")
    paths.append(public_report)
    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv"
    write_csv_rows(manifest_path, manifest_rows(paths, manifest_path))
    paths.append(manifest_path)
    return paths


def report_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join([
        "# NODI Package C Sidewall Route Decision Execution Readiness",
        "",
        f"- Disposition: `{s['disposition']}`.",
        f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
        f"- Route geometry families: `{s['route_geometry_families']}`.",
        f"- Detector accepted transfer rows: `{s['detector_accepted_transfer_rows_total']}`.",
        f"- Wet accepted observation rows: `{s['wet_accepted_observation_rows_total']}`.",
        f"- Formula component-vector ready rows: `{s['route_formula_component_vector_ready_rows']}`.",
        f"- route/yield/detection current rows: `{s['route_score_current_rows']}` / `{s['yield_current_rows']}` / `{s['detection_probability_current_rows']}`.",
        "- Rectangle baseline and sidewall trapezoid route remain side by side; route decisions remain blocked until detector/blank and wet evidence packets contain accepted rows.",
        "",
    ])


def manifest_rows(paths: list[Path], manifest_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.append({
            "artifact": path.name,
            "path": display_path(path),
            "sha256": sha256_file(path),
            "disposition": DISPOSITION,
            "policy_impact": "route_decision_execution_readiness_not_claim",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        })
    rows.append({
        "artifact": manifest_path.name,
        "path": display_path(manifest_path),
        "sha256": SELF_MANIFEST_SHA256,
        "disposition": DISPOSITION,
        "policy_impact": "manifest_self_row_no_recursive_sha",
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    })
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_sidewall_route_decision_execution_readiness:
        parser.error("--confirm-sidewall-route-decision-execution-readiness is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
