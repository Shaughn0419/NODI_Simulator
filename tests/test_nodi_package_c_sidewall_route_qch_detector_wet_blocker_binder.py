from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_route_qch_detector_wet_blocker_binder as builder,
)


def test_route_qch_detector_wet_binder_builds_from_current_artifacts() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["binder_rows"] == 2
    assert summary["supersession_rows"] == 5
    assert summary["rectangle_rows"] == 1
    assert summary["trapezoid_rows"] == 1
    assert summary["qch_ready_rows"] == 2
    assert summary["detector_blocker_rows"] == 2
    assert summary["wet_blocker_rows"] == 2
    assert summary["detector_accepted_transfer_rows_total"] == 0
    assert summary["wet_accepted_observation_rows_total"] == 0
    assert summary["route_score_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False


def test_binder_rows_are_current_canonical_blocker_board() -> None:
    payload = builder.build_payload()
    rows = payload["binder_rows"]

    assert {row["qch_status"] for row in rows} == {
        "formal_qch_input_ready_not_route_score"
    }
    assert {row["route_formula_qch_branch_status"] for row in rows} == {"ready"}
    assert {row["detector_blank_status"] for row in rows} == {
        "blocker_not_accepted_evidence"
    }
    assert {row["wet_observation_status"] for row in rows} == {
        "blocker_not_accepted_evidence"
    }
    assert {row["route_formula_input_ready_count"] for row in rows} == {4}
    assert {row["route_formula_required_input_count"] for row in rows} == {6}


def test_route_qch_detector_wet_binder_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_BINDER_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_SUPERSESSION_ROWS_20260701.csv" in names
    assert f"568_{builder.PREFIX}_20260701.md" in names


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_route_qch_detector_wet_blocker_binder.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-route-qch-detector-wet-blocker-binder is required" in result.stderr
