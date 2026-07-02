from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_monotonic_width_policy as builder


def test_width_trajectory_combines_executed_608_609_610_summaries() -> None:
    rows = builder.width_trajectory_rows()

    assert len(rows) == 252
    assert {row["stage_id"] for row in rows} == {
        "608_candidate_width_sweep",
        "609_boundary_followup",
        "610_extended_width_envelope",
    }
    assert {row["weighting_mode"] for row in rows} == set(builder.WEIGHTING_MODES)
    assert all(row["decision_use_allowed"] is False for row in rows)


def test_response_surface_collapses_overlapping_width_points() -> None:
    trajectory = builder.width_trajectory_rows()
    rows = builder.response_surface_rows(trajectory)

    assert len(rows) == 198
    for source_route in {row["source_route_id_nodi"] for row in rows}:
        for mode in builder.WEIGHTING_MODES:
            route_mode_rows = [
                row
                for row in rows
                if row["source_route_id_nodi"] == source_route
                and row["weighting_mode"] == mode
            ]
            assert len(route_mode_rows) == 11


def test_dimension_policy_rows_capture_monotonic_width_pressure() -> None:
    surface = builder.response_surface_rows(builder.width_trajectory_rows())
    rows = builder.dimension_policy_rows(surface)

    assert len(rows) == 18
    comsol_rows = [row for row in rows if row["weighting_mode"] != "uniform_edge_mass"]
    assert len(comsol_rows) == 12
    assert sum(row["peak_upper_edge"] is True for row in comsol_rows) == 12
    assert {
        row["dimension_policy_context"] for row in comsol_rows
    } == {"monotonic_peak_response_constraint_required"}


def test_annulus_policy_rows_cover_route_weighting_grid() -> None:
    surface = builder.response_surface_rows(builder.width_trajectory_rows())
    rows = builder.annulus_policy_rows(surface)

    assert len(rows) == 18
    assert {row["weighting_mode"] for row in rows} == set(builder.WEIGHTING_MODES)
    assert all(row["canonical_annulus_window_id"] == builder.CANONICAL_WINDOW_ID for row in rows)
    assert all("annulus_policy_context" in row for row in rows)


def test_question_rows_preserve_three_mainline_questions() -> None:
    surface = builder.response_surface_rows(builder.width_trajectory_rows())
    dimensions = builder.dimension_policy_rows(surface)
    annulus = builder.annulus_policy_rows(surface)
    rows = builder.question_rows(dimensions, annulus)

    assert {
        row["question_id"] for row in rows
    } == {
        "size_recommendation_delta_after_sidewall",
        "selected_annulus_range_delta_after_sidewall",
        "interference_response_delta_after_sidewall",
    }
    assert rows[0]["comsol_rows_with_peak_upper_edge"] == 12


def test_payload_validation_and_counts() -> None:
    payload = builder.build_payload()
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION
    assert builder.validate_payload(payload) == []
    assert summary["width_trajectory_rows"] == 252
    assert summary["response_surface_rows"] == 198
    assert summary["dimension_policy_rows"] == 18
    assert summary["annulus_policy_rows"] == 18
    assert summary["question_rows"] == 3
    assert summary["comsol_peak_upper_edge_rows"] == 12
    assert summary["failed_validation_rows"] == 0


def test_monotonic_width_policy_has_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload()

    assert builder.no_forbidden_primary_columns(payload) is True


def test_monotonic_width_policy_outputs_manifest(tmp_path: Path) -> None:
    payload = builder.build_payload()
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
    assert f"{builder.PREFIX}_RESPONSE_SURFACE_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_DIMENSION_POLICY_ROWS_20260703.csv" in names
    assert f"611_{builder.PREFIX}_20260703.md" in names


def test_monotonic_width_policy_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_monotonic_width_policy.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-monotonic-width-policy is required" in (
        result.stderr + result.stdout
    )
