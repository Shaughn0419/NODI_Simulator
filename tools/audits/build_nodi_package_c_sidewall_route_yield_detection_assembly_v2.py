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
    DETECTOR_BLANK_TRANSFER_ACCEPTED_STATUS,
    WET_OBSERVATION_ACCEPTED_STATUS,
)
from nodi_simulator.sidewall_route_yield_detection_assembly import (  # noqa: E402
    ASSEMBLY_NOT_CLAIM_READY_STATUS,
    ASSEMBLY_ROUTE_POLICY_REVIEW_READY_STATUS,
    SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_CLAIM_BOUNDARY,
    build_route_yield_detection_assembly,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_V2"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_V2_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_V2_READY_NOT_CLAIM_READY"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_V2_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_CLAIM_BOUNDARY

WET_OBSERVATION_LEDGER_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_WET_SURFACE_REFRESH_STATUS_20260701.json"
)
WET_OBSERVATION_LEDGER_LANES = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_WET_SURFACE_REFRESH_PROMOTION_LANE_ROWS_20260701.csv"
)
ROUTE_POLICY_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_STATUS_20260701.json"
)
ROUTE_POLICY_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_POLICY_ROWS_20260701.csv"
)
ROUTE_POLICY_BLOCKERS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_BLOCKER_ROWS_20260701.csv"
)
ACTIVATION_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_ACTIVATION_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "route/yield/detection assembly coordination;next executable branch selection;"
    "rectangle and sidewall route comparison context"
)
BLOCKED_USE = (
    "route_score;winner;JRC;yield;detection_probability;wet_pass_probability;"
    "clogging_rate;time_to_clog;recovery;production ingestion"
)

SOURCE_FILES = {
    "wet_observation_integrated_ledger_status": WET_OBSERVATION_LEDGER_STATUS,
    "wet_observation_integrated_ledger_lanes": WET_OBSERVATION_LEDGER_LANES,
    "route_policy_wet_observation_status": ROUTE_POLICY_STATUS,
    "route_policy_wet_observation_rows": ROUTE_POLICY_ROWS,
    "route_policy_wet_observation_blockers": ROUTE_POLICY_BLOCKERS,
    "detector_wet_activation_rows": ACTIVATION_ROWS,
    "route_yield_detection_assembly_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_route_yield_detection_assembly.py",
    "route_yield_detection_assembly_tests": PROJECT_ROOT
    / "tests/test_sidewall_route_yield_detection_assembly.py",
    "route_yield_detection_assembly_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_route_yield_detection_assembly_v2.py",
    "route_yield_detection_assembly_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_route_yield_detection_assembly_v2.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_route_yield_detection_assembly.py",
    "tests/test_sidewall_route_yield_detection_assembly.py",
    "tools/audits/build_nodi_package_c_sidewall_route_yield_detection_assembly_v2.py",
    "tests/test_nodi_package_c_sidewall_route_yield_detection_assembly_v2.py",
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
        description="Build Package C sidewall route/yield/detection assembly v2 rows."
    )
    parser.add_argument(
        "--confirm-sidewall-route-yield-detection-assembly-v2",
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
            "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_V2_"
        )
        or path
        == "reports/546_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_V2_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "route_yield_detection_assembly_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_V2_"
        ) or path == (
            "reports/546_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_V2_20260701.md"
        ):
            classification = "route_yield_detection_assembly_output"
            release_decision = "included_or_rewritten_by_route_yield_detection_assembly"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_route_yield_detection_assembly"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_route_yield_detection_assembly_not_source_locked"
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
        "assembly_rows": payload["assembly_rows"],
        "branch_rows": payload["branch_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    wet_ledger_status = load_json(WET_OBSERVATION_LEDGER_STATUS)
    policy_status = load_json(ROUTE_POLICY_STATUS)
    activation_rows = read_csv_rows(ACTIVATION_ROWS)
    assembly_rows, branch_rows = build_route_yield_detection_assembly(
        _activation_refreshed_lane_rows(
            read_csv_rows(WET_OBSERVATION_LEDGER_LANES),
            activation_rows,
        ),
        read_csv_rows(ROUTE_POLICY_ROWS),
        read_csv_rows(ROUTE_POLICY_BLOCKERS),
    )
    assembly_dicts = [row.to_dict() for row in assembly_rows]
    branch_dicts = [row.to_dict() for row in branch_rows]
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    geometry_families = sorted({row["route_geometry_family"] for row in assembly_dicts})
    branch_names = sorted({row["branch_name"] for row in branch_dicts})
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and wet_ledger_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_WET_SURFACE_REFRESH_READY_PREFLIGHT_ONLY"
        and policy_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_READY_NOT_CLAIM_READY"
        and len(assembly_dicts) == 2
        and len(branch_dicts) == 8
        and geometry_families == ["ideal_rectangle", "trapezoid_tapered_sidewalls"]
        and set(branch_names)
        == {
            "detection_probability_calibration",
            "route_candidate_assembly",
            "sidewall_detector_blank_transfer_validation",
            "wet_observation_bundle_intake",
        }
        and all(
            row["assembly_status"]
            in {
                ASSEMBLY_NOT_CLAIM_READY_STATUS,
                ASSEMBLY_ROUTE_POLICY_REVIEW_READY_STATUS,
            }
            for row in assembly_dicts
        )
        and all(row["route_score_allowed"] is False for row in assembly_dicts)
        and all(row["yield_allowed"] is False for row in assembly_dicts)
        and all(row["detection_probability_allowed"] is False for row in assembly_dicts)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_wet_observation_ledger_disposition": wet_ledger_status.get("disposition", ""),
        "source_route_policy_disposition": policy_status.get("disposition", ""),
        "assembly_rows": len(assembly_dicts),
        "branch_rows": len(branch_dicts),
        "route_geometry_families": ";".join(geometry_families),
        "branch_names": ";".join(branch_names),
        "assembly_not_claim_ready_rows": sum(
            row["assembly_status"] == ASSEMBLY_NOT_CLAIM_READY_STATUS
            for row in assembly_dicts
        ),
        "assembly_policy_review_ready_rows": sum(
            row["assembly_status"] == ASSEMBLY_ROUTE_POLICY_REVIEW_READY_STATUS
            for row in assembly_dicts
        ),
        "detector_wet_activation_ready_rows": sum(
            str(row.get("route_formula_blocker_status", ""))
            == "detector_wet_branches_ready_for_formula_review"
            for row in activation_rows
        ),
        "ready_input_lane_count_total": sum(
            row["ready_input_lane_count"] for row in assembly_dicts
        ),
        "candidate_context_lane_count_total": sum(
            row["candidate_context_lane_count"] for row in assembly_dicts
        ),
        "missing_or_blocked_lane_count_total": sum(
            row["missing_or_blocked_lane_count"] for row in assembly_dicts
        ),
        "next_executable_branches": ";".join(
            sorted({row["next_executable_branch"] for row in assembly_dicts})
        ),
        "route_score_allowed_rows": sum(row["route_score_allowed"] for row in assembly_dicts),
        "winner_allowed_rows": sum(row["winner_allowed"] for row in assembly_dicts),
        "yield_allowed_rows": sum(row["yield_allowed"] for row in assembly_dicts),
        "detection_probability_allowed_rows": sum(
            row["detection_probability_allowed"] for row in assembly_dicts
        ),
        "wet_pass_probability_allowed_rows": sum(
            row["wet_pass_probability_allowed"] for row in assembly_dicts
        ),
        "implementation_can_start_branch_rows": sum(
            row["implementation_can_start"] for row in branch_dicts
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
        "assembly_rows": assembly_dicts,
        "branch_rows": branch_dicts,
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
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "two assembly rows": summary["assembly_rows"] == 2,
        "eight branch rows": summary["branch_rows"] == 8,
        "rectangle and trapezoid present": (
            summary["route_geometry_families"] == "ideal_rectangle;trapezoid_tapered_sidewalls"
        ),
        "next branch current": (
            summary["next_executable_branches"]
            in {
                "sidewall_detector_blank_transfer_validation",
                "detector_blank_calibration",
                "route_formula_policy_review",
            }
        ),
        "route score blocked": summary["route_score_allowed_rows"] == 0,
        "winner blocked": summary["winner_allowed_rows"] == 0,
        "yield blocked": summary["yield_allowed_rows"] == 0,
        "detection blocked": summary["detection_probability_allowed_rows"] == 0,
        "wet pass blocked": summary["wet_pass_probability_allowed_rows"] == 0,
    }
    for row in payload["branch_rows"]:
        checks[f"branch target false {row['branch_row_id']}"] = (
            row["target_claim_current"] is False
            and "not_route_score" in row["claim_boundary"]
            and "not_yield" in row["claim_boundary"]
            and "not_detection_probability" in row["claim_boundary"]
        )
    return [label for label, ok in checks.items() if not ok]


def _activation_refreshed_lane_rows(
    base_rows: list[dict[str, str]],
    activation_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows = [dict(row) for row in base_rows]
    activation_by_route = {
        str(row.get("route_candidate_id", "")): row for row in activation_rows
    }
    for row in rows:
        route_id = str(row.get("route_candidate_id", ""))
        activation = activation_by_route.get(route_id, {})
        lane = str(row.get("evidence_lane", ""))
        detector_ready = (
            str(activation.get("detector_branch_ready_for_formula", "")).lower()
            == "true"
        )
        wet_ready = (
            str(activation.get("wet_branch_ready_for_formula", "")).lower()
            == "true"
        )
        if detector_ready and lane in {
            "detector_response_bridge",
            "blank_false_positive_trace",
        }:
            row["current_status"] = DETECTOR_BLANK_TRANSFER_ACCEPTED_STATUS
        if wet_ready and lane == "wet_wall_interaction":
            row["current_status"] = WET_OBSERVATION_ACCEPTED_STATUS
    return rows


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    csv_payloads = {
        f"{PREFIX}_ASSEMBLY_ROWS_20260701.csv": payload["assembly_rows"],
        f"{PREFIX}_BRANCH_ROWS_20260701.csv": payload["branch_rows"],
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
        / "546_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_V2_20260701.md"
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
            "# NODI Package C Sidewall Route/Yield/Detection Assembly V2",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Assembly rows: `{s['assembly_rows']}`.",
            f"- Branch rows: `{s['branch_rows']}`.",
            f"- Route geometry families: `{s['route_geometry_families']}`.",
            f"- Next executable branch: `{s['next_executable_branches']}`.",
            "- This assembly keeps rectangle and trapezoid routes side by side.",
            "- Route score, winner/JRC, yield, wet pass probability, and detection probability remain false.",
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
                "policy_impact": "route_yield_detection_assembly_not_claim",
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
    if not args.confirm_sidewall_route_yield_detection_assembly_v2:
        parser.error("--confirm-sidewall-route-yield-detection-assembly-v2 is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_V2")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
