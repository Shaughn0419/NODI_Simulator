from __future__ import annotations

from nodi_simulator.wet_optical_detection_evidence import (
    WET_OPTICAL_DETECTION_EVIDENCE_CLAIM_BOUNDARY,
    build_wet_optical_detection_context_rows,
)


def test_wet_optical_detection_context_maps_nearest_geometry_without_final_claims() -> None:
    rows = build_wet_optical_detection_context_rows(
        route_candidate_rows=[
            {
                "route_candidate_id": "ROUTE-CAND-001",
                "qch_sidecar_id": "QCH-CAND-001",
                "route_key": "route_rectangle_limit_theta90_D900_W500",
                "source_case_id": "rectangle_limit_theta90_D900_W500",
                "route_decision_candidate_metric": "0.2",
            }
        ],
        gold_rows=[
            {
                "width_nm": "600",
                "depth_nm": "1300",
                "detection_rate": "0.7",
                "stable_detection_rate": "0.65",
            }
        ],
        blank_rows=[
            {
                "blank_stage": "final",
                "blank_false_positive_wilson_ub_per_trace": "0.001",
            }
        ],
        feasible_rows=[
            {
                "width_nm": "600",
                "depth_nm": "1300",
                "case_feasible": "true",
            }
        ],
        ev_panel_rows=[
            {
                "width_nm": "600",
                "depth_nm": "1300",
                "weighted_stable_detection_rate": "0.55",
            }
        ],
        ranking_rows=[
            {
                "selected_annulus_lens_status": (
                    "missing_selected_annulus_columns_rerun_ev_panel_required"
                )
            }
        ],
    )

    assert len(rows) == 1
    row = rows[0]
    assert row.source_width_nm == 500
    assert row.source_depth_nm == 900
    assert row.sidewall_deg_comsol == 90.0
    assert row.geometry_match_level == "nearest_width_depth_context_only"
    assert row.nearest_detection_width_nm == 600
    assert row.nearest_detection_depth_nm == 1300
    assert row.detection_context_status.endswith("not_sidewall_specific")
    assert row.optical_context_status.endswith("not_sidewall_optical_solver")
    assert row.wet_context_status.endswith("not_wet_experiment")
    assert row.detection_context_weight == 0.25
    assert row.wet_context_weight == 0.25
    assert row.route_detection_context_candidate_metric == 0.0125
    assert row.selected_annulus_context_status == "selected_annulus_context_missing_rerun_required"
    assert row.detection_probability_current is False
    assert row.yield_current is False
    assert row.route_score_current is False
    assert row.winner_current is False
    assert row.claim_boundary == WET_OPTICAL_DETECTION_EVIDENCE_CLAIM_BOUNDARY


def test_wet_optical_detection_context_exact_match_gets_higher_context_weight() -> None:
    rows = build_wet_optical_detection_context_rows(
        route_candidate_rows=[
            {
                "route_candidate_id": "ROUTE-CAND-EXACT",
                "qch_sidecar_id": "QCH-CAND-EXACT",
                "route_key": "route_taper_theta85_D900_W500",
                "source_case_id": "taper_theta85_D900_W500",
                "route_decision_candidate_metric": "0.2",
            }
        ],
        gold_rows=[
            {
                "width_nm": "500",
                "depth_nm": "900",
                "detection_rate": "0.8",
                "stable_detection_rate": "0.7",
            }
        ],
        blank_rows=[
            {
                "blank_stage": "final",
                "blank_false_positive_wilson_ub_per_trace": "0.001",
            }
        ],
        feasible_rows=[],
        ev_panel_rows=[
            {
                "width_nm": "500",
                "depth_nm": "900",
                "weighted_stable_detection_rate": "0.6",
            }
        ],
        ranking_rows=[],
    )

    row = rows[0]
    assert row.sidewall_deg_comsol == 85.0
    assert row.geometry_match_level == "exact_width_depth_context_not_sidewall_specific"
    assert row.detection_context_weight == 0.5
    assert row.wet_context_weight == 0.25
    assert row.route_detection_context_candidate_metric == 0.025
    assert row.detection_probability_current is False
    assert row.yield_current is False
