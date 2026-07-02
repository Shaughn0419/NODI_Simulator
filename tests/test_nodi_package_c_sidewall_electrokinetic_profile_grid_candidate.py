from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_electrokinetic_profile_grid_candidate as builder,
)


def test_profile_grid_candidate_builds_from_current_artifacts() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["case_rows"] == 5
    assert summary["cell_rows"] == 2205
    assert summary["mutation_check_rows"] == 5
    assert summary["claim_guard_rows"] == 5
    assert summary["rectangle_baseline_rows"] == 1
    assert summary["trapezoid_profile_grid_rows"] == 4
    assert summary["profile_aware_grid_current_rows"] == 5
    assert summary["mutation_check_pass_rows"] == 5
    assert summary["blocked_cell_weight_rows_total"] == 0
    assert summary["electrokinetic_solver_output_current_rows"] == 0
    assert summary["electrokinetic_weight_current_rows"] == 0
    assert summary["route_score_current_rows"] == 0
    assert summary["detection_probability_current_rows"] == 0


def test_profile_grid_candidate_outputs_expected_case_and_mutation_rows() -> None:
    payload = builder.build_payload()
    cases = {row["case_id"]: row for row in payload["case_rows"]}
    mutations = {row["check_type"]: row for row in payload["mutation_check_rows"]}

    assert "rectangle_theta90_baseline" in cases
    assert "trapezoid_theta85_base" in cases
    assert "trapezoid_theta80_theta_mutation" in cases
    assert cases["rectangle_theta90_baseline"]["channel_cross_section_model"] == "ideal_rectangle"
    assert cases["trapezoid_theta85_base"]["channel_cross_section_model"] == (
        "trapezoid_tapered_sidewalls"
    )
    assert {row["mutation_check_passed"] for row in mutations.values()} == {True}
    assert mutations["rectangle_limit"]["absolute_delta"] <= 1.0e-6
    assert mutations["theta_mutation"]["absolute_delta"] > 1.0
    assert mutations["blocked_bin_exclusion"]["baseline_value"] == 0.0


def test_profile_grid_candidate_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_CASE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_CELL_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_MUTATION_CHECK_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_CLAIM_GUARD_ROWS_20260701.csv" in names
    assert "563_NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_20260701.md" in names


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_electrokinetic_profile_grid_candidate.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-electrokinetic-profile-grid-candidate is required" in result.stderr
