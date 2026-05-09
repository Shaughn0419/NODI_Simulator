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
        description=(
            "Run EV/NODI realism v2 R4 representative full-wave validation only."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=rv2.DEFAULT_REPRESENTATIVE_FULL_WAVE_R4_DIR,
        help="Output directory for R4 representative full-wave artifacts.",
    )
    parser.add_argument(
        "--authorization",
        default="PASS_TO_R4_REPRESENTATIVE_FULL_WAVE_VALIDATION_ONLY",
        help="Exact external authorization gate required to execute R4.",
    )
    parser.add_argument(
        "--require-numerical-backend",
        action="store_true",
        help="Fail instead of writing a contract-proxy audit run when no solver backend is installed.",
    )
    parser.add_argument(
        "--write-root-manifest",
        action="store_true",
        help="Also update the repository-root run_manifest.json.",
    )
    args = parser.parse_args(argv)
    summary = rv2.run_representative_full_wave_R4(
        args.output_dir,
        external_authorization=args.authorization,
        write_root_manifest=args.write_root_manifest,
        allow_contract_proxy_when_backend_missing=not args.require_numerical_backend,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
