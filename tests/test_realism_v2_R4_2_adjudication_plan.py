from __future__ import annotations

import copy

import pytest

from nodi_simulator import realism_v2 as rv2


def test_R4_2_adjudication_plan_is_plan_only_and_blocks_R5():
    plan = rv2.validate_R4_2_adjudication_plan()
    boundary = plan["authorization_boundary"]

    assert plan["stage"] == "R4_2_main660_nearwall_mesh_adjudication_plan_only"
    assert boundary["R4_2_execution_authorized"] is False
    assert boundary["R5_plan_preparation_authorized"] is False
    assert boundary["R5_full_grid_v2_authorized"] is False
    assert boundary["context_route_promotion_authorized"] is False
    assert boundary["main_660_redefinition_authorized"] is False
    assert boundary["route_specific_manual_sign_flips_authorized"] is False


def test_R4_2_consumes_failed_revised_R4_without_recovering_main_660():
    plan = rv2.validate_R4_2_adjudication_plan()
    evidence = plan["input_evidence"]

    assert evidence["accepted_gate"] == (
        "FAIL_REVISED_R4_RESULTS_RERUN_OR_ROUTE_MODEL_REVISION_REQUIRED"
    )
    assert evidence["recommended_next_action"] == (
        "prepare_R4_2_main660_nearwall_mesh_adjudication_plan_only"
    )
    assert evidence["main_660_nonblank_after_global_convention"] == 0.75
    assert evidence["main_660_sign_reliable_subset"] < 0.8
    assert evidence["main_660_review_refined_mesh"] == 1.0
    assert evidence["main_660_recovery_gate_met"] is False
    assert evidence["main_660_global_flip_failures"] == 20


def test_R4_2_route_particle_and_cost_scope_are_narrow():
    plan = rv2.validate_R4_2_adjudication_plan()
    route_keys = {
        (row["wavelength_nm"], row["width_nm"], row["depth_nm"])
        for row in plan["route_panel"]
    }
    particle_panel = plan["particle_panel"]
    cost = rv2.estimate_R4_2_adjudication_cost()

    assert route_keys == {(660, 800, 1400), (660, 800, 1500)}
    assert all(row["route_role"] == "main_660" for row in plan["route_panel"])
    assert all(row["route_role_locked"] is True for row in plan["route_panel"])
    assert all(
        row["main_660_redefinition_authorized"] is False
        for row in plan["route_panel"]
    )
    assert set(particle_panel["required_nonblank_particles"]) == (
        rv2.R4_2_ADJUDICATION_PARTICLES_REQUIRED
    )
    assert set(particle_panel["optional_particles"]) == {"blank"}
    assert cost["solver_case_count"] == 48
    assert cost["under_R4_2_review_cap"] is True
    assert plan["cost_cap"]["planned_solver_case_count"] == 48
    assert plan["cost_cap"]["max_R4_2_solver_cases_before_review"] == 64
    assert rv2.estimate_R4_2_adjudication_cost(n_routes=3)[
        "under_R4_2_review_cap"
    ] is False


def test_R4_2_mesh_roles_make_coarse_screen_non_decision_grade():
    plan = rv2.validate_R4_2_adjudication_plan()
    solver_scope = plan["solver_scope"]
    adjudication = plan["adjudication_questions"]

    assert solver_scope["interface_states"] == [
        "near_wall_stress",
        "centerline_nominal",
    ]
    assert set(solver_scope["polarization_states"]) == {
        "nominal_linear",
        "orthogonal_sensitivity",
    }
    assert solver_scope["new_mesh_levels"] == ["fine_confirm"]
    assert solver_scope["mesh_level_roles"] == {
        "coarse_screen": "screening_only",
        "review_refined": "validation_grade",
        "fine_confirm": "validation_grade_confirmation",
    }
    assert set(solver_scope["validation_grade_mesh_levels"]) == {
        "review_refined",
        "fine_confirm",
    }
    assert adjudication["coarse_screen_can_confirm_or_demote_routes"] is False
    assert adjudication["route_specific_manual_sign_flips_allowed"] is False


def test_R4_2_required_mode_lobe_and_cluster_fields_are_explicit():
    plan = rv2.validate_R4_2_adjudication_plan()
    diagnostics = plan["required_diagnostics"]
    cluster_fields = set(diagnostics["required_main660_cluster_fields"])

    assert set(diagnostics["mode_lobe_fields"]) == (
        rv2.R4_2_ADJUDICATION_REQUIRED_MODE_LOBE_FIELDS
    )
    assert cluster_fields == rv2.R4_2_ADJUDICATION_REQUIRED_CLUSTER_FIELDS
    assert "BFP_lobe_left_cross_term_W" in diagnostics["mode_lobe_fields"]
    assert "mode_overlap_phase_rad" in diagnostics["mode_lobe_fields"]
    assert "ROI_parity_sign" in diagnostics["mode_lobe_fields"]
    assert "mesh_level_role" in cluster_fields
    assert "sign_reliability_threshold_W" in cluster_fields
    assert "fine_confirm_agreement" in cluster_fields
    assert diagnostics["phase_diagnostic_only_not_gate_replacement"] is True
    assert diagnostics["near_wall_stress_sidecar_not_score_bonus"] is True


def test_R4_2_decision_criteria_require_validation_grade_recovery():
    plan = rv2.validate_R4_2_adjudication_plan()
    criteria = plan["decision_criteria"]

    assert criteria["fine_confirm_main660_fraction_min"] >= 0.8
    assert criteria["review_refined_main660_fraction_min"] >= 0.8
    assert criteria["fine_confirm_agrees_with_review_refined_min"] >= 0.9
    assert criteria["coarse_screen_disagreement_warning_only"] is True
    assert criteria["validation_grade_rows_exclude_coarse_screen"] is True
    assert criteria["no_route_role_change_required"] is True
    assert criteria["no_context_route_promotion_required"] is True
    assert criteria["no_main_660_redefinition_required"] is True
    assert criteria["failure_if_route_specific_sign_flip_needed"] is True
    assert criteria["possible_future_gate_after_success"] == (
        "PASS_R4_2_RESULTS_PREPARE_R5_PLAN_ONLY"
    )
    assert criteria["R5_execution_authorized_by_success"] is False


def test_R4_2_outputs_stop_gates_and_manifest_are_guarded():
    plan = rv2.validate_R4_2_adjudication_plan()
    outputs = set(plan["required_outputs_if_executed_after_review"])
    stop_gates = set(plan["stop_gates"])
    manifest = plan["manifest_expectations"]

    assert outputs == rv2.R4_2_ADJUDICATION_REQUIRED_OUTPUTS_IF_EXECUTED
    assert "main660_fine_confirm_sign_summary.csv" in outputs
    assert "BFP_lobe_resolved_cross_term_summary.csv" in outputs
    assert not any("full_grid" in output for output in outputs)
    assert rv2.R4_2_ADJUDICATION_REQUIRED_STOP_GATES.issubset(stop_gates)
    assert "legacy_detector_SNR_output_header_emitted" in stop_gates
    assert "legacy_calibrated_detector_SNR_output_header_emitted" in stop_gates
    assert "route_specific_manual_sign_flip_attempted" in stop_gates
    assert manifest["R4_representative_full_wave_validation_run"] is True
    assert manifest["R4_revised_rerun_run"] is True
    assert manifest["R4_2_main660_nearwall_mesh_adjudication_run"] is False
    assert manifest["R5_full_grid_v2_run"] is False


@pytest.mark.parametrize(
    ("section", "key", "value", "match"),
    [
        (
            "authorization_boundary",
            "R5_plan_preparation_authorized",
            True,
            "R5_plan_preparation_authorized=false",
        ),
        (
            "authorization_boundary",
            "R4_2_execution_authorized",
            True,
            "R4_2_execution_authorized=false",
        ),
        (
            "input_evidence",
            "main_660_sign_reliable_subset",
            0.8,
            "reliable-subset gate as passing",
        ),
        (
            "input_evidence",
            "main_660_recovery_gate_met",
            True,
            "cannot treat main_660 as recovered",
        ),
    ],
)
def test_R4_2_validation_fails_closed_for_boundary_and_evidence(
    section, key, value, match
):
    broken = copy.deepcopy(rv2.load_R4_2_adjudication_plan())
    broken[section][key] = value

    with pytest.raises(ValueError, match=match):
        rv2.validate_R4_2_adjudication_plan(broken)


def test_R4_2_validation_fails_if_coarse_or_route_specific_flips_are_decision_grade():
    broken = copy.deepcopy(rv2.load_R4_2_adjudication_plan())
    broken["adjudication_questions"]["coarse_screen_can_confirm_or_demote_routes"] = True
    with pytest.raises(ValueError, match="coarse_screen cannot be decision-grade"):
        rv2.validate_R4_2_adjudication_plan(broken)

    broken = copy.deepcopy(rv2.load_R4_2_adjudication_plan())
    broken["adjudication_questions"]["route_specific_manual_sign_flips_allowed"] = True
    with pytest.raises(ValueError, match="route-specific manual sign flips"):
        rv2.validate_R4_2_adjudication_plan(broken)


def test_R4_2_missing_required_stop_gate_fails_closed():
    for gate in rv2.R4_2_ADJUDICATION_REQUIRED_STOP_GATES:
        broken = copy.deepcopy(rv2.load_R4_2_adjudication_plan())
        broken["stop_gates"] = [
            existing for existing in broken["stop_gates"] if existing != gate
        ]

        with pytest.raises(ValueError, match="stop gates are incomplete"):
            rv2.validate_R4_2_adjudication_plan(broken)


def test_R4_2_missing_required_cluster_field_fails_closed():
    broken = copy.deepcopy(rv2.load_R4_2_adjudication_plan())
    broken["required_diagnostics"]["required_main660_cluster_fields"] = [
        field
        for field in broken["required_diagnostics"]["required_main660_cluster_fields"]
        if field != "fine_confirm_agreement"
    ]

    with pytest.raises(ValueError, match="cluster diagnostic fields mismatch"):
        rv2.validate_R4_2_adjudication_plan(broken)
