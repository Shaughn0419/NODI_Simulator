"""Next-experiment and value-of-information diagnostics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .calibration_plan_advisor import build_calibration_plan_advisor
from .type_coerce import clamp01 as _clamp01
from .type_coerce import finite_float as _as_float


EXPERIMENTAL_DESIGN_ADVISOR_FIELDS = (
    "experimental_design_advisor_status",
    "experimental_design_advisor_claim_level",
    "next_experiment_priority",
    "next_experiment_priority_bucket",
    "next_experiment_priority_reason",
    "next_experiment_priority_order",
    "next_experiment_reason_codes",
    "value_of_information_score",
    "value_of_information_score_components",
    "blocker_pressure_score",
    "sensitivity_pressure_score",
    "model_disagreement_pressure_score",
    "calibration_gap_pressure_score",
    "experimental_design_advisor_gate_passed",
)

_SENSITIVITY_STATUS_TOKENS = (
    "sensitive",
    "high_sensitivity",
    "caution",
    "requires_joint_fullwave",
    "fullwave_required",
)

def _text_blob(diagnostics: Mapping[str, Any]) -> str:
    parts: list[str] = []
    for key, value in diagnostics.items():
        if value is None or value is False:
            continue
        if isinstance(value, Mapping) or hasattr(value, "shape"):
            continue
        if isinstance(value, (list, tuple, set)):
            scalar_items = [
                str(item)
                for item in value
                if item is not None
                and not isinstance(item, Mapping)
                and not hasattr(item, "shape")
            ]
            value_text = " ".join(scalar_items[:16])
        else:
            value_text = str(value)
        if value_text.casefold() in {"", "none", "false", "pass"}:
            continue
        parts.append(f"{key}={value_text}")
    return " / ".join(parts).casefold()


def _sensitivity_pressure(diagnostics: Mapping[str, Any], text: str) -> float:
    numeric_candidates = (
        _as_float(diagnostics.get("position_sensitivity_score"), 0.0),
        _as_float(diagnostics.get("event_artifact_risk_score"), 0.0),
        _as_float(diagnostics.get("fluidic_practicality_penalty"), 0.0),
        _as_float(diagnostics.get("nodi_thermal_contamination_proxy"), 0.0) / 10.0,
        _as_float(diagnostics.get("phase_flip_fraction"), 0.0),
    )
    token_pressure = 0.6 if any(token in text for token in _SENSITIVITY_STATUS_TOKENS) else 0.0
    return _clamp01(max((*numeric_candidates, token_pressure)))


def _model_disagreement_pressure(diagnostics: Mapping[str, Any], text: str) -> float:
    flags = (
        bool(diagnostics.get("route_disagreement_flag", False)),
        bool(diagnostics.get("physics_model_disagreement_flag", False)),
        "model_disagreement" in text,
        "route_disagreement" in text,
        "requires_joint_fullwave" in text,
        "fullwave_required" in text,
    )
    return 1.0 if any(flags) else 0.0


def _as_str_sequence(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [str(item) for item in value]


def _calibration_gap_pressure(diagnostics: Mapping[str, Any], text: str) -> float:
    gap = 0.0
    if not bool(diagnostics.get("calibrated_quantitative_unlocked", False)):
        gap = max(gap, 0.5)
    if not bool(diagnostics.get("bayesian_posterior_available", False)):
        gap = max(gap, 0.4)
    if "missing" in text or "not_calibrated" in text or "not_available" in text:
        gap = max(gap, 0.7)
    if "detector_unit_chain" in text or "standard_particle" in text:
        gap = max(gap, 0.8)
    return _clamp01(gap)


def _priority_bucket(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.35:
        return "medium"
    if score > 0.0:
        return "low"
    return "none"


def _fallback_priority(
    *,
    sensitivity_pressure: float,
    disagreement_pressure: float,
) -> tuple[str | None, str]:
    if disagreement_pressure >= 0.7:
        return "model_disagreement_resolution_review", "model_disagreement_pressure"
    if sensitivity_pressure >= 0.5:
        return "robustness_sensitivity_sweep", "sensitivity_pressure"
    return None, "no_high_value_experiment_identified"


def build_experimental_design_advisor(
    diagnostics: Mapping[str, Any],
) -> dict[str, object]:
    """Build deterministic next-experiment and VOI diagnostics."""
    calibration_plan = build_calibration_plan_advisor(diagnostics)
    required_experiments = _as_str_sequence(
        calibration_plan.get("required_calibration_experiments", ())
    )
    reason_codes = _as_str_sequence(
        calibration_plan.get("calibration_plan_reason_codes", ())
    )
    text = _text_blob(diagnostics)
    blocker_pressure = _clamp01(len(reason_codes) / 5.0)
    sensitivity_pressure = _sensitivity_pressure(diagnostics, text)
    disagreement_pressure = _model_disagreement_pressure(diagnostics, text)
    calibration_gap_pressure = _calibration_gap_pressure(diagnostics, text)
    score = _clamp01(
        0.35 * blocker_pressure
        + 0.25 * sensitivity_pressure
        + 0.20 * disagreement_pressure
        + 0.20 * calibration_gap_pressure
    )

    priority = required_experiments[0] if required_experiments else None
    priority_reason = reason_codes[0] if reason_codes else "calibration_plan_empty"
    if priority is None:
        priority, priority_reason = _fallback_priority(
            sensitivity_pressure=sensitivity_pressure,
            disagreement_pressure=disagreement_pressure,
        )

    status = (
        "next_experiment_recommended"
        if priority is not None
        else "no_high_value_experiment_identified"
    )

    return {
        "experimental_design_advisor_status": status,
        "experimental_design_advisor_claim_level": (
            "next_experiment_guidance_only_does_not_unlock_claims"
        ),
        "next_experiment_priority": priority,
        "next_experiment_priority_bucket": _priority_bucket(score),
        "next_experiment_priority_reason": priority_reason,
        "next_experiment_priority_order": required_experiments,
        "next_experiment_reason_codes": reason_codes,
        "value_of_information_score": score,
        "value_of_information_score_components": {
            "blocker_pressure": blocker_pressure,
            "sensitivity_pressure": sensitivity_pressure,
            "model_disagreement_pressure": disagreement_pressure,
            "calibration_gap_pressure": calibration_gap_pressure,
        },
        "blocker_pressure_score": blocker_pressure,
        "sensitivity_pressure_score": sensitivity_pressure,
        "model_disagreement_pressure_score": disagreement_pressure,
        "calibration_gap_pressure_score": calibration_gap_pressure,
        "experimental_design_advisor_gate_passed": False,
    }
