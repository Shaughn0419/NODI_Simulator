from __future__ import annotations

from pathlib import Path

from nodi_simulator.sidewall_route_yield_detection_policy import (
    ROUTE_INPUT_READY_BLOCKER_STATUS,
    ROUTE_POLICY_NOT_READY_STATUS,
)
from tools.audits import (
    build_nodi_package_c_sidewall_route_yield_detection_policy_wet_observation_refresh as builder,
)


def test_sidewall_route_policy_wet_observation_refresh_packet_builds() -> None:
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
    assert summary["selected_annulus_panel_policy_rows"] == 2
    assert summary["detector_panel_policy_rows"] == 2
    assert summary["blank_panel_policy_rows"] == 2
    assert summary["wet_observation_intake_policy_rows"] == 2
    assert summary["primary_next_execution_blocks"] == (
        "sidewall_detector_blank_transfer_validation"
    )
    assert summary["route_score_allowed_rows"] == 0
    assert summary["winner_allowed_rows"] == 0
    assert summary["yield_allowed_rows"] == 0
    assert summary["detection_probability_allowed_rows"] == 0
    assert summary["wet_pass_probability_allowed_rows"] == 0


def test_policy_rows_bind_wet_observation_integrated_ledger_statuses() -> None:
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
            "not_ready_detector_response_panel_candidate_needs_sidewall_calibration"
        )
        assert row["blank_false_positive_policy_status"] == (
            "not_ready_blank_guard_panel_bound_needs_sidewall_specific_transfer"
        )
        assert row["wet_surface_policy_status"] == (
            "not_ready_wet_observation_intake_ready_no_observations"
        )
        assert row["route_policy_status"] == ROUTE_POLICY_NOT_READY_STATUS
        assert row["primary_next_execution_block"] == (
            "sidewall_detector_blank_transfer_validation"
        )
        assert row["route_score_allowed"] is False
        assert row["winner_allowed"] is False
        assert row["yield_allowed"] is False
        assert row["detection_probability_allowed"] is False
        assert row["wet_pass_probability_allowed"] is False
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_wet_observation_policy_blockers_reflect_current_inputs() -> None:
    rows = builder.build_payload()["blocker_rows"]

    assert len(rows) == 12
    assert {row["evidence_lane"] for row in rows} == set(builder.REQUIRED_LANES)
    selected = [
        row for row in rows if row["evidence_lane"] == "selected_annulus_detection_context"
    ]
    assert {row["blocker_status"] for row in selected} == {
        ROUTE_INPUT_READY_BLOCKER_STATUS
    }
    still_blocked = [
        row
        for row in rows
        if row["evidence_lane"]
        in {
            "detector_response_bridge",
            "blank_false_positive_trace",
            "wet_wall_interaction",
        }
    ]
    assert {row["blocker_status"] for row in still_blocked} == {"blocked_not_claim_ready"}
    for row in rows:
        assert row["next_required_evidence"]
        assert row["hard_fail_if_promoted_without"]
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_wet_observation_route_policy_promotion_update_remains_not_claim_ready() -> None:
    updates = builder.build_payload()["promotion_update_rows"]

    assert len(updates) == 1
    update = updates[0]
    assert update["target_ledger_lane"] == "integrated_route_ledger"
    assert update["new_context_status"] == (
        "route_yield_detection_policy_defined_not_ready_for_claims"
    )
    assert update["target_claim_current"] == "false"
    assert "route_score" in update["blocked_promotion"]
    assert "yield" in update["blocked_promotion"]
    assert "detection_probability" in update["blocked_promotion"]
    assert update["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_sidewall_route_policy_wet_observation_outputs_manifest(tmp_path: Path) -> None:
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
        "545_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_WET_OBSERVATION_REFRESH_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
