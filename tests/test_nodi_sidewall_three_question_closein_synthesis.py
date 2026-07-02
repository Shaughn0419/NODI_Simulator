from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

from tools.audits import build_nodi_sidewall_three_question_closein_synthesis as builder


def test_three_question_rows_are_exactly_the_user_mainline() -> None:
    payload = builder.build_payload()
    question_ids = {row["question_id"] for row in payload["question_rows"]}

    assert question_ids == {
        "size_recommendation_delta_after_sidewall",
        "selected_annulus_range_delta_after_sidewall",
        "interference_response_delta_after_sidewall",
    }
    assert all(row["not_selection_metric_claim"] is True for row in payload["question_rows"])


def test_route_closein_rows_cover_candidate_dimension_envelopes() -> None:
    rows = builder.route_closein_rows()

    assert len(rows) == 6
    assert all(
        row["route_id_role"] == "three_question_closein_context_not_selection"
        for row in rows
    )
    assert all(int(row["candidate_envelope_top_width_delta_nm"]) > 0 for row in rows)
    assert all(int(row["higher_rows_with_response_improvement"]) > 0 for row in rows)


def test_annulus_followup_keeps_canonical_and_noncanonical_windows() -> None:
    rows = builder.route_closein_rows()

    assert all("0p5_0p8" in json.loads(row["followup_window_set_json"]) for row in rows)
    assert all(len(json.loads(row["followup_window_set_json"])) > 1 for row in rows)
    assert {
        row["annulus_window_followup_policy_context"] for row in rows
    } >= {
        "sweep_inner_canonical_outer_windows",
        "sweep_canonical_plus_outer_shift",
    }


def test_next_simulation_rows_expand_followup_windows_not_routes() -> None:
    closein = builder.route_closein_rows()
    next_rows = builder.next_simulation_rows(closein)
    expected_cases = sum(len(json.loads(row["followup_window_set_json"])) for row in closein)

    assert len(next_rows) == expected_cases
    assert len(next_rows) == 16
    assert all(row["simulation_intent"] == "closein_dimension_annulus_response_joint_sweep" for row in next_rows)
    assert all(row["planned_particle_diameter_count"] == len(builder.PRS_APPROVED_DIAMETERS_NM) for row in next_rows)
    assert all(
        row["recommended_n_events_per_route_diameter_window"]
        == builder.RECOMMENDED_N_EVENTS_PER_ROUTE_DIAMETER_WINDOW
        for row in next_rows
    )


def test_closein_payload_validation_counts_and_planned_trials() -> None:
    payload = builder.build_payload()
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION
    assert builder.validate_payload(payload) == []
    assert summary["route_closein_rows"] == 6
    assert summary["question_rows"] == 3
    assert summary["next_simulation_rows"] == 16
    assert summary["routes_with_candidate_dimension_change"] == 6
    assert summary["routes_with_noncanonical_annulus_followup_windows"] == 6
    assert summary["routes_with_higher_event_response_improvement"] == 6
    assert summary["planned_route_diameter_window_rows"] == 208
    assert summary["planned_event_trials"] == 3328


def test_closein_has_no_forbidden_primary_columns() -> None:
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
        "route_closein_rows",
        "question_rows",
        "next_simulation_rows",
    ):
        columns = set().union(*(set(row) for row in payload[table_name]))
        assert forbidden_exact.isdisjoint(columns)


def test_closein_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_QUESTION_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_ROUTE_CLOSEIN_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_NEXT_SIMULATION_ROWS_20260703.csv" in names
    assert f"602_{builder.PREFIX}_20260703.md" in names


def test_closein_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_three_question_closein_synthesis.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-three-question-closein-synthesis is required" in (
        result.stderr + result.stdout
    )
