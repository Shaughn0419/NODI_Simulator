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
PREFIX = "NODI_SIDEWALL_FULL_EVENT_INTEGRATED_UPDATE_PACKET"
ARTIFACT_ID = "NODI_SIDEWALL_FULL_EVENT_INTEGRATED_UPDATE_PACKET_20260702"
PACKET_VERSION = "sidewall_full_event_integrated_update_packet_v1"
DISPOSITION = "NODI_SIDEWALL_FULL_EVENT_INTEGRATED_UPDATE_PACKET_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_FULL_EVENT_INTEGRATED_UPDATE_PACKET_FAIL_CLOSED"
CLAIM_BOUNDARY = "sidewall_full_event_dimension_annulus_response_context_not_selection"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
PRIMARY_SIDEWALL_DEG_COMSOL = 85.0
BASELINE_SIDEWALL_DEG_COMSOL = 90.0

SOURCE_FILES = {
    "dimension_update_status_594": OUTPUT_DIR
    / "NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_STATUS_20260702.json",
    "dimension_update_rows_594": OUTPUT_DIR
    / "NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_ROUTE_DIAMETER_UPDATE_ROWS_20260702.csv",
    "dimension_route_summary_594": OUTPUT_DIR
    / "NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_ROUTE_SUMMARY_ROWS_20260702.csv",
    "primary85_status_595": OUTPUT_DIR
    / "NODI_SIDEWALL_PRIMARY85_FULL_BOUNDED_EVENT_EXPANSION_STATUS_20260702.json",
    "primary85_event_rows_595": OUTPUT_DIR
    / "NODI_SIDEWALL_PRIMARY85_FULL_BOUNDED_EVENT_EXPANSION_EVENT_ROWS_20260702.csv",
    "primary85_paired_delta_rows_595": OUTPUT_DIR
    / "NODI_SIDEWALL_PRIMARY85_FULL_BOUNDED_EVENT_EXPANSION_PAIRED_DELTA_ROWS_20260702.csv",
    "integrated_update_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_full_event_integrated_update_packet.py",
    "integrated_update_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_full_event_integrated_update_packet.py",
}

ALLOWED_USE = (
    "integrate full sparse NODI bounded-event context into sidewall dimension, "
    "selected-annulus, and interference-response update planning"
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
        description="Build sidewall full-event integrated update packet."
    )
    parser.add_argument(
        "--confirm-sidewall-full-event-integrated-update-packet",
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
    output_report = f"reports/596_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_full_event_integrated_update_packet.py",
        "tests/test_nodi_sidewall_full_event_integrated_update_packet.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "full_event_integrated_update_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "full_event_integrated_update_output"
            release_decision = "included_or_rewritten_by_integrated_update_builder"
        else:
            classification = "non_full_event_integrated_update_dirty_context"
            release_decision = "ignored_for_full_event_integrated_update"
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
        "baseline_sidewall_deg_comsol": BASELINE_SIDEWALL_DEG_COMSOL,
        "not_detection_probability": True,
        "not_yield": True,
        "not_selection_metric_claim": True,
        "not_winner": True,
        "not_qch_weighted": True,
        "not_true_effective_width_claim": True,
        "not_production_recommendation": True,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "comsol_v4_assumption_set_sha256": COMSOL_V4_ASSUMPTION_SET_SHA256,
    }


def update_index() -> dict[tuple[str, int], dict[str, str]]:
    rows = load_rows("dimension_update_rows_594")
    return {(row.get("route_id_nodi", ""), inum(row.get("diameter_nm"))): row for row in rows}


def delta_index() -> dict[tuple[str, int], dict[str, str]]:
    rows = load_rows("primary85_paired_delta_rows_595")
    return {(row.get("route_id_nodi", ""), inum(row.get("diameter_nm"))): row for row in rows}


def event_index(theta: float) -> dict[tuple[str, int], dict[str, str]]:
    rows = [
        row
        for row in load_rows("primary85_event_rows_595")
        if math.isclose(fnum(row.get("sidewall_deg_comsol")), theta)
    ]
    return {(row.get("route_id_nodi", ""), inum(row.get("diameter_nm"))): row for row in rows}


def dimension_context_band(row: dict[str, str]) -> str:
    action = row.get("dimension_update_action", "")
    area_fraction = fnum(row.get("center_accessible_area_fraction_vs_rectangle"))
    closure = row.get("closure_status", "")
    if closure != "open" or area_fraction <= 0.55:
        return "geometry_respecification_context"
    if action in {
        "widen_or_shallow_for_particle_support",
        "block_or_respecify_width_depth",
    }:
        return "dimension_update_required_context"
    if area_fraction < 0.75:
        return "tail_margin_review_context"
    return "dimension_margin_monitor_context"


def annulus_event_shift_band(delta_row: dict[str, str] | None) -> str:
    if delta_row is None:
        return "event_delta_missing"
    value = abs(fnum(delta_row.get("selected_annulus_fraction_delta")))
    if value >= 0.75:
        return "large_annulus_fraction_shift_context"
    if value >= 0.25:
        return "moderate_annulus_fraction_shift_context"
    return "low_annulus_fraction_shift_context"


def response_event_shift_band(delta_row: dict[str, str] | None) -> str:
    if delta_row is None:
        return "event_delta_missing"
    peak_delta = abs(fnum(delta_row.get("mean_peak_height_delta")))
    if peak_delta >= 10.0:
        return "large_interference_response_shift_context"
    if peak_delta >= 3.0:
        return "moderate_interference_response_shift_context"
    if peak_delta >= 1.0:
        return "small_interference_response_shift_context"
    return "low_interference_response_shift_context"


def integrated_update_state(
    update_row: dict[str, str],
    delta_row: dict[str, str] | None,
) -> str:
    dimension_band = dimension_context_band(update_row)
    annulus_band = annulus_event_shift_band(delta_row)
    response_band = response_event_shift_band(delta_row)
    if dimension_band == "geometry_respecification_context":
        return "respecify_geometry_before_response_context_use"
    if dimension_band == "dimension_update_required_context":
        return "dimension_update_with_full_event_context"
    if "large_" in annulus_band or "large_" in response_band:
        return "event_context_changes_annulus_or_response_followup"
    if "moderate_" in annulus_band or "moderate_" in response_band:
        return "event_context_review_before_freezing_annulus_response"
    return "retain_dimension_with_sidewall_context_overlay"


def integrated_route_diameter_rows() -> list[dict[str, Any]]:
    updates = update_index()
    deltas = delta_index()
    baseline_events = event_index(BASELINE_SIDEWALL_DEG_COMSOL)
    sidewall_events = event_index(PRIMARY_SIDEWALL_DEG_COMSOL)
    output: list[dict[str, Any]] = []
    for key in sorted(updates):
        update_row = updates[key]
        delta_row = deltas.get(key)
        baseline_event = baseline_events.get(key, {})
        sidewall_event = sidewall_events.get(key, {})
        route_id, diameter_nm = key
        output.append(
            {
                **common_guard_fields(),
                "row_id": f"INT-{route_id.replace('/', '_')}-P{diameter_nm}-TH85",
                "route_id_nodi": route_id,
                "route_id_role": "join_key_only_not_selection",
                "lambda_nm": inum(update_row.get("lambda_nm")),
                "W_nominal_nm": inum(update_row.get("W_nominal_nm")),
                "D_nm": inum(update_row.get("D_nm")),
                "diameter_nm": diameter_nm,
                "sidewall_deg_comsol": PRIMARY_SIDEWALL_DEG_COMSOL,
                "dimension_update_action_594": update_row.get("dimension_update_action", ""),
                "dimension_context_band": dimension_context_band(update_row),
                "W_top_compensated_proxy_nm": fnum(update_row.get("W_top_compensated_proxy_nm")),
                "top_width_compensation_proxy_nm": fnum(update_row.get("top_width_compensation_proxy_nm")),
                "bottom_throat_loss_nm": fnum(update_row.get("bottom_throat_loss_nm")),
                "center_accessible_area_fraction_vs_rectangle": fnum(
                    update_row.get("center_accessible_area_fraction_vs_rectangle")
                ),
                "closure_status": update_row.get("closure_status", ""),
                "annulus_update_action_594": update_row.get("annulus_update_action", ""),
                "annulus_context_status_594": update_row.get("annulus_context_status", ""),
                "full_event_delta_available": delta_row is not None,
                "baseline_event_execution_status": baseline_event.get("execution_status", ""),
                "sidewall_event_execution_status": sidewall_event.get("execution_status", ""),
                "n_events_requested_per_angle": inum(sidewall_event.get("n_events_requested")),
                "selected_annulus_fraction_rectangle": fnum(
                    baseline_event.get("selected_annulus_fraction")
                ),
                "selected_annulus_fraction_sidewall85": fnum(
                    sidewall_event.get("selected_annulus_fraction")
                ),
                "selected_annulus_fraction_delta": fnum(
                    delta_row.get("selected_annulus_fraction_delta") if delta_row else ""
                ),
                "selected_annulus_mean_edge_norm_delta": delta_row.get(
                    "selected_annulus_mean_edge_norm_delta", ""
                )
                if delta_row
                else "",
                "annulus_event_shift_band": annulus_event_shift_band(delta_row),
                "annulus_range_update_implication": (
                    "selected_annulus_0p5_0p8_needs_event_context_review"
                    if annulus_event_shift_band(delta_row)
                    in {
                        "large_annulus_fraction_shift_context",
                        "moderate_annulus_fraction_shift_context",
                    }
                    else "selected_annulus_0p5_0p8_retained_with_sidewall_context"
                ),
                "interference_update_action_594": update_row.get("interference_update_action", ""),
                "interference_context_status_594": update_row.get("interference_context_status", ""),
                "mean_peak_height_rectangle": fnum(baseline_event.get("mean_peak_height")),
                "mean_peak_height_sidewall85": fnum(sidewall_event.get("mean_peak_height")),
                "mean_peak_height_delta": fnum(
                    delta_row.get("mean_peak_height_delta") if delta_row else ""
                ),
                "mean_local_snr_delta": fnum(
                    delta_row.get("mean_local_snr_delta") if delta_row else ""
                ),
                "synthetic_counting_context_rate_delta": fnum(
                    delta_row.get("synthetic_counting_context_rate_delta")
                    if delta_row
                    else ""
                ),
                "response_event_shift_band": response_event_shift_band(delta_row),
                "interference_context_implication": (
                    "interference_enhancement_context_changes_under_85deg_sidewall"
                    if response_event_shift_band(delta_row)
                    in {
                        "large_interference_response_shift_context",
                        "moderate_interference_response_shift_context",
                        "small_interference_response_shift_context",
                    }
                    else "interference_context_low_shift_in_sparse_event_run"
                ),
                "integrated_update_state": integrated_update_state(update_row, delta_row),
                "sidewall_context_status": "full_event_integrated_context_ready"
                if delta_row is not None
                else "missing_full_event_delta",
            }
        )
    return output


def route_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["route_id_nodi"]].append(row)
    output: list[dict[str, Any]] = []
    for route_id, group in sorted(grouped.items()):
        dimension_respec = sum(
            row["dimension_context_band"] == "geometry_respecification_context"
            for row in group
        )
        dimension_update = sum(
            row["dimension_context_band"] == "dimension_update_required_context"
            for row in group
        )
        annulus_review = sum(
            row["annulus_event_shift_band"]
            in {
                "large_annulus_fraction_shift_context",
                "moderate_annulus_fraction_shift_context",
            }
            for row in group
        )
        response_review = sum(
            row["response_event_shift_band"]
            in {
                "large_interference_response_shift_context",
                "moderate_interference_response_shift_context",
            }
            for row in group
        )
        if dimension_respec:
            state = "geometry_respecification_context_present"
        elif dimension_update:
            state = "dimension_update_context_present"
        elif annulus_review or response_review:
            state = "annulus_or_response_event_context_review_present"
        else:
            state = "sidewall_context_overlay_without_dimension_change"
        output.append(
            {
                **common_guard_fields(),
                "route_id_nodi": route_id,
                "route_id_role": "join_key_only_not_selection",
                "route_summary_not_selection": True,
                "route_diameter_rows": len(group),
                "diameters_with_geometry_respecification_context": dimension_respec,
                "diameters_with_dimension_update_context": dimension_update,
                "diameters_with_annulus_event_review_context": annulus_review,
                "diameters_with_interference_event_review_context": response_review,
                "max_abs_selected_annulus_fraction_delta": max(
                    abs(float(row["selected_annulus_fraction_delta"])) for row in group
                ),
                "max_abs_mean_peak_height_delta": max(
                    abs(float(row["mean_peak_height_delta"])) for row in group
                ),
                "max_W_top_compensated_proxy_nm": max(
                    float(row["W_top_compensated_proxy_nm"]) for row in group
                ),
                "min_center_accessible_area_fraction_vs_rectangle": min(
                    float(row["center_accessible_area_fraction_vs_rectangle"])
                    for row in group
                ),
                "route_integrated_context_state": state,
            }
        )
    return output


def answer_axis_rows(rows: list[dict[str, Any]], summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **common_guard_fields(),
            "answer_axis": "recommended_dimension_window",
            "answer": "yes_sidewall_angle_changes_dimension_update_context",
            "evidence_rows": len(rows),
            "route_rows": len(summaries),
            "affected_route_diameter_rows": sum(
                row["dimension_context_band"]
                in {
                    "geometry_respecification_context",
                    "dimension_update_required_context",
                    "tail_margin_review_context",
                }
                for row in rows
            ),
            "mainline_interpretation": (
                "85deg sidewalls reduce center-accessible support and require "
                "dimension update or margin review for affected route/diameter rows"
            ),
        },
        {
            **common_guard_fields(),
            "answer_axis": "selected_annulus_range",
            "answer": "yes_sidewall_angle_changes_selected_annulus_event_context",
            "evidence_rows": len(rows),
            "route_rows": len(summaries),
            "affected_route_diameter_rows": sum(
                row["annulus_event_shift_band"]
                in {
                    "large_annulus_fraction_shift_context",
                    "moderate_annulus_fraction_shift_context",
                }
                for row in rows
            ),
            "mainline_interpretation": (
                "the nominal 0.5-0.8 edge annulus label can be retained only with "
                "sidewall-aware support filtering and event-context review"
            ),
        },
        {
            **common_guard_fields(),
            "answer_axis": "interference_response",
            "answer": "yes_sidewall_angle_changes_interference_response_context",
            "evidence_rows": len(rows),
            "route_rows": len(summaries),
            "affected_route_diameter_rows": sum(
                row["response_event_shift_band"]
                in {
                    "large_interference_response_shift_context",
                    "moderate_interference_response_shift_context",
                    "small_interference_response_shift_context",
                }
                for row in rows
            ),
            "mainline_interpretation": (
                "bounded NODI event context shows peak-height/local-SNR shifts "
                "under 85deg sidewalls, so interference enhancement should be "
                "updated with geometry-aware context rather than rectangle-only "
                "assumptions"
            ),
        },
    ]


def validation_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    failures = validate_payload(payload)
    return [
        {
            "check_name": "route_diameter_coverage",
            "check_pass": payload["summary"]["integrated_route_diameter_rows"] == 78,
            "observed": payload["summary"]["integrated_route_diameter_rows"],
            "expected": 78,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "full_event_delta_join_coverage",
            "check_pass": payload["summary"]["full_event_delta_join_rows"] == 78,
            "observed": payload["summary"]["full_event_delta_join_rows"],
            "expected": 78,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "source_artifacts_present",
            "check_pass": payload["summary"]["source_missing_rows"] == 0,
            "observed": payload["summary"]["source_missing_rows"],
            "expected": 0,
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


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    table_names = (
        "integrated_route_diameter_rows",
        "route_summary_rows",
        "answer_axis_rows",
    )
    columns: set[str] = set()
    for table_name in table_names:
        if payload[table_name]:
            columns |= set().union(*(set(row) for row in payload[table_name]))
    forbidden = sorted(columns & FORBIDDEN_PRIMARY_COLUMNS)
    if forbidden:
        failures.append(f"forbidden columns present: {forbidden}")
    if payload["summary"]["integrated_route_diameter_rows"] != 78:
        failures.append("integrated route-diameter rows must cover 6 routes x 13 diameters")
    if payload["summary"]["route_summary_rows"] != 6:
        failures.append("route summary rows must cover 6 routes")
    if payload["summary"]["answer_axis_rows"] != 3:
        failures.append("answer axis rows must cover dimension, annulus, and response")
    if payload["summary"]["full_event_delta_join_rows"] != 78:
        failures.append("every 594 row must join to a 595 full-event delta row")
    if payload["summary"]["source_missing_rows"] != 0:
        failures.append("source artifacts missing")
    for table_name in table_names:
        for index, row in enumerate(payload[table_name], start=1):
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
    return failures


def semantic_digest(payload: dict[str, Any]) -> str:
    return deterministic_sha256(
        {
            "integrated_route_diameter_rows": payload["integrated_route_diameter_rows"],
            "route_summary_rows": payload["route_summary_rows"],
            "answer_axis_rows": payload["answer_axis_rows"],
        }
    )


def build_payload() -> dict[str, Any]:
    rows = integrated_route_diameter_rows()
    summaries = route_summary_rows(rows)
    axes = answer_axis_rows(rows, summaries)
    sources = source_lock_rows()
    dirty = dirty_context_rows()
    summary = {
        "artifact_id": ARTIFACT_ID,
        "disposition": DISPOSITION,
        "packet_version": PACKET_VERSION,
        "branch": git_branch(),
        "current_head": git_head(),
        "integrated_route_diameter_rows": len(rows),
        "route_summary_rows": len(summaries),
        "answer_axis_rows": len(axes),
        "full_event_delta_join_rows": sum(
            row["full_event_delta_available"] is True for row in rows
        ),
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(1 for row in sources if row["exists"] == "false"),
        "dirty_context_rows": len(dirty),
        "non_full_event_integrated_update_dirty_context_rows": sum(
            1
            for row in dirty
            if row["classification"] == "non_full_event_integrated_update_dirty_context"
        ),
        "dimension_context_rows_requiring_update_or_review": sum(
            row["dimension_context_band"]
            in {
                "geometry_respecification_context",
                "dimension_update_required_context",
                "tail_margin_review_context",
            }
            for row in rows
        ),
        "annulus_event_review_rows": sum(
            row["annulus_event_shift_band"]
            in {
                "large_annulus_fraction_shift_context",
                "moderate_annulus_fraction_shift_context",
            }
            for row in rows
        ),
        "interference_event_review_rows": sum(
            row["response_event_shift_band"]
            in {
                "large_interference_response_shift_context",
                "moderate_interference_response_shift_context",
                "small_interference_response_shift_context",
            }
            for row in rows
        ),
        "max_abs_selected_annulus_fraction_delta": max(
            abs(float(row["selected_annulus_fraction_delta"])) for row in rows
        )
        if rows
        else 0.0,
        "max_abs_mean_peak_height_delta": max(
            abs(float(row["mean_peak_height_delta"])) for row in rows
        )
        if rows
        else 0.0,
        "primary_answer_frame": (
            "sidewall_effect_on_recommended_dimensions_selected_annulus_and_interference_response"
        ),
        "not_primary_answer_frame": "route_winner_or_final_probability",
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    payload = {
        "summary": summary,
        "integrated_route_diameter_rows": rows,
        "route_summary_rows": summaries,
        "answer_axis_rows": axes,
        "source_lock_rows": sources,
        "dirty_context_rows": dirty,
        "validation_rows": [],
        "failure_rows": [{"failure_index": "", "failure": "none"}],
        "disposition": DISPOSITION,
    }
    failures = validate_payload(payload)
    if failures:
        summary["disposition"] = BLOCKED_DISPOSITION
        payload["disposition"] = BLOCKED_DISPOSITION
        payload["failure_rows"] = [
            {"failure_index": index, "failure": failure}
            for index, failure in enumerate(failures, start=1)
        ]
    payload["validation_rows"] = validation_rows(payload)
    summary["validation_rows"] = len(payload["validation_rows"])
    summary["failed_validation_rows"] = sum(
        1 for row in payload["validation_rows"] if row["check_pass"] is not True
    )
    summary["semantic_digest"] = semantic_digest(payload)
    return payload


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json",
        "integrated_rows": OUTPUT_DIR / f"{PREFIX}_INTEGRATED_ROUTE_DIAMETER_ROWS_{DATE_STAMP}.csv",
        "route_summary": OUTPUT_DIR / f"{PREFIX}_ROUTE_SUMMARY_ROWS_{DATE_STAMP}.csv",
        "answer_axis": OUTPUT_DIR / f"{PREFIX}_ANSWER_AXIS_ROWS_{DATE_STAMP}.csv",
        "validation": OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv",
        "failures": OUTPUT_DIR / f"{PREFIX}_FAILURES_{DATE_STAMP}.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv",
        "master_report": REPORT_DIR / f"596_{PREFIX}_{DATE_STAMP}.md",
    }
    write_json_atomic(outputs["status"], payload["summary"], sort_keys=True)
    write_csv_rows(outputs["integrated_rows"], payload["integrated_route_diameter_rows"])
    write_csv_rows(outputs["route_summary"], payload["route_summary_rows"])
    write_csv_rows(outputs["answer_axis"], payload["answer_axis_rows"])
    write_csv_rows(outputs["validation"], payload["validation_rows"])
    write_csv_rows(outputs["source_lock"], payload["source_lock_rows"])
    write_csv_rows(outputs["dirty_context"], payload["dirty_context_rows"])
    write_csv_rows(outputs["failures"], payload["failure_rows"])
    write_json_atomic(
        outputs["report_json"],
        {
            "summary": payload["summary"],
            "answer_axis_rows": payload["answer_axis_rows"],
            "route_summary_rows": payload["route_summary_rows"],
            "validation_rows": payload["validation_rows"],
        },
        indent=None,
        sort_keys=True,
    )
    outputs["master_report"].write_text(render_markdown(payload), encoding="utf-8")
    write_csv_rows(outputs["manifest"], manifest_rows(outputs))
    return list(outputs.values())


def manifest_rows(outputs: dict[str, Path]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_id": artifact_id,
            "path": display_path(path),
            "sha256": SELF_MANIFEST_SHA256
            if artifact_id == "manifest"
            else sha256_file(path),
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
            "# NODI Sidewall Full-Event Integrated Update Packet",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Integrated route-diameter rows: `{s['integrated_route_diameter_rows']}`",
            f"Route summary rows: `{s['route_summary_rows']}`",
            f"Answer axis rows: `{s['answer_axis_rows']}`",
            f"Full-event delta joins: `{s['full_event_delta_join_rows']}`",
            f"Failed validation rows: `{s['failed_validation_rows']}`",
            "",
            "This package integrates the 595 full sparse bounded-event execution "
            "back into the 594 dimension update context. It answers the mainline "
            "question directly: sidewall angle changes the dimension margin, the "
            "selected annulus context, and the interference-response context. It "
            "does not select a route, score a route, or emit final probability, "
            "yield, wet, or production claims.",
            "",
        ]
    )


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_sidewall_full_event_integrated_update_packet:
        print(
            "--confirm-sidewall-full-event-integrated-update-packet is required",
            file=sys.stderr,
        )
        return 2
    payload = build_payload()
    write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if payload["disposition"] != BLOCKED_DISPOSITION else 1


if __name__ == "__main__":
    raise SystemExit(main())
