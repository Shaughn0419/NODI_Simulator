from __future__ import annotations

from nodi_simulator.sidewall_route_formula_binding_preflight import (
    SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_CLAIM_BOUNDARY,
    build_route_formula_binding_preflight,
)


def _qch_delta_rows() -> list[dict[str, object]]:
    return [
        {
            "route_candidate_id": "ROUTE-CAND-001",
            "route_geometry_family": "ideal_rectangle",
            "evidence_class": "accepted_exact_pressure_flow_for_formal_qch_sidecar",
            "may_satisfy_route_formula_qch_branch_now": "True",
            "q_ch_m3_s": "1.2e-16",
            "formal_flow_split_fraction": "0.6",
        },
        {
            "route_candidate_id": "ROUTE-CAND-002",
            "route_geometry_family": "trapezoid_tapered_sidewalls",
            "evidence_class": "accepted_exact_pressure_flow_for_formal_qch_sidecar",
            "may_satisfy_route_formula_qch_branch_now": "True",
            "q_ch_m3_s": "8.0e-17",
            "formal_flow_split_fraction": "0.4",
        },
    ]


def _candidate_rows() -> list[dict[str, object]]:
    return [
        {
            "route_candidate_id": "ROUTE-CAND-001",
            "qch_sidecar_id": "QCH-CAND-001",
            "route_key": "route_rectangle_limit_theta90_D900_W500",
            "source_case_id": "rectangle_limit_theta90_D900_W500",
            "route_decision_candidate_metric": "0.6",
            "candidate_sort_index_under_context": "1",
        },
        {
            "route_candidate_id": "ROUTE-CAND-002",
            "qch_sidecar_id": "QCH-CAND-002",
            "route_key": "route_taper_theta85_D900_W500",
            "source_case_id": "taper_theta85_D900_W500",
            "route_decision_candidate_metric": "0.4",
            "candidate_sort_index_under_context": "2",
        },
    ]


def _closure_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for route_id, family in [
        ("ROUTE-CAND-001", "ideal_rectangle"),
        ("ROUTE-CAND-002", "trapezoid_tapered_sidewalls"),
    ]:
        rows.append(
            {
                "route_candidate_id": route_id,
                "route_geometry_family": family,
                "selected_annulus_context_ready": "True",
                "runtime_substep_guard_ready": "True",
                "detector_validator_hardened": "True",
                "wet_validator_hardened": "True",
                "detector_accepted_transfer_rows": "0",
                "wet_accepted_observation_rows": "0",
            }
        )
    return rows


def test_preflight_marks_qch_ready_but_detector_wet_blocked() -> None:
    rows, branches, guards = build_route_formula_binding_preflight(
        qch_delta_rows=_qch_delta_rows(),
        route_candidate_rows=_candidate_rows(),
        detector_wet_closure_rows=_closure_rows(),
    )

    assert len(rows) == 2
    assert len(branches) == 12
    assert len(guards) == 5
    assert {row.route_geometry_family for row in rows} == {
        "ideal_rectangle",
        "trapezoid_tapered_sidewalls",
    }
    assert {row.qch_branch_ready for row in rows} == {True}
    assert {row.exact_pressure_flow_branch_ready for row in rows} == {True}
    assert {row.detector_branch_ready for row in rows} == {False}
    assert {row.wet_branch_ready for row in rows} == {False}
    assert {row.route_formula_binding_status for row in rows} == {
        "blocked_detector_blank_and_wet_accepted_evidence_required"
    }


def test_preflight_does_not_emit_claims() -> None:
    rows, branches, guards = build_route_formula_binding_preflight(
        qch_delta_rows=_qch_delta_rows(),
        route_candidate_rows=_candidate_rows(),
        detector_wet_closure_rows=_closure_rows(),
    )

    assert {row.route_score_current for row in rows} == {False}
    assert {row.winner_current for row in rows} == {False}
    assert {row.yield_current for row in rows} == {False}
    assert {row.detection_probability_current for row in rows} == {False}
    assert {branch.target_claim_current for branch in branches} == {False}
    assert {guard.activation_allowed_now for guard in guards} == {False}
    assert {row.claim_boundary for row in rows} == {
        SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_CLAIM_BOUNDARY
    }
