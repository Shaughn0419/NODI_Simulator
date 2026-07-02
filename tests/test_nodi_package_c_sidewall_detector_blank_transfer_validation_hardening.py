from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_detector_blank_transfer_validation_hardening as builder,
)


def test_detector_blank_transfer_validation_hardening_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["accepted_fixture_rows"] == 2
    assert summary["negative_control_rows"] == 4
    assert summary["current_intake_audit_rows"] == 2
    assert summary["current_no_transfer_rows"] == 0
    assert summary["current_accepted_transfer_rows"] == 2
    assert summary["fixture_detection_probability_current_rows"] == 0
    assert summary["fixture_route_score_current_rows"] == 0


def test_accepted_fixtures_are_transfer_candidates_not_probability() -> None:
    rows = builder.build_payload()["accepted_fixture_rows"]

    assert {row["route_candidate_id"] for row in rows} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    assert {row["geometry_match_level"] for row in rows} == {
        "sidewall_specific",
        "validated_transfer",
    }
    assert {row["transfer_validation_status"] for row in rows} == {
        "detector_blank_transfer_accepted_candidate_not_detection_probability"
    }
    assert {row["transfer_rejection_reason"] for row in rows} == {
        "accepted_transfer_candidate"
    }
    assert {row["route_transfer_matrix_status"] for row in rows} == {
        "detector_blank_transfer_bundle_candidate_ready_requires_policy_review"
    }
    for row in rows:
        assert row["accepted_transfer_current"] is True
        assert row["detection_probability_current"] is False
        assert row["route_score_current"] is False
        assert row["yield_current"] is False
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_negative_controls_fail_closed_with_specific_reasons() -> None:
    rows = builder.build_payload()["negative_control_rows"]

    assert {row["negative_control_id"] for row in rows} == {
        "bad_blank_sha",
        "bad_fpr_ci_order",
        "controls_missing",
        "low_blank_trace_count",
    }
    assert {row["transfer_rejection_reason"] for row in rows} == {
        "controls_not_pass",
        "insufficient_blank_trace_count",
        "invalid_blank_trace_sha256",
        "invalid_false_positive_ci_order",
    }
    assert {row["transfer_validation_status"] for row in rows} == {
        "detector_blank_transfer_rejected_missing_required_evidence"
    }
    assert {row["route_transfer_matrix_status"] for row in rows} == {
        "detector_blank_transfer_intake_ready_no_transfer_evidence"
    }
    for row in rows:
        assert row["accepted_transfer_current"] is False
        assert row["detection_probability_current"] is False
        assert row["route_score_current"] is False


def test_current_transfer_audit_accepts_nodi_candidate_without_probability() -> None:
    rows = builder.build_payload()["current_intake_audit_rows"]

    assert len(rows) == 2
    assert {row["route_transfer_matrix_status"] for row in rows} == {
        "detector_blank_transfer_bundle_candidate_ready_requires_policy_review"
    }
    assert {row["accepted_transfer_count"] for row in rows} == {"1"}
    assert {row["detection_probability_current"] for row in rows} == {"False"}
    assert {row["route_score_current"] for row in rows} == {"False"}


def test_detector_blank_transfer_validation_hardening_outputs_manifest(
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
    assert f"{builder.PREFIX}_ACCEPTED_FIXTURE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_NEGATIVE_CONTROL_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_CURRENT_INTAKE_AUDIT_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert (
        "551_NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_VALIDATION_HARDENING_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
