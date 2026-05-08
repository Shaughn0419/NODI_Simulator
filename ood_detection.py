"""Out-of-distribution rejection diagnostics for particle classification."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from .data_objects import Particle, SimulationConfig
from .type_coerce import finite_float as _as_float


OOD_DIAGNOSTIC_FIELDS = (
    "ood_detection_model",
    "ood_detection_status",
    "ood_detection_claim_level",
    "ood_feature_schema",
    "ood_feature_vector",
    "ood_mahalanobis_distance",
    "ood_one_class_density_score",
    "ood_conformal_p_value",
    "ood_rejection_threshold",
    "unknown_particle_flag",
    "unknown_particle_reason",
    "classifier_rejection_rate",
    "classifier_rejection_policy",
    "EV_contaminant_hard_classification_allowed",
    "EV_contaminant_classifier_claim_level",
    "ood_gate_passed",
    "ood_blocker_summary",
)

def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _particle_family(particle: Particle) -> str:
    material = str(particle.material_key or "").casefold()
    name = str(particle.name).casefold()
    if material in {"gold", "silver"} or "gold" in name or "silver" in name:
        return "standard_metal"
    if "exosome" in name or "ev" in name or str(particle.model_type) == "mie_core_shell":
        return "EV_like"
    if "contaminant" in name or "dust" in name or "aggregate" in name:
        return "contaminant_like"
    return "unlabeled_particle"


def _blocker_summary(blockers: list[str]) -> str:
    return "none" if not blockers else " / ".join(blockers)


def _unknown_reason(
    *,
    distance: float,
    density_score: float,
    artifact_risk: float,
    overlap: float,
    threshold: float,
) -> str:
    if density_score < threshold:
        return "density_below_one_class_threshold"
    if distance >= 3.0:
        return "mahalanobis_distance_outside_surrogate_envelope"
    if artifact_risk >= 0.5:
        return "event_artifact_risk_high"
    if overlap >= 0.8:
        return "ev_contaminant_feature_overlap_high"
    return "none"


def build_ood_detection_diagnostics(
    particle: Particle,
    summary: Mapping[str, Any],
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """
    Build OOD/rejection diagnostics from already-exported batch features.

    This P1 route is an explicit reject-option interface, not a trained
    classifier. Unknown cases are rejected instead of being forced into EV or
    contaminant labels.
    """
    detection_rate = _clamp01(_as_float(summary.get("detection_rate"), 0.0))
    stable_rate = _clamp01(
        _as_float(summary.get("stable_detection_rate"), detection_rate)
    )
    margin_z = max(_as_float(summary.get("mean_peak_margin_z"), 0.0), 0.0)
    artifact_risk = _clamp01(_as_float(summary.get("event_artifact_risk_score"), 0.0))
    overlap = _clamp01(
        _as_float(summary.get("EV_to_contaminant_signal_overlap"), 0.0)
    )
    phase_flip = _clamp01(_as_float(summary.get("phase_flip_fraction"), 0.0))
    family = _particle_family(particle)

    feature_vector = {
        "detection_rate": detection_rate,
        "stable_detection_rate": stable_rate,
        "mean_peak_margin_z": margin_z,
        "event_artifact_risk_score": artifact_risk,
        "EV_to_contaminant_signal_overlap": overlap,
        "phase_flip_fraction": phase_flip,
    }
    center = {
        "detection_rate": 0.8,
        "stable_detection_rate": 0.75,
        "mean_peak_margin_z": 3.0,
        "event_artifact_risk_score": 0.1,
        "EV_to_contaminant_signal_overlap": 0.25 if family == "EV_like" else 0.0,
        "phase_flip_fraction": 0.05,
    }
    scale = {
        "detection_rate": 0.25,
        "stable_detection_rate": 0.25,
        "mean_peak_margin_z": 2.0,
        "event_artifact_risk_score": 0.2,
        "EV_to_contaminant_signal_overlap": 0.25,
        "phase_flip_fraction": 0.2,
    }
    distance_sq = sum(
        ((feature_vector[name] - center[name]) / scale[name]) ** 2
        for name in feature_vector
    )
    distance = math.sqrt(distance_sq)
    density_score = math.exp(-0.5 * distance_sq)
    conformal_p_value = _clamp01(density_score)
    threshold = 0.05
    reason = _unknown_reason(
        distance=distance,
        density_score=density_score,
        artifact_risk=artifact_risk,
        overlap=overlap,
        threshold=threshold,
    )
    unknown = reason != "none"
    blockers = [
        "ood_training_reference_set_missing",
        "classifier_held_out_validation_missing",
    ]
    if unknown:
        blockers.append("unknown_particle_rejected_not_hard_classified")

    return {
        "ood_detection_model": (
            "mahalanobis_density_conformal_rejection_surrogate"
        ),
        "ood_detection_status": (
            "surrogate_reject_option_active_no_trained_classifier"
        ),
        "ood_detection_claim_level": (
            "exploratory_ood_rejection_not_trained_classifier"
        ),
        "ood_feature_schema": (
            "detection_rate,stable_detection_rate,mean_peak_margin_z,"
            "event_artifact_risk_score,EV_to_contaminant_signal_overlap,"
            "phase_flip_fraction"
        ),
        "ood_feature_vector": feature_vector,
        "ood_mahalanobis_distance": distance,
        "ood_one_class_density_score": density_score,
        "ood_conformal_p_value": conformal_p_value,
        "ood_rejection_threshold": threshold,
        "unknown_particle_flag": unknown,
        "unknown_particle_reason": reason,
        "classifier_rejection_rate": 1.0 if unknown else 0.0,
        "classifier_rejection_policy": (
            "reject_unknown_instead_of_forced_EV_or_contaminant_label"
        ),
        "EV_contaminant_hard_classification_allowed": False,
        "EV_contaminant_classifier_claim_level": (
            "blocked_until_trained_classifier_and_ood_rejection_calibrated"
        ),
        "ood_gate_passed": not unknown,
        "ood_blocker_summary": _blocker_summary(blockers),
    }
