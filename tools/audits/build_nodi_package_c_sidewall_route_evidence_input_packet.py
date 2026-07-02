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
from nodi_simulator.sidewall_route_evidence_input_packet import (  # noqa: E402
    SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_CLAIM_BOUNDARY,
    SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_VERSION,
    build_route_evidence_input_packet,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_READY_AWAITING_INPUT_ROWS"
READY_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_READY_FOR_ROUTE_FORMULA_REVIEW"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_CLAIM_BOUNDARY

DETECTOR_INTAKE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_STATUS_20260701.json"
DETECTOR_TEMPLATE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_TEMPLATE_ROWS_20260701.csv"
DETECTOR_TARGET_INPUT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INPUT_ROWS_20260701.csv"
WET_INTAKE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_STATUS_20260701.json"
WET_TEMPLATE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_OBSERVATION_TEMPLATE_ROWS_20260701.csv"
WET_TARGET_INPUT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INPUT_ROWS_20260701.csv"
WET_SOURCE_MANIFEST = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_SOURCE_MANIFEST_20260701.csv"
ACTIVATION_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_STATUS_20260701.json"
CLOSURE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_STATUS_20260701.json"
CLOSURE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_CLOSURE_ROWS_20260701.csv"
CLAIM_VALUE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_STATUS_20260701.json"
CLAIM_VALUE_SOURCE_MANIFEST = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_SOURCE_MANIFEST_20260701.csv"
DETECTION_VALUE_TEMPLATE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_DETECTION_VALUE_TEMPLATE_ROWS_20260701.csv"
YIELD_VALUE_TEMPLATE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_YIELD_VALUE_TEMPLATE_ROWS_20260701.csv"
DETECTION_VALUE_TARGET_INPUT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTION_PROBABILITY_VALUE_INPUT_ROWS_20260701.csv"
YIELD_VALUE_TARGET_INPUT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_YIELD_WET_VALUE_INPUT_ROWS_20260701.csv"
REAL_EVIDENCE_WORKSPACE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_REAL_EVIDENCE_INPUT_WORKSPACE_STATUS_20260701.json"

ALLOWED_USE = "single entry packet for detector/wet/value evidence input and full route decision rerun chain"
BLOCKED_USE = (
    "template-as-evidence;route_score;winner;JRC;yield;detection_probability;"
    "wet_pass_probability from templates or unaccepted rows;production ingestion"
)

SOURCE_FILES = {
    "detector_intake_status": DETECTOR_INTAKE_STATUS,
    "detector_template_rows": DETECTOR_TEMPLATE_ROWS,
    "wet_intake_status": WET_INTAKE_STATUS,
    "wet_template_rows": WET_TEMPLATE_ROWS,
    "activation_status": ACTIVATION_STATUS,
    "closure_status": CLOSURE_STATUS,
    "closure_rows": CLOSURE_ROWS,
    "claim_value_status": CLAIM_VALUE_STATUS,
    "real_evidence_workspace_status": REAL_EVIDENCE_WORKSPACE_STATUS,
    "detection_value_template_rows": DETECTION_VALUE_TEMPLATE_ROWS,
    "yield_value_template_rows": YIELD_VALUE_TEMPLATE_ROWS,
    "claim_value_manifest_import_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_yield_detection_claim_value_manifest_import.py",
    "claim_value_manifest_import_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_yield_detection_claim_value_manifest_import.py",
    "claim_value_manifest_import_tests": PROJECT_ROOT
    / "tests/test_sidewall_yield_detection_claim_value_manifest_import.py",
    "claim_value_manifest_import_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_yield_detection_claim_value_manifest_import.py",
    "input_packet_source": PROJECT_ROOT / "nodi_simulator/sidewall_route_evidence_input_packet.py",
    "input_packet_builder": PROJECT_ROOT / "tools/audits/build_nodi_package_c_sidewall_route_evidence_input_packet.py",
    "input_packet_tests": PROJECT_ROOT / "tests/test_sidewall_route_evidence_input_packet.py",
    "input_packet_builder_tests": PROJECT_ROOT / "tests/test_nodi_package_c_sidewall_route_evidence_input_packet.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_route_evidence_input_packet.py",
    "tools/audits/build_nodi_package_c_sidewall_route_evidence_input_packet.py",
    "tests/test_sidewall_route_evidence_input_packet.py",
    "tests/test_nodi_package_c_sidewall_route_evidence_input_packet.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build route evidence input packet.")
    parser.add_argument("--confirm-sidewall-route-evidence-input-packet", action="store_true")
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


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    output_prefix = f"reports/joint_interface_20260701/{PREFIX}_"
    output_report = f"reports/571_{PREFIX}_20260701.md"
    target_input_paths = {
        display_path(DETECTOR_TARGET_INPUT_ROWS),
        display_path(WET_TARGET_INPUT_ROWS),
        display_path(DETECTION_VALUE_TARGET_INPUT_ROWS),
        display_path(YIELD_VALUE_TARGET_INPUT_ROWS),
    }
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "route_evidence_input_packet_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path in target_input_paths:
            classification = "route_evidence_target_input_rows"
            release_decision = "source_locked_header_only_or_real_input"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "route_evidence_input_packet_output"
            release_decision = "included_or_rewritten_by_input_packet_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_route_evidence_input_packet"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


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
        "target_detector_input_rows": DETECTOR_TARGET_INPUT_ROWS,
        "target_wet_input_rows": WET_TARGET_INPUT_ROWS,
        "target_detection_value_input_rows": DETECTION_VALUE_TARGET_INPUT_ROWS,
        "target_yield_value_input_rows": YIELD_VALUE_TARGET_INPUT_ROWS,
        "optional_wet_source_manifest": WET_SOURCE_MANIFEST,
        "optional_claim_value_source_manifest": CLAIM_VALUE_SOURCE_MANIFEST,
    }.items():
        rows.append(
            {
                "source_id": source_id,
                "path": display_path(path),
                "exists": str(path.exists()).lower(),
                "sha256": sha256_file(path) if path.exists() else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "input_rows": payload["input_rows"],
                "command_rows": payload["command_rows"],
                "formula_rows": payload["formula_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    detector_summary = load_status(DETECTOR_INTAKE_STATUS)
    wet_summary = load_status(WET_INTAKE_STATUS)
    activation_summary = load_status(ACTIVATION_STATUS)
    closure_summary = load_status(CLOSURE_STATUS)
    claim_value_summary = load_status(CLAIM_VALUE_STATUS)
    workspace_summary = load_status(REAL_EVIDENCE_WORKSPACE_STATUS)
    input_rows, command_rows, formula_rows = build_route_evidence_input_packet(
        detector_intake_summary=detector_summary,
        wet_intake_summary=wet_summary,
        activation_summary=activation_summary,
        claim_value_summary=claim_value_summary,
        closure_rows=read_csv_rows(CLOSURE_ROWS),
        detector_template_path=display_path(DETECTOR_TEMPLATE_ROWS),
        wet_template_path=display_path(WET_TEMPLATE_ROWS),
        detection_value_template_path=display_path(DETECTION_VALUE_TEMPLATE_ROWS),
        yield_value_template_path=display_path(YIELD_VALUE_TEMPLATE_ROWS),
        detector_target_input_path=display_path(DETECTOR_TARGET_INPUT_ROWS),
        wet_target_input_path=display_path(WET_TARGET_INPUT_ROWS),
        detection_value_target_input_path=display_path(DETECTION_VALUE_TARGET_INPUT_ROWS),
        yield_value_target_input_path=display_path(YIELD_VALUE_TARGET_INPUT_ROWS),
    )
    input_dicts = [row.to_dict() for row in input_rows]
    command_dicts = [row.to_dict() for row in command_rows]
    formula_dicts = [row.to_dict() for row in formula_rows]
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    required_source_missing = sum(
        row["exists"] != "true"
        for row in source_lock
        if not str(row["source_id"]).startswith(("target_", "optional_"))
    )
    route_formula_ready = sum(
        row["route_formula_ready_for_claim_review"] for row in formula_dicts
    )
    disposition = READY_DISPOSITION if route_formula_ready == len(formula_dicts) and formula_dicts else DISPOSITION
    if (
        required_source_missing
        or len(input_dicts) != 4
        or len(command_dicts) != 11
        or len(formula_dicts) != 2
        or any(row["route_score_current"] for row in formula_dicts)
    ):
        disposition = BLOCKED_DISPOSITION
    missing_current_acceptance_branches = [
        row["input_branch"] for row in input_dicts if row["current_accepted_rows"] == 0
    ]
    summary: dict[str, Any] = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "input_packet_version": SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_VERSION,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_detector_intake_disposition": str(detector_summary.get("disposition", "")),
        "source_wet_intake_disposition": str(wet_summary.get("disposition", "")),
        "source_activation_disposition": str(activation_summary.get("disposition", "")),
        "source_closure_disposition": str(closure_summary.get("disposition", "")),
        "source_claim_value_disposition": str(claim_value_summary.get("disposition", "")),
        "source_real_evidence_workspace_disposition": str(
            workspace_summary.get("disposition", "")
        ),
        "workspace_target_header_only_rows": int(
            workspace_summary.get("target_header_only_rows", 0)
        ),
        "workspace_target_header_refreshed_now_rows": int(
            workspace_summary.get("target_header_refreshed_now_rows", 0)
        ),
        "workspace_target_real_data_rows_total": int(
            workspace_summary.get("target_real_data_rows_total", 0)
        ),
        "detector_input_present": bool(activation_summary.get("detector_input_present")),
        "wet_input_present": bool(activation_summary.get("wet_input_present")),
        "detection_value_input_present": bool(claim_value_summary.get("detection_input_present")),
        "yield_value_input_present": bool(claim_value_summary.get("yield_input_present")),
        "detector_template_rows": int(detector_summary.get("template_rows", 0)),
        "wet_template_rows": int(wet_summary.get("template_rows", 0)),
        "detection_value_template_rows": int(claim_value_summary.get("detection_template_rows", 0)),
        "yield_value_template_rows": int(claim_value_summary.get("yield_template_rows", 0)),
        "detector_accepted_transfer_rows_total": int(activation_summary.get("detector_accepted_transfer_rows_total", 0)),
        "wet_accepted_endpoint_count_total": int(activation_summary.get("wet_accepted_endpoint_count_total", 0)),
        "detection_probability_current_rows": int(claim_value_summary.get("detection_probability_current_rows", 0)),
        "yield_current_rows": int(claim_value_summary.get("yield_current_rows", 0)),
        "wet_pass_probability_current_rows": int(claim_value_summary.get("wet_pass_probability_current_rows", 0)),
        "input_rows": len(input_dicts),
        "input_branches_missing_current_acceptance": ";".join(
            missing_current_acceptance_branches
        ),
        "command_rows": len(command_dicts),
        "route_formula_rows": len(formula_dicts),
        "route_formula_ready_for_claim_review_rows": route_formula_ready,
        "route_score_current": False,
        "winner_current": False,
        "JRC_current": False,
        "yield_current": bool(claim_value_summary.get("yield_current_rows")),
        "detection_probability_current": bool(claim_value_summary.get("detection_probability_current_rows")),
        "wet_pass_probability_current": bool(claim_value_summary.get("wet_pass_probability_current_rows")),
        "production_ingestion_current": False,
        "source_lock_rows": len(source_lock),
        "required_source_missing_rows": required_source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context"
            for row in dirty_context
        ),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "next_high_leverage_step": (
            "populate source manifests/importer inputs for "
            + ", ".join(missing_current_acceptance_branches)
            + ", then rerun the eleven-step command chain"
            if missing_current_acceptance_branches
            else "all evidence input branches have accepted rows; rerun the eleven-step command chain"
        ),
    }
    payload = {
        "summary": summary,
        "input_rows": input_dicts,
        "command_rows": command_dicts,
        "formula_rows": formula_dicts,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    if summary["disposition"] not in {DISPOSITION, READY_DISPOSITION}:
        failures.append("disposition_not_ready")
    if summary["required_source_missing_rows"] != 0:
        failures.append("required_source_missing")
    if summary["input_rows"] != 4:
        failures.append("expected_four_input_rows")
    if summary["command_rows"] != 11:
        failures.append("expected_eleven_command_rows")
    if summary["route_formula_rows"] != 2:
        failures.append("expected_two_formula_rows")
    if summary["route_score_current"]:
        failures.append("claim_current_unexpectedly_true")
    if (
        summary["detector_template_rows"] != 2
        or summary["wet_template_rows"] != 14
        or summary["detection_value_template_rows"] != 2
        or summary["yield_value_template_rows"] != 2
    ):
        failures.append("unexpected_template_row_counts")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json",
        "input_rows": OUTPUT_DIR / f"{PREFIX}_INPUT_ROWS_20260701.csv",
        "command_rows": OUTPUT_DIR / f"{PREFIX}_COMMAND_ROWS_20260701.csv",
        "formula_rows": OUTPUT_DIR / f"{PREFIX}_FORMULA_ROWS_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"571_{PREFIX}_20260701.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    }
    write_json_atomic(outputs["status"], {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]}, sort_keys=True)
    write_csv_rows(outputs["input_rows"], payload["input_rows"])
    write_csv_rows(outputs["command_rows"], payload["command_rows"])
    write_csv_rows(outputs["formula_rows"], payload["formula_rows"])
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
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Sidewall Route Evidence Input Packet",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Claim boundary: `{s['claim_boundary']}`",
            "",
            f"Detector template rows: `{s['detector_template_rows']}`; target input present: `{s['detector_input_present']}`.",
            f"Wet template rows: `{s['wet_template_rows']}`; target input present: `{s['wet_input_present']}`.",
            f"Detection-value template rows: `{s['detection_value_template_rows']}`; target input present: `{s['detection_value_input_present']}`.",
            f"Yield/wet-value template rows: `{s['yield_value_template_rows']}`; target input present: `{s['yield_value_input_present']}`.",
            f"Workspace header-only target rows: `{s['workspace_target_header_only_rows']}`; refreshed now: `{s['workspace_target_header_refreshed_now_rows']}`.",
            f"Detector accepted transfer rows: `{s['detector_accepted_transfer_rows_total']}`.",
            f"Missing current-acceptance branches: `{s['input_branches_missing_current_acceptance']}`.",
            f"Route formula ready rows: `{s['route_formula_ready_for_claim_review_rows']}`.",
            f"Detection probability current rows: `{s['detection_probability_current_rows']}`; yield current rows: `{s['yield_current_rows']}`; wet-pass current rows: `{s['wet_pass_probability_current_rows']}`.",
            "",
            "This packet is the single entry point for filling detector/blank transfer, wet/surface observation, detection-probability value, and yield/wet-pass value evidence, then rerunning the eleven-step chain through route decision readiness.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_route_evidence_input_packet:
        raise SystemExit("--confirm-sidewall-route-evidence-input-packet is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
