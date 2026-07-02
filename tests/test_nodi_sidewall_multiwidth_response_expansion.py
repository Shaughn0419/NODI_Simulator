from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from nodi_simulator.nodi_comsol_next_artifacts import (
    PRS_APPROVED_DIAMETERS_NM,
    PRS_APPROVED_ROUTE_MATRIX,
)
from tools.audits import build_nodi_sidewall_multiwidth_response_expansion as builder


def test_multiwidth_response_expansion_builds_ready_state() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["prs_approved_route_count"] == len(PRS_APPROVED_ROUTE_MATRIX)
    assert summary["prs_approved_diameter_count"] == len(PRS_APPROVED_DIAMETERS_NM)
    assert summary["dimension_window_rows"] == (
        len(PRS_APPROVED_ROUTE_MATRIX)
        * len(builder.SIDEWALL_DEG_COMSOL_GRID)
        * len(PRS_APPROVED_DIAMETERS_NM)
    )
    assert summary["trapezoid_local_response_bin_rows"] == (
        len(PRS_APPROVED_ROUTE_MATRIX)
        * len(builder.SIDEWALL_DEG_COMSOL_GRID)
        * len(builder.FOCUS_RESPONSE_PARTICLE_DIAMETERS_NM)
        * len(builder.U_NORM_GRID)
        * len(builder.X_BIN_SPECS)
    )
    assert summary["selected_annulus_expansion_rows"] > 0
    assert summary["failed_alignment_check_rows"] == 0
    assert summary["source_missing_rows"] == 0


def test_dimension_window_uses_prs_route_and_diameter_grids() -> None:
    rows = builder.dimension_window_rows()
    routes = {
        (int(row["lambda_nm"]), int(row["W_nominal_nm"]), int(row["D_nm"]))
        for row in rows
    }
    diameters = {int(row["diameter_nm"]) for row in rows}

    assert routes == set(PRS_APPROVED_ROUTE_MATRIX)
    assert diameters == set(PRS_APPROVED_DIAMETERS_NM)
    assert any(row["sidewall_deg_comsol"] == 90.0 for row in rows)
    assert any(row["sidewall_deg_comsol"] == 85.0 for row in rows)
    assert any(row["sidewall_deg_comsol"] == 70.0 for row in rows)
    assert all(row["route_scope"] == "prs_approved_route_matrix" for row in rows)
    assert all(row["W_top_semantics"] == "runtime_top_aperture_surrogate" for row in rows)
    assert all("closure_depth_nm" in row for row in rows)
    assert any(
        row["dimension_window_shift_candidate"] == "increase_top_width_candidate"
        for row in rows
    )
    assert any(
        row["dimension_window_shift_candidate"]
        == "avoid_depth_angle_pair_candidate"
        for row in rows
    )


def test_w500_d900_theta85_formula_and_compensation_proxy() -> None:
    rows = builder.dimension_window_rows()
    row = next(
        row
        for row in rows
        if row["lambda_nm"] == 404
        and row["W_nominal_nm"] == 500
        and row["D_nm"] == 900
        and row["sidewall_deg_comsol"] == 85.0
        and row["diameter_nm"] == 100
    )

    assert abs(row["W_bottom_unclipped_nm"] - 342.52) < 0.03
    assert row["center_accessible_area_fraction_vs_rectangle"] < 1.0
    assert row["top_width_compensation_proxy_nm"] > 0.0


def test_response_bins_use_prs_sidewall_v2_geometry_fields() -> None:
    rows = builder.response_bin_rows()
    sample = rows[0]

    for field in (
        "response_surface_artifact_version",
        "row_scope",
        "route_id_nodi",
        "lambda_nm",
        "W_nominal_nm",
        "W_top_nm",
        "W_top_semantics",
        "D_nm",
        "depth_nm",
        "diameter_nm",
        "bin_id",
        "selected_annulus_rectangular_v1",
        "selected_annulus_trapezoid_wall_distance_v1",
        "x_nm",
        "u_nm",
        "x_local_norm",
        "d_nearest_wall_nm",
        "bin_accessible",
        "bin_particle_center_support_status",
        "response_value_status",
        "response_proxy_value",
        "not_comsol_transport_distribution",
        "not_detection_probability",
        "not_route_selection_claim",
        "not_qch_weighted",
        "decision_use_allowed",
        "decision_use_allowed_role",
        "decision_use_allowed_prs_bin",
    ):
        assert field in sample

    assert all(row["route_scope"] == "prs_approved_route_matrix" for row in rows)
    assert all(row["decision_use_allowed"] is False for row in rows)
    assert all(row["decision_use_allowed_prs_bin"] is False for row in rows)
    assert any(row["bin_id"] == "selected_annulus_0p5_0p8" for row in rows)
    assert any(row["response_value_status"] == "blocked_bin_no_response_value" for row in rows)
    assert any(
        row["interference_impact_status"] == "sidewall_response_shift_candidate"
        for row in rows
    )


def test_blocked_response_bins_have_blank_response_values() -> None:
    rows = builder.response_bin_rows()
    blocked = [
        row for row in rows if row["response_value_status"] == "blocked_bin_no_response_value"
    ]

    assert blocked
    assert all(row["response_proxy_value"] is None for row in blocked)
    assert all(row["signal_response_proxy"] is None for row in blocked)
    assert all(row["neighbor_fill_used"] is False for row in blocked)


def test_selected_annulus_expansion_summarizes_accessible_slices() -> None:
    annulus_rows = builder.selected_annulus_expansion_rows(builder.response_bin_rows())

    assert annulus_rows
    assert all(row["annulus_edge_norm_min"] == 0.5 for row in annulus_rows)
    assert all(row["annulus_edge_norm_max"] == 0.8 for row in annulus_rows)
    assert all(row["W_top_semantics"] == "runtime_top_aperture_surrogate" for row in annulus_rows)
    assert all(row["route_scope"] == "prs_approved_route_matrix" for row in annulus_rows)
    assert all(row["no_neighbor_fill_for_blocked_bins"] is True for row in annulus_rows)
    assert any(row["annulus_mapping_status"] == "blocked_or_partial" for row in annulus_rows)


def test_no_forbidden_primary_columns_in_590_outputs() -> None:
    payload = builder.build_payload()
    forbidden_exact = {
        "winner",
        "route_score",
        "rank",
        "recommended_candidate",
        "detection_probability",
        "W_eff",
        "yield",
        "q_ch_eta",
    }
    for table_key in (
        "dimension_window_rows",
        "trapezoid_local_response_bin_rows",
        "selected_annulus_expansion_rows",
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
        row["check_name"] == "route_matrix_matches_prs_approved_routes"
        for row in checks
    )
    assert any(
        row["check_name"] == "blocked_response_bins_have_blank_proxy_values"
        for row in checks
    )


def test_multiwidth_response_expansion_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_DIMENSION_WINDOW_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_TRAPEZOID_LOCAL_RESPONSE_BIN_ROWS_20260702.csv" in names
    assert f"{builder.PREFIX}_SELECTED_ANNULUS_EXPANSION_ROWS_20260702.csv" in names
    assert f"590_{builder.PREFIX}_20260702.md" in names


def test_multiwidth_response_expansion_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_multiwidth_response_expansion.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-multiwidth-response-expansion is required" in (
        result.stderr + result.stdout
    )
