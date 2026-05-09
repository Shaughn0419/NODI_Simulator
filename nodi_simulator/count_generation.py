"""
Package-local concentration-to-count diagnostics.

This module keeps experiment-level count-rate semantics separate from the
existing per-event detectability simulation. The first route is intentionally a
small Poisson flux + non-paralyzable dead-time model, with explicit provenance
for wall interaction and occupancy assumptions.
"""

from __future__ import annotations

import math
from typing import Any

from .data_objects import Channel, Particle, SimulationConfig


def _accessible_cross_section_area_m2(
    channel: Channel,
    particle_radius_m: float,
) -> tuple[float, str]:
    width = float(channel.width_m) - 2.0 * float(particle_radius_m)
    depth = float(channel.depth_m) - 2.0 * float(particle_radius_m)
    if width <= 0.0 or depth <= 0.0:
        return 0.0, "particle_excluded_by_channel_geometry"
    return float(width * depth), "hard_exclusion_accessible_area"


def _poisson_multi_occupancy_probability(mean_occupancy: float) -> float:
    lam = max(float(mean_occupancy), 0.0)
    return float(1.0 - math.exp(-lam) * (1.0 + lam))


def build_count_model_diagnostics(
    particle: Particle,
    channel: Channel,
    sim_cfg: SimulationConfig,
    *,
    conditional_detection_rate: float | None = None,
    conditional_detection_rate_source: str = "provided_event_detection_rate",
    mean_transit_time_s: float | None = None,
    blank_false_positive_rate_Hz: float | None = None,
) -> dict[str, Any]:
    """
    Build concentration-to-count provenance for one batch summary.

    `conditional_detection_rate` is copied from the existing event-conditioned
    batch metric. This helper never rewrites it; count prediction lives in
    separate fields so dead time and multi-occupancy do not pollute per-event
    detectability.
    """
    accessible_area_m2, accessible_area_status = _accessible_cross_section_area_m2(
        channel,
        particle.radius_m,
    )
    volumetric_flow_rate_m3_s = float(sim_cfg.mean_flow_velocity_m_s) * accessible_area_m2
    model = str(sim_cfg.count_prediction_model)
    concentration = sim_cfg.number_concentration_m3
    observation_window_s = float(
        sim_cfg.count_observation_window_s
        if sim_cfg.count_observation_window_s is not None
        else sim_cfg.total_time_s
    )
    dead_time_s = float(sim_cfg.count_dead_time_s)
    conditional_rate = float(conditional_detection_rate or 0.0)
    conditional_rate_source = str(conditional_detection_rate_source)
    event_qc_conditioned_rate = (
        conditional_rate_source == "detected_rate_after_event_qc"
    )
    occupancy_window_s = float(
        mean_transit_time_s
        if mean_transit_time_s is not None and mean_transit_time_s > 0.0
        else max(dead_time_s, sim_cfg.min_peak_width_s)
    )
    blank_fp_rate = float(blank_false_positive_rate_Hz or 0.0)

    if model == "not_applied":
        status = "not_applied_per_event_detection_only"
        poisson_status = "not_applied_count_prediction_disabled"
        event_rate_Hz = None
        expected_events = None
        detected_event_rate_Hz = None
        dead_time_limited_rate_Hz = None
        predicted_count_rate_Hz = None
        predicted_counts = None
        missed_event_rate_Hz = None
        dead_time_loss_fraction = None
        focus_occupancy_mean = None
        multi_occupancy_probability = None
    elif concentration is None:
        status = "disabled_no_number_concentration"
        poisson_status = "not_applied_missing_number_concentration"
        event_rate_Hz = None
        expected_events = None
        detected_event_rate_Hz = None
        dead_time_limited_rate_Hz = None
        predicted_count_rate_Hz = None
        predicted_counts = None
        missed_event_rate_Hz = None
        dead_time_loss_fraction = None
        focus_occupancy_mean = None
        multi_occupancy_probability = None
    else:
        poisson_status = "poisson_arrival_process_surrogate_active"
        event_rate_Hz = float(concentration) * volumetric_flow_rate_m3_s
        expected_events = event_rate_Hz * observation_window_s
        detected_event_rate_Hz = event_rate_Hz * conditional_rate
        if dead_time_s > 0.0:
            dead_time_limited_rate_Hz = detected_event_rate_Hz / (
                1.0 + detected_event_rate_Hz * dead_time_s
            )
        else:
            dead_time_limited_rate_Hz = detected_event_rate_Hz
        predicted_count_rate_Hz = dead_time_limited_rate_Hz + blank_fp_rate
        predicted_counts = predicted_count_rate_Hz * observation_window_s
        missed_event_rate_Hz = event_rate_Hz * max(1.0 - conditional_rate, 0.0)
        dead_time_loss_fraction = (
            1.0 - dead_time_limited_rate_Hz / detected_event_rate_Hz
            if detected_event_rate_Hz > 0.0
            else 0.0
        )
        focus_occupancy_mean = event_rate_Hz * occupancy_window_s
        multi_occupancy_probability = _poisson_multi_occupancy_probability(
            focus_occupancy_mean
        )
        status = "poisson_flux_deadtime_surrogate_active"

    blank_fp_status = (
        "empirical_blank_false_positive_rate_added"
        if blank_fp_rate > 0.0
        else "not_applied_no_empirical_blank_rate"
    )
    missed_event_status = (
        (
            "event_qc_conditioned_detection_rate_applied_to_flux"
            if event_qc_conditioned_rate
            else "conditional_detection_rate_applied_to_flux"
        )
        if predicted_count_rate_Hz is not None
        else "not_applied_without_count_prediction"
    )
    dead_time_status = (
        "nonparalyzable_dead_time_applied"
        if predicted_count_rate_Hz is not None and dead_time_s > 0.0
        else (
            "dead_time_zero_no_rate_limiting"
            if predicted_count_rate_Hz is not None
            else "not_applied_without_count_prediction"
        )
    )
    occupancy_status = (
        "poisson_focus_occupancy_estimated"
        if multi_occupancy_probability is not None
        else "not_evaluated_without_count_prediction"
    )

    wall_model = str(sim_cfg.wall_interaction_model)
    if wall_model == "none":
        wall_status = "wall_interaction_unmodeled"
    elif wall_model == "hard_exclusion":
        wall_status = "hard_exclusion_accessible_area_only"
    else:
        wall_status = "configured_wall_loss_metadata_not_applied_to_flux"

    return {
        "conditional_detection_rate": conditional_rate,
        "conditional_detection_rate_definition": (
            "given_one_particle_event_after_event_qc"
            if event_qc_conditioned_rate
            else "given_one_particle_event"
        ),
        "conditional_detection_rate_source": conditional_rate_source,
        "count_generation_model": "per_event_batch_plus_optional_poisson_flux",
        "per_event_detectability_boundary": (
            "conditional_detection_rate_not_experiment_count_rate"
        ),
        "count_prediction_model": model,
        "count_prediction_status": status,
        "count_prediction_claim_level": (
            "per_event_only"
            if predicted_count_rate_Hz is None
            else "poisson_flux_deadtime_surrogate"
        ),
        "number_concentration_m3": concentration,
        "count_observation_window_s": observation_window_s,
        "accessible_area_m2": accessible_area_m2,
        "accessible_area_status": accessible_area_status,
        "volumetric_flow_rate_m3_s": volumetric_flow_rate_m3_s,
        "volumetric_flow_rate_source": (
            "mean_flow_velocity_times_hard_exclusion_accessible_area"
        ),
        "poisson_arrival_process_status": poisson_status,
        "flux_conditioned_initial_distribution_status": (
            "not_implemented_event_positions_sampled_by_transport_surrogate"
        ),
        "crossing_conditioned_transport_status": (
            "not_implemented_uses_existing_per_event_initial_distribution"
        ),
        "event_rate_Hz": event_rate_Hz,
        "expected_events_in_window": expected_events,
        "detected_event_rate_before_deadtime_Hz": detected_event_rate_Hz,
        "predicted_count_rate_Hz": predicted_count_rate_Hz,
        "predicted_counts_in_window": predicted_counts,
        "missed_event_rate_Hz": missed_event_rate_Hz,
        "count_dead_time_s": dead_time_s,
        "dead_time_model": "nonparalyzable" if predicted_count_rate_Hz is not None else None,
        "dead_time_limited_count_rate_Hz": dead_time_limited_rate_Hz,
        "dead_time_loss_fraction": dead_time_loss_fraction,
        "blank_false_positive_rate_Hz": blank_fp_rate,
        "blank_false_positive_correction_status": blank_fp_status,
        "missed_event_correction_status": missed_event_status,
        "multi_occupancy_window_s": occupancy_window_s,
        "focus_occupancy_mean": focus_occupancy_mean,
        "multi_occupancy_probability": multi_occupancy_probability,
        "occupancy_correction_status": occupancy_status,
        "dead_time_correction_status": dead_time_status,
        "single_particle_condition_status": (
            "not_evaluated"
            if multi_occupancy_probability is None
            else (
                "single_particle_condition_likely"
                if multi_occupancy_probability < 0.01
                else "multi_occupancy_caution"
            )
        ),
        "wall_interaction_model": wall_model,
        "wall_interaction_status": wall_status,
        "zeta_potential_particle_mV": sim_cfg.zeta_potential_particle_mV,
        "zeta_potential_wall_mV": sim_cfg.zeta_potential_wall_mV,
        "ionic_strength_M": sim_cfg.ionic_strength_M,
        "adsorption_probability_per_length_m": sim_cfg.adsorption_probability_per_length_m,
        "adsorption_or_clogging_exclusion_status": (
            "not_modeled"
            if wall_model in {"none", "hard_exclusion"}
            else "metadata_only_not_applied_to_count_rate"
        ),
        "count_rate_source": (
            (
                "event_qc_conditioned_detection_rate_times_poisson_flux"
                if event_qc_conditioned_rate
                else "conditional_detection_rate_times_poisson_flux"
            )
            if predicted_count_rate_Hz is not None
            else "not_predicted"
        ),
        "count_rate_confidence_status": (
            "not_available_no_blank_false_positive_or_uncertainty_propagation"
        ),
        "count_prediction_uncertainty_status": "not_propagated",
    }
