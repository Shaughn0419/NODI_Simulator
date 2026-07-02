from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_compensated_width_followup_bounded_events as builder


def test_compensated_width_plan_covers_affected_dimension_rows_only() -> None:
    rows = builder.plan_rows(n_events=2, random_seed=59700)

    assert len(rows) == 66
    assert len({row["source_route_id_nodi"] for row in rows}) == 6
    assert {row["sidewall_deg_comsol"] for row in rows} == {85.0}
    assert all(row["channel_cross_section_model"] == "trapezoid_tapered_sidewalls" for row in rows)
    assert all(row["execution_status"] == "planned_not_executed" for row in rows)


def test_compensated_width_plan_uses_ceil_compensation_width() -> None:
    row = next(
        row
        for row in builder.plan_rows(n_events=2, random_seed=59700)
        if row["source_route_id_nodi"] == "404/W500/D900"
        and row["diameter_nm"] == 220
    )

    assert row["source_W_nominal_nm"] == 500
    assert row["W_top_nm"] == 580
    assert row["candidate_top_width_delta_nm"] == 80
    assert row["candidate_width_rounding_policy"] == "ceil_W_top_compensated_proxy_nm_to_integer_nm"
    assert abs(row["W_bottom_unclipped_nm"] - 422.52) < 0.03


def test_compensated_delta_rows_join_original_sidewall85_context() -> None:
    rows = builder.plan_rows(n_events=2, random_seed=59700)
    deltas = builder.candidate_delta_rows(rows)

    assert len(deltas) == 66
    assert all(row["original_execution_status"] == "executed_bounded_nodi_shard" for row in deltas)
    assert {row["candidate_execution_status"] for row in deltas} == {"planned_not_executed"}
    assert all(row["route_id_role"] == "candidate_join_key_only_not_selection" for row in deltas)


def test_route_envelopes_preserve_non_selection_candidate_context() -> None:
    rows = builder.plan_rows(n_events=2, random_seed=59700)
    deltas = builder.candidate_delta_rows(rows)
    envelopes = builder.route_envelope_rows(rows, deltas)

    assert len(envelopes) == 6
    assert all(row["route_id_role"] == "candidate_envelope_not_selection" for row in envelopes)
    assert any(int(row["candidate_envelope_top_width_delta_nm"]) > 100 for row in envelopes)


def test_compensated_width_payload_plan_validation_and_counts() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=2, random_seed=59700)
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION_PLAN
    assert builder.validate_payload(payload) == []
    assert summary["candidate_event_rows"] == 66
    assert summary["executed_candidate_event_rows"] == 0
    assert summary["candidate_delta_rows"] == 66
    assert summary["route_envelope_rows"] == 6
    assert summary["answer_axis_rows"] == 3
    assert summary["source_missing_rows"] == 0
    assert summary["failed_validation_rows"] == 0


def test_compensated_width_packet_has_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=2, random_seed=59700)
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
        "candidate_event_rows",
        "candidate_delta_rows",
        "route_envelope_rows",
        "answer_axis_rows",
    ):
        columns = set().union(*(set(row) for row in payload[table_name]))
        assert forbidden_exact.isdisjoint(columns)


def test_compensated_width_outputs_manifest(tmp_path: Path) -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=2, random_seed=59700)
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
    assert f"{builder.PREFIX}_CANDIDATE_EVENT_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_CANDIDATE_DELTA_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_ROUTE_ENVELOPE_ROWS_20260702.csv" in names
    assert f"597_{builder.PREFIX}_20260702.md" in names


def test_compensated_width_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_compensated_width_followup_bounded_events.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-compensated-width-followup-bounded-events is required" in (
        result.stderr + result.stdout
    )
