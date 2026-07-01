from __future__ import annotations

from nodi_simulator.sidewall_integrated_promotion_ledger import (
    SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY,
    build_blocker_catalog_rows,
    build_integrated_promotion_lane_rows,
    build_integrated_promotion_ledger_rows,
)
from nodi_simulator.sidewall_optical_calibration_bridge import (
    build_sidewall_optical_calibration_readiness_rows,
)


def test_integrated_promotion_ledger_blocks_claim_promotion() -> None:
    readiness = [row.to_dict() for row in build_sidewall_optical_calibration_readiness_rows()]
    blockers = build_blocker_catalog_rows(calibration_readiness_rows=readiness)
    rows = build_integrated_promotion_ledger_rows(
        route_candidate_rows=[
            {
                "route_candidate_id": "ROUTE-CAND-002",
                "route_key": "route_taper_theta85_D900_W500",
                "source_case_id": "taper_theta85_D900_W500",
                "qch_sidecar_id": "QCH-CAND-002",
                "qch_sidecar_status": "candidate_qch_sidecar_row",
                "candidate_flow_split_fraction": "0.396627059978",
            }
        ],
        wet_context_rows=[
            {
                "route_candidate_id": "ROUTE-CAND-002",
                "wet_context_status": "ev_weighted_panel_surrogate_context_available_not_wet_experiment",
                "selected_annulus_context_status": "selected_annulus_context_missing_rerun_required",
                "sidewall_specific_wet_evidence_current": "false",
            }
        ],
        qch_rows=[
            {
                "qch_sidecar_id": "QCH-CAND-002",
                "formal_qch_weighting_current": "false",
            }
        ],
        pressure_rows=[
            {
                "qch_sidecar_id": "QCH-CAND-002",
                "validation_status": "context_only_not_formal_validation",
            }
        ],
        calibration_bridge_summary={
            "disposition": "NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_READY_SEED_ONLY",
            "source_reference_smoke_disposition": "NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_SMOKE_READY_NOT_OPTICAL_SOLVER",
            "calibrated_lookup_unlock_status": "blocked_synthetic_fixture_not_experimental",
            "full_wave_or_calibrated_optical_solver_current": False,
            "true_W_eff_current": False,
            "detector_response_validation_current": False,
        },
        blocker_catalog_rows=blockers,
    )

    assert len(rows) == 1
    row = rows[0]
    assert row.promotion_preflight_status == (
        "blocked_missing_calibrated_optical_wet_route_evidence"
    )
    assert row.blocker_count >= 9
    assert "formal_qch_sidecar_not_accepted" in row.blocker_ids
    assert "true_reference_calibration_from_synthetic_seed" in row.blocker_ids
    assert row.sidewall_reference_surrogate_smoke_current is True
    assert row.full_wave_or_calibrated_optical_solver_current is False
    assert row.detection_probability_current is False
    assert row.route_score_current is False
    assert row.not_route_score is True
    assert row.not_winner is True
    assert row.not_yield is True
    assert row.not_detection_probability is True
    assert row.claim_boundary == SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY

    lane_rows = build_integrated_promotion_lane_rows(
        ledger_rows=rows,
        blocker_catalog_rows=blockers,
        source_artifact_by_lane={
            "flow_split_qch": (
                "reports/joint_interface_20260701/NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_QCH_ROWS_20260701.csv",
                "sha",
                "candidate_qch_sidecar_not_formal_weighting",
            )
        },
    )
    assert len(lane_rows) == len(blockers)
    assert all(lane.route_candidate_id == "ROUTE-CAND-002" for lane in lane_rows)
    assert all(lane.target_claim_current is False for lane in lane_rows)
    assert all(lane.not_route_score is True for lane in lane_rows)
    assert any(lane.evidence_lane == "flow_split_qch" for lane in lane_rows)
    assert any(
        lane.hard_fail_if_promoted_without
        == "true_reference_calibration_from_synthetic_seed"
        for lane in lane_rows
    )


def test_blocker_catalog_includes_calibration_and_route_lanes() -> None:
    readiness = [row.to_dict() for row in build_sidewall_optical_calibration_readiness_rows()]
    blockers = build_blocker_catalog_rows(calibration_readiness_rows=readiness)
    ids = {row.blocker_id for row in blockers}
    lanes = {row.evidence_lane for row in blockers}

    assert "formal_qch_sidecar_not_accepted" in ids
    assert "pressure_flow_context_only_not_formal_validation" in ids
    assert "selected_annulus_context_missing" in ids
    assert "blank_channel_reference_amplitude_phase" in lanes
    assert "wet_wall_interaction" in lanes
    for row in blockers:
        assert row.required_before_promotion
        assert row.claim_boundary == SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY
