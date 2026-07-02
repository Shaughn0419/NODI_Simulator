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
from nodi_simulator.sidewall_wet_surface_observation_intake import (  # noqa: E402
    ROUTE_MATRIX_NO_OBSERVATIONS_STATUS,
    SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_CLAIM_BOUNDARY,
    SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_VERSION,
    build_wet_surface_observation_intake,
    wet_surface_observation_promotion_update_rows,
    wet_surface_observation_template_rows,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_READY_SCHEMA_NO_OBSERVATIONS"
)
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_CLAIM_BOUNDARY

DETECTOR_BLANK_PANEL_LEDGER_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_PANEL_REFRESH_STATUS_20260701.json"
)
DETECTOR_BLANK_PANEL_LEDGER_LANES = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_PANEL_REFRESH_PROMOTION_LANE_ROWS_20260701.csv"
)
WET_CONTRACT_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_STATUS_20260701.json"
)
WET_CONTRACT_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_CONTRACT_ROWS_20260701.csv"
)
OPTIONAL_OBSERVATION_INPUT_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INPUT_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "wet/surface observation intake schema;wet endpoint validation;"
    "route wet evidence matrix planning"
)
BLOCKED_USE = (
    "wet_pass_probability;clogging_rate;time_to_clog;recovery;yield;"
    "detection_probability;route_score;winner;JRC;production ingestion"
)

SOURCE_FILES = {
    "detector_blank_panel_ledger_status": DETECTOR_BLANK_PANEL_LEDGER_STATUS,
    "detector_blank_panel_ledger_lanes": DETECTOR_BLANK_PANEL_LEDGER_LANES,
    "wet_surface_contract_status": WET_CONTRACT_STATUS,
    "wet_surface_contract_rows": WET_CONTRACT_ROWS,
    "wet_surface_observation_intake_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_wet_surface_observation_intake.py",
    "wet_surface_observation_intake_tests": PROJECT_ROOT
    / "tests/test_sidewall_wet_surface_observation_intake.py",
    "wet_surface_observation_intake_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_wet_surface_observation_intake.py",
    "wet_surface_observation_intake_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_wet_surface_observation_intake.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_wet_surface_observation_intake.py",
    "tests/test_sidewall_wet_surface_observation_intake.py",
    "tools/audits/build_nodi_package_c_sidewall_wet_surface_observation_intake.py",
    "tests/test_nodi_package_c_sidewall_wet_surface_observation_intake.py",
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
        description="Build sidewall wet/surface observation intake packet."
    )
    parser.add_argument(
        "--confirm-sidewall-wet-surface-observation-intake",
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
            "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_"
        )
        or path
        == "reports/543_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "wet_surface_observation_intake_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_"
        ) or path == (
            "reports/543_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_20260701.md"
        ):
            classification = "wet_surface_observation_intake_output"
            release_decision = "included_or_rewritten_by_wet_surface_observation_intake"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_wet_surface_observation_intake"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_wet_surface_observation_intake_not_source_locked"
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
    if OPTIONAL_OBSERVATION_INPUT_ROWS.exists():
        rows.append(
            {
                "source_id": "optional_wet_surface_observation_input_rows",
                "path": display_path(OPTIONAL_OBSERVATION_INPUT_ROWS),
                "exists": "true",
                "sha256": sha256_file(OPTIONAL_OBSERVATION_INPUT_ROWS),
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def _stringify_row(row: dict[str, Any]) -> dict[str, str]:
    return {key: _stringify(value) for key, value in row.items()}


def _stringify(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def observation_rows() -> list[dict[str, str]]:
    if not OPTIONAL_OBSERVATION_INPUT_ROWS.exists():
        return []
    return read_csv_rows(OPTIONAL_OBSERVATION_INPUT_ROWS)


def intake_payload_rows() -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
]:
    contract_rows = read_csv_rows(WET_CONTRACT_ROWS)
    intake_rows, matrix_rows = build_wet_surface_observation_intake(
        contract_rows=contract_rows,
        observation_rows=observation_rows(),
    )
    updates = wet_surface_observation_promotion_update_rows(matrix_rows)
    templates = wet_surface_observation_template_rows(contract_rows)
    return (
        [_stringify_row(row.to_dict()) for row in intake_rows],
        [_stringify_row(row.to_dict()) for row in matrix_rows],
        [_stringify_row(row) for row in updates],
        templates,
    )


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "intake_rows": payload["intake_rows"],
        "route_observation_matrix_rows": payload["route_observation_matrix_rows"],
        "promotion_update_rows": payload["promotion_update_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    detector_blank_panel_status = load_json(DETECTOR_BLANK_PANEL_LEDGER_STATUS)
    wet_contract_status = load_json(WET_CONTRACT_STATUS)
    intake_rows, matrix_rows, updates, templates = intake_payload_rows()
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    matrix_no_observations = sum(
        row["route_wet_observation_matrix_status"] == ROUTE_MATRIX_NO_OBSERVATIONS_STATUS
        for row in matrix_rows
    )
    accepted_observations = sum(
        row["accepted_observation_current"] == "true" for row in intake_rows
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and detector_blank_panel_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_PANEL_REFRESH_READY_PREFLIGHT_ONLY"
        and wet_contract_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_READY_CONTRACT_ONLY"
        and len(intake_rows) == 14
        and len(matrix_rows) == 2
        and len(updates) == 1
        and len(templates) == 14
        and matrix_no_observations == 2
        and accepted_observations == 0
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "intake_version": SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_VERSION,
        "source_detector_blank_panel_ledger_disposition": detector_blank_panel_status.get(
            "disposition", ""
        ),
        "source_wet_surface_contract_disposition": wet_contract_status.get(
            "disposition", ""
        ),
        "optional_observation_input_present": OPTIONAL_OBSERVATION_INPUT_ROWS.exists(),
        "intake_rows": len(intake_rows),
        "route_observation_matrix_rows": len(matrix_rows),
        "template_rows": len(templates),
        "promotion_update_rows": len(updates),
        "accepted_observation_rows": accepted_observations,
        "no_observation_matrix_rows": matrix_no_observations,
        "wet_pass_probability_current": False,
        "clogging_rate_current": False,
        "time_to_clog_current": False,
        "recovery_current": False,
        "yield_current": False,
        "detection_probability_current": False,
        "route_score_current": False,
        "winner_current": False,
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
        "intake_rows": intake_rows,
        "route_observation_matrix_rows": matrix_rows,
        "promotion_update_rows": updates,
        "observation_template_rows": templates,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "fourteen intake rows": summary["intake_rows"] == 14,
        "two matrix rows": summary["route_observation_matrix_rows"] == 2,
        "fourteen template rows": summary["template_rows"] == 14,
        "one promotion update": summary["promotion_update_rows"] == 1,
        "no accepted observations": summary["accepted_observation_rows"] == 0,
        "two no-observation matrix rows": summary["no_observation_matrix_rows"] == 2,
        "yield false": summary["yield_current"] is False,
        "wet pass false": summary["wet_pass_probability_current"] is False,
        "detection false": summary["detection_probability_current"] is False,
        "route false": summary["route_score_current"] is False,
    }
    for row in payload["route_observation_matrix_rows"]:
        checks[f"matrix no claim {row['matrix_row_id']}"] = (
            row["route_wet_observation_matrix_status"] == ROUTE_MATRIX_NO_OBSERVATIONS_STATUS
            and row["yield_current"] == "false"
            and row["wet_pass_probability_current"] == "false"
            and row["detection_probability_current"] == "false"
            and row["route_score_current"] == "false"
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    csv_payloads = {
        f"{PREFIX}_INTAKE_ROWS_20260701.csv": payload["intake_rows"],
        f"{PREFIX}_ROUTE_OBSERVATION_MATRIX_ROWS_20260701.csv": payload[
            "route_observation_matrix_rows"
        ],
        f"{PREFIX}_OBSERVATION_TEMPLATE_ROWS_20260701.csv": payload[
            "observation_template_rows"
        ],
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
    write_json_atomic(status_path, {"disposition": DISPOSITION, "summary": payload["summary"]})
    paths.append(status_path)

    report_path = OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_path, payload)
    paths.append(report_path)

    public_report = (
        REPORT_DIR / "543_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_20260701.md"
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
            "# NODI Package C Sidewall Wet/Surface Observation Intake",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Intake rows: `{s['intake_rows']}`.",
            f"- Route observation matrix rows: `{s['route_observation_matrix_rows']}`.",
            f"- Observation template rows: `{s['template_rows']}`.",
            "- No sidewall wet observations are present in this packet.",
            "- Wet pass probability, clogging, recovery, yield, detection probability, and route score remain false.",
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
                "policy_impact": "wet_surface_observation_intake_schema_not_claim",
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
    if not args.confirm_sidewall_wet_surface_observation_intake:
        parser.error("--confirm-sidewall-wet-surface-observation-intake is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
