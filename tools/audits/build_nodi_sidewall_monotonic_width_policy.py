#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
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
from tools.audits.build_nodi_sidewall_distribution_weighted_width_sweep import (  # noqa: E402
    CANONICAL_WINDOW_ID,
    WEIGHTING_MODES,
    fnum,
    inum,
    parse_route_id,
)


DATE_STAMP = "20260703"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_MONOTONIC_WIDTH_POLICY"
ARTIFACT_ID = "NODI_SIDEWALL_MONOTONIC_WIDTH_POLICY_20260703"
SYNTHESIS_VERSION = "sidewall_monotonic_width_policy_v1"
DISPOSITION = "NODI_SIDEWALL_MONOTONIC_WIDTH_POLICY_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_MONOTONIC_WIDTH_POLICY_FAIL_CLOSED"
CLAIM_BOUNDARY = "monotonic_width_policy_context_not_route_selection"

SOURCE_FILES = {
    "width_summary_608": OUTPUT_DIR
    / "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_WIDTH_SWEEP_WIDTH_SUMMARY_ROWS_20260703.csv",
    "boundary_summary_609": OUTPUT_DIR
    / "NODI_SIDEWALL_BOUNDARY_WIDTH_FOLLOWUP_BOUNDARY_WIDTH_SUMMARY_ROWS_20260703.csv",
    "extended_summary_610": OUTPUT_DIR
    / "NODI_SIDEWALL_EXTENDED_WIDTH_ENVELOPE_EXTENDED_WIDTH_SUMMARY_ROWS_20260703.csv",
    "dimension_context_608": OUTPUT_DIR
    / "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_WIDTH_SWEEP_DIMENSION_CONTEXT_ROWS_20260703.csv",
    "dimension_context_609": OUTPUT_DIR
    / "NODI_SIDEWALL_BOUNDARY_WIDTH_FOLLOWUP_BOUNDARY_DIMENSION_CONTEXT_ROWS_20260703.csv",
    "dimension_context_610": OUTPUT_DIR
    / "NODI_SIDEWALL_EXTENDED_WIDTH_ENVELOPE_EXTENDED_DIMENSION_CONTEXT_ROWS_20260703.csv",
    "monotonic_width_policy_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_monotonic_width_policy.py",
    "monotonic_width_policy_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_monotonic_width_policy.py",
}

ALLOWED_USE = (
    "summarize sidewall-induced top-width, annulus, and response-surface context "
    "after executed 608-610 width sweeps"
)
BLOCKED_USE = (
    "route winner, scalar route score, exact P(x,u) probability claim, final yield, "
    "final detection probability, wet experimental claim, q_ch weighting, true W_eff, "
    "or production runtime ingestion"
)
FORBIDDEN_PRIMARY_COLUMNS = {
    "winner",
    "route_score",
    "rank",
    "recommended_candidate",
    "detection_probability",
    "yield",
    "W_eff",
    "q_ch_eta",
    "rank_under_surrogate",
}

STAGE_SUMMARY_SOURCES = [
    ("608_candidate_width_sweep", "width_summary_608"),
    ("609_boundary_followup", "boundary_summary_609"),
    ("610_extended_width_envelope", "extended_summary_610"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build sidewall monotonic width policy packet.")
    parser.add_argument("--confirm-sidewall-monotonic-width-policy", action="store_true")
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
    return run_git(["rev-parse", "--abbrev-ref", "HEAD"])


def git_status_lines() -> list[str]:
    output = run_git(["status", "--short"])
    return [line for line in output.splitlines() if line.strip()]


def git_path_from_status_line(line: str) -> str:
    return line[3:] if len(line) > 3 else line


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def deterministic_sha256(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def common_guard_fields(row_id: str) -> dict[str, Any]:
    return {
        "synthesis_version": SYNTHESIS_VERSION,
        "row_id": row_id,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_exact_pxu_probability_grid": True,
        "not_detection_probability": True,
        "not_yield": True,
        "not_selection_metric_claim": True,
        "not_winner": True,
        "not_qch_weighted": True,
        "not_true_W_eff": True,
        "not_production_recommendation": True,
        "decision_use_allowed": False,
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "comsol_v4_assumption_set_sha256": COMSOL_V4_ASSUMPTION_SET_SHA256,
    }


def load_rows(source_id: str) -> list[dict[str, str]]:
    path = SOURCE_FILES[source_id]
    return read_csv_rows(path) if path.exists() else []


def source_lock_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, path in SOURCE_FILES.items():
        rows.append(
            {
                **common_guard_fields(f"SOURCE-{source_id}"),
                "source_id": source_id,
                "path": display_path(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    tracked_prefixes = (
        "tools/audits/build_nodi_sidewall_monotonic_width_policy.py",
        "tests/test_nodi_sidewall_monotonic_width_policy.py",
        "reports/611_NODI_SIDEWALL_MONOTONIC_WIDTH_POLICY_20260703.md",
        "reports/joint_interface_20260703/NODI_SIDEWALL_MONOTONIC_WIDTH_POLICY_",
    )
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path.startswith(tracked_prefixes):
            classification = "this_artifact_scope"
            release_decision = "include_or_review_before_commit"
        else:
            classification = "pre_existing_or_unrelated_dirty_context"
            release_decision = "ignored_by_this_artifact"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def width_trajectory_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stage_id, source_id in STAGE_SUMMARY_SOURCES:
        for row in load_rows(source_id):
            source_route = row["source_route_id_nodi"]
            _, source_w_nm, _ = parse_route_id(source_route)
            width_nm = inum(row["W_top_nm"])
            rows.append(
                {
                    **common_guard_fields(
                        f"TRAJ-{stage_id}-{source_route.replace('/', '_')}-{row['weighting_mode']}-W{width_nm}"
                    ),
                    "stage_id": stage_id,
                    "source_route_id_nodi": source_route,
                    "weighting_mode": row["weighting_mode"],
                    "candidate_envelope_route_id_nodi": row["candidate_envelope_route_id_nodi"],
                    "source_W_nominal_nm": source_w_nm,
                    "candidate_envelope_W_top_nm": inum(row["candidate_envelope_W_top_nm"]),
                    "W_top_nm": width_nm,
                    "width_delta_vs_candidate_nm": inum(row["width_sweep_delta_vs_candidate_nm"]),
                    "width_context": row["width_context"],
                    "weighted_event_rows": inum(row["weighted_event_rows"]),
                    "leading_mass_window_context": row["leading_mass_window_context"],
                    "leading_peak_contribution_window_context": row[
                        "leading_peak_contribution_window_context"
                    ],
                    "leading_snr_contribution_window_context": row[
                        "leading_snr_contribution_window_context"
                    ],
                    "mean_weighted_peak_contribution": fnum(row["mean_weighted_peak_contribution"]),
                    "mean_weighted_local_snr_contribution": fnum(
                        row["mean_weighted_local_snr_contribution"]
                    ),
                    "mean_weighted_selected_annulus_fraction": fnum(
                        row["mean_weighted_selected_annulus_fraction"]
                    ),
                }
            )
    return rows


def response_surface_rows(trajectory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in trajectory_rows:
        grouped[(row["source_route_id_nodi"], row["weighting_mode"], inum(row["W_top_nm"]))].append(row)

    rows: list[dict[str, Any]] = []
    for (source_route, mode, width_nm), group in sorted(grouped.items()):
        peak_values = [fnum(row["mean_weighted_peak_contribution"]) for row in group]
        snr_values = [fnum(row["mean_weighted_local_snr_contribution"]) for row in group]
        annulus_values = [
            fnum(row["mean_weighted_selected_annulus_fraction"]) for row in group
        ]
        rows.append(
            {
                **common_guard_fields(f"SURFACE-{source_route.replace('/', '_')}-{mode}-W{width_nm}"),
                "source_route_id_nodi": source_route,
                "weighting_mode": mode,
                "W_top_nm": width_nm,
                "stage_ids_json": json.dumps(sorted({row["stage_id"] for row in group}), ensure_ascii=True),
                "stage_occurrence_count": len(group),
                "mean_peak_contribution_across_stages": sum(peak_values) / len(peak_values),
                "mean_snr_contribution_across_stages": sum(snr_values) / len(snr_values),
                "mean_annulus_fraction_across_stages": sum(annulus_values) / len(annulus_values),
                "leading_peak_window_mode": Counter(
                    row["leading_peak_contribution_window_context"] for row in group
                ).most_common(1)[0][0],
                "leading_snr_window_mode": Counter(
                    row["leading_snr_contribution_window_context"] for row in group
                ).most_common(1)[0][0],
                "leading_mass_window_mode": Counter(
                    row["leading_mass_window_context"] for row in group
                ).most_common(1)[0][0],
            }
        )
    return rows


def adjacent_non_decreasing_fraction(values: list[float]) -> float:
    if len(values) < 2:
        return 1.0
    comparisons = [b >= a for a, b in zip(values, values[1:])]
    return sum(1 for value in comparisons if value) / len(comparisons)


def dimension_policy_rows(surface_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in surface_rows:
        grouped[(row["source_route_id_nodi"], row["weighting_mode"])].append(row)

    rows: list[dict[str, Any]] = []
    for (source_route, mode), group in sorted(grouped.items()):
        ordered = sorted(group, key=lambda row: inum(row["W_top_nm"]))
        widths = [inum(row["W_top_nm"]) for row in ordered]
        peaks = [fnum(row["mean_peak_contribution_across_stages"]) for row in ordered]
        snrs = [fnum(row["mean_snr_contribution_across_stages"]) for row in ordered]
        annulus_values = [fnum(row["mean_annulus_fraction_across_stages"]) for row in ordered]
        leading_peak = max(ordered, key=lambda row: fnum(row["mean_peak_contribution_across_stages"]))
        leading_snr = max(ordered, key=lambda row: fnum(row["mean_snr_contribution_across_stages"]))
        leading_annulus = max(ordered, key=lambda row: fnum(row["mean_annulus_fraction_across_stages"]))
        max_width = max(widths)
        _, source_w_nm, _ = parse_route_id(source_route)
        candidate_w_nm = inum(load_rows("width_summary_608")[0]["candidate_envelope_W_top_nm"])
        route_candidates = [
            inum(row["candidate_envelope_W_top_nm"])
            for row in width_trajectory_rows()
            if row["source_route_id_nodi"] == source_route
        ]
        if route_candidates:
            candidate_w_nm = route_candidates[0]
        peak_upper_edge = inum(leading_peak["W_top_nm"]) == max_width
        snr_upper_edge = inum(leading_snr["W_top_nm"]) == max_width
        peak_fraction = adjacent_non_decreasing_fraction(peaks)
        snr_fraction = adjacent_non_decreasing_fraction(snrs)
        if peak_upper_edge and peak_fraction >= 0.8:
            policy = "monotonic_peak_response_constraint_required"
            size_context = "sidewall_response_pushes_wider_than_tested_envelope"
        elif peak_upper_edge or snr_upper_edge:
            policy = "upper_edge_response_context_requires_constraint_review"
            size_context = "sidewall_response_has_upper_edge_width_pressure"
        else:
            policy = "local_width_context_available"
            size_context = "sidewall_response_has_internal_width_context"
        rows.append(
            {
                **common_guard_fields(f"POLICY-DIM-{source_route.replace('/', '_')}-{mode}"),
                "source_route_id_nodi": source_route,
                "weighting_mode": mode,
                "source_W_nominal_nm": source_w_nm,
                "candidate_envelope_W_top_nm": candidate_w_nm,
                "max_tested_W_top_nm": max_width,
                "leading_peak_W_top_nm": inum(leading_peak["W_top_nm"]),
                "leading_snr_W_top_nm": inum(leading_snr["W_top_nm"]),
                "leading_annulus_fraction_W_top_nm": inum(leading_annulus["W_top_nm"]),
                "peak_upper_edge": peak_upper_edge,
                "snr_upper_edge": snr_upper_edge,
                "peak_adjacent_non_decreasing_fraction": peak_fraction,
                "snr_adjacent_non_decreasing_fraction": snr_fraction,
                "annulus_adjacent_non_decreasing_fraction": adjacent_non_decreasing_fraction(
                    annulus_values
                ),
                "width_grid_json": json.dumps(widths, ensure_ascii=True),
                "dimension_policy_context": policy,
                "size_recommendation_context_after_sidewall": size_context,
                "not_final_recommendation": True,
            }
        )
    return rows


def annulus_policy_rows(surface_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in surface_rows:
        grouped[(row["source_route_id_nodi"], row["weighting_mode"])].append(row)

    rows: list[dict[str, Any]] = []
    for (source_route, mode), group in sorted(grouped.items()):
        peak_windows = Counter(row["leading_peak_window_mode"] for row in group)
        snr_windows = Counter(row["leading_snr_window_mode"] for row in group)
        mass_windows = Counter(row["leading_mass_window_mode"] for row in group)
        leading_peak_window = peak_windows.most_common(1)[0][0]
        leading_snr_window = snr_windows.most_common(1)[0][0]
        leading_mass_window = mass_windows.most_common(1)[0][0]
        noncanonical = {
            leading_peak_window,
            leading_snr_window,
            leading_mass_window,
        } - {CANONICAL_WINDOW_ID}
        context = (
            "sidewall_annulus_context_shifted_from_canonical"
            if noncanonical
            else "sidewall_annulus_context_retains_canonical_window"
        )
        rows.append(
            {
                **common_guard_fields(f"POLICY-ANN-{source_route.replace('/', '_')}-{mode}"),
                "source_route_id_nodi": source_route,
                "weighting_mode": mode,
                "canonical_annulus_window_id": CANONICAL_WINDOW_ID,
                "leading_mass_window_mode": leading_mass_window,
                "leading_peak_window_mode": leading_peak_window,
                "leading_snr_window_mode": leading_snr_window,
                "peak_window_counts_json": json.dumps(dict(sorted(peak_windows.items())), ensure_ascii=True),
                "snr_window_counts_json": json.dumps(dict(sorted(snr_windows.items())), ensure_ascii=True),
                "mass_window_counts_json": json.dumps(dict(sorted(mass_windows.items())), ensure_ascii=True),
                "annulus_policy_context": context,
                "not_final_annulus_selection": True,
            }
        )
    return rows


def question_rows(
    dimension_rows: list[dict[str, Any]],
    annulus_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    comsol_dimension_rows = [
        row for row in dimension_rows if row["weighting_mode"] != "uniform_edge_mass"
    ]
    comsol_annulus_rows = [
        row for row in annulus_rows if row["weighting_mode"] != "uniform_edge_mass"
    ]
    return [
        {
            **common_guard_fields("QUESTION-611-DIMENSION"),
            "question_id": "size_recommendation_delta_after_sidewall",
            "answer_context": "sidewall branch shows sustained wider-width pressure, not a local optimum",
            "comsol_rows_with_peak_upper_edge": sum(row["peak_upper_edge"] is True for row in comsol_dimension_rows),
            "comsol_rows_with_monotonic_constraint_policy": sum(
                row["dimension_policy_context"] == "monotonic_peak_response_constraint_required"
                for row in comsol_dimension_rows
            ),
            "next_action": "define_dimension_constraints_or_objective_before_more_width_expansion",
        },
        {
            **common_guard_fields("QUESTION-611-ANNULUS"),
            "question_id": "selected_annulus_range_delta_after_sidewall",
            "answer_context": "annulus window context summarized across 608-610 width envelopes",
            "comsol_rows_with_noncanonical_annulus_context": sum(
                row["annulus_policy_context"] == "sidewall_annulus_context_shifted_from_canonical"
                for row in comsol_annulus_rows
            ),
            "next_action": "carry_annulus_policy_into_sidewall_dimension_decision_packet",
        },
        {
            **common_guard_fields("QUESTION-611-INTERFERENCE"),
            "question_id": "interference_response_delta_after_sidewall",
            "answer_context": "weighted peak/SNR response surface remains width-sensitive under sidewall geometry",
            "comsol_rows_peak_upper_edge": sum(row["peak_upper_edge"] is True for row in comsol_dimension_rows),
            "next_action": "separate response enhancement context from final detection or yield claims",
        },
    ]


def validation_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        rows.append(
            {
                "check_id": check_id,
                "status": "pass" if passed else "fail",
                "detail": detail,
            }
        )

    trajectory = payload["width_trajectory_rows"]
    surface = payload["response_surface_rows"]
    dimensions = payload["dimension_policy_rows"]
    annulus = payload["annulus_policy_rows"]
    add("trajectory_rows_cover_608_609_610", len(trajectory) == 252, f"width_trajectory_rows={len(trajectory)}")
    add("response_surface_rows_cover_unique_widths", len(surface) == 198, f"response_surface_rows={len(surface)}")
    add("dimension_policy_rows_cover_six_routes_times_three_modes", len(dimensions) == 18, f"dimension_policy_rows={len(dimensions)}")
    add("annulus_policy_rows_cover_six_routes_times_three_modes", len(annulus) == 18, f"annulus_policy_rows={len(annulus)}")
    add(
        "comsol_peak_upper_edge_all_rows",
        sum(row["peak_upper_edge"] is True for row in dimensions if row["weighting_mode"] != "uniform_edge_mass") == 12,
        "12 COMSOL-weighted rows keep peak response at the upper tested width",
    )
    add(
        "v4_assumption_hash_bound",
        all(
            row["comsol_v4_assumption_set_sha256"] == COMSOL_V4_ASSUMPTION_SET_SHA256
            for table in (trajectory, surface, dimensions, annulus)
            for row in table
        ),
        COMSOL_V4_ASSUMPTION_SET_SHA256,
    )
    add(
        "no_forbidden_primary_columns",
        no_forbidden_primary_columns(payload),
        "outputs avoid score/winner/yield/detection/W_eff/q_ch primary columns",
    )
    return rows


def no_forbidden_primary_columns(payload: dict[str, Any]) -> bool:
    for table_name in (
        "width_trajectory_rows",
        "response_surface_rows",
        "dimension_policy_rows",
        "annulus_policy_rows",
        "question_rows",
    ):
        rows = payload[table_name]
        columns = set().union(*(set(row) for row in rows)) if rows else set()
        if FORBIDDEN_PRIMARY_COLUMNS.intersection(columns):
            return False
    return True


def manifest_rows(paths: list[Path]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_id": ARTIFACT_ID,
            "path": display_path(path),
            "sha256": sha256_file(path) if path.exists() else "",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for path in paths
    ]


def build_payload() -> dict[str, Any]:
    trajectory = width_trajectory_rows()
    surface = response_surface_rows(trajectory)
    dimensions = dimension_policy_rows(surface)
    annulus = annulus_policy_rows(surface)
    questions = question_rows(dimensions, annulus)
    payload: dict[str, Any] = {
        "artifact_id": ARTIFACT_ID,
        "synthesis_version": SYNTHESIS_VERSION,
        "date_stamp": DATE_STAMP,
        "disposition": DISPOSITION,
        "claim_boundary": CLAIM_BOUNDARY,
        "git_head": git_head(),
        "git_branch": git_branch(),
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "comsol_v4_assumption_set_sha256": COMSOL_V4_ASSUMPTION_SET_SHA256,
        "summary": {
            "width_trajectory_rows": len(trajectory),
            "response_surface_rows": len(surface),
            "dimension_policy_rows": len(dimensions),
            "annulus_policy_rows": len(annulus),
            "question_rows": len(questions),
            "comsol_peak_upper_edge_rows": sum(
                row["peak_upper_edge"] is True
                for row in dimensions
                if row["weighting_mode"] != "uniform_edge_mass"
            ),
            "exact_pxu_probability_grid_available_now": False,
            "next_executable_block": "dimension_constraints_or_objective_packet",
        },
        "width_trajectory_rows": trajectory,
        "response_surface_rows": surface,
        "dimension_policy_rows": dimensions,
        "annulus_policy_rows": annulus,
        "question_rows": questions,
        "source_lock_rows": source_lock_rows(),
        "dirty_context_rows": dirty_context_rows(),
    }
    validation = validation_rows(payload)
    payload["validation_rows"] = validation
    payload["summary"]["failed_validation_rows"] = sum(
        1 for row in validation if row["status"] != "pass"
    )
    if payload["summary"]["failed_validation_rows"]:
        payload["disposition"] = BLOCKED_DISPOSITION
    payload["payload_sha256"] = deterministic_sha256(
        {
            key: value
            for key, value in payload.items()
            if key not in {"payload_sha256", "dirty_context_rows"}
        }
    )
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    return [
        f"{row['check_id']}: {row['detail']}"
        for row in payload["validation_rows"]
        if row["status"] != "pass"
    ]


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    dimension_rows = sorted(
        payload["dimension_policy_rows"],
        key=lambda row: (row["source_route_id_nodi"], row["weighting_mode"]),
    )
    annulus_rows = sorted(
        payload["annulus_policy_rows"],
        key=lambda row: (row["source_route_id_nodi"], row["weighting_mode"]),
    )
    lines = [
        "# NODI sidewall monotonic width policy",
        "",
        "## Mainline",
        "",
        (
            "This artifact combines the executed 608, 609, and 610 width sweeps. "
            "It does not declare a route winner; it records whether the sidewall-aware "
            "response surface has an internal width context or keeps pressing against "
            "the upper tested envelope."
        ),
        "",
        "## Counts",
        "",
        f"- width trajectory rows: {summary['width_trajectory_rows']}",
        f"- response surface rows: {summary['response_surface_rows']}",
        f"- dimension policy rows: {summary['dimension_policy_rows']}",
        f"- annulus policy rows: {summary['annulus_policy_rows']}",
        f"- COMSOL-weighted peak-upper-edge rows: {summary['comsol_peak_upper_edge_rows']}",
        f"- failed validation rows: {summary['failed_validation_rows']}",
        "",
        "## Dimension Context",
        "",
        (
            "| source route | weighting mode | candidate W_top nm | max tested W_top nm | "
            "leading peak W_top nm | leading SNR W_top nm | policy |"
        ),
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in dimension_rows:
        lines.append(
            "| {source} | {mode} | {candidate} | {maxw} | {peak} | {snr} | {policy} |".format(
                source=row["source_route_id_nodi"],
                mode=row["weighting_mode"],
                candidate=row["candidate_envelope_W_top_nm"],
                maxw=row["max_tested_W_top_nm"],
                peak=row["leading_peak_W_top_nm"],
                snr=row["leading_snr_W_top_nm"],
                policy=row["dimension_policy_context"],
            )
        )
    lines.extend(
        [
            "",
            "## Annulus Context",
            "",
            "| source route | weighting mode | peak window mode | SNR window mode | annulus context |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in annulus_rows:
        lines.append(
            "| {source} | {mode} | {peak} | {snr} | {context} |".format(
                source=row["source_route_id_nodi"],
                mode=row["weighting_mode"],
                peak=row["leading_peak_window_mode"],
                snr=row["leading_snr_window_mode"],
                context=row["annulus_policy_context"],
            )
        )
    lines.extend(
        [
            "",
            "## Main Answer",
            "",
            (
                "Within the current sidewall-aware surrogate, COMSOL-weighted response "
                "does change the dimension context: peak response remains at the upper "
                "tested width for all COMSOL-weighted rows. This is evidence of wider-width "
                "pressure, not a final size recommendation. The next step is to define "
                "the dimension objective/constraints that convert the monotonic response "
                "surface into a recommended design envelope."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json"
    report_json_path = OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json"
    trajectory_path = OUTPUT_DIR / f"{PREFIX}_WIDTH_TRAJECTORY_ROWS_{DATE_STAMP}.csv"
    surface_path = OUTPUT_DIR / f"{PREFIX}_RESPONSE_SURFACE_ROWS_{DATE_STAMP}.csv"
    dimension_path = OUTPUT_DIR / f"{PREFIX}_DIMENSION_POLICY_ROWS_{DATE_STAMP}.csv"
    annulus_path = OUTPUT_DIR / f"{PREFIX}_ANNULUS_POLICY_ROWS_{DATE_STAMP}.csv"
    question_path = OUTPUT_DIR / f"{PREFIX}_QUESTION_ROWS_{DATE_STAMP}.csv"
    validation_path = OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv"
    source_lock_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv"
    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv"
    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv"
    report_md_path = REPORT_DIR / f"611_{PREFIX}_{DATE_STAMP}.md"

    status_payload = {
        key: payload[key]
        for key in (
            "artifact_id",
            "synthesis_version",
            "date_stamp",
            "disposition",
            "claim_boundary",
            "git_head",
            "git_branch",
            "comsol_v4_assumption_set_id",
            "comsol_v4_assumption_set_version",
            "comsol_v4_assumption_set_sha256",
            "summary",
            "payload_sha256",
        )
    }
    write_json_atomic(status_path, status_payload, sort_keys=True)
    write_json_atomic(report_json_path, payload, sort_keys=True)
    write_csv_rows(trajectory_path, payload["width_trajectory_rows"])
    write_csv_rows(surface_path, payload["response_surface_rows"])
    write_csv_rows(dimension_path, payload["dimension_policy_rows"])
    write_csv_rows(annulus_path, payload["annulus_policy_rows"])
    write_csv_rows(question_path, payload["question_rows"])
    write_csv_rows(validation_path, payload["validation_rows"])
    write_csv_rows(source_lock_path, payload["source_lock_rows"])
    write_csv_rows(
        dirty_path,
        payload["dirty_context_rows"]
        or [{"path": "", "git_status": "", "classification": "clean", "release_decision": "none"}],
    )
    paths = [
        status_path,
        report_json_path,
        trajectory_path,
        surface_path,
        dimension_path,
        annulus_path,
        question_path,
        validation_path,
        source_lock_path,
        dirty_path,
        report_md_path,
    ]
    report_md_path.write_text(render_report(payload), encoding="utf-8", newline="\n")
    write_csv_rows(manifest_path, manifest_rows(paths))
    paths.append(manifest_path)
    return paths


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_sidewall_monotonic_width_policy:
        print("--confirm-sidewall-monotonic-width-policy is required", file=sys.stderr)
        return 2
    payload = build_payload()
    failures = validate_payload(payload)
    paths = write_outputs(payload)
    print(json.dumps(payload["summary"], sort_keys=True))
    for path in paths:
        print(display_path(path))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
