"""Candidate trapezoid cross-section pressure-flow solver.

The solver computes a no-slip Poisson cross-section surrogate for straight
trapezoid sidewalls:

    laplacian(phi) = -1
    phi = 0 on the channel walls
    Q = (dp/dy) / viscosity * integral(phi dA)

It is intentionally packaged as candidate solver evidence. It is not q_ch
weighting, not route selection, and not COMSOL validation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any

import numpy as np

from .cross_section_geometry import TrapezoidCrossSection
from .fluidic_resistance import compute_rectangular_channel_hydraulic_resistance


TRAPEZOID_FLOW_SOLVER_VERSION = "trapezoid_poisson_no_slip_fd_candidate_v1"
TRAPEZOID_FLOW_SOLVER_CLAIM_LEVEL = (
    "candidate_solver_output_not_comsol_validated_not_qch_weighted"
)


@dataclass(frozen=True)
class TrapezoidFlowSolverResult:
    solver_version: str
    solver_claim_level: str
    solver_status: str
    top_width_m: float
    depth_m: float
    sidewall_taper_angle_deg: float
    viscosity_Pa_s: float
    length_m: float
    grid_nx: int
    grid_nu: int
    active_cell_count: int
    conductance_shape_integral_m4: float
    hydraulic_resistance_Pa_s_m3: float
    rectangle_proxy_resistance_Pa_s_m3: float
    resistance_ratio_vs_rectangle_proxy: float
    not_qch_weighted: bool
    q_ch_weighting_current: bool
    route_score_current: bool
    winner_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def solve_trapezoid_pressure_flow_candidate(
    geometry: TrapezoidCrossSection,
    *,
    viscosity_Pa_s: float = 1.0e-3,
    length_m: float = 50.0e-6,
    grid_nx: int = 25,
    grid_nu: int = 25,
) -> TrapezoidFlowSolverResult:
    """Solve a small finite-difference Poisson surrogate on a trapezoid mask."""
    viscosity = float(viscosity_Pa_s)
    length = float(length_m)
    nx = int(grid_nx)
    nu = int(grid_nu)
    if viscosity <= 0.0 or length <= 0.0:
        raise ValueError("viscosity_Pa_s and length_m must be positive")
    if nx < 5 or nu < 5:
        raise ValueError("grid_nx and grid_nu must be >= 5")

    rectangle_proxy = compute_rectangular_channel_hydraulic_resistance(
        geometry.top_width_m,
        geometry.depth_m,
        length,
        viscosity,
    )
    if geometry.closure_status == "geometry_closed":
        return _blocked_result(
            geometry,
            viscosity_Pa_s=viscosity,
            length_m=length,
            grid_nx=nx,
            grid_nu=nu,
            rectangle_proxy=rectangle_proxy,
        )

    x_min = -0.5 * geometry.top_width_m
    dx = geometry.top_width_m / nx
    du = geometry.depth_m / nu
    cells: list[tuple[int, int, float, float]] = []
    cell_index: dict[tuple[int, int], int] = {}
    for iu in range(nu):
        u = (iu + 0.5) * du
        half_width = geometry.half_width_at_depth_m(u, clipped=True)
        for ix in range(nx):
            x = x_min + (ix + 0.5) * dx
            if abs(x) < half_width:
                cell_index[(ix, iu)] = len(cells)
                cells.append((ix, iu, x, u))

    n = len(cells)
    if n == 0:
        return _blocked_result(
            geometry,
            viscosity_Pa_s=viscosity,
            length_m=length,
            grid_nx=nx,
            grid_nu=nu,
            rectangle_proxy=rectangle_proxy,
        )

    matrix = np.zeros((n, n), dtype=float)
    rhs = np.ones(n, dtype=float)
    inv_dx2 = 1.0 / (dx * dx)
    inv_du2 = 1.0 / (du * du)
    for row, (ix, iu, _x, _u) in enumerate(cells):
        matrix[row, row] = 2.0 * inv_dx2 + 2.0 * inv_du2
        for nix, niu, coeff in (
            (ix - 1, iu, -inv_dx2),
            (ix + 1, iu, -inv_dx2),
            (ix, iu - 1, -inv_du2),
            (ix, iu + 1, -inv_du2),
        ):
            col = cell_index.get((nix, niu))
            if col is not None:
                matrix[row, col] = coeff

    phi = np.linalg.solve(matrix, rhs)
    conductance_shape_integral = float(np.sum(phi) * dx * du)
    if conductance_shape_integral <= 0.0 or not math.isfinite(conductance_shape_integral):
        resistance = math.inf
        ratio = math.inf
        status = "blocked_nonpositive_conductance"
    else:
        resistance = float(viscosity * length / conductance_shape_integral)
        ratio = float(resistance / rectangle_proxy)
        status = "candidate_solver_output"

    return TrapezoidFlowSolverResult(
        solver_version=TRAPEZOID_FLOW_SOLVER_VERSION,
        solver_claim_level=TRAPEZOID_FLOW_SOLVER_CLAIM_LEVEL,
        solver_status=status,
        top_width_m=float(geometry.top_width_m),
        depth_m=float(geometry.depth_m),
        sidewall_taper_angle_deg=float(geometry.sidewall_taper_angle_deg),
        viscosity_Pa_s=viscosity,
        length_m=length,
        grid_nx=nx,
        grid_nu=nu,
        active_cell_count=n,
        conductance_shape_integral_m4=conductance_shape_integral,
        hydraulic_resistance_Pa_s_m3=resistance,
        rectangle_proxy_resistance_Pa_s_m3=rectangle_proxy,
        resistance_ratio_vs_rectangle_proxy=ratio,
        not_qch_weighted=True,
        q_ch_weighting_current=False,
        route_score_current=False,
        winner_current=False,
        claim_boundary="trapezoid_flow_solver_candidate_not_qch_not_route_not_wet",
    )


def _blocked_result(
    geometry: TrapezoidCrossSection,
    *,
    viscosity_Pa_s: float,
    length_m: float,
    grid_nx: int,
    grid_nu: int,
    rectangle_proxy: float,
) -> TrapezoidFlowSolverResult:
    return TrapezoidFlowSolverResult(
        solver_version=TRAPEZOID_FLOW_SOLVER_VERSION,
        solver_claim_level=TRAPEZOID_FLOW_SOLVER_CLAIM_LEVEL,
        solver_status="blocked_geometry_closed",
        top_width_m=float(geometry.top_width_m),
        depth_m=float(geometry.depth_m),
        sidewall_taper_angle_deg=float(geometry.sidewall_taper_angle_deg),
        viscosity_Pa_s=float(viscosity_Pa_s),
        length_m=float(length_m),
        grid_nx=int(grid_nx),
        grid_nu=int(grid_nu),
        active_cell_count=0,
        conductance_shape_integral_m4=0.0,
        hydraulic_resistance_Pa_s_m3=math.inf,
        rectangle_proxy_resistance_Pa_s_m3=float(rectangle_proxy),
        resistance_ratio_vs_rectangle_proxy=math.inf,
        not_qch_weighted=True,
        q_ch_weighting_current=False,
        route_score_current=False,
        winner_current=False,
        claim_boundary="trapezoid_flow_solver_candidate_not_qch_not_route_not_wet",
    )
