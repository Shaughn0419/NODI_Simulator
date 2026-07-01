from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_wet_optical_detection_evidence_context as builder,
)


def test_wet_optical_detection_evidence_context_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["source_route_disposition"] == (
        "NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_READY_NOT_FINAL"
    )
    assert summary["evidence_context_rows"] >= 2
    assert summary["detection_context_available_rows"] >= 2
    assert summary["wet_context_available_rows"] >= 2
    assert summary["sidewall_specific_optical_solver_current"] is False
    assert summary["sidewall_specific_wet_evidence_current"] is False
    assert summary["detection_probability_current"] is False
    assert summary["yield_current"] is False
    assert summary["route_score_current"] is False


def test_wet_optical_detection_rows_bind_context_without_final_claims() -> None:
    rows = builder.build_payload()["evidence_context_rows"]

    assert rows
    assert {row["geometry_match_level"] for row in rows} == {
        "nearest_width_depth_context_only"
    }
    for row in rows:
        assert row["detection_context_status"].endswith("not_sidewall_specific")
        assert row["optical_context_status"].endswith("not_sidewall_optical_solver")
        assert row["wet_context_status"].endswith("not_wet_experiment")
        assert int(row["detection_context_rows"]) > 0
        assert int(row["ev_panel_context_rows"]) > 0
        assert float(row["route_detection_context_candidate_metric"]) > 0.0
        assert row["sidewall_specific_optical_solver_current"] == "false"
        assert row["sidewall_specific_wet_evidence_current"] == "false"
        assert row["detection_probability_current"] == "false"
        assert row["yield_current"] == "false"
        assert row["route_score_current"] == "false"
        assert row["winner_current"] == "false"
        assert row["claim_boundary"] == builder.WET_OPTICAL_DETECTION_EVIDENCE_CLAIM_BOUNDARY


def test_wet_optical_detection_promotion_gaps_are_explicit() -> None:
    gaps = builder.promotion_gap_rows()
    targets = {row["target"] for row in gaps}

    assert "sidewall_specific_detection_probability" in targets
    assert "wet_yield_or_recovery" in targets
    assert "route_score_or_winner" in targets
    assert "selected_annulus_detection_claim" in targets
    for row in gaps:
        assert row["current_value"] == "false"
        assert row["hard_fail_if"]


def test_wet_optical_detection_boundary_context_sources_are_bound() -> None:
    payload = builder.build_payload()
    rows = payload["boundary_context_rows"]
    ids = {row["context_id"] for row in rows}

    assert "detector_identity_report_147" in ids
    assert "depth_noise_report_146" in ids
    assert "bfp_roi_operator_summary" in ids
    assert "green_tensor_diagnostic" in ids
    assert "calibration_plan_advisor" in ids
    assert all(row["exists"] == "true" for row in rows)
    assert any(row["source_lock_status"] == "source_locked_clean_git_context" for row in rows)
    assert any(
        row["source_lock_status"] == "deferred_dirty_local_context_not_source_locked"
        for row in rows
    )
    assert all(
        row["sha256"]
        for row in rows
        if row["source_lock_status"] == "source_locked_clean_git_context"
    )


def test_wet_optical_detection_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_EVIDENCE_CONTEXT_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_GAPS_20260701.csv" in names
    assert f"{builder.PREFIX}_BOUNDARY_CONTEXT_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "525_NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
