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
from nodi_simulator.sidewall_route_yield_detection_readiness_board import (  # noqa: E402
    MISSING_CLAIM_EVIDENCE,
    READINESS_BOARD_STATUS,
    READY_ROUTE_INPUT,
    SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_CLAIM_BOUNDARY,
    build_route_yield_detection_readiness_board,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_READY_INPUTS_NOT_CLAIMS"
)
BLOCKED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_FAIL_CLOSED"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_CLAIM_BOUNDARY

FORMAL_QCH_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE_STATUS_20260701.json"
)
FORMAL_QCH_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE_BRIDGE_ROWS_20260701.csv"
)
ASSEMBLY_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_DETECTOR_BLANK_TRANSFER_REFRESH_STATUS_20260701.json"
)
ASSEMBLY_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_DETECTOR_BLANK_TRANSFER_REFRESH_ASSEMBLY_ROWS_20260701.csv"
)
POLICY_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_WET_OBSERVATION_REFRESH_STATUS_20260701.json"
)
POLICY_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_WET_OBSERVATION_REFRESH_POLICY_ROWS_20260701.csv"
)
POLICY_BLOCKER_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_WET_OBSERVATION_REFRESH_BLOCKER_ROWS_20260701.csv"
)
TRANSFER_HARDENING_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_STATUS_20260701.json"
)
TRANSFER_CURRENT_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_CURRENT_INTAKE_AUDIT_ROWS_20260701.csv"
)
WET_HARDENING_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_STATUS_20260701.json"
)
WET_CURRENT_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_CURRENT_INTAKE_AUDIT_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "route/yield/detection route-level readiness board;next execution prioritization;"
    "formal q_ch, detector/blank, and wet evidence reconciliation"
)
BLOCKED_USE = (
    "route_score;winner;JRC;yield;detection_probability;wet_pass_probability;"
    "clogging_rate;time_to_clog;recovery;q_ch_weighting;production ingestion"
)

SOURCE_FILES = {
    "formal_qch_bridge_status": FORMAL_QCH_STATUS,
    "formal_qch_bridge_rows": FORMAL_QCH_ROWS,
    "route_yield_detection_assembly_status": ASSEMBLY_STATUS,
    "route_yield_detection_assembly_rows": ASSEMBLY_ROWS,
    "route_yield_detection_policy_status": POLICY_STATUS,
    "route_yield_detection_policy_rows": POLICY_ROWS,
    "route_yield_detection_policy_blocker_rows": POLICY_BLOCKER_ROWS,
    "detector_blank_transfer_hardening_status": TRANSFER_HARDENING_STATUS,
    "detector_blank_transfer_current_rows": TRANSFER_CURRENT_ROWS,
    "wet_surface_observation_hardening_status": WET_HARDENING_STATUS,
    "wet_surface_observation_current_rows": WET_CURRENT_ROWS,
    "readiness_board_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_route_yield_detection_readiness_board.py",
    "readiness_board_tests": PROJECT_ROOT
    / "tests/test_sidewall_route_yield_detection_readiness_board.py",
    "readiness_board_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_route_yield_detection_readiness_board.py",
    "readiness_board_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_route_yield_detection_readiness_board.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_route_yield_detection_readiness_board.py",
    "tests/test_sidewall_route_yield_detection_readiness_board.py",
    "tools/audits/build_nodi_package_c_sidewall_route_yield_detection_readiness_board.py",
    "tests/test_nodi_package_c_sidewall_route_yield_detection_readiness_board.py",
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
        description="Build sidewall route/yield/detection readiness board."
    )
    parser.add_argument(
        "--confirm-sidewall-route-yield-detection-readiness-board",
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
            "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_"
        )
        or path
        == "reports/554_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_20260701.md"
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
            classification = "readiness_board_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_"
        ) or path == (
            "reports/554_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_20260701.md"
        ):
            classification = "readiness_board_output"
            release_decision = "included_or_rewritten_by_readiness_board"
        elif source_locked_path(path):
            classification = "source_locked_upstream_dirty_context"
            release_decision = "source_locked_current_workspace_not_in_commit_scope"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_readiness_board"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_readiness_board_not_source_locked"
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
        "board_rows": payload["board_rows"],
        "blocker_rows": payload["blocker_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    formal_status = load_json(FORMAL_QCH_STATUS)
    assembly_status = load_json(ASSEMBLY_STATUS)
    policy_status = load_json(POLICY_STATUS)
    transfer_status = load_json(TRANSFER_HARDENING_STATUS)
    wet_status = load_json(WET_HARDENING_STATUS)
    board_rows, blocker_rows = build_route_yield_detection_readiness_board(
        formal_qch_bridge_rows=read_csv_rows(FORMAL_QCH_ROWS),
        policy_rows=read_csv_rows(POLICY_ROWS),
        policy_blocker_rows=read_csv_rows(POLICY_BLOCKER_ROWS),
        assembly_rows=read_csv_rows(ASSEMBLY_ROWS),
        detector_transfer_audit_rows=read_csv_rows(TRANSFER_CURRENT_ROWS),
        wet_observation_audit_rows=read_csv_rows(WET_CURRENT_ROWS),
    )
    board_dicts = [row.to_dict() for row in board_rows]
    blocker_dicts = [row.to_dict() for row in blocker_rows]
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
        and formal_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE_READY_ROUTE_INPUT_NOT_SCORE"
        and assembly_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_DETECTOR_BLANK_TRANSFER_REFRESH_READY_NOT_CLAIM_READY"
        and policy_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_WET_OBSERVATION_REFRESH_READY_NOT_CLAIM_READY"
        and transfer_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_READY_NOT_PROBABILITY"
        and wet_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_READY_NOT_YIELD"
        and len(board_dicts) == 2
        and len(blocker_dicts) == 10
        and all(row["board_status"] == READINESS_BOARD_STATUS for row in board_dicts)
        and all(row["ready_route_input_count"] == 3 for row in board_dicts)
        and all(row["missing_claim_evidence_count"] == 2 for row in board_dicts)
        and all(row["primary_next_execution_block"] == "sidewall_detector_blank_transfer_validation" for row in board_dicts)
        and all(row["route_score_current"] is False for row in board_dicts)
        and all(row["yield_current"] is False for row in board_dicts)
        and all(row["detection_probability_current"] is False for row in board_dicts)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_formal_qch_disposition": formal_status.get("disposition", ""),
        "source_assembly_disposition": assembly_status.get("disposition", ""),
        "source_policy_disposition": policy_status.get("disposition", ""),
        "source_transfer_hardening_disposition": transfer_status.get("disposition", ""),
        "source_wet_hardening_disposition": wet_status.get("disposition", ""),
        "board_rows": len(board_dicts),
        "blocker_rows": len(blocker_dicts),
        "route_geometry_families": ";".join(
            sorted({row["route_geometry_family"] for row in board_dicts})
        ),
        "ready_route_input_count_total": sum(
            row["ready_route_input_count"] for row in board_dicts
        ),
        "missing_claim_evidence_count_total": sum(
            row["missing_claim_evidence_count"] for row in board_dicts
        ),
        "ready_blocker_rows": sum(
            row["readiness_class"] == READY_ROUTE_INPUT for row in blocker_dicts
        ),
        "missing_blocker_rows": sum(
            row["readiness_class"] == MISSING_CLAIM_EVIDENCE
            for row in blocker_dicts
        ),
        "primary_next_execution_blocks": ";".join(
            sorted({row["primary_next_execution_block"] for row in board_dicts})
        ),
        "secondary_next_execution_blocks": ";".join(
            sorted({row["secondary_next_execution_block"] for row in board_dicts})
        ),
        "route_score_current_rows": sum(row["route_score_current"] for row in board_dicts),
        "winner_current_rows": sum(row["winner_current"] for row in board_dicts),
        "yield_current_rows": sum(row["yield_current"] for row in board_dicts),
        "detection_probability_current_rows": sum(
            row["detection_probability_current"] for row in board_dicts
        ),
        "wet_pass_probability_current_rows": sum(
            row["wet_pass_probability_current"] for row in board_dicts
        ),
        "production_ingestion_current_rows": sum(
            row["production_ingestion_current"] for row in board_dicts
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
        "board_rows": board_dicts,
        "blocker_rows": blocker_dicts,
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
        "two board rows": s["board_rows"] == 2,
        "ten blocker rows": s["blocker_rows"] == 10,
        "rectangle and trapezoid": (
            s["route_geometry_families"] == "ideal_rectangle;trapezoid_tapered_sidewalls"
        ),
        "six ready inputs": s["ready_route_input_count_total"] == 6,
        "four missing claim blockers": s["missing_claim_evidence_count_total"] == 4,
        "six ready blocker rows": s["ready_blocker_rows"] == 6,
        "four missing blocker rows": s["missing_blocker_rows"] == 4,
        "primary branch": (
            s["primary_next_execution_blocks"]
            == "sidewall_detector_blank_transfer_validation"
        ),
        "secondary branch": s["secondary_next_execution_blocks"]
        == "wet_observation_bundle_intake",
        "route score false": s["route_score_current_rows"] == 0,
        "winner false": s["winner_current_rows"] == 0,
        "yield false": s["yield_current_rows"] == 0,
        "detection false": s["detection_probability_current_rows"] == 0,
        "wet pass false": s["wet_pass_probability_current_rows"] == 0,
        "production false": s["production_ingestion_current_rows"] == 0,
    }
    for row in payload["board_rows"]:
        checks[f"board row current false {row['board_row_id']}"] = (
            row["q_ch_m3_s"] > 0.0
            and row["qch_route_input_status"] == READY_ROUTE_INPUT
            and row["pressure_flow_route_input_status"] == READY_ROUTE_INPUT
            and row["selected_annulus_context_status"] == READY_ROUTE_INPUT
            and row["detector_blank_transfer_status"] == MISSING_CLAIM_EVIDENCE
            and row["wet_observation_status"] == MISSING_CLAIM_EVIDENCE
            and row["claim_boundary"] == CLAIM_BOUNDARY
        )
    for row in payload["blocker_rows"]:
        checks[f"blocker target false {row['blocker_row_id']}"] = (
            row["target_claim_current"] is False and row["claim_boundary"] == CLAIM_BOUNDARY
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    csv_payloads = {
        f"{PREFIX}_BOARD_ROWS_20260701.csv": payload["board_rows"],
        f"{PREFIX}_BLOCKER_ROWS_20260701.csv": payload["blocker_rows"],
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
        / "554_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_20260701.md"
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
            "# NODI Package C Sidewall Route/Yield/Detection Readiness Board",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Board rows: `{s['board_rows']}`.",
            f"- Route geometry families: `{s['route_geometry_families']}`.",
            f"- Ready route input lanes total: `{s['ready_route_input_count_total']}`.",
            f"- Missing claim-evidence lanes total: `{s['missing_claim_evidence_count_total']}`.",
            f"- Primary next execution block: `{s['primary_next_execution_blocks']}`.",
            f"- Secondary next execution block: `{s['secondary_next_execution_blocks']}`.",
            "- Formal q_ch, pressure-flow, and selected-annulus context are route inputs only.",
            "- Detector/blank transfer and wet/surface observations remain the current claim blockers.",
            "- Route score, winner/JRC, yield, detection probability, wet pass probability, and production ingestion remain false.",
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
                "policy_impact": "route_yield_detection_readiness_board_not_claim",
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
    if not args.confirm_sidewall_route_yield_detection_readiness_board:
        parser.error("--confirm-sidewall-route-yield-detection-readiness-board is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
