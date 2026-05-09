"""
Package-local interface-correction diagnostics.

The current optical solver uses homogeneous-medium Mie / coated-sphere Mie.
This module reports when that approximation is active, what a configured
interface route would claim to correct, and when a planar-interface or full-wave
route should be considered.
"""

from __future__ import annotations

from typing import Any

from .data_objects import Channel, Medium, OpticalSystem, Particle, SimulationConfig


def _particle_family(particle: Particle) -> str:
    name = str(particle.name)
    material_key = getattr(particle, "material_key", None)
    if (
        getattr(particle, "structure_key", None) == "exosome_biomimetic"
        or name.startswith("exosome_")
        or material_key == "exosome_uniform"
    ):
        return "EV_sEV"
    if str(material_key or "").startswith("gold") or name.startswith("gold_"):
        return "gold"
    if str(material_key or "").startswith("silver") or name.startswith("silver_"):
        return "silver"
    return str(material_key or "unknown")


def build_interface_correction_diagnostics(
    particle: Particle,
    medium: Medium,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
) -> dict[str, Any]:
    """Return interface-correction provenance for one optical case."""
    family = _particle_family(particle)
    radius_m = float(particle.radius_m)
    half_gap_m = max(min(float(channel.width_m), float(channel.depth_m)) / 2.0 - radius_m, 0.0)
    lambda_medium_m = float(optical.wavelength_m) / max(
        float(medium.refractive_index),
        1e-12,
    )
    eta_interface = radius_m / half_gap_m if half_gap_m > 0.0 else float("inf")
    eta_lambda = radius_m / max(lambda_medium_m, 1e-18)
    mode = str(sim_cfg.interface_correction_mode)
    applied_to = str(sim_cfg.interface_correction_applied_to)
    priority = str(sim_cfg.interface_correction_priority)
    phase_or_polarity_sensitive = (
        str(sim_cfg.readout_observable_mode) == "in_phase"
        or str(sim_cfg.pulse_detection_mode) == "absolute"
    )
    angular_pattern_sensitive = (
        str(sim_cfg.collection_angle_model) != "fixed"
        or str(sim_cfg.collection_integration_mode) != "single_angle"
    )
    output_sensitive = phase_or_polarity_sensitive or angular_pattern_sensitive
    if phase_or_polarity_sensitive and angular_pattern_sensitive:
        output_sensitivity_status = "phase_polarity_and_angular_pattern_sensitive"
    elif phase_or_polarity_sensitive:
        output_sensitivity_status = "phase_or_polarity_sensitive"
    elif angular_pattern_sensitive:
        output_sensitivity_status = "angular_pattern_sensitive"
    else:
        output_sensitivity_status = "intensity_only_fixed_angle"
    selected_family_active = applied_to == "all_particles" or (
        applied_to == "selected_family"
        and (
            priority == "all_particles"
            or (priority in {"EV_first", "exosome_first"} and family == "EV_sEV")
        )
    )
    correction_active = mode != "off" and selected_family_active

    fullwave_reasons: list[str] = []
    if eta_interface >= 0.5:
        fullwave_reasons.append("particle_radius_comparable_to_wall_gap")
    if eta_lambda >= 0.25:
        fullwave_reasons.append("particle_not_deep_subwavelength_in_medium")
    if output_sensitive:
        fullwave_reasons.append("phase_polarity_or_angular_pattern_output")
    if mode in {"planar_interface_tmatrix", "fullwave"}:
        fullwave_reasons.append(f"configured_{mode}")
    fullwave_required = bool(fullwave_reasons)

    if mode == "off":
        status = "homogeneous_medium_mie_no_interface_correction"
    elif correction_active:
        status = f"{mode}_configured"
    else:
        status = "configured_but_not_applied_to_particle_family"

    if correction_active and mode == "dipole_image_surrogate":
        incident = "unmodeled"
        polarizability = "dipole_image_first_order_surrogate"
        radiation = "dipole_image_collection_caution"
        claim = "first_order_near_interface_surrogate_not_fullwave"
    elif correction_active and mode == "planar_interface_tmatrix":
        incident = "planar_interface_route_requested"
        polarizability = "planar_interface_tmatrix_requested"
        radiation = "planar_interface_collection_requested"
        claim = "higher_fidelity_route_requested_not_current_solver"
    elif correction_active and mode == "fullwave":
        incident = "fullwave_route_requested"
        polarizability = "fullwave_route_requested"
        radiation = "fullwave_route_requested"
        claim = "fullwave_required_or_requested_not_current_solver"
    else:
        incident = "unmodeled"
        polarizability = "unmodeled"
        radiation = "unmodeled"
        claim = "homogeneous_medium_approximation"

    quantitative_blockers: list[str] = []
    if mode == "off" or not correction_active:
        quantitative_blockers.append("homogeneous_medium_interface_unmodeled")
    if correction_active and mode == "dipole_image_surrogate" and output_sensitive:
        quantitative_blockers.append(
            "dipole_image_surrogate_not_quantitative_for_sensitive_outputs"
        )
    if output_sensitive:
        quantitative_blockers.append(
            "phase_polarity_or_angular_pattern_requires_interface_solver"
        )
    if eta_interface >= 0.5:
        quantitative_blockers.append("near_wall_gap_requires_interface_solver")
    if eta_lambda >= 0.25:
        quantitative_blockers.append("finite_size_requires_interface_solver")
    blocker_summary = (
        "none" if not quantitative_blockers else "; ".join(quantitative_blockers)
    )
    if correction_active and mode == "dipole_image_surrogate":
        dipole_validity = (
            "first_order_only_not_quantitative_for_sensitive_outputs"
            if output_sensitive
            else "first_order_small_particle_surrogate"
        )
    else:
        dipole_validity = "not_applied"
    required_inputs = [
        "particle_position_distribution_relative_to_walls",
        "wall_material_complex_index_by_wavelength",
        "medium_complex_index_by_wavelength",
        "interface_green_function_or_tmatrix",
        "collection_operator_with_interface_radiation_pattern",
        "phase_polarity_validation_reference",
    ]
    missing_inputs = [
        "particle_position_distribution_relative_to_walls",
        "interface_green_function_or_tmatrix",
        "collection_operator_with_interface_radiation_pattern",
        "phase_polarity_validation_reference",
    ]
    if mode in {"planar_interface_tmatrix", "fullwave"}:
        missing_inputs.append("solver_implementation")

    return {
        "interface_correction_mode": mode,
        "interface_correction_input_contract_schema": (
            "interface_correction_input_contract_v1"
        ),
        "interface_required_inputs": ";".join(required_inputs),
        "interface_missing_inputs": ";".join(missing_inputs),
        "interface_api_boundary_status": (
            "blocked_missing_interface_solver_inputs"
            if missing_inputs
            else "inputs_declared"
        ),
        "interface_correction_status": status,
        "interface_correction_priority": priority,
        "interface_correction_applied_to": applied_to,
        "interface_correction_particle_family": family,
        "interface_correction_active": correction_active,
        "interface_incident_field_correction": incident,
        "interface_particle_polarizability_correction": polarizability,
        "interface_radiation_pattern_collection_correction": radiation,
        "interface_correction_claim_level": claim,
        "interface_output_sensitivity_status": output_sensitivity_status,
        "interface_phase_or_polarity_sensitive_output": bool(
            phase_or_polarity_sensitive
        ),
        "interface_angular_pattern_sensitive_output": bool(angular_pattern_sensitive),
        "interface_dipole_surrogate_validity": dipole_validity,
        "interface_quantitative_claim_blocker_summary": blocker_summary,
        "homogeneous_medium_mie_assumption": mode == "off" or not correction_active,
        "nearest_wall_gap_nominal_m": half_gap_m,
        "lambda_medium_m": lambda_medium_m,
        "eta_interface": float(eta_interface),
        "eta_lambda": float(eta_lambda),
        "interface_fullwave_required": fullwave_required,
        "interface_fullwave_reason": (
            " / ".join(fullwave_reasons) if fullwave_reasons else "not_required_by_nominal_thresholds"
        ),
        "interface_escalation_route": (
            "planar_interface_tmatrix_or_fullwave"
            if fullwave_required
            else "homogeneous_mie_with_visible_provenance"
        ),
    }
