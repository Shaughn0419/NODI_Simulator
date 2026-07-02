from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_full_event_integrated_update_packet as builder


def test_integrated_rows_cover_full_primary85_route_diameter_grid() -> None:
    rows = builder.integrated_route_diameter_rows()

    assert len(rows) == 78
    assert len({row["route_id_nodi"] for row in rows}) == 6
    assert len({row["diameter_nm"] for row in rows}) == 13
    assert {row["sidewall_deg_comsol"] for row in rows} == {85.0}
    assert all(row["full_event_delta_available"] is True for row in rows)
    assert all(row["route_id_role"] == "join_key_only_not_selection" for row in rows)


def test_integrated_rows_answer_dimension_annulus_and_response_axes() -> None:
    rows = builder.integrated_route_diameter_rows()

    assert any(
        row["dimension_context_band"]
        in {
            "geometry_respecification_context",
            "dimension_update_required_context",
            "tail_margin_review_context",
        }
        for row in rows
    )
    assert any(
        row["annulus_event_shift_band"]
        in {
            "large_annulus_fraction_shift_context",
            "moderate_annulus_fraction_shift_context",
        }
        for row in rows
    )
    assert any(
        row["response_event_shift_band"]
        in {
            "large_interference_response_shift_context",
            "moderate_interference_response_shift_context",
            "small_interference_response_shift_context",
        }
        for row in rows
    )


def test_integrated_rows_preserve_comsol_v4_and_no_claim_guards() -> None:
    rows = builder.integrated_route_diameter_rows()

    assert rows
    assert all(
        row["comsol_v4_assumption_set_id"]
        == "EV_PBS_SAMPLE_SURFACE_ASSUMPTION_SET_V4_20260627"
        for row in rows
    )
    assert all(row["not_detection_probability"] is True for row in rows)
    assert all(row["not_yield"] is True for row in rows)
    assert all(row["not_selection_metric_claim"] is True for row in rows)
    assert all(row["not_winner"] is True for row in rows)


def test_route_summary_rows_remain_non_selection_context() -> None:
    rows = builder.integrated_route_diameter_rows()
    summaries = builder.route_summary_rows(rows)

    assert len(summaries) == 6
    assert all(row["route_summary_not_selection"] is True for row in summaries)
    assert any(
        row["route_integrated_context_state"]
        in {
            "geometry_respecification_context_present",
            "dimension_update_context_present",
            "annulus_or_response_event_context_review_present",
        }
        for row in summaries
    )


def test_answer_axis_rows_make_the_three_mainline_answers_explicit() -> None:
    rows = builder.integrated_route_diameter_rows()
    summaries = builder.route_summary_rows(rows)
    axes = builder.answer_axis_rows(rows, summaries)

    assert {row["answer_axis"] for row in axes} == {
        "recommended_dimension_window",
        "selected_annulus_range",
        "interference_response",
    }
    assert all(str(row["answer"]).startswith("yes_sidewall_angle_changes") for row in axes)
    assert all(int(row["affected_route_diameter_rows"]) > 0 for row in axes)


def test_integrated_update_payload_validation_and_counts() -> None:
    payload = builder.build_payload()
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION
    assert builder.validate_payload(payload) == []
    assert summary["integrated_route_diameter_rows"] == 78
    assert summary["route_summary_rows"] == 6
    assert summary["answer_axis_rows"] == 3
    assert summary["full_event_delta_join_rows"] == 78
    assert summary["source_missing_rows"] == 0
    assert summary["failed_validation_rows"] == 0
    assert summary["max_abs_mean_peak_height_delta"] > 10


def test_integrated_update_packet_has_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload()
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
        "integrated_route_diameter_rows",
        "route_summary_rows",
        "answer_axis_rows",
    ):
        columns = set().union(*(set(row) for row in payload[table_name]))
        assert forbidden_exact.isdisjoint(columns)


def test_integrated_update_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_INTEGRATED_ROUTE_DIAMETER_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_ROUTE_SUMMARY_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_ANSWER_AXIS_ROWS_20260702.csv" in names
    assert f"596_{builder.PREFIX}_20260702.md" in names


def test_integrated_update_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_full_event_integrated_update_packet.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-full-event-integrated-update-packet is required" in (
        result.stderr + result.stdout
    )
