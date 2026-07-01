from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_detector_blank_calibration_panel as builder,
)


def test_detector_blank_calibration_panel_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["panel_rows"] == 12
    assert summary["route_evidence_matrix_rows"] == 2
    assert summary["promotion_update_rows"] == 3
    assert summary["ready_panel_rows"] == 12
    assert summary["ready_route_evidence_matrix_rows"] == 2
    assert summary["total_selected_annulus_events"] >= 100
    assert summary["sidewall_specific_blank_trace_current"] is False
    assert summary["detector_response_validation_current"] is False
    assert summary["detection_probability_current"] is False
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False
    assert summary["yield_current"] is False


def test_detector_blank_calibration_panel_rows_keep_candidate_boundary() -> None:
    rows = builder.build_payload()["panel_rows"]

    assert len(rows) == 12
    assert {row["route_candidate_id"] for row in rows} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    assert {row["wavelength_nm"] for row in rows} == {"404", "660"}
    assert {row["random_seed"] for row in rows} == {"601", "602", "603"}
    for row in rows:
        assert row["panel_evidence_status"] == builder.PANEL_READY_STATUS
        assert row["blank_guard_status"].startswith("nearest_blank_guard_finite")
        assert row["detection_probability_current"] == "false"
        assert row["route_score_current"] == "false"
        assert row["yield_current"] == "false"
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_detector_blank_route_evidence_matrix_is_not_route_score() -> None:
    rows = builder.build_payload()["route_evidence_matrix_rows"]

    assert len(rows) == 2
    for row in rows:
        assert row["route_evidence_matrix_status"] == builder.PANEL_AGGREGATE_READY_STATUS
        assert int(row["total_selected_annulus_events"]) >= 50
        assert row["detection_probability_current"] == "false"
        assert row["route_score_current"] == "false"
        assert row["winner_current"] == "false"
        assert row["yield_current"] == "false"
        assert "sidewall-specific blank traces" in row["next_required_evidence"]


def test_detector_blank_calibration_promotion_updates_cover_three_lanes() -> None:
    updates = builder.build_payload()["promotion_update_rows"]

    assert {row["target_ledger_lane"] for row in updates} == {
        "selected_annulus_detection_context",
        "blank_false_positive_trace",
        "detector_response_bridge",
    }
    for row in updates:
        assert row["target_claim_current"] == "false"
        assert "detection_probability" in row["blocked_promotion"]
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_detector_blank_calibration_panel_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_PANEL_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_ROUTE_EVIDENCE_MATRIX_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert (
        "541_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
