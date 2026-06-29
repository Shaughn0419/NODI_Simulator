"""Hydraulic resistance and package-local fluidic-practicality diagnostics."""

from __future__ import annotations

import numpy as np

from .data_objects import Channel, Medium, Particle, SimulationConfig


FLUIDIC_RESISTANCE_DIAGNOSTIC_FIELDS = (
    "flow_control_mode",
    "hydraulic_resistance_Pa_s_m3",
    "pressure_required_for_target_velocity_Pa",
    "predicted_flow_rate_m3_s",
    "sample_consumption_pL_min",
    "residence_time_s",
    "fluidic_practicality_penalty",
    "fluidic_clogging_risk_band",
    "fluidic_clogging_risk_band_claim_level",
    "not_clogging_rate",
    "not_time_to_clog",
    "wall_interaction_risk_band",
    "accessible_cross_section_fraction",
    "nearest_wall_gap_D50_nm",
    "nearest_wall_gap_D90_nm",
    "fluidic_geometry_model",
    "hydraulic_resistance_model",
    "hydraulic_resistance_claim_level",
    "fluidic_geometry_propagation_status",
    "geometry_not_propagated_to_fluidic_resistance",
    "fluidic_practicality_status",
    "fixed_pressure_diagnostic_status",
)


def compute_rectangular_channel_hydraulic_resistance(
    width_m: float,
    depth_m: float,
    length_m: float,
    viscosity_Pa_s: float,
) -> float:
    """Return rectangular-channel pressure resistance using the shorter side cubed."""
    width = float(width_m)
    depth = float(depth_m)
    length = float(length_m)
    viscosity = float(viscosity_Pa_s)
    if width <= 0.0 or depth <= 0.0 or length <= 0.0 or viscosity <= 0.0:
        raise ValueError("width, depth, length, and viscosity must be positive")
    short_side = min(width, depth)
    long_side = max(width, depth)
    aspect = short_side / long_side
    correction = max(1.0 - 0.630 * aspect + 0.053 * aspect**5, 1e-6)
    return float(12.0 * viscosity * length / (long_side * short_side**3 * correction))


def _risk_from_gap(gap_nm: float, *, moderate_nm: float, high_nm: float) -> str:
    if gap_nm < high_nm:
        return "high"
    if gap_nm < moderate_nm:
        return "moderate"
    return "low"


def _penalty_from_band(band: str) -> float:
    return {"low": 0.0, "moderate": 0.5, "high": 1.0}.get(str(band), 0.5)


def compute_fluidic_practicality_penalty(
    particle: Particle,
    medium: Medium,
    channel: Channel,
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """Compute static P0 fluidic practicality diagnostics."""
    sidewall_active = (
        str(getattr(sim_cfg, "channel_cross_section_model", "ideal_rectangle"))
        == "trapezoid_tapered_sidewalls"
    )
    viscosity = float(medium.viscosity_Pa_s or 1.0e-3)
    area = float(channel.width_m * channel.depth_m)
    resistance = compute_rectangular_channel_hydraulic_resistance(
        channel.width_m,
        channel.depth_m,
        sim_cfg.fluidic_channel_length_m,
        viscosity,
    )
    target_flow_rate = float(sim_cfg.mean_flow_velocity_m_s * area)
    pressure_required = float(resistance * target_flow_rate)
    fixed_pressure_flow_rate = (
        float(sim_cfg.flow_control_pressure_Pa / resistance)
        if resistance > 0.0
        else 0.0
    )
    predicted_flow_rate = (
        fixed_pressure_flow_rate
        if str(sim_cfg.flow_control_mode) == "fixed_pressure"
        else target_flow_rate
    )
    active_velocity = predicted_flow_rate / max(area, 1e-30)
    residence_time = float(sim_cfg.fluidic_channel_length_m / max(active_velocity, 1e-30))
    sample_consumption = float(predicted_flow_rate * 60.0 * 1e15)

    diameter = float(2.0 * particle.radius_m)
    accessible_width = max(float(channel.width_m) - diameter, 0.0)
    accessible_depth = max(float(channel.depth_m) - diameter, 0.0)
    accessible_fraction = float((accessible_width * accessible_depth) / max(area, 1e-30))
    min_dimension = min(float(channel.width_m), float(channel.depth_m))
    nearest_gap_d50_nm = float(0.5 * (min_dimension - diameter) * 1e9)
    nearest_gap_d90_nm = float(0.5 * (min_dimension - 1.5 * diameter) * 1e9)

    clogging_band = _risk_from_gap(
        nearest_gap_d90_nm,
        moderate_nm=75.0,
        high_nm=25.0,
    )
    wall_band = _risk_from_gap(
        nearest_gap_d50_nm,
        moderate_nm=75.0,
        high_nm=25.0,
    )
    if str(sim_cfg.wall_interaction_model) != "none" and wall_band == "low":
        wall_band = "moderate"
    pressure_penalty = min(1.0, pressure_required / 100_000.0)
    accessibility_penalty = 1.0 - accessible_fraction
    penalty = float(
        np.clip(
            0.35 * pressure_penalty
            + 0.30 * _penalty_from_band(clogging_band)
            + 0.20 * _penalty_from_band(wall_band)
            + 0.15 * accessibility_penalty,
            0.0,
            1.0,
        )
    )
    fixed_pressure_status = (
        "active_sets_predicted_flow_rate"
        if str(sim_cfg.flow_control_mode) == "fixed_pressure"
        else "diagnostic_only_trajectory_uses_fixed_velocity"
    )
    if sidewall_active:
        fluidic_geometry_model = "trapezoid_descriptor_with_rectangular_proxy_fluidics"
        hydraulic_resistance_model = (
            "rectangular_hydraulic_resistance_proxy_under_trapezoid"
        )
        hydraulic_resistance_claim_level = (
            "proxy_not_trapezoid_poiseuille_not_accepted_for_formula_use"
        )
        fluidic_geometry_status = "geometry_not_propagated_to_fluidic_resistance"
        fixed_pressure_status = (
            "proxy_only_rectangular_resistance_under_trapezoid"
            if str(sim_cfg.flow_control_mode) == "fixed_pressure"
            else fixed_pressure_status
        )
    else:
        fluidic_geometry_model = "rectangular_static_hydraulic_proxy"
        hydraulic_resistance_model = "rectangular_hydraulic_resistance_proxy"
        hydraulic_resistance_claim_level = "rectangular_static_proxy_not_calibrated"
        fluidic_geometry_status = "rectangle_native_or_non_sidewall_geometry"

    return {
        "flow_control_mode": str(sim_cfg.flow_control_mode),
        "hydraulic_resistance_Pa_s_m3": resistance,
        "pressure_required_for_target_velocity_Pa": pressure_required,
        "predicted_flow_rate_m3_s": predicted_flow_rate,
        "sample_consumption_pL_min": sample_consumption,
        "residence_time_s": residence_time,
        "fluidic_practicality_penalty": penalty,
        "fluidic_clogging_risk_band": clogging_band,
        "fluidic_clogging_risk_band_claim_level": (
            "static_throat_clearance_proxy_not_clogging_rate"
        ),
        "not_clogging_rate": True,
        "not_time_to_clog": True,
        "wall_interaction_risk_band": wall_band,
        "accessible_cross_section_fraction": accessible_fraction,
        "nearest_wall_gap_D50_nm": nearest_gap_d50_nm,
        "nearest_wall_gap_D90_nm": nearest_gap_d90_nm,
        "fluidic_geometry_model": fluidic_geometry_model,
        "hydraulic_resistance_model": hydraulic_resistance_model,
        "hydraulic_resistance_claim_level": hydraulic_resistance_claim_level,
        "fluidic_geometry_propagation_status": fluidic_geometry_status,
        "geometry_not_propagated_to_fluidic_resistance": sidewall_active,
        "fluidic_practicality_status": "static_hydraulic_proxy_active",
        "fixed_pressure_diagnostic_status": fixed_pressure_status,
    }
