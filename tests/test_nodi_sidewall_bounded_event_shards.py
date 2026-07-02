from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_bounded_event_shards as builder


def test_bounded_shard_plan_covers_routes_angles_and_particles() -> None:
    rows = builder.bounded_shard_plan_rows()

    assert len(rows) == (
        len(builder.BOUNDED_ROUTES)
        * len(builder.SIDEWALL_PAIR_DEG_COMSOL)
        * len(builder.PARTICLE_DIAMETERS_NM)
    )
    assert {row["sidewall_deg_comsol"] for row in rows} == {90.0, 85.0}
    assert {row["diameter_nm"] for row in rows} == {100, 220, 300}
    assert {row["W_nominal_nm"] for row in rows} >= {500, 600, 800}
    assert all(row["execution_status"] == "planned_not_executed" for row in rows)
    assert all(row["not_detection_probability"] is True for row in rows)


def test_bounded_shard_plan_preserves_sidewall_formula() -> None:
    rows = builder.bounded_shard_plan_rows()
    row = next(
        row
        for row in rows
        if row["lambda_nm"] == 404
        and row["W_nominal_nm"] == 500
        and row["D_nm"] == 900
        and row["sidewall_deg_comsol"] == 85.0
        and row["diameter_nm"] == 100
    )

    assert abs(row["W_bottom_unclipped_nm"] - 342.52) < 0.03
    assert row["channel_cross_section_model"] == "trapezoid_tapered_sidewalls"


def test_plan_payload_builds_ready_state_without_execution() -> None:
    payload = builder.build_payload(execute_nodi=False)
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION_PLAN
    assert summary["execute_nodi"] is False
    assert summary["event_shard_rows"] == 24
    assert summary["executed_event_shard_rows"] == 0
    assert summary["paired_delta_rows"] == 12
    assert summary["failed_alignment_check_rows"] == 0
    assert summary["source_missing_rows"] == 0


def test_paired_delta_rows_are_theta85_vs_theta90_context() -> None:
    event_rows = builder.bounded_shard_plan_rows()
    rows = builder.paired_delta_rows(event_rows)

    assert len(rows) == len(builder.BOUNDED_ROUTES) * len(builder.PARTICLE_DIAMETERS_NM)
    assert all(row["baseline_sidewall_deg_comsol"] == 90.0 for row in rows)
    assert all(row["sidewall_deg_comsol"] == 85.0 for row in rows)
    assert all(row["delta_status"] == "planned_delta_context" for row in rows)
    assert all(row["not_route_score"] is True for row in rows)


def test_no_forbidden_primary_columns_in_plan_outputs() -> None:
    payload = builder.build_payload(execute_nodi=False)
    forbidden_exact = {
        "winner",
        "route_score",
        "rank",
        "detection_probability",
        "yield",
        "W_eff",
        "q_ch_eta",
    }
    for table_key in ("event_shard_rows", "paired_delta_rows"):
        columns = set()
        for row in payload[table_key]:
            columns.update(row)
        assert forbidden_exact.isdisjoint(columns)


def test_alignment_checks_are_hard_pass_for_plan() -> None:
    payload = builder.build_payload(execute_nodi=False)
    checks = payload["alignment_check_rows"]

    assert checks
    assert all(row["check_pass"] is True for row in checks)
    assert all(row["hard_fail_if_false"] is True for row in checks)
    assert any(row["check_name"] == "bounded_plan_row_count" for row in checks)
    assert any(row["check_name"] == "forbidden_primary_columns_absent" for row in checks)


def test_bounded_event_shards_outputs_manifest(tmp_path: Path) -> None:
    payload = builder.build_payload(execute_nodi=False)
    old_output_dir = builder.OUTPUT_DIR
    old_report_dir = builder.REPORT_DIR
    try:
        builder.OUTPUT_DIR = tmp_path / "joint"
        builder.REPORT_DIR = tmp_path / "reports"
        paths = builder.write_outputs(payload)
    finally:
        builder.OUTPUT_DIR = old_output_dir
        builder.REPORT_DIR = old_report_dir

    names = {path.name for path in paths}
    assert f"{builder.PREFIX}_STATUS_20260702.json" in names
    assert f"{builder.PREFIX}_EVENT_SHARD_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_PAIRED_DELTA_ROWS_20260702.csv" in names
    assert f"591_{builder.PREFIX}_20260702.md" in names


def test_bounded_event_shards_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_bounded_event_shards.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-bounded-event-shards is required" in (
        result.stderr + result.stdout
    )
