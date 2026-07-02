from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_three_question_result_lock as builder


def test_question_result_rows_answer_the_three_user_questions() -> None:
    route_rows = builder.route_result_rows()
    question_rows = builder.question_result_rows(route_rows)

    assert {row["question_id"] for row in question_rows} == {
        "size_recommendation_delta_after_sidewall",
        "selected_annulus_range_delta_after_sidewall",
        "interference_response_delta_after_sidewall",
    }
    assert all(row["not_selection_metric_claim"] is True for row in question_rows)


def test_route_results_cover_six_candidate_envelopes() -> None:
    rows = builder.route_result_rows()

    assert len(rows) == 6
    assert all(row["route_id_role"] == "three_question_result_context_not_selection" for row in rows)
    assert all(int(row["candidate_envelope_top_width_delta_nm"]) > 0 for row in rows)
    assert all(
        row["dimension_result_context"]
        == "candidate_top_width_envelope_changed_under_sidewall"
        for row in rows
    )


def test_route_results_split_response_and_annulus_contexts() -> None:
    rows = builder.route_result_rows()

    assert sum(int(row["noncanonical_windows_with_response_positive_context"]) > 0 for row in rows) == 4
    assert sum(int(row["noncanonical_windows_with_annulus_change_context"]) > 0 for row in rows) == 6
    assert {
        row["route_result_context"] for row in rows
    } == {
        "full_window_response_context_retained",
        "outer_window_annulus_context_retained",
    }


def test_next_actions_cover_routes_without_selection_language() -> None:
    rows = builder.route_result_rows()
    actions = builder.next_action_rows(rows)

    assert len(actions) == 6
    assert all(row["route_id_role"] == "next_action_context_not_selection" for row in actions)
    assert {
        row["next_action_context"] for row in actions
    } == {
        "keep_inner_canonical_outer_windows_for_diameter_resolution",
        "keep_canonical_outer_windows_for_annulus_monitoring",
    }


def test_result_lock_payload_validation_and_counts() -> None:
    payload = builder.build_payload()
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION
    assert builder.validate_payload(payload) == []
    assert summary["route_result_rows"] == 6
    assert summary["question_result_rows"] == 3
    assert summary["routes_with_dimension_delta_context"] == 6
    assert summary["routes_with_annulus_change_context"] == 6
    assert summary["routes_with_response_positive_context"] == 4
    assert summary["source_603_executed_event_rows"] == 208
    assert summary["failed_validation_rows"] == 0


def test_result_lock_has_no_forbidden_primary_columns() -> None:
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
        "route_result_rows",
        "question_result_rows",
        "next_action_rows",
    ):
        columns = set().union(*(set(row) for row in payload[table_name]))
        assert forbidden_exact.isdisjoint(columns)


def test_result_lock_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_QUESTION_RESULT_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_ROUTE_RESULT_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_NEXT_ACTION_ROWS_20260703.csv" in names
    assert f"604_{builder.PREFIX}_20260703.md" in names


def test_result_lock_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_three_question_result_lock.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-three-question-result-lock is required" in (
        result.stderr + result.stdout
    )
