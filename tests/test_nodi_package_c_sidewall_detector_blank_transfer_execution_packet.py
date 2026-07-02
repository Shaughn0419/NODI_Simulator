from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_detector_blank_transfer_execution_packet as builder,
)


def test_detector_blank_transfer_execution_packet_builds_from_current_artifacts() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["execution_rows"] == 5
    assert summary["claim_guard_rows"] == 5
    assert summary["candidate_or_fixture_rows_total"] > 0
    assert summary["current_accepted_transfer_rows_total"] == 2
    assert summary["sidewall_specific_blank_trace_current_rows"] == 0
    assert summary["detector_response_validation_current_rows"] == 1
    assert summary["validated_transfer_current_rows"] == 1
    assert summary["detection_probability_current_rows"] == 0
    assert summary["route_score_current_rows"] == 0
    assert summary["yield_current_rows"] == 0
    assert summary["claim_promotion_allowed_guard_rows"] == 0


def test_execution_rows_keep_fixtures_context_and_candidates_separate() -> None:
    rows = builder.build_payload()["execution_rows"]
    by_lane = {row["lane"]: row for row in rows}

    assert by_lane["transfer_intake"]["current_status"] == (
        "accepted_detector_blank_transfer_candidate_ready_not_probability"
    )
    assert by_lane["validator_hardening"]["current_status"] == (
        "validator_ready_fixture_only_not_current_transfer_evidence"
    )
    assert by_lane["calibration_panel"]["current_status"] == (
        "candidate_panel_ready_not_sidewall_blank_or_detector_response"
    )
    assert by_lane["route_readiness_blocker"]["current_status"] == (
        "route_readiness_primary_blocker_still_detector_blank_transfer"
    )


def test_execution_rows_block_detection_and_route_claims() -> None:
    rows = builder.build_payload()["execution_rows"]

    assert {row["current_accepted_transfer_rows"] for row in rows} == {0, 2}
    assert {row["detection_probability_current"] for row in rows} == {False}
    assert {row["route_score_current"] for row in rows} == {False}
    assert {row["yield_current"] for row in rows} == {False}
    assert {row["claim_boundary"] for row in rows} == {builder.CLAIM_BOUNDARY}


def test_claim_guards_require_real_or_validated_transfer_before_promotion() -> None:
    rows = builder.build_payload()["claim_guard_rows"]

    assert len(rows) == 5
    for row in rows:
        assert row["implementation_authorized"] is True
        assert row["fixture_or_context_available"] is True
        assert row["claim_promoted_current"] is False
        assert row["claim_promotion_allowed_now"] is False
        assert row["required_evidence_before_true"]
        assert row["hard_fail_if_missing_evidence"]
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_detector_blank_transfer_execution_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_EXECUTION_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_CLAIM_GUARD_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert (
        "559_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_detector_blank_transfer_execution_packet.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert (
        "--confirm-sidewall-detector-blank-transfer-execution-packet is required"
        in result.stderr
    )
