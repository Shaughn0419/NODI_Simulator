"""Candidate q_ch sidecar rows derived from flow-solver evidence.

The sidecar computes fixed-pressure flow candidates from source hydraulic
resistance rows. It is candidate evidence for downstream route work; it is not
route scoring, winner selection, wet yield, or detection probability.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Iterable, Mapping


QCH_SIDECAR_VERSION = "qch_sidecar_candidate_from_trapezoid_flow_solver_v1"
QCH_SIDECAR_CLAIM_BOUNDARY = (
    "qch_sidecar_candidate_not_route_score_not_winner_not_yield_not_detection"
)


@dataclass(frozen=True)
class QchSidecarCandidateRow:
    qch_sidecar_id: str
    qch_sidecar_version: str
    qch_sidecar_status: str
    route_key: str
    NODI_view: str
    diameter_nm: str
    bin_basis: str
    source_case_id: str
    source_solver_version: str
    source_solver_status: str
    source_solver_claim_level: str
    pressure_drop_Pa: float
    hydraulic_resistance_Pa_s_m3: float
    q_ch_candidate_m3_s: float
    candidate_flow_split_fraction: float
    q_ch_units: str
    normalization_basis: str
    source_solve_hash: str
    geometry_hash: str
    integration_definition: str
    calibration_status: str
    is_formal_gate2_qch_sidecar: bool
    candidate_flow_split_current: bool
    formal_qch_weighting_current: bool
    route_score_current: bool
    winner_current: bool
    yield_detection_probability_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_qch_sidecar_candidates(
    solver_rows: Iterable[Mapping[str, Any]],
    *,
    pressure_drop_Pa: float = 1000.0,
    nodi_view: str = "sidewall_flow_candidate",
    diameter_nm: str = "aggregate_flow_sidecar",
    bin_basis: str = "route_geometry_aggregate",
) -> list[QchSidecarCandidateRow]:
    """Build normalized q_ch candidate rows from hydraulic resistance rows."""
    pressure = float(pressure_drop_Pa)
    if pressure <= 0.0 or not math.isfinite(pressure):
        raise ValueError("pressure_drop_Pa must be a finite positive value")

    normalized_input = [dict(row) for row in solver_rows]
    raw_q_values = [_candidate_q_from_row(row, pressure) for row in normalized_input]
    q_total = sum(q for q in raw_q_values if math.isfinite(q) and q > 0.0)

    candidates: list[QchSidecarCandidateRow] = []
    for index, (row, q_value) in enumerate(zip(normalized_input, raw_q_values), start=1):
        case_id = str(row.get("case_id", f"source_case_{index}"))
        status = str(row.get("solver_status", "missing_solver_status"))
        is_open_candidate = status == "candidate_solver_output" and q_value > 0.0
        split = float(q_value / q_total) if is_open_candidate and q_total > 0.0 else 0.0
        candidates.append(
            QchSidecarCandidateRow(
                qch_sidecar_id=f"QCH-CAND-{index:03d}",
                qch_sidecar_version=QCH_SIDECAR_VERSION,
                qch_sidecar_status=(
                    "candidate_qch_sidecar_row"
                    if is_open_candidate
                    else "blocked_source_solver_not_open"
                ),
                route_key=f"route_{case_id}",
                NODI_view=nodi_view,
                diameter_nm=diameter_nm,
                bin_basis=bin_basis,
                source_case_id=case_id,
                source_solver_version=str(row.get("solver_version", "")),
                source_solver_status=status,
                source_solver_claim_level=str(row.get("solver_claim_level", "")),
                pressure_drop_Pa=pressure,
                hydraulic_resistance_Pa_s_m3=_float_value(
                    row.get("hydraulic_resistance_Pa_s_m3")
                ),
                q_ch_candidate_m3_s=float(q_value if is_open_candidate else 0.0),
                candidate_flow_split_fraction=split,
                q_ch_units="m3/s",
                normalization_basis=(
                    "fixed_pressure_candidate_flow_split_over_open_solver_rows"
                ),
                source_solve_hash=_stable_hash(row),
                geometry_hash=_stable_hash(
                    {
                        key: row.get(key, "")
                        for key in (
                            "sidewall_taper_angle_deg_nodi",
                            "sidewall_deg_comsol",
                            "source_case_id",
                            "case_id",
                        )
                    }
                ),
                integration_definition=(
                    "q_ch_candidate_m3_s=pressure_drop_Pa/"
                    "hydraulic_resistance_Pa_s_m3"
                ),
                calibration_status="candidate_not_pressure_flow_calibrated",
                is_formal_gate2_qch_sidecar=False,
                candidate_flow_split_current=True if is_open_candidate else False,
                formal_qch_weighting_current=False,
                route_score_current=False,
                winner_current=False,
                yield_detection_probability_current=False,
                claim_boundary=QCH_SIDECAR_CLAIM_BOUNDARY,
            )
        )
    return candidates


def _candidate_q_from_row(row: Mapping[str, Any], pressure_drop_Pa: float) -> float:
    if str(row.get("solver_status", "")) != "candidate_solver_output":
        return 0.0
    resistance = _float_value(row.get("hydraulic_resistance_Pa_s_m3"))
    if resistance <= 0.0 or not math.isfinite(resistance):
        return 0.0
    return float(pressure_drop_Pa / resistance)


def _float_value(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return math.inf
    return numeric


def _stable_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
