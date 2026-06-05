from __future__ import annotations

from dataclasses import replace
import math

import numpy as np
import pytest

from nodi_simulator.data_objects import BASELINE_OPTICAL, Channel, DEFAULT_SIM_CFG
from nodi_simulator.interferometric_trace import generate_interferometric_trace
from nodi_simulator.materials import get_n_complex
from nodi_simulator.mie_engine import (
    mie_angular_from_coefficients,
    mie_coefficients,
    mie_compute,
    mie_core_shell_coefficients,
    mie_efficiencies_from_coefficients,
)
from nodi_simulator.post_v2_audit import direction_cosine_jacobian
from nodi_simulator.pulse_analysis import estimate_threshold_stats_robust
from nodi_simulator.trajectory import simulate_particle_trajectory_block


def test_mie_positive_and_rayleigh_qsca_x4_trend():
    m_rel = complex(1.45 / 1.333, 0.0)
    qext_small, qsca_small = mie_compute(0.02, m_rel)
    qext_big, qsca_big = mie_compute(0.04, m_rel)

    assert qext_small >= 0.0
    assert qsca_small >= 0.0
    assert qext_big >= 0.0
    assert qsca_big >= 0.0
    assert qsca_big / qsca_small == pytest.approx(16.0, rel=0.04)


def test_mie_angular_integral_matches_qsca():
    x = 0.8
    m_rel = complex(1.45 / 1.333, 0.0)
    theta = np.linspace(1e-5, math.pi - 1e-5, 8001)
    a_n, b_n = mie_coefficients(x, m_rel)
    _, qsca = mie_efficiencies_from_coefficients(x, a_n, b_n)
    s1, s2 = mie_angular_from_coefficients(a_n, b_n, theta)
    integral = np.trapezoid((np.abs(s1) ** 2 + np.abs(s2) ** 2) * np.sin(theta), theta)

    assert integral / (x * x) == pytest.approx(qsca, rel=7e-4)


@pytest.mark.parametrize(
    ("diameter_nm", "wavelength_nm", "qext_expected", "qsca_expected"),
    [
        (20.0, 404.0, 0.729460576101, 0.006184736772),
        (40.0, 660.0, 0.092996052500, 0.029197494331),
        (60.0, 532.0, 4.826852066160, 0.943610428552),
    ],
)
def test_gold_mie_hardcoded_benchmarks(diameter_nm, wavelength_nm, qext_expected, qsca_expected):
    wavelength_m = wavelength_nm * 1e-9
    n_medium = 1.333
    m_rel = get_n_complex("gold", wavelength_m) / n_medium
    x = 2.0 * math.pi * n_medium * (diameter_nm * 0.5e-9) / wavelength_m

    qext, qsca = mie_compute(x, m_rel)

    assert qext == pytest.approx(qext_expected, rel=1e-9, abs=1e-12)
    assert qsca == pytest.approx(qsca_expected, rel=1e-9, abs=1e-12)


def test_core_shell_non_degenerate_benchmark_is_positive_and_distinct():
    a_shell, b_shell = mie_core_shell_coefficients(
        0.6,
        core_radius_ratio=0.62,
        m_shell_rel=complex(1.45 / 1.333, 0.0),
        m_core_rel=complex(1.36 / 1.333, 0.0),
    )
    qext_shell, qsca_shell = mie_efficiencies_from_coefficients(0.6, a_shell, b_shell)
    a_hom, b_hom = mie_coefficients(0.6, complex(1.45 / 1.333, 0.0))
    qext_hom, qsca_hom = mie_efficiencies_from_coefficients(0.6, a_hom, b_hom)

    assert qext_shell > 0.0
    assert qsca_shell > 0.0
    assert qext_shell != pytest.approx(qext_hom, rel=1e-3)
    assert qsca_shell != pytest.approx(qsca_hom, rel=1e-3)


def test_reference_zero_contrast_and_small_phase_limit_and_sign():
    theta = 1.0e-6
    exact = np.exp(1j * theta) - 1.0
    flipped = np.exp(-1j * theta) - 1.0

    assert np.exp(0j) - 1.0 == 0.0
    assert exact == pytest.approx(1j * theta, abs=1e-12)
    assert flipped.imag == pytest.approx(-exact.imag, rel=1e-12)
    assert flipped.real == pytest.approx(exact.real, rel=1e-12)


def test_detector_jacobian_exactly_once_guard():
    u = 0.4
    v = 0.2
    jacobian = direction_cosine_jacobian(u, v)

    assert jacobian == pytest.approx(1.0 / math.sqrt(1.0 - u * u - v * v))
    assert jacobian * jacobian != pytest.approx(jacobian)


def test_interference_cross_term_and_self_term_scaling():
    trajectory = {"time_s": np.array([0.0, 1.0])}
    reference = {"E_ref_complex": 2.0 + 0.0j, "interference_overlap_factor_complex": 1.0 + 0.0j}
    sim_cfg = replace(DEFAULT_SIM_CFG, background_subtraction_on=True)
    trace_1 = generate_interferometric_trace(
        trajectory,
        reference,
        {"E_sca_complex": np.array([0.0 + 0.0j, 0.1 + 0.0j])},
        sim_cfg,
    )
    trace_2 = generate_interferometric_trace(
        trajectory,
        reference,
        {"E_sca_complex": np.array([0.0 + 0.0j, 0.2 + 0.0j])},
        sim_cfg,
    )

    assert trace_1["scattering_only_intensity"][1] == pytest.approx(0.01)
    assert trace_1["interference_cross_term"][1] == pytest.approx(0.4)
    assert trace_2["scattering_only_intensity"][1] == pytest.approx(4.0 * 0.01)
    assert trace_2["interference_cross_term"][1] == pytest.approx(2.0 * 0.4)


def test_free_brownian_msd_matches_two_dt_per_dimension():
    n_events = 4000
    diffusion_coefficient = 1.0e-12
    cfg = replace(
        DEFAULT_SIM_CFG,
        total_time_s=0.01,
        sampling_rate_Hz=10000.0,
        include_diffusion=True,
        diffusion_hindrance_model="none",
        flow_profile_model="plug",
        reflecting_boundary=False,
        random_seed=123,
    )
    channel = Channel(width_m=1.0e-3, depth_m=1.0e-3)
    trajectory = simulate_particle_trajectory_block(
        channel,
        BASELINE_OPTICAL,
        cfg,
        initial_x_m=np.zeros(n_events),
        initial_z_m=np.zeros(n_events),
        particle_radius_m=50e-9,
        diffusion_coefficient=diffusion_coefficient,
        rng=np.random.default_rng(123),
        export_velocity_trace=False,
    )
    elapsed = float(trajectory["time_s"][-1] - trajectory["time_s"][0])
    expected_variance = 2.0 * diffusion_coefficient * elapsed

    assert np.var(trajectory["x_m"][:, -1], ddof=1) == pytest.approx(expected_variance, rel=0.12)
    assert np.var(trajectory["z_m"][:, -1], ddof=1) == pytest.approx(expected_variance, rel=0.12)


def test_threshold_monotonicity():
    segment = np.array([-0.2, -0.1, 0.0, 0.1, 0.2, 0.25, -0.25])
    threshold_4 = estimate_threshold_stats_robust(segment, sigma_multiplier=4.0)["threshold"]
    threshold_5 = estimate_threshold_stats_robust(segment, sigma_multiplier=5.0)["threshold"]
    threshold_6 = estimate_threshold_stats_robust(segment, sigma_multiplier=6.0)["threshold"]

    assert threshold_4 < threshold_5 < threshold_6
