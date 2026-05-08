from __future__ import annotations

import math

from nodi_simulator.type_coerce import (
    as_float,
    finite_float,
    finite_float_or_nan,
    float_or_nan,
    optional_finite_float,
)


def test_as_float_preserves_numeric_values_and_uses_default_on_conversion_failure():
    assert as_float("1.25") == 1.25
    assert as_float(None, 7.0) == 7.0


def test_finite_float_rejects_nan_and_infinity():
    assert finite_float("nan", 3.0) == 3.0
    assert finite_float(float("inf"), 4.0) == 4.0
    assert finite_float("2.5", 0.0) == 2.5


def test_nan_default_helpers_preserve_nan_on_invalid_values():
    assert math.isnan(float_or_nan("bad"))
    assert math.isinf(float_or_nan(float("inf")))
    assert math.isnan(finite_float_or_nan("bad"))
    assert math.isnan(finite_float_or_nan(float("inf")))


def test_optional_finite_float_preserves_none_default():
    assert optional_finite_float("bad") is None
    assert optional_finite_float("nan") is None
    assert optional_finite_float("bad", 1.0) == 1.0
    assert optional_finite_float(math.pi) == math.pi
