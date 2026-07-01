from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_integrated_promotion_ledger_route_policy_refresh as builder,
)


def test_sidewall_integrated_promotion_ledger_route_policy_refresh_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["refreshed_promotion_lane_rows"] == 18
    assert summary["route_policy_delta_rows"] == 2
    assert summary["route_policy_rows"] == 2
    assert summary["integrated_route_policy_defined_rows"] == 2
    assert summary["qch_grid_refined_lane_rows_retained"] == 2
    assert summary["selected_annulus_context_available_rows_retained"] == 2
    assert summary["detector_context_available_rows_retained"] == 2
    assert summary["blank_context_available_rows_retained"] == 2
    assert summary["wet_surface_contract_defined_rows_retained"] == 2
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False
    assert summary["wet_pass_probability_current"] is False


def test_route_policy_lane_refresh_preserves_claim_boundary() -> None:
    rows = [
        row
        for row in builder.build_payload()["refreshed_promotion_lane_rows"]
        if row["evidence_lane"] == "integrated_route_ledger"
    ]

    assert len(rows) == 2
    assert {row["source_disposition"] for row in rows} == {
        "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_READY_NOT_CLAIM_READY"
    }
    assert all(
        row["source_artifact"].endswith(
            "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_POLICY_ROWS_20260701.csv"
        )
        for row in rows
    )
    assert {row["current_status"] for row in rows} == {
        "route_yield_detection_policy_defined_not_ready_for_claims"
    }
    for row in rows:
        assert row["target_claim_current"] == "false"
        assert row["not_detection_probability"] == "true"
        assert row["not_route_score"] == "true"
        assert row["not_winner"] == "true"
        assert row["not_yield"] == "true"
        assert "formal qch/pressure validation" in row["next_required_evidence"]


def test_route_policy_refresh_retains_prior_lane_progress() -> None:
    rows = builder.build_payload()["refreshed_promotion_lane_rows"]

    expected = {
        "flow_split_qch": "w500_d900_grid_refined_split_candidate_absolute_q_requires_validation",
        "selected_annulus_detection_context": "selected_annulus_context_available_small_n_not_probability",
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


def test_route_policy_delta_rows_keep_claims_false() -> None:
    deltas = builder.build_payload()["refresh_delta_rows"]

    assert len(deltas) == 2
    for delta in deltas:
        assert delta["evidence_lane"] == "integrated_route_ledger"
        assert delta["target_claim_current"] == "false"
        assert "route_score" in delta["blocked_use"]
        assert "yield" in delta["blocked_use"]
        assert "detection_probability" in delta["blocked_use"]
        assert delta["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_sidewall_integrated_promotion_ledger_route_policy_refresh_outputs_manifest(
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
        "540_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_ROUTE_POLICY_REFRESH_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
