"""
Photothermal POD provenance diagnostics.

The existing POD lane is a frequency-separated readout surrogate. This module
keeps that boundary explicit by reporting the missing thermal-source,
heat-diffusion, ROI-derivative, and wavelength-bookkeeping pieces required
before POD amplitude or sign can be treated as quantitative photothermal output.
"""

from __future__ import annotations

import math
from typing import Any

from .data_objects import OpticalSystem, SimulationConfig


_QUANTITATIVE_SIGN_SOURCES = {
    "ROI_integrated_dIdtheta",
    "recomputed_thermal_field",
    "measured_phase",
}


def _same_wavelength(lambda_a_m: float | None, lambda_b_m: float | None) -> bool:
    if lambda_a_m is None or lambda_b_m is None:
        return False
    return math.isclose(float(lambda_a_m), float(lambda_b_m), rel_tol=1e-9, abs_tol=1e-15)


def _blocker_summary(blockers: list[str]) -> str:
    return "none" if not blockers else "; ".join(blockers)


def _wavelength_group_id(prefix: str, wavelength_m: float | None) -> str | None:
    if wavelength_m is None:
        return None
    return f"{prefix}_{int(round(float(wavelength_m) * 1e9))}nm"


def build_photothermal_pod_diagnostics(
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
) -> dict[str, Any]:
    """Return thermal-POD provenance for one optical/readout case."""
    model = str(sim_cfg.thermal_pod_model)
    probe_wavelength_m = float(
        sim_cfg.probe_wavelength_m
        if sim_cfg.probe_wavelength_m is not None
        else optical.wavelength_m
    )
    excitation_wavelength_m = (
        float(sim_cfg.excitation_wavelength_m)
        if sim_cfg.excitation_wavelength_m is not None
        else None
    )
    wavelengths_separated = (
        excitation_wavelength_m is not None
        and not _same_wavelength(probe_wavelength_m, excitation_wavelength_m)
    )
    if excitation_wavelength_m is None:
        wavelength_status = "excitation_wavelength_not_configured"
        grouping_status = "single_probe_no_excitation_configured"
    elif wavelengths_separated:
        wavelength_status = "probe_and_excitation_wavelengths_separated"
        grouping_status = "probe_coherent_excitation_incoherent_separated"
    else:
        wavelength_status = "probe_and_excitation_wavelengths_identical"
        grouping_status = "same_wavelength_configured_but_excitation_not_added_to_probe_field"
    probe_reference_field_status = (
        "probe_E_ref_E_sca_use_current_optical_wavelength"
        if _same_wavelength(probe_wavelength_m, optical.wavelength_m)
        else "probe_wavelength_differs_from_optical_reference_not_recomputed"
    )

    roi_derivative_status = str(sim_cfg.pod_roi_sensitivity_derivative_status)
    sign_source = str(sim_cfg.pod_signal_sign_source)
    roi_derivative_validity = str(sim_cfg.pod_roi_derivative_validity)
    thermal_spatial_status = str(sim_cfg.pod_thermal_spatial_distribution_status)
    sign_available = (
        sign_source in _QUANTITATIVE_SIGN_SOURCES
        and (
            roi_derivative_status == "field_derivative"
            or sign_source in {"recomputed_thermal_field", "measured_phase"}
        )
    )

    blockers = []
    if model == "unavailable":
        model_status = "unavailable_no_heat_diffusion_model"
        claim_level = "unavailable_frequency_lane_surrogate_only"
        blockers.append("thermal_pod_model_unavailable")
    elif model == "surrogate_frequency_lane":
        model_status = "surrogate_frequency_lane_not_photothermal_model"
        claim_level = "qualitative_frequency_separation_surrogate_only"
        blockers.append("frequency_lane_surrogate_not_photothermal_pde")
    else:
        model_status = "thermal_diffusion_requested_but_not_implemented"
        claim_level = "thermal_route_requested_without_solver"
        blockers.append("heat_diffusion_solver_not_implemented")

    if excitation_wavelength_m is None:
        blockers.append("excitation_wavelength_missing")
    if sim_cfg.excitation_power_W is None:
        blockers.append("excitation_power_missing")
    if sim_cfg.probe_power_W is None:
        blockers.append("probe_power_missing")
    if roi_derivative_status != "field_derivative":
        blockers.append("ROI_integrated_dIdtheta_missing")
    if thermal_spatial_status != "coupled_optical_thermal":
        blockers.append("thermal_spatial_distribution_not_coupled")
    if roi_derivative_validity != "validated":
        blockers.append("pod_roi_derivative_not_validated")
    if not sign_available:
        blockers.append("quantitative_POD_sign_source_missing")
    if probe_reference_field_status.endswith("not_recomputed"):
        blockers.append("probe_reference_field_not_recomputed")

    required_inputs = [
        "excitation_wavelength_m",
        "excitation_power_W",
        "probe_power_W",
        "absorption_cross_section_at_excitation",
        "heat_diffusion_solver",
        "solvent_dn_dT_by_probe_wavelength",
        "ROI_integrated_dIdtheta",
        "detector_responsivity_by_probe_wavelength",
        "spectral_filter_transmission",
        "modulation_response",
    ]
    provided_inputs = {
        "excitation_wavelength_m": excitation_wavelength_m is not None,
        "excitation_power_W": sim_cfg.excitation_power_W is not None,
        "probe_power_W": sim_cfg.probe_power_W is not None,
        "ROI_integrated_dIdtheta": roi_derivative_status == "field_derivative",
    }
    missing_contract_inputs = [
        item for item in required_inputs if not bool(provided_inputs.get(item, False))
    ]

    heat_diffusion_status = "not_implemented"
    absorption_status = (
        "not_available_no_excitation_wavelength"
        if excitation_wavelength_m is None
        else "not_computed_for_excitation_wavelength"
    )
    heat_source_status = (
        "not_available_missing_excitation_wavelength_or_power"
        if excitation_wavelength_m is None or sim_cfg.excitation_power_W is None
        else "not_implemented_absorption_to_heat_source"
    )
    solvent_dn_dt_status = "not_configured_by_probe_wavelength"
    solvent_dn_dt_source = "not_configured"
    detector_responsivity_status = "not_configured_by_probe_wavelength"
    detector_responsivity_source = "not_configured"
    spectral_filter_status = "not_configured_by_probe_wavelength"
    spectral_filter_source = "not_configured"
    modulation_response_status = "not_implemented"
    substrate_heat_status = "not_implemented"
    blockers.extend(
        [
            "absorption_cross_section_missing",
            "thermal_heat_source_missing",
            "solvent_dn_dT_missing",
            "detector_responsivity_missing",
            "spectral_filter_transmission_missing",
            "modulation_response_missing",
        ]
    )
    if model == "thermal_diffusion":
        amplitude_boundary = "thermal_diffusion_route_requested_without_solver"
    else:
        amplitude_boundary = "frequency_lane_surrogate_not_absolute_photothermal_amplitude"

    return {
        "thermal_pod_model": model,
        "thermal_pod_input_contract_schema": "thermal_pod_input_contract_v1",
        "thermal_pod_required_inputs": ";".join(required_inputs),
        "thermal_pod_missing_inputs": ";".join(missing_contract_inputs),
        "thermal_pod_api_boundary_status": (
            "blocked_missing_required_inputs_or_solver"
            if missing_contract_inputs or model != "thermal_diffusion"
            else "thermal_diffusion_inputs_declared_solver_still_unimplemented"
        ),
        "thermal_pod_model_status": model_status,
        "pod_quantitative_amplitude_available": False,
        "pod_quantitative_sign_available": bool(sign_available),
        "pod_quantitative_claim_level": claim_level,
        "probe_wavelength_m": probe_wavelength_m,
        "excitation_wavelength_m": excitation_wavelength_m,
        "probe_power_W": sim_cfg.probe_power_W,
        "excitation_power_W": sim_cfg.excitation_power_W,
        "pod_quantitative_route_status": (
            "blocked_missing_thermal_forward_model_or_calibration"
        ),
        "pod_amplitude_model_boundary": amplitude_boundary,
        "probe_wavelength_source": (
            "sim_cfg.probe_wavelength_m"
            if sim_cfg.probe_wavelength_m is not None
            else "optical.wavelength_m"
        ),
        "pod_probe_reference_field_status": probe_reference_field_status,
        "probe_coherent_field_group_id": _wavelength_group_id(
            "probe",
            probe_wavelength_m,
        ),
        "excitation_incoherent_power_group_id": _wavelength_group_id(
            "excitation",
            excitation_wavelength_m,
        ),
        "pod_probe_excitation_wavelength_status": wavelength_status,
        "pod_wavelength_grouping_status": grouping_status,
        "multi_wavelength_coherent_addition_policy": "same_probe_wavelength_only",
        "multi_wavelength_power_addition_policy": "excitation_absorption_incoherent_only",
        "probe_excitation_wavelengths_separated": bool(wavelengths_separated),
        "probe_wavelength_fields_add_coherently": True,
        "excitation_wavelength_fields_never_add_to_probe_E_ref_E_sca": True,
        "pod_roi_sensitivity_derivative_status": roi_derivative_status,
        "pod_signal_sign_source": sign_source,
        "pod_thermal_spatial_distribution_status": thermal_spatial_status,
        "pod_roi_derivative_validity": roi_derivative_validity,
        "pod_absorption_cross_section_status": absorption_status,
        "pod_excitation_absorption_cross_section_status": absorption_status,
        "pod_heat_source_status": heat_source_status,
        "pod_heat_diffusion_status": heat_diffusion_status,
        "pod_solvent_dn_dT_status": solvent_dn_dt_status,
        "pod_solvent_dn_dT_source": solvent_dn_dt_source,
        "pod_substrate_heat_contribution_status": substrate_heat_status,
        "pod_detector_responsivity_status": detector_responsivity_status,
        "pod_detector_responsivity_source": detector_responsivity_source,
        "pod_spectral_filter_status": spectral_filter_status,
        "pod_spectral_filter_source": spectral_filter_source,
        "pod_modulation_response_status": modulation_response_status,
        "pod_thermal_validation_status": "not_validated",
        "pod_amplitude_quantitative_blocker_summary": _blocker_summary(blockers),
    }
