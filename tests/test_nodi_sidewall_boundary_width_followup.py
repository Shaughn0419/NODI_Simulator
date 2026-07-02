from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_boundary_width_followup as builder


def test_boundary_anchors_follow_608_upper_edge_contexts() -> None:
    rows = builder.boundary_anchor_rows()

    assert len(rows) == 6
    assert {
        row["source_route_id_nodi"]: row["boundary_anchor_W_top_nm"]
        for row in rows
    } == {
        "404/W500/D1200": 647,
        "404/W500/D900": 620,
        "404/W600/D900": 720,
        "660/W500/D1500": 673,
        "660/W800/D1200": 947,
        "660/W800/D900": 920,
    }
    assert all(
        row["boundary_anchor_source"] == "max_608_comsol_weighted_peak_or_snr_width_context"
        for row in rows
    )
    assert all(row["anchor_is_608_grid_upper_edge"] is True for row in rows)


def test_boundary_followup_plan_covers_route_width_window_diameter_grid() -> None:
    rows = builder.plan_rows(n_events=4, random_seed=609)

    assert len(rows) == 832
    assert all(row["execution_status"] == "planned_boundary_followup_not_executed" for row in rows)
    assert all(row["route_id_role"] == "boundary_width_followup_context_not_route_selection" for row in rows)
    assert all(row["n_events_requested"] == 4 for row in rows)
    assert all("width_sweep_delta_vs_source_nm" in row for row in rows)
    assert all("width_sweep_delta_vs_boundary_anchor_nm" in row for row in rows)
    for source_route in {row["source_route_id_nodi"] for row in rows}:
        route_rows = [row for row in rows if row["source_route_id_nodi"] == source_route]
        assert len({int(row["W_top_nm"]) for row in route_rows}) == 4
        assert {"below_boundary_anchor_width", "boundary_anchor_width", "above_boundary_anchor_width"}.issubset(
            {row["width_context"] for row in route_rows}
        )


def test_weighted_boundary_rows_expand_by_weighting_modes() -> None:
    plan = builder.plan_rows(n_events=4, random_seed=609)
    rows = builder.weighted_event_rows(plan)

    assert len(rows) == 832 * len(builder.WEIGHTING_MODES)
    assert {row["weighting_mode"] for row in rows} == set(builder.WEIGHTING_MODES)
    assert all(row["decision_use_allowed"] is False for row in rows)
    assert all(row["not_exact_pxu_probability_grid"] is True for row in rows)


def test_boundary_summary_and_dimension_context_cover_expected_grid() -> None:
    plan = builder.plan_rows(n_events=4, random_seed=609)
    weighted = builder.weighted_event_rows(plan)
    summaries = builder.width_summary_rows(weighted)
    dimensions = builder.boundary_dimension_context_rows(summaries)

    assert len(summaries) == 6 * 4 * len(builder.WEIGHTING_MODES)
    assert len(dimensions) == 6 * len(builder.WEIGHTING_MODES)
    assert {row["weighting_mode"] for row in dimensions} == set(builder.WEIGHTING_MODES)
    assert all("width_grid_json" in row for row in dimensions)
    assert all("dimension_context_after_boundary_followup" in row for row in dimensions)


def test_question_rows_preserve_three_mainline_questions() -> None:
    plan = builder.plan_rows(n_events=4, random_seed=609)
    dimensions = builder.boundary_dimension_context_rows(
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
    assert rows[0]["next_action"] == "610_lock_or_extend_width_context"


def test_payload_plan_mode_validation_and_counts() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=4, random_seed=609)
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION_PLAN
    assert builder.validate_payload(payload) == []
    assert summary["boundary_anchor_rows"] == 6
    assert summary["boundary_followup_event_rows"] == 832
    assert summary["boundary_followup_executed_rows"] == 0
    assert summary["weighted_boundary_event_rows"] == 2496
    assert summary["boundary_width_summary_rows"] == 72
    assert summary["boundary_dimension_context_rows"] == 18
    assert summary["failed_validation_rows"] == 0


def test_boundary_followup_has_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=4, random_seed=609)

    assert builder.no_forbidden_primary_columns(payload) is True


def test_boundary_followup_outputs_manifest(tmp_path: Path) -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=4, random_seed=609)
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
    assert f"{builder.PREFIX}_BOUNDARY_FOLLOWUP_EVENT_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_BOUNDARY_DIMENSION_CONTEXT_ROWS_20260703.csv" in names
    assert f"609_{builder.PREFIX}_20260703.md" in names


def test_boundary_followup_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_boundary_width_followup.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-boundary-width-followup is required" in (
        result.stderr + result.stdout
    )
