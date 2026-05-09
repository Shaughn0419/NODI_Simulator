"""Bayesian calibration scaffold diagnostics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .data_objects import SimulationConfig
from .type_coerce import blocker_summary as _blocker_summary


BAYESIAN_CALIBRATION_DIAGNOSTIC_FIELDS = (
    "bayesian_calibration_schema",
    "bayesian_calibration_status",
    "bayesian_calibration_claim_level",
    "bayesian_prior_schema",
    "bayesian_prior_parameters",
    "bayesian_posterior_schema",
    "bayesian_posterior_available",
    "bayesian_posterior_sample_count",
    "bayesian_posterior_source",
    "posterior_predictive_detection_rate_p10",
    "posterior_predictive_detection_rate_p50",
    "posterior_predictive_detection_rate_p90",
    "posterior_predictive_design_score_p10",
    "posterior_predictive_design_score_p50",
    "posterior_predictive_design_score_p90",
    "posterior_predictive_interval_status",
    "bayesian_calibration_gate_passed",
    "bayesian_calibration_blocker_summary",
)


def _prior_parameters(sim_cfg: SimulationConfig) -> dict[str, dict[str, object]]:
    return {
        "K_sca": {
            "distribution": "lognormal",
            "median": 1.0,
            "geometric_sigma": 2.0,
            "status": str(sim_cfg.K_sca_calibration_status),
        },
        "rho": {
            "distribution": "truncated_normal",
            "mean": float(sim_cfg.rho),
            "sd": max(abs(float(sim_cfg.rho)) * 0.5, 1.0e-6),
            "lower": 0.0,
        },
        "global_phase_offset_rad": {
            "distribution": "wrapped_uniform",
            "lower": -3.141592653589793,
            "upper": 3.141592653589793,
            "status": str(sim_cfg.global_phase_offset_source),
        },
        "A_ref_scale": {
            "distribution": "lognormal",
            "median": 1.0,
            "geometric_sigma": 2.0,
        },
        "absolute_throughput": {
            "distribution": "lognormal",
            "median": 1.0,
            "geometric_sigma": 3.0,
            "status": str(sim_cfg.absolute_throughput_route),
        },
        "noise_scale": {
            "distribution": "halfnormal",
            "scale": max(float(sim_cfg.noise_std), 1.0e-12),
            "status": str(sim_cfg.detector_noise_model_route),
        },
    }


def build_bayesian_calibration_scaffold(
    reference: Mapping[str, Any],
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """Export Bayesian calibration schemas without running posterior sampling."""
    standard_path_configured = bool(
        reference.get("standard_particle_calibration_path_configured", False)
    )
    synthetic_fixture = bool(
        reference.get("standard_particle_synthetic_fixture_active", False)
    )
    standard_status = str(
        reference.get("standard_particle_calibration_status", "not_calibrated")
    )
    real_standard_available = bool(
        standard_path_configured
        and not synthetic_fixture
        and standard_status == "standard_particle_table_available"
    )

    blockers = ["posterior_sampler_not_implemented"]
    if not real_standard_available:
        blockers.append("real_standard_particle_data_missing")
    if synthetic_fixture:
        blockers.append("synthetic_standard_fixture_not_posterior_data")

    status = (
        "real_standard_data_available_sampler_not_implemented"
        if real_standard_available
        else "scaffold_only_no_real_standard_data"
    )

    return {
        "bayesian_calibration_schema": "bayesian_calibration_scaffold_v1",
        "bayesian_calibration_status": status,
        "bayesian_calibration_claim_level": (
            "scaffold_only_no_posterior_claim"
        ),
        "bayesian_prior_schema": (
            "K_sca,rho,global_phase_offset,A_ref_scale,throughput,noise"
        ),
        "bayesian_prior_parameters": _prior_parameters(sim_cfg),
        "bayesian_posterior_schema": (
            "posterior_samples_and_predictive_intervals_required"
        ),
        "bayesian_posterior_available": False,
        "bayesian_posterior_sample_count": 0,
        "bayesian_posterior_source": "not_available_sampler_not_run",
        "posterior_predictive_detection_rate_p10": None,
        "posterior_predictive_detection_rate_p50": None,
        "posterior_predictive_detection_rate_p90": None,
        "posterior_predictive_design_score_p10": None,
        "posterior_predictive_design_score_p50": None,
        "posterior_predictive_design_score_p90": None,
        "posterior_predictive_interval_status": (
            "not_available_no_posterior_samples"
        ),
        "bayesian_calibration_gate_passed": False,
        "bayesian_calibration_blocker_summary": _blocker_summary(blockers),
    }
