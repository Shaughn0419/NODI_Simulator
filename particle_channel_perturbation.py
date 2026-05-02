"""Particle-channel phase perturbation diagnostics and double-count guard."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from .data_objects import Channel, Medium, OpticalSystem, Particle, SimulationConfig


PARTICLE_CHANNEL_PERTURBATION_DIAGNOSTIC_FIELDS = (
    "particle_induced_channel_perturbation_model",
    "particle_channel_perturbation_application_mode",
    "particle_induced_channel_phase_perturbation_status",
    "delta_phi_particle_peak_rad",
    "particle_channel_projected_area_fraction",
    "delta_E_ref_particle_peak_abs",
    "delta_E_ref_particle_to_E_sca_ratio",
    "delta_E_ref_particle_to_E_ref_ratio",
    "particle_phase_perturbation_to_mie_forward_ratio",
    "double_counting_risk_band",
    "no_double_count_guard_passed",
    "particle_channel_perturbation_claim_level",
    "nodi_particle_induced_channel_coupling_status",
    "particle_channel_double_count_guard_status",
)


def _base_payload(sim_cfg: SimulationConfig) -> dict[str, object]:
    return {
        "particle_induced_channel_perturbation_model": str(
            sim_cfg.particle_induced_channel_perturbation_model
        ),
        "particle_channel_perturbation_application_mode": str(
            sim_cfg.particle_channel_perturbation_application_mode
        ),
        "particle_induced_channel_phase_perturbation_status": "not_evaluated",
        "delta_phi_particle_peak_rad": None,
        "particle_channel_projected_area_fraction": None,
        "delta_E_ref_particle_peak_abs": None,
        "delta_E_ref_particle_to_E_sca_ratio": None,
        "delta_E_ref_particle_to_E_ref_ratio": None,
        "particle_phase_perturbation_to_mie_forward_ratio": None,
        "double_counting_risk_band": "unavailable_particle_channel_guard_required",
        "no_double_count_guard_passed": False,
        "particle_channel_perturbation_claim_level": "unavailable",
        "nodi_particle_induced_channel_coupling_status": "unavailable",
        "particle_channel_double_count_guard_status": "unavailable",
    }


def _effective_particle_n_real(
    particle: Particle,
    medium_n: float,
    wavelength_m: float,
    intrinsic: Mapping[str, Any] | None,
) -> float:
    if intrinsic is not None and "effective_relative_index" in intrinsic:
        return float(np.real(complex(intrinsic["effective_relative_index"]) * medium_n))
    return float(np.real(particle.n_complex_at(wavelength_m)))


def _ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0.0 or not np.isfinite(denominator):
        return None
    return float(numerator / max(denominator, 1e-30))


def _risk_band(delta_to_sca_ratio: float | None) -> str:
    if delta_to_sca_ratio is None:
        return "unavailable_mie_forward_reference"
    if delta_to_sca_ratio > 0.3:
        return "high"
    if delta_to_sca_ratio > 0.1:
        return "moderate"
    return "low"


def build_particle_channel_perturbation_diagnostics(
    particle: Particle,
    medium: Medium,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    *,
    E_ref_complex: complex,
    E_sca_unit_normalized_complex: complex,
    intrinsic: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    """
    Build a diagnostic-only excluded-volume phase perturbation lane.

    The returned field is never added to the main `E_ref + E_sca` event path in
    P0. It exists to make particle-channel coupling and double-counting risk
    visible to claim governance.
    """
    payload = _base_payload(sim_cfg)
    model = str(sim_cfg.particle_induced_channel_perturbation_model)
    application_mode = str(sim_cfg.particle_channel_perturbation_application_mode)
    coherent_requested = application_mode == "coherent_addition_with_no_double_count_guard"

    if model == "not_applied":
        guard_passed = not coherent_requested
        payload.update(
            {
                "particle_induced_channel_phase_perturbation_status": (
                    "not_applied_no_channel_phase_surrogate"
                ),
                "double_counting_risk_band": (
                    "none_no_particle_channel_perturbation_added"
                ),
                "no_double_count_guard_passed": guard_passed,
                "particle_channel_perturbation_claim_level": (
                    "not_modeled_weak_superposition_assumed"
                ),
                "nodi_particle_induced_channel_coupling_status": (
                    "not_applied_not_added_to_score"
                ),
                "particle_channel_double_count_guard_status": (
                    "pass_no_particle_channel_term_added"
                    if guard_passed
                    else "blocked_coherent_application_without_perturbation_model"
                ),
            }
        )
        return payload

    if model != "excluded_volume_phase_surrogate":
        guard_passed = not coherent_requested
        payload.update(
            {
                "particle_induced_channel_phase_perturbation_status": (
                    f"{model}_not_implemented"
                ),
                "double_counting_risk_band": "unavailable_model_not_implemented",
                "no_double_count_guard_passed": guard_passed,
                "particle_channel_perturbation_claim_level": (
                    "model_interface_present_but_solver_not_implemented"
                ),
                "nodi_particle_induced_channel_coupling_status": (
                    "unavailable_not_added_to_score"
                ),
                "particle_channel_double_count_guard_status": (
                    "pass_not_added_to_main_score"
                    if guard_passed
                    else "blocked_coherent_application_without_validated_guard"
                ),
            }
        )
        return payload

    medium_n = float(medium.refractive_index_at(optical.wavelength_m))
    particle_n = _effective_particle_n_real(
        particle,
        medium_n,
        optical.wavelength_m,
        intrinsic,
    )
    path_length_eff_m = min(float(2.0 * particle.radius_m), float(channel.depth_m))
    delta_phi = (
        (2.0 * np.pi / float(optical.wavelength_m))
        * (particle_n - medium_n)
        * path_length_eff_m
    )
    channel_area_m2 = max(float(channel.width_m) * float(channel.depth_m), 1e-30)
    projected_area_fraction = min(
        1.0,
        float(np.pi * particle.radius_m**2) / channel_area_m2,
    )
    phase_object_amplitude = float(abs(np.exp(1j * delta_phi) - 1.0))
    E_ref_abs = float(abs(complex(E_ref_complex)))
    E_sca_abs = float(abs(complex(E_sca_unit_normalized_complex)))
    delta_E_ref_particle = E_ref_abs * phase_object_amplitude * projected_area_fraction
    delta_to_sca = _ratio(delta_E_ref_particle, E_sca_abs)
    delta_to_ref = _ratio(delta_E_ref_particle, E_ref_abs)
    risk_band = _risk_band(delta_to_sca)
    guard_passed = not coherent_requested

    if coherent_requested:
        guard_status = "blocked_coherent_application_without_validated_guard"
        claim_level = "blocked_coherent_addition_without_double_count_guard"
    elif application_mode == "alternative_forward_phase_lane":
        guard_status = "pass_alternative_lane_not_main_score"
        claim_level = "alternative_forward_lane_not_main_score"
    else:
        guard_status = "pass_diagnostic_only_not_added_to_main_score"
        claim_level = "diagnostic_only_excluded_volume_phase_surrogate"

    if risk_band == "high" and not coherent_requested:
        coupling_status = "diagnostic_only_particle_channel_coupling_high_not_in_score"
    elif risk_band == "moderate" and not coherent_requested:
        coupling_status = "diagnostic_only_particle_channel_coupling_caution"
    elif not coherent_requested:
        coupling_status = "diagnostic_only_particle_channel_coupling_low"
    else:
        coupling_status = "blocked_coherent_particle_channel_coupling"

    payload.update(
        {
            "particle_induced_channel_phase_perturbation_status": (
                "excluded_volume_phase_surrogate_active"
            ),
            "delta_phi_particle_peak_rad": float(delta_phi),
            "particle_channel_projected_area_fraction": projected_area_fraction,
            "delta_E_ref_particle_peak_abs": float(delta_E_ref_particle),
            "delta_E_ref_particle_to_E_sca_ratio": delta_to_sca,
            "delta_E_ref_particle_to_E_ref_ratio": delta_to_ref,
            "particle_phase_perturbation_to_mie_forward_ratio": delta_to_sca,
            "double_counting_risk_band": risk_band,
            "no_double_count_guard_passed": guard_passed,
            "particle_channel_perturbation_claim_level": claim_level,
            "nodi_particle_induced_channel_coupling_status": coupling_status,
            "particle_channel_double_count_guard_status": guard_status,
        }
    )
    return payload
