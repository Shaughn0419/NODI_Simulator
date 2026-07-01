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
from nodi_simulator.sidewall_detector_blank_calibration_panel import (  # noqa: E402
    PANEL_AGGREGATE_READY_STATUS,
    PANEL_READY_STATUS,
    SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_CLAIM_BOUNDARY,
    SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_VERSION,
    SidewallDetectorBlankCalibrationPanelConfig,
    build_detector_blank_calibration_panel,
    detector_blank_calibration_promotion_update_rows,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_READY_CANDIDATE_NOT_PROBABILITY"
)
BLOCKED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_FAIL_CLOSED"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_CLAIM_BOUNDARY

DETECTOR_CONTEXT_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_STATUS_20260701.json"
)
DETECTOR_CONTEXT_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_CONTEXT_ROWS_20260701.csv"
)
ROUTE_POLICY_REFRESH_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_STATUS_20260701.json"
)

ALLOWED_USE = (
    "detector/blank calibration candidate panel;selected-annulus expansion;"
    "route evidence matrix planning"
)
BLOCKED_USE = (
    "detection_probability;route_score;winner;JRC;yield;wet_pass_probability;"
    "sidewall_specific_blank_fpr;detector_response_validation;production ingestion"
)

PANEL_CONFIG = SidewallDetectorBlankCalibrationPanelConfig(
    n_events_per_run=64,
    random_seeds=(601, 602, 603),
    wavelength_nm=(404, 660),
    min_selected_annulus_events_per_route=50,
    blank_false_positive_ub_threshold_per_trace=0.001,
)

SOURCE_FILES = {
    "detector_blank_context_status": DETECTOR_CONTEXT_STATUS,
    "detector_blank_context_rows": DETECTOR_CONTEXT_ROWS,
    "route_policy_refresh_status": ROUTE_POLICY_REFRESH_STATUS,
    "detector_blank_calibration_panel_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_detector_blank_calibration_panel.py",
    "detector_blank_calibration_panel_tests": PROJECT_ROOT
    / "tests/test_sidewall_detector_blank_calibration_panel.py",
    "detector_blank_calibration_panel_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_detector_blank_calibration_panel.py",
    "detector_blank_calibration_panel_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_detector_blank_calibration_panel.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_detector_blank_calibration_panel.py",
    "tests/test_sidewall_detector_blank_calibration_panel.py",
    "tools/audits/build_nodi_package_c_sidewall_detector_blank_calibration_panel.py",
    "tests/test_nodi_package_c_sidewall_detector_blank_calibration_panel.py",
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
        description="Build sidewall detector/blank calibration candidate panel."
    )
    parser.add_argument(
        "--confirm-sidewall-detector-blank-calibration-panel",
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
            "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_"
        )
        or path
        == "reports/541_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "detector_blank_calibration_panel_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_"
        ) or path == (
            "reports/541_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_20260701.md"
        ):
            classification = "detector_blank_calibration_panel_output"
            release_decision = (
                "included_or_rewritten_by_detector_blank_calibration_panel"
            )
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_detector_blank_calibration_panel"
        else:
            classification = "non_release_dirty_context"
            release_decision = (
                "ignored_for_detector_blank_calibration_panel_not_source_locked"
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


def _stringify_row(row: dict[str, Any]) -> dict[str, str]:
    return {key: _stringify(value) for key, value in row.items()}


def _stringify(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        if value != value:
            return "nan"
        return f"{value:.12g}"
    return str(value)


def panel_payload_rows() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    panel_rows, matrix_rows = build_detector_blank_calibration_panel(
        detector_blank_context_rows=read_csv_rows(DETECTOR_CONTEXT_ROWS),
        config=PANEL_CONFIG,
    )
    updates = detector_blank_calibration_promotion_update_rows(matrix_rows)
    return (
        [_stringify_row(row.to_dict()) for row in panel_rows],
        [_stringify_row(row.to_dict()) for row in matrix_rows],
        [_stringify_row(row) for row in updates],
    )


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "panel_rows": payload["panel_rows"],
        "route_evidence_matrix_rows": payload["route_evidence_matrix_rows"],
        "promotion_update_rows": payload["promotion_update_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    detector_context_status = load_json(DETECTOR_CONTEXT_STATUS)
    route_policy_status = load_json(ROUTE_POLICY_REFRESH_STATUS)
    panel_rows, matrix_rows, updates = panel_payload_rows()
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    ready_panel_rows = sum(
        row["panel_evidence_status"] == PANEL_READY_STATUS for row in panel_rows
    )
    ready_matrix_rows = sum(
        row["route_evidence_matrix_status"] == PANEL_AGGREGATE_READY_STATUS
        for row in matrix_rows
    )
    total_selected = sum(
        int(row["total_selected_annulus_events"]) for row in matrix_rows
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and detector_context_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_READY_CONTEXT_ONLY"
        and route_policy_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_READY_PREFLIGHT_ONLY"
        and len(panel_rows) == 12
        and len(matrix_rows) == 2
        and len(updates) == 3
        and ready_panel_rows == 12
        and ready_matrix_rows == 2
        and all(row["detection_probability_current"] == "false" for row in panel_rows)
        and all(row["route_score_current"] == "false" for row in matrix_rows)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "panel_version": SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_VERSION,
        "source_detector_blank_context_disposition": detector_context_status.get(
            "disposition", ""
        ),
        "source_route_policy_refresh_disposition": route_policy_status.get(
            "disposition", ""
        ),
        "panel_rows": len(panel_rows),
        "route_evidence_matrix_rows": len(matrix_rows),
        "promotion_update_rows": len(updates),
        "ready_panel_rows": ready_panel_rows,
        "ready_route_evidence_matrix_rows": ready_matrix_rows,
        "n_events_per_run": PANEL_CONFIG.n_events_per_run,
        "random_seed_count": len(PANEL_CONFIG.random_seeds),
        "wavelength_count": len(PANEL_CONFIG.wavelength_nm),
        "total_selected_annulus_events": total_selected,
        "sidewall_specific_blank_trace_current": False,
        "detector_response_validation_current": False,
        "sidewall_specific_optical_calibration_current": False,
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
        "panel_rows": panel_rows,
        "route_evidence_matrix_rows": matrix_rows,
        "promotion_update_rows": updates,
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
        "twelve panel rows": summary["panel_rows"] == 12,
        "two matrix rows": summary["route_evidence_matrix_rows"] == 2,
        "three promotion updates": summary["promotion_update_rows"] == 3,
        "all panel rows ready": summary["ready_panel_rows"] == 12,
        "all matrix rows ready": summary["ready_route_evidence_matrix_rows"] == 2,
        "detection false": summary["detection_probability_current"] is False,
        "route false": summary["route_score_current"] is False,
        "yield false": summary["yield_current"] is False,
    }
    for row in payload["route_evidence_matrix_rows"]:
        checks[f"matrix not final {row['matrix_row_id']}"] = (
            row["route_evidence_matrix_status"] == PANEL_AGGREGATE_READY_STATUS
            and row["detection_probability_current"] == "false"
            and row["route_score_current"] == "false"
            and row["yield_current"] == "false"
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    csv_payloads = {
        f"{PREFIX}_PANEL_ROWS_20260701.csv": payload["panel_rows"],
        f"{PREFIX}_ROUTE_EVIDENCE_MATRIX_ROWS_20260701.csv": payload[
            "route_evidence_matrix_rows"
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
        REPORT_DIR
        / "541_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_20260701.md"
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
            "# NODI Package C Sidewall Detector/Blank Calibration Panel",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Panel rows: `{s['panel_rows']}`.",
            f"- Route evidence matrix rows: `{s['route_evidence_matrix_rows']}`.",
            f"- Total selected-annulus events: `{s['total_selected_annulus_events']}`.",
            "- The panel expands selected-annulus evidence and binds a nearest-geometry blank guard.",
            "- Detection probability, route score, winner/JRC, yield, and wet-pass probability remain false.",
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
                "policy_impact": "detector_blank_calibration_candidate_not_probability",
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
    if not args.confirm_sidewall_detector_blank_calibration_panel:
        parser.error("--confirm-sidewall-detector-blank-calibration-panel is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
