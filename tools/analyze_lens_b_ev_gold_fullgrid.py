#!/usr/bin/env python3
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportCallIssue=false, reportGeneralTypeIssues=false
"""Analyze historical Lens-B EV+gold full-grid CSVs.

This tool is retained for provenance and regression checks. Current no-data
closure wording lives in reports 140/147/148 and must not be replaced by the
older seed-42, route-role, or B6/B7 terminology emitted here.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools._common import dataframe_to_markdown_table, format_record_lines, write_json_file
from tools.audits import ev_size_weighted_route_analysis as route_analysis


EXPECTED_ROWS_PER_SEED = 32_032
FORMAL_FULL_GRID_SEEDS = (11, 22, 33)
LEGACY_REFERENCE_SEED = 42
ACCEPTED_N_EVENTS = (1_000, 10_000)
FINAL_VALIDATION_N_EVENTS = 10_000
EXPECTED_MATERIALS = ("exosome", "gold")
EXPECTED_WAVELENGTHS_NM = (404, 488, 532, 660)
RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM = (
    route_analysis.RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM
)
CONTROL_ONLY_WAVELENGTHS_NM = route_analysis.CONTROL_ONLY_WAVELENGTHS_NM
ANCHOR_DIAMETERS_NM = (20, 30, 40, 60)
TSUYAMA_AU_SIZE_EXPONENT_TARGET = 2.3


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"raw CSV not found: {path}")
    return pd.read_csv(path, low_memory=False)


def validate_input(
    df: pd.DataFrame,
    *,
    expected_rows: int = EXPECTED_ROWS_PER_SEED,
    expected_seed: int | None = None,
    expected_n_events: int | None = None,
    expected_normalization_lane: str | None = None,
) -> dict[str, Any]:
    wavelength_col = "wavelength_nm"
    normalization_lane_values = (
        sorted(df["normalization_lane"].dropna().astype(str).unique().tolist())
        if "normalization_lane" in df
        else []
    )
    checks = {
        "row_count": int(len(df)),
        "expected_rows": int(expected_rows),
        "random_seed_values": sorted(pd.to_numeric(df["random_seed"]).dropna().astype(int).unique().tolist()),
        "expected_seed": expected_seed,
        "n_events_values": sorted(pd.to_numeric(df["n_events"]).dropna().astype(int).unique().tolist()),
        "expected_n_events": expected_n_events,
        "normalization_lane_values": normalization_lane_values,
        "expected_normalization_lane": expected_normalization_lane,
        "particle_material_values": sorted(df["particle_material"].dropna().astype(str).unique().tolist()),
        "wavelength_nm_values": sorted(pd.to_numeric(df[wavelength_col]).dropna().astype(int).unique().tolist()),
        "lockin_time_constant_s_values": sorted(
            pd.to_numeric(df.get("lockin_time_constant_s"), errors="coerce")
            .dropna()
            .unique()
            .tolist()
        ),
        "rows_by_material": {
            str(k): int(v) for k, v in df.groupby("particle_material").size().to_dict().items()
        },
        "rows_by_material_wavelength": {
            f"{material}:{int(wavelength)}": int(count)
            for (material, wavelength), count in df.groupby(["particle_material", wavelength_col]).size().to_dict().items()
        },
    }
    failures: list[str] = []
    if checks["row_count"] != int(expected_rows):
        failures.append(f"row_count expected {expected_rows}, got {checks['row_count']}")
    if len(checks["random_seed_values"]) != 1:
        failures.append(
            "input must contain exactly one seed for this per-seed analyzer, "
            f"got {checks['random_seed_values']}"
        )
    elif expected_seed is not None and checks["random_seed_values"] != [int(expected_seed)]:
        failures.append(
            f"random_seed expected [{expected_seed}], got {checks['random_seed_values']}"
        )
    if len(checks["n_events_values"]) != 1:
        failures.append(f"input must contain exactly one n_events value, got {checks['n_events_values']}")
    elif expected_n_events is not None and checks["n_events_values"] != [int(expected_n_events)]:
        failures.append(
            f"n_events expected [{expected_n_events}], got {checks['n_events_values']}"
        )
    elif checks["n_events_values"][0] not in ACCEPTED_N_EVENTS:
        failures.append(
            "n_events expected one of "
            f"{list(ACCEPTED_N_EVENTS)}, got {checks['n_events_values']}"
        )
    if len(normalization_lane_values) > 1:
        failures.append(
            "this per-seed analyzer accepts one normalization view at a time; "
            f"got {normalization_lane_values}"
        )
    if (
        expected_normalization_lane is not None
        and normalization_lane_values != [expected_normalization_lane]
    ):
        failures.append(
            "normalization_lane expected "
            f"[{expected_normalization_lane}], got {normalization_lane_values}"
        )
    if checks["particle_material_values"] != list(EXPECTED_MATERIALS):
        failures.append(
            f"particle_material expected {list(EXPECTED_MATERIALS)}, got {checks['particle_material_values']}"
        )
    if checks["wavelength_nm_values"] != list(EXPECTED_WAVELENGTHS_NM):
        failures.append(
            f"wavelength_nm expected {list(EXPECTED_WAVELENGTHS_NM)}, got {checks['wavelength_nm_values']}"
        )
    mixed_route_particles = (
        df.groupby(["wavelength_nm", "width_nm", "depth_nm", "particle_name"])["particle_material"]
        .nunique()
        .gt(1)
        .any()
    )
    if bool(mixed_route_particles):
        failures.append("at least one route/particle_name mixes particle_material values")
    checks["status"] = "passed" if not failures else "failed"
    checks["failures"] = failures
    return checks


def _with_wavelength_role(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    recommendation_wavelength = route_analysis.wavelength_isin(
        out,
        RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM,
    )
    control_wavelength = route_analysis.wavelength_isin(
        out,
        CONTROL_ONLY_WAVELENGTHS_NM,
    )
    out["wavelength_role"] = np.select(
        [recommendation_wavelength, control_wavelength],
        ["recommendation_eligible_404_660", "control_only_488_532"],
        default="unexpected_wavelength",
    )
    return out


def _add_rank_column(
    df: pd.DataFrame,
    *,
    mask: pd.Series,
    sort_columns: list[str],
    rank_column: str,
) -> None:
    df[rank_column] = np.nan
    ranked = df.loc[mask].sort_values(sort_columns, ascending=[False] * len(sort_columns))
    df.loc[ranked.index, rank_column] = np.arange(1, len(ranked) + 1, dtype=int)


def build_ev_route_ranking(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict[int, float]]]:
    ev = df[df["particle_material"].astype(str).eq("exosome")].copy()
    diameters = sorted(pd.to_numeric(ev["particle_diameter_nm"]).dropna().astype(int).unique().tolist())
    priors = route_analysis.build_priors(diameters)
    routes = route_analysis.aggregate_routes(ev, priors)
    routes = _with_wavelength_role(routes)
    reference_useful = routes["reference_operating_band"].astype(str).eq(
        route_analysis.REFERENCE_USEFUL_BAND
    )
    eligible = route_analysis.wavelength_isin(
        routes,
        RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM,
    )
    control = route_analysis.wavelength_isin(routes, CONTROL_ONLY_WAVELENGTHS_NM)

    for prior_name in priors:
        sort_columns = [
            f"{prior_name}_weighted_selected_annulus_detection",
            f"{prior_name}_weighted_stable",
            f"{prior_name}_weighted_final",
        ]
        _add_rank_column(
            routes,
            mask=routes["selected_annulus_lens_available"].astype(bool),
            sort_columns=sort_columns,
            rank_column=f"{prior_name}_selected_rank_all_routes",
        )
        _add_rank_column(
            routes,
            mask=routes["selected_annulus_lens_available"].astype(bool) & reference_useful,
            sort_columns=sort_columns,
            rank_column=f"{prior_name}_selected_rank_reference_useful",
        )
        _add_rank_column(
            routes,
            mask=routes["selected_annulus_lens_available"].astype(bool) & reference_useful & eligible,
            sort_columns=sort_columns,
            rank_column=f"{prior_name}_selected_rank_recommendation_eligible",
        )
        _add_rank_column(
            routes,
            mask=routes["selected_annulus_lens_available"].astype(bool) & reference_useful & control,
            sort_columns=sort_columns,
            rank_column=f"{prior_name}_selected_rank_control_only",
        )

    return routes.sort_values(
        ["uniform_selected_rank_reference_useful", "uniform_selected_rank_all_routes"],
        na_position="last",
    ), priors


def _fit_log_slope(sub: pd.DataFrame, diameters: tuple[int, ...]) -> float:
    fit = sub[sub["particle_diameter_nm"].astype(int).isin(diameters)].copy()
    if len(fit) < 2:
        return float("nan")
    fit = fit.sort_values("particle_diameter_nm")
    x = np.log(pd.to_numeric(fit["particle_diameter_nm"], errors="coerce").astype(float))
    y = np.log(pd.to_numeric(fit["mean_peak_height"], errors="coerce").astype(float))
    finite = np.isfinite(x) & np.isfinite(y)
    if int(finite.sum()) < 2:
        return float("nan")
    return float(np.polyfit(x[finite], y[finite], 1)[0])


def build_gold_anchor_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    gold = df[df["particle_material"].astype(str).eq("gold")].copy()
    rows: list[dict[str, Any]] = []
    for (wavelength_nm, width_nm, depth_nm), sub in gold.groupby(
        ["wavelength_nm", "width_nm", "depth_nm"]
    ):
        anchor = sub[sub["particle_diameter_nm"].astype(int).isin(ANCHOR_DIAMETERS_NM)].copy()
        row = {
            "wavelength_nm": int(wavelength_nm),
            "width_nm": int(width_nm),
            "depth_nm": int(depth_nm),
            "diagnostic_scope": "gold_anchor_tsuyama_consistency_only",
            "anchor_panel": "Au20_Au30_Au40_Au60",
            "anchor_rows": int(len(anchor)),
            "all_gold_rows": int(len(sub)),
            "mean_anchor_selected_annulus_detection": float(
                pd.to_numeric(anchor["selected_detector_mode_annulus_detection_rate"], errors="coerce").mean()
            ),
            "mean_anchor_all_crossing_detection": float(
                pd.to_numeric(anchor["all_crossing_detection_rate"], errors="coerce").mean()
            ),
            "mean_anchor_stable_detection": float(
                pd.to_numeric(anchor["stable_detection_rate"], errors="coerce").mean()
            ),
            "mean_anchor_peak_height": float(
                pd.to_numeric(anchor["mean_peak_height"], errors="coerce").mean()
            ),
            "mean_anchor_local_snr": float(
                pd.to_numeric(anchor["mean_local_snr"], errors="coerce").mean()
            ),
            "raw_peak_exponent_20_60": _fit_log_slope(anchor, ANCHOR_DIAMETERS_NM),
            "raw_peak_exponent_40_60": _fit_log_slope(anchor, (40, 60)),
            "is_b1_report_anchor_diagnostic_geometry": bool(
                int(wavelength_nm) == 660
                and int(depth_nm) == 550
                and int(width_nm) in {800, 1200}
            ),
            "ev_recommendation_allowed": False,
        }
        row["raw_peak_exponent_20_60_abs_residual_vs_2p3"] = abs(
            row["raw_peak_exponent_20_60"] - TSUYAMA_AU_SIZE_EXPONENT_TARGET
        )
        row["raw_peak_exponent_40_60_abs_residual_vs_2p3"] = abs(
            row["raw_peak_exponent_40_60"] - TSUYAMA_AU_SIZE_EXPONENT_TARGET
        )
        rows.append(row)
    out = pd.DataFrame(rows)
    return out.sort_values(
        [
            "raw_peak_exponent_20_60_abs_residual_vs_2p3",
            "mean_anchor_selected_annulus_detection",
        ],
        ascending=[True, False],
    )


def build_wavelength_summary(routes: pd.DataFrame, priors: dict[str, dict[int, float]]) -> pd.DataFrame:
    agg = routes.groupby("wavelength_nm").agg(
        route_count=("width_nm", "count"),
        raw_mean_selected_annulus_detection=("raw_mean_selected_annulus_detection", "mean"),
        raw_max_selected_annulus_detection=("raw_mean_selected_annulus_detection", "max"),
        raw_mean_all_crossing_detection=("raw_mean_all_crossing_detection", "mean"),
        raw_max_all_crossing_detection=("raw_mean_all_crossing_detection", "max"),
        reference_useful_route_count=(
            "reference_operating_band",
            lambda s: int(s.astype(str).eq(route_analysis.REFERENCE_USEFUL_BAND).sum()),
        ),
    ).reset_index()
    for prior_name in priors:
        selected_col = f"{prior_name}_weighted_selected_annulus_detection"
        ref = routes[routes["reference_operating_band"].astype(str).eq(route_analysis.REFERENCE_USEFUL_BAND)]
        by_wavelength = ref.groupby("wavelength_nm")[selected_col].max().rename(
            f"{prior_name}_reference_useful_max_selected_annulus_detection"
        )
        agg = agg.merge(by_wavelength, on="wavelength_nm", how="left")
    return agg.sort_values("wavelength_nm")


def _top_route_record(routes: pd.DataFrame, prior_name: str, mask: pd.Series) -> dict[str, Any]:
    selected_col = f"{prior_name}_weighted_selected_annulus_detection"
    ranked = routes.loc[mask].sort_values(
        [selected_col, f"{prior_name}_weighted_stable", f"{prior_name}_weighted_final"],
        ascending=[False, False, False],
    )
    if ranked.empty:
        return {}
    row = ranked.iloc[0]
    return {
        "profile": prior_name,
        "wavelength_nm": int(row["wavelength_nm"]),
        "width_nm": int(row["width_nm"]),
        "depth_nm": int(row["depth_nm"]),
        "reference_operating_band": str(row["reference_operating_band"]),
        "selected_annulus_detection": float(row[selected_col]),
        "all_crossing_detection": float(row[f"{prior_name}_weighted_all_crossing_detection"]),
        "stable_detection": float(row[f"{prior_name}_weighted_stable"]),
        "final_engineering_score": float(row[f"{prior_name}_weighted_final"]),
    }


def build_topline_summary(
    checks: dict[str, Any],
    routes: pd.DataFrame,
    gold: pd.DataFrame,
    priors: dict[str, dict[int, float]],
) -> dict[str, Any]:
    reference_useful = routes["reference_operating_band"].astype(str).eq(
        route_analysis.REFERENCE_USEFUL_BAND
    )
    eligible = route_analysis.wavelength_isin(
        routes,
        RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM,
    )
    control = route_analysis.wavelength_isin(routes, CONTROL_ONLY_WAVELENGTHS_NM)
    selected_available = routes["selected_annulus_lens_available"].astype(bool)
    return {
        "input_precheck": checks,
        "recommendation_rule": {
            "ev_recommendation_rows": "exosome only",
            "gold_rows_role": "anchor / Tsuyama consistency diagnostics only",
            "recommendation_eligible_wavelengths_nm": list(RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM),
            "control_only_wavelengths_nm": list(CONTROL_ONLY_WAVELENGTHS_NM),
            "raw_rankings_keep_all_wavelengths_nm": list(EXPECTED_WAVELENGTHS_NM),
        },
        "ev_reference_useful_top_by_profile": [
            _top_route_record(routes, prior_name, selected_available & reference_useful)
            for prior_name in priors
        ],
        "ev_recommendation_eligible_top_by_profile": [
            _top_route_record(routes, prior_name, selected_available & reference_useful & eligible)
            for prior_name in priors
        ],
        "ev_control_only_top_by_profile": [
            _top_route_record(routes, prior_name, selected_available & reference_useful & control)
            for prior_name in priors
        ],
        "gold_anchor_best_exponent_diagnostics": gold.head(8).to_dict(orient="records"),
    }


def build_a_vs_b_difference_table(routes: pd.DataFrame, raw_df: pd.DataFrame) -> pd.DataFrame:
    ev_selected_mean = float(routes["raw_mean_selected_annulus_detection"].mean())
    ev_all_mean = float(routes["raw_mean_all_crossing_detection"].mean())
    ev_uplift = ev_selected_mean / ev_all_mean if ev_all_mean > 0 else float("nan")
    observed_tau_values = sorted(
        pd.to_numeric(raw_df.get("lockin_time_constant_s"), errors="coerce")
        .dropna()
        .unique()
        .tolist()
    )
    observed_tau_text = ", ".join(f"{value:.6g}" for value in observed_tau_values) or "unavailable"
    tau_status = (
        "matches_current_1ms_requirement"
        if observed_tau_values == [0.001]
        else "legacy_non_1ms_runtime_not_final_for_current_B_requirement"
    )
    return pd.DataFrame(
        [
            {
                "difference_axis": "particle_scope",
                "criterion_a_engineering_lens": "EV engineering ranking can include EV biomimetic plus Au anchor context in its evidence pool.",
                "criterion_b_tsuyama_anchored_ev_application": "B2 recommendation is EV/exosome rows only; gold rows are anchor / Tsuyama diagnostics only.",
                "implemented_field_or_source": "particle_material; run_manifest.json recommendation_rule",
                "observed_effect_in_fullgrid": "The derived recommendation tables filter particle_material == exosome before ranking; gold outputs have ev_recommendation_allowed=false.",
            },
            {
                "difference_axis": "event_denominator_metric",
                "criterion_a_engineering_lens": "all-crossing / engineering route governance uses all_crossing_detection_rate, stable_detection_rate and final_engineering_score.",
                "criterion_b_tsuyama_anchored_ev_application": "selected-annulus lens ranks selected_detector_mode_annulus_detection_rate with annulus edges 0.5-0.8.",
                "implemented_field_or_source": "all_crossing_detection_rate vs selected_detector_mode_annulus_detection_rate; selected_detector_mode_annulus_edge_norm_min/max",
                "observed_effect_in_fullgrid": f"Across EV routes, mean selected-annulus detection is {ev_selected_mean:.6f} vs all-crossing {ev_all_mean:.6f} (uplift {ev_uplift:.3f}x), so rankings can move.",
            },
            {
                "difference_axis": "operator_family_and_lockin",
                "criterion_a_engineering_lens": "Engineering main route is not overridden by the Tsuyama reproduction operator.",
                "criterion_b_tsuyama_anchored_ev_application": "Current Criterion B runtime requirement fixes lock-in time constant to 0.001 s; the D2.1 refphase/collection operator provenance remains diagnostic only.",
                "implemented_field_or_source": "run_manifest.json frozen_b_metadata/operator_family; lockin_time_constant_s; nodi_lockin_frequency_Hz; readout_preset",
                "observed_effect_in_fullgrid": f"Analyzed rows carry lockin_time_constant_s={observed_tau_text}; status={tau_status}. Non-1ms rows can be used for impact/sensitivity assessment but not as final B=1ms full-grid evidence.",
            },
            {
                "difference_axis": "frozen_estimated_parameters",
                "criterion_a_engineering_lens": "A does not use the B1 reproduction-lens estimated parameters as physical constants.",
                "criterion_b_tsuyama_anchored_ev_application": "B1 currently records the 1 ms B4 descriptive parameter set gamma=0.736502, snr_scale=0.890700, snr_response_exp=0.810281 and raw_global_snr_scale=0.293130 as estimated-parameter metadata from Tsuyama target fitting.",
                "implemented_field_or_source": "run_manifest.json frozen_b_metadata and frozen_b_implementation_status.metadata_only_in_this_runner",
                "observed_effect_in_fullgrid": "These fields explain the B lens lineage and anchor fitting; the manifest states they are metadata-only in this runner unless future code applies active transforms to runtime outputs. Legacy 2 ms values 0.749/0.728/0.812 are retained only as provenance.",
            },
            {
                "difference_axis": "wavelength_governance",
                "criterion_a_engineering_lens": "Historical A route-role table kept 660 main, 404 sidecar, 488/532 controls.",
                "criterion_b_tsuyama_anchored_ev_application": "B raw/control rankings keep 404/488/532/660, but final recommendation conclusions can only use 404/660.",
                "implemented_field_or_source": "RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM=(404,660); CONTROL_ONLY_WAVELENGTHS_NM=(488,532)",
                "observed_effect_in_fullgrid": "The B full-grid control-only table keeps 488/532 raw ranks, but the recommendation-eligible table excludes them before final selection.",
            },
            {
                "difference_axis": "reference_operating_band_filter",
                "criterion_a_engineering_lens": "A uses broader route governance and width-prior reasoning for weak/narrow routes.",
                "criterion_b_tsuyama_anchored_ev_application": "B selected-annulus ranking records weak-reference boundary rows but final EV summary uses reference_operating_band == electronics_noise_limited_useful.",
                "implemented_field_or_source": "reference_operating_band; selected_annulus_reference_interpretation",
                "observed_effect_in_fullgrid": "Several raw selected-annulus maxima are 660/500 nm width weak-reference rows; the reference-useful B recommendation moves to 660/800 nm width.",
            },
        ]
    )


def _format_top_rows(records: list[dict[str, Any]]) -> str:
    return format_record_lines(
        records,
        "- {profile}: {wavelength_nm} nm / {width_nm} x {depth_nm} nm; "
        "selected={selected_annulus_detection:.6f}, all-crossing={all_crossing_detection:.6f}, "
        "final_score={final_engineering_score:.6f}",
    )


def _markdown_table(df: pd.DataFrame) -> str:
    return dataframe_to_markdown_table(df)


def write_markdown_report(path: Path, summary: dict[str, Any], wavelength_summary: pd.DataFrame) -> None:
    tau_values = summary["input_precheck"].get("lockin_time_constant_s_values", [])
    n_event_values = summary["input_precheck"].get("n_events_values", [])
    n_event_value = n_event_values[0] if len(n_event_values) == 1 else None
    if n_event_value == FINAL_VALIDATION_N_EVENTS:
        event_scope_text = (
            f"one seed x {FINAL_VALIDATION_N_EVENTS} events/case synthetic relative evidence, "
            "not measured calibration."
        )
    elif n_event_value is not None:
        event_scope_text = (
            f"one seed x {n_event_value} events/case low-event full-grid design evidence; "
            f"it is not the planned {FINAL_VALIDATION_N_EVENTS} events/case final-validation run "
            "and is not measured calibration."
        )
    else:
        event_scope_text = (
            "one-seed synthetic relative evidence with mixed or unavailable event counts; "
            "not measured calibration."
        )
    tau_overlay = ""
    if tau_values != [0.001]:
        tau_overlay = (
            "\n> 2026-05-14 overlay: this derived report describes rows whose "
            f"`lockin_time_constant_s` values are {tau_values}. Under the current "
            "Criterion B requirement that runtime tau is fixed to 1 ms, non-1ms "
            "tables are legacy sensitivity/reference evidence, not final B=1 ms "
            "recommendation evidence. Do not relabel these rows as 1 ms without "
            "rerunning or rebuilding the analysis.\n"
        )
    source_name = summary["input_precheck"].get("source_csv", "input raw CSV")
    seed_values = summary["input_precheck"].get("random_seed_values", [])
    normalization_values = summary["input_precheck"].get("normalization_lane_values", [])
    text = f"""# Lens B EV + Gold Full-Grid Derived Analysis

Source: `{source_name}`
{tau_overlay}

> 2026-06-12 status: this is a historical/provenance analyzer output. Current
> no-data closure is `reports/140_*`, `reports/147_*`, and `reports/148_*`:
> `404/W500` fixed-view candidate plus `660/W800` per-wavelength-view candidate,
> with no detector-resolved or absolute winner.

## Precheck

- Rows: {summary['input_precheck']['row_count']}
- Seed: {seed_values}
- n_events: {summary['input_precheck']['n_events_values']}
- normalization_lane: {normalization_values}
- Materials: {summary['input_precheck']['particle_material_values']}
- Wavelengths: {summary['input_precheck']['wavelength_nm_values']}
- lockin_time_constant_s: {summary['input_precheck'].get('lockin_time_constant_s_values')}
- Status: {summary['input_precheck']['status']}

## Lens-B interpretation rule

- B1 uses Tsuyama Au/Ag anchors to freeze an estimated parameter set.
- B2 applies the frozen Lens-B runtime/operator to EV biomimetic rows.
- EV recommendation uses exosome rows only.
- Gold rows are diagnostic only and are not eligible for EV recommendation.
- Raw rankings retain 404/488/532/660; final recommendation conclusions only use 404/660.
- This run is {event_scope_text}

## EV reference-useful selected-annulus tops

{_format_top_rows(summary['ev_reference_useful_top_by_profile'])}

## EV recommendation-eligible tops (404/660 only)

{_format_top_rows(summary['ev_recommendation_eligible_top_by_profile'])}

## EV control-only tops (488/532 retained as controls)

{_format_top_rows(summary['ev_control_only_top_by_profile'])}

## Wavelength summary

{_markdown_table(wavelength_summary)}

## Main reading guard

Use the generated top tables above for this exact seed, event count, and
normalization view. Do not carry forward old hard-coded route conclusions from
legacy seed-42 or low-event reports. A final 3-seed statement must be written
only after the dedicated aggregation step has compared seeds and preserved the
normalization-view boundary.

404 and 660 nm are recommendation-eligible. 488/532 nm remain control-only /
trend-only even when a raw metric is high. Gold rows should be discussed only as
anchor/Tsuyama consistency diagnostics.
"""
    path.write_text(text, encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    input_csv = Path(args.input_csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = _load_csv(input_csv)
    checks = validate_input(
        df,
        expected_rows=int(args.expected_rows),
        expected_seed=args.expected_seed,
        expected_n_events=args.expected_n_events,
        expected_normalization_lane=args.expected_normalization_lane,
    )
    checks["source_csv"] = str(input_csv)
    write_json_file(output_dir / "lens_b_fullgrid_data_precheck.json", checks)
    if checks["status"] != "passed":
        raise SystemExit("Input precheck failed; see lens_b_fullgrid_data_precheck.json")
    if args.check_only:
        return

    routes, priors = build_ev_route_ranking(df)
    routes.to_csv(output_dir / "lens_b_ev_fullgrid_route_ranking.csv", index=False)

    eligible = routes[
        route_analysis.wavelength_isin(routes, RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM)
    ]
    eligible.to_csv(output_dir / "lens_b_ev_recommendation_eligible_404_660.csv", index=False)

    control = routes[route_analysis.wavelength_isin(routes, CONTROL_ONLY_WAVELENGTHS_NM)]
    control.to_csv(output_dir / "lens_b_ev_control_only_488_532.csv", index=False)

    gold = build_gold_anchor_diagnostics(df)
    gold.to_csv(output_dir / "lens_b_gold_anchor_tsuyama_diagnostic_summary.csv", index=False)

    wavelength_summary = build_wavelength_summary(routes, priors)
    wavelength_summary.to_csv(output_dir / "lens_b_ev_wavelength_summary.csv", index=False)

    difference_table = build_a_vs_b_difference_table(routes, df)
    difference_table.to_csv(output_dir / "lens_b_a_vs_b_difference_explainer.csv", index=False)

    summary = build_topline_summary(checks, routes, gold, priors)
    write_json_file(output_dir / "lens_b_fullgrid_topline_summary.json", summary)
    write_markdown_report(
        output_dir / "lens_b_fullgrid_analysis_report.md",
        summary,
        wavelength_summary,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze historical Lens-B EV+gold full-grid CSVs. Current no-data "
            "closure wording belongs to reports 140/147/148."
        )
    )
    parser.add_argument(
        "--input-csv",
        default="results/lens_b_ev_gold_fullgrid_1seed_20260513/seed_42_raw_rows.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="results/lens_b_ev_gold_fullgrid_1seed_20260513",
    )
    parser.add_argument("--expected-rows", type=int, default=EXPECTED_ROWS_PER_SEED)
    parser.add_argument("--expected-seed", type=int, default=None)
    parser.add_argument("--expected-n-events", type=int, default=None)
    parser.add_argument(
        "--expected-normalization-lane",
        choices=["fixed_660_gold", "per_wavelength_gold"],
        default=None,
    )
    parser.add_argument("--check-only", action="store_true")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
