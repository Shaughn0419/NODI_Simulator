"""Route formula closure after q_ch and detector/wet activation inputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_VERSION = (
    "sidewall_route_formula_activation_closure_v1"
)
SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_CLAIM_BOUNDARY = (
    "route_formula_activation_closure_not_route_score_not_winner_not_yield_not_detection"
)
SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_STATUS = (
    "route_formula_activation_closure_simulation_candidate_input_joiner"
)


@dataclass(frozen=True)
class SidewallRouteFormulaActivationClosureRow:
    closure_row_id: str
    closure_version: str
    route_candidate_id: str
    route_geometry_family: str
    qch_sidecar_id: str
    qch_status: str
    q_ch_m3_s: float
    formal_flow_split_fraction: float
    detector_wet_activation_status: str
    detector_branch_ready: bool
    wet_branch_ready: bool
    route_formula_ready_for_claim_review: bool
    route_formula_ready_for_simulation_candidate_review: bool
    route_formula_activation_status: str
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


def build_route_formula_activation_closure(
    *,
    qch_detector_wet_binder_rows: list[Mapping[str, Any]],
    detector_wet_activation_rows: list[Mapping[str, Any]],
) -> list[SidewallRouteFormulaActivationClosureRow]:
    activation_by_route = {
        str(row.get("route_candidate_id", "")): row
        for row in detector_wet_activation_rows
    }
    rows: list[SidewallRouteFormulaActivationClosureRow] = []
    for binder in sorted(
        qch_detector_wet_binder_rows,
        key=lambda row: str(row.get("route_candidate_id", "")),
    ):
        route_id = str(binder.get("route_candidate_id", ""))
        activation = activation_by_route.get(route_id, {})
        detector_ready = _bool(activation.get("detector_branch_ready_for_formula"))
        wet_ready = _bool(activation.get("wet_branch_ready_for_formula"))
        qch_ready = str(binder.get("qch_status", "")) == (
            "formal_qch_input_ready_not_route_score"
        )
        formula_ready = qch_ready and detector_ready and wet_ready
        rows.append(
            SidewallRouteFormulaActivationClosureRow(
                closure_row_id=f"ROUTE-FORMULA-ACTIVATION-CLOSURE-{route_id}",
                closure_version=SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_VERSION,
                route_candidate_id=route_id,
                route_geometry_family=str(binder.get("route_geometry_family", "")),
                qch_sidecar_id=str(binder.get("qch_sidecar_id", "")),
                qch_status=str(binder.get("qch_status", "")),
                q_ch_m3_s=_float(binder.get("q_ch_m3_s")),
                formal_flow_split_fraction=_float(
                    binder.get("formal_flow_split_fraction")
                ),
                detector_wet_activation_status=str(
                    activation.get(
                        "route_formula_blocker_status",
                        "detector_wet_activation_missing",
                    )
                ),
                detector_branch_ready=detector_ready,
                wet_branch_ready=wet_ready,
                route_formula_ready_for_claim_review=formula_ready,
                route_formula_ready_for_simulation_candidate_review=formula_ready,
                route_formula_activation_status=(
                    "route_formula_inputs_ready_for_simulation_candidate_review_not_auto_scored"
                    if formula_ready
                    else "blocked_detector_wet_activation_required"
                ),
                route_score_current=False,
                winner_current=False,
                JRC_current=False,
                yield_current=False,
                detection_probability_current=False,
                wet_pass_probability_current=False,
                production_ingestion_current=False,
                next_required_evidence=(
                    "accepted detector/wet activation rows, then route score policy review"
                ),
                hard_fail_if=(
                    "route_formula_activation_closure_emits_score_winner_yield_detection_or_production"
                ),
                claim_boundary=SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_CLAIM_BOUNDARY,
            )
        )
    return rows


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _float(value: Any) -> float:
    if value is None or str(value).strip() == "":
        return 0.0
    return float(str(value))
