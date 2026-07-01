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
from nodi_simulator.sidewall_selected_annulus_context import (  # noqa: E402
    SIDEWALL_SELECTED_ANNULUS_CONTEXT_CLAIM_BOUNDARY,
    SIDEWALL_SELECTED_ANNULUS_CONTEXT_VERSION,
    run_sidewall_selected_annulus_context,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_READY_NOT_PROBABILITY"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

PROMOTION_LEDGER_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_STATUS_20260701.json"
)
PROMOTION_LANE_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PROMOTION_LANE_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "sidewall selected-annulus context;small-n NODI diagnostic rerun;"
    "promotion-ledger blocker reduction planning"
)
BLOCKED_USE = (
    "detection_probability;route_score;winner;JRC;yield;wet pass;production ingestion"
)

SOURCE_FILES = {
    "integrated_promotion_ledger_status": PROMOTION_LEDGER_STATUS,
    "integrated_promotion_lane_rows": PROMOTION_LANE_ROWS,
    "selected_annulus_context_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_selected_annulus_context.py",
    "selected_annulus_context_tests": PROJECT_ROOT
    / "tests/test_sidewall_selected_annulus_context.py",
    "selected_annulus_context_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_selected_annulus_context.py",
    "selected_annulus_context_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_selected_annulus_context.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_selected_annulus_context.py",
    "tests/test_sidewall_selected_annulus_context.py",
    "tools/audits/build_nodi_package_c_sidewall_selected_annulus_context.py",
    "tests/test_nodi_package_c_sidewall_selected_annulus_context.py",
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
        description="Build Package C sidewall selected-annulus context packet."
    )
    parser.add_argument("--confirm-sidewall-selected-annulus-context", action="store_true")
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
            "NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_"
        )
        or path == "reports/531_NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "sidewall_selected_annulus_context_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_"
        ) or path == "reports/531_NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_20260701.md":
            classification = "sidewall_selected_annulus_context_output"
            release_decision = "included_or_rewritten_by_sidewall_selected_annulus_context"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_sidewall_selected_annulus_context"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_sidewall_selected_annulus_context_not_source_locked"
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
                "claim_boundary": SIDEWALL_SELECTED_ANNULUS_CONTEXT_CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def context_rows() -> list[dict[str, str]]:
    return [_stringify_row(row.to_dict()) for row in run_sidewall_selected_annulus_context()]


def promotion_update_rows() -> list[dict[str, str]]:
    return [
        {
            "target_ledger_lane": "selected_annulus_detection_context",
            "previous_status": "selected_annulus_context_missing_rerun_required",
            "new_context_status": "selected_annulus_context_available_small_n_not_probability",
            "new_context_artifact": (
                "reports/joint_interface_20260701/"
                "NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_CONTEXT_ROWS_20260701.csv"
            ),
            "allowed_ledger_update": "replace_missing_with_context_available",
            "blocked_promotion": "detection_probability;route_score;winner",
            "hard_fail_if": "selected_annulus_context_promoted_to_detection_probability",
            "claim_boundary": SIDEWALL_SELECTED_ANNULUS_CONTEXT_CLAIM_BOUNDARY,
        }
    ]


def self_review_rows() -> list[dict[str, str]]:
    topics = [
        "selected annulus rerun context is available for rectangle and theta85",
        "annulus detection values are small-n context rates",
        "detection probability and route score remain false",
        "integrated promotion ledger may now replace missing with context-available",
    ]
    return [
        {
            "review_id": f"SELANN-SELF-{index:02d}",
            "dimension": topic,
            "verdict": "PASS_SELECTED_ANNULUS_CONTEXT_NOT_PROBABILITY",
            "notes": "Context reduces a ledger blocker but does not promote detection or route claims.",
        }
        for index, topic in enumerate(topics, start=1)
    ]


def build_payload() -> dict[str, Any]:
    source_status = load_json(PROMOTION_LEDGER_STATUS)
    rows = context_rows()
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    current_rows = sum(row["selected_annulus_context_current"] == "true" for row in rows)
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and source_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_READY_PREFLIGHT_ONLY"
        and len(rows) == 2
        and current_rows == 2
        and all(row["detection_probability_current"] == "false" for row in rows)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": SIDEWALL_SELECTED_ANNULUS_CONTEXT_CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "context_version": SIDEWALL_SELECTED_ANNULUS_CONTEXT_VERSION,
        "source_promotion_ledger_disposition": source_status.get("disposition", ""),
        "context_rows": len(rows),
        "selected_annulus_context_current_rows": current_rows,
        "small_n_synthetic_context": True,
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
        "promotion_update_rows": promotion_update_rows(),
        "source_lock": source_lock,
        "dirty_context": dirty_context,
        "self_review": self_review_rows(),
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "context_rows": payload["context_rows"],
        "promotion_update_rows": payload["promotion_update_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "two context rows": summary["context_rows"] == 2,
        "both rows current": summary["selected_annulus_context_current_rows"] == 2,
        "detection false": summary["detection_probability_current"] is False,
        "route false": summary["route_score_current"] is False,
    }
    for row in payload["context_rows"]:
        checks[f"context not final {row['row_id']}"] = (
            row["selected_annulus_context_current"] == "true"
            and row["small_n_synthetic_context"] == "true"
            and row["detection_probability_current"] == "false"
            and row["route_score_current"] == "false"
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_CONTEXT_ROWS_20260701.csv": payload["context_rows"],
        f"{PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv": payload["promotion_update_rows"],
        f"{PREFIX}_SOURCE_LOCK_20260701.csv": payload["source_lock"],
        f"{PREFIX}_DIRTY_CONTEXT_20260701.csv": payload["dirty_context"],
        f"{PREFIX}_SELF_REVIEW_20260701.csv": payload["self_review"],
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

    public_report = REPORT_DIR / "531_NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT_20260701.md"
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
            "# NODI Package C Sidewall Selected-Annulus Context",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Context version: `{s['context_version']}`.",
            f"- Context rows: `{s['context_rows']}`.",
            f"- Selected-annulus current rows: `{s['selected_annulus_context_current_rows']}`.",
            "- This packet executes small W500/D900 NODI sidewall selected-annulus smoke rows.",
            "- It may reduce the integrated ledger's selected-annulus missing blocker to context-available, but it is still not detection probability, route score, winner/JRC, or yield.",
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
                "policy_impact": "sidewall_selected_annulus_context_not_probability",
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


def _stringify_row(row: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in row.items():
        if isinstance(value, bool):
            out[key] = str(value).lower()
        elif isinstance(value, float):
            if value != value:
                out[key] = "nan"
            else:
                out[key] = f"{value:.12g}"
        else:
            out[key] = str(value)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_sidewall_selected_annulus_context:
        parser.error("--confirm-sidewall-selected-annulus-context is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_SELECTED_ANNULUS_CONTEXT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
