"""Small numeric coercion helpers shared by diagnostics modules."""

from __future__ import annotations

import math
from typing import Any


def as_float(value: Any, default: float = 0.0) -> float:
    """Return ``float(value)`` or ``default`` when conversion fails."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def float_or_nan(value: Any, default: float = math.nan) -> float:
    """Return ``float(value)`` or ``default`` when conversion fails."""
    return as_float(value, default)


def finite_float(value: Any, default: float = 0.0) -> float:
    """Return a finite float or ``default`` for missing, invalid, NaN, or inf."""
    numeric = as_float(value, default)
    return numeric if math.isfinite(numeric) else default


def finite_float_or_nan(value: Any, default: float = math.nan) -> float:
    """Return a finite float or ``default`` for missing, invalid, NaN, or inf."""
    return finite_float(value, default)


def optional_finite_float(
    value: Any,
    default: float | None = None,
) -> float | None:
    """Return a finite float, preserving ``None`` defaults for absent values."""
    numeric = as_float(value, math.nan)
    return numeric if math.isfinite(numeric) else default


def clamp01(value: Any) -> float:
    """Clamp a numeric value into the closed unit interval."""
    return max(0.0, min(1.0, float(value)))


def positive_ratio(
    numerator: float | None,
    denominator: float | None,
    *,
    require_finite_denominator: bool = False,
) -> float | None:
    """Return ``numerator / denominator`` when the denominator is positive."""
    if numerator is None or denominator is None:
        return None
    denominator_float = float(denominator)
    if denominator_float <= 0.0:
        return None
    if require_finite_denominator and not math.isfinite(denominator_float):
        return None
    return float(float(numerator) / denominator_float)


def blocker_summary(
    blockers: Any,
    *,
    separator: str = " / ",
    empty: str = "none",
    dedupe: bool = False,
) -> str:
    """Summarize blocker tokens with optional de-duplication."""
    items = [str(item) for item in blockers if item]
    if dedupe:
        items = list(dict.fromkeys(items))
    return empty if not items else separator.join(items)


def wilson_half_width(
    successes: int,
    total: int,
    *,
    z: float = 1.96,
    zero_total: float | None = None,
) -> float:
    """Return half-width of the Wilson interval for a binomial estimate."""
    if total <= 0:
        if zero_total is None:
            raise ValueError("total must be positive")
        return float(zero_total)
    total_i = int(total)
    p_hat = int(successes) / total_i
    denom = 1.0 + z**2 / total_i
    return float(
        z
        * math.sqrt(p_hat * (1.0 - p_hat) / total_i + z**2 / (4.0 * total_i**2))
        / denom
    )
