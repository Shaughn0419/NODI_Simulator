from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from nodi_simulator.nodi_comsol_next_artifacts import (
    AUTHORIZATION_GATE_PASS_STATUS,
    BOUNDED_SMOKE_EXECUTION_PASS_STATUS,
    BOUNDED_SMOKE_EXECUTION_ROW_STATUS,
    BOUNDED_SMOKE_READINESS_PASS_STATUS,
    BOUNDED_SMOKE_AUTHORIZATION_PHRASE,
    COMSOL_V4_ASSUMPTION_SET_ID,
    COMSOL_V4_ASSUMPTION_SET_SHA256,
    COMSOL_V4_SCOPE_OUT_OF_SCOPE_DRY_OPTICAL_SURROGATE,
    COMSOL_V4_SCOPE_WET_SURFACE_CONTEXT,
    COMSOL_V4_UNBOUND_REQUIRED,
    EAS_BOUNDED_SMOKE_EXECUTION_MANIFEST_FILENAME,
    EAS_FIRST_PRODUCTION_MODES,
    EAS_PRODUCTION_FILENAME,
    EAS_SELECTOR_POLICY_METADATA_FILENAME,
    EAS_SMOKE_MANIFEST_FILENAME,
    EAS_CLAIM_BOUNDARY,
    EAS_RANK_SOURCE,
    EAS_RECOMMENDATION_RANK_SOURCE,
    EAS_WEIGHTING_BASIS,
    FUTURE_AUTHORIZATION_PHRASE_MATCH_BLOCKED_NO_EXECUTION,
    FUTURE_AUTHORIZATION_PHRASE_MATCH_RUNNER_IMPLEMENTATION,
    FUTURE_AUTHORIZATION_PHRASE_MISMATCH,
    GEOMETRY_DESCRIPTOR_CLAIM_BOUNDARY,
    GEOMETRY_DESCRIPTOR_SHA256,
    NEXT_ARTIFACTS_SMOKE_INDEX_FILENAME,
    NEXT_ARTIFACTS_SMOKE_METADATA_FILENAME,
    NEXT_ARTIFACTS_RUNNER_PREFLIGHT_ISSUES_FILENAME,
    NEXT_ARTIFACTS_RUNNER_PREFLIGHT_REPORT_FILENAME,
    EAS_PLAN_BLUEPRINT_FILENAME,
    NEXT_ARTIFACTS_PLAN_BLUEPRINT_INDEX_FILENAME,
    NEXT_ARTIFACTS_PLAN_BLUEPRINT_METADATA_FILENAME,
    NEXT_ARTIFACTS_AUTHORIZATION_GATE_ISSUES_FILENAME,
    NEXT_ARTIFACTS_AUTHORIZATION_GATE_RECORD_FILENAME,
    PENDING_FLOW_SHA,
    PLAN_ONLY_EXECUTION_STATUS,
    POSITION_RESPONSE_BIN_SOURCE_ARTIFACT,
    POSITION_RESPONSE_ARTIFACT,
    PRS_BIN_SOURCE_SMOKE_EVENTS_FILENAME,
    PRS_BIN_SOURCE_SMOKE_PASS_STATUS,
    PRS_BIN_SOURCE_SMOKE_REPORT_FILENAME,
    PRS_BIN_SOURCE_SMOKE_SOURCE_FILENAME,
    PRS_REAL_EVENT_SOURCE_SMOKE_EVENTS_FILENAME,
    PRS_REAL_EVENT_SOURCE_SMOKE_PASS_STATUS,
    PRS_REAL_EVENT_SOURCE_SMOKE_REPORT_FILENAME,
    PRS_REAL_EVENT_SOURCE_SMOKE_SOURCE_FILENAME,
    PRS_EDGE_PRIMARY_CANDIDATE_FILENAME,
    PRS_EDGE_PRIMARY_CANDIDATE_PASS_STATUS,
    PRS_EDGE_PRIMARY_CANDIDATE_REPORT_FILENAME,
    PRS_RUNNER_SLICE_SOURCE_EXPORT_EVENTS_FILENAME,
    PRS_RUNNER_SLICE_SOURCE_EXPORT_PASS_STATUS,
    PRS_RUNNER_SLICE_SOURCE_EXPORT_REPORT_FILENAME,
    PRS_RUNNER_SLICE_SOURCE_EXPORT_SOURCE_FILENAME,
    PRS_APPROVED_DIAMETERS_NM,
    PRS_APPROVED_ROUTE_MATRIX,
    PRS_APPROVED_VIEWS,
    PRS_SOURCE_ACCUMULATION_BLOCKED_STATUS,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_AUTHORIZATION_PHRASE,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_EVENTS_FILENAME,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MANIFEST_FILENAME,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_PASS_STATUS,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_REPORT_FILENAME,
    PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_SOURCE_FILENAME,
    PRS_SOURCE_ACCUMULATION_CAMPAIGN_JOB_SCHEDULE_FILENAME,
    PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_PASS_STATUS,
    PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_REPORT_FILENAME,
    PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_PASS_STATUS,
    PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_REPORT_FILENAME,
    PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_SHARD_FILENAME,
    PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARDS_FILENAME,
    PRS_SOURCE_ACCUMULATION_BLOCKERS_FILENAME,
    PRS_SOURCE_ACCUMULATION_ISSUES_FILENAME,
    PRS_SOURCE_ACCUMULATION_JOB_PLAN_FILENAME,
    PRS_SOURCE_ACCUMULATION_PASS_STATUS,
    PRS_SOURCE_ACCUMULATION_REPORT_FILENAME,
    PRS_SOURCE_ACCUMULATION_TARGET_EVENTS_PER_SEED,
    PRS_SOURCE_PRODUCTION_SCOPE,
    PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS,
    PRS_SOURCE_SUFFICIENCY_BLOCKERS_FILENAME,
    PRS_SOURCE_SUFFICIENCY_CANDIDATES_FILENAME,
    PRS_SOURCE_SUFFICIENCY_ISSUES_FILENAME,
    PRS_SOURCE_SUFFICIENCY_JOB_PLAN_FILENAME,
    PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
    PRS_SOURCE_SUFFICIENCY_REPORT_FILENAME,
    PRS_SOURCE_PREFLIGHT_BLOCKED_STATUS,
    PRS_SOURCE_PREFLIGHT_BLOCKERS_FILENAME,
    PRS_SOURCE_PREFLIGHT_CANDIDATES_FILENAME,
    PRS_SOURCE_PREFLIGHT_PASS_STATUS,
    PRS_SOURCE_PREFLIGHT_REPORT_FILENAME,
    PRS_SOURCE_PREFLIGHT_ISSUES_FILENAME,
    PRS_SOURCE_PRODUCTION_ELIGIBILITY_BLOCKED_STATUS,
    PRS_SOURCE_PRODUCTION_ELIGIBILITY_PASS_STATUS,
    PRS_SOURCE_PRODUCTION_ELIGIBILITY_REPORT_FILENAME,
    PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
    PRS_PLAN_BLUEPRINT_FILENAME,
    PRS_RUNNER_LAUNCH_PLAN_FILENAME,
    PRS_SMOKE_MANIFEST_FILENAME,
    PRS_CLAIM_BOUNDARY,
    PRS_FLOW_CONDITION_CLAIM_BOUNDARY,
    PRS_FLOW_CONDITION_SCOPE,
    PRS_NEUTRAL_FLOW_CONDITION_ID,
    PRS_POSITION_DISTRIBUTION_BASIS,
    PRS_PRODUCTION_FILENAME,
    QCH_FLOW_CONDITION_ID,
    ROWS_PER_ROUTE_DIAMETER_VIEW,
    RUNNER_IMPLEMENTATION_AUTHORIZATION_PHRASE,
    RUNNER_IMPLEMENTATION_READY_STATUS,
    EAS_RUNNER_LAUNCH_PLAN_FILENAME,
    build_effective_aperture_runner_launch_plan,
    build_bounded_smoke_readiness_report,
    build_position_response_runner_launch_plan,
    default_comsol_v4_readonly_context,
    effective_aperture_smoke_manifest_rows,
    evaluate_next_artifacts_future_authorization_request,
    position_response_smoke_manifest_rows,
    effective_aperture_plan_blueprint_rows,
    position_response_plan_blueprint_rows,
    validate_effective_aperture_surrogate_rows,
    validate_geometry_descriptor_rows,
    validate_next_artifacts_runner_authorization_gate_record,
    validate_plan_only_blueprint_bundle,
    validate_bounded_smoke_readiness_report,
    validate_position_response_surface_rows,
    validate_runner_launch_plan,
    validate_sidewall_package_d_precheck_rows,
    NEXT_ARTIFACTS_BOUNDED_SMOKE_READINESS_REPORT_FILENAME,
    NEXT_ARTIFACTS_BOUNDED_SMOKE_READINESS_ISSUES_FILENAME,
    NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_REPORT_FILENAME,
    NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_ISSUES_FILENAME,
    NEXT_ARTIFACTS_PRODUCTION_GENERATION_BLOCKERS_FILENAME,
    NEXT_ARTIFACTS_PRODUCTION_GENERATION_ISSUES_FILENAME,
    NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_FILENAME,
    APERTURE_SURROGATE_ARTIFACT,
    PRS_BOUNDED_SMOKE_EXECUTION_MANIFEST_FILENAME,
    PRODUCTION_GENERATION_BLOCKED_STATUS,
    PRODUCTION_GENERATION_PARTIAL_STATUS,
    PRODUCTION_GENERATION_PASS_STATUS,
    build_position_response_bin_source_rows_from_events,
    build_position_response_event_rows_from_nodi_events,
    build_effective_aperture_first_production_rows,
    build_position_response_source_accumulation_campaign_policy,
    build_position_response_source_accumulation_campaign_runner_readiness,
    build_position_response_source_accumulation_job_plan,
    build_position_response_source_accumulation_bounded_shard_report,
    build_position_response_source_production_eligibility_report,
    build_position_response_source_preflight_report,
    build_position_response_source_sufficiency_report,
    build_bounded_smoke_execution_report,
    build_production_generation_report,
    build_position_response_edge_primary_candidate_rows,
    default_position_response_source_candidate_paths,
    write_design_only_smoke_manifest_bundle,
    write_effective_aperture_runner_launch_plan,
    write_bounded_smoke_execution_bundle,
    write_bounded_smoke_readiness_report,
    write_no_execution_runner_preflight_report,
    write_next_artifacts_runner_authorization_gate_record,
    write_position_response_runner_launch_plan,
    write_plan_only_blueprint_bundle,
    write_position_response_bin_source_smoke_bundle,
    write_position_response_source_accumulation_job_plan_bundle,
    write_position_response_source_accumulation_bounded_shard_sidecars,
    write_position_response_source_accumulation_campaign_policy_bundle,
    write_position_response_source_accumulation_campaign_runner_readiness_bundle,
    write_position_response_source_production_eligibility_bundle,
    write_position_response_source_preflight_bundle,
    write_position_response_source_sufficiency_bundle,
    write_production_generation_bundle,
    write_position_response_edge_primary_candidate_bundle,
    ContractValidationError,
    effective_aperture_bounded_smoke_execution_manifest_rows,
    position_response_bounded_smoke_execution_manifest_rows,
    select_position_response_source_accumulation_bounded_shard_jobs,
    validate_bounded_smoke_execution_manifest_rows,
    validate_bounded_smoke_execution_report,
    validate_comsol_v4_readonly_context,
    validate_position_response_bin_source_event_rows,
    validate_position_response_bin_source_rows,
    validate_position_response_source_accumulation_job_plan_report,
    validate_position_response_source_accumulation_bounded_shard_report,
    validate_position_response_source_accumulation_campaign_policy_report,
    validate_position_response_source_accumulation_campaign_runner_readiness_report,
    validate_position_response_source_production_eligibility_report,
    validate_position_response_source_preflight_report,
    validate_position_response_source_sufficiency_report,
    validate_production_generation_report,
)
from nodi_simulator.realism_v2_io import read_csv_rows, write_csv_rows
from tools.audits.run_nodi_position_response_runner_slice_source_export import (
    validate_route_source_slice,
)
from tools.audits.merge_nodi_position_response_edge_primary_candidates import (
    merge_candidate_rows,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


VALID_SHA = "a" * 64


def _valid_prs_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "response_surface_artifact_version": "NODI_POSITION_RESPONSE_SURFACE_V1",
        "row_scope": "response_surface_bin",
        "route_id_nodi": "404/W500/D900",
        "lambda_nm": 404,
        "W_nominal_nm": 500,
        "D_nm": 900,
        "NODI_view": "fixed_660_gold",
        "diameter_nm": 150,
        "particle_kind": "exosome_synthetic",
        "distribution_type": "edge_norm_1d",
        "row_kind": "base_bin",
        "aggregate_id": "",
        "bin_id": "edge_00",
        "edge_norm_min": 0.0,
        "edge_norm_max": 0.05,
        "x_norm_min": "",
        "x_norm_max": "",
        "z_norm_min": "",
        "z_norm_max": "",
        "aggregate_source_type": "edge_norm_primary",
        "n_seeds": 3,
        "n_events_total": 300,
        "n_events_bin": 300,
        "n_events_bin_per_seed_min": 100,
        "sparse_bin_flag": "false",
        "sparse_bin_policy": "aggregate_level_explicit_only",
        "bin_sample_status": "adequate",
        "decision_use_allowed": "true",
        "guardrail_status": "recommendation_eligible",
        "position_distribution_basis": PRS_POSITION_DISTRIBUTION_BASIS,
        "flow_condition_id": PRS_NEUTRAL_FLOW_CONDITION_ID,
        "flow_condition_version": "V1",
        "flow_condition_source_sha": PENDING_FLOW_SHA,
        "flow_condition_scope": PRS_FLOW_CONDITION_SCOPE,
        "flow_condition_claim_boundary": PRS_FLOW_CONDITION_CLAIM_BOUNDARY,
        "view_physical_independence_flag": "false",
        "not_comsol_transport_distribution": "true",
        "not_qch_weighted": "true",
        "not_yield": "true",
        "not_detection_probability": "true",
        "claim_boundary": PRS_CLAIM_BOUNDARY,
        "source_artifact": "results/unit/prs_fixture.csv",
        "source_sha256": VALID_SHA,
    }
    row.update(overrides)
    return row


def _sidewall_descriptor_context_fields(
    depth_nm: float = 900.0,
    sidewall_deg: float = 85.0,
) -> dict[str, object]:
    w_top_nm = 500.0
    w_bottom_unclipped_nm = w_top_nm - 2.0 * depth_nm / math.tan(
        math.radians(sidewall_deg)
    )
    if w_bottom_unclipped_nm <= 0.0:
        closure_status = "geometry_closed"
    elif w_bottom_unclipped_nm <= 80.0:
        closure_status = "near_closed"
    else:
        closure_status = "open"
    runtime_guard_status = {
        "open": "none",
        "near_closed": "solver_guard",
        "geometry_closed": "validation_guard",
    }[closure_status]
    return {
        "geometry_profile_source": "comsol_descriptor",
        "geometry_profile_sha256": GEOMETRY_DESCRIPTOR_SHA256,
        "geometry_claim_level": "descriptor_only",
        "metrology_status": "not_measured",
        "sidewall_angle_convention": "sidewall_angle_from_substrate_plane_90deg_vertical",
        "sidewall_deg_comsol": sidewall_deg,
        "sidewall_taper_angle_deg_nodi": 90.0 - sidewall_deg,
        "angle_conversion_formula_id": "sidewall_from_horizontal_to_taper_from_vertical_v1",
        "W_top_nm": w_top_nm,
        "W_top_semantics": "comsol_descriptor",
        "W_bottom_unclipped_nm": w_bottom_unclipped_nm,
        "W_bottom_runtime_clipped_nm": max(w_bottom_unclipped_nm, 0.0),
        "closure_status": closure_status,
        "closure_policy": "preserve_unclipped_descriptor",
        "runtime_guard_status": runtime_guard_status,
    }


def _without_sidewall_descriptor_context(row: dict[str, object]) -> dict[str, object]:
    for field in _sidewall_descriptor_context_fields():
        row.pop(field, None)
    return row


def _sidewall_observation_cache_fields(
    channel_model: str = "trapezoid_tapered_sidewalls",
) -> dict[str, object]:
    trapezoid_guard_fragments = (
        "|cross_section_geometry_version=trapezoid_straight_sidewall_v1"
        f"|geometry_profile_sha256={GEOMETRY_DESCRIPTOR_SHA256}"
        "|particle_radius_m=1.1e-07"
        "|center_accessible_support_model=wall_normal_half_plane_offset_v1"
        "|sampler_geometry_model=trapezoid_accessible_area_v1"
        "|trajectory_boundary_model=not_applicable_pure_advection"
        "|wall_distance_model=not_applicable_diffusion_hindrance_none"
        "|flow_profile_geometry_model=plug_flow_geometry_independent_v1"
        "|geometry_propagation_status=sidewall_sampler_and_pure_advection_propagated"
        "|reference_geometry_propagation_status=blocked_trapezoid_geometry_not_propagated_to_reference_field"
        "|geometry_not_propagated_to_reference_field=True"
        "|not_optical_solver_output=True"
        "|fluidic_clogging_risk_band_claim_level=static_throat_clearance_proxy_not_clogging_rate"
        "|not_clogging_rate=True"
        "|not_time_to_clog=True"
        "|fluidic_geometry_propagation_status=geometry_not_propagated_to_fluidic_resistance"
        "|geometry_not_propagated_to_fluidic_resistance=True"
        "|fluidic_network_geometry_propagation_status=geometry_not_propagated_to_fluidic_network"
        "|geometry_not_propagated_to_fluidic_network=True"
        "|fluidic_network_not_qch_weighted=True"
        "|electrokinetic_geometry_propagation_status=blocked_geometry_not_propagated"
        "|geometry_not_propagated_to_electrokinetic_transport=True"
        "|surface_charge_transport_claim_level=blocked_trapezoid_geometry_not_propagated_to_electrokinetic_transport"
        "|electrokinetic_diagnostic_gate_passed=False"
    )
    signature = (
        f"channel_cross_section_model={channel_model}"
        "|sidewall_taper_angle_deg=5.000000000e+00"
    )
    if channel_model == "trapezoid_tapered_sidewalls":
        signature += trapezoid_guard_fragments
    else:
        signature += f"|geometry_profile_sha256={GEOMETRY_DESCRIPTOR_SHA256}"
    return {
        "observation_signature": signature,
        "observation_signature_version": "sidewall_observation_signature_v1",
        "cache_geometry_match_status": "matched_current_geometry",
    }


def _sidewall_runtime_propagation_guard_fields() -> dict[str, object]:
    return {
        "reference_geometry_propagation_status": (
            "blocked_trapezoid_geometry_not_propagated_to_reference_field"
        ),
        "geometry_not_propagated_to_reference_field": "true",
        "not_optical_solver_output": "true",
        "fluidic_clogging_risk_band_claim_level": (
            "static_throat_clearance_proxy_not_clogging_rate"
        ),
        "not_clogging_rate": "true",
        "not_time_to_clog": "true",
        "fluidic_geometry_model": (
            "trapezoid_descriptor_with_rectangular_proxy_fluidics"
        ),
        "hydraulic_resistance_model": (
            "rectangular_hydraulic_resistance_proxy_under_trapezoid"
        ),
        "hydraulic_resistance_claim_level": (
            "proxy_not_trapezoid_poiseuille_not_accepted_for_formula_use"
        ),
        "fluidic_geometry_propagation_status": (
            "geometry_not_propagated_to_fluidic_resistance"
        ),
        "geometry_not_propagated_to_fluidic_resistance": "true",
        "fluidic_network_geometry_model": (
            "trapezoid_descriptor_with_rectangular_proxy_network"
        ),
        "fluidic_network_hydraulic_resistance_model": (
            "rectangular_hydraulic_resistance_network_proxy_under_trapezoid"
        ),
        "fluidic_network_hydraulic_resistance_claim_level": (
            "diagnostic_only_rectangular_proxy_not_trapezoid_poiseuille_not_qch"
        ),
        "fluidic_network_geometry_propagation_status": (
            "geometry_not_propagated_to_fluidic_network"
        ),
        "geometry_not_propagated_to_fluidic_network": "true",
        "fluidic_network_not_qch_weighted": "true",
        "electrokinetic_transport_geometry_model": (
            "blocked_trapezoid_requires_profile_aware_grid"
        ),
        "electrokinetic_wall_distance_model": "blocked_rectangular_wall_distance_grid",
        "electrokinetic_geometry_propagation_status": "blocked_geometry_not_propagated",
        "geometry_not_propagated_to_electrokinetic_transport": "true",
        "surface_charge_transport_claim_level": (
            "blocked_trapezoid_geometry_not_propagated_to_electrokinetic_transport"
        ),
        "electrokinetic_diagnostic_gate_passed": "false",
    }


def _sidewall_acceptance_guard_fields() -> dict[str, object]:
    return {
        "roadmap_status": "surrogate_sensitivity_only",
        "not_accepted_for_formula_use": "true",
        "not_accepted_for_runtime_config": "true",
        "not_accepted_for_production": "true",
    }


def _sidewall_artifact_metadata_fields(artifact_version: str) -> dict[str, object]:
    return {
        "artifact_id": "sidewall-v2-fixture",
        "artifact_version": artifact_version,
        "artifact_created_utc": "2026-06-29T00:00:00Z",
    }


def _valid_prs_sidewall_v2_row(**overrides: object) -> dict[str, object]:
    row = _valid_prs_row(
        diameter_nm=220,
        particle_kind="exosome_synthetic_large_tail",
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        cross_section_geometry_version="trapezoid_straight_sidewall_v1",
        geometry_runtime_binding_version="geometry_runtime_binding_manifest_v1",
        geometry_propagation_status="propagated",
        geometry_not_propagated_reasons="",
        sampler_geometry_model="trapezoid_accessible_area_v1",
        sampler_support_model="wall_normal_half_plane_offset_v1",
        particle_radius_nm=110.0,
        tail_particle_auto_admitted="false",
        steric_support_source="exact_geometry_primitive",
        coordinate_basis="u_from_top",
        coordinate_conversion_formula_id="centered_z_to_u_from_top_v1",
        x_nm=0.0,
        u_nm=450.0,
        z_nm=0.0,
        x_left_nm=-210.5,
        x_right_nm=210.5,
        x_center_nm=0.0,
        local_width_nm=421.0,
        local_half_width_nm=210.5,
        x_local_norm=0.0,
        u_norm=0.5,
        d_top_nm=450.0,
        d_bottom_nm=450.0,
        d_side_left_nm=171.0,
        d_side_right_nm=171.0,
        d_nearest_wall_nm=171.0,
        nearest_wall_id="left_side",
        surface_gap_for_particle_nm=61.0,
        bin_basis="edge_norm_1d_trapezoid_wall_distance_v1",
        bin_accessible="true",
        bin_accessible_area_fraction=1.0,
        bin_particle_center_support_status="open",
        blocked_reason="",
        sparse_reason="",
        neighbor_fill_used="false",
        trajectory_boundary_model="not_applicable_pure_advection",
        wall_distance_model="not_applicable_diffusion_hindrance_none",
        flow_profile_model="plug",
        flow_control_mode="fixed_velocity",
        reference_field_model="geometry_scaled",
        reference_spatial_mode="cross_section_surrogate",
        source_geometry_descriptor_id="descriptor-404-W500-D900-sidewall-85",
        source_geometry_descriptor_sha=GEOMETRY_DESCRIPTOR_SHA256,
        **_sidewall_artifact_metadata_fields("NODI_POSITION_RESPONSE_SIDEWALL_V2"),
        **_sidewall_acceptance_guard_fields(),
        **_sidewall_observation_cache_fields(),
        **_sidewall_runtime_propagation_guard_fields(),
        **_sidewall_descriptor_context_fields(),
    )
    row.update(overrides)
    return row


def _valid_eas_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "aperture_artifact_version": "NODI_EFFECTIVE_APERTURE_SURROGATE_V1",
        "route_id_nodi": "404/W500/D900",
        "lambda_nm": 404,
        "W_nominal_nm": 500,
        "D_nm": 900,
        "NODI_view": "fixed_660_gold",
        "weighting_basis": EAS_WEIGHTING_BASIS,
        "aperture_surrogate_mode": "nominal_width",
        "W_eff_surrogate_nm": 500.0,
        "delta_W_eff_surrogate_nm": 0.0,
        "source_geometry_descriptor_id": "descriptor-404-W500-D900",
        "source_geometry_descriptor_sha": GEOMETRY_DESCRIPTOR_SHA256,
        "descriptor_evidence_class": "nominal/design-state",
        "rank_source": EAS_RANK_SOURCE,
        "recommendation_eligible_rank_source": EAS_RECOMMENDATION_RANK_SOURCE,
        "guardrail_status": "recommendation_eligible",
        "eta_selected_proxy_under_surrogate": 0.2,
        "eta_all_proxy_under_surrogate": 0.3,
        "rank_under_surrogate": 1,
        "rank_flip_flag": "false",
        "candidate_family_flip_flag": "false",
        "eta_selected_relative_change": 0.0,
        "eta_all_relative_change": 0.0,
        "guardrail_status_change_flag": "false",
        "W_eff_mode_sensitivity_class": "stable",
        "solver_contract_trigger_flag": "false",
        "solver_contract_trigger_reason": "none",
        "not_true_W_eff": "true",
        "not_measured_geometry": "true",
        "not_optical_solver_output": "true",
        "not_fabrication_release": "true",
        "not_yield": "true",
        "not_winner": "true",
        "claim_boundary": EAS_CLAIM_BOUNDARY,
        "source_artifact": "exports/nodi_comsol_handoff_v1/rank.csv;roadmap/descriptor.csv",
        "source_sha256": "b" * 64,
    }
    row.update(overrides)
    return row


def _valid_eas_sidewall_v2_row(**overrides: object) -> dict[str, object]:
    row = _valid_eas_row(
        eas_mode="sidewall_aperture_surrogate_v2",
        aperture_surrogate_basis="center_accessible_geometry_proxy",
        aperture_surrogate_claim_level="surrogate_sensitivity_only",
        W_eff_optical_surrogate_nm=480.0,
        optical_solver_triggered="false",
        optical_solver_trigger_reason="none",
        optical_solver_trigger_is_result="false",
        optical_geometry_claim_level="surrogate",
        reference_field_model="geometry_scaled",
        reference_spatial_mode="cross_section_surrogate",
        reference_route="rectangular_width_depth_reference_proxy_under_trapezoid",
        illumination_mode="edge_illumination_surrogate",
        detector_operator_id="fixed_660_gold_detector_operator_v1",
        rank_under_surrogate="",
        not_qch_weighted="true",
        not_detection_probability="true",
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        cross_section_geometry_version="trapezoid_straight_sidewall_v1",
        geometry_runtime_binding_version="geometry_runtime_binding_manifest_v1",
        geometry_propagation_status="propagated",
        geometry_not_propagated_reasons="",
        **_sidewall_artifact_metadata_fields("NODI_EFFECTIVE_APERTURE_SIDEWALL_V2"),
        **_sidewall_acceptance_guard_fields(),
        **_sidewall_observation_cache_fields(),
        **_sidewall_runtime_propagation_guard_fields(),
        **_sidewall_descriptor_context_fields(),
    )
    row.update(overrides)
    return row


def _valid_sidewall_package_d_precheck_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "sidewall_package_d_precheck_version": "sidewall_package_d_precheck_v1",
        "target_artifact_family": "eas",
        "includes_trajectory_near_wall_metrics": "false",
        "package_A_validation_status": "pass",
        "package_B_validation_status": "pass",
        "package_C_validation_status": "not_applicable_for_this_artifact",
        "no_forbidden_claim_columns": "true",
        "no_rectangular_cache_reuse": "true",
        "no_comsol_context_grain_promotion": "true",
        "no_edge4_to_edge20_direct_mapping": "true",
        "no_D900_to_D1200_borrowing": "true",
        "no_auto_220_300nm_admission": "true",
        "package_d_precheck_status": "pass",
    }
    row.update(overrides)
    return row


def _valid_descriptor_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "route_geometry_id_comsol": "geom-a",
        "route_geometry_id_comsol_version": "route_geometry_id_comsol_v1_contract_20260616",
        "process_state": "nominal_smooth_geometry",
        "W_nominal_nm": 500.0,
        "width_group_um": 0.5,
        "D_nm": 900.0,
        "W_top_um": 0.5,
        "W_bottom_um": 0.25,
        "bottom_width_nm": 250.0,
        "D_inscribed_nm": 300.0,
        "min_aperture_nm": 250.0,
        "bottom_cd_bias_nm": "",
        "edge_lip_nm_per_side": "",
        "residue_thickness_nm": "",
        "roughness_rms_nm": "",
        "scallop_amplitude_nm": "",
        "rounded_corner_radius_nm": "",
        "claim_boundary": GEOMETRY_DESCRIPTOR_CLAIM_BOUNDARY,
    }
    row.update(overrides)
    return row


def _valid_descriptor_v2_row(**overrides: object) -> dict[str, object]:
    sidewall_deg = float(overrides.pop("sidewall_deg_comsol", 85.0))
    w_top_nm = float(overrides.pop("W_top_nm", 500.0))
    depth_nm = float(overrides.pop("D_nm", 900.0))
    w_bottom_unclipped_nm = w_top_nm - 2.0 * depth_nm / math.tan(
        math.radians(sidewall_deg)
    )
    w_bottom_runtime_clipped_nm = max(w_bottom_unclipped_nm, 0.0)
    closure_status = "open" if w_bottom_unclipped_nm > 0.0 else "geometry_closed"
    min_aperture_descriptor_nm = min(w_bottom_unclipped_nm, 300.0)
    row = _valid_descriptor_row(
        D_nm=depth_nm,
        W_top_um=w_top_nm / 1000.0,
        W_bottom_um=w_bottom_unclipped_nm / 1000.0,
        bottom_width_nm=w_bottom_unclipped_nm,
        D_inscribed_nm=300.0,
        min_aperture_nm=min_aperture_descriptor_nm,
        sidewall_angle_convention="sidewall_angle_from_substrate_plane_90deg_vertical",
        sidewall_deg_comsol=sidewall_deg,
        sidewall_taper_angle_deg_nodi=90.0 - sidewall_deg,
        angle_conversion_formula_id="sidewall_from_horizontal_to_taper_from_vertical_v1",
        W_top_nm=w_top_nm,
        W_top_semantics="comsol_descriptor",
        W_bottom_unclipped_nm=w_bottom_unclipped_nm,
        W_bottom_runtime_clipped_nm=w_bottom_runtime_clipped_nm,
        closure_status=closure_status,
        closure_policy="preserve_unclipped_descriptor",
        runtime_guard_status="none",
        min_aperture_descriptor_nm=min_aperture_descriptor_nm,
    )
    row.update(overrides)
    return row


def _assert_has_issue(issues: list[str], rule_id: str) -> None:
    assert any(rule_id in issue for issue in issues), issues


def test_comsol_v4_default_context_is_readonly_and_out_of_scope_for_dry_optical() -> None:
    context = default_comsol_v4_readonly_context()

    assert context["v4_assumption_set_id"] == COMSOL_V4_ASSUMPTION_SET_ID
    assert context["v4_assumption_set_sha256"] == COMSOL_V4_ASSUMPTION_SET_SHA256
    assert context["v4_scope"] == COMSOL_V4_SCOPE_OUT_OF_SCOPE_DRY_OPTICAL_SURROGATE
    assert context["nodi_production_ingestion_allowed"] is False
    assert context["nodi_count_prediction_allowed"] is False
    assert context["nodi_optical_update_allowed"] is False
    assert context["comsol_launch_authorized_now"] is False
    assert validate_comsol_v4_readonly_context(context) == []


def test_comsol_v4_wet_context_requires_explicit_unbound_or_bound_identities() -> None:
    context = default_comsol_v4_readonly_context(
        v4_scope=COMSOL_V4_SCOPE_WET_SURFACE_CONTEXT
    )

    assert context["scenario_id"] == COMSOL_V4_UNBOUND_REQUIRED
    assert context["roughness_state_id"] == COMSOL_V4_UNBOUND_REQUIRED
    assert validate_comsol_v4_readonly_context(context) == []


def test_comsol_v4_context_rejects_production_promotion_or_hash_drift() -> None:
    context = default_comsol_v4_readonly_context()
    context["v4_assumption_set_sha256"] = "0" * 64
    context["nodi_production_ingestion_allowed"] = True

    issues = validate_comsol_v4_readonly_context(context)

    assert any("sha256 drifted" in issue for issue in issues)
    assert any("nodi_production_ingestion_allowed must remain false" in issue for issue in issues)


def test_position_response_accepts_neutral_response_surface_row() -> None:
    assert validate_position_response_surface_rows([_valid_prs_row()]) == []


def test_position_response_accepts_sidewall_v2_geometry_fields_when_consistent() -> None:
    assert validate_position_response_surface_rows([_valid_prs_sidewall_v2_row()]) == []


def test_position_response_sidewall_v2_keeps_ideal_rectangle_context_path() -> None:
    row = _without_sidewall_descriptor_context(
        _valid_prs_sidewall_v2_row(
            channel_cross_section_model="ideal_rectangle",
            cross_section_geometry_version="ideal_rectangle_v1",
            sampler_geometry_model="rectangle_accessible_area_v1",
            **_sidewall_observation_cache_fields("ideal_rectangle"),
        )
    )

    assert validate_position_response_surface_rows([row]) == []


def test_position_response_sidewall_v2_requires_complete_geometry_fields() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_row(channel_cross_section_model="trapezoid_tapered_sidewalls")]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_requires_runtime_binding_version() -> None:
    row = _valid_prs_sidewall_v2_row()
    del row["geometry_runtime_binding_version"]

    issues = validate_position_response_surface_rows([row])

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_requires_artifact_metadata() -> None:
    row = _valid_prs_sidewall_v2_row()
    del row["artifact_id"]

    issues = validate_position_response_surface_rows([row])

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_wrong_artifact_version() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_sidewall_v2_row(artifact_version="NODI_POSITION_RESPONSE_SURFACE_V1")]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_requires_acceptance_guards() -> None:
    row = _valid_prs_sidewall_v2_row()
    del row["not_accepted_for_runtime_config"]

    issues = validate_position_response_surface_rows([row])

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_formula_use_acceptance() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_sidewall_v2_row(not_accepted_for_formula_use="false")]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_promoted_roadmap_status() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_sidewall_v2_row(roadmap_status="production_ready")]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_rectangular_sampler_under_trapezoid() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_sidewall_v2_row(sampler_geometry_model="rectangular_half_span_v1")]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_requires_runtime_propagation_models() -> None:
    row = _valid_prs_sidewall_v2_row()
    del row["wall_distance_model"]
    del row["reference_spatial_mode"]

    issues = validate_position_response_surface_rows([row])

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_rectangular_flow_profile() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_sidewall_v2_row(flow_profile_model="rect_series")]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_rectangular_wall_distance_model() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_sidewall_v2_row(wall_distance_model="rectangular_half_span_gap_v1")]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_blocked_bin_neighbor_fill() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                bin_accessible="false",
                bin_accessible_area_fraction=0.0,
                bin_particle_center_support_status="blocked",
                blocked_reason="",
                decision_use_allowed="true",
                neighbor_fill_used="true",
            )
        ]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_blocked_bin_numeric_response() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                bin_accessible="false",
                bin_accessible_area_fraction=0.0,
                bin_particle_center_support_status="blocked",
                blocked_reason="steric_blocked",
                decision_use_allowed="false",
                steric_support_source="not_available",
                response_value=0.42,
            )
        ]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_allows_blocked_bin_response_token() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                bin_accessible="false",
                bin_accessible_area_fraction=0.0,
                bin_particle_center_support_status="blocked",
                blocked_reason="steric_blocked",
                decision_use_allowed="false",
                steric_support_source="not_available",
                response_value="blocked",
            )
        ]
    )

    assert issues == []


def test_position_response_sidewall_v2_rejects_incomplete_local_geometry() -> None:
    row = _valid_prs_sidewall_v2_row()
    del row["x_left_nm"]
    del row["nearest_wall_id"]

    issues = validate_position_response_surface_rows([row])

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_requires_local_normalized_coordinates() -> None:
    row = _valid_prs_sidewall_v2_row()
    del row["x_local_norm"]
    del row["u_norm"]

    issues = validate_position_response_surface_rows([row])

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_inconsistent_local_geometry() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                x_left_nm=-200.0,
                x_right_nm=200.0,
                local_width_nm=421.0,
                nearest_wall_id="diagonal",
            )
        ]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_inconsistent_normalized_coordinates() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                x_nm=100.0,
                x_center_nm=0.0,
                local_half_width_nm=200.0,
                x_local_norm=0.0,
                u_nm=600.0,
                D_nm=900.0,
                u_norm=0.5,
            )
        ]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_wrong_nearest_wall_distance() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                d_top_nm=10.0,
                d_nearest_wall_nm=171.0,
                nearest_wall_id="left_side",
            )
        ]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_surface_gap_mismatch() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_sidewall_v2_row(surface_gap_for_particle_nm=100.0)]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_requires_source_geometry_descriptor_id() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_sidewall_v2_row(source_geometry_descriptor_id="")]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_requires_source_geometry_descriptor_sha() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_sidewall_v2_row(source_geometry_descriptor_sha="not-a-sha")]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_requires_descriptor_context_fields() -> None:
    row = _valid_prs_sidewall_v2_row()
    del row["sidewall_angle_convention"]

    issues = validate_position_response_surface_rows([row])

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_descriptor_angle_mismatch() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_sidewall_v2_row(sidewall_taper_angle_deg_nodi=85.0)]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_requires_observation_signature() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_sidewall_v2_row(observation_signature="")]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_rectangular_cache_signature() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                **_sidewall_observation_cache_fields("ideal_rectangle"),
            )
        ]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_requires_signature_guard_fragments() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                observation_signature=(
                    "channel_cross_section_model=trapezoid_tapered_sidewalls"
                    "|sidewall_taper_angle_deg=5.000000000e+00"
                    f"|geometry_profile_sha256={GEOMETRY_DESCRIPTOR_SHA256}"
                )
            )
        ]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_requires_runtime_guard_columns() -> None:
    row = _valid_prs_sidewall_v2_row()
    del row["fluidic_network_not_qch_weighted"]

    issues = validate_position_response_surface_rows([row])

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_runtime_guard_claim_promotion() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                not_clogging_rate="false",
                surface_charge_transport_claim_level="calibrated_transport_result",
            )
        ]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_requires_geometry_profile_sha() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_sidewall_v2_row(geometry_profile_sha256="not-a-sha")]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_D900_to_D1200_source_borrowing() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                route_id_nodi="404/W500/D1200",
                D_nm=1200,
                source_D_nm=900,
                **_sidewall_descriptor_context_fields(depth_nm=1200.0),
            )
        ]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_edge4_to_edge20_direct_mapping() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                source_bin_basis="edge_norm_1d_edge4",
                bin_basis="edge_norm_1d_edge20",
            )
        ]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_non_propagated_open_decision_row() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                geometry_propagation_status="not_propagated",
                geometry_not_propagated_reasons="geometry_not_propagated_to_sampler",
            )
        ]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_keeps_non_propagated_audit_row_blocked() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                geometry_propagation_status="not_propagated",
                geometry_not_propagated_reasons="geometry_not_propagated_to_sampler",
                bin_accessible="false",
                bin_accessible_area_fraction=0.0,
                bin_particle_center_support_status="blocked",
                blocked_reason="geometry_not_propagated_to_sampler",
                decision_use_allowed="false",
                steric_support_source="not_available",
            )
        ]
    )

    assert issues == []


def test_position_response_sidewall_v2_rejects_closed_geometry_as_propagated() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                **_sidewall_descriptor_context_fields(depth_nm=900.0, sidewall_deg=70.0)
            )
        ]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_closure_guard_mismatch() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                closure_status="near_closed",
                runtime_guard_status="none",
            )
        ]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_requires_large_tail_support_guard() -> None:
    row = _valid_prs_sidewall_v2_row()
    del row["tail_particle_auto_admitted"]
    del row["steric_support_source"]

    issues = validate_position_response_surface_rows([row])

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_auto_tail_admission() -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_sidewall_v2_row(
                tail_particle_auto_admitted="true",
                steric_support_source="not_available",
            )
        ]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_sidewall_v2_rejects_particle_radius_diameter_mismatch() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_sidewall_v2_row(diameter_nm=220, particle_radius_nm=100.0)]
    )

    _assert_has_issue(issues, "PRS-SIDEWALL-V2")


def test_position_response_rejects_qch_flow_on_production_row() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_row(flow_condition_id=QCH_FLOW_CONDITION_ID)]
    )

    _assert_has_issue(issues, "PRS-V29")
    _assert_has_issue(issues, "PRS-V30")


def test_position_response_rejects_qch_row_scope_in_production_table() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_row(row_scope="qch_provenance_reference")]
    )

    _assert_has_issue(issues, "PRS-V28")


def test_position_response_rejects_comsol_transport_distribution_basis() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_row(position_distribution_basis="comsol_transported_distribution")]
    )

    _assert_has_issue(issues, "PRS-V32")
    _assert_has_issue(issues, "PRS-V39")


def test_position_response_rejects_v4_event_rate_or_pass_probability_columns() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_row(v4_event_rate="1.0", wet_pass_probability="0.2")]
    )

    _assert_has_issue(issues, "PRS-V41")


def test_position_response_rejects_exact_sidewall_claim_columns() -> None:
    issues = validate_position_response_surface_rows(
        [_valid_prs_row(q_ch="1.0", route_score="0.7")]
    )

    _assert_has_issue(issues, "PRS-V41")


@pytest.mark.parametrize(
    ("n_events_bin", "status", "decision_use", "expected_rule"),
    [
        (0, "adequate", "false", "PRS-V17"),
        (50, "sparse", "true", "PRS-V21"),
        (300, "guardrail_blocked", "true", "PRS-V16"),
    ],
)
def test_position_response_sample_status_and_guardrail_separation(
    n_events_bin: int,
    status: str,
    decision_use: str,
    expected_rule: str,
) -> None:
    issues = validate_position_response_surface_rows(
        [
            _valid_prs_row(
                n_events_bin=n_events_bin,
                bin_sample_status=status,
                sparse_bin_flag=str(n_events_bin < 100).lower(),
                decision_use_allowed=decision_use,
            )
        ]
    )

    _assert_has_issue(issues, expected_rule)


def test_position_response_rejects_500_nm_eta_response_rows() -> None:
    issues = validate_position_response_surface_rows([_valid_prs_row(diameter_nm=500)])

    _assert_has_issue(issues, "PRS-V05")


def test_position_response_smoke_manifest_is_design_only_not_production() -> None:
    rows = position_response_smoke_manifest_rows()

    assert rows[0]["artifact"] == POSITION_RESPONSE_ARTIFACT
    assert {row["execution_status"] for row in rows} == {"DESIGN_ONLY_NOT_EXECUTED"}
    assert any(row["smoke_id"] == "PRS-SMOKE-QCH-NEGATIVE" for row in rows)


def test_effective_aperture_accepts_surrogate_row() -> None:
    assert validate_effective_aperture_surrogate_rows([_valid_eas_row()]) == []


def test_effective_aperture_accepts_sidewall_v2_fields_when_consistent() -> None:
    assert validate_effective_aperture_surrogate_rows([_valid_eas_sidewall_v2_row()]) == []


def test_effective_aperture_sidewall_v2_requires_solver_trigger_result_guard() -> None:
    row = _valid_eas_sidewall_v2_row()
    del row["optical_solver_trigger_is_result"]

    issues = validate_effective_aperture_surrogate_rows([row])

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_requires_artifact_metadata() -> None:
    row = _valid_eas_sidewall_v2_row()
    del row["artifact_created_utc"]

    issues = validate_effective_aperture_surrogate_rows([row])

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_rejects_wrong_artifact_version() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [_valid_eas_sidewall_v2_row(artifact_version="NODI_EFFECTIVE_APERTURE_SURROGATE_V1")]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_requires_solver_trigger_fields() -> None:
    row = _valid_eas_sidewall_v2_row()
    del row["optical_solver_triggered"]
    del row["optical_solver_trigger_reason"]

    issues = validate_effective_aperture_surrogate_rows([row])

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_rejects_solver_reason_without_trigger() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_sidewall_v2_row(
                optical_solver_triggered="false",
                optical_solver_trigger_reason="geometry_complexity",
            )
        ]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_requires_optical_geometry_claim_level() -> None:
    row = _valid_eas_sidewall_v2_row()
    del row["optical_geometry_claim_level"]

    issues = validate_effective_aperture_surrogate_rows([row])

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_rejects_optical_solver_output_claim() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_sidewall_v2_row(
                optical_geometry_claim_level="optical_solver_output",
            )
        ]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_accepts_solver_required_trigger() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_sidewall_v2_row(
                optical_solver_triggered="true",
                optical_solver_trigger_reason="geometry_complexity",
                optical_geometry_claim_level="solver_required",
            )
        ]
    )

    assert issues == []


def test_effective_aperture_sidewall_v2_requires_solver_required_when_triggered() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_sidewall_v2_row(
                optical_solver_triggered="true",
                optical_solver_trigger_reason="geometry_complexity",
                optical_geometry_claim_level="surrogate",
            )
        ]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_requires_surrogate_when_not_triggered() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_sidewall_v2_row(
                optical_solver_triggered="false",
                optical_solver_trigger_reason="none",
                optical_geometry_claim_level="solver_required",
            )
        ]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_requires_runtime_geometry_context() -> None:
    row = _valid_eas_sidewall_v2_row()
    del row["channel_cross_section_model"]
    del row["geometry_runtime_binding_version"]

    issues = validate_effective_aperture_surrogate_rows([row])

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_requires_reference_context() -> None:
    row = _valid_eas_sidewall_v2_row()
    del row["reference_field_model"]
    del row["detector_operator_id"]

    issues = validate_effective_aperture_surrogate_rows([row])

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_rejects_blank_reference_context() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [_valid_eas_sidewall_v2_row(reference_spatial_mode="")]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_requires_acceptance_guards() -> None:
    row = _valid_eas_sidewall_v2_row()
    del row["not_accepted_for_production"]

    issues = validate_effective_aperture_surrogate_rows([row])

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_rejects_runtime_config_acceptance() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [_valid_eas_sidewall_v2_row(not_accepted_for_runtime_config="false")]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_rejects_promoted_roadmap_status() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [_valid_eas_sidewall_v2_row(roadmap_status="production_ready")]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_rejects_solver_trigger_as_result() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_sidewall_v2_row(
                aperture_surrogate_claim_level="optical_solver_output",
                optical_solver_trigger_is_result="true",
            )
        ]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_requires_specific_surrogate_width() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [_valid_eas_sidewall_v2_row(W_eff_optical_surrogate_nm="")]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_rejects_rank_promotion() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [_valid_eas_sidewall_v2_row(rank_under_surrogate=1)]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_rejects_exact_claim_columns() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_sidewall_v2_row(
                W_eff=500.0,
                route_score=0.7,
                winner="true",
            )
        ]
    )

    _assert_has_issue(issues, "EAS-V26")


def test_effective_aperture_sidewall_v2_requires_no_probability_claim_guards() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_sidewall_v2_row(
                not_qch_weighted="false",
                not_detection_probability="false",
            )
        ]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_requires_source_geometry_descriptor_id() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [_valid_eas_sidewall_v2_row(source_geometry_descriptor_id="")]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_requires_source_geometry_descriptor_sha() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [_valid_eas_sidewall_v2_row(source_geometry_descriptor_sha="not-a-sha")]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_requires_descriptor_context_fields() -> None:
    row = _valid_eas_sidewall_v2_row()
    del row["sidewall_angle_convention"]

    issues = validate_effective_aperture_surrogate_rows([row])

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_rejects_descriptor_angle_mismatch() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [_valid_eas_sidewall_v2_row(sidewall_taper_angle_deg_nodi=85.0)]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_rejects_closed_geometry_as_propagated() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_sidewall_v2_row(
                **_sidewall_descriptor_context_fields(depth_nm=900.0, sidewall_deg=70.0)
            )
        ]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_requires_geometry_profile_sha() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [_valid_eas_sidewall_v2_row(geometry_profile_sha256="not-a-sha")]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_requires_observation_signature() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [_valid_eas_sidewall_v2_row(observation_signature="")]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_rejects_rectangular_cache_signature() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_sidewall_v2_row(
                **_sidewall_observation_cache_fields("ideal_rectangle"),
            )
        ]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_requires_signature_guard_fragments() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_sidewall_v2_row(
                observation_signature=(
                    "channel_cross_section_model=trapezoid_tapered_sidewalls"
                    "|sidewall_taper_angle_deg=5.000000000e+00"
                    f"|geometry_profile_sha256={GEOMETRY_DESCRIPTOR_SHA256}"
                )
            )
        ]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_requires_runtime_guard_columns() -> None:
    row = _valid_eas_sidewall_v2_row()
    del row["geometry_not_propagated_to_electrokinetic_transport"]

    issues = validate_effective_aperture_surrogate_rows([row])

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_rejects_runtime_guard_claim_promotion() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_sidewall_v2_row(
                fluidic_network_not_qch_weighted="false",
                hydraulic_resistance_claim_level="trapezoid_poiseuille_result",
            )
        ]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_effective_aperture_sidewall_v2_rejects_source_route_borrowing() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_sidewall_v2_row(
                route_id_nodi="404/W500/D1200",
                D_nm=1200,
                source_route_id_nodi="404/W500/D900",
                **_sidewall_descriptor_context_fields(depth_nm=1200.0),
            )
        ]
    )

    _assert_has_issue(issues, "EAS-SIDEWALL-V2")


def test_sidewall_package_d_precheck_accepts_eas_without_near_wall_metrics() -> None:
    assert validate_sidewall_package_d_precheck_rows([_valid_sidewall_package_d_precheck_row()]) == []


def test_sidewall_package_d_precheck_requires_package_a_and_b_pass() -> None:
    issues = validate_sidewall_package_d_precheck_rows(
        [
            _valid_sidewall_package_d_precheck_row(
                package_A_validation_status="blocked",
                package_B_validation_status="blocked",
            )
        ]
    )

    _assert_has_issue(issues, "SIDEWALL-D-PRECHECK-V02")


def test_sidewall_package_d_precheck_requires_package_c_for_near_wall_metrics() -> None:
    issues = validate_sidewall_package_d_precheck_rows(
        [
            _valid_sidewall_package_d_precheck_row(
                target_artifact_family="prs",
                includes_trajectory_near_wall_metrics="true",
                package_C_validation_status="not_applicable_for_this_artifact",
            )
        ]
    )

    _assert_has_issue(issues, "SIDEWALL-D-PRECHECK-V03")


def test_sidewall_package_d_precheck_accepts_near_wall_metrics_after_package_c_pass() -> None:
    issues = validate_sidewall_package_d_precheck_rows(
        [
            _valid_sidewall_package_d_precheck_row(
                target_artifact_family="prs",
                includes_trajectory_near_wall_metrics="true",
                package_C_validation_status="pass",
            )
        ]
    )

    assert issues == []


def test_sidewall_package_d_precheck_rejects_forbidden_gate_false() -> None:
    issues = validate_sidewall_package_d_precheck_rows(
        [_valid_sidewall_package_d_precheck_row(no_D900_to_D1200_borrowing="false")]
    )

    _assert_has_issue(issues, "SIDEWALL-D-PRECHECK-V04")
    _assert_has_issue(issues, "SIDEWALL-D-PRECHECK-V05")


def test_sidewall_package_d_precheck_scans_forbidden_columns_even_when_flag_passes() -> None:
    issues = validate_sidewall_package_d_precheck_rows(
        [_valid_sidewall_package_d_precheck_row(route_score=1.0)]
    )

    _assert_has_issue(issues, "SIDEWALL-D-PRECHECK-V06")


def test_effective_aperture_rejects_old_w_eff_field_name() -> None:
    row = _valid_eas_row(W_eff_nm=500.0)

    issues = validate_effective_aperture_surrogate_rows([row])

    _assert_has_issue(issues, "EAS-V03")


def test_effective_aperture_rejects_exact_sidewall_claim_columns() -> None:
    row = _valid_eas_row(W_eff=500.0, JRC="candidate")

    issues = validate_effective_aperture_surrogate_rows([row])

    _assert_has_issue(issues, "EAS-V26")


def test_effective_aperture_rejects_true_weff_or_solver_claim_drift() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_row(
                not_true_W_eff="false",
                not_optical_solver_output="false",
                claim_boundary="true_optical_width_claim",
            )
        ]
    )

    _assert_has_issue(issues, "EAS-V19")
    _assert_has_issue(issues, "EAS-V21")
    _assert_has_issue(issues, "EAS-V03")


@pytest.mark.parametrize(
    "claim_field",
    ["measured_geometry", "optical_solver_output", "fabrication_release", "p3_conclusion"],
)
def test_effective_aperture_rejects_extra_positive_claim_columns(claim_field: str) -> None:
    issues = validate_effective_aperture_surrogate_rows([_valid_eas_row(**{claim_field: "true"})])

    _assert_has_issue(issues, "EAS-V26")


def test_effective_aperture_rejects_v4_clogging_or_runtime_promotion_columns() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [_valid_eas_row(clogging_probability="0.1", runtime_configuration="v4")]
    )

    _assert_has_issue(issues, "EAS-V26")


def test_effective_aperture_rejects_stage1_detector_identity_rank_source() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [_valid_eas_row(rank_source="stage1_detector_identity_rank.csv")]
    )

    _assert_has_issue(issues, "EAS-V13")
    _assert_has_issue(issues, "EAS-V15")


def test_effective_aperture_nonpositive_min_aperture_keeps_proxy_blank() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_row(
                aperture_surrogate_mode="min_aperture_conservative",
                W_eff_surrogate_nm=-5.0,
                delta_W_eff_surrogate_nm=-505.0,
                eta_selected_proxy_under_surrogate="",
                eta_all_proxy_under_surrogate="",
                rank_under_surrogate="",
                W_eff_mode_sensitivity_class="solver_required",
                solver_contract_trigger_flag="true",
                solver_contract_trigger_reason="nonpositive_surrogate_aperture",
            )
        ]
    )

    assert issues == []


def test_effective_aperture_rejects_nonpositive_min_aperture_proxy_invention() -> None:
    issues = validate_effective_aperture_surrogate_rows(
        [
            _valid_eas_row(
                aperture_surrogate_mode="min_aperture_conservative",
                W_eff_surrogate_nm=-5.0,
                delta_W_eff_surrogate_nm=-505.0,
                eta_selected_proxy_under_surrogate=0.01,
                eta_all_proxy_under_surrogate="",
                rank_under_surrogate="",
            )
        ]
    )

    _assert_has_issue(issues, "EAS-V10")


def test_geometry_descriptor_accepts_nominal_surrogate_descriptor_rules() -> None:
    assert validate_geometry_descriptor_rows([_valid_descriptor_row()]) == []


def test_geometry_descriptor_accepts_sidewall_v2_fields_when_consistent() -> None:
    assert validate_geometry_descriptor_rows([_valid_descriptor_v2_row()]) == []


def test_geometry_descriptor_v2_requires_angle_convention() -> None:
    row = _valid_descriptor_v2_row()
    del row["sidewall_angle_convention"]

    issues = validate_geometry_descriptor_rows([row])

    _assert_has_issue(issues, "DESC-V2")


def test_geometry_descriptor_v2_rejects_angle_conversion_mismatch() -> None:
    issues = validate_geometry_descriptor_rows(
        [_valid_descriptor_v2_row(sidewall_taper_angle_deg_nodi=85.0)]
    )

    _assert_has_issue(issues, "DESC-V2")


def test_geometry_descriptor_v2_rejects_open_status_for_nonpositive_bottom() -> None:
    issues = validate_geometry_descriptor_rows(
        [
            _valid_descriptor_v2_row(
                sidewall_deg_comsol=70.0,
                D_nm=700.0,
                closure_status="open",
            )
        ]
    )

    _assert_has_issue(issues, "DESC-V2")


def test_geometry_descriptor_v2_runtime_top_semantics_requires_runtime_aperture() -> None:
    issues = validate_geometry_descriptor_rows(
        [_valid_descriptor_v2_row(W_top_semantics="runtime_top_aperture")]
    )

    _assert_has_issue(issues, "DESC-V2")


def test_geometry_descriptor_v2_accepts_bound_runtime_top_aperture() -> None:
    assert (
        validate_geometry_descriptor_rows(
            [
                _valid_descriptor_v2_row(
                    W_top_semantics="runtime_top_aperture",
                    runtime_top_aperture_nm=500.0,
                )
            ]
        )
        == []
    )


def test_geometry_descriptor_v2_rejects_runtime_top_aperture_mismatch() -> None:
    issues = validate_geometry_descriptor_rows(
        [
            _valid_descriptor_v2_row(
                W_top_semantics="runtime_top_aperture",
                runtime_top_aperture_nm=480.0,
            )
        ]
    )

    _assert_has_issue(issues, "DESC-V2")


def test_geometry_descriptor_v2_rejects_runtime_clipped_bottom_mismatch() -> None:
    issues = validate_geometry_descriptor_rows(
        [
            _valid_descriptor_v2_row(
                sidewall_deg_comsol=70.0,
                D_nm=700.0,
                W_bottom_runtime_clipped_nm=50.0,
            )
        ]
    )

    _assert_has_issue(issues, "DESC-V2")


def test_geometry_descriptor_v2_rejects_clipped_negative_min_aperture_descriptor() -> None:
    issues = validate_geometry_descriptor_rows(
        [
            _valid_descriptor_v2_row(
                sidewall_deg_comsol=70.0,
                D_nm=700.0,
                min_aperture_nm=0.0,
                min_aperture_descriptor_nm=0.0,
            )
        ]
    )

    _assert_has_issue(issues, "DESC-V2")


def test_geometry_descriptor_v2_rejects_min_aperture_passability_evidence() -> None:
    issues = validate_geometry_descriptor_rows(
        [
            _valid_descriptor_v2_row(
                min_aperture_descriptor_passability_evidence="particle_admitted"
            )
        ]
    )

    _assert_has_issue(issues, "DESC-V2")


def test_geometry_descriptor_v2_rejects_unbacked_measured_geometry_claim() -> None:
    issues = validate_geometry_descriptor_rows(
        [_valid_descriptor_v2_row(geometry_claim_level="measured_geometry")]
    )

    _assert_has_issue(issues, "DESC-V2")


def test_geometry_descriptor_v2_accepts_validated_measured_geometry_metadata() -> None:
    assert (
        validate_geometry_descriptor_rows(
            [
                _valid_descriptor_v2_row(
                    geometry_claim_level="measured_geometry",
                    metrology_status="validated",
                    not_measured_geometry="false",
                    geometry_profile_source="fibsem",
                    geometry_profile_sha256="a" * 64,
                    measured_profile_path="profiles/fibsem_sidewall.csv",
                )
            ]
        )
        == []
    )


def test_geometry_descriptor_v2_rejects_comsol_descriptor_as_measured_profile() -> None:
    issues = validate_geometry_descriptor_rows(
        [
            _valid_descriptor_v2_row(
                geometry_claim_level="measured_geometry",
                metrology_status="validated",
                not_measured_geometry="false",
                geometry_profile_source="comsol_descriptor",
                geometry_profile_sha256="a" * 64,
                measured_profile_path="profiles/fibsem_sidewall.csv",
            )
        ]
    )

    _assert_has_issue(issues, "DESC-V2")


def test_geometry_descriptor_rejects_exact_sidewall_claim_columns() -> None:
    issues = validate_geometry_descriptor_rows(
        [_valid_descriptor_row(W_eff=500.0, route_score=0.7)]
    )

    _assert_has_issue(issues, "EAS-V06")


def test_geometry_descriptor_rejects_clipped_negative_min_aperture() -> None:
    issues = validate_geometry_descriptor_rows(
        [
            _valid_descriptor_row(
                W_bottom_um=-0.01,
                bottom_width_nm=-10.0,
                D_inscribed_nm=300.0,
                min_aperture_nm=0.0,
            )
        ]
    )

    _assert_has_issue(issues, "EAS-V09")
    _assert_has_issue(issues, "EAS-V10")


def test_geometry_descriptor_rejects_wrong_route_geometry_version() -> None:
    issues = validate_geometry_descriptor_rows(
        [_valid_descriptor_row(route_geometry_id_comsol_version="wrong_version")]
    )

    _assert_has_issue(issues, "EAS-V06")


def test_geometry_descriptor_rejects_unavailable_fields_as_zero() -> None:
    issues = validate_geometry_descriptor_rows([_valid_descriptor_row(roughness_rms_nm=0)])

    _assert_has_issue(issues, "EAS-V11")


def test_effective_aperture_smoke_manifest_is_not_final_route_decision() -> None:
    rows = effective_aperture_smoke_manifest_rows()

    assert {row["execution_status"] for row in rows} == {"DESIGN_ONLY_NOT_EXECUTED"}
    assert rows[0]["allowed_output_status"] == "smoke_only_not_final_route_decision"
    assert rows[0]["claim_boundary"] == EAS_CLAIM_BOUNDARY


def test_design_only_smoke_manifest_writer_outputs_non_executable_bundle(tmp_path: Path) -> None:
    metadata = write_design_only_smoke_manifest_bundle(tmp_path)

    prs_path = tmp_path / PRS_SMOKE_MANIFEST_FILENAME
    eas_path = tmp_path / EAS_SMOKE_MANIFEST_FILENAME
    index_path = tmp_path / NEXT_ARTIFACTS_SMOKE_INDEX_FILENAME
    metadata_path = tmp_path / NEXT_ARTIFACTS_SMOKE_METADATA_FILENAME
    assert prs_path.exists()
    assert eas_path.exists()
    assert index_path.exists()
    assert metadata_path.exists()

    assert {row["execution_status"] for row in read_csv_rows(prs_path)} == {
        "DESIGN_ONLY_NOT_EXECUTED"
    }
    assert {row["execution_status"] for row in read_csv_rows(eas_path)} == {
        "DESIGN_ONLY_NOT_EXECUTED"
    }
    assert {row["execution_status"] for row in read_csv_rows(index_path)} == {
        "DESIGN_ONLY_NOT_EXECUTED"
    }
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert payload["no_runner_execution"] is True
    assert payload["no_smoke_execution"] is True
    assert payload["no_production_artifact"] is True
    assert payload["not_true_W_eff"] is True
    assert metadata["status"] == "design_only_smoke_manifest_bundle_written"


def test_smoke_manifest_writer_cli_requires_execute(tmp_path: Path) -> None:
    output_dir = tmp_path / "blocked"
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/write_nodi_next_artifacts_smoke_manifests.py"),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "without --execute" in result.stderr
    assert not output_dir.exists()


def test_smoke_manifest_writer_cli_writes_design_only_bundle(tmp_path: Path) -> None:
    output_dir = tmp_path / "bundle"
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/write_nodi_next_artifacts_smoke_manifests.py"),
            "--execute",
            "--check-canonical-contracts",
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "NODI_NEXT_ARTIFACTS_SMOKE_MANIFESTS: PASS" in result.stdout
    assert (output_dir / PRS_SMOKE_MANIFEST_FILENAME).exists()
    assert (output_dir / EAS_SMOKE_MANIFEST_FILENAME).exists()
    payload = json.loads(
        (output_dir / NEXT_ARTIFACTS_SMOKE_METADATA_FILENAME).read_text(encoding="utf-8")
    )
    assert payload["no_comsol_run"] is True
    assert payload["no_joint_route_class_regeneration"] is True


def test_runner_preflight_report_passes_for_design_only_bundle(tmp_path: Path) -> None:
    smoke_dir = tmp_path / "smoke"
    preflight_dir = tmp_path / "preflight"
    write_design_only_smoke_manifest_bundle(smoke_dir)

    report = write_no_execution_runner_preflight_report(
        project_root=PROJECT_ROOT,
        smoke_manifest_dir=smoke_dir,
        output_dir=preflight_dir,
    )

    assert report["status"] == "PASS_NO_EXECUTION_IMPLEMENTATION_PREFLIGHT"
    assert report["issues"] == []
    assert report["no_runner_execution"] is True
    assert report["no_smoke_execution"] is True
    assert report["no_production_artifact"] is True
    assert (preflight_dir / NEXT_ARTIFACTS_RUNNER_PREFLIGHT_REPORT_FILENAME).exists()
    assert (preflight_dir / NEXT_ARTIFACTS_RUNNER_PREFLIGHT_ISSUES_FILENAME).exists()
    payload = json.loads(
        (preflight_dir / NEXT_ARTIFACTS_RUNNER_PREFLIGHT_REPORT_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert payload["status"] == "PASS_NO_EXECUTION_IMPLEMENTATION_PREFLIGHT"
    assert payload["not_optical_solver_output"] is True


def test_runner_preflight_report_blocks_missing_smoke_bundle(tmp_path: Path) -> None:
    report = write_no_execution_runner_preflight_report(
        project_root=PROJECT_ROOT,
        smoke_manifest_dir=tmp_path / "missing-smoke",
        output_dir=tmp_path / "preflight",
    )

    assert report["status"] == "BLOCKED_BEFORE_IMPLEMENTATION"
    assert any("missing" in issue for issue in report["issues"])
    assert report["no_runner_execution"] is True


def test_runner_preflight_cli_requires_execute(tmp_path: Path) -> None:
    smoke_dir = tmp_path / "smoke"
    output_dir = tmp_path / "blocked"
    write_design_only_smoke_manifest_bundle(smoke_dir)
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/write_nodi_next_artifacts_runner_preflight.py"),
            "--smoke-manifest-dir",
            str(smoke_dir),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "without --execute" in result.stderr
    assert not output_dir.exists()


def test_runner_preflight_cli_writes_no_execution_report(tmp_path: Path) -> None:
    smoke_dir = tmp_path / "smoke"
    output_dir = tmp_path / "preflight"
    write_design_only_smoke_manifest_bundle(smoke_dir)
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/write_nodi_next_artifacts_runner_preflight.py"),
            "--execute",
            "--smoke-manifest-dir",
            str(smoke_dir),
            "--geometry-descriptor",
            str(PROJECT_ROOT / "tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv"),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (
        "NODI_NEXT_ARTIFACTS_NO_EXECUTION_PREFLIGHT: "
        "PASS_NO_EXECUTION_IMPLEMENTATION_PREFLIGHT"
    ) in result.stdout
    payload = json.loads(
        (output_dir / NEXT_ARTIFACTS_RUNNER_PREFLIGHT_REPORT_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert payload["geometry_descriptor_status"] == "checked"
    assert payload["no_comsol_run"] is True
    assert payload["no_joint_route_class_regeneration"] is True


def test_plan_only_blueprint_rows_expand_smoke_scopes_without_execution() -> None:
    prs_rows = position_response_plan_blueprint_rows()
    eas_rows = effective_aperture_plan_blueprint_rows()

    assert len(prs_rows) == 62
    assert len(eas_rows) == 45
    assert {row["planned_execution_status"] for row in prs_rows} == {
        PLAN_ONLY_EXECUTION_STATUS
    }
    assert {row["planned_execution_status"] for row in eas_rows} == {
        PLAN_ONLY_EXECUTION_STATUS
    }
    assert {row["no_runner_execution"] for row in prs_rows + eas_rows} == {"true"}
    assert {row["no_production_artifact"] for row in prs_rows + eas_rows} == {"true"}
    assert not any("q_ch_eta" in field for row in prs_rows + eas_rows for field in row)


def test_plan_only_blueprint_writer_outputs_non_executable_bundle(tmp_path: Path) -> None:
    smoke_dir = tmp_path / "smoke"
    blueprint_dir = tmp_path / "blueprint"
    write_design_only_smoke_manifest_bundle(smoke_dir)

    metadata = write_plan_only_blueprint_bundle(
        smoke_manifest_dir=smoke_dir,
        output_dir=blueprint_dir,
    )

    prs_path = blueprint_dir / PRS_PLAN_BLUEPRINT_FILENAME
    eas_path = blueprint_dir / EAS_PLAN_BLUEPRINT_FILENAME
    index_path = blueprint_dir / NEXT_ARTIFACTS_PLAN_BLUEPRINT_INDEX_FILENAME
    metadata_path = blueprint_dir / NEXT_ARTIFACTS_PLAN_BLUEPRINT_METADATA_FILENAME
    assert prs_path.exists()
    assert eas_path.exists()
    assert index_path.exists()
    assert metadata_path.exists()
    assert {row["planned_execution_status"] for row in read_csv_rows(prs_path)} == {
        PLAN_ONLY_EXECUTION_STATUS
    }
    assert {row["planned_execution_status"] for row in read_csv_rows(eas_path)} == {
        PLAN_ONLY_EXECUTION_STATUS
    }
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert payload["status"] == "plan_only_blueprint_bundle_written"
    assert payload["no_smoke_execution"] is True
    assert payload["no_production_artifact"] is True
    assert payload["not_true_W_eff"] is True
    assert metadata["status"] == "plan_only_blueprint_bundle_written"
    assert validate_plan_only_blueprint_bundle(blueprint_dir) == []


def test_plan_only_blueprint_writer_blocks_invalid_smoke_bundle(tmp_path: Path) -> None:
    with pytest.raises(ContractValidationError) as exc_info:
        write_plan_only_blueprint_bundle(
            smoke_manifest_dir=tmp_path / "missing-smoke",
            output_dir=tmp_path / "blueprint",
        )

    assert any("missing" in issue for issue in exc_info.value.issues)


def test_plan_only_blueprint_cli_requires_execute(tmp_path: Path) -> None:
    smoke_dir = tmp_path / "smoke"
    output_dir = tmp_path / "blocked"
    write_design_only_smoke_manifest_bundle(smoke_dir)
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/write_nodi_next_artifacts_plan_blueprints.py"),
            "--smoke-manifest-dir",
            str(smoke_dir),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "without --execute" in result.stderr
    assert not output_dir.exists()


def test_plan_only_blueprint_cli_writes_blueprint_bundle(tmp_path: Path) -> None:
    smoke_dir = tmp_path / "smoke"
    output_dir = tmp_path / "blueprint"
    write_design_only_smoke_manifest_bundle(smoke_dir)
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/write_nodi_next_artifacts_plan_blueprints.py"),
            "--execute",
            "--check-canonical-contracts",
            "--smoke-manifest-dir",
            str(smoke_dir),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINTS: PASS" in result.stdout
    payload = json.loads(
        (output_dir / NEXT_ARTIFACTS_PLAN_BLUEPRINT_METADATA_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert payload["no_runner_execution"] is True
    assert payload["no_comsol_run"] is True


def test_authorization_gate_record_denies_runner_smoke_and_production(tmp_path: Path) -> None:
    smoke_dir = tmp_path / "smoke"
    preflight_dir = tmp_path / "preflight"
    blueprint_dir = tmp_path / "blueprint"
    gate_dir = tmp_path / "gate"
    write_design_only_smoke_manifest_bundle(smoke_dir)
    write_no_execution_runner_preflight_report(
        project_root=PROJECT_ROOT,
        smoke_manifest_dir=smoke_dir,
        output_dir=preflight_dir,
    )
    write_plan_only_blueprint_bundle(
        smoke_manifest_dir=smoke_dir,
        output_dir=blueprint_dir,
    )

    record = write_next_artifacts_runner_authorization_gate_record(
        project_root=PROJECT_ROOT,
        smoke_manifest_dir=smoke_dir,
        plan_blueprint_dir=blueprint_dir,
        preflight_report_path=preflight_dir / NEXT_ARTIFACTS_RUNNER_PREFLIGHT_REPORT_FILENAME,
        output_dir=gate_dir,
    )

    assert record["status"] == AUTHORIZATION_GATE_PASS_STATUS
    assert record["authorization_gate_decision"] == "not_authorized_pending_explicit_future_request"
    assert record["runner_implementation_authorized"] is False
    assert record["runner_execution_authorized"] is False
    assert record["bounded_smoke_execution_authorized"] is False
    assert record["production_generation_authorized"] is False
    assert record["qch_eta_authorized"] is False
    assert record["not_true_W_eff"] is True
    assert record["required_future_authorization_phrases"] == {
        "runner_implementation": RUNNER_IMPLEMENTATION_AUTHORIZATION_PHRASE,
        "bounded_smoke_execution": BOUNDED_SMOKE_AUTHORIZATION_PHRASE,
        "production_generation": PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
    }
    assert validate_next_artifacts_runner_authorization_gate_record(record) == []
    assert (gate_dir / NEXT_ARTIFACTS_AUTHORIZATION_GATE_RECORD_FILENAME).exists()
    assert (gate_dir / NEXT_ARTIFACTS_AUTHORIZATION_GATE_ISSUES_FILENAME).exists()

    payload = json.loads(
        (gate_dir / NEXT_ARTIFACTS_AUTHORIZATION_GATE_RECORD_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert payload["status"] == AUTHORIZATION_GATE_PASS_STATUS
    assert payload["no_smoke_execution"] is True
    assert payload["no_production_artifact"] is True


def test_authorization_gate_blocks_missing_plan_blueprint(tmp_path: Path) -> None:
    smoke_dir = tmp_path / "smoke"
    gate_dir = tmp_path / "gate"
    write_design_only_smoke_manifest_bundle(smoke_dir)

    record = write_next_artifacts_runner_authorization_gate_record(
        project_root=PROJECT_ROOT,
        smoke_manifest_dir=smoke_dir,
        plan_blueprint_dir=tmp_path / "missing-blueprint",
        output_dir=gate_dir,
    )

    assert record["status"] == "BLOCKED_AUTHORIZATION_GATE_INPUTS"
    assert any("missing" in issue for issue in record["issues"])
    assert record["runner_execution_authorized"] is False
    assert record["no_smoke_execution"] is True


def test_authorization_gate_cli_requires_confirm_write(tmp_path: Path) -> None:
    smoke_dir = tmp_path / "smoke"
    blueprint_dir = tmp_path / "blueprint"
    output_dir = tmp_path / "blocked"
    write_design_only_smoke_manifest_bundle(smoke_dir)
    write_plan_only_blueprint_bundle(
        smoke_manifest_dir=smoke_dir,
        output_dir=blueprint_dir,
    )
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/write_nodi_next_artifacts_authorization_gate.py"),
            "--smoke-manifest-dir",
            str(smoke_dir),
            "--plan-blueprint-dir",
            str(blueprint_dir),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "without --confirm-write" in result.stderr
    assert not output_dir.exists()


def test_authorization_gate_cli_writes_not_authorized_record(tmp_path: Path) -> None:
    smoke_dir = tmp_path / "smoke"
    preflight_dir = tmp_path / "preflight"
    blueprint_dir = tmp_path / "blueprint"
    output_dir = tmp_path / "gate"
    write_design_only_smoke_manifest_bundle(smoke_dir)
    write_no_execution_runner_preflight_report(
        project_root=PROJECT_ROOT,
        smoke_manifest_dir=smoke_dir,
        output_dir=preflight_dir,
    )
    write_plan_only_blueprint_bundle(
        smoke_manifest_dir=smoke_dir,
        output_dir=blueprint_dir,
    )

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/write_nodi_next_artifacts_authorization_gate.py"),
            "--confirm-write",
            "--smoke-manifest-dir",
            str(smoke_dir),
            "--plan-blueprint-dir",
            str(blueprint_dir),
            "--preflight-report",
            str(preflight_dir / NEXT_ARTIFACTS_RUNNER_PREFLIGHT_REPORT_FILENAME),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (
        "NODI_NEXT_ARTIFACTS_AUTHORIZATION_GATE: "
        "PASS_AUTHORIZATION_GATE_RECORD_NOT_AUTHORIZED"
    ) in result.stdout
    payload = json.loads(
        (output_dir / NEXT_ARTIFACTS_AUTHORIZATION_GATE_RECORD_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert payload["runner_implementation_authorized"] is False
    assert payload["bounded_smoke_execution_authorized"] is False


def test_future_authorization_phrase_guard_rejects_generic_continue() -> None:
    result = evaluate_next_artifacts_future_authorization_request(
        requested_action="runner_implementation",
        supplied_phrase="continue",
    )

    assert result["authorization_request_status"] == FUTURE_AUTHORIZATION_PHRASE_MISMATCH
    assert result["phrase_exact_match"] is False
    assert result["this_check_authorizes_runner_implementation"] is False
    assert result["this_check_authorizes_runner_execution"] is False
    assert result["no_smoke_execution"] is True
    assert result["no_production_artifact"] is True


def test_future_authorization_phrase_guard_requires_exact_phrase() -> None:
    result = evaluate_next_artifacts_future_authorization_request(
        requested_action="runner_implementation",
        supplied_phrase=f"{RUNNER_IMPLEMENTATION_AUTHORIZATION_PHRASE} please",
    )

    assert result["authorization_request_status"] == FUTURE_AUTHORIZATION_PHRASE_MISMATCH
    assert result["phrase_exact_match"] is False
    assert result["this_check_authorizes_runner_implementation"] is False


def test_future_authorization_phrase_guard_match_is_not_execution_authorization() -> None:
    result = evaluate_next_artifacts_future_authorization_request(
        requested_action="runner_implementation",
        supplied_phrase=RUNNER_IMPLEMENTATION_AUTHORIZATION_PHRASE,
    )

    assert (
        result["authorization_request_status"]
        == FUTURE_AUTHORIZATION_PHRASE_MATCH_RUNNER_IMPLEMENTATION
    )
    assert result["phrase_exact_match"] is True
    assert result["this_check_authorizes_runner_implementation"] is False
    assert result["this_check_authorizes_runner_execution"] is False
    assert result["this_check_authorizes_bounded_smoke_execution"] is False
    assert result["no_nodi_run"] is True
    assert result["no_comsol_run"] is True


@pytest.mark.parametrize(
    ("requested_action", "phrase"),
    [
        ("bounded_smoke_execution", BOUNDED_SMOKE_AUTHORIZATION_PHRASE),
        ("production_generation", PRODUCTION_GENERATION_AUTHORIZATION_PHRASE),
    ],
)
def test_future_authorization_phrase_guard_blocks_downstream_phrases_without_prerequisites(
    requested_action: str,
    phrase: str,
) -> None:
    result = evaluate_next_artifacts_future_authorization_request(
        requested_action=requested_action,
        supplied_phrase=phrase,
    )

    assert (
        result["authorization_request_status"]
        == FUTURE_AUTHORIZATION_PHRASE_MATCH_BLOCKED_NO_EXECUTION
    )
    assert result["phrase_exact_match"] is True
    assert result["this_check_authorizes_bounded_smoke_execution"] is False
    assert result["this_check_authorizes_production_generation"] is False
    assert result["this_check_authorizes_nodi_run"] is False
    assert result["this_check_authorizes_comsol_run"] is False


def test_future_authorization_phrase_cli_rejects_generic_continue() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/check_nodi_next_artifacts_future_authorization_phrase.py"
            ),
            "--requested-action",
            "runner_implementation",
            "--supplied-phrase",
            "continue",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["authorization_request_status"] == FUTURE_AUTHORIZATION_PHRASE_MISMATCH
    assert payload["phrase_exact_match"] is False
    assert payload["no_runner_execution"] is True


def test_future_authorization_phrase_cli_matches_runner_phrase_without_writing() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/check_nodi_next_artifacts_future_authorization_phrase.py"
            ),
            "--requested-action",
            "runner_implementation",
            "--supplied-phrase",
            RUNNER_IMPLEMENTATION_AUTHORIZATION_PHRASE,
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert (
        payload["authorization_request_status"]
        == FUTURE_AUTHORIZATION_PHRASE_MATCH_RUNNER_IMPLEMENTATION
    )
    assert payload["phrase_exact_match"] is True
    assert payload["this_check_authorizes_runner_execution"] is False
    assert payload["no_production_artifact"] is True


def test_future_authorization_phrase_cli_help_has_no_write_surface() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/check_nodi_next_artifacts_future_authorization_phrase.py"
            ),
            "--help",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--requested-action" in result.stdout
    assert "--supplied-phrase" in result.stdout
    assert "--gate-record" in result.stdout
    assert "--output-dir" not in result.stdout
    assert "--confirm-write" not in result.stdout
    assert "--execute" not in result.stdout


def test_position_response_runner_launch_plan_is_implementation_only() -> None:
    plan = build_position_response_runner_launch_plan()

    assert plan["runner_implementation_status"] == RUNNER_IMPLEMENTATION_READY_STATUS
    assert plan["runner_execution_status"] == "NOT_EXECUTED"
    assert plan["runner_implementation_authorized_by_phrase"] is True
    assert plan["runner_execution_authorized"] is False
    assert plan["bounded_smoke_execution_authorized"] is False
    assert plan["production_generation_authorized"] is False
    assert plan["no_smoke_execution"] is True
    assert plan["no_production_artifact"] is True
    assert plan["planned_row_arithmetic"]["p1_preferred_expected_rows"] == 60710
    assert plan["planned_row_arithmetic"]["p2_diagnostic_trap_expected_rows"] == 12142
    assert validate_runner_launch_plan(plan) == []


def test_effective_aperture_runner_launch_plan_is_implementation_only() -> None:
    plan = build_effective_aperture_runner_launch_plan()

    assert plan["runner_implementation_status"] == RUNNER_IMPLEMENTATION_READY_STATUS
    assert plan["runner_execution_status"] == "NOT_EXECUTED"
    assert plan["runner_implementation_authorized_by_phrase"] is True
    assert plan["runner_execution_authorized"] is False
    assert plan["bounded_smoke_execution_authorized"] is False
    assert plan["production_generation_authorized"] is False
    assert plan["not_true_W_eff"] is True
    assert plan["not_measured_geometry"] is True
    assert plan["not_optical_solver_output"] is True
    assert plan["descriptor_contract"]["descriptor_is_not_measured_geometry"] is True
    assert (
        plan["planned_row_arithmetic"]["total_route_view_mode_rows_if_all_modes"]
        == 40
    )
    assert validate_runner_launch_plan(plan) == []


def test_runner_launch_plan_validator_rejects_execution_drift() -> None:
    plan = build_position_response_runner_launch_plan()
    plan["runner_execution_authorized"] = True
    plan["runner_execution_status"] = "EXECUTED"

    issues = validate_runner_launch_plan(plan)

    assert any("runner_execution_authorized" in issue for issue in issues)
    assert any("runner_execution_status" in issue for issue in issues)


def test_runner_launch_plan_writers_write_sidecars_only(tmp_path: Path) -> None:
    prs = write_position_response_runner_launch_plan(tmp_path / "prs")
    eas = write_effective_aperture_runner_launch_plan(tmp_path / "eas")

    assert prs["runner_execution_status"] == "NOT_EXECUTED"
    assert eas["runner_execution_status"] == "NOT_EXECUTED"
    assert (tmp_path / "prs" / PRS_RUNNER_LAUNCH_PLAN_FILENAME).exists()
    assert (tmp_path / "eas" / EAS_RUNNER_LAUNCH_PLAN_FILENAME).exists()
    prs_payload = json.loads(
        (tmp_path / "prs" / PRS_RUNNER_LAUNCH_PLAN_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    eas_payload = json.loads(
        (tmp_path / "eas" / EAS_RUNNER_LAUNCH_PLAN_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert prs_payload["no_runner_execution"] is True
    assert eas_payload["no_runner_execution"] is True
    assert prs_payload["no_production_artifact"] is True
    assert eas_payload["no_production_artifact"] is True


def test_prs_source_accumulation_job_plan_binds_particles_without_execution(
    tmp_path: Path,
) -> None:
    route_source = tmp_path / "route_source.csv"
    _write_prs_accumulation_route_source(route_source)

    report = build_position_response_source_accumulation_job_plan(
        route_source_path=route_source
    )

    expected_jobs = (
        len(PRS_APPROVED_ROUTE_MATRIX)
        * len(PRS_APPROVED_DIAMETERS_NM)
        * len(PRS_APPROVED_VIEWS)
        * 3
    )
    assert report["status"] == PRS_SOURCE_ACCUMULATION_PASS_STATUS
    assert report["planned_job_count"] == expected_jobs
    assert report["p1_preferred_job_count"] == 390
    assert report["p2_diagnostic_trap_job_count"] == 78
    assert report["planned_requested_event_count"] == (
        expected_jobs * PRS_SOURCE_ACCUMULATION_TARGET_EVENTS_PER_SEED
    )
    assert report["particle_binding_count"] == len(PRS_APPROVED_DIAMETERS_NM)
    assert report["runner_execution_authorized"] is False
    assert report["job_plan_execution_authorized"] is False
    assert report["position_response_surface_production_generated"] is False
    assert report["no_prs_production_artifact"] is True
    assert report["not_detection_probability"] is True
    assert report["post_run_required_gate"] == PRS_SOURCE_SUFFICIENCY_PASS_STATUS
    assert validate_position_response_source_accumulation_job_plan_report(report) == []
    job_rows = report["job_plan_rows"]
    assert {row["execution_authorized"] for row in job_rows} == {"false"}
    assert {row["post_run_required_gate"] for row in job_rows} == {
        PRS_SOURCE_SUFFICIENCY_PASS_STATUS
    }
    assert {row["route_source_binding_status"] for row in job_rows} == {"available"}
    assert {row["target_event_floor_basis"] for row in job_rows} == {
        "xz_441_bins_times_min_100_per_bin_floor_not_sufficiency_guarantee"
    }
    assert {row["nodi_run_performed"] for row in job_rows} == {"false"}
    assert {row["production_prs_generated"] for row in job_rows} == {"false"}
    first_job = job_rows[0]
    assert first_job["execution_authorized"] == "false"
    assert first_job["post_run_required_gate"] == PRS_SOURCE_SUFFICIENCY_PASS_STATUS
    assert first_job["route_source_binding_status"] == "available"


def test_prs_source_accumulation_job_plan_blocks_missing_particle_binding(
    tmp_path: Path,
) -> None:
    route_source = tmp_path / "route_source_missing.csv"
    _write_prs_accumulation_route_source(route_source, omit_diameter=150)

    report = build_position_response_source_accumulation_job_plan(
        route_source_path=route_source
    )

    assert report["status"] == PRS_SOURCE_ACCUMULATION_BLOCKED_STATUS
    assert report["missing_diameters"] == [150]
    assert report["job_plan_execution_authorized"] is False
    assert report["position_response_surface_production_generated"] is False
    assert any(
        blocker["status"] == "blocked_missing_particle_binding_for_diameter"
        for blocker in report["blockers"]
    )
    assert validate_position_response_source_accumulation_job_plan_report(report) == []


def test_prs_source_accumulation_job_plan_cli_writes_sidecars_only(
    tmp_path: Path,
) -> None:
    route_source = tmp_path / "route_source.csv"
    _write_prs_accumulation_route_source(route_source)
    output_dir = tmp_path / "accumulation-plan"

    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/write_nodi_position_response_source_accumulation_job_plan.py"
            ),
            "--confirm-write-job-plan",
            "--route-source",
            str(route_source),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert PRS_SOURCE_ACCUMULATION_PASS_STATUS in result.stdout
    assert {path.name for path in output_dir.iterdir()} == {
        PRS_SOURCE_ACCUMULATION_REPORT_FILENAME,
        PRS_SOURCE_ACCUMULATION_JOB_PLAN_FILENAME,
        PRS_SOURCE_ACCUMULATION_BLOCKERS_FILENAME,
        PRS_SOURCE_ACCUMULATION_ISSUES_FILENAME,
    }
    payload = json.loads(
        (output_dir / PRS_SOURCE_ACCUMULATION_REPORT_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    job_rows = read_csv_rows(output_dir / PRS_SOURCE_ACCUMULATION_JOB_PLAN_FILENAME)
    assert payload["planned_job_count"] == len(job_rows)
    assert {row["route_source_binding_status"] for row in job_rows} == {"available"}
    assert {row["target_event_floor_basis"] for row in job_rows} == {
        "xz_441_bins_times_min_100_per_bin_floor_not_sufficiency_guarantee"
    }
    assert {row["execution_authorized"] for row in job_rows} == {"false"}
    assert payload["runner_execution_authorized"] is False
    assert payload["nodi_run_performed"] is False
    assert payload["comsol_run_performed"] is False
    assert payload["joint_route_class_regenerated"] is False
    assert not (output_dir / "NODI_POSITION_RESPONSE_SURFACE.csv").exists()


def test_prs_source_accumulation_job_plan_cli_requires_confirm(tmp_path: Path) -> None:
    route_source = tmp_path / "route_source.csv"
    _write_prs_accumulation_route_source(route_source)
    output_dir = tmp_path / "accumulation-plan"

    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/write_nodi_position_response_source_accumulation_job_plan.py"
            ),
            "--route-source",
            str(route_source),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-write-job-plan" in result.stderr
    assert not output_dir.exists()


def test_prs_source_accumulation_bounded_shard_report_preserves_sufficiency_gate(
    tmp_path: Path,
) -> None:
    route_source = tmp_path / "route_source.csv"
    _write_prs_accumulation_route_source(route_source)
    plan_report = build_position_response_source_accumulation_job_plan(
        route_source_path=route_source
    )
    selected = select_position_response_source_accumulation_bounded_shard_jobs(
        plan_report["job_plan_rows"],
        max_jobs=1,
    )
    event_path = tmp_path / PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_EVENTS_FILENAME
    source_path = tmp_path / PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_SOURCE_FILENAME
    event_path.write_text("placeholder\n", encoding="utf-8")
    source_path.write_text("placeholder\n", encoding="utf-8")

    report = build_position_response_source_accumulation_bounded_shard_report(
        authorization_phrase=PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_AUTHORIZATION_PHRASE,
        job_plan_path=tmp_path / "job_plan.csv",
        job_plan_sha256=VALID_SHA,
        selected_job_rows=selected,
        n_events_per_job=6,
        event_source_path=event_path,
        event_source_sha256=VALID_SHA,
        event_row_count=6,
        bin_source_path=source_path,
        bin_source_sha256=VALID_SHA,
        bin_source_row_count=ROWS_PER_ROUTE_DIAMETER_VIEW,
        source_availability_report={
            "status": PRS_SOURCE_PREFLIGHT_PASS_STATUS,
            "report_path": str(tmp_path / "source_preflight.json"),
            "report_sha256": VALID_SHA,
            "source_available_candidate_count": 1,
        },
        source_numeric_sufficiency_report={
            "status": PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS,
            "report_path": str(tmp_path / "source_sufficiency.json"),
            "report_sha256": VALID_SHA,
            "numeric_sufficient_candidate_count": 0,
        },
    )

    assert report["status"] == PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_PASS_STATUS
    assert report["source_availability_status"] == PRS_SOURCE_PREFLIGHT_PASS_STATUS
    assert (
        report["source_numeric_sufficiency_status"]
        == PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS
    )
    assert report["source_numeric_sufficiency_expected_blocked_due_to_bounded_shard"] is True
    assert report["position_response_surface_production_generated"] is False
    assert report["production_generation_performed"] is False
    assert report["comsol_run_performed"] is False
    assert report["joint_route_class_regenerated"] is False
    assert report["not_detection_probability"] is True
    assert validate_position_response_source_accumulation_bounded_shard_report(report) == []

    written = write_position_response_source_accumulation_bounded_shard_sidecars(
        output_dir=tmp_path / "bounded-shard-sidecars",
        report=report,
    )
    manifest_rows = read_csv_rows(
        tmp_path
        / "bounded-shard-sidecars"
        / PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MANIFEST_FILENAME
    )
    assert written["execution_manifest_csv_sha256"]
    assert manifest_rows[0]["bounded_shard_only"] == "true"
    assert manifest_rows[0]["production_prs_generated"] == "false"
    assert manifest_rows[0]["source_numeric_sufficiency_status"] == (
        PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS
    )


def test_prs_source_accumulation_bounded_shard_selection_rejects_mutated_job(
    tmp_path: Path,
) -> None:
    route_source = tmp_path / "route_source.csv"
    _write_prs_accumulation_route_source(route_source)
    plan_report = build_position_response_source_accumulation_job_plan(
        route_source_path=route_source
    )
    bad_job = dict(plan_report["job_plan_rows"][0])
    bad_job["execution_authorized"] = "true"

    with pytest.raises(ContractValidationError) as exc_info:
        select_position_response_source_accumulation_bounded_shard_jobs([bad_job])

    assert any("PRS-ACCUM-SHARD-J07" in issue for issue in exc_info.value.issues)


def test_prs_source_accumulation_bounded_shard_cli_requires_confirm(
    tmp_path: Path,
) -> None:
    job_plan = tmp_path / "job_plan.csv"
    job_plan.write_text("placeholder\n", encoding="utf-8")
    output_dir = tmp_path / "bounded-shard"

    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/run_nodi_position_response_source_accumulation_bounded_shard.py"
            ),
            "--job-plan",
            str(job_plan),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-bounded-shard-execution" in result.stderr
    assert not output_dir.exists()


def test_prs_source_accumulation_bounded_shard_cli_writes_source_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    import tools.audits.run_nodi_position_response_source_accumulation_bounded_shard as shard

    route_source = tmp_path / "route_source.csv"
    _write_prs_accumulation_route_source(route_source)
    plan_dir = tmp_path / "plan"
    plan_report = write_position_response_source_accumulation_job_plan_bundle(
        route_source_path=route_source,
        output_dir=plan_dir,
        seeds=(11,),
    )
    fake_events = [
        {
            "initial_position_x_norm": x_norm,
            "initial_position_z_norm": z_norm,
            "features": {"n_peaks": n_peaks},
        }
        for x_norm, z_norm, n_peaks in [
            (-0.92, -0.25, 0),
            (-0.52, 0.11, 1),
            (-0.12, 0.18, 0),
            (0.08, -0.04, 1),
            (0.44, 0.72, 1),
            (0.88, -0.88, 0),
        ]
    ]
    monkeypatch.setattr(
        shard,
        "build_frozen_b_cfg",
        lambda _n_events, _seed: (
            SimpleNamespace(),
            SimpleNamespace(wavelength_m=0.0),
        ),
    )
    monkeypatch.setattr(shard, "_cfg_for_normalization_lane", lambda base_cfg, _view: base_cfg)
    monkeypatch.setattr(shard, "_resolve_e_sca_ref", lambda **_kwargs: 1.0)
    monkeypatch.setattr(shard, "particle_from_name", lambda _name: SimpleNamespace(name="fake"))
    monkeypatch.setattr(
        shard,
        "infer_particle_diameter_nm",
        lambda name: int(str(name).split("_")[-1].removesuffix("nm")),
    )
    monkeypatch.setattr(shard, "medium_for_particle", lambda _particle: "water")
    monkeypatch.setattr(
        shard.lane,
        "case_baseline_channel",
        lambda _width_nm, _depth_nm: SimpleNamespace(),
    )
    monkeypatch.setattr(shard, "run_single_case_batch", lambda *_args, **_kwargs: {"events": fake_events})
    output_dir = tmp_path / "bounded-shard"

    exit_code = shard.main(
        [
            "--confirm-bounded-shard-execution",
            "--job-plan",
            str(plan_report["job_plan_csv"]),
            "--output-dir",
            str(output_dir),
            "--max-jobs",
            "1",
            "--n-events-per-job",
            "6",
        ]
    )

    assert exit_code == 0
    report_path = output_dir / PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_REPORT_FILENAME
    event_path = output_dir / PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_EVENTS_FILENAME
    source_path = output_dir / PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_SOURCE_FILENAME
    manifest_path = output_dir / PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MANIFEST_FILENAME
    report = json.loads(report_path.read_text(encoding="utf-8"))
    source_rows = read_csv_rows(source_path)
    manifest_rows = read_csv_rows(manifest_path)

    assert report["status"] == PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_PASS_STATUS
    assert report["selected_job_count"] == 1
    assert report["event_rows"] == 6
    assert report["bin_source_rows"] == ROWS_PER_ROUTE_DIAMETER_VIEW
    assert report["source_availability_status"] == PRS_SOURCE_PREFLIGHT_PASS_STATUS
    assert (
        report["source_numeric_sufficiency_status"]
        == PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS
    )
    assert report["numeric_sufficient_candidate_count"] == 0
    assert report["position_response_surface_production_generated"] is False
    assert report["production_generation_performed"] is False
    assert report["comsol_run_performed"] is False
    assert report["joint_route_class_regenerated"] is False
    assert report["not_qch_weighted"] is True
    assert report["not_detection_probability"] is True
    assert len(read_csv_rows(event_path)) == 6
    assert len(source_rows) == ROWS_PER_ROUTE_DIAMETER_VIEW
    assert {row["source_scope"] for row in source_rows} == {PRS_SOURCE_PRODUCTION_SCOPE}
    assert {row["decision_use_allowed"] for row in source_rows} == {"false"}
    assert {row["production_prs_generated"] for row in source_rows} == {"false"}
    assert manifest_rows[0]["bounded_shard_only"] == "true"
    assert manifest_rows[0]["full_job_plan_execution_authorized"] == "false"
    assert manifest_rows[0]["production_prs_generated"] == "false"
    assert not (output_dir / "NODI_POSITION_RESPONSE_SURFACE.csv").exists()


def test_prs_source_accumulation_campaign_policy_schedules_all_jobs_without_execution(
    tmp_path: Path,
) -> None:
    route_source = tmp_path / "route_source.csv"
    _write_prs_accumulation_route_source(route_source)
    plan_report = write_position_response_source_accumulation_job_plan_bundle(
        route_source_path=route_source,
        output_dir=tmp_path / "job-plan",
    )

    report = build_position_response_source_accumulation_campaign_policy(
        job_plan_path=Path(plan_report["job_plan_csv"]),
        jobs_per_shard=12,
        max_parallel_shards=1,
    )

    assert report["status"] == PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_PASS_STATUS
    assert report["valid_job_count"] == 468
    assert report["planned_shard_count"] == 39
    assert report["planned_requested_event_count"] == 20638800
    assert report["expected_bin_source_rows_if_all_jobs_complete"] == (
        468 * ROWS_PER_ROUTE_DIAMETER_VIEW
    )
    assert report["campaign_execution_authorized"] is False
    assert report["shard_execution_authorized"] is False
    assert report["nodi_run_performed"] is False
    assert report["position_response_surface_production_generated"] is False
    assert report["numeric_sufficiency_pass_action"] == (
        "stop_for_review_not_auto_production_prs"
    )
    assert validate_position_response_source_accumulation_campaign_policy_report(report) == []
    shard_rows = report["campaign_shard_rows"]
    schedule_rows = report["campaign_job_schedule_rows"]
    assert len(shard_rows) == 39
    assert len(schedule_rows) == 468
    assert {row["execution_authorized"] for row in shard_rows} == {"false"}
    assert {row["execution_authorized"] for row in schedule_rows} == {"false"}
    assert {row["policy_only_not_executed"] for row in shard_rows + schedule_rows} == {
        "true"
    }
    assert {row["post_shard_numeric_sufficiency_gate"] for row in schedule_rows} == {
        PRS_SOURCE_SUFFICIENCY_PASS_STATUS
    }
    assert len({row["source_job_id"] for row in schedule_rows}) == 468
    assert shard_rows[0]["job_count"] == 12
    assert shard_rows[-1]["job_count"] == 12


def test_prs_source_accumulation_campaign_policy_rejects_mutated_schedule(
    tmp_path: Path,
) -> None:
    route_source = tmp_path / "route_source.csv"
    _write_prs_accumulation_route_source(route_source)
    plan_report = write_position_response_source_accumulation_job_plan_bundle(
        route_source_path=route_source,
        output_dir=tmp_path / "job-plan",
    )
    report = build_position_response_source_accumulation_campaign_policy(
        job_plan_path=Path(plan_report["job_plan_csv"]),
    )
    report["campaign_job_schedule_rows"][0]["execution_authorized"] = "true"

    issues = validate_position_response_source_accumulation_campaign_policy_report(report)

    _assert_has_issue(issues, "PRS-ACCUM-CAMPAIGN-S15")


def test_prs_source_accumulation_campaign_policy_cli_requires_confirm(
    tmp_path: Path,
) -> None:
    job_plan = tmp_path / "job_plan.csv"
    job_plan.write_text("placeholder\n", encoding="utf-8")
    output_dir = tmp_path / "campaign-policy"

    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/write_nodi_position_response_source_accumulation_campaign_policy.py"
            ),
            "--job-plan",
            str(job_plan),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-write-campaign-policy" in result.stderr
    assert not output_dir.exists()


def test_prs_source_accumulation_campaign_policy_cli_writes_sidecars_only(
    tmp_path: Path,
) -> None:
    route_source = tmp_path / "route_source.csv"
    _write_prs_accumulation_route_source(route_source)
    plan_report = write_position_response_source_accumulation_job_plan_bundle(
        route_source_path=route_source,
        output_dir=tmp_path / "job-plan",
    )
    output_dir = tmp_path / "campaign-policy"

    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/write_nodi_position_response_source_accumulation_campaign_policy.py"
            ),
            "--confirm-write-campaign-policy",
            "--job-plan",
            str(plan_report["job_plan_csv"]),
            "--output-dir",
            str(output_dir),
            "--jobs-per-shard",
            "12",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_PASS_STATUS in result.stdout
    assert (output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_REPORT_FILENAME).exists()
    assert (output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARDS_FILENAME).exists()
    assert (output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_JOB_SCHEDULE_FILENAME).exists()
    payload = json.loads(
        (output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_REPORT_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    shard_rows = read_csv_rows(output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARDS_FILENAME)
    schedule_rows = read_csv_rows(
        output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_JOB_SCHEDULE_FILENAME
    )
    assert payload["planned_shard_count"] == 39
    assert payload["valid_job_count"] == 468
    assert len(shard_rows) == 39
    assert len(schedule_rows) == 468
    assert payload["campaign_execution_authorized"] is False
    assert payload["position_response_surface_production_generated"] is False
    assert not (output_dir / "NODI_POSITION_RESPONSE_SURFACE.csv").exists()


def test_prs_source_accumulation_campaign_runner_readiness_selects_first_shard(
    tmp_path: Path,
) -> None:
    route_source = tmp_path / "route_source.csv"
    _write_prs_accumulation_route_source(route_source)
    plan_report = write_position_response_source_accumulation_job_plan_bundle(
        route_source_path=route_source,
        output_dir=tmp_path / "job-plan",
    )
    policy_report = write_position_response_source_accumulation_campaign_policy_bundle(
        job_plan_path=Path(plan_report["job_plan_csv"]),
        output_dir=tmp_path / "campaign-policy",
        jobs_per_shard=12,
        max_parallel_shards=1,
    )

    report = build_position_response_source_accumulation_campaign_runner_readiness(
        campaign_report_path=Path(policy_report["report_path"])
    )

    assert report["status"] == PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_PASS_STATUS
    assert report["selected_campaign_shard_id"] == "PRS_ACCUM_CAMPAIGN_SHARD_0001"
    assert report["selected_job_count"] == 12
    assert report["selected_expected_job_count"] == 12
    assert report["selected_expected_bin_source_rows"] == (
        12 * ROWS_PER_ROUTE_DIAMETER_VIEW
    )
    assert report["runner_readiness_authorized"] is False
    assert report["shard_execution_authorized"] is False
    assert report["nodi_run_performed"] is False
    assert report["position_response_surface_production_generated"] is False
    assert report["comsol_run_performed"] is False
    assert report["joint_route_class_regenerated"] is False
    assert {
        row["campaign_shard_id"]
        for row in report["selected_campaign_job_schedule_rows"]
    } == {"PRS_ACCUM_CAMPAIGN_SHARD_0001"}
    assert (
        validate_position_response_source_accumulation_campaign_runner_readiness_report(
            report
        )
        == []
    )


def test_prs_source_accumulation_campaign_runner_readiness_blocks_missing_shard(
    tmp_path: Path,
) -> None:
    route_source = tmp_path / "route_source.csv"
    _write_prs_accumulation_route_source(route_source)
    plan_report = write_position_response_source_accumulation_job_plan_bundle(
        route_source_path=route_source,
        output_dir=tmp_path / "job-plan",
    )
    policy_report = write_position_response_source_accumulation_campaign_policy_bundle(
        job_plan_path=Path(plan_report["job_plan_csv"]),
        output_dir=tmp_path / "campaign-policy",
        jobs_per_shard=12,
        max_parallel_shards=1,
    )

    report = build_position_response_source_accumulation_campaign_runner_readiness(
        campaign_report_path=Path(policy_report["report_path"]),
        campaign_shard_id="PRS_ACCUM_CAMPAIGN_SHARD_9999",
    )

    assert report["status"] != PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_PASS_STATUS
    assert report["selected_job_count"] == 0
    assert report["shard_execution_authorized"] is False
    assert report["position_response_surface_production_generated"] is False
    assert any("must match exactly one shard" in issue for issue in report["issues"])


def test_prs_source_accumulation_campaign_runner_readiness_cli_requires_confirm(
    tmp_path: Path,
) -> None:
    campaign_report = tmp_path / "campaign.json"
    campaign_report.write_text("{}", encoding="utf-8")
    output_dir = tmp_path / "runner-readiness"

    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/write_nodi_position_response_source_accumulation_campaign_runner_readiness.py"
            ),
            "--campaign-report",
            str(campaign_report),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-write-runner-readiness" in result.stderr
    assert not output_dir.exists()


def test_prs_source_accumulation_campaign_runner_readiness_cli_writes_sidecars_only(
    tmp_path: Path,
) -> None:
    route_source = tmp_path / "route_source.csv"
    _write_prs_accumulation_route_source(route_source)
    plan_report = write_position_response_source_accumulation_job_plan_bundle(
        route_source_path=route_source,
        output_dir=tmp_path / "job-plan",
    )
    policy_report = write_position_response_source_accumulation_campaign_policy_bundle(
        job_plan_path=Path(plan_report["job_plan_csv"]),
        output_dir=tmp_path / "campaign-policy",
        jobs_per_shard=12,
        max_parallel_shards=1,
    )
    output_dir = tmp_path / "runner-readiness"

    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/write_nodi_position_response_source_accumulation_campaign_runner_readiness.py"
            ),
            "--confirm-write-runner-readiness",
            "--campaign-report",
            str(policy_report["report_path"]),
            "--campaign-shard-id",
            "PRS_ACCUM_CAMPAIGN_SHARD_0001",
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_PASS_STATUS in result.stdout
    assert (
        output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_REPORT_FILENAME
    ).exists()
    assert (
        output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_SHARD_FILENAME
    ).exists()
    payload = json.loads(
        (
            output_dir
            / PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_REPORT_FILENAME
        ).read_text(encoding="utf-8")
    )
    shard_rows = read_csv_rows(
        output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_SHARD_FILENAME
    )
    assert payload["selected_campaign_shard_id"] == "PRS_ACCUM_CAMPAIGN_SHARD_0001"
    assert payload["selected_job_count"] == 12
    assert len(shard_rows) == 12
    assert {row["execution_authorized"] for row in shard_rows} == {"false"}
    assert payload["shard_execution_authorized"] is False
    assert payload["position_response_surface_production_generated"] is False
    assert not (output_dir / "NODI_POSITION_RESPONSE_SURFACE.csv").exists()


@pytest.mark.parametrize(
    ("script", "message"),
    [
        (
            "tools/audits/build_nodi_position_response_surface.py",
            "without --confirm-write-launch-plan",
        ),
        (
            "tools/audits/build_nodi_effective_aperture_surrogate_sensitivity.py",
            "without --confirm-write-launch-plan",
        ),
    ],
)
def test_runner_entrypoint_clis_require_confirm_write_launch_plan(
    tmp_path: Path,
    script: str,
    message: str,
) -> None:
    output_dir = tmp_path / "blocked"
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / script),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert message in result.stderr
    assert not output_dir.exists()


@pytest.mark.parametrize(
    ("script", "expected_status", "filename"),
    [
        (
            "tools/audits/build_nodi_position_response_surface.py",
            "NODI_POSITION_RESPONSE_SURFACE_RUNNER: "
            "RUNNER_IMPLEMENTATION_READY_NOT_EXECUTED",
            PRS_RUNNER_LAUNCH_PLAN_FILENAME,
        ),
        (
            "tools/audits/build_nodi_effective_aperture_surrogate_sensitivity.py",
            "NODI_EFFECTIVE_APERTURE_SURROGATE_RUNNER: "
            "RUNNER_IMPLEMENTATION_READY_NOT_EXECUTED",
            EAS_RUNNER_LAUNCH_PLAN_FILENAME,
        ),
    ],
)
def test_runner_entrypoint_clis_write_launch_plan_without_execution(
    tmp_path: Path,
    script: str,
    expected_status: str,
    filename: str,
) -> None:
    output_dir = tmp_path / "runner-launch"
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / script),
            "--confirm-write-launch-plan",
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert expected_status in result.stdout
    assert "runner_execution_status: NOT_EXECUTED" in result.stdout
    payload = json.loads((output_dir / filename).read_text(encoding="utf-8"))
    assert payload["runner_execution_authorized"] is False
    assert payload["bounded_smoke_execution_authorized"] is False
    assert payload["production_generation_authorized"] is False
    assert payload["no_runner_execution"] is True


@pytest.mark.parametrize(
    "script",
    [
        "tools/audits/build_nodi_position_response_surface.py",
        "tools/audits/build_nodi_effective_aperture_surrogate_sensitivity.py",
    ],
)
def test_runner_entrypoint_help_has_no_execution_surface(script: str) -> None:
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / script), "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--confirm-write-launch-plan" in result.stdout
    assert "--output-dir" in result.stdout
    assert "--execute" not in result.stdout
    assert "--run" not in result.stdout
    assert "--production" not in result.stdout


def test_bounded_smoke_readiness_report_passes_without_authorizing_smoke(
    tmp_path: Path,
) -> None:
    prs = write_position_response_runner_launch_plan(tmp_path / "prs")
    eas = write_effective_aperture_runner_launch_plan(tmp_path / "eas")

    report = build_bounded_smoke_readiness_report(
        prs_launch_plan_path=Path(prs["launch_plan_path"]),
        eas_launch_plan_path=Path(eas["launch_plan_path"]),
    )

    assert report["status"] == BOUNDED_SMOKE_READINESS_PASS_STATUS
    assert report["required_future_authorization_phrase"] == BOUNDED_SMOKE_AUTHORIZATION_PHRASE
    assert report["authorization_phrase_already_received"] is False
    assert report["bounded_smoke_execution_authorized"] is False
    assert report["runner_execution_authorized"] is False
    assert report["production_generation_authorized"] is False
    assert report["no_smoke_execution"] is True
    assert report["no_production_artifact"] is True
    assert report["readiness_summary"]["prs_planned_rows"] == "72852"
    assert report["readiness_summary"]["eas_planned_rows"] == "40"
    assert validate_bounded_smoke_readiness_report(report) == []


def test_bounded_smoke_readiness_report_blocks_missing_launch_plan(tmp_path: Path) -> None:
    eas = write_effective_aperture_runner_launch_plan(tmp_path / "eas")

    report = build_bounded_smoke_readiness_report(
        prs_launch_plan_path=tmp_path / "missing-prs.json",
        eas_launch_plan_path=Path(eas["launch_plan_path"]),
    )

    assert report["status"] == "BLOCKED_BOUNDED_SMOKE_READINESS_PREFLIGHT_NOT_AUTHORIZED"
    assert any("missing" in issue for issue in report["issues"])
    assert report["bounded_smoke_execution_authorized"] is False
    assert report["no_smoke_execution"] is True


def test_bounded_smoke_readiness_validator_rejects_authorization_drift(
    tmp_path: Path,
) -> None:
    prs = write_position_response_runner_launch_plan(tmp_path / "prs")
    eas = write_effective_aperture_runner_launch_plan(tmp_path / "eas")
    report = build_bounded_smoke_readiness_report(
        prs_launch_plan_path=Path(prs["launch_plan_path"]),
        eas_launch_plan_path=Path(eas["launch_plan_path"]),
    )
    report["bounded_smoke_execution_authorized"] = True
    report["no_smoke_execution"] = False

    issues = validate_bounded_smoke_readiness_report(report)

    assert any("bounded_smoke_execution_authorized" in issue for issue in issues)
    assert any("no_smoke_execution" in issue for issue in issues)


def test_bounded_smoke_readiness_writer_outputs_sidecar_only(tmp_path: Path) -> None:
    prs = write_position_response_runner_launch_plan(tmp_path / "prs")
    eas = write_effective_aperture_runner_launch_plan(tmp_path / "eas")

    report = write_bounded_smoke_readiness_report(
        prs_launch_plan_path=Path(prs["launch_plan_path"]),
        eas_launch_plan_path=Path(eas["launch_plan_path"]),
        output_dir=tmp_path / "readiness",
    )

    assert report["status"] == BOUNDED_SMOKE_READINESS_PASS_STATUS
    assert (tmp_path / "readiness" / NEXT_ARTIFACTS_BOUNDED_SMOKE_READINESS_REPORT_FILENAME).exists()
    assert (tmp_path / "readiness" / NEXT_ARTIFACTS_BOUNDED_SMOKE_READINESS_ISSUES_FILENAME).exists()
    payload = json.loads(
        (
            tmp_path
            / "readiness"
            / NEXT_ARTIFACTS_BOUNDED_SMOKE_READINESS_REPORT_FILENAME
        ).read_text(encoding="utf-8")
    )
    assert payload["bounded_smoke_execution_authorized"] is False
    assert payload["runner_execution_authorized"] is False
    assert payload["no_runner_execution"] is True


def test_bounded_smoke_readiness_cli_requires_confirm_write(tmp_path: Path) -> None:
    prs = write_position_response_runner_launch_plan(tmp_path / "prs")
    eas = write_effective_aperture_runner_launch_plan(tmp_path / "eas")
    output_dir = tmp_path / "blocked"

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/write_nodi_next_artifacts_bounded_smoke_readiness.py"),
            "--prs-launch-plan",
            str(prs["launch_plan_path"]),
            "--eas-launch-plan",
            str(eas["launch_plan_path"]),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "without --confirm-write-readiness" in result.stderr
    assert not output_dir.exists()


def test_bounded_smoke_readiness_cli_writes_not_authorized_report(
    tmp_path: Path,
) -> None:
    prs = write_position_response_runner_launch_plan(tmp_path / "prs")
    eas = write_effective_aperture_runner_launch_plan(tmp_path / "eas")
    output_dir = tmp_path / "readiness"

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/write_nodi_next_artifacts_bounded_smoke_readiness.py"),
            "--confirm-write-readiness",
            "--prs-launch-plan",
            str(prs["launch_plan_path"]),
            "--eas-launch-plan",
            str(eas["launch_plan_path"]),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (
        "NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_READINESS: "
        "PASS_BOUNDED_SMOKE_READINESS_PREFLIGHT_NOT_AUTHORIZED"
    ) in result.stdout
    payload = json.loads(
        (output_dir / NEXT_ARTIFACTS_BOUNDED_SMOKE_READINESS_REPORT_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert payload["bounded_smoke_execution_authorized"] is False
    assert payload["no_smoke_execution"] is True


def test_bounded_smoke_readiness_cli_help_has_no_execution_surface() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/write_nodi_next_artifacts_bounded_smoke_readiness.py"),
            "--help",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--confirm-write-readiness" in result.stdout
    assert "--prs-launch-plan" in result.stdout
    assert "--eas-launch-plan" in result.stdout
    assert "--execute" not in result.stdout
    assert "--run" not in result.stdout
    assert "--production" not in result.stdout


def _write_passing_bounded_smoke_readiness(tmp_path: Path) -> dict[str, Any]:
    prs = write_position_response_runner_launch_plan(tmp_path / "prs")
    eas = write_effective_aperture_runner_launch_plan(tmp_path / "eas")
    return write_bounded_smoke_readiness_report(
        prs_launch_plan_path=Path(prs["launch_plan_path"]),
        eas_launch_plan_path=Path(eas["launch_plan_path"]),
        output_dir=tmp_path / "readiness",
    )


def test_bounded_smoke_execution_manifest_rows_stay_sidecar_only() -> None:
    prs_rows = position_response_bounded_smoke_execution_manifest_rows()
    eas_rows = effective_aperture_bounded_smoke_execution_manifest_rows()

    assert len(prs_rows) == len(position_response_smoke_manifest_rows())
    assert len(eas_rows) == len(effective_aperture_smoke_manifest_rows())
    assert (
        validate_bounded_smoke_execution_manifest_rows(
            prs_rows,
            artifact=POSITION_RESPONSE_ARTIFACT,
        )
        == []
    )
    assert (
        validate_bounded_smoke_execution_manifest_rows(
            eas_rows,
            artifact="NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY",
        )
        == []
    )
    for row in [*prs_rows, *eas_rows]:
        assert row["bounded_smoke_execution_status"] == BOUNDED_SMOKE_EXECUTION_ROW_STATUS
        assert row["runner_execution_scope"] == "bounded_smoke_contract_sidecar_only"
        assert row["production_artifact_generated"] == "false"
        assert row["nodi_run_performed"] == "false"
        assert row["comsol_run_performed"] == "false"
        assert row["joint_route_class_regenerated"] == "false"
        assert row["not_qch_weighted"] == "true"
        assert row["not_yield"] == "true"
        assert row["not_winner"] == "true"
        assert row["not_true_W_eff"] == "true"


def test_bounded_smoke_execution_report_accepts_exact_phrase_after_readiness(
    tmp_path: Path,
) -> None:
    readiness = _write_passing_bounded_smoke_readiness(tmp_path)

    report = build_bounded_smoke_execution_report(
        readiness_report_path=Path(readiness["report_path"]),
        authorization_phrase=BOUNDED_SMOKE_AUTHORIZATION_PHRASE,
    )

    assert report["status"] == BOUNDED_SMOKE_EXECUTION_PASS_STATUS
    assert report["authorization_phrase_exact_match"] is True
    assert report["bounded_smoke_execution_performed"] is True
    assert report["bounded_smoke_runner_execution_authorized"] is True
    assert report["production_generation_authorized"] is False
    assert report["production_generation_performed"] is False
    assert report["full_runner_execution_authorized"] is False
    assert report["nodi_run_performed"] is False
    assert report["comsol_run_performed"] is False
    assert report["joint_route_class_regenerated"] is False
    assert report["not_qch_weighted"] is True
    assert report["not_yield"] is True
    assert report["not_winner"] is True
    assert report["not_true_W_eff"] is True
    assert report["production_artifact_filenames"] == []
    assert validate_bounded_smoke_execution_report(report) == []


def test_bounded_smoke_execution_rejects_wrong_phrase_without_manifests(
    tmp_path: Path,
) -> None:
    readiness = _write_passing_bounded_smoke_readiness(tmp_path)
    output_dir = tmp_path / "blocked-smoke"

    report = write_bounded_smoke_execution_bundle(
        readiness_report_path=Path(readiness["report_path"]),
        authorization_phrase="authorize NODI next-artifacts bounded smoke execution please",
        output_dir=output_dir,
    )

    assert report["status"] == "BLOCKED_BOUNDED_SMOKE_EXECUTION_CONTRACT_ONLY"
    assert report["authorization_phrase_exact_match"] is False
    assert report["bounded_smoke_execution_performed"] is False
    assert any("authorization phrase" in issue for issue in report["issues"])
    assert (output_dir / NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_REPORT_FILENAME).exists()
    assert (output_dir / NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_ISSUES_FILENAME).exists()
    assert not (output_dir / PRS_BOUNDED_SMOKE_EXECUTION_MANIFEST_FILENAME).exists()
    assert not (output_dir / EAS_BOUNDED_SMOKE_EXECUTION_MANIFEST_FILENAME).exists()


def test_bounded_smoke_execution_writer_outputs_smoke_sidecars_only(
    tmp_path: Path,
) -> None:
    readiness = _write_passing_bounded_smoke_readiness(tmp_path)
    output_dir = tmp_path / "smoke-execution"

    report = write_bounded_smoke_execution_bundle(
        readiness_report_path=Path(readiness["report_path"]),
        authorization_phrase=BOUNDED_SMOKE_AUTHORIZATION_PHRASE,
        output_dir=output_dir,
    )

    assert report["status"] == BOUNDED_SMOKE_EXECUTION_PASS_STATUS
    assert report["bounded_smoke_execution_performed"] is True
    assert report["no_production_artifact"] is True
    assert (output_dir / NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_REPORT_FILENAME).exists()
    assert (output_dir / NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_ISSUES_FILENAME).exists()
    prs_path = output_dir / PRS_BOUNDED_SMOKE_EXECUTION_MANIFEST_FILENAME
    eas_path = output_dir / EAS_BOUNDED_SMOKE_EXECUTION_MANIFEST_FILENAME
    assert prs_path.exists()
    assert eas_path.exists()
    prs_rows = read_csv_rows(prs_path)
    eas_rows = read_csv_rows(eas_path)
    assert len(prs_rows) == len(position_response_smoke_manifest_rows())
    assert len(eas_rows) == len(effective_aperture_smoke_manifest_rows())
    assert {row["production_artifact_generated"] for row in prs_rows + eas_rows} == {
        "false"
    }
    assert {row["bounded_smoke_execution_status"] for row in prs_rows + eas_rows} == {
        BOUNDED_SMOKE_EXECUTION_ROW_STATUS
    }


def test_bounded_smoke_execution_cli_requires_confirm(tmp_path: Path) -> None:
    readiness = _write_passing_bounded_smoke_readiness(tmp_path)
    output_dir = tmp_path / "blocked-cli"

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/run_nodi_next_artifacts_bounded_smoke.py"),
            "--authorization-phrase",
            BOUNDED_SMOKE_AUTHORIZATION_PHRASE,
            "--readiness-report",
            str(readiness["report_path"]),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "without --confirm-bounded-smoke-execution" in result.stderr
    assert not output_dir.exists()


def test_bounded_smoke_execution_cli_writes_smoke_sidecars_only(
    tmp_path: Path,
) -> None:
    readiness = _write_passing_bounded_smoke_readiness(tmp_path)
    output_dir = tmp_path / "smoke-cli"

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/run_nodi_next_artifacts_bounded_smoke.py"),
            "--confirm-bounded-smoke-execution",
            "--authorization-phrase",
            BOUNDED_SMOKE_AUTHORIZATION_PHRASE,
            "--readiness-report",
            str(readiness["report_path"]),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (
        "NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION: "
        "PASS_BOUNDED_SMOKE_EXECUTION_CONTRACT_ONLY"
    ) in result.stdout
    payload = json.loads(
        (output_dir / NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_REPORT_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert payload["bounded_smoke_execution_performed"] is True
    assert payload["production_generation_performed"] is False
    assert payload["nodi_run_performed"] is False
    assert payload["comsol_run_performed"] is False
    assert payload["joint_route_class_regenerated"] is False
    assert (output_dir / PRS_BOUNDED_SMOKE_EXECUTION_MANIFEST_FILENAME).exists()
    assert (output_dir / EAS_BOUNDED_SMOKE_EXECUTION_MANIFEST_FILENAME).exists()


def test_bounded_smoke_execution_cli_help_has_no_production_surface() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/run_nodi_next_artifacts_bounded_smoke.py"),
            "--help",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--confirm-bounded-smoke-execution" in result.stdout
    assert "--authorization-phrase" in result.stdout
    assert "--readiness-report" in result.stdout
    assert "--execute" not in result.stdout
    assert "--production" not in result.stdout


def _write_passing_bounded_smoke_execution(tmp_path: Path) -> dict[str, Any]:
    readiness = _write_passing_bounded_smoke_readiness(tmp_path)
    return write_bounded_smoke_execution_bundle(
        readiness_report_path=Path(readiness["report_path"]),
        authorization_phrase=BOUNDED_SMOKE_AUTHORIZATION_PHRASE,
        output_dir=tmp_path / "smoke-execution",
    )


def test_effective_aperture_first_production_rows_use_approved_selector_and_modes() -> None:
    rows = build_effective_aperture_first_production_rows(
        geometry_descriptor_path=PROJECT_ROOT / "tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv",
        rank_source_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv",
        guardrail_table_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv",
    )

    assert len(rows) == 32
    assert validate_effective_aperture_surrogate_rows(rows) == []
    assert {row["aperture_surrogate_mode"] for row in rows} == set(EAS_FIRST_PRODUCTION_MODES)
    assert "COMSOL_descriptor_if_available" not in {
        row["aperture_surrogate_mode"] for row in rows
    }
    for row in rows:
        assert "W_eff_nm" not in row
        assert row["source_geometry_descriptor_sha"] == GEOMETRY_DESCRIPTOR_SHA256
        assert "sidewall_deg=85.0" in row["source_geometry_descriptor_id"]
        assert row["not_true_W_eff"] == "true"
        if row["aperture_surrogate_mode"] == "nominal_width":
            assert row["solver_contract_trigger_flag"] == "false"
            assert row["eta_selected_proxy_under_surrogate"] != ""
            assert row["eta_all_proxy_under_surrogate"] != ""
        else:
            assert row["solver_contract_trigger_flag"] == "true"
            assert row["eta_selected_proxy_under_surrogate"] == ""
            assert row["eta_all_proxy_under_surrogate"] == ""


def test_production_generation_report_writes_eas_and_blocks_only_prs(
    tmp_path: Path,
) -> None:
    smoke = _write_passing_bounded_smoke_execution(tmp_path)

    report = build_production_generation_report(
        smoke_execution_report_path=Path(smoke["report_path"]),
        geometry_descriptor_path=PROJECT_ROOT / "tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv",
        rank_source_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv",
        guardrail_table_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv",
        authorization_phrase=PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
    )

    assert report["status"] == PRODUCTION_GENERATION_PARTIAL_STATUS
    assert report["authorization_phrase_exact_match"] is True
    assert report["production_generation_authorized_by_phrase"] is True
    assert report["production_generation_performed"] is True
    assert report["production_artifacts_generated"] == []
    assert report["nodi_run_performed"] is False
    assert report["comsol_run_performed"] is False
    assert report["joint_route_class_regenerated"] is False
    assert report["not_qch_weighted"] is True
    assert report["not_yield"] is True
    assert report["not_winner"] is True
    assert report["not_true_W_eff"] is True
    blocker_statuses = {blocker["status"] for blocker in report["blockers"]}
    assert blocker_statuses == {
        "blocked_missing_numeric_sufficient_position_response_source"
    }
    assert report["effective_aperture_surrogate_status"] == "ready_to_write_first_production_eas"
    assert report["excluded_first_production_eas_modes"] == [
        "COMSOL_descriptor_if_available"
    ]
    assert validate_production_generation_report(report) == []


def test_production_generation_report_accepts_valid_prs_candidate(
    tmp_path: Path,
) -> None:
    smoke = _write_passing_bounded_smoke_execution(tmp_path)
    source_path = tmp_path / "edge_primary_xz_diagnostic_source.csv"
    write_csv_rows(source_path, _edge_primary_xz_diagnostic_prs_bin_source_rows())
    candidate = write_position_response_edge_primary_candidate_bundle(
        source_path=source_path,
        output_dir=tmp_path / "edge-primary-candidate",
    )

    report = build_production_generation_report(
        smoke_execution_report_path=Path(smoke["report_path"]),
        geometry_descriptor_path=PROJECT_ROOT / "tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv",
        rank_source_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv",
        guardrail_table_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv",
        position_response_candidate_path=Path(candidate["candidate_csv"]),
        authorization_phrase=PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
    )

    assert report["status"] == PRODUCTION_GENERATION_PASS_STATUS
    assert report["blockers"] == []
    assert report["position_response_surface_status"] == "ready_to_write_edge_primary_candidate_prs"
    assert report["position_response_candidate_row_count"] == ROWS_PER_ROUTE_DIAMETER_VIEW
    assert report["position_response_candidate_validation_issue_count"] == 0
    assert report["position_response_surface_production_generated"] is False
    assert report["effective_aperture_surrogate_status"] == "ready_to_write"
    assert validate_production_generation_report(report) == []


def test_production_generation_report_blocks_missing_prs_candidate(
    tmp_path: Path,
) -> None:
    smoke = _write_passing_bounded_smoke_execution(tmp_path)
    missing_candidate = tmp_path / "missing_prs_candidate.csv"

    report = build_production_generation_report(
        smoke_execution_report_path=Path(smoke["report_path"]),
        geometry_descriptor_path=PROJECT_ROOT / "tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv",
        rank_source_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv",
        guardrail_table_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv",
        position_response_candidate_path=missing_candidate,
        authorization_phrase=PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
    )

    assert report["status"] == PRODUCTION_GENERATION_BLOCKED_STATUS
    assert report["position_response_surface_status"] == "blocked_missing_position_response_event_source"
    assert report["position_response_candidate_validation_issue_count"] == 1
    assert any("PROD-PRS-CANDIDATE: missing" in issue for issue in report["issues"])
    assert {blocker["status"] for blocker in report["blockers"]} == {
        "blocked_invalid_position_response_candidate"
    }
    assert validate_production_generation_report(report) == []


def test_production_generation_report_blocks_invalid_prs_candidate(
    tmp_path: Path,
) -> None:
    smoke = _write_passing_bounded_smoke_execution(tmp_path)
    invalid_candidate = tmp_path / "invalid_prs_candidate.csv"
    write_csv_rows(invalid_candidate, [{"not": "a_prs_row"}])

    report = build_production_generation_report(
        smoke_execution_report_path=Path(smoke["report_path"]),
        geometry_descriptor_path=PROJECT_ROOT / "tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv",
        rank_source_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv",
        guardrail_table_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv",
        position_response_candidate_path=invalid_candidate,
        authorization_phrase=PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
    )

    assert report["status"] == PRODUCTION_GENERATION_BLOCKED_STATUS
    assert report["position_response_surface_status"] == "blocked_missing_position_response_event_source"
    assert report["position_response_candidate_validation_issue_count"] > 0
    assert {blocker["status"] for blocker in report["blockers"]} == {
        "blocked_invalid_position_response_candidate"
    }
    assert report["position_response_surface_production_generated"] is False
    assert validate_production_generation_report(report) == []


def test_production_generation_rejects_wrong_phrase(
    tmp_path: Path,
) -> None:
    smoke = _write_passing_bounded_smoke_execution(tmp_path)

    report = build_production_generation_report(
        smoke_execution_report_path=Path(smoke["report_path"]),
        geometry_descriptor_path=PROJECT_ROOT / "tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv",
        rank_source_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv",
        guardrail_table_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv",
        authorization_phrase="authorize NODI next-artifacts production generation please",
    )

    assert report["status"] == PRODUCTION_GENERATION_BLOCKED_STATUS
    assert report["authorization_phrase_exact_match"] is False
    assert report["production_generation_authorized_by_phrase"] is False
    assert report["production_generation_performed"] is False
    assert any("authorization phrase" in issue for issue in report["issues"])


def test_production_generation_writer_outputs_eas_and_prs_blocker_sidecars(
    tmp_path: Path,
) -> None:
    smoke = _write_passing_bounded_smoke_execution(tmp_path)
    output_dir = tmp_path / "production-generation"

    report = write_production_generation_bundle(
        smoke_execution_report_path=Path(smoke["report_path"]),
        geometry_descriptor_path=PROJECT_ROOT / "tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv",
        rank_source_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv",
        guardrail_table_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv",
        authorization_phrase=PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
        output_dir=output_dir,
    )

    assert report["status"] == PRODUCTION_GENERATION_PARTIAL_STATUS
    assert report["effective_aperture_surrogate_production_generated"] is True
    assert (output_dir / NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_FILENAME).exists()
    assert (output_dir / NEXT_ARTIFACTS_PRODUCTION_GENERATION_ISSUES_FILENAME).exists()
    blocker_path = output_dir / NEXT_ARTIFACTS_PRODUCTION_GENERATION_BLOCKERS_FILENAME
    assert blocker_path.exists()
    blocker_rows = read_csv_rows(blocker_path)
    assert {row["artifact"] for row in blocker_rows} == {POSITION_RESPONSE_ARTIFACT}
    eas_path = output_dir / EAS_PRODUCTION_FILENAME
    selector_path = output_dir / EAS_SELECTOR_POLICY_METADATA_FILENAME
    assert eas_path.exists()
    assert selector_path.exists()
    eas_rows = read_csv_rows(eas_path)
    assert len(eas_rows) == 32
    assert validate_effective_aperture_surrogate_rows(eas_rows) == []
    selector_payload = json.loads(selector_path.read_text(encoding="utf-8"))
    assert selector_payload["selector_policy"]["sidewall_deg"] == "85.0"
    assert selector_payload["excluded_first_production_modes"] == [
        "COMSOL_descriptor_if_available"
    ]
    assert selector_payload["no_comsol_run"] is True
    assert {artifact["artifact"] for artifact in report["production_artifacts_generated"]} == {
        APERTURE_SURROGATE_ARTIFACT,
        "NODI_EFFECTIVE_APERTURE_SURROGATE_SELECTOR_POLICY",
    }
    assert not any(output_dir.glob("NODI_POSITION_RESPONSE_SURFACE.csv"))


def test_production_generation_writer_outputs_eas_and_validated_prs(
    tmp_path: Path,
) -> None:
    smoke = _write_passing_bounded_smoke_execution(tmp_path)
    source_path = tmp_path / "edge_primary_xz_diagnostic_source.csv"
    write_csv_rows(source_path, _edge_primary_xz_diagnostic_prs_bin_source_rows())
    candidate = write_position_response_edge_primary_candidate_bundle(
        source_path=source_path,
        output_dir=tmp_path / "edge-primary-candidate",
    )
    output_dir = tmp_path / "production-generation-full"

    report = write_production_generation_bundle(
        smoke_execution_report_path=Path(smoke["report_path"]),
        geometry_descriptor_path=PROJECT_ROOT / "tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv",
        rank_source_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv",
        guardrail_table_path=PROJECT_ROOT
        / "exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv",
        position_response_candidate_path=Path(candidate["candidate_csv"]),
        authorization_phrase=PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
        output_dir=output_dir,
    )

    assert report["status"] == PRODUCTION_GENERATION_PASS_STATUS
    assert report["blockers"] == []
    assert report["effective_aperture_surrogate_production_generated"] is True
    assert report["position_response_surface_production_generated"] is True
    prs_path = output_dir / PRS_PRODUCTION_FILENAME
    eas_path = output_dir / EAS_PRODUCTION_FILENAME
    assert prs_path.exists()
    assert eas_path.exists()
    prs_rows = read_csv_rows(prs_path)
    assert len(prs_rows) == ROWS_PER_ROUTE_DIAMETER_VIEW
    assert validate_position_response_surface_rows(
        prs_rows,
        production_table=True,
        require_complete_row_arithmetic=True,
    ) == []
    assert {row["aggregate_source_type"] for row in prs_rows if row["distribution_type"] == "xz_norm_2d"} == {
        "xz_norm_diagnostic"
    }
    assert {artifact["artifact"] for artifact in report["production_artifacts_generated"]} == {
        APERTURE_SURROGATE_ARTIFACT,
        "NODI_EFFECTIVE_APERTURE_SURROGATE_SELECTOR_POLICY",
        POSITION_RESPONSE_ARTIFACT,
    }
    assert report["comsol_run_performed"] is False
    assert report["joint_route_class_regenerated"] is False


def test_production_generation_cli_requires_confirm(tmp_path: Path) -> None:
    smoke = _write_passing_bounded_smoke_execution(tmp_path)
    output_dir = tmp_path / "blocked-cli"

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/run_nodi_next_artifacts_production_generation.py"),
            "--authorization-phrase",
            PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
            "--smoke-execution-report",
            str(smoke["report_path"]),
            "--geometry-descriptor",
            str(PROJECT_ROOT / "tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv"),
            "--rank-source",
            str(
                PROJECT_ROOT
                / "exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv"
            ),
            "--guardrail-table",
            str(PROJECT_ROOT / "exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv"),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "without --confirm-production-generation" in result.stderr
    assert not output_dir.exists()


def test_production_generation_cli_writes_partial_eas_gate(
    tmp_path: Path,
) -> None:
    smoke = _write_passing_bounded_smoke_execution(tmp_path)
    output_dir = tmp_path / "production-cli"

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/run_nodi_next_artifacts_production_generation.py"),
            "--confirm-production-generation",
            "--authorization-phrase",
            PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
            "--smoke-execution-report",
            str(smoke["report_path"]),
            "--geometry-descriptor",
            str(PROJECT_ROOT / "tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv"),
            "--rank-source",
            str(
                PROJECT_ROOT
                / "exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv"
            ),
            "--guardrail-table",
            str(PROJECT_ROOT / "exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv"),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert (
        "NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION: "
        "PARTIAL_PRODUCTION_GENERATION_EAS_WRITTEN_PRS_BLOCKED"
    ) in result.stdout
    payload = json.loads(
        (output_dir / NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert payload["production_generation_authorized_by_phrase"] is True
    assert payload["production_generation_performed"] is True
    assert payload["effective_aperture_surrogate_production_generated"] is True
    assert payload["position_response_surface_production_generated"] is False
    assert payload["comsol_run_performed"] is False
    assert payload["joint_route_class_regenerated"] is False
    assert (output_dir / EAS_PRODUCTION_FILENAME).exists()
    assert not (output_dir / "NODI_POSITION_RESPONSE_SURFACE.csv").exists()


def test_production_generation_cli_writes_full_gate_with_prs_candidate(
    tmp_path: Path,
) -> None:
    smoke = _write_passing_bounded_smoke_execution(tmp_path)
    source_path = tmp_path / "edge_primary_xz_diagnostic_source.csv"
    write_csv_rows(source_path, _edge_primary_xz_diagnostic_prs_bin_source_rows())
    candidate = write_position_response_edge_primary_candidate_bundle(
        source_path=source_path,
        output_dir=tmp_path / "edge-primary-candidate",
    )
    output_dir = tmp_path / "production-cli-full"

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/run_nodi_next_artifacts_production_generation.py"),
            "--confirm-production-generation",
            "--authorization-phrase",
            PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
            "--smoke-execution-report",
            str(smoke["report_path"]),
            "--geometry-descriptor",
            str(PROJECT_ROOT / "tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv"),
            "--rank-source",
            str(
                PROJECT_ROOT
                / "exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv"
            ),
            "--guardrail-table",
            str(PROJECT_ROOT / "exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv"),
            "--position-response-candidate",
            str(candidate["candidate_csv"]),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION: PASS_PRODUCTION_GENERATION" in result.stdout
    payload = json.loads(
        (output_dir / NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert payload["position_response_surface_production_generated"] is True
    assert payload["effective_aperture_surrogate_production_generated"] is True
    assert payload["comsol_run_performed"] is False
    assert payload["joint_route_class_regenerated"] is False
    assert (output_dir / PRS_PRODUCTION_FILENAME).exists()
    assert (output_dir / EAS_PRODUCTION_FILENAME).exists()


def test_production_generation_cli_blocks_missing_prs_candidate(
    tmp_path: Path,
) -> None:
    smoke = _write_passing_bounded_smoke_execution(tmp_path)
    output_dir = tmp_path / "production-cli-missing-prs"
    missing_candidate = tmp_path / "missing_prs_candidate.csv"

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/run_nodi_next_artifacts_production_generation.py"),
            "--confirm-production-generation",
            "--authorization-phrase",
            PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
            "--smoke-execution-report",
            str(smoke["report_path"]),
            "--geometry-descriptor",
            str(PROJECT_ROOT / "tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv"),
            "--rank-source",
            str(
                PROJECT_ROOT
                / "exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv"
            ),
            "--guardrail-table",
            str(PROJECT_ROOT / "exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv"),
            "--position-response-candidate",
            str(missing_candidate),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "BLOCKED_PRODUCTION_GENERATION_INPUTS" in result.stdout
    payload = json.loads(
        (output_dir / NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert payload["position_response_surface_status"] == "blocked_missing_position_response_event_source"
    assert {blocker["status"] for blocker in payload["blockers"]} == {
        "blocked_invalid_position_response_candidate"
    }
    assert not (output_dir / PRS_PRODUCTION_FILENAME).exists()


def test_production_generation_cli_help_has_no_comsol_or_joint_surface() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/run_nodi_next_artifacts_production_generation.py"),
            "--help",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--confirm-production-generation" in result.stdout
    assert "--authorization-phrase" in result.stdout
    assert "--smoke-execution-report" in result.stdout
    assert "--run-comsol" not in result.stdout
    assert "--joint-route-class" not in result.stdout


def test_prs_source_preflight_accepts_minimum_bin_conditioned_source(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "prs_bin_conditioned_source.csv"
    write_csv_rows(
        candidate,
        [
            {
                "route_id_nodi": "404/W500/D900",
                "diameter_nm": "150",
                "NODI_view": "fixed_660_gold",
                "seed": "11",
                "distribution_type": "edge_norm_1d",
                "bin_id": "edge_00",
                "n_events_bin": "120",
                "response_count_bin": "60",
                "source_scope": "production_candidate_from_real_nodi_event_export",
            }
        ],
    )

    report = build_position_response_source_preflight_report(
        candidate_paths=[candidate]
    )

    assert report["status"] == PRS_SOURCE_PREFLIGHT_PASS_STATUS
    assert report["source_available_candidate_count"] == 1
    assert report["position_response_surface_production_generated"] is False
    assert report["production_generation_performed"] is False
    assert report["no_prs_production_artifact"] is True
    assert validate_position_response_source_preflight_report(report) == []


def _prs_event_fixture_rows() -> list[dict[str, object]]:
    base: dict[str, object] = {
        "route_id_nodi": "404/W500/D900",
        "lambda_nm": "404",
        "W_nominal_nm": "500",
        "D_nm": "900",
        "diameter_nm": "150",
        "NODI_view": "fixed_660_gold",
        "seed": "11",
        "particle_kind": "exosome_synthetic",
    }
    return [
        {**base, "event_id": "evt_000", "x_norm": -0.9, "z_norm": -0.1, "response_detected": "false"},
        {**base, "event_id": "evt_001", "x_norm": -0.4, "z_norm": 0.3, "response_detected": "true"},
        {**base, "event_id": "evt_002", "x_norm": 0.2, "z_norm": -0.2, "response_detected": "false"},
        {**base, "event_id": "evt_003", "x_norm": 0.7, "z_norm": 0.7, "response_detected": "true"},
    ]


def _adequate_prs_bin_source_rows() -> list[dict[str, object]]:
    rows = build_position_response_bin_source_rows_from_events(
        _prs_event_fixture_rows(),
        source_scope=PRS_SOURCE_PRODUCTION_SCOPE,
        source_artifact="unit/adequate_prs_event_fixture.csv",
        source_sha256=VALID_SHA,
    )
    for row in rows:
        row.update(
            {
                "n_events_total_seed": 44100,
                "n_events_bin": 100,
                "response_count_bin": 50,
                "response_rate_bin": "0.5",
                "bin_sample_status": "adequate",
                "sparse_bin_flag": "false",
                "decision_use_allowed": "true",
            }
        )
    return rows


def _edge_primary_xz_diagnostic_prs_bin_source_rows() -> list[dict[str, object]]:
    seed_11_rows = _adequate_prs_bin_source_rows()
    rows: list[dict[str, object]] = []
    for seed in ("11", "22", "33"):
        for source_row in seed_11_rows:
            row = dict(source_row)
            row["seed"] = seed
            if row["distribution_type"] == "xz_norm_2d":
                row.update(
                    {
                        "n_events_bin": 0,
                        "response_count_bin": 0,
                        "response_rate_bin": "",
                        "bin_sample_status": "empty",
                        "sparse_bin_flag": "true",
                        "decision_use_allowed": "false",
                    }
                )
            rows.append(row)
    return rows


def _write_prs_accumulation_route_source(
    path: Path,
    *,
    omit_diameter: int | None = None,
) -> None:
    rows: list[dict[str, object]] = []
    for lambda_nm, width_nm, depth_nm in sorted(PRS_APPROVED_ROUTE_MATRIX):
        for diameter in sorted(PRS_APPROVED_DIAMETERS_NM):
            if diameter == omit_diameter:
                continue
            rows.append(
                {
                    "particle_name": f"exosome_biomimetic_corona_nominal_{diameter}nm",
                    "particle_material": "exosome",
                    "wavelength_nm": lambda_nm,
                    "width_nm": width_nm,
                    "depth_nm": depth_nm,
                }
            )
    write_csv_rows(path, rows)


def test_prs_bin_source_builder_aggregates_event_rows_without_prs_production() -> None:
    source_rows = build_position_response_bin_source_rows_from_events(
        _prs_event_fixture_rows(),
        source_scope="bounded_smoke_fixture_not_production",
        source_artifact="unit/prs_event_fixture.csv",
        source_sha256=VALID_SHA,
    )

    assert len(source_rows) == ROWS_PER_ROUTE_DIAMETER_VIEW
    assert validate_position_response_bin_source_rows(source_rows) == []
    assert {row["bin_source_artifact_version"] for row in source_rows} == {
        "NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_V1"
    }
    assert {row["source_scope"] for row in source_rows} == {
        "bounded_smoke_fixture_not_production"
    }
    assert {row["production_prs_generated"] for row in source_rows} == {"false"}
    assert {row["not_detection_probability"] for row in source_rows} == {"true"}
    assert sum(
        1
        for row in source_rows
        if row["distribution_type"] == "edge_norm_1d" and row["row_kind"] == "base_bin"
    ) == 20
    assert sum(
        1
        for row in source_rows
        if row["distribution_type"] == "xz_norm_2d" and row["row_kind"] == "base_bin"
    ) == 441
    assert sum(1 for row in source_rows if row["row_kind"] == "special_aggregate") == 6
    assert any(
        row["bin_id"] == "selected_annulus_0p5_0p8"
        and int(row["n_events_bin"]) >= 1
        for row in source_rows
    )


@pytest.mark.parametrize(
    "forbidden_field",
    [
        "q_ch_eta",
        "yield",
        "winner",
        "true_W_eff",
        "measured_geometry",
        "optical_solver_output",
        "fabrication_release",
        "P3_solver_conclusion",
    ],
)
def test_prs_bin_source_event_rows_reject_forbidden_positive_claim_fields(
    forbidden_field: str,
) -> None:
    rows = _prs_event_fixture_rows()
    rows[0][forbidden_field] = "true"

    issues = validate_position_response_bin_source_event_rows(rows)

    _assert_has_issue(issues, "PRS-BINSRC-E08")


@pytest.mark.parametrize(
    "forbidden_field",
    [
        "q_ch_eta",
        "yield",
        "winner",
        "true_W_eff",
        "measured_geometry",
        "optical_solver_output",
        "fabrication_release",
        "P3_solver_conclusion",
    ],
)
def test_prs_bin_source_rows_reject_forbidden_positive_claim_fields(
    forbidden_field: str,
) -> None:
    source_rows = build_position_response_bin_source_rows_from_events(
        _prs_event_fixture_rows(),
        source_scope=PRS_SOURCE_PRODUCTION_SCOPE,
        source_artifact="unit/prs_event_fixture.csv",
        source_sha256=VALID_SHA,
    )
    source_rows[0][forbidden_field] = "true"

    issues = validate_position_response_bin_source_rows(source_rows)

    _assert_has_issue(issues, "PRS-BINSRC-V14")


def test_prs_event_rows_from_nodi_slim_events_unlock_source_preflight_only(
    tmp_path: Path,
) -> None:
    events = [
        {
            "initial_position_x_norm": -0.75,
            "initial_position_z_norm": 0.25,
            "features": {"n_peaks": 0},
        },
        {
            "initial_position_x_norm": 0.55,
            "initial_position_z_norm": -0.65,
            "features": {"n_peaks": 1},
        },
    ]
    event_rows = build_position_response_event_rows_from_nodi_events(
        events,
        route=(404, 500, 900),
        diameter_nm=150,
        view="fixed_660_gold",
        seed=11,
        particle_kind="exosome_150nm",
    )

    assert [row["response_detected"] for row in event_rows] == ["false", "true"]
    assert {row["source_scope"] for row in event_rows} == {
        "production_candidate_from_real_nodi_event_export"
    }
    source_rows = build_position_response_bin_source_rows_from_events(
        event_rows,
        source_scope="production_candidate_from_real_nodi_event_export",
        source_artifact="unit/nodi_real_event_rows.csv",
        source_sha256=VALID_SHA,
    )
    assert {row["decision_use_allowed"] for row in source_rows} == {"false"}
    assert {row["bin_sample_status"] for row in source_rows} <= {"empty", "sparse"}
    source_path = tmp_path / "real_event_bin_source.csv"
    write_csv_rows(source_path, source_rows)

    preflight = build_position_response_source_preflight_report(
        candidate_paths=[source_path]
    )

    assert preflight["status"] == PRS_SOURCE_PREFLIGHT_PASS_STATUS
    assert preflight["source_available_candidate_count"] == 1
    assert preflight["position_response_surface_production_generated"] is False
    assert preflight["production_generation_performed"] is False
    assert preflight["no_prs_production_artifact"] is True
    assert not (tmp_path / "NODI_POSITION_RESPONSE_SURFACE.csv").exists()


def test_prs_bin_source_smoke_bundle_does_not_unlock_source_preflight(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "bin-source-smoke"

    smoke = write_position_response_bin_source_smoke_bundle(output_dir)

    assert smoke["status"] == PRS_BIN_SOURCE_SMOKE_PASS_STATUS
    assert smoke["artifact"] == POSITION_RESPONSE_BIN_SOURCE_ARTIFACT
    assert smoke["bin_source_rows"] == ROWS_PER_ROUTE_DIAMETER_VIEW
    assert (output_dir / PRS_BIN_SOURCE_SMOKE_EVENTS_FILENAME).exists()
    source_path = output_dir / PRS_BIN_SOURCE_SMOKE_SOURCE_FILENAME
    assert source_path.exists()
    assert (output_dir / PRS_BIN_SOURCE_SMOKE_REPORT_FILENAME).exists()
    source_rows = read_csv_rows(source_path)
    assert validate_position_response_bin_source_rows(source_rows) == []

    preflight = build_position_response_source_preflight_report(
        candidate_paths=[source_path]
    )

    assert preflight["status"] == PRS_SOURCE_PREFLIGHT_BLOCKED_STATUS
    assert preflight["source_available_candidate_count"] == 0
    assert preflight["candidate_rows"][0]["candidate_status"] == (
        "source_shape_available_not_production_eligible"
    )
    assert preflight["candidate_rows"][0]["source_scope_status"] == (
        "bounded_smoke_scope_not_production_eligible"
    )
    assert preflight["position_response_surface_production_generated"] is False
    assert not (output_dir / "NODI_POSITION_RESPONSE_SURFACE.csv").exists()


def test_prs_source_preflight_rejects_n_events_bin_without_response_count(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "prs_bin_count_without_response_count.csv"
    write_csv_rows(
        candidate,
        [
            {
                "route_id_nodi": "404/W500/D900",
                "diameter_nm": "150",
                "NODI_view": "fixed_660_gold",
                "seed": "11",
                "distribution_type": "edge_norm_1d",
                "bin_id": "edge_00",
                "n_events_bin": "120",
                "source_scope": "production_candidate_from_real_nodi_event_export",
            }
        ],
    )

    preflight = build_position_response_source_preflight_report(
        candidate_paths=[candidate]
    )

    assert preflight["status"] == PRS_SOURCE_PREFLIGHT_BLOCKED_STATUS
    assert preflight["source_available_candidate_count"] == 0
    row = preflight["candidate_rows"][0]
    assert row["response_count_status"] == "missing_per_bin_response_count"
    assert "per_bin_response_count" in row["missing_requirements"]
    assert row["candidate_status"] == "blocked_missing_minimum_prs_source_grain"


def test_prs_source_preflight_blocks_current_route_level_candidates(
    tmp_path: Path,
) -> None:
    candidates = default_position_response_source_candidate_paths(PROJECT_ROOT)
    output_dir = tmp_path / "prs-source-preflight"

    report = write_position_response_source_preflight_bundle(
        candidate_paths=candidates,
        output_dir=output_dir,
    )

    assert report["status"] == PRS_SOURCE_PREFLIGHT_BLOCKED_STATUS
    assert report["source_available_candidate_count"] == 0
    assert report["position_response_surface_production_generated"] is False
    assert (output_dir / PRS_SOURCE_PREFLIGHT_REPORT_FILENAME).exists()
    assert (output_dir / PRS_SOURCE_PREFLIGHT_CANDIDATES_FILENAME).exists()
    assert (output_dir / PRS_SOURCE_PREFLIGHT_BLOCKERS_FILENAME).exists()
    assert (output_dir / PRS_SOURCE_PREFLIGHT_ISSUES_FILENAME).exists()
    candidate_rows = read_csv_rows(output_dir / PRS_SOURCE_PREFLIGHT_CANDIDATES_FILENAME)
    assert candidate_rows
    assert {
        "blocked_missing_minimum_prs_source_grain",
    } == {row["candidate_status"] for row in candidate_rows}
    assert any(
        "distribution_or_bin" in row["missing_requirements"]
        or "per_bin_response_count" in row["missing_requirements"]
        for row in candidate_rows
    )
    assert not (output_dir / "NODI_POSITION_RESPONSE_SURFACE.csv").exists()


def test_prs_source_preflight_cli_writes_blocked_sidecars(tmp_path: Path) -> None:
    output_dir = tmp_path / "prs-source-cli"

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/run_nodi_position_response_source_preflight.py"),
            "--confirm-source-preflight",
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "NODI_POSITION_RESPONSE_SOURCE_PREFLIGHT: BLOCKED_PRS_SOURCE_AVAILABILITY_PREFLIGHT" in result.stdout
    assert (output_dir / PRS_SOURCE_PREFLIGHT_REPORT_FILENAME).exists()
    assert (output_dir / PRS_SOURCE_PREFLIGHT_BLOCKERS_FILENAME).exists()
    payload = json.loads(
        (output_dir / PRS_SOURCE_PREFLIGHT_REPORT_FILENAME).read_text(encoding="utf-8")
    )
    assert payload["position_response_surface_production_generated"] is False
    assert payload["comsol_run_performed"] is False
    assert payload["joint_route_class_regenerated"] is False
    assert payload["source_available_candidate_count"] == 0
    assert not (output_dir / "NODI_POSITION_RESPONSE_SURFACE.csv").exists()


def test_prs_source_sufficiency_blocks_sparse_bin_source(tmp_path: Path) -> None:
    source_rows = build_position_response_bin_source_rows_from_events(
        _prs_event_fixture_rows(),
        source_scope=PRS_SOURCE_PRODUCTION_SCOPE,
        source_artifact="unit/sparse_prs_event_fixture.csv",
        source_sha256=VALID_SHA,
    )
    source_path = tmp_path / "sparse_bin_source.csv"
    write_csv_rows(source_path, source_rows)

    report = build_position_response_source_sufficiency_report(
        candidate_paths=[source_path]
    )

    assert report["status"] == PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS
    assert report["numeric_sufficient_candidate_count"] == 0
    assert report["candidate_rows"][0]["inadequate_row_count"] == str(
        ROWS_PER_ROUTE_DIAMETER_VIEW
    )
    assert report["candidate_rows"][0]["decision_use_disallowed_row_count"] == str(
        ROWS_PER_ROUTE_DIAMETER_VIEW
    )
    assert report["job_plan_rows"][0]["route_id_nodi"] == "404/W500/D900"
    assert report["job_plan_rows"][0]["insufficient_row_count"] == str(
        ROWS_PER_ROUTE_DIAMETER_VIEW
    )
    assert report["job_plan_execution_authorized"] is False
    assert report["job_plan_shortfall_fields_are_diagnostic_not_event_counts"] is True
    assert report["job_plan_rows"][0]["execution_authorized"] == "false"
    assert report["job_plan_rows"][0][
        "shortfall_fields_are_diagnostic_not_event_counts"
    ] == "true"
    assert report["position_response_surface_production_generated"] is False
    assert report["not_true_W_eff"] is True
    assert report["not_measured_geometry"] is True
    assert report["not_optical_solver_output"] is True
    assert report["not_fabrication_release"] is True
    assert report["not_P3_solver_conclusion"] is True
    assert validate_position_response_source_sufficiency_report(report) == []


def test_prs_source_sufficiency_accepts_adequate_bin_source(tmp_path: Path) -> None:
    source_path = tmp_path / "adequate_bin_source.csv"
    write_csv_rows(source_path, _adequate_prs_bin_source_rows())

    report = build_position_response_source_sufficiency_report(
        candidate_paths=[source_path]
    )

    assert report["status"] == PRS_SOURCE_SUFFICIENCY_PASS_STATUS
    assert report["numeric_sufficient_candidate_count"] == 1
    assert report["numeric_sufficient_candidates"] == [str(source_path)]
    assert report["candidate_rows"][0]["inadequate_row_count"] == "0"
    assert report["candidate_rows"][0]["minimum_n_events_bin"] == "100"
    assert report["job_plan_rows"] == []
    assert report["no_prs_production_artifact"] is True
    assert report["job_plan_execution_authorized"] is False
    assert report["job_plan_shortfall_fields_are_diagnostic_not_event_counts"] is True
    assert report["not_true_W_eff"] is True
    assert report["not_measured_geometry"] is True
    assert report["not_optical_solver_output"] is True
    assert report["not_fabrication_release"] is True
    assert report["not_P3_solver_conclusion"] is True
    assert validate_position_response_source_sufficiency_report(report) == []


def test_prs_source_production_eligibility_accepts_edge_primary_with_xz_diagnostic(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "edge_primary_xz_diagnostic_source.csv"
    write_csv_rows(source_path, _edge_primary_xz_diagnostic_prs_bin_source_rows())

    strict_report = build_position_response_source_sufficiency_report(
        candidate_paths=[source_path]
    )
    eligibility_report = build_position_response_source_production_eligibility_report(
        candidate_paths=[source_path]
    )

    assert strict_report["status"] == PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS
    assert strict_report["numeric_sufficient_candidate_count"] == 0
    assert eligibility_report["status"] == PRS_SOURCE_PRODUCTION_ELIGIBILITY_PASS_STATUS
    assert eligibility_report["eligible_candidate_count"] == 1
    assert eligibility_report["eligible_candidates"] == [str(source_path)]
    assert eligibility_report["candidate_rows"][0]["edge_primary_ineligible_row_count"] == "0"
    assert eligibility_report["candidate_rows"][0]["xz_sparse_or_empty_diagnostic_row_count"] == "1332"
    assert eligibility_report["xz_sparse_rows_are_diagnostic_not_blocking_edge_primary"] is True
    assert eligibility_report["xz_primary_promotion_authorized"] is False
    assert eligibility_report["position_response_surface_production_generated"] is False
    assert eligibility_report["no_prs_production_artifact"] is True
    assert (
        validate_position_response_source_production_eligibility_report(
            eligibility_report
        )
        == []
    )


def test_prs_source_production_eligibility_blocks_edge_sparse_source(
    tmp_path: Path,
) -> None:
    source_rows = _edge_primary_xz_diagnostic_prs_bin_source_rows()
    source_rows[0].update(
        {
            "n_events_bin": 99,
            "response_count_bin": 49,
            "response_rate_bin": "0.494949494949",
            "bin_sample_status": "sparse",
            "sparse_bin_flag": "true",
            "decision_use_allowed": "false",
        }
    )
    source_path = tmp_path / "edge_sparse_source.csv"
    write_csv_rows(source_path, source_rows)

    report = build_position_response_source_production_eligibility_report(
        candidate_paths=[source_path]
    )

    assert report["status"] == PRS_SOURCE_PRODUCTION_ELIGIBILITY_BLOCKED_STATUS
    assert report["eligible_candidate_count"] == 0
    assert report["candidate_rows"][0]["edge_primary_ineligible_row_count"] == "1"
    assert report["candidate_rows"][0]["issue_summary"] == "edge_primary_group_ineligible"
    assert report["blockers"][0]["status"] == "blocked_no_edge_primary_eligible_prs_source"
    assert report["position_response_surface_production_generated"] is False
    assert validate_position_response_source_production_eligibility_report(report) == []


def test_prs_source_production_eligibility_cli_writes_pass_sidecars(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "edge_primary_xz_diagnostic_source.csv"
    write_csv_rows(source_path, _edge_primary_xz_diagnostic_prs_bin_source_rows())
    output_dir = tmp_path / "eligibility"

    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/run_nodi_position_response_source_production_eligibility_preflight.py"
            ),
            "--confirm-production-eligibility-preflight",
            "--candidate",
            str(source_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert (
        "NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY: "
        f"{PRS_SOURCE_PRODUCTION_ELIGIBILITY_PASS_STATUS}"
    ) in result.stdout
    report_path = output_dir / PRS_SOURCE_PRODUCTION_ELIGIBILITY_REPORT_FILENAME
    assert report_path.exists()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["eligible_candidate_count"] == 1
    assert payload["position_response_surface_production_generated"] is False
    assert not (output_dir / "NODI_POSITION_RESPONSE_SURFACE.csv").exists()


def test_prs_edge_primary_candidate_builder_validates_production_shape(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "edge_primary_xz_diagnostic_source.csv"
    write_csv_rows(source_path, _edge_primary_xz_diagnostic_prs_bin_source_rows())

    rows = build_position_response_edge_primary_candidate_rows(source_path=source_path)

    assert len(rows) == ROWS_PER_ROUTE_DIAMETER_VIEW
    assert validate_position_response_surface_rows(
        rows,
        production_table=True,
        require_complete_row_arithmetic=True,
    ) == []
    edge_rows = [row for row in rows if row["distribution_type"] == "edge_norm_1d"]
    xz_rows = [row for row in rows if row["distribution_type"] == "xz_norm_2d"]
    assert len(edge_rows) == 23
    assert len(xz_rows) == 444
    assert {row["aggregate_source_type"] for row in edge_rows} == {"edge_norm_primary"}
    assert {row["aggregate_source_type"] for row in xz_rows} == {"xz_norm_diagnostic"}
    assert all(row["decision_use_allowed"] == "true" for row in edge_rows)
    assert all(row["decision_use_allowed"] == "false" for row in xz_rows)
    assert all(row["not_qch_weighted"] == "true" for row in rows)
    assert all(row["not_yield"] == "true" for row in rows)
    assert all(row["not_detection_probability"] == "true" for row in rows)


def test_prs_edge_primary_candidate_bundle_writes_not_promoted_candidate(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "edge_primary_xz_diagnostic_source.csv"
    write_csv_rows(source_path, _edge_primary_xz_diagnostic_prs_bin_source_rows())
    output_dir = tmp_path / "edge-primary-candidate"

    report = write_position_response_edge_primary_candidate_bundle(
        source_path=source_path,
        output_dir=output_dir,
    )

    assert report["status"] == PRS_EDGE_PRIMARY_CANDIDATE_PASS_STATUS
    assert report["candidate_row_count"] == ROWS_PER_ROUTE_DIAMETER_VIEW
    assert report["xz_primary_promoted_row_count"] == 0
    assert report["candidate_promoted_to_production_gate"] is False
    assert report["production_generation_performed"] is False
    assert report["comsol_run_performed"] is False
    assert (output_dir / PRS_EDGE_PRIMARY_CANDIDATE_FILENAME).exists()
    assert (output_dir / PRS_EDGE_PRIMARY_CANDIDATE_REPORT_FILENAME).exists()


def test_prs_edge_primary_candidate_cli_writes_validated_candidate(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "edge_primary_xz_diagnostic_source.csv"
    write_csv_rows(source_path, _edge_primary_xz_diagnostic_prs_bin_source_rows())
    output_dir = tmp_path / "edge-primary-candidate-cli"

    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/build_nodi_position_response_edge_primary_candidate.py"
            ),
            "--confirm-edge-primary-candidate",
            "--source",
            str(source_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert (
        "NODI_POSITION_RESPONSE_EDGE_PRIMARY_CANDIDATE: "
        f"{PRS_EDGE_PRIMARY_CANDIDATE_PASS_STATUS}"
    ) in result.stdout
    candidate_path = output_dir / PRS_EDGE_PRIMARY_CANDIDATE_FILENAME
    assert candidate_path.exists()
    rows = read_csv_rows(candidate_path)
    assert validate_position_response_surface_rows(
        rows,
        production_table=True,
        require_complete_row_arithmetic=True,
    ) == []
    report_payload = json.loads(
        (output_dir / PRS_EDGE_PRIMARY_CANDIDATE_REPORT_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert report_payload["candidate_promoted_to_production_gate"] is False
    assert report_payload["xz_primary_promoted_row_count"] == 0


def test_prs_source_sufficiency_cli_writes_pass_sidecars(tmp_path: Path) -> None:
    source_path = tmp_path / "adequate_bin_source.csv"
    write_csv_rows(source_path, _adequate_prs_bin_source_rows())
    output_dir = tmp_path / "source-sufficiency-pass"

    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/run_nodi_position_response_source_sufficiency_preflight.py"
            ),
            "--confirm-source-sufficiency-preflight",
            "--candidate-source",
            str(source_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert PRS_SOURCE_SUFFICIENCY_PASS_STATUS in result.stdout
    assert (output_dir / PRS_SOURCE_SUFFICIENCY_REPORT_FILENAME).exists()
    assert (output_dir / PRS_SOURCE_SUFFICIENCY_CANDIDATES_FILENAME).exists()
    assert (output_dir / PRS_SOURCE_SUFFICIENCY_BLOCKERS_FILENAME).exists()
    assert (output_dir / PRS_SOURCE_SUFFICIENCY_JOB_PLAN_FILENAME).exists()
    assert (output_dir / PRS_SOURCE_SUFFICIENCY_ISSUES_FILENAME).exists()
    assert {path.name for path in output_dir.iterdir()} == {
        PRS_SOURCE_SUFFICIENCY_REPORT_FILENAME,
        PRS_SOURCE_SUFFICIENCY_CANDIDATES_FILENAME,
        PRS_SOURCE_SUFFICIENCY_BLOCKERS_FILENAME,
        PRS_SOURCE_SUFFICIENCY_JOB_PLAN_FILENAME,
        PRS_SOURCE_SUFFICIENCY_ISSUES_FILENAME,
    }
    payload = json.loads(
        (output_dir / PRS_SOURCE_SUFFICIENCY_REPORT_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert payload["status"] == PRS_SOURCE_SUFFICIENCY_PASS_STATUS
    assert payload["numeric_sufficient_candidate_count"] == 1
    assert payload["job_plan_execution_authorized"] is False
    assert payload["position_response_surface_production_generated"] is False
    assert payload["comsol_run_performed"] is False
    assert payload["joint_route_class_regenerated"] is False
    assert not (output_dir / "NODI_POSITION_RESPONSE_SURFACE.csv").exists()


def test_prs_source_sufficiency_cli_writes_blocked_sidecars(tmp_path: Path) -> None:
    source_rows = build_position_response_bin_source_rows_from_events(
        _prs_event_fixture_rows(),
        source_scope=PRS_SOURCE_PRODUCTION_SCOPE,
        source_artifact="unit/sparse_prs_event_fixture.csv",
        source_sha256=VALID_SHA,
    )
    source_path = tmp_path / "sparse_bin_source.csv"
    write_csv_rows(source_path, source_rows)
    output_dir = tmp_path / "source-sufficiency"

    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/run_nodi_position_response_source_sufficiency_preflight.py"
            ),
            "--confirm-source-sufficiency-preflight",
            "--candidate-source",
            str(source_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS in result.stdout
    assert (output_dir / PRS_SOURCE_SUFFICIENCY_REPORT_FILENAME).exists()
    assert (output_dir / PRS_SOURCE_SUFFICIENCY_CANDIDATES_FILENAME).exists()
    assert (output_dir / PRS_SOURCE_SUFFICIENCY_BLOCKERS_FILENAME).exists()
    assert (output_dir / PRS_SOURCE_SUFFICIENCY_JOB_PLAN_FILENAME).exists()
    assert (output_dir / PRS_SOURCE_SUFFICIENCY_ISSUES_FILENAME).exists()
    payload = json.loads(
        (output_dir / PRS_SOURCE_SUFFICIENCY_REPORT_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    job_rows = read_csv_rows(output_dir / PRS_SOURCE_SUFFICIENCY_JOB_PLAN_FILENAME)
    assert payload["job_plan_execution_authorized"] is False
    assert payload["job_plan_shortfall_fields_are_diagnostic_not_event_counts"] is True
    assert job_rows[0]["execution_authorized"] == "false"
    assert job_rows[0]["shortfall_fields_are_diagnostic_not_event_counts"] == "true"
    assert not (output_dir / "NODI_POSITION_RESPONSE_SURFACE.csv").exists()


def test_prs_bin_source_smoke_cli_writes_source_only(tmp_path: Path) -> None:
    output_dir = tmp_path / "prs-bin-source-cli"

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/build_nodi_position_response_bin_source.py"),
            "--confirm-smoke-source",
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (
        "NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE: "
        "PASS_PRS_BIN_SOURCE_SMOKE_NOT_PRODUCTION"
    ) in result.stdout
    assert (output_dir / PRS_BIN_SOURCE_SMOKE_EVENTS_FILENAME).exists()
    assert (output_dir / PRS_BIN_SOURCE_SMOKE_SOURCE_FILENAME).exists()
    assert (output_dir / PRS_BIN_SOURCE_SMOKE_REPORT_FILENAME).exists()
    payload = json.loads(
        (output_dir / PRS_BIN_SOURCE_SMOKE_REPORT_FILENAME).read_text(encoding="utf-8")
    )
    assert payload["position_response_surface_production_generated"] is False
    assert payload["production_generation_performed"] is False
    assert payload["comsol_run_performed"] is False
    assert payload["joint_route_class_regenerated"] is False
    assert not (output_dir / "NODI_POSITION_RESPONSE_SURFACE.csv").exists()


def test_prs_real_event_source_smoke_cli_help_is_preflight_only() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/run_nodi_position_response_real_event_source_smoke.py"
            ),
            "--help",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--confirm-real-event-source-smoke" in result.stdout
    assert PRS_REAL_EVENT_SOURCE_SMOKE_EVENTS_FILENAME in result.stdout
    assert PRS_REAL_EVENT_SOURCE_SMOKE_SOURCE_FILENAME in result.stdout
    assert PRS_REAL_EVENT_SOURCE_SMOKE_REPORT_FILENAME in result.stdout
    assert PRS_REAL_EVENT_SOURCE_SMOKE_PASS_STATUS not in result.stdout
    assert "never generates" in result.stdout
    assert "NODI_POSITION_RESPONSE_SURFACE" in result.stdout
    assert "--run-comsol" not in result.stdout
    assert "--joint-route-class" not in result.stdout


def test_prs_real_event_source_smoke_cli_requires_confirm(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/run_nodi_position_response_real_event_source_smoke.py"
            ),
            "--output-dir",
            str(tmp_path / "real-event-source-smoke"),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-real-event-source-smoke" in result.stderr
    assert not (tmp_path / "real-event-source-smoke").exists()


def test_prs_runner_slice_source_export_validates_route_source_slice(
    tmp_path: Path,
) -> None:
    route_source = tmp_path / "runner_slice_source.csv"
    write_csv_rows(
        route_source,
        [
            {
                "particle_name": "exosome_biomimetic_corona_nominal_150nm",
                "particle_material": "exosome",
                "particle_family": "exosome_biomimetic",
                "wavelength_nm": "404",
                "width_nm": "500",
                "depth_nm": "900",
            },
            {
                "particle_name": "gold_150nm",
                "particle_material": "gold",
                "particle_family": "gold",
                "wavelength_nm": "660",
                "width_nm": "800",
                "depth_nm": "900",
            },
        ],
    )

    metadata = validate_route_source_slice(
        route_source,
        route=(404, 500, 900),
        particle_name="exosome_biomimetic_corona_nominal_150nm",
        particle_scope="ev_gold",
    )

    assert metadata["route_source_exact_slice_row_count"] == 1
    assert metadata["route_source_unique_route_count"] == 2
    assert metadata["route_source_unique_particle_count"] == 2
    assert metadata["selected_particle_material"] == "exosome"
    assert metadata["selected_particle_family"] == "exosome_biomimetic"
    assert metadata["route_source_scope"] == (
        "selected_route_particle_slice_validated_no_fullgrid_coverage_claim"
    )


def test_prs_runner_slice_source_export_cli_help_is_preflight_only() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/run_nodi_position_response_runner_slice_source_export.py"
            ),
            "--help",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "--confirm-runner-slice-event-source" in result.stdout
    assert "--route-source" in result.stdout
    assert PRS_RUNNER_SLICE_SOURCE_EXPORT_EVENTS_FILENAME in result.stdout
    assert PRS_RUNNER_SLICE_SOURCE_EXPORT_SOURCE_FILENAME in result.stdout
    assert PRS_RUNNER_SLICE_SOURCE_EXPORT_REPORT_FILENAME in result.stdout
    assert PRS_RUNNER_SLICE_SOURCE_EXPORT_PASS_STATUS not in result.stdout
    assert "never generates" in result.stdout
    assert "NODI_POSITION_RESPONSE_SURFACE" in result.stdout
    assert "--run-comsol" not in result.stdout
    assert "--joint-route-class" not in result.stdout


def test_prs_runner_slice_source_export_cli_requires_confirm(tmp_path: Path) -> None:
    route_source = tmp_path / "runner_slice_source.csv"
    write_csv_rows(
        route_source,
        [
            {
                "particle_name": "exosome_biomimetic_corona_nominal_150nm",
                "particle_material": "exosome",
                "wavelength_nm": "404",
                "width_nm": "500",
                "depth_nm": "900",
            }
        ],
    )
    output_dir = tmp_path / "runner-slice-source-export"

    result = subprocess.run(
        [
            sys.executable,
            str(
                PROJECT_ROOT
                / "tools/audits/run_nodi_position_response_runner_slice_source_export.py"
            ),
            "--route-source",
            str(route_source),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-runner-slice-event-source" in result.stderr
    assert not output_dir.exists()


def test_prs_runner_slice_source_export_cli_success_is_preflight_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    import tools.audits.run_nodi_position_response_runner_slice_source_export as runner_slice_export

    route_source = tmp_path / "runner_slice_source.csv"
    write_csv_rows(
        route_source,
        [
            {
                "particle_name": "exosome_biomimetic_corona_nominal_150nm",
                "particle_material": "exosome",
                "particle_family": "exosome_biomimetic",
                "wavelength_nm": "404",
                "width_nm": "500",
                "depth_nm": "900",
            }
        ],
    )
    fake_events = [
        {
            "initial_position_x_norm": x_norm,
            "initial_position_z_norm": z_norm,
            "features": {"n_peaks": n_peaks},
        }
        for x_norm, z_norm, n_peaks in [
            (-0.92, -0.25, 0),
            (-0.52, 0.11, 1),
            (-0.12, 0.18, 0),
            (0.08, -0.04, 1),
            (0.44, 0.72, 1),
            (0.88, -0.88, 0),
        ]
    ]
    monkeypatch.setattr(
        runner_slice_export,
        "build_frozen_b_cfg",
        lambda _n_events, _seed: (
            SimpleNamespace(),
            SimpleNamespace(wavelength_m=0.0),
        ),
    )
    monkeypatch.setattr(
        runner_slice_export,
        "_cfg_for_normalization_lane",
        lambda base_cfg, _view: base_cfg,
    )
    monkeypatch.setattr(
        runner_slice_export,
        "_resolve_e_sca_ref",
        lambda **_kwargs: 1.0,
    )
    monkeypatch.setattr(
        runner_slice_export,
        "particle_from_name",
        lambda _name: SimpleNamespace(name="fake_exosome"),
    )
    monkeypatch.setattr(runner_slice_export, "infer_particle_diameter_nm", lambda _name: 150)
    monkeypatch.setattr(runner_slice_export, "medium_for_particle", lambda _particle: "water")
    monkeypatch.setattr(
        runner_slice_export.lane,
        "case_baseline_channel",
        lambda _width_nm, _depth_nm: SimpleNamespace(),
    )
    monkeypatch.setattr(
        runner_slice_export,
        "run_single_case_batch",
        lambda *_args, **_kwargs: {"events": fake_events},
    )
    output_dir = tmp_path / "runner-slice-success"

    exit_code = runner_slice_export.main(
        [
            "--confirm-runner-slice-event-source",
            "--route-source",
            str(route_source),
            "--output-dir",
            str(output_dir),
            "--route",
            "404/W500/D900",
            "--particle-name",
            "exosome_biomimetic_corona_nominal_150nm",
            "--NODI-view",
            "fixed_660_gold",
            "--seed",
            "11",
            "--n-events",
            "6",
        ]
    )

    assert exit_code == 0
    event_path = output_dir / PRS_RUNNER_SLICE_SOURCE_EXPORT_EVENTS_FILENAME
    source_path = output_dir / PRS_RUNNER_SLICE_SOURCE_EXPORT_SOURCE_FILENAME
    report_path = output_dir / PRS_RUNNER_SLICE_SOURCE_EXPORT_REPORT_FILENAME
    preflight_report_path = output_dir / PRS_SOURCE_PREFLIGHT_REPORT_FILENAME
    report = json.loads(report_path.read_text())
    preflight_report = json.loads(preflight_report_path.read_text())
    event_rows = read_csv_rows(event_path)
    source_rows = read_csv_rows(source_path)

    assert report["status"] == PRS_RUNNER_SLICE_SOURCE_EXPORT_PASS_STATUS
    assert report["preflight_only"] is True
    assert report["nodi_event_rows"] == 6
    assert report["bin_source_rows"] == ROWS_PER_ROUTE_DIAMETER_VIEW
    assert report["source_preflight_status"] == PRS_SOURCE_PREFLIGHT_PASS_STATUS
    assert report["source_available_candidate_count"] == 1
    assert report["decision_use_allowed_values"] == ["false"]
    assert report["comsol_run_performed"] is False
    assert report["joint_route_class_regenerated"] is False
    assert report["position_response_surface_production_generated"] is False
    assert preflight_report["status"] == PRS_SOURCE_PREFLIGHT_PASS_STATUS
    assert preflight_report["no_prs_production_artifact"] is True
    assert len(event_rows) == 6
    assert len(source_rows) == ROWS_PER_ROUTE_DIAMETER_VIEW
    assert {row["decision_use_allowed"] for row in source_rows} == {"false"}
    assert {row["bin_sample_status"] for row in source_rows} <= {"empty", "sparse"}
    assert not (output_dir / "NODI_POSITION_RESPONSE_SURFACE.csv").exists()


def test_prs_edge_primary_candidate_merge_blocks_duplicate_rows(tmp_path: Path) -> None:
    source_path = tmp_path / "edge_primary_xz_diagnostic_source.csv"
    write_csv_rows(source_path, _edge_primary_xz_diagnostic_prs_bin_source_rows())
    candidate_rows = build_position_response_edge_primary_candidate_rows(
        source_path=source_path
    )
    candidate_path = tmp_path / "NODI_POSITION_RESPONSE_SURFACE.csv"
    write_csv_rows(candidate_path, candidate_rows)

    merged_rows, manifest_rows, issues = merge_candidate_rows(
        [candidate_path, candidate_path]
    )

    assert len(merged_rows) == len(candidate_rows)
    assert len(manifest_rows) == 2
    assert any("MERGE-PRS-C03" in issue for issue in issues)
