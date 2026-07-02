#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
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
)


DATE_STAMP = "20260703"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_DIMENSION_OBJECTIVE_PACKET"
ARTIFACT_ID = "NODI_SIDEWALL_DIMENSION_OBJECTIVE_PACKET_20260703"
SYNTHESIS_VERSION = "sidewall_dimension_objective_packet_v1"
DISPOSITION = "NODI_SIDEWALL_DIMENSION_OBJECTIVE_PACKET_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_DIMENSION_OBJECTIVE_PACKET_FAIL_CLOSED"
CLAIM_BOUNDARY = "assumption_driven_dimension_objective_context_not_route_selection"

OBJECTIVE_FUNCTION_ID = "balanced_peak_snr_95pct_min_width_v1"
OBJECTIVE_VERSION = "1.0.0"
OBJECTIVE_CLAIM_LEVEL = "assumption_driven_simulation_policy_not_route_winner"
PEAK_RETENTION_THRESHOLD = 0.95
SNR_RETENTION_THRESHOLD = 0.95

SOURCE_FILES = {
    "response_surface_611": OUTPUT_DIR
    / "NODI_SIDEWALL_MONOTONIC_WIDTH_POLICY_RESPONSE_SURFACE_ROWS_20260703.csv",
    "dimension_policy_611": OUTPUT_DIR
    / "NODI_SIDEWALL_MONOTONIC_WIDTH_POLICY_DIMENSION_POLICY_ROWS_20260703.csv",
    "annulus_policy_611": OUTPUT_DIR
    / "NODI_SIDEWALL_MONOTONIC_WIDTH_POLICY_ANNULUS_POLICY_ROWS_20260703.csv",
    "question_rows_611": OUTPUT_DIR
    / "NODI_SIDEWALL_MONOTONIC_WIDTH_POLICY_QUESTION_ROWS_20260703.csv",
    "dimension_objective_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_dimension_objective_packet.py",
    "dimension_objective_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_dimension_objective_packet.py",
}

ALLOWED_USE = (
    "derive an assumption-driven sidewall top-width envelope from the executed "
    "608-610 response surface and 611 monotonic policy"
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build sidewall dimension objective packet.")
    parser.add_argument("--confirm-sidewall-dimension-objective-packet", action="store_true")
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
        "tools/audits/build_nodi_sidewall_dimension_objective_packet.py",
        "tests/test_nodi_sidewall_dimension_objective_packet.py",
        "reports/612_NODI_SIDEWALL_DIMENSION_OBJECTIVE_PACKET_20260703.md",
        "reports/joint_interface_20260703/NODI_SIDEWALL_DIMENSION_OBJECTIVE_PACKET_",
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


def dimension_policy_lookup() -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row["source_route_id_nodi"], row["weighting_mode"]): row
        for row in load_rows("dimension_policy_611")
    }


def annulus_policy_lookup() -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row["source_route_id_nodi"], row["weighting_mode"]): row
        for row in load_rows("annulus_policy_611")
    }


def objective_width_for_group(group: list[dict[str, str]]) -> dict[str, Any]:
    ordered = sorted(group, key=lambda row: inum(row["W_top_nm"]))
    max_peak = max(fnum(row["mean_peak_contribution_across_stages"]) for row in ordered)
    max_snr = max(fnum(row["mean_snr_contribution_across_stages"]) for row in ordered)
    max_annulus = max(fnum(row["mean_annulus_fraction_across_stages"]) for row in ordered)
    selected = ordered[-1]
    for row in ordered:
        peak_retention = fnum(row["mean_peak_contribution_across_stages"]) / max_peak
        snr_retention = fnum(row["mean_snr_contribution_across_stages"]) / max_snr
        if (
            peak_retention >= PEAK_RETENTION_THRESHOLD
            and snr_retention >= SNR_RETENTION_THRESHOLD
        ):
            selected = row
            break
    return {
        "selected_row": selected,
        "max_width_row": ordered[-1],
        "max_peak": max_peak,
        "max_snr": max_snr,
        "max_annulus": max_annulus,
        "peak_retention": fnum(selected["mean_peak_contribution_across_stages"]) / max_peak,
        "snr_retention": fnum(selected["mean_snr_contribution_across_stages"]) / max_snr,
        "annulus_retention": (
            fnum(selected["mean_annulus_fraction_across_stages"]) / max_annulus
            if max_annulus
            else 0.0
        ),
    }


def dimension_objective_rows() -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in load_rows("response_surface_611"):
        grouped[(row["source_route_id_nodi"], row["weighting_mode"])].append(row)
    dim_lookup = dimension_policy_lookup()
    ann_lookup = annulus_policy_lookup()

    rows: list[dict[str, Any]] = []
    for (source_route, mode), group in sorted(grouped.items()):
        objective = objective_width_for_group(group)
        selected = objective["selected_row"]
        max_row = objective["max_width_row"]
        dim = dim_lookup[(source_route, mode)]
        ann = ann_lookup[(source_route, mode)]
        candidate_w = inum(dim["candidate_envelope_W_top_nm"])
        objective_w = inum(selected["W_top_nm"])
        max_tested_w = inum(max_row["W_top_nm"])
        rows.append(
            {
                **common_guard_fields(f"OBJ-DIM-{source_route.replace('/', '_')}-{mode}"),
                "source_route_id_nodi": source_route,
                "weighting_mode": mode,
                "objective_function_id": OBJECTIVE_FUNCTION_ID,
                "objective_version": OBJECTIVE_VERSION,
                "objective_type": "response_retention_min_width_envelope",
                "objective_claim_level": OBJECTIVE_CLAIM_LEVEL,
                "peak_retention_threshold": PEAK_RETENTION_THRESHOLD,
                "snr_retention_threshold": SNR_RETENTION_THRESHOLD,
                "dimension_constraint_fields_json": json.dumps(
                    {
                        "min_width_source": "executed_608_609_610_response_surface",
                        "max_width_source": "max_tested_width_not_fabrication_cap",
                        "objective_rule": "smallest tested W_top meeting peak and SNR retention thresholds",
                        "forbidden_interpretation": "not winner, not route score, not production recommendation",
                    },
                    sort_keys=True,
                ),
                "candidate_envelope_W_top_nm": candidate_w,
                "objective_W_top_nm": objective_w,
                "objective_delta_vs_candidate_nm": objective_w - candidate_w,
                "max_tested_W_top_nm": max_tested_w,
                "objective_width_savings_vs_max_tested_nm": max_tested_w - objective_w,
                "peak_retention_at_objective": objective["peak_retention"],
                "snr_retention_at_objective": objective["snr_retention"],
                "annulus_fraction_retention_at_objective": objective["annulus_retention"],
                "peak_upper_edge_in_611": dim["peak_upper_edge"],
                "snr_upper_edge_in_611": dim["snr_upper_edge"],
                "dimension_policy_context_611": dim["dimension_policy_context"],
                "annulus_policy_context_611": ann["annulus_policy_context"],
                "leading_peak_window_mode": ann["leading_peak_window_mode"],
                "leading_snr_window_mode": ann["leading_snr_window_mode"],
                "canonical_annulus_window_id": CANONICAL_WINDOW_ID,
                "width_grid_json": dim["width_grid_json"],
                "objective_interpretation": (
                    "smallest_width_meeting_peak_and_snr_retention_thresholds"
                ),
                "not_final_route_or_fabrication_decision": True,
            }
        )
    return rows


def objective_summary_rows(objective_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in objective_rows:
        grouped[row["source_route_id_nodi"]].append(row)
    rows: list[dict[str, Any]] = []
    for source_route, group in sorted(grouped.items()):
        comsol_rows = [row for row in group if row["weighting_mode"] != "uniform_edge_mass"]
        objective_widths = [inum(row["objective_W_top_nm"]) for row in comsol_rows]
        deltas = [inum(row["objective_delta_vs_candidate_nm"]) for row in comsol_rows]
        annulus_contexts = sorted({row["annulus_policy_context_611"] for row in comsol_rows})
        rows.append(
            {
                **common_guard_fields(f"OBJ-SUM-{source_route.replace('/', '_')}"),
                "source_route_id_nodi": source_route,
                "objective_function_id": OBJECTIVE_FUNCTION_ID,
                "comsol_weighted_objective_widths_json": json.dumps(objective_widths, ensure_ascii=True),
                "comsol_weighted_objective_width_min_nm": min(objective_widths),
                "comsol_weighted_objective_width_max_nm": max(objective_widths),
                "comsol_weighted_delta_vs_candidate_min_nm": min(deltas),
                "comsol_weighted_delta_vs_candidate_max_nm": max(deltas),
                "comsol_annulus_contexts_json": json.dumps(annulus_contexts, ensure_ascii=True),
                "summary_context": "assumption_driven_sidewall_dimension_envelope",
                "not_route_winner": True,
            }
        )
    return rows


def question_rows(objective_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    comsol_rows = [row for row in objective_rows if row["weighting_mode"] != "uniform_edge_mass"]
    annulus_shifted = sum(
        row["annulus_policy_context_611"] == "sidewall_annulus_context_shifted_from_canonical"
        for row in comsol_rows
    )
    return [
        {
            **common_guard_fields("QUESTION-612-DIMENSION"),
            "question_id": "size_recommendation_delta_after_sidewall",
            "answer_context": (
                "under balanced 95pct peak/SNR simulation objective, most COMSOL-weighted "
                "rows require a wider top-width envelope while retained rows are explicit"
            ),
            "comsol_rows_with_objective_width_above_candidate": sum(
                inum(row["objective_delta_vs_candidate_nm"]) > 0 for row in comsol_rows
            ),
            "comsol_rows_with_objective_width_equal_candidate": sum(
                inum(row["objective_delta_vs_candidate_nm"]) == 0 for row in comsol_rows
            ),
            "objective_function_id": OBJECTIVE_FUNCTION_ID,
            "next_action": "propagate_objective_widths_to_sidewall_annulus_and_response_packet",
        },
        {
            **common_guard_fields("QUESTION-612-ANNULUS"),
            "question_id": "selected_annulus_range_delta_after_sidewall",
            "answer_context": "COMSOL-weighted annulus contexts are mixed between canonical and shifted windows",
            "comsol_rows_with_shifted_annulus_context": annulus_shifted,
            "canonical_annulus_window_id": CANONICAL_WINDOW_ID,
            "next_action": "carry_annulus_context_with_objective_widths",
        },
        {
            **common_guard_fields("QUESTION-612-INTERFERENCE"),
            "question_id": "interference_response_delta_after_sidewall",
            "answer_context": (
                "objective widths preserve at least 95pct of the tested peak and SNR "
                "response maxima under the current surrogate"
            ),
            "min_peak_retention_at_objective": min(
                fnum(row["peak_retention_at_objective"]) for row in comsol_rows
            ),
            "min_snr_retention_at_objective": min(
                fnum(row["snr_retention_at_objective"]) for row in comsol_rows
            ),
            "next_action": "summarize_interference_response_delta_without_detection_probability",
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

    objectives = payload["dimension_objective_rows"]
    summaries = payload["objective_summary_rows"]
    comsol_rows = [row for row in objectives if row["weighting_mode"] != "uniform_edge_mass"]
    add("dimension_objective_rows_cover_six_routes_times_three_modes", len(objectives) == 18, f"dimension_objective_rows={len(objectives)}")
    add("objective_summary_rows_cover_six_routes", len(summaries) == 6, f"objective_summary_rows={len(summaries)}")
    above_count = sum(inum(row["objective_delta_vs_candidate_nm"]) > 0 for row in comsol_rows)
    equal_count = sum(inum(row["objective_delta_vs_candidate_nm"]) == 0 for row in comsol_rows)
    add(
        "comsol_objective_widths_not_below_candidate",
        all(inum(row["objective_delta_vs_candidate_nm"]) >= 0 for row in comsol_rows),
        f"above_candidate={above_count}; equal_candidate={equal_count}; total={len(comsol_rows)}",
    )
    add(
        "all_comsol_objective_retention_thresholds_met",
        all(
            fnum(row["peak_retention_at_objective"]) >= PEAK_RETENTION_THRESHOLD
            and fnum(row["snr_retention_at_objective"]) >= SNR_RETENTION_THRESHOLD
            for row in comsol_rows
        ),
        "peak/SNR retention thresholds met",
    )
    add(
        "v4_assumption_hash_bound",
        all(
            row["comsol_v4_assumption_set_sha256"] == COMSOL_V4_ASSUMPTION_SET_SHA256
            for table in (objectives, summaries)
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
        "dimension_objective_rows",
        "objective_summary_rows",
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
    objective = dimension_objective_rows()
    summaries = objective_summary_rows(objective)
    questions = question_rows(objective)
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
        "objective_function_id": OBJECTIVE_FUNCTION_ID,
        "objective_claim_level": OBJECTIVE_CLAIM_LEVEL,
        "summary": {
            "dimension_objective_rows": len(objective),
            "objective_summary_rows": len(summaries),
            "question_rows": len(questions),
            "comsol_rows_with_objective_width_above_candidate": sum(
                inum(row["objective_delta_vs_candidate_nm"]) > 0
                for row in objective
                if row["weighting_mode"] != "uniform_edge_mass"
            ),
            "comsol_rows_with_objective_width_equal_candidate": sum(
                inum(row["objective_delta_vs_candidate_nm"]) == 0
                for row in objective
                if row["weighting_mode"] != "uniform_edge_mass"
            ),
            "exact_pxu_probability_grid_available_now": False,
            "next_executable_block": "objective_width_annulus_response_summary_packet",
        },
        "dimension_objective_rows": objective,
        "objective_summary_rows": summaries,
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
    objective_rows = sorted(
        payload["dimension_objective_rows"],
        key=lambda row: (row["source_route_id_nodi"], row["weighting_mode"]),
    )
    summary_rows = sorted(payload["objective_summary_rows"], key=lambda row: row["source_route_id_nodi"])
    lines = [
        "# NODI sidewall dimension objective packet",
        "",
        "## Mainline",
        "",
        (
            "This artifact converts the monotonic 611 response surface into an "
            "assumption-driven top-width envelope. The objective is the smallest "
            "tested width retaining at least 95% of both peak and local-SNR response."
        ),
        "",
        "## Counts",
        "",
        f"- dimension objective rows: {summary['dimension_objective_rows']}",
        f"- objective summary rows: {summary['objective_summary_rows']}",
        f"- COMSOL rows wider than candidate: {summary['comsol_rows_with_objective_width_above_candidate']}",
        f"- COMSOL rows equal to candidate: {summary['comsol_rows_with_objective_width_equal_candidate']}",
        f"- failed validation rows: {summary['failed_validation_rows']}",
        "",
        "## Objective Rows",
        "",
        (
            "| source route | weighting mode | candidate W_top nm | objective W_top nm | "
            "max tested W_top nm | peak retention | SNR retention | annulus context |"
        ),
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in objective_rows:
        lines.append(
            "| {source} | {mode} | {candidate} | {objective} | {maxw} | {peak:.3f} | {snr:.3f} | {annulus} |".format(
                source=row["source_route_id_nodi"],
                mode=row["weighting_mode"],
                candidate=row["candidate_envelope_W_top_nm"],
                objective=row["objective_W_top_nm"],
                maxw=row["max_tested_W_top_nm"],
                peak=fnum(row["peak_retention_at_objective"]),
                snr=fnum(row["snr_retention_at_objective"]),
                annulus=row["annulus_policy_context_611"],
            )
        )
    lines.extend(
        [
            "",
            "## Route Summaries",
            "",
            (
                "| source route | COMSOL objective widths nm | delta vs candidate nm | "
                "annulus contexts |"
            ),
            "| --- | --- | --- | --- |",
        ]
    )
    for row in summary_rows:
        lines.append(
            "| {source} | {widths} | {dmin} to {dmax} | {contexts} |".format(
                source=row["source_route_id_nodi"],
                widths=row["comsol_weighted_objective_widths_json"],
                dmin=row["comsol_weighted_delta_vs_candidate_min_nm"],
                dmax=row["comsol_weighted_delta_vs_candidate_max_nm"],
                contexts=row["comsol_annulus_contexts_json"],
            )
        )
    lines.extend(
        [
            "",
            "## Main Answer",
            "",
            (
                "Under this explicit simulation objective, sidewall geometry changes the "
                "dimension envelope upward for most COMSOL-weighted rows while retaining "
                "current candidate width where it already meets the response-retention "
                "threshold. This is an assumption-bound size envelope, not a route winner, "
                "yield, or detection probability claim."
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
    objective_path = OUTPUT_DIR / f"{PREFIX}_DIMENSION_OBJECTIVE_ROWS_{DATE_STAMP}.csv"
    summary_path = OUTPUT_DIR / f"{PREFIX}_OBJECTIVE_SUMMARY_ROWS_{DATE_STAMP}.csv"
    question_path = OUTPUT_DIR / f"{PREFIX}_QUESTION_ROWS_{DATE_STAMP}.csv"
    validation_path = OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv"
    source_lock_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv"
    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv"
    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv"
    report_md_path = REPORT_DIR / f"612_{PREFIX}_{DATE_STAMP}.md"

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
            "objective_function_id",
            "objective_claim_level",
            "summary",
            "payload_sha256",
        )
    }
    write_json_atomic(status_path, status_payload, sort_keys=True)
    write_json_atomic(report_json_path, payload, sort_keys=True)
    write_csv_rows(objective_path, payload["dimension_objective_rows"])
    write_csv_rows(summary_path, payload["objective_summary_rows"])
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
        objective_path,
        summary_path,
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
    if not args.confirm_sidewall_dimension_objective_packet:
        print("--confirm-sidewall-dimension-objective-packet is required", file=sys.stderr)
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
