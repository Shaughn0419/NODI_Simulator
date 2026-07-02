#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
from nodi_simulator.sidewall_electrokinetic_profile_grid_candidate import (  # noqa: E402
    SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_CLAIM_BOUNDARY,
    SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_STATUS,
    build_profile_grid_candidate,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_READY_NOT_SOLVER"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_CLAIM_BOUNDARY

PREFLIGHT_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_STATUS_20260701.json"
PREFLIGHT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_PREFLIGHT_ROWS_20260701.csv"
WORK_ORDER_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_STATUS_20260701.json"
WORK_ORDER_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_WORK_ORDER_ROWS_20260701.csv"

ALLOWED_USE = (
    "profile-aware electrokinetic grid candidate;rectangle-limit and mutation evidence;"
    "blocked-bin exclusion evidence"
)
BLOCKED_USE = (
    "electrokinetic solver output;calibrated electrokinetic weighting;route_score;"
    "winner;JRC;yield;detection_probability;production ingestion"
)

SOURCE_FILES = {
    "electrokinetic_preflight_status": PREFLIGHT_STATUS,
    "electrokinetic_preflight_rows": PREFLIGHT_ROWS,
    "mainline_work_order_status": WORK_ORDER_STATUS,
    "mainline_work_order_rows": WORK_ORDER_ROWS,
    "cross_section_geometry": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
    "profile_grid_candidate_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_electrokinetic_profile_grid_candidate.py",
    "profile_grid_candidate_tests": PROJECT_ROOT
    / "tests/test_sidewall_electrokinetic_profile_grid_candidate.py",
    "profile_grid_candidate_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_electrokinetic_profile_grid_candidate.py",
    "profile_grid_candidate_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_electrokinetic_profile_grid_candidate.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_electrokinetic_profile_grid_candidate.py",
    "tests/test_sidewall_electrokinetic_profile_grid_candidate.py",
    "tools/audits/build_nodi_package_c_sidewall_electrokinetic_profile_grid_candidate.py",
    "tests/test_nodi_package_c_sidewall_electrokinetic_profile_grid_candidate.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sidewall electrokinetic profile-grid candidate packet."
    )
    parser.add_argument(
        "--confirm-sidewall-electrokinetic-profile-grid-candidate",
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


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    source_paths = {
        display_path(source_path)
        for source_path in SOURCE_FILES.values()
        if source_path.exists()
    }
    output_prefix = (
        "reports/joint_interface_20260701/"
        "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_"
    )
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "electrokinetic_profile_grid_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == (
            "reports/563_NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_20260701.md"
        ):
            classification = "electrokinetic_profile_grid_output"
            release_decision = "included_or_rewritten_by_profile_grid_candidate"
        elif path in source_paths:
            classification = "source_locked_upstream_dirty_context"
            release_decision = "source_locked_current_workspace_not_in_commit_scope"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_profile_grid_candidate"
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
                "case_rows": payload["case_rows"],
                "mutation_check_rows": payload["mutation_check_rows"],
                "claim_guard_rows": payload["claim_guard_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    case_rows_obj, cell_rows_obj, mutation_rows_obj, guard_rows_obj = (
        build_profile_grid_candidate()
    )
    case_rows = [row.to_dict() for row in case_rows_obj]
    cell_rows = [row.to_dict() for row in cell_rows_obj]
    mutation_rows = [row.to_dict() for row in mutation_rows_obj]
    guard_rows = [row.to_dict() for row in guard_rows_obj]
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    status = (
        DISPOSITION
        if source_missing == 0
        and len(case_rows) == 5
        and len(cell_rows) == 2205
        and len(mutation_rows) == 5
        and len(guard_rows) == 5
        and all(row["mutation_check_passed"] is True for row in mutation_rows)
        and sum(row["blocked_cell_weight_rows"] for row in case_rows) == 0
        and sum(row["electrokinetic_solver_output_current"] for row in case_rows) == 0
        and sum(row["electrokinetic_weight_current"] for row in case_rows) == 0
        and sum(row["route_score_current"] for row in case_rows) == 0
        and sum(row["detection_probability_current"] for row in case_rows) == 0
        else BLOCKED_DISPOSITION
    )
    preflight_status = load_status(PREFLIGHT_STATUS)
    work_order_status = load_status(WORK_ORDER_STATUS)
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "candidate_status": SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_preflight_disposition": str(preflight_status.get("disposition", "")),
        "source_work_order_disposition": str(work_order_status.get("disposition", "")),
        "case_rows": len(case_rows),
        "cell_rows": len(cell_rows),
        "mutation_check_rows": len(mutation_rows),
        "claim_guard_rows": len(guard_rows),
        "rectangle_baseline_rows": sum(
            row["channel_cross_section_model"] == "ideal_rectangle" for row in case_rows
        ),
        "trapezoid_profile_grid_rows": sum(
            row["channel_cross_section_model"] == "trapezoid_tapered_sidewalls"
            for row in case_rows
        ),
        "profile_aware_grid_current_rows": sum(
            row["profile_aware_grid_current"] for row in case_rows
        ),
        "blocked_cell_rows_total": sum(row["blocked_cell_rows"] for row in case_rows),
        "blocked_cell_weight_rows_total": sum(
            row["blocked_cell_weight_rows"] for row in case_rows
        ),
        "mutation_check_pass_rows": sum(
            row["mutation_check_passed"] for row in mutation_rows
        ),
        "electrokinetic_solver_output_current_rows": sum(
            row["electrokinetic_solver_output_current"] for row in case_rows
        ),
        "electrokinetic_weight_current_rows": sum(
            row["electrokinetic_weight_current"] for row in case_rows
        ),
        "route_score_current_rows": sum(row["route_score_current"] for row in case_rows),
        "detection_probability_current_rows": sum(
            row["detection_probability_current"] for row in case_rows
        ),
        "claim_promotion_allowed_guard_rows": sum(
            row["claim_promotion_allowed_now"] for row in guard_rows
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
        "case_rows": case_rows,
        "cell_rows": cell_rows,
        "mutation_check_rows": mutation_rows,
        "claim_guard_rows": guard_rows,
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
        "five cases": s["case_rows"] == 5,
        "cell row count": s["cell_rows"] == 2205,
        "five mutation checks": s["mutation_check_rows"] == 5,
        "five guards": s["claim_guard_rows"] == 5,
        "rectangle preserved": s["rectangle_baseline_rows"] == 1,
        "trapezoid rows present": s["trapezoid_profile_grid_rows"] == 4,
        "profile grid rows present": s["profile_aware_grid_current_rows"] == 5,
        "mutation checks pass": s["mutation_check_pass_rows"] == 5,
        "blocked cells unweighted": s["blocked_cell_weight_rows_total"] == 0,
        "no solver output": s["electrokinetic_solver_output_current_rows"] == 0,
        "no electrokinetic weight claim": s["electrokinetic_weight_current_rows"] == 0,
        "no route score": s["route_score_current_rows"] == 0,
        "no detection": s["detection_probability_current_rows"] == 0,
        "no guard promotion": s["claim_promotion_allowed_guard_rows"] == 0,
    }
    for row in payload["cell_rows"]:
        if row["center_accessible"] is False:
            checks[f"blocked cell no weight {row['cell_row_id']}"] = (
                row["electrostatic_weight_surrogate"] is None
                and row["blocked_reason"] == "outside_particle_center_support"
            )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_CASE_ROWS_20260701.csv": payload["case_rows"],
        f"{PREFIX}_CELL_ROWS_20260701.csv": payload["cell_rows"],
        f"{PREFIX}_MUTATION_CHECK_ROWS_20260701.csv": payload["mutation_check_rows"],
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
    public_report = REPORT_DIR / "563_NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_20260701.md"
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
            "# NODI Package C Sidewall Electrokinetic Profile-Grid Candidate",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Case rows / cell rows: `{s['case_rows']}` / `{s['cell_rows']}`.",
            f"- Rectangle / trapezoid case rows: `{s['rectangle_baseline_rows']}` / `{s['trapezoid_profile_grid_rows']}`.",
            f"- Mutation checks passed: `{s['mutation_check_pass_rows']}` / `{s['mutation_check_rows']}`.",
            f"- Blocked cell weight rows: `{s['blocked_cell_weight_rows_total']}`.",
            f"- Solver/weight/route/detection rows: `{s['electrokinetic_solver_output_current_rows']}` / `{s['electrokinetic_weight_current_rows']}` / `{s['route_score_current_rows']}` / `{s['detection_probability_current_rows']}`.",
            "",
            "This packet creates a profile-aware grid candidate over the particle-center support for rectangle and trapezoid cases. It is mutation-tested for rectangle limit, sidewall angle, zeta sign, ionic strength, and blocked-bin exclusion. It is not an electrokinetic solver output and does not activate route, yield, or detection claims.",
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
                "policy_impact": "electrokinetic_profile_grid_candidate_not_solver",
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
    if not args.confirm_sidewall_electrokinetic_profile_grid_candidate:
        parser.error("--confirm-sidewall-electrokinetic-profile-grid-candidate is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE")
        for failure in failures[:50]:
            print(f"FAIL: {failure}")
        if len(failures) > 50:
            print(f"FAIL: {len(failures) - 50} additional failures omitted")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
