"""
dashboard/estimate_precompute_runtime.py

Benchmark a small representative subset on another machine, then extrapolate
the runtime for larger precompute targets.

Typical usage:
    python -m nodi_simulator.dashboard.estimate_precompute_runtime \
        --target-grid ev_design \
        --target-particle-profile full_range_biomimetic_exosome_with_anchors
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import sys
import time

import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for candidate in (PROJECT_ROOT,):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from nodi_simulator import run_parameter_sweep
from nodi_simulator.dashboard.config import (
    BASELINE_PARTICLE,
    GRID_CONFIGS,
    MEDIUM,
    OPTICAL_TEMPLATE,
    PRECOMPUTE_PROFILES,
    THETA_GRID_RAD,
    get_precompute_particles,
    get_precompute_profile,
    medium_for_particle,
)
from nodi_simulator.dashboard.precompute import build_precompute_sim_cfg
from nodi_simulator.optional_acceleration import warn_numba_unavailable


def _get_numba_info() -> dict:
    try:
        import numba  # type: ignore
    except (ImportError, OSError, RuntimeError):
        warn_numba_unavailable("precompute runtime estimates")
        return {"available": False, "version": None}
    return {"available": True, "version": getattr(numba, "__version__", None)}


def _pick_evenly_spaced(values: list, n: int) -> list:
    """Pick up to n representative values across an ordered list."""
    if n <= 0:
        raise ValueError("sample size must be positive")
    if len(values) <= n:
        return list(values)
    indices = np.linspace(0, len(values) - 1, n)
    picked = []
    used = set()
    for idx in indices:
        i = int(round(float(idx)))
        if i not in used:
            picked.append(values[i])
            used.add(i)
    return picked


def _seconds_to_readable(seconds: float) -> str:
    seconds = float(seconds)
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes = seconds / 60.0
    if minutes < 60:
        return f"{minutes:.1f} min"
    hours = minutes / 60.0
    if hours < 48:
        return f"{hours:.2f} h"
    days = hours / 24.0
    return f"{days:.2f} d"


def _write_json_atomic(path: str, payload: dict) -> None:
    """Atomically replace a JSON report, rejecting NaN/Inf payloads."""
    output_dir = os.path.dirname(os.path.abspath(path))
    os.makedirs(output_dir, exist_ok=True)
    tmp_path = f"{path}.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, allow_nan=False)
        os.replace(tmp_path, path)
    except (OSError, TypeError, ValueError):
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _build_benchmark_subset(
    particle_profile: str,
    grid_name: str,
    sample_particles: int,
    sample_widths: int,
    sample_depths: int,
    sample_wavelengths: int,
):
    profile = get_precompute_profile(particle_profile)
    grid = GRID_CONFIGS[grid_name]

    particles_all = get_precompute_particles(particle_profile)
    widths_all = list(grid["width_list_m"])
    depths_all = list(grid["depth_list_m"])
    wavelengths_all = list(grid["wavelength_list_m"])

    particles = _pick_evenly_spaced(particles_all, sample_particles)
    widths = np.array(_pick_evenly_spaced(widths_all, sample_widths), dtype=float)
    depths = np.array(_pick_evenly_spaced(depths_all, sample_depths), dtype=float)
    wavelengths = np.array(_pick_evenly_spaced(wavelengths_all, sample_wavelengths), dtype=float)

    return {
        "profile": profile,
        "particles": particles,
        "widths": widths,
        "depths": depths,
        "wavelengths": wavelengths,
    }


def estimate_runtime(
    *,
    target_grid: str,
    target_particle_profile: str,
    benchmark_grid: str | None = None,
    benchmark_particle_profile: str | None = None,
    benchmark_events: int | None = None,
    sample_particles: int = 4,
    sample_widths: int = 2,
    sample_depths: int = 2,
    sample_wavelengths: int = 4,
    verbose: bool = False,
    n_workers: int | None = 1,
) -> dict:
    benchmark_grid = benchmark_grid or target_grid
    benchmark_particle_profile = benchmark_particle_profile or target_particle_profile

    benchmark_subset = _build_benchmark_subset(
        particle_profile=benchmark_particle_profile,
        grid_name=benchmark_grid,
        sample_particles=sample_particles,
        sample_widths=sample_widths,
        sample_depths=sample_depths,
        sample_wavelengths=sample_wavelengths,
    )

    target_profile = get_precompute_profile(target_particle_profile)
    target_particles = get_precompute_particles(target_particle_profile)
    benchmark_grid_cfg = GRID_CONFIGS[benchmark_grid]
    target_grid_cfg = GRID_CONFIGS[target_grid]
    benchmark_events_per_case = (
        int(benchmark_events)
        if benchmark_events is not None
        else int(benchmark_grid_cfg["n_events"])
    )
    target_events_per_case = int(target_grid_cfg["n_events"])

    sim_cfg = build_precompute_sim_cfg(benchmark_grid)
    sim_cfg.n_events = benchmark_events_per_case

    benchmark_case_count = (
        len(benchmark_subset["particles"])
        * len(benchmark_subset["widths"])
        * len(benchmark_subset["depths"])
        * len(benchmark_subset["wavelengths"])
    )
    benchmark_event_count = benchmark_case_count * benchmark_events_per_case

    t0 = time.time()
    results = run_parameter_sweep(
        particle_types=benchmark_subset["particles"],
        medium=MEDIUM,
        medium_resolver=medium_for_particle,
        width_list_m=benchmark_subset["widths"],
        depth_list_m=benchmark_subset["depths"],
        wavelength_list_m=benchmark_subset["wavelengths"],
        optical_template=OPTICAL_TEMPLATE,
        sim_cfg=sim_cfg,
        theta_grid_rad=THETA_GRID_RAD,
        baseline_particle=BASELINE_PARTICLE,
        verbose=verbose,
        n_workers=n_workers,
    )
    elapsed_s = time.time() - t0

    target_case_count = (
        len(target_particles)
        * len(target_grid_cfg["width_list_m"])
        * len(target_grid_cfg["depth_list_m"])
        * len(target_grid_cfg["wavelength_list_m"])
    )
    target_event_count = target_case_count * target_events_per_case

    cases_per_second = benchmark_case_count / elapsed_s if elapsed_s > 0 else math.inf
    events_per_second = benchmark_event_count / elapsed_s if elapsed_s > 0 else math.inf
    estimated_seconds = target_event_count / events_per_second if events_per_second > 0 else math.inf
    numba_info = _get_numba_info()

    return {
        "machine": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "python_executable": sys.executable,
            "cpu_count": os.cpu_count(),
            "numba_available": numba_info["available"],
            "numba_version": numba_info["version"],
        },
        "benchmark": {
            "grid": benchmark_grid,
            "particle_profile": benchmark_particle_profile,
            "sample_particles": len(benchmark_subset["particles"]),
            "sample_widths": len(benchmark_subset["widths"]),
            "sample_depths": len(benchmark_subset["depths"]),
            "sample_wavelengths": len(benchmark_subset["wavelengths"]),
            "cases": benchmark_case_count,
            "events_per_case": benchmark_events_per_case,
            "total_events": benchmark_event_count,
            "elapsed_seconds": elapsed_s,
            "cases_per_second": cases_per_second,
            "events_per_second": events_per_second,
            "results_returned": len(results),
        },
        "target": {
            "grid": target_grid,
            "particle_profile": target_particle_profile,
            "profile_label": target_profile["label"],
            "particles": len(target_particles),
            "widths": len(target_grid_cfg["width_list_m"]),
            "depths": len(target_grid_cfg["depth_list_m"]),
            "wavelengths": len(target_grid_cfg["wavelength_list_m"]),
            "cases": target_case_count,
            "events_per_case": target_events_per_case,
            "total_events": target_event_count,
            "estimated_seconds": estimated_seconds,
            "estimated_readable": _seconds_to_readable(estimated_seconds),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark a small subset and estimate full precompute runtime."
    )
    parser.add_argument("--target-grid", default="ev_design", choices=sorted(GRID_CONFIGS))
    parser.add_argument(
        "--target-particle-profile",
        default="full_range_biomimetic_exosome_with_anchors",
        choices=sorted(PRECOMPUTE_PROFILES),
    )
    parser.add_argument(
        "--benchmark-grid",
        default=None,
        choices=sorted(GRID_CONFIGS),
    )
    parser.add_argument(
        "--benchmark-particle-profile",
        default=None,
        choices=sorted(PRECOMPUTE_PROFILES),
    )
    parser.add_argument(
        "--benchmark-events",
        type=int,
        default=None,
        help="Override event count during the benchmark run. "
        "Target estimate will still use the target grid's official n_events.",
    )
    parser.add_argument("--sample-particles", type=int, default=4)
    parser.add_argument("--sample-widths", type=int, default=2)
    parser.add_argument("--sample-depths", type=int, default=2)
    parser.add_argument("--sample-wavelengths", type=int, default=4)
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Worker process count for the benchmark run. Use 0 for all logical CPUs.",
    )
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--output-json",
        default=None,
        help="Optional path to save the estimate report as JSON.",
    )
    args = parser.parse_args()

    report = estimate_runtime(
        target_grid=args.target_grid,
        target_particle_profile=args.target_particle_profile,
        benchmark_grid=args.benchmark_grid,
        benchmark_particle_profile=args.benchmark_particle_profile,
        benchmark_events=args.benchmark_events,
        sample_particles=args.sample_particles,
        sample_widths=args.sample_widths,
        sample_depths=args.sample_depths,
        sample_wavelengths=args.sample_wavelengths,
        verbose=args.verbose,
        n_workers=args.workers,
    )

    print("=" * 72)
    print("NODI Precompute Runtime Estimate")
    print("=" * 72)
    print("Machine")
    for key, value in report["machine"].items():
        print(f"  {key}: {value}")
    print()

    print("Benchmark run")
    for key in [
        "grid",
        "particle_profile",
        "sample_particles",
        "sample_widths",
        "sample_depths",
        "sample_wavelengths",
        "cases",
        "events_per_case",
        "total_events",
    ]:
        print(f"  {key}: {report['benchmark'][key]}")
    print(f"  elapsed_seconds: {report['benchmark']['elapsed_seconds']:.2f}")
    print(f"  cases_per_second: {report['benchmark']['cases_per_second']:.4f}")
    print(f"  events_per_second: {report['benchmark']['events_per_second']:.2f}")
    print()

    print("Target estimate")
    for key in [
        "grid",
        "particle_profile",
        "profile_label",
        "particles",
        "widths",
        "depths",
        "wavelengths",
        "cases",
        "events_per_case",
        "total_events",
    ]:
        print(f"  {key}: {report['target'][key]}")
    print(f"  estimated_seconds: {report['target']['estimated_seconds']:.2f}")
    print(f"  estimated_readable: {report['target']['estimated_readable']}")

    if args.output_json:
        _write_json_atomic(args.output_json, report)
        print()
        print(f"Saved JSON report to: {args.output_json}")


if __name__ == "__main__":
    main()
