from __future__ import annotations

from nodi_simulator.sidewall_pressure_flow_validation_harness import (
    SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_CLAIM_BOUNDARY,
    build_pressure_flow_validation_control_rows,
    build_pressure_flow_validation_request_rows,
    pressure_flow_validation_promotion_update_rows,
)


def _grid_rows() -> list[dict[str, str]]:
    return [
        {
            "case_id": "rectangle_limit_theta90_D900_W500",
            "grid_nx": "41",
            "grid_nu": "41",
            "sidewall_deg_comsol": "90",
            "sidewall_taper_angle_deg_nodi": "0",
            "top_width_nm": "500",
            "depth_nm": "900",
            "pressure_drop_Pa": "1000",
            "solver_status": "candidate_solver_output",
            "hydraulic_resistance_Pa_s_m3": "7.4e18",
            "q_ch_grid_candidate_m3_s": "1.34e-16",
            "candidate_flow_split_fraction": "0.60",
            "geometry_hash": "recthash",
        },
        {
            "case_id": "taper_theta85_D900_W500",
            "grid_nx": "41",
            "grid_nu": "41",
            "sidewall_deg_comsol": "85",
            "sidewall_taper_angle_deg_nodi": "5",
            "top_width_nm": "500",
            "depth_nm": "900",
            "pressure_drop_Pa": "1000",
            "solver_status": "candidate_solver_output",
            "hydraulic_resistance_Pa_s_m3": "1.14e19",
            "q_ch_grid_candidate_m3_s": "8.75e-17",
            "candidate_flow_split_fraction": "0.40",
            "geometry_hash": "taperhash",
        },
        {
            "case_id": "closed_theta70_D900_W500",
            "grid_nx": "41",
            "grid_nu": "41",
            "sidewall_deg_comsol": "70",
            "sidewall_taper_angle_deg_nodi": "20",
            "top_width_nm": "500",
            "depth_nm": "900",
            "solver_status": "blocked_geometry_closed",
            "geometry_hash": "closedhash",
        },
    ]


def test_pressure_flow_validation_requests_cover_exact_open_w500_d900_routes() -> None:
    rows = build_pressure_flow_validation_request_rows(_grid_rows())

    assert len(rows) == 2
    assert {row.route_candidate_id for row in rows} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    for row in rows:
        assert row.top_width_nm == 500
        assert row.depth_nm == 900
        assert row.reference_grid_nx == 41
        assert row.candidate_q_grid_m3_s > 0
        assert row.acceptance_ratio_min == 0.5
        assert row.acceptance_ratio_max == 2.0
        assert row.split_abs_delta_max == 0.05
        assert "q_total_m3_s" in row.required_observables
        assert "geometry_descriptor_sha256" in row.required_metadata
        assert row.validation_status == (
            "exact_w500_d900_validation_harness_ready_missing_external_result"
        )
        assert row.formal_qch_weighting_current is False
        assert row.route_score_current is False
        assert row.yield_current is False
        assert row.detection_probability_current is False
        assert row.claim_boundary == SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_CLAIM_BOUNDARY


def test_pressure_flow_validation_harness_keeps_closed_geometry_as_control() -> None:
    controls = build_pressure_flow_validation_control_rows(_grid_rows())

    assert len(controls) == 1
    control = controls[0]
    assert control.case_id == "closed_theta70_D900_W500"
    assert control.control_status == "closed_geometry_control_must_remain_blocked"
    assert control.required_behavior == "no pressure-flow validation request and no qch sidecar"
    assert control.hard_fail_if == "closed_geometry_enters_formal_qch_or_route_score"
    assert control.claim_boundary == SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_CLAIM_BOUNDARY


def test_pressure_flow_validation_promotion_update_is_not_formal_validation() -> None:
    rows = build_pressure_flow_validation_request_rows(_grid_rows())
    updates = pressure_flow_validation_promotion_update_rows(rows)

    assert len(updates) == 1
    update = updates[0]
    assert update["target_ledger_lane"] == "pressure_flow_validation"
    assert update["new_context_status"] == (
        "exact_w500_d900_pressure_flow_validation_harness_ready_missing_external_result"
    )
    assert update["target_claim_current"] == "false"
    assert "formal_qch_weighting" in update["blocked_promotion"]
    assert "route_score" in update["blocked_promotion"]
    assert "detection_probability" in update["blocked_promotion"]
    assert update["claim_boundary"] == SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_CLAIM_BOUNDARY
