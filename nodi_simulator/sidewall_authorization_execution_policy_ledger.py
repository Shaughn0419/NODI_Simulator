"""Authorization-to-execution policy ledger for sidewall Package C.

This module joins user authorization, the authorized execution queue, runtime
packet state, and the route/yield/detection readiness board. It separates
"authorized to prepare/execute a branch" from "allowed to promote a result
claim".
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_VERSION = (
    "sidewall_authorization_execution_policy_ledger_v1"
)
SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_CLAIM_BOUNDARY = (
    "authorization_execution_policy_not_route_score_not_yield_not_detection_probability"
)
POLICY_LEDGER_READY_STATUS = "authorized_execution_policy_ready_claims_still_guarded"


@dataclass(frozen=True)
class SidewallAuthorizationExecutionPolicyRow:
    policy_row_id: str
    policy_version: str
    branch_id: str
    task_id: str
    task: str
    execution_mode: str
    dependency: str
    user_authorization_status: str
    authorized_to_prepare: bool
    authorized_to_execute_when_packet_passes: bool
    current_execution_state: str
    execution_packet_status: str
    route_readiness_dependency: str
    comsol_launch_allowed_now: bool
    mph_load_allowed_now: bool
    nodi_runtime_recomputation_allowed_now: bool
    sidewall_prs_eas_numeric_allowed_now: bool
    claim_promoted_by_this_task: bool
    claim_promotion_allowed_now: bool
    next_required_evidence: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallAuthorizationExecutionClaimGuardRow:
    guard_row_id: str
    policy_version: str
    promotion_target: str
    implementation_authorized: bool
    candidate_evidence_authorized: bool
    claim_promoted_current: bool
    claim_promotion_allowed_now: bool
    required_evidence_before_claim_true: str
    first_allowed_status: str
    hard_fail_if_missing_evidence: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_authorization_execution_policy_ledger(
    *,
    authorization_scope_rows: list[Mapping[str, Any]],
    execution_queue_rows: list[Mapping[str, Any]],
    promotion_contract_rows: list[Mapping[str, Any]],
    readiness_board_rows: list[Mapping[str, Any]],
    readiness_blocker_rows: list[Mapping[str, Any]],
    runtime_packet_status: Mapping[str, Any],
) -> tuple[
    list[SidewallAuthorizationExecutionPolicyRow],
    list[SidewallAuthorizationExecutionClaimGuardRow],
]:
    authorization = _authorization_map(authorization_scope_rows)
    readiness = _readiness_summary(readiness_board_rows, readiness_blocker_rows)
    policy_rows = [
        _policy_row(
            row=row,
            authorization=authorization,
            readiness=readiness,
            runtime_packet_status=runtime_packet_status,
        )
        for row in execution_queue_rows
    ]
    guard_rows = [
        SidewallAuthorizationExecutionClaimGuardRow(
            guard_row_id=f"AUTH-EXEC-CLAIM-GUARD-{row.get('promotion_target', '')}",
            policy_version=SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_VERSION,
            promotion_target=str(row.get("promotion_target", "")),
            implementation_authorized=_bool_value(row.get("implementation_authorized")),
            candidate_evidence_authorized=_bool_value(
                row.get("candidate_evidence_authorized")
            ),
            claim_promoted_current=_bool_value(row.get("claim_promoted_current")),
            claim_promotion_allowed_now=False,
            required_evidence_before_claim_true=str(
                row.get("required_evidence_before_claim_true", "")
            ),
            first_allowed_status=str(row.get("first_allowed_status", "")),
            hard_fail_if_missing_evidence=str(row.get("hard_fail_if_missing_evidence", "")),
            claim_boundary=SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_CLAIM_BOUNDARY,
        )
        for row in promotion_contract_rows
    ]
    return policy_rows, guard_rows


def _policy_row(
    *,
    row: Mapping[str, Any],
    authorization: dict[str, bool],
    readiness: dict[str, Any],
    runtime_packet_status: Mapping[str, Any],
) -> SidewallAuthorizationExecutionPolicyRow:
    branch_id = str(row.get("branch_id", ""))
    task_id = str(row.get("task_id", ""))
    runtime_packet_passed = (
        str(runtime_packet_status.get("disposition", ""))
        == "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_READY_WITH_GUARDED_SMOKE"
    )
    authorized_to_prepare = _bool_value(row.get("authorized_to_prepare"))
    authorized_to_execute = _bool_value(row.get("authorized_to_execute_when_packet_passes"))
    current_state = _current_execution_state(
        branch_id=branch_id,
        task_id=task_id,
        runtime_packet_passed=runtime_packet_passed,
        readiness=readiness,
    )
    packet_status = _execution_packet_status(
        branch_id=branch_id,
        task_id=task_id,
        runtime_packet_passed=runtime_packet_passed,
        readiness=readiness,
    )
    return SidewallAuthorizationExecutionPolicyRow(
        policy_row_id=f"AUTH-EXEC-POLICY-{task_id}",
        policy_version=SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_VERSION,
        branch_id=branch_id,
        task_id=task_id,
        task=str(row.get("task", "")),
        execution_mode=str(row.get("execution_mode", "")),
        dependency=str(row.get("dependency", "")),
        user_authorization_status=_branch_authorization_status(branch_id, authorization),
        authorized_to_prepare=authorized_to_prepare,
        authorized_to_execute_when_packet_passes=authorized_to_execute,
        current_execution_state=current_state,
        execution_packet_status=packet_status,
        route_readiness_dependency=_route_dependency(branch_id, readiness),
        comsol_launch_allowed_now=False,
        mph_load_allowed_now=False,
        nodi_runtime_recomputation_allowed_now=_nodi_runtime_allowed_now(
            task_id, runtime_packet_passed
        ),
        sidewall_prs_eas_numeric_allowed_now=False,
        claim_promoted_by_this_task=False,
        claim_promotion_allowed_now=False,
        next_required_evidence=_next_required_evidence(branch_id, readiness),
        hard_fail_if=_hard_fail_if(branch_id),
        claim_boundary=SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_CLAIM_BOUNDARY,
    )


def _authorization_map(rows: list[Mapping[str, Any]]) -> dict[str, bool]:
    output: dict[str, bool] = {}
    for row in rows:
        output[str(row.get("scope_id", ""))] = (
            str(row.get("authorization_status", "")) == "authorized"
        )
    return output


def _readiness_summary(
    board_rows: list[Mapping[str, Any]],
    blocker_rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    primary_branches = sorted(
        {str(row.get("primary_next_execution_block", "")) for row in board_rows}
    )
    secondary_branches = sorted(
        {str(row.get("secondary_next_execution_block", "")) for row in board_rows}
    )
    missing_lanes = sorted(
        {
            str(row.get("evidence_lane", ""))
            for row in blocker_rows
            if str(row.get("readiness_class", "")) == "missing_required_claim_evidence"
        }
    )
    ready_lanes = sorted(
        {
            str(row.get("evidence_lane", ""))
            for row in blocker_rows
            if str(row.get("readiness_class", "")) == "ready_route_input_not_final_claim"
        }
    )
    next_evidence = sorted(
        {
            str(row.get("next_required_evidence", "")).strip()
            for row in blocker_rows
            if str(row.get("readiness_class", "")) == "missing_required_claim_evidence"
            and str(row.get("next_required_evidence", "")).strip()
        }
    )
    return {
        "primary_next_execution_blocks": primary_branches,
        "secondary_next_execution_blocks": secondary_branches,
        "missing_claim_lanes": missing_lanes,
        "ready_route_input_lanes": ready_lanes,
        "next_required_evidence": next_evidence,
    }


def _branch_authorization_status(branch_id: str, authorization: dict[str, bool]) -> str:
    if branch_id == "runtime_substep_execution":
        return _status(authorization.get("runtime_substep_policy_path"))
    if branch_id in {
        "trapezoid_flow_solver",
        "electrokinetic_solver",
        "optical_reference_solver",
    }:
        return _status(authorization.get("solver_branch_path"))
    if branch_id == "wet_ev_evidence":
        return _status(authorization.get("wet_branch_path"))
    if branch_id == "route_yield_detection_decision":
        return _status(
            authorization.get("solver_branch_path") and authorization.get("wet_branch_path")
        )
    return "authorized_by_mainline_queue"


def _status(value: bool | None) -> str:
    return "authorized" if bool(value) else "not_authorized"


def _current_execution_state(
    *,
    branch_id: str,
    task_id: str,
    runtime_packet_passed: bool,
    readiness: dict[str, Any],
) -> str:
    if task_id == "guarded_trajectory_smoke" and runtime_packet_passed:
        return "guarded_trajectory_smoke_executed_not_prs_eas_numeric"
    if branch_id == "runtime_substep_execution" and runtime_packet_passed:
        return "candidate_runtime_smoke_packet_passed_not_production_runtime"
    if branch_id == "route_yield_detection_decision":
        return "blocked_until_detector_blank_wet_and_solver_evidence_pass"
    if branch_id == "wet_ev_evidence" and "wet_observation" in readiness["missing_claim_lanes"]:
        return "authorized_to_prepare_wet_evidence_contract_observations_missing"
    if (
        branch_id in {"trapezoid_flow_solver", "electrokinetic_solver", "optical_reference_solver"}
        and "detector_blank_transfer" in readiness["missing_claim_lanes"]
    ):
        return "authorized_to_prepare_solver_packet_claim_blockers_remain"
    return "authorized_to_prepare_execution_packet_required"


def _execution_packet_status(
    *,
    branch_id: str,
    task_id: str,
    runtime_packet_passed: bool,
    readiness: dict[str, Any],
) -> str:
    if task_id == "guarded_trajectory_smoke" and runtime_packet_passed:
        return "runtime_smoke_executed_candidate_only"
    if branch_id == "runtime_substep_execution" and runtime_packet_passed:
        return "runtime_substep_execution_packet_passed_candidate_only"
    if branch_id == "route_yield_detection_decision":
        return "route_promotion_packet_blocked_by_missing_claim_evidence"
    if branch_id == "wet_ev_evidence" and "wet_observation" in readiness["missing_claim_lanes"]:
        return "wet_observation_packet_required"
    return "branch_execution_packet_required_before_result_output"


def _route_dependency(branch_id: str, readiness: dict[str, Any]) -> str:
    if branch_id == "route_yield_detection_decision":
        return "missing:" + ";".join(readiness["missing_claim_lanes"])
    if branch_id == "wet_ev_evidence":
        return "missing:wet_observation"
    if branch_id in {"trapezoid_flow_solver", "electrokinetic_solver", "optical_reference_solver"}:
        return "ready_inputs:" + ";".join(readiness["ready_route_input_lanes"])
    return "runtime_or_context_branch"


def _nodi_runtime_allowed_now(task_id: str, runtime_packet_passed: bool) -> bool:
    return task_id == "guarded_trajectory_smoke" and runtime_packet_passed


def _next_required_evidence(branch_id: str, readiness: dict[str, Any]) -> str:
    if branch_id == "wet_ev_evidence":
        return "wet observation bundle with controls, replicates, uncertainty, and hashes"
    if branch_id == "route_yield_detection_decision":
        return " | ".join(readiness["next_required_evidence"])
    if branch_id in {"trapezoid_flow_solver", "electrokinetic_solver", "optical_reference_solver"}:
        return "branch-specific solver execution packet and source-hashed result evidence"
    if branch_id == "runtime_substep_execution":
        return "runtime packet already passed for candidate smoke; production runtime still separate"
    return "execution packet and source hash before result output"


def _hard_fail_if(branch_id: str) -> str:
    if branch_id == "runtime_substep_execution":
        return "production_runtime_or_prs_eas_numeric_true_from_runtime_smoke_only"
    if branch_id == "wet_ev_evidence":
        return "yield_or_wet_pass_true_without_accepted_wet_observation_bundle"
    if branch_id == "route_yield_detection_decision":
        return "route_score_winner_yield_detection_true_before_all_claim_evidence_passes"
    if branch_id in {"trapezoid_flow_solver", "electrokinetic_solver", "optical_reference_solver"}:
        return "solver_output_promoted_without_branch_execution_packet_and_hashes"
    return "claim_promoted_without_required_execution_packet"


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}
