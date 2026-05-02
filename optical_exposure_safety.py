"""Optical exposure and EV photodamage safety diagnostics."""

from __future__ import annotations

import math

from .data_objects import OpticalSystem, Particle, SimulationConfig


def _risk_from_density_and_temperature(
    power_density_W_m2: float,
    temperature_rise_K: float | None,
) -> str:
    if temperature_rise_K is not None and temperature_rise_K >= 5.0:
        return "high"
    if power_density_W_m2 >= 1.0e9:
        return "high"
    if temperature_rise_K is not None and temperature_rise_K >= 1.0:
        return "medium"
    if power_density_W_m2 >= 1.0e8:
        return "medium"
    return "low"


def build_optical_exposure_safety_diagnostics(
    particle: Particle,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    intrinsic: dict,
) -> dict[str, object]:
    """Export optical exposure safety blockers without calibrated safety claims."""
    geometry = optical.resolve_illumination_geometry()
    waist_x = float(geometry["illumination_beam_waist_x_m"])
    waist_z = float(geometry["illumination_beam_waist_z_m"])
    beam_area_m2 = math.pi * waist_x * waist_z
    if sim_cfg.probe_power_W is not None:
        laser_power_density = float(sim_cfg.probe_power_W) / max(beam_area_m2, 1e-30)
        power_density_source = "probe_power_divided_by_surrogate_waist_area"
    else:
        laser_power_density = float(optical.peak_irradiance_W_m2)
        power_density_source = "optical_peak_irradiance_metadata_no_probe_power"

    cabs = float(intrinsic.get("Cabs_m2", 0.0) or 0.0)
    particle_absorbed_power = max(cabs, 0.0) * laser_power_density
    thermal_conductivity_water_W_m_K = 0.6
    estimated_temperature_rise = (
        particle_absorbed_power
        / max(
            4.0
            * math.pi
            * thermal_conductivity_water_W_m_K
            * float(particle.radius_m),
            1e-30,
        )
        if particle.radius_m > 0.0
        else None
    )

    if sim_cfg.probe_power_W is None:
        ev_risk = "unknown_missing_probe_power_metadata"
        bubble_risk = "unknown_missing_probe_power_metadata"
        safe_claim = "blocked_missing_probe_power_metadata"
        gate_passed = False
    else:
        ev_risk = _risk_from_density_and_temperature(
            laser_power_density,
            estimated_temperature_rise,
        )
        bubble_risk = "high" if ev_risk == "high" else "not_high_by_surrogate"
        safe_claim = "proxy_from_probe_power_metadata_not_calibrated"
        gate_passed = False

    particle_name = str(particle.name).lower()
    material_key = str(particle.material_key or "").lower()
    is_gold_like = "gold" in particle_name or material_key == "gold"
    if is_gold_like and ev_risk in {"high", "medium"}:
        au_risk = ev_risk
    elif is_gold_like:
        au_risk = "low_by_surrogate"
    else:
        au_risk = "not_gold_standard"

    blocker_parts = []
    if sim_cfg.probe_power_W is None:
        blocker_parts.append("probe_power_missing")
    if safe_claim != "calibrated_or_bounded":
        blocker_parts.append("safe_power_not_calibrated_or_bounded")
    if ev_risk == "high":
        blocker_parts.append("ev_photodamage_risk_high")
    if bubble_risk == "high":
        blocker_parts.append("bubble_or_thermal_lens_artifact_risk_high")

    return {
        "laser_power_density_W_m2": laser_power_density,
        "laser_power_density_source": power_density_source,
        "particle_absorbed_power_proxy": particle_absorbed_power,
        "medium_absorption_heating_proxy": None,
        "wall_heating_proxy": None,
        "estimated_temperature_rise_K_surrogate": estimated_temperature_rise,
        "ev_photodamage_risk_band": ev_risk,
        "bubble_or_thermal_lens_artifact_risk": bubble_risk,
        "au_standard_thermal_artifact_risk": au_risk,
        "safe_power_claim_level": safe_claim,
        "optical_exposure_safety_gate_passed": gate_passed,
        "exposure_safety_not_red": ev_risk != "high" and bubble_risk != "high",
        "optical_exposure_safety_blocker_summary": (
            "none" if not blocker_parts else " / ".join(blocker_parts)
        ),
    }
