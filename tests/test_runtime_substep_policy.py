from __future__ import annotations

import math

import pytest

from nodi_simulator.data_objects import Channel, SimulationConfig
from nodi_simulator.cross_section_geometry import TrapezoidCrossSection
from nodi_simulator.runtime_substep_policy import (
    build_trapezoid_runtime_substep_decision,
    estimate_trapezoid_surface_gap_quantile_m,
    required_substeps_for_brownian_surface_gap,
)
from nodi_simulator.trajectory import simulate_particle_trajectory


def _cfg(*, model: str = "trapezoid_tapered_sidewalls", taper_deg: float = 0.0) -> SimulationConfig:
    return SimulationConfig(
        total_time_s=1.0e-3,
        sampling_rate_Hz=4.0e4,
        mean_flow_velocity_m_s=1.0e-3,
        channel_cross_section_model=model,
        sidewall_taper_angle_deg=taper_deg,
        include_diffusion=True,
        diffusion_coefficient_m2_s=4.0e-12,
        reflecting_boundary=True,
        flow_profile_model="plug",
        diffusion_hindrance_model="none",
    )


def test_required_substeps_matches_gate_candidate_formula() -> None:
    required, required_dt, projected, observed = required_substeps_for_brownian_surface_gap(
        diffusion_coefficient_m2_s=4.0e-12,
        dt_s=2.5e-5,
        surface_gap_m=0.61687242e-9,
        trigger_threshold=1.0,
    )

    assert required == 526
    assert required_dt == pytest.approx(4.752851711e-8, rel=1e-9)
    assert projected == pytest.approx(0.9996012076, rel=1e-9)
    assert observed == pytest.approx(22.925543703, rel=1e-9)


def test_rectangle_path_is_not_substep_guarded() -> None:
    decision = build_trapezoid_runtime_substep_decision(
        channel=Channel(width_m=500e-9, depth_m=900e-9),
        sim_cfg=_cfg(model="ideal_rectangle"),
        particle_radius_m=20e-9,
    )

    assert decision.runtime_policy_status == "not_applicable_rectangle_path"
    assert decision.runtime_allowed is True
    assert decision.execution_packet_required is False
    assert decision.sidewall_prs_eas_numeric_allowed is False


def test_low_cost_substep_guard_allows_runtime_only_with_execution_packet() -> None:
    decision = build_trapezoid_runtime_substep_decision(
        channel=Channel(width_m=500e-9, depth_m=900e-9),
        sim_cfg=_cfg(taper_deg=0.0),
        particle_radius_m=20e-9,
        surface_gap_quantile_m=7.438709749e-9,
    )

    assert decision.required_substeps_to_meet_threshold == 4
    assert decision.runtime_policy_class == "low_substep_cost_runtime_guard"
    assert decision.runtime_allowed is True
    assert decision.execution_packet_required is True
    assert decision.sidewall_prs_eas_numeric_allowed is False


def test_prohibitive_substep_cost_blocks_runtime_without_waiver() -> None:
    decision = build_trapezoid_runtime_substep_decision(
        channel=Channel(width_m=800e-9, depth_m=900e-9),
        sim_cfg=_cfg(taper_deg=20.0),
        particle_radius_m=150e-9,
        surface_gap_quantile_m=0.61687242e-9,
    )

    assert decision.required_substeps_to_meet_threshold == 526
    assert decision.runtime_policy_status == "blocked_prohibitive_substep_cost"
    assert decision.runtime_policy_class == "prohibitive_substep_cost_runtime_blocked"
    assert decision.runtime_allowed is False
    assert decision.execution_packet_required is True


def test_manual_runtime_waiver_records_path_but_still_requires_execution_packet() -> None:
    decision = build_trapezoid_runtime_substep_decision(
        channel=Channel(width_m=800e-9, depth_m=900e-9),
        sim_cfg=_cfg(taper_deg=20.0),
        particle_radius_m=150e-9,
        surface_gap_quantile_m=0.61687242e-9,
        manual_runtime_cost_waiver=True,
    )

    assert decision.required_substeps_to_meet_threshold == 526
    assert decision.runtime_policy_status == (
        "manual_waiver_recorded_execution_packet_required"
    )
    assert decision.runtime_allowed is False
    assert decision.execution_packet_required is True


def test_surface_gap_quantile_estimator_returns_positive_gap_for_open_support() -> None:
    decision = build_trapezoid_runtime_substep_decision(
        channel=Channel(width_m=800e-9, depth_m=900e-9),
        sim_cfg=_cfg(taper_deg=5.0),
        particle_radius_m=50e-9,
    )

    assert math.isfinite(decision.surface_gap_quantile_m)
    assert decision.surface_gap_quantile_m > 0.0


def test_surface_gap_quantile_estimator_rejects_bad_quantile() -> None:
    geometry = TrapezoidCrossSection(
        top_width_m=800e-9,
        depth_m=900e-9,
        sidewall_taper_angle_deg=5.0,
    )
    with pytest.raises(ValueError, match="quantile"):
        estimate_trapezoid_surface_gap_quantile_m(
            geometry,
            particle_radius_m=50e-9,
            quantile=1.0,
        )


def test_low_cost_guarded_trapezoid_trajectory_smoke_stays_inside_support() -> None:
    from nodi_simulator.data_objects import OpticalSystem

    channel = Channel(width_m=500e-9, depth_m=900e-9)
    cfg = _cfg(taper_deg=0.0)
    radius_m = 20e-9
    decision = build_trapezoid_runtime_substep_decision(
        channel=channel,
        sim_cfg=cfg,
        particle_radius_m=radius_m,
        surface_gap_quantile_m=7.438709749e-9,
    )

    assert decision.runtime_allowed is True
    assert decision.execution_packet_required is True

    optical = OpticalSystem(
        wavelength_m=660e-9,
        peak_irradiance_W_m2=1.0e8,
        beam_waist_x_m=1.0e-6,
        beam_waist_y_m=1.0e-6,
        beam_waist_z_m=1.0e-6,
    )
    trajectory = simulate_particle_trajectory(
        channel,
        optical,
        cfg,
        initial_x_m=0.0,
        initial_z_m=0.0,
        particle_radius_m=radius_m,
        diffusion_coefficient=4.0e-12,
    )
    geometry = TrapezoidCrossSection(
        top_width_m=channel.width_m,
        depth_m=channel.depth_m,
        sidewall_taper_angle_deg=cfg.sidewall_taper_angle_deg,
    )

    assert all(
        geometry.contains_particle_center(float(x), float(z) + channel.depth_m / 2.0, radius_m)
        for x, z in zip(trajectory["x_m"], trajectory["z_m"], strict=True)
    )
