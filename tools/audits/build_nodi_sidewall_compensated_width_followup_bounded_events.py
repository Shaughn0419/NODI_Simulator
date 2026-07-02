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

from nodi_simulator.cross_section_geometry import (  # noqa: E402
    TrapezoidCrossSection,
    comsol_sidewall_deg_to_nodi_taper_deg,
)
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
from tools.audits.build_nodi_sidewall_bounded_event_shards import (  # noqa: E402
    execute_shard_row,
    m_to_nm,
    nm_to_m,
)


DATE_STAMP = "20260702"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_COMPENSATED_WIDTH_FOLLOWUP_BOUNDED_EVENTS"
ARTIFACT_ID = "NODI_SIDEWALL_COMPENSATED_WIDTH_FOLLOWUP_BOUNDED_EVENTS_20260702"
FOLLOWUP_VERSION = "sidewall_compensated_width_followup_bounded_events_v1"
DISPOSITION_EXECUTED = "NODI_SIDEWALL_COMPENSATED_WIDTH_FOLLOWUP_BOUNDED_EVENTS_EXECUTED_READY"
DISPOSITION_PLAN = "NODI_SIDEWALL_COMPENSATED_WIDTH_FOLLOWUP_BOUNDED_EVENTS_PLAN_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_COMPENSATED_WIDTH_FOLLOWUP_BOUNDED_EVENTS_FAIL_CLOSED"
CLAIM_BOUNDARY = "sidewall_compensated_width_followup_context_not_selection"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
PRIMARY_SIDEWALL_DEG_COMSOL = 85.0
DEFAULT_N_EVENTS = 2
DEFAULT_RANDOM_SEED = 59700
FOLLOWUP_DIMENSION_BANDS = {
    "geometry_respecification_context",
    "dimension_update_required_context",
}

SOURCE_FILES = {
    "integrated_status_596": OUTPUT_DIR
    / "NODI_SIDEWALL_FULL_EVENT_INTEGRATED_UPDATE_PACKET_STATUS_20260702.json",
    "integrated_rows_596": OUTPUT_DIR
    / "NODI_SIDEWALL_FULL_EVENT_INTEGRATED_UPDATE_PACKET_INTEGRATED_ROUTE_DIAMETER_ROWS_20260702.csv",
    "primary85_event_rows_595": OUTPUT_DIR
    / "NODI_SIDEWALL_PRIMARY85_FULL_BOUNDED_EVENT_EXPANSION_EVENT_ROWS_20260702.csv",
    "bounded_event_runner_591": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_bounded_event_shards.py",
    "compensated_width_followup_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_compensated_width_followup_bounded_events.py",
    "compensated_width_followup_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_compensated_width_followup_bounded_events.py",
}

ALLOWED_USE = (
    "run sparse NODI bounded-event context for compensated 85deg top-width "
    "candidates derived from sidewall dimension update rows"
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
        description="Build/execute compensated-width sidewall follow-up bounded events."
    )
    parser.add_argument(
        "--confirm-sidewall-compensated-width-followup-bounded-events",
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


def route_id(lambda_nm: int, width_nm: int, depth_nm: int) -> str:
    return f"{int(lambda_nm)}/W{int(width_nm)}/D{int(depth_nm)}"


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
    output_report = f"reports/597_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_compensated_width_followup_bounded_events.py",
        "tests/test_nodi_sidewall_compensated_width_followup_bounded_events.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "compensated_width_followup_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "compensated_width_followup_output"
            release_decision = "included_or_rewritten_by_compensated_width_followup_builder"
        else:
            classification = "non_compensated_width_followup_dirty_context"
            release_decision = "ignored_for_compensated_width_followup"
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
        "followup_version": FOLLOWUP_VERSION,
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


def original_sidewall85_index() -> dict[tuple[str, int], dict[str, str]]:
    rows = [
        row
        for row in load_rows("primary85_event_rows_595")
        if math.isclose(fnum(row.get("sidewall_deg_comsol")), PRIMARY_SIDEWALL_DEG_COMSOL)
    ]
    return {(row.get("route_id_nodi", ""), inum(row.get("diameter_nm"))): row for row in rows}


def followup_source_rows() -> list[dict[str, str]]:
    return [
        row
        for row in load_rows("integrated_rows_596")
        if row.get("dimension_context_band") in FOLLOWUP_DIMENSION_BANDS
    ]


def candidate_width_nm(row: dict[str, str]) -> int:
    return int(math.ceil(fnum(row.get("W_top_compensated_proxy_nm"))))


def plan_rows(
    *,
    n_events: int = DEFAULT_N_EVENTS,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, source in enumerate(followup_source_rows(), start=1):
        lambda_nm = inum(source.get("lambda_nm"))
        width_nm = candidate_width_nm(source)
        source_width_nm = inum(source.get("W_nominal_nm"))
        depth_nm = inum(source.get("D_nm"))
        diameter_nm = inum(source.get("diameter_nm"))
        source_route = source.get("route_id_nodi", "")
        candidate_route = route_id(lambda_nm, width_nm, depth_nm)
        theta = PRIMARY_SIDEWALL_DEG_COMSOL
        taper = comsol_sidewall_deg_to_nodi_taper_deg(theta)
        geometry = TrapezoidCrossSection(
            top_width_m=nm_to_m(width_nm),
            depth_m=nm_to_m(depth_nm),
            sidewall_taper_angle_deg=taper,
        )
        seed = int(random_seed + index * 17 + diameter_nm)
        row_id = (
            f"CW-{route_case_id(source_route)}-P{diameter_nm}-"
            f"W{source_width_nm}_to_W{width_nm}-TH85"
        )
        rows.append(
            {
                **common_guard_fields(row_id),
                "source_artifacts_json": json.dumps(
                    [
                        "596_NODI_SIDEWALL_FULL_EVENT_INTEGRATED_UPDATE_PACKET_20260702",
                        "595_NODI_SIDEWALL_PRIMARY85_FULL_BOUNDED_EVENT_EXPANSION_20260702",
                        "run_single_case_batch",
                    ],
                    sort_keys=True,
                ),
                "shard_case_id": row_id,
                "source_route_id_nodi": source_route,
                "source_route_id_role": "join_key_only_not_selection",
                "route_id_nodi": candidate_route,
                "route_id_nodi_role": "candidate_dimension_context_not_selection",
                "lambda_nm": lambda_nm,
                "source_W_nominal_nm": source_width_nm,
                "W_nominal_nm": width_nm,
                "W_top_nm": width_nm,
                "W_top_semantics": "compensated_runtime_top_aperture_surrogate",
                "candidate_width_rounding_policy": "ceil_W_top_compensated_proxy_nm_to_integer_nm",
                "candidate_top_width_delta_nm": width_nm - source_width_nm,
                "D_nm": depth_nm,
                "depth_nm": depth_nm,
                "diameter_nm": diameter_nm,
                "source_dimension_context_band": source.get("dimension_context_band", ""),
                "source_dimension_update_action_594": source.get(
                    "dimension_update_action_594", ""
                ),
                "source_W_top_compensated_proxy_nm": fnum(
                    source.get("W_top_compensated_proxy_nm")
                ),
                "source_mean_peak_height_delta_85_vs_90": fnum(
                    source.get("mean_peak_height_delta")
                ),
                "source_selected_annulus_fraction_delta_85_vs_90": fnum(
                    source.get("selected_annulus_fraction_delta")
                ),
                "particle_model": "gold_baseline_material_model",
                "channel_cross_section_model": "trapezoid_tapered_sidewalls",
                "sidewall_angle_convention": "comsol_from_horizontal",
                "sidewall_deg_comsol": theta,
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
    return rows


def event_rows(*, execute_nodi: bool, n_events: int, random_seed: int) -> list[dict[str, Any]]:
    rows = plan_rows(n_events=n_events, random_seed=random_seed)
    if not execute_nodi:
        return rows
    executed_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        print(f"[compensated-width] {index}/{len(rows)} {row['shard_case_id']}", flush=True)
        executed_rows.append(execute_shard_row(row))
    return executed_rows


def delta_value(candidate: dict[str, Any], original: dict[str, Any], field: str) -> float | str:
    if field not in candidate or field not in original:
        return ""
    left = fnum(original.get(field), default=math.nan)
    right = fnum(candidate.get(field), default=math.nan)
    if not (math.isfinite(left) and math.isfinite(right)):
        return ""
    return right - left


def candidate_recovery_context(delta: dict[str, Any]) -> str:
    ann_delta = fnum(delta.get("candidate_minus_original_selected_annulus_fraction_delta"))
    peak_delta = fnum(delta.get("candidate_minus_original_mean_peak_height_delta"))
    if ann_delta > 0 and peak_delta > 0:
        return "annulus_and_response_improved_context"
    if ann_delta > 0:
        return "annulus_context_improved_response_not_improved"
    if peak_delta > 0:
        return "response_context_improved_annulus_not_improved"
    if ann_delta == 0 and peak_delta == 0:
        return "no_sparse_event_context_change"
    return "candidate_context_not_improved_in_sparse_events"


def candidate_delta_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    original = original_sidewall85_index()
    deltas: list[dict[str, Any]] = []
    for row in rows:
        key = (row["source_route_id_nodi"], int(row["diameter_nm"]))
        original_row = original.get(key, {})
        row_id = f"CW-DELTA-{route_case_id(row['source_route_id_nodi'])}-P{row['diameter_nm']}-TH85"
        delta = {
            **common_guard_fields(row_id),
            "delta_case_id": row_id,
            "source_route_id_nodi": row["source_route_id_nodi"],
            "candidate_route_id_nodi": row["route_id_nodi"],
            "route_id_role": "candidate_join_key_only_not_selection",
            "diameter_nm": int(row["diameter_nm"]),
            "source_W_nominal_nm": int(row["source_W_nominal_nm"]),
            "candidate_W_top_nm": int(row["W_top_nm"]),
            "candidate_top_width_delta_nm": int(row["candidate_top_width_delta_nm"]),
            "sidewall_deg_comsol": PRIMARY_SIDEWALL_DEG_COMSOL,
            "original_execution_status": original_row.get("execution_status", ""),
            "candidate_execution_status": row.get("execution_status", ""),
            "original_selected_annulus_fraction": fnum(
                original_row.get("selected_annulus_fraction")
            ),
            "candidate_selected_annulus_fraction": fnum(
                row.get("selected_annulus_fraction")
            ),
            "candidate_minus_original_selected_annulus_fraction_delta": delta_value(
                row, original_row, "selected_annulus_fraction"
            ),
            "original_mean_peak_height": fnum(original_row.get("mean_peak_height")),
            "candidate_mean_peak_height": fnum(row.get("mean_peak_height")),
            "candidate_minus_original_mean_peak_height_delta": delta_value(
                row, original_row, "mean_peak_height"
            ),
            "candidate_minus_original_mean_local_snr_delta": delta_value(
                row, original_row, "mean_local_snr"
            ),
            "candidate_minus_original_synthetic_counting_context_rate_delta": delta_value(
                row, original_row, "synthetic_counting_context_rate"
            ),
            "delta_status": "executed_candidate_delta_context"
            if row.get("execution_status") == "executed_bounded_nodi_shard"
            and original_row.get("execution_status") == "executed_bounded_nodi_shard"
            else "planned_candidate_delta_context",
        }
        delta["candidate_recovery_context"] = candidate_recovery_context(delta)
        deltas.append(delta)
    return deltas


def route_envelope_rows(rows: list[dict[str, Any]], deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    delta_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["source_route_id_nodi"]].append(row)
    for delta in deltas:
        delta_grouped[delta["source_route_id_nodi"]].append(delta)
    output: list[dict[str, Any]] = []
    for source_route, group in sorted(grouped.items()):
        source_width = int(group[0]["source_W_nominal_nm"])
        depth_nm = int(group[0]["D_nm"])
        lambda_nm = int(group[0]["lambda_nm"])
        max_width = max(int(row["W_top_nm"]) for row in group)
        route_deltas = delta_grouped[source_route]
        annulus_improved = sum(
            fnum(delta["candidate_minus_original_selected_annulus_fraction_delta"]) > 0
            for delta in route_deltas
        )
        response_improved = sum(
            fnum(delta["candidate_minus_original_mean_peak_height_delta"]) > 0
            for delta in route_deltas
        )
        if annulus_improved and response_improved:
            state = "compensated_width_has_annulus_or_response_recovery_context"
        elif route_deltas and all(
            delta["delta_status"] == "executed_candidate_delta_context"
            for delta in route_deltas
        ):
            state = "compensated_width_executed_context_mixed_or_no_recovery"
        else:
            state = "compensated_width_plan_context"
        output.append(
            {
                **common_guard_fields(f"CW-ENVELOPE-{route_case_id(source_route)}"),
                "source_route_id_nodi": source_route,
                "candidate_envelope_route_id_nodi": route_id(lambda_nm, max_width, depth_nm),
                "route_id_role": "candidate_envelope_not_selection",
                "lambda_nm": lambda_nm,
                "source_W_nominal_nm": source_width,
                "D_nm": depth_nm,
                "candidate_route_diameter_rows": len(group),
                "candidate_envelope_W_top_nm": max_width,
                "candidate_envelope_top_width_delta_nm": max_width - source_width,
                "candidate_rows_with_annulus_improvement": annulus_improved,
                "candidate_rows_with_response_improvement": response_improved,
                "max_candidate_minus_original_selected_annulus_fraction_delta": max(
                    fnum(delta["candidate_minus_original_selected_annulus_fraction_delta"])
                    for delta in route_deltas
                )
                if route_deltas
                else "",
                "max_candidate_minus_original_mean_peak_height_delta": max(
                    fnum(delta["candidate_minus_original_mean_peak_height_delta"])
                    for delta in route_deltas
                )
                if route_deltas
                else "",
                "route_followup_context_state": state,
            }
        )
    return output


def answer_axis_rows(
    rows: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
    envelopes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            **common_guard_fields("CW-AXIS-DIMENSION-CANDIDATE"),
            "answer_axis": "recommended_dimension_followup_candidate",
            "answer": "compensated_width_candidates_generated_for_affected_rows",
            "evidence_rows": len(rows),
            "route_rows": len(envelopes),
            "affected_rows": len(rows),
            "mainline_interpretation": (
                "affected 85deg sidewall rows now have explicit compensated top-width "
                "candidates for sparse bounded-event follow-up"
            ),
        },
        {
            **common_guard_fields("CW-AXIS-ANNULUS-RECOVERY"),
            "answer_axis": "selected_annulus_followup_context",
            "answer": "compensated_width_candidates_change_selected_annulus_context",
            "evidence_rows": len(deltas),
            "route_rows": len(envelopes),
            "affected_rows": sum(
                fnum(delta["candidate_minus_original_selected_annulus_fraction_delta"])
                != 0
                for delta in deltas
            ),
            "mainline_interpretation": (
                "compensated width follow-up provides direct context for whether the "
                "0.5-0.8 selected-annulus event fraction recovers, worsens, or stays flat"
            ),
        },
        {
            **common_guard_fields("CW-AXIS-INTERFERENCE-RECOVERY"),
            "answer_axis": "interference_response_followup_context",
            "answer": "compensated_width_candidates_change_interference_response_context",
            "evidence_rows": len(deltas),
            "route_rows": len(envelopes),
            "affected_rows": sum(
                fnum(delta["candidate_minus_original_mean_peak_height_delta"]) != 0
                for delta in deltas
            ),
            "mainline_interpretation": (
                "candidate width changes are compared against original 85deg event "
                "context through peak-height and local-SNR deltas"
            ),
        },
    ]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    table_names = (
        "candidate_event_rows",
        "candidate_delta_rows",
        "route_envelope_rows",
        "answer_axis_rows",
    )
    columns: set[str] = set()
    for table_name in table_names:
        if payload[table_name]:
            columns |= set().union(*(set(row) for row in payload[table_name]))
    forbidden = sorted(columns & FORBIDDEN_PRIMARY_COLUMNS)
    if forbidden:
        failures.append(f"forbidden columns present: {forbidden}")
    if payload["summary"]["candidate_event_rows"] != 66:
        failures.append("candidate event rows must cover 596 affected dimension rows")
    if payload["summary"]["candidate_delta_rows"] != 66:
        failures.append("candidate delta rows must cover every candidate event row")
    if payload["summary"]["route_envelope_rows"] != 6:
        failures.append("route envelope rows must cover six source routes")
    if payload["summary"]["source_missing_rows"] != 0:
        failures.append("source artifacts missing")
    for table_name in table_names:
        for index, row in enumerate(payload[table_name], start=1):
            for field in (
                "not_detection_probability",
                "not_yield",
                "not_selection_metric_claim",
                "not_qch_weighted",
                "not_production_recommendation",
            ):
                if row.get(field) is not True:
                    failures.append(f"{table_name} row {index} {field} must be true")
    return failures


def validation_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    failures = validate_payload(payload)
    return [
        {
            "check_name": "candidate_event_coverage",
            "check_pass": payload["summary"]["candidate_event_rows"] == 66,
            "observed": payload["summary"]["candidate_event_rows"],
            "expected": 66,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "candidate_delta_coverage",
            "check_pass": payload["summary"]["candidate_delta_rows"] == 66,
            "observed": payload["summary"]["candidate_delta_rows"],
            "expected": 66,
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


def semantic_digest(payload: dict[str, Any]) -> str:
    return deterministic_sha256(
        {
            "candidate_event_rows": payload["candidate_event_rows"],
            "candidate_delta_rows": payload["candidate_delta_rows"],
            "route_envelope_rows": payload["route_envelope_rows"],
            "answer_axis_rows": payload["answer_axis_rows"],
        }
    )


def build_payload(*, execute_nodi: bool, n_events: int, random_seed: int) -> dict[str, Any]:
    rows = event_rows(
        execute_nodi=execute_nodi,
        n_events=n_events,
        random_seed=random_seed,
    )
    deltas = candidate_delta_rows(rows)
    envelopes = route_envelope_rows(rows, deltas)
    axes = answer_axis_rows(rows, deltas, envelopes)
    sources = source_lock_rows()
    dirty = dirty_context_rows()
    summary = {
        "artifact_id": ARTIFACT_ID,
        "disposition": DISPOSITION_EXECUTED if execute_nodi else DISPOSITION_PLAN,
        "followup_version": FOLLOWUP_VERSION,
        "branch": git_branch(),
        "current_head": git_head(),
        "execute_nodi": bool(execute_nodi),
        "n_events_requested_per_candidate": int(n_events),
        "candidate_event_rows": len(rows),
        "executed_candidate_event_rows": sum(
            row.get("execution_status") == "executed_bounded_nodi_shard"
            for row in rows
        ),
        "candidate_delta_rows": len(deltas),
        "executed_candidate_delta_rows": sum(
            row["delta_status"] == "executed_candidate_delta_context"
            for row in deltas
        ),
        "route_envelope_rows": len(envelopes),
        "answer_axis_rows": len(axes),
        "candidate_rows_with_annulus_improvement": sum(
            fnum(delta["candidate_minus_original_selected_annulus_fraction_delta"]) > 0
            for delta in deltas
        ),
        "candidate_rows_with_response_improvement": sum(
            fnum(delta["candidate_minus_original_mean_peak_height_delta"]) > 0
            for delta in deltas
        ),
        "max_candidate_minus_original_selected_annulus_fraction_delta": max(
            fnum(delta["candidate_minus_original_selected_annulus_fraction_delta"])
            for delta in deltas
        )
        if deltas
        else 0.0,
        "max_candidate_minus_original_mean_peak_height_delta": max(
            fnum(delta["candidate_minus_original_mean_peak_height_delta"])
            for delta in deltas
        )
        if deltas
        else 0.0,
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(1 for row in sources if row["exists"] == "false"),
        "dirty_context_rows": len(dirty),
        "non_compensated_width_followup_dirty_context_rows": sum(
            1
            for row in dirty
            if row["classification"] == "non_compensated_width_followup_dirty_context"
        ),
        "primary_answer_frame": "sidewall_compensated_dimension_followup_for_annulus_and_response",
        "not_primary_answer_frame": "route_winner_or_final_probability",
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    payload = {
        "summary": summary,
        "candidate_event_rows": rows,
        "candidate_delta_rows": deltas,
        "route_envelope_rows": envelopes,
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
        "candidate_events": OUTPUT_DIR / f"{PREFIX}_CANDIDATE_EVENT_ROWS_{DATE_STAMP}.csv",
        "candidate_deltas": OUTPUT_DIR / f"{PREFIX}_CANDIDATE_DELTA_ROWS_{DATE_STAMP}.csv",
        "route_envelopes": OUTPUT_DIR / f"{PREFIX}_ROUTE_ENVELOPE_ROWS_{DATE_STAMP}.csv",
        "answer_axis": OUTPUT_DIR / f"{PREFIX}_ANSWER_AXIS_ROWS_{DATE_STAMP}.csv",
        "validation": OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv",
        "failures": OUTPUT_DIR / f"{PREFIX}_FAILURES_{DATE_STAMP}.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv",
        "master_report": REPORT_DIR / f"597_{PREFIX}_{DATE_STAMP}.md",
    }
    write_json_atomic(outputs["status"], payload["summary"], sort_keys=True)
    write_csv_rows(outputs["candidate_events"], payload["candidate_event_rows"])
    write_csv_rows(outputs["candidate_deltas"], payload["candidate_delta_rows"])
    write_csv_rows(outputs["route_envelopes"], payload["route_envelope_rows"])
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
            "route_envelope_rows": payload["route_envelope_rows"],
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
            "# NODI Sidewall Compensated Width Follow-Up Bounded Events",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Execute NODI: `{s['execute_nodi']}`",
            f"Candidate event rows: `{s['candidate_event_rows']}`",
            f"Executed candidate event rows: `{s['executed_candidate_event_rows']}`",
            f"Candidate delta rows: `{s['candidate_delta_rows']}`",
            f"Route envelope rows: `{s['route_envelope_rows']}`",
            f"Failed validation rows: `{s['failed_validation_rows']}`",
            "",
            "This package tests compensated 85deg top-width candidates derived "
            "from the full-event integrated update packet. It remains sparse "
            "bounded-event context for dimension, selected-annulus, and response "
            "follow-up, not a route winner, probability, yield, or production "
            "recommendation.",
            "",
        ]
    )


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_sidewall_compensated_width_followup_bounded_events:
        print(
            "--confirm-sidewall-compensated-width-followup-bounded-events is required",
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
