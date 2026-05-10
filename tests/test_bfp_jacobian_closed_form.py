from __future__ import annotations

import math

import pytest

from nodi_simulator.post_v2_audit import direction_cosine_jacobian


pytestmark = pytest.mark.review_package_required


def test_direction_cosine_jacobian_is_finite_inside_na_support() -> None:
    assert math.isfinite(direction_cosine_jacobian(0.2, 0.3))
    assert direction_cosine_jacobian(0.0, 0.0) == pytest.approx(1.0)


def test_direction_cosine_jacobian_paraxial_limit_approaches_constant_weighting() -> None:
    assert direction_cosine_jacobian(1e-6, -1e-6) == pytest.approx(1.0, rel=1e-9)


def test_direction_cosine_jacobian_edge_behavior_is_explicit() -> None:
    near_edge = direction_cosine_jacobian(0.999, 0.0)

    assert math.isfinite(near_edge)
    with pytest.raises(ValueError, match="inside unit NA support"):
        direction_cosine_jacobian(1.0, 0.0)
