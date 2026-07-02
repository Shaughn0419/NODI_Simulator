from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_mainline_synthesis as builder


def test_route_synthesis_rows_capture_dimension_and_annulus_contexts() -> None:
    rows = builder.route_synthesis_rows()

    assert len(rows) == 6
    assert sum(row["dimension_context"] == "sidewall_objective_width_above_candidate" for row in rows) == 5
    assert sum(row["dimension_context"] == "sidewall_objective_width_retains_candidate" for row in rows) == 1
    assert sum(row["annulus_context"] == "sidewall_annulus_context_shifted_from_canonical" for row in rows) == 4
    assert sum(row["annulus_context"] == "sidewall_annulus_context_retains_canonical_window" for row in rows) == 2


def test_aggregate_answers_cover_three_user_questions() -> None:
    rows = builder.aggregate_answer_rows(builder.route_synthesis_rows())

    assert len(rows) == 3
    assert {
        row["question_id"] for row in rows
    } == {
        "size_recommendation_delta_after_sidewall",
        "selected_annulus_range_delta_after_sidewall",
        "interference_response_delta_after_sidewall",
    }
    dimension = next(row for row in rows if row["question_id"] == "size_recommendation_delta_after_sidewall")
    assert dimension["routes_above_candidate"] == 5
    assert dimension["routes_retaining_candidate"] == 1


def test_payload_validation_and_counts() -> None:
    payload = builder.build_payload()
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION
    assert builder.validate_payload(payload) == []
    assert summary["route_synthesis_rows"] == 6
    assert summary["aggregate_answer_rows"] == 3
    assert summary["routes_above_candidate"] == 5
    assert summary["routes_retaining_candidate"] == 1
    assert summary["routes_shifted_annulus_context"] == 4
    assert summary["routes_retaining_canonical_annulus_context"] == 2
    assert summary["failed_validation_rows"] == 0


def test_mainline_synthesis_has_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload()

    assert builder.no_forbidden_primary_columns(payload) is True


def test_mainline_synthesis_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_ROUTE_SYNTHESIS_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_AGGREGATE_ANSWER_ROWS_20260703.csv" in names
    assert f"613_{builder.PREFIX}_20260703.md" in names


def test_mainline_synthesis_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_mainline_synthesis.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-mainline-synthesis is required" in (
        result.stderr + result.stdout
    )
