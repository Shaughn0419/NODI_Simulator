from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_sidewall_route_yield_detection_policy as builder


def test_sidewall_route_yield_detection_policy_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["policy_rows"] == 2
    assert summary["blocker_rows"] == 12
    assert summary["required_lanes_per_route"] == 6
    assert summary["promotion_update_rows"] == 1
    assert summary["not_ready_policy_rows"] == 2
    assert summary["route_score_allowed_rows"] == 0
    assert summary["winner_allowed_rows"] == 0
    assert summary["yield_allowed_rows"] == 0
    assert summary["detection_probability_allowed_rows"] == 0
    assert summary["wet_pass_probability_allowed_rows"] == 0
    assert summary["primary_next_execution_blocks"] == [
        "qch_or_pressure_flow_validation"
    ]


def test_policy_rows_bind_current_integrated_ledger_statuses() -> None:
    rows = builder.build_payload()["policy_rows"]

    assert len(rows) == 2
    for row in rows:
        assert row["qch_policy_status"] == (
            "not_ready_grid_refined_split_candidate_absolute_q_requires_validation"
        )
        assert row["pressure_flow_policy_status"] == "not_ready_pressure_flow_context_only"
        assert row["selected_annulus_policy_status"] == (
            "not_ready_selected_annulus_small_n_not_probability"
        )
        assert row["detector_response_policy_status"] == (
            "not_ready_detector_identity_context_not_response_validation"
        )
        assert row["blank_false_positive_policy_status"] == (
            "not_ready_nearest_blank_context_not_sidewall_specific_validation"
        )
        assert row["wet_surface_policy_status"] == (
            "not_ready_wet_surface_contract_defined_no_validation"
        )
        assert row["route_score_allowed"] is False
        assert row["yield_allowed"] is False
        assert row["detection_probability_allowed"] is False
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_blocker_rows_cover_required_lanes_for_each_route() -> None:
    rows = builder.build_payload()["blocker_rows"]

    assert len(rows) == 12
    assert {row["evidence_lane"] for row in rows} == set(builder.REQUIRED_LANES)
    assert {row["blocker_status"] for row in rows} == {"blocked_not_claim_ready"}
    assert {row["route_candidate_id"] for row in rows} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    for row in rows:
        assert row["next_required_evidence"]
        assert row["hard_fail_if_promoted_without"]
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_route_policy_promotion_update_remains_not_claim_ready() -> None:
    updates = builder.build_payload()["promotion_update_rows"]

    assert len(updates) == 1
    update = updates[0]
    assert update["target_ledger_lane"] == "integrated_route_ledger"
    assert update["new_context_status"] == (
        "route_yield_detection_policy_defined_not_ready_for_claims"
    )
    assert update["target_claim_current"] == "false"
    assert "route_score" in update["blocked_promotion"]
    assert "yield" in update["blocked_promotion"]
    assert "detection_probability" in update["blocked_promotion"]
    assert update["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_sidewall_route_yield_detection_policy_outputs_manifest(tmp_path: Path) -> None:
    payload = builder.build_payload()
    old_output_dir = builder.OUTPUT_DIR
    old_report_dir = builder.REPORT_DIR
    try:
        builder.OUTPUT_DIR = tmp_path / "joint"
        builder.REPORT_DIR = tmp_path / "reports"
        paths = builder.write_outputs(payload)
    finally:
        builder.OUTPUT_DIR = old_output_dir
        builder.REPORT_DIR = old_report_dir

    names = {path.name for path in paths}
    assert f"{builder.PREFIX}_POLICY_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_BLOCKER_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "539_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
