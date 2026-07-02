from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_route_formula_binding_preflight as builder,
)


def test_route_formula_preflight_builds_from_current_artifacts() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DETECTOR_READY_DISPOSITION
    assert summary["preflight_rows"] == 2
    assert summary["branch_rows"] == 12
    assert summary["guard_rows"] == 5
    assert summary["source_566_accepted_exact_pressure_flow_rows"] == 2
    assert summary["source_566_route_formula_qch_branch_ready_rows"] == 2
    assert summary["qch_branch_ready_rows"] == 2
    assert summary["exact_pressure_flow_ready_rows"] == 2
    assert summary["selected_annulus_ready_rows"] == 2
    assert summary["runtime_substep_guard_ready_rows"] == 2
    assert summary["detector_hardening_fixture_rows"] == 2
    assert summary["wet_hardening_fixture_rows"] == 14
    assert summary["detector_accepted_transfer_rows_total"] == 2
    assert summary["wet_accepted_observation_rows_total"] == 0
    assert summary["detector_branch_ready_rows"] == 2
    assert summary["wet_branch_ready_rows"] == 0
    assert summary["route_formula_claim_ready_rows"] == 0
    assert summary["route_score_current"] is False
    assert summary["wet_pass_probability_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False


def test_preflight_rows_have_parallel_geometry_and_blockers() -> None:
    payload = builder.build_payload()
    rows = payload["preflight_rows"]

    assert {row["route_geometry_family"] for row in rows} == {
        "ideal_rectangle",
        "trapezoid_tapered_sidewalls",
    }
    assert {row["route_formula_input_ready_count"] for row in rows} == {5}
    assert {row["route_formula_required_input_count"] for row in rows} == {6}
    assert {row["route_formula_binding_status"] for row in rows} == {
        "blocked_detector_blank_and_wet_accepted_evidence_required"
    }


def test_route_formula_preflight_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_PREFLIGHT_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_BRANCH_ROWS_20260701.csv" in names
    assert f"567_{builder.PREFIX}_20260701.md" in names


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_route_formula_binding_preflight.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-route-formula-binding-preflight is required" in result.stderr
