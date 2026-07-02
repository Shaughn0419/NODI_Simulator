from __future__ import annotations

from nodi_simulator.sidewall_comsol_target_binding_qch_integration import (
    SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_CLAIM_BOUNDARY,
    build_comsol_target_binding_qch_integration,
)


def _requests() -> list[dict[str, object]]:
    return [
        {
            "validation_request_id": "PFV-REQUEST-ROUTE-CAND-001",
            "route_candidate_id": "ROUTE-CAND-001",
            "qch_sidecar_id": "QCH-CAND-001",
            "case_id": "rectangle_limit_theta90_D900_W500",
            "source_geometry_hash": "a" * 64,
            "sidewall_deg_comsol": "90.0",
            "sidewall_taper_angle_deg_nodi": "0.0",
            "top_width_nm": "500.0",
            "depth_nm": "900.0",
        },
        {
            "validation_request_id": "PFV-REQUEST-ROUTE-CAND-002",
            "route_candidate_id": "ROUTE-CAND-002",
            "qch_sidecar_id": "QCH-CAND-002",
            "case_id": "taper_theta85_D900_W500",
            "source_geometry_hash": "b" * 64,
            "sidewall_deg_comsol": "85.0",
            "sidewall_taper_angle_deg_nodi": "5.0",
            "top_width_nm": "500.0",
            "depth_nm": "900.0",
        },
    ]


def _bindings() -> list[dict[str, object]]:
    return [
        {
            "validation_request_id": "PFV-REQUEST-ROUTE-CAND-001",
            "external_result_id": "COMSOL-PKG-C-W500-D900-001",
            "per_route_acceptance_status": "accepted_exact_pressure_flow_for_formal_qch_sidecar",
            "pressure_drop_Pa": "1000.0",
            "result_artifact_sha256": "c" * 64,
        },
        {
            "validation_request_id": "PFV-REQUEST-ROUTE-CAND-002",
            "external_result_id": "COMSOL-PKG-C-W500-D900-002",
            "per_route_acceptance_status": "accepted_exact_pressure_flow_for_formal_qch_sidecar",
            "pressure_drop_Pa": "1000.0",
            "result_artifact_sha256": "d" * 64,
        },
    ]


def _sidecars() -> list[dict[str, object]]:
    return [
        {
            "source_validation_request_id": "PFV-REQUEST-ROUTE-CAND-001",
            "source_external_result_id": "COMSOL-PKG-C-W500-D900-001",
            "q_ch_m3_s": "1.2e-16",
            "formal_flow_split_fraction": "0.6",
            "formal_qch_sidecar_current": "True",
        },
        {
            "source_validation_request_id": "PFV-REQUEST-ROUTE-CAND-002",
            "source_external_result_id": "COMSOL-PKG-C-W500-D900-002",
            "q_ch_m3_s": "8.0e-17",
            "formal_flow_split_fraction": "0.4",
            "formal_qch_sidecar_current": "True",
        },
    ]


def _build():
    return build_comsol_target_binding_qch_integration(
        request_rows=_requests(),
        binding_rows=_bindings(),
        sidecar_rows=_sidecars(),
        source_hashes={
            "launcher": "1" * 64,
            "build_scaffold": "2" * 64,
            "pressure_runner": "3" * 64,
            "connections": "4" * 64,
            "nodi_template": "5" * 64,
        },
        launcher_path="COMSOL_REPO/full_chip/dwg_analysis/run.py",
        launch_command_template="python run.py --run",
        launch_command_template_sha256="6" * 64,
        comsol_repo_head="7" * 40,
        comsol_repo_dirty_count=12,
    )


def test_integration_keeps_rectangle_and_trapezoid_parallel() -> None:
    rows, guards = _build()

    assert len(rows) == 2
    assert len(guards) == 5
    assert {row.route_geometry_family for row in rows} == {
        "ideal_rectangle",
        "trapezoid_tapered_sidewalls",
    }
    assert {row.formal_qch_sidecar_current for row in rows} == {True}
    assert {row.may_satisfy_route_formula_qch_branch_now for row in rows} == {True}
    assert {row.comsol_launch_required_for_current_qch for row in rows} == {False}


def test_integration_does_not_promote_qch_into_route_yield_detection() -> None:
    rows, guards = _build()

    assert {row.route_score_current for row in rows} == {False}
    assert {row.winner_current for row in rows} == {False}
    assert {row.yield_current for row in rows} == {False}
    assert {row.detection_probability_current for row in rows} == {False}
    assert {row.production_ingestion_current for row in rows} == {False}
    assert {row.claim_boundary for row in rows} == {
        SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_CLAIM_BOUNDARY
    }
    assert {
        guard.guard_target
        for guard in guards
        if guard.activation_allowed_now
    } == {"formal_qch_input"}
