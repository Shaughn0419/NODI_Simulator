"""
Compatibility package for environments where the project directory has been
renamed and is no longer literally called ``nodi_simulator``.

This shim exposes the project root as the ``nodi_simulator`` package path so
imports such as ``nodi_simulator.dashboard.backend`` continue to work.
"""

from __future__ import annotations

import types
from pathlib import Path


_PACKAGE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _PACKAGE_DIR.parent

# Allow ``nodi_simulator.<submodule>`` to resolve to modules that still live at
# the project root (for example ``dashboard/`` and ``tests/``). Prefer real
# package-local modules as they are migrated into ``nodi_simulator/``.
__path__ = [str(_PACKAGE_DIR), str(_PROJECT_ROOT)]

# Reuse the canonical package exports defined inside the package.
from . import _exports as _package_exports

for _name, _value in vars(_package_exports).items():
    if _name.startswith("__") and _name != "__version__":
        continue
    if isinstance(_value, types.ModuleType):
        continue
    globals()[_name] = _value

__all__ = [
    _name
    for _name in globals()
    if not _name.startswith("_") and _name not in {"types", "Path"}
]
