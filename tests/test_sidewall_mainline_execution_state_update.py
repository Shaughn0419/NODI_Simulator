from __future__ import annotations

from nodi_simulator.sidewall_mainline_execution_state_update import (
    SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_CLAIM_BOUNDARY,
    build_mainline_execution_state_update,
)


def _work_order_rows() -> list[dict[str, object]]:
    lanes = [
        ("WO-001-current-head-source-lock", "source_lock_and_commit_binding"),
        ("WO-002-comsol-target-binding", "comsol_target_model_and_command_binding"),
        ("WO-003-electrokinetic-profile-grid", "electrokinetic_profile_aware_grid"),
        ("WO-004-detector-blank-transfer", "detector_blank_transfer_evidence"),
        ("WO-005-wet-observation", "wet_observation_evidence"),
        ("WO-006-route-yield-detection-formula-binding", "route_yield_detection_formula_binding"),
        ("WO-007-runtime-substep-policy", "reflection_runtime_substep_policy"),
        ("WO-008-mainline-integration-closeout", "mainline_integration_and_release_closeout"),
    ]
    return [
        {"work_order_id": work_order_id, "lane": lane, "current_blocker": "old blocker"}
        for work_order_id, lane in lanes
    ]


def _route_register() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for route_id, family in [
        ("ROUTE-CAND-001", "ideal_rectangle"),
        ("ROUTE-CAND-002", "trapezoid_tapered_sidewalls"),
    ]:
        for lane, evidence_class in [
            ("q_ch_route_input", "ready_route_input"),
            ("detector_blank_transfer", "fixture_or_context_available_no_accepted_claim_evidence"),
            ("wet_observation", "fixture_or_contract_available_no_accepted_claim_evidence"),
            ("electrokinetic_profile_grid", "preflight_requirement"),
            ("comsol_target_binding", "precondition_only"),
        ]:
            rows.append(
                {
                    "route_candidate_id": route_id,
                    "route_geometry_family": family,
                    "evidence_lane": lane,
                    "evidence_class": evidence_class,
                    "source_artifact_id": lane,
                    "source_disposition": "source",
                    "evidence_rows": 1,
                    "accepted_claim_evidence_rows": 0,
                    "hard_fail_if": "hard_fail",
                }
            )
    return rows


def _build():
    return build_mainline_execution_state_update(
        work_order_rows=_work_order_rows(),
        route_evidence_register_rows=_route_register(),
        runtime_status={
            "artifact_id": "RUNTIME",
            "disposition": "runtime_ready",
            "guarded_runtime_smoke_executed": True,
        },
        profile_grid_status={
            "artifact_id": "PROFILE",
            "disposition": "profile_ready",
            "profile_aware_grid_current_rows": 5,
        },
        flow_solver_status={
            "artifact_id": "FLOW",
            "disposition": "flow_candidate",
            "candidate_solver_output_rows": 2,
        },
        comsol_status={
            "artifact_id": "COMSOL",
            "disposition": "comsol_precondition",
            "precondition_rows": 5,
            "target_model_bound_rows": 0,
            "launch_command_hash_bound_rows": 0,
        },
        detector_status={
            "artifact_id": "DETECTOR",
            "disposition": "detector_ready",
            "current_accepted_transfer_rows_total": 0,
        },
        wet_status={
            "artifact_id": "WET",
            "disposition": "wet_ready",
            "current_accepted_observation_rows_total": 0,
        },
        route_status={
            "artifact_id": "ROUTE",
            "disposition": "route_ready",
            "readiness_rows": 2,
        },
    )


def test_state_update_integrates_profile_grid_and_runtime_smoke() -> None:
    work_rows, route_rows, guards = _build()
    assert len(work_rows) == 8
    assert len(route_rows) == 14
    assert len(guards) == 5
    assert sum(row.current_state == "candidate_profile_grid_available_not_solver" for row in work_rows) == 1
    assert sum(row.current_state == "guarded_runtime_smoke_available_stress_blocked" for row in work_rows) == 1
    assert {row.claim_activation_allowed_now for row in work_rows} == {False}
    assert {row.claim_boundary for row in work_rows} == {
        SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_CLAIM_BOUNDARY
    }


def test_route_evidence_update_keeps_candidate_evidence_out_of_claims() -> None:
    _work_rows, route_rows, guards = _build()
    assert sum(
        row.evidence_lane == "electrokinetic_profile_grid"
        and row.evidence_class == "candidate"
        for row in route_rows
    ) == 2
    assert sum(row.evidence_lane == "runtime_substep_guard" for row in route_rows) == 2
    assert sum(
        row.evidence_lane == "flow_solver_candidate" and row.evidence_class == "candidate"
        for row in route_rows
    ) == 1
    assert {row.may_satisfy_route_formula_now for row in route_rows} == {False}
    assert {row.may_satisfy_yield_now for row in route_rows} == {False}
    assert {row.may_satisfy_detection_now for row in route_rows} == {False}
    assert {row.activation_allowed_now for row in guards} == {False}
