#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_next_artifacts import (
    SIDEWALL_PACKAGE_D_PRECHECK_ARTIFACT,
    validate_sidewall_package_d_precheck_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a NODI sidewall Package D precheck CSV artifact."
    )
    parser.add_argument("csv_path", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    issues = validate_sidewall_package_d_precheck_csv(args.csv_path)
    if issues:
        print(f"{SIDEWALL_PACKAGE_D_PRECHECK_ARTIFACT}: FAIL")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print(f"{SIDEWALL_PACKAGE_D_PRECHECK_ARTIFACT}: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
