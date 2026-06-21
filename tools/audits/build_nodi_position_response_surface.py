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
    RUNNER_IMPLEMENTATION_READY_STATUS,
    write_position_response_runner_launch_plan,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("results/audits") / f"nodi_position_response_surface_runner_launch_{stamp}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create the implementation launch plan for the future "
            "NODI_POSITION_RESPONSE_SURFACE runner. This does not execute the runner, "
            "run smoke, run NODI/COMSOL, or generate production rows."
        )
    )
    parser.add_argument(
        "--confirm-write-launch-plan",
        action="store_true",
        help="Write the implementation launch-plan sidecar only; this is not execution.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_write_launch_plan:
        parser.error(
            "refusing to write PRS runner launch plan without --confirm-write-launch-plan"
        )

    plan = write_position_response_runner_launch_plan(args.output_dir)
    print(f"NODI_POSITION_RESPONSE_SURFACE_RUNNER: {plan['runner_implementation_status']}")
    print(f"runner_execution_status: {plan['runner_execution_status']}")
    print(f"launch_plan_path: {plan['launch_plan_path']}")
    print(f"launch_plan_sha256: {plan['launch_plan_sha256']}")
    return 0 if plan["runner_implementation_status"] == RUNNER_IMPLEMENTATION_READY_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
