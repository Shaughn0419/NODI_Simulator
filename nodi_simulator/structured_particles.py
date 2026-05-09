"""
Package-local structured particle optical surrogates.

This module keeps non-homogeneous particle assumptions out of the main
homogeneous-material database. The first structured model is a biomimetic
exosome surrogate: aqueous cargo core + membrane/protein-corona/electric-double-
layer collapsed into one optically effective shell.

Literature anchors used in this module:
    - A. L. Aden and M. Kerker, J. Appl. Phys. 22, 1242-1246 (1951):
      coated-sphere extension of Mie theory.
      DOI: 10.1063/1.1699834
    - C. F. Bohren and D. R. Huffman, Absorption and Scattering of Light by
      Small Particles (Wiley, 1983): standard reference for sphere/coated-sphere
      scattering and small-particle polarizability matching.
      Publisher: https://www.wiley-vch.de/en?isbn=9780471293408&option=com_eshop&view=product
    - E. van der Pol et al., J. Extracell. Vesicles 9:e12074 (2020):
      EVs are commonly modeled as core-shell particles with a 5 nm shell,
      shell RI about 1.46, and core RI about 1.343-1.36 for optical sizing.
      DOI: 10.1002/jev2.12074
    - A. Enciso-Martinez et al., J. Extracell. Vesicles 9:e1730134 (2020):
      single-particle Rayleigh/Raman analysis again models EVs as core-shell
      particles and notes that EV RI is typically below about 1.42; the paper
      uses EV_core = 1.36-1.40, EV_shell = 1.48, shell thickness = 6 nm.
      DOI: 10.1080/20013078.2020.1730134
    - E. van der Pol, T. G. van Leeuwen, and X. Yan, Sci. Rep. 11, 24151 (2021):
      plausible EV optical shells span from about 4 nm / RI 1.45 to 12 nm /
      RI 1.52, with core RI about 1.353-1.380 depending on membrane protein
      loading and brightness scenario.
      DOI: 10.1038/s41598-021-03015-2
    - M. Heidarzadeh et al., Cell Commun. Signal. 21, 64 (2023):
      exosomes can acquire a dynamic protein corona in biofluids; the corona
      changes size, zeta potential, and surface fingerprint.
      DOI: 10.1186/s12964-023-01089-1
    - M. Midekessa et al., ACS Omega 5, 16701-16710 (2020):
      EVs are negatively charged in physiological media and ionic strength /
      valency compress the electric double layer and reduce the magnitude of
      zeta potential.
      DOI: 10.1021/acsomega.0c01582
    - J. N. Israelachvili, Intermolecular and Surface Forces, 3rd ed.
      (Academic Press, 2011): standard Debye-length / double-layer reference.

Modeling stance:
    - The membrane thickness and membrane RI are taken near the dim-to-mid EV
      literature range.
    - The protein corona is represented as an additional moderate-RI layer
      because the literature strongly supports its existence but does not give
      one universal optical constant.
    - Surface charge is not treated as a direct optical Drude-like response in
      the visible; instead we include its first-order optical footprint through
      an ionic hydrated layer with Debye-scale thickness.
    - This is therefore a physics-informed surrogate for exosome scattering,
      not a claim that every exosome is a static isotropic concentric sphere.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import numpy as np

from .data_objects import Particle


EXOSOME_MODEL_PRESETS = {
    "membrane_only_dim_2021": {
        "core_n_real": 1.380,
        "membrane_n_real": 1.450,
        "corona_n_real": 1.330,
        "membrane_thickness_m": 4.0e-9,
        "corona_thickness_m": 0.0,
        "ionic_strength_M": 0.150,
        "edl_refractive_increment": 0.000,
        "min_core_radius_fraction": 0.25,
        "source_label": "van der Pol et al. 2021 dim EV shell scenario",
        "source_type": "direct literature scenario",
    },
    "membrane_only_nominal_2020": {
        # Core RI: placed inside the 1.343-1.380 interval used in EV optical papers.
        "core_n_real": 1.360,
        # Membrane RI: aligned with the 1.45-1.46 phospholipid-membrane values
        # used in van der Pol et al. (2020, 2021).
        "membrane_n_real": 1.460,
        "corona_n_real": 1.330,
        # A bare phospholipid bilayer is about 4 nm thick in the 2021 EV optical
        # paper; 5 nm matches the 2020 JEV EV shell assumption.
        "membrane_thickness_m": 5.0e-9,
        "corona_thickness_m": 0.0,
        "ionic_strength_M": 0.150,
        "edl_refractive_increment": 0.000,
        "min_core_radius_fraction": 0.25,
        "source_label": "van der Pol et al. 2020 nominal EV shell scenario",
        "source_type": "direct literature scenario",
    },
    "biomimetic_corona_nominal": {
        "core_n_real": 1.360,
        "membrane_n_real": 1.460,
        # Protein-corona RI: literature supports corona formation but does not
        # offer a single optical constant. We use a conservative intermediate
        # value above water/core and below the brightest membrane-rich shells.
        "corona_n_real": 1.400,
        "membrane_thickness_m": 5.0e-9,
        # Corona thickness is set to 4 nm so the total surface shell remains
        # near the common ~10 nm EV optical-shell surrogate while separating
        # membrane and externally adsorbed biomolecules.
        "corona_thickness_m": 4.0e-9,
        "ionic_strength_M": 0.150,
        # Small local RI lift for the hydrated ionic layer. This is a weak
        # optical surrogate for the EDL, not a direct zeta-potential inversion.
        "edl_refractive_increment": 0.005,
        "min_core_radius_fraction": 0.25,
        "source_label": "membrane literature + corona/EDL biomimetic nominal",
        "source_type": "literature-constrained surrogate",
    },
    "surface_loaded_bright_2021": {
        "core_n_real": 1.353,
        "membrane_n_real": 1.520,
        "corona_n_real": 1.330,
        "membrane_thickness_m": 12.0e-9,
        "corona_thickness_m": 0.0,
        "ionic_strength_M": 0.150,
        "edl_refractive_increment": 0.000,
        "min_core_radius_fraction": 0.25,
        "source_label": "van der Pol et al. 2021 bright EV shell scenario",
        "source_type": "direct literature scenario",
    },
}

BIOMIMETIC_EXOSOME_DEFAULTS = deepcopy(EXOSOME_MODEL_PRESETS["biomimetic_corona_nominal"])

EV_SEV_ENSEMBLE_PRESET_GROUPS = {
    "literature_bounds_2021": (
        "membrane_only_dim_2021",
        "membrane_only_nominal_2020",
        "biomimetic_corona_nominal",
        "surface_loaded_bright_2021",
    ),
}


def list_exosome_model_presets() -> list[str]:
    """Return the available literature-bounded exosome preset names."""
    return sorted(EXOSOME_MODEL_PRESETS.keys())


def list_ev_sev_ensemble_presets() -> list[str]:
    """Return deterministic EV/sEV ensemble preset group names."""
    return sorted(EV_SEV_ENSEMBLE_PRESET_GROUPS.keys())


def get_exosome_model_preset(preset_name: str = "biomimetic_corona_nominal") -> dict[str, Any]:
    """Return a copy of one exosome preset."""
    if preset_name not in EXOSOME_MODEL_PRESETS:
        raise ValueError(
            f"Unknown exosome preset '{preset_name}'. "
            f"Available: {list_exosome_model_presets()}"
        )
    return deepcopy(EXOSOME_MODEL_PRESETS[preset_name])


def _sphere_volume(radius_m: float) -> float:
    return 4.0 * np.pi * radius_m**3 / 3.0


def _debye_length_m(ionic_strength_M: float) -> float:
    """
    Debye length in water near room temperature.

    Uses lambda_D[nm] ~= 0.304 / sqrt(I[M]), a standard dilute-electrolyte
    approximation tabulated in interfacial-science texts such as Israelachvili.

    Important scope note:
        This controls only the thickness of the hydrated ionic atmosphere.
        The optical contrast assigned to the EDL is a separate surrogate term;
        zeta potential itself is not converted directly into a visible-frequency
        dielectric function.
    """
    ionic_strength_M = max(float(ionic_strength_M), 1e-9)
    return 0.304e-9 / np.sqrt(ionic_strength_M)


def equivalent_uniform_permittivity_core_shell(
    epsilon_core: complex,
    epsilon_shell: complex,
    epsilon_medium: complex,
    core_radius_ratio: float,
) -> complex:
    """
    Quasistatic equivalent permittivity of a coated sphere obtained by matching
    the exact dipole polarizability.

    This is the standard coated-sphere internal-homogenization relation used to
    report what uniform-sphere RI would reproduce the same dipole response.
    We use it for interpretation / comparison only; the actual scattering
    calculation still uses the exact coated-sphere Mie coefficients.
    """
    f = float(core_radius_ratio) ** 3
    numerator = (
        (epsilon_shell - epsilon_medium) * (epsilon_core + 2.0 * epsilon_shell)
        + f * (epsilon_core - epsilon_shell) * (epsilon_medium + 2.0 * epsilon_shell)
    )
    denominator = (
        (epsilon_shell + 2.0 * epsilon_medium) * (epsilon_core + 2.0 * epsilon_shell)
        + 2.0 * f * (epsilon_shell - epsilon_medium) * (epsilon_core - epsilon_shell)
    )
    if abs(denominator) < 1e-30:
        raise ValueError(
            "Maxwell-Garnett denominator near zero "
            f"(abs={abs(denominator):.3e}); dielectric configuration is at an "
            "effective-medium resonance."
        )
    beta = numerator / denominator
    return epsilon_medium * (1.0 + 2.0 * beta) / (1.0 - beta)


def build_biomimetic_exosome_core_shell(
    radius_m: float,
    medium_n: float,
    *,
    preset_name: str = "biomimetic_corona_nominal",
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a biomimetic exosome optical shell:
        aqueous core + membrane + protein corona + Debye-length hydrated ion layer.

    The membrane/corona/EDL are collapsed into one effective shell by volume-
    averaging their permittivities inside the total surface shell volume.

    Parameter mapping to literature:
        - Core-shell representation: standard EV optical-sizing approximation.
        - membrane_thickness_m, membrane_n_real:
            grounded in van der Pol et al. 2020/2021 EV core-shell models.
        - corona_thickness_m, corona_n_real:
            not a direct single-source measurement; chosen as a conservative
            protein-rich external layer because the 2023 protein-corona review
            shows Exos acquire soft/hard corona structures in biofluids.
        - ionic_strength_M and Debye-length EDL:
            motivated by the 2020 ACS Omega zeta-potential study showing that
            ionic strength/valency reshape EV double-layer-mediated stability.

    What this surrogate deliberately omits:
        - membrane anisotropy
        - nonspherical morphology
        - patchy / time-evolving corona composition
        - explicit charge-regulation electrodynamics
    """
    params = get_exosome_model_preset(preset_name)
    if overrides:
        params.update(overrides)

    outer_radius_m = float(radius_m)
    if outer_radius_m <= 0:
        raise ValueError(f"radius_m must be positive, got {radius_m}")

    membrane_thickness_m = float(params["membrane_thickness_m"])
    corona_thickness_m = float(params["corona_thickness_m"])
    edl_thickness_m = _debye_length_m(float(params["ionic_strength_M"]))
    surface_total_m = membrane_thickness_m + corona_thickness_m + edl_thickness_m

    max_surface_total_m = outer_radius_m * (
        1.0 - float(params["min_core_radius_fraction"])
    )
    if surface_total_m > max_surface_total_m:
        scale = max_surface_total_m / surface_total_m
        membrane_thickness_m *= scale
        corona_thickness_m *= scale
        edl_thickness_m *= scale
        surface_total_m *= scale

    r_edl_inner = outer_radius_m - edl_thickness_m
    r_corona_inner = r_edl_inner - corona_thickness_m
    core_radius_m = r_corona_inner - membrane_thickness_m

    epsilon_medium = complex(float(medium_n) ** 2, 0.0)
    epsilon_core = complex(float(params["core_n_real"]) ** 2, 0.0)
    epsilon_membrane = complex(float(params["membrane_n_real"]) ** 2, 0.0)
    epsilon_corona = complex(float(params["corona_n_real"]) ** 2, 0.0)
    epsilon_edl = complex(
        float(medium_n + float(params["edl_refractive_increment"])) ** 2,
        0.0,
    )

    shell_volume_m3 = _sphere_volume(outer_radius_m) - _sphere_volume(core_radius_m)
    volume_membrane_m3 = _sphere_volume(r_corona_inner) - _sphere_volume(core_radius_m)
    volume_corona_m3 = _sphere_volume(r_edl_inner) - _sphere_volume(r_corona_inner)
    volume_edl_m3 = _sphere_volume(outer_radius_m) - _sphere_volume(r_edl_inner)
    epsilon_shell = (
        volume_membrane_m3 * epsilon_membrane
        + volume_corona_m3 * epsilon_corona
        + volume_edl_m3 * epsilon_edl
    ) / shell_volume_m3

    core_radius_ratio = core_radius_m / outer_radius_m
    epsilon_equivalent = equivalent_uniform_permittivity_core_shell(
        epsilon_core,
        epsilon_shell,
        epsilon_medium,
        core_radius_ratio,
    )

    return {
        "structure_key": "exosome_biomimetic",
        "preset_name": str(preset_name),
        "outer_radius_m": outer_radius_m,
        "core_radius_m": core_radius_m,
        "core_radius_ratio": core_radius_ratio,
        "shell_thickness_m": surface_total_m,
        "membrane_thickness_m": membrane_thickness_m,
        "corona_thickness_m": corona_thickness_m,
        "edl_thickness_m": edl_thickness_m,
        "core_n_complex": np.sqrt(epsilon_core),
        "shell_n_complex": np.sqrt(epsilon_shell),
        "equivalent_uniform_n_complex": np.sqrt(epsilon_equivalent),
        "surface_volume_fraction": 1.0 - core_radius_ratio**3,
        "substructure": {
            "membrane_n_real": float(params["membrane_n_real"]),
            "corona_n_real": float(params["corona_n_real"]),
            "edl_n_real": float(np.sqrt(epsilon_edl).real),
            "volume_membrane_fraction_in_shell": float(volume_membrane_m3 / shell_volume_m3),
            "volume_corona_fraction_in_shell": float(volume_corona_m3 / shell_volume_m3),
            "volume_edl_fraction_in_shell": float(volume_edl_m3 / shell_volume_m3),
        },
        "params": params,
    }


def resolve_structured_particle_spec(
    particle: Particle,
    medium_n: float,
    wavelength_m: float,
) -> dict[str, Any]:
    """
    Resolve a structured particle description into solver-ready optical data.

    wavelength_m is kept in the signature for forward compatibility with future
    weakly dispersive structured-particle models.
    """
    _ = wavelength_m
    overrides = deepcopy(particle.structure_params or {})
    if particle.structure_key == "exosome_biomimetic":
        preset_name = str(overrides.pop("preset_name", "biomimetic_corona_nominal"))
        return build_biomimetic_exosome_core_shell(
            particle.radius_m,
            medium_n,
            preset_name=preset_name,
            overrides=overrides,
        )
    raise ValueError(
        f"Unknown structured particle key '{particle.structure_key}' for '{particle.name}'."
    )


def make_biomimetic_exosome_particle(
    diameter_nm: float,
    *,
    name: str | None = None,
    preset_name: str = "biomimetic_corona_nominal",
    overrides: dict[str, Any] | None = None,
) -> Particle:
    """Convenience factory for the biomimetic core-shell exosome surrogate."""
    diameter_nm = float(diameter_nm)
    rounded_nm = int(round(diameter_nm))
    structure_params = deepcopy(overrides) if overrides else {}
    structure_params["preset_name"] = preset_name
    return Particle(
        name=name or f"exosome_{preset_name}_{rounded_nm}nm",
        radius_m=diameter_nm * 1e-9 / 2.0,
        n_real=1.38,
        n_imag=0.0,
        model_type="mie_core_shell",
        structure_key="exosome_biomimetic",
        structure_params=structure_params,
    )


def make_biomimetic_exosome_ensemble_particles(
    diameter_nm: float,
    *,
    ensemble_name: str = "literature_bounds_2021",
) -> list[Particle]:
    """
    Expand one EV/sEV ensemble name into explicit deterministic preset cases.

    No hidden random sampling is performed. Each returned particle carries
    ensemble membership metadata so downstream reports can group or audit the
    expanded cases.
    """
    if ensemble_name not in EV_SEV_ENSEMBLE_PRESET_GROUPS:
        raise ValueError(
            f"Unknown EV/sEV ensemble '{ensemble_name}'. "
            f"Available: {list_ev_sev_ensemble_presets()}"
        )
    presets = EV_SEV_ENSEMBLE_PRESET_GROUPS[ensemble_name]
    particles: list[Particle] = []
    for index, preset_name in enumerate(presets):
        particles.append(
            make_biomimetic_exosome_particle(
                diameter_nm,
                name=(
                    f"exosome_{ensemble_name}_{index + 1:02d}_"
                    f"{preset_name}_{int(round(float(diameter_nm)))}nm"
                ),
                preset_name=preset_name,
                overrides={
                    "EV_ensemble_name": ensemble_name,
                    "EV_ensemble_member_index": index,
                    "EV_ensemble_member_count": len(presets),
                    "EV_ensemble_member_preset": preset_name,
                },
            )
        )
    return particles
