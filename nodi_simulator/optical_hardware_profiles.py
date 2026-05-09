"""Package-local optical objective profile schema and claim diagnostics."""

from __future__ import annotations

from dataclasses import dataclass

from .data_objects import OpticalSystem, SimulationConfig


@dataclass(frozen=True)
class ObjectiveProfile:
    objective_id: str
    magnification: float
    illumination_NA: float
    collection_NA: float | None
    immersion: str
    working_distance_mm: float | None
    coverglass_correction: str | None
    wavelength_transmission_band: tuple[float, float] | None
    nominal_waist_model: str
    bfp_mapping_status: str


OBJECTIVE_PROFILES: dict[str, ObjectiveProfile] = {
    "current_control": ObjectiveProfile(
        objective_id="current_control",
        magnification=20.0,
        illumination_NA=0.45,
        collection_NA=0.9,
        immersion="air_or_external_collection_surrogate",
        working_distance_mm=None,
        coverglass_correction=None,
        wavelength_transmission_band=(400e-9, 700e-9),
        nominal_waist_model="0.61_lambda_over_NA_surrogate",
        bfp_mapping_status="surrogate_not_measured",
    ),
    "moderate_upgrade": ObjectiveProfile(
        objective_id="moderate_upgrade",
        magnification=40.0,
        illumination_NA=0.65,
        collection_NA=0.9,
        immersion="air_or_water_candidate",
        working_distance_mm=None,
        coverglass_correction=None,
        wavelength_transmission_band=None,
        nominal_waist_model="candidate_schema_only",
        bfp_mapping_status="not_measured",
    ),
    "high_NA_test": ObjectiveProfile(
        objective_id="high_NA_test",
        magnification=60.0,
        illumination_NA=1.10,
        collection_NA=1.20,
        immersion="water_or_oil_high_NA_candidate",
        working_distance_mm=None,
        coverglass_correction=None,
        wavelength_transmission_band=None,
        nominal_waist_model="candidate_schema_only",
        bfp_mapping_status="not_measured",
    ),
    "large_spot_control": ObjectiveProfile(
        objective_id="large_spot_control",
        magnification=10.0,
        illumination_NA=0.25,
        collection_NA=0.9,
        immersion="air_candidate",
        working_distance_mm=None,
        coverglass_correction=None,
        wavelength_transmission_band=None,
        nominal_waist_model="candidate_schema_only",
        bfp_mapping_status="not_measured",
    ),
}


def get_objective_profile(objective_id: str) -> ObjectiveProfile:
    """Return a known objective profile by id, falling back to current control."""
    return OBJECTIVE_PROFILES.get(str(objective_id), OBJECTIVE_PROFILES["current_control"])


def build_objective_profile_diagnostics(
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """Export objective profile schema and claim-governance diagnostics."""
    profile = get_objective_profile(sim_cfg.objective_candidate_id)
    geometry = optical.resolve_illumination_geometry()
    waist_x = float(geometry["illumination_beam_waist_x_m"])
    waist_y = float(geometry["illumination_beam_waist_y_m"])
    waist_z = float(geometry["illumination_beam_waist_z_m"])
    illumination_waist_m = min(waist_x, waist_z)
    illumination_na = float(optical.illumination_NA or profile.illumination_NA)
    depth_of_focus_m = (
        2.0 * float(optical.wavelength_m) / max(illumination_na**2, 1e-18)
    )
    transit_time_s = waist_y / max(float(sim_cfg.mean_flow_velocity_m_s), 1e-18)
    lockin_margin_ratio = transit_time_s / max(float(sim_cfg.lockin_time_constant_s), 1e-18)
    if transit_time_s < 3.0 * float(sim_cfg.lockin_time_constant_s):
        lockin_bandwidth_margin = "risk"
    else:
        lockin_bandwidth_margin = "ok"

    if profile.working_distance_mm is None:
        working_distance = "not_configured_claim_blocker"
    elif profile.working_distance_mm <= 0:
        working_distance = "not_practical"
    else:
        working_distance = "declared_not_measured_against_chip"

    wavelength = float(optical.wavelength_m)
    band = profile.wavelength_transmission_band
    if band is None:
        transmission_status = "not_configured_by_wavelength"
    elif band[0] <= wavelength <= band[1]:
        transmission_status = "nominal_band_contains_wavelength"
    else:
        transmission_status = "wavelength_outside_nominal_profile_band"

    profile_known = str(sim_cfg.objective_candidate_id) in OBJECTIVE_PROFILES
    objective_gate_passed = bool(profile_known)
    return {
        "objective_candidate_id": profile.objective_id,
        "objective_candidate_requested_id": str(sim_cfg.objective_candidate_id),
        "objective_profile_schema_present": True,
        "objective_profile_known": profile_known,
        "objective_magnification": float(profile.magnification),
        "objective_illumination_NA": illumination_na,
        "objective_collection_NA": (
            float(optical.NA_collection)
            if optical.NA_collection is not None
            else profile.collection_NA
        ),
        "objective_immersion": profile.immersion,
        "objective_working_distance_mm": profile.working_distance_mm,
        "illumination_waist_m": illumination_waist_m,
        "illumination_waist_x_m": waist_x,
        "illumination_waist_y_m": waist_y,
        "illumination_waist_z_m": waist_z,
        "depth_of_focus_m": depth_of_focus_m,
        "objective_transit_time_s": transit_time_s,
        "lockin_bandwidth_margin": lockin_bandwidth_margin,
        "lockin_bandwidth_margin_ratio": lockin_margin_ratio,
        "position_sensitivity_score": min(1.0, illumination_na / 1.2),
        "working_distance_compatibility": working_distance,
        "objective_transmission_lambda_status": transmission_status,
        "objective_bfp_mapping_status": profile.bfp_mapping_status,
        "objective_design_claim_level": "single_profile_relative_only",
        "objective_cross_profile_claim_allowed": False,
        "objective_profile_gate_passed": objective_gate_passed,
        "objective_claim_blocker_summary": (
            "no_active_objective_panel_sweep / working_distance_not_measured / "
            "BFP_mapping_not_measured"
        ),
    }
