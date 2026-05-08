#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_PARENT = PROJECT_ROOT.parent
for candidate in (str(PROJECT_ROOT), str(PROJECT_PARENT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from nodi_simulator.realism_v2 import DEFAULT_UNCERTAINTY_R3B_DIR, run_uncertainty_R3b


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run EV/NODI realism v2 R3b route-sensitive uncertainty expansion only."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_UNCERTAINTY_R3B_DIR,
        help="Output directory for R3b uncertainty artifacts.",
    )
    args = parser.parse_args(argv)
    summary = run_uncertainty_R3b(args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
