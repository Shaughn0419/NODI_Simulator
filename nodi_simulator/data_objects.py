"""
Package-local data objects for NODI interferometric simulation.

Semi-physical interferometric simulator with material-aware normalization.
All outputs are in arbitrary units for detectability ranking across (W, H, λ).

Contains 5 core dataclasses and their default instances.
"""

from dataclasses import dataclass, replace
import math
import os
from typing import Any
import numpy as np

DEFAULT_PATH_OPD_MODEL = "single_pass"
DEFAULT_PATH_OPD_REFERENCE_PLANE = "detector_projection_single_pass_surrogate"
DEFAULT_PATH_OPD_Z_GEOMETRY_FACTOR = 1.0

REFERENCE_ROUTE_OPTIONS = (
    "auto",
    "calibrated_primary",
    "paper_aligned_comparison",
    "engineering_fallback",
    "legacy_debug",
)
REFERENCE_ROUTE_MODEL_COMPATIBILITY = {
    "calibrated_primary": {"calibrated_lookup"},
    "paper_aligned_comparison": {
        "paper_aligned_phase_filter",
        "tsuyama_bfp_integrated",
    },
    "engineering_fallback": {"channel_angular_surrogate"},
    "legacy_debug": {"constant", "geometry_scaled"},
}
REFERENCE_SOLVER_ROUTE_OPTIONS = (
    "auto",
    "calibrated_lookup",
    "paper_aligned_angular_surrogate",
    "engineering_channel_angular_surrogate",
    "tsuyama_phase_filter_1d",
    "tsuyama_bfp_integrated",
    "legacy_debug",
)
REFERENCE_NA_EDGE_POLICY_OPTIONS = (
    "hard_guardrail",
    "soft_rolloff",
)
FLOW_CONTROL_MODE_OPTIONS = (
    "fixed_velocity",
    "fixed_pressure",
)
CHANNEL_CROSS_SECTION_MODEL_OPTIONS = (
    "ideal_rectangle",
    "rounded_rectangle",
    "trapezoid_tapered_sidewalls",
    "measured_profile_lookup",
)
DETECTOR_FORWARD_MODEL_OPTIONS = (
    "joint_overlap_coherent_surrogate",
    "collapsed_scalar_surrogate",
    "roi_intensity_integral",
    "roi_complex_mode_overlap_integral",
)
FIELD_COORDINATE_MEASURE_OPTIONS = (
    "theta_phi_surrogate",
    "solid_angle",
    "direction_cosine_uv",
)
COMPLEX_TIME_HARMONIC_CONVENTION_OPTIONS = (
    "exp_minus_i_omega_t",
)
FOURIER_TRANSFORM_SIGN_CONVENTION_OPTIONS = (
    "forward_exp_minus_i_q_x",
)
MIE_AMPLITUDE_PHASE_CONVENTION_OPTIONS = (
    "miepython_S1S2_complex",
)
INTERFERENCE_CONJUGATION_CONVENTION_OPTIONS = (
    "Re_Eref_conj_Esca",
)
GLOBAL_PHASE_OFFSET_SOURCE_OPTIONS = (
    "unmeasured_zero_reference",
    "calibrated_blank_reference",
    "external_metrology",
)
POLARIZATION_BASIS_MODEL_OPTIONS = (
    "scalar_parallel_perpendicular_surrogate",
)
JONES_BASIS_STATUS_OPTIONS = (
    "not_applied_scalar_projection",
)
POLARIZATION_JONES_OPERATOR_MODE_OPTIONS = (
    "scalar_projection",
    "jones_pupil_surrogate",
    "measured_jones_matrix",
)
VECTOR_OPTICS_MODE_OPTIONS = (
    "scalar_surrogate",
)
SCATTERING_NORMALIZATION_ROUTE_OPTIONS = (
    "baseline_particle_relative",
)
K_SCA_CALIBRATION_STATUS_OPTIONS = (
    "not_calibrated",
)
CALIBRATION_STATE_MACHINE_VERSION_OPTIONS = (
    "partial_calibration_state_v1",
)
DETECTOR_NOISE_MODEL_ROUTE_OPTIONS = (
    "surrogate",
)
PHOTON_UNIT_NOISE_MODEL_OPTIONS = (
    "not_applied",
    "calibrated_photon_units",
)
ABSOLUTE_THROUGHPUT_ROUTE_OPTIONS = (
    "unit_normalized_surrogate",
    "calibrated_operator_table",
)
DETECTOR_DYNAMIC_RANGE_MODEL_OPTIONS = (
    "not_applied",
)
ADC_DYNAMIC_RANGE_MODEL_OPTIONS = (
    "not_applied",
)
RIN_NOISE_MODEL_OPTIONS = (
    "not_applied",
)
SPECKLE_BACKGROUND_NOISE_MODEL_OPTIONS = (
    "not_applied",
)
BACKGROUND_FIELD_MODEL_OPTIONS = (
    "baseline_subtraction_surrogate",
)
TRANSMITTED_LEAKAGE_MODEL_OPTIONS = (
    "not_applied",
)
STRAY_LIGHT_MODEL_OPTIONS = (
    "not_applied",
)
PARTICLE_INDUCED_CHANNEL_PERTURBATION_MODEL_OPTIONS = (
    "not_applied",
    "excluded_volume_phase_surrogate",
    "born_phase_object",
    "full_phase_mask_recompute",
)
PARTICLE_CHANNEL_PERTURBATION_APPLICATION_MODE_OPTIONS = (
    "diagnostic_only",
    "alternative_forward_phase_lane",
    "coherent_addition_with_no_double_count_guard",
)
NODI_READOUT_SEMANTICS_OPTIONS = (
    "locked_carrier_surrogate",
    "bandpass_envelope_surrogate",
    "random_arrival_phase_lockin",
    "measured_transfer_function",
)
READOUT_PRESET_OPTIONS = (
    "exploratory_default",
    "EV_NODI_only_design",
    "tsuyama_2022_counting_10sigma",
    "tsuyama_2024_paired_5sigma",
    "tsuyama_2024_paired_10sigma",
)
READOUT_PRESET_CONFIG_OVERRIDES = {
    "exploratory_default": {
        "readout_observable_mode": "in_phase",
        "lockin_time_constant_s": 1.0e-3,
        "pod_lockin_frequency_Hz": 1200.0,
        "nodi_lockin_frequency_Hz": 2400.0,
        "pod_to_nodi_crosstalk": 0.05,
        "nodi_to_pod_crosstalk": 0.02,
        "threshold_sigma": 5.0,
        "threshold_tail": "two_sided",
        "min_peak_width_s": 2.5e-3,
        "min_peak_interval_s": 0.1,
        "detection_decision_mode": "single_channel",
        "pulse_detection_mode": "absolute",
        "pulse_pairing_tolerance_s": 5.0e-3,
        "engineering_decision_basis": "final_decision",
        "engineering_max_phase_flip_fraction": 0.5,
    },
    "EV_NODI_only_design": {
        "readout_observable_mode": "magnitude",
        "readout_internal_demod_route": "analytic_lockin_surrogate",
        "readout_anti_alias_policy": "analytic_demod_no_carrier_sampling",
        "nodi_readout_semantics": "bandpass_envelope_surrogate",
        "electronics_demod_phase_policy": "magnitude_only",
        "lockin_time_constant_s": 1.0e-3,
        "nodi_lockin_frequency_Hz": 2000.0,
        "threshold_sigma": 5.0,
        "threshold_tail": "one_sided",
        "min_peak_width_s": 2.5e-3,
        "min_peak_interval_s": 0.1,
        "detection_decision_mode": "single_channel",
        "pulse_detection_mode": "positive",
        "engineering_decision_basis": "single_channel",
        "engineering_max_phase_flip_fraction": 1.0,
    },
    "tsuyama_2022_counting_10sigma": {
        "readout_observable_mode": "magnitude",
        "lockin_time_constant_s": 1.0e-3,
        "pod_lockin_frequency_Hz": 1200.0,
        "nodi_lockin_frequency_Hz": 3000.0,
        "pod_to_nodi_crosstalk": 0.05,
        "nodi_to_pod_crosstalk": 0.02,
        "threshold_sigma": 10.0,
        "threshold_tail": "one_sided",
        "min_peak_width_s": 2.5e-3,
        "min_peak_interval_s": 0.1,
        "detection_decision_mode": "single_channel",
        "pulse_detection_mode": "positive",
        "pulse_pairing_tolerance_s": 5.0e-3,
        "engineering_decision_basis": "single_channel",
        "engineering_max_phase_flip_fraction": 1.0,
    },
    "tsuyama_2024_paired_5sigma": {
        "readout_observable_mode": "magnitude",
        "readout_internal_demod_route": "analytic_lockin_surrogate",
        "readout_anti_alias_policy": "analytic_demod_no_carrier_sampling",
        "lockin_time_constant_s": 1.0e-3,
        "pod_lockin_frequency_Hz": 4100.0,
        "nodi_lockin_frequency_Hz": 1200.0,
        "pod_to_nodi_crosstalk": 0.05,
        "nodi_to_pod_crosstalk": 0.02,
        "threshold_sigma": 5.0,
        "threshold_tail": "one_sided",
        "min_peak_width_s": 2.5e-3,
        "min_peak_interval_s": 0.1,
        "detection_decision_mode": "paired_channel",
        "pulse_detection_mode": "positive",
        "pulse_pairing_tolerance_s": 5.0e-2,
        "engineering_decision_basis": "paired_channel",
        "engineering_max_phase_flip_fraction": 1.0,
    },
    "tsuyama_2024_paired_10sigma": {
        "readout_observable_mode": "magnitude",
        "readout_internal_demod_route": "analytic_lockin_surrogate",
        "readout_anti_alias_policy": "analytic_demod_no_carrier_sampling",
        "lockin_time_constant_s": 1.0e-3,
        "pod_lockin_frequency_Hz": 4100.0,
        "nodi_lockin_frequency_Hz": 1200.0,
        "pod_to_nodi_crosstalk": 0.05,
        "nodi_to_pod_crosstalk": 0.02,
        "threshold_sigma": 10.0,
        "threshold_tail": "one_sided",
        "min_peak_width_s": 2.5e-3,
        "min_peak_interval_s": 0.1,
        "detection_decision_mode": "paired_channel",
        "pulse_detection_mode": "positive",
        "pulse_pairing_tolerance_s": 5.0e-2,
        "engineering_decision_basis": "paired_channel",
        "engineering_max_phase_flip_fraction": 1.0,
    },
}
READOUT_PRESET_PROVENANCE = {
    "exploratory_default": {
        "claim_level": "exploratory_phase_aware_surrogate",
        "threshold_scope": "shared_single_channel_threshold",
        "frequency_leakage_note": "engineering_default_fixed_crosstalk_constants",
        "paper_time_constant_range_s": None,
    },
    "EV_NODI_only_design": {
        "claim_level": "ev_nodi_envelope_surrogate_not_measured_transfer",
        "threshold_scope": "single_channel_positive_5sigma",
        "frequency_leakage_note": (
            "EV/NODI transient envelope governance; analytic lock-in surrogate "
            "does not claim a measured electronics transfer function"
        ),
        "paper_time_constant_range_s": None,
    },
    "tsuyama_2022_counting_10sigma": {
        "claim_level": "paper_counting_semantics_patch_not_physical_electronics",
        "threshold_scope": "shared_single_channel_positive_10sigma",
        "frequency_leakage_note": "single_nodi_lane_no_empirical_transfer_function",
        "paper_time_constant_range_s": (1.0e-3, 2.0e-3),
    },
    "tsuyama_2024_paired_5sigma": {
        "claim_level": "paper_paired_semantics_patch_not_physical_electronics",
        "threshold_scope": "shared_pod_nodi_positive_5sigma",
        "frequency_leakage_note": (
            "1.2kHz lane leakage risk retained; 3.1-4.1kHz lane cleaner "
            "range represented by configured POD frequency"
        ),
        "paper_time_constant_range_s": (1.0e-3, 2.0e-3),
    },
    "tsuyama_2024_paired_10sigma": {
        "claim_level": "paper_paired_semantics_patch_not_physical_electronics",
        "threshold_scope": "shared_pod_nodi_positive_10sigma",
        "frequency_leakage_note": (
            "1.2kHz lane leakage risk retained; 3.1-4.1kHz lane cleaner "
            "range represented by configured POD frequency"
        ),
        "paper_time_constant_range_s": (1.0e-3, 2.0e-3),
    },
}
ELECTRONICS_DEMOD_PHASE_POLICY_OPTIONS = (
    "locked_to_event_center",
    "random_arrival_phase",
    "recorded_reference_phase",
    "magnitude_only",
)
READOUT_INTERNAL_DEMOD_ROUTE_OPTIONS = (
    "sampled_carrier_demod_on_event_grid",
    "analytic_lockin_surrogate",
    "measured_transfer_function",
)
READOUT_ANTI_ALIAS_POLICY_OPTIONS = (
    "sampled_grid_nyquist_guard",
    "analytic_demod_no_carrier_sampling",
    "measured_transfer_function_guard",
)
LOCKIN_OUTPUT_UNIT_CONVENTION_OPTIONS = (
    "arbitrary_lockin_output_units",
    "rms_voltage",
    "peak_voltage",
    "peak_to_peak_voltage",
)
THRESHOLD_TAIL_OPTIONS = (
    "auto_by_detection_mode",
    "one_sided",
    "two_sided",
)
THRESHOLD_CALIBRATION_SOURCE_OPTIONS = (
    "gaussian_iid",
    "blank_trace_empirical",
    "block_bootstrap",
)
PULSE_DURATION_ESTIMATION_POLICY_OPTIONS = (
    "interpolated_threshold_crossing",
    "sample_span_conservative",
)
COLORED_NOISE_FALSE_ALARM_MODEL_OPTIONS = (
    "not_applied",
    "iid_gaussian_surrogate",
    "empirical_blank",
    "block_bootstrap",
)
PARTICLE_UNCERTAINTY_PROPAGATION_MODE_OPTIONS = (
    "none",
    "first_order_linear",
    "interval_bounds",
    "monte_carlo_ensemble",
)
PARTICLE_UNCERTAINTY_BUDGET_MODEL_OPTIONS = (
    "nominal_only",
    "metadata_only",
)
EV_ENSEMBLE_MODE_OPTIONS = (
    "nominal_single_preset",
    "explicit_preset_cases",
)
EV_SAMPLE_PREPARATION_PROFILE_OPTIONS = (
    "unknown",
    "SEC",
    "IEX",
    "UF",
    "UC",
    "PEG",
)
INITIAL_POSITION_DISTRIBUTION_MODE_OPTIONS = (
    "uniform",
    "center_biased_surrogate",
    "uniform_accessible_area",
    "flux_weighted",
    "flux_uniform_mixture_surrogate",
    "electrostatic_equilibrium",
    "measured_cross_section_distribution",
)
RANDOM_SEQUENCE_POLICY_OPTIONS = (
    "common_random_numbers",
    "case_keyed_independent",
)
EVENT_SAMPLING_POLICY_OPTIONS = (
    "random",
    "stratified_grid",
    "sobol_stratified",
)
ADAPTIVE_EVENT_BUDGET_MODE_OPTIONS = (
    "fixed",
    "wilson_precision",
)
VECTORIZED_EVENT_ENGINE_OPTIONS = (
    "off",
    "pure_advection_block",
    "event_block_v2",
    "event_block_v3",
)
EVENT_BLOCK_RNG_ORDER_OPTIONS = (
    "event_loop_order",
    "block_lane_order",
)
COUNT_PREDICTION_MODEL_OPTIONS = (
    "not_applied",
    "poisson_flux_deadtime_surrogate",
)
WALL_INTERACTION_MODEL_OPTIONS = (
    "none",
    "hard_exclusion",
    "electrostatic_DLVO_surrogate",
    "adsorption_loss_empirical",
)
ELECTROKINETIC_MODEL_OPTIONS = (
    "not_applied",
    "debye_layer_diagnostic",
    "boltzmann_wall_exclusion",
    "pressure_plus_eof_surrogate",
)
INTERFACE_CORRECTION_MODE_OPTIONS = (
    "off",
    "dipole_image_surrogate",
    "planar_interface_tmatrix",
    "fullwave",
)
INTERFACE_CORRECTION_PRIORITY_OPTIONS = (
    "all_particles",
    "EV_first",
    "exosome_first",
)
INTERFACE_CORRECTION_APPLIED_TO_OPTIONS = (
    "all_particles",
    "selected_family",
)
THERMAL_POD_MODEL_OPTIONS = (
    "unavailable",
    "surrogate_frequency_lane",
    "thermal_diffusion",
)
POD_ROI_SENSITIVITY_DERIVATIVE_STATUS_OPTIONS = (
    "unavailable",
    "scalar_approx",
    "field_derivative",
)
POD_SIGNAL_SIGN_SOURCE_OPTIONS = (
    "unavailable",
    "frequency_surrogate",
    "solvent_delta_n_scalar",
    "ROI_integrated_dIdtheta",
    "recomputed_thermal_field",
    "measured_phase",
)
POD_THERMAL_SPATIAL_DISTRIBUTION_STATUS_OPTIONS = (
    "ignored",
    "COMSOL_relative",
    "coupled_optical_thermal",
)
POD_ROI_DERIVATIVE_VALIDITY_OPTIONS = (
    "unavailable",
    "approximate",
    "validated",
)
DEFAULT_COORDINATE_FRAME_MAPPING = (
    "chip:x_width,y_flow,z_depth|optical:detector_projection_surrogate|bfp:theta_phi"
)


@dataclass(frozen=True)
class DesignObjectiveConfig:
    """Weights and thresholds for the first EV/NODI design-decision score."""

    target_family: str = "EV_sEV"
    anchor_particle_name: str = "gold_20nm"
    ev_size_quantiles_nm: tuple[float, ...] = (50.0, 70.0, 100.0, 150.0)
    ev_ensemble_group: str = "literature_bounds_2021"
    w_ev_worst_case: float = 0.35
    w_ev_d50: float = 0.15
    w_au20_anchor: float = 0.15
    w_reference: float = 0.10
    w_specificity_or_overlap: float = 0.10
    w_practicality_penalty: float = 0.10
    w_route_or_model_disagreement_penalty: float = 0.10
    au20_equivalent_green: float = 1.0
    au20_equivalent_yellow: float = 0.5

    def __post_init__(self):
        if not self.target_family:
            raise ValueError("target_family must be non-empty")
        if not self.anchor_particle_name:
            raise ValueError("anchor_particle_name must be non-empty")
        if not self.ev_size_quantiles_nm:
            raise ValueError("ev_size_quantiles_nm must contain at least one size")
        if any(size <= 0 for size in self.ev_size_quantiles_nm):
            raise ValueError("ev_size_quantiles_nm values must be positive")
        for name, value in {
            "w_ev_worst_case": self.w_ev_worst_case,
            "w_ev_d50": self.w_ev_d50,
            "w_au20_anchor": self.w_au20_anchor,
            "w_reference": self.w_reference,
            "w_specificity_or_overlap": self.w_specificity_or_overlap,
            "w_practicality_penalty": self.w_practicality_penalty,
            "w_route_or_model_disagreement_penalty": self.w_route_or_model_disagreement_penalty,
            "au20_equivalent_green": self.au20_equivalent_green,
            "au20_equivalent_yellow": self.au20_equivalent_yellow,
        }.items():
            if value < 0:
                raise ValueError(f"{name} must be non-negative, got {value}")
        if self.au20_equivalent_green < self.au20_equivalent_yellow:
            raise ValueError(
                "au20_equivalent_green must be >= au20_equivalent_yellow"
            )


DEFAULT_DESIGN_OBJECTIVE_CONFIG = DesignObjectiveConfig()


def resolve_reference_route_name(reference_model: str, reference_route: str = "auto") -> str:
    """Resolve the compatibility route used to interpret a reference model."""
    route = str(reference_route)
    model = str(reference_model)
    if route != "auto":
        compatible_models = REFERENCE_ROUTE_MODEL_COMPATIBILITY.get(route)
        if compatible_models is None:
            route = "auto"
        elif model in compatible_models:
            return route
        else:
            route = "auto"
    if route != "auto":
        return route
    if model == "calibrated_lookup":
        return "calibrated_primary"
    if model in {"paper_aligned_phase_filter", "tsuyama_bfp_integrated"}:
        return "paper_aligned_comparison"
    if model == "channel_angular_surrogate":
        return "engineering_fallback"
    return "legacy_debug"


def resolve_reference_solver_route_name(
    reference_model: str,
    reference_route: str = "auto",
    reference_solver_route: str = "auto",
) -> str:
    """Resolve the solver/provenance route beneath a reference model."""
    solver_route = str(reference_solver_route)
    if solver_route != "auto":
        return solver_route
    model = str(reference_model)
    resolved_route = resolve_reference_route_name(model, reference_route)
    if model == "calibrated_lookup":
        return "calibrated_lookup"
    if model == "tsuyama_bfp_integrated":
        return "tsuyama_bfp_integrated"
    if resolved_route == "paper_aligned_comparison":
        return "tsuyama_phase_filter_1d"
    if model == "paper_aligned_phase_filter":
        return "paper_aligned_angular_surrogate"
    if model == "channel_angular_surrogate":
        return "engineering_channel_angular_surrogate"
    return "legacy_debug"


@dataclass
class Particle:
    """
    Represents a single nanoparticle to be detected.

    Attributes:
        name: Descriptive name (e.g. "gold_40nm_diameter").
        radius_m: Particle radius in meters.
        n_real: Real part of refractive index (used when use_material_model=False).
        n_imag: Imaginary part of refractive index (used when use_material_model=False).
        model_type: Scattering model. "mie" for a homogeneous sphere, or
            "mie_core_shell" for a concentric core-shell sphere.
        material_key: Key into materials.MATERIAL_DB (e.g. "gold", "polystyrene").
        use_material_model: If True, n_complex_at() queries materials.py instead of
            using the fixed n_real/n_imag fields.
        structure_key: Optional structured-particle profile key. Used when
            model_type is not a homogeneous sphere.
        structure_params: Optional per-particle overrides for structured models.
    """
    name: str
    radius_m: float
    n_real: float
    n_imag: float = 0.0
    model_type: str = "mie"
    material_key: str | None = None
    use_material_model: bool = False
    structure_key: str | None = None
    structure_params: dict[str, Any] | None = None

    @property
    def n_complex(self) -> complex:
        """Complex refractive index ñ = n_real + i·n_imag (fixed, not wavelength-dependent)."""
        return complex(self.n_real, self.n_imag)

    def n_complex_at(self, wavelength_m: float) -> complex:
        """
        Return complex refractive index at a specific wavelength.

        If use_material_model=True, queries materials.py for wavelength-dependent data.
        Otherwise, returns the fixed n_complex.
        """
        if self.use_material_model:
            if self.material_key is None:
                raise ValueError(
                    "material_key must be set when use_material_model=True"
                )
            material_key = self.material_key
            from .materials import get_n_complex
            return get_n_complex(material_key, wavelength_m)
        return self.n_complex

    def __post_init__(self):
        if self.radius_m <= 0:
            raise ValueError(f"radius must be positive, got {self.radius_m}")
        if self.n_real < 0:
            raise ValueError(f"n_real must be non-negative, got {self.n_real}")
        if self.n_imag < 0:
            raise ValueError(f"n_imag must be non-negative, got {self.n_imag}")
        if self.use_material_model and self.material_key is None:
            raise ValueError("material_key must be set when use_material_model=True")
        if self.use_material_model and self.material_key is not None:
            from .materials import MATERIAL_DB
            if self.material_key not in MATERIAL_DB:
                from .materials import list_materials
                raise ValueError(
                    f"Unknown material_key '{self.material_key}' for Particle. "
                    f"Available: {list_materials()}"
                )
        if self.model_type == "mie_core_shell" and self.structure_key is None:
            raise ValueError(
                "structure_key must be set when model_type='mie_core_shell'"
            )


def make_gold_baseline_particle(
    diameter_nm: float = 40.0,
    *,
    use_material_model: bool = True,
    name: str = "gold_40nm_diameter",
) -> Particle:
    """
    Build the canonical gold baseline particle used for normalization.

    The default is material-model aware so per-wavelength normalization uses
    wavelength-specific Johnson & Christy data instead of a fixed 660 nm index.
    Set ``use_material_model=False`` only for legacy fixtures that intentionally
    need the old compact constant-index baseline.
    """
    return Particle(
        name=name,
        radius_m=float(diameter_nm) * 1e-9 / 2.0,
        n_real=0.164,
        n_imag=2.47,
        model_type="mie",
        material_key="gold",
        use_material_model=bool(use_material_model),
    )


@dataclass
class Medium:
    """
    Represents the liquid medium inside the nanochannel.

    Attributes:
        name: Descriptive name (e.g. "pbs_1x").
        refractive_index: Real refractive index of the medium (fixed value).
        viscosity_Pa_s: Dynamic viscosity (for diffusion).
        temperature_K: Temperature (for diffusion).
        material_key: Key into materials.MATERIAL_DB (e.g. "water").
        use_material_model: If True, refractive_index_at() queries materials.py.
        optical_material_key: Optional optical material key used for n(lambda).
        transport_material_key: Optional material key used for viscosity/density.
        thermal_material_key: Optional material key used for thermal properties.
    """
    name: str
    refractive_index: float
    viscosity_Pa_s: float | None = None
    temperature_K: float | None = None
    material_key: str | None = None
    use_material_model: bool = False
    optical_material_key: str | None = None
    transport_material_key: str | None = None
    thermal_material_key: str | None = None
    dn_dT: float | None = None
    density_kg_m3: float | None = None
    thermal_conductivity_W_mK: float | None = None
    thermal_diffusivity_m2_s: float | None = None
    osmolarity_or_solute_fraction: float | str | None = None
    source: str | None = None
    claim_level: str | None = None

    def refractive_index_at(self, wavelength_m: float) -> float:
        """
        Return the real refractive index at a specific wavelength.

        Note: Current workflows may use either water or 1x PBS depending on
        particle family. Both are treated as visible-range constants in the
        current implementation; wavelength dependence is not used in current
        conclusions.
        """
        if self.use_material_model:
            from .materials import get_n_complex
            material_key = self.optical_material_key or self.material_key
            if material_key is None:
                raise ValueError(
                    "material_key or optical_material_key must be set when "
                    "use_material_model=True"
                )
            n = get_n_complex(material_key, wavelength_m)
            return n.real
        return self.refractive_index

    def __post_init__(self):
        if self.refractive_index <= 0:
            raise ValueError(
                f"refractive_index must be positive, got {self.refractive_index}"
            )
        if self.use_material_model and not (self.optical_material_key or self.material_key):
            raise ValueError(
                "material_key or optical_material_key must be set when "
                "use_material_model=True"
            )
        material_keys = {
            self.material_key,
            self.optical_material_key,
            self.transport_material_key,
            self.thermal_material_key,
        }
        known_material_keys = {key for key in material_keys if key is not None}
        if known_material_keys:
            from .materials import MATERIAL_DB
            unknown_keys = sorted(key for key in known_material_keys if key not in MATERIAL_DB)
            if unknown_keys:
                from .materials import list_materials
                raise ValueError(
                    f"Unknown material key(s) {unknown_keys} for Medium. "
                    f"Available: {list_materials()}"
                )


@dataclass
class Channel:
    """
    Represents the nanochannel cross-section.

    Coordinate convention:
        x: channel width direction, range [-W/2, W/2]
        z: channel depth direction, range [-H/2, H/2]
        y: flow direction

    Attributes:
        width_m: Channel width W in meters. Scan range: 500–2000 nm.
        depth_m: Channel depth H in meters. Scan range: 500–2000 nm.
        wall_refractive_index: Refractive index of channel walls.
        material_name: Wall material name.
    """
    width_m: float
    depth_m: float
    wall_refractive_index: float = 1.46
    material_name: str = "fused_silica"
    wall_material_key: str | None = "fused_silica"

    def wall_refractive_index_at(self, wavelength_m: float) -> float:
        """
        Return the real refractive index of the channel wall at a specific wavelength.

        Note: The current default channel wall uses a fused-silica constant
        approximation (≈1.46) across the visible range. Wavelength dependence
        is not used in any current conclusions.
        """
        if self.wall_material_key is not None:
            from .materials import get_n_complex
            n = get_n_complex(self.wall_material_key, wavelength_m)
            return n.real
        return self.wall_refractive_index

    def __post_init__(self):
        if self.width_m <= 0:
            raise ValueError(f"width must be positive, got {self.width_m}")
        if self.depth_m <= 0:
            raise ValueError(f"depth must be positive, got {self.depth_m}")
        if self.wall_refractive_index <= 0:
            raise ValueError(
                f"wall_refractive_index must be positive, got {self.wall_refractive_index}"
            )


@dataclass
class OpticalSystem:
    """
    Describes the laser focusing and detection geometry.

    θ_det is read exclusively from collection_theta_rad by all modules.

    Attributes:
        wavelength_m: Laser wavelength in vacuum.
        peak_irradiance_W_m2: Peak intensity at focus (I₀).
        beam_waist_x/y/z_m: Legacy beam waist radii retained as backwards-
            compatible fallbacks.
        illumination_beam_waist_x/y/z_m: Optional explicit illumination waists
            used by beam-phase, pulse-width, and focus-crossing surrogates.
            In overfill mode, x/z can be flattened while the y waist still sets
            the finite transit window through the focal region.
        illumination_NA: Optional illumination-objective NA. When explicit
            illumination waists are not provided, x/z illumination geometry is
            derived as 0.61 * lambda / NA to match the Tsuyama 20x, NA=0.45
            overfill spot-size scale instead of reusing the legacy shared beam.
        focus_x/y/z_m: Focal point coordinates.
        collection_theta_rad: Detection polar angle (the SOLE source of θ_det).
        system_efficiency: Legacy metadata/cache discriminator, not a gain factor
            in current formulas.
        detection_mode: "NODI" for interferometric detection.
    """
    wavelength_m: float
    peak_irradiance_W_m2: float
    beam_waist_x_m: float
    beam_waist_y_m: float
    beam_waist_z_m: float
    illumination_beam_waist_x_m: float | None = None
    illumination_beam_waist_y_m: float | None = None
    illumination_beam_waist_z_m: float | None = None
    illumination_NA: float | None = 0.45
    focus_x_m: float = 0.0
    focus_y_m: float = 0.0
    focus_z_m: float = 0.0
    collection_theta_rad: float = math.pi / 2
    system_efficiency: float = 1.0  # Legacy metadata; not multiplied into formulas.
    detection_mode: str = "NODI"
    NA_collection: float = 0.9  # Collection objective numerical aperture.
    # Used for the physical NA cutoff check: if the nanochannel first-order
    # diffraction angle arcsin(λ/(n·W)) exceeds arcsin(NA/n), no diffracted
    # reference light reaches the detector and NODI fails.
    # Typical values: 0.9 (air/water high-NA objective, Tsuyama 2022).
    # [Added: Tsuyama et al. 2022 alignment fix; 工程文件 41_实验对齐原则 Principle 1]

    def __post_init__(self):
        if self.wavelength_m <= 0:
            raise ValueError(f"wavelength must be positive, got {self.wavelength_m}")
        if self.peak_irradiance_W_m2 <= 0:
            raise ValueError(
                f"peak_irradiance must be positive, got {self.peak_irradiance_W_m2}"
            )
        if self.beam_waist_x_m <= 0:
            raise ValueError(
                f"beam_waist_x must be positive, got {self.beam_waist_x_m}"
            )
        if self.beam_waist_y_m <= 0:
            raise ValueError(
                f"beam_waist_y must be positive, got {self.beam_waist_y_m}"
            )
        if self.beam_waist_z_m <= 0:
            raise ValueError(
                f"beam_waist_z must be positive, got {self.beam_waist_z_m}"
            )
        for name, value in {
            "illumination_beam_waist_x_m": self.illumination_beam_waist_x_m,
            "illumination_beam_waist_y_m": self.illumination_beam_waist_y_m,
            "illumination_beam_waist_z_m": self.illumination_beam_waist_z_m,
        }.items():
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive when set, got {value}")
        if self.illumination_NA is not None and not (0.0 < self.illumination_NA <= 2.0):
            raise ValueError(
                f"illumination_NA must be in (0, 2] when set, got {self.illumination_NA}"
            )
        if not (0 < self.collection_theta_rad < math.pi):
            raise ValueError(
                f"collection_theta must be in (0, pi), got {self.collection_theta_rad}"
            )
        if not (0.0 < self.NA_collection <= 2.0):
            raise ValueError(
                f"NA_collection must be in (0, 2], got {self.NA_collection}"
            )

    def resolve_illumination_geometry(self) -> dict[str, float | str | bool]:
        """
        Resolve the illumination geometry used by beam-phase surrogates.

        Priority:
          1. explicit illumination_beam_waist_x/y/z_m overrides
          2. objective-NA surrogate: 0.61 * lambda / illumination_NA
          3. legacy shared beam_waist_x/y/z_m fallback
        """
        derived_from_na = None
        if self.illumination_NA is not None:
            derived_from_na = 0.61 * float(self.wavelength_m) / float(self.illumination_NA)

        wx = (
            float(self.illumination_beam_waist_x_m)
            if self.illumination_beam_waist_x_m is not None
            else (
                float(derived_from_na)
                if derived_from_na is not None
                else float(self.beam_waist_x_m)
            )
        )
        wy = (
            float(self.illumination_beam_waist_y_m)
            if self.illumination_beam_waist_y_m is not None
            else (
                float(derived_from_na)
                if derived_from_na is not None
                else float(self.beam_waist_y_m)
            )
        )
        wz = (
            float(self.illumination_beam_waist_z_m)
            if self.illumination_beam_waist_z_m is not None
            else (
                float(derived_from_na)
                if derived_from_na is not None
                else float(self.beam_waist_z_m)
            )
        )

        if (
            self.illumination_beam_waist_x_m is not None
            or self.illumination_beam_waist_y_m is not None
            or self.illumination_beam_waist_z_m is not None
        ):
            source = "explicit_illumination_beam"
        elif derived_from_na is not None:
            source = "objective_na_surrogate"
        else:
            source = "legacy_shared_beam"

        return {
            "illumination_beam_waist_x_m": wx,
            "illumination_beam_waist_y_m": wy,
            "illumination_beam_waist_z_m": wz,
            "illumination_geometry_source": source,
            "illumination_geometry_decoupled_from_legacy_shared_beam": bool(
                source != "legacy_shared_beam"
            ),
        }


@dataclass
class SimulationConfig:
    """
    Simulation control parameters.

    Attributes:
        total_time_s: Total simulation duration. Must be >= 10× transit duration.
        sampling_rate_Hz: Temporal sampling rate.
        mean_flow_velocity_m_s: Average flow velocity along y.
        flow_control_mode: Whether fluidic diagnostics are interpreted as fixed
            velocity or fixed pressure. The trajectory solver remains
            fixed-velocity in P0.
        flow_control_pressure_Pa: Nominal pressure drop used for fixed-pressure
            diagnostics.
        fluidic_channel_length_m: Effective hydraulic channel length used by
            resistance diagnostics.
        channel_cross_section_model: Parameterized geometry model used for
            effective accessible-area and phase-mask diagnostics.
        sidewall_taper_angle_deg: Sidewall taper angle for the trapezoid
            surrogate. Positive values make the bottom width narrower than the
            nominal top width.
        corner_radius_nm: Rounded-corner radius for the rounded-rectangle
            surrogate.
        surface_roughness_rms_nm: RMS roughness metadata for background
            scattering diagnostics.
        width_along_channel_cv: Width variation coefficient along the flow axis.
        depth_along_channel_cv: Depth variation coefficient along the flow axis.
        measured_profile_path: Optional measured cross-section profile path for
            future lookup-based geometry.
        include_diffusion: Enable Brownian diffusion.
        diffusion_coefficient_m2_s: Diffusion coefficient.
        phase_model: Scattering phase model.
        reference_model: Reference field model.
        reference_route: Higher-level interpretation route for reference_model.
            "auto" preserves old configs and resolves from reference_model.
        reference_solver_route: Solver/provenance route under reference_model.
            In auto mode, paper-aligned comparisons export tsuyama_phase_filter_1d
            diagnostics while retaining the current angular surrogate bridge
            until BFP-to-detector integration is complete.
        reference_calibration_path: Optional blank-channel reference calibration
            table for calibrated_lookup mode.
        reference_interference_on: Whether the channel-derived reference field
            participates in the interferometric cross-term.
        reference_phase_grating_mode: Which depth-phase-grating surrogate is
            used by the channel-diffraction reference model. The frozen mainline
            is "phase_grating_sine"; the old linearized sinc response is
            retained only as a diagnostic comparison path.
        reference_width_saturation_mode: Whether the width-direction angular
            surrogate keeps a narrow-channel soft cutoff. The frozen mainline
            is "waveguide_cutoff_surrogate"; "none" retains the old pure-sinc
            width response for diagnostics / compatibility.
        reference_width_saturation_cutoff_ratio: Soft cutoff ratio applied to
            `W / λ_eff` when the narrow-channel width saturation surrogate is
            active.
        reference_na_edge_policy: Whether NA cutoff remains a hard guardrail or
            is also reported as a soft edge rolloff diagnostic.
        reference_na_rolloff_width_deg: Angular width for the soft NA edge
            rolloff diagnostic.
        nanoconfinement_on: Whether particle transport keeps the channel-confined
            surrogate (restricted cross-section + hindered transport).
        background_subtraction_on: Whether the detector baseline |E_ref|^2 is
            subtracted before the downstream readout chain.
        collection_angle_model: How to resolve the effective detection angle.
        collection_integration_mode: How the angular collection kernel is applied.
        collection_sigma_rad: Width of the angular theta-kernel.
        collection_phi_sigma_rad: Azimuthal width used by the 2D pupil/slit surrogate.
        slit_phi_limit_rad: Half-width of the slit acceptance in azimuth.
        collection_operator_calibration_path: Optional blank-image / slit-scan
            calibration table for theta/phi operator geometry and absolute
            throughput.
        collection_operator_id: Optional identifier used to select one operator
            row from a multi-operator calibration table.
        path_opd_model: How the scattering-side path surrogate defines the
            z-direction optical path difference relative to the reference-side
            surrogate plane. The default frozen mainline is
            DEFAULT_PATH_OPD_MODEL="single_pass"; the roundtrip-like option is
            retained as a diagnostic comparison surrogate.
        scattering_projection_mode: Which scattering-field proxy is fed into the
            interference model.
        illumination_polarization_mode: How the illumination envelope projects
            onto the active scattering channel.
        reference_projection_mode: How the reference field projects onto the
            active scattering channel.
        cross_polarization_leakage: Residual amplitude kept when illumination or
            reference is forced into the orthogonal polarization channel.
        polarization_jones_operator_mode: Polarization/Jones operator interface
            route. The current implementation is diagnostic-only and does not
            load measured Jones matrices.
        interference_overlap_mode: How the interference cross-term is evaluated.
            The current frozen mainline is "joint_overlap_integrated"; the
            collapsed scalar path is retained as a legacy-compatible audit
            alternative.
        detector_forward_model: Higher-level detector forward-equation claim.
            The default names the current joint-overlap coherent surrogate; it
            is not a photon-unit detector or full intensity-integral model.
        objective_candidate_id: Optical hardware profile identifier used for
            design-claim governance. P0 treats this as schema/claim metadata,
            not an active objective sweep.
        field_coordinate_measure: Coordinate measure used for angular fields.
        bfp_to_angle_jacobian_applied: Whether a calibrated BFP-to-angle
            Jacobian has been applied. The current angular surrogate leaves this
            false and reports that limitation in diagnostics.
        detector_mask_units: Units for the current detector/slit mask.
        coordinate_frame_mapping: Explicit chip / optical / BFP frame mapping.
        complex_time_harmonic_convention: Time-harmonic sign convention used by
            complex fields.
        fourier_transform_sign_convention: Fourier sign convention for BFP
            diagnostic solvers.
        mie_amplitude_phase_convention: Complex Mie amplitude convention used
            when exposing S1/S2 fields.
        interference_conjugation_convention: Which field is conjugated in the
            interference cross-term.
        global_phase_offset_source: Whether an external phase zero is known.
        polarization_basis_model: Current polarization-basis representation.
        jones_basis_status: Whether Jones vectors/matrices are actually applied.
        vector_optics_mode: Vector-optics fidelity currently claimed by the
            detector and basis bridge.
        measured_jones_matrix_path: Optional measured Jones matrix calibration
            path reserved for the future measured calibration lane.
        scattering_normalization_route: Route used to convert Mie scattering
            fields into the runtime detected-field scale.
        K_sca_calibration_status: Standard-particle scattering-scale calibration
            status. Current implementation deliberately exposes not_calibrated.
        standard_particle_calibration_path: Optional standard-particle
            calibration table for a lumped K_sca scale and global phase offset.
        standard_particle_calibration_id: Optional identifier used to select one
            standard-particle calibration row.
        calibration_state_machine_version: Version tag for route-level output
            claim diagnostics.
        detector_noise_model_route: Noise-model route currently used before
            readout. The current implementation is an engineering surrogate.
        photon_unit_noise_model: Photon-counting / photodiode-unit model status.
        absolute_throughput_route: Whether collection throughput is calibrated
            in absolute units.
        detector_dynamic_range_model: Saturation/dynamic-range model status.
        adc_dynamic_range_model: ADC range / quantization model status.
        rin_noise_model: Relative-intensity-noise model status.
        speckle_background_noise_model: Speckle-like blank background status.
        background_field_model: Background-field model for residual blank light.
        transmitted_leakage_model: Residual transmitted leakage status.
        stray_light_model: Stray-light background status.
        particle_induced_channel_perturbation_model: Whether particle-induced
            perturbation of the channel/reference field is modeled.
        particle_channel_perturbation_application_mode: Whether a particle-channel
            perturbation is diagnostic-only, evaluated as an alternative lane, or
            coherently added to the main signal path.
        readout_preset: Named readout/threshold/paper-counting contract.
        nodi_readout_semantics: Whether NODI event readout is treated as a
            legacy phase-locked carrier surrogate, transient envelope surrogate,
            random-arrival lock-in surrogate, or measured transfer function.
        electronics_demod_phase_policy: How the event arrival phase is related
            to the lock-in demodulation reference.
        readout_internal_demod_route: Whether carrier demodulation is sampled,
            analytic, or delegated to a measured transfer function.
        readout_anti_alias_policy: Guard policy for carrier sampling and
            post-lock-in output-grid semantics.
        lockin_output_unit_convention: Reported lock-in output unit convention.
        lockin_gain_chain: Gain-chain provenance for lock-in output units.
        threshold_tail: One-sided/two-sided false-alarm tail semantics for the
            active pulse detection threshold.
        threshold_calibration_source: Source used to interpret threshold sigma.
        colored_noise_false_alarm_model: Whether lock-in colored-noise false
            alarm is empirically modeled.
        blank_false_positive_calibration_path: Optional empirical blank-trace
            summary table for threshold and colored-noise false-positive rates.
        blank_false_positive_calibration_id: Optional identifier used to select
            one blank false-positive calibration row.
        raw_blank_trace_path: Optional future raw blank trace input. The current
            runtime exposes only an API boundary and does not bootstrap traces.
        bfp_roi_mask_path: Optional future BFP pixel-to-angle ROI mask input.
            The current runtime exposes only an API boundary.
        tsuyama_bfp_roi_mode: ROI mask used by the Tsuyama BFP integrated
            comparison lane.
        tsuyama_bfp_transmitted_block_fraction: Fraction of the NA q cutoff
            blocked around q=0 by the slit surrogate.
        tsuyama_bfp_lobe_center_fraction: Fraction of the NA q cutoff used as the
            off-axis lobe center for the slit surrogate.
        tsuyama_bfp_lobe_sigma_fraction: Fraction of the NA q cutoff used as the
            off-axis lobe Gaussian sigma.
        particle_uncertainty_propagation_mode: How particle/material uncertainty
            is propagated into output metrics.
        particle_uncertainty_budget_model: Whether particle/material uncertainty
            is only nominal metadata or actively modeled.
        EV_ensemble_mode: How EV/sEV optical ensembles are represented.
        EV_sample_preparation_profile: Sample-preparation metadata profile used
            by EV/contaminant design-library weighting diagnostics.
        count_prediction_model: Whether per-event detection is converted into
            an experiment-level concentration-to-count prediction.
        number_concentration_m3: Particle number concentration used by the count
            prediction route.
        count_observation_window_s: Counting window for Poisson expected counts.
            Defaults to `total_time_s` when omitted.
        count_dead_time_s: Non-paralyzable dead time used by the count route.
        wall_interaction_model: Wall interaction / loss model for count flux.
        electrokinetic_model: Surface-charge transport sensitivity model.
        zeta_potential_particle_mV: Optional particle zeta potential metadata.
        zeta_potential_wall_mV: Optional wall zeta potential metadata.
        ionic_strength_M: Optional ionic-strength metadata for wall interaction.
        electroosmotic_flow_fraction: Optional EOF contribution metadata.
        adsorption_probability_per_length_m: Optional empirical adsorption loss
            probability per meter for future count/loss models.
        interface_correction_mode: Interface correction fidelity for the
            homogeneous-medium Mie / core-shell approximation.
        interface_correction_priority: Which particle family is prioritized when
            a correction route is family-gated.
        interface_correction_applied_to: Whether interface correction targets all
            particles or only a selected family.
        thermal_pod_model: Photothermal POD source / heat-diffusion model status.
        pod_roi_sensitivity_derivative_status: Whether ROI-integrated POD
            `dI/dtheta` is unavailable, approximate, or field-derived.
        pod_signal_sign_source: Source allowed to assign POD quantitative sign.
        pod_thermal_spatial_distribution_status: Thermal spatial distribution
            provenance for POD amplitude/sign interpretation.
        pod_roi_derivative_validity: Validation level for the POD ROI derivative.
        probe_wavelength_m: Probe wavelength for coherent `E_ref + E_sca`.
            Defaults to the optical case wavelength when omitted.
        excitation_wavelength_m: POD excitation wavelength for absorption/heat
            bookkeeping. It is never coherently added to the probe field.
        probe_power_W: Optional probe power metadata.
        excitation_power_W: Optional excitation power metadata.
        wavelength_lane_id: Optional explicit lane id for wavelength-calibration maps.
        medium_optical_material_key: Optional medium key for n(lambda) diagnostics.
        medium_transport_material_key: Optional medium key for viscosity/density diagnostics.
        medium_thermal_material_key: Optional medium key for thermal diagnostics.
        probe_power_by_wavelength_W: Optional lane-specific probe power map.
        detector_responsivity_by_wavelength: Optional lane-specific detector map.
        filter_transmission_by_wavelength: Optional lane-specific objective/filter map.
        reference_calibration_by_wavelength: Optional lane-specific reference map.
        pulse_detection_mode: How pulse extraction interprets the trace polarity.
        readout_observable_mode: Which lock-in observable is exported to the
            detector thresholding layer.
        event_qc_min_pass_fraction: Minimum stable/pass fraction required for the
            event QC gate.
        event_qc_max_artifact_risk_score: Maximum batch artifact risk allowed by
            the event QC gate.
        pod_frequency_response_model: POD frequency-response surrogate.
        pod_frequency_response_reference_Hz: Reference frequency used to
            normalize the POD response gain.
        pod_frequency_response_exponent: Exponent in the inverse-frequency POD
            response surrogate.
        pod_frequency_response_min_gain: Lower clip bound for the POD response gain.
        pod_frequency_response_max_gain: Upper clip bound for the POD response gain.
        nodi_transit_response_model: NODI transit-time bandwidth surrogate.
        nodi_transit_response_min_gain: Lower clip bound for the NODI transit gain.
        nodi_transit_response_max_gain: Upper clip bound for the NODI transit gain.
        noise_std: Additive pre-readout Gaussian noise standard deviation (raw detector layer).
        shot_noise_scale: Baseline/intensity-dependent shot-noise surrogate scale
            applied before the readout stage.
        evaluation_false_alarm_rate: Target false-alarm rate used when converting
            event/background score distributions into a hit-rate metric.
        selected_annulus_edge_norm_min: Inner edge-norm bound for the
            selected-annulus analysis lens. This is a paper-alignment / audit
            denominator and does not replace the all-crossing engineering gate.
        selected_annulus_edge_norm_max: Outer edge-norm bound for the
            selected-annulus analysis lens.
        pulse_pairing_tolerance_s: Maximum allowed POD/NODI peak-time mismatch
            when computing the minimal two-channel pulse-pairing diagnostic.
        initial_position_distribution_mode: How initial `(x0, z0)` positions are
            sampled inside the transport cross-section. `uniform` keeps the
            legacy accessible-area behavior, while `flux_weighted` samples
            crossing events proportional to the local axial transport velocity.
            `flux_uniform_mixture_surrogate` interpolates between those two
            event-population assumptions.
        initial_position_center_bias_strength: Strength of the centered occupancy
            surrogate when the diagnostic center-biased mode is active.
        initial_position_center_bias_min_confinement_ratio: Minimum confinement
            ratio `a / min(W/2, H/2)` before the centered occupancy surrogate
            starts deviating from uniform sampling.
        initial_position_flux_weighted_mixture_fraction: Probability of drawing
            a flux-weighted event in `flux_uniform_mixture_surrogate` mode.
        post_readout_noise_std: Additional noise added after the readout surrogate.
        threshold_sigma: Number of robust std deviations for pulse threshold.
        min_peak_width_s: Minimum acceptable peak width.
        min_peak_interval_s: Minimum interval between consecutive peaks.
        pulse_width_measure_mode: Whether min_peak_width_s is interpreted as
            scipy peak width or continuous duration above the threshold.
        pulse_duration_estimation_policy: How threshold-crossing duration is
            measured when `pulse_width_measure_mode="duration_above_threshold"`.
            The conservative policy is useful for coarse logger samples because
            it avoids interpolating beyond observed above-threshold samples.
        pulse_extraction_sampling_interval_s: Optional data-logger interval used
            to resample post-readout traces before thresholding and pulse
            extraction. `None` keeps the internal simulation grid.
        post_readout_colored_noise_std: Optional AR(1)-like post-readout
            colored-noise standard deviation, used as a blank/background
            surrogate in sensitivity lanes.
        post_readout_colored_noise_tau_s: Correlation time for the colored
            post-readout noise surrogate.
        n_events: Number of events per batch.
        random_seed: RNG seed for reproducibility.
        random_sequence_policy: How case-level random streams are seeded.
            `common_random_numbers` preserves the legacy behavior and reuses
            the same sequence across cases for paired comparisons.
            `case_keyed_independent` derives a stable independent stream per
            particle/channel/wavelength case.
        event_sampling_policy: How event initial positions are sampled.
            `random` preserves legacy random positions; `stratified_grid` and
            `sobol_stratified` use low-variance position samples and therefore
            intentionally change numerical estimates.
        adaptive_event_budget_mode: Whether to run exactly n_events or stop
            early when Wilson intervals reach the configured precision target.
        vectorized_event_engine: Optional event-loop execution engine. `off`
            preserves the scalar event loop; `pure_advection_block` batches
            non-diffusive stream-summary cases; `event_block_v2` also batches
            diffusion-enabled stream-summary cases; `event_block_v3` further
            replaces per-event peak extraction with a block summary path and
            intentionally records that the optimized numerical path was used.
        event_block_size: Maximum events per vectorized block.
        event_block_rng_order: Random draw ordering used by event_block_v2/v3.
            `event_loop_order` preserves scalar event-loop draw order for exact
            regression comparisons. `block_lane_order` uses independent
            per-lane block streams and may change individual event trajectories
            while preserving the configured distributions.
        rho: |E_ref|/|E_sca_ref| ratio. Model parameter, NOT a physical constant.
    """
    total_time_s: float
    sampling_rate_Hz: float
    mean_flow_velocity_m_s: float
    flow_control_mode: str = "fixed_velocity"
    flow_control_pressure_Pa: float = 1000.0
    fluidic_channel_length_m: float = 1.0e-2
    channel_cross_section_model: str = "ideal_rectangle"
    sidewall_taper_angle_deg: float = 0.0
    corner_radius_nm: float = 0.0
    surface_roughness_rms_nm: float = 0.0
    width_along_channel_cv: float = 0.0
    depth_along_channel_cv: float = 0.0
    measured_profile_path: str | None = None
    include_diffusion: bool = False
    diffusion_coefficient_m2_s: float | None = None
    flow_profile_model: str = "plug"  # "plug", "parabolic_rect", or "rect_series"
    diffusion_hindrance_model: str = "none"  # "none", "near_wall_surrogate", or "anisotropic_tensor_surrogate"
    phase_model: str = "relative_surrogate"
    reference_model: str = "channel_angular_surrogate"
    reference_calibration_path: str | None = None
    reference_interference_on: bool = True
    reference_spatial_mode: str = "cross_section_surrogate"  # "uniform" or "cross_section_surrogate"
    reference_phase_grating_mode: str = "phase_grating_sine"  # "phase_grating_sine" or "legacy_sinc_linearized"
    reference_width_saturation_mode: str = "waveguide_cutoff_surrogate"  # "waveguide_cutoff_surrogate" or "none"
    reference_width_saturation_cutoff_ratio: float = 0.75
    reference_na_edge_policy: str = "hard_guardrail"
    reference_na_rolloff_width_deg: float = 2.0
    reference_spatial_amplitude_strength: float = 0.35
    reference_spatial_phase_strength_rad: float = math.pi / 5
    reference_spatial_min_amplitude_scale: float = 0.2
    nanoconfinement_on: bool = True
    background_subtraction_on: bool = True
    free_solution_window_scale: float = 3.0
    collection_angle_model: str = "channel_diffraction"  # "fixed" or "channel_diffraction"
    collection_integration_mode: str = "pupil_slit_surrogate"  # "single_angle", "gaussian_weighted", "pupil_slit_surrogate"
    collection_sigma_rad: float = 0.12
    collection_phi_sigma_rad: float = 0.35
    slit_phi_limit_rad: float = 0.45
    collection_operator_calibration_path: str | None = None
    collection_operator_id: str | None = None
    path_opd_model: str = DEFAULT_PATH_OPD_MODEL  # "single_pass", "reference_plane_roundtrip_surrogate", or "wall_referenced_gap_surrogate"
    scattering_projection_mode: str = "parallel"  # "parallel" main path; "intensity_proxy" kept as legacy compatibility
    illumination_polarization_mode: str = "match_scattering"  # "match_scattering", "parallel", "perpendicular", or "unpolarized"
    reference_projection_mode: str = "match_scattering"  # "match_scattering", "parallel", "perpendicular", or "unpolarized"
    cross_polarization_leakage: float = 0.05
    polarization_jones_operator_mode: str = "scalar_projection"
    interference_overlap_mode: str = "joint_overlap_integrated"  # "collapsed_then_multiplied" or "joint_overlap_integrated"
    diffraction_order: int = 1
    pulse_detection_mode: str = "absolute"  # "positive" or "absolute"
    detection_decision_mode: str = "single_channel"  # "single_channel" or "paired_channel"
    engineering_decision_basis: str = "final_decision"  # "final_decision", "single_channel", or "paired_channel"
    readout_model: str = "lockin_surrogate"  # "raw" or "lockin_surrogate"
    readout_observable_mode: str = "in_phase"  # "in_phase" or "magnitude"
    lockin_time_constant_s: float = 1.0e-3
    # Tsuyama 2022/2024 reports a 1-2 ms lock-in time constant range.
    # The current machine-facing default uses 1 ms because hardware settings
    # are discrete (1 ms / 2 ms), and 1.5 ms is not directly selectable.
    pod_lockin_frequency_Hz: float = 1200.0
    nodi_lockin_frequency_Hz: float = 2400.0
    pod_reference_phase_rad: float = 0.0
    nodi_reference_phase_rad: float = 0.0
    pod_frequency_response_model: str = "inverse_power_surrogate"  # "flat" or "inverse_power_surrogate"
    pod_frequency_response_reference_Hz: float = 1200.0
    pod_frequency_response_exponent: float = 1.0
    pod_frequency_response_min_gain: float = 0.25
    pod_frequency_response_max_gain: float = 4.0
    nodi_transit_response_model: str = "time_constant_surrogate"  # "flat" or "time_constant_surrogate"
    nodi_transit_response_min_gain: float = 0.2
    nodi_transit_response_max_gain: float = 1.0
    pod_to_nodi_crosstalk: float = 0.05
    nodi_to_pod_crosstalk: float = 0.02
    noise_std: float = 0.0
    shot_noise_scale: float = 0.0
    evaluation_false_alarm_rate: float = 0.05
    selected_annulus_edge_norm_min: float = 0.5
    selected_annulus_edge_norm_max: float = 0.8
    pulse_pairing_tolerance_s: float = 5.0e-3
    initial_position_distribution_mode: str = "uniform"
    initial_position_center_bias_strength: float = 1.0
    initial_position_center_bias_min_confinement_ratio: float = 0.08
    initial_position_flux_weighted_mixture_fraction: float = 0.5
    post_readout_noise_std: float = 0.0
    threshold_sigma: float = 5.0
    event_qc_min_pass_fraction: float = 0.5
    event_qc_max_artifact_risk_score: float = 0.5
    stable_detection_margin_z_min: float = 1.0
    engineering_min_detected_events: int = 5
    engineering_min_detected_fraction: float = 0.1
    engineering_min_stable_detection_rate: float = 0.2
    engineering_min_strict_paired_detection_rate: float = 0.0
    engineering_max_phase_flip_fraction: float = 0.5
    engineering_min_mean_peak_margin_z: float = 0.5
    min_peak_width_s: float = 2.5e-3
    min_peak_interval_s: float = 0.1
    pulse_width_measure_mode: str = "peak_width"
    pulse_duration_estimation_policy: str = "interpolated_threshold_crossing"
    pulse_extraction_sampling_interval_s: float | None = None
    n_events: int = 50
    random_seed: int | None = None
    random_sequence_policy: str = "common_random_numbers"
    event_sampling_policy: str = "random"
    adaptive_event_budget_mode: str = "fixed"
    adaptive_min_events: int = 10
    adaptive_check_interval: int = 5
    adaptive_wilson_half_width_target: float = 0.05
    vectorized_event_engine: str = "off"
    event_block_size: int = 32
    event_block_rng_order: str = "event_loop_order"
    rho: float = 0.5
    normalization_mode: str = "per_wavelength"  # or "global_single_lambda"
    ref_alpha: float = 0.0     # W dependence exponent
    ref_beta: float = 0.0      # H dependence exponent
    ref_gamma: float = 0.0     # λ dependence exponent
    ref_g_min: float = 0.01    # minimum g to prevent numerical collapse
    ref_phi0_rad: float = 0.0  # reference phase for geometry_scaled mode
    coupling_model: str = "constant"  # "constant" or "gaussian_xy"
    illumination_mode: str = "overfill"  # "overfill" or "tight_focus"
    # "overfill": beam spot >> channel (Tsuyama 2022 method, NA=0.45 illumination,
    #   ~2μm spot >> 800nm channel) → x/z illumination is nearly uniform across
    #   particle paths, while the y-axis transit window through focus remains finite.
    # "tight_focus": standard Gaussian beam waist from OpticalSystem; edge particles
    #   are penalized by exp(-(x/w)²). Use for sub-channel-width beam experiments.
    # [Added: Tsuyama et al. 2022 alignment fix; 工程文件 41_实验对齐原则 Principle 2]
    noise_model: str = "gaussian"  # "gaussian" or "gaussian_plus_drift"
    drift_slope: float = 0.0  # linear drift slope (signal units per second)
    post_readout_drift_slope: float = 0.0  # post-readout baseline drift (signal units per second)
    post_readout_colored_noise_std: float = 0.0
    post_readout_colored_noise_tau_s: float = 1.0e-3
    reflecting_boundary: bool = True  # reflecting boundary for Brownian diffusion
    score_mode: str = "single"  # "single" or "joint"
    joint_alpha: float = 0.5  # weight for object A in joint scoring
    reference_route: str = "auto"  # appended for positional compatibility
    detector_forward_model: str = "joint_overlap_coherent_surrogate"
    objective_candidate_id: str = "current_control"
    detector_mode_definition: str = "shared_collection_operator_scalar_mode"
    field_coordinate_measure: str = "theta_phi_surrogate"
    bfp_to_angle_jacobian_applied: bool = False
    detector_mask_units: str = "radian_surrogate"
    coordinate_frame_mapping: str = DEFAULT_COORDINATE_FRAME_MAPPING
    reference_solver_route: str = "auto"
    tsuyama_phase_filter_grid_n: int = 2048
    tsuyama_phase_filter_grid_extent_factor: float = 8.0
    tsuyama_bfp_roi_mode: str = "symmetric_na_aperture"
    tsuyama_bfp_transmitted_block_fraction: float = 0.15
    tsuyama_bfp_lobe_center_fraction: float = 0.55
    tsuyama_bfp_lobe_sigma_fraction: float = 0.18
    complex_time_harmonic_convention: str = "exp_minus_i_omega_t"
    fourier_transform_sign_convention: str = "forward_exp_minus_i_q_x"
    mie_amplitude_phase_convention: str = "miepython_S1S2_complex"
    interference_conjugation_convention: str = "Re_Eref_conj_Esca"
    global_phase_offset_source: str = "unmeasured_zero_reference"
    polarization_basis_model: str = "scalar_parallel_perpendicular_surrogate"
    jones_basis_status: str = "not_applied_scalar_projection"
    vector_optics_mode: str = "scalar_surrogate"
    measured_jones_matrix_path: str | None = None
    scattering_normalization_route: str = "baseline_particle_relative"
    K_sca_calibration_status: str = "not_calibrated"
    standard_particle_calibration_path: str | None = None
    standard_particle_calibration_id: str | None = None
    calibration_state_machine_version: str = "partial_calibration_state_v1"
    detector_noise_model_route: str = "surrogate"
    photon_unit_noise_model: str = "not_applied"
    absolute_throughput_route: str = "unit_normalized_surrogate"
    detector_dynamic_range_model: str = "not_applied"
    adc_dynamic_range_model: str = "not_applied"
    rin_noise_model: str = "not_applied"
    speckle_background_noise_model: str = "not_applied"
    background_field_model: str = "baseline_subtraction_surrogate"
    transmitted_leakage_model: str = "not_applied"
    stray_light_model: str = "not_applied"
    particle_induced_channel_perturbation_model: str = "not_applied"
    particle_channel_perturbation_application_mode: str = "diagnostic_only"
    readout_preset: str = "exploratory_default"
    nodi_readout_semantics: str = "locked_carrier_surrogate"
    electronics_demod_phase_policy: str = "locked_to_event_center"
    readout_internal_demod_route: str = "sampled_carrier_demod_on_event_grid"
    readout_anti_alias_policy: str = "sampled_grid_nyquist_guard"
    lockin_output_unit_convention: str = "arbitrary_lockin_output_units"
    lockin_gain_chain: str = "mixer_x2_then_first_order_lowpass_no_instrument_gain"
    threshold_tail: str = "two_sided"
    threshold_calibration_source: str = "gaussian_iid"
    colored_noise_false_alarm_model: str = "not_applied"
    blank_false_positive_calibration_path: str | None = None
    blank_false_positive_calibration_id: str | None = None
    raw_blank_trace_path: str | None = None
    bfp_roi_mask_path: str | None = None
    particle_uncertainty_propagation_mode: str = "none"
    particle_uncertainty_budget_model: str = "nominal_only"
    EV_ensemble_mode: str = "nominal_single_preset"
    EV_sample_preparation_profile: str = "unknown"
    count_prediction_model: str = "not_applied"
    number_concentration_m3: float | None = None
    count_observation_window_s: float | None = None
    count_dead_time_s: float = 0.0
    wall_interaction_model: str = "none"
    electrokinetic_model: str = "not_applied"
    zeta_potential_particle_mV: float | None = None
    zeta_potential_wall_mV: float | None = None
    ionic_strength_M: float | None = None
    electroosmotic_flow_fraction: float | None = None
    adsorption_probability_per_length_m: float = 0.0
    interface_correction_mode: str = "off"
    interface_correction_priority: str = "EV_first"
    interface_correction_applied_to: str = "all_particles"
    thermal_pod_model: str = "unavailable"
    pod_roi_sensitivity_derivative_status: str = "unavailable"
    pod_signal_sign_source: str = "unavailable"
    pod_thermal_spatial_distribution_status: str = "ignored"
    pod_roi_derivative_validity: str = "unavailable"
    probe_wavelength_m: float | None = None
    excitation_wavelength_m: float | None = None
    probe_power_W: float | None = None
    excitation_power_W: float | None = None
    wavelength_lane_id: str | None = None
    medium_optical_material_key: str | None = None
    medium_transport_material_key: str | None = None
    medium_thermal_material_key: str | None = None
    probe_power_by_wavelength_W: dict[str | int | float, float] | None = None
    detector_responsivity_by_wavelength: dict[str | int | float, float] | None = None
    filter_transmission_by_wavelength: dict[str | int | float, float] | None = None
    reference_calibration_by_wavelength: dict[str | int | float, object] | None = None

    @property
    def dt_s(self) -> float:
        """Time step in seconds."""
        return 1.0 / self.sampling_rate_Hz

    @property
    def n_samples(self) -> int:
        """Total number of time samples."""
        return int(self.total_time_s * self.sampling_rate_Hz)

    def __post_init__(self):
        if self.total_time_s <= 0:
            raise ValueError(f"total_time must be positive, got {self.total_time_s}")
        if self.sampling_rate_Hz <= 0:
            raise ValueError(
                f"sampling_rate must be positive, got {self.sampling_rate_Hz}"
            )
        if self.mean_flow_velocity_m_s <= 0:
            raise ValueError(
                f"velocity must be positive, got {self.mean_flow_velocity_m_s}"
            )
        if self.flow_control_mode not in FLOW_CONTROL_MODE_OPTIONS:
            raise ValueError(
                "flow_control_mode must be one of "
                f"{FLOW_CONTROL_MODE_OPTIONS}, got {self.flow_control_mode}"
            )
        if self.flow_control_pressure_Pa < 0:
            raise ValueError(
                "flow_control_pressure_Pa must be non-negative, got "
                f"{self.flow_control_pressure_Pa}"
            )
        if self.fluidic_channel_length_m <= 0:
            raise ValueError(
                "fluidic_channel_length_m must be positive, got "
                f"{self.fluidic_channel_length_m}"
            )
        if self.channel_cross_section_model not in CHANNEL_CROSS_SECTION_MODEL_OPTIONS:
            raise ValueError(
                "channel_cross_section_model must be one of "
                f"{CHANNEL_CROSS_SECTION_MODEL_OPTIONS}, got "
                f"{self.channel_cross_section_model}"
            )
        if not (0.0 <= self.sidewall_taper_angle_deg < 45.0):
            raise ValueError(
                "sidewall_taper_angle_deg must be in [0, 45), got "
                f"{self.sidewall_taper_angle_deg}"
            )
        if self.corner_radius_nm < 0.0:
            raise ValueError(
                f"corner_radius_nm must be non-negative, got {self.corner_radius_nm}"
            )
        if self.surface_roughness_rms_nm < 0.0:
            raise ValueError(
                "surface_roughness_rms_nm must be non-negative, got "
                f"{self.surface_roughness_rms_nm}"
            )
        if self.width_along_channel_cv < 0.0:
            raise ValueError(
                "width_along_channel_cv must be non-negative, got "
                f"{self.width_along_channel_cv}"
            )
        if self.depth_along_channel_cv < 0.0:
            raise ValueError(
                "depth_along_channel_cv must be non-negative, got "
                f"{self.depth_along_channel_cv}"
            )
        if self.rho <= 0:
            raise ValueError(f"rho must be positive, got {self.rho}")
        if self.stable_detection_margin_z_min < 0:
            raise ValueError(
                "stable_detection_margin_z_min must be >= 0, "
                f"got {self.stable_detection_margin_z_min}"
            )
        if not (0.0 <= self.evaluation_false_alarm_rate < 1.0):
            raise ValueError(
                "evaluation_false_alarm_rate must be in [0, 1), "
                f"got {self.evaluation_false_alarm_rate}"
            )
        if not (
            0.0
            <= float(self.selected_annulus_edge_norm_min)
            < float(self.selected_annulus_edge_norm_max)
            <= 1.0
        ):
            raise ValueError(
                "selected_annulus_edge_norm_min/max must satisfy "
                "0 <= min < max <= 1, got "
                f"{self.selected_annulus_edge_norm_min}/"
                f"{self.selected_annulus_edge_norm_max}"
            )
        if self.pulse_pairing_tolerance_s <= 0:
            raise ValueError(
                "pulse_pairing_tolerance_s must be positive, "
                f"got {self.pulse_pairing_tolerance_s}"
            )
        if self.engineering_min_detected_events < 0:
            raise ValueError(
                "engineering_min_detected_events must be >= 0, "
                f"got {self.engineering_min_detected_events}"
            )
        if not (0.0 <= self.engineering_min_detected_fraction <= 1.0):
            raise ValueError(
                "engineering_min_detected_fraction must be in [0, 1], "
                f"got {self.engineering_min_detected_fraction}"
            )
        if not (0.0 <= self.engineering_min_stable_detection_rate <= 1.0):
            raise ValueError(
                "engineering_min_stable_detection_rate must be in [0, 1], "
                f"got {self.engineering_min_stable_detection_rate}"
            )
        if not (0.0 <= self.engineering_min_strict_paired_detection_rate <= 1.0):
            raise ValueError(
                "engineering_min_strict_paired_detection_rate must be in [0, 1], "
                f"got {self.engineering_min_strict_paired_detection_rate}"
            )
        if not (0.0 <= self.engineering_max_phase_flip_fraction <= 1.0):
            raise ValueError(
                "engineering_max_phase_flip_fraction must be in [0, 1], "
                f"got {self.engineering_max_phase_flip_fraction}"
            )
        if self.engineering_min_mean_peak_margin_z < 0:
            raise ValueError(
                "engineering_min_mean_peak_margin_z must be >= 0, "
                f"got {self.engineering_min_mean_peak_margin_z}"
            )
        if self.phase_model not in {"constant", "axial_path", "relative_surrogate"}:
            raise ValueError(
                "phase_model must be 'constant', 'axial_path', or "
                f"'relative_surrogate', got {self.phase_model}"
            )
        if self.path_opd_model not in {
            "single_pass",
            "reference_plane_roundtrip_surrogate",
            "wall_referenced_gap_surrogate",
        }:
            raise ValueError(
                "path_opd_model must be 'single_pass', "
                "'reference_plane_roundtrip_surrogate', or "
                f"'wall_referenced_gap_surrogate', got {self.path_opd_model}"
            )
        if self.flow_profile_model not in {"plug", "parabolic_rect", "rect_series"}:
            raise ValueError(
                "flow_profile_model must be 'plug', 'parabolic_rect', or "
                f"'rect_series', got {self.flow_profile_model}"
            )
        if self.diffusion_hindrance_model not in {
            "none",
            "near_wall_surrogate",
            "anisotropic_tensor_surrogate",
        }:
            raise ValueError(
                "diffusion_hindrance_model must be 'none', "
                "'near_wall_surrogate', or 'anisotropic_tensor_surrogate', "
                f"got {self.diffusion_hindrance_model}"
            )
        if self.reference_model not in {
            "constant",
            "geometry_scaled",
            "calibrated_lookup",
            "channel_angular_surrogate",
            "paper_aligned_phase_filter",
            "tsuyama_bfp_integrated",
        }:
            raise ValueError(
                "reference_model must be 'constant', 'geometry_scaled', "
                "'calibrated_lookup', 'channel_angular_surrogate', or "
                "'paper_aligned_phase_filter', or 'tsuyama_bfp_integrated', "
                f"got {self.reference_model}"
            )
        if self.reference_route not in REFERENCE_ROUTE_OPTIONS:
            raise ValueError(
                "reference_route must be 'auto', 'calibrated_primary', "
                "'paper_aligned_comparison', 'engineering_fallback', or "
                f"'legacy_debug', got {self.reference_route}"
            )
        if self.reference_route != "auto":
            compatible_models = REFERENCE_ROUTE_MODEL_COMPATIBILITY[self.reference_route]
            if self.reference_model not in compatible_models:
                raise ValueError(
                    "reference_route is incompatible with reference_model: "
                    f"reference_route={self.reference_route}, "
                    f"reference_model={self.reference_model}"
                )
        if self.reference_solver_route not in REFERENCE_SOLVER_ROUTE_OPTIONS:
            raise ValueError(
                "reference_solver_route must be one of "
                f"{REFERENCE_SOLVER_ROUTE_OPTIONS}, got {self.reference_solver_route}"
            )
        if self.reference_na_edge_policy not in REFERENCE_NA_EDGE_POLICY_OPTIONS:
            raise ValueError(
                "reference_na_edge_policy must be one of "
                f"{REFERENCE_NA_EDGE_POLICY_OPTIONS}, got "
                f"{self.reference_na_edge_policy}"
            )
        if self.reference_na_rolloff_width_deg <= 0:
            raise ValueError(
                "reference_na_rolloff_width_deg must be positive, got "
                f"{self.reference_na_rolloff_width_deg}"
            )
        if self.tsuyama_phase_filter_grid_n < 128:
            raise ValueError(
                "tsuyama_phase_filter_grid_n must be >= 128, "
                f"got {self.tsuyama_phase_filter_grid_n}"
            )
        if self.tsuyama_phase_filter_grid_extent_factor <= 0:
            raise ValueError(
                "tsuyama_phase_filter_grid_extent_factor must be positive, "
                f"got {self.tsuyama_phase_filter_grid_extent_factor}"
            )
        if self.tsuyama_bfp_roi_mode not in {
            "symmetric_na_aperture",
            "slit_off_axis_lobe_surrogate",
        }:
            raise ValueError(
                "tsuyama_bfp_roi_mode must be 'symmetric_na_aperture' or "
                "'slit_off_axis_lobe_surrogate', got "
                f"{self.tsuyama_bfp_roi_mode}"
            )
        for name, value in {
            "tsuyama_bfp_transmitted_block_fraction": (
                self.tsuyama_bfp_transmitted_block_fraction
            ),
            "tsuyama_bfp_lobe_center_fraction": self.tsuyama_bfp_lobe_center_fraction,
            "tsuyama_bfp_lobe_sigma_fraction": self.tsuyama_bfp_lobe_sigma_fraction,
        }.items():
            if not np.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and > 0, got {value}")
        if self.tsuyama_bfp_transmitted_block_fraction >= 1.0:
            raise ValueError("tsuyama_bfp_transmitted_block_fraction must be < 1")
        if self.tsuyama_bfp_lobe_center_fraction >= 1.0:
            raise ValueError("tsuyama_bfp_lobe_center_fraction must be < 1")
        if self.reference_model == "calibrated_lookup":
            if not self.reference_calibration_path:
                raise ValueError(
                    "reference_calibration_path is required when "
                    "reference_model='calibrated_lookup'"
                )
            if not os.path.exists(self.reference_calibration_path):
                raise ValueError(
                    "reference_calibration_path does not exist: "
                    f"{self.reference_calibration_path}"
                )
        elif self.reference_calibration_path is not None and not os.path.exists(self.reference_calibration_path):
            raise ValueError(
                "reference_calibration_path does not exist: "
                f"{self.reference_calibration_path}"
            )
        if self.reference_spatial_mode not in {"uniform", "cross_section_surrogate"}:
            raise ValueError(
                "reference_spatial_mode must be 'uniform' or "
                f"'cross_section_surrogate', got {self.reference_spatial_mode}"
            )
        if self.reference_phase_grating_mode not in {
            "phase_grating_sine",
            "legacy_sinc_linearized",
        }:
            raise ValueError(
                "reference_phase_grating_mode must be 'phase_grating_sine' or "
                f"'legacy_sinc_linearized', got {self.reference_phase_grating_mode}"
            )
        if self.reference_width_saturation_mode not in {
            "waveguide_cutoff_surrogate",
            "none",
        }:
            raise ValueError(
                "reference_width_saturation_mode must be "
                "'waveguide_cutoff_surrogate' or 'none', "
                f"got {self.reference_width_saturation_mode}"
            )
        if (
            not np.isfinite(self.reference_width_saturation_cutoff_ratio)
            or self.reference_width_saturation_cutoff_ratio <= 0
        ):
            raise ValueError(
                "reference_width_saturation_cutoff_ratio must be finite and > 0, "
                f"got {self.reference_width_saturation_cutoff_ratio}"
            )
        if self.reference_spatial_amplitude_strength < 0:
            raise ValueError(
                "reference_spatial_amplitude_strength must be >= 0, "
                f"got {self.reference_spatial_amplitude_strength}"
            )
        if not np.isfinite(self.reference_spatial_phase_strength_rad):
            raise ValueError(
                "reference_spatial_phase_strength_rad must be finite, "
                f"got {self.reference_spatial_phase_strength_rad}"
            )
        if self.reference_spatial_min_amplitude_scale <= 0:
            raise ValueError(
                "reference_spatial_min_amplitude_scale must be > 0, "
                f"got {self.reference_spatial_min_amplitude_scale}"
            )
        if self.free_solution_window_scale < 1.0:
            raise ValueError(
                "free_solution_window_scale must be >= 1.0, "
                f"got {self.free_solution_window_scale}"
            )
        if self.collection_angle_model not in {"fixed", "channel_diffraction"}:
            raise ValueError(
                "collection_angle_model must be 'fixed' or 'channel_diffraction', "
                f"got {self.collection_angle_model}"
            )
        if self.collection_integration_mode not in {
            "single_angle",
            "gaussian_weighted",
            "pupil_slit_surrogate",
        }:
            raise ValueError(
                "collection_integration_mode must be 'single_angle', "
                "'gaussian_weighted', or "
                "'pupil_slit_surrogate', got "
                f"{self.collection_integration_mode}"
            )
        if self.collection_sigma_rad <= 0:
            raise ValueError(
                f"collection_sigma_rad must be positive, got {self.collection_sigma_rad}"
            )
        if self.collection_phi_sigma_rad <= 0:
            raise ValueError(
                "collection_phi_sigma_rad must be positive, "
                f"got {self.collection_phi_sigma_rad}"
            )
        if self.slit_phi_limit_rad <= 0 or self.slit_phi_limit_rad > math.pi / 2:
            raise ValueError(
                "slit_phi_limit_rad must be in (0, pi/2], "
                f"got {self.slit_phi_limit_rad}"
            )
        if (
            self.collection_operator_calibration_path is not None
            and not os.path.exists(self.collection_operator_calibration_path)
        ):
            raise ValueError(
                "collection_operator_calibration_path does not exist: "
                f"{self.collection_operator_calibration_path}"
            )
        if (
            self.absolute_throughput_route == "calibrated_operator_table"
            and not self.collection_operator_calibration_path
        ):
            raise ValueError(
                "collection_operator_calibration_path is required when "
                "absolute_throughput_route='calibrated_operator_table'"
            )
        if (
            self.collection_operator_id is not None
            and not str(self.collection_operator_id).strip()
        ):
            raise ValueError("collection_operator_id must be non-empty when set")
        if self.scattering_projection_mode not in {
            "intensity_proxy",
            "parallel",
            "perpendicular",
        }:
            raise ValueError(
                "scattering_projection_mode must be 'intensity_proxy', "
                f"'parallel', or 'perpendicular', got {self.scattering_projection_mode}"
            )
        for mode_name, mode_value in {
            "illumination_polarization_mode": self.illumination_polarization_mode,
            "reference_projection_mode": self.reference_projection_mode,
        }.items():
            if mode_value not in {
                "match_scattering",
                "parallel",
                "perpendicular",
                "unpolarized",
            }:
                raise ValueError(
                    f"{mode_name} must be 'match_scattering', 'parallel', "
                    f"'perpendicular', or 'unpolarized', got {mode_value}"
                )
        if not (0.0 <= self.cross_polarization_leakage <= 1.0):
            raise ValueError(
                "cross_polarization_leakage must be in [0, 1], "
                f"got {self.cross_polarization_leakage}"
            )
        if (
            self.polarization_jones_operator_mode
            not in POLARIZATION_JONES_OPERATOR_MODE_OPTIONS
        ):
            raise ValueError(
                "polarization_jones_operator_mode must be one of "
                f"{POLARIZATION_JONES_OPERATOR_MODE_OPTIONS}, got "
                f"{self.polarization_jones_operator_mode}"
            )
        if self.interference_overlap_mode not in {
            "collapsed_then_multiplied",
            "joint_overlap_integrated",
        }:
            raise ValueError(
                "interference_overlap_mode must be "
                "'collapsed_then_multiplied' or 'joint_overlap_integrated', "
                f"got {self.interference_overlap_mode}"
            )
        if self.detector_forward_model not in DETECTOR_FORWARD_MODEL_OPTIONS:
            raise ValueError(
                "detector_forward_model must be one of "
                f"{DETECTOR_FORWARD_MODEL_OPTIONS}, got {self.detector_forward_model}"
            )
        if not str(self.objective_candidate_id).strip():
            raise ValueError("objective_candidate_id must be non-empty")
        if self.field_coordinate_measure not in FIELD_COORDINATE_MEASURE_OPTIONS:
            raise ValueError(
                "field_coordinate_measure must be 'theta_phi_surrogate', "
                "'solid_angle', or 'direction_cosine_uv', "
                f"got {self.field_coordinate_measure}"
            )
        if not isinstance(self.bfp_to_angle_jacobian_applied, bool):
            raise ValueError(
                "bfp_to_angle_jacobian_applied must be bool, "
                f"got {self.bfp_to_angle_jacobian_applied}"
            )
        if not self.detector_mask_units:
            raise ValueError("detector_mask_units must be non-empty")
        if not self.coordinate_frame_mapping:
            raise ValueError("coordinate_frame_mapping must be non-empty")
        if self.complex_time_harmonic_convention not in COMPLEX_TIME_HARMONIC_CONVENTION_OPTIONS:
            raise ValueError(
                "complex_time_harmonic_convention must be one of "
                f"{COMPLEX_TIME_HARMONIC_CONVENTION_OPTIONS}, got "
                f"{self.complex_time_harmonic_convention}"
            )
        if self.fourier_transform_sign_convention not in FOURIER_TRANSFORM_SIGN_CONVENTION_OPTIONS:
            raise ValueError(
                "fourier_transform_sign_convention must be one of "
                f"{FOURIER_TRANSFORM_SIGN_CONVENTION_OPTIONS}, got "
                f"{self.fourier_transform_sign_convention}"
            )
        if self.mie_amplitude_phase_convention not in MIE_AMPLITUDE_PHASE_CONVENTION_OPTIONS:
            raise ValueError(
                "mie_amplitude_phase_convention must be one of "
                f"{MIE_AMPLITUDE_PHASE_CONVENTION_OPTIONS}, got "
                f"{self.mie_amplitude_phase_convention}"
            )
        if self.interference_conjugation_convention not in INTERFERENCE_CONJUGATION_CONVENTION_OPTIONS:
            raise ValueError(
                "interference_conjugation_convention must be one of "
                f"{INTERFERENCE_CONJUGATION_CONVENTION_OPTIONS}, got "
                f"{self.interference_conjugation_convention}"
            )
        if self.global_phase_offset_source not in GLOBAL_PHASE_OFFSET_SOURCE_OPTIONS:
            raise ValueError(
                "global_phase_offset_source must be one of "
                f"{GLOBAL_PHASE_OFFSET_SOURCE_OPTIONS}, got "
                f"{self.global_phase_offset_source}"
            )
        if self.polarization_basis_model not in POLARIZATION_BASIS_MODEL_OPTIONS:
            raise ValueError(
                "polarization_basis_model must be one of "
                f"{POLARIZATION_BASIS_MODEL_OPTIONS}, got "
                f"{self.polarization_basis_model}"
            )
        if self.jones_basis_status not in JONES_BASIS_STATUS_OPTIONS:
            raise ValueError(
                "jones_basis_status must be one of "
                f"{JONES_BASIS_STATUS_OPTIONS}, got {self.jones_basis_status}"
            )
        if self.vector_optics_mode not in VECTOR_OPTICS_MODE_OPTIONS:
            raise ValueError(
                "vector_optics_mode must be one of "
                f"{VECTOR_OPTICS_MODE_OPTIONS}, got {self.vector_optics_mode}"
            )
        if (
            self.measured_jones_matrix_path is not None
            and not str(self.measured_jones_matrix_path).strip()
        ):
            raise ValueError(
                "measured_jones_matrix_path must be non-empty when set"
            )
        if self.scattering_normalization_route not in SCATTERING_NORMALIZATION_ROUTE_OPTIONS:
            raise ValueError(
                "scattering_normalization_route must be one of "
                f"{SCATTERING_NORMALIZATION_ROUTE_OPTIONS}, got "
                f"{self.scattering_normalization_route}"
            )
        if self.K_sca_calibration_status not in K_SCA_CALIBRATION_STATUS_OPTIONS:
            raise ValueError(
                "K_sca_calibration_status must be one of "
                f"{K_SCA_CALIBRATION_STATUS_OPTIONS}, got "
                f"{self.K_sca_calibration_status}"
            )
        if (
            self.standard_particle_calibration_path is not None
            and not os.path.exists(self.standard_particle_calibration_path)
        ):
            raise ValueError(
                "standard_particle_calibration_path does not exist: "
                f"{self.standard_particle_calibration_path}"
            )
        if (
            self.standard_particle_calibration_id is not None
            and not str(self.standard_particle_calibration_id).strip()
        ):
            raise ValueError(
                "standard_particle_calibration_id must be non-empty when set"
            )
        if self.calibration_state_machine_version not in CALIBRATION_STATE_MACHINE_VERSION_OPTIONS:
            raise ValueError(
                "calibration_state_machine_version must be one of "
                f"{CALIBRATION_STATE_MACHINE_VERSION_OPTIONS}, got "
                f"{self.calibration_state_machine_version}"
            )
        if self.detector_noise_model_route not in DETECTOR_NOISE_MODEL_ROUTE_OPTIONS:
            raise ValueError(
                "detector_noise_model_route must be one of "
                f"{DETECTOR_NOISE_MODEL_ROUTE_OPTIONS}, got "
                f"{self.detector_noise_model_route}"
            )
        if self.photon_unit_noise_model not in PHOTON_UNIT_NOISE_MODEL_OPTIONS:
            raise ValueError(
                "photon_unit_noise_model must be one of "
                f"{PHOTON_UNIT_NOISE_MODEL_OPTIONS}, got "
                f"{self.photon_unit_noise_model}"
            )
        if self.absolute_throughput_route not in ABSOLUTE_THROUGHPUT_ROUTE_OPTIONS:
            raise ValueError(
                "absolute_throughput_route must be one of "
                f"{ABSOLUTE_THROUGHPUT_ROUTE_OPTIONS}, got "
                f"{self.absolute_throughput_route}"
            )
        if self.detector_dynamic_range_model not in DETECTOR_DYNAMIC_RANGE_MODEL_OPTIONS:
            raise ValueError(
                "detector_dynamic_range_model must be one of "
                f"{DETECTOR_DYNAMIC_RANGE_MODEL_OPTIONS}, got "
                f"{self.detector_dynamic_range_model}"
            )
        if self.adc_dynamic_range_model not in ADC_DYNAMIC_RANGE_MODEL_OPTIONS:
            raise ValueError(
                "adc_dynamic_range_model must be one of "
                f"{ADC_DYNAMIC_RANGE_MODEL_OPTIONS}, got "
                f"{self.adc_dynamic_range_model}"
            )
        if self.rin_noise_model not in RIN_NOISE_MODEL_OPTIONS:
            raise ValueError(
                "rin_noise_model must be one of "
                f"{RIN_NOISE_MODEL_OPTIONS}, got {self.rin_noise_model}"
            )
        if self.speckle_background_noise_model not in SPECKLE_BACKGROUND_NOISE_MODEL_OPTIONS:
            raise ValueError(
                "speckle_background_noise_model must be one of "
                f"{SPECKLE_BACKGROUND_NOISE_MODEL_OPTIONS}, got "
                f"{self.speckle_background_noise_model}"
            )
        if self.background_field_model not in BACKGROUND_FIELD_MODEL_OPTIONS:
            raise ValueError(
                "background_field_model must be one of "
                f"{BACKGROUND_FIELD_MODEL_OPTIONS}, got {self.background_field_model}"
            )
        if self.transmitted_leakage_model not in TRANSMITTED_LEAKAGE_MODEL_OPTIONS:
            raise ValueError(
                "transmitted_leakage_model must be one of "
                f"{TRANSMITTED_LEAKAGE_MODEL_OPTIONS}, got "
                f"{self.transmitted_leakage_model}"
            )
        if self.stray_light_model not in STRAY_LIGHT_MODEL_OPTIONS:
            raise ValueError(
                "stray_light_model must be one of "
                f"{STRAY_LIGHT_MODEL_OPTIONS}, got {self.stray_light_model}"
            )
        if self.particle_induced_channel_perturbation_model not in PARTICLE_INDUCED_CHANNEL_PERTURBATION_MODEL_OPTIONS:
            raise ValueError(
                "particle_induced_channel_perturbation_model must be one of "
                f"{PARTICLE_INDUCED_CHANNEL_PERTURBATION_MODEL_OPTIONS}, got "
                f"{self.particle_induced_channel_perturbation_model}"
            )
        if (
            self.particle_channel_perturbation_application_mode
            not in PARTICLE_CHANNEL_PERTURBATION_APPLICATION_MODE_OPTIONS
        ):
            raise ValueError(
                "particle_channel_perturbation_application_mode must be one of "
                f"{PARTICLE_CHANNEL_PERTURBATION_APPLICATION_MODE_OPTIONS}, got "
                f"{self.particle_channel_perturbation_application_mode}"
            )
        if self.readout_preset not in READOUT_PRESET_OPTIONS:
            raise ValueError(
                "readout_preset must be one of "
                f"{READOUT_PRESET_OPTIONS}, got {self.readout_preset}"
            )
        if self.nodi_readout_semantics not in NODI_READOUT_SEMANTICS_OPTIONS:
            raise ValueError(
                "nodi_readout_semantics must be one of "
                f"{NODI_READOUT_SEMANTICS_OPTIONS}, got "
                f"{self.nodi_readout_semantics}"
            )
        if self.electronics_demod_phase_policy not in ELECTRONICS_DEMOD_PHASE_POLICY_OPTIONS:
            raise ValueError(
                "electronics_demod_phase_policy must be one of "
                f"{ELECTRONICS_DEMOD_PHASE_POLICY_OPTIONS}, got "
                f"{self.electronics_demod_phase_policy}"
            )
        if self.readout_internal_demod_route not in READOUT_INTERNAL_DEMOD_ROUTE_OPTIONS:
            raise ValueError(
                "readout_internal_demod_route must be one of "
                f"{READOUT_INTERNAL_DEMOD_ROUTE_OPTIONS}, got "
                f"{self.readout_internal_demod_route}"
            )
        if self.readout_anti_alias_policy not in READOUT_ANTI_ALIAS_POLICY_OPTIONS:
            raise ValueError(
                "readout_anti_alias_policy must be one of "
                f"{READOUT_ANTI_ALIAS_POLICY_OPTIONS}, got "
                f"{self.readout_anti_alias_policy}"
            )
        if self.lockin_output_unit_convention not in LOCKIN_OUTPUT_UNIT_CONVENTION_OPTIONS:
            raise ValueError(
                "lockin_output_unit_convention must be one of "
                f"{LOCKIN_OUTPUT_UNIT_CONVENTION_OPTIONS}, got "
                f"{self.lockin_output_unit_convention}"
            )
        if not self.lockin_gain_chain:
            raise ValueError("lockin_gain_chain must be non-empty")
        if self.threshold_tail not in THRESHOLD_TAIL_OPTIONS:
            raise ValueError(
                "threshold_tail must be one of "
                f"{THRESHOLD_TAIL_OPTIONS}, got {self.threshold_tail}"
            )
        if not (0.0 <= self.event_qc_min_pass_fraction <= 1.0):
            raise ValueError(
                "event_qc_min_pass_fraction must be in [0, 1], "
                f"got {self.event_qc_min_pass_fraction}"
            )
        if not (0.0 <= self.event_qc_max_artifact_risk_score <= 1.0):
            raise ValueError(
                "event_qc_max_artifact_risk_score must be in [0, 1], "
                f"got {self.event_qc_max_artifact_risk_score}"
            )
        if self.threshold_calibration_source not in THRESHOLD_CALIBRATION_SOURCE_OPTIONS:
            raise ValueError(
                "threshold_calibration_source must be one of "
                f"{THRESHOLD_CALIBRATION_SOURCE_OPTIONS}, got "
                f"{self.threshold_calibration_source}"
            )
        if self.colored_noise_false_alarm_model not in COLORED_NOISE_FALSE_ALARM_MODEL_OPTIONS:
            raise ValueError(
                "colored_noise_false_alarm_model must be one of "
                f"{COLORED_NOISE_FALSE_ALARM_MODEL_OPTIONS}, got "
                f"{self.colored_noise_false_alarm_model}"
            )
        if (
            self.blank_false_positive_calibration_path is not None
            and not os.path.exists(self.blank_false_positive_calibration_path)
        ):
            raise ValueError(
                "blank_false_positive_calibration_path does not exist: "
                f"{self.blank_false_positive_calibration_path}"
            )
        if (
            self.blank_false_positive_calibration_id is not None
            and not str(self.blank_false_positive_calibration_id).strip()
        ):
            raise ValueError(
                "blank_false_positive_calibration_id must be non-empty when set"
            )
        if (
            self.raw_blank_trace_path is not None
            and not os.path.exists(self.raw_blank_trace_path)
        ):
            raise ValueError(
                "raw_blank_trace_path does not exist: "
                f"{self.raw_blank_trace_path}"
            )
        if (
            self.bfp_roi_mask_path is not None
            and not os.path.exists(self.bfp_roi_mask_path)
        ):
            raise ValueError(
                "bfp_roi_mask_path does not exist: "
                f"{self.bfp_roi_mask_path}"
            )
        if self.particle_uncertainty_propagation_mode not in PARTICLE_UNCERTAINTY_PROPAGATION_MODE_OPTIONS:
            raise ValueError(
                "particle_uncertainty_propagation_mode must be one of "
                f"{PARTICLE_UNCERTAINTY_PROPAGATION_MODE_OPTIONS}, got "
                f"{self.particle_uncertainty_propagation_mode}"
            )
        if self.particle_uncertainty_budget_model not in PARTICLE_UNCERTAINTY_BUDGET_MODEL_OPTIONS:
            raise ValueError(
                "particle_uncertainty_budget_model must be one of "
                f"{PARTICLE_UNCERTAINTY_BUDGET_MODEL_OPTIONS}, got "
                f"{self.particle_uncertainty_budget_model}"
            )
        if self.EV_ensemble_mode not in EV_ENSEMBLE_MODE_OPTIONS:
            raise ValueError(
                "EV_ensemble_mode must be one of "
                f"{EV_ENSEMBLE_MODE_OPTIONS}, got {self.EV_ensemble_mode}"
            )
        if self.EV_sample_preparation_profile not in EV_SAMPLE_PREPARATION_PROFILE_OPTIONS:
            raise ValueError(
                "EV_sample_preparation_profile must be one of "
                f"{EV_SAMPLE_PREPARATION_PROFILE_OPTIONS}, got "
                f"{self.EV_sample_preparation_profile}"
            )
        if self.count_prediction_model not in COUNT_PREDICTION_MODEL_OPTIONS:
            raise ValueError(
                "count_prediction_model must be one of "
                f"{COUNT_PREDICTION_MODEL_OPTIONS}, got {self.count_prediction_model}"
            )
        if self.number_concentration_m3 is not None and self.number_concentration_m3 < 0:
            raise ValueError(
                "number_concentration_m3 must be non-negative when provided, "
                f"got {self.number_concentration_m3}"
            )
        if (
            self.count_observation_window_s is not None
            and self.count_observation_window_s <= 0
        ):
            raise ValueError(
                "count_observation_window_s must be positive when provided, "
                f"got {self.count_observation_window_s}"
            )
        if self.count_dead_time_s < 0:
            raise ValueError(
                f"count_dead_time_s must be non-negative, got {self.count_dead_time_s}"
            )
        if self.wall_interaction_model not in WALL_INTERACTION_MODEL_OPTIONS:
            raise ValueError(
                "wall_interaction_model must be one of "
                f"{WALL_INTERACTION_MODEL_OPTIONS}, got {self.wall_interaction_model}"
            )
        if self.electrokinetic_model not in ELECTROKINETIC_MODEL_OPTIONS:
            raise ValueError(
                "electrokinetic_model must be one of "
                f"{ELECTROKINETIC_MODEL_OPTIONS}, got {self.electrokinetic_model}"
            )
        if self.electroosmotic_flow_fraction is not None and not (
            0.0 <= self.electroosmotic_flow_fraction <= 1.0
        ):
            raise ValueError(
                "electroosmotic_flow_fraction must be in [0, 1] when set, got "
                f"{self.electroosmotic_flow_fraction}"
            )
        if self.ionic_strength_M is not None and self.ionic_strength_M < 0:
            raise ValueError(
                f"ionic_strength_M must be non-negative when provided, got {self.ionic_strength_M}"
            )
        if self.adsorption_probability_per_length_m < 0:
            raise ValueError(
                "adsorption_probability_per_length_m must be non-negative, got "
                f"{self.adsorption_probability_per_length_m}"
            )
        if self.interface_correction_mode not in INTERFACE_CORRECTION_MODE_OPTIONS:
            raise ValueError(
                "interface_correction_mode must be one of "
                f"{INTERFACE_CORRECTION_MODE_OPTIONS}, got "
                f"{self.interface_correction_mode}"
            )
        if self.interface_correction_priority not in INTERFACE_CORRECTION_PRIORITY_OPTIONS:
            raise ValueError(
                "interface_correction_priority must be one of "
                f"{INTERFACE_CORRECTION_PRIORITY_OPTIONS}, got "
                f"{self.interface_correction_priority}"
            )
        if self.interface_correction_applied_to not in INTERFACE_CORRECTION_APPLIED_TO_OPTIONS:
            raise ValueError(
                "interface_correction_applied_to must be one of "
                f"{INTERFACE_CORRECTION_APPLIED_TO_OPTIONS}, got "
                f"{self.interface_correction_applied_to}"
            )
        if self.thermal_pod_model not in THERMAL_POD_MODEL_OPTIONS:
            raise ValueError(
                "thermal_pod_model must be one of "
                f"{THERMAL_POD_MODEL_OPTIONS}, got {self.thermal_pod_model}"
            )
        if (
            self.pod_roi_sensitivity_derivative_status
            not in POD_ROI_SENSITIVITY_DERIVATIVE_STATUS_OPTIONS
        ):
            raise ValueError(
                "pod_roi_sensitivity_derivative_status must be one of "
                f"{POD_ROI_SENSITIVITY_DERIVATIVE_STATUS_OPTIONS}, got "
                f"{self.pod_roi_sensitivity_derivative_status}"
            )
        if self.pod_signal_sign_source not in POD_SIGNAL_SIGN_SOURCE_OPTIONS:
            raise ValueError(
                "pod_signal_sign_source must be one of "
                f"{POD_SIGNAL_SIGN_SOURCE_OPTIONS}, got "
                f"{self.pod_signal_sign_source}"
            )
        if (
            self.pod_thermal_spatial_distribution_status
            not in POD_THERMAL_SPATIAL_DISTRIBUTION_STATUS_OPTIONS
        ):
            raise ValueError(
                "pod_thermal_spatial_distribution_status must be one of "
                f"{POD_THERMAL_SPATIAL_DISTRIBUTION_STATUS_OPTIONS}, got "
                f"{self.pod_thermal_spatial_distribution_status}"
            )
        if self.pod_roi_derivative_validity not in POD_ROI_DERIVATIVE_VALIDITY_OPTIONS:
            raise ValueError(
                "pod_roi_derivative_validity must be one of "
                f"{POD_ROI_DERIVATIVE_VALIDITY_OPTIONS}, got "
                f"{self.pod_roi_derivative_validity}"
            )
        if self.probe_wavelength_m is not None and self.probe_wavelength_m <= 0:
            raise ValueError(
                "probe_wavelength_m must be positive when provided, "
                f"got {self.probe_wavelength_m}"
            )
        if (
            self.excitation_wavelength_m is not None
            and self.excitation_wavelength_m <= 0
        ):
            raise ValueError(
                "excitation_wavelength_m must be positive when provided, "
                f"got {self.excitation_wavelength_m}"
            )
        if self.probe_power_W is not None and self.probe_power_W < 0:
            raise ValueError(
                "probe_power_W must be non-negative when provided, "
                f"got {self.probe_power_W}"
            )
        if self.excitation_power_W is not None and self.excitation_power_W < 0:
            raise ValueError(
                "excitation_power_W must be non-negative when provided, "
                f"got {self.excitation_power_W}"
            )
        if self.wavelength_lane_id is not None and not str(self.wavelength_lane_id).strip():
            raise ValueError("wavelength_lane_id must be non-empty when set")
        medium_material_keys = {
            self.medium_optical_material_key,
            self.medium_transport_material_key,
            self.medium_thermal_material_key,
        }
        configured_medium_keys = {
            key for key in medium_material_keys if key is not None
        }
        if configured_medium_keys:
            from .materials import MATERIAL_DB
            unknown_medium_keys = sorted(
                key for key in configured_medium_keys if key not in MATERIAL_DB
            )
            if unknown_medium_keys:
                from .materials import list_materials
                raise ValueError(
                    "Unknown medium material key(s) in SimulationConfig: "
                    f"{unknown_medium_keys}. Available: {list_materials()}"
                )
        wavelength_numeric_maps = {
            "probe_power_by_wavelength_W": self.probe_power_by_wavelength_W,
            "detector_responsivity_by_wavelength": self.detector_responsivity_by_wavelength,
            "filter_transmission_by_wavelength": self.filter_transmission_by_wavelength,
        }
        for map_name, mapping in wavelength_numeric_maps.items():
            if mapping is None:
                continue
            if not isinstance(mapping, dict):
                raise ValueError(f"{map_name} must be a dict when provided")
            for wavelength_key, wavelength_value in mapping.items():
                if not str(wavelength_key).strip():
                    raise ValueError(f"{map_name} contains an empty wavelength key")
                if float(wavelength_value) < 0.0:
                    raise ValueError(
                        f"{map_name}[{wavelength_key!r}] must be non-negative, got"
                        f" {wavelength_value}"
                    )
        if self.reference_calibration_by_wavelength is not None:
            if not isinstance(self.reference_calibration_by_wavelength, dict):
                raise ValueError(
                    "reference_calibration_by_wavelength must be a dict when provided"
                )
            for (
                reference_key,
                reference_value,
            ) in self.reference_calibration_by_wavelength.items():
                if not str(reference_key).strip():
                    raise ValueError(
                        "reference_calibration_by_wavelength contains an empty "
                        "wavelength key"
                    )
                if reference_value is None or str(reference_value) == "":
                    raise ValueError(
                        "reference_calibration_by_wavelength entries must be non-empty"
                    )
        if self.pulse_detection_mode not in {"positive", "absolute"}:
            raise ValueError(
                "pulse_detection_mode must be 'positive' or 'absolute', "
                f"got {self.pulse_detection_mode}"
            )
        if self.pulse_width_measure_mode not in {
            "peak_width",
            "duration_above_threshold",
        }:
            raise ValueError(
                "pulse_width_measure_mode must be 'peak_width' or "
                "'duration_above_threshold', got "
                f"{self.pulse_width_measure_mode}"
            )
        if self.pulse_duration_estimation_policy not in PULSE_DURATION_ESTIMATION_POLICY_OPTIONS:
            raise ValueError(
                "pulse_duration_estimation_policy must be one of "
                f"{PULSE_DURATION_ESTIMATION_POLICY_OPTIONS}, got "
                f"{self.pulse_duration_estimation_policy}"
            )
        if self.detection_decision_mode not in {"single_channel", "paired_channel"}:
            raise ValueError(
                "detection_decision_mode must be 'single_channel' or "
                f"'paired_channel', got {self.detection_decision_mode}"
            )
        if self.engineering_decision_basis not in {
            "final_decision",
            "single_channel",
            "paired_channel",
        }:
            raise ValueError(
                "engineering_decision_basis must be 'final_decision', "
                "'single_channel', or 'paired_channel', got "
                f"{self.engineering_decision_basis}"
            )
        if self.readout_model not in {"raw", "lockin_surrogate"}:
            raise ValueError(
                "readout_model must be 'raw' or 'lockin_surrogate', "
                f"got {self.readout_model}"
            )
        if self.readout_observable_mode not in {"in_phase", "magnitude"}:
            raise ValueError(
                "readout_observable_mode must be 'in_phase' or 'magnitude', "
                f"got {self.readout_observable_mode}"
            )
        if self.readout_model == "lockin_surrogate" and self.lockin_time_constant_s <= 0:
            raise ValueError(
                "lockin_time_constant_s must be positive when "
                "readout_model='lockin_surrogate'"
            )
        for name, value in {
            "pod_lockin_frequency_Hz": self.pod_lockin_frequency_Hz,
            "nodi_lockin_frequency_Hz": self.nodi_lockin_frequency_Hz,
        }.items():
            if self.readout_model == "lockin_surrogate" and value <= 0:
                raise ValueError(f"{name} must be positive when readout_model='lockin_surrogate'")
        for name, value in {
            "pod_reference_phase_rad": self.pod_reference_phase_rad,
            "nodi_reference_phase_rad": self.nodi_reference_phase_rad,
        }.items():
            if not np.isfinite(value):
                raise ValueError(f"{name} must be finite, got {value}")
        if self.pod_frequency_response_model not in {"flat", "inverse_power_surrogate"}:
            raise ValueError(
                "pod_frequency_response_model must be 'flat' or "
                f"'inverse_power_surrogate', got {self.pod_frequency_response_model}"
            )
        for name, value in {
            "pod_frequency_response_reference_Hz": self.pod_frequency_response_reference_Hz,
            "pod_frequency_response_exponent": self.pod_frequency_response_exponent,
            "pod_frequency_response_min_gain": self.pod_frequency_response_min_gain,
            "pod_frequency_response_max_gain": self.pod_frequency_response_max_gain,
        }.items():
            if value < 0:
                raise ValueError(f"{name} must be >= 0, got {value}")
        if self.pod_frequency_response_reference_Hz == 0:
            raise ValueError("pod_frequency_response_reference_Hz must be > 0")
        if self.pod_frequency_response_min_gain <= 0:
            raise ValueError("pod_frequency_response_min_gain must be > 0")
        if self.pod_frequency_response_max_gain < self.pod_frequency_response_min_gain:
            raise ValueError(
                "pod_frequency_response_max_gain must be >= "
                "pod_frequency_response_min_gain"
            )
        if self.nodi_transit_response_model not in {"flat", "time_constant_surrogate"}:
            raise ValueError(
                "nodi_transit_response_model must be 'flat' or "
                f"'time_constant_surrogate', got {self.nodi_transit_response_model}"
            )
        for name, value in {
            "nodi_transit_response_min_gain": self.nodi_transit_response_min_gain,
            "nodi_transit_response_max_gain": self.nodi_transit_response_max_gain,
        }.items():
            if value < 0:
                raise ValueError(f"{name} must be >= 0, got {value}")
        if self.nodi_transit_response_max_gain > 1.0:
            raise ValueError("nodi_transit_response_max_gain must be <= 1")
        if self.nodi_transit_response_max_gain < self.nodi_transit_response_min_gain:
            raise ValueError(
                "nodi_transit_response_max_gain must be >= "
                "nodi_transit_response_min_gain"
            )
        if self.initial_position_distribution_mode not in INITIAL_POSITION_DISTRIBUTION_MODE_OPTIONS:
            raise ValueError(
                "initial_position_distribution_mode must be one of "
                f"{INITIAL_POSITION_DISTRIBUTION_MODE_OPTIONS}, got "
                f"{self.initial_position_distribution_mode}"
            )
        if self.initial_position_distribution_mode in {
            "electrostatic_equilibrium",
            "measured_cross_section_distribution",
        }:
            raise ValueError(
                "initial_position_distribution_mode is schema-reserved but not "
                f"runtime-active yet: {self.initial_position_distribution_mode}"
            )
        if self.initial_position_center_bias_strength < 0:
            raise ValueError(
                "initial_position_center_bias_strength must be >= 0, got "
                f"{self.initial_position_center_bias_strength}"
            )
        if not (0.0 <= self.initial_position_center_bias_min_confinement_ratio < 1.0):
            raise ValueError(
                "initial_position_center_bias_min_confinement_ratio must be in [0, 1), got "
                f"{self.initial_position_center_bias_min_confinement_ratio}"
            )
        if not (0.0 <= self.initial_position_flux_weighted_mixture_fraction <= 1.0):
            raise ValueError(
                "initial_position_flux_weighted_mixture_fraction must be in [0, 1], got "
                f"{self.initial_position_flux_weighted_mixture_fraction}"
            )
        if (
            self.pulse_extraction_sampling_interval_s is not None
            and self.pulse_extraction_sampling_interval_s <= 0.0
        ):
            raise ValueError(
                "pulse_extraction_sampling_interval_s must be positive when set, got "
                f"{self.pulse_extraction_sampling_interval_s}"
            )
        for name, value in {
            "noise_std": self.noise_std,
            "shot_noise_scale": self.shot_noise_scale,
            "post_readout_noise_std": self.post_readout_noise_std,
            "post_readout_colored_noise_std": self.post_readout_colored_noise_std,
            "drift_slope": self.drift_slope,
            "post_readout_drift_slope": self.post_readout_drift_slope,
        }.items():
            if value < 0:
                raise ValueError(f"{name} must be >= 0, got {value}")
        if self.post_readout_colored_noise_tau_s <= 0:
            raise ValueError(
                "post_readout_colored_noise_tau_s must be > 0, got "
                f"{self.post_readout_colored_noise_tau_s}"
            )
        if self.noise_model not in {"gaussian", "gaussian_plus_drift"}:
            raise ValueError(
                "noise_model must be 'gaussian' or 'gaussian_plus_drift', "
                f"got {self.noise_model}"
            )
        for name, value in {
            "pod_to_nodi_crosstalk": self.pod_to_nodi_crosstalk,
            "nodi_to_pod_crosstalk": self.nodi_to_pod_crosstalk,
        }.items():
            if not np.isfinite(value):
                raise ValueError(f"{name} must be finite, got {value}")
        if self.diffraction_order <= 0:
            raise ValueError(
                f"diffraction_order must be positive, got {self.diffraction_order}"
            )
        if self.illumination_mode not in {"overfill", "tight_focus"}:
            raise ValueError(
                "illumination_mode must be 'overfill' or 'tight_focus', "
                f"got {self.illumination_mode}"
            )
        if self.coupling_model not in {"constant", "gaussian_xy"}:
            raise ValueError(
                "coupling_model must be 'constant' or 'gaussian_xy', "
                f"got {self.coupling_model}"
            )
        if self.n_events <= 0:
            raise ValueError(f"n_events must be positive, got {self.n_events}")
        if self.random_sequence_policy not in RANDOM_SEQUENCE_POLICY_OPTIONS:
            raise ValueError(
                "random_sequence_policy must be one of "
                f"{RANDOM_SEQUENCE_POLICY_OPTIONS}, got {self.random_sequence_policy}"
            )
        if self.event_sampling_policy not in EVENT_SAMPLING_POLICY_OPTIONS:
            raise ValueError(
                "event_sampling_policy must be one of "
                f"{EVENT_SAMPLING_POLICY_OPTIONS}, got {self.event_sampling_policy}"
            )
        if self.adaptive_event_budget_mode not in ADAPTIVE_EVENT_BUDGET_MODE_OPTIONS:
            raise ValueError(
                "adaptive_event_budget_mode must be one of "
                f"{ADAPTIVE_EVENT_BUDGET_MODE_OPTIONS}, got "
                f"{self.adaptive_event_budget_mode}"
            )
        if self.adaptive_min_events <= 0:
            raise ValueError(
                "adaptive_min_events must be positive, got "
                f"{self.adaptive_min_events}"
            )
        if self.adaptive_check_interval <= 0:
            raise ValueError(
                "adaptive_check_interval must be positive, got "
                f"{self.adaptive_check_interval}"
            )
        if not (0.0 < self.adaptive_wilson_half_width_target < 1.0):
            raise ValueError(
                "adaptive_wilson_half_width_target must be in (0, 1), got "
                f"{self.adaptive_wilson_half_width_target}"
            )
        if (
            self.adaptive_event_budget_mode != "fixed"
            and self.adaptive_min_events > self.n_events
        ):
            raise ValueError(
                "adaptive_min_events must be <= n_events when adaptive event "
                "budgeting is enabled"
            )
        if self.vectorized_event_engine not in VECTORIZED_EVENT_ENGINE_OPTIONS:
            raise ValueError(
                "vectorized_event_engine must be one of "
                f"{VECTORIZED_EVENT_ENGINE_OPTIONS}, got "
                f"{self.vectorized_event_engine}"
            )
        if self.event_block_size <= 0:
            raise ValueError(
                f"event_block_size must be positive, got {self.event_block_size}"
            )
        if self.event_block_rng_order not in EVENT_BLOCK_RNG_ORDER_OPTIONS:
            raise ValueError(
                "event_block_rng_order must be one of "
                f"{EVENT_BLOCK_RNG_ORDER_OPTIONS}, got {self.event_block_rng_order}"
            )


def get_readout_preset_overrides(readout_preset: str) -> dict[str, object]:
    """Return a copy of the runtime fields governed by a readout preset."""
    if readout_preset not in READOUT_PRESET_CONFIG_OVERRIDES:
        raise ValueError(
            f"Unknown readout_preset: {readout_preset}. "
            f"Available: {READOUT_PRESET_OPTIONS}"
        )
    return dict(READOUT_PRESET_CONFIG_OVERRIDES[readout_preset])


def apply_readout_preset(
    base_cfg: SimulationConfig,
    readout_preset: str,
) -> SimulationConfig:
    """
    Apply a named readout / threshold / decision contract to a config.

    The preset intentionally freezes only the current shared readout fields.
    Lane-specific POD/NODI thresholds remain a future schema extension and are
    exposed through diagnostics as shared-threshold profiles.
    """
    overrides = get_readout_preset_overrides(readout_preset)
    # Cast to Any so dataclasses.replace can apply per-field overrides explicitly
    # typed in READOUT_PRESET_CONFIG_OVERRIDES.
    typed_overrides: dict[str, Any] = overrides
    return replace(base_cfg, readout_preset=readout_preset, **typed_overrides)


# ============================================================
# Default instances (close to paper values)
# ============================================================

BASELINE_PARTICLE = make_gold_baseline_particle()

PBS_1X = Medium(
    name="pbs_1x",
    refractive_index=1.334,
    viscosity_Pa_s=1e-3,
    temperature_K=298.15,
    material_key="pbs_1x",
    use_material_model=True,
    optical_material_key="pbs_1x",
    transport_material_key="pbs_1x",
    thermal_material_key="pbs_1x",
    dn_dT=-1.0e-4,
    density_kg_m3=1005.0,
    thermal_conductivity_W_mK=0.60,
    thermal_diffusivity_m2_s=1.43e-7,
    osmolarity_or_solute_fraction=0.30,
    source="materials_db:pbs_1x",
    claim_level="nominal_material_properties_no_uncertainty",
)

WATER = Medium(
    name="water",
    refractive_index=1.33,
    viscosity_Pa_s=1e-3,
    temperature_K=298.15,
    material_key="water",
    use_material_model=True,
    optical_material_key="water",
    transport_material_key="water",
    thermal_material_key="water",
    dn_dT=-1.0e-4,
    density_kg_m3=997.0,
    thermal_conductivity_W_mK=0.60,
    thermal_diffusivity_m2_s=1.43e-7,
    osmolarity_or_solute_fraction=0.0,
    source="materials_db:water",
    claim_level="nominal_material_properties_no_uncertainty",
)

BASELINE_CHANNEL = Channel(
    width_m=800e-9,
    depth_m=550e-9,
)

BASELINE_OPTICAL = OpticalSystem(
    wavelength_m=660e-9,
    peak_irradiance_W_m2=1.0,
    beam_waist_x_m=300e-9,
    beam_waist_y_m=700e-9,
    beam_waist_z_m=300e-9,
)

DEFAULT_SIM_CFG = SimulationConfig(
    total_time_s=0.2,
    sampling_rate_Hz=20000.0,
    mean_flow_velocity_m_s=2e-4,
    noise_std=0.01,
    collection_angle_model="channel_diffraction",
    collection_integration_mode="pupil_slit_surrogate",
    path_opd_model=DEFAULT_PATH_OPD_MODEL,
    scattering_projection_mode="parallel",
    phase_model="relative_surrogate",
    reference_model="channel_angular_surrogate",
    reference_spatial_mode="cross_section_surrogate",
    pulse_detection_mode="absolute",
    readout_model="lockin_surrogate",
    normalization_mode="per_wavelength",
    threshold_sigma=5.0,
    min_peak_width_s=2.5e-3,
    min_peak_interval_s=0.1,
    n_events=100,
    random_seed=42,
    rho=0.5,
)


def make_ev_nodi_design_sweep_config(
    base_cfg: SimulationConfig | None = None,
) -> SimulationConfig:
    """
    Build the first P0 EV/NODI design-sweep configuration.

    This preserves the legacy/default configs and gives downstream smoke paths a
    single explicit entry point for the roadmap-43 EV design semantics.
    """
    cfg = DEFAULT_SIM_CFG if base_cfg is None else base_cfg
    cfg = replace(
        cfg,
        include_diffusion=True,
        flow_profile_model="rect_series",
        diffusion_hindrance_model="near_wall_surrogate",
        initial_position_distribution_mode="flux_weighted",
        reference_model="channel_angular_surrogate",
        reference_route="engineering_fallback",
        particle_induced_channel_perturbation_model="excluded_volume_phase_surrogate",
        particle_channel_perturbation_application_mode="diagnostic_only",
        EV_ensemble_mode="explicit_preset_cases",
    )
    return apply_readout_preset(cfg, "EV_NODI_only_design")
