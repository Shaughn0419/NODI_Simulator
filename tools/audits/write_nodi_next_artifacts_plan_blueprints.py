#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_next_artifacts import (
    ContractValidationError,
    validate_canonical_contract_files,
    write_plan_only_blueprint_bundle,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("results/audits") / f"nodi_next_artifacts_plan_blueprints_{stamp}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Write PLAN_ONLY_NOT_EXECUTED blueprints for future NODI/COMSOL next-artifact "
            "work. This does not run smoke, NODI, COMSOL, or production."
        )
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Confirm writing plan-only blueprint files; this is not execution.",
    )
    parser.add_argument(
        "--smoke-manifest-dir",
        type=Path,
        required=True,
        help="Directory containing the design-only smoke manifest bundle from Report 159.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    parser.add_argument(
        "--check-canonical-contracts",
        action="store_true",
        help="Verify Report 156 patched contract file hashes before writing.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.execute:
        parser.error("refusing to write plan-only blueprints without --execute")

    if args.check_canonical_contracts:
        issues = validate_canonical_contract_files(PROJECT_ROOT)
        if issues:
            print("NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINTS: FAIL")
            for issue in issues:
                print(f"- {issue}")
            return 1

    try:
        metadata = write_plan_only_blueprint_bundle(
            smoke_manifest_dir=args.smoke_manifest_dir,
            output_dir=args.output_dir,
        )
    except ContractValidationError as exc:
        print("NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINTS: FAIL")
        for issue in exc.issues:
            print(f"- {issue}")
        return 1

    print("NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINTS: PASS")
    print(f"output_dir: {args.output_dir}")
    for entry in metadata["files"]:
        print(f"- {entry['artifact']}: {entry['path']} sha256={entry['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
