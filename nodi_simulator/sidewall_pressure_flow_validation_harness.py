"""Executable pressure-flow validation harness rows for W500/D900 sidewall q_ch.

The harness translates the current grid-refined q_ch candidates into exact
COMSOL/measurement validation requests. It is not a validation result: it
defines the observables, tolerances, and promotion guards needed before formal
q_ch or route/yield/detection claims can be made.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_VERSION = (
    "sidewall_pressure_flow_validation_harness_w500_d900_v1"
)
SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_CLAIM_BOUNDARY = (
    "pressure_flow_validation_harness_not_formal_qch_not_route_score"
)

ROUTE_BY_CASE_ID = {
    "rectangle_limit_theta90_D900_W500": "ROUTE-CAND-001",
    "taper_theta85_D900_W500": "ROUTE-CAND-002",
}
QCH_BY_ROUTE_ID = {
    "ROUTE-CAND-001": "QCH-CAND-001",
    "ROUTE-CAND-002": "QCH-CAND-002",
}


@dataclass(frozen=True)
class SidewallPressureFlowValidationRequestRow:
    validation_request_id: str
    harness_version: str
    route_candidate_id: str
    qch_sidecar_id: str
    case_id: str
    route_key: str
    source_geometry_hash: str
    sidewall_deg_comsol: float
    sidewall_taper_angle_deg_nodi: float
    top_width_nm: float
    depth_nm: float
    pressure_drop_Pa: float
    reference_grid_nx: int
    reference_grid_nu: int
    candidate_q_grid_m3_s: float
    candidate_flow_split_fraction: float
    candidate_hydraulic_resistance_Pa_s_m3: float
    required_validation_source: str
    required_observables: str
    required_metadata: str
    acceptance_ratio_min: float
    acceptance_ratio_max: float
    split_abs_delta_max: float
    validation_status: str
    formal_qch_weighting_current: bool
    route_score_current: bool
    winner_current: bool
    yield_current: bool
    detection_probability_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallPressureFlowValidationControlRow:
    control_id: str
    harness_version: str
    case_id: str
    sidewall_deg_comsol: float
    sidewall_taper_angle_deg_nodi: float
    top_width_nm: float
    depth_nm: float
    geometry_hash: str
    solver_status: str
    control_status: str
    required_behavior: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_pressure_flow_validation_request_rows(
    qch_grid_rows: list[Mapping[str, Any]],
    *,
    reference_grid_nx: int = 41,
) -> list[SidewallPressureFlowValidationRequestRow]:
    rows: list[SidewallPressureFlowValidationRequestRow] = []
    for row in qch_grid_rows:
        if int(_float_value(row.get("grid_nx"))) != reference_grid_nx:
            continue
        case_id = str(row.get("case_id", ""))
        route_id = ROUTE_BY_CASE_ID.get(case_id)
        if route_id is None:
            continue
        if str(row.get("solver_status", "")) != "candidate_solver_output":
            continue
        rows.append(
            SidewallPressureFlowValidationRequestRow(
                validation_request_id=f"PFV-REQUEST-{route_id}",
                harness_version=SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_VERSION,
                route_candidate_id=route_id,
                qch_sidecar_id=QCH_BY_ROUTE_ID[route_id],
                case_id=case_id,
                route_key=_route_key(case_id),
                source_geometry_hash=str(row.get("geometry_hash", "")),
                sidewall_deg_comsol=_float_value(row.get("sidewall_deg_comsol")),
                sidewall_taper_angle_deg_nodi=_float_value(
                    row.get("sidewall_taper_angle_deg_nodi")
                ),
                top_width_nm=_float_value(row.get("top_width_nm")),
                depth_nm=_float_value(row.get("depth_nm")),
                pressure_drop_Pa=_float_value(row.get("pressure_drop_Pa")),
                reference_grid_nx=reference_grid_nx,
                reference_grid_nu=int(_float_value(row.get("grid_nu"))),
                candidate_q_grid_m3_s=_float_value(row.get("q_ch_grid_candidate_m3_s")),
                candidate_flow_split_fraction=_float_value(
                    row.get("candidate_flow_split_fraction")
                ),
                candidate_hydraulic_resistance_Pa_s_m3=_float_value(
                    row.get("hydraulic_resistance_Pa_s_m3")
                ),
                required_validation_source=(
                    "exact W500/D900 sidewall COMSOL pressure-flow run or matched measurement"
                ),
                required_observables=(
                    "pressure_drop_Pa;q_total_m3_s;q_upper_ports_m3_s;"
                    "q_lower_ports_m3_s;port_balance_rel;quality_gate"
                ),
                required_metadata=(
                    "geometry_descriptor_sha256;model_or_measurement_id;"
                    "mesh_or_instrument_resolution;fluid_viscosity_Pa_s;"
                    "channel_length_m;boundary_condition_id"
                ),
                acceptance_ratio_min=0.5,
                acceptance_ratio_max=2.0,
                split_abs_delta_max=0.05,
                validation_status=(
                    "exact_w500_d900_validation_harness_ready_missing_external_result"
                ),
                formal_qch_weighting_current=False,
                route_score_current=False,
                winner_current=False,
                yield_current=False,
                detection_probability_current=False,
                claim_boundary=SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_CLAIM_BOUNDARY,
            )
        )
    return rows


def build_pressure_flow_validation_control_rows(
    qch_grid_rows: list[Mapping[str, Any]],
    *,
    reference_grid_nx: int = 41,
) -> list[SidewallPressureFlowValidationControlRow]:
    rows: list[SidewallPressureFlowValidationControlRow] = []
    for row in qch_grid_rows:
        if int(_float_value(row.get("grid_nx"))) != reference_grid_nx:
            continue
        if str(row.get("solver_status", "")) != "blocked_geometry_closed":
            continue
        rows.append(
            SidewallPressureFlowValidationControlRow(
                control_id=f"PFV-CONTROL-{row.get('case_id', '')}",
                harness_version=SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_VERSION,
                case_id=str(row.get("case_id", "")),
                sidewall_deg_comsol=_float_value(row.get("sidewall_deg_comsol")),
                sidewall_taper_angle_deg_nodi=_float_value(
                    row.get("sidewall_taper_angle_deg_nodi")
                ),
                top_width_nm=_float_value(row.get("top_width_nm")),
                depth_nm=_float_value(row.get("depth_nm")),
                geometry_hash=str(row.get("geometry_hash", "")),
                solver_status=str(row.get("solver_status", "")),
                control_status="closed_geometry_control_must_remain_blocked",
                required_behavior="no pressure-flow validation request and no qch sidecar",
                hard_fail_if="closed_geometry_enters_formal_qch_or_route_score",
                claim_boundary=SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_CLAIM_BOUNDARY,
            )
        )
    return rows


def pressure_flow_validation_promotion_update_rows(
    request_rows: list[SidewallPressureFlowValidationRequestRow],
) -> list[dict[str, str]]:
    route_ids = sorted({row.route_candidate_id for row in request_rows})
    return [
        {
            "target_ledger_lane": "pressure_flow_validation",
            "covered_route_candidate_ids": ";".join(route_ids),
            "previous_status": "context_only_not_formal_validation",
            "new_context_status": (
                "exact_w500_d900_pressure_flow_validation_harness_ready_missing_external_result"
            ),
            "target_claim_current": "false",
            "blocked_promotion": (
                "formal_qch_weighting;route_score;winner;yield;detection_probability"
            ),
            "hard_fail_if": (
                "pressure_flow_validation_harness_promoted_without_exact_external_result"
            ),
            "next_required_evidence": (
                "run exact W500/D900 sidewall COMSOL pressure-flow or matched measurement "
                "and bind q_total/q_upper/q_lower/port_balance/quality_gate"
            ),
            "claim_boundary": SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_CLAIM_BOUNDARY,
        }
    ]


def _route_key(case_id: str) -> str:
    if case_id == "rectangle_limit_theta90_D900_W500":
        return "route_rectangle_limit_theta90_D900_W500"
    if case_id == "taper_theta85_D900_W500":
        return "route_taper_theta85_D900_W500"
    return f"route_{case_id}"


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
