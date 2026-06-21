#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_next_artifacts import (
    APERTURE_SURROGATE_ARTIFACT,
    validate_canonical_contract_files,
    validate_effective_aperture_surrogate_csv,
    validate_geometry_descriptor_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY CSV."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument(
        "--geometry-descriptor",
        type=Path,
        help="Optional COMSOL_GEOMETRY_DESCRIPTOR_V1.csv to validate before EAS rows.",
    )
    parser.add_argument(
        "--allow-pending-source-hash",
        action="store_true",
        help="Allow pending_until_artifact_generation in source hash fields.",
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
    if args.geometry_descriptor is not None:
        issues.extend(validate_geometry_descriptor_csv(args.geometry_descriptor))
    issues.extend(
        validate_effective_aperture_surrogate_csv(
            args.csv_path,
            allow_pending_source_hash=args.allow_pending_source_hash,
        )
    )
    if issues:
        print(f"{APERTURE_SURROGATE_ARTIFACT}: FAIL")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print(f"{APERTURE_SURROGATE_ARTIFACT}: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
