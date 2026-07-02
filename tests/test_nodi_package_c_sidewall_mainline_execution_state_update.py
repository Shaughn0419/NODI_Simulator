from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_mainline_execution_state_update as builder,
)


def test_mainline_execution_state_update_builds_from_current_artifacts() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["work_order_state_rows"] == 8
    assert summary["route_evidence_state_rows"] == 14
    assert summary["state_guard_rows"] == 5
    assert summary["profile_grid_integrated_rows"] == 1
    assert summary["runtime_substep_integrated_rows"] == 1
    assert summary["candidate_profile_grid_route_rows"] == 2
    assert summary["guarded_runtime_smoke_route_rows"] == 2
    assert summary["flow_solver_candidate_route_rows"] == 1
    assert summary["route_score_activation_rows"] == 0
    assert summary["yield_activation_rows"] == 0
    assert summary["detection_activation_rows"] == 0


def test_state_update_rows_identify_remaining_external_input_lanes() -> None:
    payload = builder.build_payload()
    by_work = {
        row["work_order_id"]: row for row in payload["work_order_state_rows"]
    }

    assert by_work["WO-003-electrokinetic-profile-grid"]["current_state"] == (
        "candidate_profile_grid_available_not_solver"
    )
    assert by_work["WO-007-runtime-substep-policy"]["current_state"] == (
        "guarded_runtime_smoke_available_stress_blocked"
    )
    assert by_work["WO-002-comsol-target-binding"]["current_state"] == (
        "open_target_binding_required"
    )
    assert by_work["WO-004-detector-blank-transfer"]["current_state"] == (
        "open_accepted_transfer_rows_required"
    )
    assert by_work["WO-005-wet-observation"]["current_state"] == (
        "open_accepted_wet_rows_required"
    )


def test_state_update_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_WORK_ORDER_STATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_ROUTE_EVIDENCE_STATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATE_GUARD_ROWS_20260701.csv" in names
    assert "564_NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_20260701.md" in names


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_mainline_execution_state_update.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-mainline-execution-state-update is required" in result.stderr
