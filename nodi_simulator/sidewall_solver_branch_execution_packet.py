"""Execution packet planner for sidewall solver, wet, and decision branches.

The packet is deliberately an execution router. It records which branches are
authorized to prepare and which candidate/context evidence already exists, but
it does not promote solver, q_ch, route, wet, yield, or detection claims.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_VERSION = (
    "sidewall_solver_branch_execution_packet_v1"
)
SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_CLAIM_BOUNDARY = (
    "solver_branch_execution_packet_authorized_prepare_not_solver_claim_not_route_yield_detection"
)
SOLVER_BRANCH_EXECUTION_PACKET_READY_STATUS = (
    "solver_branch_execution_packet_ready_for_branch_packets_claims_guarded"
)


@dataclass(frozen=True)
class SidewallSolverBranchExecutionRow:
    branch_row_id: str
    packet_version: str
    branch_id: str
    branch_name: str
    policy_task_id: str
    user_authorization_status: str
    authorized_to_prepare: bool
    authorized_to_execute_when_packet_passes: bool
    current_candidate_evidence_status: str
    candidate_evidence_artifact_id: str
    candidate_evidence_disposition: str
    candidate_source_head: str
    candidate_rows: int
    candidate_output_rows: int
    blocked_rows: int
    execution_packet_status: str
    next_execution_step: str
    current_claim_level: str
    candidate_evidence_current: bool
    final_solver_claim_current: bool
    q_ch_weighting_current: bool
    route_score_current: bool
    winner_current: bool
    yield_current: bool
    detection_probability_current: bool
    wet_pass_claim_current: bool
    comsol_launch_allowed_now: bool
    mph_load_allowed_now: bool
    production_ingestion_current: bool
    next_required_evidence: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallSolverBranchClaimGuardRow:
    guard_row_id: str
    packet_version: str
    promotion_target: str
    source_branch_id: str
    implementation_authorized: bool
    candidate_evidence_current: bool
    claim_promoted_current: bool
    claim_promotion_allowed_now: bool
    first_allowed_status: str
    required_evidence_before_true: str
    hard_fail_if_missing_evidence: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_solver_branch_execution_packet(
    *,
    policy_rows: list[Mapping[str, Any]],
    flow_status: Mapping[str, Any],
    reference_status: Mapping[str, Any],
    optical_calibration_status: Mapping[str, Any],
    wet_optical_status: Mapping[str, Any],
    readiness_board_status: Mapping[str, Any],
) -> tuple[
    list[SidewallSolverBranchExecutionRow],
    list[SidewallSolverBranchClaimGuardRow],
]:
    policy_by_task = {str(row.get("task_id", "")): row for row in policy_rows}
    rows = [
        _comsol_receipt_row(policy_by_task),
        _flow_solver_row(policy_by_task, flow_status),
        _electrokinetic_solver_row(policy_by_task),
        _optical_reference_solver_row(
            policy_by_task, reference_status, optical_calibration_status
        ),
        _wet_detection_context_row(policy_by_task, wet_optical_status),
        _route_decision_row(policy_by_task, readiness_board_status),
    ]
    guards = _claim_guard_rows(rows)
    return rows, guards


def _comsol_receipt_row(
    policy_by_task: Mapping[str, Mapping[str, Any]],
) -> SidewallSolverBranchExecutionRow:
    policy = policy_by_task.get("comsol_clean_mirror_receipt", {})
    return _row(
        branch_id="comsol_clean_mirror_receipt",
        branch_name="COMSOL clean mirror receipt and launch precondition",
        policy=policy,
        current_candidate_evidence_status="receipt_not_yet_bound_to_clean_comsol_hash",
        candidate_evidence_artifact_id="",
        candidate_evidence_disposition="",
        candidate_source_head="",
        candidate_rows=0,
        candidate_output_rows=0,
        blocked_rows=0,
        execution_packet_status="read_only_receipt_packet_required_before_comsol_launch",
        next_execution_step="publish source-hashed clean COMSOL mirror receipt before any launch",
        current_claim_level="pre_execution_receipt_required",
        candidate_evidence_current=False,
        final_solver_claim_current=False,
        next_required_evidence=(
            "COMSOL clean mirror receipt with source path, git head, artifact hashes, "
            "and explicit launch/no-launch state"
        ),
        hard_fail_if="comsol_launch_or_mph_load_true_without_clean_mirror_receipt_packet",
    )


def _flow_solver_row(
    policy_by_task: Mapping[str, Mapping[str, Any]],
    flow_status: Mapping[str, Any],
) -> SidewallSolverBranchExecutionRow:
    policy = policy_by_task.get("trapezoid_flow_solver_preflight", {})
    return _row(
        branch_id="trapezoid_flow_solver",
        branch_name="Trapezoid pressure-flow solver branch",
        policy=policy,
        current_candidate_evidence_status=(
            "candidate_solver_output_available_not_q_ch_not_comsol_validated"
        ),
        candidate_evidence_artifact_id=str(flow_status.get("artifact_id", "")),
        candidate_evidence_disposition=str(flow_status.get("disposition", "")),
        candidate_source_head=str(flow_status.get("current_head", "")),
        candidate_rows=_int_value(flow_status.get("solver_candidate_rows")),
        candidate_output_rows=_int_value(flow_status.get("candidate_solver_output_rows")),
        blocked_rows=_int_value(flow_status.get("blocked_solver_rows")),
        execution_packet_status="flow_solver_branch_packet_required_before_formal_q_ch",
        next_execution_step=(
            "expand pressure-flow evidence with validation grid or COMSOL/solver "
            "comparison packet before q_ch weighting"
        ),
        current_claim_level="candidate_solver_output_not_q_ch_not_route_claim",
        candidate_evidence_current=_bool_value(
            flow_status.get("trapezoid_flow_solver_candidate_output_current")
        ),
        final_solver_claim_current=_bool_value(
            flow_status.get("trapezoid_flow_solver_final_claim_current")
        ),
        next_required_evidence=(
            "validated pressure-flow grid, solver tolerance, source hash, and "
            "formal q_ch binding contract"
        ),
        hard_fail_if="formal_q_ch_or_route_score_true_from_candidate_flow_solver_only",
    )


def _electrokinetic_solver_row(
    policy_by_task: Mapping[str, Mapping[str, Any]],
) -> SidewallSolverBranchExecutionRow:
    policy = policy_by_task.get("electrokinetic_grid_preflight", {})
    return _row(
        branch_id="electrokinetic_solver",
        branch_name="Profile-aware electrokinetic solver branch",
        policy=policy,
        current_candidate_evidence_status=(
            "preflight_authorized_profile_aware_grid_and_zeta_metadata_missing"
        ),
        candidate_evidence_artifact_id="",
        candidate_evidence_disposition="",
        candidate_source_head="",
        candidate_rows=0,
        candidate_output_rows=0,
        blocked_rows=1,
        execution_packet_status="electrokinetic_grid_packet_required",
        next_execution_step=(
            "define trapezoid cut-cell/FEM grid, zeta metadata, ionic strength, "
            "Debye length, and blocked-bin policy"
        ),
        current_claim_level="metadata_preflight_only_no_electrokinetic_solver_output",
        candidate_evidence_current=False,
        final_solver_claim_current=False,
        next_required_evidence=(
            "profile-aware electrokinetic grid, zeta/ionic-strength metadata, "
            "rectangle-limit test, and theta-mutation evidence"
        ),
        hard_fail_if="electrokinetic_weight_or_solver_claim_true_before_profile_aware_grid",
    )


def _optical_reference_solver_row(
    policy_by_task: Mapping[str, Mapping[str, Any]],
    reference_status: Mapping[str, Any],
    optical_calibration_status: Mapping[str, Any],
) -> SidewallSolverBranchExecutionRow:
    policy = policy_by_task.get("optical_reference_preflight", {})
    candidate_rows = _int_value(reference_status.get("surrogate_rows")) + _int_value(
        optical_calibration_status.get("seed_rows")
    )
    disposition = (
        f"reference={reference_status.get('disposition', '')};"
        f"calibration={optical_calibration_status.get('disposition', '')}"
    )
    artifact_ids = (
        f"{reference_status.get('artifact_id', '')};"
        f"{optical_calibration_status.get('artifact_id', '')}"
    )
    heads = (
        f"{reference_status.get('current_head', '')};"
        f"{optical_calibration_status.get('current_head', '')}"
    )
    final_claim = _bool_value(
        reference_status.get("full_wave_or_calibrated_optical_solver_current")
    ) or _bool_value(
        optical_calibration_status.get("full_wave_or_calibrated_optical_solver_current")
    )
    return _row(
        branch_id="optical_reference_solver",
        branch_name="Optical reference, true W_eff, and detector response branch",
        policy=policy,
        current_candidate_evidence_status=(
            "reference_surrogate_and_synthetic_calibration_seed_available_not_solver"
        ),
        candidate_evidence_artifact_id=artifact_ids,
        candidate_evidence_disposition=disposition,
        candidate_source_head=heads,
        candidate_rows=candidate_rows,
        candidate_output_rows=candidate_rows,
        blocked_rows=_int_value(optical_calibration_status.get("readiness_rows")),
        execution_packet_status="optical_solver_or_blank_calibration_packet_required",
        next_execution_step=(
            "bind blank-channel calibration or optical solver output to detector "
            "operator before true W_eff or detection probability"
        ),
        current_claim_level="surrogate_and_seed_only_not_optical_solver_not_detector_response",
        candidate_evidence_current=(
            _bool_value(reference_status.get("sidewall_reference_surrogate_current"))
            or _int_value(optical_calibration_status.get("seed_rows")) > 0
        ),
        final_solver_claim_current=final_claim,
        next_required_evidence=(
            "measured blank-channel amplitude/phase table or optical solver output, "
            "detector operator, ROI/slit throughput, and transfer validation"
        ),
        hard_fail_if="true_W_eff_detector_response_or_detection_probability_true_from_surrogate_seed",
    )


def _wet_detection_context_row(
    policy_by_task: Mapping[str, Mapping[str, Any]],
    wet_optical_status: Mapping[str, Any],
) -> SidewallSolverBranchExecutionRow:
    policy = policy_by_task.get("wet_ev_evidence_contract", {})
    return _row(
        branch_id="wet_optical_detection_evidence",
        branch_name="Wet EV, detection context, and passability evidence branch",
        policy=policy,
        current_candidate_evidence_status=(
            "nearest_geometry_context_available_not_sidewall_specific_wet_or_detection"
        ),
        candidate_evidence_artifact_id=str(wet_optical_status.get("artifact_id", "")),
        candidate_evidence_disposition=str(wet_optical_status.get("disposition", "")),
        candidate_source_head=str(wet_optical_status.get("current_head", "")),
        candidate_rows=_int_value(wet_optical_status.get("evidence_context_rows")),
        candidate_output_rows=_int_value(wet_optical_status.get("detection_context_available_rows")),
        blocked_rows=_int_value(wet_optical_status.get("boundary_context_rows")),
        execution_packet_status="wet_observation_and_detector_blank_packet_required",
        next_execution_step=(
            "ingest sidewall-specific wet observations and detector/blank transfer "
            "evidence with controls, uncertainty, and hashes"
        ),
        current_claim_level="context_only_not_detection_probability_not_yield",
        candidate_evidence_current=_int_value(
            wet_optical_status.get("evidence_context_rows")
        )
        > 0,
        final_solver_claim_current=False,
        next_required_evidence=(
            "accepted wet observation bundle, sidewall detector/blank transfer, "
            "replicates, controls, uncertainty, and preregistration"
        ),
        hard_fail_if="yield_detection_or_wet_pass_true_from_nearest_geometry_context_only",
    )


def _route_decision_row(
    policy_by_task: Mapping[str, Mapping[str, Any]],
    readiness_board_status: Mapping[str, Any],
) -> SidewallSolverBranchExecutionRow:
    policy = policy_by_task.get("route_promotion_contract", {})
    ready_count = _int_value(readiness_board_status.get("ready_route_input_count_total"))
    missing_count = _int_value(
        readiness_board_status.get("missing_claim_evidence_count_total")
    )
    return _row(
        branch_id="route_yield_detection_decision",
        branch_name="Integrated route, yield, and detection decision branch",
        policy=policy,
        current_candidate_evidence_status=(
            "route_inputs_partly_ready_claim_evidence_missing"
        ),
        candidate_evidence_artifact_id=str(readiness_board_status.get("artifact_id", "")),
        candidate_evidence_disposition=str(readiness_board_status.get("disposition", "")),
        candidate_source_head=str(readiness_board_status.get("current_head", "")),
        candidate_rows=_int_value(readiness_board_status.get("board_rows")),
        candidate_output_rows=ready_count,
        blocked_rows=missing_count,
        execution_packet_status="route_promotion_packet_blocked_until_branch_evidence_passes",
        next_execution_step=(
            "wait for flow/q_ch, optical/detection, and wet observation evidence "
            "packets; then bind route score and yield/detection formula text"
        ),
        current_claim_level="readiness_board_only_not_route_score_not_yield_not_detection",
        candidate_evidence_current=ready_count > 0,
        final_solver_claim_current=False,
        next_required_evidence=(
            "all blocker lanes resolved plus route score, winner, yield, and "
            "detection formula/hash contract"
        ),
        hard_fail_if="route_score_winner_yield_detection_true_before_all_branch_packets_pass",
    )


def _row(
    *,
    branch_id: str,
    branch_name: str,
    policy: Mapping[str, Any],
    current_candidate_evidence_status: str,
    candidate_evidence_artifact_id: str,
    candidate_evidence_disposition: str,
    candidate_source_head: str,
    candidate_rows: int,
    candidate_output_rows: int,
    blocked_rows: int,
    execution_packet_status: str,
    next_execution_step: str,
    current_claim_level: str,
    candidate_evidence_current: bool,
    final_solver_claim_current: bool,
    next_required_evidence: str,
    hard_fail_if: str,
) -> SidewallSolverBranchExecutionRow:
    return SidewallSolverBranchExecutionRow(
        branch_row_id=f"SOLVER-BRANCH-{branch_id}",
        packet_version=SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_VERSION,
        branch_id=branch_id,
        branch_name=branch_name,
        policy_task_id=str(policy.get("task_id", "")),
        user_authorization_status=str(policy.get("user_authorization_status", "")),
        authorized_to_prepare=_bool_value(policy.get("authorized_to_prepare")),
        authorized_to_execute_when_packet_passes=_bool_value(
            policy.get("authorized_to_execute_when_packet_passes")
        ),
        current_candidate_evidence_status=current_candidate_evidence_status,
        candidate_evidence_artifact_id=candidate_evidence_artifact_id,
        candidate_evidence_disposition=candidate_evidence_disposition,
        candidate_source_head=candidate_source_head,
        candidate_rows=candidate_rows,
        candidate_output_rows=candidate_output_rows,
        blocked_rows=blocked_rows,
        execution_packet_status=execution_packet_status,
        next_execution_step=next_execution_step,
        current_claim_level=current_claim_level,
        candidate_evidence_current=candidate_evidence_current,
        final_solver_claim_current=final_solver_claim_current,
        q_ch_weighting_current=False,
        route_score_current=False,
        winner_current=False,
        yield_current=False,
        detection_probability_current=False,
        wet_pass_claim_current=False,
        comsol_launch_allowed_now=False,
        mph_load_allowed_now=False,
        production_ingestion_current=False,
        next_required_evidence=next_required_evidence,
        hard_fail_if=hard_fail_if,
        claim_boundary=SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_CLAIM_BOUNDARY,
    )


def _claim_guard_rows(
    branch_rows: list[SidewallSolverBranchExecutionRow],
) -> list[SidewallSolverBranchClaimGuardRow]:
    evidence = {row.branch_id: row.candidate_evidence_current for row in branch_rows}
    specs = [
        (
            "final_trapezoid_flow_solver_claim",
            "trapezoid_flow_solver",
            "flow_solver_branch_packet_passed_with_validation_hashes",
            "validated pressure-flow grid and q_ch binding sidecar",
            "final_flow_solver_claim_true_without_validation_hashes",
        ),
        (
            "formal_q_ch_weighting",
            "trapezoid_flow_solver",
            "formal_qch_sidecar_passed",
            "solver output, pressure boundary, route normalization, and q_ch sidecar",
            "q_ch_weighting_true_without_formal_sidecar",
        ),
        (
            "electrokinetic_solver_claim",
            "electrokinetic_solver",
            "electrokinetic_profile_grid_packet_passed",
            "profile-aware grid, zeta, ionic strength, Debye length, and mutation tests",
            "electrokinetic_claim_true_without_profile_aware_grid",
        ),
        (
            "true_W_eff_and_detector_response",
            "optical_reference_solver",
            "optical_solver_or_blank_calibration_packet_passed",
            "optical solver or measured blank-channel calibration plus detector operator",
            "true_W_eff_or_detector_response_true_from_surrogate_seed",
        ),
        (
            "detection_probability",
            "wet_optical_detection_evidence",
            "detection_probability_packet_passed",
            "detector/blank transfer, threshold model, standard particles, and uncertainty",
            "detection_probability_true_without_detection_packet",
        ),
        (
            "wet_pass_yield_recovery",
            "wet_optical_detection_evidence",
            "wet_observation_bundle_passed",
            "sidewall-specific wet observations, controls, replicates, and uncertainty",
            "yield_or_wet_pass_true_without_accepted_wet_observation_bundle",
        ),
        (
            "route_score_winner_JRC",
            "route_yield_detection_decision",
            "route_decision_packet_passed",
            "all branch packets plus route-score formula, JRC policy, and source hashes",
            "route_score_or_winner_true_before_all_branch_packets_pass",
        ),
        (
            "fabrication_or_production_release",
            "route_yield_detection_decision",
            "separate_fabrication_release_packet_passed",
            "route decision, wet validation, fabrication tolerances, and release ledger",
            "production_or_fabrication_release_true_from_solver_packet",
        ),
    ]
    return [
        SidewallSolverBranchClaimGuardRow(
            guard_row_id=f"SOLVER-BRANCH-GUARD-{target}",
            packet_version=SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_VERSION,
            promotion_target=target,
            source_branch_id=branch_id,
            implementation_authorized=True,
            candidate_evidence_current=bool(evidence.get(branch_id, False)),
            claim_promoted_current=False,
            claim_promotion_allowed_now=False,
            first_allowed_status=first_allowed,
            required_evidence_before_true=required,
            hard_fail_if_missing_evidence=hard_fail,
            claim_boundary=SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_CLAIM_BOUNDARY,
        )
        for target, branch_id, first_allowed, required, hard_fail in specs
    ]


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _int_value(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if value is None or str(value).strip() == "":
        return 0
    return int(float(str(value)))
