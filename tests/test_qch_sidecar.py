from __future__ import annotations

import math

import pytest

from nodi_simulator.qch_sidecar import (
    QCH_SIDECAR_CLAIM_BOUNDARY,
    QCH_SIDECAR_VERSION,
    build_qch_sidecar_candidates,
)


def _solver_rows() -> list[dict[str, str]]:
    return [
        {
            "case_id": "rectangle_limit_theta90_D900_W500",
            "solver_version": "trapezoid_poisson_no_slip_fd_candidate_v1",
            "solver_status": "candidate_solver_output",
            "solver_claim_level": "candidate_solver_output_not_comsol_validated_not_qch_weighted",
            "sidewall_taper_angle_deg_nodi": "0",
            "sidewall_deg_comsol": "90",
            "hydraulic_resistance_Pa_s_m3": "10",
        },
        {
            "case_id": "taper_theta85_D900_W500",
            "solver_version": "trapezoid_poisson_no_slip_fd_candidate_v1",
            "solver_status": "candidate_solver_output",
            "solver_claim_level": "candidate_solver_output_not_comsol_validated_not_qch_weighted",
            "sidewall_taper_angle_deg_nodi": "5",
            "sidewall_deg_comsol": "85",
            "hydraulic_resistance_Pa_s_m3": "30",
        },
        {
            "case_id": "closed_theta70_D900_W500",
            "solver_version": "trapezoid_poisson_no_slip_fd_candidate_v1",
            "solver_status": "blocked_geometry_closed",
            "solver_claim_level": "candidate_solver_output_not_comsol_validated_not_qch_weighted",
            "sidewall_taper_angle_deg_nodi": "20",
            "sidewall_deg_comsol": "70",
            "hydraulic_resistance_Pa_s_m3": "inf",
        },
    ]


def test_qch_sidecar_candidates_normalize_open_fixed_pressure_rows() -> None:
    rows = build_qch_sidecar_candidates(_solver_rows(), pressure_drop_Pa=90.0)

    assert [row.qch_sidecar_version for row in rows] == [QCH_SIDECAR_VERSION] * 3
    open_rows = [row for row in rows if row.qch_sidecar_status == "candidate_qch_sidecar_row"]
    assert len(open_rows) == 2
    assert open_rows[0].q_ch_candidate_m3_s == pytest.approx(9.0)
    assert open_rows[1].q_ch_candidate_m3_s == pytest.approx(3.0)
    assert sum(row.candidate_flow_split_fraction for row in rows) == pytest.approx(1.0)
    assert open_rows[0].candidate_flow_split_fraction == pytest.approx(0.75)
    assert open_rows[1].candidate_flow_split_fraction == pytest.approx(0.25)


def test_qch_sidecar_blocks_closed_geometry_without_route_or_yield() -> None:
    rows = build_qch_sidecar_candidates(_solver_rows(), pressure_drop_Pa=90.0)
    closed = rows[-1]

    assert closed.qch_sidecar_status == "blocked_source_solver_not_open"
    assert closed.q_ch_candidate_m3_s == 0.0
    assert closed.candidate_flow_split_fraction == 0.0
    assert closed.is_formal_gate2_qch_sidecar is False
    assert closed.candidate_flow_split_current is False
    assert closed.formal_qch_weighting_current is False
    assert closed.route_score_current is False
    assert closed.winner_current is False
    assert closed.yield_detection_probability_current is False
    assert closed.claim_boundary == QCH_SIDECAR_CLAIM_BOUNDARY


def test_qch_sidecar_requires_positive_pressure_drop() -> None:
    with pytest.raises(ValueError, match="pressure_drop_Pa"):
        build_qch_sidecar_candidates(_solver_rows(), pressure_drop_Pa=0.0)

    with pytest.raises(ValueError, match="pressure_drop_Pa"):
        build_qch_sidecar_candidates(_solver_rows(), pressure_drop_Pa=math.inf)
