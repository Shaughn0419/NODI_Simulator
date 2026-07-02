from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_wet_observation_execution_packet as builder,
)


def test_wet_observation_execution_packet_builds_from_current_artifacts() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["execution_rows"] == 6
    assert summary["claim_guard_rows"] == 5
    assert summary["contract_or_fixture_rows_total"] > 0
    assert summary["current_accepted_observation_rows_total"] == 0
    assert summary["wet_pass_probability_current_rows"] == 0
    assert summary["clogging_rate_current_rows"] == 0
    assert summary["time_to_clog_current_rows"] == 0
    assert summary["recovery_current_rows"] == 0
    assert summary["yield_current_rows"] == 0
    assert summary["detection_probability_current_rows"] == 0
    assert summary["route_score_current_rows"] == 0
    assert summary["claim_promotion_allowed_guard_rows"] == 0


def test_execution_rows_keep_wet_assets_as_non_claim_evidence() -> None:
    rows = builder.build_payload()["execution_rows"]
    by_lane = {row["lane"]: row for row in rows}

    assert by_lane["wet_surface_contract"]["current_status"] == (
        "contract_ready_no_wet_validation"
    )
    assert by_lane["wet_observation_intake"]["current_status"] == (
        "intake_schema_ready_no_observations"
    )
    assert by_lane["validator_hardening"]["current_status"] == (
        "validator_ready_fixture_only_not_current_observations"
    )
    assert by_lane["route_readiness_blocker"]["current_status"] == (
        "route_readiness_secondary_blocker_still_wet_observation"
    )


def test_execution_rows_block_wet_yield_detection_and_route_claims() -> None:
    rows = builder.build_payload()["execution_rows"]

    assert {row["current_accepted_observation_rows"] for row in rows} == {0}
    assert {row["wet_pass_probability_current"] for row in rows} == {False}
    assert {row["yield_current"] for row in rows} == {False}
    assert {row["detection_probability_current"] for row in rows} == {False}
    assert {row["route_score_current"] for row in rows} == {False}
    assert {row["claim_boundary"] for row in rows} == {builder.CLAIM_BOUNDARY}


def test_claim_guards_require_real_wet_observations_before_promotion() -> None:
    rows = builder.build_payload()["claim_guard_rows"]

    assert len(rows) == 5
    for row in rows:
        assert row["implementation_authorized"] is True
        assert row["fixture_or_contract_available"] is True
        assert row["claim_promoted_current"] is False
        assert row["claim_promotion_allowed_now"] is False
        assert row["required_evidence_before_true"]
        assert row["hard_fail_if_missing_evidence"]
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_wet_observation_execution_outputs_manifest(tmp_path: Path) -> None:
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
    assert "560_NODI_PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_wet_observation_execution_packet.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-wet-observation-execution-packet is required" in result.stderr
