from __future__ import annotations

from pathlib import Path

from tools.audits import (
    build_nodi_package_c_sidewall_authorization_execution_policy_ledger as builder,
)


def test_authorization_execution_policy_packet_builds_from_current_artifacts() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)

    assert failures == []
    summary = payload["summary"]
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["policy_rows"] == 8
    assert summary["claim_guard_rows"] == 8
    assert summary["authorized_prepare_rows"] == 8
    assert summary["authorized_execute_when_packet_passes_rows"] == 8
    assert summary["runtime_smoke_packet_passed_rows"] == 1
    assert summary["nodi_runtime_recomputation_allowed_rows"] == 1
    assert summary["comsol_launch_allowed_rows"] == 0
    assert summary["mph_load_allowed_rows"] == 0
    assert summary["sidewall_prs_eas_numeric_allowed_rows"] == 0
    assert summary["claim_promotion_allowed_policy_rows"] == 0
    assert summary["claim_promotion_allowed_guard_rows"] == 0
    assert summary["wet_branch_rows"] == 1
    assert summary["route_decision_rows"] == 1


def test_policy_rows_authorize_execution_paths_without_claim_promotion() -> None:
    rows = builder.build_payload()["policy_rows"]

    assert len(rows) == 8
    assert {row["authorized_to_prepare"] for row in rows} == {True}
    assert {row["authorized_to_execute_when_packet_passes"] for row in rows} == {True}
    assert {row["claim_promoted_by_this_task"] for row in rows} == {False}
    assert {row["claim_promotion_allowed_now"] for row in rows} == {False}
    assert {row["comsol_launch_allowed_now"] for row in rows} == {False}
    assert {row["mph_load_allowed_now"] for row in rows} == {False}
    assert {row["sidewall_prs_eas_numeric_allowed_now"] for row in rows} == {False}
    assert {row["claim_boundary"] for row in rows} == {builder.CLAIM_BOUNDARY}


def test_runtime_and_route_rows_have_expected_state() -> None:
    rows = builder.build_payload()["policy_rows"]
    packet = next(row for row in rows if row["task_id"] == "runtime_substep_execution_packet")
    runtime = next(row for row in rows if row["task_id"] == "guarded_trajectory_smoke")
    route = next(row for row in rows if row["branch_id"] == "route_yield_detection_decision")
    wet = next(row for row in rows if row["branch_id"] == "wet_ev_evidence")

    assert packet["execution_packet_status"] == (
        "runtime_substep_execution_packet_passed_candidate_only"
    )
    assert packet["nodi_runtime_recomputation_allowed_now"] is False
    assert runtime["execution_packet_status"] == "runtime_smoke_executed_candidate_only"
    assert runtime["nodi_runtime_recomputation_allowed_now"] is True
    assert runtime["sidewall_prs_eas_numeric_allowed_now"] is False
    assert route["current_execution_state"] == (
        "blocked_until_detector_blank_wet_and_solver_evidence_pass"
    )
    assert route["route_readiness_dependency"] == (
        "missing:detector_blank_transfer;wet_observation"
    )
    assert wet["current_execution_state"] == (
        "authorized_to_prepare_wet_evidence_contract_observations_missing"
    )
    assert wet["route_readiness_dependency"] == "missing:wet_observation"


def test_claim_guard_rows_remain_false() -> None:
    rows = builder.build_payload()["claim_guard_rows"]

    assert len(rows) == 8
    assert {row["implementation_authorized"] for row in rows} == {True}
    assert {row["candidate_evidence_authorized"] for row in rows} == {True}
    assert {row["claim_promoted_current"] for row in rows} == {False}
    assert {row["claim_promotion_allowed_now"] for row in rows} == {False}
    assert {row["claim_boundary"] for row in rows} == {builder.CLAIM_BOUNDARY}


def test_authorization_execution_policy_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_POLICY_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_CLAIM_GUARD_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert (
        "555_NODI_PACKAGE_C_SIDEWALL_AUTHORIZATION_EXECUTION_POLICY_LEDGER_20260701.md"
        in names
    )
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names
