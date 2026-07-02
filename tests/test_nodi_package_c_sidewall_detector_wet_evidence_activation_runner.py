from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_detector_wet_evidence_activation_runner as builder,
)


def test_detector_wet_activation_runner_builds_current_no_input_state() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["detector_input_present"] is False
    assert summary["wet_input_present"] is False
    assert summary["activation_rows"] == 2
    assert summary["input_contract_rows"] == 2
    assert summary["combined_detector_wet_ready_rows"] == 0
    assert summary["detector_accepted_transfer_rows_total"] == 0
    assert summary["wet_accepted_endpoint_count_total"] == 0
    assert summary["route_score_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False


def test_detector_wet_activation_rows_keep_claims_false() -> None:
    payload = builder.build_payload()
    rows = payload["activation_rows"]

    assert {row["combined_detector_wet_ready_for_formula"] for row in rows} == {False}
    assert {row["route_formula_blocker_status"] for row in rows} == {
        "blocked_detector_blank_or_wet_accepted_evidence_missing"
    }
    assert {row["route_score_current"] for row in rows} == {False}
    assert {row["yield_current"] for row in rows} == {False}
    assert {row["detection_probability_current"] for row in rows} == {False}


def test_detector_wet_activation_runner_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_ACTIVATION_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_INPUT_CONTRACT_ROWS_20260701.csv" in names
    assert f"569_{builder.PREFIX}_20260701.md" in names


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_detector_wet_evidence_activation_runner.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-detector-wet-evidence-activation-runner is required" in result.stderr
