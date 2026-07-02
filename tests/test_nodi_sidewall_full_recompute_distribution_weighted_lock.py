from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_sidewall_full_recompute_distribution_weighted_lock as builder,
)


def test_full_recompute_plan_covers_route_window_diameter_grid() -> None:
    rows = builder.recompute_plan_rows(n_events=8, random_seed=607)

    assert len(rows) == 208
    assert {row["execution_status"] for row in rows} == {
        "planned_full_recompute_not_executed"
    }
    assert all(row["rectangle_baseline_status"] == "preserved_not_overwritten" for row in rows)
    assert all(row["n_events_requested"] == 8 for row in rows)


def test_weighted_recompute_rows_expand_plan_by_weight_modes() -> None:
    plan_rows = builder.recompute_plan_rows(n_events=8, random_seed=607)
    rows = builder.weighted_recompute_rows(plan_rows)

    assert len(rows) == 208 * len(builder.WEIGHTING_MODES)
    assert {row["weighting_mode"] for row in rows} == set(builder.WEIGHTING_MODES)
    assert all(row["decision_use_allowed"] is False for row in rows)
    assert all(row["not_exact_pxu_probability_grid"] is True for row in rows)


def test_route_lock_rows_cover_six_routes_times_three_modes() -> None:
    plan_rows = builder.recompute_plan_rows(n_events=8, random_seed=607)
    weighted_rows = builder.weighted_recompute_rows(plan_rows)
    rows = builder.route_lock_rows(weighted_rows)

    assert len(rows) == 18
    assert {row["weighting_mode"] for row in rows} == set(builder.WEIGHTING_MODES)
    assert all(row["route_id_role"] == "full_recompute_route_context_not_selection" for row in rows)
    assert any(
        row["weighting_mode"] != "uniform_edge_mass"
        and row["annulus_context_after_full_recompute"]
        == "weighted_mass_context_shifts_from_canonical"
        for row in rows
    )


def test_question_rows_keep_dimension_annulus_interference_mainline() -> None:
    plan_rows = builder.recompute_plan_rows(n_events=8, random_seed=607)
    route_rows = builder.route_lock_rows(builder.weighted_recompute_rows(plan_rows))
    rows = builder.question_rows(route_rows, execute_nodi=False)

    assert {
        row["question_id"] for row in rows
    } == {
        "size_recommendation_delta_after_sidewall",
        "selected_annulus_range_delta_after_sidewall",
        "interference_response_delta_after_sidewall",
    }
    assert rows[0]["rectangle_baseline_status"] == "preserved_not_overwritten"
    assert rows[0]["next_action"] == "608_width_sweep_with_distribution_weights"


def test_payload_plan_mode_validation_and_counts() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=8, random_seed=607)
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION_PLAN
    assert builder.validate_payload(payload) == []
    assert summary["full_recompute_event_rows"] == 208
    assert summary["full_recompute_executed_rows"] == 0
    assert summary["weighted_recompute_rows"] == 624
    assert summary["route_lock_rows"] == 18
    assert summary["rectangle_baseline_status"] == "preserved_not_overwritten"
    assert summary["failed_validation_rows"] == 0


def test_full_recompute_has_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=8, random_seed=607)

    assert builder.no_forbidden_primary_columns(payload) is True


def test_full_recompute_outputs_manifest(tmp_path: Path) -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=8, random_seed=607)
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
    assert f"{builder.PREFIX}_STATUS_20260703.json" in names
    assert f"{builder.PREFIX}_FULL_RECOMPUTE_EVENT_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_WEIGHTED_RECOMPUTE_ROWS_20260703.csv" in names
    assert f"607_{builder.PREFIX}_20260703.md" in names


def test_full_recompute_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_full_recompute_distribution_weighted_lock.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-full-recompute-distribution-weighted-lock is required" in (
        result.stderr + result.stdout
    )
