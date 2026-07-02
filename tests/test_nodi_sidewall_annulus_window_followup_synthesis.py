from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

from tools.audits import build_nodi_sidewall_annulus_window_followup_synthesis as builder


def test_route_followup_rows_cover_candidate_envelopes() -> None:
    rows = builder.route_followup_rows()

    assert len(rows) == 6
    assert all(row["route_id_role"] == "annulus_followup_context_not_selection" for row in rows)
    assert all(row["annulus_window_context_is_sparse"] is True for row in rows)
    assert all("0p5_0p8" in json.loads(row["followup_window_set_json"]) for row in rows)


def test_route_followup_rows_include_noncanonical_window_sets() -> None:
    rows = builder.route_followup_rows()

    assert any(len(json.loads(row["followup_window_set_json"])) > 1 for row in rows)
    assert any(
        row["annulus_window_followup_policy_context"]
        in {
            "sweep_inner_canonical_outer_windows",
            "sweep_canonical_plus_outer_shift",
            "sweep_canonical_plus_inner_shift",
        }
        for row in rows
    )


def test_window_family_rows_cover_three_windows_without_selection() -> None:
    rows = builder.window_family_rows()

    assert len(rows) == 3
    assert {row["annulus_window_id"] for row in rows} == {"0p4_0p7", "0p5_0p8", "0p6_0p9"}
    assert all(row["window_family_role"] == "context_family_not_selection" for row in rows)


def test_answer_axis_rows_keep_user_questions_explicit() -> None:
    route_rows = builder.route_followup_rows()
    family_rows = builder.window_family_rows()
    axes = builder.answer_axis_rows(route_rows, family_rows)

    assert {row["answer_axis"] for row in axes} == {
        "selected_annulus_range",
        "interference_response",
        "candidate_dimension_envelope",
    }
    assert all(row["not_selection_metric_claim"] is True for row in axes)


def test_annulus_followup_payload_validation_and_counts() -> None:
    payload = builder.build_payload()
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION
    assert builder.validate_payload(payload) == []
    assert summary["route_followup_rows"] == 6
    assert summary["window_family_rows"] == 3
    assert summary["answer_axis_rows"] == 3
    assert summary["source_missing_rows"] == 0
    assert summary["failed_validation_rows"] == 0
    assert summary["routes_with_noncanonical_followup_windows"] > 0


def test_annulus_followup_has_no_forbidden_primary_columns() -> None:
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
        "route_followup_rows",
        "window_family_rows",
        "answer_axis_rows",
    ):
        columns = set().union(*(set(row) for row in payload[table_name]))
        assert forbidden_exact.isdisjoint(columns)


def test_annulus_followup_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_ROUTE_FOLLOWUP_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_WINDOW_FAMILY_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_ANSWER_AXIS_ROWS_20260703.csv" in names
    assert f"601_{builder.PREFIX}_20260703.md" in names


def test_annulus_followup_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_annulus_window_followup_synthesis.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-annulus-window-followup-synthesis is required" in (
        result.stderr + result.stdout
    )
