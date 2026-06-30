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
    AUTHORIZATION_GATE_PASS_STATUS,
    write_sidewall_package_c_authorization_gate_record,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("results/audits") / f"nodi_sidewall_package_c_authorization_gate_{stamp}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Write a no-execution authorization-gate sidecar for future NODI "
            "sidewall Package C physics work. This does not authorize runtime, "
            "Package C physics, COMSOL launch, .mph load, NODI recomputation, "
            "PRS/EAS numeric output, or production."
        )
    )
    parser.add_argument(
        "--confirm-write",
        action="store_true",
        help="Confirm writing the Package C authorization-gate sidecar; this is not execution.",
    )
    parser.add_argument(
        "--gate23-status",
        type=Path,
        default=PROJECT_ROOT
        / "reports/joint_interface_20260630/NODI_COMSOL_GATE23_SIDEWALL_STATUS_20260630.json",
        help="Gate23 static fixture status JSON.",
    )
    parser.add_argument(
        "--gate23-manifest",
        type=Path,
        default=PROJECT_ROOT
        / "reports/joint_interface_20260630/NODI_COMSOL_GATE23_SIDEWALL_MANIFEST_20260630.csv",
        help="Gate23 static fixture manifest CSV.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_write:
        parser.error("refusing to write sidewall Package C authorization gate without --confirm-write")

    record = write_sidewall_package_c_authorization_gate_record(
        gate23_status_path=args.gate23_status,
        gate23_manifest_path=args.gate23_manifest,
        output_dir=args.output_dir,
    )
    print(f"NODI_SIDEWALL_PACKAGE_C_AUTHORIZATION_GATE: {record['status']}")
    print(f"record_path: {record['record_path']}")
    print(f"record_sha256: {record['record_sha256']}")
    print(f"issue_csv: {record['issue_csv']}")
    for issue in record["issues"]:
        print(f"- {issue}")
    return 0 if record["status"] == AUTHORIZATION_GATE_PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
