from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_dimension_annulus_interference_synthesis as builder


def test_synthesis_answers_three_main_user_questions() -> None:
    payload = builder.build_payload()
    rows = payload["answer_axis_rows"]

    assert payload["summary"]["disposition"] == builder.DISPOSITION
    assert {row["axis"] for row in rows} == {
        "recommended_dimension_window",
        "selected_annulus_range",
        "interference_response",
    }
    assert all("yes" in row["answer"] for row in rows)
    assert all(row["not_selection_metric_claim"] is True for row in rows)


def test_dimension_change_rows_cover_multiwidth_grid_and_signal_changes() -> None:
    rows = builder.dimension_change_rows()

    assert len(rows) == 546
    assert any(row["sidewall_deg_comsol"] == 85.0 for row in rows)
    assert any(row["dimension_change_signal"] == "tail_sensitive_shift" for row in rows)
    assert any(row["dimension_change_signal"] == "closed_geometry" for row in rows)
    assert all(row["route_id_role"] == "join_key_only_not_selection" for row in rows)


def test_annulus_change_rows_cover_partial_support_without_neighbor_fill() -> None:
    rows = builder.annulus_change_rows()

    assert len(rows) == 168
    assert any(row["annulus_change_signal"] == "annulus_partial_remap" for row in rows)
    assert all(row["no_neighbor_fill_for_blocked_bins"] is True for row in rows)
    assert all(row["annulus_edge_norm_min"] == 0.5 for row in rows)
    assert all(row["annulus_edge_norm_max"] == 0.8 for row in rows)


def test_interference_change_rows_join_bounded_event_deltas() -> None:
    rows = builder.interference_change_rows()
    joined = [row for row in rows if row["bounded_event_delta_available"] is True]

    assert len(rows) == 168
    assert len(joined) == 12
    assert any(row["interference_change_signal"] == "bounded_event_shift_observed" for row in rows)
    assert all(row["axis"] == "interference_response" for row in rows)


def test_synthesis_payload_has_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
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
    for table_name in (
        "answer_axis_rows",
        "dimension_change_rows",
        "annulus_change_rows",
        "interference_change_rows",
    ):
        columns = set().union(*(set(row) for row in payload[table_name]))
        assert forbidden_exact.isdisjoint(columns)


def test_synthesis_alignment_checks_are_all_pass() -> None:
    payload = builder.build_payload()

    assert payload["summary"]["failed_alignment_check_rows"] == 0
    assert payload["summary"]["source_missing_rows"] == 0
    assert payload["summary"]["bounded_event_delta_join_rows"] == 12
    assert all(row["check_pass"] is True for row in payload["alignment_check_rows"])


def test_synthesis_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_STATUS_20260702.json" in names
    assert f"{builder.PREFIX}_ANSWER_AXIS_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_DIMENSION_CHANGE_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_ANNULUS_CHANGE_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_INTERFERENCE_CHANGE_ROWS_20260702.csv" in names
    assert f"593_{builder.PREFIX}_20260702.md" in names


def test_synthesis_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_dimension_annulus_interference_synthesis.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-dimension-annulus-interference-synthesis is required" in (
        result.stderr + result.stdout
    )
