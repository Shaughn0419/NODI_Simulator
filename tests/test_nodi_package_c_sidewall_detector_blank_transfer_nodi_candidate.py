from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file
from nodi_simulator.sidewall_detector_blank_transfer_intake import (
    ROUTE_MATRIX_ACCEPTED_STATUS,
    TRANSFER_ACCEPTED_STATUS,
    build_detector_blank_transfer_intake,
)
from tools.audits import (
    build_nodi_package_c_sidewall_detector_blank_transfer_nodi_candidate as builder,
)


def test_nodi_detector_blank_transfer_candidate_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["panel_rows"] == 2
    assert summary["candidate_transfer_rows"] == 2
    assert summary["detection_probability_current"] is False
    assert summary["route_score_current"] is False
    assert summary["yield_current"] is False


def test_nodi_detector_blank_transfer_candidate_outputs_hash_bound_inputs(tmp_path: Path) -> None:
    payload = builder.build_payload()
    old_output_dir = builder.OUTPUT_DIR
    old_report_dir = builder.REPORT_DIR
    old_source_dir = builder.SOURCE_DIR
    old_transfer_rows = builder.TRANSFER_INPUT_ROWS
    try:
        builder.OUTPUT_DIR = tmp_path / "joint"
        builder.REPORT_DIR = tmp_path / "reports"
        builder.SOURCE_DIR = builder.OUTPUT_DIR / "detector_blank_transfer_nodi_candidate_sources"
        builder.TRANSFER_INPUT_ROWS = (
            builder.OUTPUT_DIR
            / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INPUT_ROWS_20260701.csv"
        )
        paths = builder.write_outputs(payload)
        transfer_rows = read_csv_rows(builder.TRANSFER_INPUT_ROWS)
    finally:
        builder.OUTPUT_DIR = old_output_dir
        builder.REPORT_DIR = old_report_dir
        builder.SOURCE_DIR = old_source_dir
        builder.TRANSFER_INPUT_ROWS = old_transfer_rows

    names = {path.name for path in paths}
    assert "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INPUT_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_SOURCE_ARTIFACT_MANIFEST_20260701.csv" in names
    assert f"577_{builder.PREFIX}_20260701.md" in names
    assert len(transfer_rows) == 2
    for row in transfer_rows:
        blank_path = Path(row["blank_trace_artifact_path"])
        detector_path = Path(row["detector_response_artifact_path"])
        assert sha256_file(blank_path) == row["blank_trace_sha256"]
        assert sha256_file(detector_path) == row["detector_response_sha256"]
        assert row["blank_trace_geometry_match_level"] == "validated_transfer"
        assert row["controls_status"] == "candidate_controls_pass"
        assert row["pre_registered_rule_status"] == "candidate_rule_pre_registered"


def test_nodi_detector_blank_transfer_candidate_is_accepted_by_existing_intake(tmp_path: Path) -> None:
    payload = builder.build_payload()
    old_output_dir = builder.OUTPUT_DIR
    old_report_dir = builder.REPORT_DIR
    old_source_dir = builder.SOURCE_DIR
    old_transfer_rows = builder.TRANSFER_INPUT_ROWS
    try:
        builder.OUTPUT_DIR = tmp_path / "reports" / "joint_interface_20260701"
        builder.REPORT_DIR = tmp_path / "reports"
        builder.SOURCE_DIR = builder.OUTPUT_DIR / "detector_blank_transfer_nodi_candidate_sources"
        builder.TRANSFER_INPUT_ROWS = (
            builder.OUTPUT_DIR
            / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INPUT_ROWS_20260701.csv"
        )
        builder.write_outputs(payload)
        transfer_rows = read_csv_rows(builder.TRANSFER_INPUT_ROWS)
    finally:
        builder.OUTPUT_DIR = old_output_dir
        builder.REPORT_DIR = old_report_dir
        builder.SOURCE_DIR = old_source_dir
        builder.TRANSFER_INPUT_ROWS = old_transfer_rows

    intake_rows, matrix_rows = build_detector_blank_transfer_intake(
        panel_matrix_rows=payload["panel_rows"],
        transfer_input_rows=transfer_rows,
        artifact_root=tmp_path,
    )

    assert {row.transfer_validation_status for row in intake_rows} == {
        TRANSFER_ACCEPTED_STATUS
    }
    assert {row.route_transfer_matrix_status for row in matrix_rows} == {
        ROUTE_MATRIX_ACCEPTED_STATUS
    }
    assert {row.detection_probability_current for row in intake_rows} == {False}
    assert {row.route_score_current for row in intake_rows} == {False}


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_detector_blank_transfer_nodi_candidate.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert (
        "--confirm-sidewall-detector-blank-transfer-nodi-candidate is required"
        in result.stderr
    )
