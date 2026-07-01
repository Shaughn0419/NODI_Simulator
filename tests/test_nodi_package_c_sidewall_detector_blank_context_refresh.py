from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_sidewall_detector_blank_context_refresh as builder


def test_sidewall_detector_blank_context_refresh_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["context_rows"] == 2
    assert summary["detector_blank_context_available_rows"] == 2
    assert summary["promotion_update_rows"] == 2
    assert summary["detector_response_validation_current"] is False
    assert summary["sidewall_specific_blank_trace_current"] is False
    assert summary["detection_probability_current"] is False
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False
    assert summary["yield_current"] is False


def test_sidewall_detector_blank_context_rows_are_context_only() -> None:
    rows = builder.build_payload()["context_rows"]

    assert {row["route_candidate_id"] for row in rows} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    for row in rows:
        assert row["detector_blank_lane_status"] == (
            "detector_blank_context_available_not_probability"
        )
        assert row["selected_annulus_context_status"] == (
            "selected_annulus_context_available_small_n_not_probability"
        )
        assert row["qch_flow_split_context_status"] == (
            "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting"
        )
        assert row["blank_false_positive_context_status"] == (
            "nearest_blank_context_available_not_sidewall_specific_validation"
        )
        assert row["detector_response_context_status"] == (
            "detector_identity_context_available_not_sidewall_response_validation"
        )
        assert row["detection_probability_current"] == "false"
        assert row["route_score_current"] == "false"
        assert row["winner_current"] == "false"
        assert row["yield_current"] == "false"
        assert row["claim_boundary"] == builder.SIDEWALL_DETECTOR_BLANK_CONTEXT_CLAIM_BOUNDARY


def test_sidewall_detector_blank_context_promotion_updates_are_not_claims() -> None:
    updates = builder.build_payload()["promotion_update_rows"]

    assert {row["target_ledger_lane"] for row in updates} == {
        "blank_false_positive_trace",
        "detector_response_bridge",
    }
    for row in updates:
        assert row["target_claim_current"] == "false"
        assert "detection_probability" in row["blocked_promotion"]
        assert "route_score" in row["blocked_promotion"]
        assert row["claim_boundary"] == builder.SIDEWALL_DETECTOR_BLANK_CONTEXT_CLAIM_BOUNDARY


def test_sidewall_detector_blank_context_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_CONTEXT_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "535_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
