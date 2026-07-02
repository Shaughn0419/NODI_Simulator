from __future__ import annotations

from nodi_simulator.sidewall_route_yield_detection_assembly import (
    ASSEMBLY_NOT_CLAIM_READY_STATUS,
    DETECTOR_BLANK_TRANSFER_NO_EVIDENCE_STATUS,
    SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_CLAIM_BOUNDARY,
    build_route_yield_detection_assembly,
)


def _lane(route_id: str, lane: str, status: str) -> dict[str, str]:
    route_key = (
        "route_rectangle_limit_theta90_D900_W500"
        if route_id == "ROUTE-CAND-001"
        else "route_taper_theta85_D900_W500"
    )
    source_case_id = (
        "rectangle_limit_theta90_D900_W500"
        if route_id == "ROUTE-CAND-001"
        else "taper_theta85_D900_W500"
    )
    return {
        "route_candidate_id": route_id,
        "route_key": route_key,
        "source_case_id": source_case_id,
        "qch_sidecar_id": f"QCH-{route_id}",
        "evidence_lane": lane,
        "current_status": status,
        "next_required_evidence": f"next evidence for {lane}",
    }


def _promotion_rows() -> list[dict[str, str]]:
    statuses = {
        "flow_split_qch": "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting",
        "pressure_flow_validation": (
            "exact_w500_d900_pressure_flow_result_accepted_formal_qch_sidecar_ready"
        ),
        "selected_annulus_detection_context": (
            "expanded_selected_annulus_panel_available_not_probability"
        ),
        "detector_response_bridge": (
            "detector_response_panel_candidate_not_sidewall_calibrated"
        ),
        "blank_false_positive_trace": "nearest_blank_guard_bound_to_panel_not_sidewall_specific",
        "wet_wall_interaction": "wet_surface_observation_intake_ready_no_observations",
        "blank_channel_reference_amplitude_phase": "synthetic_seed_available_not_experimental",
        "sidewall_geometry_coverage": "single_W500_D900_theta85_and_rectangle_seed_only",
        "integrated_route_ledger": "route_yield_detection_policy_defined_not_ready_for_claims",
    }
    return [
        _lane(route_id, lane, status)
        for route_id in ("ROUTE-CAND-001", "ROUTE-CAND-002")
        for lane, status in statuses.items()
    ]


def _promotion_rows_after_detector_blank_transfer_refresh() -> list[dict[str, str]]:
    rows = _promotion_rows()
    for row in rows:
        if row["evidence_lane"] in {
            "detector_response_bridge",
            "blank_false_positive_trace",
        }:
            row["current_status"] = DETECTOR_BLANK_TRANSFER_NO_EVIDENCE_STATUS
    return rows


def _policy_rows() -> list[dict[str, str]]:
    return [
        {
            "route_candidate_id": route_id,
            "route_policy_status": (
                "not_ready_missing_detector_blank_wet_selected_annulus_evidence_after_formal_qch_pressure_flow"
            ),
            "primary_next_execution_block": "sidewall_detector_blank_transfer_validation",
            "next_required_evidence": "policy next evidence",
        }
        for route_id in ("ROUTE-CAND-001", "ROUTE-CAND-002")
    ]


def _blocker_rows() -> list[dict[str, str]]:
    blocker_status = {
        "flow_split_qch": "ready_for_route_input_not_final_claim",
        "pressure_flow_validation": "ready_for_route_input_not_final_claim",
        "selected_annulus_detection_context": "ready_for_route_input_not_final_claim",
        "detector_response_bridge": "blocked_not_claim_ready",
        "blank_false_positive_trace": "blocked_not_claim_ready",
        "wet_wall_interaction": "blocked_not_claim_ready",
    }
    return [
        {
            "route_candidate_id": route_id,
            "evidence_lane": lane,
            "blocker_status": status,
            "next_required_evidence": f"blocker evidence for {lane}",
        }
        for route_id in ("ROUTE-CAND-001", "ROUTE-CAND-002")
        for lane, status in blocker_status.items()
    ]


def test_route_yield_detection_assembly_keeps_rectangle_and_trapezoid_parallel() -> None:
    assembly_rows, branch_rows = build_route_yield_detection_assembly(
        _promotion_rows(), _policy_rows(), _blocker_rows()
    )

    assert len(assembly_rows) == 2
    assert len(branch_rows) == 8
    assert {row.route_geometry_family for row in assembly_rows} == {
        "ideal_rectangle",
        "trapezoid_tapered_sidewalls",
    }
    for row in assembly_rows:
        assert row.ready_input_lane_count == 3
        assert row.candidate_context_lane_count == 5
        assert row.missing_or_blocked_lane_count == 1
        assert row.input_completeness_fraction == 1.0
        assert row.assembly_status == ASSEMBLY_NOT_CLAIM_READY_STATUS
        assert row.next_executable_branch == "sidewall_detector_blank_transfer_validation"
        assert row.route_score_allowed is False
        assert row.winner_allowed is False
        assert row.yield_allowed is False
        assert row.detection_probability_allowed is False
        assert row.wet_pass_probability_allowed is False
        assert row.claim_boundary == SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_CLAIM_BOUNDARY


def test_route_yield_detection_assembly_branch_rows_are_not_claims() -> None:
    _assembly_rows, branch_rows = build_route_yield_detection_assembly(
        _promotion_rows(), _policy_rows(), _blocker_rows()
    )

    assert {row.branch_name for row in branch_rows} == {
        "sidewall_detector_blank_transfer_validation",
        "wet_observation_bundle_intake",
        "route_candidate_assembly",
        "detection_probability_calibration",
    }
    for row in branch_rows:
        assert row.target_claim_current is False
        assert row.claim_boundary == SIDEWALL_ROUTE_YIELD_DETECTION_ASSEMBLY_CLAIM_BOUNDARY
    detection_rows = [
        row for row in branch_rows if row.branch_name == "detection_probability_calibration"
    ]
    assert {row.implementation_can_start for row in detection_rows} == {False}


def test_route_yield_detection_assembly_recognizes_transfer_intake_without_evidence() -> None:
    assembly_rows, branch_rows = build_route_yield_detection_assembly(
        _promotion_rows_after_detector_blank_transfer_refresh(),
        _policy_rows(),
        _blocker_rows(),
    )

    assert len(assembly_rows) == 2
    for row in assembly_rows:
        assert row.ready_input_lane_count == 3
        assert row.candidate_context_lane_count == 3
        assert row.missing_or_blocked_lane_count == 3
        assert row.detector_response_bridge_status == DETECTOR_BLANK_TRANSFER_NO_EVIDENCE_STATUS
        assert row.blank_false_positive_trace_status == DETECTOR_BLANK_TRANSFER_NO_EVIDENCE_STATUS
        assert row.next_executable_branch == "sidewall_detector_blank_transfer_validation"
        assert row.detection_probability_allowed is False

    transfer_rows = [
        row
        for row in branch_rows
        if row.branch_name == "sidewall_detector_blank_transfer_validation"
    ]
    assert {row.branch_status for row in transfer_rows} == {
        "transfer_intake_ready_waiting_for_sidewall_transfer_rows"
    }
