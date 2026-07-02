#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Iterable
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
    PRS_APPROVED_DIAMETERS_NM,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260703"
SOURCE_DATE_598_599 = "20260702"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
SOURCE_DIR_598_599 = PROJECT_ROOT / f"reports/joint_interface_{SOURCE_DATE_598_599}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_THREE_QUESTION_CLOSEIN_SYNTHESIS"
ARTIFACT_ID = "NODI_SIDEWALL_THREE_QUESTION_CLOSEIN_SYNTHESIS_20260703"
SYNTHESIS_VERSION = "sidewall_three_question_closein_synthesis_v1"
DISPOSITION = "NODI_SIDEWALL_THREE_QUESTION_CLOSEIN_SYNTHESIS_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_THREE_QUESTION_CLOSEIN_SYNTHESIS_FAIL_CLOSED"
CLAIM_BOUNDARY = "three_question_closein_context_not_probability_not_selection"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CANONICAL_WINDOW_ID = "0p5_0p8"
RECOMMENDED_N_EVENTS_PER_ROUTE_DIAMETER_WINDOW = 16

SOURCE_FILES = {
    "dimension_status_598": SOURCE_DIR_598_599
    / "NODI_SIDEWALL_CANDIDATE_DIMENSION_RECOMMENDATION_SYNTHESIS_STATUS_20260702.json",
    "dimension_route_rows_598": SOURCE_DIR_598_599
    / "NODI_SIDEWALL_CANDIDATE_DIMENSION_RECOMMENDATION_SYNTHESIS_ROUTE_RECOMMENDATION_ROWS_20260702.csv",
    "higher_event_status_599": SOURCE_DIR_598_599
    / "NODI_SIDEWALL_CANDIDATE_ENVELOPE_HIGHER_EVENT_SWEEP_STATUS_20260702.json",
    "higher_event_route_rows_599": SOURCE_DIR_598_599
    / "NODI_SIDEWALL_CANDIDATE_ENVELOPE_HIGHER_EVENT_SWEEP_ROUTE_SUMMARY_ROWS_20260702.csv",
    "annulus_window_status_600": OUTPUT_DIR
    / "NODI_SIDEWALL_CANDIDATE_ENVELOPE_ANNULUS_WINDOW_SWEEP_STATUS_20260703.json",
    "annulus_window_route_rows_600": OUTPUT_DIR
    / "NODI_SIDEWALL_CANDIDATE_ENVELOPE_ANNULUS_WINDOW_SWEEP_ROUTE_WINDOW_SUMMARY_ROWS_20260703.csv",
    "annulus_followup_status_601": OUTPUT_DIR
    / "NODI_SIDEWALL_ANNULUS_WINDOW_FOLLOWUP_SYNTHESIS_STATUS_20260703.json",
    "annulus_followup_route_rows_601": OUTPUT_DIR
    / "NODI_SIDEWALL_ANNULUS_WINDOW_FOLLOWUP_SYNTHESIS_ROUTE_FOLLOWUP_ROWS_20260703.csv",
    "three_question_closein_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_three_question_closein_synthesis.py",
    "three_question_closein_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_three_question_closein_synthesis.py",
}

ALLOWED_USE = (
    "synthesize the sidewall-angle mainline answers for dimension changes, "
    "annulus-window changes, and interference-response changes before the next "
    "large NODI simulation block"
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
WINDOW_EDGES = {
    "0p4_0p7": ("0.4", "0.7"),
    "0p5_0p8": ("0.5", "0.8"),
    "0p6_0p9": ("0.6", "0.9"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the sidewall three-question close-in synthesis."
    )
    parser.add_argument(
        "--confirm-sidewall-three-question-closein-synthesis",
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
    output_report = f"reports/602_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_three_question_closein_synthesis.py",
        "tests/test_nodi_sidewall_three_question_closein_synthesis.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "three_question_closein_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "three_question_closein_output"
            release_decision = "included_or_rewritten_by_three_question_closein_builder"
        else:
            classification = "non_three_question_closein_dirty_context"
            release_decision = "ignored_for_three_question_closein"
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


def common_guard_fields(row_id: str) -> dict[str, Any]:
    return {
        "synthesis_version": SYNTHESIS_VERSION,
        "row_id": row_id,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "not_detection_probability": True,
        "not_yield": True,
        "not_selection_metric_claim": True,
        "not_winner": True,
        "not_qch_weighted": True,
        "not_true_W_eff": True,
        "not_production_recommendation": True,
        "claim_boundary": CLAIM_BOUNDARY,
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "comsol_v4_assumption_set_sha256": COMSOL_V4_ASSUMPTION_SET_SHA256,
    }


def index_by_route(rows: Iterable[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("source_route_id_nodi", ""): row for row in rows}


def route_case_id(route: str) -> str:
    return route.replace("/", "_")


def route_closein_rows() -> list[dict[str, Any]]:
    dimension_rows = index_by_route(load_rows("dimension_route_rows_598"))
    higher_rows = index_by_route(load_rows("higher_event_route_rows_599"))
    followup_rows = index_by_route(load_rows("annulus_followup_route_rows_601"))
    output: list[dict[str, Any]] = []

    for source_route in sorted(dimension_rows):
        dim = dimension_rows[source_route]
        higher = higher_rows.get(source_route, {})
        followup = followup_rows.get(source_route, {})
        window_set = json.loads(followup.get("followup_window_set_json", "[]") or "[]")
        width_delta = inum(dim.get("candidate_envelope_top_width_delta_nm"))
        response_rows = inum(higher.get("candidate_rows_with_response_improvement"))
        annulus_rows = inum(higher.get("candidate_rows_with_annulus_improvement"))
        tradeoff_rows = inum(higher.get("candidate_rows_with_annulus_tradeoff"))
        route_diameter_rows = max(
            inum(higher.get("route_diameter_rows")),
            len(PRS_APPROVED_DIAMETERS_NM),
        )
        followup_case_rows = len(window_set)
        planned_rows = route_diameter_rows * followup_case_rows
        planned_event_trials = planned_rows * RECOMMENDED_N_EVENTS_PER_ROUTE_DIAMETER_WINDOW
        if width_delta > 0 and response_rows > 0 and followup_case_rows > 1:
            closein_status = (
                "dimension_changed_response_positive_annulus_window_followup_ready"
            )
        elif width_delta > 0 and response_rows > 0:
            closein_status = "dimension_changed_response_positive_canonical_window_only"
        else:
            closein_status = "requires_route_level_review"
        output.append(
            {
                **common_guard_fields(f"CLOSEIN-{route_case_id(source_route)}"),
                "source_route_id_nodi": source_route,
                "candidate_envelope_route_id_nodi": dim.get(
                    "candidate_envelope_route_id_nodi", ""
                ),
                "route_id_role": "three_question_closein_context_not_selection",
                "source_W_nominal_nm": dim.get("source_W_nominal_nm", ""),
                "candidate_envelope_W_top_nm": dim.get(
                    "candidate_envelope_W_top_nm", ""
                ),
                "candidate_envelope_top_width_delta_nm": width_delta,
                "dimension_delta_status": (
                    "candidate_top_width_increased_after_sidewall_compensation"
                    if width_delta > 0
                    else "no_candidate_top_width_increase_detected"
                ),
                "higher_event_n_events_requested": inum(
                    higher.get("candidate_n_events_requested")
                ),
                "route_diameter_rows": route_diameter_rows,
                "higher_rows_with_response_improvement": response_rows,
                "higher_rows_with_annulus_improvement": annulus_rows,
                "higher_rows_with_annulus_tradeoff": tradeoff_rows,
                "max_peak_height_delta_context": fnum(
                    higher.get("max_candidate_minus_original_mean_peak_height_delta")
                ),
                "max_selected_annulus_fraction_delta_context": fnum(
                    higher.get(
                        "max_candidate_minus_original_selected_annulus_fraction_delta"
                    )
                ),
                "followup_window_set_json": json.dumps(window_set, ensure_ascii=True),
                "followup_window_count": followup_case_rows,
                "annulus_window_followup_policy_context": followup.get(
                    "annulus_window_followup_policy_context", ""
                ),
                "windows_with_positive_response_context": inum(
                    followup.get("windows_with_positive_response_context")
                ),
                "windows_with_positive_annulus_fraction_context": inum(
                    followup.get("windows_with_positive_annulus_fraction_context")
                ),
                "closein_status": closein_status,
                "next_large_block_action": (
                    "run_higher_event_followup_window_sweep_on_candidate_envelopes"
                ),
                "recommended_n_events_per_route_diameter_window": (
                    RECOMMENDED_N_EVENTS_PER_ROUTE_DIAMETER_WINDOW
                ),
                "planned_route_diameter_window_rows": planned_rows,
                "planned_event_trials": planned_event_trials,
                "primary_question_coverage": (
                    "dimension_delta;selected_annulus_range_delta;"
                    "interference_response_delta"
                ),
                "sparse_simulation_context_only": True,
            }
        )
    return output


def route_window_summary_rows() -> list[dict[str, str]]:
    return load_rows("annulus_window_route_rows_600")


def route_window_lookup() -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row.get("source_route_id_nodi", ""), row.get("annulus_window_id", "")): row
        for row in route_window_summary_rows()
    }


def next_simulation_rows(closein_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    window_lookup = route_window_lookup()
    output: list[dict[str, Any]] = []
    for row in closein_rows:
        source_route = str(row["source_route_id_nodi"])
        windows = json.loads(str(row["followup_window_set_json"]))
        for window_id in windows:
            window_row = window_lookup.get((source_route, window_id), {})
            edge_min, edge_max = WINDOW_EDGES.get(window_id, ("", ""))
            if len(windows) == 3:
                priority_context = "full_inner_canonical_outer_closein"
            elif window_id == CANONICAL_WINDOW_ID:
                priority_context = "canonical_reference_retained"
            else:
                priority_context = "noncanonical_window_closein"
            output.append(
                {
                    **common_guard_fields(
                        f"NEXT-{route_case_id(source_route)}-{window_id}"
                    ),
                    "source_route_id_nodi": source_route,
                    "candidate_envelope_route_id_nodi": row[
                        "candidate_envelope_route_id_nodi"
                    ],
                    "route_id_role": "next_simulation_context_not_selection",
                    "annulus_window_id": window_id,
                    "selected_annulus_edge_norm_min": window_row.get(
                        "selected_annulus_edge_norm_min", edge_min
                    ),
                    "selected_annulus_edge_norm_max": window_row.get(
                        "selected_annulus_edge_norm_max", edge_max
                    ),
                    "window_reference_context": (
                        "canonical_reference_window"
                        if window_id == CANONICAL_WINDOW_ID
                        else "noncanonical_followup_window"
                    ),
                    "planned_particle_diameter_count": len(PRS_APPROVED_DIAMETERS_NM),
                    "planned_particle_diameter_grid_nm_json": json.dumps(
                        list(PRS_APPROVED_DIAMETERS_NM), ensure_ascii=True
                    ),
                    "recommended_n_events_per_route_diameter_window": (
                        RECOMMENDED_N_EVENTS_PER_ROUTE_DIAMETER_WINDOW
                    ),
                    "planned_route_diameter_window_rows": len(PRS_APPROVED_DIAMETERS_NM),
                    "planned_event_trials": (
                        len(PRS_APPROVED_DIAMETERS_NM)
                        * RECOMMENDED_N_EVENTS_PER_ROUTE_DIAMETER_WINDOW
                    ),
                    "mean_peak_height_delta_vs_canonical_context": fnum(
                        window_row.get("mean_peak_height_delta_vs_canonical")
                    ),
                    "mean_annulus_fraction_delta_vs_canonical_context": fnum(
                        window_row.get("mean_annulus_fraction_delta_vs_canonical")
                    ),
                    "priority_context": priority_context,
                    "simulation_intent": (
                        "closein_dimension_annulus_response_joint_sweep"
                    ),
                    "sparse_simulation_context_only": True,
                }
            )
    return output


def question_rows(
    closein_rows: list[dict[str, Any]], next_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    width_deltas = [inum(row["candidate_envelope_top_width_delta_nm"]) for row in closein_rows]
    response_routes = [
        row
        for row in closein_rows
        if inum(row["higher_rows_with_response_improvement"]) > 0
    ]
    noncanonical_routes = [
        row for row in closein_rows if inum(row["followup_window_count"]) > 1
    ]
    planned_rows = sum(inum(row["planned_route_diameter_window_rows"]) for row in next_rows)
    planned_events = sum(inum(row["planned_event_trials"]) for row in next_rows)
    return [
        {
            **common_guard_fields("QUESTION-DIMENSION-DELTA"),
            "axis_order": 1,
            "question_id": "size_recommendation_delta_after_sidewall",
            "question_text": "Does adding sidewall angle change NODI recommended dimensions?",
            "answer_status": "changed_candidate_top_width_envelope_for_6_of_6_routes",
            "evidence_sources": "598_dimension_synthesis;599_higher_event_sweep",
            "route_count": len(closein_rows),
            "routes_with_observed_delta": sum(1 for delta in width_deltas if delta > 0),
            "min_candidate_top_width_delta_nm": min(width_deltas) if width_deltas else 0,
            "max_candidate_top_width_delta_nm": max(width_deltas) if width_deltas else 0,
            "next_large_block": (
                "hold_candidate_envelope_widths_fixed_for_followup_window_sweep"
            ),
            "planned_route_diameter_window_rows": planned_rows,
            "planned_event_trials": planned_events,
        },
        {
            **common_guard_fields("QUESTION-ANNULUS-DELTA"),
            "axis_order": 2,
            "question_id": "selected_annulus_range_delta_after_sidewall",
            "question_text": "Does adding sidewall angle change selected-annulus ranges?",
            "answer_status": "noncanonical_annulus_followup_windows_for_6_of_6_routes",
            "evidence_sources": "600_annulus_window_sweep;601_annulus_followup_synthesis",
            "route_count": len(closein_rows),
            "routes_with_observed_delta": len(noncanonical_routes),
            "min_candidate_top_width_delta_nm": min(width_deltas) if width_deltas else 0,
            "max_candidate_top_width_delta_nm": max(width_deltas) if width_deltas else 0,
            "next_large_block": (
                "sweep_canonical_and_noncanonical_annulus_windows_per_route"
            ),
            "planned_route_diameter_window_rows": planned_rows,
            "planned_event_trials": planned_events,
        },
        {
            **common_guard_fields("QUESTION-RESPONSE-DELTA"),
            "axis_order": 3,
            "question_id": "interference_response_delta_after_sidewall",
            "question_text": "Does adding sidewall angle affect interference enhancement?",
            "answer_status": "peak_response_context_changed_for_6_of_6_routes",
            "evidence_sources": "599_higher_event_sweep;600_annulus_window_sweep",
            "route_count": len(closein_rows),
            "routes_with_observed_delta": len(response_routes),
            "min_candidate_top_width_delta_nm": min(width_deltas) if width_deltas else 0,
            "max_candidate_top_width_delta_nm": max(width_deltas) if width_deltas else 0,
            "next_large_block": (
                "increase_event_count_on_candidate_dimensions_and_followup_windows"
            ),
            "planned_route_diameter_window_rows": planned_rows,
            "planned_event_trials": planned_events,
        },
    ]


def table_has_forbidden_columns(rows: Iterable[dict[str, Any]]) -> bool:
    columns: set[str] = set()
    for row in rows:
        columns.update(row)
    return bool(columns & FORBIDDEN_PRIMARY_COLUMNS)


def validation_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    closein = payload["route_closein_rows"]
    questions = payload["question_rows"]
    next_rows = payload["next_simulation_rows"]
    source_missing = payload["summary"]["source_missing_rows"]
    checks = [
        (
            "source_artifacts_present",
            source_missing == 0,
            str(source_missing),
            "0",
        ),
        (
            "three_canonical_questions_present",
            {row["question_id"] for row in questions}
            == {
                "size_recommendation_delta_after_sidewall",
                "selected_annulus_range_delta_after_sidewall",
                "interference_response_delta_after_sidewall",
            },
            str(len(questions)),
            "3",
        ),
        (
            "route_closein_coverage",
            len(closein) == 6,
            str(len(closein)),
            "6",
        ),
        (
            "all_routes_have_dimension_delta",
            all(inum(row["candidate_envelope_top_width_delta_nm"]) > 0 for row in closein),
            str(
                sum(
                    1
                    for row in closein
                    if inum(row["candidate_envelope_top_width_delta_nm"]) > 0
                )
            ),
            "6",
        ),
        (
            "all_routes_have_noncanonical_annulus_followup",
            all(inum(row["followup_window_count"]) > 1 for row in closein),
            str(sum(1 for row in closein if inum(row["followup_window_count"]) > 1)),
            "6",
        ),
        (
            "all_routes_have_response_improvement_context",
            all(inum(row["higher_rows_with_response_improvement"]) > 0 for row in closein),
            str(
                sum(
                    1
                    for row in closein
                    if inum(row["higher_rows_with_response_improvement"]) > 0
                )
            ),
            "6",
        ),
        (
            "next_simulation_rows_cover_followup_windows",
            len(next_rows) == sum(inum(row["followup_window_count"]) for row in closein),
            str(len(next_rows)),
            str(sum(inum(row["followup_window_count"]) for row in closein)),
        ),
        (
            "no_forbidden_primary_columns",
            not any(
                table_has_forbidden_columns(rows)
                for rows in (closein, questions, next_rows)
            ),
            "pass",
            "pass",
        ),
    ]
    return [
        {
            "check_name": name,
            "check_pass": passed,
            "observed": observed,
            "expected": expected,
            "hard_fail_if_false": True,
        }
        for name, passed, observed, expected in checks
    ]


def validate_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in validation_rows(payload)
        if str(row["check_pass"]).lower() != "true"
    ]


def build_payload() -> dict[str, Any]:
    source_rows = source_lock_rows()
    dirty_rows = dirty_context_rows()
    closein_rows = route_closein_rows()
    next_rows = next_simulation_rows(closein_rows)
    questions = question_rows(closein_rows, next_rows)
    source_missing_rows = sum(1 for row in source_rows if row["exists"] != "true")
    route_candidate_envelopes = {
        row["source_route_id_nodi"]: row["candidate_envelope_route_id_nodi"]
        for row in closein_rows
    }
    summary = {
        "artifact_id": ARTIFACT_ID,
        "synthesis_version": SYNTHESIS_VERSION,
        "disposition": DISPOSITION,
        "branch": git_branch(),
        "current_head": git_head(),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
        "primary_answer_frame": "sidewall_dimension_annulus_interference_three_question_closein",
        "not_primary_answer_frame": "route_winner_or_final_probability",
        "route_closein_rows": len(closein_rows),
        "question_rows": len(questions),
        "next_simulation_rows": len(next_rows),
        "routes_with_candidate_dimension_change": sum(
            1
            for row in closein_rows
            if inum(row["candidate_envelope_top_width_delta_nm"]) > 0
        ),
        "routes_with_noncanonical_annulus_followup_windows": sum(
            1 for row in closein_rows if inum(row["followup_window_count"]) > 1
        ),
        "routes_with_higher_event_response_improvement": sum(
            1 for row in closein_rows if inum(row["higher_rows_with_response_improvement"]) > 0
        ),
        "planned_route_diameter_window_rows": sum(
            inum(row["planned_route_diameter_window_rows"]) for row in next_rows
        ),
        "planned_event_trials": sum(inum(row["planned_event_trials"]) for row in next_rows),
        "recommended_n_events_per_route_diameter_window": (
            RECOMMENDED_N_EVENTS_PER_ROUTE_DIAMETER_WINDOW
        ),
        "route_candidate_envelopes_json": json.dumps(
            route_candidate_envelopes, sort_keys=True, ensure_ascii=True
        ),
        "source_lock_rows": len(source_rows),
        "source_missing_rows": source_missing_rows,
        "dirty_context_rows": len(dirty_rows),
        "non_three_question_closein_dirty_context_rows": sum(
            1
            for row in dirty_rows
            if row["classification"] == "non_three_question_closein_dirty_context"
        ),
    }
    payload: dict[str, Any] = {
        "summary": summary,
        "route_closein_rows": closein_rows,
        "question_rows": questions,
        "next_simulation_rows": next_rows,
        "source_lock_rows": source_rows,
        "dirty_context_rows": dirty_rows,
        "disposition": DISPOSITION,
    }
    failures = validate_payload(payload)
    summary["failed_validation_rows"] = len(failures)
    payload["validation_rows"] = validation_rows(payload)
    payload["failures"] = failures
    if failures:
        payload["disposition"] = BLOCKED_DISPOSITION
        summary["disposition"] = BLOCKED_DISPOSITION
    summary["semantic_digest"] = deterministic_sha256(
        {
            "route_closein_rows": closein_rows,
            "question_rows": questions,
            "next_simulation_rows": next_rows,
            "validation_rows": payload["validation_rows"],
        }
    )
    return payload


def manifest_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        exists = path.exists()
        rows.append(
            {
                "artifact_id": ARTIFACT_ID,
                "path": display_path(path),
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    rows.append(
        {
            "artifact_id": ARTIFACT_ID,
            "path": f"reports/joint_interface_{DATE_STAMP}/{PREFIX}_MANIFEST_{DATE_STAMP}.csv",
            "exists": "true",
            "sha256": SELF_MANIFEST_SHA256,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "claim_boundary": CLAIM_BOUNDARY,
        }
    )
    return rows


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json"
    report_json_path = OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json"
    route_path = OUTPUT_DIR / f"{PREFIX}_ROUTE_CLOSEIN_ROWS_{DATE_STAMP}.csv"
    question_path = OUTPUT_DIR / f"{PREFIX}_QUESTION_ROWS_{DATE_STAMP}.csv"
    next_path = OUTPUT_DIR / f"{PREFIX}_NEXT_SIMULATION_ROWS_{DATE_STAMP}.csv"
    source_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv"
    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv"
    validation_path = OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv"
    failure_path = OUTPUT_DIR / f"{PREFIX}_FAILURES_{DATE_STAMP}.csv"
    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv"
    md_path = REPORT_DIR / f"602_{PREFIX}_{DATE_STAMP}.md"

    write_json_atomic(status_path, payload["summary"])
    write_json_atomic(
        report_json_path,
        {
            "summary": payload["summary"],
            "route_closein_rows": payload["route_closein_rows"],
            "question_rows": payload["question_rows"],
            "next_simulation_rows": payload["next_simulation_rows"],
            "validation_rows": payload["validation_rows"],
            "failures": payload["failures"],
        },
    )
    write_csv_rows(route_path, payload["route_closein_rows"])
    write_csv_rows(question_path, payload["question_rows"])
    write_csv_rows(next_path, payload["next_simulation_rows"])
    write_csv_rows(source_path, payload["source_lock_rows"])
    write_csv_rows(dirty_path, payload["dirty_context_rows"])
    write_csv_rows(validation_path, payload["validation_rows"])
    write_csv_rows(failure_path, payload["failures"] or [{"failure": "none"}])

    md_path.write_text(render_markdown(payload), encoding="utf-8", newline="\n")
    outputs.extend(
        [
            status_path,
            report_json_path,
            route_path,
            question_path,
            next_path,
            source_path,
            dirty_path,
            validation_path,
            failure_path,
            md_path,
        ]
    )
    write_csv_rows(manifest_path, manifest_rows(outputs))
    outputs.append(manifest_path)
    return outputs


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    question_lines = [
        f"- `{row['question_id']}`: `{row['answer_status']}`"
        for row in payload["question_rows"]
    ]
    route_lines = [
        "- `{source}` -> `{candidate}`; windows `{windows}`; status `{status}`".format(
            source=row["source_route_id_nodi"],
            candidate=row["candidate_envelope_route_id_nodi"],
            windows=row["followup_window_set_json"],
            status=row["closein_status"],
        )
        for row in payload["route_closein_rows"]
    ]
    return "\n".join(
        [
            "# NODI Sidewall Three-Question Close-In Synthesis",
            "",
            f"Disposition: `{summary['disposition']}`",
            f"Artifact ID: `{summary['artifact_id']}`",
            f"Route close-in rows: `{summary['route_closein_rows']}`",
            f"Question rows: `{summary['question_rows']}`",
            f"Next simulation rows: `{summary['next_simulation_rows']}`",
            f"Planned route-diameter-window rows: `{summary['planned_route_diameter_window_rows']}`",
            f"Planned event trials: `{summary['planned_event_trials']}`",
            f"Failed validation rows: `{summary['failed_validation_rows']}`",
            "",
            "This packet closes in the sidewall-angle mainline around the three user questions: dimension changes, annulus-window changes, and interference-response changes. It consumes 598-601 artifacts and prepares the next large sparse NODI simulation block without route selection, probability, yield, wet, fabrication, q_ch weighting, true W_eff, or production claims.",
            "",
            "## Question Status",
            *question_lines,
            "",
            "## Route Close-In Rows",
            *route_lines,
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_three_question_closein_synthesis:
        raise SystemExit(
            "--confirm-sidewall-three-question-closein-synthesis is required"
        )
    payload = build_payload()
    paths = write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    print("wrote:")
    for path in paths:
        print(f"- {display_path(path)}")
    return 0 if payload["disposition"] == DISPOSITION else 2


if __name__ == "__main__":
    raise SystemExit(main())
