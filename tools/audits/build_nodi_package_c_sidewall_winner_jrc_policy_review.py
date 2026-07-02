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
from nodi_simulator.sidewall_winner_jrc_policy_review import (  # noqa: E402
    FIXTURE_EVIDENCE_CLASS,
    SIMULATION_ACCEPTED_EVIDENCE_CLASS,
    SIDEWALL_WINNER_JRC_POLICY_REVIEW_CLAIM_BOUNDARY,
    SIDEWALL_WINNER_JRC_POLICY_REVIEW_VERSION,
    build_winner_jrc_policy_review,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_WINNER_JRC_POLICY_REVIEW"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_WINNER_JRC_POLICY_REVIEW_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_WINNER_JRC_POLICY_REVIEW_READY_WAITING_FOR_CURRENT_ROUTE_SCORES"
)
READY_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_WINNER_JRC_POLICY_REVIEW_SIMULATION_TOP_CANDIDATE_READY_FOR_INTEGRATED_REVIEW"
)
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_WINNER_JRC_POLICY_REVIEW_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_WINNER_JRC_POLICY_REVIEW_CLAIM_BOUNDARY

ROUTE_FORMULA_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_STATUS_20260701.json"
)
ROUTE_FORMULA_POLICY_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_POLICY_ROWS_20260701.csv"
)
ROUTE_FORMULA_FIXTURE_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_FIXTURE_POLICY_ROWS_NOT_EVIDENCE_20260701.csv"
)

ALLOWED_USE = "winner/JRC policy review after route-score candidate policy"
BLOCKED_USE = (
    "yield;detection_probability;wet_pass_probability;production ingestion;fixture rows as evidence"
)

SOURCE_FILES = {
    "route_formula_policy_status": ROUTE_FORMULA_STATUS,
    "route_formula_policy_rows": ROUTE_FORMULA_POLICY_ROWS,
    "route_formula_fixture_rows": ROUTE_FORMULA_FIXTURE_ROWS,
    "winner_jrc_source": PROJECT_ROOT / "nodi_simulator/sidewall_winner_jrc_policy_review.py",
    "winner_jrc_builder": PROJECT_ROOT / "tools/audits/build_nodi_package_c_sidewall_winner_jrc_policy_review.py",
    "winner_jrc_tests": PROJECT_ROOT / "tests/test_sidewall_winner_jrc_policy_review.py",
    "winner_jrc_builder_tests": PROJECT_ROOT / "tests/test_nodi_package_c_sidewall_winner_jrc_policy_review.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_winner_jrc_policy_review.py",
    "tools/audits/build_nodi_package_c_sidewall_winner_jrc_policy_review.py",
    "tests/test_sidewall_winner_jrc_policy_review.py",
    "tests/test_nodi_package_c_sidewall_winner_jrc_policy_review.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build sidewall winner/JRC policy review.")
    parser.add_argument("--confirm-sidewall-winner-jrc-policy-review", action="store_true")
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
    output_report = f"reports/575_{PREFIX}_20260701.md"
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "winner_jrc_policy_review_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "winner_jrc_policy_review_output"
            release_decision = "included_or_rewritten_by_winner_jrc_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_winner_jrc_policy_review"
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
                "review_rows": payload["review_rows"],
                "fixture_review_rows": payload["fixture_review_rows"],
                "guard_rows": payload["guard_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    review_rows, guard_rows = build_winner_jrc_policy_review(
        route_formula_policy_rows=read_csv_rows(ROUTE_FORMULA_POLICY_ROWS),
        source_evidence_class=SIMULATION_ACCEPTED_EVIDENCE_CLASS,
    )
    fixture_rows, fixture_guard_rows = build_winner_jrc_policy_review(
        route_formula_policy_rows=read_csv_rows(ROUTE_FORMULA_FIXTURE_ROWS),
        source_evidence_class=FIXTURE_EVIDENCE_CLASS,
    )
    review_dicts = [row.to_dict() for row in review_rows]
    fixture_dicts = [row.to_dict() for row in fixture_rows]
    guard_dicts = [row.to_dict() for row in guard_rows]
    fixture_guard_dicts = [row.to_dict() for row in fixture_guard_rows]
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    formula_status = load_json(ROUTE_FORMULA_STATUS)
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    winner_rows = sum(row["winner_current"] for row in review_dicts)
    jrc_rows = sum(row["JRC_current"] for row in review_dicts)
    simulation_top_rows = sum(
        row["simulation_top_candidate_current"] for row in review_dicts
    )
    fixture_order_rows = sum(
        row["winner_jrc_policy_review_status"]
        == "fixture_winner_order_path_passes_not_evidence"
        for row in fixture_dicts
    )
    disposition = READY_DISPOSITION if simulation_top_rows == 1 else DISPOSITION
    if (
        source_missing
        or len(review_dicts) != 2
        or len(fixture_dicts) != 2
        or fixture_order_rows != 2
        or any(row["winner_current"] for row in fixture_dicts)
        or any(row["JRC_current"] for row in fixture_dicts)
        or any(row["yield_current"] for row in review_dicts + fixture_dicts)
        or any(row["detection_probability_current"] for row in review_dicts + fixture_dicts)
    ):
        disposition = BLOCKED_DISPOSITION
    summary: dict[str, Any] = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "review_version": SIDEWALL_WINNER_JRC_POLICY_REVIEW_VERSION,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_route_formula_policy_disposition": str(formula_status.get("disposition", "")),
        "review_rows": len(review_dicts),
        "fixture_review_rows": len(fixture_dicts),
        "guard_rows": len(guard_dicts),
        "fixture_guard_rows": len(fixture_guard_dicts),
        "winner_current_rows": winner_rows,
        "JRC_current_rows": jrc_rows,
        "simulation_top_candidate_current_rows": simulation_top_rows,
        "fixture_order_rows_not_evidence": fixture_order_rows,
        "route_score_current_rows": sum(row["route_score_current"] for row in review_dicts),
        "unique_top_available_rows": sum(
            row["unique_top_route_score_available"] for row in review_dicts
        ),
        "yield_current_rows": sum(row["yield_current"] for row in review_dicts),
        "detection_probability_current_rows": sum(
            row["detection_probability_current"] for row in review_dicts
        ),
        "production_ingestion_current_rows": sum(
            row["production_ingestion_current"] for row in review_dicts
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
            "after current simulation route scores and unique top are ready, run integrated route/yield/detection review"
        ),
    }
    payload = {
        "summary": summary,
        "review_rows": review_dicts,
        "fixture_review_rows": fixture_dicts,
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
    if s["review_rows"] != 2 or s["fixture_review_rows"] != 2:
        failures.append("expected_two_route_rows_each")
    if s["fixture_order_rows_not_evidence"] != 2:
        failures.append("fixture_order_path_not_open")
    for key in (
        "yield_current_rows",
        "detection_probability_current_rows",
        "production_ingestion_current_rows",
    ):
        if s[key] != 0:
            failures.append(f"{key}_unexpectedly_positive")
    for row in payload["fixture_review_rows"]:
        if row["winner_current"] or row["JRC_current"] or not row["fixture_not_evidence"]:
            failures.append(f"fixture_row_promoted_{row['route_candidate_id']}")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json",
        "review_rows": OUTPUT_DIR / f"{PREFIX}_REVIEW_ROWS_20260701.csv",
        "fixture_review_rows": OUTPUT_DIR / f"{PREFIX}_FIXTURE_REVIEW_ROWS_NOT_EVIDENCE_20260701.csv",
        "guard_rows": OUTPUT_DIR / f"{PREFIX}_GUARD_ROWS_20260701.csv",
        "fixture_guard_rows": OUTPUT_DIR / f"{PREFIX}_FIXTURE_GUARD_ROWS_NOT_EVIDENCE_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"575_{PREFIX}_20260701.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    }
    write_json_atomic(
        outputs["status"],
        {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]},
        sort_keys=True,
    )
    write_csv_rows(outputs["review_rows"], payload["review_rows"])
    write_csv_rows(outputs["fixture_review_rows"], payload["fixture_review_rows"])
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
            "# NODI Package C Sidewall Winner/JRC Policy Review",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Claim boundary: `{s['claim_boundary']}`",
            "",
            f"Current review rows: `{s['review_rows']}`.",
            f"Current route-score rows: `{s['route_score_current_rows']}`.",
            f"Current winner/JRC rows: `{s['winner_current_rows']}` / `{s['JRC_current_rows']}`.",
            f"Simulation top-candidate rows: `{s['simulation_top_candidate_current_rows']}`.",
            f"Fixture order rows, not evidence: `{s['fixture_order_rows_not_evidence']}`.",
            "",
            "Winner/JRC activation is implemented, but it requires current simulation route-score candidates for every route and a unique top route. Fixture ordering is not evidence.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_sidewall_winner_jrc_policy_review:
        parser.error("--confirm-sidewall-winner-jrc-policy-review is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_WINNER_JRC_POLICY_REVIEW")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
