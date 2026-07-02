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
from nodi_simulator.sidewall_yield_detection_claim_value_review import (  # noqa: E402
    SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_CLAIM_BOUNDARY,
    SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_VERSION,
    build_yield_detection_claim_value_review,
    detection_claim_value_template_rows,
    yield_claim_value_template_rows,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_READY_AWAITING_REAL_VALUE_ROWS"
)
READY_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_VALUES_READY_FOR_INTEGRATED_REVIEW"
)
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_CLAIM_BOUNDARY

WINNER_JRC_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WINNER_JRC_POLICY_REVIEW_STATUS_20260701.json"
WINNER_JRC_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WINNER_JRC_POLICY_REVIEW_REVIEW_ROWS_20260701.csv"
DETECTION_VALUE_INPUT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTION_PROBABILITY_VALUE_INPUT_ROWS_20260701.csv"
YIELD_VALUE_INPUT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_YIELD_WET_VALUE_INPUT_ROWS_20260701.csv"

ALLOWED_USE = (
    "yield and detection-probability claim-value input validation;integrated route review input"
)
BLOCKED_USE = "production ingestion;fabrication release;template rows as evidence"

SOURCE_FILES = {
    "winner_jrc_status": WINNER_JRC_STATUS,
    "winner_jrc_rows": WINNER_JRC_ROWS,
    "detection_value_input_rows": DETECTION_VALUE_INPUT_ROWS,
    "yield_value_input_rows": YIELD_VALUE_INPUT_ROWS,
    "claim_value_source": PROJECT_ROOT / "nodi_simulator/sidewall_yield_detection_claim_value_review.py",
    "claim_value_builder": PROJECT_ROOT / "tools/audits/build_nodi_package_c_sidewall_yield_detection_claim_value_review.py",
    "claim_value_tests": PROJECT_ROOT / "tests/test_sidewall_yield_detection_claim_value_review.py",
    "claim_value_builder_tests": PROJECT_ROOT / "tests/test_nodi_package_c_sidewall_yield_detection_claim_value_review.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_yield_detection_claim_value_review.py",
    "tools/audits/build_nodi_package_c_sidewall_yield_detection_claim_value_review.py",
    "tests/test_sidewall_yield_detection_claim_value_review.py",
    "tests/test_nodi_package_c_sidewall_yield_detection_claim_value_review.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sidewall yield/detection claim-value review packet."
    )
    parser.add_argument(
        "--confirm-sidewall-yield-detection-claim-value-review",
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


def optional_csv(path: Path) -> list[dict[str, str]]:
    return read_csv_rows(path) if path.exists() else []


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    output_prefix = f"reports/joint_interface_20260701/{PREFIX}_"
    output_report = f"reports/576_{PREFIX}_20260701.md"
    input_paths = {
        display_path(DETECTION_VALUE_INPUT_ROWS),
        display_path(YIELD_VALUE_INPUT_ROWS),
    }
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "yield_detection_claim_value_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "yield_detection_claim_value_output"
            release_decision = "included_or_rewritten_by_claim_value_builder"
        elif path in input_paths:
            classification = "claim_value_real_input_context"
            release_decision = "source_locked_input_not_rewritten_by_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_yield_detection_claim_value_review"
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
                "claim_value_rows": payload["claim_value_rows"],
                "guard_rows": payload["guard_rows"],
                "input_contract_rows": payload["input_contract_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    winner_rows = read_csv_rows(WINNER_JRC_ROWS)
    claim_rows, guard_rows = build_yield_detection_claim_value_review(
        winner_jrc_rows=winner_rows,
        detection_value_rows=optional_csv(DETECTION_VALUE_INPUT_ROWS),
        yield_value_rows=optional_csv(YIELD_VALUE_INPUT_ROWS),
        artifact_root=PROJECT_ROOT,
    )
    claim_dicts = [row.to_dict() for row in claim_rows]
    guard_dicts = [row.to_dict() for row in guard_rows]
    detection_templates = detection_claim_value_template_rows(winner_rows)
    yield_templates = yield_claim_value_template_rows(winner_rows)
    input_contract_rows = [
        {
            "input_name": "detection_probability_value_input_rows",
            "input_path": display_path(DETECTION_VALUE_INPUT_ROWS),
            "input_present": DETECTION_VALUE_INPUT_ROWS.exists(),
            "template_rows": len(detection_templates),
            "accepted_current_rows": sum(
                row["detection_probability_current"] for row in claim_dicts
            ),
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "input_name": "yield_wet_value_input_rows",
            "input_path": display_path(YIELD_VALUE_INPUT_ROWS),
            "input_present": YIELD_VALUE_INPUT_ROWS.exists(),
            "template_rows": len(yield_templates),
            "accepted_current_rows": sum(row["yield_current"] for row in claim_dicts),
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(
        row["exists"] != "true"
        for row in source_lock
        if row["source_id"] not in {"detection_value_input_rows", "yield_value_input_rows"}
    )
    detection_ready = sum(row["detection_probability_current"] for row in claim_dicts)
    yield_ready = sum(row["yield_current"] for row in claim_dicts)
    wet_pass_ready = sum(row["wet_pass_probability_current"] for row in claim_dicts)
    disposition = (
        READY_DISPOSITION
        if detection_ready == len(claim_dicts)
        and yield_ready == len(claim_dicts)
        and wet_pass_ready == len(claim_dicts)
        and claim_dicts
        else DISPOSITION
    )
    if (
        source_missing
        or len(claim_dicts) != 2
        or any(row["production_ingestion_current"] for row in claim_dicts)
    ):
        disposition = BLOCKED_DISPOSITION
    winner_status = load_json(WINNER_JRC_STATUS)
    summary: dict[str, Any] = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "review_version": SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_VERSION,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_winner_jrc_disposition": str(winner_status.get("disposition", "")),
        "claim_value_rows": len(claim_dicts),
        "guard_rows": len(guard_dicts),
        "detection_template_rows": len(detection_templates),
        "yield_template_rows": len(yield_templates),
        "detection_input_present": DETECTION_VALUE_INPUT_ROWS.exists(),
        "yield_input_present": YIELD_VALUE_INPUT_ROWS.exists(),
        "detection_probability_current_rows": detection_ready,
        "yield_current_rows": yield_ready,
        "wet_pass_probability_current_rows": wet_pass_ready,
        "production_ingestion_current_rows": sum(
            row["production_ingestion_current"] for row in claim_dicts
        ),
        "guard_activation_allowed_rows": sum(
            row["activation_allowed_now"] for row in guard_dicts
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
            "provide real detection/yield value input rows, then rerun this review and the integrated decision review"
        ),
    }
    payload = {
        "summary": summary,
        "claim_value_rows": claim_dicts,
        "guard_rows": guard_dicts,
        "detection_template_rows": detection_templates,
        "yield_template_rows": yield_templates,
        "input_contract_rows": input_contract_rows,
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
    if s["claim_value_rows"] != 2:
        failures.append("expected_two_claim_value_rows")
    if s["detection_template_rows"] != 2 or s["yield_template_rows"] != 2:
        failures.append("expected_two_template_rows_each")
    if s["production_ingestion_current_rows"] != 0:
        failures.append("production_ingestion_unexpectedly_positive")
    for row in payload["claim_value_rows"]:
        if row["claim_boundary"] != CLAIM_BOUNDARY:
            failures.append(f"claim_boundary_mismatch_{row['route_candidate_id']}")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json",
        "claim_value_rows": OUTPUT_DIR / f"{PREFIX}_CLAIM_VALUE_ROWS_20260701.csv",
        "guard_rows": OUTPUT_DIR / f"{PREFIX}_GUARD_ROWS_20260701.csv",
        "detection_template_rows": OUTPUT_DIR / f"{PREFIX}_DETECTION_VALUE_TEMPLATE_ROWS_20260701.csv",
        "yield_template_rows": OUTPUT_DIR / f"{PREFIX}_YIELD_VALUE_TEMPLATE_ROWS_20260701.csv",
        "input_contract_rows": OUTPUT_DIR / f"{PREFIX}_INPUT_CONTRACT_ROWS_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"576_{PREFIX}_20260701.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    }
    write_json_atomic(
        outputs["status"],
        {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]},
        sort_keys=True,
    )
    write_csv_rows(outputs["claim_value_rows"], payload["claim_value_rows"])
    write_csv_rows(outputs["guard_rows"], payload["guard_rows"])
    write_csv_rows(outputs["detection_template_rows"], payload["detection_template_rows"])
    write_csv_rows(outputs["yield_template_rows"], payload["yield_template_rows"])
    write_csv_rows(outputs["input_contract_rows"], payload["input_contract_rows"])
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
            "# NODI Package C Sidewall Yield/Detection Claim Value Review",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Claim boundary: `{s['claim_boundary']}`",
            "",
            f"Detection input present: `{s['detection_input_present']}`.",
            f"Yield input present: `{s['yield_input_present']}`.",
            f"Current detection/yield/wet-pass rows: `{s['detection_probability_current_rows']}` / `{s['yield_current_rows']}` / `{s['wet_pass_probability_current_rows']}`.",
            "",
            "This packet defines the real numeric value rows required before detection probability, yield, or wet-pass claims can become current. Templates are not evidence.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_sidewall_yield_detection_claim_value_review:
        parser.error("--confirm-sidewall-yield-detection-claim-value-review is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
