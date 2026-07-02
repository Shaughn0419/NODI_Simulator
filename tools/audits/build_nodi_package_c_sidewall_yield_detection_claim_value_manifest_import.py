#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
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
from nodi_simulator.sidewall_yield_detection_claim_value_manifest_import import (  # noqa: E402
    SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT_CLAIM_BOUNDARY,
    SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT_VERSION,
    build_yield_detection_claim_value_rows_from_manifest,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT_20260701"
READY_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT_READY_FOR_REVIEW"
)
MANIFEST_REQUIRED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT_READY_MANIFEST_REQUIRED"
)
BLOCKED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT_FAIL_CLOSED"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT_CLAIM_BOUNDARY

DEFAULT_SOURCE_MANIFEST = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_SOURCE_MANIFEST_20260701.csv"
)
CANONICAL_DETECTION_VALUE_INPUT_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_DETECTION_PROBABILITY_VALUE_INPUT_ROWS_20260701.csv"
)
CANONICAL_YIELD_VALUE_INPUT_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_YIELD_WET_VALUE_INPUT_ROWS_20260701.csv"
)

ALLOWED_USE = "manifest-bound yield/detection value input import;source artifact hash binding"
BLOCKED_USE = (
    "template-as-evidence;invented detection/yield values;route_score;winner;JRC;"
    "fabrication release;production ingestion"
)

SOURCE_FILES = {
    "manifest_import_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_yield_detection_claim_value_manifest_import.py",
    "manifest_import_module": PROJECT_ROOT
    / "nodi_simulator/sidewall_yield_detection_claim_value_manifest_import.py",
    "claim_value_review_module": PROJECT_ROOT
    / "nodi_simulator/sidewall_yield_detection_claim_value_review.py",
    "manifest_import_module_tests": PROJECT_ROOT
    / "tests/test_sidewall_yield_detection_claim_value_manifest_import.py",
    "manifest_import_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_yield_detection_claim_value_manifest_import.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_yield_detection_claim_value_manifest_import.py",
    "tools/audits/build_nodi_package_c_sidewall_yield_detection_claim_value_manifest_import.py",
    "tests/test_sidewall_yield_detection_claim_value_manifest_import.py",
    "tests/test_nodi_package_c_sidewall_yield_detection_claim_value_manifest_import.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import manifest-bound yield/detection value source artifacts."
    )
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--artifact-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--confirm-sidewall-yield-detection-claim-value-manifest-import",
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


def source_lock_rows(source_manifest: Path) -> list[dict[str, str]]:
    sources = {**SOURCE_FILES, "source_manifest": source_manifest}
    rows: list[dict[str, str]] = []
    for source_id, path in sources.items():
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
    output_report = f"reports/579_{PREFIX}_20260701.md"
    canonical_paths = {
        display_path(CANONICAL_DETECTION_VALUE_INPUT_ROWS),
        display_path(CANONICAL_YIELD_VALUE_INPUT_ROWS),
    }
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "yield_detection_claim_value_manifest_import_build_edit"
            release_decision = "included_in_code_commit_scope"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "yield_detection_claim_value_manifest_import_output"
            release_decision = "included_or_rewritten_by_manifest_import_builder"
        elif path in canonical_paths:
            classification = "claim_value_real_input_context"
            release_decision = "source_locked_input_not_rewritten_unless_manifest_import_ready"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_yield_detection_claim_value_manifest_import"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def build_payload(
    *,
    source_manifest: Path = DEFAULT_SOURCE_MANIFEST,
    artifact_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    manifest_rows = read_csv_rows(source_manifest) if source_manifest.exists() else []
    detection_rows, yield_rows, audit_rows = (
        build_yield_detection_claim_value_rows_from_manifest(
            manifest_rows=manifest_rows,
            artifact_root=artifact_root,
        )
    )
    audit_dicts = [row.to_dict() for row in audit_rows]
    if not source_manifest.exists():
        audit_dicts.append(
            {
                "import_row_id": "YIELD-DETECTION-VALUE-MANIFEST-IMPORT-source-manifest",
                "import_version": SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT_VERSION,
                "claim_value_branch": "",
                "route_candidate_id": "",
                "source_artifact_path": display_path(source_manifest),
                "source_artifact_sha256": "",
                "import_status": "yield_detection_claim_value_source_manifest_missing",
                "import_rejection_reason": "source_manifest_missing",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    source_lock = source_lock_rows(source_manifest)
    dirty_context = dirty_context_rows()
    required_source_missing = sum(
        row["source_id"] != "source_manifest" and row["exists"] != "true"
        for row in source_lock
    )
    rejected_rows = sum(
        row["import_status"].endswith("rejected") for row in audit_dicts
    )
    imported_rows = len(detection_rows) + len(yield_rows)
    if required_source_missing:
        disposition = BLOCKED_DISPOSITION
    elif not source_manifest.exists():
        disposition = MANIFEST_REQUIRED_DISPOSITION
    elif imported_rows and rejected_rows == 0:
        disposition = READY_DISPOSITION
    else:
        disposition = BLOCKED_DISPOSITION
    summary = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "import_version": SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT_VERSION,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_manifest_path": display_path(source_manifest),
        "source_manifest_present": source_manifest.exists(),
        "artifact_root": display_path(artifact_root),
        "source_manifest_rows": len(manifest_rows),
        "imported_detection_value_rows": len(detection_rows),
        "imported_yield_value_rows": len(yield_rows),
        "imported_claim_value_rows": imported_rows,
        "import_audit_rows": len(audit_dicts),
        "rejected_import_rows": rejected_rows,
        "canonical_detection_input_written": bool(detection_rows) and rejected_rows == 0,
        "canonical_yield_input_written": bool(yield_rows) and rejected_rows == 0,
        "detection_probability_current": False,
        "yield_current": False,
        "wet_pass_probability_current": False,
        "route_score_current": False,
        "winner_current": False,
        "JRC_current": False,
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
            "rerun yield_detection_claim_value_review after canonical value rows are written"
            if imported_rows
            else "provide source manifest rows for detection_probability_value and yield_wet_value"
        ),
    }
    payload = {
        "summary": summary,
        "detection_value_rows": detection_rows,
        "yield_value_rows": yield_rows,
        "import_audit_rows": audit_dicts,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "detection_value_rows": payload["detection_value_rows"],
                "yield_value_rows": payload["yield_value_rows"],
                "import_audit_rows": payload["import_audit_rows"],
                "claim_boundary": CLAIM_BOUNDARY,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    failures: list[str] = []
    if s["disposition"] not in {READY_DISPOSITION, MANIFEST_REQUIRED_DISPOSITION}:
        failures.append("disposition_not_ready")
    if s["required_source_missing_rows"] != 0:
        failures.append("required_source_missing")
    if s["route_score_current"] or s["winner_current"] or s["JRC_current"]:
        failures.append("route_decision_claim_unexpectedly_current")
    if (
        s["detection_probability_current"]
        or s["yield_current"]
        or s["wet_pass_probability_current"]
    ):
        failures.append("claim_value_unexpectedly_current")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json",
        "audit_rows": OUTPUT_DIR / f"{PREFIX}_AUDIT_ROWS_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"579_{PREFIX}_20260701.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    }
    write_json_atomic(
        outputs["status"],
        {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]},
        sort_keys=True,
    )
    if payload["detection_value_rows"]:
        outputs["imported_detection_rows"] = (
            OUTPUT_DIR / f"{PREFIX}_IMPORTED_DETECTION_VALUE_ROWS_20260701.csv"
        )
        write_csv_rows(outputs["imported_detection_rows"], payload["detection_value_rows"])
    if payload["yield_value_rows"]:
        outputs["imported_yield_rows"] = (
            OUTPUT_DIR / f"{PREFIX}_IMPORTED_YIELD_VALUE_ROWS_20260701.csv"
        )
        write_csv_rows(outputs["imported_yield_rows"], payload["yield_value_rows"])
    write_csv_rows(outputs["audit_rows"], payload["import_audit_rows"])
    if payload["summary"]["canonical_detection_input_written"]:
        write_csv_rows(
            CANONICAL_DETECTION_VALUE_INPUT_ROWS,
            payload["detection_value_rows"],
        )
        outputs["canonical_detection_value_input_rows"] = CANONICAL_DETECTION_VALUE_INPUT_ROWS
    if payload["summary"]["canonical_yield_input_written"]:
        write_csv_rows(CANONICAL_YIELD_VALUE_INPUT_ROWS, payload["yield_value_rows"])
        outputs["canonical_yield_value_input_rows"] = CANONICAL_YIELD_VALUE_INPUT_ROWS
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
            "# NODI Package C Sidewall Yield/Detection Claim Value Manifest Import",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Imported detection value rows: `{s['imported_detection_value_rows']}`",
            f"Imported yield value rows: `{s['imported_yield_value_rows']}`",
            f"Rejected import rows: `{s['rejected_import_rows']}`",
            f"Canonical detection input written: `{s['canonical_detection_input_written']}`",
            f"Canonical yield input written: `{s['canonical_yield_input_written']}`",
            f"Claim boundary: `{s['claim_boundary']}`",
            "",
            "This importer binds detection-probability, yield, and wet-pass value rows to source artifact hashes. It does not create route-score, winner, JRC, production, or fabrication claims, and current claim activation remains owned by the claim-value review packet.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_sidewall_yield_detection_claim_value_manifest_import:
        raise SystemExit(
            "--confirm-sidewall-yield-detection-claim-value-manifest-import is required"
        )
    payload = build_payload(source_manifest=args.source_manifest, artifact_root=args.artifact_root)
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
