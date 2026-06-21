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
    BOUNDED_SMOKE_EXECUTION_PASS_STATUS,
    write_bounded_smoke_execution_bundle,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("results/audits") / f"nodi_next_artifacts_bounded_smoke_execution_{stamp}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the bounded-smoke sidecar execution for NODI/COMSOL next artifacts. "
            "This writes smoke execution evidence only; it does not run COMSOL, run "
            "NODI production, regenerate JOINT_ROUTE_CLASS, or generate production "
            "PRS/EAS rows."
        )
    )
    parser.add_argument(
        "--confirm-bounded-smoke-execution",
        action="store_true",
        help="Confirm bounded-smoke sidecar execution only; this is not production.",
    )
    parser.add_argument(
        "--authorization-phrase",
        required=True,
        help="Exact bounded-smoke authorization phrase supplied by the user.",
    )
    parser.add_argument(
        "--readiness-report",
        type=Path,
        required=True,
        help="Bounded-smoke readiness report JSON from the prior preflight.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_bounded_smoke_execution:
        parser.error(
            "refusing bounded-smoke sidecar execution without "
            "--confirm-bounded-smoke-execution"
        )

    report = write_bounded_smoke_execution_bundle(
        readiness_report_path=args.readiness_report,
        authorization_phrase=args.authorization_phrase,
        output_dir=args.output_dir,
    )
    print(f"NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION: {report['status']}")
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report['report_sha256']}")
    print(f"issue_csv: {report['issue_csv']}")
    for file_entry in report.get("files", []):
        print(f"file: {file_entry['path']}")
        print(f"sha256: {file_entry['sha256']}")
    for issue in report["issues"]:
        print(f"- {issue}")
    return 0 if report["status"] == BOUNDED_SMOKE_EXECUTION_PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
