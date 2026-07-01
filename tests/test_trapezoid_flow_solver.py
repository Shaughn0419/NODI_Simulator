from __future__ import annotations

import math

import pytest

from nodi_simulator.cross_section_geometry import TrapezoidCrossSection
from nodi_simulator.trapezoid_flow_solver import (
    TRAPEZOID_FLOW_SOLVER_CLAIM_LEVEL,
    TRAPEZOID_FLOW_SOLVER_VERSION,
    solve_trapezoid_pressure_flow_candidate,
)


def test_rectangle_limit_candidate_is_close_to_rectangular_proxy() -> None:
    geometry = TrapezoidCrossSection(
        top_width_m=500e-9,
        depth_m=900e-9,
        sidewall_taper_angle_deg=0.0,
    )

    result = solve_trapezoid_pressure_flow_candidate(geometry, grid_nx=21, grid_nu=21)

    assert result.solver_version == TRAPEZOID_FLOW_SOLVER_VERSION
    assert result.solver_claim_level == TRAPEZOID_FLOW_SOLVER_CLAIM_LEVEL
    assert result.solver_status == "candidate_solver_output"
    assert result.active_cell_count == 21 * 21
    assert result.conductance_shape_integral_m4 > 0.0
    assert result.resistance_ratio_vs_rectangle_proxy == pytest.approx(1.0, rel=0.35)
    assert result.not_qch_weighted is True
    assert result.q_ch_weighting_current is False
    assert result.route_score_current is False
    assert result.winner_current is False
    assert result.claim_boundary == "trapezoid_flow_solver_candidate_not_qch_not_route_not_wet"


def test_tapered_sidewalls_increase_candidate_resistance_vs_vertical() -> None:
    vertical = solve_trapezoid_pressure_flow_candidate(
        TrapezoidCrossSection(500e-9, 900e-9, 0.0),
        grid_nx=21,
        grid_nu=21,
    )
    tapered = solve_trapezoid_pressure_flow_candidate(
        TrapezoidCrossSection(500e-9, 900e-9, 5.0),
        grid_nx=21,
        grid_nu=21,
    )

    assert tapered.solver_status == "candidate_solver_output"
    assert tapered.active_cell_count < vertical.active_cell_count
    assert tapered.hydraulic_resistance_Pa_s_m3 > vertical.hydraulic_resistance_Pa_s_m3
    assert tapered.resistance_ratio_vs_rectangle_proxy > 1.0


def test_geometry_closed_trapezoid_flow_solver_blocks_without_qch() -> None:
    result = solve_trapezoid_pressure_flow_candidate(
        TrapezoidCrossSection(500e-9, 900e-9, 20.0),
        grid_nx=21,
        grid_nu=21,
    )

    assert result.solver_status == "blocked_geometry_closed"
    assert math.isinf(result.hydraulic_resistance_Pa_s_m3)
    assert result.active_cell_count == 0
    assert result.not_qch_weighted is True
    assert result.q_ch_weighting_current is False
    assert result.claim_boundary == "trapezoid_flow_solver_candidate_not_qch_not_route_not_wet"
