from __future__ import annotations

from nodi_simulator.sidewall_wet_surface_contract import (
    SIDEWALL_WET_SURFACE_CONTRACT_CLAIM_BOUNDARY,
    WET_SURFACE_ENDPOINTS,
    build_wet_surface_contract_rows,
    wet_surface_promotion_update_rows,
)


def _promotion_lanes() -> list[dict[str, str]]:
    return [
        {
            "route_candidate_id": "ROUTE-CAND-001",
            "route_key": "route_rectangle_limit_theta90_D900_W500",
            "source_case_id": "rectangle_limit_theta90_D900_W500",
            "qch_sidecar_id": "QCH-CAND-001",
            "evidence_lane": "wet_wall_interaction",
            "current_status": "wet_sidewall_evidence_missing",
        },
        {
            "route_candidate_id": "ROUTE-CAND-002",
            "route_key": "route_taper_theta85_D900_W500",
            "source_case_id": "taper_theta85_D900_W500",
            "qch_sidecar_id": "QCH-CAND-002",
            "evidence_lane": "wet_wall_interaction",
            "current_status": "wet_sidewall_evidence_missing",
        },
    ]


def _wet_context_rows() -> list[dict[str, str]]:
    return [
        {
            "route_candidate_id": "ROUTE-CAND-001",
            "wet_context_status": (
                "ev_weighted_panel_surrogate_context_available_not_wet_experiment"
            ),
        },
        {
            "route_candidate_id": "ROUTE-CAND-002",
            "wet_context_status": (
                "ev_weighted_panel_surrogate_context_available_not_wet_experiment"
            ),
        },
    ]


def test_wet_surface_contract_defines_endpoint_rows_without_claims() -> None:
    rows = build_wet_surface_contract_rows(_promotion_lanes(), _wet_context_rows())

    assert len(rows) == len(WET_SURFACE_ENDPOINTS) * 2
    assert {row.route_candidate_id for row in rows} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    assert {row.endpoint_id for row in rows} == {
        endpoint["endpoint_id"] for endpoint in WET_SURFACE_ENDPOINTS
    }
    for row in rows:
        assert row.evidence_lane == "wet_wall_interaction"
        assert row.target_claim_current is False
        assert row.contract_status == "wet_surface_contract_defined_no_wet_validation"
        assert row.required_fields
        assert row.minimum_controls
        assert row.hard_fail_if_missing
        assert row.not_wet_pass_probability is True
        assert row.not_clogging_rate is True
        assert row.not_time_to_clog is True
        assert row.not_recovery is True
        assert row.not_yield is True
        assert row.not_detection_probability is True
        assert row.not_route_score is True
        assert row.not_winner is True
        assert row.claim_boundary == SIDEWALL_WET_SURFACE_CONTRACT_CLAIM_BOUNDARY


def test_wet_surface_contract_keeps_geometry_parsing_explicit() -> None:
    rows = build_wet_surface_contract_rows(_promotion_lanes(), _wet_context_rows())
    by_route = {row.route_candidate_id: row for row in rows if row.endpoint_id == "yield_bridge"}

    assert by_route["ROUTE-CAND-001"].source_width_nm == 500
    assert by_route["ROUTE-CAND-001"].source_depth_nm == 900
    assert by_route["ROUTE-CAND-001"].sidewall_deg_comsol == 90.0
    assert by_route["ROUTE-CAND-002"].source_width_nm == 500
    assert by_route["ROUTE-CAND-002"].source_depth_nm == 900
    assert by_route["ROUTE-CAND-002"].sidewall_deg_comsol == 85.0


def test_wet_surface_promotion_update_remains_single_context_update() -> None:
    rows = build_wet_surface_contract_rows(_promotion_lanes(), _wet_context_rows())
    updates = wet_surface_promotion_update_rows(rows)

    assert len(updates) == 1
    update = updates[0]
    assert update["target_ledger_lane"] == "wet_wall_interaction"
    assert update["new_context_status"] == (
        "wet_surface_evidence_contract_defined_no_wet_validation"
    )
    assert update["target_claim_current"] == "false"
    assert "yield" in update["blocked_promotion"]
    assert "clogging_rate" in update["blocked_promotion"]
    assert "detection_probability" in update["blocked_promotion"]
    assert update["claim_boundary"] == SIDEWALL_WET_SURFACE_CONTRACT_CLAIM_BOUNDARY
