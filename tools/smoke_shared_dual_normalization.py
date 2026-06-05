#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from copy import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.config import BASELINE_PARTICLE, THETA_GRID_RAD, medium_for_particle, particle_from_name  # noqa: E402
from nodi_simulator.parameter_sweep import run_single_case_batch  # noqa: E402
from nodi_simulator.utils import compute_baseline_normalization_per_wavelength  # noqa: E402
from tools._common import json_safe, write_json_file  # noqa: E402
from tools import lens_b_ev_gold_fullgrid_runner as runner  # noqa: E402


LANES = ("fixed_660_gold", "per_wavelength_gold")
COMPARE_FIELDS = (
    "case_random_seed",
    "case_random_identity",
    "all_crossing_detection_rate",
    "selected_detector_mode_annulus_detection_rate",
    "selected_detector_mode_annulus_fraction",
    "mean_peak_height",
    "mean_local_snr",
    "stable_detection_rate",
)


def _pick_particles(scope: runner.SourceScope, requested: list[str] | None) -> list[str]:
    if requested:
        missing = sorted(set(requested) - set(scope.particle_names))
        if missing:
            raise ValueError(f"requested particles are not in source scope: {missing}")
        return list(requested)
    preferred = [
        "gold_40nm",
        "exosome_biomimetic_corona_nominal_100nm",
        "gold_40nm_diameter",
        "exosome_biomimetic_100nm",
        "exosome_100nm",
    ]
    selected: list[str] = []
    for name in preferred:
        if name in scope.particle_names and name not in selected:
            selected.append(name)
    if not selected:
        selected.append(scope.gold_particle_names[0])
    if len(selected) == 1:
        for name in scope.ev_particle_names:
            if name not in selected:
                selected.append(name)
                break
    return selected[:2]


def _pick_routes(scope: runner.SourceScope, requested: list[str] | None, count: int) -> list[tuple[int, int, int]]:
    if requested:
        routes: list[tuple[int, int, int]] = []
        allowed = set(scope.routes)
        for item in requested:
            parts = tuple(int(piece) for piece in item.split(","))
            if len(parts) != 3:
                raise ValueError(f"route must be wavelength,width,depth: {item}")
            if parts not in allowed:
                raise ValueError(f"requested route is not in source scope: {parts}")
            routes.append(parts)
        return routes
    preferred = [(660, 800, 1400), (404, 800, 1400), (660, 500, 500)]
    routes = [route for route in preferred if route in set(scope.routes)]
    if routes:
        return routes[:count]
    return scope.routes[:count]


def _summary_by_particle(results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for result in results:
        particle_name = str(result.get("particle_name"))
        summary = dict(result.get("summary", {}))
        intrinsic = result.get("intrinsic", {})
        if not isinstance(intrinsic, dict):
            intrinsic = {}
        summary.update(
            {
                "particle_name": particle_name,
                "E_sca_ref": result.get("E_sca_ref", intrinsic.get("E_sca_ref")),
                "E_sca_normalized": result.get(
                    "E_sca_normalized",
                    intrinsic.get("E_sca_unit_normalized"),
                ),
            }
        )
        out[particle_name] = summary
    return out


def _run_route_lane(
    *,
    route: tuple[int, int, int],
    particle_names: list[str],
    base_cfg: Any,
    optical_template: Any,
    normalization_lane: str,
) -> tuple[list[dict[str, Any]], float]:
    cfg = runner._cfg_for_normalization_lane(base_cfg, normalization_lane)
    particles = [particle_from_name(name) for name in particle_names]
    start = time.perf_counter()
    results = runner._run_one_route(
        route=route,
        particles=particles,
        cfg=cfg,
        optical_template=optical_template,
        workers=1,
        normalization_lane=normalization_lane,
    )
    elapsed = time.perf_counter() - start
    return results, elapsed


def _per_wavelength_ref(
    *,
    route: tuple[int, int, int],
    cfg: Any,
    optical_template: Any,
    medium: Any,
) -> float:
    wavelength_nm, width_nm, depth_nm = route
    optical = copy(optical_template)
    optical.wavelength_m = float(wavelength_nm) * 1e-9
    baseline_channel = runner.lane.case_baseline_channel(width_nm, depth_nm)
    refs = compute_baseline_normalization_per_wavelength(
        BASELINE_PARTICLE,
        medium,
        optical,
        np.array([float(wavelength_nm) * 1e-9], dtype=float),
        THETA_GRID_RAD,
        channel=baseline_channel,
        sim_cfg=cfg,
    )
    return float(refs[float(wavelength_nm) * 1e-9])


def _direct_batch_pair_smoke(
    *,
    route: tuple[int, int, int],
    particle_names: list[str],
    base_cfg: Any,
    optical_template: Any,
) -> tuple[dict[str, dict[str, dict[str, Any]]], float]:
    wavelength_nm, width_nm, depth_nm = route
    channel = runner.lane.case_baseline_channel(width_nm, depth_nm)
    optical = copy(optical_template)
    optical.wavelength_m = float(wavelength_nm) * 1e-9
    cfg_by_lane = {
        lane_name: runner._cfg_for_normalization_lane(base_cfg, lane_name)
        for lane_name in LANES
    }
    fixed_ref = runner._fixed_660_e_sca_ref(
        width_nm=width_nm,
        depth_nm=depth_nm,
        cfg=cfg_by_lane["fixed_660_gold"],
        optical_template=optical_template,
    )
    intrinsic_cache: dict[Any, Any] = {}
    reference_cache: dict[Any, Any] = {}
    collection_operator_cache: dict[Any, Any] = {}
    output: dict[str, dict[str, dict[str, Any]]] = {}
    start = time.perf_counter()
    for particle_name in particle_names:
        particle = particle_from_name(particle_name)
        medium = medium_for_particle(particle)
        per_ref = _per_wavelength_ref(
            route=route,
            cfg=cfg_by_lane["per_wavelength_gold"],
            optical_template=optical_template,
            medium=medium,
        )
        output[particle_name] = {}
        for lane_name, e_ref in (
            ("fixed_660_gold", fixed_ref),
            ("per_wavelength_gold", per_ref),
        ):
            batch = run_single_case_batch(
                particle,
                medium,
                channel,
                optical,
                cfg_by_lane[lane_name],
                e_ref,
                THETA_GRID_RAD,
                retain_event_traces=False,
                stream_summary_only=True,
                intrinsic_cache=intrinsic_cache,
                reference_cache=reference_cache,
                collection_operator_cache=collection_operator_cache,
            )
            summary = dict(batch.get("summary", {}))
            summary["E_sca_ref"] = float(e_ref)
            output[particle_name][lane_name] = summary
    elapsed = time.perf_counter() - start
    return output, elapsed


def _comparison_rows(
    *,
    route: tuple[int, int, int],
    lane_outputs: dict[str, dict[str, dict[str, Any]]],
    direct_outputs: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    particles = sorted(set(lane_outputs["fixed_660_gold"]) & set(lane_outputs["per_wavelength_gold"]))
    for particle_name in particles:
        fixed = lane_outputs["fixed_660_gold"][particle_name]
        per = lane_outputs["per_wavelength_gold"][particle_name]
        same_seed = fixed.get("case_random_seed") == per.get("case_random_seed")
        same_identity = fixed.get("case_random_identity") == per.get("case_random_identity")
        row: dict[str, Any] = {
            "route": list(route),
            "particle_name": particle_name,
            "same_case_random_seed_between_lanes": bool(same_seed),
            "same_case_random_identity_between_lanes": bool(same_identity),
            "fixed_E_sca_ref": fixed.get("E_sca_ref"),
            "per_wavelength_E_sca_ref": per.get("E_sca_ref"),
            "fixed_E_sca_normalized": fixed.get("E_sca_normalized"),
            "per_wavelength_E_sca_normalized": per.get("E_sca_normalized"),
        }
        for field in COMPARE_FIELDS:
            row[f"fixed_{field}"] = fixed.get(field)
            row[f"per_wavelength_{field}"] = per.get(field)
        for lane_name in LANES:
            direct = direct_outputs.get(particle_name, {}).get(lane_name, {})
            one_lane = lane_outputs[lane_name][particle_name]
            for field in (
                "case_random_seed",
                "case_random_identity",
                "all_crossing_detection_rate",
                "selected_detector_mode_annulus_detection_rate",
                "mean_peak_height",
            ):
                row[f"{lane_name}_direct_matches_one_lane_{field}"] = (
                    direct.get(field) == one_lane.get(field)
                )
        rows.append(row)
    return rows


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    scope = runner.load_and_validate_source(Path(args.route_source), particle_scope="ev_gold")
    particle_names = _pick_particles(scope, args.particle)
    routes = _pick_routes(scope, args.route, int(args.route_count))
    base_cfg, optical_template = runner.build_frozen_b_cfg(int(args.n_events), int(args.seed))
    timings: list[dict[str, Any]] = []
    comparison_records: list[dict[str, Any]] = []
    failures: list[str] = []
    for route in routes:
        lane_outputs: dict[str, dict[str, dict[str, Any]]] = {}
        lane_timings: dict[str, float] = {}
        for lane_name in LANES:
            results, elapsed = _run_route_lane(
                route=route,
                particle_names=particle_names,
                base_cfg=base_cfg,
                optical_template=optical_template,
                normalization_lane=lane_name,
            )
            lane_outputs[lane_name] = _summary_by_particle(results)
            lane_timings[lane_name] = elapsed
        direct_outputs, direct_elapsed = _direct_batch_pair_smoke(
            route=route,
            particle_names=particle_names,
            base_cfg=base_cfg,
            optical_template=optical_template,
        )
        comparison_records.extend(
            _comparison_rows(
                route=route,
                lane_outputs=lane_outputs,
                direct_outputs=direct_outputs,
            )
        )
        separate_total = sum(lane_timings.values())
        timings.append(
            {
                "route": list(route),
                "particle_count": len(particle_names),
                "n_events": int(args.n_events),
                "fixed_660_gold_s": lane_timings["fixed_660_gold"],
                "per_wavelength_gold_s": lane_timings["per_wavelength_gold"],
                "separate_one_lane_total_s": separate_total,
                "paired_direct_with_shared_intrinsic_cache_s": direct_elapsed,
                "paired_direct_ratio_vs_separate": (
                    direct_elapsed / separate_total if separate_total > 0 else None
                ),
            }
        )
    for row in comparison_records:
        if not row["same_case_random_seed_between_lanes"]:
            failures.append(f"RNG seed mismatch for {row['route']} {row['particle_name']}")
        if not row["same_case_random_identity_between_lanes"]:
            failures.append(f"case identity mismatch for {row['route']} {row['particle_name']}")
    comparison_frame = pd.DataFrame(comparison_records)
    comparison_frame.to_csv(output_dir / "shared_dual_normalization_comparison.csv", index=False)
    timing_frame = pd.DataFrame(timings)
    timing_frame.to_csv(output_dir / "shared_dual_normalization_timings.csv", index=False)
    summary = {
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "route_count": len(routes),
        "particles": particle_names,
        "seed": int(args.seed),
        "n_events": int(args.n_events),
        "timing_summary": {
            "separate_one_lane_total_s": float(timing_frame["separate_one_lane_total_s"].sum()),
            "paired_direct_with_shared_intrinsic_cache_s": float(
                timing_frame["paired_direct_with_shared_intrinsic_cache_s"].sum()
            ),
            "paired_direct_ratio_vs_separate_mean": float(
                timing_frame["paired_direct_ratio_vs_separate"].mean()
            ),
        },
        "interpretation": {
            "event_stream_shared_feasibility": (
                "case_random_seed and case_random_identity match across lanes when "
                "route, particle, seed, and n_events match"
            ),
            "production_shared_event_status": (
                "not yet production single-pass; this smoke uses current one-lane "
                "outputs plus a direct paired batch feasibility path"
            ),
            "optimization_hint": (
                "true speedup requires factoring event trajectory/noise generation "
                "below run_single_case_batch; same-process cache sharing alone is "
                "only a partial optimization"
            ),
        },
    }
    write_json_file(output_dir / "shared_dual_normalization_smoke_summary.json", summary)
    print(json.dumps(json_safe(summary), indent=2, sort_keys=True))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke-test shared-event feasibility for dual normalization views."
    )
    parser.add_argument(
        "--route-source",
        default="results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv",
    )
    parser.add_argument("--output-dir", default="tmp/shared_dual_normalization_smoke_20260518")
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--n-events", type=int, default=20)
    parser.add_argument("--route-count", type=int, default=1)
    parser.add_argument("--route", action="append", help="Route as wavelength,width,depth.")
    parser.add_argument("--particle", action="append", help="Particle name. Repeatable.")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
