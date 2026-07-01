"""Candidate route/yield/detection decision rows for sidewall q_ch evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


ROUTE_YIELD_DETECTION_CANDIDATE_VERSION = (
    "route_yield_detection_candidate_from_qch_context_v1"
)
ROUTE_YIELD_DETECTION_CLAIM_BOUNDARY = (
    "route_candidate_metric_not_route_score_not_winner_not_yield_not_detection"
)


@dataclass(frozen=True)
class RouteYieldDetectionCandidateRow:
    route_candidate_id: str
    candidate_version: str
    qch_sidecar_id: str
    route_key: str
    source_case_id: str
    qch_sidecar_status: str
    pressure_flow_validation_status: str
    pressure_flow_context_weight: float
    candidate_flow_split_fraction: float
    route_decision_candidate_metric: float
    candidate_sort_index_under_context: int
    wet_evidence_status: str
    optical_detection_status: str
    route_score_current: bool
    winner_current: bool
    JRC_current: bool
    yield_current: bool
    detection_probability_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_route_yield_detection_candidates(
    qch_rows: list[Mapping[str, Any]],
    pressure_flow_rows: list[Mapping[str, Any]],
) -> list[RouteYieldDetectionCandidateRow]:
    """Create candidate route decision metrics without final claims."""
    pressure_by_qch = {
        str(row.get("qch_sidecar_id", "")): row for row in pressure_flow_rows
    }
    candidates: list[RouteYieldDetectionCandidateRow] = []
    open_rows = [
        row for row in qch_rows if str(row.get("qch_sidecar_status")) == "candidate_qch_sidecar_row"
    ]
    metric_rows: list[tuple[Mapping[str, Any], str, float, float]] = []
    for row in open_rows:
        pressure = pressure_by_qch.get(str(row.get("qch_sidecar_id", "")), {})
        validation_status = str(
            pressure.get("validation_status", "pressure_flow_context_missing")
        )
        context_weight = _context_weight(validation_status)
        split = _float_value(row.get("candidate_flow_split_fraction"))
        metric_rows.append((row, validation_status, context_weight, split * context_weight))

    sorted_metrics = sorted(
        metric_rows,
        key=lambda item: (item[3], str(item[0].get("qch_sidecar_id", ""))),
        reverse=True,
    )
    sort_indices = {
        str(row.get("qch_sidecar_id", "")): index
        for index, (row, _status, _weight, _metric) in enumerate(sorted_metrics, start=1)
    }
    for row, validation_status, context_weight, metric in metric_rows:
        qch_id = str(row.get("qch_sidecar_id", ""))
        candidates.append(
            RouteYieldDetectionCandidateRow(
                route_candidate_id=f"ROUTE-CAND-{qch_id.removeprefix('QCH-CAND-')}",
                candidate_version=ROUTE_YIELD_DETECTION_CANDIDATE_VERSION,
                qch_sidecar_id=qch_id,
                route_key=str(row.get("route_key", "")),
                source_case_id=str(row.get("source_case_id", "")),
                qch_sidecar_status=str(row.get("qch_sidecar_status", "")),
                pressure_flow_validation_status=validation_status,
                pressure_flow_context_weight=context_weight,
                candidate_flow_split_fraction=_float_value(
                    row.get("candidate_flow_split_fraction")
                ),
                route_decision_candidate_metric=metric,
                candidate_sort_index_under_context=sort_indices[qch_id],
                wet_evidence_status="wet_ev_evidence_contract_missing",
                optical_detection_status="optical_detection_calibration_missing",
                route_score_current=False,
                winner_current=False,
                JRC_current=False,
                yield_current=False,
                detection_probability_current=False,
                claim_boundary=ROUTE_YIELD_DETECTION_CLAIM_BOUNDARY,
            )
        )
    return sorted(candidates, key=lambda row: row.candidate_sort_index_under_context)


def _context_weight(validation_status: str) -> float:
    if validation_status == "formal_validation_candidate":
        return 1.0
    if validation_status == "context_only_not_formal_validation":
        return 0.25
    return 0.0


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
