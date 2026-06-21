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
    BOUNDED_SMOKE_READINESS_PASS_STATUS,
    write_bounded_smoke_readiness_report,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("results/audits") / f"nodi_next_artifacts_bounded_smoke_readiness_{stamp}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Write a bounded-smoke readiness preflight report for NODI/COMSOL next "
            "artifacts. This writes a sidecar only and does not execute runners, "
            "smoke, NODI, COMSOL, or production generation."
        )
    )
    parser.add_argument(
        "--confirm-write-readiness",
        action="store_true",
        help="Confirm writing the readiness sidecar only; this is not smoke execution.",
    )
    parser.add_argument(
        "--prs-launch-plan",
        type=Path,
        required=True,
        help="PRS runner launch-plan JSON from Report 164.",
    )
    parser.add_argument(
        "--eas-launch-plan",
        type=Path,
        required=True,
        help="EAS runner launch-plan JSON from Report 164.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_write_readiness:
        parser.error(
            "refusing to write bounded-smoke readiness without --confirm-write-readiness"
        )

    report = write_bounded_smoke_readiness_report(
        prs_launch_plan_path=args.prs_launch_plan,
        eas_launch_plan_path=args.eas_launch_plan,
        output_dir=args.output_dir,
    )
    print(f"NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_READINESS: {report['status']}")
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report['report_sha256']}")
    print(f"issue_csv: {report['issue_csv']}")
    for issue in report["issues"]:
        print(f"- {issue}")
    return 0 if report["status"] == BOUNDED_SMOKE_READINESS_PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
