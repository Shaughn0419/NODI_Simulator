"""
NODI readout transfer semantics and claim governance.

P0.19 keeps the current lock-in surrogate as an engineering model, while making
the NODI event interpretation explicit: EV/NODI pulses are transient events, not
phase-locked carriers, unless a measured transfer-function route is active.
"""

from __future__ import annotations

import math

from .data_objects import SimulationConfig


READOUT_TRANSFER_DIAGNOSTIC_FIELDS = (
    "nodi_readout_semantics",
    "nodi_readout_semantics_claim_level",
    "nodi_readout_semantics_gate_passed",
    "nodi_readout_semantics_blocker_summary",
    "nodi_event_arrival_phase_policy",
    "nodi_bandpass_center_Hz",
    "nodi_bandpass_gain",
    "nodi_bandpass_phase",
    "nodi_random_arrival_phase_average_gain",
    "nodi_random_arrival_phase_i_variance_factor",
    "nodi_random_arrival_phase_q_variance_factor",
    "nodi_random_arrival_phase_magnitude_bias",
    "nodi_random_vs_locked_disagreement",
    "nodi_random_vs_locked_claim_degraded",
    "nodi_lockin_phase_bias_risk",
    "readout_phase_locked_claim_allowed",
    "readout_sampling_output_claim_blocker_active",
    "readout_numerical_route",
    "readout_numerical_route_claim_level",
)

_RANDOM_PHASE_AVERAGE_ABS_GAIN = 2.0 / math.pi
_RANDOM_PHASE_IQ_VARIANCE_FACTOR = 0.5
_RANDOM_VS_LOCKED_DEGRADE_THRESHOLD = 0.25


def _sampled_carrier_output_gate_passed(sim_cfg: SimulationConfig) -> bool:
    """Return whether the sampled-carrier route can support output claims."""
    route = str(sim_cfg.readout_internal_demod_route)
    if str(sim_cfg.readout_model) == "raw":
        return True
    analytic_envelope_route_used = bool(
        route == "analytic_lockin_surrogate"
        and str(sim_cfg.nodi_readout_semantics) == "bandpass_envelope_surrogate"
        and str(sim_cfg.readout_observable_mode) == "magnitude"
    )
    if analytic_envelope_route_used:
        return True
    # The measured route is declared but unimplemented, so it falls back to the
    # sampled-carrier surrogate and must obey the same sampling guard.
    max_lockin_frequency_hz = max(
        float(sim_cfg.pod_lockin_frequency_Hz),
        float(sim_cfg.nodi_lockin_frequency_Hz),
    )
    return bool(float(sim_cfg.sampling_rate_Hz) >= 10.0 * max_lockin_frequency_hz)


def build_nodi_readout_transfer_diagnostics(
    sim_cfg: SimulationConfig,
    *,
    observable_mode: str | None = None,
    sampling_hard_gate_passed: bool | None = None,
) -> dict[str, object]:
    """Return P0.19 NODI nonsynchronized readout semantics diagnostics."""
    observable = str(observable_mode or sim_cfg.readout_observable_mode)
    route = str(sim_cfg.readout_internal_demod_route)
    measured_transfer_declared = route == "measured_transfer_function"
    # No measured transfer-function table is wired into the runtime yet. Keep the
    # declared route visible, but do not let it promote claim eligibility.
    measured_transfer_used = False
    sampling_passed = (
        _sampled_carrier_output_gate_passed(sim_cfg)
        if sampling_hard_gate_passed is None
        else bool(sampling_hard_gate_passed)
    )

    nodi_readout_semantics = str(sim_cfg.nodi_readout_semantics)
    bandpass_center_hz = float(sim_cfg.nodi_lockin_frequency_Hz)
    bandpass_gain: float | None = 1.0
    bandpass_phase: float | None = None
    random_arrival_phase_average_gain: float | None = None
    random_arrival_phase_i_variance_factor: float | None = None
    random_arrival_phase_q_variance_factor: float | None = None
    random_arrival_phase_magnitude_bias: float | None = None
    random_vs_locked_disagreement: float | None = None
    random_vs_locked_claim_degraded = False

    if nodi_readout_semantics == "locked_carrier_surrogate":
        nodi_event_arrival_phase_policy = "locked_to_event_center_surrogate"
        nodi_semantics_claim_level = "legacy_debug_phase_locked_surrogate_not_ev_claim"
        nodi_lockin_phase_bias_risk = "high_for_transient_ev_events"
        nodi_semantics_gate_passed = False
        nodi_semantics_blocker = "locked_carrier_surrogate_not_valid_for_ev_nodi_claim"
        bandpass_phase = 0.0
    elif nodi_readout_semantics == "bandpass_envelope_surrogate":
        nodi_event_arrival_phase_policy = "transient_envelope_magnitude_governed"
        nodi_semantics_claim_level = "ev_transient_envelope_surrogate_not_measured_transfer"
        nodi_lockin_phase_bias_risk = (
            "mitigated_by_magnitude_governance"
            if observable == "magnitude"
            else "unresolved_signed_phase_bias"
        )
        nodi_semantics_gate_passed = observable == "magnitude"
        nodi_semantics_blocker = (
            "none"
            if nodi_semantics_gate_passed
            else "bandpass_envelope_requires_magnitude_governance"
        )
    elif nodi_readout_semantics == "random_arrival_phase_lockin":
        nodi_event_arrival_phase_policy = "random_arrival_phase_surrogate"
        random_arrival_phase_average_gain = _RANDOM_PHASE_AVERAGE_ABS_GAIN
        random_arrival_phase_i_variance_factor = _RANDOM_PHASE_IQ_VARIANCE_FACTOR
        random_arrival_phase_q_variance_factor = _RANDOM_PHASE_IQ_VARIANCE_FACTOR
        random_arrival_phase_magnitude_bias = (
            0.0 if observable == "magnitude" else 1.0 - _RANDOM_PHASE_AVERAGE_ABS_GAIN
        )
        random_vs_locked_disagreement = 1.0 - _RANDOM_PHASE_AVERAGE_ABS_GAIN
        random_vs_locked_claim_degraded = (
            random_vs_locked_disagreement >= _RANDOM_VS_LOCKED_DEGRADE_THRESHOLD
        )
        nodi_semantics_claim_level = (
            "random_arrival_phase_surrogate_degraded_from_locked_claim"
            if random_vs_locked_claim_degraded
            else "random_arrival_phase_surrogate_not_measured_transfer"
        )
        nodi_lockin_phase_bias_risk = (
            "large_locked_vs_random_disagreement"
            if random_vs_locked_claim_degraded
            else "phase_averaged_not_measured"
        )
        nodi_semantics_gate_passed = observable == "magnitude"
        nodi_semantics_blocker = (
            "none"
            if nodi_semantics_gate_passed
            else "random_arrival_phase_requires_magnitude_or_iq_distribution"
        )
    elif nodi_readout_semantics == "measured_transfer_function":
        nodi_event_arrival_phase_policy = "measured_transfer_function"
        nodi_semantics_claim_level = (
            "measured_transfer_function_declared_without_table"
        )
        nodi_lockin_phase_bias_risk = "measured_transfer_table_missing"
        nodi_semantics_gate_passed = measured_transfer_used
        nodi_semantics_blocker = (
            "none"
            if nodi_semantics_gate_passed
            else "measured_semantics_requires_measured_transfer_table"
        )
        bandpass_gain = 1.0 if measured_transfer_used else None
        bandpass_phase = 0.0 if measured_transfer_used else None
    else:
        nodi_event_arrival_phase_policy = "unknown"
        nodi_semantics_claim_level = "unknown_nodi_readout_semantics"
        nodi_lockin_phase_bias_risk = "unknown"
        nodi_semantics_gate_passed = False
        nodi_semantics_blocker = "unknown_nodi_readout_semantics"
        bandpass_gain = None

    readout_phase_locked_claim_allowed = bool(
        nodi_readout_semantics == "measured_transfer_function"
        and measured_transfer_used
    )
    if (
        route == "analytic_lockin_surrogate"
        and nodi_readout_semantics == "bandpass_envelope_surrogate"
        and observable == "magnitude"
    ):
        readout_numerical_route = "bandpass_envelope_response_surrogate"
        readout_numerical_route_claim_level = (
            "ev_transient_envelope_numerical_surrogate_not_measured_transfer"
        )
    elif str(sim_cfg.readout_model) == "raw":
        readout_numerical_route = "raw_detector_trace"
        readout_numerical_route_claim_level = "raw_detector_trace_no_readout_transfer"
    elif measured_transfer_declared:
        readout_numerical_route = "sampled_carrier_lockin_demod_surrogate"
        readout_numerical_route_claim_level = (
            "declared_measured_transfer_unimplemented_falls_back_to_carrier_surrogate"
        )
    elif route == "analytic_lockin_surrogate":
        readout_numerical_route = "sampled_carrier_lockin_demod_surrogate"
        readout_numerical_route_claim_level = (
            "declared_analytic_route_not_implemented_for_semantics_falls_back_to_carrier_surrogate"
        )
    else:
        readout_numerical_route = "sampled_carrier_lockin_demod_surrogate"
        readout_numerical_route_claim_level = (
            "carrier_lockin_surrogate_not_measured_transfer"
        )

    return {
        "nodi_readout_semantics": nodi_readout_semantics,
        "nodi_readout_semantics_claim_level": nodi_semantics_claim_level,
        "nodi_readout_semantics_gate_passed": nodi_semantics_gate_passed,
        "nodi_readout_semantics_blocker_summary": nodi_semantics_blocker,
        "nodi_event_arrival_phase_policy": nodi_event_arrival_phase_policy,
        "nodi_bandpass_center_Hz": bandpass_center_hz,
        "nodi_bandpass_gain": bandpass_gain,
        "nodi_bandpass_phase": bandpass_phase,
        "nodi_random_arrival_phase_average_gain": random_arrival_phase_average_gain,
        "nodi_random_arrival_phase_i_variance_factor": (
            random_arrival_phase_i_variance_factor
        ),
        "nodi_random_arrival_phase_q_variance_factor": (
            random_arrival_phase_q_variance_factor
        ),
        "nodi_random_arrival_phase_magnitude_bias": random_arrival_phase_magnitude_bias,
        "nodi_random_vs_locked_disagreement": random_vs_locked_disagreement,
        "nodi_random_vs_locked_claim_degraded": random_vs_locked_claim_degraded,
        "nodi_lockin_phase_bias_risk": nodi_lockin_phase_bias_risk,
        "readout_phase_locked_claim_allowed": readout_phase_locked_claim_allowed,
        "readout_sampling_output_claim_blocker_active": not sampling_passed,
        "readout_numerical_route": readout_numerical_route,
        "readout_numerical_route_claim_level": readout_numerical_route_claim_level,
    }
