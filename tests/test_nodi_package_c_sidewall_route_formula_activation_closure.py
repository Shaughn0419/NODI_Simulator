from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_route_formula_activation_closure as builder,
)


def test_route_formula_activation_closure_builds_current_simulation_candidate_state() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.READY_DISPOSITION
    assert summary["closure_rows"] == 2
    assert summary["route_formula_ready_for_claim_review_rows"] == 2
    assert summary["route_formula_ready_for_simulation_candidate_review_rows"] == 2
    assert summary["route_score_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False


def test_route_formula_activation_closure_rows_keep_claims_false() -> None:
    payload = builder.build_payload()
    rows = payload["closure_rows"]

    assert {row["route_formula_activation_status"] for row in rows} == {
        "route_formula_inputs_ready_for_simulation_candidate_review_not_auto_scored"
    }
    assert {row["route_formula_ready_for_simulation_candidate_review"] for row in rows} == {
        True
    }
    assert {row["route_score_current"] for row in rows} == {False}
    assert {row["yield_current"] for row in rows} == {False}
    assert {row["detection_probability_current"] for row in rows} == {False}


def test_route_formula_activation_closure_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_CLOSURE_ROWS_20260701.csv" in names
    assert f"570_{builder.PREFIX}_20260701.md" in names


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_route_formula_activation_closure.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-route-formula-activation-closure is required" in result.stderr
