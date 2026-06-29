"""Channel-geometry diagnostics and package-local cross-section surrogates."""

from __future__ import annotations

import math

from .cross_section_geometry import (
    CENTER_ACCESSIBLE_SUPPORT_MODEL,
    DEFAULT_CLOSURE_POLICY,
    TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION,
    TRAPEZOID_WALL_DISTANCE_MODEL,
    TrapezoidCrossSection,
)
from .data_objects import (
    CHANNEL_CROSS_SECTION_MODEL_OPTIONS,
    Channel,
    OpticalSystem,
    Particle,
    SimulationConfig,
)
from .type_coerce import positive_ratio as _ratio


CHANNEL_GEOMETRY_DIAGNOSTIC_FIELDS = (
    "channel_cross_section_model",
    "sidewall_taper_angle_deg",
    "corner_radius_nm",
    "surface_roughness_rms_nm",
    "width_along_channel_cv",
    "depth_along_channel_cv",
    "measured_profile_path",
    "measured_profile_configured",
    "measured_profile_loaded",
    "measured_profile_validated",
    "measured_profile_sha256",
    "measured_profile_runtime_status",
    "ideal_accessible_area_m2",
    "ideal_phase_mask_area_m2",
    "effective_accessible_area_m2",
    "effective_phase_mask_area_m2",
    "effective_to_ideal_accessible_area_ratio",
    "effective_to_ideal_phase_mask_area_ratio",
    "trapezoid_top_width_m",
    "trapezoid_depth_m",
    "trapezoid_bottom_width_m",
    "trapezoid_bottom_width_unclipped_m",
    "trapezoid_bottom_width_runtime_clipped_m",
    "trapezoid_closure_depth_m",
    "trapezoid_closure_status",
    "trapezoid_closure_policy",
    "trapezoid_runtime_guard_status",
    "trapezoid_center_accessible_area_m2",
    "trapezoid_center_accessible_area_fraction",
    "center_accessible_support_model",
    "channel_geometry_wall_distance_model",
    "channel_geometry_wall_distance_claim_level",
    "cross_section_geometry_version",
    "geometry_surrogate_status",
    "geometry_model_discrepancy_flag",
    "roughness_scattering_background_proxy",
    "geometry_claim_level",
    "channel_geometry_diagnostic_gate_passed",
)


def _getattr_float(sim_cfg: SimulationConfig, name: str, default: float) -> float:
    value = getattr(sim_cfg, name, default)
    if value is None:
        return default
    return float(value)


def _getattr_str(sim_cfg: SimulationConfig, name: str, default: str) -> str:
    value = getattr(sim_cfg, name, default)
    if value is None:
        return default
    return str(value)


def _ideal_accessible_area_m2(channel: Channel, particle_radius_m: float) -> float:
    accessible_width_m = max(float(channel.width_m) - 2.0 * particle_radius_m, 0.0)
    accessible_depth_m = max(float(channel.depth_m) - 2.0 * particle_radius_m, 0.0)
    return accessible_width_m * accessible_depth_m


def _rounded_rectangle_area_m2(
    width_m: float,
    depth_m: float,
    corner_radius_m: float,
) -> float:
    radius_m = max(0.0, min(corner_radius_m, 0.5 * min(width_m, depth_m)))
    return max(width_m * depth_m - (4.0 - math.pi) * radius_m**2, 0.0)


def _trapezoid_widths_m(
    channel: Channel,
    sidewall_taper_angle_deg: float,
) -> tuple[float, float]:
    geometry = TrapezoidCrossSection(
        top_width_m=float(channel.width_m),
        depth_m=float(channel.depth_m),
        sidewall_taper_angle_deg=sidewall_taper_angle_deg,
    )
    return geometry.top_width_m, geometry.bottom_width_runtime_clipped_m


def _trapezoid_area_m2(
    top_width_m: float,
    bottom_width_m: float,
    depth_m: float,
) -> float:
    return max(0.5 * (top_width_m + bottom_width_m) * max(depth_m, 0.0), 0.0)


def build_channel_geometry_diagnostics(
    particle: Particle,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """Export cross-section geometry diagnostics and ideal-rectangle discrepancy."""
    model = _getattr_str(sim_cfg, "channel_cross_section_model", "ideal_rectangle")
    sidewall_taper_angle_deg = _getattr_float(
        sim_cfg,
        "sidewall_taper_angle_deg",
        0.0,
    )
    corner_radius_nm = _getattr_float(sim_cfg, "corner_radius_nm", 0.0)
    roughness_rms_nm = _getattr_float(sim_cfg, "surface_roughness_rms_nm", 0.0)
    width_cv = _getattr_float(sim_cfg, "width_along_channel_cv", 0.0)
    depth_cv = _getattr_float(sim_cfg, "depth_along_channel_cv", 0.0)
    measured_profile_path = getattr(sim_cfg, "measured_profile_path", None)
    measured_profile_configured = bool(measured_profile_path)
    measured_profile_loaded = False
    measured_profile_validated = False
    measured_profile_sha256 = ""
    measured_profile_runtime_status = "not_requested"

    radius_m = float(particle.radius_m)
    ideal_phase_mask_area_m2 = float(channel.width_m) * float(channel.depth_m)
    ideal_accessible_area_m2 = _ideal_accessible_area_m2(channel, radius_m)
    effective_accessible_area_m2 = ideal_accessible_area_m2
    effective_phase_mask_area_m2 = ideal_phase_mask_area_m2
    trapezoid_top_width_m: float | None = None
    trapezoid_depth_m: float | None = None
    trapezoid_bottom_width_m: float | None = None
    trapezoid_bottom_width_unclipped_m: float | None = None
    trapezoid_bottom_width_runtime_clipped_m: float | None = None
    trapezoid_closure_depth_m: float | None = None
    trapezoid_closure_status: str | None = None
    trapezoid_closure_policy: str | None = None
    trapezoid_runtime_guard_status: str | None = None
    trapezoid_center_accessible_area_m2: float | None = None
    trapezoid_center_accessible_area_fraction: float | None = None
    center_accessible_support_model = "rectangular_half_span_v1"
    channel_geometry_wall_distance_model = "rectangular_half_span_gap_v1"
    channel_geometry_wall_distance_claim_level = (
        "geometry_distance_primitive_not_hindered_diffusion"
    )
    cross_section_geometry_version = "ideal_rectangle_v1"
    geometry_surrogate_status = "ideal_rectangle_no_active_surrogate"

    if model == "rounded_rectangle":
        cross_section_geometry_version = "rounded_rectangle_area_surrogate_v1"
        corner_radius_m = corner_radius_nm * 1e-9
        effective_phase_mask_area_m2 = _rounded_rectangle_area_m2(
            float(channel.width_m),
            float(channel.depth_m),
            corner_radius_m,
        )
        accessible_width_m = max(float(channel.width_m) - 2.0 * radius_m, 0.0)
        accessible_depth_m = max(float(channel.depth_m) - 2.0 * radius_m, 0.0)
        accessible_corner_radius_m = max(corner_radius_m - radius_m, 0.0)
        effective_accessible_area_m2 = _rounded_rectangle_area_m2(
            accessible_width_m,
            accessible_depth_m,
            accessible_corner_radius_m,
        )
        geometry_surrogate_status = "rounded_rectangle_area_surrogate_active"
    elif model == "trapezoid_tapered_sidewalls":
        trapezoid_geometry = TrapezoidCrossSection(
            top_width_m=float(channel.width_m),
            depth_m=float(channel.depth_m),
            sidewall_taper_angle_deg=sidewall_taper_angle_deg,
        )
        trapezoid_top_width_m = trapezoid_geometry.top_width_m
        trapezoid_depth_m = trapezoid_geometry.depth_m
        trapezoid_bottom_width_unclipped_m = (
            trapezoid_geometry.bottom_width_unclipped_m
        )
        trapezoid_bottom_width_runtime_clipped_m = (
            trapezoid_geometry.bottom_width_runtime_clipped_m
        )
        # Backwards-compatible alias: legacy consumers expect the clipped value here.
        trapezoid_bottom_width_m = trapezoid_bottom_width_runtime_clipped_m
        trapezoid_closure_depth_m = trapezoid_geometry.closure_depth_m
        trapezoid_closure_status = trapezoid_geometry.closure_status
        trapezoid_closure_policy = DEFAULT_CLOSURE_POLICY
        if trapezoid_closure_status == "geometry_closed":
            trapezoid_runtime_guard_status = "validation_guard"
        elif trapezoid_closure_status == "near_closed":
            trapezoid_runtime_guard_status = "solver_guard"
        else:
            trapezoid_runtime_guard_status = "none"
        effective_phase_mask_area_m2 = trapezoid_geometry.phase_mask_area_m2()
        trapezoid_center_accessible_area_m2 = (
            trapezoid_geometry.center_accessible_area_m2(radius_m)
        )
        effective_accessible_area_m2 = trapezoid_center_accessible_area_m2
        trapezoid_center_accessible_area_fraction = _ratio(
            trapezoid_center_accessible_area_m2,
            effective_phase_mask_area_m2,
        )
        center_accessible_support_model = CENTER_ACCESSIBLE_SUPPORT_MODEL
        channel_geometry_wall_distance_model = TRAPEZOID_WALL_DISTANCE_MODEL
        cross_section_geometry_version = TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION
        geometry_surrogate_status = "trapezoid_sidewall_area_surrogate_active"

    if model == "ideal_rectangle":
        discrepancy = "ideal_rectangle_assumed_measured_profile_unavailable"
        claim_level = "nominal_ideal_rectangle_geometry_only"
    elif model == "measured_profile_lookup" and not measured_profile_configured:
        discrepancy = "blocked_measured_profile_path_missing"
        claim_level = "blocked_missing_measured_profile"
        geometry_surrogate_status = "measured_profile_lookup_blocked_missing_path"
        measured_profile_runtime_status = "blocked_missing_profile_path"
    elif model == "rounded_rectangle":
        discrepancy = "active_rounded_rectangle_surrogate_deviates_from_ideal_rectangle"
        claim_level = "active_parameterized_geometry_surrogate_not_measured"
    elif model == "trapezoid_tapered_sidewalls":
        discrepancy = "active_trapezoid_sidewall_surrogate_deviates_from_ideal_rectangle"
        claim_level = "active_parameterized_geometry_surrogate_not_measured"
    elif model == "measured_profile_lookup":
        discrepancy = "measured_profile_lookup_configured_not_loaded_or_validated"
        claim_level = "blocked_measured_profile_not_loaded_or_validated"
        geometry_surrogate_status = (
            "measured_profile_lookup_metadata_only_not_loaded_or_validated"
        )
        measured_profile_runtime_status = "blocked_profile_not_loaded_or_validated"
    elif model in CHANNEL_CROSS_SECTION_MODEL_OPTIONS:
        discrepancy = "configured_geometry_model_not_loaded_in_p1_surrogate"
        claim_level = "parameterized_geometry_surrogate_not_measured"
        geometry_surrogate_status = "parameterized_geometry_metadata_only"
    else:
        discrepancy = "blocked_unknown_channel_cross_section_model"
        claim_level = "blocked_unknown_geometry_model"
        geometry_surrogate_status = "blocked_unknown_geometry_model"

    roughness_m = roughness_rms_nm * 1e-9
    roughness_proxy = (
        (roughness_m / max(float(optical.wavelength_m), 1e-30)) ** 2
        if roughness_m > 0.0
        else 0.0
    )
    gate_passed = bool(
        model in CHANNEL_CROSS_SECTION_MODEL_OPTIONS
        and model != "measured_profile_lookup"
    )

    return {
        "channel_cross_section_model": model,
        "sidewall_taper_angle_deg": sidewall_taper_angle_deg,
        "corner_radius_nm": corner_radius_nm,
        "surface_roughness_rms_nm": roughness_rms_nm,
        "width_along_channel_cv": width_cv,
        "depth_along_channel_cv": depth_cv,
        "measured_profile_path": measured_profile_path,
        "measured_profile_configured": measured_profile_configured,
        "measured_profile_loaded": measured_profile_loaded,
        "measured_profile_validated": measured_profile_validated,
        "measured_profile_sha256": measured_profile_sha256,
        "measured_profile_runtime_status": measured_profile_runtime_status,
        "ideal_accessible_area_m2": ideal_accessible_area_m2,
        "ideal_phase_mask_area_m2": ideal_phase_mask_area_m2,
        "effective_accessible_area_m2": effective_accessible_area_m2,
        "effective_phase_mask_area_m2": effective_phase_mask_area_m2,
        "effective_to_ideal_accessible_area_ratio": _ratio(
            effective_accessible_area_m2,
            ideal_accessible_area_m2,
        ),
        "effective_to_ideal_phase_mask_area_ratio": _ratio(
            effective_phase_mask_area_m2,
            ideal_phase_mask_area_m2,
        ),
        "trapezoid_top_width_m": trapezoid_top_width_m,
        "trapezoid_depth_m": trapezoid_depth_m,
        "trapezoid_bottom_width_m": trapezoid_bottom_width_m,
        "trapezoid_bottom_width_unclipped_m": trapezoid_bottom_width_unclipped_m,
        "trapezoid_bottom_width_runtime_clipped_m": (
            trapezoid_bottom_width_runtime_clipped_m
        ),
        "trapezoid_closure_depth_m": trapezoid_closure_depth_m,
        "trapezoid_closure_status": trapezoid_closure_status,
        "trapezoid_closure_policy": trapezoid_closure_policy,
        "trapezoid_runtime_guard_status": trapezoid_runtime_guard_status,
        "trapezoid_center_accessible_area_m2": trapezoid_center_accessible_area_m2,
        "trapezoid_center_accessible_area_fraction": (
            trapezoid_center_accessible_area_fraction
        ),
        "center_accessible_support_model": center_accessible_support_model,
        "channel_geometry_wall_distance_model": channel_geometry_wall_distance_model,
        "channel_geometry_wall_distance_claim_level": (
            channel_geometry_wall_distance_claim_level
        ),
        "cross_section_geometry_version": cross_section_geometry_version,
        "geometry_surrogate_status": geometry_surrogate_status,
        "geometry_model_discrepancy_flag": discrepancy,
        "roughness_scattering_background_proxy": roughness_proxy,
        "geometry_claim_level": claim_level,
        "channel_geometry_diagnostic_gate_passed": gate_passed,
    }
