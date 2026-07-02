from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_yield_detection_claim_value_review as builder,
)


def test_yield_detection_claim_value_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["claim_value_rows"] == 2
    assert summary["guard_rows"] == 6
    assert summary["detection_template_rows"] == 2
    assert summary["yield_template_rows"] == 2
    assert summary["detection_input_present"] is True
    assert summary["yield_input_present"] is True
    assert summary["detection_probability_current_rows"] == 0
    assert summary["yield_current_rows"] == 0
    assert summary["wet_pass_probability_current_rows"] == 0
    assert summary["detection_probability_simulation_candidate_rows"] == 0
    assert summary["yield_simulation_candidate_rows"] == 0
    assert summary["wet_pass_probability_simulation_candidate_rows"] == 0
    assert summary["final_claim_current_rows"] == 0
    assert summary["production_ingestion_current_rows"] == 0


def test_claim_value_rows_block_current_claims_without_simulation_inputs() -> None:
    rows = builder.build_payload()["claim_value_rows"]

    assert {row["route_candidate_id"] for row in rows} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    for row in rows:
        assert row["detection_value_row_present"] is False
        assert row["yield_value_row_present"] is False
        assert row["detection_probability_current"] is False
        assert row["yield_current"] is False
        assert row["wet_pass_probability_current"] is False
        assert row["detection_probability_simulation_candidate_current"] is False
        assert row["yield_simulation_candidate_current"] is False
        assert row["wet_pass_probability_simulation_candidate_current"] is False
        assert row["claim_value_review_status"] == (
            "blocked_until_simulation_detection_and_yield_value_rows_accepted"
        )
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_claim_value_review_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_CLAIM_VALUE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_DETECTION_VALUE_TEMPLATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_YIELD_VALUE_TEMPLATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_INPUT_CONTRACT_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert f"576_{builder.PREFIX}_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
