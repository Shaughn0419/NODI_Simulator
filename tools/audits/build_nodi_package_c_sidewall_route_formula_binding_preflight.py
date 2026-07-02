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
from nodi_simulator.sidewall_route_formula_binding_preflight import (  # noqa: E402
    SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_CLAIM_BOUNDARY,
    SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_STATUS,
    build_route_formula_binding_preflight,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_PREFLIGHT_READY_QCH_READY_DETECTOR_WET_BLOCKED"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_PREFLIGHT_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_CLAIM_BOUNDARY

QCH_DELTA_ROWS = OUTPUT_DIR / (
    "NODI_PACKAGE_C_SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_"
    "ROUTE_EVIDENCE_DELTA_ROWS_20260701.csv"
)
QCH_INTEGRATION_STATUS = OUTPUT_DIR / (
    "NODI_PACKAGE_C_SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_STATUS_20260701.json"
)
ROUTE_CANDIDATE_ROWS = OUTPUT_DIR / (
    "NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_ROUTE_CANDIDATE_ROWS_20260701.csv"
)
ROUTE_CANDIDATE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_STATUS_20260701.json"
DETECTOR_WET_CLOSURE_ROWS = OUTPUT_DIR / (
    "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_CLOSURE_ROWS_20260701.csv"
)
DETECTOR_WET_CLOSURE_STATUS = OUTPUT_DIR / (
    "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_STATUS_20260701.json"
)
DETECTOR_EXECUTION_STATUS = OUTPUT_DIR / (
    "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_STATUS_20260701.json"
)
WET_EXECUTION_STATUS = OUTPUT_DIR / (
    "NODI_PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_STATUS_20260701.json"
)
DETECTOR_VALIDATION_STATUS = OUTPUT_DIR / (
    "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_STATUS_20260701.json"
)
WET_VALIDATION_STATUS = OUTPUT_DIR / (
    "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_STATUS_20260701.json"
)

ALLOWED_USE = (
    "route formula input preflight;formal q_ch integration;detector/wet blocker localization"
)
BLOCKED_USE = (
    "route_score;winner;JRC;yield;detection_probability;wet_pass_probability;"
    "clogging_rate;time_to_clog;recovery;production ingestion"
)

SOURCE_FILES = {
    "qch_integration_status": QCH_INTEGRATION_STATUS,
    "qch_route_evidence_delta_rows": QCH_DELTA_ROWS,
    "route_candidate_status": ROUTE_CANDIDATE_STATUS,
    "route_candidate_rows": ROUTE_CANDIDATE_ROWS,
    "detector_wet_closure_status": DETECTOR_WET_CLOSURE_STATUS,
    "detector_wet_closure_rows": DETECTOR_WET_CLOSURE_ROWS,
    "detector_execution_status": DETECTOR_EXECUTION_STATUS,
    "wet_execution_status": WET_EXECUTION_STATUS,
    "detector_validation_status": DETECTOR_VALIDATION_STATUS,
    "wet_validation_status": WET_VALIDATION_STATUS,
    "preflight_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_route_formula_binding_preflight.py",
    "preflight_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_route_formula_binding_preflight.py",
    "preflight_tests": PROJECT_ROOT
    / "tests/test_sidewall_route_formula_binding_preflight.py",
    "preflight_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_route_formula_binding_preflight.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_route_formula_binding_preflight.py",
    "tools/audits/build_nodi_package_c_sidewall_route_formula_binding_preflight.py",
    "tests/test_sidewall_route_formula_binding_preflight.py",
    "tests/test_nodi_package_c_sidewall_route_formula_binding_preflight.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build route formula binding preflight.")
    parser.add_argument("--confirm-sidewall-route-formula-binding-preflight", action="store_true")
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
    output_report = f"reports/567_{PREFIX}_20260701.md"
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "route_formula_preflight_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "route_formula_preflight_output"
            release_decision = "included_or_rewritten_by_preflight_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_route_formula_preflight"
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
                "preflight_rows": payload["preflight_rows"],
                "branch_rows": payload["branch_rows"],
                "guard_rows": payload["guard_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    qch_integration_status = load_status(QCH_INTEGRATION_STATUS)
    detector_execution_status = load_status(DETECTOR_EXECUTION_STATUS)
    wet_execution_status = load_status(WET_EXECUTION_STATUS)
    detector_validation_status = load_status(DETECTOR_VALIDATION_STATUS)
    wet_validation_status = load_status(WET_VALIDATION_STATUS)
    rows, branches, guards = build_route_formula_binding_preflight(
        qch_delta_rows=read_csv_rows(QCH_DELTA_ROWS),
        route_candidate_rows=read_csv_rows(ROUTE_CANDIDATE_ROWS),
        detector_wet_closure_rows=read_csv_rows(DETECTOR_WET_CLOSURE_ROWS),
    )
    preflight_rows = [row.to_dict() for row in rows]
    branch_rows = [row.to_dict() for row in branches]
    guard_rows = [row.to_dict() for row in guards]
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    status = (
        DISPOSITION
        if source_missing == 0
        and len(preflight_rows) == 2
        and len(branch_rows) == 12
        and len(guard_rows) == 5
        and int(qch_integration_status.get("accepted_exact_pressure_flow_rows", 0)) == 2
        and int(qch_integration_status.get("route_formula_qch_branch_ready_rows", 0)) == 2
        and sum(row["qch_branch_ready"] for row in preflight_rows) == 2
        and sum(row["detector_branch_ready"] for row in preflight_rows) == 0
        and sum(row["wet_branch_ready"] for row in preflight_rows) == 0
        and int(detector_execution_status.get("current_accepted_transfer_rows_total", 0)) == 0
        and int(wet_execution_status.get("current_accepted_observation_rows_total", 0)) == 0
        and sum(row["route_score_current"] for row in preflight_rows) == 0
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "preflight_status": SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "qch_integration_disposition": str(qch_integration_status.get("disposition", "")),
        "route_candidate_disposition": str(load_status(ROUTE_CANDIDATE_STATUS).get("disposition", "")),
        "detector_wet_closure_disposition": str(load_status(DETECTOR_WET_CLOSURE_STATUS).get("disposition", "")),
        "detector_execution_disposition": str(detector_execution_status.get("disposition", "")),
        "wet_execution_disposition": str(wet_execution_status.get("disposition", "")),
        "detector_validation_disposition": str(detector_validation_status.get("disposition", "")),
        "wet_validation_disposition": str(wet_validation_status.get("disposition", "")),
        "preflight_rows": len(preflight_rows),
        "branch_rows": len(branch_rows),
        "guard_rows": len(guard_rows),
        "source_566_accepted_exact_pressure_flow_rows": int(
            qch_integration_status.get("accepted_exact_pressure_flow_rows", 0)
        ),
        "source_566_route_formula_qch_branch_ready_rows": int(
            qch_integration_status.get("route_formula_qch_branch_ready_rows", 0)
        ),
        "qch_branch_ready_rows": sum(row["qch_branch_ready"] for row in preflight_rows),
        "exact_pressure_flow_ready_rows": sum(row["exact_pressure_flow_branch_ready"] for row in preflight_rows),
        "selected_annulus_ready_rows": sum(row["selected_annulus_context_ready"] for row in preflight_rows),
        "runtime_substep_guard_ready_rows": sum(row["runtime_substep_guard_ready"] for row in preflight_rows),
        "detector_validator_hardened_rows": sum(row["detector_validator_hardened"] for row in preflight_rows),
        "wet_validator_hardened_rows": sum(row["wet_validator_hardened"] for row in preflight_rows),
        "detector_hardening_fixture_rows": int(
            detector_validation_status.get("accepted_fixture_rows", 0)
        ),
        "wet_hardening_fixture_rows": int(
            wet_validation_status.get("accepted_fixture_rows", 0)
        ),
        "detector_execution_candidate_or_fixture_rows_total": int(
            detector_execution_status.get("candidate_or_fixture_rows_total", 0)
        ),
        "wet_execution_contract_or_fixture_rows_total": int(
            wet_execution_status.get("contract_or_fixture_rows_total", 0)
        ),
        "detector_accepted_transfer_rows_total": int(
            detector_execution_status.get("current_accepted_transfer_rows_total", 0)
        ),
        "wet_accepted_observation_rows_total": int(
            wet_execution_status.get("current_accepted_observation_rows_total", 0)
        ),
        "detector_branch_ready_rows": sum(row["detector_branch_ready"] for row in preflight_rows),
        "wet_branch_ready_rows": sum(row["wet_branch_ready"] for row in preflight_rows),
        "route_formula_claim_ready_rows": sum(
            row["route_formula_binding_status"]
            == "route_formula_inputs_ready_for_claim_activation_review"
            for row in preflight_rows
        ),
        "max_input_completeness_fraction": max(
            row["route_formula_input_completeness_fraction"] for row in preflight_rows
        ),
        "route_score_current": False,
        "winner_current": False,
        "JRC_current": False,
        "wet_pass_probability_current": False,
        "clogging_rate_current": False,
        "time_to_clog_current": False,
        "recovery_current": False,
        "yield_current": False,
        "detection_probability_current": False,
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
        "preflight_rows": preflight_rows,
        "branch_rows": branch_rows,
        "guard_rows": guard_rows,
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
    if summary["preflight_rows"] != 2:
        failures.append("expected_two_preflight_rows")
    if summary["qch_branch_ready_rows"] != 2:
        failures.append("qch_branch_not_ready_for_both_routes")
    if summary["source_566_accepted_exact_pressure_flow_rows"] != 2:
        failures.append("source_566_accepted_exact_pressure_flow_not_two")
    if summary["source_566_route_formula_qch_branch_ready_rows"] != 2:
        failures.append("source_566_qch_branch_ready_not_two")
    if summary["detector_branch_ready_rows"] != 0:
        failures.append("detector_branch_unexpectedly_ready")
    if summary["wet_branch_ready_rows"] != 0:
        failures.append("wet_branch_unexpectedly_ready")
    if summary["detector_accepted_transfer_rows_total"] != 0:
        failures.append("detector_fixture_or_context_promoted_to_accepted_transfer")
    if summary["wet_accepted_observation_rows_total"] != 0:
        failures.append("wet_fixture_or_context_promoted_to_accepted_observation")
    for key in (
        "route_score_current",
        "winner_current",
        "JRC_current",
        "wet_pass_probability_current",
        "clogging_rate_current",
        "time_to_clog_current",
        "recovery_current",
        "yield_current",
        "detection_probability_current",
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
        "preflight_rows": OUTPUT_DIR / f"{PREFIX}_PREFLIGHT_ROWS_20260701.csv",
        "branch_rows": OUTPUT_DIR / f"{PREFIX}_BRANCH_ROWS_20260701.csv",
        "guard_rows": OUTPUT_DIR / f"{PREFIX}_GUARD_ROWS_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"567_{PREFIX}_20260701.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    }
    write_json_atomic(outputs["status"], {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]}, sort_keys=True)
    write_csv_rows(outputs["preflight_rows"], payload["preflight_rows"])
    write_csv_rows(outputs["branch_rows"], payload["branch_rows"])
    write_csv_rows(outputs["guard_rows"], payload["guard_rows"])
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
            "# NODI Package C Sidewall Route Formula Binding Preflight",
            "",
            f"Disposition: `{summary['disposition']}`",
            f"Artifact ID: `{summary['artifact_id']}`",
            f"Claim boundary: `{summary['claim_boundary']}`",
            "",
            "## Current Formula Inputs",
            "",
            f"- q_ch branch ready rows: `{summary['qch_branch_ready_rows']}`",
            f"- exact pressure-flow ready rows: `{summary['exact_pressure_flow_ready_rows']}`",
            f"- selected-annulus ready rows: `{summary['selected_annulus_ready_rows']}`",
            f"- runtime/substep guard ready rows: `{summary['runtime_substep_guard_ready_rows']}`",
            f"- detector branch ready rows: `{summary['detector_branch_ready_rows']}`",
            f"- wet branch ready rows: `{summary['wet_branch_ready_rows']}`",
            f"- route formula claim-ready rows: `{summary['route_formula_claim_ready_rows']}`",
            "",
            "## Boundary",
            "",
            "This packet converts the 566 q_ch delta into a route-formula input table. It does not emit route_score, winner/JRC, yield, detection_probability, wet-pass, or production values.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_route_formula_binding_preflight:
        raise SystemExit("--confirm-sidewall-route-formula-binding-preflight is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
