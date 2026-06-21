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
    AUTHORIZATION_GATE_PASS_STATUS,
    write_next_artifacts_runner_authorization_gate_record,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("results/audits") / f"nodi_next_artifacts_authorization_gate_{stamp}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Write a future authorization gate record for NODI/COMSOL next artifacts. "
            "This writes a no-execution sidecar only; it does not implement runners, "
            "execute smoke, run NODI/COMSOL, or generate production artifacts."
        )
    )
    parser.add_argument(
        "--confirm-write",
        action="store_true",
        help="Confirm writing the authorization-gate sidecar; this is not execution.",
    )
    parser.add_argument(
        "--smoke-manifest-dir",
        type=Path,
        required=True,
        help="Directory containing the design-only smoke manifest bundle from Report 159.",
    )
    parser.add_argument(
        "--plan-blueprint-dir",
        type=Path,
        required=True,
        help="Directory containing the PLAN_ONLY_NOT_EXECUTED blueprint bundle from Report 161.",
    )
    parser.add_argument(
        "--preflight-report",
        type=Path,
        help="Optional no-execution preflight JSON report from Report 160.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_write:
        parser.error("refusing to write authorization gate sidecar without --confirm-write")

    record = write_next_artifacts_runner_authorization_gate_record(
        project_root=PROJECT_ROOT,
        smoke_manifest_dir=args.smoke_manifest_dir,
        plan_blueprint_dir=args.plan_blueprint_dir,
        output_dir=args.output_dir,
        preflight_report_path=args.preflight_report,
    )
    print(f"NODI_NEXT_ARTIFACTS_AUTHORIZATION_GATE: {record['status']}")
    print(f"record_path: {record['record_path']}")
    print(f"record_sha256: {record['record_sha256']}")
    print(f"issue_csv: {record['issue_csv']}")
    for issue in record["issues"]:
        print(f"- {issue}")
    return 0 if record["status"] == AUTHORIZATION_GATE_PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
