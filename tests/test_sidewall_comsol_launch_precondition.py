from __future__ import annotations

from nodi_simulator.sidewall_comsol_launch_precondition import (
    SIDEWALL_COMSOL_LAUNCH_PRECONDITION_CLAIM_BOUNDARY,
    build_comsol_launch_precondition,
)


def _solver_branch_rows() -> list[dict[str, object]]:
    return [
        {
            "branch_row_id": "SOLVER-BRANCH-comsol_clean_mirror_receipt",
            "branch_id": "comsol_clean_mirror_receipt",
            "user_authorization_status": "authorized",
            "authorized_to_prepare": True,
        },
        {
            "branch_row_id": "SOLVER-BRANCH-trapezoid_flow_solver",
            "branch_id": "trapezoid_flow_solver",
            "user_authorization_status": "authorized",
            "authorized_to_prepare": True,
        },
    ]


def _build():
    return build_comsol_launch_precondition(
        solver_branch_rows=_solver_branch_rows(),
        electrokinetic_preflight_status={
            "disposition": (
                "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_READY_PROFILE_GRID_REQUIRED"
            )
        },
        toolchain={
            "comsol_path": "C:/COMSOL/comsol.exe",
            "comsolbatch_path": "C:/COMSOL/comsolbatch.exe",
            "comsol_detected": True,
            "comsolbatch_detected": True,
            "version_check_passed": True,
            "version_text": "COMSOL Multiphysics 6.4.0.293",
        },
        comsol_project={
            "project_path": "C:/repo/comsol",
            "project_detected": True,
            "head": "abc",
            "head_bound": True,
            "dirty_summary": "dirty_rows=10",
        },
        mirror_request_rows=[
            {"target_nodi_commit": "old"},
            {"target_nodi_commit": "old"},
        ],
        nodi_current_head="new",
    )


def test_precondition_records_toolchain_but_not_launch() -> None:
    rows, contexts, guards = _build()

    assert len(rows) == 5
    assert len(contexts) == 4
    assert len(guards) == 6
    toolchain = next(row for row in rows if row.lane == "toolchain_detection")
    assert toolchain.precondition_passed is True
    assert toolchain.comsolbatch_executable_detected is True
    assert toolchain.version_check_passed is True
    assert {row.launch_allowed_now for row in rows} == {False}
    assert {row.mph_load_allowed_now for row in rows} == {False}


def test_target_model_and_command_hash_remain_required() -> None:
    rows, _contexts, _guards = _build()
    target = next(row for row in rows if row.lane == "target_model_binding")
    command = next(row for row in rows if row.lane == "launch_command_binding")

    assert target.precondition_passed is False
    assert target.target_mph_or_model_bound is False
    assert "target .mph" in target.next_required_evidence
    assert command.launch_command_hash_bound is False
    assert command.hard_fail_if == "comsolbatch_started_without_command_hash_and_output_manifest"


def test_legacy_mirror_request_is_stale_for_current_head() -> None:
    _rows, contexts, _guards = _build()
    legacy = next(row for row in contexts if row.context_kind == "legacy_mirror_request")

    assert legacy.context_status == "stale_for_current_head"
    assert legacy.observed_value == "old"
    assert legacy.target_nodi_commit == "new"
    assert "older NODI commit" in legacy.stale_or_missing_reason


def test_claim_guards_block_launch_solver_qch_route_and_wet_claims() -> None:
    rows, _contexts, guards = _build()

    assert {row.claim_boundary for row in rows} == {
        SIDEWALL_COMSOL_LAUNCH_PRECONDITION_CLAIM_BOUNDARY
    }
    targets = {row.promotion_target for row in guards}
    assert targets == {
        "comsol_launch",
        "mph_load",
        "pressure_flow_solver_claim",
        "electrokinetic_solver_claim",
        "formal_q_ch_or_route_score",
        "yield_detection_wet_or_production",
    }
    for guard in guards:
        assert guard.implementation_authorized is True
        assert guard.claim_promoted_current is False
        assert guard.claim_promotion_allowed_now is False
        assert guard.required_evidence_before_true
        assert guard.claim_boundary == SIDEWALL_COMSOL_LAUNCH_PRECONDITION_CLAIM_BOUNDARY
