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
        claim_value_summary={
            "detection_template_rows": 2,
            "yield_template_rows": 2,
            "detection_input_present": False,
            "yield_input_present": False,
            "detection_probability_current_rows": 0,
            "yield_current_rows": 0,
            "wet_pass_probability_current_rows": 0,
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
        detection_value_template_path="detection_value_template.csv",
        yield_value_template_path="yield_value_template.csv",
        detector_target_input_path="detector_input.csv",
        wet_target_input_path="wet_input.csv",
        detection_value_target_input_path="detection_value_input.csv",
        yield_value_target_input_path="yield_value_input.csv",
        wet_source_manifest_path="wet_source_manifest.csv",
        claim_value_source_manifest_path="claim_value_source_manifest.csv",
    )

    assert len(input_rows) == 4
    assert {row.input_branch for row in input_rows} == {
        "detector_blank_transfer",
        "wet_surface_observation",
        "detection_probability_value",
        "yield_wet_value",
    }
    by_branch = {row.input_branch: row for row in input_rows}
    assert by_branch["detector_blank_transfer"].source_manifest_path == ""
    assert (
        by_branch["wet_surface_observation"].source_manifest_path
        == "wet_source_manifest.csv"
    )
    assert (
        by_branch["detection_probability_value"].source_manifest_path
        == "claim_value_source_manifest.csv"
    )
    assert (
        by_branch["yield_wet_value"].source_manifest_path
        == "claim_value_source_manifest.csv"
    )
    assert {row.current_accepted_rows for row in input_rows} == {0}
    assert {row.ready_to_rerun_chain for row in input_rows} == {True}
    assert len(command_rows) == 11
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
        claim_value_summary={
            "detection_template_rows": 2,
            "yield_template_rows": 2,
            "detection_input_present": False,
            "yield_input_present": False,
            "detection_probability_current_rows": 0,
            "yield_current_rows": 0,
            "wet_pass_probability_current_rows": 0,
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
        detection_value_template_path="detection_value_template.csv",
        yield_value_template_path="yield_value_template.csv",
        detector_target_input_path="detector_input.csv",
        wet_target_input_path="wet_input.csv",
        detection_value_target_input_path="detection_value_input.csv",
        yield_value_target_input_path="yield_value_input.csv",
        wet_source_manifest_path="wet_source_manifest.csv",
        claim_value_source_manifest_path="claim_value_source_manifest.csv",
    )

    assert formula_rows[0].route_formula_ready_for_claim_review is True
    assert "policy/review" in formula_rows[0].next_required_action
    assert formula_rows[0].route_score_current is False
    assert formula_rows[0].yield_current is False
    assert formula_rows[0].detection_probability_current is False


def test_route_evidence_input_packet_marks_detector_ready_and_wet_missing() -> None:
    input_rows, _commands, formula_rows = build_route_evidence_input_packet(
        detector_intake_summary={"template_rows": 2},
        wet_intake_summary={"template_rows": 14},
        activation_summary={
            "detector_input_present": True,
            "wet_input_present": True,
            "detector_accepted_transfer_rows_total": 2,
            "wet_accepted_endpoint_count_total": 0,
        },
        claim_value_summary={
            "detection_template_rows": 2,
            "yield_template_rows": 2,
            "detection_input_present": True,
            "yield_input_present": True,
            "detection_probability_current_rows": 0,
            "yield_current_rows": 0,
            "wet_pass_probability_current_rows": 0,
        },
        closure_rows=[
            {
                "route_candidate_id": "ROUTE-CAND-001",
                "route_geometry_family": "ideal_rectangle",
                "qch_status": "formal_qch_input_ready_not_route_score",
                "detector_branch_ready": "True",
                "wet_branch_ready": "False",
                "route_formula_ready_for_claim_review": "False",
                "route_formula_activation_status": "blocked_wet_accepted_evidence_missing",
            }
        ],
        detector_template_path="detector_template.csv",
        wet_template_path="wet_template.csv",
        detection_value_template_path="detection_value_template.csv",
        yield_value_template_path="yield_value_template.csv",
        detector_target_input_path="detector_input.csv",
        wet_target_input_path="wet_input.csv",
        detection_value_target_input_path="detection_value_input.csv",
        yield_value_target_input_path="yield_value_input.csv",
        wet_source_manifest_path="wet_source_manifest.csv",
        claim_value_source_manifest_path="claim_value_source_manifest.csv",
    )

    by_branch = {row.input_branch: row for row in input_rows}
    assert by_branch["detector_blank_transfer"].current_accepted_rows == 2
    assert "already has accepted candidate rows" in (
        by_branch["detector_blank_transfer"].required_action
    )
    assert by_branch["wet_surface_observation"].current_accepted_rows == 0
    assert "simulation/assumption source manifest" in (
        by_branch["wet_surface_observation"].required_action
    )
    assert "claim-value simulation/assumption source manifest" in (
        by_branch["detection_probability_value"].required_action
    )
    assert "claim-value simulation/assumption source manifest" in (
        by_branch["yield_wet_value"].required_action
    )
    assert formula_rows[0].next_required_action == (
        "complete accepted wet simulation evidence inputs, then rerun the command chain"
    )
    assert formula_rows[0].route_score_current is False
