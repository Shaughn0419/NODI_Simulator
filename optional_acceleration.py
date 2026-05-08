"""Helpers for optional JIT acceleration dependencies."""

from __future__ import annotations

import warnings


def warn_numba_unavailable(feature: str) -> None:
    """Warn that a feature is running without optional numba acceleration."""
    warnings.warn(
        (
            f"numba is not installed; JIT acceleration is unavailable for {feature}. "
            "Install with: python -m pip install -e '.[acceleration]'"
        ),
        RuntimeWarning,
        stacklevel=3,
    )
