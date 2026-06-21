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
    PRODUCTION_GENERATION_PARTIAL_STATUS,
    PRODUCTION_GENERATION_PASS_STATUS,
    write_production_generation_bundle,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("results/audits") / f"nodi_next_artifacts_production_generation_{stamp}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate authorized production generation for NODI/COMSOL next artifacts. "
            "The command writes production artifacts only when all required production "
            "inputs and selector policies are explicit; otherwise it writes blocker "
            "sidecars. It never runs COMSOL or regenerates JOINT_ROUTE_CLASS."
        )
    )
    parser.add_argument(
        "--confirm-production-generation",
        action="store_true",
        help="Confirm entering the production-generation gate.",
    )
    parser.add_argument(
        "--authorization-phrase",
        required=True,
        help="Exact production-generation authorization phrase supplied by the user.",
    )
    parser.add_argument(
        "--smoke-execution-report",
        type=Path,
        required=True,
        help="Bounded-smoke execution report JSON from the prior gate.",
    )
    parser.add_argument(
        "--geometry-descriptor",
        type=Path,
        required=True,
        help="COMSOL_GEOMETRY_DESCRIPTOR_V1 CSV staged locally.",
    )
    parser.add_argument(
        "--rank-source",
        type=Path,
        required=True,
        help="NODI fullgrid route-stability rank/proxy CSV.",
    )
    parser.add_argument(
        "--guardrail-table",
        type=Path,
        required=True,
        help="NODI guardrail table CSV.",
    )
    parser.add_argument(
        "--position-response-candidate",
        type=Path,
        default=None,
        help=(
            "Optional validated edge-primary NODI_POSITION_RESPONSE_SURFACE "
            "candidate CSV. When omitted, PRS remains blocked and only EAS can "
            "be written."
        ),
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_production_generation:
        parser.error(
            "refusing production-generation gate without "
            "--confirm-production-generation"
        )

    report = write_production_generation_bundle(
        smoke_execution_report_path=args.smoke_execution_report,
        geometry_descriptor_path=args.geometry_descriptor,
        rank_source_path=args.rank_source,
        guardrail_table_path=args.guardrail_table,
        position_response_candidate_path=args.position_response_candidate,
        authorization_phrase=args.authorization_phrase,
        output_dir=args.output_dir,
    )
    print(f"NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION: {report['status']}")
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report['report_sha256']}")
    print(f"blocker_csv: {report['blocker_csv']}")
    print(f"issue_csv: {report['issue_csv']}")
    for artifact in report["production_artifacts_generated"]:
        print(f"production_artifact: {artifact['path']}")
        print(f"production_artifact_sha256: {artifact['sha256']}")
    for blocker in report["blockers"]:
        print(f"- {blocker['artifact']}: {blocker['status']}")
    for issue in report["issues"]:
        print(f"- issue: {issue}")
    return (
        0
        if report["status"]
        in {PRODUCTION_GENERATION_PARTIAL_STATUS, PRODUCTION_GENERATION_PASS_STATUS}
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
