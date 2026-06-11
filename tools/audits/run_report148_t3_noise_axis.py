#!/usr/bin/env python3
# pyright: reportAttributeAccessIssue=false, reportCallIssue=false, reportArgumentType=false, reportGeneralTypeIssues=false
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.config import THETA_GRID_RAD, medium_for_particle, particle_from_name  # noqa: E402
from nodi_simulator.parameter_sweep import run_single_case_batch_shared_event_normalization_views  # noqa: E402
from nodi_simulator.structured_particles import make_biomimetic_exosome_particle  # noqa: E402
from tools._common import write_json_file  # noqa: E402
from tools.audits import tsuyama_gold_aligned_detection_lane as lane  # noqa: E402
from tools.audits.ev_size_weighted_route_analysis import build_priors, normalize_prior  # noqa: E402
from tools.audits.run_report148_stage1_ab_minimal import (  # noqa: E402
    NORMALIZATION_VIEWS,
    PRIOR_NAME,
    READOUT_POLICY,
    ROUTE_MODEL_CATALOG,
    _build_route_cfg,
)
from tools.lens_b_ev_gold_fullgrid_runner import _fixed_660_e_sca_ref, _per_wavelength_e_sca_ref  # noqa: E402


OUTPUT_DIR_DEFAULT = Path("results/audits") / f"report148_t3_noise_axis_{datetime.now().strftime('%Y%m%d')}"
SHOT_NOISE_SCALES = (0.001, 0.05, 0.2)
SEEDS = (11, 22, 33)
BASELINE_SHOT = 0.001
EV_DIAMETERS_NM = (80, 120, 160)
GOLD_ANCHOR_NAMES = ("gold_20nm", "gold_40nm", "gold_60nm")
DETECTOR_ROUTE_ID = "A_hybrid"
GAUGE_MODE = "V1_gauge_locked"
BASELINE_PRESET_NAME = "biomimetic_corona_nominal"
ROUTES_404 = [(404, width_nm, depth_nm) for width_nm in (500, 600, 700) for depth_nm in (700, 900, 1100, 1300, 1500)]
ROUTES_660 = [(660, width_nm, depth_nm) for width_nm in (700, 800) for depth_nm in (700, 900, 1100, 1300, 1500)]
ROUTES = (*ROUTES_404, *ROUTES_660)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _route_family_id(route: tuple[int, int, int]) -> str:
    wavelength_nm, width_nm, _ = route
    return f"lambda{wavelength_nm}_w{width_nm}_depth_sweep"


def _route_family_note(route: tuple[int, int, int]) -> str:
    wavelength_nm, width_nm, _ = route
    return f"{wavelength_nm} width-{width_nm} depth sweep"


def _baseline_ev_particles() -> list[Any]:
    particles: list[Any] = []
    for diameter_nm in EV_DIAMETERS_NM:
        particles.append(
            make_biomimetic_exosome_particle(
                diameter_nm,
                name=f"exosome_t3_{BASELINE_PRESET_NAME}_{int(diameter_nm)}nm",
                preset_name=BASELINE_PRESET_NAME,
                overrides={
                    "core_n_real": 1.38,
                    "corona_thickness_m": 4e-9,
                    "t3_noise_baseline_combo": True,
                },
            )
        )
    return particles


def _gold_particles() -> list[Any]:
    return [particle_from_name(name) for name in GOLD_ANCHOR_NAMES]


def _weighted_metrics(route_rows: pd.DataFrame) -> dict[str, float]:
    diameters = sorted(
        pd.to_numeric(route_rows["particle_diameter_nm"], errors="coerce")
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )
    prior = normalize_prior(build_priors(diameters)[PRIOR_NAME])
    weighted_selected = 0.0
    weighted_all_crossing = 0.0
    weighted_stable = 0.0
    for _, row in route_rows.iterrows():
        weight = float(prior[int(round(float(row["particle_diameter_nm"])))])
        weighted_selected += weight * float(row["selected_detector_mode_annulus_detection_rate"])
        weighted_all_crossing += weight * float(row["all_crossing_detection_rate"])
        weighted_stable += weight * float(row["stable_detection_rate"])
    return {
        "weighted_selected_annulus_detection": weighted_selected,
        "weighted_all_crossing_detection": weighted_all_crossing,
        "weighted_stable_detection": weighted_stable,
    }


def _build_case_rows(
    *,
    route: tuple[int, int, int],
    particle: Any,
    seed: int,
    shot_noise_scale: float,
    n_events: int,
) -> list[dict[str, Any]]:
    wavelength_nm, width_nm, depth_nm = route
    particle_name = particle.name
    medium = medium_for_particle(particle)
    channel = lane.case_baseline_channel(width_nm, depth_nm)
    view_configs: dict[str, Any] = {}
    e_sca_refs: dict[str, float] = {}
    for normalization_view in NORMALIZATION_VIEWS:
        cfg, optical_template = _build_route_cfg(
            n_events=int(n_events),
            seed=seed,
            detector_route_id=DETECTOR_ROUTE_ID,
            detector_forward_model=ROUTE_MODEL_CATALOG[DETECTOR_ROUTE_ID],
            normalization_lane=normalization_view,
        )
        cfg = replace(cfg, shot_noise_scale=float(shot_noise_scale))
        view_configs[normalization_view] = cfg
        if normalization_view == "fixed_660_gold":
            e_sca_refs[normalization_view] = _fixed_660_e_sca_ref(
                width_nm=width_nm,
                depth_nm=depth_nm,
                cfg=cfg,
                optical_template=optical_template,
            )
        else:
            e_sca_refs[normalization_view] = _per_wavelength_e_sca_ref(
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                medium=medium,
                cfg=cfg,
                optical_template=optical_template,
            )
    optical = optical_template
    optical.wavelength_m = float(wavelength_nm) * 1e-9
    outputs = run_single_case_batch_shared_event_normalization_views(
        particle,
        medium,
        channel,
        optical,
        view_configs,
        e_sca_refs,
        THETA_GRID_RAD,
    )
    rows: list[dict[str, Any]] = []
    for normalization_view, payload in outputs.items():
        summary = payload["summary"]
        rows.append(
            {
                "detector_route_id": DETECTOR_ROUTE_ID,
                "detector_forward_model": ROUTE_MODEL_CATALOG[DETECTOR_ROUTE_ID],
                "gauge_mode": GAUGE_MODE,
                "readout_policy": READOUT_POLICY,
                "normalization_view": normalization_view,
                "noise_policy": "common_noise_control",
                "shot_noise_scale": float(shot_noise_scale),
                "seed": int(seed),
                "wavelength_nm": int(wavelength_nm),
                "width_nm": int(width_nm),
                "depth_nm": int(depth_nm),
                "route_family_id": _route_family_id(route),
                "route_family_note": _route_family_note(route),
                "particle_name": particle_name,
                "particle_family": "gold" if "gold" in particle_name else "EV_sEV",
                "particle_diameter_nm": float(particle.radius_m * 2e9),
                "detection_rate": float(summary["detection_rate"]),
                "stable_detection_rate": float(summary["stable_detection_rate"]),
                "detection_rate_wilson_lb": float(summary["detection_rate_wilson_lb"]),
                "stable_detection_rate_wilson_lb": float(summary["stable_detection_rate_wilson_lb"]),
                "mean_peak_margin_z": float(summary["mean_peak_margin_z"]),
                "all_crossing_detection_rate": float(summary["all_crossing_detection_rate"]),
                "all_crossing_detection_rate_wilson_lb": float(summary["all_crossing_detection_rate_wilson_lb"]),
                "selected_detector_mode_annulus_detection_rate": float(summary["selected_detector_mode_annulus_detection_rate"]),
                "selected_detector_mode_annulus_detection_rate_wilson_lb": float(summary["selected_detector_mode_annulus_detection_rate_wilson_lb"]),
                "selected_detector_mode_annulus_fraction": float(summary["selected_detector_mode_annulus_fraction"]),
                "selected_detector_mode_annulus_mean_edge_norm": float(summary["selected_detector_mode_annulus_mean_edge_norm"]),
                "reference_operating_band": str(summary["reference_operating_band"]),
                "engineering_gate_passed": bool(summary["engineering_gate_passed"]),
                "strict_ok": bool(
                    bool(summary["engineering_gate_passed"])
                    and not bool(summary.get("na_cutoff_active"))
                    and str(summary.get("rho_physical_envelope_status")) == "within_envelope"
                ),
            }
        )
    return rows


def _run_task_tuple(args: tuple[tuple[int, int, int], Any, int, float, int]) -> list[dict[str, Any]]:
    route, particle, seed, shot_noise_scale, n_events = args
    return _build_case_rows(
        route=route,
        particle=particle,
        seed=seed,
        shot_noise_scale=shot_noise_scale,
        n_events=n_events,
    )


def _seed11_df(workers: int, n_events: int) -> pd.DataFrame:
    tasks = [
        (route, particle, SEEDS[0], shot_noise_scale, int(n_events))
        for shot_noise_scale in SHOT_NOISE_SCALES
        for route in ROUTES
        for particle in (_baseline_ev_particles() + _gold_particles())
    ]
    rows: list[dict[str, Any]] = []
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for batch_rows in executor.map(_run_task_tuple, tasks):
                rows.extend(batch_rows)
    else:
        for task in tasks:
            rows.extend(_run_task_tuple(task))
    return pd.DataFrame(rows)


def _route_summary(case_df: pd.DataFrame) -> pd.DataFrame:
    ev = case_df[case_df["particle_family"].eq("EV_sEV")].copy()
    rows: list[dict[str, Any]] = []
    for keys, group in ev.groupby(["shot_noise_scale", "seed", "normalization_view", "wavelength_nm", "width_nm", "depth_nm"], sort=True):
        shot_noise_scale, seed, normalization_view, wavelength_nm, width_nm, depth_nm = keys
        metrics = _weighted_metrics(group)
        rows.append(
            {
                "shot_noise_scale": float(shot_noise_scale),
                "seed": int(seed),
                "normalization_view": normalization_view,
                "wavelength_nm": int(wavelength_nm),
                "width_nm": int(width_nm),
                "depth_nm": int(depth_nm),
                "route_family_id": _route_family_id((int(wavelength_nm), int(width_nm), int(depth_nm))),
                **metrics,
                "reference_operating_band": group["reference_operating_band"].mode().iat[0],
                "mean_peak_margin_z": float(group["mean_peak_margin_z"].mean()),
            }
        )
    route_df = pd.DataFrame(rows)

    # depth ranks within width family
    route_df["selected_depth_rank"] = (
        route_df.groupby(["shot_noise_scale", "seed", "normalization_view", "wavelength_nm", "width_nm"])["weighted_selected_annulus_detection"]
        .rank(ascending=False, method="dense")
        .astype(int)
    )
    route_df["all_crossing_depth_rank"] = (
        route_df.groupby(["shot_noise_scale", "seed", "normalization_view", "wavelength_nm", "width_nm"])["weighted_all_crossing_detection"]
        .rank(ascending=False, method="dense")
        .astype(int)
    )
    return route_df


def _headline_rows(route_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, group in route_df.groupby(["shot_noise_scale", "seed", "normalization_view", "wavelength_nm"], sort=True):
        shot_noise_scale, seed, normalization_view, wavelength_nm = keys
        top = group.sort_values(["weighted_selected_annulus_detection", "mean_peak_margin_z"], ascending=[False, False]).iloc[0]
        rows.append(
            {
                "shot_noise_scale": float(shot_noise_scale),
                "seed": int(seed),
                "normalization_view": normalization_view,
                "wavelength_nm": int(wavelength_nm),
                "winner_wavelength": int(wavelength_nm),
                "winner_family_id": top["route_family_id"],
                "winner_route": f"{int(top['wavelength_nm'])}/{int(top['width_nm'])}x{int(top['depth_nm'])}",
                "winner_selected_metric": float(top["weighted_selected_annulus_detection"]),
                "reference_operating_band": top["reference_operating_band"],
            }
        )
    headline_df = pd.DataFrame(rows)
    cross_rows: list[dict[str, Any]] = []
    for keys, group in headline_df.groupby(["shot_noise_scale", "seed", "normalization_view"], sort=True):
        shot_noise_scale, seed, normalization_view = keys
        winners = {int(row["wavelength_nm"]): row for row in group.to_dict("records")}
        if set(winners) != {404, 660}:
            continue
        w404 = winners[404]
        w660 = winners[660]
        overall = w404 if w404["winner_selected_metric"] >= w660["winner_selected_metric"] else w660
        cross_rows.append(
            {
                "shot_noise_scale": float(shot_noise_scale),
                "seed": int(seed),
                "normalization_view": normalization_view,
                "winner_wavelength": int(overall["wavelength_nm"]),
                "winner_family_id": overall["winner_family_id"],
                "winner_route": overall["winner_route"],
                "band_404": w404["reference_operating_band"],
                "band_660": w660["reference_operating_band"],
            }
        )
    cross_df = pd.DataFrame(cross_rows)
    if not cross_df.empty:
        disagreement_map: dict[tuple[float, int], bool] = {}
        for (shot_noise_scale, seed), group in cross_df.groupby(["shot_noise_scale", "seed"], sort=True):
            winners_by_view = {
                str(row["normalization_view"]): int(row["winner_wavelength"])
                for row in group.to_dict("records")
            }
            if set(winners_by_view) == set(NORMALIZATION_VIEWS):
                disagreement_map[(float(shot_noise_scale), int(seed))] = (
                    winners_by_view["fixed_660_gold"] != winners_by_view["per_wavelength_gold"]
                )
        cross_df["views_disagree_on_winner_wavelength"] = [
            disagreement_map.get((float(row["shot_noise_scale"]), int(row["seed"])))
            for _, row in cross_df.iterrows()
        ]
    return cross_df


def _depth_span_rows(route_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, group in route_df.groupby(["shot_noise_scale", "seed", "normalization_view", "wavelength_nm"], sort=True):
        shot_noise_scale, seed, normalization_view, wavelength_nm = keys
        selected_winner = group.sort_values(["weighted_selected_annulus_detection", "mean_peak_margin_z"], ascending=[False, False]).iloc[0]
        selected_width = int(selected_winner["width_nm"])
        selected_group = group[group["width_nm"].eq(selected_width)]
        all_winner = group.sort_values(["weighted_all_crossing_detection", "mean_peak_margin_z"], ascending=[False, False]).iloc[0]
        all_width = int(all_winner["width_nm"])
        all_group = group[group["width_nm"].eq(all_width)]
        rows.append(
            {
                "shot_noise_scale": float(shot_noise_scale),
                "seed": int(seed),
                "normalization_view": normalization_view,
                "wavelength_nm": int(wavelength_nm),
                "selected_width_nm": selected_width,
                "all_crossing_width_nm": all_width,
                "depth_span_selected_annulus": float(selected_group["weighted_selected_annulus_detection"].max() - selected_group["weighted_selected_annulus_detection"].min()),
                "depth_span_all_crossing": float(all_group["weighted_all_crossing_detection"].max() - all_group["weighted_all_crossing_detection"].min()),
            }
        )
    return pd.DataFrame(rows)


def _depth_rank_seed_stability(route_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    route_df = cast(
        pd.DataFrame,
        route_df[route_df["shot_noise_scale"].isin(SHOT_NOISE_SCALES)].copy(),
    )
    records: list[dict[str, Any]] = []
    selected_stable = 0
    selected_total = 0
    all_stable = 0
    all_total = 0
    for (shot_noise_scale, normalization_view, wavelength_nm, width_nm), group in route_df.groupby(
        ["shot_noise_scale", "normalization_view", "wavelength_nm", "width_nm"],
        sort=True,
    ):
        for metric_face, metric_column in (
            ("selected_annulus", "weighted_selected_annulus_detection"),
            ("all_crossing", "weighted_all_crossing_detection"),
        ):
            per_seed_top_depths: list[int] = []
            for seed, seed_group in group.groupby("seed", sort=True):
                top = seed_group.sort_values([metric_column, "mean_peak_margin_z"], ascending=[False, False]).iloc[0]
                per_seed_top_depths.append(int(top["depth_nm"]))
            seed_stable = len(set(per_seed_top_depths)) == 1
            records.append(
                {
                    "shot_noise_scale": float(shot_noise_scale),
                    "normalization_view": normalization_view,
                    "wavelength_nm": int(wavelength_nm),
                    "width_nm": int(width_nm),
                    "metric_face": metric_face,
                    "per_seed_top_depths": ",".join(str(depth) for depth in per_seed_top_depths),
                    "seed_stable": bool(seed_stable),
                }
            )
            if metric_face == "selected_annulus":
                selected_total += 1
                selected_stable += int(seed_stable)
            else:
                all_total += 1
                all_stable += int(seed_stable)
    return pd.DataFrame(records), {
        "selected_stable": selected_stable,
        "selected_total": selected_total,
        "all_crossing_stable": all_stable,
        "all_crossing_total": all_total,
    }


def _promoted_shots(headline_df: pd.DataFrame) -> set[float]:
    baseline = headline_df[headline_df["shot_noise_scale"].eq(BASELINE_SHOT)]
    promoted: set[float] = set()
    for shot in SHOT_NOISE_SCALES:
        if shot == BASELINE_SHOT:
            continue
        compare = headline_df[headline_df["shot_noise_scale"].eq(shot)]
        for view in NORMALIZATION_VIEWS:
            b = baseline[baseline["normalization_view"].eq(view)]
            c = compare[compare["normalization_view"].eq(view)]
            if b.empty or c.empty:
                continue
            if (
                tuple(sorted(c["winner_wavelength"].unique().tolist())) != tuple(sorted(b["winner_wavelength"].unique().tolist()))
                or tuple(sorted(c["winner_family_id"].unique().tolist())) != tuple(sorted(b["winner_family_id"].unique().tolist()))
                or tuple(sorted(c["band_404"].unique().tolist())) != tuple(sorted(b["band_404"].unique().tolist()))
                or tuple(sorted(c["band_660"].unique().tolist())) != tuple(sorted(b["band_660"].unique().tolist()))
            ):
                promoted.add(float(shot))
    return promoted


def _promoted_df(shots: set[float], workers: int, n_events: int) -> pd.DataFrame:
    if not shots:
        return pd.DataFrame()
    tasks = [
        (route, particle, seed, shot_noise_scale, int(n_events))
        for shot_noise_scale in sorted(shots)
        for seed in SEEDS[1:]
        for route in ROUTES
        for particle in (_baseline_ev_particles() + _gold_particles())
    ]
    rows: list[dict[str, Any]] = []
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for batch_rows in executor.map(_run_task_tuple, tasks):
                rows.extend(batch_rows)
    else:
        for task in tasks:
            rows.extend(_run_task_tuple(task))
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run report 148 T3 noise-regime screening on route A.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR_DEFAULT)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--n-events", type=int, default=2000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    seed11_df = _seed11_df(int(args.workers), int(args.n_events))
    baseline_extra_df = _promoted_df({BASELINE_SHOT}, int(args.workers), int(args.n_events))
    route_seed11 = _route_summary(seed11_df)
    headline_seed11 = _headline_rows(route_seed11)
    promoted_shots = _promoted_shots(headline_seed11)
    promoted_df = _promoted_df(promoted_shots, int(args.workers), int(args.n_events))
    case_df = pd.concat([seed11_df, baseline_extra_df, promoted_df], ignore_index=True)
    route_df = _route_summary(case_df)
    headline_df = _headline_rows(route_df)
    depth_df = _depth_span_rows(route_df)
    stability_df, stability_counts = _depth_rank_seed_stability(route_df)

    case_df.to_csv(output_dir / "report148_t3_case_rows.csv", index=False)
    route_df.to_csv(output_dir / "report148_t3_route_rows.csv", index=False)
    headline_df.to_csv(output_dir / "report148_t3_headline_rows.csv", index=False)
    depth_df.to_csv(output_dir / "report148_t3_depth_span_rows.csv", index=False)
    stability_df.to_csv(output_dir / "report148_t3_depth_rank_seed_stability.csv", index=False)

    summary_rows: list[dict[str, Any]] = []
    for shot_noise_scale, group in headline_df.groupby("shot_noise_scale", sort=True):
        vote_counts = {}
        for view in NORMALIZATION_VIEWS:
            sub = group[group["normalization_view"].eq(view)]
            vote_counts[view] = (
                sub["winner_wavelength"]
                .value_counts()
                .sort_index()
                .to_dict()
            )
        summary_rows.append(
            {
                "shot_noise_scale": float(shot_noise_scale),
                "seed_count": int(group["seed"].nunique()),
                "winner_wavelengths": sorted(group["winner_wavelength"].unique().tolist()),
                "winner_families": sorted(group["winner_family_id"].unique().tolist()),
                "bands_404": sorted(group["band_404"].unique().tolist()),
                "bands_660": sorted(group["band_660"].unique().tolist()),
                "fixed_660_gold_winner_wavelength_vote_counts": str(vote_counts["fixed_660_gold"]),
                "per_wavelength_gold_winner_wavelength_vote_counts": str(vote_counts["per_wavelength_gold"]),
                "views_disagree_on_winner_wavelength_any_seed": bool(group["views_disagree_on_winner_wavelength"].any()),
            }
        )
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(output_dir / "report148_t3_noise_summary.csv", index=False)

    manifest = {
        "generated_at": _utc_now_iso(),
        "output_dir": str(output_dir),
        "route_id": DETECTOR_ROUTE_ID,
        "gauge_mode": GAUGE_MODE,
        "n_events": int(args.n_events),
        "workers": int(args.workers),
        "shot_noise_scales": list(SHOT_NOISE_SCALES),
        "promoted_shot_noise_scales": sorted(promoted_shots),
        "seed11_only_rows": int(len(seed11_df)),
        "baseline_extra_rows": int(len(baseline_extra_df)),
        "promoted_rows": int(len(promoted_df)),
        "distinct_physical_events": int((len(seed11_df) + len(baseline_extra_df) + len(promoted_df)) * int(args.n_events) / 2),
        "case_row_events": int((len(seed11_df) + len(baseline_extra_df) + len(promoted_df)) * int(args.n_events)),
        **stability_counts,
    }
    write_json_file(output_dir / "report148_t3_manifest.json", manifest)


if __name__ == "__main__":
    main()
