from __future__ import annotations

from nodi_simulator.sidewall_route_formula_activation_closure import (
    build_route_formula_activation_closure,
)


def _binder_rows() -> list[dict[str, object]]:
    return [
        {
            "route_candidate_id": "ROUTE-CAND-001",
            "route_geometry_family": "ideal_rectangle",
            "qch_sidecar_id": "QCH-CAND-001",
            "qch_status": "formal_qch_input_ready_not_route_score",
            "q_ch_m3_s": "1e-16",
            "formal_flow_split_fraction": "0.6",
        }
    ]


def test_formula_activation_closure_blocks_until_detector_wet_ready() -> None:
    rows = build_route_formula_activation_closure(
        qch_detector_wet_binder_rows=_binder_rows(),
        detector_wet_activation_rows=[
            {
                "route_candidate_id": "ROUTE-CAND-001",
                "route_formula_blocker_status": "blocked_detector_blank_or_wet_accepted_evidence_missing",
                "detector_branch_ready_for_formula": "False",
                "wet_branch_ready_for_formula": "False",
            }
        ],
    )

    assert len(rows) == 1
    assert rows[0].route_formula_ready_for_claim_review is False
    assert rows[0].route_formula_ready_for_simulation_candidate_review is False
    assert rows[0].route_formula_activation_status == "blocked_detector_wet_activation_required"
    assert rows[0].route_score_current is False
    assert rows[0].yield_current is False
    assert rows[0].detection_probability_current is False


def test_formula_activation_closure_can_reach_review_ready_without_claims() -> None:
    rows = build_route_formula_activation_closure(
        qch_detector_wet_binder_rows=_binder_rows(),
        detector_wet_activation_rows=[
            {
                "route_candidate_id": "ROUTE-CAND-001",
                "route_formula_blocker_status": "detector_wet_branches_ready_for_formula_review",
                "detector_branch_ready_for_formula": "True",
                "wet_branch_ready_for_formula": "True",
            }
        ],
    )

    assert rows[0].route_formula_ready_for_claim_review is True
    assert rows[0].route_formula_ready_for_simulation_candidate_review is True
    assert rows[0].route_formula_activation_status == (
        "route_formula_inputs_ready_for_simulation_candidate_review_not_auto_scored"
    )
    assert rows[0].route_score_current is False
    assert rows[0].yield_current is False
    assert rows[0].detection_probability_current is False
