#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.cross_section_geometry import (  # noqa: E402
    TrapezoidCrossSection,
    comsol_sidewall_deg_to_nodi_taper_deg,
)
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
from tools.audits.build_nodi_sidewall_bounded_event_shards import (  # noqa: E402
    m_to_nm,
    nm_to_m,
)
from tools.audits.build_nodi_sidewall_candidate_envelope_annulus_window_sweep import (  # noqa: E402
    execute_annulus_row,
)


DATE_STAMP = "20260703"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_FOLLOWUP_WINDOW_HIGHER_EVENT_SWEEP"
ARTIFACT_ID = "NODI_SIDEWALL_FOLLOWUP_WINDOW_HIGHER_EVENT_SWEEP_20260703"
SWEEP_VERSION = "sidewall_followup_window_higher_event_sweep_v1"
DISPOSITION_EXECUTED = "NODI_SIDEWALL_FOLLOWUP_WINDOW_HIGHER_EVENT_SWEEP_EXECUTED_READY"
DISPOSITION_PLAN = "NODI_SIDEWALL_FOLLOWUP_WINDOW_HIGHER_EVENT_SWEEP_PLAN_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_FOLLOWUP_WINDOW_HIGHER_EVENT_SWEEP_FAIL_CLOSED"
CLAIM_BOUNDARY = "followup_window_higher_event_context_not_probability_not_selection"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
PRIMARY_SIDEWALL_DEG_COMSOL = 85.0
DEFAULT_N_EVENTS = 16
DEFAULT_RANDOM_SEED = 60300
CANONICAL_WINDOW_ID = "0p5_0p8"

SOURCE_FILES = {
    "three_question_closein_status_602": OUTPUT_DIR
    / "NODI_SIDEWALL_THREE_QUESTION_CLOSEIN_SYNTHESIS_STATUS_20260703.json",
    "three_question_next_rows_602": OUTPUT_DIR
    / "NODI_SIDEWALL_THREE_QUESTION_CLOSEIN_SYNTHESIS_NEXT_SIMULATION_ROWS_20260703.csv",
    "annulus_followup_route_rows_601": OUTPUT_DIR
    / "NODI_SIDEWALL_ANNULUS_WINDOW_FOLLOWUP_SYNTHESIS_ROUTE_FOLLOWUP_ROWS_20260703.csv",
    "annulus_execute_reference_600": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_candidate_envelope_annulus_window_sweep.py",
    "followup_higher_event_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_followup_window_higher_event_sweep.py",
    "followup_higher_event_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_followup_window_higher_event_sweep.py",
}

ALLOWED_USE = (
    "execute higher-event sparse NODI follow-up on route-specific sidewall "
    "candidate-envelope annulus windows for the dimension, annulus, and "
    "interference-response mainline"
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
        description="Build/execute sidewall follow-up window higher-event sweep."
    )
    parser.add_argument(
        "--confirm-sidewall-followup-window-higher-event-sweep",
        action="store_true",
    )
    parser.add_argument("--execute-nodi", action="store_true")
    parser.add_argument("--n-events", type=int, default=DEFAULT_N_EVENTS)
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED)
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


def parse_route_id(route: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"(\d+)/W(\d+)/D(\d+)", str(route))
    if not match:
        raise ValueError(f"invalid route id: {route}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def route_case_id(route: str) -> str:
    return str(route).replace("/", "_")


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
    output_report = f"reports/603_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_followup_window_higher_event_sweep.py",
        "tests/test_nodi_sidewall_followup_window_higher_event_sweep.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "followup_window_higher_event_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "followup_window_higher_event_output"
            release_decision = "included_or_rewritten_by_followup_window_higher_event_builder"
        else:
            classification = "non_followup_window_higher_event_dirty_context"
            release_decision = "ignored_for_followup_window_higher_event"
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
        "sweep_version": SWEEP_VERSION,
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


def next_simulation_rows_602() -> list[dict[str, str]]:
    return load_rows("three_question_next_rows_602")


def plan_rows(
    *,
    n_events: int = DEFAULT_N_EVENTS,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    diameters = sorted(int(value) for value in PRS_APPROVED_DIAMETERS_NM)
    next_rows = next_simulation_rows_602()
    for route_window_index, next_row in enumerate(next_rows):
        source_route = next_row["source_route_id_nodi"]
        candidate_route = next_row["candidate_envelope_route_id_nodi"]
        lambda_nm, width_nm, depth_nm = parse_route_id(candidate_route)
        source_lambda_nm, source_width_nm, source_depth_nm = parse_route_id(source_route)
        if lambda_nm != source_lambda_nm or depth_nm != source_depth_nm:
            raise ValueError(f"candidate route changes lambda/depth: {source_route} -> {candidate_route}")
        taper = comsol_sidewall_deg_to_nodi_taper_deg(PRIMARY_SIDEWALL_DEG_COMSOL)
        geometry = TrapezoidCrossSection(
            top_width_m=nm_to_m(width_nm),
            depth_m=nm_to_m(depth_nm),
            sidewall_taper_angle_deg=taper,
        )
        inner = fnum(next_row["selected_annulus_edge_norm_min"])
        outer = fnum(next_row["selected_annulus_edge_norm_max"])
        window_id = next_row["annulus_window_id"]
        for diameter_nm in diameters:
            seed = int(random_seed + route_window_index * 1000 + diameter_nm)
            row_id = (
                f"FUW-{route_case_id(source_route)}-to-{route_case_id(candidate_route)}-"
                f"A{window_id}-P{diameter_nm}-N{n_events}-TH85"
            )
            output.append(
                {
                    **common_guard_fields(row_id),
                    "source_artifacts_json": json.dumps(
                        [
                            "602_NODI_SIDEWALL_THREE_QUESTION_CLOSEIN_SYNTHESIS_20260703",
                            "600_execute_annulus_row_reused_for_nodi_execution",
                            "route_specific_followup_window_set",
                        ],
                        sort_keys=True,
                    ),
                    "shard_case_id": row_id,
                    "source_route_id_nodi": source_route,
                    "source_route_id_role": "join_key_only_not_selection",
                    "route_id_nodi": candidate_route,
                    "candidate_envelope_route_id_nodi": candidate_route,
                    "route_id_nodi_role": "followup_window_context_not_selection",
                    "lambda_nm": lambda_nm,
                    "source_W_nominal_nm": source_width_nm,
                    "W_nominal_nm": width_nm,
                    "W_top_nm": width_nm,
                    "W_top_semantics": "candidate_envelope_runtime_top_aperture_surrogate",
                    "candidate_envelope_top_width_delta_nm": width_nm - source_width_nm,
                    "D_nm": depth_nm,
                    "depth_nm": depth_nm,
                    "diameter_nm": diameter_nm,
                    "annulus_window_id": window_id,
                    "selected_annulus_edge_norm_min": inner,
                    "selected_annulus_edge_norm_max": outer,
                    "is_canonical_annulus_window": window_id == CANONICAL_WINDOW_ID,
                    "window_reference_context": next_row.get(
                        "window_reference_context", ""
                    ),
                    "priority_context": next_row.get("priority_context", ""),
                    "particle_model": "gold_baseline_material_model",
                    "channel_cross_section_model": "trapezoid_tapered_sidewalls",
                    "sidewall_angle_convention": "comsol_from_horizontal",
                    "sidewall_deg_comsol": PRIMARY_SIDEWALL_DEG_COMSOL,
                    "sidewall_taper_angle_deg_nodi": taper,
                    "W_bottom_unclipped_nm": m_to_nm(geometry.bottom_width_unclipped_m),
                    "W_bottom_runtime_clipped_nm": m_to_nm(
                        geometry.bottom_width_runtime_clipped_m
                    ),
                    "closure_status": geometry.closure_status,
                    "n_events_requested": int(n_events),
                    "random_seed": seed,
                    "reference_model": "trapezoid_effective_aperture_surrogate",
                    "reference_spatial_mode": "cross_section_surrogate",
                    "flow_profile_model": "plug",
                    "diffusion_hindrance_model": "none",
                    "readout_preset": "tsuyama_2022_counting_10sigma",
                    "execution_status": "planned_not_executed",
                }
            )
    return output


def event_rows(*, execute_nodi: bool, n_events: int, random_seed: int) -> list[dict[str, Any]]:
    rows = plan_rows(n_events=n_events, random_seed=random_seed)
    if not execute_nodi:
        return rows
    executed: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        print(f"[followup-window] {index}/{len(rows)} {row['shard_case_id']}", flush=True)
        executed.append(execute_annulus_row(row))
    return executed


def comparison_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = {
        (
            row["source_route_id_nodi"],
            int(row["diameter_nm"]),
            row["annulus_window_id"],
        ): row
        for row in rows
    }
    output: list[dict[str, Any]] = []
    for row in rows:
        canonical = lookup.get(
            (row["source_route_id_nodi"], int(row["diameter_nm"]), CANONICAL_WINDOW_ID),
            {},
        )

        def delta(field: str) -> float | str:
            if field not in row or field not in canonical:
                return ""
            left = fnum(canonical.get(field), default=math.nan)
            right = fnum(row.get(field), default=math.nan)
            if not (math.isfinite(left) and math.isfinite(right)):
                return ""
            return right - left

        row_id = (
            f"FUW-CMP-{route_case_id(row['source_route_id_nodi'])}-"
            f"P{row['diameter_nm']}-A{row['annulus_window_id']}"
        )
        output.append(
            {
                **common_guard_fields(row_id),
                "comparison_case_id": row_id,
                "source_route_id_nodi": row["source_route_id_nodi"],
                "candidate_envelope_route_id_nodi": row["route_id_nodi"],
                "route_id_role": "followup_window_join_key_only_not_selection",
                "diameter_nm": int(row["diameter_nm"]),
                "annulus_window_id": row["annulus_window_id"],
                "selected_annulus_edge_norm_min": row[
                    "selected_annulus_edge_norm_min"
                ],
                "selected_annulus_edge_norm_max": row[
                    "selected_annulus_edge_norm_max"
                ],
                "canonical_annulus_window_id": CANONICAL_WINDOW_ID,
                "is_canonical_annulus_window": row["is_canonical_annulus_window"],
                "candidate_execution_status": row.get("execution_status", ""),
                "canonical_execution_status": canonical.get("execution_status", ""),
                "selected_annulus_fraction": fnum(row.get("selected_annulus_fraction")),
                "selected_annulus_fraction_delta_vs_canonical": delta(
                    "selected_annulus_fraction"
                ),
                "selected_annulus_n_events": inum(row.get("selected_annulus_n_events")),
                "selected_annulus_n_events_delta_vs_canonical": delta(
                    "selected_annulus_n_events"
                ),
                "mean_peak_height": fnum(row.get("mean_peak_height")),
                "mean_peak_height_delta_vs_canonical": delta("mean_peak_height"),
                "mean_local_snr": fnum(row.get("mean_local_snr")),
                "mean_local_snr_delta_vs_canonical": delta("mean_local_snr"),
                "synthetic_counting_context_rate_delta_vs_canonical": delta(
                    "synthetic_counting_context_rate"
                ),
                "window_context_status": "executed_followup_window_context"
                if row.get("execution_status") == "executed_annulus_window_nodi_shard"
                else "planned_followup_window_context",
            }
        )
    return output


def route_window_summary_rows(comparisons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in comparisons:
        grouped[(row["source_route_id_nodi"], row["annulus_window_id"])].append(row)
    output: list[dict[str, Any]] = []
    for (source_route, window_id), group in sorted(grouped.items()):
        positive_peak = sum(
            fnum(row["mean_peak_height_delta_vs_canonical"]) > 0 for row in group
        )
        positive_snr = sum(
            fnum(row["mean_local_snr_delta_vs_canonical"]) > 0 for row in group
        )
        positive_annulus = sum(
            fnum(row["selected_annulus_fraction_delta_vs_canonical"]) > 0
            for row in group
        )
        negative_annulus = sum(
            fnum(row["selected_annulus_fraction_delta_vs_canonical"]) < 0
            for row in group
        )
        row_id = f"FUW-SUM-{route_case_id(source_route)}-{window_id}"
        output.append(
            {
                **common_guard_fields(row_id),
                "source_route_id_nodi": source_route,
                "candidate_envelope_route_id_nodi": group[0][
                    "candidate_envelope_route_id_nodi"
                ],
                "route_id_role": "followup_window_summary_not_selection",
                "annulus_window_id": window_id,
                "selected_annulus_edge_norm_min": group[0][
                    "selected_annulus_edge_norm_min"
                ],
                "selected_annulus_edge_norm_max": group[0][
                    "selected_annulus_edge_norm_max"
                ],
                "is_canonical_annulus_window": group[0][
                    "is_canonical_annulus_window"
                ],
                "diameter_rows": len(group),
                "diameters_with_peak_height_above_canonical": positive_peak,
                "diameters_with_local_snr_above_canonical": positive_snr,
                "diameters_with_annulus_fraction_above_canonical": positive_annulus,
                "diameters_with_annulus_fraction_below_canonical": negative_annulus,
                "mean_selected_annulus_fraction": sum(
                    fnum(row["selected_annulus_fraction"]) for row in group
                )
                / len(group),
                "mean_peak_height": sum(fnum(row["mean_peak_height"]) for row in group)
                / len(group),
                "mean_local_snr": sum(fnum(row["mean_local_snr"]) for row in group)
                / len(group),
                "mean_peak_height_delta_vs_canonical": sum(
                    fnum(row["mean_peak_height_delta_vs_canonical"]) for row in group
                )
                / len(group),
                "mean_local_snr_delta_vs_canonical": sum(
                    fnum(row["mean_local_snr_delta_vs_canonical"]) for row in group
                )
                / len(group),
                "mean_annulus_fraction_delta_vs_canonical": sum(
                    fnum(row["selected_annulus_fraction_delta_vs_canonical"])
                    for row in group
                )
                / len(group),
                "followup_window_context": (
                    "window_changes_peak_snr_or_annulus_context"
                    if positive_peak or positive_snr or positive_annulus or negative_annulus
                    else "canonical_equivalent_context_in_followup_sweep"
                ),
            }
        )
    return output


def route_closein_rows(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in summaries:
        grouped[row["source_route_id_nodi"]].append(row)
    output: list[dict[str, Any]] = []
    for source_route, group in sorted(grouped.items()):
        noncanonical = [row for row in group if row["is_canonical_annulus_window"] is not True]
        row_id = f"FUW-CLOSEIN-{route_case_id(source_route)}"
        response_positive = sum(
            fnum(row["mean_peak_height_delta_vs_canonical"]) > 0
            or fnum(row["mean_local_snr_delta_vs_canonical"]) > 0
            for row in noncanonical
        )
        annulus_changed = sum(
            fnum(row["mean_annulus_fraction_delta_vs_canonical"]) != 0
            for row in noncanonical
        )
        output.append(
            {
                **common_guard_fields(row_id),
                "source_route_id_nodi": source_route,
                "candidate_envelope_route_id_nodi": group[0][
                    "candidate_envelope_route_id_nodi"
                ],
                "route_id_role": "followup_window_route_closein_not_selection",
                "followup_window_set_json": json.dumps(
                    [row["annulus_window_id"] for row in group], ensure_ascii=True
                ),
                "followup_window_count": len(group),
                "noncanonical_windows_with_response_positive_context": response_positive,
                "noncanonical_windows_with_annulus_change_context": annulus_changed,
                "route_closein_status": (
                    "noncanonical_window_changes_response_or_annulus_context"
                    if response_positive or annulus_changed
                    else "canonical_window_retained_no_noncanonical_gain_context"
                ),
                "next_mainline_action": (
                    "summarize_dimension_annulus_response_closein_against_602"
                ),
            }
        )
    return output


def answer_axis_rows(
    comparisons: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    noncanonical = [
        row for row in comparisons if row["is_canonical_annulus_window"] is not True
    ]
    return [
        {
            **common_guard_fields("FUW-AXIS-DIMENSION"),
            "answer_axis": "candidate_dimension_envelope",
            "answer": "candidate_dimensions_held_fixed_during_followup_window_sweep",
            "affected_rows": len({row["candidate_envelope_route_id_nodi"] for row in comparisons}),
            "route_window_rows": len(summaries),
            "mainline_interpretation": (
                "603 tests the 598/599 candidate dimensions under 601/602 "
                "route-specific annulus windows with a higher event count"
            ),
        },
        {
            **common_guard_fields("FUW-AXIS-ANNULUS"),
            "answer_axis": "selected_annulus_range",
            "answer": "route_specific_noncanonical_annulus_windows_remain_active_context",
            "affected_rows": sum(
                fnum(row["selected_annulus_fraction_delta_vs_canonical"]) != 0
                for row in noncanonical
            ),
            "route_window_rows": len(summaries),
            "mainline_interpretation": (
                "annulus remains an explicit simulation axis after width "
                "compensation; canonical 0.5-0.8 is retained as reference"
            ),
        },
        {
            **common_guard_fields("FUW-AXIS-INTERFERENCE"),
            "answer_axis": "interference_response",
            "answer": "followup_windows_change_peak_or_local_snr_context",
            "affected_rows": sum(
                fnum(row["mean_peak_height_delta_vs_canonical"]) != 0
                or fnum(row["mean_local_snr_delta_vs_canonical"]) != 0
                for row in noncanonical
            ),
            "route_window_rows": len(summaries),
            "mainline_interpretation": (
                "higher-event follow-up measures peak-height and local-SNR "
                "context shifts, not detection probability"
            ),
        },
    ]


def table_has_forbidden_columns(rows: list[dict[str, Any]]) -> bool:
    columns = set().union(*(set(row) for row in rows)) if rows else set()
    return bool(columns & FORBIDDEN_PRIMARY_COLUMNS)


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    summary = payload["summary"]
    expected_event_rows = len(next_simulation_rows_602()) * len(PRS_APPROVED_DIAMETERS_NM)
    expected_route_windows = len(next_simulation_rows_602())
    if summary["event_rows"] != expected_event_rows:
        failures.append("event rows must match 602 next rows x PRS diameters")
    if summary["comparison_rows"] != expected_event_rows:
        failures.append("comparison rows must cover every event row")
    if summary["route_window_summary_rows"] != expected_route_windows:
        failures.append("route-window summary rows must match 602 next rows")
    if summary["route_closein_rows"] != 6:
        failures.append("route close-in rows must cover six candidate envelopes")
    if summary["source_missing_rows"] != 0:
        failures.append("source artifacts missing")
    for name in (
        "event_rows",
        "comparison_rows",
        "route_window_summary_rows",
        "route_closein_rows",
        "answer_axis_rows",
    ):
        if table_has_forbidden_columns(payload[name]):
            failures.append(f"forbidden columns present in {name}")
    return failures


def validation_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    summary = payload["summary"]
    expected_event_rows = len(next_simulation_rows_602()) * len(PRS_APPROVED_DIAMETERS_NM)
    expected_route_windows = len(next_simulation_rows_602())
    checks = [
        (
            "followup_event_coverage",
            summary["event_rows"] == expected_event_rows,
            summary["event_rows"],
            expected_event_rows,
        ),
        (
            "route_window_summary_coverage",
            summary["route_window_summary_rows"] == expected_route_windows,
            summary["route_window_summary_rows"],
            expected_route_windows,
        ),
        (
            "route_closein_coverage",
            summary["route_closein_rows"] == 6,
            summary["route_closein_rows"],
            6,
        ),
        (
            "source_artifacts_present",
            summary["source_missing_rows"] == 0,
            summary["source_missing_rows"],
            0,
        ),
        (
            "no_forbidden_primary_columns",
            not validate_payload(payload),
            "pass" if not validate_payload(payload) else "; ".join(validate_payload(payload)),
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


def semantic_digest(payload: dict[str, Any]) -> str:
    return deterministic_sha256(
        {
            "comparison_rows": payload["comparison_rows"],
            "route_window_summary_rows": payload["route_window_summary_rows"],
            "route_closein_rows": payload["route_closein_rows"],
            "answer_axis_rows": payload["answer_axis_rows"],
        }
    )


def build_payload(*, execute_nodi: bool, n_events: int, random_seed: int) -> dict[str, Any]:
    rows = event_rows(
        execute_nodi=execute_nodi,
        n_events=n_events,
        random_seed=random_seed,
    )
    comparisons = comparison_rows(rows)
    summaries = route_window_summary_rows(comparisons)
    closein = route_closein_rows(summaries)
    axes = answer_axis_rows(comparisons, summaries, closein)
    sources = source_lock_rows()
    dirty = dirty_context_rows()
    noncanonical = [
        row for row in comparisons if row["is_canonical_annulus_window"] is not True
    ]
    summary = {
        "artifact_id": ARTIFACT_ID,
        "disposition": DISPOSITION_EXECUTED if execute_nodi else DISPOSITION_PLAN,
        "sweep_version": SWEEP_VERSION,
        "branch": git_branch(),
        "current_head": git_head(),
        "execute_nodi": bool(execute_nodi),
        "n_events_requested_per_case": int(n_events),
        "source_next_simulation_rows_602": len(next_simulation_rows_602()),
        "candidate_envelope_route_count": len({row["source_route_id_nodi"] for row in rows}),
        "diameter_count": len(PRS_APPROVED_DIAMETERS_NM),
        "event_rows": len(rows),
        "executed_event_rows": sum(
            row.get("execution_status") == "executed_annulus_window_nodi_shard"
            for row in rows
        ),
        "comparison_rows": len(comparisons),
        "executed_comparison_rows": sum(
            row["window_context_status"] == "executed_followup_window_context"
            for row in comparisons
        ),
        "route_window_summary_rows": len(summaries),
        "route_closein_rows": len(closein),
        "answer_axis_rows": len(axes),
        "noncanonical_rows_with_annulus_fraction_change": sum(
            fnum(row["selected_annulus_fraction_delta_vs_canonical"]) != 0
            for row in noncanonical
        ),
        "noncanonical_rows_with_peak_height_change": sum(
            fnum(row["mean_peak_height_delta_vs_canonical"]) != 0
            for row in noncanonical
        ),
        "noncanonical_rows_with_local_snr_change": sum(
            fnum(row["mean_local_snr_delta_vs_canonical"]) != 0
            for row in noncanonical
        ),
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(1 for row in sources if row["exists"] == "false"),
        "dirty_context_rows": len(dirty),
        "non_followup_window_higher_event_dirty_context_rows": sum(
            1
            for row in dirty
            if row["classification"] == "non_followup_window_higher_event_dirty_context"
        ),
        "primary_answer_frame": "followup_window_higher_event_sweep_for_dimension_annulus_response",
        "not_primary_answer_frame": "route_winner_or_final_probability",
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    payload: dict[str, Any] = {
        "summary": summary,
        "event_rows": rows,
        "comparison_rows": comparisons,
        "route_window_summary_rows": summaries,
        "route_closein_rows": closein,
        "answer_axis_rows": axes,
        "source_lock_rows": sources,
        "dirty_context_rows": dirty,
        "validation_rows": [],
        "failure_rows": [{"failure_index": "", "failure": "none"}],
        "disposition": summary["disposition"],
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
        "event_rows": OUTPUT_DIR / f"{PREFIX}_EVENT_ROWS_{DATE_STAMP}.csv",
        "comparisons": OUTPUT_DIR / f"{PREFIX}_COMPARISON_ROWS_{DATE_STAMP}.csv",
        "route_window_summary": OUTPUT_DIR / f"{PREFIX}_ROUTE_WINDOW_SUMMARY_ROWS_{DATE_STAMP}.csv",
        "route_closein": OUTPUT_DIR / f"{PREFIX}_ROUTE_CLOSEIN_ROWS_{DATE_STAMP}.csv",
        "answer_axis": OUTPUT_DIR / f"{PREFIX}_ANSWER_AXIS_ROWS_{DATE_STAMP}.csv",
        "validation": OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv",
        "failures": OUTPUT_DIR / f"{PREFIX}_FAILURES_{DATE_STAMP}.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv",
        "master_report": REPORT_DIR / f"603_{PREFIX}_{DATE_STAMP}.md",
    }
    write_json_atomic(outputs["status"], payload["summary"], sort_keys=True)
    write_csv_rows(outputs["event_rows"], payload["event_rows"])
    write_csv_rows(outputs["comparisons"], payload["comparison_rows"])
    write_csv_rows(outputs["route_window_summary"], payload["route_window_summary_rows"])
    write_csv_rows(outputs["route_closein"], payload["route_closein_rows"])
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
            "route_closein_rows": payload["route_closein_rows"],
            "route_window_summary_rows": payload["route_window_summary_rows"],
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
    lines = [
        "# NODI Sidewall Follow-Up Window Higher-Event Sweep",
        "",
        f"Disposition: `{s['disposition']}`",
        f"Artifact ID: `{s['artifact_id']}`",
        f"Execute NODI: `{s['execute_nodi']}`",
        f"Event rows: `{s['event_rows']}`",
        f"Executed event rows: `{s['executed_event_rows']}`",
        f"Route-window summary rows: `{s['route_window_summary_rows']}`",
        f"Route close-in rows: `{s['route_closein_rows']}`",
        f"Failed validation rows: `{s['failed_validation_rows']}`",
        "",
        "This package executes the 602 route-specific follow-up annulus windows at a higher event count. It keeps the candidate top-width envelopes fixed and measures selected-annulus, peak-height, and local-SNR context. It is not route selection, probability, yield, wet, q_ch weighting, true W_eff, fabrication, or production evidence.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_sidewall_followup_window_higher_event_sweep:
        print(
            "--confirm-sidewall-followup-window-higher-event-sweep is required",
            file=sys.stderr,
        )
        return 2
    payload = build_payload(
        execute_nodi=bool(args.execute_nodi),
        n_events=int(args.n_events),
        random_seed=int(args.random_seed),
    )
    write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if payload["disposition"] != BLOCKED_DISPOSITION else 1


if __name__ == "__main__":
    raise SystemExit(main())
