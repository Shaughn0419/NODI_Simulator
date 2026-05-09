"""Package-local objective-panel candidate refinement smoke lane."""

from __future__ import annotations

from copy import copy
from collections.abc import Sequence
from dataclasses import replace

from .data_objects import OpticalSystem, Particle, SimulationConfig
from .optical_exposure_safety import build_optical_exposure_safety_diagnostics
from .optical_hardware_profiles import (
    OBJECTIVE_PROFILES,
    build_objective_profile_diagnostics,
    get_objective_profile,
)


DEFAULT_OBJECTIVE_PANEL_IDS = (
    "current_control",
    "moderate_upgrade",
    "high_NA_test",
    "large_spot_control",
)

OBJECTIVE_PANEL_DIAGNOSTIC_FIELDS = (
    "objective_panel_status",
    "objective_panel_claim_level",
    "objective_panel_candidate_count",
    "objective_panel_candidate_ids",
    "objective_panel_recommendation",
    "objective_panel_recommended_score",
    "objective_panel_recommendation_reason",
    "objective_panel_blocker_summary",
    "objective_panel_records",
)


def _candidate_optical(
    optical: OpticalSystem,
    objective_id: str,
) -> OpticalSystem:
    profile = get_objective_profile(objective_id)
    return replace(
        optical,
        illumination_NA=float(profile.illumination_NA),
        NA_collection=(
            float(profile.collection_NA)
            if profile.collection_NA is not None
            else float(optical.NA_collection)
        ),
        illumination_beam_waist_x_m=None,
        illumination_beam_waist_y_m=None,
        illumination_beam_waist_z_m=None,
    )


def _candidate_config(
    sim_cfg: SimulationConfig,
    objective_id: str,
) -> SimulationConfig:
    candidate_cfg = copy(sim_cfg)
    candidate_cfg.objective_candidate_id = objective_id
    return candidate_cfg


def _component_scores(record: dict[str, object]) -> dict[str, float]:
    lockin_score = 1.0 if record.get("lockin_bandwidth_margin") == "ok" else 0.45
    exposure_risk = str(record.get("ev_photodamage_risk_band"))
    exposure_score = {
        "low": 1.0,
        "medium": 0.45,
        "high": 0.0,
        "unknown_missing_probe_power_metadata": 0.55,
    }.get(exposure_risk, 0.55)
    working_distance_status = str(record.get("working_distance_compatibility"))
    working_distance_score = {
        "declared_not_measured_against_chip": 0.90,
        "not_configured_claim_blocker": 0.70,
        "not_practical": 0.0,
    }.get(working_distance_status, 0.50)
    position_sensitivity = float(record.get("position_sensitivity_score") or 0.0)
    position_score = max(0.0, 1.0 - 0.35 * position_sensitivity)
    return {
        "objective_panel_lockin_score": lockin_score,
        "objective_panel_exposure_score": exposure_score,
        "objective_panel_working_distance_score": working_distance_score,
        "objective_panel_position_score": position_score,
    }


def _objective_panel_score(record: dict[str, object]) -> float:
    components = _component_scores(record)
    return float(
        0.35 * components["objective_panel_lockin_score"]
        + 0.35 * components["objective_panel_exposure_score"]
        + 0.20 * components["objective_panel_working_distance_score"]
        + 0.10 * components["objective_panel_position_score"]
    )


def _recommendation_reason(record: dict[str, object]) -> str:
    reasons = [
        f"lockin={record.get('lockin_bandwidth_margin')}",
        f"exposure={record.get('ev_photodamage_risk_band')}",
        f"working_distance={record.get('working_distance_compatibility')}",
        f"position_sensitivity={float(record.get('position_sensitivity_score') or 0.0):.3f}",
    ]
    return " / ".join(reasons)


def evaluate_objective_panel(
    particle: Particle,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    intrinsic: dict,
    *,
    candidate_ids: Sequence[str] = DEFAULT_OBJECTIVE_PANEL_IDS,
) -> dict[str, object]:
    """Evaluate objective candidates without changing the main simulation path."""
    records: list[dict[str, object]] = []
    for objective_id in candidate_ids:
        if objective_id not in OBJECTIVE_PROFILES:
            continue
        candidate_optical = _candidate_optical(optical, objective_id)
        candidate_cfg = _candidate_config(sim_cfg, objective_id)
        objective_diagnostics = build_objective_profile_diagnostics(
            candidate_optical,
            candidate_cfg,
        )
        exposure_diagnostics = build_optical_exposure_safety_diagnostics(
            particle,
            candidate_optical,
            candidate_cfg,
            intrinsic,
        )
        record = {
            **objective_diagnostics,
            **exposure_diagnostics,
        }
        component_scores = _component_scores(record)
        record.update(component_scores)
        record["objective_panel_score"] = _objective_panel_score(record)
        records.append(record)

    if not records:
        return {
            "objective_panel_status": "unavailable_no_known_candidates",
            "objective_panel_claim_level": (
                "candidate_refinement_surrogate_not_hardware_calibration"
            ),
            "objective_panel_candidate_count": 0,
            "objective_panel_candidate_ids": [],
            "objective_panel_recommendation": None,
            "objective_panel_recommended_score": None,
            "objective_panel_recommendation_reason": "no_known_candidates",
            "objective_panel_blocker_summary": "no_known_objective_candidates",
            "objective_panel_records": [],
        }

    ranked = sorted(
        records,
        key=lambda item: float(item["objective_panel_score"]),
        reverse=True,
    )
    best = ranked[0]
    return {
        "objective_panel_status": "synthetic_candidate_refinement_active",
        "objective_panel_claim_level": (
            "candidate_refinement_surrogate_not_hardware_calibration"
        ),
        "objective_panel_candidate_count": len(records),
        "objective_panel_candidate_ids": [
            str(record["objective_candidate_id"]) for record in records
        ],
        "objective_panel_recommendation": best["objective_candidate_id"],
        "objective_panel_recommended_score": float(best["objective_panel_score"]),
        "objective_panel_recommendation_reason": _recommendation_reason(best),
        "objective_panel_blocker_summary": (
            "working_distance_not_measured / BFP_mapping_not_measured / "
            "exposure_safety_not_calibrated"
        ),
        "objective_panel_records": ranked,
    }
