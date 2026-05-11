"""
Package-local synthetic population-trace smoke lane for roadmap-43 P1.

This module turns isolated event summaries into a simple full-run trace:
blank(t) + drift(t) + sum_i event_i(t - t_i) + noise(t). It is intentionally a
candidate-refinement diagnostic and does not replace the single-event simulator
or claim population inference from synthetic traces.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np


POPULATION_TRACE_DIAGNOSTIC_FIELDS = (
    "population_trace_simulator_status",
    "population_trace_claim_level",
    "scheduled_event_count",
    "accepted_event_count",
    "trace_detected_event_count",
    "overlap_rejected_event_count",
    "deadtime_suppressed_event_count",
    "population_trace_overlap_rejection_active",
    "population_trace_deadtime_suppression_active",
    "isolated_event_detectability_estimate",
    "full_trace_detectability_estimate",
    "full_trace_detectability_vs_isolated_detectability_ratio",
    "population_trace_bias_band",
    "population_trace_blank_model_status",
    "population_trace_drift_model_status",
    "reference_drift_rate_per_min",
    "population_trace_threshold",
)


@dataclass(frozen=True)
class PopulationTraceConfig:
    """Configuration for a synthetic population-trace smoke simulation."""

    total_time_s: float
    sampling_rate_Hz: float
    event_rate_Hz: float
    blank_noise_std: float = 0.0
    drift_slope_per_s: float = 0.0
    baseline: float = 0.0
    min_event_interval_s: float = 0.0
    dead_time_s: float = 0.0
    event_width_s: float | None = None
    threshold: float | None = None
    random_seed: int | None = None
    max_events: int | None = None

    def __post_init__(self) -> None:
        if self.total_time_s <= 0.0:
            raise ValueError("total_time_s must be positive")
        if self.sampling_rate_Hz <= 0.0:
            raise ValueError("sampling_rate_Hz must be positive")
        if self.event_rate_Hz < 0.0:
            raise ValueError("event_rate_Hz must be non-negative")
        if self.blank_noise_std < 0.0:
            raise ValueError("blank_noise_std must be non-negative")
        if self.min_event_interval_s < 0.0:
            raise ValueError("min_event_interval_s must be non-negative")
        if self.dead_time_s < 0.0:
            raise ValueError("dead_time_s must be non-negative")
        if self.event_width_s is not None and self.event_width_s <= 0.0:
            raise ValueError("event_width_s must be positive when provided")
        if self.threshold is not None and self.threshold < 0.0:
            raise ValueError("threshold must be non-negative when provided")
        if self.max_events is not None and self.max_events < 0:
            raise ValueError("max_events must be non-negative when provided")


def _peak_height(event: Mapping[str, object]) -> float:
    def _as_float(value: object) -> float | None:
        if isinstance(value, (int, float, np.integer, np.floating, np.number)):
            return float(value)
        return None

    for key in ("peak_height", "mean_peak_height", "event_peak_height"):
        value = event.get(key)
        peak_value = _as_float(value)
        if peak_value is not None:
            return peak_value
    features = event.get("features")
    if isinstance(features, Mapping):
        peaks = features.get("peaks")
        if isinstance(peaks, Sequence) and peaks:
            first_peak = peaks[0]
            if isinstance(first_peak, Mapping) and first_peak.get("peak_height") is not None:
                peak_value = _as_float(first_peak["peak_height"])
                if peak_value is not None:
                    return peak_value
    raise ValueError("Each isolated event must expose peak_height or mean_peak_height")


def _event_width_s(event: Mapping[str, object], cfg: PopulationTraceConfig) -> float:
    def _as_float(value: object) -> float | None:
        if isinstance(value, (int, float, np.integer, np.floating, np.number)):
            return float(value)
        return None

    if cfg.event_width_s is not None:
        return float(cfg.event_width_s)
    for key in ("transit_time_s", "peak_width_s", "mean_transit_time_s"):
        value = event.get(key)
        width_value = _as_float(value)
        if width_value is not None and width_value > 0.0:
            return width_value
    return max(5.0 / float(cfg.sampling_rate_Hz), 1.0e-3)


def _default_threshold(peaks: np.ndarray, cfg: PopulationTraceConfig) -> float:
    if cfg.threshold is not None:
        return float(cfg.threshold)
    if peaks.size == 0:
        return 0.0
    return float(max(3.0 * cfg.blank_noise_std, 0.5 * np.median(peaks)))


def _scheduled_event_times(
    cfg: PopulationTraceConfig,
    rng: np.random.Generator,
    event_times_s: Sequence[float] | None,
) -> np.ndarray:
    if event_times_s is not None:
        event_times = np.asarray(event_times_s, dtype=float)
        return np.sort(event_times[(event_times >= 0.0) & (event_times < cfg.total_time_s)])
    if cfg.event_rate_Hz <= 0.0 or cfg.max_events == 0:
        return np.asarray([], dtype=float)

    event_time_values: list[float] = []
    current_time = 0.0
    while current_time < cfg.total_time_s:
        current_time += float(rng.exponential(1.0 / cfg.event_rate_Hz))
        if current_time >= cfg.total_time_s:
            break
        event_time_values.append(current_time)
        if cfg.max_events is not None and len(event_time_values) >= cfg.max_events:
            break
    return np.asarray(event_time_values, dtype=float)


def _add_gaussian_event(
    trace: np.ndarray,
    time_s: np.ndarray,
    *,
    center_s: float,
    peak_height: float,
    width_s: float,
) -> None:
    dt_s = float(time_s[1] - time_s[0]) if time_s.size > 1 else 1.0
    sigma_s = max(float(width_s) / 6.0, dt_s)
    trace += float(peak_height) * np.exp(-0.5 * ((time_s - center_s) / sigma_s) ** 2)


def _detect_accepted_events(
    trace: np.ndarray,
    blank_trace: np.ndarray,
    time_s: np.ndarray,
    accepted_events: Sequence[dict[str, float]],
    threshold: float,
) -> int:
    detected_count = 0
    signal_only = trace - blank_trace
    dt_s = float(time_s[1] - time_s[0]) if time_s.size > 1 else 1.0
    for event in accepted_events:
        center = event["event_time_s"]
        half_width = max(event["width_s"] / 2.0, dt_s)
        mask = (time_s >= center - half_width) & (time_s <= center + half_width)
        if not bool(np.any(mask)):
            nearest_index = int(np.argmin(np.abs(time_s - center)))
            response = float(signal_only[nearest_index])
        else:
            response = float(np.max(signal_only[mask]))
        if response >= threshold:
            detected_count += 1
    return detected_count


def _bias_band(ratio: float | None) -> str:
    if ratio is None:
        return "unavailable"
    if ratio < 0.5:
        return "strong_full_trace_suppression"
    if ratio < 0.8:
        return "moderate_full_trace_suppression"
    if ratio <= 1.2:
        return "near_isolated_detectability"
    return "full_trace_detectability_inflated_by_overlap_or_noise"


def simulate_population_trace_from_event_library(
    isolated_events: Sequence[Mapping[str, object]],
    cfg: PopulationTraceConfig,
    *,
    event_times_s: Sequence[float] | None = None,
) -> dict[str, object]:
    """
    Build a synthetic full trace from isolated event summaries.

    The detectability estimate is intentionally simple: isolated detectability is
    the fraction of template peaks above threshold, while full-trace detectability
    is the accepted-and-detected event count divided by scheduled events.
    """
    if not isolated_events:
        raise ValueError("isolated_events must not be empty")

    rng = np.random.default_rng(cfg.random_seed)
    n_samples = max(1, int(round(cfg.total_time_s * cfg.sampling_rate_Hz)))
    time_s = np.arange(n_samples, dtype=float) / float(cfg.sampling_rate_Hz)
    drift = float(cfg.drift_slope_per_s) * time_s
    noise = (
        rng.normal(0.0, float(cfg.blank_noise_std), size=n_samples)
        if cfg.blank_noise_std > 0.0
        else np.zeros(n_samples, dtype=float)
    )
    blank_trace = float(cfg.baseline) + drift + noise
    trace = np.array(blank_trace, copy=True)

    peaks = np.asarray([_peak_height(event) for event in isolated_events], dtype=float)
    threshold = _default_threshold(peaks, cfg)
    isolated_detectability = float(np.mean(peaks >= threshold)) if peaks.size else 0.0
    scheduled_times = _scheduled_event_times(cfg, rng, event_times_s)

    accepted_events: list[dict[str, float]] = []
    overlap_rejected_count = 0
    deadtime_suppressed_count = 0
    last_accepted_time: float | None = None
    last_accepted_end: float | None = None
    min_separation_s = max(float(cfg.min_event_interval_s), float(cfg.dead_time_s))

    for index, event_time_s in enumerate(scheduled_times):
        template = isolated_events[index % len(isolated_events)]
        peak = _peak_height(template)
        width_s = _event_width_s(template, cfg)
        half_width_s = width_s / 2.0

        if last_accepted_end is not None and float(event_time_s) < last_accepted_end:
            overlap_rejected_count += 1
            continue
        if (
            last_accepted_time is not None
            and min_separation_s > 0.0
            and float(event_time_s) - last_accepted_time < min_separation_s
        ):
            deadtime_suppressed_count += 1
            continue

        _add_gaussian_event(
            trace,
            time_s,
            center_s=float(event_time_s),
            peak_height=peak,
            width_s=width_s,
        )
        accepted_events.append(
            {
                "event_time_s": float(event_time_s),
                "peak_height": float(peak),
                "width_s": float(width_s),
            }
        )
        last_accepted_time = float(event_time_s)
        last_accepted_end = float(event_time_s) + half_width_s

    detected_count = _detect_accepted_events(
        trace,
        blank_trace,
        time_s,
        accepted_events,
        threshold,
    )
    scheduled_count = int(scheduled_times.size)
    full_trace_detectability = (
        float(detected_count / scheduled_count) if scheduled_count > 0 else 0.0
    )
    ratio = (
        float(full_trace_detectability / isolated_detectability)
        if isolated_detectability > 0.0
        else None
    )
    blank_status = (
        "synthetic_gaussian_blank"
        if cfg.blank_noise_std > 0.0
        else "synthetic_zero_blank"
    )
    drift_status = (
        "linear_drift_surrogate"
        if abs(float(cfg.drift_slope_per_s)) > 0.0
        else "no_drift"
    )

    diagnostics = {
        "population_trace_simulator_status": (
            "synthetic_smoke_active" if scheduled_count else "no_scheduled_events"
        ),
        "population_trace_claim_level": (
            "synthetic_full_trace_smoke_not_population_inference"
        ),
        "scheduled_event_count": scheduled_count,
        "accepted_event_count": int(len(accepted_events)),
        "trace_detected_event_count": int(detected_count),
        "overlap_rejected_event_count": int(overlap_rejected_count),
        "deadtime_suppressed_event_count": int(deadtime_suppressed_count),
        "population_trace_overlap_rejection_active": bool(overlap_rejected_count > 0),
        "population_trace_deadtime_suppression_active": bool(
            deadtime_suppressed_count > 0
        ),
        "isolated_event_detectability_estimate": isolated_detectability,
        "full_trace_detectability_estimate": full_trace_detectability,
        "full_trace_detectability_vs_isolated_detectability_ratio": ratio,
        "population_trace_bias_band": _bias_band(ratio),
        "population_trace_blank_model_status": blank_status,
        "population_trace_drift_model_status": drift_status,
        "reference_drift_rate_per_min": float(cfg.drift_slope_per_s) * 60.0,
        "population_trace_threshold": threshold,
    }

    return {
        "time_s": time_s,
        "trace": trace,
        "blank_trace": blank_trace,
        "accepted_events": accepted_events,
        "scheduled_event_times_s": scheduled_times,
        "diagnostics": diagnostics,
    }
