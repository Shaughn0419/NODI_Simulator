from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_integrated_promotion_ledger_detector_blank_refresh as builder,
)


def test_sidewall_integrated_promotion_ledger_detector_blank_refresh_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["refreshed_promotion_lane_rows"] == 18
    assert summary["detector_blank_delta_rows"] == 4
    assert summary["formal_qch_lane_rows_retained"] == 2
    assert summary["selected_annulus_context_available_rows_retained"] == 2
    assert summary["blank_context_available_rows"] == 2
    assert summary["detector_context_available_rows"] == 2
    assert summary["detector_response_validation_current"] is False
    assert summary["sidewall_specific_blank_trace_current"] is False
    assert summary["sidewall_specific_optical_calibration_current"] is False
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False


def test_detector_blank_lane_refresh_preserves_detection_boundary() -> None:
    rows = [
        row
        for row in builder.build_payload()["refreshed_promotion_lane_rows"]
        if row["evidence_lane"] in {"blank_false_positive_trace", "detector_response_bridge"}
    ]

    assert len(rows) == 4
    assert {row["source_disposition"] for row in rows} == {
        "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_READY_CONTEXT_ONLY"
    }
    assert all(
        row["source_artifact"].endswith(
            "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_CONTEXT_REFRESH_CONTEXT_ROWS_20260701.csv"
        )
        for row in rows
    )
    assert all(row["source_sha256"] for row in rows)
    assert {row["current_status"] for row in rows} == {
        "nearest_blank_context_available_not_sidewall_specific_validation",
        "detector_identity_context_available_not_sidewall_response_validation",
    }
    for row in rows:
        assert row["target_claim_current"] == "false"
        assert row["not_detection_probability"] == "true"
        assert row["not_route_score"] == "true"
        assert row["not_winner"] == "true"
        assert row["not_yield"] == "true"


def test_detector_blank_refresh_retains_upstream_lane_progress() -> None:
    rows = builder.build_payload()["refreshed_promotion_lane_rows"]
    qch_rows = [row for row in rows if row["evidence_lane"] == "flow_split_qch"]
    annulus_rows = [
        row for row in rows if row["evidence_lane"] == "selected_annulus_detection_context"
    ]

    assert len(qch_rows) == 2
    assert {row["current_status"] for row in qch_rows} == {
        "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting"
    }
    assert len(annulus_rows) == 2
    assert {row["current_status"] for row in annulus_rows} == {
        "selected_annulus_context_available_small_n_not_probability"
    }


def test_detector_blank_delta_rows_keep_claims_false() -> None:
    deltas = builder.build_payload()["refresh_delta_rows"]

    assert len(deltas) == 4
    assert {delta["evidence_lane"] for delta in deltas} == {
        "blank_false_positive_trace",
        "detector_response_bridge",
    }
    for delta in deltas:
        assert delta["target_claim_current"] == "false"
        assert "detector_response_validation" in delta["blocked_use"]
        assert "detection_probability" in delta["blocked_use"]
        assert "route_score" in delta["blocked_use"]
        assert delta["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_sidewall_integrated_promotion_ledger_detector_blank_refresh_outputs_manifest(
    tmp_path: Path,
) -> None:
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
    assert f"{builder.PREFIX}_PROMOTION_LANE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_DELTA_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert (
        "536_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_DETECTOR_BLANK_REFRESH_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
