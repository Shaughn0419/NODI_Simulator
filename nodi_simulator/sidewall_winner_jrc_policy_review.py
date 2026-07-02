"""Winner/JRC policy review for sidewall route-score candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_WINNER_JRC_POLICY_REVIEW_VERSION = "sidewall_winner_jrc_policy_review_v1"
SIDEWALL_WINNER_JRC_POLICY_REVIEW_CLAIM_BOUNDARY = (
    "winner_jrc_policy_review_requires_current_route_scores_not_yield_not_detection"
)
SIMULATION_ACCEPTED_EVIDENCE_CLASS = "simulation_accepted_detector_wet_evidence"
# Backward-compatible import alias. In this simulation-only lane, this is not an
# experimental evidence class.
REAL_ACCEPTED_EVIDENCE_CLASS = SIMULATION_ACCEPTED_EVIDENCE_CLASS
FIXTURE_EVIDENCE_CLASS = "fixture_not_evidence"


@dataclass(frozen=True)
class SidewallWinnerJRCPolicyReviewRow:
    review_row_id: str
    review_version: str
    route_candidate_id: str
    route_geometry_family: str
    source_evidence_class: str
    fixture_not_evidence: bool
    route_score_current: bool
    route_score_value_current: str
    route_score_candidate_value: float
    simulation_route_score_candidate_current: bool
    simulation_route_score_value_current: str
    candidate_order_index_under_policy: int
    unique_top_route_score_available: bool
    simulation_top_candidate_current: bool
    simulation_rank_label: str
    winner_activation_allowed_now: bool
    winner_current: bool
    JRC_current: bool
    JRC_value_current: str
    yield_current: bool
    detection_probability_current: bool
    wet_pass_probability_current: bool
    production_ingestion_current: bool
    winner_jrc_policy_review_status: str
    next_required_action: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallWinnerJRCPolicyReviewGuardRow:
    guard_row_id: str
    review_version: str
    promotion_target: str
    implementation_authorized: bool
    activation_allowed_now: bool
    required_evidence_before_activation: str
    hard_fail_if_activated_early: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_winner_jrc_policy_review(
    *,
    route_formula_policy_rows: list[Mapping[str, Any]],
    source_evidence_class: str,
) -> tuple[
    list[SidewallWinnerJRCPolicyReviewRow],
    list[SidewallWinnerJRCPolicyReviewGuardRow],
]:
    fixture_not_evidence = source_evidence_class == FIXTURE_EVIDENCE_CLASS
    sorted_rows = sorted(
        route_formula_policy_rows,
        key=lambda row: (
            -_float(row.get("route_score_candidate_value")),
            str(row.get("route_candidate_id", "")),
        ),
    )
    top_value = _float(sorted_rows[0].get("route_score_candidate_value")) if sorted_rows else 0.0
    top_count = sum(
        _float(row.get("route_score_candidate_value")) == top_value
        for row in sorted_rows
    )
    all_simulation_scores_current = bool(sorted_rows) and all(
        _bool(row.get("simulation_route_score_candidate_current"))
        for row in sorted_rows
    )
    unique_top = bool(sorted_rows) and top_count == 1 and top_value > 0.0
    winner_allowed = (
        all_simulation_scores_current
        and unique_top
        and source_evidence_class == SIMULATION_ACCEPTED_EVIDENCE_CLASS
        and not fixture_not_evidence
    )
    rows = [
        _review_row(
            row,
            order_index=index,
            source_evidence_class=source_evidence_class,
            fixture_not_evidence=fixture_not_evidence,
            unique_top=unique_top,
            winner_allowed=winner_allowed,
            top_value=top_value,
        )
        for index, row in enumerate(sorted_rows, start=1)
    ]
    return rows, _guard_rows(rows)


def _review_row(
    row: Mapping[str, Any],
    *,
    order_index: int,
    source_evidence_class: str,
    fixture_not_evidence: bool,
    unique_top: bool,
    winner_allowed: bool,
    top_value: float,
) -> SidewallWinnerJRCPolicyReviewRow:
    score = _float(row.get("route_score_candidate_value"))
    is_simulation_top = winner_allowed and score == top_value
    route_id = str(row.get("route_candidate_id", ""))
    return SidewallWinnerJRCPolicyReviewRow(
        review_row_id=f"WINNER-JRC-POLICY-{route_id}",
        review_version=SIDEWALL_WINNER_JRC_POLICY_REVIEW_VERSION,
        route_candidate_id=route_id,
        route_geometry_family=str(row.get("route_geometry_family", "")),
        source_evidence_class=source_evidence_class,
        fixture_not_evidence=fixture_not_evidence,
        route_score_current=False,
        route_score_value_current="",
        route_score_candidate_value=score,
        simulation_route_score_candidate_current=_bool(
            row.get("simulation_route_score_candidate_current")
        ),
        simulation_route_score_value_current=str(
            row.get("simulation_route_score_value_current", "")
        ),
        candidate_order_index_under_policy=order_index,
        unique_top_route_score_available=unique_top,
        simulation_top_candidate_current=is_simulation_top,
        simulation_rank_label=(
            "simulation_top_candidate" if is_simulation_top else f"simulation_rank_{order_index}"
        ),
        winner_activation_allowed_now=winner_allowed,
        winner_current=False,
        JRC_current=False,
        JRC_value_current="",
        yield_current=False,
        detection_probability_current=False,
        wet_pass_probability_current=False,
        production_ingestion_current=False,
        winner_jrc_policy_review_status=_review_status(
            winner_allowed=winner_allowed,
            fixture_not_evidence=fixture_not_evidence,
            unique_top=unique_top,
            route_score_current=_bool(row.get("simulation_route_score_candidate_current")),
        ),
        next_required_action=_next_required_action(
            winner_allowed=winner_allowed,
            fixture_not_evidence=fixture_not_evidence,
            route_score_current=_bool(row.get("route_score_current")),
        ),
        hard_fail_if="winner_or_JRC_true_from_simulation_candidate_without_final_claim_authorization",
        claim_boundary=SIDEWALL_WINNER_JRC_POLICY_REVIEW_CLAIM_BOUNDARY,
    )


def _review_status(
    *,
    winner_allowed: bool,
    fixture_not_evidence: bool,
    unique_top: bool,
    route_score_current: bool,
) -> str:
    if winner_allowed:
        return "simulation_top_candidate_ready_for_integrated_candidate_review"
    if fixture_not_evidence and unique_top:
        return "fixture_winner_order_path_passes_not_evidence"
    if not route_score_current:
        return "blocked_until_route_score_candidates_current"
    return "blocked_until_unique_top_and_winner_authorization_conditions_met"


def _next_required_action(
    *,
    winner_allowed: bool,
    fixture_not_evidence: bool,
    route_score_current: bool,
) -> str:
    if winner_allowed:
        return "run integrated route/yield/detection claim review"
    if fixture_not_evidence:
        return "replace fixture score rows with simulation route-score candidate rows"
    if not route_score_current:
        return "complete accepted simulation detector/wet evidence and route-score policy review"
    return "resolve route-score tie or missing winner/JRC policy condition"


def _guard_rows(
    rows: list[SidewallWinnerJRCPolicyReviewRow],
) -> list[SidewallWinnerJRCPolicyReviewGuardRow]:
    simulation_top_ready = sum(row.simulation_top_candidate_current for row in rows) == 1
    specs = [
        (
            "winner_JRC",
            False,
            "current route scores for all candidates plus unique top route",
            "winner_or_JRC_true_without_unique_current_route_score_top",
        ),
        (
            "simulation_top_candidate",
            simulation_top_ready,
            "simulation route scores for all candidates plus unique top route",
            "simulation_top_candidate_true_without_unique_current_route_score_top",
        ),
        (
            "yield",
            False,
            "separate yield review after wet model evidence",
            "yield_true_from_winner_jrc_policy_review",
        ),
        (
            "detection_probability",
            False,
            "separate detection probability review after detector calibration evidence",
            "detection_probability_true_from_winner_jrc_policy_review",
        ),
        (
            "production_ingestion",
            False,
            "separate production release ledger",
            "production_ingestion_true_from_winner_jrc_policy_review",
        ),
    ]
    return [
        SidewallWinnerJRCPolicyReviewGuardRow(
            guard_row_id=f"WINNER-JRC-POLICY-GUARD-{target}",
            review_version=SIDEWALL_WINNER_JRC_POLICY_REVIEW_VERSION,
            promotion_target=target,
            implementation_authorized=True,
            activation_allowed_now=allowed,
            required_evidence_before_activation=required,
            hard_fail_if_activated_early=hard_fail,
            claim_boundary=SIDEWALL_WINNER_JRC_POLICY_REVIEW_CLAIM_BOUNDARY,
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
