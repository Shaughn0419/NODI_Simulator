#!/usr/bin/env python3
"""Generate pre-3seed/10000e logic-hardening artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.pre3seed_hardening import (
    VERIFICATION_SUMMARY_PATH,
    generate_pre3seed_hardening_artifacts,
    run_verification_suite,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate route governance, formula ledger, ablation, stability, "
            "smoke/rehearsal, freeze manifest, and dry-report artifacts for "
            "the pre-3seed/10000e gate."
        )
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Repository root. Defaults to the parent of tools/.",
    )
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="Skip the actual low-event micro integrated smoke run.",
    )
    parser.add_argument(
        "--skip-rehearsal",
        action="store_true",
        help="Skip the actual low-event three-seed rehearsal run.",
    )
    parser.add_argument(
        "--run-verification",
        action="store_true",
        help=(
            "Run the preflight pytest suite first, persist its summary, then "
            "regenerate artifacts so the freeze manifest includes the test hash."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    project_root = args.project_root.resolve()
    verification_summary = None
    if args.run_verification:
        verification_summary = run_verification_suite(project_root)
    artifacts = generate_pre3seed_hardening_artifacts(
        project_root=project_root,
        run_smoke=not args.skip_smoke,
        run_rehearsal=not args.skip_rehearsal,
        verification_summary_path=(
            project_root / VERIFICATION_SUMMARY_PATH
            if verification_summary is not None
            else None
        ),
    )
    print(json.dumps(artifacts, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
