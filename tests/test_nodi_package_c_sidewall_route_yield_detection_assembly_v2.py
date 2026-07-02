from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_route_yield_detection_assembly_v2 as builder,
)


def test_sidewall_route_yield_detection_assembly_v2_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["assembly_rows"] == 2
    assert summary["branch_rows"] == 8
    assert summary["route_geometry_families"] == (
        "ideal_rectangle;trapezoid_tapered_sidewalls"
    )
    assert summary["next_executable_branches"] == (
        "sidewall_detector_blank_transfer_validation"
    )
    assert summary["ready_input_lane_count_total"] == 6
    assert summary["candidate_context_lane_count_total"] == 10
    assert summary["missing_or_blocked_lane_count_total"] == 2
    assert summary["route_score_allowed_rows"] == 0
    assert summary["winner_allowed_rows"] == 0
    assert summary["yield_allowed_rows"] == 0
    assert summary["detection_probability_allowed_rows"] == 0
    assert summary["wet_pass_probability_allowed_rows"] == 0


def test_assembly_rows_bind_rectangle_and_taper_routes() -> None:
    rows = builder.build_payload()["assembly_rows"]

    assert len(rows) == 2
    by_family = {row["route_geometry_family"]: row for row in rows}
    assert set(by_family) == {"ideal_rectangle", "trapezoid_tapered_sidewalls"}
    for row in rows:
        assert row["assembly_status"] == builder.ASSEMBLY_NOT_CLAIM_READY_STATUS
        assert row["flow_split_qch_status"] == (
            "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting"
        )
        assert row["pressure_flow_validation_status"] == (
            "exact_w500_d900_pressure_flow_result_accepted_formal_qch_sidecar_ready"
        )
        assert row["selected_annulus_detection_context_status"] == (
            "expanded_selected_annulus_panel_available_not_probability"
        )
        assert row["detector_response_bridge_status"] == (
            "detector_response_panel_candidate_not_sidewall_calibrated"
        )
        assert row["blank_false_positive_trace_status"] == (
            "nearest_blank_guard_bound_to_panel_not_sidewall_specific"
        )
        assert row["wet_wall_interaction_status"] == (
            "wet_surface_observation_intake_ready_no_observations"
        )
        assert row["route_score_allowed"] is False
        assert row["yield_allowed"] is False
        assert row["detection_probability_allowed"] is False
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_branch_rows_prioritize_detector_blank_transfer_without_claims() -> None:
    rows = builder.build_payload()["branch_rows"]

    assert len(rows) == 8
    assert {row["branch_name"] for row in rows} == {
        "detection_probability_calibration",
        "route_candidate_assembly",
        "sidewall_detector_blank_transfer_validation",
        "wet_observation_bundle_intake",
    }
    detector_rows = [
        row
        for row in rows
        if row["branch_name"] == "sidewall_detector_blank_transfer_validation"
    ]
    assert len(detector_rows) == 2
    assert {row["implementation_can_start"] for row in detector_rows} == {True}
    for row in rows:
        assert row["target_claim_current"] is False
        assert "route_score" in row["claim_boundary"]
        assert "yield" in row["claim_boundary"]
        assert "detection_probability" in row["claim_boundary"]


def test_sidewall_route_yield_detection_assembly_v2_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_ASSEMBLY_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_BRANCH_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert (
        "546_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_V2_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
