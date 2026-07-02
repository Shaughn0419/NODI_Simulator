from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_mainline_execution_work_order as builder,
)


def test_mainline_execution_work_order_builds_from_current_artifacts() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]
    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["work_order_rows"] == 8
    assert summary["claim_guard_rows"] == 7
    assert summary["route_evidence_register_rows"] == 10
    assert summary["route_geometry_scope"] == "ideal_rectangle;trapezoid_tapered_sidewalls"
    assert summary["implementation_authorized_rows"] == 8
    assert summary["codex_can_execute_next_rows"] == 8
    assert summary["claim_activation_allowed_work_order_rows"] == 0
    assert summary["route_evidence_ready_input_rows"] == 2
    assert summary["route_evidence_current_accepted_claim_rows"] == 0


def test_mainline_work_order_route_register_classifies_current_gaps() -> None:
    payload = builder.build_payload()
    register = payload["route_evidence_register_rows"]
    assert {row["route_geometry_family"] for row in register} == {
        "ideal_rectangle",
        "trapezoid_tapered_sidewalls",
    }
    assert sum(row["evidence_class"] == "ready_route_input" for row in register) == 2
    assert sum(row["may_satisfy_route_formula_now"] for row in register) == 0
    assert sum(row["may_satisfy_yield_now"] for row in register) == 0
    assert sum(row["may_satisfy_detection_now"] for row in register) == 0
    assert {
        row["evidence_class"]
        for row in register
        if row["evidence_lane"] == "detector_blank_transfer"
    } == {"fixture_or_context_available_no_accepted_claim_evidence"}
    assert {
        row["evidence_class"]
        for row in register
        if row["evidence_lane"] == "wet_observation"
    } == {"fixture_or_contract_available_no_accepted_claim_evidence"}


def test_mainline_execution_work_order_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_WORK_ORDER_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_ROUTE_EVIDENCE_REGISTER_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_CLAIM_GUARD_ROWS_20260701.csv" in names
    assert "562_NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_20260701.md" in names


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_mainline_execution_work_order.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "--confirm-sidewall-mainline-execution-work-order is required" in result.stderr
