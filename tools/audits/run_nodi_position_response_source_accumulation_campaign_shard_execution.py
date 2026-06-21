#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_EVENTS_PER_JOB,
    PRS_SOURCE_PREFLIGHT_PASS_STATUS,
    PRS_SOURCE_PRODUCTION_SCOPE,
    PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS,
    PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
    build_position_response_bin_source_rows_from_events,
    validate_position_response_bin_source_event_rows,
    validate_position_response_bin_source_rows,
    validate_position_response_source_accumulation_campaign_runner_readiness_report,
    write_position_response_source_preflight_bundle,
    write_position_response_source_sufficiency_bundle,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)
from tools.audits.run_nodi_position_response_source_accumulation_bounded_shard import (  # noqa: E402
    _guard_output_paths,
    _run_bounded_job,
)


AUTHORIZATION_PHRASE = "authorize NODI PRS source accumulation campaign shard execution"
PASS_STATUS = "PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_EXECUTION_SLICE_NOT_PRODUCTION"
BLOCKED_STATUS = "BLOCKED_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_EXECUTION_SLICE"
REPORT_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_EXECUTION_REPORT_20260618.json"
)
EVENTS_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_EVENTS_20260618.csv"
)
SOURCE_FILENAME = (
    "NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_20260618.csv"
)
MANIFEST_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_EXECUTION_MANIFEST_20260618.csv"
)
ISSUES_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_EXECUTION_ISSUES_20260618.csv"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Execute a bounded campaign-shard slice from a runner-readiness report. "
            "This runs NODI for the selected shard jobs with a bounded event cap, "
            "writes bin-source sidecars, then runs availability/sufficiency gates. "
            "It does not generate production NODI_POSITION_RESPONSE_SURFACE rows, "
            "run COMSOL, or regenerate JOINT_ROUTE_CLASS."
        )
    )
    parser.add_argument(
        "--confirm-campaign-shard-execution",
        action="store_true",
        help="Confirm bounded campaign-shard execution slice.",
    )
    parser.add_argument(
        "--authorization-phrase",
        default=AUTHORIZATION_PHRASE,
        help="Exact campaign-shard execution authorization phrase to record.",
    )
    parser.add_argument(
        "--readiness-report",
        type=Path,
        required=True,
        help="Campaign runner-readiness report JSON.",
    )
    parser.add_argument(
        "--n-events-per-job",
        type=int,
        default=PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_EVENTS_PER_JOB,
        help=(
            "Bounded events to execute per selected job. This is capped by the "
            "existing bounded-shard event ceiling and is not the full campaign "
            "planned event count."
        ),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--overwrite-output",
        action="store_true",
        help="Allow replacing existing campaign-shard execution sidecars.",
    )
    return parser


def _read_readiness_report(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("readiness report must be a JSON object")
    issues = validate_position_response_source_accumulation_campaign_runner_readiness_report(
        loaded
    )
    if issues:
        raise ValueError("readiness report validation failed: " + "; ".join(issues))
    return loaded


def _selected_job_rows(readiness_report: dict[str, Any]) -> list[dict[str, Any]]:
    selected_schedule_rows = readiness_report["selected_campaign_job_schedule_rows"]
    if not isinstance(selected_schedule_rows, list) or not selected_schedule_rows:
        raise ValueError("readiness report has no selected campaign job schedule rows")
    job_plan_paths = {str(row["job_plan_path"]) for row in selected_schedule_rows}
    if len(job_plan_paths) != 1:
        raise ValueError("selected campaign jobs must share exactly one job_plan_path")
    job_plan_path = Path(next(iter(job_plan_paths)))
    job_plan_rows = read_csv_rows(job_plan_path)
    by_id = {str(row["job_id"]): dict(row) for row in job_plan_rows}
    selected: list[dict[str, Any]] = []
    missing: list[str] = []
    for schedule_row in selected_schedule_rows:
        source_job_id = str(schedule_row["source_job_id"])
        job_row = by_id.get(source_job_id)
        if job_row is None:
            missing.append(source_job_id)
            continue
        for field in ("route_id_nodi", "diameter_nm", "NODI_view", "seed"):
            if str(job_row.get(field, "")) != str(schedule_row.get(field, "")):
                raise ValueError(
                    f"job-plan row {source_job_id} does not match schedule field {field}"
                )
        selected.append(job_row)
    if missing:
        raise ValueError(f"selected source_job_id values missing from job plan: {missing}")
    return selected


def _manifest_rows(
    *,
    readiness_report: dict[str, Any],
    selected_job_rows: list[dict[str, Any]],
    n_events_per_job: int,
    event_path: Path,
    event_sha: str,
    source_path: Path,
    source_sha: str,
    source_availability_status: str,
    source_sufficiency_status: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    planned_total = 0
    executed_total = 0
    shard_id = str(readiness_report["selected_campaign_shard_id"])
    for index, job in enumerate(selected_job_rows, start=1):
        planned = int(float(str(job["n_events_requested_per_seed"])))
        planned_total += planned
        executed_total += int(n_events_per_job)
        rows.append(
            {
                "campaign_shard_execution_artifact_version": (
                    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_EXECUTION_SLICE_V1"
                ),
                "campaign_shard_id": shard_id,
                "execution_sequence": str(index),
                "source_job_id": str(job["job_id"]),
                "route_scope_class": str(job["route_scope_class"]),
                "route_id_nodi": str(job["route_id_nodi"]),
                "lambda_nm": str(job["lambda_nm"]),
                "W_nominal_nm": str(job["W_nominal_nm"]),
                "D_nm": str(job["D_nm"]),
                "diameter_nm": str(job["diameter_nm"]),
                "particle_name": str(job["particle_name"]),
                "NODI_view": str(job["NODI_view"]),
                "seed": str(job["seed"]),
                "source_scope": PRS_SOURCE_PRODUCTION_SCOPE,
                "planned_events_per_job": str(planned),
                "executed_events_per_job": str(int(n_events_per_job)),
                "full_planned_job_completed": str(planned == int(n_events_per_job)).lower(),
                "bounded_campaign_shard_slice": "true",
                "full_campaign_shard_completed": "false",
                "post_run_required_gate": PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
                "source_availability_status": source_availability_status,
                "source_numeric_sufficiency_status": source_sufficiency_status,
                "event_source_path": str(event_path),
                "event_source_sha256": event_sha,
                "bin_source_path": str(source_path),
                "bin_source_sha256": source_sha,
                "campaign_shard_execution_authorized": "true",
                "campaign_shard_execution_performed": "true",
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
    if rows:
        rows[0]["planned_campaign_shard_event_count"] = str(planned_total)
        rows[0]["executed_campaign_shard_event_count"] = str(executed_total)
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_campaign_shard_execution:
        parser.error(
            "refusing campaign-shard execution without "
            "--confirm-campaign-shard-execution"
        )
    if str(args.authorization_phrase) != AUTHORIZATION_PHRASE:
        parser.error("authorization phrase mismatch")
    if (
        args.n_events_per_job < 1
        or args.n_events_per_job > PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_EVENTS_PER_JOB
    ):
        parser.error(
            "--n-events-per-job must be between 1 and "
            f"{PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_EVENTS_PER_JOB}"
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
    event_rows: list[dict[str, Any]] = []
    for job in selected_jobs:
        event_rows.extend(
            _run_bounded_job(job, n_events_per_job=int(args.n_events_per_job))
        )
    event_issues = validate_position_response_bin_source_event_rows(event_rows)
    write_csv_rows(event_path, event_rows)
    event_sha = sha256_file(event_path)
    source_rows = build_position_response_bin_source_rows_from_events(
        event_rows,
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
    planned_events = sum(
        int(float(str(job["n_events_requested_per_seed"]))) for job in selected_jobs
    )
    executed_events = len(selected_jobs) * int(args.n_events_per_job)
    manifest_rows = _manifest_rows(
        readiness_report=readiness,
        selected_job_rows=selected_jobs,
        n_events_per_job=int(args.n_events_per_job),
        event_path=event_path,
        event_sha=event_sha,
        source_path=source_path,
        source_sha=source_sha,
        source_availability_status=source_availability_status,
        source_sufficiency_status=source_sufficiency_status,
    )
    issues = [
        *event_issues,
        *source_issues,
    ]
    if source_availability_status != PRS_SOURCE_PREFLIGHT_PASS_STATUS:
        issues.append("PRS-ACCUM-CAMPAIGN-SHARD: source availability did not pass")
    if source_sufficiency_status != PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS:
        issues.append(
            "PRS-ACCUM-CAMPAIGN-SHARD: bounded slice unexpectedly passed sufficiency"
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
            "nodi_position_response_source_accumulation_campaign_shard_execution_slice_v1"
        ),
        "status": status,
        "artifact": POSITION_RESPONSE_BIN_SOURCE_ARTIFACT,
        "downstream_artifact": POSITION_RESPONSE_ARTIFACT,
        "gate_role": "campaign_shard_execution_slice_not_production",
        "allowed_current_action": (
            "execute_campaign_shard_bounded_slice_sidecars_only"
        ),
        "authorization_phrase_exact_match": True,
        "readiness_report_path": str(args.readiness_report),
        "readiness_report_sha256": sha256_file(args.readiness_report),
        "selected_campaign_shard_id": readiness["selected_campaign_shard_id"],
        "selected_job_count": len(selected_jobs),
        "planned_events_per_job_from_schedule": (
            int(float(str(selected_jobs[0]["n_events_requested_per_seed"])))
            if selected_jobs
            else 0
        ),
        "executed_events_per_job": int(args.n_events_per_job),
        "planned_campaign_shard_event_count": planned_events,
        "executed_campaign_shard_event_count": executed_events,
        "full_campaign_shard_completed": False,
        "bounded_campaign_shard_slice": True,
        "event_rows": len(event_rows),
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
        "campaign_shard_execution_authorized": True,
        "campaign_shard_execution_performed": status == PASS_STATUS,
        "nodi_campaign_shard_slice_run_performed": status == PASS_STATUS,
        "full_runner_execution_authorized": False,
        "full_runner_execution_performed": False,
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
        "stop_reason": "campaign_shard_bounded_slice_written_numeric_sufficiency_blocked",
        "elapsed_s": time.perf_counter() - started,
    }
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    write_json_atomic(report_path, report, sort_keys=True)
    report_sha256 = sha256_file(report_path)
    print(f"NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_EXECUTION: {status}")
    print(f"selected_campaign_shard_id: {report['selected_campaign_shard_id']}")
    print(f"selected_job_count: {report['selected_job_count']}")
    print(f"planned_campaign_shard_event_count: {planned_events}")
    print(f"executed_campaign_shard_event_count: {executed_events}")
    print(f"event_rows: {report['event_rows']}")
    print(f"bin_source_rows: {report['bin_source_rows']}")
    print(f"source_availability_status: {source_availability_status}")
    print(f"source_numeric_sufficiency_status: {source_sufficiency_status}")
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report_sha256}")
    for issue in issues:
        print(f"- issue: {issue}")
    return 0 if status == PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
