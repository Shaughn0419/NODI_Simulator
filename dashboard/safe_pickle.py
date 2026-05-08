"""Restricted pickle helpers for dashboard-generated artifacts."""

from __future__ import annotations

import pickle  # nosec B403
from typing import Any, BinaryIO


_ALLOWED_PICKLE_GLOBALS: frozenset[tuple[str, str]] = frozenset({
    ("numpy", "dtype"),
    ("numpy", "ndarray"),
    ("numpy.core.multiarray", "_reconstruct"),
    ("numpy.core.multiarray", "scalar"),
    ("numpy._core.multiarray", "_reconstruct"),
    ("numpy._core.multiarray", "scalar"),
})


class RestrictedDashboardUnpickler(pickle.Unpickler):
    """Unpickler limited to primitive containers and numpy scalar/array payloads."""

    def find_class(self, module: str, name: str) -> Any:
        if (module, name) in _ALLOWED_PICKLE_GLOBALS:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(
            f"Forbidden class in dashboard pickle artifact: {module}.{name}"
        )


def load_dashboard_pickle(file_obj: BinaryIO) -> Any:
    """Load a dashboard-generated pickle artifact with restricted globals."""
    return RestrictedDashboardUnpickler(file_obj).load()


def dump_dashboard_pickle(file_obj: BinaryIO, payload: Any) -> None:
    """Write a dashboard pickle artifact using the highest available protocol."""
    pickle.dump(payload, file_obj, protocol=pickle.HIGHEST_PROTOCOL)
