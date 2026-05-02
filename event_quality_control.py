"""Batch-level event QC and readout sign-governance diagnostics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .data_objects import SimulationConfig


EVENT_QC_DIAGNOSTIC_FIELDS = (
    "event_qc_schema_version",
    "event_qc_status",
    "event_qc_claim_level",
    "event_qc_pass_fraction",
    "event_qc_primary_failure_reason",
    "event_artifact_risk_score",
    "detected_rate_after_event_qc",
    "event_baseline_nonstationary",
    "event_pulse_width_out_of_range",
    "event_saturation_risk",
    "event_doublet_or_overlap_risk",
    "event_edge_clipped",
    "event_negative_positive_mismatch",
    "event_pod_nodi_pairing_mismatch",
    "event_shape_template_mismatch",
    "event_local_noise_burst",
    "event_qc_soft_gate_passed",
    "event_qc_hard_gate_passed",
    "event_qc_gate_passed",
    "signed_signal_available",
    "magnitude_readout_information_loss",
    "phase_sensitive_classification_allowed",
    "polarity_claim_allowed",
    "readout_sign_governance_status",
)

EVENT_ARTIFACT_RISK_WEIGHTS = {
    "failed_event_fraction": 0.55,
    "baseline_nonstationary": 0.15,
    "pulse_width_out_of_range": 0.15,
    "saturation_risk": 0.15,
    "doublet_or_overlap_risk": 0.10,
    "pairing_mismatch": 0.10,
    "local_noise_burst": 0.15,
    "phase_flip_fraction": 0.20,
}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bounded_probability(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _primary_failure(
    *,
    n_events: int,
    raw_detection_rate: float,
    pass_fraction: float,
    phase_flip_fraction: float,
    pulse_width_out_of_range: bool,
    baseline_nonstationary: bool,
    local_noise_burst: bool,
    saturation_risk: bool,
    doublet_or_overlap_risk: bool,
    pairing_mismatch: bool,
    artifact_risk_score: float,
    min_pass_fraction: float,
    max_artifact_risk_score: float,
) -> str:
    if n_events <= 0 or raw_detection_rate <= 0.0:
        return "no_detected_events"
    if pulse_width_out_of_range:
        return "pulse_width_out_of_range"
    if saturation_risk:
        return "saturation_risk"
    if pass_fraction < min_pass_fraction:
        return "low_stable_detected_fraction"
    if artifact_risk_score > max_artifact_risk_score:
        if local_noise_burst:
            return "local_noise_burst"
        if pairing_mismatch:
            return "pod_nodi_pairing_mismatch"
        if doublet_or_overlap_risk:
            return "doublet_or_overlap_risk"
        if phase_flip_fraction > 0.4:
            return "negative_positive_mismatch"
        if baseline_nonstationary:
            return "baseline_nonstationary"
        return "high_artifact_risk_score"
    return "none"


def build_event_quality_control_diagnostics(
    summary: Mapping[str, Any],
    sim_cfg: SimulationConfig,
    *,
    reference: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    """Export P0 batch-surrogate event QC and sign-governance fields."""
    reference = reference or {}
    n_events = int(_as_float(summary.get("n_events"), 0.0))
    raw_detection_rate = _bounded_probability(
        _as_float(summary.get("detection_rate"), 0.0)
    )
    stable_detection_rate = _bounded_probability(
        _as_float(summary.get("stable_detection_rate"), raw_detection_rate)
    )
    pass_fraction = (
        _bounded_probability(stable_detection_rate / raw_detection_rate)
        if raw_detection_rate > 0.0
        else 0.0
    )
    detected_rate_after_qc = min(raw_detection_rate, stable_detection_rate)

    mean_width_s = _as_float(summary.get("mean_peak_width_s"), 0.0)
    pulse_width_out_of_range = bool(
        mean_width_s > 0.0
        and (
            mean_width_s < 0.5 * float(sim_cfg.min_peak_width_s)
            or mean_width_s > 10.0 * float(sim_cfg.min_peak_width_s)
        )
    )
    baseline_nonstationary = bool(
        str(sim_cfg.noise_model) == "gaussian_plus_drift"
        or abs(float(sim_cfg.drift_slope)) > 0.0
        or abs(float(sim_cfg.post_readout_drift_slope)) > 0.0
    )
    phase_flip_fraction = _bounded_probability(
        _as_float(summary.get("phase_flip_fraction"), 0.0)
    )
    local_snr = _as_float(summary.get("mean_local_snr"), 0.0)
    local_noise_burst = bool(raw_detection_rate > 0.0 and local_snr < 1.0)
    saturation_status = str(
        summary.get(
            "detector_saturation_status",
            reference.get("detector_saturation_status", "not_evaluated_no_detector_range"),
        )
    )
    saturation_risk = saturation_status not in {
        "not_applied",
        "not_evaluated_no_detector_range",
        "within_range",
        "unknown",
    }
    doublet_or_overlap_risk = bool(
        sim_cfg.count_dead_time_s > 0.0
        and sim_cfg.min_peak_interval_s < 2.0 * sim_cfg.count_dead_time_s
    )
    pairing_mismatch = bool(
        str(sim_cfg.detection_decision_mode) == "paired_channel"
        and _as_float(summary.get("paired_detection_rate"), raw_detection_rate)
        < 0.5 * raw_detection_rate
    )
    artifact_risk_score = _bounded_probability(
        EVENT_ARTIFACT_RISK_WEIGHTS["failed_event_fraction"] * (1.0 - pass_fraction)
        + (
            EVENT_ARTIFACT_RISK_WEIGHTS["baseline_nonstationary"]
            if baseline_nonstationary
            else 0.0
        )
        + (
            EVENT_ARTIFACT_RISK_WEIGHTS["pulse_width_out_of_range"]
            if pulse_width_out_of_range
            else 0.0
        )
        + (
            EVENT_ARTIFACT_RISK_WEIGHTS["saturation_risk"]
            if saturation_risk
            else 0.0
        )
        + (
            EVENT_ARTIFACT_RISK_WEIGHTS["doublet_or_overlap_risk"]
            if doublet_or_overlap_risk
            else 0.0
        )
        + (
            EVENT_ARTIFACT_RISK_WEIGHTS["pairing_mismatch"]
            if pairing_mismatch
            else 0.0
        )
        + (
            EVENT_ARTIFACT_RISK_WEIGHTS["local_noise_burst"]
            if local_noise_burst
            else 0.0
        )
        + EVENT_ARTIFACT_RISK_WEIGHTS["phase_flip_fraction"] * phase_flip_fraction
    )

    event_qc_soft_gate_passed = bool(
        n_events > 0
        and pass_fraction >= float(sim_cfg.event_qc_min_pass_fraction)
        and artifact_risk_score <= float(sim_cfg.event_qc_max_artifact_risk_score)
    )
    event_qc_hard_gate_passed = bool(
        event_qc_soft_gate_passed
        and not pulse_width_out_of_range
        and not saturation_risk
    )
    primary_failure = _primary_failure(
        n_events=n_events,
        raw_detection_rate=raw_detection_rate,
        pass_fraction=pass_fraction,
        phase_flip_fraction=phase_flip_fraction,
        pulse_width_out_of_range=pulse_width_out_of_range,
        baseline_nonstationary=baseline_nonstationary,
        local_noise_burst=local_noise_burst,
        saturation_risk=saturation_risk,
        doublet_or_overlap_risk=doublet_or_overlap_risk,
        pairing_mismatch=pairing_mismatch,
        artifact_risk_score=artifact_risk_score,
        min_pass_fraction=float(sim_cfg.event_qc_min_pass_fraction),
        max_artifact_risk_score=float(sim_cfg.event_qc_max_artifact_risk_score),
    )

    signed_signal_available = str(sim_cfg.readout_observable_mode) == "in_phase"
    magnitude_information_loss = str(sim_cfg.readout_observable_mode) == "magnitude"
    phase_locked_claim_allowed = bool(
        reference.get("readout_phase_locked_claim_allowed", False)
    )
    polarity_claim_allowed = bool(signed_signal_available and phase_locked_claim_allowed)
    phase_sensitive_classification_allowed = bool(
        signed_signal_available
        and not magnitude_information_loss
        and phase_locked_claim_allowed
        and str(sim_cfg.nodi_readout_semantics) == "measured_transfer_function"
    )

    return {
        "event_qc_schema_version": "batch_surrogate_v1",
        "event_qc_status": (
            "batch_surrogate_active"
            if n_events > 0
            else "unavailable_no_events"
        ),
        "event_qc_claim_level": "batch_surrogate_not_empirical_event_qc",
        "event_qc_pass_fraction": pass_fraction if n_events > 0 else None,
        "event_qc_primary_failure_reason": primary_failure,
        "event_artifact_risk_score": artifact_risk_score if n_events > 0 else None,
        "detected_rate_after_event_qc": (
            detected_rate_after_qc if n_events > 0 else None
        ),
        "event_baseline_nonstationary": baseline_nonstationary,
        "event_pulse_width_out_of_range": pulse_width_out_of_range,
        "event_saturation_risk": saturation_risk,
        "event_doublet_or_overlap_risk": doublet_or_overlap_risk,
        "event_edge_clipped": False,
        "event_negative_positive_mismatch": phase_flip_fraction > 0.4,
        "event_pod_nodi_pairing_mismatch": pairing_mismatch,
        "event_shape_template_mismatch": False,
        "event_local_noise_burst": local_noise_burst,
        "event_qc_soft_gate_passed": event_qc_soft_gate_passed,
        "event_qc_hard_gate_passed": event_qc_hard_gate_passed,
        "event_qc_gate_passed": event_qc_hard_gate_passed,
        "signed_signal_available": signed_signal_available,
        "magnitude_readout_information_loss": magnitude_information_loss,
        "phase_sensitive_classification_allowed": (
            phase_sensitive_classification_allowed
        ),
        "polarity_claim_allowed": polarity_claim_allowed,
        "readout_sign_governance_status": (
            "magnitude_readout_blocks_polarity_and_phase_sensitive_claims"
            if magnitude_information_loss
            else "signed_surrogate_requires_phase_calibration_for_polarity_claim"
        ),
    }
