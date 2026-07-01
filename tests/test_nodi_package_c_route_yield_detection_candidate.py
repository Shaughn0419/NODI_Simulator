from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_route_yield_detection_candidate as builder


def test_route_yield_detection_candidate_packet_builds_without_final_claims() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["source_qch_sidecar_disposition"] == (
        "NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_READY_NOT_ROUTE"
    )
    assert summary["source_pressure_flow_disposition"] == (
        "NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_READY_NOT_FORMAL_QCH"
    )
    assert summary["route_candidate_rows"] >= 2
    assert summary["candidate_metric_rows"] >= 2
    assert summary["route_score_current"] is False
    assert summary["winner_current"] is False
    assert summary["JRC_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False


def test_route_candidate_rows_have_metrics_and_explicit_gaps() -> None:
    rows = builder.build_payload()["route_candidate_rows"]

    assert rows
    assert rows[0]["candidate_sort_index_under_context"] == "1"
    for row in rows:
        assert float(row["route_decision_candidate_metric"]) > 0.0
        assert row["wet_evidence_status"] == "wet_ev_evidence_contract_missing"
        assert row["optical_detection_status"] == "optical_detection_calibration_missing"
        assert row["route_score_current"] == "false"
        assert row["winner_current"] == "false"
        assert row["JRC_current"] == "false"
        assert row["yield_current"] == "false"
        assert row["detection_probability_current"] == "false"
        assert row["claim_boundary"] == builder.ROUTE_YIELD_DETECTION_CLAIM_BOUNDARY


def test_evidence_gaps_bind_wet_optical_route_claims() -> None:
    gaps = builder.evidence_gap_rows()
    targets = {row["target"] for row in gaps}

    assert "formal_route_score" in targets
    assert "winner_or_JRC" in targets
    assert "yield" in targets
    assert "detection_probability" in targets
    for row in gaps:
        assert row["candidate_metric_available"] == "true"
        assert row["current_value"] == "false"
        assert row["hard_fail_if"].endswith("_true_from_candidate_metric_only")


def test_route_yield_detection_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_ROUTE_CANDIDATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_EVIDENCE_GAPS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "524_NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
