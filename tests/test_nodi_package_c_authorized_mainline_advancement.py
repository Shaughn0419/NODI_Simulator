from __future__ import annotations

from functools import lru_cache
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_package_c_authorized_mainline_advancement as mainline


@lru_cache(maxsize=1)
def _payload() -> dict:
    return mainline.build_payload()


def test_authorized_mainline_packet_passes_and_keeps_proof_scope_narrow() -> None:
    payload = _payload()
    failures = mainline.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == mainline.DISPOSITION
    assert summary["package_c_proof_artifact_registered"] is True
    assert summary["package_c_validation_status_pass_current"] is True
    assert (
        summary["package_c_validation_status_pass_scope"]
        == "finite_step_reflection_surrogate_evidence_only"
    )
    assert summary["all_downstream_branches_authorized_to_implement"] is True
    assert summary["runtime_substep_next"] is True
    assert summary["release_scoped_dirty_blocker_rows"] == 0


def test_all_downstream_branches_are_authorized_without_final_claim_promotion() -> None:
    rows = _payload()["branch_roadmap"]
    branch_ids = {row["branch_id"] for row in rows}

    assert {
        "runtime_substep_execution",
        "trapezoid_flow_solver",
        "electrokinetic_solver",
        "optical_reference_solver",
        "wet_ev_evidence",
        "route_yield_detection_decision",
    } <= branch_ids
    assert {row["authorized_to_implement"] for row in rows} == {"true"}
    assert {row["evidence_generation_allowed"] for row in rows} == {"true"}
    assert {row["candidate_numeric_output_allowed_after_branch_packet"] for row in rows} == {
        "true"
    }
    assert {row["final_claim_promoted_current"] for row in rows} == {"false"}
    assert {row["current_runtime_or_solver_started"] for row in rows} == {"false"}


def test_execution_queue_prioritizes_runtime_but_keeps_solver_wet_route_in_mainline() -> None:
    rows = _payload()["execution_queue"]
    by_queue = {row["queue_id"]: row for row in rows}
    branch_ids = {row["branch_id"] for row in rows}

    assert by_queue["Q001"]["task_id"] == "runtime_substep_execution_packet"
    assert by_queue["Q002"]["task_id"] == "guarded_trajectory_smoke"
    assert {
        "trapezoid_flow_solver",
        "electrokinetic_solver",
        "optical_reference_solver",
        "wet_ev_evidence",
        "route_yield_detection_decision",
    } <= branch_ids
    assert {row["authorized_to_prepare"] for row in rows} == {"true"}
    assert {row["authorized_to_execute_when_packet_passes"] for row in rows} == {"true"}
    assert {row["claim_promoted_by_this_task"] for row in rows} == {"false"}


def test_promotion_contract_allows_implementation_but_requires_evidence_hashes() -> None:
    rows = _payload()["promotion_contract"]
    by_target = {row["promotion_target"]: row for row in rows}

    for target in [
        "runtime_result",
        "sidewall_prs_eas_numeric_output",
        "trapezoid_flow_solver_output",
        "electrokinetic_solver_output",
        "optical_solver_output",
        "wet_claim",
        "route_score_winner_JRC_qch",
        "yield_detection_probability",
    ]:
        row = by_target[target]
        assert row["implementation_authorized"] == "true"
        assert row["candidate_evidence_authorized"] == "true"
        assert row["claim_promoted_current"] == "false"
        assert row["required_evidence_before_claim_true"]
        assert row["hard_fail_if_missing_evidence"].endswith(
            "_claim_true_without_required_hashes"
        )


def test_current_result_fields_remain_unpromoted_while_branches_are_authorized() -> None:
    summary = _payload()["summary"]

    assert summary["solver_branches_authorized_to_prepare"] is True
    assert summary["wet_branch_authorized_to_prepare"] is True
    assert summary["route_yield_detection_branch_authorized_to_prepare"] is True
    for key in [
        "runtime_execution_started",
        "comsol_launch_started",
        "mph_load_started",
        "solver_output_current",
        "wet_claim_current",
        "route_yield_detection_claim_current",
        "final_claim_promotion_current",
    ]:
        assert summary[key] is False


def test_written_outputs_manifest_contains_mainline_artifacts(tmp_path) -> None:
    payload = _payload()
    outputs = mainline.write_outputs(
        payload,
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    artifacts = {path.name for path in outputs}

    assert "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_STATUS_20260701.json" in artifacts
    assert "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_BRANCH_ROADMAP_20260701.csv" in artifacts
    assert "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_EXECUTION_QUEUE_20260701.csv" in artifacts
    assert "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_PROMOTION_CONTRACT_20260701.csv" in artifacts
    assert "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_DIRTY_CONTEXT_20260701.csv" in artifacts
    assert "519_NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_20260701.md" in artifacts

    manifest_rows = read_csv_rows(
        tmp_path
        / "joint_interface"
        / "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_MANIFEST_20260701.csv"
    )
    by_artifact = {row["artifact"]: row for row in manifest_rows}
    assert by_artifact[
        "NODI_PACKAGE_C_AUTHORIZED_MAINLINE_ADVANCEMENT_MANIFEST_20260701.csv"
    ]["sha256"] == mainline.SELF_MANIFEST_SHA256


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_authorized_mainline_advancement.py",
        ],
        cwd=mainline.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-authorized-mainline-advancement is required" in result.stderr
