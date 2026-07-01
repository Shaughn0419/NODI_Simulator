from __future__ import annotations

from nodi_simulator.sidewall_qch_grid_validation import (
    SIDEWALL_QCH_GRID_VALIDATION_CLAIM_BOUNDARY,
    build_sidewall_qch_convergence_rows,
    build_sidewall_qch_grid_rows,
)


def test_sidewall_qch_grid_rows_cover_w500_d900_open_and_closed_cases() -> None:
    rows = build_sidewall_qch_grid_rows(grids=(21, 31, 41))

    assert len(rows) == 9
    assert {row.case_id for row in rows} == {
        "rectangle_limit_theta90_D900_W500",
        "taper_theta85_D900_W500",
        "closed_theta70_D900_W500",
    }
    closed = [row for row in rows if row.case_id == "closed_theta70_D900_W500"]
    assert {row.qch_grid_validation_status for row in closed} == {
        "blocked_source_geometry_closed"
    }
    assert all(row.q_ch_grid_candidate_m3_s == 0.0 for row in closed)


def test_sidewall_qch_grid_split_is_stable_but_absolute_q_not_promoted() -> None:
    rows = build_sidewall_qch_grid_rows(grids=(21, 31, 41))
    convergence = build_sidewall_qch_convergence_rows(rows, reference_grid_nx=41)

    assert len(convergence) == 6
    assert max(row.split_fraction_abs_delta_vs_reference for row in convergence) < 0.003
    assert any(
        row.absolute_q_convergence_status == "candidate_review_required"
        for row in convergence
        if row.compared_grid_nx == 21
    )
    for row in convergence:
        assert row.split_candidate_convergence_status == "candidate_pass"
        assert row.absolute_qch_calibration_current is False
        assert row.formal_qch_weighting_current is False
        assert row.route_score_current is False
        assert row.winner_current is False
        assert row.yield_detection_probability_current is False
        assert row.claim_boundary == SIDEWALL_QCH_GRID_VALIDATION_CLAIM_BOUNDARY


def test_sidewall_qch_grid_candidate_preserves_route_claim_guards() -> None:
    rows = build_sidewall_qch_grid_rows(grids=(41,))
    open_rows = [row for row in rows if row.solver_status == "candidate_solver_output"]

    assert len(open_rows) == 2
    assert sum(row.candidate_flow_split_fraction for row in open_rows) == 1.0
    for row in open_rows:
        assert row.split_candidate_current is True
        assert row.absolute_qch_calibration_current is False
        assert row.formal_qch_weighting_current is False
        assert row.route_score_current is False
        assert row.winner_current is False
        assert row.yield_detection_probability_current is False
        assert row.claim_boundary == SIDEWALL_QCH_GRID_VALIDATION_CLAIM_BOUNDARY
