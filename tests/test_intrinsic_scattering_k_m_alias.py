from __future__ import annotations

import pytest

from dashboard.config import THETA_GRID_RAD
from nodi_simulator.data_objects import BASELINE_PARTICLE, WATER
from nodi_simulator.intrinsic_scattering import compute_intrinsic_scattering


def test_intrinsic_scattering_k_m_is_canonical_and_legacy_alias_is_exact() -> None:
    intrinsic = compute_intrinsic_scattering(
        BASELINE_PARTICLE,
        WATER,
        660e-9,
        THETA_GRID_RAD,
    )

    expected_k_m = (
        2.0
        * 3.141592653589793
        * WATER.refractive_index_at(660e-9)
        / 660e-9
    )

    assert intrinsic["k_m"] == pytest.approx(expected_k_m)
    assert intrinsic["k_m_inv"] == pytest.approx(intrinsic["k_m"])
    assert intrinsic["k_m_inv_alias_status"] == "deprecated_legacy_alias_for_k_m_not_inverse"
