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


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_REFRESH"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_REFRESH_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_REFRESH_READY_PREFLIGHT_ONLY"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_REFRESH_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = "promotion_ledger_refresh_not_route_score_not_detection_probability"

LEDGER_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_STATUS_20260701.json"
)
LEDGER_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_LEDGER_ROWS_20260701.csv"
)
PROMOTION_LANE_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PROMOTION_LANE_ROWS_20260701.csv"
)
SELECTED_ANNULUS_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_STATUS_20260701.json"
)
SELECTED_ANNULUS_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_CONTEXT_ROWS_20260701.csv"
)

ALLOWED_USE = "integrated promotion ledger refresh;selected-annulus blocker update"
BLOCKED_USE = (
    "route_score;winner;JRC;detection_probability;yield;wet pass;production ingestion"
)

SOURCE_FILES = {
    "integrated_promotion_ledger_status": LEDGER_STATUS,
    "integrated_promotion_ledger_rows": LEDGER_ROWS,
    "integrated_promotion_lane_rows": PROMOTION_LANE_ROWS,
    "selected_annulus_context_status": SELECTED_ANNULUS_STATUS,
    "selected_annulus_context_rows": SELECTED_ANNULUS_ROWS,
    "ledger_refresh_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_integrated_promotion_ledger_refresh.py",
    "ledger_refresh_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_integrated_promotion_ledger_refresh.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "tools/audits/build_nodi_package_c_sidewall_integrated_promotion_ledger_refresh.py",
    "tests/test_nodi_package_c_sidewall_integrated_promotion_ledger_refresh.py",
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
        description="Refresh sidewall integrated promotion ledger with selected-annulus context."
    )
    parser.add_argument("--confirm-sidewall-integrated-promotion-ledger-refresh", action="store_true")
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
            "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_REFRESH_"
        )
        or path == "reports/532_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_REFRESH_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "integrated_promotion_ledger_refresh_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_REFRESH_"
        ) or path == "reports/532_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_REFRESH_20260701.md":
            classification = "integrated_promotion_ledger_refresh_output"
            release_decision = "included_or_rewritten_by_integrated_promotion_ledger_refresh"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_integrated_promotion_ledger_refresh"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_integrated_promotion_ledger_refresh_not_source_locked"
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


def refreshed_promotion_lane_rows() -> list[dict[str, str]]:
    rows = read_csv_rows(PROMOTION_LANE_ROWS)
    selected_sha = sha256_file(SELECTED_ANNULUS_ROWS)
    selected_path = display_path(SELECTED_ANNULUS_ROWS)
    for row in rows:
        if row.get("evidence_lane") == "selected_annulus_detection_context":
            row["source_artifact"] = selected_path
            row["source_sha256"] = selected_sha
            row["source_disposition"] = (
                "NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_READY_NOT_PROBABILITY"
            )
            row["current_status"] = (
                "selected_annulus_context_available_small_n_not_probability"
            )
            row["required_before_promotion"] = (
                "calibrated detector response and blank-trace validation before probability use"
            )
            row["hard_fail_if_promoted_without"] = (
                "selected_annulus_context_promoted_to_detection_probability"
            )
            row["next_required_evidence"] = (
                "sidewall detector calibration, blank false-positive traces, and larger event panel"
            )
    return rows


def refresh_delta_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "delta_id": f"SELANN-REFRESH-{row['route_candidate_id']}",
            "route_candidate_id": row["route_candidate_id"],
            "evidence_lane": row["evidence_lane"],
            "new_current_status": row["current_status"],
            "source_artifact": row["source_artifact"],
            "target_claim": row["target_claim"],
            "target_claim_current": row["target_claim_current"],
            "blocked_use": BLOCKED_USE,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for row in rows
        if row.get("evidence_lane") == "selected_annulus_detection_context"
    ]


def build_payload() -> dict[str, Any]:
    ledger_status = load_json(LEDGER_STATUS)
    selected_status = load_json(SELECTED_ANNULUS_STATUS)
    lanes = refreshed_promotion_lane_rows()
    deltas = refresh_delta_rows(lanes)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    selected_current = sum(
        row["new_current_status"]
        == "selected_annulus_context_available_small_n_not_probability"
        for row in deltas
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and ledger_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_READY_PREFLIGHT_ONLY"
        and selected_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_READY_NOT_PROBABILITY"
        and len(deltas) == 2
        and selected_current == 2
        and all(row["target_claim_current"] == "false" for row in deltas)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_ledger_disposition": ledger_status.get("disposition", ""),
        "source_selected_annulus_disposition": selected_status.get("disposition", ""),
        "refreshed_promotion_lane_rows": len(lanes),
        "selected_annulus_delta_rows": len(deltas),
        "selected_annulus_context_available_rows": selected_current,
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
        "refreshed_promotion_lane_rows": lanes,
        "refresh_delta_rows": deltas,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "refreshed_promotion_lane_rows": payload["refreshed_promotion_lane_rows"],
        "refresh_delta_rows": payload["refresh_delta_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "two selected deltas": summary["selected_annulus_delta_rows"] == 2,
        "two context available": summary["selected_annulus_context_available_rows"] == 2,
        "detection false": summary["detection_probability_current"] is False,
        "route false": summary["route_score_current"] is False,
    }
    for row in payload["refresh_delta_rows"]:
        checks[f"delta not final {row['delta_id']}"] = (
            row["target_claim_current"] == "false"
            and "detection_probability" in row["blocked_use"]
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_PROMOTION_LANE_ROWS_20260701.csv": payload["refreshed_promotion_lane_rows"],
        f"{PREFIX}_DELTA_ROWS_20260701.csv": payload["refresh_delta_rows"],
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

    public_report = REPORT_DIR / "532_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_REFRESH_20260701.md"
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
            "# NODI Package C Sidewall Integrated Promotion Ledger Refresh",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Refreshed promotion lane rows: `{s['refreshed_promotion_lane_rows']}`.",
            f"- Selected-annulus delta rows: `{s['selected_annulus_delta_rows']}`.",
            "- This refresh replaces the selected-annulus missing status with small-n context available.",
            "- Detection probability, route score, winner/JRC, and yield remain false.",
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
                "policy_impact": "selected_annulus_ledger_refresh_not_promotion",
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
    if not args.confirm_sidewall_integrated_promotion_ledger_refresh:
        parser.error("--confirm-sidewall-integrated-promotion-ledger-refresh is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_REFRESH")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
