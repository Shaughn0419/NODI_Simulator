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

PREFIX = "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_FORMAL_QCH_REFRESH"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_FORMAL_QCH_REFRESH_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_FORMAL_QCH_REFRESH_READY_PREFLIGHT_ONLY"
)
BLOCKED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_FORMAL_QCH_REFRESH_FAIL_CLOSED"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = "promotion_ledger_formal_qch_refresh_not_route_score_not_yield_not_detection"

ROUTE_POLICY_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_STATUS_20260701.json"
)
ROUTE_POLICY_LANES = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_PROMOTION_LANE_ROWS_20260701.csv"
)
FORMAL_QCH_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_STATUS_20260701.json"
)
FORMAL_QCH_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_FORMAL_QCH_SIDECAR_ROWS_20260701.csv"
)
BINDING_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_BINDING_ROWS_20260701.csv"
)
PROMOTION_UPDATE_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_PROMOTION_UPDATE_ROWS_20260701.csv"
)

ALLOWED_USE = "integrated promotion ledger formal qch refresh;next-evidence prioritization"
BLOCKED_USE = (
    "route_score;winner;JRC;q_ch_weighting;yield;detection_probability;"
    "wet_pass_probability;clogging_rate;time_to_clog;recovery;production ingestion"
)

SOURCE_FILES = {
    "route_policy_refresh_status": ROUTE_POLICY_STATUS,
    "route_policy_refresh_lanes": ROUTE_POLICY_LANES,
    "formal_qch_binder_status": FORMAL_QCH_STATUS,
    "formal_qch_sidecar_rows": FORMAL_QCH_ROWS,
    "formal_qch_binding_rows": BINDING_ROWS,
    "formal_qch_promotion_update": PROMOTION_UPDATE_ROWS,
    "formal_qch_refresh_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_integrated_promotion_ledger_formal_qch_refresh.py",
    "formal_qch_refresh_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_integrated_promotion_ledger_formal_qch_refresh.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "tools/audits/build_nodi_package_c_sidewall_integrated_promotion_ledger_formal_qch_refresh.py",
    "tests/test_nodi_package_c_sidewall_integrated_promotion_ledger_formal_qch_refresh.py",
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
        description="Refresh integrated promotion ledger with formal q_ch pressure-flow binder evidence."
    )
    parser.add_argument(
        "--confirm-sidewall-integrated-promotion-ledger-formal-qch-refresh",
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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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
            "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_FORMAL_QCH_REFRESH_"
        )
        or path
        == "reports/544_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_FORMAL_QCH_REFRESH_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "formal_qch_refresh_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_FORMAL_QCH_REFRESH_"
        ) or path == (
            "reports/544_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_"
            "FORMAL_QCH_REFRESH_20260701.md"
        ):
            classification = "formal_qch_refresh_output"
            release_decision = "included_or_rewritten_by_formal_qch_refresh"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_formal_qch_refresh"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_formal_qch_refresh_not_source_locked"
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


def promotion_update_row() -> dict[str, str]:
    rows = read_csv_rows(PROMOTION_UPDATE_ROWS)
    return rows[0] if len(rows) == 1 else {}


def refreshed_promotion_lane_rows() -> list[dict[str, str]]:
    rows = read_csv_rows(ROUTE_POLICY_LANES)
    binder_status = load_json(FORMAL_QCH_STATUS).get("disposition", "")
    qch_path = display_path(FORMAL_QCH_ROWS)
    qch_sha = sha256_file(FORMAL_QCH_ROWS) if FORMAL_QCH_ROWS.exists() else ""
    binding_path = display_path(BINDING_ROWS)
    binding_sha = sha256_file(BINDING_ROWS) if BINDING_ROWS.exists() else ""
    update = promotion_update_row()
    for row in rows:
        lane = row.get("evidence_lane")
        if lane == "flow_split_qch":
            row["source_artifact"] = qch_path
            row["source_sha256"] = qch_sha
            row["source_disposition"] = binder_status
            row["current_status"] = (
                "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting"
            )
            row["required_before_promotion"] = (
                "detector/blank calibration, wet/surface validation, and explicit route policy before route scoring"
            )
            row["hard_fail_if_promoted_without"] = (
                "formal_qch_sidecar_promoted_to_route_score_without_detector_wet_policy"
            )
            row["next_required_evidence"] = (
                "detector/blank calibration plus wet/surface validation and explicit route selection policy"
            )
        elif lane == "pressure_flow_validation":
            row["source_artifact"] = binding_path
            row["source_sha256"] = binding_sha
            row["source_disposition"] = binder_status
            row["current_status"] = update.get(
                "new_context_status",
                "exact_w500_d900_pressure_flow_result_accepted_formal_qch_sidecar_ready",
            )
            row["required_before_promotion"] = (
                "route policy plus calibrated detector/wet/yield evidence"
            )
            row["hard_fail_if_promoted_without"] = update.get(
                "hard_fail_if",
                "formal_qch_sidecar_promoted_to_route_score_without_route_policy_and_detection_yield_evidence",
            )
            row["next_required_evidence"] = update.get(
                "next_required_evidence",
                "route policy plus calibrated detector/wet/yield evidence",
            )
    return rows


def refresh_delta_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "delta_id": f"FORMAL-QCH-REFRESH-{row['route_candidate_id']}-{row['evidence_lane']}",
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
        if row.get("evidence_lane") in {"flow_split_qch", "pressure_flow_validation"}
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "refreshed_promotion_lane_rows": payload["refreshed_promotion_lane_rows"],
        "refresh_delta_rows": payload["refresh_delta_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    route_policy_status = load_json(ROUTE_POLICY_STATUS)
    binder_status = load_json(FORMAL_QCH_STATUS)
    lanes = refreshed_promotion_lane_rows()
    deltas = refresh_delta_rows(lanes)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    qch_formal = sum(
        row["evidence_lane"] == "flow_split_qch"
        and row["current_status"]
        == "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting"
        for row in lanes
    )
    pressure_accepted = sum(
        row["evidence_lane"] == "pressure_flow_validation"
        and row["current_status"]
        == "exact_w500_d900_pressure_flow_result_accepted_formal_qch_sidecar_ready"
        for row in lanes
    )
    retained_next = {
        "selected_annulus": sum(
            row["evidence_lane"] == "selected_annulus_detection_context"
            and row["current_status"] == "selected_annulus_context_available_small_n_not_probability"
            for row in lanes
        ),
        "detector": sum(
            row["evidence_lane"] == "detector_response_bridge"
            and row["current_status"]
            == "detector_identity_context_available_not_sidewall_response_validation"
            for row in lanes
        ),
        "blank": sum(
            row["evidence_lane"] == "blank_false_positive_trace"
            and row["current_status"]
            == "nearest_blank_context_available_not_sidewall_specific_validation"
            for row in lanes
        ),
        "wet": sum(
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
        and binder_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_FORMAL_QCH_SIDECAR_READY"
        and len(read_csv_rows(FORMAL_QCH_ROWS)) == 2
        and len(read_csv_rows(BINDING_ROWS)) == 2
        and len(deltas) == 4
        and qch_formal == 2
        and pressure_accepted == 2
        and all(count == 2 for count in retained_next.values())
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
        "source_formal_qch_binder_disposition": binder_status.get("disposition", ""),
        "refreshed_promotion_lane_rows": len(lanes),
        "formal_qch_delta_rows": len(deltas),
        "formal_qch_lane_rows": qch_formal,
        "pressure_flow_accepted_lane_rows": pressure_accepted,
        "selected_annulus_context_available_rows_retained": retained_next[
            "selected_annulus"
        ],
        "detector_context_available_rows_retained": retained_next["detector"],
        "blank_context_available_rows_retained": retained_next["blank"],
        "wet_surface_contract_defined_rows_retained": retained_next["wet"],
        "primary_next_execution_block": "detector_blank_calibration_and_wet_surface_validation",
        "formal_qch_sidecar_current": True,
        "formal_qch_weighting_current": False,
        "route_score_current": False,
        "winner_current": False,
        "yield_current": False,
        "detection_probability_current": False,
        "wet_pass_probability_current": False,
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
        "four qch/pressure deltas": summary["formal_qch_delta_rows"] == 4,
        "two formal qch lanes": summary["formal_qch_lane_rows"] == 2,
        "two pressure accepted lanes": summary["pressure_flow_accepted_lane_rows"] == 2,
        "detector retained": summary["detector_context_available_rows_retained"] == 2,
        "blank retained": summary["blank_context_available_rows_retained"] == 2,
        "wet retained": summary["wet_surface_contract_defined_rows_retained"] == 2,
        "formal qch true": summary["formal_qch_sidecar_current"] is True,
        "formal qch weighting false": summary["formal_qch_weighting_current"] is False,
        "route false": summary["route_score_current"] is False,
        "yield false": summary["yield_current"] is False,
        "detection false": summary["detection_probability_current"] is False,
    }
    for row in payload["refresh_delta_rows"]:
        checks[f"delta not final {row['delta_id']}"] = (
            row["target_claim_current"] == "false"
            and "route_score" in row["blocked_use"]
            and "yield" in row["blocked_use"]
            and "detection_probability" in row["blocked_use"]
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_PROMOTION_LANE_ROWS_20260701.csv": payload["refreshed_promotion_lane_rows"],
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
        / "544_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_FORMAL_QCH_REFRESH_20260701.md"
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
            "# NODI Package C Sidewall Integrated Promotion Ledger Formal q_ch Refresh",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Formal q_ch lane rows: `{s['formal_qch_lane_rows']}`.",
            f"- Accepted pressure-flow lane rows: `{s['pressure_flow_accepted_lane_rows']}`.",
            f"- Primary next execution block: `{s['primary_next_execution_block']}`.",
            "- This refresh updates flow_split_qch and pressure_flow_validation lanes from the exact W500/D900 pressure-flow binder.",
            "- Formal q_ch sidecar is current, but formal q_ch weighting, route_score, winner/JRC, yield, wet pass probability, and detection probability remain false.",
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
                "policy_impact": "formal_qch_ledger_refresh_not_route_promotion",
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
    if not args.confirm_sidewall_integrated_promotion_ledger_formal_qch_refresh:
        parser.error(
            "--confirm-sidewall-integrated-promotion-ledger-formal-qch-refresh is required"
        )
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_FORMAL_QCH_REFRESH")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
