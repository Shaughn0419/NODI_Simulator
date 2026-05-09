"""
Package-local pulse analysis module for NODI interferometric simulation.

Implements robust threshold estimation and pulse feature extraction.
Designed to match the paper's data processing approach:
    - Background-fluctuation-based threshold (median + MAD)
    - Minimum peak width and interval filtering
    - Peak height, width, area, prominence extraction

Key design choice:
    Threshold is estimated from the FIRST 20% of the signal (background-only),
    NOT from the entire trace, to avoid pulse contamination.
"""

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks


@dataclass(frozen=True)
class PulseExtractionContext:
    """Reusable pulse-detection sampling geometry for one fixed time grid."""

    dt_s: float
    min_width_samples: int
    min_distance_samples: int


def build_pulse_extraction_context(
    time_s: np.ndarray,
    min_peak_width_s: float,
    min_peak_interval_s: float,
) -> PulseExtractionContext:
    """Build reusable pulse-detection sample constraints."""
    time_arr = np.asarray(time_s, dtype=float)
    dt = float(time_arr[1] - time_arr[0])
    return PulseExtractionContext(
        dt_s=dt,
        min_width_samples=max(1, int(min_peak_width_s / dt)),
        min_distance_samples=max(1, int(min_peak_interval_s / dt)),
    )


def estimate_threshold_stats_robust(
    signal_segment: np.ndarray,
    sigma_multiplier: float = 5.0,
) -> dict:
    """
    Estimate robust background statistics and the corresponding threshold.

    Returns:
        dict with median, mad, robust_std, threshold
    """
    med = np.median(signal_segment)
    mad = np.median(np.abs(signal_segment - med))
    robust_std = 1.4826 * mad  # MAD -> Gaussian sigma conversion
    threshold = med + sigma_multiplier * robust_std
    return {
        "median": float(med),
        "mad": float(mad),
        "robust_std": float(robust_std),
        "threshold": float(threshold),
    }


def estimate_threshold_robust(
    signal_segment: np.ndarray,
    sigma_multiplier: float = 5.0,
) -> float:
    """
    Estimate detection threshold using robust statistics (median + MAD).

    This function should be called with a BACKGROUND-ONLY segment
    (typically the first 20% of the signal, before the particle enters
    the illumination zone).

    Args:
        signal_segment: Background signal segment (1D array).
        sigma_multiplier: Number of robust standard deviations above median.

    Returns:
        Threshold value.
    """
    return estimate_threshold_stats_robust(
        signal_segment,
        sigma_multiplier=sigma_multiplier,
    )["threshold"]


def extract_pulse_features(
    time_s: np.ndarray,
    signal_noisy: np.ndarray,
    threshold: float,
    min_peak_width_s: float,
    min_peak_interval_s: float,
    detection_mode: str = "positive",
    *,
    context: PulseExtractionContext | None = None,
    include_area_prominence: bool = True,
    width_measure_mode: str = "peak_width",
    duration_estimation_policy: str = "interpolated_threshold_crossing",
) -> dict:
    """
    Extract pulse features from a (potentially noisy) signal trace.

    Uses scipy.signal.find_peaks with height, width, and distance constraints.
    Matches the paper's approach: threshold-based detection with minimum
    peak width and minimum inter-peak interval.

    Args:
        time_s: Time array in seconds.
        signal_noisy: Signal trace (1D array, same length as time_s).
        threshold: Detection threshold (from estimate_threshold_robust).
        min_peak_width_s: Minimum acceptable pulse width/duration in seconds.
        min_peak_interval_s: Minimum interval between peaks in seconds.
        detection_mode: "positive" for positive-only peaks, "absolute" to
            detect peaks on |signal| while retaining the signed trace value.
        width_measure_mode: "peak_width" keeps the historical scipy
            half-prominence width gate; "duration_above_threshold" gates on
            the continuous threshold-crossing duration around the peak.
        duration_estimation_policy: "interpolated_threshold_crossing" keeps the
            historical continuous crossing estimate; "sample_span_conservative"
            measures only the span covered by observed above-threshold samples.

    Returns:
        dict with:
            n_peaks: int — number of detected peaks
            peaks: list[dict] — per-peak features
            threshold_used: float — the threshold that was applied
    """
    time_arr = np.asarray(time_s, dtype=float)
    signal_arr = np.asarray(signal_noisy, dtype=float)
    if context is None:
        context = build_pulse_extraction_context(
            time_arr,
            min_peak_width_s,
            min_peak_interval_s,
        )
    dt = float(context.dt_s)
    min_width_samples = int(context.min_width_samples)
    min_distance_samples = int(context.min_distance_samples)

    if detection_mode == "positive":
        signal_for_detection = signal_arr
    elif detection_mode == "absolute":
        signal_for_detection = np.abs(signal_arr)
    else:
        raise ValueError(
            f"detection_mode must be 'positive' or 'absolute', got {detection_mode}"
        )
    if width_measure_mode not in {"peak_width", "duration_above_threshold"}:
        raise ValueError(
            "width_measure_mode must be 'peak_width' or "
            f"'duration_above_threshold', got {width_measure_mode}"
        )
    if duration_estimation_policy not in {
        "interpolated_threshold_crossing",
        "sample_span_conservative",
    }:
        raise ValueError(
            "duration_estimation_policy must be 'interpolated_threshold_crossing' "
            f"or 'sample_span_conservative', got {duration_estimation_policy}"
        )

    if signal_for_detection.size == 0 or float(np.max(signal_for_detection)) < float(threshold):
        return {
            "n_peaks": 0,
            "peaks": [],
            "threshold_used": threshold,
            "detection_mode": detection_mode,
            "width_measure_mode": width_measure_mode,
            "duration_estimation_policy": duration_estimation_policy,
        }

    peak_kwargs = {
        "height": threshold,
        "distance": min_distance_samples,
    }
    if width_measure_mode == "peak_width":
        peak_kwargs["width"] = min_width_samples
    if include_area_prominence:
        peak_kwargs["prominence"] = 0

    peak_indices, properties = find_peaks(
        signal_for_detection,
        **peak_kwargs,
    )

    cumulative_area = None
    if include_area_prominence:
        cumulative_area = np.empty(signal_arr.size, dtype=float)
        cumulative_area[0] = 0.0
        if signal_arr.size > 1:
            cumulative_area[1:] = np.cumsum(
                0.5 * (signal_arr[:-1] + signal_arr[1:]) * (time_arr[1:] - time_arr[:-1])
            )

    peaks = []
    for i, idx in enumerate(peak_indices):
        height = float(properties["peak_heights"][i])
        signed_height = float(signal_arr[idx])
        peak_time = float(time_arr[idx])
        (
            threshold_duration_s,
            threshold_left,
            threshold_right,
            threshold_left_time_s,
            threshold_right_time_s,
        ) = (
            _threshold_crossing_duration_s(
                time_arr,
                signal_for_detection,
                int(idx),
                float(threshold),
                duration_estimation_policy=duration_estimation_policy,
            )
        )
        if width_measure_mode == "duration_above_threshold":
            if threshold_duration_s < float(min_peak_width_s):
                continue
            width_s = threshold_duration_s
            prominence_width_s = 0.0
        else:
            width_s = float(properties["widths"][i] * dt)
            prominence_width_s = width_s
        prominence = (
            float(properties["prominences"][i])
            if include_area_prominence
            else 0.0
        )

        # Area: use floor/ceil for floating-point boundary indices, clip to valid range
        if width_measure_mode == "peak_width":
            left = max(0, int(np.floor(properties["left_ips"][i])))
            right = min(len(signal_arr) - 1, int(np.ceil(properties["right_ips"][i])))
        else:
            left = threshold_left
            right = threshold_right

        if include_area_prominence and cumulative_area is not None and right > left:
            area = float(cumulative_area[right] - cumulative_area[left])
        else:
            area = 0.0

        peaks.append({
            "peak_time_s": peak_time,
            "peak_height": height,
            "peak_signed_height": signed_height,
            "peak_polarity": "negative" if signed_height < 0 else "positive",
            "peak_width_s": width_s,
            "peak_threshold_duration_s": threshold_duration_s,
            "peak_threshold_left_time_s": threshold_left_time_s,
            "peak_threshold_right_time_s": threshold_right_time_s,
            "peak_prominence_width_s": prominence_width_s,
            "peak_area": area,
            "prominence": prominence,
            "width_measure_mode": width_measure_mode,
            "duration_estimation_policy": duration_estimation_policy,
        })

    return {
        "n_peaks": len(peaks),
        "peaks": peaks,
        "threshold_used": threshold,
        "detection_mode": detection_mode,
        "width_measure_mode": width_measure_mode,
        "duration_estimation_policy": duration_estimation_policy,
    }


def _threshold_crossing_duration_s(
    time_s: np.ndarray,
    signal_for_detection: np.ndarray,
    peak_idx: int,
    threshold: float,
    *,
    duration_estimation_policy: str = "interpolated_threshold_crossing",
) -> tuple[float, int, int, float, float]:
    """Return contiguous above-threshold duration around one detected peak."""
    n = int(signal_for_detection.size)
    if n == 0:
        return 0.0, 0, 0, 0.0, 0.0
    left = int(peak_idx)
    while left > 0 and signal_for_detection[left - 1] >= threshold:
        left -= 1
    right = int(peak_idx)
    while right < n - 1 and signal_for_detection[right + 1] >= threshold:
        right += 1

    if duration_estimation_policy == "sample_span_conservative":
        if right <= left:
            left_t = float(time_s[left])
            right_t = float(time_s[right])
            return 0.0, left, right, left_t, right_t
        left_t = float(time_s[left])
        right_t = float(time_s[right])
        return max(0.0, right_t - left_t), left, right, left_t, right_t
    if duration_estimation_policy != "interpolated_threshold_crossing":
        raise ValueError(
            "duration_estimation_policy must be 'interpolated_threshold_crossing' "
            f"or 'sample_span_conservative', got {duration_estimation_policy}"
        )

    if left > 0:
        left_t = _interpolate_threshold_crossing_time(
            float(time_s[left - 1]),
            float(time_s[left]),
            float(signal_for_detection[left - 1]),
            float(signal_for_detection[left]),
            threshold,
        )
    else:
        left_t = float(time_s[left])

    if right < n - 1:
        right_t = _interpolate_threshold_crossing_time(
            float(time_s[right]),
            float(time_s[right + 1]),
            float(signal_for_detection[right]),
            float(signal_for_detection[right + 1]),
            threshold,
        )
    else:
        right_t = float(time_s[right])
    return max(0.0, right_t - left_t), left, right, left_t, right_t


def _interpolate_threshold_crossing_time(
    t0: float,
    t1: float,
    y0: float,
    y1: float,
    threshold: float,
) -> float:
    denom = y1 - y0
    if abs(denom) <= 1e-15:
        return t0
    frac = (threshold - y0) / denom
    frac = min(1.0, max(0.0, frac))
    return t0 + frac * (t1 - t0)
