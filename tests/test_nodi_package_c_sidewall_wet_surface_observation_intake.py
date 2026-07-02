from __future__ import annotations

from pathlib import Path

from tools.audits import build_nodi_package_c_sidewall_wet_surface_observation_intake as builder


def test_wet_surface_observation_intake_packet_builds() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.ACCEPTED_DISPOSITION
    assert summary["intake_rows"] == 14
    assert summary["route_observation_matrix_rows"] == 2
    assert summary["template_rows"] == 14
    assert summary["promotion_update_rows"] == 1
    assert summary["accepted_observation_rows"] == 14
    assert summary["accepted_observation_matrix_rows"] == 2
    assert summary["wet_pass_probability_current"] is False
    assert summary["clogging_rate_current"] is False
    assert summary["time_to_clog_current"] is False
    assert summary["recovery_current"] is False
    assert summary["yield_current"] is False
    assert summary["detection_probability_current"] is False
    assert summary["route_score_current"] is False


def test_wet_surface_observation_intake_rows_are_missing_not_claims() -> None:
    rows = builder.build_payload()["intake_rows"]

    assert len(rows) == 14
    assert {row["route_candidate_id"] for row in rows} == {
        "ROUTE-CAND-001",
        "ROUTE-CAND-002",
    }
    for row in rows:
        assert row["observation_validation_status"] == (
            "wet_observation_accepted_candidate_not_route_or_detection_claim"
        )
        assert row["accepted_observation_current"] == "true"
        assert row["target_claim_current"] == "false"
        assert row["yield_current"] == "false"
        assert row["detection_probability_current"] == "false"
        assert row["route_score_current"] == "false"
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_wet_surface_route_matrix_is_accepted_simulation_bundle() -> None:
    rows = builder.build_payload()["route_observation_matrix_rows"]

    assert len(rows) == 2
    for row in rows:
        assert row["route_wet_observation_matrix_status"] == (
            "wet_surface_observation_bundle_candidate_ready_requires_policy_review"
        )
        assert row["accepted_endpoint_count"] == "7"
        assert row["missing_endpoint_count"] == "0"
        assert row["yield_current"] == "false"
        assert row["wet_pass_probability_current"] == "false"
        assert row["detection_probability_current"] == "false"


def test_wet_surface_observation_template_and_promotion_update_are_safe() -> None:
    payload = builder.build_payload()
    templates = payload["observation_template_rows"]
    updates = payload["promotion_update_rows"]

    assert len(templates) == 14
    assert {row["observation_artifact_id"] for row in templates} == {""}
    assert len(updates) == 1
    update = updates[0]
    assert update["target_ledger_lane"] == "wet_wall_interaction"
    assert update["target_claim_current"] == "false"
    assert "yield" in update["blocked_promotion"]
    assert "wet_pass_probability" in update["blocked_promotion"]
    assert "detection_probability" in update["blocked_promotion"]
    assert update["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_wet_surface_observation_intake_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_INTAKE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_ROUTE_OBSERVATION_MATRIX_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_OBSERVATION_TEMPLATE_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "543_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
