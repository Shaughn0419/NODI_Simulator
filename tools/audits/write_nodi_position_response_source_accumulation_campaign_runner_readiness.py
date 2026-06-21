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
    PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_PASS_STATUS,
    write_position_response_source_accumulation_campaign_runner_readiness_bundle,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return (
        Path("results/audits")
        / f"nodi_position_response_source_accumulation_campaign_runner_readiness_{stamp}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Write a no-execution PRS source accumulation campaign runner-readiness "
            "bundle. This selects one planned shard and confirms the next execution "
            "gate; it never runs NODI, runs COMSOL, regenerates JOINT_ROUTE_CLASS, "
            "or generates production NODI_POSITION_RESPONSE_SURFACE rows."
        )
    )
    parser.add_argument(
        "--confirm-write-runner-readiness",
        action="store_true",
        help="Confirm writing runner-readiness sidecars only.",
    )
    parser.add_argument(
        "--campaign-report",
        type=Path,
        required=True,
        help="Campaign-policy report JSON from Report 177.",
    )
    parser.add_argument(
        "--campaign-shard-id",
        default=None,
        help="Campaign shard id to prepare. Defaults to the first planned shard.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_write_runner_readiness:
        parser.error(
            "refusing PRS campaign runner-readiness write without "
            "--confirm-write-runner-readiness"
        )

    report = write_position_response_source_accumulation_campaign_runner_readiness_bundle(
        campaign_report_path=args.campaign_report,
        output_dir=args.output_dir,
        campaign_shard_id=args.campaign_shard_id,
    )
    print(
        "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS: "
        f"{report['status']}"
    )
    print(f"selected_campaign_shard_id: {report['selected_campaign_shard_id']}")
    print(f"selected_job_count: {report['selected_job_count']}")
    print(
        "selected_planned_requested_event_count: "
        f"{report['selected_planned_requested_event_count']}"
    )
    print(
        "selected_expected_bin_source_rows: "
        f"{report['selected_expected_bin_source_rows']}"
    )
    print(f"shard_execution_authorized: {report['shard_execution_authorized']}")
    print(f"nodi_run_performed: {report['nodi_run_performed']}")
    print(
        "position_response_surface_production_generated: "
        f"{report['position_response_surface_production_generated']}"
    )
    print(f"selected_shard_schedule_csv: {report['selected_shard_schedule_csv']}")
    print(
        "selected_shard_schedule_csv_sha256: "
        f"{report['selected_shard_schedule_csv_sha256']}"
    )
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report['report_sha256']}")
    for issue in report["issues"]:
        print(f"- issue: {issue}")
    return (
        0
        if report["status"]
        == PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_PASS_STATUS
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
