#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import replace
import hashlib
import json
import math
import re
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


DATE_STAMP = "20260703"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_CANDIDATE_ENVELOPE_ANNULUS_WINDOW_SWEEP"
ARTIFACT_ID = "NODI_SIDEWALL_CANDIDATE_ENVELOPE_ANNULUS_WINDOW_SWEEP_20260703"
SWEEP_VERSION = "sidewall_candidate_envelope_annulus_window_sweep_v1"
DISPOSITION_EXECUTED = "NODI_SIDEWALL_CANDIDATE_ENVELOPE_ANNULUS_WINDOW_SWEEP_EXECUTED_READY"
DISPOSITION_PLAN = "NODI_SIDEWALL_CANDIDATE_ENVELOPE_ANNULUS_WINDOW_SWEEP_PLAN_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_CANDIDATE_ENVELOPE_ANNULUS_WINDOW_SWEEP_FAIL_CLOSED"
CLAIM_BOUNDARY = "annulus_window_sweep_context_not_probability_not_selection"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
PRIMARY_SIDEWALL_DEG_COMSOL = 85.0
DEFAULT_N_EVENTS = 6
DEFAULT_RANDOM_SEED = 60000
CANONICAL_WINDOW = (0.5, 0.8)
ANNULUS_WINDOWS = (
    (0.4, 0.7),
    CANONICAL_WINDOW,
    (0.6, 0.9),
)

SOURCE_FILES = {
    "candidate_envelope_status_599": PROJECT_ROOT
    / "reports/joint_interface_20260702/NODI_SIDEWALL_CANDIDATE_ENVELOPE_HIGHER_EVENT_SWEEP_STATUS_20260702.json",
    "candidate_envelope_route_summary_599": PROJECT_ROOT
    / "reports/joint_interface_20260702/NODI_SIDEWALL_CANDIDATE_ENVELOPE_HIGHER_EVENT_SWEEP_ROUTE_SUMMARY_ROWS_20260702.csv",
    "candidate_envelope_event_rows_599": PROJECT_ROOT
    / "reports/joint_interface_20260702/NODI_SIDEWALL_CANDIDATE_ENVELOPE_HIGHER_EVENT_SWEEP_CANDIDATE_EVENT_ROWS_20260702.csv",
    "annulus_window_sweep_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_candidate_envelope_annulus_window_sweep.py",
    "annulus_window_sweep_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_candidate_envelope_annulus_window_sweep.py",
}

ALLOWED_USE = (
    "run sparse annulus-window context on sidewall-aware candidate envelope "
    "dimensions for selected-annulus and response follow-up"
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
        description="Build/execute candidate envelope annulus-window sweep."
    )
    parser.add_argument(
        "--confirm-sidewall-candidate-envelope-annulus-window-sweep",
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


def annulus_window_id(inner: float, outer: float) -> str:
    def part(value: float) -> str:
        return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", "p")

    return f"{part(inner)}_{part(outer)}"


def route_case_id(route: str) -> str:
    return str(route).replace("/", "_")


def parse_route_id(route: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"(\d+)/W(\d+)/D(\d+)", str(route))
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
    output_report = f"reports/600_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_candidate_envelope_annulus_window_sweep.py",
        "tests/test_nodi_sidewall_candidate_envelope_annulus_window_sweep.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "annulus_window_sweep_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "annulus_window_sweep_output"
            release_decision = "included_or_rewritten_by_annulus_window_sweep_builder"
        else:
            classification = "non_annulus_window_sweep_dirty_context"
            release_decision = "ignored_for_annulus_window_sweep"
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


def candidate_route_rows() -> list[dict[str, str]]:
    return load_rows("candidate_envelope_route_summary_599")


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
        for window_index, (inner, outer) in enumerate(ANNULUS_WINDOWS):
            window_id = annulus_window_id(inner, outer)
            for diameter_nm in diameters:
                seed = int(
                    random_seed
                    + route_index * 10000
                    + window_index * 1000
                    + int(diameter_nm)
                )
                row_id = (
                    f"ANN-{route_case_id(source_route)}-to-{route_case_id(candidate_route)}-"
                    f"P{diameter_nm}-A{window_id}-N{n_events}-TH85"
                )
                rows.append(
                    {
                        **common_guard_fields(row_id),
                        "source_artifacts_json": json.dumps(
                            [
                                "599_NODI_SIDEWALL_CANDIDATE_ENVELOPE_HIGHER_EVENT_SWEEP_20260702",
                                "run_single_case_batch",
                                "selected_annulus_edge_norm_min_max",
                            ],
                            sort_keys=True,
                        ),
                        "shard_case_id": row_id,
                        "source_route_id_nodi": source_route,
                        "source_route_id_role": "join_key_only_not_selection",
                        "route_id_nodi": candidate_route,
                        "route_id_nodi_role": "candidate_envelope_annulus_context_not_selection",
                        "lambda_nm": lambda_nm,
                        "source_W_nominal_nm": source_width_nm,
                        "W_nominal_nm": width_nm,
                        "W_top_nm": width_nm,
                        "W_top_semantics": "candidate_envelope_runtime_top_aperture_surrogate",
                        "candidate_envelope_top_width_delta_nm": width_nm - source_width_nm,
                        "D_nm": depth_nm,
                        "depth_nm": depth_nm,
                        "diameter_nm": int(diameter_nm),
                        "annulus_window_id": window_id,
                        "selected_annulus_edge_norm_min": float(inner),
                        "selected_annulus_edge_norm_max": float(outer),
                        "is_canonical_annulus_window": (inner, outer) == CANONICAL_WINDOW,
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


def _float_value(value: Any) -> float | str:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return ""
    return result if math.isfinite(result) else ""


def execute_annulus_row(plan_row: dict[str, Any]) -> dict[str, Any]:
    lambda_nm = int(plan_row["lambda_nm"])
    width_nm = int(plan_row["W_nominal_nm"])
    depth_nm = int(plan_row["D_nm"])
    diameter_nm = int(plan_row["diameter_nm"])
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
        selected_annulus_edge_norm_min=float(plan_row["selected_annulus_edge_norm_min"]),
        selected_annulus_edge_norm_max=float(plan_row["selected_annulus_edge_norm_max"]),
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
            "execution_status": "executed_annulus_window_nodi_shard",
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
            "selected_annulus_edge_norm_min_observed": _float_value(
                summary.get("selected_detector_mode_annulus_edge_norm_min")
            ),
            "selected_annulus_edge_norm_max_observed": _float_value(
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


def event_rows(*, execute_nodi: bool, n_events: int, random_seed: int) -> list[dict[str, Any]]:
    rows = plan_rows(n_events=n_events, random_seed=random_seed)
    if not execute_nodi:
        return rows
    executed_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        print(f"[annulus-window] {index}/{len(rows)} {row['shard_case_id']}", flush=True)
        executed_rows.append(execute_annulus_row(row))
    return executed_rows


def window_comparison_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = {
        (
            row["source_route_id_nodi"],
            int(row["diameter_nm"]),
            row["annulus_window_id"],
        ): row
        for row in rows
    }
    output: list[dict[str, Any]] = []
    canonical_id = annulus_window_id(*CANONICAL_WINDOW)
    for row in rows:
        canonical = lookup.get(
            (row["source_route_id_nodi"], int(row["diameter_nm"]), canonical_id),
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
            f"ANN-CMP-{route_case_id(row['source_route_id_nodi'])}-"
            f"P{row['diameter_nm']}-A{row['annulus_window_id']}"
        )
        output.append(
            {
                **common_guard_fields(row_id),
                "comparison_case_id": row_id,
                "source_route_id_nodi": row["source_route_id_nodi"],
                "candidate_envelope_route_id_nodi": row["route_id_nodi"],
                "route_id_role": "annulus_window_join_key_only_not_selection",
                "diameter_nm": int(row["diameter_nm"]),
                "annulus_window_id": row["annulus_window_id"],
                "selected_annulus_edge_norm_min": row["selected_annulus_edge_norm_min"],
                "selected_annulus_edge_norm_max": row["selected_annulus_edge_norm_max"],
                "canonical_annulus_window_id": canonical_id,
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
                "mean_local_snr_delta_vs_canonical": delta("mean_local_snr"),
                "synthetic_counting_context_rate_delta_vs_canonical": delta(
                    "synthetic_counting_context_rate"
                ),
                "window_context_status": "executed_annulus_window_context"
                if row.get("execution_status") == "executed_annulus_window_nodi_shard"
                else "planned_annulus_window_context",
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
        positive_annulus = sum(
            fnum(row["selected_annulus_fraction_delta_vs_canonical"]) > 0
            for row in group
        )
        negative_annulus = sum(
            fnum(row["selected_annulus_fraction_delta_vs_canonical"]) < 0
            for row in group
        )
        output.append(
            {
                **common_guard_fields(f"ANN-SUM-{route_case_id(source_route)}-{window_id}"),
                "source_route_id_nodi": source_route,
                "candidate_envelope_route_id_nodi": group[0][
                    "candidate_envelope_route_id_nodi"
                ],
                "route_id_role": "route_window_summary_not_selection",
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
                "diameters_with_annulus_fraction_above_canonical": positive_annulus,
                "diameters_with_annulus_fraction_below_canonical": negative_annulus,
                "mean_selected_annulus_fraction": sum(
                    fnum(row["selected_annulus_fraction"]) for row in group
                )
                / len(group),
                "mean_peak_height": sum(fnum(row["mean_peak_height"]) for row in group)
                / len(group),
                "mean_peak_height_delta_vs_canonical": sum(
                    fnum(row["mean_peak_height_delta_vs_canonical"]) for row in group
                )
                / len(group),
                "mean_annulus_fraction_delta_vs_canonical": sum(
                    fnum(row["selected_annulus_fraction_delta_vs_canonical"])
                    for row in group
                )
                / len(group),
                "annulus_window_followup_context": (
                    "window_changes_response_or_annulus_context"
                    if positive_peak or positive_annulus or negative_annulus
                    else "canonical_equivalent_context_in_sparse_sweep"
                ),
            }
        )
    return output


def answer_axis_rows(comparisons: list[dict[str, Any]], summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    noncanonical = [
        row for row in comparisons if row["is_canonical_annulus_window"] is not True
    ]
    return [
        {
            **common_guard_fields("ANN-AXIS-ANNULUS-RANGE"),
            "answer_axis": "selected_annulus_range",
            "answer": "annulus_window_changes_under_sidewall_candidate_envelopes",
            "affected_rows": sum(
                fnum(row["selected_annulus_fraction_delta_vs_canonical"]) != 0
                for row in noncanonical
            ),
            "route_window_rows": len(summaries),
            "mainline_interpretation": (
                "noncanonical annulus windows change selected-annulus event context "
                "under sidewall-aware candidate dimensions, so the 0.5-0.8 window "
                "should remain an explicit simulation axis"
            ),
        },
        {
            **common_guard_fields("ANN-AXIS-INTERFERENCE"),
            "answer_axis": "interference_response",
            "answer": "annulus_window_changes_response_context",
            "affected_rows": sum(
                fnum(row["mean_peak_height_delta_vs_canonical"]) != 0
                for row in noncanonical
            ),
            "route_window_rows": len(summaries),
            "mainline_interpretation": (
                "annulus window changes alter peak-height/local-SNR sparse context "
                "even after width compensation"
            ),
        },
        {
            **common_guard_fields("ANN-AXIS-DIMENSION"),
            "answer_axis": "candidate_dimension_envelope",
            "answer": "dimension_envelopes_retained_while_annulus_window_is_swept",
            "affected_rows": len({row["candidate_envelope_route_id_nodi"] for row in comparisons}),
            "route_window_rows": len(summaries),
            "mainline_interpretation": (
                "candidate dimensions from 598/599 are held fixed while annulus "
                "window is swept, separating geometry compensation from detector "
                "annulus choice"
            ),
        },
    ]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    table_names = (
        "event_rows",
        "window_comparison_rows",
        "route_window_summary_rows",
        "answer_axis_rows",
    )
    columns: set[str] = set()
    for table_name in table_names:
        if payload[table_name]:
            columns |= set().union(*(set(row) for row in payload[table_name]))
    forbidden = sorted(columns & FORBIDDEN_PRIMARY_COLUMNS)
    if forbidden:
        failures.append(f"forbidden columns present: {forbidden}")
    if payload["summary"]["event_rows"] != 234:
        failures.append("event rows must cover 6 routes x 13 diameters x 3 windows")
    if payload["summary"]["window_comparison_rows"] != 234:
        failures.append("comparison rows must cover every event row")
    if payload["summary"]["route_window_summary_rows"] != 18:
        failures.append("route-window rows must cover 6 routes x 3 windows")
    if payload["summary"]["source_missing_rows"] != 0:
        failures.append("source artifacts missing")
    return failures


def validation_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    failures = validate_payload(payload)
    return [
        {
            "check_name": "annulus_window_event_coverage",
            "check_pass": payload["summary"]["event_rows"] == 234,
            "observed": payload["summary"]["event_rows"],
            "expected": 234,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "route_window_summary_coverage",
            "check_pass": payload["summary"]["route_window_summary_rows"] == 18,
            "observed": payload["summary"]["route_window_summary_rows"],
            "expected": 18,
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
            "event_rows": payload["event_rows"],
            "window_comparison_rows": payload["window_comparison_rows"],
            "route_window_summary_rows": payload["route_window_summary_rows"],
        }
    )


def build_payload(*, execute_nodi: bool, n_events: int, random_seed: int) -> dict[str, Any]:
    rows = event_rows(
        execute_nodi=execute_nodi,
        n_events=n_events,
        random_seed=random_seed,
    )
    comparisons = window_comparison_rows(rows)
    summaries = route_window_summary_rows(comparisons)
    axes = answer_axis_rows(comparisons, summaries)
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
        "candidate_envelope_route_count": len(candidate_route_rows()),
        "diameter_count": len(PRS_APPROVED_DIAMETERS_NM),
        "annulus_window_count": len(ANNULUS_WINDOWS),
        "event_rows": len(rows),
        "executed_event_rows": sum(
            row.get("execution_status") == "executed_annulus_window_nodi_shard"
            for row in rows
        ),
        "window_comparison_rows": len(comparisons),
        "executed_window_comparison_rows": sum(
            row["window_context_status"] == "executed_annulus_window_context"
            for row in comparisons
        ),
        "route_window_summary_rows": len(summaries),
        "answer_axis_rows": len(axes),
        "noncanonical_rows_with_annulus_fraction_change": sum(
            fnum(row["selected_annulus_fraction_delta_vs_canonical"]) != 0
            for row in noncanonical
        ),
        "noncanonical_rows_with_peak_height_change": sum(
            fnum(row["mean_peak_height_delta_vs_canonical"]) != 0
            for row in noncanonical
        ),
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(1 for row in sources if row["exists"] == "false"),
        "dirty_context_rows": len(dirty),
        "non_annulus_window_sweep_dirty_context_rows": sum(
            1
            for row in dirty
            if row["classification"] == "non_annulus_window_sweep_dirty_context"
        ),
        "primary_answer_frame": "candidate_envelope_annulus_window_sweep_for_selected_annulus_and_response",
        "not_primary_answer_frame": "route_winner_or_final_probability",
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    payload = {
        "summary": summary,
        "event_rows": rows,
        "window_comparison_rows": comparisons,
        "route_window_summary_rows": summaries,
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
        "window_comparisons": OUTPUT_DIR / f"{PREFIX}_WINDOW_COMPARISON_ROWS_{DATE_STAMP}.csv",
        "route_window_summary": OUTPUT_DIR / f"{PREFIX}_ROUTE_WINDOW_SUMMARY_ROWS_{DATE_STAMP}.csv",
        "answer_axis": OUTPUT_DIR / f"{PREFIX}_ANSWER_AXIS_ROWS_{DATE_STAMP}.csv",
        "validation": OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv",
        "failures": OUTPUT_DIR / f"{PREFIX}_FAILURES_{DATE_STAMP}.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv",
        "master_report": REPORT_DIR / f"600_{PREFIX}_{DATE_STAMP}.md",
    }
    write_json_atomic(outputs["status"], payload["summary"], sort_keys=True)
    write_csv_rows(outputs["event_rows"], payload["event_rows"])
    write_csv_rows(outputs["window_comparisons"], payload["window_comparison_rows"])
    write_csv_rows(outputs["route_window_summary"], payload["route_window_summary_rows"])
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
    return "\n".join(
        [
            "# NODI Sidewall Candidate Envelope Annulus Window Sweep",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Execute NODI: `{s['execute_nodi']}`",
            f"Event rows: `{s['event_rows']}`",
            f"Executed event rows: `{s['executed_event_rows']}`",
            f"Window comparison rows: `{s['window_comparison_rows']}`",
            f"Route-window summary rows: `{s['route_window_summary_rows']}`",
            f"Failed validation rows: `{s['failed_validation_rows']}`",
            "",
            "This package sweeps selected-annulus edge-norm windows while holding "
            "the 598/599 candidate envelope dimensions fixed. It separates annulus "
            "choice from width compensation and remains sparse simulation context, "
            "not route selection, final probability, yield, wet, or production "
            "evidence.",
            "",
        ]
    )


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_sidewall_candidate_envelope_annulus_window_sweep:
        print(
            "--confirm-sidewall-candidate-envelope-annulus-window-sweep is required",
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
