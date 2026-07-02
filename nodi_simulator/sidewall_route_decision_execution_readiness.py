"""Route/yield/detection execution readiness after solver and evidence packets."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_VERSION = (
    "sidewall_route_decision_execution_readiness_v2"
)
SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_CLAIM_BOUNDARY = (
    "route_decision_execution_readiness_not_route_score_not_yield_not_detection"
)
ROUTE_DECISION_EXECUTION_READINESS_STATUS = (
    "route_decision_execution_readiness_ready_branch_statuses_not_claim_ready"
)


@dataclass(frozen=True)
class SidewallRouteDecisionExecutionReadinessRow:
    readiness_row_id: str
    readiness_version: str
    route_candidate_id: str
    route_key: str
    route_geometry_family: str
    source_case_id: str
    q_ch_m3_s: float
    qch_route_input_status: str
    solver_branch_packet_status: str
    electrokinetic_preflight_status: str
    comsol_launch_precondition_status: str
    detector_blank_transfer_execution_status: str
    wet_observation_execution_status: str
    route_formula_dry_run_status: str
    route_formula_component_vector_ready: bool
    route_formula_policy_review_status: str
    route_score_candidate_ready: bool
    winner_jrc_policy_review_status: str
    winner_jrc_candidate_ready: bool
    yield_detection_claim_value_review_status: str
    yield_detection_values_ready: bool
    detector_accepted_transfer_rows: int
    wet_accepted_observation_rows: int
    rectangle_baseline_preserved: bool
    sidewall_trapezoid_route_present: bool
    ready_input_count: int
    missing_claim_evidence_count: int
    execution_readiness_status: str
    route_score_current: bool
    winner_current: bool
    JRC_current: bool
    yield_current: bool
    detection_probability_current: bool
    wet_pass_probability_current: bool
    production_ingestion_current: bool
    next_required_evidence: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallRouteDecisionClaimGuardRow:
    guard_row_id: str
    readiness_version: str
    promotion_target: str
    implementation_authorized: bool
    branch_packets_available: bool
    claim_promoted_current: bool
    claim_promotion_allowed_now: bool
    required_evidence_before_true: str
    hard_fail_if_missing_evidence: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_route_decision_execution_readiness(
    *,
    readiness_board_rows: list[Mapping[str, Any]],
    solver_packet_status: Mapping[str, Any],
    electrokinetic_status: Mapping[str, Any],
    comsol_precondition_status: Mapping[str, Any],
    detector_blank_status: Mapping[str, Any],
    wet_observation_status: Mapping[str, Any],
    route_formula_dry_run_status: Mapping[str, Any] | None = None,
    route_formula_dry_run_rows: list[Mapping[str, Any]] | None = None,
    route_formula_policy_status: Mapping[str, Any] | None = None,
    route_formula_policy_rows: list[Mapping[str, Any]] | None = None,
    winner_jrc_policy_status: Mapping[str, Any] | None = None,
    winner_jrc_policy_rows: list[Mapping[str, Any]] | None = None,
    yield_detection_claim_value_status: Mapping[str, Any] | None = None,
    yield_detection_claim_value_rows: list[Mapping[str, Any]] | None = None,
) -> tuple[list[SidewallRouteDecisionExecutionReadinessRow], list[SidewallRouteDecisionClaimGuardRow]]:
    families = {str(row.get("route_geometry_family", "")) for row in readiness_board_rows}
    rectangle_present = "ideal_rectangle" in families
    trapezoid_present = "trapezoid_tapered_sidewalls" in families
    detector_accepted = _accepted_detector_count(detector_blank_status)
    wet_accepted = _accepted_wet_count(wet_observation_status)
    dry_status = route_formula_dry_run_status or {}
    dry_by_route = {
        str(row.get("route_candidate_id", "")): row
        for row in (route_formula_dry_run_rows or [])
    }
    formula_policy = route_formula_policy_status or {}
    formula_policy_by_route = {
        str(row.get("route_candidate_id", "")): row
        for row in (route_formula_policy_rows or [])
    }
    winner_policy = winner_jrc_policy_status or {}
    winner_policy_by_route = {
        str(row.get("route_candidate_id", "")): row
        for row in (winner_jrc_policy_rows or [])
    }
    claim_value_status = yield_detection_claim_value_status or {}
    claim_value_by_route = {
        str(row.get("route_candidate_id", "")): row
        for row in (yield_detection_claim_value_rows or [])
    }
    route_ids = [
        str(row.get("route_candidate_id", "")) for row in readiness_board_rows
    ]
    overall_route_score_ready = bool(route_ids) and all(
        _route_score_candidate_ready(formula_policy_by_route.get(route_id, {}))
        for route_id in route_ids
    )
    overall_winner_ready = overall_route_score_ready and sum(
        _winner_jrc_ready(winner_policy_by_route.get(route_id, {}))
        for route_id in route_ids
    ) == 1
    overall_yield_detection_ready = bool(route_ids) and all(
        _yield_detection_values_ready(claim_value_by_route.get(route_id, {}))
        for route_id in route_ids
    )
    rows = [
        SidewallRouteDecisionExecutionReadinessRow(
            readiness_row_id=f"ROUTE-DECISION-EXEC-{row.get('route_candidate_id', '')}",
            readiness_version=SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_VERSION,
            route_candidate_id=str(row.get("route_candidate_id", "")),
            route_key=str(row.get("route_key", "")),
            route_geometry_family=str(row.get("route_geometry_family", "")),
            source_case_id=str(row.get("source_case_id", "")),
            q_ch_m3_s=float(row.get("q_ch_m3_s", 0.0)),
            qch_route_input_status=str(row.get("qch_route_input_status", "")),
            solver_branch_packet_status=str(solver_packet_status.get("disposition", "")),
            electrokinetic_preflight_status=str(electrokinetic_status.get("disposition", "")),
            comsol_launch_precondition_status=str(comsol_precondition_status.get("disposition", "")),
            detector_blank_transfer_execution_status=str(detector_blank_status.get("disposition", "")),
            wet_observation_execution_status=str(wet_observation_status.get("disposition", "")),
            route_formula_dry_run_status=str(dry_status.get("disposition", "")),
            route_formula_component_vector_ready=_component_vector_ready(
                dry_by_route.get(str(row.get("route_candidate_id", "")), {})
            ),
            route_formula_policy_review_status=str(
                formula_policy.get("disposition", "")
            ),
            route_score_candidate_ready=_route_score_candidate_ready(
                formula_policy_by_route.get(str(row.get("route_candidate_id", "")), {})
            ),
            winner_jrc_policy_review_status=str(winner_policy.get("disposition", "")),
            winner_jrc_candidate_ready=overall_winner_ready,
            yield_detection_claim_value_review_status=str(
                claim_value_status.get("disposition", "")
            ),
            yield_detection_values_ready=overall_yield_detection_ready,
            detector_accepted_transfer_rows=detector_accepted,
            wet_accepted_observation_rows=wet_accepted,
            rectangle_baseline_preserved=rectangle_present,
            sidewall_trapezoid_route_present=trapezoid_present,
            ready_input_count=_int(row.get("ready_route_input_count")),
            missing_claim_evidence_count=_int(row.get("missing_claim_evidence_count")),
            execution_readiness_status=_execution_status(
                detector_accepted=detector_accepted,
                wet_accepted=wet_accepted,
                component_vector_ready=_component_vector_ready(
                    dry_by_route.get(str(row.get("route_candidate_id", "")), {})
                ),
                route_score_ready=_route_score_candidate_ready(
                    formula_policy_by_route.get(str(row.get("route_candidate_id", "")), {})
                ),
                winner_ready=overall_winner_ready,
                yield_detection_ready=overall_yield_detection_ready,
            ),
            route_score_current=False,
            winner_current=_bool(
                winner_policy_by_route.get(str(row.get("route_candidate_id", "")), {}).get(
                    "winner_current"
                )
            ),
            JRC_current=_bool(
                winner_policy_by_route.get(str(row.get("route_candidate_id", "")), {}).get(
                    "JRC_current"
                )
            ),
            yield_current=_bool(
                claim_value_by_route.get(str(row.get("route_candidate_id", "")), {}).get(
                    "yield_current"
                )
            ),
            detection_probability_current=_bool(
                claim_value_by_route.get(str(row.get("route_candidate_id", "")), {}).get(
                    "detection_probability_current"
                )
            ),
            wet_pass_probability_current=_bool(
                claim_value_by_route.get(str(row.get("route_candidate_id", "")), {}).get(
                    "wet_pass_probability_current"
                )
            ),
            production_ingestion_current=False,
            next_required_evidence=(
                "accepted simulation detector/blank transfer rows, accepted wet observation rows, "
                "and route formula component-vector dry run before route/yield/detection policy review"
            ),
            hard_fail_if=(
                "route_score_winner_yield_detection_or_production_true_before_detector_blank_and_wet_simulation_evidence_pass"
            ),
            claim_boundary=SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_CLAIM_BOUNDARY,
        )
        for row in readiness_board_rows
    ]
    return rows, _claim_guard_rows(
        branch_packets_available=True,
        route_score_ready=bool(rows) and all(row.route_score_current for row in rows),
        winner_ready=sum(row.winner_current for row in rows) == 1
        and all(row.route_score_current for row in rows),
        yield_ready=bool(rows) and all(row.yield_current for row in rows),
        detection_ready=bool(rows)
        and all(row.detection_probability_current for row in rows),
    )


def _execution_status(
    *,
    detector_accepted: int,
    wet_accepted: int,
    component_vector_ready: bool,
    route_score_ready: bool,
    winner_ready: bool,
    yield_detection_ready: bool,
) -> str:
    if winner_ready and yield_detection_ready:
        return "route_yield_detection_claim_values_ready_for_integrated_review"
    if winner_ready:
        return "winner_jrc_ready_for_integrated_yield_detection_review"
    if route_score_ready:
        return "route_score_candidates_ready_for_winner_jrc_policy_review"
    if detector_accepted > 0 and wet_accepted > 0 and component_vector_ready:
        return "branch_evidence_and_formula_components_ready_for_route_policy_review"
    if detector_accepted > 0 and wet_accepted > 0:
        return "blocked_route_formula_component_vector_required"
    return "blocked_detector_blank_and_wet_observation_evidence_required"


def _claim_guard_rows(
    *,
    branch_packets_available: bool,
    route_score_ready: bool = False,
    winner_ready: bool = False,
    yield_ready: bool = False,
    detection_ready: bool = False,
) -> list[SidewallRouteDecisionClaimGuardRow]:
    specs = [
        (
            "route_score",
            route_score_ready,
            "accepted simulation detector/blank, wet observation, flow/q_ch, and route formula packet",
            "route_score_true_without_all_branch_evidence",
        ),
        (
            "winner_JRC",
            winner_ready,
            "route score packet, JRC policy, source hashes, and no unresolved blockers",
            "winner_or_JRC_true_without_route_decision_packet",
        ),
        (
            "yield",
            yield_ready,
            "simulation wet observation evidence plus detector/blank and route policy packets",
            "yield_true_without_wet_detector_and_route_packets",
        ),
        (
            "detection_probability",
            detection_ready,
            "simulation detector/blank transfer, threshold policy, wet context, and uncertainty",
            "detection_probability_true_without_detector_blank_transfer",
        ),
        (
            "production_ingestion",
            False,
            "separate production/fabrication release ledger after route decision",
            "production_ingestion_true_from_readiness_packet",
        ),
    ]
    return [
        SidewallRouteDecisionClaimGuardRow(
            guard_row_id=f"ROUTE-DECISION-GUARD-{target}",
            readiness_version=SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_VERSION,
            promotion_target=target,
            implementation_authorized=True,
            branch_packets_available=branch_packets_available,
            claim_promoted_current=False,
            claim_promotion_allowed_now=allowed,
            required_evidence_before_true=required,
            hard_fail_if_missing_evidence=hard_fail,
            claim_boundary=SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_CLAIM_BOUNDARY,
        )
        for target, allowed, required, hard_fail in specs
    ]


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if value is None or str(value).strip() == "":
        return 0
    return int(float(str(value)))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _accepted_detector_count(status: Mapping[str, Any]) -> int:
    return max(
        _int(status.get("current_accepted_transfer_rows_total")),
        _int(status.get("detector_accepted_transfer_rows_total")),
    )


def _accepted_wet_count(status: Mapping[str, Any]) -> int:
    return max(
        _int(status.get("current_accepted_observation_rows_total")),
        _int(status.get("wet_accepted_endpoint_count_total")),
    )


def _component_vector_ready(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("route_formula_ready_for_claim_review")) and str(
        row.get("route_formula_review_dry_run_status", "")
    ) == "route_formula_component_vector_ready_for_policy_review_not_scored"


def _route_score_candidate_ready(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("simulation_route_score_candidate_current")) or (
        _bool(row.get("route_score_current"))
        and _bool(row.get("route_score_activation_allowed_now"))
    )


def _winner_jrc_ready(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("simulation_top_candidate_current")) or (
        _bool(row.get("winner_current")) and _bool(row.get("JRC_current"))
    )


def _yield_detection_values_ready(row: Mapping[str, Any]) -> bool:
    return (
        (
            _bool(row.get("yield_simulation_candidate_current"))
            and _bool(row.get("detection_probability_simulation_candidate_current"))
            and _bool(row.get("wet_pass_probability_simulation_candidate_current"))
        )
        or (
            _bool(row.get("yield_current"))
            and _bool(row.get("detection_probability_current"))
            and _bool(row.get("wet_pass_probability_current"))
        )
    )
