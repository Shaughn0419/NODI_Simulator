from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_comsol_target_binding_qch_integration as builder,
)


def test_comsol_target_binding_qch_integration_builds_from_current_artifacts() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["integration_rows"] == 2
    assert summary["accepted_exact_pressure_flow_rows"] == 2
    assert summary["formal_qch_sidecar_current_rows"] == 2
    assert summary["route_formula_qch_branch_ready_rows"] == 2
    assert summary["rectangle_rows"] == 1
    assert summary["trapezoid_rows"] == 1
    assert summary["comsol_launch_required_for_current_qch_rows"] == 0
    assert summary["comsol_rerun_allowed_rows"] == 2
    assert summary["route_score_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False


def test_route_evidence_delta_marks_qch_branch_ready_only() -> None:
    payload = builder.build_payload()
    rows = payload["route_evidence_delta_rows"]

    assert len(rows) == 2
    assert {row["evidence_class"] for row in rows} == {
        "accepted_exact_pressure_flow_for_formal_qch_sidecar"
    }
    assert {row["may_satisfy_route_formula_qch_branch_now"] for row in rows} == {
        True
    }
    assert {row["may_satisfy_yield_now"] for row in rows} == {False}
    assert {row["may_satisfy_detection_now"] for row in rows} == {False}
    assert {row["route_score_current"] for row in rows} == {False}


def test_comsol_target_binding_qch_integration_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_INTEGRATION_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_ROUTE_EVIDENCE_DELTA_ROWS_20260701.csv" in names
    assert f"566_{builder.PREFIX}_20260701.md" in names


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_comsol_target_binding_qch_integration.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert (
        "--confirm-sidewall-comsol-target-binding-qch-integration is required"
        in result.stderr
    )
