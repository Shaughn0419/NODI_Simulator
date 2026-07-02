#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)
from nodi_simulator.sidewall_route_qch_detector_wet_blocker_binder import (  # noqa: E402
    SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_CLAIM_BOUNDARY,
    SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_STATUS,
    build_route_qch_detector_wet_blocker_binder,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_READY"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_CLAIM_BOUNDARY

PREFLIGHT_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_STATUS_20260701.json"
PREFLIGHT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_PREFLIGHT_ROWS_20260701.csv"
QCH_INTEGRATION_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_STATUS_20260701.json"
DETECTOR_EXECUTION_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_STATUS_20260701.json"
WET_EXECUTION_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_STATUS_20260701.json"
OLD_READINESS_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_STATUS_20260701.json"
OLD_POLICY_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_WET_OBSERVATION_REFRESH_STATUS_20260701.json"
OLD_ASSEMBLY_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_DETECTOR_BLANK_TRANSFER_REFRESH_STATUS_20260701.json"
OLD_FORMAL_QCH_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE_STATUS_20260701.json"

ALLOWED_USE = (
    "canonical current route q_ch/detector/wet blocker board;source supersession pointer;"
    "next route/yield/detection execution planning"
)
BLOCKED_USE = (
    "route_score;winner;JRC;yield;detection_probability;wet_pass_probability;"
    "clogging_rate;time_to_clog;recovery;production ingestion"
)

SOURCE_FILES = {
    "preflight_status": PREFLIGHT_STATUS,
    "preflight_rows": PREFLIGHT_ROWS,
    "qch_integration_status": QCH_INTEGRATION_STATUS,
    "detector_execution_status": DETECTOR_EXECUTION_STATUS,
    "wet_execution_status": WET_EXECUTION_STATUS,
    "old_readiness_status": OLD_READINESS_STATUS,
    "old_policy_status": OLD_POLICY_STATUS,
    "old_assembly_status": OLD_ASSEMBLY_STATUS,
    "old_formal_qch_status": OLD_FORMAL_QCH_STATUS,
    "binder_source": PROJECT_ROOT / "nodi_simulator/sidewall_route_qch_detector_wet_blocker_binder.py",
    "binder_builder": PROJECT_ROOT / "tools/audits/build_nodi_package_c_sidewall_route_qch_detector_wet_blocker_binder.py",
    "binder_tests": PROJECT_ROOT / "tests/test_sidewall_route_qch_detector_wet_blocker_binder.py",
    "binder_builder_tests": PROJECT_ROOT / "tests/test_nodi_package_c_sidewall_route_qch_detector_wet_blocker_binder.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_route_qch_detector_wet_blocker_binder.py",
    "tools/audits/build_nodi_package_c_sidewall_route_qch_detector_wet_blocker_binder.py",
    "tests/test_sidewall_route_qch_detector_wet_blocker_binder.py",
    "tests/test_nodi_package_c_sidewall_route_qch_detector_wet_blocker_binder.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build canonical route q_ch/detector/wet blocker binder.")
    parser.add_argument("--confirm-sidewall-route-qch-detector-wet-blocker-binder", action="store_true")
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
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def load_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def source_statuses() -> dict[str, dict[str, Any]]:
    return {
        "build_nodi_package_c_sidewall_integrated_promotion_ledger_formal_qch_refresh.py": load_status(OLD_FORMAL_QCH_STATUS),
        "build_nodi_package_c_sidewall_route_yield_detection_policy.py": load_status(OLD_POLICY_STATUS),
        "build_nodi_package_c_sidewall_route_yield_detection_policy_wet_observation_refresh.py": load_status(OLD_POLICY_STATUS),
        "build_nodi_package_c_sidewall_route_yield_detection_assembly_v2.py": load_status(OLD_ASSEMBLY_STATUS),
        "build_nodi_package_c_sidewall_route_yield_detection_readiness_board.py": load_status(OLD_READINESS_STATUS),
    }


def source_lock_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_id": source_id,
                "path": display_path(path) if exists else str(path),
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    output_prefix = f"reports/joint_interface_20260701/{PREFIX}_"
    output_report = f"reports/568_{PREFIX}_20260701.md"
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "route_qch_detector_wet_binder_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "route_qch_detector_wet_binder_output"
            release_decision = "included_or_rewritten_by_binder_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_route_qch_detector_wet_binder"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "binder_rows": payload["binder_rows"],
                "supersession_rows": payload["supersession_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    rows, supersession = build_route_qch_detector_wet_blocker_binder(
        preflight_rows=read_csv_rows(PREFLIGHT_ROWS),
        source_statuses=source_statuses(),
    )
    binder_rows = [row.to_dict() for row in rows]
    supersession_rows = [row.to_dict() for row in supersession]
    preflight_status = load_status(PREFLIGHT_STATUS)
    qch_status = load_status(QCH_INTEGRATION_STATUS)
    detector_status = load_status(DETECTOR_EXECUTION_STATUS)
    wet_status = load_status(WET_EXECUTION_STATUS)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    status = (
        DISPOSITION
        if source_missing == 0
        and len(binder_rows) == 2
        and len(supersession_rows) == 5
        and int(qch_status.get("accepted_exact_pressure_flow_rows", 0)) == 2
        and int(qch_status.get("route_formula_qch_branch_ready_rows", 0)) == 2
        and int(preflight_status.get("qch_branch_ready_rows", 0)) == 2
        and int(preflight_status.get("detector_branch_ready_rows", 0)) == 0
        and int(preflight_status.get("wet_branch_ready_rows", 0)) == 0
        and int(detector_status.get("current_accepted_transfer_rows_total", 0)) == 0
        and int(wet_status.get("current_accepted_observation_rows_total", 0)) == 0
        and sum(row["route_score_current"] for row in binder_rows) == 0
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "binder_status": SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "preflight_disposition": str(preflight_status.get("disposition", "")),
        "qch_integration_disposition": str(qch_status.get("disposition", "")),
        "detector_execution_disposition": str(detector_status.get("disposition", "")),
        "wet_execution_disposition": str(wet_status.get("disposition", "")),
        "binder_rows": len(binder_rows),
        "supersession_rows": len(supersession_rows),
        "rectangle_rows": sum(row["route_geometry_family"] == "ideal_rectangle" for row in binder_rows),
        "trapezoid_rows": sum(row["route_geometry_family"] == "trapezoid_tapered_sidewalls" for row in binder_rows),
        "qch_ready_rows": sum(row["qch_status"] == "formal_qch_input_ready_not_route_score" for row in binder_rows),
        "detector_blocker_rows": sum(row["detector_blank_status"] == "blocker_not_accepted_evidence" for row in binder_rows),
        "wet_blocker_rows": sum(row["wet_observation_status"] == "blocker_not_accepted_evidence" for row in binder_rows),
        "route_formula_input_ready_count_total": sum(row["route_formula_input_ready_count"] for row in binder_rows),
        "route_formula_required_input_count_total": sum(row["route_formula_required_input_count"] for row in binder_rows),
        "detector_accepted_transfer_rows_total": int(detector_status.get("current_accepted_transfer_rows_total", 0)),
        "wet_accepted_observation_rows_total": int(wet_status.get("current_accepted_observation_rows_total", 0)),
        "route_score_current": False,
        "winner_current": False,
        "JRC_current": False,
        "yield_current": False,
        "detection_probability_current": False,
        "wet_pass_probability_current": False,
        "production_ingestion_current": False,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context"
            for row in dirty_context
        ),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "binder_rows": binder_rows,
        "supersession_rows": supersession_rows,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    summary = payload["summary"]
    if summary["disposition"] != DISPOSITION:
        failures.append("disposition_not_ready")
    if summary["binder_rows"] != 2:
        failures.append("expected_two_route_rows")
    if summary["rectangle_rows"] != 1 or summary["trapezoid_rows"] != 1:
        failures.append("rectangle_trapezoid_parallelism_missing")
    if summary["qch_ready_rows"] != 2:
        failures.append("qch_not_ready_for_both_routes")
    if summary["detector_blocker_rows"] != 2:
        failures.append("detector_blocker_not_preserved")
    if summary["wet_blocker_rows"] != 2:
        failures.append("wet_blocker_not_preserved")
    if summary["detector_accepted_transfer_rows_total"] != 0:
        failures.append("detector_fixture_or_context_promoted_to_accepted_transfer")
    if summary["wet_accepted_observation_rows_total"] != 0:
        failures.append("wet_fixture_or_context_promoted_to_accepted_observation")
    for key in (
        "route_score_current",
        "winner_current",
        "JRC_current",
        "yield_current",
        "detection_probability_current",
        "wet_pass_probability_current",
        "production_ingestion_current",
    ):
        if summary[key] is not False:
            failures.append(f"{key}_unexpectedly_true")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json",
        "binder_rows": OUTPUT_DIR / f"{PREFIX}_BINDER_ROWS_20260701.csv",
        "supersession_rows": OUTPUT_DIR / f"{PREFIX}_SUPERSESSION_ROWS_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"568_{PREFIX}_20260701.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    }
    write_json_atomic(outputs["status"], {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]}, sort_keys=True)
    write_csv_rows(outputs["binder_rows"], payload["binder_rows"])
    write_csv_rows(outputs["supersession_rows"], payload["supersession_rows"])
    write_csv_rows(outputs["source_lock"], payload["source_lock_rows"])
    write_csv_rows(outputs["dirty_context"], payload["dirty_context_rows"])
    write_json_atomic(outputs["report_json"], payload, sort_keys=True)
    outputs["master_report"].write_text(render_markdown(payload), encoding="utf-8")
    write_csv_rows(outputs["manifest"], manifest_rows(outputs))
    return list(outputs.values())


def manifest_rows(outputs: dict[str, Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_id, path in outputs.items():
        rows.append(
            {
                "artifact_id": artifact_id,
                "path": display_path(path),
                "sha256": SELF_MANIFEST_SHA256 if artifact_id == "manifest" else sha256_file(path),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Sidewall Route QCH Detector Wet Blocker Binder",
            "",
            f"Disposition: `{summary['disposition']}`",
            f"Artifact ID: `{summary['artifact_id']}`",
            f"Claim boundary: `{summary['claim_boundary']}`",
            "",
            "## Canonical State",
            "",
            f"- q_ch ready rows: `{summary['qch_ready_rows']}`",
            f"- detector blocker rows: `{summary['detector_blocker_rows']}`",
            f"- wet blocker rows: `{summary['wet_blocker_rows']}`",
            f"- rectangle rows: `{summary['rectangle_rows']}`",
            f"- trapezoid rows: `{summary['trapezoid_rows']}`",
            f"- superseded source rows: `{summary['supersession_rows']}`",
            "",
            "This is the current board for the route/yield/detection lane: q_ch is ready as an input; detector/blank and wet accepted evidence remain the execution blockers.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_route_qch_detector_wet_blocker_binder:
        raise SystemExit("--confirm-sidewall-route-qch-detector-wet-blocker-binder is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
