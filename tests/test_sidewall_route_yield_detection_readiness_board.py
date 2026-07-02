from __future__ import annotations

from nodi_simulator.sidewall_route_yield_detection_readiness_board import (
    MISSING_CLAIM_EVIDENCE,
    READINESS_BOARD_STATUS,
    READY_ROUTE_INPUT,
    SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_CLAIM_BOUNDARY,
    build_route_yield_detection_readiness_board,
)


def _qch(route_id: str) -> dict[str, str]:
    family = "ideal_rectangle" if route_id == "ROUTE-CAND-001" else "trapezoid_tapered_sidewalls"
    case_id = (
        "rectangle_limit_theta90_D900_W500"
        if route_id == "ROUTE-CAND-001"
        else "taper_theta85_D900_W500"
    )
    return {
        "route_candidate_id": route_id,
        "route_key": f"route_{case_id}",
        "route_geometry_family": family,
        "case_id": case_id,
        "qch_sidecar_id": f"QCH-{route_id}",
        "per_route_acceptance_status": "accepted_exact_pressure_flow_for_formal_qch_sidecar",
        "source_match_status": "exact_request_and_geometry_match",
        "quality_gate": "pass",
        "formal_qch_sidecar_id": f"FORMAL-QCH-{route_id}",
        "q_ch_m3_s": "1.0e-16",
        "formal_flow_split_fraction": "0.5",
        "formal_qch_sidecar_current": "True",
        "formal_qch_weighting_current": "False",
        "q_ch_weighting_current": "False",
        "bridge_status": (
            "formal_qch_receipt_reconciled_ready_as_route_input_not_route_weighting"
        ),
    }


def _policy(route_id: str) -> dict[str, str]:
    return {
        "route_candidate_id": route_id,
        "route_key": f"route_{route_id}",
        "source_case_id": "case",
        "qch_sidecar_id": f"QCH-{route_id}",
        "pressure_flow_policy_status": (
            "ready_exact_pressure_flow_validation_for_formal_qch_input"
        ),
        "selected_annulus_policy_status": (
            "ready_selected_annulus_event_panel_input_not_probability"
        ),
        "primary_next_execution_block": "sidewall_detector_blank_transfer_validation",
        "next_required_evidence": "policy evidence",
    }


def _assembly(route_id: str) -> dict[str, str]:
    family = "ideal_rectangle" if route_id == "ROUTE-CAND-001" else "trapezoid_tapered_sidewalls"
    return {
        "route_candidate_id": route_id,
        "route_key": f"route_{route_id}",
        "route_geometry_family": family,
        "source_case_id": "case",
        "qch_sidecar_id": f"QCH-{route_id}",
        "selected_annulus_detection_context_status": (
            "expanded_selected_annulus_panel_available_not_probability"
        ),
        "next_executable_branch": "sidewall_detector_blank_transfer_validation",
        "next_required_evidence": "assembly evidence",
    }


def _policy_blockers(route_id: str) -> list[dict[str, str]]:
    return [
        {
            "route_candidate_id": route_id,
            "evidence_lane": "detector_response_bridge",
            "next_required_evidence": "detector response validation",
        },
        {
            "route_candidate_id": route_id,
            "evidence_lane": "blank_false_positive_trace",
            "next_required_evidence": "blank false-positive transfer",
        },
        {
            "route_candidate_id": route_id,
            "evidence_lane": "wet_wall_interaction",
            "next_required_evidence": "wet observation bundle",
        },
    ]


def _transfer(route_id: str) -> dict[str, str]:
    return {
        "route_candidate_id": route_id,
        "route_transfer_matrix_status": (
            "detector_blank_transfer_intake_ready_no_transfer_evidence"
        ),
        "accepted_transfer_count": "0",
    }


def _wet(route_id: str) -> dict[str, str]:
    return {
        "route_candidate_id": route_id,
        "route_wet_observation_matrix_status": (
            "wet_surface_observation_intake_ready_no_observations"
        ),
        "accepted_endpoint_count": "0",
    }


def _build() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    routes = ("ROUTE-CAND-001", "ROUTE-CAND-002")
    rows, blockers = build_route_yield_detection_readiness_board(
        formal_qch_bridge_rows=[_qch(route) for route in routes],
        policy_rows=[_policy(route) for route in routes],
        policy_blocker_rows=[
            blocker for route in routes for blocker in _policy_blockers(route)
        ],
        assembly_rows=[_assembly(route) for route in routes],
        detector_transfer_audit_rows=[_transfer(route) for route in routes],
        wet_observation_audit_rows=[_wet(route) for route in routes],
    )
    return [row.to_dict() for row in rows], [row.to_dict() for row in blockers]


def test_readiness_board_keeps_rectangle_and_trapezoid_parallel() -> None:
    rows, blockers = _build()

    assert len(rows) == 2
    assert len(blockers) == 10
    assert {row["route_geometry_family"] for row in rows} == {
        "ideal_rectangle",
        "trapezoid_tapered_sidewalls",
    }
    for row in rows:
        assert row["qch_route_input_status"] == READY_ROUTE_INPUT
        assert row["pressure_flow_route_input_status"] == READY_ROUTE_INPUT
        assert row["selected_annulus_context_status"] == READY_ROUTE_INPUT
        assert row["detector_blank_transfer_status"] == MISSING_CLAIM_EVIDENCE
        assert row["wet_observation_status"] == MISSING_CLAIM_EVIDENCE
        assert row["ready_route_input_count"] == 3
        assert row["missing_claim_evidence_count"] == 2
        assert row["readiness_fraction"] == 0.6
        assert row["board_status"] == READINESS_BOARD_STATUS
        assert row["primary_next_execution_block"] == (
            "sidewall_detector_blank_transfer_validation"
        )
        assert row["secondary_next_execution_block"] == "wet_observation_bundle_intake"


def test_readiness_board_never_promotes_claims_from_inputs() -> None:
    rows, blockers = _build()

    for row in rows:
        assert row["route_score_current"] is False
        assert row["winner_current"] is False
        assert row["yield_current"] is False
        assert row["detection_probability_current"] is False
        assert row["wet_pass_probability_current"] is False
        assert row["production_ingestion_current"] is False
        assert row["claim_boundary"] == (
            SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_CLAIM_BOUNDARY
        )
    for row in blockers:
        assert row["target_claim_current"] is False
        assert row["claim_boundary"] == (
            SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_CLAIM_BOUNDARY
        )


def test_readiness_blockers_show_ready_inputs_and_missing_claim_evidence() -> None:
    _rows, blockers = _build()

    assert {
        row["evidence_lane"]
        for row in blockers
        if row["readiness_class"] == READY_ROUTE_INPUT
    } == {
        "formal_qch",
        "pressure_flow_validation",
        "selected_annulus_detection_context",
    }
    assert {
        row["evidence_lane"]
        for row in blockers
        if row["readiness_class"] == MISSING_CLAIM_EVIDENCE
    } == {"detector_blank_transfer", "wet_observation"}
