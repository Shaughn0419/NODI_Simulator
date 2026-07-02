from __future__ import annotations

from nodi_simulator.sidewall_winner_jrc_policy_review import (
    FIXTURE_EVIDENCE_CLASS,
    SIMULATION_ACCEPTED_EVIDENCE_CLASS,
    SIDEWALL_WINNER_JRC_POLICY_REVIEW_CLAIM_BOUNDARY,
    build_winner_jrc_policy_review,
)


def _score_row(
    route_id: str,
    *,
    score: str,
    current: bool,
) -> dict[str, str]:
    return {
        "route_candidate_id": route_id,
        "route_geometry_family": "ideal_rectangle"
        if route_id == "ROUTE-CAND-001"
        else "trapezoid_tapered_sidewalls",
        "route_score_current": str(current),
        "route_score_value_current": score if current else "",
        "simulation_route_score_candidate_current": str(current),
        "simulation_route_score_value_current": score if current else "",
        "route_score_candidate_value": score,
    }


def test_blocks_without_current_route_scores() -> None:
    rows, guards = build_winner_jrc_policy_review(
        route_formula_policy_rows=[
            _score_row("ROUTE-CAND-001", score="0.85", current=False),
            _score_row("ROUTE-CAND-002", score="0.75", current=False),
        ],
        source_evidence_class=SIMULATION_ACCEPTED_EVIDENCE_CLASS,
    )

    assert len(rows) == 2
    assert len(guards) == 5
    assert rows[0].candidate_order_index_under_policy == 1
    for row in rows:
        assert row.route_score_current is False
        assert row.simulation_route_score_candidate_current is False
        assert row.winner_activation_allowed_now is False
        assert row.winner_current is False
        assert row.JRC_current is False
        assert row.yield_current is False
        assert row.detection_probability_current is False
        assert row.claim_boundary == SIDEWALL_WINNER_JRC_POLICY_REVIEW_CLAIM_BOUNDARY


def test_simulation_current_scores_activate_unique_winner_jrc() -> None:
    rows, guards = build_winner_jrc_policy_review(
        route_formula_policy_rows=[
            _score_row("ROUTE-CAND-001", score="0.85", current=True),
            _score_row("ROUTE-CAND-002", score="0.75", current=True),
        ],
        source_evidence_class=SIMULATION_ACCEPTED_EVIDENCE_CLASS,
    )

    by_route = {row.route_candidate_id: row for row in rows}
    assert by_route["ROUTE-CAND-001"].simulation_top_candidate_current is True
    assert by_route["ROUTE-CAND-001"].winner_current is False
    assert by_route["ROUTE-CAND-001"].JRC_current is False
    assert by_route["ROUTE-CAND-001"].JRC_value_current == ""
    assert by_route["ROUTE-CAND-002"].winner_current is False
    winner_guard = next(row for row in guards if row.promotion_target == "winner_JRC")
    assert winner_guard.activation_allowed_now is False
    simulation_guard = next(
        row for row in guards if row.promotion_target == "simulation_top_candidate"
    )
    assert simulation_guard.activation_allowed_now is True
    assert {row.yield_current for row in rows} == {False}


def test_fixture_order_does_not_promote_winner() -> None:
    rows, guards = build_winner_jrc_policy_review(
        route_formula_policy_rows=[
            _score_row("ROUTE-CAND-001", score="0.85", current=False),
            _score_row("ROUTE-CAND-002", score="0.75", current=False),
        ],
        source_evidence_class=FIXTURE_EVIDENCE_CLASS,
    )

    assert [row.route_candidate_id for row in rows] == [
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    ]
    for row in rows:
        assert row.fixture_not_evidence is True
        assert row.winner_current is False
        assert row.JRC_current is False
        assert row.winner_jrc_policy_review_status == (
            "fixture_winner_order_path_passes_not_evidence"
        )
    winner_guard = next(row for row in guards if row.promotion_target == "winner_JRC")
    assert winner_guard.activation_allowed_now is False
