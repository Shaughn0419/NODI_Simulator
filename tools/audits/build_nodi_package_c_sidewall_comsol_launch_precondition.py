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
from nodi_simulator.sidewall_comsol_launch_precondition import (  # noqa: E402
    COMSOL_LAUNCH_PRECONDITION_READY_STATUS,
    SIDEWALL_COMSOL_LAUNCH_PRECONDITION_CLAIM_BOUNDARY,
    build_comsol_launch_precondition,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_COMSOL_LAUNCH_PRECONDITION"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_COMSOL_LAUNCH_PRECONDITION_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_COMSOL_LAUNCH_PRECONDITION_READY_TARGET_BINDING_REQUIRED"
)
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_COMSOL_LAUNCH_PRECONDITION_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_COMSOL_LAUNCH_PRECONDITION_CLAIM_BOUNDARY

SOLVER_PACKET_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_STATUS_20260701.json"
)
SOLVER_BRANCH_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_BRANCH_ROWS_20260701.csv"
)
ELECTROKINETIC_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_STATUS_20260701.json"
)
LEGACY_MIRROR_REQUEST = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_POST_PROOF_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.csv"
)
COMSOL_PROJECT_PATH = (
    PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
)

ALLOWED_USE = (
    "COMSOL toolchain and launch precondition evidence;current-head mirror requirement;"
    "target model/script binding checklist"
)
BLOCKED_USE = (
    "COMSOL launch;.mph load;solver output claim;formal q_ch;route_score;winner;JRC;"
    "yield;detection_probability;wet_pass_probability;fabrication release;"
    "production ingestion"
)

SOURCE_FILES = {
    "solver_branch_packet_status": SOLVER_PACKET_STATUS,
    "solver_branch_packet_branch_rows": SOLVER_BRANCH_ROWS,
    "electrokinetic_grid_preflight_status": ELECTROKINETIC_STATUS,
    "legacy_post_proof_mirror_request": LEGACY_MIRROR_REQUEST,
    "comsol_launch_precondition_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_comsol_launch_precondition.py",
    "comsol_launch_precondition_tests": PROJECT_ROOT
    / "tests/test_sidewall_comsol_launch_precondition.py",
    "comsol_launch_precondition_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_comsol_launch_precondition.py",
    "comsol_launch_precondition_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_comsol_launch_precondition.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_comsol_launch_precondition.py",
    "tests/test_sidewall_comsol_launch_precondition.py",
    "tools/audits/build_nodi_package_c_sidewall_comsol_launch_precondition.py",
    "tests/test_nodi_package_c_sidewall_comsol_launch_precondition.py",
}

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sidewall COMSOL launch precondition packet."
    )
    parser.add_argument(
        "--confirm-sidewall-comsol-launch-precondition",
        action="store_true",
    )
    return parser


def run_git(args: list[str], *, cwd: Path = PROJECT_ROOT) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={cwd.as_posix()}", *args],
        cwd=cwd,
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
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def detect_command(name: str) -> str:
    result = subprocess.run(
        ["where.exe", name],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.splitlines()[0].strip()


def detect_toolchain() -> dict[str, Any]:
    comsol_path = detect_command("comsol")
    comsolbatch_path = detect_command("comsolbatch")
    version_text = ""
    version_check_passed = False
    if comsolbatch_path:
        result = subprocess.run(
            ["comsolbatch", "-version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=30,
        )
        version_text = result.stdout.strip()
        version_check_passed = result.returncode == 0 and "COMSOL Multiphysics" in version_text
    return {
        "comsol_path": comsol_path,
        "comsolbatch_path": comsolbatch_path,
        "comsol_detected": bool(comsol_path),
        "comsolbatch_detected": bool(comsolbatch_path),
        "version_text": version_text,
        "version_check_passed": version_check_passed,
    }


def detect_comsol_project() -> dict[str, Any]:
    detected = COMSOL_PROJECT_PATH.exists()
    head = ""
    dirty_count = 0
    dirty_summary = ""
    if detected:
        try:
            head = run_git(["rev-parse", "HEAD"], cwd=COMSOL_PROJECT_PATH)
            dirty = run_git(["status", "--short"], cwd=COMSOL_PROJECT_PATH).splitlines()
            dirty_count = len([line for line in dirty if line.strip()])
            dirty_summary = f"dirty_rows={dirty_count}"
        except subprocess.CalledProcessError as exc:
            dirty_summary = f"git_status_failed={exc.returncode}"
    return {
        "project_path": str(COMSOL_PROJECT_PATH),
        "project_detected": detected,
        "head": head,
        "head_bound": bool(head),
        "dirty_count": dirty_count,
        "dirty_summary": dirty_summary,
    }


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
            "NODI_PACKAGE_C_SIDEWALL_COMSOL_LAUNCH_PRECONDITION_"
        )
        or path == "reports/558_NODI_PACKAGE_C_SIDEWALL_COMSOL_LAUNCH_PRECONDITION_20260701.md"
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
            classification = "comsol_launch_precondition_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_COMSOL_LAUNCH_PRECONDITION_"
        ) or path == (
            "reports/558_NODI_PACKAGE_C_SIDEWALL_COMSOL_LAUNCH_PRECONDITION_20260701.md"
        ):
            classification = "comsol_launch_precondition_output"
            release_decision = "included_or_rewritten_by_comsol_launch_precondition"
        elif source_locked_path(path):
            classification = "source_locked_upstream_dirty_context"
            release_decision = "source_locked_current_workspace_not_in_commit_scope"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_comsol_launch_precondition"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_comsol_launch_precondition_not_source_locked"
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
        "precondition_rows": payload["precondition_rows"],
        "context_rows": payload["context_rows"],
        "claim_guard_rows": payload["claim_guard_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    solver_status = load_json(SOLVER_PACKET_STATUS)
    ek_status = load_json(ELECTROKINETIC_STATUS)
    toolchain = detect_toolchain()
    comsol_project = detect_comsol_project()
    precondition_rows, context_rows, guard_rows = build_comsol_launch_precondition(
        solver_branch_rows=read_csv_rows(SOLVER_BRANCH_ROWS),
        electrokinetic_preflight_status=ek_status,
        toolchain=toolchain,
        comsol_project=comsol_project,
        mirror_request_rows=read_csv_rows(LEGACY_MIRROR_REQUEST),
        nodi_current_head=git_head(),
    )
    precondition_dicts = [row.to_dict() for row in precondition_rows]
    context_dicts = [row.to_dict() for row in context_rows]
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
        and solver_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_READY_BRANCHES_GUARDED"
        and ek_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_READY_PROFILE_GRID_REQUIRED"
        and len(precondition_dicts) == 5
        and len(context_dicts) == 4
        and len(guard_dicts) == 6
        and toolchain["comsolbatch_detected"] is True
        and toolchain["version_check_passed"] is True
        and comsol_project["project_detected"] is True
        and all(row["launch_allowed_now"] is False for row in precondition_dicts)
        and all(row["mph_load_allowed_now"] is False for row in precondition_dicts)
        and all(row["claim_promotion_allowed_now"] is False for row in guard_dicts)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "precondition_status": COMSOL_LAUNCH_PRECONDITION_READY_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_solver_branch_packet_disposition": solver_status.get("disposition", ""),
        "source_electrokinetic_preflight_disposition": ek_status.get("disposition", ""),
        "comsol_path": toolchain["comsol_path"],
        "comsolbatch_path": toolchain["comsolbatch_path"],
        "comsolbatch_version": toolchain["version_text"],
        "comsol_project_path": str(COMSOL_PROJECT_PATH),
        "comsol_project_head": comsol_project["head"],
        "comsol_project_dirty_count": comsol_project["dirty_count"],
        "precondition_rows": len(precondition_dicts),
        "context_rows": len(context_dicts),
        "claim_guard_rows": len(guard_dicts),
        "toolchain_passed_rows": sum(
            row["lane"] == "toolchain_detection" and row["precondition_passed"]
            for row in precondition_dicts
        ),
        "precondition_passed_rows": sum(
            row["precondition_passed"] for row in precondition_dicts
        ),
        "launch_allowed_now_rows": sum(
            row["launch_allowed_now"] for row in precondition_dicts
        ),
        "mph_load_allowed_now_rows": sum(
            row["mph_load_allowed_now"] for row in precondition_dicts
        ),
        "target_model_bound_rows": sum(
            row["target_mph_or_model_bound"] for row in precondition_dicts
        ),
        "launch_command_hash_bound_rows": sum(
            row["launch_command_hash_bound"] for row in precondition_dicts
        ),
        "claim_promotion_allowed_guard_rows": sum(
            row["claim_promotion_allowed_now"] for row in guard_dicts
        ),
        "stale_legacy_mirror_context_rows": sum(
            row["context_status"] == "stale_for_current_head" for row in context_dicts
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
        "precondition_rows": precondition_dicts,
        "context_rows": context_dicts,
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
        "five precondition rows": s["precondition_rows"] == 5,
        "four context rows": s["context_rows"] == 4,
        "six guard rows": s["claim_guard_rows"] == 6,
        "toolchain passed": s["toolchain_passed_rows"] == 1,
        "no launch now": s["launch_allowed_now_rows"] == 0,
        "no mph load now": s["mph_load_allowed_now_rows"] == 0,
        "no target model bound": s["target_model_bound_rows"] == 0,
        "no command hash bound": s["launch_command_hash_bound_rows"] == 0,
        "no guard promotion": s["claim_promotion_allowed_guard_rows"] == 0,
        "legacy mirror stale": s["stale_legacy_mirror_context_rows"] >= 1,
    }
    for row in payload["precondition_rows"]:
        checks[f"precondition guarded {row['precondition_row_id']}"] = (
            row["claim_boundary"] == CLAIM_BOUNDARY
            and row["launch_allowed_now"] is False
            and row["mph_load_allowed_now"] is False
            and row["target_mph_or_model_bound"] is False
            and bool(row["hard_fail_if"])
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
        f"{PREFIX}_PRECONDITION_ROWS_20260701.csv": payload["precondition_rows"],
        f"{PREFIX}_CONTEXT_ROWS_20260701.csv": payload["context_rows"],
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
        / "558_NODI_PACKAGE_C_SIDEWALL_COMSOL_LAUNCH_PRECONDITION_20260701.md"
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
            "# NODI Package C Sidewall COMSOL Launch Precondition",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current NODI head: `{s['current_head']}` on `{s['branch']}`.",
            f"- COMSOL batch: `{s['comsolbatch_path']}`.",
            f"- COMSOL version: `{s['comsolbatch_version']}`.",
            f"- COMSOL-side project: `{s['comsol_project_path']}`.",
            f"- COMSOL-side head: `{s['comsol_project_head']}`; dirty rows: `{s['comsol_project_dirty_count']}`.",
            f"- Precondition rows: `{s['precondition_rows']}`.",
            f"- Toolchain passed rows: `{s['toolchain_passed_rows']}`.",
            f"- Target model bound rows: `{s['target_model_bound_rows']}`.",
            f"- Launch command hash bound rows: `{s['launch_command_hash_bound_rows']}`.",
            f"- COMSOL launch / .mph load allowed now: `{s['launch_allowed_now_rows']}` / `{s['mph_load_allowed_now_rows']}`.",
            "- User authorization is recorded as an execution path, but this packet still requires a current-head mirror receipt, branch-specific target model/script, command hash, and output manifest before starting COMSOL.",
            "- The older clean mirror request is retained as stale historical context for the current NODI head.",
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
                "policy_impact": "comsol_launch_precondition_not_launch",
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
    if not args.confirm_sidewall_comsol_launch_precondition:
        parser.error("--confirm-sidewall-comsol-launch-precondition is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_COMSOL_LAUNCH_PRECONDITION")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
