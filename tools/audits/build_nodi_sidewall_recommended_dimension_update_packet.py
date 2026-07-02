#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_next_artifacts import (  # noqa: E402
    COMSOL_V4_ASSUMPTION_SET_ID,
    COMSOL_V4_ASSUMPTION_SET_SHA256,
    COMSOL_V4_ASSUMPTION_SET_VERSION,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260702"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET"
ARTIFACT_ID = "NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_20260702"
PACKET_VERSION = "sidewall_recommended_dimension_update_packet_v1"
DISPOSITION = "NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_FAIL_CLOSED"
CLAIM_BOUNDARY = (
    "sidewall_dimension_update_policy_not_route_selection_not_probability"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
PRIMARY_SIDEWALL_DEG_COMSOL = 85.0

SOURCE_FILES = {
    "synthesis_status_593": OUTPUT_DIR
    / "NODI_SIDEWALL_DIMENSION_ANNULUS_INTERFERENCE_SYNTHESIS_STATUS_20260702.json",
    "synthesis_answer_axis_593": OUTPUT_DIR
    / "NODI_SIDEWALL_DIMENSION_ANNULUS_INTERFERENCE_SYNTHESIS_ANSWER_AXIS_ROWS_20260702.csv",
    "synthesis_dimension_rows_593": OUTPUT_DIR
    / "NODI_SIDEWALL_DIMENSION_ANNULUS_INTERFERENCE_SYNTHESIS_DIMENSION_CHANGE_ROWS_20260702.csv",
    "synthesis_annulus_rows_593": OUTPUT_DIR
    / "NODI_SIDEWALL_DIMENSION_ANNULUS_INTERFERENCE_SYNTHESIS_ANNULUS_CHANGE_ROWS_20260702.csv",
    "synthesis_interference_rows_593": OUTPUT_DIR
    / "NODI_SIDEWALL_DIMENSION_ANNULUS_INTERFERENCE_SYNTHESIS_INTERFERENCE_CHANGE_ROWS_20260702.csv",
    "dimension_update_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_recommended_dimension_update_packet.py",
    "dimension_update_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_recommended_dimension_update_packet.py",
}

ALLOWED_USE = (
    "translate sidewall-angle synthesis into dimension/annulus/response update "
    "actions for simulation planning"
)
BLOCKED_USE = (
    "route winner, scalar score, final detection probability, yield, wet "
    "experimental claim, fabrication release, q_ch weighting, true W_eff, or "
    "production runtime ingestion"
)
FORBIDDEN_PRIMARY_COLUMNS = {
    "winner",
    "route_score",
    "rank",
    "detection_probability",
    "yield",
    "W_eff",
    "q_ch_eta",
    "rank_under_surrogate",
    "not_route_score",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sidewall-aware recommended dimension update packet."
    )
    parser.add_argument(
        "--confirm-sidewall-recommended-dimension-update-packet",
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


def fnum(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        numeric = float(text)
    except ValueError:
        return default
    return numeric if math.isfinite(numeric) else default


def inum(value: Any, default: int = 0) -> int:
    return int(round(fnum(value, float(default))))


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def deterministic_sha256(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def dirty_context_rows() -> list[dict[str, str]]:
    output_prefix = f"reports/joint_interface_{DATE_STAMP}/{PREFIX}_"
    output_report = f"reports/594_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_recommended_dimension_update_packet.py",
        "tests/test_nodi_sidewall_recommended_dimension_update_packet.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "dimension_update_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "dimension_update_output"
            release_decision = "included_or_rewritten_by_dimension_update_builder"
        else:
            classification = "non_dimension_update_dirty_context"
            release_decision = "ignored_for_dimension_update"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def load_rows(source_id: str) -> list[dict[str, str]]:
    path = SOURCE_FILES[source_id]
    return read_csv_rows(path) if path.exists() else []


def common_guard_fields() -> dict[str, Any]:
    return {
        "packet_version": PACKET_VERSION,
        "claim_boundary": CLAIM_BOUNDARY,
        "primary_sidewall_deg_comsol": PRIMARY_SIDEWALL_DEG_COMSOL,
        "not_detection_probability": True,
        "not_yield": True,
        "not_selection_metric_claim": True,
        "not_qch_weighted": True,
        "not_true_effective_width_claim": True,
        "not_production_recommendation": True,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "comsol_v4_assumption_set_sha256": COMSOL_V4_ASSUMPTION_SET_SHA256,
    }


def dimension_action(row: dict[str, str]) -> str:
    implication = row.get("dimension_recommendation_implication", "")
    signal = row.get("dimension_change_signal", "")
    if signal in {"rectangle_baseline", "rectangle_like"}:
        return "retain_rectangle_dimension_for_this_axis"
    if "increase_top_width_or_reduce_depth" in implication:
        return "widen_or_shallow_for_particle_support"
    if "widen_or_shallow" in implication or signal == "closed_geometry":
        return "block_or_respecify_width_depth"
    if "review" in implication:
        return "revise_margin_before_runtime_use"
    if "monitor" in implication:
        return "retain_with_margin_monitor"
    return "review_dimension_context"


def annulus_index() -> dict[tuple[str, int], dict[str, str]]:
    rows = [
        row
        for row in load_rows("synthesis_annulus_rows_593")
        if fnum(row.get("sidewall_deg_comsol")) == PRIMARY_SIDEWALL_DEG_COMSOL
    ]
    return {(row.get("route_id_nodi", ""), inum(row.get("diameter_nm"))): row for row in rows}


def interference_index() -> dict[tuple[str, int], dict[str, str]]:
    rows = [
        row
        for row in load_rows("synthesis_interference_rows_593")
        if fnum(row.get("sidewall_deg_comsol")) == PRIMARY_SIDEWALL_DEG_COMSOL
    ]
    return {(row.get("route_id_nodi", ""), inum(row.get("diameter_nm"))): row for row in rows}


def annulus_action(row: dict[str, str] | None) -> tuple[str, str]:
    if row is None:
        return "not_sampled_for_this_particle_diameter", "annulus_support_requires_followup_or_interpolation"
    signal = row.get("annulus_change_signal", "")
    if signal == "annulus_partial_remap":
        return "filter_0p5_0p8_by_particle_center_support", "selected_annulus_partially_accessible"
    if signal == "annulus_blocked":
        return "replace_or_block_selected_annulus", "selected_annulus_blocked"
    return "retain_0p5_0p8_with_trapezoid_coordinate_remap", "selected_annulus_accessible"


def response_action(row: dict[str, str] | None) -> tuple[str, str]:
    if row is None:
        return "not_sampled_for_this_particle_diameter", "response_sensitivity_requires_followup_or_interpolation"
    signal = row.get("interference_change_signal", "")
    if signal == "bounded_event_shift_observed":
        return "bounded_event_context_shift_observed", "sparse_event_context_available"
    if signal == "surrogate_response_shift":
        return "surrogate_response_shift_check", "surrogate_context_available"
    return "retain_response_context", "rectangle_like_response_context"


def route_diameter_update_rows() -> list[dict[str, Any]]:
    annulus = annulus_index()
    interference = interference_index()
    rows = [
        row
        for row in load_rows("synthesis_dimension_rows_593")
        if fnum(row.get("sidewall_deg_comsol")) == PRIMARY_SIDEWALL_DEG_COMSOL
    ]
    output: list[dict[str, Any]] = []
    for row in rows:
        route_id = row.get("route_id_nodi", "")
        diameter_nm = inum(row.get("diameter_nm"))
        ann_row = annulus.get((route_id, diameter_nm))
        int_row = interference.get((route_id, diameter_nm))
        ann_action, ann_context = annulus_action(ann_row)
        int_action, int_context = response_action(int_row)
        top_width_proxy = fnum(row.get("W_top_nm")) + max(
            fnum(row.get("top_width_compensation_proxy_nm")),
            0.0,
        )
        output.append(
            {
                **common_guard_fields(),
                "row_id": f"UPD-{route_id.replace('/', '_')}-P{diameter_nm}-TH85",
                "route_id_nodi": route_id,
                "route_id_role": "join_key_only_not_selection",
                "lambda_nm": inum(row.get("lambda_nm")),
                "W_nominal_nm": inum(row.get("W_nominal_nm")),
                "D_nm": inum(row.get("D_nm")),
                "diameter_nm": diameter_nm,
                "sidewall_deg_comsol": PRIMARY_SIDEWALL_DEG_COMSOL,
                "dimension_change_signal": row.get("dimension_change_signal", ""),
                "dimension_update_action": dimension_action(row),
                "W_top_compensated_proxy_nm": top_width_proxy,
                "top_width_compensation_proxy_nm": fnum(
                    row.get("top_width_compensation_proxy_nm")
                ),
                "bottom_throat_loss_nm": fnum(row.get("bottom_throat_loss_nm")),
                "center_accessible_area_fraction_vs_rectangle": fnum(
                    row.get("center_accessible_area_fraction_vs_rectangle"),
                    1.0,
                ),
                "closure_status": row.get("closure_status", ""),
                "annulus_update_action": ann_action,
                "annulus_context_status": ann_context,
                "annulus_accessible_fraction": ""
                if ann_row is None
                else fnum(ann_row.get("selected_annulus_accessible_fraction")),
                "annulus_changed_source_available": ann_row is not None,
                "interference_update_action": int_action,
                "interference_context_status": int_context,
                "surrogate_response_delta_mean": ""
                if int_row is None
                else fnum(int_row.get("surrogate_response_delta_mean")),
                "bounded_event_delta_available": False
                if int_row is None
                else boolish(int_row.get("bounded_event_delta_available")),
                "bounded_event_mean_peak_height_delta": ""
                if int_row is None
                else row_or_blank(int_row, "bounded_event_mean_peak_height_delta"),
                "bounded_event_mean_local_snr_delta": ""
                if int_row is None
                else row_or_blank(int_row, "bounded_event_mean_local_snr_delta"),
                "update_packet_status": "sidewall_update_context_ready",
            }
        )
    return output


def row_or_blank(row: dict[str, str], field: str) -> float | str:
    text = str(row.get(field, "")).strip()
    if not text:
        return ""
    return fnum(text)


def route_summary_rows(update_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    severity = {
        "retain_rectangle_dimension_for_this_axis": 0,
        "retain_with_margin_monitor": 1,
        "revise_margin_before_runtime_use": 2,
        "widen_or_shallow_for_particle_support": 3,
        "block_or_respecify_width_depth": 4,
        "review_dimension_context": 2,
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in update_rows:
        grouped[row["route_id_nodi"]].append(row)
    output: list[dict[str, Any]] = []
    for route_id, rows in sorted(grouped.items()):
        worst = max(rows, key=lambda row: severity.get(row["dimension_update_action"], 0))
        output.append(
            {
                **common_guard_fields(),
                "row_id": f"ROUTE-UPD-{route_id.replace('/', '_')}-TH85",
                "route_id_nodi": route_id,
                "route_id_role": "join_key_only_not_selection",
                "lambda_nm": worst["lambda_nm"],
                "W_nominal_nm": worst["W_nominal_nm"],
                "D_nm": worst["D_nm"],
                "sidewall_deg_comsol": PRIMARY_SIDEWALL_DEG_COMSOL,
                "diameter_rows": len(rows),
                "tail_sensitive_rows": sum(
                    1
                    for row in rows
                    if row["dimension_update_action"]
                    == "widen_or_shallow_for_particle_support"
                ),
                "block_or_respecify_rows": sum(
                    1
                    for row in rows
                    if row["dimension_update_action"] == "block_or_respecify_width_depth"
                ),
                "annulus_followup_rows": sum(
                    1
                    for row in rows
                    if row["annulus_update_action"]
                    != "retain_0p5_0p8_with_trapezoid_coordinate_remap"
                ),
                "bounded_event_context_rows": sum(
                    1 for row in rows if row["bounded_event_delta_available"] is True
                ),
                "max_W_top_compensated_proxy_nm": max(
                    fnum(row["W_top_compensated_proxy_nm"]) for row in rows
                ),
                "min_center_accessible_area_fraction_vs_rectangle": min(
                    fnum(row["center_accessible_area_fraction_vs_rectangle"], 1.0)
                    for row in rows
                ),
                "route_dimension_update_status": route_status(rows),
                "route_summary_not_selection": True,
            }
        )
    return output


def route_status(rows: list[dict[str, Any]]) -> str:
    actions = {row["dimension_update_action"] for row in rows}
    if "block_or_respecify_width_depth" in actions:
        return "geometry_stress_requires_respecification_for_some_particles"
    if "widen_or_shallow_for_particle_support" in actions:
        return "tail_sensitive_dimension_update_required"
    if "revise_margin_before_runtime_use" in actions:
        return "dimension_margin_revision_required"
    if "retain_with_margin_monitor" in actions:
        return "retain_with_sidewall_margin_monitor"
    return "retain_rectangle_dimension_under_primary_sidewall_context"


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for table_name in ("route_diameter_update_rows", "route_summary_rows"):
        table = payload[table_name]
        if not table:
            failures.append(f"{table_name} is empty")
            continue
        columns = set().union(*(set(row) for row in table))
        forbidden = sorted(columns & FORBIDDEN_PRIMARY_COLUMNS)
        if forbidden:
            failures.append(f"{table_name} has forbidden columns: {forbidden}")
        for index, row in enumerate(table, start=1):
            for field in (
                "not_detection_probability",
                "not_yield",
                "not_selection_metric_claim",
                "not_qch_weighted",
                "not_true_effective_width_claim",
                "not_production_recommendation",
            ):
                if row.get(field) is not True:
                    failures.append(f"{table_name} row {index} {field} must be true")
    if payload["summary"]["source_missing_rows"] != 0:
        failures.append("one or more source artifacts are missing")
    if payload["summary"]["route_diameter_update_rows"] != 78:
        failures.append("primary sidewall action rows should cover 6 routes x 13 diameters")
    if payload["summary"]["route_summary_rows"] != 6:
        failures.append("route summary rows should cover 6 PRS-approved routes")
    return failures


def alignment_check_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    failures = validate_payload(payload)
    return [
        {
            "check_name": "source_artifacts_present",
            "check_pass": payload["summary"]["source_missing_rows"] == 0,
            "observed": payload["summary"]["source_missing_rows"],
            "expected": 0,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "primary_theta85_route_diameter_coverage",
            "check_pass": payload["summary"]["route_diameter_update_rows"] == 78,
            "observed": payload["summary"]["route_diameter_update_rows"],
            "expected": 78,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "route_summary_coverage",
            "check_pass": payload["summary"]["route_summary_rows"] == 6,
            "observed": payload["summary"]["route_summary_rows"],
            "expected": 6,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "bounded_event_context_joined",
            "check_pass": payload["summary"]["bounded_event_context_rows"] == 12,
            "observed": payload["summary"]["bounded_event_context_rows"],
            "expected": 12,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "no_forbidden_primary_columns",
            "check_pass": not failures,
            "observed": "pass" if not failures else "; ".join(failures),
            "expected": "pass",
            "hard_fail_if_false": True,
        },
    ]


def build_payload() -> dict[str, Any]:
    update_rows = route_diameter_update_rows()
    summary_rows = route_summary_rows(update_rows)
    source_rows = source_lock_rows()
    dirty_rows = dirty_context_rows()
    summary = {
        "artifact_id": ARTIFACT_ID,
        "disposition": DISPOSITION,
        "packet_version": PACKET_VERSION,
        "branch": git_branch(),
        "current_head": git_head(),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
        "primary_sidewall_deg_comsol": PRIMARY_SIDEWALL_DEG_COMSOL,
        "route_diameter_update_rows": len(update_rows),
        "route_summary_rows": len(summary_rows),
        "widen_or_shallow_rows": sum(
            1
            for row in update_rows
            if row["dimension_update_action"] == "widen_or_shallow_for_particle_support"
        ),
        "block_or_respecify_rows": sum(
            1
            for row in update_rows
            if row["dimension_update_action"] == "block_or_respecify_width_depth"
        ),
        "annulus_followup_rows": sum(
            1
            for row in update_rows
            if row["annulus_update_action"]
            != "retain_0p5_0p8_with_trapezoid_coordinate_remap"
        ),
        "bounded_event_context_rows": sum(
            1 for row in update_rows if row["bounded_event_delta_available"] is True
        ),
        "source_lock_rows": len(source_rows),
        "source_missing_rows": sum(1 for row in source_rows if row["exists"] == "false"),
        "dirty_context_rows": len(dirty_rows),
        "non_dimension_update_dirty_context_rows": sum(
            1
            for row in dirty_rows
            if row["classification"] == "non_dimension_update_dirty_context"
        ),
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "primary_answer_frame": "sidewall_aware_dimension_annulus_response_update_actions",
        "not_primary_answer_frame": "route_winner_scoreboard_or_probability",
    }
    payload = {
        "disposition": summary["disposition"],
        "summary": summary,
        "source_lock_rows": source_rows,
        "dirty_context_rows": dirty_rows,
        "route_diameter_update_rows": update_rows,
        "route_summary_rows": summary_rows,
        "alignment_check_rows": [],
        "failure_rows": [{"failure_index": "", "failure": "none"}],
    }
    failures = validate_payload(payload)
    if failures:
        summary["disposition"] = BLOCKED_DISPOSITION
        payload["disposition"] = BLOCKED_DISPOSITION
        payload["failure_rows"] = [
            {"failure_index": index, "failure": failure}
            for index, failure in enumerate(failures, start=1)
        ]
    payload["alignment_check_rows"] = alignment_check_rows(payload)
    summary["alignment_check_rows"] = len(payload["alignment_check_rows"])
    summary["failed_alignment_check_rows"] = sum(
        1 for row in payload["alignment_check_rows"] if row["check_pass"] is not True
    )
    summary["semantic_digest"] = deterministic_sha256(
        {
            "update_rows": update_rows,
            "route_summary_rows": summary_rows,
            "sources": [(row["source_id"], row["sha256"]) for row in source_rows],
        }
    )
    return payload


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv",
        "route_diameter_update": OUTPUT_DIR
        / f"{PREFIX}_ROUTE_DIAMETER_UPDATE_ROWS_{DATE_STAMP}.csv",
        "route_summary": OUTPUT_DIR / f"{PREFIX}_ROUTE_SUMMARY_ROWS_{DATE_STAMP}.csv",
        "alignment_checks": OUTPUT_DIR / f"{PREFIX}_ALIGNMENT_CHECKS_{DATE_STAMP}.csv",
        "failures": OUTPUT_DIR / f"{PREFIX}_FAILURES_{DATE_STAMP}.csv",
        "master_report": REPORT_DIR / f"594_{PREFIX}_{DATE_STAMP}.md",
    }
    write_json_atomic(paths["status"], payload["summary"], sort_keys=True)
    write_csv_rows(paths["source_lock"], payload["source_lock_rows"])
    write_csv_rows(paths["dirty_context"], payload["dirty_context_rows"])
    write_csv_rows(paths["route_diameter_update"], payload["route_diameter_update_rows"])
    write_csv_rows(paths["route_summary"], payload["route_summary_rows"])
    write_csv_rows(paths["alignment_checks"], payload["alignment_check_rows"])
    write_csv_rows(paths["failures"], payload["failure_rows"])
    preliminary_manifest = [
        {
            "artifact_id": key,
            "path": display_path(path),
            "sha256": "",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for key, path in paths.items()
        if key != "report_json"
    ]
    paths["master_report"].write_text(
        master_report(payload, preliminary_manifest),
        encoding="utf-8",
    )
    manifest_rows = [
        {
            "artifact_id": key,
            "path": display_path(path),
            "sha256": SELF_MANIFEST_SHA256 if key == "manifest" else sha256_file(path),
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for key, path in paths.items()
        if key != "report_json"
    ]
    write_csv_rows(paths["manifest"], manifest_rows)
    write_json_atomic(
        paths["report_json"],
        {
            "disposition": payload["disposition"],
            "summary": payload["summary"],
            "route_summary_rows": payload["route_summary_rows"],
            "alignment_checks": payload["alignment_check_rows"],
            "manifest": manifest_rows,
        },
        indent=None,
        sort_keys=True,
    )
    return list(paths.values())


def master_report(payload: dict[str, Any], manifest_rows: list[dict[str, Any]]) -> str:
    summary = payload["summary"]
    route_status_lines = [
        f"- `{row['route_id_nodi']}`: `{row['route_dimension_update_status']}`; max W_top proxy `{row['max_W_top_compensated_proxy_nm']:.2f}` nm"
        for row in payload["route_summary_rows"]
    ]
    return "\n".join(
        [
            f"# 594 {PREFIX} {DATE_STAMP}",
            "",
            "## Disposition",
            "",
            f"- disposition: `{summary['disposition']}`",
            f"- primary_sidewall_deg_comsol: `{summary['primary_sidewall_deg_comsol']}`",
            f"- primary_answer_frame: `{summary['primary_answer_frame']}`",
            f"- not_primary_answer_frame: `{summary['not_primary_answer_frame']}`",
            "",
            "## Route-Level Dimension Update Context",
            "",
            *route_status_lines,
            "",
            "## Counts",
            "",
            f"- route_diameter_update_rows: `{summary['route_diameter_update_rows']}`",
            f"- route_summary_rows: `{summary['route_summary_rows']}`",
            f"- widen_or_shallow_rows: `{summary['widen_or_shallow_rows']}`",
            f"- block_or_respecify_rows: `{summary['block_or_respecify_rows']}`",
            f"- annulus_followup_rows: `{summary['annulus_followup_rows']}`",
            f"- bounded_event_context_rows: `{summary['bounded_event_context_rows']}`",
            "",
            "## Boundary",
            "",
            (
                "This packet gives sidewall-aware update actions for simulation "
                "planning. It does not select a route, estimate final detection "
                "probability, assign yield, or release a production runtime config."
            ),
            "",
            "## Manifest",
            "",
            *[
                f"- `{row['artifact_id']}`: `{row['path']}`"
                for row in manifest_rows
            ],
            "",
        ]
    )


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_sidewall_recommended_dimension_update_packet:
        print(
            "--confirm-sidewall-recommended-dimension-update-packet is required",
            file=sys.stderr,
        )
        return 2
    payload = build_payload()
    write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if payload["summary"]["disposition"] == DISPOSITION else 1


if __name__ == "__main__":
    raise SystemExit(main())
