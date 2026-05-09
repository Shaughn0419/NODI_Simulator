"""Compatibility launcher for pre-tiered tool paths.

The repository root is added to ``sys.path`` only as a fallback for direct
source-tree execution of legacy wrappers. Installed/package execution should
prefer the canonical tiered module path.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def run_legacy_tool(
    module_name: str,
    *,
    safe_help: bool = False,
    require_execute: bool = False,
    pass_execute_to_module: bool = False,
) -> None:
    """Run a tiered tool module from a legacy ``tools/<name>.py`` wrapper."""
    if safe_help and any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
        print(
            "Compatibility wrapper for a tiered one-shot tool.\n"
            f"Canonical module: {module_name}\n"
            "Run the tiered path directly for automation; this legacy --help "
            "does not execute the underlying one-shot."
        )
        return

    if require_execute and "--execute" not in sys.argv[1:]:
        print(
            "Compatibility wrapper for a tiered one-shot tool.\n"
            f"Canonical module: {module_name}\n"
            "This legacy wrapper refuses to execute one-shot writers without "
            "explicit confirmation. Run the tiered module directly with "
            f"`python -m {module_name} --execute <your args>` from the repository root, "
            "or use this legacy wrapper with `--execute <your args>`."
        )
        raise SystemExit(2)
    if require_execute and "--execute" in sys.argv[1:] and not pass_execute_to_module:
        sys.argv = [sys.argv[0], *(arg for arg in sys.argv[1:] if arg != "--execute")]

    project_root = Path(__file__).resolve().parents[1]
    for candidate in (str(project_root),):
        if candidate not in sys.path:
            sys.path.insert(0, candidate)
    runpy.run_module(module_name, run_name="__main__")
