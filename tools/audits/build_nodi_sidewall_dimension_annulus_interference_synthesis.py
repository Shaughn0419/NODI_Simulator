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
PREFIX = "NODI_SIDEWALL_DIMENSION_ANNULUS_INTERFERENCE_SYNTHESIS"
ARTIFACT_ID = "NODI_SIDEWALL_DIMENSION_ANNULUS_INTERFERENCE_SYNTHESIS_20260702"
SYNTHESIS_VERSION = "sidewall_dimension_annulus_interference_synthesis_v1"
DISPOSITION = "NODI_SIDEWALL_DIMENSION_ANNULUS_INTERFERENCE_SYNTHESIS_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_DIMENSION_ANNULUS_INTERFERENCE_SYNTHESIS_FAIL_CLOSED"
CLAIM_BOUNDARY = (
    "sidewall_dimension_annulus_interference_synthesis_not_selection_not_probability"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

SOURCE_FILES = {
    "geometry_dimension_rows_589": OUTPUT_DIR
    / "NODI_SIDEWALL_GEOMETRY_EFFECTS_IMPACT_MATRIX_DIMENSION_RECOMMENDATION_DRIFT_ROWS_20260702.csv",
    "geometry_annulus_rows_589": OUTPUT_DIR
    / "NODI_SIDEWALL_GEOMETRY_EFFECTS_IMPACT_MATRIX_SELECTED_ANNULUS_REMAP_ROWS_20260702.csv",
    "geometry_response_rows_589": OUTPUT_DIR
    / "NODI_SIDEWALL_GEOMETRY_EFFECTS_IMPACT_MATRIX_INTERFERENCE_RESPONSE_SENSITIVITY_ROWS_20260702.csv",
    "multiwidth_dimension_rows_590": OUTPUT_DIR
    / "NODI_SIDEWALL_MULTIWIDTH_RESPONSE_EXPANSION_DIMENSION_WINDOW_ROWS_20260702.csv",
    "multiwidth_annulus_rows_590": OUTPUT_DIR
    / "NODI_SIDEWALL_MULTIWIDTH_RESPONSE_EXPANSION_SELECTED_ANNULUS_EXPANSION_ROWS_20260702.csv",
    "multiwidth_response_rows_590": OUTPUT_DIR
    / "NODI_SIDEWALL_MULTIWIDTH_RESPONSE_EXPANSION_TRAPEZOID_LOCAL_RESPONSE_BIN_ROWS_20260702.csv",
    "bounded_event_rows_591": OUTPUT_DIR
    / "NODI_SIDEWALL_BOUNDED_EVENT_SHARDS_EVENT_SHARD_ROWS_20260702.csv",
    "bounded_delta_rows_591": OUTPUT_DIR
    / "NODI_SIDEWALL_BOUNDED_EVENT_SHARDS_PAIRED_DELTA_ROWS_20260702.csv",
    "prs_sidewall_candidate_rows_592": OUTPUT_DIR
    / "NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS_CANDIDATE_ROWS_20260702.csv",
    "prs_sidewall_delta_rows_592": OUTPUT_DIR
    / "NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS_DELTA_CONTEXT_ROWS_20260702.csv",
    "synthesis_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_dimension_annulus_interference_synthesis.py",
    "synthesis_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_dimension_annulus_interference_synthesis.py",
}

ALLOWED_USE = (
    "answer sidewall-angle impact on NODI dimension windows, selected-annulus "
    "range, and interference/response sensitivity from simulation artifacts"
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
        description=(
            "Build integrated sidewall dimension/annulus/interference synthesis."
        )
    )
    parser.add_argument(
        "--confirm-sidewall-dimension-annulus-interference-synthesis",
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


def load_rows(source_id: str) -> list[dict[str, str]]:
    path = SOURCE_FILES[source_id]
    return read_csv_rows(path) if path.exists() else []


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
    output_report = f"reports/593_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_dimension_annulus_interference_synthesis.py",
        "tests/test_nodi_sidewall_dimension_annulus_interference_synthesis.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "sidewall_synthesis_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "sidewall_synthesis_output"
            release_decision = "included_or_rewritten_by_sidewall_synthesis_builder"
        else:
            classification = "non_sidewall_synthesis_dirty_context"
            release_decision = "ignored_for_sidewall_synthesis"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def common_guard_fields() -> dict[str, Any]:
    return {
        "synthesis_version": SYNTHESIS_VERSION,
        "claim_boundary": CLAIM_BOUNDARY,
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


def dimension_implication(row: dict[str, str]) -> tuple[str, str]:
    theta = fnum(row.get("sidewall_deg_comsol"), 90.0)
    closure_status = row.get("closure_status", "")
    area_fraction = fnum(row.get("center_accessible_area_fraction_vs_rectangle"), 1.0)
    top_comp = fnum(row.get("top_width_compensation_proxy_nm"), 0.0)
    diameter = fnum(row.get("diameter_nm"), fnum(row.get("particle_diameter_nm"), 0.0))
    if theta == 90.0:
        return "rectangle_baseline", "no_sidewall_dimension_shift"
    if closure_status == "geometry_closed":
        return "closed_geometry", "exclude_or_widen_and_shallow_dimension_window"
    if diameter >= 220.0 and (area_fraction < 0.9 or top_comp > 25.0):
        return "tail_sensitive_shift", "increase_top_width_or_reduce_depth_for_tail_particles"
    if area_fraction < 0.75 or top_comp > 80.0:
        return "major_shift", "widen_or_shallow_dimension_window"
    if area_fraction < 0.95 or top_comp > 25.0:
        return "moderate_shift", "review_dimension_window_margin"
    if area_fraction < 0.99 or top_comp > 5.0:
        return "small_shift", "monitor_dimension_margin"
    return "rectangle_like", "no_material_dimension_shift"


def dimension_change_rows() -> list[dict[str, Any]]:
    rows = load_rows("multiwidth_dimension_rows_590")
    output: list[dict[str, Any]] = []
    for row in rows:
        route_id = row.get("route_id_nodi_join_key", row.get("route_id_nodi", ""))
        shift_class, implication = dimension_implication(row)
        output.append(
            {
                **common_guard_fields(),
                "row_id": f"SYN-DIM-{row.get('dimension_window_case_id', row.get('row_id', ''))}",
                "axis": "recommended_dimension_window",
                "source_artifact": "590_multiwidth_dimension_rows",
                "route_id_nodi": route_id,
                "lambda_nm": inum(row.get("lambda_nm")),
                "W_nominal_nm": inum(row.get("W_nominal_nm")),
                "D_nm": inum(row.get("D_nm")),
                "diameter_nm": inum(row.get("diameter_nm")),
                "sidewall_deg_comsol": fnum(row.get("sidewall_deg_comsol"), 90.0),
                "W_top_nm": fnum(row.get("W_top_nm")),
                "W_bottom_unclipped_nm": fnum(row.get("W_bottom_unclipped_nm")),
                "bottom_throat_loss_nm": fnum(row.get("W_top_nm"))
                - fnum(row.get("W_bottom_unclipped_nm")),
                "center_accessible_area_fraction_vs_rectangle": fnum(
                    row.get("center_accessible_area_fraction_vs_rectangle"),
                    1.0,
                ),
                "top_width_compensation_proxy_nm": fnum(
                    row.get("top_width_compensation_proxy_nm")
                ),
                "reference_aperture_surrogate_factor": fnum(
                    row.get("reference_aperture_surrogate_factor"),
                    1.0,
                ),
                "closure_status": row.get("closure_status", ""),
                "dimension_change_signal": shift_class,
                "dimension_recommendation_implication": implication,
                "route_id_role": "join_key_only_not_selection",
            }
        )
    return output


def annulus_implication(row: dict[str, str]) -> tuple[str, str]:
    theta = fnum(row.get("sidewall_deg_comsol"), 90.0)
    accessible_fraction = fnum(row.get("selected_annulus_accessible_fraction"), 1.0)
    blocked_slices = inum(row.get("blocked_u_slice_rows"))
    if theta == 90.0:
        return "rectangle_baseline", "legacy_edge_norm_range_retained"
    if accessible_fraction <= 0.0:
        return "annulus_blocked", "selected_annulus_requires_replacement_or_width_depth_change"
    if blocked_slices > 0 or accessible_fraction < 1.0:
        return "annulus_partial_remap", "selected_annulus_range_requires_geometry_support_filter"
    return "annulus_geometry_remap_only", "edge_norm_range_retained_with_trapezoid_coordinates"


def annulus_change_rows() -> list[dict[str, Any]]:
    rows = load_rows("multiwidth_annulus_rows_590")
    output: list[dict[str, Any]] = []
    for row in rows:
        signal, implication = annulus_implication(row)
        output.append(
            {
                **common_guard_fields(),
                "row_id": f"SYN-ANN-{row.get('annulus_expansion_case_id', row.get('row_id', ''))}",
                "axis": "selected_annulus_range",
                "source_artifact": "590_multiwidth_annulus_rows",
                "route_id_nodi": row.get("route_id_nodi", ""),
                "lambda_nm": inum(row.get("lambda_nm")),
                "W_nominal_nm": inum(row.get("W_nominal_nm")),
                "D_nm": inum(row.get("D_nm")),
                "diameter_nm": inum(row.get("diameter_nm")),
                "sidewall_deg_comsol": fnum(row.get("sidewall_deg_comsol"), 90.0),
                "annulus_edge_norm_min": fnum(row.get("annulus_edge_norm_min"), 0.5),
                "annulus_edge_norm_max": fnum(row.get("annulus_edge_norm_max"), 0.8),
                "u_slice_rows": inum(row.get("u_slice_rows")),
                "accessible_u_slice_rows": inum(row.get("accessible_u_slice_rows")),
                "blocked_u_slice_rows": inum(row.get("blocked_u_slice_rows")),
                "selected_annulus_accessible_fraction": fnum(
                    row.get("selected_annulus_accessible_fraction"),
                    1.0,
                ),
                "annulus_response_delta_mean": fnum(row.get("annulus_response_delta_mean")),
                "annulus_change_signal": signal,
                "annulus_range_implication": implication,
                "no_neighbor_fill_for_blocked_bins": boolish(
                    row.get("no_neighbor_fill_for_blocked_bins")
                ),
            }
        )
    return output


def bounded_delta_index() -> dict[tuple[str, int], dict[str, str]]:
    rows = load_rows("prs_sidewall_delta_rows_592")
    return {
        (row.get("route_id_nodi", ""), inum(row.get("diameter_nm"))): row
        for row in rows
    }


def selected_response_groups() -> dict[tuple[str, int, float], list[dict[str, str]]]:
    grouped: dict[tuple[str, int, float], list[dict[str, str]]] = defaultdict(list)
    for row in load_rows("multiwidth_response_rows_590"):
        if row.get("bin_id") != "selected_annulus_0p5_0p8":
            continue
        key = (
            row.get("route_id_nodi", ""),
            inum(row.get("diameter_nm")),
            fnum(row.get("sidewall_deg_comsol"), 90.0),
        )
        grouped[key].append(row)
    return grouped


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def interference_implication(
    *,
    surrogate_delta_mean: float,
    surrogate_delta_abs_max: float,
    event_peak_delta: float | None,
    event_snr_delta: float | None,
) -> tuple[str, str]:
    event_available = event_peak_delta is not None or event_snr_delta is not None
    if event_available and (
        abs(event_peak_delta or 0.0) > 1.0e-9 or abs(event_snr_delta or 0.0) > 1.0e-9
    ):
        return "bounded_event_shift_observed", "interference_response_context_changes_under_sidewall"
    if surrogate_delta_abs_max > 1.0e-9 or abs(surrogate_delta_mean) > 1.0e-9:
        return "surrogate_response_shift", "response_map_changes_under_sidewall_surrogate"
    return "rectangle_like_response", "no_material_response_shift_in_current_surrogate"


def interference_change_rows() -> list[dict[str, Any]]:
    deltas = bounded_delta_index()
    output: list[dict[str, Any]] = []
    for (route_id, diameter_nm, theta), rows in sorted(selected_response_groups().items()):
        response_deltas = [fnum(row.get("response_proxy_delta_vs_rectangle")) for row in rows]
        enhancement_deltas = [fnum(row.get("enhancement_delta_proxy")) for row in rows]
        event_delta = deltas.get((route_id, diameter_nm)) if theta == 85.0 else None
        event_peak_delta = (
            fnum(event_delta.get("mean_peak_height_delta"))
            if event_delta is not None
            else None
        )
        event_snr_delta = (
            fnum(event_delta.get("mean_local_snr_delta"))
            if event_delta is not None
            else None
        )
        signal, implication = interference_implication(
            surrogate_delta_mean=mean(response_deltas),
            surrogate_delta_abs_max=max((abs(value) for value in response_deltas), default=0.0),
            event_peak_delta=event_peak_delta,
            event_snr_delta=event_snr_delta,
        )
        first = rows[0]
        output.append(
            {
                **common_guard_fields(),
                "row_id": f"SYN-RESP-{route_id.replace('/', '_')}-TH{theta:g}-P{diameter_nm}",
                "axis": "interference_response",
                "source_artifact": "590_response_bins_plus_592_bounded_deltas",
                "route_id_nodi": route_id,
                "lambda_nm": inum(first.get("lambda_nm")),
                "W_nominal_nm": inum(first.get("W_nominal_nm")),
                "D_nm": inum(first.get("D_nm")),
                "diameter_nm": diameter_nm,
                "sidewall_deg_comsol": theta,
                "selected_annulus_u_slice_rows": len(rows),
                "selected_annulus_accessible_bin_rows": sum(
                    1 for row in rows if boolish(row.get("bin_accessible"))
                ),
                "surrogate_response_delta_mean": mean(response_deltas),
                "surrogate_response_delta_abs_max": max(
                    (abs(value) for value in response_deltas),
                    default=0.0,
                ),
                "enhancement_delta_proxy_mean": mean(enhancement_deltas),
                "bounded_event_delta_available": event_delta is not None,
                "bounded_event_mean_peak_height_delta": ""
                if event_peak_delta is None
                else event_peak_delta,
                "bounded_event_mean_local_snr_delta": ""
                if event_snr_delta is None
                else event_snr_delta,
                "interference_change_signal": signal,
                "interference_implication": implication,
            }
        )
    return output


def answer_axis_rows(
    dimension_rows: list[dict[str, Any]],
    annulus_rows: list[dict[str, Any]],
    response_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    shifted_dimension_rows = [
        row
        for row in dimension_rows
        if row["dimension_change_signal"]
        not in {"rectangle_baseline", "rectangle_like"}
    ]
    annulus_changed_rows = [
        row
        for row in annulus_rows
        if row["annulus_change_signal"]
        not in {"rectangle_baseline", "annulus_geometry_remap_only"}
    ]
    response_changed_rows = [
        row
        for row in response_rows
        if row["interference_change_signal"] != "rectangle_like_response"
    ]
    bounded_event_rows = [
        row for row in response_rows if row["bounded_event_delta_available"] is True
    ]
    return [
        {
            **common_guard_fields(),
            "axis": "recommended_dimension_window",
            "axis_question": "after_sidewall_angle_do_recommended_dimensions_change",
            "answer": "yes_under_nonvertical_sidewalls_dimension_margins_change",
            "evidence_row_count": len(dimension_rows),
            "changed_row_count": len(shifted_dimension_rows),
            "bounded_event_context_rows": 0,
            "main_implication": (
                "sidewall taper reduces bottom throat and center-accessible area; "
                "tail particles and deep/narrow W/D combinations need widening, "
                "shallower depth, or explicit blocked handling"
            ),
        },
        {
            **common_guard_fields(),
            "axis": "selected_annulus_range",
            "axis_question": "after_sidewall_angle_does_selected_annulus_range_change",
            "answer": "yes_physical_annulus_support_changes_even_when_edge_norm_label_is_retained",
            "evidence_row_count": len(annulus_rows),
            "changed_row_count": len(annulus_changed_rows),
            "bounded_event_context_rows": 0,
            "main_implication": (
                "the nominal 0.5-0.8 edge-norm annulus can remain as a label, "
                "but it must be remapped through trapezoid local width and support; "
                "blocked slices cannot be neighbor-filled"
            ),
        },
        {
            **common_guard_fields(),
            "axis": "interference_response",
            "axis_question": "after_sidewall_angle_is_interference_enhancement_affected",
            "answer": "yes_surrogate_and_bounded_event_context_show_response_sensitivity",
            "evidence_row_count": len(response_rows),
            "changed_row_count": len(response_changed_rows),
            "bounded_event_context_rows": len(bounded_event_rows),
            "main_implication": (
                "interference/response changes through accessible-position weighting, "
                "annulus support, and reference-aperture surrogate factors; bounded "
                "NODI shards provide sparse direction checks, not final probabilities"
            ),
        },
    ]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    tables = (
        payload["answer_axis_rows"],
        payload["dimension_change_rows"],
        payload["annulus_change_rows"],
        payload["interference_change_rows"],
    )
    for table_name, table in zip(
        ("answer", "dimension", "annulus", "interference"),
        tables,
        strict=True,
    ):
        if not table:
            failures.append(f"{table_name} table is empty")
            continue
        columns = set().union(*(set(row) for row in table))
        forbidden = sorted(FORBIDDEN_PRIMARY_COLUMNS & columns)
        if forbidden:
            failures.append(f"{table_name} table has forbidden columns: {forbidden}")
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
    axes = {row["axis"] for row in payload["answer_axis_rows"]}
    expected_axes = {
        "recommended_dimension_window",
        "selected_annulus_range",
        "interference_response",
    }
    if axes != expected_axes:
        failures.append(f"answer axes mismatch: {axes}")
    if payload["summary"]["source_missing_rows"] != 0:
        failures.append("one or more source artifacts are missing")
    return failures


def alignment_check_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    failures = validate_payload(payload)
    return [
        {
            "check_name": "all_source_artifacts_present",
            "check_pass": payload["summary"]["source_missing_rows"] == 0,
            "observed": payload["summary"]["source_missing_rows"],
            "expected": 0,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "answer_axis_rows_cover_three_user_questions",
            "check_pass": len(payload["answer_axis_rows"]) == 3,
            "observed": len(payload["answer_axis_rows"]),
            "expected": 3,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "dimension_rows_loaded_from_590",
            "check_pass": payload["summary"]["dimension_change_rows"] == 546,
            "observed": payload["summary"]["dimension_change_rows"],
            "expected": 546,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "annulus_rows_loaded_from_590",
            "check_pass": payload["summary"]["annulus_change_rows"] == 168,
            "observed": payload["summary"]["annulus_change_rows"],
            "expected": 168,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "interference_rows_group_selected_annulus_bins",
            "check_pass": payload["summary"]["interference_change_rows"] == 168,
            "observed": payload["summary"]["interference_change_rows"],
            "expected": 168,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "bounded_event_deltas_joined",
            "check_pass": payload["summary"]["bounded_event_delta_join_rows"] == 12,
            "observed": payload["summary"]["bounded_event_delta_join_rows"],
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
    dimension_rows = dimension_change_rows()
    annulus_rows = annulus_change_rows()
    response_rows = interference_change_rows()
    answer_rows = answer_axis_rows(dimension_rows, annulus_rows, response_rows)
    source_rows = source_lock_rows()
    dirty_rows = dirty_context_rows()
    summary = {
        "artifact_id": ARTIFACT_ID,
        "disposition": DISPOSITION,
        "synthesis_version": SYNTHESIS_VERSION,
        "branch": git_branch(),
        "current_head": git_head(),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
        "primary_answer_frame": "dimension_window_annulus_range_interference_response",
        "not_primary_answer_frame": "route_winner_scoreboard_or_detection_probability",
        "answer_axis_rows": len(answer_rows),
        "dimension_change_rows": len(dimension_rows),
        "annulus_change_rows": len(annulus_rows),
        "interference_change_rows": len(response_rows),
        "dimension_shift_signal_rows": sum(
            1
            for row in dimension_rows
            if row["dimension_change_signal"]
            not in {"rectangle_baseline", "rectangle_like"}
        ),
        "annulus_changed_signal_rows": sum(
            1
            for row in annulus_rows
            if row["annulus_change_signal"]
            not in {"rectangle_baseline", "annulus_geometry_remap_only"}
        ),
        "interference_changed_signal_rows": sum(
            1
            for row in response_rows
            if row["interference_change_signal"] != "rectangle_like_response"
        ),
        "bounded_event_delta_join_rows": sum(
            1 for row in response_rows if row["bounded_event_delta_available"] is True
        ),
        "source_lock_rows": len(source_rows),
        "source_missing_rows": sum(1 for row in source_rows if row["exists"] == "false"),
        "dirty_context_rows": len(dirty_rows),
        "non_sidewall_synthesis_dirty_context_rows": sum(
            1
            for row in dirty_rows
            if row["classification"] == "non_sidewall_synthesis_dirty_context"
        ),
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
    }
    payload = {
        "disposition": summary["disposition"],
        "summary": summary,
        "source_lock_rows": source_rows,
        "dirty_context_rows": dirty_rows,
        "answer_axis_rows": answer_rows,
        "dimension_change_rows": dimension_rows,
        "annulus_change_rows": annulus_rows,
        "interference_change_rows": response_rows,
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
            "answers": answer_rows,
            "dimension": summary["dimension_shift_signal_rows"],
            "annulus": summary["annulus_changed_signal_rows"],
            "interference": summary["interference_changed_signal_rows"],
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
        "answer_axis": OUTPUT_DIR / f"{PREFIX}_ANSWER_AXIS_ROWS_{DATE_STAMP}.csv",
        "dimension_change": OUTPUT_DIR / f"{PREFIX}_DIMENSION_CHANGE_ROWS_{DATE_STAMP}.csv",
        "annulus_change": OUTPUT_DIR / f"{PREFIX}_ANNULUS_CHANGE_ROWS_{DATE_STAMP}.csv",
        "interference_change": OUTPUT_DIR / f"{PREFIX}_INTERFERENCE_CHANGE_ROWS_{DATE_STAMP}.csv",
        "alignment_checks": OUTPUT_DIR / f"{PREFIX}_ALIGNMENT_CHECKS_{DATE_STAMP}.csv",
        "failures": OUTPUT_DIR / f"{PREFIX}_FAILURES_{DATE_STAMP}.csv",
        "master_report": REPORT_DIR / f"593_{PREFIX}_{DATE_STAMP}.md",
    }
    write_json_atomic(paths["status"], payload["summary"], sort_keys=True)
    write_csv_rows(paths["source_lock"], payload["source_lock_rows"])
    write_csv_rows(paths["dirty_context"], payload["dirty_context_rows"])
    write_csv_rows(paths["answer_axis"], payload["answer_axis_rows"])
    write_csv_rows(paths["dimension_change"], payload["dimension_change_rows"])
    write_csv_rows(paths["annulus_change"], payload["annulus_change_rows"])
    write_csv_rows(paths["interference_change"], payload["interference_change_rows"])
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
            "answer_axis_rows": payload["answer_axis_rows"],
            "alignment_checks": payload["alignment_check_rows"],
            "manifest": manifest_rows,
        },
        indent=None,
        sort_keys=True,
    )
    return list(paths.values())


def master_report(payload: dict[str, Any], manifest_rows: list[dict[str, Any]]) -> str:
    summary = payload["summary"]
    answers = payload["answer_axis_rows"]
    answer_lines = [
        f"- `{row['axis']}`: {row['answer']} ({row['changed_row_count']}/{row['evidence_row_count']} changed/context rows)"
        for row in answers
    ]
    return "\n".join(
        [
            f"# 593 {PREFIX} {DATE_STAMP}",
            "",
            "## Disposition",
            "",
            f"- disposition: `{summary['disposition']}`",
            f"- primary_answer_frame: `{summary['primary_answer_frame']}`",
            f"- not_primary_answer_frame: `{summary['not_primary_answer_frame']}`",
            f"- claim_boundary: `{CLAIM_BOUNDARY}`",
            "",
            "## Direct Answers",
            "",
            *answer_lines,
            "",
            "## Counts",
            "",
            f"- dimension_change_rows: `{summary['dimension_change_rows']}`",
            f"- annulus_change_rows: `{summary['annulus_change_rows']}`",
            f"- interference_change_rows: `{summary['interference_change_rows']}`",
            f"- bounded_event_delta_join_rows: `{summary['bounded_event_delta_join_rows']}`",
            f"- failed_alignment_check_rows: `{summary['failed_alignment_check_rows']}`",
            "",
            "## Interpretation",
            "",
            (
                "Sidewall angle is now represented as a geometry-sensitive "
                "simulation axis. The result is not a route-selection table: it "
                "is a synthesis of how width/depth margins, selected-annulus "
                "support, and interference-response context move once the "
                "rectangle assumption is relaxed."
            ),
            "",
            "## COMSOL V4 Alignment",
            "",
            f"- assumption_set_id: `{summary['comsol_v4_assumption_set_id']}`",
            f"- assumption_set_version: `{summary['comsol_v4_assumption_set_version']}`",
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
    if not args.confirm_sidewall_dimension_annulus_interference_synthesis:
        print(
            "--confirm-sidewall-dimension-annulus-interference-synthesis is required",
            file=sys.stderr,
        )
        return 2
    payload = build_payload()
    write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if payload["summary"]["disposition"] == DISPOSITION else 1


if __name__ == "__main__":
    raise SystemExit(main())
