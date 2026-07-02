"""Mainline execution work order for sidewall Package C follow-through."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_VERSION = (
    "sidewall_mainline_execution_work_order_v1"
)
SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_CLAIM_BOUNDARY = (
    "mainline_execution_work_order_authorized_execute_evidence_gated_claims"
)
SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_STATUS = (
    "mainline_execution_work_order_ready_large_blocks_prioritized"
)


@dataclass(frozen=True)
class SidewallMainlineExecutionWorkOrderRow:
    work_order_id: str
    work_order_version: str
    priority: int
    lane: str
    owner_packet_id: str
    source_disposition: str
    route_geometry_scope: str
    implementation_authorized: bool
    codex_can_execute_next: bool
    external_or_lab_input_required: bool
    current_evidence_rows: int
    accepted_evidence_rows: int
    claim_activation_allowed_now: bool
    current_blocker: str
    next_action: str
    intended_next_artifact: str
    acceptance_checks: str
    downstream_unlocked_when_pass: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallMainlineClaimActivationGuardRow:
    guard_row_id: str
    work_order_version: str
    claim_target: str
    implementation_authorized: bool
    activation_allowed_now: bool
    required_work_orders_before_activation: str
    current_blocker: str
    hard_fail_if_activated_early: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallRouteEvidenceRegisterRow:
    register_row_id: str
    work_order_version: str
    route_candidate_id: str
    route_geometry_family: str
    evidence_lane: str
    evidence_class: str
    source_artifact_id: str
    source_head: str
    evidence_rows: int
    accepted_claim_evidence_rows: int
    may_satisfy_route_formula_now: bool
    may_satisfy_yield_now: bool
    may_satisfy_detection_now: bool
    current_blocker: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_mainline_execution_work_order(
    *,
    solver_status: Mapping[str, Any],
    electrokinetic_status: Mapping[str, Any],
    comsol_status: Mapping[str, Any],
    detector_status: Mapping[str, Any],
    wet_status: Mapping[str, Any],
    route_status: Mapping[str, Any],
    route_rows: list[Mapping[str, Any]],
) -> tuple[
    list[SidewallMainlineExecutionWorkOrderRow],
    list[SidewallMainlineClaimActivationGuardRow],
    list[SidewallRouteEvidenceRegisterRow],
]:
    route_families = _route_geometry_scope(route_rows, route_status)
    detector_accepted = _int(detector_status.get("current_accepted_transfer_rows_total"))
    wet_accepted = _int(wet_status.get("current_accepted_observation_rows_total"))
    comsol_target_bound = _int(comsol_status.get("target_model_bound_rows"))
    comsol_command_bound = _int(comsol_status.get("launch_command_hash_bound_rows"))
    electrokinetic_grid_rows = _int(electrokinetic_status.get("profile_aware_grid_current_rows"))
    route_formula_ready = detector_accepted > 0 and wet_accepted > 0

    rows = [
        _row(
            work_order_id="WO-001-current-head-source-lock",
            priority=10,
            lane="source_lock_and_commit_binding",
            owner_packet_id="562",
            source_status=route_status,
            route_geometry_scope=route_families,
            codex_can_execute_next=True,
            external_or_lab_input_required=False,
            current_evidence_rows=_int(route_status.get("readiness_rows")),
            accepted_evidence_rows=0,
            claim_activation_allowed_now=False,
            current_blocker="downstream evidence packets must be regenerated from current reviewed head before claim activation",
            next_action=(
                "bind the latest committed NODI head, source locks, and work-order "
                "hashes before executing the next evidence-producing blocks"
            ),
            intended_next_artifact="current_head_source_lock_receipt",
            acceptance_checks=(
                "source_missing_rows=0; release_scoped_dirty_blocker_rows=0; "
                "rectangle and trapezoid routes both present"
            ),
            downstream_unlocked_when_pass="safe local execution of profile-grid and runtime-policy blocks",
            hard_fail_if="rectangle_baseline_or_trapezoid_route_missing_from_work_order",
        ),
        _row(
            work_order_id="WO-002-comsol-target-binding",
            priority=20,
            lane="comsol_target_model_and_command_binding",
            owner_packet_id=str(comsol_status.get("artifact_id", "")),
            source_status=comsol_status,
            route_geometry_scope=route_families,
            codex_can_execute_next=True,
            external_or_lab_input_required=True,
            current_evidence_rows=_int(comsol_status.get("precondition_passed_rows")),
            accepted_evidence_rows=min(comsol_target_bound, comsol_command_bound),
            claim_activation_allowed_now=comsol_target_bound > 0 and comsol_command_bound > 0,
            current_blocker="target model/script and launch command hash are not bound",
            next_action=(
                "bind clean current-head COMSOL mirror receipt, target .mph/script, "
                "command hash, output manifest, and no-overwrite policy"
            ),
            intended_next_artifact="comsol_target_binding_and_dry_run_receipt",
            acceptance_checks=(
                "target_model_bound_rows>0; launch_command_hash_bound_rows>0; "
                "mph_load_allowed only after explicit target binding"
            ),
            downstream_unlocked_when_pass="COMSOL sidewall solver execution under bounded command receipt",
            hard_fail_if="comsol_launch_or_mph_load_true_without_target_and_command_hash",
        ),
        _row(
            work_order_id="WO-003-electrokinetic-profile-grid",
            priority=30,
            lane="electrokinetic_profile_aware_grid",
            owner_packet_id=str(electrokinetic_status.get("artifact_id", "")),
            source_status=electrokinetic_status,
            route_geometry_scope=route_families,
            codex_can_execute_next=True,
            external_or_lab_input_required=False,
            current_evidence_rows=_int(electrokinetic_status.get("preflight_rows")),
            accepted_evidence_rows=electrokinetic_grid_rows,
            claim_activation_allowed_now=electrokinetic_grid_rows > 0,
            current_blocker="profile-aware grid implementation and rectangle/theta mutation tests are absent",
            next_action=(
                "implement cut-cell or signed-distance grid metadata with zeta, "
                "ionic strength, Debye length, blocked-bin exclusion, rectangle limit, "
                "and theta mutation checks"
            ),
            intended_next_artifact="electrokinetic_profile_grid_candidate_packet",
            acceptance_checks=(
                "profile_aware_grid_current_rows>0; rectangle baseline preserved; "
                "theta mutation changes electrokinetic wall-distance weights"
            ),
            downstream_unlocked_when_pass="electrokinetic weighting candidate, not route score",
            hard_fail_if="electrokinetic_weight_or_detection_true_before_profile_grid_tests",
        ),
        _row(
            work_order_id="WO-004-detector-blank-transfer",
            priority=40,
            lane="detector_blank_transfer_evidence",
            owner_packet_id=str(detector_status.get("artifact_id", "")),
            source_status=detector_status,
            route_geometry_scope=route_families,
            codex_can_execute_next=True,
            external_or_lab_input_required=True,
            current_evidence_rows=_int(detector_status.get("candidate_or_fixture_rows_total")),
            accepted_evidence_rows=detector_accepted,
            claim_activation_allowed_now=detector_accepted > 0,
            current_blocker="accepted sidewall-specific or validated-transfer detector/blank rows are absent",
            next_action=(
                "ingest or generate accepted detector/blank transfer rows with "
                "readout path, ROI policy, blank denominator, threshold policy, "
                "uncertainty, and source hashes"
            ),
            intended_next_artifact="detector_blank_transfer_accepted_evidence_packet",
            acceptance_checks=(
                "current_accepted_transfer_rows_total>0; sidewall blank or validated "
                "transfer present for rectangle and trapezoid routes"
            ),
            downstream_unlocked_when_pass="detection-probability formula input eligibility",
            hard_fail_if="detection_probability_or_route_score_true_without_accepted_transfer_rows",
        ),
        _row(
            work_order_id="WO-005-wet-observation",
            priority=50,
            lane="wet_observation_evidence",
            owner_packet_id=str(wet_status.get("artifact_id", "")),
            source_status=wet_status,
            route_geometry_scope=route_families,
            codex_can_execute_next=True,
            external_or_lab_input_required=True,
            current_evidence_rows=_int(wet_status.get("contract_or_fixture_rows_total")),
            accepted_evidence_rows=wet_accepted,
            claim_activation_allowed_now=wet_accepted > 0,
            current_blocker="accepted wet observation rows with controls and uncertainty are absent",
            next_action=(
                "ingest accepted wet observations for passability, clogging/time, "
                "recovery, yield context, controls, replicates, uncertainty, and hashes"
            ),
            intended_next_artifact="wet_observation_accepted_evidence_packet",
            acceptance_checks=(
                "current_accepted_observation_rows_total>0; controls, replicates, "
                "uncertainty, geometry match, and preregistration present"
            ),
            downstream_unlocked_when_pass="yield and wet-performance formula input eligibility",
            hard_fail_if="yield_or_wet_pass_true_without_accepted_wet_observations",
        ),
        _row(
            work_order_id="WO-006-route-yield-detection-formula-binding",
            priority=60,
            lane="route_yield_detection_formula_binding",
            owner_packet_id=str(route_status.get("artifact_id", "")),
            source_status=route_status,
            route_geometry_scope=route_families,
            codex_can_execute_next=True,
            external_or_lab_input_required=False,
            current_evidence_rows=_int(route_status.get("readiness_rows")),
            accepted_evidence_rows=min(detector_accepted, wet_accepted),
            claim_activation_allowed_now=route_formula_ready,
            current_blocker="detector/blank and wet accepted evidence are both required before formula binding",
            next_action=(
                "prepare formula-binding schema now, but activate route_score, "
                "winner, yield, and detection only after detector and wet rows pass"
            ),
            intended_next_artifact="route_yield_detection_formula_binding_candidate",
            acceptance_checks=(
                "detector_accepted_transfer_rows_total>0; "
                "wet_accepted_observation_rows_total>0; q_ch input hashes bound; "
                "rectangle and trapezoid routes both scored"
            ),
            downstream_unlocked_when_pass="route score, yield, detection candidate values",
            hard_fail_if="route_score_winner_yield_detection_true_before_detector_and_wet_pass",
        ),
        _row(
            work_order_id="WO-007-runtime-substep-policy",
            priority=70,
            lane="reflection_runtime_substep_policy",
            owner_packet_id=str(solver_status.get("artifact_id", "")),
            source_status=solver_status,
            route_geometry_scope=route_families,
            codex_can_execute_next=True,
            external_or_lab_input_required=False,
            current_evidence_rows=_int(solver_status.get("candidate_evidence_current_rows")),
            accepted_evidence_rows=0,
            claim_activation_allowed_now=False,
            current_blocker="runtime substep/fail policy is not yet bound to large-step and near-closed guards",
            next_action=(
                "convert reflection proof metrics into runtime guard policy: rms-step "
                "margin, corner active-set limit, substep trigger, and fail-closed status"
            ),
            intended_next_artifact="reflection_runtime_substep_policy_packet",
            acceptance_checks=(
                "substep_trigger_policy present; max displacement guard present; "
                "near-closed geometry blocks runtime or substeps deterministically"
            ),
            downstream_unlocked_when_pass="bounded NODI sidewall trajectory runtime guard",
            hard_fail_if="trajectory_runtime_enabled_without_substep_or_near_closed_guard",
        ),
        _row(
            work_order_id="WO-008-mainline-integration-closeout",
            priority=80,
            lane="mainline_integration_and_release_closeout",
            owner_packet_id="562",
            source_status=solver_status,
            route_geometry_scope=route_families,
            codex_can_execute_next=True,
            external_or_lab_input_required=False,
            current_evidence_rows=_int(solver_status.get("branch_rows")),
            accepted_evidence_rows=0,
            claim_activation_allowed_now=False,
            current_blocker="branch evidence is distributed across packets and needs a single promotion ledger after inputs pass",
            next_action=(
                "after WO-002 through WO-007 pass, rebuild integrated promotion ledger, "
                "claim scanner, and production-preflight release table"
            ),
            intended_next_artifact="sidewall_package_c_integrated_execution_closeout",
            acceptance_checks=(
                "all prerequisite work orders pass; no forbidden claim columns; "
                "source hashes bind every accepted evidence row"
            ),
            downstream_unlocked_when_pass="production-preflight review, not fabrication release",
            hard_fail_if="production_ingestion_true_before_integrated_closeout_and_release_ledger",
        ),
    ]
    guards = _guard_rows(route_formula_ready, detector_accepted, wet_accepted, electrokinetic_grid_rows)
    register = _route_evidence_register_rows(
        route_rows=route_rows,
        electrokinetic_status=electrokinetic_status,
        comsol_status=comsol_status,
        detector_status=detector_status,
        wet_status=wet_status,
        route_status=route_status,
        detector_accepted=detector_accepted,
        wet_accepted=wet_accepted,
        electrokinetic_grid_rows=electrokinetic_grid_rows,
        comsol_target_bound=comsol_target_bound,
        comsol_command_bound=comsol_command_bound,
    )
    return rows, guards, register


def _row(
    *,
    work_order_id: str,
    priority: int,
    lane: str,
    owner_packet_id: str,
    source_status: Mapping[str, Any],
    route_geometry_scope: str,
    codex_can_execute_next: bool,
    external_or_lab_input_required: bool,
    current_evidence_rows: int,
    accepted_evidence_rows: int,
    claim_activation_allowed_now: bool,
    current_blocker: str,
    next_action: str,
    intended_next_artifact: str,
    acceptance_checks: str,
    downstream_unlocked_when_pass: str,
    hard_fail_if: str,
) -> SidewallMainlineExecutionWorkOrderRow:
    return SidewallMainlineExecutionWorkOrderRow(
        work_order_id=work_order_id,
        work_order_version=SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_VERSION,
        priority=priority,
        lane=lane,
        owner_packet_id=owner_packet_id,
        source_disposition=str(source_status.get("disposition", "")),
        route_geometry_scope=route_geometry_scope,
        implementation_authorized=True,
        codex_can_execute_next=codex_can_execute_next,
        external_or_lab_input_required=external_or_lab_input_required,
        current_evidence_rows=current_evidence_rows,
        accepted_evidence_rows=accepted_evidence_rows,
        claim_activation_allowed_now=claim_activation_allowed_now,
        current_blocker=current_blocker,
        next_action=next_action,
        intended_next_artifact=intended_next_artifact,
        acceptance_checks=acceptance_checks,
        downstream_unlocked_when_pass=downstream_unlocked_when_pass,
        hard_fail_if=hard_fail_if,
        claim_boundary=SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_CLAIM_BOUNDARY,
    )


def _guard_rows(
    route_formula_ready: bool,
    detector_accepted: int,
    wet_accepted: int,
    electrokinetic_grid_rows: int,
) -> list[SidewallMainlineClaimActivationGuardRow]:
    specs = [
        (
            "comsol_launch_and_mph_load",
            False,
            "WO-002-comsol-target-binding",
            "target model/script and command hash not bound in current work order",
            "comsol_launch_or_mph_load_true_before_target_binding",
        ),
        (
            "electrokinetic_weight",
            electrokinetic_grid_rows > 0,
            "WO-003-electrokinetic-profile-grid",
            "profile-aware grid candidate rows are absent",
            "electrokinetic_weight_true_without_profile_grid",
        ),
        (
            "detection_probability",
            detector_accepted > 0 and route_formula_ready,
            "WO-004-detector-blank-transfer;WO-006-route-yield-detection-formula-binding",
            "detector/blank accepted transfer rows are absent",
            "detection_probability_true_without_accepted_detector_blank_transfer",
        ),
        (
            "yield",
            wet_accepted > 0 and route_formula_ready,
            "WO-005-wet-observation;WO-006-route-yield-detection-formula-binding",
            "wet accepted observation rows are absent",
            "yield_true_without_accepted_wet_observations",
        ),
        (
            "route_score_winner_JRC",
            route_formula_ready,
            "WO-004-detector-blank-transfer;WO-005-wet-observation;WO-006-route-yield-detection-formula-binding",
            "detector/blank and wet accepted evidence are absent",
            "route_score_winner_or_JRC_true_before_route_formula_binding",
        ),
        (
            "runtime_sidewall_trajectory",
            False,
            "WO-007-runtime-substep-policy",
            "runtime substep/fail policy is not yet bound",
            "runtime_sidewall_trajectory_enabled_without_substep_policy",
        ),
        (
            "production_ingestion",
            False,
            "WO-008-mainline-integration-closeout",
            "integrated release ledger is not complete",
            "production_ingestion_true_before_integrated_closeout",
        ),
    ]
    return [
        SidewallMainlineClaimActivationGuardRow(
            guard_row_id=f"MAINLINE-GUARD-{target}",
            work_order_version=SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_VERSION,
            claim_target=target,
            implementation_authorized=True,
            activation_allowed_now=allowed,
            required_work_orders_before_activation=required,
            current_blocker=blocker,
            hard_fail_if_activated_early=hard_fail,
            claim_boundary=SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_CLAIM_BOUNDARY,
        )
        for target, allowed, required, blocker, hard_fail in specs
    ]


def _route_evidence_register_rows(
    *,
    route_rows: list[Mapping[str, Any]],
    electrokinetic_status: Mapping[str, Any],
    comsol_status: Mapping[str, Any],
    detector_status: Mapping[str, Any],
    wet_status: Mapping[str, Any],
    route_status: Mapping[str, Any],
    detector_accepted: int,
    wet_accepted: int,
    electrokinetic_grid_rows: int,
    comsol_target_bound: int,
    comsol_command_bound: int,
) -> list[SidewallRouteEvidenceRegisterRow]:
    rows: list[SidewallRouteEvidenceRegisterRow] = []
    for route in route_rows:
        route_candidate_id = str(route.get("route_candidate_id", ""))
        route_geometry_family = str(route.get("route_geometry_family", ""))
        rows.extend(
            [
                _register_row(
                    route_candidate_id=route_candidate_id,
                    route_geometry_family=route_geometry_family,
                    evidence_lane="q_ch_route_input",
                    evidence_class="ready_route_input",
                    source_status=route_status,
                    evidence_rows=1,
                    accepted_claim_evidence_rows=0,
                    may_satisfy_route_formula_now=False,
                    may_satisfy_yield_now=False,
                    may_satisfy_detection_now=False,
                    current_blocker="q_ch is a ready route input but not a route score or q_ch weighting claim",
                    hard_fail_if="q_ch_route_input_promoted_to_route_score_without_formula_packet",
                ),
                _register_row(
                    route_candidate_id=route_candidate_id,
                    route_geometry_family=route_geometry_family,
                    evidence_lane="detector_blank_transfer",
                    evidence_class=(
                        "current_accepted_claim_evidence"
                        if detector_accepted > 0
                        else "fixture_or_context_available_no_accepted_claim_evidence"
                    ),
                    source_status=detector_status,
                    evidence_rows=_int(detector_status.get("candidate_or_fixture_rows_total")),
                    accepted_claim_evidence_rows=detector_accepted,
                    may_satisfy_route_formula_now=detector_accepted > 0 and wet_accepted > 0,
                    may_satisfy_yield_now=False,
                    may_satisfy_detection_now=detector_accepted > 0,
                    current_blocker="accepted detector/blank transfer rows are absent",
                    hard_fail_if="fixture_or_context_detector_rows_satisfy_detection_or_route_score",
                ),
                _register_row(
                    route_candidate_id=route_candidate_id,
                    route_geometry_family=route_geometry_family,
                    evidence_lane="wet_observation",
                    evidence_class=(
                        "current_accepted_claim_evidence"
                        if wet_accepted > 0
                        else "fixture_or_contract_available_no_accepted_claim_evidence"
                    ),
                    source_status=wet_status,
                    evidence_rows=_int(wet_status.get("contract_or_fixture_rows_total")),
                    accepted_claim_evidence_rows=wet_accepted,
                    may_satisfy_route_formula_now=detector_accepted > 0 and wet_accepted > 0,
                    may_satisfy_yield_now=wet_accepted > 0,
                    may_satisfy_detection_now=False,
                    current_blocker="accepted wet observation rows are absent",
                    hard_fail_if="fixture_or_contract_wet_rows_satisfy_yield_or_wet_pass",
                ),
                _register_row(
                    route_candidate_id=route_candidate_id,
                    route_geometry_family=route_geometry_family,
                    evidence_lane="electrokinetic_profile_grid",
                    evidence_class=(
                        "candidate"
                        if electrokinetic_grid_rows > 0
                        else "preflight_requirement"
                    ),
                    source_status=electrokinetic_status,
                    evidence_rows=_int(electrokinetic_status.get("preflight_rows")),
                    accepted_claim_evidence_rows=electrokinetic_grid_rows,
                    may_satisfy_route_formula_now=False,
                    may_satisfy_yield_now=False,
                    may_satisfy_detection_now=False,
                    current_blocker="profile-aware grid rows are absent",
                    hard_fail_if="electrokinetic_preflight_used_as_route_or_detection_claim",
                ),
                _register_row(
                    route_candidate_id=route_candidate_id,
                    route_geometry_family=route_geometry_family,
                    evidence_lane="comsol_target_binding",
                    evidence_class=(
                        "candidate"
                        if comsol_target_bound > 0 and comsol_command_bound > 0
                        else "precondition_only"
                    ),
                    source_status=comsol_status,
                    evidence_rows=_int(comsol_status.get("precondition_rows")),
                    accepted_claim_evidence_rows=min(comsol_target_bound, comsol_command_bound),
                    may_satisfy_route_formula_now=False,
                    may_satisfy_yield_now=False,
                    may_satisfy_detection_now=False,
                    current_blocker="COMSOL target model and command hash are not bound",
                    hard_fail_if="comsol_precondition_used_as_solver_or_route_claim",
                ),
            ]
        )
    return rows


def _register_row(
    *,
    route_candidate_id: str,
    route_geometry_family: str,
    evidence_lane: str,
    evidence_class: str,
    source_status: Mapping[str, Any],
    evidence_rows: int,
    accepted_claim_evidence_rows: int,
    may_satisfy_route_formula_now: bool,
    may_satisfy_yield_now: bool,
    may_satisfy_detection_now: bool,
    current_blocker: str,
    hard_fail_if: str,
) -> SidewallRouteEvidenceRegisterRow:
    return SidewallRouteEvidenceRegisterRow(
        register_row_id=f"ROUTE-EVIDENCE-{route_candidate_id}-{evidence_lane}",
        work_order_version=SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_VERSION,
        route_candidate_id=route_candidate_id,
        route_geometry_family=route_geometry_family,
        evidence_lane=evidence_lane,
        evidence_class=evidence_class,
        source_artifact_id=str(source_status.get("artifact_id", "")),
        source_head=str(source_status.get("current_head", "")),
        evidence_rows=evidence_rows,
        accepted_claim_evidence_rows=accepted_claim_evidence_rows,
        may_satisfy_route_formula_now=may_satisfy_route_formula_now,
        may_satisfy_yield_now=may_satisfy_yield_now,
        may_satisfy_detection_now=may_satisfy_detection_now,
        current_blocker=current_blocker,
        hard_fail_if=hard_fail_if,
        claim_boundary=SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_CLAIM_BOUNDARY,
    )


def _route_geometry_scope(
    route_rows: list[Mapping[str, Any]],
    route_status: Mapping[str, Any],
) -> str:
    families = sorted(
        {
            str(row.get("route_geometry_family", "")).strip()
            for row in route_rows
            if str(row.get("route_geometry_family", "")).strip()
        }
    )
    if families:
        return ";".join(families)
    return str(route_status.get("route_geometry_families", ""))


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if value is None or str(value).strip() == "":
        return 0
    return int(float(str(value)))
