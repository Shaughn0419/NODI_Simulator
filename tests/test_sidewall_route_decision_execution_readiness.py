from __future__ import annotations

from nodi_simulator.sidewall_route_decision_execution_readiness import (
    SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_CLAIM_BOUNDARY,
    build_route_decision_execution_readiness,
)


def _board_rows() -> list[dict[str, object]]:
    return [
        {"route_candidate_id": "R1", "route_key": "rect", "route_geometry_family": "ideal_rectangle", "source_case_id": "rect", "q_ch_m3_s": 1.0, "qch_route_input_status": "ready", "ready_route_input_count": 3, "missing_claim_evidence_count": 2},
        {"route_candidate_id": "R2", "route_key": "trap", "route_geometry_family": "trapezoid_tapered_sidewalls", "source_case_id": "trap", "q_ch_m3_s": 0.8, "qch_route_input_status": "ready", "ready_route_input_count": 3, "missing_claim_evidence_count": 2},
    ]


def _build():
    return build_route_decision_execution_readiness(
        readiness_board_rows=_board_rows(),
        solver_packet_status={"disposition": "SOLVER"},
        electrokinetic_status={"disposition": "EK"},
        comsol_precondition_status={"disposition": "COMSOL"},
        detector_blank_status={"disposition": "DETECTOR", "current_accepted_transfer_rows_total": 0},
        wet_observation_status={"disposition": "WET", "current_accepted_observation_rows_total": 0},
    )


def test_route_readiness_preserves_rectangle_and_trapezoid_routes() -> None:
    rows, guards = _build()
    assert len(rows) == 2
    assert len(guards) == 5
    assert {row.route_geometry_family for row in rows} == {"ideal_rectangle", "trapezoid_tapered_sidewalls"}
    assert {row.rectangle_baseline_preserved for row in rows} == {True}
    assert {row.sidewall_trapezoid_route_present for row in rows} == {True}


def test_route_decision_remains_blocked_until_detector_and_wet_rows_are_accepted() -> None:
    rows, guards = _build()
    assert {row.detector_accepted_transfer_rows for row in rows} == {0}
    assert {row.wet_accepted_observation_rows for row in rows} == {0}
    assert {row.execution_readiness_status for row in rows} == {
        "blocked_detector_blank_and_wet_observation_evidence_required"
    }
    assert {row.route_score_current for row in rows} == {False}
    assert {row.yield_current for row in rows} == {False}
    assert {row.detection_probability_current for row in rows} == {False}
    assert {row.claim_boundary for row in rows} == {
        SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_CLAIM_BOUNDARY
    }
    assert {guard.claim_promotion_allowed_now for guard in guards} == {False}
