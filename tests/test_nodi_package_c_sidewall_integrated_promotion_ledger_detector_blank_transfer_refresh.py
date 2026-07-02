from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_integrated_promotion_ledger_detector_blank_transfer_refresh as builder,
)


def test_detector_blank_transfer_ledger_refresh_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["refreshed_promotion_lane_rows"] == 18
    assert summary["detector_blank_transfer_delta_rows"] == 4
    assert summary["detector_transfer_intake_rows"] == 2
    assert summary["blank_transfer_intake_rows"] == 2
    assert summary["formal_qch_lane_rows_retained"] == 2
    assert summary["pressure_flow_validation_rows_retained"] == 2
    assert summary["selected_annulus_panel_rows_retained"] == 2
    assert summary["wet_observation_intake_rows_retained"] == 2
    assert summary["detection_probability_current"] is False
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False
    assert summary["yield_current"] is False


def test_detector_blank_transfer_refresh_updates_two_lanes() -> None:
    rows = builder.build_payload()["refreshed_promotion_lane_rows"]
    expected_status = "detector_blank_transfer_intake_ready_no_transfer_evidence"

    for lane in ("detector_response_bridge", "blank_false_positive_trace"):
        lane_rows = [row for row in rows if row["evidence_lane"] == lane]
        assert len(lane_rows) == 2
        assert {row["current_status"] for row in lane_rows} == {expected_status}
        assert all(
            row["source_artifact"].endswith(
                "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_ROUTE_TRANSFER_MATRIX_ROWS_20260701.csv"
            )
            for row in lane_rows
        )
        assert all(
            row["source_disposition"]
            == "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_READY_SCHEMA_NO_TRANSFER_EVIDENCE"
            for row in lane_rows
        )
        assert all(row["target_claim_current"] == "false" for row in lane_rows)
        assert all(row["not_detection_probability"] == "true" for row in lane_rows)


def test_detector_blank_transfer_refresh_retains_upstream_progress() -> None:
    rows = builder.build_payload()["refreshed_promotion_lane_rows"]

    expected = {
        "flow_split_qch": "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting",
        "pressure_flow_validation": (
            "exact_w500_d900_pressure_flow_result_accepted_formal_qch_sidecar_ready"
        ),
        "selected_annulus_detection_context": (
            "expanded_selected_annulus_panel_available_not_probability"
        ),
        "wet_wall_interaction": "wet_surface_observation_intake_ready_no_observations",
    }
    for lane, status in expected.items():
        assert {row["current_status"] for row in rows if row["evidence_lane"] == lane} == {
            status
        }


def test_detector_blank_transfer_delta_rows_keep_claims_false() -> None:
    deltas = builder.build_payload()["refresh_delta_rows"]

    assert len(deltas) == 4
    assert {delta["evidence_lane"] for delta in deltas} == {
        "blank_false_positive_trace",
        "detector_response_bridge",
    }
    for delta in deltas:
        assert delta["target_claim_current"] == "false"
        assert "detection_probability" in delta["blocked_use"]
        assert "route_score" in delta["blocked_use"]
        assert delta["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_detector_blank_transfer_ledger_refresh_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_PROMOTION_LANE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_DELTA_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert (
        "548_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_TRANSFER_REFRESH_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
