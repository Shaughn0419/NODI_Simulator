from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import build_nodi_sidewall_geometry_effects_impact_matrix as builder


def test_geometry_effects_impact_matrix_builds_ready_state() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["dimension_recommendation_drift_rows"] == 84
    assert summary["selected_annulus_remap_rows"] == 210
    assert summary["interference_response_sensitivity_rows"] == 84
    assert summary["axis_synthesis_rows"] == 3
    assert summary["failed_alignment_check_rows"] == 0
    assert summary["source_missing_rows"] == 0
    assert summary["primary_answer_frame"] == (
        "dimension_window_annulus_range_and_interference_response_sensitivity"
    )
    assert summary["not_primary_answer_frame"] == "route_selection_or_scalar_scoreboard"


def test_dimension_matrix_preserves_formula_examples_and_negative_bottom() -> None:
    rows = builder.dimension_recommendation_drift_rows()

    w500_d900_theta85 = next(
        row
        for row in rows
        if row["W_top_nm"] == 500.0
        and row["depth_nm"] == 900.0
        and row["sidewall_deg_comsol"] == 85.0
        and row["particle_diameter_nm"] == 100.0
    )
    assert abs(w500_d900_theta85["W_bottom_unclipped_nm"] - 342.52) < 0.03
    assert w500_d900_theta85["baseline_pair_status"] == (
        "paired_rectangle_baseline_present"
    )
    assert w500_d900_theta85["center_accessible_area_fraction_vs_rectangle"] < 1.0

    closed_rows = [
        row for row in rows if float(row["W_bottom_unclipped_nm"]) < 0.0
    ]
    assert closed_rows
    assert all(row["closure_status"] == "geometry_closed" for row in closed_rows)


def test_dimension_matrix_covers_rectangle_and_tail_particles() -> None:
    rows = builder.dimension_recommendation_drift_rows()
    angles = {row["sidewall_deg_comsol"] for row in rows}
    depths = {row["depth_nm"] for row in rows}
    particles = {row["particle_diameter_nm"] for row in rows}

    assert {90.0, 85.0, 70.0}.issubset(angles)
    assert {900.0, 1200.0}.issubset(depths)
    assert {220.0, 300.0}.issubset(particles)
    assert any(row["channel_cross_section_model"] == "ideal_rectangle" for row in rows)
    assert any(
        row["dimension_recommendation_drift_class"]
        == "particle_tail_blocked_candidate"
        for row in rows
    )


def test_annulus_remap_uses_trapezoid_local_basis_and_block_guards() -> None:
    rows = builder.annulus_remap_rows()

    assert rows
    assert all(
        row["old_rectangle_basis"] == "rectangular_edge_norm_0p50_to_0p80"
        for row in rows
    )
    assert all(
        row["new_trapezoid_annulus_basis"]
        == "trapezoid_local_width_x_norm_plus_wall_normal_distance"
        for row in rows
    )
    assert all(row["no_neighbor_fill_for_blocked_bins"] is True for row in rows)
    assert any(row["bin_accessible"] is False for row in rows)
    assert any(row["annulus_range_shift"] == "local_annulus_narrowed" for row in rows)


def test_interference_response_rows_split_position_reference_detector_terms() -> None:
    payload = builder.build_payload()
    rows = payload["interference_response_sensitivity_rows"]

    assert rows
    assert all("position_distribution_effect_delta" in row for row in rows)
    assert all("reference_field_effect_delta" in row for row in rows)
    assert all("detector_overlap_annulus_effect_delta" in row for row in rows)
    assert all(row["true_W_eff_not_claimed"] is True for row in rows)
    assert all(row["not_detection_probability_current"] is True for row in rows)
    assert any(
        row["enhancement_delta_map_status"] == "candidate_response_changed"
        for row in rows
    )
    assert any(
        row["reference_field_solver_needed_flags"]
        == "sidewall_reference_response_solver_needed_for_quantitative_claim"
        for row in rows
    )


def test_no_forbidden_primary_columns_in_core_outputs() -> None:
    payload = builder.build_payload()
    forbidden_exact = {
        "winner",
        "route_score",
        "rank",
        "recommended_candidate",
        "detection_probability",
        "W_eff",
    }
    for table_key in (
        "dimension_recommendation_drift_rows",
        "selected_annulus_remap_rows",
        "interference_response_sensitivity_rows",
    ):
        columns = set()
        for row in payload[table_key]:
            columns.update(row)
        assert forbidden_exact.isdisjoint(columns)


def test_alignment_checks_are_hard_pass() -> None:
    payload = builder.build_payload()
    checks = payload["alignment_check_rows"]

    assert checks
    assert all(row["check_pass"] is True for row in checks)
    assert all(row["hard_fail_if_false"] is True for row in checks)
    assert any(
        row["check_name"] == "forbidden_primary_columns_absent" for row in checks
    )
    assert any(
        row["check_name"] == "interference_rows_split_position_reference_detector_terms"
        for row in checks
    )


def test_geometry_effects_impact_matrix_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_STATUS_20260702.json" in names
    assert (
        f"{builder.PREFIX}_DIMENSION_RECOMMENDATION_DRIFT_ROWS_20260702.csv"
        in names
    )
    assert f"{builder.PREFIX}_SELECTED_ANNULUS_REMAP_ROWS_20260702.csv" in names
    assert (
        f"{builder.PREFIX}_INTERFERENCE_RESPONSE_SENSITIVITY_ROWS_20260702.csv"
        in names
    )
    assert f"{builder.PREFIX}_AXIS_SYNTHESIS_ROWS_20260702.csv" in names
    assert f"589_{builder.PREFIX}_20260702.md" in names


def test_geometry_effects_impact_matrix_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_geometry_effects_impact_matrix.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-geometry-effects-impact-matrix is required" in (
        result.stderr + result.stdout
    )
