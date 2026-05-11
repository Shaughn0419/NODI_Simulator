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

from nodi_simulator._exports import (  # noqa: E402
    BASELINE_PARTICLE,
    Channel,
    WATER,
    compute_baseline_normalization,
    extract_pulse_features,
    run_single_case_batch,
)
from nodi_simulator.dashboard.config import (  # noqa: E402
    DEFAULT_SIM_CFG,
    FULL_SWEEP_WAVELENGTHS_NM,
    OPTICAL_TEMPLATE,
    THETA_GRID_RAD,
    make_particle,
)
from nodi_simulator.pulse_analysis import (  # noqa: E402
    PulseExtractionContext,
    build_pulse_extraction_context,
)
from tools._common import write_csv_records, write_json_file  # noqa: E402

DEFAULT_GEOMETRIES_NM = ((500, 500), (800, 500), (1200, 800))
DEFAULT_WAVELENGTHS_NM = FULL_SWEEP_WAVELENGTHS_NM
DECISION_RATE_TOLERANCE = 0.02
DECISION_HEIGHT_REL_TOLERANCE = 0.02
DECISION_WIDTH_REL_TOLERANCE = 0.05
EPS = 1e-15


def _safe_tag(raw_tag: str) -> str:
    """Return a filesystem-safe experiment tag."""
    tag = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(raw_tag)).strip("._-")
    return tag or "peak_detector_vectorization"


def _empty_features(threshold: float, detection_mode: str) -> dict[str, Any]:
    return {
        "n_peaks": 0,
        "peaks": [],
        "threshold_used": float(threshold),
        "detection_mode": str(detection_mode),
    }


def _intersection_left(values: np.ndarray, peak_index: int, level: float) -> float:
    left = int(peak_index)
    while left > 0 and float(values[left]) > level:
        left -= 1
    if left == 0 and float(values[left]) > level:
        return 0.0
    if left == peak_index:
        return float(peak_index)

    y0 = float(values[left])
    y1 = float(values[left + 1])
    if abs(y1 - y0) <= EPS:
        return float(left)
    frac = float(np.clip((level - y0) / (y1 - y0), 0.0, 1.0))
    return float(left) + frac


def _intersection_right(values: np.ndarray, peak_index: int, level: float) -> float:
    right = int(peak_index)
    last = int(values.size - 1)
    while right < last and float(values[right]) > level:
        right += 1
    if right == last and float(values[right]) > level:
        return float(last)
    if right == peak_index:
        return float(peak_index)

    y0 = float(values[right - 1])
    y1 = float(values[right])
    if abs(y1 - y0) <= EPS:
        return float(right)
    frac = float(np.clip((level - y0) / (y1 - y0), 0.0, 1.0))
    return float(right - 1) + frac


def _half_height_width_samples(
    values: np.ndarray,
    peak_index: int,
    peak_height: float,
) -> float:
    """Approximate width from half-height crossings around one local maximum."""
    half_height = 0.5 * float(peak_height)
    left_ip = _intersection_left(values, peak_index, half_height)
    right_ip = _intersection_right(values, peak_index, half_height)
    return float(max(right_ip - left_ip, 0.0))


def _distance_pruned_indices(
    candidate_indices: np.ndarray,
    candidate_heights: np.ndarray,
    min_distance_samples: int,
) -> list[int]:
    """Greedily keep taller peaks first, matching the important distance rule."""
    if candidate_indices.size == 0:
        return []
    order = np.argsort(candidate_heights, kind="stable")[::-1]
    kept: list[int] = []
    distance = max(1, int(min_distance_samples))
    for order_index in order:
        peak_index = int(candidate_indices[order_index])
        if all(abs(peak_index - existing) >= distance for existing in kept):
            kept.append(peak_index)
    kept.sort()
    return kept


def extract_vector_localmax_features_block(
    time_s: np.ndarray,
    signals: np.ndarray,
    thresholds: np.ndarray,
    *,
    detection_mode: str,
    context: PulseExtractionContext,
) -> list[dict[str, Any]]:
    """
    Experimental detector candidate.

    This intentionally lives outside production. It vectorizes thresholded local
    maximum discovery across event traces, then applies a small scalar loop for
    distance pruning and approximate half-height widths. The approximation is
    the behavior under test; it is not assumed equivalent to SciPy widths.
    """
    time_arr = np.asarray(time_s, dtype=float)
    signal_arr = np.asarray(signals, dtype=float)
    threshold_arr = np.asarray(thresholds, dtype=float)
    if signal_arr.ndim != 2:
        raise ValueError(f"signals must be 2D, got shape {signal_arr.shape}")
    if threshold_arr.shape != (signal_arr.shape[0],):
        raise ValueError(
            "thresholds must have one value per signal trace, got "
            f"{threshold_arr.shape} for {signal_arr.shape[0]} traces"
        )

    if detection_mode == "positive":
        detection_values = signal_arr
    elif detection_mode == "absolute":
        detection_values = np.abs(signal_arr)
    else:
        raise ValueError(
            f"detection_mode must be 'positive' or 'absolute', got {detection_mode}"
        )

    if detection_values.shape[1] < 3:
        return [
            _empty_features(float(threshold), detection_mode)
            for threshold in threshold_arr
        ]

    centers = detection_values[:, 1:-1]
    local_maxima = (
        (centers > detection_values[:, :-2])
        & (centers >= detection_values[:, 2:])
        & (centers >= threshold_arr[:, None])
    )
    row_maxima = np.max(detection_values, axis=1)
    dt = float(context.dt_s)
    min_width_samples = int(context.min_width_samples)
    min_distance_samples = int(context.min_distance_samples)

    feature_payloads: list[dict[str, Any]] = []
    for row_index in range(signal_arr.shape[0]):
        threshold = float(threshold_arr[row_index])
        if detection_values.shape[1] == 0 or float(row_maxima[row_index]) < threshold:
            feature_payloads.append(_empty_features(threshold, detection_mode))
            continue

        candidate_indices = np.flatnonzero(local_maxima[row_index]) + 1
        if candidate_indices.size == 0:
            feature_payloads.append(_empty_features(threshold, detection_mode))
            continue

        values = detection_values[row_index]
        candidate_heights = values[candidate_indices]
        pruned_indices = _distance_pruned_indices(
            candidate_indices,
            candidate_heights,
            min_distance_samples,
        )
        peaks: list[dict[str, Any]] = []
        for peak_index in pruned_indices:
            peak_height = float(values[peak_index])
            width_samples = _half_height_width_samples(values, peak_index, peak_height)
            if width_samples < min_width_samples:
                continue

            signed_height = float(signal_arr[row_index, peak_index])
            peaks.append(
                {
                    "peak_time_s": float(time_arr[peak_index]),
                    "peak_height": peak_height,
                    "peak_signed_height": signed_height,
                    "peak_polarity": "negative" if signed_height < 0 else "positive",
                    "peak_width_s": float(width_samples * dt),
                    "peak_area": 0.0,
                    "prominence": 0.0,
                }
            )

        feature_payloads.append(
            {
                "n_peaks": len(peaks),
                "peaks": peaks,
                "threshold_used": threshold,
                "detection_mode": detection_mode,
            }
        )

    return feature_payloads


def _extract_baseline_features_block(
    time_s: np.ndarray,
    signals: np.ndarray,
    thresholds: np.ndarray,
    *,
    sim_cfg: Any,
    context: PulseExtractionContext,
) -> list[dict[str, Any]]:
    return [
        extract_pulse_features(
            time_s,
            signal,
            float(threshold),
            sim_cfg.min_peak_width_s,
            sim_cfg.min_peak_interval_s,
            detection_mode=sim_cfg.pulse_detection_mode,
            context=context,
            include_area_prominence=False,
        )
        for signal, threshold in zip(signals, thresholds, strict=True)
    ]


def _best_peak(features: dict[str, Any]) -> dict[str, Any] | None:
    peaks = features.get("peaks", [])
    if not peaks:
        return None
    return max(peaks, key=lambda peak: float(peak.get("peak_height", 0.0)))


def _summarize_features(
    features_list: list[dict[str, Any]],
    thresholds: np.ndarray,
    robust_stds: np.ndarray,
    *,
    stable_detection_margin_z_min: float,
) -> dict[str, float]:
    n_total = len(features_list)
    heights: list[float] = []
    widths: list[float] = []
    n_detected = 0
    n_stable = 0
    for features, threshold, robust_std in zip(
        features_list,
        thresholds,
        robust_stds,
        strict=True,
    ):
        best = _best_peak(features)
        if best is None:
            continue
        n_detected += 1
        peak_height = float(best["peak_height"])
        heights.append(peak_height)
        widths.append(float(best["peak_width_s"]))
        margin_z = round(
            max(peak_height - float(threshold), 0.0) / max(float(robust_std), EPS),
            12,
        )
        if margin_z >= stable_detection_margin_z_min:
            n_stable += 1

    return {
        "n_events": float(n_total),
        "n_detected": float(n_detected),
        "detection_rate": float(n_detected / n_total) if n_total else 0.0,
        "stable_detection_rate": float(n_stable / n_total) if n_total else 0.0,
        "mean_peak_height": float(np.mean(heights)) if heights else 0.0,
        "mean_peak_width_s": float(np.mean(widths)) if widths else 0.0,
    }


def _relative_delta(experimental: float, baseline: float) -> float:
    if abs(baseline) <= EPS:
        return 0.0 if abs(experimental) <= EPS else float("inf")
    return float((experimental - baseline) / abs(baseline))


def _detected_mask(features_list: list[dict[str, Any]]) -> np.ndarray:
    return np.asarray(
        [int(features.get("n_peaks", 0) > 0) for features in features_list],
        dtype=bool,
    )


def _agreement_summary(
    baseline_features: list[dict[str, Any]],
    experimental_features: list[dict[str, Any]],
) -> dict[str, float]:
    baseline_detected = _detected_mask(baseline_features)
    experimental_detected = _detected_mask(experimental_features)
    n_events = int(baseline_detected.size)
    n_baseline = int(np.sum(baseline_detected))
    n_experimental = int(np.sum(experimental_detected))
    false_negative = int(np.sum(baseline_detected & ~experimental_detected))
    false_positive = int(np.sum(~baseline_detected & experimental_detected))

    paired_height_abs_rel_errors: list[float] = []
    paired_width_abs_rel_errors: list[float] = []
    for baseline, experimental in zip(
        baseline_features,
        experimental_features,
        strict=True,
    ):
        baseline_peak = _best_peak(baseline)
        experimental_peak = _best_peak(experimental)
        if baseline_peak is None or experimental_peak is None:
            continue
        baseline_height = float(baseline_peak["peak_height"])
        experimental_height = float(experimental_peak["peak_height"])
        baseline_width = float(baseline_peak["peak_width_s"])
        experimental_width = float(experimental_peak["peak_width_s"])
        if baseline_height > EPS:
            paired_height_abs_rel_errors.append(
                abs((experimental_height - baseline_height) / baseline_height)
            )
        if baseline_width > EPS:
            paired_width_abs_rel_errors.append(
                abs((experimental_width - baseline_width) / baseline_width)
            )

    return {
        "event_detection_agreement_rate": (
            float(np.mean(baseline_detected == experimental_detected))
            if n_events
            else 0.0
        ),
        "false_negative_rate_vs_baseline": (
            float(false_negative / n_baseline) if n_baseline else 0.0
        ),
        "false_positive_rate_vs_baseline": (
            float(false_positive / (n_events - n_baseline))
            if n_events > n_baseline
            else 0.0
        ),
        "baseline_detected_events": float(n_baseline),
        "experimental_detected_events": float(n_experimental),
        "mean_abs_rel_error_matched_peak_height": (
            float(np.mean(paired_height_abs_rel_errors))
            if paired_height_abs_rel_errors
            else 0.0
        ),
        "mean_abs_rel_error_matched_peak_width": (
            float(np.mean(paired_width_abs_rel_errors))
            if paired_width_abs_rel_errors
            else 0.0
        ),
    }


def _case_record(
    *,
    particle: Any,
    width_nm: int,
    depth_nm: int,
    wavelength_nm: int,
    baseline_summary: dict[str, float],
    experimental_summary: dict[str, float],
    agreement: dict[str, float],
    baseline_detection_time_s: float,
    experimental_detection_time_s: float,
    simulation_time_s: float,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "particle_name": str(particle.name),
        "particle_radius_nm": float(particle.radius_m * 1e9),
        "wavelength_nm": int(wavelength_nm),
        "width_nm": int(width_nm),
        "depth_nm": int(depth_nm),
        "simulation_time_s": float(simulation_time_s),
        "baseline_detection_time_s": float(baseline_detection_time_s),
        "experimental_detection_time_s": float(experimental_detection_time_s),
    }
    for prefix, summary in (
        ("baseline", baseline_summary),
        ("experimental", experimental_summary),
    ):
        for key, value in summary.items():
            record[f"{prefix}_{key}"] = float(value)
    for key, value in agreement.items():
        record[key] = float(value)
    for metric in (
        "detection_rate",
        "stable_detection_rate",
        "mean_peak_height",
        "mean_peak_width_s",
    ):
        baseline = float(baseline_summary[metric])
        experimental = float(experimental_summary[metric])
        record[f"delta_{metric}"] = float(experimental - baseline)
        record[f"relative_delta_{metric}"] = _relative_delta(experimental, baseline)
    return record


def _run_case(
    *,
    particle: Any,
    width_nm: int,
    depth_nm: int,
    wavelength_nm: int,
    sim_cfg: Any,
) -> dict[str, Any]:
    channel = Channel(width_nm * 1e-9, depth_nm * 1e-9)
    optical = replace(OPTICAL_TEMPLATE, wavelength_m=wavelength_nm * 1e-9)
    normalization = compute_baseline_normalization(
        BASELINE_PARTICLE,
        WATER,
        optical,
        THETA_GRID_RAD,
        channel=channel,
        sim_cfg=sim_cfg,
    )

    simulation_start = time.perf_counter()
    batch = run_single_case_batch(
        particle,
        WATER,
        channel,
        optical,
        sim_cfg,
        normalization["E_sca_ref"],
        THETA_GRID_RAD,
        retain_event_traces=True,
    )
    simulation_time_s = time.perf_counter() - simulation_start
    events = batch["events"]
    if not events:
        raise RuntimeError(
            f"No control events generated for {particle.name} "
            f"{wavelength_nm}nm {width_nm}x{depth_nm}nm"
        )

    time_s = np.asarray(events[0]["trajectory"]["time_s"], dtype=float)
    signals = np.vstack([np.asarray(event["signal_noisy"], dtype=float) for event in events])
    thresholds = np.asarray([float(event["threshold"]) for event in events], dtype=float)
    robust_stds = np.asarray(
        [float(event["threshold_robust_std"]) for event in events],
        dtype=float,
    )
    context = build_pulse_extraction_context(
        time_s,
        sim_cfg.min_peak_width_s,
        sim_cfg.min_peak_interval_s,
    )

    baseline_start = time.perf_counter()
    baseline_features = _extract_baseline_features_block(
        time_s,
        signals,
        thresholds,
        sim_cfg=sim_cfg,
        context=context,
    )
    baseline_detection_time_s = time.perf_counter() - baseline_start

    experimental_start = time.perf_counter()
    experimental_features = extract_vector_localmax_features_block(
        time_s,
        signals,
        thresholds,
        detection_mode=sim_cfg.pulse_detection_mode,
        context=context,
    )
    experimental_detection_time_s = time.perf_counter() - experimental_start

    baseline_summary = _summarize_features(
        baseline_features,
        thresholds,
        robust_stds,
        stable_detection_margin_z_min=sim_cfg.stable_detection_margin_z_min,
    )
    experimental_summary = _summarize_features(
        experimental_features,
        thresholds,
        robust_stds,
        stable_detection_margin_z_min=sim_cfg.stable_detection_margin_z_min,
    )
    agreement = _agreement_summary(baseline_features, experimental_features)
    return _case_record(
        particle=particle,
        width_nm=width_nm,
        depth_nm=depth_nm,
        wavelength_nm=wavelength_nm,
        baseline_summary=baseline_summary,
        experimental_summary=experimental_summary,
        agreement=agreement,
        baseline_detection_time_s=baseline_detection_time_s,
        experimental_detection_time_s=experimental_detection_time_s,
        simulation_time_s=simulation_time_s,
    )


def _experiment_particles() -> list[Any]:
    return [
        BASELINE_PARTICLE,
        make_particle("exosome", 100, name="exosome_uniform_100nm_control"),
    ]


def _finite_abs(values: list[float]) -> list[float]:
    return [abs(value) for value in values if np.isfinite(value)]


def _overall_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = (
        "detection_rate",
        "stable_detection_rate",
        "mean_peak_height",
        "mean_peak_width_s",
    )
    overall: dict[str, Any] = {
        "n_cases": len(records),
        "n_events_total": int(sum(record["baseline_n_events"] for record in records)),
        "simulation_time_s": float(sum(record["simulation_time_s"] for record in records)),
        "baseline_detection_time_s": float(
            sum(record["baseline_detection_time_s"] for record in records)
        ),
        "experimental_detection_time_s": float(
            sum(record["experimental_detection_time_s"] for record in records)
        ),
        "mean_event_detection_agreement_rate": float(
            np.mean([record["event_detection_agreement_rate"] for record in records])
        ),
        "max_false_negative_rate_vs_baseline": float(
            np.max([record["false_negative_rate_vs_baseline"] for record in records])
        ),
        "max_false_positive_rate_vs_baseline": float(
            np.max([record["false_positive_rate_vs_baseline"] for record in records])
        ),
        "mean_abs_rel_error_matched_peak_height": float(
            np.mean(
                [
                    record["mean_abs_rel_error_matched_peak_height"]
                    for record in records
                ]
            )
        ),
        "mean_abs_rel_error_matched_peak_width": float(
            np.mean(
                [
                    record["mean_abs_rel_error_matched_peak_width"]
                    for record in records
                ]
            )
        ),
    }
    experimental_time = float(overall["experimental_detection_time_s"])
    baseline_time = float(overall["baseline_detection_time_s"])
    overall["detector_speedup_experimental_vs_baseline"] = (
        baseline_time / experimental_time if experimental_time > 0.0 else float("inf")
    )

    for metric in metrics:
        deltas = [float(record[f"delta_{metric}"]) for record in records]
        relative_deltas = _finite_abs(
            [float(record[f"relative_delta_{metric}"]) for record in records]
        )
        overall[f"mean_abs_delta_{metric}"] = float(np.mean(np.abs(deltas)))
        overall[f"max_abs_delta_{metric}"] = float(np.max(np.abs(deltas)))
        overall[f"max_abs_relative_delta_{metric}"] = (
            float(np.max(relative_deltas)) if relative_deltas else 0.0
        )

    return overall


def _decision(overall: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if overall["max_abs_delta_detection_rate"] > DECISION_RATE_TOLERANCE:
        blockers.append("detection_rate_bias")
    if overall["max_abs_delta_stable_detection_rate"] > DECISION_RATE_TOLERANCE:
        blockers.append("stable_detection_rate_bias")
    if (
        overall["max_abs_relative_delta_mean_peak_height"]
        > DECISION_HEIGHT_REL_TOLERANCE
    ):
        blockers.append("peak_height_bias")
    if (
        overall["max_abs_relative_delta_mean_peak_width_s"]
        > DECISION_WIDTH_REL_TOLERANCE
    ):
        blockers.append("peak_width_bias")

    replace_safe = not blockers
    return {
        "replace_recommendation": (
            "candidate_is_replaceable_under_current_controls"
            if replace_safe
            else "do_not_replace_current_baseline"
        ),
        "replace_safe": replace_safe,
        "blockers": blockers,
        "tolerances": {
            "max_abs_delta_detection_rate": DECISION_RATE_TOLERANCE,
            "max_abs_delta_stable_detection_rate": DECISION_RATE_TOLERANCE,
            "max_abs_relative_delta_mean_peak_height": DECISION_HEIGHT_REL_TOLERANCE,
            "max_abs_relative_delta_mean_peak_width_s": DECISION_WIDTH_REL_TOLERANCE,
        },
    }


def _parse_geometry(raw: str) -> tuple[int, int]:
    width_raw, depth_raw = raw.lower().split("x", maxsplit=1)
    return int(width_raw), int(depth_raw)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run an isolated control-data experiment for a vector/local-maximum "
            "pulse detector candidate. The production detector is not modified."
        )
    )
    parser.add_argument("--events", type=int, default=12, help="Events per case.")
    parser.add_argument("--seed", type=int, default=42, help="Base RNG seed.")
    parser.add_argument(
        "--wavelengths-nm",
        type=int,
        nargs="+",
        default=list(DEFAULT_WAVELENGTHS_NM),
        help="Wavelength control points in nm.",
    )
    parser.add_argument(
        "--geometries-nm",
        type=_parse_geometry,
        nargs="+",
        default=list(DEFAULT_GEOMETRIES_NM),
        help="Geometry control points as WIDTHxDEPTH in nm.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "reports" / "peak_detector_experiment",
        help="Directory for JSON/CSV reports.",
    )
    parser.add_argument(
        "--tag",
        type=str,
        default="codex_peak_detector_vectorization_20260426",
        help="Safe tag used in report filenames.",
    )
    parser.add_argument(
        "--no-diffusion",
        action="store_true",
        help="Disable diffusion for a faster pure-advection control run.",
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
        include_diffusion=not bool(args.no_diffusion),
        random_sequence_policy="case_keyed_independent",
        event_sampling_policy="sobol_stratified",
        adaptive_event_budget_mode="fixed",
        vectorized_event_engine="off",
    )

    records: list[dict[str, Any]] = []
    experiment_start = time.perf_counter()
    for particle in _experiment_particles():
        for wavelength_nm in args.wavelengths_nm:
            for width_nm, depth_nm in args.geometries_nm:
                records.append(
                    _run_case(
                        particle=particle,
                        width_nm=int(width_nm),
                        depth_nm=int(depth_nm),
                        wavelength_nm=int(wavelength_nm),
                        sim_cfg=sim_cfg,
                    )
                )

    overall = _overall_summary(records)
    overall["wall_time_s"] = float(time.perf_counter() - experiment_start)
    decision = _decision(overall)

    csv_path = args.output_dir / f"{tag}_cases.csv"
    json_path = args.output_dir / f"{tag}_summary.json"
    write_csv_records(csv_path, records)
    write_json_file(
        json_path,
        {
            "experiment": {
                "tag": tag,
                "detector_candidate": "vector_localmax_half_height_width",
                "baseline_detector": "scipy.signal.find_peaks",
                "production_path_modified": False,
                "events_per_case": int(args.events),
                "random_seed": int(args.seed),
                "wavelengths_nm": [int(value) for value in args.wavelengths_nm],
                "geometries_nm": [
                    {"width_nm": int(width), "depth_nm": int(depth)}
                    for width, depth in args.geometries_nm
                ],
                "particles": [str(particle.name) for particle in _experiment_particles()],
                "include_diffusion": bool(sim_cfg.include_diffusion),
                "pulse_detection_mode": str(sim_cfg.pulse_detection_mode),
                "min_peak_width_s": float(sim_cfg.min_peak_width_s),
                "min_peak_interval_s": float(sim_cfg.min_peak_interval_s),
                "stable_detection_margin_z_min": float(
                    sim_cfg.stable_detection_margin_z_min
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
