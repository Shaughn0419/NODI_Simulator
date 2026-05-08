from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


def test_R4_plan_cost_cap_blocks_over_cap_solver_design():
    cost = rv2.estimate_representative_full_wave_R4_cost(
        n_routes=rv2.MAX_R4_REPRESENTATIVE_ROUTES + 1
    )

    assert cost["under_R4_review_cap"] is False
    assert cost["solver_case_count"] > rv2.MAX_R4_SOLVER_CASES_BEFORE_REVIEW


def test_R4_route_panel_is_representative_and_does_not_promote_context_routes():
    plan = rv2.validate_representative_full_wave_R4_plan()
    routes = plan["route_panel"]
    route_keys = {
        (row["wavelength_nm"], row["width_nm"], row["depth_nm"], row["route_role"])
        for row in routes
    }

    assert len(routes) == rv2.MAX_R4_REPRESENTATIVE_ROUTES == 9
    assert (660, 800, 1400, "main_660") in route_keys
    assert (660, 800, 1500, "main_660") in route_keys
    assert (660, 900, 1400, "optional_robustness_probe") in route_keys
    assert (532, 900, 1500, "context_validation_candidate") in route_keys
    assert (660, 900, 1500, "context_validation_candidate") in route_keys
    assert (532, 800, 1500, "context_validation_candidate") in route_keys
    assert (404, 600, 1300, "shortwave_mechanism_candidate") in route_keys
    assert (404, 800, 600, "selected_annulus_sanity_overlap_shortwave") in route_keys
    assert (660, 800, 600, "selected_annulus_sanity_overlap_longwave") in route_keys
    assert all(row["route_role_locked"] is True for row in routes)
    assert all(row["route_role_source"] == rv2.R4_ROUTE_ROLE_SOURCE for row in routes)
    assert all(row["context_route_promotion_authorized"] is False for row in routes)
    assert all(row["confirm_if"] and row["demote_if"] and row["reclassify_if"] for row in routes)


def test_R4_particle_panel_is_representative_without_specificity_claims():
    particles = rv2.representative_full_wave_R4_particle_panel()
    particle_ids = {row["particle_id"] for row in particles}

    assert len(particles) == rv2.MAX_R4_REPRESENTATIVE_PARTICLES == 6
    assert particle_ids == rv2.R4_REQUIRED_PARTICLES
    assert all(row["biological_specificity_claim_allowed"] is False for row in particles)
    assert {"blank", "EV", "contaminant", "standard"}.issubset(
        {row["particle_class"] for row in particles}
    )


def test_R4_solver_scope_observables_and_outputs_are_defined():
    plan = rv2.validate_representative_full_wave_R4_plan()
    solver = plan["solver_scope"]
    observable_ids = {row["observable_id"] for row in plan["observables"]}

    assert solver["execution_status"] == "not_run_plan_only"
    assert len(solver["interface_states"]) == rv2.MAX_R4_INTERFACE_STATES
    assert len(solver["polarization_states"]) == rv2.MAX_R4_POLARIZATION_STATES
    assert len(solver["mesh_levels"]) == rv2.MAX_R4_MESH_LEVELS
    assert rv2.R4_REQUIRED_OBSERVABLES.issubset(observable_ids)
    assert set(plan["required_outputs_if_executed"]) == rv2.R4_REQUIRED_OUTPUTS_IF_EXECUTED
    assert all(
        row["claim_level"] in {"relative_with_priors", "diagnostic_only"}
        for row in plan["observables"]
    )


def test_R4_solver_case_contract_has_numeric_executable_definitions():
    plan = rv2.validate_representative_full_wave_R4_plan()
    solver = plan["solver_scope"]
    contract = plan["solver_case_contract"]

    assert set(rv2.R4_REQUIRED_SOLVER_CASE_CONTRACT_FIELDS).issubset(contract)
    assert contract["solver_engine_class"] == "FEM_modal_equivalent"
    assert contract["solver_name_or_backend"] == rv2.R4_INTERNAL_NUMERICAL_SOLVER_BACKEND
    assert contract["geometry_units"] == "nm"
    assert contract["near_wall_stress_distance_nm"] == pytest.approx(10.0)
    assert contract["mesh_convergence_threshold"] == pytest.approx(0.15)
    assert contract["solver_boundary_sensitivity_threshold"] == pytest.approx(0.25)
    assert set(contract["particle_pose_definition"]) == set(solver["interface_states"])
    assert (
        contract["particle_pose_definition"]["near_wall_stress"][
            "nearest_wall_clearance_nm"
        ]
        == pytest.approx(10.0)
    )
    assert set(contract["polarization_vector_definition"]) == set(
        solver["polarization_states"]
    )
    assert set(contract["mesh_level_definitions_nm"]) == set(solver["mesh_levels"])
    assert contract["slit_ROI_definition"][
        "same_operator_applied_to_reference_and_scattering"
    ] is True
    assert contract["pinhole_ROI_definition"][
        "same_operator_applied_to_reference_and_scattering"
    ] is True


def test_R4_solver_state_string_label_fails_closed():
    plan = rv2.load_representative_full_wave_R4_plan()
    broken = copy.deepcopy(plan)
    broken["solver_case_contract"]["particle_pose_definition"][
        "near_wall_stress"
    ] = "near_wall_stress"

    with pytest.raises(ValueError, match="interface state is only a label"):
        rv2.validate_representative_full_wave_R4_plan(broken)


def test_R4_particle_material_contract_defines_optical_parameters():
    plan = rv2.validate_representative_full_wave_R4_plan()
    material_rows = plan["particle_material_contract"]
    by_id = {row["particle_id"]: row for row in material_rows}

    assert set(by_id) == rv2.R4_REQUIRED_PARTICLES
    for row in material_rows:
        assert set(rv2.R4_REQUIRED_PARTICLE_MATERIAL_FIELDS).issubset(row)
        assert row["biological_specificity_claim_allowed"] is False
        assert row["medium_RI_source"]
        assert row["wavelength_interpolation_policy"]
        assert row["absorption_imaginary_RI_policy"]
    assert by_id["EV70_lowRI"]["shape_model"] == "core_shell_sphere"
    assert by_id["EV70_lowRI"]["diameter_nm"] == pytest.approx(70.0)
    assert by_id["EV100_nominal"]["core_RI"] == pytest.approx(1.39)
    assert by_id["EV250_nominal"]["shell_thickness_nm"] == pytest.approx(5.0)
    assert by_id["LDL_like_contaminant"]["shape_model"] == "homogeneous_sphere"
    assert "Johnson_Christy_1972" in by_id["Au40"]["material_database_key"]


def test_R4_particle_material_contract_missing_field_fails_closed():
    plan = rv2.load_representative_full_wave_R4_plan()
    broken = copy.deepcopy(plan)
    broken["particle_material_contract"][1].pop("core_RI")

    with pytest.raises(ValueError, match="particle material contract missing fields"):
        rv2.validate_representative_full_wave_R4_plan(broken)


def test_R4_pre_run_plan_is_plan_only_and_under_cap():
    pre_run = rv2.validate_R4_pre_run_plan()

    assert pre_run["R4_execution_authorized"] is False
    assert pre_run["R4_representative_full_wave_validation_run"] is False
    assert pre_run["R5_full_grid_v2_run"] is False
    assert pre_run["context_route_promotion_authorized"] is False
    assert pre_run["cost"]["under_R4_review_cap"] is True
    assert pre_run["cost"]["solver_case_count"] == rv2.MAX_R4_SOLVER_CASES_BEFORE_REVIEW


def test_R4_manifest_plan_keeps_R4_execution_false_and_R5_false(tmp_path: Path):
    manifest = rv2.build_run_manifest(
        output_directory=tmp_path,
        event_budget={
            "stage": "R4_plan_pre_run_validation_only",
            "R4_representative_full_wave_validation_started": False,
        },
        scenario_budget={
            "max_R4_solver_cases_before_review": rv2.MAX_R4_SOLVER_CASES_BEFORE_REVIEW,
            "R4_execution_authorized": False,
            "R5_full_grid_v2_authorized": False,
        },
        run_id="EV_NODI_realism_v2_R4_plan_pre_run_validation_only",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=True,
        R4_representative_full_wave_validation_run=False,
        R5_full_grid_v2_run=False,
    )

    rv2.validate_run_manifest(manifest)
    assert manifest["R3b_uncertainty_expansion_run"] is True
    assert manifest["R4_representative_full_wave_validation_run"] is False
    assert manifest["R5_full_grid_v2_run"] is False
    assert manifest["v1_full_grid_overwritten"] is False
    assert manifest["Tsuyama_paper_fit_continued"] is False
    assert manifest["selected_annulus_bounds_changed"] is False
    assert manifest["calibrated_SNR_claim_emitted"] is False
    assert manifest["ET2030_direct_current_input_unlocked"] is False
    assert "r4_representative_full_wave_plan_checksum" in manifest
    json.dumps(manifest)


def test_R4_stop_gates_and_decision_criteria_are_active():
    plan = rv2.validate_representative_full_wave_R4_plan()
    labels = set(plan["promotion_demotion_criteria"]["allowed_decision_labels"])
    stop_gates = set(plan["stop_gates"])

    assert plan["promotion_demotion_criteria"]["context_route_promotion_authorized"] is False
    assert {
        "confirm_for_future_review",
        "demote_from_R4_candidate",
        "reclassify_requires_external_review",
        "inconclusive_requires_plan_revision",
    }.issubset(labels)
    assert "R4_execution_without_external_authorization" in stop_gates
    assert "R5_or_full_grid_v2_started" in stop_gates
    assert "context_route_promotion_attempted" in stop_gates
    assert "calibrated_SNR_or_event_probability_claim_emitted" in stop_gates
    assert "legacy_detector_SNR_output_header_emitted" in stop_gates
    assert "legacy_calibrated_detector_SNR_output_header_emitted" in stop_gates
    assert rv2.R4_REQUIRED_STOP_GATES.issubset(stop_gates)


def test_R4_numeric_decision_thresholds_are_pre_registered():
    plan = rv2.validate_representative_full_wave_R4_plan()
    thresholds = plan["promotion_demotion_criteria"]["numeric_decision_thresholds"]
    bins = plan["promotion_demotion_criteria"]["numeric_decision_bins"]

    assert thresholds["eps"] > 0.0
    assert thresholds["surrogate_delta_log_confirm_abs_max"] == pytest.approx(0.35)
    assert thresholds["surrogate_delta_log_demote_abs_min"] == pytest.approx(0.75)
    assert (
        thresholds["surrogate_delta_log_confirm_abs_max"]
        < thresholds["surrogate_delta_log_demote_abs_min"]
    )
    assert thresholds["mesh_refined_delta_abs_max"] == pytest.approx(0.15)
    assert thresholds["polarization_sensitivity_abs_max"] == pytest.approx(0.50)
    assert thresholds["near_wall_stress_delta_abs_max"] == pytest.approx(0.75)
    assert thresholds["solver_boundary_sensitivity_abs_max"] == pytest.approx(0.25)
    assert thresholds["BFP_extraction_unit_guard_required"] is True
    assert thresholds["ROI_mapping_reversal_demotes"] is True
    assert "sign_preserved" in bins["confirm_for_future_review"]
    assert "sign_mismatch" in bins["demote_from_R4_candidate"]
    assert "mesh_refined_delta_abs_gt_0p15" in bins[
        "inconclusive_requires_plan_revision"
    ]


def test_R4_plan_carries_R3b_effect_delta_and_thermal_field_hardening():
    plan = rv2.validate_representative_full_wave_R4_plan()
    hardening = plan["R3b_hardening_preconditions"]

    assert hardening["R3b_effect_delta_hardening_status"] == "equivalence_test_passed"
    assert hardening["effect_delta_equivalence_test_name"] == (
        "test_R4_R3b_group_component_log_multiplier_equivalence_is_active"
    )
    assert "effect_delta_log_score_ratio" in hardening["effect_delta_policy"]
    assert "group_component_log_multiplier" in hardening["effect_delta_policy"]
    assert (
        "thermal_not_blocking_stage_progression"
        in hardening["thermal_promotion_field_policy"]
    )
    assert hardening["uncertainty_band_overlap_policy"].endswith("may not promote routes.")


def test_R4_R3b_group_component_log_multiplier_equivalence_is_active():
    component_logs = {
        "660_800x1400": [0.0, 0.10, 0.20],
        "532_900x1500": [-0.05, 0.25, 0.45],
    }

    check = rv2.R3b_group_component_log_multiplier_equivalence_check(component_logs)
    direct = rv2.R3b_effect_delta_from_group_component_log_multipliers(component_logs)

    assert check["effect_delta_convention"] == rv2.R3B_EFFECT_DELTA_CONVENTION
    assert check["equivalence_passed"] is True
    assert check["max_abs_error"] <= 1.0e-12
    assert direct["660_800x1400"] == pytest.approx(0.10)
    assert direct["532_900x1500"] == pytest.approx(0.25)


def test_R4_effect_delta_policy_carried_forward_status_fails_closed():
    plan = rv2.load_representative_full_wave_R4_plan()
    broken = copy.deepcopy(plan)
    broken["R3b_hardening_preconditions"][
        "R3b_effect_delta_hardening_status"
    ] = "policy_carried_forward"

    with pytest.raises(ValueError, match="hardening status is not active"):
        rv2.validate_representative_full_wave_R4_plan(broken)


def test_R4_each_required_stop_gate_is_validated_fail_closed():
    plan = rv2.load_representative_full_wave_R4_plan()
    for gate in rv2.R4_REQUIRED_STOP_GATES:
        broken = copy.deepcopy(plan)
        broken["stop_gates"] = [
            existing for existing in broken["stop_gates"] if existing != gate
        ]
        with pytest.raises(ValueError, match="stop gates are incomplete"):
            rv2.validate_representative_full_wave_R4_plan(broken)


def test_R4_missing_route_criterion_fails_closed():
    plan = rv2.load_representative_full_wave_R4_plan()
    broken = copy.deepcopy(plan)
    broken["route_panel"][0].pop("confirm_if")

    with pytest.raises(ValueError, match="missing validation criterion"):
        rv2.validate_representative_full_wave_R4_plan(broken)
