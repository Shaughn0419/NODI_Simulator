from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_dimension_objective_packet as builder


def test_dimension_objective_rows_cover_route_weighting_grid() -> None:
    rows = builder.dimension_objective_rows()

    assert len(rows) == 18
    assert {row["weighting_mode"] for row in rows} == set(builder.WEIGHTING_MODES)
    assert all(row["objective_function_id"] == builder.OBJECTIVE_FUNCTION_ID for row in rows)
    assert all(row["objective_version"] == builder.OBJECTIVE_VERSION for row in rows)
    assert all(row["objective_claim_level"] == builder.OBJECTIVE_CLAIM_LEVEL for row in rows)


def test_comsol_objective_widths_are_not_below_candidate_and_most_are_wider() -> None:
    rows = [
        row
        for row in builder.dimension_objective_rows()
        if row["weighting_mode"] != "uniform_edge_mass"
    ]

    assert len(rows) == 12
    assert all(int(row["objective_delta_vs_candidate_nm"]) >= 0 for row in rows)
    assert sum(int(row["objective_delta_vs_candidate_nm"]) > 0 for row in rows) == 10
    assert sum(int(row["objective_delta_vs_candidate_nm"]) == 0 for row in rows) == 2


def test_objective_rows_meet_peak_and_snr_retention_thresholds() -> None:
    rows = builder.dimension_objective_rows()

    assert all(
        float(row["peak_retention_at_objective"]) >= builder.PEAK_RETENTION_THRESHOLD
        for row in rows
    )
    assert all(
        float(row["snr_retention_at_objective"]) >= builder.SNR_RETENTION_THRESHOLD
        for row in rows
    )


def test_objective_summary_rows_cover_six_routes() -> None:
    rows = builder.objective_summary_rows(builder.dimension_objective_rows())

    assert len(rows) == 6
    assert all(row["summary_context"] == "assumption_driven_sidewall_dimension_envelope" for row in rows)
    assert all(row["not_route_winner"] is True for row in rows)


def test_question_rows_preserve_three_mainline_questions() -> None:
    rows = builder.question_rows(builder.dimension_objective_rows())

    assert {
        row["question_id"] for row in rows
    } == {
        "size_recommendation_delta_after_sidewall",
        "selected_annulus_range_delta_after_sidewall",
        "interference_response_delta_after_sidewall",
    }
    dimension_row = next(row for row in rows if row["question_id"].endswith("sidewall"))
    assert dimension_row["comsol_rows_with_objective_width_above_candidate"] == 10
    assert dimension_row["comsol_rows_with_objective_width_equal_candidate"] == 2


def test_payload_validation_and_counts() -> None:
    payload = builder.build_payload()
    summary = payload["summary"]

    assert payload["disposition"] == builder.DISPOSITION
    assert builder.validate_payload(payload) == []
    assert summary["dimension_objective_rows"] == 18
    assert summary["objective_summary_rows"] == 6
    assert summary["question_rows"] == 3
    assert summary["comsol_rows_with_objective_width_above_candidate"] == 10
    assert summary["comsol_rows_with_objective_width_equal_candidate"] == 2
    assert summary["failed_validation_rows"] == 0


def test_dimension_objective_has_no_forbidden_primary_columns() -> None:
    payload = builder.build_payload()

    assert builder.no_forbidden_primary_columns(payload) is True


def test_dimension_objective_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_DIMENSION_OBJECTIVE_ROWS_20260703.csv" in names
    assert f"{builder.PREFIX}_OBJECTIVE_SUMMARY_ROWS_20260703.csv" in names
    assert f"612_{builder.PREFIX}_20260703.md" in names


def test_dimension_objective_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_dimension_objective_packet.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-dimension-objective-packet is required" in (
        result.stderr + result.stdout
    )
