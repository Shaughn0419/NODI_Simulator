from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_electrokinetic_grid_preflight as builder,
)


def test_electrokinetic_grid_preflight_builds_from_current_artifacts() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["preflight_rows"] == 4
    assert summary["claim_guard_rows"] == 6
    assert summary["rectangle_baseline_rows"] == 1
    assert summary["trapezoid_preflight_rows"] == 3
    assert summary["legacy_rectangle_path_allowed_rows"] == 1
    assert summary["profile_aware_grid_current_rows"] == 0
    assert summary["electrokinetic_solver_output_current_rows"] == 0
    assert summary["electrokinetic_weight_current_rows"] == 0
    assert summary["route_score_current_rows"] == 0
    assert summary["detection_probability_current_rows"] == 0
    assert summary["required_metadata_rows"] == 4
    assert summary["required_mutation_test_rows"] == 4


def test_preflight_rows_preserve_rectangle_and_block_trapezoid_rectangular_reuse() -> None:
    rows = builder.build_payload()["preflight_rows"]
    by_case = {row["case_id"]: row for row in rows}

    assert by_case["rectangle_baseline_boltzmann_grid_diagnostic"][
        "legacy_rectangle_path_allowed"
    ] is True
    assert by_case["trapezoid_theta85_profile_aware_grid_required"][
        "legacy_rectangle_path_allowed"
    ] is False
    assert by_case["trapezoid_theta85_profile_aware_grid_required"][
        "hard_fail_if"
    ] == "trapezoid_uses_rectangular_wall_distance_grid"
    assert by_case["trapezoid_metadata_required_zeta_ionic_strength"][
        "hard_fail_if"
    ] == "electrokinetic_weight_true_without_zeta_or_ionic_strength"


def test_preflight_rows_do_not_emit_solver_weights_or_detection() -> None:
    rows = builder.build_payload()["preflight_rows"]

    assert {row["electrokinetic_solver_output_current"] for row in rows} == {False}
    assert {row["electrokinetic_weight_current"] for row in rows} == {False}
    assert {row["route_score_current"] for row in rows} == {False}
    assert {row["detection_probability_current"] for row in rows} == {False}
    assert {row["claim_boundary"] for row in rows} == {builder.CLAIM_BOUNDARY}


def test_guard_rows_are_authorized_but_not_promoted() -> None:
    rows = builder.build_payload()["claim_guard_rows"]

    assert len(rows) == 6
    for row in rows:
        assert row["implementation_authorized"] is True
        assert row["claim_promoted_current"] is False
        assert row["claim_promotion_allowed_now"] is False
        assert row["required_evidence_before_true"]
        assert row["hard_fail_if_missing_evidence"]
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_electrokinetic_grid_preflight_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_CLAIM_GUARD_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "557_NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_electrokinetic_grid_preflight.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-electrokinetic-grid-preflight is required" in result.stderr
