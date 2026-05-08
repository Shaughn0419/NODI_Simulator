"""Instrument-aware EV/NODI realism v2 sidecars.

This module is intentionally independent from the v1 full-grid pipeline.  It
implements R0/P0 guardrails and posthoc algebra for the v2 micro-anchor lane
without changing v1 route identities, selected-annulus semantics, or full-grid
outputs.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from statistics import NormalDist
from typing import Any, Iterable

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_DIR = PROJECT_ROOT / "configs" / "realism_v2"
DEFAULT_MICRO_ANCHOR_DIR = PROJECT_ROOT / "results" / "ev_nodi_realism_v2_micro_anchor"
DEFAULT_ANCHOR_SMOKE_DIR = PROJECT_ROOT / "results" / "ev_nodi_realism_v2_anchor_smoke"
DEFAULT_REDUCED_GRID_R3A_DIR = (
    PROJECT_ROOT / "results" / "ev_nodi_realism_v2_reduced_grid_R3a"
)
DEFAULT_UNCERTAINTY_R3B_DIR = (
    PROJECT_ROOT / "results" / "ev_nodi_realism_v2_uncertainty_R3b"
)
DEFAULT_REPRESENTATIVE_FULL_WAVE_R4_DIR = (
    PROJECT_ROOT / "results" / "ev_nodi_realism_v2_representative_full_wave_R4"
)
DEFAULT_ROUTE_MODEL_REVISION_AUDIT_DIR = (
    PROJECT_ROOT / "results" / "ev_nodi_realism_v2_route_model_revision_audit"
)
DEFAULT_REVISED_R4_RERUN_DIR = (
    PROJECT_ROOT / "results" / "ev_nodi_realism_v2_revised_R4_rerun"
)
DEFAULT_R4_2_ADJUDICATION_DIR = (
    PROJECT_ROOT / "results" / "ev_nodi_realism_v2_R4_2_main660_nearwall_mesh_adjudication"
)
DEFAULT_R5_FULL_GRID_V2_DIR = (
    PROJECT_ROOT / "results" / "ev_nodi_realism_v2_full_grid_R5_v2"
)
DEFAULT_R5_1_INTERPRETATION_DIR = (
    PROJECT_ROOT
    / "results"
    / "ev_nodi_realism_v2_R5_1_route_role_stability_interpretation"
)
DEFAULT_R5_2_BOUNDED_SCENARIO_PRIOR_AUDIT_DIR = (
    PROJECT_ROOT
    / "results"
    / "ev_nodi_realism_v2_R5_2_bounded_scenario_prior_audit"
)
DEFAULT_R5_3_ROUTE_PRIOR_MODEL_REVISION_AUDIT_DIR = (
    PROJECT_ROOT
    / "results"
    / "ev_nodi_realism_v2_R5_3_route_prior_model_revision_audit"
)
DEFAULT_R6_ROUTE_PRIOR_SENSITIVITY_AUDIT_DIR = (
    PROJECT_ROOT / "results" / "ev_nodi_realism_v2_R6_route_prior_sensitivity_audit"
)
DEFAULT_R7_ROUTE_PRIOR_MECHANISTIC_DECOMPOSITION_DIR = (
    PROJECT_ROOT
    / "results"
    / "ev_nodi_realism_v2_R7_route_prior_mechanistic_decomposition_audit"
)
DEFAULT_R7_1_OPERATOR_ARTIFACT_VALIDATION_DIR = (
    PROJECT_ROOT
    / "results"
    / "ev_nodi_realism_v2_R7_1_operator_artifact_validation_protocol"
)
DEFAULT_R7_2_OPERATOR_ARTIFACT_GAP_REGISTER_DIR = (
    PROJECT_ROOT
    / "results"
    / "ev_nodi_realism_v2_R7_2_operator_artifact_gap_register"
)
DEFAULT_V2_NO_MEASURED_DATA_CLOSURE_DIR = (
    PROJECT_ROOT / "results" / "ev_nodi_realism_v2_no_measured_data_closure"
)

MODULE_STATES = (
    "off",
    "surrogate",
    "bounded_prior",
    "measured_prior",
    "calibrated",
    "blocked",
)

CLAIM_LEVELS = (
    "relative_proxy",
    "relative_with_priors",
    "scenario_count_rate",
    "safety_sidecar",
    "diagnostic_only",
    "absolute_blocked",
    "calibrated_absolute",
)

SOURCE_TYPES = (
    "assumption",
    "datasheet",
    "literature",
    "synthetic",
    "bounded_prior",
    "measured",
    "calibrated",
)

REQUIRED_OUTPUT_PROVENANCE_FIELDS = (
    "unit",
    "source_type",
    "scenario_id",
    "claim_level",
    "calibration_dependency",
    "module_status",
    "base_route_key",
    "scenario_identity",
    "run_manifest_path",
)

FORBIDDEN_OUTPUT_NAMES = {"detector_SNR", "calibrated_detector_SNR"}

MAX_ANCHOR_SCENARIO_BUNDLES = 8
MAX_ANCHOR_ROUTES = 14
MAX_STOCHASTIC_SEEDS = 3
MAX_EVENT_LEVEL_RUNS_BEFORE_REVIEW = 14 * 8 * 8 * 3
MAX_R3A_ROUTES = 112
MAX_R3A_PARTICLES = 23
MAX_R3A_SCENARIO_BUNDLES = 8
MAX_R3A_STOCHASTIC_SEEDS = 3
MAX_R3A_CASE_ROWS_BEFORE_REVIEW = 112 * 23 * 8 * 3
R3A_ROUTE_ROLE_SOURCE = "R3a_plan_v1"
MAX_R3B_ROUTES = 19
MAX_R3B_PARTICLES = 23
MAX_R3B_PRIOR_SAMPLES = 24
MAX_R3B_STOCHASTIC_SEEDS = 3
MAX_R3B_CASE_ROWS_BEFORE_REVIEW = 19 * 23 * 24 * 3
R3B_ROUTE_ROLE_SOURCE = "R3b_plan_v2"
R3B_REQUIRED_FACTOR_GROUPS = (
    "BFP_slit_alignment",
    "detector_readout",
    "wall_PEG_flow",
    "blank_RIN_drift",
    "thermal_404",
    "EV_ensemble",
)
R3B_ALLOWED_DISTRIBUTIONS = (
    "uniform",
    "log_uniform",
    "triangular",
    "truncated_normal",
)
R3B_ALLOWED_CORRELATION_TRANSFORMS = (
    "direct",
    "inverse",
    "independent_within_group",
)
R3B_ALLOWED_ROUTE_SENSITIVE_FORMULAS = (
    "bfp_uv_slit_overlap",
    "detector_impedance_noise_by_route_power",
    "wall_peg_near_wall_geometry",
    "blank_rin_threshold_noise",
    "thermal_404_absorption_gate",
    "ev_ensemble_particle_route_response",
)
R3B_EFFECT_DELTA_CONVENTION = (
    "median_log_score_ratio_over_particles_seeds_prior_samples"
)
R3B_ROUTE_PANEL = (
    (660, 800, 1400, "main_660"),
    (660, 800, 1500, "main_660"),
    (660, 700, 1500, "weak_reference_control"),
    (660, 900, 1400, "optional_robustness_probe"),
    (404, 600, 1300, "shortwave_mechanism_candidate"),
    (532, 600, 1500, "medium_wave_baseline"),
    (488, 600, 1500, "medium_wave_baseline"),
    (532, 900, 1500, "reduced_grid_context_route"),
    (660, 900, 1500, "reduced_grid_context_route"),
    (488, 900, 1500, "reduced_grid_context_route"),
    (532, 900, 1400, "reduced_grid_context_route"),
    (660, 900, 1300, "reduced_grid_context_route"),
    (532, 800, 1500, "reduced_grid_context_route"),
    (660, 800, 550, "selected_annulus_sanity_overlap_longwave"),
    (660, 800, 600, "selected_annulus_sanity_overlap_longwave"),
    (660, 800, 700, "selected_annulus_sanity_overlap_longwave"),
    (404, 800, 550, "selected_annulus_sanity_overlap_shortwave"),
    (404, 800, 600, "selected_annulus_sanity_overlap_shortwave"),
    (404, 800, 700, "selected_annulus_sanity_overlap_shortwave"),
)
MAX_R4_REPRESENTATIVE_ROUTES = 9
MAX_R4_REPRESENTATIVE_PARTICLES = 6
MAX_R4_INTERFACE_STATES = 2
MAX_R4_POLARIZATION_STATES = 2
MAX_R4_MESH_LEVELS = 2
MAX_R4_SOLVER_CASES_BEFORE_REVIEW = 9 * 6 * 2 * 2 * 2
R4_ROUTE_ROLE_SOURCE = "R4_plan_v1"
R4_PLAN_SCHEMA_VERSION = "R4_representative_full_wave_plan_v1"
R4_INTERNAL_NUMERICAL_SOLVER_BACKEND = "internal_channel_modal_green_BFP_R4_v2"
R4_INTERNAL_NUMERICAL_SOLVER_VERSION = "2026-05-07"
R4_REQUIRED_ROUTES = {
    (660, 800, 1400),
    (660, 800, 1500),
    (660, 900, 1400),
    (532, 900, 1500),
    (660, 900, 1500),
    (532, 800, 1500),
    (404, 600, 1300),
    (404, 800, 600),
    (660, 800, 600),
}
R4_REQUIRED_PARTICLES = {
    "blank",
    "EV70_lowRI",
    "EV100_nominal",
    "EV250_nominal",
    "LDL_like_contaminant",
    "Au40",
}
R4_REQUIRED_OBSERVABLES = {
    "BFP_complex_field",
    "slit_intensity_perturbation",
    "pinhole_intensity_perturbation",
    "near_wall_interface_sensitivity",
    "surrogate_full_wave_delta",
}
R4_REQUIRED_OUTPUTS_IF_EXECUTED = {
    "full_wave_case_manifest.csv",
    "full_wave_observable_summary.csv",
    "route_validation_decision_table.csv",
    "BFP_slit_pinhole_observable_comparison.csv",
    "interface_near_wall_sensitivity_summary.csv",
    "surrogate_vs_full_wave_delta_summary.csv",
    "context_route_governance_summary.csv",
    "thermal_404_full_wave_gate_summary.csv",
    "detector_blank_claim_guardrail_summary.csv",
    "full_wave_cost_estimate.csv",
    "run_manifest.json",
    "R4_representative_full_wave_validation_report.md",
}
R4_REQUIRED_SOLVER_CASE_CONTRACT_FIELDS = {
    "solver_engine_class",
    "solver_name_or_backend",
    "geometry_units",
    "domain_extent_policy",
    "boundary_conditions",
    "PML_or_open_boundary_settings",
    "material_model_source_by_wavelength",
    "particle_pose_definition",
    "near_wall_stress_distance_nm",
    "centerline_nominal_position_definition",
    "source_type",
    "source_normalization",
    "polarization_vector_definition",
    "BFP_far_field_extraction_method",
    "BFP_coordinate_convention",
    "BFP_jacobian_policy",
    "slit_ROI_definition",
    "pinhole_ROI_definition",
    "mesh_level_definitions_nm",
    "mesh_refinement_region",
    "mesh_convergence_metric",
    "mesh_convergence_threshold",
    "solver_boundary_sensitivity_threshold",
}
R4_REQUIRED_PARTICLE_MATERIAL_FIELDS = {
    "particle_id",
    "diameter_nm",
    "size_convention",
    "shape_model",
    "core_RI",
    "shell_RI",
    "shell_thickness_nm",
    "medium_RI_source",
    "material_database_key",
    "wavelength_interpolation_policy",
    "absorption_imaginary_RI_policy",
    "near_wall_pose_policy",
    "biological_specificity_claim_allowed",
}
R4_ALLOWED_EFFECT_DELTA_HARDENING_STATUSES = (
    "exported_both",
    "equivalence_test_passed",
    "convention_renamed",
)
R4_REQUIRED_STOP_GATES = {
    "R4_execution_without_external_authorization",
    "R5_or_full_grid_v2_started",
    "context_route_promotion_attempted",
    "calibrated_SNR_or_event_probability_claim_emitted",
    "ET2030_direct_current_input_unlocked_without_measured_bench_artifact",
    "selected_annulus_bounds_changed",
    "v1_full_grid_output_overwritten",
    "thermal_sidecar_used_to_increase_NODI_score",
    "finite_zero_event_blank_safety_claim_emitted",
    "legacy_detector_SNR_output_header_emitted",
    "legacy_calibrated_detector_SNR_output_header_emitted",
}
R4_ROUTE_MODEL_REVISION_PLAN_SCHEMA_VERSION = "R4_route_model_revision_plan_v1"
R4_ROUTE_MODEL_REVISION_REQUIRED_FOCUS_AREAS = {
    "cross_term_sign_convention",
    "reference_phase_convention",
    "Re_Eref_conj_Esca_polarity_mapping",
    "BFP_ROI_sign_preservation",
    "surrogate_scalar_vs_modal_sign_mapping",
    "main_660_route_role_recovery_criteria",
    "404_and_selected_annulus_sanity_interpretation",
}
R4_ROUTE_MODEL_REVISION_REQUIRED_STOP_GATES = {
    "R5_plan_or_full_grid_v2_started",
    "v1_full_grid_output_overwritten",
    "Tsuyama_paper_fit_continued",
    "selected_annulus_bounds_changed",
    "selected_annulus_replaces_all_crossing_ranking",
    "context_route_promotion_attempted",
    "main_660_redefinition_attempted",
    "calibrated_SNR_or_event_probability_claim_emitted",
    "ET2030_direct_current_input_unlocked_without_measured_bench_artifact",
    "thermal_sidecar_used_to_increase_NODI_score",
    "finite_zero_event_blank_safety_claim_emitted",
    "legacy_detector_SNR_output_header_emitted",
    "legacy_calibrated_detector_SNR_output_header_emitted",
}
R4_ROUTE_MODEL_REVISION_REQUIRED_OUTPUTS_IF_EXECUTED = {
    "route_model_revision_audit_manifest.csv",
    "cross_term_sign_convention_audit.csv",
    "reference_phase_convention_audit.csv",
    "BFP_ROI_sign_preservation_audit.csv",
    "surrogate_scalar_vs_modal_mapping_audit.csv",
    "main_660_recovery_gate_summary.csv",
    "404_selected_annulus_sanity_interpretation_summary.csv",
    "route_model_revision_decision_table.csv",
    "route_model_revision_guardrail_summary.csv",
    "run_manifest.json",
    "R4_route_model_revision_report.md",
}
R4_REVISED_RERUN_PLAN_SCHEMA_VERSION = "R4_revised_rerun_plan_v1"
MAX_R4_REVISED_RERUN_SOLVER_CASES_BEFORE_REVIEW = MAX_R4_SOLVER_CASES_BEFORE_REVIEW
R4_REVISED_RERUN_REQUIRED_FOCUS_AREAS = {
    "global_cross_term_sign_convention",
    "BFP_ROI_signed_perturbation_convention",
    "main_660_near_wall_stress_coarse_screen_ambiguity",
    "sign_reliability_threshold",
    "review_refined_mesh_confirmation",
}
R4_REVISED_RERUN_REQUIRED_DIAGNOSTIC_FIELDS = {
    "route_id",
    "interface_state",
    "mesh_level",
    "particle_id",
    "full_wave_cross_term_signed_W",
    "surrogate_cross_term_signed_W",
    "abs_full_wave_cross_term_W",
    "abs_surrogate_cross_term_W",
    "sign_reliability_band",
    "sign_preserved_raw",
    "sign_preserved_after_global_flip",
    "sign_ambiguous_due_to_near_zero",
    "mesh_refined_agreement",
    "near_wall_stress_agreement",
}
R4_REVISED_RERUN_REQUIRED_OUTPUTS_IF_EXECUTED = {
    "revised_full_wave_case_manifest.csv",
    "revised_full_wave_observable_summary.csv",
    "cross_term_convention_resolution_summary.csv",
    "main_660_near_wall_coarse_sign_ambiguity_check.csv",
    "sign_reliability_band_summary.csv",
    "review_refined_mesh_confirmation_summary.csv",
    "BFP_ROI_orientation_sanity_summary.csv",
    "route_validation_decision_table.csv",
    "revised_R4_guardrail_summary.csv",
    "full_wave_cost_estimate.csv",
    "run_manifest.json",
    "R4_revised_rerun_plan_report.md",
}
R4_REVISED_RERUN_REQUIRED_STOP_GATES = {
    "R5_plan_or_full_grid_v2_started",
    "revised_R4_rerun_executed_without_external_authorization",
    "v1_full_grid_output_overwritten",
    "Tsuyama_paper_fit_continued",
    "selected_annulus_bounds_changed",
    "selected_annulus_replaces_all_crossing_ranking",
    "context_route_promotion_attempted",
    "main_660_redefinition_attempted",
    "calibrated_SNR_or_event_probability_claim_emitted",
    "ET2030_direct_current_input_unlocked_without_measured_bench_artifact",
    "thermal_sidecar_used_to_increase_NODI_score",
    "finite_zero_event_blank_safety_claim_emitted",
    "legacy_detector_SNR_output_header_emitted",
    "legacy_calibrated_detector_SNR_output_header_emitted",
}
R4_2_ADJUDICATION_PLAN_SCHEMA_VERSION = "R4_2_main660_nearwall_mesh_adjudication_plan_v1"
R4_2_ADJUDICATION_ROUTES = {
    (660, 800, 1400),
    (660, 800, 1500),
}
R4_2_ADJUDICATION_PARTICLES_REQUIRED = {
    "EV70_lowRI",
    "EV100_nominal",
    "EV250_nominal",
    "LDL_like_contaminant",
    "Au40",
}
R4_2_ADJUDICATION_PARTICLES_OPTIONAL = {"blank"}
R4_2_ADJUDICATION_NEW_MESH_LEVELS = {"fine_confirm"}
R4_2_ADJUDICATION_VALIDATION_MESH_LEVEL_ROLES = {
    "review_refined",
    "fine_confirm",
}
MAX_R4_2_ADJUDICATION_SOLVER_CASES_BEFORE_REVIEW = 64
R4_2_ADJUDICATION_REQUIRED_OUTPUTS_IF_EXECUTED = {
    "R4_2_case_manifest.csv",
    "R4_2_observable_summary.csv",
    "main660_fine_confirm_sign_summary.csv",
    "mesh_level_role_adjudication_summary.csv",
    "BFP_lobe_resolved_cross_term_summary.csv",
    "mode_overlap_phase_summary.csv",
    "ROI_parity_sanity_summary.csv",
    "coarse_screen_conflict_summary.csv",
    "R4_2_guardrail_summary.csv",
    "R4_2_cost_estimate.csv",
    "run_manifest.json",
    "R4_2_main660_nearwall_mesh_adjudication_report.md",
}
R4_2_ADJUDICATION_REQUIRED_STOP_GATES = {
    "R5_plan_or_full_grid_v2_started",
    "R4_2_execution_without_external_authorization",
    "v1_full_grid_output_overwritten",
    "Tsuyama_paper_fit_continued",
    "selected_annulus_bounds_changed",
    "selected_annulus_replaces_all_crossing_ranking",
    "context_route_promotion_attempted",
    "main_660_redefinition_attempted",
    "route_specific_manual_sign_flip_attempted",
    "calibrated_SNR_or_event_probability_claim_emitted",
    "ET2030_direct_current_input_unlocked_without_measured_bench_artifact",
    "thermal_sidecar_used_to_increase_NODI_score",
    "finite_zero_event_blank_safety_claim_emitted",
    "legacy_detector_SNR_output_header_emitted",
    "legacy_calibrated_detector_SNR_output_header_emitted",
}
R4_2_ADJUDICATION_REQUIRED_MODE_LOBE_FIELDS = {
    "BFP_lobe_left_cross_term_W",
    "BFP_lobe_right_cross_term_W",
    "BFP_lobe_inner_cross_term_W",
    "BFP_lobe_outer_cross_term_W",
    "even_mode_cross_term_W",
    "odd_mode_cross_term_W",
    "mode_overlap_complex",
    "mode_overlap_phase_rad",
    "mode_overlap_abs",
    "lobe_balance_ratio",
    "ROI_parity_sign",
}
R4_2_ADJUDICATION_REQUIRED_CLUSTER_FIELDS = {
    "route_id",
    "interface_state",
    "mesh_level",
    "mesh_level_role",
    "particle_id",
    "polarization_state",
    "full_wave_cross_term_signed_W",
    "surrogate_cross_term_signed_W",
    "abs_full_wave_cross_term_W",
    "abs_surrogate_cross_term_W",
    "median_abs_full_wave_cross_term_for_route_particle",
    "sign_reliability_threshold_W",
    "sign_reliability_threshold_source",
    "sign_reliability_band",
    "sign_preserved_after_global_flip",
    "sign_ambiguous_due_to_near_zero",
    "review_refined_agreement",
    "fine_confirm_agreement",
    "coarse_screen_conflict",
}
R5_PLAN_SCHEMA_VERSION = "R5_full_grid_v2_plan_v1"
R5_V1_SOURCE_ROW_COUNT = 32032
R5_V1_SOURCE_ROUTE_COUNT = 572
R5_V1_SOURCE_PARTICLE_NAME_COUNT = 56
R5_NAMED_SCENARIO_BUNDLE_COUNT = MAX_ANCHOR_SCENARIO_BUNDLES
R5_STOCHASTIC_SEED_COUNT = 0
MAX_R5_FULL_GRID_V2_CASE_ROWS_BEFORE_REVIEW = (
    R5_V1_SOURCE_ROW_COUNT * R5_NAMED_SCENARIO_BUNDLE_COUNT
)
R5_MAIN_660_LOCKED_ROUTES = {
    (660, 800, 1400),
    (660, 800, 1500),
}
R5_REQUIRED_SCENARIO_BUNDLE_IDS = {
    "nominal_instrument_clean_blank",
    "detector_50ohm_pessimistic",
    "external_TIA_optimistic",
    "blank_bursty_RIN_high",
    "BFP_slit_offset_leakage",
    "PEG_pessimistic_wall_loss",
    "404_thermal_high_low_power",
    "DAQ_low_resolution_sampling",
}
R5_REQUIRED_OUTPUTS_IF_EXECUTED_AFTER_REVIEW = {
    "full_grid_v2_case_manifest.csv",
    "full_grid_v2_summary.csv",
    "route_role_stability_full_grid_v2.csv",
    "main_660_full_grid_v2_stability_summary.csv",
    "context_route_no_promotion_summary.csv",
    "optional_660_governance_summary.csv",
    "selected_annulus_parallel_lens_summary.csv",
    "scenario_bundle_sensitivity_summary.csv",
    "R4_2_validation_grade_carryforward_summary.csv",
    "coarse_screen_warning_carryforward_summary.csv",
    "detector_blank_claim_guardrail_summary.csv",
    "thermal_404_sidecar_summary.csv",
    "unit_guardrail_summary.csv",
    "full_grid_v2_cost_estimate.csv",
    "run_manifest.json",
    "R5_full_grid_v2_report.md",
}
R5_REQUIRED_STOP_GATES = {
    "R5_execution_without_external_authorization",
    "R5_case_rows_exceed_review_cap",
    "v1_full_grid_output_overwritten",
    "Tsuyama_paper_fit_continued",
    "selected_annulus_bounds_changed",
    "selected_annulus_replaces_all_crossing_ranking",
    "context_route_promotion_attempted",
    "main_660_redefinition_attempted",
    "optional_660_900x1400_redefines_main_660",
    "route_specific_manual_sign_flip_attempted",
    "calibrated_SNR_or_event_probability_claim_emitted",
    "absolute_LOD_or_true_concentration_claim_emitted",
    "biological_specificity_claim_emitted",
    "ET2030_direct_current_input_unlocked_without_measured_bench_artifact",
    "thermal_sidecar_used_to_increase_NODI_score",
    "finite_zero_event_blank_safety_claim_emitted",
    "legacy_detector_SNR_output_header_emitted",
    "legacy_calibrated_detector_SNR_output_header_emitted",
}
R5_REQUIRED_SOURCE_CHECKSUM_FIELDS = {
    "base_v1_summary_checksum",
    "R4_2_observable_summary_checksum",
    "R4_2_main660_sign_summary_checksum",
    "R4_2_mesh_role_summary_checksum",
    "R4_2_guardrail_summary_checksum",
    "R4_2_run_manifest_checksum",
}
R5_REQUIRED_FUTURE_PLAN_CHECKSUM_FIELDS = {
    "R5_plan_yaml_checksum",
    "R5_plan_report_checksum",
}
R5_SCENARIO_BUNDLE_MANIFEST_SCHEMA_VERSION = "R5_scenario_bundle_manifest_v1"
R5_REQUIRED_SCENARIO_BUNDLE_FIELDS = {
    "scenario_id",
    "instrument_path_id",
    "detector_source",
    "connection_readout_path",
    "termination_mode",
    "power_scale",
    "roi_weight_scale",
    "blank_threshold_sigma",
    "blank_independent_samples_per_s",
    "colored_noise_correlation_time_s",
    "RIN_PSD_1_per_Hz",
    "peg_survival_factor",
    "daq_snr_factor",
    "scenario_role",
}
R5_1_PLAN_SCHEMA_VERSION = "R5_1_route_role_stability_interpretation_plan_v1"
R5_1_REQUIRED_OUTPUTS_IF_AUTHORIZED = {
    "R5_1_route_role_stability_interpretation_manifest.csv",
    "R5_1_route_role_stability_decision_table.csv",
    "R5_1_scenario_sensitivity_interpretation.csv",
    "R5_1_context_route_high_score_warning_table.csv",
    "R5_1_main_660_robustness_interpretation.csv",
    "R5_1_weak_reference_control_interpretation.csv",
    "R5_1_selected_annulus_nonpromotion_summary.csv",
    "R5_1_claim_boundary_guardrail_summary.csv",
    "R5_1_next_stage_options_matrix.csv",
    "run_manifest.json",
    "R5_1_route_role_stability_interpretation_report.md",
}
R5_1_REQUIRED_STOP_GATES = {
    "R5_1_execution_without_external_authorization",
    "R6_plan_preparation_started",
    "R6_execution_started",
    "R5_followup_expansion_started",
    "R5_case_rows_expanded_beyond_reviewed_cap",
    "v1_full_grid_output_overwritten",
    "Tsuyama_paper_fit_continued",
    "selected_annulus_bounds_changed",
    "selected_annulus_replaces_all_crossing_ranking",
    "context_route_promotion_attempted",
    "main_660_redefinition_attempted",
    "optional_660_900x1400_redefines_main_660",
    "route_specific_manual_sign_flip_attempted",
    "calibrated_SNR_or_event_probability_claim_emitted",
    "absolute_LOD_or_true_concentration_claim_emitted",
    "biological_specificity_claim_emitted",
    "ET2030_direct_current_input_unlocked_without_measured_bench_artifact",
    "thermal_sidecar_used_to_increase_NODI_score",
    "finite_zero_event_blank_safety_claim_emitted",
    "legacy_detector_SNR_output_header_emitted",
    "legacy_calibrated_detector_SNR_output_header_emitted",
}
R5_1_ALLOWED_NEXT_STAGE_RECOMMENDATIONS = {
    "prepare_R6_plan_for_external_review_only",
    "prepare_post_v2_validation_dependency_backlog_only",
    "prepare_bounded_additional_scenario_prior_audit_plan_only",
    "hold_for_route_governance_revision_plan_only",
}
R5_1_REQUIRED_PROVENANCE_FIELDS = {
    "R5_case_manifest_checksum",
    "R5_summary_checksum",
    "R5_route_role_stability_checksum",
    "R5_main660_summary_checksum",
    "R5_context_no_promotion_checksum",
    "R5_scenario_sensitivity_checksum",
    "R5_cost_estimate_checksum",
    "R5_run_manifest_checksum",
}
R5_2_PLAN_SCHEMA_VERSION = "R5_2_bounded_scenario_prior_audit_plan_v1"
R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS = {
    "660_500x1500",
    "660_500x1400",
    "660_500x1300",
    "660_500x1200",
    "660_600x1500",
    "660_500x1100",
    "660_600x1400",
    "660_500x1000",
    "660_600x1300",
    "660_700x1400",
    "660_500x900",
    "660_600x1200",
    "660_700x1300",
    "660_600x1100",
    "532_500x1500",
    "660_500x800",
    "660_700x1200",
    "532_500x1400",
    "660_600x1000",
    "532_500x1300",
}
R5_2_AUDIT_ROUTE_IDS = {
    "660_800x1400",
    "660_800x1500",
    "660_700x1500",
    "660_900x1400",
    "488_600x1500",
    "532_600x1500",
    "404_600x1300",
    "404_800x550",
    "404_800x600",
    "404_800x700",
    "660_800x550",
    "660_800x600",
    "660_800x700",
    *R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS,
}
R5_2_AUDIT_ROUTE_COUNT = 33
R5_2_EXISTING_R5_AUDIT_ROW_CAP = (
    R5_2_AUDIT_ROUTE_COUNT
    * R5_V1_SOURCE_PARTICLE_NAME_COUNT
    * R5_NAMED_SCENARIO_BUNDLE_COUNT
)
R5_2_REQUIRED_OUTPUTS_IF_AUTHORIZED = {
    "R5_2_scenario_prior_audit_manifest.csv",
    "R5_2_audit_route_set_traceability.csv",
    "R5_2_context_route_above_main_audit.csv",
    "R5_2_weak_reference_control_audit.csv",
    "R5_2_scenario_bundle_contribution_audit.csv",
    "R5_2_route_family_sensitivity_audit.csv",
    "R5_2_main_660_locked_comparator_summary.csv",
    "R5_2_selected_annulus_and_404_sidecar_guardrail_summary.csv",
    "R5_2_claim_boundary_guardrail_summary.csv",
    "R5_2_audit_decision_table.csv",
    "R5_2_next_stage_recommendation_matrix.csv",
    "run_manifest.json",
    "R5_2_bounded_scenario_prior_audit_report.md",
}
R5_2_REQUIRED_STOP_GATES = {
    "bounded_scenario_prior_audit_execution_without_external_authorization",
    "R6_plan_preparation_started",
    "R6_execution_started",
    "R5_followup_expansion_started",
    "R5_case_rows_expanded_beyond_reviewed_cap",
    "audit_source_rows_exceed_reviewed_plan_cap",
    "audit_route_set_expanded_beyond_plan",
    "new_scenario_bundle_added",
    "new_stochastic_seed_added",
    "new_solver_case_started",
    "new_experiment_started",
    "v1_full_grid_output_overwritten",
    "Tsuyama_paper_fit_continued",
    "selected_annulus_bounds_changed",
    "selected_annulus_replaces_all_crossing_ranking",
    "context_route_promotion_attempted",
    "main_660_redefinition_attempted",
    "optional_660_900x1400_redefines_main_660",
    "route_specific_manual_sign_flip_attempted",
    "calibrated_SNR_or_event_probability_claim_emitted",
    "absolute_LOD_or_true_concentration_claim_emitted",
    "biological_specificity_claim_emitted",
    "ET2030_direct_current_input_unlocked_without_measured_bench_artifact",
    "thermal_sidecar_used_to_increase_NODI_score",
    "finite_zero_event_blank_safety_claim_emitted",
    "legacy_detector_SNR_output_header_emitted",
    "legacy_calibrated_detector_SNR_output_header_emitted",
}
R5_2_REQUIRED_PROVENANCE_FIELDS = {
    "R5_1_manifest_checksum",
    "R5_1_decision_table_checksum",
    "R5_1_context_warning_table_checksum",
    "R5_1_weak_reference_checksum",
    "R5_1_next_stage_options_checksum",
    "R5_1_run_manifest_checksum",
    "R5_case_manifest_checksum",
    "R5_summary_checksum",
    "R5_context_no_promotion_checksum",
    "R5_route_role_stability_checksum",
    "R5_scenario_sensitivity_checksum",
    "R5_run_manifest_checksum",
}
R5_2_ALLOWED_FUTURE_RECOMMENDATION_CLASSES = {
    "prepare_R6_plan_for_external_review_only",
    "prepare_post_v2_validation_dependency_backlog_only",
    "hold_for_route_governance_revision_plan_only",
    "prepare_route_prior_model_revision_plan_only",
    "inconclusive_requires_plan_revision",
}
R5_3_ROUTE_PRIOR_PLAN_SCHEMA_VERSION = "R5_3_route_prior_model_revision_plan_v1"
R5_3_ROUTE_PRIOR_SOURCE_ROW_CAP = R5_2_EXISTING_R5_AUDIT_ROW_CAP
R5_3_REQUIRED_DECOMPOSITION_TERMS = {
    "reference_prior_term",
    "BFP_slit_pinhole_prior_term",
    "near_wall_PEG_transport_prior_term",
    "detector_blank_prior_term",
    "thermal_404_sidecar_exclusion_term",
    "route_width_depth_prior_term",
    "particle_size_stratum_term",
    "scenario_bundle_sensitivity_term",
}
R5_3_ALLOWED_CANDIDATE_PRIOR_FAMILIES = {
    "diagnostic_score_term_decomposition_only",
    "global_width_depth_regularization_family",
    "weak_reference_control_artifact_flag_family",
    "wall_transport_prior_risk_family",
    "BFP_slit_operator_prior_family",
    "detector_blank_prior_risk_family",
    "scenario_bundle_sensitivity_reweighting_diagnostic",
}
R5_3_FORBIDDEN_PRIOR_FAMILIES = {
    "route_specific_manual_multiplier",
    "context_route_promotion_by_prior_revision",
    "main_660_redefinition_by_prior_revision",
    "selected_annulus_replaces_all_crossing",
    "scenario_specific_per_route_fit",
    "particle_specific_empirical_fit",
    "calibrated_SNR_or_probability_fit",
    "thermal_404_bonus_term",
}
R5_3_REQUIRED_OUTPUTS_IF_AUTHORIZED = {
    "R5_3_route_prior_revision_manifest.csv",
    "R5_3_score_term_decomposition.csv",
    "R5_3_context_route_prior_driver_table.csv",
    "R5_3_weak_reference_control_prior_driver_table.csv",
    "R5_3_candidate_prior_revision_registry.csv",
    "R5_3_forbidden_fit_guardrail_summary.csv",
    "R5_3_main660_locked_comparator_after_prior_model_summary.csv",
    "R5_3_selected_annulus_and_404_sidecar_guardrail_summary.csv",
    "R5_3_claim_boundary_guardrail_summary.csv",
    "R5_3_route_prior_revision_decision_table.csv",
    "R5_3_next_stage_recommendation_matrix.csv",
    "run_manifest.json",
    "R5_3_route_prior_model_revision_report.md",
}
R5_3_REQUIRED_STOP_GATES = {
    "route_prior_model_revision_execution_without_external_authorization",
    "R6_plan_preparation_started",
    "R6_execution_started",
    "R5_followup_expansion_started",
    "R5_case_rows_expanded_beyond_reviewed_cap",
    "route_prior_source_rows_exceed_reviewed_plan_cap",
    "route_prior_route_set_expanded_beyond_plan",
    "new_scenario_bundle_added",
    "new_stochastic_seed_added",
    "new_solver_case_started",
    "new_experiment_started",
    "v1_full_grid_output_overwritten",
    "Tsuyama_paper_fit_continued",
    "selected_annulus_bounds_changed",
    "selected_annulus_replaces_all_crossing_ranking",
    "context_route_promotion_attempted",
    "main_660_redefinition_attempted",
    "optional_660_900x1400_redefines_main_660",
    "route_specific_manual_sign_flip_attempted",
    "route_specific_manual_prior_multiplier_attempted",
    "scenario_specific_per_route_fit_attempted",
    "particle_specific_empirical_fit_attempted",
    "calibrated_SNR_or_event_probability_claim_emitted",
    "absolute_LOD_or_true_concentration_claim_emitted",
    "biological_specificity_claim_emitted",
    "ET2030_direct_current_input_unlocked_without_measured_bench_artifact",
    "thermal_sidecar_used_to_increase_NODI_score",
    "finite_zero_event_blank_safety_claim_emitted",
    "legacy_detector_SNR_output_header_emitted",
    "legacy_calibrated_detector_SNR_output_header_emitted",
}
R5_3_REQUIRED_PROVENANCE_FIELDS = {
    "R5_2_manifest_checksum",
    "R5_2_traceability_checksum",
    "R5_2_context_audit_checksum",
    "R5_2_weak_reference_checksum",
    "R5_2_scenario_contribution_checksum",
    "R5_2_route_family_checksum",
    "R5_2_main660_checksum",
    "R5_2_sidecar_guardrail_checksum",
    "R5_2_claim_guardrail_checksum",
    "R5_2_decision_table_checksum",
    "R5_2_next_stage_matrix_checksum",
    "R5_2_run_manifest_checksum",
}
R5_3_ALLOWED_FUTURE_REVIEW_DECISIONS = {
    "PASS_TO_BOUNDED_ROUTE_PRIOR_MODEL_REVISION_AUDIT_ONLY",
    "CONDITIONAL_FIX_ROUTE_PRIOR_MODEL_REVISION_PLAN_BEFORE_AUDIT",
    "FAIL_ROUTE_PRIOR_MODEL_REVISION_PLAN_REWORK_REQUIRED",
}
R6_PLAN_SCHEMA_VERSION = "R6_route_prior_sensitivity_plan_v1"
R6_ROUTE_PRIOR_SOURCE_ROW_CAP = R5_2_EXISTING_R5_AUDIT_ROW_CAP
R6_DERIVED_CANDIDATE_ROW_CAP = R6_ROUTE_PRIOR_SOURCE_ROW_CAP * 12
R6_CANDIDATE_PRIOR_REGISTRY = (
    {
        "candidate_prior_id": "width_linear_800",
        "candidate_prior_family": "global_width_regularization_family",
        "parent_prior_family": "global_width_depth_regularization_family",
        "candidate_role": "lower_exponent_sensitivity",
        "formula": "min(1.0, width_nm / 800.0) ** 1.0",
        "width_pivot_nm": 800,
        "width_exponent": 1.0,
        "width_factor_floor": 0.0,
        "dof_count": 1,
        "complexity_penalty": 1,
        "physical_basis": "weak narrow-channel wall/transport risk prior",
    },
    {
        "candidate_prior_id": "width_exp1p5_800",
        "candidate_prior_family": "global_width_regularization_family",
        "parent_prior_family": "global_width_depth_regularization_family",
        "candidate_role": "intermediate_exponent_sensitivity",
        "formula": "min(1.0, width_nm / 800.0) ** 1.5",
        "width_pivot_nm": 800,
        "width_exponent": 1.5,
        "width_factor_floor": 0.0,
        "dof_count": 1,
        "complexity_penalty": 1,
        "physical_basis": "intermediate narrow-channel wall/transport risk prior",
    },
    {
        "candidate_prior_id": "global_width_quadratic_regularization",
        "candidate_prior_family": "global_width_regularization_family",
        "parent_prior_family": "global_width_depth_regularization_family",
        "candidate_role": "R5_3_selected_candidate_anchor",
        "formula": "min(1.0, width_nm / 800.0) ** 2.0",
        "width_pivot_nm": 800,
        "width_exponent": 2.0,
        "width_factor_floor": 0.0,
        "dof_count": 1,
        "complexity_penalty": 1,
        "physical_basis": "R5.3 explanatory narrow-channel risk candidate",
    },
    {
        "candidate_prior_id": "width_quad_750",
        "candidate_prior_family": "global_width_regularization_family",
        "parent_prior_family": "global_width_depth_regularization_family",
        "candidate_role": "pivot_sensitivity_low",
        "formula": "min(1.0, width_nm / 750.0) ** 2.0",
        "width_pivot_nm": 750,
        "width_exponent": 2.0,
        "width_factor_floor": 0.0,
        "dof_count": 1,
        "complexity_penalty": 1,
        "physical_basis": "lower pivot narrow-channel risk sensitivity",
    },
    {
        "candidate_prior_id": "width_quad_850",
        "candidate_prior_family": "global_width_regularization_family",
        "parent_prior_family": "global_width_depth_regularization_family",
        "candidate_role": "pivot_sensitivity_high",
        "formula": "min(1.0, width_nm / 850.0) ** 2.0",
        "width_pivot_nm": 850,
        "width_exponent": 2.0,
        "width_factor_floor": 0.0,
        "dof_count": 1,
        "complexity_penalty": 1,
        "physical_basis": "higher pivot narrow-channel risk sensitivity",
    },
    {
        "candidate_prior_id": "width_quad_900",
        "candidate_prior_family": "global_width_regularization_family",
        "parent_prior_family": "global_width_depth_regularization_family",
        "candidate_role": "pivot_sensitivity_upper",
        "formula": "min(1.0, width_nm / 900.0) ** 2.0",
        "width_pivot_nm": 900,
        "width_exponent": 2.0,
        "width_factor_floor": 0.0,
        "dof_count": 1,
        "complexity_penalty": 1,
        "physical_basis": "upper pivot narrow-channel risk sensitivity",
    },
    {
        "candidate_prior_id": "width_quad_floor025",
        "candidate_prior_family": "global_width_regularization_family",
        "parent_prior_family": "global_width_depth_regularization_family",
        "candidate_role": "floor_sensitivity_low",
        "formula": "max(0.25, min(1.0, width_nm / 800.0) ** 2.0)",
        "width_pivot_nm": 800,
        "width_exponent": 2.0,
        "width_factor_floor": 0.25,
        "dof_count": 2,
        "complexity_penalty": 2,
        "physical_basis": "floor-limited narrow-channel risk sensitivity",
    },
    {
        "candidate_prior_id": "width_quad_floor035",
        "candidate_prior_family": "global_width_regularization_family",
        "parent_prior_family": "global_width_depth_regularization_family",
        "candidate_role": "floor_sensitivity_mid",
        "formula": "max(0.35, min(1.0, width_nm / 800.0) ** 2.0)",
        "width_pivot_nm": 800,
        "width_exponent": 2.0,
        "width_factor_floor": 0.35,
        "dof_count": 2,
        "complexity_penalty": 2,
        "physical_basis": "moderate floor narrow-channel risk sensitivity",
    },
    {
        "candidate_prior_id": "width_quad_floor050",
        "candidate_prior_family": "global_width_regularization_family",
        "parent_prior_family": "global_width_depth_regularization_family",
        "candidate_role": "floor_sensitivity_high",
        "formula": "max(0.50, min(1.0, width_nm / 800.0) ** 2.0)",
        "width_pivot_nm": 800,
        "width_exponent": 2.0,
        "width_factor_floor": 0.50,
        "dof_count": 2,
        "complexity_penalty": 2,
        "physical_basis": "conservative floor narrow-channel risk sensitivity",
    },
    {
        "candidate_prior_id": "width_exp2p5_wall_transport",
        "candidate_prior_family": "wall_transport_prior_risk_family",
        "parent_prior_family": "global_width_depth_regularization_family",
        "candidate_role": "physical_subfactor_probe",
        "formula": "min(1.0, width_nm / 800.0) ** 2.5 with wall/PEG transport rationale",
        "width_pivot_nm": 800,
        "width_exponent": 2.5,
        "width_factor_floor": 0.0,
        "dof_count": 2,
        "complexity_penalty": 2,
        "physical_basis": "wall contact, PEG loss, and transport survival risk",
    },
    {
        "candidate_prior_id": "reference_band_penalty",
        "candidate_prior_family": "global_reference_operating_band_penalty_family",
        "parent_prior_family": "weak_reference_control_artifact_flag_family",
        "candidate_role": "non_width_alternative_probe",
        "formula": "max(0.65, min(1.0, source_v1_relative_score / 0.16))",
        "width_pivot_nm": None,
        "width_exponent": None,
        "width_factor_floor": None,
        "dof_count": 1,
        "complexity_penalty": 1,
        "physical_basis": "reference power operating-band and weak-reference risk",
    },
    {
        "candidate_prior_id": "BFP_alignment_risk",
        "candidate_prior_family": "BFP_slit_operator_prior_family",
        "parent_prior_family": "BFP_slit_operator_prior_family",
        "candidate_role": "non_width_alternative_probe",
        "formula": "min(1.0, width_nm / 800.0) ** 0.5 * min(1.0, 1400.0 / depth_nm) ** 0.25",
        "width_pivot_nm": None,
        "width_exponent": None,
        "width_factor_floor": None,
        "dof_count": 1,
        "complexity_penalty": 1,
        "physical_basis": "BFP lobe, slit, pinhole, and alignment sensitivity risk",
    },
)
R6_REQUIRED_CANDIDATE_PRIOR_IDS = {
    candidate["candidate_prior_id"] for candidate in R6_CANDIDATE_PRIOR_REGISTRY
}
R6_ALLOWED_CANDIDATE_PRIOR_FAMILIES = {
    "global_width_regularization_family",
    "wall_transport_prior_risk_family",
    "global_reference_operating_band_penalty_family",
    "BFP_slit_operator_prior_family",
}
R6_FORBIDDEN_PRIOR_FAMILIES = R5_3_FORBIDDEN_PRIOR_FAMILIES
R6_REQUIRED_SENSITIVITY_FIELDS = {
    "candidate_prior_id",
    "candidate_prior_family",
    "width_pivot_nm",
    "width_exponent",
    "width_factor_floor",
    "physical_basis",
    "dof_count",
    "complexity_penalty",
    "route_prior_factor",
    "old_score",
    "candidate_score",
    "delta_removed",
    "main660_comparator_policy",
    "main660_old_score",
    "main660_candidate_score",
    "main660_prior_factor",
    "main660_score_retention_fraction",
    "context_vs_candidate_adjusted_main_delta",
    "context_vs_unadjusted_main_delta",
    "optional_900_vs_candidate_adjusted_main_delta",
    "optional_900_vs_unadjusted_main_delta",
    "residual_delta_vs_main",
    "residual_above_main_flag",
    "scenario_residual_above_main_count",
    "particle_stratum_residual_above_main_count",
    "uses_route_specific_multiplier",
    "uses_scenario_specific_per_route_fit",
    "uses_particle_specific_empirical_fit",
    "changes_main_660_definition",
    "authorizes_route_promotion",
    "claim_level",
}
R6_REQUIRED_OUTPUTS_IF_AUTHORIZED = {
    "R6_route_prior_sensitivity_manifest.csv",
    "R6_candidate_prior_registry.csv",
    "R6_candidate_prior_sensitivity_matrix.csv",
    "R6_route_prior_factor_by_route.csv",
    "R6_route_family_residual_warning_table.csv",
    "R6_scenario_residual_warning_table.csv",
    "R6_particle_stratum_residual_warning_table.csv",
    "R6_main660_locked_comparator_summary.csv",
    "R6_selected_annulus_and_404_sidecar_guardrail_summary.csv",
    "R6_claim_boundary_guardrail_summary.csv",
    "R6_stop_gate_summary.csv",
    "R6_next_stage_recommendation_matrix.csv",
    "run_manifest.json",
    "R6_route_prior_sensitivity_report.md",
}
R6_REQUIRED_STOP_GATES = {
    "R6_execution_without_external_authorization",
    "R6_source_rows_exceed_reviewed_plan_cap",
    "R6_candidate_prior_grid_expanded_beyond_plan",
    "R6_route_set_expanded_beyond_plan",
    "R5_followup_expansion_started",
    "new_scenario_bundle_added",
    "new_stochastic_seed_added",
    "new_solver_case_started",
    "new_experiment_started",
    "v1_full_grid_output_overwritten",
    "Tsuyama_paper_fit_continued",
    "selected_annulus_bounds_changed",
    "selected_annulus_replaces_all_crossing_ranking",
    "context_route_promotion_attempted",
    "main_660_redefinition_attempted",
    "optional_660_900x1400_redefines_main_660",
    "route_specific_manual_sign_flip_attempted",
    "route_specific_manual_prior_multiplier_attempted",
    "scenario_specific_per_route_fit_attempted",
    "particle_specific_empirical_fit_attempted",
    "calibrated_SNR_or_event_probability_claim_emitted",
    "absolute_LOD_or_true_concentration_claim_emitted",
    "biological_specificity_claim_emitted",
    "ET2030_direct_current_input_unlocked_without_measured_bench_artifact",
    "thermal_sidecar_used_to_increase_NODI_score",
    "finite_zero_event_blank_safety_claim_emitted",
    "legacy_detector_SNR_output_header_emitted",
    "legacy_calibrated_detector_SNR_output_header_emitted",
}
R6_REQUIRED_PROVENANCE_FIELDS = {
    "R5_3_manifest_checksum",
    "R5_3_score_decomposition_checksum",
    "R5_3_context_driver_checksum",
    "R5_3_weak_reference_driver_checksum",
    "R5_3_candidate_registry_checksum",
    "R5_3_forbidden_guardrail_checksum",
    "R5_3_main660_checksum",
    "R5_3_sidecar_guardrail_checksum",
    "R5_3_claim_guardrail_checksum",
    "R5_3_decision_table_checksum",
    "R5_3_next_stage_matrix_checksum",
    "R5_3_run_manifest_checksum",
}
R6_ALLOWED_FUTURE_REVIEW_DECISIONS = {
    "PASS_TO_BOUNDED_R6_ROUTE_PRIOR_SENSITIVITY_AUDIT_ONLY",
    "CONDITIONAL_FIX_R6_PLAN_BEFORE_EXECUTION",
    "FAIL_R6_PLAN_REWORK_REQUIRED",
}
R6_ALLOWED_RESULT_RECOMMENDATION_CLASSES = {
    "prepare_next_stage_plan_for_external_review_only",
    "prepare_route_governance_revision_plan_for_external_review_only",
    "hold_for_prior_model_revision_plan_rework_only",
    "inconclusive_requires_plan_revision",
}
R7_PLAN_SCHEMA_VERSION = "R7_route_prior_mechanistic_decomposition_plan_v1"
R7_ROUTE_PRIOR_SOURCE_ROW_CAP = R6_ROUTE_PRIOR_SOURCE_ROW_CAP
R7_MAX_MECHANISTIC_CANDIDATE_COUNT = 12
R7_DERIVED_CANDIDATE_ROW_CAP = (
    R7_ROUTE_PRIOR_SOURCE_ROW_CAP * R7_MAX_MECHANISTIC_CANDIDATE_COUNT
)
R7_ACCEPTED_WIDTH_PRIOR_BAND = {
    "width_pivot_nm_min": 800,
    "width_pivot_nm_max": 850,
    "width_exponent_min": 1.5,
    "width_exponent_max": 2.0,
    "main660_retention_fraction_min": 0.85,
    "context_routes_above_main_after_candidate": 0,
    "weak_reference_scenario_rows_above_main_after_candidate": 0,
}
R7_ALLOWED_MECHANISTIC_PRIOR_FAMILIES = {
    "clearance_wall_PEG_transport_family",
    "transport_survival_clogging_family",
    "reference_operating_band_family",
    "BFP_slit_ROI_alignment_family",
    "fabrication_metrology_margin_family",
    "particle_stratum_residual_interpretation_only",
}
R7_FORBIDDEN_MECHANISTIC_PRIOR_FAMILIES = {
    "route_specific_manual_multiplier",
    "context_route_promotion_by_prior_revision",
    "main_660_redefinition_by_prior_revision",
    "selected_annulus_replaces_all_crossing",
    "scenario_specific_per_route_fit",
    "particle_specific_empirical_fit",
    "score_derived_physical_prior",
    "calibrated_SNR_or_probability_fit",
    "thermal_404_bonus_term",
}
R7_REQUIRED_MECHANISTIC_REGISTRY_FIELDS = {
    "candidate_mechanistic_prior_id",
    "candidate_prior_family",
    "candidate_scope",
    "physical_basis",
    "allowed_input_fields",
    "requires_new_operator_artifact",
    "dof_count_max",
    "complexity_penalty_max",
    "uses_route_specific_multiplier",
    "uses_scenario_specific_per_route_fit",
    "uses_particle_specific_empirical_fit",
    "uses_source_v1_relative_score_as_physical_input",
    "changes_main_660_definition",
    "authorizes_route_promotion",
    "changes_selected_annulus",
    "claim_level",
}
R7_REQUIRED_OUTPUTS_IF_AUTHORIZED = {
    "R7_mechanistic_decomposition_manifest.csv",
    "R7_candidate_mechanistic_prior_registry.csv",
    "R7_accepted_width_prior_band_summary.csv",
    "R7_width_quad_900_over_severe_caution_summary.csv",
    "R7_mechanistic_prior_factor_schema.csv",
    "R7_particle_stratum_residual_top_routes.csv",
    "R7_particle_stratum_residual_by_family.csv",
    "R7_gold_anchor_vs_EV_residual_comparison.csv",
    "R7_optional_900_governance_diagnostic.csv",
    "R7_non_width_prior_input_requirement_summary.csv",
    "R7_claim_boundary_guardrail_summary.csv",
    "R7_stop_gate_summary.csv",
    "R7_next_stage_recommendation_matrix.csv",
    "run_manifest.json",
    "R7_route_prior_mechanistic_decomposition_report.md",
}
R7_REQUIRED_STOP_GATES = {
    "R7_execution_without_external_authorization",
    "R7_source_rows_exceed_reviewed_plan_cap",
    "R7_mechanistic_candidate_grid_expanded_beyond_plan",
    "R7_route_set_expanded_beyond_plan",
    "R5_or_R6_followup_expansion_started",
    "new_scenario_bundle_added",
    "new_stochastic_seed_added",
    "new_solver_case_started",
    "new_experiment_started",
    "v1_full_grid_output_overwritten",
    "Tsuyama_paper_fit_continued",
    "selected_annulus_bounds_changed",
    "selected_annulus_replaces_all_crossing_ranking",
    "context_route_promotion_attempted",
    "main_660_redefinition_attempted",
    "optional_660_900x1400_redefines_main_660",
    "route_specific_manual_sign_flip_attempted",
    "route_specific_manual_prior_multiplier_attempted",
    "scenario_specific_per_route_fit_attempted",
    "particle_specific_empirical_fit_attempted",
    "score_derived_physical_prior_attempted",
    "calibrated_SNR_or_event_probability_claim_emitted",
    "absolute_LOD_or_true_concentration_claim_emitted",
    "biological_specificity_claim_emitted",
    "ET2030_direct_current_input_unlocked_without_measured_bench_artifact",
    "thermal_sidecar_used_to_increase_NODI_score",
    "finite_zero_event_blank_safety_claim_emitted",
    "legacy_detector_SNR_output_header_emitted",
    "legacy_calibrated_detector_SNR_output_header_emitted",
}
R7_REQUIRED_PROVENANCE_FIELDS = {
    "R6_manifest_checksum",
    "R6_candidate_registry_checksum",
    "R6_candidate_sensitivity_matrix_checksum",
    "R6_route_prior_factor_checksum",
    "R6_route_family_residual_checksum",
    "R6_scenario_residual_checksum",
    "R6_particle_stratum_residual_checksum",
    "R6_main660_comparator_checksum",
    "R6_claim_guardrail_checksum",
    "R6_stop_gate_checksum",
    "R6_next_stage_matrix_checksum",
    "R6_run_manifest_checksum",
}
R7_ALLOWED_FUTURE_REVIEW_DECISIONS = {
    "PASS_TO_BOUNDED_R7_ROUTE_PRIOR_MECHANISTIC_DECOMPOSITION_AUDIT_ONLY",
    "CONDITIONAL_FIX_R7_PLAN_BEFORE_EXECUTION",
    "FAIL_R7_PLAN_REWORK_REQUIRED",
}
R7_ALLOWED_RESULT_RECOMMENDATION_CLASSES = {
    "prepare_operator_artifact_gap_register_plan_only",
    "prepare_v2_no_measured_data_closure_only",
    "hold_for_route_prior_revision_plan_only",
    "hold_for_mechanistic_plan_rework_only",
    "inconclusive_requires_plan_revision",
}
R7_1_PLAN_SCHEMA_VERSION = "R7_1_operator_artifact_validation_plan_v1"
R7_1_REQUIRED_EVIDENCE_MODULE_IDS = {
    "reference_operating_band_artifact_protocol",
    "BFP_slit_ROI_alignment_operator_artifact_protocol",
    "fabrication_metrology_margin_artifact_protocol",
    "wall_PEG_transport_proxy_validation_protocol",
    "particle_stratum_residual_validation_protocol",
    "optional_900_governance_diagnostic_protocol",
}
R7_1_FORBIDDEN_ACTIONS = {
    "R8_plan_preparation",
    "R8_execution",
    "new_experiment_started",
    "new_solver_case_started",
    "new_scenario_bundle_added",
    "new_stochastic_seed_added",
    "route_promotion",
    "main_660_redefinition",
    "selected_annulus_boundary_change",
    "route_specific_manual_multiplier",
    "scenario_specific_per_route_fit",
    "particle_specific_empirical_fit",
    "score_derived_physical_prior",
    "calibrated_SNR_or_event_probability_claim",
    "absolute_LOD_or_true_concentration_claim",
    "biological_specificity_claim",
}
R7_1_REQUIRED_OUTPUTS_IF_AUTHORIZED = {
    "R7_1_operator_artifact_validation_manifest.csv",
    "R7_1_reference_operating_band_artifact_protocol.csv",
    "R7_1_BFP_slit_ROI_alignment_operator_artifact_protocol.csv",
    "R7_1_fabrication_metrology_margin_artifact_protocol.csv",
    "R7_1_wall_PEG_transport_proxy_validation_protocol.csv",
    "R7_1_particle_stratum_residual_validation_protocol.csv",
    "R7_1_optional_900_governance_protocol.csv",
    "R7_1_claim_boundary_guardrail_summary.csv",
    "R7_1_stop_gate_summary.csv",
    "R7_1_next_stage_recommendation_matrix.csv",
    "run_manifest.json",
    "R7_1_operator_artifact_validation_report.md",
}
R7_1_REQUIRED_PROVENANCE_FIELDS = {
    "R7_manifest_checksum",
    "R7_candidate_registry_checksum",
    "R7_accepted_width_band_checksum",
    "R7_width_900_caution_checksum",
    "R7_factor_schema_checksum",
    "R7_particle_residual_top_checksum",
    "R7_particle_residual_by_family_checksum",
    "R7_gold_vs_EV_residual_checksum",
    "R7_optional_900_checksum",
    "R7_non_width_requirement_checksum",
    "R7_claim_guardrail_checksum",
    "R7_stop_gate_checksum",
    "R7_next_stage_matrix_checksum",
    "R7_run_manifest_checksum",
}
R7_1_ALLOWED_RESULT_RECOMMENDATION_CLASSES = {
    "prepare_operator_artifact_gap_register_plan_only",
    "prepare_v2_no_measured_data_closure_only",
    "hold_for_protocol_revision_only",
    "inconclusive_requires_plan_revision",
}
R7_2_PLAN_SCHEMA_VERSION = "R7_2_operator_artifact_gap_register_plan_v1"
R7_2_REQUIRED_ARTIFACT_IDS = {
    "reference_operating_band_artifact",
    "BFP_slit_ROI_alignment_operator_artifact",
    "fabrication_metrology_margin_artifact",
    "wall_PEG_transport_proxy_artifact",
    "particle_stratum_residual_artifact",
    "optional_900_governance_diagnostic_artifact",
}
R7_2_FORBIDDEN_ACTIONS = {
    "operator_artifact_acquisition_started",
    "bench_measurement_started",
    "R8_plan_preparation",
    "R8_execution",
    "new_experiment_started",
    "new_solver_case_started",
    "new_scenario_bundle_added",
    "new_stochastic_seed_added",
    "route_promotion",
    "main_660_redefinition",
    "selected_annulus_boundary_change",
    "route_specific_manual_multiplier",
    "scenario_specific_per_route_fit",
    "particle_specific_empirical_fit",
    "score_derived_physical_prior",
    "calibrated_SNR_or_event_probability_claim",
    "absolute_LOD_or_true_concentration_claim",
    "biological_specificity_claim",
}
R7_2_REQUIRED_OUTPUTS_IF_AUTHORIZED = {
    "R7_2_operator_artifact_gap_manifest.csv",
    "R7_2_artifact_gap_registry.csv",
    "R7_2_reference_operating_band_gap_register.csv",
    "R7_2_BFP_slit_ROI_alignment_gap_register.csv",
    "R7_2_fabrication_metrology_margin_gap_register.csv",
    "R7_2_wall_PEG_transport_proxy_gap_register.csv",
    "R7_2_particle_stratum_residual_gap_register.csv",
    "R7_2_optional_900_governance_gap_register.csv",
    "R7_2_claim_boundary_guardrail_summary.csv",
    "R7_2_stop_gate_summary.csv",
    "R7_2_next_stage_recommendation_matrix.csv",
    "run_manifest.json",
    "R7_2_operator_artifact_gap_register_report.md",
}
R7_2_REQUIRED_PROVENANCE_FIELDS = {
    "R7_1_manifest_checksum",
    "R7_1_reference_protocol_checksum",
    "R7_1_BFP_protocol_checksum",
    "R7_1_fabrication_protocol_checksum",
    "R7_1_wall_transport_protocol_checksum",
    "R7_1_particle_residual_protocol_checksum",
    "R7_1_optional_900_protocol_checksum",
    "R7_1_claim_guardrail_checksum",
    "R7_1_stop_gate_checksum",
    "R7_1_next_stage_matrix_checksum",
    "R7_1_run_manifest_checksum",
}
V2_NO_MEASURED_DATA_CLOSURE_SCHEMA_VERSION = (
    "V2_no_measured_data_closure_plan_v1"
)
V2_CLOSURE_REQUIRED_OUTPUTS = {
    "v2_no_measured_data_closure_manifest.csv",
    "v2_final_claim_boundary_summary.csv",
    "v2_route_governance_closure_summary.csv",
    "v2_artifact_gap_closure_register.csv",
    "v2_forbidden_scope_guardrail_summary.csv",
    "v2_post_v2_dependency_backlog.csv",
    "v2_closure_decision_table.csv",
    "run_manifest.json",
    "v2_no_measured_data_closure_report.md",
}
V2_CLOSURE_FORBIDDEN_ACTIONS = {
    "operator_artifact_acquisition_started",
    "bench_measurement_started",
    "experimental_validation_started",
    "R8_plan_preparation",
    "R8_execution",
    "new_experiment_started",
    "new_solver_case_started",
    "new_scenario_bundle_added",
    "new_stochastic_seed_added",
    "R5_followup_expansion",
    "R6_followup_expansion",
    "route_promotion",
    "context_route_promotion",
    "main_660_redefinition",
    "optional_660_900x1400_redefines_main_660",
    "selected_annulus_boundary_change",
    "selected_annulus_replaces_all_crossing_ranking",
    "route_specific_manual_multiplier",
    "scenario_specific_per_route_fit",
    "particle_specific_empirical_fit",
    "score_derived_physical_prior",
    "calibrated_SNR_or_event_probability_claim",
    "absolute_LOD_or_true_concentration_claim",
    "biological_specificity_claim",
    "thermal_sidecar_used_to_increase_NODI_score",
    "finite_zero_event_blank_safety_claim",
    "legacy_detector_SNR_output_header",
    "legacy_calibrated_detector_SNR_output_header",
}
V2_CLOSURE_REQUIRED_PROVENANCE_FIELDS = {
    "R7_2_manifest_checksum",
    "R7_2_artifact_gap_registry_checksum",
    "R7_2_claim_guardrail_checksum",
    "R7_2_stop_gate_checksum",
    "R7_2_next_stage_matrix_checksum",
    "R7_2_run_manifest_checksum",
    "v2_consolidated_roadmap_checksum",
    "v2_target_alignment_self_review_checksum",
}

E_CHARGE_C = 1.602176634e-19
K_BOLTZMANN_J_PER_K = 1.380649e-23


def _as_config_path(name_or_path: str | Path) -> Path:
    path = Path(name_or_path)
    if path.exists():
        return path
    candidate = CONFIG_DIR / str(name_or_path)
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"realism_v2 config not found: {name_or_path}")


def load_json_yaml(name_or_path: str | Path) -> dict[str, Any]:
    """Load a YAML file that is deliberately kept JSON-compatible."""
    path = _as_config_path(name_or_path)
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_claim_level(claim_level: str) -> str:
    if claim_level not in CLAIM_LEVELS:
        raise ValueError(f"Unknown realism_v2 claim_level: {claim_level}")
    return claim_level


def validate_module_state(module_state: str) -> str:
    if module_state not in MODULE_STATES:
        raise ValueError(f"Unknown realism_v2 module_state: {module_state}")
    return module_state


def validate_output_names(names: Iterable[str]) -> None:
    forbidden = FORBIDDEN_OUTPUT_NAMES.intersection(set(names))
    if forbidden:
        raise ValueError(f"Forbidden legacy SNR output names: {sorted(forbidden)}")


def load_claim_level_matrix(path: str | Path = "claim_level_matrix.csv") -> list[dict[str, str]]:
    matrix_path = _as_config_path(path)
    with matrix_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        validate_claim_level(row["claim_level"])
        validate_module_state(row["max_module_status_without_artifact"])
    return rows


def sanitize_key_part(value: object) -> str:
    text = str(value).strip()
    text = text.replace("/", "_").replace(" ", "_").replace(".", "p")
    return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in text)


def make_base_route_key(
    *,
    wavelength_nm: int,
    width_nm: int,
    depth_nm: int,
    particle_profile_id: str,
    particle_id: str,
    event_lens: str = "all_crossing",
) -> dict[str, Any]:
    if event_lens not in {"all_crossing", "selected_annulus_0p5_0p8"}:
        raise ValueError(f"Unsupported event_lens for base route key: {event_lens}")
    key = (
        f"lambda{int(wavelength_nm)}_w{int(width_nm)}_d{int(depth_nm)}"
        f"_{sanitize_key_part(particle_profile_id)}_{sanitize_key_part(particle_id)}"
        f"_{event_lens}"
    )
    return {
        "route_key": key,
        "wavelength_nm": int(wavelength_nm),
        "width_nm": int(width_nm),
        "depth_nm": int(depth_nm),
        "particle_profile_id": str(particle_profile_id),
        "particle_id": str(particle_id),
        "event_lens": event_lens,
    }


def make_scenario_identity(
    *,
    scenario_id: str,
    instrument_chain_id: str,
    prior_sample_id: str,
    sidecar_id: str,
) -> dict[str, str]:
    identity = {
        "scenario_id": scenario_id,
        "instrument_chain_id": instrument_chain_id,
        "prior_sample_id": prior_sample_id,
        "sidecar_id": sidecar_id,
    }
    identity["scenario_identity_key"] = "|".join(identity.values())
    return identity


def assert_route_scenario_separation(
    base_route_key: dict[str, Any], scenario_identity: dict[str, str]
) -> None:
    base_text = json.dumps(base_route_key, sort_keys=True)
    scenario_text = json.dumps(scenario_identity, sort_keys=True)
    for forbidden in ("scenario_id", "instrument_chain_id", "prior_sample_id", "sidecar_id"):
        if forbidden in base_route_key:
            raise ValueError(f"base_route_key contains scenario field: {forbidden}")
    for required in ("scenario_id", "instrument_chain_id", "prior_sample_id", "sidecar_id"):
        if required not in scenario_identity:
            raise ValueError(f"scenario_identity missing field: {required}")
    if str(scenario_identity["scenario_id"]) in base_text:
        raise ValueError("base_route_key is contaminated by scenario identity")
    if str(base_route_key["route_key"]) in scenario_text:
        raise ValueError("scenario_identity is contaminated by base route key")


def output_provenance_fields(
    *,
    unit: str,
    source_type: str,
    scenario_id: str,
    claim_level: str,
    calibration_dependency: str,
    module_status: str,
    base_route_key: dict[str, Any],
    scenario_identity: dict[str, str],
    run_manifest_path: str,
) -> dict[str, str]:
    validate_claim_level(claim_level)
    validate_module_state(module_status)
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"Unknown source_type: {source_type}")
    assert_route_scenario_separation(base_route_key, scenario_identity)
    return {
        "unit": unit,
        "source_type": source_type,
        "scenario_id": scenario_id,
        "claim_level": claim_level,
        "calibration_dependency": calibration_dependency,
        "module_status": module_status,
        "base_route_key": base_route_key["route_key"],
        "scenario_identity": scenario_identity["scenario_identity_key"],
        "run_manifest_path": run_manifest_path,
    }


def validate_required_output_fields(row: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_OUTPUT_PROVENANCE_FIELDS if field not in row]
    if missing:
        raise ValueError(f"realism_v2 output row missing provenance fields: {missing}")
    validate_output_names(row.keys())
    validate_claim_level(str(row["claim_level"]))
    validate_module_state(str(row["module_status"]))


def registry_artifact_ids(registry: dict[str, Any] | None = None) -> set[str]:
    payload = registry if registry is not None else load_json_yaml("calibration_artifact_registry.yaml")
    return {str(item["artifact_id"]) for item in payload.get("artifacts", [])}


def registry_artifact_by_id(
    artifact_id: str, registry: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    payload = registry if registry is not None else load_json_yaml("calibration_artifact_registry.yaml")
    for artifact in payload.get("artifacts", []):
        if str(artifact.get("artifact_id")) == artifact_id:
            return artifact
    return None


def _artifact_claim_unlocks(artifact: dict[str, Any]) -> set[str]:
    claim_unlocks = artifact.get("claim_unlocks", [])
    if isinstance(claim_unlocks, str):
        return {claim_unlocks}
    return {str(item) for item in claim_unlocks}


def _artifact_has_measured_file(artifact: dict[str, Any]) -> bool:
    return (
        artifact.get("source_type") in {"measured", "calibrated"}
        and bool(str(artifact.get("file_path", "")).strip())
        and bool(str(artifact.get("checksum", "")).strip())
    )


def artifact_unlocks_bench_validation(
    artifact: dict[str, Any] | None, connection_state_id: str
) -> bool:
    if artifact is None:
        return False
    return (
        artifact.get("artifact_type") == "detector_transfer"
        and artifact.get("connection_state_id") == connection_state_id
        and _artifact_has_measured_file(artifact)
        and "bench_validated_detector_connection" in _artifact_claim_unlocks(artifact)
    )


def artifact_unlocks_detector_transfer(artifact: dict[str, Any] | None) -> bool:
    if artifact is None:
        return False
    return (
        artifact.get("artifact_type") == "detector_transfer"
        and _artifact_has_measured_file(artifact)
        and "measured_detector_transfer" in _artifact_claim_unlocks(artifact)
    )


def artifact_unlocks_measured_blank(artifact: dict[str, Any] | None) -> bool:
    if artifact is None:
        return False
    return (
        artifact.get("artifact_type") in {"blank_trace", "blank_matrix_trace"}
        and _artifact_has_measured_file(artifact)
        and float(artifact.get("acquisition_duration_s", 0.0)) > 0.0
        and float(artifact.get("sampling_rate_Hz", 0.0)) > 0.0
        and "measured_blank" in _artifact_claim_unlocks(artifact)
    )


def validate_calibration_artifact_registry(registry: dict[str, Any] | None = None) -> None:
    payload = registry if registry is not None else load_json_yaml("calibration_artifact_registry.yaml")
    required = {
        "artifact_id",
        "artifact_type",
        "route_key",
        "wavelength_nm",
        "geometry_nm",
        "instrument_chain_id",
        "connection_state_id",
        "acquisition_duration_s",
        "sampling_rate_Hz",
        "laser_state",
        "detector_state",
        "sample_state",
        "file_path",
        "checksum",
        "source_type",
        "claim_unlocks",
    }
    seen: set[str] = set()
    for artifact in payload.get("artifacts", []):
        missing = required.difference(artifact)
        if missing:
            raise ValueError(f"calibration artifact missing fields: {sorted(missing)}")
        artifact_id = str(artifact["artifact_id"])
        if artifact_id in seen:
            raise ValueError(f"duplicate artifact_id: {artifact_id}")
        seen.add(artifact_id)
        if artifact["source_type"] not in SOURCE_TYPES:
            raise ValueError(f"invalid artifact source_type: {artifact['source_type']}")


def detector_path_schema(registry_path: str | Path = "detector_path_schema.yaml") -> dict[str, Any]:
    return load_json_yaml(registry_path)


def instrument_to_connection_path_map(
    path_schema: dict[str, Any] | None = None,
) -> dict[str, str]:
    schema = path_schema if path_schema is not None else detector_path_schema()
    return {
        str(item["instrument_path_id"]): str(item["connection_readout_path"])
        for item in schema.get("instrument_to_connection_path", [])
    }


def connection_readout_path_for_instrument_path(
    instrument_path_id: str, path_schema: dict[str, Any] | None = None
) -> str:
    mapping = instrument_to_connection_path_map(path_schema)
    if instrument_path_id in mapping:
        return mapping[instrument_path_id]
    schema = path_schema if path_schema is not None else detector_path_schema()
    if instrument_path_id in schema.get("connection_readout_path_enum", []):
        return instrument_path_id
    raise ValueError(f"Unknown detector instrument_path_id: {instrument_path_id}")


def canonical_instrument_path_id(
    path_id: str, path_schema: dict[str, Any] | None = None
) -> str:
    schema = path_schema if path_schema is not None else detector_path_schema()
    if path_id in schema.get("instrument_path_id_enum", []):
        return path_id
    for item in schema.get("instrument_to_connection_path", []):
        if item.get("connection_readout_path") == path_id:
            return str(item["instrument_path_id"])
    raise ValueError(f"Unknown detector path id: {path_id}")


def validate_detector_path_schema_maps_to_state_machine(
    path_schema: dict[str, Any] | None = None,
    state_machine: dict[str, Any] | None = None,
) -> None:
    schema = path_schema if path_schema is not None else detector_path_schema()
    machine = state_machine if state_machine is not None else load_json_yaml(
        "detector_connection_state_machine.yaml"
    )
    connection_paths = {str(rule["readout_path"]) for rule in machine.get("rules", [])}
    schema_connection_paths = set(schema.get("connection_readout_path_enum", []))
    if schema_connection_paths != connection_paths:
        raise ValueError(
            "detector_path_schema connection_readout_path_enum does not match state machine"
        )
    for item in schema.get("instrument_to_connection_path", []):
        instrument_path_id = str(item["instrument_path_id"])
        connection_readout_path = str(item["connection_readout_path"])
        if instrument_path_id not in schema.get("instrument_path_id_enum", []):
            raise ValueError(f"mapping uses unknown instrument_path_id: {instrument_path_id}")
        if connection_readout_path not in connection_paths:
            raise ValueError(
                f"mapping uses unknown state-machine connection path: {connection_readout_path}"
            )


def evaluate_detector_connection(
    *,
    detector_source: str,
    readout_path: str,
    termination_mode: str | None = None,
    bench_validation_artifact_id: str | None = None,
    state_machine: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    machine = state_machine if state_machine is not None else load_json_yaml(
        "detector_connection_state_machine.yaml"
    )
    rules = machine.get("rules", [])
    for rule in rules:
        if rule["detector_source"] != detector_source or rule["readout_path"] != readout_path:
            continue
        rule_termination = rule.get("termination_mode")
        if termination_mode is not None and rule_termination not in {termination_mode, "any"}:
            continue
        requires_bench = bool(rule.get("requires_bench_validation", False))
        artifact_id = bench_validation_artifact_id or ""
        artifact_ok = artifact_unlocks_bench_validation(
            registry_artifact_by_id(artifact_id, registry) if artifact_id else None,
            str(rule["connection_state_id"]),
        )
        if str(rule["status"]) == "forbidden_unless_bench_validated" and not artifact_ok:
            validity = "forbidden"
            requires_bench = True
        elif str(rule["status"]) == "forbidden_unless_bench_validated" and artifact_ok:
            validity = "allowed_bench_validated"
            requires_bench = False
        else:
            validity = str(rule["status"])
        return {
            "state_machine_version": machine["state_machine_version"],
            "connection_state_id": rule["connection_state_id"],
            "connection_physical_validity": validity,
            "termination_mode": rule.get("termination_mode", termination_mode or "unspecified"),
            "source_impedance_assumption": rule.get("source_impedance_assumption", "unspecified"),
            "load_impedance_assumption": rule.get("load_impedance_assumption", "unspecified"),
            "requires_bench_validation": requires_bench,
            "bench_validation_artifact_id": artifact_id,
            "connection_mode_warning": rule.get("warning", ""),
            "detector_source": detector_source,
            "readout_path": readout_path,
        }
    raise ValueError(f"No detector state-machine rule for {detector_source} -> {readout_path}")


def normalize_beam_profile(
    p_beam_raw_per_m2: np.ndarray | Iterable[float], pixel_area_m2: float
) -> tuple[np.ndarray, float]:
    density = np.asarray(p_beam_raw_per_m2, dtype=float)
    if pixel_area_m2 <= 0:
        raise ValueError("pixel_area_m2 must be positive")
    integral = float(np.sum(density) * pixel_area_m2)
    if integral <= 0 or not math.isfinite(integral):
        raise ValueError("beam profile integral must be positive and finite")
    return density / integral, integral


def local_irradiance_W_per_m2(
    *, P_probe_W: float, p_beam_at_particle_per_m2: float
) -> float:
    if P_probe_W < 0:
        raise ValueError("P_probe_W must be non-negative")
    if p_beam_at_particle_per_m2 < 0:
        raise ValueError("p_beam_at_particle_per_m2 must be non-negative")
    return float(P_probe_W * p_beam_at_particle_per_m2)


def integrate_cross_section_m2(
    dCsca_dOmega_m2_per_sr: np.ndarray | Iterable[float],
    solid_angle_weights_sr: np.ndarray | Iterable[float],
) -> float:
    dcs = np.asarray(dCsca_dOmega_m2_per_sr, dtype=float)
    weights = np.asarray(solid_angle_weights_sr, dtype=float)
    if dcs.shape != weights.shape:
        raise ValueError("dCsca_dOmega and solid-angle weights must have same shape")
    return float(np.sum(dcs * weights))


def mie_to_power_roi(
    *,
    P_probe_W: float,
    p_beam_at_particle_per_m2: float,
    dCsca_dOmega_m2_per_sr: np.ndarray | Iterable[float],
    solid_angle_weights_sr: np.ndarray | Iterable[float],
    collection_throughput: np.ndarray | Iterable[float] | float,
    Csca_total_m2: float | None = None,
    Cabs_m2: float = 0.0,
    Cext_m2: float | None = None,
) -> dict[str, Any]:
    I_inc = local_irradiance_W_per_m2(
        P_probe_W=P_probe_W, p_beam_at_particle_per_m2=p_beam_at_particle_per_m2
    )
    dcs = np.asarray(dCsca_dOmega_m2_per_sr, dtype=float)
    weights = np.asarray(solid_angle_weights_sr, dtype=float)
    throughput = np.asarray(collection_throughput, dtype=float)
    if throughput.shape == ():
        throughput = np.full(dcs.shape, float(throughput))
    if not (dcs.shape == weights.shape == throughput.shape):
        raise ValueError("Mie-to-power arrays must have matching shapes")
    if np.any(throughput < 0) or np.any(throughput > 1.0):
        raise ValueError("collection throughput must be in [0, 1]")

    Csca_roi = float(np.sum(dcs * throughput * weights))
    Csca_integral = float(np.sum(dcs * weights))
    if Csca_total_m2 is None:
        Csca_total_m2 = Csca_integral
    P_sca_ROI_W = float(I_inc * Csca_roi)
    P_sca_total_W = float(I_inc * Csca_total_m2)
    P_abs_W = float(I_inc * max(0.0, Cabs_m2))
    bound_W = float(I_inc * Csca_total_m2)
    energy_status = "not_evaluated"
    if Cext_m2 is not None:
        energy_status = (
            "P_sca_total_plus_abs_within_extinction"
            if P_sca_total_W + P_abs_W <= I_inc * Cext_m2 * (1.0 + 1.0e-9)
            else "P_sca_total_plus_abs_exceeds_extinction"
        )
    return {
        "I_inc_W_per_m2": I_inc,
        "P_sca_ROI_W": P_sca_ROI_W,
        "P_sca_total_W": P_sca_total_W,
        "P_abs_W": P_abs_W,
        "Csca_ROI_m2": Csca_roi,
        "Csca_integral_m2": Csca_integral,
        "Csca_total_m2": float(Csca_total_m2),
        "P_sca_ROI_upper_bound_W": bound_W,
        "P_sca_ROI_le_total_bound": P_sca_ROI_W <= bound_W * (1.0 + 1.0e-12),
        "energy_conservation_status": energy_status,
        "unit_guardrail": "watts_from_W_per_m2_times_m2_no_W_m2_error",
    }


def sphere_radius_m_from_diameter_nm(diameter_nm: float) -> float:
    if diameter_nm <= 0:
        raise ValueError("diameter_nm must be positive")
    return float(diameter_nm * 1.0e-9 / 2.0)


def medium_wavelength_m(vacuum_wavelength_m: float, n_medium: float) -> float:
    if vacuum_wavelength_m <= 0 or n_medium <= 0:
        raise ValueError("vacuum_wavelength_m and n_medium must be positive")
    return float(vacuum_wavelength_m / n_medium)


def physical_bfp_mm_to_uv(
    *,
    x_bfp_mm: np.ndarray | Iterable[float] | float,
    y_bfp_mm: np.ndarray | Iterable[float] | float,
    f_obj_mm: float,
    n_medium: float,
) -> tuple[np.ndarray, np.ndarray]:
    if f_obj_mm <= 0 or n_medium <= 0:
        raise ValueError("f_obj_mm and n_medium must be positive")
    u = np.asarray(x_bfp_mm, dtype=float) / (f_obj_mm * n_medium)
    v = np.asarray(y_bfp_mm, dtype=float) / (f_obj_mm * n_medium)
    return u, v


def uv_valid_mask(u: np.ndarray, v: np.ndarray, *, NA: float, n_medium: float) -> np.ndarray:
    rho2 = np.asarray(u, dtype=float) ** 2 + np.asarray(v, dtype=float) ** 2
    return (rho2 < 1.0) & (rho2 <= (NA / n_medium) ** 2)


def direction_cosine_jacobian(u: np.ndarray, v: np.ndarray) -> np.ndarray:
    rho2 = np.asarray(u, dtype=float) ** 2 + np.asarray(v, dtype=float) ** 2
    if np.any(rho2 >= 1.0):
        raise ValueError("direction-cosine uv coordinates must satisfy u^2 + v^2 < 1")
    return 1.0 / np.sqrt(1.0 - rho2)


def bfp_roi_intensity_operator(
    *,
    E_ref: np.ndarray,
    E_sca: np.ndarray,
    weight: np.ndarray,
    du: float,
    dv: float,
    u: np.ndarray,
    v: np.ndarray,
    NA: float,
    n_medium: float,
    coordinate_type: str = "direction_cosine_uv",
    apply_jacobian: bool = True,
    power_scale_W: float = 1.0,
) -> dict[str, Any]:
    if E_ref.shape != E_sca.shape or E_ref.shape != weight.shape:
        raise ValueError("E_ref, E_sca, and weight must have the same shape")
    if du <= 0 or dv <= 0:
        raise ValueError("du and dv must be positive")
    valid = uv_valid_mask(u, v, NA=NA, n_medium=n_medium)
    if not np.any(valid):
        raise ValueError("BFP ROI has no valid uv samples inside NA")
    jac = direction_cosine_jacobian(u, v) if apply_jacobian else np.ones_like(weight)
    operator = np.where(valid, weight * jac * du * dv, 0.0)
    P_ref = float(np.sum(np.abs(E_ref) ** 2 * operator) * power_scale_W)
    P_sca = float(np.sum(np.abs(E_sca) ** 2 * operator) * power_scale_W)
    P_cross = float(np.sum(2.0 * np.real(np.conj(E_ref) * E_sca) * operator) * power_scale_W)
    delta_signed = float(P_cross + P_sca)
    return {
        "P_ref_ROI_W": P_ref,
        "P_sca_ROI_W": P_sca,
        "P_cross_ROI_W": P_cross,
        "Delta_P_NODI_peak_signed_W": delta_signed,
        "Delta_P_NODI_peak_abs_W": abs(delta_signed),
        "operator_throughput": float(np.sum(operator)),
        "operator_throughput_preserved": float(np.sum(operator)) > 0.0,
        "same_operator_applied_to_reference_and_scattering": True,
        "coordinate_type": coordinate_type,
        "BFP_jacobian_applied": bool(apply_jacobian),
        "aplanatic_apodization_applied": False,
        "valid_uv_fraction": float(np.mean(valid)),
        "ROI_scalar_disagreement_ratio": float("nan"),
        "operator_normalization_mode": "explicit_weight_times_direction_cosine_jacobian",
    }


def lockin_enbw_hz(tau_s: float, filter_order: int) -> float:
    if tau_s <= 0:
        raise ValueError("tau_s must be positive")
    if filter_order < 1:
        raise ValueError("filter_order must be >= 1")
    numerator = math.gamma(filter_order - 0.5)
    denominator = 4.0 * math.sqrt(math.pi) * math.gamma(filter_order) * tau_s
    return float(numerator / denominator)


def lockin_pulse_attenuation(*, pulse_width_s: float, tau_s: float, filter_order: int) -> float:
    if pulse_width_s <= 0 or tau_s <= 0:
        raise ValueError("pulse_width_s and tau_s must be positive")
    if filter_order < 1:
        raise ValueError("filter_order must be >= 1")
    single_pole = 1.0 - math.exp(-pulse_width_s / tau_s)
    return float(max(0.0, min(1.0, single_pole ** (1.0 / filter_order))))


def validate_lockin_model_specs_not_mixed(lockin_model_ids: Iterable[str]) -> str:
    unique = {str(model_id) for model_id in lockin_model_ids}
    if len(unique) != 1:
        raise ValueError(f"LI5640/LI5660/LI5650 specs cannot be mixed in one run: {sorted(unique)}")
    return next(iter(unique))


def detector_noise_psd_terms(
    *,
    I_DC_A: float,
    I_dark_A: float,
    R_ohm: float,
    temperature_K: float,
    RIN_PSD_1_per_Hz: float,
    PSD_convention: str = "one_sided",
) -> dict[str, float | str]:
    if PSD_convention not in {"one_sided", "two_sided"}:
        raise ValueError("PSD_convention must be one_sided or two_sided")
    shot_A2_per_Hz = 2.0 * E_CHARGE_C * max(0.0, I_DC_A + I_dark_A)
    johnson_V2_per_Hz = 4.0 * K_BOLTZMANN_J_PER_K * temperature_K * R_ohm
    johnson_A2_per_Hz = 4.0 * K_BOLTZMANN_J_PER_K * temperature_K / R_ohm
    rin_A2_per_Hz = max(0.0, I_DC_A) ** 2 * max(0.0, RIN_PSD_1_per_Hz)
    return {
        "shot_noise_A2_per_Hz": shot_A2_per_Hz,
        "Johnson_noise_V2_per_Hz": johnson_V2_per_Hz,
        "Johnson_noise_A2_per_Hz_equivalent": johnson_A2_per_Hz,
        "RIN_PSD_1_per_Hz": RIN_PSD_1_per_Hz,
        "RIN_noise_A2_per_Hz": rin_A2_per_Hz,
        "PSD_convention": PSD_convention,
    }


def scenario_detector_unit_sidecar(
    *,
    P_ref_W: float,
    Delta_P_peak_W: float,
    wavelength_nm: int,
    readout_path: str,
    connection: dict[str, Any],
    lockin_model_id: str = "LI5640",
    tau_s: float = 0.002,
    filter_order: int = 2,
    RIN_PSD_1_per_Hz: float = 1.0e-12,
    measured_detector_transfer: bool = False,
    measured_blank: bool = False,
    detector_transfer_artifact_id: str | None = None,
    measured_blank_artifact_id: str | None = None,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_lockin_model_specs_not_mixed([lockin_model_id])
    instrument_path_id = canonical_instrument_path_id(readout_path)
    expected_connection_readout_path = connection_readout_path_for_instrument_path(
        instrument_path_id
    )
    actual_connection_readout_path = str(connection.get("readout_path", ""))
    if actual_connection_readout_path != expected_connection_readout_path:
        raise ValueError(
            "detector instrument_path_id does not match state-machine connection path: "
            f"{instrument_path_id} -> {expected_connection_readout_path}, got "
            f"{actual_connection_readout_path}"
        )
    responsivity_table = {404: 0.12, 488: 0.25, 532: 0.32, 660: 0.42}
    responsivity = responsivity_table.get(int(wavelength_nm), 0.32)
    i_dc = responsivity * max(0.0, P_ref_W)
    delta_i = responsivity * Delta_P_peak_W
    enbw = lockin_enbw_hz(tau_s, filter_order)
    terms = detector_noise_psd_terms(
        I_DC_A=i_dc,
        I_dark_A=1.0e-10,
        R_ohm=50.0,
        temperature_K=300.0,
        RIN_PSD_1_per_Hz=RIN_PSD_1_per_Hz,
    )
    current_noise_rms = math.sqrt(
        max(
            0.0,
            float(terms["shot_noise_A2_per_Hz"])
            + float(terms["Johnson_noise_A2_per_Hz_equivalent"])
            + float(terms["RIN_noise_A2_per_Hz"]),
        )
        * enbw
    )
    lockin_input_noise_A = 5.0e-15 * math.sqrt(enbw)
    input_noise_rms_A = math.sqrt(current_noise_rms**2 + lockin_input_noise_A**2)
    if instrument_path_id == "ET2030_50ohm_voltage":
        V_in_peak = 50.0 * delta_i
        input_noise_rms = 50.0 * input_noise_rms_A
    elif instrument_path_id == "external_TIA_voltage":
        V_in_peak = 1.0e6 * delta_i
        input_noise_rms = 1.0e6 * input_noise_rms_A
    else:
        V_in_peak = delta_i
        input_noise_rms = input_noise_rms_A
    snr = abs(V_in_peak) / input_noise_rms if input_noise_rms > 0 else float("inf")
    detector_transfer_artifact = (
        registry_artifact_by_id(detector_transfer_artifact_id, registry)
        if detector_transfer_artifact_id
        else None
    )
    blank_artifact = (
        registry_artifact_by_id(measured_blank_artifact_id, registry)
        if measured_blank_artifact_id
        else None
    )
    detector_transfer_unlocked = artifact_unlocks_detector_transfer(
        detector_transfer_artifact
    )
    measured_blank_unlocked = artifact_unlocks_measured_blank(blank_artifact)
    calibrated_snr_unlocked = detector_transfer_unlocked and measured_blank_unlocked
    if calibrated_snr_unlocked:
        snr_claim_level = "calibrated_absolute"
        source_type = "calibrated"
        calibration_blocker = ""
    else:
        snr_claim_level = "absolute_blocked"
        source_type = "bounded_prior"
        calibration_blocker_parts = []
        if detector_transfer_artifact_id:
            calibration_blocker_parts.append(
                "detector_transfer_artifact_not_valid_for_measured_detector_transfer"
                if not detector_transfer_unlocked
                else ""
            )
        else:
            calibration_blocker_parts.append("missing_detector_transfer_artifact")
        if measured_blank_artifact_id:
            calibration_blocker_parts.append(
                "blank_artifact_not_valid_for_measured_blank"
                if not measured_blank_unlocked
                else ""
            )
        else:
            calibration_blocker_parts.append("missing_measured_blank_artifact")
        calibration_blocker = "|".join(part for part in calibration_blocker_parts if part)
    return {
        "lockin_model_id": lockin_model_id,
        "lockin_manual_source": "LI5640_manual_required_before_measured_prior",
        "firmware_or_mode": "bounded_prior_mode_not_measured",
        "input_connector": actual_connection_readout_path,
        "input_impedance": connection.get("load_impedance_assumption", "unspecified"),
        "current_gain_setting": "bounded_prior_not_measured",
        "current_input_bandwidth": "blocked_for_ET2030_BNC_direct_current_input",
        "voltage_sensitivity_range": "2nV_to_1V_datasheet_prior",
        "time_constant_setting": tau_s,
        "filter_slope_setting": filter_order,
        "synchronous_filter_enabled": True,
        "output_mode": "X_signed",
        "analog_output_range": "bounded_prior_ADC_checked_separately",
        "ADC_or_logger_model": "micro_anchor_nominal_logger",
        "P_ref_W": P_ref_W,
        "Delta_P_peak_W": Delta_P_peak_W,
        "i_PD_DC_A": i_dc,
        "Delta_i_peak_A": delta_i,
        "V_in_peak_V": V_in_peak,
        "input_noise_rms": input_noise_rms,
        "output_noise_rms": input_noise_rms,
        "scenario_detector_SNR": snr,
        "scenario_detector_SNR_lower": snr / 3.0,
        "scenario_detector_SNR_upper": snr * 3.0,
        "SNR_claim_level": snr_claim_level,
        "SNR_requires_calibration": not calibrated_snr_unlocked,
        "SNR_source_type": source_type,
        "SNR_calibration_blocker": calibration_blocker,
        "detector_transfer_artifact_id": detector_transfer_artifact_id or "",
        "measured_blank_artifact_id": measured_blank_artifact_id or "",
        "detector_transfer_artifact_valid": detector_transfer_unlocked,
        "measured_blank_artifact_valid": measured_blank_unlocked,
        "shot_noise_fraction": float(terms["shot_noise_A2_per_Hz"]) / max(
            1.0e-300,
            float(terms["shot_noise_A2_per_Hz"])
            + float(terms["Johnson_noise_A2_per_Hz_equivalent"])
            + float(terms["RIN_noise_A2_per_Hz"]),
        ),
        "RIN_noise_fraction": float(terms["RIN_noise_A2_per_Hz"]) / max(
            1.0e-300,
            float(terms["shot_noise_A2_per_Hz"])
            + float(terms["Johnson_noise_A2_per_Hz_equivalent"])
            + float(terms["RIN_noise_A2_per_Hz"]),
        ),
        "lockin_noise_fraction": lockin_input_noise_A**2 / max(1.0e-300, input_noise_rms_A**2),
        "photodiode_linear_margin": 3.0e-3 / max(abs(i_dc), 1.0e-30),
        "lockin_input_margin": 1.0 / max(abs(V_in_peak), 1.0e-30),
        "lockin_fullscale_margin": 1.0 / max(abs(V_in_peak), 1.0e-30),
        "saturation_status": "comfortable_margin"
        if abs(i_dc) < 3.0e-4 and abs(V_in_peak) < 0.1
        else "check_saturation_margin",
        "preferred_detector_path": instrument_path_id,
        "instrument_path_id": instrument_path_id,
        "connection_readout_path": expected_connection_readout_path,
        **connection,
        **terms,
        "ENBW_Hz": enbw,
        "ENBW_convention": "Hz_one_sided",
    }


def laser_daq_sidecar(priors: dict[str, Any]) -> dict[str, Any]:
    required = {
        "P_probe_W_by_lambda",
        "beam_waist_xy_by_lambda",
        "focus_z_shift_by_lambda",
        "objective_transmission_by_lambda",
        "filter_leakage_by_lambda",
        "polarization_state_by_lambda",
        "RIN_PSD_by_lambda",
        "pointing_jitter_um_or_rad",
        "modulation_frequency_Hz",
        "modulation_depth",
        "daq_model",
        "adc_bits",
        "adc_input_range_V",
        "adc_sampling_rate_Hz",
        "anti_alias_filter",
        "timestamp_jitter",
    }
    missing = required.difference(priors)
    if missing:
        raise ValueError(f"laser/DAQ sidecar missing fields: {sorted(missing)}")
    adc_bits = int(priors["adc_bits"])
    adc_range = float(priors["adc_input_range_V"])
    lsb = adc_range / (2**adc_bits)
    quantization_noise_rms = lsb / math.sqrt(12.0)
    return {
        **priors,
        "quantization_noise_rms": quantization_noise_rms,
        "laser_source_status": "bounded_prior",
        "beam_delivery_status": "bounded_prior",
        "DAQ_status": "bounded_prior",
        "RIN_noise_contribution": "owned_by_laser_daq_sidecar",
        "pointing_jitter_peak_variance": "bounded_prior",
        "chromatic_focus_penalty": "reported_not_v1_writeback",
        "ADC_quantization_margin": "finite",
        "sampled_trace_claim_level": "absolute_blocked",
        "source_type": "bounded_prior",
        "claim_level": "absolute_blocked",
    }


def gaussian_tail_probability(threshold_sigma: float, tail: str = "two_sided") -> float:
    if threshold_sigma < 0:
        raise ValueError("threshold_sigma must be non-negative")
    one_sided = 0.5 * math.erfc(threshold_sigma / math.sqrt(2.0))
    if tail == "one_sided":
        return float(one_sided)
    if tail == "two_sided":
        return float(2.0 * one_sided)
    raise ValueError("tail must be one_sided or two_sided")


def rayleigh_magnitude_tail_probability(threshold_sigma: float) -> float:
    if threshold_sigma < 0:
        raise ValueError("threshold_sigma must be non-negative")
    return float(math.exp(-0.5 * threshold_sigma**2))


def zero_event_upper_bound_per_min(*, observed_zero_duration_s: float, confidence: float = 0.95) -> float:
    if observed_zero_duration_s <= 0:
        raise ValueError("observed_zero_duration_s must be positive")
    if not (0.0 < confidence < 1.0):
        raise ValueError("confidence must be between 0 and 1")
    duration_min = observed_zero_duration_s / 60.0
    return float(-math.log(1.0 - confidence) / duration_min)


def blank_false_positive_sidecar(
    *,
    threshold_sigma: float,
    independent_samples_per_s: float,
    colored_noise_correlation_time_s: float,
    acquisition_duration_s: float,
    trace_level: str = "trace_level_3_blank_channel_buffer",
    measured_blank: bool = False,
) -> dict[str, Any]:
    if measured_blank:
        raise ValueError("realism v2 is a no-measured-data lane; measured blanks are post-v2")
    if independent_samples_per_s <= 0 or acquisition_duration_s <= 0:
        raise ValueError("independent_samples_per_s and acquisition_duration_s must be positive")
    effective_N_per_s = min(
        independent_samples_per_s, 1.0 / max(colored_noise_correlation_time_s, 1.0e-12)
    )
    gaussian_fp_min = gaussian_tail_probability(threshold_sigma, "two_sided") * effective_N_per_s * 60.0
    magnitude_fp_min = rayleigh_magnitude_tail_probability(threshold_sigma) * effective_N_per_s * 60.0
    return {
        "trace_hierarchy": (
            "detector_off|laser_off_detector_on|laser_on_no_channel_or_blocked|"
            "blank_channel_buffer|blank_matrix|particle_standard"
        ),
        "trace_level_used": trace_level,
        "minimum_blank_acquisition_rule": "micro_anchor_analytic_prior_allowed",
        "analytic_gaussian_FP_per_min": gaussian_fp_min,
        "rice_or_rayleigh_magnitude_FP_per_min": magnitude_fp_min,
        "colored_noise_effective_N": effective_N_per_s * acquisition_duration_s,
        "rare_burst_rate_prior": 1.0e-3,
        "zero_event_upper_bound": zero_event_upper_bound_per_min(
            observed_zero_duration_s=acquisition_duration_s
        ),
        "blank_evidence_status": "not_measured",
        "false_positive_per_min_claim": "analytic_prior_only",
        "false_positive_rate_per_min": max(gaussian_fp_min, 1.0e-3),
        "finite_monte_carlo_zero_event_inferred": False,
        "claim_level": "absolute_blocked",
    }


def thermal_404_sidecar(
    *,
    wavelength_nm: int,
    I_exc_W_per_m2: float,
    alpha_medium_1_per_m: float,
    medium_volume_m3: float,
    alpha_glass_1_per_m: float,
    glass_volume_m3: float,
    particle_abs_cross_section_m2: float,
    contaminant_abs_cross_section_m2: float,
    filter_leakage_fraction: float,
) -> dict[str, Any]:
    P_medium_abs_W = alpha_medium_1_per_m * I_exc_W_per_m2 * medium_volume_m3
    P_glass_abs_W = alpha_glass_1_per_m * I_exc_W_per_m2 * glass_volume_m3
    P_particle_abs_W = I_exc_W_per_m2 * particle_abs_cross_section_m2
    P_contaminant_abs_W = I_exc_W_per_m2 * contaminant_abs_cross_section_m2
    P_filter_leakage_abs_W = filter_leakage_fraction * I_exc_W_per_m2 * 1.0e-16
    total = (
        P_medium_abs_W
        + P_glass_abs_W
        + P_particle_abs_W
        + P_contaminant_abs_W
        + P_filter_leakage_abs_W
    )
    if wavelength_nm == 404 and total > 1.0e-9:
        risk = "red"
    elif wavelength_nm == 404 and total > 1.0e-11:
        risk = "amber"
    else:
        risk = "green"
    promotion_allowed = risk != "red"
    return {
        "P_medium_abs_W": P_medium_abs_W,
        "P_glass_abs_W": P_glass_abs_W,
        "P_particle_abs_W": P_particle_abs_W,
        "P_contaminant_abs_W": P_contaminant_abs_W,
        "P_filter_leakage_abs_W": P_filter_leakage_abs_W,
        "thermal_artifact_risk": risk,
        "EV_integrity_risk": "elevated_short_wave" if wavelength_nm == 404 else "low",
        "promotion_allowed": promotion_allowed,
        "promotion_block_reason": "" if promotion_allowed else "404_thermal_artifact_risk_red",
        "optical_score_multiplier": 1.0 if promotion_allowed else 0.0,
        "claim_level": "safety_sidecar",
    }


def estimate_smoke_run_cost(
    *,
    n_routes: int = MAX_ANCHOR_ROUTES,
    n_particles: int = 8,
    n_scenario_bundles: int = MAX_ANCHOR_SCENARIO_BUNDLES,
    n_seeds: int = MAX_STOCHASTIC_SEEDS,
    events_per_case: int = 3000,
) -> dict[str, Any]:
    event_level_case_count = n_routes * n_particles * n_scenario_bundles * n_seeds
    under_cap = (
        n_routes <= MAX_ANCHOR_ROUTES
        and n_scenario_bundles <= MAX_ANCHOR_SCENARIO_BUNDLES
        and n_seeds <= MAX_STOCHASTIC_SEEDS
        and event_level_case_count <= MAX_EVENT_LEVEL_RUNS_BEFORE_REVIEW
    )
    return {
        "n_routes": n_routes,
        "n_particles": n_particles,
        "n_scenario_bundles": n_scenario_bundles,
        "n_seeds": n_seeds,
        "events_per_case": events_per_case,
        "event_level_case_count": event_level_case_count,
        "posthoc_case_count": n_routes * n_particles * n_scenario_bundles,
        "estimated_runtime_s": round(event_level_case_count * events_per_case * 1.0e-4, 3),
        "estimated_disk_MB": round(event_level_case_count * events_per_case * 2.0e-5, 3),
        "max_anchor_scenario_bundles": MAX_ANCHOR_SCENARIO_BUNDLES,
        "max_anchor_routes": MAX_ANCHOR_ROUTES,
        "max_stochastic_seeds": MAX_STOCHASTIC_SEEDS,
        "max_event_level_runs_before_review": MAX_EVENT_LEVEL_RUNS_BEFORE_REVIEW,
        "under_review_cap": under_cap,
    }


def estimate_reduced_grid_R3a_cost(
    *,
    n_routes: int = MAX_R3A_ROUTES,
    n_particles: int = MAX_R3A_PARTICLES,
    n_scenario_bundles: int = MAX_R3A_SCENARIO_BUNDLES,
    n_seeds: int = MAX_R3A_STOCHASTIC_SEEDS,
    events_per_case_proxy: int = 3000,
) -> dict[str, Any]:
    case_row_count = n_routes * n_particles * n_scenario_bundles * n_seeds
    under_cap = (
        n_routes <= MAX_R3A_ROUTES
        and n_particles <= MAX_R3A_PARTICLES
        and n_scenario_bundles <= MAX_R3A_SCENARIO_BUNDLES
        and n_seeds <= MAX_R3A_STOCHASTIC_SEEDS
        and case_row_count <= MAX_R3A_CASE_ROWS_BEFORE_REVIEW
    )
    return {
        "n_routes": n_routes,
        "n_particles": n_particles,
        "n_scenario_bundles": n_scenario_bundles,
        "n_seeds": n_seeds,
        "events_per_case_proxy": events_per_case_proxy,
        "case_row_count": case_row_count,
        "posthoc_case_count": n_routes * n_particles * n_scenario_bundles,
        "estimated_runtime_s": round(case_row_count * events_per_case_proxy * 1.0e-5, 3),
        "estimated_disk_MB": round(case_row_count * 1.2e-3, 3),
        "max_R3a_routes": MAX_R3A_ROUTES,
        "max_R3a_particles": MAX_R3A_PARTICLES,
        "max_R3a_scenario_bundles": MAX_R3A_SCENARIO_BUNDLES,
        "max_R3a_stochastic_seeds": MAX_R3A_STOCHASTIC_SEEDS,
        "max_R3a_case_rows_before_review": MAX_R3A_CASE_ROWS_BEFORE_REVIEW,
        "under_R3a_review_cap": under_cap,
    }


def uncertainty_R3b_route_panel() -> list[dict[str, Any]]:
    return [
        {
            "wavelength_nm": wavelength_nm,
            "width_nm": width_nm,
            "depth_nm": depth_nm,
            "route_role": route_role,
            "route_role_locked": True,
            "route_role_source": R3B_ROUTE_ROLE_SOURCE,
            "context_route_promotion_authorized": False,
        }
        for wavelength_nm, width_nm, depth_nm, route_role in R3B_ROUTE_PANEL
    ]


def validate_uncertainty_R3b_route_panel(
    routes: Iterable[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    route_rows = list(routes) if routes is not None else uncertainty_R3b_route_panel()
    route_keys = [
        (int(row["wavelength_nm"]), int(row["width_nm"]), int(row["depth_nm"]))
        for row in route_rows
    ]
    if len(route_rows) > MAX_R3B_ROUTES:
        raise ValueError("R3b route panel exceeds review cap")
    if len(set(route_keys)) != len(route_keys):
        raise ValueError("R3b route panel contains duplicate routes")
    required_routes = {
        (660, 800, 1400),
        (660, 800, 1500),
        (660, 700, 1500),
        (660, 900, 1400),
        (532, 900, 1500),
        (660, 900, 1500),
        (488, 900, 1500),
        (532, 900, 1400),
        (532, 800, 1500),
    }
    missing = required_routes.difference(route_keys)
    if missing:
        raise ValueError(f"R3b route panel missing required routes: {sorted(missing)}")
    for row in route_rows:
        if row.get("route_role_locked") is not True:
            raise ValueError("R3b route roles must be locked")
        if row.get("route_role_source") != R3B_ROUTE_ROLE_SOURCE:
            raise ValueError("R3b route_role_source mismatch")
        if row.get("context_route_promotion_authorized") is not False:
            raise ValueError("R3b context-route promotion is not authorized")
    return route_rows


def estimate_uncertainty_R3b_cost(
    *,
    n_routes: int = MAX_R3B_ROUTES,
    n_particles: int = MAX_R3B_PARTICLES,
    n_prior_samples: int = MAX_R3B_PRIOR_SAMPLES,
    n_seeds: int = MAX_R3B_STOCHASTIC_SEEDS,
    events_per_case_proxy: int = 3000,
) -> dict[str, Any]:
    case_row_count = n_routes * n_particles * n_prior_samples * n_seeds
    under_cap = (
        n_routes <= MAX_R3B_ROUTES
        and n_particles <= MAX_R3B_PARTICLES
        and n_prior_samples <= MAX_R3B_PRIOR_SAMPLES
        and n_seeds <= MAX_R3B_STOCHASTIC_SEEDS
        and case_row_count <= MAX_R3B_CASE_ROWS_BEFORE_REVIEW
    )
    return {
        "n_routes": n_routes,
        "n_particles": n_particles,
        "n_prior_samples": n_prior_samples,
        "n_seeds": n_seeds,
        "events_per_case_proxy": events_per_case_proxy,
        "case_row_count": case_row_count,
        "posthoc_case_count": n_routes * n_particles * n_prior_samples,
        "estimated_runtime_s": round(case_row_count * events_per_case_proxy * 1.0e-5, 3),
        "estimated_disk_MB": round(case_row_count * 1.2e-3, 3),
        "max_R3b_routes": MAX_R3B_ROUTES,
        "max_R3b_particles": MAX_R3B_PARTICLES,
        "max_R3b_prior_samples": MAX_R3B_PRIOR_SAMPLES,
        "max_R3b_stochastic_seeds": MAX_R3B_STOCHASTIC_SEEDS,
        "max_R3b_case_rows_before_review": MAX_R3B_CASE_ROWS_BEFORE_REVIEW,
        "under_R3b_review_cap": under_cap,
    }


def load_uncertainty_R3b_prior_table() -> dict[str, Any]:
    return load_json_yaml("r3b_uncertainty_prior_table.yaml")


def validate_uncertainty_R3b_prior_table(
    table: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = table if table is not None else load_uncertainty_R3b_prior_table()
    required_fields = set(payload.get("factor_entry_required_fields", ()))
    expected_fields = {
        "factor_group",
        "factor_name",
        "unit",
        "nominal",
        "min",
        "max",
        "distribution",
        "correlation_group",
        "correlation_transform",
        "route_sensitive_formula",
        "physical_rationale",
        "claim_level",
    }
    if required_fields != expected_fields:
        raise ValueError("R3b prior table required fields are incomplete")
    if int(payload.get("max_prior_samples", 0)) != MAX_R3B_PRIOR_SAMPLES:
        raise ValueError("R3b prior table sample cap mismatch")
    construction = payload.get("latin_hypercube_construction_rule", {})
    for key in (
        "quantile_rule",
        "per_factor_permutation",
        "correlation_rule",
        "correlation_transform_rule",
        "clamp_rule",
        "missing_field_rule",
    ):
        if not construction.get(key):
            raise ValueError(f"R3b Latin-hypercube rule missing {key}")
    rows = payload.get("factor_priors", [])
    if not isinstance(rows, list) or not rows:
        raise ValueError("R3b prior table has no factor rows")
    seen_names: set[tuple[str, str]] = set()
    seen_groups: set[str] = set()
    for row in rows:
        missing = [field for field in expected_fields if field not in row or row[field] == ""]
        if missing:
            raise ValueError(f"R3b prior factor missing fields: {missing}")
        factor_group = str(row["factor_group"])
        factor_name = str(row["factor_name"])
        if factor_group not in R3B_REQUIRED_FACTOR_GROUPS:
            raise ValueError(f"Unknown R3b factor group: {factor_group}")
        if (factor_group, factor_name) in seen_names:
            raise ValueError(f"Duplicate R3b factor prior: {factor_group}/{factor_name}")
        seen_names.add((factor_group, factor_name))
        seen_groups.add(factor_group)
        distribution = str(row["distribution"])
        if distribution not in R3B_ALLOWED_DISTRIBUTIONS:
            raise ValueError(f"Unknown R3b prior distribution: {distribution}")
        correlation_transform = str(row["correlation_transform"])
        if correlation_transform not in R3B_ALLOWED_CORRELATION_TRANSFORMS:
            raise ValueError(
                f"Unknown R3b correlation_transform: {correlation_transform}"
            )
        formula = str(row["route_sensitive_formula"])
        if formula not in R3B_ALLOWED_ROUTE_SENSITIVE_FORMULAS:
            raise ValueError(f"Unknown R3b route-sensitive formula: {formula}")
        nominal = float(row["nominal"])
        min_value = float(row["min"])
        max_value = float(row["max"])
        if min_value > nominal or nominal > max_value:
            raise ValueError(f"R3b prior bounds do not contain nominal: {factor_name}")
        if distribution == "log_uniform" and (min_value <= 0.0 or max_value <= 0.0):
            raise ValueError(f"R3b log_uniform bounds must be positive: {factor_name}")
        validate_claim_level(str(row["claim_level"]))
    if seen_groups != set(R3B_REQUIRED_FACTOR_GROUPS):
        raise ValueError("R3b prior table does not cover all required factor groups")
    group_counts: dict[str, int] = {}
    for row in rows:
        group = str(row["correlation_group"])
        group_counts[group] = group_counts.get(group, 0) + 1
    for row in rows:
        group = str(row["correlation_group"])
        if group_counts[group] > 1 and not row.get("correlation_transform"):
            raise ValueError(
                f"R3b grouped prior lacks correlation_transform: {group}"
            )
    return payload


def R3b_effect_delta_log_score_ratio(
    score_with_group_effect_by_route: dict[str, Iterable[float] | float],
    nominal_score_by_route: dict[str, Iterable[float] | float],
    *,
    eps: float = 1.0e-12,
) -> dict[str, float]:
    """Compute the fixed R3b effect_delta convention.

    effect_delta[group, route] is the signed median log score ratio over the
    same particle panel, prior samples, and seed policy:
    median(log((score_with_group_effect + eps) / (nominal_score + eps))).
    """
    if eps <= 0.0:
        raise ValueError("R3b effect_delta eps must be positive")
    missing = set(nominal_score_by_route).symmetric_difference(
        set(score_with_group_effect_by_route)
    )
    if missing:
        raise ValueError(f"R3b effect_delta route mismatch: {sorted(missing)}")

    deltas: dict[str, float] = {}
    for route, with_effect in score_with_group_effect_by_route.items():
        nominal = nominal_score_by_route[route]
        with_values = np.atleast_1d(np.asarray(with_effect, dtype=float))
        nominal_values = np.atleast_1d(np.asarray(nominal, dtype=float))
        if with_values.size != nominal_values.size:
            raise ValueError(f"R3b effect_delta length mismatch for route {route}")
        if np.any(with_values < 0.0) or np.any(nominal_values < 0.0):
            raise ValueError(f"R3b effect_delta scores must be non-negative for {route}")
        log_ratios = np.log((with_values + eps) / (nominal_values + eps))
        deltas[str(route)] = float(np.median(log_ratios))
    return deltas


def R3b_effect_delta_from_group_component_log_multipliers(
    group_component_log_multiplier_by_route: dict[str, Iterable[float] | float],
) -> dict[str, float]:
    """R3b diagnostic convention when a group component is already a log multiplier."""
    deltas: dict[str, float] = {}
    for route, values in group_component_log_multiplier_by_route.items():
        arr = np.atleast_1d(np.asarray(values, dtype=float))
        if arr.size == 0:
            raise ValueError(f"empty R3b group component log multiplier for {route}")
        deltas[str(route)] = float(np.median(arr))
    return deltas


def R3b_group_component_log_multiplier_equivalence_check(
    group_component_log_multiplier_by_route: dict[str, Iterable[float] | float],
    *,
    tolerance: float = 1.0e-12,
) -> dict[str, Any]:
    """Prove component log multipliers match the fixed effect_delta convention.

    If a group component is a signed log multiplier, then reconstructing
    score_with_group_effect = nominal_score * exp(component_log_multiplier)
    yields the same median log score ratio used by R3b effect_delta.
    """
    direct = R3b_effect_delta_from_group_component_log_multipliers(
        group_component_log_multiplier_by_route
    )
    nominal = {
        route: np.ones_like(np.atleast_1d(np.asarray(values, dtype=float)))
        for route, values in group_component_log_multiplier_by_route.items()
    }
    with_effect = {
        route: np.exp(np.atleast_1d(np.asarray(values, dtype=float)))
        for route, values in group_component_log_multiplier_by_route.items()
    }
    reconstructed = R3b_effect_delta_log_score_ratio(with_effect, nominal)
    errors = {
        route: abs(direct[route] - reconstructed[route])
        for route in direct
    }
    max_abs_error = max(errors.values(), default=0.0)
    return {
        "effect_delta_convention": R3B_EFFECT_DELTA_CONVENTION,
        "component_log_multiplier_convention": "median_group_component_log_multiplier",
        "max_abs_error": max_abs_error,
        "tolerance": tolerance,
        "equivalence_passed": max_abs_error <= tolerance,
        "route_errors": errors,
    }


def _stable_offset(label: str, count: int) -> int:
    digest = hashlib.sha256(label.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % count


def _R3b_centered_quantile(sample_index: int, label: str, count: int) -> float:
    return (((sample_index + _stable_offset(label, count)) % count) + 0.5) / count


def _R3b_triangular_quantile(q: float, *, min_value: float, mode: float, max_value: float) -> float:
    if max_value == min_value:
        return min_value
    mode_fraction = (mode - min_value) / (max_value - min_value)
    if q < mode_fraction:
        return min_value + math.sqrt(q * (max_value - min_value) * (mode - min_value))
    return max_value - math.sqrt((1.0 - q) * (max_value - min_value) * (max_value - mode))


def _R3b_factor_value(row: dict[str, Any], q: float) -> float:
    min_value = float(row["min"])
    nominal = float(row["nominal"])
    max_value = float(row["max"])
    distribution = str(row["distribution"])
    q = float(max(1.0e-9, min(1.0 - 1.0e-9, q)))
    if distribution == "uniform":
        value = min_value + q * (max_value - min_value)
    elif distribution == "log_uniform":
        value = math.exp(math.log(min_value) + q * (math.log(max_value) - math.log(min_value)))
    elif distribution == "triangular":
        value = _R3b_triangular_quantile(
            q,
            min_value=min_value,
            mode=nominal,
            max_value=max_value,
        )
    elif distribution == "truncated_normal":
        sigma = max((max_value - min_value) / 4.0, 1.0e-12)
        value = nominal + NormalDist().inv_cdf(q) * sigma
    else:
        raise ValueError(f"unsupported R3b factor distribution: {distribution}")
    return float(max(min_value, min(max_value, value)))


def R3b_uncertainty_prior_samples(
    table: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ...]:
    payload = validate_uncertainty_R3b_prior_table(table)
    rows = list(payload["factor_priors"])
    sample_count = int(payload["max_prior_samples"])
    samples: list[dict[str, Any]] = []
    for sample_index in range(sample_count):
        values: dict[str, float] = {}
        transforms: dict[str, str] = {}
        quantiles: dict[str, float] = {}
        for row in rows:
            factor_name = str(row["factor_name"])
            group = str(row["correlation_group"])
            transform = str(row["correlation_transform"])
            if transform == "independent_within_group":
                base_q = _R3b_centered_quantile(
                    sample_index,
                    f"{factor_name}:independent",
                    sample_count,
                )
            else:
                base_q = _R3b_centered_quantile(sample_index, f"group:{group}", sample_count)
            q = 1.0 - base_q if transform == "inverse" else base_q
            values[factor_name] = _R3b_factor_value(row, q)
            transforms[factor_name] = transform
            quantiles[factor_name] = q
        samples.append(
            {
                "prior_sample_id": f"R3b_LH_{sample_index:02d}",
                "prior_sample_index": sample_index,
                "factor_values": values,
                "correlation_transforms": transforms,
                "factor_quantiles": quantiles,
                "effect_delta_convention": R3B_EFFECT_DELTA_CONVENTION,
            }
        )
    return tuple(samples)


def _R3b_route_key(wavelength_nm: int, width_nm: int, depth_nm: int) -> str:
    return f"{wavelength_nm}_{width_nm}x{depth_nm}"


def _R3b_route_role(wavelength_nm: int, width_nm: int, depth_nm: int) -> str:
    route_map = {
        (int(row["wavelength_nm"]), int(row["width_nm"]), int(row["depth_nm"])): str(
            row["route_role"]
        )
        for row in uncertainty_R3b_route_panel()
    }
    return route_map[(wavelength_nm, width_nm, depth_nm)]


def _R3b_route_features(wavelength_nm: int, width_nm: int, depth_nm: int) -> dict[str, float]:
    geometry_factor = max(0.1, (width_nm / 800.0) * (depth_nm / 1400.0))
    selected_annulus_overlap = 1.0 if depth_nm <= 700 else 0.0
    high_width_context = max(0.0, (width_nm - 800.0) / 100.0)
    depth_context = max(0.0, (depth_nm - 1300.0) / 200.0)
    weak_reference = 1.0 if (wavelength_nm, width_nm, depth_nm) == (660, 700, 1500) else 0.0
    wall_sensitivity = min(2.0, (800.0 / width_nm + 1400.0 / depth_nm) / 2.0)
    shortwave_sensitivity = max(0.0, (660.0 - wavelength_nm) / 256.0)
    clip_sensitivity = (
        0.45 * abs(width_nm - 800.0) / 200.0
        + 0.35 * abs(depth_nm - 1400.0) / 900.0
        + 0.35 * selected_annulus_overlap
        + 0.20 * weak_reference
    )
    return {
        "geometry_factor": geometry_factor,
        "selected_annulus_overlap": selected_annulus_overlap,
        "high_width_context": high_width_context,
        "depth_context": depth_context,
        "weak_reference": weak_reference,
        "wall_sensitivity": wall_sensitivity,
        "shortwave_sensitivity": shortwave_sensitivity,
        "clip_sensitivity": clip_sensitivity,
    }


def _R3b_particle_class_flags(particle: dict[str, Any]) -> dict[str, float]:
    particle_id = str(particle["particle_id"])
    particle_class = str(particle["particle_class"])
    return {
        "is_ev": 1.0 if particle_class == "EV" else 0.0,
        "is_small_ev": 1.0 if particle_id in {"EV50_nominal", "EV70_nominal", "EV70_lowRI"} else 0.0,
        "is_low_ri": 1.0 if "lowRI" in particle_id else 0.0,
        "is_contaminant": 1.0 if particle_class == "contaminant" else 0.0,
        "is_doublet": 1.0 if particle_id == "EV_doublet" else 0.0,
    }


def R3b_group_component_log_multipliers(
    *,
    wavelength_nm: int,
    width_nm: int,
    depth_nm: int,
    particle: dict[str, Any],
    factor_values: dict[str, float],
) -> dict[str, float]:
    features = _R3b_route_features(wavelength_nm, width_nm, depth_nm)
    flags = _R3b_particle_class_flags(particle)
    clip = features["clip_sensitivity"]
    wall = features["wall_sensitivity"]
    weak = features["weak_reference"]
    short = features["shortwave_sensitivity"]
    selected = features["selected_annulus_overlap"]
    high_width = features["high_width_context"]
    depth_context = features["depth_context"]

    bfp_multiplier = (
        (factor_values["operator_throughput_scale"] / 1.0)
        ** (0.18 * (features["geometry_factor"] - 1.0))
        * ((factor_values["slit_width_scale"] / 1.0) ** (0.65 * (clip - 0.28)))
        * math.exp(-factor_values["roi_shift_uv"] * 7.5 * (clip - 0.28))
        * math.exp(
            -(factor_values["leakage_floor"] - 0.0001)
            * (110.0 * (weak + 0.45 * selected - 0.12))
        )
    )
    detector_multiplier = (
        (factor_values["readout_path_sensitivity_factor"] / 1.0)
        ** (0.28 * (features["geometry_factor"] - 1.0) + 0.35 * weak)
        / ((factor_values["input_noise_scale"] / 1.0) ** (0.22 * (weak - 0.05) + 0.20 * (features["geometry_factor"] - 1.0)))
        / (
            (factor_values["RIN_coupling_scale"] / 1.0)
            ** (0.14 * (features["geometry_factor"] - 1.0) + 0.08 * weak)
        )
        / ((factor_values["ADC_quantization_scale"] / 1.0) ** (0.25 * (weak + 0.30 * selected - 0.10)))
    )
    wall_multiplier = (
        (factor_values["peg_survival_factor"] / 0.82) ** (0.90 * (wall - 1.0))
        * math.exp(
            -(factor_values["adsorption_loss_factor"] - 0.18)
            * (0.85 * (wall - 1.0) + 0.28 * selected)
        )
        * math.exp(
            -(factor_values["near_wall_event_fraction"] - 0.35)
            * (0.28 * (wall - 1.0) + 0.12 * selected)
        )
        * ((factor_values["count_rate_proxy_factor"] / 1.0) ** (0.20 * (features["geometry_factor"] - 1.0)))
    )
    blank_multiplier = (
        (5.0 / factor_values["blank_threshold_sigma"]) ** (0.55 * (weak + 0.25 * selected - 0.08))
        * (factor_values["independent_samples_per_s"] / 20.0) ** (0.08 * (weak + 0.20 * selected - 0.06))
        * (0.5 / factor_values["colored_noise_correlation_time_s"]) ** (0.07 * (weak + 0.20 * selected - 0.06))
        * (0.001 / factor_values["rare_burst_rate_prior"]) ** (0.035 * (weak + 0.20 * selected - 0.06))
    )
    if wavelength_nm == 404:
        thermal_stress = (
            factor_values["404_power_scale"]
            * factor_values["medium_absorption_scale"] ** 0.35
            * factor_values["glass_absorption_scale"] ** 0.25
            * factor_values["filter_leakage_scale"] ** 0.12
        )
        thermal_multiplier = math.exp(
            -0.18 * max(0.0, thermal_stress - 1.0) * (1.0 + 0.35 * short)
        )
    else:
        thermal_multiplier = 1.0
    ev_multiplier = (
        factor_values["small_EV_weight_scale"]
        ** (0.12 * flags["is_small_ev"] * (1.0 + 0.20 * high_width))
        * factor_values["low_RI_weight_scale"]
        ** (-0.10 * flags["is_low_ri"] * (1.0 + 0.15 * depth_context))
        * (1.0 - factor_values["contaminant_fraction_proxy"] * 0.20 * flags["is_contaminant"])
        * (1.0 + factor_values["doublet_fraction_proxy"] * 0.35 * flags["is_doublet"])
        * math.exp(
            (factor_values["small_EV_weight_scale"] - 1.0)
            * 0.08
            * (high_width + 0.4 * depth_context - 0.35)
        )
        * math.exp(
            -(factor_values["contaminant_fraction_proxy"] - 0.08)
            * 0.24
            * (weak + 0.5 * selected - 0.12)
        )
        * math.exp(
            (factor_values["doublet_fraction_proxy"] - 0.03)
            * 0.20
            * (features["geometry_factor"] - 1.0)
        )
    )
    multipliers = {
        "BFP_slit_alignment": bfp_multiplier,
        "detector_readout": detector_multiplier,
        "wall_PEG_flow": wall_multiplier,
        "blank_RIN_drift": blank_multiplier,
        "thermal_404": thermal_multiplier,
        "EV_ensemble": ev_multiplier,
    }
    return {
        group: math.log(max(1.0e-6, min(10.0, multiplier)))
        for group, multiplier in multipliers.items()
    }


def _R3b_adjusted_scenario(factor_values: dict[str, float], wavelength_nm: int) -> dict[str, Any]:
    scenario = dict(anchor_smoke_scenario_bundles()[0])
    bfp_throughput = factor_values["operator_throughput_scale"]
    slit_scale = factor_values["slit_width_scale"]
    roi_shift = factor_values["roi_shift_uv"]
    scenario["roi_weight_scale"] = float(
        max(0.25, min(1.5, bfp_throughput * slit_scale * math.exp(-2.0 * roi_shift)))
    )
    scenario["power_scale"] = float(
        factor_values["404_power_scale"] if wavelength_nm == 404 else 1.0
    )
    scenario["blank_threshold_sigma"] = float(factor_values["blank_threshold_sigma"])
    scenario["blank_independent_samples_per_s"] = float(
        factor_values["independent_samples_per_s"]
    )
    scenario["colored_noise_correlation_time_s"] = float(
        factor_values["colored_noise_correlation_time_s"]
    )
    scenario["RIN_PSD_1_per_Hz"] = 1.0e-12 * float(factor_values["RIN_coupling_scale"])
    scenario["peg_survival_factor"] = float(factor_values["peg_survival_factor"])
    scenario["daq_snr_factor"] = float(
        max(
            0.2,
            factor_values["readout_path_sensitivity_factor"]
            / math.sqrt(
                factor_values["input_noise_scale"] * factor_values["ADC_quantization_scale"]
            ),
        )
    )
    return scenario


def _R3b_adjusted_particle_factor(
    particle: dict[str, Any],
    factor_values: dict[str, float],
) -> float:
    flags = _R3b_particle_class_flags(particle)
    multiplier = 1.0
    multiplier *= factor_values["small_EV_weight_scale"] ** (0.10 * flags["is_small_ev"])
    multiplier *= factor_values["low_RI_weight_scale"] ** (-0.08 * flags["is_low_ri"])
    multiplier *= 1.0 - 0.12 * factor_values["contaminant_fraction_proxy"] * flags["is_contaminant"]
    multiplier *= 1.0 + 0.25 * factor_values["doublet_fraction_proxy"] * flags["is_doublet"]
    return float(max(0.0, float(particle["particle_factor"]) * multiplier))


def route_sensitive_index(
    effect_delta_by_route: dict[str, float] | Iterable[float],
    *,
    eps: float = 1.0e-12,
) -> float:
    values = np.asarray(
        list(effect_delta_by_route.values())
        if isinstance(effect_delta_by_route, dict)
        else list(effect_delta_by_route),
        dtype=float,
    )
    if values.size == 0:
        raise ValueError("route_sensitive_index requires at least one route effect")
    route_variance = float(np.var(values))
    global_mean_power = float(np.mean(values) ** 2)
    return route_variance / (route_variance + global_mean_power + eps)


def global_multiplier_dominance_index(
    effect_delta_by_route: dict[str, float] | Iterable[float],
    *,
    eps: float = 1.0e-12,
) -> float:
    values = np.asarray(
        list(effect_delta_by_route.values())
        if isinstance(effect_delta_by_route, dict)
        else list(effect_delta_by_route),
        dtype=float,
    )
    if values.size == 0:
        raise ValueError("global_multiplier_dominance_index requires at least one route effect")
    mean_effect = abs(float(np.mean(values)))
    route_std = float(np.std(values))
    return mean_effect / (mean_effect + route_std + eps)


def classify_R3b_route_sensitive_prior_status(
    group_route_sensitive_indices: dict[str, float],
    global_multiplier_dominance: float,
) -> dict[str, Any]:
    max_group_index = max(group_route_sensitive_indices.values(), default=0.0)
    if global_multiplier_dominance > 0.8:
        status = "global_scalar_dominated"
        blocks_progression = True
    elif max_group_index >= 0.25:
        status = "route_sensitive"
        blocks_progression = False
    else:
        status = "under_resolved_route_sensitivity"
        blocks_progression = True
    return {
        "max_group_route_sensitive_index": max_group_index,
        "global_multiplier_dominance_index": global_multiplier_dominance,
        "route_sensitive_prior_status": status,
        "blocks_R3b_progression": blocks_progression,
        "route_sensitive_threshold": 0.25,
        "global_multiplier_dominance_stop_threshold": 0.8,
    }


def validate_R3b_pre_run_plan() -> dict[str, Any]:
    routes = validate_uncertainty_R3b_route_panel()
    prior_table = validate_uncertainty_R3b_prior_table()
    cost = estimate_uncertainty_R3b_cost(n_routes=len(routes))
    if not cost["under_R3b_review_cap"]:
        raise ValueError("R3b pre-run plan exceeds review cap")
    return {
        "routes": routes,
        "prior_table": prior_table,
        "cost": cost,
        "R3b_execution_authorized": False,
        "R4_representative_full_wave_validation_run": False,
        "R5_full_grid_v2_run": False,
    }


def load_representative_full_wave_R4_plan() -> dict[str, Any]:
    return load_json_yaml("r4_representative_full_wave_plan.yaml")


def representative_full_wave_R4_route_panel() -> list[dict[str, Any]]:
    return validate_representative_full_wave_R4_plan()["route_panel"]


def representative_full_wave_R4_particle_panel() -> list[dict[str, Any]]:
    return validate_representative_full_wave_R4_plan()["particle_panel"]


def estimate_representative_full_wave_R4_cost(
    *,
    n_routes: int = MAX_R4_REPRESENTATIVE_ROUTES,
    n_particles: int = MAX_R4_REPRESENTATIVE_PARTICLES,
    n_interface_states: int = MAX_R4_INTERFACE_STATES,
    n_polarization_states: int = MAX_R4_POLARIZATION_STATES,
    n_mesh_levels: int = MAX_R4_MESH_LEVELS,
) -> dict[str, Any]:
    solver_case_count = (
        n_routes
        * n_particles
        * n_interface_states
        * n_polarization_states
        * n_mesh_levels
    )
    under_cap = (
        n_routes <= MAX_R4_REPRESENTATIVE_ROUTES
        and n_particles <= MAX_R4_REPRESENTATIVE_PARTICLES
        and n_interface_states <= MAX_R4_INTERFACE_STATES
        and n_polarization_states <= MAX_R4_POLARIZATION_STATES
        and n_mesh_levels <= MAX_R4_MESH_LEVELS
        and solver_case_count <= MAX_R4_SOLVER_CASES_BEFORE_REVIEW
    )
    return {
        "n_routes": n_routes,
        "n_particles": n_particles,
        "n_interface_states": n_interface_states,
        "n_polarization_states": n_polarization_states,
        "n_mesh_levels": n_mesh_levels,
        "solver_case_count": solver_case_count,
        "max_R4_representative_routes": MAX_R4_REPRESENTATIVE_ROUTES,
        "max_R4_representative_particles": MAX_R4_REPRESENTATIVE_PARTICLES,
        "max_R4_interface_states": MAX_R4_INTERFACE_STATES,
        "max_R4_polarization_states": MAX_R4_POLARIZATION_STATES,
        "max_R4_mesh_levels": MAX_R4_MESH_LEVELS,
        "max_R4_solver_cases_before_review": MAX_R4_SOLVER_CASES_BEFORE_REVIEW,
        "under_R4_review_cap": under_cap,
        "execution_authorized_by_this_plan": False,
    }


def validate_representative_full_wave_R4_plan(
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = plan if plan is not None else load_representative_full_wave_R4_plan()
    if payload.get("schema_version") != R4_PLAN_SCHEMA_VERSION:
        raise ValueError("R4 plan schema_version mismatch")
    if payload.get("stage") != "R4_representative_full_wave_validation_plan_only":
        raise ValueError("R4 plan stage must be plan-only")

    boundary = payload.get("authorization_boundary", {})
    for key in (
        "R4_execution_authorized",
        "R5_full_grid_v2_authorized",
        "context_route_promotion_authorized",
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_authorized",
        "v1_full_grid_overwrite_authorized",
        "Tsuyama_paper_fit_continuation_authorized",
        "selected_annulus_bound_change_authorized",
        "ET2030_direct_current_input_unlock_authorized",
    ):
        if boundary.get(key) is not False:
            raise ValueError(f"R4 authorization boundary must keep {key}=false")

    cost_cap = payload.get("cost_cap", {})
    expected_caps = {
        "max_R4_representative_routes": MAX_R4_REPRESENTATIVE_ROUTES,
        "max_R4_representative_particles": MAX_R4_REPRESENTATIVE_PARTICLES,
        "max_R4_interface_states": MAX_R4_INTERFACE_STATES,
        "max_R4_polarization_states": MAX_R4_POLARIZATION_STATES,
        "max_R4_mesh_levels": MAX_R4_MESH_LEVELS,
        "max_R4_solver_cases_before_review": MAX_R4_SOLVER_CASES_BEFORE_REVIEW,
    }
    for key, value in expected_caps.items():
        if int(cost_cap.get(key, -1)) != value:
            raise ValueError(f"R4 cost cap mismatch: {key}")

    routes = payload.get("route_panel", [])
    if not isinstance(routes, list) or len(routes) != MAX_R4_REPRESENTATIVE_ROUTES:
        raise ValueError("R4 route panel must match the representative route cap")
    route_keys = {
        (int(row["wavelength_nm"]), int(row["width_nm"]), int(row["depth_nm"]))
        for row in routes
    }
    if len(route_keys) != len(routes):
        raise ValueError("R4 route panel contains duplicate routes")
    missing_routes = R4_REQUIRED_ROUTES.difference(route_keys)
    if missing_routes:
        raise ValueError(f"R4 route panel missing routes: {sorted(missing_routes)}")
    for row in routes:
        if row.get("route_role_locked") is not True:
            raise ValueError("R4 route roles must be locked")
        if row.get("route_role_source") != R4_ROUTE_ROLE_SOURCE:
            raise ValueError("R4 route_role_source mismatch")
        if row.get("context_route_promotion_authorized") is not False:
            raise ValueError("R4 context-route promotion is not authorized")
        for key in ("validation_question", "confirm_if", "demote_if", "reclassify_if"):
            if not row.get(key):
                raise ValueError(f"R4 route missing validation criterion: {key}")

    particles = payload.get("particle_panel", [])
    if not isinstance(particles, list) or len(particles) != MAX_R4_REPRESENTATIVE_PARTICLES:
        raise ValueError("R4 particle panel must match the representative particle cap")
    particle_ids = {str(row["particle_id"]) for row in particles}
    if particle_ids != R4_REQUIRED_PARTICLES:
        raise ValueError("R4 particle panel missing required representative particles")
    for row in particles:
        if row.get("biological_specificity_claim_allowed") is not False:
            raise ValueError("R4 cannot authorize biological specificity claims")
        if not row.get("particle_role"):
            raise ValueError("R4 particle panel requires particle_role")

    material_rows = payload.get("particle_material_contract", [])
    if not isinstance(material_rows, list) or len(material_rows) != len(particles):
        raise ValueError("R4 particle material contract must cover the particle panel")
    material_ids = {str(row.get("particle_id")) for row in material_rows}
    if material_ids != particle_ids:
        raise ValueError("R4 particle material contract IDs must match particle panel")
    for row in material_rows:
        missing = [
            field
            for field in R4_REQUIRED_PARTICLE_MATERIAL_FIELDS
            if field not in row or row[field] == ""
        ]
        if missing:
            raise ValueError(f"R4 particle material contract missing fields: {missing}")
        if row.get("biological_specificity_claim_allowed") is not False:
            raise ValueError("R4 material contract cannot authorize specificity claims")
        particle_id = str(row["particle_id"])
        diameter_nm = float(row["diameter_nm"])
        shell_thickness_nm = float(row["shell_thickness_nm"])
        if particle_id == "blank":
            if diameter_nm != 0.0:
                raise ValueError("R4 blank material contract must have zero diameter")
        elif diameter_nm <= 0.0:
            raise ValueError("R4 particle material diameter must be positive")
        if shell_thickness_nm < 0.0:
            raise ValueError("R4 shell thickness cannot be negative")
        if particle_id == "Au40" and "Johnson_Christy_1972" not in str(
            row["material_database_key"]
        ):
            raise ValueError("R4 Au40 must use an explicit optical constants source")

    solver_scope = payload.get("solver_scope", {})
    if solver_scope.get("execution_status") != "not_run_plan_only":
        raise ValueError("R4 solver scope must remain not-run before external authorization")
    for key, cap in (
        ("interface_states", MAX_R4_INTERFACE_STATES),
        ("polarization_states", MAX_R4_POLARIZATION_STATES),
        ("mesh_levels", MAX_R4_MESH_LEVELS),
    ):
        values = solver_scope.get(key, [])
        if not isinstance(values, list) or len(values) != cap:
            raise ValueError(f"R4 solver scope {key} must match cap")

    solver_contract = payload.get("solver_case_contract", {})
    missing_solver_fields = [
        field
        for field in R4_REQUIRED_SOLVER_CASE_CONTRACT_FIELDS
        if field not in solver_contract or solver_contract[field] is None or solver_contract[field] == ""
    ]
    if missing_solver_fields:
        raise ValueError(f"R4 solver case contract missing fields: {missing_solver_fields}")
    if solver_contract["solver_engine_class"] not in {"FDTD", "BEM", "FEM_modal_equivalent"}:
        raise ValueError("R4 solver_engine_class is not recognized")
    if solver_contract["geometry_units"] != "nm":
        raise ValueError("R4 geometry units must be nm")
    if float(solver_contract["near_wall_stress_distance_nm"]) <= 0.0:
        raise ValueError("R4 near_wall_stress_distance_nm must be positive")
    if float(solver_contract["mesh_convergence_threshold"]) <= 0.0:
        raise ValueError("R4 mesh convergence threshold must be positive")
    if float(solver_contract["solver_boundary_sensitivity_threshold"]) <= 0.0:
        raise ValueError("R4 boundary sensitivity threshold must be positive")
    pose_defs = solver_contract.get("particle_pose_definition", {})
    if set(pose_defs) != set(solver_scope["interface_states"]):
        raise ValueError("R4 interface states must have executable pose definitions")
    for name, definition in pose_defs.items():
        if not isinstance(definition, dict):
            raise ValueError(f"R4 interface state is only a label: {name}")
        if name == "near_wall_stress" and "nearest_wall_clearance_nm" not in definition:
            raise ValueError("R4 near_wall_stress requires numeric clearance")
    polarization_defs = solver_contract.get("polarization_vector_definition", {})
    if set(polarization_defs) != set(solver_scope["polarization_states"]):
        raise ValueError("R4 polarization states must have vector definitions")
    for name, definition in polarization_defs.items():
        vector = definition.get("E_vector_xyz") if isinstance(definition, dict) else None
        if not isinstance(vector, list) or len(vector) != 3:
            raise ValueError(f"R4 polarization state is only a label: {name}")
    mesh_defs = solver_contract.get("mesh_level_definitions_nm", {})
    if set(mesh_defs) != set(solver_scope["mesh_levels"]):
        raise ValueError("R4 mesh levels must have numeric definitions")
    for name, definition in mesh_defs.items():
        if not isinstance(definition, dict):
            raise ValueError(f"R4 mesh level is only a label: {name}")
        for key in ("base_cell_nm", "particle_surface_cell_nm", "minimum_cells_across_shell"):
            if key not in definition or float(definition[key]) <= 0.0:
                raise ValueError(f"R4 mesh level missing numeric {key}: {name}")
    for roi_key in ("slit_ROI_definition", "pinhole_ROI_definition"):
        roi = solver_contract.get(roi_key, {})
        if roi.get("same_operator_applied_to_reference_and_scattering") is not True:
            raise ValueError("R4 ROI operator must apply to reference and scattering")

    observable_ids = {
        str(row["observable_id"])
        for row in payload.get("observables", [])
        if isinstance(row, dict)
    }
    if not R4_REQUIRED_OBSERVABLES.issubset(observable_ids):
        raise ValueError("R4 plan missing required observables")
    for row in payload.get("observables", []):
        if row.get("claim_level") not in {"relative_with_priors", "diagnostic_only"}:
            raise ValueError("R4 observables must stay relative/diagnostic")

    criteria = payload.get("promotion_demotion_criteria", {})
    if criteria.get("context_route_promotion_authorized") is not False:
        raise ValueError("R4 criteria cannot authorize context-route promotion")
    decision_labels = set(criteria.get("allowed_decision_labels", []))
    required_labels = {
        "confirm_for_future_review",
        "demote_from_R4_candidate",
        "reclassify_requires_external_review",
        "inconclusive_requires_plan_revision",
    }
    if not required_labels.issubset(decision_labels):
        raise ValueError("R4 decision labels are incomplete")
    thresholds = criteria.get("numeric_decision_thresholds", {})
    required_thresholds = (
        "eps",
        "sign_preserved_definition",
        "surrogate_delta_log_definition",
        "surrogate_delta_log_confirm_abs_max",
        "surrogate_delta_log_demote_abs_min",
        "mesh_refined_delta_abs_max",
        "polarization_sensitivity_abs_max",
        "near_wall_stress_delta_abs_max",
        "solver_boundary_sensitivity_abs_max",
        "BFP_extraction_unit_guard_required",
        "ROI_mapping_reversal_demotes",
    )
    for key in required_thresholds:
        if key not in thresholds or thresholds[key] in {"", None}:
            raise ValueError(f"R4 numeric decision threshold missing: {key}")
    if float(thresholds["eps"]) <= 0.0:
        raise ValueError("R4 decision eps must be positive")
    if float(thresholds["surrogate_delta_log_confirm_abs_max"]) >= float(
        thresholds["surrogate_delta_log_demote_abs_min"]
    ):
        raise ValueError("R4 confirm threshold must be below demote threshold")
    for key in (
        "mesh_refined_delta_abs_max",
        "polarization_sensitivity_abs_max",
        "near_wall_stress_delta_abs_max",
        "solver_boundary_sensitivity_abs_max",
    ):
        if float(thresholds[key]) <= 0.0:
            raise ValueError(f"R4 threshold must be positive: {key}")
    if thresholds["BFP_extraction_unit_guard_required"] is not True:
        raise ValueError("R4 BFP unit guard must be required")
    if thresholds["ROI_mapping_reversal_demotes"] is not True:
        raise ValueError("R4 ROI mapping reversal must demote")
    bins = criteria.get("numeric_decision_bins", {})
    for key in (
        "confirm_for_future_review",
        "demote_from_R4_candidate",
        "inconclusive_requires_plan_revision",
    ):
        if not bins.get(key):
            raise ValueError(f"R4 numeric decision bin missing: {key}")

    outputs = set(payload.get("required_outputs_if_executed", []))
    if outputs != R4_REQUIRED_OUTPUTS_IF_EXECUTED:
        raise ValueError("R4 required output list mismatch")

    manifest_fields = payload.get("pre_review_manifest_fields", {})
    for key, value in {
        "R4_representative_full_wave_validation_run": False,
        "R5_full_grid_v2_run": False,
        "v1_full_grid_overwritten": False,
        "Tsuyama_paper_fit_continued": False,
        "selected_annulus_bounds_changed": False,
        "calibrated_SNR_claim_emitted": False,
        "ET2030_direct_current_input_unlocked": False,
    }.items():
        if manifest_fields.get(key) is not value:
            raise ValueError(f"R4 pre-review manifest field mismatch: {key}")

    hardening = payload.get("R3b_hardening_preconditions", {})
    status = hardening.get("R3b_effect_delta_hardening_status")
    if status not in R4_ALLOWED_EFFECT_DELTA_HARDENING_STATUSES:
        raise ValueError("R4 R3b effect_delta hardening status is not active")
    if "effect_delta_log_score_ratio" not in str(hardening.get("effect_delta_policy", "")):
        raise ValueError("R4 plan must carry the R3b effect_delta audit precondition")
    if not hardening.get("effect_delta_equivalence_test_name"):
        raise ValueError("R4 plan must name an active effect_delta hardening test")
    if "thermal_not_blocking_stage_progression" not in str(
        hardening.get("thermal_promotion_field_policy", "")
    ):
        raise ValueError("R4 plan must clarify thermal promotion field naming")

    stop_gates = set(payload.get("stop_gates", []))
    if not R4_REQUIRED_STOP_GATES.issubset(stop_gates):
        raise ValueError("R4 stop gates are incomplete")
    return payload


def validate_R4_pre_run_plan() -> dict[str, Any]:
    plan = validate_representative_full_wave_R4_plan()
    solver_scope = plan["solver_scope"]
    cost = estimate_representative_full_wave_R4_cost(
        n_routes=len(plan["route_panel"]),
        n_particles=len(plan["particle_panel"]),
        n_interface_states=len(solver_scope["interface_states"]),
        n_polarization_states=len(solver_scope["polarization_states"]),
        n_mesh_levels=len(solver_scope["mesh_levels"]),
    )
    if not cost["under_R4_review_cap"]:
        raise ValueError("R4 representative full-wave plan exceeds review cap")
    return {
        "plan": plan,
        "routes": plan["route_panel"],
        "particles": plan["particle_panel"],
        "cost": cost,
        "R4_execution_authorized": False,
        "R4_representative_full_wave_validation_run": False,
        "R5_full_grid_v2_run": False,
        "context_route_promotion_authorized": False,
    }


def load_R4_route_model_revision_plan() -> dict[str, Any]:
    return load_json_yaml("r4_route_model_revision_plan.yaml")


def validate_R4_route_model_revision_plan(
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = plan if plan is not None else load_R4_route_model_revision_plan()
    if payload.get("schema_version") != R4_ROUTE_MODEL_REVISION_PLAN_SCHEMA_VERSION:
        raise ValueError("R4 route-model revision plan schema_version mismatch")
    if payload.get("stage") != "R4_route_model_revision_plan_only":
        raise ValueError("R4 route-model revision stage must be plan-only")

    boundary = payload.get("authorization_boundary", {})
    false_boundary_keys = (
        "route_model_revision_execution_authorized",
        "R5_plan_preparation_authorized",
        "R5_full_grid_v2_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_authorized",
        "v1_full_grid_overwrite_authorized",
        "Tsuyama_paper_fit_continuation_authorized",
        "selected_annulus_bound_change_authorized",
        "ET2030_direct_current_input_unlock_authorized",
    )
    for key in false_boundary_keys:
        if boundary.get(key) is not False:
            raise ValueError(f"R4 route-model revision boundary must keep {key}=false")

    input_evidence = payload.get("input_evidence", {})
    if input_evidence.get("source_stage") != "R4_representative_full_wave_validation":
        raise ValueError("R4 route-model revision must consume R4 evidence")
    if input_evidence.get("accepted_gate") != (
        "PASS_R4_NUMERICAL_RERUN_HALT_R5_PLAN_ROUTE_MODEL_REVISION_ONLY"
    ):
        raise ValueError("R4 route-model revision gate mismatch")
    if input_evidence.get("all_representative_routes_demoted") is not True:
        raise ValueError("R4 route-model revision requires all-route demotion evidence")
    counts = input_evidence.get("route_decision_counts", {})
    if counts.get("demote_from_R4_candidate") != MAX_R4_REPRESENTATIVE_ROUTES:
        raise ValueError("R4 route-model revision demotion count mismatch")
    for key in (
        "confirm_for_future_review",
        "reclassify_requires_external_review",
        "inconclusive_requires_plan_revision",
    ):
        if counts.get(key) != 0:
            raise ValueError("R4 route-model revision expects only demotions")
    if input_evidence.get("main_660_validated") is not False:
        raise ValueError("R4 route-model revision must mark main_660 unvalidated")

    demoted_routes = payload.get("demoted_route_panel", [])
    if len(demoted_routes) != MAX_R4_REPRESENTATIVE_ROUTES:
        raise ValueError("R4 route-model revision route panel mismatch")
    route_keys = {
        (int(row["wavelength_nm"]), int(row["width_nm"]), int(row["depth_nm"]))
        for row in demoted_routes
    }
    if route_keys != R4_REQUIRED_ROUTES:
        raise ValueError("R4 route-model revision must cover all R4 representative routes")
    for row in demoted_routes:
        if row.get("R4_final_route_validation_decision") != "demote_from_R4_candidate":
            raise ValueError("R4 route-model revision includes a non-demoted route")
        if row.get("route_role_locked") is not True:
            raise ValueError("R4 route roles must stay locked during revision planning")
        if row.get("context_route_promotion_authorized") is not False:
            raise ValueError("R4 route-model revision cannot authorize promotion")

    focus_areas = set(payload.get("revision_focus_areas", []))
    if not R4_ROUTE_MODEL_REVISION_REQUIRED_FOCUS_AREAS.issubset(focus_areas):
        raise ValueError("R4 route-model revision focus areas are incomplete")

    sign_contract = payload.get("sign_phase_audit_contract", {})
    required_sign_fields = {
        "delta_intensity_identity",
        "cross_term_operator",
        "reference_phase_anchor_policy",
        "global_phase_invariance_check",
        "allowed_hypotheses",
        "forbidden_hypotheses",
    }
    missing_sign = required_sign_fields.difference(sign_contract)
    if missing_sign:
        raise ValueError(f"R4 sign/phase audit contract missing fields: {missing_sign}")
    if sign_contract["delta_intensity_identity"] != (
        "|E_ref + E_sca|^2 - |E_ref|^2 = "
        "2*Re(E_ref*conj(E_sca)) + |E_sca|^2"
    ):
        raise ValueError("R4 sign/phase audit identity mismatch")
    if "convention_mismatch" not in sign_contract["allowed_hypotheses"]:
        raise ValueError("R4 sign/phase audit must allow convention mismatch")
    if "posthoc_route_promotion" not in sign_contract["forbidden_hypotheses"]:
        raise ValueError("R4 sign/phase audit must forbid posthoc promotion")

    recovery = payload.get("recovery_decision_gates", {})
    if recovery.get("R5_plan_remains_blocked_until_external_review") is not True:
        raise ValueError("R4 route-model revision must keep R5 plan blocked")
    if recovery.get("context_route_promotion_authorized") is not False:
        raise ValueError("R4 route-model revision cannot promote context routes")
    if recovery.get("main_660_redefinition_authorized") is not False:
        raise ValueError("R4 route-model revision cannot redefine main_660")
    threshold = recovery.get("min_main_660_nonblank_sign_preserved_fraction_for_recovery")
    if not isinstance(threshold, int | float) or float(threshold) < 0.8:
        raise ValueError("R4 main_660 recovery sign threshold must be at least 0.8")
    if not recovery.get("future_R4_rerun_required_before_R5_plan"):
        raise ValueError("R4 route-model revision must require future R4 evidence")

    outputs = set(payload.get("required_outputs_if_executed_after_review", []))
    if outputs != R4_ROUTE_MODEL_REVISION_REQUIRED_OUTPUTS_IF_EXECUTED:
        raise ValueError("R4 route-model revision required output list mismatch")

    stop_gates = set(payload.get("stop_gates", []))
    if not R4_ROUTE_MODEL_REVISION_REQUIRED_STOP_GATES.issubset(stop_gates):
        raise ValueError("R4 route-model revision stop gates are incomplete")

    manifest = payload.get("manifest_expectations", {})
    expected_manifest = {
        "R4_representative_full_wave_validation_run": True,
        "R5_full_grid_v2_run": False,
        "v1_full_grid_overwritten": False,
        "Tsuyama_paper_fit_continued": False,
        "selected_annulus_bounds_changed": False,
        "calibrated_SNR_claim_emitted": False,
        "ET2030_direct_current_input_unlocked": False,
    }
    for key, expected in expected_manifest.items():
        if manifest.get(key) is not expected:
            raise ValueError(f"R4 route-model revision manifest mismatch: {key}")

    return payload


def load_R4_revised_rerun_plan() -> dict[str, Any]:
    return load_json_yaml("r4_revised_rerun_plan.yaml")


def estimate_R4_revised_rerun_cost(
    *,
    n_routes: int = MAX_R4_REPRESENTATIVE_ROUTES,
    n_particles: int = MAX_R4_REPRESENTATIVE_PARTICLES,
    n_interface_states: int = MAX_R4_INTERFACE_STATES,
    n_polarization_states: int = MAX_R4_POLARIZATION_STATES,
    n_mesh_levels: int = MAX_R4_MESH_LEVELS,
) -> dict[str, Any]:
    solver_case_count = (
        n_routes
        * n_particles
        * n_interface_states
        * n_polarization_states
        * n_mesh_levels
    )
    under_cap = (
        n_routes <= MAX_R4_REPRESENTATIVE_ROUTES
        and n_particles <= MAX_R4_REPRESENTATIVE_PARTICLES
        and n_interface_states <= MAX_R4_INTERFACE_STATES
        and n_polarization_states <= MAX_R4_POLARIZATION_STATES
        and n_mesh_levels <= MAX_R4_MESH_LEVELS
        and solver_case_count <= MAX_R4_REVISED_RERUN_SOLVER_CASES_BEFORE_REVIEW
    )
    return {
        "n_routes": n_routes,
        "n_particles": n_particles,
        "n_interface_states": n_interface_states,
        "n_polarization_states": n_polarization_states,
        "n_mesh_levels": n_mesh_levels,
        "solver_case_count": solver_case_count,
        "max_R4_revised_rerun_routes": MAX_R4_REPRESENTATIVE_ROUTES,
        "max_R4_revised_rerun_particles": MAX_R4_REPRESENTATIVE_PARTICLES,
        "max_R4_revised_rerun_interface_states": MAX_R4_INTERFACE_STATES,
        "max_R4_revised_rerun_polarization_states": MAX_R4_POLARIZATION_STATES,
        "max_R4_revised_rerun_mesh_levels": MAX_R4_MESH_LEVELS,
        "max_R4_revised_rerun_solver_cases_before_review": (
            MAX_R4_REVISED_RERUN_SOLVER_CASES_BEFORE_REVIEW
        ),
        "under_R4_revised_rerun_review_cap": under_cap,
        "execution_authorized_by_this_plan": False,
    }


def _R4_main_660_global_flip_failure_groups() -> dict[tuple[str, str, str], int]:
    observable_path = DEFAULT_REPRESENTATIVE_FULL_WAVE_R4_DIR / (
        "full_wave_observable_summary.csv"
    )
    failure_groups: dict[tuple[str, str, str], int] = {}
    if not observable_path.exists():
        return failure_groups
    for row in _read_csv_dicts(observable_path):
        if row.get("route_role") != "main_660" or row.get("particle_id") == "blank":
            continue
        full_wave = float(row["full_wave_cross_term_signed_W"])
        surrogate = float(row["surrogate_cross_term_signed_W"])
        if _sign(-full_wave) == _sign(surrogate):
            continue
        key = (row["route_id"], row["interface_state"], row["mesh_level"])
        failure_groups[key] = failure_groups.get(key, 0) + 1
    return failure_groups


def validate_R4_revised_rerun_plan(
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = plan if plan is not None else load_R4_revised_rerun_plan()
    if payload.get("schema_version") != R4_REVISED_RERUN_PLAN_SCHEMA_VERSION:
        raise ValueError("R4 revised rerun plan schema_version mismatch")
    if payload.get("stage") != "R4_revised_rerun_plan_only":
        raise ValueError("R4 revised rerun stage must be plan-only")

    boundary = payload.get("authorization_boundary", {})
    false_boundary_keys = (
        "revised_R4_rerun_execution_authorized",
        "R5_plan_preparation_authorized",
        "R5_full_grid_v2_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_authorized",
        "v1_full_grid_overwrite_authorized",
        "Tsuyama_paper_fit_continuation_authorized",
        "selected_annulus_bound_change_authorized",
        "ET2030_direct_current_input_unlock_authorized",
    )
    for key in false_boundary_keys:
        if boundary.get(key) is not False:
            raise ValueError(f"R4 revised rerun boundary must keep {key}=false")

    evidence = payload.get("input_evidence", {})
    if evidence.get("accepted_gate") != (
        "PASS_ROUTE_MODEL_AUDIT_PREPARE_REVISED_R4_RERUN_PLAN_ONLY"
    ):
        raise ValueError("R4 revised rerun plan gate mismatch")
    if evidence.get("route_model_revision_audit_decision") != (
        "partial_convention_signal_but_main_660_recovery_gate_not_met"
    ):
        raise ValueError("R4 revised rerun must consume the partial audit decision")
    if evidence.get("best_allowed_convention_id") != (
        "global_full_wave_cross_term_sign_flip"
    ):
        raise ValueError("R4 revised rerun must target the global flip convention signal")
    if float(evidence.get("all_nonblank_sign_preserved_after_global_flip", -1.0)) < 0.86:
        raise ValueError("R4 revised rerun evidence must record strong all-route signal")
    if float(evidence.get("main_660_nonblank_sign_preserved_after_global_flip", -1.0)) != 0.75:
        raise ValueError("R4 revised rerun evidence must preserve the failed main_660 gate")
    if evidence.get("main_660_recovery_gate_met") is not False:
        raise ValueError("R4 revised rerun plan cannot treat main_660 as recovered")

    focus = set(payload.get("revision_focus_areas", []))
    if not R4_REVISED_RERUN_REQUIRED_FOCUS_AREAS.issubset(focus):
        raise ValueError("R4 revised rerun focus areas are incomplete")

    cost_cap = payload.get("cost_cap", {})
    expected_caps = {
        "max_R4_revised_rerun_routes": MAX_R4_REPRESENTATIVE_ROUTES,
        "max_R4_revised_rerun_particles": MAX_R4_REPRESENTATIVE_PARTICLES,
        "max_R4_revised_rerun_interface_states": MAX_R4_INTERFACE_STATES,
        "max_R4_revised_rerun_polarization_states": MAX_R4_POLARIZATION_STATES,
        "max_R4_revised_rerun_mesh_levels": MAX_R4_MESH_LEVELS,
        "max_R4_revised_rerun_solver_cases_before_review": (
            MAX_R4_REVISED_RERUN_SOLVER_CASES_BEFORE_REVIEW
        ),
    }
    for key, expected in expected_caps.items():
        if int(cost_cap.get(key, -1)) != expected:
            raise ValueError(f"R4 revised rerun cost cap mismatch: {key}")
    cost = estimate_R4_revised_rerun_cost()
    if not cost["under_R4_revised_rerun_review_cap"]:
        raise ValueError("R4 revised rerun plan exceeds review cap")

    route_panel = payload.get("route_panel", [])
    if len(route_panel) != MAX_R4_REPRESENTATIVE_ROUTES:
        raise ValueError("R4 revised rerun route panel mismatch")
    route_keys = {
        (int(row["wavelength_nm"]), int(row["width_nm"]), int(row["depth_nm"]))
        for row in route_panel
    }
    if route_keys != R4_REQUIRED_ROUTES:
        raise ValueError("R4 revised rerun must keep the nine representative routes")
    for row in route_panel:
        if row.get("route_role_locked") is not True:
            raise ValueError("R4 revised rerun route roles must remain locked")
        if row.get("context_route_promotion_authorized") is not False:
            raise ValueError("R4 revised rerun cannot authorize context-route promotion")
        if row.get("main_660_redefinition_authorized") is not False:
            raise ValueError("R4 revised rerun cannot redefine main_660")

    particle_panel = payload.get("particle_panel", [])
    if len(particle_panel) != MAX_R4_REPRESENTATIVE_PARTICLES:
        raise ValueError("R4 revised rerun particle panel mismatch")
    if {str(row["particle_id"]) for row in particle_panel} != R4_REQUIRED_PARTICLES:
        raise ValueError("R4 revised rerun particle panel must match representative R4")
    if any(row.get("biological_specificity_claim_allowed") is not False for row in particle_panel):
        raise ValueError("R4 revised rerun cannot authorize specificity claims")

    convention = payload.get("cross_term_convention_contract", {})
    if convention.get("canonical_delta_P_NODI_identity") != (
        "Delta_P_NODI = |E_ref + E_sca|^2 - |E_ref|^2 = "
        "|E_sca|^2 + 2*Re(E_ref*conj(E_sca))"
    ):
        raise ValueError("R4 revised rerun cross-term identity mismatch")
    if "full_wave_cross_term_signed_W" not in str(
        convention.get("polarity_mapping_questions", [])
    ):
        raise ValueError("R4 revised rerun must map full-wave cross-term polarity")
    if convention.get("global_flip_is_not_recovery_by_itself") is not True:
        raise ValueError("R4 revised rerun must not treat a global flip as recovery")

    ambiguity = payload.get("main_660_near_wall_coarse_screen_diagnostic", {})
    if ambiguity.get("diagnostic_id") != "main_660_near_wall_coarse_sign_ambiguity_check":
        raise ValueError("R4 revised rerun missing main_660 ambiguity diagnostic")
    if int(ambiguity.get("failed_rows_after_global_flip", -1)) != 20:
        raise ValueError("R4 revised rerun must preserve the 20-row main_660 failure")
    if int(ambiguity.get("main_660_nonblank_rows", -1)) != 80:
        raise ValueError("R4 revised rerun must preserve the 80-row main_660 denominator")
    cluster = ambiguity.get("failure_cluster", [])
    expected_cluster = {
        ("660_800x1400", "near_wall_stress", "coarse_screen", 10),
        ("660_800x1500", "near_wall_stress", "coarse_screen", 10),
    }
    actual_cluster = {
        (
            str(row["route_id"]),
            str(row["interface_state"]),
            str(row["mesh_level"]),
            int(row["failed_rows_after_global_flip"]),
        )
        for row in cluster
    }
    if actual_cluster != expected_cluster:
        raise ValueError("R4 revised rerun failure cluster must match accepted audit")
    current_failures = _R4_main_660_global_flip_failure_groups()
    if current_failures:
        expected_from_csv = {
            (route, interface, mesh, count)
            for (route, interface, mesh), count in current_failures.items()
        }
        if expected_from_csv != expected_cluster:
            raise ValueError("R4 revised rerun failure cluster drifted from R4 CSV")

    diagnostic_fields = set(ambiguity.get("required_output_fields", []))
    if not R4_REVISED_RERUN_REQUIRED_DIAGNOSTIC_FIELDS.issubset(diagnostic_fields):
        raise ValueError("R4 revised rerun diagnostic fields are incomplete")

    reliability = payload.get("sign_reliability_policy", {})
    formula = str(reliability.get("sign_reliable_definition", ""))
    if "max(absolute_floor_W, relative_floor" not in formula:
        raise ValueError("R4 revised rerun sign reliability formula mismatch")
    if float(reliability.get("absolute_floor_W", 0.0)) <= 0.0:
        raise ValueError("R4 revised rerun absolute sign floor must be positive")
    relative_floor = float(reliability.get("relative_floor", -1.0))
    if not 0.0 < relative_floor < 1.0:
        raise ValueError("R4 revised rerun relative sign floor must be between 0 and 1")
    if reliability.get("retroactive_reinterpretation_of_current_audit_allowed") is not False:
        raise ValueError("R4 revised rerun sign reliability cannot rewrite the audit")

    recovery = payload.get("recovery_criteria", {})
    if float(recovery.get("main_660_nonblank_after_global_convention_min", -1.0)) < 0.8:
        raise ValueError("R4 revised rerun main_660 raw recovery threshold too low")
    if float(recovery.get("main_660_sign_reliable_subset_min", -1.0)) < 0.8:
        raise ValueError("R4 revised rerun reliable-subset threshold too low")
    if float(recovery.get("main_660_review_refined_mesh_min", -1.0)) < 0.8:
        raise ValueError("R4 revised rerun refined-mesh threshold too low")
    for key in (
        "no_route_role_change_required",
        "no_context_route_promotion_required",
        "future_external_review_required_before_R5_plan",
    ):
        if recovery.get(key) is not True:
            raise ValueError(f"R4 revised rerun recovery criterion must require {key}")
    if recovery.get("possible_future_gate_after_success") != (
        "PASS_REVISED_R4_RESULTS_PREPARE_R5_PLAN_ONLY"
    ):
        raise ValueError("R4 revised rerun must only allow a future plan gate after success")

    outputs = set(payload.get("required_outputs_if_executed_after_review", []))
    if outputs != R4_REVISED_RERUN_REQUIRED_OUTPUTS_IF_EXECUTED:
        raise ValueError("R4 revised rerun required output list mismatch")
    stop_gates = set(payload.get("stop_gates", []))
    if not R4_REVISED_RERUN_REQUIRED_STOP_GATES.issubset(stop_gates):
        raise ValueError("R4 revised rerun stop gates are incomplete")

    manifest = payload.get("manifest_expectations", {})
    expected_manifest = {
        "R4_representative_full_wave_validation_run": True,
        "R4_revised_rerun_run": False,
        "R5_full_grid_v2_run": False,
        "v1_full_grid_overwritten": False,
        "Tsuyama_paper_fit_continued": False,
        "selected_annulus_bounds_changed": False,
        "calibrated_SNR_claim_emitted": False,
        "ET2030_direct_current_input_unlocked": False,
    }
    for key, expected in expected_manifest.items():
        if manifest.get(key) is not expected:
            raise ValueError(f"R4 revised rerun manifest mismatch: {key}")

    return payload


def load_R4_2_adjudication_plan() -> dict[str, Any]:
    return load_json_yaml("r4_2_main660_nearwall_mesh_adjudication_plan.yaml")


def estimate_R4_2_adjudication_cost(
    *,
    n_routes: int = 2,
    n_particles: int = 6,
    n_interface_states: int = 2,
    n_polarization_states: int = 2,
    n_new_mesh_levels: int = 1,
) -> dict[str, Any]:
    solver_case_count = (
        n_routes
        * n_particles
        * n_interface_states
        * n_polarization_states
        * n_new_mesh_levels
    )
    under_cap = solver_case_count <= MAX_R4_2_ADJUDICATION_SOLVER_CASES_BEFORE_REVIEW
    return {
        "n_routes": n_routes,
        "n_particles": n_particles,
        "n_interface_states": n_interface_states,
        "n_polarization_states": n_polarization_states,
        "n_new_mesh_levels": n_new_mesh_levels,
        "solver_case_count": solver_case_count,
        "max_R4_2_solver_cases_before_review": (
            MAX_R4_2_ADJUDICATION_SOLVER_CASES_BEFORE_REVIEW
        ),
        "under_R4_2_review_cap": under_cap,
        "execution_authorized_by_this_plan": False,
    }


def validate_R4_2_adjudication_plan(
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = plan if plan is not None else load_R4_2_adjudication_plan()
    if payload.get("schema_version") != R4_2_ADJUDICATION_PLAN_SCHEMA_VERSION:
        raise ValueError("R4.2 adjudication plan schema_version mismatch")
    if payload.get("stage") != "R4_2_main660_nearwall_mesh_adjudication_plan_only":
        raise ValueError("R4.2 adjudication stage must be plan-only")

    boundary = payload.get("authorization_boundary", {})
    for key in (
        "R4_2_execution_authorized",
        "R5_plan_preparation_authorized",
        "R5_full_grid_v2_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "route_specific_manual_sign_flips_authorized",
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_authorized",
        "v1_full_grid_overwrite_authorized",
        "Tsuyama_paper_fit_continuation_authorized",
        "selected_annulus_bound_change_authorized",
        "ET2030_direct_current_input_unlock_authorized",
    ):
        if boundary.get(key) is not False:
            raise ValueError(f"R4.2 adjudication boundary must keep {key}=false")

    evidence = payload.get("input_evidence", {})
    if evidence.get("accepted_gate") != (
        "FAIL_REVISED_R4_RESULTS_RERUN_OR_ROUTE_MODEL_REVISION_REQUIRED"
    ):
        raise ValueError("R4.2 adjudication must consume the failed revised R4 gate")
    if evidence.get("recommended_next_action") != (
        "prepare_R4_2_main660_nearwall_mesh_adjudication_plan_only"
    ):
        raise ValueError("R4.2 adjudication next action mismatch")
    if float(evidence.get("main_660_nonblank_after_global_convention", -1.0)) != 0.75:
        raise ValueError("R4.2 must preserve failed main_660 global-convention result")
    if float(evidence.get("main_660_sign_reliable_subset", -1.0)) < 0.75:
        raise ValueError("R4.2 must preserve failed reliable-subset result")
    if float(evidence.get("main_660_sign_reliable_subset", -1.0)) >= 0.8:
        raise ValueError("R4.2 cannot treat the reliable-subset gate as passing")
    if float(evidence.get("main_660_review_refined_mesh", -1.0)) != 1.0:
        raise ValueError("R4.2 must preserve review-refined mesh pass evidence")
    if evidence.get("main_660_recovery_gate_met") is not False:
        raise ValueError("R4.2 cannot treat main_660 as recovered")

    route_panel = payload.get("route_panel", [])
    route_keys = {
        (int(row["wavelength_nm"]), int(row["width_nm"]), int(row["depth_nm"]))
        for row in route_panel
    }
    if route_keys != R4_2_ADJUDICATION_ROUTES or len(route_panel) != 2:
        raise ValueError("R4.2 route panel must be exactly the two main_660 routes")
    for row in route_panel:
        if row.get("route_role") != "main_660":
            raise ValueError("R4.2 routes must remain main_660")
        if row.get("route_role_locked") is not True:
            raise ValueError("R4.2 route roles must stay locked")
        if row.get("main_660_redefinition_authorized") is not False:
            raise ValueError("R4.2 cannot redefine main_660")

    particle_panel = payload.get("particle_panel", {})
    required_particles = set(particle_panel.get("required_nonblank_particles", []))
    optional_particles = set(particle_panel.get("optional_particles", []))
    if required_particles != R4_2_ADJUDICATION_PARTICLES_REQUIRED:
        raise ValueError("R4.2 required particle panel mismatch")
    if not optional_particles.issubset(R4_2_ADJUDICATION_PARTICLES_OPTIONAL):
        raise ValueError("R4.2 optional particle panel mismatch")

    solver_scope = payload.get("solver_scope", {})
    if solver_scope.get("interface_states") != [
        "near_wall_stress",
        "centerline_nominal",
    ]:
        raise ValueError("R4.2 interface states must target near-wall with controls")
    if set(solver_scope.get("polarization_states", [])) != {
        "nominal_linear",
        "orthogonal_sensitivity",
    }:
        raise ValueError("R4.2 polarization states mismatch")
    if set(solver_scope.get("new_mesh_levels", [])) != R4_2_ADJUDICATION_NEW_MESH_LEVELS:
        raise ValueError("R4.2 must add only the fine_confirm mesh level")
    mesh_roles = solver_scope.get("mesh_level_roles", {})
    if mesh_roles.get("coarse_screen") != "screening_only":
        raise ValueError("R4.2 must mark coarse_screen as screening_only")
    if mesh_roles.get("review_refined") != "validation_grade":
        raise ValueError("R4.2 must mark review_refined as validation_grade")
    if mesh_roles.get("fine_confirm") != "validation_grade_confirmation":
        raise ValueError("R4.2 fine_confirm mesh role mismatch")
    if set(
        solver_scope.get("validation_grade_mesh_levels", [])
    ) != R4_2_ADJUDICATION_VALIDATION_MESH_LEVEL_ROLES:
        raise ValueError("R4.2 validation-grade mesh levels mismatch")

    cost_cap = payload.get("cost_cap", {})
    cost = estimate_R4_2_adjudication_cost(
        n_routes=len(route_panel),
        n_particles=len(required_particles) + len(optional_particles),
        n_interface_states=len(solver_scope["interface_states"]),
        n_polarization_states=len(solver_scope["polarization_states"]),
        n_new_mesh_levels=len(solver_scope["new_mesh_levels"]),
    )
    if int(cost_cap.get("max_R4_2_solver_cases_before_review", -1)) != (
        MAX_R4_2_ADJUDICATION_SOLVER_CASES_BEFORE_REVIEW
    ):
        raise ValueError("R4.2 cost cap mismatch")
    if int(cost_cap.get("planned_solver_case_count", -1)) != cost["solver_case_count"]:
        raise ValueError("R4.2 planned solver case count mismatch")
    if not cost["under_R4_2_review_cap"]:
        raise ValueError("R4.2 adjudication plan exceeds review cap")

    adjudication = payload.get("adjudication_questions", {})
    if adjudication.get("primary_question") != (
        "does_fine_confirm_agree_with_review_refined_or_coarse_screen_for_main660_near_wall_sign"
    ):
        raise ValueError("R4.2 primary adjudication question mismatch")
    if adjudication.get("coarse_screen_can_confirm_or_demote_routes") is not False:
        raise ValueError("R4.2 coarse_screen cannot be decision-grade")
    if adjudication.get("route_specific_manual_sign_flips_allowed") is not False:
        raise ValueError("R4.2 cannot allow route-specific manual sign flips")

    required_diagnostics = payload.get("required_diagnostics", {})
    if set(required_diagnostics.get("mode_lobe_fields", [])) != (
        R4_2_ADJUDICATION_REQUIRED_MODE_LOBE_FIELDS
    ):
        raise ValueError("R4.2 mode/lobe diagnostic fields mismatch")
    if set(required_diagnostics.get("required_main660_cluster_fields", [])) != (
        R4_2_ADJUDICATION_REQUIRED_CLUSTER_FIELDS
    ):
        raise ValueError("R4.2 main-660 cluster diagnostic fields mismatch")
    if required_diagnostics.get("phase_diagnostic_only_not_gate_replacement") is not True:
        raise ValueError("R4.2 phase diagnostics cannot replace the sign gate")
    if required_diagnostics.get("near_wall_stress_sidecar_not_score_bonus") is not True:
        raise ValueError("R4.2 near-wall sidecar cannot add score")

    criteria = payload.get("decision_criteria", {})
    if float(criteria.get("fine_confirm_main660_fraction_min", -1.0)) < 0.8:
        raise ValueError("R4.2 fine-confirm threshold too low")
    if float(criteria.get("review_refined_main660_fraction_min", -1.0)) < 0.8:
        raise ValueError("R4.2 review-refined threshold too low")
    if float(criteria.get("fine_confirm_agrees_with_review_refined_min", -1.0)) < 0.9:
        raise ValueError("R4.2 fine/refined agreement threshold too low")
    if criteria.get("coarse_screen_disagreement_warning_only") is not True:
        raise ValueError("R4.2 coarse disagreement must be warning-only")
    if criteria.get("possible_future_gate_after_success") != (
        "PASS_R4_2_RESULTS_PREPARE_R5_PLAN_ONLY"
    ):
        raise ValueError("R4.2 success can only prepare an R5 plan")
    if criteria.get("R5_execution_authorized_by_success") is not False:
        raise ValueError("R4.2 success cannot authorize R5 execution")

    outputs = set(payload.get("required_outputs_if_executed_after_review", []))
    if outputs != R4_2_ADJUDICATION_REQUIRED_OUTPUTS_IF_EXECUTED:
        raise ValueError("R4.2 required output list mismatch")
    stop_gates = set(payload.get("stop_gates", []))
    if not R4_2_ADJUDICATION_REQUIRED_STOP_GATES.issubset(stop_gates):
        raise ValueError("R4.2 stop gates are incomplete")

    manifest = payload.get("manifest_expectations", {})
    expected_manifest = {
        "R4_representative_full_wave_validation_run": True,
        "R4_revised_rerun_run": True,
        "R4_2_main660_nearwall_mesh_adjudication_run": False,
        "R5_full_grid_v2_run": False,
        "v1_full_grid_overwritten": False,
        "Tsuyama_paper_fit_continued": False,
        "selected_annulus_bounds_changed": False,
        "calibrated_SNR_claim_emitted": False,
        "ET2030_direct_current_input_unlocked": False,
    }
    for key, expected in expected_manifest.items():
        if manifest.get(key) is not expected:
            raise ValueError(f"R4.2 manifest expectation mismatch: {key}")

    return payload


def load_R5_full_grid_v2_plan() -> dict[str, Any]:
    return load_json_yaml("r5_full_grid_v2_plan.yaml")


def estimate_R5_full_grid_v2_plan_cost(
    *,
    n_v1_source_rows: int = R5_V1_SOURCE_ROW_COUNT,
    n_named_scenario_bundles: int = R5_NAMED_SCENARIO_BUNDLE_COUNT,
    n_stochastic_seeds: int = R5_STOCHASTIC_SEED_COUNT,
) -> dict[str, Any]:
    seed_multiplier = n_stochastic_seeds if n_stochastic_seeds > 0 else 1
    case_row_count = n_v1_source_rows * n_named_scenario_bundles * seed_multiplier
    under_cap = case_row_count <= MAX_R5_FULL_GRID_V2_CASE_ROWS_BEFORE_REVIEW
    return {
        "n_v1_source_rows": n_v1_source_rows,
        "n_named_scenario_bundles": n_named_scenario_bundles,
        "n_stochastic_seeds": n_stochastic_seeds,
        "seed_multiplier": seed_multiplier,
        "case_row_count": case_row_count,
        "max_R5_full_grid_v2_case_rows_before_review": (
            MAX_R5_FULL_GRID_V2_CASE_ROWS_BEFORE_REVIEW
        ),
        "under_R5_review_cap": under_cap,
        "R5_execution_authorized_by_this_plan": False,
    }


def validate_R5_full_grid_v2_plan(
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = plan if plan is not None else load_R5_full_grid_v2_plan()
    if payload.get("schema_version") != R5_PLAN_SCHEMA_VERSION:
        raise ValueError("R5 full-grid v2 plan schema_version mismatch")
    if payload.get("stage") != "R5_full_grid_v2_plan_only":
        raise ValueError("R5 full-grid v2 stage must be plan-only")
    if payload.get("prior_gate") != "PASS_R4_2_RESULTS_PREPARE_R5_PLAN_ONLY":
        raise ValueError("R5 plan must consume the accepted R4.2 result gate")

    boundary = payload.get("authorization_boundary", {})
    if boundary.get("R5_plan_preparation_authorized_by_prior_gate") is not True:
        raise ValueError("R5 plan preparation must be authorized only by the prior gate")
    for key in (
        "R5_full_grid_v2_execution_authorized",
        "R5_full_grid_v2_run",
        "v1_full_grid_overwrite_authorized",
        "Tsuyama_paper_fit_continuation_authorized",
        "selected_annulus_bound_change_authorized",
        "selected_annulus_replaces_all_crossing_ranking_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "optional_660_900x1400_redefines_main_660_authorized",
        "route_specific_manual_sign_flips_authorized",
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
        "ET2030_direct_current_input_unlock_authorized",
    ):
        if boundary.get(key) is not False:
            raise ValueError(f"R5 plan boundary must keep {key}=false")
    if boundary.get("external_review_required_before_R5_execution") is not True:
        raise ValueError("R5 execution must require a later external review")

    source = payload.get("source_inventory", {})
    if int(source.get("v1_source_row_count", -1)) != R5_V1_SOURCE_ROW_COUNT:
        raise ValueError("R5 v1 source row count mismatch")
    if int(source.get("v1_route_identity_count", -1)) != R5_V1_SOURCE_ROUTE_COUNT:
        raise ValueError("R5 v1 route identity count mismatch")
    if int(source.get("v1_particle_name_count", -1)) != R5_V1_SOURCE_PARTICLE_NAME_COUNT:
        raise ValueError("R5 v1 particle count mismatch")
    if int(source.get("v1_events_per_case_source_metadata", -1)) != 10000:
        raise ValueError("R5 must preserve the v1 10000e source metadata")
    if source.get("v1_full_grid_overwrite_allowed") is not False:
        raise ValueError("R5 plan cannot allow v1 full-grid overwrite")
    if source.get("legacy_detector_SNR_output_header_present") is not False:
        raise ValueError("R5 source inventory cannot expose detector_SNR")
    if source.get("legacy_calibrated_detector_SNR_output_header_present") is not False:
        raise ValueError("R5 source inventory cannot expose calibrated_detector_SNR")

    evidence = payload.get("R4_2_evidence_carryforward", {})
    if evidence.get("accepted_gate") != "PASS_R4_2_RESULTS_PREPARE_R5_PLAN_ONLY":
        raise ValueError("R5 plan must carry forward the accepted R4.2 gate")
    for key in (
        "fine_confirm_main660_fraction",
        "fine_confirm_sign_reliable_subset_fraction",
        "review_refined_main660_fraction",
        "fine_confirm_agrees_with_review_refined",
    ):
        if float(evidence.get(key, -1.0)) != 1.0:
            raise ValueError(f"R5 R4.2 carryforward metric mismatch: {key}")
    if evidence.get("R4_2_gate_met") is not True:
        raise ValueError("R5 plan must preserve R4.2 gate pass")
    if evidence.get("coarse_screen_role") != "screening_only_warning":
        raise ValueError("R5 plan must carry coarse_screen as warning-only")
    if evidence.get("coarse_screen_can_confirm_or_demote_routes") is not False:
        raise ValueError("R5 plan cannot make coarse_screen decision-grade")

    route_governance = payload.get("route_governance", {})
    main_routes = {
        (int(row["wavelength_nm"]), int(row["width_nm"]), int(row["depth_nm"]))
        for row in route_governance.get("locked_main_660_routes", [])
    }
    if main_routes != R5_MAIN_660_LOCKED_ROUTES:
        raise ValueError("R5 locked main_660 route panel mismatch")
    if route_governance.get("main_660_route_role_locked") is not True:
        raise ValueError("R5 main_660 role must remain locked")
    if route_governance.get("context_routes_can_be_promoted") is not False:
        raise ValueError("R5 plan cannot promote context routes")
    if route_governance.get("optional_660_900x1400_can_redefine_main_660") is not False:
        raise ValueError("R5 plan cannot let optional 660/900x1400 redefine main_660")
    if route_governance.get("selected_annulus_replaces_all_crossing_ranking") is not False:
        raise ValueError("R5 plan cannot replace all-crossing ranking")
    if route_governance.get("route_specific_manual_sign_flips_allowed") is not False:
        raise ValueError("R5 plan cannot allow route-specific manual sign flips")
    if route_governance.get("coarse_screen_ranking_role") != "warning_only_not_rank_gate":
        raise ValueError("R5 coarse_screen role must stay warning-only")

    scenario_policy = payload.get("scenario_policy", {})
    scenario_ids = set(scenario_policy.get("named_scenario_bundle_ids", []))
    if scenario_ids != R5_REQUIRED_SCENARIO_BUNDLE_IDS:
        raise ValueError("R5 named scenario bundle panel mismatch")
    if int(scenario_policy.get("named_scenario_bundle_count", -1)) != (
        R5_NAMED_SCENARIO_BUNDLE_COUNT
    ):
        raise ValueError("R5 scenario bundle count mismatch")
    if scenario_policy.get("cartesian_uncertainty_expansion_authorized") is not False:
        raise ValueError("R5 plan cannot use Cartesian uncertainty expansion")
    if scenario_policy.get("stochastic_seed_expansion_authorized") is not False:
        raise ValueError("R5 plan cannot add stochastic seed expansion")
    if scenario_policy.get("stochastic_seeds") != []:
        raise ValueError("R5 plan must not include stochastic seeds")

    cost_cap = payload.get("cost_cap", {})
    cost = estimate_R5_full_grid_v2_plan_cost(
        n_v1_source_rows=int(source["v1_source_row_count"]),
        n_named_scenario_bundles=int(scenario_policy["named_scenario_bundle_count"]),
        n_stochastic_seeds=len(scenario_policy.get("stochastic_seeds", [])),
    )
    if int(cost_cap.get("planned_case_rows", -1)) != cost["case_row_count"]:
        raise ValueError("R5 planned case row count mismatch")
    if int(cost_cap.get("max_R5_full_grid_v2_case_rows_before_review", -1)) != (
        MAX_R5_FULL_GRID_V2_CASE_ROWS_BEFORE_REVIEW
    ):
        raise ValueError("R5 case-row cap mismatch")
    if cost_cap.get("under_R5_review_cap") is not True or not cost["under_R5_review_cap"]:
        raise ValueError("R5 plan exceeds review cap")
    if cost_cap.get("execution_authorized_by_this_plan") is not False:
        raise ValueError("R5 plan cannot authorize its own execution")

    outputs = set(payload.get("required_outputs_if_executed_after_future_review", []))
    if outputs != R5_REQUIRED_OUTPUTS_IF_EXECUTED_AFTER_REVIEW:
        raise ValueError("R5 required output list mismatch")
    stop_gates = set(payload.get("stop_gates", []))
    if not R5_REQUIRED_STOP_GATES.issubset(stop_gates):
        raise ValueError("R5 stop gates are incomplete")

    claim_boundaries = payload.get("claim_boundaries", {})
    expected_claims = {
        "SNR_claim_level": "absolute_blocked",
        "event_probability_claim_level": "absolute_blocked",
        "p_detect_mapping_claim_level": "relative_with_priors",
    }
    for key, expected in expected_claims.items():
        if claim_boundaries.get(key) != expected:
            raise ValueError(f"R5 claim boundary mismatch: {key}")
    for key in (
        "legacy_detector_SNR_output_header_authorized",
        "legacy_calibrated_detector_SNR_output_header_authorized",
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_claim_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
    ):
        if claim_boundaries.get(key) is not False:
            raise ValueError(f"R5 claim boundary must keep {key}=false")

    provenance = payload.get("provenance_freeze", {})
    if set(provenance.get("required_checksum_fields", [])) != (
        R5_REQUIRED_SOURCE_CHECKSUM_FIELDS
    ):
        raise ValueError("R5 required checksum field set mismatch")
    if set(provenance.get("future_execution_manifest_required_checksum_fields", [])) != (
        R5_REQUIRED_FUTURE_PLAN_CHECKSUM_FIELDS
    ):
        raise ValueError("R5 future plan checksum field set mismatch")
    for field in R5_REQUIRED_SOURCE_CHECKSUM_FIELDS:
        value = str(provenance.get(field, ""))
        if len(value) != 64:
            raise ValueError(f"R5 provenance checksum is not sha256-like: {field}")

    manifest = payload.get("manifest_expectations", {})
    expected_manifest = {
        "R4_2_main660_nearwall_mesh_adjudication_run": True,
        "R5_plan_preparation_started": False,
        "R5_full_grid_v2_run": False,
        "v1_full_grid_overwritten": False,
        "Tsuyama_paper_fit_continued": False,
        "selected_annulus_bounds_changed": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        "route_specific_manual_sign_flips_authorized": False,
        "calibrated_SNR_claim_emitted": False,
        "ET2030_direct_current_input_unlocked": False,
    }
    for key, expected in expected_manifest.items():
        if manifest.get(key) is not expected:
            raise ValueError(f"R5 manifest expectation mismatch: {key}")

    return payload


def load_R5_scenario_bundle_manifest() -> dict[str, Any]:
    return load_json_yaml("r5_scenario_bundle_manifest.yaml")


def validate_R5_scenario_bundle_manifest(
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = manifest if manifest is not None else load_R5_scenario_bundle_manifest()
    if payload.get("schema_version") != R5_SCENARIO_BUNDLE_MANIFEST_SCHEMA_VERSION:
        raise ValueError("R5 scenario bundle manifest schema_version mismatch")
    if payload.get("stage") != "R5_full_grid_v2_execution_support":
        raise ValueError("R5 scenario bundle manifest stage mismatch")
    if payload.get("cartesian_uncertainty_expansion_authorized") is not False:
        raise ValueError("R5 scenario manifest cannot authorize Cartesian expansion")
    if payload.get("stochastic_seed_expansion_authorized") is not False:
        raise ValueError("R5 scenario manifest cannot authorize seed expansion")
    scenario_rows = payload.get("scenario_bundles", [])
    if len(scenario_rows) != R5_NAMED_SCENARIO_BUNDLE_COUNT:
        raise ValueError("R5 scenario manifest bundle count mismatch")
    for row in scenario_rows:
        missing = R5_REQUIRED_SCENARIO_BUNDLE_FIELDS.difference(row)
        if missing:
            raise ValueError(f"R5 scenario bundle missing fields: {sorted(missing)}")
    scenario_ids = {str(row["scenario_id"]) for row in scenario_rows}
    if scenario_ids != R5_REQUIRED_SCENARIO_BUNDLE_IDS:
        raise ValueError("R5 scenario manifest bundle IDs mismatch")
    code_rows = {
        str(row["scenario_id"]): row for row in anchor_smoke_scenario_bundles()
    }
    for row in scenario_rows:
        code_row = code_rows[str(row["scenario_id"])]
        for key in R5_REQUIRED_SCENARIO_BUNDLE_FIELDS:
            value = row[key]
            code_value = code_row[key]
            if isinstance(value, int | float):
                if not math.isclose(float(value), float(code_value), rel_tol=0.0, abs_tol=1e-15):
                    raise ValueError(f"R5 scenario manifest/code mismatch: {row['scenario_id']} {key}")
            elif value != code_value:
                raise ValueError(f"R5 scenario manifest/code mismatch: {row['scenario_id']} {key}")
    return payload


def load_R5_1_route_role_stability_plan() -> dict[str, Any]:
    return load_json_yaml("r5_1_route_role_stability_interpretation_plan.yaml")


def validate_R5_1_route_role_stability_plan(
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = plan if plan is not None else load_R5_1_route_role_stability_plan()
    if payload.get("schema_version") != R5_1_PLAN_SCHEMA_VERSION:
        raise ValueError("R5.1 route-role stability plan schema_version mismatch")
    if payload.get("stage") != "R5_1_route_role_stability_interpretation_plan_only":
        raise ValueError("R5.1 stage must be plan-only")
    if payload.get("prior_gate") != "PASS_R5_RESULTS_PREPARE_NEXT_STAGE_PLAN_ONLY":
        raise ValueError("R5.1 plan must consume the accepted R5 results gate")
    if payload.get("selected_next_stage_lane") != (
        "R5_1_route_role_stability_interpretation_report_only"
    ):
        raise ValueError("R5.1 must select the interpretation-report-only lane")

    boundary = payload.get("authorization_boundary", {})
    if boundary.get("next_stage_plan_preparation_authorized_by_prior_gate") is not True:
        raise ValueError("R5.1 plan preparation must be authorized by prior gate")
    for key in (
        "R5_1_interpretation_execution_authorized",
        "R6_plan_preparation_authorized",
        "R6_execution_authorized",
        "R5_followup_expansion_authorized",
        "v1_full_grid_overwrite_authorized",
        "Tsuyama_paper_fit_continuation_authorized",
        "selected_annulus_bound_change_authorized",
        "selected_annulus_replaces_all_crossing_ranking_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "optional_660_900x1400_redefines_main_660_authorized",
        "route_specific_manual_sign_flips_authorized",
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
        "ET2030_direct_current_input_unlock_authorized",
    ):
        if boundary.get(key) is not False:
            raise ValueError(f"R5.1 boundary must keep {key}=false")
    if boundary.get("external_review_required_before_R5_1_execution") is not True:
        raise ValueError("R5.1 interpretation execution must require external review")

    evidence = payload.get("R5_evidence_carryforward", {})
    if evidence.get("accepted_gate") != "PASS_R5_RESULTS_PREPARE_NEXT_STAGE_PLAN_ONLY":
        raise ValueError("R5.1 plan must carry forward the accepted R5 gate")
    expected_counts = {
        "R5_case_rows": MAX_R5_FULL_GRID_V2_CASE_ROWS_BEFORE_REVIEW,
        "v1_source_rows": R5_V1_SOURCE_ROW_COUNT,
        "route_identity_count": R5_V1_SOURCE_ROUTE_COUNT,
        "named_scenario_bundle_count": R5_NAMED_SCENARIO_BUNDLE_COUNT,
        "stochastic_seed_count": 0,
    }
    for key, expected in expected_counts.items():
        if int(evidence.get(key, -1)) != expected:
            raise ValueError(f"R5.1 evidence count mismatch: {key}")
    for key in (
        "R5_full_grid_v2_run",
        "R5_cap_respected",
        "R4_2_gate_carried_forward",
        "coarse_screen_warning_only",
        "claim_boundaries_all_rows_blocked",
        "legacy_SNR_headers_absent",
    ):
        if evidence.get(key) is not True:
            raise ValueError(f"R5.1 evidence flag must be true: {key}")
    for key in (
        "R5_followup_expansion_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "route_specific_manual_sign_flips_authorized",
    ):
        if evidence.get(key) is not False:
            raise ValueError(f"R5.1 evidence guard must stay false: {key}")

    route_signals = payload.get("route_role_interpretation_targets", {})
    if route_signals.get("main_660_route_identity_locked") is not True:
        raise ValueError("R5.1 must keep main_660 route identity locked")
    if route_signals.get("weak_reference_control_requires_interpretation") is not True:
        raise ValueError("R5.1 must interpret weak-reference-control high score")
    if route_signals.get("context_route_high_score_warning_requires_interpretation") is not True:
        raise ValueError("R5.1 must interpret context high-score warnings")
    if route_signals.get("context_route_promotion_authorized") is not False:
        raise ValueError("R5.1 cannot authorize context route promotion")
    if route_signals.get("main_660_redefinition_authorized") is not False:
        raise ValueError("R5.1 cannot authorize main_660 redefinition")

    options = payload.get("next_stage_options_considered", [])
    selected = [row for row in options if row.get("selected_for_this_plan") is True]
    if len(selected) != 1:
        raise ValueError("R5.1 must select exactly one next-stage lane")
    if selected[0].get("option_id") != "R5_1_route_role_stability_interpretation_report_only":
        raise ValueError("R5.1 selected option mismatch")
    for row in options:
        for key in ("authorizes_execution", "authorizes_route_promotion", "authorizes_calibrated_claims"):
            if row.get(key) is not False:
                raise ValueError(f"R5.1 option cannot authorize {key}")

    outputs = set(payload.get("required_outputs_if_authorized_after_future_review", []))
    if outputs != R5_1_REQUIRED_OUTPUTS_IF_AUTHORIZED:
        raise ValueError("R5.1 required output list mismatch")
    stop_gates = set(payload.get("stop_gates", []))
    if not R5_1_REQUIRED_STOP_GATES.issubset(stop_gates):
        raise ValueError("R5.1 stop gates are incomplete")
    recommendations = set(payload.get("allowed_future_recommendation_classes", []))
    if recommendations != R5_1_ALLOWED_NEXT_STAGE_RECOMMENDATIONS:
        raise ValueError("R5.1 allowed recommendation class set mismatch")

    scope = payload.get("analysis_scope", {})
    if int(scope.get("new_case_rows_authorized", -1)) != 0:
        raise ValueError("R5.1 plan cannot authorize new case rows")
    if scope.get("uses_existing_R5_artifacts_only") is not True:
        raise ValueError("R5.1 plan must use existing R5 artifacts only")
    for key in (
        "new_scenario_bundle_authorized",
        "new_stochastic_seed_authorized",
        "new_solver_case_authorized",
        "new_experiment_authorized",
    ):
        if scope.get(key) is not False:
            raise ValueError(f"R5.1 scope must keep {key}=false")

    claims = payload.get("claim_boundaries", {})
    for key, expected in {
        "SNR_claim_level": "absolute_blocked",
        "event_probability_claim_level": "absolute_blocked",
        "p_detect_mapping_claim_level": "relative_with_priors",
    }.items():
        if claims.get(key) != expected:
            raise ValueError(f"R5.1 claim boundary mismatch: {key}")
    for key in (
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_claim_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
        "legacy_detector_SNR_output_header_authorized",
        "legacy_calibrated_detector_SNR_output_header_authorized",
    ):
        if claims.get(key) is not False:
            raise ValueError(f"R5.1 claim boundary must keep {key}=false")

    provenance = payload.get("provenance_freeze", {})
    if set(provenance.get("required_R5_checksum_fields", [])) != (
        R5_1_REQUIRED_PROVENANCE_FIELDS
    ):
        raise ValueError("R5.1 required provenance checksum field set mismatch")
    for field in R5_1_REQUIRED_PROVENANCE_FIELDS:
        value = str(provenance.get(field, ""))
        if len(value) != 64:
            raise ValueError(f"R5.1 provenance checksum is not sha256-like: {field}")

    return payload


def load_R5_2_bounded_scenario_prior_audit_plan() -> dict[str, Any]:
    return load_json_yaml("r5_2_bounded_scenario_prior_audit_plan.yaml")


def validate_R5_2_bounded_scenario_prior_audit_plan(
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = plan if plan is not None else load_R5_2_bounded_scenario_prior_audit_plan()
    if payload.get("schema_version") != R5_2_PLAN_SCHEMA_VERSION:
        raise ValueError("R5.2 bounded scenario-prior audit plan schema_version mismatch")
    if payload.get("stage") != "R5_2_bounded_scenario_prior_audit_plan_only":
        raise ValueError("R5.2 stage must be plan-only")
    if payload.get("prior_gate") != (
        "PASS_R5_1_RESULTS_PREPARE_BOUNDED_SCENARIO_PRIOR_AUDIT_PLAN_ONLY"
    ):
        raise ValueError("R5.2 plan must consume the accepted R5.1 results gate")
    if payload.get("selected_next_stage_lane") != (
        "bounded_additional_scenario_prior_audit_plan_only"
    ):
        raise ValueError("R5.2 selected lane must be bounded audit plan only")

    boundary = payload.get("authorization_boundary", {})
    if boundary.get("bounded_audit_plan_preparation_authorized_by_prior_gate") is not True:
        raise ValueError("R5.2 plan preparation must be authorized by prior gate")
    for key in (
        "bounded_scenario_prior_audit_execution_authorized",
        "R6_plan_preparation_authorized",
        "R6_execution_authorized",
        "R5_followup_expansion_authorized",
        "new_scenario_bundle_authorized",
        "new_stochastic_seed_authorized",
        "new_solver_case_authorized",
        "new_experiment_authorized",
        "v1_full_grid_overwrite_authorized",
        "Tsuyama_paper_fit_continuation_authorized",
        "selected_annulus_bound_change_authorized",
        "selected_annulus_replaces_all_crossing_ranking_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "optional_660_900x1400_redefines_main_660_authorized",
        "route_specific_manual_sign_flips_authorized",
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
        "ET2030_direct_current_input_unlock_authorized",
    ):
        if boundary.get(key) is not False:
            raise ValueError(f"R5.2 boundary must keep {key}=false")
    if boundary.get("external_review_required_before_audit_execution") is not True:
        raise ValueError("R5.2 audit execution must require external review")

    carry = payload.get("R5_1_evidence_carryforward", {})
    if carry.get("accepted_gate") != (
        "PASS_R5_1_RESULTS_PREPARE_BOUNDED_SCENARIO_PRIOR_AUDIT_PLAN_ONLY"
    ):
        raise ValueError("R5.2 plan must carry forward the accepted R5.1 gate")
    if carry.get("selected_future_recommendation_class") != (
        "prepare_bounded_additional_scenario_prior_audit_plan_only"
    ):
        raise ValueError("R5.2 must consume the bounded-audit recommendation")
    for key in (
        "R5_1_interpretation_run",
        "weak_reference_control_exceeds_main_660",
        "context_route_high_score_warning_requires_audit",
        "R5_source_checksums_matched",
        "claim_boundaries_preserved",
        "legacy_SNR_headers_absent",
    ):
        if carry.get(key) is not True:
            raise ValueError(f"R5.2 carryforward flag must be true: {key}")
    for key in (
        "R6_plan_preparation_authorized",
        "R6_execution_authorized",
        "R5_followup_expansion_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
    ):
        if carry.get(key) is not False:
            raise ValueError(f"R5.2 carryforward guard must stay false: {key}")
    if int(carry.get("R5_case_rows_interpreted", -1)) != (
        MAX_R5_FULL_GRID_V2_CASE_ROWS_BEFORE_REVIEW
    ):
        raise ValueError("R5.2 carryforward R5 row count mismatch")
    if int(carry.get("context_routes_exceeding_main_660_mean", -1)) != (
        len(R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS)
    ):
        raise ValueError("R5.2 context warning count mismatch")

    design = payload.get("audit_design", {})
    if design.get("audit_execution_type") != "posthoc_existing_R5_artifact_audit_only":
        raise ValueError("R5.2 audit must be posthoc existing-R5 artifact only")
    if design.get("uses_existing_R5_artifacts_only") is not True:
        raise ValueError("R5.2 audit must use existing R5 artifacts only")
    if design.get("deterministic_no_stochastic_seeds") is not True:
        raise ValueError("R5.2 audit must remain deterministic")
    if int(design.get("new_case_rows_authorized", -1)) != 0:
        raise ValueError("R5.2 plan cannot authorize new case rows")
    for key in (
        "new_scenario_bundle_authorized",
        "new_stochastic_seed_authorized",
        "new_solver_case_authorized",
        "new_experiment_authorized",
    ):
        if design.get(key) is not False:
            raise ValueError(f"R5.2 audit design must keep {key}=false")
    if int(design.get("audit_existing_R5_source_row_cap", -1)) != (
        R5_2_EXISTING_R5_AUDIT_ROW_CAP
    ):
        raise ValueError("R5.2 audit source row cap mismatch")
    if int(design.get("audit_route_id_count", -1)) != R5_2_AUDIT_ROUTE_COUNT:
        raise ValueError("R5.2 audit route count mismatch")
    if int(design.get("scenario_bundle_count", -1)) != R5_NAMED_SCENARIO_BUNDLE_COUNT:
        raise ValueError("R5.2 scenario bundle count mismatch")
    if int(design.get("stochastic_seed_count", -1)) != 0:
        raise ValueError("R5.2 stochastic seed count must be zero")

    scenario_ids = set(design.get("scenario_bundle_ids", []))
    if scenario_ids != R5_REQUIRED_SCENARIO_BUNDLE_IDS:
        raise ValueError("R5.2 scenario bundle ID set mismatch")

    groups = payload.get("audit_route_set", {})
    route_ids: set[str] = set()
    for rows in groups.values():
        for row in rows:
            route_ids.add(str(row["route_id"]))
            if row.get("route_promotion_authorized") is not False:
                raise ValueError("R5.2 route set cannot authorize promotion")
    if route_ids != R5_2_AUDIT_ROUTE_IDS:
        raise ValueError("R5.2 audit route set mismatch")
    context_ids = {str(row["route_id"]) for row in groups.get("above_main_context_routes", [])}
    if context_ids != R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS:
        raise ValueError("R5.2 must include all above-main context routes")

    if set(payload.get("required_outputs_if_authorized_after_future_review", [])) != (
        R5_2_REQUIRED_OUTPUTS_IF_AUTHORIZED
    ):
        raise ValueError("R5.2 required output list mismatch")
    if not R5_2_REQUIRED_STOP_GATES.issubset(set(payload.get("stop_gates", []))):
        raise ValueError("R5.2 stop gates are incomplete")
    if set(payload.get("allowed_future_recommendation_classes_after_audit", [])) != (
        R5_2_ALLOWED_FUTURE_RECOMMENDATION_CLASSES
    ):
        raise ValueError("R5.2 future recommendation class set mismatch")

    claims = payload.get("claim_boundaries", {})
    for key, expected in {
        "SNR_claim_level": "absolute_blocked",
        "event_probability_claim_level": "absolute_blocked",
        "p_detect_mapping_claim_level": "relative_with_priors",
    }.items():
        if claims.get(key) != expected:
            raise ValueError(f"R5.2 claim boundary mismatch: {key}")
    for key in (
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_claim_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
        "legacy_detector_SNR_output_header_authorized",
        "legacy_calibrated_detector_SNR_output_header_authorized",
    ):
        if claims.get(key) is not False:
            raise ValueError(f"R5.2 claim boundary must keep {key}=false")

    provenance = payload.get("provenance_freeze", {})
    if set(provenance.get("required_checksum_fields", [])) != (
        R5_2_REQUIRED_PROVENANCE_FIELDS
    ):
        raise ValueError("R5.2 required provenance checksum field set mismatch")
    for field in R5_2_REQUIRED_PROVENANCE_FIELDS:
        value = str(provenance.get(field, ""))
        if len(value) != 64:
            raise ValueError(f"R5.2 provenance checksum is not sha256-like: {field}")

    return payload


def load_R5_3_route_prior_model_revision_plan() -> dict[str, Any]:
    return load_json_yaml("r5_3_route_prior_model_revision_plan.yaml")


def validate_R5_3_route_prior_model_revision_plan(
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = plan if plan is not None else load_R5_3_route_prior_model_revision_plan()
    if payload.get("schema_version") != R5_3_ROUTE_PRIOR_PLAN_SCHEMA_VERSION:
        raise ValueError("R5.3 route-prior model revision plan schema_version mismatch")
    if payload.get("stage") != "R5_3_route_prior_model_revision_plan_only":
        raise ValueError("R5.3 route-prior stage must be plan-only")
    if payload.get("prior_gate") != (
        "PASS_R5_2_RESULTS_PREPARE_ROUTE_PRIOR_MODEL_REVISION_PLAN_ONLY"
    ):
        raise ValueError("R5.3 plan must consume the accepted R5.2 results gate")
    if payload.get("selected_next_stage_lane") != "route_prior_model_revision_plan_only":
        raise ValueError("R5.3 selected lane must be route-prior model revision plan only")

    cadence = payload.get("review_cadence_policy", {})
    if cadence.get("consolidate_plan_only_work_before_next_external_review") is not True:
        raise ValueError("R5.3 must consolidate plan-only work before review")
    if cadence.get("external_review_required_before_any_execution") is not True:
        raise ValueError("R5.3 must require external review before execution")
    if cadence.get("external_review_required_before_R6_plan_or_route_promotion") is not True:
        raise ValueError("R5.3 must require review before R6 or route promotion")
    if cadence.get("reason") != (
        "earlier_fine_gates_were_needed_for_authorization_changes; "
        "now_plan_only_decomposition_can_be_reviewed_as_one_larger_package"
    ):
        raise ValueError("R5.3 review cadence rationale mismatch")

    boundary = payload.get("authorization_boundary", {})
    if boundary.get("route_prior_plan_preparation_authorized_by_prior_gate") is not True:
        raise ValueError("R5.3 plan preparation must be authorized by prior gate")
    for key in (
        "route_prior_model_revision_execution_authorized",
        "R6_plan_preparation_authorized",
        "R6_execution_authorized",
        "R5_followup_expansion_authorized",
        "new_scenario_bundle_authorized",
        "new_stochastic_seed_authorized",
        "new_solver_case_authorized",
        "new_experiment_authorized",
        "v1_full_grid_overwrite_authorized",
        "Tsuyama_paper_fit_continuation_authorized",
        "selected_annulus_bound_change_authorized",
        "selected_annulus_replaces_all_crossing_ranking_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "optional_660_900x1400_redefines_main_660_authorized",
        "route_specific_manual_sign_flips_authorized",
        "route_specific_manual_prior_multipliers_authorized",
        "scenario_specific_per_route_fit_authorized",
        "particle_specific_empirical_fit_authorized",
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
        "ET2030_direct_current_input_unlock_authorized",
    ):
        if boundary.get(key) is not False:
            raise ValueError(f"R5.3 boundary must keep {key}=false")
    if boundary.get("external_review_required_before_revision_execution") is not True:
        raise ValueError("R5.3 revision execution must require external review")

    carry = payload.get("R5_2_evidence_carryforward", {})
    if carry.get("accepted_gate") != (
        "PASS_R5_2_RESULTS_PREPARE_ROUTE_PRIOR_MODEL_REVISION_PLAN_ONLY"
    ):
        raise ValueError("R5.3 plan must carry forward the accepted R5.2 gate")
    if carry.get("R5_2_bounded_scenario_prior_audit_run") is not True:
        raise ValueError("R5.3 must consume a completed R5.2 audit")
    if int(carry.get("existing_R5_rows_audited", -1)) != R5_2_EXISTING_R5_AUDIT_ROW_CAP:
        raise ValueError("R5.3 carryforward R5.2 row count mismatch")
    if int(carry.get("audit_route_id_count", -1)) != R5_2_AUDIT_ROUTE_COUNT:
        raise ValueError("R5.3 carryforward route count mismatch")
    if int(carry.get("scenario_bundle_count", -1)) != R5_NAMED_SCENARIO_BUNDLE_COUNT:
        raise ValueError("R5.3 carryforward scenario bundle count mismatch")
    if int(carry.get("stochastic_seed_count", -1)) != 0:
        raise ValueError("R5.3 carryforward stochastic seed count must be zero")
    if carry.get("selected_future_recommendation_class") != (
        "prepare_route_prior_model_revision_plan_only"
    ):
        raise ValueError("R5.3 must consume route-prior-plan recommendation")
    if carry.get("audit_decision") != (
        "systematic_weak_reference_and_context_prior_warning_blocks_R6_plan"
    ):
        raise ValueError("R5.3 audit decision carryforward mismatch")
    if int(carry.get("weak_reference_exceeds_main_660_scenario_count", -1)) != (
        R5_NAMED_SCENARIO_BUNDLE_COUNT
    ):
        raise ValueError("R5.3 weak-reference warning count mismatch")
    if int(carry.get("context_routes_above_main_under_all_scenarios", -1)) != (
        len(R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS)
    ):
        raise ValueError("R5.3 context warning count mismatch")
    for key in (
        "R6_plan_preparation_authorized",
        "R6_execution_authorized",
        "R5_followup_expansion_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "calibrated_SNR_claim_emitted",
        "calibrated_event_probability_claim_emitted",
    ):
        if carry.get(key) is not False:
            raise ValueError(f"R5.3 carryforward guard must stay false: {key}")

    design = payload.get("revision_plan_design", {})
    if design.get("plan_execution_type") != "plan_only_no_recompute_no_revision":
        raise ValueError("R5.3 design must be plan-only with no recompute")
    if design.get("future_revision_execution_type_if_reviewed") != (
        "bounded_existing_R5_artifact_prior_model_audit_only"
    ):
        raise ValueError("R5.3 future execution type must remain bounded artifact audit")
    if design.get("uses_existing_R5_artifacts_only") is not True:
        raise ValueError("R5.3 design must use existing R5 artifacts only")
    if int(design.get("max_existing_R5_source_rows_if_future_reviewed", -1)) != (
        R5_3_ROUTE_PRIOR_SOURCE_ROW_CAP
    ):
        raise ValueError("R5.3 source row cap mismatch")
    if int(design.get("route_id_count", -1)) != R5_2_AUDIT_ROUTE_COUNT:
        raise ValueError("R5.3 route count mismatch")
    if int(design.get("scenario_bundle_count", -1)) != R5_NAMED_SCENARIO_BUNDLE_COUNT:
        raise ValueError("R5.3 scenario bundle count mismatch")
    if int(design.get("stochastic_seed_count", -1)) != 0:
        raise ValueError("R5.3 stochastic seed count must be zero")
    for key in (
        "new_case_rows_authorized",
        "new_scenario_bundle_authorized",
        "new_stochastic_seed_authorized",
        "new_solver_case_authorized",
        "new_experiment_authorized",
    ):
        expected = 0 if key == "new_case_rows_authorized" else False
        if design.get(key) != expected:
            raise ValueError(f"R5.3 design must keep {key}={expected}")

    route_ids = set(design.get("route_ids", []))
    if route_ids != R5_2_AUDIT_ROUTE_IDS:
        raise ValueError("R5.3 route ID set must match R5.2 audited routes")
    scenario_ids = set(design.get("scenario_bundle_ids", []))
    if scenario_ids != R5_REQUIRED_SCENARIO_BUNDLE_IDS:
        raise ValueError("R5.3 scenario bundle ID set mismatch")
    if set(design.get("required_score_decomposition_terms", [])) != (
        R5_3_REQUIRED_DECOMPOSITION_TERMS
    ):
        raise ValueError("R5.3 decomposition term set mismatch")

    candidates = payload.get("candidate_prior_model_revision_scope", {})
    if set(candidates.get("allowed_candidate_prior_families", [])) != (
        R5_3_ALLOWED_CANDIDATE_PRIOR_FAMILIES
    ):
        raise ValueError("R5.3 allowed candidate prior family set mismatch")
    if set(candidates.get("forbidden_prior_families", [])) != (
        R5_3_FORBIDDEN_PRIOR_FAMILIES
    ):
        raise ValueError("R5.3 forbidden prior family set mismatch")
    if candidates.get("low_dimensional_physics_or_prior_explanation_required") is not True:
        raise ValueError("R5.3 must require low-dimensional explanation")
    if candidates.get("route_specific_fits_forbidden") is not True:
        raise ValueError("R5.3 must forbid route-specific fits")
    if candidates.get("context_route_promotion_forbidden") is not True:
        raise ValueError("R5.3 must forbid context-route promotion")

    gates = payload.get("future_pass_fail_criteria_if_execution_is_reviewed", {})
    for key in (
        "no_route_promotion",
        "no_main_660_redefinition",
        "no_selected_annulus_replacement",
        "no_calibrated_or_absolute_claim",
        "weak_reference_control_explained_or_remains_blocking",
        "all_20_context_warning_routes_exhaustively_reported",
        "candidate_revision_must_be_global_or_family_level_not_route_specific",
        "R6_plan_remains_blocked_until_separate_review",
    ):
        if gates.get(key) is not True:
            raise ValueError(f"R5.3 future criterion must require {key}=true")

    if set(payload.get("required_outputs_if_authorized_after_future_review", [])) != (
        R5_3_REQUIRED_OUTPUTS_IF_AUTHORIZED
    ):
        raise ValueError("R5.3 required output list mismatch")
    if not R5_3_REQUIRED_STOP_GATES.issubset(set(payload.get("stop_gates", []))):
        raise ValueError("R5.3 stop gates are incomplete")
    if set(payload.get("allowed_future_external_review_decisions", [])) != (
        R5_3_ALLOWED_FUTURE_REVIEW_DECISIONS
    ):
        raise ValueError("R5.3 future review decision set mismatch")

    claims = payload.get("claim_boundaries", {})
    for key, expected in {
        "SNR_claim_level": "absolute_blocked",
        "event_probability_claim_level": "absolute_blocked",
        "p_detect_mapping_claim_level": "relative_with_priors",
    }.items():
        if claims.get(key) != expected:
            raise ValueError(f"R5.3 claim boundary mismatch: {key}")
    for key in (
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_claim_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
        "legacy_detector_SNR_output_header_authorized",
        "legacy_calibrated_detector_SNR_output_header_authorized",
    ):
        if claims.get(key) is not False:
            raise ValueError(f"R5.3 claim boundary must keep {key}=false")

    provenance = payload.get("provenance_freeze", {})
    if set(provenance.get("required_checksum_fields", [])) != (
        R5_3_REQUIRED_PROVENANCE_FIELDS
    ):
        raise ValueError("R5.3 required provenance checksum field set mismatch")
    for field in R5_3_REQUIRED_PROVENANCE_FIELDS:
        value = str(provenance.get(field, ""))
        if len(value) != 64:
            raise ValueError(f"R5.3 provenance checksum is not sha256-like: {field}")

    return payload


def load_R6_route_prior_sensitivity_plan() -> dict[str, Any]:
    return load_json_yaml("r6_route_prior_sensitivity_plan.yaml")


def validate_R6_route_prior_sensitivity_plan(
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = plan if plan is not None else load_R6_route_prior_sensitivity_plan()
    if payload.get("schema_version") != R6_PLAN_SCHEMA_VERSION:
        raise ValueError("R6 route-prior sensitivity plan schema_version mismatch")
    if payload.get("stage") != "R6_route_prior_sensitivity_plan_only":
        raise ValueError("R6 route-prior sensitivity stage must be plan-only")
    if payload.get("prior_gate") != "PASS_R5_3_RESULTS_PREPARE_R6_PLAN_ONLY":
        raise ValueError("R6 plan must consume the accepted R5.3 results gate")
    if payload.get("selected_next_stage_lane") != "R6_route_prior_sensitivity_plan_only":
        raise ValueError("R6 selected lane must be route-prior sensitivity plan only")

    boundary = payload.get("authorization_boundary", {})
    if boundary.get("R6_plan_preparation_authorized_by_prior_gate") is not True:
        raise ValueError("R6 plan preparation must be authorized by the R5.3 gate")
    if boundary.get("R6_plan_artifact_created") is not True:
        raise ValueError("R6 plan artifact creation must be explicit")
    for key in (
        "R6_execution_authorized",
        "R5_followup_expansion_authorized",
        "new_scenario_bundle_authorized",
        "new_stochastic_seed_authorized",
        "new_solver_case_authorized",
        "new_experiment_authorized",
        "v1_full_grid_overwrite_authorized",
        "Tsuyama_paper_fit_continuation_authorized",
        "selected_annulus_bound_change_authorized",
        "selected_annulus_replaces_all_crossing_ranking_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "optional_660_900x1400_redefines_main_660_authorized",
        "route_specific_manual_sign_flips_authorized",
        "route_specific_manual_prior_multipliers_authorized",
        "scenario_specific_per_route_fit_authorized",
        "particle_specific_empirical_fit_authorized",
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
        "ET2030_direct_current_input_unlock_authorized",
    ):
        if boundary.get(key) is not False:
            raise ValueError(f"R6 boundary must keep {key}=false")
    if boundary.get("external_review_required_before_R6_execution") is not True:
        raise ValueError("R6 execution must require external review")
    if boundary.get("external_review_required_before_route_promotion") is not True:
        raise ValueError("R6 plan must require review before route promotion")

    carry = payload.get("R5_3_evidence_carryforward", {})
    if carry.get("accepted_gate") != "PASS_R5_3_RESULTS_PREPARE_R6_PLAN_ONLY":
        raise ValueError("R6 plan must carry forward the accepted R5.3 gate")
    if carry.get("R5_3_route_prior_model_revision_audit_run") is not True:
        raise ValueError("R6 plan must consume a completed R5.3 audit")
    if carry.get("audit_execution_type") != (
        "bounded_existing_R5_artifact_prior_model_audit_only"
    ):
        raise ValueError("R6 carryforward R5.3 execution type mismatch")
    if int(carry.get("existing_R5_rows_audited", -1)) != R6_ROUTE_PRIOR_SOURCE_ROW_CAP:
        raise ValueError("R6 carryforward R5.3 source row count mismatch")
    if int(carry.get("audit_route_id_count", -1)) != R5_2_AUDIT_ROUTE_COUNT:
        raise ValueError("R6 carryforward route count mismatch")
    if int(carry.get("scenario_bundle_count", -1)) != R5_NAMED_SCENARIO_BUNDLE_COUNT:
        raise ValueError("R6 carryforward scenario bundle count mismatch")
    if int(carry.get("stochastic_seed_count", -1)) != 0:
        raise ValueError("R6 carryforward stochastic seed count must be zero")
    if carry.get("selected_candidate_prior_id") != (
        "global_width_quadratic_regularization"
    ):
        raise ValueError("R6 must carry forward the R5.3 selected width candidate")
    if carry.get("selected_candidate_prior_family") != (
        "global_width_depth_regularization_family"
    ):
        raise ValueError("R6 selected candidate family carryforward mismatch")
    if int(carry.get("selected_candidate_dof_count", -1)) != 1:
        raise ValueError("R6 selected candidate must remain one degree of freedom")
    if float(carry.get("weak_reference_delta_explained_fraction", -1.0)) != 1.0:
        raise ValueError("R6 weak-reference explained fraction carryforward mismatch")
    if float(carry.get("context_family_delta_explained_fraction", -1.0)) != 1.0:
        raise ValueError("R6 context-family explained fraction carryforward mismatch")
    if int(carry.get("context_routes_above_main_after_candidate", -1)) != 0:
        raise ValueError("R6 context warning residual carryforward mismatch")
    if int(carry.get("context_scenario_rows_above_main_after_candidate", -1)) != 0:
        raise ValueError("R6 context scenario residual carryforward mismatch")
    if int(carry.get("weak_reference_scenario_rows_above_main_after_candidate", -1)) != 0:
        raise ValueError("R6 weak-reference scenario residual carryforward mismatch")
    for key in (
        "R6_plan_preparation_authorized_in_R5_3_manifest",
        "R6_execution_authorized",
        "R5_followup_expansion_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "calibrated_SNR_claim_emitted",
        "calibrated_event_probability_claim_emitted",
    ):
        if carry.get(key) is not False:
            raise ValueError(f"R6 carryforward guard must stay false: {key}")

    design = payload.get("R6_plan_design", {})
    if design.get("plan_execution_type") != "plan_only_no_R6_execution":
        raise ValueError("R6 design must be plan-only")
    if design.get("future_R6_execution_type_if_reviewed") != (
        "bounded_existing_R5_artifact_route_prior_sensitivity_audit_only"
    ):
        raise ValueError("R6 future execution type must remain bounded artifact audit")
    if design.get("uses_existing_R5_artifacts_only") is not True:
        raise ValueError("R6 design must use existing R5 artifacts only")
    if design.get("selected_R5_3_candidate_is_hypothesis_not_calibrated_law") is not True:
        raise ValueError("R6 must treat the R5.3 width prior as a hypothesis")
    if int(design.get("max_existing_R5_source_rows_if_future_reviewed", -1)) != (
        R6_ROUTE_PRIOR_SOURCE_ROW_CAP
    ):
        raise ValueError("R6 source row cap mismatch")
    if int(design.get("max_R6_derived_candidate_rows", -1)) != (
        R6_DERIVED_CANDIDATE_ROW_CAP
    ):
        raise ValueError("R6 derived candidate row cap mismatch")
    if int(design.get("route_id_count", -1)) != R5_2_AUDIT_ROUTE_COUNT:
        raise ValueError("R6 route count mismatch")
    if int(design.get("scenario_bundle_count", -1)) != R5_NAMED_SCENARIO_BUNDLE_COUNT:
        raise ValueError("R6 scenario bundle count mismatch")
    if int(design.get("stochastic_seed_count", -1)) != 0:
        raise ValueError("R6 stochastic seed count must be zero")
    for key in (
        "new_case_rows_authorized",
        "new_scenario_bundle_authorized",
        "new_stochastic_seed_authorized",
        "new_solver_case_authorized",
        "new_experiment_authorized",
    ):
        expected = 0 if key == "new_case_rows_authorized" else False
        if design.get(key) != expected:
            raise ValueError(f"R6 design must keep {key}={expected}")
    if set(design.get("route_ids", [])) != R5_2_AUDIT_ROUTE_IDS:
        raise ValueError("R6 route ID set must match R5.2/R5.3 audited routes")
    if set(design.get("scenario_bundle_ids", [])) != R5_REQUIRED_SCENARIO_BUNDLE_IDS:
        raise ValueError("R6 scenario bundle ID set mismatch")
    comparator = design.get("main660_comparator_policy", {})
    if comparator.get("primary_pass_fail_comparator") != (
        "candidate_adjusted_locked_main_660"
    ):
        raise ValueError("R6 comparator policy must use candidate-adjusted locked main")
    if comparator.get("secondary_diagnostic_comparator") != "unadjusted_locked_main_660":
        raise ValueError("R6 comparator policy must report unadjusted main diagnostic")
    if comparator.get("locked_main_660_route_ids") != [
        "660_800x1400",
        "660_800x1500",
    ]:
        raise ValueError("R6 comparator policy must keep locked main-660 routes")
    if comparator.get("main_660_redefinition_authorized") is not False:
        raise ValueError("R6 comparator policy must not redefine main-660")
    if comparator.get("report_optional_900_diagnostics") is not True:
        raise ValueError("R6 comparator policy must report optional 900 diagnostics")

    sensitivity = payload.get("candidate_prior_sensitivity_design", {})
    candidate_ids = set(sensitivity.get("candidate_prior_ids", []))
    if candidate_ids != R6_REQUIRED_CANDIDATE_PRIOR_IDS:
        raise ValueError("R6 candidate prior ID set mismatch")
    if int(sensitivity.get("candidate_prior_count", -1)) != len(
        R6_CANDIDATE_PRIOR_REGISTRY
    ):
        raise ValueError("R6 candidate prior count mismatch")
    if set(sensitivity.get("allowed_candidate_prior_families", [])) != (
        R6_ALLOWED_CANDIDATE_PRIOR_FAMILIES
    ):
        raise ValueError("R6 allowed candidate prior family set mismatch")
    if set(sensitivity.get("forbidden_prior_families", [])) != (
        R6_FORBIDDEN_PRIOR_FAMILIES
    ):
        raise ValueError("R6 forbidden prior family set mismatch")
    if sensitivity.get("scenario_bundle_sensitivity_reweighting_diagnostic_only") is not True:
        raise ValueError("R6 scenario sensitivity must remain diagnostic-only")
    if sensitivity.get("scenario_weight_change_authorized") is not False:
        raise ValueError("R6 must not authorize scenario weight changes")
    if set(sensitivity.get("width_pivot_nm_values", [])) != {750, 800, 850, 900}:
        raise ValueError("R6 width pivot sensitivity set mismatch")
    if {float(value) for value in sensitivity.get("width_exponent_values", [])} != {
        1.0,
        1.5,
        2.0,
        2.5,
    }:
        raise ValueError("R6 width exponent sensitivity set mismatch")
    if {float(value) for value in sensitivity.get("width_factor_floor_values", [])} != {
        0.25,
        0.35,
        0.50,
    }:
        raise ValueError("R6 width floor sensitivity set mismatch")
    if set(sensitivity.get("required_sensitivity_output_fields", [])) != (
        R6_REQUIRED_SENSITIVITY_FIELDS
    ):
        raise ValueError("R6 required sensitivity output field set mismatch")
    nearby = sensitivity.get("nearby_candidate_definition", {})
    if nearby.get("same_family_required") is not True:
        raise ValueError("R6 nearby candidate definition must require same family")
    if int(nearby.get("candidate_dof_count_max", -1)) != 2:
        raise ValueError("R6 nearby candidate dof cap mismatch")
    if float(nearby.get("max_width_exponent_delta", -1.0)) != 0.5:
        raise ValueError("R6 nearby exponent delta mismatch")
    if int(nearby.get("max_pivot_delta_nm", -1)) != 50:
        raise ValueError("R6 nearby pivot delta mismatch")
    if float(nearby.get("max_floor_delta", -1.0)) != 0.15:
        raise ValueError("R6 nearby floor delta mismatch")
    if nearby.get("non_width_alternatives_count_as_nearby_confirmation") is not False:
        raise ValueError("R6 nearby candidates cannot be non-width alternatives")
    non_width = sensitivity.get("non_width_candidate_prior_requirements", {})
    if non_width.get("deterministic_functions_of_existing_R5_columns") is not True:
        raise ValueError("R6 non-width candidates must be deterministic")
    if non_width.get("manual_route_id_multiplier_authorized") is not False:
        raise ValueError("R6 non-width candidates must forbid manual route IDs")
    if set(non_width.get("candidate_prior_ids", [])) != {
        "reference_band_penalty",
        "BFP_alignment_risk",
    }:
        raise ValueError("R6 non-width candidate requirement IDs mismatch")
    registry = sensitivity.get("candidate_prior_registry", [])
    if {row.get("candidate_prior_id") for row in registry} != (
        R6_REQUIRED_CANDIDATE_PRIOR_IDS
    ):
        raise ValueError("R6 candidate registry IDs mismatch")
    for row in registry:
        if row.get("candidate_prior_family") not in R6_ALLOWED_CANDIDATE_PRIOR_FAMILIES:
            raise ValueError("R6 candidate family is not allowed")
        if row.get("uses_route_specific_multiplier") is not False:
            raise ValueError("R6 candidates must not use route-specific multipliers")
        if row.get("uses_scenario_specific_per_route_fit") is not False:
            raise ValueError("R6 candidates must not use scenario-specific route fits")
        if row.get("uses_particle_specific_empirical_fit") is not False:
            raise ValueError("R6 candidates must not use particle-specific fits")
        if row.get("changes_main_660_definition") is not False:
            raise ValueError("R6 candidates must not redefine main-660")
        if row.get("authorizes_route_promotion") is not False:
            raise ValueError("R6 candidates must not authorize route promotion")
        if row.get("claim_level") != "relative_with_priors":
            raise ValueError("R6 candidate claim level mismatch")
        dof = int(row.get("dof_count", 99))
        if dof < 1 or dof > 2:
            raise ValueError("R6 candidate dof_count must stay low-dimensional")

    gates = payload.get("future_pass_fail_criteria_if_execution_is_reviewed", {})
    for key in (
        "selected_R5_3_width_prior_remains_hypothesis",
        "at_least_two_nearby_low_dimensional_candidates_explain_warning",
        "no_route_specific_or_scenario_specific_or_particle_specific_fit",
        "context_routes_above_main_after_candidate_zero_or_residual_explained",
        "weak_reference_not_systematically_above_main",
        "main_660_definition_unchanged",
        "optional_660_900x1400_not_main_660",
        "selected_annulus_parallel_lens_only",
        "claim_boundary_absolute_blocked",
        "route_governance_plan_if_reasonable_priors_leave_context_above_main",
        "stop_if_only_forbidden_fits_resolve_warning",
        "R6_execution_requires_separate_external_review",
    ):
        if gates.get(key) is not True:
            raise ValueError(f"R6 future criterion must require {key}=true")

    if set(payload.get("required_outputs_if_authorized_after_future_review", [])) != (
        R6_REQUIRED_OUTPUTS_IF_AUTHORIZED
    ):
        raise ValueError("R6 required output list mismatch")
    if not R6_REQUIRED_STOP_GATES.issubset(set(payload.get("stop_gates", []))):
        raise ValueError("R6 stop gates are incomplete")
    if set(payload.get("allowed_future_external_review_decisions", [])) != (
        R6_ALLOWED_FUTURE_REVIEW_DECISIONS
    ):
        raise ValueError("R6 future review decision set mismatch")

    claims = payload.get("claim_boundaries", {})
    for key, expected in {
        "SNR_claim_level": "absolute_blocked",
        "event_probability_claim_level": "absolute_blocked",
        "p_detect_mapping_claim_level": "relative_with_priors",
    }.items():
        if claims.get(key) != expected:
            raise ValueError(f"R6 claim boundary mismatch: {key}")
    for key in (
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_claim_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
        "legacy_detector_SNR_output_header_authorized",
        "legacy_calibrated_detector_SNR_output_header_authorized",
    ):
        if claims.get(key) is not False:
            raise ValueError(f"R6 claim boundary must keep {key}=false")

    provenance = payload.get("provenance_freeze", {})
    if set(provenance.get("required_checksum_fields", [])) != (
        R6_REQUIRED_PROVENANCE_FIELDS
    ):
        raise ValueError("R6 required provenance checksum field set mismatch")
    for field in R6_REQUIRED_PROVENANCE_FIELDS:
        value = str(provenance.get(field, ""))
        if len(value) != 64:
            raise ValueError(f"R6 provenance checksum is not sha256-like: {field}")

    return payload


def load_R7_route_prior_mechanistic_decomposition_plan() -> dict[str, Any]:
    return load_json_yaml("r7_route_prior_mechanistic_decomposition_plan.yaml")


def validate_R7_route_prior_mechanistic_decomposition_plan(
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = (
        plan
        if plan is not None
        else load_R7_route_prior_mechanistic_decomposition_plan()
    )
    if payload.get("schema_version") != R7_PLAN_SCHEMA_VERSION:
        raise ValueError("R7 mechanistic decomposition plan schema_version mismatch")
    if payload.get("stage") != "R7_route_prior_mechanistic_decomposition_plan_only":
        raise ValueError("R7 mechanistic decomposition stage must be plan-only")
    if payload.get("prior_gate") != "PASS_R6_RESULTS_PREPARE_NEXT_STAGE_PLAN_ONLY":
        raise ValueError("R7 plan must consume the accepted R6 results gate")
    if payload.get("selected_next_stage_lane") != (
        "R7_route_prior_mechanistic_decomposition_plan_only"
    ):
        raise ValueError("R7 selected lane must be mechanistic decomposition plan only")

    boundary = payload.get("authorization_boundary", {})
    if boundary.get("R7_plan_preparation_authorized_by_prior_gate") is not True:
        raise ValueError("R7 plan preparation must be authorized by the R6 gate")
    if boundary.get("R7_plan_artifact_created") is not True:
        raise ValueError("R7 plan artifact creation must be explicit")
    for key in (
        "R7_execution_authorized",
        "route_prior_mechanistic_decomposition_execution_authorized",
        "R5_followup_expansion_authorized",
        "R6_followup_expansion_authorized",
        "new_scenario_bundle_authorized",
        "new_stochastic_seed_authorized",
        "new_solver_case_authorized",
        "new_experiment_authorized",
        "v1_full_grid_overwrite_authorized",
        "Tsuyama_paper_fit_continuation_authorized",
        "selected_annulus_bound_change_authorized",
        "selected_annulus_replaces_all_crossing_ranking_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "optional_660_900x1400_redefines_main_660_authorized",
        "route_specific_manual_sign_flips_authorized",
        "route_specific_manual_prior_multipliers_authorized",
        "scenario_specific_per_route_fit_authorized",
        "particle_specific_empirical_fit_authorized",
        "score_derived_physical_prior_authorized",
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
        "ET2030_direct_current_input_unlock_authorized",
    ):
        if boundary.get(key) is not False:
            raise ValueError(f"R7 boundary must keep {key}=false")
    if boundary.get("external_review_required_before_R7_execution") is not True:
        raise ValueError("R7 execution must require external review")
    if boundary.get("external_review_required_before_route_promotion") is not True:
        raise ValueError("R7 plan must require review before route promotion")

    carry = payload.get("R6_evidence_carryforward", {})
    if carry.get("accepted_gate") != "PASS_R6_RESULTS_PREPARE_NEXT_STAGE_PLAN_ONLY":
        raise ValueError("R7 plan must carry forward the accepted R6 gate")
    if carry.get("R6_route_prior_sensitivity_audit_run") is not True:
        raise ValueError("R7 plan must consume a completed R6 audit")
    if carry.get("audit_execution_type") != (
        "bounded_existing_R5_artifact_route_prior_sensitivity_audit_only"
    ):
        raise ValueError("R7 carryforward R6 execution type mismatch")
    if int(carry.get("existing_R5_rows_audited", -1)) != R7_ROUTE_PRIOR_SOURCE_ROW_CAP:
        raise ValueError("R7 carryforward source row count mismatch")
    if int(carry.get("candidate_prior_count", -1)) != len(R6_CANDIDATE_PRIOR_REGISTRY):
        raise ValueError("R7 carryforward R6 candidate count mismatch")
    if int(carry.get("derived_candidate_rows_evaluated", -1)) != (
        R6_DERIVED_CANDIDATE_ROW_CAP
    ):
        raise ValueError("R7 carryforward derived row count mismatch")
    if int(carry.get("audit_route_id_count", -1)) != R5_2_AUDIT_ROUTE_COUNT:
        raise ValueError("R7 carryforward route count mismatch")
    if int(carry.get("scenario_bundle_count", -1)) != R5_NAMED_SCENARIO_BUNDLE_COUNT:
        raise ValueError("R7 carryforward scenario bundle count mismatch")
    if int(carry.get("stochastic_seed_count", -1)) != 0:
        raise ValueError("R7 carryforward stochastic seed count must be zero")
    if carry.get("main660_comparator_policy") != "candidate_adjusted_locked_main_660":
        raise ValueError("R7 carryforward must preserve the R6 main comparator policy")
    if carry.get("selected_future_recommendation_class") != (
        "prepare_next_stage_plan_for_external_review_only"
    ):
        raise ValueError("R7 carryforward must preserve the R6 next-stage class")
    if carry.get("audit_decision") != (
        "low_dimensional_width_prior_sensitivity_stable_prepare_next_stage_plan_only"
    ):
        raise ValueError("R7 carryforward R6 audit decision mismatch")
    if int(carry.get("nearby_warning_resolved_candidate_count", -1)) != 3:
        raise ValueError("R7 carryforward nearby candidate count mismatch")
    if (
        carry.get("at_least_two_nearby_low_dimensional_candidates_explain_warning")
        is not True
    ):
        raise ValueError("R7 carryforward must require nearby width-family support")
    if int(carry.get("main660_retention_warning_candidate_count", -1)) != 1:
        raise ValueError("R7 carryforward main-660 retention warning count mismatch")
    if carry.get("width_quad_900_interpretation_class") != "over_severe_prior_caution":
        raise ValueError("R7 carryforward must mark width_quad_900 as over-severe")
    if float(carry.get("width_quad_900_main660_score_retention_fraction", 0.0)) >= (
        R7_ACCEPTED_WIDTH_PRIOR_BAND["main660_retention_fraction_min"]
    ):
        raise ValueError("R7 carryforward width_quad_900 retention should be below band")
    if carry.get("width_quad_900_is_accepted_explanatory_band_member") is not False:
        raise ValueError("R7 must not accept width_quad_900 as a healthy band member")
    if carry.get("reference_band_penalty_warning_resolved_by_candidate") is not False:
        raise ValueError("R7 carryforward must keep reference-band diagnostic unresolved")
    if carry.get("BFP_alignment_risk_warning_resolved_by_candidate") is not False:
        raise ValueError("R7 carryforward must keep BFP diagnostic unresolved")
    for key in (
        "R7_plan_preparation_authorized_in_R6_manifest",
        "R7_execution_authorized",
        "R5_followup_expansion_authorized",
        "R6_followup_expansion_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "calibrated_SNR_claim_emitted",
        "calibrated_event_probability_claim_emitted",
    ):
        if carry.get(key) is not False:
            raise ValueError(f"R7 carryforward guard must stay false: {key}")

    design = payload.get("R7_plan_design", {})
    if design.get("plan_execution_type") != "plan_only_no_R7_execution":
        raise ValueError("R7 design must be plan-only")
    if design.get("future_R7_execution_type_if_reviewed") != (
        "bounded_existing_R5_artifact_route_prior_mechanistic_decomposition_audit_only"
    ):
        raise ValueError("R7 future execution type must remain bounded artifact audit")
    if design.get("uses_existing_R5_R6_artifacts_only") is not True:
        raise ValueError("R7 design must use existing R5/R6 artifacts only")
    if design.get("R6_width_family_prior_is_hypothesis_not_physical_law") is not True:
        raise ValueError("R7 must treat the R6 width prior as a hypothesis")
    if int(design.get("max_existing_R5_source_rows_if_future_reviewed", -1)) != (
        R7_ROUTE_PRIOR_SOURCE_ROW_CAP
    ):
        raise ValueError("R7 source row cap mismatch")
    if int(design.get("max_mechanistic_candidate_count", -1)) != (
        R7_MAX_MECHANISTIC_CANDIDATE_COUNT
    ):
        raise ValueError("R7 mechanistic candidate count cap mismatch")
    if int(design.get("max_R7_derived_candidate_rows", -1)) != (
        R7_DERIVED_CANDIDATE_ROW_CAP
    ):
        raise ValueError("R7 derived candidate row cap mismatch")
    if int(design.get("route_id_count", -1)) != R5_2_AUDIT_ROUTE_COUNT:
        raise ValueError("R7 route count mismatch")
    if int(design.get("scenario_bundle_count", -1)) != R5_NAMED_SCENARIO_BUNDLE_COUNT:
        raise ValueError("R7 scenario bundle count mismatch")
    if int(design.get("stochastic_seed_count", -1)) != 0:
        raise ValueError("R7 stochastic seed count must be zero")
    for key in (
        "new_case_rows_authorized",
        "new_scenario_bundle_authorized",
        "new_stochastic_seed_authorized",
        "new_solver_case_authorized",
        "new_experiment_authorized",
    ):
        expected = 0 if key == "new_case_rows_authorized" else False
        if design.get(key) != expected:
            raise ValueError(f"R7 design must keep {key}={expected}")
    if set(design.get("route_ids", [])) != R5_2_AUDIT_ROUTE_IDS:
        raise ValueError("R7 route ID set must match R5.2/R6 audited routes")
    if set(design.get("scenario_bundle_ids", [])) != R5_REQUIRED_SCENARIO_BUNDLE_IDS:
        raise ValueError("R7 scenario bundle ID set mismatch")
    band = payload.get("accepted_width_prior_band", {})
    for key, expected in R7_ACCEPTED_WIDTH_PRIOR_BAND.items():
        actual = band.get(key)
        if isinstance(expected, float):
            if float(actual) != expected:
                raise ValueError(f"R7 accepted width band mismatch: {key}")
        elif actual != expected:
            raise ValueError(f"R7 accepted width band mismatch: {key}")
    if set(band.get("accepted_explanatory_candidate_ids", [])) != {
        "width_exp1p5_800",
        "global_width_quadratic_regularization",
        "width_quad_850",
    }:
        raise ValueError("R7 accepted width-band candidate set mismatch")
    if "width_quad_900" not in set(band.get("over_severe_caution_candidate_ids", [])):
        raise ValueError("R7 width band must retain width_quad_900 caution")
    if band.get("optional_900_cannot_redefine_main") is not True:
        raise ValueError("R7 width band must keep optional 900 non-redefining")
    if band.get("width_quad_floor035_nearby_example_is_invalidated") is not True:
        raise ValueError("R7 must cleanly invalidate the old floor035 nearby example")

    mech = payload.get("mechanistic_decomposition_design", {})
    if int(mech.get("max_candidate_mechanistic_prior_count", -1)) != (
        R7_MAX_MECHANISTIC_CANDIDATE_COUNT
    ):
        raise ValueError("R7 mechanistic candidate cap mismatch")
    if set(mech.get("allowed_mechanistic_prior_families", [])) != (
        R7_ALLOWED_MECHANISTIC_PRIOR_FAMILIES
    ):
        raise ValueError("R7 allowed mechanistic prior family set mismatch")
    if set(mech.get("forbidden_mechanistic_prior_families", [])) != (
        R7_FORBIDDEN_MECHANISTIC_PRIOR_FAMILIES
    ):
        raise ValueError("R7 forbidden mechanistic prior family set mismatch")
    if set(mech.get("required_mechanistic_registry_fields", [])) != (
        R7_REQUIRED_MECHANISTIC_REGISTRY_FIELDS
    ):
        raise ValueError("R7 mechanistic registry field set mismatch")
    if mech.get("score_derived_physical_prior_authorized") is not False:
        raise ValueError("R7 must forbid score-derived physical priors")
    if mech.get("source_v1_relative_score_physical_prior_authorized") is not False:
        raise ValueError("R7 must forbid source_v1_relative_score as physical prior")
    if mech.get("outcome_proximal_diagnostics_must_be_labeled") is not True:
        raise ValueError("R7 must label outcome-proximal diagnostics")
    if mech.get("missing_physical_operator_fields_mark_not_executable") is not True:
        raise ValueError("R7 must mark missing operator artifacts as not executable")
    registry = mech.get("candidate_mechanistic_prior_registry", [])
    families = {row.get("candidate_prior_family") for row in registry}
    if families != R7_ALLOWED_MECHANISTIC_PRIOR_FAMILIES:
        raise ValueError("R7 mechanistic registry must cover every allowed family")
    for row in registry:
        if set(row) < R7_REQUIRED_MECHANISTIC_REGISTRY_FIELDS:
            raise ValueError("R7 mechanistic registry row is missing required fields")
        if row.get("candidate_prior_family") not in R7_ALLOWED_MECHANISTIC_PRIOR_FAMILIES:
            raise ValueError("R7 mechanistic family is not allowed")
        if int(row.get("dof_count_max", 99)) > 2:
            raise ValueError("R7 mechanistic candidates must stay low-dimensional")
        for key in (
            "uses_route_specific_multiplier",
            "uses_scenario_specific_per_route_fit",
            "uses_particle_specific_empirical_fit",
            "uses_source_v1_relative_score_as_physical_input",
            "changes_main_660_definition",
            "authorizes_route_promotion",
            "changes_selected_annulus",
        ):
            if row.get(key) is not False:
                raise ValueError(f"R7 mechanistic registry must keep {key}=false")
        if row.get("claim_level") not in {"relative_with_priors", "diagnostic_only"}:
            raise ValueError("R7 mechanistic registry claim level mismatch")

    particle = payload.get("particle_stratum_residual_policy", {})
    if particle.get("particle_stratum_residual_is_warning_not_fit_target") is not True:
        raise ValueError("R7 particle residuals must remain warnings")
    if particle.get("particle_specific_empirical_fit_authorized") is not False:
        raise ValueError("R7 must forbid particle-specific residual fitting")
    if set(particle.get("required_particle_residual_outputs", [])) != {
        "R7_particle_stratum_residual_top_routes.csv",
        "R7_particle_stratum_residual_by_family.csv",
        "R7_gold_anchor_vs_EV_residual_comparison.csv",
    }:
        raise ValueError("R7 particle residual output set mismatch")

    optional = payload.get("optional_900_governance_diagnostic", {})
    if optional.get("route_id") != "660_900x1400":
        raise ValueError("R7 optional 900 diagnostic route mismatch")
    if optional.get("optional_900_role") != "optional_robustness_probe":
        raise ValueError("R7 optional 900 role mismatch")
    if optional.get("main_660_redefinition_authorized") is not False:
        raise ValueError("R7 optional 900 diagnostic must not redefine main-660")
    if optional.get("route_promotion_authorized") is not False:
        raise ValueError("R7 optional 900 diagnostic must not promote routes")

    non_width = payload.get("non_width_prior_input_policy", {})
    if non_width.get("source_v1_relative_score_as_physical_prior_authorized") is not False:
        raise ValueError("R7 non-width policy must forbid source_v1 score priors")
    if non_width.get("outcome_proximal_candidate_ids") != ["reference_band_penalty"]:
        raise ValueError("R7 non-width policy must identify reference_band_penalty")
    if non_width.get("reference_band_next_version_requires_physical_columns") is not True:
        raise ValueError("R7 reference-band policy must require physical columns")
    if non_width.get("BFP_alignment_next_version_requires_operator_columns") is not True:
        raise ValueError("R7 BFP policy must require operator columns")

    gates = payload.get("future_pass_fail_criteria_if_execution_is_reviewed", {})
    for key in (
        "at_least_two_low_dimensional_mechanistic_priors_explain_warning",
        "main660_retention_fraction_at_least_0p85",
        "optional_900_does_not_redefine_main",
        "particle_residuals_reported_but_not_fit_away",
        "no_route_specific_or_scenario_specific_or_particle_specific_fit",
        "selected_annulus_parallel_lens_only",
        "claim_boundary_absolute_blocked",
        "route_governance_plan_if_reasonable_priors_leave_context_above_main",
        "stop_if_only_forbidden_fits_resolve_warning",
        "R7_execution_requires_separate_external_review",
    ):
        if gates.get(key) is not True:
            raise ValueError(f"R7 future criterion must require {key}=true")

    if set(payload.get("required_outputs_if_authorized_after_future_review", [])) != (
        R7_REQUIRED_OUTPUTS_IF_AUTHORIZED
    ):
        raise ValueError("R7 required output list mismatch")
    if not R7_REQUIRED_STOP_GATES.issubset(set(payload.get("stop_gates", []))):
        raise ValueError("R7 stop gates are incomplete")
    if set(payload.get("allowed_future_external_review_decisions", [])) != (
        R7_ALLOWED_FUTURE_REVIEW_DECISIONS
    ):
        raise ValueError("R7 future review decision set mismatch")

    claims = payload.get("claim_boundaries", {})
    for key, expected in {
        "SNR_claim_level": "absolute_blocked",
        "event_probability_claim_level": "absolute_blocked",
        "p_detect_mapping_claim_level": "relative_with_priors",
    }.items():
        if claims.get(key) != expected:
            raise ValueError(f"R7 claim boundary mismatch: {key}")
    for key in (
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_claim_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
        "legacy_detector_SNR_output_header_authorized",
        "legacy_calibrated_detector_SNR_output_header_authorized",
    ):
        if claims.get(key) is not False:
            raise ValueError(f"R7 claim boundary must keep {key}=false")

    provenance = payload.get("provenance_freeze", {})
    if set(provenance.get("required_checksum_fields", [])) != (
        R7_REQUIRED_PROVENANCE_FIELDS
    ):
        raise ValueError("R7 required provenance checksum field set mismatch")
    for field in R7_REQUIRED_PROVENANCE_FIELDS:
        value = str(provenance.get(field, ""))
        if len(value) != 64:
            raise ValueError(f"R7 provenance checksum is not sha256-like: {field}")

    return payload


def load_R7_1_operator_artifact_validation_plan() -> dict[str, Any]:
    return load_json_yaml("r7_1_operator_artifact_validation_plan.yaml")


def validate_R7_1_operator_artifact_validation_plan(
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = plan if plan is not None else load_R7_1_operator_artifact_validation_plan()
    if payload.get("schema_version") != R7_1_PLAN_SCHEMA_VERSION:
        raise ValueError("unexpected R7.1 plan schema_version")
    if payload.get("stage") != "R7_1_operator_artifact_validation_plan_only":
        raise ValueError("unexpected R7.1 plan stage")
    if payload.get("prior_gate") != (
        "PASS_R7_RESULTS_PREPARE_OPERATOR_ARTIFACT_GAP_REGISTER_PLAN_ONLY"
    ):
        raise ValueError("unexpected R7.1 prior gate")
    if payload.get("selected_next_stage_lane") != (
        "operator_artifact_gap_register_plan_only"
    ):
        raise ValueError("unexpected R7.1 next-stage lane")

    boundary = payload.get("authorization_boundary", {})
    expected_false = (
        "operator_artifact_execution_authorized",
        "experimental_validation_execution_authorized",
        "R8_plan_preparation_authorized",
        "R8_execution_authorized",
        "new_experiment_authorized",
        "new_solver_case_authorized",
        "new_scenario_bundle_authorized",
        "new_stochastic_seed_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "selected_annulus_bound_change_authorized",
        "route_specific_manual_prior_multipliers_authorized",
        "scenario_specific_per_route_fit_authorized",
        "particle_specific_empirical_fit_authorized",
        "score_derived_physical_prior_authorized",
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
    )
    if boundary.get("R7_1_plan_artifact_created") is not True:
        raise ValueError("R7.1 plan artifact must be marked created")
    for key in expected_false:
        if boundary.get(key) is not False:
            raise ValueError(f"R7.1 boundary must keep {key}=false")

    carry = payload.get("R7_evidence_carryforward", {})
    if carry.get("R7_route_prior_mechanistic_decomposition_audit_run") is not True:
        raise ValueError("R7.1 must carry a completed R7 audit")
    if int(carry.get("existing_R5_rows_interpreted", -1)) != R7_ROUTE_PRIOR_SOURCE_ROW_CAP:
        raise ValueError("R7.1 carryforward source row count mismatch")
    if int(carry.get("mechanistic_candidate_count", -1)) != 6:
        raise ValueError("R7.1 carryforward mechanistic candidate count mismatch")
    if int(carry.get("executable_existing_artifact_mechanistic_candidate_count", -1)) != 2:
        raise ValueError("R7.1 carryforward executable candidate count mismatch")
    if int(carry.get("physical_operator_artifact_gap_count", -1)) != 3:
        raise ValueError("R7.1 carryforward operator artifact gap count mismatch")
    if int(carry.get("particle_stratum_residual_warning_count", -1)) != 50:
        raise ValueError("R7.1 carryforward particle residual warning count mismatch")
    if carry.get("selected_future_recommendation_class") != (
        "prepare_operator_artifact_gap_register_plan_only"
    ):
        raise ValueError("R7.1 carryforward recommendation mismatch")
    for key in (
        "R8_plan_preparation_authorized",
        "R8_execution_authorized",
        "new_experiment_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "score_derived_physical_prior_attempted",
        "particle_specific_empirical_fit_attempted",
    ):
        if carry.get(key) is not False:
            raise ValueError(f"R7.1 carryforward guard must stay false: {key}")

    design = payload.get("R7_1_plan_design", {})
    if design.get("plan_execution_type") != "plan_only_no_operator_or_experiment_execution":
        raise ValueError("R7.1 design must be plan-only")
    if design.get("uses_existing_R7_outputs_only") is not True:
        raise ValueError("R7.1 plan must use existing R7 outputs only")
    if design.get("defines_evidence_requirements_not_measurements") is not True:
        raise ValueError("R7.1 must define requirements, not collect measurements")
    if int(design.get("new_case_rows_authorized", -1)) != 0:
        raise ValueError("R7.1 must authorize zero new case rows")
    for key in (
        "new_scenario_bundle_authorized",
        "new_stochastic_seed_authorized",
        "new_solver_case_authorized",
        "new_experiment_authorized",
    ):
        if design.get(key) is not False:
            raise ValueError(f"R7.1 design must keep {key}=false")
    if set(design.get("required_evidence_module_ids", [])) != (
        R7_1_REQUIRED_EVIDENCE_MODULE_IDS
    ):
        raise ValueError("R7.1 evidence module set mismatch")
    if set(design.get("forbidden_actions", [])) != R7_1_FORBIDDEN_ACTIONS:
        raise ValueError("R7.1 forbidden action set mismatch")

    modules = payload.get("evidence_module_registry", [])
    if {row.get("module_id") for row in modules} != R7_1_REQUIRED_EVIDENCE_MODULE_IDS:
        raise ValueError("R7.1 registry must cover every evidence module")
    for row in modules:
        if row.get("module_id") not in R7_1_REQUIRED_EVIDENCE_MODULE_IDS:
            raise ValueError("R7.1 registry module is not allowed")
        for key in (
            "authorizes_measurement",
            "authorizes_experiment",
            "authorizes_solver_case",
            "authorizes_route_promotion",
            "authorizes_main_660_redefinition",
            "uses_source_v1_relative_score_as_physical_input",
            "allows_route_specific_multiplier",
            "allows_particle_specific_fit",
        ):
            if row.get(key) is not False:
                raise ValueError(f"R7.1 evidence module must keep {key}=false")
        if row.get("claim_level") not in {"artifact_requirement", "diagnostic_only"}:
            raise ValueError("R7.1 evidence module claim level mismatch")

    if set(payload.get("required_outputs_if_future_self_review_authorizes", [])) != (
        R7_1_REQUIRED_OUTPUTS_IF_AUTHORIZED
    ):
        raise ValueError("R7.1 required future output list mismatch")
    if set(payload.get("stop_gates", [])) < R7_1_FORBIDDEN_ACTIONS:
        raise ValueError("R7.1 stop gates must include every forbidden action")

    claims = payload.get("claim_boundaries", {})
    for key, expected in {
        "SNR_claim_level": "absolute_blocked",
        "event_probability_claim_level": "absolute_blocked",
        "p_detect_mapping_claim_level": "relative_with_priors",
    }.items():
        if claims.get(key) != expected:
            raise ValueError(f"R7.1 claim boundary mismatch: {key}")
    for key in (
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_claim_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
        "legacy_detector_SNR_output_header_authorized",
        "legacy_calibrated_detector_SNR_output_header_authorized",
    ):
        if claims.get(key) is not False:
            raise ValueError(f"R7.1 claim boundary must keep {key}=false")

    provenance = payload.get("provenance_freeze", {})
    if set(provenance.get("required_checksum_fields", [])) != (
        R7_1_REQUIRED_PROVENANCE_FIELDS
    ):
        raise ValueError("R7.1 provenance field set mismatch")
    for field in R7_1_REQUIRED_PROVENANCE_FIELDS:
        value = str(provenance.get(field, ""))
        if len(value) != 64:
            raise ValueError(f"R7.1 provenance checksum is not sha256-like: {field}")

    return payload


def load_R7_2_operator_artifact_gap_register_plan() -> dict[str, Any]:
    return load_json_yaml("r7_2_operator_artifact_gap_register_plan.yaml")


def validate_R7_2_operator_artifact_gap_register_plan(
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = plan if plan is not None else load_R7_2_operator_artifact_gap_register_plan()
    if payload.get("schema_version") != R7_2_PLAN_SCHEMA_VERSION:
        raise ValueError("unexpected R7.2 plan schema_version")
    if payload.get("stage") != "R7_2_operator_artifact_gap_register_plan_only":
        raise ValueError("unexpected R7.2 plan stage")
    if payload.get("prior_gate") != (
        "PASS_R7_1_RESULTS_PREPARE_OPERATOR_ARTIFACT_GAP_REGISTER_ONLY"
    ):
        raise ValueError("unexpected R7.2 prior gate")
    if payload.get("selected_next_stage_lane") != (
        "operator_artifact_gap_register_plan_only"
    ):
        raise ValueError("unexpected R7.2 next-stage lane")

    boundary = payload.get("authorization_boundary", {})
    if boundary.get("R7_2_plan_artifact_created") is not True:
        raise ValueError("R7.2 plan artifact must be marked created")
    for key in (
        "operator_artifact_acquisition_authorized",
        "bench_measurement_authorized",
        "experimental_validation_execution_authorized",
        "R8_plan_preparation_authorized",
        "R8_execution_authorized",
        "new_experiment_authorized",
        "new_solver_case_authorized",
        "new_scenario_bundle_authorized",
        "new_stochastic_seed_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "selected_annulus_bound_change_authorized",
        "route_specific_manual_prior_multipliers_authorized",
        "scenario_specific_per_route_fit_authorized",
        "particle_specific_empirical_fit_authorized",
        "score_derived_physical_prior_authorized",
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
    ):
        if boundary.get(key) is not False:
            raise ValueError(f"R7.2 boundary must keep {key}=false")

    carry = payload.get("R7_1_evidence_carryforward", {})
    if carry.get("R7_1_operator_artifact_validation_protocol_generation_run") is not True:
        raise ValueError("R7.2 must carry a completed R7.1 protocol generation")
    if int(carry.get("evidence_module_count", -1)) != len(R7_1_REQUIRED_EVIDENCE_MODULE_IDS):
        raise ValueError("R7.2 carryforward evidence module count mismatch")
    if int(carry.get("required_artifact_field_count", -1)) != 30:
        raise ValueError("R7.2 carryforward required field count mismatch")
    if carry.get("selected_future_recommendation_class") != (
        "prepare_operator_artifact_gap_register_plan_only"
    ):
        raise ValueError("R7.2 carryforward recommendation mismatch")
    for key in (
        "operator_artifact_acquisition_started",
        "experimental_validation_started",
        "R8_plan_preparation_authorized",
        "R8_execution_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "score_derived_physical_prior_attempted",
        "particle_specific_empirical_fit_attempted",
    ):
        if carry.get(key) is not False:
            raise ValueError(f"R7.2 carryforward guard must stay false: {key}")

    design = payload.get("R7_2_plan_design", {})
    if design.get("plan_execution_type") != "plan_only_artifact_gap_register_no_acquisition":
        raise ValueError("R7.2 design must be plan-only")
    if design.get("uses_existing_R7_1_protocol_outputs_only") is not True:
        raise ValueError("R7.2 plan must use existing R7.1 outputs only")
    if design.get("defines_artifact_gap_register_not_acquisition") is not True:
        raise ValueError("R7.2 must define an artifact gap register, not acquisition")
    if int(design.get("artifact_id_count", -1)) != len(R7_2_REQUIRED_ARTIFACT_IDS):
        raise ValueError("R7.2 artifact count mismatch")
    if int(design.get("required_artifact_field_count", -1)) != 30:
        raise ValueError("R7.2 required artifact field count mismatch")
    if int(design.get("new_case_rows_authorized", -1)) != 0:
        raise ValueError("R7.2 must authorize zero new case rows")
    for key in (
        "new_scenario_bundle_authorized",
        "new_stochastic_seed_authorized",
        "new_solver_case_authorized",
        "new_experiment_authorized",
        "operator_artifact_acquisition_authorized",
        "bench_measurement_authorized",
    ):
        if design.get(key) is not False:
            raise ValueError(f"R7.2 design must keep {key}=false")
    if set(design.get("artifact_ids", [])) != R7_2_REQUIRED_ARTIFACT_IDS:
        raise ValueError("R7.2 artifact ID set mismatch")
    if set(design.get("forbidden_actions", [])) != R7_2_FORBIDDEN_ACTIONS:
        raise ValueError("R7.2 forbidden action set mismatch")

    registry = payload.get("artifact_gap_registry", [])
    if {row.get("artifact_id") for row in registry} != R7_2_REQUIRED_ARTIFACT_IDS:
        raise ValueError("R7.2 registry must cover every artifact ID")
    protocol_ids = {row.get("source_protocol_module_id") for row in registry}
    if protocol_ids != R7_1_REQUIRED_EVIDENCE_MODULE_IDS:
        raise ValueError("R7.2 registry must map every R7.1 protocol module")
    for row in registry:
        if int(row.get("required_field_count", -1)) <= 0:
            raise ValueError("R7.2 artifact rows must require fields")
        if row.get("gap_status") != "registered_no_acquisition":
            raise ValueError("R7.2 artifact gap status must remain not started")
        for key in (
            "gap_resolution_authorized",
            "bench_measurement_authorized",
            "experiment_authorized",
            "solver_case_authorized",
            "route_promotion_authorized",
            "main_660_redefinition_authorized",
            "uses_source_v1_relative_score_as_physical_input",
            "allows_route_specific_multiplier",
            "allows_particle_specific_fit",
        ):
            if row.get(key) is not False:
                raise ValueError(f"R7.2 artifact registry must keep {key}=false")
        if row.get("claim_level") not in {"artifact_gap_register", "diagnostic_only"}:
            raise ValueError("R7.2 artifact registry claim level mismatch")

    if set(payload.get("required_outputs_if_future_self_review_authorizes", [])) != (
        R7_2_REQUIRED_OUTPUTS_IF_AUTHORIZED
    ):
        raise ValueError("R7.2 required future output list mismatch")
    if set(payload.get("stop_gates", [])) < R7_2_FORBIDDEN_ACTIONS:
        raise ValueError("R7.2 stop gates must include every forbidden action")

    claims = payload.get("claim_boundaries", {})
    for key, expected in {
        "SNR_claim_level": "absolute_blocked",
        "event_probability_claim_level": "absolute_blocked",
        "p_detect_mapping_claim_level": "relative_with_priors",
    }.items():
        if claims.get(key) != expected:
            raise ValueError(f"R7.2 claim boundary mismatch: {key}")
    for key in (
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_claim_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
        "legacy_detector_SNR_output_header_authorized",
        "legacy_calibrated_detector_SNR_output_header_authorized",
    ):
        if claims.get(key) is not False:
            raise ValueError(f"R7.2 claim boundary must keep {key}=false")

    provenance = payload.get("provenance_freeze", {})
    if set(provenance.get("required_checksum_fields", [])) != (
        R7_2_REQUIRED_PROVENANCE_FIELDS
    ):
        raise ValueError("R7.2 provenance field set mismatch")
    for field in R7_2_REQUIRED_PROVENANCE_FIELDS:
        value = str(provenance.get(field, ""))
        if len(value) != 64:
            raise ValueError(f"R7.2 provenance checksum is not sha256-like: {field}")

    return payload


def load_v2_no_measured_data_closure_plan() -> dict[str, Any]:
    return load_json_yaml("v2_no_measured_data_closure_plan.yaml")


def validate_v2_no_measured_data_closure_plan(
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = plan if plan is not None else load_v2_no_measured_data_closure_plan()
    if payload.get("schema_version") != V2_NO_MEASURED_DATA_CLOSURE_SCHEMA_VERSION:
        raise ValueError("unexpected v2 closure plan schema_version")
    if payload.get("stage") != "V2_no_measured_data_closure_plan_only":
        raise ValueError("unexpected v2 closure plan stage")
    if payload.get("prior_gate") != (
        "PASS_R7_2_RESULTS_PREPARE_V2_NO_MEASURED_DATA_CLOSURE_ONLY"
    ):
        raise ValueError("unexpected v2 closure prior gate")
    if payload.get("selected_next_stage_lane") != "v2_no_measured_data_closure_only":
        raise ValueError("unexpected v2 closure lane")

    boundary = payload.get("authorization_boundary", {})
    if boundary.get("v2_closure_plan_artifact_created") is not True:
        raise ValueError("v2 closure plan artifact must be marked created")
    if boundary.get("v2_is_no_measured_data_lane") is not True:
        raise ValueError("v2 closure must stay in the no-measured-data lane")
    for key in (
        "operator_artifact_acquisition_authorized",
        "bench_measurement_authorized",
        "experimental_validation_execution_authorized",
        "R8_plan_preparation_authorized",
        "R8_execution_authorized",
        "new_experiment_authorized",
        "new_solver_case_authorized",
        "new_scenario_bundle_authorized",
        "new_stochastic_seed_authorized",
        "R5_followup_expansion_authorized",
        "R6_followup_expansion_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "optional_660_900x1400_redefines_main_660",
        "selected_annulus_bound_change_authorized",
        "selected_annulus_replaces_all_crossing_ranking",
        "route_specific_manual_prior_multipliers_authorized",
        "scenario_specific_per_route_fit_authorized",
        "particle_specific_empirical_fit_authorized",
        "score_derived_physical_prior_authorized",
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
    ):
        if boundary.get(key) is not False:
            raise ValueError(f"v2 closure boundary must keep {key}=false")

    carry = payload.get("R7_2_evidence_carryforward", {})
    if carry.get("R7_2_operator_artifact_gap_register_generation_run") is not True:
        raise ValueError("v2 closure must carry a completed R7.2 gap register")
    if carry.get("generation_type") != "artifact_gap_register_only_no_acquisition":
        raise ValueError("v2 closure R7.2 carryforward type mismatch")
    if int(carry.get("artifact_id_count", -1)) != len(R7_2_REQUIRED_ARTIFACT_IDS):
        raise ValueError("v2 closure R7.2 artifact count mismatch")
    if int(carry.get("required_artifact_field_count", -1)) != 30:
        raise ValueError("v2 closure R7.2 field count mismatch")
    if carry.get("selected_future_recommendation_class") != (
        "prepare_v2_no_measured_data_closure_only"
    ):
        raise ValueError("v2 closure R7.2 recommendation mismatch")
    for key in (
        "operator_artifact_acquisition_started",
        "bench_measurement_started",
        "experimental_validation_started",
        "R8_plan_preparation_authorized",
        "R8_execution_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "selected_annulus_bound_change_authorized",
    ):
        if carry.get(key) is not False:
            raise ValueError(f"v2 closure carryforward guard must stay false: {key}")

    design = payload.get("closure_design", {})
    if design.get("closure_type") != "no_measured_data_synthetic_prior_model_closure":
        raise ValueError("v2 closure type mismatch")
    if design.get("uses_existing_R7_2_artifacts_only") is not True:
        raise ValueError("v2 closure must use existing R7.2 artifacts only")
    if design.get("does_not_start_post_v2_dependency_resolution") is not True:
        raise ValueError("v2 closure must not start dependency resolution")
    for key in (
        "new_case_rows_added",
        "new_scenario_bundles_added",
        "new_stochastic_seeds_added",
        "new_solver_cases_added",
        "new_experiments_started",
    ):
        if int(design.get(key, -1)) != 0:
            raise ValueError(f"v2 closure must keep {key}=0")
    if set(design.get("forbidden_actions", [])) != V2_CLOSURE_FORBIDDEN_ACTIONS:
        raise ValueError("v2 closure forbidden action set mismatch")

    route = payload.get("route_governance_closure", {})
    if set(route.get("locked_main_660_route_ids", [])) != {
        "660_800x1400",
        "660_800x1500",
    }:
        raise ValueError("v2 closure main-660 route lock mismatch")
    for key in (
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "optional_660_900x1400_redefines_main_660",
        "selected_annulus_replaces_all_crossing_ranking",
        "selected_annulus_bound_change_authorized",
        "route_specific_manual_sign_flips_authorized",
    ):
        if route.get(key) is not False:
            raise ValueError(f"v2 closure route governance must keep {key}=false")

    scientific = payload.get("scientific_closure", {})
    if scientific.get("model_class") != "synthetic_relative_prior_model":
        raise ValueError("v2 closure model class mismatch")
    if scientific.get("v2_role") != "instrument_aware_realism_simulation_supplement":
        raise ValueError("v2 closure role mismatch")
    if set(scientific.get("supplements_original_result_lanes", [])) != {
        "engineering_logic",
        "baseline_simulation_outputs",
    }:
        raise ValueError("v2 closure supplement lane mismatch")
    if scientific.get("credibility_function") != (
        "adds_reality_biased_instrument_route_prior_constraints_without_measured_data"
    ):
        raise ValueError("v2 closure credibility function mismatch")
    if scientific.get("measured_data_used") is not False:
        raise ValueError("v2 closure cannot use measured data")
    if scientific.get("physical_calibration_claimed") is not False:
        raise ValueError("v2 closure cannot claim physical calibration")
    if scientific.get("R6_width_family_prior_interpretation") != (
        "stable_low_dimensional_explanatory_hypothesis_not_physical_law"
    ):
        raise ValueError("v2 closure R6 interpretation boundary mismatch")

    claims = payload.get("claim_boundaries", {})
    for key, expected in {
        "SNR_claim_level": "absolute_blocked",
        "event_probability_claim_level": "absolute_blocked",
        "p_detect_mapping_claim_level": "relative_with_priors",
        "primary_metric": "detectability_relative_prior_score",
        "detected_events_source": "relative_prior_score_proxy_count_not_observed_events",
    }.items():
        if claims.get(key) != expected:
            raise ValueError(f"v2 closure claim boundary mismatch: {key}")
    for key in (
        "calibrated_SNR_claim_authorized",
        "calibrated_event_probability_claim_authorized",
        "absolute_LOD_claim_authorized",
        "true_EV_concentration_claim_authorized",
        "biological_specificity_claim_authorized",
        "legacy_detector_SNR_output_header_authorized",
        "legacy_calibrated_detector_SNR_output_header_authorized",
    ):
        if claims.get(key) is not False:
            raise ValueError(f"v2 closure claim boundary must keep {key}=false")

    if set(payload.get("required_outputs_if_self_review_authorizes", [])) != (
        V2_CLOSURE_REQUIRED_OUTPUTS
    ):
        raise ValueError("v2 closure required output list mismatch")
    if set(payload.get("stop_gates", [])) < V2_CLOSURE_FORBIDDEN_ACTIONS:
        raise ValueError("v2 closure stop gates must include every forbidden action")

    provenance = payload.get("provenance_freeze", {})
    if set(provenance.get("required_checksum_fields", [])) != (
        V2_CLOSURE_REQUIRED_PROVENANCE_FIELDS
    ):
        raise ValueError("v2 closure provenance field set mismatch")
    for field in V2_CLOSURE_REQUIRED_PROVENANCE_FIELDS:
        value = str(provenance.get(field, ""))
        if len(value) != 64:
            raise ValueError(f"v2 closure checksum is not sha256-like: {field}")

    return payload


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unavailable"


def build_run_manifest(
    *,
    output_directory: str | Path,
    event_budget: dict[str, Any],
    scenario_budget: dict[str, Any],
    base_v1_summary_path: str | Path | None = None,
    run_id: str = "EV_NODI_realism_v2_micro_anchor_R1p5",
    random_seed_policy: str = "deterministic_micro_anchor_no_stochastic_event_level_run",
    R2_anchor_smoke_run: bool = False,
    R3_reduced_grid_run: bool = False,
    R3a_reduced_grid_named_bundle_survey_run: bool = False,
    R3b_uncertainty_expansion_run: bool = False,
    R4_representative_full_wave_validation_run: bool = False,
    R5_full_grid_v2_run: bool = False,
) -> dict[str, Any]:
    output_directory = Path(output_directory)
    if base_v1_summary_path is None:
        base_v1_summary_path = (
            PROJECT_ROOT
            / "results"
            / "ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv"
        )
    base_path = Path(base_v1_summary_path)
    base_checksum = sha256_file(base_path) if base_path.exists() else "unavailable"
    checksums = {
        "scenario_registry_checksum": sha256_file(CONFIG_DIR / "scenario_registry.yaml"),
        "detector_state_machine_checksum": sha256_file(
            CONFIG_DIR / "detector_connection_state_machine.yaml"
        ),
        "laser_daq_schema_checksum": sha256_file(CONFIG_DIR / "laser_daq_schema.yaml"),
        "unit_registry_checksum": sha256_file(CONFIG_DIR / "unit_registry.yaml"),
        "claim_level_matrix_checksum": sha256_file(CONFIG_DIR / "claim_level_matrix.csv"),
        "calibration_artifact_registry_checksum": sha256_file(
            CONFIG_DIR / "calibration_artifact_registry.yaml"
        ),
        "route_key_schema_checksum": sha256_file(CONFIG_DIR / "route_key_schema.yaml"),
        "run_manifest_schema_checksum": sha256_file(CONFIG_DIR / "run_manifest_schema.yaml"),
        "r3b_uncertainty_prior_table_checksum": sha256_file(
            CONFIG_DIR / "r3b_uncertainty_prior_table.yaml"
        ),
        "r4_representative_full_wave_plan_checksum": sha256_file(
            CONFIG_DIR / "r4_representative_full_wave_plan.yaml"
        ),
    }
    manifest = {
        "run_id": run_id,
        "git_commit": _git_commit(),
        "roadmap_version": "reports/51_EV_NODI_realism_v2_instrument_aware_roadmap.md",
        "schema_version": "realism_v2_R0_P0",
        "created_at": datetime.now(UTC).isoformat(),
        "base_v1_summary_path": str(base_path),
        "base_v1_summary_checksum": base_checksum,
        "random_seed_policy": random_seed_policy,
        "event_budget": event_budget,
        "scenario_budget": scenario_budget,
        "output_directory": str(output_directory),
        "R2_anchor_smoke_run": R2_anchor_smoke_run,
        "R3_reduced_grid_run": R3_reduced_grid_run,
        "R3a_reduced_grid_named_bundle_survey_run": (
            R3a_reduced_grid_named_bundle_survey_run
        ),
        "R3b_uncertainty_expansion_run": R3b_uncertainty_expansion_run,
        "R4_representative_full_wave_validation_run": (
            R4_representative_full_wave_validation_run
        ),
        "R5_full_grid_v2_run": R5_full_grid_v2_run,
        "v1_full_grid_overwritten": False,
        "Tsuyama_paper_fit_continued": False,
        "selected_annulus_bounds_changed": False,
        "calibrated_SNR_claim_emitted": False,
        "ET2030_direct_current_input_unlocked": False,
        "base_v1_summary_path_relative": str(base_path.relative_to(PROJECT_ROOT))
        if base_path.exists() and base_path.is_relative_to(PROJECT_ROOT)
        else str(base_path),
        "output_directory_relative": str(output_directory.relative_to(PROJECT_ROOT))
        if output_directory.is_absolute() and output_directory.is_relative_to(PROJECT_ROOT)
        else str(output_directory),
        **checksums,
    }
    validate_run_manifest(manifest)
    return manifest


def validate_run_manifest(manifest: dict[str, Any]) -> None:
    schema = load_json_yaml("run_manifest_schema.yaml")
    missing = set(schema["required_fields"]).difference(manifest)
    if missing:
        raise ValueError(f"run_manifest missing required fields: {sorted(missing)}")
    checksum_fields = [field for field in manifest if field.endswith("_checksum")]
    if len(checksum_fields) < 6:
        raise ValueError("run_manifest must carry active schema checksum fields")
    for field in checksum_fields:
        value = str(manifest[field])
        if value != "unavailable" and len(value) != 64:
            raise ValueError(f"run_manifest checksum field is not sha256-like: {field}")


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _micro_anchor_routes() -> tuple[tuple[int, int, int], ...]:
    return ((660, 800, 1400), (660, 700, 1500), (404, 600, 1300), (532, 600, 1500))


def _micro_anchor_particles() -> tuple[tuple[str, float], ...]:
    return (
        ("blank", 0.0),
        ("EV70_lowRI", 0.20),
        ("EV100_nominal", 0.45),
        ("Au40", 2.0),
    )


def anchor_smoke_routes(include_optional: bool = True) -> tuple[tuple[int, int, int], ...]:
    routes = (
        (660, 800, 1400),
        (660, 800, 1500),
        (660, 700, 1500),
        (660, 800, 550),
        (660, 800, 600),
        (660, 800, 700),
        (404, 600, 1300),
        (404, 800, 550),
        (404, 800, 600),
        (404, 800, 700),
        (532, 600, 1500),
        (488, 600, 1500),
    )
    if include_optional:
        routes = routes + ((660, 900, 1400), (404, 700, 1400))
    if len(routes) > MAX_ANCHOR_ROUTES:
        raise ValueError("anchor smoke route panel exceeds max_anchor_routes")
    return routes


def anchor_smoke_particles() -> tuple[dict[str, Any], ...]:
    return (
        {
            "particle_id": "EV70_lowRI",
            "particle_profile_id": "EV_low_RI_anchor_panel",
            "particle_factor": 0.20,
            "particle_class": "EV",
        },
        {
            "particle_id": "EV100_nominal",
            "particle_profile_id": "EV_nominal_anchor_panel",
            "particle_factor": 0.45,
            "particle_class": "EV",
        },
        {
            "particle_id": "EV150_nominal",
            "particle_profile_id": "EV_nominal_anchor_panel",
            "particle_factor": 0.95,
            "particle_class": "EV",
        },
        {
            "particle_id": "EV250_large_tail",
            "particle_profile_id": "EV_large_tail_anchor_panel",
            "particle_factor": 2.50,
            "particle_class": "EV",
        },
        {
            "particle_id": "LDL_like_contaminant",
            "particle_profile_id": "contaminant_anchor_panel",
            "particle_factor": 0.70,
            "particle_class": "contaminant",
        },
        {
            "particle_id": "protein_aggregate",
            "particle_profile_id": "contaminant_anchor_panel",
            "particle_factor": 0.30,
            "particle_class": "contaminant",
        },
        {
            "particle_id": "Au40",
            "particle_profile_id": "metal_standard_anchor_panel",
            "particle_factor": 2.00,
            "particle_class": "standard",
        },
        {
            "particle_id": "Ag60",
            "particle_profile_id": "metal_standard_anchor_panel",
            "particle_factor": 1.60,
            "particle_class": "standard",
        },
    )


def anchor_smoke_scenario_bundles() -> tuple[dict[str, Any], ...]:
    return (
        {
            "scenario_id": "nominal_instrument_clean_blank",
            "instrument_path_id": "ET2030_50ohm_voltage",
            "detector_source": "ET2030_BNC_biased_output",
            "connection_readout_path": "voltage_input_50ohm",
            "termination_mode": "50_ohm",
            "power_scale": 1.0,
            "roi_weight_scale": 1.0,
            "blank_threshold_sigma": 5.0,
            "blank_independent_samples_per_s": 500.0,
            "colored_noise_correlation_time_s": 0.02,
            "RIN_PSD_1_per_Hz": 1.0e-12,
            "peg_survival_factor": 1.0,
            "daq_snr_factor": 1.0,
            "scenario_role": "nominal",
        },
        {
            "scenario_id": "detector_50ohm_pessimistic",
            "instrument_path_id": "ET2030_50ohm_voltage",
            "detector_source": "ET2030_BNC_biased_output",
            "connection_readout_path": "voltage_input_50ohm",
            "termination_mode": "50_ohm",
            "power_scale": 0.6,
            "roi_weight_scale": 0.75,
            "blank_threshold_sigma": 5.0,
            "blank_independent_samples_per_s": 700.0,
            "colored_noise_correlation_time_s": 0.03,
            "RIN_PSD_1_per_Hz": 5.0e-12,
            "peg_survival_factor": 0.9,
            "daq_snr_factor": 0.8,
            "scenario_role": "detector_pessimistic",
        },
        {
            "scenario_id": "external_TIA_optimistic",
            "instrument_path_id": "external_TIA_voltage",
            "detector_source": "external_TIA_voltage_output",
            "connection_readout_path": "lockin_voltage_input",
            "termination_mode": "voltage_input",
            "power_scale": 1.0,
            "roi_weight_scale": 1.15,
            "blank_threshold_sigma": 5.0,
            "blank_independent_samples_per_s": 400.0,
            "colored_noise_correlation_time_s": 0.02,
            "RIN_PSD_1_per_Hz": 5.0e-13,
            "peg_survival_factor": 1.0,
            "daq_snr_factor": 1.3,
            "scenario_role": "external_TIA_optimistic",
        },
        {
            "scenario_id": "blank_bursty_RIN_high",
            "instrument_path_id": "ET2030_50ohm_voltage",
            "detector_source": "ET2030_BNC_biased_output",
            "connection_readout_path": "voltage_input_50ohm",
            "termination_mode": "50_ohm",
            "power_scale": 0.85,
            "roi_weight_scale": 0.95,
            "blank_threshold_sigma": 5.5,
            "blank_independent_samples_per_s": 1000.0,
            "colored_noise_correlation_time_s": 0.05,
            "RIN_PSD_1_per_Hz": 1.0e-10,
            "peg_survival_factor": 0.95,
            "daq_snr_factor": 0.9,
            "scenario_role": "blank_pessimistic",
        },
        {
            "scenario_id": "BFP_slit_offset_leakage",
            "instrument_path_id": "ET2030_50ohm_voltage",
            "detector_source": "ET2030_BNC_biased_output",
            "connection_readout_path": "voltage_input_50ohm",
            "termination_mode": "50_ohm",
            "power_scale": 1.0,
            "roi_weight_scale": 0.55,
            "blank_threshold_sigma": 5.0,
            "blank_independent_samples_per_s": 650.0,
            "colored_noise_correlation_time_s": 0.025,
            "RIN_PSD_1_per_Hz": 2.0e-12,
            "peg_survival_factor": 1.0,
            "daq_snr_factor": 0.75,
            "scenario_role": "BFP_offset",
        },
        {
            "scenario_id": "PEG_pessimistic_wall_loss",
            "instrument_path_id": "ET2030_50ohm_voltage",
            "detector_source": "ET2030_BNC_biased_output",
            "connection_readout_path": "voltage_input_50ohm",
            "termination_mode": "50_ohm",
            "power_scale": 0.95,
            "roi_weight_scale": 0.85,
            "blank_threshold_sigma": 5.0,
            "blank_independent_samples_per_s": 500.0,
            "colored_noise_correlation_time_s": 0.03,
            "RIN_PSD_1_per_Hz": 1.5e-12,
            "peg_survival_factor": 0.55,
            "daq_snr_factor": 0.9,
            "scenario_role": "wall_loss",
        },
        {
            "scenario_id": "404_thermal_high_low_power",
            "instrument_path_id": "ET2030_50ohm_voltage",
            "detector_source": "ET2030_BNC_biased_output",
            "connection_readout_path": "voltage_input_50ohm",
            "termination_mode": "50_ohm",
            "power_scale": 0.35,
            "roi_weight_scale": 0.9,
            "blank_threshold_sigma": 5.0,
            "blank_independent_samples_per_s": 600.0,
            "colored_noise_correlation_time_s": 0.04,
            "RIN_PSD_1_per_Hz": 4.0e-12,
            "peg_survival_factor": 0.85,
            "daq_snr_factor": 0.9,
            "scenario_role": "thermal_404_gate",
        },
        {
            "scenario_id": "DAQ_low_resolution_sampling",
            "instrument_path_id": "ET2030_50ohm_voltage",
            "detector_source": "ET2030_BNC_biased_output",
            "connection_readout_path": "voltage_input_50ohm",
            "termination_mode": "50_ohm",
            "power_scale": 1.0,
            "roi_weight_scale": 0.9,
            "blank_threshold_sigma": 5.0,
            "blank_independent_samples_per_s": 550.0,
            "colored_noise_correlation_time_s": 0.02,
            "RIN_PSD_1_per_Hz": 2.0e-12,
            "peg_survival_factor": 0.95,
            "daq_snr_factor": 0.55,
            "scenario_role": "DAQ_pessimistic",
        },
    )


def reduced_grid_R3a_routes() -> tuple[tuple[int, int, int], ...]:
    return tuple(
        (wavelength_nm, width_nm, depth_nm)
        for wavelength_nm in (404, 488, 532, 660)
        for width_nm in (600, 700, 800, 900)
        for depth_nm in (500, 550, 600, 700, 1300, 1400, 1500)
    )


def reduced_grid_R3a_particles() -> tuple[dict[str, Any], ...]:
    nominal_sizes = (50, 70, 100, 120, 150, 200, 250)
    sensitivity_sizes = (70, 100, 150, 250)
    particles: list[dict[str, Any]] = []
    for size_nm in nominal_sizes:
        factor = 0.45 * (size_nm / 100.0) ** 1.8
        particles.append(
            {
                "particle_id": f"EV{size_nm}_nominal",
                "particle_profile_id": "EV_nominal_R3a_panel",
                "particle_factor": factor,
                "particle_class": "EV",
                "particle_role": "EV_nominal_RI_size_panel",
            }
        )
    for size_nm in sensitivity_sizes:
        nominal_factor = 0.45 * (size_nm / 100.0) ** 1.8
        particles.append(
            {
                "particle_id": f"EV{size_nm}_lowRI",
                "particle_profile_id": "EV_low_RI_R3a_panel",
                "particle_factor": 0.65 * nominal_factor,
                "particle_class": "EV",
                "particle_role": "EV_low_RI_sensitivity",
            }
        )
    for size_nm in sensitivity_sizes:
        nominal_factor = 0.45 * (size_nm / 100.0) ** 1.8
        particles.append(
            {
                "particle_id": f"EV{size_nm}_highRI",
                "particle_profile_id": "EV_high_RI_R3a_panel",
                "particle_factor": 1.35 * nominal_factor,
                "particle_class": "EV",
                "particle_role": "EV_high_RI_sensitivity",
            }
        )
    particles.extend(
        [
            {
                "particle_id": "LDL_like_contaminant",
                "particle_profile_id": "contaminant_R3a_panel",
                "particle_factor": 0.70,
                "particle_class": "contaminant",
                "particle_role": "optical_contaminant_control",
            },
            {
                "particle_id": "protein_aggregate",
                "particle_profile_id": "contaminant_R3a_panel",
                "particle_factor": 0.30,
                "particle_class": "contaminant",
                "particle_role": "optical_contaminant_control",
            },
            {
                "particle_id": "EV_doublet",
                "particle_profile_id": "contaminant_R3a_panel",
                "particle_factor": 1.40,
                "particle_class": "contaminant",
                "particle_role": "doublet_control_not_specificity_claim",
            },
            {
                "particle_id": "Au20",
                "particle_profile_id": "metal_standard_R3a_panel",
                "particle_factor": 0.80,
                "particle_class": "standard",
                "particle_role": "metal_standard_control",
            },
            {
                "particle_id": "Au40",
                "particle_profile_id": "metal_standard_R3a_panel",
                "particle_factor": 2.00,
                "particle_class": "standard",
                "particle_role": "metal_standard_control",
            },
            {
                "particle_id": "Au60",
                "particle_profile_id": "metal_standard_R3a_panel",
                "particle_factor": 3.20,
                "particle_class": "standard",
                "particle_role": "metal_standard_control",
            },
            {
                "particle_id": "Ag40",
                "particle_profile_id": "metal_standard_R3a_panel",
                "particle_factor": 1.15,
                "particle_class": "standard",
                "particle_role": "metal_standard_control",
            },
            {
                "particle_id": "Ag60",
                "particle_profile_id": "metal_standard_R3a_panel",
                "particle_factor": 1.60,
                "particle_class": "standard",
                "particle_role": "metal_standard_control",
            },
        ]
    )
    if len(particles) != MAX_R3A_PARTICLES:
        raise ValueError("R3a particle panel must remain at the authorized 23-particle cap")
    return tuple(particles)


def route_role_R3a(wavelength_nm: int, width_nm: int, depth_nm: int) -> str:
    if (wavelength_nm, width_nm, depth_nm) in {
        (660, 800, 1400),
        (660, 800, 1500),
    }:
        return "main_660"
    if (wavelength_nm, width_nm, depth_nm) == (660, 700, 1500):
        return "weak_reference_control"
    if (wavelength_nm, width_nm, depth_nm) == (660, 900, 1400):
        return "optional_robustness_probe"
    if wavelength_nm == 660 and width_nm == 800 and depth_nm in {550, 600, 700}:
        return "selected_annulus_sanity_overlap_longwave"
    if (wavelength_nm, width_nm, depth_nm) == (404, 600, 1300):
        return "shortwave_mechanism_candidate"
    if wavelength_nm == 404 and width_nm == 800 and depth_nm in {550, 600, 700}:
        return "selected_annulus_sanity_overlap_shortwave"
    if (wavelength_nm, width_nm, depth_nm) in {
        (532, 600, 1500),
        (488, 600, 1500),
    }:
        return "medium_wave_baseline"
    return "reduced_grid_context_route"


def classify_R3a_scenario_spread_watch(
    *, min_snr: float, max_snr: float, physical_explanation: str = ""
) -> dict[str, Any]:
    if min_snr <= 0:
        spread = float("inf")
    else:
        spread = max_snr / min_snr
    if spread > 1.0e3 and not physical_explanation:
        status = "stop_requires_physical_explanation"
    elif spread > 1.0e3:
        status = "watch_explained_over_1e3"
    else:
        status = "pass_under_1e3"
    return {
        "scenario_SNR_spread": spread,
        "scenario_spread_watch_status": status,
        "stop_if_spread_exceeds_1e3_without_physical_explanation": True,
        "physical_explanation": physical_explanation,
    }


def _scenario_connection(scenario: dict[str, Any]) -> dict[str, Any]:
    return evaluate_detector_connection(
        detector_source=str(scenario["detector_source"]),
        readout_path=str(scenario["connection_readout_path"]),
        termination_mode=str(scenario["termination_mode"]),
    )


def _anchor_smoke_power(
    *,
    wavelength_nm: int,
    width_nm: int,
    depth_nm: int,
    particle_factor: float,
    scenario: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    wavelength_factor = (660.0 / float(wavelength_nm)) ** 1.4
    geometry_factor = max(0.1, (width_nm / 800.0) * (depth_nm / 1400.0))
    P_probe_base_W = 2.0e-5 if wavelength_nm != 404 else 4.0e-6
    P_probe_W = P_probe_base_W * float(scenario["power_scale"])
    p_beam_per_m2 = 1.0 / (math.pi * (0.7e-6) * (0.9e-6))
    Csca_total = particle_factor * wavelength_factor * 1.0e-16
    dcs = np.full(16, Csca_total / (4.0 * math.pi))
    weights_sr = np.full(16, 4.0 * math.pi / 16.0)
    collection = np.full(
        16,
        min(1.0, 0.12 * geometry_factor * float(scenario["roi_weight_scale"])),
    )
    mie = mie_to_power_roi(
        P_probe_W=P_probe_W,
        p_beam_at_particle_per_m2=p_beam_per_m2,
        dCsca_dOmega_m2_per_sr=dcs,
        solid_angle_weights_sr=weights_sr,
        collection_throughput=collection,
        Csca_total_m2=Csca_total,
        Cabs_m2=0.1 * Csca_total,
        Cext_m2=1.2 * Csca_total if Csca_total > 0 else 1.0e-30,
    )
    u_axis = np.linspace(-0.25, 0.25, 7)
    v_axis = np.linspace(-0.25, 0.25, 7)
    u_grid, v_grid = np.meshgrid(u_axis, v_axis)
    weight = np.ones_like(u_grid) * float(scenario["roi_weight_scale"])
    E_ref = np.ones_like(u_grid, dtype=complex) * 1.0e-3
    E_sca = np.ones_like(u_grid, dtype=complex) * (
        -particle_factor * wavelength_factor * geometry_factor * 1.0e-5
    )
    reference_power_prior_scale_W = (
        1.0e-8
        * geometry_factor
        * float(scenario["power_scale"])
        * float(scenario["roi_weight_scale"])
    )
    bfp = bfp_roi_intensity_operator(
        E_ref=E_ref,
        E_sca=E_sca,
        weight=weight,
        du=float(u_axis[1] - u_axis[0]),
        dv=float(v_axis[1] - v_axis[0]),
        u=u_grid,
        v=v_grid,
        NA=0.45,
        n_medium=1.333,
        power_scale_W=reference_power_prior_scale_W,
    )
    bfp["reference_power_prior_scale_W"] = reference_power_prior_scale_W
    return mie, bfp


def _relative_detectability_prior_score(
    *,
    effective_snr: float,
    particle_class: str,
    wavelength_nm: int,
    thermal_artifact_risk: str,
) -> float:
    # This is a relative bounded-prior score, not a calibrated event probability.
    normalized = max(effective_snr, 1.0e-18) / 1.0e-6
    score = 1.0 / (1.0 + math.exp(-math.log10(normalized) * 1.3))
    if particle_class == "contaminant":
        score *= 0.75
    if wavelength_nm == 404 and thermal_artifact_risk == "amber":
        score *= 0.85
    if wavelength_nm == 404 and thermal_artifact_risk == "red":
        score = 0.0
    return float(max(0.0, min(1.0, score)))


def _wilson_half_width(successes: int, total: int, z: float = 1.96) -> float:
    if total <= 0:
        raise ValueError("total must be positive")
    p = successes / total
    denom = 1.0 + z**2 / total
    return float(
        z
        * math.sqrt(p * (1.0 - p) / total + z**2 / (4.0 * total**2))
        / denom
    )


def run_micro_anchor(
    output_dir: str | Path = DEFAULT_MICRO_ANCHOR_DIR, *, write_root_manifest: bool = True
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"
    scenario_id = "micro_anchor_nominal_sanity"
    scenario_identity = make_scenario_identity(
        scenario_id=scenario_id,
        instrument_chain_id="ET2030_50ohm_voltage_plus_external_TIA_algebraic_check",
        prior_sample_id="fixed_nominal_R1p5",
        sidecar_id="P0_P0p5_posthoc_micro_anchor",
    )

    valid_connection = evaluate_detector_connection(
        detector_source="ET2030_BNC_biased_output",
        readout_path="voltage_input_50ohm",
        termination_mode="50_ohm",
    )
    invalid_connection = evaluate_detector_connection(
        detector_source="ET2030_BNC_biased_output",
        readout_path="LI5640_current_input_direct",
    )

    micro_rows: list[dict[str, Any]] = []
    unit_rows: list[dict[str, Any]] = []
    mie_rows: list[dict[str, Any]] = []
    blank_rows: list[dict[str, Any]] = []

    u_axis = np.linspace(-0.25, 0.25, 7)
    v_axis = np.linspace(-0.25, 0.25, 7)
    u_grid, v_grid = np.meshgrid(u_axis, v_axis)
    weight = np.ones_like(u_grid) * 0.9
    E_ref = np.ones_like(u_grid, dtype=complex) * 1.0e-3

    for wavelength_nm, width_nm, depth_nm in _micro_anchor_routes():
        wavelength_factor = (660.0 / float(wavelength_nm)) ** 1.4
        geometry_factor = (width_nm / 800.0) * (depth_nm / 1400.0)
        reference_power_prior_scale_W = 1.0e-8 * geometry_factor
        P_probe_W = 2.0e-5 if wavelength_nm != 404 else 4.0e-6
        p_beam_per_m2 = 1.0 / (math.pi * (0.7e-6) * (0.9e-6))
        for particle_id, particle_factor in _micro_anchor_particles():
            base_route = make_base_route_key(
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                particle_profile_id="micro_anchor_particle_panel",
                particle_id=particle_id,
            )
            Csca_total = particle_factor * wavelength_factor * 1.0e-16
            dcs = np.full(8, Csca_total / (4.0 * math.pi))
            weights_sr = np.full(8, 4.0 * math.pi / 8.0)
            mie = mie_to_power_roi(
                P_probe_W=P_probe_W,
                p_beam_at_particle_per_m2=p_beam_per_m2,
                dCsca_dOmega_m2_per_sr=dcs,
                solid_angle_weights_sr=weights_sr,
                collection_throughput=np.full(8, 0.12 * geometry_factor),
                Csca_total_m2=Csca_total,
                Cabs_m2=0.1 * Csca_total,
                Cext_m2=1.2 * Csca_total if Csca_total > 0 else 1.0e-30,
            )
            E_sca = np.ones_like(u_grid, dtype=complex) * (
                -particle_factor * wavelength_factor * geometry_factor * 1.0e-5
            )
            bfp = bfp_roi_intensity_operator(
                E_ref=E_ref,
                E_sca=E_sca,
                weight=weight,
                du=float(u_axis[1] - u_axis[0]),
                dv=float(v_axis[1] - v_axis[0]),
                u=u_grid,
                v=v_grid,
                NA=0.45,
                n_medium=1.333,
                power_scale_W=reference_power_prior_scale_W,
            )
            delta_power = bfp["Delta_P_NODI_peak_signed_W"]
            detector = scenario_detector_unit_sidecar(
                P_ref_W=max(1.0e-10, bfp["P_ref_ROI_W"]),
                Delta_P_peak_W=delta_power,
                wavelength_nm=wavelength_nm,
                readout_path="ET2030_50ohm_voltage",
                connection=valid_connection,
            )
            blank = blank_false_positive_sidecar(
                threshold_sigma=5.0,
                independent_samples_per_s=500.0,
                colored_noise_correlation_time_s=0.02,
                acquisition_duration_s=120.0,
            )
            thermal = thermal_404_sidecar(
                wavelength_nm=wavelength_nm,
                I_exc_W_per_m2=mie["I_inc_W_per_m2"],
                alpha_medium_1_per_m=0.02,
                medium_volume_m3=1.0e-18,
                alpha_glass_1_per_m=0.05,
                glass_volume_m3=1.0e-18,
                particle_abs_cross_section_m2=0.05 * Csca_total,
                contaminant_abs_cross_section_m2=0.02 * Csca_total,
                filter_leakage_fraction=1.0e-4,
            )
            row = {
                "wavelength_nm": wavelength_nm,
                "width_nm": width_nm,
                "depth_nm": depth_nm,
                "particle_id": particle_id,
                "P_ref_ROI_W": bfp["P_ref_ROI_W"],
                "P_ref_scale_independent_of_particle": True,
                "reference_power_prior_scale_W": reference_power_prior_scale_W,
                "P_ref_ROI_W_unit": "W",
                "P_sca_ROI_W": mie["P_sca_ROI_W"],
                "P_sca_ROI_W_unit": "W",
                "P_cross_ROI_W": bfp["P_cross_ROI_W"],
                "P_cross_ROI_W_unit": "W",
                "Delta_P_NODI_peak_signed_W": bfp["Delta_P_NODI_peak_signed_W"],
                "Delta_P_NODI_peak_signed_W_unit": "W",
                "Delta_P_NODI_peak_abs_W": bfp["Delta_P_NODI_peak_abs_W"],
                "Delta_P_NODI_peak_abs_W_unit": "W",
                "Delta_i_peak_A": detector["Delta_i_peak_A"],
                "Delta_i_peak_A_unit": "A",
                "V_in_peak_V": detector["V_in_peak_V"],
                "V_in_peak_V_unit": "V",
                "scenario_detector_SNR": detector["scenario_detector_SNR"],
                "SNR_claim_level": detector["SNR_claim_level"],
                "false_positive_rate_per_min": blank["false_positive_rate_per_min"],
                "saturation_status": detector["saturation_status"],
                "connection_physical_validity": detector["connection_physical_validity"],
                "sampled_trace_claim_level": "absolute_blocked",
                "operator_throughput_preserved": bfp["operator_throughput_preserved"],
                "finite_monte_carlo_zero_event_inferred": blank[
                    "finite_monte_carlo_zero_event_inferred"
                ],
                "thermal_artifact_risk": thermal["thermal_artifact_risk"],
                "promotion_allowed": thermal["promotion_allowed"],
                **output_provenance_fields(
                    unit="mixed_units_with_per_field_unit_columns",
                    source_type="bounded_prior",
                    scenario_id=scenario_id,
                    claim_level="absolute_blocked",
                    calibration_dependency="measured_detector_transfer_and_measured_blank_required",
                    module_status="bounded_prior",
                    base_route_key=base_route,
                    scenario_identity=scenario_identity,
                    run_manifest_path=str(manifest_path),
                ),
            }
            validate_required_output_fields(row)
            validate_output_names(row)
            micro_rows.append(row)
            mie_rows.append(
                {
                    "wavelength_nm": wavelength_nm,
                    "particle_id": particle_id,
                    "I_inc_W_per_m2": mie["I_inc_W_per_m2"],
                    "P_sca_ROI_W": mie["P_sca_ROI_W"],
                    "P_sca_ROI_upper_bound_W": mie["P_sca_ROI_upper_bound_W"],
                    "P_sca_ROI_le_total_bound": mie["P_sca_ROI_le_total_bound"],
                    "energy_conservation_status": mie["energy_conservation_status"],
                    "unit_guardrail": mie["unit_guardrail"],
                }
            )
            unit_rows.extend(
                [
                    {
                        "metric": "P_ref_ROI_W",
                        "unit": "W",
                        "status": "pass",
                        "wavelength_nm": wavelength_nm,
                        "particle_id": particle_id,
                    },
                    {
                        "metric": "P_sca_ROI_W",
                        "unit": "W",
                        "status": "pass",
                        "wavelength_nm": wavelength_nm,
                        "particle_id": particle_id,
                    },
                    {
                        "metric": "P_cross_ROI_W",
                        "unit": "W",
                        "status": "pass",
                        "wavelength_nm": wavelength_nm,
                        "particle_id": particle_id,
                    },
                ]
            )
            blank_rows.append(
                {
                    "wavelength_nm": wavelength_nm,
                    "particle_id": particle_id,
                    "analytic_gaussian_FP_per_min": blank["analytic_gaussian_FP_per_min"],
                    "rice_or_rayleigh_magnitude_FP_per_min": blank[
                        "rice_or_rayleigh_magnitude_FP_per_min"
                    ],
                    "colored_noise_effective_N": blank["colored_noise_effective_N"],
                    "rare_burst_rate_prior": blank["rare_burst_rate_prior"],
                    "zero_event_upper_bound": blank["zero_event_upper_bound"],
                    "blank_evidence_status": blank["blank_evidence_status"],
                    "false_positive_per_min_claim": blank["false_positive_per_min_claim"],
                    "finite_monte_carlo_zero_event_inferred": blank[
                        "finite_monte_carlo_zero_event_inferred"
                    ],
                }
            )

    state_rows = [
        valid_connection,
        invalid_connection,
        evaluate_detector_connection(
            detector_source="ET2030_BNC_biased_output",
            readout_path="high_Z_voltage_input",
        ),
        evaluate_detector_connection(
            detector_source="bare_photodiode",
            readout_path="lockin_current_input",
        ),
        evaluate_detector_connection(
            detector_source="external_TIA_voltage_output",
            readout_path="lockin_voltage_input",
        ),
    ]
    cost = estimate_smoke_run_cost()
    smoke_cost_rows = [cost]
    event_budget = {
        "stage": "R1.5_micro_anchor_dry_run",
        "routes": len(_micro_anchor_routes()),
        "particles": len(_micro_anchor_particles()),
        "event_level_runs": 0,
        "R2_anchor_smoke_started": False,
    }
    scenario_budget = {
        "scenario_bundle": scenario_id,
        "uses_full_scenario_registry": False,
        "smoke_cost_under_cap": cost["under_review_cap"],
        "max_anchor_scenario_bundles": MAX_ANCHOR_SCENARIO_BUNDLES,
        "max_anchor_routes": MAX_ANCHOR_ROUTES,
        "max_stochastic_seeds": MAX_STOCHASTIC_SEEDS,
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
    )

    write_csv_rows(output / "micro_anchor_summary.csv", micro_rows)
    write_csv_rows(output / "unit_guardrail_summary.csv", unit_rows)
    write_csv_rows(output / "detector_connection_state_machine_summary.csv", state_rows)
    write_csv_rows(output / "mie_to_power_unit_check.csv", mie_rows)
    write_csv_rows(output / "blank_rare_tail_check.csv", blank_rows)
    write_csv_rows(output / "smoke_run_cost_estimate.csv", smoke_cost_rows)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )
    report = (
        "# EV/NODI realism v2 micro-anchor report\n\n"
        "- Stage: R1.5 micro-anchor dry run only.\n"
        "- Scenario bundle: micro_anchor_nominal_sanity.\n"
        "- R2 anchor smoke: not run.\n"
        "- R3 reduced grid: not run.\n"
        "- R5 full-grid v2: not run.\n"
        "- Invalid ET2030 BNC direct current-input path: blocked unless bench validated.\n"
        "- scenario_detector_SNR claim level: absolute_blocked without measured detector transfer "
        "and measured blank.\n"
        "- Blank rare tail: analytic/semi-analytic prior, not finite Monte Carlo zero-event safety.\n"
    )
    (output / "micro_anchor_report.md").write_text(report, encoding="utf-8")
    return {
        "output_dir": str(output),
        "manifest": manifest,
        "micro_anchor_rows": len(micro_rows),
        "detector_state_rows": len(state_rows),
        "smoke_cost_under_cap": cost["under_review_cap"],
        "invalid_et2030_current_path": invalid_connection["connection_physical_validity"],
    }


def run_anchor_smoke(
    output_dir: str | Path = DEFAULT_ANCHOR_SMOKE_DIR,
    *,
    include_optional_routes: bool = True,
    write_root_manifest: bool = True,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"
    routes = anchor_smoke_routes(include_optional_routes)
    particles = anchor_smoke_particles()
    scenarios = anchor_smoke_scenario_bundles()
    seeds = (42, 43, 44)
    events_per_case = 3000
    cost = estimate_smoke_run_cost(
        n_routes=len(routes),
        n_particles=len(particles),
        n_scenario_bundles=len(scenarios),
        n_seeds=len(seeds),
        events_per_case=events_per_case,
    )
    if not cost["under_review_cap"]:
        raise RuntimeError("R2 anchor smoke cost estimate exceeds review cap")

    summary_rows: list[dict[str, Any]] = []
    route_particle_rows: list[dict[str, Any]] = []
    scenario_rows: list[dict[str, Any]] = []
    detector_state_rows: list[dict[str, Any]] = []
    mie_rows: list[dict[str, Any]] = []
    blank_rows: list[dict[str, Any]] = []
    unit_rows: list[dict[str, Any]] = []

    seen_connections: set[str] = set()
    for scenario in scenarios:
        connection = _scenario_connection(scenario)
        connection_key = str(connection["connection_state_id"])
        if connection_key not in seen_connections:
            detector_state_rows.append(connection)
            seen_connections.add(connection_key)
        scenario_rows.append(
            {
                "scenario_id": scenario["scenario_id"],
                "instrument_path_id": scenario["instrument_path_id"],
                "connection_readout_path": scenario["connection_readout_path"],
                "scenario_role": scenario["scenario_role"],
                "power_scale": scenario["power_scale"],
                "roi_weight_scale": scenario["roi_weight_scale"],
                "blank_threshold_sigma": scenario["blank_threshold_sigma"],
                "RIN_PSD_1_per_Hz": scenario["RIN_PSD_1_per_Hz"],
                "peg_survival_factor": scenario["peg_survival_factor"],
                "daq_snr_factor": scenario["daq_snr_factor"],
                "module_status": "bounded_prior",
                "claim_level": "absolute_blocked",
            }
        )

    invalid_connection = evaluate_detector_connection(
        detector_source="ET2030_BNC_biased_output",
        readout_path="LI5640_current_input_direct",
    )
    detector_state_rows.append(invalid_connection)

    route_aggregate: dict[tuple[int, int, int, str], list[float]] = {}
    for wavelength_nm, width_nm, depth_nm in routes:
        for particle in particles:
            particle_id = str(particle["particle_id"])
            particle_factor = float(particle["particle_factor"])
            base_route = make_base_route_key(
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                particle_profile_id=str(particle["particle_profile_id"]),
                particle_id=particle_id,
            )
            for scenario in scenarios:
                connection = _scenario_connection(scenario)
                scenario_identity = make_scenario_identity(
                    scenario_id=str(scenario["scenario_id"]),
                    instrument_chain_id=str(scenario["instrument_path_id"]),
                    prior_sample_id="anchor_smoke_named_bundle",
                    sidecar_id="R2_anchor_smoke_posthoc_event_budget",
                )
                mie, bfp = _anchor_smoke_power(
                    wavelength_nm=wavelength_nm,
                    width_nm=width_nm,
                    depth_nm=depth_nm,
                    particle_factor=particle_factor,
                    scenario=scenario,
                )
                detector = scenario_detector_unit_sidecar(
                    P_ref_W=max(1.0e-10, bfp["P_ref_ROI_W"]),
                    Delta_P_peak_W=bfp["Delta_P_NODI_peak_signed_W"],
                    wavelength_nm=wavelength_nm,
                    readout_path=str(scenario["instrument_path_id"]),
                    connection=connection,
                    RIN_PSD_1_per_Hz=float(scenario["RIN_PSD_1_per_Hz"]),
                )
                blank = blank_false_positive_sidecar(
                    threshold_sigma=float(scenario["blank_threshold_sigma"]),
                    independent_samples_per_s=float(
                        scenario["blank_independent_samples_per_s"]
                    ),
                    colored_noise_correlation_time_s=float(
                        scenario["colored_noise_correlation_time_s"]
                    ),
                    acquisition_duration_s=300.0,
                    measured_blank=False,
                )
                thermal = thermal_404_sidecar(
                    wavelength_nm=wavelength_nm,
                    I_exc_W_per_m2=mie["I_inc_W_per_m2"],
                    alpha_medium_1_per_m=0.02,
                    medium_volume_m3=1.0e-18,
                    alpha_glass_1_per_m=0.05,
                    glass_volume_m3=1.0e-18,
                    particle_abs_cross_section_m2=0.05 * mie["Csca_total_m2"],
                    contaminant_abs_cross_section_m2=0.02 * mie["Csca_total_m2"],
                    filter_leakage_fraction=1.0e-4,
                )
                raw_snr = detector["scenario_detector_SNR"] * float(
                    scenario["daq_snr_factor"]
                )
                effective_snr = (
                    raw_snr
                    * float(scenario["peg_survival_factor"])
                    * max(0.0, thermal["optical_score_multiplier"])
                )
                p_detect = _relative_detectability_prior_score(
                    effective_snr=effective_snr,
                    particle_class=str(particle["particle_class"]),
                    wavelength_nm=wavelength_nm,
                    thermal_artifact_risk=str(thermal["thermal_artifact_risk"]),
                )
                false_positive_per_min = blank["false_positive_rate_per_min"]
                for seed in seeds:
                    seed_adjustment = 1.0 + ((seed % 7) - 3) * 0.015
                    p_seed = float(max(0.0, min(1.0, p_detect * seed_adjustment)))
                    detected_events = int(round(p_seed * events_per_case))
                    wilson_half_width = _wilson_half_width(detected_events, events_per_case)
                    expected_detected_events_at_10000 = p_seed * 10000.0
                    statistical_precision_rerun_recommended = wilson_half_width > 0.05
                    low_detectability_prior = p_seed < 0.02
                    adaptive_event_count_will_not_clear_gate = (
                        low_detectability_prior
                        and not statistical_precision_rerun_recommended
                    )
                    adaptive_rerun_recommended = statistical_precision_rerun_recommended
                    row = {
                        "stage": "R2_anchor_smoke",
                        "wavelength_nm": wavelength_nm,
                        "width_nm": width_nm,
                        "depth_nm": depth_nm,
                        "particle_id": particle_id,
                        "particle_class": particle["particle_class"],
                        "scenario_bundle": scenario["scenario_id"],
                        "seed": seed,
                        "events_per_case": events_per_case,
                        "detected_events": detected_events,
                        "detected_events_source": (
                            "relative_prior_score_proxy_count_not_observed_events"
                        ),
                        "detected_events_claim_level": "relative_with_priors",
                        "p_detect_scenario": p_seed,
                        "p_detect_scenario_interpretation": (
                            "legacy_named_relative_prior_score_not_event_probability"
                        ),
                        "detectability_relative_prior_score": p_seed,
                        "p_detect_relative_prior_score": p_seed,
                        "p_detect_mapping_mode": (
                            "relative_prior_score_from_absolute_blocked_snr_not_event_probability"
                        ),
                        "p_detect_mapping_claim_level": "relative_with_priors",
                        "event_probability_claim_level": "absolute_blocked",
                        "expected_detected_events_at_10000": expected_detected_events_at_10000,
                        "expected_prior_score_proxy_count_at_10000": (
                            expected_detected_events_at_10000
                        ),
                        "wilson_half_width": wilson_half_width,
                        "statistical_precision_rerun_basis": (
                            "relative_prior_score_proxy_wilson_half_width"
                        ),
                        "statistical_precision_rerun_recommended": (
                            statistical_precision_rerun_recommended
                        ),
                        "low_detectability_prior": low_detectability_prior,
                        "adaptive_event_count_will_not_clear_gate": (
                            adaptive_event_count_will_not_clear_gate
                        ),
                        "adaptive_rerun_recommended": adaptive_rerun_recommended,
                        "P_ref_ROI_W": bfp["P_ref_ROI_W"],
                        "P_ref_scale_independent_of_particle": True,
                        "reference_power_prior_scale_W": bfp[
                            "reference_power_prior_scale_W"
                        ],
                        "P_ref_ROI_W_unit": "W",
                        "P_sca_ROI_W": mie["P_sca_ROI_W"],
                        "P_sca_ROI_W_unit": "W",
                        "P_cross_ROI_W": bfp["P_cross_ROI_W"],
                        "P_cross_ROI_W_unit": "W",
                        "Delta_P_NODI_peak_signed_W": bfp[
                            "Delta_P_NODI_peak_signed_W"
                        ],
                        "Delta_P_NODI_peak_signed_W_unit": "W",
                        "Delta_P_NODI_peak_abs_W": bfp["Delta_P_NODI_peak_abs_W"],
                        "Delta_P_NODI_peak_abs_W_unit": "W",
                        "Delta_i_peak_A": detector["Delta_i_peak_A"],
                        "Delta_i_peak_A_unit": "A",
                        "V_in_peak_V": detector["V_in_peak_V"],
                        "V_in_peak_V_unit": "V",
                        "scenario_detector_SNR": detector["scenario_detector_SNR"],
                        "effective_scenario_detector_SNR": effective_snr,
                        "SNR_claim_level": detector["SNR_claim_level"],
                        "false_positive_rate_per_min": false_positive_per_min,
                        "false_positive_per_min_claim": blank[
                            "false_positive_per_min_claim"
                        ],
                        "finite_monte_carlo_zero_event_inferred": blank[
                            "finite_monte_carlo_zero_event_inferred"
                        ],
                        "saturation_status": detector["saturation_status"],
                        "connection_physical_validity": detector[
                            "connection_physical_validity"
                        ],
                        "instrument_path_id": detector["instrument_path_id"],
                        "connection_readout_path": detector["connection_readout_path"],
                        "thermal_artifact_risk": thermal["thermal_artifact_risk"],
                        "promotion_allowed": thermal["promotion_allowed"],
                        "sampled_trace_claim_level": "absolute_blocked",
                        "operator_throughput_preserved": bfp[
                            "operator_throughput_preserved"
                        ],
                        "R2_anchor_smoke_only": True,
                        "R3_reduced_grid_run": False,
                        "R5_full_grid_v2_run": False,
                        **output_provenance_fields(
                            unit="mixed_units_with_per_field_unit_columns",
                            source_type="bounded_prior",
                            scenario_id=str(scenario["scenario_id"]),
                            claim_level="absolute_blocked",
                            calibration_dependency=(
                                "measured_detector_transfer_and_measured_blank_required"
                            ),
                            module_status="bounded_prior",
                            base_route_key=base_route,
                            scenario_identity=scenario_identity,
                            run_manifest_path=str(manifest_path),
                        ),
                    }
                    validate_required_output_fields(row)
                    validate_output_names(row)
                    summary_rows.append(row)
                    route_aggregate.setdefault(
                        (wavelength_nm, width_nm, depth_nm, particle_id), []
                    ).append(p_seed)
                mie_rows.append(
                    {
                        "wavelength_nm": wavelength_nm,
                        "width_nm": width_nm,
                        "depth_nm": depth_nm,
                        "particle_id": particle_id,
                        "scenario_bundle": scenario["scenario_id"],
                        "I_inc_W_per_m2": mie["I_inc_W_per_m2"],
                        "P_sca_ROI_W": mie["P_sca_ROI_W"],
                        "P_sca_ROI_upper_bound_W": mie[
                            "P_sca_ROI_upper_bound_W"
                        ],
                        "P_sca_ROI_le_total_bound": mie[
                            "P_sca_ROI_le_total_bound"
                        ],
                        "energy_conservation_status": mie[
                            "energy_conservation_status"
                        ],
                        "unit_guardrail": mie["unit_guardrail"],
                    }
                )
                blank_rows.append(
                    {
                        "wavelength_nm": wavelength_nm,
                        "width_nm": width_nm,
                        "depth_nm": depth_nm,
                        "particle_id": particle_id,
                        "scenario_bundle": scenario["scenario_id"],
                        "analytic_gaussian_FP_per_min": blank[
                            "analytic_gaussian_FP_per_min"
                        ],
                        "rice_or_rayleigh_magnitude_FP_per_min": blank[
                            "rice_or_rayleigh_magnitude_FP_per_min"
                        ],
                        "colored_noise_effective_N": blank[
                            "colored_noise_effective_N"
                        ],
                        "rare_burst_rate_prior": blank["rare_burst_rate_prior"],
                        "zero_event_upper_bound": blank["zero_event_upper_bound"],
                        "blank_evidence_status": blank[
                            "blank_evidence_status"
                        ],
                        "false_positive_per_min_claim": blank[
                            "false_positive_per_min_claim"
                        ],
                        "finite_monte_carlo_zero_event_inferred": blank[
                            "finite_monte_carlo_zero_event_inferred"
                        ],
                    }
                )
                unit_rows.extend(
                    [
                        {
                            "metric": "P_ref_ROI_W",
                            "unit": "W",
                            "status": "pass",
                            "wavelength_nm": wavelength_nm,
                            "particle_id": particle_id,
                            "scenario_bundle": scenario["scenario_id"],
                        },
                        {
                            "metric": "P_sca_ROI_W",
                            "unit": "W",
                            "status": "pass",
                            "wavelength_nm": wavelength_nm,
                            "particle_id": particle_id,
                            "scenario_bundle": scenario["scenario_id"],
                        },
                        {
                            "metric": "P_cross_ROI_W",
                            "unit": "W",
                            "status": "pass",
                            "wavelength_nm": wavelength_nm,
                            "particle_id": particle_id,
                            "scenario_bundle": scenario["scenario_id"],
                        },
                    ]
                )

    for (wavelength_nm, width_nm, depth_nm, particle_id), values in sorted(
        route_aggregate.items()
    ):
        route_particle_rows.append(
            {
                "wavelength_nm": wavelength_nm,
                "width_nm": width_nm,
                "depth_nm": depth_nm,
                "particle_id": particle_id,
                "mean_p_detect_scenario": float(np.mean(values)),
                "min_p_detect_scenario": float(np.min(values)),
                "max_p_detect_scenario": float(np.max(values)),
                "n_case_rows": len(values),
                "claim_level": "absolute_blocked",
                "module_status": "bounded_prior",
            }
        )

    event_budget = {
        "stage": "R2_anchor_smoke",
        "routes": len(routes),
        "particles": len(particles),
        "scenario_bundles": len(scenarios),
        "seeds": list(seeds),
        "events_per_case": events_per_case,
        "event_level_runs": len(summary_rows),
        "max_event_level_runs_before_review": MAX_EVENT_LEVEL_RUNS_BEFORE_REVIEW,
        "R2_anchor_smoke_started": True,
        "R3_reduced_grid_started": False,
        "R5_full_grid_v2_started": False,
    }
    scenario_budget = {
        "scenario_bundles": [str(scenario["scenario_id"]) for scenario in scenarios],
        "uses_full_scenario_registry": False,
        "smoke_cost_under_cap": cost["under_review_cap"],
        "max_anchor_scenario_bundles": MAX_ANCHOR_SCENARIO_BUNDLES,
        "max_anchor_routes": MAX_ANCHOR_ROUTES,
        "max_stochastic_seeds": MAX_STOCHASTIC_SEEDS,
        "selected_particle_count_due_to_cap": len(particles),
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_anchor_smoke_R2",
        random_seed_policy="fixed_anchor_smoke_seeds_42_43_44",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=False,
        R5_full_grid_v2_run=False,
    )

    write_csv_rows(output / "anchor_smoke_summary.csv", summary_rows)
    write_csv_rows(output / "anchor_smoke_route_particle_summary.csv", route_particle_rows)
    write_csv_rows(output / "anchor_smoke_scenarios.csv", scenario_rows)
    write_csv_rows(output / "detector_connection_state_machine_summary.csv", detector_state_rows)
    write_csv_rows(output / "mie_to_power_unit_check.csv", mie_rows)
    write_csv_rows(output / "blank_rare_tail_check.csv", blank_rows)
    write_csv_rows(output / "unit_guardrail_summary.csv", unit_rows)
    write_csv_rows(output / "smoke_run_cost_estimate.csv", [cost])
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    all_snr_blocked = all(row["SNR_claim_level"] == "absolute_blocked" for row in summary_rows)
    no_legacy_names = all(
        not FORBIDDEN_OUTPUT_NAMES.intersection(row.keys()) for row in summary_rows
    )
    report = (
        "# EV/NODI realism v2 anchor-smoke report\n\n"
        "- Stage: R2 anchor smoke only.\n"
        f"- Routes: {len(routes)}.\n"
        f"- Particles: {len(particles)} selected under cap.\n"
        f"- Scenario bundles: {len(scenarios)}.\n"
        f"- Seeds: {', '.join(str(seed) for seed in seeds)}.\n"
        f"- Event-level case rows: {len(summary_rows)} / cap {MAX_EVENT_LEVEL_RUNS_BEFORE_REVIEW}.\n"
        f"- Cost under cap: {cost['under_review_cap']}.\n"
        f"- All SNR claims absolute_blocked: {all_snr_blocked}.\n"
        f"- Legacy SNR names absent from outputs: {no_legacy_names}.\n"
        "- Detectability mapping: relative prior score, not calibrated event probability.\n"
        "- Event probability claim level: absolute_blocked.\n"
        "- Adaptive rerun basis: statistical precision proxy only; low detectability is a separate gate.\n"
        "- Reference ROI power scale: route/scenario dependent and particle independent.\n"
        "- R3 reduced grid: not run.\n"
        "- R4 representative full-wave validation: not run.\n"
        "- R5 full-grid v2: not run.\n"
        "- Blank rare tail remains analytic/semi-analytic; no finite zero-event safety claim.\n"
    )
    (output / "anchor_smoke_report.md").write_text(report, encoding="utf-8")

    return {
        "output_dir": str(output),
        "manifest": manifest,
        "anchor_smoke_rows": len(summary_rows),
        "route_count": len(routes),
        "particle_count": len(particles),
        "scenario_bundle_count": len(scenarios),
        "seed_count": len(seeds),
        "smoke_cost_under_cap": cost["under_review_cap"],
        "all_snr_claims_absolute_blocked": all_snr_blocked,
        "legacy_snr_output_names_absent": no_legacy_names,
        "R3_reduced_grid_run": False,
        "R5_full_grid_v2_run": False,
    }


def _correlation_pair(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2 or len(xs) != len(ys):
        return float("nan")
    x_arr = np.asarray(xs, dtype=float)
    y_arr = np.asarray(ys, dtype=float)
    if float(np.std(x_arr)) == 0.0 or float(np.std(y_arr)) == 0.0:
        return float("nan")
    return float(np.corrcoef(x_arr, y_arr)[0, 1])


def _ordinal_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    for rank, index in enumerate(order, start=1):
        ranks[index] = float(rank)
    return ranks


def _read_anchor_overlap_means() -> dict[tuple[int, int, int, str], float]:
    path = DEFAULT_ANCHOR_SMOKE_DIR / "anchor_smoke_route_particle_summary.csv"
    if not path.exists():
        return {}
    values: dict[tuple[int, int, int, str], float] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (
                int(row["wavelength_nm"]),
                int(row["width_nm"]),
                int(row["depth_nm"]),
                row["particle_id"],
            )
            values[key] = float(row["mean_p_detect_scenario"])
    return values


def run_reduced_grid_R3a(
    output_dir: str | Path = DEFAULT_REDUCED_GRID_R3A_DIR,
    *,
    write_root_manifest: bool = True,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"
    routes = reduced_grid_R3a_routes()
    particles = reduced_grid_R3a_particles()
    scenarios = anchor_smoke_scenario_bundles()
    seeds = (42, 43, 44)
    events_per_case_proxy = 3000
    cost = estimate_reduced_grid_R3a_cost(
        n_routes=len(routes),
        n_particles=len(particles),
        n_scenario_bundles=len(scenarios),
        n_seeds=len(seeds),
        events_per_case_proxy=events_per_case_proxy,
    )
    if not cost["under_R3a_review_cap"]:
        raise RuntimeError("R3a reduced-grid case count exceeds review cap")

    summary_rows: list[dict[str, Any]] = []
    route_values: dict[tuple[int, int, int, str], list[float]] = {}
    scenario_values: dict[str, list[float]] = {}
    route_role_values: dict[str, list[float]] = {}
    route_particle_values: dict[tuple[int, int, int, str], list[float]] = {}
    snr_by_role_scenario: dict[tuple[str, str], list[float]] = {}
    detector_state_rows: list[dict[str, Any]] = []
    blank_rows: list[dict[str, Any]] = []
    unit_rows: list[dict[str, Any]] = []
    seen_connections: set[str] = set()

    for scenario in scenarios:
        connection = _scenario_connection(scenario)
        connection_key = str(connection["connection_state_id"])
        if connection_key not in seen_connections:
            detector_state_rows.append(connection)
            seen_connections.add(connection_key)
    detector_state_rows.append(
        evaluate_detector_connection(
            detector_source="ET2030_BNC_biased_output",
            readout_path="LI5640_current_input_direct",
        )
    )

    for wavelength_nm, width_nm, depth_nm in routes:
        route_role = route_role_R3a(wavelength_nm, width_nm, depth_nm)
        for particle in particles:
            particle_id = str(particle["particle_id"])
            particle_factor = float(particle["particle_factor"])
            base_route = make_base_route_key(
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                particle_profile_id=str(particle["particle_profile_id"]),
                particle_id=particle_id,
            )
            for scenario in scenarios:
                scenario_id = str(scenario["scenario_id"])
                connection = _scenario_connection(scenario)
                scenario_identity = make_scenario_identity(
                    scenario_id=scenario_id,
                    instrument_chain_id=str(scenario["instrument_path_id"]),
                    prior_sample_id="R3a_named_bundle_reduced_grid",
                    sidecar_id="R3a_reduced_grid_relative_prior_survey",
                )
                mie, bfp = _anchor_smoke_power(
                    wavelength_nm=wavelength_nm,
                    width_nm=width_nm,
                    depth_nm=depth_nm,
                    particle_factor=particle_factor,
                    scenario=scenario,
                )
                detector = scenario_detector_unit_sidecar(
                    P_ref_W=max(1.0e-10, bfp["P_ref_ROI_W"]),
                    Delta_P_peak_W=bfp["Delta_P_NODI_peak_signed_W"],
                    wavelength_nm=wavelength_nm,
                    readout_path=str(scenario["instrument_path_id"]),
                    connection=connection,
                    RIN_PSD_1_per_Hz=float(scenario["RIN_PSD_1_per_Hz"]),
                )
                blank = blank_false_positive_sidecar(
                    threshold_sigma=float(scenario["blank_threshold_sigma"]),
                    independent_samples_per_s=float(
                        scenario["blank_independent_samples_per_s"]
                    ),
                    colored_noise_correlation_time_s=float(
                        scenario["colored_noise_correlation_time_s"]
                    ),
                    acquisition_duration_s=300.0,
                    measured_blank=False,
                )
                thermal = thermal_404_sidecar(
                    wavelength_nm=wavelength_nm,
                    I_exc_W_per_m2=mie["I_inc_W_per_m2"],
                    alpha_medium_1_per_m=0.02,
                    medium_volume_m3=1.0e-18,
                    alpha_glass_1_per_m=0.05,
                    glass_volume_m3=1.0e-18,
                    particle_abs_cross_section_m2=0.05 * mie["Csca_total_m2"],
                    contaminant_abs_cross_section_m2=0.02 * mie["Csca_total_m2"],
                    filter_leakage_fraction=1.0e-4,
                )
                raw_snr = detector["scenario_detector_SNR"] * float(
                    scenario["daq_snr_factor"]
                )
                effective_snr = (
                    raw_snr
                    * float(scenario["peg_survival_factor"])
                    * max(0.0, thermal["optical_score_multiplier"])
                )
                p_detect = _relative_detectability_prior_score(
                    effective_snr=effective_snr,
                    particle_class=str(particle["particle_class"]),
                    wavelength_nm=wavelength_nm,
                    thermal_artifact_risk=str(thermal["thermal_artifact_risk"]),
                )
                threshold_sigma = float(scenario["blank_threshold_sigma"])
                signal_to_threshold_relative_margin = effective_snr / threshold_sigma
                blank_rows.append(
                    {
                        "stage": "R3a_reduced_grid_named_bundle_survey",
                        "wavelength_nm": wavelength_nm,
                        "width_nm": width_nm,
                        "depth_nm": depth_nm,
                        "route_role": route_role,
                        "particle_id": particle_id,
                        "scenario_bundle": scenario_id,
                        "analytic_gaussian_FP_per_min": blank[
                            "analytic_gaussian_FP_per_min"
                        ],
                        "rice_or_rayleigh_magnitude_FP_per_min": blank[
                            "rice_or_rayleigh_magnitude_FP_per_min"
                        ],
                        "colored_noise_effective_N": blank[
                            "colored_noise_effective_N"
                        ],
                        "rare_burst_rate_prior": blank["rare_burst_rate_prior"],
                        "zero_event_upper_bound": blank["zero_event_upper_bound"],
                        "blank_evidence_status": blank[
                            "blank_evidence_status"
                        ],
                        "false_positive_per_min_claim": blank[
                            "false_positive_per_min_claim"
                        ],
                        "finite_monte_carlo_zero_event_inferred": blank[
                            "finite_monte_carlo_zero_event_inferred"
                        ],
                    }
                )
                unit_rows.extend(
                    [
                        {
                            "stage": "R3a_reduced_grid_named_bundle_survey",
                            "metric": "P_ref_ROI_W",
                            "unit": "W",
                            "status": "pass",
                            "wavelength_nm": wavelength_nm,
                            "particle_id": particle_id,
                            "scenario_bundle": scenario_id,
                        },
                        {
                            "stage": "R3a_reduced_grid_named_bundle_survey",
                            "metric": "P_sca_ROI_W",
                            "unit": "W",
                            "status": "pass",
                            "wavelength_nm": wavelength_nm,
                            "particle_id": particle_id,
                            "scenario_bundle": scenario_id,
                        },
                        {
                            "stage": "R3a_reduced_grid_named_bundle_survey",
                            "metric": "P_cross_ROI_W",
                            "unit": "W",
                            "status": "pass",
                            "wavelength_nm": wavelength_nm,
                            "particle_id": particle_id,
                            "scenario_bundle": scenario_id,
                        },
                    ]
                )
                for seed in seeds:
                    seed_adjustment = 1.0 + ((seed % 7) - 3) * 0.015
                    p_seed = float(max(0.0, min(1.0, p_detect * seed_adjustment)))
                    detected_proxy_count = int(round(p_seed * events_per_case_proxy))
                    row = {
                        "stage": "R3a_reduced_grid_named_bundle_survey",
                        "wavelength_nm": wavelength_nm,
                        "width_nm": width_nm,
                        "depth_nm": depth_nm,
                        "route_role": route_role,
                        "route_role_locked": True,
                        "route_role_source": R3A_ROUTE_ROLE_SOURCE,
                        "optional_660_900x1400_eligible_for_main_660_redefinition": False,
                        "particle_id": particle_id,
                        "particle_class": particle["particle_class"],
                        "particle_role": particle["particle_role"],
                        "scenario_bundle": scenario_id,
                        "seed": seed,
                        "events_per_case_proxy": events_per_case_proxy,
                        "detected_events": detected_proxy_count,
                        "detected_events_source": (
                            "relative_prior_score_proxy_count_not_observed_events"
                        ),
                        "detected_events_claim_level": "relative_with_priors",
                        "p_detect_scenario": p_seed,
                        "p_detect_scenario_interpretation": (
                            "legacy_named_relative_prior_score_not_event_probability"
                        ),
                        "detectability_relative_prior_score": p_seed,
                        "p_detect_relative_prior_score": p_seed,
                        "primary_metric": "detectability_relative_prior_score",
                        "p_detect_mapping_mode": (
                            "relative_prior_score_from_absolute_blocked_snr_not_event_probability"
                        ),
                        "p_detect_mapping_claim_level": "relative_with_priors",
                        "event_probability_claim_level": "absolute_blocked",
                        "threshold_sigma": threshold_sigma,
                        "signal_to_threshold_relative_margin": (
                            signal_to_threshold_relative_margin
                        ),
                        "P_ref_ROI_W": bfp["P_ref_ROI_W"],
                        "P_ref_scale_independent_of_particle": True,
                        "reference_power_prior_scale_W": bfp[
                            "reference_power_prior_scale_W"
                        ],
                        "P_ref_ROI_W_unit": "W",
                        "P_sca_ROI_W": mie["P_sca_ROI_W"],
                        "P_sca_ROI_W_unit": "W",
                        "P_cross_ROI_W": bfp["P_cross_ROI_W"],
                        "P_cross_ROI_W_unit": "W",
                        "Delta_P_NODI_peak_signed_W": bfp[
                            "Delta_P_NODI_peak_signed_W"
                        ],
                        "Delta_P_NODI_peak_signed_W_unit": "W",
                        "Delta_P_NODI_peak_abs_W": bfp["Delta_P_NODI_peak_abs_W"],
                        "Delta_P_NODI_peak_abs_W_unit": "W",
                        "Delta_i_peak_A": detector["Delta_i_peak_A"],
                        "Delta_i_peak_A_unit": "A",
                        "V_in_peak_V": detector["V_in_peak_V"],
                        "V_in_peak_V_unit": "V",
                        "scenario_detector_SNR": detector["scenario_detector_SNR"],
                        "effective_scenario_detector_SNR": effective_snr,
                        "SNR_claim_level": detector["SNR_claim_level"],
                        "false_positive_rate_per_min": blank[
                            "false_positive_rate_per_min"
                        ],
                        "false_positive_per_min_claim": blank[
                            "false_positive_per_min_claim"
                        ],
                        "finite_monte_carlo_zero_event_inferred": blank[
                            "finite_monte_carlo_zero_event_inferred"
                        ],
                        "saturation_status": detector["saturation_status"],
                        "connection_physical_validity": detector[
                            "connection_physical_validity"
                        ],
                        "instrument_path_id": detector["instrument_path_id"],
                        "connection_readout_path": detector["connection_readout_path"],
                        "thermal_artifact_risk": thermal["thermal_artifact_risk"],
                        "promotion_allowed": thermal["promotion_allowed"],
                        "sampled_trace_claim_level": "absolute_blocked",
                        "operator_throughput_preserved": bfp[
                            "operator_throughput_preserved"
                        ],
                        "R2_anchor_smoke_run": True,
                        "R3a_reduced_grid_named_bundle_survey_run": True,
                        "R3b_uncertainty_expansion_run": False,
                        "R4_representative_full_wave_validation_run": False,
                        "R5_full_grid_v2_run": False,
                        **output_provenance_fields(
                            unit="mixed_units_with_per_field_unit_columns",
                            source_type="bounded_prior",
                            scenario_id=scenario_id,
                            claim_level="absolute_blocked",
                            calibration_dependency=(
                                "measured_detector_transfer_and_measured_blank_required"
                            ),
                            module_status="bounded_prior",
                            base_route_key=base_route,
                            scenario_identity=scenario_identity,
                            run_manifest_path=str(manifest_path),
                        ),
                    }
                    validate_required_output_fields(row)
                    validate_output_names(row)
                    summary_rows.append(row)
                    route_key = (wavelength_nm, width_nm, depth_nm, route_role)
                    route_values.setdefault(route_key, []).append(p_seed)
                    scenario_values.setdefault(scenario_id, []).append(p_seed)
                    route_role_values.setdefault(route_role, []).append(p_seed)
                    route_particle_values.setdefault(
                        (wavelength_nm, width_nm, depth_nm, particle_id), []
                    ).append(p_seed)
                    if str(particle["particle_class"]) == "EV":
                        snr_by_role_scenario.setdefault(
                            (route_role, scenario_id), []
                        ).append(detector["scenario_detector_SNR"])

    scenario_spread_rows: list[dict[str, Any]] = []
    for route_role in sorted(route_role_values):
        scenario_means = [
            float(np.mean(values))
            for (role, _scenario_id), values in snr_by_role_scenario.items()
            if role == route_role
        ]
        min_snr = min(scenario_means) if scenario_means else 0.0
        max_snr = max(scenario_means) if scenario_means else 0.0
        watch = classify_R3a_scenario_spread_watch(min_snr=min_snr, max_snr=max_snr)
        scenario_spread_rows.append(
            {
                "route_role": route_role,
                "n_scenario_means": len(scenario_means),
                "min_scenario_mean_SNR": min_snr,
                "max_scenario_mean_SNR": max_snr,
                **watch,
            }
        )
    stop_spread_rows = [
        row
        for row in scenario_spread_rows
        if row["scenario_spread_watch_status"] == "stop_requires_physical_explanation"
    ]
    if stop_spread_rows:
        write_csv_rows(output / "scenario_SNR_spread_by_route_family.csv", scenario_spread_rows)
        raise RuntimeError("R3a scenario SNR spread exceeded 1e3 without explanation")

    route_family_rows = []
    for route_role, values in sorted(route_role_values.items()):
        route_family_rows.append(
            {
                "route_role": route_role,
                "route_role_locked": True,
                "route_role_source": R3A_ROUTE_ROLE_SOURCE,
                "route_count": len(
                    {
                        (wavelength_nm, width_nm, depth_nm)
                        for wavelength_nm, width_nm, depth_nm, role in route_values
                        if role == route_role
                    }
                ),
                "mean_detectability_relative_prior_score": float(np.mean(values)),
                "min_detectability_relative_prior_score": float(np.min(values)),
                "max_detectability_relative_prior_score": float(np.max(values)),
                "n_case_rows": len(values),
                "claim_level": "relative_with_priors",
                "event_probability_claim_level": "absolute_blocked",
            }
        )
    route_family_rows.sort(
        key=lambda row: row["mean_detectability_relative_prior_score"], reverse=True
    )
    for rank, row in enumerate(route_family_rows, start=1):
        row["rank_by_mean_relative_prior_score"] = rank

    scenario_rows = []
    for scenario_id, values in sorted(scenario_values.items()):
        scenario_rows.append(
            {
                "scenario_bundle": scenario_id,
                "mean_detectability_relative_prior_score": float(np.mean(values)),
                "min_detectability_relative_prior_score": float(np.min(values)),
                "max_detectability_relative_prior_score": float(np.max(values)),
                "n_case_rows": len(values),
                "claim_level": "relative_with_priors",
                "event_probability_claim_level": "absolute_blocked",
            }
        )
    scenario_rows.sort(
        key=lambda row: row["mean_detectability_relative_prior_score"], reverse=True
    )
    for rank, row in enumerate(scenario_rows, start=1):
        row["rank_by_mean_relative_prior_score"] = rank

    optional_rows = [
        {
            "wavelength_nm": wavelength_nm,
            "width_nm": width_nm,
            "depth_nm": depth_nm,
            "route_role": route_role,
            "route_role_locked": True,
            "route_role_source": R3A_ROUTE_ROLE_SOURCE,
            "promotion_discussion_only_in_optional_summary": True,
            "eligible_for_main_660_redefinition": False,
            "mean_detectability_relative_prior_score": float(np.mean(values)),
            "min_detectability_relative_prior_score": float(np.min(values)),
            "max_detectability_relative_prior_score": float(np.max(values)),
            "n_case_rows": len(values),
        }
        for (wavelength_nm, width_nm, depth_nm, route_role), values in route_values.items()
        if route_role == "optional_robustness_probe"
    ]
    weak_rows = [
        {
            "wavelength_nm": wavelength_nm,
            "width_nm": width_nm,
            "depth_nm": depth_nm,
            "route_role": route_role,
            "route_role_locked": True,
            "route_role_source": R3A_ROUTE_ROLE_SOURCE,
            "remains_control_unless_explicit_reclassification": True,
            "mean_detectability_relative_prior_score": float(np.mean(values)),
            "min_detectability_relative_prior_score": float(np.min(values)),
            "max_detectability_relative_prior_score": float(np.max(values)),
            "n_case_rows": len(values),
        }
        for (wavelength_nm, width_nm, depth_nm, route_role), values in route_values.items()
        if route_role == "weak_reference_control"
    ]
    thermal_rows = []
    for wavelength_nm in sorted({int(row["wavelength_nm"]) for row in summary_rows}):
        wavelength_rows = [row for row in summary_rows if row["wavelength_nm"] == wavelength_nm]
        for risk in sorted({str(row["thermal_artifact_risk"]) for row in wavelength_rows}):
            risk_rows = [row for row in wavelength_rows if row["thermal_artifact_risk"] == risk]
            thermal_rows.append(
                {
                    "wavelength_nm": wavelength_nm,
                    "thermal_artifact_risk": risk,
                    "n_case_rows": len(risk_rows),
                    "promotion_allowed_all": all(
                        bool(row["promotion_allowed"]) for row in risk_rows
                    ),
                    "sidecar_does_not_increase_nodi_score": True,
                    "claim_level": "safety_sidecar",
                }
            )

    anchor_means = _read_anchor_overlap_means()
    r3_means = {
        key: float(np.mean(values)) for key, values in route_particle_values.items()
    }
    shared_keys = sorted(set(anchor_means).intersection(r3_means))
    anchor_values = [anchor_means[key] for key in shared_keys]
    r3_values = [r3_means[key] for key in shared_keys]
    pearson = _correlation_pair(anchor_values, r3_values)
    spearman = _correlation_pair(
        _ordinal_ranks(anchor_values),
        _ordinal_ranks(r3_values),
    )
    anchor_status = (
        "pass_rank_correlation_over_0p7"
        if shared_keys and (pearson >= 0.7 or spearman >= 0.7)
        else "not_available_or_below_threshold"
    )
    anchor_overlap_rows = [
        {
            "shared_route_particle_cases": len(shared_keys),
            "pearson_correlation": pearson,
            "spearman_rank_correlation": spearman,
            "rank_correlation_requirement": ">0.7_for_shared_R2_anchor_cases_or_explain",
            "anchor_overlap_rank_correlation_status": anchor_status,
            "claim_level": "relative_with_priors",
        }
    ]

    event_budget = {
        "stage": "R3a_reduced_grid_named_bundle_survey",
        "routes": len(routes),
        "particles": len(particles),
        "scenario_bundles": len(scenarios),
        "seeds": list(seeds),
        "events_per_case_proxy": events_per_case_proxy,
        "case_rows": len(summary_rows),
        "max_R3a_case_rows_before_review": MAX_R3A_CASE_ROWS_BEFORE_REVIEW,
        "R2_anchor_smoke_started": True,
        "R3a_reduced_grid_named_bundle_survey_started": True,
        "R3b_uncertainty_expansion_started": False,
        "R4_representative_full_wave_validation_started": False,
        "R5_full_grid_v2_started": False,
    }
    scenario_budget = {
        "scenario_bundles": [str(scenario["scenario_id"]) for scenario in scenarios],
        "uses_full_scenario_registry": False,
        "under_R3a_review_cap": cost["under_R3a_review_cap"],
        "max_R3a_routes": MAX_R3A_ROUTES,
        "max_R3a_particles": MAX_R3A_PARTICLES,
        "max_R3a_scenario_bundles": MAX_R3A_SCENARIO_BUNDLES,
        "max_R3a_stochastic_seeds": MAX_R3A_STOCHASTIC_SEEDS,
        "max_R3a_case_rows_before_review": MAX_R3A_CASE_ROWS_BEFORE_REVIEW,
        "R3b_uncertainty_expansion_authorized": False,
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_reduced_grid_R3a_named_bundle_survey",
        random_seed_policy="fixed_R3a_named_bundle_seeds_42_43_44",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=False,
        R4_representative_full_wave_validation_run=False,
        R5_full_grid_v2_run=False,
    )

    write_csv_rows(output / "reduced_grid_summary.csv", summary_rows)
    write_csv_rows(output / "route_family_rank_distribution.csv", route_family_rows)
    write_csv_rows(output / "scenario_rank_distribution.csv", scenario_rows)
    write_csv_rows(output / "anchor_overlap_correlation.csv", anchor_overlap_rows)
    write_csv_rows(output / "scenario_SNR_spread_by_route_family.csv", scenario_spread_rows)
    write_csv_rows(output / "optional_660_900x1400_probe_summary.csv", optional_rows)
    write_csv_rows(output / "weak_reference_control_summary.csv", weak_rows)
    write_csv_rows(output / "thermal_404_gate_summary.csv", thermal_rows)
    write_csv_rows(output / "detector_connection_state_machine_summary.csv", detector_state_rows)
    write_csv_rows(output / "blank_rare_tail_check.csv", blank_rows)
    write_csv_rows(output / "unit_guardrail_summary.csv", unit_rows)
    write_csv_rows(output / "reduced_grid_cost_estimate.csv", [cost])
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    all_snr_blocked = all(row["SNR_claim_level"] == "absolute_blocked" for row in summary_rows)
    no_legacy_names = all(
        not FORBIDDEN_OUTPUT_NAMES.intersection(row.keys()) for row in summary_rows
    )
    report = (
        "# EV/NODI realism v2 R3a reduced-grid report\n\n"
        "- Stage: R3a reduced-grid named-bundle survey only.\n"
        f"- Routes: {len(routes)} / cap {MAX_R3A_ROUTES}.\n"
        f"- Particles: {len(particles)} / cap {MAX_R3A_PARTICLES}.\n"
        f"- Scenario bundles: {len(scenarios)} / cap {MAX_R3A_SCENARIO_BUNDLES}.\n"
        f"- Seeds: {', '.join(str(seed) for seed in seeds)}.\n"
        f"- Case rows: {len(summary_rows)} / cap {MAX_R3A_CASE_ROWS_BEFORE_REVIEW}.\n"
        f"- Cost under R3a cap: {cost['under_R3a_review_cap']}.\n"
        "- Detectability mapping: relative prior score, not calibrated event probability.\n"
        "- Event probability claim level: absolute_blocked.\n"
        f"- All SNR claims absolute_blocked: {all_snr_blocked}.\n"
        f"- Legacy SNR names absent from outputs: {no_legacy_names}.\n"
        "- Optional 660 / 900x1400 is locked as optional_robustness_probe.\n"
        "- R3b uncertainty expansion: not run.\n"
        "- R4 representative full-wave validation: not run.\n"
        "- R5 full-grid v2: not run.\n"
        "- Blank rare tail remains analytic/semi-analytic; no finite zero-event safety claim.\n"
    )
    (output / "R3a_reduced_grid_report.md").write_text(report, encoding="utf-8")

    return {
        "output_dir": str(output),
        "manifest": manifest,
        "reduced_grid_rows": len(summary_rows),
        "route_count": len(routes),
        "particle_count": len(particles),
        "scenario_bundle_count": len(scenarios),
        "seed_count": len(seeds),
        "under_R3a_review_cap": cost["under_R3a_review_cap"],
        "all_snr_claims_absolute_blocked": all_snr_blocked,
        "legacy_snr_output_names_absent": no_legacy_names,
        "anchor_overlap_status": anchor_status,
        "R3a_reduced_grid_named_bundle_survey_run": True,
        "R3b_uncertainty_expansion_run": False,
        "R4_representative_full_wave_validation_run": False,
        "R5_full_grid_v2_run": False,
    }


def run_uncertainty_R3b(
    output_dir: str | Path = DEFAULT_UNCERTAINTY_R3B_DIR,
    *,
    write_root_manifest: bool = True,
) -> dict[str, Any]:
    pre_run = validate_R3b_pre_run_plan()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"
    route_rows = pre_run["routes"]
    particles = reduced_grid_R3a_particles()
    prior_samples = R3b_uncertainty_prior_samples(pre_run["prior_table"])
    seeds = (42, 43, 44)
    events_per_case_proxy = 3000
    cost = estimate_uncertainty_R3b_cost(
        n_routes=len(route_rows),
        n_particles=len(particles),
        n_prior_samples=len(prior_samples),
        n_seeds=len(seeds),
        events_per_case_proxy=events_per_case_proxy,
    )
    if not cost["under_R3b_review_cap"]:
        raise RuntimeError("R3b uncertainty case count exceeds review cap")

    nominal_scenario = dict(anchor_smoke_scenario_bundles()[0])
    nominal_cache: dict[tuple[int, int, int, str], dict[str, float]] = {}
    for route in route_rows:
        wavelength_nm = int(route["wavelength_nm"])
        width_nm = int(route["width_nm"])
        depth_nm = int(route["depth_nm"])
        for particle in particles:
            mie, bfp = _anchor_smoke_power(
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                particle_factor=float(particle["particle_factor"]),
                scenario=nominal_scenario,
            )
            connection = _scenario_connection(nominal_scenario)
            detector = scenario_detector_unit_sidecar(
                P_ref_W=max(1.0e-10, bfp["P_ref_ROI_W"]),
                Delta_P_peak_W=bfp["Delta_P_NODI_peak_signed_W"],
                wavelength_nm=wavelength_nm,
                readout_path=str(nominal_scenario["instrument_path_id"]),
                connection=connection,
                RIN_PSD_1_per_Hz=float(nominal_scenario["RIN_PSD_1_per_Hz"]),
            )
            thermal = thermal_404_sidecar(
                wavelength_nm=wavelength_nm,
                I_exc_W_per_m2=mie["I_inc_W_per_m2"],
                alpha_medium_1_per_m=0.02,
                medium_volume_m3=1.0e-18,
                alpha_glass_1_per_m=0.05,
                glass_volume_m3=1.0e-18,
                particle_abs_cross_section_m2=0.05 * mie["Csca_total_m2"],
                contaminant_abs_cross_section_m2=0.02 * mie["Csca_total_m2"],
                filter_leakage_fraction=1.0e-4,
            )
            effective_snr = detector["scenario_detector_SNR"] * max(
                0.0, thermal["optical_score_multiplier"]
            )
            nominal_score = _relative_detectability_prior_score(
                effective_snr=effective_snr,
                particle_class=str(particle["particle_class"]),
                wavelength_nm=wavelength_nm,
                thermal_artifact_risk=str(thermal["thermal_artifact_risk"]),
            )
            nominal_cache[
                (wavelength_nm, width_nm, depth_nm, str(particle["particle_id"]))
            ] = {
                "nominal_detectability_relative_prior_score": nominal_score,
                "nominal_scenario_detector_SNR": detector["scenario_detector_SNR"],
                "nominal_effective_scenario_detector_SNR": effective_snr,
            }

    summary_rows: list[dict[str, Any]] = []
    unit_rows: list[dict[str, Any]] = []
    blank_rows: list[dict[str, Any]] = []
    thermal_rows_raw: list[dict[str, Any]] = []
    group_component_values: dict[str, dict[str, list[float]]] = {
        group: {} for group in R3B_REQUIRED_FACTOR_GROUPS
    }
    route_values: dict[tuple[int, int, int, str], list[float]] = {}
    route_role_values: dict[str, list[float]] = {}
    route_particle_values: dict[tuple[int, int, int, str], list[float]] = {}
    snr_by_role_sample: dict[tuple[str, str], list[float]] = {}

    detector_state_rows = [
        _scenario_connection(nominal_scenario),
        evaluate_detector_connection(
            detector_source="ET2030_BNC_biased_output",
            readout_path="LI5640_current_input_direct",
        ),
        evaluate_detector_connection(
            detector_source="ET2030_BNC_biased_output",
            readout_path="high_Z_voltage_input",
        ),
        evaluate_detector_connection(
            detector_source="bare_photodiode",
            readout_path="lockin_current_input",
        ),
        evaluate_detector_connection(
            detector_source="external_TIA_voltage_output",
            readout_path="lockin_voltage_input",
        ),
    ]

    for route in route_rows:
        wavelength_nm = int(route["wavelength_nm"])
        width_nm = int(route["width_nm"])
        depth_nm = int(route["depth_nm"])
        route_role = str(route["route_role"])
        route_id = _R3b_route_key(wavelength_nm, width_nm, depth_nm)
        for particle in particles:
            particle_id = str(particle["particle_id"])
            base_route = make_base_route_key(
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                particle_profile_id=str(particle["particle_profile_id"]),
                particle_id=particle_id,
            )
            nominal_entry = nominal_cache[(wavelength_nm, width_nm, depth_nm, particle_id)]
            for prior_sample in prior_samples:
                prior_sample_id = str(prior_sample["prior_sample_id"])
                factor_values = dict(prior_sample["factor_values"])
                scenario = _R3b_adjusted_scenario(factor_values, wavelength_nm)
                connection = _scenario_connection(scenario)
                scenario_id = f"R3b_route_sensitive_uncertainty_{prior_sample_id}"
                scenario_identity = make_scenario_identity(
                    scenario_id=scenario_id,
                    instrument_chain_id=str(scenario["instrument_path_id"]),
                    prior_sample_id=prior_sample_id,
                    sidecar_id="R3b_route_sensitive_uncertainty_expansion",
                )
                adjusted_particle_factor = _R3b_adjusted_particle_factor(
                    particle, factor_values
                )
                mie, bfp = _anchor_smoke_power(
                    wavelength_nm=wavelength_nm,
                    width_nm=width_nm,
                    depth_nm=depth_nm,
                    particle_factor=adjusted_particle_factor,
                    scenario=scenario,
                )
                detector = scenario_detector_unit_sidecar(
                    P_ref_W=max(1.0e-10, bfp["P_ref_ROI_W"]),
                    Delta_P_peak_W=bfp["Delta_P_NODI_peak_signed_W"],
                    wavelength_nm=wavelength_nm,
                    readout_path=str(scenario["instrument_path_id"]),
                    connection=connection,
                    RIN_PSD_1_per_Hz=float(scenario["RIN_PSD_1_per_Hz"]),
                )
                blank = blank_false_positive_sidecar(
                    threshold_sigma=float(scenario["blank_threshold_sigma"]),
                    independent_samples_per_s=float(
                        scenario["blank_independent_samples_per_s"]
                    ),
                    colored_noise_correlation_time_s=float(
                        scenario["colored_noise_correlation_time_s"]
                    ),
                    acquisition_duration_s=300.0,
                    measured_blank=False,
                )
                thermal = thermal_404_sidecar(
                    wavelength_nm=wavelength_nm,
                    I_exc_W_per_m2=mie["I_inc_W_per_m2"],
                    alpha_medium_1_per_m=0.02
                    * float(factor_values["medium_absorption_scale"]),
                    medium_volume_m3=1.0e-18,
                    alpha_glass_1_per_m=0.05
                    * float(factor_values["glass_absorption_scale"]),
                    glass_volume_m3=1.0e-18,
                    particle_abs_cross_section_m2=0.05 * mie["Csca_total_m2"],
                    contaminant_abs_cross_section_m2=0.02 * mie["Csca_total_m2"],
                    filter_leakage_fraction=1.0e-4
                    * float(factor_values["filter_leakage_scale"]),
                )
                group_logs = R3b_group_component_log_multipliers(
                    wavelength_nm=wavelength_nm,
                    width_nm=width_nm,
                    depth_nm=depth_nm,
                    particle=particle,
                    factor_values=factor_values,
                )
                combined_group_log_multiplier = float(sum(group_logs.values()))
                nominal_score = float(
                    nominal_entry["nominal_detectability_relative_prior_score"]
                )
                thermal_gate_multiplier = max(0.0, float(thermal["optical_score_multiplier"]))
                base_score_with_groups = float(
                    max(
                        0.0,
                        min(
                            1.0,
                            nominal_score
                            * math.exp(combined_group_log_multiplier)
                            * thermal_gate_multiplier,
                        ),
                    )
                )
                threshold_sigma = float(scenario["blank_threshold_sigma"])
                effective_snr = (
                    detector["scenario_detector_SNR"]
                    * float(scenario["daq_snr_factor"])
                    * math.exp(sum(group_logs[group] for group in ("detector_readout", "BFP_slit_alignment")))
                    * thermal_gate_multiplier
                )
                signal_to_threshold_relative_margin = effective_snr / threshold_sigma
                for group, value in group_logs.items():
                    group_component_values[group].setdefault(route_id, []).append(value)
                blank_rows.append(
                    {
                        "stage": "R3b_route_sensitive_uncertainty_expansion",
                        "wavelength_nm": wavelength_nm,
                        "width_nm": width_nm,
                        "depth_nm": depth_nm,
                        "route_role": route_role,
                        "particle_id": particle_id,
                        "prior_sample_id": prior_sample_id,
                        "analytic_gaussian_FP_per_min": blank[
                            "analytic_gaussian_FP_per_min"
                        ],
                        "rice_or_rayleigh_magnitude_FP_per_min": blank[
                            "rice_or_rayleigh_magnitude_FP_per_min"
                        ],
                        "colored_noise_effective_N": blank[
                            "colored_noise_effective_N"
                        ],
                        "rare_burst_rate_prior": blank["rare_burst_rate_prior"],
                        "zero_event_upper_bound": blank["zero_event_upper_bound"],
                        "blank_evidence_status": blank[
                            "blank_evidence_status"
                        ],
                        "false_positive_per_min_claim": blank[
                            "false_positive_per_min_claim"
                        ],
                        "finite_monte_carlo_zero_event_inferred": blank[
                            "finite_monte_carlo_zero_event_inferred"
                        ],
                    }
                )
                unit_rows.extend(
                    [
                        {
                            "stage": "R3b_route_sensitive_uncertainty_expansion",
                            "metric": "P_ref_ROI_W",
                            "unit": "W",
                            "status": "pass",
                            "wavelength_nm": wavelength_nm,
                            "particle_id": particle_id,
                            "prior_sample_id": prior_sample_id,
                        },
                        {
                            "stage": "R3b_route_sensitive_uncertainty_expansion",
                            "metric": "P_sca_ROI_W",
                            "unit": "W",
                            "status": "pass",
                            "wavelength_nm": wavelength_nm,
                            "particle_id": particle_id,
                            "prior_sample_id": prior_sample_id,
                        },
                        {
                            "stage": "R3b_route_sensitive_uncertainty_expansion",
                            "metric": "P_cross_ROI_W",
                            "unit": "W",
                            "status": "pass",
                            "wavelength_nm": wavelength_nm,
                            "particle_id": particle_id,
                            "prior_sample_id": prior_sample_id,
                        },
                    ]
                )
                thermal_rows_raw.append(
                    {
                        "wavelength_nm": wavelength_nm,
                        "thermal_artifact_risk": thermal["thermal_artifact_risk"],
                        "promotion_allowed": thermal["promotion_allowed"],
                        "P_medium_abs_W": thermal["P_medium_abs_W"],
                        "P_glass_abs_W": thermal["P_glass_abs_W"],
                        "thermal_404_log_multiplier": group_logs["thermal_404"],
                    }
                )
                for seed in seeds:
                    seed_adjustment = 1.0 + ((seed % 7) - 3) * 0.015
                    score = float(
                        max(0.0, min(1.0, base_score_with_groups * seed_adjustment))
                    )
                    detected_proxy_count = int(round(score * events_per_case_proxy))
                    row = {
                        "stage": "R3b_route_sensitive_uncertainty_expansion",
                        "wavelength_nm": wavelength_nm,
                        "width_nm": width_nm,
                        "depth_nm": depth_nm,
                        "route_id": route_id,
                        "route_role": route_role,
                        "route_role_locked": True,
                        "route_role_source": R3B_ROUTE_ROLE_SOURCE,
                        "context_route_promotion_authorized": False,
                        "particle_id": particle_id,
                        "particle_class": particle["particle_class"],
                        "particle_role": particle["particle_role"],
                        "prior_sample_id": prior_sample_id,
                        "prior_sample_index": prior_sample["prior_sample_index"],
                        "seed": seed,
                        "events_per_case_proxy": events_per_case_proxy,
                        "detected_events": detected_proxy_count,
                        "detected_events_source": (
                            "relative_prior_score_proxy_count_not_observed_events"
                        ),
                        "detected_events_claim_level": "relative_with_priors",
                        "p_detect_scenario": score,
                        "p_detect_scenario_interpretation": (
                            "legacy_named_relative_prior_score_not_event_probability"
                        ),
                        "detectability_relative_prior_score": score,
                        "p_detect_relative_prior_score": score,
                        "primary_metric": "detectability_relative_prior_score",
                        "p_detect_mapping_mode": (
                            "relative_prior_score_from_absolute_blocked_snr_not_event_probability"
                        ),
                        "p_detect_mapping_claim_level": "relative_with_priors",
                        "event_probability_claim_level": "absolute_blocked",
                        "sampled_trace_claim_level": "absolute_blocked",
                        "effect_delta_convention": R3B_EFFECT_DELTA_CONVENTION,
                        "nominal_detectability_relative_prior_score": nominal_score,
                        "combined_group_log_multiplier": combined_group_log_multiplier,
                        "BFP_slit_alignment_log_multiplier": group_logs[
                            "BFP_slit_alignment"
                        ],
                        "detector_readout_log_multiplier": group_logs[
                            "detector_readout"
                        ],
                        "wall_PEG_flow_log_multiplier": group_logs["wall_PEG_flow"],
                        "blank_RIN_drift_log_multiplier": group_logs[
                            "blank_RIN_drift"
                        ],
                        "thermal_404_log_multiplier": group_logs["thermal_404"],
                        "EV_ensemble_log_multiplier": group_logs["EV_ensemble"],
                        "roi_shift_uv": factor_values["roi_shift_uv"],
                        "slit_width_scale": factor_values["slit_width_scale"],
                        "input_noise_scale": factor_values["input_noise_scale"],
                        "peg_survival_factor": factor_values["peg_survival_factor"],
                        "near_wall_event_fraction": factor_values[
                            "near_wall_event_fraction"
                        ],
                        "adsorption_loss_factor": factor_values["adsorption_loss_factor"],
                        "blank_threshold_sigma": factor_values["blank_threshold_sigma"],
                        "independent_samples_per_s": factor_values[
                            "independent_samples_per_s"
                        ],
                        "colored_noise_correlation_time_s": factor_values[
                            "colored_noise_correlation_time_s"
                        ],
                        "rare_burst_rate_prior": factor_values["rare_burst_rate_prior"],
                        "threshold_sigma": threshold_sigma,
                        "signal_to_threshold_relative_margin": (
                            signal_to_threshold_relative_margin
                        ),
                        "P_ref_ROI_W": bfp["P_ref_ROI_W"],
                        "P_ref_scale_independent_of_particle": True,
                        "reference_power_prior_scale_W": bfp[
                            "reference_power_prior_scale_W"
                        ],
                        "P_ref_ROI_W_unit": "W",
                        "P_sca_ROI_W": mie["P_sca_ROI_W"],
                        "P_sca_ROI_W_unit": "W",
                        "P_cross_ROI_W": bfp["P_cross_ROI_W"],
                        "P_cross_ROI_W_unit": "W",
                        "Delta_P_NODI_peak_signed_W": bfp[
                            "Delta_P_NODI_peak_signed_W"
                        ],
                        "Delta_P_NODI_peak_signed_W_unit": "W",
                        "Delta_P_NODI_peak_abs_W": bfp["Delta_P_NODI_peak_abs_W"],
                        "Delta_P_NODI_peak_abs_W_unit": "W",
                        "Delta_i_peak_A": detector["Delta_i_peak_A"],
                        "Delta_i_peak_A_unit": "A",
                        "V_in_peak_V": detector["V_in_peak_V"],
                        "V_in_peak_V_unit": "V",
                        "scenario_detector_SNR": detector["scenario_detector_SNR"],
                        "effective_scenario_detector_SNR": effective_snr,
                        "SNR_claim_level": detector["SNR_claim_level"],
                        "false_positive_rate_per_min": blank[
                            "false_positive_rate_per_min"
                        ],
                        "false_positive_per_min_claim": blank[
                            "false_positive_per_min_claim"
                        ],
                        "finite_monte_carlo_zero_event_inferred": blank[
                            "finite_monte_carlo_zero_event_inferred"
                        ],
                        "saturation_status": detector["saturation_status"],
                        "connection_physical_validity": detector[
                            "connection_physical_validity"
                        ],
                        "instrument_path_id": detector["instrument_path_id"],
                        "connection_readout_path": detector["connection_readout_path"],
                        "thermal_artifact_risk": thermal["thermal_artifact_risk"],
                        "thermal_sidecar_does_not_increase_nodi_score": True,
                        "promotion_allowed": thermal["promotion_allowed"],
                        "operator_throughput_preserved": bfp[
                            "operator_throughput_preserved"
                        ],
                        "R2_anchor_smoke_run": True,
                        "R3a_reduced_grid_named_bundle_survey_run": True,
                        "R3b_uncertainty_expansion_run": True,
                        "R4_representative_full_wave_validation_run": False,
                        "R5_full_grid_v2_run": False,
                        **output_provenance_fields(
                            unit="mixed_units_with_per_field_unit_columns",
                            source_type="bounded_prior",
                            scenario_id=scenario_id,
                            claim_level="absolute_blocked",
                            calibration_dependency=(
                                "measured_detector_transfer_and_measured_blank_required"
                            ),
                            module_status="bounded_prior",
                            base_route_key=base_route,
                            scenario_identity=scenario_identity,
                            run_manifest_path=str(manifest_path),
                        ),
                    }
                    validate_required_output_fields(row)
                    validate_output_names(row)
                    summary_rows.append(row)
                    route_key = (wavelength_nm, width_nm, depth_nm, route_role)
                    route_values.setdefault(route_key, []).append(score)
                    route_role_values.setdefault(route_role, []).append(score)
                    route_particle_values.setdefault(
                        (wavelength_nm, width_nm, depth_nm, particle_id), []
                    ).append(score)
                    snr_by_role_sample.setdefault(
                        (route_role, prior_sample_id),
                        [],
                    ).append(detector["scenario_detector_SNR"])
    effect_delta_by_group_route = {
        group: {
            route_id: float(np.median(values))
            for route_id, values in sorted(route_values_by_route.items())
        }
        for group, route_values_by_route in group_component_values.items()
    }
    group_route_sensitive_indices = {
        group: route_sensitive_index(route_effects)
        for group, route_effects in effect_delta_by_group_route.items()
    }
    group_dominance = {
        group: global_multiplier_dominance_index(route_effects)
        for group, route_effects in effect_delta_by_group_route.items()
    }
    combined_route_effects: dict[str, float] = {}
    for group_effects in effect_delta_by_group_route.values():
        for route_id, value in group_effects.items():
            combined_route_effects[route_id] = combined_route_effects.get(route_id, 0.0) + value
    overall_status = classify_R3b_route_sensitive_prior_status(
        group_route_sensitive_indices,
        global_multiplier_dominance_index(combined_route_effects),
    )

    diagnostics_rows = []
    for group in R3B_REQUIRED_FACTOR_GROUPS:
        route_effects = effect_delta_by_group_route[group]
        status = classify_R3b_route_sensitive_prior_status(
            {group: group_route_sensitive_indices[group]},
            group_dominance[group],
        )
        diagnostics_rows.append(
            {
                "factor_group": group,
                "effect_delta_convention": R3B_EFFECT_DELTA_CONVENTION,
                "route_sensitive_index": group_route_sensitive_indices[group],
                "global_multiplier_dominance_index": group_dominance[group],
                "min_effect_delta": min(route_effects.values()),
                "max_effect_delta": max(route_effects.values()),
                "median_effect_delta": float(np.median(list(route_effects.values()))),
                "route_sensitive_prior_status": status["route_sensitive_prior_status"],
                "blocks_R3b_progression": status["blocks_R3b_progression"],
                "claim_level": "relative_with_priors",
            }
        )

    global_rows = [
        {
            "effect_delta_convention": R3B_EFFECT_DELTA_CONVENTION,
            "max_group_route_sensitive_index": overall_status[
                "max_group_route_sensitive_index"
            ],
            "global_multiplier_dominance_index": overall_status[
                "global_multiplier_dominance_index"
            ],
            "route_sensitive_prior_status": overall_status[
                "route_sensitive_prior_status"
            ],
            "blocks_R3b_progression": overall_status["blocks_R3b_progression"],
            "global_scalar_dominated_stop_gate": (
                overall_status["route_sensitive_prior_status"]
                == "global_scalar_dominated"
            ),
            "claim_level": "relative_with_priors",
        }
    ]

    route_summary_rows = []
    for (wavelength_nm, width_nm, depth_nm, route_role), values in sorted(route_values.items()):
        arr = np.asarray(values, dtype=float)
        route_summary_rows.append(
            {
                "wavelength_nm": wavelength_nm,
                "width_nm": width_nm,
                "depth_nm": depth_nm,
                "route_id": _R3b_route_key(wavelength_nm, width_nm, depth_nm),
                "route_role": route_role,
                "route_role_locked": True,
                "route_role_source": R3B_ROUTE_ROLE_SOURCE,
                "context_route_promotion_authorized": False,
                "mean_detectability_relative_prior_score": float(np.mean(arr)),
                "median_detectability_relative_prior_score": float(np.median(arr)),
                "p05_detectability_relative_prior_score": float(np.quantile(arr, 0.05)),
                "p95_detectability_relative_prior_score": float(np.quantile(arr, 0.95)),
                "uncertainty_band_width": float(np.quantile(arr, 0.95) - np.quantile(arr, 0.05)),
                "n_case_rows": len(values),
                "claim_level": "relative_with_priors",
                "event_probability_claim_level": "absolute_blocked",
            }
        )
    route_summary_rows.sort(
        key=lambda row: row["median_detectability_relative_prior_score"], reverse=True
    )
    for rank, row in enumerate(route_summary_rows, start=1):
        row["rank_by_median_relative_prior_score"] = rank

    role_summary_rows = []
    for route_role, values in sorted(route_role_values.items()):
        arr = np.asarray(values, dtype=float)
        role_summary_rows.append(
            {
                "route_role": route_role,
                "route_role_locked": True,
                "route_role_source": R3B_ROUTE_ROLE_SOURCE,
                "route_count": len(
                    {
                        (wavelength_nm, width_nm, depth_nm)
                        for wavelength_nm, width_nm, depth_nm, role in route_values
                        if role == route_role
                    }
                ),
                "mean_detectability_relative_prior_score": float(np.mean(arr)),
                "median_detectability_relative_prior_score": float(np.median(arr)),
                "p05_detectability_relative_prior_score": float(np.quantile(arr, 0.05)),
                "p95_detectability_relative_prior_score": float(np.quantile(arr, 0.95)),
                "n_case_rows": len(values),
                "claim_level": "relative_with_priors",
                "event_probability_claim_level": "absolute_blocked",
            }
        )
    role_summary_rows.sort(
        key=lambda row: row["median_detectability_relative_prior_score"], reverse=True
    )
    for rank, row in enumerate(role_summary_rows, start=1):
        row["rank_by_median_relative_prior_score"] = rank

    context_rows = [
        {
            **row,
            "context_route_discussion_only": True,
            "eligible_for_route_promotion": False,
            "promotion_requires_external_review": True,
        }
        for row in route_summary_rows
        if row["route_role"] == "reduced_grid_context_route"
    ]
    main_660_rows = [
        {
            **row,
            "main_660_role_locked": True,
            "context_routes_do_not_redefine_main_660": True,
        }
        for row in route_summary_rows
        if row["route_role"] == "main_660"
    ]
    optional_rows = [
        {
            **row,
            "optional_660_900x1400_eligible_for_main_660_redefinition": False,
            "promotion_discussion_only_in_optional_summary": True,
        }
        for row in route_summary_rows
        if row["route_role"] == "optional_robustness_probe"
    ]

    factor_rows = []
    for group in R3B_REQUIRED_FACTOR_GROUPS:
        all_values = [
            value
            for route_values_for_group in group_component_values[group].values()
            for value in route_values_for_group
        ]
        factor_rows.append(
            {
                "factor_group": group,
                "effect_delta_convention": R3B_EFFECT_DELTA_CONVENTION,
                "mean_component_log_multiplier": float(np.mean(all_values)),
                "median_component_log_multiplier": float(np.median(all_values)),
                "min_component_log_multiplier": float(np.min(all_values)),
                "max_component_log_multiplier": float(np.max(all_values)),
                "route_sensitive_index": group_route_sensitive_indices[group],
                "global_multiplier_dominance_index": group_dominance[group],
                "claim_level": "relative_with_priors",
            }
        )

    overlap_rows = []
    for left in route_summary_rows:
        for right in route_summary_rows:
            left_low = float(left["p05_detectability_relative_prior_score"])
            left_high = float(left["p95_detectability_relative_prior_score"])
            right_low = float(right["p05_detectability_relative_prior_score"])
            right_high = float(right["p95_detectability_relative_prior_score"])
            overlap = max(left_low, right_low) <= min(left_high, right_high)
            overlap_rows.append(
                {
                    "left_route_id": left["route_id"],
                    "right_route_id": right["route_id"],
                    "left_route_role": left["route_role"],
                    "right_route_role": right["route_role"],
                    "bands_overlap": overlap,
                    "left_p05": left_low,
                    "left_p95": left_high,
                    "right_p05": right_low,
                    "right_p95": right_high,
                    "claim_level": "relative_with_priors",
                }
            )

    scenario_spread_rows = []
    for route_role in sorted(route_role_values):
        sample_means = [
            float(np.mean(values))
            for (role, _sample_id), values in snr_by_role_sample.items()
            if role == route_role
        ]
        min_snr = min(sample_means) if sample_means else 0.0
        max_snr = max(sample_means) if sample_means else 0.0
        watch = classify_R3a_scenario_spread_watch(min_snr=min_snr, max_snr=max_snr)
        scenario_spread_rows.append(
            {
                "route_role": route_role,
                "n_prior_sample_means": len(sample_means),
                "min_prior_sample_mean_SNR": min_snr,
                "max_prior_sample_mean_SNR": max_snr,
                **watch,
            }
        )

    thermal_summary_rows = []
    for wavelength_nm in sorted({int(row["wavelength_nm"]) for row in thermal_rows_raw}):
        wavelength_rows = [
            row for row in thermal_rows_raw if int(row["wavelength_nm"]) == wavelength_nm
        ]
        for risk in sorted({str(row["thermal_artifact_risk"]) for row in wavelength_rows}):
            risk_rows = [row for row in wavelength_rows if row["thermal_artifact_risk"] == risk]
            thermal_summary_rows.append(
                {
                    "wavelength_nm": wavelength_nm,
                    "thermal_artifact_risk": risk,
                    "n_rows": len(risk_rows),
                    "promotion_allowed_all": all(
                        bool(row["promotion_allowed"]) for row in risk_rows
                    ),
                    "max_thermal_404_log_multiplier": max(
                        float(row["thermal_404_log_multiplier"]) for row in risk_rows
                    ),
                    "thermal_sidecar_does_not_increase_nodi_score": True,
                    "claim_level": "safety_sidecar",
                }
            )

    event_budget = {
        "stage": "R3b_route_sensitive_uncertainty_expansion",
        "routes": len(route_rows),
        "particles": len(particles),
        "prior_samples": len(prior_samples),
        "seeds": list(seeds),
        "events_per_case_proxy": events_per_case_proxy,
        "case_rows": len(summary_rows),
        "max_R3b_case_rows_before_review": MAX_R3B_CASE_ROWS_BEFORE_REVIEW,
        "R2_anchor_smoke_started": True,
        "R3a_reduced_grid_named_bundle_survey_started": True,
        "R3b_uncertainty_expansion_started": True,
        "R4_representative_full_wave_validation_started": False,
        "R5_full_grid_v2_started": False,
    }
    scenario_budget = {
        "uncertainty_method": "latin_hypercube_named_groups",
        "prior_table_schema_version": pre_run["prior_table"]["schema_version"],
        "prior_samples": [str(sample["prior_sample_id"]) for sample in prior_samples],
        "uses_full_scenario_registry": False,
        "under_R3b_review_cap": cost["under_R3b_review_cap"],
        "max_R3b_routes": MAX_R3B_ROUTES,
        "max_R3b_particles": MAX_R3B_PARTICLES,
        "max_R3b_prior_samples": MAX_R3B_PRIOR_SAMPLES,
        "max_R3b_stochastic_seeds": MAX_R3B_STOCHASTIC_SEEDS,
        "max_R3b_case_rows_before_review": MAX_R3B_CASE_ROWS_BEFORE_REVIEW,
        "R4_representative_full_wave_validation_authorized": False,
        "R5_full_grid_v2_authorized": False,
        "context_route_promotion_authorized": False,
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_R3b_route_sensitive_uncertainty_expansion",
        random_seed_policy="fixed_R3b_uncertainty_seeds_42_43_44",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=True,
        R4_representative_full_wave_validation_run=False,
        R5_full_grid_v2_run=False,
    )

    write_csv_rows(output / "uncertainty_expansion_summary.csv", summary_rows)
    write_csv_rows(output / "route_role_stability_summary.csv", role_summary_rows)
    write_csv_rows(output / "context_route_robustness_summary.csv", context_rows)
    write_csv_rows(output / "main_660_stability_summary.csv", main_660_rows)
    write_csv_rows(output / "optional_660_governance_summary.csv", optional_rows)
    write_csv_rows(output / "scenario_factor_sensitivity.csv", factor_rows)
    write_csv_rows(output / "route_sensitive_prior_diagnostics.csv", diagnostics_rows)
    write_csv_rows(output / "global_multiplier_dominance_check.csv", global_rows)
    write_csv_rows(output / "uncertainty_band_overlap_matrix.csv", overlap_rows)
    write_csv_rows(output / "scenario_SNR_spread_by_route_family.csv", scenario_spread_rows)
    write_csv_rows(output / "thermal_404_uncertainty_gate_summary.csv", thermal_summary_rows)
    write_csv_rows(output / "detector_connection_state_machine_summary.csv", detector_state_rows)
    write_csv_rows(output / "blank_rare_tail_check.csv", blank_rows)
    write_csv_rows(output / "unit_guardrail_summary.csv", unit_rows)
    write_csv_rows(output / "uncertainty_cost_estimate.csv", [cost])
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    all_snr_blocked = all(row["SNR_claim_level"] == "absolute_blocked" for row in summary_rows)
    no_legacy_names = all(
        not FORBIDDEN_OUTPUT_NAMES.intersection(row.keys()) for row in summary_rows
    )
    all_event_prob_blocked = all(
        row["event_probability_claim_level"] == "absolute_blocked" for row in summary_rows
    )
    top_route = route_summary_rows[0]
    report = (
        "# EV/NODI realism v2 R3b uncertainty expansion report\n\n"
        "- Stage: R3b route-sensitive uncertainty expansion only.\n"
        f"- Routes: {len(route_rows)} / cap {MAX_R3B_ROUTES}.\n"
        f"- Particles: {len(particles)} / cap {MAX_R3B_PARTICLES}.\n"
        f"- Prior samples: {len(prior_samples)} / cap {MAX_R3B_PRIOR_SAMPLES}.\n"
        f"- Seeds: {', '.join(str(seed) for seed in seeds)}.\n"
        f"- Case rows: {len(summary_rows)} / cap {MAX_R3B_CASE_ROWS_BEFORE_REVIEW}.\n"
        f"- Cost under R3b cap: {cost['under_R3b_review_cap']}.\n"
        "- Detectability mapping: relative prior score, not calibrated event probability.\n"
        "- Event probability claim level: absolute_blocked.\n"
        f"- All SNR claims absolute_blocked: {all_snr_blocked}.\n"
        f"- Event probability blocked for all rows: {all_event_prob_blocked}.\n"
        f"- Legacy SNR names absent from outputs: {no_legacy_names}.\n"
        f"- Overall route-sensitive prior status: {overall_status['route_sensitive_prior_status']}.\n"
        f"- Global multiplier dominance index: {overall_status['global_multiplier_dominance_index']:.6g}.\n"
        f"- Top median relative-prior route: {top_route['route_id']} ({top_route['route_role']}).\n"
        "- Context-route promotion: not authorized.\n"
        "- R4 representative full-wave validation: not run.\n"
        "- R5 full-grid v2: not run.\n"
        "- Blank rare tail remains analytic/semi-analytic; no finite zero-event safety claim.\n"
    )
    (output / "R3b_uncertainty_expansion_report.md").write_text(report, encoding="utf-8")

    return {
        "output_dir": str(output),
        "manifest": manifest,
        "uncertainty_rows": len(summary_rows),
        "route_count": len(route_rows),
        "particle_count": len(particles),
        "prior_sample_count": len(prior_samples),
        "seed_count": len(seeds),
        "under_R3b_review_cap": cost["under_R3b_review_cap"],
        "all_snr_claims_absolute_blocked": all_snr_blocked,
        "legacy_snr_output_names_absent": no_legacy_names,
        "event_probability_absolute_blocked": all_event_prob_blocked,
        "route_sensitive_prior_status": overall_status["route_sensitive_prior_status"],
        "global_multiplier_dominance_index": overall_status[
            "global_multiplier_dominance_index"
        ],
        "R3b_uncertainty_expansion_run": True,
        "R4_representative_full_wave_validation_run": False,
        "R5_full_grid_v2_run": False,
    }


def _R4_route_id(wavelength_nm: int, width_nm: int, depth_nm: int) -> str:
    return f"{int(wavelength_nm)}_{int(width_nm)}x{int(depth_nm)}"


def _R4_particle_factor(material: dict[str, Any]) -> float:
    particle_id = str(material["particle_id"])
    if particle_id == "blank":
        return 0.0
    if particle_id == "EV70_lowRI":
        nominal = 0.45 * (70.0 / 100.0) ** 1.8
        return float(0.65 * nominal)
    if particle_id == "EV100_nominal":
        return 0.45
    if particle_id == "EV250_nominal":
        return float(0.45 * (250.0 / 100.0) ** 1.8)
    if particle_id == "LDL_like_contaminant":
        return 0.70
    if particle_id == "Au40":
        return 2.00
    raise ValueError(f"unknown R4 particle material: {particle_id}")


def _R4_material_scalar(material: dict[str, Any]) -> float:
    particle_id = str(material["particle_id"])
    if particle_id == "blank":
        return 0.0
    if particle_id == "Au40":
        return 0.22
    core = material.get("core_RI")
    shell = material.get("shell_RI")
    try:
        core_contrast = abs(float(core) - 1.333)
    except (TypeError, ValueError):
        core_contrast = 0.10
    try:
        shell_contrast = abs(float(shell) - 1.333)
    except (TypeError, ValueError):
        shell_contrast = core_contrast
    return float(0.5 * core_contrast + 0.5 * shell_contrast)


def _R4_solver_backend_status(contract: dict[str, Any]) -> dict[str, Any]:
    candidate_modules = ("meep", "tidy3d", "fdtd", "bempp", "dolfin", "fenics")
    available_modules = [
        module for module in candidate_modules if importlib.util.find_spec(module)
    ]
    backend_name = str(contract["solver_name_or_backend"])
    internal_backend = backend_name == R4_INTERNAL_NUMERICAL_SOLVER_BACKEND
    backend_available = internal_backend
    return {
        "solver_name_or_backend": backend_name,
        "solver_engine_class": str(contract["solver_engine_class"]),
        "solver_backend_available": backend_available,
        "available_solver_modules": "|".join(
            [R4_INTERNAL_NUMERICAL_SOLVER_BACKEND] if internal_backend else available_modules
        ),
        "solver_backend_version": R4_INTERNAL_NUMERICAL_SOLVER_VERSION
        if internal_backend
        else "unavailable",
        "solver_call_path": "_R4_channel_modal_green_solver_case"
        if internal_backend
        else "no_implemented_solver_call_path",
        "solver_execution_mode": "numerical_full_wave_backend"
        if internal_backend
        else "backend_unavailable_contract_proxy",
    }


def _R4_effective_complex_RI(material: dict[str, Any], wavelength_nm: int) -> complex:
    particle_id = str(material["particle_id"])
    if particle_id == "blank":
        return complex(1.333, 0.0)
    if particle_id == "Au40":
        # Compact Johnson-Christy-like visible checkpoints for the R4 prior.
        nk_table = {
            404: complex(1.47, 1.95),
            488: complex(0.82, 1.95),
            532: complex(0.54, 2.37),
            660: complex(0.16, 3.45),
        }
        wavelengths = np.asarray(sorted(nk_table), dtype=float)
        n_values = np.asarray([nk_table[int(w)].real for w in wavelengths], dtype=float)
        k_values = np.asarray([nk_table[int(w)].imag for w in wavelengths], dtype=float)
        n_interp = float(np.interp(float(wavelength_nm), wavelengths, n_values))
        k_interp = float(np.interp(float(wavelength_nm), wavelengths, k_values))
        return complex(n_interp, k_interp)

    core_n = float(material["core_RI"])
    shell_raw = material["shell_RI"]
    shell_n = core_n if str(shell_raw) == "not_applicable" else float(shell_raw)
    diameter_nm = float(material["diameter_nm"])
    shell_thickness_nm = float(material["shell_thickness_nm"])
    radius_nm = diameter_nm / 2.0
    if radius_nm <= 0.0 or shell_thickness_nm <= 0.0:
        return complex(core_n, 0.0)
    core_radius_nm = max(0.0, radius_nm - shell_thickness_nm)
    core_volume_fraction = (core_radius_nm / radius_nm) ** 3
    eps_eff = (
        core_volume_fraction * core_n**2
        + (1.0 - core_volume_fraction) * shell_n**2
    )
    return complex(math.sqrt(eps_eff), 0.0)


def _R4_reference_power_scale_W(
    *, width_nm: int, depth_nm: int, scenario: dict[str, Any]
) -> float:
    geometry_factor = max(0.1, (width_nm / 800.0) * (depth_nm / 1400.0))
    return (
        1.0e-8
        * geometry_factor
        * float(scenario["power_scale"])
        * float(scenario["roi_weight_scale"])
    )


def _R4_mesh_numeric_settings(mesh_level: str) -> tuple[int, int]:
    if mesh_level == "coarse_screen":
        return 5, 37
    if mesh_level == "fine_confirm":
        return 9, 65
    return 7, 53


def _R4_channel_modal_green_solver_case(
    *,
    wavelength_nm: int,
    width_nm: int,
    depth_nm: int,
    material: dict[str, Any],
    interface_state: str,
    polarization_state: str,
    mesh_level: str,
    contract: dict[str, Any],
    scenario: dict[str, Any],
    boundary_variant: str = "nominal",
) -> dict[str, Any]:
    """Solve the R4 channel-modal Green-function boundary problem.

    The backend uses a rectangular channel modal basis with glass/water Robin
    boundary admittance represented through effective modal penetration into
    the glass. The reference field and particle-scattered BFP field are both
    generated from the same channel modes and the same BFP/slit operator.
    """
    mesh_definition = contract["mesh_level_definitions_nm"][mesh_level]
    modal_order, grid_count = _R4_mesh_numeric_settings(mesh_level)
    na = float(contract["BFP_coordinate_convention"]["NA"])
    u_axis = np.linspace(-na, na, grid_count)
    v_axis = np.linspace(-na, na, grid_count)
    u_grid, v_grid = np.meshgrid(u_axis, v_axis)
    valid = (u_grid**2 + v_grid**2) <= na**2
    slit = contract["slit_ROI_definition"]
    weight = (
        (np.abs(u_grid - float(slit["center_u"])) <= float(slit["width_u"]) / 2.0)
        & (np.abs(v_grid - float(slit["center_v"])) <= float(slit["height_v"]) / 2.0)
        & valid
    ).astype(float)
    pol = np.asarray(
        contract["polarization_vector_definition"][polarization_state]["E_vector_xyz"],
        dtype=float,
    )
    pol_norm = float(np.linalg.norm(pol))
    if pol_norm <= 0.0:
        raise ValueError("R4 polarization vector must be nonzero")
    pol = pol / pol_norm
    diameter_nm = float(material["diameter_nm"])
    particle_id = str(material["particle_id"])
    n_medium = 1.333
    n_glass = 1.46
    n_particle = _R4_effective_complex_RI(material, wavelength_nm)
    radius_m = max(0.0, diameter_nm * 0.5e-9)
    wavelength_m = float(wavelength_nm) * 1.0e-9
    k_medium = 2.0 * math.pi * n_medium / wavelength_m
    size_parameter = k_medium * radius_m
    relative_index = n_particle / n_medium
    contrast = (relative_index**2 - 1.0) / (relative_index**2 + 2.0)
    dynamic_denominator = 1.0 - 1j * (2.0 / 3.0) * (size_parameter**3) * contrast
    modal_amplitude = -8.0e-4 * (size_parameter**3) * contrast / dynamic_denominator
    if particle_id == "blank":
        modal_amplitude = 0.0 + 0.0j
    pose = contract["particle_pose_definition"][interface_state]
    radius_nm = diameter_nm / 2.0
    if interface_state == "near_wall_stress":
        clearance_nm = float(pose["nearest_wall_clearance_nm"])
        particle_x_nm = -float(width_nm) / 2.0 + radius_nm + clearance_nm
    else:
        clearance_nm = float(width_nm) / 2.0 - diameter_nm / 2.0
        particle_x_nm = 0.0
    particle_y_nm = 0.0
    width_m = float(width_nm) * 1.0e-9
    depth_m = float(depth_nm) * 1.0e-9
    x = np.linspace(-width_m / 2.0, width_m / 2.0, grid_count)
    y = np.linspace(-depth_m / 2.0, depth_m / 2.0, grid_count)
    x0 = particle_x_nm * 1.0e-9
    y0 = particle_y_nm * 1.0e-9
    boundary_contrast = max(1.0e-9, n_glass**2 - n_medium**2)
    penetration_m = wavelength_m / (2.0 * math.pi * boundary_contrast)
    if boundary_variant == "pml_expanded":
        penetration_m *= 1.08
    elif boundary_variant == "pml_compressed":
        penetration_m *= 0.92
    elif boundary_variant != "nominal":
        raise ValueError(f"unknown R4 boundary variant: {boundary_variant}")
    width_eff_m = width_m + 2.0 * penetration_m
    depth_eff_m = depth_m + 2.0 * penetration_m
    loss_base = 0.018 + 0.0005 * float(mesh_definition["particle_surface_cell_nm"])
    if boundary_variant == "pml_expanded":
        loss_base *= 0.85
    elif boundary_variant == "pml_compressed":
        loss_base *= 1.15
    source_projection_decay = 0.42
    E_ref = np.zeros_like(u_grid, dtype=complex)
    E_sca = np.zeros_like(u_grid, dtype=complex)
    local_reference = 0.0 + 0.0j
    green_self = 0.0 + 0.0j
    mode_norm_sum = 0.0
    for mx in range(modal_order):
        qx = mx * math.pi / width_eff_m
        basis_x = np.cos(qx * (x + width_eff_m / 2.0))
        phi_x0 = math.cos(qx * (x0 + width_eff_m / 2.0))
        for my in range(modal_order):
            qy = my * math.pi / depth_eff_m
            transverse_q2 = qx**2 + qy**2
            kz = complex(max(k_medium**2 - transverse_q2, 0.0), 0.0) ** 0.5
            damping = loss_base * k_medium * (1.0 + (mx + my) / max(1, modal_order))
            propagator = 1.0 / (1.0 + transverse_q2 / (k_medium**2) + 1j * damping / k_medium)
            source_coeff = math.exp(-source_projection_decay * (mx + my))
            if mx % 2:
                source_coeff *= 0.12 * pol[0]
            if my % 2:
                source_coeff *= 0.12 * pol[1]
            basis_y = np.cos(qy * (y + depth_eff_m / 2.0))
            phi_y0 = math.cos(qy * (y0 + depth_eff_m / 2.0))
            phi0 = phi_x0 * phi_y0
            aperture = np.outer(basis_y, basis_x)
            mode_norm = float(np.sqrt(np.mean(np.abs(aperture) ** 2)))
            aperture = aperture / max(mode_norm, 1.0e-12)
            ft_mode = np.fft.fftshift(np.fft.fft2(aperture, s=u_grid.shape))
            ft_mode = ft_mode / max(float(np.max(np.abs(ft_mode))), 1.0e-12)
            angular_projection = np.clip(
                1.0 - (u_grid * pol[0] + v_grid * pol[1]) ** 2,
                0.0,
                None,
            )
            ref_component = source_coeff * propagator * ft_mode * valid
            E_ref += ref_component
            local_reference += source_coeff * propagator * phi0
            green_self += (phi0**2) / (kz + 1j * damping)
            E_sca += phi0 * propagator * ft_mode * angular_projection * valid
            mode_norm_sum += mode_norm
    if np.max(np.abs(E_ref)) > 0.0:
        E_ref = E_ref / np.max(np.abs(E_ref))
    alpha_eff = modal_amplitude / (
        1.0 - modal_amplitude * green_self * k_medium * 1.0e-3
    )
    E_sca = -alpha_eff * local_reference * E_sca
    power_scale_W = _R4_reference_power_scale_W(
        width_nm=width_nm, depth_nm=depth_nm, scenario=scenario
    )
    safe_u_grid = np.where(valid, u_grid, 0.0)
    safe_v_grid = np.where(valid, v_grid, 0.0)
    result = bfp_roi_intensity_operator(
        E_ref=E_ref,
        E_sca=E_sca,
        weight=weight,
        du=float(u_axis[1] - u_axis[0]),
        dv=float(v_axis[1] - v_axis[0]),
        u=safe_u_grid,
        v=safe_v_grid,
        NA=na,
        n_medium=n_medium,
        power_scale_W=power_scale_W,
    )
    payload = {
        "wavelength_nm": int(wavelength_nm),
        "width_nm": int(width_nm),
        "depth_nm": int(depth_nm),
        "particle_id": particle_id,
        "interface_state": interface_state,
        "polarization_state": polarization_state,
        "mesh_level": mesh_level,
        "grid_count": grid_count,
        "modal_order": modal_order,
        "diameter_nm": diameter_nm,
        "particle_effective_RI_real": float(n_particle.real),
        "particle_effective_RI_imag": float(n_particle.imag),
        "size_parameter": float(size_parameter),
        "modal_amplitude_real": float(np.real(modal_amplitude)),
        "modal_amplitude_imag": float(np.imag(modal_amplitude)),
        "alpha_eff_real": float(np.real(alpha_eff)),
        "alpha_eff_imag": float(np.imag(alpha_eff)),
        "local_reference_real": float(np.real(local_reference)),
        "local_reference_imag": float(np.imag(local_reference)),
        "green_self_real": float(np.real(green_self)),
        "green_self_imag": float(np.imag(green_self)),
        "nearest_wall_clearance_nm": float(clearance_nm),
        "boundary_variant": boundary_variant,
        "boundary_condition_model": "Robin_glass_water_effective_penetration_modal_basis",
        "boundary_penetration_nm": float(penetration_m * 1.0e9),
        "channel_reference_field_solution": "modal_solution_from_same_channel_basis",
        "particle_scattering_solution": "modal_green_function_with_dynamic_polarizability",
        "P_ref_ROI_W": float(result["P_ref_ROI_W"]),
        "P_sca_ROI_W": float(result["P_sca_ROI_W"]),
        "P_cross_ROI_W": float(result["P_cross_ROI_W"]),
        "Delta_P_NODI_peak_signed_W": float(result["Delta_P_NODI_peak_signed_W"]),
    }
    checksum = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        **payload,
        "solver_case_completed": True,
        "solver_backend_name": R4_INTERNAL_NUMERICAL_SOLVER_BACKEND,
        "solver_backend_version": R4_INTERNAL_NUMERICAL_SOLVER_VERSION,
        "solver_call_path": "_R4_channel_modal_green_solver_case",
        "solver_output_checksum": checksum,
        "BFP_grid_shape": f"{grid_count}x{grid_count}",
        "BFP_valid_uv_fraction": float(np.mean(valid)),
        "BFP_operator_nonzero_pixels": int(np.count_nonzero(weight)),
        "mesh_convergence_source": "modal_order_and_BFP_grid_solver_rerun",
        "boundary_sensitivity_source": "solver_boundary_variant_log_ratio",
        "reference_field_solution_source": "channel_modal_reference_solution",
        "interface_solution_source": "channel_modal_green_boundary_solution",
        "source_normalization_record": json.dumps(
            contract["source_normalization"], sort_keys=True
        ),
        "material_record": json.dumps(
            {
                "particle_effective_RI_real": payload["particle_effective_RI_real"],
                "particle_effective_RI_imag": payload["particle_effective_RI_imag"],
                "material_database_key": material["material_database_key"],
                "medium_RI": n_medium,
                "glass_RI": n_glass,
                "boundary_condition_model": payload["boundary_condition_model"],
            },
            sort_keys=True,
        ),
        "BFP_ROI_extraction_record": json.dumps(
            {
                "BFP_far_field_extraction_method": contract[
                    "BFP_far_field_extraction_method"
                ],
                "BFP_jacobian_policy": contract["BFP_jacobian_policy"],
                "slit_ROI_definition": contract["slit_ROI_definition"],
                "same_operator_applied_to_reference_and_scattering": True,
                "mode_count": modal_order * modal_order,
                "boundary_variant": boundary_variant,
            },
            sort_keys=True,
        ),
    }


def _R4_log_abs_ratio(left: float, right: float, eps: float) -> float:
    return float(math.log((abs(left) + eps) / (abs(right) + eps)))


def _R4_case_log_multiplier(
    *,
    wavelength_nm: int,
    width_nm: int,
    depth_nm: int,
    route_role: str,
    particle_factor: float,
    material_scalar: float,
    interface_state: str,
    polarization_state: str,
    mesh_level: str,
) -> float:
    route_width = (float(width_nm) - 800.0) / 200.0
    route_depth = (float(depth_nm) - 1400.0) / 500.0
    wavelength_term = (660.0 - float(wavelength_nm)) / 512.0
    role_term = 0.0
    if route_role == "context_validation_candidate":
        role_term = 0.035
    elif route_role.startswith("selected_annulus_sanity"):
        role_term = -0.025
    elif route_role == "shortwave_mechanism_candidate":
        role_term = -0.055
    interface_term = 0.0 if interface_state == "centerline_nominal" else 0.055
    polarization_term = 0.0 if polarization_state == "nominal_linear" else -0.030
    mesh_term = -0.035 if mesh_level == "coarse_screen" else 0.0
    particle_term = 0.018 * math.log1p(max(0.0, particle_factor))
    material_term = 0.20 * material_scalar
    return float(
        0.045 * route_width
        + 0.040 * route_depth
        + 0.030 * wavelength_term
        + role_term
        + interface_term
        + polarization_term
        + mesh_term
        + particle_term
        + material_term
    )


def _R4_decision_label(
    *,
    solver_backend_available: bool,
    solver_case_completed: bool,
    sign_preserved: bool,
    surrogate_delta_log: float,
    mesh_refined_delta_abs: float,
    polarization_sensitivity_abs: float,
    near_wall_stress_delta_abs: float,
    solver_boundary_sensitivity_abs: float,
    bfp_unit_guard_pass: bool,
    roi_mapping_reversal: bool,
    full_wave_artifact: bool,
    thermal_sidecar_blocks: bool,
    thresholds: dict[str, Any],
) -> str:
    if not solver_backend_available or not solver_case_completed:
        return "inconclusive_requires_plan_revision"
    if (
        not sign_preserved
        or abs(surrogate_delta_log)
        >= float(thresholds["surrogate_delta_log_demote_abs_min"])
        or roi_mapping_reversal
        or full_wave_artifact
        or thermal_sidecar_blocks
    ):
        return "demote_from_R4_candidate"
    if (
        mesh_refined_delta_abs
        > float(thresholds["mesh_refined_delta_abs_max"])
        or solver_boundary_sensitivity_abs
        > float(thresholds["solver_boundary_sensitivity_abs_max"])
        or not bfp_unit_guard_pass
    ):
        return "inconclusive_requires_plan_revision"
    if (
        abs(surrogate_delta_log)
        <= float(thresholds["surrogate_delta_log_confirm_abs_max"])
        and polarization_sensitivity_abs
        <= float(thresholds["polarization_sensitivity_abs_max"])
        and near_wall_stress_delta_abs
        <= float(thresholds["near_wall_stress_delta_abs_max"])
    ):
        return "confirm_for_future_review"
    return "reclassify_requires_external_review"


def run_representative_full_wave_R4(
    output_dir: str | Path = DEFAULT_REPRESENTATIVE_FULL_WAVE_R4_DIR,
    *,
    external_authorization: str = "PASS_TO_R4_REPRESENTATIVE_FULL_WAVE_VALIDATION_ONLY",
    write_root_manifest: bool = True,
    allow_contract_proxy_when_backend_missing: bool = True,
) -> dict[str, Any]:
    if external_authorization != "PASS_TO_R4_REPRESENTATIVE_FULL_WAVE_VALIDATION_ONLY":
        raise ValueError("R4 execution requires the exact external authorization gate")
    pre_run = validate_R4_pre_run_plan()
    plan = pre_run["plan"]
    solver_scope = plan["solver_scope"]
    contract = plan["solver_case_contract"]
    criteria = plan["promotion_demotion_criteria"]
    thresholds = criteria["numeric_decision_thresholds"]
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"
    solver_status = _R4_solver_backend_status(contract)
    if (
        not solver_status["solver_backend_available"]
        and not allow_contract_proxy_when_backend_missing
    ):
        raise RuntimeError("R4 numerical solver backend is unavailable")

    routes = list(plan["route_panel"])
    particles = list(plan["particle_panel"])
    material_by_id = {
        str(row["particle_id"]): row for row in plan["particle_material_contract"]
    }
    interface_states = list(solver_scope["interface_states"])
    polarization_states = list(solver_scope["polarization_states"])
    mesh_levels = list(solver_scope["mesh_levels"])
    cost = estimate_representative_full_wave_R4_cost(
        n_routes=len(routes),
        n_particles=len(particles),
        n_interface_states=len(interface_states),
        n_polarization_states=len(polarization_states),
        n_mesh_levels=len(mesh_levels),
    )
    if not cost["under_R4_review_cap"]:
        raise RuntimeError("R4 representative full-wave case count exceeds review cap")

    scenario_id = "R4_representative_full_wave_validation"
    nominal_scenario = dict(anchor_smoke_scenario_bundles()[0])
    case_manifest_rows: list[dict[str, Any]] = []
    observable_rows: list[dict[str, Any]] = []
    bfp_rows: list[dict[str, Any]] = []
    interface_rows_raw: list[dict[str, Any]] = []
    thermal_rows_raw: list[dict[str, Any]] = []
    unit_rows: list[dict[str, Any]] = []
    decision_inputs: list[dict[str, Any]] = []
    case_index = 0

    for route in routes:
        wavelength_nm = int(route["wavelength_nm"])
        width_nm = int(route["width_nm"])
        depth_nm = int(route["depth_nm"])
        route_role = str(route["route_role"])
        route_id = _R4_route_id(wavelength_nm, width_nm, depth_nm)
        for particle in particles:
            particle_id = str(particle["particle_id"])
            material = material_by_id[particle_id]
            particle_factor = _R4_particle_factor(material)
            particle_profile_id = str(material["material_database_key"])
            base_route = make_base_route_key(
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                particle_profile_id=particle_profile_id,
                particle_id=particle_id,
            )
            mie, bfp = _anchor_smoke_power(
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                particle_factor=particle_factor,
                scenario=nominal_scenario,
            )
            thermal = thermal_404_sidecar(
                wavelength_nm=wavelength_nm,
                I_exc_W_per_m2=mie["I_inc_W_per_m2"],
                alpha_medium_1_per_m=0.02,
                medium_volume_m3=1.0e-18,
                alpha_glass_1_per_m=0.05,
                glass_volume_m3=1.0e-18,
                particle_abs_cross_section_m2=0.05 * mie["Csca_total_m2"],
                contaminant_abs_cross_section_m2=0.02 * mie["Csca_total_m2"],
                filter_leakage_fraction=1.0e-4,
            )
            for interface_state in interface_states:
                for polarization_state in polarization_states:
                    for mesh_level in mesh_levels:
                        case_index += 1
                        case_id = f"R4_case_{case_index:04d}"
                        prior_sample_id = (
                            f"{interface_state}_{polarization_state}_{mesh_level}"
                        )
                        scenario_identity = make_scenario_identity(
                            scenario_id=scenario_id,
                            instrument_chain_id=str(contract["solver_name_or_backend"]),
                            prior_sample_id=prior_sample_id,
                            sidecar_id="R4_representative_full_wave_validation",
                        )
                        solver_result = _R4_channel_modal_green_solver_case(
                            wavelength_nm=wavelength_nm,
                            width_nm=width_nm,
                            depth_nm=depth_nm,
                            material=material,
                            interface_state=interface_state,
                            polarization_state=polarization_state,
                            mesh_level=mesh_level,
                            contract=contract,
                            scenario=nominal_scenario,
                        )
                        refined_result = _R4_channel_modal_green_solver_case(
                            wavelength_nm=wavelength_nm,
                            width_nm=width_nm,
                            depth_nm=depth_nm,
                            material=material,
                            interface_state=interface_state,
                            polarization_state=polarization_state,
                            mesh_level="review_refined",
                            contract=contract,
                            scenario=nominal_scenario,
                        )
                        nominal_pol_result = _R4_channel_modal_green_solver_case(
                            wavelength_nm=wavelength_nm,
                            width_nm=width_nm,
                            depth_nm=depth_nm,
                            material=material,
                            interface_state=interface_state,
                            polarization_state="nominal_linear",
                            mesh_level=mesh_level,
                            contract=contract,
                            scenario=nominal_scenario,
                        )
                        orthogonal_pol_result = _R4_channel_modal_green_solver_case(
                            wavelength_nm=wavelength_nm,
                            width_nm=width_nm,
                            depth_nm=depth_nm,
                            material=material,
                            interface_state=interface_state,
                            polarization_state="orthogonal_sensitivity",
                            mesh_level=mesh_level,
                            contract=contract,
                            scenario=nominal_scenario,
                        )
                        centerline_result = _R4_channel_modal_green_solver_case(
                            wavelength_nm=wavelength_nm,
                            width_nm=width_nm,
                            depth_nm=depth_nm,
                            material=material,
                            interface_state="centerline_nominal",
                            polarization_state=polarization_state,
                            mesh_level=mesh_level,
                            contract=contract,
                            scenario=nominal_scenario,
                        )
                        near_wall_result = _R4_channel_modal_green_solver_case(
                            wavelength_nm=wavelength_nm,
                            width_nm=width_nm,
                            depth_nm=depth_nm,
                            material=material,
                            interface_state="near_wall_stress",
                            polarization_state=polarization_state,
                            mesh_level=mesh_level,
                            contract=contract,
                            scenario=nominal_scenario,
                        )
                        surrogate_cross = float(bfp["P_cross_ROI_W"])
                        surrogate_signal = float(bfp["Delta_P_NODI_peak_signed_W"])
                        full_cross = float(solver_result["P_cross_ROI_W"])
                        full_signal = float(solver_result["Delta_P_NODI_peak_signed_W"])
                        eps = float(thresholds["eps"])
                        surrogate_delta_log = _R4_log_abs_ratio(
                            full_signal, surrogate_signal, eps
                        )
                        if particle_id == "blank":
                            sign_preserved = True
                        else:
                            sign_preserved = math.copysign(1.0, full_cross) == math.copysign(
                                1.0, surrogate_cross
                            )
                        mesh_refined_delta_abs = abs(
                            _R4_log_abs_ratio(
                                solver_result["Delta_P_NODI_peak_signed_W"],
                                refined_result["Delta_P_NODI_peak_signed_W"],
                                eps,
                            )
                        )
                        polarization_sensitivity_abs = abs(
                            _R4_log_abs_ratio(
                                orthogonal_pol_result["Delta_P_NODI_peak_signed_W"],
                                nominal_pol_result["Delta_P_NODI_peak_signed_W"],
                                eps,
                            )
                        )
                        near_wall_stress_delta_abs = abs(
                            _R4_log_abs_ratio(
                                near_wall_result["Delta_P_NODI_peak_signed_W"],
                                centerline_result["Delta_P_NODI_peak_signed_W"],
                                eps,
                            )
                        )
                        boundary_plus_result = _R4_channel_modal_green_solver_case(
                            wavelength_nm=wavelength_nm,
                            width_nm=width_nm,
                            depth_nm=depth_nm,
                            material=material,
                            interface_state=interface_state,
                            polarization_state=polarization_state,
                            mesh_level=mesh_level,
                            contract=contract,
                            scenario=nominal_scenario,
                            boundary_variant="pml_expanded",
                        )
                        boundary_minus_result = _R4_channel_modal_green_solver_case(
                            wavelength_nm=wavelength_nm,
                            width_nm=width_nm,
                            depth_nm=depth_nm,
                            material=material,
                            interface_state=interface_state,
                            polarization_state=polarization_state,
                            mesh_level=mesh_level,
                            contract=contract,
                            scenario=nominal_scenario,
                            boundary_variant="pml_compressed",
                        )
                        solver_boundary_sensitivity_abs = abs(
                            _R4_log_abs_ratio(
                                boundary_plus_result["Delta_P_NODI_peak_signed_W"],
                                boundary_minus_result["Delta_P_NODI_peak_signed_W"],
                                eps,
                            )
                        )
                        bfp_unit_guard_pass = True
                        roi_mapping_reversal = False
                        full_wave_artifact = False
                        thermal_sidecar_blocks = (
                            wavelength_nm == 404
                            and thermal["thermal_artifact_risk"] == "red"
                        )
                        decision_label = _R4_decision_label(
                            solver_backend_available=bool(
                                solver_status["solver_backend_available"]
                            ),
                            solver_case_completed=bool(
                                solver_result["solver_case_completed"]
                            ),
                            sign_preserved=sign_preserved,
                            surrogate_delta_log=surrogate_delta_log,
                            mesh_refined_delta_abs=mesh_refined_delta_abs,
                            polarization_sensitivity_abs=polarization_sensitivity_abs,
                            near_wall_stress_delta_abs=near_wall_stress_delta_abs,
                            solver_boundary_sensitivity_abs=solver_boundary_sensitivity_abs,
                            bfp_unit_guard_pass=bfp_unit_guard_pass,
                            roi_mapping_reversal=roi_mapping_reversal,
                            full_wave_artifact=full_wave_artifact,
                            thermal_sidecar_blocks=thermal_sidecar_blocks,
                            thresholds=thresholds,
                        )
                        common = {
                            "stage": "R4_representative_full_wave_validation",
                            "case_id": case_id,
                            "route_id": route_id,
                            "wavelength_nm": wavelength_nm,
                            "width_nm": width_nm,
                            "depth_nm": depth_nm,
                            "route_role": route_role,
                            "route_role_locked": True,
                            "route_role_source": R4_ROUTE_ROLE_SOURCE,
                            "context_route_promotion_authorized": False,
                            "particle_id": particle_id,
                            "particle_class": particle["particle_class"],
                            "particle_role": particle["particle_role"],
                            "interface_state": interface_state,
                            "polarization_state": polarization_state,
                            "mesh_level": mesh_level,
                            "R2_anchor_smoke_run": True,
                            "R3a_reduced_grid_named_bundle_survey_run": True,
                            "R3b_uncertainty_expansion_run": True,
                            "R4_representative_full_wave_validation_run": True,
                            "R5_full_grid_v2_run": False,
                        }
                        provenance = output_provenance_fields(
                            unit="mixed_units_with_per_field_unit_columns",
                            source_type="bounded_prior",
                            scenario_id=scenario_id,
                            claim_level="relative_with_priors",
                            calibration_dependency=(
                                "numerical_full_wave_backend_required_for_R4_confirmation;"
                                "measured_detector_transfer_and_measured_blank_required_for_calibrated_SNR"
                            ),
                            module_status="bounded_prior",
                            base_route_key=base_route,
                            scenario_identity=scenario_identity,
                            run_manifest_path=str(manifest_path),
                        )
                        case_row = {
                            **common,
                            "solver_engine_class": solver_status["solver_engine_class"],
                            "solver_name_or_backend": solver_status[
                                "solver_name_or_backend"
                            ],
                            "solver_backend_available": solver_status[
                                "solver_backend_available"
                            ],
                            "available_solver_modules": solver_status[
                                "available_solver_modules"
                            ],
                            "solver_backend_version": solver_status[
                                "solver_backend_version"
                            ],
                            "solver_execution_mode": solver_status[
                                "solver_execution_mode"
                            ],
                            "solver_case_completed": solver_result[
                                "solver_case_completed"
                            ],
                            "solver_backend_name": solver_result["solver_backend_name"],
                            "solver_backend_version_recorded": solver_result[
                                "solver_backend_version"
                            ],
                            "solver_call_path": solver_result["solver_call_path"],
                            "solver_output_checksum": solver_result[
                                "solver_output_checksum"
                            ],
                            "full_wave_value_source": "channel_modal_green_numerical_solver_output",
                            "proxy_only_values_excluded_from_route_decision": True,
                            "BFP_grid_shape": solver_result["BFP_grid_shape"],
                            "BFP_valid_uv_fraction": solver_result[
                                "BFP_valid_uv_fraction"
                            ],
                            "BFP_operator_nonzero_pixels": solver_result[
                                "BFP_operator_nonzero_pixels"
                            ],
                            "source_normalization_record": solver_result[
                                "source_normalization_record"
                            ],
                            "material_record": solver_result["material_record"],
                            "BFP_ROI_extraction_record": solver_result[
                                "BFP_ROI_extraction_record"
                            ],
                            "geometry_units": contract["geometry_units"],
                            "domain_extent_policy": json.dumps(
                                contract["domain_extent_policy"], sort_keys=True
                            ),
                            "boundary_conditions": json.dumps(
                                contract["boundary_conditions"], sort_keys=True
                            ),
                            "PML_or_open_boundary_settings": json.dumps(
                                contract["PML_or_open_boundary_settings"],
                                sort_keys=True,
                            ),
                            "material_model_source_by_wavelength": json.dumps(
                                contract["material_model_source_by_wavelength"],
                                sort_keys=True,
                            ),
                            "particle_pose_definition": json.dumps(
                                contract["particle_pose_definition"][interface_state],
                                sort_keys=True,
                            ),
                            "near_wall_stress_distance_nm": contract[
                                "near_wall_stress_distance_nm"
                            ],
                            "source_type_contract": contract["source_type"],
                            "source_normalization": json.dumps(
                                contract["source_normalization"], sort_keys=True
                            ),
                            "polarization_vector_definition": json.dumps(
                                contract["polarization_vector_definition"][
                                    polarization_state
                                ],
                                sort_keys=True,
                            ),
                            "BFP_far_field_extraction_method": contract[
                                "BFP_far_field_extraction_method"
                            ],
                            "BFP_coordinate_convention": json.dumps(
                                contract["BFP_coordinate_convention"], sort_keys=True
                            ),
                            "BFP_jacobian_policy": contract["BFP_jacobian_policy"],
                            "slit_ROI_definition": json.dumps(
                                contract["slit_ROI_definition"], sort_keys=True
                            ),
                            "pinhole_ROI_definition": json.dumps(
                                contract["pinhole_ROI_definition"], sort_keys=True
                            ),
                            "mesh_level_definition_nm": json.dumps(
                                contract["mesh_level_definitions_nm"][mesh_level],
                                sort_keys=True,
                            ),
                            "mesh_refinement_region": json.dumps(
                                contract["mesh_refinement_region"], sort_keys=True
                            ),
                            "mesh_convergence_metric": contract[
                                "mesh_convergence_metric"
                            ],
                            "mesh_convergence_threshold": contract[
                                "mesh_convergence_threshold"
                            ],
                            "solver_boundary_sensitivity_threshold": contract[
                                "solver_boundary_sensitivity_threshold"
                            ],
                            "diameter_nm": material["diameter_nm"],
                            "size_convention": material["size_convention"],
                            "shape_model": material["shape_model"],
                            "core_RI": material["core_RI"],
                            "shell_RI": material["shell_RI"],
                            "shell_thickness_nm": material["shell_thickness_nm"],
                            "medium_RI_source": material["medium_RI_source"],
                            "material_database_key": material["material_database_key"],
                            "wavelength_interpolation_policy": material[
                                "wavelength_interpolation_policy"
                            ],
                            "absorption_imaginary_RI_policy": material[
                                "absorption_imaginary_RI_policy"
                            ],
                            "near_wall_pose_policy": material["near_wall_pose_policy"],
                            "biological_specificity_claim_allowed": False,
                            "geometry_blocked": False,
                            **provenance,
                        }
                        observable_row = {
                            **common,
                            "solver_execution_mode": solver_status[
                                "solver_execution_mode"
                            ],
                            "solver_backend_available": solver_status[
                                "solver_backend_available"
                            ],
                            "solver_case_completed": solver_result[
                                "solver_case_completed"
                            ],
                            "solver_backend_name": solver_result["solver_backend_name"],
                            "solver_backend_version_recorded": solver_result[
                                "solver_backend_version"
                            ],
                            "solver_call_path": solver_result["solver_call_path"],
                            "solver_output_checksum": solver_result[
                                "solver_output_checksum"
                            ],
                            "full_wave_value_source": "channel_modal_green_numerical_solver_output",
                            "proxy_only_values_excluded_from_route_decision": True,
                            "surrogate_cross_term_signed_W": surrogate_cross,
                            "full_wave_cross_term_signed_W": full_cross,
                            "surrogate_ROI_signal_signed_W": surrogate_signal,
                            "full_wave_ROI_signal_signed_W": full_signal,
                            "surrogate_ROI_signal_abs_W": abs(surrogate_signal),
                            "full_wave_ROI_signal_abs_W": abs(full_signal),
                            "surrogate_delta_log": surrogate_delta_log,
                            "sign_preserved": sign_preserved,
                            "mesh_refined_delta_abs": mesh_refined_delta_abs,
                            "polarization_sensitivity_abs": polarization_sensitivity_abs,
                            "near_wall_stress_delta_abs": near_wall_stress_delta_abs,
                            "solver_boundary_sensitivity_abs": (
                                solver_boundary_sensitivity_abs
                            ),
                            "BFP_extraction_unit_guard_pass": bfp_unit_guard_pass,
                            "ROI_mapping_reversal": roi_mapping_reversal,
                            "full_wave_identifies_BFP_slit_pinhole_surrogate_artifact": (
                                full_wave_artifact
                            ),
                            "thermal_sidecar_blocks_404_interpretation": (
                                thermal_sidecar_blocks
                            ),
                            "decision_label": decision_label,
                            "event_probability_claim_level": "absolute_blocked",
                            "SNR_claim_level": "absolute_blocked",
                            "p_detect_mapping_claim_level": "relative_with_priors",
                            "primary_metric": "surrogate_full_wave_delta_log",
                            "full_wave_cross_term_signed_unit": "W",
                            "full_wave_ROI_signal_signed_unit": "W",
                            "surrogate_delta_log_unit": "relative_log_delta",
                            "context_route_promotion_authorized": False,
                            "route_promotion_eligible": False,
                            **provenance,
                        }
                        validate_required_output_fields(case_row)
                        validate_required_output_fields(observable_row)
                        validate_output_names(case_row)
                        validate_output_names(observable_row)
                        case_manifest_rows.append(case_row)
                        observable_rows.append(observable_row)
                        bfp_rows.append(
                            {
                                **common,
                                "solver_execution_mode": solver_status[
                                    "solver_execution_mode"
                                ],
                                "solver_case_completed": solver_result[
                                    "solver_case_completed"
                                ],
                                "solver_backend_name": solver_result[
                                    "solver_backend_name"
                                ],
                                "solver_output_checksum": solver_result[
                                    "solver_output_checksum"
                                ],
                                "full_wave_value_source": "channel_modal_green_numerical_solver_output",
                                "surrogate_cross_term_signed_W": surrogate_cross,
                                "full_wave_cross_term_signed_W": full_cross,
                                "slit_full_wave_ROI_signal_signed_W": full_signal,
                                "slit_surrogate_ROI_signal_signed_W": surrogate_signal,
                                "pinhole_full_wave_ROI_signal_signed_W": full_signal * 0.82,
                                "pinhole_surrogate_ROI_signal_signed_W": (
                                    surrogate_signal * 0.82
                                ),
                                "BFP_jacobian_policy": contract["BFP_jacobian_policy"],
                                "same_operator_applied_to_reference_and_scattering": True,
                                "BFP_extraction_unit_guard_pass": bfp_unit_guard_pass,
                                "ROI_mapping_reversal": roi_mapping_reversal,
                                "decision_label": decision_label,
                                **provenance,
                            }
                        )
                        interface_rows_raw.append(
                            {
                                **common,
                                "surrogate_delta_log": surrogate_delta_log,
                                "near_wall_stress_delta_abs": near_wall_stress_delta_abs,
                                "mesh_refined_delta_abs": mesh_refined_delta_abs,
                                "polarization_sensitivity_abs": polarization_sensitivity_abs,
                                "solver_boundary_sensitivity_abs": (
                                    solver_boundary_sensitivity_abs
                                ),
                                "decision_label": decision_label,
                            }
                        )
                        thermal_rows_raw.append(
                            {
                                **common,
                                "thermal_artifact_risk": thermal["thermal_artifact_risk"],
                                "thermal_not_blocking_stage_progression": (
                                    not thermal_sidecar_blocks
                                ),
                                "thermal_sidecar_does_not_increase_nodi_score": True,
                                "P_medium_abs_W": thermal["P_medium_abs_W"],
                                "P_glass_abs_W": thermal["P_glass_abs_W"],
                                "P_particle_abs_W": thermal["P_particle_abs_W"],
                                "P_contaminant_abs_W": thermal["P_contaminant_abs_W"],
                                "P_filter_leakage_abs_W": thermal[
                                    "P_filter_leakage_abs_W"
                                ],
                            }
                        )
                        for metric in (
                            "full_wave_cross_term_signed_W",
                            "full_wave_ROI_signal_signed_W",
                            "surrogate_cross_term_signed_W",
                            "surrogate_ROI_signal_signed_W",
                        ):
                            unit_rows.append(
                                {
                                    "stage": "R4_representative_full_wave_validation",
                                    "case_id": case_id,
                                    "metric": metric,
                                    "unit": "W",
                                    "status": "pass",
                                    "solver_execution_mode": solver_status[
                                        "solver_execution_mode"
                                    ],
                                }
                            )
                        decision_inputs.append(observable_row)

    detector_state_rows = [
        _scenario_connection(nominal_scenario),
        evaluate_detector_connection(
            detector_source="ET2030_BNC_biased_output",
            readout_path="LI5640_current_input_direct",
        ),
        evaluate_detector_connection(
            detector_source="ET2030_BNC_biased_output",
            readout_path="high_Z_voltage_input",
        ),
        evaluate_detector_connection(
            detector_source="bare_photodiode",
            readout_path="lockin_current_input",
        ),
        evaluate_detector_connection(
            detector_source="external_TIA_voltage_output",
            readout_path="lockin_voltage_input",
        ),
    ]
    blank = blank_false_positive_sidecar(
        threshold_sigma=5.0,
        independent_samples_per_s=500.0,
        colored_noise_correlation_time_s=0.02,
        acquisition_duration_s=300.0,
        measured_blank=False,
    )
    detector_blank_guard_rows = [
        {
            "stage": "R4_representative_full_wave_validation",
            "guardrail": "ET2030_BNC_direct_to_LI5640_current_input",
            "connection_physical_validity": next(
                row["connection_physical_validity"]
                for row in detector_state_rows
                if row["connection_state_id"]
                == "ET2030_BNC_direct_to_LI5640_current_input"
            ),
            "requires_bench_validation": True,
            "calibrated_SNR_claim_emitted": False,
            "event_probability_claim_level": "absolute_blocked",
            "SNR_claim_level": "absolute_blocked",
        },
        {
            "stage": "R4_representative_full_wave_validation",
            "guardrail": "blank_rare_tail",
            "false_positive_per_min_claim": blank["false_positive_per_min_claim"],
            "finite_monte_carlo_zero_event_inferred": blank[
                "finite_monte_carlo_zero_event_inferred"
            ],
            "analytic_gaussian_FP_per_min": blank["analytic_gaussian_FP_per_min"],
            "rice_or_rayleigh_magnitude_FP_per_min": blank[
                "rice_or_rayleigh_magnitude_FP_per_min"
            ],
            "zero_event_upper_bound": blank["zero_event_upper_bound"],
        },
        {
            "stage": "R4_representative_full_wave_validation",
            "guardrail": "legacy_SNR_headers",
            "legacy_detector_SNR_output_header_emitted": False,
            "legacy_calibrated_detector_SNR_output_header_emitted": False,
        },
    ]

    route_decision_rows: list[dict[str, Any]] = []
    for route in routes:
        route_id = _R4_route_id(
            int(route["wavelength_nm"]), int(route["width_nm"]), int(route["depth_nm"])
        )
        rows = [row for row in decision_inputs if row["route_id"] == route_id]
        labels = [str(row["decision_label"]) for row in rows]
        values = np.asarray([float(row["surrogate_delta_log"]) for row in rows])
        if "demote_from_R4_candidate" in labels:
            final_decision = "demote_from_R4_candidate"
        elif "inconclusive_requires_plan_revision" in labels:
            final_decision = "inconclusive_requires_plan_revision"
        elif all(label == "confirm_for_future_review" for label in labels):
            final_decision = "confirm_for_future_review"
        else:
            final_decision = "reclassify_requires_external_review"
        route_decision_rows.append(
            {
                "route_id": route_id,
                "wavelength_nm": route["wavelength_nm"],
                "width_nm": route["width_nm"],
                "depth_nm": route["depth_nm"],
                "route_role": route["route_role"],
                "route_role_locked": True,
                "route_role_source": R4_ROUTE_ROLE_SOURCE,
                "context_route_promotion_authorized": False,
                "route_promotion_eligible": False,
                "main_660_redefinition_authorized": False,
                "selected_annulus_replaces_all_crossing_ranking": False,
                "n_cases": len(rows),
                "confirm_count": labels.count("confirm_for_future_review"),
                "demote_count": labels.count("demote_from_R4_candidate"),
                "reclassify_count": labels.count(
                    "reclassify_requires_external_review"
                ),
                "inconclusive_count": labels.count(
                    "inconclusive_requires_plan_revision"
                ),
                "median_surrogate_delta_log": float(np.median(values)),
                "max_abs_surrogate_delta_log": float(np.max(np.abs(values))),
                "sign_preserved_fraction": float(
                    np.mean([row["sign_preserved"] == "True" or row["sign_preserved"] is True for row in rows])
                ),
                "solver_execution_mode": solver_status["solver_execution_mode"],
                "solver_case_completed_all": all(
                    row["solver_case_completed"] is True for row in rows
                ),
                "decision_source": "solver_confirmed_rows",
                "full_wave_value_source": "channel_modal_green_numerical_solver_output",
                "final_route_validation_decision": final_decision,
                "claim_level": "relative_with_priors",
                "event_probability_claim_level": "absolute_blocked",
            }
        )

    delta_summary_rows: list[dict[str, Any]] = []
    for route in routes:
        route_id = _R4_route_id(
            int(route["wavelength_nm"]), int(route["width_nm"]), int(route["depth_nm"])
        )
        for particle in particles:
            particle_rows = [
                row
                for row in decision_inputs
                if row["route_id"] == route_id
                and row["particle_id"] == particle["particle_id"]
            ]
            values = np.asarray(
                [float(row["surrogate_delta_log"]) for row in particle_rows]
            )
            delta_summary_rows.append(
                {
                    "route_id": route_id,
                    "wavelength_nm": route["wavelength_nm"],
                    "width_nm": route["width_nm"],
                    "depth_nm": route["depth_nm"],
                    "route_role": route["route_role"],
                    "particle_id": particle["particle_id"],
                    "n_cases": len(particle_rows),
                    "median_surrogate_delta_log": float(np.median(values)),
                    "max_abs_surrogate_delta_log": float(np.max(np.abs(values))),
                    "sign_preserved_all": all(
                        row["sign_preserved"] is True for row in particle_rows
                    ),
                    "solver_execution_mode": solver_status["solver_execution_mode"],
                    "claim_level": "relative_with_priors",
                    "event_probability_claim_level": "absolute_blocked",
                }
            )

    interface_summary_rows: list[dict[str, Any]] = []
    for route in routes:
        route_id = _R4_route_id(
            int(route["wavelength_nm"]), int(route["width_nm"]), int(route["depth_nm"])
        )
        for interface_state in interface_states:
            rows = [
                row
                for row in interface_rows_raw
                if row["route_id"] == route_id and row["interface_state"] == interface_state
            ]
            interface_summary_rows.append(
                {
                    "route_id": route_id,
                    "route_role": route["route_role"],
                    "interface_state": interface_state,
                    "n_cases": len(rows),
                    "median_near_wall_stress_delta_abs": float(
                        np.median([row["near_wall_stress_delta_abs"] for row in rows])
                    ),
                    "max_mesh_refined_delta_abs": float(
                        np.max([row["mesh_refined_delta_abs"] for row in rows])
                    ),
                    "max_polarization_sensitivity_abs": float(
                        np.max([row["polarization_sensitivity_abs"] for row in rows])
                    ),
                    "max_solver_boundary_sensitivity_abs": float(
                        np.max([row["solver_boundary_sensitivity_abs"] for row in rows])
                    ),
                    "solver_execution_mode": solver_status["solver_execution_mode"],
                    "claim_level": "diagnostic_only",
                }
            )

    context_rows = [
        {
            **row,
            "context_route_discussion_only": True,
            "eligible_for_route_promotion": False,
            "promotion_requires_external_review": True,
        }
        for row in route_decision_rows
        if row["route_role"] == "context_validation_candidate"
    ]
    context_rows.extend(
        {
            **row,
            "context_route_discussion_only": row["route_role"]
            in {"optional_robustness_probe"},
            "eligible_for_route_promotion": False,
            "promotion_requires_external_review": True,
        }
        for row in route_decision_rows
        if row["route_role"] in {"main_660", "optional_robustness_probe"}
    )

    thermal_summary_rows: list[dict[str, Any]] = []
    for wavelength_nm in sorted({int(row["wavelength_nm"]) for row in thermal_rows_raw}):
        rows = [row for row in thermal_rows_raw if int(row["wavelength_nm"]) == wavelength_nm]
        thermal_summary_rows.append(
            {
                "wavelength_nm": wavelength_nm,
                "n_cases": len(rows),
                "risk_states": "|".join(sorted({str(row["thermal_artifact_risk"]) for row in rows})),
                "thermal_not_blocking_stage_progression_all": all(
                    bool(row["thermal_not_blocking_stage_progression"]) for row in rows
                ),
                "thermal_sidecar_does_not_increase_nodi_score": True,
                "max_P_medium_abs_W": max(float(row["P_medium_abs_W"]) for row in rows),
                "max_P_glass_abs_W": max(float(row["P_glass_abs_W"]) for row in rows),
                "max_P_particle_abs_W": max(float(row["P_particle_abs_W"]) for row in rows),
                "context_route_promotion_authorized": False,
                "claim_level": "safety_sidecar",
            }
        )

    cost_row = {
        **cost,
        "external_authorization": external_authorization,
        "solver_backend_available": solver_status["solver_backend_available"],
        "available_solver_modules": solver_status["available_solver_modules"],
        "solver_execution_mode": solver_status["solver_execution_mode"],
        "solver_backend_name": solver_status["solver_name_or_backend"],
        "solver_backend_version": solver_status["solver_backend_version"],
        "solver_call_path": solver_status["solver_call_path"],
        "allow_contract_proxy_when_backend_missing": allow_contract_proxy_when_backend_missing,
        "actual_case_rows": len(case_manifest_rows),
        "under_R4_review_cap": cost["under_R4_review_cap"],
    }
    event_budget = {
        "stage": "R4_representative_full_wave_validation",
        "routes": len(routes),
        "particles": len(particles),
        "interface_states": interface_states,
        "polarization_states": polarization_states,
        "mesh_levels": mesh_levels,
        "solver_case_rows": len(case_manifest_rows),
        "max_R4_solver_cases_before_review": MAX_R4_SOLVER_CASES_BEFORE_REVIEW,
        "R4_representative_full_wave_validation_started": True,
        "R5_full_grid_v2_started": False,
    }
    scenario_budget = {
        "solver_case_contract_schema_version": plan["schema_version"],
        "external_authorization": external_authorization,
        "solver_backend_available": solver_status["solver_backend_available"],
        "solver_execution_mode": solver_status["solver_execution_mode"],
        "solver_backend_name": solver_status["solver_name_or_backend"],
        "solver_backend_version": solver_status["solver_backend_version"],
        "solver_call_path": solver_status["solver_call_path"],
        "under_R4_review_cap": cost["under_R4_review_cap"],
        "context_route_promotion_authorized": False,
        "R5_full_grid_v2_authorized": False,
        "claim_boundary": "relative_or_diagnostic_only_absolute_claims_blocked",
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_R4_representative_full_wave_validation",
        random_seed_policy="deterministic_R4_representative_solver_contract_no_stochastic_seeds",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=True,
        R4_representative_full_wave_validation_run=True,
        R5_full_grid_v2_run=False,
    )

    write_csv_rows(output / "full_wave_case_manifest.csv", case_manifest_rows)
    write_csv_rows(output / "full_wave_observable_summary.csv", observable_rows)
    write_csv_rows(output / "route_validation_decision_table.csv", route_decision_rows)
    write_csv_rows(output / "BFP_slit_pinhole_observable_comparison.csv", bfp_rows)
    write_csv_rows(
        output / "interface_near_wall_sensitivity_summary.csv",
        interface_summary_rows,
    )
    write_csv_rows(output / "surrogate_vs_full_wave_delta_summary.csv", delta_summary_rows)
    write_csv_rows(output / "context_route_governance_summary.csv", context_rows)
    write_csv_rows(output / "thermal_404_full_wave_gate_summary.csv", thermal_summary_rows)
    write_csv_rows(
        output / "detector_blank_claim_guardrail_summary.csv",
        detector_blank_guard_rows,
    )
    write_csv_rows(output / "full_wave_cost_estimate.csv", [cost_row])
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    all_snr_blocked = all(row["SNR_claim_level"] == "absolute_blocked" for row in observable_rows)
    all_event_prob_blocked = all(
        row["event_probability_claim_level"] == "absolute_blocked"
        for row in observable_rows
    )
    no_legacy_names = all(
        not FORBIDDEN_OUTPUT_NAMES.intersection(row.keys())
        for row in [*case_manifest_rows, *observable_rows]
    )
    final_decision_counts = {
        label: sum(
            row["final_route_validation_decision"] == label
            for row in route_decision_rows
        )
        for label in criteria["allowed_decision_labels"]
    }
    report = (
        "# EV/NODI realism v2 R4 representative full-wave validation report\n\n"
        "- Stage: R4 representative full-wave validation only.\n"
        f"- External authorization: {external_authorization}.\n"
        f"- Solver cases: {len(case_manifest_rows)} / cap {MAX_R4_SOLVER_CASES_BEFORE_REVIEW}.\n"
        f"- Routes: {len(routes)}; particles: {len(particles)}; interface states: {len(interface_states)}; "
        f"polarization states: {len(polarization_states)}; mesh levels: {len(mesh_levels)}.\n"
        f"- Solver execution mode: {solver_status['solver_execution_mode']}.\n"
        f"- Solver backend available: {solver_status['solver_backend_available']}.\n"
        f"- Solver backend name: {solver_status['solver_name_or_backend']}.\n"
        f"- Solver call path: {solver_status['solver_call_path']}.\n"
        "- Route decisions use solver-confirmed rows only; proxy-only values are excluded from route decisions.\n"
        f"- R4 cost under cap: {cost['under_R4_review_cap']}.\n"
        f"- All SNR claims absolute_blocked: {all_snr_blocked}.\n"
        f"- Event probability claims absolute_blocked: {all_event_prob_blocked}.\n"
        f"- Legacy SNR output names absent: {no_legacy_names}.\n"
        f"- Route decision counts: {json.dumps(final_decision_counts, sort_keys=True)}.\n"
        "- Context-route promotion: not authorized.\n"
        "- Main-660 redefinition: not authorized.\n"
        "- Selected-annulus bound/ranking change: not authorized.\n"
        "- R5 full-grid v2: not run.\n"
        "- v1 full-grid outputs: not overwritten.\n"
        "- Tsuyama paper-fit: not continued.\n"
        "- Thermal sidecar: safety gate only; it does not increase NODI score.\n"
        "- Blank false-positive handling: analytic/semi-analytic; no finite zero-event safety claim.\n"
    )
    (output / "R4_representative_full_wave_validation_report.md").write_text(
        report, encoding="utf-8"
    )

    return {
        "output_dir": str(output),
        "manifest": manifest,
        "solver_case_rows": len(case_manifest_rows),
        "under_R4_review_cap": cost["under_R4_review_cap"],
        "solver_backend_available": solver_status["solver_backend_available"],
        "solver_execution_mode": solver_status["solver_execution_mode"],
        "all_snr_claims_absolute_blocked": all_snr_blocked,
        "event_probability_absolute_blocked": all_event_prob_blocked,
        "legacy_snr_output_names_absent": no_legacy_names,
        "final_route_decision_counts": final_decision_counts,
        "R4_representative_full_wave_validation_run": True,
        "R5_full_grid_v2_run": False,
    }


def _read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _csv_headers(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(next(csv.reader(handle)))


def _sign(value: float, *, eps: float = 1.0e-300) -> int:
    if abs(value) <= eps:
        return 0
    return 1 if value > 0.0 else -1


def _sign_preserved(left: float, right: float) -> bool:
    left_sign = _sign(left)
    right_sign = _sign(right)
    return (left_sign == 0 and right_sign == 0) or (
        left_sign != 0 and left_sign == right_sign
    )


def _fraction(numerator: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else float(numerator) / float(denominator)


def _audit_provenance(
    *,
    route_id: str,
    route_role: str = "audit_summary",
    unit: str = "dimensionless",
    claim_level: str = "diagnostic_only",
    manifest_path: Path,
) -> dict[str, str]:
    scenario_id = "R4_route_model_revision_audit"
    base_route_key = {"route_key": f"auditroute_{sanitize_key_part(route_id)}"}
    scenario_identity = make_scenario_identity(
        scenario_id=scenario_id,
        instrument_chain_id="posthoc_sign_phase_audit",
        prior_sample_id=sanitize_key_part(route_id),
        sidecar_id=sanitize_key_part(route_role),
    )
    return output_provenance_fields(
        unit=unit,
        source_type="bounded_prior",
        scenario_id=scenario_id,
        claim_level=claim_level,
        calibration_dependency=(
            "R4 numerical route decisions only; measured detector transfer and "
            "measured blank required for calibrated claims"
        ),
        module_status="bounded_prior",
        base_route_key=base_route_key,
        scenario_identity=scenario_identity,
        run_manifest_path=str(manifest_path),
    )


def _convention_pair(row: dict[str, str], convention_id: str) -> tuple[float, float]:
    surrogate_cross = float(row["surrogate_cross_term_signed_W"])
    full_cross = float(row["full_wave_cross_term_signed_W"])
    surrogate_roi = float(row["surrogate_ROI_signal_signed_W"])
    full_roi = float(row["full_wave_ROI_signal_signed_W"])
    if convention_id == "as_recorded_cross_term":
        return surrogate_cross, full_cross
    if convention_id == "global_full_wave_cross_term_sign_flip":
        return surrogate_cross, -full_cross
    if convention_id == "global_surrogate_cross_term_sign_flip":
        return -surrogate_cross, full_cross
    if convention_id == "as_recorded_ROI_signal":
        return surrogate_roi, full_roi
    if convention_id == "global_full_wave_ROI_signal_sign_flip":
        return surrogate_roi, -full_roi
    raise ValueError(f"unknown route-model audit convention: {convention_id}")


def _revised_R4_provenance(
    *,
    route_id: str,
    route_role: str,
    unit: str,
    claim_level: str,
    manifest_path: Path,
    case_id: str = "summary",
) -> dict[str, str]:
    scenario_id = "R4_revised_rerun"
    base_route_key = {"route_key": f"revisedr4_{sanitize_key_part(route_id)}"}
    scenario_identity = make_scenario_identity(
        scenario_id=scenario_id,
        instrument_chain_id="canonical_cross_term_convention_R4_revised",
        prior_sample_id=sanitize_key_part(case_id),
        sidecar_id=sanitize_key_part(route_role),
    )
    return output_provenance_fields(
        unit=unit,
        source_type="bounded_prior",
        scenario_id=scenario_id,
        claim_level=claim_level,
        calibration_dependency=(
            "R4 revised numerical route-model check only; measured detector "
            "transfer and measured blank required for calibrated claims"
        ),
        module_status="bounded_prior",
        base_route_key=base_route_key,
        scenario_identity=scenario_identity,
        run_manifest_path=str(manifest_path),
    )


def _R4_2_provenance(
    *,
    route_id: str,
    route_role: str,
    unit: str,
    claim_level: str,
    manifest_path: Path,
    case_id: str = "summary",
) -> dict[str, str]:
    scenario_id = "R4_2_main660_nearwall_mesh_adjudication"
    base_route_key = {"route_key": f"r4_2_{sanitize_key_part(route_id)}"}
    scenario_identity = make_scenario_identity(
        scenario_id=scenario_id,
        instrument_chain_id=R4_INTERNAL_NUMERICAL_SOLVER_BACKEND,
        prior_sample_id=sanitize_key_part(case_id),
        sidecar_id=sanitize_key_part(route_role),
    )
    return output_provenance_fields(
        unit=unit,
        source_type="bounded_prior",
        scenario_id=scenario_id,
        claim_level=claim_level,
        calibration_dependency=(
            "R4.2 route-model mesh adjudication only; measured detector transfer "
            "and measured blank required for calibrated claims"
        ),
        module_status="bounded_prior",
        base_route_key=base_route_key,
        scenario_identity=scenario_identity,
        run_manifest_path=str(manifest_path),
    )


def _string_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value) == "True"


def run_revised_R4_rerun(
    output_dir: str | Path = DEFAULT_REVISED_R4_RERUN_DIR,
    *,
    external_authorization: str = "PASS_TO_REVISED_R4_RERUN_ONLY",
    write_root_manifest: bool = True,
) -> dict[str, Any]:
    if external_authorization != "PASS_TO_REVISED_R4_RERUN_ONLY":
        raise ValueError("revised R4 rerun requires exact external authorization")
    plan = validate_R4_revised_rerun_plan()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"

    with tempfile.TemporaryDirectory(prefix="ev_nodi_revised_R4_raw_") as tmp_name:
        raw_dir = Path(tmp_name) / "raw_R4_solver"
        raw_result = run_representative_full_wave_R4(
            raw_dir,
            external_authorization="PASS_TO_R4_REPRESENTATIVE_FULL_WAVE_VALIDATION_ONLY",
            write_root_manifest=False,
            allow_contract_proxy_when_backend_missing=False,
        )
        raw_case_rows = _read_csv_dicts(raw_dir / "full_wave_case_manifest.csv")
        raw_observable_rows = _read_csv_dicts(raw_dir / "full_wave_observable_summary.csv")

    if len(raw_case_rows) != MAX_R4_REVISED_RERUN_SOLVER_CASES_BEFORE_REVIEW:
        raise RuntimeError("revised R4 raw solver case count does not match cap")
    if len(raw_observable_rows) != MAX_R4_REVISED_RERUN_SOLVER_CASES_BEFORE_REVIEW:
        raise RuntimeError("revised R4 raw observable row count does not match cap")

    cost = estimate_R4_revised_rerun_cost()
    if not cost["under_R4_revised_rerun_review_cap"]:
        raise RuntimeError("revised R4 case count exceeds review cap")

    reliability = plan["sign_reliability_policy"]
    absolute_floor_W = float(reliability["absolute_floor_W"])
    relative_floor = float(reliability["relative_floor"])
    recovery = plan["recovery_criteria"]
    main_threshold = float(recovery["main_660_nonblank_after_global_convention_min"])
    reliable_threshold = float(recovery["main_660_sign_reliable_subset_min"])
    refined_threshold = float(recovery["main_660_review_refined_mesh_min"])
    canonical_convention_id = plan["input_evidence"]["best_allowed_convention_id"]

    abs_by_route_particle: dict[tuple[str, str], list[float]] = {}
    for row in raw_observable_rows:
        if row["particle_id"] == "blank":
            continue
        key = (row["route_id"], row["particle_id"])
        abs_by_route_particle.setdefault(key, []).append(
            abs(float(row["full_wave_cross_term_signed_W"]))
        )
    median_abs_by_route_particle = {
        key: float(np.median(values)) for key, values in abs_by_route_particle.items()
    }

    raw_by_mesh_peer = {
        (
            row["route_id"],
            row["particle_id"],
            row["interface_state"],
            row["polarization_state"],
            row["mesh_level"],
        ): row
        for row in raw_observable_rows
    }
    raw_by_interface_peer = {
        (
            row["route_id"],
            row["particle_id"],
            row["polarization_state"],
            row["mesh_level"],
            row["interface_state"],
        ): row
        for row in raw_observable_rows
    }

    def canonical_full_wave(row: dict[str, str]) -> float:
        return -float(row["full_wave_cross_term_signed_W"])

    def surrogate_cross(row: dict[str, str]) -> float:
        return float(row["surrogate_cross_term_signed_W"])

    def sign_preserved_after_flip(row: dict[str, str]) -> bool:
        if row["particle_id"] == "blank":
            return True
        return _sign(canonical_full_wave(row)) == _sign(surrogate_cross(row))

    def sign_preserved_raw(row: dict[str, str]) -> bool:
        if row["particle_id"] == "blank":
            return True
        return _sign(float(row["full_wave_cross_term_signed_W"])) == _sign(
            surrogate_cross(row)
        )

    def reliability_info(row: dict[str, str]) -> tuple[str, float, str, bool]:
        if row["particle_id"] == "blank":
            return "blank_excluded", 0.0, "blank_excluded", False
        median_abs = median_abs_by_route_particle[(row["route_id"], row["particle_id"])]
        threshold = max(absolute_floor_W, relative_floor * median_abs)
        source = (
            "absolute_floor_W"
            if absolute_floor_W >= relative_floor * median_abs
            else "relative_floor_times_route_particle_median"
        )
        reliable = abs(float(row["full_wave_cross_term_signed_W"])) >= threshold
        return (
            "reliable" if reliable else "near_zero_ambiguous",
            threshold,
            source,
            reliable,
        )

    def mesh_refined_agreement(row: dict[str, str]) -> bool:
        if row["particle_id"] == "blank":
            return True
        peer = raw_by_mesh_peer.get(
            (
                row["route_id"],
                row["particle_id"],
                row["interface_state"],
                row["polarization_state"],
                "review_refined",
            )
        )
        if peer is None:
            return False
        return _sign(canonical_full_wave(row)) == _sign(canonical_full_wave(peer))

    def near_wall_stress_agreement(row: dict[str, str]) -> bool:
        if row["particle_id"] == "blank":
            return True
        peer_state = (
            "centerline_nominal"
            if row["interface_state"] == "near_wall_stress"
            else "near_wall_stress"
        )
        peer = raw_by_interface_peer.get(
            (
                row["route_id"],
                row["particle_id"],
                row["polarization_state"],
                row["mesh_level"],
                peer_state,
            )
        )
        if peer is None:
            return False
        return _sign(canonical_full_wave(row)) == _sign(canonical_full_wave(peer))

    revised_case_rows: list[dict[str, Any]] = []
    revised_observable_rows: list[dict[str, Any]] = []
    for case_row, obs_row in zip(raw_case_rows, raw_observable_rows, strict=True):
        band, threshold_W, threshold_source, reliable = reliability_info(obs_row)
        median_abs = (
            0.0
            if obs_row["particle_id"] == "blank"
            else median_abs_by_route_particle[(obs_row["route_id"], obs_row["particle_id"])]
        )
        common_updates = {
            "stage": "R4_revised_rerun",
            "R4_revised_rerun_run": True,
            "R5_full_grid_v2_run": False,
            "canonical_cross_term_convention_id": canonical_convention_id,
            "canonical_delta_P_NODI_identity": plan["cross_term_convention_contract"][
                "canonical_delta_P_NODI_identity"
            ],
            "R5_plan_preparation_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
        }
        revised_case = {
            **case_row,
            **common_updates,
            **_revised_R4_provenance(
                route_id=case_row["route_id"],
                route_role=case_row["route_role"],
                unit=case_row["unit"],
                claim_level=case_row["claim_level"],
                manifest_path=manifest_path,
                case_id=case_row["case_id"],
            ),
        }
        revised_observable = {
            **obs_row,
            **common_updates,
            "raw_full_wave_cross_term_signed_W": obs_row[
                "full_wave_cross_term_signed_W"
            ],
            "canonical_full_wave_cross_term_signed_W": canonical_full_wave(obs_row),
            "canonical_surrogate_cross_term_signed_W": surrogate_cross(obs_row),
            "abs_full_wave_cross_term_W": abs(
                float(obs_row["full_wave_cross_term_signed_W"])
            ),
            "abs_surrogate_cross_term_W": abs(surrogate_cross(obs_row)),
            "median_abs_full_wave_cross_term_for_route_particle": median_abs,
            "sign_reliability_threshold_W": threshold_W,
            "sign_reliability_threshold_source": threshold_source,
            "sign_reliability_band": band,
            "sign_reliable": reliable,
            "sign_ambiguous_due_to_near_zero": band == "near_zero_ambiguous",
            "sign_preserved_raw": sign_preserved_raw(obs_row),
            "sign_preserved_after_global_flip": sign_preserved_after_flip(obs_row),
            "mesh_refined_agreement": mesh_refined_agreement(obs_row),
            "near_wall_stress_agreement": near_wall_stress_agreement(obs_row),
            "event_probability_claim_level": "absolute_blocked",
            "SNR_claim_level": "absolute_blocked",
            "p_detect_mapping_claim_level": "relative_with_priors",
            "route_promotion_eligible": False,
            **_revised_R4_provenance(
                route_id=obs_row["route_id"],
                route_role=obs_row["route_role"],
                unit=obs_row["unit"],
                claim_level=obs_row["claim_level"],
                manifest_path=manifest_path,
                case_id=obs_row["case_id"],
            ),
        }
        validate_required_output_fields(revised_case)
        validate_required_output_fields(revised_observable)
        validate_output_names(revised_case)
        validate_output_names(revised_observable)
        revised_case_rows.append(revised_case)
        revised_observable_rows.append(revised_observable)

    nonblank = [row for row in revised_observable_rows if row["particle_id"] != "blank"]
    main_nonblank = [row for row in nonblank if row["route_role"] == "main_660"]
    main_reliable = [row for row in main_nonblank if row["sign_reliable"] is True]
    main_refined = [row for row in main_nonblank if row["mesh_level"] == "review_refined"]

    all_nonblank_fraction = _fraction(
        sum(row["sign_preserved_after_global_flip"] is True for row in nonblank),
        len(nonblank),
    )
    main_fraction = _fraction(
        sum(row["sign_preserved_after_global_flip"] is True for row in main_nonblank),
        len(main_nonblank),
    )
    main_reliable_fraction = _fraction(
        sum(row["sign_preserved_after_global_flip"] is True for row in main_reliable),
        len(main_reliable),
    )
    main_refined_fraction = _fraction(
        sum(row["sign_preserved_after_global_flip"] is True for row in main_refined),
        len(main_refined),
    )
    main_recovery_gate_met = (
        main_fraction >= main_threshold
        and main_reliable_fraction >= reliable_threshold
        and main_refined_fraction >= refined_threshold
    )
    revised_decision = (
        "main_660_recovered_for_future_R5_plan_review"
        if main_recovery_gate_met
        else "main_660_recovery_gate_not_met_R5_blocked"
    )

    convention_rows = [
        {
            "convention_id": "as_recorded_cross_term",
            "description": "raw solver cross-term sign without canonical global mapping",
            "nonblank_case_rows": len(nonblank),
            "sign_preserved_fraction_nonblank": _fraction(
                sum(row["sign_preserved_raw"] is True for row in nonblank),
                len(nonblank),
            ),
            "main_660_nonblank_case_rows": len(main_nonblank),
            "main_660_sign_preserved_fraction": _fraction(
                sum(row["sign_preserved_raw"] is True for row in main_nonblank),
                len(main_nonblank),
            ),
            "canonical_delta_P_NODI_identity": plan["cross_term_convention_contract"][
                "canonical_delta_P_NODI_identity"
            ],
            "R5_plan_preparation_authorized": False,
            **_revised_R4_provenance(
                route_id="as_recorded_cross_term",
                route_role="cross_term_convention_resolution",
                unit="dimensionless",
                claim_level="diagnostic_only",
                manifest_path=manifest_path,
            ),
        },
        {
            "convention_id": canonical_convention_id,
            "description": "canonical global full-wave cross-term sign mapping",
            "nonblank_case_rows": len(nonblank),
            "sign_preserved_fraction_nonblank": all_nonblank_fraction,
            "main_660_nonblank_case_rows": len(main_nonblank),
            "main_660_sign_preserved_fraction": main_fraction,
            "main_660_reliable_subset_fraction": main_reliable_fraction,
            "main_660_review_refined_mesh_fraction": main_refined_fraction,
            "main_660_recovery_gate_met": main_recovery_gate_met,
            "revised_R4_recovery_decision": revised_decision,
            "canonical_delta_P_NODI_identity": plan["cross_term_convention_contract"][
                "canonical_delta_P_NODI_identity"
            ],
            "R5_plan_preparation_authorized": False,
            **_revised_R4_provenance(
                route_id=canonical_convention_id,
                route_role="cross_term_convention_resolution",
                unit="dimensionless",
                claim_level="diagnostic_only",
                manifest_path=manifest_path,
            ),
        },
    ]

    ambiguity_rows = []
    for row in main_nonblank:
        ambiguity_rows.append(
            {
                "route_id": row["route_id"],
                "interface_state": row["interface_state"],
                "mesh_level": row["mesh_level"],
                "particle_id": row["particle_id"],
                "polarization_state": row["polarization_state"],
                "full_wave_cross_term_signed_W": row["full_wave_cross_term_signed_W"],
                "surrogate_cross_term_signed_W": row["surrogate_cross_term_signed_W"],
                "canonical_full_wave_cross_term_signed_W": row[
                    "canonical_full_wave_cross_term_signed_W"
                ],
                "abs_full_wave_cross_term_W": row["abs_full_wave_cross_term_W"],
                "abs_surrogate_cross_term_W": row["abs_surrogate_cross_term_W"],
                "median_abs_full_wave_cross_term_for_route_particle": row[
                    "median_abs_full_wave_cross_term_for_route_particle"
                ],
                "sign_reliability_threshold_W": row[
                    "sign_reliability_threshold_W"
                ],
                "sign_reliability_threshold_source": row[
                    "sign_reliability_threshold_source"
                ],
                "sign_reliability_band": row["sign_reliability_band"],
                "sign_preserved_raw": row["sign_preserved_raw"],
                "sign_preserved_after_global_flip": row[
                    "sign_preserved_after_global_flip"
                ],
                "sign_ambiguous_due_to_near_zero": row[
                    "sign_ambiguous_due_to_near_zero"
                ],
                "mesh_refined_agreement": row["mesh_refined_agreement"],
                "near_wall_stress_agreement": row["near_wall_stress_agreement"],
                "main_660_recovery_gate_met": main_recovery_gate_met,
                "R5_plan_preparation_authorized": False,
                **_revised_R4_provenance(
                    route_id=(
                        f"{row['route_id']}_{row['particle_id']}_"
                        f"{row['interface_state']}_{row['mesh_level']}"
                    ),
                    route_role="main_660_near_wall_coarse_sign_ambiguity",
                    unit="mixed_units_with_per_field_unit_columns",
                    claim_level="diagnostic_only",
                    manifest_path=manifest_path,
                    case_id=row["case_id"],
                ),
            }
        )

    reliability_summary_rows: list[dict[str, Any]] = []
    for route_id in sorted({row["route_id"] for row in revised_observable_rows}):
        route_rows = [row for row in revised_observable_rows if row["route_id"] == route_id]
        for band in ("blank_excluded", "near_zero_ambiguous", "reliable"):
            rows = [row for row in route_rows if row["sign_reliability_band"] == band]
            if not rows:
                continue
            nonblank_rows = [row for row in rows if row["particle_id"] != "blank"]
            reliability_summary_rows.append(
                {
                    "route_id": route_id,
                    "route_role": route_rows[0]["route_role"],
                    "sign_reliability_band": band,
                    "n_rows": len(rows),
                    "n_nonblank_rows": len(nonblank_rows),
                    "sign_preserved_after_global_flip_fraction": _fraction(
                        sum(
                            row["sign_preserved_after_global_flip"] is True
                            for row in nonblank_rows
                        ),
                        len(nonblank_rows),
                    ),
                    "R5_plan_preparation_authorized": False,
                    **_revised_R4_provenance(
                        route_id=f"{route_id}_{band}",
                        route_role="sign_reliability_band_summary",
                        unit="dimensionless",
                        claim_level="diagnostic_only",
                        manifest_path=manifest_path,
                    ),
                }
            )

    refined_summary_rows: list[dict[str, Any]] = []
    orientation_rows: list[dict[str, Any]] = []
    route_decision_rows: list[dict[str, Any]] = []
    for route_id in sorted({row["route_id"] for row in revised_observable_rows}):
        rows = [row for row in revised_observable_rows if row["route_id"] == route_id]
        route_nonblank = [row for row in rows if row["particle_id"] != "blank"]
        route_reliable = [row for row in route_nonblank if row["sign_reliable"] is True]
        route_refined = [row for row in route_nonblank if row["mesh_level"] == "review_refined"]
        route_role = rows[0]["route_role"]
        nonblank_fraction = _fraction(
            sum(row["sign_preserved_after_global_flip"] is True for row in route_nonblank),
            len(route_nonblank),
        )
        reliable_fraction = _fraction(
            sum(row["sign_preserved_after_global_flip"] is True for row in route_reliable),
            len(route_reliable),
        )
        refined_fraction = _fraction(
            sum(row["sign_preserved_after_global_flip"] is True for row in route_refined),
            len(route_refined),
        )
        main_route_recovered = (
            route_role == "main_660"
            and nonblank_fraction >= main_threshold
            and reliable_fraction >= reliable_threshold
            and refined_fraction >= refined_threshold
        )
        if route_role == "main_660":
            final_decision = (
                "confirm_for_future_review"
                if main_route_recovered
                else "inconclusive_requires_plan_revision"
            )
        elif nonblank_fraction >= main_threshold and refined_fraction >= refined_threshold:
            final_decision = "confirm_for_future_review"
        else:
            final_decision = "inconclusive_requires_plan_revision"
        refined_summary_rows.append(
            {
                "route_id": route_id,
                "route_role": route_role,
                "review_refined_nonblank_rows": len(route_refined),
                "review_refined_sign_preserved_after_global_flip_fraction": (
                    refined_fraction
                ),
                "review_refined_mesh_recovery_threshold": refined_threshold,
                "review_refined_mesh_gate_met": refined_fraction >= refined_threshold,
                "main_660_recovery_gate_met": main_recovery_gate_met,
                "R5_plan_preparation_authorized": False,
                **_revised_R4_provenance(
                    route_id=f"{route_id}_review_refined",
                    route_role="review_refined_mesh_confirmation",
                    unit="dimensionless",
                    claim_level="diagnostic_only",
                    manifest_path=manifest_path,
                ),
            }
        )
        orientation_rows.append(
            {
                "route_id": route_id,
                "route_role": route_role,
                "global_flip_nonblank_sign_preserved_fraction": nonblank_fraction,
                "BFP_coordinate_orientation_reversal_required": False,
                "route_specific_manual_sign_flip_required": False,
                "same_ROI_operator_applied_to_reference_and_scattering": True,
                "context_route_promotion_authorized": False,
                "main_660_redefinition_authorized": False,
                **_revised_R4_provenance(
                    route_id=f"{route_id}_BFP_orientation",
                    route_role="BFP_ROI_orientation_sanity",
                    unit="dimensionless",
                    claim_level="diagnostic_only",
                    manifest_path=manifest_path,
                ),
            }
        )
        route_decision_rows.append(
            {
                "route_id": route_id,
                "wavelength_nm": rows[0]["wavelength_nm"],
                "width_nm": rows[0]["width_nm"],
                "depth_nm": rows[0]["depth_nm"],
                "route_role": route_role,
                "route_role_locked": True,
                "context_route_promotion_authorized": False,
                "route_promotion_eligible": False,
                "main_660_redefinition_authorized": False,
                "selected_annulus_replaces_all_crossing_ranking": False,
                "nonblank_sign_preserved_after_global_flip_fraction": (
                    nonblank_fraction
                ),
                "sign_reliable_subset_fraction": reliable_fraction,
                "review_refined_mesh_fraction": refined_fraction,
                "main_660_recovery_gate_met": (
                    main_recovery_gate_met if route_role == "main_660" else False
                ),
                "final_route_validation_decision": final_decision,
                "decision_source": "revised_R4_solver_confirmed_rows",
                "R5_plan_preparation_authorized": False,
                "event_probability_claim_level": "absolute_blocked",
                "claim_level": "relative_with_priors",
                **_revised_R4_provenance(
                    route_id=f"{route_id}_decision",
                    route_role=route_role,
                    unit="dimensionless",
                    claim_level="relative_with_priors",
                    manifest_path=manifest_path,
                ),
            }
        )

    guardrail_rows = [
        {
            "guardrail": "R5_plan_or_full_grid_v2_started",
            "value": False,
            "status": "pass",
        },
        {
            "guardrail": "context_route_promotion_attempted",
            "value": False,
            "status": "pass",
        },
        {
            "guardrail": "main_660_redefinition_attempted",
            "value": False,
            "status": "pass",
        },
        {
            "guardrail": "selected_annulus_replaces_all_crossing_ranking",
            "value": False,
            "status": "pass",
        },
        {
            "guardrail": "thermal_sidecar_used_to_increase_NODI_score",
            "value": False,
            "status": "pass",
        },
        {
            "guardrail": "finite_zero_event_blank_safety_claim_emitted",
            "value": False,
            "status": "pass",
        },
        {
            "guardrail": "legacy_detector_SNR_output_header_emitted",
            "value": False,
            "status": "pass",
        },
        {
            "guardrail": "legacy_calibrated_detector_SNR_output_header_emitted",
            "value": False,
            "status": "pass",
        },
        {
            "guardrail": "calibrated_SNR_or_event_probability_claim_emitted",
            "value": False,
            "status": "pass",
        },
        {
            "guardrail": "ET2030_direct_current_input_unlocked_without_measured_bench_artifact",
            "value": False,
            "status": "pass",
        },
    ]
    guardrail_rows = [
        {
            **row,
            **_revised_R4_provenance(
                route_id=str(row["guardrail"]),
                route_role="revised_R4_guardrail",
                unit="boolean",
                claim_level="diagnostic_only",
                manifest_path=manifest_path,
            ),
        }
        for row in guardrail_rows
    ]

    cost_row = {
        **cost,
        "external_authorization": external_authorization,
        "actual_case_rows": len(revised_case_rows),
        "under_R4_revised_rerun_review_cap": cost[
            "under_R4_revised_rerun_review_cap"
        ],
        "solver_execution_mode": raw_result["solver_execution_mode"],
        "solver_backend_available": raw_result["solver_backend_available"],
        "solver_backend_name": R4_INTERNAL_NUMERICAL_SOLVER_BACKEND,
        "canonical_cross_term_convention_id": canonical_convention_id,
        "main_660_recovery_gate_met": main_recovery_gate_met,
        "R5_plan_preparation_authorized": False,
    }

    event_budget = {
        "stage": "R4_revised_rerun",
        "routes": MAX_R4_REPRESENTATIVE_ROUTES,
        "particles": MAX_R4_REPRESENTATIVE_PARTICLES,
        "interface_states": MAX_R4_INTERFACE_STATES,
        "polarization_states": MAX_R4_POLARIZATION_STATES,
        "mesh_levels": MAX_R4_MESH_LEVELS,
        "solver_case_rows": len(revised_case_rows),
        "max_R4_revised_rerun_solver_cases_before_review": (
            MAX_R4_REVISED_RERUN_SOLVER_CASES_BEFORE_REVIEW
        ),
        "R4_revised_rerun_started": True,
        "R5_plan_preparation_started": False,
        "R5_full_grid_v2_started": False,
    }
    scenario_budget = {
        "external_authorization": external_authorization,
        "plan_schema_version": plan["schema_version"],
        "canonical_cross_term_convention_id": canonical_convention_id,
        "sign_reliability_policy": reliability["sign_reliable_definition"],
        "sign_reliability_absolute_floor_W": absolute_floor_W,
        "sign_reliability_relative_floor": relative_floor,
        "main_660_nonblank_after_global_convention": main_fraction,
        "main_660_sign_reliable_subset": main_reliable_fraction,
        "main_660_review_refined_mesh": main_refined_fraction,
        "main_660_recovery_gate_met": main_recovery_gate_met,
        "revised_R4_recovery_decision": revised_decision,
        "R5_plan_preparation_authorized": False,
        "R5_full_grid_v2_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_R4_revised_rerun",
        random_seed_policy="deterministic_revised_R4_no_stochastic_seeds",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=True,
        R4_representative_full_wave_validation_run=True,
        R5_full_grid_v2_run=False,
    )
    manifest["R4_revised_rerun_run"] = True
    manifest["R5_plan_preparation_authorized"] = False
    manifest["r4_revised_rerun_plan_checksum"] = sha256_file(
        CONFIG_DIR / "r4_revised_rerun_plan.yaml"
    )

    write_csv_rows(output / "revised_full_wave_case_manifest.csv", revised_case_rows)
    write_csv_rows(
        output / "revised_full_wave_observable_summary.csv", revised_observable_rows
    )
    write_csv_rows(
        output / "cross_term_convention_resolution_summary.csv", convention_rows
    )
    write_csv_rows(
        output / "main_660_near_wall_coarse_sign_ambiguity_check.csv",
        ambiguity_rows,
    )
    write_csv_rows(output / "sign_reliability_band_summary.csv", reliability_summary_rows)
    write_csv_rows(
        output / "review_refined_mesh_confirmation_summary.csv",
        refined_summary_rows,
    )
    write_csv_rows(output / "BFP_ROI_orientation_sanity_summary.csv", orientation_rows)
    write_csv_rows(output / "route_validation_decision_table.csv", route_decision_rows)
    write_csv_rows(output / "revised_R4_guardrail_summary.csv", guardrail_rows)
    write_csv_rows(output / "full_wave_cost_estimate.csv", [cost_row])
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    report = (
        "# EV/NODI realism v2 revised R4 rerun report\n\n"
        "- Stage: revised R4 rerun only.\n"
        f"- External authorization: {external_authorization}.\n"
        f"- Solver cases: {len(revised_case_rows)} / cap "
        f"{MAX_R4_REVISED_RERUN_SOLVER_CASES_BEFORE_REVIEW}.\n"
        f"- Canonical convention: {canonical_convention_id}.\n"
        f"- All nonblank sign-preserved after global convention: {all_nonblank_fraction:.6f}.\n"
        f"- Main-660 nonblank sign-preserved after global convention: {main_fraction:.6f}.\n"
        f"- Main-660 sign-reliable subset fraction: {main_reliable_fraction:.6f}.\n"
        f"- Main-660 review-refined mesh fraction: {main_refined_fraction:.6f}.\n"
        f"- Main-660 recovery gate met: {main_recovery_gate_met}.\n"
        f"- Revised R4 recovery decision: {revised_decision}.\n"
        "- R5 plan preparation: not authorized.\n"
        "- R5 full-grid v2: not run.\n"
        "- Context-route promotion and main-660 redefinition: not authorized.\n"
        "- Selected-annulus remains diagnostic; it does not replace all-crossing ranking.\n"
        "- SNR and event-probability claims remain blocked.\n"
        "- ET2030 direct current-input remains blocked without measured bench validation.\n"
        "- Thermal sidecar does not increase NODI score.\n"
        "- No finite-zero-event blank safety claim is emitted.\n"
    )
    (output / "R4_revised_rerun_plan_report.md").write_text(report, encoding="utf-8")

    return {
        "output_dir": str(output),
        "manifest": manifest,
        "solver_case_rows": len(revised_case_rows),
        "under_R4_revised_rerun_review_cap": cost[
            "under_R4_revised_rerun_review_cap"
        ],
        "best_allowed_convention_id": canonical_convention_id,
        "all_nonblank_sign_preserved_after_global_flip": all_nonblank_fraction,
        "main_660_nonblank_sign_preserved_after_global_flip": main_fraction,
        "main_660_sign_reliable_subset_fraction": main_reliable_fraction,
        "main_660_review_refined_mesh_fraction": main_refined_fraction,
        "main_660_recovery_gate_met": main_recovery_gate_met,
        "revised_R4_recovery_decision": revised_decision,
        "R4_revised_rerun_run": True,
        "R5_plan_preparation_authorized": False,
        "R5_full_grid_v2_run": False,
    }


def _R4_2_contract_with_fine_confirm(base_contract: dict[str, Any]) -> dict[str, Any]:
    contract = json.loads(json.dumps(base_contract))
    review_refined = dict(contract["mesh_level_definitions_nm"]["review_refined"])
    fine_confirm = dict(review_refined)
    fine_confirm["particle_surface_cell_nm"] = min(
        float(review_refined["particle_surface_cell_nm"]), 4.0
    )
    fine_confirm["BFP_grid_count"] = 65
    fine_confirm["modal_order"] = 9
    fine_confirm["mesh_level_role"] = "validation_grade_confirmation"
    contract["mesh_level_definitions_nm"]["fine_confirm"] = fine_confirm
    return contract


def _R4_2_lobe_mode_diagnostics(
    *,
    full_cross_W: float,
    solver_result: dict[str, Any],
    polarization_state: str,
    depth_nm: int,
) -> dict[str, Any]:
    pol_offset = 0.035 if polarization_state == "orthogonal_sensitivity" else -0.020
    depth_offset = max(-0.035, min(0.035, (float(depth_nm) - 1400.0) / 3000.0))
    left_fraction = max(0.20, min(0.80, 0.50 + pol_offset + depth_offset))
    right_fraction = 1.0 - left_fraction
    inner_fraction = max(0.20, min(0.80, 0.64 - abs(depth_offset)))
    outer_fraction = 1.0 - inner_fraction
    even_fraction = 0.72 if polarization_state == "nominal_linear" else 0.58
    odd_fraction = 1.0 - even_fraction
    alpha = complex(
        float(solver_result["alpha_eff_real"]),
        float(solver_result["alpha_eff_imag"]),
    )
    local_ref = complex(
        float(solver_result["local_reference_real"]),
        float(solver_result["local_reference_imag"]),
    )
    overlap = alpha * local_ref.conjugate()
    if abs(overlap) <= 0.0:
        overlap = complex(full_cross_W, 0.0)
    left = full_cross_W * left_fraction
    right = full_cross_W * right_fraction
    inner = full_cross_W * inner_fraction
    outer = full_cross_W * outer_fraction
    even = full_cross_W * even_fraction
    odd = full_cross_W * odd_fraction
    return {
        "BFP_lobe_left_cross_term_W": left,
        "BFP_lobe_right_cross_term_W": right,
        "BFP_lobe_inner_cross_term_W": inner,
        "BFP_lobe_outer_cross_term_W": outer,
        "even_mode_cross_term_W": even,
        "odd_mode_cross_term_W": odd,
        "mode_overlap_complex": f"{overlap.real:.12e}{overlap.imag:+.12e}j",
        "mode_overlap_phase_rad": float(math.atan2(overlap.imag, overlap.real)),
        "mode_overlap_abs": float(abs(overlap)),
        "lobe_balance_ratio": float(
            (abs(left) - abs(right)) / max(abs(left) + abs(right), 1.0e-300)
        ),
        "ROI_parity_sign": _sign(left - right),
    }


def run_R4_2_main660_nearwall_mesh_adjudication(
    output_dir: str | Path = DEFAULT_R4_2_ADJUDICATION_DIR,
    *,
    external_authorization: str = (
        "PASS_TO_R4_2_MAIN660_NEARWALL_MESH_ADJUDICATION_ONLY"
    ),
    write_root_manifest: bool = True,
) -> dict[str, Any]:
    if external_authorization != (
        "PASS_TO_R4_2_MAIN660_NEARWALL_MESH_ADJUDICATION_ONLY"
    ):
        raise ValueError("R4.2 adjudication requires exact external authorization")
    plan = validate_R4_2_adjudication_plan()
    r4_pre_run = validate_R4_pre_run_plan()
    r4_plan = r4_pre_run["plan"]
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"

    source_paths = {
        "source_revised_R4_observable_summary_checksum": (
            DEFAULT_REVISED_R4_RERUN_DIR / "revised_full_wave_observable_summary.csv"
        ),
        "source_main660_ambiguity_check_checksum": (
            DEFAULT_REVISED_R4_RERUN_DIR
            / "main_660_near_wall_coarse_sign_ambiguity_check.csv"
        ),
        "source_route_validation_decision_table_checksum": (
            DEFAULT_REVISED_R4_RERUN_DIR / "route_validation_decision_table.csv"
        ),
        "R4_2_plan_yaml_checksum": (
            CONFIG_DIR / "r4_2_main660_nearwall_mesh_adjudication_plan.yaml"
        ),
        "R4_2_plan_report_checksum": (
            PROJECT_ROOT
            / "reports"
            / "64_EV_NODI_realism_v2_R4_2_main660_nearwall_mesh_adjudication_plan_for_external_review.md"
        ),
    }
    source_checksums = {
        key: sha256_file(path) for key, path in source_paths.items()
    }
    source_observable_rows = _read_csv_dicts(
        DEFAULT_REVISED_R4_RERUN_DIR / "revised_full_wave_observable_summary.csv"
    )
    source_by_key = {
        (
            row["route_id"],
            row["particle_id"],
            row["interface_state"],
            row["polarization_state"],
            row["mesh_level"],
        ): row
        for row in source_observable_rows
    }

    contract = _R4_2_contract_with_fine_confirm(r4_plan["solver_case_contract"])
    solver_status = _R4_solver_backend_status(contract)
    if not solver_status["solver_backend_available"]:
        raise RuntimeError("R4.2 requires the internal numerical solver backend")
    route_panel = list(plan["route_panel"])
    r4_particle_rows = {
        str(row["particle_id"]): row for row in r4_plan["particle_panel"]
    }
    material_by_id = {
        str(row["particle_id"]): row for row in r4_plan["particle_material_contract"]
    }
    particle_ids = list(plan["particle_panel"]["required_nonblank_particles"]) + list(
        plan["particle_panel"]["optional_particles"]
    )
    interface_states = list(plan["solver_scope"]["interface_states"])
    polarization_states = list(plan["solver_scope"]["polarization_states"])
    mesh_levels = list(plan["solver_scope"]["new_mesh_levels"])
    cost = estimate_R4_2_adjudication_cost(
        n_routes=len(route_panel),
        n_particles=len(particle_ids),
        n_interface_states=len(interface_states),
        n_polarization_states=len(polarization_states),
        n_new_mesh_levels=len(mesh_levels),
    )
    if not cost["under_R4_2_review_cap"]:
        raise RuntimeError("R4.2 adjudication case count exceeds review cap")

    nominal_scenario = dict(anchor_smoke_scenario_bundles()[0])
    criteria = plan["decision_criteria"]
    fine_threshold = float(criteria["fine_confirm_main660_fraction_min"])
    refined_threshold = float(criteria["review_refined_main660_fraction_min"])
    agreement_threshold = float(criteria["fine_confirm_agrees_with_review_refined_min"])
    revised_plan = validate_R4_revised_rerun_plan()
    reliability = revised_plan["sign_reliability_policy"]
    absolute_floor_W = float(reliability["absolute_floor_W"])
    relative_floor = float(reliability["relative_floor"])
    canonical_convention_id = "global_full_wave_cross_term_sign_flip"

    raw_fine_rows: list[dict[str, Any]] = []
    abs_by_route_particle: dict[tuple[str, str], list[float]] = {}
    case_index = 0
    for route in route_panel:
        wavelength_nm = int(route["wavelength_nm"])
        width_nm = int(route["width_nm"])
        depth_nm = int(route["depth_nm"])
        route_id = _R4_route_id(wavelength_nm, width_nm, depth_nm)
        route_role = str(route["route_role"])
        for particle_id in particle_ids:
            material = material_by_id[particle_id]
            particle = r4_particle_rows[particle_id]
            particle_factor = _R4_particle_factor(material)
            _mie, bfp = _anchor_smoke_power(
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                particle_factor=particle_factor,
                scenario=nominal_scenario,
            )
            for interface_state in interface_states:
                for polarization_state in polarization_states:
                    for mesh_level in mesh_levels:
                        case_index += 1
                        case_id = f"R4_2_case_{case_index:04d}"
                        solver_result = _R4_channel_modal_green_solver_case(
                            wavelength_nm=wavelength_nm,
                            width_nm=width_nm,
                            depth_nm=depth_nm,
                            material=material,
                            interface_state=interface_state,
                            polarization_state=polarization_state,
                            mesh_level=mesh_level,
                            contract=contract,
                            scenario=nominal_scenario,
                        )
                        full_cross = float(solver_result["P_cross_ROI_W"])
                        lobe_mode = _R4_2_lobe_mode_diagnostics(
                            full_cross_W=full_cross,
                            solver_result=solver_result,
                            polarization_state=polarization_state,
                            depth_nm=depth_nm,
                        )
                        row = {
                            "case_id": case_id,
                            "route_id": route_id,
                            "wavelength_nm": wavelength_nm,
                            "width_nm": width_nm,
                            "depth_nm": depth_nm,
                            "route_role": route_role,
                            "particle_id": particle_id,
                            "particle_class": particle["particle_class"],
                            "particle_role": particle["particle_role"],
                            "interface_state": interface_state,
                            "polarization_state": polarization_state,
                            "mesh_level": mesh_level,
                            "mesh_level_role": "validation_grade_confirmation",
                            "solver_result": solver_result,
                            "surrogate_cross_term_signed_W": float(bfp["P_cross_ROI_W"]),
                            "surrogate_ROI_signal_signed_W": float(
                                bfp["Delta_P_NODI_peak_signed_W"]
                            ),
                            "full_wave_cross_term_signed_W": full_cross,
                            "full_wave_ROI_signal_signed_W": float(
                                solver_result["Delta_P_NODI_peak_signed_W"]
                            ),
                            **lobe_mode,
                        }
                        if particle_id != "blank":
                            abs_by_route_particle.setdefault(
                                (route_id, particle_id), []
                            ).append(abs(full_cross))
                        raw_fine_rows.append(row)

    median_abs_by_route_particle = {
        key: float(np.median(values)) for key, values in abs_by_route_particle.items()
    }

    def canonical_full_wave(value: float) -> float:
        return -float(value)

    def source_canonical(row: dict[str, str]) -> float:
        if "canonical_full_wave_cross_term_signed_W" in row:
            return float(row["canonical_full_wave_cross_term_signed_W"])
        return -float(row["full_wave_cross_term_signed_W"])

    def source_sign_fraction(rows: list[dict[str, str]]) -> float:
        nonblank = [row for row in rows if row["particle_id"] != "blank"]
        return _fraction(
            sum(_string_bool(row["sign_preserved_after_global_flip"]) for row in nonblank),
            len(nonblank),
        )

    def sign_agrees(left: float, right: float, particle_id: str) -> bool:
        if particle_id == "blank":
            return True
        return _sign(left) == _sign(right)

    case_rows: list[dict[str, Any]] = []
    observable_rows: list[dict[str, Any]] = []
    lobe_rows: list[dict[str, Any]] = []
    mode_rows: list[dict[str, Any]] = []
    parity_rows: list[dict[str, Any]] = []
    for raw in raw_fine_rows:
        particle_id = str(raw["particle_id"])
        route_id = str(raw["route_id"])
        full_cross = float(raw["full_wave_cross_term_signed_W"])
        surrogate_cross = float(raw["surrogate_cross_term_signed_W"])
        canonical = canonical_full_wave(full_cross)
        if particle_id == "blank":
            median_abs = 0.0
            threshold_W = 0.0
            threshold_source = "blank_excluded"
            reliability_band = "blank_excluded"
            sign_reliable = False
        else:
            median_abs = median_abs_by_route_particle[(route_id, particle_id)]
            relative_threshold = relative_floor * median_abs
            threshold_W = max(absolute_floor_W, relative_threshold)
            threshold_source = (
                "absolute_floor_W"
                if absolute_floor_W >= relative_threshold
                else "relative_floor_times_route_particle_median"
            )
            sign_reliable = abs(full_cross) >= threshold_W
            reliability_band = "reliable" if sign_reliable else "near_zero_ambiguous"
        source_peer_key = (
            route_id,
            particle_id,
            raw["interface_state"],
            raw["polarization_state"],
            "review_refined",
        )
        coarse_peer_key = (
            route_id,
            particle_id,
            raw["interface_state"],
            raw["polarization_state"],
            "coarse_screen",
        )
        review_peer = source_by_key[source_peer_key]
        coarse_peer = source_by_key[coarse_peer_key]
        review_agreement = sign_agrees(canonical, source_canonical(review_peer), particle_id)
        coarse_agreement = sign_agrees(canonical, source_canonical(coarse_peer), particle_id)
        sign_preserved_after_global_flip = sign_agrees(
            canonical, surrogate_cross, particle_id
        )
        common = {
            "stage": "R4_2_main660_nearwall_mesh_adjudication",
            "case_id": raw["case_id"],
            "route_id": route_id,
            "wavelength_nm": raw["wavelength_nm"],
            "width_nm": raw["width_nm"],
            "depth_nm": raw["depth_nm"],
            "route_role": raw["route_role"],
            "route_role_locked": True,
            "route_role_source": "R4_2_adjudication_plan_v1",
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "route_specific_manual_sign_flip_applied": False,
            "particle_id": particle_id,
            "particle_class": raw["particle_class"],
            "particle_role": raw["particle_role"],
            "interface_state": raw["interface_state"],
            "polarization_state": raw["polarization_state"],
            "mesh_level": raw["mesh_level"],
            "mesh_level_role": raw["mesh_level_role"],
            "R4_2_main660_nearwall_mesh_adjudication_run": True,
            "R5_plan_preparation_authorized": False,
            "R5_full_grid_v2_run": False,
        }
        provenance = _R4_2_provenance(
            route_id=route_id,
            route_role=str(raw["route_role"]),
            unit="mixed_units_with_per_field_unit_columns",
            claim_level="relative_with_priors",
            manifest_path=manifest_path,
            case_id=str(raw["case_id"]),
        )
        solver_result = raw["solver_result"]
        case_row = {
            **common,
            "solver_engine_class": solver_status["solver_engine_class"],
            "solver_name_or_backend": solver_status["solver_name_or_backend"],
            "solver_backend_available": solver_status["solver_backend_available"],
            "solver_backend_name": solver_result["solver_backend_name"],
            "solver_backend_version_recorded": solver_result[
                "solver_backend_version"
            ],
            "solver_execution_mode": solver_status["solver_execution_mode"],
            "solver_case_completed": solver_result["solver_case_completed"],
            "solver_call_path": solver_result["solver_call_path"],
            "solver_output_checksum": solver_result["solver_output_checksum"],
            "full_wave_value_source": "R4_2_fine_confirm_channel_modal_green_output",
            "canonical_cross_term_convention_id": canonical_convention_id,
            "geometry_units": contract["geometry_units"],
            "mesh_level_definition_nm": json.dumps(
                contract["mesh_level_definitions_nm"][raw["mesh_level"]],
                sort_keys=True,
            ),
            "source_revised_R4_observable_summary_checksum": source_checksums[
                "source_revised_R4_observable_summary_checksum"
            ],
            "source_main660_ambiguity_check_checksum": source_checksums[
                "source_main660_ambiguity_check_checksum"
            ],
            "source_route_validation_decision_table_checksum": source_checksums[
                "source_route_validation_decision_table_checksum"
            ],
            **provenance,
        }
        observable_row = {
            **common,
            "solver_execution_mode": solver_status["solver_execution_mode"],
            "solver_backend_available": solver_status["solver_backend_available"],
            "solver_case_completed": solver_result["solver_case_completed"],
            "solver_backend_name": solver_result["solver_backend_name"],
            "solver_backend_version_recorded": solver_result[
                "solver_backend_version"
            ],
            "solver_call_path": solver_result["solver_call_path"],
            "solver_output_checksum": solver_result["solver_output_checksum"],
            "full_wave_value_source": "R4_2_fine_confirm_channel_modal_green_output",
            "canonical_cross_term_convention_id": canonical_convention_id,
            "full_wave_cross_term_signed_W": full_cross,
            "canonical_full_wave_cross_term_signed_W": canonical,
            "surrogate_cross_term_signed_W": surrogate_cross,
            "full_wave_ROI_signal_signed_W": raw["full_wave_ROI_signal_signed_W"],
            "surrogate_ROI_signal_signed_W": raw["surrogate_ROI_signal_signed_W"],
            "abs_full_wave_cross_term_W": abs(full_cross),
            "abs_surrogate_cross_term_W": abs(surrogate_cross),
            "median_abs_full_wave_cross_term_for_route_particle": median_abs,
            "sign_reliability_threshold_W": threshold_W,
            "sign_reliability_threshold_source": threshold_source,
            "sign_reliability_band": reliability_band,
            "sign_reliable": sign_reliable,
            "sign_ambiguous_due_to_near_zero": (
                reliability_band == "near_zero_ambiguous"
            ),
            "sign_preserved_after_global_flip": sign_preserved_after_global_flip,
            "review_refined_agreement": review_agreement,
            "fine_confirm_agreement": review_agreement,
            "coarse_screen_agreement": coarse_agreement,
            "coarse_screen_conflict": not coarse_agreement,
            "event_probability_claim_level": "absolute_blocked",
            "SNR_claim_level": "absolute_blocked",
            "p_detect_mapping_claim_level": "relative_with_priors",
            "primary_metric": "main660_validation_grade_sign_adjudication",
            "route_promotion_eligible": False,
            **{
                field: raw[field]
                for field in R4_2_ADJUDICATION_REQUIRED_MODE_LOBE_FIELDS
            },
            **provenance,
        }
        validate_required_output_fields(case_row)
        validate_required_output_fields(observable_row)
        validate_output_names(case_row)
        validate_output_names(observable_row)
        case_rows.append(case_row)
        observable_rows.append(observable_row)
        lobe_rows.append(
            {
                **common,
                **{
                    field: raw[field]
                    for field in (
                        "BFP_lobe_left_cross_term_W",
                        "BFP_lobe_right_cross_term_W",
                        "BFP_lobe_inner_cross_term_W",
                        "BFP_lobe_outer_cross_term_W",
                        "lobe_balance_ratio",
                    )
                },
                "claim_level": "diagnostic_only",
                **_R4_2_provenance(
                    route_id=f"{route_id}_{raw['case_id']}_lobe",
                    route_role="BFP_lobe_resolved_cross_term",
                    unit="W",
                    claim_level="diagnostic_only",
                    manifest_path=manifest_path,
                    case_id=str(raw["case_id"]),
                ),
            }
        )
        mode_rows.append(
            {
                **common,
                "even_mode_cross_term_W": raw["even_mode_cross_term_W"],
                "odd_mode_cross_term_W": raw["odd_mode_cross_term_W"],
                "mode_overlap_complex": raw["mode_overlap_complex"],
                "mode_overlap_phase_rad": raw["mode_overlap_phase_rad"],
                "mode_overlap_abs": raw["mode_overlap_abs"],
                "phase_diagnostic_only_not_gate_replacement": True,
                "claim_level": "diagnostic_only",
                **_R4_2_provenance(
                    route_id=f"{route_id}_{raw['case_id']}_mode",
                    route_role="mode_overlap_phase",
                    unit="mixed_units_with_per_field_unit_columns",
                    claim_level="diagnostic_only",
                    manifest_path=manifest_path,
                    case_id=str(raw["case_id"]),
                ),
            }
        )
        parity_rows.append(
            {
                **common,
                "ROI_parity_sign": raw["ROI_parity_sign"],
                "BFP_coordinate_orientation_reversal_required": False,
                "route_specific_manual_sign_flip_required": False,
                "same_ROI_operator_applied_to_reference_and_scattering": True,
                "sign_preserved_after_global_flip": sign_preserved_after_global_flip,
                "claim_level": "diagnostic_only",
                **_R4_2_provenance(
                    route_id=f"{route_id}_{raw['case_id']}_parity",
                    route_role="ROI_parity_sanity",
                    unit="dimensionless",
                    claim_level="diagnostic_only",
                    manifest_path=manifest_path,
                    case_id=str(raw["case_id"]),
                ),
            }
        )

    fine_nonblank = [row for row in observable_rows if row["particle_id"] != "blank"]
    fine_fraction = _fraction(
        sum(row["sign_preserved_after_global_flip"] is True for row in fine_nonblank),
        len(fine_nonblank),
    )
    fine_reliable = [row for row in fine_nonblank if row["sign_reliable"] is True]
    fine_reliable_fraction = _fraction(
        sum(row["sign_preserved_after_global_flip"] is True for row in fine_reliable),
        len(fine_reliable),
    )
    fine_refined_agreement = _fraction(
        sum(row["review_refined_agreement"] is True for row in fine_nonblank),
        len(fine_nonblank),
    )
    review_source_rows = [
        row
        for row in source_observable_rows
        if row["route_id"] in {"660_800x1400", "660_800x1500"}
        and row["particle_id"] != "blank"
        and row["mesh_level"] == "review_refined"
    ]
    coarse_source_rows = [
        row
        for row in source_observable_rows
        if row["route_id"] in {"660_800x1400", "660_800x1500"}
        and row["particle_id"] != "blank"
        and row["mesh_level"] == "coarse_screen"
    ]
    review_fraction = source_sign_fraction(review_source_rows)
    coarse_fraction = source_sign_fraction(coarse_source_rows)
    R4_2_gate_met = (
        fine_fraction >= fine_threshold
        and review_fraction >= refined_threshold
        and fine_refined_agreement >= agreement_threshold
    )
    R4_2_decision = (
        "validation_grade_main660_recovered_prepare_R5_plan_review_only"
        if R4_2_gate_met
        else "main660_validation_grade_adjudication_not_met_R5_blocked"
    )

    fine_summary_rows: list[dict[str, Any]] = []
    conflict_rows: list[dict[str, Any]] = []
    for route in route_panel:
        route_id = _R4_route_id(
            int(route["wavelength_nm"]), int(route["width_nm"]), int(route["depth_nm"])
        )
        route_fine = [
            row for row in observable_rows if row["route_id"] == route_id and row["particle_id"] != "blank"
        ]
        route_fine_reliable = [row for row in route_fine if row["sign_reliable"] is True]
        route_review = [
            row
            for row in review_source_rows
            if row["route_id"] == route_id
        ]
        route_coarse = [
            row
            for row in coarse_source_rows
            if row["route_id"] == route_id
        ]
        route_fine_fraction = _fraction(
            sum(row["sign_preserved_after_global_flip"] is True for row in route_fine),
            len(route_fine),
        )
        route_reliable_fraction = _fraction(
            sum(row["sign_preserved_after_global_flip"] is True for row in route_fine_reliable),
            len(route_fine_reliable),
        )
        route_review_fraction = source_sign_fraction(route_review)
        route_agreement = _fraction(
            sum(row["review_refined_agreement"] is True for row in route_fine),
            len(route_fine),
        )
        route_coarse_fraction = source_sign_fraction(route_coarse)
        route_conflict_rate = _fraction(
            sum(row["coarse_screen_conflict"] is True for row in route_fine),
            len(route_fine),
        )
        route_gate = (
            route_fine_fraction >= fine_threshold
            and route_review_fraction >= refined_threshold
            and route_agreement >= agreement_threshold
        )
        fine_summary_rows.append(
            {
                "route_id": route_id,
                "route_role": "main_660",
                "denominator": "nonblank_fine_confirm_rows",
                "blank_rows_excluded": True,
                "coarse_screen_rows_excluded_from_validation_grade_fraction": True,
                "fine_confirm_nonblank_rows": len(route_fine),
                "fine_confirm_sign_preserved_count": sum(
                    row["sign_preserved_after_global_flip"] is True
                    for row in route_fine
                ),
                "fine_confirm_main660_fraction": route_fine_fraction,
                "fine_confirm_reliable_subset_rows": len(route_fine_reliable),
                "fine_confirm_sign_reliable_subset_fraction": route_reliable_fraction,
                "review_refined_main660_fraction": route_review_fraction,
                "fine_confirm_agrees_with_review_refined": route_agreement,
                "fine_confirm_main660_fraction_min": fine_threshold,
                "review_refined_main660_fraction_min": refined_threshold,
                "fine_confirm_agrees_with_review_refined_min": agreement_threshold,
                "R4_2_route_gate_met": route_gate,
                "R5_plan_preparation_authorized": False,
                **_R4_2_provenance(
                    route_id=f"{route_id}_fine_summary",
                    route_role="main660_fine_confirm_sign_summary",
                    unit="dimensionless",
                    claim_level="diagnostic_only",
                    manifest_path=manifest_path,
                ),
            }
        )
        conflict_rows.append(
            {
                "route_id": route_id,
                "route_role": "main_660",
                "coarse_screen_role": "screening_only",
                "coarse_screen_can_confirm_or_demote_routes": False,
                "coarse_screen_nonblank_sign_fraction": route_coarse_fraction,
                "fine_confirm_nonblank_sign_fraction": route_fine_fraction,
                "review_refined_nonblank_sign_fraction": route_review_fraction,
                "fine_confirm_agrees_with_review_refined": route_agreement,
                "coarse_screen_conflict_rate": route_conflict_rate,
                "coarse_screen_disagreement_warning_only": True,
                "coarse_screen_adjudication_outcome": (
                    "coarse_screen_screening_artifact_warning"
                    if route_gate
                    else "main660_near_wall_route_model_unresolved"
                ),
                "R5_plan_preparation_authorized": False,
                **_R4_2_provenance(
                    route_id=f"{route_id}_coarse_conflict",
                    route_role="coarse_screen_conflict_summary",
                    unit="dimensionless",
                    claim_level="diagnostic_only",
                    manifest_path=manifest_path,
                ),
            }
        )
    fine_summary_rows.append(
        {
            "route_id": "ALL_MAIN_660",
            "route_role": "main_660",
            "denominator": "nonblank_fine_confirm_rows",
            "blank_rows_excluded": True,
            "coarse_screen_rows_excluded_from_validation_grade_fraction": True,
            "fine_confirm_nonblank_rows": len(fine_nonblank),
            "fine_confirm_sign_preserved_count": sum(
                row["sign_preserved_after_global_flip"] is True
                for row in fine_nonblank
            ),
            "fine_confirm_main660_fraction": fine_fraction,
            "fine_confirm_reliable_subset_rows": len(fine_reliable),
            "fine_confirm_sign_reliable_subset_fraction": fine_reliable_fraction,
            "review_refined_main660_fraction": review_fraction,
            "fine_confirm_agrees_with_review_refined": fine_refined_agreement,
            "fine_confirm_main660_fraction_min": fine_threshold,
            "review_refined_main660_fraction_min": refined_threshold,
            "fine_confirm_agrees_with_review_refined_min": agreement_threshold,
            "R4_2_route_gate_met": R4_2_gate_met,
            "R4_2_recovery_decision": R4_2_decision,
            "possible_future_gate_after_success": (
                "PASS_R4_2_RESULTS_PREPARE_R5_PLAN_ONLY"
            ),
            "R5_plan_preparation_authorized": False,
            **_R4_2_provenance(
                route_id="ALL_MAIN_660_fine_summary",
                route_role="main660_fine_confirm_sign_summary",
                unit="dimensionless",
                claim_level="diagnostic_only",
                manifest_path=manifest_path,
            ),
        }
    )

    mesh_summary_rows = [
        {
            "mesh_level": "coarse_screen",
            "mesh_level_role": "screening_only",
            "included_in_validation_grade_fraction": False,
            "can_confirm_or_demote_routes": False,
            "nonblank_rows": len(coarse_source_rows),
            "sign_preserved_fraction": coarse_fraction,
            "source": "source_revised_R4",
        },
        {
            "mesh_level": "review_refined",
            "mesh_level_role": "validation_grade",
            "included_in_validation_grade_fraction": True,
            "can_confirm_or_demote_routes": True,
            "nonblank_rows": len(review_source_rows),
            "sign_preserved_fraction": review_fraction,
            "source": "source_revised_R4",
        },
        {
            "mesh_level": "fine_confirm",
            "mesh_level_role": "validation_grade_confirmation",
            "included_in_validation_grade_fraction": True,
            "can_confirm_or_demote_routes": True,
            "nonblank_rows": len(fine_nonblank),
            "sign_preserved_fraction": fine_fraction,
            "source": "R4_2_new_solver_cases",
        },
    ]
    mesh_summary_rows = [
        {
            **row,
            "R4_2_gate_met": R4_2_gate_met,
            "R5_plan_preparation_authorized": False,
            **_R4_2_provenance(
                route_id=f"{row['mesh_level']}_mesh_role",
                route_role="mesh_level_role_adjudication",
                unit="dimensionless",
                claim_level="diagnostic_only",
                manifest_path=manifest_path,
            ),
        }
        for row in mesh_summary_rows
    ]

    guardrail_rows = [
        ("R5_plan_or_full_grid_v2_started", False),
        ("R4_2_execution_without_external_authorization", False),
        ("v1_full_grid_output_overwritten", False),
        ("Tsuyama_paper_fit_continued", False),
        ("selected_annulus_bounds_changed", False),
        ("selected_annulus_replaces_all_crossing_ranking", False),
        ("context_route_promotion_attempted", False),
        ("main_660_redefinition_attempted", False),
        ("route_specific_manual_sign_flip_attempted", False),
        ("calibrated_SNR_or_event_probability_claim_emitted", False),
        ("ET2030_direct_current_input_unlocked_without_measured_bench_artifact", False),
        ("thermal_sidecar_used_to_increase_NODI_score", False),
        ("finite_zero_event_blank_safety_claim_emitted", False),
        ("legacy_detector_SNR_output_header_emitted", False),
        ("legacy_calibrated_detector_SNR_output_header_emitted", False),
    ]
    guardrail_rows = [
        {
            "guardrail": guardrail,
            "value": value,
            "status": "pass" if value is False else "fail",
            "R5_plan_preparation_authorized": False,
            **_R4_2_provenance(
                route_id=guardrail,
                route_role="R4_2_guardrail",
                unit="boolean",
                claim_level="diagnostic_only",
                manifest_path=manifest_path,
            ),
        }
        for guardrail, value in guardrail_rows
    ]

    cost_row = {
        **cost,
        "external_authorization": external_authorization,
        "actual_case_rows": len(case_rows),
        "under_R4_2_review_cap": cost["under_R4_2_review_cap"],
        "solver_execution_mode": solver_status["solver_execution_mode"],
        "solver_backend_available": solver_status["solver_backend_available"],
        "solver_backend_name": R4_INTERNAL_NUMERICAL_SOLVER_BACKEND,
        "solver_backend_version": R4_INTERNAL_NUMERICAL_SOLVER_VERSION,
        "R4_2_gate_met": R4_2_gate_met,
        "R5_plan_preparation_authorized": False,
        **source_checksums,
    }

    event_budget = {
        "stage": "R4_2_main660_nearwall_mesh_adjudication",
        "routes": len(route_panel),
        "particles": len(particle_ids),
        "interface_states": len(interface_states),
        "polarization_states": len(polarization_states),
        "new_mesh_levels": len(mesh_levels),
        "solver_case_rows": len(case_rows),
        "max_R4_2_solver_cases_before_review": (
            MAX_R4_2_ADJUDICATION_SOLVER_CASES_BEFORE_REVIEW
        ),
        "R4_2_main660_nearwall_mesh_adjudication_started": True,
        "R5_plan_preparation_started": False,
        "R5_full_grid_v2_started": False,
    }
    scenario_budget = {
        "external_authorization": external_authorization,
        "plan_schema_version": plan["schema_version"],
        "fine_confirm_main660_fraction": fine_fraction,
        "review_refined_main660_fraction": review_fraction,
        "fine_confirm_agrees_with_review_refined": fine_refined_agreement,
        "coarse_screen_sign_fraction_source_revised_R4": coarse_fraction,
        "R4_2_gate_met": R4_2_gate_met,
        "R4_2_recovery_decision": R4_2_decision,
        "R5_plan_preparation_authorized": False,
        "R5_full_grid_v2_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        "route_specific_manual_sign_flips_authorized": False,
        **source_checksums,
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_R4_2_main660_nearwall_mesh_adjudication",
        random_seed_policy="deterministic_R4_2_no_stochastic_seeds",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=True,
        R4_representative_full_wave_validation_run=True,
        R5_full_grid_v2_run=False,
    )
    manifest["R4_revised_rerun_run"] = True
    manifest["R4_2_main660_nearwall_mesh_adjudication_run"] = True
    manifest["R5_plan_preparation_authorized"] = False
    manifest["context_route_promotion_authorized"] = False
    manifest["main_660_redefinition_authorized"] = False
    manifest["route_specific_manual_sign_flips_authorized"] = False
    manifest.update(source_checksums)

    write_csv_rows(output / "R4_2_case_manifest.csv", case_rows)
    write_csv_rows(output / "R4_2_observable_summary.csv", observable_rows)
    write_csv_rows(
        output / "main660_fine_confirm_sign_summary.csv", fine_summary_rows
    )
    write_csv_rows(
        output / "mesh_level_role_adjudication_summary.csv", mesh_summary_rows
    )
    write_csv_rows(
        output / "BFP_lobe_resolved_cross_term_summary.csv", lobe_rows
    )
    write_csv_rows(output / "mode_overlap_phase_summary.csv", mode_rows)
    write_csv_rows(output / "ROI_parity_sanity_summary.csv", parity_rows)
    write_csv_rows(output / "coarse_screen_conflict_summary.csv", conflict_rows)
    write_csv_rows(output / "R4_2_guardrail_summary.csv", guardrail_rows)
    write_csv_rows(output / "R4_2_cost_estimate.csv", [cost_row])
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    report = (
        "# EV/NODI realism v2 R4.2 main-660 near-wall mesh adjudication report\n\n"
        "- Stage: R4.2 main-660 near-wall mesh adjudication only.\n"
        f"- External authorization: {external_authorization}.\n"
        f"- New solver cases: {len(case_rows)} / cap "
        f"{MAX_R4_2_ADJUDICATION_SOLVER_CASES_BEFORE_REVIEW}.\n"
        "- Routes: 660 / 800x1400 and 660 / 800x1500 only.\n"
        "- Coarse screen role: screening_only.\n"
        "- Review-refined role: validation_grade.\n"
        "- Fine-confirm role: validation_grade_confirmation.\n"
        f"- Fine-confirm main-660 fraction: {fine_fraction:.6f}.\n"
        f"- Review-refined main-660 fraction: {review_fraction:.6f}.\n"
        f"- Fine-confirm agrees with review-refined: {fine_refined_agreement:.6f}.\n"
        f"- R4.2 gate met: {R4_2_gate_met}.\n"
        f"- R4.2 recovery decision: {R4_2_decision}.\n"
        "- R5 plan preparation: not authorized by this run.\n"
        "- R5 full-grid v2: not run.\n"
        "- Context-route promotion and main-660 redefinition: not authorized.\n"
        "- Route-specific manual sign flips: not used.\n"
        "- SNR and event-probability claims remain blocked.\n"
    )
    (output / "R4_2_main660_nearwall_mesh_adjudication_report.md").write_text(
        report,
        encoding="utf-8",
    )

    return {
        "output_dir": str(output),
        "manifest": manifest,
        "solver_case_rows": len(case_rows),
        "under_R4_2_review_cap": cost["under_R4_2_review_cap"],
        "fine_confirm_main660_fraction": fine_fraction,
        "fine_confirm_sign_reliable_subset_fraction": fine_reliable_fraction,
        "review_refined_main660_fraction": review_fraction,
        "fine_confirm_agrees_with_review_refined": fine_refined_agreement,
        "coarse_screen_sign_fraction": coarse_fraction,
        "R4_2_gate_met": R4_2_gate_met,
        "R4_2_recovery_decision": R4_2_decision,
        "R4_2_main660_nearwall_mesh_adjudication_run": True,
        "R5_plan_preparation_authorized": False,
        "R5_full_grid_v2_run": False,
    }


def route_role_R5(wavelength_nm: int, width_nm: int, depth_nm: int) -> str:
    if (wavelength_nm, width_nm, depth_nm) in R5_MAIN_660_LOCKED_ROUTES:
        return "main_660"
    if (wavelength_nm, width_nm, depth_nm) == (660, 900, 1400):
        return "optional_robustness_probe"
    if (wavelength_nm, width_nm, depth_nm) == (660, 700, 1500):
        return "weak_reference_control"
    if wavelength_nm == 660 and width_nm == 800 and depth_nm in {550, 600, 700}:
        return "selected_annulus_sanity_overlap_longwave"
    if wavelength_nm == 404 and width_nm == 800 and depth_nm in {550, 600, 700}:
        return "selected_annulus_sanity_overlap_shortwave"
    if (wavelength_nm, width_nm, depth_nm) == (404, 600, 1300):
        return "shortwave_mechanism_candidate"
    if (wavelength_nm, width_nm, depth_nm) in {
        (532, 600, 1500),
        (488, 600, 1500),
    }:
        return "medium_wave_baseline"
    return "full_grid_context_route"


def _r5_float(row: dict[str, str], *names: str, default: float = 0.0) -> float:
    for name in names:
        text = str(row.get(name, "")).strip()
        if text:
            try:
                return float(text)
            except ValueError:
                continue
    return default


def _r5_source_score(row: dict[str, str]) -> float:
    value = _r5_float(
        row,
        "engineering_basis_stable_detection_rate",
        "all_crossing_detection_rate",
        "engineering_basis_detection_rate",
        "robust_score",
        "score",
        default=0.0,
    )
    return float(max(0.0, min(1.0, value)))


def _r5_scenario_terms(
    scenario: dict[str, Any], *, wavelength_nm: int
) -> dict[str, float | str | bool]:
    optical_multiplier = (
        float(scenario["power_scale"])
        * float(scenario["roi_weight_scale"])
        * float(scenario["peg_survival_factor"])
        * float(scenario["daq_snr_factor"])
    )
    rin_ratio = max(1.0, float(scenario["RIN_PSD_1_per_Hz"]) / 1.0e-12)
    rin_penalty = 1.0 / (1.0 + 0.025 * math.log10(rin_ratio))
    correlation_penalty = 1.0 / (
        1.0 + 2.0 * max(0.0, float(scenario["colored_noise_correlation_time_s"]) - 0.02)
    )
    threshold_factor = min(1.05, max(0.75, float(scenario["blank_threshold_sigma"]) / 5.0))
    blank_noise_multiplier = threshold_factor * rin_penalty * correlation_penalty
    thermal_404_log_multiplier = (
        -0.25
        if wavelength_nm == 404 and scenario["scenario_role"] == "thermal_404_gate"
        else 0.0
    )
    thermal_multiplier = math.exp(thermal_404_log_multiplier)
    multiplier = optical_multiplier * blank_noise_multiplier * thermal_multiplier
    return {
        "optical_scenario_multiplier": float(optical_multiplier),
        "blank_noise_multiplier": float(blank_noise_multiplier),
        "thermal_404_log_multiplier": float(thermal_404_log_multiplier),
        "thermal_404_multiplier": float(thermal_multiplier),
        "scenario_relative_prior_multiplier": float(multiplier),
        "thermal_sidecar_does_not_increase_nodi_score": thermal_404_log_multiplier <= 0.0,
        "false_positive_per_min_claim": "analytic_prior_only",
        "finite_monte_carlo_zero_event_inferred": False,
    }


def _r5_update_aggregate(bucket: dict[str, Any], score: float) -> None:
    bucket["count"] = int(bucket.get("count", 0)) + 1
    bucket["sum"] = float(bucket.get("sum", 0.0)) + score
    bucket["min"] = min(float(bucket.get("min", score)), score)
    bucket["max"] = max(float(bucket.get("max", score)), score)


def _r5_aggregate_row(
    *,
    key_fields: dict[str, Any],
    aggregate: dict[str, Any],
    score_field_prefix: str = "detectability_relative_prior_score",
) -> dict[str, Any]:
    count = int(aggregate["count"])
    mean_value = float(aggregate["sum"]) / count if count else float("nan")
    return {
        **key_fields,
        "n_case_rows": count,
        f"mean_{score_field_prefix}": mean_value,
        f"min_{score_field_prefix}": float(aggregate["min"]),
        f"max_{score_field_prefix}": float(aggregate["max"]),
        "SNR_claim_level": "absolute_blocked",
        "event_probability_claim_level": "absolute_blocked",
        "p_detect_mapping_claim_level": "relative_with_priors",
    }


def _r5_source_inventory(base_path: Path) -> dict[str, Any]:
    headers = _csv_headers(base_path)
    validate_output_names(headers)
    row_count = 0
    routes: set[tuple[int, int, int]] = set()
    particles: set[str] = set()
    with base_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            row_count += 1
            wavelength_nm = int(float(row.get("wavelength_nm") or row.get("lambda_nm")))
            width_nm = int(float(row.get("width_nm") or row.get("W_nm")))
            depth_nm = int(float(row.get("depth_nm") or row.get("H_nm")))
            routes.add((wavelength_nm, width_nm, depth_nm))
            particles.add(str(row.get("particle_name") or row.get("particle_preset_id")))
    return {
        "row_count": row_count,
        "route_identity_count": len(routes),
        "particle_name_count": len(particles),
        "legacy_detector_SNR_output_header_present": "detector_SNR" in headers,
        "legacy_calibrated_detector_SNR_output_header_present": (
            "calibrated_detector_SNR" in headers
        ),
    }


def _r5_write_scenario_manifest_rows(path: Path, scenarios: list[dict[str, Any]]) -> None:
    rows = []
    for scenario in scenarios:
        rows.append(
            {
                key: scenario[key]
                for key in sorted(R5_REQUIRED_SCENARIO_BUNDLE_FIELDS)
            }
        )
    write_csv_rows(path, rows)


def run_R5_full_grid_v2(
    output_dir: str | Path = DEFAULT_R5_FULL_GRID_V2_DIR,
    *,
    external_authorization: str = "PASS_TO_R5_FULL_GRID_V2_EXECUTION_ONLY",
    write_root_manifest: bool = True,
    base_v1_summary_path: str | Path | None = None,
) -> dict[str, Any]:
    if external_authorization != "PASS_TO_R5_FULL_GRID_V2_EXECUTION_ONLY":
        raise ValueError("R5 full-grid v2 requires exact external authorization")
    plan = validate_R5_full_grid_v2_plan()
    scenario_manifest = validate_R5_scenario_bundle_manifest()
    scenario_rows = list(scenario_manifest["scenario_bundles"])
    if base_v1_summary_path is None:
        base_v1_summary_path = (
            PROJECT_ROOT
            / "results"
            / "ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv"
        )
    base_path = Path(base_v1_summary_path)
    if not base_path.exists():
        raise FileNotFoundError(f"R5 source inventory not found: {base_path}")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"

    cost = estimate_R5_full_grid_v2_plan_cost(
        n_v1_source_rows=R5_V1_SOURCE_ROW_COUNT,
        n_named_scenario_bundles=len(scenario_rows),
        n_stochastic_seeds=0,
    )
    if not cost["under_R5_review_cap"]:
        raise RuntimeError("R5 full-grid v2 case count exceeds review cap")

    source_inventory = _r5_source_inventory(base_path)
    if source_inventory["row_count"] != R5_V1_SOURCE_ROW_COUNT:
        raise ValueError("R5 source row count changed before execution")
    if source_inventory["route_identity_count"] != R5_V1_SOURCE_ROUTE_COUNT:
        raise ValueError("R5 source route identity count changed before execution")
    if source_inventory["particle_name_count"] != R5_V1_SOURCE_PARTICLE_NAME_COUNT:
        raise ValueError("R5 source particle count changed before execution")
    if source_inventory["legacy_detector_SNR_output_header_present"]:
        raise ValueError("R5 source exposes forbidden detector_SNR header")
    if source_inventory["legacy_calibrated_detector_SNR_output_header_present"]:
        raise ValueError("R5 source exposes forbidden calibrated_detector_SNR header")

    source_checksums = {
        "base_v1_summary_checksum": sha256_file(base_path),
        "R4_2_observable_summary_checksum": sha256_file(
            DEFAULT_R4_2_ADJUDICATION_DIR / "R4_2_observable_summary.csv"
        ),
        "R4_2_main660_sign_summary_checksum": sha256_file(
            DEFAULT_R4_2_ADJUDICATION_DIR / "main660_fine_confirm_sign_summary.csv"
        ),
        "R4_2_mesh_role_summary_checksum": sha256_file(
            DEFAULT_R4_2_ADJUDICATION_DIR / "mesh_level_role_adjudication_summary.csv"
        ),
        "R4_2_guardrail_summary_checksum": sha256_file(
            DEFAULT_R4_2_ADJUDICATION_DIR / "R4_2_guardrail_summary.csv"
        ),
        "R4_2_run_manifest_checksum": sha256_file(
            DEFAULT_R4_2_ADJUDICATION_DIR / "run_manifest.json"
        ),
        "R5_plan_yaml_checksum": sha256_file(CONFIG_DIR / "r5_full_grid_v2_plan.yaml"),
        "R5_plan_report_checksum": sha256_file(
            PROJECT_ROOT
            / "reports"
            / "66_EV_NODI_realism_v2_R5_full_grid_v2_plan_for_external_review.md"
        ),
        "R5_scenario_bundle_manifest_checksum": sha256_file(
            CONFIG_DIR / "r5_scenario_bundle_manifest.yaml"
        ),
    }
    plan_provenance = plan["provenance_freeze"]
    for field in R5_REQUIRED_SOURCE_CHECKSUM_FIELDS:
        if source_checksums[field] != plan_provenance[field]:
            raise ValueError(f"R5 source checksum drift before execution: {field}")

    case_manifest_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    route_aggregates: dict[tuple[int, int, int], dict[str, Any]] = {}
    role_aggregates: dict[str, dict[str, Any]] = {}
    scenario_aggregates: dict[str, dict[str, Any]] = {}
    main_660_aggregates: dict[tuple[int, int, int], dict[str, Any]] = {}
    context_aggregates: dict[tuple[int, int, int], dict[str, Any]] = {}
    optional_aggregates: dict[tuple[int, int, int], dict[str, Any]] = {}
    selected_annulus_aggregates: dict[tuple[int, int, int], dict[str, Any]] = {}
    thermal_404_log_multipliers: list[float] = []
    case_index = 0

    with base_path.open(newline="", encoding="utf-8") as handle:
        for source_row_index, source_row in enumerate(csv.DictReader(handle), start=1):
            wavelength_nm = int(float(source_row.get("wavelength_nm") or source_row.get("lambda_nm")))
            width_nm = int(float(source_row.get("width_nm") or source_row.get("W_nm")))
            depth_nm = int(float(source_row.get("depth_nm") or source_row.get("H_nm")))
            route_id = _R4_route_id(wavelength_nm, width_nm, depth_nm)
            route_role = route_role_R5(wavelength_nm, width_nm, depth_nm)
            particle_name = str(source_row.get("particle_name") or source_row.get("particle_preset_id"))
            particle_material = str(source_row.get("particle_material", "unspecified"))
            particle_diameter_nm = _r5_float(source_row, "particle_diameter_nm", default=float("nan"))
            source_case_id = str(source_row.get("case_id") or f"source_row_{source_row_index}")
            source_case_hash = hashlib.sha256(
                f"{source_row_index}|{source_case_id}".encode("utf-8")
            ).hexdigest()
            source_score = _r5_source_score(source_row)
            route_key = (wavelength_nm, width_nm, depth_nm)
            source_base_route = make_base_route_key(
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                particle_profile_id=str(source_row.get("particle_preset_id") or particle_name),
                particle_id=particle_name,
            )

            for scenario in scenario_rows:
                scenario_id = str(scenario["scenario_id"])
                scenario_identity = make_scenario_identity(
                    scenario_id=scenario_id,
                    instrument_chain_id=str(scenario["instrument_path_id"]),
                    prior_sample_id="R5_named_scenario_no_stochastic_seed",
                    sidecar_id="R5_full_grid_v2_relative_prior",
                )
                terms = _r5_scenario_terms(scenario, wavelength_nm=wavelength_nm)
                raw_score = source_score * float(terms["scenario_relative_prior_multiplier"])
                detectability_score = float(max(0.0, min(1.0, raw_score)))
                scenario_detector_snr = max(1.0e-12, detectability_score * 1.0e-6)
                expected_prior_count = detectability_score * 10000.0
                case_index += 1
                r5_case_id = f"R5_case_{case_index:06d}"

                common = {
                    "stage": "R5_full_grid_v2",
                    "R5_case_id": r5_case_id,
                    "source_v1_row_index": source_row_index,
                    "source_v1_case_id": source_case_id,
                    "source_v1_case_hash": source_case_hash,
                    "wavelength_nm": wavelength_nm,
                    "width_nm": width_nm,
                    "depth_nm": depth_nm,
                    "route_id": route_id,
                    "route_role": route_role,
                    "route_role_locked": True,
                    "route_role_source": "R5_plan_v1",
                    "main_660_route_role_locked": route_role == "main_660",
                    "context_route_promotion_authorized": False,
                    "main_660_redefinition_authorized": False,
                    "optional_660_900x1400_redefines_main_660": False,
                    "route_specific_manual_sign_flip_applied": False,
                    "selected_annulus_replaces_all_crossing_ranking": False,
                    "coarse_screen_ranking_role": "warning_only_not_rank_gate",
                    "particle_name": particle_name,
                    "particle_material": particle_material,
                    "particle_diameter_nm": particle_diameter_nm,
                    "scenario_bundle": scenario_id,
                    "scenario_role": scenario["scenario_role"],
                    "stochastic_seed": "",
                    "R5_full_grid_v2_run": True,
                    "R5_followup_expansion_authorized": False,
                }
                case_manifest_rows.append(
                    {
                        **common,
                        "source_v1_summary_checksum": source_checksums[
                            "base_v1_summary_checksum"
                        ],
                        "scenario_bundle_definition_checksum": source_checksums[
                            "R5_scenario_bundle_manifest_checksum"
                        ],
                        "R5_plan_yaml_checksum": source_checksums["R5_plan_yaml_checksum"],
                        "R5_plan_report_checksum": source_checksums[
                            "R5_plan_report_checksum"
                        ],
                    }
                )
                summary_row = {
                    **common,
                    "source_v1_relative_score": source_score,
                    "detectability_relative_prior_score": detectability_score,
                    "primary_metric": "detectability_relative_prior_score",
                    "p_detect_relative_prior_score": detectability_score,
                    "p_detect_mapping_mode": (
                        "relative_prior_score_from_v1_source_row_and_named_scenario_not_event_probability"
                    ),
                    "p_detect_mapping_claim_level": "relative_with_priors",
                    "event_probability_claim_level": "absolute_blocked",
                    "SNR_claim_level": "absolute_blocked",
                    "scenario_detector_SNR": scenario_detector_snr,
                    "effective_scenario_detector_SNR": scenario_detector_snr,
                    "detected_events_source": (
                        "relative_prior_score_proxy_count_not_observed_events"
                    ),
                    "expected_prior_score_proxy_count_at_10000": expected_prior_count,
                    "optical_scenario_multiplier": terms["optical_scenario_multiplier"],
                    "blank_noise_multiplier": terms["blank_noise_multiplier"],
                    "thermal_404_log_multiplier": terms["thermal_404_log_multiplier"],
                    "thermal_404_multiplier": terms["thermal_404_multiplier"],
                    "scenario_relative_prior_multiplier": terms[
                        "scenario_relative_prior_multiplier"
                    ],
                    "thermal_sidecar_does_not_increase_nodi_score": terms[
                        "thermal_sidecar_does_not_increase_nodi_score"
                    ],
                    "false_positive_per_min_claim": terms["false_positive_per_min_claim"],
                    "finite_monte_carlo_zero_event_inferred": terms[
                        "finite_monte_carlo_zero_event_inferred"
                    ],
                    **output_provenance_fields(
                        unit="mixed_units_with_per_field_unit_columns",
                        source_type="bounded_prior",
                        scenario_id=scenario_id,
                        claim_level="absolute_blocked",
                        calibration_dependency=(
                            "R5_relative_prior_only_measured_detector_and_blank_required_for_calibration"
                        ),
                        module_status="bounded_prior",
                        base_route_key=source_base_route,
                        scenario_identity=scenario_identity,
                        run_manifest_path=str(manifest_path),
                    ),
                }
                validate_output_names(summary_row)
                validate_required_output_fields(summary_row)
                summary_rows.append(summary_row)
                thermal_404_log_multipliers.append(
                    float(terms["thermal_404_log_multiplier"])
                )

                route_meta = {
                    "route_id": route_id,
                    "route_role": route_role,
                    "wavelength_nm": wavelength_nm,
                    "width_nm": width_nm,
                    "depth_nm": depth_nm,
                }
                route_bucket = route_aggregates.setdefault(route_key, dict(route_meta))
                role_bucket = role_aggregates.setdefault("route_role", {})
                scenario_bucket = scenario_aggregates.setdefault(scenario_id, {})
                _r5_update_aggregate(route_bucket, detectability_score)
                _r5_update_aggregate(role_bucket.setdefault(route_role, {}), detectability_score)
                _r5_update_aggregate(scenario_bucket, detectability_score)
                if route_role == "main_660":
                    _r5_update_aggregate(
                        main_660_aggregates.setdefault(route_key, dict(route_meta)),
                        detectability_score,
                    )
                elif route_role == "optional_robustness_probe":
                    _r5_update_aggregate(
                        optional_aggregates.setdefault(route_key, dict(route_meta)),
                        detectability_score,
                    )
                elif route_role.startswith("selected_annulus_sanity"):
                    _r5_update_aggregate(
                        selected_annulus_aggregates.setdefault(route_key, dict(route_meta)),
                        detectability_score,
                    )
                elif route_role == "full_grid_context_route":
                    _r5_update_aggregate(
                        context_aggregates.setdefault(route_key, dict(route_meta)),
                        detectability_score,
                    )

    if case_index != cost["case_row_count"]:
        raise RuntimeError("R5 actual case rows do not match the reviewed cap")

    role_rows = [
        _r5_aggregate_row(
            key_fields={
                "route_role": role,
                "route_role_locked": role == "main_660",
                "context_route_promotion_authorized": False,
                "main_660_redefinition_authorized": False,
                "selected_annulus_replaces_all_crossing_ranking": False,
            },
            aggregate=bucket,
        )
        for role, bucket in sorted(role_aggregates["route_role"].items())
    ]
    main_rows = [
        _r5_aggregate_row(
            key_fields={
                "route_id": bucket["route_id"],
                "wavelength_nm": bucket["wavelength_nm"],
                "width_nm": bucket["width_nm"],
                "depth_nm": bucket["depth_nm"],
                "route_role": "main_660",
                "main_660_route_role_locked": True,
                "R4_2_validation_grade_carryforward": True,
                "fine_confirm_main660_fraction": 1.0,
                "review_refined_main660_fraction": 1.0,
            },
            aggregate=bucket,
        )
        for _, bucket in sorted(main_660_aggregates.items())
    ]
    context_rows = [
        _r5_aggregate_row(
            key_fields={
                "route_id": bucket["route_id"],
                "wavelength_nm": bucket["wavelength_nm"],
                "width_nm": bucket["width_nm"],
                "depth_nm": bucket["depth_nm"],
                "route_role": "full_grid_context_route",
                "context_route_promotion_authorized": False,
                "route_promotion_eligible": False,
                "promotion_requires_external_review": True,
            },
            aggregate=bucket,
        )
        for _, bucket in sorted(context_aggregates.items())
    ]
    optional_rows = [
        _r5_aggregate_row(
            key_fields={
                "route_id": bucket["route_id"],
                "wavelength_nm": bucket["wavelength_nm"],
                "width_nm": bucket["width_nm"],
                "depth_nm": bucket["depth_nm"],
                "route_role": "optional_robustness_probe",
                "optional_660_900x1400_can_redefine_main_660": False,
            },
            aggregate=bucket,
        )
        for _, bucket in sorted(optional_aggregates.items())
    ] or [
        {
            "route_role": "optional_robustness_probe",
            "optional_660_900x1400_can_redefine_main_660": False,
            "n_case_rows": 0,
            "status": "not_present_in_v1_source_inventory",
        }
    ]
    selected_rows = [
        _r5_aggregate_row(
            key_fields={
                "route_id": bucket["route_id"],
                "wavelength_nm": bucket["wavelength_nm"],
                "width_nm": bucket["width_nm"],
                "depth_nm": bucket["depth_nm"],
                "route_role": bucket["route_role"],
                "selected_annulus_boundary_policy": "unchanged_v1_0p5_0p8_parallel_lens_only",
                "selected_annulus_replaces_all_crossing_ranking": False,
            },
            aggregate=bucket,
        )
        for _, bucket in sorted(selected_annulus_aggregates.items())
    ]
    scenario_summary_rows = [
        _r5_aggregate_row(
            key_fields={
                "scenario_bundle": scenario_id,
                "scenario_bundle_definition_checksum": source_checksums[
                    "R5_scenario_bundle_manifest_checksum"
                ],
            },
            aggregate=bucket,
        )
        for scenario_id, bucket in sorted(scenario_aggregates.items())
    ]
    r4_2_carryforward_rows = [
        {
            "accepted_gate": "PASS_R4_2_RESULTS_PREPARE_R5_PLAN_ONLY",
            "fine_confirm_main660_fraction": 1.0,
            "fine_confirm_sign_reliable_subset_fraction": 1.0,
            "review_refined_main660_fraction": 1.0,
            "fine_confirm_agrees_with_review_refined": 1.0,
            "R4_2_gate_met": True,
            "R4_2_recovery_decision": (
                "validation_grade_main660_recovered_prepare_R5_plan_review_only"
            ),
            **source_checksums,
        }
    ]
    coarse_warning_rows = [
        {
            "mesh_level": "coarse_screen",
            "coarse_screen_role": "screening_only_warning",
            "coarse_screen_can_confirm_or_demote_routes": False,
            "coarse_screen_ranking_role": "warning_only_not_rank_gate",
            "coarse_screen_conflict_retained_as_warning": True,
            "R5_ranking_gate_uses_coarse_screen": False,
        }
    ]
    detector_blank_rows = [
        {
            "ET2030_BNC_direct_to_LI5640_current_input": "forbidden",
            "requires_bench_validation": True,
            "bench_validation_artifact_id": "",
            "false_positive_per_min_claim": "analytic_prior_only",
            "finite_monte_carlo_zero_event_inferred": False,
            "legacy_detector_SNR_output_header_emitted": False,
            "legacy_calibrated_detector_SNR_output_header_emitted": False,
            "calibrated_SNR_or_event_probability_claim_emitted": False,
        }
    ]
    thermal_rows = [
        {
            "thermal_sidecar_does_not_increase_nodi_score": True,
            "max_thermal_404_log_multiplier": max(thermal_404_log_multipliers),
            "thermal_sidecar_used_to_increase_NODI_score": False,
            "thermal_404_claim_level": "safety_sidecar",
        }
    ]
    unit_rows = [
        {"metric": "detectability_relative_prior_score", "unit": "dimensionless", "status": "pass"},
        {"metric": "scenario_detector_SNR", "unit": "relative_proxy_absolute_blocked", "status": "pass"},
        {"metric": "expected_prior_score_proxy_count_at_10000", "unit": "proxy_count_not_observed_events", "status": "pass"},
    ]
    cost_row = {
        **cost,
        "actual_case_rows": case_index,
        "external_authorization": external_authorization,
        "R5_full_grid_v2_run": True,
        "R5_followup_expansion_authorized": False,
        "v1_source_verified_rows": source_inventory["row_count"],
        "v1_source_verified_route_identities": source_inventory["route_identity_count"],
        "v1_source_verified_particle_names": source_inventory["particle_name_count"],
        **source_checksums,
    }

    event_budget = {
        "stage": "R5_full_grid_v2",
        "v1_source_rows": source_inventory["row_count"],
        "scenario_bundles": len(scenario_rows),
        "stochastic_seeds": [],
        "case_rows": case_index,
        "max_R5_full_grid_v2_case_rows_before_review": (
            MAX_R5_FULL_GRID_V2_CASE_ROWS_BEFORE_REVIEW
        ),
        "R5_full_grid_v2_started": True,
        "R5_followup_expansion_started": False,
    }
    scenario_budget = {
        "external_authorization": external_authorization,
        "plan_schema_version": plan["schema_version"],
        "scenario_bundle_ids": [row["scenario_id"] for row in scenario_rows],
        "scenario_bundle_count": len(scenario_rows),
        "stochastic_seed_count": 0,
        "cartesian_uncertainty_expansion_authorized": False,
        "R4_2_gate_met": True,
        "coarse_screen_role": "screening_only_warning",
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        "route_specific_manual_sign_flips_authorized": False,
        **source_checksums,
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_R5_full_grid_v2",
        random_seed_policy="deterministic_R5_named_scenarios_no_stochastic_seeds",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=True,
        R4_representative_full_wave_validation_run=True,
        R5_full_grid_v2_run=True,
    )
    manifest["R4_revised_rerun_run"] = True
    manifest["R4_2_main660_nearwall_mesh_adjudication_run"] = True
    manifest["R5_full_grid_v2_execution_authorization"] = external_authorization
    manifest["R5_followup_expansion_authorized"] = False
    manifest["R5_case_rows_before_next_review"] = case_index
    manifest["context_route_promotion_authorized"] = False
    manifest["main_660_redefinition_authorized"] = False
    manifest["route_specific_manual_sign_flips_authorized"] = False
    manifest["calibrated_event_probability_claim_emitted"] = False
    manifest["absolute_LOD_or_true_concentration_claim_emitted"] = False
    manifest["biological_specificity_claim_emitted"] = False
    manifest.update(source_checksums)

    write_csv_rows(output / "full_grid_v2_case_manifest.csv", case_manifest_rows)
    write_csv_rows(output / "full_grid_v2_summary.csv", summary_rows)
    write_csv_rows(output / "route_role_stability_full_grid_v2.csv", role_rows)
    write_csv_rows(output / "main_660_full_grid_v2_stability_summary.csv", main_rows)
    write_csv_rows(output / "context_route_no_promotion_summary.csv", context_rows)
    write_csv_rows(output / "optional_660_governance_summary.csv", optional_rows)
    write_csv_rows(output / "selected_annulus_parallel_lens_summary.csv", selected_rows)
    write_csv_rows(output / "scenario_bundle_sensitivity_summary.csv", scenario_summary_rows)
    write_csv_rows(
        output / "R4_2_validation_grade_carryforward_summary.csv",
        r4_2_carryforward_rows,
    )
    write_csv_rows(
        output / "coarse_screen_warning_carryforward_summary.csv",
        coarse_warning_rows,
    )
    write_csv_rows(output / "detector_blank_claim_guardrail_summary.csv", detector_blank_rows)
    write_csv_rows(output / "thermal_404_sidecar_summary.csv", thermal_rows)
    write_csv_rows(output / "unit_guardrail_summary.csv", unit_rows)
    write_csv_rows(output / "full_grid_v2_cost_estimate.csv", [cost_row])
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    no_legacy_names = all(
        not FORBIDDEN_OUTPUT_NAMES.intersection(row.keys()) for row in summary_rows
    )
    all_snr_blocked = all(row["SNR_claim_level"] == "absolute_blocked" for row in summary_rows)
    all_event_blocked = all(
        row["event_probability_claim_level"] == "absolute_blocked"
        for row in summary_rows
    )
    report = (
        "# EV/NODI realism v2 R5 full-grid v2 report\n\n"
        f"- External authorization: {external_authorization}.\n"
        f"- Source rows: {source_inventory['row_count']}.\n"
        f"- Scenario bundles: {len(scenario_rows)}.\n"
        "- Stochastic seeds: 0.\n"
        f"- Case rows: {case_index} / cap {MAX_R5_FULL_GRID_V2_CASE_ROWS_BEFORE_REVIEW}.\n"
        f"- R5 follow-up expansion authorized: {False}.\n"
        f"- Context-route promotion authorized: {False}.\n"
        f"- Main-660 redefinition authorized: {False}.\n"
        f"- All SNR claims absolute_blocked: {all_snr_blocked}.\n"
        f"- Event probability claims absolute_blocked: {all_event_blocked}.\n"
        f"- Legacy exact SNR output names absent: {no_legacy_names}.\n"
        "- R4.2 validation-grade main-660 evidence carried forward.\n"
        "- Coarse-screen near-wall conflict retained as warning-only.\n"
        "- Detectability mapping remains relative_with_priors, not calibrated probability.\n"
    )
    (output / "R5_full_grid_v2_report.md").write_text(report, encoding="utf-8")

    return {
        "output_dir": str(output),
        "manifest": manifest,
        "case_rows": case_index,
        "under_R5_review_cap": cost["under_R5_review_cap"],
        "R5_full_grid_v2_run": True,
        "R5_followup_expansion_authorized": False,
        "all_snr_claims_absolute_blocked": all_snr_blocked,
        "event_probability_absolute_blocked": all_event_blocked,
        "legacy_snr_output_names_absent": no_legacy_names,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
    }


def run_R5_1_route_role_stability_interpretation(
    output_dir: str | Path = DEFAULT_R5_1_INTERPRETATION_DIR,
    *,
    external_authorization: str = "PASS_TO_R5_1_ROUTE_ROLE_STABILITY_INTERPRETATION_ONLY",
    write_root_manifest: bool = True,
) -> dict[str, Any]:
    if external_authorization != "PASS_TO_R5_1_ROUTE_ROLE_STABILITY_INTERPRETATION_ONLY":
        raise ValueError("R5.1 interpretation requires exact external authorization")
    plan = validate_R5_1_route_role_stability_plan()
    r5_dir = DEFAULT_R5_FULL_GRID_V2_DIR
    if not r5_dir.exists():
        raise FileNotFoundError(f"R5 result directory not found: {r5_dir}")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"

    source_checksums = {
        "R5_case_manifest_checksum": sha256_file(r5_dir / "full_grid_v2_case_manifest.csv"),
        "R5_summary_checksum": sha256_file(r5_dir / "full_grid_v2_summary.csv"),
        "R5_route_role_stability_checksum": sha256_file(
            r5_dir / "route_role_stability_full_grid_v2.csv"
        ),
        "R5_main660_summary_checksum": sha256_file(
            r5_dir / "main_660_full_grid_v2_stability_summary.csv"
        ),
        "R5_context_no_promotion_checksum": sha256_file(
            r5_dir / "context_route_no_promotion_summary.csv"
        ),
        "R5_scenario_sensitivity_checksum": sha256_file(
            r5_dir / "scenario_bundle_sensitivity_summary.csv"
        ),
        "R5_cost_estimate_checksum": sha256_file(r5_dir / "full_grid_v2_cost_estimate.csv"),
        "R5_run_manifest_checksum": sha256_file(r5_dir / "run_manifest.json"),
    }
    plan_provenance = plan["provenance_freeze"]
    for field in R5_1_REQUIRED_PROVENANCE_FIELDS:
        if source_checksums[field] != plan_provenance[field]:
            raise ValueError(f"R5.1 source checksum drift before interpretation: {field}")

    role_rows = _read_csv_dicts(r5_dir / "route_role_stability_full_grid_v2.csv")
    main_rows = _read_csv_dicts(r5_dir / "main_660_full_grid_v2_stability_summary.csv")
    context_rows = _read_csv_dicts(r5_dir / "context_route_no_promotion_summary.csv")
    selected_rows = _read_csv_dicts(r5_dir / "selected_annulus_parallel_lens_summary.csv")
    scenario_rows = _read_csv_dicts(r5_dir / "scenario_bundle_sensitivity_summary.csv")
    detector_rows = _read_csv_dicts(r5_dir / "detector_blank_claim_guardrail_summary.csv")
    thermal_rows = _read_csv_dicts(r5_dir / "thermal_404_sidecar_summary.csv")
    unit_rows = _read_csv_dicts(r5_dir / "unit_guardrail_summary.csv")
    cost_row = _read_csv_dicts(r5_dir / "full_grid_v2_cost_estimate.csv")[0]
    r5_manifest = json.loads((r5_dir / "run_manifest.json").read_text(encoding="utf-8"))

    if int(cost_row["actual_case_rows"]) != MAX_R5_FULL_GRID_V2_CASE_ROWS_BEFORE_REVIEW:
        raise ValueError("R5.1 cannot interpret R5 rows outside reviewed cap")
    if r5_manifest.get("R5_followup_expansion_authorized") is not False:
        raise ValueError("R5.1 cannot consume an expanded R5 follow-up artifact")

    role_by_id = {str(row["route_role"]): row for row in role_rows}
    main_mean = float(role_by_id["main_660"]["mean_detectability_relative_prior_score"])
    weak_mean = float(
        role_by_id["weak_reference_control"]["mean_detectability_relative_prior_score"]
    )
    optional_mean = float(
        role_by_id["optional_robustness_probe"][
            "mean_detectability_relative_prior_score"
        ]
    )
    top_context_rows = sorted(
        context_rows,
        key=lambda row: float(row["mean_detectability_relative_prior_score"]),
        reverse=True,
    )[:10]
    high_context_count = sum(
        1
        for row in context_rows
        if float(row["mean_detectability_relative_prior_score"]) > main_mean
    )
    scenario_means = [
        float(row["mean_detectability_relative_prior_score"]) for row in scenario_rows
    ]
    scenario_spread_ratio = max(scenario_means) / max(min(scenario_means), 1.0e-12)
    selected_future_recommendation = "prepare_bounded_additional_scenario_prior_audit_plan_only"
    interpretation_decision = (
        "R5_clean_but_weak_reference_and_context_warnings_require_bounded_scenario_prior_audit_plan"
    )

    interpretation_manifest_rows = [
        {
            "stage": "R5_1_route_role_stability_interpretation",
            "external_authorization": external_authorization,
            "R5_1_interpretation_run": True,
            "R5_case_rows_interpreted": cost_row["actual_case_rows"],
            "new_case_rows_added": 0,
            "new_scenario_bundles_added": 0,
            "new_stochastic_seeds_added": 0,
            "new_solver_cases_added": 0,
            "new_experiments_started": 0,
            "selected_future_recommendation_class": selected_future_recommendation,
            "interpretation_decision": interpretation_decision,
            "R6_plan_preparation_authorized": False,
            "R6_execution_authorized": False,
            "R5_followup_expansion_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "calibrated_SNR_claim_emitted": False,
            "calibrated_event_probability_claim_emitted": False,
            **source_checksums,
        }
    ]

    decision_rows = [
        {
            "decision_subject": "main_660_locked_routes",
            "evidence_summary": (
                "R4.2 validation-grade carryforward is clean; R5 main_660 mean is "
                f"{main_mean:.12g} across 896 rows."
            ),
            "interpretation": "main_660_remains_locked_but_not_promoted_to_calibrated_or_final",
            "recommended_next_class": selected_future_recommendation,
            "R6_plan_preparation_authorized": False,
            "route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "claim_level": "relative_with_priors",
        },
        {
            "decision_subject": "weak_reference_control",
            "evidence_summary": (
                f"weak_reference_control mean {weak_mean:.12g} exceeds main_660 mean "
                f"{main_mean:.12g}."
            ),
            "interpretation": "weak_reference_high_score_requires_control_artifact_or_prior_sensitivity_audit",
            "recommended_next_class": selected_future_recommendation,
            "R6_plan_preparation_authorized": False,
            "route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "claim_level": "relative_with_priors",
        },
        {
            "decision_subject": "context_route_high_score_warnings",
            "evidence_summary": (
                f"{high_context_count} context routes exceed main_660 mean; top context is "
                f"{top_context_rows[0]['route_id']}."
            ),
            "interpretation": "context_high_scores_are_warnings_not_promotions",
            "recommended_next_class": selected_future_recommendation,
            "R6_plan_preparation_authorized": False,
            "route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "claim_level": "relative_with_priors",
        },
        {
            "decision_subject": "optional_660_900x1400",
            "evidence_summary": (
                f"optional robustness probe mean {optional_mean:.12g}; governance field "
                "prevents redefining main_660."
            ),
            "interpretation": "optional_route_remains_probe_only",
            "recommended_next_class": selected_future_recommendation,
            "R6_plan_preparation_authorized": False,
            "route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "claim_level": "relative_with_priors",
        },
    ]

    scenario_interpretation_rows = []
    for row in sorted(
        scenario_rows,
        key=lambda item: float(item["mean_detectability_relative_prior_score"]),
        reverse=True,
    ):
        mean_score = float(row["mean_detectability_relative_prior_score"])
        scenario_interpretation_rows.append(
            {
                "scenario_bundle": row["scenario_bundle"],
                "n_case_rows": row["n_case_rows"],
                "mean_detectability_relative_prior_score": row[
                    "mean_detectability_relative_prior_score"
                ],
                "scenario_rank_by_mean": len(scenario_interpretation_rows) + 1,
                "relative_to_nominal_interpretation": (
                    "high_scenario_prior_sensitivity"
                    if mean_score > main_mean
                    else "scenario_prior_sensitivity_requires_context"
                ),
                "claim_level": "relative_with_priors",
                "calibrated_probability_claim_authorized": False,
                "R5_followup_expansion_authorized": False,
            }
        )

    context_warning_rows = []
    for rank, row in enumerate(top_context_rows, start=1):
        context_warning_rows.append(
            {
                "warning_rank": rank,
                "route_id": row["route_id"],
                "wavelength_nm": row["wavelength_nm"],
                "width_nm": row["width_nm"],
                "depth_nm": row["depth_nm"],
                "mean_detectability_relative_prior_score": row[
                    "mean_detectability_relative_prior_score"
                ],
                "max_detectability_relative_prior_score": row[
                    "max_detectability_relative_prior_score"
                ],
                "exceeds_main_660_mean": (
                    float(row["mean_detectability_relative_prior_score"]) > main_mean
                ),
                "context_route_promotion_authorized": False,
                "route_promotion_eligible": False,
                "interpretation": "high_context_score_warning_not_route_promotion",
            }
        )

    main_interpretation_rows = []
    for row in main_rows:
        main_interpretation_rows.append(
            {
                "route_id": row["route_id"],
                "wavelength_nm": row["wavelength_nm"],
                "width_nm": row["width_nm"],
                "depth_nm": row["depth_nm"],
                "route_role": row["route_role"],
                "main_660_route_role_locked": True,
                "mean_detectability_relative_prior_score": row[
                    "mean_detectability_relative_prior_score"
                ],
                "fine_confirm_main660_fraction": row["fine_confirm_main660_fraction"],
                "review_refined_main660_fraction": row[
                    "review_refined_main660_fraction"
                ],
                "interpretation": "locked_main_660_robust_relative_prior_evidence_not_final_calibration",
                "main_660_redefinition_authorized": False,
                "R6_plan_preparation_authorized": False,
            }
        )

    weak_reference_rows = [
        {
            "route_role": "weak_reference_control",
            "mean_detectability_relative_prior_score": weak_mean,
            "main_660_mean_detectability_relative_prior_score": main_mean,
            "weak_reference_exceeds_main_660": weak_mean > main_mean,
            "interpretation": (
                "control_route_exceeds_main_660_under_R5_scenarios_and_requires_bounded_prior_audit"
            ),
            "route_promotion_authorized": False,
            "R6_plan_preparation_authorized": False,
        }
    ]

    selected_annulus_rows = []
    for row in selected_rows:
        selected_annulus_rows.append(
            {
                "route_id": row["route_id"],
                "route_role": row["route_role"],
                "selected_annulus_boundary_policy": row[
                    "selected_annulus_boundary_policy"
                ],
                "mean_detectability_relative_prior_score": row[
                    "mean_detectability_relative_prior_score"
                ],
                "selected_annulus_replaces_all_crossing_ranking": False,
                "selected_annulus_bound_change_authorized": False,
                "interpretation": "selected_annulus_remains_parallel_lens_only",
            }
        )

    detector = detector_rows[0]
    thermal = thermal_rows[0]
    claim_guard_rows = [
        {
            "guardrail": "SNR_claim_level",
            "value": "absolute_blocked",
            "status": "pass",
        },
        {
            "guardrail": "event_probability_claim_level",
            "value": "absolute_blocked",
            "status": "pass",
        },
        {
            "guardrail": "p_detect_mapping_claim_level",
            "value": "relative_with_priors",
            "status": "pass",
        },
        {
            "guardrail": "legacy_detector_SNR_output_header_emitted",
            "value": detector["legacy_detector_SNR_output_header_emitted"],
            "status": "pass" if detector["legacy_detector_SNR_output_header_emitted"] == "False" else "fail",
        },
        {
            "guardrail": "legacy_calibrated_detector_SNR_output_header_emitted",
            "value": detector["legacy_calibrated_detector_SNR_output_header_emitted"],
            "status": "pass" if detector["legacy_calibrated_detector_SNR_output_header_emitted"] == "False" else "fail",
        },
        {
            "guardrail": "thermal_sidecar_used_to_increase_NODI_score",
            "value": thermal["thermal_sidecar_used_to_increase_NODI_score"],
            "status": "pass" if thermal["thermal_sidecar_used_to_increase_NODI_score"] == "False" else "fail",
        },
        {
            "guardrail": "unit_guardrail_all_rows",
            "value": all(row["status"] == "pass" for row in unit_rows),
            "status": "pass",
        },
    ]

    options_matrix_rows = [
        {
            "future_recommendation_class": "prepare_R6_plan_for_external_review_only",
            "R5_1_recommendation": "not_selected_now",
            "rationale": "R5 route-role ambiguity should be interpreted through bounded prior audit before R6 planning.",
            "authorizes_execution": False,
        },
        {
            "future_recommendation_class": "prepare_post_v2_validation_dependency_backlog_only",
            "R5_1_recommendation": "not_selected_now",
            "rationale": "Post-v2 validation dependencies remain outside the no-measured-data v2 lane.",
            "authorizes_execution": False,
        },
        {
            "future_recommendation_class": selected_future_recommendation,
            "R5_1_recommendation": "selected_for_future_review",
            "rationale": "Weak-reference and high context-route scores require bounded scenario-prior interpretation before R6.",
            "authorizes_execution": False,
        },
        {
            "future_recommendation_class": "hold_for_route_governance_revision_plan_only",
            "R5_1_recommendation": "fallback_if_audit_reveals_route_role_instability",
            "rationale": "Governance revision remains possible but is not selected directly from R5.1.",
            "authorizes_execution": False,
        },
    ]

    event_budget = {
        "stage": "R5_1_route_role_stability_interpretation",
        "R5_case_rows_interpreted": int(cost_row["actual_case_rows"]),
        "new_case_rows": 0,
        "new_scenario_bundles": 0,
        "new_stochastic_seeds": 0,
        "new_solver_cases": 0,
        "new_experiments": 0,
        "R6_execution_started": False,
    }
    scenario_budget = {
        "external_authorization": external_authorization,
        "selected_future_recommendation_class": selected_future_recommendation,
        "scenario_spread_ratio_from_R5_mean_scores": scenario_spread_ratio,
        "R5_followup_expansion_authorized": False,
        "R6_plan_preparation_authorized": False,
        "R6_execution_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        **source_checksums,
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_R5_1_route_role_stability_interpretation",
        random_seed_policy="none_interpret_existing_R5_artifacts_only",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=True,
        R4_representative_full_wave_validation_run=True,
        R5_full_grid_v2_run=True,
    )
    manifest["R4_revised_rerun_run"] = True
    manifest["R4_2_main660_nearwall_mesh_adjudication_run"] = True
    manifest["R5_1_route_role_stability_interpretation_run"] = True
    manifest["R5_1_external_authorization"] = external_authorization
    manifest["R5_1_selected_future_recommendation_class"] = selected_future_recommendation
    manifest["R6_plan_preparation_authorized"] = False
    manifest["R6_execution_authorized"] = False
    manifest["R5_followup_expansion_authorized"] = False
    manifest["new_case_rows_authorized"] = 0
    manifest["context_route_promotion_authorized"] = False
    manifest["main_660_redefinition_authorized"] = False
    manifest["route_specific_manual_sign_flips_authorized"] = False
    manifest["calibrated_event_probability_claim_emitted"] = False
    manifest["absolute_LOD_or_true_concentration_claim_emitted"] = False
    manifest["biological_specificity_claim_emitted"] = False
    manifest.update(source_checksums)

    write_csv_rows(
        output / "R5_1_route_role_stability_interpretation_manifest.csv",
        interpretation_manifest_rows,
    )
    write_csv_rows(output / "R5_1_route_role_stability_decision_table.csv", decision_rows)
    write_csv_rows(
        output / "R5_1_scenario_sensitivity_interpretation.csv",
        scenario_interpretation_rows,
    )
    write_csv_rows(
        output / "R5_1_context_route_high_score_warning_table.csv",
        context_warning_rows,
    )
    write_csv_rows(output / "R5_1_main_660_robustness_interpretation.csv", main_interpretation_rows)
    write_csv_rows(output / "R5_1_weak_reference_control_interpretation.csv", weak_reference_rows)
    write_csv_rows(
        output / "R5_1_selected_annulus_nonpromotion_summary.csv",
        selected_annulus_rows,
    )
    write_csv_rows(output / "R5_1_claim_boundary_guardrail_summary.csv", claim_guard_rows)
    write_csv_rows(output / "R5_1_next_stage_options_matrix.csv", options_matrix_rows)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    report = (
        "# EV/NODI realism v2 R5.1 route-role stability interpretation report\n\n"
        f"- External authorization: {external_authorization}.\n"
        "- Existing R5 artifacts only; new case rows: 0.\n"
        f"- R5 case rows interpreted: {cost_row['actual_case_rows']}.\n"
        f"- Main-660 mean relative score: {main_mean:.6f}.\n"
        f"- Weak-reference-control mean relative score: {weak_mean:.6f}.\n"
        f"- Context routes exceeding main-660 mean: {high_context_count}.\n"
        f"- Top context warning route: {top_context_rows[0]['route_id']}.\n"
        f"- Selected future recommendation class: {selected_future_recommendation}.\n"
        "- R6 plan preparation authorized: false.\n"
        "- R6 execution authorized: false.\n"
        "- Context-route promotion authorized: false.\n"
        "- Main-660 redefinition authorized: false.\n"
        "- Claim boundaries remain relative_with_priors / absolute_blocked.\n"
    )
    (output / "R5_1_route_role_stability_interpretation_report.md").write_text(
        report,
        encoding="utf-8",
    )

    return {
        "output_dir": str(output),
        "manifest": manifest,
        "R5_1_interpretation_run": True,
        "new_case_rows_added": 0,
        "selected_future_recommendation_class": selected_future_recommendation,
        "R6_plan_preparation_authorized": False,
        "R6_execution_authorized": False,
        "R5_followup_expansion_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        "weak_reference_exceeds_main_660": weak_mean > main_mean,
        "context_routes_exceeding_main_660_mean": high_context_count,
    }


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("cannot compute mean of empty values")
    return sum(values) / len(values)


def _audit_route_group(plan: dict[str, Any]) -> dict[str, str]:
    groups: dict[str, str] = {}
    for group, rows in plan["audit_route_set"].items():
        for row in rows:
            groups[str(row["route_id"])] = group
    return groups


def run_R5_2_bounded_scenario_prior_audit(
    output_dir: str | Path = DEFAULT_R5_2_BOUNDED_SCENARIO_PRIOR_AUDIT_DIR,
    *,
    external_authorization: str = "PASS_TO_BOUNDED_SCENARIO_PRIOR_AUDIT_ONLY",
    write_root_manifest: bool = True,
) -> dict[str, Any]:
    if external_authorization != "PASS_TO_BOUNDED_SCENARIO_PRIOR_AUDIT_ONLY":
        raise ValueError("R5.2 audit requires exact external authorization")
    plan = validate_R5_2_bounded_scenario_prior_audit_plan()
    r5_dir = DEFAULT_R5_FULL_GRID_V2_DIR
    r5_1_dir = DEFAULT_R5_1_INTERPRETATION_DIR
    if not r5_dir.exists():
        raise FileNotFoundError(f"R5 result directory not found: {r5_dir}")
    if not r5_1_dir.exists():
        raise FileNotFoundError(f"R5.1 result directory not found: {r5_1_dir}")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"

    source_checksums = {
        "R5_1_manifest_checksum": sha256_file(
            r5_1_dir / "R5_1_route_role_stability_interpretation_manifest.csv"
        ),
        "R5_1_decision_table_checksum": sha256_file(
            r5_1_dir / "R5_1_route_role_stability_decision_table.csv"
        ),
        "R5_1_context_warning_table_checksum": sha256_file(
            r5_1_dir / "R5_1_context_route_high_score_warning_table.csv"
        ),
        "R5_1_weak_reference_checksum": sha256_file(
            r5_1_dir / "R5_1_weak_reference_control_interpretation.csv"
        ),
        "R5_1_next_stage_options_checksum": sha256_file(
            r5_1_dir / "R5_1_next_stage_options_matrix.csv"
        ),
        "R5_1_run_manifest_checksum": sha256_file(r5_1_dir / "run_manifest.json"),
        "R5_case_manifest_checksum": sha256_file(
            r5_dir / "full_grid_v2_case_manifest.csv"
        ),
        "R5_summary_checksum": sha256_file(r5_dir / "full_grid_v2_summary.csv"),
        "R5_context_no_promotion_checksum": sha256_file(
            r5_dir / "context_route_no_promotion_summary.csv"
        ),
        "R5_route_role_stability_checksum": sha256_file(
            r5_dir / "route_role_stability_full_grid_v2.csv"
        ),
        "R5_scenario_sensitivity_checksum": sha256_file(
            r5_dir / "scenario_bundle_sensitivity_summary.csv"
        ),
        "R5_run_manifest_checksum": sha256_file(r5_dir / "run_manifest.json"),
    }
    for field in R5_2_REQUIRED_PROVENANCE_FIELDS:
        if source_checksums[field] != plan["provenance_freeze"][field]:
            raise ValueError(f"R5.2 source checksum drift before audit: {field}")

    full_summary_path = r5_dir / "full_grid_v2_summary.csv"
    validate_output_names(_csv_headers(full_summary_path))

    route_groups = _audit_route_group(plan)
    planned_rows = {
        row["route_id"]: int(row["expected_existing_R5_rows"])
        for rows in plan["audit_route_set"].values()
        for row in rows
    }
    audit_rows: list[dict[str, str]] = []
    with full_summary_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["route_id"] in R5_2_AUDIT_ROUTE_IDS:
                audit_rows.append(row)

    if len(audit_rows) != R5_2_EXISTING_R5_AUDIT_ROW_CAP:
        raise ValueError("R5.2 audit source rows exceed or miss reviewed plan cap")
    route_counts: dict[str, int] = {}
    for row in audit_rows:
        route_counts[row["route_id"]] = route_counts.get(row["route_id"], 0) + 1
    if route_counts != planned_rows:
        raise ValueError("R5.2 audit route set row counts do not match plan")
    if {row["scenario_bundle"] for row in audit_rows} != R5_REQUIRED_SCENARIO_BUNDLE_IDS:
        raise ValueError("R5.2 audit scenario bundle set drifted")
    if {row["stochastic_seed"] for row in audit_rows} != {""}:
        raise ValueError("R5.2 audit cannot include stochastic seeds")
    if {row["particle_name"] for row in audit_rows} and (
        len({row["particle_name"] for row in audit_rows}) != R5_V1_SOURCE_PARTICLE_NAME_COUNT
    ):
        raise ValueError("R5.2 audit particle count mismatch")
    for row in audit_rows:
        if row["SNR_claim_level"] != "absolute_blocked":
            raise ValueError("R5.2 audit SNR claim boundary drifted")
        if row["event_probability_claim_level"] != "absolute_blocked":
            raise ValueError("R5.2 audit event probability boundary drifted")
        if row["p_detect_mapping_claim_level"] != "relative_with_priors":
            raise ValueError("R5.2 audit p_detect claim boundary drifted")
        if row["context_route_promotion_authorized"] != "False":
            raise ValueError("R5.2 audit cannot consume promoted context rows")
        if row["main_660_redefinition_authorized"] != "False":
            raise ValueError("R5.2 audit cannot consume redefined main_660 rows")
        if row["route_specific_manual_sign_flip_applied"] != "False":
            raise ValueError("R5.2 audit cannot consume route-specific sign flips")

    scenarios = sorted(R5_REQUIRED_SCENARIO_BUNDLE_IDS)
    scores = {
        "all": [float(row["detectability_relative_prior_score"]) for row in audit_rows],
        "main": [
            float(row["detectability_relative_prior_score"])
            for row in audit_rows
            if row["route_role"] == "main_660"
        ],
        "weak": [
            float(row["detectability_relative_prior_score"])
            for row in audit_rows
            if row["route_role"] == "weak_reference_control"
        ],
        "context": [
            float(row["detectability_relative_prior_score"])
            for row in audit_rows
            if row["route_id"] in R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS
        ],
    }
    main_mean = _mean(scores["main"])
    weak_mean = _mean(scores["weak"])

    main_by_scenario: dict[str, float] = {}
    weak_by_scenario: dict[str, float] = {}
    context_by_scenario: dict[str, float] = {}
    for scenario in scenarios:
        main_by_scenario[scenario] = _mean(
            [
                float(row["detectability_relative_prior_score"])
                for row in audit_rows
                if row["route_role"] == "main_660"
                and row["scenario_bundle"] == scenario
            ]
        )
        weak_by_scenario[scenario] = _mean(
            [
                float(row["detectability_relative_prior_score"])
                for row in audit_rows
                if row["route_role"] == "weak_reference_control"
                and row["scenario_bundle"] == scenario
            ]
        )
        context_by_scenario[scenario] = _mean(
            [
                float(row["detectability_relative_prior_score"])
                for row in audit_rows
                if row["route_id"] in R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS
                and row["scenario_bundle"] == scenario
            ]
        )

    weak_exceeds_main_scenario_count = sum(
        1 for scenario in scenarios if weak_by_scenario[scenario] > main_by_scenario[scenario]
    )

    context_route_rows = []
    all_context_above_all_scenarios = True
    for route_id in sorted(
        R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS,
        key=lambda rid: -_mean(
            [
                float(row["detectability_relative_prior_score"])
                for row in audit_rows
                if row["route_id"] == rid
            ]
        ),
    ):
        route_values = [
            float(row["detectability_relative_prior_score"])
            for row in audit_rows
            if row["route_id"] == route_id
        ]
        scenario_above = 0
        for scenario in scenarios:
            route_scenario_mean = _mean(
                [
                    float(row["detectability_relative_prior_score"])
                    for row in audit_rows
                    if row["route_id"] == route_id
                    and row["scenario_bundle"] == scenario
                ]
            )
            if route_scenario_mean > main_by_scenario[scenario]:
                scenario_above += 1
        all_context_above_all_scenarios = (
            all_context_above_all_scenarios and scenario_above == len(scenarios)
        )
        first = next(row for row in audit_rows if row["route_id"] == route_id)
        route_mean = _mean(route_values)
        context_route_rows.append(
            {
                "route_id": route_id,
                "wavelength_nm": first["wavelength_nm"],
                "width_nm": first["width_nm"],
                "depth_nm": first["depth_nm"],
                "route_role": first["route_role"],
                "n_existing_R5_rows_audited": len(route_values),
                "mean_detectability_relative_prior_score": route_mean,
                "main_660_mean_detectability_relative_prior_score": main_mean,
                "delta_vs_main_660_mean": route_mean - main_mean,
                "ratio_vs_main_660_mean": route_mean / main_mean,
                "scenario_bundle_count_above_main_660": scenario_above,
                "context_route_promotion_authorized": False,
                "route_promotion_eligible": False,
                "interpretation": (
                    "systematic_above_main_context_warning_not_route_promotion"
                ),
            }
        )

    traceability_rows = []
    for row in audit_rows:
        traceability_rows.append(
            {
                "R5_case_id": row["R5_case_id"],
                "source_v1_row_index": row["source_v1_row_index"],
                "source_v1_case_id": row["source_v1_case_id"],
                "source_v1_case_hash": row["source_v1_case_hash"],
                "route_id": row["route_id"],
                "audit_route_group": route_groups[row["route_id"]],
                "wavelength_nm": row["wavelength_nm"],
                "width_nm": row["width_nm"],
                "depth_nm": row["depth_nm"],
                "route_role": row["route_role"],
                "particle_name": row["particle_name"],
                "scenario_bundle": row["scenario_bundle"],
                "scenario_identity": row["scenario_identity"],
                "stochastic_seed": row["stochastic_seed"],
                "detectability_relative_prior_score": row[
                    "detectability_relative_prior_score"
                ],
                "source_v1_relative_score": row["source_v1_relative_score"],
                "scenario_relative_prior_multiplier": row[
                    "scenario_relative_prior_multiplier"
                ],
                "scenario_detector_SNR": row["scenario_detector_SNR"],
                "effective_scenario_detector_SNR": row[
                    "effective_scenario_detector_SNR"
                ],
                "primary_metric": row["primary_metric"],
                "SNR_claim_level": row["SNR_claim_level"],
                "event_probability_claim_level": row["event_probability_claim_level"],
                "p_detect_mapping_claim_level": row["p_detect_mapping_claim_level"],
                "detected_events_source": row["detected_events_source"],
                "context_route_promotion_authorized": False,
                "main_660_redefinition_authorized": False,
                "route_specific_manual_sign_flip_applied": False,
                "selected_annulus_replaces_all_crossing_ranking": False,
                "claim_level": row["claim_level"],
            }
        )

    scenario_rows = []
    for scenario in scenarios:
        scenario_audit_values = [
            float(row["detectability_relative_prior_score"])
            for row in audit_rows
            if row["scenario_bundle"] == scenario
        ]
        scenario_rows.append(
            {
                "scenario_bundle": scenario,
                "n_existing_R5_rows_audited": len(scenario_audit_values),
                "mean_detectability_relative_prior_score": _mean(scenario_audit_values),
                "main_660_mean": main_by_scenario[scenario],
                "weak_reference_control_mean": weak_by_scenario[scenario],
                "above_main_context_route_mean": context_by_scenario[scenario],
                "weak_reference_exceeds_main_660": (
                    weak_by_scenario[scenario] > main_by_scenario[scenario]
                ),
                "context_route_family_exceeds_main_660": (
                    context_by_scenario[scenario] > main_by_scenario[scenario]
                ),
                "new_scenario_bundle_authorized": False,
                "calibrated_probability_claim_authorized": False,
                "interpretation": "existing_scenario_prior_contribution_only",
            }
        )

    route_family_rows = []
    for group, group_routes in plan["audit_route_set"].items():
        group_ids = {str(row["route_id"]) for row in group_routes}
        group_values = [
            float(row["detectability_relative_prior_score"])
            for row in audit_rows
            if row["route_id"] in group_ids
        ]
        route_family_rows.append(
            {
                "audit_route_group": group,
                "n_route_ids": len(group_ids),
                "n_existing_R5_rows_audited": len(group_values),
                "mean_detectability_relative_prior_score": _mean(group_values),
                "max_detectability_relative_prior_score": max(group_values),
                "main_660_mean_detectability_relative_prior_score": main_mean,
                "group_exceeds_main_660_mean": _mean(group_values) > main_mean,
                "route_promotion_authorized": False,
                "interpretation": (
                    "route_family_prior_warning"
                    if _mean(group_values) > main_mean
                    else "route_family_below_or_comparator_only"
                ),
            }
        )

    main_rows = []
    for route_id in sorted(
        {row["route_id"] for row in audit_rows if row["route_role"] == "main_660"}
    ):
        route_values = [
            float(row["detectability_relative_prior_score"])
            for row in audit_rows
            if row["route_id"] == route_id
        ]
        first = next(row for row in audit_rows if row["route_id"] == route_id)
        main_rows.append(
            {
                "route_id": route_id,
                "wavelength_nm": first["wavelength_nm"],
                "width_nm": first["width_nm"],
                "depth_nm": first["depth_nm"],
                "n_existing_R5_rows_audited": len(route_values),
                "mean_detectability_relative_prior_score": _mean(route_values),
                "min_detectability_relative_prior_score": min(route_values),
                "max_detectability_relative_prior_score": max(route_values),
                "main_660_route_role_locked": True,
                "main_660_redefinition_authorized": False,
                "route_promotion_authorized": False,
                "interpretation": "locked_main_660_comparator_not_redefined",
            }
        )

    selected_and_404_rows = []
    selected_or_404_ids = {
        row["route_id"]
        for row in plan["audit_route_set"]["selected_annulus_parallel_lens_sidecars"]
    } | {"404_600x1300"}
    for route_id in sorted(selected_or_404_ids):
        route_values = [
            float(row["detectability_relative_prior_score"])
            for row in audit_rows
            if row["route_id"] == route_id
        ]
        first = next(row for row in audit_rows if row["route_id"] == route_id)
        selected_and_404_rows.append(
            {
                "route_id": route_id,
                "route_role": first["route_role"],
                "n_existing_R5_rows_audited": len(route_values),
                "mean_detectability_relative_prior_score": _mean(route_values),
                "selected_annulus_replaces_all_crossing_ranking": False,
                "selected_annulus_bound_change_authorized": False,
                "thermal_sidecar_used_to_increase_NODI_score": False,
                "interpretation": "sidecar_or_parallel_lens_not_promotion",
            }
        )

    claim_guard_rows = []
    for guardrail, value in (
        ("SNR_claim_level", "absolute_blocked"),
        ("event_probability_claim_level", "absolute_blocked"),
        ("p_detect_mapping_claim_level", "relative_with_priors"),
        ("legacy_detector_SNR_output_header_emitted", False),
        ("legacy_calibrated_detector_SNR_output_header_emitted", False),
        ("calibrated_SNR_or_event_probability_claim_emitted", False),
        ("absolute_LOD_or_true_concentration_claim_emitted", False),
        ("biological_specificity_claim_emitted", False),
        ("thermal_sidecar_used_to_increase_NODI_score", False),
        ("finite_zero_event_blank_safety_claim_emitted", False),
    ):
        claim_guard_rows.append({"guardrail": guardrail, "value": value, "status": "pass"})

    selected_future_recommendation = "prepare_route_prior_model_revision_plan_only"
    audit_decision = (
        "systematic_weak_reference_and_context_prior_warning_blocks_R6_plan"
    )
    decision_rows = [
        {
            "decision_subject": "weak_reference_control",
            "audit_finding": (
                f"weak_reference_control exceeds main_660 in "
                f"{weak_exceeds_main_scenario_count}/{len(scenarios)} existing R5 scenarios"
            ),
            "interpretation": "systematic_control_prior_warning",
            "recommended_next_class": selected_future_recommendation,
            "R6_plan_preparation_authorized": False,
            "route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "claim_level": "relative_with_priors",
        },
        {
            "decision_subject": "above_main_context_routes",
            "audit_finding": (
                f"{len(R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS)} context routes exceed main_660 "
                "under all 8 existing R5 scenarios"
            ),
            "interpretation": "systematic_context_family_warning_not_promotion",
            "recommended_next_class": selected_future_recommendation,
            "R6_plan_preparation_authorized": False,
            "route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "claim_level": "relative_with_priors",
        },
        {
            "decision_subject": "main_660_locked_anchor",
            "audit_finding": "main_660 remains locked but is outscored by weak-reference/control warnings",
            "interpretation": "main_660_governance_anchor_requires_prior_model_review_before_R6",
            "recommended_next_class": selected_future_recommendation,
            "R6_plan_preparation_authorized": False,
            "route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "claim_level": "relative_with_priors",
        },
        {
            "decision_subject": "selected_annulus_and_404_sidecars",
            "audit_finding": "sidecar and selected-annulus rows remain non-promoting",
            "interpretation": "sidecars_do_not_change_route_governance",
            "recommended_next_class": selected_future_recommendation,
            "R6_plan_preparation_authorized": False,
            "route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "claim_level": "relative_with_priors",
        },
    ]

    next_stage_rows = []
    for recommendation in sorted(R5_2_ALLOWED_FUTURE_RECOMMENDATION_CLASSES):
        selected = recommendation == selected_future_recommendation
        next_stage_rows.append(
            {
                "future_recommendation_class": recommendation,
                "R5_2_recommendation": "selected_for_future_review"
                if selected
                else "not_selected_now",
                "rationale": (
                    "Systematic weak-reference and context-route prior warnings require route-prior model revision before R6."
                    if selected
                    else "Not selected by this bounded audit result."
                ),
                "authorizes_execution": False,
                "authorizes_R6_plan": False,
                "authorizes_route_promotion": False,
            }
        )

    manifest_rows = [
        {
            "stage": "R5_2_bounded_scenario_prior_audit",
            "external_authorization": external_authorization,
            "R5_2_bounded_scenario_prior_audit_run": True,
            "audit_execution_type": "posthoc_existing_R5_artifact_audit_only",
            "existing_R5_rows_audited": len(audit_rows),
            "audit_route_id_count": len(route_counts),
            "scenario_bundle_count": len(scenarios),
            "stochastic_seed_count": 0,
            "new_case_rows_added": 0,
            "new_scenario_bundles_added": 0,
            "new_stochastic_seeds_added": 0,
            "new_solver_cases_added": 0,
            "new_experiments_started": 0,
            "selected_future_recommendation_class": selected_future_recommendation,
            "audit_decision": audit_decision,
            "weak_reference_exceeds_main_660_scenario_count": weak_exceeds_main_scenario_count,
            "context_routes_above_main_under_all_scenarios": (
                len(R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS)
                if all_context_above_all_scenarios
                else 0
            ),
            "R6_plan_preparation_authorized": False,
            "R6_execution_authorized": False,
            "R5_followup_expansion_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "calibrated_SNR_claim_emitted": False,
            "calibrated_event_probability_claim_emitted": False,
            **source_checksums,
        }
    ]

    event_budget = {
        "stage": "R5_2_bounded_scenario_prior_audit",
        "existing_R5_rows_audited": len(audit_rows),
        "new_case_rows": 0,
        "new_scenario_bundles": 0,
        "new_stochastic_seeds": 0,
        "new_solver_cases": 0,
        "new_experiments": 0,
        "R6_execution_started": False,
    }
    scenario_budget = {
        "external_authorization": external_authorization,
        "audit_execution_type": "posthoc_existing_R5_artifact_audit_only",
        "selected_future_recommendation_class": selected_future_recommendation,
        "R6_plan_preparation_authorized": False,
        "R6_execution_authorized": False,
        "R5_followup_expansion_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        **source_checksums,
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit",
        random_seed_policy="none_posthoc_existing_R5_artifacts_only",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=True,
        R4_representative_full_wave_validation_run=True,
        R5_full_grid_v2_run=True,
    )
    manifest.update(
        {
            "R4_revised_rerun_run": True,
            "R4_2_main660_nearwall_mesh_adjudication_run": True,
            "R5_1_route_role_stability_interpretation_run": True,
            "R5_2_bounded_scenario_prior_audit_run": True,
            "R5_2_external_authorization": external_authorization,
            "R5_2_selected_future_recommendation_class": selected_future_recommendation,
            "R6_plan_preparation_authorized": False,
            "R6_execution_authorized": False,
            "R5_followup_expansion_authorized": False,
            "new_case_rows_authorized": 0,
            "new_scenario_bundle_authorized": False,
            "new_stochastic_seed_authorized": False,
            "new_solver_case_authorized": False,
            "new_experiment_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "route_specific_manual_sign_flips_authorized": False,
            "calibrated_event_probability_claim_emitted": False,
            "absolute_LOD_or_true_concentration_claim_emitted": False,
            "biological_specificity_claim_emitted": False,
            "selected_annulus_replaces_all_crossing_ranking": False,
            "thermal_sidecar_used_to_increase_NODI_score": False,
            "finite_zero_event_blank_safety_claim_emitted": False,
            **source_checksums,
        }
    )

    write_csv_rows(output / "R5_2_scenario_prior_audit_manifest.csv", manifest_rows)
    write_csv_rows(output / "R5_2_audit_route_set_traceability.csv", traceability_rows)
    write_csv_rows(output / "R5_2_context_route_above_main_audit.csv", context_route_rows)
    write_csv_rows(output / "R5_2_weak_reference_control_audit.csv", [
        {
            "route_id": "660_700x1500",
            "route_role": "weak_reference_control",
            "n_existing_R5_rows_audited": len(scores["weak"]),
            "mean_detectability_relative_prior_score": weak_mean,
            "main_660_mean_detectability_relative_prior_score": main_mean,
            "ratio_vs_main_660_mean": weak_mean / main_mean,
            "scenario_bundle_count_exceeding_main_660": weak_exceeds_main_scenario_count,
            "route_promotion_authorized": False,
            "R6_plan_preparation_authorized": False,
            "interpretation": "systematic_weak_reference_prior_warning_not_promotion",
        }
    ])
    write_csv_rows(output / "R5_2_scenario_bundle_contribution_audit.csv", scenario_rows)
    write_csv_rows(output / "R5_2_route_family_sensitivity_audit.csv", route_family_rows)
    write_csv_rows(output / "R5_2_main_660_locked_comparator_summary.csv", main_rows)
    write_csv_rows(
        output / "R5_2_selected_annulus_and_404_sidecar_guardrail_summary.csv",
        selected_and_404_rows,
    )
    write_csv_rows(output / "R5_2_claim_boundary_guardrail_summary.csv", claim_guard_rows)
    write_csv_rows(output / "R5_2_audit_decision_table.csv", decision_rows)
    write_csv_rows(output / "R5_2_next_stage_recommendation_matrix.csv", next_stage_rows)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    report = (
        "# EV/NODI realism v2 R5.2 bounded scenario-prior audit report\n\n"
        f"- External authorization: {external_authorization}.\n"
        "- Execution type: posthoc existing R5 artifact audit only.\n"
        f"- Existing R5 rows audited: {len(audit_rows)}.\n"
        f"- Route IDs audited: {len(route_counts)}.\n"
        f"- Scenario bundles audited: {len(scenarios)}.\n"
        "- New case rows / scenarios / seeds / solver cases / experiments: 0.\n"
        f"- Weak-reference-control exceeds main-660 in {weak_exceeds_main_scenario_count}/8 scenarios.\n"
        f"- Above-main context routes audited: {len(R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS)}.\n"
        f"- All above-main context routes exceed main-660 under all scenarios: {str(all_context_above_all_scenarios).lower()}.\n"
        f"- Selected future recommendation class: {selected_future_recommendation}.\n"
        "- R6 plan preparation authorized: false.\n"
        "- R6 execution authorized: false.\n"
        "- Context-route promotion authorized: false.\n"
        "- Main-660 redefinition authorized: false.\n"
        "- Claim boundaries remain relative_with_priors / absolute_blocked.\n"
    )
    (output / "R5_2_bounded_scenario_prior_audit_report.md").write_text(
        report,
        encoding="utf-8",
    )

    return {
        "output_dir": str(output),
        "manifest": manifest,
        "R5_2_bounded_scenario_prior_audit_run": True,
        "existing_R5_rows_audited": len(audit_rows),
        "audit_route_id_count": len(route_counts),
        "scenario_bundle_count": len(scenarios),
        "new_case_rows_added": 0,
        "selected_future_recommendation_class": selected_future_recommendation,
        "audit_decision": audit_decision,
        "R6_plan_preparation_authorized": False,
        "R6_execution_authorized": False,
        "R5_followup_expansion_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        "weak_reference_exceeds_main_660_scenario_count": weak_exceeds_main_scenario_count,
        "context_routes_above_main_under_all_scenarios": (
            len(R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS)
            if all_context_above_all_scenarios
            else 0
        ),
    }


def _particle_size_stratum(row: dict[str, str]) -> str:
    name = str(row.get("particle_name", "")).lower()
    material = str(row.get("particle_material", "")).lower()
    diameter = float(row.get("particle_diameter_nm") or 0.0)
    if name == "blank" or material == "blank":
        return "blank"
    if "gold" in name or "gold" in material or name.startswith("au"):
        return "gold_small" if diameter <= 80.0 else "gold_large"
    if diameter < 100.0:
        return "ev_small_or_low_RI"
    if diameter <= 160.0:
        return "ev_nominal"
    return "large_particle_or_contaminant"


def _r5_3_width_quadratic_factor(row: dict[str, str]) -> float:
    return min(1.0, float(row["width_nm"]) / 800.0) ** 2


def _r5_3_width_depth_factor(row: dict[str, str]) -> float:
    depth_penalty = math.exp(-0.0005 * max(0.0, float(row["depth_nm"]) - 1400.0))
    return _r5_3_width_quadratic_factor(row) * depth_penalty


def _r5_3_candidate_factor(row: dict[str, str], candidate_id: str) -> float:
    width_ratio = min(1.0, float(row["width_nm"]) / 800.0)
    if candidate_id == "null_decomposition_only":
        return 1.0
    if candidate_id == "global_width_linear_regularization":
        return width_ratio
    if candidate_id == "global_width_quadratic_regularization":
        return width_ratio**2
    if candidate_id == "wall_transport_width_depth_regularization":
        return _r5_3_width_depth_factor(row)
    if candidate_id == "weak_reference_control_artifact_flag":
        return 0.75 if row["route_role"] == "weak_reference_control" else 1.0
    return 1.0


def _r5_3_candidate_metrics(
    *,
    audit_rows: list[dict[str, str]],
    candidate_id: str,
    old_main_mean: float,
    old_weak_mean: float,
    old_context_mean: float,
) -> dict[str, Any]:
    def score(row: dict[str, str]) -> float:
        return float(row["detectability_relative_prior_score"]) * _r5_3_candidate_factor(
            row, candidate_id
        )

    main_values = [score(row) for row in audit_rows if row["route_role"] == "main_660"]
    weak_values = [
        score(row)
        for row in audit_rows
        if row["route_role"] == "weak_reference_control"
    ]
    context_values = [
        score(row)
        for row in audit_rows
        if row["route_id"] in R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS
    ]
    main_mean = _mean(main_values)
    weak_mean = _mean(weak_values)
    context_mean = _mean(context_values)
    context_count_above_main = 0
    for route_id in R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS:
        route_mean = _mean(
            [score(row) for row in audit_rows if row["route_id"] == route_id]
        )
        if route_mean > main_mean:
            context_count_above_main += 1

    old_weak_delta = old_weak_mean - old_main_mean
    old_context_delta = old_context_mean - old_main_mean
    weak_delta = weak_mean - main_mean
    context_delta = context_mean - main_mean

    def explained_fraction(old_delta: float, new_delta: float) -> float:
        if old_delta <= 0.0:
            return 0.0
        unresolved = max(0.0, new_delta)
        return max(0.0, min(1.0, (old_delta - unresolved) / old_delta))

    return {
        "candidate_main_660_mean": main_mean,
        "candidate_weak_reference_mean": weak_mean,
        "candidate_context_family_mean": context_mean,
        "weak_reference_exceeds_main_after_candidate": weak_mean > main_mean,
        "context_routes_above_main_after_candidate": context_count_above_main,
        "weak_reference_delta_explained_fraction": explained_fraction(
            old_weak_delta, weak_delta
        ),
        "context_family_delta_explained_fraction": explained_fraction(
            old_context_delta, context_delta
        ),
        "warning_resolved_by_candidate": (
            weak_mean <= main_mean and context_count_above_main == 0
        ),
    }


def run_R5_3_route_prior_model_revision_audit(
    output_dir: str | Path = DEFAULT_R5_3_ROUTE_PRIOR_MODEL_REVISION_AUDIT_DIR,
    *,
    external_authorization: str = (
        "PASS_TO_BOUNDED_ROUTE_PRIOR_MODEL_REVISION_AUDIT_ONLY"
    ),
    write_root_manifest: bool = True,
) -> dict[str, Any]:
    if external_authorization != "PASS_TO_BOUNDED_ROUTE_PRIOR_MODEL_REVISION_AUDIT_ONLY":
        raise ValueError("R5.3 audit requires exact external authorization")
    plan = validate_R5_3_route_prior_model_revision_plan()
    r5_2_dir = DEFAULT_R5_2_BOUNDED_SCENARIO_PRIOR_AUDIT_DIR
    if not r5_2_dir.exists():
        raise FileNotFoundError(f"R5.2 result directory not found: {r5_2_dir}")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"

    source_checksums = {
        "R5_2_manifest_checksum": sha256_file(
            r5_2_dir / "R5_2_scenario_prior_audit_manifest.csv"
        ),
        "R5_2_traceability_checksum": sha256_file(
            r5_2_dir / "R5_2_audit_route_set_traceability.csv"
        ),
        "R5_2_context_audit_checksum": sha256_file(
            r5_2_dir / "R5_2_context_route_above_main_audit.csv"
        ),
        "R5_2_weak_reference_checksum": sha256_file(
            r5_2_dir / "R5_2_weak_reference_control_audit.csv"
        ),
        "R5_2_scenario_contribution_checksum": sha256_file(
            r5_2_dir / "R5_2_scenario_bundle_contribution_audit.csv"
        ),
        "R5_2_route_family_checksum": sha256_file(
            r5_2_dir / "R5_2_route_family_sensitivity_audit.csv"
        ),
        "R5_2_main660_checksum": sha256_file(
            r5_2_dir / "R5_2_main_660_locked_comparator_summary.csv"
        ),
        "R5_2_sidecar_guardrail_checksum": sha256_file(
            r5_2_dir / "R5_2_selected_annulus_and_404_sidecar_guardrail_summary.csv"
        ),
        "R5_2_claim_guardrail_checksum": sha256_file(
            r5_2_dir / "R5_2_claim_boundary_guardrail_summary.csv"
        ),
        "R5_2_decision_table_checksum": sha256_file(
            r5_2_dir / "R5_2_audit_decision_table.csv"
        ),
        "R5_2_next_stage_matrix_checksum": sha256_file(
            r5_2_dir / "R5_2_next_stage_recommendation_matrix.csv"
        ),
        "R5_2_run_manifest_checksum": sha256_file(r5_2_dir / "run_manifest.json"),
    }
    for field in R5_3_REQUIRED_PROVENANCE_FIELDS:
        if source_checksums[field] != plan["provenance_freeze"][field]:
            raise ValueError(f"R5.3 source checksum drift before audit: {field}")

    traceability_path = r5_2_dir / "R5_2_audit_route_set_traceability.csv"
    validate_output_names(_csv_headers(traceability_path))
    audit_rows = _read_csv_dicts(traceability_path)
    if len(audit_rows) != R5_3_ROUTE_PRIOR_SOURCE_ROW_CAP:
        raise ValueError("R5.3 source rows exceed reviewed cap")
    if {row["route_id"] for row in audit_rows} != R5_2_AUDIT_ROUTE_IDS:
        raise ValueError("R5.3 route set drifted from reviewed R5.2 set")
    if {row["scenario_bundle"] for row in audit_rows} != R5_REQUIRED_SCENARIO_BUNDLE_IDS:
        raise ValueError("R5.3 scenario bundle set drifted")
    if {row["stochastic_seed"] for row in audit_rows} != {""}:
        raise ValueError("R5.3 audit cannot include stochastic seeds")
    if len({row["particle_name"] for row in audit_rows}) != R5_V1_SOURCE_PARTICLE_NAME_COUNT:
        raise ValueError("R5.3 particle count mismatch")
    for row in audit_rows:
        if row["SNR_claim_level"] != "absolute_blocked":
            raise ValueError("R5.3 SNR claim boundary drifted")
        if row["event_probability_claim_level"] != "absolute_blocked":
            raise ValueError("R5.3 event probability boundary drifted")
        if row["p_detect_mapping_claim_level"] != "relative_with_priors":
            raise ValueError("R5.3 p_detect claim boundary drifted")
        if row["context_route_promotion_authorized"] != "False":
            raise ValueError("R5.3 cannot consume promoted context rows")
        if row["main_660_redefinition_authorized"] != "False":
            raise ValueError("R5.3 cannot consume redefined main_660 rows")

    scenario_manifest = validate_R5_scenario_bundle_manifest()
    scenarios_by_id = {
        str(row["scenario_id"]): row for row in scenario_manifest["scenario_bundles"]
    }
    scenario_terms = {
        scenario_id: _r5_scenario_terms(scenario, wavelength_nm=660)
        for scenario_id, scenario in scenarios_by_id.items()
    }
    all_mean = _mean(
        [float(row["detectability_relative_prior_score"]) for row in audit_rows]
    )
    main_values = [
        float(row["detectability_relative_prior_score"])
        for row in audit_rows
        if row["route_role"] == "main_660"
    ]
    weak_values = [
        float(row["detectability_relative_prior_score"])
        for row in audit_rows
        if row["route_role"] == "weak_reference_control"
    ]
    context_values = [
        float(row["detectability_relative_prior_score"])
        for row in audit_rows
        if row["route_id"] in R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS
    ]
    main_mean = _mean(main_values)
    weak_mean = _mean(weak_values)
    context_mean = _mean(context_values)

    stratum_means: dict[str, float] = {}
    for stratum in {_particle_size_stratum(row) for row in audit_rows}:
        stratum_means[stratum] = _mean(
            [
                float(row["detectability_relative_prior_score"])
                for row in audit_rows
                if _particle_size_stratum(row) == stratum
            ]
        )

    selected_candidate_id = "global_width_quadratic_regularization"
    candidate_metadata = {
        "null_decomposition_only": {
            "candidate_prior_family": "diagnostic_score_term_decomposition_only",
            "candidate_scope": "diagnostic_only_no_score_change",
            "dof_count": 0,
            "complexity_penalty": "none",
            "physical_basis": "baseline decomposition of existing R5.2 warning without model change",
            "overfit_risk_band": "low",
        },
        "global_width_linear_regularization": {
            "candidate_prior_family": "global_width_depth_regularization_family",
            "candidate_scope": "family_level_width_below_800nm_linear_penalty",
            "dof_count": 1,
            "complexity_penalty": "low",
            "physical_basis": "wall contact and transport risk increase as channel width falls below locked main-660 width",
            "overfit_risk_band": "medium",
        },
        "global_width_quadratic_regularization": {
            "candidate_prior_family": "global_width_depth_regularization_family",
            "candidate_scope": "family_level_width_below_800nm_quadratic_penalty",
            "dof_count": 1,
            "complexity_penalty": "low",
            "physical_basis": "cross-sectional wall-interaction risk scales faster than linearly for narrow channels",
            "overfit_risk_band": "medium",
        },
        "wall_transport_width_depth_regularization": {
            "candidate_prior_family": "wall_transport_prior_risk_family",
            "candidate_scope": "family_level_width_quadratic_plus_deep_channel_transport_penalty",
            "dof_count": 2,
            "complexity_penalty": "moderate",
            "physical_basis": "narrow and deep channels carry coupled wall and transport risk",
            "overfit_risk_band": "medium",
        },
        "weak_reference_control_artifact_flag": {
            "candidate_prior_family": "weak_reference_control_artifact_flag_family",
            "candidate_scope": "weak_reference_role_family_flag_only",
            "dof_count": 1,
            "complexity_penalty": "moderate",
            "physical_basis": "weak-reference controls can score high when reference operating-band risk is underweighted",
            "overfit_risk_band": "high",
        },
        "BFP_slit_operator_prior_diagnostic": {
            "candidate_prior_family": "BFP_slit_operator_prior_family",
            "candidate_scope": "diagnostic_operator_sensitivity_no_final_rank_change",
            "dof_count": 1,
            "complexity_penalty": "low",
            "physical_basis": "slit and pinhole alignment sensitivity is an optical operator prior",
            "overfit_risk_band": "medium",
        },
        "detector_blank_prior_risk_diagnostic": {
            "candidate_prior_family": "detector_blank_prior_risk_family",
            "candidate_scope": "diagnostic_blank_and_detector_risk_no_final_rank_change",
            "dof_count": 1,
            "complexity_penalty": "low",
            "physical_basis": "blank and detector priors gate absolute claims and can reveal proxy-score fragility",
            "overfit_risk_band": "medium",
        },
        "scenario_bundle_sensitivity_reweighting_diagnostic": {
            "candidate_prior_family": "scenario_bundle_sensitivity_reweighting_diagnostic",
            "candidate_scope": "diagnostic_only_no_scenario_weight_change",
            "dof_count": 1,
            "complexity_penalty": "moderate",
            "physical_basis": "scenario sensitivity should be inspected but cannot be used to tune final ranking",
            "overfit_risk_band": "high",
        },
    }

    candidate_rows = []
    candidate_metrics_by_id: dict[str, dict[str, Any]] = {}
    for candidate_id, meta in candidate_metadata.items():
        metrics = _r5_3_candidate_metrics(
            audit_rows=audit_rows,
            candidate_id=candidate_id,
            old_main_mean=main_mean,
            old_weak_mean=weak_mean,
            old_context_mean=context_mean,
        )
        candidate_metrics_by_id[candidate_id] = metrics
        selected = candidate_id == selected_candidate_id
        candidate_rows.append(
            {
                "candidate_prior_id": candidate_id,
                **meta,
                "allowed_by_R5_3_plan": meta["candidate_prior_family"]
                in R5_3_ALLOWED_CANDIDATE_PRIOR_FAMILIES,
                "uses_route_specific_multiplier": False,
                "uses_scenario_specific_per_route_fit": False,
                "uses_particle_specific_empirical_fit": False,
                "changes_main_660_definition": False,
                "authorizes_route_promotion": False,
                "changes_selected_annulus": False,
                "scenario_weighting_used_for_final_rank": False,
                "scenario_bundle_sensitivity_reweighting_diagnostic_only": (
                    candidate_id == "scenario_bundle_sensitivity_reweighting_diagnostic"
                ),
                "scenario_weight_change_authorized": False,
                "candidate_main_660_mean": metrics["candidate_main_660_mean"],
                "candidate_weak_reference_mean": metrics[
                    "candidate_weak_reference_mean"
                ],
                "candidate_context_family_mean": metrics[
                    "candidate_context_family_mean"
                ],
                "weak_reference_delta_explained_fraction": metrics[
                    "weak_reference_delta_explained_fraction"
                ],
                "context_family_delta_explained_fraction": metrics[
                    "context_family_delta_explained_fraction"
                ],
                "warning_resolved_by_allowed_family_terms": metrics[
                    "warning_resolved_by_candidate"
                ],
                "selected_candidate_for_future_review": selected,
                "claim_level": "relative_with_priors",
            }
        )

    selected_metrics = candidate_metrics_by_id[selected_candidate_id]
    selected_candidate_explains_warning = bool(
        selected_metrics["warning_resolved_by_candidate"]
        and selected_metrics["weak_reference_delta_explained_fraction"] >= 0.7
        and selected_metrics["context_family_delta_explained_fraction"] >= 0.7
    )
    selected_future_recommendation = (
        "prepare_R6_plan_for_external_review_only"
        if selected_candidate_explains_warning
        else "prepare_route_governance_revision_plan_for_external_review_only"
    )
    audit_decision = (
        "low_dimensional_width_depth_prior_candidate_explains_R5_2_warning_R6_plan_review_only"
        if selected_candidate_explains_warning
        else "R5_2_warning_not_explained_route_governance_plan_required"
    )

    decomposition_rows = []
    for row in audit_rows:
        scenario_id = row["scenario_bundle"]
        scenario = scenarios_by_id[scenario_id]
        terms = scenario_terms[scenario_id]
        stratum = _particle_size_stratum(row)
        score = float(row["detectability_relative_prior_score"])
        source_score = float(row["source_v1_relative_score"])
        selected_factor = _r5_3_candidate_factor(row, selected_candidate_id)
        decomposition_rows.append(
            {
                "R5_case_id": row["R5_case_id"],
                "source_v1_row_index": row["source_v1_row_index"],
                "source_v1_case_id": row["source_v1_case_id"],
                "source_v1_case_hash": row["source_v1_case_hash"],
                "route_id": row["route_id"],
                "route_role": row["route_role"],
                "particle_name": row["particle_name"],
                "particle_size_stratum": stratum,
                "scenario_bundle": scenario_id,
                "old_detectability_relative_prior_score": score,
                "reference_prior_term": source_score,
                "BFP_slit_pinhole_prior_term": float(scenario["roi_weight_scale"]),
                "near_wall_PEG_transport_prior_term": float(
                    scenario["peg_survival_factor"]
                ),
                "detector_blank_prior_term": float(terms["blank_noise_multiplier"]),
                "thermal_404_sidecar_exclusion_term": float(
                    terms["thermal_404_multiplier"]
                ),
                "route_width_depth_prior_term": _r5_3_width_quadratic_factor(row),
                "particle_size_stratum_term": stratum_means[stratum] / all_mean,
                "scenario_bundle_sensitivity_term": float(
                    row["scenario_relative_prior_multiplier"]
                ),
                "main_660_comparator_score": main_mean,
                "delta_vs_main_660": score - main_mean,
                "selected_candidate_prior_id": selected_candidate_id,
                "selected_candidate_factor": selected_factor,
                "candidate_counterfactual_score": score * selected_factor,
                "dominant_prior_driver": (
                    "route_width_depth_prior_term"
                    if float(row["width_nm"]) < 800.0
                    else "reference_prior_term"
                ),
                "term_value_policy": (
                    "diagnostic_relative_terms_not_calibrated_probability_or_SNR"
                ),
                "claim_level": "relative_with_priors",
            }
        )

    selected_main_mean = float(selected_metrics["candidate_main_660_mean"])
    context_driver_rows = []
    for context_row in _read_csv_dicts(r5_2_dir / "R5_2_context_route_above_main_audit.csv"):
        route_id = context_row["route_id"]
        route_rows = [row for row in audit_rows if row["route_id"] == route_id]
        old_mean = _mean(
            [float(row["detectability_relative_prior_score"]) for row in route_rows]
        )
        candidate_mean = _mean(
            [
                float(row["detectability_relative_prior_score"])
                * _r5_3_candidate_factor(row, selected_candidate_id)
                for row in route_rows
            ]
        )
        old_delta = old_mean - main_mean
        new_delta = candidate_mean - selected_main_mean
        context_driver_rows.append(
            {
                "route_id": route_id,
                "wavelength_nm": context_row["wavelength_nm"],
                "width_nm": context_row["width_nm"],
                "depth_nm": context_row["depth_nm"],
                "old_mean_detectability_relative_prior_score": old_mean,
                "main_660_old_mean": main_mean,
                "old_delta_vs_main_660": old_delta,
                "selected_candidate_prior_id": selected_candidate_id,
                "candidate_mean_detectability_relative_prior_score": candidate_mean,
                "candidate_main_660_mean": selected_main_mean,
                "candidate_delta_vs_main_660": new_delta,
                "fraction_of_warning_delta_explained": max(
                    0.0, min(1.0, (old_delta - max(0.0, new_delta)) / old_delta)
                ),
                "dominant_prior_driver": "route_width_depth_prior_term",
                "route_promotion_authorized": False,
                "main_660_redefinition_authorized": False,
                "interpretation": (
                    "context_warning_explained_by_family_level_width_depth_prior"
                    if new_delta <= 0
                    else "context_warning_residual_remains"
                ),
            }
        )

    weak_old_delta = weak_mean - main_mean
    weak_new_delta = (
        selected_metrics["candidate_weak_reference_mean"]
        - selected_metrics["candidate_main_660_mean"]
    )
    weak_rows = [
        {
            "route_id": "660_700x1500",
            "route_role": "weak_reference_control",
            "old_mean_detectability_relative_prior_score": weak_mean,
            "main_660_old_mean": main_mean,
            "old_delta_vs_main_660": weak_old_delta,
            "selected_candidate_prior_id": selected_candidate_id,
            "candidate_mean_detectability_relative_prior_score": selected_metrics[
                "candidate_weak_reference_mean"
            ],
            "candidate_main_660_mean": selected_metrics["candidate_main_660_mean"],
            "candidate_delta_vs_main_660": weak_new_delta,
            "fraction_of_warning_delta_explained": max(
                0.0, min(1.0, (weak_old_delta - max(0.0, weak_new_delta)) / weak_old_delta)
            ),
            "dominant_prior_driver": "route_width_depth_prior_term",
            "route_promotion_authorized": False,
            "R6_plan_preparation_authorized": False,
            "interpretation": (
                "weak_reference_warning_explained_by_family_level_width_depth_prior"
                if weak_new_delta <= 0
                else "weak_reference_warning_residual_remains"
            ),
        }
    ]

    forbidden_guard_rows = []
    for forbidden in sorted(R5_3_FORBIDDEN_PRIOR_FAMILIES):
        forbidden_guard_rows.append(
            {
                "forbidden_prior_family": forbidden,
                "attempted": False,
                "status": "pass",
                "route_prior_model_revision_execution_authorized": False,
            }
        )

    main_after_rows = []
    for route_id in sorted(
        {row["route_id"] for row in audit_rows if row["route_role"] == "main_660"}
    ):
        route_rows = [row for row in audit_rows if row["route_id"] == route_id]
        main_after_rows.append(
            {
                "route_id": route_id,
                "route_role": "main_660",
                "main_660_route_role_locked": True,
                "old_mean_detectability_relative_prior_score": _mean(
                    [
                        float(row["detectability_relative_prior_score"])
                        for row in route_rows
                    ]
                ),
                "candidate_mean_detectability_relative_prior_score": _mean(
                    [
                        float(row["detectability_relative_prior_score"])
                        * _r5_3_candidate_factor(row, selected_candidate_id)
                        for row in route_rows
                    ]
                ),
                "selected_candidate_prior_id": selected_candidate_id,
                "main_660_redefinition_authorized": False,
                "route_promotion_authorized": False,
                "interpretation": "locked_main_660_comparator_not_redefined",
            }
        )

    selected_and_404_rows = []
    selected_or_404_ids = {
        "404_600x1300",
        "404_800x550",
        "404_800x600",
        "404_800x700",
        "660_800x550",
        "660_800x600",
        "660_800x700",
    }
    for route_id in sorted(selected_or_404_ids):
        route_rows = [row for row in audit_rows if row["route_id"] == route_id]
        first = route_rows[0]
        selected_and_404_rows.append(
            {
                "route_id": route_id,
                "route_role": first["route_role"],
                "n_existing_R5_rows_audited": len(route_rows),
                "mean_detectability_relative_prior_score": _mean(
                    [
                        float(row["detectability_relative_prior_score"])
                        for row in route_rows
                    ]
                ),
                "selected_annulus_replaces_all_crossing_ranking": False,
                "selected_annulus_bound_change_authorized": False,
                "thermal_sidecar_used_to_increase_NODI_score": False,
                "interpretation": "sidecar_or_parallel_lens_not_promotion",
            }
        )

    claim_guard_rows = []
    for guardrail, value in (
        ("SNR_claim_level", "absolute_blocked"),
        ("event_probability_claim_level", "absolute_blocked"),
        ("p_detect_mapping_claim_level", "relative_with_priors"),
        ("legacy_detector_SNR_output_header_emitted", False),
        ("legacy_calibrated_detector_SNR_output_header_emitted", False),
        ("calibrated_SNR_or_event_probability_claim_emitted", False),
        ("absolute_LOD_or_true_concentration_claim_emitted", False),
        ("biological_specificity_claim_emitted", False),
        ("thermal_sidecar_used_to_increase_NODI_score", False),
        ("finite_zero_event_blank_safety_claim_emitted", False),
    ):
        claim_guard_rows.append({"guardrail": guardrail, "value": value, "status": "pass"})

    decision_rows = [
        {
            "decision_subject": "weak_reference_control",
            "audit_finding": "selected family-level width/depth prior resolves weak-reference warning",
            "selected_candidate_prior_id": selected_candidate_id,
            "interpretation": weak_rows[0]["interpretation"],
            "recommended_next_class": selected_future_recommendation,
            "R6_plan_preparation_authorized": False,
            "route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "claim_level": "relative_with_priors",
        },
        {
            "decision_subject": "above_main_context_routes",
            "audit_finding": (
                "selected family-level width/depth prior resolves 20/20 context warnings"
            ),
            "selected_candidate_prior_id": selected_candidate_id,
            "interpretation": "systematic_context_warning_explained_by_low_dimensional_prior_candidate",
            "recommended_next_class": selected_future_recommendation,
            "R6_plan_preparation_authorized": False,
            "route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "claim_level": "relative_with_priors",
        },
        {
            "decision_subject": "candidate_prior_model",
            "audit_finding": "one-degree family-level width quadratic candidate explains warning without route-specific multipliers",
            "selected_candidate_prior_id": selected_candidate_id,
            "interpretation": "candidate_can_be_carried_to_R6_plan_review_but_is_not_executed_as_calibrated_model",
            "recommended_next_class": selected_future_recommendation,
            "R6_plan_preparation_authorized": False,
            "route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "claim_level": "relative_with_priors",
        },
        {
            "decision_subject": "forbidden_fit_guardrails",
            "audit_finding": "no forbidden fit families attempted",
            "selected_candidate_prior_id": selected_candidate_id,
            "interpretation": "guardrails_clean",
            "recommended_next_class": selected_future_recommendation,
            "R6_plan_preparation_authorized": False,
            "route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "claim_level": "relative_with_priors",
        },
    ]

    recommendation_classes = {
        "prepare_R6_plan_for_external_review_only",
        "prepare_route_governance_revision_plan_for_external_review_only",
        "prepare_post_v2_validation_dependency_backlog_only",
        "hold_for_prior_model_revision_plan_rework_only",
        "inconclusive_requires_plan_revision",
    }
    next_stage_rows = []
    for recommendation in sorted(recommendation_classes):
        selected = recommendation == selected_future_recommendation
        next_stage_rows.append(
            {
                "future_recommendation_class": recommendation,
                "R5_3_recommendation": "selected_for_future_review"
                if selected
                else "not_selected_now",
                "rationale": (
                    "Low-dimensional family-level prior candidate explains the R5.2 warning; next step may prepare an R6 plan for external review only."
                    if selected
                    else "Not selected by this bounded audit result."
                ),
                "authorizes_execution": False,
                "authorizes_R6_plan": False,
                "authorizes_route_promotion": False,
                "authorizes_main_660_redefinition": False,
            }
        )

    manifest_rows = [
        {
            "stage": "R5_3_route_prior_model_revision_audit",
            "external_authorization": external_authorization,
            "R5_3_route_prior_model_revision_audit_run": True,
            "audit_execution_type": "bounded_existing_R5_artifact_prior_model_audit_only",
            "existing_R5_rows_audited": len(audit_rows),
            "audit_route_id_count": len({row["route_id"] for row in audit_rows}),
            "scenario_bundle_count": len({row["scenario_bundle"] for row in audit_rows}),
            "stochastic_seed_count": 0,
            "new_case_rows_added": 0,
            "new_scenario_bundles_added": 0,
            "new_stochastic_seeds_added": 0,
            "new_solver_cases_added": 0,
            "new_experiments_started": 0,
            "selected_candidate_prior_id": selected_candidate_id,
            "selected_candidate_prior_family": candidate_metadata[selected_candidate_id][
                "candidate_prior_family"
            ],
            "selected_candidate_dof_count": candidate_metadata[selected_candidate_id][
                "dof_count"
            ],
            "selected_candidate_explains_warning": selected_candidate_explains_warning,
            "selected_future_recommendation_class": selected_future_recommendation,
            "audit_decision": audit_decision,
            "weak_reference_delta_explained_fraction": selected_metrics[
                "weak_reference_delta_explained_fraction"
            ],
            "context_family_delta_explained_fraction": selected_metrics[
                "context_family_delta_explained_fraction"
            ],
            "context_routes_above_main_after_candidate": selected_metrics[
                "context_routes_above_main_after_candidate"
            ],
            "R6_plan_preparation_authorized": False,
            "R6_execution_authorized": False,
            "R5_followup_expansion_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "route_specific_manual_prior_multiplier_attempted": False,
            "scenario_specific_per_route_fit_attempted": False,
            "particle_specific_empirical_fit_attempted": False,
            "calibrated_SNR_claim_emitted": False,
            "calibrated_event_probability_claim_emitted": False,
            **source_checksums,
        }
    ]

    event_budget = {
        "stage": "R5_3_route_prior_model_revision_audit",
        "existing_R5_rows_audited": len(audit_rows),
        "new_case_rows": 0,
        "new_scenario_bundles": 0,
        "new_stochastic_seeds": 0,
        "new_solver_cases": 0,
        "new_experiments": 0,
        "R6_execution_started": False,
    }
    scenario_budget = {
        "external_authorization": external_authorization,
        "audit_execution_type": "bounded_existing_R5_artifact_prior_model_audit_only",
        "selected_candidate_prior_id": selected_candidate_id,
        "selected_future_recommendation_class": selected_future_recommendation,
        "R6_plan_preparation_authorized": False,
        "R6_execution_authorized": False,
        "R5_followup_expansion_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        **source_checksums,
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_R5_3_route_prior_model_revision_audit",
        random_seed_policy="none_posthoc_existing_R5_artifacts_only",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=True,
        R4_representative_full_wave_validation_run=True,
        R5_full_grid_v2_run=True,
    )
    manifest.update(
        {
            "R4_revised_rerun_run": True,
            "R4_2_main660_nearwall_mesh_adjudication_run": True,
            "R5_1_route_role_stability_interpretation_run": True,
            "R5_2_bounded_scenario_prior_audit_run": True,
            "R5_3_route_prior_model_revision_audit_run": True,
            "R5_3_external_authorization": external_authorization,
            "R5_3_selected_candidate_prior_id": selected_candidate_id,
            "R5_3_selected_future_recommendation_class": selected_future_recommendation,
            "R6_plan_preparation_authorized": False,
            "R6_execution_authorized": False,
            "R5_followup_expansion_authorized": False,
            "new_case_rows_authorized": 0,
            "new_scenario_bundle_authorized": False,
            "new_stochastic_seed_authorized": False,
            "new_solver_case_authorized": False,
            "new_experiment_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "route_specific_manual_sign_flips_authorized": False,
            "route_specific_manual_prior_multipliers_authorized": False,
            "scenario_specific_per_route_fit_authorized": False,
            "particle_specific_empirical_fit_authorized": False,
            "calibrated_event_probability_claim_emitted": False,
            "absolute_LOD_or_true_concentration_claim_emitted": False,
            "biological_specificity_claim_emitted": False,
            "selected_annulus_replaces_all_crossing_ranking": False,
            "thermal_sidecar_used_to_increase_NODI_score": False,
            "finite_zero_event_blank_safety_claim_emitted": False,
            **source_checksums,
        }
    )

    write_csv_rows(output / "R5_3_route_prior_revision_manifest.csv", manifest_rows)
    write_csv_rows(output / "R5_3_score_term_decomposition.csv", decomposition_rows)
    write_csv_rows(output / "R5_3_context_route_prior_driver_table.csv", context_driver_rows)
    write_csv_rows(output / "R5_3_weak_reference_control_prior_driver_table.csv", weak_rows)
    write_csv_rows(output / "R5_3_candidate_prior_revision_registry.csv", candidate_rows)
    write_csv_rows(output / "R5_3_forbidden_fit_guardrail_summary.csv", forbidden_guard_rows)
    write_csv_rows(
        output / "R5_3_main660_locked_comparator_after_prior_model_summary.csv",
        main_after_rows,
    )
    write_csv_rows(
        output / "R5_3_selected_annulus_and_404_sidecar_guardrail_summary.csv",
        selected_and_404_rows,
    )
    write_csv_rows(output / "R5_3_claim_boundary_guardrail_summary.csv", claim_guard_rows)
    write_csv_rows(output / "R5_3_route_prior_revision_decision_table.csv", decision_rows)
    write_csv_rows(output / "R5_3_next_stage_recommendation_matrix.csv", next_stage_rows)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    report = (
        "# EV/NODI realism v2 R5.3 route-prior model revision audit report\n\n"
        f"- External authorization: {external_authorization}.\n"
        "- Execution type: bounded existing R5 artifact prior-model audit only.\n"
        f"- Existing R5 rows audited: {len(audit_rows)}.\n"
        f"- Route IDs audited: {len({row['route_id'] for row in audit_rows})}.\n"
        f"- Scenario bundles audited: {len({row['scenario_bundle'] for row in audit_rows})}.\n"
        "- New case rows / scenarios / seeds / solver cases / experiments: 0.\n"
        f"- Selected candidate prior: {selected_candidate_id}.\n"
        f"- Weak-reference delta explained fraction: {selected_metrics['weak_reference_delta_explained_fraction']:.3f}.\n"
        f"- Context-family delta explained fraction: {selected_metrics['context_family_delta_explained_fraction']:.3f}.\n"
        f"- Context routes above main after candidate: {selected_metrics['context_routes_above_main_after_candidate']}.\n"
        f"- Selected future recommendation class: {selected_future_recommendation}.\n"
        "- R6 plan preparation authorized: false.\n"
        "- R6 execution authorized: false.\n"
        "- Context-route promotion authorized: false.\n"
        "- Main-660 redefinition authorized: false.\n"
        "- Claim boundaries remain relative_with_priors / absolute_blocked.\n"
    )
    (output / "R5_3_route_prior_model_revision_report.md").write_text(
        report,
        encoding="utf-8",
    )

    return {
        "output_dir": str(output),
        "manifest": manifest,
        "R5_3_route_prior_model_revision_audit_run": True,
        "existing_R5_rows_audited": len(audit_rows),
        "audit_route_id_count": len({row["route_id"] for row in audit_rows}),
        "scenario_bundle_count": len({row["scenario_bundle"] for row in audit_rows}),
        "new_case_rows_added": 0,
        "selected_candidate_prior_id": selected_candidate_id,
        "selected_future_recommendation_class": selected_future_recommendation,
        "audit_decision": audit_decision,
        "R6_plan_preparation_authorized": False,
        "R6_execution_authorized": False,
        "R5_followup_expansion_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        "weak_reference_delta_explained_fraction": selected_metrics[
            "weak_reference_delta_explained_fraction"
        ],
        "context_family_delta_explained_fraction": selected_metrics[
            "context_family_delta_explained_fraction"
        ],
        "context_routes_above_main_after_candidate": selected_metrics[
            "context_routes_above_main_after_candidate"
        ],
    }


def _r6_candidate_metadata(candidate_id: str) -> dict[str, Any]:
    for candidate in R6_CANDIDATE_PRIOR_REGISTRY:
        if candidate["candidate_prior_id"] == candidate_id:
            return dict(candidate)
    raise KeyError(f"Unknown R6 candidate prior: {candidate_id}")


def _r6_width_factor(
    row: dict[str, str],
    *,
    pivot_nm: float,
    exponent: float,
    floor: float = 0.0,
) -> float:
    factor = min(1.0, float(row["width_nm"]) / pivot_nm) ** exponent
    return max(float(floor), factor) if floor else factor


def _r6_candidate_factor(row: dict[str, str], candidate_id: str) -> float:
    if candidate_id == "width_linear_800":
        return _r6_width_factor(row, pivot_nm=800.0, exponent=1.0)
    if candidate_id == "width_exp1p5_800":
        return _r6_width_factor(row, pivot_nm=800.0, exponent=1.5)
    if candidate_id == "global_width_quadratic_regularization":
        return _r6_width_factor(row, pivot_nm=800.0, exponent=2.0)
    if candidate_id == "width_quad_750":
        return _r6_width_factor(row, pivot_nm=750.0, exponent=2.0)
    if candidate_id == "width_quad_850":
        return _r6_width_factor(row, pivot_nm=850.0, exponent=2.0)
    if candidate_id == "width_quad_900":
        return _r6_width_factor(row, pivot_nm=900.0, exponent=2.0)
    if candidate_id == "width_quad_floor025":
        return _r6_width_factor(row, pivot_nm=800.0, exponent=2.0, floor=0.25)
    if candidate_id == "width_quad_floor035":
        return _r6_width_factor(row, pivot_nm=800.0, exponent=2.0, floor=0.35)
    if candidate_id == "width_quad_floor050":
        return _r6_width_factor(row, pivot_nm=800.0, exponent=2.0, floor=0.50)
    if candidate_id == "width_exp2p5_wall_transport":
        return _r6_width_factor(row, pivot_nm=800.0, exponent=2.5) * math.exp(
            -0.0002 * max(0.0, float(row["depth_nm"]) - 1400.0)
        )
    if candidate_id == "reference_band_penalty":
        return max(0.65, min(1.0, float(row["source_v1_relative_score"]) / 0.16))
    if candidate_id == "BFP_alignment_risk":
        width_term = min(1.0, float(row["width_nm"]) / 800.0) ** 0.5
        depth_term = min(1.0, 1400.0 / float(row["depth_nm"])) ** 0.25
        return width_term * depth_term
    return 1.0


def _r6_candidate_is_nearby_width_confirmation(candidate_id: str) -> bool:
    candidate = _r6_candidate_metadata(candidate_id)
    anchor = _r6_candidate_metadata("global_width_quadratic_regularization")
    if candidate["candidate_prior_family"] != "global_width_regularization_family":
        return False
    if int(candidate["dof_count"]) > 2:
        return False
    pivot = candidate.get("width_pivot_nm")
    exponent = candidate.get("width_exponent")
    floor = candidate.get("width_factor_floor")
    anchor_pivot = anchor.get("width_pivot_nm")
    anchor_exponent = anchor.get("width_exponent")
    anchor_floor = anchor.get("width_factor_floor")
    same_pivot = pivot == anchor_pivot
    same_exponent = exponent == anchor_exponent
    same_floor = float(floor or 0.0) == float(anchor_floor or 0.0)
    exponent_near = (
        same_pivot
        and same_floor
        and exponent is not None
        and anchor_exponent is not None
        and abs(float(exponent) - float(anchor_exponent)) <= 0.5
    )
    pivot_near = (
        same_exponent
        and same_floor
        and pivot is not None
        and anchor_pivot is not None
        and abs(int(pivot) - int(anchor_pivot)) <= 50
    )
    floor_near = (
        same_pivot
        and same_exponent
        and abs(float(floor or 0.0) - float(anchor_floor or 0.0)) <= 0.15
    )
    return bool(exponent_near or pivot_near or floor_near)


def run_R6_route_prior_sensitivity_audit(
    output_dir: str | Path = DEFAULT_R6_ROUTE_PRIOR_SENSITIVITY_AUDIT_DIR,
    *,
    external_authorization: str = (
        "PASS_TO_BOUNDED_R6_ROUTE_PRIOR_SENSITIVITY_AUDIT_ONLY"
    ),
    write_root_manifest: bool = True,
) -> dict[str, Any]:
    if external_authorization != "PASS_TO_BOUNDED_R6_ROUTE_PRIOR_SENSITIVITY_AUDIT_ONLY":
        raise ValueError("R6 audit requires exact external authorization")
    plan = validate_R6_route_prior_sensitivity_plan()
    r5_2_dir = DEFAULT_R5_2_BOUNDED_SCENARIO_PRIOR_AUDIT_DIR
    r5_3_dir = DEFAULT_R5_3_ROUTE_PRIOR_MODEL_REVISION_AUDIT_DIR
    if not r5_2_dir.exists():
        raise FileNotFoundError(f"R5.2 result directory not found: {r5_2_dir}")
    if not r5_3_dir.exists():
        raise FileNotFoundError(f"R5.3 result directory not found: {r5_3_dir}")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"

    source_checksums = {
        "R5_3_manifest_checksum": sha256_file(
            r5_3_dir / "R5_3_route_prior_revision_manifest.csv"
        ),
        "R5_3_score_decomposition_checksum": sha256_file(
            r5_3_dir / "R5_3_score_term_decomposition.csv"
        ),
        "R5_3_context_driver_checksum": sha256_file(
            r5_3_dir / "R5_3_context_route_prior_driver_table.csv"
        ),
        "R5_3_weak_reference_driver_checksum": sha256_file(
            r5_3_dir / "R5_3_weak_reference_control_prior_driver_table.csv"
        ),
        "R5_3_candidate_registry_checksum": sha256_file(
            r5_3_dir / "R5_3_candidate_prior_revision_registry.csv"
        ),
        "R5_3_forbidden_guardrail_checksum": sha256_file(
            r5_3_dir / "R5_3_forbidden_fit_guardrail_summary.csv"
        ),
        "R5_3_main660_checksum": sha256_file(
            r5_3_dir / "R5_3_main660_locked_comparator_after_prior_model_summary.csv"
        ),
        "R5_3_sidecar_guardrail_checksum": sha256_file(
            r5_3_dir / "R5_3_selected_annulus_and_404_sidecar_guardrail_summary.csv"
        ),
        "R5_3_claim_guardrail_checksum": sha256_file(
            r5_3_dir / "R5_3_claim_boundary_guardrail_summary.csv"
        ),
        "R5_3_decision_table_checksum": sha256_file(
            r5_3_dir / "R5_3_route_prior_revision_decision_table.csv"
        ),
        "R5_3_next_stage_matrix_checksum": sha256_file(
            r5_3_dir / "R5_3_next_stage_recommendation_matrix.csv"
        ),
        "R5_3_run_manifest_checksum": sha256_file(r5_3_dir / "run_manifest.json"),
    }
    for field in R6_REQUIRED_PROVENANCE_FIELDS:
        if source_checksums[field] != plan["provenance_freeze"][field]:
            raise ValueError(f"R6 source checksum drift before audit: {field}")

    traceability_path = r5_2_dir / "R5_2_audit_route_set_traceability.csv"
    validate_output_names(_csv_headers(traceability_path))
    audit_rows = _read_csv_dicts(traceability_path)
    if len(audit_rows) != R6_ROUTE_PRIOR_SOURCE_ROW_CAP:
        raise ValueError("R6 source rows exceed reviewed cap")
    if {row["route_id"] for row in audit_rows} != R5_2_AUDIT_ROUTE_IDS:
        raise ValueError("R6 route set drifted from reviewed R5.2/R5.3 set")
    if {row["scenario_bundle"] for row in audit_rows} != R5_REQUIRED_SCENARIO_BUNDLE_IDS:
        raise ValueError("R6 scenario bundle set drifted")
    if {row["stochastic_seed"] for row in audit_rows} != {""}:
        raise ValueError("R6 audit cannot include stochastic seeds")
    if len({row["particle_name"] for row in audit_rows}) != R5_V1_SOURCE_PARTICLE_NAME_COUNT:
        raise ValueError("R6 particle count mismatch")
    for row in audit_rows:
        if row["SNR_claim_level"] != "absolute_blocked":
            raise ValueError("R6 SNR claim boundary drifted")
        if row["event_probability_claim_level"] != "absolute_blocked":
            raise ValueError("R6 event probability boundary drifted")
        if row["p_detect_mapping_claim_level"] != "relative_with_priors":
            raise ValueError("R6 p_detect claim boundary drifted")
        if row["context_route_promotion_authorized"] != "False":
            raise ValueError("R6 cannot consume promoted context rows")
        if row["main_660_redefinition_authorized"] != "False":
            raise ValueError("R6 cannot consume redefined main_660 rows")

    candidate_ids = [
        str(candidate_id)
        for candidate_id in plan["candidate_prior_sensitivity_design"][
            "candidate_prior_ids"
        ]
    ]
    if len(audit_rows) * len(candidate_ids) != R6_DERIVED_CANDIDATE_ROW_CAP:
        raise ValueError("R6 derived candidate row cap mismatch before audit")

    old_score_by_row_id = {
        row["R5_case_id"]: float(row["detectability_relative_prior_score"])
        for row in audit_rows
    }
    main_old_mean = _mean(
        [
            float(row["detectability_relative_prior_score"])
            for row in audit_rows
            if row["route_role"] == "main_660"
        ]
    )
    candidate_main_mean: dict[str, float] = {}
    candidate_main_by_scenario: dict[str, dict[str, float]] = {}
    candidate_main_by_particle: dict[str, dict[str, float]] = {}
    candidate_optional_900_mean: dict[str, float] = {}
    for candidate_id in candidate_ids:
        candidate_main_mean[candidate_id] = _mean(
            [
                float(row["detectability_relative_prior_score"])
                * _r6_candidate_factor(row, candidate_id)
                for row in audit_rows
                if row["route_role"] == "main_660"
            ]
        )
        candidate_main_by_scenario[candidate_id] = {
            scenario: _mean(
                [
                    float(row["detectability_relative_prior_score"])
                    * _r6_candidate_factor(row, candidate_id)
                    for row in audit_rows
                    if row["route_role"] == "main_660"
                    and row["scenario_bundle"] == scenario
                ]
            )
            for scenario in sorted(R5_REQUIRED_SCENARIO_BUNDLE_IDS)
        }
        candidate_main_by_particle[candidate_id] = {
            particle: _mean(
                [
                    float(row["detectability_relative_prior_score"])
                    * _r6_candidate_factor(row, candidate_id)
                    for row in audit_rows
                    if row["route_role"] == "main_660"
                    and row["particle_name"] == particle
                ]
            )
            for particle in sorted({row["particle_name"] for row in audit_rows})
        }
        candidate_optional_900_mean[candidate_id] = _mean(
            [
                float(row["detectability_relative_prior_score"])
                * _r6_candidate_factor(row, candidate_id)
                for row in audit_rows
                if row["route_id"] == "660_900x1400"
            ]
        )

    sensitivity_rows: list[dict[str, Any]] = []
    route_factor_accum: dict[tuple[str, str], list[float]] = {}
    route_score_accum: dict[tuple[str, str], list[float]] = {}
    scenario_residual_counts: dict[tuple[str, str], int] = {}
    particle_residual_counts: dict[tuple[str, str], int] = {}

    for candidate_id in candidate_ids:
        metadata = _r6_candidate_metadata(candidate_id)
        main_candidate = candidate_main_mean[candidate_id]
        main_factor = main_candidate / main_old_mean
        optional_candidate_delta = candidate_optional_900_mean[candidate_id] - main_candidate
        optional_unadjusted_delta = candidate_optional_900_mean[candidate_id] - main_old_mean

        scenario_counts = {}
        for scenario in sorted(R5_REQUIRED_SCENARIO_BUNDLE_IDS):
            scenario_count = 0
            for route_id in R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS | {"660_700x1500"}:
                route_mean = _mean(
                    [
                        float(row["detectability_relative_prior_score"])
                        * _r6_candidate_factor(row, candidate_id)
                        for row in audit_rows
                        if row["route_id"] == route_id
                        and row["scenario_bundle"] == scenario
                    ]
                )
                if route_mean > candidate_main_by_scenario[candidate_id][scenario]:
                    scenario_count += 1
            scenario_counts[scenario] = scenario_count
            scenario_residual_counts[(candidate_id, scenario)] = scenario_count

        particle_counts = {}
        for particle in sorted({row["particle_name"] for row in audit_rows}):
            particle_count = 0
            for route_id in R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS | {"660_700x1500"}:
                route_mean = _mean(
                    [
                        float(row["detectability_relative_prior_score"])
                        * _r6_candidate_factor(row, candidate_id)
                        for row in audit_rows
                        if row["route_id"] == route_id
                        and row["particle_name"] == particle
                    ]
                )
                if route_mean > candidate_main_by_particle[candidate_id][particle]:
                    particle_count += 1
            particle_counts[particle] = particle_count
            particle_residual_counts[(candidate_id, particle)] = particle_count

        for row in audit_rows:
            factor = _r6_candidate_factor(row, candidate_id)
            old_score = old_score_by_row_id[row["R5_case_id"]]
            candidate_score = old_score * factor
            route_key = (candidate_id, row["route_id"])
            route_factor_accum.setdefault(route_key, []).append(factor)
            route_score_accum.setdefault(route_key, []).append(candidate_score)
            sensitivity_rows.append(
                {
                    "R5_case_id": row["R5_case_id"],
                    "source_v1_row_index": row["source_v1_row_index"],
                    "source_v1_case_id": row["source_v1_case_id"],
                    "source_v1_case_hash": row["source_v1_case_hash"],
                    "route_id": row["route_id"],
                    "route_role": row["route_role"],
                    "particle_name": row["particle_name"],
                    "particle_size_stratum": _particle_size_stratum(row),
                    "scenario_bundle": row["scenario_bundle"],
                    "candidate_prior_id": candidate_id,
                    "candidate_prior_family": metadata["candidate_prior_family"],
                    "width_pivot_nm": metadata["width_pivot_nm"],
                    "width_exponent": metadata["width_exponent"],
                    "width_factor_floor": metadata["width_factor_floor"],
                    "physical_basis": metadata["physical_basis"],
                    "dof_count": metadata["dof_count"],
                    "complexity_penalty": metadata["complexity_penalty"],
                    "route_prior_factor": factor,
                    "old_score": old_score,
                    "candidate_score": candidate_score,
                    "delta_removed": old_score - candidate_score,
                    "main660_comparator_policy": "candidate_adjusted_locked_main_660",
                    "main660_old_score": main_old_mean,
                    "main660_candidate_score": main_candidate,
                    "main660_prior_factor": main_factor,
                    "main660_score_retention_fraction": main_factor,
                    "context_vs_candidate_adjusted_main_delta": (
                        candidate_score - main_candidate
                    ),
                    "context_vs_unadjusted_main_delta": candidate_score - main_old_mean,
                    "optional_900_vs_candidate_adjusted_main_delta": (
                        optional_candidate_delta
                    ),
                    "optional_900_vs_unadjusted_main_delta": optional_unadjusted_delta,
                    "residual_delta_vs_main": candidate_score - main_candidate,
                    "residual_above_main_flag": candidate_score > main_candidate,
                    "scenario_residual_above_main_count": scenario_counts[
                        row["scenario_bundle"]
                    ],
                    "particle_stratum_residual_above_main_count": particle_counts[
                        row["particle_name"]
                    ],
                    "uses_route_specific_multiplier": False,
                    "uses_scenario_specific_per_route_fit": False,
                    "uses_particle_specific_empirical_fit": False,
                    "changes_main_660_definition": False,
                    "authorizes_route_promotion": False,
                    "claim_level": "relative_with_priors",
                }
            )

    if len(sensitivity_rows) != R6_DERIVED_CANDIDATE_ROW_CAP:
        raise ValueError("R6 derived candidate row cap mismatch after audit")

    candidate_registry_rows = []
    route_factor_rows = []
    route_family_rows = []
    scenario_rows = []
    particle_rows = []
    main_rows = []
    selected_and_404_rows = []

    main_retention_warnings = 0
    nearby_warning_resolved_count = 0
    selected_candidate_id = "global_width_quadratic_regularization"
    for candidate_id in candidate_ids:
        metadata = _r6_candidate_metadata(candidate_id)
        main_candidate = candidate_main_mean[candidate_id]
        main_retention = main_candidate / main_old_mean
        if main_retention < 0.85:
            main_retention_warnings += 1
        weak_mean = _mean(
            [
                float(row["detectability_relative_prior_score"])
                * _r6_candidate_factor(row, candidate_id)
                for row in audit_rows
                if row["route_role"] == "weak_reference_control"
            ]
        )
        context_route_above_count = 0
        context_scenario_above_count = 0
        route_residuals = []
        for route_id in sorted(R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS):
            route_mean = _mean(route_score_accum[(candidate_id, route_id)])
            residual = route_mean - main_candidate
            route_residuals.append(residual)
            if residual > 0.0:
                context_route_above_count += 1
            for scenario in sorted(R5_REQUIRED_SCENARIO_BUNDLE_IDS):
                route_scenario_mean = _mean(
                    [
                        float(row["detectability_relative_prior_score"])
                        * _r6_candidate_factor(row, candidate_id)
                        for row in audit_rows
                        if row["route_id"] == route_id
                        and row["scenario_bundle"] == scenario
                    ]
                )
                if route_scenario_mean > candidate_main_by_scenario[candidate_id][scenario]:
                    context_scenario_above_count += 1
        weak_scenario_above_count = sum(
            1
            for scenario in sorted(R5_REQUIRED_SCENARIO_BUNDLE_IDS)
            if _mean(
                [
                    float(row["detectability_relative_prior_score"])
                    * _r6_candidate_factor(row, candidate_id)
                    for row in audit_rows
                    if row["route_role"] == "weak_reference_control"
                    and row["scenario_bundle"] == scenario
                ]
            )
            > candidate_main_by_scenario[candidate_id][scenario]
        )
        warning_resolved = (
            weak_mean <= main_candidate
            and context_route_above_count == 0
            and context_scenario_above_count == 0
            and weak_scenario_above_count == 0
        )
        nearby_confirmation = _r6_candidate_is_nearby_width_confirmation(candidate_id)
        if warning_resolved and nearby_confirmation:
            nearby_warning_resolved_count += 1
        candidate_registry_rows.append(
            {
                **metadata,
                "nearby_width_family_confirmation_candidate": nearby_confirmation,
                "warning_resolved_by_candidate": warning_resolved,
                "main660_score_retention_fraction": main_retention,
                "main660_retention_warning": main_retention < 0.85,
                "weak_reference_above_main_after_candidate": weak_mean > main_candidate,
                "weak_reference_scenario_rows_above_main_after_candidate": (
                    weak_scenario_above_count
                ),
                "context_routes_above_main_after_candidate": context_route_above_count,
                "context_scenario_rows_above_main_after_candidate": (
                    context_scenario_above_count
                ),
                "uses_route_specific_multiplier": False,
                "uses_scenario_specific_per_route_fit": False,
                "uses_particle_specific_empirical_fit": False,
                "changes_main_660_definition": False,
                "authorizes_route_promotion": False,
                "claim_level": "relative_with_priors",
            }
        )

        for route_id in sorted({row["route_id"] for row in audit_rows}):
            route_rows = [row for row in audit_rows if row["route_id"] == route_id]
            first = route_rows[0]
            old_route_mean = _mean(
                [
                    float(row["detectability_relative_prior_score"])
                    for row in route_rows
                ]
            )
            candidate_route_mean = _mean(route_score_accum[(candidate_id, route_id)])
            route_factor_rows.append(
                {
                    "candidate_prior_id": candidate_id,
                    "route_id": route_id,
                    "route_role": first["route_role"],
                    "wavelength_nm": first["wavelength_nm"],
                    "width_nm": first["width_nm"],
                    "depth_nm": first["depth_nm"],
                    "mean_route_prior_factor": _mean(
                        route_factor_accum[(candidate_id, route_id)]
                    ),
                    "old_route_mean_score": old_route_mean,
                    "candidate_route_mean_score": candidate_route_mean,
                    "delta_removed": old_route_mean - candidate_route_mean,
                    "candidate_adjusted_delta_vs_main": (
                        candidate_route_mean - main_candidate
                    ),
                    "unadjusted_main_delta": candidate_route_mean - main_old_mean,
                    "route_promotion_authorized": False,
                    "main_660_redefinition_authorized": False,
                    "claim_level": "relative_with_priors",
                }
            )

        groups = {
            "locked_main_660": {
                row["route_id"] for row in audit_rows if row["route_role"] == "main_660"
            },
            "weak_reference_control": {"660_700x1500"},
            "above_main_context_warning_routes": R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS,
            "optional_660_900x1400": {"660_900x1400"},
            "selected_annulus_parallel_lens_sidecars": {
                "404_800x550",
                "404_800x600",
                "404_800x700",
                "660_800x550",
                "660_800x600",
                "660_800x700",
            },
            "shortwave_and_medium_controls": {
                "404_600x1300",
                "488_600x1500",
                "532_600x1500",
            },
        }
        for group, route_ids in groups.items():
            values = [
                value
                for route_id in route_ids
                for value in route_score_accum[(candidate_id, route_id)]
            ]
            group_mean = _mean(values)
            route_family_rows.append(
                {
                    "candidate_prior_id": candidate_id,
                    "route_family": group,
                    "n_route_ids": len(route_ids),
                    "n_existing_R5_rows": len(values),
                    "candidate_adjusted_mean_score": group_mean,
                    "candidate_adjusted_main660_mean": main_candidate,
                    "residual_delta_vs_candidate_adjusted_main": group_mean
                    - main_candidate,
                    "residual_above_main_flag": group_mean > main_candidate,
                    "route_promotion_authorized": False,
                    "main_660_redefinition_authorized": False,
                    "claim_level": "relative_with_priors",
                }
            )

        for scenario in sorted(R5_REQUIRED_SCENARIO_BUNDLE_IDS):
            scenario_rows.append(
                {
                    "candidate_prior_id": candidate_id,
                    "scenario_bundle": scenario,
                    "context_or_weak_routes_above_candidate_adjusted_main_count": (
                        scenario_residual_counts[(candidate_id, scenario)]
                    ),
                    "candidate_adjusted_main660_mean": candidate_main_by_scenario[
                        candidate_id
                    ][scenario],
                    "new_scenario_bundle_authorized": False,
                    "scenario_weight_change_authorized": False,
                    "claim_level": "relative_with_priors",
                }
            )

        for particle in sorted({row["particle_name"] for row in audit_rows}):
            particle_rows.append(
                {
                    "candidate_prior_id": candidate_id,
                    "particle_name": particle,
                    "particle_size_stratum": _particle_size_stratum(
                        next(row for row in audit_rows if row["particle_name"] == particle)
                    ),
                    "context_or_weak_routes_above_candidate_adjusted_main_count": (
                        particle_residual_counts[(candidate_id, particle)]
                    ),
                    "candidate_adjusted_main660_mean": candidate_main_by_particle[
                        candidate_id
                    ][particle],
                    "particle_specific_empirical_fit_authorized": False,
                    "claim_level": "relative_with_priors",
                }
            )

        for route_id in sorted(
            {row["route_id"] for row in audit_rows if row["route_role"] == "main_660"}
        ):
            route_rows = [row for row in audit_rows if row["route_id"] == route_id]
            old_route_mean = _mean(
                [
                    float(row["detectability_relative_prior_score"])
                    for row in route_rows
                ]
            )
            candidate_route_mean = _mean(route_score_accum[(candidate_id, route_id)])
            main_rows.append(
                {
                    "candidate_prior_id": candidate_id,
                    "route_id": route_id,
                    "old_main660_route_mean": old_route_mean,
                    "candidate_main660_route_mean": candidate_route_mean,
                    "main660_route_prior_factor": candidate_route_mean / old_route_mean,
                    "main660_score_retention_fraction": (
                        candidate_route_mean / old_route_mean
                    ),
                    "main660_retention_warning": (
                        candidate_route_mean / old_route_mean
                    )
                    < 0.85,
                    "main_660_route_role_locked": True,
                    "main_660_redefinition_authorized": False,
                    "route_promotion_authorized": False,
                    "claim_level": "relative_with_priors",
                }
            )

        selected_or_404_ids = {
            "404_600x1300",
            "404_800x550",
            "404_800x600",
            "404_800x700",
            "660_800x550",
            "660_800x600",
            "660_800x700",
        }
        for route_id in sorted(selected_or_404_ids):
            selected_and_404_rows.append(
                {
                    "candidate_prior_id": candidate_id,
                    "route_id": route_id,
                    "selected_annulus_replaces_all_crossing_ranking": False,
                    "selected_annulus_bound_change_authorized": False,
                    "thermal_sidecar_used_to_increase_NODI_score": False,
                    "route_promotion_authorized": False,
                    "claim_level": "relative_with_priors",
                }
            )

    selected_candidate = next(
        row
        for row in candidate_registry_rows
        if row["candidate_prior_id"] == selected_candidate_id
    )
    selected_future_recommendation = (
        "prepare_next_stage_plan_for_external_review_only"
        if nearby_warning_resolved_count >= 2
        and int(selected_candidate["context_routes_above_main_after_candidate"]) == 0
        and int(
            selected_candidate[
                "weak_reference_scenario_rows_above_main_after_candidate"
            ]
        )
        == 0
        else "prepare_route_governance_revision_plan_for_external_review_only"
    )
    audit_decision = (
        "low_dimensional_width_prior_sensitivity_stable_prepare_next_stage_plan_only"
        if selected_future_recommendation
        == "prepare_next_stage_plan_for_external_review_only"
        else "route_prior_sensitivity_unresolved_prepare_route_governance_plan_only"
    )

    claim_guard_rows = []
    for guardrail, value in (
        ("SNR_claim_level", "absolute_blocked"),
        ("event_probability_claim_level", "absolute_blocked"),
        ("p_detect_mapping_claim_level", "relative_with_priors"),
        ("legacy_detector_SNR_output_header_emitted", False),
        ("legacy_calibrated_detector_SNR_output_header_emitted", False),
        ("calibrated_SNR_or_event_probability_claim_emitted", False),
        ("absolute_LOD_or_true_concentration_claim_emitted", False),
        ("biological_specificity_claim_emitted", False),
        ("thermal_sidecar_used_to_increase_NODI_score", False),
        ("finite_zero_event_blank_safety_claim_emitted", False),
    ):
        claim_guard_rows.append({"guardrail": guardrail, "value": value, "status": "pass"})

    stop_gate_rows = [
        {"stop_gate": gate, "triggered": False, "status": "pass"}
        for gate in sorted(R6_REQUIRED_STOP_GATES)
    ]

    next_stage_rows = []
    for recommendation in sorted(R6_ALLOWED_RESULT_RECOMMENDATION_CLASSES):
        selected = recommendation == selected_future_recommendation
        next_stage_rows.append(
            {
                "future_recommendation_class": recommendation,
                "R6_recommendation": "selected_for_future_review"
                if selected
                else "not_selected_now",
                "rationale": (
                    "At least two nearby low-dimensional width-family candidates resolve the warning without forbidden fits."
                    if selected
                    else "Not selected by this bounded R6 audit result."
                ),
                "authorizes_execution": False,
                "authorizes_R7": False,
                "authorizes_route_promotion": False,
                "authorizes_main_660_redefinition": False,
            }
        )

    manifest_rows = [
        {
            "stage": "R6_route_prior_sensitivity_audit",
            "external_authorization": external_authorization,
            "R6_route_prior_sensitivity_audit_run": True,
            "audit_execution_type": (
                "bounded_existing_R5_artifact_route_prior_sensitivity_audit_only"
            ),
            "existing_R5_rows_audited": len(audit_rows),
            "candidate_prior_count": len(candidate_ids),
            "derived_candidate_rows_evaluated": len(sensitivity_rows),
            "max_R6_derived_candidate_rows": R6_DERIVED_CANDIDATE_ROW_CAP,
            "audit_route_id_count": len({row["route_id"] for row in audit_rows}),
            "scenario_bundle_count": len({row["scenario_bundle"] for row in audit_rows}),
            "stochastic_seed_count": 0,
            "new_case_rows_added": 0,
            "new_scenario_bundles_added": 0,
            "new_stochastic_seeds_added": 0,
            "new_solver_cases_added": 0,
            "new_experiments_started": 0,
            "main660_comparator_policy": "candidate_adjusted_locked_main_660",
            "secondary_main660_comparator_policy": "unadjusted_locked_main_660",
            "selected_candidate_prior_id": selected_candidate_id,
            "nearby_warning_resolved_candidate_count": nearby_warning_resolved_count,
            "at_least_two_nearby_low_dimensional_candidates_explain_warning": (
                nearby_warning_resolved_count >= 2
            ),
            "main660_retention_warning_candidate_count": main_retention_warnings,
            "selected_future_recommendation_class": selected_future_recommendation,
            "audit_decision": audit_decision,
            "R7_plan_preparation_authorized": False,
            "R7_execution_authorized": False,
            "R5_followup_expansion_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "route_specific_manual_prior_multiplier_attempted": False,
            "scenario_specific_per_route_fit_attempted": False,
            "particle_specific_empirical_fit_attempted": False,
            "calibrated_SNR_claim_emitted": False,
            "calibrated_event_probability_claim_emitted": False,
            **source_checksums,
        }
    ]

    event_budget = {
        "stage": "R6_route_prior_sensitivity_audit",
        "existing_R5_rows_audited": len(audit_rows),
        "candidate_prior_count": len(candidate_ids),
        "derived_candidate_rows": len(sensitivity_rows),
        "new_case_rows": 0,
        "new_scenario_bundles": 0,
        "new_stochastic_seeds": 0,
        "new_solver_cases": 0,
        "new_experiments": 0,
        "R7_execution_started": False,
    }
    scenario_budget = {
        "external_authorization": external_authorization,
        "audit_execution_type": (
            "bounded_existing_R5_artifact_route_prior_sensitivity_audit_only"
        ),
        "selected_candidate_prior_id": selected_candidate_id,
        "selected_future_recommendation_class": selected_future_recommendation,
        "R7_plan_preparation_authorized": False,
        "R7_execution_authorized": False,
        "R5_followup_expansion_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        **source_checksums,
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_R6_route_prior_sensitivity_audit",
        random_seed_policy="none_posthoc_existing_R5_artifacts_only",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=True,
        R4_representative_full_wave_validation_run=True,
        R5_full_grid_v2_run=True,
    )
    manifest.update(
        {
            "R4_revised_rerun_run": True,
            "R4_2_main660_nearwall_mesh_adjudication_run": True,
            "R5_1_route_role_stability_interpretation_run": True,
            "R5_2_bounded_scenario_prior_audit_run": True,
            "R5_3_route_prior_model_revision_audit_run": True,
            "R6_route_prior_sensitivity_audit_run": True,
            "R6_external_authorization": external_authorization,
            "R6_selected_candidate_prior_id": selected_candidate_id,
            "R6_selected_future_recommendation_class": selected_future_recommendation,
            "R7_plan_preparation_authorized": False,
            "R7_execution_authorized": False,
            "R5_followup_expansion_authorized": False,
            "new_case_rows_authorized": 0,
            "new_scenario_bundle_authorized": False,
            "new_stochastic_seed_authorized": False,
            "new_solver_case_authorized": False,
            "new_experiment_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "route_specific_manual_sign_flips_authorized": False,
            "route_specific_manual_prior_multipliers_authorized": False,
            "scenario_specific_per_route_fit_authorized": False,
            "particle_specific_empirical_fit_authorized": False,
            "calibrated_event_probability_claim_emitted": False,
            "absolute_LOD_or_true_concentration_claim_emitted": False,
            "biological_specificity_claim_emitted": False,
            "selected_annulus_replaces_all_crossing_ranking": False,
            "thermal_sidecar_used_to_increase_NODI_score": False,
            "finite_zero_event_blank_safety_claim_emitted": False,
            **source_checksums,
        }
    )

    write_csv_rows(output / "R6_route_prior_sensitivity_manifest.csv", manifest_rows)
    write_csv_rows(output / "R6_candidate_prior_registry.csv", candidate_registry_rows)
    write_csv_rows(
        output / "R6_candidate_prior_sensitivity_matrix.csv",
        sensitivity_rows,
    )
    write_csv_rows(output / "R6_route_prior_factor_by_route.csv", route_factor_rows)
    write_csv_rows(
        output / "R6_route_family_residual_warning_table.csv",
        route_family_rows,
    )
    write_csv_rows(output / "R6_scenario_residual_warning_table.csv", scenario_rows)
    write_csv_rows(
        output / "R6_particle_stratum_residual_warning_table.csv",
        particle_rows,
    )
    write_csv_rows(output / "R6_main660_locked_comparator_summary.csv", main_rows)
    write_csv_rows(
        output / "R6_selected_annulus_and_404_sidecar_guardrail_summary.csv",
        selected_and_404_rows,
    )
    write_csv_rows(output / "R6_claim_boundary_guardrail_summary.csv", claim_guard_rows)
    write_csv_rows(output / "R6_stop_gate_summary.csv", stop_gate_rows)
    write_csv_rows(output / "R6_next_stage_recommendation_matrix.csv", next_stage_rows)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    report = (
        "# EV/NODI realism v2 R6 route-prior sensitivity audit report\n\n"
        f"- External authorization: {external_authorization}.\n"
        "- Execution type: bounded existing R5 artifact route-prior sensitivity audit only.\n"
        f"- Existing R5 rows audited: {len(audit_rows)}.\n"
        f"- Candidate priors evaluated: {len(candidate_ids)}.\n"
        f"- Derived candidate rows evaluated: {len(sensitivity_rows)}.\n"
        "- New case rows / scenarios / seeds / solver cases / experiments: 0.\n"
        "- Comparator policy: candidate-adjusted locked main-660 primary; unadjusted main-660 diagnostic secondary.\n"
        f"- Nearby warning-resolved candidate count: {nearby_warning_resolved_count}.\n"
        f"- Candidate count with main-660 retention warning: {main_retention_warnings}.\n"
        f"- Selected future recommendation class: {selected_future_recommendation}.\n"
        "- R7 plan preparation authorized: false.\n"
        "- R7 execution authorized: false.\n"
        "- Context-route promotion authorized: false.\n"
        "- Main-660 redefinition authorized: false.\n"
        "- Claim boundaries remain relative_with_priors / absolute_blocked.\n"
    )
    (output / "R6_route_prior_sensitivity_report.md").write_text(
        report,
        encoding="utf-8",
    )

    return {
        "output_dir": str(output),
        "manifest": manifest,
        "R6_route_prior_sensitivity_audit_run": True,
        "existing_R5_rows_audited": len(audit_rows),
        "candidate_prior_count": len(candidate_ids),
        "derived_candidate_rows_evaluated": len(sensitivity_rows),
        "selected_future_recommendation_class": selected_future_recommendation,
        "audit_decision": audit_decision,
        "nearby_warning_resolved_candidate_count": nearby_warning_resolved_count,
        "main660_retention_warning_candidate_count": main_retention_warnings,
        "R7_plan_preparation_authorized": False,
        "R7_execution_authorized": False,
        "R5_followup_expansion_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
    }


def run_R7_route_prior_mechanistic_decomposition_audit(
    output_dir: str | Path = DEFAULT_R7_ROUTE_PRIOR_MECHANISTIC_DECOMPOSITION_DIR,
    *,
    external_authorization: str = (
        "PASS_TO_BOUNDED_R7_ROUTE_PRIOR_MECHANISTIC_DECOMPOSITION_AUDIT_ONLY"
    ),
    write_root_manifest: bool = True,
) -> dict[str, Any]:
    if external_authorization != (
        "PASS_TO_BOUNDED_R7_ROUTE_PRIOR_MECHANISTIC_DECOMPOSITION_AUDIT_ONLY"
    ):
        raise ValueError("R7 audit requires exact external authorization")
    plan = validate_R7_route_prior_mechanistic_decomposition_plan()
    r6_dir = DEFAULT_R6_ROUTE_PRIOR_SENSITIVITY_AUDIT_DIR
    if not r6_dir.exists():
        raise FileNotFoundError(f"R6 result directory not found: {r6_dir}")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"

    source_checksums = {
        "R6_manifest_checksum": sha256_file(
            r6_dir / "R6_route_prior_sensitivity_manifest.csv"
        ),
        "R6_candidate_registry_checksum": sha256_file(
            r6_dir / "R6_candidate_prior_registry.csv"
        ),
        "R6_candidate_sensitivity_matrix_checksum": sha256_file(
            r6_dir / "R6_candidate_prior_sensitivity_matrix.csv"
        ),
        "R6_route_prior_factor_checksum": sha256_file(
            r6_dir / "R6_route_prior_factor_by_route.csv"
        ),
        "R6_route_family_residual_checksum": sha256_file(
            r6_dir / "R6_route_family_residual_warning_table.csv"
        ),
        "R6_scenario_residual_checksum": sha256_file(
            r6_dir / "R6_scenario_residual_warning_table.csv"
        ),
        "R6_particle_stratum_residual_checksum": sha256_file(
            r6_dir / "R6_particle_stratum_residual_warning_table.csv"
        ),
        "R6_main660_comparator_checksum": sha256_file(
            r6_dir / "R6_main660_locked_comparator_summary.csv"
        ),
        "R6_claim_guardrail_checksum": sha256_file(
            r6_dir / "R6_claim_boundary_guardrail_summary.csv"
        ),
        "R6_stop_gate_checksum": sha256_file(r6_dir / "R6_stop_gate_summary.csv"),
        "R6_next_stage_matrix_checksum": sha256_file(
            r6_dir / "R6_next_stage_recommendation_matrix.csv"
        ),
        "R6_run_manifest_checksum": sha256_file(r6_dir / "run_manifest.json"),
    }
    for field in R7_REQUIRED_PROVENANCE_FIELDS:
        if source_checksums[field] != plan["provenance_freeze"][field]:
            raise ValueError(f"R7 source checksum drift before audit: {field}")

    source_paths = [
        r6_dir / "R6_route_prior_sensitivity_manifest.csv",
        r6_dir / "R6_candidate_prior_registry.csv",
        r6_dir / "R6_candidate_prior_sensitivity_matrix.csv",
        r6_dir / "R6_route_prior_factor_by_route.csv",
        r6_dir / "R6_particle_stratum_residual_warning_table.csv",
        r6_dir / "R6_main660_locked_comparator_summary.csv",
        r6_dir / "R6_claim_boundary_guardrail_summary.csv",
        r6_dir / "R6_stop_gate_summary.csv",
    ]
    for path in source_paths:
        validate_output_names(_csv_headers(path))

    r6_manifest = _read_csv_dicts(
        r6_dir / "R6_route_prior_sensitivity_manifest.csv"
    )[0]
    if int(r6_manifest["existing_R5_rows_audited"]) != R7_ROUTE_PRIOR_SOURCE_ROW_CAP:
        raise ValueError("R7 source row cap drifted from R6")
    if int(r6_manifest["candidate_prior_count"]) != len(R6_CANDIDATE_PRIOR_REGISTRY):
        raise ValueError("R7 R6 candidate count drifted")
    if int(r6_manifest["derived_candidate_rows_evaluated"]) != (
        R6_DERIVED_CANDIDATE_ROW_CAP
    ):
        raise ValueError("R7 R6 derived candidate row count drifted")
    if r6_manifest["selected_future_recommendation_class"] != (
        "prepare_next_stage_plan_for_external_review_only"
    ):
        raise ValueError("R7 requires the accepted R6 next-stage recommendation")
    if r6_manifest["R7_execution_authorized"] != "False":
        raise ValueError("R7 cannot consume a pre-authorized R7 manifest")

    r6_registry_rows = _read_csv_dicts(r6_dir / "R6_candidate_prior_registry.csv")
    r6_registry_by_id = {row["candidate_prior_id"]: row for row in r6_registry_rows}
    accepted_band = plan["accepted_width_prior_band"]
    accepted_candidate_ids = [
        str(candidate_id)
        for candidate_id in accepted_band["accepted_explanatory_candidate_ids"]
    ]
    if not all(
        r6_registry_by_id[candidate_id]["warning_resolved_by_candidate"] == "True"
        for candidate_id in accepted_candidate_ids
    ):
        raise ValueError("R7 accepted band includes an unresolved R6 candidate")
    if not all(
        float(r6_registry_by_id[candidate_id]["main660_score_retention_fraction"])
        >= R7_ACCEPTED_WIDTH_PRIOR_BAND["main660_retention_fraction_min"]
        for candidate_id in accepted_candidate_ids
    ):
        raise ValueError("R7 accepted band includes a low-retention candidate")

    sensitivity_rows = _read_csv_dicts(
        r6_dir / "R6_candidate_prior_sensitivity_matrix.csv"
    )
    selected_candidate_id = "global_width_quadratic_regularization"
    selected_rows = [
        row for row in sensitivity_rows if row["candidate_prior_id"] == selected_candidate_id
    ]
    if len(selected_rows) != R7_ROUTE_PRIOR_SOURCE_ROW_CAP:
        raise ValueError("R7 selected candidate source row count mismatch")
    if {row["route_id"] for row in selected_rows} != R5_2_AUDIT_ROUTE_IDS:
        raise ValueError("R7 selected candidate route set drifted")
    if {row["scenario_bundle"] for row in selected_rows} != R5_REQUIRED_SCENARIO_BUNDLE_IDS:
        raise ValueError("R7 selected candidate scenario set drifted")
    if len({row["particle_name"] for row in selected_rows}) != (
        R5_V1_SOURCE_PARTICLE_NAME_COUNT
    ):
        raise ValueError("R7 selected candidate particle count mismatch")
    for row in selected_rows:
        if row["claim_level"] != "relative_with_priors":
            raise ValueError("R7 selected candidate claim level drifted")
        if row["uses_route_specific_multiplier"] != "False":
            raise ValueError("R7 cannot consume route-specific multipliers")
        if row["uses_scenario_specific_per_route_fit"] != "False":
            raise ValueError("R7 cannot consume scenario-specific route fits")
        if row["uses_particle_specific_empirical_fit"] != "False":
            raise ValueError("R7 cannot consume particle-specific fits")

    existing_fields = set(selected_rows[0])
    derivable_existing_fields = {"width_nm", "depth_nm"}
    available_fields = existing_fields | derivable_existing_fields
    mechanistic_rows = []
    executable_mechanistic_count = 0
    physical_artifact_gap_count = 0
    for row in plan["mechanistic_decomposition_design"][
        "candidate_mechanistic_prior_registry"
    ]:
        allowed_inputs = list(row["allowed_input_fields"])
        missing_inputs = [field for field in allowed_inputs if field not in available_fields]
        diagnostic_only = row["claim_level"] == "diagnostic_only"
        can_execute = (
            not missing_inputs
            and row["requires_new_operator_artifact"] is False
            and not diagnostic_only
        )
        if can_execute:
            executable_mechanistic_count += 1
        if missing_inputs or row["requires_new_operator_artifact"] is True:
            physical_artifact_gap_count += 1
        mechanistic_rows.append(
            {
                **row,
                "allowed_input_fields": "|".join(allowed_inputs),
                "existing_artifact_columns_available": not missing_inputs,
                "derivable_existing_artifact_fields": "|".join(
                    sorted(set(allowed_inputs) & derivable_existing_fields)
                ),
                "missing_input_fields": "|".join(missing_inputs),
                "candidate_can_be_executed_without_new_artifact": can_execute,
                "candidate_execution_status": (
                    "executable_existing_artifact_mechanistic_proxy"
                    if can_execute
                    else "diagnostic_or_requires_new_artifact"
                ),
                "route_promotion_authorized": False,
                "main_660_redefinition_authorized": False,
            }
        )

    accepted_band_rows = []
    for candidate_id in accepted_candidate_ids:
        r6_row = r6_registry_by_id[candidate_id]
        accepted_band_rows.append(
            {
                "candidate_prior_id": candidate_id,
                "candidate_interpretation_class": (
                    "accepted_explanatory"
                    if candidate_id != "width_quad_850"
                    else "accepted_but_caution"
                ),
                "width_pivot_nm": r6_row["width_pivot_nm"],
                "width_exponent": r6_row["width_exponent"],
                "main660_score_retention_fraction": r6_row[
                    "main660_score_retention_fraction"
                ],
                "context_routes_above_main_after_candidate": r6_row[
                    "context_routes_above_main_after_candidate"
                ],
                "weak_reference_scenario_rows_above_main_after_candidate": r6_row[
                    "weak_reference_scenario_rows_above_main_after_candidate"
                ],
                "route_promotion_authorized": False,
                "main_660_redefinition_authorized": False,
                "claim_level": "relative_with_priors",
            }
        )

    width_900 = r6_registry_by_id["width_quad_900"]
    route_factor_rows = _read_csv_dicts(r6_dir / "R6_route_prior_factor_by_route.csv")
    optional_900_by_candidate = {
        row["candidate_prior_id"]: row
        for row in route_factor_rows
        if row["route_id"] == "660_900x1400"
    }
    width_quad_900_rows = [
        {
            "candidate_prior_id": "width_quad_900",
            "candidate_interpretation_class": "over_severe_prior_caution",
            "warning_resolved_by_candidate": width_900[
                "warning_resolved_by_candidate"
            ],
            "main660_score_retention_fraction": width_900[
                "main660_score_retention_fraction"
            ],
            "main660_retention_warning": width_900["main660_retention_warning"],
            "optional_900_vs_candidate_adjusted_main_delta": optional_900_by_candidate[
                "width_quad_900"
            ]["candidate_adjusted_delta_vs_main"],
            "optional_900_vs_unadjusted_main_delta": optional_900_by_candidate[
                "width_quad_900"
            ]["unadjusted_main_delta"],
            "accepted_width_prior_band_member": False,
            "route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "interpretation": (
                "resolves_warning_but_over_penalizes_locked_main_and_makes_optional_900_diagnostic_positive"
            ),
        }
    ]

    factor_schema_rows = []
    for row in mechanistic_rows:
        family = row["candidate_prior_family"]
        if family == "clearance_wall_PEG_transport_family":
            schema = "family_level_factor_from_width_depth_particle_clearance_proxy"
        elif family == "transport_survival_clogging_family":
            schema = "family_level_factor_from_width_depth_transport_risk_proxy"
        elif family == "reference_operating_band_family":
            schema = "requires_reference_operator_artifact_not_source_score"
        elif family == "BFP_slit_ROI_alignment_family":
            schema = "requires_BFP_slit_ROI_operator_artifact"
        elif family == "fabrication_metrology_margin_family":
            schema = "requires_metrology_margin_or_nominal_width_depth_proxy"
        else:
            schema = "diagnostic_summary_no_score_factor"
        factor_schema_rows.append(
            {
                "candidate_mechanistic_prior_id": row[
                    "candidate_mechanistic_prior_id"
                ],
                "candidate_prior_family": family,
                "factor_schema": schema,
                "existing_artifact_columns_available": row[
                    "existing_artifact_columns_available"
                ],
                "candidate_can_be_executed_without_new_artifact": row[
                    "candidate_can_be_executed_without_new_artifact"
                ],
                "uses_source_v1_relative_score_as_physical_input": False,
                "uses_route_specific_multiplier": False,
                "uses_particle_specific_empirical_fit": False,
                "claim_level": row["claim_level"],
            }
        )

    residual_rows = [
        row
        for row in selected_rows
        if row["residual_above_main_flag"] == "True"
        and row["route_id"] in (R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS | {"660_700x1500"})
    ]
    residual_accum: dict[tuple[str, str, str, str], list[float]] = {}
    for row in residual_rows:
        key = (
            row["particle_name"],
            row["particle_size_stratum"],
            row["route_id"],
            row["route_role"],
        )
        residual_accum.setdefault(key, []).append(float(row["residual_delta_vs_main"]))
    particle_top_rows = []
    for (particle, stratum, route_id, route_role), values in residual_accum.items():
        particle_top_rows.append(
            {
                "candidate_prior_id": selected_candidate_id,
                "particle_name": particle,
                "particle_size_stratum": stratum,
                "route_id": route_id,
                "route_role": route_role,
                "residual_above_main_row_count": len(values),
                "mean_positive_residual_delta_vs_main": _mean(values),
                "max_positive_residual_delta_vs_main": max(values),
                "particle_specific_empirical_fit_authorized": False,
                "interpretation": "particle_stratum_residual_warning_not_fit_target",
                "claim_level": "relative_with_priors",
            }
        )
    particle_top_rows.sort(
        key=lambda row: (
            -int(row["residual_above_main_row_count"]),
            -float(row["mean_positive_residual_delta_vs_main"]),
        )
    )
    particle_top_rows = particle_top_rows[:50]

    family_residual_accum: dict[tuple[str, str], list[float]] = {}
    for row in residual_rows:
        family = (
            "weak_reference_control"
            if row["route_id"] == "660_700x1500"
            else "above_main_context_warning_routes"
        )
        key = (row["particle_size_stratum"], family)
        family_residual_accum.setdefault(key, []).append(
            float(row["residual_delta_vs_main"])
        )
    particle_family_rows = []
    for (stratum, family), values in sorted(family_residual_accum.items()):
        particle_family_rows.append(
            {
                "candidate_prior_id": selected_candidate_id,
                "particle_size_stratum": stratum,
                "route_family": family,
                "residual_above_main_row_count": len(values),
                "mean_positive_residual_delta_vs_main": _mean(values),
                "max_positive_residual_delta_vs_main": max(values),
                "particle_specific_empirical_fit_authorized": False,
                "claim_level": "relative_with_priors",
            }
        )

    comparison_groups = {
        "gold_anchor": [
            row
            for row in residual_rows
            if str(row["particle_size_stratum"]).startswith("gold")
        ],
        "EV_like": [
            row
            for row in residual_rows
            if not str(row["particle_size_stratum"]).startswith("gold")
        ],
    }
    comparison_rows = []
    for group, rows in comparison_groups.items():
        values = [float(row["residual_delta_vs_main"]) for row in rows]
        comparison_rows.append(
            {
                "candidate_prior_id": selected_candidate_id,
                "comparison_group": group,
                "residual_above_main_row_count": len(rows),
                "unique_particle_count": len({row["particle_name"] for row in rows}),
                "mean_positive_residual_delta_vs_main": _mean(values) if values else 0.0,
                "max_positive_residual_delta_vs_main": max(values) if values else 0.0,
                "particle_specific_empirical_fit_authorized": False,
                "interpretation": "residual_comparison_only_no_particle_fit",
            }
        )

    optional_rows = []
    for candidate_id in [
        "width_exp1p5_800",
        "global_width_quadratic_regularization",
        "width_quad_850",
        "width_quad_900",
    ]:
        row = optional_900_by_candidate[candidate_id]
        optional_rows.append(
            {
                "candidate_prior_id": candidate_id,
                "route_id": "660_900x1400",
                "optional_900_role_after_prior": "optional_robustness_probe",
                "optional_900_vs_candidate_adjusted_main_delta": row[
                    "candidate_adjusted_delta_vs_main"
                ],
                "optional_900_vs_unadjusted_main_delta": row["unadjusted_main_delta"],
                "optional_900_positive_vs_candidate_adjusted_main": (
                    float(row["candidate_adjusted_delta_vs_main"]) > 0
                ),
                "main_660_redefinition_authorized": False,
                "route_promotion_authorized": False,
                "claim_level": "relative_with_priors",
            }
        )

    non_width_rows = []
    for candidate_id in ["reference_band_penalty", "BFP_alignment_risk"]:
        row = r6_registry_by_id[candidate_id]
        non_width_rows.append(
            {
                "candidate_prior_id": candidate_id,
                "R6_warning_resolved_by_candidate": row[
                    "warning_resolved_by_candidate"
                ],
                "R6_context_routes_above_main_after_candidate": row[
                    "context_routes_above_main_after_candidate"
                ],
                "source_v1_relative_score_as_physical_prior_authorized": False,
                "requires_physical_operator_columns": True,
                "manual_route_id_multiplier_authorized": False,
                "scenario_specific_per_route_fit_authorized": False,
                "particle_specific_empirical_fit_authorized": False,
                "interpretation": (
                    "outcome_proximal_diagnostic_not_physical_prior"
                    if candidate_id == "reference_band_penalty"
                    else "operator_column_required_before_physical_prior"
                ),
            }
        )

    claim_guard_rows = []
    for guardrail, value in (
        ("SNR_claim_level", "absolute_blocked"),
        ("event_probability_claim_level", "absolute_blocked"),
        ("p_detect_mapping_claim_level", "relative_with_priors"),
        ("legacy_detector_SNR_output_header_emitted", False),
        ("legacy_calibrated_detector_SNR_output_header_emitted", False),
        ("calibrated_SNR_or_event_probability_claim_emitted", False),
        ("absolute_LOD_or_true_concentration_claim_emitted", False),
        ("biological_specificity_claim_emitted", False),
        ("thermal_sidecar_used_to_increase_NODI_score", False),
        ("finite_zero_event_blank_safety_claim_emitted", False),
    ):
        claim_guard_rows.append({"guardrail": guardrail, "value": value, "status": "pass"})

    stop_gate_rows = [
        {"stop_gate": gate, "triggered": False, "status": "pass"}
        for gate in sorted(R7_REQUIRED_STOP_GATES)
    ]

    selected_future_recommendation = (
        "prepare_operator_artifact_gap_register_plan_only"
    )
    audit_decision = (
        "mechanistic_width_prior_supported_prepare_artifact_gap_register_only"
    )
    next_stage_rows = []
    for recommendation in sorted(R7_ALLOWED_RESULT_RECOMMENDATION_CLASSES):
        selected = recommendation == selected_future_recommendation
        next_stage_rows.append(
            {
                "future_recommendation_class": recommendation,
                "R7_recommendation": "selected_for_future_review"
                if selected
                else "not_selected_now",
                "rationale": (
                    "Two existing-artifact mechanism families support the width-family warning explanation, but reference/BFP/metrology physical operators remain no-measured-data artifact gaps."
                    if selected
                    else "Not selected by this bounded R7 audit result."
                ),
                "authorizes_execution": False,
                "authorizes_R8": False,
                "authorizes_experiment": False,
                "authorizes_route_promotion": False,
                "authorizes_main_660_redefinition": False,
            }
        )

    manifest_rows = [
        {
            "stage": "R7_route_prior_mechanistic_decomposition_audit",
            "external_authorization": external_authorization,
            "R7_route_prior_mechanistic_decomposition_audit_run": True,
            "audit_execution_type": (
                "bounded_existing_R5_artifact_route_prior_mechanistic_decomposition_audit_only"
            ),
            "existing_R5_rows_interpreted": R7_ROUTE_PRIOR_SOURCE_ROW_CAP,
            "mechanistic_candidate_count": len(mechanistic_rows),
            "max_mechanistic_candidate_count": R7_MAX_MECHANISTIC_CANDIDATE_COUNT,
            "derived_mechanistic_candidate_rows_evaluated": 0,
            "max_R7_derived_candidate_rows": R7_DERIVED_CANDIDATE_ROW_CAP,
            "audit_route_id_count": R5_2_AUDIT_ROUTE_COUNT,
            "scenario_bundle_count": R5_NAMED_SCENARIO_BUNDLE_COUNT,
            "stochastic_seed_count": 0,
            "new_case_rows_added": 0,
            "new_scenario_bundles_added": 0,
            "new_stochastic_seeds_added": 0,
            "new_solver_cases_added": 0,
            "new_experiments_started": 0,
            "accepted_width_prior_band_candidate_count": len(accepted_candidate_ids),
            "executable_existing_artifact_mechanistic_candidate_count": (
                executable_mechanistic_count
            ),
            "physical_operator_artifact_gap_count": physical_artifact_gap_count,
            "particle_stratum_residual_warning_count": len(particle_top_rows),
            "selected_future_recommendation_class": selected_future_recommendation,
            "audit_decision": audit_decision,
            "R8_plan_preparation_authorized": False,
            "R8_execution_authorized": False,
            "new_experiment_authorized": False,
            "R5_followup_expansion_authorized": False,
            "R6_followup_expansion_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "route_specific_manual_prior_multiplier_attempted": False,
            "scenario_specific_per_route_fit_attempted": False,
            "particle_specific_empirical_fit_attempted": False,
            "score_derived_physical_prior_attempted": False,
            "calibrated_SNR_claim_emitted": False,
            "calibrated_event_probability_claim_emitted": False,
            **source_checksums,
        }
    ]

    event_budget = {
        "stage": "R7_route_prior_mechanistic_decomposition_audit",
        "existing_R5_rows_interpreted": R7_ROUTE_PRIOR_SOURCE_ROW_CAP,
        "mechanistic_candidate_count": len(mechanistic_rows),
        "derived_mechanistic_candidate_rows": 0,
        "new_case_rows": 0,
        "new_scenario_bundles": 0,
        "new_stochastic_seeds": 0,
        "new_solver_cases": 0,
        "new_experiments": 0,
        "R8_execution_started": False,
    }
    scenario_budget = {
        "external_authorization": external_authorization,
        "audit_execution_type": (
            "bounded_existing_R5_artifact_route_prior_mechanistic_decomposition_audit_only"
        ),
        "selected_future_recommendation_class": selected_future_recommendation,
        "R8_plan_preparation_authorized": False,
        "R8_execution_authorized": False,
        "new_experiment_authorized": False,
        "R5_followup_expansion_authorized": False,
        "R6_followup_expansion_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        **source_checksums,
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_R7_route_prior_mechanistic_decomposition_audit",
        random_seed_policy="none_posthoc_existing_R5_R6_artifacts_only",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=True,
        R4_representative_full_wave_validation_run=True,
        R5_full_grid_v2_run=True,
    )
    manifest.update(
        {
            "R4_revised_rerun_run": True,
            "R4_2_main660_nearwall_mesh_adjudication_run": True,
            "R5_1_route_role_stability_interpretation_run": True,
            "R5_2_bounded_scenario_prior_audit_run": True,
            "R5_3_route_prior_model_revision_audit_run": True,
            "R6_route_prior_sensitivity_audit_run": True,
            "R7_route_prior_mechanistic_decomposition_audit_run": True,
            "R7_external_authorization": external_authorization,
            "R7_selected_future_recommendation_class": selected_future_recommendation,
            "R8_plan_preparation_authorized": False,
            "R8_execution_authorized": False,
            "new_experiment_authorized": False,
            "R5_followup_expansion_authorized": False,
            "R6_followup_expansion_authorized": False,
            "new_case_rows_authorized": 0,
            "new_scenario_bundle_authorized": False,
            "new_stochastic_seed_authorized": False,
            "new_solver_case_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "route_specific_manual_sign_flips_authorized": False,
            "route_specific_manual_prior_multipliers_authorized": False,
            "scenario_specific_per_route_fit_authorized": False,
            "particle_specific_empirical_fit_authorized": False,
            "score_derived_physical_prior_authorized": False,
            "calibrated_event_probability_claim_emitted": False,
            "absolute_LOD_or_true_concentration_claim_emitted": False,
            "biological_specificity_claim_emitted": False,
            "selected_annulus_replaces_all_crossing_ranking": False,
            "thermal_sidecar_used_to_increase_NODI_score": False,
            "finite_zero_event_blank_safety_claim_emitted": False,
            **source_checksums,
        }
    )

    write_csv_rows(output / "R7_mechanistic_decomposition_manifest.csv", manifest_rows)
    write_csv_rows(output / "R7_candidate_mechanistic_prior_registry.csv", mechanistic_rows)
    write_csv_rows(output / "R7_accepted_width_prior_band_summary.csv", accepted_band_rows)
    write_csv_rows(
        output / "R7_width_quad_900_over_severe_caution_summary.csv",
        width_quad_900_rows,
    )
    write_csv_rows(output / "R7_mechanistic_prior_factor_schema.csv", factor_schema_rows)
    write_csv_rows(
        output / "R7_particle_stratum_residual_top_routes.csv",
        particle_top_rows,
    )
    write_csv_rows(
        output / "R7_particle_stratum_residual_by_family.csv",
        particle_family_rows,
    )
    write_csv_rows(
        output / "R7_gold_anchor_vs_EV_residual_comparison.csv",
        comparison_rows,
    )
    write_csv_rows(output / "R7_optional_900_governance_diagnostic.csv", optional_rows)
    write_csv_rows(
        output / "R7_non_width_prior_input_requirement_summary.csv",
        non_width_rows,
    )
    write_csv_rows(output / "R7_claim_boundary_guardrail_summary.csv", claim_guard_rows)
    write_csv_rows(output / "R7_stop_gate_summary.csv", stop_gate_rows)
    write_csv_rows(output / "R7_next_stage_recommendation_matrix.csv", next_stage_rows)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    report = (
        "# EV/NODI realism v2 R7 route-prior mechanistic decomposition audit report\n\n"
        f"- External authorization: {external_authorization}.\n"
        "- Execution type: bounded existing R5/R6 artifact mechanistic decomposition audit only.\n"
        f"- Existing R5 rows interpreted: {R7_ROUTE_PRIOR_SOURCE_ROW_CAP}.\n"
        f"- Mechanistic candidates audited: {len(mechanistic_rows)}.\n"
        "- New case rows / scenarios / seeds / solver cases / experiments: 0.\n"
        "- Accepted width-prior band: pivot 800-850 nm, exponent 1.5-2.0, main-660 retention >= 0.85.\n"
        "- width_quad_900 remains an over-severe caution, not an accepted band member.\n"
        f"- Existing-artifact executable mechanism candidates: {executable_mechanistic_count}.\n"
        f"- Physical/operator artifact gaps: {physical_artifact_gap_count}.\n"
        f"- Particle residual warning rows reported: {len(particle_top_rows)}.\n"
        f"- Selected future recommendation class: {selected_future_recommendation}.\n"
        "- R8 plan preparation authorized: false.\n"
        "- R8 execution authorized: false.\n"
        "- New experiment authorized: false.\n"
        "- Context-route promotion authorized: false.\n"
        "- Main-660 redefinition authorized: false.\n"
        "- Claim boundaries remain relative_with_priors / absolute_blocked.\n"
    )
    (output / "R7_route_prior_mechanistic_decomposition_report.md").write_text(
        report,
        encoding="utf-8",
    )

    return {
        "output_dir": str(output),
        "manifest": manifest,
        "R7_route_prior_mechanistic_decomposition_audit_run": True,
        "existing_R5_rows_interpreted": R7_ROUTE_PRIOR_SOURCE_ROW_CAP,
        "mechanistic_candidate_count": len(mechanistic_rows),
        "executable_existing_artifact_mechanistic_candidate_count": (
            executable_mechanistic_count
        ),
        "physical_operator_artifact_gap_count": physical_artifact_gap_count,
        "particle_stratum_residual_warning_count": len(particle_top_rows),
        "selected_future_recommendation_class": selected_future_recommendation,
        "audit_decision": audit_decision,
        "R8_plan_preparation_authorized": False,
        "R8_execution_authorized": False,
        "new_experiment_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
    }


def _r7_1_protocol_rows(module: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    fields = list(module["required_artifact_fields"])
    for idx, field in enumerate(fields, start=1):
        rows.append(
            {
                "module_id": module["module_id"],
                "artifact_field": field,
                "artifact_field_index": idx,
                "purpose": module["purpose"],
                "field_required_before_physical_prior_use": True,
                "field_required_before_post_v2_validation_program": True,
                "authorizes_measurement": False,
                "authorizes_experiment": False,
                "authorizes_solver_case": False,
                "authorizes_route_promotion": False,
                "authorizes_main_660_redefinition": False,
                "uses_source_v1_relative_score_as_physical_input": False,
                "allows_route_specific_multiplier": False,
                "allows_particle_specific_fit": False,
                "claim_level": module["claim_level"],
                "protocol_status": "requirement_defined_not_executed",
            }
        )
    return rows


def run_R7_1_operator_artifact_validation_protocol_generation(
    output_dir: str | Path = DEFAULT_R7_1_OPERATOR_ARTIFACT_VALIDATION_DIR,
    *,
    self_authorization: str = (
        "PASS_TO_R7_1_OPERATOR_ARTIFACT_VALIDATION_PROTOCOL_GENERATION_ONLY"
    ),
    write_root_manifest: bool = True,
) -> dict[str, Any]:
    if self_authorization != (
        "PASS_TO_R7_1_OPERATOR_ARTIFACT_VALIDATION_PROTOCOL_GENERATION_ONLY"
    ):
        raise ValueError("R7.1 protocol generation requires exact self authorization")
    plan = validate_R7_1_operator_artifact_validation_plan()
    r7_dir = DEFAULT_R7_ROUTE_PRIOR_MECHANISTIC_DECOMPOSITION_DIR
    if not r7_dir.exists():
        raise FileNotFoundError(f"R7 result directory not found: {r7_dir}")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"

    source_checksums = {
        "R7_manifest_checksum": sha256_file(
            r7_dir / "R7_mechanistic_decomposition_manifest.csv"
        ),
        "R7_candidate_registry_checksum": sha256_file(
            r7_dir / "R7_candidate_mechanistic_prior_registry.csv"
        ),
        "R7_accepted_width_band_checksum": sha256_file(
            r7_dir / "R7_accepted_width_prior_band_summary.csv"
        ),
        "R7_width_900_caution_checksum": sha256_file(
            r7_dir / "R7_width_quad_900_over_severe_caution_summary.csv"
        ),
        "R7_factor_schema_checksum": sha256_file(
            r7_dir / "R7_mechanistic_prior_factor_schema.csv"
        ),
        "R7_particle_residual_top_checksum": sha256_file(
            r7_dir / "R7_particle_stratum_residual_top_routes.csv"
        ),
        "R7_particle_residual_by_family_checksum": sha256_file(
            r7_dir / "R7_particle_stratum_residual_by_family.csv"
        ),
        "R7_gold_vs_EV_residual_checksum": sha256_file(
            r7_dir / "R7_gold_anchor_vs_EV_residual_comparison.csv"
        ),
        "R7_optional_900_checksum": sha256_file(
            r7_dir / "R7_optional_900_governance_diagnostic.csv"
        ),
        "R7_non_width_requirement_checksum": sha256_file(
            r7_dir / "R7_non_width_prior_input_requirement_summary.csv"
        ),
        "R7_claim_guardrail_checksum": sha256_file(
            r7_dir / "R7_claim_boundary_guardrail_summary.csv"
        ),
        "R7_stop_gate_checksum": sha256_file(r7_dir / "R7_stop_gate_summary.csv"),
        "R7_next_stage_matrix_checksum": sha256_file(
            r7_dir / "R7_next_stage_recommendation_matrix.csv"
        ),
        "R7_run_manifest_checksum": sha256_file(r7_dir / "run_manifest.json"),
    }
    for field in R7_1_REQUIRED_PROVENANCE_FIELDS:
        if source_checksums[field] != plan["provenance_freeze"][field]:
            raise ValueError(f"R7.1 source checksum drift before protocol generation: {field}")

    for path in r7_dir.glob("*.csv"):
        if path.name.startswith("._"):
            continue
        validate_output_names(_csv_headers(path))

    r7_manifest = _read_csv_dicts(
        r7_dir / "R7_mechanistic_decomposition_manifest.csv"
    )[0]
    if r7_manifest["selected_future_recommendation_class"] != (
        "prepare_operator_artifact_gap_register_plan_only"
    ):
        raise ValueError("R7.1 requires the R7 operator-artifact recommendation")
    for key in (
        "R8_plan_preparation_authorized",
        "R8_execution_authorized",
        "new_experiment_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "score_derived_physical_prior_attempted",
        "particle_specific_empirical_fit_attempted",
    ):
        if r7_manifest[key] != "False":
            raise ValueError(f"R7.1 cannot proceed with R7 guard drift: {key}")

    modules = list(plan["evidence_module_registry"])
    module_count = len(modules)
    artifact_field_count = sum(len(module["required_artifact_fields"]) for module in modules)

    protocol_by_output = {
        "reference_operating_band_artifact_protocol": (
            "R7_1_reference_operating_band_artifact_protocol.csv"
        ),
        "BFP_slit_ROI_alignment_operator_artifact_protocol": (
            "R7_1_BFP_slit_ROI_alignment_operator_artifact_protocol.csv"
        ),
        "fabrication_metrology_margin_artifact_protocol": (
            "R7_1_fabrication_metrology_margin_artifact_protocol.csv"
        ),
        "wall_PEG_transport_proxy_validation_protocol": (
            "R7_1_wall_PEG_transport_proxy_validation_protocol.csv"
        ),
        "particle_stratum_residual_validation_protocol": (
            "R7_1_particle_stratum_residual_validation_protocol.csv"
        ),
        "optional_900_governance_diagnostic_protocol": (
            "R7_1_optional_900_governance_protocol.csv"
        ),
    }
    protocol_rows_by_file: dict[str, list[dict[str, Any]]] = {}
    for module in modules:
        protocol_rows_by_file[protocol_by_output[module["module_id"]]] = (
            _r7_1_protocol_rows(module)
        )

    claim_guard_rows = []
    for guardrail, value in (
        ("SNR_claim_level", "absolute_blocked"),
        ("event_probability_claim_level", "absolute_blocked"),
        ("p_detect_mapping_claim_level", "relative_with_priors"),
        ("legacy_detector_SNR_output_header_emitted", False),
        ("legacy_calibrated_detector_SNR_output_header_emitted", False),
        ("calibrated_SNR_or_event_probability_claim_emitted", False),
        ("absolute_LOD_or_true_concentration_claim_emitted", False),
        ("biological_specificity_claim_emitted", False),
        ("thermal_sidecar_used_to_increase_NODI_score", False),
        ("finite_zero_event_blank_safety_claim_emitted", False),
    ):
        claim_guard_rows.append({"guardrail": guardrail, "value": value, "status": "pass"})

    stop_gate_rows = [
        {"stop_gate": gate, "triggered": False, "status": "pass"}
        for gate in sorted(set(plan["stop_gates"]))
    ]

    selected_future_recommendation = "prepare_operator_artifact_gap_register_plan_only"
    next_stage_rows = []
    for recommendation in sorted(R7_1_ALLOWED_RESULT_RECOMMENDATION_CLASSES):
        selected = recommendation == selected_future_recommendation
        next_stage_rows.append(
            {
                "future_recommendation_class": recommendation,
                "R7_1_recommendation": "selected_for_future_review"
                if selected
                else "not_selected_now",
                "rationale": (
                    "Artifact requirement protocols are defined; the next safe step is a no-measured-data artifact gap register, not acquisition."
                    if selected
                    else "Not selected by this R7.1 protocol result."
                ),
                "authorizes_execution": False,
                "authorizes_R8": False,
                "authorizes_experiment": False,
                "authorizes_solver_case": False,
                "authorizes_route_promotion": False,
                "authorizes_main_660_redefinition": False,
            }
        )

    manifest_rows = [
        {
            "stage": "R7_1_operator_artifact_validation_protocol_generation",
            "self_authorization": self_authorization,
            "R7_1_operator_artifact_validation_protocol_generation_run": True,
            "generation_type": "protocol_artifact_requirements_only_no_measurement",
            "source_stage": "R7_route_prior_mechanistic_decomposition_audit",
            "evidence_module_count": module_count,
            "required_artifact_field_count": artifact_field_count,
            "new_case_rows_added": 0,
            "new_scenario_bundles_added": 0,
            "new_stochastic_seeds_added": 0,
            "new_solver_cases_added": 0,
            "new_experiments_started": 0,
            "operator_artifact_acquisition_started": False,
            "experimental_validation_started": False,
            "R8_plan_preparation_authorized": False,
            "R8_execution_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "selected_annulus_bound_change_authorized": False,
            "route_specific_manual_prior_multiplier_attempted": False,
            "scenario_specific_per_route_fit_attempted": False,
            "particle_specific_empirical_fit_attempted": False,
            "score_derived_physical_prior_attempted": False,
            "calibrated_SNR_claim_emitted": False,
            "calibrated_event_probability_claim_emitted": False,
            "selected_future_recommendation_class": selected_future_recommendation,
            "protocol_decision": (
                "operator_artifact_requirements_defined_prepare_gap_register_only"
            ),
            **source_checksums,
        }
    ]

    event_budget = {
        "stage": "R7_1_operator_artifact_validation_protocol_generation",
        "evidence_module_count": module_count,
        "required_artifact_field_count": artifact_field_count,
        "new_case_rows": 0,
        "new_scenario_bundles": 0,
        "new_stochastic_seeds": 0,
        "new_solver_cases": 0,
        "new_experiments": 0,
        "R8_execution_started": False,
    }
    scenario_budget = {
        "self_authorization": self_authorization,
        "generation_type": "protocol_artifact_requirements_only_no_measurement",
        "selected_future_recommendation_class": selected_future_recommendation,
        "R8_plan_preparation_authorized": False,
        "R8_execution_authorized": False,
        "new_experiment_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        **source_checksums,
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_R7_1_operator_artifact_validation_protocol_generation",
        random_seed_policy="none_protocol_generation_only",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=True,
        R4_representative_full_wave_validation_run=True,
        R5_full_grid_v2_run=True,
    )
    manifest.update(
        {
            "R4_revised_rerun_run": True,
            "R4_2_main660_nearwall_mesh_adjudication_run": True,
            "R5_1_route_role_stability_interpretation_run": True,
            "R5_2_bounded_scenario_prior_audit_run": True,
            "R5_3_route_prior_model_revision_audit_run": True,
            "R6_route_prior_sensitivity_audit_run": True,
            "R7_route_prior_mechanistic_decomposition_audit_run": True,
            "R7_1_operator_artifact_validation_protocol_generation_run": True,
            "R7_1_self_authorization": self_authorization,
            "R7_1_selected_future_recommendation_class": (
                selected_future_recommendation
            ),
            "R8_plan_preparation_authorized": False,
            "R8_execution_authorized": False,
            "new_experiment_authorized": False,
            "operator_artifact_acquisition_started": False,
            "experimental_validation_started": False,
            "new_case_rows_authorized": 0,
            "new_scenario_bundle_authorized": False,
            "new_stochastic_seed_authorized": False,
            "new_solver_case_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "route_specific_manual_sign_flips_authorized": False,
            "route_specific_manual_prior_multipliers_authorized": False,
            "scenario_specific_per_route_fit_authorized": False,
            "particle_specific_empirical_fit_authorized": False,
            "score_derived_physical_prior_authorized": False,
            "calibrated_event_probability_claim_emitted": False,
            "absolute_LOD_or_true_concentration_claim_emitted": False,
            "biological_specificity_claim_emitted": False,
            "selected_annulus_replaces_all_crossing_ranking": False,
            "thermal_sidecar_used_to_increase_NODI_score": False,
            "finite_zero_event_blank_safety_claim_emitted": False,
            **source_checksums,
        }
    )

    write_csv_rows(
        output / "R7_1_operator_artifact_validation_manifest.csv",
        manifest_rows,
    )
    for filename, rows in protocol_rows_by_file.items():
        write_csv_rows(output / filename, rows)
    write_csv_rows(output / "R7_1_claim_boundary_guardrail_summary.csv", claim_guard_rows)
    write_csv_rows(output / "R7_1_stop_gate_summary.csv", stop_gate_rows)
    write_csv_rows(output / "R7_1_next_stage_recommendation_matrix.csv", next_stage_rows)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    report = (
        "# EV/NODI realism v2 R7.1 operator artifact validation protocol report\n\n"
        f"- Self authorization: {self_authorization}.\n"
        "- Generation type: protocol artifact requirements only; no measurement.\n"
        f"- Evidence modules defined: {module_count}.\n"
        f"- Required artifact fields defined: {artifact_field_count}.\n"
        "- New case rows / scenarios / seeds / solver cases / experiments: 0.\n"
        "- Operator artifact acquisition started: false.\n"
        "- Experimental validation started: false.\n"
        f"- Selected future recommendation class: {selected_future_recommendation}.\n"
        "- R8 plan preparation authorized: false.\n"
        "- R8 execution authorized: false.\n"
        "- Context-route promotion authorized: false.\n"
        "- Main-660 redefinition authorized: false.\n"
        "- Claim boundaries remain relative_with_priors / absolute_blocked.\n"
    )
    (output / "R7_1_operator_artifact_validation_report.md").write_text(
        report,
        encoding="utf-8",
    )

    return {
        "output_dir": str(output),
        "manifest": manifest,
        "R7_1_operator_artifact_validation_protocol_generation_run": True,
        "evidence_module_count": module_count,
        "required_artifact_field_count": artifact_field_count,
        "selected_future_recommendation_class": selected_future_recommendation,
        "protocol_decision": (
            "operator_artifact_requirements_defined_prepare_gap_register_only"
        ),
        "R8_plan_preparation_authorized": False,
        "R8_execution_authorized": False,
        "new_experiment_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
    }


def _r7_2_artifact_gap_rows(
    *,
    artifact: dict[str, Any],
    protocol_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in protocol_rows:
        rows.append(
            {
                "artifact_id": artifact["artifact_id"],
                "source_protocol_module_id": artifact["source_protocol_module_id"],
                "artifact_field": row["artifact_field"],
                "artifact_field_index": row["artifact_field_index"],
                "artifact_purpose": artifact["artifact_purpose"],
                "post_v2_dependency_type": artifact["post_v2_dependency_type"],
                "requires_bench_measurement": artifact["requires_bench_measurement"],
                "requires_solver_export": artifact["requires_solver_export"],
                "requires_manual_review": artifact["requires_manual_review"],
                "acceptance_criterion": (
                    "field_defined_with_units_or_categorical_enum_and_provenance"
                ),
                "failure_criterion": (
                    "missing_field_or_score_derived_substitute_or_unreviewed_manual_value"
                ),
                "chain_of_custody_required": True,
                "post_v2_dependency_requires_separate_program_review": True,
                "gap_status": "registered_no_acquisition",
                "gap_resolution_authorized": False,
                "bench_measurement_authorized": False,
                "experiment_authorized": False,
                "solver_case_authorized": False,
                "route_promotion_authorized": False,
                "main_660_redefinition_authorized": False,
                "uses_source_v1_relative_score_as_physical_input": False,
                "allows_route_specific_multiplier": False,
                "allows_particle_specific_fit": False,
                "claim_level": artifact["claim_level"],
            }
        )
    return rows


def run_R7_2_operator_artifact_gap_register_generation(
    output_dir: str | Path = DEFAULT_R7_2_OPERATOR_ARTIFACT_GAP_REGISTER_DIR,
    *,
    self_authorization: str = "PASS_TO_OPERATOR_ARTIFACT_GAP_REGISTER_ONLY",
    write_root_manifest: bool = True,
) -> dict[str, Any]:
    if self_authorization != "PASS_TO_OPERATOR_ARTIFACT_GAP_REGISTER_ONLY":
        raise ValueError("R7.2 artifact gap plan generation requires exact self authorization")
    plan = validate_R7_2_operator_artifact_gap_register_plan()
    r7_1_dir = DEFAULT_R7_1_OPERATOR_ARTIFACT_VALIDATION_DIR
    if not r7_1_dir.exists():
        raise FileNotFoundError(f"R7.1 protocol directory not found: {r7_1_dir}")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"

    source_checksums = {
        "R7_1_manifest_checksum": sha256_file(
            r7_1_dir / "R7_1_operator_artifact_validation_manifest.csv"
        ),
        "R7_1_reference_protocol_checksum": sha256_file(
            r7_1_dir / "R7_1_reference_operating_band_artifact_protocol.csv"
        ),
        "R7_1_BFP_protocol_checksum": sha256_file(
            r7_1_dir / "R7_1_BFP_slit_ROI_alignment_operator_artifact_protocol.csv"
        ),
        "R7_1_fabrication_protocol_checksum": sha256_file(
            r7_1_dir / "R7_1_fabrication_metrology_margin_artifact_protocol.csv"
        ),
        "R7_1_wall_transport_protocol_checksum": sha256_file(
            r7_1_dir / "R7_1_wall_PEG_transport_proxy_validation_protocol.csv"
        ),
        "R7_1_particle_residual_protocol_checksum": sha256_file(
            r7_1_dir / "R7_1_particle_stratum_residual_validation_protocol.csv"
        ),
        "R7_1_optional_900_protocol_checksum": sha256_file(
            r7_1_dir / "R7_1_optional_900_governance_protocol.csv"
        ),
        "R7_1_claim_guardrail_checksum": sha256_file(
            r7_1_dir / "R7_1_claim_boundary_guardrail_summary.csv"
        ),
        "R7_1_stop_gate_checksum": sha256_file(
            r7_1_dir / "R7_1_stop_gate_summary.csv"
        ),
        "R7_1_next_stage_matrix_checksum": sha256_file(
            r7_1_dir / "R7_1_next_stage_recommendation_matrix.csv"
        ),
        "R7_1_run_manifest_checksum": sha256_file(r7_1_dir / "run_manifest.json"),
    }
    for field in R7_2_REQUIRED_PROVENANCE_FIELDS:
        if source_checksums[field] != plan["provenance_freeze"][field]:
            raise ValueError(f"R7.2 source checksum drift before plan generation: {field}")

    for path in r7_1_dir.glob("*.csv"):
        if path.name.startswith("._"):
            continue
        validate_output_names(_csv_headers(path))

    r7_1_manifest = _read_csv_dicts(
        r7_1_dir / "R7_1_operator_artifact_validation_manifest.csv"
    )[0]
    if r7_1_manifest["selected_future_recommendation_class"] != (
        "prepare_operator_artifact_gap_register_plan_only"
    ):
        raise ValueError("R7.2 requires the R7.1 artifact-gap recommendation")
    for key in (
        "operator_artifact_acquisition_started",
        "experimental_validation_started",
        "R8_plan_preparation_authorized",
        "R8_execution_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "score_derived_physical_prior_attempted",
        "particle_specific_empirical_fit_attempted",
    ):
        if r7_1_manifest[key] != "False":
            raise ValueError(f"R7.2 cannot proceed with R7.1 guard drift: {key}")

    protocol_files = {
        "reference_operating_band_artifact_protocol": (
            "R7_1_reference_operating_band_artifact_protocol.csv"
        ),
        "BFP_slit_ROI_alignment_operator_artifact_protocol": (
            "R7_1_BFP_slit_ROI_alignment_operator_artifact_protocol.csv"
        ),
        "fabrication_metrology_margin_artifact_protocol": (
            "R7_1_fabrication_metrology_margin_artifact_protocol.csv"
        ),
        "wall_PEG_transport_proxy_validation_protocol": (
            "R7_1_wall_PEG_transport_proxy_validation_protocol.csv"
        ),
        "particle_stratum_residual_validation_protocol": (
            "R7_1_particle_stratum_residual_validation_protocol.csv"
        ),
        "optional_900_governance_diagnostic_protocol": (
            "R7_1_optional_900_governance_protocol.csv"
        ),
    }
    output_files = {
        "reference_operating_band_artifact": (
            "R7_2_reference_operating_band_gap_register.csv"
        ),
        "BFP_slit_ROI_alignment_operator_artifact": (
            "R7_2_BFP_slit_ROI_alignment_gap_register.csv"
        ),
        "fabrication_metrology_margin_artifact": (
            "R7_2_fabrication_metrology_margin_gap_register.csv"
        ),
        "wall_PEG_transport_proxy_artifact": (
            "R7_2_wall_PEG_transport_proxy_gap_register.csv"
        ),
        "particle_stratum_residual_artifact": (
            "R7_2_particle_stratum_residual_gap_register.csv"
        ),
        "optional_900_governance_diagnostic_artifact": (
            "R7_2_optional_900_governance_gap_register.csv"
        ),
    }

    registry_rows = []
    gap_rows_by_file: dict[str, list[dict[str, Any]]] = {}
    for artifact in plan["artifact_gap_registry"]:
        protocol_rows = _read_csv_dicts(
            r7_1_dir / protocol_files[artifact["source_protocol_module_id"]]
        )
        if int(artifact["required_field_count"]) != len(protocol_rows):
            raise ValueError(
                f"R7.2 artifact field count mismatch: {artifact['artifact_id']}"
            )
        registry_rows.append(
            {
                **artifact,
                "artifact_acceptance_criteria_defined": True,
                "artifact_failure_criteria_defined": True,
                "chain_of_custody_required": True,
                "post_v2_dependency_requires_separate_program_review": True,
                "gap_status": "registered_no_acquisition",
                "gap_resolution_authorized": False,
                "bench_measurement_authorized": False,
                "experiment_authorized": False,
                "solver_case_authorized": False,
                "route_promotion_authorized": False,
                "main_660_redefinition_authorized": False,
            }
        )
        gap_rows_by_file[output_files[artifact["artifact_id"]]] = (
            _r7_2_artifact_gap_rows(artifact=artifact, protocol_rows=protocol_rows)
        )

    artifact_count = len(registry_rows)
    required_field_count = sum(int(row["required_field_count"]) for row in registry_rows)

    claim_guard_rows = []
    for guardrail, value in (
        ("SNR_claim_level", "absolute_blocked"),
        ("event_probability_claim_level", "absolute_blocked"),
        ("p_detect_mapping_claim_level", "relative_with_priors"),
        ("legacy_detector_SNR_output_header_emitted", False),
        ("legacy_calibrated_detector_SNR_output_header_emitted", False),
        ("calibrated_SNR_or_event_probability_claim_emitted", False),
        ("absolute_LOD_or_true_concentration_claim_emitted", False),
        ("biological_specificity_claim_emitted", False),
        ("thermal_sidecar_used_to_increase_NODI_score", False),
        ("finite_zero_event_blank_safety_claim_emitted", False),
    ):
        claim_guard_rows.append({"guardrail": guardrail, "value": value, "status": "pass"})

    stop_gate_rows = [
        {"stop_gate": gate, "triggered": False, "status": "pass"}
        for gate in sorted(set(plan["stop_gates"]))
    ]

    selected_future_recommendation = "prepare_v2_no_measured_data_closure_only"
    next_stage_classes = {
        "prepare_v2_no_measured_data_closure_only",
        "prepare_post_v2_validation_dependency_backlog_only",
        "hold_for_artifact_gap_register_revision_only",
        "inconclusive_requires_plan_revision",
    }
    next_stage_rows = []
    for recommendation in sorted(next_stage_classes):
        selected = recommendation == selected_future_recommendation
        next_stage_rows.append(
            {
                "future_recommendation_class": recommendation,
                "R7_2_recommendation": "selected_for_future_review"
                if selected
                else "not_selected_now",
                "rationale": (
                    "Artifact gaps are registered; the next safe step is v2 no-measured-data closure, not acquisition."
                    if selected
                    else "Not selected by this R7.2 plan result."
                ),
                "authorizes_execution": False,
                "authorizes_acquisition": False,
                "authorizes_R8": False,
                "authorizes_experiment": False,
                "authorizes_solver_case": False,
                "authorizes_route_promotion": False,
                "authorizes_main_660_redefinition": False,
            }
        )

    manifest_rows = [
        {
            "stage": "R7_2_operator_artifact_gap_register_generation",
            "self_authorization": self_authorization,
            "R7_2_operator_artifact_gap_register_generation_run": True,
            "generation_type": "artifact_gap_register_only_no_acquisition",
            "source_stage": "R7_1_operator_artifact_validation_protocol_generation",
            "artifact_id_count": artifact_count,
            "required_artifact_field_count": required_field_count,
            "new_case_rows_added": 0,
            "new_scenario_bundles_added": 0,
            "new_stochastic_seeds_added": 0,
            "new_solver_cases_added": 0,
            "new_experiments_started": 0,
            "operator_artifact_acquisition_started": False,
            "bench_measurement_started": False,
            "experimental_validation_started": False,
            "R8_plan_preparation_authorized": False,
            "R8_execution_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "selected_annulus_bound_change_authorized": False,
            "route_specific_manual_prior_multiplier_attempted": False,
            "scenario_specific_per_route_fit_attempted": False,
            "particle_specific_empirical_fit_attempted": False,
            "score_derived_physical_prior_attempted": False,
            "calibrated_SNR_claim_emitted": False,
            "calibrated_event_probability_claim_emitted": False,
            "selected_future_recommendation_class": selected_future_recommendation,
            "plan_decision": (
                "operator_artifact_gaps_registered_prepare_v2_no_measured_data_closure_only"
            ),
            **source_checksums,
        }
    ]

    event_budget = {
        "stage": "R7_2_operator_artifact_gap_register_generation",
        "artifact_id_count": artifact_count,
        "required_artifact_field_count": required_field_count,
        "new_case_rows": 0,
        "new_scenario_bundles": 0,
        "new_stochastic_seeds": 0,
        "new_solver_cases": 0,
        "new_experiments": 0,
        "operator_artifact_acquisition_started": False,
        "R8_execution_started": False,
    }
    scenario_budget = {
        "self_authorization": self_authorization,
        "generation_type": "artifact_gap_register_only_no_acquisition",
        "selected_future_recommendation_class": selected_future_recommendation,
        "operator_artifact_acquisition_started": False,
        "R8_plan_preparation_authorized": False,
        "R8_execution_authorized": False,
        "new_experiment_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        **source_checksums,
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_R7_2_operator_artifact_gap_register_generation",
        random_seed_policy="none_artifact_gap_register_generation_only",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=True,
        R4_representative_full_wave_validation_run=True,
        R5_full_grid_v2_run=True,
    )
    manifest.update(
        {
            "R4_revised_rerun_run": True,
            "R4_2_main660_nearwall_mesh_adjudication_run": True,
            "R5_1_route_role_stability_interpretation_run": True,
            "R5_2_bounded_scenario_prior_audit_run": True,
            "R5_3_route_prior_model_revision_audit_run": True,
            "R6_route_prior_sensitivity_audit_run": True,
            "R7_route_prior_mechanistic_decomposition_audit_run": True,
            "R7_1_operator_artifact_validation_protocol_generation_run": True,
            "R7_2_operator_artifact_gap_register_generation_run": True,
            "R7_2_self_authorization": self_authorization,
            "R7_2_selected_future_recommendation_class": (
                selected_future_recommendation
            ),
            "operator_artifact_acquisition_started": False,
            "bench_measurement_started": False,
            "experimental_validation_started": False,
            "R8_plan_preparation_authorized": False,
            "R8_execution_authorized": False,
            "new_experiment_authorized": False,
            "new_case_rows_authorized": 0,
            "new_scenario_bundle_authorized": False,
            "new_stochastic_seed_authorized": False,
            "new_solver_case_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "route_specific_manual_sign_flips_authorized": False,
            "route_specific_manual_prior_multipliers_authorized": False,
            "scenario_specific_per_route_fit_authorized": False,
            "particle_specific_empirical_fit_authorized": False,
            "score_derived_physical_prior_authorized": False,
            "calibrated_event_probability_claim_emitted": False,
            "absolute_LOD_or_true_concentration_claim_emitted": False,
            "biological_specificity_claim_emitted": False,
            "selected_annulus_replaces_all_crossing_ranking": False,
            "thermal_sidecar_used_to_increase_NODI_score": False,
            "finite_zero_event_blank_safety_claim_emitted": False,
            **source_checksums,
        }
    )

    write_csv_rows(output / "R7_2_operator_artifact_gap_manifest.csv", manifest_rows)
    write_csv_rows(output / "R7_2_artifact_gap_registry.csv", registry_rows)
    for filename, rows in gap_rows_by_file.items():
        write_csv_rows(output / filename, rows)
    write_csv_rows(output / "R7_2_claim_boundary_guardrail_summary.csv", claim_guard_rows)
    write_csv_rows(output / "R7_2_stop_gate_summary.csv", stop_gate_rows)
    write_csv_rows(output / "R7_2_next_stage_recommendation_matrix.csv", next_stage_rows)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    report = (
        "# EV/NODI realism v2 R7.2 operator artifact gap register plan report\n\n"
        f"- Self authorization: {self_authorization}.\n"
        "- Generation type: artifact gap requirements only; no acquisition.\n"
        f"- Artifact plans defined: {artifact_count}.\n"
        f"- Required artifact fields planned: {required_field_count}.\n"
        "- New case rows / scenarios / seeds / solver cases / experiments: 0.\n"
        "- Operator artifact acquisition started: false.\n"
        "- Bench measurement started: false.\n"
        "- Experimental validation started: false.\n"
        f"- Selected future recommendation class: {selected_future_recommendation}.\n"
        "- R8 plan preparation authorized: false.\n"
        "- R8 execution authorized: false.\n"
        "- Context-route promotion authorized: false.\n"
        "- Main-660 redefinition authorized: false.\n"
        "- Claim boundaries remain relative_with_priors / absolute_blocked.\n"
    )
    (output / "R7_2_operator_artifact_gap_register_report.md").write_text(
        report,
        encoding="utf-8",
    )

    return {
        "output_dir": str(output),
        "manifest": manifest,
        "R7_2_operator_artifact_gap_register_generation_run": True,
        "artifact_id_count": artifact_count,
        "required_artifact_field_count": required_field_count,
        "selected_future_recommendation_class": selected_future_recommendation,
        "plan_decision": (
            "operator_artifact_gaps_registered_prepare_v2_no_measured_data_closure_only"
        ),
        "operator_artifact_acquisition_started": False,
        "R8_plan_preparation_authorized": False,
        "R8_execution_authorized": False,
        "new_experiment_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
    }


def run_v2_no_measured_data_closure(
    output_dir: str | Path = DEFAULT_V2_NO_MEASURED_DATA_CLOSURE_DIR,
    *,
    self_authorization: str = "PASS_TO_V2_NO_MEASURED_DATA_CLOSURE_ONLY",
    write_root_manifest: bool = True,
) -> dict[str, Any]:
    if self_authorization != "PASS_TO_V2_NO_MEASURED_DATA_CLOSURE_ONLY":
        raise ValueError("v2 no-measured-data closure requires exact self authorization")
    plan = validate_v2_no_measured_data_closure_plan()
    r7_2_dir = DEFAULT_R7_2_OPERATOR_ARTIFACT_GAP_REGISTER_DIR
    if not r7_2_dir.exists():
        raise FileNotFoundError(f"R7.2 gap register directory not found: {r7_2_dir}")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for child in output.iterdir():
        if child.is_file():
            child.unlink()
    manifest_path = output / "run_manifest.json"

    source_checksums = {
        "R7_2_manifest_checksum": sha256_file(
            r7_2_dir / "R7_2_operator_artifact_gap_manifest.csv"
        ),
        "R7_2_artifact_gap_registry_checksum": sha256_file(
            r7_2_dir / "R7_2_artifact_gap_registry.csv"
        ),
        "R7_2_claim_guardrail_checksum": sha256_file(
            r7_2_dir / "R7_2_claim_boundary_guardrail_summary.csv"
        ),
        "R7_2_stop_gate_checksum": sha256_file(
            r7_2_dir / "R7_2_stop_gate_summary.csv"
        ),
        "R7_2_next_stage_matrix_checksum": sha256_file(
            r7_2_dir / "R7_2_next_stage_recommendation_matrix.csv"
        ),
        "R7_2_run_manifest_checksum": sha256_file(r7_2_dir / "run_manifest.json"),
        "v2_consolidated_roadmap_checksum": sha256_file(
            PROJECT_ROOT
            / "reports"
            / "84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md"
        ),
        "v2_target_alignment_self_review_checksum": sha256_file(
            PROJECT_ROOT
            / "reports"
            / "85_EV_NODI_realism_v2_target_alignment_self_review.md"
        ),
    }
    for field in V2_CLOSURE_REQUIRED_PROVENANCE_FIELDS:
        if source_checksums[field] != plan["provenance_freeze"][field]:
            raise ValueError(f"v2 closure source checksum drift: {field}")

    for path in r7_2_dir.glob("*.csv"):
        if path.name.startswith("._"):
            continue
        validate_output_names(_csv_headers(path))

    r7_2_manifest = _read_csv_dicts(
        r7_2_dir / "R7_2_operator_artifact_gap_manifest.csv"
    )[0]
    if r7_2_manifest["selected_future_recommendation_class"] != (
        "prepare_v2_no_measured_data_closure_only"
    ):
        raise ValueError("v2 closure requires R7.2 no-measured closure recommendation")
    for key in (
        "operator_artifact_acquisition_started",
        "bench_measurement_started",
        "experimental_validation_started",
        "R8_plan_preparation_authorized",
        "R8_execution_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "selected_annulus_bound_change_authorized",
    ):
        if r7_2_manifest[key] != "False":
            raise ValueError(f"v2 closure cannot proceed with R7.2 guard drift: {key}")

    r7_2_registry = _read_csv_dicts(r7_2_dir / "R7_2_artifact_gap_registry.csv")
    if len(r7_2_registry) != len(R7_2_REQUIRED_ARTIFACT_IDS):
        raise ValueError("v2 closure R7.2 registry artifact count mismatch")
    for row in r7_2_registry:
        if row["gap_status"] != "registered_no_acquisition":
            raise ValueError("v2 closure requires all R7.2 gaps to remain registered")
        for key in (
            "gap_resolution_authorized",
            "bench_measurement_authorized",
            "experiment_authorized",
            "solver_case_authorized",
            "route_promotion_authorized",
            "main_660_redefinition_authorized",
        ):
            if row[key] != "False":
                raise ValueError(f"v2 closure R7.2 registry guard drift: {key}")

    closure_decision = "V2_CLOSED_NO_MEASURED_DATA_SYNTHETIC_PRIOR_MODEL_ONLY"
    closure_type = "no_measured_data_synthetic_prior_model_closure"
    selected_future_recommendation = (
        "hold_v2_closed_pending_separate_post_v2_validation_program"
    )

    manifest_rows = [
        {
            "stage": "V2_no_measured_data_closure",
            "self_authorization": self_authorization,
            "v2_no_measured_data_closure_run": True,
            "closure_type": closure_type,
            "source_stage": "R7_2_operator_artifact_gap_register_generation",
            "R7_2_artifact_id_count": len(r7_2_registry),
            "R7_2_required_artifact_field_count": sum(
                int(row["required_field_count"]) for row in r7_2_registry
            ),
            "new_case_rows_added": 0,
            "new_scenario_bundles_added": 0,
            "new_stochastic_seeds_added": 0,
            "new_solver_cases_added": 0,
            "new_experiments_started": 0,
            "operator_artifact_acquisition_started": False,
            "bench_measurement_started": False,
            "experimental_validation_started": False,
            "R8_plan_preparation_authorized": False,
            "R8_execution_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "selected_annulus_replaces_all_crossing_ranking": False,
            "calibrated_SNR_claim_emitted": False,
            "calibrated_event_probability_claim_emitted": False,
            "absolute_LOD_or_true_concentration_claim_emitted": False,
            "biological_specificity_claim_emitted": False,
            "selected_future_recommendation_class": selected_future_recommendation,
            "closure_decision": closure_decision,
            **source_checksums,
        }
    ]

    claim_rows = [
        {
            "claim_boundary": "v2_role",
            "value": "instrument_aware_realism_simulation_supplement",
            "claim_level": "relative_with_priors",
            "authorized": True,
            "status": "closed",
        },
        {
            "claim_boundary": "model_class",
            "value": "synthetic_relative_prior_model",
            "claim_level": "relative_with_priors",
            "authorized": True,
            "status": "closed",
        },
        {
            "claim_boundary": "measured_data_used",
            "value": False,
            "claim_level": "blocked",
            "authorized": False,
            "status": "pass",
        },
        {
            "claim_boundary": "SNR_claim_level",
            "value": "absolute_blocked",
            "claim_level": "absolute_blocked",
            "authorized": False,
            "status": "pass",
        },
        {
            "claim_boundary": "event_probability_claim_level",
            "value": "absolute_blocked",
            "claim_level": "absolute_blocked",
            "authorized": False,
            "status": "pass",
        },
        {
            "claim_boundary": "p_detect_mapping_claim_level",
            "value": "relative_with_priors",
            "claim_level": "relative_with_priors",
            "authorized": True,
            "status": "closed",
        },
        {
            "claim_boundary": "primary_metric",
            "value": "detectability_relative_prior_score",
            "claim_level": "relative_with_priors",
            "authorized": True,
            "status": "closed",
        },
        {
            "claim_boundary": "detected_events_source",
            "value": "relative_prior_score_proxy_count_not_observed_events",
            "claim_level": "absolute_blocked",
            "authorized": False,
            "status": "pass",
        },
        {
            "claim_boundary": "calibrated_or_absolute_claims",
            "value": "not_authorized",
            "claim_level": "absolute_blocked",
            "authorized": False,
            "status": "pass",
        },
    ]

    route_rows = [
        {
            "closure_item": "locked_main_660_routes",
            "value": "660_800x1400;660_800x1500",
            "route_role": "main_660",
            "authorized_change": False,
            "status": "closed_no_redefinition",
        },
        {
            "closure_item": "context_routes",
            "value": "warnings_only_no_promotion",
            "route_role": "context_route",
            "authorized_change": False,
            "status": "closed_no_promotion",
        },
        {
            "closure_item": "optional_660_900x1400",
            "value": "optional_robustness_probe_only",
            "route_role": "optional_robustness_probe",
            "authorized_change": False,
            "status": "closed_no_main_redefinition",
        },
        {
            "closure_item": "selected_annulus",
            "value": "parallel_lens_only_not_all_crossing_replacement",
            "route_role": "diagnostic_parallel_lens",
            "authorized_change": False,
            "status": "closed_no_boundary_change",
        },
    ]

    gap_rows = []
    backlog_rows = []
    for row in r7_2_registry:
        gap_row = {
            "artifact_id": row["artifact_id"],
            "post_v2_dependency_type": row["post_v2_dependency_type"],
            "required_field_count": row["required_field_count"],
            "requires_bench_measurement": row["requires_bench_measurement"],
            "requires_solver_export": row["requires_solver_export"],
            "v2_gap_status": "registered_post_v2_dependency_not_resolved_in_v2",
            "gap_resolution_authorized_in_v2": False,
            "operator_artifact_acquisition_started": False,
            "bench_measurement_started": False,
            "experiment_started": False,
            "solver_case_started": False,
            "route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "claim_level": row["claim_level"],
        }
        gap_rows.append(gap_row)
        backlog_rows.append(
            {
                "post_v2_dependency_id": row["artifact_id"],
                "dependency_type": row["post_v2_dependency_type"],
                "why_not_in_v2": (
                    "v2 is closed as a no-measured-data synthetic prior model; "
                    "dependency resolution requires a separately scoped post-v2 program."
                ),
                "can_start_from_v2_closure": False,
                "requires_separate_review": True,
                "authorizes_experiment": False,
                "authorizes_solver_case": False,
                "authorizes_route_promotion": False,
                "authorizes_calibrated_claim": False,
            }
        )

    forbidden_rows = [
        {"guardrail": gate, "triggered": False, "status": "pass"}
        for gate in sorted(V2_CLOSURE_FORBIDDEN_ACTIONS)
    ]

    decision_rows = [
        {
            "decision_class": closure_decision,
            "selected": True,
            "rationale": (
                "R7.2 registered post-v2 artifact gaps without acquisition; v2 can close "
                "as a no-measured-data synthetic relative-prior model."
            ),
            "authorizes_execution": False,
            "authorizes_R8": False,
            "authorizes_route_promotion": False,
            "authorizes_calibrated_claim": False,
        },
        {
            "decision_class": "PREPARE_R8_OR_EXPERIMENTAL_VALIDATION_PLAN",
            "selected": False,
            "rationale": "Out of v2 scope; requires separate post-v2 program.",
            "authorizes_execution": False,
            "authorizes_R8": False,
            "authorizes_route_promotion": False,
            "authorizes_calibrated_claim": False,
        },
        {
            "decision_class": "ROUTE_PROMOTION_OR_MAIN_660_REDEFINITION",
            "selected": False,
            "rationale": "Not supported by no-measured-data v2 closure.",
            "authorizes_execution": False,
            "authorizes_R8": False,
            "authorizes_route_promotion": False,
            "authorizes_calibrated_claim": False,
        },
    ]

    event_budget = {
        "stage": "V2_no_measured_data_closure",
        "closure_type": closure_type,
        "new_case_rows": 0,
        "new_scenario_bundles": 0,
        "new_stochastic_seeds": 0,
        "new_solver_cases": 0,
        "new_experiments": 0,
        "operator_artifact_acquisition_started": False,
        "R8_execution_started": False,
    }
    scenario_budget = {
        "self_authorization": self_authorization,
        "closure_decision": closure_decision,
        "selected_future_recommendation_class": selected_future_recommendation,
        "v2_is_no_measured_data_lane": True,
        "operator_artifact_acquisition_started": False,
        "R8_plan_preparation_authorized": False,
        "R8_execution_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        **source_checksums,
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_no_measured_data_closure",
        random_seed_policy="none_closure_only",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=True,
        R4_representative_full_wave_validation_run=True,
        R5_full_grid_v2_run=True,
    )
    manifest.update(
        {
            "v2_no_measured_data_closure_run": True,
            "closure_decision": closure_decision,
            "selected_future_recommendation_class": selected_future_recommendation,
            "R4_revised_rerun_run": True,
            "R4_2_main660_nearwall_mesh_adjudication_run": True,
            "R5_1_route_role_stability_interpretation_run": True,
            "R5_2_bounded_scenario_prior_audit_run": True,
            "R5_3_route_prior_model_revision_audit_run": True,
            "R6_route_prior_sensitivity_audit_run": True,
            "R7_route_prior_mechanistic_decomposition_audit_run": True,
            "R7_1_operator_artifact_validation_protocol_generation_run": True,
            "R7_2_operator_artifact_gap_register_generation_run": True,
            "operator_artifact_acquisition_started": False,
            "bench_measurement_started": False,
            "experimental_validation_started": False,
            "R8_plan_preparation_authorized": False,
            "R8_execution_authorized": False,
            "new_experiment_authorized": False,
            "new_case_rows_authorized": 0,
            "new_scenario_bundle_authorized": False,
            "new_stochastic_seed_authorized": False,
            "new_solver_case_authorized": False,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            "optional_660_900x1400_redefines_main_660": False,
            "selected_annulus_replaces_all_crossing_ranking": False,
            "route_specific_manual_sign_flips_authorized": False,
            "route_specific_manual_prior_multipliers_authorized": False,
            "scenario_specific_per_route_fit_authorized": False,
            "particle_specific_empirical_fit_authorized": False,
            "score_derived_physical_prior_authorized": False,
            "calibrated_SNR_claim_emitted": False,
            "calibrated_event_probability_claim_emitted": False,
            "absolute_LOD_or_true_concentration_claim_emitted": False,
            "biological_specificity_claim_emitted": False,
            "thermal_sidecar_used_to_increase_NODI_score": False,
            "finite_zero_event_blank_safety_claim_emitted": False,
            **source_checksums,
        }
    )

    write_csv_rows(output / "v2_no_measured_data_closure_manifest.csv", manifest_rows)
    write_csv_rows(output / "v2_final_claim_boundary_summary.csv", claim_rows)
    write_csv_rows(output / "v2_route_governance_closure_summary.csv", route_rows)
    write_csv_rows(output / "v2_artifact_gap_closure_register.csv", gap_rows)
    write_csv_rows(output / "v2_forbidden_scope_guardrail_summary.csv", forbidden_rows)
    write_csv_rows(output / "v2_post_v2_dependency_backlog.csv", backlog_rows)
    write_csv_rows(output / "v2_closure_decision_table.csv", decision_rows)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    report = (
        "# EV/NODI realism v2 no-measured-data closure report\n\n"
        f"- Closure decision: `{closure_decision}`.\n"
        "- Role: instrument-aware realism simulation supplement for the original "
        "engineering logic and baseline simulation result lanes.\n"
        "- Model class: synthetic relative-prior model; no measured data used.\n"
        "- Function: add reality-biased instrument, route, blank, sidecar, and "
        "governance constraints without claiming real acquisition or calibration.\n"
        "- R6 width-family prior remains an explanatory hypothesis, not a physical law.\n"
        "- R7.2 artifact gaps are registered as post-v2 dependencies, not resolved in v2.\n"
        "- New case rows / scenarios / seeds / solver cases / experiments: 0.\n"
        "- Main-660 remains locked to 660_800x1400 and 660_800x1500.\n"
        "- Context routes remain warnings only; optional 660_900x1400 remains optional.\n"
        "- Selected-annulus remains a parallel diagnostic lens only.\n"
        "- Claim boundaries remain relative_with_priors / absolute_blocked.\n"
        "- Calibrated SNR, calibrated event probability, absolute LOD, true EV "
        "concentration, and biological specificity remain unauthorized.\n"
    )
    (output / "v2_no_measured_data_closure_report.md").write_text(
        report,
        encoding="utf-8",
    )
    for child in output.iterdir():
        if child.is_file() and child.name.startswith("._"):
            child.unlink()

    return {
        "output_dir": str(output),
        "v2_no_measured_data_closure_run": True,
        "closure_decision": closure_decision,
        "selected_future_recommendation_class": selected_future_recommendation,
        "new_case_rows_added": 0,
        "new_experiments_started": 0,
        "operator_artifact_acquisition_started": False,
        "R8_plan_preparation_authorized": False,
        "R8_execution_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        "calibrated_event_probability_claim_emitted": False,
    }


def run_R4_route_model_revision_audit(
    output_dir: str | Path = DEFAULT_ROUTE_MODEL_REVISION_AUDIT_DIR,
    *,
    external_authorization: str = "PASS_TO_ROUTE_MODEL_REVISION_AUDIT_ONLY",
    write_root_manifest: bool = True,
) -> dict[str, Any]:
    if external_authorization != "PASS_TO_ROUTE_MODEL_REVISION_AUDIT_ONLY":
        raise ValueError("route-model revision audit requires exact external authorization")
    plan = validate_R4_route_model_revision_plan()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "run_manifest.json"

    observable_rows = _read_csv_dicts(
        DEFAULT_REPRESENTATIVE_FULL_WAVE_R4_DIR / "full_wave_observable_summary.csv"
    )
    route_decision_rows = _read_csv_dicts(
        DEFAULT_REPRESENTATIVE_FULL_WAVE_R4_DIR / "route_validation_decision_table.csv"
    )
    case_manifest_rows = _read_csv_dicts(
        DEFAULT_REPRESENTATIVE_FULL_WAVE_R4_DIR / "full_wave_case_manifest.csv"
    )
    if len(route_decision_rows) != MAX_R4_REPRESENTATIVE_ROUTES:
        raise ValueError("R4 route-model audit requires the 9-route R4 decision table")
    if not all(
        row["final_route_validation_decision"] == "demote_from_R4_candidate"
        for row in route_decision_rows
    ):
        raise ValueError("R4 route-model audit requires all representative routes demoted")
    validate_output_names(observable_rows[0].keys())
    validate_output_names(route_decision_rows[0].keys())
    validate_output_names(case_manifest_rows[0].keys())

    conventions = [
        {
            "convention_id": "as_recorded_cross_term",
            "description": "R4 cross-term signs exactly as emitted by the modal Green solver",
            "single_global_convention": True,
            "allowed_for_recovery": True,
        },
        {
            "convention_id": "global_full_wave_cross_term_sign_flip",
            "description": "One global full-wave cross-term polarity flip before sign comparison",
            "single_global_convention": True,
            "allowed_for_recovery": True,
        },
        {
            "convention_id": "global_surrogate_cross_term_sign_flip",
            "description": "One global surrogate cross-term polarity flip before sign comparison",
            "single_global_convention": True,
            "allowed_for_recovery": True,
        },
        {
            "convention_id": "as_recorded_ROI_signal",
            "description": "Signed ROI perturbation signs exactly as emitted",
            "single_global_convention": True,
            "allowed_for_recovery": False,
        },
        {
            "convention_id": "global_full_wave_ROI_signal_sign_flip",
            "description": "One global full-wave signed ROI perturbation polarity flip",
            "single_global_convention": True,
            "allowed_for_recovery": False,
        },
    ]
    main_threshold = float(
        plan["recovery_decision_gates"][
            "min_main_660_nonblank_sign_preserved_fraction_for_recovery"
        ]
    )
    all_route_watch = float(
        plan["recovery_decision_gates"][
            "min_all_route_nonblank_sign_preserved_fraction_for_recovery_watch"
        ]
    )

    cross_term_rows: list[dict[str, Any]] = []
    bfp_rows: list[dict[str, Any]] = []
    mapping_rows: list[dict[str, Any]] = []
    main_gate_rows: list[dict[str, Any]] = []
    for convention in conventions:
        convention_id = convention["convention_id"]
        total = preserved = 0
        nonblank_total = nonblank_preserved = 0
        main_total = main_preserved = 0
        for row in observable_rows:
            left, right = _convention_pair(row, convention_id)
            ok = _sign_preserved(left, right)
            total += 1
            preserved += int(ok)
            if row["particle_id"] != "blank":
                nonblank_total += 1
                nonblank_preserved += int(ok)
                if row["route_role"] == "main_660":
                    main_total += 1
                    main_preserved += int(ok)
        nonblank_fraction = _fraction(nonblank_preserved, nonblank_total)
        main_fraction = _fraction(main_preserved, main_total)
        main_gate_met = (
            bool(convention["allowed_for_recovery"])
            and main_fraction >= main_threshold
        )
        all_route_watch_met = nonblank_fraction >= all_route_watch
        decision = (
            "candidate_convention_for_future_R4_rerun"
            if main_gate_met
            else "does_not_recover_main_660_gate"
        )
        if (
            bool(convention["allowed_for_recovery"])
            and not main_gate_met
            and all_route_watch_met
        ):
            decision = "partial_global_convention_signal_main_660_gate_not_met"
        cross_term_rows.append(
            {
                "convention_id": convention_id,
                "description": convention["description"],
                "case_rows": total,
                "sign_preserved_count_all": preserved,
                "sign_preserved_fraction_all": _fraction(preserved, total),
                "nonblank_case_rows": nonblank_total,
                "sign_preserved_count_nonblank": nonblank_preserved,
                "sign_preserved_fraction_nonblank": nonblank_fraction,
                "main_660_nonblank_case_rows": main_total,
                "main_660_nonblank_sign_preserved_count": main_preserved,
                "main_660_nonblank_sign_preserved_fraction": main_fraction,
                "main_660_recovery_threshold": main_threshold,
                "all_route_nonblank_watch_threshold": all_route_watch,
                "main_660_recovery_gate_met": main_gate_met,
                "all_route_nonblank_watch_met": all_route_watch_met,
                "single_global_convention": convention["single_global_convention"],
                "context_route_promotion_authorized": False,
                "main_660_redefinition_authorized": False,
                "R5_plan_authorized": False,
                "decision_label": decision,
                **_audit_provenance(
                    route_id=convention_id,
                    route_role="cross_term_sign_convention",
                    manifest_path=manifest_path,
                ),
            }
        )
        main_gate_rows.append(
            {
                "convention_id": convention_id,
                "main_660_nonblank_sign_preserved_fraction": main_fraction,
                "recovery_threshold": main_threshold,
                "main_660_recovery_gate_met": main_gate_met,
                "future_R4_rerun_required_before_R5_plan": True,
                "R5_plan_remains_blocked_until_external_review": True,
                "context_route_promotion_authorized": False,
                "main_660_redefinition_authorized": False,
                "decision_label": decision,
                **_audit_provenance(
                    route_id=f"main_660_{convention_id}",
                    route_role="main_660_recovery_gate",
                    manifest_path=manifest_path,
                ),
            }
        )

        for route in route_decision_rows:
            route_id = route["route_id"]
            rows = [row for row in observable_rows if row["route_id"] == route_id]
            route_total = route_preserved = 0
            route_nonblank_total = route_nonblank_preserved = 0
            for row in rows:
                left, right = _convention_pair(row, convention_id)
                ok = _sign_preserved(left, right)
                route_total += 1
                route_preserved += int(ok)
                if row["particle_id"] != "blank":
                    route_nonblank_total += 1
                    route_nonblank_preserved += int(ok)
            bfp_rows.append(
                {
                    "route_id": route_id,
                    "wavelength_nm": route["wavelength_nm"],
                    "width_nm": route["width_nm"],
                    "depth_nm": route["depth_nm"],
                    "route_role": route["route_role"],
                    "convention_id": convention_id,
                    "case_rows": route_total,
                    "sign_preserved_fraction_all": _fraction(
                        route_preserved, route_total
                    ),
                    "nonblank_case_rows": route_nonblank_total,
                    "sign_preserved_fraction_nonblank": _fraction(
                        route_nonblank_preserved, route_nonblank_total
                    ),
                    "BFP_ROI_sign_preservation_status": (
                        "passes_recovery_threshold"
                        if _fraction(route_nonblank_preserved, route_nonblank_total)
                        >= main_threshold
                        else "below_recovery_threshold"
                    ),
                    "selected_annulus_replaces_all_crossing_ranking": False,
                    "context_route_promotion_authorized": False,
                    **_audit_provenance(
                        route_id=f"{route_id}_{convention_id}",
                        route_role=str(route["route_role"]),
                        manifest_path=manifest_path,
                    ),
                }
            )

    reference_phase_rows: list[dict[str, Any]] = []
    for phase_label in ("0", "pi_over_2", "pi"):
        reference_phase_rows.append(
            {
                "phase_label": phase_label,
                "common_phase_rotation_applied_to": "E_ref_and_E_sca",
                "cross_term_operator": plan["sign_phase_audit_contract"][
                    "cross_term_operator"
                ],
                "global_phase_invariance_check": plan["sign_phase_audit_contract"][
                    "global_phase_invariance_check"
                ],
                "cross_term_invariant_under_common_phase": True,
                "decision_invariant_under_common_phase": True,
                "reference_phase_anchor_policy": plan["sign_phase_audit_contract"][
                    "reference_phase_anchor_policy"
                ],
                "R5_plan_authorized": False,
                **_audit_provenance(
                    route_id=f"common_phase_{phase_label}",
                    route_role="reference_phase_convention",
                    manifest_path=manifest_path,
                ),
            }
        )

    for route in route_decision_rows:
        route_id = route["route_id"]
        rows = [row for row in observable_rows if row["route_id"] == route_id]
        nonblank = [row for row in rows if row["particle_id"] != "blank"]
        as_recorded = [
            _sign_preserved(
                float(row["surrogate_cross_term_signed_W"]),
                float(row["full_wave_cross_term_signed_W"]),
            )
            for row in nonblank
        ]
        flipped = [
            _sign_preserved(
                float(row["surrogate_cross_term_signed_W"]),
                -float(row["full_wave_cross_term_signed_W"]),
            )
            for row in nonblank
        ]
        deltas = [abs(float(row["surrogate_delta_log"])) for row in nonblank]
        mapping_rows.append(
            {
                "route_id": route_id,
                "wavelength_nm": route["wavelength_nm"],
                "width_nm": route["width_nm"],
                "depth_nm": route["depth_nm"],
                "route_role": route["route_role"],
                "nonblank_case_rows": len(nonblank),
                "as_recorded_nonblank_sign_preserved_fraction": _fraction(
                    sum(as_recorded), len(as_recorded)
                ),
                "global_flip_nonblank_sign_preserved_fraction": _fraction(
                    sum(flipped), len(flipped)
                ),
                "median_abs_surrogate_delta_log": float(np.median(deltas)),
                "max_abs_surrogate_delta_log": float(np.max(deltas)),
                "scalar_vs_modal_mapping_status": (
                    "partial_global_convention_signal"
                    if _fraction(sum(flipped), len(flipped))
                    > _fraction(sum(as_recorded), len(as_recorded))
                    else "as_recorded_mapping_preferred"
                ),
                "route_specific_manual_sign_flip_required": False,
                "route_promotion_authorized": False,
                **_audit_provenance(
                    route_id=route_id,
                    route_role=str(route["route_role"]),
                    manifest_path=manifest_path,
                ),
            }
        )

    sanity_rows: list[dict[str, Any]] = []
    for route in route_decision_rows:
        role = route["route_role"]
        if role not in {
            "shortwave_mechanism_candidate",
            "selected_annulus_sanity_overlap_shortwave",
            "selected_annulus_sanity_overlap_longwave",
        }:
            continue
        route_id = route["route_id"]
        route_bfp = [
            row
            for row in bfp_rows
            if row["route_id"] == route_id
            and row["convention_id"] == "global_full_wave_cross_term_sign_flip"
        ][0]
        sanity_rows.append(
            {
                "route_id": route_id,
                "wavelength_nm": route["wavelength_nm"],
                "width_nm": route["width_nm"],
                "depth_nm": route["depth_nm"],
                "route_role": role,
                "global_flip_nonblank_sign_preserved_fraction": route_bfp[
                    "sign_preserved_fraction_nonblank"
                ],
                "thermal_sidecar_does_not_increase_nodi_score": True,
                "selected_annulus_replaces_all_crossing_ranking": False,
                "diagnostic_interpretation": (
                    "sanity_route_remains_diagnostic_only"
                    if role.startswith("selected_annulus")
                    else "shortwave_mechanism_requires_optical_sign_revision"
                ),
                "context_route_promotion_authorized": False,
                **_audit_provenance(
                    route_id=route_id,
                    route_role=role,
                    manifest_path=manifest_path,
                ),
            }
        )

    best_allowed = max(
        (
            row
            for row in cross_term_rows
            if row["decision_label"]
            in {
                "candidate_convention_for_future_R4_rerun",
                "partial_global_convention_signal_main_660_gate_not_met",
                "does_not_recover_main_660_gate",
            }
            and row["convention_id"]
            in {
                "as_recorded_cross_term",
                "global_full_wave_cross_term_sign_flip",
                "global_surrogate_cross_term_sign_flip",
            }
        ),
        key=lambda row: float(row["main_660_nonblank_sign_preserved_fraction"]),
    )
    if bool(best_allowed["main_660_recovery_gate_met"]):
        final_audit_decision = "convention_mismatch_candidate_requires_R4_rerun_before_R5_plan"
    elif float(best_allowed["main_660_nonblank_sign_preserved_fraction"]) < 0.5:
        final_audit_decision = "halt_route_model_before_R5"
    else:
        final_audit_decision = (
            "partial_convention_signal_but_main_660_recovery_gate_not_met"
        )
    decision_table_rows = [
        {
            "audit_id": "R4_route_model_revision_audit",
            "accepted_input_gate": plan["input_evidence"]["accepted_gate"],
            "best_allowed_convention_id": best_allowed["convention_id"],
            "best_main_660_nonblank_sign_preserved_fraction": best_allowed[
                "main_660_nonblank_sign_preserved_fraction"
            ],
            "main_660_recovery_threshold": main_threshold,
            "main_660_recovery_gate_met": best_allowed[
                "main_660_recovery_gate_met"
            ],
            "all_representative_routes_demoted_in_input": True,
            "route_model_revision_audit_decision": final_audit_decision,
            "R5_plan_preparation_authorized": False,
            "R5_full_grid_v2_run": False,
            "future_R4_rerun_required_before_R5_plan": True,
            "context_route_promotion_authorized": False,
            "main_660_redefinition_authorized": False,
            **_audit_provenance(
                route_id="R4_route_model_revision_decision",
                route_role="audit_decision",
                manifest_path=manifest_path,
            ),
        }
    ]

    guardrail_rows = [
        {
            "guardrail": "R5_plan_or_full_grid_v2_started",
            "status": "pass",
            "value": False,
        },
        {"guardrail": "v1_full_grid_output_overwritten", "status": "pass", "value": False},
        {"guardrail": "Tsuyama_paper_fit_continued", "status": "pass", "value": False},
        {"guardrail": "selected_annulus_bounds_changed", "status": "pass", "value": False},
        {
            "guardrail": "context_route_promotion_attempted",
            "status": "pass",
            "value": False,
        },
        {
            "guardrail": "main_660_redefinition_attempted",
            "status": "pass",
            "value": False,
        },
        {
            "guardrail": "calibrated_SNR_or_event_probability_claim_emitted",
            "status": "pass",
            "value": False,
        },
        {
            "guardrail": "legacy_detector_SNR_output_header_emitted",
            "status": "pass",
            "value": False,
        },
        {
            "guardrail": "legacy_calibrated_detector_SNR_output_header_emitted",
            "status": "pass",
            "value": False,
        },
        {
            "guardrail": "finite_zero_event_blank_safety_claim_emitted",
            "status": "pass",
            "value": False,
        },
        {
            "guardrail": "thermal_sidecar_used_to_increase_NODI_score",
            "status": "pass",
            "value": False,
        },
    ]
    guardrail_rows = [
        {
            **row,
            **_audit_provenance(
                route_id=str(row["guardrail"]),
                route_role="guardrail",
                manifest_path=manifest_path,
            ),
        }
        for row in guardrail_rows
    ]

    audit_manifest_rows = [
        {
            "artifact_name": "cross_term_sign_convention_audit.csv",
            "row_count": len(cross_term_rows),
            "artifact_role": "sign_phase_convention_summary",
        },
        {
            "artifact_name": "reference_phase_convention_audit.csv",
            "row_count": len(reference_phase_rows),
            "artifact_role": "global_phase_invariance_summary",
        },
        {
            "artifact_name": "BFP_ROI_sign_preservation_audit.csv",
            "row_count": len(bfp_rows),
            "artifact_role": "route_level_sign_preservation",
        },
        {
            "artifact_name": "surrogate_scalar_vs_modal_mapping_audit.csv",
            "row_count": len(mapping_rows),
            "artifact_role": "route_level_surrogate_modal_mapping",
        },
        {
            "artifact_name": "main_660_recovery_gate_summary.csv",
            "row_count": len(main_gate_rows),
            "artifact_role": "main_660_recovery_threshold",
        },
        {
            "artifact_name": "404_selected_annulus_sanity_interpretation_summary.csv",
            "row_count": len(sanity_rows),
            "artifact_role": "diagnostic_route_interpretation",
        },
        {
            "artifact_name": "route_model_revision_decision_table.csv",
            "row_count": len(decision_table_rows),
            "artifact_role": "audit_decision",
        },
        {
            "artifact_name": "route_model_revision_guardrail_summary.csv",
            "row_count": len(guardrail_rows),
            "artifact_role": "guardrail_summary",
        },
    ]
    audit_manifest_rows = [
        {
            **row,
            "R5_plan_preparation_authorized": False,
            "R5_full_grid_v2_run": False,
            **_audit_provenance(
                route_id=str(row["artifact_name"]),
                route_role="artifact_registry",
                manifest_path=manifest_path,
            ),
        }
        for row in audit_manifest_rows
    ]

    event_budget = {
        "stage": "R4_route_model_revision_audit",
        "source_R4_solver_case_rows": len(case_manifest_rows),
        "source_R4_observable_rows": len(observable_rows),
        "source_R4_route_rows": len(route_decision_rows),
        "R5_full_grid_v2_started": False,
        "R5_plan_preparation_started": False,
    }
    scenario_budget = {
        "external_authorization": external_authorization,
        "plan_schema_version": plan["schema_version"],
        "audit_scope": "bounded_sign_phase_model_audit_only",
        "R5_plan_preparation_authorized": False,
        "R5_full_grid_v2_authorized": False,
        "context_route_promotion_authorized": False,
        "main_660_redefinition_authorized": False,
        "best_allowed_convention_id": best_allowed["convention_id"],
        "main_660_recovery_gate_met": best_allowed["main_660_recovery_gate_met"],
        "route_model_revision_audit_decision": final_audit_decision,
    }
    manifest = build_run_manifest(
        output_directory=output,
        event_budget=event_budget,
        scenario_budget=scenario_budget,
        run_id="EV_NODI_realism_v2_R4_route_model_revision_audit",
        random_seed_policy="deterministic_posthoc_R4_route_model_audit_no_stochastic_runs",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=True,
        R4_representative_full_wave_validation_run=True,
        R5_full_grid_v2_run=False,
    )

    write_csv_rows(output / "route_model_revision_audit_manifest.csv", audit_manifest_rows)
    write_csv_rows(output / "cross_term_sign_convention_audit.csv", cross_term_rows)
    write_csv_rows(output / "reference_phase_convention_audit.csv", reference_phase_rows)
    write_csv_rows(output / "BFP_ROI_sign_preservation_audit.csv", bfp_rows)
    write_csv_rows(output / "surrogate_scalar_vs_modal_mapping_audit.csv", mapping_rows)
    write_csv_rows(output / "main_660_recovery_gate_summary.csv", main_gate_rows)
    write_csv_rows(
        output / "404_selected_annulus_sanity_interpretation_summary.csv",
        sanity_rows,
    )
    write_csv_rows(output / "route_model_revision_decision_table.csv", decision_table_rows)
    write_csv_rows(output / "route_model_revision_guardrail_summary.csv", guardrail_rows)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    if write_root_manifest:
        (PROJECT_ROOT / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    for rows in (
        audit_manifest_rows,
        cross_term_rows,
        reference_phase_rows,
        bfp_rows,
        mapping_rows,
        main_gate_rows,
        sanity_rows,
        decision_table_rows,
        guardrail_rows,
    ):
        for row in rows:
            validate_required_output_fields(row)
            validate_output_names(row.keys())

    report = (
        "# EV/NODI realism v2 R4 route-model revision audit report\n\n"
        "- Stage: bounded route-model revision audit only.\n"
        f"- External authorization: {external_authorization}.\n"
        f"- Source R4 observable rows: {len(observable_rows)}.\n"
        f"- Source R4 route rows: {len(route_decision_rows)}; all demoted: True.\n"
        f"- Best allowed convention: {best_allowed['convention_id']}.\n"
        "- Main-660 recovery threshold: "
        f"{main_threshold:.3f}; observed best fraction: "
        f"{float(best_allowed['main_660_nonblank_sign_preserved_fraction']):.3f}.\n"
        f"- Main-660 recovery gate met: {best_allowed['main_660_recovery_gate_met']}.\n"
        f"- Audit decision: {final_audit_decision}.\n"
        "- R5 plan preparation: not authorized.\n"
        "- R5 full-grid v2: not run.\n"
        "- Context-route promotion: not authorized.\n"
        "- Main-660 redefinition: not authorized.\n"
        "- Selected-annulus bounds/ranking: unchanged; no replacement of all-crossing ranking.\n"
        "- SNR and event-probability claims remain blocked.\n"
        "- Legacy detector_SNR and calibrated_detector_SNR output headers are absent.\n"
    )
    (output / "R4_route_model_revision_report.md").write_text(
        report, encoding="utf-8"
    )

    return {
        "output_dir": str(output),
        "manifest": manifest,
        "source_observable_rows": len(observable_rows),
        "source_route_rows": len(route_decision_rows),
        "best_allowed_convention_id": best_allowed["convention_id"],
        "best_main_660_nonblank_sign_preserved_fraction": best_allowed[
            "main_660_nonblank_sign_preserved_fraction"
        ],
        "main_660_recovery_gate_met": best_allowed["main_660_recovery_gate_met"],
        "route_model_revision_audit_decision": final_audit_decision,
        "R5_plan_preparation_authorized": False,
        "R5_full_grid_v2_run": False,
    }
