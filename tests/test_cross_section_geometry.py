from __future__ import annotations

from dataclasses import replace
import math

import numpy as np
import pytest

from nodi_simulator.channel_geometry_model import build_channel_geometry_diagnostics
from nodi_simulator.cross_section_geometry import (
    CENTER_ACCESSIBLE_SUPPORT_MODEL,
    TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION,
    TrapezoidCrossSection,
    comsol_sidewall_deg_to_nodi_taper_deg,
    nodi_taper_deg_to_comsol_sidewall_deg,
)
from nodi_simulator.data_objects import (
    BASELINE_OPTICAL,
    DEFAULT_SIM_CFG,
    WATER,
    Channel,
    Particle,
)
from nodi_simulator.electrokinetic_transport import (
    build_electrokinetic_transport_diagnostics,
)
from nodi_simulator.fluidic_resistance import compute_fluidic_practicality_penalty
from nodi_simulator.parameter_sweep import (
    _build_observation_signature,
    _sample_initial_positions_block,
)
from nodi_simulator.reference_field import compute_reference_field
from nodi_simulator.trajectory import (
    axial_transport_velocity_m_s,
    build_trajectory_context,
    build_trajectory_geometry_diagnostics,
    hindered_diffusion_factors,
    simulate_particle_trajectory,
    simulate_particle_trajectory_block,
)
from nodi_simulator.utils import sample_initial_position


def test_comsol_85_deg_converts_to_nodi_taper_5_deg() -> None:
    assert comsol_sidewall_deg_to_nodi_taper_deg(85.0) == pytest.approx(5.0)
    assert nodi_taper_deg_to_comsol_sidewall_deg(5.0) == pytest.approx(85.0)


def test_trapezoid_formula_examples_preserve_unclipped_bottom_width() -> None:
    geom_85 = TrapezoidCrossSection(
        top_width_m=500.0e-9,
        depth_m=900.0e-9,
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
    )
    geom_70 = TrapezoidCrossSection(
        top_width_m=500.0e-9,
        depth_m=600.0e-9,
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(70.0),
    )

    assert geom_85.bottom_width_unclipped_m * 1.0e9 == pytest.approx(342.52, abs=0.02)
    assert geom_70.bottom_width_unclipped_m * 1.0e9 == pytest.approx(63.24, abs=0.02)
    assert geom_85.bottom_width_runtime_clipped_m == pytest.approx(
        geom_85.bottom_width_unclipped_m
    )
    assert geom_70.closure_status == "near_closed"


def test_negative_bottom_width_is_preserved_in_descriptor_space() -> None:
    geom = TrapezoidCrossSection(
        top_width_m=500.0e-9,
        depth_m=700.0e-9,
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(70.0),
    )

    assert geom.bottom_width_unclipped_m < 0.0
    assert geom.bottom_width_runtime_clipped_m == 0.0
    assert geom.closure_status == "geometry_closed"


def test_particle_center_support_uses_wall_normal_sidewall_offset() -> None:
    geom = TrapezoidCrossSection(
        top_width_m=500.0e-9,
        depth_m=900.0e-9,
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
    )
    radius_m = 110.0e-9
    u_m = 200.0e-9
    local_half_width_m = geom.half_width_at_depth_m(u_m)
    x_limit_m = local_half_width_m - radius_m * math.sqrt(1.0 + geom.k_taper**2)

    assert geom.contains_particle_center(x_limit_m - 1.0e-12, u_m, radius_m)
    assert not geom.contains_particle_center(x_limit_m + 1.0e-10, u_m, radius_m)


def test_center_accessible_width_blocks_too_deep_tail_particle_slice() -> None:
    geom = TrapezoidCrossSection(
        top_width_m=500.0e-9,
        depth_m=900.0e-9,
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(70.0),
    )

    assert geom.center_accessible_width_at_depth_m(600.0e-9, 110.0e-9) == 0.0


def test_project_particle_center_into_trapezoid_support() -> None:
    geom = TrapezoidCrossSection(
        top_width_m=500.0e-9,
        depth_m=900.0e-9,
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
    )
    radius_m = 110.0e-9

    x_m, u_m = geom.project_particle_center_into_support(
        x_m=400.0e-9,
        u_m=950.0e-9,
        particle_radius_m=radius_m,
    )

    assert geom.contains_particle_center(x_m, u_m, radius_m)
    u_bounds = geom.center_accessible_u_bounds_m(radius_m)
    assert u_bounds is not None
    assert u_m == pytest.approx(u_bounds[1])
    x_left_m, x_right_m = geom.center_accessible_x_bounds_at_depth_m(u_m, radius_m)
    assert x_m == pytest.approx(x_right_m)
    assert x_left_m <= x_m <= x_right_m


def test_project_particle_center_raises_when_no_support_exists() -> None:
    geom = TrapezoidCrossSection(
        top_width_m=120.0e-9,
        depth_m=400.0e-9,
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
    )

    with pytest.raises(ValueError, match="no center-accessible support"):
        geom.project_particle_center_into_support(0.0, 200.0e-9, 110.0e-9)


def test_channel_diagnostics_emit_unclipped_and_runtime_clipped_bottom_widths() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(70.0),
    )
    diagnostics = build_channel_geometry_diagnostics(
        Particle("ev_220nm_tail", radius_m=110.0e-9, n_real=1.37),
        Channel(width_m=500.0e-9, depth_m=700.0e-9),
        BASELINE_OPTICAL,
        cfg,
    )

    assert diagnostics["trapezoid_bottom_width_unclipped_m"] < 0.0
    assert diagnostics["trapezoid_bottom_width_runtime_clipped_m"] == 0.0
    assert diagnostics["trapezoid_bottom_width_m"] == 0.0
    assert diagnostics["trapezoid_depth_m"] == pytest.approx(700.0e-9)
    assert diagnostics["trapezoid_closure_status"] == "geometry_closed"
    assert diagnostics["trapezoid_closure_policy"] == "preserve_unclipped_descriptor"
    assert diagnostics["trapezoid_runtime_guard_status"] == "validation_guard"
    assert diagnostics["center_accessible_support_model"] == CENTER_ACCESSIBLE_SUPPORT_MODEL
    assert (
        diagnostics["cross_section_geometry_version"]
        == TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION
    )
    assert diagnostics["effective_accessible_area_m2"] == diagnostics[
        "trapezoid_center_accessible_area_m2"
    ]
    assert diagnostics["effective_accessible_area_m2"] > 0.0


def test_geometry_closed_trapezoid_cannot_enter_runtime_sampler() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(70.0),
        initial_position_distribution_mode="uniform_accessible_area",
    )

    with pytest.raises(ValueError, match="geometry_closed"):
        sample_initial_position(
            Channel(width_m=500.0e-9, depth_m=700.0e-9),
            np.random.default_rng(123),
            110.0e-9,
            sim_cfg=cfg,
        )


def test_geometry_closed_trapezoid_cannot_enter_trajectory_context() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(70.0),
        flow_profile_model="plug",
        diffusion_hindrance_model="none",
        include_diffusion=False,
    )

    with pytest.raises(ValueError, match="geometry_closed"):
        build_trajectory_context(
            Channel(width_m=500.0e-9, depth_m=700.0e-9),
            cfg,
            particle_radius_m=110.0e-9,
        )


def test_geometry_closed_trapezoid_cannot_enter_direct_axial_transport() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(70.0),
        flow_profile_model="plug",
        diffusion_hindrance_model="none",
        include_diffusion=False,
    )

    with pytest.raises(ValueError, match="geometry_closed"):
        axial_transport_velocity_m_s(
            0.0,
            0.0,
            Channel(width_m=500.0e-9, depth_m=700.0e-9),
            cfg,
            particle_radius_m=110.0e-9,
        )


def test_trapezoid_uniform_sampler_stays_in_particle_center_support() -> None:
    channel = Channel(width_m=500.0e-9, depth_m=900.0e-9)
    radius_m = 110.0e-9
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        initial_position_distribution_mode="uniform_accessible_area",
    )
    geom = TrapezoidCrossSection(
        top_width_m=channel.width_m,
        depth_m=channel.depth_m,
        sidewall_taper_angle_deg=cfg.sidewall_taper_angle_deg,
    )

    unit_samples = [
        (0.0, 0.0, 0.2),
        (0.25, 0.3, 0.4),
        (0.5, 0.5, 0.6),
        (0.75, 0.8, 0.8),
        (0.999, 0.999, 0.1),
    ]
    for unit_sample in unit_samples:
        x0, z0, diag = sample_initial_position(
            channel,
            np.random.default_rng(123),
            radius_m,
            sim_cfg=cfg,
            unit_position_sample=unit_sample,
        )
        u0 = z0 + 0.5 * channel.depth_m
        assert geom.contains_particle_center(x0, u0, radius_m, tolerance_m=1.0e-18)
        assert diag["initial_position_sampler_geometry_model"] == (
            "trapezoid_tapered_sidewalls"
        )
        assert diag["initial_position_sampler_support_model"] == (
            CENTER_ACCESSIBLE_SUPPORT_MODEL
        )
        assert diag["geometry_not_propagated_to_sampler"] is False
        assert diag["cross_section_event_bias_status"] == (
            "uniform_over_trapezoid_center_accessible_area"
        )


def test_trapezoid_sampler_rejects_flux_weighted_without_flow_model() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        initial_position_distribution_mode="flux_weighted",
    )

    with pytest.raises(ValueError, match="flux_weighted initial-position sampling"):
        sample_initial_position(
            Channel(width_m=500.0e-9, depth_m=900.0e-9),
            np.random.default_rng(123),
            110.0e-9,
            sim_cfg=cfg,
        )


def test_block_trapezoid_sampler_uses_scalar_oracle_path() -> None:
    channel = Channel(width_m=500.0e-9, depth_m=900.0e-9)
    radius_m = 110.0e-9
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        initial_position_distribution_mode="uniform_accessible_area",
    )
    unit_samples = np.array(
        [
            [0.1, 0.2, 0.3],
            [0.3, 0.4, 0.5],
            [0.5, 0.6, 0.7],
            [0.7, 0.8, 0.9],
        ],
        dtype=float,
    )
    geom = TrapezoidCrossSection(
        top_width_m=channel.width_m,
        depth_m=channel.depth_m,
        sidewall_taper_angle_deg=cfg.sidewall_taper_angle_deg,
    )

    x_vals, z_vals, diagnostics = _sample_initial_positions_block(
        channel,
        np.random.default_rng(999),
        radius_m,
        cfg,
        unit_samples,
        0,
        len(unit_samples),
    )

    assert len(diagnostics) == len(unit_samples)
    for x0, z0, diag in zip(x_vals, z_vals, diagnostics):
        u0 = float(z0 + 0.5 * channel.depth_m)
        assert geom.contains_particle_center(float(x0), u0, radius_m)
        assert diag["initial_position_sampler_geometry_model"] == (
            "trapezoid_tapered_sidewalls"
        )
        assert diag["initial_position_sampler_support_model"] == (
            CENTER_ACCESSIBLE_SUPPORT_MODEL
        )


def test_trapezoid_pure_advection_accepts_oracle_sampled_initial_position() -> None:
    channel = Channel(width_m=500.0e-9, depth_m=900.0e-9)
    radius_m = 110.0e-9
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        flow_profile_model="plug",
        diffusion_hindrance_model="none",
        include_diffusion=False,
        initial_position_distribution_mode="uniform_accessible_area",
    )
    x0, z0, _ = sample_initial_position(
        channel,
        np.random.default_rng(123),
        radius_m,
        sim_cfg=cfg,
        unit_position_sample=(0.75, 0.5, 0.25),
    )

    trajectory = simulate_particle_trajectory(
        channel,
        BASELINE_OPTICAL,
        cfg,
        x0,
        z0,
        particle_radius_m=radius_m,
    )

    np.testing.assert_allclose(trajectory["x_m"], x0)
    np.testing.assert_allclose(trajectory["z_m"], z0)
    assert np.all(trajectory["v_y_m_s"] == pytest.approx(cfg.mean_flow_velocity_m_s))


def test_trapezoid_trajectory_rejects_rectangular_flow_profiles() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        flow_profile_model="rect_series",
        diffusion_hindrance_model="none",
        include_diffusion=False,
    )

    with pytest.raises(ValueError, match="rectangular and not sidewall-aware"):
        build_trajectory_context(
            Channel(width_m=500.0e-9, depth_m=900.0e-9),
            cfg,
            particle_radius_m=110.0e-9,
        )


def test_trapezoid_hindered_diffusion_rejects_rectangular_wall_distance() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        flow_profile_model="plug",
        diffusion_hindrance_model="near_wall_surrogate",
        include_diffusion=False,
    )

    with pytest.raises(ValueError, match="rectangular wall-distance"):
        hindered_diffusion_factors(
            0.0,
            0.0,
            Channel(width_m=500.0e-9, depth_m=900.0e-9),
            110.0e-9,
            cfg,
        )


def test_trapezoid_trajectory_rejects_unbounded_diffusive_boundary() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        flow_profile_model="plug",
        diffusion_hindrance_model="none",
        include_diffusion=True,
        reflecting_boundary=False,
    )

    with pytest.raises(ValueError, match="reflecting_boundary=True"):
        build_trajectory_context(
            Channel(width_m=500.0e-9, depth_m=900.0e-9),
            cfg,
            particle_radius_m=110.0e-9,
        )


def test_trapezoid_diffusive_runtime_rejects_rectangular_flow_profile() -> None:
    channel = Channel(width_m=500.0e-9, depth_m=900.0e-9)
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        flow_profile_model="rect_series",
        diffusion_hindrance_model="none",
        include_diffusion=True,
        reflecting_boundary=True,
    )

    with pytest.raises(ValueError, match="rectangular and not sidewall-aware"):
        build_trajectory_context(channel, cfg, particle_radius_m=110.0e-9)

    with pytest.raises(ValueError, match="rectangular and not sidewall-aware"):
        simulate_particle_trajectory(
            channel,
            BASELINE_OPTICAL,
            cfg,
            initial_x_m=0.0,
            initial_z_m=0.0,
            particle_radius_m=110.0e-9,
            diffusion_coefficient=8.0e-12,
        )


def test_trapezoid_diffusive_block_rejects_rectangular_near_wall_model() -> None:
    channel = Channel(width_m=500.0e-9, depth_m=900.0e-9)
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        flow_profile_model="plug",
        diffusion_hindrance_model="near_wall_surrogate",
        include_diffusion=True,
        reflecting_boundary=True,
    )

    with pytest.raises(ValueError, match="rectangular wall-distance"):
        build_trajectory_context(channel, cfg, particle_radius_m=110.0e-9)

    with pytest.raises(ValueError, match="rectangular wall-distance"):
        simulate_particle_trajectory_block(
            channel,
            BASELINE_OPTICAL,
            cfg,
            initial_x_m=np.asarray([0.0]),
            initial_z_m=np.asarray([0.0]),
            particle_radius_m=110.0e-9,
            diffusion_coefficient=8.0e-12,
        )


def test_trapezoid_projected_diffusive_trajectory_stays_in_support() -> None:
    channel = Channel(width_m=500.0e-9, depth_m=900.0e-9)
    radius_m = 110.0e-9
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        flow_profile_model="plug",
        diffusion_hindrance_model="none",
        include_diffusion=True,
        reflecting_boundary=True,
        total_time_s=1.0e-3,
        sampling_rate_Hz=1.0e4,
    )
    x0, z0, _ = sample_initial_position(
        channel,
        np.random.default_rng(123),
        radius_m,
        sim_cfg=cfg,
        unit_position_sample=(0.85, 0.8, 0.5),
    )

    trajectory = simulate_particle_trajectory(
        channel,
        BASELINE_OPTICAL,
        cfg,
        x0,
        z0,
        particle_radius_m=radius_m,
        diffusion_coefficient=8.0e-12,
        rng=np.random.default_rng(456),
    )

    geom = TrapezoidCrossSection(
        top_width_m=channel.width_m,
        depth_m=channel.depth_m,
        sidewall_taper_angle_deg=cfg.sidewall_taper_angle_deg,
    )
    for x_m, z_m in zip(trajectory["x_m"], trajectory["z_m"]):
        assert geom.contains_particle_center(
            float(x_m),
            float(z_m) + 0.5 * channel.depth_m,
            radius_m,
            tolerance_m=1.0e-18,
        )
    assert np.any(np.diff(trajectory["x_m"]) != 0.0)
    np.testing.assert_allclose(trajectory["v_y_m_s"], cfg.mean_flow_velocity_m_s)


def test_trapezoid_projected_diffusive_block_stays_in_support() -> None:
    channel = Channel(width_m=500.0e-9, depth_m=900.0e-9)
    radius_m = 110.0e-9
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        flow_profile_model="plug",
        diffusion_hindrance_model="none",
        include_diffusion=True,
        reflecting_boundary=True,
        total_time_s=1.0e-3,
        sampling_rate_Hz=1.0e4,
    )
    initial_positions = [
        sample_initial_position(
            channel,
            np.random.default_rng(123),
            radius_m,
            sim_cfg=cfg,
            unit_position_sample=unit_sample,
        )
        for unit_sample in [(0.2, 0.25, 0.5), (0.9, 0.9, 0.5)]
    ]
    x0 = np.asarray([position[0] for position in initial_positions])
    z0 = np.asarray([position[1] for position in initial_positions])
    diffusion_draws = np.full((2, 2 * (cfg.n_samples - 1)), 18.0, dtype=float)

    trajectory = simulate_particle_trajectory_block(
        channel,
        BASELINE_OPTICAL,
        cfg,
        x0,
        z0,
        particle_radius_m=radius_m,
        diffusion_coefficient=8.0e-12,
        diffusion_draws=diffusion_draws,
        export_velocity_trace=True,
    )

    geom = TrapezoidCrossSection(
        top_width_m=channel.width_m,
        depth_m=channel.depth_m,
        sidewall_taper_angle_deg=cfg.sidewall_taper_angle_deg,
    )
    for event_index in range(x0.size):
        for x_m, z_m in zip(
            trajectory["x_m"][event_index],
            trajectory["z_m"][event_index],
        ):
            assert geom.contains_particle_center(
                float(x_m),
                float(z_m) + 0.5 * channel.depth_m,
                radius_m,
                tolerance_m=1.0e-18,
            )
    assert trajectory["x_m"].shape == (2, cfg.n_samples)
    assert trajectory["z_m"].shape == (2, cfg.n_samples)
    np.testing.assert_allclose(trajectory["v_y_m_s"], cfg.mean_flow_velocity_m_s)


def test_trapezoid_trajectory_rejects_initial_point_outside_oracle_support() -> None:
    channel = Channel(width_m=500.0e-9, depth_m=900.0e-9)
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        flow_profile_model="plug",
        diffusion_hindrance_model="none",
        include_diffusion=False,
    )

    with pytest.raises(ValueError, match="trapezoid particle-center support"):
        simulate_particle_trajectory(
            channel,
            BASELINE_OPTICAL,
            cfg,
            initial_x_m=120.0e-9,
            initial_z_m=310.0e-9,
            particle_radius_m=110.0e-9,
        )


def test_trapezoid_axial_transport_rejects_rectangular_flow_direct_call() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        flow_profile_model="parabolic_rect",
        diffusion_hindrance_model="none",
        include_diffusion=False,
    )

    with pytest.raises(ValueError, match="rectangular and not sidewall-aware"):
        axial_transport_velocity_m_s(
            0.0,
            0.0,
            Channel(width_m=500.0e-9, depth_m=900.0e-9),
            cfg,
            particle_radius_m=110.0e-9,
        )


def test_trapezoid_trajectory_diagnostics_mark_pure_advection_boundary() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        flow_profile_model="plug",
        diffusion_hindrance_model="none",
        include_diffusion=False,
    )

    diagnostics = build_trajectory_geometry_diagnostics(cfg)

    assert diagnostics["trajectory_geometry_diagnostics_scope"] == (
        "config_only_not_closure_or_passability_verdict"
    )
    assert diagnostics["trajectory_closure_authority"] == (
        "channel_geometry_runtime_guards_and_prs_eas_validators"
    )
    assert diagnostics["trajectory_boundary_model"] == "not_applicable_pure_advection"
    assert diagnostics["wall_distance_model"] == (
        "not_applicable_diffusion_hindrance_none"
    )
    assert diagnostics["flow_profile_geometry_model"] == (
        "plug_flow_geometry_independent_v1"
    )
    assert diagnostics["geometry_propagation_status"] == (
        "sidewall_sampler_and_pure_advection_propagated"
    )
    assert diagnostics["geometry_not_propagated_reasons"] == ()
    assert diagnostics["sidewall_aware_runtime_status"] == (
        "partial_sidewall_runtime_no_diffusion_no_wall_metrics"
    )


def test_trapezoid_trajectory_diagnostics_mark_projection_boundary() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        flow_profile_model="plug",
        diffusion_hindrance_model="none",
        include_diffusion=True,
        reflecting_boundary=True,
    )

    diagnostics = build_trajectory_geometry_diagnostics(cfg)

    assert diagnostics["trajectory_boundary_model"] == (
        "trapezoid_center_support_projection_boundary_v1"
    )
    assert diagnostics["trajectory_boundary_claim_level"] == (
        "sidewall_projection_boundary_surrogate_not_specular_reflection"
    )
    assert diagnostics["geometry_propagation_status"] == (
        "sidewall_projection_boundary_surrogate_propagated"
    )
    assert diagnostics["geometry_not_propagated_reasons"] == ()
    assert diagnostics["sidewall_aware_runtime_status"] == (
        "partial_sidewall_runtime_projection_boundary_no_wall_metrics"
    )


def test_trapezoid_trajectory_diagnostics_mark_blocked_rectangular_leakage() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        flow_profile_model="rect_series",
        diffusion_hindrance_model="near_wall_surrogate",
        include_diffusion=True,
    )

    diagnostics = build_trajectory_geometry_diagnostics(cfg)

    assert diagnostics["geometry_propagation_status"] == (
        "blocked_rectangular_geometry_leakage"
    )
    assert diagnostics["geometry_not_propagated_to_flow_model"] is True
    assert diagnostics["geometry_not_propagated_to_near_wall_metrics"] is True
    assert diagnostics["trajectory_boundary_model"] == (
        "trapezoid_center_support_projection_boundary_v1"
    )
    assert diagnostics["geometry_not_propagated_to_trajectory_boundary"] is False
    assert set(diagnostics["geometry_not_propagated_reasons"]) == {
        "geometry_not_propagated_to_flow_model",
        "geometry_not_propagated_to_near_wall_metrics",
    }


def test_sidewall_observation_signature_records_geometry_propagation_fields() -> None:
    channel = Channel(width_m=500.0e-9, depth_m=900.0e-9)
    particle = Particle("ev_220nm_tail", radius_m=110.0e-9, n_real=1.37)
    cfg_85 = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        flow_profile_model="plug",
        diffusion_hindrance_model="none",
        include_diffusion=False,
    )
    cfg_83 = replace(
        cfg_85,
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(83.0),
    )
    channel_geometry_85 = build_channel_geometry_diagnostics(
        particle,
        channel,
        BASELINE_OPTICAL,
        cfg_85,
    )
    channel_geometry_83 = build_channel_geometry_diagnostics(
        particle,
        channel,
        BASELINE_OPTICAL,
        cfg_83,
    )
    deeper_channel = Channel(width_m=500.0e-9, depth_m=1200.0e-9)
    channel_geometry_85_deeper = build_channel_geometry_diagnostics(
        particle,
        deeper_channel,
        BASELINE_OPTICAL,
        cfg_85,
    )
    reference_85 = {
        **channel_geometry_85,
        "cross_section_geometry_version": TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION,
        "center_accessible_support_model": CENTER_ACCESSIBLE_SUPPORT_MODEL,
        "initial_position_sampler_geometry_model": "trapezoid_tapered_sidewalls",
        "sampler_geometry_model": "trapezoid_accessible_area_v1",
        "sidewall_angle_convention": "sidewall_angle_from_substrate_plane_90deg_vertical",
        "sidewall_deg_comsol": 85.0,
        "W_top_semantics": "comsol_descriptor",
        "runtime_top_aperture_nm": 500.0,
        "source_geometry_descriptor_sha": "a" * 64,
        "geometry_profile_sha256": "b" * 64,
        "geometry_profile_descriptor_version": "geometry_profile_descriptor_v2",
        "geometry_runtime_binding_version": "geometry_runtime_binding_manifest_v1",
        "reference_geometry_model": "rectangular_width_depth_reference_proxy_under_trapezoid",
        "reference_geometry_propagation_status": (
            "blocked_trapezoid_geometry_not_propagated_to_reference_field"
        ),
        "geometry_not_propagated_to_reference_field": True,
        "not_optical_solver_output": True,
        "optical_solver_trigger_is_result": False,
        **build_trajectory_geometry_diagnostics(cfg_85),
    }
    reference_83 = {
        **channel_geometry_83,
        "cross_section_geometry_version": TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION,
        "center_accessible_support_model": CENTER_ACCESSIBLE_SUPPORT_MODEL,
        **build_trajectory_geometry_diagnostics(cfg_83),
    }
    cfg_85_diffusive = replace(
        cfg_85,
        include_diffusion=True,
        reflecting_boundary=True,
    )
    reference_85_diffusive = {
        "cross_section_geometry_version": TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION,
        "center_accessible_support_model": CENTER_ACCESSIBLE_SUPPORT_MODEL,
        **build_trajectory_geometry_diagnostics(cfg_85_diffusive),
    }
    reference_85_deeper = {
        **channel_geometry_85_deeper,
        "cross_section_geometry_version": TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION,
        "center_accessible_support_model": CENTER_ACCESSIBLE_SUPPORT_MODEL,
        **build_trajectory_geometry_diagnostics(cfg_85),
    }

    signature_85 = _build_observation_signature(
        "operator=test",
        reference_85,
        cfg_85,
        particle_radius_m=110.0e-9,
    )
    signature_83 = _build_observation_signature(
        "operator=test",
        reference_83,
        cfg_83,
        particle_radius_m=110.0e-9,
    )
    signature_85_larger_particle = _build_observation_signature(
        "operator=test",
        reference_85,
        cfg_85,
        particle_radius_m=150.0e-9,
    )
    signature_85_diffusive = _build_observation_signature(
        "operator=test",
        reference_85_diffusive,
        cfg_85_diffusive,
        particle_radius_m=110.0e-9,
    )
    signature_85_deeper = _build_observation_signature(
        "operator=test",
        reference_85_deeper,
        cfg_85,
        particle_radius_m=110.0e-9,
    )

    assert "channel_cross_section_model=trapezoid_tapered_sidewalls" in signature_85
    assert "sidewall_taper_angle_deg=5.000000000e+00" in signature_85
    assert (
        "sidewall_angle_convention="
        "sidewall_angle_from_substrate_plane_90deg_vertical"
    ) in signature_85
    assert "sidewall_deg_comsol=85.0" in signature_85
    assert "W_top_semantics=comsol_descriptor" in signature_85
    assert "runtime_top_aperture_nm=500.0" in signature_85
    assert f"source_geometry_descriptor_sha={'a' * 64}" in signature_85
    assert f"geometry_profile_sha256={'b' * 64}" in signature_85
    assert (
        "geometry_profile_descriptor_version=geometry_profile_descriptor_v2"
        in signature_85
    )
    assert (
        "geometry_runtime_binding_version=geometry_runtime_binding_manifest_v1"
        in signature_85
    )
    assert "particle_radius_m=1.1e-07" in signature_85
    assert f"center_accessible_support_model={CENTER_ACCESSIBLE_SUPPORT_MODEL}" in (
        signature_85
    )
    assert (
        "initial_position_sampler_geometry_model=trapezoid_tapered_sidewalls"
        in signature_85
    )
    assert "sampler_geometry_model=trapezoid_accessible_area_v1" in signature_85
    assert (
        f"cross_section_geometry_version={TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION}"
        in signature_85
    )
    assert "trajectory_boundary_model=not_applicable_pure_advection" in signature_85
    assert "trajectory_boundary_claim_level=no_diffusive_boundary_claim" in signature_85
    assert "trapezoid_top_width_m=5e-07" in signature_85
    assert "trapezoid_depth_m=9e-07" in signature_85
    assert "trapezoid_bottom_width_unclipped_m=" in signature_85
    assert "trapezoid_bottom_width_runtime_clipped_m=" in signature_85
    assert "trapezoid_center_accessible_area_m2=" in signature_85
    assert "trapezoid_center_accessible_area_fraction=" in signature_85
    assert (
        "wall_distance_model=not_applicable_diffusion_hindrance_none"
        in signature_85
    )
    assert "wall_distance_claim_level=not_used" in signature_85
    assert (
        "flow_profile_geometry_claim_level="
        "geometry_independent_uniform_flow_surrogate"
        in signature_85
    )
    assert (
        "trajectory_boundary_claim_level="
        "sidewall_projection_boundary_surrogate_not_specular_reflection"
        in signature_85_diffusive
    )
    assert (
        "geometry_propagation_status="
        "sidewall_sampler_and_pure_advection_propagated"
    ) in signature_85
    assert (
        "reference_geometry_model="
        "rectangular_width_depth_reference_proxy_under_trapezoid"
    ) in signature_85
    assert (
        "reference_geometry_propagation_status="
        "blocked_trapezoid_geometry_not_propagated_to_reference_field"
    ) in signature_85
    assert "geometry_not_propagated_to_reference_field=True" in signature_85
    assert "not_optical_solver_output=True" in signature_85
    assert "optical_solver_trigger_is_result=False" in signature_85
    assert signature_85 != signature_83
    assert signature_85 != signature_85_diffusive
    assert signature_85 != signature_85_deeper
    assert signature_85 != signature_85_larger_particle

    for mutated_reference in (
        {**reference_85, "W_top_semantics": "runtime_top_aperture"},
        {**reference_85, "runtime_top_aperture_nm": 480.0},
        {**reference_85, "source_geometry_descriptor_sha": "c" * 64},
        {**reference_85, "geometry_profile_sha256": "d" * 64},
        {**reference_85, "sampler_geometry_model": "rectangular_half_span_v1"},
    ):
        assert (
            _build_observation_signature(
                "operator=test",
                mutated_reference,
                cfg_85,
                particle_radius_m=110.0e-9,
            )
            != signature_85
        )


def test_observation_signature_separates_secondary_geometry_descriptors() -> None:
    base_cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
    )
    base_reference = {
        "reference_geometry_model": "rectangular_width_depth_reference_proxy_under_trapezoid",
        "reference_geometry_propagation_status": (
            "blocked_trapezoid_geometry_not_propagated_to_reference_field"
        ),
    }
    base_signature = _build_observation_signature(
        "operator=test",
        base_reference,
        base_cfg,
        particle_radius_m=110.0e-9,
    )

    assert "corner_radius_nm=0.000000000e+00" in base_signature
    assert "surface_roughness_rms_nm=0.000000000e+00" in base_signature
    assert "width_along_channel_cv=0.000000000e+00" in base_signature
    assert "depth_along_channel_cv=0.000000000e+00" in base_signature
    assert "measured_profile_path=none" in base_signature

    for mutated_cfg in (
        replace(base_cfg, corner_radius_nm=12.0),
        replace(base_cfg, surface_roughness_rms_nm=3.5),
        replace(base_cfg, width_along_channel_cv=0.04),
        replace(base_cfg, depth_along_channel_cv=0.03),
        replace(base_cfg, measured_profile_path="profiles/fibsem_sidewall.csv"),
    ):
        assert (
            _build_observation_signature(
                "operator=test",
                base_reference,
                mutated_cfg,
                particle_radius_m=110.0e-9,
            )
            != base_signature
        )


def test_trapezoid_boltzmann_electrokinetic_grid_is_blocked_not_rectangular() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        electrokinetic_model="boltzmann_wall_exclusion",
        ionic_strength_M=1.0e-4,
        zeta_potential_particle_mV=-35.0,
        zeta_potential_wall_mV=-45.0,
    )

    diagnostics = build_electrokinetic_transport_diagnostics(
        Channel(width_m=500.0e-9, depth_m=900.0e-9),
        cfg,
    )

    assert diagnostics["boltzmann_wall_exclusion_status"] == (
        "blocked_trapezoid_geometry_not_propagated"
    )
    assert diagnostics["geometry_not_propagated_to_electrokinetic_transport"] is True
    assert diagnostics["electrokinetic_transport_sensitivity_lane_active"] is False
    assert diagnostics["electrokinetic_diagnostic_gate_passed"] is False
    assert diagnostics["unweighted_mean_wall_distance_nm"] is None
    assert diagnostics["boltzmann_weighted_mean_wall_distance_nm"] is None
    assert diagnostics["surface_charge_transport_claim_level"] == (
        "blocked_trapezoid_geometry_not_propagated_to_electrokinetic_transport"
    )


def test_trapezoid_fluidic_resistance_is_marked_rectangular_proxy() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        flow_control_mode="fixed_pressure",
    )

    diagnostics = compute_fluidic_practicality_penalty(
        Particle("ev_220nm_tail", radius_m=110.0e-9, n_real=1.37),
        WATER,
        Channel(width_m=500.0e-9, depth_m=900.0e-9),
        cfg,
    )

    assert diagnostics["geometry_not_propagated_to_fluidic_resistance"] is True
    assert diagnostics["hydraulic_resistance_model"] == (
        "rectangular_hydraulic_resistance_proxy_under_trapezoid"
    )
    assert diagnostics["hydraulic_resistance_claim_level"] == (
        "proxy_not_trapezoid_poiseuille_not_accepted_for_formula_use"
    )
    assert diagnostics["fluidic_clogging_risk_band_claim_level"] == (
        "static_throat_clearance_proxy_not_clogging_rate"
    )
    assert diagnostics["not_clogging_rate"] is True
    assert diagnostics["not_time_to_clog"] is True
    assert diagnostics["fixed_pressure_diagnostic_status"] == (
        "proxy_only_rectangular_resistance_under_trapezoid"
    )


def test_trapezoid_reference_field_is_marked_rectangular_proxy() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
        reference_model="geometry_scaled",
        reference_spatial_mode="cross_section_surrogate",
    )

    reference = compute_reference_field(
        Channel(width_m=500.0e-9, depth_m=900.0e-9),
        BASELINE_OPTICAL,
        cfg,
        medium_refractive_index=1.33,
    )

    assert reference["reference_geometry_model"] == (
        "rectangular_width_depth_reference_proxy_under_trapezoid"
    )
    assert reference["reference_spatial_geometry_model"] == (
        "rectangular_xz_norm_cross_section_surrogate_under_trapezoid"
    )
    assert reference["reference_geometry_claim_level"] == (
        "proxy_not_sidewall_aware_not_optical_solver_output"
    )
    assert reference["reference_geometry_propagation_status"] == (
        "blocked_trapezoid_geometry_not_propagated_to_reference_field"
    )
    assert reference["reference_geometry_not_propagated_reasons"] == (
        "geometry_not_propagated_to_reference_field",
    )
    assert reference["geometry_not_propagated_to_reference_field"] is True
    assert reference["reference_uses_rectangular_width_depth_surrogate"] is True
    assert reference["not_optical_solver_output"] is True
    assert reference["optical_solver_trigger_is_result"] is False
