#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_next_artifacts import (
    FUTURE_AUTHORIZATION_PHRASE_MATCH_RUNNER_IMPLEMENTATION,
    evaluate_next_artifacts_future_authorization_request,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check a future NODI/COMSOL next-artifacts authorization phrase. "
            "This is a read-only guard check and does not implement runners, execute "
            "smoke, run NODI/COMSOL, or generate production artifacts."
        )
    )
    parser.add_argument(
        "--requested-action",
        required=True,
        choices=("runner_implementation", "bounded_smoke_execution", "production_generation"),
    )
    parser.add_argument(
        "--supplied-phrase",
        required=True,
        help="Candidate phrase to check for exact match. It is not written to disk.",
    )
    parser.add_argument(
        "--gate-record",
        type=Path,
        help="Optional gate record JSON to validate while checking the phrase.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    gate_record = None
    if args.gate_record is not None:
        gate_record = json.loads(args.gate_record.read_text(encoding="utf-8"))
    result = evaluate_next_artifacts_future_authorization_request(
        requested_action=args.requested_action,
        supplied_phrase=args.supplied_phrase,
        gate_record=gate_record,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return (
        0
        if result["authorization_request_status"]
        == FUTURE_AUTHORIZATION_PHRASE_MATCH_RUNNER_IMPLEMENTATION
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
