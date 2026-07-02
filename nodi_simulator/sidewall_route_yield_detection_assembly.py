"""Route/yield/detection assembly rows for sidewall Package C.

The assembly consumes the current integrated promotion ledger and route policy
rows. It is a coordination artifact, not a route score, winner, yield, wet pass,
or detection-probability calculation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_VERSION = (
    "sidewall_route_yield_detection_assembly_v2"
)
SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_CLAIM_BOUNDARY = (
    "route_yield_detection_assembly_not_route_score_not_yield_not_detection_probability"
)
ASSEMBLY_NOT_CLAIM_READY_STATUS = (
    "assembly_ready_for_detector_blank_transfer_and_wet_input_not_claim_ready"
)
ASSEMBLY_INPUT_READY_STATUS = "ready_input_not_final_claim"
ASSEMBLY_CONTEXT_STATUS = "candidate_context_not_claim_ready"
ASSEMBLY_MISSING_STATUS = "missing_required_observation_or_calibration"

ROUTE_READY_INPUT_LANES: tuple[str, ...] = (
    "flow_split_qch",
    "pressure_flow_validation",
    "selected_annulus_detection_context",
)
ROUTE_BLOCKING_LANES: tuple[str, ...] = (
    "detector_response_bridge",
    "blank_false_positive_trace",
    "wet_wall_interaction",
)
ROUTE_CONTEXT_LANES: tuple[str, ...] = (
    "blank_channel_reference_amplitude_phase",
    "sidewall_geometry_coverage",
    "integrated_route_ledger",
)


@dataclass(frozen=True)
class SidewallRouteYieldDetectionAssemblyRow:
    assembly_row_id: str
    assembly_version: str
    route_candidate_id: str
    route_key: str
    route_geometry_family: str
    source_case_id: str
    qch_sidecar_id: str
    flow_split_qch_status: str
    pressure_flow_validation_status: str
    selected_annulus_detection_context_status: str
    detector_response_bridge_status: str
    blank_false_positive_trace_status: str
    wet_wall_interaction_status: str
    blank_channel_reference_status: str
    sidewall_geometry_coverage_status: str
    integrated_route_policy_status: str
    route_policy_status: str
    primary_next_execution_block: str
    ready_input_lane_count: int
    candidate_context_lane_count: int
    missing_or_blocked_lane_count: int
    total_tracked_lane_count: int
    input_completeness_fraction: float
    assembly_status: str
    next_executable_branch: str
    next_required_evidence: str
    route_score_allowed: bool
    winner_allowed: bool
    yield_allowed: bool
    detection_probability_allowed: bool
    wet_pass_probability_allowed: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallRouteYieldDetectionBranchRow:
    branch_row_id: str
    assembly_version: str
    route_candidate_id: str
    branch_name: str
    branch_status: str
    branch_basis: str
    minimum_next_input: str
    target_claim: str
    target_claim_current: bool
    implementation_can_start: bool
    result_claim_requires_future_evidence: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_route_yield_detection_assembly(
    promotion_lane_rows: list[Mapping[str, Any]],
    policy_rows: list[Mapping[str, Any]],
    blocker_rows: list[Mapping[str, Any]],
) -> tuple[
    list[SidewallRouteYieldDetectionAssemblyRow],
    list[SidewallRouteYieldDetectionBranchRow],
]:
    lanes_by_route = _lanes_by_route(promotion_lane_rows)
    policy_by_route = {
        str(row.get("route_candidate_id", "")): row for row in policy_rows
    }
    blockers_by_route = _blockers_by_route(blocker_rows)
    assembly_rows: list[SidewallRouteYieldDetectionAssemblyRow] = []
    branch_rows: list[SidewallRouteYieldDetectionBranchRow] = []
    for route_id, lanes in sorted(lanes_by_route.items()):
        representative = _representative_row(lanes)
        policy = policy_by_route.get(route_id, {})
        blocker_map = blockers_by_route.get(route_id, {})
        lane_statuses = {
            lane: str(lanes.get(lane, {}).get("current_status", "lane_missing"))
            for lane in (
                *ROUTE_READY_INPUT_LANES,
                *ROUTE_BLOCKING_LANES,
                *ROUTE_CONTEXT_LANES,
            )
        }
        ready_inputs = sum(
            _lane_classification(lane, lane_statuses[lane], blocker_map)
            == ASSEMBLY_INPUT_READY_STATUS
            for lane in ROUTE_READY_INPUT_LANES
        )
        candidate_context = sum(
            _lane_classification(lane, lane_statuses[lane], blocker_map)
            == ASSEMBLY_CONTEXT_STATUS
            for lane in (*ROUTE_BLOCKING_LANES, *ROUTE_CONTEXT_LANES)
        )
        missing_or_blocked = sum(
            _lane_classification(lane, lane_statuses[lane], blocker_map)
            == ASSEMBLY_MISSING_STATUS
            for lane in (*ROUTE_BLOCKING_LANES, *ROUTE_CONTEXT_LANES)
        )
        total = len(ROUTE_READY_INPUT_LANES) + len(ROUTE_BLOCKING_LANES) + len(
            ROUTE_CONTEXT_LANES
        )
        next_branch = str(
            policy.get(
                "primary_next_execution_block",
                "sidewall_detector_blank_transfer_validation",
            )
        )
        next_required = _route_next_required_evidence(lanes, policy, blocker_map)
        assembly_rows.append(
            SidewallRouteYieldDetectionAssemblyRow(
                assembly_row_id=f"RYD-ASSEMBLY-{route_id}",
                assembly_version=SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_VERSION,
                route_candidate_id=route_id,
                route_key=str(representative.get("route_key", "")),
                route_geometry_family=_route_geometry_family(representative),
                source_case_id=str(representative.get("source_case_id", "")),
                qch_sidecar_id=str(representative.get("qch_sidecar_id", "")),
                flow_split_qch_status=lane_statuses["flow_split_qch"],
                pressure_flow_validation_status=lane_statuses["pressure_flow_validation"],
                selected_annulus_detection_context_status=lane_statuses[
                    "selected_annulus_detection_context"
                ],
                detector_response_bridge_status=lane_statuses["detector_response_bridge"],
                blank_false_positive_trace_status=lane_statuses[
                    "blank_false_positive_trace"
                ],
                wet_wall_interaction_status=lane_statuses["wet_wall_interaction"],
                blank_channel_reference_status=lane_statuses[
                    "blank_channel_reference_amplitude_phase"
                ],
                sidewall_geometry_coverage_status=lane_statuses[
                    "sidewall_geometry_coverage"
                ],
                integrated_route_policy_status=lane_statuses["integrated_route_ledger"],
                route_policy_status=str(policy.get("route_policy_status", "")),
                primary_next_execution_block=next_branch,
                ready_input_lane_count=ready_inputs,
                candidate_context_lane_count=candidate_context,
                missing_or_blocked_lane_count=missing_or_blocked,
                total_tracked_lane_count=total,
                input_completeness_fraction=round(ready_inputs / len(ROUTE_READY_INPUT_LANES), 6),
                assembly_status=ASSEMBLY_NOT_CLAIM_READY_STATUS,
                next_executable_branch=next_branch,
                next_required_evidence=next_required,
                route_score_allowed=False,
                winner_allowed=False,
                yield_allowed=False,
                detection_probability_allowed=False,
                wet_pass_probability_allowed=False,
                claim_boundary=SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_CLAIM_BOUNDARY,
            )
        )
        branch_rows.extend(_branch_rows(route_id, lanes, policy, blocker_map))
    return assembly_rows, branch_rows


def _lanes_by_route(
    rows: list[Mapping[str, Any]],
) -> dict[str, dict[str, Mapping[str, Any]]]:
    output: dict[str, dict[str, Mapping[str, Any]]] = {}
    for row in rows:
        route_id = str(row.get("route_candidate_id", ""))
        lane = str(row.get("evidence_lane", ""))
        if not route_id or not lane:
            continue
        output.setdefault(route_id, {})[lane] = row
    return output


def _blockers_by_route(
    rows: list[Mapping[str, Any]],
) -> dict[str, dict[str, Mapping[str, Any]]]:
    output: dict[str, dict[str, Mapping[str, Any]]] = {}
    for row in rows:
        route_id = str(row.get("route_candidate_id", ""))
        lane = str(row.get("evidence_lane", ""))
        if not route_id or not lane:
            continue
        output.setdefault(route_id, {})[lane] = row
    return output


def _representative_row(lanes: dict[str, Mapping[str, Any]]) -> Mapping[str, Any]:
    for lane in ("flow_split_qch", "pressure_flow_validation", "integrated_route_ledger"):
        if lane in lanes:
            return lanes[lane]
    return next(iter(lanes.values()), {})


def _route_geometry_family(row: Mapping[str, Any]) -> str:
    route_key = str(row.get("route_key", ""))
    source_case_id = str(row.get("source_case_id", ""))
    text = f"{route_key} {source_case_id}"
    if "rectangle" in text or "theta90" in text:
        return "ideal_rectangle"
    if "taper" in text or "theta85" in text:
        return "trapezoid_tapered_sidewalls"
    return "geometry_family_unspecified"


def _lane_classification(
    lane: str,
    status: str,
    blocker_map: dict[str, Mapping[str, Any]],
) -> str:
    blocker_status = str(blocker_map.get(lane, {}).get("blocker_status", ""))
    if lane in ROUTE_READY_INPUT_LANES and blocker_status == "ready_for_route_input_not_final_claim":
        return ASSEMBLY_INPUT_READY_STATUS
    if lane == "detector_response_bridge" and status == (
        "detector_response_panel_candidate_not_sidewall_calibrated"
    ):
        return ASSEMBLY_CONTEXT_STATUS
    if lane == "blank_false_positive_trace" and status == (
        "nearest_blank_guard_bound_to_panel_not_sidewall_specific"
    ):
        return ASSEMBLY_CONTEXT_STATUS
    if lane == "integrated_route_ledger" and status == (
        "route_yield_detection_policy_defined_not_ready_for_claims"
    ):
        return ASSEMBLY_CONTEXT_STATUS
    if lane in ROUTE_CONTEXT_LANES and status and status != "lane_missing":
        return ASSEMBLY_CONTEXT_STATUS
    return ASSEMBLY_MISSING_STATUS


def _route_next_required_evidence(
    lanes: dict[str, Mapping[str, Any]],
    policy: Mapping[str, Any],
    blocker_map: dict[str, Mapping[str, Any]],
) -> str:
    items: list[str] = []
    policy_text = str(policy.get("next_required_evidence", "")).strip()
    if policy_text:
        items.append(policy_text)
    for lane in ROUTE_BLOCKING_LANES:
        text = str(blocker_map.get(lane, {}).get("next_required_evidence", "")).strip()
        if text and text not in items:
            items.append(text)
        lane_text = str(lanes.get(lane, {}).get("next_required_evidence", "")).strip()
        if lane_text and lane_text not in items:
            items.append(lane_text)
    return " | ".join(items)


def _branch_rows(
    route_id: str,
    lanes: dict[str, Mapping[str, Any]],
    policy: Mapping[str, Any],
    blocker_map: dict[str, Mapping[str, Any]],
) -> list[SidewallRouteYieldDetectionBranchRow]:
    branch_specs = [
        (
            "sidewall_detector_blank_transfer_validation",
            "implementation_ready_from_panel_candidate_requires_sidewall_specific_transfer_evidence",
            "detector_response_bridge;blank_false_positive_trace",
            _minimum_input_for(
                lanes,
                blocker_map,
                ("detector_response_bridge", "blank_false_positive_trace"),
            ),
            "detection_probability",
            True,
            "sidewall-specific blank traces or validated transferable blank false-positive model plus detector response validation",
        ),
        (
            "wet_observation_bundle_intake",
            "schema_ready_waiting_for_observation_rows",
            "wet_wall_interaction",
            _minimum_input_for(lanes, blocker_map, ("wet_wall_interaction",)),
            "yield;wet_pass_probability",
            True,
            "accepted sidewall-specific or validated-transfer wet observation endpoint bundle",
        ),
        (
            "route_candidate_assembly",
            "assembly_rows_available_not_route_score",
            "flow_split_qch;pressure_flow_validation;selected_annulus_detection_context;integrated_route_ledger",
            str(policy.get("next_required_evidence", "")),
            "route_score;winner",
            True,
            "detector, blank, wet, and explicit decision policy evidence",
        ),
        (
            "detection_probability_calibration",
            "blocked_until_detector_blank_and_optical_calibration_are_validated",
            "selected_annulus_detection_context;detector_response_bridge;blank_false_positive_trace",
            "sidewall-specific optical/reference calibration, detector response validation, and blank false-positive model",
            "detection_probability",
            False,
            "calibrated detector model and sidewall-specific blank transfer evidence",
        ),
    ]
    return [
        SidewallRouteYieldDetectionBranchRow(
            branch_row_id=f"RYD-BRANCH-{route_id}-{branch_name}",
            assembly_version=SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_VERSION,
            route_candidate_id=route_id,
            branch_name=branch_name,
            branch_status=branch_status,
            branch_basis=branch_basis,
            minimum_next_input=minimum_next_input,
            target_claim=target_claim,
            target_claim_current=False,
            implementation_can_start=implementation_can_start,
            result_claim_requires_future_evidence=future_evidence,
            claim_boundary=SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_CLAIM_BOUNDARY,
        )
        for (
            branch_name,
            branch_status,
            branch_basis,
            minimum_next_input,
            target_claim,
            implementation_can_start,
            future_evidence,
        ) in branch_specs
    ]


def _minimum_input_for(
    lanes: dict[str, Mapping[str, Any]],
    blocker_map: dict[str, Mapping[str, Any]],
    evidence_lanes: tuple[str, ...],
) -> str:
    items: list[str] = []
    for lane in evidence_lanes:
        blocker_text = str(blocker_map.get(lane, {}).get("next_required_evidence", "")).strip()
        lane_text = str(lanes.get(lane, {}).get("next_required_evidence", "")).strip()
        for text in (blocker_text, lane_text):
            if text and text not in items:
                items.append(text)
    return " | ".join(items)
