#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.config import (  # noqa: E402
    BASELINE_PARTICLE,
    THETA_GRID_RAD,
    medium_for_particle,
    particle_from_name,
)
from nodi_simulator._exports import WATER, run_parameter_sweep  # noqa: E402
from tools._common import (  # noqa: E402
    dataframe_to_markdown_table,
    format_record_lines,
    write_json_file,
)
from tools.audits import ev_size_weighted_route_analysis as route_analysis  # noqa: E402
from tools.audits import tsuyama_detection_rate_calibration as rate_calib  # noqa: E402
from tools.audits import tsuyama_gold_aligned_detection_lane as lane  # noqa: E402


RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM = (
    route_analysis.RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM
)
CONTROL_ONLY_WAVELENGTHS_NM = route_analysis.CONTROL_ONLY_WAVELENGTHS_NM
TAU_1MS_CANDIDATE_ID = "tau_1ms_global_refphi_plus_collection_narrow"
TAU_1MS_SCENARIO_ID = "nodi_2022_5sigma_single_sensitivity"
TAU_1MS_LOCKIN_TIME_CONSTANT_S = 0.001
GOLD_ANCHOR_NAMES = ("gold_20nm", "gold_30nm", "gold_40nm", "gold_60nm")
OUTPUT_PREFIX = "stage_b5_tau1ms_targeted_ev_probe"


@dataclass(frozen=True)
class PanelRoute:
    wavelength_nm: int
    width_nm: int
    depth_nm: int
    route_role: str
    route_note: str

    @property
    def key(self) -> tuple[int, int, int]:
        return (self.wavelength_nm, self.width_nm, self.depth_nm)


@dataclass(frozen=True)
class ProbeScope:
    routes: list[PanelRoute]
    ev_particle_names: list[str]
    gold_anchor_names: list[str]
    particle_names: list[str]
    route_particle_rows_per_seed: int
    substitutions: list[dict[str, Any]]


def default_route_panel() -> tuple[list[PanelRoute], list[dict[str, Any]]]:
    substitutions = [
        {
            "requested_route": [532, 700, 750],
            "used_route": [532, 700, 700],
            "reason": "route source has no 750 nm depth rows at 532 nm; nearest top-control grid row retained",
        }
    ]
    routes = [
        PanelRoute(660, 800, 800, "longwave_660_candidate_band", "roadmap 660/800x800"),
        PanelRoute(660, 800, 900, "longwave_660_candidate_band", "roadmap 660/800x900"),
        PanelRoute(660, 800, 1300, "longwave_660_candidate_band", "roadmap 660/800x1300"),
        PanelRoute(660, 800, 1400, "longwave_660_candidate_band", "roadmap 660/800x1400"),
        PanelRoute(660, 800, 1500, "longwave_660_candidate_band", "roadmap 660/800x1500"),
        PanelRoute(404, 500, 550, "shortwave_404_candidate_probe", "roadmap 404/500x550"),
        PanelRoute(404, 600, 1300, "shortwave_404_candidate_probe", "roadmap and prior sidecar 404/600x1300"),
        PanelRoute(404, 800, 700, "shortwave_404_prior_sidecar", "prior report-49/report-88 sidecar sanity route"),
        PanelRoute(488, 600, 650, "control_only_488_reference", "roadmap top control-only reference"),
        PanelRoute(532, 700, 700, "control_only_532_reference", "substituted for unavailable 532/700x750"),
        PanelRoute(404, 500, 1500, "weak_reference_control_500nm_width", "representative weak-reference control"),
        PanelRoute(488, 500, 1500, "weak_reference_control_500nm_width", "representative weak-reference control"),
        PanelRoute(532, 500, 1500, "weak_reference_control_500nm_width", "representative weak-reference control"),
        PanelRoute(660, 500, 1500, "weak_reference_control_500nm_width", "representative weak-reference control"),
    ]
    return routes, substitutions


def read_source(path: Path) -> pd.DataFrame:
    required = [
        "particle_name",
        "particle_material",
        "particle_family",
        "wavelength_nm",
        "width_nm",
        "depth_nm",
    ]
    if not path.exists():
        raise FileNotFoundError(f"route source does not exist: {path}")
    df = pd.read_csv(path, usecols=required, low_memory=False)
    for column in ("wavelength_nm", "width_nm", "depth_nm"):
        df[column] = pd.to_numeric(df[column], errors="raise").astype(int)
    for column in ("particle_name", "particle_material", "particle_family"):
        df[column] = df[column].astype(str)
    return df


def build_probe_scope(source: pd.DataFrame, *, include_gold_anchors: bool) -> ProbeScope:
    routes, substitutions = default_route_panel()
    available_routes = {
        (int(row.wavelength_nm), int(row.width_nm), int(row.depth_nm))
        for row in source[["wavelength_nm", "width_nm", "depth_nm"]]
        .drop_duplicates()
        .itertuples(index=False)
    }
    missing = [route.key for route in routes if route.key not in available_routes]
    if missing:
        raise ValueError(f"targeted route panel has routes missing from source: {missing}")

    particles = (
        source[["particle_name", "particle_material", "particle_family"]]
        .drop_duplicates()
        .sort_values(["particle_material", "particle_name"])
    )
    ev = particles[
        (particles["particle_material"].str.lower() == "exosome")
        | particles["particle_family"].str.lower().str.contains("ev|exosome|sev", regex=True)
        | particles["particle_name"].str.lower().str.startswith("exosome_")
    ]
    ev_names = sorted(ev["particle_name"].astype(str).tolist())
    gold_anchor_names: list[str] = []
    if include_gold_anchors:
        available_names = set(particles["particle_name"].astype(str))
        gold_anchor_names = [name for name in GOLD_ANCHOR_NAMES if name in available_names]
        missing_gold = [name for name in GOLD_ANCHOR_NAMES if name not in available_names]
        if missing_gold:
            raise ValueError(f"gold anchor particles missing from source: {missing_gold}")
    particle_names = ev_names + gold_anchor_names
    return ProbeScope(
        routes=routes,
        ev_particle_names=ev_names,
        gold_anchor_names=gold_anchor_names,
        particle_names=particle_names,
        route_particle_rows_per_seed=len(routes) * len(particle_names),
        substitutions=substitutions,
    )


def build_tau1ms_cfg(n_events: int, seed: int):
    candidate = rate_calib.candidate_by_id()[TAU_1MS_CANDIDATE_ID]
    cfg = rate_calib.build_candidate_cfg(
        candidate,
        n_events=int(n_events),
        random_seed=int(seed),
        scenario_id=TAU_1MS_SCENARIO_ID,
    )
    if float(cfg.lockin_time_constant_s) != TAU_1MS_LOCKIN_TIME_CONSTANT_S:
        raise AssertionError(
            f"candidate cfg has lockin_time_constant_s={cfg.lockin_time_constant_s}, expected 0.001"
        )
    optical_template = rate_calib.build_candidate_optical_template(candidate)
    return cfg, optical_template


def _run_one_route(
    *,
    route: PanelRoute,
    particles: list[Any],
    cfg: Any,
    optical_template: Any,
    workers: int,
) -> pd.DataFrame:
    baseline_channel = lane.case_baseline_channel(route.width_nm, route.depth_nm)
    results = run_parameter_sweep(
        particle_types=particles,
        medium=WATER,
        width_list_m=np.array([float(route.width_nm) * 1e-9], dtype=float),
        depth_list_m=np.array([float(route.depth_nm) * 1e-9], dtype=float),
        wavelength_list_m=np.array([float(route.wavelength_nm) * 1e-9], dtype=float),
        optical_template=optical_template,
        sim_cfg=cfg,
        theta_grid_rad=THETA_GRID_RAD,
        baseline_particle=BASELINE_PARTICLE,
        baseline_channel=baseline_channel,
        verbose=False,
        n_workers=int(workers),
        medium_resolver=medium_for_particle,
        allow_partial=False,
    )
    frame = lane.flatten_sweep_results(
        results,
        scenario_config_id=TAU_1MS_SCENARIO_ID,
        cfg=cfg,
        n_events=int(cfg.n_events),
        random_seed=int(cfg.random_seed),
        claim_level="criterion_b_tau1ms_targeted_ev_probe_not_final_fullgrid",
    )
    frame.insert(0, "route_role", route.route_role)
    frame.insert(1, "route_note", route.route_note)
    frame.insert(2, "candidate_id", TAU_1MS_CANDIDATE_ID)
    return frame


def _route_panel_frame(scope: ProbeScope) -> pd.DataFrame:
    return pd.DataFrame([asdict(route) for route in scope.routes])


def write_manifest(output_dir: Path, args: argparse.Namespace, scope: ProbeScope, cfg: Any) -> None:
    manifest = {
        "stage": "B5_targeted_EV_1ms_probe_before_fullgrid",
        "status": "targeted_probe_not_B1ms_final_fullgrid_recommendation",
        "route_source": str(Path(args.route_source)),
        "output_dir": str(output_dir),
        "workers": int(args.workers),
        "seed": int(args.seed),
        "n_events": int(args.n_events),
        "include_gold_anchors": bool(args.include_gold_anchors),
        "probe_scope": {
            "routes": [asdict(route) for route in scope.routes],
            "ev_particle_count": len(scope.ev_particle_names),
            "gold_anchor_count": len(scope.gold_anchor_names),
            "particle_count": len(scope.particle_names),
            "route_particle_rows_per_seed": scope.route_particle_rows_per_seed,
            "substitutions": scope.substitutions,
        },
        "criterion_b_runtime_config": {
            "candidate_id": TAU_1MS_CANDIDATE_ID,
            "scenario_id": TAU_1MS_SCENARIO_ID,
            "lockin_time_constant_s": float(cfg.lockin_time_constant_s),
            "threshold_sigma": float(cfg.threshold_sigma),
            "readout_preset": cfg.readout_preset,
            "readout_observable_mode": cfg.readout_observable_mode,
            "pulse_detection_mode": cfg.pulse_detection_mode,
            "detection_decision_mode": cfg.detection_decision_mode,
            "selected_annulus_edge_norm_min": cfg.selected_annulus_edge_norm_min,
            "selected_annulus_edge_norm_max": cfg.selected_annulus_edge_norm_max,
        },
        "governance": {
            "criterion_a_remains_engineering_main_ranking": True,
            "criterion_b_role": "Tsuyama-anchored EV application lens",
            "ev_recommendation_rows": "exosome only",
            "gold_rows_role": "anchor diagnostics only; never EV recommendation",
            "recommendation_eligible_wavelengths_nm": list(RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM),
            "control_only_wavelengths_nm": list(CONTROL_ONLY_WAVELENGTHS_NM),
        },
    }
    write_json_file(output_dir / f"{OUTPUT_PREFIX}_manifest.json", manifest)
    _route_panel_frame(scope).to_csv(output_dir / f"{OUTPUT_PREFIX}_route_panel.csv", index=False)


def run_probe(args: argparse.Namespace) -> Path:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    source = read_source(Path(args.route_source))
    scope = build_probe_scope(source, include_gold_anchors=bool(args.include_gold_anchors))
    cfg, optical_template = build_tau1ms_cfg(args.n_events, args.seed)
    write_manifest(output_dir, args, scope, cfg)

    if args.dry_run:
        return output_dir / f"{OUTPUT_PREFIX}_raw_rows.csv"

    particles = [particle_from_name(name) for name in scope.particle_names]
    frames: list[pd.DataFrame] = []
    start = time.perf_counter()
    raw_path = output_dir / f"{OUTPUT_PREFIX}_raw_rows.csv"
    for index, route in enumerate(scope.routes, start=1):
        frame = _run_one_route(
            route=route,
            particles=particles,
            cfg=cfg,
            optical_template=optical_template,
            workers=args.workers,
        )
        frame.insert(0, "route_index", index)
        frame["run_elapsed_s_at_route_complete"] = time.perf_counter() - start
        frames.append(frame)
        pd.concat(frames, ignore_index=True).to_csv(raw_path, index=False)
        print(
            f"completed route {index}/{len(scope.routes)} {route.key}: "
            f"{sum(len(part) for part in frames)} rows in {time.perf_counter() - start:.1f}s",
            flush=True,
        )
    return raw_path


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


def build_route_ranking(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict[int, float]]]:
    ev = raw[raw["particle_material"].astype(str).eq("exosome")].copy()
    diameters = sorted(pd.to_numeric(ev["particle_diameter_nm"]).dropna().astype(int).unique())
    priors = route_analysis.build_priors(diameters)
    routes = route_analysis.aggregate_routes(ev, priors)
    role_lookup = (
        raw[["wavelength_nm", "width_nm", "depth_nm", "route_role", "route_note"]]
        .drop_duplicates()
        .groupby(["wavelength_nm", "width_nm", "depth_nm"])
        .first()
        .reset_index()
    )
    routes = routes.merge(role_lookup, on=["wavelength_nm", "width_nm", "depth_nm"], how="left")
    ev_metric_agg = (
        ev.groupby(["wavelength_nm", "width_nm", "depth_nm"])
        .agg(
            raw_mean_peak_height=("mean_peak_height", "mean"),
            raw_mean_peak_margin_z=("mean_peak_margin_z", "mean"),
            raw_mean_nodi_transit_bandwidth_gain=("mean_nodi_transit_bandwidth_gain", "mean"),
            raw_mean_local_snr=("mean_local_snr", "mean"),
        )
        .reset_index()
    )
    routes = routes.merge(ev_metric_agg, on=["wavelength_nm", "width_nm", "depth_nm"], how="left")
    recommendation_wavelength = route_analysis.wavelength_isin(
        routes,
        RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM,
    )
    control_wavelength = route_analysis.wavelength_isin(
        routes,
        CONTROL_ONLY_WAVELENGTHS_NM,
    )
    routes["wavelength_role"] = np.select(
        [recommendation_wavelength, control_wavelength],
        ["recommendation_eligible_404_660", "control_only_488_532"],
        default="unexpected_wavelength",
    )
    reference_useful = routes["reference_operating_band"].astype(str).eq(
        route_analysis.REFERENCE_USEFUL_BAND
    )
    selected_available = routes["selected_annulus_lens_available"].astype(bool)
    eligible = recommendation_wavelength
    for prior_name in priors:
        sort_columns = [
            f"{prior_name}_weighted_selected_annulus_detection",
            f"{prior_name}_weighted_stable",
            f"{prior_name}_weighted_final",
        ]
        _add_rank_column(
            routes,
            mask=selected_available,
            sort_columns=sort_columns,
            rank_column=f"{prior_name}_rank_all_panel_routes",
        )
        _add_rank_column(
            routes,
            mask=selected_available & reference_useful,
            sort_columns=sort_columns,
            rank_column=f"{prior_name}_rank_reference_useful",
        )
        _add_rank_column(
            routes,
            mask=selected_available & reference_useful & eligible,
            sort_columns=sort_columns,
            rank_column=f"{prior_name}_rank_recommendation_eligible",
        )
    return routes.sort_values(
        ["uniform_rank_reference_useful", "uniform_rank_all_panel_routes"],
        na_position="last",
    ), priors


def build_wavelength_summary(routes: pd.DataFrame, priors: dict[str, dict[int, float]]) -> pd.DataFrame:
    grouped = routes.groupby("wavelength_nm").agg(
        route_count=("width_nm", "count"),
        reference_useful_route_count=(
            "reference_operating_band",
            lambda s: int(s.astype(str).eq(route_analysis.REFERENCE_USEFUL_BAND).sum()),
        ),
        raw_mean_selected_annulus_detection=("raw_mean_selected_annulus_detection", "mean"),
        raw_max_selected_annulus_detection=("raw_mean_selected_annulus_detection", "max"),
        raw_mean_all_crossing_detection=("raw_mean_all_crossing_detection", "mean"),
        raw_max_all_crossing_detection=("raw_mean_all_crossing_detection", "max"),
        raw_mean_stable_detection=("raw_mean_stable", "mean"),
        raw_mean_peak_height=("raw_mean_peak_height", "mean"),
        raw_mean_peak_margin_z=("raw_mean_peak_margin_z", "mean"),
        raw_mean_nodi_transit_bandwidth_gain=("raw_mean_nodi_transit_bandwidth_gain", "mean"),
    ).reset_index()
    useful = routes[routes["reference_operating_band"].astype(str).eq(route_analysis.REFERENCE_USEFUL_BAND)]
    for prior_name in priors:
        col = f"{prior_name}_weighted_selected_annulus_detection"
        best = useful.groupby("wavelength_nm")[col].max().rename(
            f"{prior_name}_reference_useful_best_selected_annulus_detection"
        )
        grouped = grouped.merge(best, on="wavelength_nm", how="left")
    return grouped.sort_values("wavelength_nm")


def _top_record(routes: pd.DataFrame, prior_name: str, mask: pd.Series) -> dict[str, Any]:
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
        "route_role": str(row.get("route_role", "")),
        "reference_operating_band": str(row["reference_operating_band"]),
        "selected_annulus_detection": float(row[selected_col]),
        "all_crossing_detection": float(row[f"{prior_name}_weighted_all_crossing_detection"]),
        "stable_detection": float(row[f"{prior_name}_weighted_stable"]),
        "mean_peak_height": float(row["raw_mean_peak_height"]),
        "mean_peak_margin_z": float(row["raw_mean_peak_margin_z"]),
        "mean_nodi_transit_bandwidth_gain": float(row["raw_mean_nodi_transit_bandwidth_gain"]),
    }


def build_topline_summary(raw: pd.DataFrame, routes: pd.DataFrame, priors: dict[str, dict[int, float]]) -> dict[str, Any]:
    selected_available = routes["selected_annulus_lens_available"].astype(bool)
    reference_useful = routes["reference_operating_band"].astype(str).eq(
        route_analysis.REFERENCE_USEFUL_BAND
    )
    eligible = route_analysis.wavelength_isin(
        routes,
        RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM,
    )
    control = route_analysis.wavelength_isin(routes, CONTROL_ONLY_WAVELENGTHS_NM)
    comparison_rows: list[dict[str, Any]] = []
    any_404_overtakes_660 = False
    for prior_name in priors:
        selected_col = f"{prior_name}_weighted_selected_annulus_detection"
        base = routes[selected_available & reference_useful & eligible]
        best_by_wavelength = (
            base.sort_values([selected_col, f"{prior_name}_weighted_stable"], ascending=[False, False])
            .groupby("wavelength_nm")
            .head(1)
        )
        best_404 = best_by_wavelength[best_by_wavelength["wavelength_nm"].astype(int).eq(404)]
        best_660 = best_by_wavelength[best_by_wavelength["wavelength_nm"].astype(int).eq(660)]
        value_404 = float(best_404[selected_col].iloc[0]) if not best_404.empty else float("nan")
        value_660 = float(best_660[selected_col].iloc[0]) if not best_660.empty else float("nan")
        overtakes = bool(pd.notna(value_404) and pd.notna(value_660) and value_404 > value_660)
        any_404_overtakes_660 = any_404_overtakes_660 or overtakes
        comparison_rows.append(
            {
                "profile": prior_name,
                "best_404_selected_annulus_detection": value_404,
                "best_660_selected_annulus_detection": value_660,
                "best_404_overtakes_best_660": overtakes,
            }
        )
    return {
        "status": "targeted_probe_not_B1ms_final_fullgrid_recommendation",
        "input_precheck": {
            "row_count": int(len(raw)),
            "random_seed_values": sorted(pd.to_numeric(raw["random_seed"]).astype(int).unique().tolist()),
            "n_events_values": sorted(pd.to_numeric(raw["n_events"]).astype(int).unique().tolist()),
            "lockin_time_constant_s_values": sorted(pd.to_numeric(raw["lockin_time_constant_s"]).unique().tolist()),
            "particle_material_values": sorted(raw["particle_material"].astype(str).unique().tolist()),
            "wavelength_nm_values": sorted(pd.to_numeric(raw["wavelength_nm"]).astype(int).unique().tolist()),
        },
        "recommendation_rule": {
            "ev_recommendation_rows": "exosome only",
            "gold_rows_role": "anchor diagnostics only; never EV recommendation",
            "recommendation_eligible_wavelengths_nm": list(RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM),
            "control_only_wavelengths_nm": list(CONTROL_ONLY_WAVELENGTHS_NM),
        },
        "ev_reference_useful_top_by_profile": [
            _top_record(routes, prior_name, selected_available & reference_useful)
            for prior_name in priors
        ],
        "ev_recommendation_eligible_top_by_profile": [
            _top_record(routes, prior_name, selected_available & reference_useful & eligible)
            for prior_name in priors
        ],
        "ev_control_only_top_by_profile": [
            _top_record(routes, prior_name, selected_available & reference_useful & control)
            for prior_name in priors
        ],
        "eligible_404_vs_660_by_profile": comparison_rows,
        "stage_b5_exit_read": {
            "best_404_overtakes_best_660_under_reference_useful_filter": any_404_overtakes_660,
            "fullgrid_priority": (
                "proceed_to_B6_before_report_recommendation"
                if any_404_overtakes_660
                else "lower_priority_if_no_other_instability_appears"
            ),
            "control_only_rule": "488/532 remain control-only regardless of raw rank",
        },
    }


def _markdown_table(df: pd.DataFrame) -> str:
    return dataframe_to_markdown_table(df)


def _format_top(records: list[dict[str, Any]]) -> str:
    return format_record_lines(
        records,
        "- {profile}: {wavelength_nm} nm / {width_nm} x {depth_nm} nm; "
        "selected={selected_annulus_detection:.6g}, all-crossing={all_crossing_detection:.6g}, "
        "stable={stable_detection:.6g}, transit_gain={mean_nodi_transit_bandwidth_gain:.6g}",
        empty_message="- no rankable rows",
    )


def write_markdown_summary(path: Path, summary: dict[str, Any], wavelength_summary: pd.DataFrame) -> None:
    text = f"""# Stage B5 Tau=1 ms Targeted EV Probe

This is a targeted Criterion B probe, not B=1 ms final full-grid recommendation evidence.

## Precheck

- Rows: {summary['input_precheck']['row_count']}
- Seed: {summary['input_precheck']['random_seed_values']}
- n_events: {summary['input_precheck']['n_events_values']}
- lockin_time_constant_s: {summary['input_precheck']['lockin_time_constant_s_values']}
- Materials: {summary['input_precheck']['particle_material_values']}
- Wavelengths: {summary['input_precheck']['wavelength_nm_values']}

## EV Reference-Useful Tops

{_format_top(summary['ev_reference_useful_top_by_profile'])}

## EV Recommendation-Eligible Tops

{_format_top(summary['ev_recommendation_eligible_top_by_profile'])}

## EV Control-Only Tops

{_format_top(summary['ev_control_only_top_by_profile'])}

## Wavelength Summary

{_markdown_table(wavelength_summary)}

## Stage B5 Exit Read

- 404 overtakes 660 under the reference-useful selected-annulus filter: {summary['stage_b5_exit_read']['best_404_overtakes_best_660_under_reference_useful_filter']}
- Suggested full-grid priority: {summary['stage_b5_exit_read']['fullgrid_priority']}
- 488/532 rule: {summary['stage_b5_exit_read']['control_only_rule']}

Gold anchors, when present, are diagnostic continuity rows only and are not eligible for EV recommendation.
"""
    path.write_text(text, encoding="utf-8")


def analyze_probe(raw_csv: Path, output_dir: Path) -> None:
    raw = pd.read_csv(raw_csv, low_memory=False)
    routes, priors = build_route_ranking(raw)
    route_path = output_dir / f"{OUTPUT_PREFIX}_route_ranking.csv"
    wavelength_path = output_dir / f"{OUTPUT_PREFIX}_wavelength_summary.csv"
    summary_path = output_dir / f"{OUTPUT_PREFIX}_summary.json"
    markdown_path = output_dir / f"{OUTPUT_PREFIX}_summary.md"
    routes.to_csv(route_path, index=False)
    wavelength_summary = build_wavelength_summary(routes, priors)
    wavelength_summary.to_csv(wavelength_path, index=False)
    summary = build_topline_summary(raw, routes, priors)
    write_json_file(summary_path, summary)
    write_markdown_summary(markdown_path, summary, wavelength_summary)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stage B5 targeted Criterion B tau=1 ms EV probe.")
    parser.add_argument(
        "--route-source",
        default="results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="results/lens_b_tau1ms_recalibration_20260514/stage_b5_tau1ms_targeted_ev_probe_3000e_1seed",
    )
    parser.add_argument("--workers", type=int, default=7)
    parser.add_argument("--n-events", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--include-gold-anchors", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--analyze-only", action="store_true")
    parser.add_argument("--input-csv", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.analyze_only:
        if args.input_csv is None:
            raise SystemExit("--input-csv is required with --analyze-only")
        analyze_probe(Path(args.input_csv), output_dir)
        return
    raw_path = run_probe(args)
    if not args.dry_run:
        analyze_probe(raw_path, output_dir)


if __name__ == "__main__":
    main()
