#!/usr/bin/env python3
"""Compatibility wrapper for the simulation-assumption input workspace builder."""

from __future__ import annotations

import sys

from tools.audits.build_nodi_package_c_sidewall_simulation_assumption_input_workspace import *  # noqa: F401,F403
from tools.audits.build_nodi_package_c_sidewall_simulation_assumption_input_workspace import (
    main as _canonical_main,
)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    args = [
        "--confirm-sidewall-simulation-assumption-input-workspace"
        if arg == "--confirm-sidewall-real-evidence-input-workspace"
        else arg
        for arg in args
    ]
    return _canonical_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
