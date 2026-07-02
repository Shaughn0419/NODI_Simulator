"""Review-only route formula component dry run for sidewall candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_VERSION = (
    "sidewall_route_formula_review_dry_run_v1"
)
SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_CLAIM_BOUNDARY = (
    "route_formula_review_dry_run_components_not_route_score_not_winner"
)


@dataclass(frozen=True)
class SidewallRouteFormulaReviewDryRunRow:
    dry_run_row_id: str
    dry_run_version: str
    route_candidate_id: str
    route_geometry_family: str
    qch_sidecar_id: str
    q_ch_m3_s: float
    formal_flow_split_fraction: float
    qch_component_ready: bool
    detector_component_ready: bool
    wet_component_ready: bool
    route_formula_ready_for_claim_review: bool
    diagnostic_qch_component_value: float
    diagnostic_flow_split_component_value: float
    diagnostic_detector_gate_component_value: float
    diagnostic_wet_gate_component_value: float
    diagnostic_component_ready_count: int
    diagnostic_component_required_count: int
    diagnostic_component_completeness_fraction: float
    route_formula_review_dry_run_status: str
    route_score_current: bool
    route_score_value_current: str
    winner_current: bool
    JRC_current: bool
    yield_current: bool
    detection_probability_current: bool
    wet_pass_probability_current: bool
    production_ingestion_current: bool
    next_required_action: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_route_formula_review_dry_run(
    *,
    closure_rows: list[Mapping[str, Any]],
) -> list[SidewallRouteFormulaReviewDryRunRow]:
    rows: list[SidewallRouteFormulaReviewDryRunRow] = []
    for row in sorted(closure_rows, key=lambda item: str(item.get("route_candidate_id", ""))):
        qch_ready = str(row.get("qch_status", "")) == (
            "formal_qch_input_ready_not_route_score"
        )
        detector_ready = _bool(row.get("detector_branch_ready"))
        wet_ready = _bool(row.get("wet_branch_ready"))
        formula_ready = _bool(row.get("route_formula_ready_for_claim_review"))
        ready_count = sum([qch_ready, detector_ready, wet_ready])
        required_count = 3
        blocked_status, next_action = _blocked_status_and_next_action(
            formula_ready=formula_ready,
            detector_ready=detector_ready,
            wet_ready=wet_ready,
        )
        rows.append(
            SidewallRouteFormulaReviewDryRunRow(
                dry_run_row_id=f"ROUTE-FORMULA-DRY-RUN-{row.get('route_candidate_id', '')}",
                dry_run_version=SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_VERSION,
                route_candidate_id=str(row.get("route_candidate_id", "")),
                route_geometry_family=str(row.get("route_geometry_family", "")),
                qch_sidecar_id=str(row.get("qch_sidecar_id", "")),
                q_ch_m3_s=_float(row.get("q_ch_m3_s")),
                formal_flow_split_fraction=_float(
                    row.get("formal_flow_split_fraction")
                ),
                qch_component_ready=qch_ready,
                detector_component_ready=detector_ready,
                wet_component_ready=wet_ready,
                route_formula_ready_for_claim_review=formula_ready,
                diagnostic_qch_component_value=(
                    _float(row.get("q_ch_m3_s")) if qch_ready else 0.0
                ),
                diagnostic_flow_split_component_value=(
                    _float(row.get("formal_flow_split_fraction")) if qch_ready else 0.0
                ),
                diagnostic_detector_gate_component_value=1.0 if detector_ready else 0.0,
                diagnostic_wet_gate_component_value=1.0 if wet_ready else 0.0,
                diagnostic_component_ready_count=ready_count,
                diagnostic_component_required_count=required_count,
                diagnostic_component_completeness_fraction=round(
                    ready_count / required_count, 6
                ),
                route_formula_review_dry_run_status=(
                    "route_formula_component_vector_ready_for_policy_review_not_scored"
                    if formula_ready
                    else blocked_status
                ),
                route_score_current=False,
                route_score_value_current="",
                winner_current=False,
                JRC_current=False,
                yield_current=False,
                detection_probability_current=False,
                wet_pass_probability_current=False,
                production_ingestion_current=False,
                next_required_action=next_action,
                hard_fail_if=(
                    "dry_run_emits_route_score_winner_yield_detection_or_production"
                ),
                claim_boundary=SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_CLAIM_BOUNDARY,
            )
        )
    return rows


def _blocked_status_and_next_action(
    *,
    formula_ready: bool,
    detector_ready: bool,
    wet_ready: bool,
) -> tuple[str, str]:
    if formula_ready:
        return (
            "route_formula_component_vector_ready_for_policy_review_not_scored",
            "run route formula policy review using component vector; scoring remains separate",
        )
    if detector_ready and not wet_ready:
        return (
            "blocked_until_wet_evidence_accepted",
            "complete accepted wet evidence inputs, rerun activation closure",
        )
    if wet_ready and not detector_ready:
        return (
            "blocked_until_detector_evidence_accepted",
            "complete accepted detector evidence inputs, rerun activation closure",
        )
    return (
        "blocked_until_detector_wet_evidence_accepted",
        "complete accepted detector and wet evidence inputs, rerun activation closure",
    )


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _float(value: Any) -> float:
    if value is None or str(value).strip() == "":
        return 0.0
    return float(str(value))
