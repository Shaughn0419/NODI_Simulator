#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in (str(PROJECT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from nodi_simulator import realism_v2 as rv2  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run EV/NODI realism v2 R3a reduced-grid named-bundle survey only."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=rv2.DEFAULT_REDUCED_GRID_R3A_DIR,
        help="Output directory for R3a reduced-grid artifacts.",
    )
    parser.add_argument(
        "--write-root-manifest",
        action="store_true",
        help="Also update the repository-root run_manifest.json.",
    )
    args = parser.parse_args(argv)
    summary = rv2.run_reduced_grid_R3a(
        args.output_dir,
        write_root_manifest=args.write_root_manifest,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
