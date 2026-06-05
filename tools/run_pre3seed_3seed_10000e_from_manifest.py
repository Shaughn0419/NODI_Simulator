#!/usr/bin/env python3
"""Manifest-driven formal 3seed/10000e runner.

Default mode is a dry-run prelaunch check. The expensive simulation path runs
only when --execute, --allow-large-run, and --confirm-p19-level1-launch are
all supplied.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.pre3seed_hardening import (  # noqa: E402
    CANDIDATE_MANIFEST_PATH,
    CARRY_FORWARD_PATH,
    FORMAL_EXACT_COMMAND_TEMPLATE,
    FORMAL_LAUNCH_CONFIRMATION_FLAG,
    FORMAL_LAUNCH_CONTRACT_VERSION,
    FORMAL_DUAL_LENS_TOP_TABLE_PATH,
    FORMAL_P19_REQUIRED_ARTIFACT_PATHS,
    FORMAL_POOLED_PER_SEED_CONSISTENCY_PATH,
    FORMAL_PRELAUNCH_MANIFEST_PATH,
    FORMAL_RUN_PLAN_CSV_PATH,
    FORMAL_RUN_PLAN_JSON_PATH,
    FORMAL_WORKER_COUNT,
    PreflightGateError,
    STABILITY_MATRIX_PATH,
    build_claim_linter_policy,
    build_dual_lens_top_table,
    build_formal_3seed_run_plan,
    build_formal_particle_panel,
    build_formal_prelaunch_manifest,
    build_pooled_per_seed_consistency,
    now_utc_iso,
    read_csv_rows,
    relpath,
    run_low_event_sweep,
    sha256_payload,
    sha256_or_na,
    validate_formal_3seed_run_plan,
    validate_formal_execution_freeze,
    validate_preflight_table_scope,
    write_csv_rows,
    write_json_atomic,
)


def _parse_seeds(raw: str) -> tuple[int, ...]:
    values = tuple(int(part.strip()) for part in raw.split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("seed list must not be empty")
    if len(set(values)) != len(values):
        raise argparse.ArgumentTypeError("seed list contains duplicates")
    return values


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build or execute the formal 3seed/10000e run from carry-forward manifest."
    )
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--events-per-case", type=int, default=10_000)
    parser.add_argument("--seeds", type=_parse_seeds, default=(11, 22, 33))
    parser.add_argument(
        "--workers",
        type=int,
        default=FORMAL_WORKER_COUNT,
        help=(
            "Worker count for the formal run. The P19 prelaunch contract freezes "
            f"this at {FORMAL_WORKER_COUNT}; changing it is a new scope."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/pre3seed_formal_3seed_10000e_run"),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Write/validate plan and prelaunch manifest without running simulation. This is the default.",
    )
    mode.add_argument(
        "--execute",
        action="store_true",
        help="Run the expensive manifest-driven sweep.",
    )
    parser.add_argument(
        "--allow-large-run",
        action="store_true",
        help="Required with --execute to prevent accidental 10000e launch.",
    )
    parser.add_argument(
        "--confirm-p19-level1-launch",
        action="store_true",
        help=(
            "Required with --execute and --allow-large-run. Confirms this is the "
            "P19-scoped no-measured-data Level-1 relative/proxy run, not a "
            "calibrated or measured-artifact run."
        ),
    )
    return parser.parse_args()


def _load_plan(project_root: Path, *, seeds: tuple[int, ...], events_per_case: int) -> list[dict[str, object]]:
    carry_rows = read_csv_rows(project_root / CARRY_FORWARD_PATH)
    candidate_rows = read_csv_rows(project_root / CANDIDATE_MANIFEST_PATH)
    stability_rows = read_csv_rows(project_root / STABILITY_MATRIX_PATH)
    plan = build_formal_3seed_run_plan(
        carry_rows,
        candidate_rows,
        stability_rows,
        seeds=seeds,
        events_per_case=events_per_case,
        particle_panel_size=len({row["particle_id"] for row in candidate_rows}),
    )
    validate_formal_3seed_run_plan(plan)
    return plan


def _preserved_created_at(path: Path, *, plan_hash: str) -> str | None:
    if not path.exists():
        return None
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if str(existing.get("formal_run_plan_hash")) != plan_hash:
        return None
    created_at = existing.get("created_at")
    return str(created_at) if created_at else None


def _existing_prelaunch_matches_current(
    project_root: Path,
    *,
    plan_hash: str,
    plan: list[dict[str, object]],
) -> dict[str, object] | None:
    path = project_root / FORMAL_PRELAUNCH_MANIFEST_PATH
    if not path.exists():
        return None
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    top_table_rows = (
        read_csv_rows(project_root / FORMAL_DUAL_LENS_TOP_TABLE_PATH)
        if (project_root / FORMAL_DUAL_LENS_TOP_TABLE_PATH).exists()
        else []
    )
    consistency_rows = (
        read_csv_rows(project_root / FORMAL_POOLED_PER_SEED_CONSISTENCY_PATH)
        if (project_root / FORMAL_POOLED_PER_SEED_CONSISTENCY_PATH).exists()
        else []
    )
    expected = {
        "formal_run_plan_hash": plan_hash,
        "carry_forward_manifest_hash": sha256_or_na(project_root / CARRY_FORWARD_PATH),
        "candidate_manifest_hash": sha256_or_na(project_root / CANDIDATE_MANIFEST_PATH),
        "stability_matrix_hash": sha256_or_na(project_root / STABILITY_MATRIX_PATH),
        "expected_rows": sum(int(row["expected_rows_for_seed_route"]) for row in plan),
        "expected_event_count": sum(int(row["expected_event_count_for_seed_route"]) for row in plan),
        "top_table_template_hash": sha256_payload(top_table_rows),
        "pooled_per_seed_consistency_hash": sha256_payload(consistency_rows),
    }
    for key, value in expected.items():
        if existing.get(key) != value:
            return None
    if existing.get("exact_command_template") != FORMAL_EXACT_COMMAND_TEMPLATE:
        return None
    contract = existing.get("launch_authorization_contract")
    if not isinstance(contract, dict):
        return None
    if contract.get("contract_version") != FORMAL_LAUNCH_CONTRACT_VERSION:
        return None
    if FORMAL_LAUNCH_CONFIRMATION_FLAG not in contract.get("required_execute_flags", []):
        return None
    if existing.get("planned_worker_count") != FORMAL_WORKER_COUNT:
        return None
    if contract.get("planned_worker_count") != FORMAL_WORKER_COUNT:
        return None
    if contract.get("required_worker_flag") != f"--workers {FORMAL_WORKER_COUNT}":
        return None
    p19_hashes = existing.get("p19_required_artifact_hashes")
    if not isinstance(p19_hashes, dict):
        return None
    expected_p19_paths = {
        relpath(project_root / path, project_root)
        for path in FORMAL_P19_REQUIRED_ARTIFACT_PATHS
    }
    if set(p19_hashes) != expected_p19_paths:
        return None
    for path in FORMAL_P19_REQUIRED_ARTIFACT_PATHS:
        rel = relpath(project_root / path, project_root)
        if p19_hashes.get(rel) != sha256_or_na(project_root / rel):
            return None
    return existing


def _write_prelaunch_artifacts(project_root: Path, plan: list[dict[str, object]]) -> dict[str, object]:
    plan_hash = sha256_payload(plan)
    run_plan_created_at = _preserved_created_at(
        project_root / FORMAL_RUN_PLAN_JSON_PATH,
        plan_hash=plan_hash,
    ) or now_utc_iso()
    write_csv_rows(project_root / FORMAL_RUN_PLAN_CSV_PATH, plan)
    write_json_atomic(
        project_root / FORMAL_RUN_PLAN_JSON_PATH,
        {
            "schema_version": "pre3seed_formal_3seed_10000e_run_plan_manifest_v1",
            "created_at": run_plan_created_at,
            "formal_run_plan_path": relpath(project_root / FORMAL_RUN_PLAN_CSV_PATH, project_root),
            "formal_run_plan_hash": plan_hash,
            "candidate_family_count": len({row["candidate_family_id"] for row in plan}),
            "seed_list": sorted({int(row["seed"]) for row in plan}),
            "expected_rows": sum(int(row["expected_rows_for_seed_route"]) for row in plan),
            "expected_event_count": sum(int(row["expected_event_count_for_seed_route"]) for row in plan),
            "claim_boundary": (
                "dry-run plan unless the full P19 launch command, including "
                f"{FORMAL_LAUNCH_CONFIRMATION_FLAG}, was supplied after final launch authorization"
            ),
        },
        sort_keys=True,
    )
    existing_prelaunch = _existing_prelaunch_matches_current(
        project_root,
        plan_hash=plan_hash,
        plan=plan,
    )
    if existing_prelaunch is not None:
        return existing_prelaunch
    top_table_rows = (
        read_csv_rows(project_root / FORMAL_DUAL_LENS_TOP_TABLE_PATH)
        if (project_root / FORMAL_DUAL_LENS_TOP_TABLE_PATH).exists()
        else []
    )
    consistency_rows = (
        read_csv_rows(project_root / FORMAL_POOLED_PER_SEED_CONSISTENCY_PATH)
        if (project_root / FORMAL_POOLED_PER_SEED_CONSISTENCY_PATH).exists()
        else []
    )
    prelaunch = build_formal_prelaunch_manifest(
        formal_plan_rows=plan,
        top_table_rows=top_table_rows,
        consistency_rows=consistency_rows,
        project_root=project_root,
    )
    prelaunch["created_at"] = _preserved_created_at(
        project_root / FORMAL_PRELAUNCH_MANIFEST_PATH,
        plan_hash=plan_hash,
    ) or prelaunch["created_at"]
    write_json_atomic(project_root / FORMAL_PRELAUNCH_MANIFEST_PATH, prelaunch, sort_keys=True)
    return prelaunch


def _write_formal_postprocess_outputs(
    project_root: Path,
    output_dir: Path,
    rows: list[dict[str, object]],
    plan: list[dict[str, object]],
    freeze_check: dict[str, object],
    run_manifest: dict[str, object] | None = None,
) -> dict[str, object]:
    policy = build_claim_linter_policy()
    validate_preflight_table_scope(rows, table_name="formal_3seed_10000e_raw_summary", policy=policy)
    candidate_rows = read_csv_rows(project_root / CANDIDATE_MANIFEST_PATH)
    stability_rows = read_csv_rows(project_root / STABILITY_MATRIX_PATH)
    top_rows = build_dual_lens_top_table(rows, stability_rows, candidate_rows)
    for lens_policy in sorted({str(row["lens_policy"]) for row in top_rows}):
        validate_preflight_table_scope(
            [row for row in top_rows if str(row["lens_policy"]) == lens_policy],
            table_name=f"formal_3seed_10000e_top_table_{lens_policy}",
            policy=policy,
        )
    consistency_rows = build_pooled_per_seed_consistency(top_rows)
    resolved_output_dir = project_root / output_dir
    top_path = resolved_output_dir / "pre3seed_formal_3seed_10000e_dual_lens_top_table.csv"
    consistency_path = resolved_output_dir / "pre3seed_formal_3seed_10000e_pooled_per_seed_consistency.csv"
    postrun_manifest_path = resolved_output_dir / "pre3seed_formal_3seed_10000e_postrun_manifest.json"
    write_csv_rows(top_path, top_rows)
    write_csv_rows(consistency_path, consistency_rows)
    postrun_manifest = {
        "schema_version": "pre3seed_formal_3seed_10000e_postrun_manifest_v1",
        "created_at": now_utc_iso(),
        "claim_boundary": "formal relative/proxy design-selection postprocess; no calibrated detector or biological specificity claim",
        "formal_run_plan_hash": sha256_payload(plan),
        "freeze_check": freeze_check,
        "raw_summary_path": (run_manifest or {}).get("summary_path", ""),
        "raw_summary_sha256": (run_manifest or {}).get("summary_sha256", ""),
        "diagnostic_snapshot_path": (run_manifest or {}).get("diagnostic_snapshot_path", ""),
        "diagnostic_snapshot_sha256": (run_manifest or {}).get("diagnostic_snapshot_sha256", ""),
        "diagnostic_snapshot_row_count": (run_manifest or {}).get("diagnostic_snapshot_row_count", ""),
        "diagnostic_snapshot_schema": (run_manifest or {}).get("diagnostic_snapshot_schema", ""),
        "diagnostic_snapshot_policy": (run_manifest or {}).get("diagnostic_snapshot_policy", ""),
        "raw_summary_rows": len(rows),
        "dual_lens_top_table_rows": len(top_rows),
        "pooled_per_seed_consistency_rows": len(consistency_rows),
        "dual_lens_top_table_path": relpath(top_path, project_root),
        "dual_lens_top_table_sha256": sha256_or_na(top_path),
        "pooled_per_seed_consistency_path": relpath(consistency_path, project_root),
        "pooled_per_seed_consistency_sha256": sha256_or_na(consistency_path),
        "required_lens_outputs": ["all_crossing", "selected_annulus_event_position_window"],
        "route_scope_policy": "rank and aggregate only within lens_policy, seed_scope, and normalization_policy",
    }
    write_json_atomic(postrun_manifest_path, postrun_manifest, sort_keys=True)
    postrun_manifest["postrun_manifest_path"] = relpath(postrun_manifest_path, project_root)
    postrun_manifest["postrun_manifest_sha256"] = sha256_or_na(postrun_manifest_path)
    write_json_atomic(postrun_manifest_path, postrun_manifest, sort_keys=True)
    return postrun_manifest


def main() -> int:
    args = _parse_args()
    if args.execute and not args.allow_large_run:
        raise SystemExit("--execute requires --allow-large-run")
    if args.execute and not args.confirm_p19_level1_launch:
        raise SystemExit(
            "--execute requires --confirm-p19-level1-launch after explicit user "
            "authorization, final freeze/prelaunch closure, and P19 Level-1 scope review"
        )
    if int(args.workers) != FORMAL_WORKER_COUNT:
        raise SystemExit(
            f"formal P19 full run requires --workers {FORMAL_WORKER_COUNT}; "
            "changing worker count is a new scope and requires P19/freeze refresh"
        )
    project_root = args.project_root.resolve()
    plan = _load_plan(
        project_root,
        seeds=tuple(args.seeds),
        events_per_case=int(args.events_per_case),
    )

    summary = {
        "mode": "dry_run",
        "formal_run_plan_path": relpath(project_root / FORMAL_RUN_PLAN_CSV_PATH, project_root),
        "prelaunch_manifest_path": relpath(project_root / FORMAL_PRELAUNCH_MANIFEST_PATH, project_root),
        "candidate_family_count": len({row["candidate_family_id"] for row in plan}),
        "seed_list": sorted({int(row["seed"]) for row in plan}),
        "events_per_case": int(args.events_per_case),
        "planned_worker_count": int(args.workers),
        "expected_rows": sum(int(row["expected_rows_for_seed_route"]) for row in plan),
    }
    if args.execute:
        try:
            freeze_check = validate_formal_execution_freeze(
                formal_plan_rows=plan,
                project_root=project_root,
            )
        except PreflightGateError as exc:
            raise SystemExit(str(exc)) from None
        routes = sorted(
            {
                (int(row["wavelength_nm"]), int(row["width_nm"]), int(row["depth_nm"]))
                for row in plan
            }
        )
        rows, manifest = run_low_event_sweep(
            args.output_dir,
            routes=routes,
            seeds=tuple(args.seeds),
            n_events=int(args.events_per_case),
            label="pre3seed_formal_3seed_10000e",
            project_root=project_root,
            particles=build_formal_particle_panel(),
            n_workers=int(args.workers),
        )
        postrun_manifest = _write_formal_postprocess_outputs(
            project_root,
            args.output_dir,
            rows,
            plan,
            freeze_check,
            run_manifest=manifest,
        )
        summary.update(
            {
                "mode": "executed",
                "output_dir": relpath(project_root / args.output_dir, project_root),
                "actual_rows": len(rows),
                "run_manifest": manifest,
                "postrun_manifest": postrun_manifest,
            }
        )
    else:
        _write_prelaunch_artifacts(project_root, plan)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
