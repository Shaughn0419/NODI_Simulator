from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_integrated_promotion_ledger_formal_qch_refresh as builder,
)


def test_sidewall_integrated_promotion_ledger_formal_qch_refresh_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["source_route_policy_refresh_disposition"] == (
        "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_READY_PREFLIGHT_ONLY"
    )
    assert summary["source_formal_qch_binder_disposition"] == (
        "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_FORMAL_QCH_SIDECAR_READY"
    )
    assert summary["formal_qch_delta_rows"] == 4
    assert summary["formal_qch_lane_rows"] == 2
    assert summary["pressure_flow_accepted_lane_rows"] == 2
    assert summary["primary_next_execution_block"] == (
        "detector_blank_calibration_and_wet_surface_validation"
    )
    assert summary["formal_qch_sidecar_current"] is True
    assert summary["formal_qch_weighting_current"] is False
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False


def test_formal_qch_refresh_updates_only_qch_and_pressure_lanes() -> None:
    rows = builder.build_payload()["refreshed_promotion_lane_rows"]

    qch_rows = [row for row in rows if row["evidence_lane"] == "flow_split_qch"]
    pressure_rows = [
        row for row in rows if row["evidence_lane"] == "pressure_flow_validation"
    ]
    assert len(qch_rows) == 2
    assert len(pressure_rows) == 2
    assert {row["current_status"] for row in qch_rows} == {
        "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting"
    }
    assert {row["current_status"] for row in pressure_rows} == {
        "exact_w500_d900_pressure_flow_result_accepted_formal_qch_sidecar_ready"
    }
    for row in qch_rows + pressure_rows:
        assert row["target_claim_current"] == "false"
        assert row["not_route_score"] == "true"
        assert row["not_winner"] == "true"
        assert row["not_yield"] == "true"
        assert row["not_detection_probability"] == "true"


def test_formal_qch_refresh_keeps_detector_blank_wet_as_next_blockers() -> None:
    rows = builder.build_payload()["refreshed_promotion_lane_rows"]
    expected = {
        "selected_annulus_detection_context": (
            "selected_annulus_context_available_small_n_not_probability"
        ),
        "detector_response_bridge": (
            "detector_identity_context_available_not_sidewall_response_validation"
        ),
        "blank_false_positive_trace": (
            "nearest_blank_context_available_not_sidewall_specific_validation"
        ),
        "wet_wall_interaction": "wet_surface_evidence_contract_defined_no_wet_validation",
    }
    for lane, status in expected.items():
        assert {
            row["current_status"] for row in rows if row["evidence_lane"] == lane
        } == {status}


def test_formal_qch_refresh_delta_rows_keep_claims_false() -> None:
    deltas = builder.build_payload()["refresh_delta_rows"]

    assert len(deltas) == 4
    assert {delta["evidence_lane"] for delta in deltas} == {
        "flow_split_qch",
        "pressure_flow_validation",
    }
    for delta in deltas:
        assert delta["target_claim_current"] == "false"
        assert "route_score" in delta["blocked_use"]
        assert "yield" in delta["blocked_use"]
        assert "detection_probability" in delta["blocked_use"]
        assert delta["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_sidewall_integrated_promotion_ledger_formal_qch_refresh_outputs_manifest(
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
        "544_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_FORMAL_QCH_REFRESH_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
