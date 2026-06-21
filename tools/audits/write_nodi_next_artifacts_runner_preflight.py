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
    write_no_execution_runner_preflight_report,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("results/audits") / f"nodi_next_artifacts_runner_preflight_{stamp}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Write a no-execution implementation preflight report for future NODI/COMSOL "
            "next-artifact work. This is not runner authorization and does not run smoke, "
            "NODI, COMSOL, or production."
        )
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Confirm writing the no-execution preflight report, not runner execution.",
    )
    parser.add_argument(
        "--smoke-manifest-dir",
        type=Path,
        required=True,
        help="Directory containing the design-only smoke manifest bundle from Report 159.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    parser.add_argument(
        "--geometry-descriptor",
        type=Path,
        help="Optional COMSOL_GEOMETRY_DESCRIPTOR_V1.csv to validate in preflight.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.execute:
        parser.error("refusing to write no-execution preflight report without --execute")

    report = write_no_execution_runner_preflight_report(
        project_root=PROJECT_ROOT,
        smoke_manifest_dir=args.smoke_manifest_dir,
        output_dir=args.output_dir,
        geometry_descriptor_path=args.geometry_descriptor,
    )
    print(f"NODI_NEXT_ARTIFACTS_NO_EXECUTION_PREFLIGHT: {report['status']}")
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report['report_sha256']}")
    print(f"issue_csv: {report['issue_csv']}")
    for issue in report["issues"]:
        print(f"- {issue}")
    return 0 if report["status"] == "PASS_NO_EXECUTION_IMPLEMENTATION_PREFLIGHT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
