# ruff: noqa: F401
"""
Package-local public exports for the NODI Interferometric Simulator.
==============================

Semi-physical interferometric simulator with material-aware normalization.

Simulates single nanoparticle transit events through a NODI-type nanochannel
detection zone. The nanochannel diffracted light serves as an interferometric
reference field, enabling detection of weak scattering signals from nanoparticles.

Main workflow:
    1. compute_baseline_normalization              → global E_sca_ref
       compute_baseline_normalization_per_wavelength → per-λ E_sca_ref
    2. run_single_case_batch                       → batch statistics for one (W,H,λ)
    3. run_parameter_sweep                         → design map across (W,H,λ)
"""

from .data_objects import (
    Particle, Medium, Channel, OpticalSystem, SimulationConfig,
    DesignObjectiveConfig,
    make_ev_nodi_design_sweep_config, make_gold_baseline_particle,
    BASELINE_PARTICLE, PBS_1X, WATER, BASELINE_CHANNEL, BASELINE_OPTICAL,
    DEFAULT_SIM_CFG, DEFAULT_DESIGN_OBJECTIVE_CONFIG,
)
from .design_claim_governance import (
    DESIGN_CLAIM_GOVERNANCE_FIELDS,
    MINIMUM_OUTPUT_SCHEMA_FIELDS,
    build_design_claim_governance_diagnostics,
)
from .design_metrics import (
    DESIGN_METRIC_DIAGNOSTIC_FIELDS,
    DESIGN_METRIC_MATCH_KEYS,
    attach_anchor_equivalent_metrics,
    attach_fluidic_practicality_metrics,
    attach_reference_operating_metrics,
    design_metric_match_key,
)
from .design_postprocess import (
    EV_DESIGN_POSTPROCESS_FIELDS,
    attach_ev_design_postprocess,
    compute_ev_ensemble_design_score,
    compute_pareto_front,
    compute_physics_model_consensus,
    compute_reference_route_consensus,
    generate_claim_text,
)
from .channel_geometry_model import (
    CHANNEL_GEOMETRY_DIAGNOSTIC_FIELDS,
    build_channel_geometry_diagnostics,
)
from .electrokinetic_transport import (
    ELECTROKINETIC_DIAGNOSTIC_FIELDS,
    build_electrokinetic_transport_diagnostics,
)
from .ev_integrity_risk import (
    EV_INTEGRITY_DIAGNOSTIC_FIELDS,
    build_ev_integrity_risk_diagnostics,
)
from .ev_reporting_metadata import (
    EVPreanalyticalMetadata,
    EV_REPORTING_DIAGNOSTIC_FIELDS,
    build_ev_reporting_metadata_diagnostics,
)
from .assay_control_matrix import (
    ASSAY_CONTROL_DIAGNOSTIC_FIELDS,
    REQUIRED_CONTROL_SAMPLES,
    build_assay_control_matrix_diagnostics,
)
from .control_interpretation import (
    CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS,
    build_control_interpretation_diagnostics,
)
from .bfp_detector_operator import (
    BFP_DETECTOR_OPERATOR_DIAGNOSTIC_FIELDS,
    build_bfp_detector_operator_diagnostics,
    compute_detector_integrated_interference,
)
from .particle_channel_perturbation import (
    PARTICLE_CHANNEL_PERTURBATION_DIAGNOSTIC_FIELDS,
    build_particle_channel_perturbation_diagnostics,
)
from .recompute_manifest import (
    RECOMPUTE_MANIFEST_DIAGNOSTIC_FIELDS,
    build_recompute_manifest_diagnostics,
)
from .materials import (
    MATERIAL_DB,
    get_n_complex,
    list_materials,
    material_property_summary,
)
from .mie_engine import (
    mie_angular,
    mie_compute,
)
from .intrinsic_scattering import compute_intrinsic_scattering
from .reference_field import (
    TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS,
    compute_reference_field,
    compute_reference_field_from_tsuyama_bfp,
    compute_reference_field_trace,
)
from .reference_operating_point import (
    REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS,
    build_reference_operating_point_diagnostics,
)
from .fluidic_resistance import (
    FLUIDIC_RESISTANCE_DIAGNOSTIC_FIELDS,
    compute_fluidic_practicality_penalty,
    compute_rectangular_channel_hydraulic_resistance,
)
from .fluidic_network_model import (
    FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS,
    build_fluidic_network_diagnostics,
)
from .particle_design_library import (
    EV_SAMPLE_PREPARATION_PROFILES,
    EV_SHAPE_MODEL_OPTIONS,
    PARTICLE_CONTAMINANT_PRESETS,
    PARTICLE_DESIGN_LIBRARY_DIAGNOSTIC_FIELDS,
    STANDARD_PARTICLE_PRESETS,
    StandardParticleSpec,
    build_particle_design_library_diagnostics,
)
from .ev_population_prior import (
    EV_POPULATION_PRIOR_DIAGNOSTIC_FIELDS,
    build_ev_population_prior_diagnostics,
)
from .tsuyama_phase_filter import (
    classify_phase_filter_validity,
    compute_tsuyama_phase_filter_bfp_field,
    decompose_tsuyama_reference_field,
    integrate_bfp_roi,
)
from .illumination import compute_illumination_envelope
from .count_generation import build_count_model_diagnostics
from .count_likelihood import (
    COUNT_LIKELIHOOD_DIAGNOSTIC_FIELDS,
    build_count_likelihood_diagnostics,
    log_likelihood_counts,
)
from .ood_detection import (
    OOD_DIAGNOSTIC_FIELDS,
    build_ood_detection_diagnostics,
)
from .bayesian_calibration import (
    BAYESIAN_CALIBRATION_DIAGNOSTIC_FIELDS,
    build_bayesian_calibration_scaffold,
)
from .experimental_design_advisor import (
    EXPERIMENTAL_DESIGN_ADVISOR_FIELDS,
    build_experimental_design_advisor,
)
from .population_inference import (
    POPULATION_INFERENCE_DIAGNOSTIC_FIELDS,
    build_population_inference_scaffold,
)
from .interface_correction import build_interface_correction_diagnostics
from .photothermal_pod import build_photothermal_pod_diagnostics
from .nodi_thermal_contamination import (
    NODI_THERMAL_CONTAMINATION_FIELDS,
    build_nodi_thermal_contamination_diagnostics,
)
from .polarization_jones_operator import (
    POLARIZATION_JONES_DIAGNOSTIC_FIELDS,
    build_polarization_jones_diagnostics,
)
from .population_trace_simulator import (
    POPULATION_TRACE_DIAGNOSTIC_FIELDS,
    PopulationTraceConfig,
    simulate_population_trace_from_event_library,
)
from .event_quality_control import (
    EVENT_QC_DIAGNOSTIC_FIELDS,
    build_event_quality_control_diagnostics,
)
from .selection_function import (
    SELECTION_FUNCTION_DIAGNOSTIC_FIELDS,
    build_selection_function_diagnostics,
    compute_observed_distribution_correction,
)
from .run_state_model import (
    RUN_STATE_DIAGNOSTIC_FIELDS,
    build_run_state_diagnostics,
)
from .seed_robustness import (
    SEED_ROBUSTNESS_DIAGNOSTIC_FIELDS,
    compute_seed_detectability_score,
    run_seed_replicates,
    summarize_seed_replicate_metrics,
)
from .detector_units import build_detector_unit_chain_boundary
from .uncertainty import build_uncertainty_propagation_boundary
from .optical_exposure_safety import build_optical_exposure_safety_diagnostics
from .optical_hardware_profiles import (
    OBJECTIVE_PROFILES,
    ObjectiveProfile,
    build_objective_profile_diagnostics,
    get_objective_profile,
)
from .objective_panel import (
    DEFAULT_OBJECTIVE_PANEL_IDS,
    OBJECTIVE_PANEL_DIAGNOSTIC_FIELDS,
    evaluate_objective_panel,
)
from .readout_transfer_model import (
    READOUT_TRANSFER_DIAGNOSTIC_FIELDS,
    build_nodi_readout_transfer_diagnostics,
)
from .unit_conventions import (
    build_mie_validation_diagnostics,
    build_unit_axis_convention_diagnostics,
)
from .wavelength_comparability import (
    WAVELENGTH_COMPARABILITY_DIAGNOSTIC_FIELDS,
    build_wavelength_comparability_diagnostics,
)
from .calibration_models import (
    build_bfp_roi_mask_contract,
    build_raw_blank_trace_bootstrap_boundary,
    calibration_contract_summary,
    validate_calibration_manifest,
    validate_calibration_table,
)
from .calibration_plan_advisor import (
    CALIBRATION_PLAN_ADVISOR_FIELDS,
    build_calibration_plan_advisor,
)
from .trajectory import simulate_particle_trajectory
from .scattering_trace import compute_scattering_field_trace, spatial_coupling_factor
from .interferometric_trace import generate_interferometric_trace
from .pulse_analysis import estimate_threshold_robust, extract_pulse_features
from .parameter_sweep import (
    add_detector_noise,
    simulate_one_event, summarize_batch,
    run_single_case_batch, compute_case_score,
    compute_joint_score, compute_robust_scores,
    run_parameter_sweep,
)
from .utils import (
    interpolate_at_theta, validate_simulation_config,
    sample_initial_position, min_max_normalize,
    compute_baseline_normalization, compute_baseline_normalization_per_wavelength,
    resolve_collection_theta_rad, interpolate_complex_at_theta,
    compute_detected_scattering_field,
    build_calibration_state_diagnostics,
    build_background_field_diagnostics,
    build_complex_field_convention_diagnostics,
    build_detector_noise_diagnostics,
    build_interference_overlap_diagnostics,
    build_mie_incident_field_validity_diagnostics,
    resolve_projection_basis,
    classify_interference_overlap_freeze,
    classify_projection_freeze,
    classify_delta_phi_gouy_geometry_validity,
    classify_observation_freeze,
    classify_design_recommendation,
    classify_engineering_gate_explanation,
    build_case_decision_summary,
)
from .structured_particles import (
    BIOMIMETIC_EXOSOME_DEFAULTS,
    EV_SEV_ENSEMBLE_PRESET_GROUPS,
    EXOSOME_MODEL_PRESETS,
    build_biomimetic_exosome_core_shell,
    get_exosome_model_preset,
    list_ev_sev_ensemble_presets,
    list_exosome_model_presets,
    make_biomimetic_exosome_ensemble_particles,
    make_biomimetic_exosome_particle,
    resolve_structured_particle_spec,
)
from .paper_aligned_profiles import (
    PAPER_ALIGNED_PROFILES,
    PaperAlignedProfile,
    apply_paper_aligned_profile,
    list_paper_aligned_profiles,
)

__version__ = "0.2.1"

__all__ = [name for name in globals() if not name.startswith("_")]
