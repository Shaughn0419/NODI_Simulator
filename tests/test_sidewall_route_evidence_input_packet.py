from __future__ import annotations

from nodi_simulator.sidewall_route_evidence_input_packet import (
    build_route_evidence_input_packet,
)


def test_route_evidence_input_packet_keeps_templates_separate_from_evidence() -> None:
    input_rows, command_rows, formula_rows = build_route_evidence_input_packet(
        detector_intake_summary={"template_rows": 2},
        wet_intake_summary={"template_rows": 14},
        activation_summary={
            "detector_input_present": False,
            "wet_input_present": False,
            "detector_accepted_transfer_rows_total": 0,
            "wet_accepted_endpoint_count_total": 0,
        },
        closure_rows=[
            {
                "route_candidate_id": "ROUTE-CAND-001",
                "route_geometry_family": "ideal_rectangle",
                "qch_status": "formal_qch_input_ready_not_route_score",
                "detector_branch_ready": "False",
                "wet_branch_ready": "False",
                "route_formula_ready_for_claim_review": "False",
                "route_formula_activation_status": "blocked_detector_wet_activation_required",
            }
        ],
        detector_template_path="detector_template.csv",
        wet_template_path="wet_template.csv",
        detector_target_input_path="detector_input.csv",
        wet_target_input_path="wet_input.csv",
    )

    assert len(input_rows) == 2
    assert {row.current_accepted_rows for row in input_rows} == {0}
    assert {row.ready_to_rerun_chain for row in input_rows} == {True}
    assert len(command_rows) == 4
    assert formula_rows[0].route_formula_ready_for_claim_review is False
    assert formula_rows[0].route_score_current is False
    assert formula_rows[0].yield_current is False
    assert formula_rows[0].detection_probability_current is False


def test_route_evidence_input_packet_can_mark_formula_review_ready_without_claims() -> None:
    _inputs, _commands, formula_rows = build_route_evidence_input_packet(
        detector_intake_summary={"template_rows": 2},
        wet_intake_summary={"template_rows": 14},
        activation_summary={
            "detector_input_present": True,
            "wet_input_present": True,
            "detector_accepted_transfer_rows_total": 2,
            "wet_accepted_endpoint_count_total": 14,
        },
        closure_rows=[
            {
                "route_candidate_id": "ROUTE-CAND-002",
                "route_geometry_family": "trapezoid_tapered_sidewalls",
                "qch_status": "formal_qch_input_ready_not_route_score",
                "detector_branch_ready": "True",
                "wet_branch_ready": "True",
                "route_formula_ready_for_claim_review": "True",
                "route_formula_activation_status": (
                    "route_formula_inputs_ready_for_claim_review_not_auto_scored"
                ),
                "route_score_current": "False",
                "winner_current": "False",
                "yield_current": "False",
                "detection_probability_current": "False",
            }
        ],
        detector_template_path="detector_template.csv",
        wet_template_path="wet_template.csv",
        detector_target_input_path="detector_input.csv",
        wet_target_input_path="wet_input.csv",
    )

    assert formula_rows[0].route_formula_ready_for_claim_review is True
    assert "policy/review" in formula_rows[0].next_required_action
    assert formula_rows[0].route_score_current is False
    assert formula_rows[0].yield_current is False
    assert formula_rows[0].detection_probability_current is False
