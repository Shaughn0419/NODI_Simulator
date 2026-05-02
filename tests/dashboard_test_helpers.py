from copy import deepcopy

import pandas as pd

from nodi_simulator.channel_geometry_model import CHANNEL_GEOMETRY_DIAGNOSTIC_FIELDS
from nodi_simulator.assay_control_matrix import ASSAY_CONTROL_DIAGNOSTIC_FIELDS
from nodi_simulator.bfp_detector_operator import BFP_DETECTOR_OPERATOR_DIAGNOSTIC_FIELDS
from nodi_simulator.control_interpretation import (
    CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS,
)
from nodi_simulator.design_claim_governance import MINIMUM_OUTPUT_SCHEMA_FIELDS
from nodi_simulator.design_metrics import DESIGN_METRIC_DIAGNOSTIC_FIELDS
from nodi_simulator.design_postprocess import EV_DESIGN_POSTPROCESS_FIELDS
from nodi_simulator.electrokinetic_transport import ELECTROKINETIC_DIAGNOSTIC_FIELDS
from nodi_simulator.event_quality_control import EVENT_QC_DIAGNOSTIC_FIELDS
from nodi_simulator.ev_integrity_risk import EV_INTEGRITY_DIAGNOSTIC_FIELDS
from nodi_simulator.ev_reporting_metadata import EV_REPORTING_DIAGNOSTIC_FIELDS
from nodi_simulator.fluidic_network_model import FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS
from nodi_simulator.fluidic_resistance import FLUIDIC_RESISTANCE_DIAGNOSTIC_FIELDS
from nodi_simulator.particle_channel_perturbation import (
    PARTICLE_CHANNEL_PERTURBATION_DIAGNOSTIC_FIELDS,
)
from nodi_simulator.particle_design_library import (
    PARTICLE_DESIGN_LIBRARY_DIAGNOSTIC_FIELDS,
)
from nodi_simulator.reference_field import TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS
from nodi_simulator.reference_operating_point import (
    REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS,
)
from nodi_simulator.recompute_manifest import RECOMPUTE_MANIFEST_DIAGNOSTIC_FIELDS
from nodi_simulator.selection_function import SELECTION_FUNCTION_DIAGNOSTIC_FIELDS
from nodi_simulator.wavelength_comparability import (
    WAVELENGTH_COMPARABILITY_DIAGNOSTIC_FIELDS,
)


EXPECTED_PRECOMPUTE_ENGINEERING_DF_COLUMNS = (
    *MINIMUM_OUTPUT_SCHEMA_FIELDS,
    *EVENT_QC_DIAGNOSTIC_FIELDS,
    *SELECTION_FUNCTION_DIAGNOSTIC_FIELDS,
    *CHANNEL_GEOMETRY_DIAGNOSTIC_FIELDS,
    *ELECTROKINETIC_DIAGNOSTIC_FIELDS,
    *EV_INTEGRITY_DIAGNOSTIC_FIELDS,
    *EV_REPORTING_DIAGNOSTIC_FIELDS,
    *ASSAY_CONTROL_DIAGNOSTIC_FIELDS,
    *CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS,
    *RECOMPUTE_MANIFEST_DIAGNOSTIC_FIELDS,
    *BFP_DETECTOR_OPERATOR_DIAGNOSTIC_FIELDS,
    *PARTICLE_CHANNEL_PERTURBATION_DIAGNOSTIC_FIELDS,
    *TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS,
    *REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS,
    *FLUIDIC_RESISTANCE_DIAGNOSTIC_FIELDS,
    *FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS,
    *PARTICLE_DESIGN_LIBRARY_DIAGNOSTIC_FIELDS,
    *DESIGN_METRIC_DIAGNOSTIC_FIELDS,
    *EV_DESIGN_POSTPROCESS_FIELDS,
    *WAVELENGTH_COMPARABILITY_DIAGNOSTIC_FIELDS,
    "engineering_score",
    "final_engineering_score",
    "engineering_gate_passed",
    "engineering_gate_required_detected_events",
    "detection_rate_wilson_lb",
    "all_crossing_detection_rate",
    "selected_detector_mode_candidate_detection_rate",
    "selected_detector_mode_candidate_fraction",
    "selected_detector_mode_annulus_detection_rate",
    "selected_detector_mode_annulus_fraction",
    "detection_operator_signature",
    "observation_signature",
    "stable_detection_rate",
    "robust_cv_peak_height",
    "mean_peak_to_threshold_ratio",
    "mean_peak_margin_z",
    "mean_local_snr",
    "mean_nodi_transit_bandwidth_Hz",
    "mean_nodi_transit_bandwidth_gain",
    "mean_nodi_bandwidth_limited_fraction",
    "rho_physical_envelope_nominal",
    "rho_physical_envelope_status",
    "reference_width_saturation_status",
    "reference_width_saturation_factor",
    "phase_filter_validity",
    "subwavelength_groove_validity_status",
    "requires_calibration_or_fullwave",
    "na_cutoff_policy",
    "interference_overlap_default_freeze_status",
    "projection_default_freeze_status",
    "delta_phi_gouy_validity",
    "observation_freeze_status",
    "engineering_gate_status_label",
    "engineering_gate_primary_blocker_label",
    "engineering_gate_blocker_summary",
    "design_recommendation_status",
    "design_recommendation_label",
    "paired_detection_rate",
    "strict_paired_detection_rate_wilson_lb",
    "engineering_gate_required_strict_paired_detection_rate",
    "engineering_decision_basis",
    "phase_flip_fraction",
    "mean_positive_peak_height",
    "mean_negative_peak_height",
    "positive_peak_fraction",
    "negative_peak_fraction",
    "phi_projection_rad",
    "phi_sca_material_rad",
    "complex_time_harmonic_convention",
    "interference_conjugation_convention",
    "complex_convention_status",
    "absolute_polarity_claim",
    "active_mie_basis_component",
    "high_NA_collection_warning",
    "vector_validity_status",
    "incident_field_model_for_mie",
    "local_plane_wave_validity",
    "mie_radius_to_beam_waist_ratio",
    "output_claim_level",
    "scattering_normalization_route",
    "K_sca_calibration_status",
    "mie_to_power_chain_status",
    "detector_unit_chain_status",
    "detector_field_units",
    "standard_particle_calibration_data_role",
    "power_chain_absolute_units_available",
    "K_sca_uncertainty_status",
    "K_sca_uncertainty_propagated_to_outputs",
    "standard_particle_uncertainty_budget_status",
    "calibration_design_rank",
    "calibration_held_out_validation_status",
    "fit_parameters_identifiable",
    "calibrated_quantitative_unlocked",
    "noise_model_route",
    "detector_noise_claim_level",
    "noise_terms_schema_version",
    "lockin_ENBW_Hz",
    "photon_shot_noise_term_status",
    "electronics_noise_term_status",
    "rin_noise_term_status",
    "speckle_like_noise_term_status",
    "drift_noise_term_status",
    "lockin_output_noise_term_status",
    "shot_noise_model_status",
    "photon_unit_noise_model_status",
    "detector_saturation_status",
    "dynamic_range_margin",
    "superposition_validity_status",
    "channel_particle_coupling_model",
    "joint_fullwave_required_for_quantitative_phase",
    "background_field_model",
    "background_claim_level",
    "residual_transmitted_leakage_status",
    "particle_family",
    "particle_optical_model",
    "EV_claim_level",
    "EV_ensemble_mode",
    "EV_ensemble_name",
    "particle_uncertainty_budget_status",
    "uncertainty_propagation_mode",
    "uncertainty_propagation_status",
    "particle_material_model_mode",
    "particle_material_uncertainty_status",
    "peak_height_CI_available",
    "interface_correction_mode",
    "interface_api_boundary_status",
    "interface_correction_status",
    "interface_output_sensitivity_status",
    "interface_fullwave_required",
    "count_generation_model",
    "per_event_detectability_boundary",
    "count_prediction_model",
    "count_prediction_status",
    "poisson_arrival_process_status",
    "crossing_conditioned_transport_status",
    "count_rate_confidence_status",
    "accessible_area_m2",
    "volumetric_flow_rate_m3_s",
    "predicted_count_rate_Hz",
    "wall_interaction_status",
    "thermal_pod_model",
    "thermal_pod_model_status",
    "thermal_pod_api_boundary_status",
    "pod_quantitative_amplitude_available",
    "pod_quantitative_route_status",
    "pod_probe_reference_field_status",
    "pod_heat_source_status",
    "pod_roi_sensitivity_derivative_status",
    "pod_signal_sign_source",
    "readout_preset",
    "readout_preset_status",
    "readout_preset_claim_level",
    "readout_sampling_validity",
    "lockin_output_unit_convention",
    "polarity_source",
    "threshold_tail",
    "threshold_calibration_source",
    "threshold_lane_specific_model",
    "raw_blank_trace_bootstrap_status",
    "blank_false_positive_calibration_data_role",
    "colored_noise_false_alarm_status",
)


def assert_precompute_engineering_dataframe_columns(df: pd.DataFrame) -> None:
    for column in EXPECTED_PRECOMPUTE_ENGINEERING_DF_COLUMNS:
        assert column in df.columns


def mock_dashboard_engineering_result() -> dict:
    return {
        "particle_name": "gold_80nm",
        "wavelength_m": 660e-9,
        "width_m": 800e-9,
        "depth_m": 550e-9,
        "score": 0.8,
        "final_engineering_score": 0.55,
        "engineering_score": 0.6,
        "engineering_decision_basis": "paired_channel",
        "engineering_basis_n_detected": 1,
        "engineering_basis_detection_rate": 1 / 3,
        "engineering_basis_detection_rate_wilson_lb": 0.06,
        "engineering_basis_stable_detection_rate": 0.0,
        "engineering_basis_stable_detection_rate_wilson_lb": 0.0,
        "engineering_basis_phase_flip_fraction": 0.0,
        "engineering_basis_phase_flip_fraction_wilson_ub": 0.79,
        "engineering_basis_mean_peak_margin_z": 0.3,
        "engineering_gate_passed": True,
        "engineering_gate_basis": "paired_channel",
        "engineering_gate_failed_count": 0,
        "engineering_gate_reason": "PASS",
        "engineering_gate_status_label": "工程门槛通过",
        "engineering_gate_primary_blocker": "pass",
        "engineering_gate_primary_blocker_label": "已通过",
        "engineering_gate_blocker_summary": "已通过 engineering gate",
        "engineering_gate_guidance": "当前 case 已满足工程门槛，可在 freeze 前继续复核并进入结果整理。",
        "engineering_gate_required_detected_events": 2,
        "engineering_gate_detected_fraction_lb": 0.48,
        "engineering_gate_stable_detection_rate_lb": 0.0,
        "engineering_gate_phase_flip_fraction_ub": 0.79,
        "engineering_gate_mean_peak_margin_z": 0.3,
        "engineering_gate_strict_paired_rate_lb": 0.12,
        "engineering_gate_required_strict_paired_detection_rate": 0.25,
        "design_recommendation_status": "recommended_with_caution",
        "design_recommendation_label": "推荐（需复核）",
        "design_recommendation_guidance": "已通过 engineering gate，但 observation freeze 仍有 caution，建议继续复核后再冻结。",
        "robust_score": 0.7,
        "stable_rate_norm": 0.4,
        "threshold_margin_norm": 0.5,
        "local_snr_norm": 0.45,
        "summary": {
            "n_events": 3,
            "n_detected": 2,
            "detection_rate": 2 / 3,
            "detection_rate_wilson_lb": 0.48,
            "all_crossing_n_events": 3,
            "all_crossing_n_detected": 2,
            "all_crossing_detection_rate": 2 / 3,
            "all_crossing_detection_rate_wilson_lb": 0.48,
            "selected_detector_mode_candidate_source": (
                "event_max_margin_z_above_threshold_before_width_gate"
            ),
            "selected_detector_mode_candidate_margin_z_min": 0.0,
            "selected_detector_mode_candidate_n_events": 2,
            "selected_detector_mode_candidate_n_detected": 2,
            "selected_detector_mode_candidate_fraction": 2 / 3,
            "selected_detector_mode_candidate_detection_rate": 1.0,
            "selected_detector_mode_candidate_detection_rate_wilson_lb": 0.34,
            "selected_detector_mode_annulus_source": (
                "initial_position_edge_norm_annulus_diagnostic_v1"
            ),
            "selected_detector_mode_annulus_edge_norm_min": 0.5,
            "selected_detector_mode_annulus_edge_norm_max": 0.8,
            "selected_detector_mode_annulus_n_events": 1,
            "selected_detector_mode_annulus_n_detected": 1,
            "selected_detector_mode_annulus_fraction": 1 / 3,
            "selected_detector_mode_annulus_detection_rate": 1.0,
            "selected_detector_mode_annulus_detection_rate_wilson_lb": 0.21,
            "selected_detector_mode_annulus_mean_edge_norm": 0.65,
            "stable_detection_rate": 1 / 3,
            "mean_peak_height": 2.0,
            "std_peak_height": 0.5,
            "mean_positive_peak_height": 2.0,
            "mean_negative_peak_height": 1.0,
            "positive_peak_fraction": 0.5,
            "negative_peak_fraction": 0.5,
            "mean_peak_width_s": 0.01,
            "phase_flip_fraction": 0.5,
            "robust_cv_peak_height": 0.32,
            "mean_peak_to_threshold_ratio": 1.6,
            "mean_peak_margin_z": 0.8,
            "mean_transit_time_s": 0.012,
            "mean_local_snr": 3.2,
            "mean_nodi_transit_bandwidth_Hz": 83.3,
            "mean_nodi_transit_bandwidth_gain": 0.74,
            "mean_nodi_bandwidth_limited_fraction": 0.61,
            "single_channel_n_detected": 2,
            "single_channel_detection_rate": 2 / 3,
            "single_channel_detection_rate_wilson_lb": 0.21,
            "single_channel_stable_detection_rate": 1 / 3,
            "single_channel_stable_detection_rate_wilson_lb": 0.06,
            "single_channel_phase_flip_fraction": 0.5,
            "single_channel_phase_flip_fraction_wilson_ub": 0.91,
            "single_channel_mean_peak_margin_z": 0.8,
            "paired_channel_n_detected": 1,
            "paired_channel_detection_rate": 1 / 3,
            "paired_channel_detection_rate_wilson_lb": 0.06,
            "paired_channel_stable_detection_rate": 0.0,
            "paired_channel_stable_detection_rate_wilson_lb": 0.0,
            "paired_channel_phase_flip_fraction": 0.0,
            "paired_channel_phase_flip_fraction_wilson_ub": 0.79,
            "paired_channel_mean_peak_margin_z": 0.3,
            "strict_paired_detection_rate": 1 / 3,
            "strict_paired_detection_rate_wilson_lb": 0.06,
            "paired_detection_rate": 0.5,
            "best_peak_pairing_rate": 0.5,
            "all_heights": [2.0, 1.0],
            "all_signed_heights": [2.0, -1.0],
            "all_widths": [0.01, 0.012],
            "all_peak_to_threshold_ratios": [2.0, 1.2],
            "all_peak_margin_z": [1.0, 0.6],
            "rho_requested": 10.0,
            "rho_physical_envelope_nominal": 8.0,
            "rho_physical_envelope_status": "within_envelope",
            "interference_overlap_default_frozen": False,
            "interference_overlap_default_freeze_status": "review_required_before_freeze",
            "projection_default_frozen": True,
            "projection_default_freeze_status": "default_frozen_active",
            "delta_phi_gouy_validity": "shared_beam_caution",
            "delta_phi_gouy_geometry_width_to_waist_ratio": 2.6666666666666665,
            "delta_phi_gouy_geometry_depth_to_waist_ratio": 1.8333333333333335,
            "observation_freeze_status": "review_required_before_result_freeze",
            "engineering_gate_status_label": "工程门槛通过",
            "engineering_gate_primary_blocker": "pass",
            "engineering_gate_primary_blocker_label": "已通过",
            "engineering_gate_blocker_summary": "已通过 engineering gate",
            "engineering_gate_guidance": "当前 case 已满足工程门槛，可在 freeze 前继续复核并进入结果整理。",
            "design_recommendation_status": "recommended_with_caution",
            "design_recommendation_label": "推荐（需复核）",
            "design_recommendation_guidance": "已通过 engineering gate，但 observation freeze 仍有 caution，建议继续复核后再冻结。",
        },
        "intrinsic": {
            "Csca_m2": 1e-18,
            "theta_det_rad": 0.7,
            "theta_center_rad": 0.8,
            "E_sca_at_det": 0.2,
            "E_sca_ref": 0.4,
            "E_sca_unit_normalized": 0.5,
            "phi_projection_rad": 0.6,
            "phi_sca_material_rad": 0.3,
            "phi_sca_material_parallel_rad": 0.3,
            "phi_sca_material_perpendicular_rad": -0.4,
            "operator_signature": "angle=channel_diffraction|integration=pupil_slit_surrogate|projection=parallel",
            "observation_signature": "angle=channel_diffraction|integration=pupil_slit_surrogate|projection=parallel|reference_model=geometry_scaled",
            "detector_forward_model": "joint_overlap_coherent_surrogate",
            "detector_forward_status": (
                "joint_overlap_requested_scalar_surrogate_fallback"
            ),
            "detector_forward_claim_level": "engineering_detector_forward_surrogate",
            "field_coordinate_measure": "theta_phi_surrogate",
            "field_measure_status": "theta_phi_solid_angle_surrogate",
            "bfp_to_angle_jacobian_applied": False,
            "detector_mask_units": "angle_radian_surrogate",
            "coordinate_frame_mapping": (
                "chip:x_width,y_flow,z_depth|optical_axis:z_depth|bfp:u_x,v_y"
            ),
            "scattering_projection_basis": "parallel",
            "particle_family": "gold",
            "particle_family_status": "explicit_particle_family_diagnostic",
            "particle_optical_model": "homogeneous_mie_sphere",
            "structured_particle_model_status": "not_structured",
            "structured_particle_key": None,
            "structured_particle_preset_name": None,
            "EV_label": None,
            "EV_claim_level": "not_applicable",
            "exosome_biogenesis_claim": "not_applicable",
            "biogenesis_claim": "not_applicable",
            "material_dataset": "materials_db:gold",
            "particle_material_model_mode": "materials_db_tabulated_interpolation",
            "particle_material_dataset_key": "gold",
            "particle_material_dataset_source": "Johnson & Christy 1972",
            "particle_material_dataset_type": "tabulated",
            "particle_material_wavelength_status": (
                "materials_db_interpolation_range_checked"
            ),
            "particle_material_temperature_correction_status": (
                "not_applied_room_temperature_nominal"
            ),
            "particle_material_uncertainty_status": (
                "not_quantified_material_dataset_nominal"
            ),
            "metal_size_damping": "off",
            "metal_size_damping_status": "not_applied",
            "ligand_shell": "none",
            "ligand_shell_status": "not_modeled",
            "medium_dispersion": "materials_db_or_constant_runtime",
            "medium_dispersion_status": (
                "runtime_material_db_or_constant_no_uncertainty"
            ),
            "wall_dispersion": "materials_db_or_constant_runtime",
            "wall_dispersion_status": "runtime_material_db_or_constant_no_uncertainty",
            "shape_model": "sphere",
            "anisotropic_shell_model": "not_applicable",
            "orientation_average_status": "not_applicable_spherical_particle",
            "shape_uncertainty_status": "homogeneous_sphere_nominal",
            "EV_sample_preparation_status": "not_applicable",
            "EV_isolation_method": None,
            "EV_aggregation_or_coisolate_status": "not_modeled",
            "EV_ensemble_mode": "nominal_single_preset",
            "EV_ensemble_status": "nominal_single_preset_no_hidden_sampling",
            "EV_core_RI_nominal": None,
            "EV_shell_RI_nominal": None,
            "EV_shell_thickness_m": None,
            "EV_uncertainty_inputs": ["size", "material_RI"],
            "size_distribution_uncertainty": "not_propagated",
            "core_RI_uncertainty": None,
            "shell_RI_uncertainty": None,
            "shell_thickness_uncertainty": None,
            "anisotropy_uncertainty": None,
            "shape_uncertainty": "sphere_assumed",
            "corona_coisolate_uncertainty": None,
            "isolation_batch_uncertainty": None,
            "particle_uncertainty_budget_model": "nominal_only",
            "particle_uncertainty_budget_status": "nominal_only_uncertainty_not_propagated",
            "uncertainty_propagation_mode": "none",
            "uncertainty_inputs": ["size", "material_RI"],
            "uncertainty_outputs": "not_propagated_to_peak_or_detection_confidence",
            "uncertainty_output_confidence_status": "no_particle_uncertainty_CI",
            "peak_height_CI_available": False,
            "detection_rate_CI_available": False,
            "count_rate_CI_available": False,
            "classification_probability_CI_available": False,
            "interface_correction_mode": "off",
            "interface_correction_status": "homogeneous_medium_mie_no_interface_correction",
            "interface_correction_priority": "EV_first",
            "interface_correction_applied_to": "all_particles",
            "interface_correction_particle_family": "gold",
            "interface_correction_active": False,
            "interface_incident_field_correction": "unmodeled",
            "interface_particle_polarizability_correction": "unmodeled",
            "interface_radiation_pattern_collection_correction": "unmodeled",
            "interface_correction_claim_level": "homogeneous_medium_approximation",
            "interface_output_sensitivity_status": (
                "phase_polarity_and_angular_pattern_sensitive"
            ),
            "interface_phase_or_polarity_sensitive_output": True,
            "interface_angular_pattern_sensitive_output": True,
            "interface_dipole_surrogate_validity": "not_applied",
            "interface_quantitative_claim_blocker_summary": (
                "homogeneous_medium_interface_unmodeled; "
                "phase_polarity_or_angular_pattern_requires_interface_solver"
            ),
            "homogeneous_medium_mie_assumption": True,
            "nearest_wall_gap_nominal_m": 1.95e-7,
            "lambda_medium_m": 4.962406015037594e-7,
            "eta_interface": 0.20512820512820512,
            "eta_lambda": 0.0806060606060606,
            "interface_fullwave_required": True,
            "interface_fullwave_reason": "phase_polarity_or_angular_pattern_output",
            "interface_escalation_route": "planar_interface_tmatrix_or_fullwave",
            "conditional_detection_rate": 2 / 3,
            "conditional_detection_rate_definition": "given_one_particle_event",
            "count_generation_model": "per_event_batch_plus_optional_poisson_flux",
            "per_event_detectability_boundary": (
                "conditional_detection_rate_not_experiment_count_rate"
            ),
            "count_prediction_model": "not_applied",
            "count_prediction_status": "not_applied_per_event_detection_only",
            "count_prediction_claim_level": "per_event_only",
            "number_concentration_m3": None,
            "count_observation_window_s": 0.2,
            "accessible_area_m2": 3.384e-13,
            "accessible_area_status": "hard_exclusion_accessible_area",
            "volumetric_flow_rate_m3_s": 6.768e-17,
            "volumetric_flow_rate_source": (
                "mean_flow_velocity_times_hard_exclusion_accessible_area"
            ),
            "poisson_arrival_process_status": "not_applied_count_prediction_disabled",
            "flux_conditioned_initial_distribution_status": (
                "not_implemented_event_positions_sampled_by_transport_surrogate"
            ),
            "crossing_conditioned_transport_status": (
                "not_implemented_uses_existing_per_event_initial_distribution"
            ),
            "event_rate_Hz": None,
            "expected_events_in_window": None,
            "detected_event_rate_before_deadtime_Hz": None,
            "predicted_count_rate_Hz": None,
            "predicted_counts_in_window": None,
            "missed_event_rate_Hz": None,
            "count_dead_time_s": 0.0,
            "dead_time_model": None,
            "dead_time_limited_count_rate_Hz": None,
            "dead_time_loss_fraction": None,
            "blank_false_positive_rate_Hz": 0.0,
            "blank_false_positive_correction_status": (
                "not_applied_no_empirical_blank_rate"
            ),
            "missed_event_correction_status": "not_applied_without_count_prediction",
            "multi_occupancy_window_s": 0.012,
            "focus_occupancy_mean": None,
            "multi_occupancy_probability": None,
            "occupancy_correction_status": "not_evaluated_without_count_prediction",
            "dead_time_correction_status": "not_applied_without_count_prediction",
            "single_particle_condition_status": "not_evaluated",
            "wall_interaction_model": "none",
            "wall_interaction_status": "wall_interaction_unmodeled",
            "zeta_potential_particle_mV": None,
            "zeta_potential_wall_mV": None,
            "ionic_strength_M": None,
            "adsorption_probability_per_length_m": 0.0,
            "adsorption_or_clogging_exclusion_status": "not_modeled",
            "count_rate_source": "not_predicted",
            "count_rate_confidence_status": (
                "not_available_no_blank_false_positive_or_uncertainty_propagation"
            ),
            "count_prediction_uncertainty_status": "not_propagated",
            "control_interpretation_schema": "control_interpretation_risk_v1",
            "control_interpretation_status": (
                "risk_interpretation_scaffold_active_missing_controls"
            ),
            "control_interpretation_claim_level": (
                "interpretation_risk_only_no_control_outcome_claim"
            ),
            "control_interpretation_required_controls": (
                "detergent_lysis",
                "EV_depleted",
                "filtration",
                "proteinase",
                "spike_in",
                "dilution",
            ),
            "control_interpretation_missing_controls": (
                "detergent_lysis",
                "EV_depleted",
                "filtration",
                "proteinase",
                "spike_in",
                "dilution",
            ),
            "control_failure_interpretation": {
                "detergent_lysis": (
                    "lysis_failure_or_nonvesicular_artifact_can_mimic_EV_optical_signal"
                ),
                "EV_depleted": (
                    "depletion_failure_or_coisolate_bias_limits_EV_specificity"
                ),
                "filtration": (
                    "filtration_artifact_can_be_misread_as_EV_size_or_RI_signature"
                ),
                "proteinase": (
                    "proteinase_nonresponse_does_not_prove_non_EV_optical_origin"
                ),
                "spike_in": (
                    "spike_failure_limits_recovery_specificity_and_calibration_claims"
                ),
                "dilution": (
                    "nonlinear_dilution_can_masquerade_as_population_or_detection_limit"
                ),
            },
            "control_failure_interpretation_risk_table": {},
            "control_failure_interpretation_high_risk_controls": (
                "detergent_lysis",
                "EV_depleted",
                "spike_in",
                "dilution",
            ),
            "control_failure_interpretation_gate_passed": False,
            "control_interpretation_blocker_summary": (
                "control_outcome_data_not_ingested / detergent_lysis_missing"
            ),
            "fluidic_network_schema": "fluidic_network_diagnostic_v1",
            "fluidic_network_model_status": "partial_network_nanochannel_array_only",
            "fluidic_network_claim_level": (
                "diagnostic_only_no_measured_pressure_flow_relation"
            ),
            "fluidic_network_component_table": (),
            "fluidic_network_component_count": 5,
            "fluidic_network_known_component_ids": ("nanochannel_parallel_array",),
            "fluidic_network_missing_component_inputs": (
                "fluidic_microchannel_length_m",
                "fluidic_capillary_length_m",
                "inlet_outlet_access_loss_calibration",
                "reservoir_or_vial_boundary_calibration",
                "measured_pressure_flow_trace",
            ),
            "fluidic_parallel_channel_count": 1,
            "fluidic_network_per_channel_flow_rate_m3_s": 8.8e-17,
            "fluidic_network_total_flow_rate_m3_s": 8.8e-17,
            "fluidic_network_nanochannel_array_resistance_Pa_s_m3": 1.0e23,
            "fluidic_network_known_series_resistance_Pa_s_m3": 1.0e23,
            "fluidic_network_known_pressure_drop_for_target_velocity_Pa": 8.8e6,
            "fluidic_network_nanochannel_resistance_fraction": 1.0,
            "fluidic_network_external_geometry_status": (
                "external_network_geometry_incomplete"
            ),
            "fluidic_network_pressure_flow_relation_status": (
                "blocked_until_measured_pressure_flow_trace"
            ),
            "fluidic_network_measured_flow_available": False,
            "fluidic_network_fixed_pressure_prediction_allowed": False,
            "fluidic_network_gate_passed": False,
            "fluidic_network_blocker_summary": (
                "pressure_flow_relation_not_calibrated / measured_pressure_flow_trace"
            ),
            "complex_time_harmonic_convention": "exp_minus_i_omega_t",
            "fourier_transform_sign_convention": "forward_exp_minus_i_q_x",
            "mie_amplitude_phase_convention": "miepython_S1S2_complex",
            "interference_conjugation_convention": "Re_Eref_conj_Esca",
            "interference_cross_term_convention": "2*Re(E_ref*conj(E_sca))",
            "global_phase_offset_source": "unmeasured_zero_reference",
            "absolute_polarity_claim": "not_available_without_measured_global_phase_offset",
            "complex_convention_status": "frozen_surrogate_convention",
            "complex_field_claim_level": "relative_complex_surrogate_not_absolute_phase",
            "polarization_basis_model": "scalar_parallel_perpendicular_surrogate",
            "jones_basis_status": "not_applied_scalar_projection",
            "vector_optics_mode": "scalar_surrogate",
            "mie_s1_s2_lab_basis_mapping": "parallel->S2,perpendicular->S1",
            "active_mie_basis_component": "S2_complex",
            "S1S2_to_lab_basis_rotation_applied": False,
            "reference_jones_field_defined": False,
            "detector_analyzer_jones_matrix_defined": False,
            "mie_jones_bridge_status": "scalar_S1S2_projection_no_jones_rotation",
            "high_NA_collection_warning": True,
            "vector_validity_status": "scalar_high_NA_caution",
            "incident_field_model_for_mie": "local_plane_wave",
            "local_plane_wave_validity": "valid_for_ranking",
            "mie_particle_radius_m": 2.0e-8,
            "mie_size_parameter": 0.2538,
            "mie_incident_beam_waist_min_m": 8.946666666666666e-7,
            "mie_radius_to_beam_waist_ratio": 0.022354694485842027,
            "mie_field_gradient_across_particle_status": (
                "negligible_for_engineering_ranking"
            ),
            "mie_incident_field_GLMT_required": False,
            "mie_incident_field_fullwave_required": False,
            "mie_incident_field_claim_level": (
                "local_plane_wave_mie_for_engineering_ranking"
            ),
            "mie_illumination_geometry_source": "objective_na_surrogate",
            "mie_illumination_NA": 0.45,
            "mie_incident_field_blocker_summary": "none",
            "calibration_state_machine_version": "partial_calibration_state_v1",
            "calibration_state_machine_status": "partial_lane_calibration_only",
            "output_claim_level": "engineering_ranking",
            "calibrated_quantitative_unlocked": False,
            "output_claim_blocker_summary": (
                "missing_K_sca_standard_calibration / "
                "missing_detector_unit_noise_model / "
                "missing_readout_electronics_calibration / "
                "missing_concentration_to_count_model / "
                "missing_global_phase_offset_calibration"
            ),
            "reference_calibration_level": "reference_not_calibrated_or_surrogate",
            "reference_phase_calibration_level": "phase_unmeasured_zero_or_model_assigned",
            "scattering_normalization_route": "baseline_particle_relative",
            "scattering_normalization_status": "baseline_particle_relative_active",
            "scattering_normalization_claim": "relative_field_units_not_photon_or_detector_units",
            "scattering_calibration_level": "relative_baseline_particle_normalized",
            "baseline_normalization_role": "relative_scattering_scale_anchor_not_absolute_detector_unit",
            "baseline_particle_absolute_scale_restored": False,
            "baseline_normalized_E_sca_allowed_in_photon_unit_route": False,
            "baseline_normalized_E_sca_allowed_in_detector_unit_route": False,
            "E_sca_ref_normalization_role": "divides_detected_scattering_field_for_relative_ranking",
            "K_sca_calibration_status": "not_calibrated",
            "K_sca_scope": "none",
            "K_sca_role": "not_applied",
            "mie_to_power_chain_status": (
                "not_implemented_dCsca_dOmega_not_converted_to_detector_units"
            ),
            "mie_differential_cross_section_source": "mie_dCsca_dOmega_nominal",
            "scattered_power_conversion_status": (
                "not_applied_no_incident_power_density_or_detector_etendue"
            ),
            "detector_field_units": "arbitrary_relative_field_units",
            "detector_voltage_units": "not_calibrated",
            "power_chain_absolute_units_available": False,
            "K_sca_power_chain_role": (
                "not_available_cannot_replace_mie_to_power_chain"
            ),
            "mie_to_power_chain_blocker_summary": (
                "incident_power_density_not_applied / "
                "dCsca_dOmega_not_converted_to_dP_sca_dOmega / "
                "detector_etendue_not_calibrated / "
                "absolute_optical_throughput_not_calibrated / "
                "detector_field_voltage_conversion_not_calibrated / "
                "K_sca_not_available_as_residual_calibration"
            ),
            "standard_particle_calibration_status": "not_calibrated",
            "K_sca_uncertainty_status": (
                "not_propagated_no_standard_particle_uncertainty_budget"
            ),
            "K_sca_uncertainty_required_inputs": (
                "standard_particle_size_distribution; "
                "standard_particle_shape_uncertainty; "
                "standard_particle_ligand_shell; "
                "standard_particle_batch_metadata; "
                "standard_particle_concentration_uncertainty; "
                "standard_particle_material_dataset_uncertainty"
            ),
            "K_sca_uncertainty_propagated_to_outputs": False,
            "standard_particle_uncertainty_budget_status": (
                "missing_standard_particle_uncertainty_budget"
            ),
            "standard_particle_size_distribution_status": "not_provided",
            "standard_particle_shape_uncertainty_status": "not_provided",
            "standard_particle_ligand_shell_status": "not_provided",
            "standard_particle_batch_status": "not_provided",
            "standard_particle_concentration_uncertainty_status": "not_provided",
            "standard_particle_material_dataset_uncertainty_status": (
                "not_uncertainty_quantified"
            ),
            "K_sca_uncertainty_blocker_summary": (
                "missing_standard_particle_size_distribution / "
                "missing_standard_particle_shape_uncertainty / "
                "missing_standard_particle_ligand_shell / "
                "missing_standard_particle_batch_metadata / "
                "missing_standard_particle_concentration_uncertainty / "
                "missing_standard_particle_material_dataset_uncertainty / "
                "K_sca_not_calibrated / "
                "K_sca_uncertainty_not_propagated"
            ),
            "calibration_design_rank": "none",
            "calibration_design_rank_reason": "no_standard_particle_calibration",
            "calibration_standard_count": 0,
            "calibration_wavelength_count": 0,
            "calibration_geometry_count": 0,
            "calibration_held_out_validation_status": (
                "not_available_no_standard_particle_design"
            ),
            "calibration_held_out_error": None,
            "calibration_identifiability_blocker_summary": (
                "no_standard_particle_measurements / "
                "no_multi_wavelength_calibration / "
                "no_multi_geometry_calibration / "
                "no_held_out_validation / "
                "A_ref_K_sca_phase_throughput_gain_not_jointly_identifiable"
            ),
            "calibration_fit_parameter_coupling_status": (
                "A_ref_K_sca_phase_throughput_detector_gain_coupled"
            ),
            "calibration_design_minimum_requirement_status": (
                "not_met_requires_standard_particle_and_held_out_dimension"
            ),
            "fit_parameters_identifiable": False,
            "detector_calibration_level": "surrogate_not_detector_unit",
            "readout_calibration_level": "lockin_surrogate_not_physical_electronics",
            "count_calibration_level": "conditional_event_detection_not_count_rate",
            "noise_model_route": "surrogate",
            "detector_noise_claim_level": "engineering_noise_surrogate_not_detector_unit",
            "detector_signal_unit_convention": "arbitrary_relative_signal_units",
            "absolute_throughput_route": "unit_normalized_surrogate",
            "absolute_throughput_calibrated": False,
            "photon_unit_noise_model": "not_applied",
            "photon_unit_noise_model_status": "not_applied",
            "photon_count_route_active": False,
            "lockin_ENBW_Hz": 250.0,
            "lockin_ENBW_status": "first_order_lockin_surrogate",
            "lockin_ENBW_claim_level": (
                "first_order_surrogate_not_measured_lockin_electronics"
            ),
            "shot_noise_model_status": "intensity_proxy_shot_noise_surrogate",
            "photon_shot_noise_term_status": "intensity_proxy_shot_noise_surrogate",
            "shot_noise_limited_snr": None,
            "electronics_noise_model_status": "disabled",
            "electronics_noise_term_status": "disabled",
            "electronics_noise_limited_snr": None,
            "rin_noise_model_status": "not_applied",
            "rin_noise_term_status": "not_applied",
            "rin_limited_snr": None,
            "speckle_background_noise_model_status": "not_applied",
            "speckle_like_noise_term_status": "not_applied",
            "drift_noise_model_status": "disabled",
            "drift_noise_term_status": "disabled",
            "post_readout_noise_model_status": "disabled",
            "lockin_output_noise_term_status": "disabled",
            "noise_terms_schema_version": "noise_terms_v1",
            "noise_term_quantitative_contribution_status": (
                "not_available_arbitrary_units"
            ),
            "noise_terms": {
                "photon_shot": "intensity_proxy_shot_noise_surrogate",
                "electronics": "disabled",
                "RIN": "not_applied",
                "speckle_like": "not_applied",
                "drift": "disabled",
                "lockin_output_noise": "disabled",
            },
            "detector_dynamic_range_model": "not_applied",
            "detector_saturation_status": "not_evaluated_no_detector_range",
            "detector_saturation_margin": None,
            "ADC_dynamic_range_status": "not_evaluated_no_adc_range",
            "ADC_dynamic_range_margin": None,
            "dynamic_range_margin": None,
            "blank_trace_noise_model_fit_quality": None,
            "reference_enhancement_gain": 5.0,
            "reference_enhancement_snr_claim": "not_monotonic_without_photon_unit_noise_model",
            "background_field_model": "baseline_subtraction_surrogate",
            "background_field_status": "baseline_subtraction_only_no_explicit_leakage_field",
            "background_claim_level": "engineering_background_surrogate_not_measured_blank",
            "background_subtraction_status": "active",
            "residual_transmitted_leakage_model": "not_applied",
            "residual_transmitted_leakage_status": "not_modeled",
            "transmitted_leakage_model": "not_applied",
            "stray_light_model": "not_applied",
            "stray_light_status": "not_modeled",
            "speckle_like_background_status": "not_applied",
            "blank_trace_provenance": "synthetic_event_background_segment",
            "blank_trace_empirical_available": False,
            "particle_induced_channel_perturbation_model": "not_applied",
            "particle_induced_channel_phase_perturbation_status": "not_modeled_weak_superposition_assumed",
            "independent_superposition_status": "E_ref_plus_E_sca_independent_surrogate",
            "weak_superposition_validity_status": "not_a_fullwave_channel_perturbation_model",
            "superposition_validity_status": "weak_scatterer_valid",
            "E_sca_to_E_ref_amplitude_ratio_estimate": 0.02,
            "extinction_to_beam_area_estimate": 0.001,
            "reference_depletion_fraction_estimate": None,
            "reference_depletion_estimate_status": (
                "not_computed_requires_joint_field_solution"
            ),
            "channel_particle_coupling_model": "independent_superposition",
            "joint_fullwave_required_for_quantitative_phase": False,
            "superposition_validity_claim_level": (
                "engineering_weak_superposition_diagnostic_not_fullwave_validated"
            ),
            "superposition_validity_blocker_summary": (
                "joint_fullwave_channel_particle_solution_not_implemented / "
                "reference_depletion_not_computed_from_field_solution"
            ),
            "nodi_signal_component_model": "scattering_interference_only_surrogate",
            "nodi_signal_component_status": (
                "no_forward_extinction_or_channel_perturbation_component"
            ),
            "nodi_forward_extinction_leakage_status": "not_modeled",
            "nodi_transmitted_leakage_component_status": "not_modeled",
            "nodi_particle_induced_channel_coupling_status": (
                "not_modeled_weak_superposition_assumed"
            ),
            "nodi_signal_component_claim_level": (
                "engineering_scattering_interference_surrogate_not_full_signal_decomposition"
            ),
            "nodi_component_escalation_route": (
                "measured_blank_or_fullwave_required_for_extinction_leakage"
            ),
            "readout_preset": "exploratory_default",
            "readout_preset_status": "exploratory_default_active",
            "readout_preset_claim_level": "exploratory_phase_aware_surrogate",
            "readout_preset_threshold_scope": "shared_single_channel_threshold",
            "readout_shared_threshold_profile": True,
            "readout_lane_specific_thresholds_available": False,
            "readout_preset_frequency_leakage_note": "engineering_default_fixed_crosstalk_constants",
            "readout_paper_time_constant_range_s": None,
            "electronics_demod_phase_policy": "locked_to_event_center",
            "effective_electronics_demod_phase_policy": "locked_to_event_center",
            "readout_reference_phase_source": "configured_constant_phase",
            "readout_polarity": "sign(lockin_output_I)",
            "polarity_source": "optical_and_electronics_phase_mixed",
            "arrival_phase_distribution": "not_modeled_fixed_time_grid",
            "readout_internal_sampling_rate_Hz": 20000.0,
            "readout_output_sampling_rate_Hz": 20000.0,
            "readout_max_lockin_frequency_Hz": 2400.0,
            "readout_sampling_oversampling_ratio": 8.333333333333334,
            "readout_carrier_nyquist_resolved": True,
            "readout_carrier_resolved": False,
            "readout_carrier_resolved_with_margin": False,
            "readout_analytic_demod_used": False,
            "readout_internal_demod_route": "sampled_carrier_demod_on_event_grid",
            "readout_anti_alias_policy": "sampled_grid_nyquist_guard",
            "readout_anti_alias_filter_before_downsample": False,
            "lockin_output_grid_matches_data_logger": False,
            "readout_sampling_validity": "carrier_underresolved",
            "lockin_output_unit_convention": "arbitrary_lockin_output_units",
            "lockin_gain_chain": "mixer_x2_then_first_order_lowpass_no_instrument_gain",
            "lockin_reported_channel": "X",
            "lockin_reported_channel_source": "configured_readout_observable_mode",
            "lockin_measured_voltage_comparable": False,
            "readout_model_claim_level": "lockin_surrogate_not_physical_electronics",
            "pod_source_model_status": "frequency_lane_surrogate_not_thermal_pod_source",
            "nodi_source_model_status": "transient_scattering_surrogate_not_carrier_modulated_source",
            "thermal_pod_model": "unavailable",
            "thermal_pod_model_status": "unavailable_no_heat_diffusion_model",
            "pod_quantitative_amplitude_available": False,
            "pod_quantitative_sign_available": False,
            "pod_quantitative_claim_level": "unavailable_frequency_lane_surrogate_only",
            "pod_quantitative_route_status": (
                "blocked_missing_thermal_forward_model_or_calibration"
            ),
            "pod_amplitude_model_boundary": (
                "frequency_lane_surrogate_not_absolute_photothermal_amplitude"
            ),
            "probe_wavelength_m": 660e-9,
            "excitation_wavelength_m": None,
            "probe_power_W": None,
            "excitation_power_W": None,
            "probe_wavelength_source": "optical.wavelength_m",
            "pod_probe_reference_field_status": (
                "probe_E_ref_E_sca_use_current_optical_wavelength"
            ),
            "probe_coherent_field_group_id": "probe_660nm",
            "excitation_incoherent_power_group_id": None,
            "pod_probe_excitation_wavelength_status": "excitation_wavelength_not_configured",
            "pod_wavelength_grouping_status": "single_probe_no_excitation_configured",
            "multi_wavelength_coherent_addition_policy": "same_probe_wavelength_only",
            "multi_wavelength_power_addition_policy": "excitation_absorption_incoherent_only",
            "probe_excitation_wavelengths_separated": False,
            "probe_wavelength_fields_add_coherently": True,
            "excitation_wavelength_fields_never_add_to_probe_E_ref_E_sca": True,
            "pod_roi_sensitivity_derivative_status": "unavailable",
            "pod_signal_sign_source": "unavailable",
            "pod_thermal_spatial_distribution_status": "ignored",
            "pod_roi_derivative_validity": "unavailable",
            "pod_absorption_cross_section_status": (
                "not_available_no_excitation_wavelength"
            ),
            "pod_excitation_absorption_cross_section_status": (
                "not_available_no_excitation_wavelength"
            ),
            "pod_heat_source_status": (
                "not_available_missing_excitation_wavelength_or_power"
            ),
            "pod_heat_diffusion_status": "not_implemented",
            "pod_solvent_dn_dT_status": "not_configured_by_probe_wavelength",
            "pod_solvent_dn_dT_source": "not_configured",
            "pod_substrate_heat_contribution_status": "not_implemented",
            "pod_detector_responsivity_status": "not_configured_by_probe_wavelength",
            "pod_detector_responsivity_source": "not_configured",
            "pod_spectral_filter_status": "not_configured_by_probe_wavelength",
            "pod_spectral_filter_source": "not_configured",
            "pod_modulation_response_status": "not_implemented",
            "pod_thermal_validation_status": "not_validated",
            "pod_amplitude_quantitative_blocker_summary": (
                "thermal_pod_model_unavailable; excitation_wavelength_missing; "
                "excitation_power_missing; probe_power_missing; "
                "ROI_integrated_dIdtheta_missing; thermal_spatial_distribution_not_coupled; "
                "pod_roi_derivative_not_validated; quantitative_POD_sign_source_missing; "
                "absorption_cross_section_missing; thermal_heat_source_missing; "
                "solvent_dn_dT_missing; detector_responsivity_missing; "
                "spectral_filter_transmission_missing; modulation_response_missing"
            ),
            "threshold_sigma": 5.0,
            "threshold_sigma_nodi": 5.0,
            "threshold_sigma_pod": 5.0,
            "threshold_lane_specific_model": "shared_threshold",
            "threshold_tail": "two_sided",
            "threshold_tail_configured": "two_sided",
            "threshold_tail_status": "matches_detection_mode",
            "threshold_false_alarm_tail_count": 2,
            "threshold_sign": "absolute_magnitude",
            "threshold_polarity_mode": "positive_or_negative_peak",
            "target_false_alarm_rate": 0.05,
            "threshold_from_blank_trace": False,
            "threshold_from_event_background_segment": True,
            "threshold_background_source": "synthetic_event_background_segment",
            "threshold_background_segment_fraction": 0.2,
            "threshold_background_segment_samples": 800,
            "threshold_calibration_source": "gaussian_iid",
            "threshold_calibration_status": "gaussian_iid_surrogate_not_empirical_blank",
            "absolute_threshold_sigma_equivalent": 5.0,
            "positive_threshold_sigma_equivalent": None,
            "gaussian_iid_single_sample_false_alarm_probability": 5.733031437583892e-7,
            "gaussian_iid_background_segment_false_alarm_probability": 0.0004585371773081234,
            "mean_threshold_robust_std": 0.02,
            "mean_pod_threshold_robust_std": 0.02,
            "blank_trace_autocorrelation_time_s": None,
            "effective_independent_samples_per_trace": None,
            "lockin_filter_order": 1,
            "empirical_peak_false_alarm_rate_per_minute": None,
            "empirical_pair_false_alarm_rate_per_minute": None,
            "lane_noise_correlation_coefficient": None,
            "colored_noise_false_alarm_model": "not_applied",
            "colored_noise_false_alarm_status": "not_evaluated_iid_surrogate_only",
            "paired_false_alarm_status": "not_evaluated_no_joint_blank_trace",
            "path_opd_freeze_status": "default_frozen_active",
        },
        "reference": {
            "A_ref": 8.0,
            "g_ref": 1.2,
            "calibration_extrapolated": True,
            "reference_projection_basis": "parallel",
            "reference_effective_basis": "parallel",
            "reference_projection_basis_match": True,
            "reference_projection_coupling_status": "shared_basis_matched",
            "rho_requested": 10.0,
            "rho_physical_envelope_source": "reference_field_amplitude_envelope / g_ref_geometry",
            "rho_physical_envelope_nominal": 8.0,
            "rho_physical_envelope_lower": 4.0,
            "rho_physical_envelope_upper": 16.0,
            "rho_physical_ratio_to_nominal": 1.25,
            "rho_physical_envelope_in_range": True,
            "rho_physical_envelope_status": "within_envelope",
            "reference_diffraction_efficiency_model": "thin_phase_grating:eta0~cos^2(phase_delay/2),eta1~sin^2(phase_delay/2)",
            "reference_diffraction_efficiency_zeroth_order": 0.84,
            "reference_diffraction_efficiency_first_order": 0.16,
            "reference_field_amplitude_envelope_nominal": 3.2,
            "reference_width_saturation_mode": "waveguide_cutoff_surrogate",
            "reference_width_saturation_status": "active_soft_cutoff",
            "reference_width_saturation_factor": 1.6,
            "reference_width_effective_m": 8.0e-7,
            "phase_filter_validity": None,
            "phase_filter_H_over_lambda0": None,
            "phase_filter_delta_ref_rad": None,
            "phase_filter_theta_signed_rad": None,
            "phase_filter_H_over_zR": None,
            "phase_filter_multiple_reflection_warning": None,
            "subwavelength_groove_validity_status": None,
            "finite_length_assumption_status": None,
            "sidewall_scattering_roughness_status": None,
            "evanescent_component_unmodeled": None,
            "groove_waveguide_mode_unmodeled": None,
            "roughness_scatter_unmodeled": None,
            "depth_validity_reason": None,
            "requires_calibration_or_fullwave": None,
            "na_cutoff_active": False,
            "na_cutoff_condition_met": False,
            "na_cutoff_hard_zero_applied": False,
            "na_cutoff_policy": "hard_guardrail",
            "na_cutoff_diff_ratio": 0.62,
            "na_cutoff_na_ratio": 0.68,
            "na_cutoff_NA_collection": 0.9,
            "na_cutoff_W_min_m": 7.333333333333333e-7,
            "interference_overlap_default_frozen": False,
            "interference_overlap_default_freeze_status": "review_required_before_freeze",
            "projection_default_frozen": True,
            "projection_default_freeze_status": "default_frozen_active",
            "delta_phi_gouy_validity": "shared_beam_caution",
            "delta_phi_gouy_geometry_width_to_waist_ratio": 2.6666666666666665,
            "delta_phi_gouy_geometry_depth_to_waist_ratio": 1.8333333333333335,
            "observation_freeze_status": "review_required_before_result_freeze",
            "engineering_gate_status_label": "工程门槛通过",
            "engineering_gate_primary_blocker": "pass",
            "engineering_gate_primary_blocker_label": "已通过",
            "engineering_gate_blocker_summary": "已通过 engineering gate",
            "engineering_gate_guidance": "当前 case 已满足工程门槛，可在 freeze 前继续复核并进入结果整理。",
            "design_recommendation_status": "recommended_with_caution",
            "design_recommendation_label": "推荐（需复核）",
            "design_recommendation_guidance": "已通过 engineering gate，但 observation freeze 仍有 caution，建议继续复核后再冻结。",
        },
    }


def mock_dashboard_breakdown_case() -> dict:
    case = deepcopy(mock_dashboard_engineering_result())
    case.update(
        {
            "score": 0.9,
            "final_engineering_score": -10.2,
            "engineering_score": 0.7,
            "engineering_basis_n_detected": 3,
            "engineering_basis_detection_rate": 0.3,
            "engineering_basis_detection_rate_wilson_lb": 0.12,
            "engineering_basis_stable_detection_rate": 0.1,
            "engineering_basis_stable_detection_rate_wilson_lb": 0.02,
            "engineering_basis_phase_flip_fraction": 0.0,
            "engineering_basis_phase_flip_fraction_wilson_ub": 0.56,
            "engineering_basis_mean_peak_margin_z": 0.45,
            "engineering_gate_passed": False,
            "engineering_gate_failed_count": 2,
            "engineering_gate_reason": "stable_detection_rate<0.30 / phase_flip_fraction>0.40",
            "engineering_gate_status_label": "工程门槛未通过",
            "engineering_gate_primary_blocker": "stable_detection_rate",
            "engineering_gate_primary_blocker_label": "稳定检出率不足",
            "engineering_gate_blocker_summary": "稳定检出率不足 / 其他失败项 2 条",
            "engineering_gate_guidance": "建议优先提升稳定检出率和 pulse 质量，再观察 freeze 是否稳定。",
            "engineering_gate_required_detected_events": 8,
            "engineering_gate_detected_fraction_lb": 0.18,
            "engineering_gate_stable_detection_rate_lb": 0.02,
            "engineering_gate_phase_flip_fraction_ub": 0.56,
            "engineering_gate_mean_peak_margin_z": 0.45,
            "engineering_gate_strict_paired_rate_lb": 0.16,
            "robust_score": 0.8,
            "design_recommendation_status": "physics_ready_gate_blocked",
            "design_recommendation_label": "可研究（门槛未过）",
            "design_recommendation_guidance": "物理侧基本 ready，但尚未通过 engineering gate，建议作为研究候选继续优化。",
        }
    )
    case["physics"] = {
        **case["intrinsic"],
        **case["reference"],
        "detection_operator_signature": case["intrinsic"]["operator_signature"],
        "reference_model_precision_tier": "legacy_empirical_fallback",
        "reference_model_role": "legacy_fallback_only",
        "reference_geometry_depth_exponent": 1.0,
        "reference_geometry_depth_scaling_class": "amplitude_like",
        "interference_overlap_default_frozen": True,
        "interference_overlap_default_freeze_status": "default_frozen_active",
        "projection_default_frozen": False,
        "projection_default_freeze_status": "review_required_before_freeze",
        "delta_phi_gouy_validity": "shared_beam_caution",
        "delta_phi_gouy_geometry_width_to_waist_ratio": 4.0,
        "delta_phi_gouy_geometry_depth_to_waist_ratio": 2.2,
        "observation_freeze_status": "review_required_before_result_freeze",
        "engineering_gate_status_label": "工程门槛未通过",
        "engineering_gate_primary_blocker": "stable_detection_rate",
        "engineering_gate_primary_blocker_label": "稳定检出率不足",
        "engineering_gate_blocker_summary": "稳定检出率不足 / 其他失败项 2 条",
        "engineering_gate_guidance": "建议优先提升稳定检出率和 pulse 质量，再观察 freeze 是否稳定。",
        "design_recommendation_status": "physics_ready_gate_blocked",
        "design_recommendation_label": "可研究（门槛未过）",
        "design_recommendation_guidance": "物理侧基本 ready，但尚未通过 engineering gate，建议作为研究候选继续优化。",
        "fluidic_network_model_status": "partial_network_nanochannel_array_only",
        "fluidic_network_claim_level": (
            "diagnostic_only_no_measured_pressure_flow_relation"
        ),
        "fluidic_network_external_geometry_status": "external_network_geometry_incomplete",
        "fluidic_network_pressure_flow_relation_status": (
            "blocked_until_measured_pressure_flow_trace"
        ),
        "fluidic_network_gate_passed": False,
        "fluidic_network_blocker_summary": (
            "pressure_flow_relation_not_calibrated / measured_pressure_flow_trace"
        ),
    }
    return case


def build_freeze_probe_fixture_cases() -> tuple[dict, dict]:
    ready = deepcopy(mock_dashboard_engineering_result())
    ready["particle_name"] = "gold_60nm"
    ready["width_m"] = 1200e-9
    ready["depth_m"] = 700e-9
    ready["score"] = 1.1
    ready["final_engineering_score"] = 1.3
    ready["reference"]["A_ref"] = 6.0
    ready["summary"]["mean_reference_to_scattering_amplitude_ratio"] = 18.0
    ready["summary"]["mean_interference_overlap_factor_abs"] = 0.92
    ready["summary"]["observation_freeze_status"] = "default_ready_for_result_freeze"
    ready["summary"]["delta_phi_gouy_validity"] = "shared_beam_acceptable"
    ready["summary"]["rho_physical_envelope_status"] = "within_envelope"
    ready["summary"]["projection_default_freeze_status"] = "default_frozen_active"
    ready["summary"]["interference_overlap_default_freeze_status"] = "default_frozen_active"
    ready["summary"]["path_opd_freeze_status"] = "default_frozen_active"
    ready["intrinsic"]["count_prediction_status"] = "poisson_flux_deadtime_surrogate_active"
    ready["intrinsic"][
        "poisson_arrival_process_status"
    ] = "poisson_arrival_process_surrogate_active"

    review = deepcopy(mock_dashboard_engineering_result())
    review["particle_name"] = "gold_80nm"
    review["width_m"] = 500e-9
    review["depth_m"] = 550e-9
    review["score"] = 0.8
    review["final_engineering_score"] = 0.55
    review["reference"]["A_ref"] = 3.5
    review["summary"]["mean_reference_to_scattering_amplitude_ratio"] = 9.0
    review["summary"]["mean_interference_overlap_factor_abs"] = 0.78
    review["summary"]["observation_freeze_status"] = "review_required_before_result_freeze"
    review["summary"]["delta_phi_gouy_validity"] = "shared_beam_caution"
    review["summary"]["rho_physical_envelope_status"] = "above_upper_envelope"
    review["summary"]["projection_default_freeze_status"] = "default_frozen_active"
    review["summary"]["interference_overlap_default_freeze_status"] = "review_required_before_freeze"
    review["summary"]["path_opd_freeze_status"] = "default_frozen_active"
    return review, ready


def assert_freeze_probe_report_contract(report: dict) -> None:
    assert "n_cases" in report
    assert "status_distributions" in report
    assert "width_groups" in report
    assert "top_cases" in report
    assert "sanity_checks" in report


def build_result_health_fixture_frame() -> pd.DataFrame:
    governed_defaults = {
        "detector_forward_model": "joint_overlap_coherent_surrogate",
        "detector_forward_status": (
            "joint_overlap_requested_scalar_surrogate_fallback"
        ),
        "detector_forward_claim_level": "engineering_detector_forward_surrogate",
        "field_coordinate_measure": "theta_phi_surrogate",
        "bfp_to_angle_jacobian_applied": False,
        "coordinate_frame_mapping": (
            "chip:x_width,y_flow,z_depth|optical_axis:z_depth|bfp:u_x,v_y"
        ),
        "output_claim_level": "engineering_ranking",
        "scattering_normalization_route": "baseline_particle_relative",
        "mie_to_power_chain_status": (
            "not_implemented_dCsca_dOmega_not_converted_to_detector_units"
        ),
        "detector_field_units": "arbitrary_relative_field_units",
        "calibration_design_rank": "none",
        "calibration_held_out_validation_status": (
            "not_available_no_standard_particle_design"
        ),
        "vector_validity_status": "scalar_high_NA_caution",
        "high_NA_collection_warning": True,
        "superposition_validity_status": "weak_scatterer_valid",
        "joint_fullwave_required_for_quantitative_phase": False,
        "background_field_status": (
            "baseline_subtraction_only_no_explicit_leakage_field"
        ),
        "residual_transmitted_leakage_status": "not_modeled",
        "readout_preset_status": "exploratory_default_active",
        "readout_sampling_validity": "carrier_underresolved",
        "lockin_output_unit_convention": "arbitrary_lockin_output_units",
        "threshold_tail": "two_sided",
        "threshold_calibration_status": "gaussian_iid_surrogate_not_empirical_blank",
        "colored_noise_false_alarm_status": "not_evaluated_iid_surrogate_only",
        "particle_material_uncertainty_status": (
            "not_quantified_material_dataset_nominal"
        ),
        "particle_uncertainty_budget_status": (
            "nominal_only_uncertainty_not_propagated"
        ),
        "peak_height_CI_available": False,
        "interface_correction_status": "homogeneous_medium_mie_no_interface_correction",
        "interface_output_sensitivity_status": (
            "phase_polarity_and_angular_pattern_sensitive"
        ),
        "interface_fullwave_required": True,
        "thermal_pod_model_status": "unavailable_no_heat_diffusion_model",
        "pod_quantitative_route_status": (
            "blocked_missing_thermal_forward_model_or_calibration"
        ),
        "pod_probe_reference_field_status": (
            "probe_E_ref_E_sca_use_current_optical_wavelength"
        ),
        "pod_heat_source_status": (
            "not_available_missing_excitation_wavelength_or_power"
        ),
        "count_generation_model": "per_event_batch_plus_optional_poisson_flux",
        "per_event_detectability_boundary": (
            "conditional_detection_rate_not_experiment_count_rate"
        ),
        "count_prediction_model": "not_applied",
    }
    return pd.DataFrame(
        [
            {
                **governed_defaults,
                "particle_name": "gold_60nm",
                "particle_material": "gold",
                "wavelength_nm": 660,
                "width_nm": 500,
                "depth_nm": 550,
                "score": 1.0,
                "final_engineering_score": 1.2,
                "engineering_gate_passed": True,
                "observation_freeze_status": "default_ready_for_result_freeze",
                "delta_phi_gouy_validity": "shared_beam_caution",
                "rho_physical_envelope_status": "within_envelope",
                "reference_width_saturation_status": "active_soft_cutoff",
                "reference_width_saturation_factor": 1.20,
                "count_prediction_status": "not_applied_per_event_detection_only",
                "poisson_arrival_process_status": "not_applied_count_prediction_disabled",
                "crossing_conditioned_transport_status": (
                    "not_implemented_uses_existing_per_event_initial_distribution"
                ),
                "count_rate_confidence_status": (
                    "not_available_no_blank_false_positive_or_uncertainty_propagation"
                ),
            },
            {
                **governed_defaults,
                "particle_name": "gold_80nm",
                "particle_material": "gold",
                "wavelength_nm": 660,
                "width_nm": 2000,
                "depth_nm": 550,
                "score": 0.8,
                "final_engineering_score": -9.8,
                "engineering_gate_passed": False,
                "observation_freeze_status": "caution_probe_before_result_freeze",
                "delta_phi_gouy_validity": "shared_beam_acceptable",
                "rho_physical_envelope_status": "within_envelope",
                "reference_width_saturation_status": "active_soft_cutoff",
                "reference_width_saturation_factor": 1.02,
                "count_prediction_status": "not_applied_per_event_detection_only",
                "poisson_arrival_process_status": "not_applied_count_prediction_disabled",
                "crossing_conditioned_transport_status": (
                    "not_implemented_uses_existing_per_event_initial_distribution"
                ),
                "count_rate_confidence_status": (
                    "not_available_no_blank_false_positive_or_uncertainty_propagation"
                ),
            },
            {
                **governed_defaults,
                "particle_name": "exosome_100nm",
                "particle_material": "exosome",
                "wavelength_nm": 532,
                "width_nm": 800,
                "depth_nm": 550,
                "score": 0.7,
                "final_engineering_score": -0.4,
                "engineering_gate_passed": True,
                "observation_freeze_status": "default_ready_for_result_freeze",
                "delta_phi_gouy_validity": "shared_beam_acceptable",
                "rho_physical_envelope_status": "within_envelope",
                "reference_width_saturation_status": "active_soft_cutoff",
                "reference_width_saturation_factor": 1.10,
                "count_prediction_status": "poisson_flux_deadtime_surrogate_active",
                "poisson_arrival_process_status": (
                    "poisson_arrival_process_surrogate_active"
                ),
                "crossing_conditioned_transport_status": (
                    "not_implemented_uses_existing_per_event_initial_distribution"
                ),
                "count_rate_confidence_status": (
                    "not_available_no_blank_false_positive_or_uncertainty_propagation"
                ),
            },
        ]
    )


def assert_result_health_report_contract(report: dict) -> None:
    assert "n_cases" in report
    assert "status_distributions" in report
    assert "recommendation_distribution" in report
    assert "engineering_gate_distribution" in report
    assert "health_slices" in report
    assert "monitoring_summary" in report
    assert "monitoring_guidance" in report
    assert "top_caution_cases" in report
