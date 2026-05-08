from __future__ import annotations

import tomllib
import warnings
from pathlib import Path

from nodi_simulator.optional_acceleration import warn_numba_unavailable
import nodi_simulator.trajectory as trajectory


def test_numba_is_declared_as_optional_acceleration_not_required_runtime_dependency():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert "numba" not in pyproject["project"]["dependencies"]
    assert "numba" in pyproject["project"]["optional-dependencies"]["acceleration"]


def test_optional_njit_decorator_falls_back_to_plain_function_without_numba(monkeypatch):
    monkeypatch.setattr(trajectory, "njit", None)

    decorated = trajectory._optional_njit()(lambda value: value + 1)

    assert decorated(1) == 2


def test_missing_numba_warning_names_acceleration_extra():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        warn_numba_unavailable("test kernels")

    assert caught
    message = str(caught[0].message)
    assert "numba is not installed" in message
    assert "[acceleration]" in message
