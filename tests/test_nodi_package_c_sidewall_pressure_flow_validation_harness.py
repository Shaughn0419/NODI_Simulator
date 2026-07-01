from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_sidewall_pressure_flow_validation_harness as builder


def test_sidewall_pressure_flow_validation_harness_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["validation_request_rows"] == 2
    assert summary["closed_geometry_control_rows"] == 1
    assert summary["promotion_update_rows"] == 1
    assert summary["exact_w500_d900_route_requests"] == 2
    assert summary["formal_qch_weighting_current"] is False
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False
    assert summary["comsol_launch_started"] is False
    assert summary["mph_load_started"] is False


def test_validation_request_rows_are_exact_w500_d900_execution_inputs() -> None:
    rows = builder.build_payload()["validation_request_rows"]

    assert {row["route_candidate_id"] for row in rows} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    for row in rows:
        assert row["top_width_nm"] == 500.0
        assert row["depth_nm"] == 900.0
        assert row["reference_grid_nx"] == 41
        assert row["candidate_q_grid_m3_s"] > 0.0
        assert row["candidate_flow_split_fraction"] > 0.0
        assert "q_total_m3_s" in row["required_observables"]
        assert "geometry_descriptor_sha256" in row["required_metadata"]
        assert row["validation_status"] == (
            "exact_w500_d900_validation_harness_ready_missing_external_result"
        )
        assert row["formal_qch_weighting_current"] is False
        assert row["route_score_current"] is False
        assert row["detection_probability_current"] is False
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_closed_geometry_control_prevents_qch_for_closed70() -> None:
    rows = builder.build_payload()["closed_geometry_control_rows"]

    assert len(rows) == 1
    row = rows[0]
    assert row["case_id"] == "closed_theta70_D900_W500"
    assert row["control_status"] == "closed_geometry_control_must_remain_blocked"
    assert row["required_behavior"] == "no pressure-flow validation request and no qch sidecar"
    assert row["hard_fail_if"] == "closed_geometry_enters_formal_qch_or_route_score"


def test_pressure_flow_validation_promotion_update_is_not_formal_qch() -> None:
    updates = builder.build_payload()["promotion_update_rows"]

    assert len(updates) == 1
    update = updates[0]
    assert update["target_ledger_lane"] == "pressure_flow_validation"
    assert update["new_context_status"] == (
        "exact_w500_d900_pressure_flow_validation_harness_ready_missing_external_result"
    )
    assert update["target_claim_current"] == "false"
    assert "formal_qch_weighting" in update["blocked_promotion"]
    assert "route_score" in update["blocked_promotion"]
    assert "detection_probability" in update["blocked_promotion"]
    assert update["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_sidewall_pressure_flow_validation_harness_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_REQUEST_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_CONTROL_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "541_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
