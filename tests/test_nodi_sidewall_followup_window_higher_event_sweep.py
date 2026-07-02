from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

from tools.audits import build_nodi_sidewall_followup_window_higher_event_sweep as builder


def test_followup_plan_uses_602_route_specific_windows() -> None:
    rows = builder.plan_rows(n_events=16, random_seed=60300)

    assert len(rows) == 208
    assert len({row["source_route_id_nodi"] for row in rows}) == 6
    assert len({row["diameter_nm"] for row in rows}) == 13
    assert len({(row["source_route_id_nodi"], row["annulus_window_id"]) for row in rows}) == 16
    assert {row["n_events_requested"] for row in rows} == {16}
    assert all(row["route_id_nodi_role"] == "followup_window_context_not_selection" for row in rows)


def test_followup_plan_retains_canonical_window_per_route() -> None:
    rows = builder.plan_rows(n_events=16, random_seed=60300)
    by_route = {}
    for row in rows:
        by_route.setdefault(row["source_route_id_nodi"], set()).add(row["annulus_window_id"])

    assert set(by_route) == {
        "404/W500/D1200",
        "404/W500/D900",
        "404/W600/D900",
        "660/W500/D1500",
        "660/W800/D1200",
        "660/W800/D900",
    }
    assert all("0p5_0p8" in windows for windows in by_route.values())
    assert {len(windows) for windows in by_route.values()} == {2, 3}


def test_comparisons_are_relative_to_route_canonical_window() -> None:
    rows = builder.plan_rows(n_events=16, random_seed=60300)
    comparisons = builder.comparison_rows(rows)

    assert len(comparisons) == 208
    assert {row["canonical_annulus_window_id"] for row in comparisons} == {"0p5_0p8"}
    canonical = [row for row in comparisons if row["is_canonical_annulus_window"] is True]
    assert len(canonical) == 78
    assert all(row["mean_peak_height_delta_vs_canonical"] in {"", 0.0} for row in canonical)
    assert all(row["route_id_role"] == "followup_window_join_key_only_not_selection" for row in comparisons)


def test_route_window_and_route_closein_rows_cover_expected_shapes() -> None:
    rows = builder.plan_rows(n_events=16, random_seed=60300)
    comparisons = builder.comparison_rows(rows)
    summaries = builder.route_window_summary_rows(comparisons)
    closein = builder.route_closein_rows(summaries)

    assert len(summaries) == 16
    assert len(closein) == 6
    assert {row["route_id_role"] for row in summaries} == {"followup_window_summary_not_selection"}
    assert {row["route_id_role"] for row in closein} == {"followup_window_route_closein_not_selection"}
    assert all("0p5_0p8" in json.loads(row["followup_window_set_json"]) for row in closein)


def test_followup_payload_plan_validation_and_counts() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=16, random_seed=60300)
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION_PLAN
    assert builder.validate_payload(payload) == []
    assert summary["event_rows"] == 208
    assert summary["executed_event_rows"] == 0
    assert summary["comparison_rows"] == 208
    assert summary["route_window_summary_rows"] == 16
    assert summary["route_closein_rows"] == 6
    assert summary["answer_axis_rows"] == 3
    assert summary["source_missing_rows"] == 0
    assert summary["failed_validation_rows"] == 0


def test_followup_packet_has_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=16, random_seed=60300)
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
        "event_rows",
        "comparison_rows",
        "route_window_summary_rows",
        "route_closein_rows",
        "answer_axis_rows",
    ):
        columns = set().union(*(set(row) for row in payload[table_name]))
        assert forbidden_exact.isdisjoint(columns)


def test_followup_outputs_manifest(tmp_path: Path) -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=16, random_seed=60300)
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
    assert f"{builder.PREFIX}_EVENT_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_COMPARISON_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_ROUTE_WINDOW_SUMMARY_ROWS_20260703.csv" in names
    assert f"603_{builder.PREFIX}_20260703.md" in names


def test_followup_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_followup_window_higher_event_sweep.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-followup-window-higher-event-sweep is required" in (
        result.stderr + result.stdout
    )
