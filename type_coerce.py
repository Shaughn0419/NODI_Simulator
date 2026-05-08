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
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return numeric if math.isfinite(numeric) else default
