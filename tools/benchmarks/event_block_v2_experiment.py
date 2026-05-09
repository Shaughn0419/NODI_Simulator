from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in (str(PROJECT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from nodi_simulator import (  # noqa: E402
    BASELINE_PARTICLE,
    Channel,
    WATER,
    compute_baseline_normalization,
    run_single_case_batch,
)
from nodi_simulator.dashboard.config import (  # noqa: E402
    DEFAULT_SIM_CFG,
    FULL_SWEEP_WAVELENGTHS_NM,
    OPTICAL_TEMPLATE,
    THETA_GRID_RAD,
    make_particle,
)
from nodi_simulator.dashboard.precompute import build_precompute_sim_cfg  # noqa: E402
from tools._common import write_csv_records, write_json_file  # noqa: E402
from nodi_simulator.parameter_sweep import evaluate_engineering_gate  # noqa: E402

DEFAULT_GEOMETRIES_NM = ((500, 500), (800, 500), (1200, 800))
DEFAULT_WAVELENGTHS_NM = FULL_SWEEP_WAVELENGTHS_NM
BIAS_METRICS = (
    "detection_rate",
    "stable_detection_rate",
    "mean_peak_height",
    "mean_peak_width_s",
)
RATE_TOLERANCE = 0.05
HEIGHT_REL_TOLERANCE = 0.10
WIDTH_REL_TOLERANCE = 0.10
MIN_SPEEDUP_FOR_DEFAULT = 1.5
EPS = 1e-15


def _safe_tag(raw_tag: str) -> str:
    tag = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(raw_tag)).strip("._-")
    return tag or "event_block_candidate"


def _parse_geometry(raw: str) -> tuple[int, int]:
    width_raw, depth_raw = raw.lower().split("x", maxsplit=1)
    return int(width_raw), int(depth_raw)


def _experiment_particles() -> list[Any]:
    return [
        BASELINE_PARTICLE,
        make_particle("exosome", 100, name="exosome_uniform_100nm_control"),
    ]


def _relative_delta(candidate: float, baseline: float) -> float:
    if abs(baseline) <= EPS:
        return 0.0 if abs(candidate) <= EPS else float("inf")
    return float((candidate - baseline) / abs(baseline))


def _run_one(
    *,
    particle: Any,
    width_nm: int,
    depth_nm: int,
    wavelength_nm: int,
    sim_cfg: Any,
    vectorized_event_engine: str,
    event_block_size: int,
) -> tuple[dict[str, Any], float]:
    channel = Channel(width_nm * 1e-9, depth_nm * 1e-9)
    optical = replace(OPTICAL_TEMPLATE, wavelength_m=wavelength_nm * 1e-9)
    cfg = replace(
        sim_cfg,
        vectorized_event_engine=vectorized_event_engine,
        event_block_size=int(event_block_size),
    )
    normalization = compute_baseline_normalization(
        BASELINE_PARTICLE,
        WATER,
        optical,
        THETA_GRID_RAD,
        channel=channel,
        sim_cfg=cfg,
    )
    start = time.perf_counter()
    batch = run_single_case_batch(
        particle,
        WATER,
        channel,
        optical,
        cfg,
        normalization["E_sca_ref"],
        THETA_GRID_RAD,
        retain_event_traces=False,
        stream_summary_only=True,
    )
    elapsed_s = time.perf_counter() - start
    gate = evaluate_engineering_gate(batch["summary"], cfg)
    return batch["summary"] | gate, elapsed_s


def _case_record(
    *,
    particle: Any,
    width_nm: int,
    depth_nm: int,
    wavelength_nm: int,
    scalar_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
    scalar_time_s: float,
    candidate_time_s: float,
    candidate_engine: str,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "particle_name": str(particle.name),
        "particle_radius_nm": float(particle.radius_m * 1e9),
        "wavelength_nm": int(wavelength_nm),
        "width_nm": int(width_nm),
        "depth_nm": int(depth_nm),
        "scalar_time_s": float(scalar_time_s),
        "candidate_engine": str(candidate_engine),
        "candidate_time_s": float(candidate_time_s),
        "speedup": (
            float(scalar_time_s / candidate_time_s)
            if candidate_time_s > 0
            else float("inf")
        ),
        "scalar_engine_used": str(scalar_summary.get("vectorized_event_engine_used")),
        "candidate_engine_used": str(
            candidate_summary.get("vectorized_event_engine_used")
        ),
        "candidate_fallback_reason": candidate_summary.get(
            "vectorized_event_engine_fallback_reason"
        ),
        "scalar_engineering_gate_passed": bool(
            scalar_summary.get("engineering_gate_passed", False)
        ),
        "candidate_engineering_gate_passed": bool(
            candidate_summary.get("engineering_gate_passed", False)
        ),
        "engineering_gate_agrees": bool(
            scalar_summary.get("engineering_gate_passed", False)
            == candidate_summary.get("engineering_gate_passed", False)
        ),
    }
    for metric in BIAS_METRICS:
        scalar_value = float(scalar_summary.get(metric, 0.0) or 0.0)
        vector_value = float(candidate_summary.get(metric, 0.0) or 0.0)
        record[f"scalar_{metric}"] = scalar_value
        record[f"candidate_{metric}"] = vector_value
        record[f"delta_{metric}"] = float(vector_value - scalar_value)
        record[f"relative_delta_{metric}"] = _relative_delta(vector_value, scalar_value)
    return record


def _finite_abs(values: list[float]) -> list[float]:
    return [abs(value) for value in values if np.isfinite(value)]


def _overall(records: list[dict[str, Any]]) -> dict[str, Any]:
    scalar_time = float(sum(record["scalar_time_s"] for record in records))
    candidate_time = float(sum(record["candidate_time_s"] for record in records))
    payload: dict[str, Any] = {
        "n_cases": len(records),
        "scalar_time_s": scalar_time,
        "candidate_time_s": candidate_time,
        "speedup": scalar_time / candidate_time if candidate_time > 0 else float("inf"),
        "engineering_gate_agreement_rate": float(
            np.mean([record["engineering_gate_agrees"] for record in records])
        ),
        "min_case_speedup": float(np.min([record["speedup"] for record in records])),
        "max_case_speedup": float(np.max([record["speedup"] for record in records])),
    }
    for metric in BIAS_METRICS:
        deltas = [float(record[f"delta_{metric}"]) for record in records]
        relative_deltas = _finite_abs(
            [float(record[f"relative_delta_{metric}"]) for record in records]
        )
        payload[f"mean_abs_delta_{metric}"] = float(np.mean(np.abs(deltas)))
        payload[f"max_abs_delta_{metric}"] = float(np.max(np.abs(deltas)))
        payload[f"max_abs_relative_delta_{metric}"] = (
            float(np.max(relative_deltas)) if relative_deltas else 0.0
        )
    return payload


def _decision(overall: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if overall["speedup"] < MIN_SPEEDUP_FOR_DEFAULT:
        blockers.append("speedup_below_default_threshold")
    if overall["max_abs_delta_detection_rate"] > RATE_TOLERANCE:
        blockers.append("detection_rate_bias")
    if overall["max_abs_delta_stable_detection_rate"] > RATE_TOLERANCE:
        blockers.append("stable_detection_rate_bias")
    if overall["max_abs_relative_delta_mean_peak_height"] > HEIGHT_REL_TOLERANCE:
        blockers.append("peak_height_bias")
    if overall["max_abs_relative_delta_mean_peak_width_s"] > WIDTH_REL_TOLERANCE:
        blockers.append("peak_width_bias")
    if overall["engineering_gate_agreement_rate"] < 1.0:
        blockers.append("engineering_gate_disagreement")
    return {
        "default_enable_recommendation": (
            "candidate_for_precompute_default"
            if not blockers
            else "keep_experimental"
        ),
        "blockers": blockers,
        "tolerances": {
            "min_speedup": MIN_SPEEDUP_FOR_DEFAULT,
            "max_abs_delta_detection_rate": RATE_TOLERANCE,
            "max_abs_delta_stable_detection_rate": RATE_TOLERANCE,
            "max_abs_relative_delta_mean_peak_height": HEIGHT_REL_TOLERANCE,
            "max_abs_relative_delta_mean_peak_width_s": WIDTH_REL_TOLERANCE,
            "engineering_gate_agreement_rate": 1.0,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare scalar event loop with a vectorized candidate engine."
    )
    parser.add_argument("--events", type=int, default=200, help="Events per case.")
    parser.add_argument("--seed", type=int, default=42, help="Base RNG seed.")
    parser.add_argument("--event-block-size", type=int, default=32)
    parser.add_argument(
        "--wavelengths-nm",
        type=int,
        nargs="+",
        default=list(DEFAULT_WAVELENGTHS_NM),
    )
    parser.add_argument(
        "--geometries-nm",
        type=_parse_geometry,
        nargs="+",
        default=list(DEFAULT_GEOMETRIES_NM),
    )
    parser.add_argument(
        "--candidate-engine",
        type=str,
        default="event_block_v3",
        help="Vectorized event engine to compare against scalar off.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "reports" / "event_block_v2_experiment",
    )
    parser.add_argument(
        "--tag",
        type=str,
        default="codex_event_block_candidate_20260426",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.events <= 0:
        raise ValueError(f"--events must be positive, got {args.events}")
    tag = _safe_tag(args.tag)
    sim_cfg = replace(
        DEFAULT_SIM_CFG,
        n_events=int(args.events),
        random_seed=int(args.seed),
        include_diffusion=True,
        random_sequence_policy="case_keyed_independent",
        event_sampling_policy="sobol_stratified",
        adaptive_event_budget_mode="fixed",
    )

    records: list[dict[str, Any]] = []
    wall_start = time.perf_counter()
    for particle in _experiment_particles():
        for wavelength_nm in args.wavelengths_nm:
            for width_nm, depth_nm in args.geometries_nm:
                scalar_summary, scalar_time_s = _run_one(
                    particle=particle,
                    width_nm=width_nm,
                    depth_nm=depth_nm,
                    wavelength_nm=wavelength_nm,
                    sim_cfg=sim_cfg,
                    vectorized_event_engine="off",
                    event_block_size=args.event_block_size,
                )
                candidate_summary, candidate_time_s = _run_one(
                    particle=particle,
                    width_nm=width_nm,
                    depth_nm=depth_nm,
                    wavelength_nm=wavelength_nm,
                    sim_cfg=sim_cfg,
                    vectorized_event_engine=args.candidate_engine,
                    event_block_size=args.event_block_size,
                )
                records.append(
                    _case_record(
                        particle=particle,
                        width_nm=width_nm,
                        depth_nm=depth_nm,
                        wavelength_nm=wavelength_nm,
                        scalar_summary=scalar_summary,
                        candidate_summary=candidate_summary,
                        scalar_time_s=scalar_time_s,
                        candidate_time_s=candidate_time_s,
                        candidate_engine=args.candidate_engine,
                    )
                )

    overall = _overall(records)
    overall["wall_time_s"] = float(time.perf_counter() - wall_start)
    decision = _decision(overall)
    precompute_default_engine = build_precompute_sim_cfg("coarse").vectorized_event_engine
    csv_path = args.output_dir / f"{tag}_cases.csv"
    json_path = args.output_dir / f"{tag}_summary.json"
    write_csv_records(csv_path, records)
    write_json_file(
        json_path,
        {
            "experiment": {
                "tag": tag,
                "events_per_case": int(args.events),
                "event_block_size": int(args.event_block_size),
                "random_seed": int(args.seed),
                "wavelengths_nm": [int(value) for value in args.wavelengths_nm],
                "geometries_nm": [
                    {"width_nm": int(width), "depth_nm": int(depth)}
                    for width, depth in args.geometries_nm
                ],
                "particles": [str(particle.name) for particle in _experiment_particles()],
                "scalar_engine": "off",
                "candidate_engine": str(args.candidate_engine),
                "precompute_default_engine": str(precompute_default_engine),
                "candidate_matches_current_precompute_default": bool(
                    args.candidate_engine == precompute_default_engine
                ),
            },
            "overall": overall,
            "decision": decision,
            "case_report_csv": str(csv_path),
        },
    )
    print(json.dumps({"overall": overall, "decision": decision}, indent=2))
    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
