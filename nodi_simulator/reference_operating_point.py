"""Package-local reference design and operating-point diagnostics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from .data_objects import Channel, OpticalSystem, SimulationConfig


REFERENCE_OPERATING_POINT_DIAGNOSTIC_FIELDS = (
    "reference_design_intensity_proxy",
    "reference_design_amplitude_proxy",
    "reference_design_roi_fraction",
    "reference_design_width_rank_metric",
    "reference_design_validity",
    "I_ref_proxy",
    "reference_shot_noise_proxy",
    "reference_total_noise_proxy",
    "reference_saturation_margin_proxy",
    "reference_operating_band",
    "reference_operating_point_status",
    "reference_operating_point_claim_level",
    "reference_na_edge_policy",
    "reference_na_edge_rolloff_factor",
    "reference_na_edge_status",
)


def _finite_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if np.isfinite(parsed) else default


def _na_edge_status_and_factor(
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    reference: Mapping[str, Any],
) -> tuple[str, float]:
    diff_ratio = _finite_float(
        reference.get("na_cutoff_diff_ratio"),
        float(optical.wavelength_m) / max(float(channel.width_m), 1e-30),
    )
    na_ratio = _finite_float(
        reference.get("na_cutoff_na_ratio"),
        float(optical.NA_collection),
    )
    if str(sim_cfg.reference_na_edge_policy) == "hard_guardrail":
        outside = bool(reference.get("na_cutoff_condition_met", diff_ratio > na_ratio))
        return ("outside" if outside else "inside", 0.0 if outside else 1.0)

    rolloff_width = max(
        np.sin(np.deg2rad(float(sim_cfg.reference_na_rolloff_width_deg))),
        1e-12,
    )
    margin = na_ratio - diff_ratio
    if margin >= rolloff_width:
        return "inside", 1.0
    if margin <= 0.0:
        return "outside", 0.0
    return "near_edge", float(np.clip(margin / rolloff_width, 0.0, 1.0))


def _operating_band(
    *,
    A_ref: float,
    I_ref: float,
    electronics_noise_proxy: float,
    shot_noise_proxy: float,
    total_noise_proxy: float,
    na_edge_status: str,
    sim_cfg: SimulationConfig,
) -> str:
    if A_ref <= 0.0 or I_ref <= 0.0 or na_edge_status == "outside":
        return "reference_too_weak"
    if str(sim_cfg.detector_dynamic_range_model) != "not_applied" and I_ref >= 1.0:
        return "reference_saturation_risk"
    if (
        str(sim_cfg.rin_noise_model) != "not_applied"
        or str(sim_cfg.transmitted_leakage_model) != "not_applied"
        or str(sim_cfg.stray_light_model) != "not_applied"
    ):
        return "rin_or_leakage_risk"
    if shot_noise_proxy > 0.0 and shot_noise_proxy >= max(electronics_noise_proxy, 1e-30):
        return "shot_noise_limited_no_gain"
    if electronics_noise_proxy > 0.0 and total_noise_proxy > 0.0:
        return "electronics_noise_limited_useful"
    return "balanced"


def build_reference_operating_point_diagnostics(
    reference: Mapping[str, Any],
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """Build relative reference-strength and NA-edge operating diagnostics."""
    A_ref = abs(complex(reference.get("E_ref_complex", reference.get("A_ref", 0.0))))
    I_ref = float(A_ref**2)
    roi_fraction = reference.get(
        "tsuyama_bfp_roi_fraction_of_total_diffraction",
        1.0 if reference.get("reference_detector_bridge_status") is not None else None,
    )
    na_edge_status, na_rolloff_factor = _na_edge_status_and_factor(
        channel,
        optical,
        sim_cfg,
        reference,
    )
    shot_noise_proxy = float(abs(sim_cfg.shot_noise_scale) * np.sqrt(max(I_ref, 0.0)))
    electronics_noise_proxy = float(abs(sim_cfg.noise_std))
    total_noise_proxy = float(np.hypot(electronics_noise_proxy, shot_noise_proxy))
    saturation_margin = None
    if str(sim_cfg.detector_dynamic_range_model) != "not_applied":
        saturation_margin = float(1.0 / max(I_ref, 1e-30))
    width_rank_metric = float(I_ref * na_rolloff_factor)
    band = _operating_band(
        A_ref=A_ref,
        I_ref=I_ref,
        electronics_noise_proxy=electronics_noise_proxy,
        shot_noise_proxy=shot_noise_proxy,
        total_noise_proxy=total_noise_proxy,
        na_edge_status=na_edge_status,
        sim_cfg=sim_cfg,
    )
    if band == "reference_too_weak":
        validity = "blocked_reference_too_weak_or_outside_na"
    elif band in {"reference_saturation_risk", "rin_or_leakage_risk"}:
        validity = "caution_reference_risk_dominates"
    elif band == "shot_noise_limited_no_gain":
        validity = "caution_reference_gain_not_monotonic"
    else:
        validity = "usable_relative_reference_operating_point"

    return {
        "reference_design_intensity_proxy": I_ref,
        "reference_design_amplitude_proxy": float(A_ref),
        "reference_design_roi_fraction": (
            float(roi_fraction) if roi_fraction is not None else None
        ),
        "reference_design_width_rank_metric": width_rank_metric,
        "reference_design_validity": validity,
        "I_ref_proxy": I_ref,
        "reference_shot_noise_proxy": shot_noise_proxy,
        "reference_total_noise_proxy": total_noise_proxy,
        "reference_saturation_margin_proxy": saturation_margin,
        "reference_operating_band": band,
        "reference_operating_point_status": "relative_proxy_active",
        "reference_operating_point_claim_level": (
            "relative_reference_proxy_not_detector_unit_calibrated"
        ),
        "reference_na_edge_policy": str(sim_cfg.reference_na_edge_policy),
        "reference_na_edge_rolloff_factor": na_rolloff_factor,
        "reference_na_edge_status": na_edge_status,
    }
