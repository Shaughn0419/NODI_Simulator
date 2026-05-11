"""
Package-local materials database for NODI interferometric simulation.

Manages wavelength-dependent complex refractive indices for all materials
in the system (particles, medium, channel walls).

Unified interface: get_n_complex(material_key, wavelength_m) -> complex

Data sources:
    - Gold: Johnson & Christy (1972), 400–700 nm
    - Silver: Johnson & Christy (1972), visible subset
    - Water / 1x PBS: visible Cauchy dispersion surrogate
    - Fused silica: Malitson Sellmeier dispersion
    - Glass (BK7): historical constant approximation 1.52
    - Polystyrene: constant approximation 1.59
    - Exosome (uniform): constant 1.38 (literature range 1.37–1.40)

Note on medium/wall materials:
    The visible-dispersion formulas below support route/claim diagnostics and
    nominal wavelength sweeps. Medium property metadata is nominal and does
    not include batch-specific temperature, salinity/buffer composition, or
    uncertainty propagation.
"""

import numpy as np
from typing import Any


# ============================================================
# Material Database
# ============================================================

# Johnson & Christy (1972) gold, visible subset from refractiveindex.info
# Johnson.yml. Wavelengths are the measured tabulation points in nm, converted
# to meters in the material database below.
# n and k values: ñ = n + i·k
_GOLD_JC_DATA = {
    # wavelength_nm, n_real, n_imag (k)
    "wavelength_nm": np.array([
        397.4, 413.3, 430.5, 450.9, 471.4, 495.9, 520.9, 548.6,
        582.1, 616.8, 659.5, 704.5,
    ], dtype=float),
    "n_real": np.array([
        1.47, 1.46, 1.45, 1.38, 1.31, 1.04, 0.62, 0.43,
        0.29, 0.21, 0.14, 0.13,
    ], dtype=float),
    "n_imag": np.array([
        1.952, 1.958, 1.948, 1.914, 1.849, 1.833, 2.081, 2.455,
        2.863, 3.272, 3.697, 4.103,
    ], dtype=float),
}

# Johnson & Christy (1972) — Silver, visible subset from 397.4–704.5 nm.
# Full source range is broader; this local table intentionally mirrors the
# simulator's current visible sweep range.
_SILVER_JC_VISIBLE_DATA = {
    "wavelength_nm": np.array([
        397.4, 413.3, 430.5, 450.9, 471.4, 495.9, 520.9, 548.6,
        582.1, 616.8, 659.5, 704.5,
    ], dtype=float),
    "n_real": np.array([
        0.05, 0.05, 0.04, 0.04, 0.05, 0.05, 0.05, 0.06,
        0.05, 0.06, 0.05, 0.04,
    ], dtype=float),
    "n_imag": np.array([
        2.070, 2.275, 2.462, 2.657, 2.869, 3.093, 3.324, 3.586,
        3.858, 4.152, 4.483, 4.838,
    ], dtype=float),
}


def _water_visible_cauchy_n(wavelength_m: float, *, pbs_offset: float = 0.0) -> float:
    """Nominal room-temperature visible Cauchy surrogate for water-like media."""
    wavelength_um = float(wavelength_m) * 1e6
    if wavelength_um <= 0.0:
        raise ValueError(f"wavelength_m must be positive, got {wavelength_m}")
    return float(1.32292 + 0.003453 / (wavelength_um**2) + pbs_offset)


def _fused_silica_sellmeier_n(wavelength_m: float) -> float:
    """Malitson fused-silica Sellmeier equation, wavelength in vacuum meters."""
    wavelength_um = float(wavelength_m) * 1e6
    if wavelength_um <= 0.0:
        raise ValueError(f"wavelength_m must be positive, got {wavelength_m}")
    lambda_sq = wavelength_um**2
    n_sq = (
        1.0
        + (0.6961663 * lambda_sq) / (lambda_sq - 0.0684043**2)
        + (0.4079426 * lambda_sq) / (lambda_sq - 0.1162414**2)
        + (0.8974794 * lambda_sq) / (lambda_sq - 9.896161**2)
    )
    return float(np.sqrt(n_sq))


_WATER_LIKE_PROPERTIES = {
    "dn_dT": -1.0e-4,
    "viscosity_Pa_s": 8.9e-4,
    "density_kg_m3": 997.0,
    "thermal_conductivity_W_mK": 0.60,
    "thermal_diffusivity_m2_s": 1.43e-7,
    "osmolarity_or_solute_fraction": 0.0,
    "claim_level": "nominal_material_properties_no_uncertainty",
}

_FUSED_SILICA_PROPERTIES = {
    "dn_dT": 1.0e-5,
    "viscosity_Pa_s": None,
    "density_kg_m3": 2200.0,
    "thermal_conductivity_W_mK": 1.38,
    "thermal_diffusivity_m2_s": 8.4e-7,
    "osmolarity_or_solute_fraction": None,
    "claim_level": "vendor_nominal_dispersion_no_uncertainty",
}


MATERIAL_DB: dict[str, dict[str, Any]] = {
    "gold": {
        "source": "Johnson & Christy 1972",
        "type": "tabulated",
        "wavelength_m": _GOLD_JC_DATA["wavelength_nm"] * 1e-9,
        "n_real": _GOLD_JC_DATA["n_real"],
        "n_imag": _GOLD_JC_DATA["n_imag"],
    },
    "silver": {
        "source": "Johnson & Christy 1972",
        "type": "tabulated",
        "wavelength_m": _SILVER_JC_VISIBLE_DATA["wavelength_nm"] * 1e-9,
        "n_real": _SILVER_JC_VISIBLE_DATA["n_real"],
        "n_imag": _SILVER_JC_VISIBLE_DATA["n_imag"],
    },
    "water": {
        "source": "room-temperature visible Cauchy surrogate",
        "type": "cauchy",
        "formula": "n=1.32292+0.003453/lambda_um^2",
        "wavelength_range_m": (400e-9, 700e-9),
        "pbs_offset": 0.0,
        "n_imag_const": 0.0,
        **_WATER_LIKE_PROPERTIES,
    },
    "pbs_1x": {
        "source": "water Cauchy surrogate plus nominal PBS offset",
        "type": "cauchy",
        "formula": "water_visible_cauchy+0.0011",
        "wavelength_range_m": (400e-9, 700e-9),
        "pbs_offset": 0.0011,
        "n_imag_const": 0.0,
        **{
            **_WATER_LIKE_PROPERTIES,
            "viscosity_Pa_s": 9.3e-4,
            "density_kg_m3": 1005.0,
            "osmolarity_or_solute_fraction": 0.30,
        },
    },
    "hepes_buffer": {
        "source": "water Cauchy surrogate plus nominal HEPES buffer offset",
        "type": "cauchy",
        "formula": "water_visible_cauchy+0.0008",
        "wavelength_range_m": (400e-9, 700e-9),
        "pbs_offset": 0.0008,
        "n_imag_const": 0.0,
        **{
            **_WATER_LIKE_PROPERTIES,
            "viscosity_Pa_s": 9.1e-4,
            "density_kg_m3": 1002.0,
            "osmolarity_or_solute_fraction": 0.28,
        },
    },
    "culture_medium_surrogate": {
        "source": "water Cauchy surrogate plus nominal culture-medium offset",
        "type": "cauchy",
        "formula": "water_visible_cauchy+0.0015",
        "wavelength_range_m": (400e-9, 700e-9),
        "pbs_offset": 0.0015,
        "n_imag_const": 0.0,
        **{
            **_WATER_LIKE_PROPERTIES,
            "viscosity_Pa_s": 9.6e-4,
            "density_kg_m3": 1008.0,
            "osmolarity_or_solute_fraction": 0.32,
        },
    },
    "sucrose_solution_xpct": {
        "source": "nominal sucrose-gradient surrogate; xpct placeholder",
        "type": "cauchy",
        "formula": "water_visible_cauchy+0.018",
        "wavelength_range_m": (400e-9, 700e-9),
        "pbs_offset": 0.018,
        "n_imag_const": 0.0,
        **{
            **_WATER_LIKE_PROPERTIES,
            "viscosity_Pa_s": 1.3e-3,
            "density_kg_m3": 1040.0,
            "thermal_diffusivity_m2_s": 1.35e-7,
            "osmolarity_or_solute_fraction": "sucrose_mass_fraction_xpct",
        },
    },
    "iodixanol_solution_xpct": {
        "source": "nominal iodixanol-gradient surrogate; xpct placeholder",
        "type": "cauchy",
        "formula": "water_visible_cauchy+0.025",
        "wavelength_range_m": (400e-9, 700e-9),
        "pbs_offset": 0.025,
        "n_imag_const": 0.0,
        **{
            **_WATER_LIKE_PROPERTIES,
            "viscosity_Pa_s": 1.6e-3,
            "density_kg_m3": 1060.0,
            "thermal_diffusivity_m2_s": 1.30e-7,
            "osmolarity_or_solute_fraction": "iodixanol_mass_fraction_xpct",
        },
    },
    "fused_silica": {
        "source": "Malitson 1965 Sellmeier",
        "type": "sellmeier",
        "formula": "Malitson fused silica",
        "wavelength_range_m": (210e-9, 3710e-9),
        "n_imag_const": 0.0,
        "sellmeier_model": "fused_silica",
        **_FUSED_SILICA_PROPERTIES,
    },
    "fused_silica_viosil": {
        "source": "Viosil fused-silica nominal; Malitson Sellmeier surrogate",
        "type": "sellmeier",
        "formula": "Malitson fused silica",
        "wavelength_range_m": (210e-9, 3710e-9),
        "n_imag_const": 0.0,
        "sellmeier_model": "fused_silica",
        **_FUSED_SILICA_PROPERTIES,
    },
    "glass_bk7": {
        "source": "Sellmeier / constant approximation",
        "type": "constant",
        "n_real_const": 1.52,
        "n_imag_const": 0.0,
    },
    "polystyrene": {
        "source": "Literature constant for visible range",
        "type": "constant",
        "n_real_const": 1.59,
        "n_imag_const": 0.0,
    },
    "exosome_uniform": {
        "source": "Literature range 1.37-1.40, using 1.38",
        "type": "constant",
        "n_real_const": 1.38,
        "n_imag_const": 0.0,
    },
}


# ============================================================
# Public Interface
# ============================================================

def get_n_complex(material_key: str, wavelength_m: float) -> complex:
    """
    Return the complex refractive index n + i*k for a material at a given wavelength.

    For tabulated materials (e.g. gold): linear interpolation on stored data.
    For constant materials (e.g. water, glass): returns the same value at any wavelength.

    Args:
        material_key: Key into MATERIAL_DB (e.g. "gold", "water", "glass_bk7").
        wavelength_m: Vacuum wavelength in meters.

    Returns:
        Complex refractive index (n_real + 1j * n_imag).

    Raises:
        KeyError: If material_key is not in the database.
        ValueError: If wavelength is outside the tabulated range (for tabulated materials).
    """
    if material_key not in MATERIAL_DB:
        raise KeyError(
            f"Unknown material '{material_key}'. "
            f"Available: {sorted(MATERIAL_DB.keys())}"
        )

    entry = MATERIAL_DB[material_key]

    if entry["type"] == "constant":
        return complex(entry["n_real_const"], entry["n_imag_const"])

    if entry["type"] == "cauchy":
        wl_min, wl_max = entry["wavelength_range_m"]
        tol = 1e-15
        if wavelength_m < wl_min - tol or wavelength_m > wl_max + tol:
            raise ValueError(
                f"Wavelength {wavelength_m * 1e9:.1f} nm is outside the "
                f"nominal Cauchy range [{wl_min * 1e9:.0f}, {wl_max * 1e9:.0f}] nm "
                f"for material '{material_key}'."
            )
        n_real = _water_visible_cauchy_n(
            wavelength_m,
            pbs_offset=float(entry.get("pbs_offset", 0.0)),
        )
        return complex(n_real, entry["n_imag_const"])

    if entry["type"] == "sellmeier":
        wl_min, wl_max = entry["wavelength_range_m"]
        tol = 1e-15
        if wavelength_m < wl_min - tol or wavelength_m > wl_max + tol:
            raise ValueError(
                f"Wavelength {wavelength_m * 1e9:.1f} nm is outside the "
                f"Sellmeier range [{wl_min * 1e9:.0f}, {wl_max * 1e9:.0f}] nm "
                f"for material '{material_key}'."
            )
        if entry.get("sellmeier_model", material_key) == "fused_silica":
            return complex(_fused_silica_sellmeier_n(wavelength_m), entry["n_imag_const"])
        raise ValueError(f"No Sellmeier evaluator is defined for '{material_key}'.")

    if entry["type"] == "tabulated":
        wl_table = entry["wavelength_m"]
        wl_min, wl_max = wl_table[0], wl_table[-1]

        tol = 1e-15
        if wavelength_m < wl_min - tol or wavelength_m > wl_max + tol:
            raise ValueError(
                f"Wavelength {wavelength_m * 1e9:.1f} nm is outside the "
                f"tabulated range [{wl_min * 1e9:.0f}, {wl_max * 1e9:.0f}] nm "
                f"for material '{material_key}'."
            )

        n_real = float(np.interp(wavelength_m, wl_table, entry["n_real"]))
        n_imag = float(np.interp(wavelength_m, wl_table, entry["n_imag"]))
        return complex(n_real, n_imag)

    raise ValueError(f"Unknown material type '{entry['type']}' for '{material_key}'.")


def list_materials() -> list[str]:
    """Return sorted list of available material keys."""
    return sorted(MATERIAL_DB.keys())


def material_property_summary(material_key: str, wavelength_m: float) -> dict[str, object]:
    """Return route-governance material properties at one wavelength."""
    n_complex = get_n_complex(material_key, wavelength_m)
    entry = MATERIAL_DB[material_key]
    return {
        "material_key": material_key,
        "wavelength_m": float(wavelength_m),
        "n_real": float(n_complex.real),
        "n_imag": float(n_complex.imag),
        "dn_dT": entry.get("dn_dT"),
        "viscosity_Pa_s": entry.get("viscosity_Pa_s"),
        "density_kg_m3": entry.get("density_kg_m3"),
        "thermal_conductivity_W_mK": entry.get("thermal_conductivity_W_mK"),
        "thermal_diffusivity_m2_s": entry.get("thermal_diffusivity_m2_s"),
        "osmolarity_or_solute_fraction": entry.get("osmolarity_or_solute_fraction"),
        "source": entry.get("source"),
        "claim_level": entry.get(
            "claim_level",
            "nominal_visible_dispersion_only",
        ),
    }


def material_db_coverage_diagnostics() -> dict[str, object]:
    """Return claim-gating diagnostics for the built-in material database."""
    gold = MATERIAL_DB.get("gold", {})
    silver = MATERIAL_DB.get("silver", {})
    water = MATERIAL_DB.get("water", {})
    pbs = MATERIAL_DB.get("pbs_1x", {})
    silica = MATERIAL_DB.get("fused_silica", {})
    au_supported = gold.get("type") == "tabulated"
    ag_supported = silver.get("type") == "tabulated"
    medium_dispersion_supported = water.get("type") == "cauchy" and pbs.get("type") == "cauchy"
    wall_dispersion_supported = silica.get("type") == "sellmeier"
    if au_supported and ag_supported and medium_dispersion_supported and wall_dispersion_supported:
        coverage_status = "visible_AuAg_medium_wall_dispersion_available_nominal"
    elif au_supported and ag_supported:
        coverage_status = "AuAg_tabulated_medium_wall_dispersion_partial"
    else:
        coverage_status = "material_db_incomplete_for_tsuyama_AuAg_multispectral"
    return {
        "material_db_coverage_status": coverage_status,
        "tsuyama_AuAg_multispectral_supported": bool(au_supported and ag_supported),
        "medium_wall_dispersion_status": (
            "nominal_visible_dispersion_available_no_uncertainty"
            if medium_dispersion_supported and wall_dispersion_supported
            else "medium_or_wall_dispersion_incomplete"
        ),
        "material_db_gold_status": (
            "tabulated_visible_available" if au_supported else "missing_or_not_tabulated"
        ),
        "material_db_silver_status": (
            "tabulated_visible_available" if ag_supported else "missing_or_not_tabulated"
        ),
    }
