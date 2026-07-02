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
from nodi_simulator.sidewall_route_accepted_evidence_smoke import (  # noqa: E402
    SIDEWALL_ROUTE_ACCEPTED_EVIDENCE_SMOKE_CLAIM_BOUNDARY,
    SIDEWALL_ROUTE_ACCEPTED_EVIDENCE_SMOKE_VERSION,
    build_route_accepted_evidence_smoke,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_ROUTE_ACCEPTED_EVIDENCE_SMOKE"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_ROUTE_ACCEPTED_EVIDENCE_SMOKE_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_ACCEPTED_EVIDENCE_SMOKE_READY_FIXTURE_PATH_PASSES_NOT_EVIDENCE"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_ACCEPTED_EVIDENCE_SMOKE_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_ROUTE_ACCEPTED_EVIDENCE_SMOKE_CLAIM_BOUNDARY

DETECTOR_PANEL_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_ROUTE_EVIDENCE_MATRIX_ROWS_20260701.csv"
WET_CONTRACT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_CONTRACT_ROWS_20260701.csv"
BINDER_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_BINDER_ROWS_20260701.csv"

ALLOWED_USE = "fixture-only accepted-evidence smoke for activation closure and formula dry-run path"
BLOCKED_USE = "simulation evidence source rows;template-as-evidence;route_score;winner;JRC;yield;detection_probability;wet_pass_probability;production ingestion"

SOURCE_FILES = {
    "detector_panel_rows": DETECTOR_PANEL_ROWS,
    "wet_contract_rows": WET_CONTRACT_ROWS,
    "qch_detector_wet_binder_rows": BINDER_ROWS,
    "smoke_source": PROJECT_ROOT / "nodi_simulator/sidewall_route_accepted_evidence_smoke.py",
    "smoke_builder": PROJECT_ROOT / "tools/audits/build_nodi_package_c_sidewall_route_accepted_evidence_smoke.py",
    "smoke_tests": PROJECT_ROOT / "tests/test_sidewall_route_accepted_evidence_smoke.py",
    "smoke_builder_tests": PROJECT_ROOT / "tests/test_nodi_package_c_sidewall_route_accepted_evidence_smoke.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_route_accepted_evidence_smoke.py",
    "tools/audits/build_nodi_package_c_sidewall_route_accepted_evidence_smoke.py",
    "tests/test_sidewall_route_accepted_evidence_smoke.py",
    "tests/test_nodi_package_c_sidewall_route_accepted_evidence_smoke.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build sidewall accepted-evidence smoke packet.")
    parser.add_argument("--confirm-sidewall-route-accepted-evidence-smoke", action="store_true")
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


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    output_prefix = f"reports/joint_interface_20260701/{PREFIX}_"
    output_report = f"reports/573_{PREFIX}_20260701.md"
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "route_accepted_evidence_smoke_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "route_accepted_evidence_smoke_output"
            release_decision = "included_or_rewritten_by_smoke_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_route_accepted_evidence_smoke"
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
        json.dumps(
            {
                "smoke_rows": payload["smoke_rows"],
                "dry_run_rows": payload["dry_run_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    detector_fixture, wet_fixture, smoke_rows, dry_run_rows = build_route_accepted_evidence_smoke(
        detector_panel_matrix_rows=read_csv_rows(DETECTOR_PANEL_ROWS),
        wet_contract_rows=read_csv_rows(WET_CONTRACT_ROWS),
        qch_detector_wet_binder_rows=read_csv_rows(BINDER_ROWS),
    )
    smoke_dicts = [row.to_dict() for row in smoke_rows]
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    fixture_path_pass = sum(
        row["smoke_status"] == "fixture_path_passes_chain_to_component_vector_not_evidence"
        for row in smoke_dicts
    )
    summary: dict[str, Any] = {
        "disposition": DISPOSITION
        if source_missing == 0
        and len(smoke_dicts) == 2
        and fixture_path_pass == 2
        and all(row["fixture_not_evidence"] is True for row in smoke_dicts)
        and all(row["route_score_current"] is False for row in smoke_dicts)
        and all(row["yield_current"] is False for row in smoke_dicts)
        and all(row["detection_probability_current"] is False for row in smoke_dicts)
        else BLOCKED_DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "smoke_version": SIDEWALL_ROUTE_ACCEPTED_EVIDENCE_SMOKE_VERSION,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "detector_fixture_rows": len(detector_fixture),
        "wet_fixture_rows": len(wet_fixture),
        "smoke_rows": len(smoke_dicts),
        "dry_run_rows": len(dry_run_rows),
        "fixture_path_pass_rows": fixture_path_pass,
        "route_formula_ready_for_claim_review_rows": sum(
            row["route_formula_ready_for_claim_review"] for row in smoke_dicts
        ),
        "component_vector_ready_rows": sum(
            row["component_vector_ready_for_policy_review"] for row in smoke_dicts
        ),
        "fixture_not_evidence_rows": sum(row["fixture_not_evidence"] for row in smoke_dicts),
        "route_score_current_rows": sum(row["route_score_current"] for row in smoke_dicts),
        "winner_current_rows": sum(row["winner_current"] for row in smoke_dicts),
        "JRC_current_rows": sum(row["JRC_current"] for row in smoke_dicts),
        "yield_current_rows": sum(row["yield_current"] for row in smoke_dicts),
        "detection_probability_current_rows": sum(row["detection_probability_current"] for row in smoke_dicts),
        "wet_pass_probability_current_rows": sum(row["wet_pass_probability_current"] for row in smoke_dicts),
        "production_ingestion_current_rows": sum(row["production_ingestion_current"] for row in smoke_dicts),
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
            "use accepted simulation detector/wet input rows, then rerun the same activation closure and dry-run chain"
        ),
    }
    payload = {
        "summary": summary,
        "detector_fixture_rows": detector_fixture,
        "wet_fixture_rows": wet_fixture,
        "smoke_rows": smoke_dicts,
        "dry_run_rows": dry_run_rows,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    failures: list[str] = []
    if s["disposition"] != DISPOSITION:
        failures.append("disposition_not_ready")
    if s["detector_fixture_rows"] != 2:
        failures.append("expected_two_detector_fixture_rows")
    if s["wet_fixture_rows"] != 14:
        failures.append("expected_fourteen_wet_fixture_rows")
    if s["fixture_path_pass_rows"] != 2:
        failures.append("fixture_path_did_not_pass_both_routes")
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
        "smoke_rows": OUTPUT_DIR / f"{PREFIX}_SMOKE_ROWS_20260701.csv",
        "detector_fixture_rows": OUTPUT_DIR / f"{PREFIX}_DETECTOR_FIXTURE_ROWS_NOT_EVIDENCE_20260701.csv",
        "wet_fixture_rows": OUTPUT_DIR / f"{PREFIX}_WET_FIXTURE_ROWS_NOT_EVIDENCE_20260701.csv",
        "dry_run_rows": OUTPUT_DIR / f"{PREFIX}_DRY_RUN_ROWS_NOT_EVIDENCE_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"573_{PREFIX}_20260701.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    }
    write_json_atomic(outputs["status"], {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]}, sort_keys=True)
    write_csv_rows(outputs["smoke_rows"], payload["smoke_rows"])
    write_csv_rows(outputs["detector_fixture_rows"], payload["detector_fixture_rows"])
    write_csv_rows(outputs["wet_fixture_rows"], payload["wet_fixture_rows"])
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
            "# NODI Package C Sidewall Route Accepted Evidence Smoke",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Claim boundary: `{s['claim_boundary']}`",
            "",
            f"Fixture detector/wet rows: `{s['detector_fixture_rows']}` / `{s['wet_fixture_rows']}`.",
            f"Fixture path pass rows: `{s['fixture_path_pass_rows']}`.",
            f"Component-vector ready rows: `{s['component_vector_ready_rows']}`.",
            f"route/yield/detection current rows: `{s['route_score_current_rows']}` / `{s['yield_current_rows']}` / `{s['detection_probability_current_rows']}`.",
            "",
            "This is a fixture-only smoke artifact. It proves the accepted-evidence code path can open the formula component vector, but the generated fixture rows are not evidence and are not written to the simulation input paths.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_route_accepted_evidence_smoke:
        raise SystemExit("--confirm-sidewall-route-accepted-evidence-smoke is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
