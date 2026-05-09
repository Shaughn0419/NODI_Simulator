"""
Focused pytest suite for core physics and signal-chain invariants.

Parallel policy:
    - this suite belongs to the xdist non-AppTest pytest lane
    - new tests must remain parallel-safe: no hidden shared mutable state,
      no fixed temp-file collisions, and no ordering dependence
"""

import math
import os
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from nodi_simulator.data_objects import (
    BASELINE_CHANNEL,
    BASELINE_OPTICAL,
    BASELINE_PARTICLE,
    DEFAULT_DESIGN_OBJECTIVE_CONFIG,
    DEFAULT_SIM_CFG,
    WATER,
    Channel,
    DesignObjectiveConfig,
    OpticalSystem,
    Particle,
    SimulationConfig,
    apply_readout_preset,
    make_ev_nodi_design_sweep_config,
    make_gold_baseline_particle,
)
from nodi_simulator.design_claim_governance import (
    MINIMUM_OUTPUT_SCHEMA_FIELDS,
    build_design_claim_governance_diagnostics,
)
from nodi_simulator.design_metrics import (
    DESIGN_METRIC_DIAGNOSTIC_FIELDS,
    attach_anchor_equivalent_metrics,
    attach_fluidic_practicality_metrics,
    attach_reference_operating_metrics,
)
from nodi_simulator.design_postprocess import (
    EV_DESIGN_POSTPROCESS_FIELDS,
    attach_ev_design_postprocess,
)
from nodi_simulator.channel_geometry_model import (
    CHANNEL_GEOMETRY_DIAGNOSTIC_FIELDS,
    build_channel_geometry_diagnostics,
)
from nodi_simulator.assay_control_matrix import (
    ASSAY_CONTROL_DIAGNOSTIC_FIELDS,
    REQUIRED_CONTROL_SAMPLES,
    build_assay_control_matrix_diagnostics,
)
from nodi_simulator.control_interpretation import (
    CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS,
    build_control_interpretation_diagnostics,
)
from nodi_simulator.bfp_detector_operator import (
    BFP_DETECTOR_OPERATOR_DIAGNOSTIC_FIELDS,
    compute_detector_integrated_interference,
)
from nodi_simulator.electrokinetic_transport import (
    ELECTROKINETIC_DIAGNOSTIC_FIELDS,
    build_electrokinetic_transport_diagnostics,
)
from nodi_simulator.event_quality_control import (
    EVENT_QC_DIAGNOSTIC_FIELDS,
    build_event_quality_control_diagnostics,
)
from nodi_simulator.ev_integrity_risk import (
    EV_INTEGRITY_DIAGNOSTIC_FIELDS,
    build_ev_integrity_risk_diagnostics,
)
from nodi_simulator.ev_reporting_metadata import (
    EVPreanalyticalMetadata,
    EV_REPORTING_DIAGNOSTIC_FIELDS,
    build_ev_reporting_metadata_diagnostics,
)
from nodi_simulator.fluidic_resistance import (
    FLUIDIC_RESISTANCE_DIAGNOSTIC_FIELDS,
    compute_fluidic_practicality_penalty,
    compute_rectangular_channel_hydraulic_resistance,
)
from nodi_simulator.fluidic_network_model import (
    FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS,
    build_fluidic_network_diagnostics,
)
from nodi_simulator.particle_channel_perturbation import (
    PARTICLE_CHANNEL_PERTURBATION_DIAGNOSTIC_FIELDS,
    build_particle_channel_perturbation_diagnostics,
)
from nodi_simulator.particle_design_library import (
    EV_SAMPLE_PREPARATION_PROFILES,
    PARTICLE_CONTAMINANT_PRESETS,
    PARTICLE_DESIGN_LIBRARY_DIAGNOSTIC_FIELDS,
    STANDARD_PARTICLE_PRESETS,
    build_particle_design_library_diagnostics,
)
from nodi_simulator.ev_population_prior import (
    EV_POPULATION_PRIOR_DIAGNOSTIC_FIELDS,
    build_ev_population_prior_diagnostics,
)
from nodi_simulator.recompute_manifest import (
    RECOMPUTE_MANIFEST_DIAGNOSTIC_FIELDS,
    build_recompute_manifest_diagnostics,
)
from nodi_simulator.selection_function import (
    SELECTION_FUNCTION_DIAGNOSTIC_FIELDS,
    build_selection_function_diagnostics,
    compute_observed_distribution_correction,
)
from nodi_simulator.seed_robustness import (
    SEED_ROBUSTNESS_DIAGNOSTIC_FIELDS,
    run_seed_replicates,
    summarize_seed_replicate_metrics,
)
from nodi_simulator.count_generation import build_count_model_diagnostics
from nodi_simulator.count_likelihood import (
    COUNT_LIKELIHOOD_DIAGNOSTIC_FIELDS,
    build_count_likelihood_diagnostics,
    log_likelihood_counts,
)
from nodi_simulator.ood_detection import (
    OOD_DIAGNOSTIC_FIELDS,
    build_ood_detection_diagnostics,
)
from nodi_simulator.bayesian_calibration import (
    BAYESIAN_CALIBRATION_DIAGNOSTIC_FIELDS,
    build_bayesian_calibration_scaffold,
)
from nodi_simulator.experimental_design_advisor import (
    EXPERIMENTAL_DESIGN_ADVISOR_FIELDS,
    build_experimental_design_advisor,
)
from nodi_simulator.population_inference import (
    POPULATION_INFERENCE_DIAGNOSTIC_FIELDS,
    build_population_inference_scaffold,
)
from nodi_simulator.calibration_models import (
    build_bfp_roi_mask_contract,
    calibration_contract_summary,
    validate_calibration_table,
)
from nodi_simulator.calibration_plan_advisor import (
    CALIBRATION_PLAN_ADVISOR_FIELDS,
    build_calibration_plan_advisor,
)
from nodi_simulator.interface_correction import build_interface_correction_diagnostics
from nodi_simulator.illumination import compute_illumination_envelope
from nodi_simulator.intrinsic_scattering import compute_intrinsic_scattering
from nodi_simulator.interferometric_trace import generate_interferometric_trace
from nodi_simulator.materials import (
    MATERIAL_DB,
    get_n_complex,
    list_materials,
    material_property_summary,
    material_db_coverage_diagnostics,
)
from nodi_simulator.mie_engine import (
    mie_angular,
    mie_coefficients,
    mie_compute,
    mie_core_shell_coefficients,
)
from nodi_simulator.parameter_sweep import (
    _empty_pulse_features,
    _estimate_transit_time_s,
    _estimate_transit_time_block,
    _estimate_threshold_stats_block,
    _sample_initial_positions_block,
    _build_readout_context,
    _extract_best_peak_summary_block,
    _first_order_lowpass_alpha,
    _iter_case_spec_chunks,
    _resolve_parallel_case_chunk_size,
    add_detector_noise,
    add_post_readout_noise,
    apply_readout_chain,
    compute_engineering_score,
    compute_final_engineering_score,
    evaluate_engineering_gate,
    run_parameter_sweep,
    run_single_case_batch,
    summarize_batch,
    wilson_lower_bound,
    wilson_upper_bound,
)
import nodi_simulator.parameter_sweep as parameter_sweep_module
from nodi_simulator.pulse_analysis import (
    build_pulse_extraction_context,
    estimate_threshold_robust,
    estimate_threshold_stats_robust,
    extract_pulse_features,
)
from nodi_simulator.paper_aligned_profiles import (
    apply_paper_aligned_profile,
    list_paper_aligned_profiles,
)
from nodi_simulator.photothermal_pod import build_photothermal_pod_diagnostics
from nodi_simulator.population_trace_simulator import (
    POPULATION_TRACE_DIAGNOSTIC_FIELDS,
    PopulationTraceConfig,
    simulate_population_trace_from_event_library,
)
from nodi_simulator.run_state_model import (
    RUN_STATE_DIAGNOSTIC_FIELDS,
    build_run_state_diagnostics,
)
from nodi_simulator.nodi_thermal_contamination import (
    NODI_THERMAL_CONTAMINATION_FIELDS,
    build_nodi_thermal_contamination_diagnostics,
)
from nodi_simulator.polarization_jones_operator import (
    POLARIZATION_JONES_DIAGNOSTIC_FIELDS,
    build_polarization_jones_diagnostics,
)
from nodi_simulator.optical_exposure_safety import (
    build_optical_exposure_safety_diagnostics,
)
from nodi_simulator.optical_hardware_profiles import (
    build_objective_profile_diagnostics,
)
from nodi_simulator.objective_panel import (
    OBJECTIVE_PANEL_DIAGNOSTIC_FIELDS,
    evaluate_objective_panel,
)
from nodi_simulator.reference_field import (
    TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS,
    _integrate_masked_bfp_roi,
    compute_reference_field,
    compute_reference_field_from_tsuyama_bfp,
    compute_reference_field_trace,
)
from nodi_simulator.reference_operating_point import (
    REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS,
    build_reference_operating_point_diagnostics,
)
from nodi_simulator.readout_transfer_model import (
    READOUT_TRANSFER_DIAGNOSTIC_FIELDS,
    build_nodi_readout_transfer_diagnostics,
)
from nodi_simulator.scattering_trace import compute_scattering_field_trace
from nodi_simulator.structured_particles import (
    get_exosome_model_preset,
    list_ev_sev_ensemble_presets,
    list_exosome_model_presets,
    make_biomimetic_exosome_ensemble_particles,
    make_biomimetic_exosome_particle,
)
from nodi_simulator.tsuyama_phase_filter import (
    classify_phase_filter_validity,
    compute_tsuyama_phase_filter_bfp_field,
    integrate_bfp_roi,
)
from nodi_simulator.unit_conventions import (
    build_mie_validation_diagnostics,
    build_unit_axis_convention_diagnostics,
)
from nodi_simulator.wavelength_comparability import (
    WAVELENGTH_COMPARABILITY_DIAGNOSTIC_FIELDS,
    build_wavelength_comparability_diagnostics,
)
from nodi_simulator.trajectory import (
    axial_transport_velocity_m_s,
    axial_velocity_m_s,
    build_trajectory_context,
    hindered_diffusion_factors,
    simulate_particle_trajectory,
    simulate_particle_trajectory_block,
)
from nodi_simulator.utils import (
    build_case_decision_summary,
    build_calibration_state_diagnostics,
    build_background_field_diagnostics,
    build_complex_field_convention_diagnostics,
    build_collection_operator,
    build_detector_noise_diagnostics,
    build_interference_overlap_diagnostics,
    build_mie_incident_field_validity_diagnostics,
    build_particle_model_diagnostics,
    build_readout_convention_diagnostics,
    build_threshold_false_alarm_diagnostics,
    classify_design_recommendation,
    classify_engineering_gate_explanation,
    classify_delta_phi_gouy_geometry_validity,
    classify_observation_freeze,
    classify_projection_freeze,
    compute_detected_scattering_field,
    compute_baseline_normalization,
    interpolate_at_theta,
    resolve_collection_theta_rad,
    sample_initial_position,
    validate_simulation_config,
)


THETA_GRID = np.linspace(0.01, np.pi - 0.01, 500)


def _synthetic_design_result(
    name: str,
    *,
    family: str,
    peak: float,
    margin: float,
    stable_rate: float,
    final_score: float = 0.8,
    final_green_eligible: bool = True,
    blocker_summary: str = "pass",
) -> dict:
    summary = {
        "particle_preset_id": name,
        "particle_family": family,
        "particle_radius_m": 10e-9 if name == "gold_20nm" else 50e-9,
        "particle_diameter_m": 20e-9 if name == "gold_20nm" else 100e-9,
        "mean_peak_height": peak,
        "mean_peak_margin_z": margin,
        "stable_detection_rate": stable_rate,
        "phase_flip_fraction": 0.1,
        "engineering_gate_passed": True,
        "final_green_eligible": final_green_eligible,
        "final_recommendation_band": (
            "candidate_design" if final_green_eligible else "exploratory_only"
        ),
        "primary_blocker_summary": blocker_summary,
        "reference_model": "tsuyama_bfp_integrated",
        "reference_solver_route": "tsuyama_bfp_integrated",
        "readout_preset": "ev_nodi_design_sweep",
        "detector_forward_model": "roi_complex_mode_overlap_integral",
        "reference_design_width_rank_metric": 0.5,
        "reference_operating_band": "balanced",
        "fluidic_practicality_penalty": 0.2,
        "EV_to_contaminant_signal_overlap": 0.25,
        "particle_optical_model": "core_shell_EV_sEV_surrogate",
    }
    return {
        "particle_name": name,
        "width_m": 800e-9,
        "depth_m": 550e-9,
        "wavelength_m": 660e-9,
        "engineering_score": final_score,
        "final_engineering_score": final_score,
        "summary": summary,
        "intrinsic": dict(summary),
        "reference": {
            "reference_model": "tsuyama_bfp_integrated",
            "reference_solver_route": "tsuyama_bfp_integrated",
            "readout_preset": "ev_nodi_design_sweep",
            "detector_forward_model": "roi_complex_mode_overlap_integral",
        },
    }


class TestDataObjects:
    def test_particle_invalid_radius(self):
        with pytest.raises(ValueError, match="radius"):
            Particle("bad", -1e-9, 1.5)

    def test_particle_material_model_requires_key(self):
        with pytest.raises(ValueError, match="material_key"):
            Particle("material-model", 10e-9, 1.5, use_material_model=True)

    def test_channel_invalid_width(self):
        with pytest.raises(ValueError, match="width"):
            Channel(width_m=0, depth_m=500e-9)

    def test_channel_invalid_wall_refractive_index(self):
        with pytest.raises(ValueError, match="wall_refractive_index"):
            Channel(width_m=800e-9, depth_m=500e-9, wall_refractive_index=0.0)

    def test_optical_invalid_theta(self):
        with pytest.raises(ValueError, match="collection_theta"):
            OpticalSystem(660e-9, 1.0, 300e-9, 700e-9, 300e-9, collection_theta_rad=0.0)

    def test_optical_resolve_illumination_geometry_defaults_to_objective_na_surrogate(self):
        optical = OpticalSystem(660e-9, 1.0, 300e-9, 700e-9, 300e-9)
        geometry = optical.resolve_illumination_geometry()
        expected_waist = 0.61 * optical.wavelength_m / optical.illumination_NA
        assert geometry["illumination_geometry_source"] == "objective_na_surrogate"
        assert geometry["illumination_geometry_decoupled_from_legacy_shared_beam"] is True
        assert geometry["illumination_beam_waist_x_m"] == pytest.approx(expected_waist)
        assert geometry["illumination_beam_waist_y_m"] == pytest.approx(expected_waist)
        assert geometry["illumination_beam_waist_z_m"] == pytest.approx(expected_waist)

    def test_sim_config_properties(self):
        cfg = SimulationConfig(0.2, 20000.0, 2e-4)
        assert cfg.dt_s == pytest.approx(5e-5)
        assert cfg.n_samples == 4000
        assert cfg.flow_control_mode == "fixed_velocity"
        assert cfg.flow_control_pressure_Pa == pytest.approx(1000.0)
        assert cfg.fluidic_channel_length_m == pytest.approx(1.0e-2)
        assert cfg.random_sequence_policy == "common_random_numbers"
        assert cfg.event_sampling_policy == "random"
        assert cfg.adaptive_event_budget_mode == "fixed"

    def test_sim_config_defaults_freeze_main_observation_chain(self):
        cfg = SimulationConfig(0.2, 20000.0, 2e-4)
        assert cfg.phase_model == "relative_surrogate"
        assert cfg.path_opd_model == "single_pass"
        assert cfg.reference_model == "channel_angular_surrogate"
        assert cfg.reference_route == "auto"
        assert cfg.reference_solver_route == "auto"
        assert cfg.reference_spatial_mode == "cross_section_surrogate"
        assert cfg.reference_phase_grating_mode == "phase_grating_sine"
        assert cfg.interference_overlap_mode == "joint_overlap_integrated"
        assert cfg.detector_forward_model == "joint_overlap_coherent_surrogate"
        assert cfg.objective_candidate_id == "current_control"
        assert cfg.detector_mode_definition == "shared_collection_operator_scalar_mode"
        assert cfg.field_coordinate_measure == "theta_phi_surrogate"
        assert cfg.bfp_to_angle_jacobian_applied is False
        assert cfg.detector_mask_units == "radian_surrogate"
        assert (
            cfg.coordinate_frame_mapping
            == "chip:x_width,y_flow,z_depth|optical:detector_projection_surrogate|bfp:theta_phi"
        )
        assert cfg.complex_time_harmonic_convention == "exp_minus_i_omega_t"
        assert cfg.fourier_transform_sign_convention == "forward_exp_minus_i_q_x"
        assert cfg.mie_amplitude_phase_convention == "miepython_S1S2_complex"
        assert cfg.interference_conjugation_convention == "Re_Eref_conj_Esca"
        assert cfg.global_phase_offset_source == "unmeasured_zero_reference"
        assert cfg.polarization_basis_model == "scalar_parallel_perpendicular_surrogate"
        assert cfg.jones_basis_status == "not_applied_scalar_projection"
        assert cfg.vector_optics_mode == "scalar_surrogate"
        assert cfg.polarization_jones_operator_mode == "scalar_projection"
        assert cfg.measured_jones_matrix_path is None
        assert cfg.scattering_normalization_route == "baseline_particle_relative"
        assert cfg.K_sca_calibration_status == "not_calibrated"
        assert cfg.standard_particle_calibration_path is None
        assert cfg.standard_particle_calibration_id is None
        assert cfg.calibration_state_machine_version == "partial_calibration_state_v1"
        assert cfg.detector_noise_model_route == "surrogate"
        assert cfg.photon_unit_noise_model == "not_applied"
        assert cfg.absolute_throughput_route == "unit_normalized_surrogate"
        assert cfg.detector_dynamic_range_model == "not_applied"
        assert cfg.adc_dynamic_range_model == "not_applied"
        assert cfg.rin_noise_model == "not_applied"
        assert cfg.speckle_background_noise_model == "not_applied"
        assert cfg.background_field_model == "baseline_subtraction_surrogate"
        assert cfg.transmitted_leakage_model == "not_applied"
        assert cfg.stray_light_model == "not_applied"
        assert cfg.particle_induced_channel_perturbation_model == "not_applied"
        assert cfg.particle_channel_perturbation_application_mode == "diagnostic_only"
        assert cfg.readout_preset == "exploratory_default"
        assert cfg.nodi_readout_semantics == "locked_carrier_surrogate"
        assert cfg.electronics_demod_phase_policy == "locked_to_event_center"
        assert cfg.readout_internal_demod_route == "sampled_carrier_demod_on_event_grid"
        assert cfg.readout_anti_alias_policy == "sampled_grid_nyquist_guard"
        assert cfg.lockin_output_unit_convention == "arbitrary_lockin_output_units"
        assert cfg.lockin_gain_chain == "mixer_x2_then_first_order_lowpass_no_instrument_gain"
        assert cfg.threshold_tail == "two_sided"
        assert cfg.threshold_calibration_source == "gaussian_iid"
        assert cfg.colored_noise_false_alarm_model == "not_applied"
        assert cfg.blank_false_positive_calibration_path is None
        assert cfg.blank_false_positive_calibration_id is None
        assert cfg.raw_blank_trace_path is None
        assert cfg.bfp_roi_mask_path is None
        assert cfg.particle_uncertainty_propagation_mode == "none"
        assert cfg.particle_uncertainty_budget_model == "nominal_only"
        assert cfg.EV_ensemble_mode == "nominal_single_preset"
        assert cfg.EV_sample_preparation_profile == "unknown"
        assert cfg.count_prediction_model == "not_applied"
        assert cfg.number_concentration_m3 is None
        assert cfg.count_observation_window_s is None
        assert cfg.count_dead_time_s == pytest.approx(0.0)
        assert cfg.wall_interaction_model == "none"
        assert cfg.interface_correction_mode == "off"
        assert cfg.interface_correction_priority == "EV_first"

        assert cfg.interface_correction_applied_to == "all_particles"
        assert cfg.thermal_pod_model == "unavailable"
        assert cfg.pod_roi_sensitivity_derivative_status == "unavailable"
        assert cfg.pod_signal_sign_source == "unavailable"
        assert cfg.pod_thermal_spatial_distribution_status == "ignored"
        assert cfg.pod_roi_derivative_validity == "unavailable"
        assert cfg.probe_wavelength_m is None
        assert cfg.excitation_wavelength_m is None
        assert cfg.probe_power_W is None
        assert cfg.excitation_power_W is None
        assert cfg.collection_angle_model == "channel_diffraction"
        assert cfg.collection_integration_mode == "pupil_slit_surrogate"
        assert cfg.collection_operator_calibration_path is None
        assert cfg.collection_operator_id is None
        assert cfg.scattering_projection_mode == "parallel"
        assert cfg.initial_position_distribution_mode == "uniform"
        assert cfg.pulse_detection_mode == "absolute"
        assert cfg.readout_model == "lockin_surrogate"
        assert cfg.normalization_mode == "per_wavelength"

    def test_design_objective_config_freezes_first_ev_weights(self):
        cfg = DEFAULT_DESIGN_OBJECTIVE_CONFIG
        assert cfg.target_family == "EV_sEV"
        assert cfg.anchor_particle_name == "gold_20nm"
        assert cfg.ev_size_quantiles_nm == (50.0, 70.0, 100.0, 150.0)
        assert cfg.w_ev_worst_case == pytest.approx(0.35)
        assert cfg.w_ev_d50 == pytest.approx(0.15)
        assert cfg.w_au20_anchor == pytest.approx(0.15)
        assert cfg.au20_equivalent_green == pytest.approx(1.0)
        assert cfg.au20_equivalent_yellow == pytest.approx(0.5)
        with pytest.raises(ValueError, match="ev_size_quantiles_nm"):
            DesignObjectiveConfig(ev_size_quantiles_nm=(100.0, 0.0))
        with pytest.raises(ValueError, match="au20_equivalent_green"):
            DesignObjectiveConfig(
                au20_equivalent_green=0.25,
                au20_equivalent_yellow=0.5,
            )

    def test_baseline_particle_uses_material_model_factory(self):
        expected = make_gold_baseline_particle()
        assert BASELINE_PARTICLE.material_key == "gold"
        assert BASELINE_PARTICLE.use_material_model is True
        assert BASELINE_PARTICLE.radius_m == pytest.approx(expected.radius_m)
        assert BASELINE_PARTICLE.n_complex_at(488e-9) != BASELINE_PARTICLE.n_complex_at(
            660e-9
        )

    def test_gold_20nm_preset_means_diameter_not_radius(self):
        particle = make_gold_baseline_particle(20.0, name="gold_20nm")
        diagnostics = build_unit_axis_convention_diagnostics(
            particle,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            DEFAULT_SIM_CFG,
        )
        assert particle.radius_m == pytest.approx(10e-9)
        assert diagnostics["particle_size_input_convention"] == (
            "diameter_nm_name_token_to_internal_radius_m"
        )
        assert diagnostics["particle_diameter_m"] == pytest.approx(20e-9)
        assert diagnostics["size_convention_validated"] is True
        assert diagnostics["unit_axis_convention_hard_gate_passed"] is True

    def test_ev_100nm_preset_means_diameter_not_radius(self):
        particle = make_biomimetic_exosome_particle(100)
        diagnostics = build_unit_axis_convention_diagnostics(
            particle,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            DEFAULT_SIM_CFG,
        )
        assert particle.radius_m == pytest.approx(50e-9)
        assert diagnostics["particle_diameter_m"] == pytest.approx(100e-9)
        assert diagnostics["particle_diameter_nm_from_name"] == pytest.approx(100.0)
        assert diagnostics["size_convention_status"] == (
            "diameter_name_matches_internal_radius"
        )

    def test_channel_width_depth_axis_convention_gate(self):
        diagnostics = build_unit_axis_convention_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            DEFAULT_SIM_CFG,
        )
        assert diagnostics["channel_width_axis"] == "x"
        assert diagnostics["channel_depth_axis"] == "z"
        assert diagnostics["flow_axis_convention"] == "y"
        assert diagnostics["optical_axis_convention"] == "detector_projection_surrogate"
        assert diagnostics["axis_convention_status"] == "pass"
        assert diagnostics["unit_axis_convention_status"] == "pass"

    def test_per_wavelength_normalization_blocks_absolute_lambda_ranking(self):
        diagnostics = build_wavelength_comparability_diagnostics(
            BASELINE_OPTICAL,
            DEFAULT_SIM_CFG,
            medium=WATER,
        )
        assert diagnostics["wavelength_lane_id"] == "lambda_660nm"
        assert diagnostics["per_wavelength_normalization_active"] is True
        assert diagnostics["within_lambda_geometry_ranking_allowed"] is True
        assert diagnostics["absolute_or_calibrated_lambda_comparison_allowed"] is False
        assert diagnostics["cross_wavelength_claim_gate_passed"] is False
        assert diagnostics["wavelength_ranking_claim_level"] == (
            "within_lambda_geometry_ranking_only"
        )
        assert "per_wavelength_normalization_active" in diagnostics[
            "laser_choice_claim_blocker"
        ]
        for field in WAVELENGTH_COMPARABILITY_DIAGNOSTIC_FIELDS:
            assert field in diagnostics

    def test_complete_wavelength_specific_chain_unlocks_calibrated_lambda_claim(self):
        cfg = replace(
            DEFAULT_SIM_CFG,
            absolute_throughput_route="calibrated_operator_table",
            collection_operator_calibration_path=str(Path(__file__).resolve()),
            photon_unit_noise_model="calibrated_photon_units",
            wavelength_lane_id="lambda_660nm",
            probe_power_by_wavelength_W={"lambda_660nm": 1.5e-3},
            detector_responsivity_by_wavelength={"lambda_660nm": 0.42},
            filter_transmission_by_wavelength={"lambda_660nm": 0.86},
            reference_calibration_by_wavelength={"lambda_660nm": "gold_40nm_660nm"},
        )
        diagnostics = build_wavelength_comparability_diagnostics(
            BASELINE_OPTICAL,
            cfg,
            medium=WATER,
        )

        assert diagnostics["wavelength_lane_calibration_complete"] is True
        assert diagnostics["absolute_or_calibrated_lambda_comparison_allowed"] is True
        assert diagnostics["cross_wavelength_claim_gate_passed"] is True
        assert diagnostics["wavelength_ranking_claim_level"] == (
            "calibrated_lambda_ranking_allowed"
        )
        assert diagnostics["laser_choice_claim_blocker"] == "none"
        assert diagnostics["detector_responsivity_lambda_status"] == (
            "configured_by_wavelength"
        )
        assert diagnostics["objective_transmission_lambda_status"] == (
            "configured_by_wavelength"
        )
        assert diagnostics["laser_power_density_lambda_status"] == (
            "configured_by_wavelength"
        )
        assert diagnostics["reference_lambda_scaling_status"] == (
            "configured_by_wavelength"
        )

        incomplete = replace(cfg, reference_calibration_by_wavelength={})
        blocked = build_wavelength_comparability_diagnostics(
            BASELINE_OPTICAL,
            incomplete,
            medium=WATER,
        )
        assert blocked["wavelength_lane_calibration_complete"] is False
        assert blocked["absolute_or_calibrated_lambda_comparison_allowed"] is False
        assert "reference_calibration_by_wavelength" in blocked[
            "laser_choice_claim_blocker"
        ]

    def test_medium_material_keys_flow_into_wavelength_diagnostics(self):
        medium = replace(
            WATER,
            name="hepes_buffer",
            material_key="hepes_buffer",
            use_material_model=True,
            optical_material_key="hepes_buffer",
            transport_material_key="hepes_buffer",
            thermal_material_key="hepes_buffer",
        )
        cfg = replace(
            DEFAULT_SIM_CFG,
            medium_optical_material_key="hepes_buffer",
            medium_transport_material_key="hepes_buffer",
            medium_thermal_material_key="hepes_buffer",
        )
        diagnostics = build_wavelength_comparability_diagnostics(
            BASELINE_OPTICAL,
            cfg,
            medium=medium,
        )

        assert diagnostics["medium_optical_material_key"] == "hepes_buffer"
        assert diagnostics["medium_transport_material_key"] == "hepes_buffer"
        assert diagnostics["medium_thermal_material_key"] == "hepes_buffer"
        assert diagnostics["medium_n_real_at_lambda"] == pytest.approx(
            get_n_complex("hepes_buffer", BASELINE_OPTICAL.wavelength_m).real
        )
        assert diagnostics["medium_viscosity_Pa_s"] is not None
        assert diagnostics["medium_density_kg_m3"] is not None
        assert diagnostics["medium_property_claim_level"] == (
            "nominal_material_properties_no_uncertainty"
        )

    def test_objective_profile_schema_exposes_current_control_claim_level(self):
        diagnostics = build_objective_profile_diagnostics(
            BASELINE_OPTICAL,
            DEFAULT_SIM_CFG,
        )
        assert diagnostics["objective_candidate_id"] == "current_control"
        assert diagnostics["objective_profile_schema_present"] is True
        assert diagnostics["objective_profile_gate_passed"] is True
        assert diagnostics["objective_cross_profile_claim_allowed"] is False
        assert diagnostics["objective_design_claim_level"] == (
            "single_profile_relative_only"
        )
        assert diagnostics["lockin_bandwidth_margin"] in {"ok", "risk"}
        assert diagnostics["working_distance_compatibility"] == (
            "not_configured_claim_blocker"
        )

    def test_objective_panel_does_not_auto_promote_high_na(self):
        intrinsic = compute_intrinsic_scattering(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL.wavelength_m,
            THETA_GRID,
        )
        cfg = replace(DEFAULT_SIM_CFG, probe_power_W=1.0e-2)
        panel = evaluate_objective_panel(
            BASELINE_PARTICLE,
            BASELINE_OPTICAL,
            cfg,
            intrinsic,
        )

        for field in OBJECTIVE_PANEL_DIAGNOSTIC_FIELDS:
            assert field in panel
        assert "high_NA_test" in panel["objective_panel_candidate_ids"]
        assert panel["objective_panel_recommendation"] != "high_NA_test"
        high_na = next(
            item for item in panel["objective_panel_records"]
            if item["objective_candidate_id"] == "high_NA_test"
        )
        assert high_na["lockin_bandwidth_margin"] == "risk"
        assert high_na["ev_photodamage_risk_band"] == "high"
        assert high_na["objective_panel_score"] < panel[
            "objective_panel_recommended_score"
        ]

    def test_objective_panel_score_matches_best_candidate(self):
        intrinsic = compute_intrinsic_scattering(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL.wavelength_m,
            THETA_GRID,
        )
        panel = evaluate_objective_panel(
            BASELINE_PARTICLE,
            BASELINE_OPTICAL,
            DEFAULT_SIM_CFG,
            intrinsic,
            candidate_ids=("current_control", "moderate_upgrade", "large_spot_control"),
        )
        scores = [
            float(record["objective_panel_score"])
            for record in panel["objective_panel_records"]
        ]
        assert panel["objective_panel_candidate_count"] == 3
        assert panel["objective_panel_recommended_score"] == pytest.approx(max(scores))
        assert panel["objective_panel_claim_level"] == (
            "candidate_refinement_surrogate_not_hardware_calibration"
        )

    def test_optical_exposure_safety_blocks_missing_power_claim(self):
        intrinsic = compute_intrinsic_scattering(BASELINE_PARTICLE, WATER, 660e-9, THETA_GRID)
        diagnostics = build_optical_exposure_safety_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_OPTICAL,
            DEFAULT_SIM_CFG,
            intrinsic,
        )
        assert diagnostics["safe_power_claim_level"] == (
            "blocked_missing_probe_power_metadata"
        )
        assert diagnostics["ev_photodamage_risk_band"] == (
            "unknown_missing_probe_power_metadata"
        )
        assert diagnostics["optical_exposure_safety_gate_passed"] is False
        assert "probe_power_missing" in diagnostics[
            "optical_exposure_safety_blocker_summary"
        ]

    def test_optical_exposure_safety_flags_high_power_density(self):
        intrinsic = compute_intrinsic_scattering(BASELINE_PARTICLE, WATER, 660e-9, THETA_GRID)
        cfg = replace(DEFAULT_SIM_CFG, probe_power_W=1.0e-2)
        diagnostics = build_optical_exposure_safety_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_OPTICAL,
            cfg,
            intrinsic,
        )
        assert diagnostics["laser_power_density_W_m2"] > 1.0e9
        assert diagnostics["ev_photodamage_risk_band"] == "high"
        assert diagnostics["bubble_or_thermal_lens_artifact_risk"] == "high"
        assert diagnostics["exposure_safety_not_red"] is False
        assert "ev_photodamage_risk_high" in diagnostics[
            "optical_exposure_safety_blocker_summary"
        ]

    def test_nodi_thermal_contamination_flags_au_absorption_crosstalk(self):
        intrinsic = compute_intrinsic_scattering(
            BASELINE_PARTICLE,
            WATER,
            660e-9,
            THETA_GRID,
        )
        cfg = replace(DEFAULT_SIM_CFG, probe_power_W=1.0e-3)
        diagnostics = build_nodi_thermal_contamination_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_OPTICAL,
            cfg,
            intrinsic,
        )

        assert set(NODI_THERMAL_CONTAMINATION_FIELDS).issubset(diagnostics)
        assert diagnostics["nodi_particle_material_thermal_class"] == (
            "absorbing_metal_standard"
        )
        assert diagnostics["nodi_absorption_to_scattering_ratio"] > 1.0
        assert diagnostics["nodi_absorption_to_scattering_crosstalk_risk"] == "high"
        assert diagnostics["nodi_standard_particle_thermal_artifact_risk"] == "high"
        assert diagnostics["nodi_thermal_solver_required_for_quantitative_claim"] is True
        assert diagnostics["nodi_thermal_contamination_claim_level"] == (
            "diagnostic_absorption_proxy_not_thermal_solver"
        )

    def test_nodi_thermal_contamination_keeps_ev_lane_diagnostic_only(self):
        particle = make_biomimetic_exosome_particle(100)
        intrinsic = compute_intrinsic_scattering(
            particle,
            WATER,
            660e-9,
            THETA_GRID,
        )
        cfg = replace(DEFAULT_SIM_CFG, probe_power_W=1.0e-4)
        diagnostics = build_nodi_thermal_contamination_diagnostics(
            particle,
            BASELINE_OPTICAL,
            cfg,
            intrinsic,
        )

        assert diagnostics["nodi_particle_material_thermal_class"] == (
            "EV_like_low_absorption"
        )
        assert diagnostics["nodi_standard_particle_thermal_artifact_risk"] == (
            "not_standard_particle"
        )
        assert diagnostics["nodi_ev_thermal_contamination_gate_required"] is False
        assert diagnostics["nodi_thermal_contamination_claim_level"] == (
            "diagnostic_absorption_proxy_not_thermal_solver"
        )

    def test_polarization_jones_default_scalar_mode_blocks_quantitative_claim(self):
        diagnostics = build_polarization_jones_diagnostics(DEFAULT_SIM_CFG)

        assert set(POLARIZATION_JONES_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["polarization_jones_operator_mode"] == "scalar_projection"
        assert diagnostics["polarization_overlap_efficiency"] == pytest.approx(1.0)
        assert diagnostics["phase_polarization_quantitative_claim_allowed"] is False
        assert diagnostics["polarization_sensitive_classification_claim_allowed"] is False
        assert diagnostics["measured_jones_matrix_loaded"] is False
        assert "measured_jones_matrix_not_validated" in diagnostics[
            "phase_polarization_claim_blocker_summary"
        ]
        assert "scalar_projection_operator_not_jones_matrix" in diagnostics[
            "phase_polarization_claim_blocker_summary"
        ]

    def test_polarization_jones_surrogate_reports_cross_leakage_overlap(self):
        cfg = replace(
            DEFAULT_SIM_CFG,
            polarization_jones_operator_mode="jones_pupil_surrogate",
            scattering_projection_mode="parallel",
            illumination_polarization_mode="perpendicular",
            reference_projection_mode="match_scattering",
            cross_polarization_leakage=0.2,
        )
        diagnostics = build_polarization_jones_diagnostics(cfg)

        assert diagnostics["polarization_jones_operator_status"] == (
            "jones_pupil_surrogate_active_unmeasured"
        )
        assert diagnostics["polarization_illumination_alignment_status"] == (
            "cross_suppressed"
        )
        assert diagnostics["polarization_reference_alignment_status"] == "matched"
        assert diagnostics["polarization_overlap_amplitude"] == pytest.approx(0.2)
        assert diagnostics["polarization_overlap_efficiency"] == pytest.approx(0.04)
        assert diagnostics["phase_polarization_quantitative_claim_allowed"] is False
        assert "jones_pupil_surrogate_unmeasured" in diagnostics[
            "phase_polarization_claim_blocker_summary"
        ]

    def test_polarization_jones_measured_mode_remains_blocked_without_validator(self):
        cfg = replace(
            DEFAULT_SIM_CFG,
            polarization_jones_operator_mode="measured_jones_matrix",
            measured_jones_matrix_path="calibration/jones_matrix_template.json",
        )
        diagnostics = build_polarization_jones_diagnostics(cfg)

        assert diagnostics["measured_jones_matrix_path_configured"] is True
        assert diagnostics["measured_jones_matrix_loaded"] is False
        assert diagnostics["measured_jones_matrix_validation_status"] == (
            "configured_but_not_loaded_or_validated_in_p1"
        )
        assert diagnostics["polarization_jones_operator_claim_level"] == (
            "measured_jones_matrix_configured_requires_p2_validator"
        )
        assert diagnostics["phase_polarization_quantitative_claim_allowed"] is False
        assert diagnostics["phase_polarization_claim_blocker_summary"] == (
            "measured_jones_matrix_not_validated"
        )

    def test_design_claim_governance_exports_minimum_schema_with_blockers(self):
        intrinsic = compute_intrinsic_scattering(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL.wavelength_m,
            THETA_GRID,
        )
        reference = {
            "reference_route": "engineering_fallback",
            "detector_forward_model": DEFAULT_SIM_CFG.detector_forward_model,
            "calibration_state_machine_status": "partial_lane_calibration_only",
            "output_claim_level_resolved": "engineering_diagnostic",
        }
        reference.update(
            build_unit_axis_convention_diagnostics(
                BASELINE_PARTICLE,
                BASELINE_CHANNEL,
                BASELINE_OPTICAL,
                DEFAULT_SIM_CFG,
            )
        )
        reference.update(build_mie_validation_diagnostics(intrinsic, DEFAULT_SIM_CFG))
        reference.update(
            build_wavelength_comparability_diagnostics(
                BASELINE_OPTICAL,
                DEFAULT_SIM_CFG,
            )
        )
        reference.update(
            build_objective_profile_diagnostics(BASELINE_OPTICAL, DEFAULT_SIM_CFG)
        )
        reference.update(
            build_optical_exposure_safety_diagnostics(
                BASELINE_PARTICLE,
                BASELINE_OPTICAL,
                DEFAULT_SIM_CFG,
                intrinsic,
            )
        )
        reference.update(build_readout_convention_diagnostics(DEFAULT_SIM_CFG))

        diagnostics = build_design_claim_governance_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            DEFAULT_SIM_CFG,
            reference=reference,
            summary={"n_events": 1},
        )

        assert set(MINIMUM_OUTPUT_SCHEMA_FIELDS).issubset(diagnostics)
        assert diagnostics["minimum_output_schema_columns_present"] is True
        assert diagnostics["minimum_output_schema_missing_fields"] == ()
        assert diagnostics["case_id"].startswith(f"{BASELINE_PARTICLE.name}|W=800nm")
        assert diagnostics["manifest_id"] == "unavailable_no_recompute_manifest"
        assert diagnostics["W_nm"] == 800
        assert diagnostics["H_nm"] == 550
        assert diagnostics["lambda_nm"] == 660
        assert diagnostics["readout_semantics"] == "locked_carrier_surrogate"
        assert diagnostics["detector_operator_disagreement_band"] == (
            "unavailable_no_roi_mode_overlap_lane"
        )
        assert diagnostics["double_counting_risk_band"] == (
            "unavailable_no_particle_channel_double_count_guard"
        )
        assert diagnostics["event_qc_pass_fraction"] is None
        assert diagnostics["relative_design_eligible"] is False
        assert diagnostics["within_lambda_design_eligible"] is False
        assert diagnostics["absolute_global_green_eligible"] is False
        assert diagnostics["final_green_eligible"] is False
        assert diagnostics["final_recommendation_band"] == "exploratory_only"
        assert "detector_operator_gate_not_passed" in diagnostics[
            "primary_blocker_summary"
        ]
        assert "recompute_manifest_missing" in diagnostics[
            "primary_blocker_summary"
        ]

    def test_design_claim_governance_treats_nan_gate_values_as_missing(self):
        diagnostics = build_design_claim_governance_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            DEFAULT_SIM_CFG,
            reference={
                "detector_operator_gate_passed": np.nan,
                "double_counting_risk_band": "low",
                "no_double_count_guard_passed": True,
                "recompute_manifest_gate_passed": True,
                "event_qc_pass_fraction": 1.0,
                "event_qc_gate_passed": True,
                "selection_bias_gate_passed": True,
                "ev_integrity_gate_passed": True,
                "nodi_readout_semantics_gate_passed": True,
                "within_lambda_geometry_ranking_allowed": True,
                "engineering_gate_passed": True,
            },
        )

        assert diagnostics["detector_operator_gate_passed"] is False
        assert diagnostics["detector_operator_caution_flag"] is True
        assert diagnostics["relative_design_eligible"] is True
        assert diagnostics["within_lambda_design_eligible"] is True
        assert diagnostics["detector_resolved_relative_design_eligible"] is False
        assert diagnostics["relative_design_with_detector_caution"] is True

    def test_design_claim_governance_detector_caution_keeps_relative_ranking(self):
        reference = {
            "detector_operator_disagreement_band": "large",
            "detector_operator_gate_passed": False,
            "double_counting_risk_band": "low",
            "no_double_count_guard_passed": True,
            "recompute_manifest_gate_passed": True,
            "event_qc_pass_fraction": 1.0,
            "event_qc_gate_passed": True,
            "selection_bias_gate_passed": True,
            "ev_integrity_gate_passed": True,
            "nodi_readout_semantics_gate_passed": True,
            "within_lambda_geometry_ranking_allowed": True,
            "engineering_gate_passed": True,
            "unit_axis_convention_hard_gate_passed": True,
            "mie_validation_hard_gate_passed": True,
            "cross_wavelength_claim_gate_passed": True,
            "objective_profile_gate_passed": True,
            "optical_exposure_safety_gate_passed": True,
            "exposure_safety_not_red": True,
            "reference_operating_band": "electronics_noise_limited_useful",
        }

        diagnostics = build_design_claim_governance_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            DEFAULT_SIM_CFG,
            reference=reference,
        )

        assert diagnostics["detector_operator_caution_flag"] is True
        assert diagnostics["detector_operator_caution_reason"] == (
            "detector_operator_large_or_missing_blocks_absolute_claim_only"
        )
        assert diagnostics["relative_design_eligible"] is True
        assert diagnostics["within_lambda_design_eligible"] is True
        assert diagnostics["relative_design_with_detector_caution"] is True
        assert diagnostics["detector_resolved_relative_design_eligible"] is False
        assert diagnostics["absolute_global_green_eligible"] is False
        assert diagnostics["final_green_eligible"] is False
        assert diagnostics["final_recommendation_band"] == (
            "yellow_detector_operator_caution"
        )
        assert diagnostics["primary_blocker_summary"] == (
            "detector_operator_gate_not_passed"
        )

    def test_event_qc_batch_surrogate_caps_detected_rate_after_qc(self):
        summary = {
            "n_events": 10,
            "detection_rate": 0.8,
            "stable_detection_rate": 0.4,
            "mean_peak_width_s": DEFAULT_SIM_CFG.min_peak_width_s,
            "phase_flip_fraction": 0.1,
            "mean_local_snr": 3.0,
        }
        diagnostics = build_event_quality_control_diagnostics(
            summary,
            DEFAULT_SIM_CFG,
            reference={"readout_phase_locked_claim_allowed": True},
        )
        assert set(EVENT_QC_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["event_qc_status"] == "batch_surrogate_active"
        assert diagnostics["event_qc_pass_fraction"] == pytest.approx(0.5)
        assert diagnostics["detected_rate_after_event_qc"] == pytest.approx(0.4)
        assert diagnostics["detected_rate_after_event_qc"] <= summary["detection_rate"]
        assert diagnostics["event_qc_soft_gate_passed"] is True
        assert diagnostics["event_qc_hard_gate_passed"] is True
        assert diagnostics["event_qc_gate_passed"] is True
        assert diagnostics["signed_signal_available"] is True
        assert diagnostics["polarity_claim_allowed"] is True

    def test_event_qc_hard_gate_blocks_width_out_of_range(self):
        summary = {
            "n_events": 10,
            "detection_rate": 0.8,
            "stable_detection_rate": 0.8,
            "mean_peak_width_s": 20.0 * DEFAULT_SIM_CFG.min_peak_width_s,
            "phase_flip_fraction": 0.0,
            "mean_local_snr": 3.0,
        }
        diagnostics = build_event_quality_control_diagnostics(
            summary,
            DEFAULT_SIM_CFG,
        )

        assert diagnostics["event_pulse_width_out_of_range"] is True
        assert diagnostics["event_qc_soft_gate_passed"] is True
        assert diagnostics["event_qc_hard_gate_passed"] is False
        assert diagnostics["event_qc_gate_passed"] is False

    def test_event_qc_soft_gate_blocks_high_artifact_risk(self):
        summary = {
            "n_events": 10,
            "detection_rate": 0.8,
            "stable_detection_rate": 0.0,
            "mean_peak_width_s": DEFAULT_SIM_CFG.min_peak_width_s,
            "phase_flip_fraction": 0.0,
            "mean_local_snr": 0.5,
        }
        diagnostics = build_event_quality_control_diagnostics(
            summary,
            DEFAULT_SIM_CFG,
        )

        assert diagnostics["event_artifact_risk_score"] > 0.5
        assert diagnostics["event_qc_soft_gate_passed"] is False
        assert diagnostics["event_qc_hard_gate_passed"] is False
        assert diagnostics["event_qc_gate_passed"] is False
        assert diagnostics["event_qc_primary_failure_reason"] != "none"

    def test_event_qc_primary_failure_tracks_actual_gate_failure(self):
        drift_cfg = replace(
            DEFAULT_SIM_CFG,
            noise_model="gaussian_plus_drift",
            drift_slope=0.001,
            post_readout_drift_slope=0.0002,
            event_qc_max_artifact_risk_score=0.5,
        )
        passing_summary = {
            "n_events": 10,
            "detection_rate": 0.8,
            "stable_detection_rate": 0.8,
            "mean_peak_width_s": drift_cfg.min_peak_width_s,
            "phase_flip_fraction": 0.0,
            "mean_local_snr": 5.0,
        }
        passing = build_event_quality_control_diagnostics(
            passing_summary,
            drift_cfg,
        )
        assert passing["event_baseline_nonstationary"] is True
        assert passing["event_qc_gate_passed"] is True
        assert passing["event_qc_primary_failure_reason"] == "none"

        saturated = build_event_quality_control_diagnostics(
            {
                **passing_summary,
                "detector_saturation_status": "saturated_high",
            },
            DEFAULT_SIM_CFG,
        )
        assert saturated["event_saturation_risk"] is True
        assert saturated["event_qc_gate_passed"] is False
        assert saturated["event_qc_primary_failure_reason"] == "saturation_risk"

    def test_event_qc_magnitude_readout_blocks_polarity_claims(self):
        cfg = apply_readout_preset(
            SimulationConfig(0.2, 20000.0, 2e-4),
            "EV_NODI_only_design",
        )
        diagnostics = build_event_quality_control_diagnostics(
            {
                "n_events": 5,
                "detection_rate": 0.6,
                "stable_detection_rate": 0.6,
                "mean_peak_width_s": cfg.min_peak_width_s,
                "phase_flip_fraction": 0.0,
                "mean_local_snr": 5.0,
            },
            cfg,
            reference={"readout_phase_locked_claim_allowed": True},
        )
        assert diagnostics["signed_signal_available"] is False
        assert diagnostics["magnitude_readout_information_loss"] is True
        assert diagnostics["polarity_claim_allowed"] is False
        assert diagnostics["phase_sensitive_classification_allowed"] is False

    def test_event_qc_phase_sensitive_classification_requires_phase_lock_gate(self):
        cfg = replace(
            DEFAULT_SIM_CFG,
            readout_observable_mode="in_phase",
            nodi_readout_semantics="measured_transfer_function",
        )
        diagnostics = build_event_quality_control_diagnostics(
            {
                "n_events": 5,
                "detection_rate": 0.6,
                "stable_detection_rate": 0.6,
                "mean_peak_width_s": cfg.min_peak_width_s,
                "phase_flip_fraction": 0.0,
                "mean_local_snr": 5.0,
            },
            cfg,
            reference={"readout_phase_locked_claim_allowed": False},
        )
        assert diagnostics["signed_signal_available"] is True
        assert diagnostics["polarity_claim_allowed"] is False
        assert diagnostics["phase_sensitive_classification_allowed"] is False

    def test_selection_function_skeleton_exports_observed_bias_boundary(self):
        summary = {
            "detection_rate": 0.25,
            "event_qc_pass_fraction": 0.8,
            "particle_family": "EV_sEV",
        }
        particle = make_biomimetic_exosome_particle(50)
        diagnostics = build_selection_function_diagnostics(
            particle,
            summary,
            DEFAULT_SIM_CFG,
        )
        assert set(SELECTION_FUNCTION_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["selection_function_status"] == (
            "single_case_detection_qc_skeleton_active"
        )
        assert diagnostics["selection_bias_gate_passed"] is True
        assert diagnostics["P_detect_by_population_bin"][particle.name] == pytest.approx(
            0.25
        )
        assert diagnostics["P_pass_QC_by_population_bin"][particle.name] == pytest.approx(
            0.8
        )
        assert diagnostics["optical_detection_selection_bias"][particle.name] == pytest.approx(
            0.2
        )
        assert diagnostics["small_EV_under_detection_bias"] == (
            "possible_under_detection_in_current_surrogate"
        )
        assert "population_inversion_unavailable" in diagnostics[
            "selection_bias_warning"
        ]

    def test_selection_function_observed_distribution_normalizes_bias(self):
        diagnostics = compute_observed_distribution_correction(
            [
                {
                    "population_bin_id": "small_low_ri_ev",
                    "p_true": 0.5,
                    "P_detect": 0.2,
                    "P_pass_QC": 0.8,
                    "diameter_nm": 50.0,
                    "refractive_index": 1.37,
                    "particle_family": "EV_sEV",
                },
                {
                    "population_bin_id": "large_ev",
                    "p_true": 0.5,
                    "P_detect": 0.8,
                    "P_pass_QC": 0.9,
                    "diameter_nm": 120.0,
                    "refractive_index": 1.40,
                    "particle_family": "EV_sEV",
                },
            ]
        )

        assert set(SELECTION_FUNCTION_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        observed = diagnostics["observed_distribution_predicted"]
        assert sum(observed.values()) == pytest.approx(1.0)
        assert observed["small_low_ri_ev"] < 0.5
        assert diagnostics["true_to_observed_bias_factor"]["small_low_ri_ev"] < 1.0
        assert diagnostics["small_EV_under_detection_bias"] == (
            "small_EV_bins_underrepresented_in_observed_distribution"
        )
        assert diagnostics["low_RI_EV_under_detection_bias"] == (
            "low_RI_EV_bins_underrepresented_in_observed_distribution"
        )
        assert diagnostics["selection_bias_claim_level"] == (
            "observed_distribution_surrogate_not_population_inversion"
        )

    def test_selection_function_observed_distribution_flags_contaminant_enrichment(self):
        diagnostics = compute_observed_distribution_correction(
            [
                {
                    "population_bin_id": "ev_bin",
                    "p_true": 0.8,
                    "P_detect": 0.25,
                    "P_pass_QC": 0.9,
                    "particle_family": "EV_sEV",
                },
                {
                    "population_bin_id": "protein_aggregate",
                    "p_true": 0.2,
                    "P_detect": 0.9,
                    "P_pass_QC": 0.95,
                    "particle_family": "contaminant",
                    "is_contaminant": True,
                },
            ]
        )

        observed = diagnostics["observed_distribution_predicted"]
        assert observed["protein_aggregate"] > 0.2
        assert diagnostics["contaminant_enrichment_in_observed_events"] == (
            "contaminant_bins_enriched_in_observed_events"
        )

    def test_selection_function_observed_distribution_handles_zero_selection(self):
        diagnostics = compute_observed_distribution_correction(
            [
                {
                    "population_bin_id": "undetected_ev",
                    "p_true": 1.0,
                    "P_detect": 0.0,
                    "P_pass_QC": 0.0,
                    "particle_family": "EV_sEV",
                }
            ]
        )

        assert diagnostics["observed_distribution_prediction_status"] == (
            "unavailable_zero_selected_population_weight"
        )
        assert diagnostics["observed_distribution_predicted"]["undetected_ev"] == 0.0
        assert diagnostics["selection_bias_gate_passed"] is False

    def test_population_inference_scaffold_defines_likelihood_shape_and_blocker(self):
        scaffold = build_population_inference_scaffold(
            {
                "observed_count": 12,
                "count_log_likelihood": -3.2,
                "observed_distribution_predicted": {
                    "small_ev": 0.25,
                    "large_ev": 0.75,
                },
                "true_to_observed_bias_factor": {
                    "small_ev": 0.5,
                    "large_ev": 1.5,
                },
                "selection_bias_claim_level": (
                    "observed_distribution_surrogate_not_population_inversion"
                ),
            }
        )

        assert set(POPULATION_INFERENCE_DIAGNOSTIC_FIELDS).issubset(scaffold)
        assert scaffold["population_inference_status"] == (
            "likelihood_shape_defined_claim_blocked"
        )
        assert scaffold["population_inference_claim_level"] == (
            "likelihood_shape_only_no_population_inversion_claim"
        )
        assert scaffold["population_inference_observed_event_count"] == 12
        assert scaffold["population_inference_log_likelihood_available"] is True
        assert (
            scaffold["population_inference_selection_correction_available"] is True
        )
        assert scaffold["population_inference_true_distribution_estimate"] is None
        assert scaffold["population_inference_posterior_available"] is False
        assert scaffold["population_inference_gate_passed"] is False
        assert "true_population_inversion_not_implemented" in str(
            scaffold["population_inference_blocker_summary"]
        )
        missing_inputs = scaffold["population_inference_missing_inputs"]
        assert isinstance(missing_inputs, tuple)
        assert "population_inference_sampler" in missing_inputs

    def test_population_inference_scaffold_reports_missing_inputs(self):
        scaffold = build_population_inference_scaffold({})

        assert scaffold["population_inference_status"] == "schema_only_missing_inputs"
        assert scaffold["population_inference_observed_event_count"] is None
        assert scaffold["population_inference_population_bins"] == ()
        missing_inputs = scaffold["population_inference_missing_inputs"]
        assert isinstance(missing_inputs, tuple)
        assert set(missing_inputs) == {
            "observed_event_count",
            "population_bins",
            "selection_correction",
            "count_log_likelihood",
            "population_inference_sampler",
        }
        assert scaffold["population_inference_gate_passed"] is False

    def test_channel_geometry_diagnostics_export_accessible_area_and_blocker(self):
        diagnostics = build_channel_geometry_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            DEFAULT_SIM_CFG,
        )
        assert set(CHANNEL_GEOMETRY_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["channel_cross_section_model"] == "ideal_rectangle"
        assert diagnostics["effective_accessible_area_m2"] == pytest.approx(
            (BASELINE_CHANNEL.width_m - 2.0 * BASELINE_PARTICLE.radius_m)
            * (BASELINE_CHANNEL.depth_m - 2.0 * BASELINE_PARTICLE.radius_m)
        )
        assert diagnostics["roughness_scattering_background_proxy"] == pytest.approx(
            0.0
        )
        assert diagnostics["geometry_claim_level"] == (
            "nominal_ideal_rectangle_geometry_only"
        )
        assert diagnostics["channel_geometry_diagnostic_gate_passed"] is True
        assert diagnostics["effective_to_ideal_accessible_area_ratio"] == pytest.approx(
            1.0
        )
        assert diagnostics["effective_to_ideal_phase_mask_area_ratio"] == pytest.approx(
            1.0
        )

    def test_channel_geometry_rounded_rectangle_surrogate_reduces_ideal_area(self):
        cfg = replace(
            DEFAULT_SIM_CFG,
            channel_cross_section_model="rounded_rectangle",
            corner_radius_nm=80.0,
        )
        diagnostics = build_channel_geometry_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
        )

        assert set(CHANNEL_GEOMETRY_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["channel_cross_section_model"] == "rounded_rectangle"
        assert diagnostics["effective_phase_mask_area_m2"] < diagnostics[
            "ideal_phase_mask_area_m2"
        ]
        assert diagnostics["effective_accessible_area_m2"] < diagnostics[
            "ideal_accessible_area_m2"
        ]
        assert 0.0 < diagnostics["effective_to_ideal_accessible_area_ratio"] < 1.0
        assert diagnostics["geometry_model_discrepancy_flag"] == (
            "active_rounded_rectangle_surrogate_deviates_from_ideal_rectangle"
        )
        assert diagnostics["geometry_claim_level"] == (
            "active_parameterized_geometry_surrogate_not_measured"
        )

    def test_channel_geometry_trapezoid_surrogate_reduces_ideal_area(self):
        cfg = replace(
            DEFAULT_SIM_CFG,
            channel_cross_section_model="trapezoid_tapered_sidewalls",
            sidewall_taper_angle_deg=6.0,
        )
        diagnostics = build_channel_geometry_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
        )

        assert diagnostics["channel_cross_section_model"] == (
            "trapezoid_tapered_sidewalls"
        )
        assert diagnostics["trapezoid_top_width_m"] == pytest.approx(
            BASELINE_CHANNEL.width_m
        )
        assert diagnostics["trapezoid_bottom_width_m"] < BASELINE_CHANNEL.width_m
        assert diagnostics["effective_phase_mask_area_m2"] < diagnostics[
            "ideal_phase_mask_area_m2"
        ]
        assert diagnostics["effective_accessible_area_m2"] < diagnostics[
            "ideal_accessible_area_m2"
        ]
        assert diagnostics["geometry_model_discrepancy_flag"] == (
            "active_trapezoid_sidewall_surrogate_deviates_from_ideal_rectangle"
        )
        assert diagnostics["channel_geometry_diagnostic_gate_passed"] is True

    def test_electrokinetic_diagnostics_compute_debye_confinement_flag(self):
        cfg = replace(
            DEFAULT_SIM_CFG,
            ionic_strength_M=0.15,
            zeta_potential_particle_mV=-20.0,
            zeta_potential_wall_mV=-40.0,
        )
        diagnostics = build_electrokinetic_transport_diagnostics(
            BASELINE_CHANNEL,
            cfg,
        )
        assert set(ELECTROKINETIC_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["debye_length_nm"] == pytest.approx(
            0.304 / np.sqrt(0.15)
        )
        assert diagnostics["debye_to_min_channel_dimension_ratio"] < 0.01
        assert diagnostics["electrostatic_confinement_flag"] == "screened_or_negligible"
        assert diagnostics["electrostatic_wall_exclusion_length_nm"] == pytest.approx(
            diagnostics["debye_length_nm"]
        )

    def test_electrokinetic_boltzmann_wall_exclusion_suppresses_near_wall_weight(self):
        cfg = replace(
            DEFAULT_SIM_CFG,
            electrokinetic_model="boltzmann_wall_exclusion",
            ionic_strength_M=1.0e-4,
            zeta_potential_particle_mV=-35.0,
            zeta_potential_wall_mV=-45.0,
        )
        diagnostics = build_electrokinetic_transport_diagnostics(
            BASELINE_CHANNEL,
            cfg,
        )

        assert set(ELECTROKINETIC_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["boltzmann_wall_exclusion_status"] == (
            "active_grid_surrogate"
        )
        assert diagnostics["boltzmann_near_wall_weight_fraction"] < diagnostics[
            "boltzmann_center_weight_fraction"
        ]
        assert diagnostics["boltzmann_center_to_near_wall_weight_ratio"] > 1.0
        assert diagnostics["boltzmann_weighted_mean_wall_distance_nm"] > diagnostics[
            "unweighted_mean_wall_distance_nm"
        ]
        assert diagnostics["surface_charge_transport_claim_level"] == (
            "boltzmann_wall_exclusion_sensitivity_not_calibrated_transport"
        )

    def test_electrokinetic_boltzmann_lane_blocks_missing_metadata(self):
        cfg = replace(
            DEFAULT_SIM_CFG,
            electrokinetic_model="boltzmann_wall_exclusion",
            ionic_strength_M=None,
            zeta_potential_particle_mV=-35.0,
            zeta_potential_wall_mV=-45.0,
        )
        diagnostics = build_electrokinetic_transport_diagnostics(
            BASELINE_CHANNEL,
            cfg,
        )

        assert diagnostics["boltzmann_wall_exclusion_status"] == (
            "blocked_missing_ionic_strength_or_zeta_metadata"
        )
        assert diagnostics["boltzmann_center_to_near_wall_weight_ratio"] is None
        assert diagnostics["electrokinetic_diagnostic_gate_passed"] is False

    def test_ev_integrity_risk_flags_confinement_and_clearance(self):
        particle = make_biomimetic_exosome_particle(400)
        geometry = {"surface_roughness_rms_nm": 5.0}
        diagnostics = build_ev_integrity_risk_diagnostics(
            particle,
            BASELINE_CHANNEL,
            DEFAULT_SIM_CFG,
            geometry=geometry,
        )
        assert set(EV_INTEGRITY_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["ev_confinement_ratio"] == pytest.approx(400.0 / 550.0)
        assert diagnostics["ev_deformation_or_rupture_risk"] == (
            "moderate_confinement_risk"
        )
        assert diagnostics["ev_integrity_claim_level"] == (
            "geometry_surrogate_integrity_risk_not_validated"
        )
        assert diagnostics["ev_integrity_gate_passed"] is True

    def test_ev_reporting_metadata_blocks_biological_specificity_when_incomplete(self):
        diagnostics = build_ev_reporting_metadata_diagnostics()
        assert set(EV_REPORTING_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["ev_biological_specificity_claim_allowed"] is False
        assert diagnostics["ev_reporting_readiness_score"] == pytest.approx(0.0)
        assert "sample_source" in diagnostics[
            "ev_biological_specificity_blocker_summary"
        ]
        assert diagnostics["ev_sample_identity_claim_level"] == (
            "EV_like_optical_particle_metadata_incomplete"
        )

    def test_ev_reporting_metadata_allows_specificity_when_controls_present(self):
        metadata = EVPreanalyticalMetadata(
            sample_source="conditioned_media",
            donor_or_cell_line="MSC",
            culture_medium="serum_free",
            serum_depletion_method="not_applicable",
            collection_time_h=24.0,
            storage_temperature_C=-80.0,
            freeze_thaw_cycles=0,
            isolation_method="SEC",
            concentration_method="ultrafiltration",
            buffer_exchange_method="SEC",
            final_buffer="PBS",
            filtration_um=0.22,
            protein_assay_available=True,
            lipid_assay_available=True,
            RNA_assay_available=True,
            marker_panel_available=True,
            negative_marker_available=True,
            orthogonal_size_method="NTA",
        )
        diagnostics = build_ev_reporting_metadata_diagnostics(metadata)
        assert diagnostics["ev_biological_specificity_claim_allowed"] is True
        assert diagnostics["ev_reporting_gate_passed"] is True
        assert diagnostics["ev_reporting_readiness_score"] == pytest.approx(1.0)
        assert diagnostics["ev_biological_specificity_blocker_summary"] == "none"

    def test_assay_control_matrix_exports_required_controls_and_readiness(self):
        diagnostics = build_assay_control_matrix_diagnostics(
            configured_controls=("buffer_blank", "spike_in_Au20")
        )
        assert set(ASSAY_CONTROL_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["required_control_samples"] == REQUIRED_CONTROL_SAMPLES
        assert diagnostics["assay_control_readiness_score"] == pytest.approx(0.2)
        assert "medium_blank" in diagnostics["missing_control_samples"]
        assert diagnostics["assay_control_gate_passed"] is False
        assert diagnostics["control_priority"]["buffer_blank"] == "P0_required"

    def test_control_interpretation_flags_ambiguous_control_failures(self):
        assay_controls = build_assay_control_matrix_diagnostics(
            configured_controls=(
                "EV_depleted_sample",
                "detergent_lysed_EV_sample",
                "proteinase_treated_sample",
                "spike_in_Au20",
                "dilution_linearity_control",
            )
        )
        diagnostics = build_control_interpretation_diagnostics(assay_controls)
        assert set(CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["control_interpretation_schema"] == (
            "control_interpretation_risk_v1"
        )
        assert diagnostics["control_failure_interpretation_gate_passed"] is False
        interpretation = diagnostics["control_failure_interpretation"]
        assert isinstance(interpretation, dict)
        assert interpretation["detergent_lysis"] == (
            "lysis_failure_or_nonvesicular_artifact_can_mimic_EV_optical_signal"
        )
        risk_table = diagnostics["control_failure_interpretation_risk_table"]
        assert isinstance(risk_table, dict)
        assert risk_table["filtration"]["configuration_status"] == (
            "missing_control_configuration"
        )
        missing = diagnostics["control_interpretation_missing_controls"]
        assert isinstance(missing, tuple)
        assert "filtration" in missing
        high_risk = diagnostics["control_failure_interpretation_high_risk_controls"]
        assert isinstance(high_risk, tuple)
        assert "spike_in" in high_risk
        assert "control_outcome_data_not_ingested" in diagnostics[
            "control_interpretation_blocker_summary"
        ]

    def test_recompute_manifest_is_deterministic_and_hashes_case_state(self):
        first = build_recompute_manifest_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            DEFAULT_SIM_CFG,
        )
        second = build_recompute_manifest_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            DEFAULT_SIM_CFG,
        )
        changed_cfg = replace(DEFAULT_SIM_CFG, random_seed=123)
        changed = build_recompute_manifest_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            changed_cfg,
        )
        assert set(RECOMPUTE_MANIFEST_DIAGNOSTIC_FIELDS).issubset(first)
        assert first["manifest_id"].startswith("manifest_")
        assert first["manifest_id"] == second["manifest_id"]
        assert first["config_hash"] == second["config_hash"]
        assert first["manifest_id"] != changed["manifest_id"]
        assert changed["random_seed_policy"] == "fixed_seed"
        assert changed["rng_stream_id"] == "seed_123"
        assert first["recompute_manifest_gate_passed"] is True

    def test_detector_forward_model_accepts_roi_comparison_lanes(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            detector_forward_model="roi_complex_mode_overlap_integral",
        )
        assert cfg.detector_forward_model == "roi_complex_mode_overlap_integral"
        cfg = replace(cfg, detector_forward_model="roi_intensity_integral")
        assert cfg.detector_forward_model == "roi_intensity_integral"
        with pytest.raises(ValueError, match="detector_forward_model"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                detector_forward_model="roi_voltage_claim",
            )

    def test_bfp_detector_operator_matches_uniform_fields(self):
        theta_grid = np.linspace(0.0, 1.0, 101)
        operator = {
            "theta_grid_rad": theta_grid,
            "theta_center_rad": 0.5,
            "theta_weights": np.ones_like(theta_grid),
            "throughput_scale": 1.0,
            "phi_grid_rad": np.array([0.0]),
            "phi_weights": np.array([1.0]),
        }
        ref_field = np.full_like(theta_grid, 2.0 + 0.0j, dtype=complex)
        sca_field = np.full_like(theta_grid, 0.5 + 0.0j, dtype=complex)
        diagnostics = compute_detector_integrated_interference(
            theta_grid,
            ref_field,
            sca_field,
            operator,
            replace(DEFAULT_SIM_CFG, collection_integration_mode="gaussian_weighted"),
        )
        assert set(BFP_DETECTOR_OPERATOR_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["I_ref_detector_integrated"] == pytest.approx(4.0)
        assert diagnostics["self_sca_detector_integrated"] == pytest.approx(0.25)
        assert diagnostics["cross_term_detector_integrated"] == pytest.approx(2.0)
        assert diagnostics["signal_detector_integrated"] == pytest.approx(2.25)
        assert diagnostics["mode_overlap_efficiency"] == pytest.approx(1.0)
        assert diagnostics["roi_vs_scalar_signal_ratio"] == pytest.approx(1.0)
        assert diagnostics["detector_operator_disagreement_band"] == "small"
        assert diagnostics["detector_operator_gate_passed"] is True

    def test_particle_channel_perturbation_config_and_guard_validation(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            particle_induced_channel_perturbation_model=(
                "excluded_volume_phase_surrogate"
            ),
            particle_channel_perturbation_application_mode=(
                "alternative_forward_phase_lane"
            ),
        )
        assert (
            cfg.particle_induced_channel_perturbation_model
            == "excluded_volume_phase_surrogate"
        )
        assert (
            cfg.particle_channel_perturbation_application_mode
            == "alternative_forward_phase_lane"
        )
        with pytest.raises(ValueError, match="particle_induced_channel_perturbation"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                particle_induced_channel_perturbation_model="ad_hoc_phase_patch",
            )
        with pytest.raises(ValueError, match="particle_channel_perturbation"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                particle_channel_perturbation_application_mode="direct_score_addition",
            )

    def test_particle_channel_excluded_volume_surrogate_is_diagnostic_only(self):
        particle = Particle("ev_like_test", 50e-9, 1.45)
        cfg = replace(
            DEFAULT_SIM_CFG,
            particle_induced_channel_perturbation_model=(
                "excluded_volume_phase_surrogate"
            ),
            particle_channel_perturbation_application_mode="diagnostic_only",
        )
        diagnostics = build_particle_channel_perturbation_diagnostics(
            particle,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            E_ref_complex=1.0 + 0.0j,
            E_sca_unit_normalized_complex=0.1 + 0.0j,
        )
        assert set(PARTICLE_CHANNEL_PERTURBATION_DIAGNOSTIC_FIELDS).issubset(
            diagnostics
        )
        assert diagnostics["particle_induced_channel_phase_perturbation_status"] == (
            "excluded_volume_phase_surrogate_active"
        )
        assert diagnostics["delta_phi_particle_peak_rad"] > 0.0
        assert diagnostics["delta_E_ref_particle_peak_abs"] > 0.0
        assert diagnostics["delta_E_ref_particle_to_E_sca_ratio"] > 0.0
        assert diagnostics["double_counting_risk_band"] in {"low", "moderate", "high"}
        assert diagnostics["no_double_count_guard_passed"] is True
        assert diagnostics["particle_channel_double_count_guard_status"] == (
            "pass_diagnostic_only_not_added_to_main_score"
        )

    def test_particle_channel_coherent_addition_without_guard_is_blocked(self):
        cfg = replace(
            DEFAULT_SIM_CFG,
            particle_induced_channel_perturbation_model=(
                "excluded_volume_phase_surrogate"
            ),
            particle_channel_perturbation_application_mode=(
                "coherent_addition_with_no_double_count_guard"
            ),
        )
        diagnostics = build_particle_channel_perturbation_diagnostics(
            Particle("ev_like_test", 50e-9, 1.45),
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            E_ref_complex=1.0 + 0.0j,
            E_sca_unit_normalized_complex=0.1 + 0.0j,
        )
        assert diagnostics["no_double_count_guard_passed"] is False
        assert diagnostics["particle_channel_perturbation_claim_level"] == (
            "blocked_coherent_addition_without_double_count_guard"
        )
        assert diagnostics["particle_channel_double_count_guard_status"] == (
            "blocked_coherent_application_without_validated_guard"
        )

    def test_rectangular_hydraulic_resistance_uses_short_side_cubed(self):
        shallow = compute_rectangular_channel_hydraulic_resistance(
            800e-9,
            400e-9,
            1.0e-2,
            1.0e-3,
        )
        square = compute_rectangular_channel_hydraulic_resistance(
            800e-9,
            800e-9,
            1.0e-2,
            1.0e-3,
        )
        swapped = compute_rectangular_channel_hydraulic_resistance(
            400e-9,
            800e-9,
            1.0e-2,
            1.0e-3,
        )
        assert shallow > square
        assert swapped == pytest.approx(shallow)

    def test_fluidic_practicality_penalty_exports_pressure_and_gap_risk(self):
        diagnostics = compute_fluidic_practicality_penalty(
            Particle("ev_like_test", 50e-9, 1.45),
            WATER,
            BASELINE_CHANNEL,
            DEFAULT_SIM_CFG,
        )
        assert set(FLUIDIC_RESISTANCE_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["hydraulic_resistance_Pa_s_m3"] > 0.0
        assert diagnostics["pressure_required_for_target_velocity_Pa"] > 0.0
        assert diagnostics["predicted_flow_rate_m3_s"] == pytest.approx(
            DEFAULT_SIM_CFG.mean_flow_velocity_m_s
            * BASELINE_CHANNEL.width_m
            * BASELINE_CHANNEL.depth_m
        )
        assert 0.0 <= diagnostics["fluidic_practicality_penalty"] <= 1.0
        assert diagnostics["accessible_cross_section_fraction"] > 0.0
        assert diagnostics["fluidic_clogging_risk_band"] in {
            "low",
            "moderate",
            "high",
        }

    def test_fluidic_network_diagnostic_blocks_pressure_flow_claims(self):
        diagnostics = build_fluidic_network_diagnostics(
            WATER,
            BASELINE_CHANNEL,
            DEFAULT_SIM_CFG,
        )
        assert set(FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["fluidic_network_schema"] == "fluidic_network_diagnostic_v1"
        assert diagnostics["fluidic_network_model_status"] == (
            "partial_network_nanochannel_array_only"
        )
        assert diagnostics["fluidic_parallel_channel_count"] == 1
        assert diagnostics["fluidic_network_component_count"] == 5
        assert diagnostics["fluidic_network_nanochannel_array_resistance_Pa_s_m3"] > 0.0
        assert diagnostics["fluidic_network_total_flow_rate_m3_s"] == pytest.approx(
            DEFAULT_SIM_CFG.mean_flow_velocity_m_s
            * BASELINE_CHANNEL.width_m
            * BASELINE_CHANNEL.depth_m
        )
        assert diagnostics["fluidic_network_pressure_flow_relation_status"] == (
            "blocked_until_measured_pressure_flow_trace"
        )
        assert diagnostics["fluidic_network_fixed_pressure_prediction_allowed"] is False
        assert diagnostics["fluidic_network_gate_passed"] is False
        assert "measured_pressure_flow_trace" in diagnostics[
            "fluidic_network_missing_component_inputs"
        ]

    def test_fluidic_network_diagnostic_uses_parallel_and_configured_geometry(self):
        cfg = replace(DEFAULT_SIM_CFG)
        setattr(cfg, "fluidic_parallel_channel_count", 4)
        setattr(cfg, "fluidic_microchannel_width_m", 500e-6)
        setattr(cfg, "fluidic_microchannel_depth_m", 5e-6)
        setattr(cfg, "fluidic_microchannel_length_m", 8.0e-3)
        setattr(cfg, "fluidic_capillary_inner_diameter_m", 260e-6)
        setattr(cfg, "fluidic_capillary_length_m", 40.0e-3)
        diagnostics = build_fluidic_network_diagnostics(
            WATER,
            BASELINE_CHANNEL,
            cfg,
        )
        single_resistance = compute_rectangular_channel_hydraulic_resistance(
            BASELINE_CHANNEL.width_m,
            BASELINE_CHANNEL.depth_m,
            cfg.fluidic_channel_length_m,
            float(WATER.viscosity_Pa_s or 1.0e-3),
        )
        assert diagnostics["fluidic_parallel_channel_count"] == 4
        assert diagnostics["fluidic_network_nanochannel_array_resistance_Pa_s_m3"] == (
            pytest.approx(single_resistance / 4.0)
        )
        assert diagnostics["fluidic_network_total_flow_rate_m3_s"] == pytest.approx(
            4.0
            * cfg.mean_flow_velocity_m_s
            * BASELINE_CHANNEL.width_m
            * BASELINE_CHANNEL.depth_m
        )
        assert "microchannel_inlet_outlet" in diagnostics[
            "fluidic_network_known_component_ids"
        ]
        assert "pressure_capillary_link" in diagnostics[
            "fluidic_network_known_component_ids"
        ]
        assert diagnostics["fluidic_network_known_series_resistance_Pa_s_m3"] > (
            diagnostics["fluidic_network_nanochannel_array_resistance_Pa_s_m3"]
        )
        assert diagnostics["fluidic_network_external_geometry_status"] == (
            "configured_external_geometry_partially_computed"
        )
        assert diagnostics["fluidic_network_gate_passed"] is False

    def test_particle_design_library_exposes_standard_and_contaminant_presets(self):
        assert "polystyrene_50nm" in STANDARD_PARTICLE_PRESETS
        assert "silica_dust" in PARTICLE_CONTAMINANT_PRESETS
        for contaminant_id in (
            "HDL_like",
            "VLDL_like",
            "chylomicron_like",
            "LNP_like",
            "PEG_polymer_aggregate",
            "salt_crystal_dust",
            "nanobubble",
            "cell_debris",
            "OMV_like",
            "virus_like",
            "column_resin_particle",
        ):
            assert contaminant_id in PARTICLE_CONTAMINANT_PRESETS
        assert "SEC" in EV_SAMPLE_PREPARATION_PROFILES
        standard = build_particle_design_library_diagnostics(
            Particle("polystyrene_50nm", 25e-9, 1.59),
            DEFAULT_SIM_CFG,
        )
        assert set(PARTICLE_DESIGN_LIBRARY_DIAGNOSTIC_FIELDS).issubset(standard)
        assert standard["standard_particle_family"] == "polystyrene"
        assert standard["standard_particle_calibration_role"] == "fit"
        assert standard["calibration_train_or_validation_split"] == "fit"
        assert standard["calibration_transfer_to_EV_risk"] == (
            "high_material_mismatch_to_EV"
        )
        resin = build_particle_design_library_diagnostics(
            Particle("column_resin_particle_150nm", 75e-9, 1.59),
            DEFAULT_SIM_CFG,
        )
        assert resin["contaminant_family"] == "resin_particle"
        assert resin["contaminant_detectability_score"] == pytest.approx(0.90)
        assert resin["EV_specificity_risk"] == "contaminant_control_particle"
        assert resin["contaminant_preset_count"] >= 15

    def test_particle_design_library_marks_ev_specificity_proxy(self):
        cfg = replace(DEFAULT_SIM_CFG, EV_sample_preparation_profile="SEC")
        ev_particle = make_biomimetic_exosome_particle(100)
        diagnostics = build_particle_design_library_diagnostics(ev_particle, cfg)
        assert diagnostics["shape_model"] in {
            "sphere",
            "spheroid_orientation_average",
        }
        assert diagnostics["EV_sample_preparation_profile"] == "SEC"
        assert diagnostics["EV_model_weight"] == pytest.approx(0.9)
        assert diagnostics["EV_specificity_risk"] == (
            "proxy_overlap_requires_contaminant_panel"
        )
        assert diagnostics["contaminant_panel_coverage_status"] == (
            "expanded_screening_panel_metadata_only"
        )
        assert diagnostics["contaminant_detectability_score"] == pytest.approx(0.5)

    def test_sim_config_explicit_legacy_chain_is_still_available(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            phase_model="constant",
            reference_model="constant",
            reference_spatial_mode="uniform",
            collection_angle_model="fixed",
            collection_integration_mode="single_angle",
            scattering_projection_mode="intensity_proxy",
            pulse_detection_mode="positive",
            readout_model="raw",
            normalization_mode="global_single_lambda",
        )
        assert cfg.phase_model == "constant"
        assert cfg.reference_model == "constant"
        assert cfg.reference_spatial_mode == "uniform"
        assert cfg.collection_angle_model == "fixed"
        assert cfg.collection_integration_mode == "single_angle"
        assert cfg.scattering_projection_mode == "intensity_proxy"
        assert cfg.pulse_detection_mode == "positive"
        assert cfg.readout_model == "raw"
        assert cfg.normalization_mode == "global_single_lambda"

    def test_sim_config_rejects_invalid_polarization_modes(self):
        with pytest.raises(ValueError, match="illumination_polarization_mode"):
            SimulationConfig(0.2, 20000.0, 2e-4, illumination_polarization_mode="diagonal")
        with pytest.raises(ValueError, match="reference_projection_mode"):
            SimulationConfig(0.2, 20000.0, 2e-4, reference_projection_mode="circular")

    def test_sim_config_rejects_invalid_cross_polarization_leakage(self):
        with pytest.raises(ValueError, match="cross_polarization_leakage"):
            SimulationConfig(0.2, 20000.0, 2e-4, cross_polarization_leakage=1.2)

    def test_sim_config_rejects_invalid_reference_phase_grating_mode(self):
        with pytest.raises(ValueError, match="reference_phase_grating_mode"):
            SimulationConfig(0.2, 20000.0, 2e-4, reference_phase_grating_mode="phase_plate")

    def test_sim_config_rejects_invalid_reference_width_saturation_mode(self):
        with pytest.raises(ValueError, match="reference_width_saturation_mode"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                reference_width_saturation_mode="hard_cutoff",
            )

    def test_sim_config_rejects_invalid_reference_width_saturation_cutoff_ratio(self):
        with pytest.raises(ValueError, match="reference_width_saturation_cutoff_ratio"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                reference_width_saturation_cutoff_ratio=0.0,
            )

    def test_sim_config_validates_reference_na_edge_policy(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            reference_na_edge_policy="soft_rolloff",
            reference_na_rolloff_width_deg=3.0,
        )
        assert cfg.reference_na_edge_policy == "soft_rolloff"
        assert cfg.reference_na_rolloff_width_deg == pytest.approx(3.0)
        with pytest.raises(ValueError, match="reference_na_edge_policy"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                reference_na_edge_policy="silent_clip",
            )
        with pytest.raises(ValueError, match="reference_na_rolloff_width_deg"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                reference_na_rolloff_width_deg=0.0,
            )

    def test_sim_config_rejects_unsupported_complex_field_conventions(self):
        with pytest.raises(ValueError, match="interference_conjugation_convention"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                interference_conjugation_convention="Re_conj_Eref_Esca",
            )
        with pytest.raises(ValueError, match="vector_optics_mode"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                vector_optics_mode="vector_debye_full",
            )
        with pytest.raises(ValueError, match="polarization_jones_operator_mode"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                polarization_jones_operator_mode="full_vector_debye",
            )
        with pytest.raises(ValueError, match="measured_jones_matrix_path"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                measured_jones_matrix_path="",
            )

    def test_sim_config_rejects_unsupported_absolute_scattering_routes(self):
        with pytest.raises(ValueError, match="scattering_normalization_route"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                scattering_normalization_route="detector_calibrated",
            )
        with pytest.raises(ValueError, match="K_sca_calibration_status"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                K_sca_calibration_status="single_point_calibration",
            )
        with pytest.raises(ValueError, match="standard_particle_calibration_path"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                standard_particle_calibration_path="/missing/standards.csv",
            )

    def test_sim_config_rejects_unsupported_detector_unit_noise_routes(self):
        with pytest.raises(ValueError, match="detector_noise_model_route"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                detector_noise_model_route="photon_unit",
            )
        with pytest.raises(ValueError, match="detector_dynamic_range_model"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                detector_dynamic_range_model="hard_saturation",
            )
        with pytest.raises(ValueError, match="collection_operator_calibration_path"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                absolute_throughput_route="calibrated_operator_table",
            )
        with pytest.raises(ValueError, match="absolute_throughput_route"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                absolute_throughput_route="calibrated_detector",
            )
        with pytest.raises(ValueError, match="collection_operator_calibration_path"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                collection_operator_calibration_path="/missing/operator_table.csv",
            )

    def test_sim_config_rejects_unsupported_background_field_routes(self):
        with pytest.raises(ValueError, match="background_field_model"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                background_field_model="measured_blank_field",
            )
        with pytest.raises(ValueError, match="transmitted_leakage_model"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                transmitted_leakage_model="calibrated_leakage_field",
            )

    def test_sim_config_rejects_unsupported_readout_governance_routes(self):
        with pytest.raises(ValueError, match="readout_preset"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                readout_preset="paperish",
            )
        with pytest.raises(ValueError, match="electronics_demod_phase_policy"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                electronics_demod_phase_policy="implicit",
            )
        with pytest.raises(ValueError, match="nodi_readout_semantics"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                nodi_readout_semantics="phase_locked_by_assumption",
            )
        with pytest.raises(ValueError, match="readout_internal_demod_route"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                readout_internal_demod_route="low_rate_carrier",
            )
        with pytest.raises(ValueError, match="objective_candidate_id"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                objective_candidate_id="",
            )
        with pytest.raises(ValueError, match="lockin_output_unit_convention"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                lockin_output_unit_convention="microvolt_claim",
            )
        with pytest.raises(ValueError, match="threshold_tail"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                threshold_tail="signed",
            )
        with pytest.raises(ValueError, match="threshold_calibration_source"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                threshold_calibration_source="colored_noise_guess",
            )
        with pytest.raises(ValueError, match="blank_false_positive_calibration_path"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                blank_false_positive_calibration_path="/missing/blank_fp.csv",
            )
        with pytest.raises(ValueError, match="raw_blank_trace_path"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                raw_blank_trace_path="/missing/raw_blank.csv",
            )
        with pytest.raises(ValueError, match="bfp_roi_mask_path"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                bfp_roi_mask_path="/missing/bfp_roi.json",
            )
        with pytest.raises(ValueError, match="particle_uncertainty_propagation_mode"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                particle_uncertainty_propagation_mode="implicit_random_draws",
            )
        with pytest.raises(ValueError, match="particle_uncertainty_budget_model"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                particle_uncertainty_budget_model="hidden_uncertainty",
            )
        with pytest.raises(ValueError, match="EV_ensemble_mode"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                EV_ensemble_mode="random_hidden_samples",
            )
        with pytest.raises(ValueError, match="count_prediction_model"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                count_prediction_model="flow_rate_guess",
            )
        with pytest.raises(ValueError, match="number_concentration_m3"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                number_concentration_m3=-1.0,
            )
        with pytest.raises(ValueError, match="count_dead_time_s"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                count_dead_time_s=-1.0e-3,
            )
        with pytest.raises(ValueError, match="wall_interaction_model"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                wall_interaction_model="sticky",
            )
        with pytest.raises(ValueError, match="interface_correction_mode"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                interface_correction_mode="image_charge_guess",
            )
        with pytest.raises(ValueError, match="interface_correction_priority"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                interface_correction_priority="exosome_only",
            )
        with pytest.raises(ValueError, match="interface_correction_applied_to"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                interface_correction_applied_to="hidden_subset",
            )
        with pytest.raises(ValueError, match="thermal_pod_model"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                thermal_pod_model="scalar_delta_n",
            )
        with pytest.raises(ValueError, match="pod_roi_sensitivity_derivative_status"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                pod_roi_sensitivity_derivative_status="hidden_scalar",
            )
        with pytest.raises(ValueError, match="pod_signal_sign_source"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                pod_signal_sign_source="sign_delta_n",
            )
        with pytest.raises(ValueError, match="pod_thermal_spatial_distribution_status"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                pod_thermal_spatial_distribution_status="thermal_blob",
            )
        with pytest.raises(ValueError, match="pod_roi_derivative_validity"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                pod_roi_derivative_validity="trusted",
            )
        with pytest.raises(ValueError, match="probe_wavelength_m"):
            SimulationConfig(0.2, 20000.0, 2e-4, probe_wavelength_m=0.0)
        with pytest.raises(ValueError, match="excitation_wavelength_m"):
            SimulationConfig(0.2, 20000.0, 2e-4, excitation_wavelength_m=-532e-9)
        with pytest.raises(ValueError, match="probe_power_W"):
            SimulationConfig(0.2, 20000.0, 2e-4, probe_power_W=-1.0e-3)
        with pytest.raises(ValueError, match="excitation_power_W"):
            SimulationConfig(0.2, 20000.0, 2e-4, excitation_power_W=-1.0e-3)

    def test_sim_config_rejects_invalid_interference_overlap_mode(self):
        with pytest.raises(ValueError, match="interference_overlap_mode"):
            SimulationConfig(0.2, 20000.0, 2e-4, interference_overlap_mode="joint_field")

    def test_sim_config_rejects_invalid_pod_frequency_response_bounds(self):
        with pytest.raises(ValueError, match="pod_frequency_response_model"):
            SimulationConfig(0.2, 20000.0, 2e-4, pod_frequency_response_model="thermal")
        with pytest.raises(ValueError, match="pod_frequency_response_max_gain"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                pod_frequency_response_min_gain=1.0,
                pod_frequency_response_max_gain=0.5,
            )
        with pytest.raises(ValueError, match="nodi_transit_response_model"):
            SimulationConfig(0.2, 20000.0, 2e-4, nodi_transit_response_model="thermal")
        with pytest.raises(ValueError, match="nodi_transit_response_max_gain"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                nodi_transit_response_min_gain=0.8,
                nodi_transit_response_max_gain=0.5,
            )

    def test_sim_config_rejects_invalid_initial_position_distribution_mode(self):
        with pytest.raises(ValueError, match="initial_position_distribution_mode"):
            SimulationConfig(0.2, 20000.0, 2e-4, initial_position_distribution_mode="bad_mode")
        SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            initial_position_distribution_mode="uniform_accessible_area",
        )
        SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            initial_position_distribution_mode="flux_weighted",
        )
        SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            initial_position_distribution_mode="flux_uniform_mixture_surrogate",
            initial_position_flux_weighted_mixture_fraction=0.25,
            pulse_extraction_sampling_interval_s=5.0e-4,
        )
        with pytest.raises(ValueError, match="schema-reserved"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                initial_position_distribution_mode="electrostatic_equilibrium",
            )
        with pytest.raises(ValueError, match="initial_position_center_bias_strength"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                initial_position_center_bias_strength=-0.1,
            )
        with pytest.raises(ValueError, match="initial_position_flux_weighted_mixture_fraction"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                initial_position_flux_weighted_mixture_fraction=1.1,
            )
        with pytest.raises(ValueError, match="pulse_extraction_sampling_interval_s"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                pulse_extraction_sampling_interval_s=0.0,
            )
        with pytest.raises(ValueError, match="pulse_duration_estimation_policy"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                pulse_duration_estimation_policy="optimistic_logger_width",
            )
        with pytest.raises(ValueError, match="post_readout_colored_noise_std"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                post_readout_colored_noise_std=-0.1,
            )
        with pytest.raises(ValueError, match="post_readout_colored_noise_tau_s"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                post_readout_colored_noise_tau_s=0.0,
            )
        with pytest.raises(
            ValueError,
            match="initial_position_center_bias_min_confinement_ratio",
        ):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                initial_position_center_bias_min_confinement_ratio=1.0,
            )

    def test_sim_config_rejects_invalid_sampling_and_adaptive_policies(self):
        with pytest.raises(ValueError, match="random_sequence_policy"):
            SimulationConfig(0.2, 20000.0, 2e-4, random_sequence_policy="same")
        with pytest.raises(ValueError, match="event_sampling_policy"):
            SimulationConfig(0.2, 20000.0, 2e-4, event_sampling_policy="halton")
        with pytest.raises(ValueError, match="adaptive_event_budget_mode"):
            SimulationConfig(0.2, 20000.0, 2e-4, adaptive_event_budget_mode="early")
        with pytest.raises(ValueError, match="adaptive_min_events"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                n_events=4,
                adaptive_event_budget_mode="wilson_precision",
                adaptive_min_events=5,
            )
        with pytest.raises(ValueError, match="vectorized_event_engine"):
            SimulationConfig(0.2, 20000.0, 2e-4, vectorized_event_engine="always")
        with pytest.raises(ValueError, match="event_block_size"):
            SimulationConfig(0.2, 20000.0, 2e-4, event_block_size=0)
        with pytest.raises(ValueError, match="event_block_rng_order"):
            SimulationConfig(0.2, 20000.0, 2e-4, event_block_rng_order="same")
        with pytest.raises(ValueError, match="pulse_width_measure_mode"):
            SimulationConfig(0.2, 20000.0, 2e-4, pulse_width_measure_mode="duration")

    def test_sim_config_rejects_invalid_path_opd_model(self):
        with pytest.raises(ValueError, match="path_opd_model"):
            SimulationConfig(0.2, 20000.0, 2e-4, path_opd_model="roundtrip")

    def test_sim_config_validates_flow_control_metadata(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            flow_control_mode="fixed_pressure",
            flow_control_pressure_Pa=2500.0,
            fluidic_channel_length_m=5.0e-3,
        )
        assert cfg.flow_control_mode == "fixed_pressure"
        assert cfg.flow_control_pressure_Pa == pytest.approx(2500.0)
        assert cfg.fluidic_channel_length_m == pytest.approx(5.0e-3)
        with pytest.raises(ValueError, match="flow_control_mode"):
            SimulationConfig(0.2, 20000.0, 2e-4, flow_control_mode="open_loop")
        with pytest.raises(ValueError, match="flow_control_pressure_Pa"):
            SimulationConfig(0.2, 20000.0, 2e-4, flow_control_pressure_Pa=-1.0)
        with pytest.raises(ValueError, match="fluidic_channel_length_m"):
            SimulationConfig(0.2, 20000.0, 2e-4, fluidic_channel_length_m=0.0)

    def test_sim_config_validates_ev_sample_preparation_profile(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            EV_sample_preparation_profile="SEC",
        )
        assert cfg.EV_sample_preparation_profile == "SEC"
        with pytest.raises(ValueError, match="EV_sample_preparation_profile"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                EV_sample_preparation_profile="mystery_gradient",
            )

    def test_sim_config_accepts_paper_aligned_phase_filter_reference_model(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            reference_model="paper_aligned_phase_filter",
            reference_route="paper_aligned_comparison",
        )
        assert cfg.reference_model == "paper_aligned_phase_filter"
        assert cfg.reference_route == "paper_aligned_comparison"

    def test_sim_config_accepts_tsuyama_bfp_integrated_reference_model(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            reference_model="tsuyama_bfp_integrated",
            reference_route="paper_aligned_comparison",
        )
        assert cfg.reference_model == "tsuyama_bfp_integrated"
        assert cfg.reference_route == "paper_aligned_comparison"

    def test_sim_config_rejects_reference_route_model_mismatch(self):
        with pytest.raises(ValueError, match="reference_route"):
            SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                reference_model="channel_angular_surrogate",
                reference_route="calibrated_primary",
            )


class TestMie:
    def test_zero_size_parameter(self):
        qext, qsca = mie_compute(0.0, complex(1.5, 0))
        assert qext == 0.0
        assert qsca == 0.0

    def test_qsca_positive(self):
        qext, qsca = mie_compute(0.5, complex(1.5, 0))
        assert qsca >= 0
        assert qext >= 0

    def test_qsca_le_qext(self):
        qext, qsca = mie_compute(0.5, complex(1.5, 0.1))
        assert qsca <= qext + 1e-10

    def test_no_absorption_dielectric(self):
        qext, qsca = mie_compute(1.0, complex(1.5, 0))
        assert abs(qext - qsca) < 0.01 * qext

    def test_angular_shapes(self):
        theta = np.linspace(0.01, np.pi - 0.01, 100)
        s1, s2 = mie_angular(0.5, complex(1.5, 0), theta)
        assert s1.shape == (100,)
        assert s2.shape == (100,)

    def test_core_shell_reduces_to_homogeneous_when_indices_match(self):
        x_outer = 1.2
        m_rel = complex(1.42, 0.0)
        a_hom, b_hom = mie_coefficients(x_outer, m_rel)
        a_shell, b_shell = mie_core_shell_coefficients(
            x_outer,
            core_radius_ratio=0.65,
            m_shell_rel=m_rel,
            m_core_rel=m_rel,
        )
        assert np.allclose(a_shell, a_hom, rtol=1e-7, atol=1e-10)
        assert np.allclose(b_shell, b_hom, rtol=1e-7, atol=1e-10)


class TestIntrinsicScattering:
    def test_cross_sections_positive(self):
        result = compute_intrinsic_scattering(BASELINE_PARTICLE, WATER, 660e-9, THETA_GRID)
        assert result["Csca_m2"] >= 0
        assert result["Cext_m2"] >= 0

    def test_intrinsic_scattering_exports_canonical_k_m_alias_boundary(self):
        result = compute_intrinsic_scattering(BASELINE_PARTICLE, WATER, 660e-9, THETA_GRID)
        expected_k = 2.0 * np.pi * WATER.refractive_index_at(660e-9) / 660e-9
        assert result["k_m"] == pytest.approx(expected_k)
        assert result["k_m_inv"] == pytest.approx(result["k_m"])
        assert result["k_m_inv_alias_status"] == (
            "deprecated_legacy_alias_for_k_m_not_inverse"
        )

    def test_cabs_equals_cext_minus_csca(self):
        result = compute_intrinsic_scattering(BASELINE_PARTICLE, WATER, 660e-9, THETA_GRID)
        assert result["Cabs_m2"] == pytest.approx(result["Cext_m2"] - result["Csca_m2"], abs=1e-30)

    def test_dcsca_domega_nonnegative(self):
        result = compute_intrinsic_scattering(BASELINE_PARTICLE, WATER, 660e-9, THETA_GRID)
        assert np.all(result["dCsca_dOmega_m2_sr"] >= 0)

    def test_dcsca_integrates_to_csca(self):
        theta = np.linspace(1e-4, np.pi - 1e-4, 5000)
        result = compute_intrinsic_scattering(BASELINE_PARTICLE, WATER, 660e-9, theta)
        csca_from_angle = 2 * np.pi * np.trapezoid(
            result["dCsca_dOmega_m2_sr"] * np.sin(theta),
            theta,
        )
        assert csca_from_angle == pytest.approx(result["Csca_m2"], rel=1e-3)

    def test_mie_validation_diagnostics_expose_hard_gate_status(self):
        result = compute_intrinsic_scattering(BASELINE_PARTICLE, WATER, 660e-9, THETA_GRID)
        diagnostics = build_mie_validation_diagnostics(result, DEFAULT_SIM_CFG)
        assert diagnostics["mie_validation_status"] == "pass"
        assert diagnostics["mie_validation_hard_gate_passed"] is True
        assert diagnostics["mie_cross_section_payload_valid"] is True
        assert diagnostics["mie_angular_payload_valid"] is True
        assert diagnostics["mie_amplitude_normalization_status"] == (
            "S1S2_to_dCsca_dOmega_runtime_payload_present"
        )

    def test_small_particle_csca_scaling(self):
        radii = [5e-9, 10e-9, 15e-9, 20e-9]
        csca_values = []
        for radius in radii:
            particle = Particle("test", radius, 1.5, 0.0)
            result = compute_intrinsic_scattering(particle, WATER, 660e-9, THETA_GRID)
            csca_values.append(result["Csca_m2"])
        slope = np.polyfit(np.log(radii), np.log(csca_values), 1)[0]
        assert 5.0 < slope < 7.0

    def test_no_absorption_particle(self):
        particle = Particle("dielectric", 20e-9, 1.5, 0.0)
        result = compute_intrinsic_scattering(particle, WATER, 660e-9, THETA_GRID)
        assert result["Cabs_m2"] < 1e-3 * result["Cext_m2"]

    def test_biomimetic_exosome_scattering_exceeds_uniform_for_100nm(self):
        uniform = Particle("exosome_uniform_100nm", 50e-9, 1.38, 0.0)
        biomimetic = make_biomimetic_exosome_particle(100)
        uniform_result = compute_intrinsic_scattering(uniform, WATER, 404e-9, THETA_GRID)
        biomimetic_result = compute_intrinsic_scattering(
            biomimetic,
            WATER,
            404e-9,
            THETA_GRID,
        )
        assert biomimetic_result["Csca_m2"] > uniform_result["Csca_m2"]
        assert biomimetic_result["relative_index"].real > uniform_result["relative_index"].real
        assert biomimetic_result["structured_particle_spec"]["core_radius_ratio"] < 1.0

    def test_exosome_preset_catalog_includes_literature_bounds(self):
        presets = list_exosome_model_presets()
        assert "membrane_only_dim_2021" in presets
        assert "membrane_only_nominal_2020" in presets
        assert "biomimetic_corona_nominal" in presets
        assert "surface_loaded_bright_2021" in presets

    def test_ev_sev_ensemble_factory_expands_to_explicit_preset_cases(self):
        ensembles = list_ev_sev_ensemble_presets()
        assert "literature_bounds_2021" in ensembles
        particles = make_biomimetic_exosome_ensemble_particles(
            100,
            ensemble_name="literature_bounds_2021",
        )
        assert len(particles) == 4
        assert {p.structure_params["EV_ensemble_member_preset"] for p in particles} == {
            "membrane_only_dim_2021",
            "membrane_only_nominal_2020",
            "biomimetic_corona_nominal",
            "surface_loaded_bright_2021",
        }
        first = particles[0]
        assert first.structure_params["EV_ensemble_name"] == "literature_bounds_2021"
        assert first.structure_params["EV_ensemble_member_index"] == 0
        assert first.structure_params["EV_ensemble_member_count"] == 4

    def test_exosome_preset_factory_preserves_selected_preset(self):
        particle = make_biomimetic_exosome_particle(
            100,
            preset_name="surface_loaded_bright_2021",
        )
        result = compute_intrinsic_scattering(particle, WATER, 404e-9, THETA_GRID)
        spec = result["structured_particle_spec"]
        preset = get_exosome_model_preset("surface_loaded_bright_2021")
        assert spec["preset_name"] == "surface_loaded_bright_2021"
        assert spec["params"]["source_type"] == "direct literature scenario"
        assert spec["params"]["membrane_n_real"] == pytest.approx(
            preset["membrane_n_real"]
        )

    def test_particle_model_diagnostics_mark_ev_claim_and_uncertainty_budget(self):
        particle = make_biomimetic_exosome_particle(100)
        intrinsic = compute_intrinsic_scattering(particle, WATER, 404e-9, THETA_GRID)
        diagnostics = build_particle_model_diagnostics(
            particle,
            DEFAULT_SIM_CFG,
            intrinsic=intrinsic,
        )

        assert diagnostics["particle_family"] == "EV_sEV"
        assert diagnostics["particle_optical_model"] == "core_shell_EV_sEV_surrogate"
        assert diagnostics["EV_label"] == "exosome_like"
        assert diagnostics["EV_claim_level"] == "optical_EV_like_particle"
        assert diagnostics["exosome_biogenesis_claim"] == "none"
        assert diagnostics["EV_ensemble_status"] == "nominal_single_preset_no_hidden_sampling"
        assert diagnostics["uncertainty_propagation_status"] == (
            "nominal_only_boundary_no_uncertainty_propagated"
        )
        assert diagnostics["uncertainty_route_active"] is False
        assert diagnostics["particle_material_model_mode"] == "structured_particle_nominal_preset"
        assert (
            diagnostics["particle_material_wavelength_status"]
            == "structured_preset_nominal_no_wavelength_uncertainty"
        )
        assert (
            diagnostics["particle_material_uncertainty_status"]
            == "not_quantified_material_dataset_nominal"
        )
        assert (
            diagnostics["material_db_coverage_status"]
            == "visible_AuAg_medium_wall_dispersion_available_nominal"
        )
        assert diagnostics["tsuyama_AuAg_multispectral_supported"] is True
        assert (
            diagnostics["medium_wall_dispersion_status"]
            == "nominal_visible_dispersion_available_no_uncertainty"
        )
        assert diagnostics["EV_core_RI_nominal"] == pytest.approx(
            intrinsic["structured_particle_spec"]["core_n_complex"].real
        )
        assert diagnostics["EV_shell_RI_nominal"] == pytest.approx(
            intrinsic["structured_particle_spec"]["shell_n_complex"].real
        )
        assert (
            diagnostics["particle_uncertainty_budget_status"]
            == "nominal_only_uncertainty_not_propagated"
        )
        assert diagnostics["uncertainty_propagation_mode"] == "none"
        assert diagnostics["peak_height_CI_available"] is False
        assert diagnostics["classification_probability_CI_available"] is False

    def test_ev_population_prior_exports_correlated_bins_and_low_ri_risk(self):
        particle = make_biomimetic_exosome_particle(100)
        prior = build_ev_population_prior_diagnostics(
            particle,
            {
                "detection_rate": 0.25,
                "event_qc_pass_fraction": 0.8,
                "EV_model_weight": 0.9,
                "low_RI_EV_under_detection_bias": (
                    "possible_low_RI_EV_under_detection"
                ),
            },
            replace(DEFAULT_SIM_CFG, EV_sample_preparation_profile="SEC"),
        )

        assert set(EV_POPULATION_PRIOR_DIAGNOSTIC_FIELDS).issubset(prior)
        assert prior["ev_population_prior_status"] == (
            "correlated_prior_scaffold_active"
        )
        assert prior["ev_prior_physical_validity"] == (
            "valid_correlated_template_no_independent_worst_case"
        )
        assert prior["ev_prior_selection_function_linked"] is True
        assert prior["ev_low_RI_tail_detection_risk"] == (
            "elevated_low_RI_tail_under_detection_risk"
        )
        bins = prior["ev_prior_population_bins"]
        assert isinstance(bins, tuple)
        bin_ids: set[object] = set()
        for item in bins:
            assert isinstance(item, dict)
            bin_ids.add(item["population_bin_id"])
            assert "P_detect" in item
            assert "P_pass_QC" in item
        assert bin_ids == {
            "ev_low_RI_small_tail",
            "ev_nominal_mode",
            "ev_large_or_corona_rich_tail",
        }
        assert prior["ev_prior_gate_passed"] is False

    def test_ev_population_prior_marks_non_ev_particles_not_applicable(self):
        prior = build_ev_population_prior_diagnostics(
            make_gold_baseline_particle(),
            {"detection_rate": 0.9},
            DEFAULT_SIM_CFG,
        )

        assert prior["ev_population_prior_status"] == "not_applicable_non_ev_particle"
        assert prior["ev_prior_population_bins"] == ()
        assert prior["ev_prior_selection_function_linked"] is False
        assert prior["ev_prior_gate_passed"] is False

    def test_material_db_coverage_supports_tsuyama_au_ag_visible_sweeps(self):
        coverage = material_db_coverage_diagnostics()
        assert MATERIAL_DB["gold"]["type"] == "tabulated"
        assert MATERIAL_DB["silver"]["type"] == "tabulated"
        assert coverage["tsuyama_AuAg_multispectral_supported"] is True
        assert coverage["material_db_silver_status"] == "tabulated_visible_available"
        assert np.imag(get_n_complex("silver", 660e-9)) > np.imag(
            get_n_complex("silver", 430e-9)
        )
        assert get_n_complex("fused_silica", 660e-9).real != pytest.approx(
            get_n_complex("fused_silica", 488e-9).real
        )

    def test_gold_material_table_uses_johnson_christy_visible_values(self):
        expected = {
            495.9e-9: (1.04, 1.833),
            520.9e-9: (0.62, 2.081),
            659.5e-9: (0.14, 3.697),
        }
        for wavelength_m, (n_real, n_imag) in expected.items():
            n_complex = get_n_complex("gold", wavelength_m)
            assert n_complex.real == pytest.approx(n_real)
            assert n_complex.imag == pytest.approx(n_imag)

    def test_medium_material_library_exposes_route_43_property_metadata(self):
        expected = {
            "hepes_buffer",
            "culture_medium_surrogate",
            "sucrose_solution_xpct",
            "iodixanol_solution_xpct",
            "fused_silica_viosil",
        }
        assert expected <= set(list_materials())
        for material_key in expected:
            n_complex = get_n_complex(material_key, 660e-9)
            summary = material_property_summary(material_key, 660e-9)
            assert n_complex.real > 1.0
            assert summary["n_real"] == pytest.approx(n_complex.real)
            assert "source" in summary
            assert summary["claim_level"] in {
                "nominal_material_properties_no_uncertainty",
                "vendor_nominal_dispersion_no_uncertainty",
            }
        assert material_property_summary("hepes_buffer", 660e-9)[
            "viscosity_Pa_s"
        ] is not None

    def test_particle_model_diagnostics_report_material_db_provenance(self):
        particle = replace(BASELINE_PARTICLE, material_key="gold", use_material_model=True)
        intrinsic = compute_intrinsic_scattering(particle, WATER, 660e-9, THETA_GRID)
        diagnostics = build_particle_model_diagnostics(
            particle,
            DEFAULT_SIM_CFG,
            intrinsic=intrinsic,
        )

        assert diagnostics["particle_family"] == "gold"
        assert diagnostics["material_dataset"] == "materials_db:gold"
        assert diagnostics["particle_material_model_mode"] == (
            "materials_db_tabulated_interpolation"
        )
        assert diagnostics["particle_material_dataset_source"] == "Johnson & Christy 1972"
        assert diagnostics["particle_material_dataset_type"] == "tabulated"
        assert (
            diagnostics["particle_material_wavelength_status"]
            == "materials_db_interpolation_range_checked"
        )
        assert (
            diagnostics["particle_material_uncertainty_status"]
            == "not_quantified_material_dataset_nominal"
        )


class TestUtils:
    def test_interpolate_at_theta(self):
        theta = np.array([0.1, 0.5, 1.0, 1.5, 3.0])
        values = np.array([1.0, 2.0, 3.0, 2.5, 1.5])
        assert interpolate_at_theta(theta, values, 0.75) == pytest.approx(2.5)

    def test_count_model_diagnostics_separate_flux_counting_from_detectability(self):
        cfg = SimulationConfig(
            10.0,
            20000.0,
            2e-4,
            count_prediction_model="poisson_flux_deadtime_surrogate",
            number_concentration_m3=1.0e15,
            count_dead_time_s=0.1,
            wall_interaction_model="hard_exclusion",
        )
        diagnostics = build_count_model_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_CHANNEL,
            cfg,
            conditional_detection_rate=0.5,
            mean_transit_time_s=0.02,
        )
        accessible_area = (
            BASELINE_CHANNEL.width_m - 2.0 * BASELINE_PARTICLE.radius_m
        ) * (BASELINE_CHANNEL.depth_m - 2.0 * BASELINE_PARTICLE.radius_m)
        event_rate = 1.0e15 * accessible_area * cfg.mean_flow_velocity_m_s
        raw_detected_rate = 0.5 * event_rate
        expected_deadtime_rate = raw_detected_rate / (
            1.0 + raw_detected_rate * cfg.count_dead_time_s
        )

        assert diagnostics["conditional_detection_rate"] == pytest.approx(0.5)
        assert diagnostics["conditional_detection_rate_definition"] == "given_one_particle_event"
        assert diagnostics["conditional_detection_rate_source"] == (
            "provided_event_detection_rate"
        )
        assert (
            diagnostics["count_generation_model"]
            == "per_event_batch_plus_optional_poisson_flux"
        )
        assert (
            diagnostics["per_event_detectability_boundary"]
            == "conditional_detection_rate_not_experiment_count_rate"
        )
        assert diagnostics["accessible_area_m2"] == pytest.approx(accessible_area)
        assert diagnostics["volumetric_flow_rate_m3_s"] == pytest.approx(
            accessible_area * cfg.mean_flow_velocity_m_s
        )
        assert diagnostics["volumetric_flow_rate_source"] == (
            "mean_flow_velocity_times_hard_exclusion_accessible_area"
        )
        assert diagnostics["poisson_arrival_process_status"] == (
            "poisson_arrival_process_surrogate_active"
        )
        assert diagnostics["flux_conditioned_initial_distribution_status"] == (
            "not_implemented_event_positions_sampled_by_transport_surrogate"
        )
        assert diagnostics["crossing_conditioned_transport_status"] == (
            "not_implemented_uses_existing_per_event_initial_distribution"
        )
        assert diagnostics["event_rate_Hz"] == pytest.approx(event_rate)
        assert diagnostics["expected_events_in_window"] == pytest.approx(
            event_rate * cfg.total_time_s
        )
        assert diagnostics["predicted_count_rate_Hz"] == pytest.approx(
            expected_deadtime_rate
        )
        assert diagnostics["dead_time_loss_fraction"] > 0.0
        assert diagnostics["dead_time_correction_status"] == "nonparalyzable_dead_time_applied"
        assert diagnostics["multi_occupancy_probability"] > 0.0
        assert diagnostics["occupancy_correction_status"] == "poisson_focus_occupancy_estimated"
        assert diagnostics["blank_false_positive_correction_status"] == (
            "not_applied_no_empirical_blank_rate"
        )
        assert diagnostics["missed_event_correction_status"] == (
            "conditional_detection_rate_applied_to_flux"
        )
        assert diagnostics["wall_interaction_status"] == "hard_exclusion_accessible_area_only"
        assert diagnostics["count_rate_source"] == "conditional_detection_rate_times_poisson_flux"
        assert diagnostics["count_rate_confidence_status"] == (
            "not_available_no_blank_false_positive_or_uncertainty_propagation"
        )
        assert diagnostics["count_prediction_uncertainty_status"] == "not_propagated"

    def test_count_model_records_event_qc_conditioned_rate_source(self):
        cfg = SimulationConfig(
            10.0,
            20000.0,
            2e-4,
            count_prediction_model="poisson_flux_deadtime_surrogate",
            number_concentration_m3=1.0e15,
            wall_interaction_model="hard_exclusion",
        )
        diagnostics = build_count_model_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_CHANNEL,
            cfg,
            conditional_detection_rate=0.25,
            conditional_detection_rate_source="detected_rate_after_event_qc",
            mean_transit_time_s=0.02,
        )

        assert diagnostics["conditional_detection_rate"] == pytest.approx(0.25)
        assert diagnostics["conditional_detection_rate_definition"] == (
            "given_one_particle_event_after_event_qc"
        )
        assert diagnostics["conditional_detection_rate_source"] == (
            "detected_rate_after_event_qc"
        )
        assert diagnostics["count_rate_source"] == (
            "event_qc_conditioned_detection_rate_times_poisson_flux"
        )

    def test_log_likelihood_counts_uses_poisson_count_model(self):
        expected = 3.5
        observed = 4

        assert log_likelihood_counts(observed, expected) == pytest.approx(
            observed * np.log(expected) - expected - math.lgamma(observed + 1)
        )
        assert log_likelihood_counts(0, 0.0) == pytest.approx(0.0)
        assert log_likelihood_counts(2, 0.0) == float("-inf")
        with pytest.raises(ValueError, match="expected_count"):
            log_likelihood_counts(1, -1.0)

    def test_count_likelihood_reports_corrected_counts_and_exploratory_blockers(self):
        cfg = SimulationConfig(
            10.0,
            20000.0,
            2e-4,
            count_prediction_model="poisson_flux_deadtime_surrogate",
            number_concentration_m3=1.0e15,
            count_dead_time_s=0.05,
            wall_interaction_model="hard_exclusion",
        )
        count_model = build_count_model_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_CHANNEL,
            cfg,
            conditional_detection_rate=0.5,
            mean_transit_time_s=0.02,
            blank_false_positive_rate_Hz=0.1,
        )
        diagnostics = build_count_likelihood_diagnostics(
            {"n_detected": 5},
            count_model,
            cfg,
        )

        assert set(COUNT_LIKELIHOOD_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["count_likelihood_status"] == (
            "poisson_log_likelihood_active"
        )
        assert diagnostics["observed_count"] == 5
        assert diagnostics["expected_count_for_likelihood"] == pytest.approx(
            count_model["predicted_counts_in_window"]
        )
        assert diagnostics["false_positive_expected_count"] == pytest.approx(1.0)
        assert diagnostics["false_positive_corrected_count"] == pytest.approx(4.0)
        assert diagnostics["false_negative_expected_count"] == pytest.approx(
            count_model["missed_event_rate_Hz"] * cfg.total_time_s
        )
        assert diagnostics["false_negative_corrected_count"] == pytest.approx(
            diagnostics["false_positive_corrected_count"]
            + diagnostics["false_negative_expected_count"]
        )
        assert diagnostics["count_log_likelihood"] == pytest.approx(
            log_likelihood_counts(5, count_model["predicted_counts_in_window"])
        )
        assert diagnostics["count_likelihood_claim_level"] == (
            "exploratory_poisson_likelihood_missing_calibration"
        )
        assert diagnostics["count_likelihood_gate_passed"] is False
        assert "dead_time_calibration_not_empirical" in diagnostics[
            "count_likelihood_blocker_summary"
        ]

    def test_count_likelihood_disabled_route_keeps_claim_exploratory(self):
        count_model = build_count_model_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_CHANNEL,
            DEFAULT_SIM_CFG,
            conditional_detection_rate=0.25,
            mean_transit_time_s=0.02,
        )
        diagnostics = build_count_likelihood_diagnostics(
            {"n_detected": 3},
            count_model,
            DEFAULT_SIM_CFG,
        )

        assert diagnostics["count_likelihood_status"] == (
            "unavailable_without_count_prediction"
        )
        assert diagnostics["expected_count_for_likelihood"] is None
        assert diagnostics["count_log_likelihood"] is None
        assert diagnostics["false_positive_corrected_count"] == pytest.approx(3.0)
        assert diagnostics["count_likelihood_claim_level"] == (
            "exploratory_no_count_prediction"
        )
        assert "expected_count_unavailable" in diagnostics[
            "count_likelihood_blocker_summary"
        ]

    def test_ood_detection_accepts_in_envelope_case_but_blocks_hard_classifier(self):
        diagnostics = build_ood_detection_diagnostics(
            BASELINE_PARTICLE,
            {
                "detection_rate": 0.8,
                "stable_detection_rate": 0.75,
                "mean_peak_margin_z": 3.0,
                "event_artifact_risk_score": 0.1,
                "EV_to_contaminant_signal_overlap": 0.0,
                "phase_flip_fraction": 0.05,
            },
            DEFAULT_SIM_CFG,
        )

        assert set(OOD_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["unknown_particle_flag"] is False
        assert diagnostics["classifier_rejection_rate"] == pytest.approx(0.0)
        assert diagnostics["ood_gate_passed"] is True
        assert (
            diagnostics["EV_contaminant_hard_classification_allowed"] is False
        )
        assert diagnostics["EV_contaminant_classifier_claim_level"] == (
            "blocked_until_trained_classifier_and_ood_rejection_calibrated"
        )

    def test_ood_detection_rejects_unknown_instead_of_forced_ev_or_contaminant(self):
        particle = make_biomimetic_exosome_particle(100)
        diagnostics = build_ood_detection_diagnostics(
            particle,
            {
                "detection_rate": 0.05,
                "stable_detection_rate": 0.02,
                "mean_peak_margin_z": 0.1,
                "event_artifact_risk_score": 0.8,
                "EV_to_contaminant_signal_overlap": 0.95,
                "phase_flip_fraction": 0.7,
            },
            DEFAULT_SIM_CFG,
        )

        assert diagnostics["unknown_particle_flag"] is True
        assert diagnostics["classifier_rejection_rate"] == pytest.approx(1.0)
        assert diagnostics["unknown_particle_reason"] in {
            "density_below_one_class_threshold",
            "mahalanobis_distance_outside_surrogate_envelope",
            "event_artifact_risk_high",
            "ev_contaminant_feature_overlap_high",
        }
        assert diagnostics["EV_contaminant_hard_classification_allowed"] is False
        assert "unknown_particle_rejected_not_hard_classified" in diagnostics[
            "ood_blocker_summary"
        ]

    def test_count_model_disabled_still_reports_accessible_area_and_wall_status(self):
        diagnostics = build_count_model_diagnostics(
            BASELINE_PARTICLE,
            BASELINE_CHANNEL,
            DEFAULT_SIM_CFG,
            conditional_detection_rate=0.25,
            mean_transit_time_s=0.02,
        )
        assert diagnostics["count_prediction_status"] == "not_applied_per_event_detection_only"
        assert diagnostics["poisson_arrival_process_status"] == (
            "not_applied_count_prediction_disabled"
        )
        assert diagnostics["crossing_conditioned_transport_status"] == (
            "not_implemented_uses_existing_per_event_initial_distribution"
        )
        assert diagnostics["count_rate_confidence_status"] == (
            "not_available_no_blank_false_positive_or_uncertainty_propagation"
        )
        assert diagnostics["predicted_count_rate_Hz"] is None
        assert diagnostics["accessible_area_m2"] > 0.0
        assert diagnostics["wall_interaction_status"] == "wall_interaction_unmodeled"

    def test_interface_correction_diagnostics_default_to_visible_homogeneous_mie(self):
        diagnostics = build_interface_correction_diagnostics(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            DEFAULT_SIM_CFG,
        )
        assert diagnostics["interface_correction_mode"] == "off"
        assert (
            diagnostics["interface_correction_status"]
            == "homogeneous_medium_mie_no_interface_correction"
        )
        assert diagnostics["interface_correction_particle_family"] == "gold"
        assert diagnostics["interface_correction_input_contract_schema"] == (
            "interface_correction_input_contract_v1"
        )
        assert diagnostics["interface_api_boundary_status"] == (
            "blocked_missing_interface_solver_inputs"
        )
        assert "interface_green_function_or_tmatrix" in diagnostics[
            "interface_missing_inputs"
        ]
        assert diagnostics["homogeneous_medium_mie_assumption"] is True
        assert diagnostics["interface_incident_field_correction"] == "unmodeled"
        assert diagnostics["interface_particle_polarizability_correction"] == "unmodeled"
        assert (
            diagnostics["interface_output_sensitivity_status"]
            == "phase_polarity_and_angular_pattern_sensitive"
        )
        assert diagnostics["interface_phase_or_polarity_sensitive_output"] is True
        assert diagnostics["interface_angular_pattern_sensitive_output"] is True
        assert diagnostics["interface_fullwave_required"] is True
        assert "phase_polarity_or_angular_pattern_output" in diagnostics[
            "interface_fullwave_reason"
        ]
        assert "homogeneous_medium_interface_unmodeled" in diagnostics[
            "interface_quantitative_claim_blocker_summary"
        ]
        assert diagnostics["eta_interface"] > 0.0
        assert diagnostics["eta_lambda"] > 0.0

    def test_interface_correction_diagnostics_flag_ev_first_surrogate_scope(self):
        particle = make_biomimetic_exosome_particle(100)
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            interface_correction_mode="dipole_image_surrogate",
            interface_correction_priority="EV_first",
            interface_correction_applied_to="selected_family",
        )
        diagnostics = build_interface_correction_diagnostics(
            particle,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
        )
        assert diagnostics["interface_correction_particle_family"] == "EV_sEV"
        assert diagnostics["interface_correction_active"] is True
        assert diagnostics["interface_particle_polarizability_correction"] == (
            "dipole_image_first_order_surrogate"
        )
        assert diagnostics["interface_correction_claim_level"] == (
            "first_order_near_interface_surrogate_not_fullwave"
        )
        assert diagnostics["interface_dipole_surrogate_validity"] == (
            "first_order_only_not_quantitative_for_sensitive_outputs"
        )
        assert "dipole_image_surrogate_not_quantitative" in diagnostics[
            "interface_quantitative_claim_blocker_summary"
        ]

    def test_photothermal_pod_diagnostics_keep_default_pod_quantitative_route_blocked(self):
        diagnostics = build_photothermal_pod_diagnostics(BASELINE_OPTICAL, DEFAULT_SIM_CFG)
        assert diagnostics["thermal_pod_model"] == "unavailable"
        assert diagnostics["thermal_pod_input_contract_schema"] == (
            "thermal_pod_input_contract_v1"
        )
        assert diagnostics["thermal_pod_api_boundary_status"] == (
            "blocked_missing_required_inputs_or_solver"
        )
        assert "heat_diffusion_solver" in diagnostics["thermal_pod_missing_inputs"]
        assert diagnostics["thermal_pod_model_status"] == "unavailable_no_heat_diffusion_model"
        assert diagnostics["probe_wavelength_m"] == pytest.approx(BASELINE_OPTICAL.wavelength_m)
        assert diagnostics["excitation_wavelength_m"] is None
        assert diagnostics["probe_coherent_field_group_id"] == "probe_660nm"
        assert diagnostics["excitation_incoherent_power_group_id"] is None
        assert (
            diagnostics["pod_wavelength_grouping_status"]
            == "single_probe_no_excitation_configured"
        )
        assert diagnostics["multi_wavelength_coherent_addition_policy"] == (
            "same_probe_wavelength_only"
        )
        assert diagnostics["pod_quantitative_route_status"] == (
            "blocked_missing_thermal_forward_model_or_calibration"
        )
        assert diagnostics["pod_amplitude_model_boundary"] == (
            "frequency_lane_surrogate_not_absolute_photothermal_amplitude"
        )
        assert diagnostics["pod_probe_reference_field_status"] == (
            "probe_E_ref_E_sca_use_current_optical_wavelength"
        )
        assert diagnostics["pod_quantitative_amplitude_available"] is False
        assert diagnostics["pod_quantitative_sign_available"] is False
        assert diagnostics["pod_roi_sensitivity_derivative_status"] == "unavailable"
        assert diagnostics["pod_signal_sign_source"] == "unavailable"
        assert diagnostics["pod_excitation_absorption_cross_section_status"] == (
            "not_available_no_excitation_wavelength"
        )
        assert diagnostics["pod_heat_source_status"] == (
            "not_available_missing_excitation_wavelength_or_power"
        )
        assert diagnostics["pod_heat_diffusion_status"] == "not_implemented"
        assert diagnostics["pod_solvent_dn_dT_status"] == (
            "not_configured_by_probe_wavelength"
        )
        assert diagnostics["pod_detector_responsivity_status"] == (
            "not_configured_by_probe_wavelength"
        )
        assert diagnostics["pod_thermal_validation_status"] == "not_validated"
        assert diagnostics["probe_wavelength_fields_add_coherently"] is True
        assert diagnostics[
            "excitation_wavelength_fields_never_add_to_probe_E_ref_E_sca"
        ] is True
        assert "thermal_pod_model_unavailable" in diagnostics[
            "pod_amplitude_quantitative_blocker_summary"
        ]
        assert "ROI_integrated_dIdtheta_missing" in diagnostics[
            "pod_amplitude_quantitative_blocker_summary"
        ]
        assert "thermal_heat_source_missing" in diagnostics[
            "pod_amplitude_quantitative_blocker_summary"
        ]

    def test_photothermal_pod_diagnostics_separate_probe_and_excitation_wavelengths(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            thermal_pod_model="thermal_diffusion",
            probe_wavelength_m=660e-9,
            excitation_wavelength_m=532e-9,
            probe_power_W=1.0e-3,
            excitation_power_W=5.0e-3,
            pod_roi_sensitivity_derivative_status="field_derivative",
            pod_signal_sign_source="ROI_integrated_dIdtheta",
            pod_thermal_spatial_distribution_status="coupled_optical_thermal",
            pod_roi_derivative_validity="validated",
        )
        diagnostics = build_photothermal_pod_diagnostics(BASELINE_OPTICAL, cfg)
        assert (
            diagnostics["thermal_pod_model_status"]
            == "thermal_diffusion_requested_but_not_implemented"
        )
        assert diagnostics["probe_wavelength_m"] == pytest.approx(660e-9)
        assert diagnostics["excitation_wavelength_m"] == pytest.approx(532e-9)
        assert diagnostics["probe_coherent_field_group_id"] == "probe_660nm"
        assert diagnostics["excitation_incoherent_power_group_id"] == "excitation_532nm"
        assert diagnostics["probe_excitation_wavelengths_separated"] is True
        assert diagnostics["pod_probe_excitation_wavelength_status"] == (
            "probe_and_excitation_wavelengths_separated"
        )
        assert diagnostics["pod_wavelength_grouping_status"] == (
            "probe_coherent_excitation_incoherent_separated"
        )
        assert diagnostics["pod_excitation_absorption_cross_section_status"] == (
            "not_computed_for_excitation_wavelength"
        )
        assert diagnostics["pod_heat_source_status"] == (
            "not_implemented_absorption_to_heat_source"
        )
        assert diagnostics["pod_quantitative_sign_available"] is True
        assert diagnostics["pod_quantitative_amplitude_available"] is False
        assert diagnostics["pod_amplitude_model_boundary"] == (
            "thermal_diffusion_route_requested_without_solver"
        )
        assert "heat_diffusion_solver_not_implemented" in diagnostics[
            "pod_amplitude_quantitative_blocker_summary"
        ]

    def test_interpolate_out_of_range(self):
        theta = np.array([0.1, 1.0, 2.0])
        values = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="outside grid"):
            interpolate_at_theta(theta, values, 3.0)

    def test_validate_config_passes(self):
        validate_simulation_config(DEFAULT_SIM_CFG, BASELINE_OPTICAL)

    def test_validate_config_too_short(self):
        cfg = SimulationConfig(0.001, 20000.0, 2e-4)
        with pytest.raises(ValueError, match="total_time"):
            validate_simulation_config(cfg, BASELINE_OPTICAL)

    def test_sample_position_in_bounds(self):
        rng = np.random.default_rng(42)
        channel = Channel(800e-9, 550e-9)
        for _ in range(100):
            x0, z0, _ = sample_initial_position(channel, rng)
            assert abs(x0) <= channel.width_m / 2
            assert abs(z0) <= channel.depth_m / 2

    def test_sample_position_accepts_low_variance_unit_sample(self):
        rng = np.random.default_rng(42)
        channel = Channel(800e-9, 550e-9)

        x0, z0, diag = sample_initial_position(
            channel,
            rng,
            unit_position_sample=(0.25, 0.75, 0.5),
        )

        assert x0 == pytest.approx(-channel.width_m / 4)
        assert z0 == pytest.approx(channel.depth_m / 4)
        assert diag["initial_position_unit_sample_supplied"] is True

    def test_block_initial_positions_match_scalar_uniform_rng_order(self):
        channel = Channel(800e-9, 550e-9)
        particle_radius = 50e-9
        sim_cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            initial_position_distribution_mode="uniform",
        )
        block_rng = np.random.default_rng(123)
        scalar_rng = np.random.default_rng(123)

        x_block, z_block, diag_block = _sample_initial_positions_block(
            channel,
            block_rng,
            particle_radius,
            sim_cfg,
            None,
            0,
            6,
        )
        scalar_results = [
            sample_initial_position(channel, scalar_rng, particle_radius, sim_cfg=sim_cfg)
            for _ in range(6)
        ]

        np.testing.assert_allclose(x_block, [item[0] for item in scalar_results])
        np.testing.assert_allclose(z_block, [item[1] for item in scalar_results])
        assert diag_block == [item[2] for item in scalar_results]
        assert block_rng.random() == pytest.approx(scalar_rng.random())

    def test_block_initial_positions_match_scalar_center_biased_units(self):
        channel = Channel(300e-9, 300e-9)
        particle_radius = 50e-9
        sim_cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            initial_position_distribution_mode="center_biased_surrogate",
            initial_position_center_bias_strength=1.5,
            initial_position_center_bias_min_confinement_ratio=0.05,
        )
        unit_samples = np.array(
            [
                [0.1, 0.2, 0.3],
                [0.25, 0.75, 0.5],
                [0.5, 0.5, 0.9],
                [0.9, 0.8, 0.1],
            ],
            dtype=float,
        )

        x_block, z_block, diag_block = _sample_initial_positions_block(
            channel,
            np.random.default_rng(1),
            particle_radius,
            sim_cfg,
            unit_samples,
            0,
            len(unit_samples),
        )
        scalar_results = [
            sample_initial_position(
                channel,
                np.random.default_rng(999),
                particle_radius,
                sim_cfg=sim_cfg,
                unit_position_sample=tuple(row),
            )
            for row in unit_samples
        ]

        np.testing.assert_allclose(x_block, [item[0] for item in scalar_results])
        np.testing.assert_allclose(z_block, [item[1] for item in scalar_results])
        assert diag_block == [item[2] for item in scalar_results]
        assert all(diag["initial_position_distribution_active"] for diag in diag_block)

    def test_block_initial_positions_flux_weighted_uses_scalar_fallback(self):
        channel = Channel(800e-9, 550e-9)
        particle_radius = 50e-9
        sim_cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            flow_profile_model="parabolic_rect",
            initial_position_distribution_mode="flux_weighted",
        )
        block_rng = np.random.default_rng(321)
        scalar_rng = np.random.default_rng(321)

        x_block, z_block, diag_block = _sample_initial_positions_block(
            channel,
            block_rng,
            particle_radius,
            sim_cfg,
            None,
            0,
            5,
        )
        scalar_results = [
            sample_initial_position(channel, scalar_rng, particle_radius, sim_cfg=sim_cfg)
            for _ in range(5)
        ]

        np.testing.assert_allclose(x_block, [item[0] for item in scalar_results])
        np.testing.assert_allclose(z_block, [item[1] for item in scalar_results])
        assert diag_block == [item[2] for item in scalar_results]
        assert block_rng.random() == pytest.approx(scalar_rng.random())

    def test_center_biased_initial_positions_pull_samples_toward_channel_center(self):
        channel = Channel(800e-9, 550e-9)
        particle_radius = 50e-9
        n = 4000
        uniform_cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            initial_position_distribution_mode="uniform",
        )
        biased_cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            initial_position_distribution_mode="center_biased_surrogate",
            initial_position_center_bias_strength=1.5,
            initial_position_center_bias_min_confinement_ratio=0.05,
        )
        rng_uniform = np.random.default_rng(0)
        rng_biased = np.random.default_rng(0)
        uniform_samples = np.array(
            [
                sample_initial_position(channel, rng_uniform, particle_radius, sim_cfg=uniform_cfg)[:2]
                for _ in range(n)
            ]
        )
        biased_results = [
            sample_initial_position(channel, rng_biased, particle_radius, sim_cfg=biased_cfg)
            for _ in range(n)
        ]
        biased_samples = np.array([item[:2] for item in biased_results])
        biased_diags = [item[2] for item in biased_results]
        half_w = channel.width_m / 2.0 - particle_radius
        half_h = channel.depth_m / 2.0 - particle_radius
        uniform_mean_abs_x = float(np.mean(np.abs(uniform_samples[:, 0]) / half_w))
        uniform_mean_abs_z = float(np.mean(np.abs(uniform_samples[:, 1]) / half_h))
        biased_mean_abs_x = float(np.mean(np.abs(biased_samples[:, 0]) / half_w))
        biased_mean_abs_z = float(np.mean(np.abs(biased_samples[:, 1]) / half_h))
        assert biased_mean_abs_x < uniform_mean_abs_x
        assert biased_mean_abs_z < uniform_mean_abs_z
        assert all(diag["initial_position_distribution_active"] for diag in biased_diags)
        assert all(diag["initial_position_center_bias_x_exponent"] > 1.0 for diag in biased_diags)
        assert all(diag["initial_position_center_bias_z_exponent"] > 1.0 for diag in biased_diags)

    def test_flux_weighted_initial_positions_follow_axial_flow_profile(self):
        channel = Channel(800e-9, 550e-9)
        particle_radius = 50e-9
        n = 3000
        uniform_cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            flow_profile_model="parabolic_rect",
            initial_position_distribution_mode="uniform",
        )
        flux_cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            flow_profile_model="parabolic_rect",
            initial_position_distribution_mode="flux_weighted",
        )
        rng_uniform = np.random.default_rng(123)
        rng_flux = np.random.default_rng(123)
        uniform_samples = np.array(
            [
                sample_initial_position(channel, rng_uniform, particle_radius, sim_cfg=uniform_cfg)[:2]
                for _ in range(n)
            ]
        )
        flux_results = [
            sample_initial_position(channel, rng_flux, particle_radius, sim_cfg=flux_cfg)
            for _ in range(n)
        ]
        flux_samples = np.array([item[:2] for item in flux_results])
        flux_diags = [item[2] for item in flux_results]
        half_w = channel.width_m / 2.0 - particle_radius
        half_h = channel.depth_m / 2.0 - particle_radius
        uniform_mean_abs_x = float(np.mean(np.abs(uniform_samples[:, 0]) / half_w))
        uniform_mean_abs_z = float(np.mean(np.abs(uniform_samples[:, 1]) / half_h))
        flux_mean_abs_x = float(np.mean(np.abs(flux_samples[:, 0]) / half_w))
        flux_mean_abs_z = float(np.mean(np.abs(flux_samples[:, 1]) / half_h))
        assert flux_mean_abs_x < uniform_mean_abs_x
        assert flux_mean_abs_z < uniform_mean_abs_z
        assert all(diag["initial_position_distribution_active"] for diag in flux_diags)
        assert all(
            diag["cross_section_event_bias_status"]
            == "flux_weighted_by_axial_transport_velocity"
            for diag in flux_diags
        )
        assert all(
            0.0 < diag["flux_weighted_sampling_acceptance_rate"] <= 1.0
            for diag in flux_diags
        )

    def test_flux_uniform_mixture_initial_positions_interpolate_event_prior(self):
        channel = Channel(800e-9, 550e-9)
        particle_radius = 50e-9
        n = 2500
        uniform_cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            flow_profile_model="parabolic_rect",
            initial_position_distribution_mode="uniform_accessible_area",
        )
        mixture_cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            flow_profile_model="parabolic_rect",
            initial_position_distribution_mode="flux_uniform_mixture_surrogate",
            initial_position_flux_weighted_mixture_fraction=0.5,
        )
        flux_cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            flow_profile_model="parabolic_rect",
            initial_position_distribution_mode="flux_weighted",
        )
        rng_uniform = np.random.default_rng(11)
        rng_mixture = np.random.default_rng(11)
        rng_flux = np.random.default_rng(11)
        uniform_samples = np.array(
            [
                sample_initial_position(channel, rng_uniform, particle_radius, sim_cfg=uniform_cfg)[:2]
                for _ in range(n)
            ]
        )
        mixture_results = [
            sample_initial_position(channel, rng_mixture, particle_radius, sim_cfg=mixture_cfg)
            for _ in range(n)
        ]
        flux_samples = np.array(
            [
                sample_initial_position(channel, rng_flux, particle_radius, sim_cfg=flux_cfg)[:2]
                for _ in range(n)
            ]
        )
        mixture_samples = np.array([item[:2] for item in mixture_results])
        mixture_diags = [item[2] for item in mixture_results]
        half_w = channel.width_m / 2.0 - particle_radius
        uniform_mean_abs_x = float(np.mean(np.abs(uniform_samples[:, 0]) / half_w))
        mixture_mean_abs_x = float(np.mean(np.abs(mixture_samples[:, 0]) / half_w))
        flux_mean_abs_x = float(np.mean(np.abs(flux_samples[:, 0]) / half_w))

        assert flux_mean_abs_x < mixture_mean_abs_x < uniform_mean_abs_x
        assert {diag["initial_position_mixture_component"] for diag in mixture_diags} == {
            "flux_weighted",
            "uniform_accessible_area",
        }

    def test_projection_freeze_classifies_matched_phase_aware_chain(self):
        freeze = classify_projection_freeze(
            scattering_projection_basis="parallel",
            illumination_projection_coupling_status="shared_basis_matched",
            reference_projection_coupling_status="shared_basis_matched",
            interference_projection_coupling_status="shared_basis_matched",
        )
        assert freeze["projection_freeze_agreement_status"] == "aligned"
        assert freeze["projection_default_frozen"] is True
        assert freeze["projection_default_freeze_status"] == "default_frozen_active"

    def test_delta_phi_gouy_geometry_validity_requires_large_channel_to_waist_ratio(self):
        validity = classify_delta_phi_gouy_geometry_validity(
            channel=Channel(800e-9, 550e-9),
            optical=BASELINE_OPTICAL,
            phase_model="relative_surrogate",
        )
        expected_waist = 0.61 * BASELINE_OPTICAL.wavelength_m / BASELINE_OPTICAL.illumination_NA
        assert validity["delta_phi_gouy_validity"] == "shared_beam_acceptable"
        assert validity["delta_phi_gouy_geometry_source"] == "objective_na_surrogate"
        assert validity["delta_phi_gouy_geometry_width_to_waist_ratio"] == pytest.approx(
            800e-9 / expected_waist
        )
        assert validity["delta_phi_gouy_geometry_depth_to_waist_ratio"] == pytest.approx(
            550e-9 / expected_waist
        )

    def test_observation_freeze_requires_all_default_paths_and_acceptable_gouy_geometry(self):
        ready = classify_observation_freeze(
            path_opd_freeze_status="default_frozen_active",
            interference_overlap_default_freeze_status="default_frozen_active",
            projection_default_freeze_status="default_frozen_active",
            delta_phi_gouy_validity="shared_beam_acceptable",
        )
        caution = classify_observation_freeze(
            path_opd_freeze_status="default_frozen_active",
            interference_overlap_default_freeze_status="warning_review_before_freeze",
            projection_default_freeze_status="default_frozen_active",
            delta_phi_gouy_validity="shared_beam_caution",
        )
        assert ready["observation_freeze_status"] == "default_ready_for_result_freeze"
        assert caution["observation_freeze_status"] == "caution_probe_before_result_freeze"

    def test_design_recommendation_distinguishes_default_caution_and_blocked_cases(self):
        default_case = classify_design_recommendation(
            engineering_gate_passed=True,
            observation_freeze_status="default_ready_for_result_freeze",
        )
        caution_case = classify_design_recommendation(
            engineering_gate_passed=True,
            observation_freeze_status="caution_probe_before_result_freeze",
        )
        blocked_case = classify_design_recommendation(
            engineering_gate_passed=False,
            observation_freeze_status="default_ready_for_result_freeze",
        )
        freeze_blocked_case = classify_design_recommendation(
            engineering_gate_passed=False,
            observation_freeze_status="review_required_before_result_freeze",
        )

        assert default_case["design_recommendation_status"] == "recommended_default"
        assert default_case["design_recommendation_label"] == "推荐（默认）"
        assert default_case["design_recommendation_rank"] == 4
        assert caution_case["design_recommendation_status"] == "recommended_with_caution"
        assert blocked_case["design_recommendation_status"] == "physics_ready_gate_blocked"
        assert freeze_blocked_case["design_recommendation_status"] == "not_recommended_freeze_blocked"

    def test_case_decision_summary_prioritizes_recommendation_gate_and_freeze(self):
        summary = build_case_decision_summary(
            design_recommendation_label="推荐（需复核）",
            design_recommendation_status="recommended_with_caution",
            design_recommendation_guidance="先复核 freeze 诊断。",
            engineering_gate_passed=True,
            engineering_gate_status_label="工程门槛通过",
            engineering_gate_primary_blocker_label="已通过",
            engineering_gate_blocker_summary="已通过 engineering gate",
            engineering_gate_guidance="当前 case 已过工程门槛。",
            observation_freeze_status="caution_probe_before_result_freeze",
            observation_freeze_guidance="建议先做 coarse probe。",
        )
        assert summary["decision_summary_tone"] == "warning"
        assert "freeze caution" in summary["decision_summary_headline"]
        assert "已通过 engineering gate" in summary["decision_summary_blocker_text"]
        assert "复核" in summary["decision_summary_next_step"]

    def test_engineering_gate_explanation_summarizes_primary_blocker(self):
        passed_case = classify_engineering_gate_explanation(
            engineering_gate_passed=True,
            engineering_gate_reason="PASS",
            engineering_gate_failed_count=0,
        )
        failed_case = classify_engineering_gate_explanation(
            engineering_gate_passed=False,
            engineering_gate_reason="stable_detection_rate<0.30 / phase_flip_fraction>0.40",
            engineering_gate_failed_count=2,
        )

        assert passed_case["engineering_gate_status_label"] == "工程门槛通过"
        assert passed_case["engineering_gate_primary_blocker"] == "pass"
        assert failed_case["engineering_gate_status_label"] == "工程门槛未通过"
        assert failed_case["engineering_gate_primary_blocker_label"] == "稳定检出率不足"
        assert "相位翻转占比过高" in failed_case["engineering_gate_blocker_summary"]

    def test_baseline_normalization_positive(self):
        result = compute_baseline_normalization(BASELINE_PARTICLE, WATER, BASELINE_OPTICAL, THETA_GRID)
        assert result["E_sca_ref"] > 0

    def test_resolve_collection_theta_fixed(self):
        cfg = SimulationConfig(0.2, 20000.0, 2e-4, collection_angle_model="fixed")
        theta = resolve_collection_theta_rad(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg)
        assert theta == pytest.approx(BASELINE_OPTICAL.collection_theta_rad)

    def test_resolve_collection_theta_channel_diffraction(self):
        optical = OpticalSystem(660e-9, 1.0, 300e-9, 700e-9, 300e-9, collection_theta_rad=np.pi / 4)
        cfg = SimulationConfig(0.2, 20000.0, 2e-4, collection_angle_model="channel_diffraction")
        theta_wide = resolve_collection_theta_rad(
            Channel(1200e-9, 550e-9), optical, cfg, medium_refractive_index=1.33
        )
        theta_narrow = resolve_collection_theta_rad(
            Channel(800e-9, 550e-9), optical, cfg, medium_refractive_index=1.33
        )
        assert 0 < theta_wide < theta_narrow < np.pi / 2

    def test_resolve_collection_theta_calibrated_lookup_stays_forward(self):
        optical = OpticalSystem(660e-9, 1.0, 300e-9, 700e-9, 300e-9, collection_theta_rad=np.pi / 4)
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            collection_angle_model="channel_diffraction",
            reference_model="calibrated_lookup",
            reference_calibration_path=__file__,
        )
        theta = resolve_collection_theta_rad(
            Channel(800e-9, 550e-9),
            optical,
            cfg,
            medium_refractive_index=1.33,
        )
        assert theta == pytest.approx(0.0)

    def test_detected_field_single_angle_recovers_legacy_amplitude(self):
        intrinsic = compute_intrinsic_scattering(BASELINE_PARTICLE, WATER, 660e-9, THETA_GRID)
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            collection_angle_model="fixed",
            collection_integration_mode="single_angle",
            scattering_projection_mode="intensity_proxy",
        )
        result = compute_detected_scattering_field(
            intrinsic,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
        )
        legacy = interpolate_at_theta(
            intrinsic["theta_grid_rad"],
            intrinsic["Esca_unit_amp"],
            BASELINE_OPTICAL.collection_theta_rad,
        )
        assert result["E_sca_detected_abs"] == pytest.approx(legacy)

    def test_detected_field_weighted_parallel_preserves_complex_phase(self):
        intrinsic = compute_intrinsic_scattering(BASELINE_PARTICLE, WATER, 660e-9, THETA_GRID)
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            collection_angle_model="channel_diffraction",
            collection_integration_mode="gaussian_weighted",
            collection_sigma_rad=np.deg2rad(10.0),
            scattering_projection_mode="parallel",
        )
        result = compute_detected_scattering_field(
            intrinsic,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
        )
        assert result["E_sca_detected_abs"] > 0
        assert np.isfinite(result["theta_effective_rad"])
        assert abs(result["E_sca_detected_complex"].imag) > 0
        assert result["sigma_effective_rad"] > 0
        assert np.isfinite(result["phi_projection_rad"])
        assert np.isfinite(result["phi_sca_material_rad"])
        assert np.isfinite(result["phi_sca_material_parallel_rad"])
        assert np.isfinite(result["phi_sca_material_perpendicular_rad"])

    def test_detected_field_pupil_slit_surrogate_is_finite(self):
        intrinsic = compute_intrinsic_scattering(BASELINE_PARTICLE, WATER, 660e-9, THETA_GRID)
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            collection_sigma_rad=np.deg2rad(10.0),
            collection_phi_sigma_rad=np.deg2rad(14.0),
            slit_phi_limit_rad=np.deg2rad(20.0),
            scattering_projection_mode="parallel",
        )
        result = compute_detected_scattering_field(
            intrinsic,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
        )
        assert result["E_sca_detected_abs"] > 0
        assert np.isfinite(result["theta_effective_rad"])

    def test_detected_field_pupil_slit_surrogate_narrower_slit_reduces_collection(self):
        intrinsic = compute_intrinsic_scattering(BASELINE_PARTICLE, WATER, 660e-9, THETA_GRID)
        cfg_wide = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            collection_sigma_rad=np.deg2rad(10.0),
            collection_phi_sigma_rad=np.deg2rad(14.0),
            slit_phi_limit_rad=np.deg2rad(20.0),
            scattering_projection_mode="parallel",
        )
        cfg_narrow = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            collection_sigma_rad=np.deg2rad(10.0),
            collection_phi_sigma_rad=np.deg2rad(6.0),
            slit_phi_limit_rad=np.deg2rad(8.0),
            scattering_projection_mode="parallel",
        )
        wide = compute_detected_scattering_field(intrinsic, BASELINE_CHANNEL, BASELINE_OPTICAL, cfg_wide)
        narrow = compute_detected_scattering_field(intrinsic, BASELINE_CHANNEL, BASELINE_OPTICAL, cfg_narrow)
        assert narrow["E_sca_detected_abs"] < wide["E_sca_detected_abs"]

    def test_detected_field_parallel_and_perpendicular_pupil_projections_differ(self):
        intrinsic = compute_intrinsic_scattering(BASELINE_PARTICLE, WATER, 660e-9, THETA_GRID)
        cfg_parallel = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            collection_sigma_rad=np.deg2rad(10.0),
            collection_phi_sigma_rad=np.deg2rad(14.0),
            slit_phi_limit_rad=np.deg2rad(20.0),
            scattering_projection_mode="parallel",
        )
        cfg_perp = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            collection_sigma_rad=np.deg2rad(10.0),
            collection_phi_sigma_rad=np.deg2rad(14.0),
            slit_phi_limit_rad=np.deg2rad(20.0),
            scattering_projection_mode="perpendicular",
        )
        parallel = compute_detected_scattering_field(intrinsic, BASELINE_CHANNEL, BASELINE_OPTICAL, cfg_parallel)
        perpendicular = compute_detected_scattering_field(intrinsic, BASELINE_CHANNEL, BASELINE_OPTICAL, cfg_perp)
        assert parallel["E_sca_detected_complex"] != pytest.approx(perpendicular["E_sca_detected_complex"])

    def test_baseline_normalization_uses_same_collection_operator(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            collection_sigma_rad=np.deg2rad(10.0),
            collection_phi_sigma_rad=np.deg2rad(14.0),
            slit_phi_limit_rad=np.deg2rad(20.0),
            scattering_projection_mode="parallel",
        )
        intrinsic = compute_intrinsic_scattering(BASELINE_PARTICLE, WATER, 660e-9, THETA_GRID)
        runtime = compute_detected_scattering_field(
            intrinsic,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
        )
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            THETA_GRID,
            channel=BASELINE_CHANNEL,
            sim_cfg=cfg,
        )
        assert baseline["E_sca_ref"] == pytest.approx(runtime["E_sca_detected_abs"])
        assert baseline["E_sca_ref_complex"] == pytest.approx(runtime["E_sca_detected_complex"])
        assert baseline["operator_signature"] == runtime["operator_signature"]

    def test_collection_operator_exports_measure_and_jacobian_contract(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            collection_sigma_rad=np.deg2rad(10.0),
            collection_phi_sigma_rad=np.deg2rad(14.0),
            slit_phi_limit_rad=np.deg2rad(20.0),
            scattering_projection_mode="parallel",
        )
        operator = build_collection_operator(
            THETA_GRID,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            medium_refractive_index=WATER.refractive_index,
        )
        assert operator["operator_route"] == "pupil_slit_surrogate"
        assert operator["operator_normalization"] == "unit_normalized_weights_with_throughput_surrogate"
        assert operator["field_coordinate_measure"] == "theta_phi_surrogate"
        assert operator["bfp_to_angle_jacobian_applied"] is False
        assert operator["field_measure_status"] == "surrogate_theta_phi_weights_not_solid_angle"
        assert operator["detector_mask_units"] == "radian_surrogate"
        assert operator["collection_operator_calibration_status"] == (
            "not_configured_surrogate"
        )
        assert operator["collection_operator_coverage_status"] == "not_applicable"
        assert operator["bfp_roi_mask_status"] == (
            "not_configured_current_radian_surrogate_mask"
        )
        assert operator["bfp_pixel_to_angle_status"] == (
            "not_calibrated_pixel_to_angle_mapping_missing"
        )

    def test_required_calibration_csv_templates_are_present(self):
        template_names = (
            "collection_operator_template.csv",
            "standard_particle_template.csv",
            "reference_blank_channel_template.csv",
            "blank_false_positive_template.csv",
        )
        for template_name in template_names:
            table_path = REPO_ROOT / "calibration" / template_name
            assert table_path.exists(), f"Missing calibration template: {template_name}"
            assert (
                "synthetic_fixture_not_experimental"
                in table_path.read_text(encoding="utf-8")
            )

    def test_calibration_templates_validate_but_remain_synthetic_fixtures(self):
        table_path = REPO_ROOT / "calibration" / "collection_operator_template.csv"
        validation = validate_calibration_table(str(table_path), "collection_operator")
        contract = calibration_contract_summary(
            table_path=str(table_path),
            kind="collection_operator",
        )
        assert validation["validation_status"] == "valid_minimal_schema"
        assert contract["calibration_data_role"] == "synthetic_fixture_not_experimental"
        assert contract["synthetic_fixture_active"] is True

    def test_bfp_roi_mask_template_is_valid_plumbing_not_calibration(self):
        mask_path = REPO_ROOT / "calibration" / "bfp_roi_mask_template.json"
        contract = build_bfp_roi_mask_contract(
            bfp_roi_mask_path=str(mask_path),
        )
        assert contract["bfp_roi_mask_schema"] == "bfp_roi_mask_v2"
        assert contract["bfp_roi_mask_path_configured"] is True
        assert contract["bfp_roi_mask_synthetic_fixture_active"] is True
        assert contract["bfp_roi_mask_calibrated"] is False
        assert contract["bfp_roi_mask_source"] == "synthetic_fixture_contract_only"
        assert contract["bfp_roi_mask_manifest_validation_status"] == (
            "valid_minimal_manifest"
        )
        assert contract["bfp_roi_mask_gate_passed"] is False

    def test_bfp_roi_mask_measured_fixture_can_expose_calibrated_mask_source(
        self,
        tmp_path,
    ):
        mask_path = tmp_path / "bfp_mask.csv"
        mask_path.write_text(
            "pixel_x,pixel_y,theta_rad,phi_rad,mask_weight,solid_angle_weight\n"
            "10,20,0.5,0.1,1.0,0.002\n",
            encoding="utf-8",
        )
        (tmp_path / "bfp_mask.csv.manifest.json").write_text(
            "{"
            '"calibration_kind":"bfp_roi_mask",'
            '"calibration_data_role":"experimental_measurement",'
            '"units":{'
            '"pixel_x":"pixel","pixel_y":"pixel","theta_rad":"rad",'
            '"phi_rad":"rad","mask_weight":"dimensionless",'
            '"solid_angle_weight":"sr"'
            "}"
            "}",
            encoding="utf-8",
        )
        contract = build_bfp_roi_mask_contract(
            bfp_roi_mask_path=str(mask_path),
            bfp_to_angle_jacobian_applied=True,
        )
        assert contract["bfp_roi_mask_calibrated"] is True
        assert contract["bfp_roi_mask_source"] == "calibrated_mask"
        assert contract["bfp_roi_mask_status"] == "calibrated_mask_contract_loaded"
        assert contract["bfp_roi_mask_data_role"] == "experimental_measurement"
        assert contract["bfp_roi_mask_table_validation_status"] == (
            "valid_minimal_schema"
        )
        assert contract["bfp_roi_mask_gate_passed"] is True
        assert contract["bfp_pixel_to_angle_status"] == (
            "jacobian_flag_set_with_calibrated_mask"
        )

    def test_bfp_roi_mask_wrong_manifest_kind_cannot_expose_calibrated_mask_source(
        self,
        tmp_path,
    ):
        mask_path = tmp_path / "bfp_mask.csv"
        mask_path.write_text(
            "pixel_x,pixel_y,theta_rad,phi_rad,mask_weight,solid_angle_weight\n"
            "10,20,0.5,0.1,1.0,0.002\n",
            encoding="utf-8",
        )
        (tmp_path / "bfp_mask.csv.manifest.json").write_text(
            "{"
            '"calibration_kind":"standard_particle",'
            '"calibration_data_role":"experimental_measurement",'
            '"units":{'
            '"pixel_x":"pixel","pixel_y":"pixel","theta_rad":"rad",'
            '"phi_rad":"rad","mask_weight":"dimensionless",'
            '"solid_angle_weight":"sr"'
            "}"
            "}",
            encoding="utf-8",
        )
        contract = build_bfp_roi_mask_contract(
            bfp_roi_mask_path=str(mask_path),
            bfp_to_angle_jacobian_applied=True,
        )
        assert contract["bfp_roi_mask_calibrated"] is False
        assert contract["bfp_roi_mask_source"] == "configured_mask_contract_not_measured"
        assert contract["bfp_roi_mask_manifest_validation_status"] == (
            "manifest_kind_mismatch"
        )
        assert contract["bfp_roi_mask_gate_passed"] is False

    def test_calibration_plan_advisor_maps_claim_blockers_to_experiments(self):
        plan = build_calibration_plan_advisor(
            {
                "primary_blocker_summary": (
                    "cross_wavelength_claim_gate_not_passed / "
                    "detector_operator_gate_not_passed / "
                    "optical_exposure_safety_gate_not_passed"
                ),
                "laser_choice_claim_blocker": (
                    "probe_power_by_wavelength_W_or_detector_responsivity_by_wavelength_"
                    "or_filter_transmission_by_wavelength_or_reference_calibration_by_wavelength"
                ),
                "objective_claim_blocker_summary": "working_distance_not_measured",
                "optical_exposure_safety_blocker_summary": "probe_power_missing",
            }
        )

        for field in CALIBRATION_PLAN_ADVISOR_FIELDS:
            assert field in plan
        assert plan["calibration_plan_status"] == "experiments_recommended"
        assert plan["calibration_plan_calibrated_claim_unlocked"] is False
        assert "multi_wavelength_power_responsivity_filter_reference_calibration" in plan[
            "required_calibration_experiments"
        ]
        assert "slit_scan_or_pinhole_roi_mapping" in plan[
            "required_calibration_experiments"
        ]
        assert "probe_power_and_beam_waist_exposure_calibration" in plan[
            "required_calibration_experiments"
        ]

    def test_calibration_plan_advisor_deduplicates_standard_blank_and_flow_steps(self):
        plan = build_calibration_plan_advisor(
            {
                "output_claim_blocker_summary": (
                    "missing_K_sca_standard_calibration / "
                    "missing_standard_particle_uncertainty_budget / "
                    "threshold_from_blank_trace_false"
                ),
                "threshold_calibration_status": "gaussian_iid_surrogate_not_empirical_blank",
                "count_prediction_status": "missing_flow_velocity_calibration",
                "fluidic_practicality_status": "fixed_velocity_not_pressure_calibrated",
            }
        )

        required = plan["required_calibration_experiments"]
        assert required.count("Au20_Au30_Au40_standard_particle_trace_panel") == 1
        assert required.count("blank_buffer_trace_false_positive_bootstrap") == 1
        assert required.count("flow_velocity_and_pressure_drop_calibration") == 1
        assert plan["calibration_plan_priority_order"][0] == (
            "blank_channel_bfp_reference_image_by_W_H_lambda"
        )

    def test_calibration_plan_advisor_empty_blockers_remain_guidance_only(self):
        plan = build_calibration_plan_advisor({"primary_blocker_summary": "none"})

        assert plan["calibration_plan_status"] == "no_blocker_specific_experiments"
        assert plan["required_calibration_experiments"] == []
        assert plan["calibration_plan_calibrated_claim_unlocked"] is False
        assert plan["calibration_plan_claim_level"] == (
            "next_step_guidance_only_does_not_unlock_calibration"
        )

    def test_calibration_advisors_ignore_large_array_payloads(self):
        diagnostics = {
            "primary_blocker_summary": "detector_operator_gate_not_passed",
            "reference_angular_field_status": np.ones(128),
            "large_nested_status": {"status": "missing_standard_particle"},
        }

        plan = build_calibration_plan_advisor(diagnostics)
        advisor = build_experimental_design_advisor(diagnostics)

        assert plan["required_calibration_experiments"] == [
            "slit_scan_or_pinhole_roi_mapping"
        ]
        assert advisor["next_experiment_priority"] == "slit_scan_or_pinhole_roi_mapping"

    def test_experimental_design_advisor_prioritizes_blockers_and_voi(self):
        advisor = build_experimental_design_advisor(
            {
                "primary_blocker_summary": (
                    "detector_operator_gate_not_passed / "
                    "missing_standard_particle_uncertainty_budget"
                ),
                "position_sensitivity_score": 0.82,
                "route_disagreement_flag": True,
                "calibrated_quantitative_unlocked": False,
                "bayesian_posterior_available": False,
            }
        )

        for field in EXPERIMENTAL_DESIGN_ADVISOR_FIELDS:
            assert field in advisor
        assert advisor["experimental_design_advisor_status"] == (
            "next_experiment_recommended"
        )
        assert advisor["experimental_design_advisor_claim_level"] == (
            "next_experiment_guidance_only_does_not_unlock_claims"
        )
        assert advisor["next_experiment_priority"] == "slit_scan_or_pinhole_roi_mapping"
        assert advisor["next_experiment_priority_bucket"] == "high"
        assert advisor["next_experiment_priority_reason"] == (
            "detector_operator_or_bfp_mapping_missing"
        )
        assert advisor["blocker_pressure_score"] == pytest.approx(0.4)
        assert advisor["sensitivity_pressure_score"] == pytest.approx(0.82)
        assert advisor["model_disagreement_pressure_score"] == pytest.approx(1.0)
        assert advisor["calibration_gap_pressure_score"] == pytest.approx(0.8)
        assert advisor["value_of_information_score"] == pytest.approx(0.705)
        assert advisor["experimental_design_advisor_gate_passed"] is False

    def test_experimental_design_advisor_falls_back_to_model_disagreement(self):
        advisor = build_experimental_design_advisor(
            {
                "route_disagreement_flag": True,
                "calibrated_quantitative_unlocked": True,
                "bayesian_posterior_available": True,
            }
        )

        assert advisor["next_experiment_priority"] == (
            "model_disagreement_resolution_review"
        )
        assert advisor["next_experiment_priority_reason"] == (
            "model_disagreement_pressure"
        )
        assert advisor["next_experiment_priority_order"] == []
        assert advisor["value_of_information_score"] == pytest.approx(0.2)
        assert advisor["experimental_design_advisor_gate_passed"] is False

    def test_experimental_design_advisor_empty_input_remains_guidance_only(self):
        advisor = build_experimental_design_advisor(
            {
                "primary_blocker_summary": "none",
                "calibrated_quantitative_unlocked": True,
                "bayesian_posterior_available": True,
            }
        )

        assert advisor["experimental_design_advisor_status"] == (
            "no_high_value_experiment_identified"
        )
        assert advisor["next_experiment_priority"] is None
        assert advisor["next_experiment_priority_bucket"] == "none"
        assert advisor["value_of_information_score"] == pytest.approx(0.0)
        assert advisor["experimental_design_advisor_gate_passed"] is False

    def test_collection_operator_template_is_not_applied_as_calibration(self):
        table_path = REPO_ROOT / "calibration" / "collection_operator_template.csv"
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            collection_operator_calibration_path=str(table_path),
            collection_operator_id="template_operator",
            absolute_throughput_route="calibrated_operator_table",
        )
        operator = build_collection_operator(
            THETA_GRID,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            medium_refractive_index=WATER.refractive_index,
        )
        assert operator["collection_operator_calibration_status"] == (
            "synthetic_operator_fixture_selected_not_applied"
        )
        assert operator["collection_operator_synthetic_fixture_active"] is True
        assert operator["operator_route"] == "pupil_slit_surrogate"
        assert operator["collection_operator_calibrated_geometry"] is False
        assert operator["absolute_throughput_calibrated"] is False

    def test_collection_operator_uses_calibrated_operator_table(self, tmp_path):
        table_path = tmp_path / "collection_operator.csv"
        table_path.write_text(
            "\n".join(
                [
                    "operator_id,width_nm,depth_nm,wavelength_nm,theta_center_rad,"
                    "theta_sigma_rad,phi_sigma_rad,slit_phi_limit_rad,throughput_scale",
                    "opA,800,550,660,0.11,0.04,0.18,0.22,0.37",
                ]
            ),
            encoding="utf-8",
        )
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            collection_operator_calibration_path=str(table_path),
            collection_operator_id="opA",
            absolute_throughput_route="calibrated_operator_table",
        )
        operator = build_collection_operator(
            THETA_GRID,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            medium_refractive_index=WATER.refractive_index,
        )
        assert operator["operator_route"] == "calibrated_operator_table"
        assert (
            operator["operator_normalization"]
            == "absolute_throughput_calibrated_operator_table"
        )
        assert operator["collection_operator_calibration_status"] == (
            "calibrated_operator_table_selected"
        )
        assert operator["collection_operator_coverage_status"] == "covered_exact"
        assert operator["collection_operator_id"] == "opA"
        assert operator["collection_operator_calibrated_geometry"] is True
        assert operator["absolute_throughput_calibrated"] is True
        assert operator["theta_center_rad"] == pytest.approx(0.11)
        assert operator["sigma_effective_rad"] == pytest.approx(0.04)
        assert np.max(np.abs(operator["phi_grid_rad"])) == pytest.approx(0.22)
        assert operator["throughput_scale"] == pytest.approx(0.37)
        assert "operator_route=calibrated_operator_table" in operator[
            "operator_signature"
        ]

    def test_collection_operator_marks_nearest_row_extrapolation(self, tmp_path):
        table_path = tmp_path / "collection_operator.csv"
        table_path.write_text(
            "\n".join(
                [
                    "operator_id,width_nm,depth_nm,wavelength_nm,theta_center_rad",
                    "opA,400,250,488,0.09",
                ]
            ),
            encoding="utf-8",
        )
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            collection_operator_calibration_path=str(table_path),
        )
        operator = build_collection_operator(
            THETA_GRID,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            medium_refractive_index=WATER.refractive_index,
        )
        assert operator["operator_route"] == "calibrated_operator_table"
        assert operator["collection_operator_coverage_status"] == (
            "extrapolated_nearest_row"
        )
        assert operator["absolute_throughput_calibrated"] is False

    def test_complex_field_convention_diagnostics_lock_scalar_basis(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            scattering_projection_mode="parallel",
        )
        diagnostics = build_complex_field_convention_diagnostics(
            cfg,
            optical=BASELINE_OPTICAL,
        )
        assert diagnostics["complex_time_harmonic_convention"] == "exp_minus_i_omega_t"
        assert diagnostics["interference_cross_term_convention"] == "2*Re(E_ref*conj(E_sca))"
        assert diagnostics["mie_s1_s2_lab_basis_mapping"] == "parallel->S2,perpendicular->S1"
        assert diagnostics["active_mie_basis_component"] == "S2_complex"
        assert diagnostics["S1S2_to_lab_basis_rotation_applied"] is False
        assert diagnostics["reference_jones_field_defined"] is False
        assert diagnostics["detector_analyzer_jones_matrix_defined"] is False
        assert diagnostics["high_NA_collection_warning"] is True
        assert diagnostics["vector_validity_status"] == "scalar_high_NA_caution"
        assert diagnostics["incident_field_model_for_mie"] == "local_plane_wave"
        assert (
            diagnostics["local_plane_wave_validity"]
            == "unknown_missing_optical_or_intrinsic_payload"
        )
        assert (
            diagnostics["absolute_polarity_claim"]
            == "not_available_without_measured_global_phase_offset"
        )

    def test_mie_incident_field_validity_flags_focused_beam_gradient_limits(self):
        intrinsic = compute_intrinsic_scattering(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL.wavelength_m,
            THETA_GRID,
        )
        diagnostics = build_mie_incident_field_validity_diagnostics(
            optical=BASELINE_OPTICAL,
            intrinsic=intrinsic,
        )
        assert diagnostics["incident_field_model_for_mie"] == "local_plane_wave"
        assert diagnostics["local_plane_wave_validity"] == "valid_for_ranking"
        assert diagnostics["mie_radius_to_beam_waist_ratio"] == pytest.approx(
            BASELINE_PARTICLE.radius_m
            / BASELINE_OPTICAL.resolve_illumination_geometry()[
                "illumination_beam_waist_x_m"
            ]
        )
        assert diagnostics["mie_incident_field_GLMT_required"] is False
        assert diagnostics["mie_incident_field_fullwave_required"] is False
        assert diagnostics["mie_incident_field_blocker_summary"] == "none"

        focused_optical = replace(
            BASELINE_OPTICAL,
            illumination_NA=1.2,
            illumination_beam_waist_x_m=60e-9,
            illumination_beam_waist_y_m=60e-9,
            illumination_beam_waist_z_m=60e-9,
        )
        focused = build_mie_incident_field_validity_diagnostics(
            optical=focused_optical,
            intrinsic=intrinsic,
        )
        assert focused["incident_field_model_for_mie"] == "fullwave_required"
        assert focused["local_plane_wave_validity"] == "fullwave_required"
        assert focused["mie_incident_field_GLMT_required"] is True
        assert focused["mie_incident_field_fullwave_required"] is True
        assert "GLMT_not_implemented" in focused["mie_incident_field_blocker_summary"]
        assert "fullwave_incident_field_not_implemented" in focused[
            "mie_incident_field_blocker_summary"
        ]

    def test_calibration_state_diagnostics_keep_baseline_normalization_relative(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
        )
        reference = {
            "reference_claim_level": "engineering_ranking",
            "reference_calibration_amplitude_status": "not_calibrated",
            "reference_phase_absolute_claim": "not_measured_absolute_phase",
        }
        diagnostics = build_calibration_state_diagnostics(
            cfg,
            reference=reference,
            E_sca_ref=0.25,
        )
        assert diagnostics["scattering_normalization_route"] == "baseline_particle_relative"
        assert diagnostics["baseline_particle_absolute_scale_restored"] is False
        assert diagnostics["baseline_normalized_E_sca_allowed_in_photon_unit_route"] is False
        assert diagnostics["K_sca_calibration_status"] == "not_calibrated"
        assert diagnostics["standard_particle_calibration_path_configured"] is False
        assert diagnostics["standard_particle_calibration_coverage_status"] == (
            "not_applicable"
        )
        assert diagnostics["global_phase_offset_calibration_status"] == (
            "not_available_no_standard_particle_phase_offset"
        )
        assert (
            diagnostics["mie_to_power_chain_status"]
            == "not_implemented_dCsca_dOmega_not_converted_to_detector_units"
        )
        assert (
            diagnostics["scattered_power_conversion_status"]
            == "not_applied_no_incident_power_density_or_detector_etendue"
        )
        assert diagnostics["detector_field_units"] == "arbitrary_relative_field_units"
        assert diagnostics["power_chain_absolute_units_available"] is False
        assert (
            diagnostics["K_sca_power_chain_role"]
            == "not_available_cannot_replace_mie_to_power_chain"
        )
        assert "dCsca_dOmega_not_converted_to_dP_sca_dOmega" in diagnostics[
            "mie_to_power_chain_blocker_summary"
        ]
        assert (
            diagnostics["K_sca_uncertainty_status"]
            == "not_propagated_no_standard_particle_uncertainty_budget"
        )
        assert diagnostics["K_sca_uncertainty_propagated_to_outputs"] is False
        assert (
            diagnostics["standard_particle_uncertainty_budget_status"]
            == "missing_standard_particle_uncertainty_budget"
        )
        assert diagnostics["standard_particle_size_distribution_status"] == "not_provided"
        assert (
            diagnostics["standard_particle_material_dataset_uncertainty_status"]
            == "not_uncertainty_quantified"
        )
        assert "standard_particle_size_distribution" in diagnostics[
            "K_sca_uncertainty_required_inputs"
        ]
        assert "K_sca_uncertainty_not_propagated" in diagnostics[
            "K_sca_uncertainty_blocker_summary"
        ]
        assert diagnostics["scattering_calibration_level"] == "relative_baseline_particle_normalized"
        assert diagnostics["calibration_design_rank"] == "none"
        assert diagnostics["calibration_standard_count"] == 0
        assert diagnostics["calibration_wavelength_count"] == 0
        assert diagnostics["calibration_geometry_count"] == 0
        assert (
            diagnostics["calibration_held_out_validation_status"]
            == "not_available_no_standard_particle_design"
        )
        assert diagnostics["calibration_held_out_error"] is None
        assert "no_held_out_validation" in diagnostics[
            "calibration_identifiability_blocker_summary"
        ]
        assert (
            diagnostics["calibration_fit_parameter_coupling_status"]
            == "A_ref_K_sca_phase_throughput_detector_gain_coupled"
        )
        assert diagnostics["detector_calibration_level"] == "surrogate_not_detector_unit"
        assert diagnostics["readout_calibration_level"] == "lockin_surrogate_not_physical_electronics"
        assert diagnostics["count_calibration_level"] == "conditional_event_detection_not_count_rate"
        assert diagnostics["calibrated_quantitative_unlocked"] is False
        assert diagnostics["output_claim_level"] == "engineering_ranking"
        assert diagnostics["baseline_normalized_absolute_route_blocker_active"] is True
        assert diagnostics["detector_unit_claim_allowed"] is False
        assert diagnostics["photon_unit_claim_allowed"] is False
        assert diagnostics["absolute_route_claim_blocker"] == (
            "baseline_normalized_E_sca_cannot_unlock_detector_or_photon_units"
        )
        bayes = build_bayesian_calibration_scaffold(diagnostics, cfg)
        assert set(BAYESIAN_CALIBRATION_DIAGNOSTIC_FIELDS).issubset(bayes)
        assert bayes["bayesian_calibration_status"] == (
            "scaffold_only_no_real_standard_data"
        )
        assert bayes["bayesian_posterior_available"] is False
        assert bayes["posterior_predictive_design_score_p10"] is None
        assert bayes["bayesian_calibration_claim_level"] == (
            "scaffold_only_no_posterior_claim"
        )
        assert "real_standard_particle_data_missing" in bayes[
            "bayesian_calibration_blocker_summary"
        ]

    def test_standard_particle_calibration_table_records_k_sca_without_unlocking_power_chain(
        self,
        tmp_path,
    ):
        table_path = tmp_path / "standard_particles.csv"
        table_path.write_text(
            "\n".join(
                [
                    "calibration_id,wavelength_nm,operator_id,K_sca,"
                    "global_phase_offset_rad",
                    "stdA,660,opA,2.5,0.31",
                ]
            ),
            encoding="utf-8",
        )
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            standard_particle_calibration_path=str(table_path),
            standard_particle_calibration_id="stdA",
        )
        reference = {
            "reference_claim_level": "engineering_ranking",
            "reference_calibration_amplitude_status": "not_calibrated",
            "reference_phase_absolute_claim": "not_measured_absolute_phase",
        }
        diagnostics = build_calibration_state_diagnostics(
            cfg,
            reference=reference,
            optical=BASELINE_OPTICAL,
            collection_operator={"collection_operator_id": "opA"},
            E_sca_ref=0.25,
        )

        assert diagnostics["K_sca_calibration_status"] == (
            "standard_particle_table_available"
        )
        assert diagnostics["K_sca_value"] == pytest.approx(2.5)
        assert diagnostics["K_sca_role"] == (
            "lumped_residual_scale_available_not_mie_to_power_chain"
        )
        assert diagnostics["standard_particle_calibration_coverage_status"] == (
            "covered_exact"
        )
        assert diagnostics["global_phase_offset_rad"] == pytest.approx(0.31)
        assert diagnostics["global_phase_offset_calibration_status"] == (
            "standard_particle_table_phase_offset_available"
        )
        assert "missing_K_sca_standard_calibration" not in diagnostics[
            "output_claim_blocker_summary"
        ]
        assert diagnostics["power_chain_absolute_units_available"] is False
        assert diagnostics["calibrated_quantitative_unlocked"] is False
        bayes = build_bayesian_calibration_scaffold(diagnostics, cfg)
        assert bayes["bayesian_calibration_status"] == (
            "real_standard_data_available_sampler_not_implemented"
        )
        assert bayes["bayesian_posterior_available"] is False
        assert bayes["bayesian_posterior_sample_count"] == 0
        assert "posterior_sampler_not_implemented" in bayes[
            "bayesian_calibration_blocker_summary"
        ]
        assert "real_standard_particle_data_missing" not in bayes[
            "bayesian_calibration_blocker_summary"
        ]
        assert (
            diagnostics["K_sca_power_chain_role"]
            == "available_as_lumped_residual_cannot_replace_mie_to_power_chain"
        )
        assert "K_sca_available_only_as_lumped_residual" in diagnostics[
            "mie_to_power_chain_blocker_summary"
        ]
        assert diagnostics["detector_unit_chain_status"] == (
            "blocked_missing_mie_to_power_and_detector_gain"
        )

    def test_standard_particle_template_does_not_unlock_k_sca(self):
        table_path = REPO_ROOT / "calibration" / "standard_particle_template.csv"
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            standard_particle_calibration_path=str(table_path),
            standard_particle_calibration_id="template_standard",
        )
        diagnostics = build_calibration_state_diagnostics(
            cfg,
            reference={
                "reference_claim_level": "engineering_ranking",
                "reference_calibration_amplitude_status": "not_calibrated",
                "reference_phase_absolute_claim": "not_measured_absolute_phase",
            },
            optical=BASELINE_OPTICAL,
            collection_operator={"collection_operator_id": "template_operator"},
            E_sca_ref=0.25,
        )
        assert diagnostics["K_sca_calibration_status"] == (
            "synthetic_standard_particle_fixture_not_experimental"
        )
        assert diagnostics["K_sca_value"] is None
        assert diagnostics["standard_particle_synthetic_fixture_active"] is True
        assert "synthetic_calibration_fixture_not_experimental" in diagnostics[
            "output_claim_blocker_summary"
        ]
        assert diagnostics["calibration_synthetic_fixture_active"] is True

    def test_interference_overlap_diagnostics_identity_for_single_angle_scalar_fields(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            collection_integration_mode="single_angle",
            collection_angle_model="fixed",
        )
        theta_grid = np.array([0.1, 0.2, 0.3], dtype=float)
        operator = {
            "theta_center_rad": 0.2,
            "theta_weights": np.array([0.0, 1.0, 0.0], dtype=float),
            "throughput_scale": 1.0,
        }
        ref_field = np.array([1.0 + 0.0j, 2.0 + 0.5j, 1.5 + 0.2j], dtype=complex)
        sca_field = np.array([0.2 - 0.1j, 0.4 + 0.3j, 0.1 + 0.0j], dtype=complex)
        diag = build_interference_overlap_diagnostics(
            theta_grid,
            ref_field,
            sca_field,
            operator,
            cfg,
        )
        expected = ref_field[1] * np.conj(sca_field[1])
        assert diag["interference_cross_term_model_default"] == "joint_overlap_integrated"
        assert diag["interference_cross_term_joint_available"] is True
        assert diag["interference_overlap_status"] == "aligned"
        assert diag["interference_collapsed_product_complex"] == pytest.approx(expected)
        assert diag["interference_joint_overlap_complex"] == pytest.approx(expected)
        assert diag["interference_overlap_factor_complex"] == pytest.approx(1.0 + 0.0j)
        assert diag["interference_overlap_factor_abs"] == pytest.approx(1.0)
        assert diag["interference_overlap_factor_phase_rad"] == pytest.approx(0.0)


class TestReferenceField:
    def _write_reference_calibration(self) -> str:
        rows = """width_nm,depth_nm,wavelength_nm,g_ref,A_ref,phi_ref_rad
800,550,488,0.95,,0.00
800,550,660,1.10,,0.05
1200,550,488,1.15,,0.03
1200,550,660,1.28,,0.07
800,900,488,1.05,,0.01
800,900,660,1.20,,0.06
1200,900,488,1.22,,0.04
1200,900,660,1.38,,0.08
"""
        tmp = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
        tmp.write(rows)
        tmp.close()
        return tmp.name

    def test_constant_mode(self):
        cfg = SimulationConfig(0.2, 20000.0, 2e-4, rho=10.0, reference_model="constant")
        ref = compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg)
        assert ref["A_ref"] == 10.0
        assert abs(ref["E_ref_complex"]) == pytest.approx(10.0)
        assert ref["phi_ref_rad"] == 0.0

    def test_paper_aligned_phase_filter_disables_depth_aperture_term(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="paper_aligned_phase_filter",
        )
        ref = compute_reference_field(Channel(800e-9, 1400e-9), BASELINE_OPTICAL, cfg)
        assert ref["reference_model_precision_tier"] == "paper_aligned_comparison_surrogate"
        assert ref["reference_model_role"] == "tsuyama_depth_semantics_audit_path"
        assert ref["reference_phase_structure_mode"] == "paper_aligned_1d_phase_filter_width_only"
        assert ref["reference_depth_aperture_term_active"] is False
        assert ref["reference_width_saturation_status"] == "disabled_paper_aligned_phase_filter"
        assert ref["reference_solver_route"] == "tsuyama_phase_filter_1d"
        assert ref["reference_solver_status"] == "diagnostic_complex_bfp_field_available"
        assert ref["reference_solver_active_field_source"] == "paper_aligned_angular_surrogate"
        assert ref["paper_aligned_reference_claim"] == "diagnostic_only"
        assert (
            ref["reference_solver_detector_bridge_status"]
            == "diagnostic_only_uses_paper_aligned_angular_surrogate"
        )
        assert ref["phase_delay_over_2_role"] == "amplitude_envelope_surrogate_only"
        assert ref["polarity_claim_from_phase_delay_over_2_allowed"] is False
        assert ref["reference_absolute_polarity_claim"] == (
            "blocked_active_reference_phase_surrogate"
        )
        assert ref["phi_ref_model_source"] == (
            "thin_phase_complex_factor_exp_i_theta_minus_one_diagnostic"
        )
        np.testing.assert_allclose(
            ref["tsuyama_E_diffraction_BFP"],
            ref["tsuyama_E_total_channel_BFP"] - ref["tsuyama_E_no_channel_BFP"],
            rtol=1e-10,
            atol=1e-12,
        )
        assert (
            ref["tsuyama_phase_filter_numerical_invariants"]["power_normalization_check"]
            == "parseval_pass"
        )
        assert ref["theta_signed_rad"] < 0.0
        assert ref["phase_filter_validity"] in {
            "within_phase_filter_assumption",
            "extrapolated_phase_filter",
            "requires_blank_or_fullwave",
        }
        assert ref["phase_filter_H_over_lambda0"] == pytest.approx(1400e-9 / 660e-9)
        assert ref["subwavelength_groove_validity_status"] in {
            "scalar_phase_filter_ok",
            "scalar_extrapolated",
            "fullwave_required",
        }
        assert ref["finite_length_assumption_status"] == "infinite_1d_phase_filter"
        assert ref["evanescent_component_unmodeled"] is True
        assert "H/lambda0" in ref["depth_validity_reason"]

    def test_tsuyama_bfp_integrated_reference_exports_roi_bridge(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="tsuyama_bfp_integrated",
            tsuyama_phase_filter_grid_n=512,
        )
        ref = compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg)
        assert set(TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS).issubset(ref)
        assert ref["reference_route"] == "paper_aligned_comparison"
        assert ref["reference_solver_route"] == "tsuyama_bfp_integrated"
        assert ref["reference_detector_bridge_status"] == "surrogate_roi"
        assert ref["reference_solver_detector_bridge_status"] == "surrogate_roi"
        assert ref["reference_claim_level"] == (
            "paper_aligned_detector_resolved_comparison"
        )
        assert isinstance(ref["E_ref_complex_roi"], complex)
        assert ref["I_ref_intensity_roi"] > 0.0
        assert ref["tsuyama_bfp_roi_sample_count"] > 0
        assert ref["tsuyama_bfp_roi_mode"] == "symmetric_na_aperture"
        assert ref["tsuyama_bfp_symmetric_vs_slit_roi_ratio"] is None
        assert 0.0 < ref["tsuyama_bfp_roi_fraction_of_total_diffraction"] <= 1.0
        assert abs(ref["E_ref_complex"]) == pytest.approx(ref["A_ref"])

    def test_reference_operating_point_balances_reference_gain_and_noise(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=5.0,
            reference_model="constant",
            noise_std=0.01,
            shot_noise_scale=0.0,
        )
        ref = compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg)
        diagnostics = build_reference_operating_point_diagnostics(
            ref,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
        )
        assert set(REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS).issubset(
            diagnostics
        )
        assert diagnostics["reference_design_amplitude_proxy"] == pytest.approx(5.0)
        assert diagnostics["I_ref_proxy"] == pytest.approx(25.0)
        assert diagnostics["reference_operating_band"] == (
            "electronics_noise_limited_useful"
        )
        assert diagnostics["reference_na_edge_status"] == "inside"
        assert diagnostics["reference_na_edge_rolloff_factor"] == pytest.approx(1.0)

    def test_reference_operating_point_marks_soft_na_edge_outside(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=5.0,
            reference_model="constant",
            reference_na_edge_policy="soft_rolloff",
        )
        ref = compute_reference_field(
            Channel(300e-9, BASELINE_CHANNEL.depth_m),
            BASELINE_OPTICAL,
            cfg,
        )
        diagnostics = build_reference_operating_point_diagnostics(
            ref,
            Channel(300e-9, BASELINE_CHANNEL.depth_m),
            BASELINE_OPTICAL,
            cfg,
        )
        assert diagnostics["reference_na_edge_status"] == "outside"
        assert diagnostics["reference_na_edge_rolloff_factor"] == pytest.approx(0.0)
        assert diagnostics["reference_operating_band"] == "reference_too_weak"

    def test_compute_reference_field_from_tsuyama_bfp_accepts_mask_roi(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            tsuyama_phase_filter_grid_n=512,
        )
        preliminary = compute_reference_field_from_tsuyama_bfp(
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            WATER.refractive_index_at(BASELINE_OPTICAL.wavelength_m),
            BASELINE_CHANNEL.wall_refractive_index_at(BASELINE_OPTICAL.wavelength_m),
        )
        q = preliminary["tsuyama_phase_filter_bfp_q_rad_per_m"]
        mask = np.abs(q) <= preliminary["tsuyama_bfp_roi_half_width_rad_per_m"]
        masked = compute_reference_field_from_tsuyama_bfp(
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            WATER.refractive_index_at(BASELINE_OPTICAL.wavelength_m),
            BASELINE_CHANNEL.wall_refractive_index_at(BASELINE_OPTICAL.wavelength_m),
            roi_mask=mask,
        )
        assert masked["reference_detector_bridge_status"] == "surrogate_roi"
        assert masked["tsuyama_bfp_roi_mode"] == "external_mask"
        assert masked["tsuyama_bfp_roi_sample_count"] == preliminary[
            "tsuyama_bfp_roi_sample_count"
        ]

    def test_configured_measured_bfp_roi_mask_changes_tsuyama_reference_integral(
        self,
        tmp_path,
    ):
        base_cfg = replace(
            DEFAULT_SIM_CFG,
            reference_model="tsuyama_bfp_integrated",
            tsuyama_phase_filter_grid_n=512,
        )
        unmasked = compute_reference_field(
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            base_cfg,
        )
        q = np.asarray(unmasked["tsuyama_phase_filter_bfp_q_rad_per_m"], dtype=float)
        roi_half_width = float(unmasked["tsuyama_bfp_roi_half_width_rad_per_m"])
        positive_roi_indices = np.flatnonzero((q > 0.0) & (np.abs(q) <= roi_half_width))
        target_q = float(q[positive_roi_indices[len(positive_roi_indices) // 2]])
        theta_rad = math.asin(
            min(abs(target_q) * BASELINE_OPTICAL.wavelength_m / (2.0 * math.pi), 1.0)
        )

        mask_path = tmp_path / "measured_bfp_mask.csv"
        mask_path.write_text(
            "pixel_x,pixel_y,theta_rad,phi_rad,mask_weight,solid_angle_weight\n"
            f"10,20,{theta_rad:.12e},0.0,1.0,1.0\n",
            encoding="utf-8",
        )
        (tmp_path / "measured_bfp_mask.csv.manifest.json").write_text(
            "{"
            '"calibration_kind":"bfp_roi_mask",'
            '"calibration_data_role":"experimental_measurement",'
            '"units":{'
            '"pixel_x":"pixel","pixel_y":"pixel","theta_rad":"rad",'
            '"phi_rad":"rad","mask_weight":"dimensionless",'
            '"solid_angle_weight":"sr"'
            "}"
            "}",
            encoding="utf-8",
        )
        masked_cfg = replace(
            base_cfg,
            bfp_roi_mask_path=str(mask_path),
            bfp_to_angle_jacobian_applied=True,
        )
        masked = compute_reference_field(
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            masked_cfg,
        )

        assert masked["bfp_roi_mask_status"] == "calibrated_mask_contract_loaded"
        assert masked["bfp_roi_mask_gate_passed"] is True
        assert masked["tsuyama_bfp_roi_mode"] == "calibrated_bfp_roi_mask_projected_1d"
        assert masked["reference_detector_bridge_status"] == (
            "calibrated_roi_mask_projected_1d_no_detector_unit_chain"
        )
        assert masked["bfp_roi_mask_projection_status"] == (
            "calibrated_mask_projected_to_1d_tsuyama_bfp_grid"
        )
        assert masked["bfp_roi_mask_projected_row_count"] == 1
        assert masked["tsuyama_bfp_roi_sample_count"] == 1
        assert masked["I_ref_intensity_roi"] != pytest.approx(
            unmasked["I_ref_intensity_roi"]
        )
        assert masked["E_ref_complex_roi"] != pytest.approx(
            unmasked["E_ref_complex_roi"]
        )

    def test_masked_bfp_roi_integrates_disjoint_segments_without_bridge(self):
        q = np.arange(6, dtype=float)
        field = np.ones_like(q, dtype=complex)
        mask = np.array([True, True, False, False, True, True], dtype=bool)

        roi = _integrate_masked_bfp_roi(q, field, mask)

        assert roi["roi_sample_count"] == 4
        assert roi["roi_complex_amplitude"] == pytest.approx(2.0 + 0.0j)
        assert roi["roi_intensity"] == pytest.approx(2.0)

    def test_compute_reference_field_from_tsuyama_bfp_supports_slit_lobe_roi(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            tsuyama_phase_filter_grid_n=512,
            tsuyama_bfp_roi_mode="slit_off_axis_lobe_surrogate",
        )
        ref = compute_reference_field_from_tsuyama_bfp(
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            WATER.refractive_index_at(BASELINE_OPTICAL.wavelength_m),
            BASELINE_CHANNEL.wall_refractive_index_at(BASELINE_OPTICAL.wavelength_m),
        )

        assert ref["tsuyama_bfp_roi_mode"] == "slit_off_axis_lobe_surrogate"
        assert ref["tsuyama_bfp_transmitted_block_q_rad_per_m"] > 0.0
        assert ref["tsuyama_bfp_lobe_center_q_rad_per_m"] > ref[
            "tsuyama_bfp_transmitted_block_q_rad_per_m"
        ]
        assert ref["tsuyama_bfp_lobe_sigma_q_rad_per_m"] > 0.0
        assert ref["tsuyama_bfp_roi_sample_count"] > 0
        assert 0.0 <= ref["tsuyama_bfp_roi_fraction"] <= 1.0
        assert ref["tsuyama_bfp_symmetric_vs_slit_roi_ratio"] is not None

    def test_reference_active_source_claim_gate_for_paper_aligned_solver(self):
        paper_cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            reference_model="paper_aligned_phase_filter",
        )
        paper = compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, paper_cfg)
        assert paper["reference_solver_route"] == "tsuyama_phase_filter_1d"
        assert paper["reference_solver_active_field_source"] == "paper_aligned_angular_surrogate"
        assert paper["paper_aligned_reference_claim"] == "diagnostic_only"
        assert paper["reference_solver_claim_level"] == "complex_field_solver_not_detector_unit"

        engineering_cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            reference_model="channel_angular_surrogate",
        )
        engineering = compute_reference_field(
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            engineering_cfg,
        )
        assert engineering["reference_solver_active_field_source"] == "angular_surrogate"
        assert engineering["paper_aligned_reference_claim"] == (
            "not_applicable_engineering_surrogate"
        )

    def test_signed_reference_phase_diagnostic_flips_but_active_polarity_is_blocked(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            reference_model="paper_aligned_phase_filter",
        )
        high_wall = compute_reference_field(
            Channel(800e-9, 1e-12, wall_refractive_index=1.46, wall_material_key=None),
            BASELINE_OPTICAL,
            cfg,
            medium_refractive_index=1.33,
        )
        low_wall = compute_reference_field(
            Channel(800e-9, 1e-12, wall_refractive_index=1.20, wall_material_key=None),
            BASELINE_OPTICAL,
            cfg,
            medium_refractive_index=1.33,
        )
        assert high_wall["theta_signed_rad"] < 0.0
        assert low_wall["theta_signed_rad"] > 0.0
        assert high_wall["phi_ref_model_rad"] == pytest.approx(-0.5 * np.pi, abs=0.1)
        assert low_wall["phi_ref_model_rad"] == pytest.approx(0.5 * np.pi, abs=0.1)
        assert high_wall["polarity_claim_from_phase_delay_over_2_allowed"] is False
        assert low_wall["polarity_claim_from_phase_delay_over_2_allowed"] is False
        assert high_wall["reference_absolute_polarity_claim"] == (
            "blocked_active_reference_phase_surrogate"
        )

    def test_geometry_scaled_behaves_as_expected(self):
        cfg_zero = SimulationConfig(
            0.2, 20000.0, 2e-4,
            reference_model="geometry_scaled",
            ref_alpha=0.0, ref_beta=0.0, ref_gamma=0.0, rho=10.0,
        )
        ref_zero = compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg_zero)
        assert ref_zero["A_ref"] == pytest.approx(10.0)
        assert ref_zero["g_ref"] == pytest.approx(1.0)

        cfg = SimulationConfig(
            0.2, 20000.0, 2e-4,
            reference_model="geometry_scaled",
            ref_alpha=0.5, ref_beta=1.0, ref_gamma=1.0, rho=10.0,
        )
        ref_wide = compute_reference_field(Channel(1600e-9, 550e-9), BASELINE_OPTICAL, cfg)
        ref_narrow = compute_reference_field(Channel(500e-9, 550e-9), BASELINE_OPTICAL, cfg)
        assert ref_wide["g_ref"] > ref_narrow["g_ref"]
        assert ref_wide["reference_model_precision_tier"] == "legacy_empirical_fallback"
        assert ref_wide["reference_model_role"] == "legacy_fallback_only"
        assert ref_wide["reference_geometry_depth_exponent"] == pytest.approx(1.0)
        assert ref_wide["reference_geometry_depth_scaling_class"] == "amplitude_like"

    def test_calibrated_lookup_exact_grid_point(self):
        path = self._write_reference_calibration()
        try:
            cfg = SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                rho=10.0,
                reference_model="calibrated_lookup",
                reference_calibration_path=path,
            )
            ref = compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg)
            assert ref["g_ref"] == pytest.approx(1.10)
            assert ref["A_ref"] == pytest.approx(11.0)
            assert ref["phi_ref_rad"] == pytest.approx(0.05)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_calibrated_lookup_rejects_synthetic_reference_template(self):
        template_path = REPO_ROOT / "calibration" / "reference_blank_channel_template.csv"
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="calibrated_lookup",
            reference_calibration_path=str(template_path),
        )
        with pytest.raises(ValueError, match="synthetic/template fixture"):
            compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg)

    def test_calibrated_lookup_A_ref_is_rho_independent_and_absolute_provenance(self):
        rows = """width_nm,depth_nm,wavelength_nm,g_ref,A_ref,phi_ref_rad
800,550,660,1.10,42.0,0.05
"""
        tmp = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
        tmp.write(rows)
        tmp.close()
        try:
            cfg_low = SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                rho=10.0,
                reference_model="calibrated_lookup",
                reference_route="calibrated_primary",
                reference_calibration_path=tmp.name,
            )
            cfg_high = SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                rho=99.0,
                reference_model="calibrated_lookup",
                reference_route="calibrated_primary",
                reference_calibration_path=tmp.name,
            )
            ref_low = compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg_low)
            ref_high = compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg_high)
            assert ref_low["A_ref"] == pytest.approx(42.0)
            assert ref_high["A_ref"] == pytest.approx(42.0)
            assert ref_low["reference_route"] == "calibrated_primary"
            assert ref_low["reference_claim_level"] == "reference_calibrated_relative"
            assert ref_low["reference_calibration_amplitude_status"] == "absolute_calibrated"
            assert ref_low["reference_calibration_amplitude_source"] == "A_ref"
            assert ref_low["rho_used_for_reference_amplitude"] is False
            assert ref_low["reference_phase_calibration_status"] == "model_assigned_or_unknown_phase"
            assert ref_low["reference_phase_absolute_claim"] == "not_measured_absolute_phase"
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_calibrated_lookup_g_ref_only_remains_rho_dependent_scale_only(self):
        rows = """width_nm,depth_nm,wavelength_nm,g_ref,A_ref,phi_ref_rad
800,550,660,1.10,,0.05
"""
        tmp = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False)
        tmp.write(rows)
        tmp.close()
        try:
            cfg_low = SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                rho=10.0,
                reference_model="calibrated_lookup",
                reference_route="calibrated_primary",
                reference_calibration_path=tmp.name,
            )
            cfg_high = SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                rho=20.0,
                reference_model="calibrated_lookup",
                reference_route="calibrated_primary",
                reference_calibration_path=tmp.name,
            )
            ref_low = compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg_low)
            ref_high = compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg_high)
            assert ref_low["A_ref"] == pytest.approx(11.0)
            assert ref_high["A_ref"] == pytest.approx(22.0)
            assert ref_low["reference_calibration_amplitude_status"] == "calibrated_scale_only"
            assert ref_low["reference_calibration_amplitude_source"] == "rho_times_g_ref"
            assert ref_low["rho_used_for_reference_amplitude"] is True
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    def test_calibrated_lookup_interpolates_inside_grid(self):
        path = self._write_reference_calibration()
        try:
            cfg = SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                rho=10.0,
                reference_model="calibrated_lookup",
                reference_calibration_path=path,
            )
            ref = compute_reference_field(Channel(1000e-9, 725e-9), BASELINE_OPTICAL, cfg)
            assert 1.20 < ref["g_ref"] < 1.30
            assert 12.0 < ref["A_ref"] < 13.0
            assert 0.05 < ref["phi_ref_rad"] < 0.08
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_calibrated_lookup_sets_extrapolation_flag_outside_grid(self):
        path = self._write_reference_calibration()
        try:
            cfg = SimulationConfig(
                0.2,
                20000.0,
                2e-4,
                rho=10.0,
                reference_model="calibrated_lookup",
                reference_calibration_path=path,
            )
            ref = compute_reference_field(Channel(2000e-9, 2000e-9), BASELINE_OPTICAL, cfg)
            assert ref["calibration_extrapolated"] is True
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_channel_angular_surrogate_varies_with_geometry(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
        )
        ref_wide = compute_reference_field(Channel(1200e-9, 550e-9), BASELINE_OPTICAL, cfg)
        ref_narrow = compute_reference_field(Channel(700e-9, 550e-9), BASELINE_OPTICAL, cfg)
        assert ref_wide["g_ref"] != pytest.approx(ref_narrow["g_ref"])
        assert np.isfinite(ref_wide["phi_ref_rad"])
        assert np.isfinite(ref_narrow["phi_ref_rad"])

    def test_channel_angular_surrogate_operator_signature_tracks_slit_and_changes_reference(self):
        cfg_wide = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            collection_phi_sigma_rad=np.deg2rad(14.0),
            slit_phi_limit_rad=np.deg2rad(20.0),
        )
        cfg_narrow = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            collection_phi_sigma_rad=np.deg2rad(6.0),
            slit_phi_limit_rad=np.deg2rad(8.0),
        )
        channel = Channel(1200e-9, 550e-9)
        ref_wide = compute_reference_field(channel, BASELINE_OPTICAL, cfg_wide)
        ref_narrow = compute_reference_field(channel, BASELINE_OPTICAL, cfg_narrow)
        assert ref_narrow["A_ref"] != pytest.approx(ref_wide["A_ref"])
        assert "throughput=" in ref_wide["operator_signature"]
        assert "throughput=" in ref_narrow["operator_signature"]
        assert ref_wide["operator_signature"] != ref_narrow["operator_signature"]

    def test_channel_angular_surrogate_tracks_medium_refractive_index(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
        )
        ref_low = compute_reference_field(
            Channel(1200e-9, 550e-9),
            BASELINE_OPTICAL,
            cfg,
            medium_refractive_index=1.20,
        )
        ref_high = compute_reference_field(
            Channel(1200e-9, 550e-9),
            BASELINE_OPTICAL,
            cfg,
            medium_refractive_index=1.45,
        )
        assert ref_low["reference_medium_refractive_index"] == pytest.approx(1.20)
        assert ref_high["reference_medium_refractive_index"] == pytest.approx(1.45)
        assert ref_low["A_ref"] != pytest.approx(ref_high["A_ref"])

    def test_channel_angular_surrogate_applies_na_cutoff_only_to_uncollectable_cases(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
        )
        optical = replace(BASELINE_OPTICAL, wavelength_m=660e-9, NA_collection=0.9)
        blocked = compute_reference_field(
            Channel(700e-9, 550e-9),
            optical,
            cfg,
            medium_refractive_index=WATER.refractive_index,
        )
        allowed = compute_reference_field(
            Channel(800e-9, 550e-9),
            optical,
            cfg,
            medium_refractive_index=WATER.refractive_index,
        )
        assert blocked["na_cutoff_active"] is True
        assert blocked["A_ref"] == pytest.approx(0.0)
        assert blocked["g_ref"] == pytest.approx(0.0)
        assert blocked["na_cutoff_W_min_m"] == pytest.approx(660e-9 / 0.9)
        assert allowed["na_cutoff_active"] is False
        assert allowed["A_ref"] > 0.0
        assert allowed["g_ref"] > 0.0

    def test_paper_aligned_route_records_soft_na_policy_without_hard_zero(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="paper_aligned_phase_filter",
            reference_route="paper_aligned_comparison",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
        )
        optical = replace(BASELINE_OPTICAL, wavelength_m=660e-9, NA_collection=0.9)
        ref = compute_reference_field(
            Channel(700e-9, 550e-9),
            optical,
            cfg,
            medium_refractive_index=WATER.refractive_index,
        )
        assert ref["reference_route"] == "paper_aligned_comparison"
        assert ref["na_cutoff_condition_met"] is True
        assert ref["na_cutoff_active"] is False
        assert ref["na_cutoff_hard_zero_applied"] is False
        assert ref["na_cutoff_policy"] == "soft_operator_no_hard_zero"
        assert ref["A_ref"] > 0.0

    def test_channel_angular_surrogate_exports_linear_delta_n_scaling_diagnostics(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
        )
        channel = Channel(1200e-9, 550e-9)
        ref = compute_reference_field(
            channel,
            BASELINE_OPTICAL,
            cfg,
            medium_refractive_index=1.20,
        )
        expected_contrast = abs(channel.wall_refractive_index_at(BASELINE_OPTICAL.wavelength_m) - 1.20)
        expected_scale = expected_contrast / ref["reference_index_contrast_baseline_abs"]
        assert ref["reference_index_contrast_abs"] == pytest.approx(expected_contrast)
        assert ref["reference_contrast_amplitude_scale"] == pytest.approx(expected_scale)
        assert ref["reference_contrast_scaling_law"] == "amplitude~|n_wall-n_medium|"

    def test_channel_angular_surrogate_exports_phase_grating_diagnostics(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
        )
        channel = Channel(1200e-9, 1000e-9)
        ref = compute_reference_field(
            channel,
            BASELINE_OPTICAL,
            cfg,
            medium_refractive_index=1.20,
        )
        contrast = abs(channel.wall_refractive_index_at(BASELINE_OPTICAL.wavelength_m) - 1.20)
        phase_delay = 2.0 * np.pi * contrast * channel.depth_m / BASELINE_OPTICAL.wavelength_m
        expected_sine_scale = max(2.0 * abs(np.sin(0.5 * phase_delay)), 0.05)
        expected_legacy_sinc_scale = max(
            (channel.depth_m / 550e-9) * abs(np.sinc(phase_delay / (2.0 * np.pi))),
            0.05,
        )
        expected_first_order_efficiency = np.sin(0.5 * phase_delay) ** 2
        expected_zeroth_order_efficiency = np.cos(0.5 * phase_delay) ** 2
        expected_amplitude_envelope = abs(np.sin(0.5 * phase_delay))
        assert ref["reference_phase_delay_rad"] == pytest.approx(phase_delay)
        assert ref["reference_phase_grating_mode"] == "phase_grating_sine"
        assert ref["reference_phase_grating_phase_rad"] == pytest.approx(0.5 * phase_delay)
        assert ref["reference_phase_grating_amplitude_scale"] == pytest.approx(expected_sine_scale)
        assert ref["reference_phase_grating_sine_amplitude_scale"] == pytest.approx(
            expected_sine_scale
        )
        assert ref["reference_phase_grating_legacy_sinc_amplitude_scale"] == pytest.approx(
            expected_legacy_sinc_scale
        )
        assert ref["reference_contrast_scaling_role"] == "small_signal_diagnostic_only"
        assert ref["reference_phase_grating_model"].startswith("thin_phase_grating_surrogate")
        assert ref["reference_diffraction_efficiency_zeroth_order"] == pytest.approx(
            expected_zeroth_order_efficiency
        )
        assert ref["reference_diffraction_efficiency_first_order"] == pytest.approx(
            expected_first_order_efficiency
        )
        assert ref["reference_field_amplitude_envelope_nominal"] == pytest.approx(
            expected_amplitude_envelope
        )
        assert ref["reference_field_amplitude_envelope_lower"] == pytest.approx(
            0.5 * expected_amplitude_envelope
        )
        assert ref["reference_field_amplitude_envelope_upper"] == pytest.approx(
            2.0 * expected_amplitude_envelope
        )

    def test_channel_angular_surrogate_can_still_export_legacy_sinc_phase_grating_mode(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            reference_phase_grating_mode="legacy_sinc_linearized",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
        )
        channel = Channel(1200e-9, 1000e-9)
        ref = compute_reference_field(
            channel,
            BASELINE_OPTICAL,
            cfg,
            medium_refractive_index=1.20,
        )
        contrast = abs(channel.wall_refractive_index_at(BASELINE_OPTICAL.wavelength_m) - 1.20)
        phase_delay = 2.0 * np.pi * contrast * channel.depth_m / BASELINE_OPTICAL.wavelength_m
        expected_legacy_sinc_scale = max(
            (channel.depth_m / 550e-9) * abs(np.sinc(phase_delay / (2.0 * np.pi))),
            0.05,
        )
        assert ref["reference_phase_grating_mode"] == "legacy_sinc_linearized"
        assert ref["reference_phase_grating_amplitude_scale"] == pytest.approx(
            expected_legacy_sinc_scale
        )
        assert ref["reference_phase_grating_legacy_sinc_amplitude_scale"] == pytest.approx(
            expected_legacy_sinc_scale
        )
        assert ref["reference_contrast_scaling_role"] == "active_multiplier"

    def test_channel_angular_surrogate_phase_grating_changes_depth_response(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
        )
        ref_shallow = compute_reference_field(Channel(1200e-9, 500e-9), BASELINE_OPTICAL, cfg)
        ref_deep = compute_reference_field(Channel(1200e-9, 2000e-9), BASELINE_OPTICAL, cfg)
        assert ref_shallow["reference_phase_delay_rad"] != pytest.approx(
            ref_deep["reference_phase_delay_rad"]
        )
        assert ref_shallow["reference_phase_grating_amplitude_scale"] != pytest.approx(
            ref_deep["reference_phase_grating_amplitude_scale"]
        )
        assert ref_shallow["A_ref"] != pytest.approx(ref_deep["A_ref"])

    def test_channel_angular_surrogate_applies_width_saturation_for_narrow_channels(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            reference_width_saturation_mode="waveguide_cutoff_surrogate",
            reference_width_saturation_cutoff_ratio=0.75,
        )
        narrow = compute_reference_field(Channel(320e-9, 550e-9), BASELINE_OPTICAL, cfg)
        wide = compute_reference_field(Channel(1600e-9, 550e-9), BASELINE_OPTICAL, cfg)
        assert narrow["reference_width_saturation_mode"] == "waveguide_cutoff_surrogate"
        assert narrow["reference_width_saturation_status"] == "active_soft_cutoff"
        assert narrow["reference_width_effective_m"] > 320e-9
        assert narrow["reference_width_saturation_factor"] > 1.0
        assert wide["reference_width_saturation_factor"] >= 1.0
        assert wide["reference_width_saturation_factor"] < 1.2

    def test_channel_angular_surrogate_can_disable_width_saturation(self):
        cfg_active = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            reference_width_saturation_mode="waveguide_cutoff_surrogate",
            reference_width_saturation_cutoff_ratio=0.75,
        )
        cfg_none = replace(cfg_active, reference_width_saturation_mode="none")
        optical = replace(BASELINE_OPTICAL, wavelength_m=404e-9)
        channel = Channel(500e-9, 550e-9)
        ref_active = compute_reference_field(
            channel,
            optical,
            cfg_active,
            medium_refractive_index=WATER.refractive_index,
        )
        ref_none = compute_reference_field(
            channel,
            optical,
            cfg_none,
            medium_refractive_index=WATER.refractive_index,
        )
        assert ref_active["na_cutoff_active"] is False
        assert ref_none["na_cutoff_active"] is False
        assert ref_none["reference_width_saturation_status"] == "disabled_legacy_width_sinc"
        assert ref_none["reference_width_effective_m"] == pytest.approx(channel.width_m)
        assert ref_active["reference_width_effective_m"] > ref_none["reference_width_effective_m"]
        assert ref_active["A_ref"] != pytest.approx(ref_none["A_ref"])

    def test_channel_angular_surrogate_exports_rectangular_phase_jump_diagnostics(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            slit_phi_limit_rad=np.deg2rad(45.0),
            collection_sigma_rad=np.deg2rad(45.0),
        )
        ref = compute_reference_field(
            Channel(2000e-9, 2000e-9),
            BASELINE_OPTICAL,
            cfg,
        )
        assert ref["reference_phase_structure_mode"] == "rectangular_fraunhofer_pi_jumps"
        assert ref["reference_phase_jump_fraction"] > 0.0
        assert (
            ref["reference_width_phase_jump_fraction"] > 0.0
            or ref["reference_depth_phase_jump_fraction"] > 0.0
        )
        assert ref["reference_phase_jump_max_rad"] >= np.pi - 1e-12

    def test_reference_projection_cross_polarization_suppresses_effective_reference(self):
        cfg_match = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            scattering_projection_mode="parallel",
            reference_projection_mode="match_scattering",
            cross_polarization_leakage=0.05,
        )
        cfg_cross = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            scattering_projection_mode="parallel",
            reference_projection_mode="perpendicular",
            cross_polarization_leakage=0.05,
        )
        ref_match = compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg_match)
        ref_cross = compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg_cross)
        assert ref_match["reference_projection_alignment_status"] == "matched"
        assert ref_cross["reference_projection_alignment_status"] == "cross_suppressed"
        assert ref_match["reference_projection_basis"] == "parallel"
        assert ref_cross["reference_projection_basis"] == "parallel"
        assert ref_match["reference_projection_basis_match"] is True
        assert ref_cross["reference_projection_basis_match"] is True
        assert ref_match["reference_projection_coupling_status"] == "shared_basis_matched"
        assert ref_cross["reference_projection_coupling_status"] == "shared_basis_cross_suppressed"
        assert ref_cross["reference_projection_amplitude_factor"] == pytest.approx(0.05)
        assert ref_cross["A_ref_unprojected"] == pytest.approx(ref_match["A_ref_unprojected"])
        assert ref_cross["g_ref_geometry"] == pytest.approx(ref_match["g_ref_geometry"])
        assert ref_cross["A_ref"] == pytest.approx(
            ref_match["A_ref"] * cfg_cross.cross_polarization_leakage,
            rel=1e-6,
        )

    def test_reference_field_trace_uniform_mode_stays_constant(self):
        cfg = SimulationConfig(0.2, 20000.0, 2e-4, rho=10.0, reference_spatial_mode="uniform")
        ref = compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg)
        traj = {
            "time_s": np.arange(3) * 5e-5,
            "x_m": np.array([-100e-9, 0.0, 100e-9]),
            "z_m": np.array([100e-9, 0.0, -100e-9]),
        }
        trace = compute_reference_field_trace(
            traj,
            ref,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
        )
        np.testing.assert_allclose(trace["A_ref_trace"], np.full(3, ref["A_ref"]), atol=1e-12)
        np.testing.assert_allclose(trace["phi_ref_trace_rad"], np.full(3, ref["phi_ref_rad"]), atol=1e-12)

    def test_reference_field_trace_cross_section_surrogate_varies_with_position(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_spatial_mode="cross_section_surrogate",
            reference_spatial_amplitude_strength=0.4,
            reference_spatial_phase_strength_rad=0.6,
        )
        ref = compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg)
        traj = {
            "time_s": np.arange(3) * 5e-5,
            "x_m": np.array([0.0, BASELINE_CHANNEL.width_m / 2, 0.0]),
            "z_m": np.array([0.0, 0.0, BASELINE_CHANNEL.depth_m / 2]),
        }
        trace = compute_reference_field_trace(
            traj,
            ref,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
        )
        assert trace["A_ref_trace"][0] > trace["A_ref_trace"][1]
        assert trace["A_ref_trace"][0] > trace["A_ref_trace"][2]
        assert trace["phi_ref_trace_rad"][0] != pytest.approx(trace["phi_ref_trace_rad"][2])
        assert np.max(np.abs(trace["reference_spatial_phase_rad"])) > 0.0

    def test_light_reference_field_trace_omits_complex_diagnostics(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            rho=10.0,
            reference_spatial_mode="cross_section_surrogate",
            reference_spatial_amplitude_strength=0.4,
            reference_spatial_phase_strength_rad=0.6,
        )
        ref = compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg)
        traj = {
            "time_s": np.arange(3) * 5e-5,
            "x_m": np.array([0.0, BASELINE_CHANNEL.width_m / 2, 0.0]),
            "z_m": np.array([0.0, 0.0, BASELINE_CHANNEL.depth_m / 2]),
        }
        full = compute_reference_field_trace(
            traj,
            ref,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
        )
        light = compute_reference_field_trace(
            traj,
            ref,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            export_full_diagnostics=False,
        )

        np.testing.assert_allclose(light["A_ref_trace"], full["A_ref_trace"])
        np.testing.assert_allclose(light["phi_ref_trace_rad"], full["phi_ref_trace_rad"])
        assert "E_ref_trace_complex" not in light
        assert "reference_x_norm" not in light
        assert "reference_z_norm" not in light


class TestPaperAlignedProfiles:
    def test_list_paper_aligned_profiles_exposes_expected_profiles(self):
        profiles = list_paper_aligned_profiles()
        assert set(profiles) >= {
            "diffraction_2020",
            "nodi_2022",
            "paired_2024",
            "paired_2024_10sigma",
            "pod_2019_2020",
        }
        assert profiles["pod_2019_2020"]["status"] == "unavailable"
        assert profiles["diffraction_2020"]["reference_route"] == "paper_aligned_comparison"
        assert profiles["diffraction_2020"]["reference_solver_route"] == "tsuyama_phase_filter_1d"

    def test_apply_paper_aligned_profile_nodi_2022_sets_expected_fields(self):
        cfg = apply_paper_aligned_profile(DEFAULT_SIM_CFG, "nodi_2022")
        assert cfg.reference_model == "paper_aligned_phase_filter"
        assert cfg.reference_route == "paper_aligned_comparison"
        assert cfg.illumination_mode == "overfill"
        assert cfg.readout_preset == "tsuyama_2022_counting_10sigma"
        assert cfg.readout_observable_mode == "magnitude"
        assert cfg.pulse_detection_mode == "positive"
        assert cfg.detection_decision_mode == "single_channel"
        assert cfg.engineering_decision_basis == "single_channel"
        assert cfg.nodi_lockin_frequency_Hz == pytest.approx(3000.0)
        assert cfg.threshold_sigma == pytest.approx(10.0)
        assert cfg.threshold_tail == "one_sided"
        assert cfg.min_peak_width_s == pytest.approx(2.5e-3)
        assert cfg.min_peak_interval_s == pytest.approx(0.1)
        assert cfg.engineering_max_phase_flip_fraction == pytest.approx(1.0)

    def test_apply_paper_aligned_profile_paired_2024_sets_expected_fields(self):
        cfg = apply_paper_aligned_profile(DEFAULT_SIM_CFG, "paired_2024")
        assert cfg.reference_model == "paper_aligned_phase_filter"
        assert cfg.reference_route == "paper_aligned_comparison"
        assert cfg.illumination_mode == "overfill"
        assert cfg.readout_preset == "tsuyama_2024_paired_5sigma"
        assert cfg.readout_observable_mode == "magnitude"
        assert cfg.pulse_detection_mode == "positive"
        assert cfg.detection_decision_mode == "paired_channel"
        assert cfg.engineering_decision_basis == "paired_channel"
        assert cfg.pod_lockin_frequency_Hz == pytest.approx(4100.0)
        assert cfg.nodi_lockin_frequency_Hz == pytest.approx(1200.0)
        assert cfg.threshold_sigma == pytest.approx(5.0)
        assert cfg.threshold_tail == "one_sided"
        assert cfg.pulse_pairing_tolerance_s == pytest.approx(5.0e-2)
        assert cfg.engineering_max_phase_flip_fraction == pytest.approx(1.0)

    def test_apply_paper_aligned_profile_paired_2024_10sigma_sets_expected_fields(self):
        cfg = apply_paper_aligned_profile(DEFAULT_SIM_CFG, "paired_2024_10sigma")
        assert cfg.readout_preset == "tsuyama_2024_paired_10sigma"
        assert cfg.threshold_sigma == pytest.approx(10.0)
        assert cfg.threshold_tail == "one_sided"
        assert cfg.detection_decision_mode == "paired_channel"
        assert cfg.readout_observable_mode == "magnitude"

    def test_apply_paper_aligned_profile_unavailable_pod_profile_raises(self):
        with pytest.raises(ValueError, match="not available"):
            apply_paper_aligned_profile(DEFAULT_SIM_CFG, "pod_2019_2020")


class TestTsuyamaPhaseFilter:
    def test_solver_exports_complex_decomposition_and_numerical_invariants(self):
        result = compute_tsuyama_phase_filter_bfp_field(
            channel_width_m=800e-9,
            channel_depth_m=20e-9,
            wavelength_m=660e-9,
            medium_refractive_index=1.33,
            wall_refractive_index=1.46,
            gaussian_waist_m=2.0e-6,
            n_grid=2048,
        )
        np.testing.assert_allclose(
            result["E_diffraction_BFP"],
            result["E_total_channel_BFP"] - result["E_no_channel_BFP"],
            rtol=1e-10,
            atol=1e-12,
        )
        factor = result["thin_phase_complex_factor"]
        np.testing.assert_allclose(
            result["E_diffraction_BFP"],
            factor * result["thin_phase_basis_BFP"],
            rtol=1e-10,
            atol=1e-12,
        )
        invariants = result["tsuyama_phase_filter_numerical_invariants"]
        assert invariants["W_code_convention"] == "W_code=2*l_paper"
        assert invariants["H_code_convention"] == "H_code=d_paper"
        assert invariants["lambda0_definition"] == "vacuum_wavelength_m"
        assert invariants["fft_sign_convention"] == "forward_exp_minus_i_q_x"
        assert invariants["power_normalization_check"] == "parseval_pass"
        assert invariants["parseval_relative_error"] < 1e-10

    def test_small_phase_perturbation_phase_uses_signed_exp_i_theta_minus_one(self):
        result = compute_tsuyama_phase_filter_bfp_field(
            channel_width_m=800e-9,
            channel_depth_m=1e-12,
            wavelength_m=660e-9,
            medium_refractive_index=1.33,
            wall_refractive_index=1.46,
            gaussian_waist_m=2.0e-6,
            n_grid=2048,
        )
        basis = result["thin_phase_basis_BFP"]
        idx = int(np.argmax(np.abs(basis)))
        perturbation_phase = np.angle(result["E_diffraction_BFP"][idx] / basis[idx])
        expected = -0.5 * np.pi
        assert result["theta_signed_rad"] < 0.0
        assert perturbation_phase == pytest.approx(expected, abs=2e-4)
        assert result["thin_phase_perturbation_phase_rad"] == pytest.approx(
            expected,
            abs=2e-4,
        )

    def test_phase_filter_validity_thresholds_depth_by_lambda0(self):
        shallow = classify_phase_filter_validity(
            channel_width_m=800e-9,
            channel_depth_m=0.7 * 660e-9,
            wavelength_m=660e-9,
            medium_refractive_index=1.33,
            wall_refractive_index=1.46,
        )
        mid = classify_phase_filter_validity(
            channel_width_m=800e-9,
            channel_depth_m=1.0 * 660e-9,
            wavelength_m=660e-9,
            medium_refractive_index=1.33,
            wall_refractive_index=1.46,
        )
        deep = classify_phase_filter_validity(
            channel_width_m=800e-9,
            channel_depth_m=1.8 * 660e-9,
            wavelength_m=660e-9,
            medium_refractive_index=1.33,
            wall_refractive_index=1.46,
        )
        assert shallow["phase_filter_validity"] == "within_phase_filter_assumption"
        assert mid["phase_filter_validity"] == "extrapolated_phase_filter"
        assert deep["phase_filter_validity"] == "requires_blank_or_fullwave"
        assert deep["requires_calibration_or_fullwave"] is True

    def test_integrate_bfp_roi_reports_complex_amplitude_and_mask_units(self):
        result = compute_tsuyama_phase_filter_bfp_field(
            channel_width_m=800e-9,
            channel_depth_m=20e-9,
            wavelength_m=660e-9,
            medium_refractive_index=1.33,
            wall_refractive_index=1.46,
            gaussian_waist_m=2.0e-6,
            n_grid=2048,
        )
        roi = integrate_bfp_roi(
            result["bfp_q_rad_per_m"],
            result["E_diffraction_BFP"],
            roi_half_width_rad_per_m=1.0e6,
        )
        assert isinstance(roi["roi_complex_amplitude"], complex)
        assert roi["detector_mask_units"] == "rad_per_m"
        assert roi["roi_sample_count"] > 0


class TestIllumination:
    def test_focus_maximum(self):
        optical = BASELINE_OPTICAL
        result = compute_illumination_envelope(
            np.array([optical.focus_x_m]),
            np.array([optical.focus_y_m]),
            np.array([optical.focus_z_m]),
            optical,
        )
        assert result["A_env"][0] == pytest.approx(1.0)
        assert result["I_inc_W_m2"][0] == pytest.approx(optical.peak_irradiance_W_m2)

    def test_monotonic_decrease(self):
        optical = BASELINE_OPTICAL
        y = np.linspace(optical.focus_y_m, optical.focus_y_m + 5e-6, 100)
        result = compute_illumination_envelope(
            np.full_like(y, optical.focus_x_m),
            y,
            np.full_like(y, optical.focus_z_m),
            optical,
        )
        assert np.all(np.diff(result["A_env"]) <= 1e-15)

    def test_aenv_squared_equals_ratio(self):
        optical = BASELINE_OPTICAL
        y = np.linspace(-5e-6, 5e-6, 100)
        result = compute_illumination_envelope(np.zeros_like(y), y, np.zeros_like(y), optical)
        ratio = result["I_inc_W_m2"] / optical.peak_irradiance_W_m2
        np.testing.assert_allclose(result["A_env"] ** 2, ratio, atol=1e-12)

    def test_aenv_range(self):
        optical = BASELINE_OPTICAL
        y = np.linspace(-1e-4, 1e-4, 1000)
        result = compute_illumination_envelope(np.zeros_like(y), y, np.zeros_like(y), optical)
        assert np.all(result["A_env"] >= 0)
        assert np.all(result["A_env"] <= 1.0 + 1e-12)

    def test_complex_envelope_preserves_amplitude_and_adds_phase(self):
        optical = BASELINE_OPTICAL
        y = np.array([optical.focus_y_m - 1e-6, optical.focus_y_m, optical.focus_y_m + 1e-6])
        result = compute_illumination_envelope(
            np.zeros_like(y),
            y,
            np.zeros_like(y),
            optical,
            medium_refractive_index=WATER.refractive_index,
        )
        np.testing.assert_allclose(np.abs(result["E_env_complex"]), result["A_env"], atol=1e-12)
        assert result["phi_beam_rad"][0] < result["phi_beam_rad"][1] < result["phi_beam_rad"][2]

    def test_light_illumination_diagnostics_keep_signal_fields_without_heavy_arrays(self):
        optical = BASELINE_OPTICAL
        y = np.array([optical.focus_y_m - 1e-6, optical.focus_y_m, optical.focus_y_m + 1e-6])
        full = compute_illumination_envelope(
            np.zeros_like(y),
            y,
            np.zeros_like(y),
            optical,
            medium_refractive_index=WATER.refractive_index,
        )
        light = compute_illumination_envelope(
            np.zeros_like(y),
            y,
            np.zeros_like(y),
            optical,
            medium_refractive_index=WATER.refractive_index,
            export_full_diagnostics=False,
        )

        for key in (
            "A_env",
            "A_env_scalar",
            "phi_beam_rad",
            "phi_beam_gouy_rad",
            "phi_beam_curv_rad",
        ):
            np.testing.assert_allclose(light[key], full[key], atol=0.0)
        assert "I_inc_W_m2" not in light
        assert "I_inc_scalar_W_m2" not in light
        assert "E_env_complex" not in light
        assert "beam_inverse_wavefront_radius_m_inv" not in light
        assert "beam_inverse_wavefront_radius_m_inv" in full

    def test_light_illumination_2d_matches_full_signal_fields(self):
        optical = BASELINE_OPTICAL
        y = optical.focus_y_m + np.vstack(
            [
                np.linspace(-1e-6, 1e-6, 5),
                np.linspace(1e-6, -1e-6, 5),
            ]
        )
        x = np.array(
            [
                np.linspace(-100e-9, 100e-9, 5),
                np.linspace(80e-9, -120e-9, 5),
            ]
        )
        z = np.array(
            [
                np.linspace(60e-9, -40e-9, 5),
                np.linspace(-30e-9, 70e-9, 5),
            ]
        )
        full = compute_illumination_envelope(
            x,
            y,
            z,
            optical,
            medium_refractive_index=WATER.refractive_index,
            sim_cfg=DEFAULT_SIM_CFG,
        )
        light = compute_illumination_envelope(
            x,
            y,
            z,
            optical,
            medium_refractive_index=WATER.refractive_index,
            sim_cfg=DEFAULT_SIM_CFG,
            export_full_diagnostics=False,
        )

        for key in (
            "A_env",
            "A_env_scalar",
            "phi_beam_rad",
            "phi_beam_gouy_rad",
            "phi_beam_curv_rad",
        ):
            np.testing.assert_allclose(light[key], full[key], rtol=0.0, atol=0.0)
        assert "I_inc_W_m2" not in light

    def test_beam_curvature_phase_vanishes_at_focus_even_off_axis(self):
        optical = BASELINE_OPTICAL
        x = np.array([-200e-9, 0.0, 200e-9])
        y = np.full_like(x, optical.focus_y_m)
        z = np.array([150e-9, 0.0, -150e-9])
        result = compute_illumination_envelope(
            x,
            y,
            z,
            optical,
            medium_refractive_index=WATER.refractive_index,
        )
        np.testing.assert_allclose(result["phi_beam_curv_rad"], 0.0, atol=1e-12)
        np.testing.assert_allclose(
            result["phi_beam_rad"],
            result["phi_beam_gouy_rad"],
            atol=1e-12,
        )

    def test_beam_curvature_phase_appears_only_off_axis_away_from_focus(self):
        optical = BASELINE_OPTICAL
        y = np.array([
            optical.focus_y_m + 3e-6,
            optical.focus_y_m + 3e-6,
        ])
        z = np.zeros_like(y)
        x = np.array([0.0, 250e-9])
        result = compute_illumination_envelope(
            x,
            y,
            z,
            optical,
            medium_refractive_index=WATER.refractive_index,
        )
        assert result["phi_beam_curv_rad"][0] == pytest.approx(0.0, abs=1e-12)
        assert abs(result["phi_beam_curv_rad"][1]) > 0.0
        np.testing.assert_allclose(
            result["phi_beam_rad"],
            result["phi_beam_gouy_rad"] + result["phi_beam_curv_rad"],
            atol=1e-12,
        )

    def test_illumination_polarization_cross_channel_suppresses_envelope(self):
        optical = BASELINE_OPTICAL
        y = np.array([optical.focus_y_m])
        cfg_match = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            scattering_projection_mode="parallel",
            illumination_polarization_mode="match_scattering",
            cross_polarization_leakage=0.05,
        )
        cfg_cross = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            scattering_projection_mode="parallel",
            illumination_polarization_mode="perpendicular",
            cross_polarization_leakage=0.05,
        )
        match = compute_illumination_envelope(
            np.array([optical.focus_x_m]),
            y,
            np.array([optical.focus_z_m]),
            optical,
            sim_cfg=cfg_match,
        )
        cross = compute_illumination_envelope(
            np.array([optical.focus_x_m]),
            y,
            np.array([optical.focus_z_m]),
            optical,
            sim_cfg=cfg_cross,
        )
        assert match["illumination_polarization_alignment_status"] == "matched"
        assert cross["illumination_polarization_alignment_status"] == "cross_suppressed"
        assert match["illumination_projection_basis"] == "parallel"
        assert cross["illumination_projection_basis"] == "parallel"
        assert match["illumination_projection_basis_match"] is True
        assert cross["illumination_projection_basis_match"] is True
        assert match["illumination_projection_coupling_status"] == "shared_basis_matched"
        assert cross["illumination_projection_coupling_status"] == "shared_basis_cross_suppressed"
        assert cross["illumination_polarization_amplitude_factor"] == pytest.approx(0.05)
        assert cross["A_env_scalar"][0] == pytest.approx(match["A_env_scalar"][0])
        assert cross["A_env"][0] == pytest.approx(
            match["A_env"][0] * cfg_cross.cross_polarization_leakage,
            rel=1e-9,
        )

    def test_overfill_mode_flattens_cross_section_but_preserves_flow_window(self):
        optical = BASELINE_OPTICAL
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            illumination_mode="overfill",
            scattering_projection_mode="parallel",
            illumination_polarization_mode="match_scattering",
        )
        x = np.array([-optical.beam_waist_x_m, 0.0, optical.beam_waist_x_m])
        y = np.array([
            optical.focus_y_m - 3e-6,
            optical.focus_y_m,
            optical.focus_y_m + 3e-6,
        ])
        z = np.array([-optical.beam_waist_z_m, 0.0, optical.beam_waist_z_m])
        result = compute_illumination_envelope(
            x,
            y,
            z,
            optical,
            medium_refractive_index=WATER.refractive_index,
            sim_cfg=cfg,
        )
        assert result["A_env_scalar"][1] == pytest.approx(1.0, abs=1e-12)
        assert result["A_env_scalar"][0] < result["A_env_scalar"][1]
        assert result["A_env_scalar"][2] < result["A_env_scalar"][1]
        assert result["A_env_scalar"][0] == pytest.approx(
            result["A_env_scalar"][2],
            rel=1e-12,
            abs=1e-12,
        )
        np.testing.assert_allclose(
            result["I_inc_scalar_W_m2"],
            optical.peak_irradiance_W_m2 * result["A_env_scalar"] ** 2,
            atol=1e-12,
        )
        np.testing.assert_allclose(result["A_env"], result["A_env_scalar"], atol=1e-12)
        np.testing.assert_allclose(
            result["I_inc_W_m2"],
            optical.peak_irradiance_W_m2 * result["A_env"] ** 2,
            atol=1e-12,
        )

    def test_overfill_mode_keeps_finite_transit_window_for_bandwidth_estimation(self):
        optical = BASELINE_OPTICAL
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            illumination_mode="overfill",
            scattering_projection_mode="parallel",
            illumination_polarization_mode="match_scattering",
        )
        geometry = optical.resolve_illumination_geometry()
        wy = float(geometry["illumination_beam_waist_y_m"])
        time_s = np.linspace(-0.03, 0.03, 4001)
        y = optical.focus_y_m + cfg.mean_flow_velocity_m_s * time_s
        result = compute_illumination_envelope(
            np.zeros_like(y),
            y,
            np.zeros_like(y),
            optical,
            medium_refractive_index=WATER.refractive_index,
            sim_cfg=cfg,
        )
        transit_time_s = _estimate_transit_time_s(time_s, result["A_env_scalar"])
        expected_transit_time_s = 2.0 * wy / cfg.mean_flow_velocity_m_s

        assert transit_time_s == pytest.approx(expected_transit_time_s, rel=0.05)
        assert transit_time_s < 0.03
        assert result["I_inc_W_m2"].max() == pytest.approx(
            optical.peak_irradiance_W_m2,
            abs=1e-12,
        )


class TestTrajectory:
    def test_pure_advection_trajectory_keeps_transverse_position_and_crosses_focus(self):
        cfg = SimulationConfig(0.2, 20000.0, 2e-4)
        traj = simulate_particle_trajectory(
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            1e-7,
            -1e-7,
        )
        np.testing.assert_array_equal(traj["x_m"], 1e-7)
        np.testing.assert_array_equal(traj["z_m"], -1e-7)
        np.testing.assert_allclose(
            np.diff(traj["y_m"]),
            cfg.mean_flow_velocity_m_s * cfg.dt_s,
            rtol=1e-10,
        )
        assert traj["y_m"].min() < BASELINE_OPTICAL.focus_y_m
        assert traj["y_m"].max() > BASELINE_OPTICAL.focus_y_m
        assert len(traj["time_s"]) == cfg.n_samples

    def test_invalid_initial_position(self):
        cfg = SimulationConfig(0.2, 20000.0, 2e-4)
        with pytest.raises(ValueError, match="initial_x"):
            simulate_particle_trajectory(BASELINE_CHANNEL, BASELINE_OPTICAL, cfg, 1e-3, 0.0)

    def test_diffusion_changes_xz_but_keeps_y_advective(self):
        cfg = SimulationConfig(0.2, 20000.0, 2e-4, include_diffusion=True)
        traj = simulate_particle_trajectory(
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            0.0,
            0.0,
            diffusion_coefficient=1e-12,
            rng=np.random.default_rng(42),
        )
        assert np.std(traj["x_m"]) > 0
        assert np.std(traj["z_m"]) > 0
        np.testing.assert_allclose(np.diff(traj["y_m"]), cfg.mean_flow_velocity_m_s * cfg.dt_s, rtol=1e-10)

    def test_parabolic_rect_profile_slows_near_wall_streamlines(self):
        cfg = SimulationConfig(0.2, 20000.0, 2e-4, flow_profile_model="parabolic_rect")
        center_v = axial_velocity_m_s(0.0, 0.0, BASELINE_CHANNEL, cfg, particle_radius_m=20e-9)
        edge_v = axial_velocity_m_s(300e-9, 180e-9, BASELINE_CHANNEL, cfg, particle_radius_m=20e-9)
        assert center_v > cfg.mean_flow_velocity_m_s
        assert edge_v < center_v

    def test_rect_series_profile_slows_near_wall_streamlines(self):
        cfg = SimulationConfig(0.2, 20000.0, 2e-4, flow_profile_model="rect_series")
        center_v = axial_velocity_m_s(0.0, 0.0, BASELINE_CHANNEL, cfg, particle_radius_m=20e-9)
        edge_v = axial_velocity_m_s(300e-9, 180e-9, BASELINE_CHANNEL, cfg, particle_radius_m=20e-9)
        assert center_v > cfg.mean_flow_velocity_m_s
        assert edge_v < center_v

    def test_parabolic_rect_diffusion_makes_y_velocity_time_varying(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            include_diffusion=True,
            flow_profile_model="parabolic_rect",
        )
        traj = simulate_particle_trajectory(
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            250e-9,
            120e-9,
            particle_radius_m=20e-9,
            diffusion_coefficient=1e-12,
            rng=np.random.default_rng(7),
        )
        assert np.std(traj["v_y_m_s"]) > 0

    def test_hindered_diffusion_factors_drop_near_wall(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            include_diffusion=True,
            diffusion_hindrance_model="near_wall_surrogate",
        )
        center_fx, center_fz = hindered_diffusion_factors(
            0.0,
            0.0,
            BASELINE_CHANNEL,
            20e-9,
            cfg,
        )
        wall_fx, wall_fz = hindered_diffusion_factors(
            340e-9,
            200e-9,
            BASELINE_CHANNEL,
            20e-9,
            cfg,
        )
        assert center_fx == pytest.approx(1.0)
        assert center_fz == pytest.approx(1.0)
        assert wall_fx < center_fx
        assert wall_fz < wall_fx

    def test_hindered_diffusion_factors_strengthen_with_particle_radius(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            include_diffusion=True,
            diffusion_hindrance_model="near_wall_surrogate",
        )
        small_fx, small_fz = hindered_diffusion_factors(
            0.0,
            200e-9,
            BASELINE_CHANNEL,
            20e-9,
            cfg,
        )
        large_fx, large_fz = hindered_diffusion_factors(
            0.0,
            170e-9,
            BASELINE_CHANNEL,
            50e-9,
            cfg,
        )
        assert large_fx < small_fx
        assert large_fz < small_fz

    def test_anisotropic_tensor_surrogate_is_directional(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            include_diffusion=True,
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
        )
        wall_fx, wall_fz = hindered_diffusion_factors(
            0.0,
            200e-9,
            BASELINE_CHANNEL,
            20e-9,
            cfg,
        )
        assert wall_fz < wall_fx

    def test_anisotropic_tensor_surrogate_is_stronger_than_soft_near_wall_blend(self):
        soft_cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            include_diffusion=True,
            diffusion_hindrance_model="near_wall_surrogate",
        )
        tensor_cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            include_diffusion=True,
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
        )
        soft_fx, soft_fz = hindered_diffusion_factors(
            0.0,
            200e-9,
            BASELINE_CHANNEL,
            20e-9,
            soft_cfg,
        )
        tensor_fx, tensor_fz = hindered_diffusion_factors(
            0.0,
            200e-9,
            BASELINE_CHANNEL,
            20e-9,
            tensor_cfg,
        )
        assert tensor_fx < soft_fx
        assert tensor_fz < soft_fz

    def test_hindered_diffusion_scalar_matches_array_path(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            include_diffusion=True,
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
        )
        scalar_fx, scalar_fz = hindered_diffusion_factors(
            300e-9,
            180e-9,
            BASELINE_CHANNEL,
            20e-9,
            cfg,
        )
        array_fx, array_fz = hindered_diffusion_factors(
            np.array([300e-9]),
            np.array([180e-9]),
            BASELINE_CHANNEL,
            20e-9,
            cfg,
        )
        assert scalar_fx == pytest.approx(float(array_fx[0]), rel=1e-12, abs=1e-15)
        assert scalar_fz == pytest.approx(float(array_fz[0]), rel=1e-12, abs=1e-15)

    def test_axial_transport_velocity_adds_near_wall_drag_in_tensor_mode(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
        )
        base = axial_velocity_m_s(300e-9, 180e-9, BASELINE_CHANNEL, cfg, particle_radius_m=20e-9)
        dragged = axial_transport_velocity_m_s(300e-9, 180e-9, BASELINE_CHANNEL, cfg, particle_radius_m=20e-9)
        assert dragged < base

    def test_axial_transport_scalar_matches_array_path(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
        )
        scalar_velocity = axial_transport_velocity_m_s(
            300e-9,
            180e-9,
            BASELINE_CHANNEL,
            cfg,
            particle_radius_m=20e-9,
        )
        array_velocity = axial_transport_velocity_m_s(
            np.array([300e-9]),
            np.array([180e-9]),
            BASELINE_CHANNEL,
            cfg,
            particle_radius_m=20e-9,
        )
        assert scalar_velocity == pytest.approx(float(array_velocity[0]), rel=1e-12, abs=1e-15)

    def test_diffusive_rect_series_tensor_trajectory_matches_reference_loop(self):
        cfg = SimulationConfig(
            total_time_s=0.01,
            sampling_rate_Hz=1000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
        )
        radius_m = 20e-9
        diffusion_coefficient = 1e-12
        initial_x_m = 250e-9
        initial_z_m = 120e-9

        trajectory = simulate_particle_trajectory(
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            initial_x_m,
            initial_z_m,
            particle_radius_m=radius_m,
            diffusion_coefficient=diffusion_coefficient,
            rng=np.random.default_rng(42),
        )

        def _reflect_reference(value: float, lo: float, hi: float) -> float:
            while value < lo or value > hi:
                if value < lo:
                    value = 2.0 * lo - value
                if value > hi:
                    value = 2.0 * hi - value
            return value

        half_w = BASELINE_CHANNEL.width_m / 2.0 - radius_m
        half_h = BASELINE_CHANNEL.depth_m / 2.0 - radius_m
        time_s = np.arange(cfg.n_samples) * cfg.dt_s
        x_ref = np.empty(cfg.n_samples)
        z_ref = np.empty(cfg.n_samples)
        y_ref = np.empty(cfg.n_samples)
        v_ref = np.empty(cfg.n_samples)
        x_ref[0] = initial_x_m
        z_ref[0] = initial_z_m
        v_ref[0] = float(
            axial_transport_velocity_m_s(
                initial_x_m,
                initial_z_m,
                BASELINE_CHANNEL,
                cfg,
                particle_radius_m=radius_m,
            )
        )
        y_ref[0] = BASELINE_OPTICAL.focus_y_m - v_ref[0] * cfg.total_time_s / 2.0
        diffusion_step_scale = np.sqrt(2.0 * diffusion_coefficient * cfg.dt_s)
        rng = np.random.default_rng(42)

        for idx in range(cfg.n_samples - 1):
            fx, fz = hindered_diffusion_factors(
                x_ref[idx],
                z_ref[idx],
                BASELINE_CHANNEL,
                radius_m,
                cfg,
            )
            dx = diffusion_step_scale * np.sqrt(float(fx)) * float(rng.standard_normal())
            dz = diffusion_step_scale * np.sqrt(float(fz)) * float(rng.standard_normal())
            x_new = _reflect_reference(x_ref[idx] + dx, -half_w, half_w)
            z_new = _reflect_reference(z_ref[idx] + dz, -half_h, half_h)
            x_ref[idx + 1] = x_new
            z_ref[idx + 1] = z_new
            y_ref[idx + 1] = y_ref[idx] + v_ref[idx] * cfg.dt_s
            v_ref[idx + 1] = float(
                axial_transport_velocity_m_s(
                    x_new,
                    z_new,
                    BASELINE_CHANNEL,
                    cfg,
                    particle_radius_m=radius_m,
                )
            )

        np.testing.assert_allclose(trajectory["time_s"], time_s, rtol=0.0, atol=0.0)
        np.testing.assert_allclose(trajectory["x_m"], x_ref, rtol=0.0, atol=1e-15)
        np.testing.assert_allclose(trajectory["z_m"], z_ref, rtol=0.0, atol=1e-15)
        np.testing.assert_allclose(trajectory["y_m"], y_ref, rtol=0.0, atol=1e-15)
        np.testing.assert_allclose(trajectory["v_y_m_s"], v_ref, rtol=0.0, atol=1e-15)

    def test_trajectory_context_preserves_diffusive_rect_series_outputs(self):
        cfg = SimulationConfig(
            total_time_s=0.01,
            sampling_rate_Hz=1000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
        )
        radius_m = 20e-9
        context = build_trajectory_context(
            BASELINE_CHANNEL,
            cfg,
            particle_radius_m=radius_m,
        )
        uncached = simulate_particle_trajectory(
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            250e-9,
            120e-9,
            particle_radius_m=radius_m,
            diffusion_coefficient=1e-12,
            rng=np.random.default_rng(42),
        )
        cached = simulate_particle_trajectory(
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            250e-9,
            120e-9,
            particle_radius_m=radius_m,
            diffusion_coefficient=1e-12,
            rng=np.random.default_rng(42),
            trajectory_context=context,
        )

        for key in ("time_s", "x_m", "y_m", "z_m", "v_y_m_s"):
            np.testing.assert_array_equal(cached[key], uncached[key])


class TestScatteringTrace:
    def test_zero_envelope_gives_zero_field(self):
        traj = {"time_s": np.arange(100) * 5e-5, "x_m": np.zeros(100), "y_m": np.zeros(100), "z_m": np.zeros(100)}
        illum = {"A_env": np.zeros(100), "I_inc_W_m2": np.zeros(100)}
        result = compute_scattering_field_trace(traj, 1.0, BASELINE_OPTICAL, illum, BASELINE_CHANNEL, 0.0, 0.0, "constant")
        np.testing.assert_array_equal(result["E_sca_complex"], 0)

    def test_amplitude_proportional(self):
        traj = {"time_s": np.arange(100) * 5e-5, "x_m": np.zeros(100), "y_m": np.zeros(100), "z_m": np.zeros(100)}
        illum1 = {"A_env": np.ones(100) * 0.5, "I_inc_W_m2": np.ones(100)}
        illum2 = {"A_env": np.ones(100) * 1.0, "I_inc_W_m2": np.ones(100)}
        r1 = compute_scattering_field_trace(traj, 1.0, BASELINE_OPTICAL, illum1, BASELINE_CHANNEL, 0.0, 0.0)
        r2 = compute_scattering_field_trace(traj, 1.0, BASELINE_OPTICAL, illum2, BASELINE_CHANNEL, 0.0, 0.0)
        np.testing.assert_allclose(np.abs(r1["E_sca_complex"]) * 2, np.abs(r2["E_sca_complex"]), rtol=1e-12)

    def test_constant_phase(self):
        traj = {"time_s": np.arange(100) * 5e-5, "x_m": np.zeros(100), "y_m": np.zeros(100), "z_m": np.zeros(100)}
        illum = {"A_env": np.ones(100), "I_inc_W_m2": np.ones(100)}
        result = compute_scattering_field_trace(
            traj, 1.0, BASELINE_OPTICAL, illum, BASELINE_CHANNEL, 0.0, 0.0,
            phase_model="constant",
        )
        np.testing.assert_array_equal(result["phi_sca_rad"], 0)

    def test_axial_path_phase_changes_with_depth(self):
        traj = {
            "time_s": np.arange(3) * 5e-5,
            "x_m": np.zeros(3),
            "y_m": np.zeros(3),
            "z_m": np.array([-100e-9, 0.0, 100e-9]),
        }
        illum = {"A_env": np.ones(3), "I_inc_W_m2": np.ones(3)}
        result = compute_scattering_field_trace(
            traj,
            1.0,
            BASELINE_OPTICAL,
            illum,
            BASELINE_CHANNEL,
            0.0,
            0.0,
            phase_model="axial_path",
            detection_theta_rad=np.pi / 4,
            medium_refractive_index=WATER.refractive_index,
        )
        assert result["phi_sca_rad"][0] < result["phi_sca_rad"][1] < result["phi_sca_rad"][2]

    def test_relative_surrogate_phase_changes_with_y_and_tracks_reference_phase(self):
        traj = {
            "time_s": np.arange(3) * 5e-5,
            "x_m": np.zeros(3),
            "y_m": np.array([-800e-9, 0.0, 800e-9]),
            "z_m": np.zeros(3),
        }
        illum = {"A_env": np.ones(3), "I_inc_W_m2": np.ones(3)}
        result = compute_scattering_field_trace(
            traj,
            1.0,
            BASELINE_OPTICAL,
            illum,
            BASELINE_CHANNEL,
            0.0,
            0.0,
            phase_model="relative_surrogate",
            detection_theta_rad=np.pi / 4,
            medium_refractive_index=WATER.refractive_index,
            reference_phase_rad=0.4,
        )
        assert result["phi_sca_rad"][0] < result["phi_sca_rad"][1] < result["phi_sca_rad"][2]
        np.testing.assert_allclose(
            result["delta_phi_ref_rad"],
            ((result["phi_sca_rad"] - 0.4 + np.pi) % (2.0 * np.pi)) - np.pi,
            atol=1e-12,
        )
        np.testing.assert_allclose(result["phi_sca_path_x_rad"], 0.0, atol=1e-12)
        np.testing.assert_allclose(result["phi_sca_path_z_rad"], 0.0, atol=1e-12)
        np.testing.assert_allclose(result["phi_gouy_ref_rad"], 0.0, atol=1e-12)
        np.testing.assert_allclose(result["phi_gouy_sca_rad"], result["delta_phi_gouy_rad"], atol=1e-12)
        assert result["gouy_dedup_active"] is True
        assert result["phi_gouy_reference_status"] == "inactive_not_carried_by_reference_trace"
        assert result["phi_gouy_scattering_status"] == "active_focus_crossing_only_deduplicated"
        assert result["phi_gouy_semantics_status"] == "active_interference_contribution_fields"

    def test_relative_surrogate_phase_includes_x_path_projection(self):
        traj = {
            "time_s": np.arange(3) * 5e-5,
            "x_m": np.array([-100e-9, 0.0, 100e-9]),
            "y_m": np.zeros(3),
            "z_m": np.zeros(3),
        }
        illum = {"A_env": np.ones(3), "I_inc_W_m2": np.ones(3)}
        result = compute_scattering_field_trace(
            traj,
            1.0,
            BASELINE_OPTICAL,
            illum,
            BASELINE_CHANNEL,
            0.0,
            0.0,
            phase_model="relative_surrogate",
            detection_theta_rad=np.pi / 4,
            medium_refractive_index=WATER.refractive_index,
        )
        assert result["phi_sca_path_x_rad"][0] < result["phi_sca_path_x_rad"][1] < result["phi_sca_path_x_rad"][2]
        np.testing.assert_allclose(result["phi_sca_path_z_rad"], 0.0, atol=1e-12)
        np.testing.assert_allclose(result["phi_sca_path_rad"], result["phi_sca_path_x_rad"], atol=1e-12)

    def test_relative_surrogate_roundtrip_opd_doubles_only_z_path(self):
        traj = {
            "time_s": np.arange(3) * 5e-5,
            "x_m": np.array([-100e-9, 0.0, 100e-9]),
            "y_m": np.zeros(3),
            "z_m": np.array([-50e-9, 0.0, 50e-9]),
        }
        illum = {"A_env": np.ones(3), "I_inc_W_m2": np.ones(3)}
        single = compute_scattering_field_trace(
            traj,
            1.0,
            BASELINE_OPTICAL,
            illum,
            BASELINE_CHANNEL,
            0.0,
            0.0,
            phase_model="relative_surrogate",
            path_opd_model="single_pass",
            detection_theta_rad=np.pi / 4,
            medium_refractive_index=WATER.refractive_index,
        )
        roundtrip = compute_scattering_field_trace(
            traj,
            1.0,
            BASELINE_OPTICAL,
            illum,
            BASELINE_CHANNEL,
            0.0,
            0.0,
            phase_model="relative_surrogate",
            path_opd_model="reference_plane_roundtrip_surrogate",
            detection_theta_rad=np.pi / 4,
            medium_refractive_index=WATER.refractive_index,
        )
        np.testing.assert_allclose(roundtrip["phi_sca_path_x_rad"], single["phi_sca_path_x_rad"], atol=1e-12)
        np.testing.assert_allclose(roundtrip["phi_sca_path_z_rad"], 2.0 * single["phi_sca_path_z_rad"], atol=1e-12)
        assert single["path_opd_default_model"] == "single_pass"
        assert single["path_opd_model_role"] == "default_frozen_mainline"
        assert single["path_opd_default_frozen"] is True
        assert single["path_opd_freeze_status"] == "default_frozen_active"
        assert roundtrip["path_opd_model"] == "reference_plane_roundtrip_surrogate"
        assert roundtrip["path_opd_reference_plane"] == "channel_center_reference_plane_roundtrip_surrogate"
        assert roundtrip["path_opd_z_geometry_factor"] == pytest.approx(2.0)
        assert roundtrip["path_opd_default_model"] == "single_pass"
        assert roundtrip["path_opd_model_role"] == "diagnostic_review_alternative"
        assert roundtrip["path_opd_default_frozen"] is False
        assert roundtrip["path_opd_freeze_status"] == "alternative_review_mode"

    def test_relative_surrogate_wall_referenced_opd_centers_nearest_wall_gap(self):
        traj = {
            "time_s": np.arange(3) * 5e-5,
            "x_m": np.array([-100e-9, 0.0, 100e-9]),
            "y_m": np.array([-50e-9, 0.0, 50e-9]),
            "z_m": np.array([-50e-9, 0.0, 50e-9]),
        }
        illum = {"A_env": np.ones(3), "I_inc_W_m2": np.ones(3)}
        wall_ref = compute_scattering_field_trace(
            traj,
            1.0,
            BASELINE_OPTICAL,
            illum,
            BASELINE_CHANNEL,
            0.0,
            0.0,
            phase_model="relative_surrogate",
            path_opd_model="wall_referenced_gap_surrogate",
            detection_theta_rad=np.pi / 4,
            medium_refractive_index=WATER.refractive_index,
        )
        single = compute_scattering_field_trace(
            traj,
            1.0,
            BASELINE_OPTICAL,
            illum,
            BASELINE_CHANNEL,
            0.0,
            0.0,
            phase_model="relative_surrogate",
            path_opd_model="single_pass",
            detection_theta_rad=np.pi / 4,
            medium_refractive_index=WATER.refractive_index,
        )
        np.testing.assert_allclose(
            wall_ref["phi_sca_path_x_rad"],
            single["phi_sca_path_x_rad"],
            atol=1e-12,
        )
        assert wall_ref["phi_sca_path_z_rad"][1] == pytest.approx(0.0, abs=1e-12)
        assert wall_ref["phi_sca_path_z_rad"][0] == pytest.approx(
            wall_ref["phi_sca_path_z_rad"][2],
            abs=1e-12,
        )
        assert wall_ref["phi_sca_path_z_rad"][0] < 0.0
        np.testing.assert_allclose(
            wall_ref["phi_focus_crossing_rad"],
            wall_ref["delta_phi_gouy_rad"],
            atol=1e-12,
        )
        np.testing.assert_allclose(
            wall_ref["phi_gouy_sca_rad"] - wall_ref["phi_gouy_ref_rad"],
            wall_ref["delta_phi_gouy_rad"],
            atol=1e-12,
        )
        assert wall_ref["path_opd_model"] == "wall_referenced_gap_surrogate"
        assert (
            wall_ref["path_opd_reference_plane"]
            == "nearest_channel_wall_centered_gap_surrogate"
        )
        assert (
            wall_ref["path_opd_z_reference_mode"]
            == "nearest_wall_gap_centered_about_channel_midplane"
        )
        assert wall_ref["path_opd_default_model"] == "single_pass"
        assert wall_ref["path_opd_model_role"] == "diagnostic_review_alternative"
        assert wall_ref["path_opd_default_frozen"] is False
        assert wall_ref["path_opd_freeze_status"] == "alternative_review_mode"

    def test_relative_surrogate_gouy_dedup_ignores_illumination_beam_gouy_phase(self):
        optical = replace(BASELINE_OPTICAL)
        traj = {
            "time_s": np.arange(5) * 5e-5,
            "x_m": np.full(5, 250e-9),
            "y_m": optical.focus_y_m + np.array([-2.0e-6, -1.0e-6, 0.0, 1.0e-6, 2.0e-6]),
            "z_m": np.zeros(5),
        }
        illumination = compute_illumination_envelope(
            traj["x_m"],
            traj["y_m"],
            traj["z_m"],
            optical,
            medium_refractive_index=WATER.refractive_index,
        )
        gouy_offset = np.linspace(-0.4, 0.4, len(traj["time_s"]))
        illumination_shifted = dict(illumination)
        illumination_shifted["phi_beam_rad"] = illumination["phi_beam_rad"] + gouy_offset
        illumination_shifted["phi_beam_gouy_rad"] = illumination["phi_beam_gouy_rad"] + gouy_offset
        illumination_shifted["E_env_complex"] = illumination["A_env"] * np.exp(
            1j * illumination_shifted["phi_beam_rad"]
        )

        baseline = compute_scattering_field_trace(
            traj,
            1.0,
            optical,
            illumination,
            BASELINE_CHANNEL,
            float(traj["x_m"][0]),
            0.0,
            phase_model="relative_surrogate",
            detection_theta_rad=0.0,
            medium_refractive_index=WATER.refractive_index,
        )
        shifted = compute_scattering_field_trace(
            traj,
            1.0,
            optical,
            illumination_shifted,
            BASELINE_CHANNEL,
            float(traj["x_m"][0]),
            0.0,
            phase_model="relative_surrogate",
            detection_theta_rad=0.0,
            medium_refractive_index=WATER.refractive_index,
        )

        np.testing.assert_allclose(
            shifted["E_sca_complex"],
            baseline["E_sca_complex"],
            atol=1e-12,
            rtol=1e-12,
        )
        np.testing.assert_allclose(
            shifted["phi_gouy_sca_rad"],
            baseline["phi_gouy_sca_rad"],
            atol=1e-12,
        )
        assert baseline["gouy_dedup_active"] is True
        assert shifted["gouy_dedup_active"] is True

    def test_relative_surrogate_can_reuse_matching_illumination_gouy_phase(self):
        optical = replace(BASELINE_OPTICAL)
        traj = {
            "time_s": np.arange(5) * 5e-5,
            "x_m": np.full(5, 250e-9),
            "y_m": optical.focus_y_m + np.array([-2.0e-6, -1.0e-6, 0.0, 1.0e-6, 2.0e-6]),
            "z_m": np.zeros(5),
        }
        illumination = compute_illumination_envelope(
            traj["x_m"],
            traj["y_m"],
            traj["z_m"],
            optical,
            medium_refractive_index=WATER.refractive_index,
        )

        computed = compute_scattering_field_trace(
            traj,
            1.0,
            optical,
            illumination,
            BASELINE_CHANNEL,
            float(traj["x_m"][0]),
            0.0,
            phase_model="relative_surrogate",
            detection_theta_rad=0.0,
            medium_refractive_index=WATER.refractive_index,
            include_phase_diagnostics=False,
            export_complex_field=False,
        )
        reused = compute_scattering_field_trace(
            traj,
            1.0,
            optical,
            illumination,
            BASELINE_CHANNEL,
            float(traj["x_m"][0]),
            0.0,
            phase_model="relative_surrogate",
            detection_theta_rad=0.0,
            medium_refractive_index=WATER.refractive_index,
            include_phase_diagnostics=False,
            export_complex_field=False,
            reuse_illumination_gouy_phase=True,
        )

        np.testing.assert_allclose(reused["A_sca"], computed["A_sca"], rtol=0.0, atol=0.0)
        np.testing.assert_allclose(
            reused["phi_sca_unwrapped_rad"],
            computed["phi_sca_unwrapped_rad"],
            rtol=0.0,
            atol=0.0,
        )

    def test_axial_path_keeps_full_beam_phase_when_gouy_dedup_is_inactive(self):
        optical = replace(BASELINE_OPTICAL)
        traj = {
            "time_s": np.arange(5) * 5e-5,
            "x_m": np.full(5, 250e-9),
            "y_m": optical.focus_y_m + np.array([-2.0e-6, -1.0e-6, 0.0, 1.0e-6, 2.0e-6]),
            "z_m": np.zeros(5),
        }
        illumination = compute_illumination_envelope(
            traj["x_m"],
            traj["y_m"],
            traj["z_m"],
            optical,
            medium_refractive_index=WATER.refractive_index,
        )
        gouy_offset = np.linspace(-0.4, 0.4, len(traj["time_s"]))
        illumination_shifted = dict(illumination)
        illumination_shifted["phi_beam_rad"] = illumination["phi_beam_rad"] + gouy_offset
        illumination_shifted["phi_beam_gouy_rad"] = illumination["phi_beam_gouy_rad"] + gouy_offset
        illumination_shifted["E_env_complex"] = illumination["A_env"] * np.exp(
            1j * illumination_shifted["phi_beam_rad"]
        )

        baseline = compute_scattering_field_trace(
            traj,
            1.0,
            optical,
            illumination,
            BASELINE_CHANNEL,
            float(traj["x_m"][0]),
            0.0,
            phase_model="axial_path",
            detection_theta_rad=0.0,
            medium_refractive_index=WATER.refractive_index,
        )
        shifted = compute_scattering_field_trace(
            traj,
            1.0,
            optical,
            illumination_shifted,
            BASELINE_CHANNEL,
            float(traj["x_m"][0]),
            0.0,
            phase_model="axial_path",
            detection_theta_rad=0.0,
            medium_refractive_index=WATER.refractive_index,
        )

        assert baseline["gouy_dedup_active"] is False
        assert shifted["gouy_dedup_active"] is False
        assert not np.allclose(shifted["E_sca_complex"], baseline["E_sca_complex"])
        assert shifted["phi_gouy_scattering_status"] == "active_beam_gouy_component"

    def test_gaussian_coupling_follows_trajectory_positions(self):
        traj = {
            "time_s": np.arange(3) * 5e-5,
            "x_m": np.array([0.0, BASELINE_CHANNEL.width_m / 4, BASELINE_CHANNEL.width_m / 2]),
            "y_m": np.zeros(3),
            "z_m": np.zeros(3),
        }
        illum = {"A_env": np.ones(3), "I_inc_W_m2": np.ones(3)}
        result = compute_scattering_field_trace(
            traj,
            1.0,
            BASELINE_OPTICAL,
            illum,
            BASELINE_CHANNEL,
            0.0,
            0.0,
            coupling_model="gaussian_xy",
        )
        assert result["f_coupling"][0] > result["f_coupling"][1] > result["f_coupling"][2]

    def test_beam_phase_enters_total_scattering_phase(self):
        traj = {
            "time_s": np.arange(3) * 5e-5,
            "x_m": np.zeros(3),
            "y_m": np.zeros(3),
            "z_m": np.zeros(3),
        }
        illum = {
            "A_env": np.ones(3),
            "I_inc_W_m2": np.ones(3),
            "phi_beam_rad": np.array([0.0, 0.2, 0.4]),
            "E_env_complex": np.exp(1j * np.array([0.0, 0.2, 0.4])),
        }
        result = compute_scattering_field_trace(
            traj,
            1.0,
            BASELINE_OPTICAL,
            illum,
            BASELINE_CHANNEL,
            0.0,
            0.0,
        )
        np.testing.assert_allclose(result["phi_beam_rad"], np.array([0.0, 0.2, 0.4]), atol=1e-12)
        np.testing.assert_allclose(result["phi_sca_rad"], np.array([0.0, 0.2, 0.4]), atol=1e-12)

    def test_scattering_trace_exposes_material_and_projection_phase_separately(self):
        traj = {
            "time_s": np.arange(3) * 5e-5,
            "x_m": np.zeros(3),
            "y_m": np.zeros(3),
            "z_m": np.zeros(3),
        }
        illum = {
            "A_env": np.ones(3),
            "I_inc_W_m2": np.ones(3),
            "E_env_complex": np.exp(1j * np.array([0.1, 0.1, 0.1])),
        }
        result = compute_scattering_field_trace(
            traj,
            np.exp(1j * 0.6),
            BASELINE_OPTICAL,
            illum,
            BASELINE_CHANNEL,
            0.0,
            0.0,
            reference_phase_rad=0.2,
            scattering_phase_diagnostics={
                "phi_sca_material_rad": 0.3,
                "phi_sca_material_parallel_rad": 0.3,
                "phi_sca_material_perpendicular_rad": -0.4,
                "phi_projection_rad": 0.6,
            },
        )
        np.testing.assert_allclose(result["phi_material_rad"], np.full(3, 0.3), atol=1e-12)
        np.testing.assert_allclose(result["phi_projection_rad"], np.full(3, 0.6), atol=1e-12)
        np.testing.assert_allclose(
            result["phi_material_perpendicular_rad"],
            np.full(3, -0.4),
            atol=1e-12,
        )

    def test_light_scattering_trace_can_skip_complex_field(self):
        traj = {
            "time_s": np.arange(3) * 5e-5,
            "x_m": np.zeros(3),
            "y_m": np.array([-1e-6, 0.0, 1e-6]),
            "z_m": np.zeros(3),
        }
        illum = {
            "A_env": np.array([0.5, 1.0, 0.7]),
            "phi_beam_rad": np.array([0.0, 0.2, 0.4]),
            "phi_beam_gouy_rad": np.zeros(3),
            "phi_beam_curv_rad": np.array([0.0, 0.2, 0.4]),
        }

        full = compute_scattering_field_trace(
            traj,
            np.exp(1j * 0.6),
            BASELINE_OPTICAL,
            illum,
            BASELINE_CHANNEL,
            0.0,
            0.0,
            reference_phase_rad=0.2,
            include_phase_diagnostics=False,
        )
        light = compute_scattering_field_trace(
            traj,
            np.exp(1j * 0.6),
            BASELINE_OPTICAL,
            illum,
            BASELINE_CHANNEL,
            0.0,
            0.0,
            reference_phase_rad=0.2,
            include_phase_diagnostics=False,
            export_complex_field=False,
        )

        np.testing.assert_allclose(light["A_sca"], full["A_sca"])
        np.testing.assert_allclose(
            light["phi_sca_unwrapped_rad"],
            np.angle(full["E_sca_complex"]),
        )
        assert "E_sca_complex" not in light


class TestInterferometricTrace:
    def _make_inputs(self, e_ref_val, e_sca_arr):
        traj = {"time_s": np.arange(len(e_sca_arr)) * 5e-5}
        ref = {"E_ref_complex": complex(e_ref_val), "A_ref": abs(e_ref_val), "phi_ref_rad": 0.0}
        sca = {"E_sca_complex": e_sca_arr, "A_sca": np.abs(e_sca_arr), "phi_sca_rad": np.zeros(len(e_sca_arr))}
        cfg = SimulationConfig(len(e_sca_arr) * 5e-5, 20000.0, 2e-4)
        return traj, ref, sca, cfg

    def test_zero_scattering(self):
        traj, ref, sca, cfg = self._make_inputs(10.0, np.zeros(100, dtype=complex))
        result = generate_interferometric_trace(traj, ref, sca, cfg)
        np.testing.assert_allclose(result["signal_trace"], 0, atol=1e-12)

    def test_zero_reference(self):
        e_sca = np.array([0.1 + 0.2j, 0.3 + 0.0j, 0.0 + 0.0j])
        traj, ref, sca, cfg = self._make_inputs(0.0, e_sca)
        result = generate_interferometric_trace(traj, ref, sca, cfg)
        np.testing.assert_allclose(result["signal_trace"], np.abs(e_sca) ** 2, atol=1e-12)

    def test_signal_equals_idet_minus_baseline(self):
        e_sca = np.random.default_rng(0).standard_normal(100).astype(complex) * 0.1
        traj, ref, sca, cfg = self._make_inputs(10.0, e_sca)
        result = generate_interferometric_trace(traj, ref, sca, cfg)
        np.testing.assert_allclose(result["signal_trace"], result["I_det"] - result["I_baseline_trace"], atol=1e-12)

    def test_idet_nonnegative(self):
        e_sca = np.random.default_rng(1).standard_normal(100).astype(complex) * 0.5
        traj, ref, sca, cfg = self._make_inputs(10.0, e_sca)
        result = generate_interferometric_trace(traj, ref, sca, cfg)
        assert np.all(result["I_det"] >= -1e-12)

    def test_weak_scattering_approximation(self):
        e_ref = 10.0
        e_sca = np.ones(100, dtype=complex) * 0.001
        traj, ref, sca, cfg = self._make_inputs(e_ref, e_sca)
        result = generate_interferometric_trace(traj, ref, sca, cfg)
        expected = 2.0 * np.real(e_ref * np.conj(e_sca))
        np.testing.assert_allclose(result["signal_trace"], expected, rtol=0.01)

    def test_reference_interference_switch_disables_cross_term(self):
        e_ref = 10.0
        e_sca = np.ones(100, dtype=complex) * (0.1 + 0.05j)
        traj, ref, sca, cfg = self._make_inputs(e_ref, e_sca)
        cfg.reference_interference_on = False
        result = generate_interferometric_trace(traj, ref, sca, cfg)
        np.testing.assert_allclose(result["interference_cross_term"], 0.0, atol=1e-12)
        np.testing.assert_allclose(result["signal_trace"], np.abs(e_sca) ** 2, atol=1e-12)

    def test_background_subtraction_switch_returns_full_detector_intensity(self):
        e_sca = np.ones(100, dtype=complex) * 0.01
        traj, ref, sca, cfg = self._make_inputs(10.0, e_sca)
        cfg.background_subtraction_on = False
        result = generate_interferometric_trace(traj, ref, sca, cfg)
        np.testing.assert_allclose(result["signal_trace"], result["I_det"], atol=1e-12)

    def test_light_interferometric_trace_matches_selected_outputs(self):
        e_sca = np.array([0.05 + 0.02j, 0.01 + 0.03j, 0.04 - 0.01j])
        traj, ref, sca, cfg = self._make_inputs(10.0, e_sca)
        ref["interference_overlap_factor_complex"] = 0.3 + 0.4j
        ref["interference_overlap_status"] = "mismatch_auditable"

        full = generate_interferometric_trace(traj, ref, sca, cfg)
        light = generate_interferometric_trace(
            traj,
            ref,
            sca,
            cfg,
            export_full_diagnostics=False,
        )

        for key in (
            "I_det",
            "I_baseline_trace",
            "signal_trace",
            "interference_cross_term",
        ):
            np.testing.assert_allclose(light[key], full[key], atol=0.0)
        assert light["I_baseline"] == pytest.approx(full["I_baseline"])
        assert light["interference_cross_term_mode"] == full["interference_cross_term_mode"]
        assert light["interference_overlap_factor_abs"] == pytest.approx(
            full["interference_overlap_factor_abs"]
        )
        assert light["interference_overlap_status"] == "mismatch_auditable"
        assert "E_det_complex" not in light
        assert "I_det_joint_overlap" not in light

    def test_light_interferometric_trace_accepts_phase_only_fields(self):
        A_ref = np.array([9.0, 10.0, 8.0])
        phi_ref = np.array([0.1, -0.2, 0.3])
        A_sca = np.array([0.05, 0.03, 0.04])
        phi_sca = np.array([0.4, -0.5, 0.2])
        traj = {"time_s": np.arange(A_ref.size) * 5e-5}
        ref_full = {
            "E_ref_complex": 10.0 + 0.0j,
            "E_ref_trace_complex": A_ref * np.exp(1j * phi_ref),
            "A_ref_trace": A_ref,
            "phi_ref_trace_rad": phi_ref,
            "interference_overlap_factor_complex": 0.3 + 0.4j,
            "interference_overlap_status": "mismatch_auditable",
        }
        sca_full = {
            "E_sca_complex": A_sca * np.exp(1j * phi_sca),
            "A_sca": A_sca,
            "phi_sca_unwrapped_rad": phi_sca,
        }
        ref_light = {
            key: value
            for key, value in ref_full.items()
            if key != "E_ref_trace_complex"
        }
        sca_light = {
            key: value
            for key, value in sca_full.items()
            if key != "E_sca_complex"
        }
        cfg = SimulationConfig(A_ref.size * 5e-5, 20000.0, 2e-4)
        cfg.interference_overlap_mode = "joint_overlap_integrated"

        full = generate_interferometric_trace(traj, ref_full, sca_full, cfg)
        light = generate_interferometric_trace(
            traj,
            ref_light,
            sca_light,
            cfg,
            export_full_diagnostics=False,
        )

        for key in (
            "I_det",
            "I_baseline_trace",
            "signal_trace",
            "interference_cross_term",
        ):
            np.testing.assert_allclose(light[key], full[key], rtol=1e-14, atol=1e-14)
        assert light["I_baseline"] == pytest.approx(full["I_baseline"], abs=1e-14)
        assert light["interference_cross_term_mode"] == full["interference_cross_term_mode"]
        assert "E_det_complex" not in light

    def test_time_varying_reference_trace_uses_local_baseline(self):
        e_sca = np.ones(3, dtype=complex) * 0.05
        traj, ref, sca, cfg = self._make_inputs(10.0, e_sca)
        ref["E_ref_trace_complex"] = np.array([8.0 + 0.0j, 10.0 + 0.0j, 12.0 + 0.0j])
        result = generate_interferometric_trace(traj, ref, sca, cfg)
        expected_baseline = np.array([64.0, 100.0, 144.0])
        np.testing.assert_allclose(result["I_baseline_trace"], expected_baseline, atol=1e-12)
        np.testing.assert_allclose(result["signal_trace"], result["I_det"] - expected_baseline, atol=1e-12)

    def test_default_interference_overlap_mode_keeps_joint_cross_term_active(self):
        e_sca = np.ones(4, dtype=complex) * (0.05 + 0.02j)
        traj, ref, sca, cfg = self._make_inputs(10.0, e_sca)
        ref["interference_overlap_factor_complex"] = 0.3 + 0.4j
        ref["interference_overlap_status"] = "mismatch_auditable"
        result = generate_interferometric_trace(traj, ref, sca, cfg)
        expected_collapsed = 2.0 * np.real(ref["E_ref_complex"] * np.conj(e_sca))
        expected_joint = 2.0 * np.real(ref["interference_overlap_factor_complex"] * ref["E_ref_complex"] * np.conj(e_sca))
        np.testing.assert_allclose(result["interference_cross_term"], expected_joint, atol=1e-12)
        np.testing.assert_allclose(result["interference_cross_term_collapsed"], expected_collapsed, atol=1e-12)
        np.testing.assert_allclose(result["interference_cross_term_joint"], expected_joint, atol=1e-12)
        assert result["interference_cross_term_mode"] == "joint_overlap_integrated"
        assert result["interference_overlap_status"] == "mismatch_auditable"

    def test_joint_interference_overlap_mode_activates_joint_cross_term(self):
        e_sca = np.ones(4, dtype=complex) * (0.05 + 0.02j)
        traj, ref, sca, cfg = self._make_inputs(10.0, e_sca)
        cfg.interference_overlap_mode = "joint_overlap_integrated"
        ref["interference_overlap_factor_complex"] = 0.3 + 0.4j
        result = generate_interferometric_trace(traj, ref, sca, cfg)
        expected_joint = 2.0 * np.real(ref["interference_overlap_factor_complex"] * ref["E_ref_complex"] * np.conj(e_sca))
        np.testing.assert_allclose(result["interference_cross_term"], expected_joint, atol=1e-12)
        np.testing.assert_allclose(
            result["signal_trace"],
            result["scattering_only_intensity"] + expected_joint,
            atol=1e-12,
        )
        assert result["interference_cross_term_mode"] == "joint_overlap_integrated"
        assert result["interference_overlap_factor_abs"] == pytest.approx(abs(ref["interference_overlap_factor_complex"]))

    def test_joint_overlap_consistency_marks_scalar_field_as_surrogate(self):
        e_sca = np.ones(4, dtype=complex) * (0.05 + 0.02j)
        traj, ref, sca, cfg = self._make_inputs(10.0, e_sca)
        cfg.interference_overlap_mode = "joint_overlap_integrated"
        ref["interference_overlap_factor_complex"] = 0.3 + 0.4j
        result = generate_interferometric_trace(traj, ref, sca, cfg)
        np.testing.assert_allclose(
            result["I_det_collapsed_scalar_surrogate"],
            np.abs(result["E_det_complex_scalar_surrogate"]) ** 2,
            atol=1e-12,
        )
        assert result["E_det_complex_physical_status"] == (
            "scalar_surrogate_not_intensity_consistent_joint_overlap_selected"
        )
        np.testing.assert_allclose(
            result["I_det"],
            result["I_det_joint_overlap"],
            atol=1e-12,
        )
        assert not np.allclose(
            result["I_det_joint_overlap"],
            result["I_det_collapsed_scalar_surrogate"],
        )


class TestPulseAnalysis:
    def test_block_transit_time_matches_rowwise_estimator(self):
        time_s = np.linspace(0.0, 0.09, 10)
        envelopes = np.array(
            [
                [0.0, 0.1, 0.5, 0.9, 0.8, 0.2, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.0, 0.0, 0.0],
            ],
            dtype=float,
        )

        block = _estimate_transit_time_block(time_s, envelopes, level=0.5)
        expected = np.array(
            [_estimate_transit_time_s(time_s, row, level=0.5) for row in envelopes],
            dtype=float,
        )

        np.testing.assert_allclose(block, expected, rtol=0.0, atol=0.0)

    def test_single_gaussian_peak(self):
        t = np.arange(4000) * 5e-5
        signal = np.exp(-((t - 0.1) ** 2) / (2 * 0.002 ** 2)) * 0.5
        result = extract_pulse_features(t, signal, 0.01, 1e-3, 0.05)
        assert result["n_peaks"] == 1
        peak = result["peaks"][0]
        assert abs(peak["peak_time_s"] - 0.1) < 0.005
        assert peak["peak_height"] == pytest.approx(0.5, rel=0.1)

    def test_below_threshold(self):
        t = np.arange(4000) * 5e-5
        signal = np.ones(4000) * 0.001
        result = extract_pulse_features(t, signal, 0.01, 1e-3, 0.05)
        assert result["n_peaks"] == 0

    def test_empty_pulse_features_matches_extraction_guard_payload(self):
        t = np.arange(200) * 5e-5
        signal = np.zeros(200)
        direct = extract_pulse_features(
            t,
            signal,
            0.01,
            1e-3,
            0.05,
            detection_mode="absolute",
        )
        fast = _empty_pulse_features(0.01, "absolute")

        assert fast == direct

    def test_block_peak_summary_selects_best_peak_and_preserves_signed_height(self):
        t = np.arange(7, dtype=float) * 0.1
        context = build_pulse_extraction_context(t, 0.05, 0.1)
        signals = np.array(
            [
                [0.0, 1.0, 3.0, 1.0, 0.0, 2.0, 0.0],
                [0.0, -1.0, -4.0, -1.0, 0.0, 2.0, 0.0],
                [0.0, 0.1, 0.2, 0.1, 0.0, 0.2, 0.0],
            ],
            dtype=float,
        )

        positive = _extract_best_peak_summary_block(
            t,
            signals,
            np.array([0.5, 0.5, 0.5]),
            pulse_context=context,
            detection_mode="positive",
        )
        absolute = _extract_best_peak_summary_block(
            t,
            signals,
            np.array([0.5, 0.5, 0.5]),
            pulse_context=context,
            detection_mode="absolute",
        )

        np.testing.assert_array_equal(positive["detected"], [True, True, False])
        assert positive["peak_times_s"][0] == pytest.approx(0.2)
        assert positive["peak_heights"][0] == pytest.approx(3.0)
        assert positive["peak_signed_heights"][1] == pytest.approx(2.0)
        np.testing.assert_array_equal(absolute["detected"], [True, True, False])
        assert absolute["peak_times_s"][1] == pytest.approx(0.2)
        assert absolute["peak_heights"][1] == pytest.approx(4.0)
        assert absolute["peak_signed_heights"][1] == pytest.approx(-4.0)

    def test_negative_peak_detected_in_absolute_mode(self):
        t = np.arange(4000) * 5e-5
        signal = -np.exp(-((t - 0.1) ** 2) / (2 * 0.002 ** 2)) * 0.5
        result = extract_pulse_features(
            t,
            signal,
            0.01,
            1e-3,
            0.05,
            detection_mode="absolute",
        )
        assert result["n_peaks"] == 1
        peak = result["peaks"][0]
        assert peak["peak_height"] == pytest.approx(0.5, rel=0.1)
        assert peak["peak_signed_height"] < 0
        assert peak["peak_polarity"] == "negative"

    def test_pulse_context_matches_direct_path(self):
        t = np.arange(4000) * 5e-5
        signal = np.exp(-((t - 0.1) ** 2) / (2 * 0.002 ** 2)) * 0.5
        context = build_pulse_extraction_context(t, 1e-3, 0.05)
        direct = extract_pulse_features(t, signal, 0.01, 1e-3, 0.05)
        cached = extract_pulse_features(
            t,
            signal,
            0.01,
            1e-3,
            0.05,
            context=context,
        )
        assert cached["n_peaks"] == direct["n_peaks"]
        assert cached["threshold_used"] == pytest.approx(direct["threshold_used"])
        assert cached["detection_mode"] == direct["detection_mode"]
        assert len(cached["peaks"]) == len(direct["peaks"])
        for cached_peak, direct_peak in zip(cached["peaks"], direct["peaks"]):
            assert cached_peak.keys() == direct_peak.keys()
            for key in cached_peak:
                if isinstance(cached_peak[key], float):
                    assert cached_peak[key] == pytest.approx(direct_peak[key], rel=1e-12, abs=1e-15)
                else:
                    assert cached_peak[key] == direct_peak[key]

    def test_narrow_peak_filtered(self):
        t = np.arange(4000) * 5e-5
        signal = np.exp(-((t - 0.1) ** 2) / (2 * 0.00005 ** 2)) * 0.5
        result = extract_pulse_features(t, signal, 0.01, 2.5e-3, 0.05)
        assert result["n_peaks"] == 0

    def test_duration_above_threshold_width_mode_uses_crossing_duration(self):
        t = np.arange(20) * 1e-3
        signal = np.zeros_like(t)
        signal[5:9] = [0.02, 0.05, 0.04, 0.02]

        result = extract_pulse_features(
            t,
            signal,
            0.01,
            2.5e-3,
            0.05,
            width_measure_mode="duration_above_threshold",
        )

        assert result["n_peaks"] == 1
        peak = result["peaks"][0]
        assert peak["width_measure_mode"] == "duration_above_threshold"
        assert peak["peak_width_s"] == pytest.approx(
            peak["peak_threshold_duration_s"]
        )
        assert peak["peak_threshold_duration_s"] >= 2.5e-3

    def test_duration_above_threshold_width_mode_filters_short_crossing(self):
        t = np.arange(20) * 1e-3
        signal = np.zeros_like(t)
        signal[7] = 0.05

        result = extract_pulse_features(
            t,
            signal,
            0.01,
            2.5e-3,
            0.05,
            width_measure_mode="duration_above_threshold",
        )

        assert result["n_peaks"] == 0

    def test_conservative_duration_policy_uses_observed_sample_span(self):
        t = np.arange(20) * 5e-4
        signal = np.zeros_like(t)
        signal[5:10] = 0.05

        interpolated = extract_pulse_features(
            t,
            signal,
            0.01,
            2.5e-3,
            0.05,
            width_measure_mode="duration_above_threshold",
        )
        conservative = extract_pulse_features(
            t,
            signal,
            0.01,
            2.5e-3,
            0.05,
            width_measure_mode="duration_above_threshold",
            duration_estimation_policy="sample_span_conservative",
        )

        assert interpolated["n_peaks"] == 1
        assert conservative["n_peaks"] == 0

    def test_robust_threshold(self):
        threshold = estimate_threshold_robust(np.random.default_rng(42).normal(0, 0.01, 1000), 5.0)
        assert 0.03 < threshold < 0.08

    def test_robust_threshold_stats_include_sigma(self):
        stats = estimate_threshold_stats_robust(
            np.random.default_rng(42).normal(0, 0.01, 1000),
            5.0,
        )
        assert stats["robust_std"] > 0
        assert stats["threshold"] > stats["median"]

    def test_block_threshold_stats_match_rowwise_robust_stats(self):
        rng = np.random.default_rng(42)
        signals = rng.normal(0, 0.01, size=(5, 31))
        signals[:, 12] += np.linspace(-0.02, 0.02, signals.shape[0])

        block_stats = _estimate_threshold_stats_block(signals, 4.5)

        for row_idx, row in enumerate(signals):
            row_stats = estimate_threshold_stats_robust(row, 4.5)
            assert block_stats["median"][row_idx] == pytest.approx(row_stats["median"])
            assert block_stats["mad"][row_idx] == pytest.approx(row_stats["mad"])
            assert block_stats["robust_std"][row_idx] == pytest.approx(
                row_stats["robust_std"]
            )
            assert block_stats["threshold"][row_idx] == pytest.approx(
                row_stats["threshold"]
            )


class TestReadoutSurrogate:
    def test_first_order_lowpass_alpha_matches_recursive_reference(self):
        signal = np.linspace(-1.0, 1.0, 200)
        time_s = np.arange(200) * 1e-4
        tau_s = 1.0e-3

        expected = np.empty_like(signal)
        expected[0] = signal[0]
        dt = float(time_s[1] - time_s[0])
        alpha = dt / (tau_s + dt)
        for idx in range(1, len(signal)):
            expected[idx] = expected[idx - 1] + alpha * (signal[idx] - expected[idx - 1])

        filtered = _first_order_lowpass_alpha(signal, alpha)
        np.testing.assert_allclose(filtered, expected, atol=1e-12)

    def test_first_order_lowpass_alpha_filters_event_blocks_rowwise(self):
        signal = np.vstack(
            [
                np.linspace(-1.0, 1.0, 200),
                np.sin(np.linspace(0.0, 4.0 * np.pi, 200)),
                np.cos(np.linspace(0.0, 2.0 * np.pi, 200)),
            ]
        )
        alpha = 0.1
        expected_rows = [
            _first_order_lowpass_alpha(row, alpha)
            for row in signal
        ]

        filtered = _first_order_lowpass_alpha(signal, alpha)

        np.testing.assert_allclose(
            filtered,
            np.vstack(expected_rows),
            rtol=1e-14,
            atol=1e-14,
        )

    def test_lockin_surrogate_filters_and_mixes_channels(self):
        time_s = np.arange(200) * 1e-4
        raw = np.linspace(0.0, 1.0, 200)
        sim_cfg = SimulationConfig(
            total_time_s=0.02,
            sampling_rate_Hz=10000.0,
            mean_flow_velocity_m_s=2e-4,
            readout_model="lockin_surrogate",
            lockin_time_constant_s=1.0e-3,
            pod_to_nodi_crosstalk=0.1,
            nodi_to_pod_crosstalk=0.05,
        )
        result = apply_readout_chain(raw, time_s, sim_cfg)
        assert np.std(result["signal_nodi_true"]) < np.std(raw)
        assert np.any(np.abs(result["signal_pod_true"]) > 0)
        assert not np.allclose(result["signal_detect"], result["signal_nodi_true"])
        np.testing.assert_allclose(result["signal_detect"], result["signal_nodi"])

    def test_lockin_context_matches_direct_path(self):
        time_s = np.arange(200) * 1e-4
        raw = np.linspace(-0.2, 0.8, 200)
        sim_cfg = SimulationConfig(
            total_time_s=0.02,
            sampling_rate_Hz=10000.0,
            mean_flow_velocity_m_s=2e-4,
            readout_model="lockin_surrogate",
            lockin_time_constant_s=1.0e-3,
            pod_to_nodi_crosstalk=0.1,
            nodi_to_pod_crosstalk=0.05,
            pod_reference_phase_rad=0.3,
            nodi_reference_phase_rad=-0.2,
        )
        context = _build_readout_context(time_s, sim_cfg)
        direct = apply_readout_chain(raw, time_s, sim_cfg)
        cached = apply_readout_chain(raw, time_s, sim_cfg, readout_context=context)
        for key in (
            "signal_detect",
            "signal_nodi",
            "signal_pod",
            "signal_nodi_true",
            "signal_pod_true",
            "signal_nodi_leak",
            "signal_pod_leak",
            "signal_nodi_i",
            "signal_nodi_q",
            "signal_pod_i",
            "signal_pod_q",
        ):
            np.testing.assert_allclose(cached[key], direct[key], atol=1e-12)

    def test_light_in_phase_readout_matches_full_diagnostics_for_event_block(self):
        time_s = np.arange(240) * 1e-4
        raw = np.vstack(
            [
                np.linspace(-0.2, 0.8, time_s.size),
                np.sin(2.0 * np.pi * 300.0 * time_s),
                np.cos(2.0 * np.pi * 700.0 * time_s) * 0.3,
            ]
        )
        sim_cfg = SimulationConfig(
            total_time_s=0.024,
            sampling_rate_Hz=10000.0,
            mean_flow_velocity_m_s=2e-4,
            readout_model="lockin_surrogate",
            readout_observable_mode="in_phase",
            lockin_time_constant_s=1.0e-3,
            pod_lockin_frequency_Hz=1200.0,
            nodi_lockin_frequency_Hz=2400.0,
            pod_to_nodi_crosstalk=0.1,
            nodi_to_pod_crosstalk=0.05,
            pod_reference_phase_rad=0.3,
            nodi_reference_phase_rad=-0.2,
        )
        transit_times = np.array([0.004, 0.008, 0.012])

        full = apply_readout_chain(
            raw,
            time_s,
            sim_cfg,
            transit_time_s=transit_times,
            export_full_diagnostics=True,
        )
        light = apply_readout_chain(
            raw,
            time_s,
            sim_cfg,
            transit_time_s=transit_times,
            export_full_diagnostics=False,
        )

        for key in (
            "signal_detect",
            "signal_nodi",
            "signal_pod",
            "signal_nodi_true",
            "signal_pod_true",
            "nodi_transit_bandwidth_Hz",
            "nodi_transit_bandwidth_gain",
            "nodi_bandwidth_limited_fraction",
        ):
            np.testing.assert_allclose(light[key], full[key], rtol=0.0, atol=0.0)

    def test_post_readout_noise_is_separate_from_raw_noise(self):
        time_s = np.linspace(0.0, 0.01, 50)
        sim_cfg = SimulationConfig(
            total_time_s=0.01,
            sampling_rate_Hz=5000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.0,
            post_readout_noise_std=0.01,
            post_readout_drift_slope=0.2,
        )
        result = add_post_readout_noise(
            np.zeros_like(time_s),
            time_s,
            sim_cfg,
            np.random.default_rng(7),
        )
        assert np.std(result["post_readout_noise"]) > 0
        assert result["signal_post_readout"][-1] > result["signal_post_readout"][0]

    def test_detector_noise_shot_component_scales_with_baseline(self):
        time_s = np.linspace(0.0, 0.01, 256)
        signal = np.zeros_like(time_s)
        sim_cfg = SimulationConfig(
            total_time_s=0.01,
            sampling_rate_Hz=25600.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.0,
            shot_noise_scale=0.01,
        )
        low = add_detector_noise(
            signal,
            time_s,
            sim_cfg,
            np.random.default_rng(10),
            detected_intensity=np.full_like(signal, 1.0),
            baseline_intensity=1.0,
        )
        high = add_detector_noise(
            signal,
            time_s,
            sim_cfg,
            np.random.default_rng(10),
            detected_intensity=np.full_like(signal, 100.0),
            baseline_intensity=100.0,
        )
        assert high["shot_noise_std_mean"] > low["shot_noise_std_mean"]
        assert np.std(high["shot_noise"]) > np.std(low["shot_noise"])
        assert high["mean_shot_noise_baseline_proxy"] > low["mean_shot_noise_baseline_proxy"]
        assert high["mean_shot_noise_intensity_proxy"] > low["mean_shot_noise_intensity_proxy"]

    def test_detector_noise_exports_reference_dominated_shot_noise_diagnostics(self):
        time_s = np.linspace(0.0, 0.01, 128)
        signal = np.zeros_like(time_s)
        sim_cfg = SimulationConfig(
            total_time_s=0.01,
            sampling_rate_Hz=12800.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.0,
            shot_noise_scale=0.01,
        )
        result = add_detector_noise(
            signal,
            time_s,
            sim_cfg,
            np.random.default_rng(11),
            detected_intensity=np.full_like(signal, 0.8),
            baseline_intensity=1.0,
        )
        assert result["shot_noise_reference_dominated_fraction"] == pytest.approx(1.0)
        assert result["mean_shot_noise_intensity_proxy"] == pytest.approx(1.0)
        assert result["mean_shot_noise_baseline_proxy"] == pytest.approx(1.0)
        assert result["noise_model_route"] == "surrogate"
        assert result["shot_noise_model_status"] == "intensity_proxy_shot_noise_surrogate"
        assert result["photon_unit_noise_model_status"] == "not_applied"
        assert result["detector_dynamic_range_model"] == "not_applied"
        assert result["detector_saturation_status"] == "not_evaluated_no_detector_range"
        assert result["dynamic_range_margin"] is None
        assert (
            result["reference_enhancement_snr_claim"]
            == "not_monotonic_without_photon_unit_noise_model"
        )

    def test_detector_noise_diagnostics_mark_absolute_noise_unavailable(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            noise_std=0.01,
            shot_noise_scale=0.02,
            noise_model="gaussian_plus_drift",
            drift_slope=0.1,
        )
        diagnostics = build_detector_noise_diagnostics(
            cfg,
            mean_shot_noise_std=0.03,
            mean_intensity_proxy=2.0,
            mean_baseline_proxy=1.5,
            reference_enhancement_gain=8.0,
        )
        assert diagnostics["noise_model_route"] == "surrogate"
        assert (
            diagnostics["detector_noise_claim_level"]
            == "engineering_noise_surrogate_not_detector_unit"
        )
        assert diagnostics["shot_noise_model_status"] == "intensity_proxy_shot_noise_surrogate"
        assert (
            diagnostics["photon_shot_noise_term_status"]
            == "intensity_proxy_shot_noise_surrogate"
        )
        assert diagnostics["electronics_noise_model_status"] == "gaussian_additive_surrogate"
        assert diagnostics["electronics_noise_term_status"] == "gaussian_additive_surrogate"
        assert diagnostics["drift_noise_model_status"] == "linear_drift_surrogate"
        assert diagnostics["drift_noise_term_status"] == "linear_drift_surrogate"
        assert diagnostics["rin_noise_term_status"] == "not_applied"
        assert diagnostics["speckle_like_noise_term_status"] == "not_applied"
        assert diagnostics["noise_terms_schema_version"] == "noise_terms_v1"
        assert (
            diagnostics["noise_term_quantitative_contribution_status"]
            == "not_available_arbitrary_units"
        )
        assert diagnostics["rin_limited_snr"] is None
        assert diagnostics["shot_noise_limited_snr"] is None
        assert diagnostics["reference_enhancement_gain"] == pytest.approx(8.0)
        assert (
            diagnostics["reference_enhancement_snr_claim"]
            == "not_monotonic_without_photon_unit_noise_model"
        )

    def test_background_field_diagnostics_mark_leakage_unmodeled(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            background_subtraction_on=True,
        )
        diagnostics = build_background_field_diagnostics(cfg)
        assert diagnostics["background_field_model"] == "baseline_subtraction_surrogate"
        assert diagnostics["background_field_status"] == "baseline_subtraction_only_no_explicit_leakage_field"
        assert diagnostics["background_subtraction_status"] == "active"
        assert diagnostics["residual_transmitted_leakage_status"] == "not_modeled"
        assert diagnostics["stray_light_status"] == "not_modeled"
        assert diagnostics["blank_trace_empirical_available"] is False
        assert (
            diagnostics["particle_induced_channel_phase_perturbation_status"]
            == "not_modeled_weak_superposition_assumed"
        )
        assert (
            diagnostics["nodi_signal_component_model"]
            == "scattering_interference_only_surrogate"
        )
        assert diagnostics["nodi_forward_extinction_leakage_status"] == "not_modeled"
        assert (
            diagnostics["nodi_particle_induced_channel_coupling_status"]
            == "not_modeled_weak_superposition_assumed"
        )
        assert (
            diagnostics["superposition_validity_status"]
            == "not_evaluated_missing_reference_or_beam_area"
        )
        assert diagnostics["E_sca_to_E_ref_amplitude_ratio_estimate"] is None
        assert diagnostics["extinction_to_beam_area_estimate"] is None
        assert (
            diagnostics["reference_depletion_estimate_status"]
            == "not_computed_requires_joint_field_solution"
        )
        assert diagnostics["channel_particle_coupling_model"] == "independent_superposition"
        assert diagnostics["joint_fullwave_required_for_quantitative_phase"] is True
        assert "E_sca_to_E_ref_ratio_unavailable" in diagnostics[
            "superposition_validity_blocker_summary"
        ]
        assert (
            diagnostics["nodi_component_escalation_route"]
            == "measured_blank_or_fullwave_required_for_extinction_leakage"
        )
        assert diagnostics["background_claim_level"] == "engineering_background_surrogate_not_measured_blank"

    def test_apply_readout_preset_freezes_paper_counting_fields(self):
        cfg = apply_readout_preset(
            SimulationConfig(0.2, 20000.0, 2e-4),
            "tsuyama_2022_counting_10sigma",
        )
        assert cfg.readout_preset == "tsuyama_2022_counting_10sigma"
        assert cfg.threshold_sigma == pytest.approx(10.0)
        assert cfg.min_peak_width_s == pytest.approx(2.5e-3)
        assert cfg.min_peak_interval_s == pytest.approx(0.1)
        assert cfg.pulse_detection_mode == "positive"
        assert cfg.readout_observable_mode == "magnitude"
        assert cfg.detection_decision_mode == "single_channel"

    def test_apply_ev_nodi_design_preset_freezes_envelope_readout_fields(self):
        cfg = apply_readout_preset(
            SimulationConfig(0.2, 20000.0, 2e-4),
            "EV_NODI_only_design",
        )
        assert cfg.readout_preset == "EV_NODI_only_design"
        assert cfg.readout_observable_mode == "magnitude"
        assert cfg.readout_internal_demod_route == "analytic_lockin_surrogate"
        assert cfg.readout_anti_alias_policy == "analytic_demod_no_carrier_sampling"
        assert cfg.nodi_readout_semantics == "bandpass_envelope_surrogate"
        assert cfg.electronics_demod_phase_policy == "magnitude_only"
        assert cfg.nodi_lockin_frequency_Hz == pytest.approx(2000.0)
        assert cfg.threshold_sigma == pytest.approx(5.0)
        assert cfg.threshold_tail == "one_sided"
        assert cfg.detection_decision_mode == "single_channel"
        assert cfg.pulse_detection_mode == "positive"
        assert cfg.engineering_decision_basis == "single_channel"

    def test_ev_nodi_design_sweep_config_combines_p0_transport_and_readout(self):
        cfg = make_ev_nodi_design_sweep_config(
            SimulationConfig(0.2, 20000.0, 2e-4)
        )
        assert cfg.include_diffusion is True
        assert cfg.flow_profile_model == "rect_series"
        assert cfg.diffusion_hindrance_model == "near_wall_surrogate"
        assert cfg.initial_position_distribution_mode == "flux_weighted"
        assert cfg.reference_model == "channel_angular_surrogate"
        assert cfg.reference_route == "engineering_fallback"
        assert (
            cfg.particle_induced_channel_perturbation_model
            == "excluded_volume_phase_surrogate"
        )
        assert cfg.particle_channel_perturbation_application_mode == "diagnostic_only"
        assert cfg.readout_preset == "EV_NODI_only_design"
        assert cfg.nodi_readout_semantics == "bandpass_envelope_surrogate"
        assert cfg.EV_ensemble_mode == "explicit_preset_cases"

    def test_readout_convention_diagnostics_track_phase_sampling_and_units(self):
        cfg = SimulationConfig(0.2, 20000.0, 2e-4)
        diagnostics = build_readout_convention_diagnostics(cfg)
        for field in READOUT_TRANSFER_DIAGNOSTIC_FIELDS:
            assert field in diagnostics
        assert diagnostics["readout_preset"] == "exploratory_default"
        assert diagnostics["readout_preset_status"] == "exploratory_default_active"
        assert diagnostics["readout_preset_claim_level"] == "exploratory_phase_aware_surrogate"
        assert diagnostics["nodi_readout_semantics"] == "locked_carrier_surrogate"
        assert diagnostics["nodi_readout_semantics_gate_passed"] is False
        assert diagnostics["readout_phase_locked_claim_allowed"] is False
        assert "locked_carrier_surrogate" in diagnostics[
            "nodi_readout_semantics_blocker_summary"
        ]
        assert diagnostics["electronics_demod_phase_policy"] == "locked_to_event_center"
        assert diagnostics["effective_electronics_demod_phase_policy"] == "locked_to_event_center"
        assert diagnostics["readout_polarity"] == "sign(lockin_output_I)"
        assert diagnostics["polarity_source"] == "optical_and_electronics_phase_mixed"
        assert diagnostics["readout_internal_sampling_rate_Hz"] == pytest.approx(20000.0)
        assert diagnostics["readout_output_sampling_rate_Hz"] == pytest.approx(20000.0)
        assert diagnostics["readout_carrier_nyquist_resolved"] is True
        assert diagnostics["readout_carrier_resolved"] is False
        assert diagnostics["readout_sampling_validity"] == "carrier_underresolved"
        assert diagnostics["readout_sampling_hard_gate_passed"] is False
        assert diagnostics["readout_sampling_output_claim_blocker_active"] is True
        assert diagnostics["readout_sampling_claim_level"] == "engineering_diagnostic"
        assert diagnostics["lockin_output_unit_convention"] == "arbitrary_lockin_output_units"
        assert diagnostics["lockin_measured_voltage_comparable"] is False

    def test_readout_convention_diagnostics_mark_magnitude_polarity_erased(self):
        cfg = apply_readout_preset(
            SimulationConfig(0.2, 20000.0, 2e-4),
            "tsuyama_2024_paired_5sigma",
        )
        diagnostics = build_readout_convention_diagnostics(cfg)
        assert diagnostics["readout_preset_status"] == "paper_preset_contract_active"
        assert diagnostics["readout_preset_threshold_scope"] == "shared_pod_nodi_positive_5sigma"
        assert diagnostics["readout_internal_demod_route"] == "analytic_lockin_surrogate"
        assert diagnostics["readout_analytic_demod_used"] is False
        assert diagnostics["readout_sampling_validity"] == "carrier_underresolved"
        assert diagnostics["readout_numerical_route"] == (
            "sampled_carrier_lockin_demod_surrogate"
        )
        assert diagnostics["readout_numerical_route_claim_level"] == (
            "declared_analytic_route_not_implemented_for_semantics_falls_back_to_carrier_surrogate"
        )
        assert diagnostics["effective_electronics_demod_phase_policy"] == "magnitude_only"
        assert diagnostics["polarity_source"] == "magnitude_erased"
        assert diagnostics["lockin_reported_channel"] == "R"
        assert diagnostics["readout_shared_threshold_profile"] is True
        assert diagnostics["readout_lane_specific_thresholds_available"] is False
        assert "1.2kHz lane leakage risk" in diagnostics["readout_preset_frequency_leakage_note"]

    def test_readout_convention_diagnostics_allow_ev_envelope_semantics(self):
        cfg = apply_readout_preset(
            SimulationConfig(0.2, 20000.0, 2e-4),
            "EV_NODI_only_design",
        )
        diagnostics = build_readout_convention_diagnostics(cfg)
        assert diagnostics["readout_preset_status"] == "ev_design_preset_contract_active"
        assert diagnostics["readout_preset_claim_level"] == (
            "ev_nodi_envelope_surrogate_not_measured_transfer"
        )
        assert diagnostics["nodi_readout_semantics"] == "bandpass_envelope_surrogate"
        assert diagnostics["nodi_event_arrival_phase_policy"] == (
            "transient_envelope_magnitude_governed"
        )
        assert diagnostics["nodi_readout_semantics_gate_passed"] is True
        assert diagnostics["nodi_readout_semantics_blocker_summary"] == "none"
        assert diagnostics["readout_phase_locked_claim_allowed"] is False
        assert diagnostics["readout_sampling_validity"] == "analytic_demod"
        assert diagnostics["effective_electronics_demod_phase_policy"] == "magnitude_only"
        assert diagnostics["nodi_bandpass_center_Hz"] == pytest.approx(2000.0)
        assert diagnostics["nodi_bandpass_gain"] == pytest.approx(1.0)
        assert diagnostics["nodi_bandpass_phase"] is None
        assert diagnostics["readout_numerical_route"] == (
            "bandpass_envelope_response_surrogate"
        )
        assert diagnostics["readout_numerical_route_claim_level"] == (
            "ev_transient_envelope_numerical_surrogate_not_measured_transfer"
        )

    def test_ev_analytic_readout_uses_bandpass_envelope_numerical_route(self):
        time_s = np.arange(400) * 1e-4
        raw = np.zeros_like(time_s)
        raw[180:220] = np.hanning(40)
        cfg = apply_readout_preset(
            SimulationConfig(
                total_time_s=0.04,
                sampling_rate_Hz=10000.0,
                mean_flow_velocity_m_s=2e-4,
                readout_model="lockin_surrogate",
                lockin_time_constant_s=1.0e-3,
            ),
            "EV_NODI_only_design",
        )

        result = apply_readout_chain(raw, time_s, cfg, transit_time_s=0.004)

        assert result["readout_numerical_route"] == (
            "bandpass_envelope_response_surrogate"
        )
        assert np.all(result["signal_detect"] >= 0.0)
        assert np.max(result["signal_nodi_true"]) > 0.0

    def test_declared_analytic_route_falls_back_when_semantics_are_not_envelope(self):
        time_s = np.arange(400) * 1e-4
        raw = np.zeros_like(time_s)
        raw[180:220] = np.hanning(40)
        cfg = apply_readout_preset(
            SimulationConfig(
                total_time_s=0.04,
                sampling_rate_Hz=10000.0,
                mean_flow_velocity_m_s=2e-4,
                readout_model="lockin_surrogate",
                lockin_time_constant_s=1.0e-3,
            ),
            "tsuyama_2024_paired_5sigma",
        )

        diagnostics = build_readout_convention_diagnostics(cfg)
        result = apply_readout_chain(raw, time_s, cfg, transit_time_s=0.004)

        assert diagnostics["readout_analytic_demod_used"] is False
        assert diagnostics["readout_numerical_route"] == (
            "sampled_carrier_lockin_demod_surrogate"
        )
        assert result["readout_numerical_route"] == diagnostics["readout_numerical_route"]

    def test_readout_transfer_model_marks_random_arrival_phase_gain(self):
        cfg = replace(
            apply_readout_preset(
                SimulationConfig(0.2, 20000.0, 2e-4),
                "EV_NODI_only_design",
            ),
            nodi_readout_semantics="random_arrival_phase_lockin",
            electronics_demod_phase_policy="random_arrival_phase",
        )
        diagnostics = build_nodi_readout_transfer_diagnostics(cfg)
        assert diagnostics["nodi_event_arrival_phase_policy"] == (
            "random_arrival_phase_surrogate"
        )
        assert diagnostics["nodi_readout_semantics_gate_passed"] is True
        assert diagnostics["nodi_random_arrival_phase_average_gain"] == pytest.approx(
            2.0 / np.pi
        )
        assert diagnostics[
            "nodi_random_arrival_phase_i_variance_factor"
        ] == pytest.approx(0.5)
        assert diagnostics[
            "nodi_random_arrival_phase_q_variance_factor"
        ] == pytest.approx(0.5)
        assert diagnostics["nodi_random_arrival_phase_magnitude_bias"] == pytest.approx(
            0.0
        )
        assert diagnostics["nodi_random_vs_locked_disagreement"] == pytest.approx(
            1.0 - 2.0 / np.pi
        )
        assert diagnostics["nodi_random_vs_locked_claim_degraded"] is True
        assert diagnostics["nodi_readout_semantics_claim_level"] == (
            "random_arrival_phase_surrogate_degraded_from_locked_claim"
        )
        assert diagnostics["readout_phase_locked_claim_allowed"] is False

    def test_readout_transfer_model_blocks_random_arrival_signed_i_claim(self):
        cfg = replace(
            SimulationConfig(0.2, 20000.0, 2e-4),
            nodi_readout_semantics="random_arrival_phase_lockin",
            electronics_demod_phase_policy="random_arrival_phase",
            readout_observable_mode="in_phase",
        )
        diagnostics = build_nodi_readout_transfer_diagnostics(cfg)
        assert diagnostics["nodi_readout_semantics_gate_passed"] is False
        assert diagnostics["nodi_random_arrival_phase_magnitude_bias"] == pytest.approx(
            1.0 - 2.0 / np.pi
        )
        assert diagnostics["nodi_random_vs_locked_claim_degraded"] is True
        assert diagnostics["nodi_readout_semantics_blocker_summary"] == (
            "random_arrival_phase_requires_magnitude_or_iq_distribution"
        )

    def test_readout_transfer_model_blocks_measured_semantics_without_route(self):
        cfg = replace(
            apply_readout_preset(
                SimulationConfig(0.2, 20000.0, 2e-4),
                "EV_NODI_only_design",
            ),
            nodi_readout_semantics="measured_transfer_function",
            readout_internal_demod_route="analytic_lockin_surrogate",
        )
        diagnostics = build_nodi_readout_transfer_diagnostics(cfg)
        assert diagnostics["nodi_readout_semantics_gate_passed"] is False
        assert diagnostics["readout_phase_locked_claim_allowed"] is False
        assert "measured_transfer_table" in diagnostics[
            "nodi_readout_semantics_blocker_summary"
        ]

    def test_readout_transfer_model_blocks_declared_measured_route_without_table(self):
        cfg = replace(
            SimulationConfig(0.2, 20000.0, 2e-4),
            nodi_readout_semantics="measured_transfer_function",
            readout_internal_demod_route="measured_transfer_function",
        )
        diagnostics = build_nodi_readout_transfer_diagnostics(cfg)
        assert diagnostics["nodi_readout_semantics_gate_passed"] is False
        assert diagnostics["readout_phase_locked_claim_allowed"] is False
        assert diagnostics["nodi_readout_semantics_blocker_summary"] == (
            "measured_semantics_requires_measured_transfer_table"
        )
        assert diagnostics["readout_numerical_route"] == (
            "sampled_carrier_lockin_demod_surrogate"
        )
        assert diagnostics["readout_numerical_route_claim_level"] == (
            "declared_measured_transfer_unimplemented_falls_back_to_carrier_surrogate"
        )
        assert diagnostics["readout_sampling_output_claim_blocker_active"] is True

    def test_readout_convention_diagnostics_detect_alias_risk(self):
        cfg = SimulationConfig(
            0.2,
            2000.0,
            2e-4,
            pod_lockin_frequency_Hz=1200.0,
            nodi_lockin_frequency_Hz=2400.0,
        )
        diagnostics = build_readout_convention_diagnostics(cfg)
        assert diagnostics["readout_carrier_nyquist_resolved"] is False
        assert diagnostics["readout_carrier_resolved"] is False
        assert diagnostics["readout_sampling_validity"] == "carrier_underresolved"
        assert diagnostics["readout_sampling_hard_gate_passed"] is False

    def test_lockin_alias_guard_blocks_underresolved_sampled_carrier_paper_claim(self):
        cfg = apply_readout_preset(
            SimulationConfig(0.2, 20000.0, 2e-4),
            "tsuyama_2024_paired_5sigma",
        )
        cfg = replace(
            cfg,
            readout_internal_demod_route="sampled_carrier_demod_on_event_grid",
            readout_anti_alias_policy="sampled_grid_nyquist_guard",
            sampling_rate_Hz=20000.0,
        )
        readout = build_readout_convention_diagnostics(cfg)
        calibration = build_calibration_state_diagnostics(
            cfg,
            reference={
                "reference_claim_level": "paper_aligned_comparison",
                "reference_calibration_amplitude_status": "not_calibrated",
                "reference_phase_absolute_claim": "not_measured_absolute_phase",
            },
        )
        assert readout["readout_sampling_validity"] == "carrier_underresolved"
        assert readout["readout_sampling_required_rate_Hz"] == pytest.approx(41000.0)
        assert readout["readout_frequency_dependent_paper_conclusion_allowed"] is False
        assert calibration["readout_sampling_output_claim_blocker_active"] is True
        assert calibration["output_claim_level"] == "engineering_diagnostic"
        assert "sampled_carrier_readout_underresolved" in calibration[
            "output_claim_blocker_summary"
        ]

    def test_threshold_false_alarm_diagnostics_separate_absolute_and_positive_tails(self):
        absolute_cfg = SimulationConfig(0.2, 20000.0, 2e-4)
        absolute_diag = build_threshold_false_alarm_diagnostics(absolute_cfg)
        assert absolute_diag["threshold_tail"] == "two_sided"
        assert absolute_diag["threshold_false_alarm_tail_count"] == 2
        assert absolute_diag["threshold_sign"] == "absolute_magnitude"
        assert absolute_diag["threshold_from_blank_trace"] is False
        assert absolute_diag["threshold_from_event_background_segment"] is True
        assert absolute_diag["threshold_calibration_status"] == "gaussian_iid_surrogate_not_empirical_blank"
        assert absolute_diag["colored_noise_false_alarm_status"] == "not_evaluated_iid_surrogate_only"
        assert absolute_diag["lockin_filter_order"] == 1
        assert absolute_diag["empirical_peak_false_alarm_rate_per_minute"] is None
        assert absolute_diag["lane_noise_correlation_coefficient"] is None

        positive_cfg = apply_readout_preset(
            SimulationConfig(0.2, 20000.0, 2e-4),
            "tsuyama_2022_counting_10sigma",
        )
        positive_diag = build_threshold_false_alarm_diagnostics(positive_cfg)
        assert positive_diag["threshold_tail"] == "one_sided"
        assert positive_diag["threshold_false_alarm_tail_count"] == 1
        assert positive_diag["threshold_sign"] == "positive_only"
        assert positive_diag["positive_threshold_sigma_equivalent"] == pytest.approx(10.0)
        assert positive_diag["absolute_threshold_sigma_equivalent"] is None

    def test_threshold_false_alarm_colored_surrogate_exports_bias(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            colored_noise_false_alarm_model="iid_gaussian_surrogate",
        )
        diagnostics = build_threshold_false_alarm_diagnostics(cfg)

        assert diagnostics["threshold_from_blank_trace"] is False
        assert diagnostics["colored_noise_false_alarm_status"] == (
            "iid_gaussian_ar1_1overf_speckle_surrogate_active"
        )
        assert diagnostics["colored_noise_surrogate_components"] == (
            "gaussian_iid",
            "ar1_correlation_proxy",
            "one_over_f_low_frequency_proxy",
            "slow_multiplicative_speckle_proxy",
        )
        assert diagnostics["colored_noise_threshold_bias"] is not None
        assert diagnostics["colored_noise_threshold_bias"] >= 0.0
        assert diagnostics["colored_noise_threshold_bias_status"] == (
            "surrogate_bias_estimate_not_empirical_blank"
        )
        assert diagnostics["effective_independent_samples_per_trace"] < diagnostics[
            "threshold_background_segment_samples"
        ]

    def test_blank_false_positive_summary_supplies_empirical_threshold_diagnostics(
        self,
        tmp_path,
    ):
        table_path = tmp_path / "blank_false_positive.csv"
        table_path.write_text(
            "\n".join(
                [
                    "blank_calibration_id,threshold_sigma_nodi,threshold_sigma_pod,"
                    "blank_trace_autocorrelation_time_s,"
                    "effective_independent_samples_per_trace,lockin_filter_order,"
                    "empirical_peak_false_alarm_rate_per_minute,"
                    "empirical_pair_false_alarm_rate_per_minute,"
                    "lane_noise_correlation_coefficient",
                    "blankA,9.5,10.5,0.002,140,2,0.03,0.004,0.42",
                ]
            ),
            encoding="utf-8",
        )
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            threshold_calibration_source="blank_trace_empirical",
            colored_noise_false_alarm_model="empirical_blank",
            blank_false_positive_calibration_path=str(table_path),
            blank_false_positive_calibration_id="blankA",
        )
        diagnostics = build_threshold_false_alarm_diagnostics(cfg)

        assert diagnostics["threshold_from_blank_trace"] is True
        assert diagnostics["threshold_from_event_background_segment"] is False
        assert diagnostics["threshold_sigma_nodi"] == pytest.approx(9.5)
        assert diagnostics["threshold_sigma_pod"] == pytest.approx(10.5)
        assert diagnostics["threshold_lane_specific_model"] == (
            "blank_summary_lane_specific_thresholds"
        )
        assert diagnostics["threshold_calibration_status"] == (
            "blank_trace_empirical_summary_applied"
        )
        assert diagnostics["colored_noise_false_alarm_status"] == (
            "empirical_blank_colored_noise_summary_applied"
        )
        assert diagnostics["blank_false_positive_calibration_status"] == (
            "blank_false_positive_summary_selected"
        )
        assert diagnostics["blank_trace_autocorrelation_time_s"] == pytest.approx(
            0.002
        )
        assert diagnostics["effective_independent_samples_per_trace"] == pytest.approx(
            140.0
        )
        assert diagnostics["lockin_filter_order"] == 2
        assert diagnostics["empirical_peak_false_alarm_rate_per_minute"] == pytest.approx(
            0.03
        )
        assert diagnostics["empirical_pair_false_alarm_rate_per_minute"] == pytest.approx(
            0.004
        )
        assert diagnostics["lane_noise_correlation_coefficient"] == pytest.approx(0.42)
        assert diagnostics["paired_false_alarm_status"] == (
            "empirical_pair_summary_available"
        )

    def test_blank_false_positive_template_does_not_apply_empirical_thresholds(self):
        table_path = REPO_ROOT / "calibration" / "blank_false_positive_template.csv"
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            threshold_calibration_source="blank_trace_empirical",
            colored_noise_false_alarm_model="empirical_blank",
            blank_false_positive_calibration_path=str(table_path),
            blank_false_positive_calibration_id="template_blank",
        )
        diagnostics = build_threshold_false_alarm_diagnostics(cfg)
        assert diagnostics["threshold_from_blank_trace"] is False
        assert diagnostics["threshold_calibration_status"] == (
            "blank_source_unavailable_using_event_edge_background_surrogate"
        )
        assert diagnostics["threshold_background_source"] == (
            "synthetic_event_edge_background_surrogate"
        )
        assert diagnostics["blank_false_positive_calibration_status"] == (
            "synthetic_blank_false_positive_fixture_selected_not_applied"
        )
        assert diagnostics["blank_false_positive_synthetic_fixture_active"] is True
        assert diagnostics["raw_blank_trace_bootstrap_status"] == (
            "not_configured_summary_table_or_gaussian_iid_only"
        )

    def test_lockin_frequency_separation_reduces_cross_demod_leakage(self):
        time_s = np.arange(400) * 1e-4
        raw = np.linspace(0.0, 1.0, 400)
        separated = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=10000.0,
            mean_flow_velocity_m_s=2e-4,
            readout_model="lockin_surrogate",
            lockin_time_constant_s=1.0e-3,
            pod_lockin_frequency_Hz=1200.0,
            nodi_lockin_frequency_Hz=2400.0,
        )
        overlapped = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=10000.0,
            mean_flow_velocity_m_s=2e-4,
            readout_model="lockin_surrogate",
            lockin_time_constant_s=1.0e-3,
            pod_lockin_frequency_Hz=1200.0,
            nodi_lockin_frequency_Hz=1200.0,
        )
        r_sep = apply_readout_chain(raw, time_s, separated)
        r_ov = apply_readout_chain(raw, time_s, overlapped)
        assert np.std(r_sep["signal_nodi_leak"]) < np.std(r_ov["signal_nodi_leak"])
        assert np.std(r_sep["signal_pod_leak"]) < np.std(r_ov["signal_pod_leak"])

    def test_lockin_low_pod_frequency_strengthens_pod_lane_and_pod_leakage(self):
        time_s = np.arange(400) * 1e-4
        raw = np.linspace(0.0, 1.0, 400)
        low_freq = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=10000.0,
            mean_flow_velocity_m_s=2e-4,
            readout_model="lockin_surrogate",
            lockin_time_constant_s=1.0e-3,
            pod_lockin_frequency_Hz=600.0,
            nodi_lockin_frequency_Hz=1200.0,
            pod_frequency_response_reference_Hz=1200.0,
            pod_frequency_response_exponent=1.0,
        )
        high_freq = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=10000.0,
            mean_flow_velocity_m_s=2e-4,
            readout_model="lockin_surrogate",
            lockin_time_constant_s=1.0e-3,
            pod_lockin_frequency_Hz=2400.0,
            nodi_lockin_frequency_Hz=4800.0,
            pod_frequency_response_reference_Hz=1200.0,
            pod_frequency_response_exponent=1.0,
        )
        r_low = apply_readout_chain(raw, time_s, low_freq)
        r_high = apply_readout_chain(raw, time_s, high_freq)
        assert r_low["pod_frequency_response_gain"] > r_high["pod_frequency_response_gain"]
        assert np.std(r_low["signal_pod_true"]) > np.std(r_high["signal_pod_true"])
        assert np.std(r_low["signal_pod_leak"]) > np.std(r_high["signal_pod_leak"])

    def test_lockin_short_transit_suppresses_nodi_lane_more_strongly(self):
        time_s = np.arange(400) * 1e-4
        raw = np.linspace(0.0, 1.0, 400)
        cfg = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=10000.0,
            mean_flow_velocity_m_s=2e-4,
            readout_model="lockin_surrogate",
            lockin_time_constant_s=1.0e-3,
        )
        slow = apply_readout_chain(raw, time_s, cfg, transit_time_s=0.02)
        fast = apply_readout_chain(raw, time_s, cfg, transit_time_s=0.002)
        assert fast["nodi_transit_bandwidth_Hz"] > slow["nodi_transit_bandwidth_Hz"]
        assert fast["nodi_transit_bandwidth_gain"] < slow["nodi_transit_bandwidth_gain"]
        assert fast["nodi_bandwidth_limited_fraction"] > slow["nodi_bandwidth_limited_fraction"]
        assert np.std(fast["signal_nodi_true"]) < np.std(slow["signal_nodi_true"])

    def test_lockin_slower_time_constant_suppresses_nodi_lane_more_strongly(self):
        time_s = np.arange(400) * 1e-4
        raw = np.linspace(0.0, 1.0, 400)
        fast_cfg = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=10000.0,
            mean_flow_velocity_m_s=2e-4,
            readout_model="lockin_surrogate",
            lockin_time_constant_s=5e-4,
        )
        slow_cfg = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=10000.0,
            mean_flow_velocity_m_s=2e-4,
            readout_model="lockin_surrogate",
            lockin_time_constant_s=5e-3,
        )
        r_fast = apply_readout_chain(raw, time_s, fast_cfg, transit_time_s=0.008)
        r_slow = apply_readout_chain(raw, time_s, slow_cfg, transit_time_s=0.008)
        assert r_slow["nodi_lockin_bandwidth_Hz"] < r_fast["nodi_lockin_bandwidth_Hz"]
        assert r_slow["nodi_transit_bandwidth_gain"] < r_fast["nodi_transit_bandwidth_gain"]
        assert r_slow["nodi_bandwidth_limited_fraction"] > r_fast["nodi_bandwidth_limited_fraction"]

    def test_lockin_reference_phase_rotates_signal_between_i_and_q(self):
        time_s = np.arange(400) * 1e-4
        raw = np.linspace(0.0, 1.0, 400)
        cfg_zero = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=10000.0,
            mean_flow_velocity_m_s=2e-4,
            readout_model="lockin_surrogate",
            lockin_time_constant_s=1.0e-3,
            nodi_reference_phase_rad=0.0,
        )
        cfg_quadrature = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=10000.0,
            mean_flow_velocity_m_s=2e-4,
            readout_model="lockin_surrogate",
            lockin_time_constant_s=1.0e-3,
            nodi_reference_phase_rad=np.pi / 2,
        )
        r0 = apply_readout_chain(raw, time_s, cfg_zero)
        r90 = apply_readout_chain(raw, time_s, cfg_quadrature)
        assert np.std(r0["signal_nodi_i"]) > np.std(r0["signal_nodi_q"])
        assert np.std(r90["signal_nodi_q"]) > np.std(r90["signal_nodi_i"])
        np.testing.assert_allclose(r0["signal_nodi_mag"], r90["signal_nodi_mag"], rtol=1e-6, atol=1e-9)

    def test_lockin_magnitude_observable_is_nonnegative(self):
        time_s = np.arange(400) * 1e-4
        raw = np.linspace(-1.0, 1.0, 400)
        cfg = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=10000.0,
            mean_flow_velocity_m_s=2e-4,
            readout_model="lockin_surrogate",
            readout_observable_mode="magnitude",
            lockin_time_constant_s=1.0e-3,
        )
        r = apply_readout_chain(raw, time_s, cfg)
        assert np.all(r["signal_detect"] >= -1e-12)
        np.testing.assert_allclose(r["signal_detect"], r["signal_nodi_mag"], atol=1e-12)


class TestPopulationTraceSimulator:
    def test_population_trace_sparse_smoke_preserves_isolated_detectability(self):
        cfg = PopulationTraceConfig(
            total_time_s=1.0,
            sampling_rate_Hz=2000.0,
            event_rate_Hz=0.0,
            blank_noise_std=0.0,
            drift_slope_per_s=0.0,
            threshold=1.0,
        )
        event_library = [
            {"peak_height": 2.0, "transit_time_s": 0.02},
            {"peak_height": 1.5, "transit_time_s": 0.02},
        ]
        result = simulate_population_trace_from_event_library(
            event_library,
            cfg,
            event_times_s=(0.2, 0.5),
        )

        for field in POPULATION_TRACE_DIAGNOSTIC_FIELDS:
            assert field in result["diagnostics"]
        assert result["diagnostics"]["population_trace_simulator_status"] == (
            "synthetic_smoke_active"
        )
        assert result["diagnostics"]["scheduled_event_count"] == 2
        assert result["diagnostics"]["accepted_event_count"] == 2
        assert result["diagnostics"]["trace_detected_event_count"] == 2
        assert result["diagnostics"]["full_trace_detectability_estimate"] == pytest.approx(1.0)
        assert result["diagnostics"][
            "full_trace_detectability_vs_isolated_detectability_ratio"
        ] == pytest.approx(1.0)
        assert np.max(result["trace"]) > 1.9

    def test_population_trace_reports_overlap_and_deadtime_suppression(self):
        cfg = PopulationTraceConfig(
            total_time_s=1.0,
            sampling_rate_Hz=2000.0,
            event_rate_Hz=0.0,
            blank_noise_std=0.0,
            drift_slope_per_s=0.0,
            min_event_interval_s=0.10,
            dead_time_s=0.06,
            threshold=1.0,
        )
        event_library = [{"peak_height": 2.0, "transit_time_s": 0.08}]
        result = simulate_population_trace_from_event_library(
            event_library,
            cfg,
            event_times_s=(0.10, 0.12, 0.30, 0.36),
        )
        diagnostics = result["diagnostics"]

        assert diagnostics["scheduled_event_count"] == 4
        assert diagnostics["accepted_event_count"] == 2
        assert diagnostics["overlap_rejected_event_count"] == 1
        assert diagnostics["deadtime_suppressed_event_count"] == 1
        assert diagnostics["population_trace_overlap_rejection_active"] is True
        assert diagnostics["population_trace_deadtime_suppression_active"] is True
        assert diagnostics["full_trace_detectability_estimate"] == pytest.approx(0.5)
        assert diagnostics[
            "full_trace_detectability_vs_isolated_detectability_ratio"
        ] == pytest.approx(0.5)

    def test_population_trace_records_blank_noise_and_drift_models(self):
        cfg = PopulationTraceConfig(
            total_time_s=0.5,
            sampling_rate_Hz=1000.0,
            event_rate_Hz=0.0,
            blank_noise_std=0.01,
            drift_slope_per_s=0.2,
            random_seed=7,
            threshold=0.5,
        )
        result = simulate_population_trace_from_event_library(
            [{"peak_height": 1.0, "transit_time_s": 0.01}],
            cfg,
            event_times_s=(0.25,),
        )
        diagnostics = result["diagnostics"]

        assert diagnostics["population_trace_blank_model_status"] == (
            "synthetic_gaussian_blank"
        )
        assert diagnostics["population_trace_drift_model_status"] == (
            "linear_drift_surrogate"
        )
        assert diagnostics["reference_drift_rate_per_min"] == pytest.approx(12.0)
        assert result["blank_trace"].shape == result["trace"].shape


class TestRunStateModel:
    def test_run_state_model_marks_stable_synthetic_config(self):
        diagnostics = build_run_state_diagnostics(
            {
                "mean_peak_height": 2.0,
                "mean_threshold_robust_std": 0.05,
            },
            DEFAULT_SIM_CFG,
        )

        assert set(RUN_STATE_DIAGNOSTIC_FIELDS).issubset(diagnostics)
        assert diagnostics["run_state_model_status"] == "synthetic_config_diagnostic_active"
        assert diagnostics["run_state_stationarity_score"] == pytest.approx(1.0)
        assert diagnostics["run_state_stationarity_band"] == "stable"
        assert diagnostics["reference_drift_rate_per_min"] == pytest.approx(0.0)
        assert diagnostics["recommended_reblank_interval_min"] is None
        assert diagnostics["run_state_claim_level"] == (
            "diagnostic_only_no_measured_run_trace"
        )

    def test_run_state_model_recommends_reblank_for_drift_and_fouling(self):
        cfg = replace(
            DEFAULT_SIM_CFG,
            noise_model="gaussian_plus_drift",
            drift_slope=0.02,
            post_readout_drift_slope=0.03,
            wall_interaction_model="adsorption_loss_empirical",
            adsorption_probability_per_length_m=2.0,
        )
        diagnostics = build_run_state_diagnostics(
            {
                "mean_peak_height": 10.0,
                "mean_threshold_robust_std": 0.1,
            },
            cfg,
        )

        assert diagnostics["reference_drift_rate_per_min"] == pytest.approx(3.0)
        assert diagnostics["run_state_drift_fraction_per_min"] == pytest.approx(0.3)
        assert diagnostics["run_state_fouling_index_per_min"] > 0.0
        assert diagnostics["run_state_stationarity_score"] < 1.0
        assert diagnostics["recommended_reblank_interval_min"] is not None
        assert diagnostics["recommended_reblank_basis"] in {
            "drift_limited",
            "fouling_limited",
        }

    def test_run_state_model_exports_from_single_case_batch(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 180)
        cfg = replace(
            DEFAULT_SIM_CFG,
            total_time_s=0.2,
            n_events=2,
            random_seed=4,
            noise_model="gaussian_plus_drift",
            drift_slope=0.02,
        )
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
            channel=BASELINE_CHANNEL,
            sim_cfg=cfg,
        )
        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            baseline["E_sca_ref"],
            theta_grid,
        )

        assert set(RUN_STATE_DIAGNOSTIC_FIELDS).issubset(batch["summary"])
        assert batch["summary"]["run_state_model_status"] == (
            "synthetic_config_diagnostic_active"
        )
        assert batch["intrinsic"]["reference_drift_rate_per_min"] == pytest.approx(
            batch["summary"]["reference_drift_rate_per_min"]
        )


class TestBatchSummaryAndEngineeringScore:
    def test_summarize_batch_exposes_stability_margin_and_phase_flip_metrics(self):
        fake_events = [
            {
                "threshold": 1.0,
                "threshold_robust_std": 1.0,
                "signal_noisy": np.array([0.0, 0.2, 0.1, 0.0, 0.0, 1.2, 2.0, 0.1, 0.0, 0.0]),
                "pulse_detection_mode": "absolute",
                "transit_time_s": 0.012,
                "local_snr": 3.5,
                "shot_noise_reference_dominated_fraction": 1.0,
                "mean_shot_noise_intensity_proxy": 1.2,
                "mean_shot_noise_baseline_proxy": 1.0,
                "mean_A_ref_local": 5.0,
                "mean_A_sca_local": 1.0,
                "mean_reference_to_scattering_amplitude_ratio": 5.0,
                "reference_dominated_fraction": 1.0,
                "nodi_transit_bandwidth_Hz": 80.0,
                "nodi_transit_bandwidth_gain": 0.9,
                "nodi_bandwidth_limited_fraction": 0.1,
                "detection_decision_mode": "single_channel",
                "has_paired_pulse": True,
                "best_peak_paired": True,
                "detected_single_channel": True,
                "detected_paired_channel": True,
                "strict_paired_detected": True,
                "features": {
                    "n_peaks": 1,
                    "peaks": [
                        {
                            "peak_height": 2.0,
                            "peak_signed_height": 2.0,
                            "peak_width_s": 0.010,
                        }
                    ],
                },
            },
            {
                "threshold": 1.0,
                "threshold_robust_std": 1.0,
                "signal_noisy": np.array([0.0, 0.1, -0.1, 0.0, 0.0, -1.1, -0.4, 0.0, 0.0, 0.0]),
                "pulse_detection_mode": "absolute",
                "transit_time_s": 0.014,
                "local_snr": 2.1,
                "shot_noise_reference_dominated_fraction": 0.0,
                "mean_shot_noise_intensity_proxy": 0.6,
                "mean_shot_noise_baseline_proxy": 0.5,
                "mean_A_ref_local": 4.0,
                "mean_A_sca_local": 2.0,
                "mean_reference_to_scattering_amplitude_ratio": 2.0,
                "reference_dominated_fraction": 0.5,
                "nodi_transit_bandwidth_Hz": 70.0,
                "nodi_transit_bandwidth_gain": 0.8,
                "nodi_bandwidth_limited_fraction": 0.2,
                "detection_decision_mode": "single_channel",
                "has_paired_pulse": False,
                "best_peak_paired": False,
                "detected_single_channel": True,
                "detected_paired_channel": False,
                "strict_paired_detected": False,
                "features": {
                    "n_peaks": 1,
                    "peaks": [
                        {
                            "peak_height": 1.1,
                            "peak_signed_height": -1.1,
                            "peak_width_s": 0.015,
                        }
                    ],
                },
            },
            {
                "threshold": 1.0,
                "threshold_robust_std": 1.0,
                "signal_noisy": np.array([0.0, 0.05, -0.02, 0.01, 0.0, 0.0, 0.02, 0.0, 0.0, 0.0]),
                "pulse_detection_mode": "absolute",
                "transit_time_s": 0.010,
                "local_snr": 0.6,
                "shot_noise_reference_dominated_fraction": 0.0,
                "mean_shot_noise_intensity_proxy": 0.0,
                "mean_shot_noise_baseline_proxy": 0.0,
                "mean_A_ref_local": 0.0,
                "mean_A_sca_local": 0.0,
                "mean_reference_to_scattering_amplitude_ratio": 0.0,
                "reference_dominated_fraction": 0.0,
                "nodi_transit_bandwidth_Hz": 100.0,
                "nodi_transit_bandwidth_gain": 0.6,
                "nodi_bandwidth_limited_fraction": 0.4,
                "detection_decision_mode": "single_channel",
                "has_paired_pulse": True,
                "best_peak_paired": False,
                "detected_single_channel": False,
                "detected_paired_channel": True,
                "strict_paired_detected": True,
                "features": {
                    "n_peaks": 0,
                    "peaks": [],
                },
            },
        ]

        summary = summarize_batch(fake_events)
        assert summary["n_detected"] == 2
        assert summary["detection_rate"] == pytest.approx(2 / 3)
        assert summary["stable_detection_rate"] == pytest.approx(1 / 3)
        assert summary["stable_detection_rate_wilson_lb"] < summary["stable_detection_rate"]
        assert summary["mean_positive_peak_height"] == pytest.approx(2.0)
        assert summary["mean_negative_peak_height"] == pytest.approx(1.1)
        assert summary["positive_peak_fraction"] == pytest.approx(0.5)
        assert summary["negative_peak_fraction"] == pytest.approx(0.5)
        assert summary["phase_flip_fraction"] == pytest.approx(0.5)
        assert summary["phase_flip_fraction_wilson_ub"] > summary["phase_flip_fraction"]
        assert summary["mean_peak_to_threshold_ratio"] == pytest.approx(1.55)
        assert summary["mean_peak_margin_z"] == pytest.approx(0.55)
        assert summary["mean_transit_time_s"] == pytest.approx(0.012)
        assert summary["mean_local_snr"] == pytest.approx((3.5 + 2.1 + 0.6) / 3.0)
        assert summary["mean_nodi_transit_bandwidth_Hz"] == pytest.approx((80.0 + 70.0 + 100.0) / 3.0)
        assert summary["mean_nodi_transit_bandwidth_gain"] == pytest.approx((0.9 + 0.8 + 0.6) / 3.0)
        assert summary["mean_nodi_bandwidth_limited_fraction"] == pytest.approx((0.1 + 0.2 + 0.4) / 3.0)
        assert summary["single_channel_n_detected"] == 2
        assert summary["single_channel_detection_rate"] == pytest.approx(2 / 3)
        assert summary["single_channel_detection_rate_wilson_lb"] < summary["single_channel_detection_rate"]
        assert summary["single_channel_stable_detection_rate"] == pytest.approx(1 / 3)
        assert summary["single_channel_mean_peak_margin_z"] == pytest.approx(0.55)
        assert summary["paired_channel_n_detected"] == 2
        assert summary["paired_channel_detection_rate"] == pytest.approx(2 / 3)
        assert summary["paired_channel_detection_rate_wilson_lb"] < summary["paired_channel_detection_rate"]
        assert summary["paired_channel_stable_detection_rate"] == pytest.approx(1 / 3)
        assert summary["paired_channel_mean_peak_margin_z"] == pytest.approx(0.55)
        assert summary["strict_paired_detection_rate"] == pytest.approx(2 / 3)
        assert summary["strict_paired_detection_rate_wilson_lb"] == pytest.approx(
            summary["paired_channel_detection_rate_wilson_lb"]
        )
        assert summary["paired_detection_rate"] == pytest.approx(0.5)
        assert summary["best_peak_pairing_rate"] == pytest.approx(0.5)
        assert summary["detection_decision_mode"] == "single_channel"
        assert summary["robust_cv_peak_height"] == pytest.approx(0.43043225806451607)
        assert summary["hit_rate_at_fixed_false_alarm"] == pytest.approx(2 / 3)
        assert summary["roc_auc_event_vs_background"] == pytest.approx(6.5 / 9.0)
        assert summary["d_prime_event_vs_background"] > 0
        assert summary["all_signed_heights"] == [2.0, -1.1]
        assert summary["all_peak_to_threshold_ratios"] == [2.0, 1.1]
        assert summary["all_peak_margin_z"] == pytest.approx([1.0, 0.1])
        assert summary["mean_A_ref_local"] == pytest.approx((5.0 + 4.0 + 0.0) / 3.0)
        assert summary["mean_A_sca_local"] == pytest.approx((1.0 + 2.0 + 0.0) / 3.0)
        assert summary["mean_reference_to_scattering_amplitude_ratio"] == pytest.approx((5.0 + 2.0 + 0.0) / 3.0)

    def test_summarize_batch_respects_paired_channel_decision_mode(self):
        paired_peak = {
            "peak_height": 1.4,
            "peak_signed_height": 1.4,
            "peak_width_s": 0.012,
        }
        single_only_peak = {
            "peak_height": 1.8,
            "peak_signed_height": 1.8,
            "peak_width_s": 0.010,
        }
        fake_events = [
            {
                "threshold": 1.0,
                "threshold_robust_std": 1.0,
                "signal_noisy": np.array([0.0, 0.0, 1.8, 0.0, 0.0]),
                "pulse_detection_mode": "positive",
                "transit_time_s": 0.010,
                "local_snr": 2.5,
                "detection_decision_mode": "paired_channel",
                "has_paired_pulse": False,
                "best_peak_paired": False,
                "detected_single_channel": True,
                "detected_paired_channel": False,
                "strict_paired_detected": False,
                "features": {"n_peaks": 0, "peaks": []},
                "features_nodi": {"n_peaks": 1, "peaks": [single_only_peak]},
                "features_paired": {"n_peaks": 0, "peaks": []},
            },
            {
                "threshold": 1.0,
                "threshold_robust_std": 1.0,
                "signal_noisy": np.array([0.0, 0.0, 1.4, 0.0, 0.0]),
                "pulse_detection_mode": "positive",
                "transit_time_s": 0.011,
                "local_snr": 2.0,
                "detection_decision_mode": "paired_channel",
                "has_paired_pulse": True,
                "best_peak_paired": True,
                "detected_single_channel": True,
                "detected_paired_channel": True,
                "strict_paired_detected": True,
                "features": {"n_peaks": 1, "peaks": [paired_peak]},
                "features_nodi": {"n_peaks": 1, "peaks": [paired_peak]},
                "features_paired": {"n_peaks": 1, "peaks": [paired_peak]},
            },
        ]

        summary = summarize_batch(fake_events)
        assert summary["detection_rate"] == pytest.approx(0.5)
        assert summary["single_channel_n_detected"] == 2
        assert summary["single_channel_detection_rate"] == pytest.approx(1.0)
        assert summary["single_channel_detection_rate_wilson_lb"] < 1.0
        assert summary["single_channel_stable_detection_rate"] == pytest.approx(0.0)
        assert summary["paired_channel_n_detected"] == 1
        assert summary["paired_channel_detection_rate"] == pytest.approx(0.5)
        assert summary["paired_channel_stable_detection_rate"] == pytest.approx(0.0)
        assert summary["paired_channel_mean_peak_margin_z"] == pytest.approx(0.4)
        assert summary["strict_paired_detection_rate"] == pytest.approx(0.5)
        assert summary["strict_paired_detection_rate_wilson_lb"] < 0.5
        assert summary["paired_detection_rate"] == pytest.approx(0.5)
        assert summary["best_peak_pairing_rate"] == pytest.approx(0.5)
        assert summary["detection_decision_mode"] == "paired_channel"

    def test_engineering_score_penalizes_phase_flips_and_rewards_margin(self):
        good = compute_engineering_score(
            stable_rate_norm=0.8,
            threshold_margin_norm=0.7,
            local_snr_norm=0.6,
            CV_norm=0.2,
            robust_CV_norm=0.15,
            phase_flip_penalty=0.0,
        )
        bad = compute_engineering_score(
            stable_rate_norm=0.8,
            threshold_margin_norm=0.7,
            local_snr_norm=0.6,
            CV_norm=0.2,
            robust_CV_norm=0.15,
            phase_flip_penalty=0.8,
        )
        assert good > bad

    def test_engineering_score_rewards_discriminability_metrics(self):
        richer = compute_engineering_score(
            stable_rate_norm=0.5,
            threshold_margin_norm=0.5,
            local_snr_norm=0.9,
            CV_norm=0.3,
            robust_CV_norm=0.3,
            phase_flip_penalty=0.2,
            auc_norm=0.9,
            hit_rate_norm=0.8,
            d_prime_norm=0.7,
        )
        poorer = compute_engineering_score(
            stable_rate_norm=0.5,
            threshold_margin_norm=0.5,
            local_snr_norm=0.1,
            CV_norm=0.3,
            robust_CV_norm=0.3,
            phase_flip_penalty=0.2,
            auc_norm=0.2,
            hit_rate_norm=0.1,
            d_prime_norm=0.1,
        )
        assert richer > poorer

    def test_engineering_score_penalizes_event_artifact_risk(self):
        clean = compute_engineering_score(
            stable_rate_norm=0.6,
            threshold_margin_norm=0.6,
            local_snr_norm=0.6,
            CV_norm=0.2,
            robust_CV_norm=0.2,
            phase_flip_penalty=0.0,
            event_artifact_risk_norm=0.0,
        )
        artifact_heavy = compute_engineering_score(
            stable_rate_norm=0.6,
            threshold_margin_norm=0.6,
            local_snr_norm=0.6,
            CV_norm=0.2,
            robust_CV_norm=0.2,
            phase_flip_penalty=0.0,
            event_artifact_risk_norm=1.0,
        )
        assert artifact_heavy < clean

    def test_wilson_bounds_shrink_small_sample_rates(self):
        assert wilson_lower_bound(1, 2) < 0.5
        assert wilson_upper_bound(1, 2) > 0.5

    def test_engineering_gate_rejects_unstable_case(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            engineering_min_detected_events=5,
            engineering_min_detected_fraction=0.2,
            engineering_min_stable_detection_rate=0.3,
            engineering_max_phase_flip_fraction=0.4,
            engineering_min_mean_peak_margin_z=0.8,
        )
        summary = {
            "n_events": 30,
            "n_detected": 3,
            "detection_rate": 0.1,
            "detection_rate_wilson_lb": 0.03,
            "stable_detection_rate": 0.2,
            "phase_flip_fraction": 0.6,
            "stable_detection_rate_wilson_lb": 0.08,
            "phase_flip_fraction_wilson_ub": 0.88,
            "mean_peak_margin_z": 0.4,
        }
        gate = evaluate_engineering_gate(summary, cfg)
        assert gate["engineering_gate_passed"] is False
        assert gate["engineering_gate_failed_count"] == 5
        assert "n_detected<6" in gate["engineering_gate_reason"]
        assert "detection_rate<0.20" in gate["engineering_gate_reason"]

    def test_engineering_gate_uses_hybrid_detected_requirement(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            engineering_min_detected_events=5,
            engineering_min_detected_fraction=0.25,
        )
        summary = {
            "n_events": 40,
            "n_detected": 8,
            "detection_rate_wilson_lb": 0.12,
            "stable_detection_rate_wilson_lb": 0.3,
            "phase_flip_fraction_wilson_ub": 0.1,
            "mean_peak_margin_z": 1.2,
        }
        gate = evaluate_engineering_gate(summary, cfg)
        assert gate["engineering_gate_required_detected_events"] == 10
        assert gate["engineering_gate_passed"] is False
        assert "n_detected<10" in gate["engineering_gate_reason"]

    def test_engineering_gate_can_require_strict_paired_confirmation(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            engineering_min_strict_paired_detection_rate=0.3,
        )
        summary = {
            "n_events": 20,
            "n_detected": 8,
            "detection_rate_wilson_lb": 0.22,
            "stable_detection_rate_wilson_lb": 0.35,
            "phase_flip_fraction_wilson_ub": 0.1,
            "mean_peak_margin_z": 1.2,
            "strict_paired_detection_rate_wilson_lb": 0.18,
        }
        gate = evaluate_engineering_gate(summary, cfg)
        assert gate["engineering_gate_passed"] is False
        assert "strict_paired_detection_rate<0.30" in gate["engineering_gate_reason"]
        assert gate["engineering_gate_strict_paired_rate_lb"] == pytest.approx(0.18)
        assert gate["engineering_gate_required_strict_paired_detection_rate"] == pytest.approx(0.3)

    def test_engineering_gate_can_follow_paired_channel_basis(self):
        cfg = SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            engineering_decision_basis="paired_channel",
            engineering_min_detected_fraction=0.3,
            engineering_min_stable_detection_rate=0.15,
            engineering_min_mean_peak_margin_z=0.5,
        )
        summary = {
            "n_events": 20,
            "n_detected": 12,
            "detection_rate_wilson_lb": 0.42,
            "stable_detection_rate_wilson_lb": 0.35,
            "phase_flip_fraction_wilson_ub": 0.1,
            "mean_peak_margin_z": 1.1,
            "paired_channel_n_detected": 5,
            "paired_channel_detection_rate": 0.25,
            "paired_channel_detection_rate_wilson_lb": 0.11,
            "paired_channel_stable_detection_rate": 0.05,
            "paired_channel_stable_detection_rate_wilson_lb": 0.01,
            "paired_channel_phase_flip_fraction": 0.0,
            "paired_channel_phase_flip_fraction_wilson_ub": 0.12,
            "paired_channel_mean_peak_margin_z": 0.4,
        }
        gate = evaluate_engineering_gate(summary, cfg)
        assert gate["engineering_gate_passed"] is False
        assert gate["engineering_gate_basis"] == "paired_channel"
        assert "paired_channel_detection_rate<0.30" in gate["engineering_gate_reason"]
        assert "paired_channel_stable_detection_rate<0.15" in gate["engineering_gate_reason"]
        assert "paired_channel_mean_peak_margin_z<0.50" in gate["engineering_gate_reason"]

    def test_final_engineering_score_pushes_failed_cases_below_pass_set(self):
        passed = compute_final_engineering_score(0.7, True, 0)
        failed = compute_final_engineering_score(0.9, False, 2)
        assert passed == pytest.approx(0.7)
        assert failed < passed


class TestDesignMetricsAndPostprocess:
    def test_parallel_case_chunk_size_stays_small_for_responsive_progress(self):
        assert _resolve_parallel_case_chunk_size(0, 4) == 1
        assert _resolve_parallel_case_chunk_size(16, 4) == 1
        assert _resolve_parallel_case_chunk_size(1024, 4) == 8
        assert _resolve_parallel_case_chunk_size(10_000, 16) == 8

    def test_iter_case_spec_chunks_preserves_order_and_tail(self):
        case_specs = [{"case_idx": idx} for idx in range(5)]

        chunks = list(_iter_case_spec_chunks(case_specs, 2))

        assert chunks == [
            (
                {"case_idx": 0},
                {"case_idx": 1},
            ),
            (
                {"case_idx": 2},
                {"case_idx": 3},
            ),
            ({"case_idx": 4},),
        ]

    def test_anchor_equivalent_metrics_match_geometry_and_ratios(self):
        anchor = _synthetic_design_result(
            "gold_20nm",
            family="gold",
            peak=2.0,
            margin=1.5,
            stable_rate=0.4,
        )
        ev = _synthetic_design_result(
            "exosome_100nm",
            family="EV_sEV",
            peak=1.0,
            margin=3.0,
            stable_rate=0.8,
        )

        rows = [anchor, ev]
        attach_anchor_equivalent_metrics(rows)
        attach_reference_operating_metrics(rows)
        attach_fluidic_practicality_metrics(rows)

        assert set(DESIGN_METRIC_DIAGNOSTIC_FIELDS).issubset(anchor["summary"])
        assert set(DESIGN_METRIC_DIAGNOSTIC_FIELDS).issubset(ev["summary"])
        assert anchor["summary"]["Au20_equivalent_peak_ratio"] == pytest.approx(1.0)
        assert ev["summary"]["Au20_anchor_available"] is True
        assert ev["summary"]["Au20_anchor_geometry_matched"] is True
        assert ev["summary"]["Au20_equivalent_peak_ratio"] == pytest.approx(0.5)
        assert ev["summary"]["Au20_equivalent_margin_ratio"] == pytest.approx(2.0)
        assert ev["summary"]["Au20_equivalent_stable_rate_ratio"] == pytest.approx(2.0)
        assert ev["summary"]["Au20_equivalent_detectability_band"] == "anchor_partial"

    def test_anchor_equivalent_metrics_mark_unavailable_without_matched_anchor(self):
        ev = _synthetic_design_result(
            "exosome_100nm",
            family="EV_sEV",
            peak=1.0,
            margin=3.0,
            stable_rate=0.8,
        )

        attach_anchor_equivalent_metrics([ev])

        assert ev["summary"]["Au20_anchor_available"] is False
        assert ev["summary"]["Au20_anchor_geometry_matched"] is False
        assert ev["summary"]["Au20_equivalent_peak_ratio"] is None
        assert ev["summary"]["Au20_equivalent_detectability_band"] == (
            "unavailable_no_geometry_matched_Au20_anchor"
        )

    def test_ev_design_score_keeps_hard_blocked_group_exploratory(self):
        ev_high_score = _synthetic_design_result(
            "exosome_100nm",
            family="EV_sEV",
            peak=2.0,
            margin=4.0,
            stable_rate=1.0,
            final_score=0.95,
            final_green_eligible=False,
            blocker_summary="assay_control_missing; ev_specificity_unvalidated",
        )
        ev_high_score["summary"].update(
            {
                "engineering_gate_passed": False,
                "Au20_anchor_available": True,
                "Au20_anchor_geometry_matched": True,
                "Au20_equivalent_peak_ratio": 2.0,
                "Au20_equivalent_margin_ratio": 2.0,
                "Au20_equivalent_stable_rate_ratio": 2.0,
            }
        )

        attach_ev_design_postprocess([ev_high_score])

        assert set(EV_DESIGN_POSTPROCESS_FIELDS).issubset(ev_high_score["summary"])
        assert ev_high_score["summary"]["ev_member_count"] == 1
        assert ev_high_score["summary"]["final_EV_design_score"] > 0.5
        assert ev_high_score["summary"]["EV_design_hard_blocker_flag"] is True
        assert ev_high_score["summary"]["EV_design_recommendation_band"] == (
            "exploratory_only"
        )
        assert "exploratory" in ev_high_score["summary"]["EV_design_claim_text"]

    def test_ev_design_score_allows_relative_ranking_when_absolute_green_blocked(self):
        ev_high_score = _synthetic_design_result(
            "exosome_100nm",
            family="EV_sEV",
            peak=2.0,
            margin=4.0,
            stable_rate=1.0,
            final_score=0.95,
            final_green_eligible=False,
            blocker_summary="detector_unit_chain_missing; measured_transfer_missing",
        )
        ev_high_score["summary"].update(
            {
                "relative_design_eligible": True,
                "within_lambda_design_eligible": True,
                "absolute_global_green_eligible": False,
                "Au20_anchor_available": True,
                "Au20_anchor_geometry_matched": True,
                "Au20_equivalent_peak_ratio": 2.0,
                "Au20_equivalent_margin_ratio": 2.0,
                "Au20_equivalent_stable_rate_ratio": 2.0,
                "reference_design_score": 1.0,
                "fluidic_practicality_penalty": 0.0,
                "EV_to_contaminant_signal_overlap": 0.0,
            }
        )

        attach_ev_design_postprocess([ev_high_score])

        assert ev_high_score["summary"]["EV_design_hard_blocker_flag"] is False
        assert ev_high_score["summary"]["ev_gate_pass_fraction"] == pytest.approx(1.0)
        assert ev_high_score["summary"]["EV_design_recommendation_band"] == (
            "recommended_candidate"
        )
        assert ev_high_score["summary"]["EV_design_recommendation_band_relative"] == (
            "recommended_candidate"
        )
        assert ev_high_score["summary"]["EV_design_recommendation_band_absolute"] == (
            "absolute_global_green_blocked"
        )
        assert "relative" in ev_high_score["summary"]["EV_design_claim_text"].lower()

    def test_ev_design_score_marks_detector_caution_without_hard_blocking(self):
        ev_high_score = _synthetic_design_result(
            "exosome_100nm",
            family="EV_sEV",
            peak=2.0,
            margin=4.0,
            stable_rate=1.0,
            final_score=0.95,
            final_green_eligible=False,
            blocker_summary="detector_operator_gate_not_passed",
        )
        ev_high_score["summary"].update(
            {
                "relative_design_eligible": True,
                "within_lambda_design_eligible": True,
                "detector_operator_caution_flag": True,
                "detector_operator_caution_reason": (
                    "detector_operator_large_or_missing_blocks_absolute_claim_only"
                ),
                "detector_resolved_relative_design_eligible": False,
                "relative_design_with_detector_caution": True,
                "absolute_global_green_eligible": False,
                "Au20_anchor_available": True,
                "Au20_anchor_geometry_matched": True,
                "Au20_equivalent_peak_ratio": 2.0,
                "Au20_equivalent_margin_ratio": 2.0,
                "Au20_equivalent_stable_rate_ratio": 2.0,
                "reference_design_score": 1.0,
                "fluidic_practicality_penalty": 0.0,
                "EV_to_contaminant_signal_overlap": 0.0,
            }
        )

        attach_ev_design_postprocess([ev_high_score])

        summary = ev_high_score["summary"]
        assert summary["EV_design_hard_blocker_flag"] is False
        assert summary["EV_design_detector_caution_flag"] is True
        assert summary["EV_design_detector_resolved_pass_fraction"] == pytest.approx(
            0.0
        )
        assert summary["EV_design_recommendation_band"] == "recommended_candidate"
        assert "detector" in summary["EV_design_claim_text"].lower()
        assert "relative/proxy" in summary["EV_design_claim_allowed_text"]

    def test_parameter_sweep_attaches_design_metrics_and_ev_postprocess(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 120)
        cfg = replace(
            make_ev_nodi_design_sweep_config(),
            total_time_s=0.04,
            sampling_rate_Hz=20000.0,
            noise_std=0.0,
            n_events=1,
            random_seed=21,
            tsuyama_phase_filter_grid_n=256,
        )
        gold20 = make_gold_baseline_particle(20, name="gold_20nm")
        exosome = make_biomimetic_exosome_particle(100)

        results = run_parameter_sweep(
            [gold20, exosome],
            WATER,
            np.array([BASELINE_CHANNEL.width_m]),
            np.array([BASELINE_CHANNEL.depth_m]),
            np.array([BASELINE_OPTICAL.wavelength_m]),
            BASELINE_OPTICAL,
            cfg,
            None,
            theta_grid,
            verbose=False,
            baseline_particle=gold20,
            baseline_channel=BASELINE_CHANNEL,
        )

        assert len(results) == 2
        for result in results:
            assert set(DESIGN_METRIC_DIAGNOSTIC_FIELDS).issubset(result["summary"])
            assert set(EV_DESIGN_POSTPROCESS_FIELDS).issubset(result["summary"])
        ev_result = next(
            result
            for result in results
            if result["intrinsic"]["particle_family"] == "EV_sEV"
        )
        assert ev_result["summary"]["engineering_gate_passed"] is False
        assert "n_detected<5" in ev_result["summary"]["engineering_gate_reason"]
        assert ev_result["summary"]["Au20_anchor_geometry_matched"] is True
        assert ev_result["summary"]["final_EV_design_score"] is not None
        assert ev_result["summary"]["EV_design_recommendation_band"] == (
            "exploratory_only"
        )

    def test_parameter_sweep_requires_theta_grid_before_cases_run(self, monkeypatch):
        def _unexpected_case_run(*args, **kwargs):
            raise AssertionError("case execution should not start without theta_grid_rad")

        monkeypatch.setattr(
            parameter_sweep_module,
            "run_single_case_batch",
            _unexpected_case_run,
        )

        with pytest.raises(ValueError, match="theta_grid_rad"):
            run_parameter_sweep(
                [BASELINE_PARTICLE],
                WATER,
                np.array([BASELINE_CHANNEL.width_m]),
                np.array([BASELINE_CHANNEL.depth_m]),
                np.array([BASELINE_OPTICAL.wavelength_m]),
                BASELINE_OPTICAL,
                replace(DEFAULT_SIM_CFG, n_events=1, normalization_mode="global_single_lambda"),
                E_sca_ref=1.0,
                theta_grid_rad=None,
                verbose=False,
            )

    def test_parameter_sweep_raises_on_case_failure_by_default(self, monkeypatch):
        def _failing_case(*args, **kwargs):
            raise RuntimeError("synthetic case failure")

        monkeypatch.setattr(parameter_sweep_module, "run_single_case_batch", _failing_case)

        with pytest.raises(RuntimeError, match="synthetic case failure"):
            run_parameter_sweep(
                [BASELINE_PARTICLE],
                WATER,
                np.array([BASELINE_CHANNEL.width_m]),
                np.array([BASELINE_CHANNEL.depth_m]),
                np.array([BASELINE_OPTICAL.wavelength_m]),
                BASELINE_OPTICAL,
                replace(DEFAULT_SIM_CFG, n_events=1, normalization_mode="global_single_lambda"),
                E_sca_ref=1.0,
                theta_grid_rad=np.linspace(0.01, np.pi - 0.01, 32),
                verbose=False,
            )

    def test_parameter_sweep_allows_partial_only_when_explicit(self, monkeypatch):
        def _failing_case(*args, **kwargs):
            raise RuntimeError("synthetic partial failure")

        monkeypatch.setattr(parameter_sweep_module, "run_single_case_batch", _failing_case)

        results = run_parameter_sweep(
            [BASELINE_PARTICLE],
            WATER,
            np.array([BASELINE_CHANNEL.width_m]),
            np.array([BASELINE_CHANNEL.depth_m]),
            np.array([BASELINE_OPTICAL.wavelength_m]),
            BASELINE_OPTICAL,
            replace(DEFAULT_SIM_CFG, n_events=1, normalization_mode="global_single_lambda"),
            E_sca_ref=1.0,
            theta_grid_rad=np.linspace(0.01, np.pi - 0.01, 64),
            verbose=False,
            allow_partial=True,
        )

        assert results == []


class TestSeedRobustness:
    def test_seed_replicate_summary_exports_stability_metrics(self):
        replicates = [
            {"seed": 1, "seed_score": 0.8, "engineering_gate_passed": True},
            {"seed": 2, "seed_score": 0.4, "engineering_gate_passed": False},
            {"seed": 3, "seed_score": 0.6, "engineering_gate_passed": True},
        ]

        metrics = summarize_seed_replicate_metrics(replicates)

        assert set(SEED_ROBUSTNESS_DIAGNOSTIC_FIELDS).issubset(metrics)
        assert metrics["seed_score_mean"] == pytest.approx(0.6)
        assert metrics["seed_score_std"] == pytest.approx(np.std([0.8, 0.4, 0.6]))
        assert metrics["seed_score_p10"] == pytest.approx(np.percentile([0.8, 0.4, 0.6], 10))
        assert metrics["seed_gate_pass_fraction"] == pytest.approx(2 / 3)
        assert 0.0 <= metrics["seed_rank_stability"] <= 1.0

    def test_run_seed_replicates_smoke_uses_candidate_case_only(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 120)
        cfg = replace(
            DEFAULT_SIM_CFG,
            total_time_s=0.08,
            sampling_rate_Hz=20000.0,
            noise_std=0.0,
            n_events=1,
            random_seed=1,
        )
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
            channel=BASELINE_CHANNEL,
            sim_cfg=cfg,
        )

        metrics = run_seed_replicates(
            {
                "particle": BASELINE_PARTICLE,
                "medium": WATER,
                "channel": BASELINE_CHANNEL,
                "optical": BASELINE_OPTICAL,
                "sim_cfg": cfg,
                "E_sca_ref": baseline["E_sca_ref"],
                "theta_grid_rad": theta_grid,
            },
            seeds=(1, 2),
        )

        assert set(SEED_ROBUSTNESS_DIAGNOSTIC_FIELDS).issubset(metrics)
        assert metrics["seed_replicate_count"] == 2
        assert metrics["seed_values"] == [1, 2]
        assert len(metrics["seed_scores"]) == 2
        assert 0.0 <= metrics["seed_gate_pass_fraction"] <= 1.0


class TestIntegration:
    def test_single_event_produces_pulse(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 500)
        baseline = compute_baseline_normalization(BASELINE_PARTICLE, WATER, BASELINE_OPTICAL, theta_grid)
        sim_cfg = SimulationConfig(
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.001,
            threshold_sigma=5.0,
            min_peak_width_s=2.5e-3,
            min_peak_interval_s=0.1,
            n_events=1,
            random_seed=42,
            rho=10.0,
        )
        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
        )
        assert batch["summary"]["n_detected"] >= 0

    def test_tsuyama_bfp_integrated_reference_fields_propagate_through_batch(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 180)
        cfg = SimulationConfig(
            total_time_s=0.08,
            sampling_rate_Hz=50000.0,
            mean_flow_velocity_m_s=2e-4,
            reference_model="tsuyama_bfp_integrated",
            tsuyama_phase_filter_grid_n=512,
            noise_std=0.0,
            n_events=1,
            random_seed=12,
        )
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
            channel=BASELINE_CHANNEL,
            sim_cfg=cfg,
        )
        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
        )
        for field in TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS:
            assert field in batch["summary"]
            assert field in batch["intrinsic"]
            assert field in batch["reference"]
        for field in REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS:
            assert field in batch["summary"]
            assert field in batch["intrinsic"]
            assert field in batch["reference"]
        assert batch["summary"]["reference_solver_route"] == "tsuyama_bfp_integrated"
        assert batch["summary"]["reference_detector_bridge_status"] == "surrogate_roi"
        assert batch["summary"]["reference_claim_level"] == (
            "paper_aligned_detector_resolved_comparison"
        )

    def test_bfp_roi_measured_mask_contract_propagates_without_absolute_claim(
        self,
        tmp_path,
    ):
        mask_path = tmp_path / "bfp_mask.csv"
        mask_path.write_text(
            "pixel_x,pixel_y,theta_rad,phi_rad,mask_weight,solid_angle_weight\n"
            "10,20,0.5,0.1,1.0,0.002\n",
            encoding="utf-8",
        )
        (tmp_path / "bfp_mask.csv.manifest.json").write_text(
            "{"
            '"calibration_kind":"bfp_roi_mask",'
            '"calibration_data_role":"experimental_measurement",'
            '"units":{'
            '"pixel_x":"pixel","pixel_y":"pixel","theta_rad":"rad",'
            '"phi_rad":"rad","mask_weight":"dimensionless",'
            '"solid_angle_weight":"sr"'
            "}"
            "}",
            encoding="utf-8",
        )
        theta_grid = np.linspace(0.01, np.pi - 0.01, 180)
        cfg = replace(
            DEFAULT_SIM_CFG,
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            noise_std=0.0,
            n_events=1,
            bfp_roi_mask_path=str(mask_path),
            bfp_to_angle_jacobian_applied=True,
        )
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            cfg,
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
        )
        for section in (batch["summary"], batch["intrinsic"], batch["reference"]):
            assert section["bfp_roi_mask_source"] == "calibrated_mask"
            assert section["bfp_roi_mask_status"] == (
                "calibrated_mask_contract_loaded"
            )
            assert section["bfp_roi_mask_gate_passed"] is True
            assert section["bfp_roi_mask_data_role"] == "experimental_measurement"
        assert batch["intrinsic"]["calibrated_quantitative_unlocked"] is False
        assert batch["reference"]["calibrated_quantitative_unlocked"] is False
        assert batch["intrinsic"]["detector_unit_claim_allowed"] is False
        assert batch["reference"]["detector_unit_claim_allowed"] is False

    def test_claim_state_machine_smoke_matrix_exports_route_and_boundaries(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 180)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        particle = make_biomimetic_exosome_particle(100)
        base_cfg = SimulationConfig(
            total_time_s=0.08,
            sampling_rate_Hz=50000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.0,
            n_events=1,
            random_seed=11,
            rho=10.0,
            tsuyama_phase_filter_grid_n=512,
        )
        configs = [
            replace(
                apply_readout_preset(base_cfg, "tsuyama_2024_paired_5sigma"),
                reference_model="channel_angular_surrogate",
            ),
            replace(
                apply_readout_preset(base_cfg, "tsuyama_2022_counting_10sigma"),
                reference_model="paper_aligned_phase_filter",
            ),
        ]
        for cfg in configs:
            batch = run_single_case_batch(
                particle,
                WATER,
                BASELINE_CHANNEL,
                BASELINE_OPTICAL,
                cfg,
                baseline["E_sca_ref"],
                theta_grid,
                retain_event_traces=False,
            )
            intrinsic = batch["intrinsic"]
            summary = batch["summary"]
            reference = batch["reference"]
            assert reference["reference_route"] in {
                "engineering_fallback",
                "paper_aligned_comparison",
            }
            assert intrinsic["output_claim_level"] in {
                "engineering_ranking",
                "paper_aligned_comparison",
                "engineering_diagnostic",
            }
            assert intrinsic["standard_particle_synthetic_fixture_active"] is False
            assert intrinsic["detector_unit_chain_status"].startswith("blocked_")
            assert intrinsic["detector_unit_claim_allowed"] is False
            assert intrinsic["pod_quantitative_route_status"].startswith("blocked_")
            assert summary["count_prediction_claim_level"] in {
                "not_applied_no_count_rate_claim",
                "concentration_to_count_surrogate_not_empirical",
                "per_event_only",
            }
            assert intrinsic["particle_optical_model"] == "core_shell_EV_sEV_surrogate"
            assert intrinsic["particle_family"] == "EV_sEV"
            assert intrinsic["particle_size_input_convention"] == (
                "diameter_nm_name_token_to_internal_radius_m"
            )
            assert intrinsic["particle_radius_m"] == pytest.approx(50e-9)
            assert intrinsic["particle_diameter_m"] == pytest.approx(100e-9)
            assert intrinsic["unit_axis_convention_hard_gate_passed"] is True
            assert intrinsic["mie_validation_status"] == "pass"
            assert intrinsic["wavelength_ranking_claim_level"] == (
                "within_lambda_geometry_ranking_only"
            )
            assert (
                intrinsic["absolute_or_calibrated_lambda_comparison_allowed"]
                is False
            )
            assert summary["unit_axis_convention_status"] == "pass"
            assert summary["lambda_score_comparability_band"] == "within_lambda_only"
            assert summary["objective_candidate_id"] == "current_control"
            assert summary["objective_design_claim_level"] == (
                "single_profile_relative_only"
            )
            assert summary["objective_panel_status"] == (
                "synthetic_candidate_refinement_active"
            )
            assert summary["objective_panel_recommendation"] is not None
            assert summary["ev_population_prior_status"] in {
                "correlated_prior_scaffold_active",
                "not_applicable_non_ev_particle",
            }
            assert summary["safe_power_claim_level"] == (
                "blocked_missing_probe_power_metadata"
            )
            assert summary["optical_exposure_safety_gate_passed"] is False
            assert reference["channel_width_axis"] == "x"
            assert reference["flow_axis_convention"] == "y"
            assert reference["cross_wavelength_claim_gate_passed"] is False
            assert reference["objective_profile_schema_present"] is True
            assert reference["ev_photodamage_risk_band"] == (
                "unknown_missing_probe_power_metadata"
            )
            for field in MINIMUM_OUTPUT_SCHEMA_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in EVENT_QC_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in SELECTION_FUNCTION_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in EV_POPULATION_PRIOR_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in CHANNEL_GEOMETRY_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in ELECTROKINETIC_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in EV_INTEGRITY_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in EV_REPORTING_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in ASSAY_CONTROL_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in RECOMPUTE_MANIFEST_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in BFP_DETECTOR_OPERATOR_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in PARTICLE_CHANNEL_PERTURBATION_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in OBJECTIVE_PANEL_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in FLUIDIC_RESISTANCE_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            for field in PARTICLE_DESIGN_LIBRARY_DIAGNOSTIC_FIELDS:
                assert field in summary
                assert field in intrinsic
                assert field in reference
            assert summary["case_id"].startswith(
                f"{particle.name}|W={round(BASELINE_CHANNEL.width_m * 1e9)}nm"
            )
            assert summary["particle_preset_id"] == particle.name
            assert summary["manifest_id"].startswith("manifest_")
            assert summary["recompute_manifest_gate_passed"] is True
            assert summary["config_hash"].startswith("config_")
            assert summary["rng_stream_id"]
            assert summary["event_qc_status"] == "batch_surrogate_active"
            assert (
                summary["detected_rate_after_event_qc"]
                <= summary["detection_rate"]
            )
            assert summary["selection_function_status"] == (
                "single_case_detection_qc_skeleton_active"
            )
            assert "population_inversion_unavailable" in summary[
                "selection_bias_warning"
            ]
            assert summary["channel_cross_section_model"] == "ideal_rectangle"
            assert summary["geometry_claim_level"] == (
                "nominal_ideal_rectangle_geometry_only"
            )
            assert summary["electrostatic_confinement_flag"] == (
                "unavailable_missing_ionic_strength"
            )
            assert summary["ev_integrity_claim_level"] == (
                "geometry_surrogate_integrity_risk_not_validated"
            )
            assert summary["ev_biological_specificity_claim_allowed"] is False
            assert summary["ev_sample_identity_claim_level"] == (
                "EV_like_optical_particle_metadata_incomplete"
            )
            assert summary["assay_control_readiness_score"] == pytest.approx(0.0)
            assert summary["assay_control_gate_passed"] is False
            assert summary["detector_operator_disagreement_band"] in {
                "small",
                "moderate",
                "large",
            }
            assert summary["detector_operator_comparison_lane_status"] == (
                "roi_complex_mode_overlap_comparison_active"
            )
            assert summary["bfp_roi_mask_status"] == (
                "not_configured_current_radian_surrogate_mask"
            )
            assert summary["roi_vs_scalar_signal_ratio"] is not None
            assert summary["mode_overlap_efficiency"] is not None
            assert summary["particle_channel_perturbation_application_mode"] == (
                "diagnostic_only"
            )
            assert summary["double_counting_risk_band"] == (
                "none_no_particle_channel_perturbation_added"
            )
            assert summary["no_double_count_guard_passed"] is True
            assert summary["particle_channel_double_count_guard_status"] == (
                "pass_no_particle_channel_term_added"
            )
            assert summary["reference_operating_point_status"] == (
                "relative_proxy_active"
            )
            assert summary["reference_operating_band"] in {
                "balanced",
                "electronics_noise_limited_useful",
                "shot_noise_limited_no_gain",
                "reference_too_weak",
            }
            assert summary["fluidic_practicality_status"] == (
                "static_hydraulic_proxy_active"
            )
            assert 0.0 <= summary["fluidic_practicality_penalty"] <= 1.0
            assert summary["EV_sample_preparation_profile"] == "unknown"
            assert summary["EV_specificity_risk"] == (
                "proxy_overlap_requires_contaminant_panel"
            )
            assert summary["final_green_eligible"] is False
            assert summary["final_recommendation_band"] in {
                "yellow_detector_operator_caution",
                "yellow_max_pending_gate_closure",
            }
            assert "recompute_manifest_missing" not in summary[
                "primary_blocker_summary"
            ]

        template_path = REPO_ROOT / "calibration" / "reference_blank_channel_template.csv"
        synthetic_cfg = replace(
            base_cfg,
            reference_model="calibrated_lookup",
            reference_calibration_path=str(template_path),
        )
        with pytest.raises(ValueError, match="synthetic/template fixture"):
            compute_reference_field(BASELINE_CHANNEL, BASELINE_OPTICAL, synthetic_cfg)

    def test_batch_position_variation(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 500)
        baseline = compute_baseline_normalization(BASELINE_PARTICLE, WATER, BASELINE_OPTICAL, theta_grid)
        sim_cfg = SimulationConfig(
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.0,
            n_events=10,
            random_seed=42,
            rho=10.0,
        )
        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
        )
        positions = [event["initial_position"] for event in batch["events"]]
        x_positions = [position[0] for position in positions]
        assert len(set(f"{x:.10e}" for x in x_positions)) > 1

    def test_batch_summary_exports_center_biased_position_diagnostics(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 500)
        baseline = compute_baseline_normalization(BASELINE_PARTICLE, WATER, BASELINE_OPTICAL, theta_grid)
        sim_cfg = SimulationConfig(
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.0,
            n_events=8,
            random_seed=42,
            rho=10.0,
            initial_position_distribution_mode="center_biased_surrogate",
            initial_position_center_bias_strength=1.5,
            initial_position_center_bias_min_confinement_ratio=0.05,
        )
        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
        )
        summary = batch["summary"]
        intrinsic = batch["intrinsic"]
        assert summary["initial_position_distribution_mode"] == "center_biased_surrogate"
        assert summary["initial_position_distribution_active_fraction"] > 0.0
        assert summary["mean_abs_initial_x_norm"] < 0.5
        assert summary["mean_abs_initial_z_norm"] < 0.5
        assert summary["mean_initial_position_center_bias_x_exponent"] > 1.0
        assert summary["mean_initial_position_center_bias_z_exponent"] > 1.0
        assert intrinsic["initial_position_distribution_mode"] == "center_biased_surrogate"
        assert "initial_position_distribution_mode=center_biased_surrogate" in intrinsic["observation_signature"]

    def test_batch_supports_sobol_sampling_and_adaptive_event_budget(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 160)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        sim_cfg = SimulationConfig(
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.0,
            post_readout_noise_std=0.0,
            n_events=10,
            random_seed=42,
            random_sequence_policy="case_keyed_independent",
            event_sampling_policy="sobol_stratified",
            adaptive_event_budget_mode="wilson_precision",
            adaptive_min_events=4,
            adaptive_check_interval=2,
            adaptive_wilson_half_width_target=0.5,
            rho=10.0,
        )

        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
        )
        summary = batch["summary"]

        assert summary["random_sequence_policy"] == "case_keyed_independent"
        assert summary["event_sampling_policy"] == "sobol_stratified"
        assert summary["event_position_low_variance_sampling"] is True
        assert summary["adaptive_event_budget_mode"] == "wilson_precision"
        assert summary["adaptive_event_budget_requested_events"] == 10
        assert summary["adaptive_event_budget_actual_events"] == summary["n_events"]
        assert summary["adaptive_event_budget_actual_events"] == 4
        assert summary["adaptive_event_budget_stopped_early"] is True
        assert summary["adaptive_event_budget_stop_reason"] == "wilson_precision_target_met"
        assert len(batch["events"]) == 4

    def test_batch_summary_exports_rho_physical_envelope_diagnostics(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 500)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE, WATER, BASELINE_OPTICAL, theta_grid
        )
        sim_cfg = SimulationConfig(
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.0,
            n_events=4,
            random_seed=42,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
        )
        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
        )
        summary = batch["summary"]
        reference = batch["reference"]
        g_ref_geometry = reference.get("g_ref_geometry", reference["g_ref"])
        expected_nominal = (
            reference["reference_field_amplitude_envelope_nominal"]
            / g_ref_geometry
        )
        assert summary["rho_requested"] == pytest.approx(sim_cfg.rho)
        assert reference["rho_physical_envelope_source"] == (
            "reference_field_amplitude_envelope / g_ref_geometry"
        )
        assert summary["rho_physical_envelope_nominal"] == pytest.approx(expected_nominal)
        assert reference["rho_physical_envelope_lower"] == pytest.approx(0.5 * expected_nominal)
        assert reference["rho_physical_envelope_upper"] == pytest.approx(2.0 * expected_nominal)
        assert summary["rho_physical_envelope_status"] in {
            "below_envelope",
            "within_envelope",
            "above_envelope",
        }
        assert batch["events"][0]["rho_physical_envelope_nominal"] == pytest.approx(
            expected_nominal
        )

    def test_batch_summary_exports_na_cutoff_and_illumination_mode(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 500)
        sim_cfg = SimulationConfig(
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.0,
            n_events=4,
            random_seed=42,
            rho=10.0,
            reference_model="channel_angular_surrogate",
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            illumination_mode="overfill",
        )
        optical = replace(BASELINE_OPTICAL, wavelength_m=660e-9, NA_collection=0.9)
        blocked_channel = Channel(700e-9, 550e-9)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            optical,
            theta_grid,
            channel=blocked_channel,
            sim_cfg=sim_cfg,
        )
        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            blocked_channel,
            optical,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
        )
        reference = batch["reference"]
        assert reference["illumination_mode"] == "overfill"
        assert reference["na_cutoff_active"] is True
        assert reference["na_cutoff_NA_collection"] == pytest.approx(0.9)
        assert reference["na_cutoff_W_min_m"] == pytest.approx(660e-9 / 0.9)
        assert reference["A_ref"] == pytest.approx(0.0)

    def test_summary_only_batch_keeps_summary_but_omits_full_event_traces(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 500)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        sim_cfg = SimulationConfig(
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.0,
            n_events=4,
            random_seed=42,
            rho=10.0,
        )
        full_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
        )
        slim_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
        )
        assert slim_batch["summary"] == full_batch["summary"]
        assert "trajectory" not in slim_batch["events"][0]
        assert "signal_trace" not in slim_batch["events"][0]
        assert "event_max_margin_z" in slim_batch["events"][0]

    def test_stream_summary_only_matches_slim_batch_summary(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 500)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        sim_cfg = SimulationConfig(
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.0,
            n_events=8,
            random_seed=42,
            rho=10.0,
        )
        slim_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
        )
        stream_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )
        assert stream_batch["summary"] == slim_batch["summary"]
        assert stream_batch["events"] == []

    def test_vectorized_pure_advection_block_matches_stream_summary_metrics(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 240)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        base_cfg = SimulationConfig(
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.0,
            shot_noise_scale=0.0,
            post_readout_noise_std=0.0,
            n_events=8,
            random_seed=42,
            random_sequence_policy="case_keyed_independent",
            event_sampling_policy="sobol_stratified",
            rho=10.0,
        )
        scalar_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            replace(base_cfg, vectorized_event_engine="off"),
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )
        vector_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            replace(
                base_cfg,
                vectorized_event_engine="pure_advection_block",
                event_block_size=4,
            ),
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )

        scalar_summary = scalar_batch["summary"]
        vector_summary = vector_batch["summary"]
        assert vector_batch["events"] == []
        assert scalar_summary["vectorized_event_rng_order"] == "event_loop_order"
        assert vector_summary["vectorized_event_engine_used"] == "pure_advection_block"
        assert vector_summary["vectorized_event_engine_fallback_reason"] is None
        assert vector_summary["vectorized_event_rng_order"] == "block_batched_order"
        assert vector_summary["n_events"] == scalar_summary["n_events"]
        for field in (
            "detection_rate",
            "stable_detection_rate",
            "mean_peak_height",
            "mean_peak_width_s",
            "mean_local_snr",
            "mean_transit_time_s",
            "mean_A_ref_local",
            "mean_A_sca_local",
            "mean_reference_to_scattering_amplitude_ratio",
        ):
            assert vector_summary[field] == pytest.approx(
                scalar_summary[field],
                rel=1e-9,
                abs=1e-18,
            )

    def test_vectorized_fallback_telemetry_aggregates_reasons_and_denominators(self):
        telemetry = parameter_sweep_module.summarize_vectorized_fallback_telemetry(
            [
                {
                    "summary": {
                        "n_events": 4,
                        "vectorized_event_engine": "off",
                        "vectorized_event_engine_used": "off",
                        "vectorized_event_engine_fallback_reason": "disabled",
                    }
                },
                {
                    "summary": {
                        "n_events": 6,
                        "vectorized_event_engine": "event_block_v3",
                        "vectorized_event_engine_used": "event_block_v3",
                        "vectorized_event_engine_fallback_reason": None,
                    }
                },
                {
                    "summary": {
                        "n_events": 2,
                        "vectorized_event_engine": "event_block_v3",
                        "vectorized_event_engine_used": "event_loop_fallback",
                        "vectorized_event_engine_fallback_reason": (
                            "adaptive_budget_requires_event_loop"
                        ),
                    }
                },
            ]
        )

        assert telemetry["telemetry_schema"] == "vectorized_fallback_telemetry_v1"
        assert telemetry["case_count"] == 3
        assert telemetry["event_count"] == 12
        assert telemetry["configured_off_case_count"] == 1
        assert telemetry["vectorized_requested_case_count"] == 2
        assert telemetry["vectorized_fallback_case_count"] == 1
        assert telemetry["vectorized_fallback_event_count"] == 2
        assert telemetry["vectorized_fallback_fraction_of_requested_cases"] == 0.5
        assert telemetry["fallback_reason_counts"] == {
            "<none>": 1,
            "adaptive_budget_requires_event_loop": 1,
            "disabled": 1,
        }
        assert telemetry["vectorized_requested_fallback_reason_counts"] == {
            "<none>": 1,
            "adaptive_budget_requires_event_loop": 1,
        }

    def test_vectorized_pure_advection_block_preserves_random_position_order(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 240)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        base_cfg = SimulationConfig(
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.0,
            shot_noise_scale=0.0,
            post_readout_noise_std=0.0,
            n_events=8,
            random_seed=42,
            event_sampling_policy="random",
            rho=10.0,
        )
        scalar_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            replace(base_cfg, vectorized_event_engine="off"),
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )
        vector_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            replace(
                base_cfg,
                vectorized_event_engine="pure_advection_block",
                event_block_size=4,
            ),
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )

        scalar_summary = scalar_batch["summary"]
        vector_summary = vector_batch["summary"]
        assert vector_summary["vectorized_event_engine_used"] == "pure_advection_block"
        for field in (
            "detection_rate",
            "stable_detection_rate",
            "mean_peak_height",
            "mean_peak_width_s",
            "mean_local_snr",
            "mean_transit_time_s",
            "mean_abs_initial_x_norm",
            "mean_abs_initial_z_norm",
        ):
            assert vector_summary[field] == pytest.approx(
                scalar_summary[field],
                rel=1e-9,
                abs=1e-18,
            )

    def test_vectorized_pure_advection_block_matches_no_peak_fast_path(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 160)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        base_cfg = SimulationConfig(
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.01,
            shot_noise_scale=0.0,
            post_readout_noise_std=0.0,
            threshold_sigma=1.0e6,
            n_events=8,
            random_seed=42,
            random_sequence_policy="case_keyed_independent",
            event_sampling_policy="sobol_stratified",
            rho=10.0,
        )
        scalar_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            replace(base_cfg, vectorized_event_engine="off"),
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )
        vector_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            replace(
                base_cfg,
                vectorized_event_engine="pure_advection_block",
                event_block_size=4,
            ),
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )

        scalar_summary = scalar_batch["summary"]
        vector_summary = vector_batch["summary"]
        assert scalar_summary["n_detected"] == 0
        assert vector_summary["n_detected"] == 0
        assert vector_summary["vectorized_event_engine_used"] == "pure_advection_block"
        for field in (
            "detection_rate",
            "stable_detection_rate",
            "mean_peak_height",
            "mean_peak_width_s",
            "mean_threshold",
            "mean_threshold_robust_std",
            "mean_local_snr",
        ):
            assert vector_summary[field] == pytest.approx(
                scalar_summary[field],
                rel=1e-9,
                abs=1e-18,
            )

    def test_vectorized_pure_advection_block_records_batched_rng_order_with_noise(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 160)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        sim_cfg = SimulationConfig(
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.01,
            shot_noise_scale=1e-4,
            post_readout_noise_std=1e-4,
            n_events=4,
            random_seed=42,
            random_sequence_policy="case_keyed_independent",
            event_sampling_policy="sobol_stratified",
            vectorized_event_engine="pure_advection_block",
            event_block_size=4,
            rho=10.0,
        )
        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )
        summary = batch["summary"]

        assert summary["vectorized_event_engine_used"] == "pure_advection_block"
        assert summary["vectorized_event_rng_order"] == "block_batched_order"
        assert summary["n_events"] == sim_cfg.n_events
        assert math.isfinite(summary["mean_peak_height"])
        assert math.isfinite(summary["mean_threshold"])

    def test_vectorized_pure_advection_block_falls_back_for_diffusion(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 160)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        sim_cfg = SimulationConfig(
            total_time_s=0.08,
            sampling_rate_Hz=10000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            noise_std=0.0,
            post_readout_noise_std=0.0,
            n_events=2,
            random_seed=42,
            vectorized_event_engine="pure_advection_block",
            event_block_size=4,
            rho=10.0,
        )
        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )
        summary = batch["summary"]
        assert summary["vectorized_event_engine"] == "pure_advection_block"
        assert summary["vectorized_event_engine_used"] == "event_loop_fallback"
        assert summary["vectorized_event_engine_fallback_reason"] == "diffusion_enabled"
        assert summary["vectorized_event_rng_order"] == "event_loop_order"

    def test_diffusive_trajectory_block_matches_scalar_rng_order(self):
        sim_cfg = SimulationConfig(
            total_time_s=0.02,
            sampling_rate_Hz=1000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
            n_events=3,
            random_seed=42,
        )
        channel = Channel(800e-9, 500e-9)
        context = build_trajectory_context(
            channel,
            sim_cfg,
            particle_radius_m=BASELINE_PARTICLE.radius_m,
        )
        x0 = np.array([-1.0e-7, 0.0, 1.2e-7])
        z0 = np.array([-8.0e-8, 4.0e-8, 9.0e-8])
        diffusion_coefficient = 1.5e-12

        scalar_rng = np.random.default_rng(123)
        scalar = [
            simulate_particle_trajectory(
                channel,
                BASELINE_OPTICAL,
                sim_cfg,
                float(x_val),
                float(z_val),
                particle_radius_m=BASELINE_PARTICLE.radius_m,
                diffusion_coefficient=diffusion_coefficient,
                rng=scalar_rng,
                trajectory_context=context,
            )
            for x_val, z_val in zip(x0, z0)
        ]
        block = simulate_particle_trajectory_block(
            channel,
            BASELINE_OPTICAL,
            sim_cfg,
            x0,
            z0,
            particle_radius_m=BASELINE_PARTICLE.radius_m,
            diffusion_coefficient=diffusion_coefficient,
            rng=np.random.default_rng(123),
            trajectory_context=context,
        )

        for key in ("x_m", "y_m", "z_m", "v_y_m_s"):
            expected = np.vstack([event[key] for event in scalar])
            assert block[key] == pytest.approx(expected, rel=1e-12, abs=1e-18)
        assert block["time_s"] == pytest.approx(context.time_s)

    def test_plug_diffusive_trajectory_block_matches_scalar_rng_order(self):
        sim_cfg = SimulationConfig(
            total_time_s=0.02,
            sampling_rate_Hz=1000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            flow_profile_model="plug",
            diffusion_hindrance_model="none",
            n_events=3,
            random_seed=42,
        )
        channel = Channel(800e-9, 500e-9)
        context = build_trajectory_context(
            channel,
            sim_cfg,
            particle_radius_m=BASELINE_PARTICLE.radius_m,
        )
        x0 = np.array([-1.0e-7, 0.0, 1.2e-7])
        z0 = np.array([-8.0e-8, 4.0e-8, 9.0e-8])
        diffusion_coefficient = 1.5e-12

        scalar_rng = np.random.default_rng(123)
        scalar = [
            simulate_particle_trajectory(
                channel,
                BASELINE_OPTICAL,
                sim_cfg,
                float(x_val),
                float(z_val),
                particle_radius_m=BASELINE_PARTICLE.radius_m,
                diffusion_coefficient=diffusion_coefficient,
                rng=scalar_rng,
                trajectory_context=context,
            )
            for x_val, z_val in zip(x0, z0)
        ]
        block = simulate_particle_trajectory_block(
            channel,
            BASELINE_OPTICAL,
            sim_cfg,
            x0,
            z0,
            particle_radius_m=BASELINE_PARTICLE.radius_m,
            diffusion_coefficient=diffusion_coefficient,
            rng=np.random.default_rng(123),
            trajectory_context=context,
        )

        for key in ("x_m", "y_m", "z_m", "v_y_m_s"):
            expected = np.vstack([event[key] for event in scalar])
            assert block[key] == pytest.approx(expected, rel=1e-12, abs=1e-18)
        assert block["time_s"] == pytest.approx(context.time_s)

    def test_block_trajectory_can_skip_velocity_trace_without_position_drift(self):
        sim_cfg = SimulationConfig(
            total_time_s=0.02,
            sampling_rate_Hz=1000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
        )
        channel = Channel(800e-9, 500e-9)
        context = build_trajectory_context(
            channel,
            sim_cfg,
            particle_radius_m=BASELINE_PARTICLE.radius_m,
        )
        x0 = np.array([-1.0e-7, 0.0, 1.2e-7])
        z0 = np.array([-8.0e-8, 4.0e-8, 9.0e-8])
        diffusion_coefficient = 1.5e-12

        full = simulate_particle_trajectory_block(
            channel,
            BASELINE_OPTICAL,
            sim_cfg,
            x0,
            z0,
            particle_radius_m=BASELINE_PARTICLE.radius_m,
            diffusion_coefficient=diffusion_coefficient,
            rng=np.random.default_rng(123),
            trajectory_context=context,
        )
        light = simulate_particle_trajectory_block(
            channel,
            BASELINE_OPTICAL,
            sim_cfg,
            x0,
            z0,
            particle_radius_m=BASELINE_PARTICLE.radius_m,
            diffusion_coefficient=diffusion_coefficient,
            rng=np.random.default_rng(123),
            trajectory_context=context,
            export_velocity_trace=False,
        )

        for key in ("time_s", "x_m", "y_m", "z_m"):
            np.testing.assert_allclose(light[key], full[key], rtol=0.0, atol=0.0)
        assert "v_y_m_s" not in light

    def test_event_block_v2_matches_noiseless_diffusion_stream_summary(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 160)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        base_cfg = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=2000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
            noise_std=0.0,
            shot_noise_scale=0.0,
            post_readout_noise_std=0.0,
            n_events=6,
            random_seed=42,
            random_sequence_policy="case_keyed_independent",
            event_sampling_policy="sobol_stratified",
            rho=10.0,
        )
        scalar_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            replace(base_cfg, vectorized_event_engine="off"),
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )
        vector_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            replace(
                base_cfg,
                vectorized_event_engine="event_block_v2",
                event_block_size=3,
            ),
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )

        scalar_summary = scalar_batch["summary"]
        vector_summary = vector_batch["summary"]
        assert vector_batch["events"] == []
        assert vector_summary["vectorized_event_engine_used"] == "event_block_v2"
        assert vector_summary["vectorized_event_engine_fallback_reason"] is None
        assert vector_summary["vectorized_event_rng_order"] == (
            "event_loop_order_blocked_summary"
        )
        for field in (
            "detection_rate",
            "stable_detection_rate",
            "mean_peak_height",
            "mean_peak_width_s",
            "mean_local_snr",
            "mean_transit_time_s",
            "mean_abs_initial_x_norm",
            "mean_abs_initial_z_norm",
        ):
            assert vector_summary[field] == pytest.approx(
                scalar_summary[field],
                rel=1e-9,
                abs=1e-18,
            )

    def test_event_block_v2_preserves_scalar_noise_order_for_sobol_summary(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 160)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        base_cfg = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=2000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
            noise_std=0.01,
            shot_noise_scale=1e-4,
            post_readout_noise_std=1e-4,
            n_events=4,
            random_seed=42,
            random_sequence_policy="case_keyed_independent",
            event_sampling_policy="sobol_stratified",
            rho=10.0,
        )
        scalar_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            replace(base_cfg, vectorized_event_engine="off"),
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )
        vector_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            replace(
                base_cfg,
                vectorized_event_engine="event_block_v2",
                event_block_size=2,
            ),
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )

        scalar_summary = scalar_batch["summary"]
        vector_summary = vector_batch["summary"]
        assert vector_summary["vectorized_event_rng_order"] == (
            "event_loop_order_blocked_summary"
        )
        for field in (
            "detection_rate",
            "stable_detection_rate",
            "mean_peak_height",
            "mean_peak_width_s",
            "mean_threshold",
            "mean_threshold_robust_std",
            "mean_local_snr",
            "mean_shot_noise_std",
        ):
            rel_tol = 5e-5 if field == "mean_local_snr" else 1e-5
            assert vector_summary[field] == pytest.approx(
                scalar_summary[field],
                rel=rel_tol,
                abs=1e-12,
            )

    def test_event_block_v2_block_size_does_not_change_sobol_summary(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 160)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        base_cfg = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=2000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
            noise_std=0.01,
            shot_noise_scale=1e-4,
            post_readout_noise_std=1e-4,
            n_events=6,
            random_seed=42,
            random_sequence_policy="case_keyed_independent",
            event_sampling_policy="sobol_stratified",
            rho=10.0,
        )
        summaries = {}
        for block_size in (1, 2, 3, 6):
            batch = run_single_case_batch(
                BASELINE_PARTICLE,
                WATER,
                BASELINE_CHANNEL,
                BASELINE_OPTICAL,
                replace(
                    base_cfg,
                    vectorized_event_engine="event_block_v2",
                    event_block_size=block_size,
                ),
                baseline["E_sca_ref"],
                theta_grid,
                retain_event_traces=False,
                stream_summary_only=True,
            )
            summaries[block_size] = batch["summary"]

        reference_summary = summaries[1]
        for block_size, summary in summaries.items():
            assert summary["vectorized_event_engine_used"] == "event_block_v2"
            assert summary["event_block_size"] == block_size
            assert summary["vectorized_event_rng_order"] == (
                "event_loop_order_blocked_summary"
            )
            for field in (
                "detection_rate",
                "stable_detection_rate",
                "mean_peak_height",
                "mean_peak_width_s",
                "mean_threshold",
                "mean_threshold_robust_std",
                "mean_local_snr",
                "mean_shot_noise_std",
            ):
                assert summary[field] == pytest.approx(
                    reference_summary[field],
                    rel=1e-12,
                    abs=1e-15,
                )

    def test_event_block_v2_adaptive_budget_matches_scalar_stop(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 160)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        base_cfg = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=2000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
            noise_std=0.0,
            shot_noise_scale=0.0,
            post_readout_noise_std=0.0,
            n_events=12,
            random_seed=42,
            random_sequence_policy="case_keyed_independent",
            event_sampling_policy="sobol_stratified",
            adaptive_event_budget_mode="wilson_precision",
            adaptive_min_events=4,
            adaptive_check_interval=2,
            adaptive_wilson_half_width_target=0.6,
            rho=10.0,
        )
        scalar_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            replace(base_cfg, vectorized_event_engine="off"),
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )
        vector_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            replace(
                base_cfg,
                vectorized_event_engine="event_block_v2",
                event_block_size=5,
            ),
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )

        scalar_summary = scalar_batch["summary"]
        vector_summary = vector_batch["summary"]
        assert vector_batch["events"] == []
        assert vector_summary["vectorized_event_engine_used"] == "event_block_v2"
        assert vector_summary["adaptive_event_budget_requested_events"] == 12
        assert vector_summary["adaptive_event_budget_actual_events"] == 4
        assert vector_summary["adaptive_event_budget_stopped_early"] is True
        assert vector_summary["adaptive_event_budget_stop_reason"] == (
            "wilson_precision_target_met"
        )
        for field in (
            "n_events",
            "detection_rate",
            "stable_detection_rate",
            "adaptive_event_budget_actual_events",
            "adaptive_event_budget_max_half_width",
            "adaptive_event_budget_detection_half_width",
            "adaptive_event_budget_stable_half_width",
        ):
            assert vector_summary[field] == pytest.approx(
                scalar_summary[field],
                rel=1e-12,
                abs=1e-15,
            )

    def test_event_block_v2_records_random_policy_rng_order(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 160)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        sim_cfg = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=2000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
            noise_std=0.0,
            shot_noise_scale=0.0,
            post_readout_noise_std=0.0,
            n_events=5,
            random_seed=42,
            random_sequence_policy="case_keyed_independent",
            event_sampling_policy="random",
            vectorized_event_engine="event_block_v2",
            event_block_size=2,
            rho=10.0,
        )
        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )
        summary = batch["summary"]

        assert summary["event_sampling_policy"] == "random"
        assert summary["event_position_low_variance_sampling"] is False
        assert summary["vectorized_event_engine_used"] == "event_block_v2"
        assert summary["vectorized_event_rng_order"] == (
            "block_position_order_event_noise_order"
        )
        assert summary["n_events"] == 5
        assert math.isfinite(summary["detection_rate"])
        assert math.isfinite(summary["mean_abs_initial_x_norm"])
        assert math.isfinite(summary["mean_abs_initial_z_norm"])

    def test_event_block_v2_falls_back_when_event_traces_are_retained(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 160)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        sim_cfg = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=2000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
            noise_std=0.0,
            shot_noise_scale=0.0,
            post_readout_noise_std=0.0,
            n_events=2,
            random_seed=42,
            random_sequence_policy="case_keyed_independent",
            event_sampling_policy="sobol_stratified",
            vectorized_event_engine="event_block_v2",
            event_block_size=2,
            rho=10.0,
        )
        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=True,
            stream_summary_only=False,
        )
        summary = batch["summary"]

        assert len(batch["events"]) == 2
        assert summary["vectorized_event_engine"] == "event_block_v2"
        assert summary["vectorized_event_engine_used"] == "event_loop_fallback"
        assert summary["vectorized_event_engine_fallback_reason"] == (
            "requires_stream_summary_without_event_traces"
        )
        assert summary["vectorized_event_rng_order"] == "event_loop_order"

    def test_event_block_v3_matches_scalar_noisy_sobol_summary(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 160)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        base_cfg = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=2000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
            noise_std=0.01,
            shot_noise_scale=1e-4,
            post_readout_noise_std=1e-4,
            n_events=6,
            random_seed=42,
            random_sequence_policy="case_keyed_independent",
            event_sampling_policy="sobol_stratified",
            rho=10.0,
        )
        scalar_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            replace(base_cfg, vectorized_event_engine="off"),
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )
        vector_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            replace(
                base_cfg,
                vectorized_event_engine="event_block_v3",
                event_block_size=3,
            ),
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )

        scalar_summary = scalar_batch["summary"]
        vector_summary = vector_batch["summary"]
        assert vector_batch["events"] == []
        assert vector_summary["vectorized_event_engine_used"] == "event_block_v3"
        assert vector_summary["vectorized_event_engine_fallback_reason"] is None
        assert vector_summary["vectorized_event_rng_order"] == (
            "event_loop_order_blocked_vectorized_summary"
        )
        for field in (
            "detection_rate",
            "stable_detection_rate",
            "mean_peak_height",
            "mean_peak_width_s",
            "mean_threshold",
            "mean_threshold_robust_std",
            "mean_local_snr",
            "mean_shot_noise_std",
        ):
            rel_tol = 5e-5 if field == "mean_local_snr" else 1e-9
            assert vector_summary[field] == pytest.approx(
                scalar_summary[field],
                rel=rel_tol,
                abs=1e-12,
            )

    def test_event_block_v3_block_size_does_not_change_sobol_summary(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 160)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        base_cfg = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=2000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
            noise_std=0.01,
            shot_noise_scale=1e-4,
            post_readout_noise_std=1e-4,
            n_events=6,
            random_seed=42,
            random_sequence_policy="case_keyed_independent",
            event_sampling_policy="sobol_stratified",
            rho=10.0,
        )
        summaries = {}
        for block_size in (1, 2, 3, 6):
            batch = run_single_case_batch(
                BASELINE_PARTICLE,
                WATER,
                BASELINE_CHANNEL,
                BASELINE_OPTICAL,
                replace(
                    base_cfg,
                    vectorized_event_engine="event_block_v3",
                    event_block_size=block_size,
                ),
                baseline["E_sca_ref"],
                theta_grid,
                retain_event_traces=False,
                stream_summary_only=True,
            )
            summaries[block_size] = batch["summary"]

        reference_summary = summaries[1]
        for block_size, summary in summaries.items():
            assert summary["vectorized_event_engine_used"] == "event_block_v3"
            assert summary["event_block_size"] == block_size
            assert summary["vectorized_event_rng_order"] == (
                "event_loop_order_blocked_vectorized_summary"
            )
            for field in (
                "detection_rate",
                "stable_detection_rate",
                "mean_peak_height",
                "mean_peak_width_s",
            ):
                assert summary[field] == pytest.approx(
                    reference_summary[field],
                    rel=1e-12,
                    abs=1e-15,
                )

    def test_event_block_v3_block_lane_rng_order_is_block_size_stable(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 160)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        base_cfg = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=2000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
            noise_std=0.01,
            shot_noise_scale=1e-4,
            post_readout_noise_std=1e-4,
            n_events=6,
            random_seed=42,
            random_sequence_policy="case_keyed_independent",
            event_sampling_policy="sobol_stratified",
            event_block_rng_order="block_lane_order",
            rho=10.0,
        )
        summaries = {}
        for block_size in (1, 2, 3, 6):
            batch = run_single_case_batch(
                BASELINE_PARTICLE,
                WATER,
                BASELINE_CHANNEL,
                BASELINE_OPTICAL,
                replace(
                    base_cfg,
                    vectorized_event_engine="event_block_v3",
                    event_block_size=block_size,
                ),
                baseline["E_sca_ref"],
                theta_grid,
                retain_event_traces=False,
                stream_summary_only=True,
            )
            summaries[block_size] = batch["summary"]

        reference_summary = summaries[1]
        for block_size, summary in summaries.items():
            assert summary["vectorized_event_engine_used"] == "event_block_v3"
            assert summary["event_block_size"] == block_size
            assert summary["event_block_rng_order"] == "block_lane_order"
            assert summary["vectorized_event_rng_order"] == (
                "block_lane_order_vectorized_summary"
            )
            for field in (
                "detection_rate",
                "stable_detection_rate",
                "mean_peak_height",
                "mean_peak_width_s",
            ):
                assert summary[field] == pytest.approx(
                    reference_summary[field],
                    rel=1e-12,
                    abs=1e-15,
                )

    def test_event_block_v3_falls_back_for_adaptive_budget(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 160)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        sim_cfg = SimulationConfig(
            total_time_s=0.04,
            sampling_rate_Hz=2000.0,
            mean_flow_velocity_m_s=2e-4,
            include_diffusion=True,
            flow_profile_model="rect_series",
            diffusion_hindrance_model="anisotropic_tensor_surrogate",
            noise_std=0.0,
            shot_noise_scale=0.0,
            post_readout_noise_std=0.0,
            n_events=12,
            random_seed=42,
            random_sequence_policy="case_keyed_independent",
            event_sampling_policy="sobol_stratified",
            adaptive_event_budget_mode="wilson_precision",
            adaptive_min_events=4,
            adaptive_check_interval=2,
            adaptive_wilson_half_width_target=0.6,
            vectorized_event_engine="event_block_v3",
            event_block_size=5,
            rho=10.0,
        )
        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )
        summary = batch["summary"]

        assert summary["vectorized_event_engine"] == "event_block_v3"
        assert summary["vectorized_event_engine_used"] == "event_loop_fallback"
        assert summary["vectorized_event_engine_fallback_reason"] == (
            "adaptive_budget_requires_event_loop"
        )
        assert summary["adaptive_event_budget_actual_events"] == 4
        assert summary["adaptive_event_budget_stop_reason"] == (
            "wilson_precision_target_met"
        )
        assert summary["vectorized_event_rng_order"] == "event_loop_order"

    def test_free_solution_transport_context_is_case_level(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 240)
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        sim_cfg = SimulationConfig(
            total_time_s=0.08,
            sampling_rate_Hz=10000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.0,
            n_events=1,
            random_seed=42,
            rho=10.0,
            include_diffusion=False,
            nanoconfinement_on=False,
            free_solution_window_scale=2.5,
        )

        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
        )

        event = batch["events"][0]
        assert event["transport_channel_width_m"] == pytest.approx(
            BASELINE_CHANNEL.width_m * sim_cfg.free_solution_window_scale
        )
        assert event["transport_channel_depth_m"] == pytest.approx(
            BASELINE_CHANNEL.depth_m * sim_cfg.free_solution_window_scale
        )

    def test_case_context_caches_reuse_invariant_case_work(self, monkeypatch):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 180)
        sim_cfg = SimulationConfig(
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.0,
            n_events=2,
            random_seed=42,
            rho=10.0,
        )
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        original_intrinsic = parameter_sweep_module.compute_intrinsic_scattering
        original_reference = parameter_sweep_module.compute_reference_field
        original_operator = parameter_sweep_module.build_collection_operator
        call_counts = {"intrinsic": 0, "reference": 0, "operator": 0}

        def counting_intrinsic(*args, **kwargs):
            call_counts["intrinsic"] += 1
            return original_intrinsic(*args, **kwargs)

        def counting_reference(*args, **kwargs):
            call_counts["reference"] += 1
            return original_reference(*args, **kwargs)

        def counting_operator(*args, **kwargs):
            call_counts["operator"] += 1
            return original_operator(*args, **kwargs)

        monkeypatch.setattr(
            parameter_sweep_module,
            "compute_intrinsic_scattering",
            counting_intrinsic,
        )
        monkeypatch.setattr(
            parameter_sweep_module,
            "compute_reference_field",
            counting_reference,
        )
        monkeypatch.setattr(
            parameter_sweep_module,
            "build_collection_operator",
            counting_operator,
        )
        intrinsic_cache = {}
        reference_cache = {}
        collection_operator_cache = {}
        first_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
            intrinsic_cache=intrinsic_cache,
            reference_cache=reference_cache,
            collection_operator_cache=collection_operator_cache,
        )
        second_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
            intrinsic_cache=intrinsic_cache,
            reference_cache=reference_cache,
            collection_operator_cache=collection_operator_cache,
        )

        assert second_batch["summary"] == first_batch["summary"]
        assert call_counts == {"intrinsic": 1, "reference": 1, "operator": 1}

    def test_reference_cache_returns_readonly_shallow_payloads(self):
        sim_cfg = SimulationConfig(
            total_time_s=0.02,
            sampling_rate_Hz=2000.0,
            mean_flow_velocity_m_s=2e-4,
            n_events=1,
            random_seed=42,
            reference_model="channel_angular_surrogate",
        )
        reference_cache = {}
        medium_refractive_index = float(
            WATER.refractive_index_at(BASELINE_OPTICAL.wavelength_m)
        )

        first_reference = parameter_sweep_module._get_or_compute_reference_field(
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            medium_refractive_index,
            reference_cache,
        )
        first_reference["caller_only"] = True
        second_reference = parameter_sweep_module._get_or_compute_reference_field(
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            medium_refractive_index,
            reference_cache,
        )

        assert first_reference is not second_reference
        assert "caller_only" not in second_reference
        assert first_reference["reference_angular_field"] is second_reference["reference_angular_field"]
        assert second_reference["reference_angular_field"].flags.writeable is False
        with pytest.raises(ValueError, match="read-only"):
            second_reference["reference_angular_field"][0, 0] = 0.0

    def test_invariant_case_caches_return_shallow_readonly_payloads(self, monkeypatch):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 16)
        sim_cfg = SimulationConfig(
            total_time_s=0.02,
            sampling_rate_Hz=2000.0,
            mean_flow_velocity_m_s=2e-4,
            n_events=1,
            random_seed=42,
        )
        medium_refractive_index = float(
            WATER.refractive_index_at(BASELINE_OPTICAL.wavelength_m)
        )
        call_counts = {"intrinsic": 0, "operator": 0}

        def fake_intrinsic(*args, **kwargs):
            call_counts["intrinsic"] += 1
            return {"angular_field": np.array([1.0, 2.0])}

        def fake_operator(*args, **kwargs):
            call_counts["operator"] += 1
            return {"roi_weight": np.array([0.25, 0.75])}

        monkeypatch.setattr(
            parameter_sweep_module,
            "compute_intrinsic_scattering",
            fake_intrinsic,
        )
        monkeypatch.setattr(
            parameter_sweep_module,
            "build_collection_operator",
            fake_operator,
        )
        intrinsic_cache = {}
        collection_operator_cache = {}

        first_intrinsic = parameter_sweep_module._get_or_compute_intrinsic_scattering(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL.wavelength_m,
            theta_grid,
            intrinsic_cache,
        )
        first_operator = parameter_sweep_module._get_or_build_collection_operator(
            theta_grid,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            medium_refractive_index,
            collection_operator_cache,
        )
        first_intrinsic["caller_only"] = True
        first_operator["caller_only"] = True
        second_intrinsic = parameter_sweep_module._get_or_compute_intrinsic_scattering(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL.wavelength_m,
            theta_grid,
            intrinsic_cache,
        )
        second_operator = parameter_sweep_module._get_or_build_collection_operator(
            theta_grid,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            medium_refractive_index,
            collection_operator_cache,
        )

        assert call_counts == {"intrinsic": 1, "operator": 1}
        assert first_intrinsic is not second_intrinsic
        assert first_operator is not second_operator
        assert "caller_only" not in second_intrinsic
        assert "caller_only" not in second_operator
        assert first_intrinsic["angular_field"] is second_intrinsic["angular_field"]
        assert first_operator["roi_weight"] is second_operator["roi_weight"]
        assert second_intrinsic["angular_field"].flags.writeable is False
        assert second_operator["roi_weight"].flags.writeable is False

    def test_cache_readonly_marker_rejects_nested_arrays(self):
        with pytest.raises(TypeError, match="nested ndarray"):
            parameter_sweep_module._mark_numpy_arrays_readonly(
                {"sub_diag": {"angular_field": np.array([1.0, 2.0])}}
            )

    def test_cached_case_payloads_keep_arrays_top_level(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 32)
        sim_cfg = SimulationConfig(
            total_time_s=0.02,
            sampling_rate_Hz=2000.0,
            mean_flow_velocity_m_s=2e-4,
            n_events=1,
            random_seed=42,
            reference_model="channel_angular_surrogate",
        )
        medium_refractive_index = float(
            WATER.refractive_index_at(BASELINE_OPTICAL.wavelength_m)
        )
        payloads = {
            "intrinsic": compute_intrinsic_scattering(
                BASELINE_PARTICLE,
                WATER,
                BASELINE_OPTICAL.wavelength_m,
                theta_grid,
            ),
            "operator": build_collection_operator(
                theta_grid,
                BASELINE_CHANNEL,
                BASELINE_OPTICAL,
                sim_cfg,
                medium_refractive_index=medium_refractive_index,
            ),
            "reference": compute_reference_field(
                BASELINE_CHANNEL,
                BASELINE_OPTICAL,
                sim_cfg,
                medium_refractive_index=medium_refractive_index,
            ),
        }
        for payload_name, payload in payloads.items():
            for key, value in payload.items():
                if isinstance(value, np.ndarray):
                    continue
                assert not parameter_sweep_module._contains_nested_ndarray(value), (
                    f"{payload_name}.{key} would bypass the top-level readonly marker"
                )

    def test_case_context_caches_preserve_stream_summary(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 180)
        sim_cfg = SimulationConfig(
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            mean_flow_velocity_m_s=2e-4,
            noise_std=0.001,
            post_readout_noise_std=0.0005,
            n_events=4,
            random_seed=42,
            rho=10.0,
        )
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
        )
        uncached_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
        )
        cached_batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
            retain_event_traces=False,
            stream_summary_only=True,
            intrinsic_cache={},
            reference_cache={},
            collection_operator_cache={},
        )

        assert cached_batch["summary"] == uncached_batch["summary"]
        assert cached_batch["intrinsic"] == uncached_batch["intrinsic"]
        assert cached_batch["reference"].keys() == uncached_batch["reference"].keys()

    def test_observation_signature_records_reference_and_phase_assumptions(self):
        theta_grid = np.linspace(0.01, np.pi - 0.01, 500)
        sim_cfg = SimulationConfig(
            total_time_s=0.2,
            sampling_rate_Hz=20000.0,
            mean_flow_velocity_m_s=2e-4,
            reference_model="geometry_scaled",
            reference_spatial_mode="uniform",
            phase_model="relative_surrogate",
            pulse_detection_mode="absolute",
            readout_model="lockin_surrogate",
            shot_noise_scale=0.002,
            collection_angle_model="channel_diffraction",
            collection_integration_mode="pupil_slit_surrogate",
            scattering_projection_mode="parallel",
        )
        baseline = compute_baseline_normalization(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_OPTICAL,
            theta_grid,
            channel=BASELINE_CHANNEL,
            sim_cfg=sim_cfg,
        )
        batch = run_single_case_batch(
            BASELINE_PARTICLE,
            WATER,
            BASELINE_CHANNEL,
            BASELINE_OPTICAL,
            sim_cfg,
            baseline["E_sca_ref"],
            theta_grid,
        )
        signature = batch["intrinsic"]["observation_signature"]
        assert "reference_route=legacy_debug" in signature
        assert "reference_solver_route=legacy_debug" in signature
        assert "reference_na_edge_policy=hard_guardrail" in signature
        assert "reference_na_edge_status=inside" in signature
        assert "reference_operating_band=shot_noise_limited_no_gain" in signature
        assert "phase_filter_validity=not_applicable" in signature
        assert "subwavelength_groove_validity_status=not_applicable" in signature
        assert "detector_forward_model=joint_overlap_coherent_surrogate" in signature
        assert "field_coordinate_measure=theta_phi_surrogate" in signature
        assert "complex_time_harmonic_convention=exp_minus_i_omega_t" in signature
        assert "interference_conjugation_convention=Re_Eref_conj_Esca" in signature
        assert "polarization_basis_model=scalar_parallel_perpendicular_surrogate" in signature
        assert "vector_optics_mode=scalar_surrogate" in signature
        assert "polarization_jones_operator_mode=scalar_projection" in signature
        assert "polarization_overlap_efficiency=1.0" in signature
        assert "phase_polarization_quantitative_claim_allowed=False" in signature
        assert "incident_field_model_for_mie=local_plane_wave" in signature
        assert "local_plane_wave_validity=valid_for_ranking" in signature
        assert "scattering_normalization_route=baseline_particle_relative" in signature
        assert "K_sca_calibration_status=not_calibrated" in signature
        assert (
            "mie_to_power_chain_status="
            "not_implemented_dCsca_dOmega_not_converted_to_detector_units"
        ) in signature
        assert "detector_field_units=arbitrary_relative_field_units" in signature
        assert (
            "K_sca_uncertainty_status="
            "not_propagated_no_standard_particle_uncertainty_budget"
        ) in signature
        assert (
            "standard_particle_uncertainty_budget_status="
            "missing_standard_particle_uncertainty_budget"
        ) in signature
        assert "calibration_design_rank=none" in signature
        assert (
            "calibration_held_out_validation_status="
            "not_available_no_standard_particle_design"
        ) in signature
        assert "output_claim_level=legacy_debug" in signature
        assert "noise_model_route=surrogate" in signature
        assert "noise_terms_schema_version=noise_terms_v1" in signature
        assert "photon_unit_noise_model=not_applied" in signature
        assert "detector_dynamic_range_model=not_applied" in signature
        assert "background_field_model=baseline_subtraction_surrogate" in signature
        assert "transmitted_leakage_model=not_applied" in signature
        assert "particle_induced_channel_perturbation_model=not_applied" in signature
        assert "particle_channel_perturbation_application_mode=diagnostic_only" in signature
        assert (
            "double_counting_risk_band="
            "none_no_particle_channel_perturbation_added"
        ) in signature
        assert "no_double_count_guard_passed=True" in signature
        assert "superposition_validity_status=" in signature
        assert "channel_particle_coupling_model=independent_superposition" in signature
        assert "readout_preset=exploratory_default" in signature
        assert "readout_preset_status=exploratory_default_active" in signature
        assert "electronics_demod_phase_policy=locked_to_event_center" in signature
        assert "effective_electronics_demod_phase_policy=locked_to_event_center" in signature
        assert "polarity_source=optical_and_electronics_phase_mixed" in signature
        assert "readout_internal_demod_route=sampled_carrier_demod_on_event_grid" in signature
        assert "readout_sampling_validity=carrier_underresolved" in signature
        assert "lockin_output_unit_convention=arbitrary_lockin_output_units" in signature
        assert "threshold_tail=two_sided" in signature
        assert "threshold_calibration_source=gaussian_iid" in signature
        assert "threshold_lane_specific_model=shared_threshold" in signature
        assert "colored_noise_false_alarm_model=not_applied" in signature
        assert "particle_family=gold" in signature
        assert "particle_optical_model=homogeneous_mie_sphere" in signature
        assert "particle_material_model_mode=materials_db_tabulated_interpolation" in signature
        assert (
            "particle_material_uncertainty_status="
            "not_quantified_material_dataset_nominal"
        ) in signature
        assert "EV_ensemble_mode=nominal_single_preset" in signature
        assert "uncertainty_propagation_mode=none" in signature
        assert (
            "particle_uncertainty_budget_status="
            "nominal_only_uncertainty_not_propagated"
        ) in signature
        assert (
            "per_event_detectability_boundary="
            "conditional_detection_rate_not_experiment_count_rate"
        ) in signature
        assert "EV_sample_preparation_profile=unknown" in signature
        assert "EV_specificity_risk=not_ev_specificity_target" in signature
        assert "count_prediction_model=not_applied" in signature
        assert "poisson_arrival_process_status=not_applied_count_prediction_disabled" in signature
        assert (
            "crossing_conditioned_transport_status="
            "not_implemented_uses_existing_per_event_initial_distribution"
        ) in signature
        assert "number_concentration_m3=None" in signature
        assert "flow_control_mode=fixed_velocity" in signature
        assert "fluidic_practicality_penalty=" in signature
        assert "fluidic_clogging_risk_band=" in signature
        assert "wall_interaction_model=none" in signature
        assert "interface_correction_mode=off" in signature
        assert (
            "interface_correction_status="
            "homogeneous_medium_mie_no_interface_correction"
        ) in signature
        assert (
            "interface_output_sensitivity_status="
            "phase_polarity_and_angular_pattern_sensitive"
        ) in signature
        assert "interface_fullwave_required=True" in signature
        assert "interface_fullwave_reason=phase_polarity_or_angular_pattern_output" in signature
        assert "thermal_pod_model=unavailable" in signature
        assert "thermal_pod_model_status=unavailable_no_heat_diffusion_model" in signature
        assert (
            "pod_quantitative_route_status="
            "blocked_missing_thermal_forward_model_or_calibration"
        ) in signature
        assert "pod_wavelength_grouping_status=single_probe_no_excitation_configured" in signature
        assert (
            "pod_probe_reference_field_status="
            "probe_E_ref_E_sca_use_current_optical_wavelength"
        ) in signature
        assert (
            "pod_heat_source_status="
            "not_available_missing_excitation_wavelength_or_power"
        ) in signature
        assert (
            "pod_detector_responsivity_status="
            "not_configured_by_probe_wavelength"
        ) in signature
        assert "pod_roi_sensitivity_derivative_status=unavailable" in signature
        assert "pod_signal_sign_source=unavailable" in signature
        assert f"probe_wavelength_m={BASELINE_OPTICAL.wavelength_m}" in signature
        assert "excitation_wavelength_m=None" in signature
        assert "reference_model=geometry_scaled" in signature
        assert "reference_spatial_mode=uniform" in signature
        assert "reference_claim_level=legacy_debug" in signature
        assert "reference_phase_grating_mode=phase_grating_sine" in signature
        assert "interference_overlap_mode=joint_overlap_integrated" in signature
        assert "phase_model=relative_surrogate" in signature
        assert "path_opd_model=single_pass" in signature
        assert "pulse_detection=absolute" in signature
        assert "detection_decision_mode=single_channel" in signature
        assert "readout_model=lockin_surrogate" in signature
        assert "shot_noise_scale=2.000000000e-03" in signature
        assert "evaluation_false_alarm_rate=5.000000000e-02" in signature
        assert "pulse_pairing_tolerance_s=5.000000000e-03" in signature
        assert batch["summary"]["path_opd_freeze_status"] == "default_frozen_active"
        assert batch["intrinsic"]["detector_forward_model"] == "joint_overlap_coherent_surrogate"
        assert batch["intrinsic"]["detector_forward_status"] == "joint_overlap_requested_scalar_surrogate_fallback"
        assert batch["intrinsic"]["joint_overlap_used"] is False
        assert batch["intrinsic"]["field_coordinate_measure"] == "theta_phi_surrogate"
        assert batch["intrinsic"]["field_measure_status"] == "surrogate_theta_phi_weights_not_solid_angle"
        assert batch["intrinsic"]["bfp_to_angle_jacobian_applied"] is False
        assert batch["intrinsic"]["complex_convention_status"] == "frozen_surrogate_convention"
        assert (
            batch["intrinsic"]["absolute_polarity_claim"]
            == "not_available_without_measured_global_phase_offset"
        )
        assert batch["intrinsic"]["S1S2_to_lab_basis_rotation_applied"] is False
        assert batch["intrinsic"]["active_mie_basis_component"] == "S2_complex"
        assert batch["intrinsic"]["high_NA_collection_warning"] is True
        assert batch["intrinsic"]["incident_field_model_for_mie"] == "local_plane_wave"
        assert batch["intrinsic"]["local_plane_wave_validity"] == "valid_for_ranking"
        assert batch["intrinsic"]["mie_incident_field_GLMT_required"] is False
        assert batch["intrinsic"]["mie_incident_field_fullwave_required"] is False
        assert batch["intrinsic"]["mie_incident_field_blocker_summary"] == "none"
        assert batch["intrinsic"]["scattering_normalization_route"] == "baseline_particle_relative"
        assert batch["intrinsic"]["baseline_particle_absolute_scale_restored"] is False
        assert (
            batch["intrinsic"]["baseline_normalized_E_sca_allowed_in_photon_unit_route"]
            is False
        )
        assert batch["intrinsic"]["K_sca_calibration_status"] == "not_calibrated"
        assert (
            batch["intrinsic"]["K_sca_uncertainty_status"]
            == "not_propagated_no_standard_particle_uncertainty_budget"
        )
        assert (
            batch["intrinsic"]["standard_particle_uncertainty_budget_status"]
            == "missing_standard_particle_uncertainty_budget"
        )
        assert batch["intrinsic"]["K_sca_uncertainty_propagated_to_outputs"] is False
        assert (
            batch["intrinsic"]["mie_to_power_chain_status"]
            == "not_implemented_dCsca_dOmega_not_converted_to_detector_units"
        )
        assert batch["intrinsic"]["detector_field_units"] == "arbitrary_relative_field_units"
        assert batch["intrinsic"]["calibration_design_rank"] == "none"
        assert batch["intrinsic"]["calibration_standard_count"] == 0
        assert (
            batch["intrinsic"]["calibration_held_out_validation_status"]
            == "not_available_no_standard_particle_design"
        )
        assert batch["intrinsic"]["bayesian_calibration_status"] == (
            "scaffold_only_no_real_standard_data"
        )
        assert batch["intrinsic"]["bayesian_posterior_available"] is False
        assert batch["intrinsic"]["posterior_predictive_design_score_p10"] is None
        assert batch["intrinsic"]["experimental_design_advisor_status"] == (
            "next_experiment_recommended"
        )
        assert batch["intrinsic"]["next_experiment_priority"] is not None
        assert batch["intrinsic"]["value_of_information_score"] > 0.0
        assert batch["intrinsic"]["experimental_design_advisor_gate_passed"] is False
        assert batch["intrinsic"]["population_inference_status"] == (
            "likelihood_shape_defined_claim_blocked"
        )
        assert batch["intrinsic"]["population_inference_gate_passed"] is False
        assert batch["intrinsic"]["population_inference_posterior_available"] is False
        assert batch["intrinsic"]["population_inference_true_distribution_estimate"] is None
        assert batch["intrinsic"]["calibrated_quantitative_unlocked"] is False
        assert batch["intrinsic"]["output_claim_level"] == "legacy_debug"
        assert batch["intrinsic"]["readout_sampling_hard_gate_passed"] is False
        assert batch["intrinsic"]["noise_model_route"] == "surrogate"
        assert (
            batch["intrinsic"]["detector_noise_claim_level"]
            == "engineering_noise_surrogate_not_detector_unit"
        )
        assert batch["intrinsic"]["shot_noise_model_status"] == "intensity_proxy_shot_noise_surrogate"
        assert (
            batch["intrinsic"]["photon_shot_noise_term_status"]
            == "intensity_proxy_shot_noise_surrogate"
        )
        assert batch["intrinsic"]["photon_unit_noise_model_status"] == "not_applied"
        assert batch["intrinsic"]["detector_saturation_status"] == "not_evaluated_no_detector_range"
        assert batch["intrinsic"]["dynamic_range_margin"] is None
        assert batch["summary"]["noise_model_route"] == "surrogate"
        assert batch["summary"]["dynamic_range_margin"] is None
        assert batch["intrinsic"]["background_field_model"] == "baseline_subtraction_surrogate"
        assert (
            batch["intrinsic"]["background_field_status"]
            == "baseline_subtraction_only_no_explicit_leakage_field"
        )
        assert batch["intrinsic"]["residual_transmitted_leakage_status"] == "not_modeled"
        assert batch["intrinsic"]["blank_trace_empirical_available"] is False
        assert (
            batch["intrinsic"]["nodi_signal_component_model"]
            == "scattering_interference_only_surrogate"
        )
        assert (
            batch["intrinsic"]["nodi_forward_extinction_leakage_status"]
            == "not_modeled"
        )
        assert (
            batch["intrinsic"]["nodi_particle_induced_channel_coupling_status"]
            == "not_applied_not_added_to_score"
        )
        assert batch["intrinsic"]["double_counting_risk_band"] == (
            "none_no_particle_channel_perturbation_added"
        )
        assert batch["intrinsic"]["no_double_count_guard_passed"] is True
        assert batch["intrinsic"]["particle_channel_double_count_guard_status"] == (
            "pass_no_particle_channel_term_added"
        )
        assert batch["intrinsic"]["superposition_validity_status"] in {
            "weak_scatterer_valid",
            "caution_reference_perturbation",
            "requires_joint_fullwave",
        }
        assert batch["intrinsic"]["channel_particle_coupling_model"] == "independent_superposition"
        assert batch["intrinsic"]["E_sca_to_E_ref_amplitude_ratio_estimate"] is not None
        assert batch["intrinsic"]["extinction_to_beam_area_estimate"] is not None
        assert batch["summary"]["background_claim_level"] == "engineering_background_surrogate_not_measured_blank"
        assert batch["intrinsic"]["readout_preset"] == "exploratory_default"
        assert batch["intrinsic"]["readout_preset_status"] == "exploratory_default_active"
        assert batch["intrinsic"]["electronics_demod_phase_policy"] == "locked_to_event_center"
        assert batch["intrinsic"]["polarity_source"] == "optical_and_electronics_phase_mixed"
        assert batch["intrinsic"]["readout_carrier_nyquist_resolved"] is True
        assert batch["intrinsic"]["readout_carrier_resolved"] is False
        assert batch["intrinsic"]["readout_sampling_validity"] == "carrier_underresolved"
        assert batch["intrinsic"]["lockin_output_unit_convention"] == "arbitrary_lockin_output_units"
        assert batch["summary"]["readout_preset_claim_level"] == "exploratory_phase_aware_surrogate"
        assert batch["intrinsic"]["threshold_tail"] == "two_sided"
        assert batch["intrinsic"]["threshold_sign"] == "absolute_magnitude"
        assert batch["intrinsic"]["threshold_lane_specific_model"] == "shared_threshold"
        assert batch["intrinsic"]["threshold_from_blank_trace"] is False
        assert batch["intrinsic"]["threshold_from_event_background_segment"] is True
        assert batch["intrinsic"]["threshold_calibration_status"] == "gaussian_iid_surrogate_not_empirical_blank"
        assert batch["intrinsic"]["colored_noise_false_alarm_status"] == "not_evaluated_iid_surrogate_only"
        assert batch["intrinsic"]["paired_false_alarm_status"] == "not_evaluated_no_joint_blank_trace"
        assert batch["intrinsic"]["particle_family"] == "gold"
        assert batch["intrinsic"]["particle_optical_model"] == "homogeneous_mie_sphere"
        assert batch["intrinsic"]["EV_claim_level"] == "not_applicable"
        assert (
            batch["intrinsic"]["particle_material_model_mode"]
            == "materials_db_tabulated_interpolation"
        )
        assert (
            batch["intrinsic"]["particle_material_uncertainty_status"]
            == "not_quantified_material_dataset_nominal"
        )
        assert batch["intrinsic"]["EV_ensemble_mode"] == "nominal_single_preset"
        assert (
            batch["intrinsic"]["particle_uncertainty_budget_status"]
            == "nominal_only_uncertainty_not_propagated"
        )
        assert batch["intrinsic"]["uncertainty_propagation_mode"] == "none"
        assert batch["intrinsic"]["peak_height_CI_available"] is False
        assert batch["reference"]["particle_family"] == "gold"
        assert batch["intrinsic"]["polarization_jones_operator_mode"] == (
            "scalar_projection"
        )
        assert batch["summary"]["polarization_overlap_efficiency"] == pytest.approx(
            batch["intrinsic"]["polarization_overlap_efficiency"]
        )
        assert (
            batch["intrinsic"]["phase_polarization_quantitative_claim_allowed"]
            is False
        )
        assert batch["intrinsic"]["conditional_detection_rate"] == pytest.approx(
            batch["summary"]["detected_rate_after_event_qc"]
        )
        assert batch["intrinsic"]["conditional_detection_rate_source"] == (
            "detected_rate_after_event_qc"
        )
        assert batch["intrinsic"]["count_prediction_model"] == "not_applied"
        assert (
            batch["intrinsic"]["count_prediction_status"]
            == "not_applied_per_event_detection_only"
        )
        assert batch["intrinsic"]["count_likelihood_status"] == (
            "unavailable_without_count_prediction"
        )
        assert batch["summary"]["false_positive_corrected_count"] == pytest.approx(
            batch["summary"]["n_detected"]
        )
        assert batch["intrinsic"]["count_likelihood_claim_level"] == (
            "exploratory_no_count_prediction"
        )
        assert set(OOD_DIAGNOSTIC_FIELDS).issubset(batch["summary"])
        assert batch["intrinsic"]["EV_contaminant_hard_classification_allowed"] is False
        assert 0.0 <= batch["summary"]["classifier_rejection_rate"] <= 1.0
        assert batch["intrinsic"]["predicted_count_rate_Hz"] is None
        assert batch["intrinsic"]["accessible_area_m2"] > 0.0
        assert batch["intrinsic"]["wall_interaction_status"] == "wall_interaction_unmodeled"
        assert batch["intrinsic"]["interface_correction_mode"] == "off"
        assert (
            batch["intrinsic"]["interface_correction_status"]
            == "homogeneous_medium_mie_no_interface_correction"
        )
        assert batch["intrinsic"]["interface_correction_particle_family"] == "gold"
        assert batch["intrinsic"]["interface_fullwave_required"] in {False, True}
        assert batch["intrinsic"]["thermal_pod_model"] == "unavailable"
        assert set(NODI_THERMAL_CONTAMINATION_FIELDS).issubset(batch["summary"])
        assert batch["intrinsic"]["nodi_thermal_contamination_status"] == (
            batch["summary"]["nodi_thermal_contamination_status"]
        )
        assert (
            batch["intrinsic"]["thermal_pod_model_status"]
            == "unavailable_no_heat_diffusion_model"
        )
        assert batch["intrinsic"]["pod_quantitative_amplitude_available"] is False
        assert batch["intrinsic"]["pod_quantitative_sign_available"] is False
        assert batch["intrinsic"]["probe_wavelength_m"] == pytest.approx(
            BASELINE_OPTICAL.wavelength_m
        )
        assert batch["intrinsic"]["excitation_wavelength_m"] is None
        assert batch["intrinsic"]["probe_coherent_field_group_id"] == "probe_660nm"
        assert (
            batch["intrinsic"]["pod_wavelength_grouping_status"]
            == "single_probe_no_excitation_configured"
        )
        assert batch["intrinsic"]["pod_quantitative_route_status"] == (
            "blocked_missing_thermal_forward_model_or_calibration"
        )
        assert batch["intrinsic"]["pod_heat_source_status"] == (
            "not_available_missing_excitation_wavelength_or_power"
        )
        assert batch["intrinsic"]["pod_signal_sign_source"] == "unavailable"
        assert "thermal_pod_model_unavailable" in batch["intrinsic"][
            "pod_amplitude_quantitative_blocker_summary"
        ]
        assert batch["summary"]["mean_threshold_robust_std"] is not None
        assert (
            batch["intrinsic"]["coordinate_frame_mapping"]
            == "chip:x_width,y_flow,z_depth|optical:detector_projection_surrogate|bfp:theta_phi"
        )
        assert batch["reference"]["interference_cross_term_convention"] == "2*Re(E_ref*conj(E_sca))"
        assert batch["reference"]["vector_validity_status"] == "scalar_high_NA_caution"
        assert batch["reference"]["scattering_calibration_level"] == "relative_baseline_particle_normalized"
        assert batch["reference"]["output_claim_level"] == "legacy_debug"
        assert "rho_physical_envelope_lower" not in batch["summary"]
        assert "reference_diffraction_efficiency_zeroth_order" not in batch["summary"]
        assert "reference_width_saturation_status" not in batch["summary"]
        assert batch["intrinsic"]["path_opd_model"] == "single_pass"
        assert batch["intrinsic"]["path_opd_reference_plane"] == "detector_projection_single_pass_surrogate"
        assert batch["intrinsic"]["path_opd_z_geometry_factor"] == pytest.approx(1.0)
