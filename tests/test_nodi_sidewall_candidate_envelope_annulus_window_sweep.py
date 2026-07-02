from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_candidate_envelope_annulus_window_sweep as builder


def test_annulus_window_plan_covers_candidate_envelopes_diameters_and_windows() -> None:
    rows = builder.plan_rows(n_events=6, random_seed=60000)

    assert len(rows) == 234
    assert len({row["source_route_id_nodi"] for row in rows}) == 6
    assert len({row["diameter_nm"] for row in rows}) == 13
    assert {row["annulus_window_id"] for row in rows} == {"0p4_0p7", "0p5_0p8", "0p6_0p9"}
    assert {row["n_events_requested"] for row in rows} == {6}
    assert all(row["route_id_nodi_role"] == "candidate_envelope_annulus_context_not_selection" for row in rows)


def test_annulus_window_plan_preserves_window_bounds_in_config_fields() -> None:
    row = next(
        row
        for row in builder.plan_rows(n_events=6, random_seed=60000)
        if row["source_route_id_nodi"] == "404/W500/D900"
        and row["diameter_nm"] == 220
        and row["annulus_window_id"] == "0p6_0p9"
    )

    assert row["route_id_nodi"] == "404/W580/D900"
    assert row["selected_annulus_edge_norm_min"] == 0.6
    assert row["selected_annulus_edge_norm_max"] == 0.9
    assert row["is_canonical_annulus_window"] is False


def test_annulus_window_comparisons_are_relative_to_canonical_window() -> None:
    rows = builder.plan_rows(n_events=6, random_seed=60000)
    comparisons = builder.window_comparison_rows(rows)

    assert len(comparisons) == 234
    assert {row["canonical_annulus_window_id"] for row in comparisons} == {"0p5_0p8"}
    canonical = [row for row in comparisons if row["is_canonical_annulus_window"] is True]
    assert len(canonical) == 78
    assert all(row["mean_peak_height_delta_vs_canonical"] in {"", 0.0} for row in canonical)
    assert all(row["route_id_role"] == "annulus_window_join_key_only_not_selection" for row in comparisons)


def test_route_window_summary_rows_cover_six_routes_by_three_windows() -> None:
    rows = builder.plan_rows(n_events=6, random_seed=60000)
    comparisons = builder.window_comparison_rows(rows)
    summaries = builder.route_window_summary_rows(comparisons)

    assert len(summaries) == 18
    assert len({row["source_route_id_nodi"] for row in summaries}) == 6
    assert {row["annulus_window_id"] for row in summaries} == {"0p4_0p7", "0p5_0p8", "0p6_0p9"}
    assert all(row["route_id_role"] == "route_window_summary_not_selection" for row in summaries)


def test_annulus_window_payload_plan_validation_and_counts() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=6, random_seed=60000)
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION_PLAN
    assert builder.validate_payload(payload) == []
    assert summary["event_rows"] == 234
    assert summary["executed_event_rows"] == 0
    assert summary["window_comparison_rows"] == 234
    assert summary["route_window_summary_rows"] == 18
    assert summary["answer_axis_rows"] == 3
    assert summary["source_missing_rows"] == 0
    assert summary["failed_validation_rows"] == 0


def test_annulus_window_packet_has_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=6, random_seed=60000)
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
        "window_comparison_rows",
        "route_window_summary_rows",
        "answer_axis_rows",
    ):
        columns = set().union(*(set(row) for row in payload[table_name]))
        assert forbidden_exact.isdisjoint(columns)


def test_annulus_window_outputs_manifest(tmp_path: Path) -> None:
    payload = builder.build_payload(execute_nodi=False, n_events=6, random_seed=60000)
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
    assert f"{builder.PREFIX}_WINDOW_COMPARISON_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_ROUTE_WINDOW_SUMMARY_ROWS_20260703.csv" in names
    assert f"600_{builder.PREFIX}_20260703.md" in names


def test_annulus_window_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_candidate_envelope_annulus_window_sweep.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-candidate-envelope-annulus-window-sweep is required" in (
        result.stderr + result.stdout
    )
