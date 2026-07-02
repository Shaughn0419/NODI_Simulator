from __future__ import annotations

from nodi_simulator.sidewall_route_formula_review_dry_run import (
    build_route_formula_review_dry_run,
)


def _closure_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "route_candidate_id": "ROUTE-CAND-001",
        "route_geometry_family": "ideal_rectangle",
        "qch_sidecar_id": "QCH-CAND-001",
        "qch_status": "formal_qch_input_ready_not_route_score",
        "q_ch_m3_s": "1.2e-16",
        "formal_flow_split_fraction": "0.6",
        "detector_branch_ready": "False",
        "wet_branch_ready": "False",
        "route_formula_ready_for_claim_review": "False",
    }
    row.update(overrides)
    return row


def test_dry_run_blocks_when_detector_wet_gates_are_missing() -> None:
    rows = build_route_formula_review_dry_run(closure_rows=[_closure_row()])
    row = rows[0]

    assert row.qch_component_ready is True
    assert row.detector_component_ready is False
    assert row.wet_component_ready is False
    assert row.diagnostic_component_completeness_fraction == 0.333333
    assert row.route_formula_review_dry_run_status == (
        "blocked_until_detector_wet_evidence_accepted"
    )
    assert row.route_score_current is False
    assert row.yield_current is False
    assert row.detection_probability_current is False


def test_dry_run_marks_detector_ready_and_waits_for_wet_gate() -> None:
    rows = build_route_formula_review_dry_run(
        closure_rows=[_closure_row(detector_branch_ready="True")]
    )
    row = rows[0]

    assert row.qch_component_ready is True
    assert row.detector_component_ready is True
    assert row.wet_component_ready is False
    assert row.diagnostic_component_completeness_fraction == 0.666667
    assert row.route_formula_review_dry_run_status == (
        "blocked_until_wet_evidence_accepted"
    )
    assert row.next_required_action == (
        "complete accepted wet evidence inputs, rerun activation closure"
    )
    assert row.route_score_current is False
    assert row.yield_current is False
    assert row.detection_probability_current is False


def test_dry_run_component_vector_can_be_ready_without_scoring() -> None:
    rows = build_route_formula_review_dry_run(
        closure_rows=[
            _closure_row(
                detector_branch_ready="True",
                wet_branch_ready="True",
                route_formula_ready_for_claim_review="True",
            )
        ]
    )
    row = rows[0]

    assert row.route_formula_ready_for_claim_review is True
    assert row.diagnostic_detector_gate_component_value == 1.0
    assert row.diagnostic_wet_gate_component_value == 1.0
    assert row.diagnostic_component_completeness_fraction == 1.0
    assert row.route_formula_review_dry_run_status == (
        "route_formula_component_vector_ready_for_policy_review_not_scored"
    )
    assert row.route_score_current is False
    assert row.route_score_value_current == ""
    assert row.winner_current is False
