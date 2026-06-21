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
    POSITION_RESPONSE_BIN_SOURCE_ARTIFACT,
    PRS_BIN_SOURCE_SMOKE_PASS_STATUS,
    write_position_response_bin_source_smoke_bundle,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("results/audits") / f"nodi_position_response_bin_source_smoke_{stamp}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a bounded smoke fixture for the future "
            "NODI_POSITION_RESPONSE bin-conditioned source. This does not generate "
            "production PRS rows, run COMSOL, or regenerate JOINT_ROUTE_CLASS."
        )
    )
    parser.add_argument(
        "--confirm-smoke-source",
        action="store_true",
        help="Confirm writing bounded source-builder smoke artifacts only.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_smoke_source:
        parser.error("refusing source smoke without --confirm-smoke-source")

    report = write_position_response_bin_source_smoke_bundle(args.output_dir)
    print(f"{POSITION_RESPONSE_BIN_SOURCE_ARTIFACT}: {report['status']}")
    print(f"event_rows: {report['event_rows']}")
    print(f"bin_source_rows: {report['bin_source_rows']}")
    print(f"event_fixture_path: {report['event_fixture_path']}")
    print(f"event_fixture_sha256: {report['event_fixture_sha256']}")
    print(f"bin_source_path: {report['bin_source_path']}")
    print(f"bin_source_sha256: {report['bin_source_sha256']}")
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report['report_sha256']}")
    for issue in report["issues"]:
        print(f"- issue: {issue}")
    return 0 if report["status"] == PRS_BIN_SOURCE_SMOKE_PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
