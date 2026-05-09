from __future__ import annotations

"""
Package-local Tsuyama 2020 thin phase-filter reference-field utilities.

This module is intentionally independent from the existing angular surrogate.
It provides a one-dimensional scalar phase-filter solver that exports complex
BFP fields and numerical invariants for paper-aligned comparison lanes. It is
not yet a full detector-unit model.
"""

import numpy as np


def classify_phase_filter_validity(
    *,
    channel_width_m: float,
    channel_depth_m: float,
    wavelength_m: float,
    medium_refractive_index: float,
    wall_refractive_index: float,
    gaussian_waist_m: float | None = None,
) -> dict[str, object]:
    """Classify whether a scalar thin phase-filter comparison is in-domain."""
    width = float(channel_width_m)
    depth = float(channel_depth_m)
    lambda0 = float(wavelength_m)
    n_medium = float(medium_refractive_index)
    n_wall = float(wall_refractive_index)
    h_over_lambda = depth / max(lambda0, 1e-18)
    theta_signed = 2.0 * np.pi * (n_medium - n_wall) * depth / max(lambda0, 1e-18)
    delta_ref = 2.0 * np.pi * abs(n_wall - n_medium) * depth / max(lambda0, 1e-18)

    if h_over_lambda <= 0.8:
        validity = "within_phase_filter_assumption"
        reason = "H/lambda0<=0.8 conservative scalar phase-filter range"
    elif h_over_lambda <= 1.5:
        validity = "extrapolated_phase_filter"
        reason = "0.8<H/lambda0<=1.5; scalar phase-filter extrapolation"
    else:
        validity = "requires_blank_or_fullwave"
        reason = "H/lambda0>1.5; require blank calibration or RCWA/FDTD/full-wave support"

    lambda_eff = lambda0 / max(n_medium, 1e-18)
    width_over_lambda_eff = width / max(lambda_eff, 1e-18)
    if width_over_lambda_eff < 0.75:
        subwavelength_status = "fullwave_required"
    elif width_over_lambda_eff < 1.25:
        subwavelength_status = "scalar_extrapolated"
    else:
        subwavelength_status = "scalar_phase_filter_ok"

    if gaussian_waist_m is None or gaussian_waist_m <= 0:
        h_over_zr = None
    else:
        z_rayleigh = np.pi * float(gaussian_waist_m) ** 2 / max(lambda0, 1e-18)
        h_over_zr = depth / max(z_rayleigh, 1e-18)

    return {
        "phase_filter_H_over_lambda0": float(h_over_lambda),
        "phase_filter_delta_ref_rad": float(delta_ref),
        "phase_filter_theta_signed_rad": float(theta_signed),
        "phase_filter_H_over_zR": None if h_over_zr is None else float(h_over_zr),
        "phase_filter_validity": validity,
        "phase_filter_multiple_reflection_warning": (
            "unmodeled_check_required" if h_over_lambda > 0.8 else "not_triggered"
        ),
        "sidewall_scattering_roughness_status": "unmodeled",
        "finite_length_assumption_status": "infinite_1d_phase_filter",
        "subwavelength_groove_validity_status": subwavelength_status,
        "evanescent_component_unmodeled": True,
        "groove_waveguide_mode_unmodeled": True,
        "roughness_scatter_unmodeled": True,
        "depth_validity_reason": reason,
        "requires_calibration_or_fullwave": bool(
            validity == "requires_blank_or_fullwave"
            or subwavelength_status == "fullwave_required"
        ),
    }


def _fft_continuous_forward(field_x: np.ndarray, dx_m: float) -> np.ndarray:
    """Approximate F(q)=int f(x) exp(-i q x) dx on an FFT grid."""
    return np.fft.fftshift(np.fft.fft(np.fft.ifftshift(field_x))) * float(dx_m)


def _parseval_relative_error(field_x: np.ndarray, field_q: np.ndarray, dx_m: float, dq_rad_m: float) -> float:
    spatial_power = float(np.trapezoid(np.abs(field_x) ** 2, dx=dx_m))
    spectral_power = float(np.trapezoid(np.abs(field_q) ** 2, dx=dq_rad_m) / (2.0 * np.pi))
    return float(abs(spatial_power - spectral_power) / max(spatial_power, 1e-30))


def compute_tsuyama_phase_filter_bfp_field(
    *,
    channel_width_m: float,
    channel_depth_m: float,
    wavelength_m: float,
    medium_refractive_index: float,
    wall_refractive_index: float,
    gaussian_waist_m: float,
    n_grid: int = 4096,
    grid_extent_factor: float = 8.0,
) -> dict[str, object]:
    """
    Compute a scalar 1D thin phase-filter BFP field.

    The phase filter occupies ``|x| <= W/2`` and uses the signed perturbation
    factor ``exp(i*theta_signed)-1``. The returned diffraction field is exactly
    ``E_total_channel_BFP - E_no_channel_BFP`` on the FFT grid.
    """
    width = float(channel_width_m)
    depth = float(channel_depth_m)
    lambda0 = float(wavelength_m)
    n_medium = float(medium_refractive_index)
    n_wall = float(wall_refractive_index)
    omega0 = float(gaussian_waist_m)
    if width <= 0 or depth < 0 or lambda0 <= 0 or omega0 <= 0:
        raise ValueError("channel width, wavelength, and gaussian waist must be positive; depth must be non-negative")
    if n_grid < 128:
        raise ValueError("n_grid must be >= 128")

    half_extent = max(0.5 * float(grid_extent_factor) * omega0, 4.0 * width, 4.0 * lambda0)
    x_m = np.linspace(-half_extent, half_extent, int(n_grid), endpoint=False)
    dx_m = float(x_m[1] - x_m[0])
    q_rad_m = np.fft.fftshift(np.fft.fftfreq(int(n_grid), d=dx_m)) * 2.0 * np.pi
    dq_rad_m = float(q_rad_m[1] - q_rad_m[0])

    incident_field_x = np.exp(-((x_m / omega0) ** 2))
    aperture = np.abs(x_m) <= (0.5 * width)
    theta_signed = 2.0 * np.pi * (n_medium - n_wall) * depth / lambda0
    complex_factor = complex(np.exp(1j * theta_signed) - 1.0)
    transmission = np.ones_like(incident_field_x, dtype=complex)
    transmission[aperture] = np.exp(1j * theta_signed)

    no_channel_x = incident_field_x.astype(complex)
    total_channel_x = incident_field_x * transmission
    thin_phase_basis_x = incident_field_x * aperture.astype(float)
    diffraction_x = total_channel_x - no_channel_x

    e_no = _fft_continuous_forward(no_channel_x, dx_m)
    e_total = _fft_continuous_forward(total_channel_x, dx_m)
    e_basis = _fft_continuous_forward(thin_phase_basis_x, dx_m)
    e_diff = e_total - e_no
    e_diff_from_factor = complex_factor * e_basis

    parseval_error = _parseval_relative_error(no_channel_x, e_no, dx_m, dq_rad_m)
    decomposition_error = float(
        np.max(np.abs(e_diff - e_diff_from_factor))
        / max(np.max(np.abs(e_diff_from_factor)), 1e-30)
    )
    validity = classify_phase_filter_validity(
        channel_width_m=width,
        channel_depth_m=depth,
        wavelength_m=lambda0,
        medium_refractive_index=n_medium,
        wall_refractive_index=n_wall,
        gaussian_waist_m=omega0,
    )

    return {
        "x_m": x_m,
        "incident_field_x": incident_field_x,
        "phase_filter_aperture_x": aperture,
        "E_total_channel_x": total_channel_x,
        "E_no_channel_x": no_channel_x,
        "E_diffraction_x": diffraction_x,
        "bfp_q_rad_per_m": q_rad_m,
        "E_total_channel_BFP": e_total,
        "E_no_channel_BFP": e_no,
        "E_diffraction_BFP": e_diff,
        "E_BFP_complex": e_total,
        "thin_phase_basis_BFP": e_basis,
        "I_BFP": np.abs(e_total) ** 2,
        "thin_phase_complex_factor": complex_factor,
        "thin_phase_perturbation_phase_rad": float(np.angle(complex_factor)),
        "theta_signed_rad": float(theta_signed),
        "reference_index_contrast_signed": float(n_medium - n_wall),
        "reference_solver_route": "tsuyama_phase_filter_1d",
        "tsuyama_phase_filter_numerical_invariants": {
            "W_code_convention": "W_code=2*l_paper",
            "H_code_convention": "H_code=d_paper",
            "lambda0_definition": "vacuum_wavelength_m",
            "omega0_convention": "field_amplitude_exp(-(x/omega0)^2)",
            "fft_sign_convention": "forward_exp_minus_i_q_x",
            "grid_n": int(n_grid),
            "grid_dx_m": float(dx_m),
            "grid_extent_m": float(2.0 * half_extent),
            "zero_padding_policy": "implicit_periodic_fft_grid_extent",
            "bfp_coordinate": "q_rad_per_m",
            "power_normalization_check": (
                "parseval_pass" if parseval_error < 1e-10 else "parseval_warning"
            ),
            "parseval_relative_error": float(parseval_error),
            "reference_decomposition_relative_error": float(decomposition_error),
        },
        **validity,
    }


def decompose_tsuyama_reference_field(**kwargs: object) -> dict[str, object]:
    """Compatibility wrapper that returns total/no-channel/diffracted fields."""
    return compute_tsuyama_phase_filter_bfp_field(**kwargs)


def integrate_bfp_roi(
    bfp_q_rad_per_m: np.ndarray,
    field_bfp: np.ndarray,
    *,
    roi_half_width_rad_per_m: float,
) -> dict[str, object]:
    """Integrate a complex BFP field over a symmetric 1D ROI."""
    q = np.asarray(bfp_q_rad_per_m, dtype=float)
    field = np.asarray(field_bfp, dtype=complex)
    half_width = float(roi_half_width_rad_per_m)
    if q.shape != field.shape:
        raise ValueError("bfp_q_rad_per_m and field_bfp must have the same shape")
    if half_width <= 0:
        raise ValueError("roi_half_width_rad_per_m must be positive")

    mask = np.abs(q) <= half_width
    if not np.any(mask):
        return {
            "roi_complex_amplitude": 0.0 + 0.0j,
            "roi_intensity": 0.0,
            "roi_sample_count": 0,
            "detector_mask_units": "rad_per_m",
            "roi_half_width_rad_per_m": half_width,
        }
    return {
        "roi_complex_amplitude": complex(np.trapezoid(field[mask], q[mask])),
        "roi_intensity": float(np.trapezoid(np.abs(field[mask]) ** 2, q[mask])),
        "roi_sample_count": int(np.count_nonzero(mask)),
        "detector_mask_units": "rad_per_m",
        "roi_half_width_rad_per_m": half_width,
    }
