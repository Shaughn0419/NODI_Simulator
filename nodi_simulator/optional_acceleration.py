"""Helpers for optional JIT acceleration dependencies."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from typing import Any


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


def optional_numba_njit(njit: Callable[..., Any] | None) -> Callable[..., Any]:
    """Return a decorator factory that is a no-op when numba is unavailable."""

    def maybe_njit(*args: Any, **kwargs: Any) -> Callable[..., Any]:
        if njit is None:
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                return func

            return decorator
        return njit(*args, **kwargs)

    return maybe_njit
