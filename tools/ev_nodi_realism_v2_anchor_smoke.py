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

from nodi_simulator.realism_v2 import DEFAULT_ANCHOR_SMOKE_DIR, run_anchor_smoke


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run EV/NODI realism v2 R2 anchor smoke only."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_ANCHOR_SMOKE_DIR,
        help="Output directory for R2 anchor-smoke artifacts.",
    )
    parser.add_argument(
        "--no-optional-routes",
        action="store_true",
        help="Use only the 12 required routes instead of the capped 14-route panel.",
    )
    args = parser.parse_args(argv)
    summary = run_anchor_smoke(
        args.output_dir,
        include_optional_routes=not args.no_optional_routes,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
