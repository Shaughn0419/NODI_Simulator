"""Interpretation-risk diagnostics for EV assay-control outcomes."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


CONTROL_INTERPRETATION_DIAGNOSTIC_FIELDS = (
    "control_interpretation_schema",
    "control_interpretation_status",
    "control_interpretation_claim_level",
    "control_interpretation_required_controls",
    "control_interpretation_missing_controls",
    "control_failure_interpretation_risk_table",
    "control_failure_interpretation_high_risk_controls",
    "control_failure_interpretation_gate_passed",
    "control_interpretation_blocker_summary",
)

INTERPRETATION_CONTROL_ALIASES = {
    "detergent_lysis": ("detergent_lysed_EV_sample", "detergent_lysis_control"),
    "EV_depleted": ("EV_depleted_sample", "ev_depleted_control"),
    "filtration": ("filtration_size_cutoff_control", "filtration_control"),
    "proteinase": ("proteinase_treated_sample", "proteinase_control"),
    "spike_in": (
        "spike_in_Au20",
        "spike_in_PS_or_silica",
        "spike_in_liposome",
        "generic_spike_in_control",
    ),
    "dilution": ("dilution_linearity_control", "serial_dilution_control"),
}

_RISK_TEMPLATES = {
    "detergent_lysis": {
        "expected_response": "EV_like_event_loss_or_optical_shift_after_lysis",
        "failure_modes": (
            "no_EV_like_reduction_after_lysis",
            "new_background_or_reagent_events_after_lysis",
        ),
        "interpretation_risk": (
            "lysis_failure_or_nonvesicular_artifact_can_mimic_EV_optical_signal"
        ),
        "claim_impact": "blocks_vesicle_specificity_claim",
        "recommended_followup": (
            "verify detergent blank and orthogonal vesicle marker loss"
        ),
        "risk_level": "high",
    },
    "EV_depleted": {
        "expected_response": "EV_like_event_rate_reduced_after_depletion",
        "failure_modes": (
            "EV_like_rate_not_reduced",
            "depletion_introduces_size_or_RI_bias",
        ),
        "interpretation_risk": (
            "depletion_failure_or_coisolate_bias_limits_EV_specificity"
        ),
        "claim_impact": "blocks_EV_specificity_claim",
        "recommended_followup": (
            "compare depletion efficiency against particle count and protein/lipid markers"
        ),
        "risk_level": "high",
    },
    "filtration": {
        "expected_response": "size_cutoff_changes_large_particle_or_aggregate_tail",
        "failure_modes": (
            "filtering_removes_target_EV_fraction",
            "filtering_sheds_or_adds_artifacts",
            "aggregate_tail_not_reduced",
        ),
        "interpretation_risk": (
            "filtration_artifact_can_be_misread_as_EV_size_or_RI_signature"
        ),
        "claim_impact": "blocks_size_distribution_or_population_claim",
        "recommended_followup": (
            "run filter blank and pre/post filtration recovery check"
        ),
        "risk_level": "moderate",
    },
    "proteinase": {
        "expected_response": "protein_corona_or_surface_component_shift_if_present",
        "failure_modes": (
            "no_shift_despite_expected_surface_protein",
            "global_loss_from_enzyme_buffer_or_incubation",
        ),
        "interpretation_risk": (
            "proteinase_nonresponse_does_not_prove_non_EV_optical_origin"
        ),
        "claim_impact": "limits_surface_biology_or_corona_claim",
        "recommended_followup": (
            "pair with enzyme blank and protein assay before interpreting surface shift"
        ),
        "risk_level": "moderate",
    },
    "spike_in": {
        "expected_response": "known_particle_or_vesicle_recovery_in_expected_lane",
        "failure_modes": (
            "low_spike_recovery",
            "unexpected_spike_lane_cross_reactivity",
            "spike_matrix_interaction_changes_signal",
        ),
        "interpretation_risk": (
            "spike_failure_limits_recovery_specificity_and_calibration_claims"
        ),
        "claim_impact": "blocks_recovery_or_discrimination_claim",
        "recommended_followup": (
            "run matrix-matched spike recovery and non-EV spike specificity panel"
        ),
        "risk_level": "high",
    },
    "dilution": {
        "expected_response": "event_rate_scales_with_dilution_without_shape_shift",
        "failure_modes": (
            "nonlinear_count_rate",
            "peak_shape_or_class_fraction_changes_with_dilution",
            "coincidence_or_adsorption_dominates",
        ),
        "interpretation_risk": (
            "nonlinear_dilution_can_masquerade_as_population_or_detection_limit"
        ),
        "claim_impact": "blocks_counting_or_population_abundance_claim",
        "recommended_followup": (
            "fit serial dilution slope and inspect coincidence/deadtime diagnostics"
        ),
        "risk_level": "high",
    },
}


def _configured_controls(assay_controls: Mapping[str, Any]) -> set[str]:
    value = assay_controls.get("configured_control_samples", ())
    if isinstance(value, str):
        return {value}
    try:
        return {str(item) for item in value}
    except TypeError:
        return set()


def _configured_for_family(configured: set[str], aliases: tuple[str, ...]) -> bool:
    return any(alias in configured for alias in aliases)


def _family_status(configured: set[str], family: str) -> str:
    aliases = INTERPRETATION_CONTROL_ALIASES[family]
    return (
        "configured_awaiting_measured_outcome"
        if _configured_for_family(configured, aliases)
        else "missing_control_configuration"
    )


def _compact_interpretation(risk_table: Mapping[str, Mapping[str, object]]) -> dict[str, str]:
    return {
        family: str(details["interpretation_risk"])
        for family, details in risk_table.items()
    }


def _blocker_summary(missing: tuple[str, ...]) -> str:
    blockers = ["control_outcome_data_not_ingested"]
    blockers.extend(f"{control}_missing" for control in missing)
    return " / ".join(blockers)


def build_control_interpretation_diagnostics(
    assay_controls: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    """Build conservative interpretation risks for abnormal assay controls."""
    controls = assay_controls or {}
    configured = _configured_controls(controls)
    risk_table: dict[str, dict[str, object]] = {}
    missing: list[str] = []

    for family, template in _RISK_TEMPLATES.items():
        aliases = INTERPRETATION_CONTROL_ALIASES[family]
        configured_family = _configured_for_family(configured, aliases)
        if not configured_family:
            missing.append(family)
        risk_table[family] = {
            **template,
            "control_aliases": aliases,
            "configuration_status": _family_status(configured, family),
            "measured_outcome_status": "not_ingested",
            "ev_optical_conclusion_allowed": False,
        }

    missing_tuple = tuple(missing)
    high_risk_controls = tuple(
        family
        for family, template in _RISK_TEMPLATES.items()
        if template["risk_level"] == "high"
    )
    status = (
        "risk_interpretation_scaffold_active_missing_controls"
        if missing_tuple
        else "risk_interpretation_scaffold_active_awaiting_outcomes"
    )
    return {
        "control_interpretation_schema": "control_interpretation_risk_v1",
        "control_interpretation_status": status,
        "control_interpretation_claim_level": (
            "interpretation_risk_only_no_control_outcome_claim"
        ),
        "control_interpretation_required_controls": tuple(_RISK_TEMPLATES),
        "control_interpretation_missing_controls": missing_tuple,
        "control_failure_interpretation": _compact_interpretation(risk_table),
        "control_failure_interpretation_risk_table": risk_table,
        "control_failure_interpretation_high_risk_controls": high_risk_controls,
        "control_failure_interpretation_gate_passed": False,
        "control_interpretation_blocker_summary": _blocker_summary(missing_tuple),
    }
