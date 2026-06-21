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
    PRS_SOURCE_PREFLIGHT_PASS_STATUS,
    default_position_response_source_candidate_paths,
    write_position_response_source_preflight_bundle,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("results/audits") / f"nodi_position_response_source_preflight_{stamp}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate NODI_POSITION_RESPONSE_SURFACE source availability. "
            "This is a preflight-only gate: it never generates production PRS rows, "
            "runs NODI, runs COMSOL, or regenerates JOINT_ROUTE_CLASS."
        )
    )
    parser.add_argument(
        "--confirm-source-preflight",
        action="store_true",
        help="Confirm writing PRS source-availability preflight sidecars only.",
    )
    parser.add_argument(
        "--candidate",
        action="append",
        type=Path,
        default=[],
        help=(
            "Candidate source CSV to inspect. May be repeated. If omitted, known "
            "local fullgrid route-level candidates are inspected."
        ),
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_source_preflight:
        parser.error(
            "refusing PRS source preflight without --confirm-source-preflight"
        )

    candidates = args.candidate or default_position_response_source_candidate_paths(
        PROJECT_ROOT
    )
    report = write_position_response_source_preflight_bundle(
        candidate_paths=candidates,
        output_dir=args.output_dir,
    )
    print(f"NODI_POSITION_RESPONSE_SOURCE_PREFLIGHT: {report['status']}")
    print(f"candidate_count: {report['candidate_count']}")
    print(f"source_available_candidate_count: {report['source_available_candidate_count']}")
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report['report_sha256']}")
    print(f"candidate_csv: {report['candidate_csv']}")
    print(f"candidate_csv_sha256: {report['candidate_csv_sha256']}")
    print(f"blocker_csv: {report['blocker_csv']}")
    print(f"blocker_csv_sha256: {report['blocker_csv_sha256']}")
    print(f"issue_csv: {report['issue_csv']}")
    for blocker in report["blockers"]:
        print(f"- {blocker['artifact']}: {blocker['status']}")
    for issue in report["issues"]:
        print(f"- issue: {issue}")
    return 0 if report["status"] == PRS_SOURCE_PREFLIGHT_PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
