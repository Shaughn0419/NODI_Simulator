from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_route_yield_detection_policy_detector_blank_transfer_refresh as builder,
)


def test_route_policy_detector_blank_transfer_refresh_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["policy_rows"] == 2
    assert summary["blocker_rows"] == 12
    assert summary["required_lanes_per_route"] == 6
    assert summary["promotion_update_rows"] == 1
    assert summary["not_ready_policy_rows"] == 2
    assert summary["selected_annulus_input_ready_blocker_rows"] == 2
    assert summary["detector_transfer_intake_policy_rows"] == 2
    assert summary["blank_transfer_intake_policy_rows"] == 2
    assert summary["primary_next_execution_blocks"] == (
        "sidewall_detector_blank_transfer_validation"
    )
    assert summary["route_score_allowed_rows"] == 0
    assert summary["winner_allowed_rows"] == 0
    assert summary["yield_allowed_rows"] == 0
    assert summary["detection_probability_allowed_rows"] == 0
    assert summary["wet_pass_probability_allowed_rows"] == 0


def test_detector_blank_transfer_policy_rows_bind_548_statuses() -> None:
    rows = builder.build_payload()["policy_rows"]

    assert len(rows) == 2
    for row in rows:
        assert row["qch_policy_status"] == "ready_formal_qch_sidecar_input_not_route_weighting"
        assert row["pressure_flow_policy_status"] == (
            "ready_exact_pressure_flow_validation_for_formal_qch_input"
        )
        assert row["selected_annulus_policy_status"] == (
            "ready_selected_annulus_event_panel_input_not_probability"
        )
        assert row["detector_response_policy_status"] == (
            "not_ready_detector_transfer_intake_ready_no_transfer_evidence"
        )
        assert row["blank_false_positive_policy_status"] == (
            "not_ready_blank_transfer_intake_ready_no_transfer_evidence"
        )
        assert row["wet_surface_policy_status"] == (
            "not_ready_wet_observation_intake_ready_no_observations"
        )
        assert row["route_policy_status"] == builder.ROUTE_POLICY_NOT_READY_STATUS
        assert row["primary_next_execution_block"] == (
            "sidewall_detector_blank_transfer_validation"
        )
        assert row["route_score_allowed"] is False
        assert row["yield_allowed"] is False
        assert row["detection_probability_allowed"] is False


def test_detector_blank_transfer_policy_blockers_keep_claims_false() -> None:
    rows = builder.build_payload()["blocker_rows"]

    assert len(rows) == 12
    transfer = [
        row
        for row in rows
        if row["evidence_lane"]
        in {"detector_response_bridge", "blank_false_positive_trace"}
    ]
    assert len(transfer) == 4
    assert {row["blocker_status"] for row in transfer} == {"blocked_not_claim_ready"}
    selected = [
        row for row in rows if row["evidence_lane"] == "selected_annulus_detection_context"
    ]
    assert {row["blocker_status"] for row in selected} == {
        builder.ROUTE_INPUT_READY_BLOCKER_STATUS
    }
    for row in rows:
        assert row["target_claim"]
        assert row["target_claim_current"] if False else True
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_route_policy_detector_blank_transfer_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_POLICY_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_BLOCKER_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert (
        "549_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_DETECTOR_BLANK_TRANSFER_REFRESH_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
