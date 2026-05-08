"""Correlated EV population-prior diagnostics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .data_objects import Particle, SimulationConfig
from .type_coerce import finite_float as _as_float


EV_POPULATION_PRIOR_DIAGNOSTIC_FIELDS = (
    "ev_population_prior_schema",
    "ev_population_prior_status",
    "ev_population_prior_claim_level",
    "ev_prior_model",
    "ev_prior_physical_validity",
    "ev_prior_correlated_parameter_schema",
    "ev_prior_population_bins",
    "ev_prior_sample_preparation_profile",
    "ev_prior_selection_function_linked",
    "ev_prior_invalid_combination_policy",
    "ev_low_RI_tail_detection_risk",
    "ev_prior_gate_passed",
    "ev_prior_blocker_summary",
)

_EV_PRIOR_SCHEMA = (
    "diameter_nm,refractive_index,membrane_shell_nm,corona_state,"
    "sample_prep_weight,selection_terms"
)

def _bounded_probability(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _is_ev_particle(particle: Particle) -> bool:
    label = f"{particle.name} {particle.model_type} {particle.structure_key}".casefold()
    return (
        "ev" in label
        or "exosome" in label
        or str(particle.structure_params or {}).casefold().find("exosome") >= 0
    )


def _nominal_diameter_nm(particle: Particle) -> float:
    return float(particle.radius_m) * 2.0e9


def _nominal_refractive_index(particle: Particle) -> float:
    return float(particle.n_real)


def _population_bins(
    particle: Particle,
    diagnostics: Mapping[str, Any],
    sim_cfg: SimulationConfig,
) -> tuple[dict[str, object], ...]:
    diameter_nm = _nominal_diameter_nm(particle)
    nominal_ri = _nominal_refractive_index(particle)
    detection_rate = _bounded_probability(_as_float(diagnostics.get("detection_rate"), 0.0))
    qc_rate = _bounded_probability(
        _as_float(diagnostics.get("event_qc_pass_fraction"), 1.0)
    )
    prep_weight = _bounded_probability(_as_float(diagnostics.get("EV_model_weight"), 1.0))
    sample_profile = str(sim_cfg.EV_sample_preparation_profile)
    return (
        {
            "population_bin_id": "ev_low_RI_small_tail",
            "p_true": 0.25,
            "diameter_nm": max(30.0, 0.70 * diameter_nm),
            "refractive_index": min(1.37, nominal_ri),
            "membrane_shell_nm": 4.0,
            "corona_state": "minimal_corona_low_RI_tail",
            "particle_family": "EV_sEV",
            "P_pass_sample_prep": prep_weight,
            "P_detect": _bounded_probability(0.60 * detection_rate),
            "P_pass_QC": qc_rate,
            "sample_preparation_profile": sample_profile,
        },
        {
            "population_bin_id": "ev_nominal_mode",
            "p_true": 0.50,
            "diameter_nm": diameter_nm,
            "refractive_index": nominal_ri,
            "membrane_shell_nm": 5.0,
            "corona_state": "nominal_corona",
            "particle_family": "EV_sEV",
            "P_pass_sample_prep": prep_weight,
            "P_detect": detection_rate,
            "P_pass_QC": qc_rate,
            "sample_preparation_profile": sample_profile,
        },
        {
            "population_bin_id": "ev_large_or_corona_rich_tail",
            "p_true": 0.25,
            "diameter_nm": 1.35 * diameter_nm,
            "refractive_index": max(nominal_ri, 1.39),
            "membrane_shell_nm": 6.0,
            "corona_state": "corona_or_coisolate_rich_tail",
            "particle_family": "EV_sEV",
            "P_pass_sample_prep": _bounded_probability(0.85 * prep_weight),
            "P_detect": _bounded_probability(1.25 * detection_rate),
            "P_pass_QC": qc_rate,
            "sample_preparation_profile": sample_profile,
        },
    )


def _low_ri_tail_risk(
    diagnostics: Mapping[str, Any],
    nominal_ri: float,
) -> str:
    existing_bias = str(diagnostics.get("low_RI_EV_under_detection_bias", ""))
    detection_rate = _bounded_probability(_as_float(diagnostics.get("detection_rate"), 0.0))
    if "under" in existing_bias or "possible" in existing_bias:
        return "elevated_low_RI_tail_under_detection_risk"
    if nominal_ri <= 1.38 and detection_rate < 0.5:
        return "elevated_low_RI_tail_under_detection_risk"
    if nominal_ri <= 1.38:
        return "low_RI_tail_present_monitor_selection_bias"
    return "not_flagged_by_current_single_case_surrogate"


def build_ev_population_prior_diagnostics(
    particle: Particle,
    diagnostics: Mapping[str, Any],
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """Build a correlated EV prior scaffold without inferring a true population."""
    if not _is_ev_particle(particle):
        return {
            "ev_population_prior_schema": "ev_correlated_prior_v1",
            "ev_population_prior_status": "not_applicable_non_ev_particle",
            "ev_population_prior_claim_level": "not_applicable_non_ev_particle",
            "ev_prior_model": None,
            "ev_prior_physical_validity": "not_applicable_non_ev_particle",
            "ev_prior_correlated_parameter_schema": _EV_PRIOR_SCHEMA,
            "ev_prior_population_bins": (),
            "ev_prior_sample_preparation_profile": str(
                sim_cfg.EV_sample_preparation_profile
            ),
            "ev_prior_selection_function_linked": False,
            "ev_prior_invalid_combination_policy": "not_applicable_non_ev_particle",
            "ev_low_RI_tail_detection_risk": "not_applicable_non_ev_particle",
            "ev_prior_gate_passed": False,
            "ev_prior_blocker_summary": "not_ev_population_target",
        }

    bins = _population_bins(particle, diagnostics, sim_cfg)
    risk = _low_ri_tail_risk(diagnostics, _nominal_refractive_index(particle))
    return {
        "ev_population_prior_schema": "ev_correlated_prior_v1",
        "ev_population_prior_status": "correlated_prior_scaffold_active",
        "ev_population_prior_claim_level": (
            "design_prior_only_not_true_population_inference"
        ),
        "ev_prior_model": "correlated_size_RI_shell_corona_prior",
        "ev_prior_physical_validity": "valid_correlated_template_no_independent_worst_case",
        "ev_prior_correlated_parameter_schema": _EV_PRIOR_SCHEMA,
        "ev_prior_population_bins": bins,
        "ev_prior_sample_preparation_profile": str(sim_cfg.EV_sample_preparation_profile),
        "ev_prior_selection_function_linked": True,
        "ev_prior_invalid_combination_policy": (
            "correlated_size_ri_shell_constraints_block_independent_worst_case"
        ),
        "ev_low_RI_tail_detection_risk": risk,
        "ev_prior_gate_passed": False,
        "ev_prior_blocker_summary": (
            "selection_function_forward_only / true_population_inference_not_run"
        ),
    }
