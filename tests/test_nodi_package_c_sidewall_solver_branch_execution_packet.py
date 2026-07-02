from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from tools.audits import (
    build_nodi_package_c_sidewall_solver_branch_execution_packet as builder,
)


def test_solver_branch_execution_packet_builds_from_current_artifacts() -> None:
    payload = builder.build_payload()
    failures = builder.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == builder.DISPOSITION
    assert summary["branch_rows"] == 6
    assert summary["claim_guard_rows"] == 8
    assert summary["authorized_prepare_rows"] == 6
    assert summary["authorized_execute_when_packet_passes_rows"] == 6
    assert summary["candidate_evidence_current_rows"] >= 4
    assert summary["flow_candidate_rows"] == 1
    assert summary["electrokinetic_preflight_rows"] == 1
    assert summary["optical_candidate_rows"] == 1
    assert summary["wet_context_rows"] == 1
    assert summary["route_decision_rows"] == 1
    assert summary["final_solver_claim_current_rows"] == 0
    assert summary["q_ch_weighting_current_rows"] == 0
    assert summary["route_score_current_rows"] == 0
    assert summary["yield_current_rows"] == 0
    assert summary["detection_probability_current_rows"] == 0
    assert summary["comsol_launch_allowed_rows"] == 0
    assert summary["mph_load_allowed_rows"] == 0


def test_branch_rows_prioritize_existing_solver_and_context_evidence() -> None:
    rows = builder.build_payload()["branch_rows"]
    by_branch = {row["branch_id"]: row for row in rows}

    assert by_branch["trapezoid_flow_solver"]["candidate_evidence_current"] is True
    assert by_branch["trapezoid_flow_solver"]["candidate_output_rows"] >= 2
    assert by_branch["electrokinetic_solver"]["candidate_evidence_current"] is False
    assert by_branch["electrokinetic_solver"]["execution_packet_status"] == (
        "electrokinetic_grid_packet_required"
    )
    assert by_branch["optical_reference_solver"]["candidate_evidence_current"] is True
    assert by_branch["wet_optical_detection_evidence"]["candidate_evidence_current"] is True
    assert by_branch["route_yield_detection_decision"]["blocked_rows"] >= 4


def test_branch_rows_do_not_allow_final_claims_or_comsol_launch() -> None:
    rows = builder.build_payload()["branch_rows"]

    assert {row["authorized_to_prepare"] for row in rows} == {True}
    assert {row["final_solver_claim_current"] for row in rows} == {False}
    assert {row["q_ch_weighting_current"] for row in rows} == {False}
    assert {row["route_score_current"] for row in rows} == {False}
    assert {row["winner_current"] for row in rows} == {False}
    assert {row["yield_current"] for row in rows} == {False}
    assert {row["detection_probability_current"] for row in rows} == {False}
    assert {row["comsol_launch_allowed_now"] for row in rows} == {False}
    assert {row["mph_load_allowed_now"] for row in rows} == {False}
    assert {row["claim_boundary"] for row in rows} == {builder.CLAIM_BOUNDARY}


def test_claim_guard_rows_require_branch_packets_before_promotion() -> None:
    rows = builder.build_payload()["claim_guard_rows"]
    by_target = {row["promotion_target"]: row for row in rows}

    for target in [
        "final_trapezoid_flow_solver_claim",
        "formal_q_ch_weighting",
        "electrokinetic_solver_claim",
        "true_W_eff_and_detector_response",
        "detection_probability",
        "wet_pass_yield_recovery",
        "route_score_winner_JRC",
        "fabrication_or_production_release",
    ]:
        row = by_target[target]
        assert row["implementation_authorized"] is True
        assert row["claim_promoted_current"] is False
        assert row["claim_promotion_allowed_now"] is False
        assert row["required_evidence_before_true"]
        assert row["hard_fail_if_missing_evidence"]
        assert row["claim_boundary"] == builder.CLAIM_BOUNDARY


def test_solver_branch_execution_packet_outputs_manifest(tmp_path: Path) -> None:
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
    assert f"{builder.PREFIX}_BRANCH_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_CLAIM_GUARD_ROWS_20260701.csv" in names
    assert f"{builder.PREFIX}_STATUS_20260701.json" in names
    assert "556_NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_20260701.md" in names
    assert f"{builder.PREFIX}_MANIFEST_20260701.csv" in names


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_sidewall_solver_branch_execution_packet.py",
        ],
        cwd=builder.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-solver-branch-execution-packet is required" in result.stderr
