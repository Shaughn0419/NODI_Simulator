"""Detector/wet closure harness for route/yield/detection formula binding."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_VERSION = (
    "sidewall_detector_wet_route_binding_closure_v1"
)
SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_CLAIM_BOUNDARY = (
    "detector_wet_route_binding_closure_not_route_score_not_yield_not_detection"
)
SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_STATUS = (
    "detector_wet_route_binding_closure_ready_accepted_rows_required"
)


@dataclass(frozen=True)
class SidewallDetectorWetRouteClosureRow:
    closure_row_id: str
    closure_version: str
    route_candidate_id: str
    route_geometry_family: str
    qch_route_input_ready: bool
    selected_annulus_context_ready: bool
    runtime_substep_guard_ready: bool
    profile_grid_candidate_ready: bool
    flow_solver_candidate_ready: bool
    detector_validator_hardened: bool
    wet_validator_hardened: bool
    detector_accepted_transfer_rows: int
    wet_accepted_observation_rows: int
    detector_fixture_rows: int
    wet_fixture_rows: int
    route_formula_binding_authorized: bool
    route_formula_binding_status: str
    route_score_current: bool
    winner_current: bool
    yield_current: bool
    detection_probability_current: bool
    next_required_evidence: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallDetectorWetClosureGuardRow:
    guard_row_id: str
    closure_version: str
    claim_target: str
    implementation_authorized: bool
    activation_allowed_now: bool
    required_evidence_before_activation: str
    current_blocker: str
    hard_fail_if_activated_early: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_detector_wet_route_binding_closure(
    *,
    route_evidence_state_rows: list[Mapping[str, Any]],
    route_candidate_status: Mapping[str, Any],
    selected_annulus_status: Mapping[str, Any],
    detector_execution_status: Mapping[str, Any],
    detector_validation_status: Mapping[str, Any],
    wet_execution_status: Mapping[str, Any],
    wet_validation_status: Mapping[str, Any],
) -> tuple[list[SidewallDetectorWetRouteClosureRow], list[SidewallDetectorWetClosureGuardRow]]:
    route_keys = sorted(
        {
            (str(row.get("route_candidate_id", "")), str(row.get("route_geometry_family", "")))
            for row in route_evidence_state_rows
            if str(row.get("route_candidate_id", ""))
        }
    )
    rows = [
        _closure_row(
            route_candidate_id=route_id,
            route_geometry_family=family,
            route_rows=[
                row
                for row in route_evidence_state_rows
                if str(row.get("route_candidate_id", "")) == route_id
            ],
            route_candidate_status=route_candidate_status,
            selected_annulus_status=selected_annulus_status,
            detector_execution_status=detector_execution_status,
            detector_validation_status=detector_validation_status,
            wet_execution_status=wet_execution_status,
            wet_validation_status=wet_validation_status,
        )
        for route_id, family in route_keys
    ]
    return rows, _guard_rows(rows)


def _closure_row(
    *,
    route_candidate_id: str,
    route_geometry_family: str,
    route_rows: list[Mapping[str, Any]],
    route_candidate_status: Mapping[str, Any],
    selected_annulus_status: Mapping[str, Any],
    detector_execution_status: Mapping[str, Any],
    detector_validation_status: Mapping[str, Any],
    wet_execution_status: Mapping[str, Any],
    wet_validation_status: Mapping[str, Any],
) -> SidewallDetectorWetRouteClosureRow:
    lanes = {str(row.get("evidence_lane", "")): row for row in route_rows}
    detector_accepted = _int(
        detector_execution_status.get("current_accepted_transfer_rows_total")
    )
    wet_accepted = _int(wet_execution_status.get("current_accepted_observation_rows_total"))
    binding_ready = detector_accepted > 0 and wet_accepted > 0
    return SidewallDetectorWetRouteClosureRow(
        closure_row_id=f"DETECTOR-WET-ROUTE-CLOSURE-{route_candidate_id}",
        closure_version=SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_VERSION,
        route_candidate_id=route_candidate_id,
        route_geometry_family=route_geometry_family,
        qch_route_input_ready=_lane_class(lanes, "q_ch_route_input") == "ready_route_input",
        selected_annulus_context_ready=_int(
            selected_annulus_status.get("selected_annulus_context_current_rows")
        )
        > 0,
        runtime_substep_guard_ready="runtime_substep_guard" in lanes,
        profile_grid_candidate_ready=_lane_class(lanes, "electrokinetic_profile_grid")
        == "candidate",
        flow_solver_candidate_ready=_lane_class(lanes, "flow_solver_candidate")
        == "candidate",
        detector_validator_hardened=_int(detector_validation_status.get("accepted_fixture_rows")) > 0,
        wet_validator_hardened=_int(wet_validation_status.get("accepted_fixture_rows")) > 0,
        detector_accepted_transfer_rows=detector_accepted,
        wet_accepted_observation_rows=wet_accepted,
        detector_fixture_rows=_int(detector_validation_status.get("accepted_fixture_rows")),
        wet_fixture_rows=_int(wet_validation_status.get("accepted_fixture_rows")),
        route_formula_binding_authorized=True,
        route_formula_binding_status=(
            "route_formula_binding_inputs_ready_for_candidate_values"
            if binding_ready
            else "blocked_accepted_detector_blank_and_wet_rows_required"
        ),
        route_score_current=False,
        winner_current=False,
        yield_current=False,
        detection_probability_current=False,
        next_required_evidence=(
            "accepted detector/blank transfer rows and accepted wet observation rows "
            "for both rectangle and trapezoid route candidates; selected-annulus context "
            "and q_ch inputs are already registered as inputs, not claims"
        ),
        hard_fail_if=(
            "fixture_context_or_ready_input_rows_activate_route_score_yield_or_detection"
        ),
        claim_boundary=SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_CLAIM_BOUNDARY,
    )


def _lane_class(lanes: dict[str, Mapping[str, Any]], lane: str) -> str:
    return str(lanes.get(lane, {}).get("evidence_class", ""))


def _guard_rows(
    rows: list[SidewallDetectorWetRouteClosureRow],
) -> list[SidewallDetectorWetClosureGuardRow]:
    detector_ready = all(row.detector_accepted_transfer_rows > 0 for row in rows)
    wet_ready = all(row.wet_accepted_observation_rows > 0 for row in rows)
    specs = [
        (
            "route_score_winner_JRC",
            detector_ready and wet_ready,
            "accepted detector/blank and wet rows for every route candidate",
            "detector/blank and wet accepted rows absent",
            "route_score_or_winner_true_without_detector_and_wet_closure",
        ),
        (
            "yield",
            wet_ready,
            "accepted wet observation rows with controls and uncertainty",
            "accepted wet observation rows absent",
            "yield_true_without_wet_closure",
        ),
        (
            "detection_probability",
            detector_ready,
            "accepted detector/blank transfer rows and threshold policy",
            "accepted detector/blank transfer rows absent",
            "detection_probability_true_without_detector_closure",
        ),
        (
            "wet_pass_clogging_recovery",
            wet_ready,
            "accepted wet time/end-point observations with denominators",
            "wet observation rows absent",
            "wet_claim_true_without_wet_closure",
        ),
        (
            "production_ingestion",
            False,
            "integrated closeout after route/yield/detection candidate values",
            "integrated closeout absent",
            "production_ingestion_true_from_closure_harness",
        ),
    ]
    return [
        SidewallDetectorWetClosureGuardRow(
            guard_row_id=f"DETECTOR-WET-CLOSURE-GUARD-{target}",
            closure_version=SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_VERSION,
            claim_target=target,
            implementation_authorized=True,
            activation_allowed_now=allowed,
            required_evidence_before_activation=required,
            current_blocker=blocker,
            hard_fail_if_activated_early=hard_fail,
            claim_boundary=SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_CLAIM_BOUNDARY,
        )
        for target, allowed, required, blocker, hard_fail in specs
    ]


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if value is None or str(value).strip() == "":
        return 0
    return int(float(str(value)))
