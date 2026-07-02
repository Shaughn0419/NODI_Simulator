"""Route/yield/detection readiness policy for sidewall promotion lanes.

This module consumes the latest integrated promotion ledger and reduces it to
route-level readiness rows. It does not compute route_score, winner, yield, or
detection probability; it records exactly which evidence gates still prevent
those claims.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_VERSION = (
    "sidewall_route_yield_detection_readiness_policy_v1"
)
SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_CLAIM_BOUNDARY = (
    "route_yield_detection_policy_not_route_score_not_yield_not_detection_probability"
)
ROUTE_POLICY_READY_STATUS = "ready_for_route_yield_detection_claims"
ROUTE_POLICY_NOT_READY_STATUS = (
    "not_ready_missing_detector_blank_wet_selected_annulus_evidence_after_formal_qch_pressure_flow"
)
FORMAL_QCH_READY_STATUS = (
    "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting"
)
EXACT_PRESSURE_FLOW_READY_STATUS = (
    "exact_w500_d900_pressure_flow_result_accepted_formal_qch_sidecar_ready"
)
ROUTE_INPUT_READY_BLOCKER_STATUS = "ready_for_route_input_not_final_claim"
SELECTED_ANNULUS_PANEL_STATUS = (
    "expanded_selected_annulus_panel_available_not_probability"
)
DETECTOR_RESPONSE_PANEL_STATUS = (
    "detector_response_panel_candidate_not_sidewall_calibrated"
)
BLANK_GUARD_PANEL_STATUS = "nearest_blank_guard_bound_to_panel_not_sidewall_specific"
WET_OBSERVATION_INTAKE_STATUS = "wet_surface_observation_intake_ready_no_observations"
DETECTOR_BLANK_TRANSFER_NO_EVIDENCE_STATUS = (
    "detector_blank_transfer_intake_ready_no_transfer_evidence"
)
DETECTOR_BLANK_TRANSFER_ACCEPTED_STATUS = (
    "detector_blank_transfer_bundle_candidate_ready_requires_policy_review"
)
WET_OBSERVATION_ACCEPTED_STATUS = (
    "wet_surface_observation_bundle_candidate_ready_requires_policy_review"
)

REQUIRED_LANES: tuple[str, ...] = (
    "flow_split_qch",
    "pressure_flow_validation",
    "selected_annulus_detection_context",
    "detector_response_bridge",
    "blank_false_positive_trace",
    "wet_wall_interaction",
)


@dataclass(frozen=True)
class SidewallRouteYieldDetectionPolicyRow:
    policy_row_id: str
    policy_version: str
    route_candidate_id: str
    route_key: str
    source_case_id: str
    qch_sidecar_id: str
    qch_policy_status: str
    pressure_flow_policy_status: str
    selected_annulus_policy_status: str
    detector_response_policy_status: str
    blank_false_positive_policy_status: str
    wet_surface_policy_status: str
    route_policy_status: str
    primary_next_execution_block: str
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
class SidewallRouteYieldDetectionBlockerRow:
    blocker_id: str
    route_candidate_id: str
    evidence_lane: str
    current_status: str
    blocker_status: str
    target_claim: str
    next_required_evidence: str
    hard_fail_if_promoted_without: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_route_yield_detection_policy_rows(
    promotion_lane_rows: list[Mapping[str, Any]],
) -> tuple[
    list[SidewallRouteYieldDetectionPolicyRow],
    list[SidewallRouteYieldDetectionBlockerRow],
]:
    lanes_by_route = _lanes_by_route(promotion_lane_rows)
    policy_rows: list[SidewallRouteYieldDetectionPolicyRow] = []
    blocker_rows: list[SidewallRouteYieldDetectionBlockerRow] = []
    for route_id, lanes in sorted(lanes_by_route.items()):
        representative = next(iter(lanes.values()))
        blockers = [_lane_blocker(lane, lanes.get(lane, {})) for lane in REQUIRED_LANES]
        qch_status = _qch_policy_status(lanes.get("flow_split_qch", {}))
        pressure_status = _pressure_flow_policy_status(
            lanes.get("pressure_flow_validation", {})
        )
        annulus_status = _selected_annulus_policy_status(
            lanes.get("selected_annulus_detection_context", {})
        )
        detector_status = _detector_policy_status(lanes.get("detector_response_bridge", {}))
        blank_status = _blank_policy_status(lanes.get("blank_false_positive_trace", {}))
        wet_status = _wet_policy_status(lanes.get("wet_wall_interaction", {}))
        route_ready = all(
            blocker in {"ready_for_claim_use", ROUTE_INPUT_READY_BLOCKER_STATUS}
            for blocker in blockers
        )
        next_block = _primary_next_block(
            qch_status,
            pressure_status,
            annulus_status,
            detector_status,
            blank_status,
            wet_status,
        )
        next_required = _next_required_evidence(lanes)
        policy_rows.append(
            SidewallRouteYieldDetectionPolicyRow(
                policy_row_id=f"RYD-POLICY-{route_id}",
                policy_version=SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_VERSION,
                route_candidate_id=route_id,
                route_key=str(representative.get("route_key", "")),
                source_case_id=str(representative.get("source_case_id", "")),
                qch_sidecar_id=str(representative.get("qch_sidecar_id", "")),
                qch_policy_status=qch_status,
                pressure_flow_policy_status=pressure_status,
                selected_annulus_policy_status=annulus_status,
                detector_response_policy_status=detector_status,
                blank_false_positive_policy_status=blank_status,
                wet_surface_policy_status=wet_status,
                route_policy_status=(
                    ROUTE_POLICY_READY_STATUS
                    if route_ready
                    else ROUTE_POLICY_NOT_READY_STATUS
                ),
                primary_next_execution_block=next_block,
                next_required_evidence=next_required,
                route_score_allowed=False,
                winner_allowed=False,
                yield_allowed=False,
                detection_probability_allowed=False,
                wet_pass_probability_allowed=False,
                claim_boundary=SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_CLAIM_BOUNDARY,
            )
        )
        for lane in REQUIRED_LANES:
            row = lanes.get(lane, {})
            blocker_rows.append(
                SidewallRouteYieldDetectionBlockerRow(
                    blocker_id=f"RYD-BLOCKER-{route_id}-{lane}",
                    route_candidate_id=route_id,
                    evidence_lane=lane,
                    current_status=str(row.get("current_status", "lane_missing")),
                    blocker_status=_lane_blocker(lane, row),
                    target_claim=str(row.get("target_claim", "")),
                    next_required_evidence=str(row.get("next_required_evidence", "")),
                    hard_fail_if_promoted_without=str(
                        row.get("hard_fail_if_promoted_without", "")
                    ),
                    claim_boundary=SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_CLAIM_BOUNDARY,
                )
            )
    return policy_rows, blocker_rows


def route_yield_detection_policy_promotion_update_rows(
    rows: list[SidewallRouteYieldDetectionPolicyRow],
) -> list[dict[str, str]]:
    route_ids = sorted({row.route_candidate_id for row in rows})
    return [
        {
            "target_ledger_lane": "integrated_route_ledger",
            "covered_route_candidate_ids": ";".join(route_ids),
            "previous_status": "blocked_missing_calibrated_optical_wet_route_evidence",
            "new_context_status": (
                "route_yield_detection_policy_defined_not_ready_for_claims"
            ),
            "target_claim_current": "false",
            "blocked_promotion": "route_score;winner;yield;detection_probability;wet_pass_probability",
            "hard_fail_if": "route_policy_context_promoted_to_route_score_or_probability",
            "next_required_evidence": (
                "detector/blank calibration, selected-annulus event panel expansion, "
                "and wet/surface validation"
            ),
            "claim_boundary": SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_CLAIM_BOUNDARY,
        }
    ]


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


def _lane_blocker(lane: str, row: Mapping[str, Any]) -> str:
    if not row:
        return "missing_lane"
    status = str(row.get("current_status", ""))
    if lane == "flow_split_qch" and status == FORMAL_QCH_READY_STATUS:
        return ROUTE_INPUT_READY_BLOCKER_STATUS
    if lane == "pressure_flow_validation" and status == EXACT_PRESSURE_FLOW_READY_STATUS:
        return ROUTE_INPUT_READY_BLOCKER_STATUS
    if lane == "selected_annulus_detection_context" and status == SELECTED_ANNULUS_PANEL_STATUS:
        return ROUTE_INPUT_READY_BLOCKER_STATUS
    if lane in {
        "detector_response_bridge",
        "blank_false_positive_trace",
    } and status == DETECTOR_BLANK_TRANSFER_ACCEPTED_STATUS:
        return ROUTE_INPUT_READY_BLOCKER_STATUS
    if lane == "wet_wall_interaction" and status == WET_OBSERVATION_ACCEPTED_STATUS:
        return ROUTE_INPUT_READY_BLOCKER_STATUS
    if str(row.get("target_claim_current", "")).lower() != "true":
        return "blocked_not_claim_ready"
    return "ready_for_claim_use"


def _qch_policy_status(row: Mapping[str, Any]) -> str:
    status = str(row.get("current_status", ""))
    if status == FORMAL_QCH_READY_STATUS:
        return "ready_formal_qch_sidecar_input_not_route_weighting"
    if status == "w500_d900_grid_refined_split_candidate_absolute_q_requires_validation":
        return "not_ready_grid_refined_split_candidate_absolute_q_requires_validation"
    return "not_ready_formal_qch_missing"


def _pressure_flow_policy_status(row: Mapping[str, Any]) -> str:
    status = str(row.get("current_status", ""))
    if status == EXACT_PRESSURE_FLOW_READY_STATUS:
        return "ready_exact_pressure_flow_validation_for_formal_qch_input"
    if status == "context_only_not_formal_validation":
        return "not_ready_pressure_flow_context_only"
    return "not_ready_pressure_flow_validation_missing"


def _selected_annulus_policy_status(row: Mapping[str, Any]) -> str:
    status = str(row.get("current_status", ""))
    if status == SELECTED_ANNULUS_PANEL_STATUS:
        return "ready_selected_annulus_event_panel_input_not_probability"
    if status == "selected_annulus_context_available_small_n_not_probability":
        return "not_ready_selected_annulus_small_n_not_probability"
    return "not_ready_selected_annulus_context_missing"


def _detector_policy_status(row: Mapping[str, Any]) -> str:
    status = str(row.get("current_status", ""))
    if status == DETECTOR_BLANK_TRANSFER_ACCEPTED_STATUS:
        return "ready_detector_blank_transfer_candidate_for_policy_review_not_probability"
    if status == DETECTOR_BLANK_TRANSFER_NO_EVIDENCE_STATUS:
        return "not_ready_detector_transfer_intake_ready_no_transfer_evidence"
    if status == DETECTOR_RESPONSE_PANEL_STATUS:
        return "not_ready_detector_response_panel_candidate_needs_sidewall_calibration"
    if status == "detector_identity_context_available_not_sidewall_response_validation":
        return "not_ready_detector_identity_context_not_response_validation"
    return "not_ready_detector_response_validation_missing"


def _blank_policy_status(row: Mapping[str, Any]) -> str:
    status = str(row.get("current_status", ""))
    if status == DETECTOR_BLANK_TRANSFER_ACCEPTED_STATUS:
        return "ready_blank_false_positive_transfer_candidate_for_policy_review_not_probability"
    if status == DETECTOR_BLANK_TRANSFER_NO_EVIDENCE_STATUS:
        return "not_ready_blank_transfer_intake_ready_no_transfer_evidence"
    if status == BLANK_GUARD_PANEL_STATUS:
        return "not_ready_blank_guard_panel_bound_needs_sidewall_specific_transfer"
    if status == "nearest_blank_context_available_not_sidewall_specific_validation":
        return "not_ready_nearest_blank_context_not_sidewall_specific_validation"
    return "not_ready_blank_false_positive_validation_missing"


def _wet_policy_status(row: Mapping[str, Any]) -> str:
    status = str(row.get("current_status", ""))
    if status == WET_OBSERVATION_ACCEPTED_STATUS:
        return "ready_wet_observation_bundle_candidate_for_policy_review_not_yield"
    if status == WET_OBSERVATION_INTAKE_STATUS:
        return "not_ready_wet_observation_intake_ready_no_observations"
    if status == "wet_surface_evidence_contract_defined_no_wet_validation":
        return "not_ready_wet_surface_contract_defined_no_validation"
    return "not_ready_wet_surface_evidence_missing"


def _primary_next_block(*statuses: str) -> str:
    actionable = [status for status in statuses if not status.startswith("ready_")]
    priority = (
        ("qch_or_pressure_flow_validation", ("qch_missing", "pressure_flow")),
        (
            "sidewall_detector_blank_transfer_validation",
            (
                "sidewall_calibration",
                "sidewall_specific_transfer",
                "blank_guard_panel_bound",
                "transfer_intake_ready_no_transfer_evidence",
            ),
        ),
        ("detector_blank_calibration", ("detector", "blank")),
        ("wet_surface_validation", ("wet_surface",)),
        ("selected_annulus_event_panel_expansion", ("selected_annulus",)),
    )
    for block, fragments in priority:
        if any(any(fragment in status for fragment in fragments) for status in actionable):
            return block
    return "no_primary_blocker_detected"


def _next_required_evidence(lanes: dict[str, Mapping[str, Any]]) -> str:
    items: list[str] = []
    for lane in REQUIRED_LANES:
        text = str(lanes.get(lane, {}).get("next_required_evidence", "")).strip()
        if text and text not in items:
            items.append(text)
    return " | ".join(items)
