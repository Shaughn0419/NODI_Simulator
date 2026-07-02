from __future__ import annotations

from nodi_simulator.sidewall_detector_blank_transfer_execution_packet import (
    SIDEWALL_DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_CLAIM_BOUNDARY,
    build_detector_blank_transfer_execution_packet,
)


def _build():
    return build_detector_blank_transfer_execution_packet(
        intake_status={
            "artifact_id": "INTAKE",
            "disposition": "INTAKE_READY",
            "current_head": "a",
            "template_rows": 2,
            "accepted_transfer_rows": 0,
            "sidewall_specific_blank_trace_current_rows": 0,
            "detector_response_validation_current_rows": 0,
        },
        validation_status={
            "artifact_id": "VALIDATOR",
            "disposition": "VALIDATOR_READY",
            "current_head": "b",
            "accepted_fixture_rows": 2,
        },
        calibration_panel_status={
            "artifact_id": "PANEL",
            "disposition": "PANEL_READY",
            "current_head": "c",
            "panel_rows": 12,
            "sidewall_specific_blank_trace_current": False,
            "detector_response_validation_current": False,
        },
        promotion_ledger_status={
            "artifact_id": "PROMO",
            "disposition": "PROMO_READY",
            "current_head": "d",
            "refreshed_promotion_lane_rows": 18,
        },
        readiness_board_status={
            "artifact_id": "BOARD",
            "disposition": "BOARD_READY",
            "current_head": "e",
            "board_rows": 2,
        },
    )


def test_execution_packet_summarizes_detector_blank_lanes() -> None:
    rows, guards = _build()

    assert len(rows) == 5
    assert len(guards) == 5
    assert {row.claim_boundary for row in rows} == {
        SIDEWALL_DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_CLAIM_BOUNDARY
    }
    assert {row.claim_boundary for row in guards} == {
        SIDEWALL_DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_CLAIM_BOUNDARY
    }


def test_fixtures_and_panels_do_not_count_as_current_transfer_evidence() -> None:
    rows, _guards = _build()

    assert sum(row.candidate_or_fixture_rows for row in rows) == 36
    assert {row.current_accepted_transfer_rows for row in rows} == {0}
    assert {row.sidewall_specific_blank_trace_current for row in rows} == {False}
    assert {row.detector_response_validation_current for row in rows} == {False}
    assert {row.validated_transfer_current for row in rows} == {False}


def test_detection_route_and_yield_claims_remain_false() -> None:
    rows, guards = _build()

    assert {row.detection_probability_current for row in rows} == {False}
    assert {row.route_score_current for row in rows} == {False}
    assert {row.yield_current for row in rows} == {False}
    assert {row.claim_promoted_current for row in guards} == {False}
    assert {row.claim_promotion_allowed_now for row in guards} == {False}


def test_claim_guards_name_required_transfer_evidence() -> None:
    _rows, guards = _build()
    by_target = {row.promotion_target: row for row in guards}

    assert "blank denominator" in by_target[
        "sidewall_blank_false_positive_rate"
    ].required_evidence_before_true
    assert "threshold policy" in by_target[
        "detection_probability"
    ].required_evidence_before_true
    assert by_target["route_score_winner_JRC"].hard_fail_if_missing_evidence == (
        "route_score_true_without_detector_blank_and_wet_evidence"
    )
