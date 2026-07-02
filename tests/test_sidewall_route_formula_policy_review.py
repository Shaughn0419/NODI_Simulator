from __future__ import annotations

from pytest import approx

from nodi_simulator.sidewall_route_formula_policy_review import (
    FIXTURE_EVIDENCE_CLASS,
    SIMULATION_ACCEPTED_EVIDENCE_CLASS,
    SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_CLAIM_BOUNDARY,
    build_route_formula_policy_review,
)


def _dry_row(
    route_id: str,
    *,
    ready: bool,
    flow_split: str = "0.625",
) -> dict[str, str]:
    return {
        "route_candidate_id": route_id,
        "route_geometry_family": "ideal_rectangle"
        if route_id == "ROUTE-CAND-001"
        else "trapezoid_tapered_sidewalls",
        "qch_sidecar_id": f"QCH-{route_id}",
        "q_ch_m3_s": "1.0e-16",
        "formal_flow_split_fraction": flow_split,
        "route_formula_ready_for_claim_review": str(ready),
        "diagnostic_detector_gate_component_value": "1.0" if ready else "0.0",
        "diagnostic_wet_gate_component_value": "1.0" if ready else "0.0",
        "route_formula_review_dry_run_status": (
            "route_formula_component_vector_ready_for_policy_review_not_scored"
            if ready
            else "blocked_until_detector_wet_evidence_accepted"
        ),
    }


def test_simulation_path_blocks_until_component_vector_ready() -> None:
    rows, guards = build_route_formula_policy_review(
        route_formula_dry_run_rows=[
            _dry_row("ROUTE-CAND-001", ready=False),
            _dry_row("ROUTE-CAND-002", ready=False, flow_split="0.375"),
        ],
        source_evidence_class=SIMULATION_ACCEPTED_EVIDENCE_CLASS,
    )

    assert len(rows) == 2
    assert len(guards) == 6
    for row in rows:
        assert row.route_formula_component_vector_ready is False
        assert row.route_score_activation_allowed_now is False
        assert row.simulation_route_score_candidate_current is False
        assert row.route_score_current is False
        assert row.route_score_value_current == ""
        assert row.route_score_candidate_value == 0.0
        assert row.winner_current is False
        assert row.yield_current is False
        assert row.detection_probability_current is False
        assert row.claim_boundary == SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_CLAIM_BOUNDARY


def test_simulation_accepted_path_can_activate_route_score_candidate() -> None:
    rows, guards = build_route_formula_policy_review(
        route_formula_dry_run_rows=[
            _dry_row("ROUTE-CAND-001", ready=True, flow_split="0.625"),
            _dry_row("ROUTE-CAND-002", ready=True, flow_split="0.375"),
        ],
        source_evidence_class=SIMULATION_ACCEPTED_EVIDENCE_CLASS,
    )

    by_route = {row.route_candidate_id: row for row in rows}
    assert by_route["ROUTE-CAND-001"].simulation_route_score_candidate_current is True
    assert by_route["ROUTE-CAND-001"].route_score_current is False
    assert by_route["ROUTE-CAND-001"].route_score_candidate_value == approx(0.85)
    assert by_route["ROUTE-CAND-002"].route_score_candidate_value == approx(0.75)
    assert by_route["ROUTE-CAND-002"].simulation_route_score_value_current == "0.75"
    route_score_guard = next(row for row in guards if row.promotion_target == "route_score")
    assert route_score_guard.activation_allowed_now is False
    simulation_guard = next(
        row for row in guards if row.promotion_target == "simulation_route_score_candidate"
    )
    assert simulation_guard.activation_allowed_now is True
    assert all(row.winner_current is False for row in rows)


def test_fixture_path_computes_candidate_without_promotion() -> None:
    rows, guards = build_route_formula_policy_review(
        route_formula_dry_run_rows=[
            _dry_row("ROUTE-CAND-001", ready=True, flow_split="0.625"),
            _dry_row("ROUTE-CAND-002", ready=True, flow_split="0.375"),
        ],
        source_evidence_class=FIXTURE_EVIDENCE_CLASS,
    )

    assert {row.route_score_candidate_value for row in rows} == {0.85, 0.75}
    for row in rows:
        assert row.fixture_not_evidence is True
        assert row.route_score_activation_allowed_now is False
        assert row.simulation_route_score_candidate_current is False
        assert row.route_score_current is False
        assert row.route_score_value_current == ""
        assert row.route_formula_policy_review_status == (
            "fixture_route_score_candidate_path_passes_not_evidence"
        )
    route_score_guard = next(row for row in guards if row.promotion_target == "route_score")
    assert route_score_guard.activation_allowed_now is False
