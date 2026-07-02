from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_detector_wet_route_binding_closure as builder,
)


def test_detector_wet_route_binding_closure_builds_from_current_artifacts() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["closure_rows"] == 2
    assert summary["guard_rows"] == 5
    assert summary["route_formula_binding_authorized_rows"] == 2
    assert summary["route_formula_binding_ready_rows"] == 0
    assert summary["qch_ready_rows"] == 2
    assert summary["selected_annulus_ready_rows"] == 2
    assert summary["runtime_guard_ready_rows"] == 2
    assert summary["profile_grid_candidate_ready_rows"] == 2
    assert summary["detector_validator_hardened_rows"] == 2
    assert summary["wet_validator_hardened_rows"] == 2
    assert summary["detector_accepted_transfer_rows_total"] > 0
    assert summary["wet_accepted_observation_rows_total"] == 0
    assert summary["activation_allowed_guard_rows"] == 1
    assert summary["activation_allowed_targets"] == "detection_probability"


def test_closure_rows_keep_claims_false_and_geometry_parallel() -> None:
    payload = builder.build_payload()
    rows = payload["closure_rows"]
    assert {row["route_geometry_family"] for row in rows} == {
        "ideal_rectangle",
        "trapezoid_tapered_sidewalls",
    }
    for row in rows:
        assert row["route_formula_binding_status"] == (
            "blocked_accepted_detector_blank_and_wet_rows_required"
        )
        assert row["route_score_current"] is False
        assert row["winner_current"] is False
        assert row["yield_current"] is False
        assert row["detection_probability_current"] is False
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_detector_wet_route_binding_closure_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_GUARD_ROWS_20260701.csv" in names
    assert "565_NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_20260701.md" in names


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_detector_wet_route_binding_closure.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-detector-wet-route-binding-closure is required" in result.stderr
