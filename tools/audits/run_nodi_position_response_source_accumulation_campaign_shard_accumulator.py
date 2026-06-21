#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.nodi_comsol_next_artifacts import (  # noqa: E402
    POSITION_RESPONSE_ARTIFACT,
    POSITION_RESPONSE_BIN_SOURCE_ARTIFACT,
    PRS_BIN_SOURCE_CLAIM_BOUNDARY,
    PRS_CLAIM_BOUNDARY,
    PRS_SOURCE_PREFLIGHT_PASS_STATUS,
    PRS_SOURCE_PRODUCTION_SCOPE,
    PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS,
    PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
    build_position_response_bin_source_rows_from_events,
    validate_position_response_bin_source_event_rows,
    validate_position_response_bin_source_rows,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)
from tools.audits.run_nodi_position_response_source_accumulation_campaign_shard_execution import (  # noqa: E402
    AUTHORIZATION_PHRASE,
    _read_readiness_report,
    _selected_job_rows,
)
from tools.audits.run_nodi_position_response_source_accumulation_bounded_shard import (  # noqa: E402
    _guard_output_paths,
    _run_bounded_job,
)
from nodi_simulator.nodi_comsol_next_artifacts import (  # noqa: E402
    write_position_response_source_preflight_bundle,
    write_position_response_source_sufficiency_bundle,
)


PASS_STATUS = "PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_NOT_PRODUCTION"
BLOCKED_STATUS = "BLOCKED_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR"
MAX_EVENTS_PER_JOB_PER_CHUNK = 2000
REPORT_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_REPORT_20260618.json"
)
EVENTS_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_EVENTS_20260618.csv"
)
SOURCE_FILENAME = (
    "NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_20260618.csv"
)
MANIFEST_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_MANIFEST_20260618.csv"
)
ISSUES_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_ISSUES_20260618.csv"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Append one bounded execution chunk to a PRS campaign shard event set, "
            "then rebuild accumulated bin-source sidecars and post-run gates. This "
            "does not generate production NODI_POSITION_RESPONSE_SURFACE rows, run "
            "COMSOL, or regenerate JOINT_ROUTE_CLASS."
        )
    )
    parser.add_argument(
        "--confirm-accumulate-campaign-shard",
        action="store_true",
        help="Confirm appending one campaign-shard accumulation chunk.",
    )
    parser.add_argument(
        "--authorization-phrase",
        default=AUTHORIZATION_PHRASE,
        help="Exact campaign-shard execution authorization phrase to record.",
    )
    parser.add_argument("--readiness-report", type=Path, required=True)
    parser.add_argument(
        "--previous-events",
        type=Path,
        required=True,
        help="Existing campaign-shard event CSV to extend.",
    )
    parser.add_argument(
        "--chunk-id",
        required=True,
        help="Stable chunk id embedded into new event ids, e.g. chunk002.",
    )
    parser.add_argument(
        "--n-events-per-job",
        type=int,
        default=100,
        help=f"Events per selected job for this chunk, max {MAX_EVENTS_PER_JOB_PER_CHUNK}.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--overwrite-output", action="store_true")
    return parser


def _prefix_chunk_event_ids(rows: list[dict[str, Any]], *, chunk_id: str) -> None:
    for row in rows:
        row["event_id"] = f"{chunk_id}_{row['event_id']}"
        row["accumulation_chunk_id"] = chunk_id


def _manifest_rows(
    *,
    readiness: dict[str, Any],
    selected_jobs: list[dict[str, Any]],
    previous_event_count: int,
    chunk_event_count: int,
    accumulated_event_count: int,
    chunk_events_per_job: int,
    event_path: Path,
    event_sha: str,
    source_path: Path,
    source_sha: str,
    source_availability_status: str,
    source_sufficiency_status: str,
) -> list[dict[str, str]]:
    planned_total = sum(
        int(float(str(job["n_events_requested_per_seed"]))) for job in selected_jobs
    )
    rows: list[dict[str, str]] = []
    for index, job in enumerate(selected_jobs, start=1):
        planned = int(float(str(job["n_events_requested_per_seed"])))
        rows.append(
            {
                "campaign_shard_accumulator_artifact_version": (
                    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_V1"
                ),
                "campaign_shard_id": str(readiness["selected_campaign_shard_id"]),
                "execution_sequence": str(index),
                "source_job_id": str(job["job_id"]),
                "route_id_nodi": str(job["route_id_nodi"]),
                "diameter_nm": str(job["diameter_nm"]),
                "NODI_view": str(job["NODI_view"]),
                "seed": str(job["seed"]),
                "planned_events_per_job": str(planned),
                "chunk_events_per_job": str(int(chunk_events_per_job)),
                "previous_event_count_total": str(int(previous_event_count)),
                "chunk_event_count_total": str(int(chunk_event_count)),
                "accumulated_event_count_total": str(int(accumulated_event_count)),
                "planned_campaign_shard_event_count": str(planned_total),
                "full_campaign_shard_completed": str(
                    accumulated_event_count >= planned_total
                ).lower(),
                "campaign_shard_accumulator_slice": "true",
                "post_run_required_gate": PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
                "source_availability_status": source_availability_status,
                "source_numeric_sufficiency_status": source_sufficiency_status,
                "event_source_path": str(event_path),
                "event_source_sha256": event_sha,
                "bin_source_path": str(source_path),
                "bin_source_sha256": source_sha,
                "position_response_surface_production_generated": "false",
                "production_generation_performed": "false",
                "comsol_run_performed": "false",
                "joint_route_class_regenerated": "false",
                "production_prs_generated": "false",
                "not_qch_weighted": "true",
                "not_yield": "true",
                "not_winner": "true",
                "not_detection_probability": "true",
                "not_true_W_eff": "true",
                "not_measured_geometry": "true",
                "not_optical_solver_output": "true",
                "not_fabrication_release": "true",
                "not_P3_solver_conclusion": "true",
                "claim_boundary": PRS_BIN_SOURCE_CLAIM_BOUNDARY,
                "downstream_claim_boundary": PRS_CLAIM_BOUNDARY,
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_accumulate_campaign_shard:
        parser.error(
            "refusing campaign-shard accumulation without "
            "--confirm-accumulate-campaign-shard"
        )
    if str(args.authorization_phrase) != AUTHORIZATION_PHRASE:
        parser.error("authorization phrase mismatch")
    if args.n_events_per_job < 1 or args.n_events_per_job > MAX_EVENTS_PER_JOB_PER_CHUNK:
        parser.error(
            "--n-events-per-job must be between 1 and "
            f"{MAX_EVENTS_PER_JOB_PER_CHUNK}"
        )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    event_path = output_dir / EVENTS_FILENAME
    source_path = output_dir / SOURCE_FILENAME
    manifest_path = output_dir / MANIFEST_FILENAME
    issue_path = output_dir / ISSUES_FILENAME
    report_path = output_dir / REPORT_FILENAME
    _guard_output_paths(
        [event_path, source_path, manifest_path, issue_path, report_path],
        allow_overwrite=bool(args.overwrite_output),
    )

    started = time.perf_counter()
    readiness = _read_readiness_report(args.readiness_report)
    selected_jobs = _selected_job_rows(readiness)
    previous_events = read_csv_rows(args.previous_events)
    previous_issues = validate_position_response_bin_source_event_rows(previous_events)

    chunk_events: list[dict[str, Any]] = []
    for job in selected_jobs:
        chunk_events.extend(
            _run_bounded_job(job, n_events_per_job=int(args.n_events_per_job))
        )
    _prefix_chunk_event_ids(chunk_events, chunk_id=str(args.chunk_id))
    chunk_issues = validate_position_response_bin_source_event_rows(chunk_events)
    accumulated_events = [*previous_events, *chunk_events]
    accumulated_issues = validate_position_response_bin_source_event_rows(
        accumulated_events
    )
    write_csv_rows(event_path, accumulated_events)
    event_sha = sha256_file(event_path)
    source_rows = build_position_response_bin_source_rows_from_events(
        accumulated_events,
        source_scope=PRS_SOURCE_PRODUCTION_SCOPE,
        source_artifact=str(event_path),
        source_sha256=event_sha,
    )
    source_issues = validate_position_response_bin_source_rows(source_rows)
    write_csv_rows(source_path, source_rows)
    source_sha = sha256_file(source_path)
    source_availability = write_position_response_source_preflight_bundle(
        candidate_paths=[source_path],
        output_dir=output_dir,
    )
    source_sufficiency = write_position_response_source_sufficiency_bundle(
        candidate_paths=[source_path],
        output_dir=output_dir,
    )
    source_availability_status = str(source_availability.get("status", ""))
    source_sufficiency_status = str(source_sufficiency.get("status", ""))
    manifest_rows = _manifest_rows(
        readiness=readiness,
        selected_jobs=selected_jobs,
        previous_event_count=len(previous_events),
        chunk_event_count=len(chunk_events),
        accumulated_event_count=len(accumulated_events),
        chunk_events_per_job=int(args.n_events_per_job),
        event_path=event_path,
        event_sha=event_sha,
        source_path=source_path,
        source_sha=source_sha,
        source_availability_status=source_availability_status,
        source_sufficiency_status=source_sufficiency_status,
    )
    issues = [
        *previous_issues,
        *chunk_issues,
        *accumulated_issues,
        *source_issues,
    ]
    planned_total = sum(
        int(float(str(job["n_events_requested_per_seed"]))) for job in selected_jobs
    )
    full_campaign_shard_completed = len(accumulated_events) >= planned_total
    if source_availability_status != PRS_SOURCE_PREFLIGHT_PASS_STATUS:
        issues.append("PRS-ACCUM-CAMPAIGN-ACCUM: source availability did not pass")
    if (
        not full_campaign_shard_completed
        and source_sufficiency_status != PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS
    ):
        issues.append(
            "PRS-ACCUM-CAMPAIGN-ACCUM: partial accumulation unexpectedly passed sufficiency"
        )
    if full_campaign_shard_completed and source_sufficiency_status not in {
        PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS,
        PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
    }:
        issues.append(
            "PRS-ACCUM-CAMPAIGN-ACCUM: completed shard has invalid sufficiency status"
        )
    status = PASS_STATUS if not issues else BLOCKED_STATUS
    issue_rows = [
        {"issue_index": index, "issue": issue}
        for index, issue in enumerate(issues, start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    write_csv_rows(issue_path, issue_rows)
    write_csv_rows(manifest_path, manifest_rows)
    report: dict[str, Any] = {
        "schema_version": (
            "nodi_position_response_source_accumulation_campaign_shard_accumulator_v1"
        ),
        "status": status,
        "artifact": POSITION_RESPONSE_BIN_SOURCE_ARTIFACT,
        "downstream_artifact": POSITION_RESPONSE_ARTIFACT,
        "allowed_current_action": "accumulate_campaign_shard_event_chunk_sidecars_only",
        "authorization_phrase_exact_match": True,
        "readiness_report_path": str(args.readiness_report),
        "readiness_report_sha256": sha256_file(args.readiness_report),
        "previous_events_path": str(args.previous_events),
        "previous_events_sha256": sha256_file(args.previous_events),
        "chunk_id": str(args.chunk_id),
        "selected_campaign_shard_id": readiness["selected_campaign_shard_id"],
        "selected_job_count": len(selected_jobs),
        "chunk_events_per_job": int(args.n_events_per_job),
        "previous_event_count": len(previous_events),
        "chunk_event_count": len(chunk_events),
        "accumulated_event_count": len(accumulated_events),
        "planned_campaign_shard_event_count": planned_total,
        "full_campaign_shard_completed": full_campaign_shard_completed,
        "campaign_shard_accumulator_slice": True,
        "bin_source_rows": len(source_rows),
        "event_source_path": str(event_path),
        "event_source_sha256": event_sha,
        "bin_source_path": str(source_path),
        "bin_source_sha256": source_sha,
        "manifest_csv": str(manifest_path),
        "manifest_csv_sha256": sha256_file(manifest_path),
        "issue_csv": str(issue_path),
        "issue_csv_sha256": sha256_file(issue_path),
        "source_availability_status": source_availability_status,
        "source_availability_report_path": str(source_availability.get("report_path", "")),
        "source_availability_report_sha256": str(
            source_availability.get("report_sha256", "")
        ),
        "source_numeric_sufficiency_status": source_sufficiency_status,
        "source_numeric_sufficiency_report_path": str(
            source_sufficiency.get("report_path", "")
        ),
        "source_numeric_sufficiency_report_sha256": str(
            source_sufficiency.get("report_sha256", "")
        ),
        "numeric_sufficient_candidate_count": source_sufficiency.get(
            "numeric_sufficient_candidate_count",
            0,
        ),
        "post_run_required_gate": PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
        "numeric_sufficiency_pass_action": "stop_for_review_not_auto_production_prs",
        "issues": issues,
        "position_response_surface_production_generated": False,
        "production_generation_performed": False,
        "comsol_run_performed": False,
        "joint_route_class_regenerated": False,
        "no_prs_production_artifact": True,
        "no_comsol_run": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_detection_probability": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "claim_boundary": PRS_BIN_SOURCE_CLAIM_BOUNDARY,
        "downstream_claim_boundary": PRS_CLAIM_BOUNDARY,
        "stop_reason": (
            "campaign_shard_completed_numeric_sufficiency_passed_stop_for_review"
            if full_campaign_shard_completed
            and source_sufficiency_status == PRS_SOURCE_SUFFICIENCY_PASS_STATUS
            else "campaign_shard_accumulated_slice_numeric_sufficiency_blocked"
        ),
        "elapsed_s": time.perf_counter() - started,
    }
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    write_json_atomic(report_path, report, sort_keys=True)
    report_sha = sha256_file(report_path)
    print(f"NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR: {status}")
    print(f"selected_campaign_shard_id: {report['selected_campaign_shard_id']}")
    print(f"chunk_id: {report['chunk_id']}")
    print(f"selected_job_count: {report['selected_job_count']}")
    print(f"previous_event_count: {report['previous_event_count']}")
    print(f"chunk_event_count: {report['chunk_event_count']}")
    print(f"accumulated_event_count: {report['accumulated_event_count']}")
    print(f"planned_campaign_shard_event_count: {planned_total}")
    print(f"bin_source_rows: {report['bin_source_rows']}")
    print(f"source_availability_status: {source_availability_status}")
    print(f"source_numeric_sufficiency_status: {source_sufficiency_status}")
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report_sha}")
    for issue in issues:
        print(f"- issue: {issue}")
    return 0 if status == PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
