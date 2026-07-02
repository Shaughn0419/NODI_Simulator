from __future__ import annotations

from nodi_simulator.sidewall_solver_branch_execution_packet import (
    SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_CLAIM_BOUNDARY,
    build_solver_branch_execution_packet,
)


def _policy_rows() -> list[dict[str, object]]:
    task_ids = [
        "comsol_clean_mirror_receipt",
        "trapezoid_flow_solver_preflight",
        "electrokinetic_grid_preflight",
        "optical_reference_preflight",
        "wet_ev_evidence_contract",
        "route_promotion_contract",
    ]
    return [
        {
            "task_id": task_id,
            "user_authorization_status": "authorized",
            "authorized_to_prepare": True,
            "authorized_to_execute_when_packet_passes": True,
        }
        for task_id in task_ids
    ]


def _flow_status() -> dict[str, object]:
    return {
        "artifact_id": "FLOW",
        "disposition": "FLOW_READY",
        "current_head": "abc",
        "solver_candidate_rows": 3,
        "candidate_solver_output_rows": 2,
        "blocked_solver_rows": 1,
        "trapezoid_flow_solver_candidate_output_current": True,
        "trapezoid_flow_solver_final_claim_current": False,
    }


def _reference_status() -> dict[str, object]:
    return {
        "artifact_id": "REF",
        "disposition": "REF_READY",
        "current_head": "def",
        "surrogate_rows": 4,
        "sidewall_reference_surrogate_current": True,
        "full_wave_or_calibrated_optical_solver_current": False,
    }


def _optical_status() -> dict[str, object]:
    return {
        "artifact_id": "OPT",
        "disposition": "OPT_READY",
        "current_head": "ghi",
        "seed_rows": 4,
        "readiness_rows": 6,
        "full_wave_or_calibrated_optical_solver_current": False,
    }


def _wet_status() -> dict[str, object]:
    return {
        "artifact_id": "WET",
        "disposition": "WET_CONTEXT",
        "current_head": "jkl",
        "evidence_context_rows": 2,
        "detection_context_available_rows": 2,
        "boundary_context_rows": 11,
    }


def _readiness_status() -> dict[str, object]:
    return {
        "artifact_id": "READY",
        "disposition": "READY_INPUTS",
        "current_head": "mno",
        "board_rows": 2,
        "ready_route_input_count_total": 6,
        "missing_claim_evidence_count_total": 4,
    }


def _build():
    return build_solver_branch_execution_packet(
        policy_rows=_policy_rows(),
        flow_status=_flow_status(),
        reference_status=_reference_status(),
        optical_calibration_status=_optical_status(),
        wet_optical_status=_wet_status(),
        readiness_board_status=_readiness_status(),
    )


def test_branch_packet_inventory_covers_solver_wet_and_route_mainline() -> None:
    branch_rows, guard_rows = _build()

    assert len(branch_rows) == 6
    assert len(guard_rows) == 8
    assert {row.authorized_to_prepare for row in branch_rows} == {True}
    assert {row.authorized_to_execute_when_packet_passes for row in branch_rows} == {True}
    assert {row.claim_boundary for row in branch_rows} == {
        SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_CLAIM_BOUNDARY
    }
    assert {row.claim_boundary for row in guard_rows} == {
        SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_CLAIM_BOUNDARY
    }


def test_flow_candidate_is_recorded_without_qch_or_route_promotion() -> None:
    branch_rows, guard_rows = _build()
    flow = next(row for row in branch_rows if row.branch_id == "trapezoid_flow_solver")
    qch_guard = next(row for row in guard_rows if row.promotion_target == "formal_q_ch_weighting")

    assert flow.candidate_evidence_current is True
    assert flow.candidate_output_rows == 2
    assert flow.final_solver_claim_current is False
    assert flow.q_ch_weighting_current is False
    assert flow.route_score_current is False
    assert qch_guard.candidate_evidence_current is True
    assert qch_guard.claim_promotion_allowed_now is False
    assert qch_guard.hard_fail_if_missing_evidence == (
        "q_ch_weighting_true_without_formal_sidecar"
    )


def test_electrokinetic_branch_starts_as_profile_grid_preflight() -> None:
    branch_rows, guard_rows = _build()
    ek = next(row for row in branch_rows if row.branch_id == "electrokinetic_solver")
    ek_guard = next(
        row for row in guard_rows if row.promotion_target == "electrokinetic_solver_claim"
    )

    assert ek.candidate_evidence_current is False
    assert ek.blocked_rows == 1
    assert ek.execution_packet_status == "electrokinetic_grid_packet_required"
    assert "profile-aware" in ek_guard.required_evidence_before_true
    assert ek_guard.claim_promotion_allowed_now is False


def test_optical_and_wet_context_do_not_promote_detection_or_yield() -> None:
    branch_rows, guard_rows = _build()
    optical = next(row for row in branch_rows if row.branch_id == "optical_reference_solver")
    wet = next(row for row in branch_rows if row.branch_id == "wet_optical_detection_evidence")
    detection = next(row for row in guard_rows if row.promotion_target == "detection_probability")
    yield_guard = next(row for row in guard_rows if row.promotion_target == "wet_pass_yield_recovery")

    assert optical.candidate_evidence_current is True
    assert optical.final_solver_claim_current is False
    assert wet.candidate_evidence_current is True
    assert wet.detection_probability_current is False
    assert wet.yield_current is False
    assert detection.claim_promotion_allowed_now is False
    assert yield_guard.claim_promotion_allowed_now is False


def test_route_decision_stays_waiting_for_branch_evidence() -> None:
    branch_rows, guard_rows = _build()
    route = next(row for row in branch_rows if row.branch_id == "route_yield_detection_decision")
    route_guard = next(row for row in guard_rows if row.promotion_target == "route_score_winner_JRC")

    assert route.candidate_output_rows == 6
    assert route.blocked_rows == 4
    assert route.route_score_current is False
    assert route.winner_current is False
    assert route.execution_packet_status == (
        "route_promotion_packet_blocked_until_branch_evidence_passes"
    )
    assert route_guard.candidate_evidence_current is True
    assert route_guard.claim_promotion_allowed_now is False
