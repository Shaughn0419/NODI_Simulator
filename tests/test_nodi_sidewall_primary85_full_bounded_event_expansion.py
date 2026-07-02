from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_primary85_full_bounded_event_expansion as builder


def test_primary85_full_plan_covers_all_routes_diameters_and_angle_pair() -> None:
    rows = builder.plan_rows()

    assert len(rows) == 156
    assert len({row["route_id_nodi"] for row in rows}) == 6
    assert len({row["diameter_nm"] for row in rows}) == 13
    assert {row["sidewall_deg_comsol"] for row in rows} == {90.0, 85.0}
    assert all(row["execution_status"] == "planned_not_executed" for row in rows)


def test_primary85_full_plan_preserves_sidewall_formula() -> None:
    row = next(
        row
        for row in builder.plan_rows()
        if row["route_id_nodi"] == "404/W500/D900"
        and row["sidewall_deg_comsol"] == 85.0
        and row["diameter_nm"] == 100
    )

    assert abs(row["W_bottom_unclipped_nm"] - 342.52) < 0.03
    assert row["channel_cross_section_model"] == "trapezoid_tapered_sidewalls"


def test_primary85_full_delta_rows_are_paired_theta85_vs_theta90() -> None:
    rows = builder.plan_rows()
    deltas = builder.paired_delta_rows(rows)

    assert len(deltas) == 78
    assert {row["baseline_sidewall_deg_comsol"] for row in deltas} == {90.0}
    assert {row["sidewall_deg_comsol"] for row in deltas} == {85.0}
    assert all(row["route_id_nodi_role"] == "join_key_only_not_selection" for row in deltas)


def test_primary85_full_payload_plan_ready_without_execution() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=2, random_seed=59500)
    summary = payload["summary"]

    assert summary["disposition"] == builder.DISPOSITION_PLAN
    assert summary["event_rows"] == 156
    assert summary["executed_event_rows"] == 0
    assert summary["paired_delta_rows"] == 78
    assert summary["failed_alignment_check_rows"] == 0
    assert builder.validate_payload(payload) == []


def test_primary85_full_outputs_have_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=2, random_seed=59500)
    forbidden_exact = {
        "winner",
        "route_score",
        "rank",
        "detection_probability",
        "yield",
        "W_eff",
        "q_ch_eta",
        "rank_under_surrogate",
        "not_route_score",
    }
    for table_name in ("event_rows", "paired_delta_rows"):
        columns = set().union(*(set(row) for row in payload[table_name]))
        assert forbidden_exact.isdisjoint(columns)
        assert all(row["not_selection_metric_claim"] is True for row in payload[table_name])


def test_primary85_full_outputs_manifest(tmp_path: Path) -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=2, random_seed=59500)
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
    assert f"{builder.PREFIX}_EVENT_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_PAIRED_DELTA_ROWS_20260702.csv" in names
    assert f"595_{builder.PREFIX}_20260702.md" in names


def test_primary85_full_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_primary85_full_bounded_event_expansion.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-primary85-full-bounded-event-expansion is required" in (
        result.stderr + result.stdout
    )
