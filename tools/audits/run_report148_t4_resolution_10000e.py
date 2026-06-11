#!/usr/bin/env python3
# pyright: reportAttributeAccessIssue=false, reportCallIssue=false, reportArgumentType=false, reportGeneralTypeIssues=false
from __future__ import annotations

import argparse
import hashlib
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.parameter_sweep import wilson_lower_bound, wilson_upper_bound  # noqa: E402
from tools._common import write_json_file  # noqa: E402
from tools.audits import ev_size_weighted_route_analysis as route_analysis  # noqa: E402
from tools.audits.run_report148_t4_ac_ri import (  # noqa: E402
    CaseTask,
    _particle_metadata,
    _run_case_task,
    build_ev_particles,
    build_gold_particles,
)


OUTPUT_DIR_DEFAULT = Path("results/audits") / f"report148_t4_resolution_10000e_{datetime.now().strftime('%Y%m%d')}"
UNRESOLVED_COMBOS = (
    ("surface_loaded_bright_2021", 1.36, "absent"),
    ("surface_loaded_bright_2021", 1.36, "nominal"),
    ("surface_loaded_bright_2021", 1.36, "protein_rich"),
    ("surface_loaded_bright_2021", 1.38, "absent"),
    ("surface_loaded_bright_2021", 1.40, "absent"),
    ("surface_loaded_bright_2021", 1.40, "nominal"),
    ("surface_loaded_bright_2021", 1.40, "protein_rich"),
)
FOCUSED_ROUTES = (
    (404, 500, 700),
    (404, 500, 1300),
    (404, 600, 1300),
    (660, 800, 900),
    (660, 800, 1300),
)
DETECTOR_ROUTE_IDS = ("A_hybrid", "C_collapsed_coherent")
SEEDS = (11, 22, 33)
PRIOR_NAME = "sharp_msc_sev_empirical"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _filter_ev_particles() -> list[Any]:
    selected: list[Any] = []
    for particle in build_ev_particles():
        meta = _particle_metadata(particle)
        key = (meta["preset_name"], float(meta["core_n_real"]), meta["corona_label"])
        if key in UNRESOLVED_COMBOS:
            selected.append(particle)
    return selected


def _build_tasks(n_events: int) -> list[CaseTask]:
    particles = _filter_ev_particles() + build_gold_particles()
    return [
        CaseTask(
            route=route,
            particle=particle,
            seed=seed,
            detector_route_id=route_id,
            n_events=int(n_events),
        )
        for route_id in DETECTOR_ROUTE_IDS
        for seed in SEEDS
        for route in FOCUSED_ROUTES
        for particle in particles
    ]


def _run_tasks(tasks: list[CaseTask], workers: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for batch_rows in executor.map(_run_case_task, tasks):
                rows.extend(batch_rows)
    else:
        for task in tasks:
            rows.extend(_run_case_task(task))
    return pd.DataFrame(rows)


def _weights_for_group(group: pd.DataFrame) -> dict[float, float]:
    diameters = sorted(
        pd.to_numeric(group["particle_diameter_nm"], errors="coerce")
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )
    prior = route_analysis.normalize_prior(route_analysis.build_priors(diameters)[PRIOR_NAME])
    return {float(key): float(value) for key, value in prior.items()}


def _weighted_route_metrics(route_rows: pd.DataFrame) -> dict[str, float]:
    weights = _weights_for_group(route_rows)
    weighted_detection = 0.0
    weighted_lb = 0.0
    weighted_ub = 0.0
    for _, row in route_rows.iterrows():
        weight = weights[float(int(row["particle_diameter_nm"]))]
        weighted_detection += weight * float(row["selected_detector_mode_annulus_detection_rate"])
        n_detected = int(row["selected_detector_mode_annulus_n_detected"])
        n_events = int(row["selected_detector_mode_annulus_n_events"])
        weighted_lb += weight * wilson_lower_bound(n_detected, n_events)
        weighted_ub += weight * wilson_upper_bound(n_detected, n_events)
    return {
        "weighted_selected_annulus_detection": weighted_detection,
        "weighted_selected_annulus_detection_wilson_lb": weighted_lb,
        "weighted_selected_annulus_detection_wilson_ub": weighted_ub,
    }


def _route_winner_metrics(case_df: pd.DataFrame) -> pd.DataFrame:
    ev = case_df[case_df["particle_family"].eq("EV_sEV")].copy()
    rows: list[dict[str, Any]] = []
    for keys, group in ev.groupby(
        ["detector_route_id", "seed", "preset_name", "core_n_real", "corona_label", "normalization_view", "wavelength_nm", "width_nm", "depth_nm"],
        sort=True,
    ):
        detector_route_id, seed, preset_name, core_n_real, corona_label, normalization_view, wavelength_nm, width_nm, depth_nm = keys
        metrics = _weighted_route_metrics(group)
        rows.append(
            {
                "detector_route_id": detector_route_id,
                "seed": int(seed),
                "preset_name": preset_name,
                "core_n_real": float(core_n_real),
                "corona_label": corona_label,
                "normalization_view": normalization_view,
                "wavelength_nm": int(wavelength_nm),
                "width_nm": int(width_nm),
                "depth_nm": int(depth_nm),
                "route_family_id": str(group["route_family_id"].iloc[0]),
                **metrics,
            }
        )
    route_df = pd.DataFrame(rows)
    winners: list[dict[str, Any]] = []
    for keys, group in route_df.groupby(
        ["detector_route_id", "seed", "preset_name", "core_n_real", "corona_label", "normalization_view", "wavelength_nm"],
        sort=True,
    ):
        ranked = group.sort_values(
            ["weighted_selected_annulus_detection", "weighted_selected_annulus_detection_wilson_lb"],
            ascending=[False, False],
        )
        top = ranked.iloc[0]
        winners.append(top.to_dict())
    return pd.DataFrame(winners)


def _resolution_rows(winner_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keys, group in winner_df.groupby(
        ["detector_route_id", "preset_name", "core_n_real", "corona_label"],
        sort=True,
    ):
        route_id, preset_name, core_n_real, corona_label = keys
        per = group[group["normalization_view"].eq("per_wavelength_gold")].copy()
        if per.empty:
            continue
        winners_by_seed: dict[int, dict[int, dict[str, Any]]] = {}
        for _, row in per.iterrows():
            winners_by_seed.setdefault(int(row["seed"]), {})[int(row["wavelength_nm"])] = row.to_dict()
        winner_labels: list[str] = []
        margin_values: list[float] = []
        overlap_flags: list[bool] = []
        for seed, seed_rows in sorted(winners_by_seed.items()):
            if set(seed_rows) != {404, 660}:
                continue
            row_404 = seed_rows[404]
            row_660 = seed_rows[660]
            margin = float(row_404["weighted_selected_annulus_detection"]) - float(row_660["weighted_selected_annulus_detection"])
            overlap = not (
                float(row_404["weighted_selected_annulus_detection_wilson_lb"]) > float(row_660["weighted_selected_annulus_detection_wilson_ub"])
                or float(row_660["weighted_selected_annulus_detection_wilson_lb"]) > float(row_404["weighted_selected_annulus_detection_wilson_ub"])
            )
            winner_labels.append("404" if margin > 0 else "660")
            margin_values.append(margin)
            overlap_flags.append(bool(overlap))
        seed_stable = len(set(winner_labels)) == 1 if winner_labels else False
        if seed_stable:
            resolution_class = "ri_dependent_deterministic"
        elif any(overlap_flags):
            resolution_class = "genuine_near_tie"
        else:
            resolution_class = "still_unresolved"
        rows.append(
            {
                "detector_route_id": route_id,
                "preset_name": preset_name,
                "core_n_real": float(core_n_real),
                "corona_label": corona_label,
                "seed_count": len(winner_labels),
                "per_wavelength_seed_winners": ",".join(winner_labels),
                "seed_stable_at_10000e": bool(seed_stable),
                "per_wavelength_404_vs_660_margin_min": min(margin_values) if margin_values else None,
                "per_wavelength_404_vs_660_margin_median": (
                    float(pd.Series(margin_values).median()) if margin_values else None
                ),
                "per_wavelength_404_vs_660_margin_max": max(margin_values) if margin_values else None,
                "per_wavelength_wilson_overlap_any": bool(any(overlap_flags)) if overlap_flags else None,
                "ev_ri_resolution_class": resolution_class,
            }
        )
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run focused 10000e resolution check for 7 unresolved T4 RI combos.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR_DEFAULT)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--n-events", type=int, default=10000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    case_df = _run_tasks(_build_tasks(int(args.n_events)), int(args.workers))
    winner_df = _route_winner_metrics(case_df)
    resolution_df = _resolution_rows(winner_df)

    case_df.to_csv(output_dir / "report148_t4_resolution_case_rows.csv", index=False)
    winner_df.to_csv(output_dir / "report148_t4_resolution_winner_rows.csv", index=False)
    resolution_df.to_csv(output_dir / "report148_t4_resolution_summary.csv", index=False)

    manifest = {
        "generated_at": _utc_now_iso(),
        "output_dir": str(output_dir),
        "n_events": int(args.n_events),
        "workers": int(args.workers),
        "detector_route_ids": list(DETECTOR_ROUTE_IDS),
        "focused_routes": [list(route) for route in FOCUSED_ROUTES],
        "unresolved_combos": [
            {"preset_name": combo[0], "core_n_real": combo[1], "corona_label": combo[2]}
            for combo in UNRESOLVED_COMBOS
        ],
    }
    write_json_file(output_dir / "report148_t4_resolution_manifest.json", manifest)


if __name__ == "__main__":
    main()
