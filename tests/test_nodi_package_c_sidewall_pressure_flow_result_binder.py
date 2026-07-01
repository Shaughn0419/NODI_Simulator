from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_sidewall_pressure_flow_result_binder as builder


def test_sidewall_pressure_flow_result_binder_packet_builds_current_ready_state() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION_FORMAL_READY
    assert summary["request_rows"] == 2
    assert summary["closed_geometry_control_rows"] == 1
    assert summary["external_result_input_present"] is True
    assert summary["external_result_rows"] == 2
    assert summary["external_result_template_rows"] == 2
    assert summary["binding_rows"] == 2
    assert summary["accepted_exact_pressure_flow_binding_rows"] == 2
    assert summary["missing_external_result_binding_rows"] == 0
    assert summary["formal_qch_sidecar_rows"] == 2
    assert summary["formal_qch_sidecar_current"] is True
    assert summary["formal_qch_weighting_current"] is False
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False
    assert summary["port_balance_threshold_max"] == 0.01
    assert summary["q_total_reconciliation_threshold_max"] == 0.05
    assert "sanity guard" in summary["acceptance_ratio_threshold_note"]


def test_sidewall_pressure_flow_result_binder_waits_when_external_result_missing(
    tmp_path: Path,
) -> None:
    old_external_result_rows = builder.OPTIONAL_EXTERNAL_RESULT_ROWS
    try:
        builder.OPTIONAL_EXTERNAL_RESULT_ROWS = tmp_path / "missing_external_result.csv"
        payload = builder.build_payload()
    finally:
        builder.OPTIONAL_EXTERNAL_RESULT_ROWS = old_external_result_rows

    failures = builder.validate_payload(payload)
    assert failures == []

    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION_WAITING
    assert summary["external_result_input_present"] is False
    assert summary["external_result_rows"] == 0
    assert summary["missing_external_result_binding_rows"] == 2
    assert summary["formal_qch_sidecar_rows"] == 0
    assert summary["formal_qch_sidecar_current"] is False


def test_sidewall_pressure_flow_result_binder_template_names_required_fields() -> None:
    rows = builder.build_payload()["external_result_template_rows"]

    assert len(rows) == 2
    for row in rows:
        assert row["external_result_status"] == "template_waiting_for_exact_external_result"
        assert "external_result_id" in row["required_external_result_fields"]
        assert "q_total_m3_s" in row["required_external_result_fields"]
        assert "quality_gate" in row["required_external_result_fields"]
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_sidewall_pressure_flow_result_binder_binding_rows_accept_exact_results() -> None:
    rows = builder.build_payload()["binding_rows"]

    assert len(rows) == 2
    for row in rows:
        assert row["per_route_acceptance_status"] == (
            "accepted_exact_pressure_flow_for_formal_qch_sidecar"
        )
        assert row["formal_qch_sidecar_current"] is True
        assert row["formal_qch_weighting_current"] is False
        assert row["route_score_current"] is False
        assert row["yield_current"] is False
        assert row["detection_probability_current"] is False
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_sidewall_pressure_flow_result_binder_promotion_update_accepts_qch_sidecar() -> None:
    rows = builder.build_payload()["promotion_update_rows"]

    assert len(rows) == 1
    row = rows[0]
    assert row["target_ledger_lane"] == "pressure_flow_validation"
    assert row["formal_qch_sidecar_current"] == "true"
    assert row["new_context_status"] == (
        "exact_w500_d900_pressure_flow_result_accepted_formal_qch_sidecar_ready"
    )
    assert row["target_claim_current"] == "false"
    assert "route policy plus calibrated detector/wet/yield evidence" in row[
        "next_required_evidence"
    ]
    assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_sidewall_pressure_flow_result_binder_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_EXTERNAL_RESULT_TEMPLATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_BINDING_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "543_NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
