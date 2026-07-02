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
from nodi_simulator.sidewall_route_formula_review_dry_run import (  # noqa: E402
    SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_CLAIM_BOUNDARY,
    SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_VERSION,
    build_route_formula_review_dry_run,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_READY_WAITING_FOR_ACCEPTED_EVIDENCE"
READY_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_COMPONENT_VECTOR_READY_FOR_POLICY_REVIEW"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_CLAIM_BOUNDARY

INPUT_PACKET_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_STATUS_20260701.json"
INPUT_PACKET_FORMULA_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_FORMULA_ROWS_20260701.csv"
CLOSURE_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_STATUS_20260701.json"
CLOSURE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_CLOSURE_ROWS_20260701.csv"

ALLOWED_USE = "review-only route formula component dry run after q_ch and detector/wet activation closure"
BLOCKED_USE = "route_score;winner;JRC;yield;detection_probability;wet_pass_probability;production ingestion"

SOURCE_FILES = {
    "route_evidence_input_packet_status": INPUT_PACKET_STATUS,
    "route_evidence_input_packet_formula_rows": INPUT_PACKET_FORMULA_ROWS,
    "route_formula_activation_closure_status": CLOSURE_STATUS,
    "route_formula_activation_closure_rows": CLOSURE_ROWS,
    "dry_run_source": PROJECT_ROOT / "nodi_simulator/sidewall_route_formula_review_dry_run.py",
    "dry_run_builder": PROJECT_ROOT / "tools/audits/build_nodi_package_c_sidewall_route_formula_review_dry_run.py",
    "dry_run_tests": PROJECT_ROOT / "tests/test_sidewall_route_formula_review_dry_run.py",
    "dry_run_builder_tests": PROJECT_ROOT / "tests/test_nodi_package_c_sidewall_route_formula_review_dry_run.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_route_formula_review_dry_run.py",
    "tools/audits/build_nodi_package_c_sidewall_route_formula_review_dry_run.py",
    "tests/test_sidewall_route_formula_review_dry_run.py",
    "tests/test_nodi_package_c_sidewall_route_formula_review_dry_run.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build sidewall route formula dry-run packet.")
    parser.add_argument("--confirm-sidewall-route-formula-review-dry-run", action="store_true")
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
    output_report = f"reports/572_{PREFIX}_20260701.md"
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "route_formula_review_dry_run_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "route_formula_review_dry_run_output"
            release_decision = "included_or_rewritten_by_dry_run_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_route_formula_review_dry_run"
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
    return rows


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps({"dry_run_rows": payload["dry_run_rows"]}, sort_keys=True).encode(
            "utf-8"
        )
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    rows = [row.to_dict() for row in build_route_formula_review_dry_run(closure_rows=read_csv_rows(CLOSURE_ROWS))]
    input_status = load_status(INPUT_PACKET_STATUS)
    closure_status = load_status(CLOSURE_STATUS)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    ready_rows = sum(row["route_formula_ready_for_claim_review"] for row in rows)
    disposition = READY_DISPOSITION if ready_rows == len(rows) and rows else DISPOSITION
    if (
        source_missing
        or len(rows) != 2
        or any(row["route_score_current"] for row in rows)
        or any(row["yield_current"] for row in rows)
        or any(row["detection_probability_current"] for row in rows)
    ):
        disposition = BLOCKED_DISPOSITION
    summary: dict[str, Any] = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "dry_run_version": SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_VERSION,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_input_packet_disposition": str(input_status.get("disposition", "")),
        "source_closure_disposition": str(closure_status.get("disposition", "")),
        "dry_run_rows": len(rows),
        "route_formula_ready_for_claim_review_rows": ready_rows,
        "component_vector_ready_rows": sum(
            row["route_formula_review_dry_run_status"]
            == "route_formula_component_vector_ready_for_policy_review_not_scored"
            for row in rows
        ),
        "route_score_current_rows": sum(row["route_score_current"] for row in rows),
        "winner_current_rows": sum(row["winner_current"] for row in rows),
        "JRC_current_rows": sum(row["JRC_current"] for row in rows),
        "yield_current_rows": sum(row["yield_current"] for row in rows),
        "detection_probability_current_rows": sum(row["detection_probability_current"] for row in rows),
        "wet_pass_probability_current_rows": sum(row["wet_pass_probability_current"] for row in rows),
        "production_ingestion_current_rows": sum(row["production_ingestion_current"] for row in rows),
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context"
            for row in dirty_context
        ),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "next_high_leverage_step": (
            "run formula policy review after accepted detector and wet evidence make component vectors ready"
        ),
    }
    payload = {
        "summary": summary,
        "dry_run_rows": rows,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    failures: list[str] = []
    if s["disposition"] not in {DISPOSITION, READY_DISPOSITION}:
        failures.append("disposition_not_ready")
    if s["source_missing_rows"] != 0:
        failures.append("source_missing")
    if s["dry_run_rows"] != 2:
        failures.append("expected_two_dry_run_rows")
    for key in (
        "route_score_current_rows",
        "winner_current_rows",
        "JRC_current_rows",
        "yield_current_rows",
        "detection_probability_current_rows",
        "production_ingestion_current_rows",
    ):
        if s[key] != 0:
            failures.append(f"{key}_unexpectedly_positive")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json",
        "dry_run_rows": OUTPUT_DIR / f"{PREFIX}_DRY_RUN_ROWS_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"572_{PREFIX}_20260701.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    }
    write_json_atomic(outputs["status"], {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]}, sort_keys=True)
    write_csv_rows(outputs["dry_run_rows"], payload["dry_run_rows"])
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
            "# NODI Package C Sidewall Route Formula Review Dry Run",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Claim boundary: `{s['claim_boundary']}`",
            "",
            f"Dry-run rows: `{s['dry_run_rows']}`.",
            f"Component-vector ready rows: `{s['component_vector_ready_rows']}`.",
            f"route/yield/detection current rows: `{s['route_score_current_rows']}` / `{s['yield_current_rows']}` / `{s['detection_probability_current_rows']}`.",
            "",
            "This packet computes review-only formula components from q_ch, flow split, and detector/wet gates. It does not emit a route score, winner, yield, detection probability, or production claim.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_route_formula_review_dry_run:
        raise SystemExit("--confirm-sidewall-route-formula-review-dry-run is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
