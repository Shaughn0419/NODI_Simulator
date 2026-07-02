"""Route formula policy review for sidewall route-score candidates.

This module is the first layer that can compute a route-score candidate value,
but it only promotes `route_score_current` when the upstream component vector is
ready and the source is real accepted evidence rather than a fixture.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_VERSION = (
    "sidewall_route_formula_policy_review_v1"
)
SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_CLAIM_BOUNDARY = (
    "route_formula_policy_review_route_score_candidate_not_winner_not_yield_not_detection"
)
SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_FORMULA_ID = (
    "weighted_flow_detector_wet_gate_route_score_v1"
)

QCH_FLOW_WEIGHT = 0.4
DETECTOR_GATE_WEIGHT = 0.3
WET_GATE_WEIGHT = 0.3
REAL_ACCEPTED_EVIDENCE_CLASS = "real_accepted_detector_wet_evidence"
FIXTURE_EVIDENCE_CLASS = "fixture_not_evidence"


@dataclass(frozen=True)
class SidewallRouteFormulaPolicyReviewRow:
    policy_row_id: str
    policy_version: str
    route_candidate_id: str
    route_geometry_family: str
    qch_sidecar_id: str
    q_ch_m3_s: float
    formal_flow_split_fraction: float
    route_formula_component_vector_ready: bool
    source_evidence_class: str
    fixture_not_evidence: bool
    formula_id: str
    qch_flow_weight: float
    detector_gate_weight: float
    wet_gate_weight: float
    qch_flow_component_value: float
    detector_gate_component_value: float
    wet_gate_component_value: float
    route_score_candidate_value: float
    route_score_activation_allowed_now: bool
    route_score_current: bool
    route_score_value_current: str
    winner_current: bool
    JRC_current: bool
    yield_current: bool
    detection_probability_current: bool
    wet_pass_probability_current: bool
    production_ingestion_current: bool
    route_formula_policy_review_status: str
    next_required_action: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallRouteFormulaPolicyReviewGuardRow:
    guard_row_id: str
    policy_version: str
    promotion_target: str
    implementation_authorized: bool
    activation_allowed_now: bool
    required_evidence_before_activation: str
    hard_fail_if_activated_early: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_route_formula_policy_review(
    *,
    route_formula_dry_run_rows: list[Mapping[str, Any]],
    source_evidence_class: str,
) -> tuple[
    list[SidewallRouteFormulaPolicyReviewRow],
    list[SidewallRouteFormulaPolicyReviewGuardRow],
]:
    rows = [
        _policy_row(row, source_evidence_class=source_evidence_class)
        for row in sorted(
            route_formula_dry_run_rows,
            key=lambda item: str(item.get("route_candidate_id", "")),
        )
    ]
    return rows, _guard_rows(rows)


def _policy_row(
    row: Mapping[str, Any],
    *,
    source_evidence_class: str,
) -> SidewallRouteFormulaPolicyReviewRow:
    fixture_not_evidence = source_evidence_class == FIXTURE_EVIDENCE_CLASS
    component_ready = _component_vector_ready(row)
    qch_component = _float(row.get("formal_flow_split_fraction"))
    detector_component = _float(row.get("diagnostic_detector_gate_component_value"))
    wet_component = _float(row.get("diagnostic_wet_gate_component_value"))
    candidate_value = (
        QCH_FLOW_WEIGHT * qch_component
        + DETECTOR_GATE_WEIGHT * detector_component
        + WET_GATE_WEIGHT * wet_component
        if component_ready
        else 0.0
    )
    activation_allowed = (
        component_ready
        and source_evidence_class == REAL_ACCEPTED_EVIDENCE_CLASS
        and not fixture_not_evidence
    )
    return SidewallRouteFormulaPolicyReviewRow(
        policy_row_id=f"ROUTE-FORMULA-POLICY-REVIEW-{row.get('route_candidate_id', '')}",
        policy_version=SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_VERSION,
        route_candidate_id=str(row.get("route_candidate_id", "")),
        route_geometry_family=str(row.get("route_geometry_family", "")),
        qch_sidecar_id=str(row.get("qch_sidecar_id", "")),
        q_ch_m3_s=_float(row.get("q_ch_m3_s")),
        formal_flow_split_fraction=qch_component,
        route_formula_component_vector_ready=component_ready,
        source_evidence_class=source_evidence_class,
        fixture_not_evidence=fixture_not_evidence,
        formula_id=SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_FORMULA_ID,
        qch_flow_weight=QCH_FLOW_WEIGHT,
        detector_gate_weight=DETECTOR_GATE_WEIGHT,
        wet_gate_weight=WET_GATE_WEIGHT,
        qch_flow_component_value=qch_component,
        detector_gate_component_value=detector_component,
        wet_gate_component_value=wet_component,
        route_score_candidate_value=round(candidate_value, 12),
        route_score_activation_allowed_now=activation_allowed,
        route_score_current=activation_allowed,
        route_score_value_current=(
            f"{candidate_value:.12g}" if activation_allowed else ""
        ),
        winner_current=False,
        JRC_current=False,
        yield_current=False,
        detection_probability_current=False,
        wet_pass_probability_current=False,
        production_ingestion_current=False,
        route_formula_policy_review_status=_review_status(
            component_ready=component_ready,
            activation_allowed=activation_allowed,
            fixture_not_evidence=fixture_not_evidence,
        ),
        next_required_action=_next_required_action(
            component_ready=component_ready,
            activation_allowed=activation_allowed,
            fixture_not_evidence=fixture_not_evidence,
        ),
        hard_fail_if=(
            "route_score_current_true_without_real_accepted_evidence_or_component_vector"
        ),
        claim_boundary=SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_CLAIM_BOUNDARY,
    )


def _component_vector_ready(row: Mapping[str, Any]) -> bool:
    return _bool(row.get("route_formula_ready_for_claim_review")) and str(
        row.get("route_formula_review_dry_run_status", "")
    ) == "route_formula_component_vector_ready_for_policy_review_not_scored"


def _review_status(
    *,
    component_ready: bool,
    activation_allowed: bool,
    fixture_not_evidence: bool,
) -> str:
    if activation_allowed:
        return "route_score_candidate_ready_for_winner_policy_review"
    if component_ready and fixture_not_evidence:
        return "fixture_route_score_candidate_path_passes_not_evidence"
    return "blocked_until_formula_component_vector_ready_from_real_evidence"


def _next_required_action(
    *,
    component_ready: bool,
    activation_allowed: bool,
    fixture_not_evidence: bool,
) -> str:
    if activation_allowed:
        return "run winner/JRC policy review with route-score candidate values"
    if component_ready and fixture_not_evidence:
        return "replace fixture rows with real accepted detector/wet input rows"
    return "complete accepted detector/wet evidence and rerun activation closure"


def _guard_rows(
    rows: list[SidewallRouteFormulaPolicyReviewRow],
) -> list[SidewallRouteFormulaPolicyReviewGuardRow]:
    all_scores_ready = bool(rows) and all(row.route_score_current for row in rows)
    specs = [
        (
            "route_score",
            all_scores_ready,
            "real accepted detector/wet evidence plus ready formula component vector",
            "route_score_true_without_real_accepted_component_vector",
        ),
        (
            "winner_JRC",
            False,
            "separate winner/JRC policy after route score candidates",
            "winner_or_JRC_true_from_formula_policy_review",
        ),
        (
            "yield",
            False,
            "separate yield model and wet validation evidence",
            "yield_true_from_route_formula_policy_review",
        ),
        (
            "detection_probability",
            False,
            "separate detector probability calibration and uncertainty model",
            "detection_probability_true_from_route_formula_policy_review",
        ),
        (
            "production_ingestion",
            False,
            "separate fabrication/production release ledger",
            "production_ingestion_true_from_route_formula_policy_review",
        ),
    ]
    return [
        SidewallRouteFormulaPolicyReviewGuardRow(
            guard_row_id=f"ROUTE-FORMULA-POLICY-GUARD-{target}",
            policy_version=SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_VERSION,
            promotion_target=target,
            implementation_authorized=True,
            activation_allowed_now=allowed,
            required_evidence_before_activation=required,
            hard_fail_if_activated_early=hard_fail,
            claim_boundary=SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_CLAIM_BOUNDARY,
        )
        for target, allowed, required, hard_fail in specs
    ]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _float(value: Any) -> float:
    if value is None or str(value).strip() == "":
        return 0.0
    return float(str(value))
