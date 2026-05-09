from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in (PROJECT_ROOT,):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from nodi_simulator import realism_v2 as rv2


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute capped R5 full-grid v2 only.")
    parser.add_argument(
        "--output-dir",
        default=str(rv2.DEFAULT_R5_FULL_GRID_V2_DIR),
        help="Directory for R5 full-grid v2 outputs.",
    )
    parser.add_argument(
        "--write-root-manifest",
        action="store_true",
        help="Also update the repository-root run_manifest.json.",
    )
    args = parser.parse_args()

    summary = rv2.run_R5_full_grid_v2(
        args.output_dir,
        write_root_manifest=args.write_root_manifest,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
