from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_wet_surface_observation_validation_hardening as builder,
)


def test_wet_surface_observation_validation_hardening_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["accepted_fixture_rows"] == 14
    assert summary["negative_control_rows"] == 4
    assert summary["current_intake_audit_rows"] == 2
    assert summary["current_no_observation_rows"] == 2
    assert summary["fixture_target_claim_current_rows"] == 0
    assert summary["fixture_yield_current_rows"] == 0
    assert summary["fixture_wet_pass_probability_current_rows"] == 0
    assert summary["fixture_route_score_current_rows"] == 0


def test_accepted_wet_fixtures_are_candidates_not_current_claims() -> None:
    rows = builder.build_payload()["accepted_fixture_rows"]

    assert {row["route_candidate_id"] for row in rows} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    assert {row["observation_validation_status"] for row in rows} == {
        "wet_observation_accepted_candidate_not_route_or_detection_claim"
    }
    assert {row["observation_rejection_reason"] for row in rows} == {
        "accepted_observation_candidate"
    }
    assert {row["route_wet_observation_matrix_status"] for row in rows} == {
        "wet_surface_observation_bundle_candidate_ready_requires_policy_review"
    }
    for row in rows:
        assert row["accepted_observation_current"] is True
        assert row["target_claim_current"] is False
        assert row["wet_pass_probability_current"] is False
        assert row["yield_current"] is False
        assert row["detection_probability_current"] is False
        assert row["route_score_current"] is False
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_wet_negative_controls_fail_closed_with_specific_reasons() -> None:
    rows = builder.build_payload()["negative_control_rows"]

    assert {row["negative_control_id"] for row in rows} == {
        "bad_sha",
        "controls_missing",
        "low_replicate_count",
        "missing_fields",
    }
    assert {row["observation_rejection_reason"] for row in rows} == {
        "controls_not_pass",
        "insufficient_replicate_count",
        "invalid_observation_source_sha256",
        "missing_required_fields",
    }
    assert {row["observation_validation_status"] for row in rows} == {
        "wet_observation_rejected_missing_required_evidence"
    }
    assert {row["route_wet_observation_matrix_status"] for row in rows} == {
        "wet_surface_observation_intake_partial_observations_not_claim_ready"
    }
    for row in rows:
        assert row["accepted_observation_current"] is False
        assert row["target_claim_current"] is False
        assert row["yield_current"] is False
        assert row["wet_pass_probability_current"] is False
        assert row["route_score_current"] is False


def test_current_wet_surface_audit_remains_no_observation() -> None:
    rows = builder.build_payload()["current_intake_audit_rows"]

    assert len(rows) == 2
    assert {row["route_wet_observation_matrix_status"] for row in rows} == {
        "wet_surface_observation_intake_ready_no_observations"
    }
    assert {row["accepted_endpoint_count"] for row in rows} == {"0"}
    assert {row["yield_current"] for row in rows} == {"false"}
    assert {row["wet_pass_probability_current"] for row in rows} == {"false"}
    assert {row["detection_probability_current"] for row in rows} == {"false"}
    assert {row["route_score_current"] for row in rows} == {"false"}


def test_wet_surface_observation_validation_hardening_outputs_manifest(
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
        "553_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
