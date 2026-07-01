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


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_PANEL_REFRESH"
ARTIFACT_ID = (
    "PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_PANEL_REFRESH_20260701"
)
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_PANEL_REFRESH_READY_PREFLIGHT_ONLY"
)
BLOCKED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_PANEL_REFRESH_FAIL_CLOSED"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = (
    "promotion_ledger_detector_blank_panel_refresh_not_detection_probability_not_route_score"
)

ROUTE_POLICY_REFRESH_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_STATUS_20260701.json"
)
ROUTE_POLICY_REFRESH_LANES = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_PROMOTION_LANE_ROWS_20260701.csv"
)
PANEL_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_STATUS_20260701.json"
)
PANEL_MATRIX_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_ROUTE_EVIDENCE_MATRIX_ROWS_20260701.csv"
)
PANEL_PROMOTION_UPDATE = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_PROMOTION_UPDATE_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "integrated promotion ledger detector/blank panel refresh;"
    "candidate route evidence matrix handoff"
)
BLOCKED_USE = (
    "detection_probability;route_score;winner;JRC;yield;wet_pass_probability;"
    "sidewall_specific_blank_fpr;detector_response_validation;production ingestion"
)

SOURCE_FILES = {
    "route_policy_refresh_status": ROUTE_POLICY_REFRESH_STATUS,
    "route_policy_refresh_lanes": ROUTE_POLICY_REFRESH_LANES,
    "detector_blank_calibration_panel_status": PANEL_STATUS,
    "detector_blank_calibration_panel_matrix_rows": PANEL_MATRIX_ROWS,
    "detector_blank_calibration_panel_promotion_update": PANEL_PROMOTION_UPDATE,
    "ledger_detector_blank_panel_refresh_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_integrated_promotion_ledger_detector_blank_panel_refresh.py",
    "ledger_detector_blank_panel_refresh_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_integrated_promotion_ledger_detector_blank_panel_refresh.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "tools/audits/build_nodi_package_c_sidewall_integrated_promotion_ledger_detector_blank_panel_refresh.py",
    "tests/test_nodi_package_c_sidewall_integrated_promotion_ledger_detector_blank_panel_refresh.py",
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
        description="Refresh integrated promotion ledger with detector/blank panel evidence."
    )
    parser.add_argument(
        "--confirm-sidewall-integrated-promotion-ledger-detector-blank-panel-refresh",
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
            "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_PANEL_REFRESH_"
        )
        or path
        == "reports/542_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_PANEL_REFRESH_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "integrated_detector_blank_panel_refresh_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_PANEL_REFRESH_"
        ) or path == (
            "reports/542_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_PANEL_REFRESH_20260701.md"
        ):
            classification = "integrated_detector_blank_panel_refresh_output"
            release_decision = (
                "included_or_rewritten_by_integrated_detector_blank_panel_refresh"
            )
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_integrated_detector_blank_panel_refresh"
        else:
            classification = "non_release_dirty_context"
            release_decision = (
                "ignored_for_integrated_detector_blank_panel_refresh_not_source_locked"
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


def promotion_update_rows_by_lane() -> dict[str, dict[str, str]]:
    rows = read_csv_rows(PANEL_PROMOTION_UPDATE)
    return {row["target_ledger_lane"]: row for row in rows}


def refreshed_promotion_lane_rows() -> list[dict[str, str]]:
    rows = read_csv_rows(ROUTE_POLICY_REFRESH_LANES)
    updates = promotion_update_rows_by_lane()
    matrix_sha = sha256_file(PANEL_MATRIX_ROWS)
    matrix_path = display_path(PANEL_MATRIX_ROWS)
    matrix_disposition = (
        "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_READY_CANDIDATE_NOT_PROBABILITY"
    )
    for row in rows:
        update = updates.get(row.get("evidence_lane", ""))
        if update is None:
            continue
        row["source_artifact"] = matrix_path
        row["source_sha256"] = matrix_sha
        row["source_disposition"] = matrix_disposition
        row["current_status"] = update["new_context_status"]
        row["required_before_promotion"] = update["next_required_evidence"]
        row["hard_fail_if_promoted_without"] = update["hard_fail_if"]
        row["next_required_evidence"] = update["next_required_evidence"]
    return rows


def refresh_delta_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    target_lanes = set(promotion_update_rows_by_lane())
    return [
        {
            "delta_id": f"DB-PANEL-REFRESH-{row['route_candidate_id']}-{row['evidence_lane']}",
            "route_candidate_id": row["route_candidate_id"],
            "evidence_lane": row["evidence_lane"],
            "new_current_status": row["current_status"],
            "source_artifact": row["source_artifact"],
            "target_claim": row["target_claim"],
            "target_claim_current": row["target_claim_current"],
            "blocked_use": BLOCKED_USE,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for row in rows
        if row.get("evidence_lane") in target_lanes
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "refreshed_promotion_lane_rows": payload["refreshed_promotion_lane_rows"],
        "refresh_delta_rows": payload["refresh_delta_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    route_policy_status = load_json(ROUTE_POLICY_REFRESH_STATUS)
    panel_status = load_json(PANEL_STATUS)
    lanes = refreshed_promotion_lane_rows()
    deltas = refresh_delta_rows(lanes)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    status_counts = {
        "expanded_selected_annulus_panel": sum(
            row["evidence_lane"] == "selected_annulus_detection_context"
            and row["current_status"]
            == "expanded_selected_annulus_panel_available_not_probability"
            for row in lanes
        ),
        "nearest_blank_guard_bound": sum(
            row["evidence_lane"] == "blank_false_positive_trace"
            and row["current_status"]
            == "nearest_blank_guard_bound_to_panel_not_sidewall_specific"
            for row in lanes
        ),
        "detector_response_panel_candidate": sum(
            row["evidence_lane"] == "detector_response_bridge"
            and row["current_status"]
            == "detector_response_panel_candidate_not_sidewall_calibrated"
            for row in lanes
        ),
        "formal_qch": sum(
            row["evidence_lane"] == "flow_split_qch"
            and row["current_status"]
            == "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting"
            for row in lanes
        ),
        "pressure_flow": sum(
            row["evidence_lane"] == "pressure_flow_validation"
            and row["current_status"]
            == "exact_w500_d900_pressure_flow_result_accepted_formal_qch_sidecar_ready"
            for row in lanes
        ),
        "wet_contract": sum(
            row["evidence_lane"] == "wet_wall_interaction"
            and row["current_status"] == "wet_surface_evidence_contract_defined_no_wet_validation"
            for row in lanes
        ),
    }
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and route_policy_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_READY_PREFLIGHT_ONLY"
        and panel_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_READY_CANDIDATE_NOT_PROBABILITY"
        and len(lanes) == 18
        and len(deltas) == 6
        and all(count == 2 for count in status_counts.values())
        and all(row["target_claim_current"] == "false" for row in deltas)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_route_policy_refresh_disposition": route_policy_status.get(
            "disposition", ""
        ),
        "source_detector_blank_panel_disposition": panel_status.get("disposition", ""),
        "refreshed_promotion_lane_rows": len(lanes),
        "detector_blank_panel_delta_rows": len(deltas),
        "expanded_selected_annulus_panel_rows": status_counts[
            "expanded_selected_annulus_panel"
        ],
        "nearest_blank_guard_bound_rows": status_counts["nearest_blank_guard_bound"],
        "detector_response_panel_candidate_rows": status_counts[
            "detector_response_panel_candidate"
        ],
        "formal_qch_lane_rows_retained": status_counts["formal_qch"],
        "pressure_flow_validation_rows_retained": status_counts["pressure_flow"],
        "wet_surface_contract_defined_rows_retained": status_counts["wet_contract"],
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
        "refreshed_promotion_lane_rows": lanes,
        "refresh_delta_rows": deltas,
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
        "eighteen lane rows": summary["refreshed_promotion_lane_rows"] == 18,
        "six panel deltas": summary["detector_blank_panel_delta_rows"] == 6,
        "selected expanded": summary["expanded_selected_annulus_panel_rows"] == 2,
        "blank guard bound": summary["nearest_blank_guard_bound_rows"] == 2,
        "detector panel candidate": summary["detector_response_panel_candidate_rows"] == 2,
        "formal qch retained": summary["formal_qch_lane_rows_retained"] == 2,
        "pressure retained": summary["pressure_flow_validation_rows_retained"] == 2,
        "wet retained": summary["wet_surface_contract_defined_rows_retained"] == 2,
        "detection false": summary["detection_probability_current"] is False,
        "route false": summary["route_score_current"] is False,
        "yield false": summary["yield_current"] is False,
    }
    for row in payload["refresh_delta_rows"]:
        checks[f"delta not final {row['delta_id']}"] = (
            row["target_claim_current"] == "false"
            and "detection_probability" in row["blocked_use"]
            and "route_score" in row["blocked_use"]
            and "yield" in row["blocked_use"]
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    csv_payloads = {
        f"{PREFIX}_PROMOTION_LANE_ROWS_20260701.csv": payload[
            "refreshed_promotion_lane_rows"
        ],
        f"{PREFIX}_DELTA_ROWS_20260701.csv": payload["refresh_delta_rows"],
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
        / "542_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_PANEL_REFRESH_20260701.md"
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
            "# NODI Package C Sidewall Integrated Promotion Ledger Detector/Blank Panel Refresh",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Refreshed promotion lane rows: `{s['refreshed_promotion_lane_rows']}`.",
            f"- Detector/blank panel delta rows: `{s['detector_blank_panel_delta_rows']}`.",
            "- Selected-annulus, blank, and detector bridge lanes now point to the 541 panel matrix.",
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
                "policy_impact": "integrated_detector_blank_panel_refresh_not_probability",
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
    if not args.confirm_sidewall_integrated_promotion_ledger_detector_blank_panel_refresh:
        parser.error(
            "--confirm-sidewall-integrated-promotion-ledger-detector-blank-panel-refresh is required"
        )
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_PANEL_REFRESH")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
