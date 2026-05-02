"""P0 EV confinement and integrity-risk diagnostics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .data_objects import Channel, Particle, SimulationConfig


EV_INTEGRITY_DIAGNOSTIC_FIELDS = (
    "ev_clearance_margin_nm",
    "ev_confinement_ratio",
    "ev_shear_rate_proxy",
    "ev_osmotic_stress_flag",
    "ev_wall_contact_probability",
    "ev_deformation_or_rupture_risk",
    "ev_integrity_claim_level",
    "ev_integrity_status",
    "ev_integrity_gate_passed",
)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_ev_integrity_risk_diagnostics(
    particle: Particle,
    channel: Channel,
    sim_cfg: SimulationConfig,
    *,
    geometry: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    """Export geometry-only EV integrity risk flags."""
    geometry = geometry or {}
    diameter_nm = float(particle.radius_m) * 2.0e9
    min_dimension_nm = min(float(channel.width_m), float(channel.depth_m)) * 1e9
    clearance_margin_nm = 0.5 * (min_dimension_nm - diameter_nm)
    confinement_ratio = (
        diameter_nm / min_dimension_nm if min_dimension_nm > 0.0 else float("inf")
    )
    roughness_nm = _as_float(geometry.get("surface_roughness_rms_nm"), 0.0)
    contact_threshold_nm = 2.0 * roughness_nm + 20.0
    shear_rate_proxy = (
        6.0 * float(sim_cfg.mean_flow_velocity_m_s) / max(float(channel.depth_m), 1e-30)
    )

    if clearance_margin_nm < contact_threshold_nm:
        risk = "high_contact_or_deformation_risk"
        wall_contact_probability = 0.8
    elif confinement_ratio > 0.5:
        risk = "moderate_confinement_risk"
        wall_contact_probability = 0.4
    else:
        risk = "low_by_geometry_surrogate"
        wall_contact_probability = 0.1

    is_ev_like = (
        str(getattr(particle, "family", "")).startswith("EV")
        or "exosome" in str(particle.name).lower()
    )
    if not is_ev_like:
        status = "not_applicable_non_ev_particle"
        claim_level = "not_applicable_non_ev_particle"
        gate_passed = True
    else:
        status = "geometry_surrogate_active_not_biophysical_validation"
        claim_level = "geometry_surrogate_integrity_risk_not_validated"
        gate_passed = risk != "high_contact_or_deformation_risk"

    return {
        "ev_clearance_margin_nm": clearance_margin_nm,
        "ev_confinement_ratio": confinement_ratio,
        "ev_shear_rate_proxy": shear_rate_proxy,
        "ev_osmotic_stress_flag": "unavailable_buffer_osmolality_not_configured",
        "ev_wall_contact_probability": wall_contact_probability,
        "ev_deformation_or_rupture_risk": risk,
        "ev_integrity_claim_level": claim_level,
        "ev_integrity_status": status,
        "ev_integrity_gate_passed": gate_passed,
    }
