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
    PRS_EDGE_PRIMARY_CANDIDATE_PASS_STATUS,
    write_position_response_edge_primary_candidate_bundle,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("tmp") / f"nodi_position_response_edge_primary_candidate_{stamp}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a production-shaped NODI_POSITION_RESPONSE_SURFACE edge-primary "
            "candidate from a bin-conditioned source. The candidate is validated "
            "against the production PRS row contract but is not promoted into the "
            "production-generation gate. This command does not run NODI, run COMSOL, "
            "or regenerate JOINT_ROUTE_CLASS."
        )
    )
    parser.add_argument(
        "--confirm-edge-primary-candidate",
        action="store_true",
        help="Confirm writing the not-promoted edge-primary PRS candidate.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Eligible NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE CSV.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_edge_primary_candidate:
        parser.error(
            "refusing to write candidate rows without "
            "--confirm-edge-primary-candidate"
        )

    report = write_position_response_edge_primary_candidate_bundle(
        source_path=args.source,
        output_dir=args.output_dir,
    )
    print(f"NODI_POSITION_RESPONSE_EDGE_PRIMARY_CANDIDATE: {report['status']}")
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report['report_sha256']}")
    print(f"candidate_csv: {report['candidate_csv']}")
    print(f"candidate_csv_sha256: {report['candidate_csv_sha256']}")
    print(f"candidate_row_count: {report['candidate_row_count']}")
    print(f"xz_primary_promoted_row_count: {report['xz_primary_promoted_row_count']}")
    print("candidate_promoted_to_production_gate: false")
    return 0 if report["status"] == PRS_EDGE_PRIMARY_CANDIDATE_PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
