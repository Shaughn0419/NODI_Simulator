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
    PRS_SOURCE_ACCUMULATION_APPROVED_ROUTE_SCOPES,
    PRS_SOURCE_ACCUMULATION_PASS_STATUS,
    PRS_SOURCE_ACCUMULATION_SEEDS,
    PRS_SOURCE_ACCUMULATION_TARGET_EVENTS_PER_SEED,
    write_position_response_source_accumulation_job_plan_bundle,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("results/audits") / f"nodi_position_response_source_accumulation_job_plan_{stamp}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Write a PRS source accumulation job plan. This is planning only: "
            "it never runs NODI, runs COMSOL, regenerates JOINT_ROUTE_CLASS, or "
            "generates production NODI_POSITION_RESPONSE_SURFACE rows."
        )
    )
    parser.add_argument(
        "--confirm-write-job-plan",
        action="store_true",
        help="Confirm writing source accumulation job-plan sidecars only.",
    )
    parser.add_argument(
        "--route-source",
        type=Path,
        required=True,
        help="Runner-compatible EV/gold route-source CSV.",
    )
    parser.add_argument(
        "--route-scope",
        choices=sorted(PRS_SOURCE_ACCUMULATION_APPROVED_ROUTE_SCOPES),
        default="all_approved",
    )
    parser.add_argument(
        "--seed",
        action="append",
        type=int,
        help=(
            "Seed to include in the plan. May be repeated. Defaults to the "
            "canonical PRS source accumulation seed set."
        ),
    )
    parser.add_argument(
        "--n-events-per-seed",
        type=int,
        default=PRS_SOURCE_ACCUMULATION_TARGET_EVENTS_PER_SEED,
        help=(
            "Requested event count per route/diameter/view/seed job. This is a "
            "diagnostic floor, not a sufficiency guarantee."
        ),
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_write_job_plan:
        parser.error(
            "refusing PRS source accumulation job-plan write without "
            "--confirm-write-job-plan"
        )

    seeds = tuple(args.seed) if args.seed else PRS_SOURCE_ACCUMULATION_SEEDS
    report = write_position_response_source_accumulation_job_plan_bundle(
        route_source_path=args.route_source,
        output_dir=args.output_dir,
        route_scope=str(args.route_scope),
        seeds=seeds,
        n_events_per_seed=int(args.n_events_per_seed),
    )
    print(f"NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_JOB_PLAN: {report['status']}")
    print(f"planned_job_count: {report['planned_job_count']}")
    print(f"planned_requested_event_count: {report['planned_requested_event_count']}")
    print(f"route_source_path: {report['route_source_path']}")
    print(f"route_source_sha256: {report['route_source_sha256']}")
    print(f"job_plan_csv: {report['job_plan_csv']}")
    print(f"job_plan_csv_sha256: {report['job_plan_csv_sha256']}")
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report['report_sha256']}")
    print(f"blocker_csv: {report['blocker_csv']}")
    print(f"issue_csv: {report['issue_csv']}")
    for blocker in report["blockers"]:
        print(f"- blocker: {blocker['status']}")
    for issue in report["issues"]:
        print(f"- issue: {issue}")
    return 0 if report["status"] == PRS_SOURCE_ACCUMULATION_PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
