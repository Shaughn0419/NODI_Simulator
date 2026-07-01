"""Pressure-flow comparison helpers for candidate q_ch sidecars."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping


PRESSURE_FLOW_VALIDATION_VERSION = "pressure_flow_validation_candidate_v1"
PRESSURE_FLOW_CONTEXT_CLAIM_BOUNDARY = (
    "pressure_flow_context_not_formal_qch_not_route_not_yield_not_detection"
)


@dataclass(frozen=True)
class PressureFlowComparisonRow:
    comparison_id: str
    validation_version: str
    qch_sidecar_id: str
    qch_source_case_id: str
    comsol_context_id: str
    source_match_level: str
    pressure_drop_Pa: float
    candidate_q_at_context_pressure_m3_s: float
    comsol_reference_flow_m3_s: float
    flow_ratio_candidate_to_comsol: float
    comsol_quality_gate: str
    validation_status: str
    formal_qch_sidecar_current: bool
    route_score_current: bool
    winner_current: bool
    yield_detection_probability_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_pressure_flow_comparison_rows(
    qch_rows: list[Mapping[str, Any]],
    comsol_context_rows: list[Mapping[str, Any]],
) -> list[PressureFlowComparisonRow]:
    """Compare q_ch candidate rows against COMSOL/pressure-flow context rows."""
    comparisons: list[PressureFlowComparisonRow] = []
    open_qch_rows = [
        row for row in qch_rows if str(row.get("qch_sidecar_status")) == "candidate_qch_sidecar_row"
    ]
    for index, qch_row in enumerate(open_qch_rows, start=1):
        context = _best_context_for_row(qch_row, comsol_context_rows)
        context_pressure = _float_value(context.get("pressure_drop_Pa"))
        reference_flow = _float_value(context.get("comsol_reference_flow_m3_s"))
        candidate_q_base = _float_value(qch_row.get("q_ch_candidate_m3_s"))
        candidate_pressure = _float_value(qch_row.get("pressure_drop_Pa"))
        candidate_at_context = (
            candidate_q_base * context_pressure / candidate_pressure
            if candidate_q_base > 0.0 and candidate_pressure > 0.0 and context_pressure > 0.0
            else 0.0
        )
        ratio = (
            candidate_at_context / reference_flow
            if reference_flow > 0.0 and math.isfinite(reference_flow)
            else math.inf
        )
        match_level = str(context.get("source_match_level", "no_context_available"))
        quality_gate = str(context.get("quality_gate", "missing"))
        status = (
            "formal_validation_candidate"
            if match_level == "exact_geometry_and_route"
            and quality_gate == "pass"
            and 0.5 <= ratio <= 2.0
            else "context_only_not_formal_validation"
        )
        comparisons.append(
            PressureFlowComparisonRow(
                comparison_id=f"PF-COMP-{index:03d}",
                validation_version=PRESSURE_FLOW_VALIDATION_VERSION,
                qch_sidecar_id=str(qch_row.get("qch_sidecar_id", "")),
                qch_source_case_id=str(qch_row.get("source_case_id", "")),
                comsol_context_id=str(context.get("comsol_context_id", "")),
                source_match_level=match_level,
                pressure_drop_Pa=context_pressure,
                candidate_q_at_context_pressure_m3_s=float(candidate_at_context),
                comsol_reference_flow_m3_s=reference_flow,
                flow_ratio_candidate_to_comsol=float(ratio),
                comsol_quality_gate=quality_gate,
                validation_status=status,
                formal_qch_sidecar_current=False,
                route_score_current=False,
                winner_current=False,
                yield_detection_probability_current=False,
                claim_boundary=PRESSURE_FLOW_CONTEXT_CLAIM_BOUNDARY,
            )
        )
    return comparisons


def context_row_from_comsol_summary(
    row: Mapping[str, Any],
    *,
    comsol_context_id: str,
    source_match_level: str,
    sidewall_deg_comsol: float,
    depth_nm: float,
    top_width_nm: float | None,
    route_family: str,
) -> dict[str, Any]:
    """Normalize one COMSOL pressure-flow summary row for comparison."""
    pressure_drop = abs(_float_value(row.get("p_top_left_pa")) - _float_value(row.get("p_out_pa")))
    upper = _float_value(row.get("q_upper_ports_m3_s"))
    lower = _float_value(row.get("q_lower_ports_m3_s"))
    reference_flow = abs(upper) + abs(lower)
    return {
        "comsol_context_id": comsol_context_id,
        "source_match_level": source_match_level,
        "sidewall_deg_comsol": float(sidewall_deg_comsol),
        "depth_nm": float(depth_nm),
        "top_width_nm": "" if top_width_nm is None else float(top_width_nm),
        "route_family": route_family,
        "pressure_drop_Pa": pressure_drop,
        "comsol_reference_flow_m3_s": reference_flow,
        "q_upper_ports_m3_s": upper,
        "q_lower_ports_m3_s": lower,
        "port_balance_rel": _float_value(row.get("port_balance_rel")),
        "quality_gate": str(row.get("quality_gate", "missing")),
    }


def _best_context_for_row(
    qch_row: Mapping[str, Any],
    comsol_context_rows: list[Mapping[str, Any]],
) -> Mapping[str, Any]:
    if not comsol_context_rows:
        return {}
    source_case = str(qch_row.get("source_case_id", ""))
    if "taper_theta85" in source_case:
        for row in comsol_context_rows:
            if str(row.get("sidewall_deg_comsol")) in {"85", "85.0"}:
                return row
    return comsol_context_rows[0]


def _float_value(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return math.inf
    return numeric
