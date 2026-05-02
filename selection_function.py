"""Selection-function diagnostics for roadmap-43 observed-population bias."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from .data_objects import Particle, SimulationConfig


SELECTION_FUNCTION_DIAGNOSTIC_FIELDS = (
    "selection_function_schema_version",
    "selection_function_status",
    "selection_bias_claim_level",
    "selection_bias_warning",
    "selection_bias_gate_passed",
    "true_distribution_assumption",
    "observed_distribution_prediction_status",
    "P_detect_by_population_bin",
    "P_pass_QC_by_population_bin",
    "sample_prep_selection_bias",
    "channel_entry_selection_bias",
    "optical_detection_selection_bias",
    "event_qc_selection_bias",
    "classifier_rejection_selection_bias",
    "observed_distribution_predicted",
    "true_to_observed_bias_factor",
    "true_to_observed_total_bias",
    "small_EV_under_detection_bias",
    "low_RI_EV_under_detection_bias",
    "contaminant_enrichment_in_observed_events",
)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return numeric if math.isfinite(numeric) else default


def _bounded_probability(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _diameter_nm(particle: Particle) -> float:
    return float(particle.radius_m) * 2.0e9


def _first_present(row: Mapping[str, Any], keys: Sequence[str], default: Any) -> Any:
    for key in keys:
        value = row.get(key)
        if value is not None:
            return value
    return default


def _row_probability(
    row: Mapping[str, Any],
    keys: Sequence[str],
    *,
    default: float,
) -> float:
    return _bounded_probability(_as_float(_first_present(row, keys, default), default))


def _row_nonnegative_float(
    row: Mapping[str, Any],
    keys: Sequence[str],
    *,
    default: float,
) -> float:
    return max(0.0, _as_float(_first_present(row, keys, default), default))


def _population_bin_id(row: Mapping[str, Any], index: int) -> str:
    value = _first_present(
        row,
        (
            "population_bin_id",
            "bin_id",
            "particle_bin",
            "particle_name",
            "name",
        ),
        f"population_bin_{index}",
    )
    return str(value)


def _is_ev_like(row: Mapping[str, Any], bin_id: str) -> bool:
    family = str(row.get("particle_family", "")).casefold()
    label = f"{bin_id} {row.get('name', '')}".casefold()
    return family.startswith("ev") or "exosome" in family or "exosome" in label


def _aggregate_fraction(ids: set[str], distribution: Mapping[str, float]) -> float:
    return sum(distribution.get(bin_id, 0.0) for bin_id in ids)


def _underrepresented(
    ids: set[str],
    true_distribution: Mapping[str, float],
    observed_distribution: Mapping[str, float],
    *,
    ratio_threshold: float = 0.8,
) -> bool:
    true_fraction = _aggregate_fraction(ids, true_distribution)
    if true_fraction <= 0.0:
        return False
    observed_fraction = _aggregate_fraction(ids, observed_distribution)
    return observed_fraction < true_fraction * ratio_threshold


def compute_observed_distribution_correction(
    population_bins: Sequence[Mapping[str, Any]],
) -> dict[str, object]:
    """Predict observed population fractions from true priors and selection gates.

    This is a forward correction, not an inverse estimator: it shows how the
    current surrogate would distort a supplied true population before detection,
    event QC, and classifier acceptance.
    """
    if len(population_bins) == 0:
        return {
            "selection_function_schema_version": "observed_distribution_v1",
            "selection_function_status": "unavailable_empty_population_table",
            "selection_bias_claim_level": (
                "observed_distribution_surrogate_not_population_inversion"
            ),
            "selection_bias_warning": (
                "population_prior_required_no_population_inversion_performed"
            ),
            "selection_bias_gate_passed": False,
            "true_distribution_assumption": "unavailable_empty_population_table",
            "observed_distribution_prediction_status": (
                "unavailable_empty_population_table"
            ),
            "P_detect_by_population_bin": {},
            "P_pass_QC_by_population_bin": {},
            "sample_prep_selection_bias": {},
            "channel_entry_selection_bias": {},
            "optical_detection_selection_bias": {},
            "event_qc_selection_bias": {},
            "classifier_rejection_selection_bias": {},
            "observed_distribution_predicted": {},
            "true_to_observed_bias_factor": {},
            "true_to_observed_total_bias": 0.0,
            "small_EV_under_detection_bias": "unavailable_empty_population_table",
            "low_RI_EV_under_detection_bias": "unavailable_empty_population_table",
            "contaminant_enrichment_in_observed_events": (
                "unavailable_empty_population_table"
            ),
        }

    bin_ids: list[str] = []
    true_weights: dict[str, float] = {}
    selected_weights: dict[str, float] = {}
    sample_prep_probability: dict[str, float] = {}
    channel_entry_probability: dict[str, float] = {}
    detection_probability: dict[str, float] = {}
    qc_probability: dict[str, float] = {}
    classifier_accept_probability: dict[str, float] = {}
    small_ev_ids: set[str] = set()
    low_ri_ev_ids: set[str] = set()
    contaminant_ids: set[str] = set()

    for index, row in enumerate(population_bins):
        bin_id = _population_bin_id(row, index)
        bin_ids.append(bin_id)

        true_weight = _row_nonnegative_float(
            row,
            ("p_true", "true_probability", "true_fraction", "population_fraction"),
            default=1.0,
        )
        p_sample = _row_probability(
            row,
            ("P_pass_sample_prep", "P_sample_prep", "P_not_adsorbed"),
            default=1.0,
        )
        p_channel = _row_probability(
            row,
            ("P_channel_entry", "P_entry", "P_not_coincident"),
            default=1.0,
        )
        p_transport = _row_probability(
            row,
            ("P_transport", "transport_probability"),
            default=1.0,
        )
        p_detect = _row_probability(
            row,
            ("P_detect", "detection_rate", "P_detection"),
            default=0.0,
        )
        p_qc = _row_probability(
            row,
            (
                "P_pass_QC",
                "P_pass_event_QC",
                "event_qc_pass_fraction",
                "qc_pass_fraction",
            ),
            default=1.0,
        )
        p_classifier = _row_probability(
            row,
            ("P_classifier_accept", "P_not_classifier_rejected", "classifier_accept_fraction"),
            default=1.0,
        )

        true_weights[bin_id] = true_weight
        sample_prep_probability[bin_id] = p_sample
        channel_entry_probability[bin_id] = p_channel * p_transport
        detection_probability[bin_id] = p_detect
        qc_probability[bin_id] = p_qc
        classifier_accept_probability[bin_id] = p_classifier
        selected_weights[bin_id] = (
            true_weight
            * p_sample
            * p_channel
            * p_transport
            * p_detect
            * p_qc
            * p_classifier
        )

        ev_like = _is_ev_like(row, bin_id)
        diameter_nm = _as_float(row.get("diameter_nm"), math.inf)
        refractive_index = _as_float(
            _first_present(row, ("refractive_index", "RI", "n_particle"), math.inf),
            math.inf,
        )
        if ev_like and diameter_nm <= 70.0:
            small_ev_ids.add(bin_id)
        if ev_like and refractive_index <= 1.38:
            low_ri_ev_ids.add(bin_id)
        if bool(row.get("is_contaminant")) or (
            "contaminant" in str(row.get("particle_family", "")).casefold()
        ):
            contaminant_ids.add(bin_id)

    total_true_weight = sum(true_weights.values())
    if total_true_weight <= 0.0:
        true_distribution = {bin_id: 0.0 for bin_id in bin_ids}
        observed_distribution = {bin_id: 0.0 for bin_id in bin_ids}
        bias_factor: dict[str, float | None] = {bin_id: None for bin_id in bin_ids}
        prediction_status = "unavailable_zero_true_population_weight"
        gate_passed = False
    else:
        true_distribution = {
            bin_id: true_weights[bin_id] / total_true_weight for bin_id in bin_ids
        }
        total_selected_weight = sum(selected_weights.values())
        if total_selected_weight > 0.0:
            observed_distribution = {
                bin_id: selected_weights[bin_id] / total_selected_weight
                for bin_id in bin_ids
            }
            prediction_status = "observed_distribution_predicted_by_selection_surrogate"
            gate_passed = True
        else:
            observed_distribution = {bin_id: 0.0 for bin_id in bin_ids}
            prediction_status = "unavailable_zero_selected_population_weight"
            gate_passed = False
        bias_factor = {
            bin_id: (
                observed_distribution[bin_id] / true_distribution[bin_id]
                if true_distribution[bin_id] > 0.0
                else None
            )
            for bin_id in bin_ids
        }

    true_to_observed_total_bias = 0.5 * sum(
        abs(observed_distribution[bin_id] - true_distribution[bin_id])
        for bin_id in bin_ids
    )

    if _underrepresented(small_ev_ids, true_distribution, observed_distribution):
        small_ev_bias = "small_EV_bins_underrepresented_in_observed_distribution"
    elif len(small_ev_ids) > 0:
        small_ev_bias = "not_flagged_by_population_surrogate"
    else:
        small_ev_bias = "not_applicable_no_small_EV_bins"

    if _underrepresented(low_ri_ev_ids, true_distribution, observed_distribution):
        low_ri_bias = "low_RI_EV_bins_underrepresented_in_observed_distribution"
    elif len(low_ri_ev_ids) > 0:
        low_ri_bias = "not_flagged_by_population_surrogate"
    else:
        low_ri_bias = "not_applicable_no_low_RI_EV_bins"

    contaminant_true_fraction = _aggregate_fraction(contaminant_ids, true_distribution)
    contaminant_observed_fraction = _aggregate_fraction(
        contaminant_ids,
        observed_distribution,
    )
    if contaminant_true_fraction > 0.0 and (
        contaminant_observed_fraction > contaminant_true_fraction * 1.2
    ):
        contaminant_bias = "contaminant_bins_enriched_in_observed_events"
    elif len(contaminant_ids) > 0:
        contaminant_bias = "not_flagged_by_population_surrogate"
    else:
        contaminant_bias = "not_applicable_no_contaminant_bins"

    classifier_rejection_probability = {
        bin_id: 1.0 - classifier_accept_probability[bin_id] for bin_id in bin_ids
    }

    return {
        "selection_function_schema_version": "observed_distribution_v1",
        "selection_function_status": "population_selection_function_active",
        "selection_bias_claim_level": (
            "observed_distribution_surrogate_not_population_inversion"
        ),
        "selection_bias_warning": (
            "forward_selection_surrogate_only_no_population_inversion_claim"
        ),
        "selection_bias_gate_passed": gate_passed,
        "true_distribution_assumption": "input_population_prior_normalized",
        "observed_distribution_prediction_status": prediction_status,
        "P_detect_by_population_bin": detection_probability,
        "P_pass_QC_by_population_bin": qc_probability,
        "sample_prep_selection_bias": sample_prep_probability,
        "channel_entry_selection_bias": channel_entry_probability,
        "optical_detection_selection_bias": detection_probability,
        "event_qc_selection_bias": qc_probability,
        "classifier_rejection_selection_bias": classifier_rejection_probability,
        "observed_distribution_predicted": observed_distribution,
        "true_to_observed_bias_factor": bias_factor,
        "true_to_observed_total_bias": true_to_observed_total_bias,
        "small_EV_under_detection_bias": small_ev_bias,
        "low_RI_EV_under_detection_bias": low_ri_bias,
        "contaminant_enrichment_in_observed_events": contaminant_bias,
    }


def build_selection_function_diagnostics(
    particle: Particle,
    summary: Mapping[str, Any],
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """Export single-case selection-bias skeleton fields for dashboard blockers."""
    detection_rate = _bounded_probability(_as_float(summary.get("detection_rate"), 0.0))
    qc_pass_fraction = summary.get("event_qc_pass_fraction")
    qc_probability = (
        _bounded_probability(_as_float(qc_pass_fraction))
        if qc_pass_fraction is not None
        else 0.0
    )
    observed_probability = detection_rate * qc_probability
    particle_bin = str(particle.name)
    diameter_nm = _diameter_nm(particle)

    if diameter_nm <= 70.0 and detection_rate < 0.5:
        small_ev_bias = "possible_under_detection_in_current_surrogate"
    elif diameter_nm <= 70.0:
        small_ev_bias = "not_flagged_by_single_case_surrogate"
    else:
        small_ev_bias = "not_applicable_particle_bin_not_small_ev"

    is_ev_like = str(summary.get("particle_family", "")).startswith("EV") or (
        "exosome" in particle_bin.lower()
    )
    if is_ev_like and detection_rate < 0.5:
        low_ri_bias = "possible_low_RI_EV_under_detection"
    elif is_ev_like:
        low_ri_bias = "not_flagged_by_single_case_surrogate"
    else:
        low_ri_bias = "not_applicable_particle_not_ev_like"

    return {
        "selection_function_schema_version": "single_case_skeleton_v1",
        "selection_function_status": "single_case_detection_qc_skeleton_active",
        "selection_bias_claim_level": (
            "single_case_detection_qc_surrogate_not_population_inversion"
        ),
        "selection_bias_warning": (
            "selection_function_skeleton_active_population_inversion_unavailable"
        ),
        "selection_bias_gate_passed": True,
        "true_distribution_assumption": "single_particle_bin_delta_distribution",
        "observed_distribution_prediction_status": (
            "single_bin_prediction_only_no_population_correction"
        ),
        "P_detect_by_population_bin": {particle_bin: detection_rate},
        "P_pass_QC_by_population_bin": {particle_bin: qc_probability},
        "sample_prep_selection_bias": "unavailable_no_sample_prep_model",
        "channel_entry_selection_bias": (
            "not_modeled_wall_entry_loss"
            if str(sim_cfg.wall_interaction_model) == "none"
            else "wall_interaction_model_metadata_present"
        ),
        "optical_detection_selection_bias": {
            particle_bin: observed_probability,
        },
        "event_qc_selection_bias": {
            particle_bin: qc_probability,
        },
        "classifier_rejection_selection_bias": "unavailable_no_classifier_lane",
        "observed_distribution_predicted": (
            {particle_bin: 1.0} if observed_probability > 0.0 else {particle_bin: 0.0}
        ),
        "true_to_observed_bias_factor": None,
        "true_to_observed_total_bias": (
            "unavailable_population_prior_missing_single_case_only"
        ),
        "small_EV_under_detection_bias": small_ev_bias,
        "low_RI_EV_under_detection_bias": low_ri_bias,
        "contaminant_enrichment_in_observed_events": (
            "unavailable_no_contaminant_population"
        ),
    }
