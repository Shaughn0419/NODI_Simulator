"""
NODI Interferometric Simulator — Reference Field Module

Computes the nanochannel diffraction reference field E_ref.
In the NODI detection scheme, the nanochannel itself provides diffracted light
that serves as an interferometric reference for enhancing weak scattering signals.

Models:
    - "constant": E_ref = ρ · e^{i·0}, no geometry dependence
    - "geometry_scaled": E_ref = ρ · g(W,H,λ) · e^{iφ₀}, surrogate scaling
    - "channel_angular_surrogate": channel diffraction angular-field surrogate
      collapsed by the same collection operator used for E_sca
    - "paper_aligned_phase_filter": Tsuyama-leaning comparison mode where
      depth acts through phase delay only, not as an extra kz-aperture term
    - "tsuyama_bfp_integrated": detector-resolved Tsuyama BFP ROI comparison
      route, not calibrated blank truth
"""

import os
from functools import lru_cache

import numpy as np
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator

from .calibration_models import (
    build_bfp_roi_mask_contract,
    calibration_contract_summary,
    load_calibration_rows,
    optional_calibration_float,
    optional_calibration_string,
)
from .data_objects import (
    Channel,
    OpticalSystem,
    SimulationConfig,
    resolve_reference_route_name,
    resolve_reference_solver_route_name,
)
from .tsuyama_phase_filter import (
    compute_tsuyama_phase_filter_bfp_field,
    integrate_bfp_roi,
)
from .utils import (
    build_collection_operator,
    collapse_angular_field_with_operator,
    build_projection_basis_diagnostics,
    resolve_polarization_coupling,
)


_DEFAULT_REFERENCE_MEDIUM_REFRACTIVE_INDEX = 1.33
_DEFAULT_REFERENCE_WALL_REFRACTIVE_INDEX = 1.46
_BASELINE_REFERENCE_INDEX_CONTRAST = abs(
    _DEFAULT_REFERENCE_WALL_REFRACTIVE_INDEX - _DEFAULT_REFERENCE_MEDIUM_REFRACTIVE_INDEX
)
_BASELINE_REFERENCE_DEPTH_M = 550e-9
_REFERENCE_FIELD_ENVELOPE_LOWER_FACTOR = 0.5
_REFERENCE_FIELD_ENVELOPE_UPPER_FACTOR = 2.0

TSUYAMA_BFP_REFERENCE_DIAGNOSTIC_FIELDS = (
    "E_ref_complex_roi",
    "I_ref_intensity_roi",
    "E_no_channel_complex_roi",
    "I_no_channel_intensity_roi",
    "reference_detector_bridge_status",
    "reference_solver_route",
    "reference_solver_status",
    "reference_solver_detector_bridge_status",
    "reference_solver_active_field_source",
    "paper_aligned_reference_claim",
    "reference_solver_claim_level",
    "reference_claim_level",
    "tsuyama_bfp_integrated_route_status",
    "tsuyama_bfp_roi_half_width_rad_per_m",
    "tsuyama_bfp_roi_sample_count",
    "tsuyama_bfp_roi_mode",
    "tsuyama_bfp_transmitted_block_q_rad_per_m",
    "tsuyama_bfp_lobe_center_q_rad_per_m",
    "tsuyama_bfp_lobe_sigma_q_rad_per_m",
    "tsuyama_bfp_roi_fraction",
    "tsuyama_bfp_roi_fraction_of_total_diffraction",
    "tsuyama_bfp_symmetric_vs_slit_roi_ratio",
    "bfp_roi_mask_projection_status",
    "bfp_roi_mask_projected_row_count",
    "bfp_roi_mask_projected_sample_count",
)


def _resolve_phase_grating_amplitude_scale(
    phase_delay_rad: float,
    depth_scale: float,
    sim_cfg: SimulationConfig,
) -> tuple[float, dict[str, float | str]]:
    """Select the active depth-phase-grating amplitude surrogate and export diagnostics."""
    legacy_sinc_amplitude_scale = max(
        depth_scale * abs(np.sinc(phase_delay_rad / (2.0 * np.pi))),
        0.05,
    )
    sine_response_abs = 2.0 * abs(np.sin(0.5 * phase_delay_rad))
    sine_amplitude_scale = max(sine_response_abs, 0.05)

    if sim_cfg.reference_phase_grating_mode == "legacy_sinc_linearized":
        active_mode = "legacy_sinc_linearized"
        active_scale = legacy_sinc_amplitude_scale
        field_contrast_scale = None
        active_model = (
            "thin_phase_grating_surrogate:"
            "active_amplitude~(H/H0)*|sinc(phase_delay/2π)|,"
            "phase~phase_delay/2"
        )
        active_components = "contrast_scale * (H/H0) * |sinc(phase_delay/2π)|"
    else:
        active_mode = "phase_grating_sine"
        active_scale = sine_amplitude_scale
        field_contrast_scale = 1.0
        active_model = (
            "thin_phase_grating_surrogate:"
            "active_amplitude~2|sin(phase_delay/2)|,"
            "phase~phase_delay/2,"
            "legacy_sinc_exported_for_diagnostics"
        )
        active_components = "2|sin(phase_delay/2)|"

    return active_scale, {
        "reference_phase_grating_mode": active_mode,
        "reference_phase_grating_model": active_model,
        "reference_phase_grating_active_components": active_components,
        "reference_phase_grating_sine_amplitude_scale": float(sine_amplitude_scale),
        "reference_phase_grating_legacy_sinc_amplitude_scale": float(
            legacy_sinc_amplitude_scale
        ),
        "reference_phase_grating_response_abs": float(sine_response_abs),
        "reference_phase_grating_field_contrast_scale_override": (
            None if field_contrast_scale is None else float(field_contrast_scale)
        ),
    }


def _build_reference_field_envelope_diagnostics(phase_delay_rad: float) -> dict[str, float | str]:
    """
    Export a thin-phase-grating reference-side amplitude envelope.

    This is intentionally diagnostic-only. It provides a physically motivated
    reference-field envelope based on diffraction efficiency, but it does not
    hard-clip the simulator's engineering-side rho parameter.
    """
    zeroth_order_efficiency = float(np.cos(0.5 * phase_delay_rad) ** 2)
    first_order_efficiency = float(np.sin(0.5 * phase_delay_rad) ** 2)
    amplitude_nominal = float(abs(np.sin(0.5 * phase_delay_rad)))
    amplitude_lower = float(_REFERENCE_FIELD_ENVELOPE_LOWER_FACTOR * amplitude_nominal)
    amplitude_upper = float(_REFERENCE_FIELD_ENVELOPE_UPPER_FACTOR * amplitude_nominal)
    return {
        "reference_diffraction_efficiency_model": (
            "thin_phase_grating:eta0~cos^2(phase_delay/2),eta1~sin^2(phase_delay/2)"
        ),
        "reference_diffraction_efficiency_zeroth_order": zeroth_order_efficiency,
        "reference_diffraction_efficiency_first_order": first_order_efficiency,
        "reference_field_amplitude_envelope_role": "diagnostic_only_not_hard_clipped",
        "reference_field_amplitude_envelope_nominal": amplitude_nominal,
        "reference_field_amplitude_envelope_lower": amplitude_lower,
        "reference_field_amplitude_envelope_upper": amplitude_upper,
        "reference_field_amplitude_envelope_lower_factor": float(
            _REFERENCE_FIELD_ENVELOPE_LOWER_FACTOR
        ),
        "reference_field_amplitude_envelope_upper_factor": float(
            _REFERENCE_FIELD_ENVELOPE_UPPER_FACTOR
        ),
    }


def _resolve_reference_width_saturation(
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    medium_refractive_index: float,
) -> tuple[float, dict[str, float | str | bool]]:
    """
    Resolve a soft cutoff for the width-direction angular surrogate.

    The goal is to avoid continuing to extrapolate a free-space slit response
    into the deeply sub-wavelength groove regime. The active surrogate does not
    attempt a rigorous waveguide solution; it only prevents the effective width
    term in the width-direction sinc from collapsing to zero indefinitely.
    """
    n_medium = max(float(medium_refractive_index), 1e-9)
    lambda_eff_m = optical.wavelength_m / n_medium
    width_lambda_ratio = channel.width_m / max(lambda_eff_m, 1e-18)
    cutoff_ratio = float(sim_cfg.reference_width_saturation_cutoff_ratio)

    if sim_cfg.reference_width_saturation_mode == "none":
        effective_width_m = float(channel.width_m)
        effective_ratio = float(width_lambda_ratio)
        factor = 1.0
        active = False
        status = "disabled_legacy_width_sinc"
        model = "none:free_space_width_sinc"
    else:
        effective_ratio = float(np.sqrt(width_lambda_ratio ** 2 + cutoff_ratio ** 2))
        effective_width_m = float(effective_ratio * lambda_eff_m)
        factor = float(effective_width_m / max(channel.width_m, 1e-18))
        active = bool(effective_width_m > channel.width_m * (1.0 + 1e-12))
        status = "active_soft_cutoff" if active else "inactive_wide_channel"
        model = "waveguide_cutoff_surrogate:W_eff=lambda_eff*sqrt((W/lambda_eff)^2+u_cutoff^2)"

    return effective_width_m, {
        "reference_width_saturation_mode": str(sim_cfg.reference_width_saturation_mode),
        "reference_width_saturation_model": model,
        "reference_width_saturation_status": status,
        "reference_width_saturation_active": active,
        "reference_width_saturation_cutoff_ratio": cutoff_ratio,
        "reference_width_lambda_ratio_nominal": float(width_lambda_ratio),
        "reference_width_lambda_ratio_effective": float(effective_ratio),
        "reference_width_effective_m": float(effective_width_m),
        "reference_width_saturation_factor": float(factor),
    }


def _reference_model_metadata(
    sim_cfg: SimulationConfig,
    resolved_route: str,
) -> dict[str, object]:
    """Expose audit-friendly precision tier / fallback role for the current reference model."""
    model = str(sim_cfg.reference_model)
    route_metadata = {
        "reference_model": model,
        "reference_route": str(resolved_route),
        "reference_route_requested": str(sim_cfg.reference_route),
        "reference_route_request_status": (
            "auto_resolved"
            if str(sim_cfg.reference_route) == "auto"
            else (
                "resolved_from_requested"
                if str(sim_cfg.reference_route) == str(resolved_route)
                else "requested_route_incompatible_resolved_from_model"
            )
        ),
    }
    if resolved_route == "calibrated_primary":
        route_metadata.update({
            "reference_route_role": "blank_channel_calibration_primary_entry",
            "reference_claim_level": "reference_calibrated_relative",
        })
    elif resolved_route == "paper_aligned_comparison":
        route_metadata.update({
            "reference_route_role": "paper_semantics_comparison_entry",
            "reference_claim_level": "paper_aligned_comparison",
        })
    elif resolved_route == "engineering_fallback":
        route_metadata.update({
            "reference_route_role": "no_blank_table_engineering_ranking_fallback",
            "reference_claim_level": "engineering_ranking",
        })
    else:
        route_metadata.update({
            "reference_route_role": "legacy_or_debug_reference_entry",
            "reference_claim_level": "legacy_debug",
        })

    if model == "calibrated_lookup":
        return route_metadata | {
            "reference_model_precision_tier": "blank_channel_calibrated",
            "reference_model_precision_rank": 3,
            "reference_model_role": "primary_when_calibration_available",
            "reference_model_guidance": (
                "Use as the primary path when blank-channel calibration data exists."
            ),
        }
    if model == "channel_angular_surrogate":
        return route_metadata | {
            "reference_model_precision_tier": "physics_informed_surrogate",
            "reference_model_precision_rank": 2,
            "reference_model_role": "default_no_table_fallback",
            "reference_model_guidance": (
                "Preferred no-table fallback because it keeps the operator-collapsed "
                "channel diffraction structure."
            ),
        }
    if model == "paper_aligned_phase_filter":
        return route_metadata | {
            "reference_model_precision_tier": "paper_aligned_comparison_surrogate",
            "reference_model_precision_rank": 2,
            "reference_model_role": "tsuyama_depth_semantics_audit_path",
            "reference_model_guidance": (
                "Use as a Tsuyama-leaning comparison path when auditing whether "
                "depth should act only through phase delay instead of an extra "
                "kz-aperture term."
            ),
        }
    if model == "tsuyama_bfp_integrated":
        route_metadata = route_metadata | {
            "reference_route_role": "paper_aligned_detector_resolved_comparison",
            "reference_claim_level": "paper_aligned_detector_resolved_comparison",
        }
        return route_metadata | {
            "reference_model_precision_tier": (
                "paper_aligned_detector_resolved_comparison_surrogate"
            ),
            "reference_model_precision_rank": 2,
            "reference_model_role": "tsuyama_bfp_roi_comparison_path",
            "reference_model_guidance": (
                "Tsuyama thin phase-filter BFP field is integrated over a "
                "surrogate ROI for route-consensus/design diagnostics only."
            ),
        }
    if model == "geometry_scaled":
        return route_metadata | {
            "reference_model_precision_tier": "legacy_empirical_fallback",
            "reference_model_precision_rank": 1,
            "reference_model_role": "legacy_fallback_only",
            "reference_model_guidance": (
                "Keep only as an empirical fallback; do not treat it as equivalent to "
                "calibrated_lookup or channel_angular_surrogate."
            ),
        }
    return route_metadata | {
        "reference_model_precision_tier": "phase1_placeholder",
        "reference_model_precision_rank": 0,
        "reference_model_role": "debug_placeholder_only",
        "reference_model_guidance": (
            "Constant reference is only a placeholder/debug path and should not be "
            "used for geometry comparisons."
        ),
    }


def _classify_geometry_depth_scaling(ref_beta: float) -> str:
    """Describe how the empirical depth exponent compares with thin-phase guidance."""
    beta = float(ref_beta)
    if np.isclose(beta, 1.0, atol=0.2):
        return "amplitude_like"
    if np.isclose(beta, 2.0, atol=0.3):
        return "intensity_like"
    if 1.0 < beta < 2.0:
        return "intermediate_empirical"
    if beta < 1.0:
        return "sub_amplitude_empirical"
    return "super_intensity_empirical"


def _optional_float(row: dict, key: str, default: float = float("nan")) -> float:
    value = row.get(key)
    if value in {None, ""}:
        return float(default)
    return float(value)


def _optional_string(row: dict, key: str) -> str:
    value = row.get(key)
    if value in {None, ""}:
        return ""
    return str(value)


def _coerce_rows(rows: list[dict]) -> dict[str, np.ndarray]:
    """Normalize calibration rows to arrays in nm/rad units."""
    width_nm = []
    depth_nm = []
    wavelength_nm = []
    g_ref = []
    a_ref = []
    phi_ref_rad = []
    phi_ref_source = []
    phi_ref_confidence = []
    phase_wrap_policy = []
    calibration_row_id = []
    calibration_data_role = []

    for idx, row in enumerate(rows):
        width_nm.append(float(row["width_nm"]))
        depth_nm.append(float(row["depth_nm"]))
        wavelength_nm.append(float(row["wavelength_nm"]))
        g_ref.append(_optional_float(row, "g_ref"))
        a_ref.append(_optional_float(row, "A_ref"))
        phi_ref_rad.append(_optional_float(row, "phi_ref_rad"))
        phi_ref_source.append(_optional_string(row, "phi_ref_source"))
        phi_ref_confidence.append(_optional_string(row, "phi_ref_confidence"))
        phase_wrap_policy.append(_optional_string(row, "phase_wrap_policy"))
        calibration_row_id.append(
            optional_calibration_string(
                row,
                "calibration_row_id",
                "row_id",
                default=f"reference_row_{idx}",
            )
        )
        calibration_data_role.append(
            optional_calibration_string(
                row,
                "calibration_data_role",
                "data_role",
                default="unspecified_user_table",
            )
        )

    if np.all(np.isnan(g_ref)) and np.all(np.isnan(a_ref)):
        raise ValueError("Calibration table must provide at least one of 'g_ref' or 'A_ref'.")

    return {
        "width_nm": np.asarray(width_nm, dtype=float),
        "depth_nm": np.asarray(depth_nm, dtype=float),
        "wavelength_nm": np.asarray(wavelength_nm, dtype=float),
        "g_ref": np.asarray(g_ref, dtype=float),
        "A_ref": np.asarray(a_ref, dtype=float),
        "phi_ref_rad": np.asarray(phi_ref_rad, dtype=float),
        "phi_ref_source": np.asarray(phi_ref_source, dtype=object),
        "phi_ref_confidence": np.asarray(phi_ref_confidence, dtype=object),
        "phase_wrap_policy": np.asarray(phase_wrap_policy, dtype=object),
        "calibration_row_id": np.asarray(calibration_row_id, dtype=object),
        "calibration_data_role": np.asarray(calibration_data_role, dtype=object),
    }


@lru_cache(maxsize=8)
def _load_reference_calibration(path: str) -> dict[str, np.ndarray]:
    """Load a reference calibration table from CSV or JSON."""
    resolved = os.path.abspath(path)
    rows = load_calibration_rows(resolved)

    required = {"width_nm", "depth_nm", "wavelength_nm"}
    if not rows:
        raise ValueError(f"Reference calibration file is empty: {resolved}")
    if not required.issubset(rows[0].keys()):
        raise ValueError(
            "Reference calibration rows must contain width_nm, depth_nm, wavelength_nm"
        )
    table = _coerce_rows(rows)
    contract = calibration_contract_summary(
        table_path=resolved,
        kind="reference_blank_channel",
    )
    table["calibration_manifest_status"] = np.asarray(
        [contract["calibration_manifest_status"]],
        dtype=object,
    )
    table["calibration_manifest_validation_status"] = np.asarray(
        [contract["calibration_manifest_validation_status"]],
        dtype=object,
    )
    table["calibration_manifest_path"] = np.asarray(
        [contract["calibration_manifest_path"]],
        dtype=object,
    )
    table["calibration_manifest_data_role"] = np.asarray(
        [contract["calibration_data_role"]],
        dtype=object,
    )
    table["calibration_synthetic_fixture_active"] = np.asarray(
        [contract["synthetic_fixture_active"]],
        dtype=object,
    )
    table["calibration_table_validation_status"] = np.asarray(
        [contract["calibration_table_validation_status"]],
        dtype=object,
    )
    return table


def _interpolate_scalar(points: np.ndarray, values: np.ndarray, query: np.ndarray) -> tuple[float, bool]:
    """Linear interpolation with nearest fallback."""
    finite_mask = np.isfinite(values)
    if not np.any(finite_mask):
        return float("nan"), True
    pts = points[finite_mask]
    vals = values[finite_mask]

    # Exact point match first to avoid interpolation noise on grid points.
    exact = np.all(np.isclose(pts, query[None, :], atol=1e-12), axis=1)
    if np.any(exact):
        return float(vals[np.argmax(exact)]), False

    if len(vals) >= 4:
        linear = LinearNDInterpolator(pts, vals)
        out = linear(query)
        if out is not None:
            out_arr = np.asarray(out, dtype=float).squeeze()
            if np.all(np.isfinite(out_arr)):
                return float(out_arr), False

    nearest = NearestNDInterpolator(pts, vals)
    nearest_value = np.asarray(nearest(query), dtype=float).squeeze()
    return float(nearest_value), True


def _interpolate_phase(points: np.ndarray, phi_ref_rad: np.ndarray, query: np.ndarray) -> tuple[float, bool]:
    """Interpolate phase via unit phasor to avoid naive angle wrap issues."""
    finite_mask = np.isfinite(phi_ref_rad)
    if not np.any(finite_mask):
        return float("nan"), True
    phase_points = points[finite_mask]
    phasor = np.exp(1j * phi_ref_rad[finite_mask])
    real, real_extrap = _interpolate_scalar(phase_points, np.real(phasor), query)
    imag, imag_extrap = _interpolate_scalar(phase_points, np.imag(phasor), query)
    return float(np.angle(real + 1j * imag)), bool(real_extrap or imag_extrap)


def _nearest_calibration_index(points: np.ndarray, query: np.ndarray) -> int:
    deltas = points - query[None, :]
    scales = np.maximum(np.ptp(points, axis=0), 1.0)
    distances = np.sum((deltas / scales[None, :]) ** 2, axis=1)
    return int(np.argmin(distances))


def _nearest_calibration_string(
    table: dict[str, np.ndarray],
    key: str,
    points: np.ndarray,
    query: np.ndarray,
) -> str:
    values = table.get(key)
    if values is None or len(values) == 0:
        return ""
    idx = _nearest_calibration_index(points, query)
    value = values[idx]
    if value in {None, ""}:
        return ""
    return str(value)


def _lookup_calibrated_reference(
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
) -> tuple[float, float, float, bool, dict[str, object]]:
    """
    Lookup calibrated reference amplitude / phase from a blank-channel table.

    Returns:
        (A_ref, phi_ref, g_ref)
    """
    table = _load_reference_calibration(sim_cfg.reference_calibration_path)
    query = np.array([
        channel.width_m * 1e9,
        channel.depth_m * 1e9,
        optical.wavelength_m * 1e9,
    ], dtype=float)
    points = np.column_stack([
        table["width_nm"],
        table["depth_nm"],
        table["wavelength_nm"],
    ])
    nearest_idx = _nearest_calibration_index(points, query)
    row_data_role = str(table["calibration_data_role"][nearest_idx])
    manifest_data_role = str(table["calibration_manifest_data_role"][0])
    reference_data_role = (
        manifest_data_role
        if row_data_role == "unspecified_user_table"
        else row_data_role
    )
    synthetic_fixture_active = bool(table["calibration_synthetic_fixture_active"][0]) or (
        reference_data_role == "synthetic_fixture_not_experimental"
    )
    if synthetic_fixture_active:
        raise ValueError(
            "reference_calibration_path points to a synthetic/template fixture; "
            "provide an experimental blank-channel calibration table before "
            "using reference_model='calibrated_lookup'."
        )

    g, g_extrap = _interpolate_scalar(points, table["g_ref"], query)
    a_ref, a_extrap = _interpolate_scalar(points, table["A_ref"], query)
    phi_ref, phi_extrap = _interpolate_phase(points, table["phi_ref_rad"], query)

    if np.isfinite(a_ref):
        A_ref = a_ref
        amplitude_status = "absolute_calibrated"
        amplitude_source = "A_ref"
        rho_used_for_amplitude = False
        if not np.isfinite(g):
            g = a_ref / sim_cfg.rho if sim_cfg.rho > 0 else 1.0
    else:
        if not np.isfinite(g):
            raise ValueError(
                "Reference calibration lookup did not yield a finite A_ref or g_ref."
            )
        A_ref = sim_cfg.rho * g
        amplitude_status = "calibrated_scale_only"
        amplitude_source = "rho_times_g_ref"
        rho_used_for_amplitude = True

    phase_source = _nearest_calibration_string(table, "phi_ref_source", points, query)
    phase_confidence = _nearest_calibration_string(
        table,
        "phi_ref_confidence",
        points,
        query,
    )
    phase_wrap_policy = _nearest_calibration_string(
        table,
        "phase_wrap_policy",
        points,
        query,
    ) or "unit_phasor_interpolation"
    if not np.isfinite(phi_ref):
        phi_ref = 0.0
        phase_status = "default_zero_phase_unknown"
        phase_absolute_claim = "not_measured_absolute_phase"
    elif phase_source:
        phase_status = "measured_or_fitted_phase_with_source"
        phase_absolute_claim = "measured_or_fitted_absolute_phase"
    else:
        phase_status = "model_assigned_or_unknown_phase"
        phase_absolute_claim = "not_measured_absolute_phase"

    calibration_extrapolated = bool(g_extrap or a_extrap or phi_extrap)
    diagnostics = {
        "reference_calibration_amplitude_status": amplitude_status,
        "reference_calibration_amplitude_source": amplitude_source,
        "rho_used_for_reference_amplitude": bool(rho_used_for_amplitude),
        "reference_calibration_A_ref_lookup": (
            float(a_ref) if np.isfinite(a_ref) else None
        ),
        "reference_calibration_g_ref_lookup": (
            float(g) if np.isfinite(g) else None
        ),
        "reference_calibration_g_ref_extrapolated": bool(g_extrap),
        "reference_calibration_A_ref_extrapolated": bool(a_extrap),
        "reference_calibration_phi_ref_extrapolated": bool(phi_extrap),
        "reference_calibration_coverage_status": (
            "extrapolated_nearest_fallback" if calibration_extrapolated else "covered"
        ),
        "reference_calibration_row_id": str(table["calibration_row_id"][nearest_idx]),
        "reference_calibration_row_index": int(nearest_idx),
        "reference_calibration_row_count": int(len(points)),
        "reference_calibration_data_role": reference_data_role,
        "reference_calibration_synthetic_fixture_active": False,
        "reference_calibration_table_validation_status": str(
            table["calibration_table_validation_status"][0]
        ),
        "reference_calibration_manifest_status": str(
            table["calibration_manifest_status"][0]
        ),
        "reference_calibration_manifest_validation_status": str(
            table["calibration_manifest_validation_status"][0]
        ),
        "reference_calibration_manifest_path": table["calibration_manifest_path"][0],
        "reference_phase_calibration_status": phase_status,
        "reference_phase_absolute_claim": phase_absolute_claim,
        "phi_ref_source": phase_source or None,
        "phi_ref_confidence": phase_confidence or None,
        "phase_wrap_policy": phase_wrap_policy,
    }

    return (
        float(A_ref),
        float(phi_ref),
        float(g),
        calibration_extrapolated,
        diagnostics,
    )


def _channel_diffraction_field_surrogate(
    theta_grid_rad: np.ndarray,
    phi_grid_rad: np.ndarray,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    medium_refractive_index: float,
) -> np.ndarray:
    """
    Minimal channel diffraction angular-field surrogate.

    The field is not intended to be a full-wave solution. It only introduces a
    geometry- and wavelength-dependent angular spectrum so E_ref no longer comes
    purely from a free exponent law when no blank-channel calibration table is
    available.
    """
    n_medium = max(float(medium_refractive_index), 1e-9)
    n_wall = float(channel.wall_refractive_index_at(optical.wavelength_m))
    contrast = abs(n_wall - n_medium)
    contrast_scale = max(contrast / max(_BASELINE_REFERENCE_INDEX_CONTRAST, 1e-9), 0.05)
    phase_delay_rad = 2.0 * np.pi * contrast * channel.depth_m / optical.wavelength_m
    depth_scale = channel.depth_m / max(_BASELINE_REFERENCE_DEPTH_M, 1e-12)
    phase_grating_amplitude_scale, phase_grating_diagnostics = (
        _resolve_phase_grating_amplitude_scale(
            phase_delay_rad,
            depth_scale,
            sim_cfg,
        )
    )
    field_contrast_scale = phase_grating_diagnostics[
        "reference_phase_grating_field_contrast_scale_override"
    ]
    if field_contrast_scale is None:
        field_contrast_scale = contrast_scale
    phase_grating_phase_rad = 0.5 * phase_delay_rad
    phase_delay_over_2_role = "amplitude_envelope_surrogate_only"
    polarity_claim_from_phase_delay_over_2_allowed = False

    k = 2.0 * np.pi * n_medium / optical.wavelength_m
    theta = theta_grid_rad[:, None]
    phi = phi_grid_rad[None, :]

    kx = k * np.sin(theta) * np.cos(phi)
    kz = k * np.sin(theta) * np.sin(phi)

    paper_aligned_mode = str(sim_cfg.reference_model) == "paper_aligned_phase_filter"
    if paper_aligned_mode:
        lambda_eff_m = optical.wavelength_m / max(n_medium, 1e-18)
        width_lambda_ratio = float(channel.width_m / max(lambda_eff_m, 1e-18))
        effective_width_m = float(channel.width_m)
        width_saturation_diagnostics = {
            "reference_width_saturation_mode": "paper_aligned_disabled",
            "reference_width_saturation_model": (
                "paper_aligned_phase_filter:disabled_for_width_semantics_audit"
            ),
            "reference_width_saturation_status": "disabled_paper_aligned_phase_filter",
            "reference_width_saturation_active": False,
            "reference_width_saturation_cutoff_ratio": float(
                sim_cfg.reference_width_saturation_cutoff_ratio
            ),
            "reference_width_lambda_ratio_nominal": width_lambda_ratio,
            "reference_width_lambda_ratio_effective": width_lambda_ratio,
            "reference_width_effective_m": effective_width_m,
            "reference_width_saturation_factor": 1.0,
        }
    else:
        effective_width_m, width_saturation_diagnostics = _resolve_reference_width_saturation(
            channel,
            optical,
            sim_cfg,
            medium_refractive_index,
        )
    width_term = np.sinc((effective_width_m * kx) / (2.0 * np.pi))
    if paper_aligned_mode:
        # Paper-aligned (Tsuyama 2020 diffraction): depth enters ONLY through
        # the phase delay θ = 2π|ns−ng|d/λ.  There is no sinc aperture term in
        # kz in the published derivation (Eq. 3–7 of Tsuyama & Mawatari 2020,
        # Microfluid. Nanofluid. 24:28).  Setting depth_term = 1 enforces this.
        depth_term = np.ones_like(width_term, dtype=float)
    else:
        # Engineering surrogate (channel_angular_surrogate mainline):
        # Introduces a sinc(H·kz / 2π) aperture along kz to represent a
        # finite-depth rectangular "groove" in the far-field angular spectrum.
        # ── WARNING ──────────────────────────────────────────────────────────
        # This term is NOT present in any Tsuyama / Mawatari paper.  It is an
        # engineering choice that (a) suppresses high-kz components beyond the
        # physical channel depth and (b) introduces a spurious depth dependence
        # of the S/B ratio that contradicts Tsuyama 2020 Eq. 13, which shows
        # S/B ≈ (Δns − Δng)/|ns − ng| independent of channel depth.
        # Use paper_aligned_phase_filter when comparing against paper results.
        depth_term = np.sinc((channel.depth_m * kz) / (2.0 * np.pi))
    width_jump_rad = np.where(width_term < 0.0, np.pi, 0.0)
    if paper_aligned_mode:
        depth_jump_rad = np.zeros_like(width_jump_rad, dtype=float)
    else:
        depth_jump_rad = np.where(depth_term < 0.0, np.pi, 0.0)
    signed_phase_jump_rad = width_jump_rad + depth_jump_rad
    if paper_aligned_mode:
        # Paper-aligned: only the global phase offset and the thin-grating
        # mean phase (θ/2) survive — matching Tsuyama 2020 Eq. 3–4 exactly.
        phase_continuous = sim_cfg.ref_phi0_rad + phase_grating_phase_rad
    else:
        # Engineering surrogate phase structure (channel_angular_surrogate):
        # The two extra terms below are EMPIRICAL SURROGATE COEFFICIENTS with
        # no basis in any Tsuyama / Mawatari publication.
        #
        #   0.35 · k · H · (1 − cosθ)         — depth-driven axial phase tilt
        #   0.15 · k · W · sinθ · cosφ         — width-driven lateral phase tilt
        #
        # They were introduced as engineering knobs to give the angular
        # reference-field a soft geometric slope consistent with a finite-groove
        # diffraction pattern, without fully solving the Fresnel–Kirchhoff
        # integral.  They have been shown to shift the effective reference-field
        # phase in a depth/width-dependent way that diverges from the paper's
        # 1-D phase-filter picture (Tsuyama 2020 Eq. 13: S/B independent of
        # depth).  Use paper_aligned_phase_filter for paper comparisons.
        phase_continuous = (
            sim_cfg.ref_phi0_rad
            + 0.35 * k * channel.depth_m * (1.0 - np.cos(theta))
            + 0.15 * k * channel.width_m * np.sin(theta) * np.cos(phi)
            + phase_grating_phase_rad
        )
    # NOTE: no detector-acceptance envelope here. The angular acceptance window
    # is applied exclusively by the collection operator (build_collection_operator /
    # collapse_angular_field_with_operator). Pre-multiplying it into the source
    # field would double-count the detector acceptance and artificially suppress
    # the reference amplitude.
    field = (
        field_contrast_scale
        * phase_grating_amplitude_scale
        * np.abs(width_term)
        * np.abs(depth_term)
        * np.exp(1j * (phase_continuous + signed_phase_jump_rad))
    )
    diagnostics = {
        "reference_index_contrast_abs": float(contrast),
        "reference_index_contrast_baseline_abs": float(_BASELINE_REFERENCE_INDEX_CONTRAST),
        "reference_contrast_amplitude_scale": float(contrast_scale),
        "reference_contrast_scaling_law": "amplitude~|n_wall-n_medium|",
        "reference_contrast_scaling_role": (
            "active_multiplier"
            if sim_cfg.reference_phase_grating_mode == "legacy_sinc_linearized"
            else "small_signal_diagnostic_only"
        ),
        "reference_phase_delay_rad": float(phase_delay_rad),
        "reference_phase_grating_amplitude_scale": float(phase_grating_amplitude_scale),
        "reference_phase_grating_phase_rad": float(phase_grating_phase_rad),
        "phase_delay_over_2_role": phase_delay_over_2_role,
        "polarity_claim_from_phase_delay_over_2_allowed": (
            polarity_claim_from_phase_delay_over_2_allowed
        ),
        "absolute_polarity_claim": "blocked_active_reference_phase_surrogate",
        "reference_absolute_polarity_claim": "blocked_active_reference_phase_surrogate",
        "reference_active_phase_source": "phase_delay_over_2_surrogate_not_absolute_polarity",
        "reference_phase_grating_depth_scale": float(depth_scale),
        "reference_phase_structure_mode": (
            "paper_aligned_1d_phase_filter_width_only"
            if paper_aligned_mode
            else "rectangular_fraunhofer_pi_jumps"
        ),
        "reference_depth_aperture_term_active": (not paper_aligned_mode),
        "reference_width_phase_jump_fraction": float(np.mean(width_jump_rad > 0.0)),
        "reference_depth_phase_jump_fraction": float(np.mean(depth_jump_rad > 0.0)),
        "reference_phase_jump_fraction": float(np.mean(signed_phase_jump_rad > 0.0)),
        "reference_phase_jump_max_rad": float(np.max(signed_phase_jump_rad)),
    }
    diagnostics.update(phase_grating_diagnostics)
    diagnostics.update(width_saturation_diagnostics)
    diagnostics.update(_build_reference_field_envelope_diagnostics(phase_delay_rad))
    return field, diagnostics


def _angular_surrogate_reference(
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    medium_refractive_index: float,
) -> tuple[float, float, float, str, dict, np.ndarray, np.ndarray, np.ndarray]:
    """Compute E_ref from a minimal channel diffraction angular spectrum."""
    theta_grid = np.linspace(0.0, np.deg2rad(75.0), 241)
    phi_grid = np.linspace(-float(sim_cfg.slit_phi_limit_rad), float(sim_cfg.slit_phi_limit_rad), 61)
    operator = build_collection_operator(
        theta_grid,
        channel,
        optical,
        sim_cfg,
        medium_refractive_index=medium_refractive_index,
    )
    field, diagnostics = _channel_diffraction_field_surrogate(
        theta_grid,
        phi_grid,
        channel,
        optical,
        sim_cfg,
        medium_refractive_index,
    )
    detected = collapse_angular_field_with_operator(
        theta_grid,
        field,
        operator,
        sim_cfg,
        phi_grid_rad=phi_grid,
    )

    baseline_channel = Channel(width_m=800e-9, depth_m=550e-9)
    baseline_field, _ = _channel_diffraction_field_surrogate(
        theta_grid,
        phi_grid,
        baseline_channel,
        OpticalSystem(
            wavelength_m=660e-9,
            peak_irradiance_W_m2=optical.peak_irradiance_W_m2,
            beam_waist_x_m=optical.beam_waist_x_m,
            beam_waist_y_m=optical.beam_waist_y_m,
            beam_waist_z_m=optical.beam_waist_z_m,
            illumination_beam_waist_x_m=optical.illumination_beam_waist_x_m,
            illumination_beam_waist_y_m=optical.illumination_beam_waist_y_m,
            illumination_beam_waist_z_m=optical.illumination_beam_waist_z_m,
            illumination_NA=optical.illumination_NA,
            collection_theta_rad=optical.collection_theta_rad,
            focus_x_m=optical.focus_x_m,
            focus_y_m=optical.focus_y_m,
            focus_z_m=optical.focus_z_m,
            NA_collection=optical.NA_collection,
        ),
        sim_cfg,
        medium_refractive_index,
    )
    baseline_detected = collapse_angular_field_with_operator(
        theta_grid,
        baseline_field,
        operator,
        sim_cfg,
        phi_grid_rad=phi_grid,
    )
    baseline_abs = max(abs(baseline_detected), 1e-12)

    g = max(abs(detected) / baseline_abs, sim_cfg.ref_g_min)
    A_ref = sim_cfg.rho * g
    phi_ref = float(np.angle(detected))
    return (
        float(A_ref),
        float(phi_ref),
        float(g),
        str(operator["operator_signature"]),
        diagnostics,
        field,
        theta_grid,
        phi_grid,
    )


def _tsuyama_phase_filter_reference_diagnostics(
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    medium_refractive_index: float,
) -> dict[str, object]:
    """Compute Tsuyama 1D phase-filter diagnostics without claiming detector closure."""
    illumination_geometry = optical.resolve_illumination_geometry()
    gaussian_waist_m = float(illumination_geometry["illumination_beam_waist_x_m"])
    wall_index = float(channel.wall_refractive_index_at(optical.wavelength_m))
    solver = compute_tsuyama_phase_filter_bfp_field(
        channel_width_m=channel.width_m,
        channel_depth_m=channel.depth_m,
        wavelength_m=optical.wavelength_m,
        medium_refractive_index=medium_refractive_index,
        wall_refractive_index=wall_index,
        gaussian_waist_m=gaussian_waist_m,
        n_grid=int(sim_cfg.tsuyama_phase_filter_grid_n),
        grid_extent_factor=float(sim_cfg.tsuyama_phase_filter_grid_extent_factor),
    )
    invariants = solver["tsuyama_phase_filter_numerical_invariants"]
    return {
        "reference_solver_route": "tsuyama_phase_filter_1d",
        "reference_solver_status": "diagnostic_complex_bfp_field_available",
        "reference_solver_detector_bridge_status": (
            "diagnostic_only_uses_paper_aligned_angular_surrogate"
        ),
        "reference_solver_active_field_source": "paper_aligned_angular_surrogate",
        "paper_aligned_reference_claim": "diagnostic_only",
        "reference_solver_claim_level": "complex_field_solver_not_detector_unit",
        "reference_field_decomposition_status": "total_minus_no_channel_available",
        "phi_ref_model_rad": float(np.angle(solver["thin_phase_complex_factor"])),
        "phi_ref_model_source": "thin_phase_complex_factor_exp_i_theta_minus_one_diagnostic",
        "tsuyama_phase_filter_gaussian_waist_m": gaussian_waist_m,
        "tsuyama_phase_filter_gaussian_waist_source": str(
            illumination_geometry["illumination_geometry_source"]
        ),
        "tsuyama_phase_filter_bfp_q_rad_per_m": np.asarray(
            solver["bfp_q_rad_per_m"],
            dtype=float,
        ).copy(),
        "tsuyama_E_total_channel_BFP": np.asarray(
            solver["E_total_channel_BFP"],
            dtype=complex,
        ).copy(),
        "tsuyama_E_no_channel_BFP": np.asarray(
            solver["E_no_channel_BFP"],
            dtype=complex,
        ).copy(),
        "tsuyama_E_diffraction_BFP": np.asarray(
            solver["E_diffraction_BFP"],
            dtype=complex,
        ).copy(),
        "tsuyama_E_BFP_complex": np.asarray(
            solver["E_BFP_complex"],
            dtype=complex,
        ).copy(),
        "thin_phase_complex_factor": complex(solver["thin_phase_complex_factor"]),
        "thin_phase_perturbation_phase_rad": float(
            solver["thin_phase_perturbation_phase_rad"]
        ),
        "theta_signed_rad": float(solver["theta_signed_rad"]),
        "reference_index_contrast_signed": float(
            solver["reference_index_contrast_signed"]
        ),
        "phase_filter_validity": solver["phase_filter_validity"],
        "phase_filter_H_over_lambda0": solver["phase_filter_H_over_lambda0"],
        "phase_filter_delta_ref_rad": solver["phase_filter_delta_ref_rad"],
        "phase_filter_theta_signed_rad": solver["phase_filter_theta_signed_rad"],
        "phase_filter_H_over_zR": solver["phase_filter_H_over_zR"],
        "phase_filter_multiple_reflection_warning": solver[
            "phase_filter_multiple_reflection_warning"
        ],
        "sidewall_scattering_roughness_status": solver[
            "sidewall_scattering_roughness_status"
        ],
        "finite_length_assumption_status": solver[
            "finite_length_assumption_status"
        ],
        "subwavelength_groove_validity_status": solver[
            "subwavelength_groove_validity_status"
        ],
        "evanescent_component_unmodeled": solver["evanescent_component_unmodeled"],
        "groove_waveguide_mode_unmodeled": solver[
            "groove_waveguide_mode_unmodeled"
        ],
        "roughness_scatter_unmodeled": solver["roughness_scatter_unmodeled"],
        "depth_validity_reason": solver["depth_validity_reason"],
        "requires_calibration_or_fullwave": solver[
            "requires_calibration_or_fullwave"
        ],
        "tsuyama_phase_filter_numerical_invariants": dict(invariants),
    }


def _integrate_masked_bfp_roi(
    bfp_q_rad_per_m: np.ndarray,
    field_bfp: np.ndarray,
    roi_mask: np.ndarray,
) -> dict[str, object]:
    q = np.asarray(bfp_q_rad_per_m, dtype=float)
    field = np.asarray(field_bfp, dtype=complex)
    mask = np.asarray(roi_mask, dtype=bool)
    if q.shape != field.shape or q.shape != mask.shape:
        raise ValueError("BFP q grid, field, and roi_mask must have the same shape")
    if not np.any(mask):
        return {
            "roi_complex_amplitude": 0.0 + 0.0j,
            "roi_intensity": 0.0,
            "roi_sample_count": 0,
            "detector_mask_units": "rad_per_m",
            "roi_half_width_rad_per_m": 0.0,
        }
    active_indices = np.flatnonzero(mask)
    segments = np.split(active_indices, np.where(np.diff(active_indices) > 1)[0] + 1)
    roi_complex_amplitude = 0.0 + 0.0j
    roi_intensity = 0.0
    for segment in segments:
        roi_complex_amplitude += complex(np.trapezoid(field[segment], q[segment]))
        roi_intensity += float(np.trapezoid(np.abs(field[segment]) ** 2, q[segment]))
    return {
        "roi_complex_amplitude": complex(roi_complex_amplitude),
        "roi_intensity": float(roi_intensity),
        "roi_sample_count": int(active_indices.size),
        "detector_mask_units": "rad_per_m",
        "roi_half_width_rad_per_m": float(np.max(np.abs(q[active_indices]))),
    }


def _integrate_weighted_bfp_roi(
    bfp_q_rad_per_m: np.ndarray,
    field_bfp: np.ndarray,
    roi_weights: np.ndarray,
) -> dict[str, object]:
    q = np.asarray(bfp_q_rad_per_m, dtype=float)
    field = np.asarray(field_bfp, dtype=complex)
    weights = np.asarray(roi_weights, dtype=float)
    if q.shape != field.shape or q.shape != weights.shape:
        raise ValueError("BFP q grid, field, and roi_weights must have the same shape")
    active = weights > 0.0
    if not np.any(active):
        return {
            "roi_complex_amplitude": 0.0 + 0.0j,
            "roi_intensity": 0.0,
            "roi_sample_count": 0,
            "detector_mask_units": "rad_per_m",
            "roi_half_width_rad_per_m": 0.0,
        }
    return {
        "roi_complex_amplitude": complex(np.trapezoid(field * weights, q)),
        "roi_intensity": float(np.trapezoid(np.abs(field) ** 2 * weights, q)),
        "roi_sample_count": int(np.count_nonzero(active)),
        "detector_mask_units": "rad_per_m",
        "roi_half_width_rad_per_m": float(np.max(np.abs(q[active]))),
    }


def _build_slit_off_axis_lobe_roi_weights(
    bfp_q_rad_per_m: np.ndarray,
    roi_half_width_rad_per_m: float,
    sim_cfg: SimulationConfig,
) -> tuple[np.ndarray, dict[str, float]]:
    q = np.asarray(bfp_q_rad_per_m, dtype=float)
    q_na = float(roi_half_width_rad_per_m)
    block_q = float(sim_cfg.tsuyama_bfp_transmitted_block_fraction) * q_na
    lobe_center_q = float(sim_cfg.tsuyama_bfp_lobe_center_fraction) * q_na
    sigma_q = max(float(sim_cfg.tsuyama_bfp_lobe_sigma_fraction) * q_na, 1e-30)
    aperture = (np.abs(q) >= block_q) & (np.abs(q) <= q_na)
    lobe_weight = np.exp(-0.5 * ((q - lobe_center_q) / sigma_q) ** 2) + np.exp(
        -0.5 * ((q + lobe_center_q) / sigma_q) ** 2
    )
    weights = np.where(aperture, lobe_weight, 0.0)
    max_weight = float(np.max(weights)) if weights.size else 0.0
    if max_weight > 0.0:
        weights = weights / max_weight
    return weights, {
        "tsuyama_bfp_transmitted_block_q_rad_per_m": block_q,
        "tsuyama_bfp_lobe_center_q_rad_per_m": lobe_center_q,
        "tsuyama_bfp_lobe_sigma_q_rad_per_m": sigma_q,
    }


def _bfp_grid_cell_widths(bfp_q_rad_per_m: np.ndarray) -> np.ndarray:
    q = np.asarray(bfp_q_rad_per_m, dtype=float)
    if q.size <= 1:
        return np.ones_like(q, dtype=float)
    return np.maximum(np.abs(np.gradient(q)), 1e-30)


def _project_calibrated_bfp_roi_mask_to_tsuyama_q(
    bfp_q_rad_per_m: np.ndarray,
    optical: OpticalSystem,
    rows: list[dict[str, object]],
) -> tuple[np.ndarray, dict[str, object]]:
    q = np.asarray(bfp_q_rad_per_m, dtype=float)
    weights = np.zeros_like(q, dtype=float)
    if q.size == 0:
        return weights, {
            "bfp_roi_mask_projection_status": "not_applied_empty_tsuyama_bfp_grid",
            "bfp_roi_mask_projected_row_count": 0,
            "bfp_roi_mask_projected_sample_count": 0,
        }

    q_min = float(np.min(q))
    q_max = float(np.max(q))
    cell_widths = _bfp_grid_cell_widths(q)
    q_tolerance = float(np.max(cell_widths))
    k0 = 2.0 * np.pi / float(optical.wavelength_m)
    projected_rows = 0

    for row in rows:
        theta_rad = optional_calibration_float(row, "theta_rad")
        phi_rad = optional_calibration_float(row, "phi_rad", default=0.0)
        mask_weight = optional_calibration_float(row, "mask_weight")
        solid_angle_weight = optional_calibration_float(
            row,
            "solid_angle_weight",
            default=1.0,
        )
        if (
            theta_rad is None
            or phi_rad is None
            or mask_weight is None
            or solid_angle_weight is None
            or mask_weight <= 0.0
            or solid_angle_weight <= 0.0
        ):
            continue

        # The Tsuyama route is a 1D BFP comparison lane. Project the measured
        # 2D mask row onto the solver axis instead of treating it as a full
        # detector-unit overlap.
        q_target = k0 * np.sin(theta_rad) * np.cos(phi_rad)
        if q_target < q_min - q_tolerance or q_target > q_max + q_tolerance:
            continue
        index = int(np.argmin(np.abs(q - q_target)))
        weights[index] += (mask_weight * solid_angle_weight) / cell_widths[index]
        projected_rows += 1

    projected_samples = int(np.count_nonzero(weights > 0.0))
    status = (
        "calibrated_mask_projected_to_1d_tsuyama_bfp_grid"
        if projected_samples > 0
        else "not_applied_no_calibrated_mask_rows_overlap_1d_tsuyama_bfp_grid"
    )
    return weights, {
        "bfp_roi_mask_projection_status": status,
        "bfp_roi_mask_projected_row_count": int(projected_rows),
        "bfp_roi_mask_projected_sample_count": projected_samples,
    }


def compute_reference_field_from_tsuyama_bfp(
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    medium_refractive_index: float,
    wall_refractive_index: float,
    roi_mask: np.ndarray | None = None,
) -> dict[str, object]:
    """Compute a Tsuyama BFP ROI reference comparison payload."""
    illumination_geometry = optical.resolve_illumination_geometry()
    gaussian_waist_m = float(illumination_geometry["illumination_beam_waist_x_m"])
    solver = compute_tsuyama_phase_filter_bfp_field(
        channel_width_m=channel.width_m,
        channel_depth_m=channel.depth_m,
        wavelength_m=optical.wavelength_m,
        medium_refractive_index=medium_refractive_index,
        wall_refractive_index=wall_refractive_index,
        gaussian_waist_m=gaussian_waist_m,
        n_grid=int(sim_cfg.tsuyama_phase_filter_grid_n),
        grid_extent_factor=float(sim_cfg.tsuyama_phase_filter_grid_extent_factor),
    )
    q = np.asarray(solver["bfp_q_rad_per_m"], dtype=float)
    bfp_roi_mask_contract = build_bfp_roi_mask_contract(
        bfp_roi_mask_path=sim_cfg.bfp_roi_mask_path,
        bfp_to_angle_jacobian_applied=bool(
            getattr(sim_cfg, "bfp_to_angle_jacobian_applied", False)
        ),
    )
    calibrated_roi_weights = None
    calibrated_roi_diagnostics: dict[str, object] = {
        "bfp_roi_mask_projection_status": (
            "not_configured_current_radian_surrogate_mask"
            if not sim_cfg.bfp_roi_mask_path
            else "not_applied_mask_contract_not_calibrated"
        ),
        "bfp_roi_mask_projected_row_count": 0,
        "bfp_roi_mask_projected_sample_count": 0,
    }
    if bool(bfp_roi_mask_contract["bfp_roi_mask_calibrated"]):
        calibrated_roi_rows = load_calibration_rows(str(sim_cfg.bfp_roi_mask_path))
        (
            calibrated_roi_weights,
            calibrated_roi_diagnostics,
        ) = _project_calibrated_bfp_roi_mask_to_tsuyama_q(
            q,
            optical,
            calibrated_roi_rows,
        )
        if not np.any(calibrated_roi_weights > 0.0):
            calibrated_roi_weights = None

    roi_half_width = 2.0 * np.pi * float(optical.NA_collection) / float(
        optical.wavelength_m
    )
    symmetric_diff_roi = integrate_bfp_roi(
        q,
        np.asarray(solver["E_diffraction_BFP"], dtype=complex),
        roi_half_width_rad_per_m=roi_half_width,
    )
    if roi_mask is not None:
        roi_mode = "external_mask"
        roi_diagnostics = {
            "tsuyama_bfp_transmitted_block_q_rad_per_m": None,
            "tsuyama_bfp_lobe_center_q_rad_per_m": None,
            "tsuyama_bfp_lobe_sigma_q_rad_per_m": None,
            **calibrated_roi_diagnostics,
        }
        diff_roi = _integrate_masked_bfp_roi(
            q,
            np.asarray(solver["E_diffraction_BFP"], dtype=complex),
            roi_mask,
        )
        no_channel_roi = _integrate_masked_bfp_roi(
            q,
            np.asarray(solver["E_no_channel_BFP"], dtype=complex),
            roi_mask,
        )
    elif calibrated_roi_weights is not None:
        roi_mode = "calibrated_bfp_roi_mask_projected_1d"
        roi_diagnostics = {
            "tsuyama_bfp_transmitted_block_q_rad_per_m": None,
            "tsuyama_bfp_lobe_center_q_rad_per_m": None,
            "tsuyama_bfp_lobe_sigma_q_rad_per_m": None,
            **calibrated_roi_diagnostics,
        }
        diff_roi = _integrate_weighted_bfp_roi(
            q,
            np.asarray(solver["E_diffraction_BFP"], dtype=complex),
            calibrated_roi_weights,
        )
        no_channel_roi = _integrate_weighted_bfp_roi(
            q,
            np.asarray(solver["E_no_channel_BFP"], dtype=complex),
            calibrated_roi_weights,
        )
    else:
        roi_mode = str(sim_cfg.tsuyama_bfp_roi_mode)
        if roi_mode == "slit_off_axis_lobe_surrogate":
            roi_weights, roi_diagnostics = _build_slit_off_axis_lobe_roi_weights(
                q,
                roi_half_width,
                sim_cfg,
            )
            roi_diagnostics = {
                **roi_diagnostics,
                **calibrated_roi_diagnostics,
            }
            diff_roi = _integrate_weighted_bfp_roi(
                q,
                np.asarray(solver["E_diffraction_BFP"], dtype=complex),
                roi_weights,
            )
            no_channel_roi = _integrate_weighted_bfp_roi(
                q,
                np.asarray(solver["E_no_channel_BFP"], dtype=complex),
                roi_weights,
            )
        else:
            roi_diagnostics = {
                "tsuyama_bfp_transmitted_block_q_rad_per_m": None,
                "tsuyama_bfp_lobe_center_q_rad_per_m": None,
                "tsuyama_bfp_lobe_sigma_q_rad_per_m": None,
                **calibrated_roi_diagnostics,
            }
            diff_roi = symmetric_diff_roi
            no_channel_roi = integrate_bfp_roi(
                q,
                np.asarray(solver["E_no_channel_BFP"], dtype=complex),
                roi_half_width_rad_per_m=roi_half_width,
            )
    full_diffraction_intensity = float(
        np.trapezoid(np.abs(solver["E_diffraction_BFP"]) ** 2, q)
    )
    roi_fraction = (
        float(diff_roi["roi_intensity"]) / full_diffraction_intensity
        if full_diffraction_intensity > 0.0
        else 0.0
    )
    symmetric_vs_slit_ratio = None
    if roi_mode == "slit_off_axis_lobe_surrogate" and float(diff_roi["roi_intensity"]) > 0.0:
        symmetric_vs_slit_ratio = float(symmetric_diff_roi["roi_intensity"]) / float(
            diff_roi["roi_intensity"]
        )
    if roi_mode == "calibrated_bfp_roi_mask_projected_1d":
        detector_bridge_status = (
            "calibrated_roi_mask_projected_1d_no_detector_unit_chain"
        )
        solver_status = "tsuyama_bfp_integrated_calibrated_roi_mask_projected_1d_active"
        route_status = "calibrated_roi_mask_projected_1d_not_calibrated_blank_truth"
    else:
        detector_bridge_status = "surrogate_roi"
        solver_status = "tsuyama_bfp_integrated_surrogate_roi_active"
        route_status = "surrogate_roi_integral_not_calibrated_blank_truth"
    return {
        "E_ref_complex_roi": complex(diff_roi["roi_complex_amplitude"]),
        "I_ref_intensity_roi": float(diff_roi["roi_intensity"]),
        "E_no_channel_complex_roi": complex(no_channel_roi["roi_complex_amplitude"]),
        "I_no_channel_intensity_roi": float(no_channel_roi["roi_intensity"]),
        "reference_detector_bridge_status": detector_bridge_status,
        "reference_solver_route": "tsuyama_bfp_integrated",
        "reference_solver_status": solver_status,
        "reference_solver_detector_bridge_status": detector_bridge_status,
        "reference_solver_active_field_source": (
            "tsuyama_thin_phase_filter_E_diffraction_BFP"
        ),
        "paper_aligned_reference_claim": (
            "paper_aligned_detector_resolved_comparison"
        ),
        "reference_solver_claim_level": (
            "paper_aligned_detector_resolved_comparison"
        ),
        "reference_claim_level": "paper_aligned_detector_resolved_comparison",
        "tsuyama_bfp_integrated_route_status": route_status,
        "tsuyama_bfp_roi_half_width_rad_per_m": float(
            diff_roi["roi_half_width_rad_per_m"]
        ),
        "tsuyama_bfp_roi_sample_count": int(diff_roi["roi_sample_count"]),
        "tsuyama_bfp_roi_mode": roi_mode,
        **roi_diagnostics,
        "tsuyama_bfp_roi_fraction": roi_fraction,
        "tsuyama_bfp_roi_fraction_of_total_diffraction": roi_fraction,
        "tsuyama_bfp_symmetric_vs_slit_roi_ratio": symmetric_vs_slit_ratio,
        **bfp_roi_mask_contract,
        "tsuyama_phase_filter_gaussian_waist_m": gaussian_waist_m,
        "tsuyama_phase_filter_gaussian_waist_source": str(
            illumination_geometry["illumination_geometry_source"]
        ),
        "tsuyama_phase_filter_bfp_q_rad_per_m": q.copy(),
        "tsuyama_E_total_channel_BFP": np.asarray(
            solver["E_total_channel_BFP"],
            dtype=complex,
        ).copy(),
        "tsuyama_E_no_channel_BFP": np.asarray(
            solver["E_no_channel_BFP"],
            dtype=complex,
        ).copy(),
        "tsuyama_E_diffraction_BFP": np.asarray(
            solver["E_diffraction_BFP"],
            dtype=complex,
        ).copy(),
        "tsuyama_E_BFP_complex": np.asarray(
            solver["E_BFP_complex"],
            dtype=complex,
        ).copy(),
        "thin_phase_complex_factor": complex(solver["thin_phase_complex_factor"]),
        "thin_phase_perturbation_phase_rad": float(
            solver["thin_phase_perturbation_phase_rad"]
        ),
        "theta_signed_rad": float(solver["theta_signed_rad"]),
        "reference_index_contrast_signed": float(
            solver["reference_index_contrast_signed"]
        ),
        "phase_filter_validity": solver["phase_filter_validity"],
        "phase_filter_H_over_lambda0": solver["phase_filter_H_over_lambda0"],
        "phase_filter_delta_ref_rad": solver["phase_filter_delta_ref_rad"],
        "phase_filter_theta_signed_rad": solver["phase_filter_theta_signed_rad"],
        "phase_filter_H_over_zR": solver["phase_filter_H_over_zR"],
        "phase_filter_multiple_reflection_warning": solver[
            "phase_filter_multiple_reflection_warning"
        ],
        "sidewall_scattering_roughness_status": solver[
            "sidewall_scattering_roughness_status"
        ],
        "finite_length_assumption_status": solver[
            "finite_length_assumption_status"
        ],
        "subwavelength_groove_validity_status": solver[
            "subwavelength_groove_validity_status"
        ],
        "evanescent_component_unmodeled": solver["evanescent_component_unmodeled"],
        "groove_waveguide_mode_unmodeled": solver[
            "groove_waveguide_mode_unmodeled"
        ],
        "roughness_scatter_unmodeled": solver["roughness_scatter_unmodeled"],
        "depth_validity_reason": solver["depth_validity_reason"],
        "requires_calibration_or_fullwave": solver[
            "requires_calibration_or_fullwave"
        ],
        "tsuyama_phase_filter_numerical_invariants": dict(
            solver["tsuyama_phase_filter_numerical_invariants"]
        ),
    }


def _broadcast_reference_coordinate(
    values: np.ndarray | None,
    fallback_value: float,
    time_s: np.ndarray,
) -> np.ndarray:
    """Resolve reference-field position inputs to a 1D array on the time grid."""
    if values is None:
        return np.full_like(np.asarray(time_s, dtype=float), float(fallback_value), dtype=float)
    arr = np.asarray(values, dtype=float)
    if arr.ndim == 0:
        return np.full_like(np.asarray(time_s, dtype=float), float(arr), dtype=float)
    return arr


def _compute_reference_spatial_profile(
    x_m: np.ndarray,
    z_m: np.ndarray,
    channel: Channel,
    sim_cfg: SimulationConfig,
) -> dict[str, np.ndarray]:
    """
    Build a minimal cross-section surrogate for local reference amplitude/phase.

    The goal is not a full channel-field solution. It is a structured surrogate
    that makes the reference field sensitive to particle position so event-level
    variability does not rely only on illumination/coupling.
    """
    x_arr = np.asarray(x_m, dtype=float)
    z_arr = np.asarray(z_m, dtype=float)
    half_width = max(float(channel.width_m) / 2.0, 1e-12)
    half_depth = max(float(channel.depth_m) / 2.0, 1e-12)
    x_norm = np.clip(x_arr / half_width, -1.0, 1.0)
    z_norm = np.clip(z_arr / half_depth, -1.0, 1.0)

    if sim_cfg.reference_spatial_mode == "uniform":
        amplitude_scale = np.ones_like(x_norm, dtype=float)
        spatial_phase = np.zeros_like(x_norm, dtype=float)
    elif sim_cfg.reference_spatial_mode == "cross_section_surrogate":
        radial_fraction = 0.5 * (x_norm * x_norm + z_norm * z_norm)
        amplitude_scale = 1.0 - float(sim_cfg.reference_spatial_amplitude_strength) * radial_fraction
        amplitude_scale = np.clip(
            amplitude_scale,
            float(sim_cfg.reference_spatial_min_amplitude_scale),
            None,
        )
        phase_coordinate = np.clip(0.7 * z_norm + 0.3 * x_norm, -1.0, 1.0)
        spatial_phase = float(sim_cfg.reference_spatial_phase_strength_rad) * phase_coordinate
    else:
        raise ValueError(f"Unknown reference_spatial_mode: {sim_cfg.reference_spatial_mode}")

    return {
        "x_norm": x_norm,
        "z_norm": z_norm,
        "amplitude_scale": amplitude_scale,
        "spatial_phase_rad": spatial_phase,
    }


def compute_reference_field(
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    medium_refractive_index: float | None = None,
) -> dict:
    """
    Compute the interferometric reference field from nanochannel diffraction.

    Args:
        channel: Channel geometry.
        optical: Optical system configuration.
        sim_cfg: Simulation config (provides rho and reference_model).
        medium_refractive_index: Real refractive index of the channel medium.
            When omitted, a water-like baseline value is used.

    Returns:
        dict with:
            E_ref_complex: complex — reference field as complex number
            A_ref: float — reference field amplitude
            phi_ref_rad: float — reference field phase
            g_ref: float — geometry scaling factor (1.0 for constant mode)
    """
    n_medium = float(
        medium_refractive_index
        if medium_refractive_index is not None
        else _DEFAULT_REFERENCE_MEDIUM_REFRACTIVE_INDEX
    )
    resolved_reference_route = resolve_reference_route_name(
        sim_cfg.reference_model,
        sim_cfg.reference_route,
    )
    resolved_reference_solver_route = resolve_reference_solver_route_name(
        sim_cfg.reference_model,
        sim_cfg.reference_route,
        sim_cfg.reference_solver_route,
    )
    calibration_diagnostics: dict[str, object] = {
        "reference_calibration_amplitude_status": "not_calibrated",
        "reference_calibration_amplitude_source": "unavailable",
        "rho_used_for_reference_amplitude": bool(
            sim_cfg.reference_model
            in {
                "constant",
                "geometry_scaled",
                "channel_angular_surrogate",
                "paper_aligned_phase_filter",
                "tsuyama_bfp_integrated",
            }
        ),
        "reference_phase_calibration_status": "not_calibrated",
        "reference_phase_absolute_claim": "not_measured_absolute_phase",
        "phi_ref_source": None,
        "phi_ref_confidence": None,
        "phase_wrap_policy": None,
    }
    tsuyama_bfp_reference_diagnostics: dict[str, object] = {}

    if sim_cfg.reference_model == "constant":
        A_ref = sim_cfg.rho
        phi_ref = 0.0
        g = 1.0

    elif sim_cfg.reference_model == "geometry_scaled":
        # IMPORTANT: This is a surrogate scaling model for relative ranking,
        # NOT a physical diffraction solution. Do not interpret g as a
        # quantitative diffraction efficiency.
        W0, H0, lambda0 = 800e-9, 550e-9, 660e-9
        g_raw = (
            (channel.width_m / W0) ** sim_cfg.ref_alpha
            * (channel.depth_m / H0) ** sim_cfg.ref_beta
            * (lambda0 / optical.wavelength_m) ** sim_cfg.ref_gamma
        )
        g = max(g_raw, sim_cfg.ref_g_min)
        A_ref = sim_cfg.rho * g
        phi_ref = sim_cfg.ref_phi0_rad
        geometry_scaled_diagnostics = {
            "reference_geometry_width_exponent": float(sim_cfg.ref_alpha),
            "reference_geometry_depth_exponent": float(sim_cfg.ref_beta),
            "reference_geometry_wavelength_exponent": float(sim_cfg.ref_gamma),
            "reference_geometry_depth_scaling_class": _classify_geometry_depth_scaling(
                sim_cfg.ref_beta
            ),
            "reference_geometry_depth_scaling_guidance": (
                "thin_phase_grating expects amplitude~H and intensity~H^2; "
                "geometry_scaled remains an empirical fallback."
            ),
        }
    elif sim_cfg.reference_model in {"channel_angular_surrogate", "paper_aligned_phase_filter"}:
        (
            A_ref,
            phi_ref,
            g,
            operator_signature,
            surrogate_diagnostics,
            angular_field,
            theta_grid_rad,
            phi_grid_rad,
        ) = _angular_surrogate_reference(
            channel,
            optical,
            sim_cfg,
            n_medium,
        )
    elif sim_cfg.reference_model == "tsuyama_bfp_integrated":
        wall_index = float(channel.wall_refractive_index_at(optical.wavelength_m))
        tsuyama_bfp_reference_diagnostics = (
            compute_reference_field_from_tsuyama_bfp(
                channel,
                optical,
                sim_cfg,
                n_medium,
                wall_index,
            )
        )
        E_ref_roi = complex(
            tsuyama_bfp_reference_diagnostics["E_ref_complex_roi"]
        )
        E_no_channel_roi = complex(
            tsuyama_bfp_reference_diagnostics["E_no_channel_complex_roi"]
        )
        roi_scale = abs(E_ref_roi) / max(abs(E_no_channel_roi), 1e-30)
        g = max(float(roi_scale), sim_cfg.ref_g_min)
        A_ref = sim_cfg.rho * g
        phi_ref = float(np.angle(E_ref_roi))
    elif sim_cfg.reference_model == "calibrated_lookup":
        (
            A_ref,
            phi_ref,
            g,
            calibration_extrapolated,
            calibration_diagnostics,
        ) = _lookup_calibrated_reference(
            channel, optical, sim_cfg
        )
    else:
        raise ValueError(f"Unknown reference_model: {sim_cfg.reference_model}")

    # ── Route-aware NA policy for narrow-channel diffraction ──
    # In NODI interferometry the nanochannel itself provides the reference field via
    # diffraction of the incident beam. The first-order diffraction minimum from a
    # slit of width W in medium n occurs at angle θ_diff = arcsin(λ/(n·W)).
    # The collection objective can only accept light within arcsin(NA/n).
    #
    # Engineering cutoff rule (W_min = λ/NA guardrail):
    #   λ/(n·W) > NA/n   ⟺   W < λ/NA  → NO diffracted reference light enters objective
    #   → engineering_fallback / legacy_debug hard-zero A_ref.
    # paper_aligned_comparison and calibrated_primary only record that the
    # guardrail condition was met; their reference amplitude is governed by the
    # soft collection operator or blank-channel calibration provenance.
    #
    # Key example: 660 nm in 700 nm channel (n=1.33, NA=0.9)
    #   θ_diff = arcsin(660/(1.33×700)) = arcsin(0.709) = 45.1°
    #   θ_NA   = arcsin(0.9/1.33)       = arcsin(0.677) = 42.6°
    #   45.1° > 42.6°  → hard guardrail applies only on engineering/legacy routes.
    #
    # Reference: Tsuyama et al. 2022 Lab Chip (geometry constraints);
    #            工程文件 41_实验对齐原则 Principle 1 (W_min table).
    # [Fix added: previously missing, caused incorrect non-zero A_ref for narrow channels]
    _diff_ratio = float(optical.wavelength_m) / max(
        float(n_medium) * float(channel.width_m), 1e-18
    )
    _na_ratio = float(optical.NA_collection) / max(float(n_medium), 1e-9)
    _na_cutoff_condition_met = bool(_diff_ratio > _na_ratio or _diff_ratio >= 1.0)
    _na_hard_zero_allowed = resolved_reference_route in {
        "engineering_fallback",
        "legacy_debug",
    }
    _na_cutoff_active = bool(_na_cutoff_condition_met and _na_hard_zero_allowed)
    _na_cutoff_policy = (
        "hard_guardrail"
        if _na_hard_zero_allowed
        else "soft_operator_no_hard_zero"
    )
    if _na_cutoff_active:
        A_ref = 0.0
        g = 0.0

    polarization = resolve_polarization_coupling(
        sim_cfg.reference_projection_mode,
        sim_cfg.scattering_projection_mode,
        sim_cfg.cross_polarization_leakage,
    )
    reference_amplitude_factor = float(polarization["amplitude_factor"])
    A_ref_raw = float(A_ref)
    g_ref_geometry = float(g)
    A_ref = A_ref_raw * reference_amplitude_factor
    g = g_ref_geometry * reference_amplitude_factor

    E_ref_complex = A_ref * np.exp(1j * phi_ref)

    result = {
        "E_ref_complex": complex(E_ref_complex),
        "A_ref": float(A_ref),
        "A_ref_unprojected": A_ref_raw,
        "phi_ref_rad": float(phi_ref),
        "g_ref": float(g),
        "g_ref_geometry": g_ref_geometry,
        "reference_medium_refractive_index": float(n_medium),
        "na_cutoff_active": bool(_na_cutoff_active),
        "na_cutoff_condition_met": bool(_na_cutoff_condition_met),
        "na_cutoff_hard_zero_applied": bool(_na_cutoff_active),
        "na_cutoff_policy": _na_cutoff_policy,
        "na_cutoff_diff_ratio": float(_diff_ratio),
        "na_cutoff_na_ratio": float(_na_ratio),
        "na_cutoff_NA_collection": float(optical.NA_collection),
        "na_cutoff_W_min_m": float(optical.wavelength_m / max(optical.NA_collection, 1e-9)),
        "reference_projection_mode": str(polarization["requested_mode"]),
        "reference_projection_effective_mode": str(polarization["effective_mode"]),
        "reference_detector_polarization_mode": str(polarization["detector_mode"]),
        "reference_projection_amplitude_factor": reference_amplitude_factor,
        "reference_projection_alignment_status": str(polarization["alignment_status"]),
        "reference_cross_polarization_leakage": float(
            polarization["cross_polarization_leakage"]
        ),
        "reference_diffraction_efficiency_model": "unavailable",
        "reference_diffraction_efficiency_zeroth_order": None,
        "reference_diffraction_efficiency_first_order": None,
        "reference_field_amplitude_envelope_role": "unavailable",
        "reference_field_amplitude_envelope_nominal": None,
        "reference_field_amplitude_envelope_lower": None,
        "reference_field_amplitude_envelope_upper": None,
        "reference_field_amplitude_envelope_lower_factor": float(
            _REFERENCE_FIELD_ENVELOPE_LOWER_FACTOR
        ),
        "reference_field_amplitude_envelope_upper_factor": float(
            _REFERENCE_FIELD_ENVELOPE_UPPER_FACTOR
        ),
    }
    result.update(
        build_projection_basis_diagnostics(
            "reference",
            polarization,
            sim_cfg.scattering_projection_mode,
        )
    )
    result.update(_reference_model_metadata(sim_cfg, resolved_reference_route))
    result.update(calibration_diagnostics)
    if sim_cfg.reference_model == "calibrated_lookup":
        result.update({
            "reference_solver_active_field_source": "calibrated_lookup",
            "reference_solver_detector_bridge_status": "calibrated_lookup_active",
            "paper_aligned_reference_claim": "calibrated_reference",
        })
        result["calibration_extrapolated"] = bool(calibration_extrapolated)
        if result["reference_calibration_amplitude_status"] == "calibrated_scale_only":
            result["reference_claim_level"] = "reference_calibrated_scale_only"
    if sim_cfg.reference_model in {"channel_angular_surrogate", "paper_aligned_phase_filter"}:
        result["operator_signature"] = operator_signature
        result["reference_angular_field"] = np.asarray(angular_field, dtype=complex).copy()
        result["reference_theta_grid_rad"] = np.asarray(theta_grid_rad, dtype=float).copy()
        result["reference_phi_grid_rad"] = np.asarray(phi_grid_rad, dtype=float).copy()
        result.update(surrogate_diagnostics)
        result["reference_solver_route"] = resolved_reference_solver_route
        if resolved_reference_solver_route == "tsuyama_phase_filter_1d":
            result.update(
                _tsuyama_phase_filter_reference_diagnostics(
                    channel,
                    optical,
                    sim_cfg,
                    n_medium,
                )
            )
        elif resolved_reference_solver_route == "paper_aligned_angular_surrogate":
            result.update({
                "reference_solver_status": "paper_aligned_angular_surrogate_active",
                "reference_solver_detector_bridge_status": "angular_surrogate_direct",
                "reference_solver_active_field_source": "paper_aligned_angular_surrogate",
                "paper_aligned_reference_claim": "paper_aligned_angular_surrogate_comparison",
                "reference_solver_claim_level": "angular_surrogate_comparison",
            })
        elif resolved_reference_solver_route == "engineering_channel_angular_surrogate":
            result.update({
                "reference_solver_status": "engineering_channel_angular_surrogate_active",
                "reference_solver_detector_bridge_status": "angular_surrogate_direct",
                "reference_solver_active_field_source": "angular_surrogate",
                "paper_aligned_reference_claim": "not_applicable_engineering_surrogate",
                "reference_solver_claim_level": "engineering_ranking_surrogate",
            })
    if sim_cfg.reference_model == "tsuyama_bfp_integrated":
        result.update(tsuyama_bfp_reference_diagnostics)
    if sim_cfg.reference_model == "geometry_scaled":
        result["reference_solver_route"] = resolved_reference_solver_route
        result.update(geometry_scaled_diagnostics)
    if sim_cfg.reference_model in {"constant", "calibrated_lookup"}:
        result["reference_solver_route"] = resolved_reference_solver_route
    return result


def compute_reference_field_trace(
    trajectory: dict,
    reference: dict,
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    *,
    initial_x_m: float = 0.0,
    initial_z_m: float = 0.0,
    export_full_diagnostics: bool = True,
) -> dict:
    """
    Promote a case-level reference field into an event/trajectory-level trace.

    Returns a time-dependent local reference field `E_ref(x(t), z(t))` while
    preserving the existing case-level reference amplitude/phase as the anchor.
    """
    time_s = np.asarray(trajectory["time_s"], dtype=float)
    x_path = _broadcast_reference_coordinate(trajectory.get("x_m"), initial_x_m, time_s)
    z_path = _broadcast_reference_coordinate(trajectory.get("z_m"), initial_z_m, time_s)
    spatial = _compute_reference_spatial_profile(x_path, z_path, channel, sim_cfg)

    A_ref_base = float(reference["A_ref"])
    phi_ref_base = float(reference["phi_ref_rad"])
    A_ref_local = A_ref_base * spatial["amplitude_scale"]
    phi_ref_local = phi_ref_base + spatial["spatial_phase_rad"]

    result = {
        "A_ref_trace": A_ref_local,
        "phi_ref_trace_rad": phi_ref_local,
        "reference_amplitude_scale": spatial["amplitude_scale"],
        "reference_spatial_phase_rad": spatial["spatial_phase_rad"],
        "reference_spatial_mode": sim_cfg.reference_spatial_mode,
        "reference_spatial_amplitude_strength": float(sim_cfg.reference_spatial_amplitude_strength),
        "reference_spatial_phase_strength_rad": float(sim_cfg.reference_spatial_phase_strength_rad),
        "reference_spatial_min_amplitude_scale": float(sim_cfg.reference_spatial_min_amplitude_scale),
        "reference_wavelength_m": float(optical.wavelength_m),
    }
    if export_full_diagnostics:
        result.update(
            {
                "E_ref_trace_complex": A_ref_local * np.exp(1j * phi_ref_local),
                "reference_x_norm": spatial["x_norm"],
                "reference_z_norm": spatial["z_norm"],
            }
        )
    return result
