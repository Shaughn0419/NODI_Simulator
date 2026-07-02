from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_route_decision_execution_readiness as builder,
)


def test_route_decision_execution_readiness_builds_from_current_artifacts() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]
    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["readiness_rows"] == 2
    assert summary["claim_guard_rows"] == 5
    assert summary["route_geometry_families"] == "ideal_rectangle;trapezoid_tapered_sidewalls"
    assert summary["detector_accepted_transfer_rows_total"] == 4
    assert summary["wet_accepted_observation_rows_total"] == 0
    assert summary["route_formula_component_vector_ready_rows"] == 0
    assert summary["route_score_candidate_ready_rows"] == 0
    assert summary["winner_jrc_candidate_ready_rows"] == 0
    assert summary["yield_detection_values_ready_rows"] == 0
    assert summary["route_score_current_rows"] == 0
    assert summary["JRC_current_rows"] == 0
    assert summary["yield_current_rows"] == 0
    assert summary["detection_probability_current_rows"] == 0
    assert summary["wet_pass_probability_current_rows"] == 0
    assert summary["production_ingestion_current_rows"] == 0


def test_route_rows_keep_claims_false_and_geometry_parallel() -> None:
    rows = builder.build_payload()["readiness_rows"]
    assert {row["route_geometry_family"] for row in rows} == {
        "ideal_rectangle",
        "trapezoid_tapered_sidewalls",
    }
    for row in rows:
        assert row["rectangle_baseline_preserved"] is True
        assert row["sidewall_trapezoid_route_present"] is True
        assert row["execution_readiness_status"] == (
            "blocked_detector_blank_and_wet_observation_evidence_required"
        )
        assert row["route_formula_component_vector_ready"] is False
        assert row["route_formula_policy_review_status"] == (
            "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_READY_WAITING_FOR_SIMULATION_ACCEPTED_EVIDENCE"
        )
        assert row["route_score_candidate_ready"] is False
        assert row["winner_jrc_policy_review_status"] == (
            "NODI_PACKAGE_C_SIDEWALL_WINNER_JRC_POLICY_REVIEW_READY_WAITING_FOR_CURRENT_ROUTE_SCORES"
        )
        assert row["winner_jrc_candidate_ready"] is False
        assert row["yield_detection_claim_value_review_status"] == (
            "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_READY_AWAITING_SIMULATION_VALUE_ROWS"
        )
        assert row["yield_detection_values_ready"] is False
        assert row["route_score_current"] is False
        assert row["JRC_current"] is False
        assert row["yield_current"] is False
        assert row["detection_probability_current"] is False
        assert row["wet_pass_probability_current"] is False
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_route_decision_execution_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_READINESS_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_CLAIM_GUARD_ROWS_20260701.csv" in names
    assert "561_NODI_PACKAGE_C_SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_20260701.md" in names


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_route_decision_execution_readiness.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "--confirm-sidewall-route-decision-execution-readiness is required" in result.stderr
