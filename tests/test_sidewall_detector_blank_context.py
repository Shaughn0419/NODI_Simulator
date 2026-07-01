from __future__ import annotations

from nodi_simulator.sidewall_detector_blank_context import (
    SIDEWALL_DETECTOR_BLANK_CONTEXT_CLAIM_BOUNDARY,
    build_detector_blank_context_rows,
    detector_blank_promotion_update_rows,
)


def test_detector_blank_context_joins_selected_annulus_and_qch_status() -> None:
    rows = build_detector_blank_context_rows(
        wet_context_rows=[
            {
                "route_candidate_id": "ROUTE-CAND-002",
                "route_key": "route_taper_theta85_D900_W500",
                "source_case_id": "taper_theta85_D900_W500",
                "qch_sidecar_id": "QCH-CAND-002",
                "geometry_match_level": "nearest_width_depth_context_only",
                "nearest_detection_width_nm": "800",
                "nearest_detection_depth_nm": "710",
                "geometry_distance_nm": "490",
                "min_blank_false_positive_wilson_ub_per_trace": "0.000384",
                "detection_context_status": "tsuyama_detection_lane_nearest_geometry_context_not_sidewall_specific",
                "optical_context_status": "paper_aligned_reference_context_available_not_sidewall_optical_solver",
                "wet_context_status": "ev_weighted_panel_surrogate_context_available_not_wet_experiment",
            }
        ],
        selected_annulus_rows=[
            {
                "case_id": "taper_theta85_D900_W500",
                "selected_annulus_context_status": "selected_annulus_context_available_small_n_not_probability",
                "selected_annulus_n_events": "7",
                "selected_annulus_n_detected": "5",
                "selected_annulus_context_rate": "0.714285714286",
            }
        ],
        promotion_lane_rows=[
            {
                "route_candidate_id": "ROUTE-CAND-002",
                "evidence_lane": "flow_split_qch",
                "current_status": "w500_d900_grid_refined_split_candidate_absolute_q_requires_validation",
            }
        ],
        optical_readiness_rows=[
            {
                "evidence_lane": "detector_response_bridge",
                "current_status": "not_detector_response_validation",
            },
            {
                "evidence_lane": "blank_channel_reference_amplitude_phase",
                "current_status": "synthetic_seed_available_not_experimental",
            },
        ],
    )

    assert len(rows) == 1
    row = rows[0]
    assert row.detector_blank_lane_status == "detector_blank_context_available_not_probability"
    assert row.selected_annulus_n_events == 7
    assert row.qch_flow_split_context_status == (
        "w500_d900_grid_refined_split_candidate_absolute_q_requires_validation"
    )
    assert row.blank_false_positive_context_status == (
        "nearest_blank_context_available_not_sidewall_specific_validation"
    )
    assert row.detector_response_context_status == (
        "detector_identity_context_available_not_sidewall_response_validation"
    )
    assert row.detection_probability_current is False
    assert row.route_score_current is False
    assert row.claim_boundary == SIDEWALL_DETECTOR_BLANK_CONTEXT_CLAIM_BOUNDARY


def test_detector_blank_context_blocks_when_selected_annulus_missing() -> None:
    rows = build_detector_blank_context_rows(
        wet_context_rows=[
            {
                "route_candidate_id": "ROUTE-CAND-001",
                "source_case_id": "rectangle_limit_theta90_D900_W500",
                "min_blank_false_positive_wilson_ub_per_trace": "0.000384",
            }
        ],
        selected_annulus_rows=[],
        promotion_lane_rows=[],
        optical_readiness_rows=[],
    )

    assert rows[0].detector_blank_lane_status == "blocked_selected_annulus_context_missing"
    assert rows[0].detection_probability_current is False


def test_detector_blank_promotion_updates_are_context_only() -> None:
    context_rows = build_detector_blank_context_rows(
        wet_context_rows=[
            {
                "route_candidate_id": "ROUTE-CAND-001",
                "source_case_id": "rectangle_limit_theta90_D900_W500",
                "min_blank_false_positive_wilson_ub_per_trace": "0.000384",
            }
        ],
        selected_annulus_rows=[
            {
                "case_id": "rectangle_limit_theta90_D900_W500",
                "selected_annulus_context_status": "selected_annulus_context_available_small_n_not_probability",
            }
        ],
        promotion_lane_rows=[],
        optical_readiness_rows=[],
    )
    updates = detector_blank_promotion_update_rows(context_rows)

    assert {row["target_ledger_lane"] for row in updates} == {
        "blank_false_positive_trace",
        "detector_response_bridge",
    }
    for row in updates:
        assert row["target_claim_current"] is False
        assert "detection_probability" in row["blocked_promotion"]
        assert row["claim_boundary"] == SIDEWALL_DETECTOR_BLANK_CONTEXT_CLAIM_BOUNDARY
