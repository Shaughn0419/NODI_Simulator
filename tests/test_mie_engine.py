from __future__ import annotations

import numpy as np
import pytest

from nodi_simulator import mie_engine as mie_engine_module
from nodi_simulator.mie_engine import (
    mie_angular,
    mie_coefficients,
    mie_compute,
    mie_core_shell_coefficients,
)


def test_nonabsorbing_homogeneous_sphere_conserves_extinction_to_scattering():
    qext, qsca = mie_compute(0.8, complex(1.45, 0.0))

    assert qext > 0.0
    assert qsca > 0.0
    assert qext == pytest.approx(qsca, rel=1e-3)


def test_mie_angular_returns_complex_amplitudes_on_theta_grid():
    theta = np.linspace(0.05, np.pi - 0.05, 17)

    s1, s2 = mie_angular(0.8, complex(1.45, 0.0), theta)

    assert s1.shape == theta.shape
    assert s2.shape == theta.shape
    assert np.iscomplexobj(s1)
    assert np.iscomplexobj(s2)
    assert np.all(np.isfinite(s1.real))
    assert np.all(np.isfinite(s2.real))


def test_core_shell_matches_homogeneous_solution_when_indices_match():
    size_parameter = 1.2
    refractive_index = complex(1.42, 0.0)

    a_homogeneous, b_homogeneous = mie_coefficients(size_parameter, refractive_index)
    a_shell, b_shell = mie_core_shell_coefficients(
        size_parameter,
        core_radius_ratio=0.65,
        m_shell_rel=refractive_index,
        m_core_rel=refractive_index,
    )

    np.testing.assert_allclose(a_shell, a_homogeneous, rtol=1e-7, atol=1e-10)
    np.testing.assert_allclose(b_shell, b_homogeneous, rtol=1e-7, atol=1e-10)


def test_private_riccati_bessel_fails_fast_at_zero():
    with pytest.raises(ValueError, match="non-zero size parameter"):
        mie_engine_module._riccati_bessel(0.0, 2)
