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
    PRS_SOURCE_PRODUCTION_ELIGIBILITY_PASS_STATUS,
    write_position_response_source_production_eligibility_bundle,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return (
        Path("tmp")
        / f"nodi_position_response_source_production_eligibility_{stamp}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate PRS source production eligibility using the edge_norm_1d "
            "primary / xz_norm_2d diagnostic-only policy. This writes preflight "
            "sidecars only; it does not generate production NODI_POSITION_RESPONSE_SURFACE "
            "rows, run NODI, run COMSOL, or regenerate JOINT_ROUTE_CLASS."
        )
    )
    parser.add_argument(
        "--confirm-production-eligibility-preflight",
        action="store_true",
        help="Confirm writing production-eligibility preflight sidecars.",
    )
    parser.add_argument(
        "--candidate",
        dest="candidates",
        action="append",
        type=Path,
        required=True,
        help="Candidate NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE CSV.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_production_eligibility_preflight:
        parser.error(
            "refusing to write eligibility sidecars without "
            "--confirm-production-eligibility-preflight"
        )

    report = write_position_response_source_production_eligibility_bundle(
        candidate_paths=args.candidates,
        output_dir=args.output_dir,
    )
    print(f"NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY: {report['status']}")
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report['report_sha256']}")
    print(f"candidate_csv: {report['candidate_csv']}")
    print(f"group_csv: {report['group_csv']}")
    print(f"blocker_csv: {report['blocker_csv']}")
    print(f"issue_csv: {report['issue_csv']}")
    print(f"eligible_candidate_count: {report['eligible_candidate_count']}")
    print("position_response_surface_production_generated: false")
    return 0 if report["status"] == PRS_SOURCE_PRODUCTION_ELIGIBILITY_PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
