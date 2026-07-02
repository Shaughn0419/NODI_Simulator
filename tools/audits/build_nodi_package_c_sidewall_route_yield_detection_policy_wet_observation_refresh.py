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
    BLANK_GUARD_PANEL_STATUS,
    DETECTOR_RESPONSE_PANEL_STATUS,
    REQUIRED_LANES,
    ROUTE_INPUT_READY_BLOCKER_STATUS,
    ROUTE_POLICY_NOT_READY_STATUS,
    SELECTED_ANNULUS_PANEL_STATUS,
    SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_CLAIM_BOUNDARY,
    WET_OBSERVATION_INTAKE_STATUS,
    build_route_yield_detection_policy_rows,
    route_yield_detection_policy_promotion_update_rows,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_WET_OBSERVATION_REFRESH"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_WET_OBSERVATION_REFRESH_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_WET_OBSERVATION_REFRESH_READY_NOT_CLAIM_READY"
)
BLOCKED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_WET_OBSERVATION_REFRESH_FAIL_CLOSED"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_CLAIM_BOUNDARY

LEDGER_WET_OBSERVATION_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_WET_OBSERVATION_REFRESH_STATUS_20260701.json"
)
LEDGER_WET_OBSERVATION_LANES = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_WET_OBSERVATION_REFRESH_PROMOTION_LANE_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "route/yield/detection readiness policy after wet observation intake;"
    "promotion blocker prioritization"
)
BLOCKED_USE = (
    "route_score;winner;JRC;yield;detection_probability;wet_pass_probability;"
    "clogging_rate;time_to_clog;recovery;production ingestion"
)

SOURCE_FILES = {
    "integrated_promotion_ledger_wet_observation_status": LEDGER_WET_OBSERVATION_STATUS,
    "integrated_promotion_ledger_wet_observation_lanes": LEDGER_WET_OBSERVATION_LANES,
    "route_yield_detection_policy_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_route_yield_detection_policy.py",
    "route_yield_detection_policy_tests": PROJECT_ROOT
    / "tests/test_sidewall_route_yield_detection_policy.py",
    "route_yield_detection_policy_wet_observation_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_route_yield_detection_policy_wet_observation_refresh.py",
    "route_yield_detection_policy_wet_observation_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_route_yield_detection_policy_wet_observation_refresh.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_route_yield_detection_policy.py",
    "tests/test_sidewall_route_yield_detection_policy.py",
    "tools/audits/build_nodi_package_c_sidewall_route_yield_detection_policy_wet_observation_refresh.py",
    "tests/test_nodi_package_c_sidewall_route_yield_detection_policy_wet_observation_refresh.py",
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
        description=(
            "Build sidewall route/yield/detection policy from the wet observation "
            "integrated ledger refresh."
        )
    )
    parser.add_argument(
        "--confirm-sidewall-route-yield-detection-policy-wet-observation-refresh",
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
            "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_WET_OBSERVATION_REFRESH_"
        )
        or path
        == "reports/545_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_WET_OBSERVATION_REFRESH_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "route_policy_wet_observation_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_WET_OBSERVATION_REFRESH_"
        ) or path == (
            "reports/545_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_"
            "WET_OBSERVATION_REFRESH_20260701.md"
        ):
            classification = "route_policy_wet_observation_output"
            release_decision = "included_or_rewritten_by_route_policy_wet_observation"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_route_policy_wet_observation_refresh"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_route_policy_wet_observation_not_source_locked"
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
        "policy_rows": payload["policy_rows"],
        "blocker_rows": payload["blocker_rows"],
        "promotion_update_rows": payload["promotion_update_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    ledger_status = load_json(LEDGER_WET_OBSERVATION_STATUS)
    policy_rows, blocker_rows = build_route_yield_detection_policy_rows(
        read_csv_rows(LEDGER_WET_OBSERVATION_LANES)
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
    selected_input_blockers = sum(
        row["evidence_lane"] == "selected_annulus_detection_context"
        and row["blocker_status"] == ROUTE_INPUT_READY_BLOCKER_STATUS
        for row in blocker_dicts
    )
    status_counts = {
        "selected_panel_rows": _count_policy_status(
            policy_dicts,
            "selected_annulus_policy_status",
            "ready_selected_annulus_event_panel_input_not_probability",
        ),
        "detector_panel_rows": _count_policy_status(
            policy_dicts,
            "detector_response_policy_status",
            "not_ready_detector_response_panel_candidate_needs_sidewall_calibration",
        ),
        "blank_panel_rows": _count_policy_status(
            policy_dicts,
            "blank_false_positive_policy_status",
            "not_ready_blank_guard_panel_bound_needs_sidewall_specific_transfer",
        ),
        "wet_intake_rows": _count_policy_status(
            policy_dicts,
            "wet_surface_policy_status",
            "not_ready_wet_observation_intake_ready_no_observations",
        ),
    }
    not_ready_rows = sum(
        row["route_policy_status"] == ROUTE_POLICY_NOT_READY_STATUS for row in policy_dicts
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and ledger_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_WET_OBSERVATION_REFRESH_READY_PREFLIGHT_ONLY"
        and len(policy_dicts) == 2
        and len(blocker_dicts) == 2 * len(REQUIRED_LANES)
        and len(promotion_updates) == 1
        and not_ready_rows == 2
        and selected_input_blockers == 2
        and all(count == 2 for count in status_counts.values())
        and all(row["route_score_allowed"] is False for row in policy_dicts)
        and all(row["yield_allowed"] is False for row in policy_dicts)
        and all(row["detection_probability_allowed"] is False for row in policy_dicts)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_wet_observation_ledger_disposition": ledger_status.get("disposition", ""),
        "policy_rows": len(policy_dicts),
        "blocker_rows": len(blocker_dicts),
        "required_lanes_per_route": len(REQUIRED_LANES),
        "promotion_update_rows": len(promotion_updates),
        "not_ready_policy_rows": not_ready_rows,
        "selected_annulus_input_ready_blocker_rows": selected_input_blockers,
        "selected_annulus_panel_policy_rows": status_counts["selected_panel_rows"],
        "detector_panel_policy_rows": status_counts["detector_panel_rows"],
        "blank_panel_policy_rows": status_counts["blank_panel_rows"],
        "wet_observation_intake_policy_rows": status_counts["wet_intake_rows"],
        "primary_next_execution_blocks": ";".join(
            sorted({row["primary_next_execution_block"] for row in policy_dicts})
        ),
        "route_score_allowed_rows": sum(row["route_score_allowed"] for row in policy_dicts),
        "winner_allowed_rows": sum(row["winner_allowed"] for row in policy_dicts),
        "yield_allowed_rows": sum(row["yield_allowed"] for row in policy_dicts),
        "detection_probability_allowed_rows": sum(
            row["detection_probability_allowed"] for row in policy_dicts
        ),
        "wet_pass_probability_allowed_rows": sum(
            row["wet_pass_probability_allowed"] for row in policy_dicts
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


def _count_policy_status(rows: list[dict[str, Any]], field: str, status: str) -> int:
    return sum(row.get(field) == status for row in rows)


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
        "selected annulus route input ready": (
            summary["selected_annulus_input_ready_blocker_rows"] == 2
        ),
        "selected panel recognized": summary["selected_annulus_panel_policy_rows"] == 2,
        "detector panel recognized": summary["detector_panel_policy_rows"] == 2,
        "blank panel recognized": summary["blank_panel_policy_rows"] == 2,
        "wet intake recognized": summary["wet_observation_intake_policy_rows"] == 2,
        "primary block current": (
            summary["primary_next_execution_blocks"]
            == "sidewall_detector_blank_transfer_validation"
        ),
        "route score blocked": summary["route_score_allowed_rows"] == 0,
        "winner blocked": summary["winner_allowed_rows"] == 0,
        "yield blocked": summary["yield_allowed_rows"] == 0,
        "detection blocked": summary["detection_probability_allowed_rows"] == 0,
        "wet pass blocked": summary["wet_pass_probability_allowed_rows"] == 0,
    }
    for update in payload["promotion_update_rows"]:
        checks[f"update not final {update['target_ledger_lane']}"] = (
            update["target_claim_current"] == "false"
            and "route_score" in update["blocked_promotion"]
            and "yield" in update["blocked_promotion"]
            and "detection_probability" in update["blocked_promotion"]
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    csv_payloads = {
        f"{PREFIX}_POLICY_ROWS_20260701.csv": payload["policy_rows"],
        f"{PREFIX}_BLOCKER_ROWS_20260701.csv": payload["blocker_rows"],
        f"{PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv": payload[
            "promotion_update_rows"
        ],
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
        / "545_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_WET_OBSERVATION_REFRESH_20260701.md"
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
            "# NODI Package C Sidewall Route/Yield/Detection Policy Wet Observation Refresh",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Policy rows: `{s['policy_rows']}`.",
            f"- Blocker rows: `{s['blocker_rows']}`.",
            f"- Selected-annulus input-ready blockers: `{s['selected_annulus_input_ready_blocker_rows']}`.",
            f"- Primary next execution block: `{s['primary_next_execution_blocks']}`.",
            "- Route score, winner, yield, detection probability, and wet pass probability remain blocked.",
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
                "policy_impact": "route_policy_wet_observation_refresh_not_claim",
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
    if not args.confirm_sidewall_route_yield_detection_policy_wet_observation_refresh:
        parser.error(
            "--confirm-sidewall-route-yield-detection-policy-wet-observation-refresh is required"
        )
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_WET_OBSERVATION_REFRESH")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
