from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_integrated_promotion_ledger_qch_refresh as builder,
)


def test_sidewall_integrated_promotion_ledger_qch_refresh_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["refreshed_promotion_lane_rows"] == 18
    assert summary["qch_delta_rows"] == 2
    assert summary["qch_grid_refined_lane_rows"] == 2
    assert summary["selected_annulus_context_available_rows"] == 2
    assert summary["formal_qch_weighting_current"] is False
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False


def test_qch_lane_refresh_preserves_candidate_boundary() -> None:
    payload = builder.build_payload()
    rows = [
        row
        for row in payload["refreshed_promotion_lane_rows"]
        if row["evidence_lane"] == "flow_split_qch"
    ]

    assert len(rows) == 2
    for row in rows:
        assert row["source_artifact"].endswith(
            "NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_CONVERGENCE_ROWS_20260701.csv"
        )
        assert row["source_sha256"]
        assert row["source_disposition"] == (
            "NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_READY_CANDIDATE_ONLY"
        )
        assert row["current_status"] == (
            "w500_d900_grid_refined_split_candidate_absolute_q_requires_validation"
        )
        assert row["target_claim_current"] == "false"
        assert row["hard_fail_if_promoted_without"] == (
            "grid_refined_split_candidate_promoted_to_formal_qch_or_route_score"
        )
        assert "exact COMSOL or measurement" in row["next_required_evidence"]
        assert row["not_detection_probability"] == "true"
        assert row["not_route_score"] == "true"
        assert row["not_winner"] == "true"
        assert row["not_yield"] == "true"


def test_qch_refresh_keeps_selected_annulus_lane_available() -> None:
    rows = [
        row
        for row in builder.build_payload()["refreshed_promotion_lane_rows"]
        if row["evidence_lane"] == "selected_annulus_detection_context"
    ]

    assert len(rows) == 2
    assert {row["current_status"] for row in rows} == {
        "selected_annulus_context_available_small_n_not_probability"
    }


def test_qch_delta_rows_keep_claims_false() -> None:
    deltas = builder.build_payload()["refresh_delta_rows"]

    assert len(deltas) == 2
    for delta in deltas:
        assert delta["evidence_lane"] == "flow_split_qch"
        assert delta["new_current_status"] == (
            "w500_d900_grid_refined_split_candidate_absolute_q_requires_validation"
        )
        assert delta["target_claim_current"] == "false"
        assert "formal_qch_weighting" in delta["blocked_use"]
        assert "route_score" in delta["blocked_use"]
        assert "detection_probability" in delta["blocked_use"]
        assert delta["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_sidewall_integrated_promotion_ledger_qch_refresh_outputs_manifest(tmp_path: Path) -> None:
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
    assert "534_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_QCH_REFRESH_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
