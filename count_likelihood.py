"""Observed count likelihood and correction diagnostics."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from .data_objects import SimulationConfig
from .type_coerce import optional_finite_float as _as_float


COUNT_LIKELIHOOD_DIAGNOSTIC_FIELDS = (
    "count_likelihood_model",
    "count_likelihood_status",
    "count_likelihood_claim_level",
    "observed_count",
    "observed_count_source",
    "expected_count_for_likelihood",
    "count_log_likelihood",
    "count_deviance",
    "false_positive_expected_count",
    "false_negative_expected_count",
    "false_positive_corrected_count",
    "false_negative_corrected_count",
    "count_likelihood_blank_false_positive_rate_Hz",
    "count_likelihood_conditional_detection_rate",
    "count_likelihood_gate_passed",
    "count_likelihood_blocker_summary",
)

def _as_count(value: Any) -> int:
    numeric = _as_float(value, 0.0)
    if numeric is None:
        return 0
    return max(0, int(round(numeric)))


def _blocker_summary(blockers: list[str]) -> str:
    return "none" if not blockers else " / ".join(blockers)


def log_likelihood_counts(
    observed_count: int | float,
    expected_count: int | float,
) -> float:
    """
    Return the Poisson log-likelihood for an observed count.

    `expected_count == 0` is handled exactly: observing zero has log-likelihood
    0, while observing any positive count is impossible under the model.
    """
    observed = _as_count(observed_count)
    expected = _as_float(expected_count, 0.0)
    if expected is None or expected < 0.0:
        raise ValueError("expected_count must be finite and non-negative")
    if expected == 0.0:
        return 0.0 if observed == 0 else float("-inf")
    return float(observed * math.log(expected) - expected - math.lgamma(observed + 1))


def _poisson_deviance(observed_count: int, expected_count: float) -> float:
    if expected_count <= 0.0:
        return 0.0 if observed_count == 0 else float("inf")
    if observed_count == 0:
        return float(2.0 * expected_count)
    return float(
        2.0
        * (
            observed_count * math.log(observed_count / expected_count)
            - (observed_count - expected_count)
        )
    )


def build_count_likelihood_diagnostics(
    summary: Mapping[str, Any],
    count_model: Mapping[str, Any],
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """Build observed-count likelihood diagnostics from count-model outputs."""
    observed_count = _as_count(summary.get("n_detected", 0))
    observed_source = "summary_n_detected_after_event_qc"
    expected_count = _as_float(count_model.get("predicted_counts_in_window"))
    observation_window_s = _as_float(
        count_model.get("count_observation_window_s"),
        float(sim_cfg.total_time_s),
    )
    blank_fp_rate_hz = max(
        _as_float(count_model.get("blank_false_positive_rate_Hz"), 0.0) or 0.0,
        0.0,
    )
    conditional_detection_rate = _as_float(
        count_model.get("conditional_detection_rate"),
        0.0,
    )
    missed_rate_hz = max(_as_float(count_model.get("missed_event_rate_Hz"), 0.0) or 0.0, 0.0)
    false_positive_expected = blank_fp_rate_hz * float(observation_window_s or 0.0)
    false_negative_expected = missed_rate_hz * float(observation_window_s or 0.0)
    fp_corrected = max(float(observed_count) - false_positive_expected, 0.0)
    fn_corrected = fp_corrected + false_negative_expected

    blockers: list[str] = []
    if expected_count is None:
        blockers.append("expected_count_unavailable")
    if sim_cfg.number_concentration_m3 is None:
        blockers.append("number_concentration_missing")
    if blank_fp_rate_hz <= 0.0:
        blockers.append("blank_false_positive_rate_missing")
    if float(sim_cfg.count_dead_time_s) <= 0.0:
        blockers.append("dead_time_metadata_missing_or_zero")
    else:
        blockers.append("dead_time_calibration_not_empirical")
    if str(count_model.get("count_prediction_uncertainty_status")) != "propagated":
        blockers.append("count_uncertainty_not_propagated")

    if expected_count is None:
        log_likelihood = None
        deviance = None
        status = "unavailable_without_count_prediction"
        claim_level = "exploratory_no_count_prediction"
    else:
        log_likelihood = log_likelihood_counts(observed_count, expected_count)
        deviance = _poisson_deviance(observed_count, expected_count)
        status = "poisson_log_likelihood_active"
        claim_level = (
            "exploratory_poisson_likelihood_missing_calibration"
            if blockers
            else "exploratory_poisson_likelihood_surrogate"
        )

    return {
        "count_likelihood_model": "poisson_observed_count_surrogate",
        "count_likelihood_status": status,
        "count_likelihood_claim_level": claim_level,
        "observed_count": observed_count,
        "observed_count_source": observed_source,
        "expected_count_for_likelihood": expected_count,
        "count_log_likelihood": log_likelihood,
        "count_deviance": deviance,
        "false_positive_expected_count": false_positive_expected,
        "false_negative_expected_count": false_negative_expected,
        "false_positive_corrected_count": fp_corrected,
        "false_negative_corrected_count": fn_corrected,
        "count_likelihood_blank_false_positive_rate_Hz": blank_fp_rate_hz,
        "count_likelihood_conditional_detection_rate": conditional_detection_rate,
        "count_likelihood_gate_passed": expected_count is not None and not blockers,
        "count_likelihood_blocker_summary": _blocker_summary(blockers),
    }
