"""
Compatibility package for environments where the project directory has been
renamed and is no longer literally called ``nodi_simulator``.

This shim exposes the project root as the ``nodi_simulator`` package path so
imports such as ``nodi_simulator.dashboard.backend`` continue to work.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Allow ``nodi_simulator.<submodule>`` to resolve to modules that still live at
# the project root (for example ``dashboard/`` and ``tests/``).
__path__ = [str(_PROJECT_ROOT)]

# Reuse the canonical package exports defined at the project root.
_ROOT_INIT = _PROJECT_ROOT / "__init__.py"
_ROOT_EXPORTS_MODULE = "nodi_simulator._root_exports"
_spec = importlib.util.spec_from_file_location(_ROOT_EXPORTS_MODULE, _ROOT_INIT)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load canonical package exports from {_ROOT_INIT}")

_root_exports = importlib.util.module_from_spec(_spec)
sys.modules[_ROOT_EXPORTS_MODULE] = _root_exports
_spec.loader.exec_module(_root_exports)

for _name, _value in vars(_root_exports).items():
    if _name in {"__builtins__", "__cached__", "__loader__", "__name__", "__spec__"}:
        continue
    globals()[_name] = _value

__all__ = [
    _name
    for _name in globals()
    if not _name.startswith("_") and _name not in {"importlib", "sys", "Path"}
]
