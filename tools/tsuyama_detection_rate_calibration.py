#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_PARENT = PROJECT_ROOT.parent
for candidate in (str(PROJECT_ROOT), str(PROJECT_PARENT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from tools import tsuyama_gold_aligned_detection_lane as lane

OUTPUT_DIR = PROJECT_ROOT / "results" / "tsuyama_detection_rate_calibration"
CALIBRATION_SCENARIO_ID = "nodi_2022_10sigma_single"
CALIBRATION_CASES: tuple[tuple[int, int, int], ...] = (
    (488, 800, 550),
    (532, 800, 550),
    (660, 800, 550),
)
ESTIMATED_PARAMETER_FIELDS: tuple[str, ...] = (
    "rho",
    "noise_std",
    "shot_noise_scale",
    "post_readout_noise_std",
    "mean_flow_velocity_m_s",
    "flow_profile_model",
    "lockin_time_constant_s",
    "reference_model",
    "ref_phi0_rad",
    "reference_spatial_amplitude_strength",
    "reference_spatial_phase_strength_rad",
    "collection_sigma_rad",
    "collection_phi_sigma_rad",
    "slit_phi_limit_rad",
    "tsuyama_bfp_roi_mode",
    "tsuyama_bfp_lobe_center_fraction",
    "tsuyama_bfp_lobe_sigma_fraction",
    "initial_position_distribution_mode",
    "initial_position_center_bias_strength",
    "initial_position_center_bias_min_confinement_ratio",
    "initial_position_flux_weighted_mixture_fraction",
    "nodi_transit_response_model",
    "colored_noise_false_alarm_model",
    "threshold_calibration_source",
    "pulse_duration_estimation_policy",
    "pulse_extraction_sampling_interval_s",
    "post_readout_colored_noise_std",
    "post_readout_colored_noise_tau_s",
    "optical_illumination_beam_waist_y_m",
)
OPTICAL_ESTIMATED_PARAMETER_FIELDS: tuple[str, ...] = (
    "optical_illumination_beam_waist_y_m",
)
PROTECTED_PAPER_CRITERIA: tuple[str, ...] = (
    "threshold_sigma",
    "threshold_tail",
    "min_peak_width_s",
    "min_peak_interval_s",
    "pulse_width_measure_mode",
)
TARGET_BANDS: dict[int, dict[str, Any]] = {
    20: {
        "low": 0.08,
        "high": 0.25,
        "target": 0.15,
        "basis": "20 nm Au pulses are observed, but the paper notes not all particles may be detected.",
    },
    30: {
        "low": 0.30,
        "high": 0.55,
        "target": 0.42,
        "basis": "30 nm Au is clearly stronger than 20 nm while still close enough for overlap discussion.",
    },
    40: {
        "low": 0.45,
        "high": 0.75,
        "target": 0.60,
        "basis": "40 nm Au is robust enough to support pulse-height statistics and classification lanes.",
    },
    60: {
        "low": 0.55,
        "high": 0.85,
        "target": 0.70,
        "basis": "60 nm Au is a robust positive class in the dual-wavelength classification lane.",
    },
}
TARGET_SCHEMA_ID = "tsuyama_2022_nodi_conclusion_band_v1"


@dataclass(frozen=True)
class CalibrationCandidate:
    candidate_id: str
    overrides: dict[str, Any]
    rationale: str


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def _format_float_for_id(value: float) -> str:
    text = f"{value:.6g}".replace("-", "m").replace(".", "p")
    return text.replace("+", "")


def _candidate(
    candidate_id: str,
    overrides: dict[str, Any],
    rationale: str,
) -> CalibrationCandidate:
    unknown = sorted(set(overrides) - set(ESTIMATED_PARAMETER_FIELDS))
    if unknown:
        raise ValueError(f"candidate {candidate_id} has non-estimated fields: {unknown}")
    return CalibrationCandidate(candidate_id, dict(overrides), rationale)


def candidate_catalog() -> list[CalibrationCandidate]:
    candidates = [
        _candidate("baseline_current_estimates", {}, "Current paper-aligned estimate set."),
        _candidate("rho_0p40", {"rho": 0.40}, "Lower reference/scatter ratio sensitivity."),
        _candidate("rho_0p65", {"rho": 0.65}, "Moderately stronger reference/scatter ratio."),
        _candidate("rho_0p80", {"rho": 0.80}, "Upper reference/scatter ratio sensitivity."),
        _candidate("noise_0p006", {"noise_std": 0.006}, "Lower raw detector-noise estimate."),
        _candidate("noise_0p008", {"noise_std": 0.008}, "Mildly lower raw detector-noise estimate."),
        _candidate("noise_0p012", {"noise_std": 0.012}, "Mildly higher raw detector-noise estimate."),
        _candidate(
            "shot_0p0005",
            {"shot_noise_scale": 0.0005},
            "Lower baseline-dependent shot-noise surrogate.",
        ),
        _candidate(
            "post_0p001",
            {"post_readout_noise_std": 0.001},
            "Lower post-readout electronics noise surrogate.",
        ),
        _candidate(
            "post_0p003",
            {"post_readout_noise_std": 0.003},
            "Higher post-readout electronics noise surrogate.",
        ),
        _candidate(
            "velocity_0p15mmps",
            {"mean_flow_velocity_m_s": 1.5e-4},
            "Slower flow within the pressure/flow-rate uncertainty envelope.",
        ),
        _candidate(
            "velocity_0p25mmps",
            {"mean_flow_velocity_m_s": 2.5e-4},
            "Faster flow within the pressure/flow-rate uncertainty envelope.",
        ),
        _candidate(
            "tau_2ms",
            {"lockin_time_constant_s": 2.0e-3},
            "Upper end of Tsuyama's stated 1-2 ms lock-in time constant range.",
        ),
        _candidate(
            "tau_2ms_control",
            {"lockin_time_constant_s": 2.0e-3},
            "Phase 2.5 raw-operator control: same 2 ms lock-in candidate, without local transfer/size correction.",
        ),
        _candidate(
            "tau_2ms_paper_aligned_phase_filter",
            {
                "lockin_time_constant_s": 2.0e-3,
                "reference_model": "paper_aligned_phase_filter",
            },
            "Phase 2.5 raw-operator candidate using the paper-aligned Tsuyama phase-filter reference path.",
        ),
        _candidate(
            "tau_2ms_refphase_flat",
            {
                "lockin_time_constant_s": 2.0e-3,
                "reference_spatial_phase_strength_rad": 0.0,
            },
            "Phase 2.5 raw-operator candidate with the spatial phase surrogate flattened.",
        ),
        _candidate(
            "tau_2ms_refphase_wide",
            {
                "lockin_time_constant_s": 2.0e-3,
                "reference_spatial_phase_strength_rad": 1.2,
            },
            "Phase 2.5 raw-operator candidate with wider spatial phase averaging.",
        ),
        _candidate(
            "tau_2ms_global_refphi_plus",
            {
                "lockin_time_constant_s": 2.0e-3,
                "ref_phi0_rad": 0.4,
            },
            "Phase 2.5 raw-operator candidate with a shared positive global reference phase offset.",
        ),
        _candidate(
            "tau_2ms_global_refphi_plus_0p2",
            {
                "lockin_time_constant_s": 2.0e-3,
                "ref_phi0_rad": 0.2,
            },
            "Phase 2.5 D2.1 raw-operator candidate with a smaller shared positive global reference phase offset.",
        ),
        _candidate(
            "tau_2ms_global_refphi_plus_0p6",
            {
                "lockin_time_constant_s": 2.0e-3,
                "ref_phi0_rad": 0.6,
            },
            "Phase 2.5 D2.1 raw-operator candidate with a larger shared positive global reference phase offset.",
        ),
        _candidate(
            "tau_2ms_global_refphi_minus",
            {
                "lockin_time_constant_s": 2.0e-3,
                "ref_phi0_rad": -0.4,
            },
            "Phase 2.5 raw-operator candidate with a shared negative global reference phase offset.",
        ),
        _candidate(
            "tau_2ms_collection_narrow",
            {
                "lockin_time_constant_s": 2.0e-3,
                "collection_sigma_rad": 0.08,
                "collection_phi_sigma_rad": 0.16,
                "slit_phi_limit_rad": 0.25,
            },
            "Phase 2.5 raw-operator candidate with a narrower BFP/slit collection surrogate.",
        ),
        _candidate(
            "tau_2ms_global_refphi_plus_collection_narrow",
            {
                "lockin_time_constant_s": 2.0e-3,
                "ref_phi0_rad": 0.4,
                "collection_sigma_rad": 0.08,
                "collection_phi_sigma_rad": 0.16,
                "slit_phi_limit_rad": 0.25,
            },
            "Phase 2.5 D2.1 raw-operator candidate combining the current best positive reference phase with the narrower BFP/slit collection surrogate.",
        ),
        _candidate(
            "tau_2ms_collection_wide",
            {
                "lockin_time_constant_s": 2.0e-3,
                "collection_sigma_rad": 0.22,
                "collection_phi_sigma_rad": 0.35,
                "slit_phi_limit_rad": 0.50,
            },
            "Phase 2.5 raw-operator candidate with a wider BFP/slit collection surrogate.",
        ),
        _candidate(
            "tau_2ms_bfp_lobe_045",
            {
                "lockin_time_constant_s": 2.0e-3,
                "reference_model": "tsuyama_bfp_integrated",
                "tsuyama_bfp_roi_mode": "slit_off_axis_lobe_surrogate",
                "tsuyama_bfp_lobe_center_fraction": 0.45,
                "tsuyama_bfp_lobe_sigma_fraction": 0.18,
            },
            "Phase 2.5 raw-operator candidate using an off-axis Tsuyama BFP lobe centered at 0.45 NA fraction.",
        ),
        _candidate(
            "tau_2ms_bfp_lobe_065",
            {
                "lockin_time_constant_s": 2.0e-3,
                "reference_model": "tsuyama_bfp_integrated",
                "tsuyama_bfp_roi_mode": "slit_off_axis_lobe_surrogate",
                "tsuyama_bfp_lobe_center_fraction": 0.65,
                "tsuyama_bfp_lobe_sigma_fraction": 0.18,
            },
            "Phase 2.5 raw-operator candidate using an off-axis Tsuyama BFP lobe centered at 0.65 NA fraction.",
        ),
        _candidate(
            "refspace_0p25",
            {"reference_spatial_amplitude_strength": 0.25},
            "Weaker cross-section reference-field spatial modulation estimate.",
        ),
        _candidate(
            "refspace_0p45",
            {"reference_spatial_amplitude_strength": 0.45},
            "Stronger cross-section reference-field spatial modulation estimate.",
        ),
        _candidate(
            "rho_0p65_noise_0p008",
            {"rho": 0.65, "noise_std": 0.008},
            "Moderately stronger reference with mildly lower raw noise.",
        ),
        _candidate(
            "rho_0p80_noise_0p008",
            {"rho": 0.80, "noise_std": 0.008},
            "Upper reference ratio with mildly lower raw noise.",
        ),
        _candidate(
            "rho_0p65_velocity_0p15mmps",
            {"rho": 0.65, "mean_flow_velocity_m_s": 1.5e-4},
            "Moderately stronger reference and slower transit.",
        ),
        _candidate(
            "rho_0p80_velocity_0p15mmps",
            {"rho": 0.80, "mean_flow_velocity_m_s": 1.5e-4},
            "Upper reference ratio and slower transit.",
        ),
        _candidate(
            "velocity_0p15mmps_post_0p001",
            {"mean_flow_velocity_m_s": 1.5e-4, "post_readout_noise_std": 0.001},
            "Slower transit with lower post-readout noise.",
        ),
        _candidate(
            "tau_2ms_velocity_0p15mmps",
            {"lockin_time_constant_s": 2.0e-3, "mean_flow_velocity_m_s": 1.5e-4},
            "Upper lock-in time constant with slower transit.",
        ),
        _candidate(
            "tau_2ms_rho_0p65",
            {"lockin_time_constant_s": 2.0e-3, "rho": 0.65},
            "Upper lock-in time constant with stronger reference.",
        ),
        _candidate(
            "low_noise_stack",
            {
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
            },
            "Lower raw, shot, and post-readout noise together.",
        ),
        _candidate(
            "rho_0p65_low_noise_stack",
            {
                "rho": 0.65,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
            },
            "Moderately stronger reference with lower readout-noise estimates.",
        ),
        _candidate(
            "rho_0p80_low_noise_stack",
            {
                "rho": 0.80,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
            },
            "Upper reference ratio with lower readout-noise estimates.",
        ),
        _candidate(
            "rho_0p65_velocity_0p15mmps_noise_0p008",
            {"rho": 0.65, "mean_flow_velocity_m_s": 1.5e-4, "noise_std": 0.008},
            "Moderate reference, slower transit, and mildly lower raw noise.",
        ),
        _candidate(
            "rho_0p80_velocity_0p15mmps_noise_0p008",
            {"rho": 0.80, "mean_flow_velocity_m_s": 1.5e-4, "noise_std": 0.008},
            "Upper reference, slower transit, and mildly lower raw noise.",
        ),
        _candidate(
            "rho_0p65_refspace_0p45",
            {"rho": 0.65, "reference_spatial_amplitude_strength": 0.45},
            "Stronger reference ratio and spatial modulation estimates.",
        ),
        _candidate(
            "velocity_0p15mmps_refspace_0p45",
            {"mean_flow_velocity_m_s": 1.5e-4, "reference_spatial_amplitude_strength": 0.45},
            "Slower transit with stronger spatial modulation.",
        ),
        _candidate(
            "center_bias_1p0",
            {
                "initial_position_distribution_mode": "center_biased_surrogate",
                "initial_position_center_bias_strength": 1.0,
            },
            "Center-biased cross-section occupancy surrogate; expected to raise large-Au pulse validity more than small-Au.",
        ),
        _candidate(
            "center_bias_2p0",
            {
                "initial_position_distribution_mode": "center_biased_surrogate",
                "initial_position_center_bias_strength": 2.0,
            },
            "Stronger center-biased cross-section occupancy sensitivity.",
        ),
        _candidate(
            "velocity_0p15mmps_post_0p001_uniform_accessible",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "uniform_accessible_area",
            },
            "Best prior flow/noise candidate with uniform accessible cross-section occupancy instead of flux-weighted sampling.",
        ),
        _candidate(
            "low_noise_stack_uniform_accessible",
            {
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "uniform_accessible_area",
            },
            "Lower noise stack with uniform accessible cross-section occupancy.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_uniform_accessible",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "uniform_accessible_area",
            },
            "Lower noise, slower transit, and uniform accessible cross-section occupancy.",
        ),
        _candidate(
            "velocity_0p15mmps_post_0p001_center_bias_1p0",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "center_biased_surrogate",
                "initial_position_center_bias_strength": 1.0,
            },
            "Best prior flow/noise candidate plus mild center-biased occupancy.",
        ),
        _candidate(
            "velocity_0p15mmps_post_0p001_center_bias_2p0",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "center_biased_surrogate",
                "initial_position_center_bias_strength": 2.0,
            },
            "Best prior flow/noise candidate plus stronger center-biased occupancy.",
        ),
        _candidate(
            "low_noise_stack_center_bias_2p0",
            {
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "center_biased_surrogate",
                "initial_position_center_bias_strength": 2.0,
            },
            "Lower noise stack plus stronger center-biased occupancy.",
        ),
        _candidate(
            "velocity_0p15mmps_post_0p001_ywaist_1p2um",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "post_readout_noise_std": 0.001,
                "optical_illumination_beam_waist_y_m": 1.2e-6,
            },
            "Sensitivity to the finite flow-direction spot-size estimate near the Tsuyama ~2 um spot statement.",
        ),
        _candidate(
            "velocity_0p15mmps_post_0p001_center_bias_1p0_ywaist_1p0um",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "center_biased_surrogate",
                "initial_position_center_bias_strength": 1.0,
                "optical_illumination_beam_waist_y_m": 1.0e-6,
            },
            "Mild center-biased occupancy plus a larger flow-direction illumination waist.",
        ),
        _candidate(
            "low_noise_stack_center_bias_2p0_ywaist_1p0um",
            {
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "center_biased_surrogate",
                "initial_position_center_bias_strength": 2.0,
                "optical_illumination_beam_waist_y_m": 1.0e-6,
            },
            "Lower noise, stronger center-biased occupancy, and a larger flow-direction illumination waist.",
        ),
        _candidate(
            "logger_0p5ms_baseline_current",
            {"pulse_extraction_sampling_interval_s": 5.0e-4},
            "Apply Tsuyama's 0.5 ms data-logger interval before thresholding and pulse extraction.",
        ),
        _candidate(
            "logger_0p5ms_uniform_accessible",
            {
                "pulse_extraction_sampling_interval_s": 5.0e-4,
                "initial_position_distribution_mode": "uniform_accessible_area",
            },
            "0.5 ms logger sampling with uniform accessible cross-section occupancy.",
        ),
        _candidate(
            "logger_0p5ms_low_noise_stack_uniform_accessible",
            {
                "pulse_extraction_sampling_interval_s": 5.0e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "uniform_accessible_area",
            },
            "0.5 ms logger sampling applied to the prior best low-noise uniform-accessible candidate.",
        ),
        _candidate(
            "logger_0p5ms_velocity_0p15mmps_low_noise_stack_uniform_accessible",
            {
                "pulse_extraction_sampling_interval_s": 5.0e-4,
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "uniform_accessible_area",
            },
            "0.5 ms logger sampling plus the balanced slower-flow low-noise uniform-accessible candidate.",
        ),
        _candidate(
            "logger_0p5ms_conservative_baseline_current",
            {
                "pulse_extraction_sampling_interval_s": 5.0e-4,
                "pulse_duration_estimation_policy": "sample_span_conservative",
            },
            "0.5 ms logger sampling with conservative sample-span duration gating.",
        ),
        _candidate(
            "logger_0p5ms_conservative_low_noise_stack_uniform_accessible",
            {
                "pulse_extraction_sampling_interval_s": 5.0e-4,
                "pulse_duration_estimation_policy": "sample_span_conservative",
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "uniform_accessible_area",
            },
            "Prior low-noise uniform-accessible candidate with logger sampling and conservative duration gating.",
        ),
        _candidate(
            "logger_0p5ms_conservative_velocity_0p15mmps_low_noise_stack_uniform_accessible",
            {
                "pulse_extraction_sampling_interval_s": 5.0e-4,
                "pulse_duration_estimation_policy": "sample_span_conservative",
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "uniform_accessible_area",
            },
            "Balanced slower-flow candidate with logger sampling and conservative duration gating.",
        ),
        _candidate(
            "logger_0p5ms_conservative_low_noise_stack_fluxmix_0p20",
            {
                "pulse_extraction_sampling_interval_s": 5.0e-4,
                "pulse_duration_estimation_policy": "sample_span_conservative",
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.20,
            },
            "Logger/conservative duration with fine-scan 20% flux-weighted cross-section mixture.",
        ),
        _candidate(
            "low_noise_stack_fluxmix_0p25",
            {
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.25,
            },
            "Cross-section event prior with 25% flux-weighted and 75% uniform-accessible events.",
        ),
        _candidate(
            "low_noise_stack_fluxmix_0p10",
            {
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Fine scan: mostly uniform-accessible event occupancy with 10% flux-weighted crossings.",
        ),
        _candidate(
            "low_noise_stack_fluxmix_0p15",
            {
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.15,
            },
            "Fine scan: mostly uniform-accessible event occupancy with 15% flux-weighted crossings.",
        ),
        _candidate(
            "low_noise_stack_fluxmix_0p20",
            {
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.20,
            },
            "Fine scan: mostly uniform-accessible event occupancy with 20% flux-weighted crossings.",
        ),
        _candidate(
            "low_noise_stack_fluxmix_0p30",
            {
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.30,
            },
            "Fine scan: cross-section event prior with 30% flux-weighted crossings.",
        ),
        _candidate(
            "low_noise_stack_fluxmix_0p50",
            {
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.50,
            },
            "Cross-section event prior halfway between flux-weighted crossings and uniform occupancy.",
        ),
        _candidate(
            "low_noise_stack_fluxmix_0p75",
            {
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.75,
            },
            "Cross-section event prior with mostly flux-weighted crossings.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p25",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.25,
            },
            "Slower-flow low-noise candidate with mostly uniform-accessible event occupancy.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p10",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Slower-flow fine scan with 10% flux-weighted crossings.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p05",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.05,
            },
            "Slower-flow fine scan with 5% flux-weighted crossings.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p075",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.075,
            },
            "Slower-flow fine scan with 7.5% flux-weighted crossings.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p125",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.125,
            },
            "Slower-flow fine scan with 12.5% flux-weighted crossings.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p15",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.15,
            },
            "Slower-flow fine scan with 15% flux-weighted crossings.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p20",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.20,
            },
            "Slower-flow fine scan with 20% flux-weighted crossings.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p30",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.30,
            },
            "Slower-flow fine scan with 30% flux-weighted crossings.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p50",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.50,
            },
            "Slower-flow low-noise candidate with equal flux/uniform cross-section mixture.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_refspace_0p30",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
                "reference_spatial_amplitude_strength": 0.30,
            },
            "Best prior fluxmix candidate with slightly weaker reference-field spatial modulation.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_rho_0p45",
            {
                "rho": 0.45,
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Best prior fluxmix candidate with a slightly weaker reference/scatter ratio.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_rho_0p55",
            {
                "rho": 0.55,
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Best prior fluxmix candidate with a mildly stronger reference/scatter ratio.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_rho_0p60",
            {
                "rho": 0.60,
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Best prior fluxmix candidate with a stronger reference/scatter ratio.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_rho_0p65",
            {
                "rho": 0.65,
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Best prior fluxmix candidate with an upper-envelope reference/scatter ratio.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_refspace_0p325",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
                "reference_spatial_amplitude_strength": 0.325,
            },
            "Best prior fluxmix candidate with a mildly weaker reference-field spatial modulation.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_refspace_0p375",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
                "reference_spatial_amplitude_strength": 0.375,
            },
            "Best prior fluxmix candidate with a mildly stronger reference-field spatial modulation.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_refspace_0p40",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
                "reference_spatial_amplitude_strength": 0.40,
            },
            "Best prior fluxmix candidate with stronger reference-field spatial modulation.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_flowplug",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "flow_profile_model": "plug",
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Best prior fluxmix candidate with plug-flow transit instead of the rectangular-duct velocity profile.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_flowparabolic",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "flow_profile_model": "parabolic_rect",
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Best prior fluxmix candidate with the separable parabolic rectangular-flow surrogate.",
        ),
        _candidate(
            "velocity_0p15mmps_fluxmix_0p10_flowparabolic_noise_0p007",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "flow_profile_model": "parabolic_rect",
                "noise_std": 0.007,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Parabolic-flow velocity distribution with a slightly higher raw-noise estimate.",
        ),
        _candidate(
            "velocity_0p15mmps_fluxmix_0p10_flowparabolic_noise_0p008",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "flow_profile_model": "parabolic_rect",
                "noise_std": 0.008,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Parabolic-flow velocity distribution with a moderate raw-noise estimate.",
        ),
        _candidate(
            "velocity_0p15mmps_fluxmix_0p10_flowparabolic_noise_0p009",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "flow_profile_model": "parabolic_rect",
                "noise_std": 0.009,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Parabolic-flow velocity distribution with a higher raw-noise estimate.",
        ),
        _candidate(
            "velocity_0p15mmps_fluxmix_0p10_flowparabolic_noise_0p010",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "flow_profile_model": "parabolic_rect",
                "noise_std": 0.010,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Parabolic-flow velocity distribution with the original raw-noise estimate.",
        ),
        _candidate(
            "velocity_0p15mmps_fluxmix_0p10_flowparabolic_rho_0p45",
            {
                "rho": 0.45,
                "mean_flow_velocity_m_s": 1.5e-4,
                "flow_profile_model": "parabolic_rect",
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Parabolic-flow velocity distribution with a weaker reference/scatter ratio.",
        ),
        _candidate(
            "velocity_0p15mmps_fluxmix_0p10_flowparabolic_rho_0p45_noise_0p008",
            {
                "rho": 0.45,
                "mean_flow_velocity_m_s": 1.5e-4,
                "flow_profile_model": "parabolic_rect",
                "noise_std": 0.008,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Parabolic-flow velocity distribution with weaker reference and moderate raw noise.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_ywaist_1p0um",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
                "optical_illumination_beam_waist_y_m": 1.0e-6,
            },
            "Best prior fluxmix candidate with a wider flow-direction illumination waist.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_ywaist_1p2um",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
                "optical_illumination_beam_waist_y_m": 1.2e-6,
            },
            "Best prior fluxmix candidate with a still wider flow-direction illumination waist.",
        ),
        _candidate(
            "blank_edge_velocity_0p15mmps_low_noise_stack_fluxmix_0p10",
            {
                "threshold_calibration_source": "blank_trace_empirical",
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Best prior fluxmix candidate with the blank-source edge-background threshold surrogate.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_noise_0p0055",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.0055,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Best prior fluxmix candidate with a slightly lower raw detector-noise estimate.",
        ),
        _candidate(
            "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_noise_0p0065",
            {
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.0065,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.10,
            },
            "Best prior fluxmix candidate with a slightly higher raw detector-noise estimate.",
        ),
        _candidate(
            "blank_edge_low_noise_stack_uniform_accessible",
            {
                "threshold_calibration_source": "blank_trace_empirical",
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "uniform_accessible_area",
            },
            "Use the blank-source threshold route; without raw blank files, runtime uses pre/post-event edge-background surrogate.",
        ),
        _candidate(
            "bootstrap_edge_low_noise_stack_uniform_accessible",
            {
                "threshold_calibration_source": "block_bootstrap",
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "uniform_accessible_area",
            },
            "Use the bootstrap threshold route; without raw blank files, runtime uses pre/post-event edge-background surrogate.",
        ),
        _candidate(
            "colored_ar1_0p0005_tau_1ms_low_noise_stack_uniform_accessible",
            {
                "colored_noise_false_alarm_model": "iid_gaussian_surrogate",
                "post_readout_colored_noise_std": 0.0005,
                "post_readout_colored_noise_tau_s": 1.0e-3,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "uniform_accessible_area",
            },
            "Add a mild AR(1)-like colored blank/background noise term at the lock-in output.",
        ),
        _candidate(
            "colored_ar1_0p001_tau_1ms_low_noise_stack_uniform_accessible",
            {
                "colored_noise_false_alarm_model": "iid_gaussian_surrogate",
                "post_readout_colored_noise_std": 0.001,
                "post_readout_colored_noise_tau_s": 1.0e-3,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "uniform_accessible_area",
            },
            "Add a stronger AR(1)-like colored blank/background noise term at the lock-in output.",
        ),
        _candidate(
            "colored_ar1_0p001_tau_2ms_low_noise_stack_uniform_accessible",
            {
                "colored_noise_false_alarm_model": "iid_gaussian_surrogate",
                "post_readout_colored_noise_std": 0.001,
                "post_readout_colored_noise_tau_s": 2.0e-3,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "uniform_accessible_area",
            },
            "Colored blank/background sensitivity with a 2 ms correlation time.",
        ),
        _candidate(
            "colored_ar1_0p0005_tau_1ms_low_noise_stack_fluxmix_0p20",
            {
                "colored_noise_false_alarm_model": "iid_gaussian_surrogate",
                "post_readout_colored_noise_std": 0.0005,
                "post_readout_colored_noise_tau_s": 1.0e-3,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.20,
            },
            "Mild colored blank/background noise with a conservative cross-section mixture.",
        ),
        _candidate(
            "logger_0p5ms_blank_edge_low_noise_stack_uniform_accessible",
            {
                "pulse_extraction_sampling_interval_s": 5.0e-4,
                "threshold_calibration_source": "blank_trace_empirical",
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "uniform_accessible_area",
            },
            "Combine 0.5 ms logger sampling with the blank-source edge-background threshold surrogate.",
        ),
        _candidate(
            "logger_0p5ms_blank_edge_velocity_0p15mmps_low_noise_stack_uniform_accessible",
            {
                "pulse_extraction_sampling_interval_s": 5.0e-4,
                "threshold_calibration_source": "blank_trace_empirical",
                "mean_flow_velocity_m_s": 1.5e-4,
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "uniform_accessible_area",
            },
            "Combine logger sampling, blank-source edge thresholding, slower flow, and low-noise uniform-accessible occupancy.",
        ),
        _candidate(
            "logger_0p5ms_blank_edge_low_noise_stack_fluxmix_0p25",
            {
                "pulse_extraction_sampling_interval_s": 5.0e-4,
                "threshold_calibration_source": "blank_trace_empirical",
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.25,
            },
            "Logger plus blank-edge thresholding with a mostly uniform-accessible cross-section mixture.",
        ),
        _candidate(
            "logger_0p5ms_blank_edge_low_noise_stack_fluxmix_0p50",
            {
                "pulse_extraction_sampling_interval_s": 5.0e-4,
                "threshold_calibration_source": "blank_trace_empirical",
                "noise_std": 0.006,
                "shot_noise_scale": 0.0005,
                "post_readout_noise_std": 0.001,
                "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
                "initial_position_flux_weighted_mixture_fraction": 0.50,
            },
            "Logger plus blank-edge thresholding with equal flux/uniform cross-section mixture.",
        ),
    ]
    seen: set[str] = set()
    deduped: list[CalibrationCandidate] = []
    for candidate in candidates:
        if candidate.candidate_id not in seen:
            deduped.append(candidate)
            seen.add(candidate.candidate_id)
    return deduped


def candidate_by_id() -> dict[str, CalibrationCandidate]:
    return {candidate.candidate_id: candidate for candidate in candidate_catalog()}


def build_candidate_cfg(
    candidate: CalibrationCandidate,
    *,
    n_events: int,
    random_seed: int,
    scenario_id: str = CALIBRATION_SCENARIO_ID,
) -> lane.SimulationConfig:
    cfg = lane.build_scenario_cfg(scenario_id, n_events=n_events)
    overrides = {
        key: value
        for key, value in candidate.overrides.items()
        if key not in OPTICAL_ESTIMATED_PARAMETER_FIELDS
    }
    cfg = replace(cfg, **overrides)
    return replace(cfg, random_seed=int(random_seed))


def build_candidate_optical_template(candidate: CalibrationCandidate) -> Any:
    overrides: dict[str, Any] = {}
    if "optical_illumination_beam_waist_y_m" in candidate.overrides:
        overrides["illumination_beam_waist_y_m"] = candidate.overrides[
            "optical_illumination_beam_waist_y_m"
        ]
    if not overrides:
        return lane.OPTICAL_TEMPLATE
    return replace(lane.OPTICAL_TEMPLATE, **overrides)


def resolved_estimated_parameter_values(
    cfg: lane.SimulationConfig,
    optical_template: Any,
) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for field in ESTIMATED_PARAMETER_FIELDS:
        if field == "optical_illumination_beam_waist_y_m":
            values[field] = optical_template.illumination_beam_waist_y_m
        else:
            values[field] = getattr(cfg, field)
    return values


def run_candidate_sweep(
    candidate: CalibrationCandidate,
    *,
    n_events: int,
    random_seed: int,
    n_workers: int,
    scenario_id: str = CALIBRATION_SCENARIO_ID,
    cases: tuple[tuple[int, int, int], ...] = CALIBRATION_CASES,
    claim_level: str,
) -> pd.DataFrame:
    cfg = build_candidate_cfg(
        candidate,
        n_events=n_events,
        random_seed=random_seed,
        scenario_id=scenario_id,
    )
    optical_template = build_candidate_optical_template(candidate)
    particles = [lane.make_particle("gold", diameter_nm) for diameter_nm in lane.GOLD_DIAMETERS_NM]
    frames: list[pd.DataFrame] = []
    for wavelength_nm, width_nm, depth_nm in cases:
        results = lane.run_parameter_sweep(
            particle_types=particles,
            medium=lane.WATER,
            width_list_m=np.array([float(width_nm) * 1e-9], dtype=float),
            depth_list_m=np.array([float(depth_nm) * 1e-9], dtype=float),
            wavelength_list_m=np.array([float(wavelength_nm) * 1e-9], dtype=float),
            optical_template=optical_template,
            sim_cfg=cfg,
            theta_grid_rad=lane.THETA_GRID_RAD,
            baseline_particle=lane.BASELINE_PARTICLE,
            baseline_channel=lane.case_baseline_channel(width_nm, depth_nm),
            verbose=False,
            n_workers=n_workers,
        )
        frames.append(
            lane.flatten_sweep_results(
                results,
                scenario_config_id=scenario_id,
                cfg=cfg,
                n_events=n_events,
                random_seed=random_seed,
                claim_level=claim_level,
            )
        )
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    df.insert(0, "candidate_id", candidate.candidate_id)
    df.insert(1, "target_schema_id", TARGET_SCHEMA_ID)
    df["candidate_rationale"] = candidate.rationale
    df["candidate_overrides_json"] = json.dumps(
        candidate.overrides,
        sort_keys=True,
        separators=(",", ":"),
    )
    for field, value in resolved_estimated_parameter_values(cfg, optical_template).items():
        df[field] = value
    return df


def _rate_penalty(rate: float, low: float, high: float, target: float) -> tuple[float, bool]:
    span = max(high - low, 1e-12)
    if rate < low:
        return ((low - rate) / span) ** 2 + 0.05 * ((target - rate) / span) ** 2, False
    if rate > high:
        return ((rate - high) / span) ** 2 + 0.05 * ((target - rate) / span) ** 2, False
    return 0.05 * ((target - rate) / span) ** 2, True


def summarize_candidate(
    df: pd.DataFrame,
    candidate: CalibrationCandidate,
    *,
    n_events: int,
    random_seed: int,
    n_workers: int,
    scenario_id: str = CALIBRATION_SCENARIO_ID,
) -> dict[str, Any]:
    agg_spec: dict[str, tuple[str, str]] = {
        "median_detection_rate": ("detection_rate", "median"),
        "min_detection_rate": ("detection_rate", "min"),
        "max_detection_rate": ("detection_rate", "max"),
        "median_mean_peak_height": ("mean_peak_height", "median"),
        "median_mean_local_snr": ("mean_local_snr", "median"),
    }
    optional_rate_columns = (
        "selected_detector_mode_candidate_detection_rate",
        "selected_detector_mode_candidate_fraction",
        "selected_detector_mode_annulus_detection_rate",
        "selected_detector_mode_annulus_fraction",
    )
    for column in optional_rate_columns:
        if column in df.columns:
            agg_spec[f"median_{column}"] = (column, "median")

    by_diameter = (
        df.groupby("particle_diameter_nm", dropna=False)
        .agg(**agg_spec)
        .reindex(list(lane.GOLD_DIAMETERS_NM))
    )
    penalties: dict[str, float] = {}
    band_hits: dict[str, bool] = {}
    score = 0.0
    for diameter_nm, target in TARGET_BANDS.items():
        rate = float(by_diameter.loc[diameter_nm, "median_detection_rate"])
        penalty, hit = _rate_penalty(
            rate,
            float(target["low"]),
            float(target["high"]),
            float(target["target"]),
        )
        penalties[f"au{diameter_nm}_rate_penalty"] = float(penalty)
        band_hits[f"au{diameter_nm}_within_band"] = bool(hit)
        score += penalty

    rates = [
        float(by_diameter.loc[diameter_nm, "median_detection_rate"])
        for diameter_nm in lane.GOLD_DIAMETERS_NM
    ]
    monotonic_penalty = 0.0
    for left, right in zip(rates, rates[1:]):
        if right + 1e-12 < left:
            monotonic_penalty += (left - right + 0.01) * 20.0
    score += monotonic_penalty

    reference_bad = bool(
        (df["reference_operating_band"].astype(str) == "reference_too_weak").any()
    )
    rho_bad = bool((df["rho_physical_envelope_status"].astype(str) != "within_envelope").any())
    na_bad = bool(df["na_cutoff_active"].astype(bool).any())
    hard_guardrail_penalty = 0.0
    if reference_bad:
        hard_guardrail_penalty += 5.0
    if rho_bad:
        hard_guardrail_penalty += 5.0
    if na_bad:
        hard_guardrail_penalty += 5.0
    score += hard_guardrail_penalty

    gold_status = lane.evaluate_gold_anchor(df, final_stage=n_events >= 10000).get(
        scenario_id,
        {},
    )
    if not bool(gold_status.get("gold_anchor_pass", False)):
        score += 2.0

    cfg = build_candidate_cfg(
        candidate,
        n_events=n_events,
        random_seed=random_seed,
        scenario_id=scenario_id,
    )
    optical_template = build_candidate_optical_template(candidate)
    row: dict[str, Any] = {
        "candidate_id": candidate.candidate_id,
        "target_schema_id": TARGET_SCHEMA_ID,
        "scenario_config_id": scenario_id,
        "n_events": int(n_events),
        "n_workers": int(n_workers),
        "random_seed": int(random_seed),
        "calibration_score": float(score),
        "target_fit_status": (
            "within_all_bands" if all(band_hits.values()) else "outside_one_or_more_bands"
        ),
        "monotonic_penalty": float(monotonic_penalty),
        "hard_guardrail_penalty": float(hard_guardrail_penalty),
        "reference_bad": reference_bad,
        "rho_bad": rho_bad,
        "na_cutoff_active": na_bad,
        "gold_anchor_pass": bool(gold_status.get("gold_anchor_pass", False)),
        "gold_anchor_primary_blocker": str(
            gold_status.get("gold_anchor_primary_blocker", "missing")
        ),
        "candidate_rationale": candidate.rationale,
        "candidate_overrides_json": json.dumps(
            candidate.overrides,
            sort_keys=True,
            separators=(",", ":"),
        ),
    }
    row.update(penalties)
    row.update(band_hits)
    for diameter_nm in lane.GOLD_DIAMETERS_NM:
        row[f"au{diameter_nm}_median_detection_rate"] = float(
            by_diameter.loc[diameter_nm, "median_detection_rate"]
        )
        row[f"au{diameter_nm}_min_detection_rate"] = float(
            by_diameter.loc[diameter_nm, "min_detection_rate"]
        )
        row[f"au{diameter_nm}_max_detection_rate"] = float(
            by_diameter.loc[diameter_nm, "max_detection_rate"]
        )
        row[f"au{diameter_nm}_median_peak_height"] = float(
            by_diameter.loc[diameter_nm, "median_mean_peak_height"]
        )
        row[f"au{diameter_nm}_median_local_snr"] = float(
            by_diameter.loc[diameter_nm, "median_mean_local_snr"]
        )
        for column in optional_rate_columns:
            aggregate_column = f"median_{column}"
            if aggregate_column in by_diameter.columns:
                row[f"au{diameter_nm}_median_{column}"] = float(
                    by_diameter.loc[diameter_nm, aggregate_column]
                )
    row.update(resolved_estimated_parameter_values(cfg, optical_template))
    for field in PROTECTED_PAPER_CRITERIA:
        value = getattr(cfg, field)
        row[f"protected_{field}"] = value if isinstance(value, str) else float(value)
    return row


def run_stage(
    *,
    candidates: list[CalibrationCandidate],
    n_events: int,
    random_seed: int,
    n_workers: int,
    output_dir: Path,
    stage_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, Any]] = []
    t0 = time.time()
    for index, candidate in enumerate(candidates, start=1):
        print(
            f"[{stage_name}] {index}/{len(candidates)} {candidate.candidate_id}",
            flush=True,
        )
        df = run_candidate_sweep(
            candidate,
            n_events=n_events,
            random_seed=random_seed,
            n_workers=n_workers,
            claim_level=f"tsuyama_detection_rate_calibration_{stage_name}",
        )
        frames.append(df)
        summary_rows.append(
            summarize_candidate(
                df,
                candidate,
                n_events=n_events,
                random_seed=random_seed,
                n_workers=n_workers,
            )
        )
    raw = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    summary = pd.DataFrame(summary_rows).sort_values(
        ["calibration_score", "candidate_id"],
        ignore_index=True,
    )
    raw_path = output_dir / f"{stage_name}_gold_rows_v1.csv"
    summary_path = output_dir / f"{stage_name}_candidate_summary_v1.csv"
    raw.to_csv(raw_path, index=False)
    summary.to_csv(summary_path, index=False)
    meta = {
        "stage": stage_name,
        "target_schema_id": TARGET_SCHEMA_ID,
        "scenario_config_id": CALIBRATION_SCENARIO_ID,
        "cases": [list(case) for case in CALIBRATION_CASES],
        "n_events": int(n_events),
        "n_workers": int(n_workers),
        "random_seed": int(random_seed),
        "candidate_count": int(len(candidates)),
        "rows": int(len(raw)),
        "runtime_s": time.time() - t0,
        "raw_path": str(raw_path),
        "summary_path": str(summary_path),
    }
    write_json(output_dir / f"{stage_name}_meta_v1.json", meta)
    return raw, summary, meta


def select_top_candidates(
    summary: pd.DataFrame,
    *,
    top_k: int,
) -> list[CalibrationCandidate]:
    catalog = candidate_by_id()
    selected_ids: list[str] = []
    if "baseline_current_estimates" in catalog:
        selected_ids.append("baseline_current_estimates")
    for candidate_id in summary["candidate_id"].astype(str).tolist():
        if candidate_id not in selected_ids:
            selected_ids.append(candidate_id)
        if len(selected_ids) >= top_k:
            break
    return [catalog[candidate_id] for candidate_id in selected_ids[:top_k]]


def write_report(
    output_dir: Path,
    *,
    screen_summary: pd.DataFrame,
    verify_summary: pd.DataFrame,
    screen_meta: dict[str, Any],
    verify_meta: dict[str, Any],
) -> Path:
    report_path = output_dir / "tsuyama_detection_rate_calibration_report.md"
    target_lines = [
        (
            f"- Au{diameter_nm}: `{target['low']:.2f}-{target['high']:.2f}` "
            f"(target `{target['target']:.2f}`) - {target['basis']}"
        )
        for diameter_nm, target in TARGET_BANDS.items()
    ]
    protected_lines = [
        f"- `{field}` unchanged from paper-aligned scenario"
        for field in PROTECTED_PAPER_CRITERIA
    ]
    top_verify = verify_summary.head(8).copy()
    selected_candidate_rate_cols = [
        f"au{diameter_nm}_median_selected_detector_mode_candidate_detection_rate"
        for diameter_nm in lane.GOLD_DIAMETERS_NM
    ]
    selected_candidate_fraction_cols = [
        f"au{diameter_nm}_median_selected_detector_mode_candidate_fraction"
        for diameter_nm in lane.GOLD_DIAMETERS_NM
    ]
    selected_annulus_rate_cols = [
        f"au{diameter_nm}_median_selected_detector_mode_annulus_detection_rate"
        for diameter_nm in lane.GOLD_DIAMETERS_NM
    ]
    selected_annulus_fraction_cols = [
        f"au{diameter_nm}_median_selected_detector_mode_annulus_fraction"
        for diameter_nm in lane.GOLD_DIAMETERS_NM
    ]
    top_cols = [
        "candidate_id",
        "calibration_score",
        "target_fit_status",
        "au20_median_detection_rate",
        "au30_median_detection_rate",
        "au40_median_detection_rate",
        "au60_median_detection_rate",
        *selected_candidate_rate_cols,
        *selected_candidate_fraction_cols,
        *selected_annulus_rate_cols,
        *selected_annulus_fraction_cols,
        *ESTIMATED_PARAMETER_FIELDS,
    ]
    top_cols = [column for column in top_cols if column in top_verify.columns]
    top_markdown = dataframe_to_markdown(top_verify[top_cols])
    best = verify_summary.iloc[0].to_dict() if not verify_summary.empty else {}
    lines = [
        "# Tsuyama Detection-Rate Calibration Sensitivity",
        "",
        "## Boundary",
        "",
        "- This is a sensitivity/calibration lane, not a replacement for global defaults.",
        "- Only estimated/surrogate parameters are changed.",
        "- It uses Tsuyama 2022 NODI single-channel gold conclusions as broad target bands.",
        "- The paper does not provide a direct ground-truth crossing-to-detection efficiency table; these bands are operational targets, not empirical rates.",
        "",
        "## Target Bands",
        "",
        *target_lines,
        "",
        "## Protected Criteria",
        "",
        *protected_lines,
        "",
        "## Run Metadata",
        "",
        f"- screen_events: `{screen_meta['n_events']}`",
        f"- verify_events: `{verify_meta['n_events']}`",
        f"- workers: `{verify_meta['n_workers']}`",
        f"- scenario: `{CALIBRATION_SCENARIO_ID}`",
        f"- cases: `{CALIBRATION_CASES}`",
        "",
        "## Best Verified Candidate",
        "",
        f"- candidate_id: `{best.get('candidate_id', 'none')}`",
        f"- calibration_score: `{best.get('calibration_score', float('nan'))}`",
        f"- target_fit_status: `{best.get('target_fit_status', 'none')}`",
        f"- overrides: `{best.get('candidate_overrides_json', '{}')}`",
        "",
        "## Top Verified Candidates",
        "",
        top_markdown,
        "",
        "## Output Files",
        "",
        "- `screen_gold_rows_v1.csv`",
        "- `screen_candidate_summary_v1.csv`",
        "- `verify_gold_rows_v1.csv`",
        "- `verify_candidate_summary_v1.csv`",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    headers = [str(col) for col in df.columns]
    body: list[list[str]] = []
    for row in df.itertuples(index=False, name=None):
        body.append([_markdown_cell(value) for value in row])
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in body))
        for index in range(len(headers))
    ]
    header_line = "| " + " | ".join(
        header.ljust(widths[index]) for index, header in enumerate(headers)
    ) + " |"
    sep_line = "| " + " | ".join("-" * width for width in widths) + " |"
    row_lines = [
        "| " + " | ".join(
            value.ljust(widths[index]) for index, value in enumerate(row)
        ) + " |"
        for row in body
    ]
    return "\n".join([header_line, sep_line, *row_lines])


def _markdown_cell(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value).replace("|", "\\|")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sensitivity-search estimated parameters for Tsuyama-like detection rates."
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--screen-events", type=int, default=1000)
    parser.add_argument("--verify-events", type=int, default=10000)
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=0,
        help="Limit candidate count for quick debugging; 0 means full catalog.",
    )
    parser.add_argument(
        "--candidate-ids",
        default="",
        help=(
            "Comma-separated candidate IDs to run; empty means the full catalog "
            "or the candidate-limit prefix."
        ),
    )
    parser.add_argument(
        "--screen-only",
        action="store_true",
        help="Run candidate screening only and skip top-candidate verification.",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write the report from existing screen/verify CSV and JSON outputs.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)
    if args.report_only:
        screen_summary = pd.read_csv(output_dir / "screen_candidate_summary_v1.csv")
        verify_summary = pd.read_csv(output_dir / "verify_candidate_summary_v1.csv")
        with (output_dir / "screen_meta_v1.json").open("r", encoding="utf-8") as fh:
            screen_meta = json.load(fh)
        with (output_dir / "verify_meta_v1.json").open("r", encoding="utf-8") as fh:
            verify_meta = json.load(fh)
        report_path = write_report(
            output_dir,
            screen_summary=screen_summary,
            verify_summary=verify_summary,
            screen_meta=screen_meta,
            verify_meta=verify_meta,
        )
        print(json.dumps({"report_path": str(report_path)}, ensure_ascii=False, indent=2))
        return
    candidates = candidate_catalog()
    if str(args.candidate_ids).strip():
        catalog = candidate_by_id()
        selected_ids = [
            item.strip()
            for item in str(args.candidate_ids).split(",")
            if item.strip()
        ]
        unknown = [candidate_id for candidate_id in selected_ids if candidate_id not in catalog]
        if unknown:
            raise ValueError(f"Unknown candidate IDs: {unknown}")
        candidates = [catalog[candidate_id] for candidate_id in selected_ids]
    if int(args.candidate_limit) > 0:
        candidates = candidates[: int(args.candidate_limit)]
    screen_raw, screen_summary, screen_meta = run_stage(
        candidates=candidates,
        n_events=int(args.screen_events),
        random_seed=int(args.random_seed),
        n_workers=int(args.workers),
        output_dir=output_dir,
        stage_name="screen",
    )
    _ = screen_raw
    if args.screen_only:
        print(json.dumps(screen_meta, ensure_ascii=False, indent=2))
        return
    verify_candidates = select_top_candidates(
        screen_summary,
        top_k=max(1, int(args.top_k)),
    )
    verify_raw, verify_summary, verify_meta = run_stage(
        candidates=verify_candidates,
        n_events=int(args.verify_events),
        random_seed=int(args.random_seed),
        n_workers=int(args.workers),
        output_dir=output_dir,
        stage_name="verify",
    )
    _ = verify_raw
    report_path = write_report(
        output_dir,
        screen_summary=screen_summary,
        verify_summary=verify_summary,
        screen_meta=screen_meta,
        verify_meta=verify_meta,
    )
    print(
        json.dumps(
            {
                "screen_meta": screen_meta,
                "verify_meta": verify_meta,
                "report_path": str(report_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
