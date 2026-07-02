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


DATE_STAMP = "20260703"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_RESPONSE_SURFACE"
ARTIFACT_ID = "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_RESPONSE_SURFACE_20260703"
SYNTHESIS_VERSION = "sidewall_distribution_weighted_response_surface_v1"
DISPOSITION = "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_RESPONSE_SURFACE_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_RESPONSE_SURFACE_FAIL_CLOSED"
CLAIM_BOUNDARY = "distribution_weighted_response_surface_surrogate_not_final_pxu"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

COMSOL_PROJECT_ROOT = (
    PROJECT_ROOT.parent / "comsol test" / "comsol_ev_pbs_bonded_cross_junction"
)
COMSOL_DWG = COMSOL_PROJECT_ROOT / "full_chip" / "dwg_analysis"
COMSOL_TRANSPORT_220 = COMSOL_DWG / (
    "ev_pbs_v4_normal_transport_frozenflow_smoke_20260630/"
    "stage119_sw085p0_d1p2_biasp000p0nm_ch70_d220nm/"
    "EV_PBS_V4_NORMAL_NANOCHANNEL_TRANSPORT_FROZENFLOW_SMOKE_20260630_"
    "RESULTS_stage119_sw085p0_d1p2_biasp000p0nm_ch70_d220nm.csv"
)
COMSOL_TRANSPORT_300 = COMSOL_DWG / (
    "ev_pbs_v4_normal_transport_frozenflow_smoke_20260630/"
    "stage119_sw085p0_d1p2_biasp000p0nm_ch70_d300nm/"
    "EV_PBS_V4_NORMAL_NANOCHANNEL_TRANSPORT_FROZENFLOW_SMOKE_20260630_"
    "RESULTS_stage119_sw085p0_d1p2_biasp000p0nm_ch70_d300nm.csv"
)

SOURCE_FILES = {
    "bridge_status_605": OUTPUT_DIR
    / "NODI_SIDEWALL_COMSOL_CROSS_SECTION_DISTRIBUTION_BRIDGE_STATUS_20260703.json",
    "bridge_recompute_queue_605": OUTPUT_DIR
    / "NODI_SIDEWALL_COMSOL_CROSS_SECTION_DISTRIBUTION_BRIDGE_RECOMPUTE_QUEUE_ROWS_20260703.csv",
    "bridge_route_binding_605": OUTPUT_DIR
    / "NODI_SIDEWALL_COMSOL_CROSS_SECTION_DISTRIBUTION_BRIDGE_ROUTE_DISTRIBUTION_BINDING_ROWS_20260703.csv",
    "bridge_inventory_605": OUTPUT_DIR
    / "NODI_SIDEWALL_COMSOL_CROSS_SECTION_DISTRIBUTION_BRIDGE_COMSOL_SOURCE_INVENTORY_20260703.csv",
    "followup_event_rows_603": OUTPUT_DIR
    / "NODI_SIDEWALL_FOLLOWUP_WINDOW_HIGHER_EVENT_SWEEP_EVENT_ROWS_20260703.csv",
    "followup_summary_603": OUTPUT_DIR
    / "NODI_SIDEWALL_FOLLOWUP_WINDOW_HIGHER_EVENT_SWEEP_ROUTE_WINDOW_SUMMARY_ROWS_20260703.csv",
    "comsol_v4_transport_frozenflow_220nm_context": COMSOL_TRANSPORT_220,
    "comsol_v4_transport_frozenflow_300nm_context": COMSOL_TRANSPORT_300,
    "weighted_response_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_distribution_weighted_response_surface.py",
    "weighted_response_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_distribution_weighted_response_surface.py",
}

ALLOWED_USE = (
    "compute a COMSOL-v4 transport-bin weighted surrogate response surface for "
    "the sidewall dimension, selected-annulus, and interference-response mainline"
)
BLOCKED_USE = (
    "exact P(x,u) probability claim, route winner, scalar score, final yield, "
    "final detection probability, wet experimental claim, q_ch weighting, true "
    "W_eff, or production runtime ingestion"
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
WEIGHTING_MODES = (
    "uniform_edge_mass",
    "comsol_outlet_flux_fraction",
    "comsol_residence_fraction",
)
CANONICAL_WINDOW_ID = "0p5_0p8"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build NODI sidewall distribution-weighted response surface."
    )
    parser.add_argument(
        "--confirm-sidewall-distribution-weighted-response-surface",
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
    output_report = f"reports/606_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_distribution_weighted_response_surface.py",
        "tests/test_nodi_sidewall_distribution_weighted_response_surface.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "distribution_weighted_response_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "distribution_weighted_response_output"
            release_decision = "included_or_rewritten_by_weighted_response_builder"
        else:
            classification = "non_distribution_weighted_response_dirty_context"
            release_decision = "ignored_for_distribution_weighted_response"
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


def parse_window_id(window_id: str) -> tuple[float, float]:
    left, right = window_id.replace("p", ".").split("_")
    return float(left), float(right)


def overlap_fraction(
    window_min: float, window_max: float, bin_min: float, bin_max: float
) -> float:
    overlap = max(0.0, min(window_max, bin_max) - max(window_min, bin_min))
    width = max(bin_max - bin_min, 0.0)
    return overlap / width if width > 0 else 0.0


def transport_bin_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sources = [
        (220, COMSOL_TRANSPORT_220),
        (300, COMSOL_TRANSPORT_300),
    ]
    for diameter_nm, path in sources:
        for row in read_csv_rows(path):
            if row.get("row_scope") != "edge_normalized_transport_bin_descriptor":
                continue
            rows.append(
                {
                    **common_guard_fields(
                        f"EDGE-BIN-D{diameter_nm}-B{row.get('bin_idx')}"
                    ),
                    "source_particle_diameter_nm": diameter_nm,
                    "bin_idx": row.get("bin_idx"),
                    "edge_norm_min": fnum(row.get("edge_norm_min")),
                    "edge_norm_max": fnum(row.get("edge_norm_max")),
                    "uniform_edge_mass": fnum(row.get("edge_norm_max"))
                    - fnum(row.get("edge_norm_min")),
                    "comsol_outlet_flux_fraction": fnum(
                        row.get("outlet_flux_fraction")
                    ),
                    "comsol_residence_fraction": fnum(row.get("residence_fraction")),
                    "source_descriptor_status": "edge4_transport_descriptor_not_exact_pxu",
                    "edge4_exact_annulus_mapping_status": (
                        "not_exact_0p5_0p8_annulus_mapping"
                    ),
                    "edge20_or_0p8_split_required_for_exact_annulus": True,
                    "probability_grid_available": False,
                }
            )
    return rows


def window_weight_rows() -> list[dict[str, Any]]:
    event_rows = load_rows("followup_event_rows_603")
    windows = sorted({row["annulus_window_id"] for row in event_rows})
    bins_by_diameter: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in transport_bin_rows():
        bins_by_diameter[int(row["source_particle_diameter_nm"])].append(row)

    rows: list[dict[str, Any]] = []
    for diameter_nm, bins in sorted(bins_by_diameter.items()):
        for window_id in windows:
            window_min, window_max = parse_window_id(window_id)
            for mode in WEIGHTING_MODES:
                if mode == "uniform_edge_mass":
                    mass = window_max - window_min
                    source = "analytic_uniform_edge_mass"
                else:
                    mass = sum(
                        overlap_fraction(
                            window_min,
                            window_max,
                            fnum(bin_row["edge_norm_min"]),
                            fnum(bin_row["edge_norm_max"]),
                        )
                        * fnum(bin_row[mode])
                        for bin_row in bins
                    )
                    source = "comsol_v4_edge4_transport_descriptor"
                rows.append(
                    {
                        **common_guard_fields(
                            f"WINDOW-WEIGHT-D{diameter_nm}-{window_id}-{mode}"
                        ),
                        "source_particle_diameter_nm": diameter_nm,
                        "annulus_window_id": window_id,
                        "window_edge_norm_min": window_min,
                        "window_edge_norm_max": window_max,
                        "weighting_mode": mode,
                        "window_probability_mass_surrogate": mass,
                        "weight_source": source,
                        "weight_claim_level": (
                            "uniform_surrogate"
                            if mode == "uniform_edge_mass"
                            else "comsol_transport_bin_surrogate_not_exact_pxu"
                        ),
                        "edge4_exact_annulus_mapping_status": (
                            "not_exact_0p5_0p8_annulus_mapping"
                            if mode != "uniform_edge_mass"
                            else "not_comsol_edge4_source"
                        ),
                        "probability_grid_available": False,
                    }
                )
    return rows


def nearest_comsol_profile_diameter(diameter_nm: float) -> int:
    return 300 if diameter_nm > 220 else 220


def event_lookup_rows() -> list[dict[str, str]]:
    return load_rows("followup_event_rows_603")


def window_weight_lookup() -> dict[tuple[int, str, str], float]:
    return {
        (
            int(row["source_particle_diameter_nm"]),
            row["annulus_window_id"],
            row["weighting_mode"],
        ): fnum(row["window_probability_mass_surrogate"])
        for row in window_weight_rows()
    }


def weighted_window_response_rows() -> list[dict[str, Any]]:
    weights = window_weight_lookup()
    rows: list[dict[str, Any]] = []
    for event in event_lookup_rows():
        event_diameter = fnum(event["diameter_nm"])
        source_diameter = nearest_comsol_profile_diameter(event_diameter)
        for mode in WEIGHTING_MODES:
            weight = weights[(source_diameter, event["annulus_window_id"], mode)]
            peak = fnum(event["mean_peak_height"])
            snr = fnum(event["mean_local_snr"])
            selected_fraction = fnum(event["selected_annulus_fraction"])
            rows.append(
                {
                    **common_guard_fields(
                        f"WEIGHTED-{event['row_id']}-{mode}"
                    ),
                    "source_event_row_id": event["row_id"],
                    "source_route_id_nodi": event["source_route_id_nodi"],
                    "candidate_envelope_route_id_nodi": event[
                        "candidate_envelope_route_id_nodi"
                    ],
                    "route_id_role": "weighted_response_context_not_route_selection",
                    "annulus_window_id": event["annulus_window_id"],
                    "selected_annulus_edge_norm_min": event[
                        "selected_annulus_edge_norm_min"
                    ],
                    "selected_annulus_edge_norm_max": event[
                        "selected_annulus_edge_norm_max"
                    ],
                    "diameter_nm": event["diameter_nm"],
                    "comsol_weight_profile_diameter_nm": source_diameter,
                    "weighting_mode": mode,
                    "window_probability_mass_surrogate": weight,
                    "source_selected_annulus_fraction_nodi": selected_fraction,
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
                    "probability_grid_available": False,
                }
            )
    return rows


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def route_weighted_synthesis_rows() -> list[dict[str, Any]]:
    rows = weighted_window_response_rows()
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["source_route_id_nodi"], row["weighting_mode"])].append(row)

    output: list[dict[str, Any]] = []
    for (route_id, mode), group in sorted(grouped.items()):
        by_window: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in group:
            by_window[row["annulus_window_id"]].append(row)
        window_summaries = []
        for window_id, window_rows in sorted(by_window.items()):
            window_summaries.append(
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
            (item for item in window_summaries if item["window_id"] == CANONICAL_WINDOW_ID),
            None,
        )
        leading_mass = max(window_summaries, key=lambda item: item["mass"])
        leading_peak = max(window_summaries, key=lambda item: item["peak_contribution"])
        leading_snr = max(window_summaries, key=lambda item: item["snr_contribution"])
        canonical_mass = canonical["mass"] if canonical else 0.0
        canonical_peak = canonical["peak_contribution"] if canonical else 0.0
        canonical_snr = canonical["snr_contribution"] if canonical else 0.0
        output.append(
            {
                **common_guard_fields(f"ROUTE-WEIGHTED-{route_id.replace('/', '_')}-{mode}"),
                "source_route_id_nodi": route_id,
                "weighting_mode": mode,
                "route_id_role": "distribution_weighted_context_not_route_selection",
                "windows_evaluated_json": json.dumps(
                    [item["window_id"] for item in window_summaries], ensure_ascii=True
                ),
                "canonical_window_id": CANONICAL_WINDOW_ID,
                "canonical_window_present": canonical is not None,
                "canonical_window_mass_surrogate": canonical_mass,
                "leading_mass_window_context": leading_mass["window_id"],
                "leading_mass_minus_canonical": leading_mass["mass"] - canonical_mass,
                "leading_peak_contribution_window_context": leading_peak["window_id"],
                "leading_peak_contribution_minus_canonical": (
                    leading_peak["peak_contribution"] - canonical_peak
                ),
                "leading_snr_contribution_window_context": leading_snr["window_id"],
                "leading_snr_contribution_minus_canonical": (
                    leading_snr["snr_contribution"] - canonical_snr
                ),
                "annulus_context_after_weighting": (
                    "canonical_window_retained"
                    if leading_mass["window_id"] == CANONICAL_WINDOW_ID
                    else "weighted_mass_context_shifts_from_canonical"
                ),
                "interference_context_after_weighting": (
                    "noncanonical_response_contribution_exceeds_canonical"
                    if leading_peak["window_id"] != CANONICAL_WINDOW_ID
                    or leading_snr["window_id"] != CANONICAL_WINDOW_ID
                    else "canonical_response_contribution_retained"
                ),
                "dimension_context_after_weighting": (
                    "dimension_envelope_not_recomputed_in_606_full_nodi_recompute_required"
                ),
                "window_summary_json": json.dumps(window_summaries, ensure_ascii=True),
            }
        )
    return output


def question_result_rows(route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    comsol_rows = [
        row for row in route_rows if row["weighting_mode"] != "uniform_edge_mass"
    ]
    annulus_shift_count = sum(
        row["annulus_context_after_weighting"]
        == "weighted_mass_context_shifts_from_canonical"
        for row in comsol_rows
    )
    response_shift_count = sum(
        row["interference_context_after_weighting"]
        == "noncanonical_response_contribution_exceeds_canonical"
        for row in comsol_rows
    )
    return [
        {
            **common_guard_fields("QUESTION-606-DIMENSION"),
            "question_id": "size_recommendation_delta_after_sidewall",
            "answer_context": (
                "604 dimension envelope changed; 606 does not finalize dimensions "
                "because distribution weighting must feed a full NODI recompute"
            ),
            "routes_requiring_full_nodi_recompute": len(
                {row["source_route_id_nodi"] for row in route_rows}
            ),
            "next_action": "607_full_nodi_recompute_over_distribution_weighted_queue",
        },
        {
            **common_guard_fields("QUESTION-606-ANNULUS"),
            "question_id": "selected_annulus_range_delta_after_sidewall",
            "answer_context": (
                "COMSOL transport-bin weighting shifts annulus mass context away "
                "from canonical 0.5-0.8 where edge4 weights favor inner bins"
            ),
            "comsol_weighted_route_mode_rows_with_annulus_shift": annulus_shift_count,
            "exact_pxu_required_for_final_annulus_probability": True,
            "next_action": "607_recompute_annulus_occupancy_and_response_with_weight_modes",
        },
        {
            **common_guard_fields("QUESTION-606-INTERFERENCE"),
            "question_id": "interference_response_delta_after_sidewall",
            "answer_context": (
                "weighted peak/local-SNR contribution changes under COMSOL "
                "transport-bin surrogate and must be carried into full NODI recompute"
            ),
            "comsol_weighted_route_mode_rows_with_response_shift": response_shift_count,
            "exact_pxu_required_for_final_interference_integral": True,
            "next_action": "607_full_nodi_recompute_then_compare_weighted_response",
        },
    ]


def next_action_rows(route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    routes = sorted({row["source_route_id_nodi"] for row in route_rows})
    rows: list[dict[str, Any]] = []
    for route_id in routes:
        rows.append(
            {
                **common_guard_fields(f"NEXT-607-{route_id.replace('/', '_')}"),
                "source_route_id_nodi": route_id,
                "route_id_role": "next_recompute_context_not_route_selection",
                "next_action_context": (
                    "run full NODI recompute preserving rectangle baseline and "
                    "trapezoid sidewall branch, with uniform and COMSOL transport-bin weights"
                ),
                "required_distribution_bases_json": json.dumps(
                    [
                        "rectangle_uniform_accessible_baseline_v1",
                        "trapezoid_uniform_accessible_surrogate_v1",
                        "trapezoid_comsol_v4_transport_bin_reweighted_surrogate_v1",
                    ],
                    ensure_ascii=True,
                ),
                "pending_exact_pxu_branch": (
                    "comsol_v4_cross_section_probability_grid_exact_required_v1"
                ),
            }
        )
    return rows


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

    edge_rows = payload["transport_bin_rows"]
    window_rows = payload["window_weight_rows"]
    weighted_rows = payload["weighted_window_response_rows"]
    route_rows = payload["route_weighted_synthesis_rows"]
    question_rows = payload["question_result_rows"]

    add(
        "edge4_transport_bins_available_for_220_and_300",
        len(edge_rows) == 8
        and {int(row["source_particle_diameter_nm"]) for row in edge_rows}
        == {220, 300},
        f"edge_bin_rows={len(edge_rows)}",
    )
    add(
        "edge4_not_promoted_to_exact_pxu",
        all(row["probability_grid_available"] is False for row in edge_rows),
        "COMSOL edge bins remain transport descriptors",
    )
    add(
        "window_weights_cover_three_modes",
        {row["weighting_mode"] for row in window_rows} == set(WEIGHTING_MODES),
        "uniform, outlet-flux, and residence weighting modes present",
    )
    add(
        "weighted_response_rows_match_event_rows_times_modes",
        len(weighted_rows) == 208 * len(WEIGHTING_MODES),
        f"weighted_window_response_rows={len(weighted_rows)}",
    )
    add(
        "route_synthesis_covers_six_routes_times_three_modes",
        len(route_rows) == 6 * len(WEIGHTING_MODES),
        f"route_weighted_synthesis_rows={len(route_rows)}",
    )
    add(
        "question_rows_cover_three_user_questions",
        {
            row["question_id"] for row in question_rows
        }
        == {
            "size_recommendation_delta_after_sidewall",
            "selected_annulus_range_delta_after_sidewall",
            "interference_response_delta_after_sidewall",
        },
        "dimension, annulus, and interference-response questions retained",
    )
    add(
        "comsol_weighting_shifts_annulus_context_for_at_least_one_route",
        any(
            row["weighting_mode"] != "uniform_edge_mass"
            and row["annulus_context_after_weighting"]
            == "weighted_mass_context_shifts_from_canonical"
            for row in route_rows
        ),
        "coarse COMSOL edge weighting is directionally active",
    )
    add(
        "v4_assumption_hash_bound",
        all(
            row["comsol_v4_assumption_set_sha256"] == COMSOL_V4_ASSUMPTION_SET_SHA256
            for table in (
                edge_rows,
                window_rows,
                weighted_rows,
                route_rows,
                question_rows,
            )
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
        "transport_bin_rows",
        "window_weight_rows",
        "weighted_window_response_rows",
        "route_weighted_synthesis_rows",
        "question_result_rows",
        "next_action_rows",
    ):
        rows = payload[table_name]
        columns = set().union(*(set(row) for row in rows)) if rows else set()
        if FORBIDDEN_PRIMARY_COLUMNS.intersection(columns):
            return False
    return True


def manifest_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.append(
            {
                "artifact_id": ARTIFACT_ID,
                "path": display_path(path),
                "sha256": sha256_file(path) if path.exists() else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_payload() -> dict[str, Any]:
    event_rows = event_lookup_rows()
    edge_rows = transport_bin_rows()
    window_rows = window_weight_rows()
    weighted_rows = weighted_window_response_rows()
    route_rows = route_weighted_synthesis_rows()
    question_rows = question_result_rows(route_rows)
    next_rows = next_action_rows(route_rows)
    source_rows = source_lock_rows()
    dirty_rows = dirty_context_rows()
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
            "source_event_rows_603": len(event_rows),
            "transport_bin_rows": len(edge_rows),
            "window_weight_rows": len(window_rows),
            "weighted_window_response_rows": len(weighted_rows),
            "route_weighted_synthesis_rows": len(route_rows),
            "question_result_rows": len(question_rows),
            "next_action_rows": len(next_rows),
            "exact_pxu_probability_grid_available_now": False,
            "next_executable_block": "607_full_nodi_recompute_distribution_weighted_dimension_annulus_response",
        },
        "transport_bin_rows": edge_rows,
        "window_weight_rows": window_rows,
        "weighted_window_response_rows": weighted_rows,
        "route_weighted_synthesis_rows": route_rows,
        "question_result_rows": question_rows,
        "next_action_rows": next_rows,
        "source_lock_rows": source_rows,
        "dirty_context_rows": dirty_rows,
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
    failures: list[str] = []
    for row in payload["validation_rows"]:
        if row["status"] != "pass":
            failures.append(f"{row['check_id']}: {row['detail']}")
    return failures


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    annulus_shifts = sum(
        row["weighting_mode"] != "uniform_edge_mass"
        and row["annulus_context_after_weighting"]
        == "weighted_mass_context_shifts_from_canonical"
        for row in payload["route_weighted_synthesis_rows"]
    )
    response_shifts = sum(
        row["weighting_mode"] != "uniform_edge_mass"
        and row["interference_context_after_weighting"]
        == "noncanonical_response_contribution_exceeds_canonical"
        for row in payload["route_weighted_synthesis_rows"]
    )
    lines = [
        "# NODI sidewall distribution-weighted response surface",
        "",
        "## Mainline",
        "",
        (
            "This artifact is the first executable bridge from the 604 NODI-only "
            "sidewall result lock into COMSOL-v4-informed cross-section weighting. "
            "It uses COMSOL edge-normalized transport-bin descriptors as a coarse "
            "surrogate and keeps exact `P(x,u)` probability grid claims disabled."
        ),
        "",
        "## Counts",
        "",
        f"- 603 event rows consumed: {summary['source_event_rows_603']}",
        f"- transport bin rows: {summary['transport_bin_rows']}",
        f"- weighted window response rows: {summary['weighted_window_response_rows']}",
        f"- route synthesis rows: {summary['route_weighted_synthesis_rows']}",
        f"- COMSOL-weighted route-mode rows with annulus context shift: {annulus_shifts}",
        f"- COMSOL-weighted route-mode rows with response contribution shift: {response_shifts}",
        f"- failed validation rows: {summary['failed_validation_rows']}",
        "",
        "## Interpretation",
        "",
        (
            "Dimension envelope changes from 604 are not finalized here; they now "
            "feed 607 full NODI recompute. Annulus and response contexts are already "
            "sensitive to COMSOL transport-bin weighting, especially because the "
            "outer edge bin carries low outlet-flux mass in the available v4 context."
        ),
        "",
    ]
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json"
    report_json_path = OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json"
    edge_path = OUTPUT_DIR / f"{PREFIX}_TRANSPORT_BIN_ROWS_{DATE_STAMP}.csv"
    window_path = OUTPUT_DIR / f"{PREFIX}_WINDOW_WEIGHT_ROWS_{DATE_STAMP}.csv"
    weighted_path = OUTPUT_DIR / f"{PREFIX}_WEIGHTED_WINDOW_RESPONSE_ROWS_{DATE_STAMP}.csv"
    route_path = OUTPUT_DIR / f"{PREFIX}_ROUTE_WEIGHTED_SYNTHESIS_ROWS_{DATE_STAMP}.csv"
    question_path = OUTPUT_DIR / f"{PREFIX}_QUESTION_RESULT_ROWS_{DATE_STAMP}.csv"
    next_path = OUTPUT_DIR / f"{PREFIX}_NEXT_ACTION_ROWS_{DATE_STAMP}.csv"
    validation_path = OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv"
    source_lock_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv"
    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv"
    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv"
    report_md_path = REPORT_DIR / f"606_{PREFIX}_{DATE_STAMP}.md"

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
    write_csv_rows(edge_path, payload["transport_bin_rows"])
    write_csv_rows(window_path, payload["window_weight_rows"])
    write_csv_rows(weighted_path, payload["weighted_window_response_rows"])
    write_csv_rows(route_path, payload["route_weighted_synthesis_rows"])
    write_csv_rows(question_path, payload["question_result_rows"])
    write_csv_rows(next_path, payload["next_action_rows"])
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
        edge_path,
        window_path,
        weighted_path,
        route_path,
        question_path,
        next_path,
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
    if not args.confirm_sidewall_distribution_weighted_response_surface:
        print(
            "--confirm-sidewall-distribution-weighted-response-surface is required",
            file=sys.stderr,
        )
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
