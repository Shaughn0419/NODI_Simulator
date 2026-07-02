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
from nodi_simulator.sidewall_route_formula_activation_closure import (  # noqa: E402
    SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_CLAIM_BOUNDARY,
    SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_STATUS,
    build_route_formula_activation_closure,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_READY_CURRENTLY_BLOCKED"
READY_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_READY_FOR_CLAIM_REVIEW"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_CLAIM_BOUNDARY

BINDER_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_BINDER_ROWS_20260701.csv"
BINDER_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_STATUS_20260701.json"
ACTIVATION_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_ACTIVATION_ROWS_20260701.csv"
ACTIVATION_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_STATUS_20260701.json"

ALLOWED_USE = "route formula closure after q_ch and detector/wet activation"
BLOCKED_USE = "route_score;winner;JRC;yield;detection_probability;wet_pass_probability;production ingestion"

SOURCE_FILES = {
    "qch_detector_wet_binder_status": BINDER_STATUS,
    "qch_detector_wet_binder_rows": BINDER_ROWS,
    "detector_wet_activation_status": ACTIVATION_STATUS,
    "detector_wet_activation_rows": ACTIVATION_ROWS,
    "closure_source": PROJECT_ROOT / "nodi_simulator/sidewall_route_formula_activation_closure.py",
    "closure_builder": PROJECT_ROOT / "tools/audits/build_nodi_package_c_sidewall_route_formula_activation_closure.py",
    "closure_tests": PROJECT_ROOT / "tests/test_sidewall_route_formula_activation_closure.py",
    "closure_builder_tests": PROJECT_ROOT / "tests/test_nodi_package_c_sidewall_route_formula_activation_closure.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_route_formula_activation_closure.py",
    "tools/audits/build_nodi_package_c_sidewall_route_formula_activation_closure.py",
    "tests/test_sidewall_route_formula_activation_closure.py",
    "tests/test_nodi_package_c_sidewall_route_formula_activation_closure.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build route formula activation closure.")
    parser.add_argument("--confirm-sidewall-route-formula-activation-closure", action="store_true")
    return parser


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", "-c", f"safe.directory={PROJECT_ROOT.as_posix()}", *args], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True, encoding="utf-8")
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
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def source_lock_rows() -> list[dict[str, Any]]:
    rows = []
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
    output_report = f"reports/570_{PREFIX}_20260701.md"
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "route_formula_activation_closure_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "route_formula_activation_closure_output"
            release_decision = "included_or_rewritten_by_closure_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_route_formula_activation_closure"
        rows.append({"path": path, "git_status": line[:2], "classification": classification, "release_decision": release_decision})
    return rows


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps({"closure_rows": payload["closure_rows"]}, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    closure_rows = [
        row.to_dict()
        for row in build_route_formula_activation_closure(
            qch_detector_wet_binder_rows=read_csv_rows(BINDER_ROWS),
            detector_wet_activation_rows=read_csv_rows(ACTIVATION_ROWS),
        )
    ]
    binder_status = load_status(BINDER_STATUS)
    activation_status = load_status(ACTIVATION_STATUS)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    ready_rows = sum(row["route_formula_ready_for_claim_review"] for row in closure_rows)
    disposition = READY_DISPOSITION if ready_rows == len(closure_rows) and closure_rows else DISPOSITION
    if (
        sum(row["exists"] != "true" for row in source_lock)
        or len(closure_rows) != 2
        or binder_status.get("disposition") != "NODI_PACKAGE_C_SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_READY"
        or activation_status.get("disposition") not in {
            "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_READY_NO_CURRENT_ACCEPTED_EVIDENCE",
            "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_ACCEPTED_INPUT_READY_FOR_FORMULA_REVIEW",
        }
    ):
        disposition = BLOCKED_DISPOSITION
    summary: dict[str, Any] = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "closure_status": SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_binder_disposition": str(binder_status.get("disposition", "")),
        "source_activation_disposition": str(activation_status.get("disposition", "")),
        "closure_rows": len(closure_rows),
        "route_formula_ready_for_claim_review_rows": ready_rows,
        "route_score_current": False,
        "winner_current": False,
        "JRC_current": False,
        "yield_current": False,
        "detection_probability_current": False,
        "wet_pass_probability_current": False,
        "production_ingestion_current": False,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": sum(row["exists"] != "true" for row in source_lock),
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(row["classification"] == "non_release_dirty_context" for row in dirty_context),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "closure_rows": closure_rows,
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
    if summary["closure_rows"] != 2:
        failures.append("expected_two_closure_rows")
    for key in ("route_score_current", "winner_current", "JRC_current", "yield_current", "detection_probability_current", "wet_pass_probability_current", "production_ingestion_current"):
        if summary[key] is not False:
            failures.append(f"{key}_unexpectedly_true")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json",
        "closure_rows": OUTPUT_DIR / f"{PREFIX}_CLOSURE_ROWS_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"570_{PREFIX}_20260701.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    }
    write_json_atomic(outputs["status"], {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]}, sort_keys=True)
    write_csv_rows(outputs["closure_rows"], payload["closure_rows"])
    write_csv_rows(outputs["source_lock"], payload["source_lock_rows"])
    write_csv_rows(outputs["dirty_context"], payload["dirty_context_rows"])
    write_json_atomic(outputs["report_json"], payload, sort_keys=True)
    outputs["master_report"].write_text(render_markdown(payload), encoding="utf-8")
    write_csv_rows(outputs["manifest"], manifest_rows(outputs))
    return list(outputs.values())


def manifest_rows(outputs: dict[str, Path]) -> list[dict[str, Any]]:
    return [{"artifact_id": artifact_id, "path": display_path(path), "sha256": SELF_MANIFEST_SHA256 if artifact_id == "manifest" else sha256_file(path), "allowed_use": ALLOWED_USE, "blocked_use": BLOCKED_USE, "claim_boundary": CLAIM_BOUNDARY} for artifact_id, path in outputs.items()]


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join([
        "# NODI Package C Sidewall Route Formula Activation Closure",
        "",
        f"Disposition: `{summary['disposition']}`",
        f"Artifact ID: `{summary['artifact_id']}`",
        f"Claim boundary: `{summary['claim_boundary']}`",
        "",
        f"Route formula ready rows: `{summary['route_formula_ready_for_claim_review_rows']}`",
        "",
        "This closure joins the canonical q_ch/detector/wet blocker board with the detector/wet activation runner. It does not emit route_score, winner, yield, detection_probability, or production claims.",
        "",
    ])


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_route_formula_activation_closure:
        raise SystemExit("--confirm-sidewall-route-formula-activation-closure is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
