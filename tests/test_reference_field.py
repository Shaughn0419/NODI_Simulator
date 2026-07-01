from __future__ import annotations

import numpy as np
import pytest

from nodi_simulator.data_objects import Channel, OpticalSystem, SimulationConfig
from nodi_simulator.reference_field import (
    compute_reference_field,
    compute_reference_field_trace,
)


def _channel() -> Channel:
    return Channel(width_m=800e-9, depth_m=1400e-9)


def _optical() -> OpticalSystem:
    return OpticalSystem(
        wavelength_m=660e-9,
        peak_irradiance_W_m2=1.0e8,
        beam_waist_x_m=1.0e-6,
        beam_waist_y_m=1.0e-6,
        beam_waist_z_m=1.0e-6,
    )


def test_constant_reference_field_exports_complex_amplitude_without_calibration_claim():
    cfg = SimulationConfig(
        total_time_s=1.0e-3,
        sampling_rate_Hz=10_000.0,
        mean_flow_velocity_m_s=2.0e-4,
        rho=7.0,
        reference_model="constant",
    )

    reference = compute_reference_field(_channel(), _optical(), cfg)

    assert reference["A_ref"] == pytest.approx(7.0)
    assert reference["E_ref_complex"] == pytest.approx(7.0 + 0.0j)
    assert reference["reference_calibration_amplitude_status"] == "not_calibrated"
    assert reference["reference_phase_absolute_claim"] == "not_measured_absolute_phase"


def test_reference_trace_preserves_time_grid_and_case_anchor_amplitude():
    channel = _channel()
    optical = _optical()
    cfg = SimulationConfig(
        total_time_s=1.0e-3,
        sampling_rate_Hz=10_000.0,
        mean_flow_velocity_m_s=2.0e-4,
        rho=5.0,
        reference_model="constant",
        reference_spatial_mode="uniform",
    )
    reference = compute_reference_field(channel, optical, cfg)
    trajectory = {
        "time_s": np.arange(cfg.n_samples) * cfg.dt_s,
        "x_m": np.zeros(cfg.n_samples),
        "z_m": np.zeros(cfg.n_samples),
    }

    trace = compute_reference_field_trace(trajectory, reference, channel, optical, cfg)

    assert trace["A_ref_trace"].shape == trajectory["time_s"].shape
    assert trace["phi_ref_trace_rad"].shape == trajectory["time_s"].shape
    np.testing.assert_allclose(trace["A_ref_trace"], 5.0)
    np.testing.assert_allclose(trace["reference_amplitude_scale"], 1.0)
    assert trace["reference_spatial_mode"] == "uniform"


def test_trapezoid_effective_aperture_reference_propagates_sidewall_geometry():
    channel = Channel(width_m=500e-9, depth_m=900e-9)
    optical = OpticalSystem(
        wavelength_m=404e-9,
        peak_irradiance_W_m2=1.0e8,
        beam_waist_x_m=1.0e-6,
        beam_waist_y_m=1.0e-6,
        beam_waist_z_m=1.0e-6,
    )
    rectangle_cfg = SimulationConfig(
        total_time_s=1.0e-3,
        sampling_rate_Hz=10_000.0,
        mean_flow_velocity_m_s=2.0e-4,
        rho=5.0,
        reference_model="trapezoid_effective_aperture_surrogate",
        reference_spatial_mode="cross_section_surrogate",
        channel_cross_section_model="ideal_rectangle",
    )
    trapezoid_cfg = SimulationConfig(
        total_time_s=1.0e-3,
        sampling_rate_Hz=10_000.0,
        mean_flow_velocity_m_s=2.0e-4,
        rho=5.0,
        reference_model="trapezoid_effective_aperture_surrogate",
        reference_spatial_mode="cross_section_surrogate",
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=5.0,
    )

    rectangle = compute_reference_field(channel, optical, rectangle_cfg)
    trapezoid = compute_reference_field(channel, optical, trapezoid_cfg)

    assert rectangle["trapezoid_effective_aperture_factor"] == pytest.approx(1.0)
    assert rectangle["geometry_not_propagated_to_reference_field"] is False
    assert rectangle["not_optical_solver_output"] is True

    assert trapezoid["trapezoid_effective_aperture_factor"] < 1.0
    assert trapezoid["A_ref"] < rectangle["A_ref"]
    assert trapezoid["reference_geometry_propagation_status"] == (
        "trapezoid_geometry_propagated_to_effective_aperture_reference_surrogate"
    )
    assert trapezoid["geometry_not_propagated_to_reference_field"] is False
    assert trapezoid["reference_uses_rectangular_width_depth_surrogate"] is False
    assert trapezoid["not_optical_solver_output"] is True
    assert trapezoid["reference_solver_status"] == (
        "trapezoid_effective_aperture_surrogate_active"
    )
