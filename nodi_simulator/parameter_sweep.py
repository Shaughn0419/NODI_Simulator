"""
Package-local parameter sweep module for NODI interferometric simulation.

Orchestrates:
    1. Single event simulation (simulate_one_event)
    2. Batch statistics (summarize_batch)
    3. Single-case batch runner (run_single_case_batch)
    4. Full parameter sweep over (W, H, λ) (run_parameter_sweep)
    5. Scoring and ranking (compute_case_score)
    6. Joint scoring for dual-object optimization (compute_joint_score)
    7. Robust neighborhood scoring (compute_robust_scores)

Normalization note:
    E_sca interpolation and normalization happen inside run_single_case_batch,
    keeping intrinsic_scattering pure and unnormalized.

Event randomness:
    - sample_initial_position → different (x0, z0) each event
    - Gaussian noise realization
    - Brownian diffusion trajectory (when enabled)
"""
import math
import os
import hashlib
import logging
import time
from collections import Counter
from collections.abc import Callable
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from copy import copy, deepcopy
from dataclasses import dataclass, field, replace
from typing import Any, Literal

import numpy as np
from scipy.signal import lfilter
from scipy.stats import qmc

from .optional_acceleration import optional_numba_njit, warn_numba_unavailable

try:
    from numba import njit as _numba_njit
except Exception:  # pragma: no cover - optional acceleration dependency
    warn_numba_unavailable("parameter-sweep kernels")
    _numba_njit = None

_LOGGER = logging.getLogger(__name__)

_NO_VECTORIZED_FALLBACK_REASON = "<none>"

from .data_objects import (
    Particle, Medium, Channel, OpticalSystem, SimulationConfig,
)
from .detector_route_assembly import (
    assemble_route_trace_payload,
    compute_r_self,
)
from .design_claim_governance import (
    DESIGN_CLAIM_GOVERNANCE_FIELDS,
    build_design_claim_governance_diagnostics,
)
from .design_metrics import (
    DESIGN_METRIC_DIAGNOSTIC_FIELDS,
    attach_anchor_equivalent_metrics,
    attach_fluidic_practicality_metrics,
    attach_reference_operating_metrics,
)
from .design_postprocess import (
    EV_DESIGN_POSTPROCESS_FIELDS,
    attach_ev_design_postprocess,
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
    EV_REPORTING_DIAGNOSTIC_FIELDS,
    build_ev_reporting_metadata_diagnostics,
)
from .fluidic_resistance import (
    FLUIDIC_RESISTANCE_DIAGNOSTIC_FIELDS,
    compute_fluidic_practicality_penalty,
)
from .fluidic_network_model import (
    FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS,
    build_fluidic_network_diagnostics,
)
from .assay_control_matrix import (
    ASSAY_CONTROL_DIAGNOSTIC_FIELDS,
    build_assay_control_matrix_diagnostics,
)
from .control_interpretation import (
    CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS,
    build_control_interpretation_diagnostics,
)
from .bfp_detector_operator import (
    BFP_DETECTOR_OPERATOR_DIAGNOSTIC_FIELDS,
    build_bfp_detector_operator_diagnostics,
)
from .particle_channel_perturbation import (
    PARTICLE_CHANNEL_PERTURBATION_DIAGNOSTIC_FIELDS,
    build_particle_channel_perturbation_diagnostics,
)
from .particle_design_library import (
    PARTICLE_DESIGN_LIBRARY_DIAGNOSTIC_FIELDS,
    build_particle_design_library_diagnostics,
)
from .ev_population_prior import (
    EV_POPULATION_PRIOR_DIAGNOSTIC_FIELDS,
    build_ev_population_prior_diagnostics,
)
from .recompute_manifest import (
    RECOMPUTE_MANIFEST_DIAGNOSTIC_FIELDS,
    build_recompute_manifest_diagnostics,
)
from .type_coerce import wilson_half_width as _wilson_half_width
from .intrinsic_scattering import compute_intrinsic_scattering
from .count_generation import build_count_model_diagnostics
from .count_likelihood import (
    COUNT_LIKELIHOOD_DIAGNOSTIC_FIELDS,
    build_count_likelihood_diagnostics,
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
from .reference_field import (
    TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS,
    compute_reference_field,
    compute_reference_field_trace,
)
from .reference_operating_point import (
    REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS,
    build_reference_operating_point_diagnostics,
)
from .illumination import compute_illumination_envelope
from .trajectory import (
    TRAJECTORY_GEOMETRY_DIAGNOSTIC_FIELDS,
    TrajectoryContext,
    build_trajectory_context,
    build_trajectory_geometry_diagnostics,
    simulate_particle_trajectory,
    simulate_particle_trajectory_block,
)
from .scattering_trace import compute_scattering_field_trace
from .interferometric_trace import generate_interferometric_trace
from .optical_exposure_safety import build_optical_exposure_safety_diagnostics
from .optical_hardware_profiles import build_objective_profile_diagnostics
from .objective_panel import (
    OBJECTIVE_PANEL_DIAGNOSTIC_FIELDS,
    evaluate_objective_panel,
)
from .unit_conventions import (
    build_mie_validation_diagnostics,
    build_unit_axis_convention_diagnostics,
)
from .wavelength_comparability import (
    WAVELENGTH_COMPARABILITY_DIAGNOSTIC_FIELDS,
    build_wavelength_comparability_diagnostics,
)
from .event_quality_control import (
    EVENT_QC_DIAGNOSTIC_FIELDS,
    build_event_quality_control_diagnostics,
)
from .selection_function import (
    SELECTION_FUNCTION_DIAGNOSTIC_FIELDS,
    build_selection_function_diagnostics,
)
from .run_state_model import (
    RUN_STATE_DIAGNOSTIC_FIELDS,
    build_run_state_diagnostics,
)
from .pulse_analysis import (
    PulseExtractionContext,
    build_pulse_extraction_context,
    estimate_threshold_stats_robust,
    extract_pulse_features,
)
from .utils import (
    build_collection_operator,
    compute_detected_scattering_field,
    validate_simulation_config,
    sample_initial_position,
    min_max_normalize,
    compute_baseline_normalization_per_wavelength,
    resolve_projection_basis,
    build_detector_forward_diagnostics,
    build_complex_field_convention_diagnostics,
    build_calibration_state_diagnostics,
    build_detector_noise_diagnostics,
    build_background_field_diagnostics,
    build_readout_convention_diagnostics,
    build_threshold_false_alarm_diagnostics,
    build_particle_model_diagnostics,
    build_interference_overlap_diagnostics,
    classify_interference_overlap_freeze,
    classify_projection_freeze,
    classify_delta_phi_gouy_geometry_validity,
    classify_observation_freeze,
    classify_design_recommendation,
    classify_engineering_gate_explanation,
)


# Boltzmann constant
_kB = 1.380649e-23
_BLAS_THREAD_ENV_VARS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
)


_optional_numba_njit = optional_numba_njit(_numba_njit)


@_optional_numba_njit(cache=True)
def _first_order_lowpass_alpha_2d_kernel(
    signal: np.ndarray,
    alpha: float,
) -> np.ndarray:
    rows, cols = signal.shape
    out = np.empty((rows, cols), dtype=np.float64)
    if cols == 0:
        return out
    one_minus_alpha = 1.0 - alpha
    for row_idx in range(rows):
        previous = signal[row_idx, 0]
        out[row_idx, 0] = previous
        for col_idx in range(1, cols):
            previous = alpha * signal[row_idx, col_idx] + one_minus_alpha * previous
            out[row_idx, col_idx] = previous
    return out


@_optional_numba_njit(cache=True)
def _lockin_in_phase_lowpass_2d_kernel(
    source: np.ndarray,
    alpha: float,
    carrier_cos: np.ndarray,
    demod_cos: np.ndarray,
) -> np.ndarray:
    rows, cols = source.shape
    out = np.empty((rows, cols), dtype=np.float64)
    if cols == 0:
        return out
    one_minus_alpha = 1.0 - alpha
    for row_idx in range(rows):
        previous = 2.0 * source[row_idx, 0] * carrier_cos[0] * demod_cos[0]
        out[row_idx, 0] = previous
        for col_idx in range(1, cols):
            mixed = (
                2.0
                * source[row_idx, col_idx]
                * carrier_cos[col_idx]
                * demod_cos[col_idx]
            )
            previous = alpha * mixed + one_minus_alpha * previous
            out[row_idx, col_idx] = previous
    return out


@_optional_numba_njit(cache=True)
def _lockin_light_in_phase_readout_2d_kernel(
    raw: np.ndarray,
    alpha: float,
    pod_carrier_cos: np.ndarray,
    pod_demod_cos: np.ndarray,
    nodi_carrier_cos: np.ndarray,
    nodi_demod_cos: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rows, cols = raw.shape
    pod_true_i = np.empty((rows, cols), dtype=np.float64)
    nodi_true_i = np.empty((rows, cols), dtype=np.float64)
    pod_leak_i = np.empty((rows, cols), dtype=np.float64)
    nodi_leak_i = np.empty((rows, cols), dtype=np.float64)
    if cols == 0:
        return pod_true_i, nodi_true_i, pod_leak_i, nodi_leak_i

    one_minus_alpha = 1.0 - alpha
    for row_idx in range(rows):
        raw_value = raw[row_idx, 0]
        pod_source = raw_value
        nodi_source = raw_value - pod_source

        pod_true = 2.0 * pod_source * pod_carrier_cos[0] * pod_demod_cos[0]
        nodi_true = 2.0 * nodi_source * nodi_carrier_cos[0] * nodi_demod_cos[0]
        pod_leak = 2.0 * nodi_source * nodi_carrier_cos[0] * pod_demod_cos[0]
        nodi_leak = 2.0 * pod_source * pod_carrier_cos[0] * nodi_demod_cos[0]

        pod_true_i[row_idx, 0] = pod_true
        nodi_true_i[row_idx, 0] = nodi_true
        pod_leak_i[row_idx, 0] = pod_leak
        nodi_leak_i[row_idx, 0] = nodi_leak

        for col_idx in range(1, cols):
            raw_value = raw[row_idx, col_idx]
            pod_source = alpha * raw_value + one_minus_alpha * pod_source
            nodi_input = raw_value - pod_source
            nodi_source = alpha * nodi_input + one_minus_alpha * nodi_source

            mixed_pod_true = (
                2.0
                * pod_source
                * pod_carrier_cos[col_idx]
                * pod_demod_cos[col_idx]
            )
            mixed_nodi_true = (
                2.0
                * nodi_source
                * nodi_carrier_cos[col_idx]
                * nodi_demod_cos[col_idx]
            )
            mixed_pod_leak = (
                2.0
                * nodi_source
                * nodi_carrier_cos[col_idx]
                * pod_demod_cos[col_idx]
            )
            mixed_nodi_leak = (
                2.0
                * pod_source
                * pod_carrier_cos[col_idx]
                * nodi_demod_cos[col_idx]
            )

            pod_true = alpha * mixed_pod_true + one_minus_alpha * pod_true
            nodi_true = alpha * mixed_nodi_true + one_minus_alpha * nodi_true
            pod_leak = alpha * mixed_pod_leak + one_minus_alpha * pod_leak
            nodi_leak = alpha * mixed_nodi_leak + one_minus_alpha * nodi_leak

            pod_true_i[row_idx, col_idx] = pod_true
            nodi_true_i[row_idx, col_idx] = nodi_true
            pod_leak_i[row_idx, col_idx] = pod_leak
            nodi_leak_i[row_idx, col_idx] = nodi_leak

    return pod_true_i, nodi_true_i, pod_leak_i, nodi_leak_i


@_optional_numba_njit(cache=True)
def _extract_best_peak_summary_2d_kernel(
    time_s: np.ndarray,
    signal_arr: np.ndarray,
    signal_eval: np.ndarray,
    thresholds: np.ndarray,
    min_width_samples: int,
    dt_s: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rows, cols = signal_eval.shape
    detected = np.zeros(rows, dtype=np.bool_)
    peak_heights = np.zeros(rows, dtype=np.float64)
    peak_signed_heights = np.zeros(rows, dtype=np.float64)
    peak_widths_s = np.zeros(rows, dtype=np.float64)
    peak_times_s = np.zeros(rows, dtype=np.float64)
    if cols < 3:
        return (
            detected,
            peak_heights,
            peak_signed_heights,
            peak_widths_s,
            peak_times_s,
        )

    for row_idx in range(rows):
        threshold = thresholds[row_idx]
        best_idx = -1
        best_value = -np.inf
        for col_idx in range(1, cols - 1):
            value = signal_eval[row_idx, col_idx]
            if (
                value > signal_eval[row_idx, col_idx - 1]
                and value >= signal_eval[row_idx, col_idx + 1]
                and value >= threshold
                and value > best_value
            ):
                best_idx = col_idx
                best_value = value

        if best_idx < 0:
            continue

        left_min = np.inf
        for col_idx in range(best_idx + 1):
            value = signal_eval[row_idx, col_idx]
            if value < left_min:
                left_min = value

        right_min = np.inf
        for col_idx in range(best_idx, cols):
            value = signal_eval[row_idx, col_idx]
            if value < right_min:
                right_min = value

        prominence_base = left_min if left_min > right_min else right_min
        width_level = best_value - 0.5 * (best_value - prominence_base)

        left_false = -1
        for col_idx in range(best_idx):
            if not signal_eval[row_idx, col_idx] >= width_level:
                left_false = col_idx

        if left_false >= 0:
            left_base = left_false
            left_next = left_base + 1
            if left_next >= cols:
                left_next = cols - 1
            left_y0 = signal_eval[row_idx, left_base]
            left_y1 = signal_eval[row_idx, left_next]
            left_denom = left_y1 - left_y0
            left_frac = 0.0
            if abs(left_denom) > 1e-15:
                left_frac = (width_level - left_y0) / left_denom
            if left_frac < 0.0:
                left_frac = 0.0
            elif left_frac > 1.0:
                left_frac = 1.0
            left_ip = float(left_base) + left_frac
        else:
            left_ip = 0.0

        right_false = cols
        for col_idx in range(best_idx + 1, cols):
            if not signal_eval[row_idx, col_idx] >= width_level:
                right_false = col_idx
                break

        if right_false < cols:
            right_prev = right_false - 1
            if right_prev < 0:
                right_prev = 0
            right_y0 = signal_eval[row_idx, right_prev]
            right_y1 = signal_eval[row_idx, right_false]
            right_denom = right_y1 - right_y0
            right_frac = 0.0
            if abs(right_denom) > 1e-15:
                right_frac = (width_level - right_y0) / right_denom
            if right_frac < 0.0:
                right_frac = 0.0
            elif right_frac > 1.0:
                right_frac = 1.0
            right_ip = float(right_prev) + right_frac
        else:
            right_ip = float(cols - 1)

        width_samples = right_ip - left_ip
        if width_samples < 0.0:
            width_samples = 0.0

        if width_samples >= min_width_samples:
            detected[row_idx] = True
            peak_heights[row_idx] = best_value
            peak_signed_heights[row_idx] = signal_arr[row_idx, best_idx]
            peak_widths_s[row_idx] = width_samples * dt_s
            peak_times_s[row_idx] = time_s[best_idx]

    return (
        detected,
        peak_heights,
        peak_signed_heights,
        peak_widths_s,
        peak_times_s,
    )


_WORKER_SHARED_CONTEXT: dict[str, object] | None = None
_PARTICLE_MODEL_DIAGNOSTIC_FIELDS = (
    "particle_family",
    "particle_family_status",
    "particle_optical_model",
    "structured_particle_model_status",
    "structured_particle_key",
    "structured_particle_preset_name",
    "EV_label",
    "EV_claim_level",
    "exosome_biogenesis_claim",
    "biogenesis_claim",
    "material_dataset",
    "material_db_coverage_status",
    "tsuyama_AuAg_multispectral_supported",
    "medium_wall_dispersion_status",
    "material_db_gold_status",
    "material_db_silver_status",
    "particle_material_model_mode",
    "particle_material_dataset_key",
    "particle_material_dataset_source",
    "particle_material_dataset_type",
    "particle_material_wavelength_status",
    "particle_material_temperature_correction_status",
    "particle_material_uncertainty_status",
    "metal_size_damping",
    "metal_size_damping_status",
    "ligand_shell",
    "ligand_shell_status",
    "medium_dispersion",
    "medium_dispersion_status",
    "wall_dispersion",
    "wall_dispersion_status",
    "shape_model",
    "anisotropic_shell_model",
    "orientation_average_status",
    "shape_uncertainty_status",
    "EV_sample_preparation_status",
    "EV_isolation_method",
    "EV_aggregation_or_coisolate_status",
    "EV_ensemble_mode",
    "EV_ensemble_name",
    "EV_ensemble_member_index",
    "EV_ensemble_member_count",
    "EV_ensemble_member_preset",
    "EV_ensemble_status",
    "EV_core_RI_nominal",
    "EV_shell_RI_nominal",
    "EV_shell_thickness_m",
    "EV_uncertainty_inputs",
    "size_distribution_uncertainty",
    "core_RI_uncertainty",
    "shell_RI_uncertainty",
    "shell_thickness_uncertainty",
    "anisotropy_uncertainty",
    "shape_uncertainty",
    "corona_coisolate_uncertainty",
    "isolation_batch_uncertainty",
    "particle_uncertainty_budget_model",
    "particle_uncertainty_budget_status",
    "uncertainty_propagation_mode",
    "uncertainty_inputs",
    "uncertainty_outputs",
    "uncertainty_output_confidence_status",
    "uncertainty_propagation_schema",
    "uncertainty_propagation_route_configured",
    "uncertainty_propagation_status",
    "uncertainty_required_input_schema",
    "uncertainty_propagated_outputs",
    "uncertainty_route_active",
    "uncertainty_propagation_blocker_summary",
    "peak_height_CI_available",
    "detection_rate_CI_available",
    "count_rate_CI_available",
    "classification_probability_CI_available",
)


class SweepCaseFailureError(RuntimeError):
    """Raised when one or more sweep cases fail and partial output is disabled."""

    def __init__(self, failures: list[dict]):
        self.failures = list(failures)
        super().__init__(_format_sweep_case_failure_summary(self.failures))


_COUNT_MODEL_DIAGNOSTIC_FIELDS = (
    "conditional_detection_rate",
    "conditional_detection_rate_definition",
    "conditional_detection_rate_source",
    "count_generation_model",
    "per_event_detectability_boundary",
    "count_prediction_model",
    "count_prediction_status",
    "count_prediction_claim_level",
    "number_concentration_m3",
    "count_observation_window_s",
    "accessible_area_m2",
    "accessible_area_status",
    "volumetric_flow_rate_m3_s",
    "volumetric_flow_rate_source",
    "poisson_arrival_process_status",
    "flux_conditioned_initial_distribution_status",
    "crossing_conditioned_transport_status",
    "event_rate_Hz",
    "expected_events_in_window",
    "detected_event_rate_before_deadtime_Hz",
    "predicted_count_rate_Hz",
    "predicted_counts_in_window",
    "missed_event_rate_Hz",
    "count_dead_time_s",
    "dead_time_model",
    "dead_time_limited_count_rate_Hz",
    "dead_time_loss_fraction",
    "blank_false_positive_rate_Hz",
    "blank_false_positive_correction_status",
    "missed_event_correction_status",
    "multi_occupancy_window_s",
    "focus_occupancy_mean",
    "multi_occupancy_probability",
    "occupancy_correction_status",
    "dead_time_correction_status",
    "single_particle_condition_status",
    "wall_interaction_model",
    "wall_interaction_status",
    "zeta_potential_particle_mV",
    "zeta_potential_wall_mV",
    "ionic_strength_M",
    "adsorption_probability_per_length_m",
    "adsorption_or_clogging_exclusion_status",
    "count_rate_source",
    "count_rate_confidence_status",
    "count_prediction_uncertainty_status",
)
_INTERFACE_CORRECTION_DIAGNOSTIC_FIELDS = (
    "interface_correction_mode",
    "interface_correction_input_contract_schema",
    "interface_required_inputs",
    "interface_missing_inputs",
    "interface_api_boundary_status",
    "interface_correction_status",
    "interface_correction_priority",
    "interface_correction_applied_to",
    "interface_correction_particle_family",
    "interface_correction_active",
    "interface_incident_field_correction",
    "interface_particle_polarizability_correction",
    "interface_radiation_pattern_collection_correction",
    "interface_correction_claim_level",
    "interface_output_sensitivity_status",
    "interface_phase_or_polarity_sensitive_output",
    "interface_angular_pattern_sensitive_output",
    "interface_dipole_surrogate_validity",
    "interface_quantitative_claim_blocker_summary",
    "homogeneous_medium_mie_assumption",
    "nearest_wall_gap_nominal_m",
    "lambda_medium_m",
    "eta_interface",
    "eta_lambda",
    "interface_fullwave_required",
    "interface_fullwave_reason",
    "interface_escalation_route",
)
_PHOTOTHERMAL_POD_DIAGNOSTIC_FIELDS = (
    "thermal_pod_model",
    "thermal_pod_input_contract_schema",
    "thermal_pod_required_inputs",
    "thermal_pod_missing_inputs",
    "thermal_pod_api_boundary_status",
    "thermal_pod_model_status",
    "pod_quantitative_amplitude_available",
    "pod_quantitative_sign_available",
    "pod_quantitative_claim_level",
    "probe_wavelength_m",
    "excitation_wavelength_m",
    "probe_power_W",
    "excitation_power_W",
    "pod_quantitative_route_status",
    "pod_amplitude_model_boundary",
    "probe_wavelength_source",
    "pod_probe_reference_field_status",
    "probe_coherent_field_group_id",
    "excitation_incoherent_power_group_id",
    "pod_probe_excitation_wavelength_status",
    "pod_wavelength_grouping_status",
    "multi_wavelength_coherent_addition_policy",
    "multi_wavelength_power_addition_policy",
    "probe_excitation_wavelengths_separated",
    "probe_wavelength_fields_add_coherently",
    "excitation_wavelength_fields_never_add_to_probe_E_ref_E_sca",
    "pod_roi_sensitivity_derivative_status",
    "pod_signal_sign_source",
    "pod_thermal_spatial_distribution_status",
    "pod_roi_derivative_validity",
    "pod_absorption_cross_section_status",
    "pod_excitation_absorption_cross_section_status",
    "pod_heat_source_status",
    "pod_heat_diffusion_status",
    "pod_solvent_dn_dT_status",
    "pod_solvent_dn_dT_source",
    "pod_substrate_heat_contribution_status",
    "pod_detector_responsivity_status",
    "pod_detector_responsivity_source",
    "pod_spectral_filter_status",
    "pod_spectral_filter_source",
    "pod_modulation_response_status",
    "pod_thermal_validation_status",
    "pod_amplitude_quantitative_blocker_summary",
)
_CALIBRATION_STATE_EXTRA_FIELDS = (
    "calibration_state_machine_schema",
    "calibration_state_resolver_status",
    "calibration_lane_summary",
    "calibration_state_blocker_summary",
    "calibration_synthetic_fixture_active",
    "output_claim_level_resolved",
    "standard_particle_calibration_row_id",
    "standard_particle_calibration_row_index",
    "standard_particle_calibration_row_count",
    "standard_particle_calibration_data_role",
    "standard_particle_synthetic_fixture_active",
    "standard_particle_table_validation_status",
    "standard_particle_manifest_status",
    "standard_particle_manifest_validation_status",
    "standard_particle_manifest_path",
    "detector_unit_chain_schema",
    "detector_unit_chain_unlocked",
    "detector_unit_chain_status",
    "incident_power_density_status",
    "mie_differential_cross_section_status",
    "detector_etendue_status",
    "absolute_optical_throughput_status",
    "photodiode_responsivity_status",
    "transimpedance_gain_status",
    "adc_conversion_status",
    "lockin_voltage_unit_status",
    "detector_unit_chain_blocker_summary",
    "readout_sampling_output_claim_blocker_active",
    "readout_sampling_hard_gate_required_rate_Hz",
    "readout_sampling_hard_gate_passed",
    "baseline_normalized_absolute_route_blocker_active",
    "detector_unit_claim_allowed",
    "photon_unit_claim_allowed",
    "absolute_route_claim_blocker",
)
_COLLECTION_OPERATOR_EXTRA_FIELDS = (
    "collection_operator_calibration_row_id",
    "collection_operator_calibration_row_index",
    "collection_operator_calibration_row_count",
    "collection_operator_geometry_distance_report",
    "collection_operator_calibration_data_role",
    "collection_operator_synthetic_fixture_active",
    "collection_operator_table_validation_status",
    "collection_operator_manifest_status",
    "collection_operator_manifest_validation_status",
    "collection_operator_manifest_path",
    "bfp_roi_mask_schema",
    "bfp_roi_mask_path_configured",
    "bfp_roi_mask_calibrated",
    "bfp_roi_mask_source",
    "bfp_roi_mask_status",
    "bfp_roi_mask_claim_level",
    "bfp_roi_mask_data_role",
    "bfp_roi_mask_synthetic_fixture_active",
    "bfp_roi_mask_table_validation_status",
    "bfp_roi_mask_manifest_status",
    "bfp_roi_mask_manifest_validation_status",
    "bfp_roi_mask_manifest_path",
    "bfp_roi_mask_row_count",
    "bfp_roi_mask_required_field_groups_missing",
    "bfp_roi_mask_gate_passed",
    "bfp_pixel_to_angle_status",
    "slit_position_mapping_status",
    "pinhole_projection_status",
    "bfp_roi_required_inputs",
)
_REFERENCE_CALIBRATION_EXTRA_FIELDS = (
    "reference_calibration_row_id",
    "reference_calibration_row_index",
    "reference_calibration_row_count",
    "reference_calibration_data_role",
    "reference_calibration_synthetic_fixture_active",
    "reference_calibration_table_validation_status",
    "reference_calibration_manifest_status",
    "reference_calibration_manifest_validation_status",
    "reference_calibration_manifest_path",
)
_THRESHOLD_FALSE_ALARM_EXTRA_FIELDS = (
    "blank_false_positive_calibration_row_id",
    "blank_false_positive_calibration_row_index",
    "blank_false_positive_calibration_row_count",
    "blank_false_positive_calibration_data_role",
    "blank_false_positive_synthetic_fixture_active",
    "blank_false_positive_table_validation_status",
    "blank_false_positive_manifest_status",
    "blank_false_positive_manifest_validation_status",
    "blank_false_positive_manifest_path",
    "raw_blank_trace_bootstrap_schema",
    "raw_blank_trace_path_configured",
    "raw_blank_trace_bootstrap_supported",
    "raw_blank_trace_bootstrap_status",
    "raw_blank_trace_required_columns",
    "raw_blank_trace_bootstrap_outputs",
)
_MIE_INCIDENT_FIELD_DIAGNOSTIC_FIELDS = (
    "incident_field_model_for_mie",
    "local_plane_wave_validity",
    "mie_particle_radius_m",
    "mie_size_parameter",
    "mie_incident_beam_waist_min_m",
    "mie_radius_to_beam_waist_ratio",
    "mie_field_gradient_across_particle_status",
    "mie_incident_field_GLMT_required",
    "mie_incident_field_fullwave_required",
    "mie_incident_field_claim_level",
    "mie_illumination_geometry_source",
    "mie_illumination_NA",
    "mie_incident_field_blocker_summary",
)


@dataclass(frozen=True)
class SweepCaseResult:
    """Serializable result payload for one sweep case execution."""

    ok: bool
    case_idx: int
    total_cases: int
    case_key: str
    particle_name: str
    wavelength_m: float
    width_m: float
    depth_m: float
    summary: dict | None = None
    intrinsic: dict | None = None
    reference: dict | None = None
    case_runtime_seconds: float | None = None
    error: str | None = None

    def to_payload(self) -> dict:
        payload = {
            "ok": bool(self.ok),
            "case_idx": int(self.case_idx),
            "total_cases": int(self.total_cases),
            "case_key": self.case_key,
            "particle_name": self.particle_name,
            "wavelength_m": float(self.wavelength_m),
            "width_m": float(self.width_m),
            "depth_m": float(self.depth_m),
        }
        if self.summary is not None:
            payload["summary"] = self.summary
        if self.intrinsic is not None:
            payload["intrinsic"] = self.intrinsic
        if self.reference is not None:
            payload["reference"] = self.reference
        if self.case_runtime_seconds is not None:
            payload["case_runtime_seconds"] = float(self.case_runtime_seconds)
        if self.error is not None:
            payload["error"] = self.error
        return payload


@dataclass(frozen=True)
class _ReadoutContext:
    """Case-level lock-in basis reuse for one fixed time grid."""

    alpha: float
    pod_carrier_cos: np.ndarray
    pod_demod_cos: np.ndarray
    pod_demod_sin: np.ndarray
    nodi_carrier_cos: np.ndarray
    nodi_demod_cos: np.ndarray
    nodi_demod_sin: np.ndarray


@dataclass(frozen=True)
class _EventCaseContext:
    """Case-level event execution constants reused across event simulations."""

    transport_channel: Channel
    transport_cfg: SimulationConfig
    trajectory_context: TrajectoryContext
    scattering_projection_basis: str


def _build_event_case_context(
    channel: Channel,
    sim_cfg: SimulationConfig,
    *,
    particle_radius_m: float,
) -> _EventCaseContext:
    """Resolve transport/readout-invariant event settings once per case."""
    if sim_cfg.nanoconfinement_on:
        transport_channel = channel
        transport_cfg = sim_cfg
    else:
        transport_channel = Channel(
            width_m=channel.width_m * sim_cfg.free_solution_window_scale,
            depth_m=channel.depth_m * sim_cfg.free_solution_window_scale,
        )
        transport_cfg = copy(sim_cfg)
        transport_cfg.flow_profile_model = "plug"
        transport_cfg.diffusion_hindrance_model = "none"
        transport_cfg.reflecting_boundary = False
        transport_cfg.coupling_model = "constant"

    return _EventCaseContext(
        transport_channel=transport_channel,
        transport_cfg=transport_cfg,
        trajectory_context=build_trajectory_context(
            transport_channel,
            transport_cfg,
            particle_radius_m=particle_radius_m,
        ),
        scattering_projection_basis=resolve_projection_basis(
            sim_cfg.scattering_projection_mode
        ),
    )


def _stable_uint32_from_parts(*parts: object) -> int:
    """Return a deterministic NumPy-compatible seed from stable text parts."""
    text = "|".join(str(part) for part in parts)
    digest = hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "little") % (2**32)


def _build_case_random_identity(
    particle: Particle,
    medium: Medium,
    channel: Channel,
    optical: OpticalSystem,
) -> str:
    """Build the stable identity used for per-case random streams."""
    return (
        f"particle={particle.name}"
        f"|medium={medium.name}"
        f"|wavelength={float(optical.wavelength_m):.12e}"
        f"|width={float(channel.width_m):.12e}"
        f"|depth={float(channel.depth_m):.12e}"
    )


def _resolve_case_rng_seed(
    sim_cfg: SimulationConfig,
    case_identity: str,
) -> int | None:
    """Resolve the RNG seed for one case under the configured sequence policy."""
    if sim_cfg.random_sequence_policy == "common_random_numbers":
        return sim_cfg.random_seed
    return _stable_uint32_from_parts(
        "case_keyed_independent",
        sim_cfg.random_seed if sim_cfg.random_seed is not None else "unseeded",
        case_identity,
    )


def _build_event_position_unit_samples(
    *,
    n_events: int,
    policy: str,
    seed: int | None,
    case_identity: str,
) -> np.ndarray | None:
    """Build optional [0, 1) samples for low-variance initial positions."""
    if policy == "random":
        return None
    if n_events <= 0:
        return np.empty((0, 3), dtype=float)
    sampler_seed = _stable_uint32_from_parts(
        "event_position_sampling",
        policy,
        seed if seed is not None else "unseeded",
        case_identity,
    )
    if policy == "sobol_stratified":
        exponent = int(math.ceil(math.log2(max(n_events, 1))))
        sampler = qmc.Sobol(d=3, scramble=True, seed=sampler_seed)
        return np.asarray(sampler.random_base2(m=exponent), dtype=float)[:n_events]
    if policy == "stratified_grid":
        rng = np.random.default_rng(sampler_seed)
        nx = int(math.ceil(math.sqrt(n_events)))
        nz = int(math.ceil(n_events / nx))
        cells = [
            ((ix + 0.5) / nx, (iz + 0.5) / nz)
            for iz in range(nz)
            for ix in range(nx)
        ]
        order = rng.permutation(len(cells))[:n_events]
        samples = np.empty((n_events, 3), dtype=float)
        for row_idx, cell_idx in enumerate(order):
            samples[row_idx, 0] = cells[int(cell_idx)][0]
            samples[row_idx, 1] = cells[int(cell_idx)][1]
            samples[row_idx, 2] = rng.uniform(0.0, 1.0)
        return samples
    raise ValueError(f"Unknown event_sampling_policy: {policy}")


def _adaptive_event_budget_state(
    accumulator: "_BatchSummaryAccumulator",
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """Summarize adaptive event-budget convergence for the current batch."""
    total = accumulator.final_basis.total_events
    detection_half_width = _wilson_half_width(
        accumulator.final_basis.decision_detected_events,
        total,
        zero_total=1.0,
    )
    stable_half_width = _wilson_half_width(
        accumulator.final_basis.n_stable,
        total,
        zero_total=1.0,
    )
    max_half_width = max(detection_half_width, stable_half_width)
    target = float(sim_cfg.adaptive_wilson_half_width_target)
    converged = bool(
        sim_cfg.adaptive_event_budget_mode == "wilson_precision"
        and total >= int(sim_cfg.adaptive_min_events)
        and max_half_width <= target
    )
    return {
        "adaptive_event_budget_converged": converged,
        "adaptive_event_budget_detection_half_width": detection_half_width,
        "adaptive_event_budget_stable_half_width": stable_half_width,
        "adaptive_event_budget_max_half_width": max_half_width,
        "adaptive_event_budget_target_half_width": target,
    }


def _should_stop_adaptive_event_budget(
    accumulator: "_BatchSummaryAccumulator",
    sim_cfg: SimulationConfig,
) -> tuple[bool, str, dict[str, object]]:
    """Return whether the current batch can stop before n_events."""
    state = _adaptive_event_budget_state(accumulator, sim_cfg)
    if sim_cfg.adaptive_event_budget_mode == "fixed":
        return False, "fixed_event_budget", state
    total = accumulator.final_basis.total_events
    if total < int(sim_cfg.adaptive_min_events):
        return False, "below_min_events", state
    if total % int(sim_cfg.adaptive_check_interval) != 0:
        return False, "between_checkpoints", state
    if bool(state["adaptive_event_budget_converged"]):
        return True, "wilson_precision_target_met", state
    return False, "wilson_precision_target_not_met", state


def _set_worker_shared_context(shared_context: dict[str, object] | None) -> None:
    """Install or clear the per-process sweep context."""
    global _WORKER_SHARED_CONTEXT
    _WORKER_SHARED_CONTEXT = shared_context


def _get_worker_shared_context() -> dict[str, object] | None:
    """Return the active per-process sweep context when available."""
    return _WORKER_SHARED_CONTEXT


@dataclass(frozen=True)
class SweepRawResult:
    """Checkpoint-safe successful case payload before final scoring."""

    case_key: str
    particle_name: str
    wavelength_m: float
    width_m: float
    depth_m: float
    summary: dict
    intrinsic: dict
    reference: dict
    case_runtime_seconds: float | None = None

    @classmethod
    def from_case_result(cls, case_result: dict) -> "SweepRawResult":
        return cls(
            case_key=str(case_result["case_key"]),
            particle_name=str(case_result["particle_name"]),
            wavelength_m=float(case_result["wavelength_m"]),
            width_m=float(case_result["width_m"]),
            depth_m=float(case_result["depth_m"]),
            summary=case_result["summary"],
            intrinsic=case_result["intrinsic"],
            reference=case_result["reference"],
            case_runtime_seconds=(
                float(case_result["case_runtime_seconds"])
                if case_result.get("case_runtime_seconds") is not None
                else None
            ),
        )

    def to_payload(self) -> dict:
        payload = {
            "case_key": self.case_key,
            "particle_name": self.particle_name,
            "wavelength_m": float(self.wavelength_m),
            "width_m": float(self.width_m),
            "depth_m": float(self.depth_m),
            "summary": self.summary,
            "intrinsic": self.intrinsic,
            "reference": self.reference,
        }
        if self.case_runtime_seconds is not None:
            payload["case_runtime_seconds"] = float(self.case_runtime_seconds)
        return payload


def add_detector_noise(
    signal_trace: np.ndarray,
    time_s: np.ndarray,
    sim_cfg: SimulationConfig,
    rng: np.random.Generator,
    *,
    detected_intensity: np.ndarray | None = None,
    baseline_intensity: float | None = None,
) -> dict:
    """
    Add detector noise to a signal trace.

    Supports:
        - additive Gaussian/electronics noise via noise_std
        - optional baseline-aware shot-noise surrogate via shot_noise_scale
        - optional linear drift via noise_model="gaussian_plus_drift"

    Args:
        signal_trace: Clean signal (1D array).
        time_s: Time array (same length as signal_trace).
        sim_cfg: Simulation config (provides noise_model, noise_std, drift_slope).
        rng: Random number generator.

    Returns:
        dict with signal_noisy and noise.
    """
    noise = np.zeros_like(signal_trace, dtype=float)
    if sim_cfg.noise_std > 0:
        noise = noise + rng.normal(0, sim_cfg.noise_std, size=signal_trace.shape)

    shot_noise = np.zeros_like(signal_trace, dtype=float)
    shot_std = np.zeros_like(signal_trace, dtype=float)
    intensity_for_noise = np.zeros_like(signal_trace, dtype=float)
    baseline_floor = np.zeros_like(signal_trace, dtype=float)
    reference_dominated_mask = np.zeros_like(signal_trace, dtype=bool)
    if sim_cfg.shot_noise_scale > 0:
        if baseline_intensity is None:
            baseline_floor = np.zeros_like(signal_trace, dtype=float)
        else:
            baseline_arr = np.asarray(baseline_intensity, dtype=float)
            baseline_floor = (
                np.clip(baseline_arr, 0.0, None)
                if baseline_arr.ndim > 0
                else np.full_like(signal_trace, float(max(float(baseline_arr), 0.0)), dtype=float)
            )
        if detected_intensity is None:
            signal_plus_baseline = np.asarray(signal_trace, dtype=float) + baseline_floor
            intensity_for_noise = np.maximum(signal_plus_baseline, baseline_floor)
            reference_dominated_mask = baseline_floor >= signal_plus_baseline
        else:
            detected_arr = np.asarray(detected_intensity, dtype=float)
            intensity_for_noise = np.maximum(detected_arr, baseline_floor)
            reference_dominated_mask = baseline_floor >= detected_arr
        shot_std = sim_cfg.shot_noise_scale * np.sqrt(np.clip(intensity_for_noise, 0.0, None))
        shot_noise = rng.normal(0.0, 1.0, size=signal_trace.shape) * shot_std
        noise = noise + shot_noise

    if sim_cfg.noise_model == "gaussian_plus_drift":
        drift = sim_cfg.drift_slope * time_s
        noise = noise + drift
    elif sim_cfg.noise_model != "gaussian":
        raise ValueError(f"Unknown noise_model: {sim_cfg.noise_model}")

    signal_noisy = signal_trace + noise
    mean_shot_noise_std = (
        float(np.mean(np.abs(shot_std))) if sim_cfg.shot_noise_scale > 0 else 0.0
    )
    mean_intensity_proxy = (
        float(np.mean(intensity_for_noise))
        if sim_cfg.shot_noise_scale > 0
        else 0.0
    )
    mean_baseline_proxy = (
        float(np.mean(baseline_floor))
        if sim_cfg.shot_noise_scale > 0
        else 0.0
    )
    detector_noise_diagnostics = build_detector_noise_diagnostics(
        sim_cfg,
        mean_shot_noise_std=mean_shot_noise_std,
        mean_intensity_proxy=mean_intensity_proxy,
        mean_baseline_proxy=mean_baseline_proxy,
    )
    return {
        "signal_noisy": signal_noisy,
        "noise": noise,
        "shot_noise": shot_noise,
        "shot_noise_std_trace": shot_std,
        "shot_noise_intensity_proxy_trace": intensity_for_noise,
        "shot_noise_baseline_proxy_trace": baseline_floor,
        "shot_noise_reference_dominated_mask": reference_dominated_mask,
        "shot_noise_std_mean": mean_shot_noise_std,
        "shot_noise_reference_dominated_fraction": (
            float(np.mean(reference_dominated_mask))
            if sim_cfg.shot_noise_scale > 0
            else 0.0
        ),
        "mean_shot_noise_intensity_proxy": mean_intensity_proxy,
        "mean_shot_noise_baseline_proxy": mean_baseline_proxy,
        **detector_noise_diagnostics,
    }


def _draw_event_loop_order_block_randoms(
    *,
    rng: np.random.Generator,
    block_size: int,
    n_samples: int,
    sim_cfg: SimulationConfig,
    include_diffusion: bool,
) -> dict[str, np.ndarray | None]:
    """Draw per-event random arrays in scalar event-loop order for a block."""
    draw_specs = []
    diffusion_width = 2 * max(n_samples - 1, 0)
    if include_diffusion:
        draw_specs.append(("diffusion_draws", diffusion_width, 1.0))
    if sim_cfg.noise_std > 0:
        draw_specs.append(("detector_noise", n_samples, float(sim_cfg.noise_std)))
    if sim_cfg.shot_noise_scale > 0:
        draw_specs.append(("shot_standard", n_samples, 1.0))
    if sim_cfg.post_readout_noise_std > 0:
        post_scale = float(sim_cfg.post_readout_noise_std)
        draw_specs.extend(
            [
                ("post_detect_noise", n_samples, post_scale),
                ("post_nodi_noise", n_samples, post_scale),
                ("post_pod_noise", n_samples, post_scale),
            ]
        )

    draws_by_name: dict[str, np.ndarray | None] = {
        "diffusion_draws": None,
        "detector_noise": None,
        "shot_standard": None,
        "post_detect_noise": None,
        "post_nodi_noise": None,
        "post_pod_noise": None,
    }
    total_width = sum(width for _, width, _ in draw_specs)
    if total_width > 0 and block_size > 0:
        # One row is one scalar event's RNG stream: diffusion, detector,
        # shot, and post-readout lanes in the same order as simulate_one_event.
        event_order_draws = rng.standard_normal((block_size, total_width))
        cursor = 0
        for name, width, scale in draw_specs:
            if width <= 0:
                draws_by_name[name] = np.empty((block_size, 0), dtype=float)
                continue
            stop = cursor + width
            block = event_order_draws[:, cursor:stop]
            if scale != 1.0:
                block *= float(scale)
            draws_by_name[name] = block
            cursor = stop
        return draws_by_name

    diffusion_draws = (
        np.empty((block_size, diffusion_width), dtype=float)
        if include_diffusion
        else None
    )
    detector_noise = (
        np.empty((block_size, n_samples), dtype=float)
        if sim_cfg.noise_std > 0
        else None
    )
    shot_standard = (
        np.empty((block_size, n_samples), dtype=float)
        if sim_cfg.shot_noise_scale > 0
        else None
    )
    post_detect_noise = (
        np.empty((block_size, n_samples), dtype=float)
        if sim_cfg.post_readout_noise_std > 0
        else None
    )
    post_nodi_noise = (
        np.empty((block_size, n_samples), dtype=float)
        if sim_cfg.post_readout_noise_std > 0
        else None
    )
    post_pod_noise = (
        np.empty((block_size, n_samples), dtype=float)
        if sim_cfg.post_readout_noise_std > 0
        else None
    )

    for offset in range(block_size):
        if diffusion_draws is not None:
            diffusion_draws[offset] = rng.standard_normal(2 * max(n_samples - 1, 0))
        if detector_noise is not None:
            detector_noise[offset] = rng.normal(
                0,
                sim_cfg.noise_std,
                size=n_samples,
            )
        if shot_standard is not None:
            shot_standard[offset] = rng.normal(0.0, 1.0, size=n_samples)
        if post_detect_noise is not None:
            post_detect_noise[offset] = rng.normal(
                0,
                sim_cfg.post_readout_noise_std,
                size=n_samples,
            )
            post_nodi_noise[offset] = rng.normal(
                0,
                sim_cfg.post_readout_noise_std,
                size=n_samples,
            )
            post_pod_noise[offset] = rng.normal(
                0,
                sim_cfg.post_readout_noise_std,
                size=n_samples,
            )

    return {
        "diffusion_draws": diffusion_draws,
        "detector_noise": detector_noise,
        "shot_standard": shot_standard,
        "post_detect_noise": post_detect_noise,
        "post_nodi_noise": post_nodi_noise,
        "post_pod_noise": post_pod_noise,
    }


_EVENT_BLOCK_RANDOM_LANES = (
    "diffusion_draws",
    "detector_noise",
    "shot_standard",
    "post_detect_noise",
    "post_pod_noise",
)


@dataclass
class _EventBlockRandomState:
    streams: dict[str, np.random.Generator]
    buffers: dict[tuple[str, tuple[int, int]], np.ndarray] = field(
        default_factory=dict
    )


def _build_event_block_random_state(seed: int | None) -> _EventBlockRandomState:
    """Build independent per-lane streams for statistical block RNG mode."""
    root = np.random.SeedSequence(None if seed is None else int(seed))
    child_sequences = root.spawn(len(_EVENT_BLOCK_RANDOM_LANES))
    streams = {
        lane: np.random.default_rng(child_sequence)
        for lane, child_sequence in zip(_EVENT_BLOCK_RANDOM_LANES, child_sequences)
    }
    return _EventBlockRandomState(streams=streams)


def _event_block_random_buffer(
    random_state: _EventBlockRandomState,
    lane: str,
    shape: tuple[int, int],
) -> np.ndarray:
    key = (lane, (int(shape[0]), int(shape[1])))
    buffer = random_state.buffers.get(key)
    if buffer is None:
        buffer = np.empty(shape, dtype=np.float32)
        random_state.buffers[key] = buffer
    return buffer


def _draw_block_lane_order_block_randoms(
    *,
    random_state: _EventBlockRandomState,
    block_size: int,
    n_samples: int,
    sim_cfg: SimulationConfig,
    include_diffusion: bool,
) -> dict[str, np.ndarray | None]:
    """Draw per-lane block random arrays without preserving scalar draw order."""
    diffusion_width = 2 * max(n_samples - 1, 0)
    draws_by_name: dict[str, np.ndarray | None] = {
        "diffusion_draws": None,
        "detector_noise": None,
        "shot_standard": None,
        "post_detect_noise": None,
        "post_nodi_noise": None,
        "post_pod_noise": None,
    }
    if block_size <= 0:
        return draws_by_name

    if include_diffusion:
        diffusion_draws = _event_block_random_buffer(
            random_state,
            "diffusion_draws",
            (block_size, diffusion_width),
        )
        random_state.streams["diffusion_draws"].standard_normal(
            dtype=np.float32,
            out=diffusion_draws,
        )
        draws_by_name["diffusion_draws"] = diffusion_draws
    if sim_cfg.noise_std > 0:
        detector_noise = _event_block_random_buffer(
            random_state,
            "detector_noise",
            (block_size, n_samples),
        )
        random_state.streams["detector_noise"].standard_normal(
            dtype=np.float32,
            out=detector_noise,
        )
        detector_noise *= np.float32(sim_cfg.noise_std)
        draws_by_name["detector_noise"] = detector_noise
    if sim_cfg.shot_noise_scale > 0:
        shot_standard = _event_block_random_buffer(
            random_state,
            "shot_standard",
            (block_size, n_samples),
        )
        random_state.streams["shot_standard"].standard_normal(
            dtype=np.float32,
            out=shot_standard,
        )
        draws_by_name["shot_standard"] = shot_standard
    if sim_cfg.post_readout_noise_std > 0:
        post_scale = np.float32(sim_cfg.post_readout_noise_std)
        post_detect_noise = _event_block_random_buffer(
            random_state,
            "post_detect_noise",
            (block_size, n_samples),
        )
        random_state.streams["post_detect_noise"].standard_normal(
            dtype=np.float32,
            out=post_detect_noise,
        )
        post_detect_noise *= post_scale
        draws_by_name["post_detect_noise"] = post_detect_noise
        post_pod_noise = _event_block_random_buffer(
            random_state,
            "post_pod_noise",
            (block_size, n_samples),
        )
        random_state.streams["post_pod_noise"].standard_normal(
            dtype=np.float32,
            out=post_pod_noise,
        )
        post_pod_noise *= post_scale
        draws_by_name["post_pod_noise"] = post_pod_noise

    return draws_by_name


def _add_detector_noise_block_from_draws(
    signal_trace: np.ndarray,
    time_s: np.ndarray,
    sim_cfg: SimulationConfig,
    *,
    detector_noise: np.ndarray | None,
    shot_standard: np.ndarray | None,
    detected_intensity: np.ndarray | None = None,
    baseline_intensity: np.ndarray | float | None = None,
) -> dict:
    """Add detector noise using arrays pre-drawn in scalar event order."""
    signal_arr = np.asarray(signal_trace, dtype=float)
    noise: np.ndarray | None = None
    if detector_noise is not None:
        noise = np.asarray(detector_noise, dtype=float)

    shot_noise: np.ndarray | float = 0.0
    shot_std: np.ndarray | float = 0.0
    intensity_for_noise: np.ndarray | float = 0.0
    baseline_floor: np.ndarray | float = 0.0
    reference_dominated_mask: np.ndarray | bool = False
    if sim_cfg.shot_noise_scale > 0:
        if baseline_intensity is None:
            baseline_floor = np.zeros_like(signal_arr, dtype=float)
        else:
            baseline_arr = np.asarray(baseline_intensity, dtype=float)
            baseline_floor = (
                np.clip(baseline_arr, 0.0, None)
                if baseline_arr.ndim > 0
                else np.full_like(
                    signal_arr,
                    float(max(float(baseline_arr), 0.0)),
                    dtype=float,
                )
            )
        if detected_intensity is None:
            signal_plus_baseline = signal_arr + baseline_floor
            intensity_for_noise = np.maximum(signal_plus_baseline, baseline_floor)
            reference_dominated_mask = baseline_floor >= signal_plus_baseline
        else:
            detected_arr = np.asarray(detected_intensity, dtype=float)
            intensity_for_noise = np.maximum(detected_arr, baseline_floor)
            reference_dominated_mask = baseline_floor >= detected_arr
        shot_std = sim_cfg.shot_noise_scale * np.sqrt(
            np.clip(intensity_for_noise, 0.0, None)
        )
        if shot_standard is None:
            raise ValueError("shot_standard draws are required when shot noise is enabled")
        shot_noise = shot_std.copy()
        np.multiply(shot_noise, shot_standard, out=shot_noise, casting="unsafe")
        noise = np.zeros_like(signal_arr, dtype=float) if noise is None else noise.copy()
        noise += shot_noise

    if sim_cfg.noise_model == "gaussian_plus_drift":
        noise = np.zeros_like(signal_arr, dtype=float) if noise is None else noise.copy()
        noise += sim_cfg.drift_slope * time_s
    elif sim_cfg.noise_model != "gaussian":
        raise ValueError(f"Unknown noise_model: {sim_cfg.noise_model}")

    if noise is None:
        noise = np.zeros_like(signal_arr, dtype=float)
    signal_noisy = signal_arr + noise
    mean_shot_noise_std = (
        float(np.mean(np.abs(shot_std))) if sim_cfg.shot_noise_scale > 0 else 0.0
    )
    mean_intensity_proxy = (
        float(np.mean(intensity_for_noise))
        if sim_cfg.shot_noise_scale > 0
        else 0.0
    )
    mean_baseline_proxy = (
        float(np.mean(baseline_floor))
        if sim_cfg.shot_noise_scale > 0
        else 0.0
    )
    detector_noise_diagnostics = build_detector_noise_diagnostics(
        sim_cfg,
        mean_shot_noise_std=mean_shot_noise_std,
        mean_intensity_proxy=mean_intensity_proxy,
        mean_baseline_proxy=mean_baseline_proxy,
    )
    return {
        "signal_noisy": signal_noisy,
        "noise": noise,
        "shot_noise": shot_noise,
        "shot_noise_std_trace": shot_std,
        "shot_noise_intensity_proxy_trace": intensity_for_noise,
        "shot_noise_baseline_proxy_trace": baseline_floor,
        "shot_noise_reference_dominated_mask": reference_dominated_mask,
        "shot_noise_std_mean": mean_shot_noise_std,
        "shot_noise_reference_dominated_fraction": (
            float(np.mean(reference_dominated_mask))
            if sim_cfg.shot_noise_scale > 0
            else 0.0
        ),
        "mean_shot_noise_intensity_proxy": mean_intensity_proxy,
        "mean_shot_noise_baseline_proxy": mean_baseline_proxy,
        **detector_noise_diagnostics,
    }


def add_post_readout_noise(
    signal_trace: np.ndarray,
    time_s: np.ndarray,
    sim_cfg: SimulationConfig,
    rng: np.random.Generator,
) -> dict:
    """
    Add post-readout perturbations after the raw/readout surrogate stage.

    This is a lightweight proxy for lock-in output noise / baseline bias. It is
    intentionally separated from the raw detector noise so later analysis can
    distinguish "optical/raw noise" from "post-readout threshold drift".
    """
    if sim_cfg.post_readout_noise_std <= 0:
        noise = np.zeros_like(signal_trace, dtype=float)
    else:
        noise = rng.normal(0, sim_cfg.post_readout_noise_std, size=signal_trace.shape)

    if sim_cfg.post_readout_colored_noise_std > 0:
        noise = noise + _draw_post_readout_colored_noise(
            time_s,
            np.asarray(signal_trace, dtype=float).shape,
            sim_cfg,
            rng,
        )

    if sim_cfg.post_readout_drift_slope > 0:
        noise = noise + sim_cfg.post_readout_drift_slope * time_s

    signal_post = signal_trace + noise
    return {
        "signal_post_readout": signal_post,
        "post_readout_noise": noise,
    }


def _draw_post_readout_colored_noise(
    time_s: np.ndarray,
    shape: tuple[int, ...],
    sim_cfg: SimulationConfig,
    rng: np.random.Generator,
) -> np.ndarray:
    """Draw a stationary AR(1)-like colored-noise trace on the readout grid."""
    scale = float(sim_cfg.post_readout_colored_noise_std)
    if scale <= 0.0:
        return np.zeros(shape, dtype=float)
    time_arr = np.asarray(time_s, dtype=float)
    if time_arr.size < 2:
        return rng.normal(0.0, scale, size=shape)
    dt = float(np.median(np.diff(time_arr)))
    tau = max(float(sim_cfg.post_readout_colored_noise_tau_s), 1e-15)
    alpha = float(np.clip(np.exp(-dt / tau), 0.0, np.nextafter(1.0, 0.0)))
    innovation_std = scale * float(np.sqrt(max(1.0 - alpha * alpha, 0.0)))
    colored = np.empty(shape, dtype=float)
    if len(shape) == 1:
        colored[0] = rng.normal(0.0, scale)
        for idx in range(1, shape[0]):
            colored[idx] = alpha * colored[idx - 1] + rng.normal(
                0.0,
                innovation_std,
            )
        return colored
    flat = colored.reshape((-1, shape[-1]))
    flat[:, 0] = rng.normal(0.0, scale, size=flat.shape[0])
    for idx in range(1, flat.shape[1]):
        flat[:, idx] = alpha * flat[:, idx - 1] + rng.normal(
            0.0,
            innovation_std,
            size=flat.shape[0],
        )
    return colored


def _add_post_readout_noise_from_draws(
    signal_trace: np.ndarray,
    time_s: np.ndarray,
    sim_cfg: SimulationConfig,
    noise_draws: np.ndarray | None,
) -> dict:
    """Add post-readout noise using pre-drawn Gaussian samples."""
    signal_arr = np.asarray(signal_trace, dtype=float)
    if noise_draws is None:
        noise = np.zeros_like(signal_arr, dtype=float)
    else:
        noise = np.zeros_like(signal_arr, dtype=float)
        np.add(noise, noise_draws, out=noise, casting="unsafe")

    if sim_cfg.post_readout_drift_slope > 0:
        noise += sim_cfg.post_readout_drift_slope * time_s

    return {
        "signal_post_readout": signal_arr + noise,
        "post_readout_noise": noise,
    }


def _advance_post_readout_noise_rng(
    signal_shape: tuple[int, ...],
    sim_cfg: SimulationConfig,
    rng: np.random.Generator,
    time_s: np.ndarray | None = None,
) -> None:
    """Preserve post-readout RNG order when a diagnostic lane is not retained."""
    if sim_cfg.post_readout_noise_std > 0:
        rng.normal(0, sim_cfg.post_readout_noise_std, size=signal_shape)
    if sim_cfg.post_readout_colored_noise_std > 0:
        time_arr = (
            np.arange(signal_shape[-1], dtype=float)
            if time_s is None
            else np.asarray(time_s, dtype=float)
        )
        _draw_post_readout_colored_noise(time_arr, signal_shape, sim_cfg, rng)


def _first_order_lowpass_alpha(
    signal: np.ndarray,
    alpha: float,
) -> np.ndarray:
    """First-order low-pass with a precomputed alpha coefficient."""
    if alpha <= 0:
        return np.asarray(signal, dtype=float).copy()

    signal_arr = np.asarray(signal, dtype=float)
    if signal_arr.size <= 1:
        return signal_arr.copy()
    if _numba_njit is not None and signal_arr.ndim == 2:
        return _first_order_lowpass_alpha_2d_kernel(
            np.ascontiguousarray(signal_arr, dtype=np.float64),
            float(alpha),
        )

    first_sample = np.take(signal_arr, 0, axis=-1)
    zi = np.expand_dims((1.0 - alpha) * first_sample, axis=-1)
    out, _ = lfilter(
        [alpha],
        [1.0, -(1.0 - alpha)],
        signal_arr,
        axis=-1,
        zi=zi,
    )
    return np.asarray(out, dtype=float)


def _build_lockin_basis(
    time_s: np.ndarray,
    carrier_frequency_Hz: float,
    demod_frequency_Hz: float,
    reference_phase_rad: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Precompute cosine/sine bases reused across events on one time grid."""
    time_arr = np.asarray(time_s, dtype=float)
    phase_carrier = 2.0 * np.pi * float(carrier_frequency_Hz) * time_arr
    phase_demod = (
        2.0 * np.pi * float(demod_frequency_Hz) * time_arr
        + float(reference_phase_rad)
    )
    return (
        np.cos(phase_carrier),
        np.cos(phase_demod),
        np.sin(phase_demod),
    )


def _build_readout_context(
    time_s: np.ndarray,
    sim_cfg: SimulationConfig,
) -> _ReadoutContext | None:
    """Build reusable lock-in bases for one case-level time axis."""
    if sim_cfg.readout_model != "lockin_surrogate":
        return None

    time_arr = np.asarray(time_s, dtype=float)
    if time_arr.size > 1:
        dt = float(time_arr[1] - time_arr[0])
    else:
        dt = float(sim_cfg.lockin_time_constant_s)
    tau_s = float(sim_cfg.lockin_time_constant_s)
    alpha = dt / (tau_s + dt) if tau_s > 0 else 0.0
    pod_carrier_cos, pod_demod_cos, pod_demod_sin = _build_lockin_basis(
        time_arr,
        sim_cfg.pod_lockin_frequency_Hz,
        sim_cfg.pod_lockin_frequency_Hz,
        sim_cfg.pod_reference_phase_rad,
    )
    nodi_carrier_cos, nodi_demod_cos, nodi_demod_sin = _build_lockin_basis(
        time_arr,
        sim_cfg.nodi_lockin_frequency_Hz,
        sim_cfg.nodi_lockin_frequency_Hz,
        sim_cfg.nodi_reference_phase_rad,
    )
    return _ReadoutContext(
        alpha=float(alpha),
        pod_carrier_cos=pod_carrier_cos,
        pod_demod_cos=pod_demod_cos,
        pod_demod_sin=pod_demod_sin,
        nodi_carrier_cos=nodi_carrier_cos,
        nodi_demod_cos=nodi_demod_cos,
        nodi_demod_sin=nodi_demod_sin,
    )


def _lockin_demod_components_precomputed(
    source: np.ndarray,
    alpha: float,
    carrier_cos: np.ndarray,
    demod_cos: np.ndarray,
    demod_sin: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Lock-in demodulation using precomputed carrier/reference bases."""
    source_arr = np.asarray(source, dtype=float)
    modulated = source_arr * carrier_cos
    mixed_i = 2.0 * modulated * demod_cos
    mixed_q = -2.0 * modulated * demod_sin
    i_lp = _first_order_lowpass_alpha(mixed_i, alpha)
    q_lp = _first_order_lowpass_alpha(mixed_q, alpha)
    magnitude = np.sqrt(np.maximum(i_lp * i_lp + q_lp * q_lp, 0.0))
    return i_lp, q_lp, magnitude


def _lockin_demod_in_phase_precomputed(
    source: np.ndarray,
    alpha: float,
    carrier_cos: np.ndarray,
    demod_cos: np.ndarray,
) -> np.ndarray:
    """Lock-in demodulation fast path when only the in-phase observable is needed."""
    source_arr = np.asarray(source, dtype=float)
    if _numba_njit is not None and source_arr.ndim == 2:
        return _lockin_in_phase_lowpass_2d_kernel(
            np.ascontiguousarray(source_arr, dtype=np.float64),
            float(alpha),
            np.ascontiguousarray(carrier_cos, dtype=np.float64),
            np.ascontiguousarray(demod_cos, dtype=np.float64),
        )
    modulated = source_arr * carrier_cos
    mixed_i = 2.0 * modulated * demod_cos
    return _first_order_lowpass_alpha(mixed_i, alpha)


def _select_lockin_observable_components(
    signal_i: np.ndarray,
    signal_mag: np.ndarray,
    observable_mode: str,
) -> np.ndarray:
    """Pick the detector-facing observable from explicit I/Q arrays."""
    if observable_mode == "in_phase":
        return np.asarray(signal_i, dtype=float)
    if observable_mode == "magnitude":
        return np.asarray(signal_mag, dtype=float)
    raise ValueError(f"Unknown readout_observable_mode: {observable_mode}")


def _uses_bandpass_envelope_numerical_route(sim_cfg: SimulationConfig) -> bool:
    return bool(
        str(sim_cfg.readout_internal_demod_route) == "analytic_lockin_surrogate"
        and str(sim_cfg.nodi_readout_semantics) == "bandpass_envelope_surrogate"
        and str(sim_cfg.readout_observable_mode) == "magnitude"
    )


def _pod_frequency_response_gain(sim_cfg: SimulationConfig) -> float:
    """
    Minimal POD frequency-response surrogate.

    The intent is not to reproduce a full thermal transport model. It only
    captures the first-order trend that lower POD modulation frequency leads to
    a stronger photothermal-like envelope and stronger leakage into the POD
    demodulation lane.
    """
    if sim_cfg.pod_frequency_response_model == "flat":
        return 1.0

    ref_f = max(float(sim_cfg.pod_frequency_response_reference_Hz), 1e-9)
    pod_f = max(float(sim_cfg.pod_lockin_frequency_Hz), 1e-9)
    exponent = float(sim_cfg.pod_frequency_response_exponent)
    raw_gain = (ref_f / pod_f) ** exponent
    return float(
        np.clip(
            raw_gain,
            float(sim_cfg.pod_frequency_response_min_gain),
            float(sim_cfg.pod_frequency_response_max_gain),
        )
    )


def _readout_transit_diagnostics(
    sim_cfg: SimulationConfig,
    transit_time_s: float | np.ndarray | None,
) -> dict[str, Any]:
    transit_arr = (
        np.asarray(transit_time_s, dtype=float)
        if transit_time_s is not None
        else np.asarray(0.0)
    )
    if transit_time_s is not None and transit_arr.ndim > 0:
        return _nodi_transit_response_array(sim_cfg, transit_arr)
    return _nodi_transit_response_diagnostics(sim_cfg, transit_time_s)


def _apply_bandpass_envelope_readout(
    raw: np.ndarray,
    sim_cfg: SimulationConfig,
    context: _ReadoutContext,
    transit_time_s: float | np.ndarray | None,
) -> dict[str, Any]:
    """
    Apply the EV/NODI analytic envelope surrogate without sampled carrier mixing.

    The branch uses the existing first-order lock-in time constant as a compact
    bandpass/envelope surrogate: slow content estimates the POD-like baseline,
    the residual is low-pass filtered as the NODI transient band, and the
    detector-facing observable is its magnitude.
    """
    pod_source = _first_order_lowpass_alpha(raw, context.alpha)
    nodi_band = _first_order_lowpass_alpha(raw - pod_source, context.alpha)
    pod_frequency_gain = _pod_frequency_response_gain(sim_cfg)
    pod_true_i = pod_source * float(pod_frequency_gain)
    pod_true_q = np.zeros_like(pod_true_i, dtype=float)
    pod_true_mag = np.abs(pod_true_i)

    nodi_transit_diag = _readout_transit_diagnostics(sim_cfg, transit_time_s)
    nodi_transit_gain = _broadcast_event_gain(
        nodi_transit_diag["nodi_transit_bandwidth_gain"],
        nodi_band,
    )
    nodi_true_i = nodi_band * nodi_transit_gain
    nodi_true_q = np.zeros_like(nodi_true_i, dtype=float)
    nodi_true_mag = np.abs(nodi_true_i)

    pod_leak_i = nodi_true_i
    pod_leak_q = np.zeros_like(pod_leak_i, dtype=float)
    pod_leak_mag = np.abs(pod_leak_i)
    nodi_leak_i = pod_true_i
    nodi_leak_q = np.zeros_like(nodi_leak_i, dtype=float)
    nodi_leak_mag = np.abs(nodi_leak_i)

    signal_pod_i = pod_true_i + sim_cfg.nodi_to_pod_crosstalk * pod_leak_i
    signal_pod_q = pod_true_q + sim_cfg.nodi_to_pod_crosstalk * pod_leak_q
    signal_nodi_i = nodi_true_i + sim_cfg.pod_to_nodi_crosstalk * nodi_leak_i
    signal_nodi_q = nodi_true_q + sim_cfg.pod_to_nodi_crosstalk * nodi_leak_q
    signal_pod_mag = np.sqrt(
        np.maximum(signal_pod_i * signal_pod_i + signal_pod_q * signal_pod_q, 0.0)
    )
    signal_nodi_mag = np.sqrt(
        np.maximum(
            signal_nodi_i * signal_nodi_i + signal_nodi_q * signal_nodi_q,
            0.0,
        )
    )

    signal_pod = _select_lockin_observable_components(
        signal_pod_i,
        signal_pod_mag,
        sim_cfg.readout_observable_mode,
    )
    signal_nodi = _select_lockin_observable_components(
        signal_nodi_i,
        signal_nodi_mag,
        sim_cfg.readout_observable_mode,
    )

    return {
        "signal_detect": signal_nodi,
        "signal_nodi": signal_nodi,
        "signal_pod": signal_pod,
        "signal_nodi_true": _select_lockin_observable_components(
            nodi_true_i,
            nodi_true_mag,
            sim_cfg.readout_observable_mode,
        ),
        "signal_pod_true": _select_lockin_observable_components(
            pod_true_i,
            pod_true_mag,
            sim_cfg.readout_observable_mode,
        ),
        "signal_nodi_leak": _select_lockin_observable_components(
            nodi_leak_i,
            nodi_leak_mag,
            sim_cfg.readout_observable_mode,
        ),
        "signal_pod_leak": _select_lockin_observable_components(
            pod_leak_i,
            pod_leak_mag,
            sim_cfg.readout_observable_mode,
        ),
        "pod_frequency_response_model": sim_cfg.pod_frequency_response_model,
        "pod_frequency_response_gain": float(pod_frequency_gain),
        "nodi_transit_response_model": str(
            nodi_transit_diag["nodi_transit_response_model"]
        ),
        "nodi_transit_bandwidth_Hz": nodi_transit_diag["nodi_transit_bandwidth_Hz"],
        "nodi_transit_bandwidth_gain": nodi_transit_diag[
            "nodi_transit_bandwidth_gain"
        ],
        "nodi_bandwidth_limited_fraction": nodi_transit_diag[
            "nodi_bandwidth_limited_fraction"
        ],
        "nodi_lockin_bandwidth_Hz": float(nodi_transit_diag["nodi_lockin_bandwidth_Hz"]),
        "readout_numerical_route": "bandpass_envelope_response_surrogate",
        "signal_nodi_i": signal_nodi_i,
        "signal_nodi_q": signal_nodi_q,
        "signal_nodi_mag": signal_nodi_mag,
        "signal_pod_i": signal_pod_i,
        "signal_pod_q": signal_pod_q,
        "signal_pod_mag": signal_pod_mag,
        "signal_nodi_true_i": nodi_true_i,
        "signal_nodi_true_q": nodi_true_q,
        "signal_nodi_true_mag": nodi_true_mag,
        "signal_pod_true_i": pod_true_i,
        "signal_pod_true_q": pod_true_q,
        "signal_pod_true_mag": pod_true_mag,
    }


def _nodi_transit_response_diagnostics(
    sim_cfg: SimulationConfig,
    transit_time_s: float | None,
) -> dict[str, float | str]:
    """Minimal NODI transit-bandwidth surrogate."""
    model = str(sim_cfg.nodi_transit_response_model)
    lockin_bandwidth_Hz = (
        1.0 / (2.0 * np.pi * float(sim_cfg.lockin_time_constant_s))
        if sim_cfg.lockin_time_constant_s > 0
        else 0.0
    )
    if model == "flat":
        return {
            "nodi_transit_response_model": model,
            "nodi_transit_bandwidth_Hz": 0.0,
            "nodi_transit_bandwidth_gain": 1.0,
            "nodi_bandwidth_limited_fraction": 0.0,
            "nodi_lockin_bandwidth_Hz": float(lockin_bandwidth_Hz),
        }

    transit_time = max(float(transit_time_s or 0.0), 0.0)
    if transit_time <= 0 or lockin_bandwidth_Hz <= 0:
        return {
            "nodi_transit_response_model": model,
            "nodi_transit_bandwidth_Hz": 0.0,
            "nodi_transit_bandwidth_gain": 1.0,
            "nodi_bandwidth_limited_fraction": 0.0,
            "nodi_lockin_bandwidth_Hz": float(lockin_bandwidth_Hz),
        }

    transit_bandwidth_Hz = 1.0 / transit_time
    raw_gain = 1.0 / np.sqrt(1.0 + (transit_bandwidth_Hz / lockin_bandwidth_Hz) ** 2)
    gain = float(
        np.clip(
            raw_gain,
            float(sim_cfg.nodi_transit_response_min_gain),
            float(sim_cfg.nodi_transit_response_max_gain),
        )
    )
    return {
        "nodi_transit_response_model": model,
        "nodi_transit_bandwidth_Hz": float(transit_bandwidth_Hz),
        "nodi_transit_bandwidth_gain": gain,
        "nodi_bandwidth_limited_fraction": float(max(0.0, 1.0 - gain)),
        "nodi_lockin_bandwidth_Hz": float(lockin_bandwidth_Hz),
    }


def _nodi_transit_response_array(
    sim_cfg: SimulationConfig,
    transit_time_s: np.ndarray,
) -> dict[str, np.ndarray | float | str]:
    """Vectorized NODI transit-bandwidth diagnostics for event blocks."""
    model = str(sim_cfg.nodi_transit_response_model)
    transit_time = np.asarray(transit_time_s, dtype=float)
    lockin_bandwidth_Hz = (
        1.0 / (2.0 * np.pi * float(sim_cfg.lockin_time_constant_s))
        if sim_cfg.lockin_time_constant_s > 0
        else 0.0
    )
    bandwidth = np.zeros_like(transit_time, dtype=float)
    gain = np.ones_like(transit_time, dtype=float)
    if model != "flat" and lockin_bandwidth_Hz > 0:
        valid = transit_time > 0
        bandwidth = np.where(valid, 1.0 / np.maximum(transit_time, 1e-30), 0.0)
        raw_gain = 1.0 / np.sqrt(1.0 + (bandwidth / lockin_bandwidth_Hz) ** 2)
        gain = np.where(valid, raw_gain, 1.0)
        gain = np.clip(
            gain,
            float(sim_cfg.nodi_transit_response_min_gain),
            float(sim_cfg.nodi_transit_response_max_gain),
        )
    return {
        "nodi_transit_response_model": model,
        "nodi_transit_bandwidth_Hz": bandwidth,
        "nodi_transit_bandwidth_gain": gain,
        "nodi_bandwidth_limited_fraction": np.maximum(0.0, 1.0 - gain),
        "nodi_lockin_bandwidth_Hz": float(lockin_bandwidth_Hz),
    }


def _broadcast_event_gain(gain: np.ndarray | float, source: np.ndarray) -> np.ndarray | float:
    """Broadcast one gain per event across the time axis for block readout."""
    gain_arr = np.asarray(gain, dtype=float)
    source_arr = np.asarray(source, dtype=float)
    if gain_arr.ndim == 0:
        return float(gain_arr)
    if source_arr.ndim > gain_arr.ndim:
        return gain_arr[..., np.newaxis]
    return gain_arr


def apply_readout_chain(
    signal_raw_noisy: np.ndarray,
    time_s: np.ndarray,
    sim_cfg: SimulationConfig,
    *,
    transit_time_s: float | None = None,
    readout_context: _ReadoutContext | None = None,
    export_full_diagnostics: bool = True,
) -> dict:
    """
    Apply a minimal detector/readout surrogate after raw interferometric noise.

    raw:
        detection trace is the raw noisy signal itself

    lockin_surrogate:
        pod_source  = lowpass(raw)
        nodi_source = lowpass(raw - pod_source)
        pod_true  = demod(pod_source,  f_pod  -> f_pod)
        nodi_true = demod(nodi_source, f_nodi -> f_nodi)
        observed_pod  = pod_true  + eps_np * demod(nodi_source, f_nodi -> f_pod)
        observed_nodi = nodi_true + eps_pn * demod(pod_source,  f_pod  -> f_nodi)

    The NODI-like observed channel is used for downstream thresholding and
    pulse detection, while the POD-like channel is retained for diagnostics.
    """
    raw = np.asarray(signal_raw_noisy, dtype=float)

    if sim_cfg.readout_model == "raw":
        zeros = np.zeros_like(raw)
        raw_mag = np.abs(raw)
        return {
            "signal_detect": raw.copy() if sim_cfg.readout_observable_mode == "in_phase" else raw_mag,
            "signal_nodi": raw.copy() if sim_cfg.readout_observable_mode == "in_phase" else raw_mag,
            "signal_pod": zeros,
            "signal_nodi_true": raw.copy() if sim_cfg.readout_observable_mode == "in_phase" else raw_mag,
            "signal_pod_true": zeros,
            "nodi_transit_response_model": sim_cfg.nodi_transit_response_model,
            "nodi_transit_bandwidth_Hz": 0.0,
            "nodi_transit_bandwidth_gain": 1.0,
            "nodi_bandwidth_limited_fraction": 0.0,
            "nodi_lockin_bandwidth_Hz": 0.0,
            "signal_nodi_i": raw.copy(),
            "signal_nodi_q": zeros,
            "signal_nodi_mag": raw_mag,
            "signal_pod_i": zeros,
            "signal_pod_q": zeros,
            "signal_pod_mag": zeros,
            "readout_numerical_route": "raw_detector_trace",
        }

    if sim_cfg.readout_model != "lockin_surrogate":
        raise ValueError(f"Unknown readout_model: {sim_cfg.readout_model}")

    context = readout_context
    if context is None:
        context = _build_readout_context(time_s, sim_cfg)
    if context is None:
        raise ValueError("readout_context is unavailable for lockin_surrogate")

    if _uses_bandpass_envelope_numerical_route(sim_cfg):
        return _apply_bandpass_envelope_readout(
            raw,
            sim_cfg,
            context,
            transit_time_s,
        )

    light_in_phase_only = (
        not export_full_diagnostics
        and sim_cfg.readout_observable_mode == "in_phase"
    )

    if light_in_phase_only:
        if _numba_njit is not None and raw.ndim == 2 and context.alpha > 0:
            (
                pod_true_i,
                nodi_true_i,
                pod_leak_i,
                nodi_leak_i,
            ) = _lockin_light_in_phase_readout_2d_kernel(
                np.ascontiguousarray(raw, dtype=np.float64),
                float(context.alpha),
                np.ascontiguousarray(context.pod_carrier_cos, dtype=np.float64),
                np.ascontiguousarray(context.pod_demod_cos, dtype=np.float64),
                np.ascontiguousarray(context.nodi_carrier_cos, dtype=np.float64),
                np.ascontiguousarray(context.nodi_demod_cos, dtype=np.float64),
            )
        else:
            pod_source = _first_order_lowpass_alpha(raw, context.alpha)
            nodi_source = _first_order_lowpass_alpha(raw - pod_source, context.alpha)
            pod_true_i = _lockin_demod_in_phase_precomputed(
                pod_source,
                context.alpha,
                context.pod_carrier_cos,
                context.pod_demod_cos,
            )
            nodi_true_i = _lockin_demod_in_phase_precomputed(
                nodi_source,
                context.alpha,
                context.nodi_carrier_cos,
                context.nodi_demod_cos,
            )
            pod_leak_i = _lockin_demod_in_phase_precomputed(
                nodi_source,
                context.alpha,
                context.nodi_carrier_cos,
                context.pod_demod_cos,
            )
            nodi_leak_i = _lockin_demod_in_phase_precomputed(
                pod_source,
                context.alpha,
                context.pod_carrier_cos,
                context.nodi_demod_cos,
            )
        pod_frequency_gain = _pod_frequency_response_gain(sim_cfg)
        pod_true_i = pod_true_i * float(pod_frequency_gain)
        pod_leak_i = pod_leak_i * float(pod_frequency_gain)
        transit_arr = (
            np.asarray(transit_time_s, dtype=float)
            if transit_time_s is not None
            else np.asarray(0.0)
        )
        nodi_transit_diag = (
            _nodi_transit_response_array(sim_cfg, transit_arr)
            if transit_time_s is not None and transit_arr.ndim > 0
            else _nodi_transit_response_diagnostics(sim_cfg, transit_time_s)
        )
        nodi_transit_gain = _broadcast_event_gain(
            nodi_transit_diag["nodi_transit_bandwidth_gain"],
            nodi_true_i,
        )
        nodi_true_i = nodi_true_i * nodi_transit_gain
        nodi_leak_i = nodi_leak_i * nodi_transit_gain

        signal_pod = pod_true_i + sim_cfg.nodi_to_pod_crosstalk * pod_leak_i
        signal_nodi = nodi_true_i + sim_cfg.pod_to_nodi_crosstalk * nodi_leak_i

        return {
            "signal_detect": signal_nodi,
            "signal_nodi": signal_nodi,
            "signal_pod": signal_pod,
            "signal_nodi_true": nodi_true_i,
            "signal_pod_true": pod_true_i,
            "pod_frequency_response_model": sim_cfg.pod_frequency_response_model,
            "pod_frequency_response_gain": float(pod_frequency_gain),
            "nodi_transit_response_model": str(
                nodi_transit_diag["nodi_transit_response_model"]
            ),
            "nodi_transit_bandwidth_Hz": nodi_transit_diag[
                "nodi_transit_bandwidth_Hz"
            ],
            "nodi_transit_bandwidth_gain": nodi_transit_diag[
                "nodi_transit_bandwidth_gain"
            ],
            "nodi_bandwidth_limited_fraction": nodi_transit_diag[
                "nodi_bandwidth_limited_fraction"
            ],
            "nodi_lockin_bandwidth_Hz": float(
                nodi_transit_diag["nodi_lockin_bandwidth_Hz"]
            ),
            "readout_numerical_route": "sampled_carrier_lockin_demod_surrogate",
        }

    pod_source = _first_order_lowpass_alpha(raw, context.alpha)
    nodi_source = _first_order_lowpass_alpha(raw - pod_source, context.alpha)

    pod_true_i, pod_true_q, pod_true_mag = _lockin_demod_components_precomputed(
        pod_source,
        context.alpha,
        context.pod_carrier_cos,
        context.pod_demod_cos,
        context.pod_demod_sin,
    )
    nodi_true_i, nodi_true_q, nodi_true_mag = _lockin_demod_components_precomputed(
        nodi_source,
        context.alpha,
        context.nodi_carrier_cos,
        context.nodi_demod_cos,
        context.nodi_demod_sin,
    )
    pod_leak_i, pod_leak_q, pod_leak_mag = _lockin_demod_components_precomputed(
        nodi_source,
        context.alpha,
        context.nodi_carrier_cos,
        context.pod_demod_cos,
        context.pod_demod_sin,
    )
    nodi_leak_i, nodi_leak_q, nodi_leak_mag = _lockin_demod_components_precomputed(
        pod_source,
        context.alpha,
        context.pod_carrier_cos,
        context.nodi_demod_cos,
        context.nodi_demod_sin,
    )
    pod_frequency_gain = _pod_frequency_response_gain(sim_cfg)
    pod_true_i = pod_true_i * float(pod_frequency_gain)
    pod_true_q = pod_true_q * float(pod_frequency_gain)
    pod_true_mag = pod_true_mag * float(pod_frequency_gain)
    pod_leak_i = pod_leak_i * float(pod_frequency_gain)
    pod_leak_q = pod_leak_q * float(pod_frequency_gain)
    pod_leak_mag = pod_leak_mag * float(pod_frequency_gain)
    transit_arr = (
        np.asarray(transit_time_s, dtype=float)
        if transit_time_s is not None
        else np.asarray(0.0)
    )
    nodi_transit_diag = (
        _nodi_transit_response_array(sim_cfg, transit_arr)
        if transit_time_s is not None and transit_arr.ndim > 0
        else _nodi_transit_response_diagnostics(sim_cfg, transit_time_s)
    )
    nodi_transit_gain = _broadcast_event_gain(
        nodi_transit_diag["nodi_transit_bandwidth_gain"],
        nodi_true_i,
    )
    nodi_true_i = nodi_true_i * nodi_transit_gain
    nodi_true_q = nodi_true_q * nodi_transit_gain
    nodi_true_mag = nodi_true_mag * nodi_transit_gain
    nodi_leak_i = nodi_leak_i * nodi_transit_gain
    nodi_leak_q = nodi_leak_q * nodi_transit_gain
    nodi_leak_mag = nodi_leak_mag * nodi_transit_gain

    signal_pod_i = pod_true_i + sim_cfg.nodi_to_pod_crosstalk * pod_leak_i
    signal_pod_q = pod_true_q + sim_cfg.nodi_to_pod_crosstalk * pod_leak_q
    signal_nodi_i = nodi_true_i + sim_cfg.pod_to_nodi_crosstalk * nodi_leak_i
    signal_nodi_q = nodi_true_q + sim_cfg.pod_to_nodi_crosstalk * nodi_leak_q
    signal_pod_mag = np.sqrt(np.maximum(signal_pod_i * signal_pod_i + signal_pod_q * signal_pod_q, 0.0))
    signal_nodi_mag = np.sqrt(np.maximum(signal_nodi_i * signal_nodi_i + signal_nodi_q * signal_nodi_q, 0.0))
    signal_pod = _select_lockin_observable_components(
        signal_pod_i,
        signal_pod_mag,
        sim_cfg.readout_observable_mode,
    )
    signal_nodi = _select_lockin_observable_components(
        signal_nodi_i,
        signal_nodi_mag,
        sim_cfg.readout_observable_mode,
    )

    return {
        "signal_detect": signal_nodi,
        "signal_nodi": signal_nodi,
        "signal_pod": signal_pod,
        "signal_nodi_true": _select_lockin_observable_components(
            nodi_true_i,
            nodi_true_mag,
            sim_cfg.readout_observable_mode,
        ),
        "signal_pod_true": _select_lockin_observable_components(
            pod_true_i,
            pod_true_mag,
            sim_cfg.readout_observable_mode,
        ),
        "signal_nodi_leak": _select_lockin_observable_components(
            nodi_leak_i,
            nodi_leak_mag,
            sim_cfg.readout_observable_mode,
        ),
        "signal_pod_leak": _select_lockin_observable_components(
            pod_leak_i,
            pod_leak_mag,
            sim_cfg.readout_observable_mode,
        ),
        "pod_frequency_response_model": sim_cfg.pod_frequency_response_model,
        "pod_frequency_response_gain": float(pod_frequency_gain),
        "nodi_transit_response_model": str(nodi_transit_diag["nodi_transit_response_model"]),
        "nodi_transit_bandwidth_Hz": nodi_transit_diag["nodi_transit_bandwidth_Hz"],
        "nodi_transit_bandwidth_gain": nodi_transit_diag["nodi_transit_bandwidth_gain"],
        "nodi_bandwidth_limited_fraction": nodi_transit_diag[
            "nodi_bandwidth_limited_fraction"
        ],
        "nodi_lockin_bandwidth_Hz": float(nodi_transit_diag["nodi_lockin_bandwidth_Hz"]),
        "signal_nodi_i": signal_nodi_i,
        "signal_nodi_q": signal_nodi_q,
        "signal_nodi_mag": signal_nodi_mag,
        "signal_pod_i": signal_pod_i,
        "signal_pod_q": signal_pod_q,
        "signal_pod_mag": signal_pod_mag,
        "signal_nodi_true_i": nodi_true_i,
        "signal_nodi_true_q": nodi_true_q,
        "signal_nodi_true_mag": nodi_true_mag,
        "signal_pod_true_i": pod_true_i,
        "signal_pod_true_q": pod_true_q,
        "signal_pod_true_mag": pod_true_mag,
        "readout_numerical_route": "sampled_carrier_lockin_demod_surrogate",
    }


def _build_observation_signature(
    operator_signature: str | None,
    reference: dict,
    sim_cfg: SimulationConfig,
    particle_radius_m: float | None = None,
) -> str:
    """
    Build an auditable signature for the full observable chain.

    `operator_signature` tracks only the angular collection operator. This
    higher-level signature additionally records the reference-field and
    phase/readout assumptions that materially affect the observed signal.
    """
    return (
        f"{operator_signature or 'operator=unknown'}"
        f"|reference_route={reference.get('reference_route', 'unknown')}"
        f"|reference_solver_route={reference.get('reference_solver_route', sim_cfg.reference_solver_route)}"
        f"|reference_na_edge_policy={reference.get('reference_na_edge_policy', sim_cfg.reference_na_edge_policy)}"
        f"|reference_na_edge_status={reference.get('reference_na_edge_status', 'unknown')}"
        f"|reference_operating_band={reference.get('reference_operating_band', 'unknown')}"
        f"|phase_filter_validity={reference.get('phase_filter_validity', 'not_applicable')}"
        f"|subwavelength_groove_validity_status={reference.get('subwavelength_groove_validity_status', 'not_applicable')}"
        f"|detector_forward_model={reference.get('detector_forward_model', sim_cfg.detector_forward_model)}"
        f"|field_coordinate_measure={reference.get('field_coordinate_measure', sim_cfg.field_coordinate_measure)}"
        f"|bfp_to_angle_jacobian_applied={bool(reference.get('bfp_to_angle_jacobian_applied', sim_cfg.bfp_to_angle_jacobian_applied))}"
        f"|complex_time_harmonic_convention={reference.get('complex_time_harmonic_convention', sim_cfg.complex_time_harmonic_convention)}"
        f"|fourier_transform_sign_convention={reference.get('fourier_transform_sign_convention', sim_cfg.fourier_transform_sign_convention)}"
        f"|mie_amplitude_phase_convention={reference.get('mie_amplitude_phase_convention', sim_cfg.mie_amplitude_phase_convention)}"
        f"|interference_conjugation_convention={reference.get('interference_conjugation_convention', sim_cfg.interference_conjugation_convention)}"
        f"|global_phase_offset_source={reference.get('global_phase_offset_source', sim_cfg.global_phase_offset_source)}"
        f"|polarization_basis_model={reference.get('polarization_basis_model', sim_cfg.polarization_basis_model)}"
        f"|jones_basis_status={reference.get('jones_basis_status', sim_cfg.jones_basis_status)}"
        f"|vector_optics_mode={reference.get('vector_optics_mode', sim_cfg.vector_optics_mode)}"
        f"|polarization_jones_operator_mode={reference.get('polarization_jones_operator_mode', sim_cfg.polarization_jones_operator_mode)}"
        f"|polarization_overlap_efficiency={reference.get('polarization_overlap_efficiency', 'unknown')}"
        f"|phase_polarization_quantitative_claim_allowed={reference.get('phase_polarization_quantitative_claim_allowed', False)}"
        f"|incident_field_model_for_mie={reference.get('incident_field_model_for_mie', 'unknown')}"
        f"|local_plane_wave_validity={reference.get('local_plane_wave_validity', 'unknown')}"
        f"|mie_radius_to_beam_waist_ratio={reference.get('mie_radius_to_beam_waist_ratio')}"
        f"|scattering_normalization_route={reference.get('scattering_normalization_route', sim_cfg.scattering_normalization_route)}"
        f"|K_sca_calibration_status={reference.get('K_sca_calibration_status', sim_cfg.K_sca_calibration_status)}"
        f"|standard_particle_calibration_coverage_status={reference.get('standard_particle_calibration_coverage_status', 'unknown')}"
        f"|standard_particle_calibration_data_role={reference.get('standard_particle_calibration_data_role', 'unknown')}"
        f"|detector_unit_chain_status={reference.get('detector_unit_chain_status', 'unknown')}"
        f"|global_phase_offset_calibration_status={reference.get('global_phase_offset_calibration_status', 'unknown')}"
        f"|mie_to_power_chain_status={reference.get('mie_to_power_chain_status', 'unknown')}"
        f"|detector_field_units={reference.get('detector_field_units', 'unknown')}"
        f"|K_sca_uncertainty_status={reference.get('K_sca_uncertainty_status', 'unknown')}"
        f"|standard_particle_uncertainty_budget_status={reference.get('standard_particle_uncertainty_budget_status', 'unknown')}"
        f"|calibration_design_rank={reference.get('calibration_design_rank', 'unknown')}"
        f"|calibration_held_out_validation_status={reference.get('calibration_held_out_validation_status', 'unknown')}"
        f"|calibration_state_machine_version={reference.get('calibration_state_machine_version', sim_cfg.calibration_state_machine_version)}"
        f"|bayesian_calibration_status={reference.get('bayesian_calibration_status', 'unknown')}"
        f"|next_experiment_priority={reference.get('next_experiment_priority', 'unknown')}"
        f"|output_claim_level={reference.get('output_claim_level', reference.get('reference_claim_level', 'unknown'))}"
        f"|noise_model_route={reference.get('noise_model_route', sim_cfg.detector_noise_model_route)}"
        f"|noise_terms_schema_version={reference.get('noise_terms_schema_version', 'unknown')}"
        f"|photon_unit_noise_model={reference.get('photon_unit_noise_model', sim_cfg.photon_unit_noise_model)}"
        f"|absolute_throughput_route={reference.get('absolute_throughput_route', sim_cfg.absolute_throughput_route)}"
        f"|detector_dynamic_range_model={reference.get('detector_dynamic_range_model', sim_cfg.detector_dynamic_range_model)}"
        f"|adc_dynamic_range_model={reference.get('adc_dynamic_range_model', sim_cfg.adc_dynamic_range_model)}"
        f"|background_field_model={reference.get('background_field_model', sim_cfg.background_field_model)}"
        f"|transmitted_leakage_model={reference.get('transmitted_leakage_model', sim_cfg.transmitted_leakage_model)}"
        f"|stray_light_model={reference.get('stray_light_model', sim_cfg.stray_light_model)}"
        f"|particle_induced_channel_perturbation_model={reference.get('particle_induced_channel_perturbation_model', sim_cfg.particle_induced_channel_perturbation_model)}"
        f"|particle_channel_perturbation_application_mode={reference.get('particle_channel_perturbation_application_mode', sim_cfg.particle_channel_perturbation_application_mode)}"
        f"|double_counting_risk_band={reference.get('double_counting_risk_band', 'unknown')}"
        f"|no_double_count_guard_passed={reference.get('no_double_count_guard_passed', 'unknown')}"
        f"|superposition_validity_status={reference.get('superposition_validity_status', 'unknown')}"
        f"|channel_particle_coupling_model={reference.get('channel_particle_coupling_model', 'unknown')}"
        f"|readout_preset={reference.get('readout_preset', sim_cfg.readout_preset)}"
        f"|readout_preset_status={reference.get('readout_preset_status', 'unknown')}"
        f"|electronics_demod_phase_policy={reference.get('electronics_demod_phase_policy', sim_cfg.electronics_demod_phase_policy)}"
        f"|effective_electronics_demod_phase_policy={reference.get('effective_electronics_demod_phase_policy', 'unknown')}"
        f"|polarity_source={reference.get('polarity_source', 'unknown')}"
        f"|readout_internal_demod_route={reference.get('readout_internal_demod_route', sim_cfg.readout_internal_demod_route)}"
        f"|readout_anti_alias_policy={reference.get('readout_anti_alias_policy', sim_cfg.readout_anti_alias_policy)}"
        f"|readout_sampling_validity={reference.get('readout_sampling_validity', 'unknown')}"
        f"|lockin_output_unit_convention={reference.get('lockin_output_unit_convention', sim_cfg.lockin_output_unit_convention)}"
        f"|lockin_reported_channel={reference.get('lockin_reported_channel', 'unknown')}"
        f"|threshold_tail={reference.get('threshold_tail', sim_cfg.threshold_tail)}"
        f"|threshold_calibration_source={reference.get('threshold_calibration_source', sim_cfg.threshold_calibration_source)}"
        f"|threshold_calibration_status={reference.get('threshold_calibration_status', 'unknown')}"
        f"|blank_false_positive_calibration_status={reference.get('blank_false_positive_calibration_status', 'unknown')}"
        f"|blank_false_positive_calibration_data_role={reference.get('blank_false_positive_calibration_data_role', 'unknown')}"
        f"|raw_blank_trace_bootstrap_status={reference.get('raw_blank_trace_bootstrap_status', 'unknown')}"
        f"|threshold_lane_specific_model={reference.get('threshold_lane_specific_model', 'unknown')}"
        f"|colored_noise_false_alarm_model={reference.get('colored_noise_false_alarm_model', sim_cfg.colored_noise_false_alarm_model)}"
        f"|particle_family={reference.get('particle_family', 'unknown')}"
        f"|particle_optical_model={reference.get('particle_optical_model', 'unknown')}"
        f"|particle_material_model_mode={reference.get('particle_material_model_mode', 'unknown')}"
        f"|particle_material_uncertainty_status={reference.get('particle_material_uncertainty_status', 'unknown')}"
        f"|EV_ensemble_mode={reference.get('EV_ensemble_mode', sim_cfg.EV_ensemble_mode)}"
        f"|EV_ensemble_name={reference.get('EV_ensemble_name', 'none')}"
        f"|uncertainty_propagation_mode={reference.get('uncertainty_propagation_mode', sim_cfg.particle_uncertainty_propagation_mode)}"
        f"|uncertainty_propagation_status={reference.get('uncertainty_propagation_status', 'unknown')}"
        f"|particle_uncertainty_budget_status={reference.get('particle_uncertainty_budget_status', 'unknown')}"
        f"|per_event_detectability_boundary={reference.get('per_event_detectability_boundary', 'unknown')}"
        f"|EV_sample_preparation_profile={reference.get('EV_sample_preparation_profile', sim_cfg.EV_sample_preparation_profile)}"
        f"|EV_specificity_risk={reference.get('EV_specificity_risk', 'unknown')}"
        f"|count_prediction_model={sim_cfg.count_prediction_model}"
        f"|poisson_arrival_process_status={reference.get('poisson_arrival_process_status', 'unknown')}"
        f"|crossing_conditioned_transport_status={reference.get('crossing_conditioned_transport_status', 'unknown')}"
        f"|count_likelihood_status={reference.get('count_likelihood_status', 'unknown')}"
        f"|population_inference_status={reference.get('population_inference_status', 'unknown')}"
        f"|unknown_particle_flag={reference.get('unknown_particle_flag', 'unknown')}"
        f"|classifier_rejection_rate={reference.get('classifier_rejection_rate', 'unknown')}"
        f"|number_concentration_m3={sim_cfg.number_concentration_m3}"
        f"|flow_control_mode={reference.get('flow_control_mode', sim_cfg.flow_control_mode)}"
        f"|fluidic_practicality_penalty={reference.get('fluidic_practicality_penalty', 'unknown')}"
        f"|fluidic_clogging_risk_band={reference.get('fluidic_clogging_risk_band', 'unknown')}"
        f"|wall_interaction_model={sim_cfg.wall_interaction_model}"
        f"|interface_correction_mode={reference.get('interface_correction_mode', sim_cfg.interface_correction_mode)}"
        f"|interface_correction_status={reference.get('interface_correction_status', 'unknown')}"
        f"|interface_api_boundary_status={reference.get('interface_api_boundary_status', 'unknown')}"
        f"|interface_output_sensitivity_status={reference.get('interface_output_sensitivity_status', 'unknown')}"
        f"|interface_fullwave_required={reference.get('interface_fullwave_required', 'unknown')}"
        f"|interface_fullwave_reason={reference.get('interface_fullwave_reason', 'unknown')}"
        f"|thermal_pod_model={reference.get('thermal_pod_model', sim_cfg.thermal_pod_model)}"
        f"|thermal_pod_model_status={reference.get('thermal_pod_model_status', 'unknown')}"
        f"|pod_quantitative_route_status={reference.get('pod_quantitative_route_status', 'unknown')}"
        f"|thermal_pod_api_boundary_status={reference.get('thermal_pod_api_boundary_status', 'unknown')}"
        f"|pod_wavelength_grouping_status={reference.get('pod_wavelength_grouping_status', 'unknown')}"
        f"|pod_probe_reference_field_status={reference.get('pod_probe_reference_field_status', 'unknown')}"
        f"|pod_heat_source_status={reference.get('pod_heat_source_status', 'unknown')}"
        f"|pod_detector_responsivity_status={reference.get('pod_detector_responsivity_status', 'unknown')}"
        f"|pod_roi_sensitivity_derivative_status={reference.get('pod_roi_sensitivity_derivative_status', sim_cfg.pod_roi_sensitivity_derivative_status)}"
        f"|pod_signal_sign_source={reference.get('pod_signal_sign_source', sim_cfg.pod_signal_sign_source)}"
        f"|probe_wavelength_m={reference.get('probe_wavelength_m', sim_cfg.probe_wavelength_m)}"
        f"|excitation_wavelength_m={reference.get('excitation_wavelength_m', sim_cfg.excitation_wavelength_m)}"
        f"|reference_model={sim_cfg.reference_model}"
        f"|reference_spatial_mode={sim_cfg.reference_spatial_mode}"
        f"|reference_phase_grating_mode={sim_cfg.reference_phase_grating_mode}"
        f"|reference_width_saturation_mode={sim_cfg.reference_width_saturation_mode}"
        f"|reference_width_saturation_cutoff_ratio={float(sim_cfg.reference_width_saturation_cutoff_ratio):.9e}"
        f"|interference_overlap_mode={sim_cfg.interference_overlap_mode}"
        f"|reference_spatial_amp={float(sim_cfg.reference_spatial_amplitude_strength):.9e}"
        f"|reference_spatial_phase={float(sim_cfg.reference_spatial_phase_strength_rad):.9e}"
        f"|phi_ref={float(reference.get('phi_ref_rad', 0.0)):.9e}"
        f"|g_ref={float(reference.get('g_ref', 1.0)):.9e}"
        f"|reference_claim_level={reference.get('reference_claim_level', 'unknown')}"
        f"|reference_calibration_amplitude_status={reference.get('reference_calibration_amplitude_status', 'unknown')}"
        f"|phase_model={sim_cfg.phase_model}"
        f"|path_opd_model={sim_cfg.path_opd_model}"
        f"|coupling_model={sim_cfg.coupling_model}"
        f"|illumination_mode={sim_cfg.illumination_mode}"
        f"|initial_position_distribution_mode={sim_cfg.initial_position_distribution_mode}"
        f"|initial_position_center_bias_strength={float(sim_cfg.initial_position_center_bias_strength):.9e}"
        f"|initial_position_center_bias_min_confinement_ratio={float(sim_cfg.initial_position_center_bias_min_confinement_ratio):.9e}"
        f"|random_sequence_policy={sim_cfg.random_sequence_policy}"
        f"|event_sampling_policy={sim_cfg.event_sampling_policy}"
        f"|adaptive_event_budget_mode={sim_cfg.adaptive_event_budget_mode}"
        f"|vectorized_event_engine={sim_cfg.vectorized_event_engine}"
        f"|event_block_size={int(sim_cfg.event_block_size)}"
        f"|event_block_rng_order={sim_cfg.event_block_rng_order}"
        f"|reference_interference_on={sim_cfg.reference_interference_on}"
        f"|nanoconfinement_on={sim_cfg.nanoconfinement_on}"
        f"|background_subtraction_on={sim_cfg.background_subtraction_on}"
        f"|flow_profile_model={sim_cfg.flow_profile_model}"
        f"|include_diffusion={sim_cfg.include_diffusion}"
        f"|diffusion_hindrance_model={sim_cfg.diffusion_hindrance_model}"
        f"|reflecting_boundary={sim_cfg.reflecting_boundary}"
        f"|pulse_detection={sim_cfg.pulse_detection_mode}"
        f"|detection_decision_mode={sim_cfg.detection_decision_mode}"
        f"|readout_model={sim_cfg.readout_model}"
        f"|readout_observable_mode={sim_cfg.readout_observable_mode}"
        f"|pod_f={float(sim_cfg.pod_lockin_frequency_Hz):.9e}"
        f"|nodi_f={float(sim_cfg.nodi_lockin_frequency_Hz):.9e}"
        f"|pod_phase={float(sim_cfg.pod_reference_phase_rad):.9e}"
        f"|nodi_phase={float(sim_cfg.nodi_reference_phase_rad):.9e}"
        f"|pod_freq_model={sim_cfg.pod_frequency_response_model}"
        f"|pod_freq_ref={float(sim_cfg.pod_frequency_response_reference_Hz):.9e}"
        f"|pod_freq_exp={float(sim_cfg.pod_frequency_response_exponent):.9e}"
        f"|nodi_transit_model={sim_cfg.nodi_transit_response_model}"
        f"|noise_model={sim_cfg.noise_model}"
        f"|shot_noise_scale={float(sim_cfg.shot_noise_scale):.9e}"
        f"|evaluation_false_alarm_rate={float(sim_cfg.evaluation_false_alarm_rate):.9e}"
        f"|pulse_pairing_tolerance_s={float(sim_cfg.pulse_pairing_tolerance_s):.9e}"
        f"|calibration_extrapolated={bool(reference.get('calibration_extrapolated', False))}"
        f"|channel_cross_section_model={sim_cfg.channel_cross_section_model}"
        f"|sidewall_taper_angle_deg={float(sim_cfg.sidewall_taper_angle_deg):.9e}"
        f"|particle_radius_m={particle_radius_m}"
        f"|cross_section_geometry_version={reference.get('cross_section_geometry_version', 'unknown')}"
        f"|center_accessible_support_model={reference.get('center_accessible_support_model', 'unknown')}"
        f"|trapezoid_closure_status={reference.get('trapezoid_closure_status', 'unknown')}"
        f"|trapezoid_closure_policy={reference.get('trapezoid_closure_policy', 'unknown')}"
        f"|trapezoid_runtime_guard_status={reference.get('trapezoid_runtime_guard_status', 'unknown')}"
        f"|trajectory_boundary_model={reference.get('trajectory_boundary_model', 'unknown')}"
        f"|wall_distance_model={reference.get('wall_distance_model', 'unknown')}"
        f"|flow_profile_geometry_model={reference.get('flow_profile_geometry_model', 'unknown')}"
        f"|geometry_propagation_status={reference.get('geometry_propagation_status', 'unknown')}"
        f"|geometry_not_propagated_reasons={reference.get('geometry_not_propagated_reasons', ())}"
    )

@dataclass
class _DetectionBasisAccumulator:
    """Incrementally accumulate one detection basis for batch summary."""

    feature_key: str
    stable_detection_margin_z_min: float
    detected_flag_key: str | None = None
    fallback_feature_key: str = "features"
    total_events: int = 0
    heights: list[float] = field(default_factory=list)
    signed_heights: list[float] = field(default_factory=list)
    positive_heights: list[float] = field(default_factory=list)
    negative_heights: list[float] = field(default_factory=list)
    widths: list[float] = field(default_factory=list)
    peak_to_threshold_ratios: list[float] = field(default_factory=list)
    peak_margin_z: list[float] = field(default_factory=list)
    n_negative: int = 0
    n_positive: int = 0
    n_stable: int = 0
    decision_detected_events: int = 0

    def update_from_features(
        self,
        features_local: dict,
        *,
        threshold_local: float,
        robust_std_local: float,
        detected_flag: bool,
    ) -> None:
        """Consume one feature payload plus its decision context."""
        self.total_events += 1
        if detected_flag:
            self.decision_detected_events += 1
        if features_local.get("n_peaks", 0) <= 0:
            return

        best_local = max(features_local["peaks"], key=lambda p: p["peak_height"])
        peak_height = float(best_local["peak_height"])
        peak_signed_height = float(
            best_local.get("peak_signed_height", best_local["peak_height"])
        )
        peak_width_s = float(best_local["peak_width_s"])
        threshold_safe_local = max(threshold_local, 1e-15)
        peak_ratio_local = peak_height / threshold_safe_local
        margin_z_local = float(max(peak_height - threshold_local, 0.0)) / robust_std_local
        margin_z_local = float(np.round(margin_z_local, 12))

        self.heights.append(peak_height)
        self.signed_heights.append(peak_signed_height)
        if peak_signed_height > 0:
            self.positive_heights.append(peak_height)
            self.n_positive += 1
        elif peak_signed_height < 0:
            self.negative_heights.append(peak_height)
            self.n_negative += 1
        self.widths.append(peak_width_s)
        self.peak_to_threshold_ratios.append(peak_ratio_local)
        self.peak_margin_z.append(margin_z_local)
        if margin_z_local >= self.stable_detection_margin_z_min:
            self.n_stable += 1

    def extend_from_peak_summary(
        self,
        peak_summary: dict[str, np.ndarray],
        *,
        thresholds: np.ndarray,
        robust_stds: np.ndarray,
    ) -> None:
        """Consume a block-level best-peak summary."""
        detected = np.asarray(peak_summary["detected"], dtype=bool)
        self.total_events += int(detected.size)
        if detected.size == 0:
            return
        self.decision_detected_events += int(np.count_nonzero(detected))
        if not bool(np.any(detected)):
            return

        heights = np.asarray(peak_summary["peak_heights"], dtype=float)[detected]
        signed_heights = np.asarray(
            peak_summary["peak_signed_heights"],
            dtype=float,
        )[detected]
        widths = np.asarray(peak_summary["peak_widths_s"], dtype=float)[detected]
        thresholds_arr = np.asarray(thresholds, dtype=float)[detected]
        robust_arr = np.maximum(np.asarray(robust_stds, dtype=float)[detected], 1e-15)
        threshold_safe = np.maximum(thresholds_arr, 1e-15)
        peak_ratios = heights / threshold_safe
        margins = np.round(np.maximum(heights - thresholds_arr, 0.0) / robust_arr, 12)

        self.heights.extend(float(value) for value in heights)
        self.signed_heights.extend(float(value) for value in signed_heights)
        positive_mask = signed_heights > 0
        negative_mask = signed_heights < 0
        self.positive_heights.extend(float(value) for value in heights[positive_mask])
        self.negative_heights.extend(float(value) for value in heights[negative_mask])
        self.n_positive += int(np.count_nonzero(positive_mask))
        self.n_negative += int(np.count_nonzero(negative_mask))
        self.widths.extend(float(value) for value in widths)
        self.peak_to_threshold_ratios.extend(float(value) for value in peak_ratios)
        self.peak_margin_z.extend(float(value) for value in margins)
        self.n_stable += int(
            np.count_nonzero(margins >= self.stable_detection_margin_z_min)
        )

    def update(self, event: dict) -> None:
        """Consume one event payload."""
        features_local = event.get(self.feature_key)
        if features_local is None:
            features_local = event.get(self.fallback_feature_key, {"n_peaks": 0, "peaks": []})

        if self.detected_flag_key is None:
            detected_flag = bool(features_local.get("n_peaks", 0) > 0)
        else:
            detected_flag = bool(
                event.get(self.detected_flag_key, features_local.get("n_peaks", 0) > 0)
            )
        self.update_from_features(
            features_local,
            threshold_local=float(event.get("threshold", 0.0)),
            robust_std_local=max(float(event.get("threshold_robust_std", 0.0)), 1e-15),
            detected_flag=detected_flag,
        )

    def finalize(self) -> dict[str, object]:
        """Build the basis summary payload."""
        n_total_local = self.total_events
        n_peaks_detected_local = len(self.heights)
        stable_detection_rate_local = (
            self.n_stable / n_total_local if n_total_local > 0 else 0.0
        )
        phase_flip_fraction_local = (
            self.n_negative / n_peaks_detected_local if n_peaks_detected_local > 0 else 0.0
        )
        return {
            "decision_n_detected": self.decision_detected_events,
            "n_detected": n_peaks_detected_local,
            "detection_rate": (
                self.decision_detected_events / n_total_local if n_total_local > 0 else 0.0
            ),
            "detection_rate_wilson_lb": wilson_lower_bound(
                self.decision_detected_events,
                n_total_local,
            ),
            "stable_detection_rate": stable_detection_rate_local,
            "stable_detection_rate_wilson_lb": wilson_lower_bound(
                self.n_stable,
                n_total_local,
            ),
            "phase_flip_fraction": phase_flip_fraction_local,
            "phase_flip_fraction_wilson_ub": wilson_upper_bound(
                self.n_negative,
                n_peaks_detected_local,
            ),
            "mean_peak_margin_z": (
                float(np.mean(self.peak_margin_z)) if self.peak_margin_z else 0.0
            ),
            "median_peak_margin_z": (
                float(np.median(self.peak_margin_z)) if self.peak_margin_z else 0.0
            ),
            "mean_peak_height": (
                float(np.mean(self.heights)) if self.heights else 0.0
            ),
            "mean_positive_peak_height": (
                float(np.mean(self.positive_heights)) if self.positive_heights else 0.0
            ),
            "mean_negative_peak_height": (
                float(np.mean(self.negative_heights)) if self.negative_heights else 0.0
            ),
            "mean_peak_width_s": (
                float(np.mean(self.widths)) if self.widths else 0.0
            ),
            "n_positive_peaks": self.n_positive,
            "n_negative_peaks": self.n_negative,
            "positive_peak_fraction": (
                self.n_positive / n_peaks_detected_local if n_peaks_detected_local > 0 else 0.0
            ),
            "negative_peak_fraction": phase_flip_fraction_local,
            "all_heights": list(self.heights),
            "all_signed_heights": list(self.signed_heights),
            "all_positive_heights": list(self.positive_heights),
            "all_negative_heights": list(self.negative_heights),
            "all_widths": list(self.widths),
            "all_peak_to_threshold_ratios": list(self.peak_to_threshold_ratios),
            "all_peak_margin_z": list(self.peak_margin_z),
        }


SELECTED_DETECTOR_MODE_EDGE_NORM_MIN = 0.5
SELECTED_DETECTOR_MODE_EDGE_NORM_MAX = 0.8
SELECTED_DETECTOR_MODE_CANDIDATE_MARGIN_Z_MIN = 0.0


def _conditional_rate_fields(
    *,
    prefix: str,
    detected_flags: list[bool],
    mask: np.ndarray,
) -> dict[str, object]:
    """Return conditional detection fields for an auditable denominator mask."""
    detected = np.asarray(detected_flags, dtype=bool)
    if detected.size == 0:
        n_total = 0
        n_subset = 0
        n_detected = 0
    else:
        mask_bool = np.asarray(mask, dtype=bool)
        if mask_bool.size != detected.size:
            raise ValueError(
                f"{prefix} mask length {mask_bool.size} does not match "
                f"detected length {detected.size}"
            )
        n_total = int(detected.size)
        n_subset = int(np.count_nonzero(mask_bool))
        n_detected = int(np.count_nonzero(detected & mask_bool))
    rate = n_detected / n_subset if n_subset > 0 else float("nan")
    rate_wilson_lb = (
        wilson_lower_bound(n_detected, n_subset)
        if n_subset > 0
        else float("nan")
    )
    return {
        f"{prefix}_n_events": n_subset,
        f"{prefix}_n_detected": n_detected,
        f"{prefix}_fraction": n_subset / n_total if n_total > 0 else 0.0,
        f"{prefix}_detection_rate": float(rate),
        f"{prefix}_detection_rate_wilson_lb": rate_wilson_lb,
    }


def _quantile_summary_fields(
    prefix: str,
    values: list[float],
    *,
    empty_value: float = 0.0,
) -> dict[str, float]:
    """Return compact distribution summaries without retaining event arrays."""
    if not values:
        return {
            f"{prefix}_p10": float(empty_value),
            f"{prefix}_p50": float(empty_value),
            f"{prefix}_p90": float(empty_value),
            f"{prefix}_p95": float(empty_value),
            f"{prefix}_p99": float(empty_value),
        }
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {
            f"{prefix}_p10": float(empty_value),
            f"{prefix}_p50": float(empty_value),
            f"{prefix}_p90": float(empty_value),
            f"{prefix}_p95": float(empty_value),
            f"{prefix}_p99": float(empty_value),
        }
    return {
        f"{prefix}_p10": float(np.quantile(arr, 0.10, method="linear")),
        f"{prefix}_p50": float(np.quantile(arr, 0.50, method="linear")),
        f"{prefix}_p90": float(np.quantile(arr, 0.90, method="linear")),
        f"{prefix}_p95": float(np.quantile(arr, 0.95, method="linear")),
        f"{prefix}_p99": float(np.quantile(arr, 0.99, method="linear")),
    }


@dataclass
class _BatchSummaryAccumulator:
    """Incrementally accumulate batch-summary metrics without storing all events."""

    stable_detection_margin_z_min: float = 1.0
    fixed_false_alarm_rate: float = 0.05
    selected_annulus_edge_norm_min: float = SELECTED_DETECTOR_MODE_EDGE_NORM_MIN
    selected_annulus_edge_norm_max: float = SELECTED_DETECTOR_MODE_EDGE_NORM_MAX
    first_event: dict | None = None
    baseline_levels: list[float] = field(default_factory=list)
    shot_noise_std_means: list[float] = field(default_factory=list)
    mean_reference_amplitudes: list[float] = field(default_factory=list)
    mean_scattering_amplitudes: list[float] = field(default_factory=list)
    reference_to_scattering_ratios: list[float] = field(default_factory=list)
    transit_times: list[float] = field(default_factory=list)
    local_snrs: list[float] = field(default_factory=list)
    initial_abs_x_norms: list[float] = field(default_factory=list)
    initial_abs_z_norms: list[float] = field(default_factory=list)
    initial_distribution_actives: list[float] = field(default_factory=list)
    initial_confinement_ratios: list[float] = field(default_factory=list)
    initial_confinement_activations: list[float] = field(default_factory=list)
    initial_center_bias_x_exponents: list[float] = field(default_factory=list)
    initial_center_bias_z_exponents: list[float] = field(default_factory=list)
    nodi_transit_bandwidths: list[float] = field(default_factory=list)
    nodi_transit_gains: list[float] = field(default_factory=list)
    nodi_bandwidth_limited_fractions: list[float] = field(default_factory=list)
    interference_overlap_factors: list[float] = field(default_factory=list)
    interference_overlap_phase_rads: list[float] = field(default_factory=list)
    rho_physical_nominals: list[float] = field(default_factory=list)
    event_max_margin_z: list[float] = field(default_factory=list)
    background_max_margin_z: list[float] = field(default_factory=list)
    threshold_values: list[float] = field(default_factory=list)
    threshold_robust_stds: list[float] = field(default_factory=list)
    pod_threshold_values: list[float] = field(default_factory=list)
    pod_threshold_robust_stds: list[float] = field(default_factory=list)
    threshold_background_segment_samples: list[int] = field(default_factory=list)
    final_detected_flags: list[bool] = field(default_factory=list)
    paired_detected_events: int = 0
    best_peak_paired_count: int = 0
    detected_single_channel_events: int = 0
    final_basis: _DetectionBasisAccumulator = field(init=False)
    single_basis: _DetectionBasisAccumulator = field(init=False)
    paired_basis: _DetectionBasisAccumulator = field(init=False)

    def __post_init__(self) -> None:
        self.final_basis = _DetectionBasisAccumulator(
            feature_key="features",
            stable_detection_margin_z_min=self.stable_detection_margin_z_min,
        )
        self.single_basis = _DetectionBasisAccumulator(
            feature_key="features_nodi",
            detected_flag_key="detected_single_channel",
            stable_detection_margin_z_min=self.stable_detection_margin_z_min,
        )
        self.paired_basis = _DetectionBasisAccumulator(
            feature_key="features_paired",
            detected_flag_key="detected_paired_channel",
            stable_detection_margin_z_min=self.stable_detection_margin_z_min,
        )

    def update(self, event: dict) -> None:
        """Consume one event payload."""
        if self.first_event is None:
            self.first_event = event

        self.final_basis.update(event)
        self.single_basis.update(event)
        self.paired_basis.update(event)

        self.baseline_levels.append(float(event.get("I_baseline", 0.0)))
        self.threshold_values.append(float(event.get("threshold", 0.0)))
        self.threshold_robust_stds.append(float(event.get("threshold_robust_std", 0.0)))
        self.pod_threshold_values.append(float(event.get("pod_threshold", 0.0)))
        self.pod_threshold_robust_stds.append(
            float(event.get("pod_threshold_robust_std", 0.0))
        )
        self.threshold_background_segment_samples.append(
            int(event.get("threshold_background_segment_samples", 0) or 0)
        )
        self.shot_noise_std_means.append(float(event.get("shot_noise_std_mean", 0.0)))
        self.mean_reference_amplitudes.append(float(event.get("mean_A_ref_local", 0.0)))
        self.mean_scattering_amplitudes.append(float(event.get("mean_A_sca_local", 0.0)))
        self.reference_to_scattering_ratios.append(
            float(event.get("mean_reference_to_scattering_amplitude_ratio", 0.0))
        )
        self.transit_times.append(float(event.get("transit_time_s", 0.0)))
        self.local_snrs.append(float(event.get("local_snr", 0.0)))
        self.initial_abs_x_norms.append(abs(float(event.get("initial_position_x_norm", 0.0))))
        self.initial_abs_z_norms.append(abs(float(event.get("initial_position_z_norm", 0.0))))
        self.initial_distribution_actives.append(
            1.0 if bool(event.get("initial_position_distribution_active", False)) else 0.0
        )
        self.initial_confinement_ratios.append(
            float(event.get("initial_position_confinement_ratio", 0.0))
        )
        self.initial_confinement_activations.append(
            float(event.get("initial_position_confinement_activation", 0.0))
        )
        self.initial_center_bias_x_exponents.append(
            float(event.get("initial_position_center_bias_x_exponent", 1.0))
        )
        self.initial_center_bias_z_exponents.append(
            float(event.get("initial_position_center_bias_z_exponent", 1.0))
        )
        self.nodi_transit_bandwidths.append(
            float(event.get("nodi_transit_bandwidth_Hz", 0.0) or 0.0)
        )
        self.nodi_transit_gains.append(
            float(event.get("nodi_transit_bandwidth_gain", 1.0) or 1.0)
        )
        self.nodi_bandwidth_limited_fractions.append(
            float(event.get("nodi_bandwidth_limited_fraction", 0.0) or 0.0)
        )
        self.interference_overlap_factors.append(
            float(event.get("interference_overlap_factor_abs", 1.0) or 1.0)
        )
        self.interference_overlap_phase_rads.append(
            float(event.get("interference_overlap_factor_phase_rad", 0.0) or 0.0)
        )

        rho_nominal = event.get("rho_physical_envelope_nominal")
        if rho_nominal is not None:
            self.rho_physical_nominals.append(float(rho_nominal))

        has_paired = bool(event.get("has_paired_pulse", False))

        detected_single_channel = bool(
            event.get(
                "detected_single_channel",
                event.get("features_nodi", event["features"]).get("n_peaks", 0) > 0,
            )
        )
        final_detected = bool(event.get("features", {}).get("n_peaks", 0) > 0)
        self.final_detected_flags.append(final_detected)
        if detected_single_channel:
            self.detected_single_channel_events += 1

        precomputed_event_margin_z = event.get("event_max_margin_z")
        precomputed_background_margin_z = event.get("background_max_margin_z")
        if (
            precomputed_event_margin_z is not None
            and precomputed_background_margin_z is not None
        ):
            self.event_max_margin_z.append(float(precomputed_event_margin_z))
            self.background_max_margin_z.append(float(precomputed_background_margin_z))
        else:
            signal_eval = np.asarray(event.get("signal_noisy", []), dtype=float)
            if event.get("pulse_detection_mode", "positive") == "absolute":
                signal_eval = np.abs(signal_eval)
            threshold = float(event.get("threshold", 0.0))
            robust_std = max(float(event.get("threshold_robust_std", 0.0)), 1e-15)
            if signal_eval.size > 0:
                n_bg = max(1, int(0.2 * len(signal_eval)))
                self.event_max_margin_z.append(
                    float((np.max(signal_eval) - threshold) / robust_std)
                )
                self.background_max_margin_z.append(
                    float((np.max(signal_eval[:n_bg]) - threshold) / robust_std)
                )
            else:
                fallback_margin_z = float(-threshold / robust_std)
                self.event_max_margin_z.append(fallback_margin_z)
                self.background_max_margin_z.append(fallback_margin_z)

        if (
            event.get("features", {}).get("n_peaks", 0) > 0
            and detected_single_channel
            and has_paired
        ):
            self.paired_detected_events += 1
        if (
            event.get("features", {}).get("n_peaks", 0) > 0
            and detected_single_channel
            and bool(event.get("best_peak_paired", False))
        ):
            self.best_peak_paired_count += 1

    def update_from_simulation(
        self,
        *,
        features: dict,
        features_nodi: dict,
        features_paired: dict,
        detected_single_channel: bool,
        detected_paired_channel: bool,
        threshold: float,
        threshold_robust_std: float,
        pod_threshold: float,
        pod_threshold_robust_std: float,
        threshold_background_segment_samples: int,
        trace: dict,
        noisy: dict,
        A_ref_trace: np.ndarray,
        A_sca_trace: np.ndarray,
        mean_reference_to_scattering_ratio: float,
        transit_time_s: float,
        local_snr: float,
        position_diag: dict,
        readout: dict,
        illumination: dict,
        reference: dict,
        paired_pulse_count: int,
        best_peak_paired: bool,
        sca_trace: dict,
        event_max_margin_z: float,
        background_max_margin_z: float,
        detection_decision_mode: str,
    ) -> None:
        """Consume one event directly from local simulation state."""
        if self.first_event is None:
            reference_projection_status = reference.get("reference_projection_coupling_status")
            self.first_event = {
                "illumination_projection_coupling_status": illumination.get(
                    "illumination_projection_coupling_status"
                ),
                "reference_projection_coupling_status": reference_projection_status,
                "interference_projection_coupling_status": reference_projection_status,
                "initial_position_distribution_mode": position_diag.get(
                    "initial_position_distribution_mode",
                    "uniform",
                ),
                "detection_decision_mode": detection_decision_mode,
                "rho_requested": reference.get("rho_requested"),
                "rho_physical_envelope_status": reference.get(
                    "rho_physical_envelope_status",
                    "unavailable",
                ),
                "path_opd_model": sca_trace.get("path_opd_model", "single_pass"),
                "path_opd_reference_plane": sca_trace.get(
                    "path_opd_reference_plane",
                    "unknown",
                ),
                "path_opd_z_geometry_factor": sca_trace.get(
                    "path_opd_z_geometry_factor",
                    1.0,
                ),
                "path_opd_z_reference_mode": sca_trace.get(
                    "path_opd_z_reference_mode",
                    "unknown",
                ),
                "path_opd_default_model": sca_trace.get(
                    "path_opd_default_model",
                    "single_pass",
                ),
                "path_opd_model_role": sca_trace.get("path_opd_model_role", "unknown"),
                "path_opd_default_frozen": sca_trace.get(
                    "path_opd_default_frozen",
                    True,
                ),
                "path_opd_freeze_status": sca_trace.get(
                    "path_opd_freeze_status",
                    "unknown",
                ),
            }

        robust_std = max(float(threshold_robust_std), 1e-15)
        self.final_basis.update_from_features(
            features,
            threshold_local=float(threshold),
            robust_std_local=robust_std,
            detected_flag=bool(features.get("n_peaks", 0) > 0),
        )
        self.single_basis.update_from_features(
            features_nodi,
            threshold_local=float(threshold),
            robust_std_local=robust_std,
            detected_flag=detected_single_channel,
        )
        self.paired_basis.update_from_features(
            features_paired,
            threshold_local=float(threshold),
            robust_std_local=robust_std,
            detected_flag=detected_paired_channel,
        )

        self.baseline_levels.append(float(trace.get("I_baseline", 0.0)))
        self.threshold_values.append(float(threshold))
        self.threshold_robust_stds.append(float(threshold_robust_std))
        self.pod_threshold_values.append(float(pod_threshold))
        self.pod_threshold_robust_stds.append(float(pod_threshold_robust_std))
        self.threshold_background_segment_samples.append(
            int(threshold_background_segment_samples)
        )
        self.shot_noise_std_means.append(float(noisy.get("shot_noise_std_mean", 0.0)))
        self.mean_reference_amplitudes.append(float(np.mean(A_ref_trace)))
        self.mean_scattering_amplitudes.append(float(np.mean(A_sca_trace)))
        self.reference_to_scattering_ratios.append(
            float(mean_reference_to_scattering_ratio)
        )
        self.transit_times.append(float(transit_time_s))
        self.local_snrs.append(float(local_snr))
        self.initial_abs_x_norms.append(
            abs(float(position_diag.get("initial_position_x_norm", 0.0)))
        )
        self.initial_abs_z_norms.append(
            abs(float(position_diag.get("initial_position_z_norm", 0.0)))
        )
        self.initial_distribution_actives.append(
            1.0 if bool(position_diag.get("initial_position_distribution_active", False)) else 0.0
        )
        self.initial_confinement_ratios.append(
            float(position_diag.get("initial_position_confinement_ratio", 0.0))
        )
        self.initial_confinement_activations.append(
            float(position_diag.get("initial_position_confinement_activation", 0.0))
        )
        self.initial_center_bias_x_exponents.append(
            float(position_diag.get("initial_position_center_bias_x_exponent", 1.0))
        )
        self.initial_center_bias_z_exponents.append(
            float(position_diag.get("initial_position_center_bias_z_exponent", 1.0))
        )
        self.nodi_transit_bandwidths.append(
            float(readout.get("nodi_transit_bandwidth_Hz", 0.0) or 0.0)
        )
        self.nodi_transit_gains.append(
            float(readout.get("nodi_transit_bandwidth_gain", 1.0) or 1.0)
        )
        self.nodi_bandwidth_limited_fractions.append(
            float(readout.get("nodi_bandwidth_limited_fraction", 0.0) or 0.0)
        )
        self.interference_overlap_factors.append(
            float(trace.get("interference_overlap_factor_abs", 1.0) or 1.0)
        )
        self.interference_overlap_phase_rads.append(
            float(trace.get("interference_overlap_factor_phase_rad", 0.0) or 0.0)
        )

        rho_nominal = reference.get("rho_physical_envelope_nominal")
        if rho_nominal is not None:
            self.rho_physical_nominals.append(float(rho_nominal))

        has_paired = paired_pulse_count > 0
        if detected_single_channel:
            self.detected_single_channel_events += 1
        self.event_max_margin_z.append(float(event_max_margin_z))
        self.background_max_margin_z.append(float(background_max_margin_z))
        if features.get("n_peaks", 0) > 0 and detected_single_channel and has_paired:
            self.paired_detected_events += 1
        if features.get("n_peaks", 0) > 0 and detected_single_channel and best_peak_paired:
            self.best_peak_paired_count += 1
        self.final_detected_flags.append(bool(features.get("n_peaks", 0) > 0))

    def update_from_simulation_block(
        self,
        *,
        final_peak_summary: dict[str, np.ndarray],
        single_peak_summary: dict[str, np.ndarray],
        paired_peak_summary: dict[str, np.ndarray],
        thresholds: np.ndarray,
        threshold_robust_stds: np.ndarray,
        pod_thresholds: np.ndarray,
        pod_threshold_robust_stds: np.ndarray,
        threshold_background_segment_samples: int,
        baseline_by_event: np.ndarray,
        shot_std_by_event: np.ndarray,
        A_ref_trace: np.ndarray,
        A_sca_trace: np.ndarray,
        mean_reference_to_scattering_ratios: np.ndarray,
        transit_times: np.ndarray,
        local_snrs: np.ndarray,
        position_diags: list[dict],
        nodi_transit_bandwidths: np.ndarray,
        nodi_transit_gains: np.ndarray,
        nodi_bandwidth_limited_fractions: np.ndarray,
        interference_overlap_factor_abs: float,
        interference_overlap_factor_phase_rad: float,
        illumination: dict,
        reference: dict,
        sca_trace: dict,
        event_max_margin_z: np.ndarray,
        background_max_margin_z: np.ndarray,
        detection_decision_mode: str,
    ) -> None:
        """Consume a block directly from vectorized local simulation state."""
        block_size = int(np.asarray(thresholds).size)
        if block_size <= 0:
            return
        first_position_diag = position_diags[0] if position_diags else {}
        if self.first_event is None:
            reference_projection_status = reference.get(
                "reference_projection_coupling_status"
            )
            self.first_event = {
                "illumination_projection_coupling_status": illumination.get(
                    "illumination_projection_coupling_status"
                ),
                "reference_projection_coupling_status": reference_projection_status,
                "interference_projection_coupling_status": reference_projection_status,
                "initial_position_distribution_mode": first_position_diag.get(
                    "initial_position_distribution_mode",
                    "uniform",
                ),
                "detection_decision_mode": detection_decision_mode,
                "rho_requested": reference.get("rho_requested"),
                "rho_physical_envelope_status": reference.get(
                    "rho_physical_envelope_status",
                    "unavailable",
                ),
                "path_opd_model": sca_trace.get("path_opd_model", "single_pass"),
                "path_opd_reference_plane": sca_trace.get(
                    "path_opd_reference_plane",
                    "unknown",
                ),
                "path_opd_z_geometry_factor": sca_trace.get(
                    "path_opd_z_geometry_factor",
                    1.0,
                ),
                "path_opd_z_reference_mode": sca_trace.get(
                    "path_opd_z_reference_mode",
                    "unknown",
                ),
                "path_opd_default_model": sca_trace.get(
                    "path_opd_default_model",
                    "single_pass",
                ),
                "path_opd_model_role": sca_trace.get("path_opd_model_role", "unknown"),
                "path_opd_default_frozen": sca_trace.get(
                    "path_opd_default_frozen",
                    True,
                ),
                "path_opd_freeze_status": sca_trace.get(
                    "path_opd_freeze_status",
                    "unknown",
                ),
            }

        self.final_basis.extend_from_peak_summary(
            final_peak_summary,
            thresholds=thresholds,
            robust_stds=threshold_robust_stds,
        )
        self.single_basis.extend_from_peak_summary(
            single_peak_summary,
            thresholds=thresholds,
            robust_stds=threshold_robust_stds,
        )
        self.paired_basis.extend_from_peak_summary(
            paired_peak_summary,
            thresholds=thresholds,
            robust_stds=threshold_robust_stds,
        )

        self.baseline_levels.extend(float(value) for value in baseline_by_event)
        self.threshold_values.extend(float(value) for value in thresholds)
        self.threshold_robust_stds.extend(float(value) for value in threshold_robust_stds)
        self.pod_threshold_values.extend(float(value) for value in pod_thresholds)
        self.pod_threshold_robust_stds.extend(
            float(value) for value in pod_threshold_robust_stds
        )
        self.threshold_background_segment_samples.extend(
            [int(threshold_background_segment_samples)] * block_size
        )
        self.shot_noise_std_means.extend(float(value) for value in shot_std_by_event)
        self.mean_reference_amplitudes.extend(
            float(value)
            for value in np.mean(np.asarray(A_ref_trace, dtype=float), axis=1)
        )
        self.mean_scattering_amplitudes.extend(
            float(value)
            for value in np.mean(np.asarray(A_sca_trace, dtype=float), axis=1)
        )
        self.reference_to_scattering_ratios.extend(
            float(value) for value in mean_reference_to_scattering_ratios
        )
        self.transit_times.extend(float(value) for value in transit_times)
        self.local_snrs.extend(float(value) for value in local_snrs)
        self.initial_abs_x_norms.extend(
            abs(float(diag.get("initial_position_x_norm", 0.0)))
            for diag in position_diags
        )
        self.initial_abs_z_norms.extend(
            abs(float(diag.get("initial_position_z_norm", 0.0)))
            for diag in position_diags
        )
        self.initial_distribution_actives.extend(
            1.0
            if bool(diag.get("initial_position_distribution_active", False))
            else 0.0
            for diag in position_diags
        )
        self.initial_confinement_ratios.extend(
            float(diag.get("initial_position_confinement_ratio", 0.0))
            for diag in position_diags
        )
        self.initial_confinement_activations.extend(
            float(diag.get("initial_position_confinement_activation", 0.0))
            for diag in position_diags
        )
        self.initial_center_bias_x_exponents.extend(
            float(diag.get("initial_position_center_bias_x_exponent", 1.0))
            for diag in position_diags
        )
        self.initial_center_bias_z_exponents.extend(
            float(diag.get("initial_position_center_bias_z_exponent", 1.0))
            for diag in position_diags
        )
        self.nodi_transit_bandwidths.extend(
            float(value) for value in nodi_transit_bandwidths
        )
        self.nodi_transit_gains.extend(float(value) for value in nodi_transit_gains)
        self.nodi_bandwidth_limited_fractions.extend(
            float(value) for value in nodi_bandwidth_limited_fractions
        )
        self.interference_overlap_factors.extend(
            [float(interference_overlap_factor_abs)] * block_size
        )
        self.interference_overlap_phase_rads.extend(
            [float(interference_overlap_factor_phase_rad)] * block_size
        )

        rho_nominal = reference.get("rho_physical_envelope_nominal")
        if rho_nominal is not None:
            self.rho_physical_nominals.extend([float(rho_nominal)] * block_size)

        single_detected = np.asarray(single_peak_summary["detected"], dtype=bool)
        final_detected = np.asarray(final_peak_summary["detected"], dtype=bool)
        paired_detected = np.asarray(paired_peak_summary["detected"], dtype=bool)
        paired_and_single = paired_detected & single_detected
        self.detected_single_channel_events += int(np.count_nonzero(single_detected))
        self.paired_detected_events += int(np.count_nonzero(paired_and_single))
        self.best_peak_paired_count += int(np.count_nonzero(paired_and_single))
        self.final_detected_flags.extend(bool(value) for value in final_detected)
        self.event_max_margin_z.extend(float(value) for value in event_max_margin_z)
        self.background_max_margin_z.extend(
            float(value) for value in background_max_margin_z
        )

    def _selected_detector_mode_fields(
        self,
        *,
        n_detected: int,
        n_total: int,
        detection_rate: float,
        detection_rate_wilson_lb: float,
    ) -> dict[str, object]:
        """Build raw and selected-detector-mode conditional rate diagnostics."""
        detected = np.asarray(self.final_detected_flags, dtype=bool)
        event_margin = np.asarray(self.event_max_margin_z, dtype=float)
        abs_x = np.asarray(self.initial_abs_x_norms, dtype=float)
        abs_z = np.asarray(self.initial_abs_z_norms, dtype=float)
        edge_norm = np.maximum(abs_x, abs_z)

        fields: dict[str, object] = {
            "all_crossing_n_events": int(n_total),
            "all_crossing_n_detected": int(n_detected),
            "all_crossing_detection_rate": float(detection_rate),
            "all_crossing_detection_rate_wilson_lb": float(
                detection_rate_wilson_lb
            ),
            "selected_detector_mode_candidate_source": (
                "event_max_margin_z_above_threshold_before_width_gate"
            ),
            "selected_detector_mode_candidate_margin_z_min": float(
                SELECTED_DETECTOR_MODE_CANDIDATE_MARGIN_Z_MIN
            ),
            "selected_detector_mode_annulus_source": (
                "initial_position_edge_norm_annulus_diagnostic_v1"
            ),
            "selected_detector_mode_annulus_edge_norm_min": float(
                self.selected_annulus_edge_norm_min
            ),
            "selected_detector_mode_annulus_edge_norm_max": float(
                self.selected_annulus_edge_norm_max
            ),
        }

        if (
            detected.size == event_margin.size == edge_norm.size
            and detected.size > 0
        ):
            candidate_mask = (
                event_margin >= SELECTED_DETECTOR_MODE_CANDIDATE_MARGIN_Z_MIN
            )
            annulus_mask = (
                (edge_norm >= self.selected_annulus_edge_norm_min)
                & (edge_norm <= self.selected_annulus_edge_norm_max)
            )
            fields.update(
                _conditional_rate_fields(
                    prefix="selected_detector_mode_candidate",
                    detected_flags=self.final_detected_flags,
                    mask=candidate_mask,
                )
            )
            fields.update(
                _conditional_rate_fields(
                    prefix="selected_detector_mode_annulus",
                    detected_flags=self.final_detected_flags,
                    mask=annulus_mask,
                )
            )
            selected_edges = edge_norm[annulus_mask]
            fields["selected_detector_mode_annulus_mean_edge_norm"] = (
                float(np.mean(selected_edges))
                if selected_edges.size > 0
                else float("nan")
            )
            return fields

        fields.update(
            {
                "selected_detector_mode_candidate_n_events": 0,
                "selected_detector_mode_candidate_n_detected": 0,
                "selected_detector_mode_candidate_fraction": 0.0,
                "selected_detector_mode_candidate_detection_rate": 0.0,
                "selected_detector_mode_candidate_detection_rate_wilson_lb": 0.0,
                "selected_detector_mode_annulus_n_events": 0,
                "selected_detector_mode_annulus_n_detected": 0,
                "selected_detector_mode_annulus_fraction": 0.0,
                "selected_detector_mode_annulus_detection_rate": float("nan"),
                "selected_detector_mode_annulus_detection_rate_wilson_lb": float("nan"),
                "selected_detector_mode_annulus_mean_edge_norm": float("nan"),
            }
        )
        return fields

    def finalize(self) -> dict:
        """Build the canonical batch summary payload."""
        final_basis = self.final_basis.finalize()
        single_basis = self.single_basis.finalize()
        paired_basis = self.paired_basis.finalize()
        heights = list(final_basis["all_heights"])
        signed_heights = list(final_basis["all_signed_heights"])
        widths = list(final_basis["all_widths"])
        peak_to_threshold_ratios = list(final_basis["all_peak_to_threshold_ratios"])
        peak_margin_z = list(final_basis["all_peak_margin_z"])

        n_detected = int(final_basis["n_detected"])
        n_total = self.final_basis.total_events
        detection_rate = n_detected / n_total if n_total > 0 else 0.0
        detection_rate_wilson_lb = wilson_lower_bound(n_detected, n_total)
        stable_detection_rate = float(final_basis["stable_detection_rate"])
        phase_flip_fraction = float(final_basis["phase_flip_fraction"])
        stable_detection_rate_wilson_lb = float(final_basis["stable_detection_rate_wilson_lb"])
        phase_flip_fraction_wilson_ub = float(final_basis["phase_flip_fraction_wilson_ub"])
        single_channel_detection_rate = float(single_basis["detection_rate"])
        paired_channel_detection_rate = float(paired_basis["detection_rate"])
        single_channel_detection_rate_wilson_lb = float(
            single_basis["detection_rate_wilson_lb"]
        )
        paired_channel_detection_rate_wilson_lb = float(
            paired_basis["detection_rate_wilson_lb"]
        )
        hit_rate_at_fixed_false_alarm = compute_hit_rate_at_fixed_false_alarm(
            self.event_max_margin_z,
            self.background_max_margin_z,
            self.fixed_false_alarm_rate,
        )
        roc_auc_event_vs_background = compute_empirical_roc_auc(
            self.event_max_margin_z,
            self.background_max_margin_z,
        )
        d_prime_event_vs_background = compute_d_prime(
            self.event_max_margin_z,
            self.background_max_margin_z,
        )
        mean_peak_height = float(np.mean(heights)) if heights else 0.0
        std_peak_height = (
            float(np.std(heights, ddof=1)) if len(heights) > 1 else 0.0
        )
        positive_heights = list(final_basis["all_positive_heights"])
        negative_heights = list(final_basis["all_negative_heights"])
        if heights:
            median_height = float(np.median(heights))
            mad_height = float(np.median(np.abs(np.asarray(heights) - median_height)))
            robust_std_height = 1.4826 * mad_height
            robust_cv_peak_height = (
                robust_std_height / median_height if median_height > 0 else float("inf")
            )
        else:
            median_height = 0.0
            mad_height = 0.0
            robust_std_height = 0.0
            robust_cv_peak_height = float("inf")

        first_event = self.first_event
        first_event_defaults = first_event or {}
        out = {
            "n_events": n_total,
            "n_detected": n_detected,
            "detection_rate": detection_rate,
            "detection_rate_wilson_lb": detection_rate_wilson_lb,
            "stable_detection_rate": stable_detection_rate,
            "stable_detection_rate_wilson_lb": stable_detection_rate_wilson_lb,
            "mean_peak_height": mean_peak_height,
            "std_peak_height": std_peak_height,
            "mean_positive_peak_height": (
                float(np.mean(positive_heights)) if positive_heights else 0.0
            ),
            "mean_negative_peak_height": (
                float(np.mean(negative_heights)) if negative_heights else 0.0
            ),
            "mean_peak_width_s": float(np.mean(widths)) if widths else 0.0,
            "positive_peak_fraction": float(final_basis["positive_peak_fraction"]),
            "negative_peak_fraction": float(final_basis["negative_peak_fraction"]),
            "phase_flip_fraction": phase_flip_fraction,
            "phase_flip_fraction_wilson_ub": phase_flip_fraction_wilson_ub,
            "hit_rate_at_fixed_false_alarm": hit_rate_at_fixed_false_alarm,
            "roc_auc_event_vs_background": roc_auc_event_vs_background,
            "d_prime_event_vs_background": d_prime_event_vs_background,
            "fixed_false_alarm_rate_used": float(self.fixed_false_alarm_rate),
            "mean_threshold": (
                float(np.mean(self.threshold_values)) if self.threshold_values else 0.0
            ),
            "mean_threshold_robust_std": (
                float(np.mean(self.threshold_robust_stds))
                if self.threshold_robust_stds else 0.0
            ),
            "mean_pod_threshold": (
                float(np.mean(self.pod_threshold_values))
                if self.pod_threshold_values else 0.0
            ),
            "mean_pod_threshold_robust_std": (
                float(np.mean(self.pod_threshold_robust_stds))
                if self.pod_threshold_robust_stds else 0.0
            ),
            "threshold_background_segment_samples": (
                int(max(self.threshold_background_segment_samples))
                if self.threshold_background_segment_samples else 0
            ),
            "robust_cv_peak_height": robust_cv_peak_height,
            "mean_peak_to_threshold_ratio": (
                float(np.mean(peak_to_threshold_ratios)) if peak_to_threshold_ratios else 0.0
            ),
            "mean_peak_margin_z": float(final_basis["mean_peak_margin_z"]),
            "mean_transit_time_s": (
                float(np.mean(self.transit_times)) if self.transit_times else 0.0
            ),
            "mean_local_snr": (
                float(np.mean(self.local_snrs)) if self.local_snrs else 0.0
            ),
            "initial_position_distribution_mode": (
                first_event_defaults.get("initial_position_distribution_mode", "uniform")
            ),
            "initial_position_distribution_active_fraction": (
                float(np.mean(self.initial_distribution_actives))
                if self.initial_distribution_actives else 0.0
            ),
            "mean_abs_initial_x_norm": (
                float(np.mean(self.initial_abs_x_norms)) if self.initial_abs_x_norms else 0.0
            ),
            "mean_abs_initial_z_norm": (
                float(np.mean(self.initial_abs_z_norms)) if self.initial_abs_z_norms else 0.0
            ),
            "mean_initial_position_confinement_ratio": (
                float(np.mean(self.initial_confinement_ratios))
                if self.initial_confinement_ratios else 0.0
            ),
            "mean_initial_position_confinement_activation": (
                float(np.mean(self.initial_confinement_activations))
                if self.initial_confinement_activations else 0.0
            ),
            "mean_initial_position_center_bias_x_exponent": (
                float(np.mean(self.initial_center_bias_x_exponents))
                if self.initial_center_bias_x_exponents else 1.0
            ),
            "mean_initial_position_center_bias_z_exponent": (
                float(np.mean(self.initial_center_bias_z_exponents))
                if self.initial_center_bias_z_exponents else 1.0
            ),
            "mean_nodi_transit_bandwidth_Hz": (
                float(np.mean(self.nodi_transit_bandwidths))
                if self.nodi_transit_bandwidths else 0.0
            ),
            "mean_nodi_transit_bandwidth_gain": (
                float(np.mean(self.nodi_transit_gains)) if self.nodi_transit_gains else 1.0
            ),
            "mean_nodi_bandwidth_limited_fraction": (
                float(np.mean(self.nodi_bandwidth_limited_fractions))
                if self.nodi_bandwidth_limited_fractions else 0.0
            ),
            "mean_interference_overlap_factor_abs": (
                float(np.mean(self.interference_overlap_factors))
                if self.interference_overlap_factors else 1.0
            ),
            "mean_interference_overlap_factor_phase_rad": (
                float(np.mean(self.interference_overlap_phase_rads))
                if self.interference_overlap_phase_rads else 0.0
            ),
            "single_channel_n_detected": int(single_basis["decision_n_detected"]),
            "single_channel_detection_rate": single_channel_detection_rate,
            "single_channel_detection_rate_wilson_lb": single_channel_detection_rate_wilson_lb,
            "single_channel_stable_detection_rate": float(
                single_basis["stable_detection_rate"]
            ),
            "single_channel_stable_detection_rate_wilson_lb": float(
                single_basis["stable_detection_rate_wilson_lb"]
            ),
            "single_channel_phase_flip_fraction": float(
                single_basis["phase_flip_fraction"]
            ),
            "single_channel_phase_flip_fraction_wilson_ub": float(
                single_basis["phase_flip_fraction_wilson_ub"]
            ),
            "single_channel_mean_peak_margin_z": float(
                single_basis["mean_peak_margin_z"]
            ),
            "paired_channel_n_detected": int(paired_basis["decision_n_detected"]),
            "paired_channel_detection_rate": paired_channel_detection_rate,
            "paired_channel_detection_rate_wilson_lb": paired_channel_detection_rate_wilson_lb,
            "paired_channel_stable_detection_rate": float(
                paired_basis["stable_detection_rate"]
            ),
            "paired_channel_stable_detection_rate_wilson_lb": float(
                paired_basis["stable_detection_rate_wilson_lb"]
            ),
            "paired_channel_phase_flip_fraction": float(
                paired_basis["phase_flip_fraction"]
            ),
            "paired_channel_phase_flip_fraction_wilson_ub": float(
                paired_basis["phase_flip_fraction_wilson_ub"]
            ),
            "paired_channel_mean_peak_margin_z": float(
                paired_basis["mean_peak_margin_z"]
            ),
            "strict_paired_detection_rate": paired_channel_detection_rate,
            "strict_paired_detection_rate_wilson_lb": (
                paired_channel_detection_rate_wilson_lb
            ),
            "paired_detection_rate": (
                float(self.paired_detected_events / self.detected_single_channel_events)
                if self.detected_single_channel_events > 0 else 0.0
            ),
            "best_peak_pairing_rate": (
                float(self.best_peak_paired_count / self.detected_single_channel_events)
                if self.detected_single_channel_events > 0 else 0.0
            ),
            "detection_decision_mode": (
                first_event_defaults.get("detection_decision_mode", "single_channel")
            ),
            "all_heights": heights,
            "all_signed_heights": signed_heights,
            "all_widths": widths,
            "all_peak_to_threshold_ratios": peak_to_threshold_ratios,
            "all_peak_margin_z": peak_margin_z,
            "mean_I_baseline": (
                float(np.mean(self.baseline_levels)) if self.baseline_levels else 0.0
            ),
            "mean_shot_noise_std": (
                float(np.mean(self.shot_noise_std_means))
                if self.shot_noise_std_means else 0.0
            ),
            "mean_A_ref_local": (
                float(np.mean(self.mean_reference_amplitudes))
                if self.mean_reference_amplitudes else 0.0
            ),
            "mean_A_sca_local": (
                float(np.mean(self.mean_scattering_amplitudes))
                if self.mean_scattering_amplitudes else 0.0
            ),
            "mean_reference_to_scattering_amplitude_ratio": (
                float(np.mean(self.reference_to_scattering_ratios))
                if self.reference_to_scattering_ratios else 0.0
            ),
            "rho_requested": float(first_event_defaults.get("rho_requested", 0.0)),
            "rho_physical_envelope_nominal": (
                float(self.rho_physical_nominals[0]) if self.rho_physical_nominals else None
            ),
            "rho_physical_envelope_status": first_event_defaults.get(
                "rho_physical_envelope_status",
                "unavailable",
            ),
            "path_opd_freeze_status": first_event_defaults.get(
                "path_opd_freeze_status",
                "unknown",
            ),
        }
        out.update(_quantile_summary_fields("peak_height", heights))
        out.update(_quantile_summary_fields("peak_margin_z", peak_margin_z))
        out.update(
            _quantile_summary_fields(
                "peak_to_threshold_ratio",
                peak_to_threshold_ratios,
            )
        )
        out.update(_quantile_summary_fields("peak_width_s", widths))
        out.update(_quantile_summary_fields("transit_time_s", self.transit_times))
        out.update(_quantile_summary_fields("local_snr", self.local_snrs))
        out.update(
            self._selected_detector_mode_fields(
                n_detected=n_detected,
                n_total=n_total,
                detection_rate=detection_rate,
                detection_rate_wilson_lb=detection_rate_wilson_lb,
            )
        )
        return out


def _estimate_transit_time_s(
    time_s: np.ndarray,
    envelope: np.ndarray,
    level: float = math.exp(-1.0),
) -> float:
    """
    Estimate the event transit time from the illumination envelope.

    We treat the "useful interaction window" as the time span where the field
    envelope stays above exp(-1), which corresponds to remaining inside the
    central Gaussian waist region.
    """
    time_arr = np.asarray(time_s, dtype=float)
    env_arr = np.asarray(envelope, dtype=float)
    if time_arr.size == 0 or env_arr.size == 0:
        return 0.0
    mask = env_arr >= float(level)
    if not np.any(mask):
        return 0.0
    idx = np.flatnonzero(mask)
    if idx.size == 1:
        if time_arr.size > 1:
            return float(time_arr[1] - time_arr[0])
        return 0.0
    return float(time_arr[idx[-1]] - time_arr[idx[0]])


def _estimate_transit_time_block(
    time_s: np.ndarray,
    envelopes: np.ndarray,
    level: float = math.exp(-1.0),
) -> np.ndarray:
    """Estimate transit times row-wise for a block of illumination envelopes."""
    time_arr = np.asarray(time_s, dtype=float)
    env_arr = np.asarray(envelopes, dtype=float)
    if env_arr.ndim == 1:
        env_arr = env_arr[np.newaxis, :]
    if time_arr.size == 0 or env_arr.size == 0:
        return np.zeros(env_arr.shape[0], dtype=float)

    mask = env_arr >= float(level)
    has_crossing = np.any(mask, axis=1)
    if not np.any(has_crossing):
        return np.zeros(env_arr.shape[0], dtype=float)

    first_idx = np.argmax(mask, axis=1)
    last_idx = mask.shape[1] - 1 - np.argmax(mask[:, ::-1], axis=1)
    transit_times = np.zeros(env_arr.shape[0], dtype=float)
    active = np.flatnonzero(has_crossing)
    transit_times[active] = time_arr[last_idx[active]] - time_arr[first_idx[active]]
    single_sample = active[first_idx[active] == last_idx[active]]
    if single_sample.size > 0 and time_arr.size > 1:
        transit_times[single_sample] = float(time_arr[1] - time_arr[0])
    return transit_times


def _pair_peaks_by_time(
    peaks_primary: list[dict],
    peaks_secondary: list[dict],
    tolerance_s: float,
) -> tuple[int, set[int]]:
    """
    Greedy one-to-one pulse pairing based on peak-time proximity.

    Returns:
        (n_pairs, matched_primary_indices)
    """
    if not peaks_primary or not peaks_secondary:
        return 0, set()

    matched_secondary: set[int] = set()
    matched_primary: set[int] = set()
    n_pairs = 0

    for primary_idx, primary_peak in sorted(
        enumerate(peaks_primary),
        key=lambda item: item[1]["peak_time_s"],
    ):
        best_secondary = None
        best_dt = None
        for secondary_idx, secondary_peak in enumerate(peaks_secondary):
            if secondary_idx in matched_secondary:
                continue
            dt = abs(
                float(primary_peak["peak_time_s"]) -
                float(secondary_peak["peak_time_s"])
            )
            if dt > tolerance_s:
                continue
            if best_dt is None or dt < best_dt:
                best_dt = dt
                best_secondary = secondary_idx
        if best_secondary is not None:
            matched_secondary.add(best_secondary)
            matched_primary.add(primary_idx)
            n_pairs += 1

    return n_pairs, matched_primary


def _build_paired_features(
    primary_features: dict,
    matched_primary_indices: set[int],
) -> dict:
    """
    Keep only the primary-channel peaks that have a matched POD partner.
    """
    peaks_primary = list(primary_features.get("peaks", []))
    paired_peaks = [
        peak for idx, peak in enumerate(peaks_primary)
        if idx in matched_primary_indices
    ]
    return {
        "n_peaks": len(paired_peaks),
        "peaks": paired_peaks,
        "threshold_used": primary_features.get("threshold_used"),
        "detection_mode": primary_features.get("detection_mode", "positive"),
    }


def _compute_diffusion_coefficient(
    particle: Particle,
    medium: Medium,
) -> float | None:
    """
    Compute Stokes-Einstein free-space diffusion coefficient.

    D = kB·T / (6π·η·a)

    Note: This is the free-space formula. For 500–2000nm channels with larger
    particles, confined diffusion correction may be important; near-wall
    suppression is applied in trajectory.py via diffusion_hindrance_model.

    Returns:
        D in m²/s, or None if medium lacks viscosity/temperature data.
    """
    if medium.viscosity_Pa_s is None or medium.temperature_K is None:
        return None
    if medium.viscosity_Pa_s <= 0 or medium.temperature_K <= 0:
        return None
    return _kB * medium.temperature_K / (
        6.0 * math.pi * medium.viscosity_Pa_s * particle.radius_m
    )


def _resolve_summary_metrics_for_engineering_basis(
    summary: dict,
    basis: str,
) -> dict[str, float | int | str]:
    """
    Select detection/stability metrics for engineering scoring and gate checks.

    `final_decision` follows the current `features` path used for final
    detect/miss statistics. The explicit single/paired bases allow engineering
    ranking to be calibrated on a stricter or looser channel-confirmation
    definition without changing the final detection view.
    """
    if basis == "final_decision":
        return {
            "basis": basis,
            "n_detected": int(summary.get("n_detected", 0) or 0),
            "detection_rate": float(summary.get("detection_rate", 0.0) or 0.0),
            "detection_rate_wilson_lb": float(
                summary.get(
                    "detection_rate_wilson_lb",
                    summary.get("detection_rate", 0.0),
                )
                or 0.0
            ),
            "stable_detection_rate": float(
                summary.get("stable_detection_rate", 0.0) or 0.0
            ),
            "stable_detection_rate_wilson_lb": float(
                summary.get(
                    "stable_detection_rate_wilson_lb",
                    summary.get("stable_detection_rate", 0.0),
                )
                or 0.0
            ),
            "phase_flip_fraction": float(
                summary.get("phase_flip_fraction", 0.0) or 0.0
            ),
            "phase_flip_fraction_wilson_ub": float(
                summary.get(
                    "phase_flip_fraction_wilson_ub",
                    summary.get("phase_flip_fraction", 0.0),
                )
                or 0.0
            ),
            "mean_peak_margin_z": float(
                summary.get("mean_peak_margin_z", 0.0) or 0.0
            ),
            "detection_rate_label": "detection_rate",
            "stable_detection_rate_label": "stable_detection_rate",
            "phase_flip_fraction_label": "phase_flip_fraction",
            "mean_peak_margin_z_label": "mean_peak_margin_z",
        }

    if basis == "single_channel":
        return {
            "basis": basis,
            "n_detected": int(summary.get("single_channel_n_detected", 0) or 0),
            "detection_rate": float(
                summary.get("single_channel_detection_rate", 0.0) or 0.0
            ),
            "detection_rate_wilson_lb": float(
                summary.get(
                    "single_channel_detection_rate_wilson_lb",
                    summary.get("single_channel_detection_rate", 0.0),
                )
                or 0.0
            ),
            "stable_detection_rate": float(
                summary.get("single_channel_stable_detection_rate", 0.0) or 0.0
            ),
            "stable_detection_rate_wilson_lb": float(
                summary.get(
                    "single_channel_stable_detection_rate_wilson_lb",
                    summary.get("single_channel_stable_detection_rate", 0.0),
                )
                or 0.0
            ),
            "phase_flip_fraction": float(
                summary.get("single_channel_phase_flip_fraction", 0.0) or 0.0
            ),
            "phase_flip_fraction_wilson_ub": float(
                summary.get(
                    "single_channel_phase_flip_fraction_wilson_ub",
                    summary.get("single_channel_phase_flip_fraction", 0.0),
                )
                or 0.0
            ),
            "mean_peak_margin_z": float(
                summary.get("single_channel_mean_peak_margin_z", 0.0) or 0.0
            ),
            "detection_rate_label": "single_channel_detection_rate",
            "stable_detection_rate_label": "single_channel_stable_detection_rate",
            "phase_flip_fraction_label": "single_channel_phase_flip_fraction",
            "mean_peak_margin_z_label": "single_channel_mean_peak_margin_z",
        }

    if basis == "paired_channel":
        return {
            "basis": basis,
            "n_detected": int(summary.get("paired_channel_n_detected", 0) or 0),
            "detection_rate": float(
                summary.get("paired_channel_detection_rate", 0.0) or 0.0
            ),
            "detection_rate_wilson_lb": float(
                summary.get(
                    "paired_channel_detection_rate_wilson_lb",
                    summary.get("paired_channel_detection_rate", 0.0),
                )
                or 0.0
            ),
            "stable_detection_rate": float(
                summary.get("paired_channel_stable_detection_rate", 0.0) or 0.0
            ),
            "stable_detection_rate_wilson_lb": float(
                summary.get(
                    "paired_channel_stable_detection_rate_wilson_lb",
                    summary.get("paired_channel_stable_detection_rate", 0.0),
                )
                or 0.0
            ),
            "phase_flip_fraction": float(
                summary.get("paired_channel_phase_flip_fraction", 0.0) or 0.0
            ),
            "phase_flip_fraction_wilson_ub": float(
                summary.get(
                    "paired_channel_phase_flip_fraction_wilson_ub",
                    summary.get("paired_channel_phase_flip_fraction", 0.0),
                )
                or 0.0
            ),
            "mean_peak_margin_z": float(
                summary.get("paired_channel_mean_peak_margin_z", 0.0) or 0.0
            ),
            "detection_rate_label": "paired_channel_detection_rate",
            "stable_detection_rate_label": "paired_channel_stable_detection_rate",
            "phase_flip_fraction_label": "paired_channel_phase_flip_fraction",
            "mean_peak_margin_z_label": "paired_channel_mean_peak_margin_z",
        }

    raise ValueError(f"Unknown engineering_decision_basis: {basis}")


def simulate_one_event(
    particle: Particle,
    medium: Medium,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    E_sca_unit_normalized: complex | float,
    reference: dict,
    theta_det_rad: float,
    rng: np.random.Generator,
    scattering_phase_diagnostics: dict | None = None,
    *,
    medium_refractive_index: float | None = None,
    diffusion_coefficient: float | None = None,
    retain_full_payload: bool = True,
    readout_context: _ReadoutContext | None = None,
    trajectory_context: TrajectoryContext | None = None,
    event_case_context: _EventCaseContext | None = None,
    unit_position_sample: tuple[float, float, float] | None = None,
    summary_accumulator: _BatchSummaryAccumulator | None = None,
) -> dict:
    """
    Simulate a single particle transit event.

    Each call generates a new random (x0, z0) and noise realization,
    producing statistically independent events within a batch.

    When include_diffusion=True, computes Stokes-Einstein D and passes it
    to trajectory for Brownian random walk.

    Args:
        particle: Particle type.
        medium: Medium.
        channel: Channel geometry.
        optical: Optical system.
        sim_cfg: Simulation config.
        E_sca_unit_normalized: Pre-computed normalized scattering amplitude (scalar).
        reference: Pre-computed reference field dict.
        theta_det_rad: Effective collection angle used by this case.
        rng: Random number generator (shared across batch for reproducibility).
        scattering_phase_diagnostics: Optional case-level Mie / projection phase
            diagnostics to expose alongside event traces.

    Returns:
        dict with trajectory, signals, features, and metadata.
    """
    if event_case_context is None:
        event_case_context = _build_event_case_context(
            channel,
            sim_cfg,
            particle_radius_m=particle.radius_m,
        )
    transport_channel = event_case_context.transport_channel
    transport_cfg = event_case_context.transport_cfg
    trajectory_context = trajectory_context or event_case_context.trajectory_context

    # 1. Random initial position
    x0, z0, position_diag = sample_initial_position(
        transport_channel,
        rng,
        particle.radius_m,
        sim_cfg=transport_cfg,
        unit_position_sample=unit_position_sample,
    )

    # 2. Compute diffusion coefficient
    D = diffusion_coefficient
    if D is None and sim_cfg.include_diffusion:
        D = _compute_diffusion_coefficient(particle, medium)

    medium_ri = (
        float(medium_refractive_index)
        if medium_refractive_index is not None
        else float(medium.refractive_index_at(optical.wavelength_m))
    )

    # 3. Trajectory (with optional Brownian diffusion)
    trajectory = simulate_particle_trajectory(
        transport_channel, optical, transport_cfg, x0, z0,
        particle_radius_m=particle.radius_m,
        diffusion_coefficient=D, rng=rng,
        trajectory_context=trajectory_context,
    )

    # 4. Illumination envelope
    illumination = compute_illumination_envelope(
        trajectory["x_m"],
        trajectory["y_m"],
        trajectory["z_m"],
        optical,
        medium_refractive_index=medium_ri,
        sim_cfg=sim_cfg,
    )
    # Transit bandwidth should follow the scalar interaction window, not detector-
    # side amplitude factors such as polarization leakage or matched/crossed
    # projection choices.
    transit_time_s = _estimate_transit_time_s(
        trajectory["time_s"],
        illumination["A_env_scalar"],
    )

    reference_trace = compute_reference_field_trace(
        trajectory,
        reference,
        channel,
        optical,
        sim_cfg,
        initial_x_m=x0,
        initial_z_m=z0,
    )

    # 5. Scattering field trace
    sca_trace = compute_scattering_field_trace(
        trajectory, E_sca_unit_normalized, optical, illumination,
        transport_channel, x0, z0, sim_cfg.phase_model,
        coupling_model=transport_cfg.coupling_model,
        path_opd_model=sim_cfg.path_opd_model,
        detection_theta_rad=theta_det_rad,
        medium_refractive_index=medium_ri,
        reference_phase_rad=reference_trace["phi_ref_trace_rad"],
        scattering_phase_diagnostics=scattering_phase_diagnostics,
        include_phase_diagnostics=retain_full_payload,
    )

    # 6. Interferometric trace
    trace = generate_interferometric_trace(
        trajectory, {**reference, **reference_trace}, sca_trace, sim_cfg
    )
    route_trace = _route_trace_payload(
        trace,
        sim_cfg=sim_cfg,
        E_sca_unit_normalized=E_sca_unit_normalized,
        reference=reference,
    )

    # 7. Add noise
    noisy = add_detector_noise(
        np.asarray(route_trace["route_signal_trace"], dtype=float),
        trajectory["time_s"],
        sim_cfg,
        rng,
        detected_intensity=np.asarray(route_trace["route_detected_intensity"], dtype=float),
        baseline_intensity=trace.get("I_baseline"),
    )

    # 8. Readout chain: raw noisy detector output -> detection channel
    readout = apply_readout_chain(
        noisy["signal_noisy"],
        trajectory["time_s"],
        sim_cfg,
        transit_time_s=transit_time_s,
        readout_context=readout_context,
        export_full_diagnostics=retain_full_payload,
    )
    if (
        sim_cfg.post_readout_noise_std <= 0
        and sim_cfg.post_readout_colored_noise_std <= 0
        and sim_cfg.post_readout_drift_slope == 0
    ):
        zero_noise = np.zeros_like(readout["signal_detect"], dtype=float)
        post_readout = {
            "signal_post_readout": np.asarray(readout["signal_detect"], dtype=float),
            "post_readout_noise": zero_noise,
        }
        post_readout_nodi = (
            {
                "signal_post_readout": np.asarray(readout["signal_nodi"], dtype=float),
                "post_readout_noise": zero_noise,
            }
            if retain_full_payload
            else None
        )
        post_readout_pod = {
            "signal_post_readout": np.asarray(readout["signal_pod"], dtype=float),
            "post_readout_noise": zero_noise,
        }
    else:
        post_readout = add_post_readout_noise(
            readout["signal_detect"], trajectory["time_s"], sim_cfg, rng
        )
        if retain_full_payload:
            post_readout_nodi = add_post_readout_noise(
                readout["signal_nodi"], trajectory["time_s"], sim_cfg, rng
            )
        else:
            _advance_post_readout_noise_rng(
                np.asarray(readout["signal_nodi"]).shape,
                sim_cfg,
                rng,
                time_s=trajectory["time_s"],
            )
            post_readout_nodi = None
        post_readout_pod = add_post_readout_noise(
            readout["signal_pod"], trajectory["time_s"], sim_cfg, rng
        )

    # 9. Threshold from the configured background/blank surrogate.
    pulse_time_s, pulse_traces, pulse_sampling_diag = (
        _resample_traces_for_pulse_extraction(
            trajectory["time_s"],
            (
                np.asarray(post_readout["signal_post_readout"], dtype=float),
                np.asarray(post_readout_pod["signal_post_readout"], dtype=float),
            ),
            sim_cfg,
        )
    )
    pulse_signal = pulse_traces[0]
    pulse_pod_signal = pulse_traces[1]
    pulse_context_active = build_pulse_extraction_context(
        pulse_time_s,
        sim_cfg.min_peak_width_s,
        sim_cfg.min_peak_interval_s,
    )
    threshold_stats, n_bg, threshold_background_source_runtime = (
        _estimate_runtime_threshold_stats_1d(pulse_signal, sim_cfg)
    )
    threshold = threshold_stats["threshold"]

    # 10. Pulse extraction
    features_nodi = extract_pulse_features(
        pulse_time_s,
        pulse_signal,
        threshold,
        sim_cfg.min_peak_width_s,
        sim_cfg.min_peak_interval_s,
        detection_mode=sim_cfg.pulse_detection_mode,
        context=pulse_context_active,
        include_area_prominence=retain_full_payload,
        width_measure_mode=sim_cfg.pulse_width_measure_mode,
        duration_estimation_policy=sim_cfg.pulse_duration_estimation_policy,
    )
    pod_threshold_stats, pod_n_bg, pod_threshold_background_source_runtime = (
        _estimate_runtime_threshold_stats_1d(pulse_pod_signal, sim_cfg)
    )
    features_pod = extract_pulse_features(
        pulse_time_s,
        pulse_pod_signal,
        pod_threshold_stats["threshold"],
        sim_cfg.min_peak_width_s,
        sim_cfg.min_peak_interval_s,
        detection_mode=sim_cfg.pulse_detection_mode,
        context=pulse_context_active,
        include_area_prominence=retain_full_payload,
        width_measure_mode=sim_cfg.pulse_width_measure_mode,
        duration_estimation_policy=sim_cfg.pulse_duration_estimation_policy,
    )
    paired_pulse_count, paired_primary_indices = _pair_peaks_by_time(
        features_nodi["peaks"],
        features_pod["peaks"],
        sim_cfg.pulse_pairing_tolerance_s,
    )
    features_paired = _build_paired_features(features_nodi, paired_primary_indices)
    if sim_cfg.detection_decision_mode == "paired_channel":
        features = features_paired
    else:
        features = features_nodi
    detected_single_channel = features_nodi["n_peaks"] > 0
    detected_paired_channel = features_paired["n_peaks"] > 0
    best_peak_paired = False
    if features_nodi["n_peaks"] > 0:
        best_peak_idx = int(np.argmax([peak["peak_height"] for peak in features_nodi["peaks"]]))
        best_peak_paired = best_peak_idx in paired_primary_indices
    signal_detect_arr = np.asarray(pulse_signal, dtype=float)
    local_snr = float(
        np.max(np.abs(signal_detect_arr)) / max(threshold_stats["robust_std"], 1e-15)
    )
    A_ref_trace = np.asarray(reference_trace.get("A_ref_trace", np.zeros_like(trace["signal_trace"])), dtype=float)
    A_sca_trace = np.asarray(sca_trace.get("A_sca", np.zeros_like(trace["signal_trace"])), dtype=float)
    mean_reference_to_scattering_ratio = float(
        np.mean(A_ref_trace / np.clip(A_sca_trace, 1e-15, None))
    )
    reference_dominated_fraction = (
        float(np.mean(A_ref_trace >= A_sca_trace))
        if retain_full_payload or summary_accumulator is None
        else None
    )
    scattering_projection_basis = event_case_context.scattering_projection_basis
    signal_eval = np.asarray(pulse_signal, dtype=float)
    if sim_cfg.pulse_detection_mode == "absolute":
        signal_eval = np.abs(signal_eval)
    background_eval, _, _ = _threshold_background_segments(signal_eval, sim_cfg)
    robust_std = max(float(threshold_stats["robust_std"]), 1e-15)
    if signal_eval.size > 0:
        event_max_margin_z = float((np.max(signal_eval) - threshold) / robust_std)
        background_max_margin_z = float(
            (np.max(background_eval) - threshold) / robust_std
        )
    else:
        event_max_margin_z = float(-threshold / robust_std)
        background_max_margin_z = event_max_margin_z

    if not retain_full_payload and summary_accumulator is not None:
        summary_accumulator.update_from_simulation(
            features=features,
            features_nodi=features_nodi,
            features_paired=features_paired,
            detected_single_channel=detected_single_channel,
            detected_paired_channel=detected_paired_channel,
            threshold=threshold,
            threshold_robust_std=threshold_stats["robust_std"],
            pod_threshold=pod_threshold_stats["threshold"],
            pod_threshold_robust_std=pod_threshold_stats["robust_std"],
            threshold_background_segment_samples=n_bg,
            trace=trace,
            noisy=noisy,
            A_ref_trace=A_ref_trace,
            A_sca_trace=A_sca_trace,
            mean_reference_to_scattering_ratio=mean_reference_to_scattering_ratio,
            transit_time_s=transit_time_s,
            local_snr=local_snr,
            position_diag=position_diag,
            readout=readout,
            illumination=illumination,
            reference=reference,
            paired_pulse_count=paired_pulse_count,
            best_peak_paired=best_peak_paired,
            sca_trace=sca_trace,
            event_max_margin_z=event_max_margin_z,
            background_max_margin_z=background_max_margin_z,
            detection_decision_mode=sim_cfg.detection_decision_mode,
        )
        return {}

    event_result = {
        "features": features,
        "features_nodi": features_nodi,
        "features_paired": features_paired,
        "detected_single_channel": detected_single_channel,
        "detected_paired_channel": detected_paired_channel,
        "threshold": threshold,
        "threshold_robust_std": threshold_stats["robust_std"],
        "pod_threshold": pod_threshold_stats["threshold"],
        "pod_threshold_robust_std": pod_threshold_stats["robust_std"],
        "threshold_background_segment_samples": n_bg,
        "threshold_background_source_runtime": threshold_background_source_runtime,
        "pod_threshold_background_segment_samples": pod_n_bg,
        "pod_threshold_background_source_runtime": pod_threshold_background_source_runtime,
        **pulse_sampling_diag,
        "pulse_detection_mode": sim_cfg.pulse_detection_mode,
        "I_baseline": trace.get("I_baseline"),
        "shot_noise_std_mean": noisy.get("shot_noise_std_mean", 0.0),
        "shot_noise_reference_dominated_fraction": noisy.get(
            "shot_noise_reference_dominated_fraction",
            0.0,
        ),
        "mean_shot_noise_intensity_proxy": noisy.get("mean_shot_noise_intensity_proxy", 0.0),
        "mean_shot_noise_baseline_proxy": noisy.get("mean_shot_noise_baseline_proxy", 0.0),
        "mean_A_ref_local": float(np.mean(A_ref_trace)),
        "mean_A_sca_local": float(np.mean(A_sca_trace)),
        "mean_reference_to_scattering_amplitude_ratio": mean_reference_to_scattering_ratio,
        "reference_dominated_fraction": (
            reference_dominated_fraction
            if reference_dominated_fraction is not None
            else float(np.mean(A_ref_trace >= A_sca_trace))
        ),
        "transit_time_s": transit_time_s,
        "local_snr": local_snr,
        "initial_position_distribution_mode": position_diag.get(
            "initial_position_distribution_mode",
            "uniform",
        ),
        "initial_position_distribution_active": position_diag.get(
            "initial_position_distribution_active",
            False,
        ),
        "initial_position_x_norm": position_diag.get("initial_position_x_norm", 0.0),
        "initial_position_z_norm": position_diag.get("initial_position_z_norm", 0.0),
        "initial_position_confinement_ratio": position_diag.get(
            "initial_position_confinement_ratio",
            0.0,
        ),
        "initial_position_confinement_activation": position_diag.get(
            "initial_position_confinement_activation",
            0.0,
        ),
        "initial_position_center_bias_x_exponent": position_diag.get(
            "initial_position_center_bias_x_exponent",
            1.0,
        ),
        "initial_position_center_bias_z_exponent": position_diag.get(
            "initial_position_center_bias_z_exponent",
            1.0,
        ),
        "nodi_transit_bandwidth_Hz": readout.get("nodi_transit_bandwidth_Hz"),
        "nodi_transit_bandwidth_gain": readout.get("nodi_transit_bandwidth_gain"),
        "nodi_bandwidth_limited_fraction": readout.get("nodi_bandwidth_limited_fraction"),
        "interference_overlap_factor_abs": trace.get("interference_overlap_factor_abs"),
        "interference_overlap_factor_phase_rad": trace.get(
            "interference_overlap_factor_phase_rad"
        ),
        "illumination_projection_coupling_status": illumination.get(
            "illumination_projection_coupling_status"
        ),
        "reference_projection_coupling_status": reference.get(
            "reference_projection_coupling_status"
        ),
        "interference_projection_coupling_status": reference.get(
            "reference_projection_coupling_status"
        ),
        "rho_requested": reference.get("rho_requested", float(sim_cfg.rho)),
        "rho_physical_envelope_nominal": reference.get("rho_physical_envelope_nominal"),
        "rho_physical_envelope_status": reference.get("rho_physical_envelope_status"),
        "has_paired_pulse": paired_pulse_count > 0,
        "best_peak_paired": best_peak_paired,
        "path_opd_model": sca_trace.get("path_opd_model", sim_cfg.path_opd_model),
        "path_opd_reference_plane": sca_trace.get("path_opd_reference_plane", "unknown"),
        "path_opd_z_geometry_factor": sca_trace.get("path_opd_z_geometry_factor", 1.0),
        "path_opd_z_reference_mode": sca_trace.get("path_opd_z_reference_mode", "unknown"),
        "path_opd_default_model": sca_trace.get("path_opd_default_model", sim_cfg.path_opd_model),
        "path_opd_model_role": sca_trace.get("path_opd_model_role", "unknown"),
        "path_opd_default_frozen": sca_trace.get("path_opd_default_frozen", True),
        "path_opd_freeze_status": sca_trace.get("path_opd_freeze_status", "unknown"),
        "detection_decision_mode": sim_cfg.detection_decision_mode,
        "event_max_margin_z": event_max_margin_z,
        "background_max_margin_z": background_max_margin_z,
        "detector_route_id": str(getattr(sim_cfg, "detector_route_id", "A_hybrid")),
        "detector_route_status": route_trace.get("detector_route_status"),
        "self_route_scale_r_self": route_trace.get("r_self"),
        "self_collapsed_detector": route_trace.get("self_collapsed_detector"),
        "self_roi_detector": route_trace.get("self_roi_detector"),
    }

    if not retain_full_payload:
        return event_result

    reference_to_scattering_ratio = A_ref_trace / np.clip(A_sca_trace, 1e-15, None)
    event_result.update({
        "trajectory": trajectory,
        "signal_trace": np.asarray(route_trace["route_signal_trace"], dtype=float),
        "signal_trace_default_production": trace["signal_trace"],
        "interference_cross_term": trace.get("interference_cross_term"),
        "interference_cross_term_collapsed": trace.get("interference_cross_term_collapsed"),
        "interference_cross_term_joint": trace.get("interference_cross_term_joint"),
        "interference_cross_term_mode": trace.get("interference_cross_term_mode"),
        "interference_overlap_factor_abs": trace.get("interference_overlap_factor_abs"),
        "interference_overlap_factor_phase_rad": trace.get("interference_overlap_factor_phase_rad"),
        "interference_overlap_status": trace.get("interference_overlap_status"),
        "scattering_only_intensity": trace.get("scattering_only_intensity"),
        "signal_raw_noisy": noisy["signal_noisy"],
        "pulse_time_s": pulse_time_s,
        "signal_noisy": pulse_signal,
        "signal_pre_readout_noisy": noisy["signal_noisy"],
        "shot_noise": noisy.get("shot_noise"),
        "I_baseline": trace.get("I_baseline"),
        "I_baseline_trace": trace.get("I_baseline_trace"),
        "signal_detect_pre_post": readout["signal_detect"],
        "signal_nodi": post_readout_nodi["signal_post_readout"],
        "signal_pod": post_readout_pod["signal_post_readout"],
        "signal_nodi_pre_post": readout["signal_nodi"],
        "signal_pod_pre_post": readout["signal_pod"],
        "signal_nodi_true": readout["signal_nodi_true"],
        "signal_pod_true": readout["signal_pod_true"],
        "signal_nodi_leak": readout.get("signal_nodi_leak"),
        "signal_pod_leak": readout.get("signal_pod_leak"),
        "nodi_transit_response_model": readout.get("nodi_transit_response_model"),
        "nodi_transit_bandwidth_Hz": readout.get("nodi_transit_bandwidth_Hz"),
        "nodi_transit_bandwidth_gain": readout.get("nodi_transit_bandwidth_gain"),
        "nodi_bandwidth_limited_fraction": readout.get("nodi_bandwidth_limited_fraction"),
        "nodi_lockin_bandwidth_Hz": readout.get("nodi_lockin_bandwidth_Hz"),
        "post_readout_noise": post_readout["post_readout_noise"],
        "detector_route_id": str(getattr(sim_cfg, "detector_route_id", "A_hybrid")),
        "detector_route_status": route_trace.get("detector_route_status"),
        "self_route_scale_r_self": route_trace.get("r_self"),
        "self_collapsed_detector": route_trace.get("self_collapsed_detector"),
        "self_roi_detector": route_trace.get("self_roi_detector"),
        "A_ref_trace": reference_trace.get("A_ref_trace"),
        "A_sca_trace": sca_trace.get("A_sca"),
        "median_reference_to_scattering_amplitude_ratio": float(
            np.median(reference_to_scattering_ratio)
        ),
        "phi_ref_rad": reference_trace.get("phi_ref_trace_rad"),
        "reference_amplitude_scale": reference_trace.get("reference_amplitude_scale"),
        "reference_spatial_phase_rad": reference_trace.get("reference_spatial_phase_rad"),
        "reference_spatial_mode": reference_trace.get("reference_spatial_mode"),
        "reference_x_norm": reference_trace.get("reference_x_norm"),
        "reference_z_norm": reference_trace.get("reference_z_norm"),
        "phi_material_rad": sca_trace.get("phi_material_rad"),
        "phi_projection_rad": sca_trace.get("phi_projection_rad"),
        "phi_material_parallel_rad": sca_trace.get("phi_material_parallel_rad"),
        "phi_material_perpendicular_rad": sca_trace.get("phi_material_perpendicular_rad"),
        "phi_beam_rad": sca_trace.get("phi_beam_rad"),
        "phi_beam_gouy_rad": sca_trace.get("phi_beam_gouy_rad"),
        "phi_beam_curv_rad": sca_trace.get("phi_beam_curv_rad"),
        "phi_focus_crossing_rad": sca_trace.get("phi_focus_crossing_rad"),
        "phi_gouy_ref_rad": sca_trace.get("phi_gouy_ref_rad"),
        "phi_gouy_sca_rad": sca_trace.get("phi_gouy_sca_rad"),
        "delta_phi_gouy_rad": sca_trace.get("delta_phi_gouy_rad"),
        "gouy_dedup_active": sca_trace.get("gouy_dedup_active"),
        "phi_gouy_reference_status": sca_trace.get("phi_gouy_reference_status"),
        "phi_gouy_scattering_status": sca_trace.get("phi_gouy_scattering_status"),
        "phi_gouy_semantics_status": sca_trace.get("phi_gouy_semantics_status"),
        "phi_sca_path_x_rad": sca_trace.get("phi_sca_path_x_rad"),
        "phi_sca_path_z_rad": sca_trace.get("phi_sca_path_z_rad"),
        "phi_ref_trace_rad": sca_trace.get("phi_ref_rad"),
        "phi_sca_path_rad": sca_trace.get("phi_sca_path_rad"),
        "phi_extra_rad": sca_trace.get("phi_extra_rad"),
        "scattering_projection_basis": scattering_projection_basis,
        "illumination_projection_basis": illumination.get("illumination_projection_basis"),
        "illumination_effective_basis": illumination.get("illumination_effective_basis"),
        "illumination_projection_basis_match": illumination.get(
            "illumination_projection_basis_match"
        ),
        "illumination_projection_coupling_status": illumination.get(
            "illumination_projection_coupling_status"
        ),
        "reference_projection_basis": reference.get("reference_projection_basis"),
        "reference_effective_basis": reference.get("reference_effective_basis"),
        "reference_projection_basis_match": reference.get(
            "reference_projection_basis_match"
        ),
        "reference_projection_coupling_status": reference.get(
            "reference_projection_coupling_status"
        ),
        "interference_projection_basis": reference.get("reference_projection_basis"),
        "interference_projection_basis_match": reference.get(
            "reference_projection_basis_match"
        ),
        "interference_projection_coupling_status": reference.get(
            "reference_projection_coupling_status"
        ),
        "delta_phi_ref_rad": sca_trace.get("delta_phi_ref_rad"),
        "readout_model": sim_cfg.readout_model,
        "features_pod": features_pod,
        "pulse_pairing_tolerance_s": sim_cfg.pulse_pairing_tolerance_s,
        "paired_pulse_count": paired_pulse_count,
        "strict_paired_detected": detected_paired_channel,
        "initial_position": (x0, z0),
        "initial_position_center_bias_strength": position_diag.get(
            "initial_position_center_bias_strength",
            0.0,
        ),
        "initial_position_center_bias_min_confinement_ratio": position_diag.get(
            "initial_position_center_bias_min_confinement_ratio",
            0.0,
        ),
        "transport_channel_width_m": transport_channel.width_m,
        "transport_channel_depth_m": transport_channel.depth_m,
        "threshold_background_median": threshold_stats["median"],
        "pod_threshold": pod_threshold_stats["threshold"],
        "pod_threshold_background_median": pod_threshold_stats["median"],
        "pod_threshold_robust_std": pod_threshold_stats["robust_std"],
    })
    return event_result


def _simulate_one_event_from_shared_physical_state(
    *,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    E_sca_unit_normalized: complex | float,
    reference: dict,
    theta_det_rad: float,
    rng: np.random.Generator,
    scattering_phase_diagnostics: dict | None,
    medium_refractive_index: float,
    transport_channel: Channel,
    transport_cfg: SimulationConfig,
    trajectory: dict,
    illumination: dict,
    transit_time_s: float,
    reference_trace: dict,
    x0: float,
    z0: float,
    position_diag: dict,
    retain_full_payload: bool,
    readout_context: _ReadoutContext | None,
    event_case_context: _EventCaseContext,
    summary_accumulator: _BatchSummaryAccumulator | None,
) -> dict:
    """Evaluate one normalization/readout view from a precomputed physical event."""
    sca_trace = compute_scattering_field_trace(
        trajectory,
        E_sca_unit_normalized,
        optical,
        illumination,
        transport_channel,
        x0,
        z0,
        sim_cfg.phase_model,
        coupling_model=transport_cfg.coupling_model,
        path_opd_model=sim_cfg.path_opd_model,
        detection_theta_rad=theta_det_rad,
        medium_refractive_index=medium_refractive_index,
        reference_phase_rad=reference_trace["phi_ref_trace_rad"],
        scattering_phase_diagnostics=scattering_phase_diagnostics,
        include_phase_diagnostics=retain_full_payload,
    )
    trace = generate_interferometric_trace(
        trajectory,
        {**reference, **reference_trace},
        sca_trace,
        sim_cfg,
    )
    route_trace = _route_trace_payload(
        trace,
        sim_cfg=sim_cfg,
        E_sca_unit_normalized=E_sca_unit_normalized,
        reference=reference,
    )
    noisy = add_detector_noise(
        np.asarray(route_trace["route_signal_trace"], dtype=float),
        trajectory["time_s"],
        sim_cfg,
        rng,
        detected_intensity=np.asarray(route_trace["route_detected_intensity"], dtype=float),
        baseline_intensity=trace.get("I_baseline"),
    )
    readout = apply_readout_chain(
        noisy["signal_noisy"],
        trajectory["time_s"],
        sim_cfg,
        transit_time_s=transit_time_s,
        readout_context=readout_context,
        export_full_diagnostics=retain_full_payload,
    )
    if (
        sim_cfg.post_readout_noise_std <= 0
        and sim_cfg.post_readout_colored_noise_std <= 0
        and sim_cfg.post_readout_drift_slope == 0
    ):
        zero_noise = np.zeros_like(readout["signal_detect"], dtype=float)
        post_readout = {
            "signal_post_readout": np.asarray(readout["signal_detect"], dtype=float),
            "post_readout_noise": zero_noise,
        }
        post_readout_nodi = (
            {
                "signal_post_readout": np.asarray(readout["signal_nodi"], dtype=float),
                "post_readout_noise": zero_noise,
            }
            if retain_full_payload
            else None
        )
        post_readout_pod = {
            "signal_post_readout": np.asarray(readout["signal_pod"], dtype=float),
            "post_readout_noise": zero_noise,
        }
    else:
        post_readout = add_post_readout_noise(
            readout["signal_detect"],
            trajectory["time_s"],
            sim_cfg,
            rng,
        )
        if retain_full_payload:
            post_readout_nodi = add_post_readout_noise(
                readout["signal_nodi"],
                trajectory["time_s"],
                sim_cfg,
                rng,
            )
        else:
            _advance_post_readout_noise_rng(
                np.asarray(readout["signal_nodi"]).shape,
                sim_cfg,
                rng,
                time_s=trajectory["time_s"],
            )
            post_readout_nodi = None
        post_readout_pod = add_post_readout_noise(
            readout["signal_pod"],
            trajectory["time_s"],
            sim_cfg,
            rng,
        )

    pulse_time_s, pulse_traces, pulse_sampling_diag = (
        _resample_traces_for_pulse_extraction(
            trajectory["time_s"],
            (
                np.asarray(post_readout["signal_post_readout"], dtype=float),
                np.asarray(post_readout_pod["signal_post_readout"], dtype=float),
            ),
            sim_cfg,
        )
    )
    pulse_signal = pulse_traces[0]
    pulse_pod_signal = pulse_traces[1]
    pulse_context_active = build_pulse_extraction_context(
        pulse_time_s,
        sim_cfg.min_peak_width_s,
        sim_cfg.min_peak_interval_s,
    )
    threshold_stats, n_bg, threshold_background_source_runtime = (
        _estimate_runtime_threshold_stats_1d(pulse_signal, sim_cfg)
    )
    threshold = threshold_stats["threshold"]
    features_nodi = extract_pulse_features(
        pulse_time_s,
        pulse_signal,
        threshold,
        sim_cfg.min_peak_width_s,
        sim_cfg.min_peak_interval_s,
        detection_mode=sim_cfg.pulse_detection_mode,
        context=pulse_context_active,
        include_area_prominence=retain_full_payload,
        width_measure_mode=sim_cfg.pulse_width_measure_mode,
        duration_estimation_policy=sim_cfg.pulse_duration_estimation_policy,
    )
    pod_threshold_stats, pod_n_bg, pod_threshold_background_source_runtime = (
        _estimate_runtime_threshold_stats_1d(pulse_pod_signal, sim_cfg)
    )
    features_pod = extract_pulse_features(
        pulse_time_s,
        pulse_pod_signal,
        pod_threshold_stats["threshold"],
        sim_cfg.min_peak_width_s,
        sim_cfg.min_peak_interval_s,
        detection_mode=sim_cfg.pulse_detection_mode,
        context=pulse_context_active,
        include_area_prominence=retain_full_payload,
        width_measure_mode=sim_cfg.pulse_width_measure_mode,
        duration_estimation_policy=sim_cfg.pulse_duration_estimation_policy,
    )
    paired_pulse_count, paired_primary_indices = _pair_peaks_by_time(
        features_nodi["peaks"],
        features_pod["peaks"],
        sim_cfg.pulse_pairing_tolerance_s,
    )
    features_paired = _build_paired_features(features_nodi, paired_primary_indices)
    features = (
        features_paired
        if sim_cfg.detection_decision_mode == "paired_channel"
        else features_nodi
    )
    detected_single_channel = features_nodi["n_peaks"] > 0
    detected_paired_channel = features_paired["n_peaks"] > 0
    best_peak_paired = False
    if features_nodi["n_peaks"] > 0:
        best_peak_idx = int(
            np.argmax([peak["peak_height"] for peak in features_nodi["peaks"]])
        )
        best_peak_paired = best_peak_idx in paired_primary_indices
    signal_detect_arr = np.asarray(pulse_signal, dtype=float)
    local_snr = float(
        np.max(np.abs(signal_detect_arr)) / max(threshold_stats["robust_std"], 1e-15)
    )
    A_ref_trace = np.asarray(
        reference_trace.get("A_ref_trace", np.zeros_like(trace["signal_trace"])),
        dtype=float,
    )
    A_sca_trace = np.asarray(
        sca_trace.get("A_sca", np.zeros_like(trace["signal_trace"])),
        dtype=float,
    )
    mean_reference_to_scattering_ratio = float(
        np.mean(A_ref_trace / np.clip(A_sca_trace, 1e-15, None))
    )
    reference_dominated_fraction = (
        float(np.mean(A_ref_trace >= A_sca_trace))
        if retain_full_payload or summary_accumulator is None
        else None
    )
    scattering_projection_basis = event_case_context.scattering_projection_basis
    signal_eval = np.asarray(pulse_signal, dtype=float)
    if sim_cfg.pulse_detection_mode == "absolute":
        signal_eval = np.abs(signal_eval)
    background_eval, _, _ = _threshold_background_segments(signal_eval, sim_cfg)
    robust_std = max(float(threshold_stats["robust_std"]), 1e-15)
    if signal_eval.size > 0:
        event_max_margin_z = float((np.max(signal_eval) - threshold) / robust_std)
        background_max_margin_z = float(
            (np.max(background_eval) - threshold) / robust_std
        )
    else:
        event_max_margin_z = float(-threshold / robust_std)
        background_max_margin_z = event_max_margin_z

    if not retain_full_payload and summary_accumulator is not None:
        summary_accumulator.update_from_simulation(
            features=features,
            features_nodi=features_nodi,
            features_paired=features_paired,
            detected_single_channel=detected_single_channel,
            detected_paired_channel=detected_paired_channel,
            threshold=threshold,
            threshold_robust_std=threshold_stats["robust_std"],
            pod_threshold=pod_threshold_stats["threshold"],
            pod_threshold_robust_std=pod_threshold_stats["robust_std"],
            threshold_background_segment_samples=n_bg,
            trace=trace,
            noisy=noisy,
            A_ref_trace=A_ref_trace,
            A_sca_trace=A_sca_trace,
            mean_reference_to_scattering_ratio=mean_reference_to_scattering_ratio,
            transit_time_s=transit_time_s,
            local_snr=local_snr,
            position_diag=position_diag,
            readout=readout,
            illumination=illumination,
            reference=reference,
            paired_pulse_count=paired_pulse_count,
            best_peak_paired=best_peak_paired,
            sca_trace=sca_trace,
            event_max_margin_z=event_max_margin_z,
            background_max_margin_z=background_max_margin_z,
            detection_decision_mode=sim_cfg.detection_decision_mode,
        )
        return {}

    event_result = {
        "features": features,
        "features_nodi": features_nodi,
        "features_paired": features_paired,
        "detected_single_channel": detected_single_channel,
        "detected_paired_channel": detected_paired_channel,
        "threshold": threshold,
        "threshold_robust_std": threshold_stats["robust_std"],
        "pod_threshold": pod_threshold_stats["threshold"],
        "pod_threshold_robust_std": pod_threshold_stats["robust_std"],
        "threshold_background_segment_samples": n_bg,
        "threshold_background_source_runtime": threshold_background_source_runtime,
        "pod_threshold_background_segment_samples": pod_n_bg,
        "pod_threshold_background_source_runtime": pod_threshold_background_source_runtime,
        **pulse_sampling_diag,
        "pulse_detection_mode": sim_cfg.pulse_detection_mode,
        "I_baseline": trace.get("I_baseline"),
        "shot_noise_std_mean": noisy.get("shot_noise_std_mean", 0.0),
        "shot_noise_reference_dominated_fraction": noisy.get(
            "shot_noise_reference_dominated_fraction",
            0.0,
        ),
        "mean_shot_noise_intensity_proxy": noisy.get("mean_shot_noise_intensity_proxy", 0.0),
        "mean_shot_noise_baseline_proxy": noisy.get("mean_shot_noise_baseline_proxy", 0.0),
        "mean_A_ref_local": float(np.mean(A_ref_trace)),
        "mean_A_sca_local": float(np.mean(A_sca_trace)),
        "mean_reference_to_scattering_amplitude_ratio": mean_reference_to_scattering_ratio,
        "reference_dominated_fraction": (
            reference_dominated_fraction
            if reference_dominated_fraction is not None
            else float(np.mean(A_ref_trace >= A_sca_trace))
        ),
        "transit_time_s": transit_time_s,
        "local_snr": local_snr,
        "initial_position_distribution_mode": position_diag.get(
            "initial_position_distribution_mode",
            "uniform",
        ),
        "initial_position_distribution_active": position_diag.get(
            "initial_position_distribution_active",
            False,
        ),
        "initial_position_x_norm": position_diag.get("initial_position_x_norm", 0.0),
        "initial_position_z_norm": position_diag.get("initial_position_z_norm", 0.0),
        "initial_position_confinement_ratio": position_diag.get(
            "initial_position_confinement_ratio",
            0.0,
        ),
        "initial_position_confinement_activation": position_diag.get(
            "initial_position_confinement_activation",
            0.0,
        ),
        "initial_position_center_bias_x_exponent": position_diag.get(
            "initial_position_center_bias_x_exponent",
            1.0,
        ),
        "initial_position_center_bias_z_exponent": position_diag.get(
            "initial_position_center_bias_z_exponent",
            1.0,
        ),
        "nodi_transit_bandwidth_Hz": readout.get("nodi_transit_bandwidth_Hz"),
        "nodi_transit_bandwidth_gain": readout.get("nodi_transit_bandwidth_gain"),
        "nodi_bandwidth_limited_fraction": readout.get("nodi_bandwidth_limited_fraction"),
        "interference_overlap_factor_abs": trace.get("interference_overlap_factor_abs"),
        "interference_overlap_factor_phase_rad": trace.get(
            "interference_overlap_factor_phase_rad"
        ),
        "illumination_projection_coupling_status": illumination.get(
            "illumination_projection_coupling_status"
        ),
        "reference_projection_coupling_status": reference.get(
            "reference_projection_coupling_status"
        ),
        "interference_projection_coupling_status": reference.get(
            "reference_projection_coupling_status"
        ),
        "rho_requested": reference.get("rho_requested", float(sim_cfg.rho)),
        "rho_physical_envelope_nominal": reference.get("rho_physical_envelope_nominal"),
        "rho_physical_envelope_status": reference.get("rho_physical_envelope_status"),
        "has_paired_pulse": paired_pulse_count > 0,
        "best_peak_paired": best_peak_paired,
        "path_opd_model": sca_trace.get("path_opd_model", sim_cfg.path_opd_model),
        "path_opd_reference_plane": sca_trace.get("path_opd_reference_plane", "unknown"),
        "path_opd_z_geometry_factor": sca_trace.get("path_opd_z_geometry_factor", 1.0),
        "path_opd_z_reference_mode": sca_trace.get("path_opd_z_reference_mode", "unknown"),
        "path_opd_default_model": sca_trace.get("path_opd_default_model", sim_cfg.path_opd_model),
        "path_opd_model_role": sca_trace.get("path_opd_model_role", "unknown"),
        "path_opd_default_frozen": sca_trace.get("path_opd_default_frozen", True),
        "path_opd_freeze_status": sca_trace.get("path_opd_freeze_status", "unknown"),
        "detection_decision_mode": sim_cfg.detection_decision_mode,
        "event_max_margin_z": event_max_margin_z,
        "background_max_margin_z": background_max_margin_z,
        "detector_route_id": str(getattr(sim_cfg, "detector_route_id", "A_hybrid")),
        "detector_route_status": route_trace.get("detector_route_status"),
        "self_route_scale_r_self": route_trace.get("r_self"),
        "self_collapsed_detector": route_trace.get("self_collapsed_detector"),
        "self_roi_detector": route_trace.get("self_roi_detector"),
    }
    if not retain_full_payload:
        return event_result

    reference_to_scattering_ratio = A_ref_trace / np.clip(A_sca_trace, 1e-15, None)
    event_result.update({
        "trajectory": trajectory,
        "signal_trace": np.asarray(route_trace["route_signal_trace"], dtype=float),
        "signal_trace_default_production": trace["signal_trace"],
        "interference_cross_term": trace.get("interference_cross_term"),
        "interference_cross_term_collapsed": trace.get("interference_cross_term_collapsed"),
        "interference_cross_term_joint": trace.get("interference_cross_term_joint"),
        "interference_cross_term_mode": trace.get("interference_cross_term_mode"),
        "interference_overlap_factor_abs": trace.get("interference_overlap_factor_abs"),
        "interference_overlap_factor_phase_rad": trace.get("interference_overlap_factor_phase_rad"),
        "interference_overlap_status": trace.get("interference_overlap_status"),
        "scattering_only_intensity": trace.get("scattering_only_intensity"),
        "signal_raw_noisy": noisy["signal_noisy"],
        "pulse_time_s": pulse_time_s,
        "signal_noisy": pulse_signal,
        "signal_pre_readout_noisy": noisy["signal_noisy"],
        "shot_noise": noisy.get("shot_noise"),
        "I_baseline": trace.get("I_baseline"),
        "I_baseline_trace": trace.get("I_baseline_trace"),
        "signal_detect_pre_post": readout["signal_detect"],
        "signal_nodi": post_readout_nodi["signal_post_readout"],
        "signal_pod": post_readout_pod["signal_post_readout"],
        "signal_nodi_pre_post": readout["signal_nodi"],
        "signal_pod_pre_post": readout["signal_pod"],
        "signal_nodi_true": readout["signal_nodi_true"],
        "signal_pod_true": readout["signal_pod_true"],
        "signal_nodi_leak": readout.get("signal_nodi_leak"),
        "signal_pod_leak": readout.get("signal_pod_leak"),
        "nodi_transit_response_model": readout.get("nodi_transit_response_model"),
        "nodi_transit_bandwidth_Hz": readout.get("nodi_transit_bandwidth_Hz"),
        "nodi_transit_bandwidth_gain": readout.get("nodi_transit_bandwidth_gain"),
        "nodi_bandwidth_limited_fraction": readout.get("nodi_bandwidth_limited_fraction"),
        "nodi_lockin_bandwidth_Hz": readout.get("nodi_lockin_bandwidth_Hz"),
        "post_readout_noise": post_readout["post_readout_noise"],
        "detector_route_id": str(getattr(sim_cfg, "detector_route_id", "A_hybrid")),
        "detector_route_status": route_trace.get("detector_route_status"),
        "self_route_scale_r_self": route_trace.get("r_self"),
        "self_collapsed_detector": route_trace.get("self_collapsed_detector"),
        "self_roi_detector": route_trace.get("self_roi_detector"),
        "A_ref_trace": reference_trace.get("A_ref_trace"),
        "A_sca_trace": sca_trace.get("A_sca"),
        "median_reference_to_scattering_amplitude_ratio": float(
            np.median(reference_to_scattering_ratio)
        ),
        "phi_ref_rad": reference_trace.get("phi_ref_trace_rad"),
        "reference_amplitude_scale": reference_trace.get("reference_amplitude_scale"),
        "reference_spatial_phase_rad": reference_trace.get("reference_spatial_phase_rad"),
        "reference_spatial_mode": reference_trace.get("reference_spatial_mode"),
        "reference_x_norm": reference_trace.get("reference_x_norm"),
        "reference_z_norm": reference_trace.get("reference_z_norm"),
        "phi_material_rad": sca_trace.get("phi_material_rad"),
        "phi_projection_rad": sca_trace.get("phi_projection_rad"),
        "phi_material_parallel_rad": sca_trace.get("phi_material_parallel_rad"),
        "phi_material_perpendicular_rad": sca_trace.get("phi_material_perpendicular_rad"),
        "phi_beam_rad": sca_trace.get("phi_beam_rad"),
        "phi_beam_gouy_rad": sca_trace.get("phi_beam_gouy_rad"),
        "phi_beam_curv_rad": sca_trace.get("phi_beam_curv_rad"),
        "phi_focus_crossing_rad": sca_trace.get("phi_focus_crossing_rad"),
        "phi_gouy_ref_rad": sca_trace.get("phi_gouy_ref_rad"),
        "phi_gouy_sca_rad": sca_trace.get("phi_gouy_sca_rad"),
        "delta_phi_gouy_rad": sca_trace.get("delta_phi_gouy_rad"),
        "gouy_dedup_active": sca_trace.get("gouy_dedup_active"),
        "phi_gouy_reference_status": sca_trace.get("phi_gouy_reference_status"),
        "phi_gouy_scattering_status": sca_trace.get("phi_gouy_scattering_status"),
        "phi_gouy_semantics_status": sca_trace.get("phi_gouy_semantics_status"),
        "phi_sca_path_x_rad": sca_trace.get("phi_sca_path_x_rad"),
        "phi_sca_path_z_rad": sca_trace.get("phi_sca_path_z_rad"),
        "phi_ref_trace_rad": sca_trace.get("phi_ref_rad"),
        "phi_sca_path_rad": sca_trace.get("phi_sca_path_rad"),
        "phi_extra_rad": sca_trace.get("phi_extra_rad"),
        "scattering_projection_basis": scattering_projection_basis,
        "illumination_projection_basis": illumination.get("illumination_projection_basis"),
        "illumination_effective_basis": illumination.get("illumination_effective_basis"),
        "illumination_projection_basis_match": illumination.get(
            "illumination_projection_basis_match"
        ),
        "illumination_projection_coupling_status": illumination.get(
            "illumination_projection_coupling_status"
        ),
        "reference_projection_basis": reference.get("reference_projection_basis"),
        "reference_effective_basis": reference.get("reference_effective_basis"),
        "reference_projection_basis_match": reference.get(
            "reference_projection_basis_match"
        ),
        "reference_projection_coupling_status": reference.get(
            "reference_projection_coupling_status"
        ),
        "interference_projection_basis": reference.get("reference_projection_basis"),
        "interference_projection_basis_match": reference.get(
            "reference_projection_basis_match"
        ),
        "interference_projection_coupling_status": reference.get(
            "reference_projection_coupling_status"
        ),
        "delta_phi_ref_rad": sca_trace.get("delta_phi_ref_rad"),
        "readout_model": sim_cfg.readout_model,
        "features_pod": features_pod,
        "pulse_pairing_tolerance_s": sim_cfg.pulse_pairing_tolerance_s,
        "paired_pulse_count": paired_pulse_count,
        "strict_paired_detected": detected_paired_channel,
        "initial_position": (x0, z0),
        "initial_position_center_bias_strength": position_diag.get(
            "initial_position_center_bias_strength",
            0.0,
        ),
        "initial_position_center_bias_min_confinement_ratio": position_diag.get(
            "initial_position_center_bias_min_confinement_ratio",
            0.0,
        ),
        "transport_channel_width_m": transport_channel.width_m,
        "transport_channel_depth_m": transport_channel.depth_m,
        "threshold_background_median": threshold_stats["median"],
        "pod_threshold": pod_threshold_stats["threshold"],
        "pod_threshold_background_median": pod_threshold_stats["median"],
        "pod_threshold_robust_std": pod_threshold_stats["robust_std"],
    })
    return event_result


def _vectorized_stream_event_block_supported(
    sim_cfg: SimulationConfig,
    *,
    retain_event_traces: bool,
    stream_summary_only: bool,
) -> tuple[bool, str | None]:
    """Return whether the configured block engine can run this batch path."""
    if sim_cfg.vectorized_event_engine == "off":
        return False, "disabled"
    if sim_cfg.vectorized_event_engine not in {
        "pure_advection_block",
        "event_block_v2",
        "event_block_v3",
    }:
        return False, f"unsupported_engine:{sim_cfg.vectorized_event_engine}"
    if retain_event_traces or not stream_summary_only:
        return False, "requires_stream_summary_without_event_traces"
    if sim_cfg.vectorized_event_engine == "pure_advection_block" and sim_cfg.include_diffusion:
        return False, "diffusion_enabled"
    if sim_cfg.post_readout_colored_noise_std > 0:
        return False, "colored_post_readout_noise_requires_event_loop"
    if (
        sim_cfg.vectorized_event_engine == "event_block_v3"
        and sim_cfg.detection_decision_mode != "single_channel"
    ):
        return False, "paired_channel_requires_event_loop"
    if (
        sim_cfg.vectorized_event_engine == "event_block_v3"
        and sim_cfg.pulse_width_measure_mode != "peak_width"
    ):
        return False, "duration_width_requires_event_loop"
    if (
        sim_cfg.vectorized_event_engine == "event_block_v3"
        and sim_cfg.adaptive_event_budget_mode != "fixed"
    ):
        return False, "adaptive_budget_requires_event_loop"
    return True, None


def _vectorized_event_rng_order_label(
    sim_cfg: SimulationConfig,
    vectorized_engine_used: str,
) -> str:
    """Return the summary metadata label for a block event RNG route."""
    if sim_cfg.event_block_rng_order == "block_lane_order":
        return (
            "block_lane_order_vectorized_summary"
            if vectorized_engine_used == "event_block_v3"
            else "block_lane_order_blocked_summary"
        )
    if sim_cfg.event_sampling_policy != "random":
        return (
            "event_loop_order_blocked_vectorized_summary"
            if vectorized_engine_used == "event_block_v3"
            else "event_loop_order_blocked_summary"
        )
    return (
        "block_position_order_event_noise_order_vectorized_summary"
        if vectorized_engine_used == "event_block_v3"
        else "block_position_order_event_noise_order"
    )


def _mean_trace_by_event(
    value: object,
    *,
    block_size: int,
    default: float = 0.0,
) -> np.ndarray:
    """Return one mean value per event from a block-shaped trace payload."""
    if value is None:
        return np.full(block_size, float(default), dtype=float)
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 0:
        return np.full(block_size, float(arr), dtype=float)
    if arr.shape[0] != block_size:
        return np.full(block_size, float(np.mean(arr)), dtype=float)
    if arr.ndim == 1:
        return arr.astype(float, copy=False)
    return np.mean(arr.reshape(block_size, -1), axis=1)


def _event_diag_value(value: object, event_offset: int, default: float) -> float:
    """Return a scalar diagnostic from either scalar or per-event payloads."""
    if value is None:
        return float(default)
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 0:
        return float(arr)
    if arr.shape[0] <= event_offset:
        return float(default)
    return float(arr[event_offset])


def _estimate_threshold_stats_block(
    signals: np.ndarray,
    sigma_multiplier: float,
) -> dict[str, np.ndarray]:
    """Estimate robust threshold statistics row-wise for a block of traces."""
    signal_arr = np.asarray(signals, dtype=float)
    if signal_arr.ndim == 1:
        signal_arr = signal_arr[np.newaxis, :]
    n_cols = int(signal_arr.shape[1])
    if n_cols <= 0:
        med = np.zeros(signal_arr.shape[0], dtype=float)
        mad = np.zeros(signal_arr.shape[0], dtype=float)
    else:
        k_lo = (n_cols - 1) // 2
        k_hi = n_cols // 2
        kth = (k_lo, k_hi) if k_lo != k_hi else k_lo
        partitioned = np.partition(signal_arr, kth, axis=1)
        med = 0.5 * (partitioned[:, k_lo] + partitioned[:, k_hi])
        deviations = np.abs(signal_arr - med[:, np.newaxis])
        mad_partitioned = np.partition(deviations, kth, axis=1)
        mad = 0.5 * (mad_partitioned[:, k_lo] + mad_partitioned[:, k_hi])
    robust_std = 1.4826 * mad
    threshold = med + float(sigma_multiplier) * robust_std
    return {
        "median": med.astype(float, copy=False),
        "mad": mad.astype(float, copy=False),
        "robust_std": robust_std.astype(float, copy=False),
        "threshold": threshold.astype(float, copy=False),
    }


def _pulse_extraction_time_grid(
    time_s: np.ndarray,
    sim_cfg: SimulationConfig,
) -> tuple[np.ndarray, dict[str, object]]:
    """Return the time grid used for thresholding and pulse extraction."""
    time_arr = np.asarray(time_s, dtype=float)
    interval = getattr(sim_cfg, "pulse_extraction_sampling_interval_s", None)
    if interval is None or float(interval) <= 0.0 or time_arr.size < 2:
        return time_arr, {
            "pulse_extraction_sampling_status": "internal_simulation_grid",
            "pulse_extraction_sampling_interval_s": None,
            "pulse_extraction_sample_count": int(time_arr.size),
            "pulse_extraction_downsample_factor": 1.0,
        }

    dt = float(time_arr[1] - time_arr[0])
    interval_f = float(interval)
    if interval_f <= dt * 1.000001:
        return time_arr, {
            "pulse_extraction_sampling_status": "requested_interval_not_coarser_than_internal_grid",
            "pulse_extraction_sampling_interval_s": interval_f,
            "pulse_extraction_sample_count": int(time_arr.size),
            "pulse_extraction_downsample_factor": 1.0,
        }

    duration = float(time_arr[-1] - time_arr[0])
    n_samples = int(math.floor(duration / interval_f + 1.0e-12)) + 1
    if n_samples < 2:
        return time_arr, {
            "pulse_extraction_sampling_status": "requested_interval_too_sparse_for_trace",
            "pulse_extraction_sampling_interval_s": interval_f,
            "pulse_extraction_sample_count": int(time_arr.size),
            "pulse_extraction_downsample_factor": 1.0,
        }
    sampled_time = time_arr[0] + interval_f * np.arange(n_samples, dtype=float)
    sampled_time = np.clip(sampled_time, time_arr[0], time_arr[-1])
    return sampled_time, {
        "pulse_extraction_sampling_status": "data_logger_resampled",
        "pulse_extraction_sampling_interval_s": interval_f,
        "pulse_extraction_sample_count": int(sampled_time.size),
        "pulse_extraction_downsample_factor": float(interval_f / dt),
    }


def _resample_trace_to_time_grid(
    source_time_s: np.ndarray,
    trace: np.ndarray,
    target_time_s: np.ndarray,
) -> np.ndarray:
    """Resample one trace or a block of traces to the pulse-extraction grid."""
    source_time = np.asarray(source_time_s, dtype=float)
    target_time = np.asarray(target_time_s, dtype=float)
    trace_arr = np.asarray(trace, dtype=float)
    if (
        source_time.shape == target_time.shape
        and np.allclose(source_time, target_time, rtol=0.0, atol=1.0e-15)
    ):
        return trace_arr
    if trace_arr.ndim == 1:
        return np.interp(target_time, source_time, trace_arr).astype(float, copy=False)
    return np.vstack(
        [np.interp(target_time, source_time, row) for row in trace_arr]
    ).astype(float, copy=False)


def _resample_traces_for_pulse_extraction(
    time_s: np.ndarray,
    traces: tuple[np.ndarray, ...],
    sim_cfg: SimulationConfig,
) -> tuple[np.ndarray, tuple[np.ndarray, ...], dict[str, object]]:
    """Apply optional data-logger resampling to all pulse-extraction traces."""
    extraction_time_s, diagnostics = _pulse_extraction_time_grid(time_s, sim_cfg)
    if diagnostics["pulse_extraction_sampling_status"] != "data_logger_resampled":
        return extraction_time_s, traces, diagnostics
    return (
        extraction_time_s,
        tuple(
            _resample_trace_to_time_grid(time_s, trace, extraction_time_s)
            for trace in traces
        ),
        diagnostics,
    )


def _threshold_background_segments(
    signals: np.ndarray,
    sim_cfg: SimulationConfig,
) -> tuple[np.ndarray, int, str]:
    """Return the runtime background samples used to estimate thresholds."""
    signal_arr = np.asarray(signals, dtype=float)
    was_1d = signal_arr.ndim == 1
    if was_1d:
        signal_arr = signal_arr[np.newaxis, :]
    n_cols = int(signal_arr.shape[1])
    n_edge = max(1, int(0.2 * n_cols))
    source = str(sim_cfg.threshold_calibration_source)
    if source in {"blank_trace_empirical", "block_bootstrap"} and n_cols >= 2 * n_edge:
        background = np.concatenate(
            (signal_arr[:, :n_edge], signal_arr[:, -n_edge:]),
            axis=1,
        )
        source_label = "synthetic_event_edge_background_surrogate"
    else:
        background = signal_arr[:, :n_edge]
        source_label = "synthetic_event_initial_background_segment"
    if was_1d:
        return background[0], int(background.shape[1]), source_label
    return background, int(background.shape[1]), source_label


def _estimate_runtime_threshold_stats_1d(
    signal: np.ndarray,
    sim_cfg: SimulationConfig,
) -> tuple[dict, int, str]:
    """Estimate one event threshold according to the configured source surrogate."""
    background, n_background, source = _threshold_background_segments(signal, sim_cfg)
    return (
        estimate_threshold_stats_robust(background, sim_cfg.threshold_sigma),
        n_background,
        source,
    )


def _estimate_runtime_threshold_stats_block(
    signals: np.ndarray,
    sim_cfg: SimulationConfig,
) -> tuple[dict[str, np.ndarray], int, str]:
    """Estimate block thresholds according to the configured source surrogate."""
    background, n_background, source = _threshold_background_segments(signals, sim_cfg)
    return (
        _estimate_threshold_stats_block(background, sim_cfg.threshold_sigma),
        n_background,
        source,
    )


def _route_trace_payload(
    trace: dict,
    *,
    sim_cfg: SimulationConfig,
    E_sca_unit_normalized: complex | float,
    reference: dict,
) -> dict[str, object]:
    """Assemble the route-specific signed trace before noise/readout."""
    route_id = str(getattr(sim_cfg, "detector_route_id", "A_hybrid"))
    if route_id == "A_hybrid":
        return {
            "route_signal_trace": np.asarray(trace["signal_trace"], dtype=float),
            "route_detected_intensity": np.asarray(trace.get("I_det"), dtype=float),
            "r_self": compute_r_self(reference, E_sca_unit_normalized),
            "self_collapsed_detector": float(abs(complex(E_sca_unit_normalized)) ** 2),
            "self_roi_detector": reference.get("self_sca_detector_integrated"),
            "detector_route_status": "production_hybrid_default",
        }
    r_self = compute_r_self(reference, E_sca_unit_normalized)
    payload = assemble_route_trace_payload(
        trace,
        route=route_id,
        r_self=r_self,
        background_subtraction_on=bool(sim_cfg.background_subtraction_on),
        interference_overlap_mode=str(sim_cfg.interference_overlap_mode),
    )
    payload.update(
        {
            "r_self": r_self,
            "self_collapsed_detector": float(abs(complex(E_sca_unit_normalized)) ** 2),
            "self_roi_detector": reference.get("self_sca_detector_integrated"),
            "detector_route_status": "route_assembled_from_full_diagnostics",
        }
    )
    return payload


def _extract_best_peak_summary_block(
    time_s: np.ndarray,
    signal_block: np.ndarray,
    thresholds: np.ndarray,
    *,
    pulse_context: PulseExtractionContext,
    detection_mode: str,
    signal_eval_block: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Extract one best peak per event using block-level array operations."""
    time_arr = np.asarray(time_s, dtype=float)
    signal_arr = np.asarray(signal_block, dtype=float)
    if signal_arr.ndim == 1:
        signal_arr = signal_arr[np.newaxis, :]
    block_size, n_samples = signal_arr.shape
    threshold_arr = np.asarray(thresholds, dtype=float).reshape(block_size)
    empty = {
        "detected": np.zeros(block_size, dtype=bool),
        "peak_heights": np.zeros(block_size, dtype=float),
        "peak_signed_heights": np.zeros(block_size, dtype=float),
        "peak_widths_s": np.zeros(block_size, dtype=float),
        "peak_times_s": np.zeros(block_size, dtype=float),
    }
    if n_samples < 3:
        return empty

    if signal_eval_block is None:
        if detection_mode == "positive":
            signal_eval = signal_arr
        elif detection_mode == "absolute":
            signal_eval = np.abs(signal_arr)
        else:
            raise ValueError(
                f"detection_mode must be 'positive' or 'absolute', got {detection_mode}"
            )
    else:
        signal_eval = np.asarray(signal_eval_block, dtype=float)
        if signal_eval.shape != signal_arr.shape:
            raise ValueError(
                "signal_eval_block must have the same shape as signal_block"
            )

    if _numba_njit is not None:
        (
            detected,
            peak_heights,
            peak_signed_heights,
            peak_widths_s,
            peak_times_s,
        ) = _extract_best_peak_summary_2d_kernel(
            time_arr,
            signal_arr,
            signal_eval,
            threshold_arr,
            int(pulse_context.min_width_samples),
            float(pulse_context.dt_s),
        )
        return {
            "detected": detected.astype(bool, copy=False),
            "peak_heights": peak_heights.astype(float, copy=False),
            "peak_signed_heights": peak_signed_heights.astype(float, copy=False),
            "peak_widths_s": peak_widths_s.astype(float, copy=False),
            "peak_times_s": peak_times_s.astype(float, copy=False),
        }

    inner = signal_eval[:, 1:-1]
    local_max = (
        (inner > signal_eval[:, :-2])
        & (inner >= signal_eval[:, 2:])
        & (inner >= threshold_arr[:, np.newaxis])
    )
    candidate_values = np.where(local_max, inner, -np.inf)
    best_inner = np.argmax(candidate_values, axis=1)
    best_values = candidate_values[np.arange(block_size), best_inner]
    has_candidate = np.isfinite(best_values)
    if not bool(np.any(has_candidate)):
        return empty

    best_idx = best_inner + 1
    best_values_safe = np.where(has_candidate, best_values, 0.0)
    rows = np.arange(block_size)
    cols = np.arange(n_samples)
    left_mask = cols[np.newaxis, :] <= best_idx[:, np.newaxis]
    right_mask = cols[np.newaxis, :] >= best_idx[:, np.newaxis]
    left_min = np.min(np.where(left_mask, signal_eval, np.inf), axis=1)
    right_min = np.min(np.where(right_mask, signal_eval, np.inf), axis=1)
    prominence_base = np.maximum(left_min, right_min)
    width_level = best_values_safe - 0.5 * (best_values_safe - prominence_base)

    above_width = signal_eval >= width_level[:, np.newaxis]
    left_false = np.max(
        np.where(
            (cols[np.newaxis, :] < best_idx[:, np.newaxis]) & ~above_width,
            cols[np.newaxis, :],
            -1,
        ),
        axis=1,
    )
    right_false = np.min(
        np.where(
            (cols[np.newaxis, :] > best_idx[:, np.newaxis]) & ~above_width,
            cols[np.newaxis, :],
            n_samples,
        ),
        axis=1,
    )

    left_has = left_false >= 0
    left_base = np.where(left_has, left_false, 0)
    left_next = np.minimum(left_base + 1, n_samples - 1)
    left_y0 = signal_eval[rows, left_base]
    left_y1 = signal_eval[rows, left_next]
    left_denom = left_y1 - left_y0
    left_frac = np.divide(
        width_level - left_y0,
        left_denom,
        out=np.zeros(block_size, dtype=float),
        where=np.abs(left_denom) > 1e-15,
    )
    left_ip = np.where(
        left_has,
        left_base.astype(float) + np.clip(left_frac, 0.0, 1.0),
        0.0,
    )

    right_has = right_false < n_samples
    right_prev = np.maximum(right_false - 1, 0)
    right_base = np.where(right_has, right_false, n_samples - 1)
    right_y0 = signal_eval[rows, right_prev]
    right_y1 = signal_eval[rows, right_base]
    right_denom = right_y1 - right_y0
    right_frac = np.divide(
        width_level - right_y0,
        right_denom,
        out=np.zeros(block_size, dtype=float),
        where=np.abs(right_denom) > 1e-15,
    )
    right_ip = np.where(
        right_has,
        right_prev.astype(float) + np.clip(right_frac, 0.0, 1.0),
        float(n_samples - 1),
    )

    width_samples = np.maximum(right_ip - left_ip, 0.0)
    detected = has_candidate & (
        width_samples >= float(pulse_context.min_width_samples)
    )
    peak_heights = np.where(detected, best_values_safe, 0.0)
    peak_signed_heights = np.where(detected, signal_arr[rows, best_idx], 0.0)
    peak_widths_s = np.where(detected, width_samples * float(pulse_context.dt_s), 0.0)
    peak_times_s = np.where(detected, time_arr[best_idx], 0.0)
    return {
        "detected": detected.astype(bool, copy=False),
        "peak_heights": peak_heights.astype(float, copy=False),
        "peak_signed_heights": peak_signed_heights.astype(float, copy=False),
        "peak_widths_s": peak_widths_s.astype(float, copy=False),
        "peak_times_s": peak_times_s.astype(float, copy=False),
    }


def _replace_peak_summary_detected_mask(
    peak_summary: dict[str, np.ndarray],
    detected: np.ndarray,
) -> dict[str, np.ndarray]:
    """Reuse peak attributes while replacing the event-level decision mask."""
    return {
        **peak_summary,
        "detected": np.asarray(detected, dtype=bool),
    }


def _empty_pulse_features(
    threshold: float,
    detection_mode: str,
    width_measure_mode: str = "peak_width",
    duration_estimation_policy: str = "interpolated_threshold_crossing",
) -> dict[str, object]:
    """Return the canonical no-peak feature payload."""
    return {
        "n_peaks": 0,
        "peaks": [],
        "threshold_used": threshold,
        "detection_mode": detection_mode,
        "width_measure_mode": width_measure_mode,
        "duration_estimation_policy": duration_estimation_policy,
    }


def _sample_initial_positions_block(
    channel: Channel,
    rng: np.random.Generator,
    particle_radius_m: float,
    sim_cfg: SimulationConfig | None,
    unit_position_samples: np.ndarray | None,
    start_idx: int,
    stop_idx: int,
) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """Sample event initial positions in a block for non-rejection samplers."""
    block_size = max(0, int(stop_idx) - int(start_idx))
    if block_size <= 0:
        return np.empty(0, dtype=float), np.empty(0, dtype=float), []

    mode = (
        str(sim_cfg.initial_position_distribution_mode)
        if sim_cfg is not None
        else "uniform"
    )
    uses_geometry_or_rejection_sampler = mode in {
        "flux_weighted",
        "flux_uniform_mixture_surrogate",
    } or (
        sim_cfg is not None
        and str(sim_cfg.channel_cross_section_model) == "trapezoid_tapered_sidewalls"
    )
    if uses_geometry_or_rejection_sampler:
        x_vals = np.empty(block_size, dtype=float)
        z_vals = np.empty(block_size, dtype=float)
        diagnostics: list[dict] = []
        for offset, event_idx in enumerate(range(start_idx, stop_idx)):
            unit_position_sample = (
                tuple(float(x) for x in unit_position_samples[event_idx])
                if unit_position_samples is not None
                else None
            )
            x_val, z_val, position_diag = sample_initial_position(
                channel,
                rng,
                particle_radius_m,
                sim_cfg=sim_cfg,
                unit_position_sample=unit_position_sample,
            )
            x_vals[offset] = float(x_val)
            z_vals[offset] = float(z_val)
            diagnostics.append(position_diag)
        return x_vals, z_vals, diagnostics

    half_w = channel.width_m / 2.0 - particle_radius_m
    half_h = channel.depth_m / 2.0 - particle_radius_m
    if half_w <= 0 or half_h <= 0:
        raise ValueError(
            "particle_radius_m is too large for the channel cross-section: "
            f"radius={particle_radius_m:.2e}m, width={channel.width_m:.2e}m, "
            f"depth={channel.depth_m:.2e}m"
        )

    if sim_cfg is None:
        strength = 0.0
        min_conf_ratio = 0.0
        flux_mixture_fraction = 0.0
    else:
        strength = float(sim_cfg.initial_position_center_bias_strength)
        min_conf_ratio = float(
            sim_cfg.initial_position_center_bias_min_confinement_ratio
        )
        flux_mixture_fraction = float(
            sim_cfg.initial_position_flux_weighted_mixture_fraction
        )

    if unit_position_samples is None:
        unit_xy = rng.uniform(0.0, 1.0, size=(block_size, 2))
        unit_sample_supplied = False
    else:
        unit_rows = np.asarray(unit_position_samples[start_idx:stop_idx], dtype=float)
        if unit_rows.shape != (block_size, 3):
            raise ValueError("unit_position_sample must contain exactly three values")
        unit_xy = np.clip(unit_rows[:, :2], 0.0, np.nextafter(1.0, 0.0))
        unit_sample_supplied = True

    min_half_extent = max(min(half_w, half_h), 1e-18)
    confinement_ratio = float(np.clip(particle_radius_m / min_half_extent, 0.0, 1.0))
    confinement_activation = float(
        np.clip(
            (confinement_ratio - min_conf_ratio) / max(0.25 - min_conf_ratio, 1e-12),
            0.0,
            1.0,
        )
    )
    aspect_depth_focus = float(
        np.clip(channel.width_m / max(channel.depth_m, 1e-18), 1.0, 4.0)
    )
    active = (
        mode == "center_biased_surrogate"
        and strength > 0
        and confinement_activation > 0
    )
    if active:
        x_exponent = float(1.0 + 0.6 * strength * confinement_activation)
        z_exponent = float(
            1.0 + 1.2 * strength * confinement_activation * np.sqrt(aspect_depth_focus)
        )
        unit_centered = -1.0 + 2.0 * unit_xy
        x_vals = half_w * np.sign(unit_centered[:, 0]) * (
            np.abs(unit_centered[:, 0]) ** x_exponent
        )
        z_vals = half_h * np.sign(unit_centered[:, 1]) * (
            np.abs(unit_centered[:, 1]) ** z_exponent
        )
        cross_section_event_bias_status = "center_biased_surrogate_active"
    else:
        x_exponent = 1.0
        z_exponent = 1.0
        x_vals = -half_w + 2.0 * half_w * unit_xy[:, 0]
        z_vals = -half_h + 2.0 * half_h * unit_xy[:, 1]
        if mode == "uniform_accessible_area":
            cross_section_event_bias_status = (
                "uniform_over_accessible_particle_center_area"
            )
        elif mode == "center_biased_surrogate":
            cross_section_event_bias_status = "center_biased_surrogate_inactive"
        else:
            cross_section_event_bias_status = (
                "legacy_uniform_over_accessible_particle_center_area"
            )

    diagnostics = [
        {
            "initial_position_distribution_mode": mode,
            "initial_position_distribution_active": bool(active),
            "initial_position_unit_sample_supplied": unit_sample_supplied,
            "cross_section_event_bias_status": cross_section_event_bias_status,
            "flux_weighted_sampling_acceptance_rate": 1.0,
            "flux_weighted_sampling_attempts": 1,
            "initial_position_center_bias_strength": strength,
            "initial_position_center_bias_min_confinement_ratio": min_conf_ratio,
            "initial_position_flux_weighted_mixture_fraction": flux_mixture_fraction,
            "initial_position_mixture_component": "not_applicable",
            "initial_position_confinement_ratio": confinement_ratio,
            "initial_position_confinement_activation": confinement_activation,
            "initial_position_center_bias_x_exponent": x_exponent,
            "initial_position_center_bias_z_exponent": z_exponent,
            "initial_position_x_norm": float(x_val / max(half_w, 1e-18)),
            "initial_position_z_norm": float(z_val / max(half_h, 1e-18)),
        }
        for x_val, z_val in zip(x_vals, z_vals)
    ]
    return (
        np.asarray(x_vals, dtype=float),
        np.asarray(z_vals, dtype=float),
        diagnostics,
    )


def _simulate_stream_event_block(
    *,
    particle: Particle,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    E_sca_unit_normalized: complex | float,
    reference: dict,
    theta_det_rad: float,
    rng: np.random.Generator,
    vectorized_engine: str,
    diffusion_coefficient: float | None,
    start_idx: int,
    stop_idx: int,
    unit_position_samples: np.ndarray | None,
    medium_refractive_index: float,
    readout_context: _ReadoutContext | None,
    trajectory_context: TrajectoryContext,
    event_case_context: _EventCaseContext,
    summary_accumulator: _BatchSummaryAccumulator,
    adaptive_accumulator: _BatchSummaryAccumulator | None,
    event_block_random_state: _EventBlockRandomState | None = None,
) -> tuple[int, bool, str, dict[str, object]]:
    """Simulate and accumulate one stream-summary event block."""
    block_size = max(0, int(stop_idx) - int(start_idx))
    if block_size <= 0:
        return 0, False, "empty_block", {}

    transport_channel = event_case_context.transport_channel
    transport_cfg = event_case_context.transport_cfg
    x0, z0, position_diags = _sample_initial_positions_block(
        transport_channel,
        rng,
        particle.radius_m,
        transport_cfg,
        unit_position_samples,
        start_idx,
        stop_idx,
    )

    time_s = trajectory_context.time_s
    block_randoms = None
    if vectorized_engine in {"event_block_v2", "event_block_v3"}:
        if sim_cfg.event_block_rng_order == "block_lane_order":
            if event_block_random_state is None:
                raise RuntimeError(
                    "block_lane_order requires an event block random state"
                )
            block_randoms = _draw_block_lane_order_block_randoms(
                random_state=event_block_random_state,
                block_size=block_size,
                n_samples=int(time_s.size),
                sim_cfg=sim_cfg,
                include_diffusion=bool(transport_cfg.include_diffusion),
            )
        else:
            block_randoms = _draw_event_loop_order_block_randoms(
                rng=rng,
                block_size=block_size,
                n_samples=int(time_s.size),
                sim_cfg=sim_cfg,
                include_diffusion=bool(transport_cfg.include_diffusion),
            )
    trajectory = simulate_particle_trajectory_block(
        transport_channel,
        optical,
        transport_cfg,
        x0,
        z0,
        particle_radius_m=particle.radius_m,
        diffusion_coefficient=diffusion_coefficient,
        rng=rng,
        diffusion_draws=(
            None
            if block_randoms is None
            else block_randoms["diffusion_draws"]
        ),
        trajectory_context=trajectory_context,
        export_velocity_trace=False,
    )

    illumination = compute_illumination_envelope(
        trajectory["x_m"],
        trajectory["y_m"],
        trajectory["z_m"],
        optical,
        medium_refractive_index=medium_refractive_index,
        sim_cfg=sim_cfg,
        export_full_diagnostics=False,
    )
    A_env_scalar = np.asarray(illumination["A_env_scalar"], dtype=float)
    transit_times = _estimate_transit_time_block(time_s, A_env_scalar)
    reference_trace = compute_reference_field_trace(
        trajectory,
        reference,
        channel,
        optical,
        sim_cfg,
        initial_x_m=float(x0[0]),
        initial_z_m=float(z0[0]),
        export_full_diagnostics=False,
    )
    sca_trace = compute_scattering_field_trace(
        trajectory,
        E_sca_unit_normalized,
        optical,
        illumination,
        transport_channel,
        float(x0[0]),
        float(z0[0]),
        sim_cfg.phase_model,
        coupling_model=transport_cfg.coupling_model,
        path_opd_model=sim_cfg.path_opd_model,
        detection_theta_rad=theta_det_rad,
        medium_refractive_index=medium_refractive_index,
        reference_phase_rad=reference_trace["phi_ref_trace_rad"],
        scattering_phase_diagnostics=None,
        include_phase_diagnostics=False,
        export_complex_field=False,
        reuse_illumination_gouy_phase=True,
    )
    trace = generate_interferometric_trace(
        trajectory,
        {**reference, **reference_trace},
        sca_trace,
        sim_cfg,
        export_full_diagnostics=False,
    )
    baseline_trace_payload = trace.get("I_baseline_trace", trace.get("I_baseline"))
    baseline_by_event = _mean_trace_by_event(
        baseline_trace_payload,
        block_size=block_size,
    )
    baseline_intensity_for_noise = (
        baseline_by_event[:, np.newaxis]
        if block_randoms is not None and sim_cfg.shot_noise_scale > 0
        else (
            baseline_trace_payload
            if block_randoms is None and sim_cfg.shot_noise_scale > 0
            else None
        )
    )
    if block_randoms is None:
        noisy = add_detector_noise(
            trace["signal_trace"],
            time_s,
            sim_cfg,
            rng,
            detected_intensity=trace.get("I_det"),
            baseline_intensity=baseline_intensity_for_noise,
        )
    else:
        noisy = _add_detector_noise_block_from_draws(
            trace["signal_trace"],
            time_s,
            sim_cfg,
            detector_noise=block_randoms["detector_noise"],
            shot_standard=block_randoms["shot_standard"],
            detected_intensity=trace.get("I_det"),
            baseline_intensity=baseline_intensity_for_noise,
        )
    readout = apply_readout_chain(
        noisy["signal_noisy"],
        time_s,
        sim_cfg,
        transit_time_s=transit_times,
        readout_context=readout_context,
        export_full_diagnostics=False,
    )

    if (
        sim_cfg.post_readout_noise_std <= 0
        and sim_cfg.post_readout_colored_noise_std <= 0
        and sim_cfg.post_readout_drift_slope == 0
    ):
        post_signal = np.asarray(readout["signal_detect"], dtype=float)
        post_pod_signal = np.asarray(readout["signal_pod"], dtype=float)
    else:
        if block_randoms is None:
            post_readout = add_post_readout_noise(
                readout["signal_detect"],
                time_s,
                sim_cfg,
                rng,
            )
            _advance_post_readout_noise_rng(
                np.asarray(readout["signal_nodi"]).shape,
                sim_cfg,
                rng,
                time_s=time_s,
            )
            post_readout_pod = add_post_readout_noise(
                readout["signal_pod"],
                time_s,
                sim_cfg,
                rng,
            )
        else:
            post_readout = _add_post_readout_noise_from_draws(
                readout["signal_detect"],
                time_s,
                sim_cfg,
                block_randoms["post_detect_noise"],
            )
            post_readout_pod = _add_post_readout_noise_from_draws(
                readout["signal_pod"],
                time_s,
                sim_cfg,
                block_randoms["post_pod_noise"],
            )
        post_signal = np.asarray(post_readout["signal_post_readout"], dtype=float)
        post_pod_signal = np.asarray(
            post_readout_pod["signal_post_readout"],
            dtype=float,
        )

    readout_signal_detect = np.asarray(readout["signal_detect"], dtype=float)
    pulse_time_s, pulse_traces, pulse_sampling_diag = (
        _resample_traces_for_pulse_extraction(
            time_s,
            (
                post_signal,
                post_pod_signal,
            ),
            sim_cfg,
        )
    )
    post_signal = pulse_traces[0]
    post_pod_signal = pulse_traces[1]
    pulse_context_active = build_pulse_extraction_context(
        pulse_time_s,
        sim_cfg.min_peak_width_s,
        sim_cfg.min_peak_interval_s,
    )
    A_ref_trace = np.asarray(reference_trace["A_ref_trace"], dtype=float)
    A_sca_trace = np.asarray(sca_trace["A_sca"], dtype=float)
    shot_std_by_event = _mean_trace_by_event(
        noisy.get("shot_noise_std_trace"),
        block_size=block_size,
    )
    shot_ref_dominated_by_event = _mean_trace_by_event(
        noisy.get("shot_noise_reference_dominated_mask"),
        block_size=block_size,
    )
    shot_intensity_by_event = _mean_trace_by_event(
        noisy.get("shot_noise_intensity_proxy_trace"),
        block_size=block_size,
    )
    shot_baseline_by_event = _mean_trace_by_event(
        noisy.get("shot_noise_baseline_proxy_trace"),
        block_size=block_size,
    )

    processed = 0
    stopped = False
    adaptive_stop_reason = "fixed_event_budget"
    adaptive_state: dict[str, object] = {}
    threshold_stats_block, n_bg, threshold_background_source_runtime = (
        _estimate_runtime_threshold_stats_block(
            post_signal,
            sim_cfg,
        )
    )
    pod_threshold_stats_block, pod_n_bg, pod_threshold_background_source_runtime = (
        _estimate_runtime_threshold_stats_block(
            post_pod_signal,
            sim_cfg,
        )
    )
    _ = (
        pod_n_bg,
        pulse_sampling_diag,
        threshold_background_source_runtime,
        pod_threshold_background_source_runtime,
    )
    thresholds = threshold_stats_block["threshold"]
    threshold_robust_stds = threshold_stats_block["robust_std"]
    threshold_robust_stds_safe = np.maximum(threshold_robust_stds, 1e-15)
    pod_thresholds = pod_threshold_stats_block["threshold"]
    pod_threshold_robust_stds = pod_threshold_stats_block["robust_std"]
    mean_reference_to_scattering_ratios = np.mean(
        A_ref_trace / np.clip(A_sca_trace, 1e-15, None),
        axis=1,
    )
    signal_eval_block = (
        np.abs(post_signal)
        if sim_cfg.pulse_detection_mode == "absolute"
        else post_signal
    )
    pod_signal_eval_block = (
        np.abs(post_pod_signal)
        if sim_cfg.pulse_detection_mode == "absolute"
        else post_pod_signal
    )
    if signal_eval_block.shape[-1] > 0:
        nodi_signal_max = np.max(signal_eval_block, axis=1)
        pod_signal_max = np.max(pod_signal_eval_block, axis=1)
        if (
            sim_cfg.pulse_detection_mode == "absolute"
            and post_signal is readout_signal_detect
        ):
            local_snrs = nodi_signal_max / threshold_robust_stds_safe
        else:
            local_snrs = (
                np.max(np.abs(readout_signal_detect), axis=1)
                / threshold_robust_stds_safe
            )
        nodi_peak_candidate_mask = ~(nodi_signal_max < thresholds)
        pod_peak_candidate_mask = ~(pod_signal_max < pod_thresholds)
        event_max_margin_z_by_event = (
            nodi_signal_max - thresholds
        ) / threshold_robust_stds_safe
        background_eval_block, _, _ = _threshold_background_segments(
            signal_eval_block,
            sim_cfg,
        )
        background_max_margin_z_by_event = (
            np.max(background_eval_block, axis=1) - thresholds
        ) / threshold_robust_stds_safe
    else:
        nodi_peak_candidate_mask = np.zeros(block_size, dtype=bool)
        pod_peak_candidate_mask = np.zeros(block_size, dtype=bool)
        local_snrs = np.zeros(block_size, dtype=float)
        event_max_margin_z_by_event = -thresholds / threshold_robust_stds_safe
        background_max_margin_z_by_event = event_max_margin_z_by_event
    reference_projection_status = reference.get("reference_projection_coupling_status")
    illumination_status = illumination.get("illumination_projection_coupling_status")
    trace_diag = {
        "interference_overlap_factor_abs": trace.get("interference_overlap_factor_abs"),
        "interference_overlap_factor_phase_rad": trace.get(
            "interference_overlap_factor_phase_rad"
        ),
    }
    sca_trace_diag = {
        "path_opd_model": sca_trace.get("path_opd_model", sim_cfg.path_opd_model),
        "path_opd_reference_plane": sca_trace.get(
            "path_opd_reference_plane",
            "unknown",
        ),
        "path_opd_z_geometry_factor": sca_trace.get(
            "path_opd_z_geometry_factor",
            1.0,
        ),
        "path_opd_z_reference_mode": sca_trace.get(
            "path_opd_z_reference_mode",
            "unknown",
        ),
        "path_opd_default_model": sca_trace.get(
            "path_opd_default_model",
            sim_cfg.path_opd_model,
        ),
        "path_opd_model_role": sca_trace.get("path_opd_model_role", "unknown"),
        "path_opd_default_frozen": sca_trace.get("path_opd_default_frozen", True),
        "path_opd_freeze_status": sca_trace.get("path_opd_freeze_status", "unknown"),
    }

    if vectorized_engine == "event_block_v3":
        nodi_peak_summary = _extract_best_peak_summary_block(
            pulse_time_s,
            post_signal,
            thresholds,
            pulse_context=pulse_context_active,
            detection_mode=sim_cfg.pulse_detection_mode,
            signal_eval_block=signal_eval_block,
        )
        pod_peak_summary = _extract_best_peak_summary_block(
            pulse_time_s,
            post_pod_signal,
            pod_thresholds,
            pulse_context=pulse_context_active,
            detection_mode=sim_cfg.pulse_detection_mode,
            signal_eval_block=pod_signal_eval_block,
        )
        paired_mask = (
            np.asarray(nodi_peak_summary["detected"], dtype=bool)
            & np.asarray(pod_peak_summary["detected"], dtype=bool)
            & (
                np.abs(
                    np.asarray(nodi_peak_summary["peak_times_s"], dtype=float)
                    - np.asarray(pod_peak_summary["peak_times_s"], dtype=float)
                )
                <= float(sim_cfg.pulse_pairing_tolerance_s)
            )
        )
        paired_peak_summary = _replace_peak_summary_detected_mask(
            nodi_peak_summary,
            paired_mask,
        )
        final_peak_summary = (
            paired_peak_summary
            if sim_cfg.detection_decision_mode == "paired_channel"
            else nodi_peak_summary
        )
        summary_accumulator.update_from_simulation_block(
            final_peak_summary=final_peak_summary,
            single_peak_summary=nodi_peak_summary,
            paired_peak_summary=paired_peak_summary,
            thresholds=thresholds,
            threshold_robust_stds=threshold_robust_stds,
            pod_thresholds=pod_thresholds,
            pod_threshold_robust_stds=pod_threshold_robust_stds,
            threshold_background_segment_samples=n_bg,
            baseline_by_event=baseline_by_event,
            shot_std_by_event=shot_std_by_event,
            A_ref_trace=A_ref_trace,
            A_sca_trace=A_sca_trace,
            mean_reference_to_scattering_ratios=mean_reference_to_scattering_ratios,
            transit_times=transit_times,
            local_snrs=local_snrs,
            position_diags=position_diags,
            nodi_transit_bandwidths=_mean_trace_by_event(
                readout.get("nodi_transit_bandwidth_Hz"),
                block_size=block_size,
            ),
            nodi_transit_gains=_mean_trace_by_event(
                readout.get("nodi_transit_bandwidth_gain"),
                block_size=block_size,
                default=1.0,
            ),
            nodi_bandwidth_limited_fractions=_mean_trace_by_event(
                readout.get("nodi_bandwidth_limited_fraction"),
                block_size=block_size,
            ),
            interference_overlap_factor_abs=float(
                trace_diag.get("interference_overlap_factor_abs", 1.0) or 1.0
            ),
            interference_overlap_factor_phase_rad=float(
                trace_diag.get("interference_overlap_factor_phase_rad", 0.0) or 0.0
            ),
            illumination={
                "illumination_projection_coupling_status": illumination_status,
            },
            reference={
                **reference,
                "reference_projection_coupling_status": reference_projection_status,
            },
            sca_trace=sca_trace_diag,
            event_max_margin_z=event_max_margin_z_by_event,
            background_max_margin_z=background_max_margin_z_by_event,
            detection_decision_mode=sim_cfg.detection_decision_mode,
        )
        return block_size, False, "fixed_event_budget", {}

    for offset in range(block_size):
        threshold = float(thresholds[offset])
        pod_threshold = float(pod_thresholds[offset])
        if nodi_peak_candidate_mask[offset]:
            features_nodi = extract_pulse_features(
                pulse_time_s,
                post_signal[offset],
                threshold,
                sim_cfg.min_peak_width_s,
                sim_cfg.min_peak_interval_s,
                detection_mode=sim_cfg.pulse_detection_mode,
                context=pulse_context_active,
                include_area_prominence=False,
                width_measure_mode=sim_cfg.pulse_width_measure_mode,
                duration_estimation_policy=sim_cfg.pulse_duration_estimation_policy,
            )
        else:
            features_nodi = _empty_pulse_features(
                threshold,
                sim_cfg.pulse_detection_mode,
                sim_cfg.pulse_width_measure_mode,
                sim_cfg.pulse_duration_estimation_policy,
            )
        if pod_peak_candidate_mask[offset]:
            features_pod = extract_pulse_features(
                pulse_time_s,
                post_pod_signal[offset],
                pod_threshold,
                sim_cfg.min_peak_width_s,
                sim_cfg.min_peak_interval_s,
                detection_mode=sim_cfg.pulse_detection_mode,
                context=pulse_context_active,
                include_area_prominence=False,
                width_measure_mode=sim_cfg.pulse_width_measure_mode,
                duration_estimation_policy=sim_cfg.pulse_duration_estimation_policy,
            )
        else:
            features_pod = _empty_pulse_features(
                pod_threshold,
                sim_cfg.pulse_detection_mode,
                sim_cfg.pulse_width_measure_mode,
                sim_cfg.pulse_duration_estimation_policy,
            )
        paired_pulse_count, paired_primary_indices = _pair_peaks_by_time(
            features_nodi["peaks"],
            features_pod["peaks"],
            sim_cfg.pulse_pairing_tolerance_s,
        )
        features_paired = _build_paired_features(features_nodi, paired_primary_indices)
        features = (
            features_paired
            if sim_cfg.detection_decision_mode == "paired_channel"
            else features_nodi
        )
        detected_single_channel = features_nodi["n_peaks"] > 0
        detected_paired_channel = features_paired["n_peaks"] > 0
        best_peak_paired = False
        if features_nodi["n_peaks"] > 0:
            best_peak_idx = int(
                np.argmax([peak["peak_height"] for peak in features_nodi["peaks"]])
            )
            best_peak_paired = best_peak_idx in paired_primary_indices

        A_ref_row = A_ref_trace[offset]
        A_sca_row = A_sca_trace[offset]
        mean_reference_to_scattering_ratio = float(
            mean_reference_to_scattering_ratios[offset]
        )

        summary_accumulator.update_from_simulation(
            features=features,
            features_nodi=features_nodi,
            features_paired=features_paired,
            detected_single_channel=detected_single_channel,
            detected_paired_channel=detected_paired_channel,
            threshold=threshold,
            threshold_robust_std=float(threshold_robust_stds[offset]),
            pod_threshold=pod_threshold,
            pod_threshold_robust_std=float(pod_threshold_robust_stds[offset]),
            threshold_background_segment_samples=n_bg,
            trace={
                "I_baseline": float(baseline_by_event[offset]),
                **trace_diag,
            },
            noisy={
                "shot_noise_std_mean": float(shot_std_by_event[offset]),
                "shot_noise_reference_dominated_fraction": float(
                    shot_ref_dominated_by_event[offset]
                ),
                "mean_shot_noise_intensity_proxy": float(
                    shot_intensity_by_event[offset]
                ),
                "mean_shot_noise_baseline_proxy": float(
                    shot_baseline_by_event[offset]
                ),
            },
            A_ref_trace=A_ref_row,
            A_sca_trace=A_sca_row,
            mean_reference_to_scattering_ratio=mean_reference_to_scattering_ratio,
            transit_time_s=float(transit_times[offset]),
            local_snr=float(local_snrs[offset]),
            position_diag=position_diags[offset],
            readout={
                "nodi_transit_bandwidth_Hz": _event_diag_value(
                    readout.get("nodi_transit_bandwidth_Hz"),
                    offset,
                    0.0,
                ),
                "nodi_transit_bandwidth_gain": _event_diag_value(
                    readout.get("nodi_transit_bandwidth_gain"),
                    offset,
                    1.0,
                ),
                "nodi_bandwidth_limited_fraction": _event_diag_value(
                    readout.get("nodi_bandwidth_limited_fraction"),
                    offset,
                    0.0,
                ),
            },
            illumination={
                "illumination_projection_coupling_status": illumination_status,
            },
            reference={
                **reference,
                "reference_projection_coupling_status": reference_projection_status,
            },
            paired_pulse_count=paired_pulse_count,
            best_peak_paired=best_peak_paired,
            sca_trace=sca_trace_diag,
            event_max_margin_z=float(event_max_margin_z_by_event[offset]),
            background_max_margin_z=float(background_max_margin_z_by_event[offset]),
            detection_decision_mode=sim_cfg.detection_decision_mode,
        )
        processed += 1

        if adaptive_accumulator is not None:
            stopped, adaptive_stop_reason, adaptive_state = (
                _should_stop_adaptive_event_budget(adaptive_accumulator, sim_cfg)
            )
            if stopped:
                break

    return processed, stopped, adaptive_stop_reason, adaptive_state


def summarize_batch(
    event_results: list[dict],
    stable_detection_margin_z_min: float = 1.0,
    fixed_false_alarm_rate: float = 0.05,
    selected_annulus_edge_norm_min: float = SELECTED_DETECTOR_MODE_EDGE_NORM_MIN,
    selected_annulus_edge_norm_max: float = SELECTED_DETECTOR_MODE_EDGE_NORM_MAX,
) -> dict:
    """
    Compute summary statistics from a batch of simulated events.

    For each event with detected peaks, the highest peak is used.

    Args:
        event_results: List of dicts from simulate_one_event.

    Returns:
        dict with n_events, n_detected, detection_rate, mean/std peak heights, etc.
    """
    accumulator = _BatchSummaryAccumulator(
        stable_detection_margin_z_min=stable_detection_margin_z_min,
        fixed_false_alarm_rate=fixed_false_alarm_rate,
        selected_annulus_edge_norm_min=selected_annulus_edge_norm_min,
        selected_annulus_edge_norm_max=selected_annulus_edge_norm_max,
    )
    for event in event_results:
        accumulator.update(event)
    return accumulator.finalize()


def wilson_lower_bound(successes: int, trials: int, z: float = 1.96) -> float:
    """Wilson score lower bound for a Bernoulli proportion."""
    if trials <= 0:
        return 0.0
    p_hat = float(successes) / float(trials)
    z2 = z * z
    denom = 1.0 + z2 / trials
    center = p_hat + z2 / (2.0 * trials)
    radius = z * math.sqrt(
        (p_hat * (1.0 - p_hat) + z2 / (4.0 * trials)) / trials
    )
    return float(max(0.0, (center - radius) / denom))


def wilson_upper_bound(successes: int, trials: int, z: float = 1.96) -> float:
    """Wilson score upper bound for a Bernoulli proportion."""
    if trials <= 0:
        return 1.0
    p_hat = float(successes) / float(trials)
    z2 = z * z
    denom = 1.0 + z2 / trials
    center = p_hat + z2 / (2.0 * trials)
    radius = z * math.sqrt(
        (p_hat * (1.0 - p_hat) + z2 / (4.0 * trials)) / trials
    )
    return float(min(1.0, (center + radius) / denom))


def compute_empirical_roc_auc(
    positive_scores: list[float],
    negative_scores: list[float],
) -> float:
    """
    Empirical ROC-AUC using pairwise ranking.

    Scores are interpreted as "larger means more signal-like".
    """
    if not positive_scores or not negative_scores:
        return 0.5

    pos = np.asarray(positive_scores, dtype=float)
    neg = np.asarray(negative_scores, dtype=float)
    wins = 0.0
    for score in pos:
        wins += float(np.sum(score > neg))
        wins += 0.5 * float(np.sum(score == neg))
    return float(wins / (len(pos) * len(neg)))


def compute_hit_rate_at_fixed_false_alarm(
    positive_scores: list[float],
    negative_scores: list[float],
    false_alarm_rate: float,
) -> float:
    """
    Hit rate when the detection threshold is chosen from the negative/background
    distribution at a fixed false-alarm rate.
    """
    if not positive_scores:
        return 0.0
    if not negative_scores:
        return 1.0
    far = float(np.clip(false_alarm_rate, 0.0, 1.0 - 1e-12))
    quantile = 1.0 - far
    threshold = float(np.quantile(np.asarray(negative_scores, dtype=float), quantile, method="linear"))
    pos = np.asarray(positive_scores, dtype=float)
    return float(np.mean(pos >= threshold))


def compute_d_prime(
    positive_scores: list[float],
    negative_scores: list[float],
) -> float:
    """
    Signal-detection discriminability index d' computed from event/background
    score distributions.
    """
    if not positive_scores or not negative_scores:
        return 0.0

    pos = np.asarray(positive_scores, dtype=float)
    neg = np.asarray(negative_scores, dtype=float)
    mean_diff = float(np.mean(pos) - np.mean(neg))
    var_pos = float(np.var(pos, ddof=1)) if len(pos) > 1 else 0.0
    var_neg = float(np.var(neg, ddof=1)) if len(neg) > 1 else 0.0
    pooled_std = math.sqrt(max(0.5 * (var_pos + var_neg), 0.0))
    if pooled_std <= 1e-15:
        return 0.0 if abs(mean_diff) <= 1e-15 else float(np.sign(mean_diff) * 10.0)
    return float(mean_diff / pooled_std)


def _build_rho_physical_envelope_diagnostics(
    reference: dict,
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """
    Convert the reference-side diffraction envelope into a rho-range diagnostic.

    The reference module exports a thin-phase-grating amplitude envelope on the
    reference-field side. The simulator then applies `A_ref_unprojected = rho *
    g_ref_geometry`, where `g_ref_geometry` already absorbs the geometry- and
    operator-dependent surrogate scaling. To keep the diagnostic in the same
    surrogate semantics, map the envelope back into rho-space via

        rho_nominal ~ reference_field_amplitude_envelope / g_ref_geometry

    rather than dividing by `E_sca_ref`, which belongs to the scattering-side
    normalization chain.
    """
    amplitude_nominal = reference.get("reference_field_amplitude_envelope_nominal")
    amplitude_lower = reference.get("reference_field_amplitude_envelope_lower")
    amplitude_upper = reference.get("reference_field_amplitude_envelope_upper")
    g_ref_geometry = reference.get("g_ref_geometry", reference.get("g_ref"))

    if (
        amplitude_nominal is None
        or amplitude_lower is None
        or amplitude_upper is None
        or g_ref_geometry is None
        or not np.isfinite(float(g_ref_geometry))
        or float(g_ref_geometry) <= 1e-15
    ):
        return {
            "rho_requested": float(sim_cfg.rho),
            "rho_physical_envelope_source": "reference_field_amplitude_envelope / g_ref_geometry",
            "rho_physical_envelope_nominal": None,
            "rho_physical_envelope_lower": None,
            "rho_physical_envelope_upper": None,
            "rho_physical_ratio_to_nominal": None,
            "rho_physical_envelope_in_range": None,
            "rho_physical_envelope_status": "unavailable",
        }

    amplitude_nominal = float(amplitude_nominal)
    amplitude_lower = float(amplitude_lower)
    amplitude_upper = float(amplitude_upper)
    g_ref_geometry = float(g_ref_geometry)
    rho_requested = float(sim_cfg.rho)
    rho_nominal = amplitude_nominal / g_ref_geometry
    rho_lower = amplitude_lower / g_ref_geometry
    rho_upper = amplitude_upper / g_ref_geometry

    if rho_requested < rho_lower:
        status = "below_envelope"
    elif rho_requested > rho_upper:
        status = "above_envelope"
    else:
        status = "within_envelope"

    return {
        "rho_requested": rho_requested,
        "rho_physical_envelope_source": "reference_field_amplitude_envelope / g_ref_geometry",
        "rho_physical_envelope_nominal": float(rho_nominal),
        "rho_physical_envelope_lower": float(rho_lower),
        "rho_physical_envelope_upper": float(rho_upper),
        "rho_physical_ratio_to_nominal": (
            float(rho_requested / rho_nominal) if rho_nominal > 1e-15 else None
        ),
        "rho_physical_envelope_in_range": bool(rho_lower <= rho_requested <= rho_upper),
        "rho_physical_envelope_status": status,
    }


def _freeze_cache_value(value):
    """Build a stable, hashable representation for local cache keys."""
    if isinstance(value, dict):
        return tuple(
            (str(key), _freeze_cache_value(val))
            for key, val in sorted(value.items(), key=lambda item: str(item[0]))
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_cache_value(item) for item in value)
    if isinstance(value, np.ndarray):
        arr = np.asarray(value)
        return (tuple(arr.shape), arr.dtype.str, hash(arr.tobytes()))
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, complex):
        return (float(value.real), float(value.imag))
    return value


def _particle_intrinsic_identity_key(particle: Particle) -> tuple[object, ...]:
    """Build a stable cache key for intrinsic particle optics."""
    return (
        str(particle.name),
        float(particle.radius_m),
        float(particle.n_real),
        float(particle.n_imag),
        str(particle.model_type),
        particle.material_key,
        bool(particle.use_material_model),
        particle.structure_key,
        _freeze_cache_value(particle.structure_params),
    )


def _medium_optical_identity_key(
    medium: Medium,
    wavelength_m: float,
) -> tuple[object, ...]:
    """Build a stable cache key for medium optics at one wavelength."""
    return (
        str(medium.name),
        float(medium.refractive_index),
        medium.material_key,
        bool(medium.use_material_model),
        medium.optical_material_key,
        float(medium.refractive_index_at(wavelength_m)),
    )


def _channel_identity_key(
    channel: Channel,
    wavelength_m: float,
) -> tuple[object, ...]:
    """Build a stable cache key for one channel optical geometry."""
    return (
        float(channel.width_m),
        float(channel.depth_m),
        float(channel.wall_refractive_index),
        str(channel.material_name),
        channel.wall_material_key,
        float(channel.wall_refractive_index_at(wavelength_m)),
    )


def _optical_identity_key(optical: OpticalSystem) -> tuple[object, ...]:
    """Build a stable cache key for optical fields used in case-level solvers."""
    return (
        float(optical.wavelength_m),
        float(optical.peak_irradiance_W_m2),
        float(optical.beam_waist_x_m),
        float(optical.beam_waist_y_m),
        float(optical.beam_waist_z_m),
        None
        if optical.illumination_beam_waist_x_m is None
        else float(optical.illumination_beam_waist_x_m),
        None
        if optical.illumination_beam_waist_y_m is None
        else float(optical.illumination_beam_waist_y_m),
        None
        if optical.illumination_beam_waist_z_m is None
        else float(optical.illumination_beam_waist_z_m),
        None if optical.illumination_NA is None else float(optical.illumination_NA),
        float(optical.focus_x_m),
        float(optical.focus_y_m),
        float(optical.focus_z_m),
        float(optical.collection_theta_rad),
        float(optical.system_efficiency),
        str(optical.detection_mode),
        float(optical.NA_collection),
    )


def _theta_grid_identity_key(theta_grid_rad: np.ndarray) -> tuple[object, ...]:
    """Build a cache key for one theta grid."""
    theta = np.asarray(theta_grid_rad, dtype=float)
    return (
        tuple(theta.shape),
        theta.dtype.str,
        hash(theta.tobytes()),
    )


def _contains_nested_ndarray(value: object) -> bool:
    if isinstance(value, np.ndarray):
        return True
    if isinstance(value, dict):
        return any(_contains_nested_ndarray(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_nested_ndarray(item) for item in value)
    return False


def _mark_numpy_arrays_readonly(payload: dict) -> dict:
    """Prevent accidental mutation of cached top-level numerical arrays.

    Cache builders are expected to keep NumPy arrays as top-level dict values;
    nested array payloads must be marked read-only before entering these caches.
    """
    for key, value in payload.items():
        if isinstance(value, np.ndarray):
            value.setflags(write=False)
        elif isinstance(value, (dict, list, tuple)) and _contains_nested_ndarray(value):
            raise TypeError(
                f"Cache payload key {key!r} contains a nested ndarray; "
                "_mark_numpy_arrays_readonly only handles top-level arrays"
            )
    return payload


def _get_or_compute_intrinsic_scattering(
    particle: Particle,
    medium: Medium,
    wavelength_m: float,
    theta_grid_rad: np.ndarray,
    intrinsic_cache: dict | None,
) -> dict:
    """Return intrinsic scattering, reusing worker-local immutable payloads."""
    if intrinsic_cache is None:
        return compute_intrinsic_scattering(
            particle,
            medium,
            wavelength_m,
            theta_grid_rad,
        )
    key = (
        _particle_intrinsic_identity_key(particle),
        _medium_optical_identity_key(medium, wavelength_m),
        float(wavelength_m),
        _theta_grid_identity_key(theta_grid_rad),
    )
    cached = intrinsic_cache.get(key)
    if cached is None:
        cached = compute_intrinsic_scattering(
            particle,
            medium,
            wavelength_m,
            theta_grid_rad,
        )
        intrinsic_cache[key] = _mark_numpy_arrays_readonly(cached)
    return dict(cached)


def _get_or_build_collection_operator(
    theta_grid_rad: np.ndarray,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    medium_refractive_index: float,
    collection_operator_cache: dict | None,
) -> dict:
    """Return a worker-local collection operator for one geometry/grid."""
    if collection_operator_cache is None:
        return build_collection_operator(
            theta_grid_rad,
            channel,
            optical,
            sim_cfg,
            medium_refractive_index=medium_refractive_index,
        )
    key = (
        _theta_grid_identity_key(theta_grid_rad),
        _channel_identity_key(channel, optical.wavelength_m),
        _optical_identity_key(optical),
        id(sim_cfg),
        float(medium_refractive_index),
    )
    cached = collection_operator_cache.get(key)
    if cached is None:
        cached = build_collection_operator(
            theta_grid_rad,
            channel,
            optical,
            sim_cfg,
            medium_refractive_index=medium_refractive_index,
        )
        collection_operator_cache[key] = _mark_numpy_arrays_readonly(cached)
    return dict(cached)


def _get_or_compute_reference_field(
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    medium_refractive_index: float,
    reference_cache: dict | None,
) -> dict:
    """Return a caller-owned reference payload from a worker-local base cache."""
    if reference_cache is None:
        return compute_reference_field(
            channel,
            optical,
            sim_cfg,
            medium_refractive_index=medium_refractive_index,
        )
    key = (
        _channel_identity_key(channel, optical.wavelength_m),
        _optical_identity_key(optical),
        id(sim_cfg),
        float(medium_refractive_index),
    )
    cached = reference_cache.get(key)
    if cached is None:
        reference = compute_reference_field(
            channel,
            optical,
            sim_cfg,
            medium_refractive_index=medium_refractive_index,
        )
        cached = _mark_numpy_arrays_readonly(reference)
        reference_cache[key] = cached
    return dict(cached)


def run_single_case_batch(
    particle: Particle,
    medium: Medium,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    E_sca_ref: float,
    theta_grid_rad: np.ndarray,
    *,
    retain_event_traces: bool = True,
    stream_summary_only: bool = False,
    intrinsic_cache: dict | None = None,
    reference_cache: dict | None = None,
    collection_operator_cache: dict | None = None,
) -> dict:
    """
    Run a full batch of events for a single (particle, channel, optical) case.

    This function handles:
        1. Configuration validation
        2. Intrinsic scattering computation
        3. Interpolation at θ_det + normalization by E_sca_ref
        4. Reference field computation
        5. n_events event simulations
        6. Batch summary statistics

    Args:
        particle: Particle type.
        medium: Medium.
        channel: Channel geometry (specific W, H for this case).
        optical: Optical system (specific λ for this case).
        sim_cfg: Simulation config.
        E_sca_ref: Global normalization constant (from compute_baseline_normalization).
        theta_grid_rad: Global angle grid.
        retain_event_traces: When False, keep only the per-event fields needed
            for batch summary/freeze diagnostics instead of full trajectories
            and signal arrays. This is intended for large sweeps.
        stream_summary_only: Internal optimization for large sweeps. When True
            together with retain_event_traces=False, accumulate the batch
            summary on the fly and skip retaining the slim per-event list.

    Returns:
        dict with "events" (list) and "summary" (dict).
    """
    # 1. Validate
    validate_simulation_config(sim_cfg, optical)
    non_default_detector_route = (
        str(getattr(sim_cfg, "detector_route_id", "A_hybrid")) != "A_hybrid"
    )
    if non_default_detector_route and str(sim_cfg.vectorized_event_engine) != "off":
        raise ValueError(
            "detector routes beyond A_hybrid currently require "
            "vectorized_event_engine='off' so full diagnostics are available"
        )
    medium_refractive_index = float(medium.refractive_index_at(optical.wavelength_m))
    diffusion_coefficient = (
        _compute_diffusion_coefficient(particle, medium)
        if sim_cfg.include_diffusion
        else None
    )
    event_case_context = _build_event_case_context(
        channel,
        sim_cfg,
        particle_radius_m=particle.radius_m,
    )
    trajectory_context = event_case_context.trajectory_context
    case_time_s = trajectory_context.time_s
    readout_context = _build_readout_context(
        case_time_s,
        sim_cfg,
    )
    # 2. Intrinsic scattering (pure, unnormalized)
    intrinsic = _get_or_compute_intrinsic_scattering(
        particle,
        medium,
        optical.wavelength_m,
        theta_grid_rad,
        intrinsic_cache,
    )
    unit_axis_conventions = build_unit_axis_convention_diagnostics(
        particle,
        channel,
        optical,
        sim_cfg,
    )
    mie_validation = build_mie_validation_diagnostics(intrinsic, sim_cfg)
    wavelength_comparability = build_wavelength_comparability_diagnostics(
        optical,
        sim_cfg,
        medium=medium,
    )
    objective_profile = build_objective_profile_diagnostics(optical, sim_cfg)
    optical_exposure = build_optical_exposure_safety_diagnostics(
        particle,
        optical,
        sim_cfg,
        intrinsic,
    )
    objective_panel = evaluate_objective_panel(
        particle,
        optical,
        sim_cfg,
        intrinsic,
    )
    nodi_thermal_contamination = build_nodi_thermal_contamination_diagnostics(
        particle,
        optical,
        sim_cfg,
        intrinsic,
    )
    channel_geometry = build_channel_geometry_diagnostics(
        particle,
        channel,
        optical,
        sim_cfg,
    )
    trajectory_geometry = build_trajectory_geometry_diagnostics(sim_cfg)
    electrokinetic_transport = build_electrokinetic_transport_diagnostics(
        channel,
        sim_cfg,
    )
    ev_integrity = build_ev_integrity_risk_diagnostics(
        particle,
        channel,
        sim_cfg,
        geometry=channel_geometry,
    )
    ev_reporting = build_ev_reporting_metadata_diagnostics()
    assay_controls = build_assay_control_matrix_diagnostics()
    control_interpretation = build_control_interpretation_diagnostics(assay_controls)
    recompute_manifest = build_recompute_manifest_diagnostics(
        particle,
        channel,
        optical,
        sim_cfg,
    )
    fluidic_resistance = compute_fluidic_practicality_penalty(
        particle,
        medium,
        channel,
        sim_cfg,
    )
    fluidic_network = build_fluidic_network_diagnostics(
        medium,
        channel,
        sim_cfg,
    )
    particle_design_library = build_particle_design_library_diagnostics(
        particle,
        sim_cfg,
    )
    collection_medium_refractive_index = (
        float(intrinsic.get("k_m", intrinsic["k_m_inv"]))
        * float(optical.wavelength_m)
        / (2.0 * np.pi)
    )
    collection_operator = _get_or_build_collection_operator(
        intrinsic["theta_grid_rad"],
        channel,
        optical,
        sim_cfg,
        collection_medium_refractive_index,
        collection_operator_cache,
    )
    collection = compute_detected_scattering_field(
        intrinsic,
        channel,
        optical,
        sim_cfg,
        collection_operator=collection_operator,
    )
    theta_det = collection["theta_effective_rad"]

    # 3. Collapse the angular response with the same collection logic used by
    # the baseline normalization, then normalize against the shared reference.
    E_sca_at_det_complex = collection["E_sca_detected_complex"]
    E_sca_at_det = collection["E_sca_detected_abs"]
    E_sca_unit_normalized = E_sca_at_det_complex / E_sca_ref

    # 4. Reference field
    reference = _get_or_compute_reference_field(
        channel,
        optical,
        sim_cfg,
        medium_refractive_index,
        reference_cache,
    )
    tsuyama_bfp_reference = {
        field: reference.get(field)
        for field in TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS
        if field in reference
    }
    reference.update(unit_axis_conventions)
    reference.update(mie_validation)
    reference.update(wavelength_comparability)
    reference.update(objective_profile)
    reference.update(optical_exposure)
    reference.update(objective_panel)
    reference.update(nodi_thermal_contamination)
    reference.update(channel_geometry)
    reference.update(trajectory_geometry)
    reference.update(electrokinetic_transport)
    reference.update(ev_integrity)
    reference.update(ev_reporting)
    reference.update(assay_controls)
    reference.update(control_interpretation)
    reference.update(recompute_manifest)
    reference.update(fluidic_resistance)
    reference.update(fluidic_network)
    reference.update(particle_design_library)
    reference_operating_point = build_reference_operating_point_diagnostics(
        reference,
        channel,
        optical,
        sim_cfg,
    )
    reference.update(reference_operating_point)
    collection_operator_state = {
        "operator_route": collection.get("operator_route"),
        "operator_normalization": collection.get("operator_normalization"),
        "collection_operator_calibration_status": collection.get(
            "collection_operator_calibration_status"
        ),
        "collection_operator_coverage_status": collection.get(
            "collection_operator_coverage_status"
        ),
        "collection_operator_calibration_source": collection.get(
            "collection_operator_calibration_source"
        ),
        "collection_operator_id": collection.get("collection_operator_id"),
        "collection_operator_calibrated_geometry": collection.get(
            "collection_operator_calibrated_geometry"
        ),
        "collection_operator_max_relative_geometry_distance": collection.get(
            "collection_operator_max_relative_geometry_distance"
        ),
        **{field: collection.get(field) for field in _COLLECTION_OPERATOR_EXTRA_FIELDS},
        "surrogate_throughput_scale": collection.get("surrogate_throughput_scale"),
        "absolute_throughput_route": collection.get("absolute_throughput_route"),
        "absolute_throughput_calibrated": collection.get(
            "absolute_throughput_calibrated"
        ),
    }
    reference.update(collection_operator_state)
    reference.update(
        _build_rho_physical_envelope_diagnostics(
            reference,
            sim_cfg,
        )
    )
    overlap_diagnostics = {
        "interference_overlap_mode": str(sim_cfg.interference_overlap_mode),
        "interference_cross_term_model_default": str(sim_cfg.interference_overlap_mode),
        "interference_cross_term_joint_available": False,
        "interference_overlap_status": "unavailable_no_reference_angular_field",
    }
    if (
        sim_cfg.reference_model in {"channel_angular_surrogate", "paper_aligned_phase_filter"}
        and "reference_angular_field" in reference
        and "angular_field_theta" in collection
    ):
        overlap_diagnostics = build_interference_overlap_diagnostics(
            np.asarray(reference["reference_theta_grid_rad"], dtype=float),
            np.asarray(reference["reference_angular_field"], dtype=complex),
            np.asarray(collection["angular_field_theta"], dtype=complex),
            collection["collection_operator"],
            sim_cfg,
            phi_grid_rad=np.asarray(reference["reference_phi_grid_rad"], dtype=float),
            scattering_theta_grid_rad=np.asarray(collection["theta_grid_rad"], dtype=float),
        )
    reference.update(overlap_diagnostics)
    overlap_freeze = classify_interference_overlap_freeze(
        overlap_factor_abs=float(overlap_diagnostics.get("interference_overlap_factor_abs", 1.0)),
        overlap_factor_phase_rad=float(
            overlap_diagnostics.get("interference_overlap_factor_phase_rad", 0.0)
        ),
        collapsed_cross_term_scalar=float(
            abs(overlap_diagnostics.get("interference_collapsed_product_complex", 0.0 + 0.0j))
        ),
        joint_cross_term_scalar=float(
            abs(overlap_diagnostics.get("interference_joint_overlap_complex", 0.0 + 0.0j))
        ),
        joint_available=bool(
            overlap_diagnostics.get("interference_cross_term_joint_available", False)
        ),
        default_model=str(sim_cfg.interference_overlap_mode),
    )
    reference.update(overlap_freeze)
    detector_forward = build_detector_forward_diagnostics(
        sim_cfg,
        overlap_diagnostics,
    )
    reference.update(detector_forward)
    bfp_detector_operator = build_bfp_detector_operator_diagnostics(
        reference,
        collection,
        sim_cfg,
        E_sca_unit_normalized_complex=E_sca_unit_normalized,
    )
    reference.update(bfp_detector_operator)
    complex_conventions = build_complex_field_convention_diagnostics(
        sim_cfg,
        optical=optical,
        intrinsic=intrinsic,
    )
    reference.update(complex_conventions)
    polarization_jones = build_polarization_jones_diagnostics(sim_cfg)
    reference.update(polarization_jones)
    calibration_state = build_calibration_state_diagnostics(
        sim_cfg,
        reference=reference,
        optical=optical,
        collection_operator=collection.get("collection_operator"),
        E_sca_ref=E_sca_ref,
    )
    reference.update(calibration_state)
    bayesian_calibration = build_bayesian_calibration_scaffold(
        reference,
        sim_cfg,
    )
    reference.update(bayesian_calibration)
    particle_model_state = build_particle_model_diagnostics(
        particle,
        sim_cfg,
        intrinsic=intrinsic,
    )
    reference.update(particle_model_state)
    interface_correction_state = build_interface_correction_diagnostics(
        particle,
        medium,
        channel,
        optical,
        sim_cfg,
    )
    reference.update(interface_correction_state)
    detector_noise_state = build_detector_noise_diagnostics(
        sim_cfg,
        collection_operator=collection.get("collection_operator"),
    )
    reference.update(detector_noise_state)
    illumination_geometry = optical.resolve_illumination_geometry()
    illumination_beam_area_m2 = math.pi * float(
        illumination_geometry["illumination_beam_waist_x_m"]
    ) * float(illumination_geometry["illumination_beam_waist_z_m"])
    extinction_to_beam_area_estimate = (
        float(intrinsic["Cext_m2"]) / illumination_beam_area_m2
        if illumination_beam_area_m2 > 0.0
        else None
    )
    A_ref_for_superposition = float(reference.get("A_ref", 0.0) or 0.0)
    e_sca_to_ref_amplitude_ratio_estimate = (
        float(abs(E_sca_unit_normalized)) / A_ref_for_superposition
        if A_ref_for_superposition > 0.0
        else None
    )
    background_field_state = build_background_field_diagnostics(
        sim_cfg,
        e_sca_to_ref_amplitude_ratio_estimate=e_sca_to_ref_amplitude_ratio_estimate,
        extinction_to_beam_area_estimate=extinction_to_beam_area_estimate,
    )
    reference.update(background_field_state)
    particle_channel_perturbation = (
        build_particle_channel_perturbation_diagnostics(
            particle,
            medium,
            channel,
            optical,
            sim_cfg,
            E_ref_complex=complex(reference.get("E_ref_complex", 0.0 + 0.0j)),
            E_sca_unit_normalized_complex=E_sca_unit_normalized,
            intrinsic=intrinsic,
        )
    )
    reference.update(particle_channel_perturbation)
    readout_conventions = build_readout_convention_diagnostics(sim_cfg)
    reference.update(readout_conventions)
    photothermal_pod_state = build_photothermal_pod_diagnostics(optical, sim_cfg)
    reference.update(photothermal_pod_state)
    threshold_false_alarm_state = build_threshold_false_alarm_diagnostics(sim_cfg)
    reference.update(threshold_false_alarm_state)
    gouy_geometry = classify_delta_phi_gouy_geometry_validity(
        channel=channel,
        optical=optical,
        phase_model=str(sim_cfg.phase_model),
    )
    scattering_projection_basis = event_case_context.scattering_projection_basis
    scattering_phase_summary = {
        "phi_sca_material_rad": collection.get("phi_sca_material_rad"),
        "phi_sca_material_parallel_rad": collection.get("phi_sca_material_parallel_rad"),
        "phi_sca_material_perpendicular_rad": collection.get(
            "phi_sca_material_perpendicular_rad"
        ),
        "phi_projection_rad": collection.get("phi_projection_rad"),
    }

    # 5. Batch events
    case_identity = _build_case_random_identity(
        particle,
        medium,
        channel,
        optical,
    )
    rng_seed = _resolve_case_rng_seed(sim_cfg, case_identity)
    rng = np.random.default_rng(rng_seed)
    unit_position_samples = _build_event_position_unit_samples(
        n_events=sim_cfg.n_events,
        policy=sim_cfg.event_sampling_policy,
        seed=rng_seed,
        case_identity=case_identity,
    )
    summary_accumulator = (
        _BatchSummaryAccumulator(
            stable_detection_margin_z_min=sim_cfg.stable_detection_margin_z_min,
            fixed_false_alarm_rate=sim_cfg.evaluation_false_alarm_rate,
            selected_annulus_edge_norm_min=sim_cfg.selected_annulus_edge_norm_min,
            selected_annulus_edge_norm_max=sim_cfg.selected_annulus_edge_norm_max,
        )
        if stream_summary_only and not retain_event_traces
        else None
    )
    adaptive_accumulator = None
    if sim_cfg.adaptive_event_budget_mode != "fixed":
        adaptive_accumulator = summary_accumulator
        if adaptive_accumulator is None:
            adaptive_accumulator = _BatchSummaryAccumulator(
                stable_detection_margin_z_min=sim_cfg.stable_detection_margin_z_min,
                fixed_false_alarm_rate=sim_cfg.evaluation_false_alarm_rate,
                selected_annulus_edge_norm_min=sim_cfg.selected_annulus_edge_norm_min,
                selected_annulus_edge_norm_max=sim_cfg.selected_annulus_edge_norm_max,
            )
    events = []
    adaptive_stop_reason = (
        "fixed_event_budget"
        if sim_cfg.adaptive_event_budget_mode == "fixed"
        else "max_events_reached"
    )
    adaptive_state: dict[str, object] = {
        "adaptive_event_budget_converged": False,
        "adaptive_event_budget_detection_half_width": None,
        "adaptive_event_budget_stable_half_width": None,
        "adaptive_event_budget_max_half_width": None,
        "adaptive_event_budget_target_half_width": float(
            sim_cfg.adaptive_wilson_half_width_target
        ),
    }
    vectorized_supported, vectorized_fallback_reason = (
        _vectorized_stream_event_block_supported(
            sim_cfg,
            retain_event_traces=retain_event_traces,
            stream_summary_only=stream_summary_only,
        )
    )
    vectorized_engine_used = (
        sim_cfg.vectorized_event_engine
        if vectorized_supported
        else (
            "off"
            if sim_cfg.vectorized_event_engine == "off"
            else "event_loop_fallback"
        )
    )
    event_block_random_state = (
        _build_event_block_random_state(rng_seed)
        if vectorized_supported
        and sim_cfg.vectorized_event_engine in {"event_block_v2", "event_block_v3"}
        and sim_cfg.event_block_rng_order == "block_lane_order"
        else None
    )
    if vectorized_supported:
        if summary_accumulator is None:
            raise RuntimeError(
                f"{sim_cfg.vectorized_event_engine} requires a stream summary accumulator"
            )
        event_idx = 0
        block_size = max(1, int(sim_cfg.event_block_size))
        while event_idx < int(sim_cfg.n_events):
            stop_idx = min(int(sim_cfg.n_events), event_idx + block_size)
            processed, should_stop, block_stop_reason, block_state = (
                _simulate_stream_event_block(
                    particle=particle,
                    channel=channel,
                    optical=optical,
                    sim_cfg=sim_cfg,
                    E_sca_unit_normalized=E_sca_unit_normalized,
                    reference=reference,
                    theta_det_rad=theta_det,
                    rng=rng,
                    vectorized_engine=sim_cfg.vectorized_event_engine,
                    diffusion_coefficient=diffusion_coefficient,
                    start_idx=event_idx,
                    stop_idx=stop_idx,
                    unit_position_samples=unit_position_samples,
                    medium_refractive_index=medium_refractive_index,
                    readout_context=readout_context,
                    trajectory_context=trajectory_context,
                    event_case_context=event_case_context,
                    summary_accumulator=summary_accumulator,
                    adaptive_accumulator=adaptive_accumulator,
                    event_block_random_state=event_block_random_state,
                )
            )
            event_idx += processed
            if block_state:
                adaptive_state = block_state
            if adaptive_accumulator is not None:
                adaptive_stop_reason = block_stop_reason
            if should_stop:
                break
            if processed <= 0:
                raise RuntimeError("vectorized event block made no progress")
    else:
        for event_idx in range(sim_cfg.n_events):
            unit_position_sample = (
                tuple(float(x) for x in unit_position_samples[event_idx])
                if unit_position_samples is not None
                else None
            )
            result = simulate_one_event(
                particle, medium, channel, optical, sim_cfg,
                E_sca_unit_normalized,
                reference,
                theta_det,
                rng,
                scattering_phase_diagnostics=scattering_phase_summary,
                medium_refractive_index=medium_refractive_index,
                diffusion_coefficient=diffusion_coefficient,
                retain_full_payload=retain_event_traces,
                readout_context=readout_context,
                trajectory_context=trajectory_context,
                event_case_context=event_case_context,
                unit_position_sample=unit_position_sample,
                summary_accumulator=summary_accumulator,
            )
            if summary_accumulator is None:
                events.append(result)
                if adaptive_accumulator is not None:
                    adaptive_accumulator.update(result)
            elif result:
                summary_accumulator.update(result)

            if adaptive_accumulator is not None:
                should_stop, adaptive_stop_reason, adaptive_state = (
                    _should_stop_adaptive_event_budget(adaptive_accumulator, sim_cfg)
                )
                if should_stop:
                    break

    first_event = (
        summary_accumulator.first_event
        if summary_accumulator is not None
        else (
            adaptive_accumulator.first_event
            if adaptive_accumulator is not None
            else (events[0] if events else None)
        )
    )
    first_event_defaults = first_event or {}

    projection_freeze = classify_projection_freeze(
        scattering_projection_basis=scattering_projection_basis,
        illumination_projection_coupling_status=str(
            first_event_defaults.get("illumination_projection_coupling_status", "legacy_basisless")
        ),
        reference_projection_coupling_status=str(
            first_event_defaults.get("reference_projection_coupling_status", "legacy_basisless")
        ),
        interference_projection_coupling_status=str(
            first_event_defaults.get("interference_projection_coupling_status", "legacy_basisless")
        ),
    )
    observation_freeze = classify_observation_freeze(
        path_opd_freeze_status=str(
            first_event_defaults.get("path_opd_freeze_status", "unknown")
        ),
        interference_overlap_default_freeze_status=str(
            overlap_freeze.get("interference_overlap_default_freeze_status", "freeze_unavailable")
        ),
        projection_default_freeze_status=str(
            projection_freeze.get("projection_default_freeze_status", "freeze_unavailable")
        ),
        delta_phi_gouy_validity=str(gouy_geometry.get("delta_phi_gouy_validity", "unavailable")),
    )

    # 6. Summary
    summary = (
        summary_accumulator.finalize()
        if summary_accumulator is not None
        else summarize_batch(
            events,
            stable_detection_margin_z_min=sim_cfg.stable_detection_margin_z_min,
            fixed_false_alarm_rate=sim_cfg.evaluation_false_alarm_rate,
            selected_annulus_edge_norm_min=sim_cfg.selected_annulus_edge_norm_min,
            selected_annulus_edge_norm_max=sim_cfg.selected_annulus_edge_norm_max,
        )
    )
    actual_events = int(summary.get("n_events", len(events)))
    if actual_events >= int(sim_cfg.n_events):
        adaptive_stop_reason = (
            "fixed_event_budget"
            if sim_cfg.adaptive_event_budget_mode == "fixed"
            else "max_events_reached"
        )
    adaptive_final_state = (
        _adaptive_event_budget_state(adaptive_accumulator, sim_cfg)
        if adaptive_accumulator is not None
        else adaptive_state
    )
    summary.update(
        {
            "random_sequence_policy": sim_cfg.random_sequence_policy,
            "event_sampling_policy": sim_cfg.event_sampling_policy,
            "event_position_low_variance_sampling": bool(
                sim_cfg.event_sampling_policy != "random"
            ),
            "case_random_seed": int(rng_seed) if rng_seed is not None else None,
            "case_random_identity": case_identity,
            "adaptive_event_budget_mode": sim_cfg.adaptive_event_budget_mode,
            "adaptive_event_budget_requested_events": int(sim_cfg.n_events),
            "adaptive_event_budget_actual_events": actual_events,
            "adaptive_event_budget_stopped_early": bool(
                actual_events < int(sim_cfg.n_events)
            ),
            "adaptive_event_budget_stop_reason": adaptive_stop_reason,
            "adaptive_min_events": int(sim_cfg.adaptive_min_events),
            "adaptive_check_interval": int(sim_cfg.adaptive_check_interval),
            "vectorized_event_engine": sim_cfg.vectorized_event_engine,
            "event_block_size": int(sim_cfg.event_block_size),
            "event_block_rng_order": sim_cfg.event_block_rng_order,
            "vectorized_event_engine_used": vectorized_engine_used,
            "vectorized_event_engine_fallback_reason": vectorized_fallback_reason,
            "non_default_detector_routes_require_vectorized_event_engine_off": True,
            "detector_route_slow_path_guard_status": (
                "required_for_non_default_detector_routes"
                if non_default_detector_route
                else "not_required_for_default_a_hybrid_route"
            ),
            "vectorized_event_rng_order": (
                _vectorized_event_rng_order_label(
                    sim_cfg,
                    vectorized_engine_used,
                )
                if vectorized_engine_used in {"event_block_v2", "event_block_v3"}
                else (
                    "block_batched_order"
                    if vectorized_engine_used == "pure_advection_block"
                    else "event_loop_order"
                )
            ),
            **adaptive_final_state,
        }
    )
    summary.update(overlap_freeze)
    summary.update(projection_freeze)
    summary.update(gouy_geometry)
    summary.update(observation_freeze)
    summary.update(unit_axis_conventions)
    summary.update(mie_validation)
    summary.update(wavelength_comparability)
    summary.update(objective_profile)
    summary.update(optical_exposure)
    summary.update(objective_panel)
    summary.update(nodi_thermal_contamination)
    summary.update(channel_geometry)
    summary.update(trajectory_geometry)
    summary.update(electrokinetic_transport)
    summary.update(ev_integrity)
    summary.update(ev_reporting)
    summary.update(assay_controls)
    summary.update(control_interpretation)
    summary.update(recompute_manifest)
    summary.update(fluidic_resistance)
    summary.update(fluidic_network)
    summary.update(particle_design_library)
    summary.update(bfp_detector_operator)
    summary.update(polarization_jones)
    summary.update(bayesian_calibration)
    summary.update(tsuyama_bfp_reference)
    summary.update(reference_operating_point)
    summary.update(collection_operator_state)
    detector_noise_summary = build_detector_noise_diagnostics(
        sim_cfg,
        collection_operator=collection.get("collection_operator"),
        mean_shot_noise_std=summary.get("mean_shot_noise_std"),
        reference_enhancement_gain=summary.get(
            "mean_reference_to_scattering_amplitude_ratio"
        ),
    )
    summary.update(detector_noise_summary)
    reference.update(detector_noise_summary)
    run_state = build_run_state_diagnostics(summary, sim_cfg)
    summary.update(run_state)
    reference.update(run_state)
    background_field_summary = build_background_field_diagnostics(
        sim_cfg,
        e_sca_to_ref_amplitude_ratio_estimate=e_sca_to_ref_amplitude_ratio_estimate,
        extinction_to_beam_area_estimate=extinction_to_beam_area_estimate,
    )
    summary.update(background_field_summary)
    reference.update(background_field_summary)
    summary.update(particle_channel_perturbation)
    reference.update(particle_channel_perturbation)
    readout_convention_summary = build_readout_convention_diagnostics(sim_cfg)
    summary.update(readout_convention_summary)
    reference.update(readout_convention_summary)
    threshold_false_alarm_summary = build_threshold_false_alarm_diagnostics(
        sim_cfg,
        n_background_samples=summary.get("threshold_background_segment_samples"),
        mean_threshold_robust_std=summary.get("mean_threshold_robust_std"),
        mean_pod_threshold_robust_std=summary.get("mean_pod_threshold_robust_std"),
    )
    summary.update(threshold_false_alarm_summary)
    reference.update(threshold_false_alarm_summary)
    event_quality = build_event_quality_control_diagnostics(
        summary,
        sim_cfg,
        reference=reference,
    )
    summary.update(event_quality)
    reference.update(event_quality)
    engineering_gate = evaluate_engineering_gate(summary, sim_cfg)
    summary.update(engineering_gate)
    reference.update(engineering_gate)
    qc_conditioned_detection_rate = summary.get("detected_rate_after_event_qc")
    conditional_detection_rate_source = "detected_rate_after_event_qc"
    if qc_conditioned_detection_rate is None:
        qc_conditioned_detection_rate = summary.get("detection_rate")
        conditional_detection_rate_source = (
            "detection_rate_fallback_event_qc_unavailable"
        )
    blank_false_positive_rate_hz = None
    empirical_peak_far_per_min = reference.get(
        "empirical_peak_false_alarm_rate_per_minute"
    )
    if empirical_peak_far_per_min is not None:
        blank_false_positive_rate_hz = max(
            float(empirical_peak_far_per_min) / 60.0,
            0.0,
        )
    count_model_summary = build_count_model_diagnostics(
        particle,
        channel,
        sim_cfg,
        conditional_detection_rate=qc_conditioned_detection_rate,
        conditional_detection_rate_source=conditional_detection_rate_source,
        mean_transit_time_s=summary.get("mean_transit_time_s"),
        blank_false_positive_rate_Hz=blank_false_positive_rate_hz,
    )
    summary.update(count_model_summary)
    reference.update(count_model_summary)
    count_likelihood = build_count_likelihood_diagnostics(
        summary,
        count_model_summary,
        sim_cfg,
    )
    summary.update(count_likelihood)
    reference.update(count_likelihood)
    selection_function = build_selection_function_diagnostics(
        particle,
        summary,
        sim_cfg,
    )
    summary.update(selection_function)
    reference.update(selection_function)
    ev_population_prior = build_ev_population_prior_diagnostics(
        particle,
        {**reference, **summary},
        sim_cfg,
    )
    summary.update(ev_population_prior)
    reference.update(ev_population_prior)
    population_inference = build_population_inference_scaffold(
        {**reference, **summary}
    )
    summary.update(population_inference)
    reference.update(population_inference)
    ood_detection = build_ood_detection_diagnostics(
        particle,
        summary,
    )
    summary.update(ood_detection)
    reference.update(ood_detection)
    claim_governance = build_design_claim_governance_diagnostics(
        particle,
        channel,
        optical,
        sim_cfg,
        reference=reference,
        summary=summary,
    )
    summary.update(claim_governance)
    reference.update(claim_governance)
    experimental_design_advisor = build_experimental_design_advisor(
        {**reference, **summary}
    )
    summary.update(experimental_design_advisor)
    reference.update(experimental_design_advisor)
    observation_signature = _build_observation_signature(
        collection.get("operator_signature"),
        reference,
        sim_cfg,
        particle_radius_m=particle.radius_m,
    )

    return {
        "events": [] if summary_accumulator is not None else events,
        "summary": summary,
        "intrinsic": {
            "Csca_m2": intrinsic["Csca_m2"],
            "Cext_m2": intrinsic["Cext_m2"],
            "Cabs_m2": intrinsic["Cabs_m2"],
            **unit_axis_conventions,
            **mie_validation,
            **wavelength_comparability,
            **objective_profile,
            **objective_panel,
            **optical_exposure,
            **nodi_thermal_contamination,
            **polarization_jones,
            **ood_detection,
            **bayesian_calibration,
            **experimental_design_advisor,
            **population_inference,
            **channel_geometry,
            **trajectory_geometry,
            **electrokinetic_transport,
            **ev_integrity,
            **ev_reporting,
            **assay_controls,
            **control_interpretation,
            **recompute_manifest,
            **fluidic_resistance,
            **fluidic_network,
            **particle_design_library,
            **ev_population_prior,
            **bfp_detector_operator,
            **tsuyama_bfp_reference,
            **reference_operating_point,
            **particle_channel_perturbation,
            **event_quality,
            **selection_function,
            **run_state,
            **claim_governance,
            "E_sca_at_det": float(E_sca_at_det),
            "E_sca_at_det_complex": complex(E_sca_at_det_complex),
            "E_sca_ref": float(E_sca_ref),
            "E_sca_unit_normalized": float(abs(E_sca_unit_normalized)),
            "E_sca_unit_normalized_complex": complex(E_sca_unit_normalized),
            "phi_projection_rad": float(collection.get("phi_projection_rad", 0.0)),
            "phi_sca_material_rad": float(collection.get("phi_sca_material_rad", 0.0)),
            "phi_sca_material_parallel_rad": float(
                collection.get("phi_sca_material_parallel_rad", 0.0)
            ),
            "phi_sca_material_perpendicular_rad": float(
                collection.get("phi_sca_material_perpendicular_rad", 0.0)
            ),
            "theta_det_rad": float(theta_det),
            "theta_center_rad": float(collection["theta_center_rad"]),
            "sigma_effective_rad": float(collection.get("sigma_effective_rad", sim_cfg.collection_sigma_rad)),
            "operator_signature": collection.get("operator_signature"),
            "operator_route": collection.get("operator_route"),
            "operator_normalization": collection.get("operator_normalization"),
            "collection_operator_calibration_status": collection.get(
                "collection_operator_calibration_status"
            ),
            "collection_operator_coverage_status": collection.get(
                "collection_operator_coverage_status"
            ),
            "collection_operator_calibration_source": collection.get(
                "collection_operator_calibration_source"
            ),
            "collection_operator_id": collection.get("collection_operator_id"),
            "collection_operator_calibrated_geometry": collection.get(
                "collection_operator_calibrated_geometry"
            ),
            "collection_operator_max_relative_geometry_distance": collection.get(
                "collection_operator_max_relative_geometry_distance"
            ),
            **{
                field: collection.get(field)
                for field in _COLLECTION_OPERATOR_EXTRA_FIELDS
            },
            "surrogate_throughput_scale": collection.get("surrogate_throughput_scale"),
            "observation_signature": observation_signature,
            "scattering_projection_basis": scattering_projection_basis,
            **{field: reference.get(field) for field in _PARTICLE_MODEL_DIAGNOSTIC_FIELDS},
            **{field: reference.get(field) for field in _INTERFACE_CORRECTION_DIAGNOSTIC_FIELDS},
            **{field: reference.get(field) for field in _COUNT_MODEL_DIAGNOSTIC_FIELDS},
            **{
                field: reference.get(field)
                for field in COUNT_LIKELIHOOD_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in POPULATION_INFERENCE_DIAGNOSTIC_FIELDS
            },
            **{field: reference.get(field) for field in OOD_DIAGNOSTIC_FIELDS},
            **{
                field: reference.get(field)
                for field in BAYESIAN_CALIBRATION_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in EXPERIMENTAL_DESIGN_ADVISOR_FIELDS
            },
            "detector_forward_model": reference.get("detector_forward_model"),
            "detector_forward_status": reference.get("detector_forward_status"),
            "detector_forward_claim_level": reference.get("detector_forward_claim_level"),
            "detector_mode_definition": reference.get("detector_mode_definition"),
            "joint_overlap_used": reference.get("joint_overlap_used"),
            "field_coordinate_measure": reference.get("field_coordinate_measure"),
            "field_measure_status": reference.get("field_measure_status"),
            "field_measure_normalization_claim": reference.get(
                "field_measure_normalization_claim"
            ),
            "bfp_to_angle_jacobian_applied": reference.get(
                "bfp_to_angle_jacobian_applied"
            ),
            "detector_mask_units": reference.get("detector_mask_units"),
            "coordinate_frame_mapping": reference.get("coordinate_frame_mapping"),
            "coordinate_frame_mapping_status": reference.get(
                "coordinate_frame_mapping_status"
            ),
            "complex_time_harmonic_convention": reference.get(
                "complex_time_harmonic_convention"
            ),
            "fourier_transform_sign_convention": reference.get(
                "fourier_transform_sign_convention"
            ),
            "mie_amplitude_phase_convention": reference.get(
                "mie_amplitude_phase_convention"
            ),
            "interference_conjugation_convention": reference.get(
                "interference_conjugation_convention"
            ),
            "interference_cross_term_convention": reference.get(
                "interference_cross_term_convention"
            ),
            "global_phase_offset_source": reference.get("global_phase_offset_source"),
            "complex_reference_absolute_phase_locked": reference.get(
                "complex_reference_absolute_phase_locked"
            ),
            "absolute_polarity_claim": reference.get("absolute_polarity_claim"),
            "complex_convention_status": reference.get("complex_convention_status"),
            "complex_field_claim_level": reference.get("complex_field_claim_level"),
            "polarization_basis_model": reference.get("polarization_basis_model"),
            "jones_basis_status": reference.get("jones_basis_status"),
            "vector_optics_mode": reference.get("vector_optics_mode"),
            "mie_s1_s2_lab_basis_mapping": reference.get(
                "mie_s1_s2_lab_basis_mapping"
            ),
            "active_mie_basis_component": reference.get("active_mie_basis_component"),
            "S1S2_to_lab_basis_rotation_applied": reference.get(
                "S1S2_to_lab_basis_rotation_applied"
            ),
            "reference_jones_field_defined": reference.get(
                "reference_jones_field_defined"
            ),
            "detector_analyzer_jones_matrix_defined": reference.get(
                "detector_analyzer_jones_matrix_defined"
            ),
            "mie_jones_bridge_status": reference.get("mie_jones_bridge_status"),
            "NA_collection_for_vector_warning": reference.get(
                "NA_collection_for_vector_warning"
            ),
            "high_NA_collection_warning": reference.get("high_NA_collection_warning"),
            "vector_validity_status": reference.get("vector_validity_status"),
            "mie_intrinsic_complex_fields_available": reference.get(
                "mie_intrinsic_complex_fields_available"
            ),
            **{
                field: reference.get(field)
                for field in _MIE_INCIDENT_FIELD_DIAGNOSTIC_FIELDS
            },
            "calibration_state_machine_version": reference.get(
                "calibration_state_machine_version"
            ),
            "calibration_state_machine_status": reference.get(
                "calibration_state_machine_status"
            ),
            "output_claim_level": reference.get("output_claim_level"),
            "calibrated_quantitative_unlocked": reference.get(
                "calibrated_quantitative_unlocked"
            ),
            "output_claim_blocker_summary": reference.get(
                "output_claim_blocker_summary"
            ),
            "reference_calibration_level": reference.get(
                "reference_calibration_level"
            ),
            "reference_phase_calibration_level": reference.get(
                "reference_phase_calibration_level"
            ),
            "scattering_normalization_route": reference.get(
                "scattering_normalization_route"
            ),
            "scattering_normalization_status": reference.get(
                "scattering_normalization_status"
            ),
            "scattering_normalization_claim": reference.get(
                "scattering_normalization_claim"
            ),
            "scattering_calibration_level": reference.get(
                "scattering_calibration_level"
            ),
            "baseline_normalization_role": reference.get(
                "baseline_normalization_role"
            ),
            "baseline_particle_absolute_scale_restored": reference.get(
                "baseline_particle_absolute_scale_restored"
            ),
            "baseline_normalized_E_sca_allowed_in_photon_unit_route": reference.get(
                "baseline_normalized_E_sca_allowed_in_photon_unit_route"
            ),
            "baseline_normalized_E_sca_allowed_in_detector_unit_route": reference.get(
                "baseline_normalized_E_sca_allowed_in_detector_unit_route"
            ),
            "E_sca_ref_normalization_role": reference.get(
                "E_sca_ref_normalization_role"
            ),
            "K_sca_calibration_status": reference.get("K_sca_calibration_status"),
            "K_sca_value": reference.get("K_sca_value"),
            "K_sca_scope": reference.get("K_sca_scope"),
            "K_sca_role": reference.get("K_sca_role"),
            "mie_to_power_chain_status": reference.get("mie_to_power_chain_status"),
            "mie_differential_cross_section_source": reference.get(
                "mie_differential_cross_section_source"
            ),
            "scattered_power_conversion_status": reference.get(
                "scattered_power_conversion_status"
            ),
            "detector_field_units": reference.get("detector_field_units"),
            "detector_voltage_units": reference.get("detector_voltage_units"),
            "power_chain_absolute_units_available": reference.get(
                "power_chain_absolute_units_available"
            ),
            "K_sca_power_chain_role": reference.get("K_sca_power_chain_role"),
            "mie_to_power_chain_blocker_summary": reference.get(
                "mie_to_power_chain_blocker_summary"
            ),
            "standard_particle_calibration_status": reference.get(
                "standard_particle_calibration_status"
            ),
            "standard_particle_calibration_path_configured": reference.get(
                "standard_particle_calibration_path_configured"
            ),
            "standard_particle_calibration_source": reference.get(
                "standard_particle_calibration_source"
            ),
            "standard_particle_calibration_id": reference.get(
                "standard_particle_calibration_id"
            ),
            "standard_particle_calibration_coverage_status": reference.get(
                "standard_particle_calibration_coverage_status"
            ),
            "standard_particle_calibration_table_status": reference.get(
                "standard_particle_calibration_table_status"
            ),
            "standard_particle_calibration_max_relative_distance": reference.get(
                "standard_particle_calibration_max_relative_distance"
            ),
            "global_phase_offset_rad": reference.get("global_phase_offset_rad"),
            "global_phase_offset_calibration_status": reference.get(
                "global_phase_offset_calibration_status"
            ),
            "K_sca_uncertainty_status": reference.get("K_sca_uncertainty_status"),
            "K_sca_uncertainty_required_inputs": reference.get(
                "K_sca_uncertainty_required_inputs"
            ),
            "K_sca_uncertainty_propagated_to_outputs": reference.get(
                "K_sca_uncertainty_propagated_to_outputs"
            ),
            "standard_particle_uncertainty_budget_status": reference.get(
                "standard_particle_uncertainty_budget_status"
            ),
            "standard_particle_size_distribution_status": reference.get(
                "standard_particle_size_distribution_status"
            ),
            "standard_particle_shape_uncertainty_status": reference.get(
                "standard_particle_shape_uncertainty_status"
            ),
            "standard_particle_ligand_shell_status": reference.get(
                "standard_particle_ligand_shell_status"
            ),
            "standard_particle_batch_status": reference.get(
                "standard_particle_batch_status"
            ),
            "standard_particle_concentration_uncertainty_status": reference.get(
                "standard_particle_concentration_uncertainty_status"
            ),
            "standard_particle_material_dataset_uncertainty_status": reference.get(
                "standard_particle_material_dataset_uncertainty_status"
            ),
            "K_sca_uncertainty_blocker_summary": reference.get(
                "K_sca_uncertainty_blocker_summary"
            ),
            "calibration_design_rank": reference.get("calibration_design_rank"),
            "calibration_design_rank_reason": reference.get(
                "calibration_design_rank_reason"
            ),
            "calibration_standard_count": reference.get("calibration_standard_count"),
            "calibration_wavelength_count": reference.get(
                "calibration_wavelength_count"
            ),
            "calibration_geometry_count": reference.get("calibration_geometry_count"),
            "calibration_held_out_validation_status": reference.get(
                "calibration_held_out_validation_status"
            ),
            "calibration_held_out_error": reference.get("calibration_held_out_error"),
            "calibration_identifiability_blocker_summary": reference.get(
                "calibration_identifiability_blocker_summary"
            ),
            "calibration_fit_parameter_coupling_status": reference.get(
                "calibration_fit_parameter_coupling_status"
            ),
            "calibration_design_minimum_requirement_status": reference.get(
                "calibration_design_minimum_requirement_status"
            ),
            "fit_parameters_identifiable": reference.get(
                "fit_parameters_identifiable"
            ),
            "detector_calibration_level": reference.get("detector_calibration_level"),
            "readout_calibration_level": reference.get("readout_calibration_level"),
            "count_calibration_level": reference.get("count_calibration_level"),
            **{
                field: reference.get(field)
                for field in _CALIBRATION_STATE_EXTRA_FIELDS
            },
            "noise_model_route": reference.get("noise_model_route"),
            "detector_noise_claim_level": reference.get("detector_noise_claim_level"),
            "detector_signal_unit_convention": reference.get(
                "detector_signal_unit_convention"
            ),
            "absolute_throughput_route": reference.get("absolute_throughput_route"),
            "absolute_throughput_calibrated": reference.get(
                "absolute_throughput_calibrated"
            ),
            "photon_unit_noise_model": reference.get("photon_unit_noise_model"),
            "photon_unit_noise_model_status": reference.get(
                "photon_unit_noise_model_status"
            ),
            "photon_count_route_active": reference.get("photon_count_route_active"),
            "lockin_ENBW_Hz": reference.get("lockin_ENBW_Hz"),
            "lockin_ENBW_status": reference.get("lockin_ENBW_status"),
            "lockin_ENBW_claim_level": reference.get("lockin_ENBW_claim_level"),
            "shot_noise_model_status": reference.get("shot_noise_model_status"),
            "photon_shot_noise_term_status": reference.get(
                "photon_shot_noise_term_status"
            ),
            "shot_noise_limited_snr": reference.get("shot_noise_limited_snr"),
            "electronics_noise_model_status": reference.get(
                "electronics_noise_model_status"
            ),
            "electronics_noise_term_status": reference.get(
                "electronics_noise_term_status"
            ),
            "electronics_noise_limited_snr": reference.get(
                "electronics_noise_limited_snr"
            ),
            "rin_noise_model_status": reference.get("rin_noise_model_status"),
            "rin_noise_term_status": reference.get("rin_noise_term_status"),
            "rin_limited_snr": reference.get("rin_limited_snr"),
            "speckle_background_noise_model_status": reference.get(
                "speckle_background_noise_model_status"
            ),
            "speckle_like_noise_term_status": reference.get(
                "speckle_like_noise_term_status"
            ),
            "drift_noise_model_status": reference.get("drift_noise_model_status"),
            "drift_noise_term_status": reference.get("drift_noise_term_status"),
            "post_readout_noise_model_status": reference.get(
                "post_readout_noise_model_status"
            ),
            "lockin_output_noise_term_status": reference.get(
                "lockin_output_noise_term_status"
            ),
            "noise_terms_schema_version": reference.get("noise_terms_schema_version"),
            "noise_term_quantitative_contribution_status": reference.get(
                "noise_term_quantitative_contribution_status"
            ),
            "noise_terms": reference.get("noise_terms"),
            "detector_dynamic_range_model": reference.get(
                "detector_dynamic_range_model"
            ),
            "detector_saturation_status": reference.get("detector_saturation_status"),
            "detector_saturation_margin": reference.get("detector_saturation_margin"),
            "ADC_dynamic_range_status": reference.get("ADC_dynamic_range_status"),
            "ADC_dynamic_range_margin": reference.get("ADC_dynamic_range_margin"),
            "dynamic_range_margin": reference.get("dynamic_range_margin"),
            "blank_trace_noise_model_fit_quality": reference.get(
                "blank_trace_noise_model_fit_quality"
            ),
            "reference_enhancement_gain": reference.get("reference_enhancement_gain"),
            "reference_enhancement_snr_claim": reference.get(
                "reference_enhancement_snr_claim"
            ),
            "background_field_model": reference.get("background_field_model"),
            "background_field_status": reference.get("background_field_status"),
            "background_claim_level": reference.get("background_claim_level"),
            "background_subtraction_status": reference.get(
                "background_subtraction_status"
            ),
            "residual_transmitted_leakage_model": reference.get(
                "residual_transmitted_leakage_model"
            ),
            "residual_transmitted_leakage_status": reference.get(
                "residual_transmitted_leakage_status"
            ),
            "transmitted_leakage_model": reference.get("transmitted_leakage_model"),
            "stray_light_model": reference.get("stray_light_model"),
            "stray_light_status": reference.get("stray_light_status"),
            "speckle_like_background_status": reference.get(
                "speckle_like_background_status"
            ),
            "blank_trace_provenance": reference.get("blank_trace_provenance"),
            "blank_trace_empirical_available": reference.get(
                "blank_trace_empirical_available"
            ),
            "particle_induced_channel_perturbation_model": reference.get(
                "particle_induced_channel_perturbation_model"
            ),
            "particle_induced_channel_phase_perturbation_status": reference.get(
                "particle_induced_channel_phase_perturbation_status"
            ),
            "independent_superposition_status": reference.get(
                "independent_superposition_status"
            ),
            "weak_superposition_validity_status": reference.get(
                "weak_superposition_validity_status"
            ),
            "superposition_validity_status": reference.get(
                "superposition_validity_status"
            ),
            "E_sca_to_E_ref_amplitude_ratio_estimate": reference.get(
                "E_sca_to_E_ref_amplitude_ratio_estimate"
            ),
            "extinction_to_beam_area_estimate": reference.get(
                "extinction_to_beam_area_estimate"
            ),
            "reference_depletion_fraction_estimate": reference.get(
                "reference_depletion_fraction_estimate"
            ),
            "reference_depletion_estimate_status": reference.get(
                "reference_depletion_estimate_status"
            ),
            "channel_particle_coupling_model": reference.get(
                "channel_particle_coupling_model"
            ),
            "joint_fullwave_required_for_quantitative_phase": reference.get(
                "joint_fullwave_required_for_quantitative_phase"
            ),
            "superposition_validity_claim_level": reference.get(
                "superposition_validity_claim_level"
            ),
            "superposition_validity_blocker_summary": reference.get(
                "superposition_validity_blocker_summary"
            ),
            "nodi_signal_component_model": reference.get("nodi_signal_component_model"),
            "nodi_signal_component_status": reference.get("nodi_signal_component_status"),
            "nodi_forward_extinction_leakage_status": reference.get(
                "nodi_forward_extinction_leakage_status"
            ),
            "nodi_transmitted_leakage_component_status": reference.get(
                "nodi_transmitted_leakage_component_status"
            ),
            "nodi_particle_induced_channel_coupling_status": reference.get(
                "nodi_particle_induced_channel_coupling_status"
            ),
            "nodi_signal_component_claim_level": reference.get(
                "nodi_signal_component_claim_level"
            ),
            "nodi_component_escalation_route": reference.get(
                "nodi_component_escalation_route"
            ),
            "readout_preset": reference.get("readout_preset"),
            "readout_preset_status": reference.get("readout_preset_status"),
            "readout_preset_claim_level": reference.get("readout_preset_claim_level"),
            "readout_preset_threshold_scope": reference.get(
                "readout_preset_threshold_scope"
            ),
            "readout_shared_threshold_profile": reference.get(
                "readout_shared_threshold_profile"
            ),
            "readout_lane_specific_thresholds_available": reference.get(
                "readout_lane_specific_thresholds_available"
            ),
            "readout_preset_frequency_leakage_note": reference.get(
                "readout_preset_frequency_leakage_note"
            ),
            "readout_paper_time_constant_range_s": reference.get(
                "readout_paper_time_constant_range_s"
            ),
            "electronics_demod_phase_policy": reference.get(
                "electronics_demod_phase_policy"
            ),
            "effective_electronics_demod_phase_policy": reference.get(
                "effective_electronics_demod_phase_policy"
            ),
            "readout_reference_phase_source": reference.get(
                "readout_reference_phase_source"
            ),
            "readout_polarity": reference.get("readout_polarity"),
            "polarity_source": reference.get("polarity_source"),
            "arrival_phase_distribution": reference.get(
                "arrival_phase_distribution"
            ),
            "readout_internal_sampling_rate_Hz": reference.get(
                "readout_internal_sampling_rate_Hz"
            ),
            "readout_output_sampling_rate_Hz": reference.get(
                "readout_output_sampling_rate_Hz"
            ),
            "readout_max_lockin_frequency_Hz": reference.get(
                "readout_max_lockin_frequency_Hz"
            ),
            "readout_sampling_oversampling_ratio": reference.get(
                "readout_sampling_oversampling_ratio"
            ),
            "readout_sampling_required_rate_Hz": reference.get(
                "readout_sampling_required_rate_Hz"
            ),
            "readout_sampling_hard_gate_passed": reference.get(
                "readout_sampling_hard_gate_passed"
            ),
            "readout_frequency_dependent_paper_conclusion_allowed": reference.get(
                "readout_frequency_dependent_paper_conclusion_allowed"
            ),
            "readout_sampling_claim_level": reference.get(
                "readout_sampling_claim_level"
            ),
            "readout_carrier_nyquist_resolved": reference.get(
                "readout_carrier_nyquist_resolved"
            ),
            "readout_carrier_resolved": reference.get("readout_carrier_resolved"),
            "readout_carrier_resolved_with_margin": reference.get(
                "readout_carrier_resolved_with_margin"
            ),
            "readout_analytic_demod_used": reference.get(
                "readout_analytic_demod_used"
            ),
            "readout_internal_demod_route": reference.get(
                "readout_internal_demod_route"
            ),
            "readout_anti_alias_policy": reference.get("readout_anti_alias_policy"),
            "readout_anti_alias_filter_before_downsample": reference.get(
                "readout_anti_alias_filter_before_downsample"
            ),
            "lockin_output_grid_matches_data_logger": reference.get(
                "lockin_output_grid_matches_data_logger"
            ),
            "readout_sampling_validity": reference.get("readout_sampling_validity"),
            "lockin_output_unit_convention": reference.get(
                "lockin_output_unit_convention"
            ),
            "lockin_gain_chain": reference.get("lockin_gain_chain"),
            "lockin_reported_channel": reference.get("lockin_reported_channel"),
            "lockin_reported_channel_source": reference.get(
                "lockin_reported_channel_source"
            ),
            "lockin_measured_voltage_comparable": reference.get(
                "lockin_measured_voltage_comparable"
            ),
            "readout_model_claim_level": reference.get("readout_model_claim_level"),
            "pod_source_model_status": reference.get("pod_source_model_status"),
            "nodi_source_model_status": reference.get("nodi_source_model_status"),
            **{
                field: reference.get(field)
                for field in _PHOTOTHERMAL_POD_DIAGNOSTIC_FIELDS
            },
            "threshold_sigma": reference.get("threshold_sigma"),
            "threshold_sigma_nodi": reference.get("threshold_sigma_nodi"),
            "threshold_sigma_pod": reference.get("threshold_sigma_pod"),
            "threshold_lane_specific_model": reference.get(
                "threshold_lane_specific_model"
            ),
            "threshold_tail": reference.get("threshold_tail"),
            "threshold_tail_status": reference.get("threshold_tail_status"),
            "threshold_false_alarm_tail_count": reference.get(
                "threshold_false_alarm_tail_count"
            ),
            "threshold_sign": reference.get("threshold_sign"),
            "threshold_polarity_mode": reference.get("threshold_polarity_mode"),
            "target_false_alarm_rate": reference.get("target_false_alarm_rate"),
            "threshold_from_blank_trace": reference.get("threshold_from_blank_trace"),
            "threshold_from_event_background_segment": reference.get(
                "threshold_from_event_background_segment"
            ),
            "threshold_background_source": reference.get("threshold_background_source"),
            "threshold_background_segment_samples": reference.get(
                "threshold_background_segment_samples"
            ),
            "threshold_calibration_source": reference.get(
                "threshold_calibration_source"
            ),
            "threshold_calibration_status": reference.get(
                "threshold_calibration_status"
            ),
            "blank_false_positive_calibration_status": reference.get(
                "blank_false_positive_calibration_status"
            ),
            "blank_false_positive_calibration_source": reference.get(
                "blank_false_positive_calibration_source"
            ),
            "blank_false_positive_calibration_id": reference.get(
                "blank_false_positive_calibration_id"
            ),
            "gaussian_iid_single_sample_false_alarm_probability": reference.get(
                "gaussian_iid_single_sample_false_alarm_probability"
            ),
            "gaussian_iid_background_segment_false_alarm_probability": reference.get(
                "gaussian_iid_background_segment_false_alarm_probability"
            ),
            "mean_threshold_robust_std": reference.get("mean_threshold_robust_std"),
            "mean_pod_threshold_robust_std": reference.get(
                "mean_pod_threshold_robust_std"
            ),
            "blank_trace_autocorrelation_time_s": reference.get(
                "blank_trace_autocorrelation_time_s"
            ),
            "effective_independent_samples_per_trace": reference.get(
                "effective_independent_samples_per_trace"
            ),
            "lockin_filter_order": reference.get("lockin_filter_order"),
            "empirical_peak_false_alarm_rate_per_minute": reference.get(
                "empirical_peak_false_alarm_rate_per_minute"
            ),
            "empirical_pair_false_alarm_rate_per_minute": reference.get(
                "empirical_pair_false_alarm_rate_per_minute"
            ),
            "lane_noise_correlation_coefficient": reference.get(
                "lane_noise_correlation_coefficient"
            ),
            "colored_noise_false_alarm_model": reference.get(
                "colored_noise_false_alarm_model"
            ),
            "colored_noise_false_alarm_status": reference.get(
                "colored_noise_false_alarm_status"
            ),
            "colored_noise_surrogate_components": reference.get(
                "colored_noise_surrogate_components"
            ),
            "colored_noise_threshold_bias": reference.get(
                "colored_noise_threshold_bias"
            ),
            "colored_noise_threshold_bias_status": reference.get(
                "colored_noise_threshold_bias_status"
            ),
            "paired_false_alarm_status": reference.get("paired_false_alarm_status"),
            **{
                field: reference.get(field)
                for field in _THRESHOLD_FALSE_ALARM_EXTRA_FIELDS
            },
            "interference_overlap_mode": overlap_diagnostics.get("interference_overlap_mode"),
            "interference_overlap_status": overlap_diagnostics.get("interference_overlap_status"),
            "interference_overlap_factor_abs": float(
                abs(overlap_diagnostics.get("interference_overlap_factor_complex", 1.0 + 0.0j))
            ),
            "interference_overlap_factor_phase_rad": float(
                np.angle(overlap_diagnostics.get("interference_overlap_factor_complex", 1.0 + 0.0j))
            ),
            "path_opd_model": first_event_defaults.get("path_opd_model", sim_cfg.path_opd_model),
            "path_opd_reference_plane": first_event_defaults.get("path_opd_reference_plane", "unknown"),
            "path_opd_z_geometry_factor": float(
                first_event_defaults.get("path_opd_z_geometry_factor", 1.0)
            ),
            "path_opd_z_reference_mode": first_event_defaults.get(
                "path_opd_z_reference_mode",
                "unknown",
            ),
            "path_opd_default_model": first_event_defaults.get(
                "path_opd_default_model",
                sim_cfg.path_opd_model,
            ),
            "path_opd_model_role": first_event_defaults.get(
                "path_opd_model_role",
                "unknown",
            ),
            "path_opd_default_frozen": bool(
                first_event_defaults.get("path_opd_default_frozen", True)
            ),
            "path_opd_freeze_status": summary.get("path_opd_freeze_status"),
            "initial_position_distribution_mode": summary.get(
                "initial_position_distribution_mode"
            ),
            "initial_position_distribution_active_fraction": summary.get(
                "initial_position_distribution_active_fraction"
            ),
            "mean_abs_initial_x_norm": summary.get("mean_abs_initial_x_norm"),
            "mean_abs_initial_z_norm": summary.get("mean_abs_initial_z_norm"),
            "mean_initial_position_confinement_ratio": summary.get(
                "mean_initial_position_confinement_ratio"
            ),
            "mean_initial_position_confinement_activation": summary.get(
                "mean_initial_position_confinement_activation"
            ),
            "mean_initial_position_center_bias_x_exponent": summary.get(
                "mean_initial_position_center_bias_x_exponent"
            ),
            "mean_initial_position_center_bias_z_exponent": summary.get(
                "mean_initial_position_center_bias_z_exponent"
            ),
        },
        "reference": {
            "A_ref": reference["A_ref"],
            "g_ref": reference.get("g_ref", 1.0),
            "g_ref_geometry": reference.get("g_ref_geometry", reference.get("g_ref", 1.0)),
            "phi_ref_rad": reference["phi_ref_rad"],
            "reference_route": reference.get("reference_route"),
            "reference_route_requested": reference.get("reference_route_requested"),
            "reference_route_request_status": reference.get(
                "reference_route_request_status"
            ),
            **{
                field: reference.get(field)
                for field in DESIGN_CLAIM_GOVERNANCE_FIELDS
            },
            **{
                field: reference.get(field)
                for field in EVENT_QC_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in SELECTION_FUNCTION_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in EV_POPULATION_PRIOR_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in POPULATION_INFERENCE_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in NODI_THERMAL_CONTAMINATION_FIELDS
            },
            **{
                field: reference.get(field)
                for field in POLARIZATION_JONES_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in RUN_STATE_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in CHANNEL_GEOMETRY_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in TRAJECTORY_GEOMETRY_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in ELECTROKINETIC_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in EV_INTEGRITY_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in EV_REPORTING_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in ASSAY_CONTROL_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in RECOMPUTE_MANIFEST_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in BFP_DETECTOR_OPERATOR_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in _COLLECTION_OPERATOR_EXTRA_FIELDS
            },
            **{
                field: reference.get(field)
                for field in PARTICLE_CHANNEL_PERTURBATION_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in FLUIDIC_RESISTANCE_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in PARTICLE_DESIGN_LIBRARY_DIAGNOSTIC_FIELDS
            },
            "reference_route_role": reference.get("reference_route_role"),
            "reference_claim_level": reference.get("reference_claim_level"),
            "reference_solver_route": reference.get("reference_solver_route"),
            "reference_solver_status": reference.get("reference_solver_status"),
            "reference_solver_detector_bridge_status": reference.get(
                "reference_solver_detector_bridge_status"
            ),
            "reference_solver_active_field_source": reference.get(
                "reference_solver_active_field_source"
            ),
            "paper_aligned_reference_claim": reference.get(
                "paper_aligned_reference_claim"
            ),
            "reference_solver_claim_level": reference.get("reference_solver_claim_level"),
            "reference_field_decomposition_status": reference.get(
                "reference_field_decomposition_status"
            ),
            "phi_ref_model_rad": reference.get("phi_ref_model_rad"),
            "phi_ref_model_source": reference.get("phi_ref_model_source"),
            "theta_signed_rad": reference.get("theta_signed_rad"),
            "thin_phase_perturbation_phase_rad": reference.get(
                "thin_phase_perturbation_phase_rad"
            ),
            "phase_delay_over_2_role": reference.get("phase_delay_over_2_role"),
            "polarity_claim_from_phase_delay_over_2_allowed": reference.get(
                "polarity_claim_from_phase_delay_over_2_allowed"
            ),
            "reference_absolute_polarity_claim": reference.get(
                "reference_absolute_polarity_claim"
            ),
            "reference_active_phase_source": reference.get("reference_active_phase_source"),
            "phase_filter_validity": reference.get("phase_filter_validity"),
            "phase_filter_H_over_lambda0": reference.get("phase_filter_H_over_lambda0"),
            "phase_filter_delta_ref_rad": reference.get("phase_filter_delta_ref_rad"),
            "phase_filter_theta_signed_rad": reference.get(
                "phase_filter_theta_signed_rad"
            ),
            "phase_filter_H_over_zR": reference.get("phase_filter_H_over_zR"),
            "phase_filter_multiple_reflection_warning": reference.get(
                "phase_filter_multiple_reflection_warning"
            ),
            "subwavelength_groove_validity_status": reference.get(
                "subwavelength_groove_validity_status"
            ),
            "finite_length_assumption_status": reference.get(
                "finite_length_assumption_status"
            ),
            "sidewall_scattering_roughness_status": reference.get(
                "sidewall_scattering_roughness_status"
            ),
            "evanescent_component_unmodeled": reference.get(
                "evanescent_component_unmodeled"
            ),
            "groove_waveguide_mode_unmodeled": reference.get(
                "groove_waveguide_mode_unmodeled"
            ),
            "roughness_scatter_unmodeled": reference.get(
                "roughness_scatter_unmodeled"
            ),
            "depth_validity_reason": reference.get("depth_validity_reason"),
            "requires_calibration_or_fullwave": reference.get(
                "requires_calibration_or_fullwave"
            ),
            "reference_calibration_amplitude_status": reference.get(
                "reference_calibration_amplitude_status"
            ),
            "reference_calibration_amplitude_source": reference.get(
                "reference_calibration_amplitude_source"
            ),
            "rho_used_for_reference_amplitude": reference.get(
                "rho_used_for_reference_amplitude"
            ),
            "reference_calibration_coverage_status": reference.get(
                "reference_calibration_coverage_status"
            ),
            "reference_phase_calibration_status": reference.get(
                "reference_phase_calibration_status"
            ),
            "reference_phase_absolute_claim": reference.get(
                "reference_phase_absolute_claim"
            ),
            "phi_ref_source": reference.get("phi_ref_source"),
            "phi_ref_confidence": reference.get("phi_ref_confidence"),
            "phase_wrap_policy": reference.get("phase_wrap_policy"),
            **{
                field: reference.get(field)
                for field in _REFERENCE_CALIBRATION_EXTRA_FIELDS
            },
            **{field: reference.get(field) for field in _PARTICLE_MODEL_DIAGNOSTIC_FIELDS},
            **{field: reference.get(field) for field in _INTERFACE_CORRECTION_DIAGNOSTIC_FIELDS},
            **{field: reference.get(field) for field in _COUNT_MODEL_DIAGNOSTIC_FIELDS},
            **{
                field: reference.get(field)
                for field in COUNT_LIKELIHOOD_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in POPULATION_INFERENCE_DIAGNOSTIC_FIELDS
            },
            **{field: reference.get(field) for field in OOD_DIAGNOSTIC_FIELDS},
            **{
                field: reference.get(field)
                for field in BAYESIAN_CALIBRATION_DIAGNOSTIC_FIELDS
            },
            **{
                field: reference.get(field)
                for field in EXPERIMENTAL_DESIGN_ADVISOR_FIELDS
            },
            "detector_forward_model": reference.get("detector_forward_model"),
            "detector_forward_status": reference.get("detector_forward_status"),
            "detector_forward_equation": reference.get("detector_forward_equation"),
            "detector_forward_claim_level": reference.get("detector_forward_claim_level"),
            "detector_forward_photon_units": reference.get(
                "detector_forward_photon_units"
            ),
            "detector_mode_definition": reference.get("detector_mode_definition"),
            "joint_overlap_used": reference.get("joint_overlap_used"),
            "collapsed_scalar_error_estimate_available": reference.get(
                "collapsed_scalar_error_estimate_available"
            ),
            "field_coordinate_measure": reference.get("field_coordinate_measure"),
            "field_measure_status": reference.get("field_measure_status"),
            "field_measure_normalization_claim": reference.get(
                "field_measure_normalization_claim"
            ),
            "bfp_to_angle_jacobian_applied": reference.get(
                "bfp_to_angle_jacobian_applied"
            ),
            "detector_mask_units": reference.get("detector_mask_units"),
            "coordinate_frame_mapping": reference.get("coordinate_frame_mapping"),
            "coordinate_frame_mapping_status": reference.get(
                "coordinate_frame_mapping_status"
            ),
            "particle_size_input_convention": reference.get(
                "particle_size_input_convention"
            ),
            "particle_size_convention": reference.get("particle_size_convention"),
            "particle_radius_m": reference.get("particle_radius_m"),
            "particle_diameter_m": reference.get("particle_diameter_m"),
            "size_convention_validated": reference.get("size_convention_validated"),
            "unit_axis_convention_status": reference.get(
                "unit_axis_convention_status"
            ),
            "unit_axis_convention_hard_gate_passed": reference.get(
                "unit_axis_convention_hard_gate_passed"
            ),
            "channel_width_axis": reference.get("channel_width_axis"),
            "channel_depth_axis": reference.get("channel_depth_axis"),
            "flow_axis_convention": reference.get("flow_axis_convention"),
            "optical_axis_convention": reference.get("optical_axis_convention"),
            "axis_convention_status": reference.get("axis_convention_status"),
            "mie_validation_status": reference.get("mie_validation_status"),
            "mie_validation_hard_gate_passed": reference.get(
                "mie_validation_hard_gate_passed"
            ),
            "mie_amplitude_normalization_status": reference.get(
                "mie_amplitude_normalization_status"
            ),
            **{
                field: reference.get(field)
                for field in WAVELENGTH_COMPARABILITY_DIAGNOSTIC_FIELDS
            },
            "objective_candidate_id": reference.get("objective_candidate_id"),
            "objective_candidate_requested_id": reference.get(
                "objective_candidate_requested_id"
            ),
            "objective_profile_schema_present": reference.get(
                "objective_profile_schema_present"
            ),
            "objective_profile_known": reference.get("objective_profile_known"),
            "objective_illumination_NA": reference.get("objective_illumination_NA"),
            "objective_collection_NA": reference.get("objective_collection_NA"),
            "objective_working_distance_mm": reference.get(
                "objective_working_distance_mm"
            ),
            "illumination_waist_m": reference.get("illumination_waist_m"),
            "depth_of_focus_m": reference.get("depth_of_focus_m"),
            "objective_transit_time_s": reference.get("objective_transit_time_s"),
            "lockin_bandwidth_margin": reference.get("lockin_bandwidth_margin"),
            "position_sensitivity_score": reference.get("position_sensitivity_score"),
            "working_distance_compatibility": reference.get(
                "working_distance_compatibility"
            ),
            "objective_design_claim_level": reference.get(
                "objective_design_claim_level"
            ),
            "objective_cross_profile_claim_allowed": reference.get(
                "objective_cross_profile_claim_allowed"
            ),
            "objective_profile_gate_passed": reference.get(
                "objective_profile_gate_passed"
            ),
            **{
                field: reference.get(field)
                for field in OBJECTIVE_PANEL_DIAGNOSTIC_FIELDS
            },
            "laser_power_density_W_m2": reference.get("laser_power_density_W_m2"),
            "particle_absorbed_power_proxy": reference.get(
                "particle_absorbed_power_proxy"
            ),
            "medium_absorption_heating_proxy": reference.get(
                "medium_absorption_heating_proxy"
            ),
            "wall_heating_proxy": reference.get("wall_heating_proxy"),
            "estimated_temperature_rise_K_surrogate": reference.get(
                "estimated_temperature_rise_K_surrogate"
            ),
            "ev_photodamage_risk_band": reference.get("ev_photodamage_risk_band"),
            "bubble_or_thermal_lens_artifact_risk": reference.get(
                "bubble_or_thermal_lens_artifact_risk"
            ),
            "au_standard_thermal_artifact_risk": reference.get(
                "au_standard_thermal_artifact_risk"
            ),
            "safe_power_claim_level": reference.get("safe_power_claim_level"),
            "optical_exposure_safety_gate_passed": reference.get(
                "optical_exposure_safety_gate_passed"
            ),
            "exposure_safety_not_red": reference.get("exposure_safety_not_red"),
            "chip_frame_axes": reference.get("chip_frame_axes"),
            "optical_frame_axes": reference.get("optical_frame_axes"),
            "bfp_frame_axes": reference.get("bfp_frame_axes"),
            "complex_time_harmonic_convention": reference.get(
                "complex_time_harmonic_convention"
            ),
            "fourier_transform_sign_convention": reference.get(
                "fourier_transform_sign_convention"
            ),
            "mie_amplitude_phase_convention": reference.get(
                "mie_amplitude_phase_convention"
            ),
            "interference_conjugation_convention": reference.get(
                "interference_conjugation_convention"
            ),
            "interference_cross_term_convention": reference.get(
                "interference_cross_term_convention"
            ),
            "global_phase_offset_source": reference.get("global_phase_offset_source"),
            "complex_reference_absolute_phase_locked": reference.get(
                "complex_reference_absolute_phase_locked"
            ),
            "absolute_polarity_claim": reference.get("absolute_polarity_claim"),
            "complex_convention_status": reference.get("complex_convention_status"),
            "complex_field_claim_level": reference.get("complex_field_claim_level"),
            "polarization_basis_model": reference.get("polarization_basis_model"),
            "jones_basis_status": reference.get("jones_basis_status"),
            "vector_optics_mode": reference.get("vector_optics_mode"),
            "mie_s1_s2_lab_basis_mapping": reference.get(
                "mie_s1_s2_lab_basis_mapping"
            ),
            "active_mie_basis_component": reference.get("active_mie_basis_component"),
            "S1S2_to_lab_basis_rotation_applied": reference.get(
                "S1S2_to_lab_basis_rotation_applied"
            ),
            "reference_jones_field_defined": reference.get(
                "reference_jones_field_defined"
            ),
            "detector_analyzer_jones_matrix_defined": reference.get(
                "detector_analyzer_jones_matrix_defined"
            ),
            "mie_jones_bridge_status": reference.get("mie_jones_bridge_status"),
            "NA_collection_for_vector_warning": reference.get(
                "NA_collection_for_vector_warning"
            ),
            "high_NA_collection_warning": reference.get("high_NA_collection_warning"),
            "vector_validity_status": reference.get("vector_validity_status"),
            "mie_intrinsic_complex_fields_available": reference.get(
                "mie_intrinsic_complex_fields_available"
            ),
            **{
                field: reference.get(field)
                for field in _MIE_INCIDENT_FIELD_DIAGNOSTIC_FIELDS
            },
            "calibration_state_machine_version": reference.get(
                "calibration_state_machine_version"
            ),
            "calibration_state_machine_status": reference.get(
                "calibration_state_machine_status"
            ),
            "output_claim_level": reference.get("output_claim_level"),
            "calibrated_quantitative_unlocked": reference.get(
                "calibrated_quantitative_unlocked"
            ),
            "output_claim_blocker_summary": reference.get(
                "output_claim_blocker_summary"
            ),
            "reference_calibration_level": reference.get(
                "reference_calibration_level"
            ),
            "reference_phase_calibration_level": reference.get(
                "reference_phase_calibration_level"
            ),
            "scattering_normalization_route": reference.get(
                "scattering_normalization_route"
            ),
            "scattering_normalization_status": reference.get(
                "scattering_normalization_status"
            ),
            "scattering_normalization_claim": reference.get(
                "scattering_normalization_claim"
            ),
            "scattering_calibration_level": reference.get(
                "scattering_calibration_level"
            ),
            "baseline_normalization_role": reference.get(
                "baseline_normalization_role"
            ),
            "baseline_particle_absolute_scale_restored": reference.get(
                "baseline_particle_absolute_scale_restored"
            ),
            "baseline_normalized_E_sca_allowed_in_photon_unit_route": reference.get(
                "baseline_normalized_E_sca_allowed_in_photon_unit_route"
            ),
            "baseline_normalized_E_sca_allowed_in_detector_unit_route": reference.get(
                "baseline_normalized_E_sca_allowed_in_detector_unit_route"
            ),
            "E_sca_ref_normalization_role": reference.get(
                "E_sca_ref_normalization_role"
            ),
            "K_sca_calibration_status": reference.get("K_sca_calibration_status"),
            "K_sca_value": reference.get("K_sca_value"),
            "K_sca_scope": reference.get("K_sca_scope"),
            "K_sca_role": reference.get("K_sca_role"),
            "mie_to_power_chain_status": reference.get("mie_to_power_chain_status"),
            "mie_differential_cross_section_source": reference.get(
                "mie_differential_cross_section_source"
            ),
            "scattered_power_conversion_status": reference.get(
                "scattered_power_conversion_status"
            ),
            "detector_field_units": reference.get("detector_field_units"),
            "detector_voltage_units": reference.get("detector_voltage_units"),
            "power_chain_absolute_units_available": reference.get(
                "power_chain_absolute_units_available"
            ),
            "K_sca_power_chain_role": reference.get("K_sca_power_chain_role"),
            "mie_to_power_chain_blocker_summary": reference.get(
                "mie_to_power_chain_blocker_summary"
            ),
            "standard_particle_calibration_status": reference.get(
                "standard_particle_calibration_status"
            ),
            "standard_particle_calibration_path_configured": reference.get(
                "standard_particle_calibration_path_configured"
            ),
            "standard_particle_calibration_source": reference.get(
                "standard_particle_calibration_source"
            ),
            "standard_particle_calibration_id": reference.get(
                "standard_particle_calibration_id"
            ),
            "standard_particle_calibration_coverage_status": reference.get(
                "standard_particle_calibration_coverage_status"
            ),
            "standard_particle_calibration_table_status": reference.get(
                "standard_particle_calibration_table_status"
            ),
            "standard_particle_calibration_max_relative_distance": reference.get(
                "standard_particle_calibration_max_relative_distance"
            ),
            "global_phase_offset_rad": reference.get("global_phase_offset_rad"),
            "global_phase_offset_calibration_status": reference.get(
                "global_phase_offset_calibration_status"
            ),
            "K_sca_uncertainty_status": reference.get("K_sca_uncertainty_status"),
            "K_sca_uncertainty_required_inputs": reference.get(
                "K_sca_uncertainty_required_inputs"
            ),
            "K_sca_uncertainty_propagated_to_outputs": reference.get(
                "K_sca_uncertainty_propagated_to_outputs"
            ),
            "standard_particle_uncertainty_budget_status": reference.get(
                "standard_particle_uncertainty_budget_status"
            ),
            "standard_particle_size_distribution_status": reference.get(
                "standard_particle_size_distribution_status"
            ),
            "standard_particle_shape_uncertainty_status": reference.get(
                "standard_particle_shape_uncertainty_status"
            ),
            "standard_particle_ligand_shell_status": reference.get(
                "standard_particle_ligand_shell_status"
            ),
            "standard_particle_batch_status": reference.get(
                "standard_particle_batch_status"
            ),
            "standard_particle_concentration_uncertainty_status": reference.get(
                "standard_particle_concentration_uncertainty_status"
            ),
            "standard_particle_material_dataset_uncertainty_status": reference.get(
                "standard_particle_material_dataset_uncertainty_status"
            ),
            "K_sca_uncertainty_blocker_summary": reference.get(
                "K_sca_uncertainty_blocker_summary"
            ),
            "calibration_design_rank": reference.get("calibration_design_rank"),
            "calibration_design_rank_reason": reference.get(
                "calibration_design_rank_reason"
            ),
            "calibration_standard_count": reference.get("calibration_standard_count"),
            "calibration_wavelength_count": reference.get(
                "calibration_wavelength_count"
            ),
            "calibration_geometry_count": reference.get("calibration_geometry_count"),
            "calibration_held_out_validation_status": reference.get(
                "calibration_held_out_validation_status"
            ),
            "calibration_held_out_error": reference.get("calibration_held_out_error"),
            "calibration_identifiability_blocker_summary": reference.get(
                "calibration_identifiability_blocker_summary"
            ),
            "calibration_fit_parameter_coupling_status": reference.get(
                "calibration_fit_parameter_coupling_status"
            ),
            "calibration_design_minimum_requirement_status": reference.get(
                "calibration_design_minimum_requirement_status"
            ),
            "fit_parameters_identifiable": reference.get(
                "fit_parameters_identifiable"
            ),
            "detector_calibration_level": reference.get("detector_calibration_level"),
            "readout_calibration_level": reference.get("readout_calibration_level"),
            "count_calibration_level": reference.get("count_calibration_level"),
            **{
                field: reference.get(field)
                for field in _CALIBRATION_STATE_EXTRA_FIELDS
            },
            "noise_model_route": reference.get("noise_model_route"),
            "detector_noise_claim_level": reference.get("detector_noise_claim_level"),
            "detector_signal_unit_convention": reference.get(
                "detector_signal_unit_convention"
            ),
            "absolute_throughput_route": reference.get("absolute_throughput_route"),
            "absolute_throughput_calibrated": reference.get(
                "absolute_throughput_calibrated"
            ),
            "photon_unit_noise_model": reference.get("photon_unit_noise_model"),
            "photon_unit_noise_model_status": reference.get(
                "photon_unit_noise_model_status"
            ),
            "photon_count_route_active": reference.get("photon_count_route_active"),
            "lockin_ENBW_Hz": reference.get("lockin_ENBW_Hz"),
            "lockin_ENBW_status": reference.get("lockin_ENBW_status"),
            "lockin_ENBW_claim_level": reference.get("lockin_ENBW_claim_level"),
            "shot_noise_model_status": reference.get("shot_noise_model_status"),
            "photon_shot_noise_term_status": reference.get(
                "photon_shot_noise_term_status"
            ),
            "shot_noise_limited_snr": reference.get("shot_noise_limited_snr"),
            "electronics_noise_model_status": reference.get(
                "electronics_noise_model_status"
            ),
            "electronics_noise_term_status": reference.get(
                "electronics_noise_term_status"
            ),
            "electronics_noise_limited_snr": reference.get(
                "electronics_noise_limited_snr"
            ),
            "rin_noise_model_status": reference.get("rin_noise_model_status"),
            "rin_noise_term_status": reference.get("rin_noise_term_status"),
            "rin_limited_snr": reference.get("rin_limited_snr"),
            "speckle_background_noise_model_status": reference.get(
                "speckle_background_noise_model_status"
            ),
            "speckle_like_noise_term_status": reference.get(
                "speckle_like_noise_term_status"
            ),
            "drift_noise_model_status": reference.get("drift_noise_model_status"),
            "drift_noise_term_status": reference.get("drift_noise_term_status"),
            "post_readout_noise_model_status": reference.get(
                "post_readout_noise_model_status"
            ),
            "lockin_output_noise_term_status": reference.get(
                "lockin_output_noise_term_status"
            ),
            "noise_terms_schema_version": reference.get("noise_terms_schema_version"),
            "noise_term_quantitative_contribution_status": reference.get(
                "noise_term_quantitative_contribution_status"
            ),
            "noise_terms": reference.get("noise_terms"),
            "detector_dynamic_range_model": reference.get(
                "detector_dynamic_range_model"
            ),
            "detector_saturation_status": reference.get("detector_saturation_status"),
            "detector_saturation_margin": reference.get("detector_saturation_margin"),
            "ADC_dynamic_range_status": reference.get("ADC_dynamic_range_status"),
            "ADC_dynamic_range_margin": reference.get("ADC_dynamic_range_margin"),
            "dynamic_range_margin": reference.get("dynamic_range_margin"),
            "blank_trace_noise_model_fit_quality": reference.get(
                "blank_trace_noise_model_fit_quality"
            ),
            "reference_enhancement_gain": reference.get("reference_enhancement_gain"),
            "reference_enhancement_snr_claim": reference.get(
                "reference_enhancement_snr_claim"
            ),
            "background_field_model": reference.get("background_field_model"),
            "background_field_status": reference.get("background_field_status"),
            "background_claim_level": reference.get("background_claim_level"),
            "background_subtraction_status": reference.get(
                "background_subtraction_status"
            ),
            "residual_transmitted_leakage_model": reference.get(
                "residual_transmitted_leakage_model"
            ),
            "residual_transmitted_leakage_status": reference.get(
                "residual_transmitted_leakage_status"
            ),
            "transmitted_leakage_model": reference.get("transmitted_leakage_model"),
            "stray_light_model": reference.get("stray_light_model"),
            "stray_light_status": reference.get("stray_light_status"),
            "speckle_like_background_status": reference.get(
                "speckle_like_background_status"
            ),
            "blank_trace_provenance": reference.get("blank_trace_provenance"),
            "blank_trace_empirical_available": reference.get(
                "blank_trace_empirical_available"
            ),
            "particle_induced_channel_perturbation_model": reference.get(
                "particle_induced_channel_perturbation_model"
            ),
            "particle_induced_channel_phase_perturbation_status": reference.get(
                "particle_induced_channel_phase_perturbation_status"
            ),
            "independent_superposition_status": reference.get(
                "independent_superposition_status"
            ),
            "weak_superposition_validity_status": reference.get(
                "weak_superposition_validity_status"
            ),
            "superposition_validity_status": reference.get(
                "superposition_validity_status"
            ),
            "E_sca_to_E_ref_amplitude_ratio_estimate": reference.get(
                "E_sca_to_E_ref_amplitude_ratio_estimate"
            ),
            "extinction_to_beam_area_estimate": reference.get(
                "extinction_to_beam_area_estimate"
            ),
            "reference_depletion_fraction_estimate": reference.get(
                "reference_depletion_fraction_estimate"
            ),
            "reference_depletion_estimate_status": reference.get(
                "reference_depletion_estimate_status"
            ),
            "channel_particle_coupling_model": reference.get(
                "channel_particle_coupling_model"
            ),
            "joint_fullwave_required_for_quantitative_phase": reference.get(
                "joint_fullwave_required_for_quantitative_phase"
            ),
            "superposition_validity_claim_level": reference.get(
                "superposition_validity_claim_level"
            ),
            "superposition_validity_blocker_summary": reference.get(
                "superposition_validity_blocker_summary"
            ),
            "nodi_signal_component_model": reference.get("nodi_signal_component_model"),
            "nodi_signal_component_status": reference.get("nodi_signal_component_status"),
            "nodi_forward_extinction_leakage_status": reference.get(
                "nodi_forward_extinction_leakage_status"
            ),
            "nodi_transmitted_leakage_component_status": reference.get(
                "nodi_transmitted_leakage_component_status"
            ),
            "nodi_particle_induced_channel_coupling_status": reference.get(
                "nodi_particle_induced_channel_coupling_status"
            ),
            "nodi_signal_component_claim_level": reference.get(
                "nodi_signal_component_claim_level"
            ),
            "nodi_component_escalation_route": reference.get(
                "nodi_component_escalation_route"
            ),
            "readout_preset": reference.get("readout_preset"),
            "readout_preset_status": reference.get("readout_preset_status"),
            "readout_preset_claim_level": reference.get("readout_preset_claim_level"),
            "readout_preset_mismatch_fields": reference.get(
                "readout_preset_mismatch_fields"
            ),
            "readout_preset_threshold_scope": reference.get(
                "readout_preset_threshold_scope"
            ),
            "readout_shared_threshold_profile": reference.get(
                "readout_shared_threshold_profile"
            ),
            "readout_lane_specific_thresholds_available": reference.get(
                "readout_lane_specific_thresholds_available"
            ),
            "readout_preset_frequency_leakage_note": reference.get(
                "readout_preset_frequency_leakage_note"
            ),
            "readout_paper_time_constant_range_s": reference.get(
                "readout_paper_time_constant_range_s"
            ),
            "electronics_demod_phase_policy": reference.get(
                "electronics_demod_phase_policy"
            ),
            "effective_electronics_demod_phase_policy": reference.get(
                "effective_electronics_demod_phase_policy"
            ),
            "readout_reference_phase_source": reference.get(
                "readout_reference_phase_source"
            ),
            "readout_polarity": reference.get("readout_polarity"),
            "polarity_source": reference.get("polarity_source"),
            "arrival_phase_distribution": reference.get(
                "arrival_phase_distribution"
            ),
            "readout_internal_sampling_rate_Hz": reference.get(
                "readout_internal_sampling_rate_Hz"
            ),
            "readout_output_sampling_rate_Hz": reference.get(
                "readout_output_sampling_rate_Hz"
            ),
            "readout_max_lockin_frequency_Hz": reference.get(
                "readout_max_lockin_frequency_Hz"
            ),
            "readout_sampling_oversampling_ratio": reference.get(
                "readout_sampling_oversampling_ratio"
            ),
            "readout_sampling_required_rate_Hz": reference.get(
                "readout_sampling_required_rate_Hz"
            ),
            "readout_sampling_hard_gate_passed": reference.get(
                "readout_sampling_hard_gate_passed"
            ),
            "readout_frequency_dependent_paper_conclusion_allowed": reference.get(
                "readout_frequency_dependent_paper_conclusion_allowed"
            ),
            "readout_sampling_claim_level": reference.get(
                "readout_sampling_claim_level"
            ),
            "readout_carrier_nyquist_resolved": reference.get(
                "readout_carrier_nyquist_resolved"
            ),
            "readout_carrier_resolved": reference.get("readout_carrier_resolved"),
            "readout_carrier_resolved_with_margin": reference.get(
                "readout_carrier_resolved_with_margin"
            ),
            "readout_analytic_demod_used": reference.get(
                "readout_analytic_demod_used"
            ),
            "readout_internal_demod_route": reference.get(
                "readout_internal_demod_route"
            ),
            "readout_anti_alias_policy": reference.get("readout_anti_alias_policy"),
            "readout_anti_alias_filter_before_downsample": reference.get(
                "readout_anti_alias_filter_before_downsample"
            ),
            "lockin_output_grid_matches_data_logger": reference.get(
                "lockin_output_grid_matches_data_logger"
            ),
            "readout_sampling_validity": reference.get("readout_sampling_validity"),
            "lockin_output_unit_convention": reference.get(
                "lockin_output_unit_convention"
            ),
            "lockin_gain_chain": reference.get("lockin_gain_chain"),
            "lockin_reported_channel": reference.get("lockin_reported_channel"),
            "lockin_reported_channel_source": reference.get(
                "lockin_reported_channel_source"
            ),
            "lockin_measured_voltage_comparable": reference.get(
                "lockin_measured_voltage_comparable"
            ),
            "readout_model_claim_level": reference.get("readout_model_claim_level"),
            "pod_source_model_status": reference.get("pod_source_model_status"),
            "nodi_source_model_status": reference.get("nodi_source_model_status"),
            **{
                field: reference.get(field)
                for field in _PHOTOTHERMAL_POD_DIAGNOSTIC_FIELDS
            },
            "threshold_sigma": reference.get("threshold_sigma"),
            "threshold_sigma_nodi": reference.get("threshold_sigma_nodi"),
            "threshold_sigma_pod": reference.get("threshold_sigma_pod"),
            "threshold_lane_specific_model": reference.get(
                "threshold_lane_specific_model"
            ),
            "threshold_tail": reference.get("threshold_tail"),
            "threshold_tail_configured": reference.get("threshold_tail_configured"),
            "threshold_tail_status": reference.get("threshold_tail_status"),
            "threshold_false_alarm_tail_count": reference.get(
                "threshold_false_alarm_tail_count"
            ),
            "threshold_sign": reference.get("threshold_sign"),
            "threshold_polarity_mode": reference.get("threshold_polarity_mode"),
            "target_false_alarm_rate": reference.get("target_false_alarm_rate"),
            "threshold_from_blank_trace": reference.get("threshold_from_blank_trace"),
            "threshold_from_event_background_segment": reference.get(
                "threshold_from_event_background_segment"
            ),
            "threshold_background_source": reference.get("threshold_background_source"),
            "threshold_background_segment_fraction": reference.get(
                "threshold_background_segment_fraction"
            ),
            "threshold_background_segment_samples": reference.get(
                "threshold_background_segment_samples"
            ),
            "threshold_calibration_source": reference.get(
                "threshold_calibration_source"
            ),
            "threshold_calibration_status": reference.get(
                "threshold_calibration_status"
            ),
            "blank_false_positive_calibration_status": reference.get(
                "blank_false_positive_calibration_status"
            ),
            "blank_false_positive_calibration_source": reference.get(
                "blank_false_positive_calibration_source"
            ),
            "blank_false_positive_calibration_id": reference.get(
                "blank_false_positive_calibration_id"
            ),
            "absolute_threshold_sigma_equivalent": reference.get(
                "absolute_threshold_sigma_equivalent"
            ),
            "positive_threshold_sigma_equivalent": reference.get(
                "positive_threshold_sigma_equivalent"
            ),
            "gaussian_iid_single_sample_false_alarm_probability": reference.get(
                "gaussian_iid_single_sample_false_alarm_probability"
            ),
            "gaussian_iid_background_segment_false_alarm_probability": reference.get(
                "gaussian_iid_background_segment_false_alarm_probability"
            ),
            "mean_threshold_robust_std": reference.get("mean_threshold_robust_std"),
            "mean_pod_threshold_robust_std": reference.get(
                "mean_pod_threshold_robust_std"
            ),
            "blank_trace_autocorrelation_time_s": reference.get(
                "blank_trace_autocorrelation_time_s"
            ),
            "effective_independent_samples_per_trace": reference.get(
                "effective_independent_samples_per_trace"
            ),
            "lockin_filter_order": reference.get("lockin_filter_order"),
            "empirical_peak_false_alarm_rate_per_minute": reference.get(
                "empirical_peak_false_alarm_rate_per_minute"
            ),
            "empirical_pair_false_alarm_rate_per_minute": reference.get(
                "empirical_pair_false_alarm_rate_per_minute"
            ),
            "lane_noise_correlation_coefficient": reference.get(
                "lane_noise_correlation_coefficient"
            ),
            "colored_noise_false_alarm_model": reference.get(
                "colored_noise_false_alarm_model"
            ),
            "colored_noise_false_alarm_status": reference.get(
                "colored_noise_false_alarm_status"
            ),
            "colored_noise_surrogate_components": reference.get(
                "colored_noise_surrogate_components"
            ),
            "colored_noise_threshold_bias": reference.get(
                "colored_noise_threshold_bias"
            ),
            "colored_noise_threshold_bias_status": reference.get(
                "colored_noise_threshold_bias_status"
            ),
            "paired_false_alarm_status": reference.get("paired_false_alarm_status"),
            **{
                field: reference.get(field)
                for field in _THRESHOLD_FALSE_ALARM_EXTRA_FIELDS
            },
            "reference_spatial_mode": sim_cfg.reference_spatial_mode,
            "reference_spatial_amplitude_strength": sim_cfg.reference_spatial_amplitude_strength,
            "reference_spatial_phase_strength_rad": sim_cfg.reference_spatial_phase_strength_rad,
            "reference_spatial_min_amplitude_scale": sim_cfg.reference_spatial_min_amplitude_scale,
            "calibration_extrapolated": bool(reference.get("calibration_extrapolated", False)),
            "reference_projection_basis": reference.get("reference_projection_basis"),
            "reference_effective_basis": reference.get("reference_effective_basis"),
            "reference_projection_basis_match": reference.get(
                "reference_projection_basis_match"
            ),
            "reference_projection_coupling_status": reference.get(
                "reference_projection_coupling_status"
            ),
            "rho_requested": reference.get("rho_requested"),
            "rho_physical_envelope_source": reference.get("rho_physical_envelope_source"),
            "rho_physical_envelope_nominal": reference.get(
                "rho_physical_envelope_nominal"
            ),
            "rho_physical_envelope_lower": reference.get(
                "rho_physical_envelope_lower"
            ),
            "rho_physical_envelope_upper": reference.get(
                "rho_physical_envelope_upper"
            ),
            "rho_physical_ratio_to_nominal": reference.get(
                "rho_physical_ratio_to_nominal"
            ),
            "rho_physical_envelope_in_range": reference.get(
                "rho_physical_envelope_in_range"
            ),
            "rho_physical_envelope_status": reference.get(
                "rho_physical_envelope_status"
            ),
            "reference_diffraction_efficiency_model": reference.get(
                "reference_diffraction_efficiency_model"
            ),
            "reference_diffraction_efficiency_zeroth_order": reference.get(
                "reference_diffraction_efficiency_zeroth_order"
            ),
            "reference_diffraction_efficiency_first_order": reference.get(
                "reference_diffraction_efficiency_first_order"
            ),
            "reference_field_amplitude_envelope_nominal": reference.get(
                "reference_field_amplitude_envelope_nominal"
            ),
            "reference_field_amplitude_envelope_lower": reference.get(
                "reference_field_amplitude_envelope_lower"
            ),
            "reference_field_amplitude_envelope_upper": reference.get(
                "reference_field_amplitude_envelope_upper"
            ),
            "reference_width_saturation_mode": reference.get(
                "reference_width_saturation_mode"
            ),
            "reference_width_saturation_status": reference.get(
                "reference_width_saturation_status"
            ),
            "reference_width_saturation_cutoff_ratio": reference.get(
                "reference_width_saturation_cutoff_ratio"
            ),
            "reference_width_lambda_ratio_nominal": reference.get(
                "reference_width_lambda_ratio_nominal"
            ),
            "reference_width_lambda_ratio_effective": reference.get(
                "reference_width_lambda_ratio_effective"
            ),
            "reference_width_effective_m": reference.get("reference_width_effective_m"),
            "reference_width_saturation_factor": reference.get(
                "reference_width_saturation_factor"
            ),
            "na_cutoff_active": reference.get("na_cutoff_active"),
            "na_cutoff_condition_met": reference.get("na_cutoff_condition_met"),
            "na_cutoff_hard_zero_applied": reference.get("na_cutoff_hard_zero_applied"),
            "na_cutoff_policy": reference.get("na_cutoff_policy"),
            "na_cutoff_diff_ratio": reference.get("na_cutoff_diff_ratio"),
            "na_cutoff_na_ratio": reference.get("na_cutoff_na_ratio"),
            "na_cutoff_NA_collection": reference.get("na_cutoff_NA_collection"),
            "na_cutoff_W_min_m": reference.get("na_cutoff_W_min_m"),
            "illumination_mode": sim_cfg.illumination_mode,
            "illumination_geometry_source": illumination_geometry.get(
                "illumination_geometry_source"
            ),
            "illumination_beam_waist_x_m": illumination_geometry.get(
                "illumination_beam_waist_x_m"
            ),
            "illumination_beam_waist_y_m": illumination_geometry.get(
                "illumination_beam_waist_y_m"
            ),
            "illumination_beam_waist_z_m": illumination_geometry.get(
                "illumination_beam_waist_z_m"
            ),
            "interference_overlap_mode": reference.get("interference_overlap_mode"),
            "interference_cross_term_joint_available": reference.get(
                "interference_cross_term_joint_available"
            ),
            "interference_overlap_status": reference.get("interference_overlap_status"),
            "interference_overlap_factor_abs": float(
                abs(reference.get("interference_overlap_factor_complex", 1.0 + 0.0j))
            ),
            "interference_overlap_factor_phase_rad": float(
                np.angle(reference.get("interference_overlap_factor_complex", 1.0 + 0.0j))
            ),
        },
    }


def _clone_rng_from_state(state: dict) -> np.random.Generator:
    rng = np.random.default_rng()
    rng.bit_generator.state = deepcopy(state)
    return rng


def _rng_states_equal(left: dict, right: dict) -> bool:
    if left.keys() != right.keys():
        return False
    for key, left_value in left.items():
        right_value = right[key]
        if isinstance(left_value, dict) and isinstance(right_value, dict):
            if not _rng_states_equal(left_value, right_value):
                return False
        elif isinstance(left_value, np.ndarray) or isinstance(right_value, np.ndarray):
            if not np.array_equal(np.asarray(left_value), np.asarray(right_value)):
                return False
        elif left_value != right_value:
            return False
    return True


def _shared_event_view_metadata(
    *,
    sim_cfg: SimulationConfig,
    rng_seed: int | None,
    case_identity: str,
    actual_events: int,
) -> dict[str, object]:
    return {
        "random_sequence_policy": sim_cfg.random_sequence_policy,
        "event_sampling_policy": sim_cfg.event_sampling_policy,
        "event_position_low_variance_sampling": bool(
            sim_cfg.event_sampling_policy != "random"
        ),
        "case_random_seed": int(rng_seed) if rng_seed is not None else None,
        "case_random_identity": case_identity,
        "adaptive_event_budget_mode": sim_cfg.adaptive_event_budget_mode,
        "adaptive_event_budget_requested_events": int(sim_cfg.n_events),
        "adaptive_event_budget_actual_events": int(actual_events),
        "adaptive_event_budget_stopped_early": bool(
            int(actual_events) < int(sim_cfg.n_events)
        ),
        "adaptive_event_budget_stop_reason": "fixed_event_budget",
        "adaptive_min_events": int(sim_cfg.adaptive_min_events),
        "adaptive_check_interval": int(sim_cfg.adaptive_check_interval),
        "vectorized_event_engine": sim_cfg.vectorized_event_engine,
        "event_block_size": int(sim_cfg.event_block_size),
        "event_block_rng_order": sim_cfg.event_block_rng_order,
        "vectorized_event_engine_used": "off",
        "vectorized_event_engine_fallback_reason": "shared_dual_event_loop_path",
        "vectorized_event_rng_order": "event_loop_order",
        "shared_event_dual_normalization_used": True,
        "shared_event_physical_event_count": int(actual_events),
        "shared_event_dual_normalization_scope": (
            "same initial positions, Brownian trajectories, illumination envelope, "
            "and per-event noise RNG start state shared across normalization views"
        ),
    }


def _refresh_shared_event_batch_result(
    batch: dict,
    *,
    particle: Particle,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    shared_event_summary: dict[str, object],
    rng_seed: int | None,
    case_identity: str,
) -> dict:
    """Overlay shared-event summaries onto a static zero-event case skeleton."""
    out = dict(batch)
    reference = dict(out.get("reference", {}))
    summary = dict(out.get("summary", {}))
    summary.update(shared_event_summary)
    summary.update(
        _shared_event_view_metadata(
            sim_cfg=sim_cfg,
            rng_seed=rng_seed,
            case_identity=case_identity,
            actual_events=int(shared_event_summary.get("n_events", sim_cfg.n_events)),
        )
    )
    recompute_manifest = build_recompute_manifest_diagnostics(
        particle,
        channel,
        optical,
        sim_cfg,
    )
    summary.update(recompute_manifest)
    reference.update(recompute_manifest)

    detector_noise_summary = build_detector_noise_diagnostics(
        sim_cfg,
        collection_operator=None,
        mean_shot_noise_std=summary.get("mean_shot_noise_std"),
        reference_enhancement_gain=summary.get(
            "mean_reference_to_scattering_amplitude_ratio"
        ),
    )
    summary.update(detector_noise_summary)
    reference.update(detector_noise_summary)
    run_state = build_run_state_diagnostics(summary, sim_cfg)
    summary.update(run_state)
    reference.update(run_state)
    threshold_false_alarm_summary = build_threshold_false_alarm_diagnostics(
        sim_cfg,
        n_background_samples=summary.get("threshold_background_segment_samples"),
        mean_threshold_robust_std=summary.get("mean_threshold_robust_std"),
        mean_pod_threshold_robust_std=summary.get("mean_pod_threshold_robust_std"),
    )
    summary.update(threshold_false_alarm_summary)
    reference.update(threshold_false_alarm_summary)
    event_quality = build_event_quality_control_diagnostics(
        summary,
        sim_cfg,
        reference=reference,
    )
    summary.update(event_quality)
    reference.update(event_quality)
    engineering_gate = evaluate_engineering_gate(summary, sim_cfg)
    summary.update(engineering_gate)
    reference.update(engineering_gate)

    qc_conditioned_detection_rate = summary.get("detected_rate_after_event_qc")
    conditional_detection_rate_source = "detected_rate_after_event_qc"
    if qc_conditioned_detection_rate is None:
        qc_conditioned_detection_rate = summary.get("detection_rate")
        conditional_detection_rate_source = (
            "detection_rate_fallback_event_qc_unavailable"
        )
    empirical_peak_far_per_min = reference.get(
        "empirical_peak_false_alarm_rate_per_minute"
    )
    blank_false_positive_rate_hz = (
        max(float(empirical_peak_far_per_min) / 60.0, 0.0)
        if empirical_peak_far_per_min is not None
        else None
    )
    count_model_summary = build_count_model_diagnostics(
        particle,
        channel,
        sim_cfg,
        conditional_detection_rate=qc_conditioned_detection_rate,
        conditional_detection_rate_source=conditional_detection_rate_source,
        mean_transit_time_s=summary.get("mean_transit_time_s"),
        blank_false_positive_rate_Hz=blank_false_positive_rate_hz,
    )
    summary.update(count_model_summary)
    reference.update(count_model_summary)
    count_likelihood = build_count_likelihood_diagnostics(
        summary,
        count_model_summary,
        sim_cfg,
    )
    summary.update(count_likelihood)
    reference.update(count_likelihood)
    selection_function = build_selection_function_diagnostics(
        particle,
        summary,
        sim_cfg,
    )
    summary.update(selection_function)
    reference.update(selection_function)
    ev_population_prior = build_ev_population_prior_diagnostics(
        particle,
        {**reference, **summary},
        sim_cfg,
    )
    summary.update(ev_population_prior)
    reference.update(ev_population_prior)
    population_inference = build_population_inference_scaffold(
        {**reference, **summary}
    )
    summary.update(population_inference)
    reference.update(population_inference)
    ood_detection = build_ood_detection_diagnostics(
        particle,
        summary,
    )
    summary.update(ood_detection)
    reference.update(ood_detection)
    claim_governance = build_design_claim_governance_diagnostics(
        particle,
        channel,
        optical,
        sim_cfg,
        reference=reference,
        summary=summary,
    )
    summary.update(claim_governance)
    reference.update(claim_governance)
    experimental_design_advisor = build_experimental_design_advisor(
        {**reference, **summary}
    )
    summary.update(experimental_design_advisor)
    reference.update(experimental_design_advisor)

    out["events"] = []
    out["summary"] = summary
    out["reference"] = reference
    intrinsic = dict(out.get("intrinsic", {}))
    intrinsic.update(recompute_manifest)
    intrinsic.update(event_quality)
    intrinsic.update(selection_function)
    intrinsic.update(run_state)
    intrinsic.update(count_model_summary)
    intrinsic.update(count_likelihood)
    intrinsic.update(ev_population_prior)
    intrinsic.update(population_inference)
    intrinsic.update(ood_detection)
    intrinsic.update(claim_governance)
    intrinsic.update(experimental_design_advisor)
    out["intrinsic"] = intrinsic
    return out


def _with_reconstructed_overlap_complex(reference: dict) -> dict:
    """Restore complex overlap factor needed by trace generation if flattened."""
    out = dict(reference)
    if "interference_overlap_factor_complex" not in out:
        amp = out.get("interference_overlap_factor_abs")
        phase = out.get("interference_overlap_factor_phase_rad")
        if amp is not None and phase is not None:
            out["interference_overlap_factor_complex"] = complex(
                float(amp) * np.exp(1j * float(phase))
            )
    return out


def run_single_case_batch_shared_event_normalization_views(
    particle: Particle,
    medium: Medium,
    channel: Channel,
    optical: OpticalSystem,
    view_configs: dict[str, SimulationConfig],
    E_sca_refs: dict[str, float],
    theta_grid_rad: np.ndarray,
    *,
    intrinsic_cache: dict | None = None,
    reference_cache: dict | None = None,
    collection_operator_cache: dict | None = None,
    view_payload_overrides: dict[str, dict[str, dict[str, object]]] | None = None,
) -> dict[str, dict]:
    """Run multiple normalization views from one physical event stream.

    This production path is intentionally scoped to the full-grid launch mode:
    stream-summary output, fixed event budget, and event-loop execution. It
    shares initial-position sampling, Brownian trajectory generation,
    illumination, and the per-event noise RNG start state across views while
    accumulating separate normalization/readout summaries.
    """
    if not view_configs:
        raise ValueError("at least one normalization view is required")
    if set(view_configs) != set(E_sca_refs):
        raise ValueError("view_configs and E_sca_refs must have identical keys")

    base_name = next(iter(view_configs))
    base_cfg = view_configs[base_name]
    for name, cfg in view_configs.items():
        if int(cfg.n_events) != int(base_cfg.n_events):
            raise ValueError(f"view {name} has mismatched n_events")
        if cfg.random_seed != base_cfg.random_seed:
            raise ValueError(f"view {name} has mismatched random_seed")
        if cfg.random_sequence_policy != base_cfg.random_sequence_policy:
            raise ValueError(f"view {name} has mismatched random_sequence_policy")
        if cfg.event_sampling_policy != base_cfg.event_sampling_policy:
            raise ValueError(f"view {name} has mismatched event_sampling_policy")
        for field_name in (
            "noise_std",
            "noise_model",
            "drift_slope",
            "shot_noise_scale",
            "post_readout_noise_std",
            "post_readout_drift_slope",
            "detector_noise_model_route",
        ):
            if getattr(cfg, field_name) != getattr(base_cfg, field_name):
                raise ValueError(
                    f"view {name} has mismatched {field_name}"
                )
        if cfg.adaptive_event_budget_mode != "fixed":
            raise ValueError("shared-event dual normalization requires fixed event budget")
        if cfg.vectorized_event_engine != "off":
            raise ValueError("shared-event dual normalization currently requires event-loop mode")
        if cfg.post_readout_colored_noise_std > 0:
            raise ValueError("shared-event dual normalization does not yet support colored post-readout noise")

    skeletons: dict[str, dict] = {}
    for name, cfg in view_configs.items():
        # SimulationConfig intentionally requires a positive n_events.  Use a
        # one-event static skeleton, then replace all event-derived summaries
        # below with the shared physical event stream.  This keeps the rich
        # reference/governance schema without duplicating the formal 10000e
        # event campaign for each normalization view.
        zero_cfg = replace(cfg, n_events=1, adaptive_event_budget_mode="fixed")
        skeletons[name] = run_single_case_batch(
            particle,
            medium,
            channel,
            optical,
            zero_cfg,
            E_sca_refs[name],
            theta_grid_rad,
            retain_event_traces=False,
            stream_summary_only=True,
            intrinsic_cache=intrinsic_cache,
            reference_cache=reference_cache,
            collection_operator_cache=collection_operator_cache,
        )
        if view_payload_overrides and name in view_payload_overrides:
            overrides = view_payload_overrides[name]
            for payload_name in ("reference", "intrinsic"):
                if payload_name in overrides:
                    skeletons[name][payload_name].update(overrides[payload_name])

    medium_refractive_index = float(medium.refractive_index_at(optical.wavelength_m))
    diffusion_coefficient = (
        _compute_diffusion_coefficient(particle, medium)
        if base_cfg.include_diffusion
        else None
    )
    event_case_context = _build_event_case_context(
        channel,
        base_cfg,
        particle_radius_m=particle.radius_m,
    )
    transport_channel = event_case_context.transport_channel
    transport_cfg = event_case_context.transport_cfg
    trajectory_context = event_case_context.trajectory_context
    readout_contexts = {
        name: _build_readout_context(trajectory_context.time_s, cfg)
        for name, cfg in view_configs.items()
    }
    case_identity = _build_case_random_identity(
        particle,
        medium,
        channel,
        optical,
    )
    rng_seed = _resolve_case_rng_seed(base_cfg, case_identity)
    rng = np.random.default_rng(rng_seed)
    unit_position_samples = _build_event_position_unit_samples(
        n_events=base_cfg.n_events,
        policy=base_cfg.event_sampling_policy,
        seed=rng_seed,
        case_identity=case_identity,
    )
    accumulators = {
        name: _BatchSummaryAccumulator(
            stable_detection_margin_z_min=cfg.stable_detection_margin_z_min,
            fixed_false_alarm_rate=cfg.evaluation_false_alarm_rate,
            selected_annulus_edge_norm_min=cfg.selected_annulus_edge_norm_min,
            selected_annulus_edge_norm_max=cfg.selected_annulus_edge_norm_max,
        )
        for name, cfg in view_configs.items()
    }

    for event_idx in range(int(base_cfg.n_events)):
        unit_position_sample = (
            tuple(float(x) for x in unit_position_samples[event_idx])
            if unit_position_samples is not None
            else None
        )
        x0, z0, position_diag = sample_initial_position(
            transport_channel,
            rng,
            particle.radius_m,
            sim_cfg=transport_cfg,
            unit_position_sample=unit_position_sample,
        )
        trajectory = simulate_particle_trajectory(
            transport_channel,
            optical,
            transport_cfg,
            x0,
            z0,
            particle_radius_m=particle.radius_m,
            diffusion_coefficient=diffusion_coefficient,
            rng=rng,
            trajectory_context=trajectory_context,
        )
        illumination = compute_illumination_envelope(
            trajectory["x_m"],
            trajectory["y_m"],
            trajectory["z_m"],
            optical,
            medium_refractive_index=medium_refractive_index,
            sim_cfg=base_cfg,
        )
        transit_time_s = _estimate_transit_time_s(
            trajectory["time_s"],
            illumination["A_env_scalar"],
        )
        shared_rng_state = deepcopy(rng.bit_generator.state)
        lane_end_state = None
        for name, cfg in view_configs.items():
            reference = _with_reconstructed_overlap_complex(skeletons[name]["reference"])
            intrinsic = skeletons[name]["intrinsic"]
            reference_trace = compute_reference_field_trace(
                trajectory,
                reference,
                channel,
                optical,
                cfg,
                initial_x_m=x0,
                initial_z_m=z0,
            )
            scattering_phase_summary = {
                "phi_sca_material_rad": intrinsic.get("phi_sca_material_rad"),
                "phi_sca_material_parallel_rad": intrinsic.get(
                    "phi_sca_material_parallel_rad"
                ),
                "phi_sca_material_perpendicular_rad": intrinsic.get(
                    "phi_sca_material_perpendicular_rad"
                ),
                "phi_projection_rad": intrinsic.get("phi_projection_rad"),
            }
            lane_rng = _clone_rng_from_state(shared_rng_state)
            _simulate_one_event_from_shared_physical_state(
                channel=channel,
                optical=optical,
                sim_cfg=cfg,
                E_sca_unit_normalized=intrinsic["E_sca_unit_normalized_complex"],
                reference=reference,
                theta_det_rad=float(intrinsic["theta_det_rad"]),
                rng=lane_rng,
                scattering_phase_diagnostics=scattering_phase_summary,
                medium_refractive_index=medium_refractive_index,
                transport_channel=transport_channel,
                transport_cfg=transport_cfg,
                trajectory=trajectory,
                illumination=illumination,
                transit_time_s=transit_time_s,
                reference_trace=reference_trace,
                x0=x0,
                z0=z0,
                position_diag=position_diag,
                retain_full_payload=False,
                readout_context=readout_contexts[name],
                event_case_context=event_case_context,
                summary_accumulator=accumulators[name],
            )
            state = deepcopy(lane_rng.bit_generator.state)
            if lane_end_state is None:
                lane_end_state = state
            elif not _rng_states_equal(lane_end_state, state):
                raise RuntimeError(
                    "shared-event normalization views consumed different RNG counts"
                )
        if lane_end_state is not None:
            rng.bit_generator.state = lane_end_state

    outputs: dict[str, dict] = {}
    for name, cfg in view_configs.items():
        outputs[name] = _refresh_shared_event_batch_result(
            skeletons[name],
            particle=particle,
            channel=channel,
            optical=optical,
            sim_cfg=cfg,
            shared_event_summary=accumulators[name].finalize(),
            rng_seed=rng_seed,
            case_identity=case_identity,
        )
    return outputs


def _resolve_worker_count(n_workers: int | None) -> int:
    """Normalize worker count; `0` means use all visible logical CPUs."""
    if n_workers is None:
        return 1
    if n_workers < 0:
        raise ValueError("n_workers must be >= 0")
    if n_workers == 0:
        return max(1, os.cpu_count() or 1)
    return n_workers


def _configure_parallel_worker_env() -> dict[str, str]:
    """
    Limit BLAS/OpenMP threads per worker to avoid process×thread oversubscription.

    This is most important on Windows spawn-based process pools, where each child
    imports NumPy independently and would otherwise be free to start many BLAS
    threads of its own.
    """
    updated = {}
    for env_var in _BLAS_THREAD_ENV_VARS:
        if env_var not in os.environ:
            os.environ[env_var] = "1"
            updated[env_var] = "1"
    return updated


def _build_sweep_last_case_snapshot(case_result: dict | None) -> dict | None:
    """Build the compact last-case progress snapshot."""
    if case_result is None:
        return None
    return {
        "case_idx": int(case_result["case_idx"]),
        "particle_name": case_result["particle_name"],
        "wavelength_nm": float(case_result["wavelength_m"] * 1e9),
        "width_nm": float(case_result["width_m"] * 1e9),
        "depth_nm": float(case_result["depth_m"] * 1e9),
        "ok": bool(case_result["ok"]),
        "error": case_result.get("error"),
    }


def _build_sweep_progress_state(
    *,
    total_cases: int,
    completed_cases: int,
    successful_cases: int,
    failed_cases: int,
    active_workers: int,
    elapsed_seconds: float,
    cases_per_second: float | None,
    estimated_total_seconds: float | None,
    estimated_remaining_seconds: float | None,
    last_case: dict | None,
) -> dict:
    """Build the canonical progress payload for parameter sweeps."""
    return {
        "stage": "sweep",
        "status": "running" if completed_cases < total_cases else "completed",
        "total_cases": int(total_cases),
        "completed_cases": int(completed_cases),
        "successful_cases": int(successful_cases),
        "failed_cases": int(failed_cases),
        "progress_fraction": (
            float(completed_cases / total_cases) if total_cases > 0 else 0.0
        ),
        "elapsed_seconds": float(elapsed_seconds),
        "cases_per_second": (
            float(cases_per_second)
            if cases_per_second is not None
            else None
        ),
        "estimated_total_seconds": (
            float(estimated_total_seconds)
            if estimated_total_seconds is not None
            else None
        ),
        "estimated_remaining_seconds": (
            float(estimated_remaining_seconds)
            if estimated_remaining_seconds is not None
            else None
        ),
        "active_workers": int(active_workers),
        "last_case": last_case,
    }


def _normalized_vectorized_fallback_reason(value: object) -> str:
    if value is None:
        return _NO_VECTORIZED_FALLBACK_REASON
    text = str(value)
    return text if text else _NO_VECTORIZED_FALLBACK_REASON


def _case_summary_from_result(result: dict) -> dict:
    summary = result.get("summary", result)
    return summary if isinstance(summary, dict) else {}


def summarize_vectorized_fallback_telemetry(results: list[dict]) -> dict[str, object]:
    """Aggregate vectorized event-engine routing and fallback reasons."""
    requested_engine_counts: Counter[str] = Counter()
    used_engine_counts: Counter[str] = Counter()
    fallback_reason_counts: Counter[str] = Counter()
    fallback_events_by_reason: Counter[str] = Counter()
    vectorized_requested_reason_counts: Counter[str] = Counter()
    case_count = 0
    event_count = 0
    vectorized_requested_case_count = 0
    vectorized_fallback_case_count = 0
    vectorized_fallback_event_count = 0
    configured_off_case_count = 0

    for result in results:
        summary = _case_summary_from_result(result)
        case_count += 1
        requested_engine = str(summary.get("vectorized_event_engine") or "missing")
        used_engine = str(summary.get("vectorized_event_engine_used") or "missing")
        reason = _normalized_vectorized_fallback_reason(
            summary.get("vectorized_event_engine_fallback_reason")
        )
        try:
            case_events = int(summary.get("n_events", 0) or 0)
        except (TypeError, ValueError):
            case_events = 0

        requested_engine_counts[requested_engine] += 1
        used_engine_counts[used_engine] += 1
        fallback_reason_counts[reason] += 1
        fallback_events_by_reason[reason] += max(case_events, 0)
        event_count += max(case_events, 0)

        if requested_engine == "off":
            configured_off_case_count += 1
        elif requested_engine != "missing":
            vectorized_requested_case_count += 1
            vectorized_requested_reason_counts[reason] += 1
            if reason != _NO_VECTORIZED_FALLBACK_REASON:
                vectorized_fallback_case_count += 1
                vectorized_fallback_event_count += max(case_events, 0)

    return {
        "telemetry_schema": "vectorized_fallback_telemetry_v1",
        "case_count": int(case_count),
        "event_count": int(event_count),
        "configured_off_case_count": int(configured_off_case_count),
        "vectorized_requested_case_count": int(vectorized_requested_case_count),
        "vectorized_fallback_case_count": int(vectorized_fallback_case_count),
        "vectorized_fallback_event_count": int(vectorized_fallback_event_count),
        "vectorized_fallback_fraction_of_all_cases": (
            float(vectorized_fallback_case_count / case_count)
            if case_count > 0
            else 0.0
        ),
        "vectorized_fallback_fraction_of_requested_cases": (
            float(vectorized_fallback_case_count / vectorized_requested_case_count)
            if vectorized_requested_case_count > 0
            else 0.0
        ),
        "vectorized_fallback_fraction_of_events": (
            float(vectorized_fallback_event_count / event_count)
            if event_count > 0
            else 0.0
        ),
        "requested_engine_counts": dict(sorted(requested_engine_counts.items())),
        "used_engine_counts": dict(sorted(used_engine_counts.items())),
        "fallback_reason_counts": dict(sorted(fallback_reason_counts.items())),
        "vectorized_requested_fallback_reason_counts": dict(
            sorted(vectorized_requested_reason_counts.items())
        ),
        "fallback_events_by_reason": dict(sorted(fallback_events_by_reason.items())),
    }


def _emit_progress_callback(
    *,
    progress_callback,
    progress_state: dict,
    verbose: bool,
    callback_error_policy: Literal["log", "raise"] = "log",
) -> None:
    """Best-effort dispatch of one sweep progress payload to the external callback."""
    if progress_callback is None:
        return
    try:
        progress_callback(dict(progress_state))
    except Exception as exc:
        _LOGGER.warning("Sweep progress callback failed", exc_info=True)
        if callback_error_policy == "raise":
            raise
        if verbose:
            print(f"[progress] callback failed: {exc}", flush=True)


def _emit_case_result_callback(
    *,
    case_result_callback,
    raw_result: dict,
    verbose: bool,
    callback_error_policy: Literal["log", "raise"] = "log",
) -> None:
    """Best-effort dispatch of one successful case payload to the external callback."""
    if case_result_callback is None:
        return
    try:
        case_result_callback(dict(raw_result))
    except Exception as exc:
        _LOGGER.warning("Sweep case-result callback failed", exc_info=True)
        if callback_error_policy == "raise":
            raise
        if verbose:
            print(f"[checkpoint] callback failed: {exc}", flush=True)


def _format_sweep_progress_line(progress_state: dict) -> str:
    """Render one compact human-readable progress line for stdout."""
    elapsed_seconds = float(progress_state["elapsed_seconds"])
    estimated_remaining_seconds = progress_state.get("estimated_remaining_seconds")
    cases_per_second = progress_state.get("cases_per_second")

    eta_str = "unknown"
    if isinstance(estimated_remaining_seconds, (int, float)) and math.isfinite(estimated_remaining_seconds):
        eta_str = f"{estimated_remaining_seconds:.1f}s"

    cps_str = "unknown"
    if isinstance(cases_per_second, (int, float)) and math.isfinite(cases_per_second):
        cps_str = f"{cases_per_second:.2f} cases/s"

    return (
        "[progress] "
        f"{progress_state['completed_cases']}/{progress_state['total_cases']} "
        f"({progress_state['progress_fraction'] * 100.0:.1f}%) | "
        f"ok={progress_state['successful_cases']} failed={progress_state['failed_cases']} | "
        f"elapsed={elapsed_seconds:.1f}s | eta={eta_str} | {cps_str}"
    )


def _format_sweep_case_label(case_result: dict) -> str:
    """Render the human-readable label for one sweep case."""
    return (
        f"  [{case_result['case_idx']}/{case_result['total_cases']}] "
        f"{case_result['particle_name']}, "
        f"λ={case_result['wavelength_m']*1e9:.0f}nm, "
        f"W={case_result['width_m']*1e9:.0f}nm, "
        f"H={case_result['depth_m']*1e9:.0f}nm"
    )


def _log_sweep_case_failure(case_result: dict, *, detailed_case_logging: bool) -> None:
    """Print the verbose failure message for one failed sweep case."""
    if detailed_case_logging:
        print(f"FAILED: {case_result['error']}", flush=True)
        return
    print(
        f"[warning] case {case_result['case_idx']}/{case_result['total_cases']} "
        f"failed: {case_result['error']}",
        flush=True,
    )


def _format_sweep_case_failure_summary(failures: list[dict], *, limit: int = 5) -> str:
    """Render failed case payloads into one actionable exception message."""
    total = len(failures)
    examples = [
        (
            "case "
            f"{failure.get('case_idx')}/{failure.get('total_cases')} "
            f"{failure.get('particle_name')} "
            f"lambda={float(failure.get('wavelength_m', 0.0)) * 1e9:.0f}nm "
            f"W={float(failure.get('width_m', 0.0)) * 1e9:.0f}nm "
            f"H={float(failure.get('depth_m', 0.0)) * 1e9:.0f}nm: "
            f"{failure.get('error')}"
        )
        for failure in failures[:limit]
    ]
    suffix = "" if total <= limit else f"; {total - limit} more failure(s) omitted"
    return (
        f"{total} sweep case failure(s); refusing to return partial results. "
        f"First failure(s): {'; '.join(examples)}{suffix}. "
        "Pass allow_partial=True only when a partial result set is intentional."
    )


def _validate_theta_grid_rad(theta_grid_rad: np.ndarray | None) -> np.ndarray:
    """Return a usable 1D theta grid or fail before any case execution starts."""
    if theta_grid_rad is None:
        raise ValueError("theta_grid_rad is required for run_parameter_sweep")
    theta_grid = np.asarray(theta_grid_rad, dtype=float)
    if theta_grid.ndim != 1 or theta_grid.size == 0:
        raise ValueError("theta_grid_rad must be a non-empty 1D array")
    return theta_grid


def _enforce_sweep_case_failure_policy(
    failed_case_results: list[dict],
    *,
    allow_partial: bool,
) -> None:
    """Raise on failed cases unless the caller explicitly requested partial output."""
    if failed_case_results and not allow_partial:
        raise SweepCaseFailureError(failed_case_results)


def _log_sweep_case_success(summary: dict) -> None:
    """Print the verbose success summary for one completed sweep case."""
    print(
        f"det_rate={summary['detection_rate']:.2f}, "
        f"mean_h={summary['mean_peak_height']:.4e}",
        flush=True,
    )


def build_sweep_case_key(
    particle_name: str,
    wavelength_m: float,
    width_m: float,
    depth_m: float,
) -> str:
    """Build a stable, hashable identity for one sweep case."""
    return "|".join(
        [
            str(particle_name),
            f"{float(wavelength_m):.12e}",
            f"{float(width_m):.12e}",
            f"{float(depth_m):.12e}",
        ]
    )


def _medium_identity_key(medium: Medium) -> tuple[object, ...]:
    """Build a stable cache key for one medium configuration."""
    return (
        str(medium.name),
        float(medium.refractive_index),
        None if medium.viscosity_Pa_s is None else float(medium.viscosity_Pa_s),
        None if medium.temperature_K is None else float(medium.temperature_K),
        medium.material_key,
        bool(medium.use_material_model),
    )


def _iter_case_specs(
    particle_types: list[Particle],
    media_by_particle_idx: list[Medium],
    width_list_m: np.ndarray,
    depth_list_m: np.ndarray,
    wavelength_list_m: np.ndarray,
    E_sca_ref_map: dict[float, float] | None,
    E_sca_ref: float | None,
    skip_case_keys: set[str] | None = None,
):
    """Yield one serializable case spec per sweep point."""
    total_cases = (
        len(particle_types) * len(wavelength_list_m)
        * len(width_list_m) * len(depth_list_m)
    )
    case_idx = 0

    for particle_idx, particle in enumerate(particle_types):
        case_medium = media_by_particle_idx[particle_idx]
        case_medium_key = _medium_identity_key(case_medium)
        for wavelength in wavelength_list_m:
            current_E_sca_ref = (
                E_sca_ref_map[case_medium_key][float(wavelength)]
                if E_sca_ref_map is not None and case_medium_key in E_sca_ref_map
                else E_sca_ref
            )

            for W in width_list_m:
                for H in depth_list_m:
                    case_idx += 1
                    case_key = build_sweep_case_key(
                        particle.name,
                        wavelength,
                        W,
                        H,
                    )
                    if skip_case_keys and case_key in skip_case_keys:
                        continue
                    yield {
                        "case_idx": case_idx,
                        "total_cases": total_cases,
                        "case_key": case_key,
                        "particle_idx": particle_idx,
                        "wavelength_m": float(wavelength),
                        "width_m": float(W),
                        "depth_m": float(H),
                        "E_sca_ref": current_E_sca_ref,
                    }


def _run_case_spec(case_spec: dict) -> dict:
    """Worker-safe execution of one sweep case."""
    shared_context = _get_worker_shared_context()
    if shared_context is None:
        raise RuntimeError("sweep worker shared context is not initialized")

    particle_idx = int(case_spec["particle_idx"])
    particle = shared_context["particle_types"][particle_idx]
    medium = shared_context["media_by_particle_idx"][particle_idx]
    optical = copy(shared_context["optical_template"])
    optical.wavelength_m = float(case_spec["wavelength_m"])
    channel = Channel(
        width_m=float(case_spec["width_m"]),
        depth_m=float(case_spec["depth_m"]),
    )
    sim_cfg = shared_context["sim_cfg"]
    theta_grid_rad = shared_context["theta_grid_rad"]

    case_t0 = time.perf_counter()
    try:
        batch = run_single_case_batch(
            particle,
            medium,
            channel,
            optical,
            sim_cfg,
            case_spec["E_sca_ref"],
            theta_grid_rad,
            retain_event_traces=False,
            stream_summary_only=True,
            intrinsic_cache=shared_context.get("intrinsic_cache"),
            reference_cache=shared_context.get("reference_cache"),
            collection_operator_cache=shared_context.get("collection_operator_cache"),
        )
    except Exception as exc:
        case_runtime_seconds = time.perf_counter() - case_t0
        return SweepCaseResult(
            ok=False,
            case_idx=case_spec["case_idx"],
            total_cases=case_spec["total_cases"],
            case_key=case_spec["case_key"],
            particle_name=particle.name,
            wavelength_m=optical.wavelength_m,
            width_m=channel.width_m,
            depth_m=channel.depth_m,
            case_runtime_seconds=case_runtime_seconds,
            error=str(exc),
        ).to_payload()

    case_runtime_seconds = time.perf_counter() - case_t0
    return SweepCaseResult(
        ok=True,
        case_idx=case_spec["case_idx"],
        total_cases=case_spec["total_cases"],
        case_key=case_spec["case_key"],
        particle_name=particle.name,
        wavelength_m=optical.wavelength_m,
        width_m=channel.width_m,
        depth_m=channel.depth_m,
        summary=batch["summary"],
        intrinsic=batch.get("intrinsic", {}),
        reference=batch.get("reference", {}),
        case_runtime_seconds=case_runtime_seconds,
    ).to_payload()


def _resolve_parallel_case_chunk_size(total_cases: int, n_workers: int) -> int:
    """Return a small worker task size that reduces IPC without hiding progress."""
    if total_cases <= 0 or n_workers <= 1:
        return 1
    target_chunks = max(1, n_workers * 16)
    return max(1, min(8, math.ceil(total_cases / target_chunks)))


def _iter_case_spec_chunks(case_specs, chunk_size: int):
    """Yield bounded chunks from a case-spec iterator."""
    resolved_chunk_size = max(1, int(chunk_size))
    chunk = []
    for case_spec in case_specs:
        chunk.append(case_spec)
        if len(chunk) >= resolved_chunk_size:
            yield tuple(chunk)
            chunk = []
    if chunk:
        yield tuple(chunk)


def _run_case_spec_chunk(case_spec_chunk: tuple[dict, ...]) -> list[dict]:
    """Run one small group of case specs inside a worker process."""
    return [_run_case_spec(case_spec) for case_spec in case_spec_chunk]


def _drain_parallel_cases(case_specs, n_workers: int, total_cases: int):
    """Process case specs with bounded in-flight chunks."""
    max_pending = max(1, n_workers * 2)
    chunk_size = _resolve_parallel_case_chunk_size(total_cases, n_workers)
    chunk_iter = iter(_iter_case_spec_chunks(case_specs, chunk_size))
    shared_context = _get_worker_shared_context()

    with ProcessPoolExecutor(
        max_workers=n_workers,
        initializer=_set_worker_shared_context,
        initargs=(shared_context,),
    ) as executor:
        pending = {}

        def _submit_next() -> bool:
            try:
                case_spec_chunk = next(chunk_iter)
            except StopIteration:
                return False
            future = executor.submit(_run_case_spec_chunk, case_spec_chunk)
            pending[future] = None
            return True

        for _ in range(max_pending):
            if not _submit_next():
                break

        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                pending.pop(future, None)
                yield from future.result()
                _submit_next()


def _emit_sweep_progress(
    *,
    progress_callback,
    progress_state: dict,
    verbose: bool,
    detailed_case_logging: bool,
    callback_error_policy: Literal["log", "raise"] = "log",
):
    """Emit a best-effort progress update to callback and/or stdout."""
    _emit_progress_callback(
        progress_callback=progress_callback,
        progress_state=progress_state,
        verbose=verbose,
        callback_error_policy=callback_error_policy,
    )

    if not verbose or detailed_case_logging:
        return

    print(_format_sweep_progress_line(progress_state), flush=True)


def compute_case_score(
    H_norm: float,
    R_norm: float,
    CV_norm: float,
    w_height: float = 1.0,
    w_rate: float = 1.0,
    w_cv: float = 1.0,
) -> float:
    """
    Compute a composite detectability score.

    J = w_height · H̃ + w_rate · R̃ - w_cv · CṼ

    Where H̃, R̃, CṼ are min-max normalized values.
    Higher score = better detectability.

    Args:
        H_norm: Normalized mean peak height [0,1].
        R_norm: Normalized detection rate [0,1].
        CV_norm: Normalized coefficient of variation [0,1]. Higher = worse.
        w_height, w_rate, w_cv: Weights.

    Returns:
        Score (float).
    """
    return w_height * H_norm + w_rate * R_norm - w_cv * CV_norm


def compute_engineering_score(
    stable_rate_norm: float,
    threshold_margin_norm: float,
    local_snr_norm: float,
    CV_norm: float,
    robust_CV_norm: float,
    phase_flip_penalty: float,
    event_artifact_risk_norm: float = 0.0,
    auc_norm: float = 0.0,
    hit_rate_norm: float = 0.0,
    d_prime_norm: float = 0.0,
    w_stable: float = 1.0,
    w_margin: float = 0.7,
    w_local_snr: float = 0.4,
    w_auc: float = 0.5,
    w_hit_rate: float = 0.5,
    w_dprime: float = 0.3,
    w_cv: float = 0.4,
    w_robust_cv: float = 0.4,
    w_flip: float = 0.5,
    w_event_artifact: float = 0.6,
) -> float:
    """
    Engineering-facing score that favors robust, clearly separated detections.

    It intentionally keeps the legacy `score` untouched so historical ranking
    behavior is preserved, while exposing a stricter alternative that prefers:
    - events detected reliably across the batch
    - peaks clearly above threshold
    - low variability
    - fewer polarity flips
    - lower event-QC artifact risk
    """
    return (
        w_stable * stable_rate_norm
        + w_margin * threshold_margin_norm
        + w_local_snr * local_snr_norm
        + w_auc * auc_norm
        + w_hit_rate * hit_rate_norm
        + w_dprime * d_prime_norm
        - w_cv * CV_norm
        - w_robust_cv * robust_CV_norm
        - w_flip * phase_flip_penalty
        - w_event_artifact * event_artifact_risk_norm
    )


def evaluate_engineering_gate(
    summary: dict,
    sim_cfg: SimulationConfig,
) -> dict:
    """
    Apply hard engineering accept/reject rules before final ranking.

    The gate is intentionally simple and auditable:
      1. enough detected events
      2. stable detections are frequent enough
      3. polarity flips are not excessive
      4. the average peak/threshold separation is still visibly above noise
    """
    failures = []
    basis_metrics = _resolve_summary_metrics_for_engineering_basis(
        summary,
        sim_cfg.engineering_decision_basis,
    )

    n_detected = int(basis_metrics["n_detected"] or 0)
    n_events = max(0, int(summary.get("n_events", 0) or 0))
    detection_rate_lb = float(basis_metrics["detection_rate_wilson_lb"] or 0.0)
    stable_rate = float(basis_metrics["stable_detection_rate_wilson_lb"] or 0.0)
    phase_flip = float(basis_metrics["phase_flip_fraction_wilson_ub"] or 0.0)
    mean_margin_z = float(basis_metrics["mean_peak_margin_z"] or 0.0)
    strict_paired_rate_lb = float(
        summary.get(
            "strict_paired_detection_rate_wilson_lb",
            summary.get(
                "paired_channel_detection_rate_wilson_lb",
                summary.get(
                    "strict_paired_detection_rate",
                    summary.get("paired_channel_detection_rate", 0.0),
                ),
            ),
        )
        or 0.0
    )
    strict_paired_requirement = float(
        sim_cfg.engineering_min_strict_paired_detection_rate
    )
    required_detected = max(
        int(sim_cfg.engineering_min_detected_events),
        int(math.ceil(sim_cfg.engineering_min_detected_fraction * n_events - 1e-12)),
    )

    if n_detected < required_detected:
        failures.append(
            f"n_detected<{required_detected}"
        )
    if detection_rate_lb < sim_cfg.engineering_min_detected_fraction:
        failures.append(
            f"{basis_metrics['detection_rate_label']}<{sim_cfg.engineering_min_detected_fraction:.2f}"
        )
    if stable_rate < sim_cfg.engineering_min_stable_detection_rate:
        failures.append(
            f"{basis_metrics['stable_detection_rate_label']}<{sim_cfg.engineering_min_stable_detection_rate:.2f}"
        )
    if phase_flip > sim_cfg.engineering_max_phase_flip_fraction:
        failures.append(
            f"{basis_metrics['phase_flip_fraction_label']}>{sim_cfg.engineering_max_phase_flip_fraction:.2f}"
        )
    if mean_margin_z < sim_cfg.engineering_min_mean_peak_margin_z:
        failures.append(
            f"{basis_metrics['mean_peak_margin_z_label']}<{sim_cfg.engineering_min_mean_peak_margin_z:.2f}"
        )
    if strict_paired_requirement > 0 and strict_paired_rate_lb < strict_paired_requirement:
        failures.append(
            f"strict_paired_detection_rate<{strict_paired_requirement:.2f}"
        )

    passed = len(failures) == 0
    reason = "PASS" if passed else " / ".join(failures)
    return {
        "engineering_gate_passed": passed,
        "engineering_gate_basis": basis_metrics["basis"],
        "engineering_gate_failed_count": len(failures),
        "engineering_gate_reason": reason,
        "engineering_gate_claim_scope": "candidate_family_proxy_only",
        "candidate_family_claim_allowed": True,
        "detector_resolved_claim_allowed": False,
        "absolute_snr_lod_claim_allowed": False,
        "biological_specificity_claim_allowed": False,
        "engineering_gate_required_detected_events": required_detected,
        "engineering_gate_detected_fraction_lb": detection_rate_lb,
        "engineering_gate_stable_detection_rate_lb": stable_rate,
        "engineering_gate_phase_flip_fraction_ub": phase_flip,
        "engineering_gate_mean_peak_margin_z": mean_margin_z,
        "engineering_gate_strict_paired_rate_lb": strict_paired_rate_lb,
        "engineering_gate_required_strict_paired_detection_rate": (
            strict_paired_requirement
        ),
    }


def compute_final_engineering_score(
    engineering_score: float,
    engineering_gate_passed: bool,
    engineering_gate_failed_count: int = 0,
) -> float:
    """
    Final engineering decision score.

    All gate-passing cases keep their continuous engineering_score.
    Failed cases are pushed far below the pass set while preserving a small
    ordering signal among themselves for debugging / comparison.
    """
    if engineering_gate_passed:
        return float(engineering_score)
    return float(-10.0 - float(engineering_gate_failed_count) + engineering_score)


def compute_final_engineering_rank(
    engineering_score: float,
    engineering_gate_passed: bool,
    engineering_gate_failed_count: int = 0,
) -> dict:
    """
    Explicit ranking components for final engineering decisions.

    This keeps the numeric `final_engineering_score` for heatmaps and simple
    plots, while also exposing the true lexicographic intent used by the UI:
      1. pass the engineering gate
      2. fail fewer gate conditions
      3. among comparable cases, prefer higher engineering_score
    """
    passed_rank = 1 if engineering_gate_passed else 0
    return {
        "final_engineering_gate_rank": passed_rank,
        "final_engineering_failure_rank": -int(engineering_gate_failed_count),
        "final_engineering_score_rank": float(engineering_score),
    }


def compute_joint_score(
    summary_a: dict,
    summary_b: dict,
    all_heights: list[float],
    all_rates: list[float],
    all_cvs: list[float],
    alpha: float = 0.5,
    score_weights: dict | None = None,
) -> float:
    """
    Dual-object joint score for system optimization.

    CONSTRAINT: Both objects MUST share the same system settings:
    - Same (W, H, λ) geometry and optical config
    - Same rho and reference_model / reference scaling
    - Same coupling_model and noise_model

    This reflects the physical reality that both particle types pass
    through the same detection system. Do NOT independently tune system
    parameters per object and then combine scores — that would represent
    two different instruments, not one optimized system.

    Args:
        summary_a: Batch summary for object A (e.g. gold).
        summary_b: Batch summary for object B (e.g. exosome).
        all_heights: All mean_peak_heights across the full sweep (for normalization).
        all_rates: All detection_rates across the full sweep.
        all_cvs: All finite CVs across the full sweep.
        alpha: Weight for object A. Object B gets (1 - alpha).
        score_weights: Optional dict with w_height, w_rate, w_cv.

    Returns:
        Joint score (float). Higher = better for both objects.
    """
    if score_weights is None:
        score_weights = {"w_height": 1.0, "w_rate": 1.0, "w_cv": 1.0}

    scores = []
    for summary in [summary_a, summary_b]:
        H_norm = min_max_normalize(summary["mean_peak_height"], all_heights)
        R_norm = min_max_normalize(summary["detection_rate"], all_rates)
        mh = summary["mean_peak_height"]
        sh = summary["std_peak_height"]
        cv = sh / mh if mh > 0 else float("inf")
        CV_norm = min_max_normalize(cv, all_cvs) if cv != float("inf") and all_cvs else 1.0
        scores.append(compute_case_score(H_norm, R_norm, CV_norm, **score_weights))

    return alpha * scores[0] + (1.0 - alpha) * scores[1]


def compute_robust_scores(
    results: list[dict],
    width_list_m: np.ndarray,
    depth_list_m: np.ndarray,
    wavelength_list_m: np.ndarray,
) -> list[dict]:
    """
    Compute robust neighborhood scores for each parameter point.

    For each (W, H, λ) point, the robust score is the mean of its own score
    and the scores of all direct neighbors in the (W, H, λ) grid. A high
    robust score means the entire neighborhood is good, not just an isolated
    peak.

    Args:
        results: List of result dicts from run_parameter_sweep (must have 'score').
        width_list_m: Width grid values.
        depth_list_m: Depth grid values.
        wavelength_list_m: Wavelength grid values.

    Returns:
        Same results list with added 'robust_score' key in each dict.
    """
    # Build lookup: (particle_name, W, H, λ) → score
    def _key(r):
        return (
            r["particle_name"],
            f"{r['width_m']:.12e}",
            f"{r['depth_m']:.12e}",
            f"{r['wavelength_m']:.12e}",
        )

    score_map = {}
    for r in results:
        score_map[_key(r)] = r.get("score", 0.0)

    w_list = sorted({float(w) for w in width_list_m})
    d_list = sorted({float(d) for d in depth_list_m})
    lam_list = sorted({float(l) for l in wavelength_list_m})

    def _neighbors(val, sorted_list):
        """Return val and its immediate neighbors in a sorted list."""
        idx = None
        for i, v in enumerate(sorted_list):
            if abs(v - val) < 1e-15:
                idx = i
                break
        if idx is None:
            return [val]
        result = [sorted_list[idx]]
        if idx > 0:
            result.append(sorted_list[idx - 1])
        if idx < len(sorted_list) - 1:
            result.append(sorted_list[idx + 1])
        return result

    for r in results:
        pname = r["particle_name"]
        W = float(r["width_m"])
        H = float(r["depth_m"])
        lam = float(r["wavelength_m"])

        neighbor_scores = []
        for nw in _neighbors(W, w_list):
            for nd in _neighbors(H, d_list):
                for nl in _neighbors(lam, lam_list):
                    key = (pname, f"{nw:.12e}", f"{nd:.12e}", f"{nl:.12e}")
                    if key in score_map:
                        neighbor_scores.append(score_map[key])

        r["robust_score"] = float(np.mean(neighbor_scores)) if neighbor_scores else 0.0

    return results


def run_parameter_sweep(
    particle_types: list[Particle],
    medium: Medium,
    width_list_m: np.ndarray,
    depth_list_m: np.ndarray,
    wavelength_list_m: np.ndarray,
    optical_template: OpticalSystem,
    sim_cfg: SimulationConfig,
    E_sca_ref: float | None = None,
    theta_grid_rad: np.ndarray = None,
    score_weights: dict | None = None,
    verbose: bool = True,
    baseline_particle: Particle | None = None,
    baseline_channel: Channel | None = None,
    n_workers: int | None = 1,
    progress_callback=None,
    progress_interval_s: float = 2.0,
    case_result_callback=None,
    resume_results: list[dict] | None = None,
    skip_case_keys: set[str] | None = None,
    medium_resolver: Callable[[Particle], Medium] | None = None,
    allow_partial: bool = False,
    callback_error_policy: Literal["log", "raise"] = "log",
) -> list[dict]:
    """
    Run full parameter sweep over (particle_types × W × H × λ).

    Supports per-wavelength normalization via sim_cfg.normalization_mode.
    When score_mode="joint", requires exactly 2 particle types and computes
    a combined score weighted by joint_alpha.

    Args:
        particle_types: List of Particle types to compare.
        medium: Default Medium used when medium_resolver is not provided.
        medium_resolver: Optional callback resolving one Medium per particle.
        width_list_m: Channel widths to scan.
        depth_list_m: Channel depths to scan.
        wavelength_list_m: Wavelengths to scan.
        optical_template: Template optical system (wavelength will be replaced).
        sim_cfg: Simulation config (shared across all cases).
        E_sca_ref: Global normalization constant (used when normalization_mode=
            "global_single_lambda"). Can be None if per_wavelength mode is used.
        theta_grid_rad: Global angle grid.
        score_weights: Optional dict with w_height, w_rate, w_cv.
        verbose: Print progress if True.
        baseline_particle: Particle used for per-wavelength baseline computation.
            Required when normalization_mode="per_wavelength".
        baseline_channel: Channel used when the collection angle depends on
            channel geometry. If omitted, baseline normalization falls back
            to optical.collection_theta_rad.
        n_workers: Number of worker processes. Use 1 for serial execution,
            or 0 to use all visible logical CPUs.
        progress_callback: Optional callable receiving periodic progress dicts.
        progress_interval_s: Minimum time between periodic progress updates.
        case_result_callback: Optional callable receiving one successful raw
            case result dict before final scoring/sorting.
        resume_results: Optional list of already computed raw case results to
            seed the sweep before final normalization/scoring.
        skip_case_keys: Optional set of case keys to skip recomputing.
        callback_error_policy: Use "log" to keep callbacks best-effort, or
            "raise" to fail the sweep when a progress/checkpoint callback fails.
        allow_partial: When True, return successful cases even if one or more
            cases failed. The default raises instead of silently returning a
            biased partial sweep.

    Returns:
        List of result dicts, sorted by score (descending).
        Each dict contains particle_name, wavelength, W, H, summary, score.
        If score_mode="joint", also contains joint_score and robust_score.
    """
    if score_weights is None:
        score_weights = {"w_height": 1.0, "w_rate": 1.0, "w_cv": 1.0}

    if callback_error_policy not in {"log", "raise"}:
        raise ValueError("callback_error_policy must be 'log' or 'raise'")

    theta_grid_rad = _validate_theta_grid_rad(theta_grid_rad)

    # Validate joint mode requirements
    if sim_cfg.score_mode == "joint" and len(particle_types) != 2:
        raise ValueError(
            f"score_mode='joint' requires exactly 2 particle types, "
            f"got {len(particle_types)}"
        )

    # Resolve normalization
    E_sca_ref_map = None
    if sim_cfg.normalization_mode == "per_wavelength":
        if baseline_particle is None:
            raise ValueError(
                "baseline_particle is required when normalization_mode='per_wavelength'"
            )
        media_by_key: dict[tuple[object, ...], Medium] = {}
        if medium_resolver is None:
            media_by_key[_medium_identity_key(medium)] = medium
        else:
            for particle in particle_types:
                resolved_medium = medium_resolver(particle)
                media_by_key[_medium_identity_key(resolved_medium)] = resolved_medium

        E_sca_ref_map = {
            medium_key: compute_baseline_normalization_per_wavelength(
                baseline_particle,
                resolved_medium,
                optical_template,
                wavelength_list_m,
                theta_grid_rad,
                channel=baseline_channel,
                sim_cfg=sim_cfg,
            )
            for medium_key, resolved_medium in media_by_key.items()
        }
        if verbose:
            print("Per-wavelength normalization:")
            for medium_key, ref_map in E_sca_ref_map.items():
                medium_name = str(media_by_key[medium_key].name)
                print(f"  medium={medium_name}")
                for wl, ref in sorted(ref_map.items()):
                    print(f"    λ={wl*1e9:.0f}nm → E_sca_ref={ref:.6e}")
            print()
    elif E_sca_ref is None:
        raise ValueError(
            "E_sca_ref is required when normalization_mode='global_single_lambda'"
        )

    media_by_particle_idx = [
        medium_resolver(particle) if medium_resolver is not None else medium
        for particle in particle_types
    ]

    worker_count = _resolve_worker_count(n_workers)
    if worker_count > 1:
        updated_env = _configure_parallel_worker_env()
        if verbose:
            print(f"Parallel sweep enabled with {worker_count} worker processes.", flush=True)
            if updated_env:
                print("Per-worker BLAS/OpenMP thread limits:", flush=True)
                for env_var, value in updated_env.items():
                    print(f"  {env_var}={value}", flush=True)
                print(flush=True)

    total_cases = (
        len(particle_types) * len(wavelength_list_m)
        * len(width_list_m) * len(depth_list_m)
    )
    detailed_case_logging = verbose and total_cases <= 200

    resume_results = list(resume_results or [])
    skipped_case_keys = set(skip_case_keys or set())
    results = list(resume_results)
    completed_cases = len(skipped_case_keys)
    failed_cases = 0
    failed_case_results: list[dict] = []
    sweep_start = time.perf_counter()
    last_progress_emit = sweep_start
    case_specs = _iter_case_specs(
        particle_types=particle_types,
        media_by_particle_idx=media_by_particle_idx,
        width_list_m=width_list_m,
        depth_list_m=depth_list_m,
        wavelength_list_m=wavelength_list_m,
        E_sca_ref_map=E_sca_ref_map,
        E_sca_ref=E_sca_ref,
        skip_case_keys=skipped_case_keys,
    )
    shared_context = {
        "particle_types": tuple(particle_types),
        "media_by_particle_idx": tuple(media_by_particle_idx),
        "optical_template": optical_template,
        "sim_cfg": sim_cfg,
        "theta_grid_rad": theta_grid_rad,
        "intrinsic_cache": {},
        "reference_cache": {},
        "collection_operator_cache": {},
    }
    _set_worker_shared_context(shared_context)

    try:
        if worker_count > 1:
            case_outputs = _drain_parallel_cases(case_specs, worker_count, total_cases)
        else:
            case_outputs = map(_run_case_spec, case_specs)

        initial_progress_state = _build_sweep_progress_state(
            total_cases=total_cases,
            completed_cases=completed_cases,
            successful_cases=len(results),
            failed_cases=0,
            active_workers=worker_count,
            elapsed_seconds=0.0,
            cases_per_second=None,
            estimated_total_seconds=None,
            estimated_remaining_seconds=None,
            last_case=None,
        )
        _emit_sweep_progress(
            progress_callback=progress_callback,
            progress_state=initial_progress_state,
            verbose=verbose,
            detailed_case_logging=detailed_case_logging,
            callback_error_policy=callback_error_policy,
        )

        for case_result in case_outputs:
            completed_cases += 1
            if verbose and detailed_case_logging:
                print(_format_sweep_case_label(case_result), end="... ", flush=True)

            if not case_result["ok"]:
                failed_cases += 1
                failed_case_results.append(case_result)
                if verbose:
                    _log_sweep_case_failure(
                        case_result,
                        detailed_case_logging=detailed_case_logging,
                    )
            else:
                summary = case_result["summary"]
                if verbose and detailed_case_logging:
                    _log_sweep_case_success(summary)

                raw_result = SweepRawResult.from_case_result(case_result).to_payload()
                results.append(raw_result)
                _emit_case_result_callback(
                    case_result_callback=case_result_callback,
                    raw_result=raw_result,
                    verbose=verbose,
                    callback_error_policy=callback_error_policy,
                )

            now = time.perf_counter()
            should_emit_progress = (
                completed_cases == total_cases
                or completed_cases == 1
                or (now - last_progress_emit) >= max(float(progress_interval_s), 0.1)
            )
            if should_emit_progress:
                elapsed_seconds = max(now - sweep_start, 1e-12)
                cases_per_second = completed_cases / elapsed_seconds
                estimated_total_seconds = (
                    total_cases / cases_per_second if cases_per_second > 0 else None
                )
                estimated_remaining_seconds = (
                    max(0.0, estimated_total_seconds - elapsed_seconds)
                    if estimated_total_seconds is not None
                    else None
                )
                progress_state = _build_sweep_progress_state(
                    total_cases=total_cases,
                    completed_cases=completed_cases,
                    successful_cases=len(results),
                    failed_cases=failed_cases,
                    active_workers=worker_count,
                    elapsed_seconds=elapsed_seconds,
                    cases_per_second=cases_per_second,
                    estimated_total_seconds=estimated_total_seconds,
                    estimated_remaining_seconds=estimated_remaining_seconds,
                    last_case=_build_sweep_last_case_snapshot(case_result),
                )
                _emit_sweep_progress(
                    progress_callback=progress_callback,
                    progress_state=progress_state,
                    verbose=verbose,
                    detailed_case_logging=detailed_case_logging,
                    callback_error_policy=callback_error_policy,
                )
                last_progress_emit = now
    finally:
        _set_worker_shared_context(None)

    _enforce_sweep_case_failure_policy(
        failed_case_results,
        allow_partial=allow_partial,
    )

    if not results:
        return results

    # ---- Unified normalization and scoring ----
    all_heights = [r["summary"]["mean_peak_height"] for r in results]
    all_rates = [r["summary"]["detection_rate"] for r in results]
    all_engineering_metrics = [
        _resolve_summary_metrics_for_engineering_basis(
            r["summary"],
            sim_cfg.engineering_decision_basis,
        )
        for r in results
    ]
    all_stable_rates_lb = [
        float(metrics["stable_detection_rate_wilson_lb"]) for metrics in all_engineering_metrics
    ]
    all_margin_z = [
        float(metrics["mean_peak_margin_z"]) for metrics in all_engineering_metrics
    ]
    all_auc = [
        r["summary"].get("roc_auc_event_vs_background", 0.5) for r in results
    ]
    all_hit_rates = [
        r["summary"].get("hit_rate_at_fixed_false_alarm", 0.0) for r in results
    ]
    all_d_prime = [
        r["summary"].get("d_prime_event_vs_background", 0.0) for r in results
    ]
    all_local_snr = [
        r["summary"].get("mean_local_snr", 0.0) for r in results
    ]
    all_event_artifact_risk = [
        r["summary"].get("event_artifact_risk_score", 0.0) or 0.0
        for r in results
    ]

    all_cvs = []
    all_robust_cvs = []
    for r in results:
        mean_h = float(r["summary"].get("mean_peak_height", 0.0) or 0.0)
        std_h = float(r["summary"].get("std_peak_height", 0.0) or 0.0)
        cv = std_h / mean_h if mean_h > 0 else float("inf")
        all_cvs.append(cv)
        robust_cv = r["summary"].get("robust_cv_peak_height", float("inf"))
        all_robust_cvs.append(robust_cv)
    finite_cvs = [c for c in all_cvs if c != float("inf")]
    finite_robust_cvs = [c for c in all_robust_cvs if c != float("inf")]

    for i, r in enumerate(results):
        H_norm = min_max_normalize(r["summary"]["mean_peak_height"], all_heights)
        R_norm = min_max_normalize(r["summary"]["detection_rate"], all_rates)

        cv_plain = all_cvs[i]
        if cv_plain != float("inf") and finite_cvs:
            CV_norm = min_max_normalize(cv_plain, finite_cvs)
        else:
            CV_norm = 1.0  # Worst case for infinite CV
        robust_cv = all_robust_cvs[i]
        if robust_cv != float("inf") and finite_robust_cvs:
            robust_CV_norm = min_max_normalize(robust_cv, finite_robust_cvs)
        else:
            robust_CV_norm = 1.0

        engineering_metrics = all_engineering_metrics[i]
        stable_rate_norm = min_max_normalize(
            float(engineering_metrics["stable_detection_rate_wilson_lb"]),
            all_stable_rates_lb,
        )
        threshold_margin_norm = min_max_normalize(
            float(engineering_metrics["mean_peak_margin_z"]),
            all_margin_z,
        )
        auc_norm = min_max_normalize(
            r["summary"].get("roc_auc_event_vs_background", 0.5),
            all_auc,
        )
        hit_rate_norm = min_max_normalize(
            r["summary"].get("hit_rate_at_fixed_false_alarm", 0.0),
            all_hit_rates,
        )
        d_prime_norm = min_max_normalize(
            r["summary"].get("d_prime_event_vs_background", 0.0),
            all_d_prime,
        )
        local_snr_norm = min_max_normalize(
            r["summary"].get("mean_local_snr", 0.0),
            all_local_snr,
        )
        event_artifact_risk_norm = min_max_normalize(
            r["summary"].get("event_artifact_risk_score", 0.0) or 0.0,
            all_event_artifact_risk,
        )

        r["score"] = compute_case_score(
            H_norm, R_norm, CV_norm, **score_weights
        )
        r["engineering_score"] = compute_engineering_score(
            stable_rate_norm,
            threshold_margin_norm,
            local_snr_norm,
            CV_norm,
            robust_CV_norm,
            float(engineering_metrics["phase_flip_fraction_wilson_ub"]),
            event_artifact_risk_norm=event_artifact_risk_norm,
            auc_norm=auc_norm,
            hit_rate_norm=hit_rate_norm,
            d_prime_norm=d_prime_norm,
        )
        gate = evaluate_engineering_gate(r["summary"], sim_cfg)
        r.update(gate)
        r["summary"].update(gate)
        if isinstance(r.get("reference"), dict):
            r["reference"].update(gate)
        gate_explanation = classify_engineering_gate_explanation(
            engineering_gate_passed=bool(r["engineering_gate_passed"]),
            engineering_gate_reason=str(r.get("engineering_gate_reason", "N/A")),
            engineering_gate_failed_count=int(
                r.get("engineering_gate_failed_count", 0)
            ),
        )
        r.update(gate_explanation)
        r["engineering_decision_basis"] = sim_cfg.engineering_decision_basis
        r["engineering_basis_n_detected"] = int(engineering_metrics["n_detected"])
        r["engineering_basis_detection_rate"] = float(
            engineering_metrics["detection_rate"]
        )
        r["engineering_basis_detection_rate_wilson_lb"] = float(
            engineering_metrics["detection_rate_wilson_lb"]
        )
        r["engineering_basis_stable_detection_rate"] = float(
            engineering_metrics["stable_detection_rate"]
        )
        r["engineering_basis_stable_detection_rate_wilson_lb"] = float(
            engineering_metrics["stable_detection_rate_wilson_lb"]
        )
        r["engineering_basis_phase_flip_fraction"] = float(
            engineering_metrics["phase_flip_fraction"]
        )
        r["engineering_basis_phase_flip_fraction_wilson_ub"] = float(
            engineering_metrics["phase_flip_fraction_wilson_ub"]
        )
        r["engineering_basis_mean_peak_margin_z"] = float(
            engineering_metrics["mean_peak_margin_z"]
        )
        r["final_engineering_score"] = compute_final_engineering_score(
            r["engineering_score"],
            r["engineering_gate_passed"],
            r["engineering_gate_failed_count"],
        )
        r.update(
            compute_final_engineering_rank(
                r["engineering_score"],
                r["engineering_gate_passed"],
                r["engineering_gate_failed_count"],
            )
        )
        r["H_norm"] = H_norm
        r["R_norm"] = R_norm
        r["CV_norm"] = CV_norm
        r["robust_CV_norm"] = robust_CV_norm
        r["stable_rate_norm"] = stable_rate_norm
        r["threshold_margin_norm"] = threshold_margin_norm
        r["auc_norm"] = auc_norm
        r["hit_rate_norm"] = hit_rate_norm
        r["d_prime_norm"] = d_prime_norm
        r["local_snr_norm"] = local_snr_norm
        r["event_artifact_risk_norm"] = event_artifact_risk_norm
        recommendation = classify_design_recommendation(
            engineering_gate_passed=bool(r["engineering_gate_passed"]),
            observation_freeze_status=str(
                r["summary"].get(
                    "observation_freeze_status",
                    "review_required_before_result_freeze",
                )
            ),
        )
        r.update(recommendation)
        r.update(
            {
                field: r["summary"].get(field)
                for field in (
                    DESIGN_CLAIM_GOVERNANCE_FIELDS
                    + EVENT_QC_DIAGNOSTIC_FIELDS
                    + SELECTION_FUNCTION_DIAGNOSTIC_FIELDS
                    + EV_POPULATION_PRIOR_DIAGNOSTIC_FIELDS
                    + COUNT_LIKELIHOOD_DIAGNOSTIC_FIELDS
                    + POPULATION_INFERENCE_DIAGNOSTIC_FIELDS
                    + OOD_DIAGNOSTIC_FIELDS
                    + BAYESIAN_CALIBRATION_DIAGNOSTIC_FIELDS
                    + EXPERIMENTAL_DESIGN_ADVISOR_FIELDS
                    + NODI_THERMAL_CONTAMINATION_FIELDS
                    + POLARIZATION_JONES_DIAGNOSTIC_FIELDS
                    + OBJECTIVE_PANEL_DIAGNOSTIC_FIELDS
                    + RUN_STATE_DIAGNOSTIC_FIELDS
                    + CHANNEL_GEOMETRY_DIAGNOSTIC_FIELDS
                    + ELECTROKINETIC_DIAGNOSTIC_FIELDS
                    + EV_INTEGRITY_DIAGNOSTIC_FIELDS
                    + EV_REPORTING_DIAGNOSTIC_FIELDS
                    + ASSAY_CONTROL_DIAGNOSTIC_FIELDS
                    + CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS
                    + RECOMPUTE_MANIFEST_DIAGNOSTIC_FIELDS
                    + BFP_DETECTOR_OPERATOR_DIAGNOSTIC_FIELDS
                    + PARTICLE_CHANNEL_PERTURBATION_DIAGNOSTIC_FIELDS
                    + TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS
                    + REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS
                    + FLUIDIC_RESISTANCE_DIAGNOSTIC_FIELDS
                    + FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS
                    + PARTICLE_DESIGN_LIBRARY_DIAGNOSTIC_FIELDS
                    + DESIGN_METRIC_DIAGNOSTIC_FIELDS
                    + EV_DESIGN_POSTPROCESS_FIELDS
                )
                if field in r["summary"]
            }
        )
        r["summary"].update(gate_explanation)
        r["summary"].update(recommendation)

    attach_anchor_equivalent_metrics(results)
    attach_reference_operating_metrics(results)
    attach_fluidic_practicality_metrics(results)
    attach_ev_design_postprocess(results)

    # ---- Joint scoring ----
    if sim_cfg.score_mode == "joint":
        # Group results by (W, H, λ)
        pair_map = {}  # (W_str, H_str, λ_str) → {particle_name: summary}
        for r in results:
            geo_key = (
                f"{r['width_m']:.12e}",
                f"{r['depth_m']:.12e}",
                f"{r['wavelength_m']:.12e}",
            )
            if geo_key not in pair_map:
                pair_map[geo_key] = {}
            pair_map[geo_key][r["particle_name"]] = r["summary"]

        p_names = [p.name for p in particle_types]
        for r in results:
            geo_key = (
                f"{r['width_m']:.12e}",
                f"{r['depth_m']:.12e}",
                f"{r['wavelength_m']:.12e}",
            )
            pair = pair_map.get(geo_key, {})
            if len(pair) == 2 and p_names[0] in pair and p_names[1] in pair:
                r["joint_score"] = compute_joint_score(
                    pair[p_names[0]], pair[p_names[1]],
                    all_heights, all_rates, finite_cvs,
                    alpha=sim_cfg.joint_alpha,
                    score_weights=score_weights,
                )
            else:
                r["joint_score"] = r["score"]  # fallback

    # ---- Robust neighborhood scoring ----
    compute_robust_scores(results, width_list_m, depth_list_m, wavelength_list_m)

    # Sort by score descending (use joint_score if in joint mode)
    if sim_cfg.score_mode == "joint":
        results.sort(key=lambda r: r.get("joint_score", r["score"]), reverse=True)
    else:
        results.sort(key=lambda r: r["score"], reverse=True)

    return results
