"""Population-inference likelihood scaffold and claim blocker."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .type_coerce import blocker_summary as _blocker_summary

from .type_coerce import optional_finite_float as _as_float


POPULATION_INFERENCE_DIAGNOSTIC_FIELDS = (
    "population_inference_schema",
    "population_inference_status",
    "population_inference_claim_level",
    "population_inference_likelihood_shape",
    "population_inference_model_family",
    "population_inference_required_inputs",
    "population_inference_missing_inputs",
    "population_inference_population_bins",
    "population_inference_observed_event_count",
    "population_inference_observed_count_source",
    "population_inference_log_likelihood_available",
    "population_inference_log_likelihood_value",
    "population_inference_selection_correction_available",
    "population_inference_selection_bias_claim_level",
    "population_inference_true_distribution_estimate",
    "population_inference_posterior_available",
    "population_inference_gate_passed",
    "population_inference_blocker_summary",
)

_REQUIRED_INPUTS = (
    "observed_event_count",
    "population_bins",
    "selection_correction",
    "count_log_likelihood",
    "population_inference_sampler",
)

_LIKELIHOOD_SHAPE = {
    "observed_counts": (
        "y_i ~ Poisson(N_total * pi_true_i * selection_i + blank_i)"
    ),
    "selection_factor": (
        "selection_i = P_prep_i * P_channel_i * P_transport_i * "
        "P_detect_i * P_event_QC_i * P_classifier_accept_i"
    ),
    "blocked_output": (
        "pi_true posterior not estimated until calibrated selection matrix "
        "and inference sampler exist"
    ),
}

def _as_count(
    diagnostics: Mapping[str, Any],
) -> tuple[int | None, str]:
    for key in (
        "observed_count",
        "trace_detected_event_count",
        "accepted_event_count",
        "n_detected",
    ):
        value = diagnostics.get(key)
        numeric = _as_float(value)
        if numeric is not None:
            return max(0, int(round(numeric))), key
    n_events = _as_float(diagnostics.get("n_events"))
    detection_rate = _as_float(diagnostics.get("detection_rate"))
    if n_events is not None and detection_rate is not None:
        return max(0, int(round(n_events * detection_rate))), (
            "n_events_times_detection_rate_surrogate"
        )
    return None, "unavailable"


def _population_bins_from_sequence(value: Sequence[Any]) -> list[str]:
    bins: list[str] = []
    for index, item in enumerate(value):
        if isinstance(item, Mapping):
            bin_id = item.get("population_bin_id", item.get("particle_bin"))
            bins.append(str(bin_id) if bin_id is not None else f"population_bin_{index}")
        else:
            bins.append(str(item))
    return bins


def _population_bins(diagnostics: Mapping[str, Any]) -> list[str]:
    for key in (
        "observed_distribution_predicted",
        "P_detect_by_population_bin",
        "P_pass_QC_by_population_bin",
        "population_bins",
        "particle_population_table",
    ):
        value = diagnostics.get(key)
        if isinstance(value, Mapping) and value:
            return [str(item) for item in value.keys()]
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and value:
            return _population_bins_from_sequence(value)
    return []


def _has_mapping(value: Any) -> bool:
    return isinstance(value, Mapping) and bool(value)


def build_population_inference_scaffold(
    diagnostics: Mapping[str, Any],
) -> dict[str, object]:
    """Define the population-inference likelihood shape without inverting it."""
    observed_count, observed_count_source = _as_count(diagnostics)
    population_bins = _population_bins(diagnostics)
    count_log_likelihood = diagnostics.get("count_log_likelihood")
    count_log_likelihood_available = count_log_likelihood is not None
    selection_correction_available = _has_mapping(
        diagnostics.get("true_to_observed_bias_factor")
    )

    blockers = ["true_population_inversion_not_implemented"]
    if observed_count is None:
        blockers.append("observed_event_count_missing")
    if not population_bins:
        blockers.append("population_bins_missing")
    if not selection_correction_available:
        blockers.append("selection_correction_missing")
    if not count_log_likelihood_available:
        blockers.append("count_log_likelihood_missing")
    if bool(diagnostics.get("unknown_particle_flag", False)):
        blockers.append("unknown_events_require_rejection_model")
    blockers.append("population_inference_sampler_not_implemented")

    status = (
        "likelihood_shape_defined_claim_blocked"
        if observed_count is not None and population_bins
        else "schema_only_missing_inputs"
    )
    missing_inputs = [
        required
        for required, missing in (
            ("observed_event_count", observed_count is None),
            ("population_bins", not population_bins),
            ("selection_correction", not selection_correction_available),
            ("count_log_likelihood", not count_log_likelihood_available),
            ("population_inference_sampler", True),
        )
        if missing
    ]

    return {
        "population_inference_schema": "population_inference_likelihood_scaffold_v1",
        "population_inference_status": status,
        "population_inference_claim_level": (
            "likelihood_shape_only_no_population_inversion_claim"
        ),
        "population_inference_likelihood_shape": dict(_LIKELIHOOD_SHAPE),
        "population_inference_model_family": (
            "selection_corrected_poisson_mixture_scaffold"
        ),
        "population_inference_required_inputs": _REQUIRED_INPUTS,
        "population_inference_missing_inputs": tuple(missing_inputs),
        "population_inference_population_bins": tuple(population_bins),
        "population_inference_observed_event_count": observed_count,
        "population_inference_observed_count_source": observed_count_source,
        "population_inference_log_likelihood_available": (
            count_log_likelihood_available
        ),
        "population_inference_log_likelihood_value": count_log_likelihood,
        "population_inference_selection_correction_available": (
            selection_correction_available
        ),
        "population_inference_selection_bias_claim_level": diagnostics.get(
            "selection_bias_claim_level",
            "unavailable_no_selection_function",
        ),
        "population_inference_true_distribution_estimate": None,
        "population_inference_posterior_available": False,
        "population_inference_gate_passed": False,
        "population_inference_blocker_summary": _blocker_summary(blockers),
    }
