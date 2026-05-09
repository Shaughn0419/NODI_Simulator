from __future__ import annotations

import math

import pytest

from nodi_simulator.type_coerce import (
    as_float,
    blocker_summary,
    clamp01,
    finite_float,
    finite_float_or_nan,
    float_or_nan,
    optional_finite_float,
    positive_ratio,
    wilson_half_width,
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


def test_clamp01_bounds_numeric_values():
    assert clamp01(-0.25) == 0.0
    assert clamp01("0.4") == 0.4
    assert clamp01(1.5) == 1.0


def test_positive_ratio_rejects_missing_or_invalid_denominators():
    assert positive_ratio(3.0, 2.0) == 1.5
    assert positive_ratio(None, 2.0) is None
    assert positive_ratio(3.0, 0.0) is None
    assert positive_ratio(3.0, float("inf")) == 0.0
    assert positive_ratio(
        3.0,
        float("inf"),
        require_finite_denominator=True,
    ) is None


def test_blocker_summary_formats_empty_deduped_and_custom_separator_cases():
    assert blocker_summary([]) == "none"
    assert blocker_summary(["a", "b"]) == "a / b"
    assert blocker_summary(["a", "a", "b"], dedupe=True) == "a / b"
    assert blocker_summary(["a", "b"], separator="; ") == "a; b"


def test_wilson_half_width_matches_legacy_callers_and_zero_total_modes():
    assert wilson_half_width(5, 10) == pytest.approx(0.2634104063845127)
    assert wilson_half_width(0, 0, zero_total=1.0) == 1.0
    with pytest.raises(ValueError, match="total must be positive"):
        wilson_half_width(0, 0)
