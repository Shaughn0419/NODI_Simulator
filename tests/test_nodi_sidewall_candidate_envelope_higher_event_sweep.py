from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_candidate_envelope_higher_event_sweep as builder


def test_candidate_envelope_plan_covers_six_routes_and_all_diameters() -> None:
    rows = builder.plan_rows(n_events=8, random_seed=59900)

    assert len(rows) == 78
    assert len({row["source_route_id_nodi"] for row in rows}) == 6
    assert len({row["diameter_nm"] for row in rows}) == 13
    assert {row["sidewall_deg_comsol"] for row in rows} == {85.0}
    assert {row["n_events_requested"] for row in rows} == {8}
    assert all(row["route_id_nodi_role"] == "candidate_envelope_context_not_selection" for row in rows)


def test_candidate_envelope_plan_uses_598_route_mapping() -> None:
    rows = builder.plan_rows(n_events=8, random_seed=59900)
    mapping = {
        row["source_route_id_nodi"]: row["route_id_nodi"]
        for row in rows
        if row["diameter_nm"] == 300
    }

    assert mapping == {
        "404/W500/D1200": "404/W607/D1200",
        "404/W500/D900": "404/W580/D900",
        "404/W600/D900": "404/W680/D900",
        "660/W500/D1500": "660/W633/D1500",
        "660/W800/D1200": "660/W907/D1200",
        "660/W800/D900": "660/W880/D900",
    }


def test_candidate_envelope_delta_rows_join_original_85_context() -> None:
    rows = builder.plan_rows(n_events=8, random_seed=59900)
    deltas = builder.candidate_delta_rows(rows)

    assert len(deltas) == 78
    assert all(row["original_execution_status"] == "executed_bounded_nodi_shard" for row in deltas)
    assert {row["candidate_execution_status"] for row in deltas} == {"planned_not_executed"}
    assert all(row["route_id_role"] == "candidate_envelope_join_key_only_not_selection" for row in deltas)


def test_candidate_envelope_route_summary_is_not_selection() -> None:
    rows = builder.plan_rows(n_events=8, random_seed=59900)
    deltas = builder.candidate_delta_rows(rows)
    summaries = builder.route_summary_rows(deltas)

    assert len(summaries) == 6
    assert all(row["route_id_role"] == "candidate_envelope_summary_not_selection" for row in summaries)
    assert all(row["route_diameter_rows"] == 13 for row in summaries)


def test_candidate_envelope_payload_plan_validation_and_counts() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=8, random_seed=59900)
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION_PLAN
    assert builder.validate_payload(payload) == []
    assert summary["candidate_event_rows"] == 78
    assert summary["executed_candidate_event_rows"] == 0
    assert summary["candidate_delta_rows"] == 78
    assert summary["route_summary_rows"] == 6
    assert summary["answer_axis_rows"] == 3
    assert summary["source_missing_rows"] == 0
    assert summary["failed_validation_rows"] == 0


def test_candidate_envelope_packet_has_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=8, random_seed=59900)
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
        "route_summary_rows",
        "answer_axis_rows",
    ):
        columns = set().union(*(set(row) for row in payload[table_name]))
        assert forbidden_exact.isdisjoint(columns)


def test_candidate_envelope_outputs_manifest(tmp_path: Path) -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=8, random_seed=59900)
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
    assert f"{builder.PREFIX}_ROUTE_SUMMARY_ROWS_20260702.csv" in names
    assert f"599_{builder.PREFIX}_20260702.md" in names


def test_candidate_envelope_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_candidate_envelope_higher_event_sweep.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-candidate-envelope-higher-event-sweep is required" in (
        result.stderr + result.stdout
    )
