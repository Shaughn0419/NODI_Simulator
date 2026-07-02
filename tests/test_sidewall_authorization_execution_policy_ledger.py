from __future__ import annotations

from nodi_simulator.sidewall_authorization_execution_policy_ledger import (
    POLICY_LEDGER_READY_STATUS,
    SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_CLAIM_BOUNDARY,
    build_authorization_execution_policy_ledger,
)


def _authorization_scopes() -> list[dict[str, str]]:
    return [
        {"scope_id": "package_c_proof_registration_path", "authorization_status": "authorized"},
        {"scope_id": "runtime_substep_policy_path", "authorization_status": "authorized"},
        {"scope_id": "solver_branch_path", "authorization_status": "authorized"},
        {"scope_id": "wet_branch_path", "authorization_status": "authorized"},
    ]


def _queue_rows() -> list[dict[str, str]]:
    return [
        {
            "task_id": "runtime_substep_execution_packet",
            "branch_id": "runtime_substep_execution",
            "task": "runtime task",
            "execution_mode": "local_nodi_only",
            "dependency": "next",
            "authorized_to_prepare": "true",
            "authorized_to_execute_when_packet_passes": "true",
            "claim_promoted_by_this_task": "false",
        },
        {
            "task_id": "guarded_trajectory_smoke",
            "branch_id": "runtime_substep_execution",
            "task": "guarded runtime smoke",
            "execution_mode": "local_nodi_allowed",
            "dependency": "after_packet",
            "authorized_to_prepare": "true",
            "authorized_to_execute_when_packet_passes": "true",
            "claim_promoted_by_this_task": "false",
        },
        {
            "task_id": "trapezoid_flow_solver_preflight",
            "branch_id": "trapezoid_flow_solver",
            "task": "flow task",
            "execution_mode": "solver_preflight",
            "dependency": "after_runtime",
            "authorized_to_prepare": "true",
            "authorized_to_execute_when_packet_passes": "true",
            "claim_promoted_by_this_task": "false",
        },
        {
            "task_id": "wet_ev_evidence_contract",
            "branch_id": "wet_ev_evidence",
            "task": "wet task",
            "execution_mode": "wet_contract",
            "dependency": "parallel",
            "authorized_to_prepare": "true",
            "authorized_to_execute_when_packet_passes": "true",
            "claim_promoted_by_this_task": "false",
        },
        {
            "task_id": "route_promotion_contract",
            "branch_id": "route_yield_detection_decision",
            "task": "route task",
            "execution_mode": "decision_contract",
            "dependency": "after_solver_wet",
            "authorized_to_prepare": "true",
            "authorized_to_execute_when_packet_passes": "true",
            "claim_promoted_by_this_task": "false",
        },
    ]


def _promotion_contract_rows() -> list[dict[str, str]]:
    return [
        {
            "promotion_target": "runtime_result",
            "implementation_authorized": "true",
            "candidate_evidence_authorized": "true",
            "claim_promoted_current": "false",
            "required_evidence_before_claim_true": "runtime_execution_packet_pass",
            "first_allowed_status": "runtime_result_candidate",
            "hard_fail_if_missing_evidence": "runtime_result_claim_true_without_required_hashes",
        },
        {
            "promotion_target": "yield_detection_probability",
            "implementation_authorized": "true",
            "candidate_evidence_authorized": "true",
            "claim_promoted_current": "false",
            "required_evidence_before_claim_true": "wet_evidence_pass;detection_calibration_pass",
            "first_allowed_status": "decision_candidate",
            "hard_fail_if_missing_evidence": "yield_detection_probability_claim_true_without_required_hashes",
        },
    ]


def _readiness_board_rows() -> list[dict[str, object]]:
    return [
        {
            "route_candidate_id": "ROUTE-CAND-001",
            "primary_next_execution_block": "sidewall_detector_blank_transfer_validation",
            "secondary_next_execution_block": "wet_observation_bundle_intake",
        },
        {
            "route_candidate_id": "ROUTE-CAND-002",
            "primary_next_execution_block": "sidewall_detector_blank_transfer_validation",
            "secondary_next_execution_block": "wet_observation_bundle_intake",
        },
    ]


def _readiness_blocker_rows() -> list[dict[str, str]]:
    lanes = [
        ("formal_qch", "ready_route_input_not_final_claim"),
        ("pressure_flow_validation", "ready_route_input_not_final_claim"),
        ("selected_annulus_detection_context", "ready_route_input_not_final_claim"),
        ("detector_blank_transfer", "missing_required_claim_evidence"),
        ("wet_observation", "missing_required_claim_evidence"),
    ]
    return [
        {
            "route_candidate_id": route,
            "evidence_lane": lane,
            "readiness_class": readiness,
            "next_required_evidence": f"next {lane}",
        }
        for route in ("ROUTE-CAND-001", "ROUTE-CAND-002")
        for lane, readiness in lanes
    ]


def _runtime_status() -> dict[str, str]:
    return {
        "disposition": "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_READY_WITH_GUARDED_SMOKE"
    }


def test_authorization_execution_policy_splits_authorized_from_claims() -> None:
    policy_rows, guard_rows = build_authorization_execution_policy_ledger(
        authorization_scope_rows=_authorization_scopes(),
        execution_queue_rows=_queue_rows(),
        promotion_contract_rows=_promotion_contract_rows(),
        readiness_board_rows=_readiness_board_rows(),
        readiness_blocker_rows=_readiness_blocker_rows(),
        runtime_packet_status=_runtime_status(),
    )

    assert len(policy_rows) == 5
    assert len(guard_rows) == 2
    for row in policy_rows:
        assert row.authorized_to_prepare is True
        assert row.authorized_to_execute_when_packet_passes is True
        assert row.claim_promoted_by_this_task is False
        assert row.claim_promotion_allowed_now is False
        assert row.comsol_launch_allowed_now is False
        assert row.mph_load_allowed_now is False
        assert row.sidewall_prs_eas_numeric_allowed_now is False
        assert row.claim_boundary == SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_CLAIM_BOUNDARY


def test_runtime_branch_allows_nodi_runtime_smoke_only_not_numeric_claims() -> None:
    policy_rows, _guards = build_authorization_execution_policy_ledger(
        authorization_scope_rows=_authorization_scopes(),
        execution_queue_rows=_queue_rows(),
        promotion_contract_rows=_promotion_contract_rows(),
        readiness_board_rows=_readiness_board_rows(),
        readiness_blocker_rows=_readiness_blocker_rows(),
        runtime_packet_status=_runtime_status(),
    )
    packet_row = next(row for row in policy_rows if row.task_id == "runtime_substep_execution_packet")
    runtime_row = next(row for row in policy_rows if row.task_id == "guarded_trajectory_smoke")

    assert packet_row.nodi_runtime_recomputation_allowed_now is False
    assert runtime_row.user_authorization_status == "authorized"
    assert runtime_row.current_execution_state == (
        "guarded_trajectory_smoke_executed_not_prs_eas_numeric"
    )
    assert runtime_row.execution_packet_status == (
        "runtime_smoke_executed_candidate_only"
    )
    assert runtime_row.nodi_runtime_recomputation_allowed_now is True
    assert runtime_row.sidewall_prs_eas_numeric_allowed_now is False


def test_route_and_wet_branches_remain_blocked_by_missing_claim_evidence() -> None:
    policy_rows, guard_rows = build_authorization_execution_policy_ledger(
        authorization_scope_rows=_authorization_scopes(),
        execution_queue_rows=_queue_rows(),
        promotion_contract_rows=_promotion_contract_rows(),
        readiness_board_rows=_readiness_board_rows(),
        readiness_blocker_rows=_readiness_blocker_rows(),
        runtime_packet_status=_runtime_status(),
    )
    wet_row = next(row for row in policy_rows if row.branch_id == "wet_ev_evidence")
    route_row = next(row for row in policy_rows if row.branch_id == "route_yield_detection_decision")

    assert wet_row.current_execution_state == (
        "authorized_to_prepare_wet_evidence_contract_observations_missing"
    )
    assert wet_row.route_readiness_dependency == "missing:wet_observation"
    assert route_row.current_execution_state == (
        "blocked_until_detector_blank_wet_and_solver_evidence_pass"
    )
    assert route_row.route_readiness_dependency == (
        "missing:detector_blank_transfer;wet_observation"
    )
    assert {row.claim_promotion_allowed_now for row in guard_rows} == {False}
    assert {row.claim_promoted_current for row in guard_rows} == {False}
