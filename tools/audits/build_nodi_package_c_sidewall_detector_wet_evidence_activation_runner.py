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
from nodi_simulator.sidewall_detector_wet_evidence_activation_runner import (  # noqa: E402
    SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_CLAIM_BOUNDARY,
    SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_STATUS,
    build_detector_wet_evidence_activation_runner,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_READY_NO_CURRENT_ACCEPTED_EVIDENCE"
ACCEPTED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_ACCEPTED_INPUT_READY_FOR_FORMULA_REVIEW"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_CLAIM_BOUNDARY

DETECTOR_PANEL_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_ROUTE_EVIDENCE_MATRIX_ROWS_20260701.csv"
WET_CONTRACT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_CONTRACT_ROWS_20260701.csv"
DETECTOR_INPUT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INPUT_ROWS_20260701.csv"
WET_INPUT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INPUT_ROWS_20260701.csv"
BINDER_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_STATUS_20260701.json"

ALLOWED_USE = (
    "combined detector/wet accepted-evidence activation runner;formula blocker release input"
)
BLOCKED_USE = (
    "route_score;winner;JRC;yield;detection_probability;wet_pass_probability;"
    "clogging_rate;time_to_clog;recovery;production ingestion"
)

SOURCE_FILES = {
    "detector_panel_rows": DETECTOR_PANEL_ROWS,
    "wet_contract_rows": WET_CONTRACT_ROWS,
    "route_qch_detector_wet_binder_status": BINDER_STATUS,
    "activation_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_detector_wet_evidence_activation_runner.py",
    "activation_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_detector_wet_evidence_activation_runner.py",
    "activation_tests": PROJECT_ROOT
    / "tests/test_sidewall_detector_wet_evidence_activation_runner.py",
    "activation_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_detector_wet_evidence_activation_runner.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_detector_wet_evidence_activation_runner.py",
    "tools/audits/build_nodi_package_c_sidewall_detector_wet_evidence_activation_runner.py",
    "tests/test_sidewall_detector_wet_evidence_activation_runner.py",
    "tests/test_nodi_package_c_sidewall_detector_wet_evidence_activation_runner.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build combined detector/wet evidence activation runner.")
    parser.add_argument("--confirm-sidewall-detector-wet-evidence-activation-runner", action="store_true")
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
    for source_id, path in {
        "optional_detector_transfer_input_rows": DETECTOR_INPUT_ROWS,
        "optional_wet_observation_input_rows": WET_INPUT_ROWS,
    }.items():
        if path.exists():
            rows.append(
                {
                    "source_id": source_id,
                    "path": display_path(path),
                    "exists": "true",
                    "sha256": sha256_file(path),
                    "allowed_use": ALLOWED_USE,
                    "blocked_use": BLOCKED_USE,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
    return rows


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    output_prefix = f"reports/joint_interface_20260701/{PREFIX}_"
    output_report = f"reports/569_{PREFIX}_20260701.md"
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "detector_wet_activation_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "detector_wet_activation_output"
            release_decision = "included_or_rewritten_by_activation_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_detector_wet_activation"
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
                "activation_rows": payload["activation_rows"],
                "input_contract_rows": payload["input_contract_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    rows, contracts = build_detector_wet_evidence_activation_runner(
        detector_panel_matrix_rows=read_csv_rows(DETECTOR_PANEL_ROWS),
        wet_contract_rows=read_csv_rows(WET_CONTRACT_ROWS),
        detector_transfer_input_rows=read_csv_rows(DETECTOR_INPUT_ROWS) if DETECTOR_INPUT_ROWS.exists() else [],
        wet_observation_input_rows=read_csv_rows(WET_INPUT_ROWS) if WET_INPUT_ROWS.exists() else [],
        detector_input_present=DETECTOR_INPUT_ROWS.exists(),
        wet_input_present=WET_INPUT_ROWS.exists(),
        detector_input_path=display_path(DETECTOR_INPUT_ROWS),
        wet_input_path=display_path(WET_INPUT_ROWS),
    )
    activation_rows = [row.to_dict() for row in rows]
    input_contract_rows = [row.to_dict() for row in contracts]
    binder_status = load_status(BINDER_STATUS)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    combined_ready = sum(row["combined_detector_wet_ready_for_formula"] for row in activation_rows)
    current_accepted_detector = sum(row["detector_accepted_transfer_rows"] for row in activation_rows)
    current_accepted_wet = sum(row["wet_accepted_endpoint_count"] for row in activation_rows)
    disposition = (
        ACCEPTED_DISPOSITION
        if combined_ready == len(activation_rows) and activation_rows
        else DISPOSITION
    )
    if (
        source_missing
        or len(activation_rows) != 2
        or len(input_contract_rows) != 2
        or binder_status.get("disposition")
        != "NODI_PACKAGE_C_SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_READY"
        or any(row["route_score_current"] for row in activation_rows)
    ):
        disposition = BLOCKED_DISPOSITION
    summary: dict[str, Any] = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "activation_status": SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_binder_disposition": str(binder_status.get("disposition", "")),
        "detector_input_present": DETECTOR_INPUT_ROWS.exists(),
        "wet_input_present": WET_INPUT_ROWS.exists(),
        "activation_rows": len(activation_rows),
        "input_contract_rows": len(input_contract_rows),
        "combined_detector_wet_ready_rows": combined_ready,
        "detector_branch_ready_rows": sum(row["detector_branch_ready_for_formula"] for row in activation_rows),
        "wet_branch_ready_rows": sum(row["wet_branch_ready_for_formula"] for row in activation_rows),
        "detector_accepted_transfer_rows_total": current_accepted_detector,
        "wet_accepted_endpoint_count_total": current_accepted_wet,
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
        "activation_rows": activation_rows,
        "input_contract_rows": input_contract_rows,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    summary = payload["summary"]
    if summary["disposition"] not in {DISPOSITION, ACCEPTED_DISPOSITION}:
        failures.append("disposition_not_ready")
    if summary["activation_rows"] != 2:
        failures.append("expected_two_route_activation_rows")
    if summary["input_contract_rows"] != 2:
        failures.append("expected_two_input_contract_rows")
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
        "activation_rows": OUTPUT_DIR / f"{PREFIX}_ACTIVATION_ROWS_20260701.csv",
        "input_contract_rows": OUTPUT_DIR / f"{PREFIX}_INPUT_CONTRACT_ROWS_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"569_{PREFIX}_20260701.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    }
    write_json_atomic(outputs["status"], {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]}, sort_keys=True)
    write_csv_rows(outputs["activation_rows"], payload["activation_rows"])
    write_csv_rows(outputs["input_contract_rows"], payload["input_contract_rows"])
    write_csv_rows(outputs["source_lock"], payload["source_lock_rows"])
    write_csv_rows(outputs["dirty_context"], payload["dirty_context_rows"])
    write_json_atomic(outputs["report_json"], payload, sort_keys=True)
    outputs["master_report"].write_text(render_markdown(payload), encoding="utf-8")
    write_csv_rows(outputs["manifest"], manifest_rows(outputs))
    return list(outputs.values())


def manifest_rows(outputs: dict[str, Path]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_id": artifact_id,
            "path": display_path(path),
            "sha256": SELF_MANIFEST_SHA256 if artifact_id == "manifest" else sha256_file(path),
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for artifact_id, path in outputs.items()
    ]


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Sidewall Detector Wet Evidence Activation Runner",
            "",
            f"Disposition: `{summary['disposition']}`",
            f"Artifact ID: `{summary['artifact_id']}`",
            f"Claim boundary: `{summary['claim_boundary']}`",
            "",
            "## Current Inputs",
            "",
            f"- detector input present: `{summary['detector_input_present']}`",
            f"- wet input present: `{summary['wet_input_present']}`",
            f"- combined ready rows: `{summary['combined_detector_wet_ready_rows']}`",
            f"- detector accepted transfer rows: `{summary['detector_accepted_transfer_rows_total']}`",
            f"- wet accepted endpoint rows: `{summary['wet_accepted_endpoint_count_total']}`",
            "",
            "The runner is now wired for accepted detector/wet evidence activation. It still emits no route_score, yield, detection probability, wet-pass, or production claim.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_detector_wet_evidence_activation_runner:
        raise SystemExit("--confirm-sidewall-detector-wet-evidence-activation-runner is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
