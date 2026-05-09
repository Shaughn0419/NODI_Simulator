"""Package-local particle design metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass
from collections.abc import Mapping
from types import MappingProxyType
from typing import Literal

import numpy as np

from .data_objects import Particle, SimulationConfig


EV_SHAPE_MODEL_OPTIONS = (
    "sphere",
    "spheroid_orientation_average",
)


@dataclass(frozen=True)
class StandardParticleSpec:
    preset_id: str
    family: str
    diameter_nm: float
    refractive_index_class: str
    calibration_role: Literal["fit", "validation", "challenge"]
    traceability_status: str
    transfer_to_ev_risk: str


STANDARD_PARTICLE_PRESETS: Mapping[str, StandardParticleSpec] = MappingProxyType({
    "polystyrene_50nm": StandardParticleSpec(
        "polystyrene_50nm",
        "polystyrene",
        50.0,
        "high_RI_polymer",
        "fit",
        "commercial_size_standard_nominal",
        "high_material_mismatch_to_EV",
    ),
    "polystyrene_100nm": StandardParticleSpec(
        "polystyrene_100nm",
        "polystyrene",
        100.0,
        "high_RI_polymer",
        "validation",
        "commercial_size_standard_nominal",
        "high_material_mismatch_to_EV",
    ),
    "silica_50nm": StandardParticleSpec(
        "silica_50nm",
        "silica",
        50.0,
        "moderate_RI_inorganic",
        "validation",
        "commercial_size_standard_nominal",
        "moderate_material_mismatch_to_EV",
    ),
    "silica_100nm": StandardParticleSpec(
        "silica_100nm",
        "silica",
        100.0,
        "moderate_RI_inorganic",
        "challenge",
        "commercial_size_standard_nominal",
        "moderate_material_mismatch_to_EV",
    ),
    "liposome_100nm_low_RI": StandardParticleSpec(
        "liposome_100nm_low_RI",
        "liposome",
        100.0,
        "low_RI_soft_particle",
        "challenge",
        "EV_like",
        "moderate_EV_mimic_but_batch_sensitive",
    ),
    "hollow_organosilica_EV_mimic": StandardParticleSpec(
        "hollow_organosilica_EV_mimic",
        "hollow_organosilica",
        100.0,
        "EV_mimic_core_shell",
        "challenge",
        "research_mimic_not_primary_calibrator",
        "lower_material_mismatch_but_not_biological_EV",
    ),
})

PARTICLE_CONTAMINANT_PRESETS = {
    "HDL_like": {
        "family": "lipoprotein",
        "diameter_nm": 10.0,
        "RI_class": "low_RI_soft_particle",
        "detectability_score": 0.20,
    },
    "LDL_like": {
        "family": "lipoprotein",
        "diameter_nm": 25.0,
        "RI_class": "low_RI_soft_particle",
        "detectability_score": 0.35,
    },
    "VLDL_like": {
        "family": "lipoprotein",
        "diameter_nm": 55.0,
        "RI_class": "low_RI_soft_particle",
        "detectability_score": 0.55,
    },
    "chylomicron_like": {
        "family": "lipoprotein",
        "diameter_nm": 120.0,
        "RI_class": "low_RI_soft_particle",
        "detectability_score": 0.70,
    },
    "liposome_like": {
        "family": "liposome",
        "diameter_nm": 100.0,
        "RI_class": "low_RI_soft_particle",
        "detectability_score": 0.55,
    },
    "LNP_like": {
        "family": "lipid_nanoparticle",
        "diameter_nm": 80.0,
        "RI_class": "low_RI_soft_particle",
        "detectability_score": 0.50,
    },
    "PEG_polymer_aggregate": {
        "family": "polymer_aggregate",
        "diameter_nm": 80.0,
        "RI_class": "moderate_RI_polymer",
        "detectability_score": 0.60,
    },
    "protein_aggregate": {
        "family": "protein_aggregate",
        "diameter_nm": 50.0,
        "RI_class": "moderate_RI_biopolymer",
        "detectability_score": 0.45,
    },
    "salt_crystal_dust": {
        "family": "salt_crystal",
        "diameter_nm": 80.0,
        "RI_class": "moderate_RI_inorganic",
        "detectability_score": 0.65,
    },
    "silica_dust": {
        "family": "silica_dust",
        "diameter_nm": 100.0,
        "RI_class": "moderate_RI_inorganic",
        "detectability_score": 0.75,
    },
    "nanobubble": {
        "family": "nanobubble",
        "diameter_nm": 120.0,
        "RI_class": "low_RI_void",
        "detectability_score": 0.30,
    },
    "cell_debris": {
        "family": "cell_debris",
        "diameter_nm": 250.0,
        "RI_class": "heterogeneous_biological_debris",
        "detectability_score": 0.85,
    },
    "OMV_like": {
        "family": "outer_membrane_vesicle",
        "diameter_nm": 100.0,
        "RI_class": "EV_like_biological_particle",
        "detectability_score": 0.70,
    },
    "virus_like": {
        "family": "virus_like_particle",
        "diameter_nm": 90.0,
        "RI_class": "EV_like_biological_particle",
        "detectability_score": 0.65,
    },
    "column_resin_particle": {
        "family": "resin_particle",
        "diameter_nm": 150.0,
        "RI_class": "high_RI_polymer",
        "detectability_score": 0.90,
    },
    "polystyrene_contaminant": {
        "family": "polystyrene_contaminant",
        "diameter_nm": 100.0,
        "RI_class": "high_RI_polymer",
        "detectability_score": 0.95,
    },
}

EV_SAMPLE_PREPARATION_PROFILES = {
    "unknown": {"EV_model_weight": 1.0, "bias_status": "unresolved_sample_prep"},
    "SEC": {"EV_model_weight": 0.9, "bias_status": "size_exclusion_metadata_only"},
    "IEX": {"EV_model_weight": 0.85, "bias_status": "charge_selection_metadata_only"},
    "UF": {"EV_model_weight": 0.75, "bias_status": "size_cutoff_metadata_only"},
    "UC": {"EV_model_weight": 0.7, "bias_status": "pelleting_bias_metadata_only"},
    "PEG": {"EV_model_weight": 0.6, "bias_status": "polymer_precipitation_bias_metadata_only"},
}

PARTICLE_DESIGN_LIBRARY_DIAGNOSTIC_FIELDS = (
    "shape_model",
    "aspect_ratio",
    "orientation_average_status",
    "shape_scattering_factor",
    "anchor_particle_uncertainty_status",
    "au20_anchor_signal_p10",
    "au20_anchor_signal_p50",
    "au20_anchor_signal_p90",
    "standard_particle_family",
    "standard_particle_RI_class",
    "standard_particle_traceability_status",
    "standard_particle_calibration_role",
    "calibration_train_or_validation_split",
    "calibration_transfer_to_EV_risk",
    "contaminant_panel_coverage_status",
    "contaminant_preset_count",
    "contaminant_family",
    "contaminant_detectability_score",
    "EV_to_contaminant_signal_overlap",
    "EV_specificity_risk",
    "EV_sample_preparation_profile",
    "EV_model_weight",
)


def _name_tokens(name: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", name.lower()) if token}


def _particle_family(particle: Particle) -> str:
    name = particle.name.lower()
    name_parts = _name_tokens(name)
    if "gold" in name_parts or particle.material_key == "gold":
        return "gold"
    if "polystyrene" in name:
        return "polystyrene"
    if "silica" in name:
        return "silica"
    if "liposome" in name:
        return "liposome"
    if "lnp" in name or "lipid_nanoparticle" in name:
        return "lipid_nanoparticle"
    if "ldl" in name:
        return "lipoprotein"
    if "hdl" in name or "vldl" in name or "chylomicron" in name:
        return "lipoprotein"
    if "protein" in name:
        return "protein_aggregate"
    if "peg" in name or "polymer" in name:
        return "polymer_aggregate"
    if "salt" in name or "crystal" in name:
        return "salt_crystal"
    if "nanobubble" in name:
        return "nanobubble"
    if "debris" in name:
        return "cell_debris"
    if "omv" in name:
        return "outer_membrane_vesicle"
    if "virus" in name:
        return "virus_like_particle"
    if "resin" in name or "column" in name:
        return "resin_particle"
    if (
        "exosome" in name_parts
        or "ev" in name_parts
        or "sev" in name_parts
        or particle.model_type == "mie_core_shell"
    ):
        return "EV_sEV"
    return "unknown"


def _shape_metadata(particle: Particle) -> tuple[str, float, str, float]:
    params = particle.structure_params or {}
    aspect_ratio = float(params.get("aspect_ratio", 1.0))
    if _particle_family(particle) == "EV_sEV" and not np.isclose(aspect_ratio, 1.0):
        shape_model = "spheroid_orientation_average"
        factor = float((2.0 + aspect_ratio) / (3.0 * max(aspect_ratio, 1e-9)))
        return shape_model, aspect_ratio, "rayleigh_depolarization_surrogate", factor
    return "sphere", aspect_ratio, "not_applied_spherical_surrogate", 1.0


def _standard_spec_for_particle(particle: Particle) -> StandardParticleSpec | None:
    name = particle.name
    if name in STANDARD_PARTICLE_PRESETS:
        return STANDARD_PARTICLE_PRESETS[name]
    diameter_nm = round(float(2.0 * particle.radius_m * 1e9))
    family = _particle_family(particle)
    key = f"{family}_{diameter_nm}nm"
    return STANDARD_PARTICLE_PRESETS.get(key)


def _anchor_payload(particle: Particle) -> dict[str, object]:
    if _particle_family(particle) != "gold":
        return {
            "anchor_particle_uncertainty_status": "not_anchor_particle",
            "au20_anchor_signal_p10": None,
            "au20_anchor_signal_p50": None,
            "au20_anchor_signal_p90": None,
        }
    diameter_nm = float(2.0 * particle.radius_m * 1e9)
    relative_signal = (diameter_nm / 20.0) ** 6
    cv = 0.15
    return {
        "anchor_particle_uncertainty_status": (
            "nominal_gold_anchor_size_cv_and_ligand_shell_metadata"
        ),
        "au20_anchor_signal_p10": float(relative_signal * (1.0 - cv)),
        "au20_anchor_signal_p50": float(relative_signal),
        "au20_anchor_signal_p90": float(relative_signal * (1.0 + cv)),
    }


def _contaminant_detectability_score(family: str, is_ev: bool) -> float:
    if is_ev:
        return 0.5
    scores = [
        float(item["detectability_score"])
        for item in PARTICLE_CONTAMINANT_PRESETS.values()
        if item["family"] == family
    ]
    if scores:
        return float(max(scores))
    return 0.0


def build_particle_design_library_diagnostics(
    particle: Particle,
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """Build P0 particle library metadata for one simulation row."""
    family = _particle_family(particle)
    shape_model, aspect_ratio, orientation_status, shape_factor = _shape_metadata(
        particle
    )
    standard = _standard_spec_for_particle(particle)
    contaminant_family = family if family in {
        item["family"] for item in PARTICLE_CONTAMINANT_PRESETS.values()
    } else None
    is_ev = family == "EV_sEV"
    contaminant_score = _contaminant_detectability_score(family, is_ev)
    if contaminant_family is not None:
        overlap = contaminant_score
        specificity_risk = "contaminant_control_particle"
    elif is_ev:
        overlap = 0.5
        specificity_risk = "proxy_overlap_requires_contaminant_panel"
    else:
        overlap = 0.0
        specificity_risk = "not_ev_specificity_target"
    prep = EV_SAMPLE_PREPARATION_PROFILES[str(sim_cfg.EV_sample_preparation_profile)]

    payload = {
        "shape_model": shape_model,
        "aspect_ratio": aspect_ratio,
        "orientation_average_status": orientation_status,
        "shape_scattering_factor": shape_factor,
        "standard_particle_family": None,
        "standard_particle_RI_class": None,
        "standard_particle_traceability_status": None,
        "standard_particle_calibration_role": None,
        "calibration_train_or_validation_split": "not_applicable",
        "calibration_transfer_to_EV_risk": None,
        "contaminant_panel_coverage_status": "expanded_screening_panel_metadata_only",
        "contaminant_preset_count": len(PARTICLE_CONTAMINANT_PRESETS),
        "contaminant_family": contaminant_family,
        "contaminant_detectability_score": contaminant_score,
        "EV_to_contaminant_signal_overlap": overlap,
        "EV_specificity_risk": specificity_risk,
        "EV_sample_preparation_profile": str(sim_cfg.EV_sample_preparation_profile),
        "EV_model_weight": float(prep["EV_model_weight"]),
    }
    payload.update(_anchor_payload(particle))
    if standard is not None:
        payload.update(
            {
                "standard_particle_family": standard.family,
                "standard_particle_RI_class": standard.refractive_index_class,
                "standard_particle_traceability_status": standard.traceability_status,
                "standard_particle_calibration_role": standard.calibration_role,
                "calibration_train_or_validation_split": standard.calibration_role,
                "calibration_transfer_to_EV_risk": standard.transfer_to_ev_risk,
            }
        )
    return payload
