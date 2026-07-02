from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_distribution_weighted_width_sweep as builder


def test_width_grid_includes_source_candidate_and_above_candidate() -> None:
    assert builder.width_grid_for_route(500, 607) == [567, 587, 607, 627, 647]
    assert builder.width_grid_for_route(800, 880) == [840, 860, 880, 900, 920]


def test_width_sweep_plan_covers_route_width_window_diameter_grid() -> None:
    rows = builder.plan_rows(n_events=4, random_seed=608)

    assert len(rows) == 1040
    assert all(row["execution_status"] == "planned_width_sweep_not_executed" for row in rows)
    assert all(row["n_events_requested"] == 4 for row in rows)
    assert all(row["route_id_role"] == "width_sweep_context_not_route_selection" for row in rows)
    for source_route in {row["source_route_id_nodi"] for row in rows}:
        assert len({int(row["W_top_nm"]) for row in rows if row["source_route_id_nodi"] == source_route}) == 5


def test_weighted_width_rows_expand_by_weighting_modes() -> None:
    plan = builder.plan_rows(n_events=4, random_seed=608)
    rows = builder.weighted_event_rows(plan)

    assert len(rows) == 1040 * len(builder.WEIGHTING_MODES)
    assert {row["weighting_mode"] for row in rows} == set(builder.WEIGHTING_MODES)
    assert all(row["decision_use_allowed"] is False for row in rows)
    assert all(row["not_exact_pxu_probability_grid"] is True for row in rows)


def test_width_summary_and_dimension_context_cover_expected_grid() -> None:
    plan = builder.plan_rows(n_events=4, random_seed=608)
    weighted = builder.weighted_event_rows(plan)
    summaries = builder.width_summary_rows(weighted)
    dimensions = builder.dimension_context_rows(summaries)

    assert len(summaries) == 6 * 5 * len(builder.WEIGHTING_MODES)
    assert len(dimensions) == 6 * len(builder.WEIGHTING_MODES)
    assert {row["weighting_mode"] for row in dimensions} == set(builder.WEIGHTING_MODES)
    assert all("width_grid_json" in row for row in dimensions)


def test_question_rows_preserve_three_user_questions() -> None:
    plan = builder.plan_rows(n_events=4, random_seed=608)
    dimensions = builder.dimension_context_rows(
        builder.width_summary_rows(builder.weighted_event_rows(plan))
    )
    rows = builder.question_rows(dimensions, execute_nodi=False)

    assert {
        row["question_id"] for row in rows
    } == {
        "size_recommendation_delta_after_sidewall",
        "selected_annulus_range_delta_after_sidewall",
        "interference_response_delta_after_sidewall",
    }
    assert rows[0]["next_action"] == "609_dimension_context_lock_or_refined_width_sweep"


def test_payload_plan_mode_validation_and_counts() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=4, random_seed=608)
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION_PLAN
    assert builder.validate_payload(payload) == []
    assert summary["width_sweep_event_rows"] == 1040
    assert summary["width_sweep_executed_rows"] == 0
    assert summary["weighted_width_event_rows"] == 3120
    assert summary["width_summary_rows"] == 90
    assert summary["dimension_context_rows"] == 18
    assert summary["failed_validation_rows"] == 0


def test_width_sweep_has_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=4, random_seed=608)

    assert builder.no_forbidden_primary_columns(payload) is True


def test_width_sweep_outputs_manifest(tmp_path: Path) -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=4, random_seed=608)
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
    assert f"{builder.PREFIX}_WIDTH_SWEEP_EVENT_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_DIMENSION_CONTEXT_ROWS_20260703.csv" in names
    assert f"608_{builder.PREFIX}_20260703.md" in names


def test_width_sweep_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_distribution_weighted_width_sweep.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-distribution-weighted-width-sweep is required" in (
        result.stderr + result.stdout
    )
