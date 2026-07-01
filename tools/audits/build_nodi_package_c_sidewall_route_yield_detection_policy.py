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
from nodi_simulator.sidewall_route_yield_detection_policy import (  # noqa: E402
    REQUIRED_LANES,
    SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_CLAIM_BOUNDARY,
    build_route_yield_detection_policy_rows,
    route_yield_detection_policy_promotion_update_rows,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_READY_NOT_CLAIM_READY"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_CLAIM_BOUNDARY

LEDGER_WET_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_WET_SURFACE_REFRESH_STATUS_20260701.json"
)
LEDGER_WET_LANES = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_WET_SURFACE_REFRESH_PROMOTION_LANE_ROWS_20260701.csv"
)

ALLOWED_USE = "route/yield/detection readiness policy;promotion blocker prioritization"
BLOCKED_USE = (
    "route_score;winner;JRC;yield;detection_probability;wet_pass_probability;"
    "clogging_rate;time_to_clog;recovery;production ingestion"
)

SOURCE_FILES = {
    "integrated_promotion_ledger_wet_surface_status": LEDGER_WET_STATUS,
    "integrated_promotion_ledger_wet_surface_lanes": LEDGER_WET_LANES,
    "route_yield_detection_policy_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_route_yield_detection_policy.py",
    "route_yield_detection_policy_tests": PROJECT_ROOT
    / "tests/test_sidewall_route_yield_detection_policy.py",
    "route_yield_detection_policy_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_route_yield_detection_policy.py",
    "route_yield_detection_policy_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_route_yield_detection_policy.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_route_yield_detection_policy.py",
    "tests/test_sidewall_route_yield_detection_policy.py",
    "tools/audits/build_nodi_package_c_sidewall_route_yield_detection_policy.py",
    "tests/test_nodi_package_c_sidewall_route_yield_detection_policy.py",
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
        description="Build sidewall route/yield/detection readiness policy rows."
    )
    parser.add_argument("--confirm-sidewall-route-yield-detection-policy", action="store_true")
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
            "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_"
        )
        or path
        == "reports/539_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "route_yield_detection_policy_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_"
        ) or path == (
            "reports/539_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_20260701.md"
        ):
            classification = "route_yield_detection_policy_output"
            release_decision = "included_or_rewritten_by_route_yield_detection_policy"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_route_yield_detection_policy"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_route_yield_detection_policy_not_source_locked"
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
    ledger_status = load_json(LEDGER_WET_STATUS)
    policy_rows, blocker_rows = build_route_yield_detection_policy_rows(
        read_csv_rows(LEDGER_WET_LANES)
    )
    policy_dicts = [row.to_dict() for row in policy_rows]
    blocker_dicts = [row.to_dict() for row in blocker_rows]
    promotion_updates = route_yield_detection_policy_promotion_update_rows(policy_rows)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    not_ready_rows = sum(
        row.route_policy_status
        == "not_ready_missing_calibrated_flow_detector_blank_wet_evidence"
        for row in policy_rows
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and ledger_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_WET_SURFACE_REFRESH_READY_PREFLIGHT_ONLY"
        and len(policy_rows) == 2
        and len(blocker_rows) == 2 * len(REQUIRED_LANES)
        and len(promotion_updates) == 1
        and not_ready_rows == 2
        and all(row.route_score_allowed is False for row in policy_rows)
        and all(row.yield_allowed is False for row in policy_rows)
        and all(row.detection_probability_allowed is False for row in policy_rows)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_ledger_wet_surface_disposition": ledger_status.get("disposition", ""),
        "policy_rows": len(policy_rows),
        "blocker_rows": len(blocker_rows),
        "required_lanes_per_route": len(REQUIRED_LANES),
        "promotion_update_rows": len(promotion_updates),
        "not_ready_policy_rows": not_ready_rows,
        "route_score_allowed_rows": sum(row.route_score_allowed for row in policy_rows),
        "winner_allowed_rows": sum(row.winner_allowed for row in policy_rows),
        "yield_allowed_rows": sum(row.yield_allowed for row in policy_rows),
        "detection_probability_allowed_rows": sum(
            row.detection_probability_allowed for row in policy_rows
        ),
        "wet_pass_probability_allowed_rows": sum(
            row.wet_pass_probability_allowed for row in policy_rows
        ),
        "primary_next_execution_blocks": sorted(
            {row.primary_next_execution_block for row in policy_rows}
        ),
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
        "policy_rows": policy_dicts,
        "blocker_rows": blocker_dicts,
        "promotion_update_rows": promotion_updates,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "policy_rows": payload["policy_rows"],
        "blocker_rows": payload["blocker_rows"],
        "promotion_update_rows": payload["promotion_update_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "two policy rows": summary["policy_rows"] == 2,
        "twelve blocker rows": summary["blocker_rows"] == 2 * len(REQUIRED_LANES),
        "one promotion update": summary["promotion_update_rows"] == 1,
        "two not ready rows": summary["not_ready_policy_rows"] == 2,
        "route score disallowed": summary["route_score_allowed_rows"] == 0,
        "winner disallowed": summary["winner_allowed_rows"] == 0,
        "yield disallowed": summary["yield_allowed_rows"] == 0,
        "detection disallowed": summary["detection_probability_allowed_rows"] == 0,
        "wet pass disallowed": summary["wet_pass_probability_allowed_rows"] == 0,
    }
    for row in payload["policy_rows"]:
        checks[f"policy not final {row['policy_row_id']}"] = (
            row["route_score_allowed"] is False
            and row["winner_allowed"] is False
            and row["yield_allowed"] is False
            and row["detection_probability_allowed"] is False
            and row["wet_pass_probability_allowed"] is False
            and row["route_policy_status"]
            == "not_ready_missing_calibrated_flow_detector_blank_wet_evidence"
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    policy_path = OUTPUT_DIR / f"{PREFIX}_POLICY_ROWS_20260701.csv"
    write_csv_rows(policy_path, payload["policy_rows"])
    paths.append(policy_path)

    blocker_path = OUTPUT_DIR / f"{PREFIX}_BLOCKER_ROWS_20260701.csv"
    write_csv_rows(blocker_path, payload["blocker_rows"])
    paths.append(blocker_path)

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
        REPORT_DIR / "539_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_20260701.md"
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
            "# NODI Package C Sidewall Route/Yield/Detection Policy",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Policy rows: `{s['policy_rows']}`.",
            f"- Blocker rows: `{s['blocker_rows']}`.",
            f"- Primary next execution blocks: `{';'.join(s['primary_next_execution_blocks'])}`.",
            "- Route score, winner/JRC, yield, wet pass probability, and detection probability are not allowed by this policy packet.",
            "- The policy prioritizes formal qch/pressure-flow validation, then detector/blank calibration, wet/surface validation, and selected-annulus panel expansion.",
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
                "policy_impact": "route_yield_detection_policy_not_claim_promotion",
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
    if not args.confirm_sidewall_route_yield_detection_policy:
        parser.error("--confirm-sidewall-route-yield-detection-policy is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
