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

PREFIX = "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_READY_PREFLIGHT_ONLY"
)
BLOCKED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_FAIL_CLOSED"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = "promotion_ledger_pressure_flow_refresh_not_formal_qch_not_route_score"

LEDGER_ROUTE_POLICY_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_STATUS_20260701.json"
)
LEDGER_ROUTE_POLICY_LANES = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_PROMOTION_LANE_ROWS_20260701.csv"
)
PRESSURE_FLOW_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_STATUS_20260701.json"
)
PRESSURE_FLOW_REQUEST_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_REQUEST_ROWS_20260701.csv"
)
PRESSURE_FLOW_CONTROL_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_CONTROL_ROWS_20260701.csv"
)
PRESSURE_FLOW_PROMOTION_UPDATE = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_PROMOTION_UPDATE_ROWS_20260701.csv"
)

ALLOWED_USE = "integrated promotion ledger pressure-flow validation harness refresh"
BLOCKED_USE = (
    "formal_qch_weighting;route_score;winner;JRC;yield;detection_probability;"
    "wet_pass_probability;clogging_rate;time_to_clog;recovery;production ingestion"
)

SOURCE_FILES = {
    "integrated_promotion_ledger_route_policy_status": LEDGER_ROUTE_POLICY_STATUS,
    "integrated_promotion_ledger_route_policy_lanes": LEDGER_ROUTE_POLICY_LANES,
    "pressure_flow_validation_harness_status": PRESSURE_FLOW_STATUS,
    "pressure_flow_validation_harness_request_rows": PRESSURE_FLOW_REQUEST_ROWS,
    "pressure_flow_validation_harness_control_rows": PRESSURE_FLOW_CONTROL_ROWS,
    "pressure_flow_validation_harness_promotion_update": PRESSURE_FLOW_PROMOTION_UPDATE,
    "ledger_pressure_flow_refresh_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_integrated_promotion_ledger_pressure_flow_refresh.py",
    "ledger_pressure_flow_refresh_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_integrated_promotion_ledger_pressure_flow_refresh.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "tools/audits/build_nodi_package_c_sidewall_integrated_promotion_ledger_pressure_flow_refresh.py",
    "tests/test_nodi_package_c_sidewall_integrated_promotion_ledger_pressure_flow_refresh.py",
    "reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
}
UPSTREAM_PRESSURE_FLOW_HARNESS_PREFIX = (
    "reports/joint_interface_20260701/"
    "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_"
)
UPSTREAM_PRESSURE_FLOW_HARNESS_PUBLIC_REPORT = (
    "reports/541_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_20260701.md"
)


def upstream_pressure_flow_harness_output(path: str) -> bool:
    return path.startswith(UPSTREAM_PRESSURE_FLOW_HARNESS_PREFIX) or (
        path == UPSTREAM_PRESSURE_FLOW_HARNESS_PUBLIC_REPORT
    )

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Refresh sidewall integrated promotion ledger with exact W500/D900 pressure-flow validation harness requests."
    )
    parser.add_argument(
        "--confirm-sidewall-integrated-promotion-ledger-pressure-flow-refresh",
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
            "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_"
        )
        or path
        == "reports/542_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "integrated_promotion_ledger_pressure_flow_refresh_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif upstream_pressure_flow_harness_output(path):
            classification = "source_locked_upstream_pressure_flow_harness_dirty_context"
            release_decision = "included_in_chain_rebuild_not_pressure_flow_refresh_blocker"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_"
        ) or path == (
            "reports/542_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_"
            "PRESSURE_FLOW_REFRESH_20260701.md"
        ):
            classification = "integrated_promotion_ledger_pressure_flow_refresh_output"
            release_decision = (
                "included_or_rewritten_by_integrated_promotion_ledger_pressure_flow_refresh"
            )
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_integrated_promotion_ledger_pressure_flow_refresh"
        else:
            classification = "non_release_dirty_context"
            release_decision = (
                "ignored_for_integrated_promotion_ledger_pressure_flow_refresh_not_source_locked"
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


def promotion_update_row() -> dict[str, str]:
    rows = read_csv_rows(PRESSURE_FLOW_PROMOTION_UPDATE)
    if len(rows) != 1:
        return {}
    return rows[0]


def route_ids_from_update(update: dict[str, str]) -> set[str]:
    return {
        value.strip()
        for value in update.get("covered_route_candidate_ids", "").split(";")
        if value.strip()
    }


def refreshed_promotion_lane_rows() -> list[dict[str, str]]:
    rows = read_csv_rows(LEDGER_ROUTE_POLICY_LANES)
    update = promotion_update_row()
    request_sha = sha256_file(PRESSURE_FLOW_REQUEST_ROWS)
    request_path = display_path(PRESSURE_FLOW_REQUEST_ROWS)
    status = load_json(PRESSURE_FLOW_STATUS)
    target_lane = update.get("target_ledger_lane", "")
    route_ids = route_ids_from_update(update)
    for row in rows:
        if row.get("evidence_lane") != target_lane:
            continue
        if row.get("route_candidate_id") not in route_ids:
            continue
        row["source_artifact"] = request_path
        row["source_sha256"] = request_sha
        row["source_disposition"] = status.get("disposition", "")
        row["current_status"] = update["new_context_status"]
        row["required_before_promotion"] = update["next_required_evidence"]
        row["hard_fail_if_promoted_without"] = update["hard_fail_if"]
        row["next_required_evidence"] = update["next_required_evidence"]
        row["blocked_use"] = BLOCKED_USE
    return rows


def refresh_delta_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    update = promotion_update_row()
    target_lane = update.get("target_ledger_lane", "")
    route_ids = route_ids_from_update(update)
    return [
        {
            "delta_id": f"PRESSURE-FLOW-REFRESH-{row['route_candidate_id']}",
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
        if row.get("evidence_lane") == target_lane
        and row.get("route_candidate_id") in route_ids
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "refreshed_promotion_lane_rows": payload["refreshed_promotion_lane_rows"],
        "refresh_delta_rows": payload["refresh_delta_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    ledger_status = load_json(LEDGER_ROUTE_POLICY_STATUS)
    pressure_status = load_json(PRESSURE_FLOW_STATUS)
    lanes = refreshed_promotion_lane_rows()
    deltas = refresh_delta_rows(lanes)
    request_rows = read_csv_rows(PRESSURE_FLOW_REQUEST_ROWS) if PRESSURE_FLOW_REQUEST_ROWS.exists() else []
    control_rows = read_csv_rows(PRESSURE_FLOW_CONTROL_ROWS) if PRESSURE_FLOW_CONTROL_ROWS.exists() else []
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    target_status = promotion_update_row().get("new_context_status", "")
    retained = {
        "qch": sum(
            row["evidence_lane"] == "flow_split_qch"
            and row["current_status"]
            in {
                "w500_d900_grid_refined_split_candidate_absolute_q_requires_validation",
                "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting",
            }
            for row in lanes
        ),
        "formal_qch_sidecar": sum(
            row["evidence_lane"] == "flow_split_qch"
            and row["current_status"]
            == "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting"
            for row in lanes
        ),
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
        "route_policy": sum(
            row["evidence_lane"] == "integrated_route_ledger"
            and row["current_status"] == "route_yield_detection_policy_defined_not_ready_for_claims"
            for row in lanes
        ),
    }
    pressure_integrated = sum(
        row["evidence_lane"] == "pressure_flow_validation"
        and row["current_status"] == target_status
        for row in lanes
    )
    exact_requests = sum(
        row.get("required_validation_source")
        == "exact W500/D900 sidewall COMSOL pressure-flow run or matched measurement"
        and row.get("validation_status")
        == "exact_w500_d900_validation_harness_ready_missing_external_result"
        for row in request_rows
    )
    blocked_controls = sum(
        row.get("solver_status") == "blocked_geometry_closed"
        and row.get("control_status") == "closed_geometry_control_must_remain_blocked"
        for row in control_rows
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and ledger_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_READY_PREFLIGHT_ONLY"
        and pressure_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_READY_EXECUTION_INPUT"
        and len(lanes) == 18
        and len(deltas) == 2
        and len(request_rows) == 2
        and exact_requests == 2
        and len(control_rows) == 1
        and blocked_controls == 1
        and pressure_integrated == 2
        and all(count == 2 for count in retained.values())
        and all(row["target_claim_current"] == "false" for row in deltas)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_ledger_route_policy_disposition": ledger_status.get("disposition", ""),
        "source_pressure_flow_harness_disposition": pressure_status.get("disposition", ""),
        "refreshed_promotion_lane_rows": len(lanes),
        "pressure_flow_delta_rows": len(deltas),
        "pressure_flow_request_rows": len(request_rows),
        "closed_geometry_control_rows": len(control_rows),
        "exact_w500_d900_route_requests": exact_requests,
        "closed_geometry_blocked_control_rows": blocked_controls,
        "pressure_flow_validation_harness_rows_integrated": pressure_integrated,
        "qch_grid_refined_lane_rows_retained": retained["qch"],
        "formal_qch_sidecar_lane_rows_retained": retained["formal_qch_sidecar"],
        "selected_annulus_context_available_rows_retained": retained["selected_annulus"],
        "detector_context_available_rows_retained": retained["detector"],
        "blank_context_available_rows_retained": retained["blank"],
        "wet_surface_contract_defined_rows_retained": retained["wet"],
        "integrated_route_policy_defined_rows_retained": retained["route_policy"],
        "formal_qch_weighting_current": False,
        "route_score_current": False,
        "winner_current": False,
        "yield_current": False,
        "detection_probability_current": False,
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
        "two pressure flow deltas": summary["pressure_flow_delta_rows"] == 2,
        "two request rows": summary["pressure_flow_request_rows"] == 2,
        "two exact requests": summary["exact_w500_d900_route_requests"] == 2,
        "one blocked closed control": summary["closed_geometry_blocked_control_rows"] == 1,
        "pressure flow integrated": summary["pressure_flow_validation_harness_rows_integrated"] == 2,
        "qch retained": summary["qch_grid_refined_lane_rows_retained"] == 2,
        "formal qch sidecar retained": summary[
            "formal_qch_sidecar_lane_rows_retained"
        ]
        == 2,
        "selected retained": summary["selected_annulus_context_available_rows_retained"] == 2,
        "detector retained": summary["detector_context_available_rows_retained"] == 2,
        "blank retained": summary["blank_context_available_rows_retained"] == 2,
        "wet retained": summary["wet_surface_contract_defined_rows_retained"] == 2,
        "route policy retained": summary["integrated_route_policy_defined_rows_retained"] == 2,
        "formal qch false": summary["formal_qch_weighting_current"] is False,
        "route false": summary["route_score_current"] is False,
        "yield false": summary["yield_current"] is False,
        "detection false": summary["detection_probability_current"] is False,
    }
    for row in payload["refresh_delta_rows"]:
        checks[f"delta not final {row['delta_id']}"] = (
            row["target_claim_current"] == "false"
            and "formal_qch_weighting" in row["blocked_use"]
            and "route_score" in row["blocked_use"]
            and "detection_probability" in row["blocked_use"]
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    lane_path = OUTPUT_DIR / f"{PREFIX}_PROMOTION_LANE_ROWS_20260701.csv"
    write_csv_rows(lane_path, payload["refreshed_promotion_lane_rows"])
    paths.append(lane_path)

    delta_path = OUTPUT_DIR / f"{PREFIX}_DELTA_ROWS_20260701.csv"
    write_csv_rows(delta_path, payload["refresh_delta_rows"])
    paths.append(delta_path)

    source_lock_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv"
    write_csv_rows(source_lock_path, payload["source_lock"])
    paths.append(source_lock_path)

    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv"
    write_csv_rows(dirty_path, payload["dirty_context"])
    paths.append(dirty_path)

    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(status_path, {"disposition": DISPOSITION, "summary": payload["summary"]})
    paths.append(status_path)

    report_path = OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_path, payload)
    paths.append(report_path)

    public_report = (
        REPORT_DIR
        / "542_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH_20260701.md"
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
            "# NODI Package C Sidewall Integrated Promotion Ledger Pressure-Flow Refresh",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Refreshed promotion lane rows: `{s['refreshed_promotion_lane_rows']}`.",
            f"- Pressure-flow delta rows: `{s['pressure_flow_delta_rows']}`.",
            f"- Exact W500/D900 route validation requests: `{s['exact_w500_d900_route_requests']}`.",
            "- This refresh updates pressure_flow_validation lanes with the 541 execution-input harness.",
            "- Formal q_ch weighting, route score, winner/JRC, yield, and detection probability remain false.",
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
                "policy_impact": "pressure_flow_harness_ledger_refresh_not_formal_qch",
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
    if not args.confirm_sidewall_integrated_promotion_ledger_pressure_flow_refresh:
        parser.error(
            "--confirm-sidewall-integrated-promotion-ledger-pressure-flow-refresh is required"
        )
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_PRESSURE_FLOW_REFRESH")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
