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
from nodi_simulator.sidewall_pressure_flow_validation_harness import (  # noqa: E402
    SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_CLAIM_BOUNDARY,
    build_pressure_flow_validation_control_rows,
    build_pressure_flow_validation_request_rows,
    pressure_flow_validation_promotion_update_rows,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_READY_EXECUTION_INPUT"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_CLAIM_BOUNDARY

QCH_GRID_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_STATUS_20260701.json"
)
QCH_GRID_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_GRID_ROWS_20260701.csv"
)
LEDGER_ROUTE_POLICY_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_STATUS_20260701.json"
)
LEDGER_ROUTE_POLICY_LANES = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_PROMOTION_LANE_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "exact W500/D900 pressure-flow validation execution input;COMSOL/measurement request;ledger update input"
)
BLOCKED_USE = (
    "formal_qch_weighting;route_score;winner;JRC;yield;detection_probability;"
    "wet pass;production ingestion without external validation result"
)

SOURCE_FILES = {
    "sidewall_qch_grid_validation_status": QCH_GRID_STATUS,
    "sidewall_qch_grid_validation_rows": QCH_GRID_ROWS,
    "integrated_promotion_ledger_route_policy_status": LEDGER_ROUTE_POLICY_STATUS,
    "integrated_promotion_ledger_route_policy_lanes": LEDGER_ROUTE_POLICY_LANES,
    "pressure_flow_validation_harness_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_pressure_flow_validation_harness.py",
    "pressure_flow_validation_harness_tests": PROJECT_ROOT
    / "tests/test_sidewall_pressure_flow_validation_harness.py",
    "pressure_flow_validation_harness_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_pressure_flow_validation_harness.py",
    "pressure_flow_validation_harness_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_pressure_flow_validation_harness.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_pressure_flow_validation_harness.py",
    "tests/test_sidewall_pressure_flow_validation_harness.py",
    "tools/audits/build_nodi_package_c_sidewall_pressure_flow_validation_harness.py",
    "tests/test_nodi_package_c_sidewall_pressure_flow_validation_harness.py",
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
        description="Build exact W500/D900 pressure-flow validation harness packet."
    )
    parser.add_argument("--confirm-sidewall-pressure-flow-validation-harness", action="store_true")
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
            "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_"
        )
        or path
        == "reports/541_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "pressure_flow_validation_harness_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_"
        ) or path == (
            "reports/541_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_20260701.md"
        ):
            classification = "pressure_flow_validation_harness_output"
            release_decision = "included_or_rewritten_by_pressure_flow_validation_harness"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_pressure_flow_validation_harness"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_pressure_flow_validation_harness_not_source_locked"
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


def build_payload() -> dict[str, Any]:
    qch_status = load_json(QCH_GRID_STATUS)
    ledger_status = load_json(LEDGER_ROUTE_POLICY_STATUS)
    qch_grid_rows = read_csv_rows(QCH_GRID_ROWS)
    request_rows = build_pressure_flow_validation_request_rows(qch_grid_rows)
    control_rows = build_pressure_flow_validation_control_rows(qch_grid_rows)
    request_dicts = [row.to_dict() for row in request_rows]
    control_dicts = [row.to_dict() for row in control_rows]
    update_rows = pressure_flow_validation_promotion_update_rows(request_rows)
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
        and qch_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_READY_CANDIDATE_ONLY"
        and ledger_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_READY_PREFLIGHT_ONLY"
        and len(request_rows) == 2
        and len(control_rows) == 1
        and len(update_rows) == 1
        and all(not row.formal_qch_weighting_current for row in request_rows)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_qch_grid_disposition": qch_status.get("disposition", ""),
        "source_integrated_route_policy_disposition": ledger_status.get("disposition", ""),
        "validation_request_rows": len(request_rows),
        "closed_geometry_control_rows": len(control_rows),
        "promotion_update_rows": len(update_rows),
        "exact_w500_d900_route_requests": len(
            {row.route_candidate_id for row in request_rows}
        ),
        "formal_qch_weighting_current": False,
        "route_score_current": False,
        "winner_current": False,
        "yield_current": False,
        "detection_probability_current": False,
        "comsol_launch_started": False,
        "mph_load_started": False,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context" for row in dirty_context
        ),
        "release_scoped_dirty_blocker_rows": release_dirty_blockers,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "validation_request_rows": request_dicts,
        "closed_geometry_control_rows": control_dicts,
        "promotion_update_rows": update_rows,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "validation_request_rows": payload["validation_request_rows"],
        "closed_geometry_control_rows": payload["closed_geometry_control_rows"],
        "promotion_update_rows": payload["promotion_update_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "two requests": summary["validation_request_rows"] == 2,
        "one closed control": summary["closed_geometry_control_rows"] == 1,
        "one promotion update": summary["promotion_update_rows"] == 1,
        "two exact routes": summary["exact_w500_d900_route_requests"] == 2,
        "formal qch false": summary["formal_qch_weighting_current"] is False,
        "route false": summary["route_score_current"] is False,
        "yield false": summary["yield_current"] is False,
        "detection false": summary["detection_probability_current"] is False,
        "no comsol launch": summary["comsol_launch_started"] is False,
        "no mph load": summary["mph_load_started"] is False,
    }
    for row in payload["validation_request_rows"]:
        checks[f"request not final {row['validation_request_id']}"] = (
            row["validation_status"]
            == "exact_w500_d900_validation_harness_ready_missing_external_result"
            and row["formal_qch_weighting_current"] is False
            and row["route_score_current"] is False
            and row["required_observables"]
            and row["required_metadata"]
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    request_path = OUTPUT_DIR / f"{PREFIX}_REQUEST_ROWS_20260701.csv"
    write_csv_rows(request_path, payload["validation_request_rows"])
    paths.append(request_path)

    control_path = OUTPUT_DIR / f"{PREFIX}_CONTROL_ROWS_20260701.csv"
    write_csv_rows(control_path, payload["closed_geometry_control_rows"])
    paths.append(control_path)

    update_path = OUTPUT_DIR / f"{PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv"
    write_csv_rows(update_path, payload["promotion_update_rows"])
    paths.append(update_path)

    source_lock_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv"
    write_csv_rows(source_lock_path, payload["source_lock"])
    paths.append(source_lock_path)

    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv"
    write_csv_rows(dirty_path, payload["dirty_context"])
    paths.append(dirty_path)

    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(status_path, {"disposition": DISPOSITION, "summary": payload["summary"]})
    paths.append(status_path)

    report_path = OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_path, payload)
    paths.append(report_path)

    public_report = (
        REPORT_DIR
        / "541_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_20260701.md"
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
            "# NODI Package C Sidewall Pressure-Flow Validation Harness",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Validation request rows: `{s['validation_request_rows']}`.",
            f"- Closed geometry controls: `{s['closed_geometry_control_rows']}`.",
            "- This packet converts W500/D900 grid-refined qch candidates into exact COMSOL/measurement validation inputs.",
            "- Formal qch weighting, route score, winner/JRC, yield, and detection probability remain false until external validation results are bound.",
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
                "policy_impact": "pressure_flow_validation_harness_not_formal_qch",
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
    if not args.confirm_sidewall_pressure_flow_validation_harness:
        parser.error("--confirm-sidewall-pressure-flow-validation-harness is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
