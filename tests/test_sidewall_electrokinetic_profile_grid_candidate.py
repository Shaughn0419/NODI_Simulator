from __future__ import annotations

from nodi_simulator.sidewall_electrokinetic_profile_grid_candidate import (
    SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_CLAIM_BOUNDARY,
    build_profile_grid_candidate,
)


def test_profile_grid_candidate_builds_rectangle_and_trapezoid_cases() -> None:
    case_rows, cell_rows, mutation_rows, guard_rows = build_profile_grid_candidate()
    assert len(case_rows) == 5
    assert len(cell_rows) == 2205
    assert len(mutation_rows) == 5
    assert len(guard_rows) == 5
    assert sum(row.channel_cross_section_model == "ideal_rectangle" for row in case_rows) == 1
    assert (
        sum(row.channel_cross_section_model == "trapezoid_tapered_sidewalls" for row in case_rows)
        == 4
    )
    assert {row.profile_aware_grid_current for row in case_rows} == {True}
    assert {row.electrokinetic_solver_output_current for row in case_rows} == {False}
    assert {row.route_score_current for row in case_rows} == {False}
    assert {row.claim_boundary for row in case_rows} == {
        SIDEWALL_ELECTROKINETIC_PROFILE_GRID_CANDIDATE_CLAIM_BOUNDARY
    }


def test_profile_grid_mutation_checks_pass_and_blocked_bins_have_no_weights() -> None:
    case_rows, cell_rows, mutation_rows, _guard_rows = build_profile_grid_candidate()
    assert {row.mutation_check_passed for row in mutation_rows} == {True}
    assert sum(row.blocked_cell_weight_rows for row in case_rows) == 0
    blocked_cells = [row for row in cell_rows if row.center_accessible is False]
    assert blocked_cells
    assert {row.electrostatic_weight_surrogate for row in blocked_cells} == {None}
    assert {row.blocked_reason for row in blocked_cells} == {
        "outside_particle_center_support"
    }


def test_theta_zeta_and_ionic_mutations_change_expected_metrics() -> None:
    case_rows, _cell_rows, mutation_rows, guard_rows = build_profile_grid_candidate()
    by_case = {row.case_id: row for row in case_rows}
    assert (
        by_case["trapezoid_theta85_base"].accessible_cell_rows
        != by_case["trapezoid_theta80_theta_mutation"].accessible_cell_rows
    )
    assert (
        by_case["trapezoid_theta85_base"].center_to_near_wall_weight_ratio
        != by_case["trapezoid_theta85_zeta_sign_flip"].center_to_near_wall_weight_ratio
    )
    assert (
        by_case["trapezoid_theta85_base"].debye_length_nm
        != by_case["trapezoid_theta85_high_ionic_strength"].debye_length_nm
    )
    assert {row.check_type for row in mutation_rows} == {
        "rectangle_limit",
        "theta_mutation",
        "zeta_sign_mutation",
        "ionic_strength_mutation",
        "blocked_bin_exclusion",
    }
    assert {row.claim_promotion_allowed_now for row in guard_rows} == {False}
