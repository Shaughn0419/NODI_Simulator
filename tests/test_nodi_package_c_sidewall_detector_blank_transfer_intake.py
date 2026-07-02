from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_sidewall_detector_blank_transfer_intake as builder


def test_detector_blank_transfer_intake_packet_builds_with_candidate_transfer_input() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.ACCEPTED_DISPOSITION
    assert summary["optional_transfer_input_present"] is True
    assert summary["intake_rows"] == 2
    assert summary["route_transfer_matrix_rows"] == 2
    assert summary["template_rows"] == 2
    assert summary["promotion_update_rows"] == 2
    assert summary["accepted_transfer_rows"] == 2
    assert summary["accepted_transfer_matrix_rows"] == 2
    assert summary["no_transfer_matrix_rows"] == 0
    assert summary["sidewall_specific_blank_trace_current_rows"] == 0
    assert summary["validated_transfer_current_rows"] == 2
    assert summary["detector_response_validation_current_rows"] == 2
    assert summary["detection_probability_current"] is False
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False
    assert summary["yield_current"] is False


def test_detector_blank_transfer_rows_bind_detector_panel_routes() -> None:
    payload = builder.build_payload()
    intake_rows = payload["intake_rows"]
    matrix_rows = payload["route_transfer_matrix_rows"]

    assert {row["route_candidate_id"] for row in intake_rows} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    assert {row["source_panel_matrix_row_id"] for row in intake_rows} == {
        "DB-CAL-MATRIX-ROUTE-CAND-001",
        "DB-CAL-MATRIX-ROUTE-CAND-002",
    }
    assert {row["transfer_validation_status"] for row in intake_rows} == {
        "detector_blank_transfer_accepted_candidate_not_detection_probability"
    }
    assert {row["route_transfer_matrix_status"] for row in matrix_rows} == {
        builder.ROUTE_MATRIX_ACCEPTED_STATUS
    }
    for row in intake_rows:
        assert row["detection_probability_current"] is False
        assert row["route_score_current"] is False
        assert row["yield_current"] is False
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_detector_blank_transfer_promotion_updates_do_not_open_claims() -> None:
    updates = builder.build_payload()["promotion_update_rows"]

    assert {update["target_ledger_lane"] for update in updates} == {
        "blank_false_positive_trace",
        "detector_response_bridge",
    }
    assert {update["new_context_status"] for update in updates} == {
        builder.ROUTE_MATRIX_ACCEPTED_STATUS
    }
    for update in updates:
        assert update["target_claim_current"] is False
        assert "detection_probability" in update["blocked_promotion"]
        assert "route_score" in update["blocked_promotion"]
        assert update["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_detector_blank_transfer_intake_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_INTAKE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_ROUTE_TRANSFER_MATRIX_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_TEMPLATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert (
        "547_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
