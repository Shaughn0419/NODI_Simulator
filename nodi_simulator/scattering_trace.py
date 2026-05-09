"""
Package-local scattering field trace module for NODI interferometric simulation.

Combines intrinsic scattering (already normalized), illumination envelope,
spatial coupling, and phase to produce E_sca(t) along the particle trajectory.

E_sca(t) = A_env(t) · E_sca_unit_normalized · f_coupling(t) · e^{iφ(t)}

Models for spatial_coupling_factor:
    - "constant": f = 1.0
    - "gaussian_xy": f = exp(-(x/wcx)² - (z/wcz)²)
"""

import numpy as np

from .data_objects import (
    Channel,
    OpticalSystem,
    DEFAULT_PATH_OPD_MODEL,
    DEFAULT_PATH_OPD_REFERENCE_PLANE,
    DEFAULT_PATH_OPD_Z_GEOMETRY_FACTOR,
)


def _wrap_to_pi(phase_rad: np.ndarray | float) -> np.ndarray:
    """Wrap phase values into [-pi, pi)."""
    phase_arr = np.asarray(phase_rad, dtype=float)
    return (phase_arr + np.pi) % (2.0 * np.pi) - np.pi


def _surrogate_focus_crossing_phase(
    y_m: np.ndarray,
    optical: OpticalSystem,
    medium_refractive_index: float,
) -> np.ndarray:
    """
    Surrogate focus-crossing phase along the flow axis.

    This is intentionally not called Gouy phase. In the simulator coordinate
    system, y is the flow direction rather than the optical propagation axis.
    The term simply captures the sign-changing phase trend as the particle
    crosses the focal region.
    """
    illumination_geometry = optical.resolve_illumination_geometry()
    w_eff = float(
        np.sqrt(
            float(illumination_geometry["illumination_beam_waist_x_m"])
            * float(illumination_geometry["illumination_beam_waist_z_m"])
        )
    )
    z_rayleigh = np.pi * medium_refractive_index * (w_eff ** 2) / optical.wavelength_m
    z_rayleigh = max(z_rayleigh, optical.wavelength_m)
    return np.arctan((np.asarray(y_m, dtype=float) - optical.focus_y_m) / z_rayleigh)


def _resolve_path_opd_diagnostics(path_opd_model: str) -> dict[str, object]:
    """Resolve OPD surrogate geometry and default-freeze diagnostics."""
    if path_opd_model == DEFAULT_PATH_OPD_MODEL:
        return {
            "path_reference_plane": DEFAULT_PATH_OPD_REFERENCE_PLANE,
            "path_z_geometry_factor": float(DEFAULT_PATH_OPD_Z_GEOMETRY_FACTOR),
            "path_z_reference_mode": "focus_centered_single_pass",
            "path_opd_default_model": DEFAULT_PATH_OPD_MODEL,
            "path_opd_model_role": "default_frozen_mainline",
            "path_opd_default_frozen": True,
            "path_opd_freeze_status": "default_frozen_active",
        }
    if path_opd_model == "reference_plane_roundtrip_surrogate":
        return {
            "path_reference_plane": "channel_center_reference_plane_roundtrip_surrogate",
            "path_z_geometry_factor": 2.0,
            "path_z_reference_mode": "focus_centered_roundtrip_like",
            "path_opd_default_model": DEFAULT_PATH_OPD_MODEL,
            "path_opd_model_role": "diagnostic_review_alternative",
            "path_opd_default_frozen": False,
            "path_opd_freeze_status": "alternative_review_mode",
        }
    if path_opd_model == "wall_referenced_gap_surrogate":
        return {
            "path_reference_plane": "nearest_channel_wall_centered_gap_surrogate",
            "path_z_geometry_factor": 1.0,
            "path_z_reference_mode": "nearest_wall_gap_centered_about_channel_midplane",
            "path_opd_default_model": DEFAULT_PATH_OPD_MODEL,
            "path_opd_model_role": "diagnostic_review_alternative",
            "path_opd_default_frozen": False,
            "path_opd_freeze_status": "alternative_review_mode",
        }
    raise ValueError(
        "path_opd_model must be 'single_pass', "
        "'reference_plane_roundtrip_surrogate', or "
        f"'wall_referenced_gap_surrogate', got {path_opd_model}"
    )


def spatial_coupling_factor(
    x0_m: float | np.ndarray,
    z0_m: float | np.ndarray,
    channel: Channel,
    coupling_model: str = "constant",
) -> float | np.ndarray:
    """
    Position-dependent geometric coupling factor.

    Represents how efficiently the scattered light from a particle at (x0, z0)
    is collected by the detection system, independent of illumination intensity.

    Note on double attenuation with illumination:
        A_env already applies Gaussian decay for off-center particles (illumination).
        gaussian_xy adds a SECOND decay representing geometric collection efficiency.
        These are physically distinct mechanisms. If combined attenuation is too strong,
        adjust the characteristic lengths (wcx, wcz) rather than removing one factor.

    Args:
        x0_m: Particle x position(s).
        z0_m: Particle z position(s).
        channel: Channel geometry.
        coupling_model: "constant" or "gaussian_xy".

    Returns:
        Coupling factor (dimensionless, in [0, 1]).
    """
    x = np.asarray(x0_m)
    z = np.asarray(z0_m)

    if coupling_model == "constant":
        out = np.ones_like(x, dtype=float)
        return float(out) if out.ndim == 0 else out

    elif coupling_model == "gaussian_xy":
        wcx = channel.width_m / 2
        wcz = channel.depth_m / 2
        out = np.exp(-(x / wcx)**2 - (z / wcz)**2)
        return float(out) if out.ndim == 0 else out

    raise ValueError(f"Unknown coupling_model: {coupling_model}")


def compute_scattering_field_trace(
    trajectory: dict,
    E_sca_unit_normalized: complex | float,
    optical: OpticalSystem,
    illumination: dict,
    channel: Channel,
    initial_x_m: float,
    initial_z_m: float,
    phase_model: str = "constant",
    coupling_model: str = "constant",
    path_opd_model: str = "single_pass",
    detection_theta_rad: float | None = None,
    medium_refractive_index: float = 1.0,
    reference_phase_rad: float | np.ndarray = 0.0,
    scattering_phase_diagnostics: dict | None = None,
    include_phase_diagnostics: bool = True,
    export_complex_field: bool = True,
    reuse_illumination_gouy_phase: bool = False,
) -> dict:
    """
    Compute the time-domain scattering field along a particle trajectory.

    Args:
        trajectory: dict from simulate_particle_trajectory.
        E_sca_unit_normalized: Complex normalized scattering-field proxy at the
            detector. Can carry material / angular collection phase.
        optical: Optical system.
        illumination: dict from compute_illumination_envelope.
        channel: Channel geometry (for spatial_coupling_factor).
        initial_x_m: Particle initial x position.
        initial_z_m: Particle initial z position.
        phase_model: Phase model. "constant" or "axial_path".
        coupling_model: Spatial coupling model. "constant" or "gaussian_xy".
        path_opd_model: How the z-path term is defined relative to the
            reference-side surrogate plane.
        detection_theta_rad: Effective detection angle used for the case.
        medium_refractive_index: Medium refractive index at the current wavelength.
        reference_phase_rad: Phase carried by the reference field. Can be a
            scalar (case-level) or array (event-level local reference phase).
            This is NOT reapplied to E_sca itself; it is only used to expose the
            explicit relative phase Δφ = arg(E_sca) - phi_ref for diagnostics.
        scattering_phase_diagnostics: Optional case-level phase diagnostics
            computed from the detected Mie projection, e.g. selected material
            phase and parallel / perpendicular component phases.

    Returns:
        dict with:
            E_sca_complex: np.ndarray (complex) — scattered field time series
            A_sca: np.ndarray (float >= 0) — scattering amplitude envelope
            phi_sca_rad: np.ndarray (float) — scattering phase
            delta_phi_ref_rad: np.ndarray (float) — explicit relative phase to
                the reference field

    """
    A_env = np.asarray(illumination["A_env"], dtype=float)
    phi_beam_source = illumination.get("phi_beam_rad")
    if phi_beam_source is None:
        env_complex = illumination.get("E_env_complex")
        phi_beam = (
            np.angle(env_complex)
            if env_complex is not None
            else np.zeros_like(A_env, dtype=float)
        )
    else:
        phi_beam = np.asarray(phi_beam_source, dtype=float)
    phi_beam_gouy_source = illumination.get("phi_beam_gouy_rad")
    phi_beam_gouy = (
        np.asarray(phi_beam_gouy_source, dtype=float)
        if phi_beam_gouy_source is not None
        else np.zeros_like(A_env, dtype=float)
    )
    phi_beam_curv_source = illumination.get("phi_beam_curv_rad")
    phi_beam_curv = (
        np.asarray(phi_beam_curv_source, dtype=float)
        if phi_beam_curv_source is not None
        else np.zeros_like(A_env, dtype=float)
    )

    x_positions = trajectory.get("x_m")
    z_positions = trajectory.get("z_m")

    # Spatial coupling follows the current particle position. This matters
    # once diffusion is enabled, because collection efficiency should then
    # vary over time rather than stay frozen at the initial location.
    if x_positions is None or z_positions is None:
        f_coupling = spatial_coupling_factor(
            initial_x_m, initial_z_m, channel, coupling_model
        )
    else:
        f_coupling = spatial_coupling_factor(
            x_positions, z_positions, channel, coupling_model
        )
    f_coupling_arr = np.asarray(f_coupling, dtype=float)
    if f_coupling_arr.ndim == 0:
        f_coupling_arr = np.full_like(A_env, float(f_coupling_arr), dtype=float)

    # Scattering field before extra path-dependent phase. This already carries
    # any intrinsic material / collection phase retained in E_sca_unit_normalized.
    unit_field = complex(E_sca_unit_normalized)
    unit_amplitude = float(abs(unit_field))
    unit_phase = float(np.angle(unit_field))

    # Phase
    phi_path_x = np.zeros_like(A_env, dtype=float)
    phi_path_z = np.zeros_like(A_env, dtype=float)
    phi_focus_crossing = np.zeros_like(A_env, dtype=float)
    path_opd_diag = _resolve_path_opd_diagnostics(path_opd_model)
    path_reference_plane = str(path_opd_diag["path_reference_plane"])
    path_z_geometry_factor = float(path_opd_diag["path_z_geometry_factor"])
    path_z_reference_mode = str(path_opd_diag["path_z_reference_mode"])
    if phase_model == "constant":
        phi_extra = np.zeros_like(A_env)
    elif phase_model == "axial_path":
        theta = (
            float(detection_theta_rad)
            if detection_theta_rad is not None
            else float(optical.collection_theta_rad)
        )
        z_path = (
            np.asarray(z_positions, dtype=float)
            if z_positions is not None
            else np.full_like(A_env, initial_z_m, dtype=float)
        )
        k_medium = 2.0 * np.pi * medium_refractive_index / optical.wavelength_m
        # Surrogate path-difference model: particles at different depths
        # accumulate different relative phases against the channel-derived
        # reference field, which reduces the always-constructive bias of the
        # old constant-phase model.
        phi_path_z = (
            path_z_geometry_factor
            * k_medium
            * (z_path - optical.focus_z_m)
            * np.cos(theta)
        )
        phi_extra = phi_path_z
    elif phase_model == "relative_surrogate":
        theta = (
            float(detection_theta_rad)
            if detection_theta_rad is not None
            else float(optical.collection_theta_rad)
        )
        x_path = (
            np.asarray(x_positions, dtype=float)
            if x_positions is not None
            else np.full_like(A_env, initial_x_m, dtype=float)
        )
        z_path = (
            np.asarray(z_positions, dtype=float)
            if z_positions is not None
            else np.full_like(A_env, initial_z_m, dtype=float)
        )
        y_path = (
            np.asarray(trajectory.get("y_m"), dtype=float)
            if trajectory.get("y_m") is not None
            else np.full_like(A_env, optical.focus_y_m, dtype=float)
        )
        k_medium = 2.0 * np.pi * medium_refractive_index / optical.wavelength_m
        # Minimal 2D path-difference surrogate in the detector projection plane.
        phi_path_x = k_medium * (x_path - optical.focus_x_m) * np.sin(theta)
        if path_opd_model == "wall_referenced_gap_surrogate":
            # Diagnostic alternative: treat the reference field as if it were
            # launched from the nearest channel wall, but center the wall-gap
            # contribution about the channel midplane so the center section
            # stays the zero-reference location.
            phi_path_z = (
                -k_medium
                * np.abs(np.asarray(z_path, dtype=float))
                * np.cos(theta)
            )
        else:
            phi_path_z = (
                path_z_geometry_factor
                * k_medium
                * (z_path - optical.focus_z_m)
                * np.cos(theta)
            )
        illumination_gouy = (
            illumination.get("phi_beam_gouy_rad")
            if reuse_illumination_gouy_phase
            else None
        )
        if illumination_gouy is not None:
            phi_focus_crossing = np.asarray(illumination_gouy, dtype=float)
            if phi_focus_crossing.shape != A_env.shape:
                phi_focus_crossing = _surrogate_focus_crossing_phase(
                    y_path,
                    optical,
                    medium_refractive_index,
                )
        else:
            phi_focus_crossing = _surrogate_focus_crossing_phase(
                y_path,
                optical,
                medium_refractive_index,
            )
        # The reference phase itself is already carried by E_ref_complex in the
        # interference layer. Here we only build the dynamic scattering-side
        # contribution; the explicit Δφ to the reference is exposed below.
        phi_extra = phi_path_x + phi_path_z + phi_focus_crossing
    else:
        raise ValueError(
            f"phase_model '{phase_model}' not implemented. "
            "Use phase_model='constant', 'axial_path', or "
            "'relative_surrogate'."
        )

    # Complex scattered field
    A_sca = A_env * f_coupling_arr * unit_amplitude
    # ── Gouy-phase deduplication ───────────────────────────────────────────────
    # illumination.py computes phi_beam = phi_gouy_surrogate + phi_curv, where
    #   phi_gouy_surrogate = arctan((y - y_f) / z_R).
    # In relative_surrogate mode, _surrogate_focus_crossing_phase() also returns
    #   phi_focus_crossing  = arctan((y - y_f) / z_R)  (same formula, same z_R).
    # Combining the full phi_beam with phi_extra would add arctan twice, inflating
    # the Gouy swing by 2×.  Fix: in relative_surrogate mode, drop phi_beam_gouy
    # and keep only phi_beam_curv (wavefront curvature), since phi_focus_crossing
    # already represents the focus-crossing phase once.
    # For constant / axial_path modes phi_focus_crossing = 0, so the full phi_beam
    # is correct and remains unchanged.
    # Numerical verification (2026-04-12, λ=660 nm, NA_ill=0.45, n=1.33):
    #   before fix → Δφ within FWHM ≈ 33.2°  (2× arctan)
    #   after  fix → Δφ within FWHM ≈ 16.6°  (1× arctan)
    # Reference: 工程文件 41_实验对齐原则 §Gouy去重; Codex evaluation 2026-04-12.
    _gouy_dedup_active = phase_model == "relative_surrogate"
    if _gouy_dedup_active:
        phi_sca_unwrapped = phi_beam_curv + unit_phase + phi_extra
    else:
        phi_sca_unwrapped = phi_beam + unit_phase + phi_extra
    result = {
        "A_sca": A_sca,
        "phi_sca_unwrapped_rad": phi_sca_unwrapped,
        "path_opd_model": str(path_opd_model),
        "path_opd_reference_plane": str(path_reference_plane),
        "path_opd_z_geometry_factor": float(path_z_geometry_factor),
        "path_opd_z_reference_mode": str(path_z_reference_mode),
        "path_opd_default_model": str(path_opd_diag["path_opd_default_model"]),
        "path_opd_model_role": str(path_opd_diag["path_opd_model_role"]),
        "path_opd_default_frozen": bool(path_opd_diag["path_opd_default_frozen"]),
        "path_opd_freeze_status": str(path_opd_diag["path_opd_freeze_status"]),
        "f_coupling": f_coupling_arr,
        "illumination_polarization_mode": illumination.get(
            "illumination_polarization_mode",
            "legacy_scalar",
        ),
        "illumination_polarization_effective_mode": illumination.get(
            "illumination_polarization_effective_mode",
            "intensity_proxy",
        ),
        "illumination_polarization_amplitude_factor": float(
            illumination.get("illumination_polarization_amplitude_factor", 1.0)
        ),
        "illumination_polarization_alignment_status": illumination.get(
            "illumination_polarization_alignment_status",
            "legacy_scalar",
        ),
    }
    if export_complex_field:
        result["E_sca_complex"] = A_sca * np.exp(1j * phi_sca_unwrapped)
    if not include_phase_diagnostics:
        return result

    phi_sca = _wrap_to_pi(phi_sca_unwrapped)
    reference_phase = np.asarray(reference_phase_rad, dtype=float)
    if reference_phase.ndim == 0:
        reference_phase = np.full_like(phi_sca, float(reference_phase), dtype=float)
    delta_phi_ref = _wrap_to_pi(phi_sca_unwrapped - reference_phase)
    phase_diagnostics = scattering_phase_diagnostics or {}
    phi_projection_scalar = float(_wrap_to_pi(unit_phase))
    phi_projection = np.full_like(
        A_sca,
        phi_projection_scalar,
        dtype=float,
    )
    # Export active y-phase contributions consistently with the actual fields:
    # - the reference trace never carries phi_beam_gouy in E_ref_trace_complex
    # - the scattering trace carries either
    #     relative_surrogate -> phi_focus_crossing
    #     legacy modes       -> phi_beam_gouy + phi_focus_crossing (focus term is 0)
    # Keep phi_beam_gouy_rad as the illumination-side audit field, but expose
    # phi_gouy_ref/sca/delta as the contributions that truly enter the
    # interference calculation.
    phi_gouy_ref = np.zeros_like(A_sca, dtype=float)
    if _gouy_dedup_active:
        phi_gouy_sca = np.asarray(phi_focus_crossing, dtype=float)
        phi_gouy_scattering_status = "active_focus_crossing_only_deduplicated"
    else:
        phi_gouy_sca = np.asarray(phi_beam_gouy + phi_focus_crossing, dtype=float)
        phi_gouy_scattering_status = "active_beam_gouy_component"
    delta_phi_gouy = np.asarray(phi_gouy_sca - phi_gouy_ref, dtype=float)
    phi_material_scalar = float(
        _wrap_to_pi(
            float(phase_diagnostics.get("phi_sca_material_rad", unit_phase))
        )
    )
    phi_material = np.full_like(
        A_sca,
        phi_material_scalar,
        dtype=float,
    )
    phi_material_parallel_scalar = float(
        _wrap_to_pi(
            float(phase_diagnostics.get("phi_sca_material_parallel_rad", phi_material_scalar))
        )
    )
    phi_material_parallel = np.full_like(
        A_sca,
        phi_material_parallel_scalar,
        dtype=float,
    )
    phi_material_perpendicular_scalar = float(
        _wrap_to_pi(
            float(
                phase_diagnostics.get(
                    "phi_sca_material_perpendicular_rad",
                    phi_material_scalar,
                )
            )
        )
    )
    phi_material_perpendicular = np.full_like(
        A_sca,
        phi_material_perpendicular_scalar,
        dtype=float,
    )
    result.update({
        "phi_sca_rad": phi_sca,
        "phi_material_rad": phi_material,
        "phi_projection_rad": phi_projection,
        "phi_material_parallel_rad": phi_material_parallel,
        "phi_material_perpendicular_rad": phi_material_perpendicular,
        "phi_beam_rad": _wrap_to_pi(phi_beam),
        "phi_beam_gouy_rad": _wrap_to_pi(phi_beam_gouy),
        "phi_beam_curv_rad": _wrap_to_pi(phi_beam_curv),
        "phi_focus_crossing_rad": _wrap_to_pi(phi_focus_crossing),
        "phi_gouy_ref_rad": _wrap_to_pi(phi_gouy_ref),
        "phi_gouy_sca_rad": _wrap_to_pi(phi_gouy_sca),
        "delta_phi_gouy_rad": _wrap_to_pi(delta_phi_gouy),
        "gouy_dedup_active": bool(_gouy_dedup_active),
        "phi_gouy_reference_status": "inactive_not_carried_by_reference_trace",
        "phi_gouy_scattering_status": phi_gouy_scattering_status,
        "phi_gouy_semantics_status": "active_interference_contribution_fields",
        "phi_sca_path_x_rad": _wrap_to_pi(phi_path_x),
        "phi_sca_path_z_rad": _wrap_to_pi(phi_path_z),
        "phi_sca_path_rad": _wrap_to_pi(phi_extra),
        "phi_extra_rad": _wrap_to_pi(phi_extra),
        "phi_ref_rad": _wrap_to_pi(reference_phase),
        "delta_phi_ref_rad": delta_phi_ref,
    })
    return result
