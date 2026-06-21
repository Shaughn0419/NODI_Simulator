#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import (  # noqa: E402
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)
from tools.audits.run_nodi_position_response_source_accumulation_campaign_shard_accumulator import (  # noqa: E402
    EVENTS_FILENAME,
    MAX_EVENTS_PER_JOB_PER_CHUNK,
    PASS_STATUS as ACCUMULATOR_PASS_STATUS,
    REPORT_FILENAME as ACCUMULATOR_REPORT_FILENAME,
)
from tools.audits.run_nodi_position_response_source_accumulation_campaign_shard_execution import (  # noqa: E402
    AUTHORIZATION_PHRASE,
)


BATCH_PASS_STATUS = (
    "PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH_NOT_PRODUCTION"
)
BATCH_BLOCKED_STATUS = (
    "BLOCKED_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH"
)
BATCH_REPORT_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH_REPORT_20260618.json"
)
BATCH_MANIFEST_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH_MANIFEST_20260618.csv"
)
BATCH_ISSUES_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH_ISSUES_20260618.csv"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run multiple PRS campaign-shard accumulator chunks sequentially. "
            "Each chunk is a checkpointed non-production sidecar write. The batch "
            "does not generate production NODI_POSITION_RESPONSE_SURFACE rows, "
            "run COMSOL, or regenerate JOINT_ROUTE_CLASS."
        )
    )
    parser.add_argument(
        "--confirm-accumulator-batch",
        action="store_true",
        help="Confirm sequential non-production accumulator batch execution.",
    )
    parser.add_argument(
        "--authorization-phrase",
        default=AUTHORIZATION_PHRASE,
        help="Exact campaign-shard execution authorization phrase to record.",
    )
    parser.add_argument("--readiness-report", type=Path, required=True)
    parser.add_argument(
        "--initial-events",
        type=Path,
        required=True,
        help="Event CSV used as the first previous-events input.",
    )
    parser.add_argument("--start-chunk-index", type=int, required=True)
    parser.add_argument("--chunk-count", type=int, required=True)
    parser.add_argument(
        "--n-events-per-job",
        type=int,
        default=MAX_EVENTS_PER_JOB_PER_CHUNK,
        help=f"Events per selected job for each chunk, max {MAX_EVENTS_PER_JOB_PER_CHUNK}.",
    )
    parser.add_argument("--output-parent", type=Path, default=Path("tmp"))
    parser.add_argument(
        "--chunk-dir-prefix",
        default="nodi_position_response_source_accumulation_campaign_shard_accumulator",
    )
    parser.add_argument("--batch-output-dir", type=Path, required=True)
    parser.add_argument("--overwrite-output", action="store_true")
    return parser


def _chunk_id(index: int) -> str:
    return f"chunk{index:03d}"


def _chunk_output_dir(output_parent: Path, prefix: str, chunk_id: str) -> Path:
    return output_parent / f"{prefix}_{chunk_id}_20260618"


def _run_chunk(
    *,
    readiness_report: Path,
    previous_events: Path,
    chunk_id: str,
    n_events_per_job: int,
    output_dir: Path,
    overwrite_output: bool,
) -> tuple[int, str, str]:
    cmd = [
        sys.executable,
        str(
            PROJECT_ROOT
            / "tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator.py"
        ),
        "--confirm-accumulate-campaign-shard",
        "--authorization-phrase",
        AUTHORIZATION_PHRASE,
        "--readiness-report",
        str(readiness_report),
        "--previous-events",
        str(previous_events),
        "--chunk-id",
        chunk_id,
        "--n-events-per-job",
        str(int(n_events_per_job)),
        "--output-dir",
        str(output_dir),
    ]
    if overwrite_output:
        cmd.append("--overwrite-output")
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def _read_chunk_report(output_dir: Path) -> dict[str, Any]:
    report_path = output_dir / ACCUMULATOR_REPORT_FILENAME
    loaded = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"chunk report is not an object: {report_path}")
    return dict(loaded)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_accumulator_batch:
        parser.error("refusing accumulator batch without --confirm-accumulator-batch")
    if str(args.authorization_phrase) != AUTHORIZATION_PHRASE:
        parser.error("authorization phrase mismatch")
    if args.start_chunk_index < 1:
        parser.error("--start-chunk-index must be positive")
    if args.chunk_count < 1 or args.chunk_count > 25:
        parser.error("--chunk-count must be between 1 and 25")
    if args.n_events_per_job < 1 or args.n_events_per_job > MAX_EVENTS_PER_JOB_PER_CHUNK:
        parser.error(
            "--n-events-per-job must be between 1 and "
            f"{MAX_EVENTS_PER_JOB_PER_CHUNK}"
        )

    batch_output_dir = Path(args.batch_output_dir)
    batch_output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    previous_events = Path(args.initial_events)
    chunk_rows: list[dict[str, Any]] = []
    issues: list[str] = []

    for chunk_index in range(
        int(args.start_chunk_index),
        int(args.start_chunk_index) + int(args.chunk_count),
    ):
        chunk = _chunk_id(chunk_index)
        output_dir = _chunk_output_dir(
            Path(args.output_parent),
            str(args.chunk_dir_prefix),
            chunk,
        )
        returncode, stdout, stderr = _run_chunk(
            readiness_report=Path(args.readiness_report),
            previous_events=previous_events,
            chunk_id=chunk,
            n_events_per_job=int(args.n_events_per_job),
            output_dir=output_dir,
            overwrite_output=bool(args.overwrite_output),
        )
        chunk_report: dict[str, Any] = {}
        chunk_report_path = output_dir / ACCUMULATOR_REPORT_FILENAME
        if chunk_report_path.exists():
            chunk_report = _read_chunk_report(output_dir)
        if returncode != 0:
            issues.append(f"{chunk}: accumulator returncode={returncode}")
        if stderr.strip():
            issues.append(f"{chunk}: stderr={stderr.strip()}")
        if chunk_report and chunk_report.get("status") != ACCUMULATOR_PASS_STATUS:
            issues.append(f"{chunk}: status={chunk_report.get('status')}")
        chunk_rows.append(
            {
                "chunk_id": chunk,
                "returncode": returncode,
                "status": chunk_report.get("status", ""),
                "output_dir": str(output_dir),
                "report_path": str(chunk_report_path) if chunk_report_path.exists() else "",
                "report_sha256": sha256_file(chunk_report_path)
                if chunk_report_path.exists()
                else "",
                "previous_event_count": chunk_report.get("previous_event_count", ""),
                "chunk_event_count": chunk_report.get("chunk_event_count", ""),
                "accumulated_event_count": chunk_report.get("accumulated_event_count", ""),
                "planned_campaign_shard_event_count": chunk_report.get(
                    "planned_campaign_shard_event_count",
                    "",
                ),
                "source_availability_status": chunk_report.get(
                    "source_availability_status",
                    "",
                ),
                "source_numeric_sufficiency_status": chunk_report.get(
                    "source_numeric_sufficiency_status",
                    "",
                ),
                "position_response_surface_production_generated": str(
                    chunk_report.get("position_response_surface_production_generated", "")
                ).lower(),
                "comsol_run_performed": str(chunk_report.get("comsol_run_performed", "")).lower(),
                "joint_route_class_regenerated": str(
                    chunk_report.get("joint_route_class_regenerated", "")
                ).lower(),
                "stdout_tail": "\n".join(stdout.strip().splitlines()[-6:]),
            }
        )
        if issues:
            break
        previous_events = output_dir / EVENTS_FILENAME

    manifest_path = batch_output_dir / BATCH_MANIFEST_FILENAME
    write_csv_rows(manifest_path, chunk_rows or [{"chunk_id": "", "status": ""}])
    issue_rows = [
        {"issue_index": index, "issue": issue}
        for index, issue in enumerate(issues, start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    issue_path = batch_output_dir / BATCH_ISSUES_FILENAME
    write_csv_rows(issue_path, issue_rows)
    status = BATCH_PASS_STATUS if not issues else BATCH_BLOCKED_STATUS
    final_chunk = chunk_rows[-1] if chunk_rows else {}
    final_output_dir = Path(str(final_chunk.get("output_dir", ""))) if final_chunk else Path()
    final_events = final_output_dir / EVENTS_FILENAME if final_output_dir else Path()
    report: dict[str, Any] = {
        "schema_version": (
            "nodi_position_response_source_accumulation_campaign_shard_accumulator_batch_v1"
        ),
        "status": status,
        "allowed_current_action": "run_sequential_accumulator_chunks_sidecars_only",
        "authorization_phrase_exact_match": True,
        "readiness_report_path": str(args.readiness_report),
        "readiness_report_sha256": sha256_file(Path(args.readiness_report)),
        "initial_events_path": str(args.initial_events),
        "initial_events_sha256": sha256_file(Path(args.initial_events)),
        "start_chunk_index": int(args.start_chunk_index),
        "requested_chunk_count": int(args.chunk_count),
        "completed_chunk_count": sum(
            1 for row in chunk_rows if row.get("status") == ACCUMULATOR_PASS_STATUS
        ),
        "n_events_per_job": int(args.n_events_per_job),
        "final_events_path": str(final_events) if final_events.exists() else "",
        "final_events_sha256": sha256_file(final_events) if final_events.exists() else "",
        "final_accumulated_event_count": final_chunk.get("accumulated_event_count", ""),
        "final_planned_campaign_shard_event_count": final_chunk.get(
            "planned_campaign_shard_event_count",
            "",
        ),
        "chunk_rows": chunk_rows,
        "manifest_csv": str(manifest_path),
        "manifest_csv_sha256": sha256_file(manifest_path),
        "issue_csv": str(issue_path),
        "issue_csv_sha256": sha256_file(issue_path),
        "issues": issues,
        "position_response_surface_production_generated": False,
        "production_generation_performed": False,
        "comsol_run_performed": False,
        "joint_route_class_regenerated": False,
        "no_prs_production_artifact": True,
        "no_comsol_run": True,
        "no_joint_route_class_regeneration": True,
        "stop_reason": "batch_completed_nonproduction_accumulator_chunks"
        if not issues
        else "batch_stopped_on_first_accumulator_issue",
        "elapsed_s": time.perf_counter() - started,
    }
    report_path = batch_output_dir / BATCH_REPORT_FILENAME
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    write_json_atomic(report_path, report, sort_keys=True)
    report_sha = sha256_file(report_path)
    print(f"NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH: {status}")
    print(f"completed_chunk_count: {report['completed_chunk_count']}")
    print(f"final_accumulated_event_count: {report['final_accumulated_event_count']}")
    print(f"final_events_path: {report['final_events_path']}")
    print(f"report_path: {report_path}")
    print(f"report_sha256: {report_sha}")
    for issue in issues:
        print(f"- issue: {issue}")
    return 0 if status == BATCH_PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
