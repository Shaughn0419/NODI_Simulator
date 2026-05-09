"""
Package-local intrinsic scattering module for NODI interferometric simulation.

Computes particle intrinsic optical response using Mie theory.
This module is PURE PHYSICS — it only computes intrinsic quantities.
Normalization by E_sca_ref is done in the outer layer (run_single_case_batch).

Uses Particle.n_complex_at() and Medium.refractive_index_at() for
wavelength-dependent material data, and outputs S1_complex / S2_complex
for downstream polarization analysis.

Simplifications:
    - Unified Mie engine, no Rayleigh auto-switch.
    - dCsca/dΩ averaged over two polarizations (unpolarized light).
"""

from copy import deepcopy
from functools import lru_cache

import numpy as np

from .data_objects import Particle, Medium
from .mie_engine import (
    mie_angular_from_coefficients,
    mie_coefficients,
    mie_core_shell_coefficients,
    mie_efficiencies_from_coefficients,
)
from .structured_particles import resolve_structured_particle_spec


def _copy_intrinsic_payload(payload: dict) -> dict:
    """Return a caller-owned copy while still benefiting from internal caching."""
    copied = {
        "k_m": float(payload["k_m"]),
        "k_m_inv": float(payload["k_m_inv"]),
        "k_m_inv_alias_status": "deprecated_legacy_alias_for_k_m_not_inverse",
        "size_parameter": float(payload["size_parameter"]),
        "relative_index": complex(payload["relative_index"]),
        "Csca_m2": float(payload["Csca_m2"]),
        "Cext_m2": float(payload["Cext_m2"]),
        "Cabs_m2": float(payload["Cabs_m2"]),
        "dCsca_dOmega_m2_sr": np.asarray(payload["dCsca_dOmega_m2_sr"], dtype=float).copy(),
        "theta_grid_rad": np.asarray(payload["theta_grid_rad"], dtype=float).copy(),
        "Esca_unit_amp": np.asarray(payload["Esca_unit_amp"], dtype=float).copy(),
        "S1_complex": np.asarray(payload["S1_complex"], dtype=complex).copy(),
        "S2_complex": np.asarray(payload["S2_complex"], dtype=complex).copy(),
    }
    if "particle_optical_model" in payload:
        copied["particle_optical_model"] = str(payload["particle_optical_model"])
    if "effective_relative_index" in payload:
        copied["effective_relative_index"] = complex(payload["effective_relative_index"])
    if "structured_particle_spec" in payload:
        copied["structured_particle_spec"] = deepcopy(payload["structured_particle_spec"])
    return copied


@lru_cache(maxsize=256)
def _compute_intrinsic_scattering_cached(
    radius_m: float,
    n_p_real: float,
    n_p_imag: float,
    n_m: float,
    wavelength_m: float,
    theta_grid_bytes: bytes,
    theta_grid_shape: tuple[int, ...],
    theta_grid_dtype: str,
) -> dict:
    """Process-local intrinsic-scattering cache keyed by immutable physics inputs."""
    theta_grid_rad = np.frombuffer(
        theta_grid_bytes,
        dtype=np.dtype(theta_grid_dtype),
    ).reshape(theta_grid_shape)
    n_p = complex(n_p_real, n_p_imag)
    a = float(radius_m)

    k = 2.0 * np.pi * n_m / wavelength_m
    x = k * a
    m_rel = n_p / n_m

    a_n, b_n = mie_coefficients(x, m_rel)
    Qext, Qsca = mie_efficiencies_from_coefficients(x, a_n, b_n)
    geo_cross = np.pi * a**2
    Csca = Qsca * geo_cross
    Cext = Qext * geo_cross
    Cabs = Cext - Csca

    S1, S2 = mie_angular_from_coefficients(a_n, b_n, theta_grid_rad)
    dCsca_dOmega = (np.abs(S1)**2 + np.abs(S2)**2) / (2.0 * k**2)
    Esca_unit_amp = np.sqrt(np.maximum(dCsca_dOmega, 0.0))

    return {
        "k_m": float(k),
        "k_m_inv": float(k),
        "size_parameter": float(x),
        "relative_index": complex(m_rel),
        "Csca_m2": float(Csca),
        "Cext_m2": float(Cext),
        "Cabs_m2": float(Cabs),
        "dCsca_dOmega_m2_sr": np.asarray(dCsca_dOmega, dtype=float),
        "theta_grid_rad": np.asarray(theta_grid_rad, dtype=float).copy(),
        "Esca_unit_amp": np.asarray(Esca_unit_amp, dtype=float),
        "S1_complex": np.asarray(S1, dtype=complex),
        "S2_complex": np.asarray(S2, dtype=complex),
    }


@lru_cache(maxsize=256)
def _compute_intrinsic_core_shell_scattering_cached(
    outer_radius_m: float,
    core_radius_m: float,
    n_shell_real: float,
    n_shell_imag: float,
    n_core_real: float,
    n_core_imag: float,
    effective_n_real: float,
    effective_n_imag: float,
    n_m: float,
    wavelength_m: float,
    theta_grid_bytes: bytes,
    theta_grid_shape: tuple[int, ...],
    theta_grid_dtype: str,
) -> dict:
    """Process-local intrinsic-scattering cache for structured core-shell particles."""
    theta_grid_rad = np.frombuffer(
        theta_grid_bytes,
        dtype=np.dtype(theta_grid_dtype),
    ).reshape(theta_grid_shape)
    outer_radius = float(outer_radius_m)
    core_radius = float(core_radius_m)
    n_shell = complex(n_shell_real, n_shell_imag)
    n_core = complex(n_core_real, n_core_imag)
    n_eff = complex(effective_n_real, effective_n_imag)

    k = 2.0 * np.pi * n_m / wavelength_m
    x_outer = k * outer_radius
    core_radius_ratio = core_radius / outer_radius
    m_shell = n_shell / n_m
    m_core = n_core / n_m

    a_n, b_n = mie_core_shell_coefficients(
        x_outer,
        core_radius_ratio,
        m_shell,
        m_core,
    )
    Qext, Qsca = mie_efficiencies_from_coefficients(x_outer, a_n, b_n)
    geo_cross = np.pi * outer_radius**2
    Csca = Qsca * geo_cross
    Cext = Qext * geo_cross
    Cabs = Cext - Csca

    S1, S2 = mie_angular_from_coefficients(a_n, b_n, theta_grid_rad)
    dCsca_dOmega = (np.abs(S1)**2 + np.abs(S2)**2) / (2.0 * k**2)
    Esca_unit_amp = np.sqrt(np.maximum(dCsca_dOmega, 0.0))

    return {
        "k_m": float(k),
        "k_m_inv": float(k),
        "size_parameter": float(x_outer),
        "relative_index": complex(n_eff / n_m),
        "effective_relative_index": complex(n_eff / n_m),
        "Csca_m2": float(Csca),
        "Cext_m2": float(Cext),
        "Cabs_m2": float(Cabs),
        "dCsca_dOmega_m2_sr": np.asarray(dCsca_dOmega, dtype=float),
        "theta_grid_rad": np.asarray(theta_grid_rad, dtype=float).copy(),
        "Esca_unit_amp": np.asarray(Esca_unit_amp, dtype=float),
        "S1_complex": np.asarray(S1, dtype=complex),
        "S2_complex": np.asarray(S2, dtype=complex),
        "particle_optical_model": "mie_core_shell",
    }


def compute_intrinsic_scattering(
    particle: Particle,
    medium: Medium,
    wavelength_m: float,
    theta_grid_rad: np.ndarray,
) -> dict:
    """
    Compute particle intrinsic scattering quantities.

    Args:
        particle: Particle object.
        medium: Medium object.
        wavelength_m: Vacuum wavelength in meters.
        theta_grid_rad: Array of scattering angles (radians).

    Returns:
        dict with keys:
            k_m: Wavenumber k = 2π·n_m/λ₀ [1/m]
            k_m_inv: Deprecated alias for k_m retained for old consumers; it
                is not 1/k_m.
            size_parameter: x = k·a
            relative_index: m = ñ_p / n_m (complex)
            Csca_m2: Scattering cross section [m²]
            Cext_m2: Extinction cross section [m²]
            Cabs_m2: Absorption cross section [m²]
            dCsca_dOmega_m2_sr: Differential scattering cross section [m²/sr]
            theta_grid_rad: Input angle grid (returned for downstream interpolation)
            Esca_unit_amp: √(dCsca/dΩ), NOT normalized
            S1_complex: Complex Mie amplitude function S1(θ)
            S2_complex: Complex Mie amplitude function S2(θ)
    """
    n_m = medium.refractive_index_at(wavelength_m)
    theta_grid = np.asarray(theta_grid_rad, dtype=float)

    if particle.model_type == "mie_core_shell":
        spec = resolve_structured_particle_spec(particle, n_m, wavelength_m)
        cached = _compute_intrinsic_core_shell_scattering_cached(
            float(spec["outer_radius_m"]),
            float(spec["core_radius_m"]),
            float(np.real(spec["shell_n_complex"])),
            float(np.imag(spec["shell_n_complex"])),
            float(np.real(spec["core_n_complex"])),
            float(np.imag(spec["core_n_complex"])),
            float(np.real(spec["equivalent_uniform_n_complex"])),
            float(np.imag(spec["equivalent_uniform_n_complex"])),
            float(n_m),
            float(wavelength_m),
            theta_grid.tobytes(),
            tuple(theta_grid.shape),
            theta_grid.dtype.str,
        )
        copied = _copy_intrinsic_payload(cached)
        copied["structured_particle_spec"] = deepcopy(spec)
        return copied

    n_p = particle.n_complex_at(wavelength_m)
    cached = _compute_intrinsic_scattering_cached(
        float(particle.radius_m),
        float(np.real(n_p)),
        float(np.imag(n_p)),
        float(n_m),
        float(wavelength_m),
        theta_grid.tobytes(),
        tuple(theta_grid.shape),
        theta_grid.dtype.str,
    )
    return _copy_intrinsic_payload(cached)
