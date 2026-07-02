from __future__ import annotations

from nodi_simulator.sidewall_electrokinetic_grid_preflight import (
    SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_CLAIM_BOUNDARY,
    build_electrokinetic_grid_preflight,
)


def _solver_branch_rows() -> list[dict[str, object]]:
    return [
        {
            "branch_row_id": "SOLVER-BRANCH-electrokinetic_solver",
            "branch_id": "electrokinetic_solver",
            "user_authorization_status": "authorized",
        }
    ]


def _build():
    return build_electrokinetic_grid_preflight(
        solver_branch_rows=_solver_branch_rows()
    )


def test_preflight_preserves_rectangle_and_adds_trapezoid_requirements() -> None:
    rows, guards = _build()

    assert len(rows) == 4
    assert len(guards) == 6
    assert sum(row.channel_cross_section_model == "ideal_rectangle" for row in rows) == 1
    assert (
        sum(row.channel_cross_section_model == "trapezoid_tapered_sidewalls" for row in rows)
        == 3
    )
    assert {row.rectangle_baseline_preserved for row in rows} == {True}
    assert {row.claim_boundary for row in rows} == {
        SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_CLAIM_BOUNDARY
    }


def test_rectangle_path_is_baseline_only_not_trapezoid_solver() -> None:
    rows, _guards = _build()
    rectangle = next(row for row in rows if row.channel_cross_section_model == "ideal_rectangle")

    assert rectangle.legacy_rectangle_path_allowed is True
    assert rectangle.profile_aware_grid_current is False
    assert rectangle.electrokinetic_solver_output_current is False
    assert rectangle.current_status == "rectangle_legacy_diagnostic_allowed_not_trapezoid_claim"
    assert rectangle.hard_fail_if == "rectangle_baseline_cache_reused_for_trapezoid_request"


def test_trapezoid_rows_require_profile_grid_metadata_and_mutations() -> None:
    rows, _guards = _build()
    trapezoid_rows = [
        row for row in rows if row.channel_cross_section_model == "trapezoid_tapered_sidewalls"
    ]

    for row in trapezoid_rows:
        assert row.legacy_rectangle_path_allowed is False
        assert row.electrokinetic_grid_geometry_model == (
            "trapezoid_cut_cell_or_fem_grid_v1_required"
        )
        assert row.electrokinetic_wall_distance_model == (
            "trapezoid_signed_wall_distance_v1_required"
        )
        assert row.zeta_wall_model_required is True
        assert row.zeta_particle_model_required is True
        assert row.ionic_strength_required is True
        assert row.debye_length_required is True
        assert row.rectangle_limit_test_required is True
        assert row.theta_mutation_test_required is True
        assert row.zeta_sign_mutation_test_required is True
        assert row.ionic_strength_mutation_test_required is True


def test_no_solver_weight_route_or_detection_claims_current() -> None:
    rows, guards = _build()

    assert {row.profile_aware_grid_current for row in rows} == {False}
    assert {row.electrokinetic_solver_output_current for row in rows} == {False}
    assert {row.electrokinetic_weight_current for row in rows} == {False}
    assert {row.route_score_current for row in rows} == {False}
    assert {row.detection_probability_current for row in rows} == {False}
    assert {row.claim_promoted_current for row in guards} == {False}
    assert {row.claim_promotion_allowed_now for row in guards} == {False}


def test_claim_guards_cover_solver_weight_mutation_route_and_release() -> None:
    _rows, guards = _build()
    targets = {row.promotion_target for row in guards}

    assert targets == {
        "trapezoid_electrokinetic_solver_output",
        "trapezoid_boltzmann_wall_weighting",
        "zeta_sign_response",
        "ionic_strength_debye_response",
        "route_score_or_detection_probability",
        "production_or_fabrication_release",
    }
    for guard in guards:
        assert guard.implementation_authorized is True
        assert guard.required_evidence_before_true
        assert guard.hard_fail_if_missing_evidence
        assert guard.claim_boundary == SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_CLAIM_BOUNDARY
