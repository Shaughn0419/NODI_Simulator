from __future__ import annotations

from nodi_simulator.sidewall_mainline_execution_work_order import (
    SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_CLAIM_BOUNDARY,
    build_mainline_execution_work_order,
)


def _route_rows() -> list[dict[str, object]]:
    return [
        {
            "route_candidate_id": "ROUTE-CAND-001",
            "route_geometry_family": "ideal_rectangle",
            "route_key": "route_rectangle_limit_theta90_D900_W500",
        },
        {
            "route_candidate_id": "ROUTE-CAND-002",
            "route_geometry_family": "trapezoid_tapered_sidewalls",
            "route_key": "route_taper_theta85_D900_W500",
        },
    ]


def _build():
    return build_mainline_execution_work_order(
        solver_status={
            "artifact_id": "SOLVER",
            "disposition": "solver_ready",
            "branch_rows": 6,
            "candidate_evidence_current_rows": 4,
        },
        electrokinetic_status={
            "artifact_id": "EK",
            "disposition": "ek_preflight",
            "preflight_rows": 4,
            "profile_aware_grid_current_rows": 0,
        },
        comsol_status={
            "artifact_id": "COMSOL",
            "disposition": "comsol_precondition",
            "precondition_rows": 5,
            "precondition_passed_rows": 2,
            "target_model_bound_rows": 0,
            "launch_command_hash_bound_rows": 0,
        },
        detector_status={
            "artifact_id": "DETECTOR",
            "current_head": "detector-head",
            "disposition": "detector_ready_evidence_required",
            "candidate_or_fixture_rows_total": 36,
            "current_accepted_transfer_rows_total": 0,
        },
        wet_status={
            "artifact_id": "WET",
            "current_head": "wet-head",
            "disposition": "wet_ready_observations_required",
            "contract_or_fixture_rows_total": 64,
            "current_accepted_observation_rows_total": 0,
        },
        route_status={
            "artifact_id": "ROUTE",
            "current_head": "route-head",
            "disposition": "route_ready_inputs_not_claims",
            "readiness_rows": 2,
        },
        route_rows=_route_rows(),
    )


def test_mainline_work_order_prioritizes_large_blocks_and_keeps_geometry_parallel() -> None:
    work_orders, guards, register = _build()
    assert len(work_orders) == 8
    assert len(guards) == 7
    assert len(register) == 10
    assert {row.route_geometry_scope for row in work_orders} == {
        "ideal_rectangle;trapezoid_tapered_sidewalls"
    }
    assert {row.implementation_authorized for row in work_orders} == {True}
    assert {row.codex_can_execute_next for row in work_orders} == {True}
    assert {row.claim_boundary for row in work_orders} == {
        SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_CLAIM_BOUNDARY
    }


def test_route_evidence_register_does_not_promote_fixture_or_ready_input_rows() -> None:
    _work_orders, guards, register = _build()
    assert {row.route_geometry_family for row in register} == {
        "ideal_rectangle",
        "trapezoid_tapered_sidewalls",
    }
    assert sum(row.evidence_class == "ready_route_input" for row in register) == 2
    assert sum(row.evidence_class == "current_accepted_claim_evidence" for row in register) == 0
    assert {row.may_satisfy_route_formula_now for row in register} == {False}
    assert {row.activation_allowed_now for row in guards} == {False}
    detector_rows = [row for row in register if row.evidence_lane == "detector_blank_transfer"]
    wet_rows = [row for row in register if row.evidence_lane == "wet_observation"]
    assert {row.evidence_class for row in detector_rows} == {
        "fixture_or_context_available_no_accepted_claim_evidence"
    }
    assert {row.evidence_class for row in wet_rows} == {
        "fixture_or_contract_available_no_accepted_claim_evidence"
    }
