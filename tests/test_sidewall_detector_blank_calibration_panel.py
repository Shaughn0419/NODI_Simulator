from __future__ import annotations

from nodi_simulator.sidewall_detector_blank_calibration_panel import (
    PANEL_AGGREGATE_READY_STATUS,
    PANEL_READY_STATUS,
    SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_CLAIM_BOUNDARY,
    SidewallDetectorBlankCalibrationPanelConfig,
    build_detector_blank_calibration_panel,
    detector_blank_calibration_promotion_update_rows,
)


def _detector_context_rows() -> list[dict[str, str]]:
    return [
        {
            "route_candidate_id": "ROUTE-CAND-001",
            "route_key": "route_rectangle_limit_theta90_D900_W500",
            "source_case_id": "rectangle_limit_theta90_D900_W500",
            "qch_sidecar_id": "QCH-CAND-001",
            "qch_flow_split_context_status": (
                "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting"
            ),
            "geometry_match_level": "nearest_width_depth_context_only",
            "nearest_detection_width_nm": "800",
            "nearest_detection_depth_nm": "710",
            "geometry_distance_nm": "490",
            "min_blank_false_positive_wilson_ub_per_trace": "0.000384012477767",
            "blank_false_positive_context_status": (
                "nearest_blank_context_available_not_sidewall_specific_validation"
            ),
            "detector_response_context_status": (
                "detector_identity_context_available_not_sidewall_response_validation"
            ),
            "optical_calibration_context_status": (
                "synthetic_reference_seed_available_not_blank_channel_calibration"
            ),
        },
        {
            "route_candidate_id": "ROUTE-CAND-002",
            "route_key": "route_taper_theta85_D900_W500",
            "source_case_id": "taper_theta85_D900_W500",
            "qch_sidecar_id": "QCH-CAND-002",
            "qch_flow_split_context_status": (
                "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting"
            ),
            "geometry_match_level": "nearest_width_depth_context_only",
            "nearest_detection_width_nm": "800",
            "nearest_detection_depth_nm": "710",
            "geometry_distance_nm": "490",
            "min_blank_false_positive_wilson_ub_per_trace": "0.000384012477767",
            "blank_false_positive_context_status": (
                "nearest_blank_context_available_not_sidewall_specific_validation"
            ),
            "detector_response_context_status": (
                "detector_identity_context_available_not_sidewall_response_validation"
            ),
            "optical_calibration_context_status": (
                "synthetic_reference_seed_available_not_blank_channel_calibration"
            ),
        },
    ]


def test_detector_blank_calibration_panel_expands_runs_and_aggregates_routes() -> None:
    panel_rows, matrix_rows = build_detector_blank_calibration_panel(
        detector_blank_context_rows=_detector_context_rows(),
        config=SidewallDetectorBlankCalibrationPanelConfig(
            n_events_per_run=32,
            random_seeds=(701, 702),
            wavelength_nm=(404,),
            min_selected_annulus_events_per_route=10,
        ),
    )

    assert len(panel_rows) == 4
    assert len(matrix_rows) == 2
    assert {row.route_candidate_id for row in matrix_rows} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    for row in panel_rows:
        assert row.panel_evidence_status == PANEL_READY_STATUS
        assert row.blank_guard_status.startswith("nearest_blank_guard_finite")
        assert row.selected_annulus_n_events > 0
        assert row.detection_probability_current is False
        assert row.route_score_current is False
        assert row.claim_boundary == SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_CLAIM_BOUNDARY
    for row in matrix_rows:
        assert row.route_evidence_matrix_status == PANEL_AGGREGATE_READY_STATUS
        assert row.total_selected_annulus_events >= 10
        assert row.detection_probability_current is False
        assert row.route_score_current is False
        assert row.yield_current is False


def test_detector_blank_calibration_promotion_updates_stay_non_claim() -> None:
    _panel_rows, matrix_rows = build_detector_blank_calibration_panel(
        detector_blank_context_rows=_detector_context_rows(),
        config=SidewallDetectorBlankCalibrationPanelConfig(
            n_events_per_run=16,
            random_seeds=(703,),
            wavelength_nm=(404,),
            min_selected_annulus_events_per_route=1,
        ),
    )
    updates = detector_blank_calibration_promotion_update_rows(matrix_rows)

    assert {row["target_ledger_lane"] for row in updates} == {
        "selected_annulus_detection_context",
        "blank_false_positive_trace",
        "detector_response_bridge",
    }
    for row in updates:
        assert row["target_claim_current"] is False
        assert "detection_probability" in row["blocked_promotion"]
        assert row["claim_boundary"] == SIDEWALL_DETECTOR_BLANK_CALIBRATION_PANEL_CLAIM_BOUNDARY
