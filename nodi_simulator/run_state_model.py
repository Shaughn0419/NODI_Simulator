"""Run-state drift, fouling, and reblank diagnostics."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from .data_objects import SimulationConfig
from .type_coerce import finite_float as _as_float


RUN_STATE_DIAGNOSTIC_FIELDS = (
    "run_state_model_status",
    "run_state_claim_level",
    "run_state_measured_trace_available",
    "run_state_calibration_status",
    "run_state_stationarity_score",
    "run_state_stationarity_band",
    "reference_drift_rate_per_min",
    "raw_reference_drift_rate_per_min",
    "post_readout_drift_rate_per_min",
    "run_state_signal_scale",
    "run_state_drift_fraction_per_min",
    "run_state_fouling_index_per_min",
    "run_state_flow_drift_fraction_per_min",
    "recommended_reblank_interval_min",
    "recommended_reblank_basis",
    "run_state_gate_passed",
)

def _signal_scale(summary: Mapping[str, Any], sim_cfg: SimulationConfig) -> float:
    candidates = (
        abs(_as_float(summary.get("mean_peak_height"), 0.0)),
        abs(_as_float(summary.get("median_peak_height"), 0.0)),
        abs(_as_float(summary.get("mean_peak_margin_z"), 0.0)),
        abs(_as_float(summary.get("population_trace_threshold"), 0.0)),
        abs(_as_float(summary.get("mean_threshold_robust_std"), 0.0))
        * max(float(sim_cfg.threshold_sigma), 1.0),
        abs(float(sim_cfg.noise_std)) * max(float(sim_cfg.threshold_sigma), 1.0),
        abs(float(sim_cfg.post_readout_noise_std))
        * max(float(sim_cfg.threshold_sigma), 1.0),
    )
    return max(max(candidates), 1.0e-12)


def _fouling_index_per_min(sim_cfg: SimulationConfig) -> float:
    adsorption = max(float(sim_cfg.adsorption_probability_per_length_m), 0.0)
    if adsorption <= 0.0:
        return 0.0
    exposure_per_min = adsorption * float(sim_cfg.mean_flow_velocity_m_s) * 60.0
    return float(1.0 - math.exp(-exposure_per_min))


def _recommended_interval_min(
    *,
    signal_scale: float,
    drift_slope_per_s: float,
    fouling_index_per_min: float,
    allowed_fraction: float = 0.10,
) -> tuple[float | None, str]:
    intervals: list[tuple[float, str]] = []
    if abs(drift_slope_per_s) > 0.0:
        intervals.append(
            (
                allowed_fraction * signal_scale / abs(drift_slope_per_s) / 60.0,
                "drift_limited",
            )
        )
    if fouling_index_per_min > 0.0:
        intervals.append((allowed_fraction / fouling_index_per_min, "fouling_limited"))
    finite_intervals = [
        (interval, basis)
        for interval, basis in intervals
        if math.isfinite(interval) and interval > 0.0
    ]
    if not finite_intervals:
        return None, "not_required_by_synthetic_config"
    return min(finite_intervals, key=lambda item: item[0])


def _stationarity_band(score: float) -> str:
    if score >= 0.9:
        return "stable"
    if score >= 0.7:
        return "monitor_reblank_recommended"
    if score >= 0.5:
        return "unstable_reblank_required"
    return "strongly_unstable_run_state"


def build_run_state_diagnostics(
    summary: Mapping[str, Any],
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """Build synthetic run-state diagnostics from configured drift/loss metadata."""
    scale = _signal_scale(summary, sim_cfg)
    raw_drift_slope = float(sim_cfg.drift_slope)
    post_readout_drift_slope = float(sim_cfg.post_readout_drift_slope)
    total_drift_slope = raw_drift_slope + post_readout_drift_slope
    raw_drift_rate_per_min = raw_drift_slope * 60.0
    post_drift_rate_per_min = post_readout_drift_slope * 60.0
    reference_drift_rate_per_min = total_drift_slope * 60.0
    drift_fraction_per_min = abs(reference_drift_rate_per_min) / scale
    fouling_index = _fouling_index_per_min(sim_cfg)
    flow_drift_fraction_per_min = 0.0

    stationarity_score = 1.0 / (
        1.0
        + drift_fraction_per_min
        + fouling_index
        + flow_drift_fraction_per_min
    )
    reblank_interval_min, reblank_basis = _recommended_interval_min(
        signal_scale=scale,
        drift_slope_per_s=total_drift_slope,
        fouling_index_per_min=fouling_index,
    )

    measured_trace_available = False
    return {
        "run_state_model_status": "synthetic_config_diagnostic_active",
        "run_state_claim_level": "diagnostic_only_no_measured_run_trace",
        "run_state_measured_trace_available": measured_trace_available,
        "run_state_calibration_status": "not_calibrated_no_measured_run_trace",
        "run_state_stationarity_score": stationarity_score,
        "run_state_stationarity_band": _stationarity_band(stationarity_score),
        "reference_drift_rate_per_min": reference_drift_rate_per_min,
        "raw_reference_drift_rate_per_min": raw_drift_rate_per_min,
        "post_readout_drift_rate_per_min": post_drift_rate_per_min,
        "run_state_signal_scale": scale,
        "run_state_drift_fraction_per_min": drift_fraction_per_min,
        "run_state_fouling_index_per_min": fouling_index,
        "run_state_flow_drift_fraction_per_min": flow_drift_fraction_per_min,
        "recommended_reblank_interval_min": reblank_interval_min,
        "recommended_reblank_basis": reblank_basis,
        "run_state_gate_passed": True,
    }
