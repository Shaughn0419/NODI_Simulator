#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_next_artifacts import (  # noqa: E402
    PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
    write_position_response_source_sufficiency_bundle,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("results/audits") / f"nodi_position_response_source_sufficiency_{stamp}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate numeric sufficiency for PRS bin-conditioned source candidates. "
            "This is a preflight-only gate: it never generates production "
            "NODI_POSITION_RESPONSE_SURFACE rows, runs COMSOL, or regenerates "
            "JOINT_ROUTE_CLASS."
        )
    )
    parser.add_argument(
        "--confirm-source-sufficiency-preflight",
        action="store_true",
        help="Confirm writing numeric-sufficiency preflight sidecars only.",
    )
    parser.add_argument(
        "--candidate-source",
        action="append",
        type=Path,
        required=True,
        help="Bin-conditioned PRS source candidate CSV. May be supplied more than once.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_source_sufficiency_preflight:
        parser.error(
            "refusing PRS source numeric-sufficiency preflight without "
            "--confirm-source-sufficiency-preflight"
        )

    report = write_position_response_source_sufficiency_bundle(
        candidate_paths=list(args.candidate_source),
        output_dir=args.output_dir,
    )
    print(f"NODI_POSITION_RESPONSE_SOURCE_NUMERIC_SUFFICIENCY: {report['status']}")
    print(f"candidate_count: {report['candidate_count']}")
    print(
        "numeric_sufficient_candidate_count: "
        f"{report['numeric_sufficient_candidate_count']}"
    )
    print(f"min_events_per_bin_for_production: {report['min_events_per_bin_for_production']}")
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report['report_sha256']}")
    print(f"candidate_csv: {report['candidate_csv']}")
    print(f"candidate_csv_sha256: {report['candidate_csv_sha256']}")
    print(f"blocker_csv: {report['blocker_csv']}")
    print(f"blocker_csv_sha256: {report['blocker_csv_sha256']}")
    print(f"job_plan_csv: {report['job_plan_csv']}")
    print(f"job_plan_csv_sha256: {report['job_plan_csv_sha256']}")
    print(f"issue_csv: {report['issue_csv']}")
    print(f"issue_csv_sha256: {report['issue_csv_sha256']}")
    for blocker in report["blockers"]:
        print(f"- blocker: {blocker['status']}")
    for issue in report["issues"]:
        print(f"- issue: {issue}")
    return 0 if report["status"] == PRS_SOURCE_SUFFICIENCY_PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
