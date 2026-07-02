from __future__ import annotations

from nodi_simulator.sidewall_detector_blank_transfer_intake import (
    ROUTE_MATRIX_ACCEPTED_STATUS,
    ROUTE_MATRIX_NO_TRANSFER_STATUS,
    TRANSFER_ACCEPTED_STATUS,
    TRANSFER_MISSING_STATUS,
    build_detector_blank_transfer_intake,
    detector_blank_transfer_promotion_update_rows,
    detector_blank_transfer_template_rows,
)


def _panel_rows() -> list[dict[str, str]]:
    return [
        {
            "matrix_row_id": f"DB-CAL-MATRIX-{route_id}",
            "route_candidate_id": route_id,
            "route_key": route_key,
            "source_case_id": source_case,
            "qch_sidecar_id": f"QCH-{route_id}",
            "total_selected_annulus_events": "168",
            "blank_guard_status": "nearest_blank_guard_finite_below_threshold_not_sidewall_specific",
            "detector_response_context_status": (
                "detector_identity_context_available_not_sidewall_response_validation"
            ),
            "route_evidence_matrix_status": (
                "detector_blank_route_evidence_matrix_candidate_ready_not_probability"
            ),
        }
        for route_id, route_key, source_case in (
            (
                "ROUTE-CAND-001",
                "route_rectangle_limit_theta90_D900_W500",
                "rectangle_limit_theta90_D900_W500",
            ),
            (
                "ROUTE-CAND-002",
                "route_taper_theta85_D900_W500",
                "taper_theta85_D900_W500",
            ),
        )
    ]


def test_detector_blank_transfer_intake_defaults_to_no_transfer_evidence() -> None:
    intake_rows, matrix_rows = build_detector_blank_transfer_intake(
        panel_matrix_rows=_panel_rows()
    )

    assert len(intake_rows) == 2
    assert len(matrix_rows) == 2
    assert {row.transfer_validation_status for row in intake_rows} == {
        TRANSFER_MISSING_STATUS
    }
    assert {row.route_transfer_matrix_status for row in matrix_rows} == {
        ROUTE_MATRIX_NO_TRANSFER_STATUS
    }
    for row in intake_rows:
        assert row.accepted_transfer_current is False
        assert row.detection_probability_current is False
        assert row.route_score_current is False
        assert row.yield_current is False


def test_detector_blank_transfer_intake_accepts_complete_sidewall_transfer() -> None:
    transfer_rows = [
        {
            "route_candidate_id": "ROUTE-CAND-001",
            "transfer_artifact_id": "transfer-001",
            "blank_trace_artifact_id": "blank-001",
            "blank_trace_sha256": "a" * 64,
            "detector_response_artifact_id": "detector-001",
            "detector_response_sha256": "b" * 64,
            "blank_trace_geometry_match_level": "sidewall_specific",
            "detector_response_model_id": "detector-response-v1",
            "false_positive_rate_estimate": "0.0001",
            "false_positive_rate_ci_low": "0.0",
            "false_positive_rate_ci_high": "0.0004",
            "n_blank_traces": "3",
            "n_detector_calibration_runs": "3",
            "controls_status": "controls_pass",
            "uncertainty_model": "wilson_interval",
            "pre_registered_rule_status": "pre_registered",
        }
    ]
    intake_rows, matrix_rows = build_detector_blank_transfer_intake(
        panel_matrix_rows=_panel_rows(),
        transfer_input_rows=transfer_rows,
    )

    accepted = [
        row for row in intake_rows if row.transfer_validation_status == TRANSFER_ACCEPTED_STATUS
    ]
    assert len(accepted) == 1
    assert accepted[0].accepted_transfer_current is True
    assert accepted[0].detection_probability_current is False
    accepted_matrix = [
        row for row in matrix_rows if row.route_transfer_matrix_status == ROUTE_MATRIX_ACCEPTED_STATUS
    ]
    assert len(accepted_matrix) == 1


def test_detector_blank_transfer_template_and_promotion_updates_are_not_claims() -> None:
    intake_rows, matrix_rows = build_detector_blank_transfer_intake(
        panel_matrix_rows=_panel_rows()
    )
    templates = detector_blank_transfer_template_rows(_panel_rows())
    updates = detector_blank_transfer_promotion_update_rows(matrix_rows)

    assert len(intake_rows) == 2
    assert len(templates) == 2
    assert {update["target_ledger_lane"] for update in updates} == {
        "blank_false_positive_trace",
        "detector_response_bridge",
    }
    assert {update["new_context_status"] for update in updates} == {
        ROUTE_MATRIX_NO_TRANSFER_STATUS
    }
    for update in updates:
        assert update["target_claim_current"] is False
        assert "detection_probability" in update["blocked_promotion"]
        assert "route_score" in update["blocked_promotion"]
