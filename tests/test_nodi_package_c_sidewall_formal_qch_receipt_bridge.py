from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_sidewall_formal_qch_receipt_bridge as builder


def test_formal_qch_receipt_bridge_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["bridge_rows"] == 2
    assert summary["bridge_delta_rows"] == 2
    assert summary["firewall_rows"] == 6
    assert summary["closed_geometry_control_rows"] == 1
    assert summary["route_geometry_families"] == (
        "ideal_rectangle;trapezoid_tapered_sidewalls"
    )
    assert summary["formal_qch_sidecar_current_rows"] == 2
    assert summary["formal_qch_weighting_current_rows"] == 0
    assert summary["q_ch_weighting_current_rows"] == 0
    assert summary["route_score_current_rows"] == 0
    assert summary["winner_current_rows"] == 0
    assert summary["yield_current_rows"] == 0
    assert summary["detection_probability_current_rows"] == 0
    assert summary["next_executable_branches"] == (
        "sidewall_detector_blank_transfer_validation"
    )


def test_bridge_rows_reconcile_formal_qch_receipts_without_route_score() -> None:
    rows = builder.build_payload()["bridge_rows"]

    assert {row["route_candidate_id"] for row in rows} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    by_family = {row["route_geometry_family"]: row for row in rows}
    assert set(by_family) == {"ideal_rectangle", "trapezoid_tapered_sidewalls"}
    assert by_family["ideal_rectangle"]["q_ch_m3_s"] == 1.262945597388e-16
    assert by_family["trapezoid_tapered_sidewalls"]["q_ch_m3_s"] == 8.116618123938e-17
    assert by_family["ideal_rectangle"]["formal_flow_split_fraction"] == (
        0.6087636588171794
    )
    assert by_family["trapezoid_tapered_sidewalls"]["formal_flow_split_fraction"] == (
        0.39123634118282063
    )
    for row in rows:
        assert row["candidate_solver_status"] == "candidate_solver_output"
        assert row["source_match_status"] == "exact_request_and_geometry_match"
        assert row["quality_gate"] == "pass"
        assert row["per_route_acceptance_status"] == (
            "accepted_exact_pressure_flow_for_formal_qch_sidecar"
        )
        assert row["formal_qch_sidecar_current"] is True
        assert row["formal_qch_weighting_current"] is False
        assert row["q_ch_weighting_current"] is False
        assert row["route_score_current"] is False
        assert row["winner_current"] is False
        assert row["yield_current"] is False
        assert row["detection_probability_current"] is False
        assert row["assembly_next_executable_branch"] == (
            "sidewall_detector_blank_transfer_validation"
        )
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_formal_qch_receipt_bridge_firewall_rows_block_claim_promotion() -> None:
    rows = builder.build_payload()["firewall_rows"]

    assert {row["target"] for row in rows} == {
        "detection_probability",
        "production_ingestion",
        "q_ch_weighting",
        "route_score",
        "winner",
        "yield",
    }
    for row in rows:
        assert row["formal_qch_sidecar_available"] == "true"
        assert row["current_value"] == "false"
        assert row["required_before_true"]
        assert row["hard_fail_if"].endswith("_true_from_formal_qch_receipt_alone")
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_formal_qch_receipt_bridge_delta_rows_keep_next_branch() -> None:
    rows = builder.build_payload()["bridge_delta_rows"]

    assert len(rows) == 2
    for row in rows:
        assert row["flow_split_qch_status"] == (
            "formal_qch_sidecar_accepted_exact_pressure_flow_not_route_weighting"
        )
        assert row["pressure_flow_validation_status"] == (
            "exact_w500_d900_pressure_flow_result_accepted_formal_qch_sidecar_ready"
        )
        assert row["next_executable_branch"] == (
            "sidewall_detector_blank_transfer_validation"
        )
        assert row["target_claim_current"] is False
        assert row["route_score_current"] is False
        assert row["yield_current"] is False
        assert row["detection_probability_current"] is False


def test_formal_qch_receipt_bridge_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_BRIDGE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_ASSEMBLY_DELTA_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_FIREWALL_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert (
        "552_NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
