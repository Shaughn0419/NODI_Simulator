from __future__ import annotations

from nodi_simulator.sidewall_detector_wet_route_binding_closure import (
    SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_CLAIM_BOUNDARY,
    build_detector_wet_route_binding_closure,
)


def _route_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for route_id, family in [
        ("ROUTE-CAND-001", "ideal_rectangle"),
        ("ROUTE-CAND-002", "trapezoid_tapered_sidewalls"),
    ]:
        for lane, klass in [
            ("q_ch_route_input", "ready_route_input"),
            ("selected_annulus_context", "ready_route_input"),
            ("runtime_substep_guard", "guarded_runtime_smoke_evidence"),
            ("electrokinetic_profile_grid", "candidate"),
            ("flow_solver_candidate", "candidate" if "trapezoid" in family else "not_applicable"),
        ]:
            rows.append(
                {
                    "route_candidate_id": route_id,
                    "route_geometry_family": family,
                    "evidence_lane": lane,
                    "evidence_class": klass,
                }
            )
    return rows


def _build():
    return build_detector_wet_route_binding_closure(
        route_evidence_state_rows=_route_rows(),
        route_candidate_status={"candidate_metric_rows": 2},
        selected_annulus_status={"selected_annulus_context_current_rows": 2},
        detector_execution_status={"current_accepted_transfer_rows_total": 0},
        detector_validation_status={"accepted_fixture_rows": 2},
        wet_execution_status={"current_accepted_observation_rows_total": 0},
        wet_validation_status={"accepted_fixture_rows": 14},
    )


def test_closure_harness_tracks_both_routes_and_ready_inputs() -> None:
    rows, guards = _build()
    assert len(rows) == 2
    assert len(guards) == 5
    assert {row.route_geometry_family for row in rows} == {
        "ideal_rectangle",
        "trapezoid_tapered_sidewalls",
    }
    assert {row.qch_route_input_ready for row in rows} == {True}
    assert {row.selected_annulus_context_ready for row in rows} == {True}
    assert {row.runtime_substep_guard_ready for row in rows} == {True}
    assert {row.profile_grid_candidate_ready for row in rows} == {True}
    assert {row.detector_validator_hardened for row in rows} == {True}
    assert {row.wet_validator_hardened for row in rows} == {True}


def test_closure_harness_blocks_claims_until_accepted_detector_and_wet_rows() -> None:
    rows, guards = _build()
    assert {row.detector_accepted_transfer_rows for row in rows} == {0}
    assert {row.wet_accepted_observation_rows for row in rows} == {0}
    assert {row.route_formula_binding_authorized for row in rows} == {True}
    assert {row.route_formula_binding_status for row in rows} == {
        "blocked_accepted_detector_blank_and_wet_rows_required"
    }
    assert {row.route_score_current for row in rows} == {False}
    assert {row.yield_current for row in rows} == {False}
    assert {row.detection_probability_current for row in rows} == {False}
    assert {row.claim_boundary for row in rows} == {
        SIDEWALL_DETECTOR_WET_ROUTE_BINDING_CLOSURE_CLAIM_BOUNDARY
    }
    assert {guard.activation_allowed_now for guard in guards} == {False}


def test_detector_only_closure_opens_detection_guard_but_not_route_or_yield() -> None:
    rows, guards = build_detector_wet_route_binding_closure(
        route_evidence_state_rows=_route_rows(),
        route_candidate_status={"candidate_metric_rows": 2},
        selected_annulus_status={"selected_annulus_context_current_rows": 2},
        detector_execution_status={"current_accepted_transfer_rows_total": 2},
        detector_validation_status={"accepted_fixture_rows": 2},
        wet_execution_status={"current_accepted_observation_rows_total": 0},
        wet_validation_status={"accepted_fixture_rows": 14},
    )

    assert {row.detector_accepted_transfer_rows for row in rows} == {2}
    assert {row.wet_accepted_observation_rows for row in rows} == {0}
    assert {row.route_formula_binding_status for row in rows} == {
        "blocked_accepted_detector_blank_and_wet_rows_required"
    }
    by_target = {guard.claim_target: guard for guard in guards}
    assert by_target["detection_probability"].activation_allowed_now is True
    assert by_target["route_score_winner_JRC"].activation_allowed_now is False
    assert by_target["yield"].activation_allowed_now is False
    assert {row.route_score_current for row in rows} == {False}
    assert {row.yield_current for row in rows} == {False}
    assert {row.detection_probability_current for row in rows} == {False}
