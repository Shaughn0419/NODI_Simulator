"""
Detector-unit conversion boundary diagnostics.

The current simulator reports relative field / lock-in surrogate units. This
module names the missing physical chain explicitly so a future detector model
can be connected without confusing a lumped K_sca scale for power or voltage.
"""

from __future__ import annotations

from typing import Any

from .data_objects import OpticalSystem, SimulationConfig


def build_detector_unit_chain_boundary(
    sim_cfg: SimulationConfig,
    *,
    optical: OpticalSystem | None = None,
    collection_operator: dict[str, Any] | None = None,
    calibration_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the detector-unit chain contract for one case."""
    _ = optical
    operator = collection_operator or {}
    calibration = calibration_state or {}
    absolute_throughput_calibrated = bool(
        operator.get(
            "absolute_throughput_calibrated",
            calibration.get("absolute_throughput_calibrated", False),
        )
    )
    k_status = str(
        calibration.get(
            "K_sca_calibration_status",
            getattr(sim_cfg, "K_sca_calibration_status", "not_calibrated"),
        )
    )
    blockers = [
        "incident_power_density_not_bound_to_detector_unit_chain",
        "mie_dCsca_dOmega_not_integrated_to_scattered_power",
        "detector_etendue_not_calibrated",
        "photodiode_responsivity_not_configured",
        "transimpedance_gain_not_configured",
        "adc_conversion_not_configured",
        "lockin_voltage_gain_not_measured",
    ]
    if not absolute_throughput_calibrated:
        blockers.insert(2, "absolute_optical_throughput_not_calibrated")
    if k_status == "not_calibrated":
        blockers.append("K_sca_not_available_even_as_lumped_residual")
    elif "synthetic" in k_status:
        blockers.append("K_sca_synthetic_fixture_not_experimental")
    else:
        blockers.append("K_sca_lumped_residual_cannot_replace_power_chain")

    return {
        "detector_unit_chain_schema": "detector_unit_chain_v1",
        "detector_unit_chain_unlocked": False,
        "detector_unit_chain_status": (
            "blocked_missing_mie_to_power_and_detector_gain"
        ),
        "incident_power_density_status": (
            "configured_optical_peak_irradiance_not_detector_calibrated_power"
        ),
        "mie_differential_cross_section_status": (
            "available_as_dCsca_dOmega_not_converted_to_detector_power"
        ),
        "detector_etendue_status": "not_calibrated",
        "absolute_optical_throughput_status": (
            "calibrated_operator_table_available"
            if absolute_throughput_calibrated
            else "not_calibrated"
        ),
        "photodiode_responsivity_status": "not_configured",
        "transimpedance_gain_status": "not_configured",
        "adc_conversion_status": "not_configured",
        "lockin_voltage_unit_status": (
            "surrogate_units"
            if str(sim_cfg.lockin_output_unit_convention)
            == "arbitrary_lockin_output_units"
            else "unit_convention_declared_but_gain_chain_not_calibrated"
        ),
        "detector_unit_chain_blocker_summary": " / ".join(blockers),
    }
