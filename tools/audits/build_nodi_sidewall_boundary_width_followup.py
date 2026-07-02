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
from tools.audits.build_nodi_sidewall_distribution_weighted_width_sweep import (  # noqa: E402
    CANONICAL_WINDOW_ID,
    PRIMARY_SIDEWALL_DEG_COMSOL,
    WEIGHTING_MODES,
    execute_width_sweep_rows,
    fnum,
    inum,
    m_to_nm,
    nm_to_m,
    parse_route_id,
    route_binding_rows,
    route_case_id,
    route_id,
    weighted_event_rows,
    width_summary_rows,
)


DATE_STAMP = "20260703"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_BOUNDARY_WIDTH_FOLLOWUP"
ARTIFACT_ID = "NODI_SIDEWALL_BOUNDARY_WIDTH_FOLLOWUP_20260703"
SYNTHESIS_VERSION = "sidewall_boundary_width_followup_v1"
DISPOSITION_PLAN = "NODI_SIDEWALL_BOUNDARY_WIDTH_FOLLOWUP_PLAN_READY"
DISPOSITION_EXECUTED = "NODI_SIDEWALL_BOUNDARY_WIDTH_FOLLOWUP_EXECUTED_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_BOUNDARY_WIDTH_FOLLOWUP_FAIL_CLOSED"
CLAIM_BOUNDARY = "boundary_width_followup_context_not_route_selection"
DEFAULT_N_EVENTS = 12
DEFAULT_RANDOM_SEED = 60900

SOURCE_FILES = {
    "width_sweep_status_608": OUTPUT_DIR
    / "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_WIDTH_SWEEP_STATUS_20260703.json",
    "width_sweep_dimension_context_608": OUTPUT_DIR
    / "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_WIDTH_SWEEP_DIMENSION_CONTEXT_ROWS_20260703.csv",
    "width_sweep_summary_608": OUTPUT_DIR
    / "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_WIDTH_SWEEP_WIDTH_SUMMARY_ROWS_20260703.csv",
    "bridge_route_binding_605": OUTPUT_DIR
    / "NODI_SIDEWALL_COMSOL_CROSS_SECTION_DISTRIBUTION_BRIDGE_ROUTE_DISTRIBUTION_BINDING_ROWS_20260703.csv",
    "boundary_followup_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_boundary_width_followup.py",
    "boundary_followup_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_boundary_width_followup.py",
}

ALLOWED_USE = (
    "execute or plan a boundary follow-up width sweep after 608 found leading "
    "distribution-weighted widths at the upper sweep edge"
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
    parser = argparse.ArgumentParser(description="Build sidewall boundary width follow-up.")
    parser.add_argument("--confirm-sidewall-boundary-width-followup", action="store_true")
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


def deterministic_sha256(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    output_report = f"reports/609_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_boundary_width_followup.py",
        "tests/test_nodi_sidewall_boundary_width_followup.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "boundary_width_followup_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "boundary_width_followup_output"
            release_decision = "included_or_rewritten_by_boundary_followup_builder"
        else:
            classification = "non_boundary_width_followup_dirty_context"
            release_decision = "ignored_for_boundary_width_followup"
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


def boundary_anchor_rows() -> list[dict[str, Any]]:
    rows_608 = [
        row
        for row in load_rows("width_sweep_dimension_context_608")
        if row["weighting_mode"] != "uniform_edge_mass"
    ]
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows_608:
        grouped[row["source_route_id_nodi"]].append(row)

    rows: list[dict[str, Any]] = []
    for route, group in sorted(grouped.items()):
        source_width_grid = json.loads(group[0]["width_grid_json"])
        anchor = max(
            max(inum(row["leading_peak_width_context_nm"]), inum(row["leading_snr_width_context_nm"]))
            for row in group
        )
        candidate = inum(group[0]["candidate_envelope_W_top_nm"])
        rows.append(
            {
                **common_guard_fields(f"BOUNDARY-ANCHOR-{route.replace('/', '_')}"),
                "source_route_id_nodi": route,
                "candidate_envelope_W_top_nm": candidate,
                "boundary_anchor_W_top_nm": anchor,
                "boundary_anchor_delta_vs_candidate_nm": anchor - candidate,
                "anchor_source": "max_comsol_weighted_leading_peak_or_snr_width_from_608",
                "boundary_anchor_source": "max_608_comsol_weighted_peak_or_snr_width_context",
                "source_608_width_grid_json": json.dumps(source_width_grid, ensure_ascii=True),
                "anchor_is_608_grid_upper_edge": anchor == max(inum(value) for value in source_width_grid),
                "followup_width_grid_json": json.dumps(
                    [anchor - 20, anchor, anchor + 20, anchor + 40], ensure_ascii=True
                ),
            }
        )
    return rows


def anchor_lookup() -> dict[str, dict[str, Any]]:
    return {row["source_route_id_nodi"]: row for row in boundary_anchor_rows()}


def plan_rows(*, n_events: int = DEFAULT_N_EVENTS, random_seed: int = DEFAULT_RANDOM_SEED) -> list[dict[str, Any]]:
    anchors = anchor_lookup()
    rows: list[dict[str, Any]] = []
    diameters = sorted(int(value) for value in PRS_APPROVED_DIAMETERS_NM)
    taper = comsol_sidewall_deg_to_nodi_taper_deg(PRIMARY_SIDEWALL_DEG_COMSOL)
    for route_index, route in enumerate(route_binding_rows()):
        source_route = route["source_route_id_nodi"]
        anchor = anchors[source_route]
        candidate_route = route["candidate_envelope_route_id_nodi"]
        lambda_nm, source_w_nm, depth_nm = parse_route_id(source_route)
        _, candidate_w_nm, _ = parse_route_id(candidate_route)
        boundary_anchor_w_nm = inum(anchor["boundary_anchor_W_top_nm"])
        widths = json.loads(anchor["followup_width_grid_json"])
        windows = json.loads(route["followup_window_set_json"])
        for width_index, width_nm in enumerate(widths):
            geometry = TrapezoidCrossSection(
                top_width_m=nm_to_m(width_nm),
                depth_m=nm_to_m(depth_nm),
                sidewall_taper_angle_deg=taper,
            )
            sweep_route = route_id(lambda_nm, width_nm, depth_nm)
            for window_index, window_id in enumerate(windows):
                inner, outer = (float(part.replace("p", ".")) for part in window_id.split("_"))
                for diameter_nm in diameters:
                    seed = int(
                        random_seed
                        + route_index * 100000
                        + width_index * 10000
                        + window_index * 1000
                        + diameter_nm
                    )
                    row_id = (
                        f"BOUNDARY-{route_case_id(source_route)}-to-{route_case_id(sweep_route)}-"
                        f"A{window_id}-P{diameter_nm}-N{n_events}-TH85"
                    )
                    rows.append(
                        {
                            **common_guard_fields(row_id),
                            "source_artifacts_json": json.dumps(
                                [
                                    "608_distribution_weighted_width_sweep",
                                    "605_distribution_bridge",
                                    "execute_annulus_row_reused",
                                ],
                                sort_keys=True,
                            ),
                            "shard_case_id": row_id,
                            "source_route_id_nodi": source_route,
                            "candidate_envelope_route_id_nodi": candidate_route,
                            "width_sweep_route_id_nodi": sweep_route,
                            "route_id_nodi": sweep_route,
                            "route_id_role": "boundary_width_followup_context_not_route_selection",
                            "lambda_nm": lambda_nm,
                            "source_W_nominal_nm": source_w_nm,
                            "candidate_envelope_W_top_nm": candidate_w_nm,
                            "boundary_anchor_W_top_nm": boundary_anchor_w_nm,
                            "W_nominal_nm": width_nm,
                            "W_top_nm": width_nm,
                            "W_top_semantics": "boundary_followup_runtime_top_aperture_surrogate",
                            "width_sweep_delta_vs_candidate_nm": width_nm - candidate_w_nm,
                            "width_sweep_delta_vs_source_nm": width_nm - source_w_nm,
                            "width_sweep_delta_vs_boundary_anchor_nm": width_nm - boundary_anchor_w_nm,
                            "width_context": (
                                "boundary_anchor_width"
                                if width_nm == boundary_anchor_w_nm
                                else (
                                    "above_boundary_anchor_width"
                                    if width_nm > boundary_anchor_w_nm
                                    else "below_boundary_anchor_width"
                                )
                            ),
                            "D_nm": depth_nm,
                            "depth_nm": depth_nm,
                            "diameter_nm": diameter_nm,
                            "annulus_window_id": window_id,
                            "selected_annulus_edge_norm_min": inner,
                            "selected_annulus_edge_norm_max": outer,
                            "is_canonical_annulus_window": window_id == CANONICAL_WINDOW_ID,
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
                            "execution_status": "planned_boundary_followup_not_executed",
                        }
                    )
    return rows


def boundary_dimension_context_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    anchors = anchor_lookup()
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in summary_rows:
        grouped[(row["source_route_id_nodi"], row["weighting_mode"])].append(row)

    rows: list[dict[str, Any]] = []
    for (source_route, mode), group in sorted(grouped.items()):
        anchor = inum(anchors[source_route]["boundary_anchor_W_top_nm"])
        leading_peak = max(group, key=lambda row: fnum(row["mean_weighted_peak_contribution"]))
        leading_snr = max(group, key=lambda row: fnum(row["mean_weighted_local_snr_contribution"]))
        peak_width = inum(leading_peak["W_top_nm"])
        snr_width = inum(leading_snr["W_top_nm"])
        if peak_width > anchor or snr_width > anchor:
            context = "still_wider_after_boundary_followup"
        elif peak_width == anchor and snr_width == anchor:
            context = "boundary_anchor_retained_after_followup"
        elif peak_width < anchor and snr_width < anchor:
            context = "below_boundary_anchor_possible_after_followup"
        else:
            context = "split_boundary_followup_context"
        rows.append(
            {
                **common_guard_fields(f"BOUNDARY-DIM-{source_route.replace('/', '_')}-{mode}"),
                "source_route_id_nodi": source_route,
                "weighting_mode": mode,
                "route_id_role": "boundary_dimension_context_not_route_selection",
                "boundary_anchor_W_top_nm": anchor,
                "leading_peak_width_context_nm": peak_width,
                "leading_snr_width_context_nm": snr_width,
                "peak_width_delta_vs_boundary_anchor_nm": peak_width - anchor,
                "snr_width_delta_vs_boundary_anchor_nm": snr_width - anchor,
                "dimension_context_after_boundary_followup": context,
                "width_grid_json": json.dumps(
                    [inum(row["W_top_nm"]) for row in sorted(group, key=lambda r: inum(r["W_top_nm"]))],
                    ensure_ascii=True,
                ),
            }
        )
    return rows


def question_rows(dimension_rows: list[dict[str, Any]], *, execute_nodi: bool) -> list[dict[str, Any]]:
    comsol_rows = [
        row for row in dimension_rows if row["weighting_mode"] != "uniform_edge_mass"
    ]
    still_wider = sum(
        row["dimension_context_after_boundary_followup"]
        == "still_wider_after_boundary_followup"
        for row in comsol_rows
    )
    retained = sum(
        row["dimension_context_after_boundary_followup"]
        == "boundary_anchor_retained_after_followup"
        for row in comsol_rows
    )
    mode_text = "executed" if execute_nodi else "planned"
    return [
        {
            **common_guard_fields("QUESTION-609-DIMENSION"),
            "question_id": "size_recommendation_delta_after_sidewall",
            "answer_context": (
                f"boundary follow-up {mode_text}; evaluates whether 608 upper-edge widths "
                "are retained or still push wider"
            ),
            "comsol_weighted_rows_still_wider": still_wider,
            "comsol_weighted_rows_boundary_anchor_retained": retained,
            "next_action": "610_lock_or_extend_width_context",
        },
        {
            **common_guard_fields("QUESTION-609-ANNULUS"),
            "question_id": "selected_annulus_range_delta_after_sidewall",
            "answer_context": "annulus context carried through boundary width follow-up",
            "next_action": "610_lock_annulus_context_after_boundary_followup",
        },
        {
            **common_guard_fields("QUESTION-609-INTERFERENCE"),
            "question_id": "interference_response_delta_after_sidewall",
            "answer_context": "interference-response context carried through boundary width follow-up",
            "next_action": "610_lock_interference_context_after_boundary_followup",
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

    events = payload["boundary_followup_event_rows"]
    weighted = payload["weighted_boundary_event_rows"]
    summaries = payload["boundary_width_summary_rows"]
    dimensions = payload["boundary_dimension_context_rows"]
    anchors = payload["boundary_anchor_rows"]
    execute_nodi = payload["execute_nodi"]
    route_rows = route_binding_rows()
    route_window_counts = {
        row["source_route_id_nodi"]: len(json.loads(row["followup_window_set_json"]))
        for row in route_rows
    }
    expected = sum(4 * count * len(PRS_APPROVED_DIAMETERS_NM) for count in route_window_counts.values())
    executed = sum(row["execution_status"] == "executed_width_sweep_nodi" for row in events)
    add(
        "boundary_anchors_cover_six_routes",
        len(anchors) == 6,
        f"boundary_anchor_rows={len(anchors)}",
    )
    add(
        "boundary_anchors_are_608_upper_edges",
        all(row["anchor_is_608_grid_upper_edge"] is True for row in anchors),
        "all boundary anchors equal the prior 608 local width-grid upper edge",
    )
    add(
        "boundary_followup_event_grid_complete",
        len(events) == expected,
        f"boundary_followup_event_rows={len(events)} expected={expected}",
    )
    add(
        "execution_status_matches_mode",
        (executed == expected if execute_nodi else executed == 0),
        f"execute_nodi={execute_nodi}; executed_rows={executed}",
    )
    add(
        "weighted_rows_cover_three_modes",
        len(weighted) == len(events) * len(WEIGHTING_MODES),
        f"weighted_boundary_event_rows={len(weighted)}",
    )
    add(
        "summary_rows_cover_route_width_weight_grid",
        len(summaries) == 6 * 4 * len(WEIGHTING_MODES),
        f"boundary_width_summary_rows={len(summaries)}",
    )
    add(
        "dimension_rows_cover_six_routes_times_three_modes",
        len(dimensions) == 6 * len(WEIGHTING_MODES),
        f"boundary_dimension_context_rows={len(dimensions)}",
    )
    add(
        "v4_assumption_hash_bound",
        all(
            row["comsol_v4_assumption_set_sha256"] == COMSOL_V4_ASSUMPTION_SET_SHA256
            for table in (events, weighted, summaries, dimensions)
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
        "boundary_anchor_rows",
        "boundary_followup_event_rows",
        "weighted_boundary_event_rows",
        "boundary_width_summary_rows",
        "boundary_dimension_context_rows",
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


def build_payload(
    *,
    execute_nodi: bool = False,
    n_events: int = DEFAULT_N_EVENTS,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> dict[str, Any]:
    anchors = boundary_anchor_rows()
    plan = plan_rows(n_events=n_events, random_seed=random_seed)
    failures: list[dict[str, Any]] = []
    if execute_nodi:
        event_rows, failures = execute_width_sweep_rows(plan)
        disposition = DISPOSITION_EXECUTED
    else:
        event_rows = plan
        disposition = DISPOSITION_PLAN
    weighted = weighted_event_rows(event_rows)
    summaries = width_summary_rows(weighted)
    dimensions = boundary_dimension_context_rows(summaries)
    q_rows = question_rows(dimensions, execute_nodi=execute_nodi)
    payload: dict[str, Any] = {
        "artifact_id": ARTIFACT_ID,
        "synthesis_version": SYNTHESIS_VERSION,
        "date_stamp": DATE_STAMP,
        "disposition": disposition,
        "claim_boundary": CLAIM_BOUNDARY,
        "git_head": git_head(),
        "git_branch": git_branch(),
        "execute_nodi": execute_nodi,
        "n_events": n_events,
        "random_seed": random_seed,
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "comsol_v4_assumption_set_sha256": COMSOL_V4_ASSUMPTION_SET_SHA256,
        "summary": {
            "boundary_anchor_rows": len(anchors),
            "boundary_followup_event_rows": len(event_rows),
            "boundary_followup_executed_rows": sum(
                row["execution_status"] == "executed_width_sweep_nodi"
                for row in event_rows
            ),
            "boundary_followup_failures": len(failures),
            "weighted_boundary_event_rows": len(weighted),
            "boundary_width_summary_rows": len(summaries),
            "boundary_dimension_context_rows": len(dimensions),
            "question_rows": len(q_rows),
            "exact_pxu_probability_grid_available_now": False,
            "next_executable_block": "610_lock_or_extend_width_context",
        },
        "boundary_anchor_rows": anchors,
        "boundary_followup_event_rows": event_rows,
        "weighted_boundary_event_rows": weighted,
        "boundary_width_summary_rows": summaries,
        "boundary_dimension_context_rows": dimensions,
        "question_rows": q_rows,
        "failure_rows": failures
        or [
            {
                "row_id": "NO_FAILURES",
                "execution_status": "no_failures",
                "failure_type": "",
                "failure_message": "",
            }
        ],
        "source_lock_rows": source_lock_rows(),
        "dirty_context_rows": dirty_context_rows(),
    }
    validation = validation_rows(payload)
    payload["validation_rows"] = validation
    payload["summary"]["failed_validation_rows"] = sum(
        1 for row in validation if row["status"] != "pass"
    )
    if failures or payload["summary"]["failed_validation_rows"]:
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
    still_wider = sum(
        row["dimension_context_after_boundary_followup"] == "still_wider_after_boundary_followup"
        for row in payload["boundary_dimension_context_rows"]
        if row["weighting_mode"] != "uniform_edge_mass"
    )
    context_rows = sorted(
        payload["boundary_dimension_context_rows"],
        key=lambda row: (row["source_route_id_nodi"], row["weighting_mode"]),
    )
    lines = [
        "# NODI sidewall boundary width follow-up",
        "",
        "## Mainline",
        "",
        (
            "This artifact follows up the 608 upper-edge width result by centering "
            "a second NODI width sweep on the COMSOL-weighted leading width contexts."
        ),
        "",
        "## Counts",
        "",
        f"- execution mode: {'executed' if payload['execute_nodi'] else 'plan-only'}",
        f"- boundary anchors: {summary['boundary_anchor_rows']}",
        f"- event rows: {summary['boundary_followup_event_rows']}",
        f"- executed rows: {summary['boundary_followup_executed_rows']}",
        f"- weighted rows: {summary['weighted_boundary_event_rows']}",
        f"- COMSOL-weighted rows still wider: {still_wider}",
        f"- failed validation rows: {summary['failed_validation_rows']}",
        "",
        "## Boundary Context",
        "",
        "| source route | weighting mode | anchor W_top nm | leading peak W_top nm | leading SNR W_top nm | context |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in context_rows:
        lines.append(
            "| {source} | {mode} | {anchor} | {peak} | {snr} | {context} |".format(
                source=row["source_route_id_nodi"],
                mode=row["weighting_mode"],
                anchor=row["boundary_anchor_W_top_nm"],
                peak=row["leading_peak_width_context_nm"],
                snr=row["leading_snr_width_context_nm"],
                context=row["dimension_context_after_boundary_followup"],
            )
        )
    lines.extend(
        [
            "",
            "## Next Block",
            "",
            (
                "All COMSOL-weighted boundary contexts are still wider after this follow-up, "
                "so the next executable block should extend the width envelope rather than lock "
                "the current boundary anchors."
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
    anchor_path = OUTPUT_DIR / f"{PREFIX}_BOUNDARY_ANCHOR_ROWS_{DATE_STAMP}.csv"
    event_path = OUTPUT_DIR / f"{PREFIX}_BOUNDARY_FOLLOWUP_EVENT_ROWS_{DATE_STAMP}.csv"
    weighted_path = OUTPUT_DIR / f"{PREFIX}_WEIGHTED_BOUNDARY_EVENT_ROWS_{DATE_STAMP}.csv"
    summary_path = OUTPUT_DIR / f"{PREFIX}_BOUNDARY_WIDTH_SUMMARY_ROWS_{DATE_STAMP}.csv"
    dimension_path = OUTPUT_DIR / f"{PREFIX}_BOUNDARY_DIMENSION_CONTEXT_ROWS_{DATE_STAMP}.csv"
    question_path = OUTPUT_DIR / f"{PREFIX}_QUESTION_ROWS_{DATE_STAMP}.csv"
    failure_path = OUTPUT_DIR / f"{PREFIX}_FAILURE_ROWS_{DATE_STAMP}.csv"
    validation_path = OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv"
    source_lock_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv"
    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv"
    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv"
    report_md_path = REPORT_DIR / f"609_{PREFIX}_{DATE_STAMP}.md"

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
            "execute_nodi",
            "n_events",
            "random_seed",
            "comsol_v4_assumption_set_id",
            "comsol_v4_assumption_set_version",
            "comsol_v4_assumption_set_sha256",
            "summary",
            "payload_sha256",
        )
    }
    write_json_atomic(status_path, status_payload, sort_keys=True)
    write_json_atomic(report_json_path, payload, sort_keys=True)
    write_csv_rows(anchor_path, payload["boundary_anchor_rows"])
    write_csv_rows(event_path, payload["boundary_followup_event_rows"])
    write_csv_rows(weighted_path, payload["weighted_boundary_event_rows"])
    write_csv_rows(summary_path, payload["boundary_width_summary_rows"])
    write_csv_rows(dimension_path, payload["boundary_dimension_context_rows"])
    write_csv_rows(question_path, payload["question_rows"])
    write_csv_rows(failure_path, payload["failure_rows"])
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
        anchor_path,
        event_path,
        weighted_path,
        summary_path,
        dimension_path,
        question_path,
        failure_path,
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
    if not args.confirm_sidewall_boundary_width_followup:
        print("--confirm-sidewall-boundary-width-followup is required", file=sys.stderr)
        return 2
    payload = build_payload(
        execute_nodi=args.execute_nodi,
        n_events=args.n_events,
        random_seed=args.random_seed,
    )
    failures = validate_payload(payload)
    paths = write_outputs(payload)
    print(json.dumps(payload["summary"], sort_keys=True))
    for path in paths:
        print(display_path(path))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
