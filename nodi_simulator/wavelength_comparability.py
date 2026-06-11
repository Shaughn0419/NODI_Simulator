"""
Package-local wavelength comparability governance for hard gates.

The simulator often normalizes per wavelength so W/H geometry trends are
auditable within one lambda lane. That normalization does not by itself support
claims that one wavelength has higher real detector voltage, calibrated SNR, or
absolute LOD than another wavelength.

Blocked cross-wavelength statuses are guardrails. Report builders must not
rewrite them as 404-vs-660 absolute-winner or calibrated ranking claims.
"""

from __future__ import annotations

from collections.abc import Mapping

from .data_objects import Medium, OpticalSystem, SimulationConfig
from .materials import MATERIAL_DB, material_property_summary


WAVELENGTH_COMPARABILITY_DIAGNOSTIC_FIELDS = (
    "wavelength_lane_id",
    "wavelength_nm",
    "cross_wavelength_comparison_status",
    "wavelength_lane_calibration_complete",
    "wavelength_ratio_claim_level",
    "wavelength_ranking_claim_level",
    "medium_property_claim_level",
    "medium_property_status",
    "medium_optical_material_key",
    "medium_transport_material_key",
    "medium_thermal_material_key",
    "medium_n_real_at_lambda",
    "medium_n_imag_at_lambda",
    "medium_dn_dT",
    "medium_viscosity_Pa_s",
    "medium_density_kg_m3",
    "medium_thermal_conductivity_W_mK",
    "medium_thermal_diffusivity_m2_s",
    "medium_osmolarity_or_solute_fraction",
    "medium_material_source",
    "per_wavelength_normalization_active",
    "within_lambda_geometry_ranking_allowed",
    "absolute_or_calibrated_lambda_comparison_allowed",
    "cross_wavelength_claim_gate_passed",
    "laser_choice_claim_blocker",
    "lambda_score_comparability_band",
    "detector_responsivity_lambda_status",
    "objective_transmission_lambda_status",
    "laser_power_density_lambda_status",
    "reference_lambda_scaling_status",
)


def _lane_id(optical: OpticalSystem, sim_cfg: SimulationConfig) -> tuple[str, int]:
    wavelength_nm = int(round(float(optical.wavelength_m) * 1e9))
    configured_lane = getattr(sim_cfg, "wavelength_lane_id", None)
    lane_id = str(configured_lane).strip() if configured_lane else f"lambda_{wavelength_nm}nm"
    return lane_id, wavelength_nm


def _wavelength_map_has_lane(
    mapping: Mapping[object, object] | None,
    *,
    lane_id: str,
    wavelength_nm: int,
    wavelength_m: float,
) -> bool:
    if not mapping:
        return False
    candidate_keys = (
        lane_id,
        str(lane_id),
        wavelength_nm,
        str(wavelength_nm),
        f"{wavelength_nm}nm",
        wavelength_m,
        f"{wavelength_m:.12g}",
    )
    for key in candidate_keys:
        if key in mapping:
            value = mapping[key]
            if value is not None and value != "":
                return True
    return False


def _first_not_none(*values: object) -> object:
    for value in values:
        if value is not None:
            return value
    return None


def _resolve_medium_key(
    sim_cfg: SimulationConfig,
    medium: Medium | None,
    *,
    config_attr: str,
    medium_attr: str,
) -> str | None:
    config_value = getattr(sim_cfg, config_attr, None)
    if config_value:
        return str(config_value)
    if medium is not None:
        medium_specific = getattr(medium, medium_attr, None)
        if medium_specific:
            return str(medium_specific)
        if medium.material_key:
            return str(medium.material_key)
    return None


def _summary_for_key(material_key: str | None, wavelength_m: float) -> dict[str, object]:
    if not material_key or material_key not in MATERIAL_DB:
        return {}
    return material_property_summary(material_key, wavelength_m)


def _build_medium_property_diagnostics(
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    medium: Medium | None,
) -> dict[str, object]:
    wavelength_m = float(optical.wavelength_m)
    optical_key = _resolve_medium_key(
        sim_cfg,
        medium,
        config_attr="medium_optical_material_key",
        medium_attr="optical_material_key",
    )
    transport_key = _resolve_medium_key(
        sim_cfg,
        medium,
        config_attr="medium_transport_material_key",
        medium_attr="transport_material_key",
    )
    thermal_key = _resolve_medium_key(
        sim_cfg,
        medium,
        config_attr="medium_thermal_material_key",
        medium_attr="thermal_material_key",
    )

    optical_summary = _summary_for_key(optical_key, wavelength_m)
    transport_summary = _summary_for_key(transport_key or optical_key, wavelength_m)
    thermal_summary = _summary_for_key(thermal_key or optical_key, wavelength_m)

    n_real = optical_summary.get("n_real")
    n_imag = optical_summary.get("n_imag")
    if n_real is None and medium is not None:
        n_real = float(medium.refractive_index_at(wavelength_m))
        n_imag = 0.0

    viscosity = _first_not_none(
        getattr(medium, "viscosity_Pa_s", None) if medium is not None else None,
        transport_summary.get("viscosity_Pa_s"),
    )
    density = _first_not_none(
        getattr(medium, "density_kg_m3", None) if medium is not None else None,
        transport_summary.get("density_kg_m3"),
    )
    thermal_conductivity = _first_not_none(
        (
            getattr(medium, "thermal_conductivity_W_mK", None)
            if medium is not None
            else None
        ),
        thermal_summary.get("thermal_conductivity_W_mK"),
    )
    thermal_diffusivity = _first_not_none(
        (
            getattr(medium, "thermal_diffusivity_m2_s", None)
            if medium is not None
            else None
        ),
        thermal_summary.get("thermal_diffusivity_m2_s"),
    )
    dn_dT = _first_not_none(
        getattr(medium, "dn_dT", None) if medium is not None else None,
        thermal_summary.get("dn_dT"),
    )
    osmolarity = _first_not_none(
        (
            getattr(medium, "osmolarity_or_solute_fraction", None)
            if medium is not None
            else None
        ),
        transport_summary.get("osmolarity_or_solute_fraction"),
    )
    source = _first_not_none(
        getattr(medium, "source", None) if medium is not None else None,
        optical_summary.get("source"),
        transport_summary.get("source"),
        thermal_summary.get("source"),
    )
    claim_level = _first_not_none(
        getattr(medium, "claim_level", None) if medium is not None else None,
        optical_summary.get("claim_level"),
        transport_summary.get("claim_level"),
        thermal_summary.get("claim_level"),
    )

    required_values = (
        n_real,
        n_imag,
        dn_dT,
        viscosity,
        density,
        thermal_conductivity,
        thermal_diffusivity,
        source,
        claim_level,
    )
    property_complete = all(value is not None for value in required_values)
    if property_complete:
        status = "complete_nominal_material_property_metadata"
        resolved_claim_level = str(claim_level)
    elif optical_key or transport_key or thermal_key:
        status = "partial_material_property_metadata_missing_terms"
        resolved_claim_level = "nominal_visible_dispersion_only"
    else:
        status = "fixed_medium_index_without_material_property_metadata"
        resolved_claim_level = "fixed_medium_index_only"

    return {
        "medium_property_claim_level": resolved_claim_level,
        "medium_property_status": status,
        "medium_optical_material_key": optical_key,
        "medium_transport_material_key": transport_key,
        "medium_thermal_material_key": thermal_key,
        "medium_n_real_at_lambda": n_real,
        "medium_n_imag_at_lambda": n_imag,
        "medium_dn_dT": dn_dT,
        "medium_viscosity_Pa_s": viscosity,
        "medium_density_kg_m3": density,
        "medium_thermal_conductivity_W_mK": thermal_conductivity,
        "medium_thermal_diffusivity_m2_s": thermal_diffusivity,
        "medium_osmolarity_or_solute_fraction": osmolarity,
        "medium_material_source": source,
    }


def build_wavelength_comparability_diagnostics(
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    *,
    medium: Medium | None = None,
) -> dict[str, object]:
    """Return claim blockers for cross-wavelength ranking semantics."""
    lane_id, wavelength_nm = _lane_id(optical, sim_cfg)
    wavelength_m = float(optical.wavelength_m)
    per_wavelength_normalization_active = (
        str(sim_cfg.normalization_mode) == "per_wavelength"
    )
    probe_power_by_lambda = _wavelength_map_has_lane(
        getattr(sim_cfg, "probe_power_by_wavelength_W", None),
        lane_id=lane_id,
        wavelength_nm=wavelength_nm,
        wavelength_m=wavelength_m,
    )
    detector_responsivity_by_lambda = _wavelength_map_has_lane(
        getattr(sim_cfg, "detector_responsivity_by_wavelength", None),
        lane_id=lane_id,
        wavelength_nm=wavelength_nm,
        wavelength_m=wavelength_m,
    )
    filter_transmission_by_lambda = _wavelength_map_has_lane(
        getattr(sim_cfg, "filter_transmission_by_wavelength", None),
        lane_id=lane_id,
        wavelength_nm=wavelength_nm,
        wavelength_m=wavelength_m,
    )
    reference_calibration_by_lambda = _wavelength_map_has_lane(
        getattr(sim_cfg, "reference_calibration_by_wavelength", None),
        lane_id=lane_id,
        wavelength_nm=wavelength_nm,
        wavelength_m=wavelength_m,
    )
    wavelength_specific_chain_complete = all(
        (
            probe_power_by_lambda,
            detector_responsivity_by_lambda,
            filter_transmission_by_lambda,
            reference_calibration_by_lambda,
        )
    )
    probe_power_available = bool(
        sim_cfg.probe_power_W is not None or probe_power_by_lambda
    )
    detector_unit_chain_unlocked = bool(
        str(sim_cfg.absolute_throughput_route) == "calibrated_operator_table"
        and str(sim_cfg.photon_unit_noise_model) != "not_applied"
        and probe_power_available
    )
    missing_chain_inputs = [
        name
        for name, present in (
            ("detector_unit_chain", detector_unit_chain_unlocked),
            ("probe_power_by_wavelength_W", probe_power_by_lambda),
            ("detector_responsivity_by_wavelength", detector_responsivity_by_lambda),
            ("filter_transmission_by_wavelength", filter_transmission_by_lambda),
            ("reference_calibration_by_wavelength", reference_calibration_by_lambda),
        )
        if not present
    ]
    missing_chain_text = "_or_".join(missing_chain_inputs)

    absolute_allowed = bool(
        detector_unit_chain_unlocked and wavelength_specific_chain_complete
    )
    within_lambda_allowed = bool(per_wavelength_normalization_active)

    if absolute_allowed:
        status = "calibrated_cross_wavelength_comparison_allowed"
        claim_level = "calibrated_lambda_ranking_allowed"
        blocker = "none"
        band = "green"
        gate_passed = True
    elif per_wavelength_normalization_active:
        status = "blocked_cross_lambda_absolute_claim_with_per_wavelength_normalization"
        claim_level = "within_lambda_geometry_ranking_only"
        blocker = "per_wavelength_normalization_active_without_" + missing_chain_text
        band = "within_lambda_only"
        gate_passed = False
    else:
        status = "blocked_cross_lambda_absolute_claim_without_calibrated_detector_chain"
        claim_level = "normalized_simulator_trend_only"
        blocker = "missing_" + missing_chain_text
        band = "exploratory_only"
        gate_passed = False

    medium_properties = _build_medium_property_diagnostics(optical, sim_cfg, medium)
    return {
        "wavelength_lane_id": lane_id,
        "wavelength_nm": wavelength_nm,
        "cross_wavelength_comparison_status": status,
        "wavelength_lane_calibration_complete": absolute_allowed,
        "wavelength_ratio_claim_level": claim_level,
        "wavelength_ranking_claim_level": claim_level,
        **medium_properties,
        "per_wavelength_normalization_active": per_wavelength_normalization_active,
        "within_lambda_geometry_ranking_allowed": within_lambda_allowed,
        "absolute_or_calibrated_lambda_comparison_allowed": absolute_allowed,
        "cross_wavelength_claim_gate_passed": gate_passed,
        "laser_choice_claim_blocker": blocker,
        "lambda_score_comparability_band": band,
        "detector_responsivity_lambda_status": (
            "configured_by_wavelength"
            if detector_responsivity_by_lambda
            else "not_configured_by_wavelength"
        ),
        "objective_transmission_lambda_status": (
            "configured_by_wavelength"
            if filter_transmission_by_lambda
            else "not_configured_by_wavelength"
        ),
        "laser_power_density_lambda_status": (
            "configured_by_wavelength"
            if probe_power_by_lambda
            else "single_probe_power_metadata_only"
            if sim_cfg.probe_power_W is not None
            else "not_configured_by_wavelength"
        ),
        "reference_lambda_scaling_status": (
            "configured_by_wavelength"
            if reference_calibration_by_lambda
            else "per_wavelength_relative_reference_scaling"
            if per_wavelength_normalization_active
            else "global_or_legacy_reference_scaling_not_calibrated"
        ),
    }
