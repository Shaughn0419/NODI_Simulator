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
    TRANSFER_ACCEPTED_STATUS,
    TRANSFER_REJECTED_STATUS,
    build_detector_blank_transfer_intake,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_READY_NOT_PROBABILITY"
)
BLOCKED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_FAIL_CLOSED"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_CLAIM_BOUNDARY

ASSEMBLY_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_DETECTOR_BLANK_TRANSFER_REFRESH_STATUS_20260701.json"
)
ASSEMBLY_BRANCH_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_DETECTOR_BLANK_TRANSFER_REFRESH_BRANCH_ROWS_20260701.csv"
)
TRANSFER_INTAKE_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_STATUS_20260701.json"
)
TRANSFER_INTAKE_MATRIX_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_ROUTE_TRANSFER_MATRIX_ROWS_20260701.csv"
)
PANEL_MATRIX_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_ROUTE_EVIDENCE_MATRIX_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "detector/blank transfer validator hardening;accepted/rejected transfer fixture checks;"
    "future sidewall transfer evidence gate"
)
BLOCKED_USE = (
    "detection_probability;route_score;winner;JRC;yield;wet_pass_probability;"
    "production ingestion"
)

SOURCE_FILES = {
    "detector_blank_transfer_assembly_status": ASSEMBLY_STATUS,
    "detector_blank_transfer_assembly_branch_rows": ASSEMBLY_BRANCH_ROWS,
    "detector_blank_transfer_intake_status": TRANSFER_INTAKE_STATUS,
    "detector_blank_transfer_intake_matrix_rows": TRANSFER_INTAKE_MATRIX_ROWS,
    "detector_blank_panel_matrix_rows": PANEL_MATRIX_ROWS,
    "detector_blank_transfer_intake_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_detector_blank_transfer_intake.py",
    "detector_blank_transfer_intake_tests": PROJECT_ROOT
    / "tests/test_sidewall_detector_blank_transfer_intake.py",
    "detector_blank_transfer_validation_hardening_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_detector_blank_transfer_validation_hardening.py",
    "detector_blank_transfer_validation_hardening_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_detector_blank_transfer_validation_hardening.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_detector_blank_transfer_intake.py",
    "tests/test_sidewall_detector_blank_transfer_intake.py",
    "tools/audits/build_nodi_package_c_sidewall_detector_blank_transfer_validation_hardening.py",
    "tests/test_nodi_package_c_sidewall_detector_blank_transfer_validation_hardening.py",
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
        description="Build detector/blank transfer validation hardening packet."
    )
    parser.add_argument(
        "--confirm-sidewall-detector-blank-transfer-validation-hardening",
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
    return (
        path in source_paths
        or path in BUILD_EDIT_PATHS
        or path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_"
        )
        or path
        == "reports/551_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "detector_blank_transfer_validation_hardening_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_"
        ) or path == (
            "reports/551_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_20260701.md"
        ):
            classification = "detector_blank_transfer_validation_hardening_output"
            release_decision = (
                "included_or_rewritten_by_detector_blank_transfer_validation_hardening"
            )
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_detector_blank_transfer_validation_hardening"
        else:
            classification = "non_release_dirty_context"
            release_decision = (
                "ignored_for_detector_blank_transfer_validation_hardening_not_source_locked"
            )
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
    return rows


def _complete_transfer_row(
    route_candidate_id: str,
    *,
    geometry_match: str = "sidewall_specific",
    blank_sha: str = "a" * 64,
    detector_sha: str = "b" * 64,
    fpr: str = "0.0001",
    ci_low: str = "0.0",
    ci_high: str = "0.0004",
    n_blank: str = "3",
    n_detector: str = "3",
    controls: str = "controls_pass",
    pre_registered: str = "pre_registered",
) -> dict[str, str]:
    return {
        "route_candidate_id": route_candidate_id,
        "transfer_artifact_id": f"fixture-transfer-{route_candidate_id}",
        "blank_trace_artifact_id": f"fixture-blank-{route_candidate_id}",
        "blank_trace_sha256": blank_sha,
        "detector_response_artifact_id": f"fixture-detector-{route_candidate_id}",
        "detector_response_sha256": detector_sha,
        "blank_trace_geometry_match_level": geometry_match,
        "detector_response_model_id": "fixture-detector-response-v1",
        "false_positive_rate_estimate": fpr,
        "false_positive_rate_ci_low": ci_low,
        "false_positive_rate_ci_high": ci_high,
        "n_blank_traces": n_blank,
        "n_detector_calibration_runs": n_detector,
        "controls_status": controls,
        "uncertainty_model": "wilson_interval",
        "pre_registered_rule_status": pre_registered,
    }


def accepted_fixture_rows(panel_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    transfer_rows = [
        _complete_transfer_row("ROUTE-CAND-001", geometry_match="sidewall_specific"),
        _complete_transfer_row("ROUTE-CAND-002", geometry_match="validated_transfer"),
    ]
    intake_rows, matrix_rows = build_detector_blank_transfer_intake(
        panel_matrix_rows=panel_rows,
        transfer_input_rows=transfer_rows,
    )
    return [
        {
            "fixture_id": f"ACCEPTED-{row.route_candidate_id}",
            "route_candidate_id": row.route_candidate_id,
            "geometry_match_level": row.blank_trace_geometry_match_level,
            "transfer_validation_status": row.transfer_validation_status,
            "transfer_rejection_reason": row.transfer_rejection_reason,
            "route_transfer_matrix_status": next(
                matrix.route_transfer_matrix_status
                for matrix in matrix_rows
                if matrix.route_candidate_id == row.route_candidate_id
            ),
            "accepted_transfer_current": row.accepted_transfer_current,
            "detection_probability_current": row.detection_probability_current,
            "route_score_current": row.route_score_current,
            "yield_current": row.yield_current,
            "claim_boundary": row.claim_boundary,
        }
        for row in intake_rows
    ]


def negative_control_rows(panel_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    controls = [
        ("bad_blank_sha", _complete_transfer_row("ROUTE-CAND-001", blank_sha="not-a-sha")),
        (
            "bad_fpr_ci_order",
            _complete_transfer_row("ROUTE-CAND-001", fpr="0.001", ci_low="0.002", ci_high="0.003"),
        ),
        (
            "low_blank_trace_count",
            _complete_transfer_row("ROUTE-CAND-001", n_blank="2"),
        ),
        (
            "controls_missing",
            _complete_transfer_row("ROUTE-CAND-001", controls="controls_missing"),
        ),
    ]
    rows: list[dict[str, Any]] = []
    one_panel = [row for row in panel_rows if row.get("route_candidate_id") == "ROUTE-CAND-001"]
    for control_id, transfer in controls:
        intake_rows, matrix_rows = build_detector_blank_transfer_intake(
            panel_matrix_rows=one_panel,
            transfer_input_rows=[transfer],
        )
        intake = intake_rows[0]
        matrix = matrix_rows[0]
        rows.append(
            {
                "negative_control_id": control_id,
                "route_candidate_id": intake.route_candidate_id,
                "transfer_validation_status": intake.transfer_validation_status,
                "transfer_rejection_reason": intake.transfer_rejection_reason,
                "route_transfer_matrix_status": matrix.route_transfer_matrix_status,
                "accepted_transfer_current": intake.accepted_transfer_current,
                "detection_probability_current": intake.detection_probability_current,
                "route_score_current": intake.route_score_current,
                "claim_boundary": intake.claim_boundary,
            }
        )
    return rows


def current_intake_audit_rows() -> list[dict[str, Any]]:
    rows = read_csv_rows(TRANSFER_INTAKE_MATRIX_ROWS)
    return [
        {
            "audit_row_id": f"CURRENT-TRANSFER-{row['route_candidate_id']}",
            "route_candidate_id": row["route_candidate_id"],
            "route_transfer_matrix_status": row["route_transfer_matrix_status"],
            "accepted_transfer_count": row["accepted_transfer_count"],
            "missing_transfer_count": row["missing_transfer_count"],
            "detection_probability_current": row["detection_probability_current"],
            "route_score_current": row["route_score_current"],
            "yield_current": row["yield_current"],
            "claim_boundary": row["claim_boundary"],
        }
        for row in rows
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "accepted_fixture_rows": payload["accepted_fixture_rows"],
        "negative_control_rows": payload["negative_control_rows"],
        "current_intake_audit_rows": payload["current_intake_audit_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    assembly_status = load_json(ASSEMBLY_STATUS)
    transfer_status = load_json(TRANSFER_INTAKE_STATUS)
    panel_rows = read_csv_rows(PANEL_MATRIX_ROWS)
    accepted_rows = accepted_fixture_rows(panel_rows)
    negative_rows = negative_control_rows(panel_rows)
    current_rows = current_intake_audit_rows()
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and assembly_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_DETECTOR_BLANK_TRANSFER_REFRESH_READY_NOT_CLAIM_READY"
        and transfer_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_READY_SCHEMA_NO_TRANSFER_EVIDENCE"
        and len(accepted_rows) == 2
        and all(row["transfer_validation_status"] == TRANSFER_ACCEPTED_STATUS for row in accepted_rows)
        and all(row["route_transfer_matrix_status"] == ROUTE_MATRIX_ACCEPTED_STATUS for row in accepted_rows)
        and len(negative_rows) == 4
        and all(row["transfer_validation_status"] == TRANSFER_REJECTED_STATUS for row in negative_rows)
        and all(row["route_transfer_matrix_status"] == ROUTE_MATRIX_NO_TRANSFER_STATUS for row in negative_rows)
        and len(current_rows) == 2
        and all(row["route_transfer_matrix_status"] == ROUTE_MATRIX_NO_TRANSFER_STATUS for row in current_rows)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_assembly_disposition": assembly_status.get("disposition", ""),
        "source_transfer_intake_disposition": transfer_status.get("disposition", ""),
        "accepted_fixture_rows": len(accepted_rows),
        "negative_control_rows": len(negative_rows),
        "current_intake_audit_rows": len(current_rows),
        "current_no_transfer_rows": sum(
            row["route_transfer_matrix_status"] == ROUTE_MATRIX_NO_TRANSFER_STATUS
            for row in current_rows
        ),
        "fixture_detection_probability_current_rows": sum(
            row["detection_probability_current"] for row in accepted_rows
        ),
        "fixture_route_score_current_rows": sum(
            row["route_score_current"] for row in accepted_rows
        ),
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
        "accepted_fixture_rows": accepted_rows,
        "negative_control_rows": negative_rows,
        "current_intake_audit_rows": current_rows,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    checks = {
        "disposition pass": s["disposition"] == DISPOSITION,
        "source lock complete": s["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": s["release_scoped_dirty_blocker_rows"] == 0,
        "two accepted fixtures": s["accepted_fixture_rows"] == 2,
        "four negative controls": s["negative_control_rows"] == 4,
        "two current audit rows": s["current_intake_audit_rows"] == 2,
        "current no transfer rows": s["current_no_transfer_rows"] == 2,
        "fixture no probability": s["fixture_detection_probability_current_rows"] == 0,
        "fixture no route score": s["fixture_route_score_current_rows"] == 0,
    }
    expected_reasons = {
        "invalid_blank_trace_sha256",
        "invalid_false_positive_ci_order",
        "insufficient_blank_trace_count",
        "controls_not_pass",
    }
    checks["negative reasons complete"] = {
        row["transfer_rejection_reason"] for row in payload["negative_control_rows"]
    } == expected_reasons
    for row in payload["accepted_fixture_rows"]:
        checks[f"accepted not claim {row['fixture_id']}"] = (
            row["accepted_transfer_current"] is True
            and row["detection_probability_current"] is False
            and row["route_score_current"] is False
            and row["yield_current"] is False
        )
    for row in payload["negative_control_rows"]:
        checks[f"negative blocked {row['negative_control_id']}"] = (
            row["accepted_transfer_current"] is False
            and row["detection_probability_current"] is False
            and row["route_score_current"] is False
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    csv_payloads = {
        f"{PREFIX}_ACCEPTED_FIXTURE_ROWS_20260701.csv": payload["accepted_fixture_rows"],
        f"{PREFIX}_NEGATIVE_CONTROL_ROWS_20260701.csv": payload["negative_control_rows"],
        f"{PREFIX}_CURRENT_INTAKE_AUDIT_ROWS_20260701.csv": payload[
            "current_intake_audit_rows"
        ],
        f"{PREFIX}_SOURCE_LOCK_20260701.csv": payload["source_lock"],
        f"{PREFIX}_DIRTY_CONTEXT_20260701.csv": payload["dirty_context"],
    }
    for filename, rows in csv_payloads.items():
        path = OUTPUT_DIR / filename
        write_csv_rows(path, rows)
        paths.append(path)

    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(status_path, {"disposition": DISPOSITION, "summary": payload["summary"]})
    paths.append(status_path)

    report_path = OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_path, payload)
    paths.append(report_path)

    public_report = (
        REPORT_DIR
        / "551_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_20260701.md"
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
            "# NODI Package C Sidewall Detector/Blank Transfer Validation Hardening",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Accepted transfer fixture rows: `{s['accepted_fixture_rows']}`.",
            f"- Negative control rows: `{s['negative_control_rows']}`.",
            f"- Current no-transfer audit rows: `{s['current_no_transfer_rows']}`.",
            "- This hardens transfer validation for sha256, false-positive CI, sample counts, controls, and preregistered rules.",
            "- Accepted fixtures prove validator behavior only; current real transfer evidence remains absent.",
            "- Detection probability, route score, winner/JRC, yield, and wet pass probability remain false.",
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
                "policy_impact": "detector_blank_transfer_validation_hardening_not_claim",
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
    if not args.confirm_sidewall_detector_blank_transfer_validation_hardening:
        parser.error(
            "--confirm-sidewall-detector-blank-transfer-validation-hardening is required"
        )
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
