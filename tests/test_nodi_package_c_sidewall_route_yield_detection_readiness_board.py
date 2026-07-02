from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_route_yield_detection_readiness_board as builder,
)


def test_readiness_board_packet_builds_from_current_artifacts() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["board_rows"] == 2
    assert summary["blocker_rows"] == 12
    assert summary["route_geometry_families"] == (
        "ideal_rectangle;trapezoid_tapered_sidewalls"
    )
    assert summary["ready_route_input_count_total"] == 6
    assert summary["missing_claim_evidence_count_total"] == 6
    assert summary["ready_blocker_rows"] == 6
    assert summary["missing_blocker_rows"] == 6
    assert summary["primary_next_execution_blocks"] in {
        "detector_blank_calibration",
        "sidewall_detector_blank_transfer_validation",
    }
    assert summary["secondary_next_execution_blocks"] == "wet_observation_bundle_intake"
    assert summary["route_formula_component_vector_ready_rows"] == 0
    assert summary["formula_policy_review_ready_rows"] == 0
    assert summary["route_score_current_rows"] == 0
    assert summary["winner_current_rows"] == 0
    assert summary["yield_current_rows"] == 0
    assert summary["detection_probability_current_rows"] == 0
    assert summary["wet_pass_probability_current_rows"] == 0
    assert summary["production_ingestion_current_rows"] == 0


def test_readiness_board_rows_mark_inputs_ready_and_claim_evidence_missing() -> None:
    rows = builder.build_payload()["board_rows"]

    assert {row["route_candidate_id"] for row in rows} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    for row in rows:
        assert row["q_ch_m3_s"] > 0.0
        assert row["qch_route_input_status"] == builder.READY_ROUTE_INPUT
        assert row["pressure_flow_route_input_status"] == builder.READY_ROUTE_INPUT
        assert row["selected_annulus_context_status"] == builder.READY_ROUTE_INPUT
        assert row["detector_blank_transfer_status"] == builder.MISSING_CLAIM_EVIDENCE
        assert row["wet_observation_status"] == builder.MISSING_CLAIM_EVIDENCE
        assert row["route_formula_component_status"] == builder.MISSING_CLAIM_EVIDENCE
        assert row["route_formula_component_vector_ready"] is False
        assert row["ready_route_input_count"] == 3
        assert row["missing_claim_evidence_count"] == 3
        assert row["readiness_fraction"] == 0.5
        assert row["route_score_current"] is False
        assert row["yield_current"] is False
        assert row["detection_probability_current"] is False
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_readiness_blockers_are_specific_and_non_claim() -> None:
    rows = builder.build_payload()["blocker_rows"]

    assert len(rows) == 12
    assert {
        row["evidence_lane"]
        for row in rows
        if row["readiness_class"] == builder.READY_ROUTE_INPUT
    } == {
        "formal_qch",
        "pressure_flow_validation",
        "selected_annulus_detection_context",
    }
    assert {
        row["evidence_lane"]
        for row in rows
        if row["readiness_class"] == builder.MISSING_CLAIM_EVIDENCE
    } == {"detector_blank_transfer", "wet_observation", "route_formula_component"}
    for row in rows:
        assert row["target_claim_current"] is False
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY
        assert row["hard_fail_if_promoted_without"]


def test_readiness_board_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_BOARD_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_BLOCKER_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert (
        "554_NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
