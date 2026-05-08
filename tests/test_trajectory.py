from __future__ import annotations

import numpy as np

from nodi_simulator.data_objects import Channel, OpticalSystem, SimulationConfig
from nodi_simulator.trajectory import (
    build_trajectory_context,
    simulate_particle_trajectory,
    simulate_particle_trajectory_block,
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


def _config() -> SimulationConfig:
    return SimulationConfig(
        total_time_s=1.0e-3,
        sampling_rate_Hz=10_000.0,
        mean_flow_velocity_m_s=2.0e-4,
        include_diffusion=False,
        flow_profile_model="plug",
    )


def test_pure_advection_trajectory_keeps_xz_fixed_and_advects_y_linearly():
    channel = _channel()
    optical = _optical()
    cfg = _config()

    trajectory = simulate_particle_trajectory(
        channel,
        optical,
        cfg,
        initial_x_m=20e-9,
        initial_z_m=-30e-9,
    )

    assert trajectory["time_s"].shape == (cfg.n_samples,)
    np.testing.assert_allclose(trajectory["x_m"], 20e-9)
    np.testing.assert_allclose(trajectory["z_m"], -30e-9)
    np.testing.assert_allclose(np.diff(trajectory["y_m"]), cfg.mean_flow_velocity_m_s * cfg.dt_s)
    np.testing.assert_allclose(trajectory["v_y_m_s"], cfg.mean_flow_velocity_m_s)


def test_block_trajectory_matches_scalar_pure_advection_for_same_initial_positions():
    channel = _channel()
    optical = _optical()
    cfg = _config()
    context = build_trajectory_context(channel, cfg)
    initial_x = np.array([0.0, 40e-9])
    initial_z = np.array([0.0, -50e-9])

    block = simulate_particle_trajectory_block(
        channel,
        optical,
        cfg,
        initial_x_m=initial_x,
        initial_z_m=initial_z,
        trajectory_context=context,
    )

    for idx, (x0, z0) in enumerate(zip(initial_x, initial_z, strict=True)):
        scalar = simulate_particle_trajectory(
            channel,
            optical,
            cfg,
            initial_x_m=float(x0),
            initial_z_m=float(z0),
            trajectory_context=context,
        )
        np.testing.assert_allclose(block["x_m"][idx], scalar["x_m"])
        np.testing.assert_allclose(block["y_m"][idx], scalar["y_m"])
        np.testing.assert_allclose(block["z_m"][idx], scalar["z_m"])
        np.testing.assert_allclose(block["v_y_m_s"][idx], scalar["v_y_m_s"])
