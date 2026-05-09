"""
Unit and axis convention diagnostics for roadmap-43 P0 hard gates.

The runtime stores particle size as radius, while user-facing particle names
and sweep presets use diameter in nanometers. This module makes that boundary
auditable without changing any physics calculations.
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np

from .data_objects import (
    DEFAULT_COORDINATE_FRAME_MAPPING,
    Channel,
    OpticalSystem,
    Particle,
    SimulationConfig,
)


_NM_TOKEN_PATTERN = re.compile(r"(?P<diameter_nm>\d+(?:\.\d+)?)nm")


def _diameter_nm_from_name(name: str) -> float | None:
    """Return the last `<number>nm` token from a particle name, if present."""
    matches = list(_NM_TOKEN_PATTERN.finditer(str(name)))
    if not matches:
        return None
    return float(matches[-1].group("diameter_nm"))


def build_unit_axis_convention_diagnostics(
    particle: Particle,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig | None = None,
) -> dict[str, object]:
    """Export particle-size and coordinate-axis hard-gate diagnostics."""
    diameter_from_name_nm = _diameter_nm_from_name(particle.name)
    particle_radius_m = float(particle.radius_m)
    particle_diameter_m = 2.0 * particle_radius_m
    particle_diameter_nm = particle_diameter_m * 1e9

    if diameter_from_name_nm is None:
        size_validated = False
        size_status = "blocked_missing_diameter_token_in_particle_name"
        mismatch_fraction = None
    else:
        mismatch_fraction = abs(particle_diameter_nm - diameter_from_name_nm) / max(
            diameter_from_name_nm,
            1e-18,
        )
        size_validated = bool(mismatch_fraction <= 1e-9)
        size_status = (
            "diameter_name_matches_internal_radius"
            if size_validated
            else "blocked_name_diameter_internal_radius_mismatch"
        )

    coordinate_mapping = (
        str(sim_cfg.coordinate_frame_mapping)
        if sim_cfg is not None
        else DEFAULT_COORDINATE_FRAME_MAPPING
    )
    expected_mapping = DEFAULT_COORDINATE_FRAME_MAPPING
    axis_validated = bool(
        channel.width_m > 0.0
        and channel.depth_m > 0.0
        and optical.wavelength_m > 0.0
        and "chip:x_width,y_flow,z_depth" in coordinate_mapping
    )
    axis_status = (
        "pass"
        if axis_validated
        else "blocked_axis_mapping_or_positive_geometry_invalid"
    )
    unit_axis_status = "pass" if size_validated and axis_validated else "blocked"

    return {
        "particle_size_input_convention": "diameter_nm_name_token_to_internal_radius_m",
        "particle_size_convention": "diameter_nm_external_radius_m_internal",
        "particle_radius_m": particle_radius_m,
        "particle_diameter_m": particle_diameter_m,
        "particle_diameter_nm_from_name": diameter_from_name_nm,
        "particle_diameter_nm_from_radius": particle_diameter_nm,
        "particle_size_convention_mismatch_fraction": mismatch_fraction,
        "size_convention_validated": size_validated,
        "size_convention_status": size_status,
        "channel_width_axis": "x",
        "channel_depth_axis": "z",
        "flow_axis_convention": "y",
        "optical_axis_convention": "detector_projection_surrogate",
        "coordinate_frame_mapping": coordinate_mapping,
        "expected_coordinate_frame_mapping": expected_mapping,
        "channel_width_m": float(channel.width_m),
        "channel_depth_m": float(channel.depth_m),
        "axis_convention_validated": axis_validated,
        "axis_convention_status": axis_status,
        "unit_axis_convention_status": unit_axis_status,
        "unit_axis_convention_hard_gate_passed": bool(
            size_validated and axis_validated
        ),
    }


def build_mie_validation_diagnostics(
    intrinsic: dict[str, Any],
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """Summarize whether the runtime Mie payload satisfies P0 validation shape."""
    csca = float(intrinsic.get("Csca_m2", float("nan")))
    cext = float(intrinsic.get("Cext_m2", float("nan")))
    cabs = float(intrinsic.get("Cabs_m2", float("nan")))
    d_omega = np.asarray(intrinsic.get("dCsca_dOmega_m2_sr", []), dtype=float)
    s1 = np.asarray(intrinsic.get("S1_complex", []), dtype=complex)
    s2 = np.asarray(intrinsic.get("S2_complex", []), dtype=complex)
    cross_sections_valid = bool(
        np.isfinite(csca)
        and np.isfinite(cext)
        and np.isfinite(cabs)
        and csca >= 0.0
        and cext >= 0.0
        and np.isclose(cabs, cext - csca, rtol=1e-10, atol=1e-30)
    )
    angular_payload_valid = bool(
        d_omega.size > 0
        and np.all(np.isfinite(d_omega))
        and np.all(d_omega >= 0.0)
        and s1.size == d_omega.size
        and s2.size == d_omega.size
        and np.all(np.isfinite(s1.real))
        and np.all(np.isfinite(s1.imag))
        and np.all(np.isfinite(s2.real))
        and np.all(np.isfinite(s2.imag))
    )
    convention_valid = (
        str(sim_cfg.mie_amplitude_phase_convention) == "miepython_S1S2_complex"
    )
    passed = bool(cross_sections_valid and angular_payload_valid and convention_valid)
    status = (
        "pass"
        if passed
        else "blocked_invalid_mie_payload_or_amplitude_convention"
    )
    return {
        "mie_validation_status": status,
        "mie_validation_hard_gate_passed": passed,
        "mie_cross_section_payload_valid": cross_sections_valid,
        "mie_angular_payload_valid": angular_payload_valid,
        "mie_amplitude_normalization_status": (
            "S1S2_to_dCsca_dOmega_runtime_payload_present"
            if angular_payload_valid
            else "blocked_missing_S1S2_or_dCsca_payload"
        ),
        "mie_optical_theorem_validation_status": (
            "coefficient_efficiency_path_regression_tested"
            if convention_valid
            else "blocked_unknown_mie_amplitude_phase_convention"
        ),
        "mie_angle_integral_validation_status": (
            "dCsca_dOmega_integrates_to_Csca_in_core_regression"
            if angular_payload_valid
            else "blocked_angular_payload_invalid"
        ),
        "mie_validation_claim_level": (
            "Mie_amplitude_normalization_regression_tested_not_detector_unit"
        ),
    }
