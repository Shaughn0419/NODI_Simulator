#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator._exports import (  # noqa: E402
    BASELINE_PARTICLE,
    DEFAULT_SIM_CFG,
    PBS_1X,
    Channel,
    OpticalSystem,
    compute_baseline_normalization_per_wavelength,
    make_gold_baseline_particle,
    run_single_case_batch,
)
from nodi_simulator.cross_section_geometry import (  # noqa: E402
    TrapezoidCrossSection,
    comsol_sidewall_deg_to_nodi_taper_deg,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260702"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_BOUNDED_EVENT_SHARDS"
ARTIFACT_ID = "NODI_SIDEWALL_BOUNDED_EVENT_SHARDS_20260702"
SHARD_VERSION = "sidewall_bounded_event_shards_v1"
DISPOSITION_EXECUTED = "NODI_SIDEWALL_BOUNDED_EVENT_SHARDS_EXECUTED_READY"
DISPOSITION_PLAN = "NODI_SIDEWALL_BOUNDED_EVENT_SHARDS_PLAN_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_BOUNDED_EVENT_SHARDS_FAIL_CLOSED"
CLAIM_BOUNDARY = (
    "bounded_nodi_event_context_for_sidewall_dimension_annulus_response_not_probability"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

BOUNDED_ROUTES = (
    (404, 500, 900),
    (404, 500, 1200),
    (404, 600, 900),
    (660, 800, 900),
)
SIDEWALL_PAIR_DEG_COMSOL = (90.0, 85.0)
PARTICLE_DIAMETERS_NM = (100, 220, 300)
DEFAULT_N_EVENTS = 4
DEFAULT_RANDOM_SEED = 59100

SOURCE_FILES = {
    "multiwidth_response_status": OUTPUT_DIR
    / "NODI_SIDEWALL_MULTIWIDTH_RESPONSE_EXPANSION_STATUS_20260702.json",
    "multiwidth_dimension_rows": OUTPUT_DIR
    / "NODI_SIDEWALL_MULTIWIDTH_RESPONSE_EXPANSION_DIMENSION_WINDOW_ROWS_20260702.csv",
    "multiwidth_response_rows": OUTPUT_DIR
    / "NODI_SIDEWALL_MULTIWIDTH_RESPONSE_EXPANSION_TRAPEZOID_LOCAL_RESPONSE_BIN_ROWS_20260702.csv",
    "bounded_event_shards_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_bounded_event_shards.py",
    "bounded_event_shards_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_bounded_event_shards.py",
}

ALLOWED_USE = (
    "execute a bounded NODI event shard set to compare rectangle and sidewall "
    "contexts for dimension, selected-annulus, and response-map follow-up"
)
BLOCKED_USE = (
    "production PRS, route winner, route score, final detection probability, "
    "yield, wet claim, fabrication release, q_ch weighting, or true W_eff"
)
COMMON_SOURCE_ARTIFACTS_JSON = json.dumps(
    [
        "590_NODI_SIDEWALL_MULTIWIDTH_RESPONSE_EXPANSION_20260702",
        "run_single_case_batch",
        "trapezoid_effective_aperture_surrogate",
        "tsuyama_2022_counting_10sigma",
    ],
    sort_keys=True,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build or execute bounded NODI sidewall event shards."
    )
    parser.add_argument("--confirm-sidewall-bounded-event-shards", action="store_true")
    parser.add_argument("--execute-nodi-bounded-shards", action="store_true")
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


def load_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def nm_to_m(value_nm: float) -> float:
    return float(value_nm) * 1.0e-9


def m_to_nm(value_m: float) -> float:
    return float(value_m) * 1.0e9


def route_id(lambda_nm: int, width_nm: int, depth_nm: int) -> str:
    return f"{int(lambda_nm)}/W{int(width_nm)}/D{int(depth_nm)}"


def route_case_id(lambda_nm: int, width_nm: int, depth_nm: int) -> str:
    return route_id(lambda_nm, width_nm, depth_nm).replace("/", "_")


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
    output_report = f"reports/591_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_bounded_event_shards.py",
        "tests/test_nodi_sidewall_bounded_event_shards.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "bounded_event_shards_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "bounded_event_shards_output"
            release_decision = "included_or_rewritten_by_bounded_event_shards_builder"
        else:
            classification = "non_bounded_event_shards_dirty_context"
            release_decision = "ignored_for_bounded_event_shards"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def common_fields(row_id: str) -> dict[str, Any]:
    return {
        "shard_version": SHARD_VERSION,
        "row_id": row_id,
        "source_artifacts_json": COMMON_SOURCE_ARTIFACTS_JSON,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "not_detection_probability": True,
        "not_yield": True,
        "not_route_score": True,
        "not_winner": True,
        "not_qch_weighted": True,
        "not_true_W_eff": True,
        "not_production_prs": True,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def bounded_shard_plan_rows(
    *,
    n_events: int = DEFAULT_N_EVENTS,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for route_index, (lambda_nm, width_nm, depth_nm) in enumerate(BOUNDED_ROUTES):
        for theta in SIDEWALL_PAIR_DEG_COMSOL:
            geometry = TrapezoidCrossSection(
                top_width_m=nm_to_m(width_nm),
                depth_m=nm_to_m(depth_nm),
                sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(theta),
            )
            for diameter_nm in PARTICLE_DIAMETERS_NM:
                seed = int(random_seed + route_index * 100 + int(theta) + diameter_nm)
                row_id = (
                    f"SHARD-{route_case_id(lambda_nm, width_nm, depth_nm)}-"
                    f"TH{theta:g}-P{diameter_nm}"
                )
                rows.append(
                    {
                        **common_fields(row_id),
                        "shard_case_id": row_id,
                        "route_id_nodi": route_id(lambda_nm, width_nm, depth_nm),
                        "route_id_nodi_role": "join_key_only_not_selection",
                        "lambda_nm": int(lambda_nm),
                        "W_nominal_nm": int(width_nm),
                        "W_top_nm": int(width_nm),
                        "W_top_semantics": "runtime_top_aperture_surrogate",
                        "D_nm": int(depth_nm),
                        "depth_nm": int(depth_nm),
                        "diameter_nm": int(diameter_nm),
                        "particle_model": "gold_baseline_material_model",
                        "channel_cross_section_model": "ideal_rectangle"
                        if math.isclose(theta, 90.0)
                        else "trapezoid_tapered_sidewalls",
                        "sidewall_angle_convention": "comsol_from_horizontal",
                        "sidewall_deg_comsol": float(theta),
                        "sidewall_taper_angle_deg_nodi": (
                            comsol_sidewall_deg_to_nodi_taper_deg(theta)
                        ),
                        "W_bottom_unclipped_nm": m_to_nm(
                            geometry.bottom_width_unclipped_m
                        ),
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


def _float_value(value: Any) -> float | str:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(result):
        return ""
    return result


def execute_shard_row(plan_row: dict[str, Any]) -> dict[str, Any]:
    lambda_nm = int(plan_row["lambda_nm"])
    width_nm = int(plan_row["W_nominal_nm"])
    depth_nm = int(plan_row["D_nm"])
    diameter_nm = int(plan_row["diameter_nm"])
    theta = float(plan_row["sidewall_deg_comsol"])
    channel = Channel(width_m=nm_to_m(width_nm), depth_m=nm_to_m(depth_nm))
    optical = OpticalSystem(
        wavelength_m=nm_to_m(lambda_nm),
        peak_irradiance_W_m2=1.0,
        beam_waist_x_m=300e-9,
        beam_waist_y_m=700e-9,
        beam_waist_z_m=300e-9,
    )
    particle = make_gold_baseline_particle(
        diameter_nm=float(diameter_nm),
        name=f"gold_{diameter_nm}nm_diameter",
    )
    sim_cfg = replace(
        DEFAULT_SIM_CFG,
        total_time_s=0.09,
        sampling_rate_Hz=10_000.0,
        mean_flow_velocity_m_s=2.0e-4,
        n_events=int(plan_row["n_events_requested"]),
        random_seed=int(plan_row["random_seed"]),
        include_diffusion=False,
        flow_profile_model="plug",
        diffusion_hindrance_model="none",
        reference_model="trapezoid_effective_aperture_surrogate",
        reference_spatial_mode="cross_section_surrogate",
        channel_cross_section_model=str(plan_row["channel_cross_section_model"]),
        sidewall_taper_angle_deg=float(plan_row["sidewall_taper_angle_deg_nodi"]),
        readout_preset="tsuyama_2022_counting_10sigma",
        vectorized_event_engine="off",
    )
    theta_grid = np.linspace(1.0e-3, math.pi - 1.0e-3, 181)
    e_sca_ref = compute_baseline_normalization_per_wavelength(
        BASELINE_PARTICLE,
        PBS_1X,
        optical,
        np.array([optical.wavelength_m]),
        theta_grid,
        channel=channel,
        sim_cfg=sim_cfg,
    )[optical.wavelength_m]
    result = run_single_case_batch(
        particle,
        PBS_1X,
        channel,
        optical,
        sim_cfg,
        e_sca_ref,
        theta_grid,
        retain_event_traces=False,
        stream_summary_only=True,
    )
    summary = dict(result.get("summary", {}))
    row = dict(plan_row)
    row.update(
        {
            "execution_status": "executed_bounded_nodi_shard",
            "n_events_observed": int(summary.get("n_events", 0) or 0),
            "synthetic_counting_context_rate": _float_value(
                summary.get("detection_rate")
            ),
            "stable_counting_context_rate": _float_value(
                summary.get("stable_detection_rate")
            ),
            "mean_peak_height": _float_value(summary.get("mean_peak_height")),
            "mean_local_snr": _float_value(summary.get("mean_local_snr")),
            "selected_annulus_source": str(
                summary.get("selected_detector_mode_annulus_source", "")
            ),
            "selected_annulus_edge_norm_min": _float_value(
                summary.get("selected_detector_mode_annulus_edge_norm_min")
            ),
            "selected_annulus_edge_norm_max": _float_value(
                summary.get("selected_detector_mode_annulus_edge_norm_max")
            ),
            "selected_annulus_n_events": int(
                summary.get("selected_detector_mode_annulus_n_events", 0) or 0
            ),
            "selected_annulus_fraction": _float_value(
                summary.get("selected_detector_mode_annulus_fraction")
            ),
            "selected_annulus_mean_edge_norm": _float_value(
                summary.get("selected_detector_mode_annulus_mean_edge_norm")
            ),
            "selected_annulus_counting_context_rate": _float_value(
                summary.get("selected_detector_mode_annulus_detection_rate")
            ),
            "reference_geometry_propagation_status": str(
                summary.get("reference_geometry_propagation_status", "")
            ),
            "reference_geometry_claim_level": str(
                summary.get("reference_geometry_claim_level", "")
            ),
            "geometry_not_propagated_to_reference_field": bool(
                summary.get("geometry_not_propagated_to_reference_field", False)
            ),
            "reference_uses_rectangular_width_depth_surrogate": bool(
                summary.get("reference_uses_rectangular_width_depth_surrogate", False)
            ),
            "not_optical_solver_output": bool(
                summary.get("not_optical_solver_output", True)
            ),
            "optical_solver_trigger_is_result": bool(
                summary.get("optical_solver_trigger_is_result", False)
            ),
            "not_event_run_probability_claim": True,
        }
    )
    return row


def event_shard_rows(
    *,
    execute_nodi: bool,
    n_events: int,
    random_seed: int,
) -> list[dict[str, Any]]:
    plan_rows = bounded_shard_plan_rows(n_events=n_events, random_seed=random_seed)
    if not execute_nodi:
        return plan_rows
    rows: list[dict[str, Any]] = []
    for index, plan_row in enumerate(plan_rows, start=1):
        print(
            f"[bounded-shard] {index}/{len(plan_rows)} {plan_row['shard_case_id']}",
            flush=True,
        )
        rows.append(execute_shard_row(plan_row))
    return rows


def paired_delta_rows(event_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = {
        (
            row["route_id_nodi"],
            int(row["diameter_nm"]),
            float(row["sidewall_deg_comsol"]),
        ): row
        for row in event_rows
    }
    rows: list[dict[str, Any]] = []
    for route, diameter_nm, theta in sorted(lookup):
        if not math.isclose(theta, 85.0):
            continue
        rectangle = lookup.get((route, diameter_nm, 90.0))
        sidewall = lookup[(route, diameter_nm, theta)]
        if rectangle is None:
            continue
        row_id = f"DELTA-{str(route).replace('/', '_')}-P{diameter_nm}-TH85_vs_TH90"
        def delta(field: str) -> float | str:
            left = rectangle.get(field)
            right = sidewall.get(field)
            if left in {"", None} or right in {"", None}:
                return ""
            try:
                return float(right) - float(left)
            except (TypeError, ValueError):
                return ""

        rows.append(
            {
                **common_fields(row_id),
                "delta_case_id": row_id,
                "route_id_nodi": route,
                "route_id_nodi_role": "join_key_only_not_selection",
                "diameter_nm": int(diameter_nm),
                "baseline_sidewall_deg_comsol": 90.0,
                "sidewall_deg_comsol": 85.0,
                "synthetic_counting_context_rate_delta": delta(
                    "synthetic_counting_context_rate"
                ),
                "mean_peak_height_delta": delta("mean_peak_height"),
                "mean_local_snr_delta": delta("mean_local_snr"),
                "selected_annulus_fraction_delta": delta(
                    "selected_annulus_fraction"
                ),
                "selected_annulus_mean_edge_norm_delta": delta(
                    "selected_annulus_mean_edge_norm"
                ),
                "delta_status": "executed_delta_context"
                if sidewall.get("execution_status") == "executed_bounded_nodi_shard"
                else "planned_delta_context",
            }
        )
    return rows


def axis_synthesis_rows(
    event_rows: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    executed = [row for row in event_rows if row["execution_status"].startswith("executed")]
    peak_deltas = [
        abs(float(row["mean_peak_height_delta"]))
        for row in delta_rows
        if row["mean_peak_height_delta"] not in {"", None}
    ]
    annulus_deltas = [
        abs(float(row["selected_annulus_fraction_delta"]))
        for row in delta_rows
        if row["selected_annulus_fraction_delta"] not in {"", None}
    ]
    return [
        {
            "axis_id": "AXIS-001",
            "axis_name": "bounded_event_execution",
            "axis_status": "executed" if executed else "planned",
            "evidence_rows": len(event_rows),
            "executed_rows": len(executed),
            "key_observation": "bounded NODI event shards generated paired rectangle/sidewall context",
        },
        {
            "axis_id": "AXIS-002",
            "axis_name": "selected_annulus_event_context",
            "axis_status": "annulus_delta_available" if annulus_deltas else "annulus_delta_planned",
            "evidence_rows": len(delta_rows),
            "max_abs_delta": max(annulus_deltas) if annulus_deltas else "",
            "key_observation": "selected annulus fraction and edge norm are compared as context, not probability",
        },
        {
            "axis_id": "AXIS-003",
            "axis_name": "interference_response_event_context",
            "axis_status": "response_delta_available" if peak_deltas else "response_delta_planned",
            "evidence_rows": len(delta_rows),
            "max_abs_delta": max(peak_deltas) if peak_deltas else "",
            "key_observation": "mean peak height and local SNR provide bounded event response context",
        },
    ]


def alignment_check_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    event_rows = payload["event_shard_rows"]
    delta_rows = payload["paired_delta_rows"]
    forbidden_exact_columns = {
        "winner",
        "route_score",
        "rank",
        "detection_probability",
        "yield",
        "W_eff",
        "q_ch_eta",
    }
    all_columns: set[str] = set()
    for table in (event_rows, delta_rows):
        for row in table:
            all_columns.update(row)
    planned_count = len(bounded_shard_plan_rows())
    checks = [
        (
            "bounded_plan_row_count",
            len(event_rows) == planned_count,
            str(len(event_rows)),
        ),
        (
            "paired_delta_rows_present",
            len(delta_rows)
            == len(BOUNDED_ROUTES) * len(PARTICLE_DIAMETERS_NM),
            str(len(delta_rows)),
        ),
        (
            "event_rows_have_no_probability_claim",
            all(row.get("not_detection_probability") is True for row in event_rows),
            "not_detection_probability true",
        ),
        (
            "forbidden_primary_columns_absent",
            forbidden_exact_columns.isdisjoint(all_columns),
            ",".join(sorted(forbidden_exact_columns & all_columns)),
        ),
        (
            "bounded_routes_include_width_variation",
            {int(row["W_nominal_nm"]) for row in event_rows} >= {500, 600, 800},
            str(sorted({int(row["W_nominal_nm"]) for row in event_rows})),
        ),
    ]
    return [
        {
            "check_id": f"BOUNDED-SHARD-CHECK-{index:03d}",
            "check_name": name,
            "check_pass": bool(passed),
            "check_detail": detail,
            "hard_fail_if_false": True,
        }
        for index, (name, passed, detail) in enumerate(checks, start=1)
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "event_shard_rows": payload["event_shard_rows"],
                "paired_delta_rows": payload["paired_delta_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload(
    *,
    execute_nodi: bool,
    n_events: int = DEFAULT_N_EVENTS,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> dict[str, Any]:
    event_rows = event_shard_rows(
        execute_nodi=execute_nodi,
        n_events=n_events,
        random_seed=random_seed,
    )
    delta_rows = paired_delta_rows(event_rows)
    synthesis_rows = axis_synthesis_rows(event_rows, delta_rows)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    payload: dict[str, Any] = {
        "event_shard_rows": event_rows,
        "paired_delta_rows": delta_rows,
        "axis_synthesis_rows": synthesis_rows,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    checks = alignment_check_rows(payload)
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    failed_checks = sum(not row["check_pass"] for row in checks)
    expansion = load_summary(SOURCE_FILES["multiwidth_response_status"])
    disposition = DISPOSITION_EXECUTED if execute_nodi else DISPOSITION_PLAN
    if source_missing or failed_checks:
        disposition = BLOCKED_DISPOSITION
    payload["alignment_check_rows"] = checks
    payload["summary"] = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "multiwidth_response_disposition": expansion.get("disposition", ""),
        "execute_nodi": bool(execute_nodi),
        "bounded_route_count": len(BOUNDED_ROUTES),
        "particle_diameter_count": len(PARTICLE_DIAMETERS_NM),
        "n_events_requested_per_shard": int(n_events),
        "event_shard_rows": len(event_rows),
        "executed_event_shard_rows": sum(
            row["execution_status"] == "executed_bounded_nodi_shard"
            for row in event_rows
        ),
        "paired_delta_rows": len(delta_rows),
        "axis_synthesis_rows": len(synthesis_rows),
        "alignment_check_rows": len(checks),
        "failed_alignment_check_rows": failed_checks,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_bounded_event_shards_dirty_context_rows": sum(
            row["classification"] == "non_bounded_event_shards_dirty_context"
            for row in dirty_context
        ),
        "primary_answer_frame": "bounded_nodi_event_context_for_sidewall_annulus_response",
        "not_primary_answer_frame": "route_selection_or_probability_claim",
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "next_large_block": "expand executed shards into PRS sidewall v2 candidate rows",
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    if summary["disposition"] not in {DISPOSITION_EXECUTED, DISPOSITION_PLAN}:
        failures.append("bounded_event_shards_not_ready")
    if summary["event_shard_rows"] == 0:
        failures.append("event_shard_rows_missing")
    if summary["paired_delta_rows"] == 0:
        failures.append("paired_delta_rows_missing")
    if summary["failed_alignment_check_rows"] != 0:
        failures.append("failed_alignment_checks_present")
    if summary["source_missing_rows"] != 0:
        failures.append("source_missing")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json",
        "event_shards": OUTPUT_DIR / f"{PREFIX}_EVENT_SHARD_ROWS_{DATE_STAMP}.csv",
        "paired_deltas": OUTPUT_DIR / f"{PREFIX}_PAIRED_DELTA_ROWS_{DATE_STAMP}.csv",
        "axis_synthesis": OUTPUT_DIR / f"{PREFIX}_AXIS_SYNTHESIS_ROWS_{DATE_STAMP}.csv",
        "alignment_checks": OUTPUT_DIR / f"{PREFIX}_ALIGNMENT_CHECK_ROWS_{DATE_STAMP}.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "master_report": REPORT_DIR / f"591_{PREFIX}_{DATE_STAMP}.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv",
    }
    write_json_atomic(
        outputs["status"],
        {
            "disposition": payload["summary"]["disposition"],
            "summary": payload["summary"],
        },
        sort_keys=True,
    )
    write_csv_rows(outputs["event_shards"], payload["event_shard_rows"])
    write_csv_rows(outputs["paired_deltas"], payload["paired_delta_rows"])
    write_csv_rows(outputs["axis_synthesis"], payload["axis_synthesis_rows"])
    write_csv_rows(outputs["alignment_checks"], payload["alignment_check_rows"])
    write_csv_rows(outputs["source_lock"], payload["source_lock_rows"])
    write_csv_rows(outputs["dirty_context"], payload["dirty_context_rows"])
    write_json_atomic(outputs["report_json"], payload, indent=None, sort_keys=True)
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
        "# NODI Sidewall Bounded Event Shards",
        "",
        f"Disposition: `{s['disposition']}`",
        f"Artifact ID: `{s['artifact_id']}`",
        f"Claim boundary: `{s['claim_boundary']}`",
        "",
        "This package runs, or plans, a bounded set of paired rectangle/sidewall "
        "NODI event shards over representative PRS-approved routes and particle "
        "diameters. The output is event context for dimension, selected-annulus, "
        "and response-map follow-up.",
        "",
        f"Execute NODI: `{s['execute_nodi']}`.",
        f"Event shard rows: `{s['event_shard_rows']}`.",
        f"Executed rows: `{s['executed_event_shard_rows']}`.",
        f"Paired delta rows: `{s['paired_delta_rows']}`.",
        f"Alignment check failures: `{s['failed_alignment_check_rows']}`.",
        "",
        "## Axis Synthesis",
        "",
    ]
    for row in payload["axis_synthesis_rows"]:
        lines.extend(
            [
                f"- `{row['axis_name']}`: `{row['axis_status']}`",
                f"  Evidence rows: `{row['evidence_rows']}`",
                f"  Key observation: `{row['key_observation']}`",
            ]
        )
    lines.extend(
        [
            "",
            "The shard rows keep counting outputs as synthetic context, not final "
            "detection probability. Route ids remain join keys only.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_bounded_event_shards:
        raise SystemExit("--confirm-sidewall-bounded-event-shards is required")
    payload = build_payload(
        execute_nodi=bool(args.execute_nodi_bounded_shards),
        n_events=int(args.n_events),
        random_seed=int(args.random_seed),
    )
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
