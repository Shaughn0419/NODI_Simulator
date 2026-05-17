"""Package-local NODI thermal contamination diagnostics."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from .data_objects import OpticalSystem, Particle, SimulationConfig
from .type_coerce import blocker_summary as _blocker_summary
from .type_coerce import finite_float as _as_float


NODI_THERMAL_CONTAMINATION_FIELDS = (
    "nodi_thermal_contamination_status",
    "nodi_thermal_contamination_claim_level",
    "nodi_thermal_contamination_proxy",
    "nodi_absorption_to_scattering_ratio",
    "nodi_absorbed_power_proxy",
    "nodi_probe_power_density_W_m2",
    "nodi_particle_material_thermal_class",
    "nodi_absorption_to_scattering_crosstalk_risk",
    "nodi_standard_particle_thermal_artifact_risk",
    "nodi_ev_thermal_contamination_gate_required",
    "nodi_thermal_solver_required_for_quantitative_claim",
    "nodi_thermal_contamination_gate_passed",
    "nodi_thermal_contamination_blocker_summary",
)

def _power_density_W_m2(optical: OpticalSystem, sim_cfg: SimulationConfig) -> float:
    if sim_cfg.probe_power_W is None:
        return float(optical.peak_irradiance_W_m2)
    geometry = optical.resolve_illumination_geometry()
    waist_x_m = float(geometry["illumination_beam_waist_x_m"])
    waist_z_m = float(geometry["illumination_beam_waist_z_m"])
    beam_area_m2 = math.pi * waist_x_m * waist_z_m
    return float(sim_cfg.probe_power_W) / max(beam_area_m2, 1e-30)


def _thermal_class(particle: Particle) -> str:
    name = str(particle.name).casefold()
    material_key = str(particle.material_key or "").casefold()
    if material_key in {"gold", "silver"} or "gold" in name or "silver" in name:
        return "absorbing_metal_standard"
    if (
        "exosome" in name
        or "ev" in name
        or str(particle.model_type) == "mie_core_shell"
    ):
        return "EV_like_low_absorption"
    if material_key:
        return f"material_{material_key}"
    return "unknown_particle_material"


def _risk_from_ratio_and_proxy(
    absorption_to_scattering_ratio: float,
    contamination_proxy: float,
) -> str:
    if absorption_to_scattering_ratio >= 1.0 or contamination_proxy >= 10.0:
        return "high"
    if absorption_to_scattering_ratio >= 0.1 or contamination_proxy >= 1.0:
        return "medium"
    return "low"


def build_nodi_thermal_contamination_diagnostics(
    particle: Particle,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    intrinsic: Mapping[str, Any],
) -> dict[str, object]:
    """Build NODI thermal cross-talk diagnostics from intrinsic absorption data."""
    cabs_m2 = max(_as_float(intrinsic.get("Cabs_m2"), 0.0), 0.0)
    csca_m2 = max(_as_float(intrinsic.get("Csca_m2"), 0.0), 0.0)
    ratio = cabs_m2 / max(csca_m2, 1.0e-30)
    power_density = _power_density_W_m2(optical, sim_cfg)
    absorbed_power_proxy = cabs_m2 * power_density
    contamination_proxy = ratio * (power_density / 1.0e8)
    risk = _risk_from_ratio_and_proxy(ratio, contamination_proxy)
    material_class = _thermal_class(particle)
    is_metal_standard = material_class == "absorbing_metal_standard"
    is_ev_like = material_class == "EV_like_low_absorption"

    standard_risk = risk if is_metal_standard else "not_standard_particle"

    blockers: list[str] = []
    if sim_cfg.probe_power_W is None:
        blockers.append("probe_power_missing_for_absolute_thermal_proxy")
    if risk == "high":
        blockers.append("nodi_absorption_to_scattering_crosstalk_high")
    if is_metal_standard and risk in {"high", "medium"}:
        blockers.append("absorbing_metal_standard_thermal_artifact_risk")

    return {
        "nodi_thermal_contamination_status": (
            "absorption_scattering_proxy_active"
            if csca_m2 > 0.0 or cabs_m2 > 0.0
            else "unavailable_missing_intrinsic_cross_sections"
        ),
        "nodi_thermal_contamination_claim_level": (
            "diagnostic_absorption_proxy_not_thermal_solver"
        ),
        "nodi_thermal_contamination_proxy": contamination_proxy,
        "nodi_absorption_to_scattering_ratio": ratio,
        "nodi_absorbed_power_proxy": absorbed_power_proxy,
        "nodi_probe_power_density_W_m2": power_density,
        "nodi_particle_material_thermal_class": material_class,
        "nodi_absorption_to_scattering_crosstalk_risk": risk,
        "nodi_standard_particle_thermal_artifact_risk": standard_risk,
        "nodi_ev_thermal_contamination_gate_required": bool(
            is_ev_like and risk == "high" and sim_cfg.probe_power_W is not None
        ),
        "nodi_thermal_solver_required_for_quantitative_claim": True,
        "nodi_thermal_contamination_gate_passed": risk != "high",
        "nodi_thermal_contamination_blocker_summary": _blocker_summary(blockers),
    }
