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
    PRS_SOURCE_ACCUMULATION_CAMPAIGN_DEFAULT_JOBS_PER_SHARD,
    PRS_SOURCE_ACCUMULATION_CAMPAIGN_DEFAULT_MAX_PARALLEL_SHARDS,
    PRS_SOURCE_ACCUMULATION_CAMPAIGN_MAX_JOBS_PER_SHARD,
    PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_PASS_STATUS,
    write_position_response_source_accumulation_campaign_policy_bundle,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return (
        Path("results/audits")
        / f"nodi_position_response_source_accumulation_campaign_policy_{stamp}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Write a no-execution PRS source accumulation campaign policy. "
            "This creates shard and job-schedule sidecars only; it never runs "
            "NODI, runs COMSOL, regenerates JOINT_ROUTE_CLASS, or generates "
            "production NODI_POSITION_RESPONSE_SURFACE rows."
        )
    )
    parser.add_argument(
        "--confirm-write-campaign-policy",
        action="store_true",
        help="Confirm writing campaign-policy sidecars only.",
    )
    parser.add_argument(
        "--job-plan",
        type=Path,
        required=True,
        help="PRS source accumulation job-plan CSV from Report 174.",
    )
    parser.add_argument(
        "--jobs-per-shard",
        type=int,
        default=PRS_SOURCE_ACCUMULATION_CAMPAIGN_DEFAULT_JOBS_PER_SHARD,
        help=(
            "Number of job-plan rows assigned to each policy shard. "
            "This schedules future work only."
        ),
    )
    parser.add_argument(
        "--max-parallel-shards",
        type=int,
        default=PRS_SOURCE_ACCUMULATION_CAMPAIGN_DEFAULT_MAX_PARALLEL_SHARDS,
        help="Must remain 1 for the first campaign policy.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_write_campaign_policy:
        parser.error(
            "refusing PRS source accumulation campaign-policy write without "
            "--confirm-write-campaign-policy"
        )
    if args.jobs_per_shard < 1 or args.jobs_per_shard > PRS_SOURCE_ACCUMULATION_CAMPAIGN_MAX_JOBS_PER_SHARD:
        parser.error(
            "--jobs-per-shard must be between 1 and "
            f"{PRS_SOURCE_ACCUMULATION_CAMPAIGN_MAX_JOBS_PER_SHARD}"
        )
    if args.max_parallel_shards != 1:
        parser.error("--max-parallel-shards must remain 1 for this policy")

    report = write_position_response_source_accumulation_campaign_policy_bundle(
        job_plan_path=args.job_plan,
        output_dir=args.output_dir,
        jobs_per_shard=int(args.jobs_per_shard),
        max_parallel_shards=int(args.max_parallel_shards),
    )
    print(f"NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_POLICY: {report['status']}")
    print(f"valid_job_count: {report['valid_job_count']}")
    print(f"planned_shard_count: {report['planned_shard_count']}")
    print(f"jobs_per_shard: {report['jobs_per_shard']}")
    print(f"max_parallel_shards: {report['max_parallel_shards']}")
    print(f"planned_requested_event_count: {report['planned_requested_event_count']}")
    print(
        "expected_bin_source_rows_if_all_jobs_complete: "
        f"{report['expected_bin_source_rows_if_all_jobs_complete']}"
    )
    print(f"campaign_shards_csv: {report['campaign_shards_csv']}")
    print(f"campaign_shards_csv_sha256: {report['campaign_shards_csv_sha256']}")
    print(f"campaign_job_schedule_csv: {report['campaign_job_schedule_csv']}")
    print(
        "campaign_job_schedule_csv_sha256: "
        f"{report['campaign_job_schedule_csv_sha256']}"
    )
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report['report_sha256']}")
    for issue in report["issues"]:
        print(f"- issue: {issue}")
    return 0 if report["status"] == PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
