#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_next_artifacts import (
    POSITION_RESPONSE_ARTIFACT,
    validate_canonical_contract_files,
    validate_position_response_surface_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a NODI_POSITION_RESPONSE_SURFACE CSV contract artifact."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument(
        "--allow-pending-source-hash",
        action="store_true",
        help="Allow pending_until_artifact_generation in source hash fields.",
    )
    parser.add_argument(
        "--require-complete-row-arithmetic",
        action="store_true",
        help="Require each route/diameter/view group to have the full 467-row bin shape.",
    )
    parser.add_argument(
        "--check-canonical-contracts",
        action="store_true",
        help="Also verify Report 156 patched contract file hashes before validation.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    issues: list[str] = []
    if args.check_canonical_contracts:
        issues.extend(validate_canonical_contract_files(PROJECT_ROOT))
    issues.extend(
        validate_position_response_surface_csv(
            args.csv_path,
            allow_pending_source_hash=args.allow_pending_source_hash,
            require_complete_row_arithmetic=args.require_complete_row_arithmetic,
        )
    )
    if issues:
        print(f"{POSITION_RESPONSE_ARTIFACT}: FAIL")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print(f"{POSITION_RESPONSE_ARTIFACT}: PASS_CONTEXT_ONLY_NOT_PRODUCTION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
