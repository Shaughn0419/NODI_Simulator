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
    execute_shard_row,
    m_to_nm,
    nm_to_m,
)


DATE_STAMP = "20260702"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_CANDIDATE_ENVELOPE_HIGHER_EVENT_SWEEP"
ARTIFACT_ID = "NODI_SIDEWALL_CANDIDATE_ENVELOPE_HIGHER_EVENT_SWEEP_20260702"
SWEEP_VERSION = "sidewall_candidate_envelope_higher_event_sweep_v1"
DISPOSITION_EXECUTED = "NODI_SIDEWALL_CANDIDATE_ENVELOPE_HIGHER_EVENT_SWEEP_EXECUTED_READY"
DISPOSITION_PLAN = "NODI_SIDEWALL_CANDIDATE_ENVELOPE_HIGHER_EVENT_SWEEP_PLAN_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_CANDIDATE_ENVELOPE_HIGHER_EVENT_SWEEP_FAIL_CLOSED"
CLAIM_BOUNDARY = "candidate_envelope_higher_event_context_not_probability_not_selection"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
PRIMARY_SIDEWALL_DEG_COMSOL = 85.0
DEFAULT_N_EVENTS = 8
DEFAULT_RANDOM_SEED = 59900

SOURCE_FILES = {
    "recommendation_status_598": OUTPUT_DIR
    / "NODI_SIDEWALL_CANDIDATE_DIMENSION_RECOMMENDATION_SYNTHESIS_STATUS_20260702.json",
    "recommendation_route_rows_598": OUTPUT_DIR
    / "NODI_SIDEWALL_CANDIDATE_DIMENSION_RECOMMENDATION_SYNTHESIS_ROUTE_RECOMMENDATION_ROWS_20260702.csv",
    "primary85_event_rows_595": OUTPUT_DIR
    / "NODI_SIDEWALL_PRIMARY85_FULL_BOUNDED_EVENT_EXPANSION_EVENT_ROWS_20260702.csv",
    "bounded_event_runner_591": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_bounded_event_shards.py",
    "candidate_envelope_sweep_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_candidate_envelope_higher_event_sweep.py",
    "candidate_envelope_sweep_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_candidate_envelope_higher_event_sweep.py",
}

ALLOWED_USE = (
    "run higher-event sparse NODI context for sidewall-aware candidate envelope "
    "dimensions across PRS-approved particle diameters"
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
        description="Build/execute candidate envelope higher-event sweep."
    )
    parser.add_argument(
        "--confirm-sidewall-candidate-envelope-higher-event-sweep",
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


def parse_route_id(route: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"(\d+)/W(\d+)/D(\d+)", route)
    if not match:
        raise ValueError(f"invalid route id: {route}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


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
    output_report = f"reports/599_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_candidate_envelope_higher_event_sweep.py",
        "tests/test_nodi_sidewall_candidate_envelope_higher_event_sweep.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "candidate_envelope_sweep_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "candidate_envelope_sweep_output"
            release_decision = "included_or_rewritten_by_candidate_envelope_sweep_builder"
        else:
            classification = "non_candidate_envelope_sweep_dirty_context"
            release_decision = "ignored_for_candidate_envelope_sweep"
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


def original_sidewall85_index() -> dict[tuple[str, int], dict[str, str]]:
    rows = [
        row
        for row in load_rows("primary85_event_rows_595")
        if math.isclose(fnum(row.get("sidewall_deg_comsol")), PRIMARY_SIDEWALL_DEG_COMSOL)
    ]
    return {(row.get("route_id_nodi", ""), inum(row.get("diameter_nm"))): row for row in rows}


def candidate_route_rows() -> list[dict[str, str]]:
    return load_rows("recommendation_route_rows_598")


def plan_rows(
    *,
    n_events: int = DEFAULT_N_EVENTS,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    diameters = sorted(PRS_APPROVED_DIAMETERS_NM)
    for route_index, route_row in enumerate(candidate_route_rows()):
        source_route = route_row.get("source_route_id_nodi", "")
        candidate_route = route_row.get("candidate_envelope_route_id_nodi", "")
        lambda_nm, width_nm, depth_nm = parse_route_id(candidate_route)
        source_lambda, source_width_nm, source_depth_nm = parse_route_id(source_route)
        if lambda_nm != source_lambda or depth_nm != source_depth_nm:
            raise ValueError(f"candidate route changes lambda/depth: {source_route} -> {candidate_route}")
        taper = comsol_sidewall_deg_to_nodi_taper_deg(PRIMARY_SIDEWALL_DEG_COMSOL)
        geometry = TrapezoidCrossSection(
            top_width_m=nm_to_m(width_nm),
            depth_m=nm_to_m(depth_nm),
            sidewall_taper_angle_deg=taper,
        )
        for diameter_nm in diameters:
            seed = int(random_seed + route_index * 1000 + int(diameter_nm))
            row_id = (
                f"ENV-{route_case_id(source_route)}-to-{route_case_id(candidate_route)}-"
                f"P{diameter_nm}-N{n_events}-TH85"
            )
            rows.append(
                {
                    **common_guard_fields(row_id),
                    "source_artifacts_json": json.dumps(
                        [
                            "598_NODI_SIDEWALL_CANDIDATE_DIMENSION_RECOMMENDATION_SYNTHESIS_20260702",
                            "595_NODI_SIDEWALL_PRIMARY85_FULL_BOUNDED_EVENT_EXPANSION_20260702",
                            "run_single_case_batch",
                        ],
                        sort_keys=True,
                    ),
                    "shard_case_id": row_id,
                    "source_route_id_nodi": source_route,
                    "source_route_id_role": "join_key_only_not_selection",
                    "route_id_nodi": candidate_route,
                    "route_id_nodi_role": "candidate_envelope_context_not_selection",
                    "lambda_nm": lambda_nm,
                    "source_W_nominal_nm": source_width_nm,
                    "W_nominal_nm": width_nm,
                    "W_top_nm": width_nm,
                    "W_top_semantics": "candidate_envelope_runtime_top_aperture_surrogate",
                    "candidate_envelope_top_width_delta_nm": width_nm - source_width_nm,
                    "D_nm": depth_nm,
                    "depth_nm": depth_nm,
                    "diameter_nm": int(diameter_nm),
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
    return rows


def event_rows(*, execute_nodi: bool, n_events: int, random_seed: int) -> list[dict[str, Any]]:
    rows = plan_rows(n_events=n_events, random_seed=random_seed)
    if not execute_nodi:
        return rows
    executed_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        print(f"[candidate-envelope] {index}/{len(rows)} {row['shard_case_id']}", flush=True)
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


def candidate_delta_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    original = original_sidewall85_index()
    deltas: list[dict[str, Any]] = []
    for row in rows:
        key = (row["source_route_id_nodi"], int(row["diameter_nm"]))
        original_row = original.get(key, {})
        row_id = (
            f"ENV-DELTA-{route_case_id(row['source_route_id_nodi'])}-"
            f"P{row['diameter_nm']}-TH85"
        )
        deltas.append(
            {
                **common_guard_fields(row_id),
                "delta_case_id": row_id,
                "source_route_id_nodi": row["source_route_id_nodi"],
                "candidate_envelope_route_id_nodi": row["route_id_nodi"],
                "route_id_role": "candidate_envelope_join_key_only_not_selection",
                "diameter_nm": int(row["diameter_nm"]),
                "source_W_nominal_nm": int(row["source_W_nominal_nm"]),
                "candidate_W_top_nm": int(row["W_top_nm"]),
                "candidate_envelope_top_width_delta_nm": int(
                    row["candidate_envelope_top_width_delta_nm"]
                ),
                "sidewall_deg_comsol": PRIMARY_SIDEWALL_DEG_COMSOL,
                "candidate_n_events_requested": int(row["n_events_requested"]),
                "original_n_events_observed": inum(original_row.get("n_events_observed")),
                "candidate_n_events_observed": inum(row.get("n_events_observed")),
                "original_execution_status": original_row.get("execution_status", ""),
                "candidate_execution_status": row.get("execution_status", ""),
                "candidate_minus_original_selected_annulus_fraction_delta": delta_value(
                    row, original_row, "selected_annulus_fraction"
                ),
                "candidate_minus_original_mean_peak_height_delta": delta_value(
                    row, original_row, "mean_peak_height"
                ),
                "candidate_minus_original_mean_local_snr_delta": delta_value(
                    row, original_row, "mean_local_snr"
                ),
                "candidate_minus_original_synthetic_counting_context_rate_delta": delta_value(
                    row, original_row, "synthetic_counting_context_rate"
                ),
                "delta_status": "executed_candidate_envelope_delta_context"
                if row.get("execution_status") == "executed_bounded_nodi_shard"
                and original_row.get("execution_status") == "executed_bounded_nodi_shard"
                else "planned_candidate_envelope_delta_context",
            }
        )
    return deltas


def route_summary_rows(deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for delta in deltas:
        grouped[delta["source_route_id_nodi"]].append(delta)
    output: list[dict[str, Any]] = []
    for source_route, group in sorted(grouped.items()):
        response_improved = sum(
            fnum(row["candidate_minus_original_mean_peak_height_delta"]) > 0
            for row in group
        )
        annulus_improved = sum(
            fnum(row["candidate_minus_original_selected_annulus_fraction_delta"]) > 0
            for row in group
        )
        annulus_tradeoff = sum(
            fnum(row["candidate_minus_original_selected_annulus_fraction_delta"]) < 0
            for row in group
        )
        output.append(
            {
                **common_guard_fields(f"ENV-SUMMARY-{route_case_id(source_route)}"),
                "source_route_id_nodi": source_route,
                "candidate_envelope_route_id_nodi": group[0][
                    "candidate_envelope_route_id_nodi"
                ],
                "route_id_role": "candidate_envelope_summary_not_selection",
                "route_diameter_rows": len(group),
                "candidate_n_events_requested": group[0]["candidate_n_events_requested"],
                "candidate_rows_with_response_improvement": response_improved,
                "candidate_rows_with_annulus_improvement": annulus_improved,
                "candidate_rows_with_annulus_tradeoff": annulus_tradeoff,
                "max_candidate_minus_original_mean_peak_height_delta": max(
                    fnum(row["candidate_minus_original_mean_peak_height_delta"])
                    for row in group
                ),
                "max_candidate_minus_original_selected_annulus_fraction_delta": max(
                    fnum(row["candidate_minus_original_selected_annulus_fraction_delta"])
                    for row in group
                ),
                "candidate_envelope_sweep_context": "higher_event_context_ready"
                if all(
                    row["delta_status"] == "executed_candidate_envelope_delta_context"
                    for row in group
                )
                else "higher_event_plan_context",
            }
        )
    return output


def answer_axis_rows(deltas: list[dict[str, Any]], routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **common_guard_fields("ENV-AXIS-DIMENSION"),
            "answer_axis": "candidate_dimension_envelope",
            "answer": "candidate_envelope_dimensions_have_higher_event_context",
            "affected_rows": len(deltas),
            "route_rows": len(routes),
            "mainline_interpretation": (
                "six candidate envelope dimensions from 598 now have a higher-event "
                "85deg sparse simulation sweep across PRS-approved diameters"
            ),
        },
        {
            **common_guard_fields("ENV-AXIS-ANNULUS"),
            "answer_axis": "selected_annulus_range",
            "answer": "candidate_envelope_sweep_keeps_annulus_tradeoffs_visible",
            "affected_rows": sum(
                fnum(row["candidate_minus_original_selected_annulus_fraction_delta"]) != 0
                for row in deltas
            ),
            "route_rows": len(routes),
            "mainline_interpretation": (
                "annulus fraction changes remain mixed under candidate envelopes, "
                "so the annulus window must remain an explicit optimization axis"
            ),
        },
        {
            **common_guard_fields("ENV-AXIS-RESPONSE"),
            "answer_axis": "interference_response",
            "answer": "candidate_envelope_sweep_tests_interference_response_context",
            "affected_rows": sum(
                fnum(row["candidate_minus_original_mean_peak_height_delta"]) > 0
                for row in deltas
            ),
            "route_rows": len(routes),
            "mainline_interpretation": (
                "higher-event candidate envelope rows provide a stronger sparse "
                "context for peak-height/local-SNR response changes than the n=2 "
                "per-particle follow-up"
            ),
        },
    ]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    table_names = (
        "candidate_event_rows",
        "candidate_delta_rows",
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
    if payload["summary"]["candidate_event_rows"] != 78:
        failures.append("candidate event rows must cover 6 candidate envelopes x 13 diameters")
    if payload["summary"]["candidate_delta_rows"] != 78:
        failures.append("candidate delta rows must cover every candidate event row")
    if payload["summary"]["route_summary_rows"] != 6:
        failures.append("route summary rows must cover six source routes")
    if payload["summary"]["source_missing_rows"] != 0:
        failures.append("source artifacts missing")
    return failures


def validation_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    failures = validate_payload(payload)
    return [
        {
            "check_name": "candidate_event_coverage",
            "check_pass": payload["summary"]["candidate_event_rows"] == 78,
            "observed": payload["summary"]["candidate_event_rows"],
            "expected": 78,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "candidate_delta_coverage",
            "check_pass": payload["summary"]["candidate_delta_rows"] == 78,
            "observed": payload["summary"]["candidate_delta_rows"],
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


def semantic_digest(payload: dict[str, Any]) -> str:
    return deterministic_sha256(
        {
            "candidate_event_rows": payload["candidate_event_rows"],
            "candidate_delta_rows": payload["candidate_delta_rows"],
            "route_summary_rows": payload["route_summary_rows"],
        }
    )


def build_payload(*, execute_nodi: bool, n_events: int, random_seed: int) -> dict[str, Any]:
    rows = event_rows(
        execute_nodi=execute_nodi,
        n_events=n_events,
        random_seed=random_seed,
    )
    deltas = candidate_delta_rows(rows)
    route_rows = route_summary_rows(deltas)
    axes = answer_axis_rows(deltas, route_rows)
    sources = source_lock_rows()
    dirty = dirty_context_rows()
    summary = {
        "artifact_id": ARTIFACT_ID,
        "disposition": DISPOSITION_EXECUTED if execute_nodi else DISPOSITION_PLAN,
        "sweep_version": SWEEP_VERSION,
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
            row["delta_status"] == "executed_candidate_envelope_delta_context"
            for row in deltas
        ),
        "route_summary_rows": len(route_rows),
        "answer_axis_rows": len(axes),
        "candidate_rows_with_response_improvement": sum(
            fnum(row["candidate_minus_original_mean_peak_height_delta"]) > 0
            for row in deltas
        ),
        "candidate_rows_with_annulus_improvement": sum(
            fnum(row["candidate_minus_original_selected_annulus_fraction_delta"]) > 0
            for row in deltas
        ),
        "candidate_rows_with_annulus_tradeoff": sum(
            fnum(row["candidate_minus_original_selected_annulus_fraction_delta"]) < 0
            for row in deltas
        ),
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(1 for row in sources if row["exists"] == "false"),
        "dirty_context_rows": len(dirty),
        "non_candidate_envelope_sweep_dirty_context_rows": sum(
            1
            for row in dirty
            if row["classification"] == "non_candidate_envelope_sweep_dirty_context"
        ),
        "primary_answer_frame": "candidate_envelope_higher_event_sweep_for_dimensions_annulus_response",
        "not_primary_answer_frame": "route_winner_or_final_probability",
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    payload = {
        "summary": summary,
        "candidate_event_rows": rows,
        "candidate_delta_rows": deltas,
        "route_summary_rows": route_rows,
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
        "route_summary": OUTPUT_DIR / f"{PREFIX}_ROUTE_SUMMARY_ROWS_{DATE_STAMP}.csv",
        "answer_axis": OUTPUT_DIR / f"{PREFIX}_ANSWER_AXIS_ROWS_{DATE_STAMP}.csv",
        "validation": OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv",
        "failures": OUTPUT_DIR / f"{PREFIX}_FAILURES_{DATE_STAMP}.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv",
        "master_report": REPORT_DIR / f"599_{PREFIX}_{DATE_STAMP}.md",
    }
    write_json_atomic(outputs["status"], payload["summary"], sort_keys=True)
    write_csv_rows(outputs["candidate_events"], payload["candidate_event_rows"])
    write_csv_rows(outputs["candidate_deltas"], payload["candidate_delta_rows"])
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
            "# NODI Sidewall Candidate Envelope Higher-Event Sweep",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Execute NODI: `{s['execute_nodi']}`",
            f"Candidate event rows: `{s['candidate_event_rows']}`",
            f"Executed candidate event rows: `{s['executed_candidate_event_rows']}`",
            f"Candidate delta rows: `{s['candidate_delta_rows']}`",
            f"Route summary rows: `{s['route_summary_rows']}`",
            f"Failed validation rows: `{s['failed_validation_rows']}`",
            "",
            "This package runs a higher-event sparse sweep for the six candidate "
            "sidewall-aware envelope dimensions from 598. It strengthens the "
            "simulation context for dimension, annulus, and response follow-up, "
            "without emitting route winners, probabilities, yield, wet, or "
            "production claims.",
            "",
        ]
    )


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_sidewall_candidate_envelope_higher_event_sweep:
        print(
            "--confirm-sidewall-candidate-envelope-higher-event-sweep is required",
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
