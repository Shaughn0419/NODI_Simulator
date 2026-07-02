from __future__ import annotations

from nodi_simulator.sidewall_route_qch_detector_wet_blocker_binder import (
    SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_CLAIM_BOUNDARY,
    build_route_qch_detector_wet_blocker_binder,
)


def _preflight_rows() -> list[dict[str, object]]:
    return [
        {
            "route_candidate_id": "ROUTE-CAND-001",
            "route_geometry_family": "ideal_rectangle",
            "qch_sidecar_id": "QCH-CAND-001",
            "q_ch_m3_s": "1.2e-16",
            "formal_flow_split_fraction": "0.6",
            "qch_branch_ready": "True",
            "exact_pressure_flow_branch_ready": "True",
            "selected_annulus_context_ready": "True",
            "runtime_substep_guard_ready": "True",
            "detector_accepted_transfer_rows": "0",
            "wet_accepted_observation_rows": "0",
            "route_formula_input_ready_count": "4",
            "route_formula_required_input_count": "6",
            "route_formula_input_completeness_fraction": "0.666667",
        },
        {
            "route_candidate_id": "ROUTE-CAND-002",
            "route_geometry_family": "trapezoid_tapered_sidewalls",
            "qch_sidecar_id": "QCH-CAND-002",
            "q_ch_m3_s": "8e-17",
            "formal_flow_split_fraction": "0.4",
            "qch_branch_ready": "True",
            "exact_pressure_flow_branch_ready": "True",
            "selected_annulus_context_ready": "True",
            "runtime_substep_guard_ready": "True",
            "detector_accepted_transfer_rows": "0",
            "wet_accepted_observation_rows": "0",
            "route_formula_input_ready_count": "4",
            "route_formula_required_input_count": "6",
            "route_formula_input_completeness_fraction": "0.666667",
        },
    ]


def test_binder_keeps_current_qch_ready_and_detector_wet_blocked() -> None:
    rows, supersession = build_route_qch_detector_wet_blocker_binder(
        preflight_rows=_preflight_rows(),
        source_statuses={},
    )

    assert len(rows) == 2
    assert len(supersession) == 5
    assert {row.route_geometry_family for row in rows} == {
        "ideal_rectangle",
        "trapezoid_tapered_sidewalls",
    }
    assert {row.qch_status for row in rows} == {
        "formal_qch_input_ready_not_route_score"
    }
    assert {row.detector_blank_status for row in rows} == {
        "blocker_not_accepted_evidence"
    }
    assert {row.wet_observation_status for row in rows} == {
        "blocker_not_accepted_evidence"
    }


def test_binder_does_not_promote_route_yield_detection_claims() -> None:
    rows, _supersession = build_route_qch_detector_wet_blocker_binder(
        preflight_rows=_preflight_rows(),
        source_statuses={},
    )

    assert {row.route_score_current for row in rows} == {False}
    assert {row.winner_current for row in rows} == {False}
    assert {row.yield_current for row in rows} == {False}
    assert {row.detection_probability_current for row in rows} == {False}
    assert {row.wet_pass_probability_current for row in rows} == {False}
    assert {row.claim_boundary for row in rows} == {
        SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_CLAIM_BOUNDARY
    }
