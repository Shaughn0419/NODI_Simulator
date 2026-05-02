"""
dashboard/mie_backend.py — Pure Mie scattering helpers for the dashboard

This module intentionally stays separate from interferometric/reference-field
logic. It only exposes intrinsic Mie scattering quantities for interactive
visualization.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from nodi_simulator.dashboard.config import (
    MEDIUM,
    format_particle_label,
    make_particle,
)
from nodi_simulator.data_objects import Particle
from nodi_simulator.intrinsic_scattering import compute_intrinsic_scattering


def build_theta_grid_deg(n_points: int = 361) -> np.ndarray:
    """Build an angular grid in degrees, avoiding the exact 0 and 180 endpoints."""
    return np.linspace(0.5, 179.5, n_points)


def _compute_mie_case_from_particle(
    particle: Particle,
    material: str,
    diameter_nm: float,
    wavelength_nm: float,
    theta_grid_deg: np.ndarray,
    particle_label: str | None = None,
) -> dict:
    """Shared Mie case assembly for both library and custom particles."""
    theta_grid_deg = np.asarray(theta_grid_deg, dtype=float)
    theta_grid_rad = np.deg2rad(theta_grid_deg)

    wavelength_m = wavelength_nm * 1e-9
    intrinsic = compute_intrinsic_scattering(
        particle, MEDIUM, wavelength_m, theta_grid_rad
    )

    geo_cross_m2 = np.pi * particle.radius_m**2
    Qsca = intrinsic["Csca_m2"] / geo_cross_m2
    Qext = intrinsic["Cext_m2"] / geo_cross_m2
    Qabs = intrinsic["Cabs_m2"] / geo_cross_m2

    n_particle = particle.n_complex_at(wavelength_m)
    n_medium = MEDIUM.refractive_index_at(wavelength_m)
    m_rel = intrinsic["relative_index"]

    return {
        "material": material,
        "particle_label": particle_label or particle.name,
        "particle_name": particle.name,
        "diameter_nm": float(diameter_nm),
        "radius_nm": float(diameter_nm) / 2.0,
        "wavelength_nm": float(wavelength_nm),
        "wavelength_m": wavelength_m,
        "size_parameter": intrinsic["size_parameter"],
        "n_particle_real": float(np.real(n_particle)),
        "n_particle_imag": float(np.imag(n_particle)),
        "n_medium": float(n_medium),
        "relative_index_real": float(np.real(m_rel)),
        "relative_index_imag": float(np.imag(m_rel)),
        "geo_cross_m2": float(geo_cross_m2),
        "Csca_m2": intrinsic["Csca_m2"],
        "Cext_m2": intrinsic["Cext_m2"],
        "Cabs_m2": intrinsic["Cabs_m2"],
        "Qsca": float(Qsca),
        "Qext": float(Qext),
        "Qabs": float(Qabs),
        "theta_deg": theta_grid_deg,
        "theta_rad": theta_grid_rad,
        "dCsca_dOmega_m2_sr": intrinsic["dCsca_dOmega_m2_sr"],
        "Esca_unit_amp": intrinsic["Esca_unit_amp"],
        "S1_abs": np.abs(intrinsic["S1_complex"]),
        "S2_abs": np.abs(intrinsic["S2_complex"]),
    }


def compute_mie_case(
    material: str,
    diameter_nm: float,
    wavelength_nm: float,
    theta_grid_deg: np.ndarray | None = None,
) -> dict:
    """
    Compute pure intrinsic Mie scattering for one particle / wavelength pair.

    Returns both integrated quantities and angle-resolved arrays.
    """
    if theta_grid_deg is None:
        theta_grid_deg = build_theta_grid_deg()

    particle = make_particle(material, diameter_nm)
    return _compute_mie_case_from_particle(
        particle=particle,
        material=material,
        diameter_nm=diameter_nm,
        wavelength_nm=wavelength_nm,
        theta_grid_deg=theta_grid_deg,
        particle_label=format_particle_label(material, diameter_nm),
    )


def build_mie_summary_dataframe(
    materials: list[str],
    diameters_nm: list[int] | np.ndarray,
    wavelengths_nm: list[float] | np.ndarray,
    summary_theta_deg: float = 90.0,
) -> pd.DataFrame:
    """Build a compact DataFrame of Mie quantities over a parameter grid."""
    rows = []
    for material in materials:
        for wavelength_nm in wavelengths_nm:
            for diameter_nm in diameters_nm:
                case = compute_mie_case(
                    material,
                    diameter_nm,
                    wavelength_nm,
                    theta_grid_deg=np.array([summary_theta_deg]),
                )
                rows.append({
                    "material": case["material"],
                    "particle_label": case["particle_label"],
                    "particle_name": case["particle_name"],
                    "diameter_nm": case["diameter_nm"],
                    "radius_nm": case["radius_nm"],
                    "wavelength_nm": case["wavelength_nm"],
                    "size_parameter": case["size_parameter"],
                    "n_particle_real": case["n_particle_real"],
                    "n_particle_imag": case["n_particle_imag"],
                    "n_medium": case["n_medium"],
                    "relative_index_real": case["relative_index_real"],
                    "relative_index_imag": case["relative_index_imag"],
                    "geo_cross_m2": case["geo_cross_m2"],
                    "Csca_m2": case["Csca_m2"],
                    "Cext_m2": case["Cext_m2"],
                    "Cabs_m2": case["Cabs_m2"],
                    "Qsca": case["Qsca"],
                    "Qext": case["Qext"],
                    "Qabs": case["Qabs"],
                    "summary_theta_deg": float(summary_theta_deg),
                    "dCsca_dOmega_at_theta_m2_sr": float(case["dCsca_dOmega_m2_sr"][0]),
                    "Esca_unit_amp_at_theta_m": float(case["Esca_unit_amp"][0]),
                })
    return pd.DataFrame(rows)


def build_mie_angular_dataframe(
    case_specs: list[dict],
    theta_grid_deg: np.ndarray | None = None,
) -> pd.DataFrame:
    """Build a long-form DataFrame for angle-resolved Mie comparisons."""
    rows = []
    if theta_grid_deg is None:
        theta_grid_deg = build_theta_grid_deg()

    for spec in case_specs:
        case = compute_mie_case(
            spec["material"],
            spec["diameter_nm"],
            spec["wavelength_nm"],
            theta_grid_deg=theta_grid_deg,
        )
        label = (
            f"{case['particle_label']}, "
            f"{int(round(case['wavelength_nm']))} nm"
        )
        for theta_deg, dcsca, s1_abs, s2_abs in zip(
            case["theta_deg"],
            case["dCsca_dOmega_m2_sr"],
            case["S1_abs"],
            case["S2_abs"],
        ):
            rows.append({
                "label": label,
                "material": case["material"],
                "particle_label": case["particle_label"],
                "diameter_nm": case["diameter_nm"],
                "wavelength_nm": case["wavelength_nm"],
                "theta_deg": float(theta_deg),
                "dCsca_dOmega_m2_sr": float(dcsca),
                "S1_abs": float(s1_abs),
                "S2_abs": float(s2_abs),
            })
    return pd.DataFrame(rows)


def build_mie_single_variable_scan_dataframe(
    scan_variable: str,
    material: str,
    scan_values: list[float] | np.ndarray,
    fixed_diameter_nm: float,
    fixed_wavelength_nm: float,
    theta_deg: float,
    ) -> pd.DataFrame:
    """Build a one-variable scan DataFrame at a fixed scattering angle."""
    if scan_variable not in {"diameter_nm", "wavelength_nm"}:
        raise ValueError(
            "scan_variable must be 'diameter_nm' or 'wavelength_nm', "
            f"got {scan_variable!r}"
        )

    rows = []
    for value in np.asarray(scan_values, dtype=float):
        diameter_nm = value if scan_variable == "diameter_nm" else fixed_diameter_nm
        wavelength_nm = value if scan_variable == "wavelength_nm" else fixed_wavelength_nm
        case = compute_mie_case(
            material,
            diameter_nm,
            wavelength_nm,
            theta_grid_deg=np.array([theta_deg]),
        )
        rows.append({
            "scan_variable": scan_variable,
            "scan_value": float(value),
            "material": case["material"],
            "diameter_nm": case["diameter_nm"],
            "wavelength_nm": case["wavelength_nm"],
            "theta_deg": float(theta_deg),
            "size_parameter": case["size_parameter"],
            "n_particle_real": case["n_particle_real"],
            "n_particle_imag": case["n_particle_imag"],
            "relative_index_real": case["relative_index_real"],
            "relative_index_imag": case["relative_index_imag"],
            "Csca_m2": case["Csca_m2"],
            "Cext_m2": case["Cext_m2"],
            "Cabs_m2": case["Cabs_m2"],
            "Qsca": case["Qsca"],
            "Qext": case["Qext"],
            "Qabs": case["Qabs"],
            "dCsca_dOmega_at_theta_m2_sr": float(case["dCsca_dOmega_m2_sr"][0]),
            "Esca_unit_amp_at_theta_m": float(case["Esca_unit_amp"][0]),
        })
    return pd.DataFrame(rows)


def build_mie_relative_index_scan_dataframe(
    relative_index_real_values: list[float] | np.ndarray,
    diameter_nm: float,
    wavelength_nm: float,
    theta_deg: float,
    relative_index_imag: float = 0.0,
) -> pd.DataFrame:
    """
    Build a fixed-angle scan over the real part of relative refractive index.

    This is a sensitivity-study view, separate from the material database.
    """
    rows = []
    wavelength_m = wavelength_nm * 1e-9
    n_medium = MEDIUM.refractive_index_at(wavelength_m)
    radius_m = diameter_nm * 1e-9 / 2.0

    for m_real in np.asarray(relative_index_real_values, dtype=float):
        particle = Particle(
            name=f"custom_mrel_{m_real:.3f}_{relative_index_imag:.3f}",
            radius_m=radius_m,
            n_real=float(m_real * n_medium),
            n_imag=float(relative_index_imag * n_medium),
        )
        case = _compute_mie_case_from_particle(
            particle=particle,
            material="custom_relative_index",
            diameter_nm=diameter_nm,
            wavelength_nm=wavelength_nm,
            theta_grid_deg=np.array([theta_deg]),
            particle_label=f"m={m_real:.3f}+{relative_index_imag:.3f}i",
        )
        rows.append({
            "m_real": float(m_real),
            "m_imag": float(relative_index_imag),
            "theta_deg": float(theta_deg),
            "diameter_nm": float(diameter_nm),
            "wavelength_nm": float(wavelength_nm),
            "n_medium": case["n_medium"],
            "n_particle_real": case["n_particle_real"],
            "n_particle_imag": case["n_particle_imag"],
            "relative_index_real": case["relative_index_real"],
            "relative_index_imag": case["relative_index_imag"],
            "size_parameter": case["size_parameter"],
            "Csca_m2": case["Csca_m2"],
            "Qsca": case["Qsca"],
            "dCsca_dOmega_at_theta_m2_sr": float(case["dCsca_dOmega_m2_sr"][0]),
            "Esca_unit_amp_at_theta_m": float(case["Esca_unit_amp"][0]),
        })
    return pd.DataFrame(rows)
