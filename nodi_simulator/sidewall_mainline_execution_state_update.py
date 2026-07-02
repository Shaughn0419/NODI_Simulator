"""Current-state update for the sidewall Package C execution mainline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_VERSION = (
    "sidewall_mainline_execution_state_update_v1"
)
SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_CLAIM_BOUNDARY = (
    "mainline_state_update_candidate_evidence_not_route_yield_detection"
)
SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_STATUS = (
    "mainline_state_update_ready_runtime_and_profile_grid_integrated"
)


@dataclass(frozen=True)
class SidewallMainlineWorkOrderStateRow:
    state_row_id: str
    state_version: str
    work_order_id: str
    lane: str
    previous_blocker: str
    current_state: str
    current_evidence_artifact_id: str
    current_evidence_disposition: str
    current_evidence_rows: int
    claim_activation_allowed_now: bool
    next_required_action: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallRouteEvidenceStateRow:
    evidence_state_row_id: str
    state_version: str
    route_candidate_id: str
    route_geometry_family: str
    evidence_lane: str
    evidence_class: str
    source_artifact_id: str
    source_disposition: str
    evidence_rows: int
    accepted_claim_evidence_rows: int
    may_satisfy_route_formula_now: bool
    may_satisfy_yield_now: bool
    may_satisfy_detection_now: bool
    current_state: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallMainlineStateGuardRow:
    guard_row_id: str
    state_version: str
    claim_target: str
    activation_allowed_now: bool
    current_blocker: str
    required_next_evidence: str
    hard_fail_if_activated_early: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_mainline_execution_state_update(
    *,
    work_order_rows: list[Mapping[str, Any]],
    route_evidence_register_rows: list[Mapping[str, Any]],
    runtime_status: Mapping[str, Any],
    profile_grid_status: Mapping[str, Any],
    flow_solver_status: Mapping[str, Any],
    comsol_status: Mapping[str, Any],
    detector_status: Mapping[str, Any],
    wet_status: Mapping[str, Any],
    route_status: Mapping[str, Any],
) -> tuple[
    list[SidewallMainlineWorkOrderStateRow],
    list[SidewallRouteEvidenceStateRow],
    list[SidewallMainlineStateGuardRow],
]:
    work_states = _work_order_state_rows(
        work_order_rows=work_order_rows,
        runtime_status=runtime_status,
        profile_grid_status=profile_grid_status,
        flow_solver_status=flow_solver_status,
        comsol_status=comsol_status,
        detector_status=detector_status,
        wet_status=wet_status,
        route_status=route_status,
    )
    route_states = _route_evidence_state_rows(
        route_evidence_register_rows=route_evidence_register_rows,
        runtime_status=runtime_status,
        profile_grid_status=profile_grid_status,
        flow_solver_status=flow_solver_status,
    )
    guards = _guard_rows(
        detector_accepted=_int(detector_status.get("current_accepted_transfer_rows_total")),
        wet_accepted=_int(wet_status.get("current_accepted_observation_rows_total")),
        comsol_target_bound=_int(comsol_status.get("target_model_bound_rows")),
        comsol_command_bound=_int(comsol_status.get("launch_command_hash_bound_rows")),
    )
    return work_states, route_states, guards


def _work_order_state_rows(
    *,
    work_order_rows: list[Mapping[str, Any]],
    runtime_status: Mapping[str, Any],
    profile_grid_status: Mapping[str, Any],
    flow_solver_status: Mapping[str, Any],
    comsol_status: Mapping[str, Any],
    detector_status: Mapping[str, Any],
    wet_status: Mapping[str, Any],
    route_status: Mapping[str, Any],
) -> list[SidewallMainlineWorkOrderStateRow]:
    status_by_work_order = {
        "WO-001-current-head-source-lock": (
            "current_source_lock_receipt_available",
            "PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_20260701",
            "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_READY_LARGE_BLOCKS_PRIORITIZED",
            len(work_order_rows),
            "keep regenerating downstream evidence from the latest committed head",
            "source_lock_missing_or_route_geometry_scope_lost",
        ),
        "WO-002-comsol-target-binding": (
            "open_target_binding_required",
            str(comsol_status.get("artifact_id", "")),
            str(comsol_status.get("disposition", "")),
            _int(comsol_status.get("precondition_rows")),
            "bind target .mph/script and launch command hash before any COMSOL run",
            "comsol_launch_true_without_target_binding",
        ),
        "WO-003-electrokinetic-profile-grid": (
            "candidate_profile_grid_available_not_solver",
            str(profile_grid_status.get("artifact_id", "")),
            str(profile_grid_status.get("disposition", "")),
            _int(profile_grid_status.get("profile_aware_grid_current_rows")),
            "calibrate or solve electrokinetic model before using weights in route formulas",
            "electrokinetic_weight_true_from_candidate_grid_only",
        ),
        "WO-004-detector-blank-transfer": (
            "open_accepted_transfer_rows_required",
            str(detector_status.get("artifact_id", "")),
            str(detector_status.get("disposition", "")),
            _int(detector_status.get("current_accepted_transfer_rows_total")),
            "ingest accepted detector/blank transfer rows for both route families",
            "detection_probability_true_without_accepted_transfer_rows",
        ),
        "WO-005-wet-observation": (
            "open_accepted_wet_rows_required",
            str(wet_status.get("artifact_id", "")),
            str(wet_status.get("disposition", "")),
            _int(wet_status.get("current_accepted_observation_rows_total")),
            "ingest accepted wet observation rows with controls and uncertainty",
            "yield_or_wet_claim_true_without_accepted_wet_rows",
        ),
        "WO-006-route-yield-detection-formula-binding": (
            "open_formula_binding_waiting_for_detector_and_wet",
            str(route_status.get("artifact_id", "")),
            str(route_status.get("disposition", "")),
            _int(route_status.get("readiness_rows")),
            "prepare formula schema but activate only after detector and wet rows pass",
            "route_score_yield_detection_true_before_detector_and_wet",
        ),
        "WO-007-runtime-substep-policy": (
            "guarded_runtime_smoke_available_stress_blocked",
            str(runtime_status.get("artifact_id", "")),
            str(runtime_status.get("disposition", "")),
            _int(runtime_status.get("guarded_runtime_smoke_executed")),
            "keep stress/prohibitive runtime blocked or substeped before PRS/EAS pilot",
            "sidewall_runtime_enabled_without_guarded_substep_policy",
        ),
        "WO-008-mainline-integration-closeout": (
            "open_until_external_input_lanes_close",
            str(flow_solver_status.get("artifact_id", "")),
            str(flow_solver_status.get("disposition", "")),
            _int(flow_solver_status.get("candidate_solver_output_rows")),
            "refresh integrated promotion ledger after COMSOL/detector/wet lanes close",
            "production_ingestion_true_before_integrated_closeout",
        ),
    }
    rows: list[SidewallMainlineWorkOrderStateRow] = []
    for row in work_order_rows:
        work_order_id = str(row.get("work_order_id", ""))
        state = status_by_work_order.get(
            work_order_id,
            (
                "unknown_work_order",
                "",
                "",
                0,
                "review unknown work order",
                "unknown_work_order_in_mainline_state_update",
            ),
        )
        rows.append(
            SidewallMainlineWorkOrderStateRow(
                state_row_id=f"MAINLINE-STATE-{work_order_id}",
                state_version=SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_VERSION,
                work_order_id=work_order_id,
                lane=str(row.get("lane", "")),
                previous_blocker=str(row.get("current_blocker", "")),
                current_state=state[0],
                current_evidence_artifact_id=state[1],
                current_evidence_disposition=state[2],
                current_evidence_rows=state[3],
                claim_activation_allowed_now=False,
                next_required_action=state[4],
                hard_fail_if=state[5],
                claim_boundary=SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_CLAIM_BOUNDARY,
            )
        )
    return rows


def _route_evidence_state_rows(
    *,
    route_evidence_register_rows: list[Mapping[str, Any]],
    runtime_status: Mapping[str, Any],
    profile_grid_status: Mapping[str, Any],
    flow_solver_status: Mapping[str, Any],
) -> list[SidewallRouteEvidenceStateRow]:
    rows: list[SidewallRouteEvidenceStateRow] = []
    for row in route_evidence_register_rows:
        lane = str(row.get("evidence_lane", ""))
        evidence_class = str(row.get("evidence_class", ""))
        source_artifact_id = str(row.get("source_artifact_id", ""))
        source_disposition = str(row.get("source_disposition", ""))
        evidence_rows = _int(row.get("evidence_rows"))
        accepted_rows = _int(row.get("accepted_claim_evidence_rows"))
        current_state = "unchanged_from_562_register"
        if lane == "electrokinetic_profile_grid":
            evidence_class = (
                "candidate"
                if _int(profile_grid_status.get("profile_aware_grid_current_rows")) > 0
                else evidence_class
            )
            source_artifact_id = str(profile_grid_status.get("artifact_id", ""))
            source_disposition = str(profile_grid_status.get("disposition", ""))
            evidence_rows = _int(profile_grid_status.get("profile_aware_grid_current_rows"))
            current_state = "profile_grid_candidate_available_not_route_weight"
        rows.append(
            _route_state_row(
                source=row,
                evidence_lane=lane,
                evidence_class=evidence_class,
                source_artifact_id=source_artifact_id,
                source_disposition=source_disposition,
                evidence_rows=evidence_rows,
                accepted_rows=accepted_rows,
                current_state=current_state,
                hard_fail_if=str(row.get("hard_fail_if", "")),
            )
        )

    route_keys = {
        (str(row.get("route_candidate_id", "")), str(row.get("route_geometry_family", "")))
        for row in route_evidence_register_rows
    }
    for route_candidate_id, route_geometry_family in sorted(route_keys):
        rows.append(
            _route_state_row(
                source={
                    "route_candidate_id": route_candidate_id,
                    "route_geometry_family": route_geometry_family,
                },
                evidence_lane="runtime_substep_guard",
                evidence_class="guarded_runtime_smoke_evidence",
                source_artifact_id=str(runtime_status.get("artifact_id", "")),
                source_disposition=str(runtime_status.get("disposition", "")),
                evidence_rows=_int(runtime_status.get("guarded_runtime_smoke_executed")),
                accepted_rows=0,
                current_state="low_cost_smoke_passed_stress_case_blocked",
                hard_fail_if="runtime_substep_guard_used_as_prs_eas_numeric_output",
            )
        )
        rows.append(
            _route_state_row(
                source={
                    "route_candidate_id": route_candidate_id,
                    "route_geometry_family": route_geometry_family,
                },
                evidence_lane="flow_solver_candidate",
                evidence_class="candidate" if route_geometry_family == "trapezoid_tapered_sidewalls" else "not_applicable_rectangle_baseline",
                source_artifact_id=str(flow_solver_status.get("artifact_id", "")),
                source_disposition=str(flow_solver_status.get("disposition", "")),
                evidence_rows=(
                    _int(flow_solver_status.get("candidate_solver_output_rows"))
                    if route_geometry_family == "trapezoid_tapered_sidewalls"
                    else 0
                ),
                accepted_rows=0,
                current_state="flow_solver_candidate_available_not_qch_weighting",
                hard_fail_if="flow_solver_candidate_used_as_route_score_or_formal_qch_weight",
            )
        )
    return rows


def _route_state_row(
    *,
    source: Mapping[str, Any],
    evidence_lane: str,
    evidence_class: str,
    source_artifact_id: str,
    source_disposition: str,
    evidence_rows: int,
    accepted_rows: int,
    current_state: str,
    hard_fail_if: str,
) -> SidewallRouteEvidenceStateRow:
    return SidewallRouteEvidenceStateRow(
        evidence_state_row_id=(
            f"ROUTE-EVIDENCE-STATE-{source.get('route_candidate_id', '')}-{evidence_lane}"
        ),
        state_version=SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_VERSION,
        route_candidate_id=str(source.get("route_candidate_id", "")),
        route_geometry_family=str(source.get("route_geometry_family", "")),
        evidence_lane=evidence_lane,
        evidence_class=evidence_class,
        source_artifact_id=source_artifact_id,
        source_disposition=source_disposition,
        evidence_rows=evidence_rows,
        accepted_claim_evidence_rows=accepted_rows,
        may_satisfy_route_formula_now=False,
        may_satisfy_yield_now=False,
        may_satisfy_detection_now=False,
        current_state=current_state,
        hard_fail_if=hard_fail_if,
        claim_boundary=SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_CLAIM_BOUNDARY,
    )


def _guard_rows(
    *,
    detector_accepted: int,
    wet_accepted: int,
    comsol_target_bound: int,
    comsol_command_bound: int,
) -> list[SidewallMainlineStateGuardRow]:
    specs = [
        (
            "comsol_launch",
            comsol_target_bound > 0 and comsol_command_bound > 0,
            "target binding and command hash absent",
            "WO-002 target binding receipt",
            "comsol_launch_true_without_target_binding",
        ),
        (
            "route_score_winner_JRC",
            detector_accepted > 0 and wet_accepted > 0,
            "detector/blank and wet accepted evidence absent",
            "WO-004 and WO-005 accepted evidence rows",
            "route_score_true_without_detector_and_wet_evidence",
        ),
        (
            "yield",
            wet_accepted > 0,
            "wet accepted evidence absent",
            "WO-005 accepted wet observation rows",
            "yield_true_without_accepted_wet_evidence",
        ),
        (
            "detection_probability",
            detector_accepted > 0,
            "detector/blank accepted evidence absent",
            "WO-004 accepted detector/blank transfer rows",
            "detection_probability_true_without_accepted_detector_evidence",
        ),
        (
            "production_ingestion",
            False,
            "integrated closeout absent",
            "WO-008 integrated release closeout",
            "production_ingestion_true_before_closeout",
        ),
    ]
    return [
        SidewallMainlineStateGuardRow(
            guard_row_id=f"MAINLINE-STATE-GUARD-{target}",
            state_version=SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_VERSION,
            claim_target=target,
            activation_allowed_now=allowed,
            current_blocker=blocker,
            required_next_evidence=required,
            hard_fail_if_activated_early=hard_fail,
            claim_boundary=SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_CLAIM_BOUNDARY,
        )
        for target, allowed, blocker, required, hard_fail in specs
    ]


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if value is None or str(value).strip() == "":
        return 0
    return int(float(str(value)))
