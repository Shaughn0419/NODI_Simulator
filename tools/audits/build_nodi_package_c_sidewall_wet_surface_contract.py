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
from nodi_simulator.sidewall_wet_surface_contract import (  # noqa: E402
    SIDEWALL_WET_SURFACE_CONTRACT_CLAIM_BOUNDARY,
    WET_SURFACE_ENDPOINTS,
    build_wet_surface_contract_rows,
    wet_surface_promotion_update_rows,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_READY_CONTRACT_ONLY"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_WET_SURFACE_CONTRACT_CLAIM_BOUNDARY

LEDGER_DETECTOR_BLANK_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_REFRESH_STATUS_20260701.json"
)
LEDGER_DETECTOR_BLANK_LANES = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_REFRESH_PROMOTION_LANE_ROWS_20260701.csv"
)
WET_CONTEXT_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_STATUS_20260701.json"
)
WET_CONTEXT_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_EVIDENCE_CONTEXT_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "wet/surface evidence contract;promotion preflight input for wet_wall_interaction lane"
)
BLOCKED_USE = (
    "wet_pass_probability;clogging_rate;time_to_clog;recovery;yield;"
    "route_score;winner;JRC;detection_probability;production ingestion"
)

SOURCE_FILES = {
    "integrated_promotion_ledger_detector_blank_status": LEDGER_DETECTOR_BLANK_STATUS,
    "integrated_promotion_ledger_detector_blank_lanes": LEDGER_DETECTOR_BLANK_LANES,
    "wet_optical_detection_context_status": WET_CONTEXT_STATUS,
    "wet_optical_detection_context_rows": WET_CONTEXT_ROWS,
    "wet_surface_contract_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_wet_surface_contract.py",
    "wet_surface_contract_tests": PROJECT_ROOT / "tests/test_sidewall_wet_surface_contract.py",
    "wet_surface_contract_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_wet_surface_contract.py",
    "wet_surface_contract_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_wet_surface_contract.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_wet_surface_contract.py",
    "tests/test_sidewall_wet_surface_contract.py",
    "tools/audits/build_nodi_package_c_sidewall_wet_surface_contract.py",
    "tests/test_nodi_package_c_sidewall_wet_surface_contract.py",
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
        description="Build sidewall wet/surface evidence contract rows."
    )
    parser.add_argument("--confirm-sidewall-wet-surface-contract", action="store_true")
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
            "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_"
        )
        or path
        == "reports/537_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "wet_surface_contract_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_"
        ) or path == (
            "reports/537_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_20260701.md"
        ):
            classification = "wet_surface_contract_output"
            release_decision = "included_or_rewritten_by_wet_surface_contract"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_wet_surface_contract"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_wet_surface_contract_not_source_locked"
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
    ledger_status = load_json(LEDGER_DETECTOR_BLANK_STATUS)
    wet_context_status = load_json(WET_CONTEXT_STATUS)
    contract_rows = build_wet_surface_contract_rows(
        promotion_lane_rows=read_csv_rows(LEDGER_DETECTOR_BLANK_LANES),
        wet_context_rows=read_csv_rows(WET_CONTEXT_ROWS),
    )
    contract_dicts = [row.to_dict() for row in contract_rows]
    promotion_updates = wet_surface_promotion_update_rows(contract_rows)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    route_count = len({row.route_candidate_id for row in contract_rows})
    endpoint_count = len({row.endpoint_id for row in contract_rows})
    target_false = sum(not row.target_claim_current for row in contract_rows)
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and ledger_status.get("disposition")
        == (
            "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_REFRESH_"
            "READY_PREFLIGHT_ONLY"
        )
        and wet_context_status.get("disposition")
        == "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_READY_NOT_FINAL"
        and route_count == 2
        and endpoint_count == len(WET_SURFACE_ENDPOINTS)
        and len(contract_rows) == route_count * endpoint_count
        and len(promotion_updates) == 1
        and target_false == len(contract_rows)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_ledger_detector_blank_disposition": ledger_status.get("disposition", ""),
        "source_wet_context_disposition": wet_context_status.get("disposition", ""),
        "contract_rows": len(contract_rows),
        "route_candidate_rows": route_count,
        "endpoint_rows_per_route": endpoint_count,
        "promotion_update_rows": len(promotion_updates),
        "target_claim_false_rows": target_false,
        "wet_surface_contract_status": "wet_surface_contract_defined_no_wet_validation",
        "wet_pass_probability_current": False,
        "clogging_rate_current": False,
        "time_to_clog_current": False,
        "recovery_current": False,
        "yield_current": False,
        "detection_probability_current": False,
        "route_score_current": False,
        "winner_current": False,
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
        "contract_rows": contract_dicts,
        "promotion_update_rows": promotion_updates,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "contract_rows": payload["contract_rows"],
        "promotion_update_rows": payload["promotion_update_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "two routes": summary["route_candidate_rows"] == 2,
        "all endpoints": summary["endpoint_rows_per_route"] == len(WET_SURFACE_ENDPOINTS),
        "fourteen rows": summary["contract_rows"] == 2 * len(WET_SURFACE_ENDPOINTS),
        "one promotion update": summary["promotion_update_rows"] == 1,
        "all target false": summary["target_claim_false_rows"] == summary["contract_rows"],
        "wet pass false": summary["wet_pass_probability_current"] is False,
        "clogging false": summary["clogging_rate_current"] is False,
        "recovery false": summary["recovery_current"] is False,
        "yield false": summary["yield_current"] is False,
        "route false": summary["route_score_current"] is False,
        "detection false": summary["detection_probability_current"] is False,
    }
    for row in payload["contract_rows"]:
        checks[f"contract no claim {row['contract_id']}"] = (
            row["target_claim_current"] is False
            and row["not_wet_pass_probability"] is True
            and row["not_clogging_rate"] is True
            and row["not_recovery"] is True
            and row["not_yield"] is True
            and row["not_detection_probability"] is True
            and row["required_fields"]
            and row["minimum_controls"]
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    contract_path = OUTPUT_DIR / f"{PREFIX}_CONTRACT_ROWS_20260701.csv"
    write_csv_rows(contract_path, payload["contract_rows"])
    paths.append(contract_path)

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
        / "537_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_20260701.md"
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
            "# NODI Package C Sidewall Wet/Surface Evidence Contract",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Contract rows: `{s['contract_rows']}`.",
            f"- Route candidates: `{s['route_candidate_rows']}`.",
            f"- Endpoints per route: `{s['endpoint_rows_per_route']}`.",
            "- Covered endpoints: material/surface identity, EV sample panel, adhesion/wall loss, clogging time series, recovery flush, wet pass probability, and yield bridge.",
            "- This packet defines required wet/surface evidence and emits a wet_wall_interaction promotion update.",
            "- Wet pass probability, clogging rate, time-to-clog, recovery, yield, route score, winner/JRC, and detection probability remain false.",
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
                "policy_impact": "wet_surface_contract_not_claim_promotion",
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
    if not args.confirm_sidewall_wet_surface_contract:
        parser.error("--confirm-sidewall-wet-surface-contract is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
