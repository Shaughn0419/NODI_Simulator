from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

from tools.audits import build_nodi_sidewall_candidate_dimension_recommendation_synthesis as builder


def test_candidate_dimension_rows_cover_597_followup_deltas() -> None:
    rows = builder.candidate_dimension_rows()

    assert len(rows) == 66
    assert len({row["source_route_id_nodi"] for row in rows}) == 6
    assert all(row["route_id_role"] == "candidate_dimension_context_not_selection" for row in rows)
    assert all(row["sparse_event_context_only"] is True for row in rows)


def test_route_recommendation_rows_expose_expected_candidate_envelopes() -> None:
    rows = builder.candidate_dimension_rows()
    route_rows = builder.route_recommendation_rows(rows)
    mapping = {
        row["source_route_id_nodi"]: row["candidate_envelope_route_id_nodi"]
        for row in route_rows
    }

    assert mapping == {
        "404/W500/D1200": "404/W607/D1200",
        "404/W500/D900": "404/W580/D900",
        "404/W600/D900": "404/W680/D900",
        "660/W500/D1500": "660/W633/D1500",
        "660/W800/D1200": "660/W907/D1200",
        "660/W800/D900": "660/W880/D900",
    }
    assert all(row["route_id_role"] == "candidate_envelope_not_selection" for row in route_rows)


def test_candidate_synthesis_keeps_annulus_tradeoffs_visible() -> None:
    rows = builder.candidate_dimension_rows()
    route_rows = builder.route_recommendation_rows(rows)

    assert any(row["candidate_rows_with_annulus_tradeoff"] > 0 for row in route_rows)
    assert any(
        row["candidate_dimension_recommendation_context"]
        == "advance_candidate_envelope_with_annulus_tradeoff_review"
        for row in route_rows
    )
    assert sum(
        row["candidate_dimension_context"]
        == "candidate_width_improves_response_with_annulus_tradeoff"
        for row in rows
    ) > 0


def test_answer_axis_rows_are_the_three_user_questions() -> None:
    rows = builder.candidate_dimension_rows()
    route_rows = builder.route_recommendation_rows(rows)
    axes = builder.answer_axis_rows(rows, route_rows)

    assert {row["answer_axis"] for row in axes} == {
        "recommended_dimension_window",
        "selected_annulus_range",
        "interference_response",
    }
    assert all(row["route_candidate_envelopes"] for row in axes)
    assert all(row["not_selection_metric_claim"] is True for row in axes)


def test_candidate_recommendation_payload_validation_and_counts() -> None:
    payload = builder.build_payload()
    summary = payload["summary"]
    envelope_mapping = json.loads(summary["route_candidate_envelopes_json"])

    assert payload["disposition"] == builder.DISPOSITION
    assert builder.validate_payload(payload) == []
    assert summary["candidate_dimension_rows"] == 66
    assert summary["route_recommendation_rows"] == 6
    assert summary["answer_axis_rows"] == 3
    assert summary["source_missing_rows"] == 0
    assert summary["failed_validation_rows"] == 0
    assert envelope_mapping["404/W500/D900"] == "404/W580/D900"
    assert summary["candidate_rows_with_response_improvement"] == 62


def test_candidate_recommendation_has_no_forbidden_primary_columns() -> None:
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
        "candidate_dimension_rows",
        "route_recommendation_rows",
        "answer_axis_rows",
    ):
        columns = set().union(*(set(row) for row in payload[table_name]))
        assert forbidden_exact.isdisjoint(columns)


def test_candidate_recommendation_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_CANDIDATE_DIMENSION_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_ROUTE_RECOMMENDATION_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_ANSWER_AXIS_ROWS_20260702.csv" in names
    assert f"598_{builder.PREFIX}_20260702.md" in names


def test_candidate_recommendation_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_candidate_dimension_recommendation_synthesis.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-candidate-dimension-recommendation-synthesis is required" in (
        result.stderr + result.stdout
    )
