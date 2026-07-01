from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_sidewall_wet_surface_contract as builder


def test_sidewall_wet_surface_contract_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["contract_rows"] == 14
    assert summary["route_candidate_rows"] == 2
    assert summary["endpoint_rows_per_route"] == 7
    assert summary["promotion_update_rows"] == 1
    assert summary["target_claim_false_rows"] == 14
    assert summary["wet_pass_probability_current"] is False
    assert summary["clogging_rate_current"] is False
    assert summary["time_to_clog_current"] is False
    assert summary["recovery_current"] is False
    assert summary["yield_current"] is False
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False
    assert summary["detection_probability_current"] is False


def test_wet_surface_contract_rows_cover_required_endpoints() -> None:
    rows = builder.build_payload()["contract_rows"]

    assert {row["route_candidate_id"] for row in rows} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    assert {row["endpoint_id"] for row in rows} == {
        endpoint["endpoint_id"] for endpoint in builder.WET_SURFACE_ENDPOINTS
    }
    for row in rows:
        assert row["contract_status"] == "wet_surface_contract_defined_no_wet_validation"
        assert row["target_claim_current"] is False
        assert row["required_artifact_class"]
        assert row["required_fields"]
        assert row["minimum_controls"]
        assert row["acceptance_basis"]
        assert row["hard_fail_if_missing"]
        assert row["not_wet_pass_probability"] is True
        assert row["not_clogging_rate"] is True
        assert row["not_time_to_clog"] is True
        assert row["not_recovery"] is True
        assert row["not_yield"] is True
        assert row["not_detection_probability"] is True


def test_wet_surface_promotion_update_is_context_only() -> None:
    updates = builder.build_payload()["promotion_update_rows"]

    assert len(updates) == 1
    update = updates[0]
    assert update["target_ledger_lane"] == "wet_wall_interaction"
    assert update["new_context_status"] == (
        "wet_surface_evidence_contract_defined_no_wet_validation"
    )
    assert update["target_claim_current"] == "false"
    assert "wet_pass_probability" in update["blocked_promotion"]
    assert "clogging_rate" in update["blocked_promotion"]
    assert "time_to_clog" in update["blocked_promotion"]
    assert "recovery" in update["blocked_promotion"]
    assert "yield" in update["blocked_promotion"]
    assert "detection_probability" in update["blocked_promotion"]
    assert update["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_sidewall_wet_surface_contract_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_CONTRACT_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "537_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
