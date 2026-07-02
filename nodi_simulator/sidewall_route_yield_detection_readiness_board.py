"""Route-level readiness board for sidewall route/yield/detection evidence.

This reducer joins the formal q_ch receipt bridge, route policy, assembly,
detector/blank transfer intake, and wet/surface observation intake. It reports
what is ready as route input and what still blocks route, yield, wet-pass, or
detection claims.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_VERSION = (
    "sidewall_route_yield_detection_readiness_board_v2"
)
SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_CLAIM_BOUNDARY = (
    "route_yield_detection_readiness_board_not_route_score_not_yield_not_detection_probability"
)
READINESS_BOARD_STATUS = (
    "route_inputs_ready_waiting_detector_blank_and_wet_evidence_not_claim_ready"
)
READINESS_BOARD_FORMULA_POLICY_REVIEW_STATUS = (
    "route_inputs_and_formula_components_ready_for_policy_review_not_claim_ready"
)
READY_ROUTE_INPUT = "ready_route_input_not_final_claim"
MISSING_CLAIM_EVIDENCE = "missing_required_claim_evidence"
CONTEXT_READY = "context_ready_not_final_claim"


@dataclass(frozen=True)
class SidewallRouteYieldDetectionReadinessBoardRow:
    board_row_id: str
    board_version: str
    route_candidate_id: str
    route_key: str
    route_geometry_family: str
    source_case_id: str
    qch_sidecar_id: str
    formal_qch_sidecar_id: str
    q_ch_m3_s: float
    formal_flow_split_fraction: float
    qch_route_input_status: str
    pressure_flow_route_input_status: str
    selected_annulus_context_status: str
    detector_blank_transfer_status: str
    wet_observation_status: str
    route_formula_component_status: str
    detector_wet_activation_status: str
    route_formula_dry_run_status: str
    route_formula_component_vector_ready: bool
    ready_route_input_count: int
    missing_claim_evidence_count: int
    readiness_fraction: float
    primary_next_execution_block: str
    secondary_next_execution_block: str
    board_status: str
    route_score_current: bool
    winner_current: bool
    yield_current: bool
    detection_probability_current: bool
    wet_pass_probability_current: bool
    production_ingestion_current: bool
    hard_fail_if: str
    next_required_evidence: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallRouteYieldDetectionReadinessBlockerRow:
    blocker_row_id: str
    board_version: str
    route_candidate_id: str
    evidence_lane: str
    readiness_class: str
    current_status: str
    target_claim: str
    target_claim_current: bool
    next_required_evidence: str
    hard_fail_if_promoted_without: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_route_yield_detection_readiness_board(
    *,
    formal_qch_bridge_rows: list[Mapping[str, Any]],
    policy_rows: list[Mapping[str, Any]],
    policy_blocker_rows: list[Mapping[str, Any]],
    assembly_rows: list[Mapping[str, Any]],
    detector_transfer_audit_rows: list[Mapping[str, Any]],
    wet_observation_audit_rows: list[Mapping[str, Any]],
    detector_wet_activation_rows: list[Mapping[str, Any]] | None = None,
    route_formula_dry_run_rows: list[Mapping[str, Any]] | None = None,
) -> tuple[
    list[SidewallRouteYieldDetectionReadinessBoardRow],
    list[SidewallRouteYieldDetectionReadinessBlockerRow],
]:
    qch_by_route = _by_route(formal_qch_bridge_rows)
    policy_by_route = _by_route(policy_rows)
    assembly_by_route = _by_route(assembly_rows)
    transfer_by_route = _by_route(detector_transfer_audit_rows)
    wet_by_route = _by_route(wet_observation_audit_rows)
    activation_by_route = _by_route(detector_wet_activation_rows or [])
    formula_by_route = _by_route(route_formula_dry_run_rows or [])
    policy_blockers_by_route = _blockers_by_route(policy_blocker_rows)

    route_ids = sorted(
        set(qch_by_route)
        | set(policy_by_route)
        | set(assembly_by_route)
        | set(activation_by_route)
        | set(formula_by_route)
    )
    board_rows: list[SidewallRouteYieldDetectionReadinessBoardRow] = []
    blocker_rows: list[SidewallRouteYieldDetectionReadinessBlockerRow] = []
    for route_id in route_ids:
        qch = qch_by_route.get(route_id, {})
        policy = policy_by_route.get(route_id, {})
        assembly = assembly_by_route.get(route_id, {})
        transfer = transfer_by_route.get(route_id, {})
        wet = wet_by_route.get(route_id, {})
        activation = activation_by_route.get(route_id, {})
        formula = formula_by_route.get(route_id, {})
        blockers = policy_blockers_by_route.get(route_id, {})

        detector_ready = _detector_transfer_ready(transfer, activation)
        wet_ready = _wet_observation_ready(wet, activation)
        formula_ready = _route_formula_ready(formula)
        ready_lanes = {
            "formal_qch": _formal_qch_ready(qch),
            "pressure_flow": _pressure_flow_ready(policy, qch),
            "selected_annulus": _selected_annulus_ready(policy, assembly),
        }
        missing_lanes = {
            "detector_blank_transfer": not detector_ready,
            "wet_observation": not wet_ready,
            "route_formula_component": not formula_ready,
        }
        blocker_rows.extend(
            _blocker_rows_for_route(
                route_id=route_id,
                ready_lanes=ready_lanes,
                missing_lanes=missing_lanes,
                policy_blockers=blockers,
                qch=qch,
                policy=policy,
                assembly=assembly,
                transfer=transfer,
                wet=wet,
                activation=activation,
                formula=formula,
            )
        )
        ready_count = sum(ready_lanes.values())
        missing_count = sum(missing_lanes.values())
        total_lanes = len(ready_lanes) + len(missing_lanes)
        board_status = _board_status(
            detector_ready=detector_ready,
            wet_ready=wet_ready,
            formula_ready=formula_ready,
        )
        board_rows.append(
            SidewallRouteYieldDetectionReadinessBoardRow(
                board_row_id=f"RYD-READINESS-{route_id}",
                board_version=SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_VERSION,
                route_candidate_id=route_id,
                route_key=str(
                    assembly.get("route_key")
                    or policy.get("route_key")
                    or qch.get("route_key", "")
                ),
                route_geometry_family=str(
                    assembly.get("route_geometry_family")
                    or qch.get("route_geometry_family", "")
                ),
                source_case_id=str(
                    assembly.get("source_case_id")
                    or policy.get("source_case_id")
                    or qch.get("case_id", "")
                ),
                qch_sidecar_id=str(
                    assembly.get("qch_sidecar_id")
                    or policy.get("qch_sidecar_id")
                    or qch.get("qch_sidecar_id", "")
                ),
                formal_qch_sidecar_id=str(qch.get("formal_qch_sidecar_id", "")),
                q_ch_m3_s=_float_value(qch.get("q_ch_m3_s")),
                formal_flow_split_fraction=_float_value(
                    qch.get("formal_flow_split_fraction")
                ),
                qch_route_input_status=_ready_status(ready_lanes["formal_qch"]),
                pressure_flow_route_input_status=_ready_status(
                    ready_lanes["pressure_flow"]
                ),
                selected_annulus_context_status=_ready_status(
                    ready_lanes["selected_annulus"]
                ),
                detector_blank_transfer_status=_missing_status(
                    missing_lanes["detector_blank_transfer"]
                ),
                wet_observation_status=_missing_status(missing_lanes["wet_observation"]),
                route_formula_component_status=_missing_status(
                    missing_lanes["route_formula_component"]
                ),
                detector_wet_activation_status=str(
                    activation.get("route_formula_blocker_status", "")
                ),
                route_formula_dry_run_status=str(
                    formula.get("route_formula_review_dry_run_status", "")
                ),
                route_formula_component_vector_ready=formula_ready,
                ready_route_input_count=ready_count,
                missing_claim_evidence_count=missing_count,
                readiness_fraction=round(ready_count / total_lanes, 6),
                primary_next_execution_block=str(
                    _primary_next_execution_block(
                        detector_ready=detector_ready,
                        wet_ready=wet_ready,
                        formula_ready=formula_ready,
                        assembly=assembly,
                        policy=policy,
                    )
                ),
                secondary_next_execution_block=_secondary_next_execution_block(
                    detector_ready=detector_ready,
                    wet_ready=wet_ready,
                    formula_ready=formula_ready,
                ),
                board_status=board_status,
                route_score_current=False,
                winner_current=False,
                yield_current=False,
                detection_probability_current=False,
                wet_pass_probability_current=False,
                production_ingestion_current=False,
                hard_fail_if=(
                    "route_score_or_yield_or_detection_probability_true_before_"
                    "detector_blank_transfer_and_wet_evidence_are_accepted"
                ),
                next_required_evidence=_next_required_evidence(
                    policy=policy,
                    assembly=assembly,
                    transfer=transfer,
                    wet=wet,
                    blockers=blockers,
                ),
                claim_boundary=(
                    SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_CLAIM_BOUNDARY
                ),
            )
        )
    return board_rows, blocker_rows


def _by_route(rows: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(row.get("route_candidate_id", "")): row for row in rows}


def _blockers_by_route(
    rows: list[Mapping[str, Any]],
) -> dict[str, dict[str, Mapping[str, Any]]]:
    output: dict[str, dict[str, Mapping[str, Any]]] = {}
    for row in rows:
        route_id = str(row.get("route_candidate_id", ""))
        lane = str(row.get("evidence_lane", ""))
        if route_id and lane:
            output.setdefault(route_id, {})[lane] = row
    return output


def _formal_qch_ready(row: Mapping[str, Any]) -> bool:
    return (
        _bool_value(row.get("formal_qch_sidecar_current"))
        and not _bool_value(row.get("formal_qch_weighting_current"))
        and not _bool_value(row.get("q_ch_weighting_current"))
        and str(row.get("per_route_acceptance_status", ""))
        == "accepted_exact_pressure_flow_for_formal_qch_sidecar"
        and _float_value(row.get("q_ch_m3_s")) > 0.0
    )


def _pressure_flow_ready(
    policy: Mapping[str, Any],
    qch: Mapping[str, Any],
) -> bool:
    return (
        str(policy.get("pressure_flow_policy_status", ""))
        == "ready_exact_pressure_flow_validation_for_formal_qch_input"
        and str(qch.get("quality_gate", "")) == "pass"
        and str(qch.get("source_match_status", "")) == "exact_request_and_geometry_match"
    )


def _selected_annulus_ready(
    policy: Mapping[str, Any],
    assembly: Mapping[str, Any],
) -> bool:
    policy_status = str(policy.get("selected_annulus_policy_status", ""))
    assembly_status = str(assembly.get("selected_annulus_detection_context_status", ""))
    return policy_status in {
        "ready_selected_annulus_event_panel_input_not_probability",
        "not_ready_selected_annulus_small_n_not_probability",
    } and assembly_status in {
        "expanded_selected_annulus_panel_available_not_probability",
        "selected_annulus_context_available_small_n_not_probability",
    }


def _detector_transfer_ready(
    transfer: Mapping[str, Any],
    activation: Mapping[str, Any],
) -> bool:
    if activation:
        return _bool_value(activation.get("detector_branch_ready_for_formula"))
    return _int_value(transfer.get("accepted_transfer_count")) > 0


def _wet_observation_ready(
    wet: Mapping[str, Any],
    activation: Mapping[str, Any],
) -> bool:
    if activation:
        return _bool_value(activation.get("wet_branch_ready_for_formula"))
    return _int_value(wet.get("accepted_endpoint_count")) >= 7


def _route_formula_ready(row: Mapping[str, Any]) -> bool:
    return _bool_value(row.get("route_formula_ready_for_claim_review")) and str(
        row.get("route_formula_review_dry_run_status", "")
    ) == "route_formula_component_vector_ready_for_policy_review_not_scored"


def _board_status(
    *,
    detector_ready: bool,
    wet_ready: bool,
    formula_ready: bool,
) -> str:
    if detector_ready and wet_ready and formula_ready:
        return READINESS_BOARD_FORMULA_POLICY_REVIEW_STATUS
    return READINESS_BOARD_STATUS


def _primary_next_execution_block(
    *,
    detector_ready: bool,
    wet_ready: bool,
    formula_ready: bool,
    assembly: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> str:
    if detector_ready and wet_ready and formula_ready:
        return "route_formula_policy_review"
    if not detector_ready:
        return str(
            assembly.get("next_executable_branch")
            or policy.get(
                "primary_next_execution_block",
                "sidewall_detector_blank_transfer_validation",
            )
        )
    if not wet_ready:
        return "wet_observation_bundle_intake"
    return "route_formula_review_dry_run"


def _secondary_next_execution_block(
    *,
    detector_ready: bool,
    wet_ready: bool,
    formula_ready: bool,
) -> str:
    if not detector_ready and not wet_ready:
        return "wet_observation_bundle_intake"
    if detector_ready and not wet_ready:
        return "route_formula_review_dry_run"
    if detector_ready and wet_ready and not formula_ready:
        return "route_formula_policy_review_after_component_vector"
    return "route_claim_policy_review"


def _ready_status(ok: bool) -> str:
    return READY_ROUTE_INPUT if ok else MISSING_CLAIM_EVIDENCE


def _missing_status(missing: bool) -> str:
    return MISSING_CLAIM_EVIDENCE if missing else READY_ROUTE_INPUT


def _blocker_rows_for_route(
    *,
    route_id: str,
    ready_lanes: dict[str, bool],
    missing_lanes: dict[str, bool],
    policy_blockers: dict[str, Mapping[str, Any]],
    qch: Mapping[str, Any],
    policy: Mapping[str, Any],
    assembly: Mapping[str, Any],
    transfer: Mapping[str, Any],
    wet: Mapping[str, Any],
    activation: Mapping[str, Any],
    formula: Mapping[str, Any],
) -> list[SidewallRouteYieldDetectionReadinessBlockerRow]:
    specs = [
        (
            "formal_qch",
            ready_lanes["formal_qch"],
            str(qch.get("bridge_status", "")),
            "route_input",
            "formal q_ch sidecar receipt with no q_ch weighting",
            "formal_qch_sidecar_missing_or_weighting_claimed",
        ),
        (
            "pressure_flow_validation",
            ready_lanes["pressure_flow"],
            str(policy.get("pressure_flow_policy_status", "")),
            "route_input",
            "exact pressure-flow validation bound to route geometry",
            "pressure_flow_validation_missing_or_geometry_mismatch",
        ),
        (
            "selected_annulus_detection_context",
            ready_lanes["selected_annulus"],
            str(assembly.get("selected_annulus_detection_context_status", "")),
            "detection_context",
            "selected-annulus event panel input, not probability",
            "selected_annulus_context_promoted_to_detection_probability",
        ),
        (
            "detector_blank_transfer",
            not missing_lanes["detector_blank_transfer"],
            str(
                activation.get("detector_transfer_matrix_status")
                or transfer.get("route_transfer_matrix_status", "")
            ),
            "detection_probability",
            _text_from_blocker(
                policy_blockers,
                "detector_response_bridge",
                "sidewall-specific detector/blank transfer evidence",
            ),
            "detection_probability_true_without_detector_blank_transfer",
        ),
        (
            "wet_observation",
            not missing_lanes["wet_observation"],
            str(
                activation.get("wet_observation_matrix_status")
                or wet.get("route_wet_observation_matrix_status", "")
            ),
            "yield;wet_pass_probability",
            _text_from_blocker(
                policy_blockers,
                "wet_wall_interaction",
                "accepted wet/surface endpoint bundle",
            ),
            "yield_or_wet_pass_true_without_wet_observation_bundle",
        ),
        (
            "route_formula_component",
            not missing_lanes["route_formula_component"],
            str(formula.get("route_formula_review_dry_run_status", "")),
            "route_score;winner;yield;detection_probability",
            "route formula component vector ready for policy review",
            "route_score_or_winner_true_without_formula_component_policy_review",
        ),
    ]
    rows: list[SidewallRouteYieldDetectionReadinessBlockerRow] = []
    for lane, ready, current_status, target_claim, next_required, hard_fail in specs:
        rows.append(
            SidewallRouteYieldDetectionReadinessBlockerRow(
                blocker_row_id=f"RYD-READINESS-BLOCKER-{route_id}-{lane}",
                board_version=SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_VERSION,
                route_candidate_id=route_id,
                evidence_lane=lane,
                readiness_class=READY_ROUTE_INPUT if ready else MISSING_CLAIM_EVIDENCE,
                current_status=current_status,
                target_claim=target_claim,
                target_claim_current=False,
                next_required_evidence=next_required,
                hard_fail_if_promoted_without=hard_fail,
                claim_boundary=(
                    SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_CLAIM_BOUNDARY
                ),
            )
        )
    return rows


def _text_from_blocker(
    blockers: dict[str, Mapping[str, Any]],
    lane: str,
    default: str,
) -> str:
    text = str(blockers.get(lane, {}).get("next_required_evidence", "")).strip()
    return text or default


def _next_required_evidence(
    *,
    policy: Mapping[str, Any],
    assembly: Mapping[str, Any],
    transfer: Mapping[str, Any],
    wet: Mapping[str, Any],
    blockers: dict[str, Mapping[str, Any]],
) -> str:
    items = [
        str(policy.get("next_required_evidence", "")).strip(),
        str(assembly.get("next_required_evidence", "")).strip(),
        str(transfer.get("route_transfer_matrix_status", "")).strip(),
        str(wet.get("route_wet_observation_matrix_status", "")).strip(),
        _text_from_blocker(blockers, "detector_response_bridge", ""),
        _text_from_blocker(blockers, "blank_false_positive_trace", ""),
        _text_from_blocker(blockers, "wet_wall_interaction", ""),
    ]
    return " | ".join(_dedupe_nonempty(items))


def _dedupe_nonempty(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        for part in (piece.strip() for piece in item.split("|")):
            if part and part not in output:
                output.append(part)
    return output


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _int_value(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}
