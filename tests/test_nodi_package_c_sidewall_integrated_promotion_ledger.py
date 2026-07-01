from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_sidewall_integrated_promotion_ledger as builder


def test_sidewall_integrated_promotion_ledger_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["ledger_rows"] == 2
    assert summary["blocker_catalog_rows"] >= 9
    assert summary["promotion_lane_rows"] == (
        summary["ledger_rows"] * summary["blocker_catalog_rows"]
    )
    assert summary["blocked_promotion_rows"] == 2
    assert summary["formal_qch_weighting_current"] is False
    assert summary["full_wave_or_calibrated_optical_solver_current"] is False
    assert summary["detection_probability_current"] is False
    assert summary["yield_current"] is False
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False


def test_sidewall_integrated_promotion_ledger_rows_are_preflight_only() -> None:
    rows = builder.build_payload()["ledger_rows"]
    route_ids = {row["route_candidate_id"] for row in rows}

    assert route_ids == {"ROUTE-CAND-001", "ROUTE-CAND-002"}
    for row in rows:
        assert row["promotion_preflight_status"] == (
            "blocked_missing_calibrated_optical_wet_route_evidence"
        )
        assert int(row["blocker_count"]) >= 9
        assert "formal_qch_sidecar_not_accepted" in row["blocker_ids"]
        assert "true_reference_calibration_from_synthetic_seed" in row["blocker_ids"]
        assert row["calibrated_lookup_unlock_status"] == (
            "blocked_synthetic_fixture_not_experimental"
        )
        assert row["formal_qch_weighting_current"] == "false"
        assert row["route_score_current"] == "false"
        assert row["winner_current"] == "false"
        assert row["yield_current"] == "false"
        assert row["detection_probability_current"] == "false"
        assert row["not_route_score"] == "true"
        assert row["not_winner"] == "true"
        assert row["not_yield"] == "true"
        assert row["not_detection_probability"] == "true"
        assert row["claim_boundary"] == (
            builder.SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY
        )


def test_sidewall_integrated_promotion_ledger_blocker_catalog_covers_main_lanes() -> None:
    blockers = builder.build_payload()["blocker_catalog"]
    lanes = {row["evidence_lane"] for row in blockers}

    assert "flow_split_qch" in lanes
    assert "pressure_flow_validation" in lanes
    assert "blank_channel_reference_amplitude_phase" in lanes
    assert "detector_response_bridge" in lanes
    assert "blank_false_positive_trace" in lanes
    assert "wet_wall_interaction" in lanes
    assert "integrated_route_ledger" in lanes
    for row in blockers:
        assert row["required_before_promotion"]
        assert row["claim_boundary"] == (
            builder.SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY
        )


def test_sidewall_integrated_promotion_ledger_lane_rows_have_source_and_guards() -> None:
    payload = builder.build_payload()
    lanes = payload["promotion_lane_rows"]

    assert len(lanes) == payload["summary"]["promotion_lane_rows"]
    assert {
        (row["route_candidate_id"], row["evidence_lane"]) for row in lanes
    } >= {
        ("ROUTE-CAND-001", "flow_split_qch"),
        ("ROUTE-CAND-002", "blank_channel_reference_amplitude_phase"),
        ("ROUTE-CAND-002", "wet_wall_interaction"),
    }
    for row in lanes:
        assert row["source_artifact"]
        assert row["source_disposition"]
        assert row["target_claim_current"] == "false"
        assert row["hard_fail_if_promoted_without"]
        assert row["not_route_score"] == "true"
        assert row["not_winner"] == "true"
        assert row["not_yield"] == "true"
        assert row["not_detection_probability"] == "true"
        assert row["claim_boundary"] == (
            builder.SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY
        )


def test_sidewall_integrated_promotion_ledger_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_LEDGER_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_BLOCKER_CATALOG_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_LANE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "530_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
