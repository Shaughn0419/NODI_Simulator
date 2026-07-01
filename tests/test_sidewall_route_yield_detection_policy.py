from __future__ import annotations

from nodi_simulator.sidewall_route_yield_detection_policy import (
    REQUIRED_LANES,
    SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_CLAIM_BOUNDARY,
    build_route_yield_detection_policy_rows,
    route_yield_detection_policy_promotion_update_rows,
)


def _lane(route_id: str, lane: str, status: str, target: str) -> dict[str, str]:
    return {
        "route_candidate_id": route_id,
        "route_key": f"route_{route_id}",
        "source_case_id": "taper_theta85_D900_W500",
        "qch_sidecar_id": "QCH-CAND-002",
        "evidence_lane": lane,
        "current_status": status,
        "target_claim": target,
        "target_claim_current": "false",
        "next_required_evidence": f"next evidence for {lane}",
        "hard_fail_if_promoted_without": f"hard fail {lane}",
    }


def _rows() -> list[dict[str, str]]:
    statuses = {
        "flow_split_qch": (
            "w500_d900_grid_refined_split_candidate_absolute_q_requires_validation",
            "route_score;winner;detection_probability",
        ),
        "pressure_flow_validation": (
            "context_only_not_formal_validation",
            "route_score;winner;q_ch_weighting",
        ),
        "selected_annulus_detection_context": (
            "selected_annulus_context_available_small_n_not_probability",
            "detection_probability;route_score;winner",
        ),
        "detector_response_bridge": (
            "detector_identity_context_available_not_sidewall_response_validation",
            "detection_probability",
        ),
        "blank_false_positive_trace": (
            "nearest_blank_context_available_not_sidewall_specific_validation",
            "detection_probability",
        ),
        "wet_wall_interaction": (
            "wet_surface_evidence_contract_defined_no_wet_validation",
            "yield",
        ),
    }
    return [
        _lane(route_id, lane, status, target)
        for route_id in ("ROUTE-CAND-001", "ROUTE-CAND-002")
        for lane, (status, target) in statuses.items()
    ]


def test_route_yield_detection_policy_rolls_up_blocked_lanes() -> None:
    policy_rows, blocker_rows = build_route_yield_detection_policy_rows(_rows())

    assert len(policy_rows) == 2
    assert len(blocker_rows) == 2 * len(REQUIRED_LANES)
    for row in policy_rows:
        assert row.route_policy_status == (
            "not_ready_missing_calibrated_flow_detector_blank_wet_evidence"
        )
        assert row.primary_next_execution_block == "qch_or_pressure_flow_validation"
        assert row.route_score_allowed is False
        assert row.winner_allowed is False
        assert row.yield_allowed is False
        assert row.detection_probability_allowed is False
        assert row.wet_pass_probability_allowed is False
        assert row.claim_boundary == SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_CLAIM_BOUNDARY
        assert "next evidence for flow_split_qch" in row.next_required_evidence
        assert "next evidence for wet_wall_interaction" in row.next_required_evidence

    assert {row.evidence_lane for row in blocker_rows} == set(REQUIRED_LANES)
    assert {row.blocker_status for row in blocker_rows} == {"blocked_not_claim_ready"}


def test_route_yield_detection_policy_statuses_are_specific() -> None:
    policy_rows, _blocker_rows = build_route_yield_detection_policy_rows(_rows())
    row = policy_rows[0]

    assert row.qch_policy_status == (
        "not_ready_grid_refined_split_candidate_absolute_q_requires_validation"
    )
    assert row.pressure_flow_policy_status == "not_ready_pressure_flow_context_only"
    assert row.selected_annulus_policy_status == (
        "not_ready_selected_annulus_small_n_not_probability"
    )
    assert row.detector_response_policy_status == (
        "not_ready_detector_identity_context_not_response_validation"
    )
    assert row.blank_false_positive_policy_status == (
        "not_ready_nearest_blank_context_not_sidewall_specific_validation"
    )
    assert row.wet_surface_policy_status == (
        "not_ready_wet_surface_contract_defined_no_validation"
    )


def test_route_yield_detection_policy_promotion_update_remains_not_claim_ready() -> None:
    policy_rows, _blocker_rows = build_route_yield_detection_policy_rows(_rows())
    updates = route_yield_detection_policy_promotion_update_rows(policy_rows)

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
    assert update["claim_boundary"] == SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_CLAIM_BOUNDARY
