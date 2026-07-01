"""W500/D900 sidewall q_ch grid-refinement validation helpers.

This module turns the existing trapezoid pressure-flow candidate solver into a
small grid-refinement evidence packet. It validates candidate flow split
stability for the exact W500/D900 rectangle and theta85 geometries, while
keeping absolute q_ch calibration, route scoring, and detection claims outside
this helper.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Iterable

from .cross_section_geometry import TrapezoidCrossSection
from .trapezoid_flow_solver import solve_trapezoid_pressure_flow_candidate


SIDEWALL_QCH_GRID_VALIDATION_VERSION = "sidewall_qch_grid_validation_w500_d900_v1"
SIDEWALL_QCH_GRID_VALIDATION_CLAIM_BOUNDARY = (
    "qch_grid_refinement_candidate_not_formal_qch_not_route_score"
)


@dataclass(frozen=True)
class SidewallQchGridRow:
    case_id: str
    qch_grid_validation_version: str
    grid_nx: int
    grid_nu: int
    sidewall_deg_comsol: float
    sidewall_taper_angle_deg_nodi: float
    top_width_nm: float
    depth_nm: float
    pressure_drop_Pa: float
    solver_status: str
    active_cell_count: int
    hydraulic_resistance_Pa_s_m3: float
    q_ch_grid_candidate_m3_s: float
    candidate_flow_split_fraction: float
    resistance_ratio_vs_rectangle_proxy: float
    geometry_hash: str
    solver_claim_level: str
    calibration_status: str
    qch_grid_validation_status: str
    split_candidate_current: bool
    absolute_qch_calibration_current: bool
    formal_qch_weighting_current: bool
    route_score_current: bool
    winner_current: bool
    yield_detection_probability_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallQchGridConvergenceRow:
    comparison_id: str
    qch_grid_validation_version: str
    case_id: str
    reference_grid_nx: int
    compared_grid_nx: int
    reference_q_ch_grid_candidate_m3_s: float
    compared_q_ch_grid_candidate_m3_s: float
    q_ch_relative_delta_vs_reference: float
    reference_split_fraction: float
    compared_split_fraction: float
    split_fraction_abs_delta_vs_reference: float
    split_candidate_convergence_status: str
    absolute_q_convergence_status: str
    calibration_status: str
    split_candidate_current: bool
    absolute_qch_calibration_current: bool
    formal_qch_weighting_current: bool
    route_score_current: bool
    winner_current: bool
    yield_detection_probability_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_sidewall_qch_grid_rows(
    *,
    grids: Iterable[int] = (21, 31, 41),
    pressure_drop_Pa: float = 1000.0,
) -> list[SidewallQchGridRow]:
    pressure = float(pressure_drop_Pa)
    if pressure <= 0.0 or not math.isfinite(pressure):
        raise ValueError("pressure_drop_Pa must be positive and finite")

    cases = [
        ("rectangle_limit_theta90_D900_W500", 90.0, 0.0),
        ("taper_theta85_D900_W500", 85.0, 5.0),
        ("closed_theta70_D900_W500", 70.0, 20.0),
    ]
    raw_rows: list[dict[str, Any]] = []
    for grid in grids:
        grid_int = int(grid)
        if grid_int < 5:
            raise ValueError("grid values must be >= 5")
        grid_results: list[dict[str, Any]] = []
        for case_id, sidewall_deg, taper_deg in cases:
            geometry = TrapezoidCrossSection(500.0e-9, 900.0e-9, taper_deg)
            result = solve_trapezoid_pressure_flow_candidate(
                geometry,
                grid_nx=grid_int,
                grid_nu=grid_int,
            )
            q_value = (
                pressure / result.hydraulic_resistance_Pa_s_m3
                if result.solver_status == "candidate_solver_output"
                and result.hydraulic_resistance_Pa_s_m3 > 0.0
                else 0.0
            )
            grid_results.append(
                {
                    "case_id": case_id,
                    "grid_nx": grid_int,
                    "grid_nu": grid_int,
                    "sidewall_deg_comsol": sidewall_deg,
                    "sidewall_taper_angle_deg_nodi": taper_deg,
                    "solver_status": result.solver_status,
                    "active_cell_count": result.active_cell_count,
                    "hydraulic_resistance_Pa_s_m3": result.hydraulic_resistance_Pa_s_m3,
                    "q_ch_grid_candidate_m3_s": q_value,
                    "resistance_ratio_vs_rectangle_proxy": (
                        result.resistance_ratio_vs_rectangle_proxy
                    ),
                    "solver_claim_level": result.solver_claim_level,
                    "geometry_hash": _stable_hash(
                        {
                            "case_id": case_id,
                            "top_width_nm": 500.0,
                            "depth_nm": 900.0,
                            "sidewall_deg_comsol": sidewall_deg,
                            "sidewall_taper_angle_deg_nodi": taper_deg,
                        }
                    ),
                }
            )
        open_total = sum(
            row["q_ch_grid_candidate_m3_s"]
            for row in grid_results
            if row["solver_status"] == "candidate_solver_output"
        )
        for row in grid_results:
            split = (
                row["q_ch_grid_candidate_m3_s"] / open_total
                if open_total > 0.0 and row["solver_status"] == "candidate_solver_output"
                else 0.0
            )
            row["candidate_flow_split_fraction"] = split
            raw_rows.append(row)

    return [
        SidewallQchGridRow(
            case_id=str(row["case_id"]),
            qch_grid_validation_version=SIDEWALL_QCH_GRID_VALIDATION_VERSION,
            grid_nx=int(row["grid_nx"]),
            grid_nu=int(row["grid_nu"]),
            sidewall_deg_comsol=float(row["sidewall_deg_comsol"]),
            sidewall_taper_angle_deg_nodi=float(row["sidewall_taper_angle_deg_nodi"]),
            top_width_nm=500.0,
            depth_nm=900.0,
            pressure_drop_Pa=pressure,
            solver_status=str(row["solver_status"]),
            active_cell_count=int(row["active_cell_count"]),
            hydraulic_resistance_Pa_s_m3=float(row["hydraulic_resistance_Pa_s_m3"]),
            q_ch_grid_candidate_m3_s=float(row["q_ch_grid_candidate_m3_s"]),
            candidate_flow_split_fraction=float(row["candidate_flow_split_fraction"]),
            resistance_ratio_vs_rectangle_proxy=float(
                row["resistance_ratio_vs_rectangle_proxy"]
            ),
            geometry_hash=str(row["geometry_hash"]),
            solver_claim_level=str(row["solver_claim_level"]),
            calibration_status=(
                "grid_refined_split_candidate_absolute_q_requires_validation"
                if row["solver_status"] == "candidate_solver_output"
                else "blocked_geometry_closed_no_qch"
            ),
            qch_grid_validation_status=(
                "grid_refinement_candidate_row"
                if row["solver_status"] == "candidate_solver_output"
                else "blocked_source_geometry_closed"
            ),
            split_candidate_current=row["solver_status"] == "candidate_solver_output",
            absolute_qch_calibration_current=False,
            formal_qch_weighting_current=False,
            route_score_current=False,
            winner_current=False,
            yield_detection_probability_current=False,
            claim_boundary=SIDEWALL_QCH_GRID_VALIDATION_CLAIM_BOUNDARY,
        )
        for row in raw_rows
    ]


def build_sidewall_qch_convergence_rows(
    grid_rows: Iterable[SidewallQchGridRow],
    *,
    reference_grid_nx: int = 41,
    split_delta_threshold: float = 0.01,
    q_delta_threshold: float = 0.05,
) -> list[SidewallQchGridConvergenceRow]:
    rows = list(grid_rows)
    reference_by_case = {
        row.case_id: row
        for row in rows
        if row.grid_nx == reference_grid_nx
        and row.solver_status == "candidate_solver_output"
    }
    comparisons: list[SidewallQchGridConvergenceRow] = []
    index = 1
    for row in rows:
        if row.solver_status != "candidate_solver_output":
            continue
        reference = reference_by_case.get(row.case_id)
        if reference is None:
            continue
        q_delta = _relative_delta(
            row.q_ch_grid_candidate_m3_s,
            reference.q_ch_grid_candidate_m3_s,
        )
        split_delta = abs(
            row.candidate_flow_split_fraction - reference.candidate_flow_split_fraction
        )
        comparisons.append(
            SidewallQchGridConvergenceRow(
                comparison_id=f"QCH-GRID-CONV-{index:03d}",
                qch_grid_validation_version=SIDEWALL_QCH_GRID_VALIDATION_VERSION,
                case_id=row.case_id,
                reference_grid_nx=reference_grid_nx,
                compared_grid_nx=row.grid_nx,
                reference_q_ch_grid_candidate_m3_s=(
                    reference.q_ch_grid_candidate_m3_s
                ),
                compared_q_ch_grid_candidate_m3_s=row.q_ch_grid_candidate_m3_s,
                q_ch_relative_delta_vs_reference=q_delta,
                reference_split_fraction=reference.candidate_flow_split_fraction,
                compared_split_fraction=row.candidate_flow_split_fraction,
                split_fraction_abs_delta_vs_reference=split_delta,
                split_candidate_convergence_status=(
                    "candidate_pass"
                    if split_delta <= split_delta_threshold
                    else "candidate_review_required"
                ),
                absolute_q_convergence_status=(
                    "candidate_pass"
                    if q_delta <= q_delta_threshold
                    else "candidate_review_required"
                ),
                calibration_status=(
                    "split_stable_absolute_q_requires_comsol_or_measurement_validation"
                ),
                split_candidate_current=True,
                absolute_qch_calibration_current=False,
                formal_qch_weighting_current=False,
                route_score_current=False,
                winner_current=False,
                yield_detection_probability_current=False,
                claim_boundary=SIDEWALL_QCH_GRID_VALIDATION_CLAIM_BOUNDARY,
            )
        )
        index += 1
    return comparisons


def _relative_delta(value: float, reference: float) -> float:
    if reference == 0.0 or not math.isfinite(reference):
        return math.inf
    return abs(value - reference) / abs(reference)


def _stable_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
