#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import copy
from datetime import datetime
from pathlib import Path
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.config import (  # noqa: E402
    THETA_GRID_RAD,
    infer_particle_diameter_nm,
    medium_for_particle,
    particle_from_name,
)
from nodi_simulator.nodi_comsol_next_artifacts import (  # noqa: E402
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_AUTHORIZATION_PHRASE,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_BLOCKED_STATUS,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_DEFAULT_EVENTS_PER_JOB,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_DEFAULT_MAX_JOBS,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_EVENTS_FILENAME,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MANIFEST_FILENAME,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_EVENTS_PER_JOB,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_JOBS,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_PASS_STATUS,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_REPORT_FILENAME,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_SOURCE_FILENAME,
    PRS_SOURCE_PRODUCTION_SCOPE,
    build_position_response_bin_source_rows_from_events,
    build_position_response_event_rows_from_nodi_events,
    build_position_response_source_accumulation_bounded_shard_report,
    select_position_response_source_accumulation_bounded_shard_jobs,
    validate_position_response_bin_source_event_rows,
    validate_position_response_bin_source_rows,
    write_position_response_source_accumulation_bounded_shard_sidecars,
    write_position_response_source_preflight_bundle,
    write_position_response_source_sufficiency_bundle,
)
from nodi_simulator.parameter_sweep import run_single_case_batch  # noqa: E402
from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
)
from tools.audits import tsuyama_gold_aligned_detection_lane as lane  # noqa: E402
from tools.audits.run_nodi_position_response_runner_slice_source_export import (  # noqa: E402
    _resolve_e_sca_ref,
    validate_route_source_slice,
)
from tools.lens_b_ev_gold_fullgrid_runner import (  # noqa: E402
    SINGLE_NORMALIZATION_LANES,
    build_frozen_b_cfg,
    _cfg_for_normalization_lane,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return (
        Path("results/audits")
        / f"nodi_position_response_source_accumulation_bounded_shard_{stamp}"
    )


def _guard_output_paths(paths: list[Path], *, allow_overwrite: bool) -> None:
    existing = [str(path) for path in paths if path.exists()]
    if existing and not allow_overwrite:
        joined = "\n  - ".join(existing)
        raise FileExistsError(
            "refusing to overwrite existing bounded-shard outputs; pass "
            "--overwrite-output only after confirming this is intentional:\n  - "
            + joined
        )
    for path in paths:
        if path.exists():
            path.unlink()


def _route_from_job(row: dict[str, Any]) -> tuple[int, int, int]:
    return (
        int(float(str(row["lambda_nm"]))),
        int(float(str(row["W_nominal_nm"]))),
        int(float(str(row["D_nm"]))),
    )


def _run_bounded_job(
    job: dict[str, Any],
    *,
    n_events_per_job: int,
) -> list[dict[str, Any]]:
    route = _route_from_job(job)
    wavelength_nm, width_nm, depth_nm = route
    particle_name = str(job["particle_name"])
    diameter_nm = int(float(str(job["diameter_nm"])))
    view = str(job["NODI_view"])
    seed = int(float(str(job["seed"])))
    route_source_path = Path(str(job["route_source_path"]))
    validate_route_source_slice(
        route_source_path,
        route=route,
        particle_name=particle_name,
        particle_scope="ev_gold",
    )

    particle = particle_from_name(particle_name)
    inferred_diameter = infer_particle_diameter_nm(particle_name)
    if inferred_diameter is not None and int(inferred_diameter) != diameter_nm:
        raise ValueError(
            f"particle diameter mismatch for {particle_name}: "
            f"job={diameter_nm}, inferred={inferred_diameter}"
        )

    base_cfg, optical_template = build_frozen_b_cfg(n_events_per_job, seed)
    cfg = _cfg_for_normalization_lane(base_cfg, view)
    optical = copy(optical_template)
    optical.wavelength_m = float(wavelength_nm) * 1e-9
    channel = lane.case_baseline_channel(width_nm, depth_nm)
    e_sca_ref = _resolve_e_sca_ref(
        view=view,
        route=route,
        particle=particle,
        cfg=cfg,
        optical_template=optical_template,
    )
    batch = run_single_case_batch(
        particle,
        medium_for_particle(particle),
        channel,
        optical,
        cfg,
        e_sca_ref,
        THETA_GRID_RAD,
        retain_event_traces=False,
        stream_summary_only=False,
    )
    return build_position_response_event_rows_from_nodi_events(
        batch["events"],
        route=route,
        diameter_nm=diameter_nm,
        view=view,
        seed=seed,
        particle_kind=particle_name,
        source_scope=PRS_SOURCE_PRODUCTION_SCOPE,
        event_id_prefix=(
            f"accum_shard_{wavelength_nm}_W{width_nm}_D{depth_nm}_"
            f"D{diameter_nm}_{view}_seed{seed}"
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Execute a tiny bounded shard from a PRS source-accumulation job "
            "plan and write source sidecars only. This never generates "
            "production NODI_POSITION_RESPONSE_SURFACE rows, runs COMSOL, "
            "regenerates JOINT_ROUTE_CLASS, or treats sparse bounded output as "
            "numeric sufficiency."
        ),
        epilog=(
            "Sidecars include: "
            f"{PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_EVENTS_FILENAME}, "
            f"{PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_SOURCE_FILENAME}, "
            f"{PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MANIFEST_FILENAME}, "
            f"{PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_REPORT_FILENAME}."
        ),
    )
    parser.add_argument(
        "--confirm-bounded-shard-execution",
        action="store_true",
        help="Confirm running the bounded source-accumulation shard.",
    )
    parser.add_argument(
        "--authorization-phrase",
        default=PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_AUTHORIZATION_PHRASE,
        help="Exact bounded-shard authorization phrase to record.",
    )
    parser.add_argument(
        "--job-plan",
        type=Path,
        required=True,
        help="PRS source accumulation job-plan CSV from Report 174.",
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_DEFAULT_MAX_JOBS,
        help="Tiny bounded shard size; hard-capped by the contract.",
    )
    parser.add_argument(
        "--n-events-per-job",
        type=int,
        default=PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_DEFAULT_EVENTS_PER_JOB,
        help="Tiny event count per selected job; hard-capped by the contract.",
    )
    parser.add_argument(
        "--NODI-view-filter",
        choices=SINGLE_NORMALIZATION_LANES,
        help="Optionally restrict selected jobs to one NODI view.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    parser.add_argument(
        "--overwrite-output",
        action="store_true",
        help="Allow replacing existing bounded-shard sidecars in the output directory.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_bounded_shard_execution:
        parser.error(
            "refusing PRS source accumulation bounded shard without "
            "--confirm-bounded-shard-execution"
        )
    if args.max_jobs < 1 or args.max_jobs > PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_JOBS:
        parser.error(
            "--max-jobs must be between 1 and "
            f"{PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_JOBS}"
        )
    if (
        args.n_events_per_job < 1
        or args.n_events_per_job
        > PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_EVENTS_PER_JOB
    ):
        parser.error(
            "--n-events-per-job must be between 1 and "
            f"{PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_EVENTS_PER_JOB}"
        )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    event_path = output_dir / PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_EVENTS_FILENAME
    source_path = output_dir / PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_SOURCE_FILENAME
    report_path = output_dir / PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_REPORT_FILENAME
    manifest_path = output_dir / PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MANIFEST_FILENAME
    _guard_output_paths(
        [event_path, source_path, report_path, manifest_path],
        allow_overwrite=bool(args.overwrite_output),
    )

    job_rows = read_csv_rows(args.job_plan)
    if args.NODI_view_filter:
        job_rows = [
            row
            for row in job_rows
            if str(row.get("NODI_view", "")) == str(args.NODI_view_filter)
        ]
    selected_jobs = select_position_response_source_accumulation_bounded_shard_jobs(
        job_rows,
        max_jobs=int(args.max_jobs),
    )

    started = time.perf_counter()
    event_rows: list[dict[str, Any]] = []
    for job in selected_jobs:
        event_rows.extend(
            _run_bounded_job(
                job,
                n_events_per_job=int(args.n_events_per_job),
            )
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

    report = build_position_response_source_accumulation_bounded_shard_report(
        authorization_phrase=str(args.authorization_phrase),
        job_plan_path=args.job_plan,
        job_plan_sha256=sha256_file(args.job_plan),
        selected_job_rows=selected_jobs,
        n_events_per_job=int(args.n_events_per_job),
        event_source_path=event_path,
        event_source_sha256=event_sha,
        event_row_count=len(event_rows),
        bin_source_path=source_path,
        bin_source_sha256=source_sha,
        bin_source_row_count=len(source_rows),
        source_availability_report=source_availability,
        source_numeric_sufficiency_report=source_sufficiency,
        elapsed_s=time.perf_counter() - started,
    )
    if event_issues or source_issues:
        report["status"] = PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_BLOCKED_STATUS
        report["issues"] = [
            *report["issues"],
            *event_issues,
            *source_issues,
        ]
        report["bounded_shard_execution_performed"] = False
        report["nodi_bounded_shard_run_performed"] = False
    report = write_position_response_source_accumulation_bounded_shard_sidecars(
        output_dir=output_dir,
        report=report,
    )

    print(f"NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD: {report['status']}")
    print(f"selected_job_count: {report['selected_job_count']}")
    print(f"n_events_per_job: {report['n_events_per_job']}")
    print(f"event_rows: {report['event_rows']}")
    print(f"bin_source_rows: {report['bin_source_rows']}")
    print(f"source_availability_status: {report['source_availability_status']}")
    print(
        "source_numeric_sufficiency_status: "
        f"{report['source_numeric_sufficiency_status']}"
    )
    print(f"event_source_path: {report['event_source_path']}")
    print(f"event_source_sha256: {report['event_source_sha256']}")
    print(f"bin_source_path: {report['bin_source_path']}")
    print(f"bin_source_sha256: {report['bin_source_sha256']}")
    print(f"execution_manifest_csv: {report['execution_manifest_csv']}")
    print(f"execution_manifest_csv_sha256: {report['execution_manifest_csv_sha256']}")
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report['report_sha256']}")
    for issue in report["issues"]:
        print(f"- issue: {issue}")
    return (
        0
        if report["status"] == PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_PASS_STATUS
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
