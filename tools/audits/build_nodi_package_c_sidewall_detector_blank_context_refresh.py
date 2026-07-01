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
from nodi_simulator.sidewall_detector_blank_context import (  # noqa: E402
    SIDEWALL_DETECTOR_BLANK_CONTEXT_CLAIM_BOUNDARY,
    SIDEWALL_DETECTOR_BLANK_CONTEXT_VERSION,
    build_detector_blank_context_rows,
    detector_blank_promotion_update_rows,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_READY_CONTEXT_ONLY"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

WET_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_STATUS_20260701.json"
)
WET_CONTEXT_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_EVIDENCE_CONTEXT_ROWS_20260701.csv"
)
SELECTED_ANNULUS_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_STATUS_20260701.json"
)
SELECTED_ANNULUS_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_CONTEXT_ROWS_20260701.csv"
)
QCH_LEDGER_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_QCH_REFRESH_STATUS_20260701.json"
)
QCH_LEDGER_LANES = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_QCH_REFRESH_PROMOTION_LANE_ROWS_20260701.csv"
)
OPTICAL_BRIDGE_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_STATUS_20260701.json"
)
OPTICAL_READINESS_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_READINESS_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "detector/blank context refresh;integrated promotion lane update input;"
    "sidewall route/yield/detection evidence planning"
)
BLOCKED_USE = (
    "detector_response_validation;sidewall_specific_blank_trace_validation;"
    "detection_probability;route_score;winner;JRC;yield;wet pass;production ingestion"
)

SOURCE_FILES = {
    "wet_optical_detection_status": WET_STATUS,
    "wet_optical_detection_context_rows": WET_CONTEXT_ROWS,
    "selected_annulus_context_status": SELECTED_ANNULUS_STATUS,
    "selected_annulus_context_rows": SELECTED_ANNULUS_ROWS,
    "qch_refreshed_ledger_status": QCH_LEDGER_STATUS,
    "qch_refreshed_ledger_lanes": QCH_LEDGER_LANES,
    "optical_calibration_bridge_status": OPTICAL_BRIDGE_STATUS,
    "optical_calibration_readiness_rows": OPTICAL_READINESS_ROWS,
    "detector_blank_context_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_detector_blank_context.py",
    "detector_blank_context_tests": PROJECT_ROOT
    / "tests/test_sidewall_detector_blank_context.py",
    "detector_blank_context_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_detector_blank_context_refresh.py",
    "detector_blank_context_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_detector_blank_context_refresh.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_detector_blank_context.py",
    "tests/test_sidewall_detector_blank_context.py",
    "tools/audits/build_nodi_package_c_sidewall_detector_blank_context_refresh.py",
    "tests/test_nodi_package_c_sidewall_detector_blank_context_refresh.py",
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
        description="Build sidewall detector/blank context refresh packet."
    )
    parser.add_argument("--confirm-sidewall-detector-blank-context-refresh", action="store_true")
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
            "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_"
        )
        or path
        == "reports/535_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "sidewall_detector_blank_context_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_"
        ) or path == "reports/535_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_20260701.md":
            classification = "sidewall_detector_blank_context_output"
            release_decision = "included_or_rewritten_by_sidewall_detector_blank_context"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_sidewall_detector_blank_context"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_sidewall_detector_blank_context_not_source_locked"
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
                "claim_boundary": SIDEWALL_DETECTOR_BLANK_CONTEXT_CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def _stringify_row(row: dict[str, Any]) -> dict[str, str]:
    return {key: _stringify(value) for key, value in row.items()}


def _stringify(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def context_rows() -> list[dict[str, str]]:
    rows = build_detector_blank_context_rows(
        read_csv_rows(WET_CONTEXT_ROWS),
        read_csv_rows(SELECTED_ANNULUS_ROWS),
        read_csv_rows(QCH_LEDGER_LANES),
        read_csv_rows(OPTICAL_READINESS_ROWS),
    )
    return [_stringify_row(row.to_dict()) for row in rows]


def promotion_update_rows(context: list[dict[str, str]]) -> list[dict[str, str]]:
    object_rows = build_detector_blank_context_rows(
        read_csv_rows(WET_CONTEXT_ROWS),
        read_csv_rows(SELECTED_ANNULUS_ROWS),
        read_csv_rows(QCH_LEDGER_LANES),
        read_csv_rows(OPTICAL_READINESS_ROWS),
    )
    return [_stringify_row(row) for row in detector_blank_promotion_update_rows(object_rows)]


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "context_rows": payload["context_rows"],
        "promotion_update_rows": payload["promotion_update_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    wet_status = load_json(WET_STATUS)
    selected_status = load_json(SELECTED_ANNULUS_STATUS)
    qch_ledger_status = load_json(QCH_LEDGER_STATUS)
    optical_bridge_status = load_json(OPTICAL_BRIDGE_STATUS)
    rows = context_rows()
    updates = promotion_update_rows(rows)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    context_available = sum(
        row["detector_blank_lane_status"] == "detector_blank_context_available_not_probability"
        for row in rows
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and wet_status.get("disposition")
        == "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_READY_NOT_FINAL"
        and selected_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_READY_NOT_PROBABILITY"
        and qch_ledger_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_QCH_REFRESH_READY_PREFLIGHT_ONLY"
        and optical_bridge_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_READY_SEED_ONLY"
        and len(rows) == 2
        and len(updates) == 2
        and context_available == 2
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": SIDEWALL_DETECTOR_BLANK_CONTEXT_CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "detector_blank_context_version": SIDEWALL_DETECTOR_BLANK_CONTEXT_VERSION,
        "source_wet_disposition": wet_status.get("disposition", ""),
        "source_selected_annulus_disposition": selected_status.get("disposition", ""),
        "source_qch_ledger_disposition": qch_ledger_status.get("disposition", ""),
        "source_optical_bridge_disposition": optical_bridge_status.get("disposition", ""),
        "context_rows": len(rows),
        "detector_blank_context_available_rows": context_available,
        "promotion_update_rows": len(updates),
        "detector_response_validation_current": False,
        "sidewall_specific_blank_trace_current": False,
        "sidewall_specific_optical_calibration_current": False,
        "detection_probability_current": False,
        "route_score_current": False,
        "winner_current": False,
        "yield_current": False,
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
        "context_rows": rows,
        "promotion_update_rows": updates,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "two context rows": summary["context_rows"] == 2,
        "two available rows": summary["detector_blank_context_available_rows"] == 2,
        "two promotion updates": summary["promotion_update_rows"] == 2,
        "detector response false": summary["detector_response_validation_current"] is False,
        "blank trace false": summary["sidewall_specific_blank_trace_current"] is False,
        "detection false": summary["detection_probability_current"] is False,
        "route false": summary["route_score_current"] is False,
    }
    for row in payload["context_rows"]:
        checks[f"context row not probability {row['route_candidate_id']}"] = (
            row["detection_probability_current"] == "false"
            and row["route_score_current"] == "false"
            and row["detector_response_validation_current"] == "false"
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    context_path = OUTPUT_DIR / f"{PREFIX}_CONTEXT_ROWS_20260701.csv"
    write_csv_rows(context_path, payload["context_rows"])
    paths.append(context_path)

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

    public_report = REPORT_DIR / "535_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_20260701.md"
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
            "# NODI Package C Sidewall Detector Blank Context Refresh",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Context rows: `{s['context_rows']}`.",
            f"- Detector/blank context available rows: `{s['detector_blank_context_available_rows']}`.",
            f"- Promotion update rows: `{s['promotion_update_rows']}`.",
            "- This refresh links selected-annulus context, qch ledger status, Tsuyama blank context, and optical readiness.",
            "- Detector response validation, sidewall-specific blank trace validation, detection probability, route score, winner/JRC, and yield remain false.",
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
                "policy_impact": "detector_blank_context_refresh_not_probability",
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
    if not args.confirm_sidewall_detector_blank_context_refresh:
        parser.error("--confirm-sidewall-detector-blank-context-refresh is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
