#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows, write_json_atomic  # noqa: E402
from nodi_simulator.sidewall_detector_blank_transfer_intake import (  # noqa: E402
    ROUTE_MATRIX_ACCEPTED_STATUS,
    ROUTE_MATRIX_NO_TRANSFER_STATUS,
    SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_CLAIM_BOUNDARY,
    build_detector_blank_transfer_intake,
    detector_blank_transfer_promotion_update_rows,
    detector_blank_transfer_template_rows,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_READY_SCHEMA_NO_TRANSFER_EVIDENCE"
)
ACCEPTED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_READY_ACCEPTED_TRANSFER_CANDIDATE"
)
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_CLAIM_BOUNDARY

ASSEMBLY_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_V2_STATUS_20260701.json"
)
ASSEMBLY_BRANCH_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_V2_BRANCH_ROWS_20260701.csv"
)
DETECTOR_PANEL_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_STATUS_20260701.json"
)
DETECTOR_PANEL_MATRIX_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_ROUTE_EVIDENCE_MATRIX_ROWS_20260701.csv"
)
OPTIONAL_TRANSFER_INPUT_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INPUT_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "detector/blank transfer intake schema;sidewall blank trace validation;"
    "detector response calibration handoff"
)
BLOCKED_USE = (
    "detection_probability;route_score;winner;JRC;yield;wet_pass_probability;"
    "production ingestion"
)

SOURCE_FILES = {
    "route_yield_detection_assembly_status": ASSEMBLY_STATUS,
    "route_yield_detection_assembly_branch_rows": ASSEMBLY_BRANCH_ROWS,
    "detector_blank_panel_status": DETECTOR_PANEL_STATUS,
    "detector_blank_panel_matrix_rows": DETECTOR_PANEL_MATRIX_ROWS,
    "detector_blank_transfer_intake_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_detector_blank_transfer_intake.py",
    "detector_blank_transfer_intake_tests": PROJECT_ROOT
    / "tests/test_sidewall_detector_blank_transfer_intake.py",
    "detector_blank_transfer_intake_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_detector_blank_transfer_intake.py",
    "detector_blank_transfer_intake_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_detector_blank_transfer_intake.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_detector_blank_transfer_intake.py",
    "tests/test_sidewall_detector_blank_transfer_intake.py",
    "tools/audits/build_nodi_package_c_sidewall_detector_blank_transfer_intake.py",
    "tests/test_nodi_package_c_sidewall_detector_blank_transfer_intake.py",
    "reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
}

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sidewall detector/blank transfer intake packet."
    )
    parser.add_argument(
        "--confirm-sidewall-detector-blank-transfer-intake",
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
    if path.is_relative_to(PROJECT_ROOT):
        return path.relative_to(PROJECT_ROOT).as_posix()
    return str(path)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def release_scoped_path(path: str) -> bool:
    source_paths = {
        display_path(source_path)
        for source_path in SOURCE_FILES.values()
        if source_path.exists()
    }
    optional_input = display_path(OPTIONAL_TRANSFER_INPUT_ROWS)
    return (
        path in source_paths
        or path == optional_input
        or path in BUILD_EDIT_PATHS
        or path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_"
        )
        or path
        == "reports/547_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "detector_blank_transfer_intake_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_"
        ) or path == (
            "reports/547_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_20260701.md"
        ):
            classification = "detector_blank_transfer_intake_output"
            release_decision = "included_or_rewritten_by_detector_blank_transfer_intake"
        elif path == display_path(OPTIONAL_TRANSFER_INPUT_ROWS):
            classification = "optional_detector_blank_transfer_input"
            release_decision = "source_locked_if_present"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_detector_blank_transfer_intake"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_detector_blank_transfer_intake_not_source_locked"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_id, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_id": source_id,
                "path": display_path(path) if exists else str(path),
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else "",
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    if OPTIONAL_TRANSFER_INPUT_ROWS.exists():
        rows.append(
            {
                "source_id": "optional_detector_blank_transfer_input_rows",
                "path": display_path(OPTIONAL_TRANSFER_INPUT_ROWS),
                "exists": "true",
                "sha256": sha256_file(OPTIONAL_TRANSFER_INPUT_ROWS),
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "intake_rows": payload["intake_rows"],
        "route_transfer_matrix_rows": payload["route_transfer_matrix_rows"],
        "promotion_update_rows": payload["promotion_update_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    assembly_status = load_json(ASSEMBLY_STATUS)
    detector_panel_status = load_json(DETECTOR_PANEL_STATUS)
    panel_rows = read_csv_rows(DETECTOR_PANEL_MATRIX_ROWS)
    transfer_input_rows = (
        read_csv_rows(OPTIONAL_TRANSFER_INPUT_ROWS)
        if OPTIONAL_TRANSFER_INPUT_ROWS.exists()
        else []
    )
    intake_rows, matrix_rows = build_detector_blank_transfer_intake(
        panel_matrix_rows=panel_rows,
        transfer_input_rows=transfer_input_rows,
        artifact_root=PROJECT_ROOT,
    )
    template_rows = detector_blank_transfer_template_rows(panel_rows)
    promotion_updates = detector_blank_transfer_promotion_update_rows(matrix_rows)
    intake_dicts = [row.to_dict() for row in intake_rows]
    matrix_dicts = [row.to_dict() for row in matrix_rows]
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    accepted_rows = sum(row["accepted_transfer_current"] for row in intake_dicts)
    no_transfer_rows = sum(
        row["route_transfer_matrix_status"] == ROUTE_MATRIX_NO_TRANSFER_STATUS
        for row in matrix_dicts
    )
    accepted_matrix_rows = sum(
        row["route_transfer_matrix_status"] == ROUTE_MATRIX_ACCEPTED_STATUS
        for row in matrix_dicts
    )
    base_checks_pass = (
        source_missing == 0
        and release_dirty_blockers == 0
        and assembly_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_V2_READY_NOT_CLAIM_READY"
        and detector_panel_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_READY_CANDIDATE_NOT_PROBABILITY"
        and len(intake_dicts) == 2
        and len(matrix_dicts) == 2
        and len(template_rows) == 2
        and len(promotion_updates) == 2
        and all(row["detection_probability_current"] is False for row in intake_dicts)
        and all(row["route_score_current"] is False for row in intake_dicts)
    )
    if base_checks_pass and accepted_rows == 2 and accepted_matrix_rows == 2:
        status = ACCEPTED_DISPOSITION
    elif base_checks_pass and accepted_rows == 0 and no_transfer_rows == 2:
        status = DISPOSITION
    else:
        status = BLOCKED_DISPOSITION
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_assembly_disposition": assembly_status.get("disposition", ""),
        "source_detector_panel_disposition": detector_panel_status.get("disposition", ""),
        "optional_transfer_input_present": OPTIONAL_TRANSFER_INPUT_ROWS.exists(),
        "intake_rows": len(intake_dicts),
        "route_transfer_matrix_rows": len(matrix_dicts),
        "template_rows": len(template_rows),
        "promotion_update_rows": len(promotion_updates),
        "accepted_transfer_rows": accepted_rows,
        "no_transfer_matrix_rows": no_transfer_rows,
        "accepted_transfer_matrix_rows": accepted_matrix_rows,
        "sidewall_specific_blank_trace_current_rows": sum(
            row["sidewall_specific_blank_trace_current"] for row in intake_dicts
        ),
        "validated_transfer_current_rows": sum(
            row["accepted_transfer_current"]
            and row["blank_trace_geometry_match_level"] == "validated_transfer"
            for row in intake_dicts
        ),
        "detector_response_validation_current_rows": sum(
            row["detector_response_validation_current"] for row in intake_dicts
        ),
        "detection_probability_current": False,
        "route_score_current": False,
        "winner_current": False,
        "yield_current": False,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context" for row in dirty_context
        ),
        "release_scoped_dirty_blocker_rows": release_dirty_blockers,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "intake_rows": intake_dicts,
        "route_transfer_matrix_rows": matrix_dicts,
        "template_rows": template_rows,
        "promotion_update_rows": promotion_updates,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    accepted_mode = summary["accepted_transfer_rows"] == 2
    checks = {
        "disposition pass": summary["disposition"] in {DISPOSITION, ACCEPTED_DISPOSITION},
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "two intake rows": summary["intake_rows"] == 2,
        "two matrix rows": summary["route_transfer_matrix_rows"] == 2,
        "two template rows": summary["template_rows"] == 2,
        "two promotion updates": summary["promotion_update_rows"] == 2,
        "accepted count valid": summary["accepted_transfer_rows"] in {0, 2},
        "matrix count valid": (
            summary["accepted_transfer_matrix_rows"] == 2
            if accepted_mode
            else summary["no_transfer_matrix_rows"] == 2
        ),
        "detection false": summary["detection_probability_current"] is False,
        "route false": summary["route_score_current"] is False,
        "yield false": summary["yield_current"] is False,
    }
    for update in payload["promotion_update_rows"]:
        checks[f"update not final {update['target_ledger_lane']}"] = (
            update["target_claim_current"] is False
            and "detection_probability" in update["blocked_promotion"]
            and "route_score" in update["blocked_promotion"]
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    csv_payloads = {
        f"{PREFIX}_INTAKE_ROWS_20260701.csv": payload["intake_rows"],
        f"{PREFIX}_ROUTE_TRANSFER_MATRIX_ROWS_20260701.csv": payload[
            "route_transfer_matrix_rows"
        ],
        f"{PREFIX}_TEMPLATE_ROWS_20260701.csv": payload["template_rows"],
        f"{PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv": payload[
            "promotion_update_rows"
        ],
        f"{PREFIX}_SOURCE_LOCK_20260701.csv": payload["source_lock"],
        f"{PREFIX}_DIRTY_CONTEXT_20260701.csv": payload["dirty_context"],
    }
    for filename, rows in csv_payloads.items():
        path = OUTPUT_DIR / filename
        write_csv_rows(path, rows)
        paths.append(path)

    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(
        status_path,
        {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]},
    )
    paths.append(status_path)

    report_path = OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_path, payload)
    paths.append(report_path)

    public_report = (
        REPORT_DIR
        / "547_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_20260701.md"
    )
    public_report.write_text(report_markdown(payload), encoding="utf-8", newline="\n")
    paths.append(public_report)

    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv"
    write_csv_rows(manifest_path, manifest_rows(paths, manifest_path))
    paths.append(manifest_path)
    return paths


def report_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Sidewall Detector/Blank Transfer Intake",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Intake rows: `{s['intake_rows']}`.",
            f"- Route transfer matrix rows: `{s['route_transfer_matrix_rows']}`.",
            f"- Accepted transfer rows: `{s['accepted_transfer_rows']}`.",
            f"- Optional transfer input present: `{s['optional_transfer_input_present']}`.",
            "- Detection probability, route score, winner/JRC, and yield remain false.",
            "",
        ]
    )


def manifest_rows(paths: list[Path], manifest_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "artifact": path.name,
                "path": display_path(path),
                "sha256": sha256_file(path),
                "disposition": DISPOSITION,
                "policy_impact": "detector_blank_transfer_intake_not_claim",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    rows.append(
        {
            "artifact": manifest_path.name,
            "path": display_path(manifest_path),
            "sha256": SELF_MANIFEST_SHA256,
            "disposition": DISPOSITION,
            "policy_impact": "manifest_self_row_no_recursive_sha",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_sidewall_detector_blank_transfer_intake:
        parser.error("--confirm-sidewall-detector-blank-transfer-intake is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
