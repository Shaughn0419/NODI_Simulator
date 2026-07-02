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
    PRS_APPROVED_DIAMETERS_NM,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)
from tools.audits.build_nodi_sidewall_candidate_envelope_annulus_window_sweep import (  # noqa: E402
    execute_annulus_row,
)
from tools.audits.build_nodi_sidewall_distribution_weighted_response_surface import (  # noqa: E402
    WEIGHTING_MODES,
    nearest_comsol_profile_diameter,
    window_weight_lookup,
)


DATE_STAMP = "20260703"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_WIDTH_SWEEP"
ARTIFACT_ID = "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_WIDTH_SWEEP_20260703"
SYNTHESIS_VERSION = "sidewall_distribution_weighted_width_sweep_v1"
DISPOSITION_PLAN = "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_WIDTH_SWEEP_PLAN_READY"
DISPOSITION_EXECUTED = "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_WIDTH_SWEEP_EXECUTED_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_WIDTH_SWEEP_FAIL_CLOSED"
CLAIM_BOUNDARY = "distribution_weighted_width_sweep_context_not_route_selection"
PRIMARY_SIDEWALL_DEG_COMSOL = 85.0
DEFAULT_N_EVENTS = 12
DEFAULT_RANDOM_SEED = 60800
CANONICAL_WINDOW_ID = "0p5_0p8"

SOURCE_FILES = {
    "full_recompute_status_607": OUTPUT_DIR
    / "NODI_SIDEWALL_FULL_RECOMPUTE_DISTRIBUTION_WEIGHTED_LOCK_STATUS_20260703.json",
    "full_recompute_route_lock_607": OUTPUT_DIR
    / "NODI_SIDEWALL_FULL_RECOMPUTE_DISTRIBUTION_WEIGHTED_LOCK_ROUTE_LOCK_ROWS_20260703.csv",
    "bridge_route_binding_605": OUTPUT_DIR
    / "NODI_SIDEWALL_COMSOL_CROSS_SECTION_DISTRIBUTION_BRIDGE_ROUTE_DISTRIBUTION_BINDING_ROWS_20260703.csv",
    "weighted_window_rows_606": OUTPUT_DIR
    / "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_RESPONSE_SURFACE_WINDOW_WEIGHT_ROWS_20260703.csv",
    "execute_reference_600": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_candidate_envelope_annulus_window_sweep.py",
    "width_sweep_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_distribution_weighted_width_sweep.py",
    "width_sweep_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_distribution_weighted_width_sweep.py",
}

ALLOWED_USE = (
    "execute or plan a distribution-weighted width sweep around the sidewall "
    "candidate dimensions to assess dimension, annulus, and interference-response shifts"
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
    parser = argparse.ArgumentParser(
        description="Build sidewall distribution-weighted width sweep."
    )
    parser.add_argument(
        "--confirm-sidewall-distribution-weighted-width-sweep",
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


def nm_to_m(value_nm: float) -> float:
    return float(value_nm) * 1.0e-9


def m_to_nm(value_m: float) -> float:
    return float(value_m) * 1.0e9


def deterministic_sha256(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_route_id(route: str) -> tuple[int, int, int]:
    lambda_text, width_text, depth_text = str(route).split("/")
    return int(lambda_text), int(width_text.removeprefix("W")), int(
        depth_text.removeprefix("D")
    )


def route_id(lambda_nm: int, width_nm: int, depth_nm: int) -> str:
    return f"{int(lambda_nm)}/W{int(width_nm)}/D{int(depth_nm)}"


def route_case_id(route: str) -> str:
    return str(route).replace("/", "_")


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
    output_report = f"reports/608_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_distribution_weighted_width_sweep.py",
        "tests/test_nodi_sidewall_distribution_weighted_width_sweep.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "distribution_weighted_width_sweep_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "distribution_weighted_width_sweep_output"
            release_decision = "included_or_rewritten_by_width_sweep_builder"
        else:
            classification = "non_distribution_weighted_width_sweep_dirty_context"
            release_decision = "ignored_for_distribution_weighted_width_sweep"
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


def route_binding_rows() -> list[dict[str, str]]:
    return load_rows("bridge_route_binding_605")


def width_grid_for_route(source_w_nm: int, candidate_w_nm: int) -> list[int]:
    values = [
        candidate_w_nm - 40,
        candidate_w_nm - 20,
        candidate_w_nm,
        candidate_w_nm + 20,
        candidate_w_nm + 40,
    ]
    return sorted({max(int(source_w_nm), int(round(value))) for value in values})


def width_context(source_w_nm: int, candidate_w_nm: int, width_nm: int) -> str:
    if width_nm == source_w_nm:
        return "source_width_under_trapezoid_sidewall"
    if width_nm == candidate_w_nm:
        return "current_candidate_envelope_width"
    if width_nm < candidate_w_nm:
        return "below_current_candidate_width"
    return "above_current_candidate_width"


def plan_rows(
    *,
    n_events: int = DEFAULT_N_EVENTS,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    diameters = sorted(int(value) for value in PRS_APPROVED_DIAMETERS_NM)
    taper = comsol_sidewall_deg_to_nodi_taper_deg(PRIMARY_SIDEWALL_DEG_COMSOL)
    for route_index, route in enumerate(route_binding_rows()):
        source_route = route["source_route_id_nodi"]
        candidate_route = route["candidate_envelope_route_id_nodi"]
        lambda_nm, source_w_nm, depth_nm = parse_route_id(source_route)
        candidate_lambda_nm, candidate_w_nm, candidate_depth_nm = parse_route_id(
            candidate_route
        )
        if lambda_nm != candidate_lambda_nm or depth_nm != candidate_depth_nm:
            raise ValueError(f"candidate route changes lambda/depth: {source_route} -> {candidate_route}")
        windows = json.loads(route["followup_window_set_json"])
        for width_index, width_nm in enumerate(width_grid_for_route(source_w_nm, candidate_w_nm)):
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
                        f"WIDTH-{route_case_id(source_route)}-to-{route_case_id(sweep_route)}-"
                        f"A{window_id}-P{diameter_nm}-N{n_events}-TH85"
                    )
                    rows.append(
                        {
                            **common_guard_fields(row_id),
                            "source_artifacts_json": json.dumps(
                                [
                                    "605_distribution_bridge",
                                    "606_distribution_weighted_response_surface",
                                    "607_full_recompute_distribution_weighted_lock",
                                    "execute_annulus_row_reused",
                                ],
                                sort_keys=True,
                            ),
                            "shard_case_id": row_id,
                            "source_route_id_nodi": source_route,
                            "candidate_envelope_route_id_nodi": candidate_route,
                            "width_sweep_route_id_nodi": sweep_route,
                            "route_id_nodi": sweep_route,
                            "route_id_role": "width_sweep_context_not_route_selection",
                            "lambda_nm": lambda_nm,
                            "source_W_nominal_nm": source_w_nm,
                            "candidate_envelope_W_top_nm": candidate_w_nm,
                            "W_nominal_nm": width_nm,
                            "W_top_nm": width_nm,
                            "W_top_semantics": "width_sweep_runtime_top_aperture_surrogate",
                            "width_sweep_delta_vs_candidate_nm": width_nm - candidate_w_nm,
                            "width_sweep_delta_vs_source_nm": width_nm - source_w_nm,
                            "width_context": width_context(source_w_nm, candidate_w_nm, width_nm),
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
                            "execution_status": "planned_width_sweep_not_executed",
                        }
                    )
    return rows


def execute_width_sweep_rows(plan: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    executed: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for row in plan:
        try:
            result = execute_annulus_row(row)
            result["execution_status"] = "executed_width_sweep_nodi"
            for key in (
                "candidate_envelope_W_top_nm",
                "width_sweep_delta_vs_candidate_nm",
                "width_sweep_delta_vs_source_nm",
                "width_context",
                "width_sweep_route_id_nodi",
            ):
                result[key] = row[key]
            executed.append(result)
        except Exception as exc:  # pragma: no cover - integration failure path
            failed = dict(row)
            failed["execution_status"] = "failed_width_sweep_nodi"
            failed["failure_type"] = type(exc).__name__
            failed["failure_message"] = str(exc)
            executed.append(failed)
            failures.append(failed)
    return executed, failures


def weighted_event_rows(event_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    weights = window_weight_lookup()
    rows: list[dict[str, Any]] = []
    for event in event_rows:
        event_diameter = fnum(event["diameter_nm"])
        source_diameter = nearest_comsol_profile_diameter(event_diameter)
        for mode in WEIGHTING_MODES:
            weight = weights[(source_diameter, event["annulus_window_id"], mode)]
            peak = fnum(event.get("mean_peak_height"))
            snr = fnum(event.get("mean_local_snr"))
            selected_fraction = fnum(event.get("selected_annulus_fraction"))
            rows.append(
                {
                    **common_guard_fields(f"WEIGHTED-{event['row_id']}-{mode}"),
                    "source_event_row_id": event["row_id"],
                    "source_route_id_nodi": event["source_route_id_nodi"],
                    "candidate_envelope_route_id_nodi": event[
                        "candidate_envelope_route_id_nodi"
                    ],
                    "width_sweep_route_id_nodi": event["width_sweep_route_id_nodi"],
                    "route_id_role": "width_sweep_weighted_context_not_selection",
                    "W_top_nm": event["W_top_nm"],
                    "candidate_envelope_W_top_nm": event["candidate_envelope_W_top_nm"],
                    "width_sweep_delta_vs_candidate_nm": event[
                        "width_sweep_delta_vs_candidate_nm"
                    ],
                    "width_context": event["width_context"],
                    "annulus_window_id": event["annulus_window_id"],
                    "diameter_nm": event["diameter_nm"],
                    "n_events_requested": event.get("n_events_requested", ""),
                    "n_events_observed": event.get("n_events_observed", ""),
                    "width_sweep_execution_status": event["execution_status"],
                    "weighting_mode": mode,
                    "comsol_weight_profile_diameter_nm": source_diameter,
                    "window_probability_mass_surrogate": weight,
                    "selected_annulus_fraction": selected_fraction,
                    "weighted_selected_annulus_fraction_surrogate": (
                        selected_fraction * weight
                    ),
                    "mean_peak_height": peak,
                    "mean_local_snr": snr,
                    "weighted_peak_height_contribution": peak * weight,
                    "weighted_local_snr_contribution": snr * weight,
                    "weight_claim_level": (
                        "uniform_surrogate"
                        if mode == "uniform_edge_mass"
                        else "comsol_transport_bin_surrogate_not_exact_pxu"
                    ),
                }
            )
    return rows


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def width_summary_rows(weighted_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in weighted_rows:
        grouped[(row["source_route_id_nodi"], inum(row["W_top_nm"]), row["weighting_mode"])].append(row)

    rows: list[dict[str, Any]] = []
    for (source_route, width_nm, mode), group in sorted(grouped.items()):
        by_window: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in group:
            by_window[row["annulus_window_id"]].append(row)
        summaries = []
        for window_id, window_rows in sorted(by_window.items()):
            summaries.append(
                {
                    "window_id": window_id,
                    "mass": mean(
                        [fnum(row["window_probability_mass_surrogate"]) for row in window_rows]
                    ),
                    "peak_contribution": mean(
                        [fnum(row["weighted_peak_height_contribution"]) for row in window_rows]
                    ),
                    "snr_contribution": mean(
                        [fnum(row["weighted_local_snr_contribution"]) for row in window_rows]
                    ),
                    "selected_annulus_fraction_contribution": mean(
                        [
                            fnum(row["weighted_selected_annulus_fraction_surrogate"])
                            for row in window_rows
                        ]
                    ),
                }
            )
        canonical = next(
            (item for item in summaries if item["window_id"] == CANONICAL_WINDOW_ID),
            None,
        )
        leading_mass = max(summaries, key=lambda item: item["mass"])
        leading_peak = max(summaries, key=lambda item: item["peak_contribution"])
        leading_snr = max(summaries, key=lambda item: item["snr_contribution"])
        first = group[0]
        rows.append(
            {
                **common_guard_fields(
                    f"WIDTH-SUM-{source_route.replace('/', '_')}-W{width_nm}-{mode}"
                ),
                "source_route_id_nodi": source_route,
                "candidate_envelope_route_id_nodi": first[
                    "candidate_envelope_route_id_nodi"
                ],
                "width_sweep_route_id_nodi": first["width_sweep_route_id_nodi"],
                "route_id_role": "width_sweep_summary_context_not_selection",
                "W_top_nm": width_nm,
                "candidate_envelope_W_top_nm": first["candidate_envelope_W_top_nm"],
                "width_sweep_delta_vs_candidate_nm": first[
                    "width_sweep_delta_vs_candidate_nm"
                ],
                "width_context": first["width_context"],
                "weighting_mode": mode,
                "weighted_event_rows": len(group),
                "canonical_window_present": canonical is not None,
                "leading_mass_window_context": leading_mass["window_id"],
                "leading_peak_contribution_window_context": leading_peak["window_id"],
                "leading_snr_contribution_window_context": leading_snr["window_id"],
                "mean_weighted_peak_contribution": mean(
                    [item["peak_contribution"] for item in summaries]
                ),
                "mean_weighted_local_snr_contribution": mean(
                    [item["snr_contribution"] for item in summaries]
                ),
                "mean_weighted_selected_annulus_fraction": mean(
                    [item["selected_annulus_fraction_contribution"] for item in summaries]
                ),
                "window_summary_json": json.dumps(summaries, ensure_ascii=True),
            }
        )
    return rows


def dimension_context_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in summary_rows:
        grouped[(row["source_route_id_nodi"], row["weighting_mode"])].append(row)

    rows: list[dict[str, Any]] = []
    for (source_route, mode), group in sorted(grouped.items()):
        leading_peak = max(group, key=lambda row: fnum(row["mean_weighted_peak_contribution"]))
        leading_snr = max(group, key=lambda row: fnum(row["mean_weighted_local_snr_contribution"]))
        leading_annulus = max(
            group, key=lambda row: fnum(row["mean_weighted_selected_annulus_fraction"])
        )
        candidate_width = inum(group[0]["candidate_envelope_W_top_nm"])
        peak_width = inum(leading_peak["W_top_nm"])
        snr_width = inum(leading_snr["W_top_nm"])
        annulus_width = inum(leading_annulus["W_top_nm"])
        if peak_width > candidate_width or snr_width > candidate_width:
            dimension_context = "wider_width_context_after_distribution_weighted_sweep"
        elif peak_width == candidate_width and snr_width == candidate_width:
            dimension_context = "candidate_width_context_retained_after_distribution_weighted_sweep"
        elif peak_width < candidate_width and snr_width < candidate_width:
            dimension_context = "narrower_width_context_possible_after_distribution_weighted_sweep"
        else:
            dimension_context = "split_width_context_after_distribution_weighted_sweep"
        rows.append(
            {
                **common_guard_fields(f"DIM-CTX-{source_route.replace('/', '_')}-{mode}"),
                "source_route_id_nodi": source_route,
                "weighting_mode": mode,
                "route_id_role": "dimension_context_not_route_selection",
                "candidate_envelope_W_top_nm": candidate_width,
                "leading_peak_width_context_nm": peak_width,
                "leading_snr_width_context_nm": snr_width,
                "leading_annulus_fraction_width_context_nm": annulus_width,
                "peak_width_delta_vs_candidate_nm": peak_width - candidate_width,
                "snr_width_delta_vs_candidate_nm": snr_width - candidate_width,
                "annulus_width_delta_vs_candidate_nm": annulus_width - candidate_width,
                "dimension_context_after_width_sweep": dimension_context,
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
    wider_count = sum(
        row["dimension_context_after_width_sweep"]
        == "wider_width_context_after_distribution_weighted_sweep"
        for row in comsol_rows
    )
    candidate_retained_count = sum(
        row["dimension_context_after_width_sweep"]
        == "candidate_width_context_retained_after_distribution_weighted_sweep"
        for row in comsol_rows
    )
    mode_text = "executed" if execute_nodi else "planned"
    return [
        {
            **common_guard_fields("QUESTION-608-DIMENSION"),
            "question_id": "size_recommendation_delta_after_sidewall",
            "answer_context": (
                f"width sweep {mode_text}; distribution-weighted dimension context "
                "is now evaluated around source and candidate widths"
            ),
            "comsol_weighted_rows_with_wider_width_context": wider_count,
            "comsol_weighted_rows_with_candidate_width_retained": candidate_retained_count,
            "next_action": "609_dimension_context_lock_or_refined_width_sweep",
        },
        {
            **common_guard_fields("QUESTION-608-ANNULUS"),
            "question_id": "selected_annulus_range_delta_after_sidewall",
            "answer_context": (
                "annulus context is evaluated across width grid with uniform and COMSOL edge-bin weights"
            ),
            "next_action": "609_lock_annulus_context_by_width_and_weight_mode",
        },
        {
            **common_guard_fields("QUESTION-608-INTERFERENCE"),
            "question_id": "interference_response_delta_after_sidewall",
            "answer_context": (
                "peak/local-SNR contribution is evaluated across width grid with distribution weights"
            ),
            "next_action": "609_lock_interference_context_by_width_and_weight_mode",
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

    plan = payload["width_sweep_event_rows"]
    weighted = payload["weighted_width_event_rows"]
    summaries = payload["width_summary_rows"]
    dimensions = payload["dimension_context_rows"]
    execute_nodi = payload["execute_nodi"]
    route_rows = route_binding_rows()
    route_window_counts = {
        row["source_route_id_nodi"]: len(json.loads(row["followup_window_set_json"]))
        for row in route_rows
    }
    expected_event_rows = sum(5 * count * len(PRS_APPROVED_DIAMETERS_NM) for count in route_window_counts.values())
    executed_rows = sum(
        row["execution_status"] == "executed_width_sweep_nodi" for row in plan
    )

    add(
        "width_sweep_covers_candidate_and_two_sided_neighbors",
        len(plan) == expected_event_rows,
        f"width_sweep_event_rows={len(plan)} expected={expected_event_rows}",
    )
    add(
        "each_route_has_five_widths",
        all(
            len({inum(row["W_top_nm"]) for row in plan if row["source_route_id_nodi"] == route["source_route_id_nodi"]})
            == 5
            for route in route_rows
        ),
        "candidate-40, candidate-20, candidate, candidate+20, candidate+40 after source floor",
    )
    add(
        "execution_status_matches_mode",
        (executed_rows == expected_event_rows if execute_nodi else executed_rows == 0),
        f"execute_nodi={execute_nodi}; executed_rows={executed_rows}",
    )
    add(
        "weighted_rows_cover_three_modes",
        len(weighted) == len(plan) * len(WEIGHTING_MODES)
        and {row["weighting_mode"] for row in weighted} == set(WEIGHTING_MODES),
        f"weighted_width_event_rows={len(weighted)}",
    )
    add(
        "summary_rows_cover_route_width_weight_grid",
        len(summaries) == 6 * 5 * len(WEIGHTING_MODES),
        f"width_summary_rows={len(summaries)}",
    )
    add(
        "dimension_rows_cover_six_routes_times_three_modes",
        len(dimensions) == 6 * len(WEIGHTING_MODES),
        f"dimension_context_rows={len(dimensions)}",
    )
    add(
        "v4_assumption_hash_bound",
        all(
            row["comsol_v4_assumption_set_sha256"] == COMSOL_V4_ASSUMPTION_SET_SHA256
            for table in (plan, weighted, summaries, dimensions)
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
        "width_sweep_event_rows",
        "weighted_width_event_rows",
        "width_summary_rows",
        "dimension_context_rows",
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
    dimensions = dimension_context_rows(summaries)
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
            "width_sweep_event_rows": len(event_rows),
            "width_sweep_executed_rows": sum(
                row["execution_status"] == "executed_width_sweep_nodi"
                for row in event_rows
            ),
            "width_sweep_failures": len(failures),
            "weighted_width_event_rows": len(weighted),
            "width_summary_rows": len(summaries),
            "dimension_context_rows": len(dimensions),
            "question_rows": len(q_rows),
            "exact_pxu_probability_grid_available_now": False,
            "next_executable_block": "609_dimension_annulus_interference_context_lock",
        },
        "width_sweep_event_rows": event_rows,
        "weighted_width_event_rows": weighted,
        "width_summary_rows": summaries,
        "dimension_context_rows": dimensions,
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
    failures: list[str] = []
    for row in payload["validation_rows"]:
        if row["status"] != "pass":
            failures.append(f"{row['check_id']}: {row['detail']}")
    return failures


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    wider_rows = sum(
        row["dimension_context_after_width_sweep"]
        == "wider_width_context_after_distribution_weighted_sweep"
        for row in payload["dimension_context_rows"]
        if row["weighting_mode"] != "uniform_edge_mass"
    )
    lines = [
        "# NODI sidewall distribution-weighted width sweep",
        "",
        "## Mainline",
        "",
        (
            "This artifact sweeps top width around the current sidewall candidate "
            "dimensions, executes or plans NODI rows, and applies uniform plus COMSOL "
            "transport-bin weights to dimension, annulus, and interference-response context."
        ),
        "",
        "## Counts",
        "",
        f"- execution mode: {'executed' if payload['execute_nodi'] else 'plan-only'}",
        f"- width sweep event rows: {summary['width_sweep_event_rows']}",
        f"- executed rows: {summary['width_sweep_executed_rows']}",
        f"- weighted event rows: {summary['weighted_width_event_rows']}",
        f"- dimension context rows: {summary['dimension_context_rows']}",
        f"- COMSOL-weighted rows with wider width context: {wider_rows}",
        f"- failed validation rows: {summary['failed_validation_rows']}",
        "",
        "## Next",
        "",
        (
            "609 should lock the dimension/annulus/interference context from this "
            "width sweep, then decide whether another narrower refinement around the "
            "leading width contexts is worthwhile."
        ),
        "",
    ]
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json"
    report_json_path = OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json"
    event_path = OUTPUT_DIR / f"{PREFIX}_WIDTH_SWEEP_EVENT_ROWS_{DATE_STAMP}.csv"
    weighted_path = OUTPUT_DIR / f"{PREFIX}_WEIGHTED_WIDTH_EVENT_ROWS_{DATE_STAMP}.csv"
    summary_path = OUTPUT_DIR / f"{PREFIX}_WIDTH_SUMMARY_ROWS_{DATE_STAMP}.csv"
    dimension_path = OUTPUT_DIR / f"{PREFIX}_DIMENSION_CONTEXT_ROWS_{DATE_STAMP}.csv"
    question_path = OUTPUT_DIR / f"{PREFIX}_QUESTION_ROWS_{DATE_STAMP}.csv"
    failure_path = OUTPUT_DIR / f"{PREFIX}_FAILURE_ROWS_{DATE_STAMP}.csv"
    validation_path = OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv"
    source_lock_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv"
    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv"
    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv"
    report_md_path = REPORT_DIR / f"608_{PREFIX}_{DATE_STAMP}.md"

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
    write_csv_rows(event_path, payload["width_sweep_event_rows"])
    write_csv_rows(weighted_path, payload["weighted_width_event_rows"])
    write_csv_rows(summary_path, payload["width_summary_rows"])
    write_csv_rows(dimension_path, payload["dimension_context_rows"])
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
    if not args.confirm_sidewall_distribution_weighted_width_sweep:
        print(
            "--confirm-sidewall-distribution-weighted-width-sweep is required",
            file=sys.stderr,
        )
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
