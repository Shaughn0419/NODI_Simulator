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
        route_formula_dry_run_status={"disposition": "DRY"},
        route_formula_dry_run_rows=[],
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


def test_route_decision_can_reach_policy_review_ready_when_evidence_and_components_ready() -> None:
    rows, guards = build_route_decision_execution_readiness(
        readiness_board_rows=_board_rows(),
        solver_packet_status={"disposition": "SOLVER"},
        electrokinetic_status={"disposition": "EK"},
        comsol_precondition_status={"disposition": "COMSOL"},
        detector_blank_status={
            "disposition": "ACTIVATION",
            "detector_accepted_transfer_rows_total": 2,
        },
        wet_observation_status={
            "disposition": "ACTIVATION",
            "wet_accepted_endpoint_count_total": 14,
        },
        route_formula_dry_run_status={"disposition": "DRY"},
        route_formula_dry_run_rows=[
            {
                "route_candidate_id": "R1",
                "route_formula_ready_for_claim_review": "True",
                "route_formula_review_dry_run_status": (
                    "route_formula_component_vector_ready_for_policy_review_not_scored"
                ),
            },
            {
                "route_candidate_id": "R2",
                "route_formula_ready_for_claim_review": "True",
                "route_formula_review_dry_run_status": (
                    "route_formula_component_vector_ready_for_policy_review_not_scored"
                ),
            },
        ],
    )

    assert {row.execution_readiness_status for row in rows} == {
        "branch_evidence_and_formula_components_ready_for_route_policy_review"
    }
    assert {row.route_formula_component_vector_ready for row in rows} == {True}
    assert {row.route_score_current for row in rows} == {False}
    assert {row.yield_current for row in rows} == {False}
    assert {row.detection_probability_current for row in rows} == {False}
    assert {guard.claim_promotion_allowed_now for guard in guards} == {False}


def test_route_decision_can_carry_simulation_route_score_and_top_candidate_status() -> None:
    rows, guards = build_route_decision_execution_readiness(
        readiness_board_rows=_board_rows(),
        solver_packet_status={"disposition": "SOLVER"},
        electrokinetic_status={"disposition": "EK"},
        comsol_precondition_status={"disposition": "COMSOL"},
        detector_blank_status={
            "disposition": "ACTIVATION",
            "detector_accepted_transfer_rows_total": 2,
        },
        wet_observation_status={
            "disposition": "ACTIVATION",
            "wet_accepted_endpoint_count_total": 14,
        },
        route_formula_dry_run_status={"disposition": "DRY"},
        route_formula_dry_run_rows=[
            {
                "route_candidate_id": "R1",
                "route_formula_ready_for_claim_review": "True",
                "route_formula_review_dry_run_status": (
                    "route_formula_component_vector_ready_for_policy_review_not_scored"
                ),
            },
            {
                "route_candidate_id": "R2",
                "route_formula_ready_for_claim_review": "True",
                "route_formula_review_dry_run_status": (
                    "route_formula_component_vector_ready_for_policy_review_not_scored"
                ),
            },
        ],
        route_formula_policy_status={"disposition": "FORMULA-POLICY"},
        route_formula_policy_rows=[
            {
                "route_candidate_id": "R1",
                "simulation_route_score_candidate_current": "True",
            },
            {
                "route_candidate_id": "R2",
                "simulation_route_score_candidate_current": "True",
            },
        ],
        winner_jrc_policy_status={"disposition": "WINNER-POLICY"},
        winner_jrc_policy_rows=[
            {"route_candidate_id": "R1", "simulation_top_candidate_current": "True"},
            {"route_candidate_id": "R2", "simulation_top_candidate_current": "False"},
        ],
    )

    assert {row.execution_readiness_status for row in rows} == {
        "winner_jrc_ready_for_integrated_yield_detection_review"
    }
    assert {row.route_score_candidate_ready for row in rows} == {True}
    assert {row.route_score_current for row in rows} == {False}
    assert sum(row.winner_current for row in rows) == 0
    assert sum(row.JRC_current for row in rows) == 0
    by_target = {guard.promotion_target: guard for guard in guards}
    assert by_target["route_score"].claim_promotion_allowed_now is False
    assert by_target["winner_JRC"].claim_promotion_allowed_now is False
    assert by_target["yield"].claim_promotion_allowed_now is False
    assert by_target["detection_probability"].claim_promotion_allowed_now is False


def test_route_decision_can_carry_simulation_yield_detection_value_status() -> None:
    rows, guards = build_route_decision_execution_readiness(
        readiness_board_rows=_board_rows(),
        solver_packet_status={"disposition": "SOLVER"},
        electrokinetic_status={"disposition": "EK"},
        comsol_precondition_status={"disposition": "COMSOL"},
        detector_blank_status={
            "disposition": "ACTIVATION",
            "detector_accepted_transfer_rows_total": 2,
        },
        wet_observation_status={
            "disposition": "ACTIVATION",
            "wet_accepted_endpoint_count_total": 14,
        },
        route_formula_policy_rows=[
            {
                "route_candidate_id": "R1",
                "simulation_route_score_candidate_current": "True",
            },
            {
                "route_candidate_id": "R2",
                "simulation_route_score_candidate_current": "True",
            },
        ],
        winner_jrc_policy_rows=[
            {"route_candidate_id": "R1", "simulation_top_candidate_current": "True"},
            {"route_candidate_id": "R2", "simulation_top_candidate_current": "False"},
        ],
        yield_detection_claim_value_status={"disposition": "CLAIM-VALUE"},
        yield_detection_claim_value_rows=[
            {
                "route_candidate_id": "R1",
                "yield_simulation_candidate_current": "True",
                "detection_probability_simulation_candidate_current": "True",
                "wet_pass_probability_simulation_candidate_current": "True",
            },
            {
                "route_candidate_id": "R2",
                "yield_simulation_candidate_current": "True",
                "detection_probability_simulation_candidate_current": "True",
                "wet_pass_probability_simulation_candidate_current": "True",
            },
        ],
    )

    assert {row.execution_readiness_status for row in rows} == {
        "route_yield_detection_claim_values_ready_for_integrated_review"
    }
    assert {row.yield_detection_values_ready for row in rows} == {True}
    assert {row.yield_current for row in rows} == {False}
    assert {row.detection_probability_current for row in rows} == {False}
    assert {row.wet_pass_probability_current for row in rows} == {False}
    by_target = {guard.promotion_target: guard for guard in guards}
    assert by_target["yield"].claim_promotion_allowed_now is False
    assert by_target["detection_probability"].claim_promotion_allowed_now is False
    assert by_target["production_ingestion"].claim_promotion_allowed_now is False
