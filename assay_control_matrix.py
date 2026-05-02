"""P0 assay-control matrix skeleton diagnostics."""

from __future__ import annotations

from collections.abc import Iterable


REQUIRED_CONTROL_SAMPLES = (
    "buffer_blank",
    "medium_blank",
    "EV_depleted_sample",
    "detergent_lysed_EV_sample",
    "proteinase_treated_sample",
    "spike_in_Au20",
    "spike_in_PS_or_silica",
    "spike_in_liposome",
    "dilution_linearity_control",
    "high_concentration_coincidence_control",
)

ASSAY_CONTROL_DIAGNOSTIC_FIELDS = (
    "required_control_samples",
    "configured_control_samples",
    "missing_control_samples",
    "control_expected_signal_pattern",
    "control_failure_interpretation",
    "control_priority",
    "assay_control_readiness_score",
    "assay_control_status",
    "assay_control_claim_level",
    "assay_control_gate_passed",
)


def build_assay_control_matrix_diagnostics(
    configured_controls: Iterable[str] | None = None,
) -> dict[str, object]:
    """Export required EV assay controls and claim blockers."""
    configured = tuple(sorted(set(configured_controls or ())))
    configured_set = set(configured)
    missing = tuple(
        control
        for control in REQUIRED_CONTROL_SAMPLES
        if control not in configured_set
    )
    readiness = 1.0 - (len(missing) / len(REQUIRED_CONTROL_SAMPLES))
    expected_pattern = {
        "buffer_blank": "no_particle_events_above_blank_false_positive_rate",
        "medium_blank": "no_medium_background_events_above_blank_rate",
        "EV_depleted_sample": "reduced_EV_like_event_rate",
        "detergent_lysed_EV_sample": "loss_or_shift_of_EV_like_events",
        "proteinase_treated_sample": "protein_corona_sensitive_shift_if_present",
        "spike_in_Au20": "positive_scattering_anchor_recovery",
        "spike_in_PS_or_silica": "non_EV_particle_recovery_and_specificity_check",
        "spike_in_liposome": "vesicle_like_non_EV_control_response",
        "dilution_linearity_control": "event_rate_scales_with_dilution",
        "high_concentration_coincidence_control": "doublet_or_deadtime_risk_visible",
    }
    failure_interpretation = {
        "buffer_blank": "blank_events_limit_false_positive_claim",
        "medium_blank": "medium_background_limits_specificity_claim",
        "EV_depleted_sample": "depletion_failure_limits_EV_specificity_claim",
        "detergent_lysed_EV_sample": "lysis_nonresponse_limits_vesicle_claim",
        "proteinase_treated_sample": "proteinase_nonresponse_limits_surface_claim",
        "spike_in_Au20": "anchor_failure_limits_calibrated_scattering_claim",
        "spike_in_PS_or_silica": "spike_failure_limits_non_EV_discrimination_claim",
        "spike_in_liposome": "liposome_control_needed_for_vesicle_specificity",
        "dilution_linearity_control": "nonlinear_rate_limits_count_claim",
        "high_concentration_coincidence_control": "coincidence_limits_population_claim",
    }
    priority = {
        "buffer_blank": "P0_required",
        "medium_blank": "P0_required",
        "EV_depleted_sample": "P0_required",
        "detergent_lysed_EV_sample": "P0_required",
        "proteinase_treated_sample": "P1_recommended",
        "spike_in_Au20": "P0_required",
        "spike_in_PS_or_silica": "P1_recommended",
        "spike_in_liposome": "P1_recommended",
        "dilution_linearity_control": "P0_required",
        "high_concentration_coincidence_control": "P0_required",
    }
    gate_passed = not missing
    return {
        "required_control_samples": REQUIRED_CONTROL_SAMPLES,
        "configured_control_samples": configured,
        "missing_control_samples": missing,
        "control_expected_signal_pattern": expected_pattern,
        "control_failure_interpretation": failure_interpretation,
        "control_priority": priority,
        "assay_control_readiness_score": readiness,
        "assay_control_status": (
            "complete_control_matrix_configured"
            if gate_passed
            else "blocked_missing_control_samples"
        ),
        "assay_control_claim_level": (
            "control_matrix_ready_for_EV_specificity_interpretation"
            if gate_passed
            else "control_matrix_skeleton_required_before_specificity_claim"
        ),
        "assay_control_gate_passed": gate_passed,
    }
