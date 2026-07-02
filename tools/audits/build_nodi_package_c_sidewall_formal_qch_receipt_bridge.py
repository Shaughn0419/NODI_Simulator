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

PREFIX = "NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE_READY_ROUTE_INPUT_NOT_SCORE"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = "formal_qch_receipt_bridge_not_qch_weighting_not_route_score_not_yield_not_detection"

FLOW_SOLVER_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_STATUS_20260701.json"
)
FLOW_SOLVER_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_SOLVER_ROWS_20260701.csv"
)
HARNESS_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_STATUS_20260701.json"
)
HARNESS_REQUEST_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_REQUEST_ROWS_20260701.csv"
)
HARNESS_CONTROL_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_CONTROL_ROWS_20260701.csv"
)
BINDER_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_STATUS_20260701.json"
)
BINDER_BINDING_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_BINDING_ROWS_20260701.csv"
)
BINDER_FORMAL_QCH_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_FORMAL_QCH_SIDECAR_ROWS_20260701.csv"
)
BRIDGE_RELEASE_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_BRIDGE_RELEASE_V1_STATUS_20260701.json"
)
BRIDGE_RELEASE_POLICY = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_BRIDGE_RELEASE_V1_CONSUMPTION_POLICY_20260701.csv"
)
ASSEMBLY_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_DETECTOR_BLANK_TRANSFER_REFRESH_STATUS_20260701.json"
)
ASSEMBLY_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_DETECTOR_BLANK_TRANSFER_REFRESH_ASSEMBLY_ROWS_20260701.csv"
)
ASSEMBLY_BRANCH_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_DETECTOR_BLANK_TRANSFER_REFRESH_BRANCH_ROWS_20260701.csv"
)
TRANSFER_HARDENING_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_STATUS_20260701.json"
)

ALLOWED_USE = (
    "formal q_ch sidecar receipt reconciliation;route input readiness bridge;"
    "pressure-flow evidence chain source-lock"
)
BLOCKED_USE = (
    "q_ch_weighting;route_score;winner;JRC;yield;detection_probability;"
    "wet_pass_probability;production ingestion"
)

SOURCE_FILES = {
    "flow_solver_candidate_status": FLOW_SOLVER_STATUS,
    "flow_solver_candidate_rows": FLOW_SOLVER_ROWS,
    "pressure_flow_validation_harness_status": HARNESS_STATUS,
    "pressure_flow_validation_harness_request_rows": HARNESS_REQUEST_ROWS,
    "pressure_flow_validation_harness_control_rows": HARNESS_CONTROL_ROWS,
    "pressure_flow_result_binder_status": BINDER_STATUS,
    "pressure_flow_result_binder_binding_rows": BINDER_BINDING_ROWS,
    "pressure_flow_result_binder_formal_qch_rows": BINDER_FORMAL_QCH_ROWS,
    "pressure_flow_bridge_release_status": BRIDGE_RELEASE_STATUS,
    "pressure_flow_bridge_release_consumption_policy": BRIDGE_RELEASE_POLICY,
    "route_yield_detection_assembly_detector_blank_transfer_status": ASSEMBLY_STATUS,
    "route_yield_detection_assembly_detector_blank_transfer_rows": ASSEMBLY_ROWS,
    "route_yield_detection_assembly_detector_blank_transfer_branch_rows": ASSEMBLY_BRANCH_ROWS,
    "detector_blank_transfer_validation_hardening_status": TRANSFER_HARDENING_STATUS,
    "formal_qch_receipt_bridge_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_formal_qch_receipt_bridge.py",
    "formal_qch_receipt_bridge_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_formal_qch_receipt_bridge.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "tools/audits/build_nodi_package_c_sidewall_formal_qch_receipt_bridge.py",
    "tests/test_nodi_package_c_sidewall_formal_qch_receipt_bridge.py",
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
        description="Build formal q_ch receipt bridge without route scoring."
    )
    parser.add_argument(
        "--confirm-sidewall-formal-qch-receipt-bridge",
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
            "NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE_"
        )
        or path
        == "reports/552_NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE_20260701.md"
    )


def source_locked_path(path: str) -> bool:
    return path in {
        display_path(source_path)
        for source_path in SOURCE_FILES.values()
        if source_path.exists()
    }


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "formal_qch_receipt_bridge_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE_"
        ) or path == "reports/552_NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE_20260701.md":
            classification = "formal_qch_receipt_bridge_output"
            release_decision = "included_or_rewritten_by_formal_qch_receipt_bridge"
        elif source_locked_path(path):
            classification = "source_locked_upstream_dirty_context"
            release_decision = "source_locked_current_workspace_not_in_commit_scope"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_formal_qch_receipt_bridge"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_formal_qch_receipt_bridge_not_source_locked"
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


def bridge_rows() -> list[dict[str, Any]]:
    solver_by_case = {row["case_id"]: row for row in read_csv_rows(FLOW_SOLVER_ROWS)}
    request_by_route = {
        row["route_candidate_id"]: row for row in read_csv_rows(HARNESS_REQUEST_ROWS)
    }
    binding_by_route = {
        row["route_candidate_id"]: row for row in read_csv_rows(BINDER_BINDING_ROWS)
    }
    formal_by_route = {
        row["route_candidate_id"]: row for row in read_csv_rows(BINDER_FORMAL_QCH_ROWS)
    }
    assembly_by_route = {
        row["route_candidate_id"]: row for row in read_csv_rows(ASSEMBLY_ROWS)
    }
    rows: list[dict[str, Any]] = []
    for route_id in sorted(assembly_by_route):
        assembly = assembly_by_route[route_id]
        case_id = assembly["source_case_id"]
        solver = solver_by_case.get(case_id, {})
        request = request_by_route.get(route_id, {})
        binding = binding_by_route.get(route_id, {})
        formal = formal_by_route.get(route_id, {})
        rows.append(
            {
                "bridge_row_id": f"FORMAL-QCH-RECEIPT-{route_id}",
                "artifact_id": ARTIFACT_ID,
                "route_candidate_id": route_id,
                "route_key": assembly["route_key"],
                "route_geometry_family": assembly["route_geometry_family"],
                "case_id": case_id,
                "qch_sidecar_id": assembly["qch_sidecar_id"],
                "candidate_solver_status": solver.get("solver_status", ""),
                "candidate_solver_claim_level": solver.get("solver_claim_level", ""),
                "candidate_resistance_ratio_vs_rectangle_proxy": _float_value(
                    solver.get("resistance_ratio_vs_rectangle_proxy")
                ),
                "validation_request_id": request.get("validation_request_id", ""),
                "source_geometry_hash": request.get("source_geometry_hash", ""),
                "external_result_id": binding.get("external_result_id", ""),
                "source_type": binding.get("source_type", ""),
                "source_match_status": binding.get("source_match_status", ""),
                "quality_gate": binding.get("quality_gate", ""),
                "flow_ratio_external_to_candidate": _float_value(
                    binding.get("flow_ratio_external_to_candidate")
                ),
                "split_abs_delta": _float_value(binding.get("split_abs_delta")),
                "per_route_acceptance_status": binding.get("per_route_acceptance_status", ""),
                "formal_qch_sidecar_id": formal.get("formal_qch_sidecar_id", ""),
                "q_ch_m3_s": _float_value(formal.get("q_ch_m3_s")),
                "formal_flow_split_fraction": _float_value(
                    formal.get("formal_flow_split_fraction")
                ),
                "formal_qch_sidecar_current": _bool_value(
                    formal.get("formal_qch_sidecar_current")
                ),
                "formal_qch_weighting_current": False,
                "q_ch_weighting_current": False,
                "assembly_next_executable_branch": assembly["next_executable_branch"],
                "bridge_status": (
                    "formal_qch_receipt_reconciled_ready_as_route_input_not_route_weighting"
                ),
                "next_required_evidence": assembly["next_required_evidence"],
                "route_score_current": False,
                "winner_current": False,
                "yield_current": False,
                "detection_probability_current": False,
                "wet_pass_probability_current": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def firewall_rows() -> list[dict[str, str]]:
    targets = [
        (
            "q_ch_weighting",
            "explicit q_ch weighting policy and route scoring authorization consuming formal sidecar",
        ),
        (
            "route_score",
            "detector/blank validation, wet endpoint bundle, and route scoring formula review",
        ),
        (
            "winner",
            "route_score audit, no-borrowing guards, and explicit winner policy",
        ),
        (
            "yield",
            "accepted wet/surface endpoint bundle with uncertainty and controls",
        ),
        (
            "detection_probability",
            "sidewall detector response validation plus sidewall blank false-positive trace",
        ),
        (
            "production_ingestion",
            "full route/yield/detection release packet and production acceptance",
        ),
    ]
    return [
        {
            "firewall_id": f"FORMAL-QCH-FIREWALL-{index:02d}",
            "target": target,
            "current_value": "false",
            "formal_qch_sidecar_available": "true",
            "hard_fail_if": f"{target}_true_from_formal_qch_receipt_alone",
            "required_before_true": required,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for index, (target, required) in enumerate(targets, start=1)
    ]


def bridge_delta_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "delta_id": f"FORMAL-QCH-ASSEMBLY-DELTA-{row['route_candidate_id']}",
            "route_candidate_id": row["route_candidate_id"],
            "route_geometry_family": row["route_geometry_family"],
            "flow_split_qch_status": "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting",
            "pressure_flow_validation_status": (
                "exact_w500_d900_pressure_flow_result_accepted_formal_qch_sidecar_ready"
            ),
            "formal_qch_sidecar_id": row["formal_qch_sidecar_id"],
            "q_ch_m3_s": row["q_ch_m3_s"],
            "formal_flow_split_fraction": row["formal_flow_split_fraction"],
            "next_executable_branch": row["assembly_next_executable_branch"],
            "target_claim_current": False,
            "route_score_current": False,
            "yield_current": False,
            "detection_probability_current": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for row in rows
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "bridge_rows": payload["bridge_rows"],
        "firewall_rows": payload["firewall_rows"],
        "bridge_delta_rows": payload["bridge_delta_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    flow_status = load_json(FLOW_SOLVER_STATUS)
    harness_status = load_json(HARNESS_STATUS)
    binder_status = load_json(BINDER_STATUS)
    bridge_release_status = load_json(BRIDGE_RELEASE_STATUS)
    assembly_status = load_json(ASSEMBLY_STATUS)
    transfer_hardening_status = load_json(TRANSFER_HARDENING_STATUS)
    rows = bridge_rows()
    firewall = firewall_rows()
    deltas = bridge_delta_rows(rows)
    control_rows = read_csv_rows(HARNESS_CONTROL_ROWS)
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
        and flow_status.get("disposition")
        == "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_READY_NOT_QCH"
        and harness_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_READY_EXECUTION_INPUT"
        and binder_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_FORMAL_QCH_SIDECAR_READY"
        and bridge_release_status.get("disposition")
        == "PASS_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_BRIDGE_RELEASE_V1_READY_FOR_COMSOL_RECEIVER_NO_AUTH"
        and assembly_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_DETECTOR_BLANK_TRANSFER_REFRESH_READY_NOT_CLAIM_READY"
        and transfer_hardening_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_READY_NOT_PROBABILITY"
        and len(rows) == 2
        and len(deltas) == 2
        and len(firewall) == 6
        and all(row["formal_qch_sidecar_current"] is True for row in rows)
        and all(row["formal_qch_weighting_current"] is False for row in rows)
        and all(row["route_score_current"] is False for row in rows)
        and all(row["assembly_next_executable_branch"] == "sidewall_detector_blank_transfer_validation" for row in rows)
        and len(control_rows) == 1
        and control_rows[0].get("solver_status") == "blocked_geometry_closed"
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_flow_solver_disposition": flow_status.get("disposition", ""),
        "source_harness_disposition": harness_status.get("disposition", ""),
        "source_binder_disposition": binder_status.get("disposition", ""),
        "source_bridge_release_disposition": bridge_release_status.get("disposition", ""),
        "source_assembly_disposition": assembly_status.get("disposition", ""),
        "source_transfer_hardening_disposition": transfer_hardening_status.get("disposition", ""),
        "bridge_rows": len(rows),
        "bridge_delta_rows": len(deltas),
        "firewall_rows": len(firewall),
        "closed_geometry_control_rows": len(control_rows),
        "formal_qch_sidecar_current_rows": sum(row["formal_qch_sidecar_current"] for row in rows),
        "formal_qch_weighting_current_rows": sum(row["formal_qch_weighting_current"] for row in rows),
        "q_ch_weighting_current_rows": sum(row["q_ch_weighting_current"] for row in rows),
        "route_score_current_rows": sum(row["route_score_current"] for row in rows),
        "winner_current_rows": sum(row["winner_current"] for row in rows),
        "yield_current_rows": sum(row["yield_current"] for row in rows),
        "detection_probability_current_rows": sum(
            row["detection_probability_current"] for row in rows
        ),
        "route_geometry_families": ";".join(
            sorted({row["route_geometry_family"] for row in rows})
        ),
        "next_executable_branches": ";".join(
            sorted({row["assembly_next_executable_branch"] for row in rows})
        ),
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "source_locked_upstream_dirty_context_rows": sum(
            row["classification"] == "source_locked_upstream_dirty_context"
            for row in dirty_context
        ),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context" for row in dirty_context
        ),
        "release_scoped_dirty_blocker_rows": release_dirty_blockers,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "bridge_rows": rows,
        "bridge_delta_rows": deltas,
        "firewall_rows": firewall,
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
        "two bridge rows": s["bridge_rows"] == 2,
        "two deltas": s["bridge_delta_rows"] == 2,
        "six firewall rows": s["firewall_rows"] == 6,
        "closed control retained": s["closed_geometry_control_rows"] == 1,
        "rectangle and trapezoid": (
            s["route_geometry_families"] == "ideal_rectangle;trapezoid_tapered_sidewalls"
        ),
        "formal sidecars present": s["formal_qch_sidecar_current_rows"] == 2,
        "formal weighting false": s["formal_qch_weighting_current_rows"] == 0,
        "q_ch weighting false": s["q_ch_weighting_current_rows"] == 0,
        "route false": s["route_score_current_rows"] == 0,
        "winner false": s["winner_current_rows"] == 0,
        "yield false": s["yield_current_rows"] == 0,
        "detection false": s["detection_probability_current_rows"] == 0,
        "next branch detector blank": (
            s["next_executable_branches"] == "sidewall_detector_blank_transfer_validation"
        ),
    }
    for row in payload["bridge_rows"]:
        checks[f"accepted binding {row['bridge_row_id']}"] = (
            row["per_route_acceptance_status"]
            == "accepted_exact_pressure_flow_for_formal_qch_sidecar"
            and row["source_match_status"] == "exact_request_and_geometry_match"
            and row["quality_gate"] == "pass"
            and row["q_ch_m3_s"] > 0.0
        )
    for row in payload["firewall_rows"]:
        checks[f"firewall false {row['firewall_id']}"] = row["current_value"] == "false"
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    csv_payloads = {
        f"{PREFIX}_BRIDGE_ROWS_20260701.csv": payload["bridge_rows"],
        f"{PREFIX}_ASSEMBLY_DELTA_ROWS_20260701.csv": payload["bridge_delta_rows"],
        f"{PREFIX}_FIREWALL_ROWS_20260701.csv": payload["firewall_rows"],
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

    public_report = REPORT_DIR / "552_NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE_20260701.md"
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
            "# NODI Package C Sidewall Formal q_ch Receipt Bridge",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Bridge rows: `{s['bridge_rows']}`.",
            f"- Route geometry families: `{s['route_geometry_families']}`.",
            f"- Formal q_ch sidecar rows current: `{s['formal_qch_sidecar_current_rows']}`.",
            f"- Next executable branch: `{s['next_executable_branches']}`.",
            "- Candidate solver, pressure-flow validation harness, accepted COMSOL pressure-flow binding, formal q_ch sidecars, and 550 assembly are reconciled at route grain.",
            "- Formal q_ch sidecar availability is not q_ch weighting, route score, winner/JRC, yield, detection probability, wet pass probability, runtime, or production ingestion.",
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
                "policy_impact": "formal_qch_receipt_reconciled_not_route_score",
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


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_sidewall_formal_qch_receipt_bridge:
        parser.error("--confirm-sidewall-formal-qch-receipt-bridge is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
