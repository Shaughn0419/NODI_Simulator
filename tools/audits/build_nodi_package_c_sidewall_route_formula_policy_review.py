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
from nodi_simulator.sidewall_route_formula_policy_review import (  # noqa: E402
    FIXTURE_EVIDENCE_CLASS,
    REAL_ACCEPTED_EVIDENCE_CLASS,
    SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_CLAIM_BOUNDARY,
    SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_FORMULA_ID,
    SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_VERSION,
    build_route_formula_policy_review,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_READY_WAITING_FOR_REAL_ACCEPTED_EVIDENCE"
)
READY_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_ROUTE_SCORE_CANDIDATES_READY_FOR_WINNER_POLICY_REVIEW"
)
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_CLAIM_BOUNDARY

CURRENT_DRY_RUN_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_STATUS_20260701.json"
)
CURRENT_DRY_RUN_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_DRY_RUN_ROWS_20260701.csv"
)
ACTIVATION_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_STATUS_20260701.json"
)
SMOKE_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_ACCEPTED_EVIDENCE_SMOKE_STATUS_20260701.json"
)
SMOKE_DRY_RUN_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_ACCEPTED_EVIDENCE_SMOKE_DRY_RUN_ROWS_NOT_EVIDENCE_20260701.csv"
)

ALLOWED_USE = (
    "route formula policy review;route-score candidate formula activation after real accepted evidence"
)
BLOCKED_USE = (
    "winner;JRC;yield;detection_probability;wet_pass_probability;production ingestion;"
    "fixture rows as evidence"
)

SOURCE_FILES = {
    "current_dry_run_status": CURRENT_DRY_RUN_STATUS,
    "current_dry_run_rows": CURRENT_DRY_RUN_ROWS,
    "detector_wet_activation_status": ACTIVATION_STATUS,
    "fixture_smoke_status": SMOKE_STATUS,
    "fixture_smoke_dry_run_rows": SMOKE_DRY_RUN_ROWS,
    "policy_review_source": PROJECT_ROOT / "nodi_simulator/sidewall_route_formula_policy_review.py",
    "policy_review_builder": PROJECT_ROOT / "tools/audits/build_nodi_package_c_sidewall_route_formula_policy_review.py",
    "policy_review_tests": PROJECT_ROOT / "tests/test_sidewall_route_formula_policy_review.py",
    "policy_review_builder_tests": PROJECT_ROOT / "tests/test_nodi_package_c_sidewall_route_formula_policy_review.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_route_formula_policy_review.py",
    "tools/audits/build_nodi_package_c_sidewall_route_formula_policy_review.py",
    "tests/test_sidewall_route_formula_policy_review.py",
    "tests/test_nodi_package_c_sidewall_route_formula_policy_review.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sidewall route formula policy-review packet."
    )
    parser.add_argument("--confirm-sidewall-route-formula-policy-review", action="store_true")
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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    output_prefix = f"reports/joint_interface_20260701/{PREFIX}_"
    output_report = f"reports/574_{PREFIX}_20260701.md"
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "route_formula_policy_review_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "route_formula_policy_review_output"
            release_decision = "included_or_rewritten_by_policy_review_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_route_formula_policy_review"
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
                "policy_rows": payload["policy_rows"],
                "fixture_policy_rows": payload["fixture_policy_rows"],
                "guard_rows": payload["guard_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    current_rows, current_guards = build_route_formula_policy_review(
        route_formula_dry_run_rows=read_csv_rows(CURRENT_DRY_RUN_ROWS),
        source_evidence_class=REAL_ACCEPTED_EVIDENCE_CLASS,
    )
    fixture_rows, fixture_guards = build_route_formula_policy_review(
        route_formula_dry_run_rows=read_csv_rows(SMOKE_DRY_RUN_ROWS),
        source_evidence_class=FIXTURE_EVIDENCE_CLASS,
    )
    policy_dicts = [row.to_dict() for row in current_rows]
    fixture_dicts = [row.to_dict() for row in fixture_rows]
    guard_dicts = [row.to_dict() for row in current_guards]
    fixture_guard_dicts = [row.to_dict() for row in fixture_guards]
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    current_status = load_json(CURRENT_DRY_RUN_STATUS)
    activation_status = load_json(ACTIVATION_STATUS)
    smoke_status = load_json(SMOKE_STATUS)
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    current_score_rows = sum(row["route_score_current"] for row in policy_dicts)
    fixture_candidate_rows = sum(
        row["route_formula_policy_review_status"]
        == "fixture_route_score_candidate_path_passes_not_evidence"
        for row in fixture_dicts
    )
    disposition = (
        READY_DISPOSITION
        if current_score_rows == len(policy_dicts) and policy_dicts
        else DISPOSITION
    )
    if (
        source_missing
        or len(policy_dicts) != 2
        or len(fixture_dicts) != 2
        or fixture_candidate_rows != 2
        or any(row["route_score_current"] for row in fixture_dicts)
        or any(row["winner_current"] for row in policy_dicts + fixture_dicts)
        or any(row["yield_current"] for row in policy_dicts + fixture_dicts)
        or any(row["detection_probability_current"] for row in policy_dicts + fixture_dicts)
    ):
        disposition = BLOCKED_DISPOSITION
    summary: dict[str, Any] = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "policy_version": SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_VERSION,
        "formula_id": SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_FORMULA_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_current_dry_run_disposition": str(current_status.get("disposition", "")),
        "source_activation_disposition": str(activation_status.get("disposition", "")),
        "source_fixture_smoke_disposition": str(smoke_status.get("disposition", "")),
        "policy_rows": len(policy_dicts),
        "fixture_policy_rows": len(fixture_dicts),
        "guard_rows": len(guard_dicts),
        "fixture_guard_rows": len(fixture_guard_dicts),
        "current_formula_component_ready_rows": sum(
            row["route_formula_component_vector_ready"] for row in policy_dicts
        ),
        "fixture_formula_component_ready_rows": sum(
            row["route_formula_component_vector_ready"] for row in fixture_dicts
        ),
        "route_score_current_rows": current_score_rows,
        "route_score_candidate_ready_rows": sum(
            row["route_score_activation_allowed_now"] for row in policy_dicts
        ),
        "fixture_route_score_candidate_rows_not_evidence": fixture_candidate_rows,
        "winner_current_rows": sum(row["winner_current"] for row in policy_dicts),
        "JRC_current_rows": sum(row["JRC_current"] for row in policy_dicts),
        "yield_current_rows": sum(row["yield_current"] for row in policy_dicts),
        "detection_probability_current_rows": sum(
            row["detection_probability_current"] for row in policy_dicts
        ),
        "production_ingestion_current_rows": sum(
            row["production_ingestion_current"] for row in policy_dicts
        ),
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
            "when real detector/wet rows are accepted, rerun activation/dry-run and this policy review; "
            "then run winner/JRC policy review"
        ),
    }
    payload = {
        "summary": summary,
        "policy_rows": policy_dicts,
        "fixture_policy_rows": fixture_dicts,
        "guard_rows": guard_dicts,
        "fixture_guard_rows": fixture_guard_dicts,
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
    if s["policy_rows"] != 2 or s["fixture_policy_rows"] != 2:
        failures.append("expected_two_route_rows_each")
    if s["fixture_route_score_candidate_rows_not_evidence"] != 2:
        failures.append("fixture_score_path_not_open")
    for key in (
        "winner_current_rows",
        "JRC_current_rows",
        "yield_current_rows",
        "detection_probability_current_rows",
        "production_ingestion_current_rows",
    ):
        if s[key] != 0:
            failures.append(f"{key}_unexpectedly_positive")
    for row in payload["fixture_policy_rows"]:
        if row["route_score_current"] or not row["fixture_not_evidence"]:
            failures.append(f"fixture_row_promoted_{row['route_candidate_id']}")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json",
        "policy_rows": OUTPUT_DIR / f"{PREFIX}_POLICY_ROWS_20260701.csv",
        "fixture_policy_rows": OUTPUT_DIR / f"{PREFIX}_FIXTURE_POLICY_ROWS_NOT_EVIDENCE_20260701.csv",
        "guard_rows": OUTPUT_DIR / f"{PREFIX}_GUARD_ROWS_20260701.csv",
        "fixture_guard_rows": OUTPUT_DIR / f"{PREFIX}_FIXTURE_GUARD_ROWS_NOT_EVIDENCE_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"574_{PREFIX}_20260701.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    }
    write_json_atomic(
        outputs["status"],
        {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]},
        sort_keys=True,
    )
    write_csv_rows(outputs["policy_rows"], payload["policy_rows"])
    write_csv_rows(outputs["fixture_policy_rows"], payload["fixture_policy_rows"])
    write_csv_rows(outputs["guard_rows"], payload["guard_rows"])
    write_csv_rows(outputs["fixture_guard_rows"], payload["fixture_guard_rows"])
    write_csv_rows(outputs["source_lock"], payload["source_lock_rows"])
    write_csv_rows(outputs["dirty_context"], payload["dirty_context_rows"])
    write_json_atomic(outputs["report_json"], payload, sort_keys=True)
    outputs["master_report"].write_text(render_markdown(payload), encoding="utf-8")
    write_csv_rows(outputs["manifest"], manifest_rows(outputs, payload["summary"]["disposition"]))
    return list(outputs.values())


def manifest_rows(outputs: dict[str, Path], disposition: str) -> list[dict[str, Any]]:
    return [
        {
            "artifact_id": artifact_id,
            "path": display_path(path),
            "sha256": SELF_MANIFEST_SHA256 if artifact_id == "manifest" else sha256_file(path),
            "disposition": disposition,
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
            "# NODI Package C Sidewall Route Formula Policy Review",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Formula ID: `{s['formula_id']}`",
            f"Claim boundary: `{s['claim_boundary']}`",
            "",
            f"Current policy rows: `{s['policy_rows']}`.",
            f"Current formula-component ready rows: `{s['current_formula_component_ready_rows']}`.",
            f"Current route-score rows: `{s['route_score_current_rows']}`.",
            f"Fixture candidate rows, not evidence: `{s['fixture_route_score_candidate_rows_not_evidence']}`.",
            "",
            "The route-score formula is now executable, but current real accepted detector/wet evidence is still absent. Fixture rows only prove the policy-review path and cannot be used as route evidence.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_sidewall_route_formula_policy_review:
        parser.error("--confirm-sidewall-route-formula-policy-review is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
