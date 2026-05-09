"""
Package-local laser illumination envelope module for NODI interferometric simulation.

Computes the focused laser illumination envelope at particle positions.
Uses a 3D Gaussian beam intensity profile plus a minimal complex-envelope
surrogate for focal phase evolution.

Key design choice:
    A_env (field envelope) is computed, NOT intensity directly.
    A_env is multiplied onto the scattering FIELD amplitude, not intensity.

    I_inc(x,y,z) = I₀ · exp[-2(x-xf)²/wx² - 2(y-yf)²/wy² - 2(z-zf)²/wz²]
    A_env = √(I_inc / I₀) = exp[-(x-xf)²/wx² - (y-yf)²/wy² - (z-zf)²/wz²]
    E_env_complex = A_env · exp(i·phi_beam)
"""

import numpy as np

from .data_objects import OpticalSystem, SimulationConfig
from .optional_acceleration import optional_numba_njit, warn_numba_unavailable
from .utils import build_projection_basis_diagnostics, resolve_polarization_coupling

try:
    from numba import njit as _numba_njit, prange as _numba_prange
except Exception:  # pragma: no cover - optional acceleration dependency
    warn_numba_unavailable("illumination kernels")
    _numba_njit = None
    _numba_prange = range

_optional_numba_njit = optional_numba_njit(_numba_njit)


@_optional_numba_njit(cache=True, parallel=True)
def _illumination_light_2d_kernel(
    x_rel: np.ndarray,
    y_rel: np.ndarray,
    z_rel: np.ndarray,
    beam_waist_x_m: float,
    beam_waist_y_m: float,
    beam_waist_z_m: float,
    z_rayleigh: float,
    k_medium: float,
    amplitude_factor: float,
    overfill: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rows, cols = y_rel.shape
    A_env = np.empty((rows, cols), dtype=np.float64)
    A_env_scalar = np.empty((rows, cols), dtype=np.float64)
    phi_beam = np.empty((rows, cols), dtype=np.float64)
    phi_gouy = np.empty((rows, cols), dtype=np.float64)
    phi_curv = np.empty((rows, cols), dtype=np.float64)
    beam_waist_x_sq = beam_waist_x_m * beam_waist_x_m
    beam_waist_y_sq = beam_waist_y_m * beam_waist_y_m
    beam_waist_z_sq = beam_waist_z_m * beam_waist_z_m
    z_rayleigh_sq = z_rayleigh * z_rayleigh

    for row_idx in _numba_prange(rows):
        for col_idx in range(cols):
            x_val = x_rel[row_idx, col_idx]
            y_val = y_rel[row_idx, col_idx]
            z_val = z_rel[row_idx, col_idx]
            x_sq = x_val * x_val
            y_sq = y_val * y_val
            z_sq = z_val * z_val
            exponent = -y_sq / beam_waist_y_sq
            if not overfill:
                exponent = (
                    exponent
                    - x_sq / beam_waist_x_sq
                    - z_sq / beam_waist_z_sq
                )
            scalar_env = np.exp(exponent)
            gouy = np.arctan(y_val / z_rayleigh)
            curv = (
                0.5
                * k_medium
                * (x_sq + z_sq)
                * y_val
                / (y_sq + z_rayleigh_sq)
            )
            A_env_scalar[row_idx, col_idx] = scalar_env
            A_env[row_idx, col_idx] = scalar_env * amplitude_factor
            phi_gouy[row_idx, col_idx] = gouy
            phi_curv[row_idx, col_idx] = curv
            phi_beam[row_idx, col_idx] = gouy + curv

    return A_env, A_env_scalar, phi_beam, phi_gouy, phi_curv


def compute_illumination_envelope(
    x_m: np.ndarray,
    y_m: np.ndarray,
    z_m: np.ndarray,
    optical: OpticalSystem,
    medium_refractive_index: float = 1.0,
    sim_cfg: SimulationConfig | None = None,
    *,
    export_full_diagnostics: bool = True,
) -> dict:
    """
    Compute illumination field envelope and intensity along a trajectory.

    Args:
        x_m: x-coordinates of particle positions (meters).
        y_m: y-coordinates of particle positions (meters).
        z_m: z-coordinates of particle positions (meters).
        optical: Optical system (provides beam waists, focus position, I₀).
        medium_refractive_index: Refractive index used for the minimal beam-phase
            surrogate. Defaults to 1.0 so existing callers remain compatible.
        sim_cfg: Optional simulation config. When provided, the illumination
            envelope is projected onto the active scattering polarization channel.
        export_full_diagnostics: When False, omit heavy arrays that are not
            needed by stream-summary event blocks.

    Returns:
        dict with:
            I_inc_W_m2: np.ndarray — local intensity at each position
            A_env: np.ndarray — field envelope √(I/I₀), range [0, 1]
            phi_beam_rad: np.ndarray — minimal focal phase surrogate
            E_env_complex: np.ndarray — complex field envelope
    """
    illumination_geometry = optical.resolve_illumination_geometry()
    beam_waist_x_m = float(illumination_geometry["illumination_beam_waist_x_m"])
    beam_waist_y_m = float(illumination_geometry["illumination_beam_waist_y_m"])
    beam_waist_z_m = float(illumination_geometry["illumination_beam_waist_z_m"])

    x_rel = np.asarray(x_m, dtype=float) - optical.focus_x_m
    y_rel = np.asarray(y_m, dtype=float) - optical.focus_y_m
    z_rel = np.asarray(z_m, dtype=float) - optical.focus_z_m

    if sim_cfg is None:
        polarization = {
            "requested_mode": "legacy_scalar",
            "effective_mode": "intensity_proxy",
            "detector_mode": "intensity_proxy",
            "amplitude_factor": 1.0,
            "alignment_status": "legacy_scalar",
            "cross_polarization_leakage": 0.0,
        }
    else:
        polarization = resolve_polarization_coupling(
            sim_cfg.illumination_polarization_mode,
            sim_cfg.scattering_projection_mode,
            sim_cfg.cross_polarization_leakage,
        )
    amplitude_factor = float(polarization["amplitude_factor"])

    # Field envelope exponent (coefficient is -1, not -2, because A_env = √(I/I₀)).
    # We keep the flow-axis (y) transit window explicit even in overfill mode:
    # Tsuyama's "uniform illumination" means x/z coverage across the channel is
    # nearly flat, not that the particle sees constant illumination for the full
    # simulated time trace.

    # ── Overfill illumination mode (Tsuyama 2022 experimental method) ──────────────
    # Tsuyama et al. 2022 uses a NA=0.45 objective for illumination, producing a
    # ~2 μm beam spot that is significantly larger than the 800 nm channel width.
    # Result: ALL nanoparticles traverse near the center of the laser spot and
    # receive nearly uniform irradiance across x/z particle paths.
    # Quote from paper: "all nanoparticles pass through near the center of the laser
    # spot, ensuring almost the same laser illumination for all nanoparticles."
    #
    # Importantly, "overfill" should not flatten the longitudinal transit window
    # along y. Nanoparticles still cross the focal region within a finite ~10 ms
    # interaction window, so transit-time / bandwidth diagnostics must preserve
    # the y-envelope while suppressing only the x/z path-to-path variation.
    #
    # In "tight_focus" mode, the Gaussian beam waist is comparable to or smaller
    # than the channel width: edge particles are penalized by exp(-(x/w)²),
    # which does NOT match Tsuyama's illumination conditions.
    #
    # Reference: Tsuyama et al. 2022, Lab Chip; 工程文件 41_实验対齐原则 Principle 2.
    # [Fix added: simulation–experiment alignment, April 2026]
    _active_illumination_mode = (
        sim_cfg.illumination_mode if sim_cfg is not None else "tight_focus"
    )
    n_medium = max(float(medium_refractive_index), 1e-9)
    w_eff = float(np.sqrt(beam_waist_x_m * beam_waist_z_m))
    z_rayleigh = max(np.pi * n_medium * (w_eff ** 2) / optical.wavelength_m, optical.wavelength_m)
    k_medium = 2.0 * np.pi * n_medium / optical.wavelength_m
    overfill = _active_illumination_mode == "overfill"

    if (
        not export_full_diagnostics
        and _numba_njit is not None
        and x_rel.ndim == 2
        and y_rel.shape == x_rel.shape
        and z_rel.shape == x_rel.shape
    ):
        (
            A_env,
            A_env_scalar,
            phi_beam,
            phi_gouy_surrogate,
            phi_curv,
        ) = _illumination_light_2d_kernel(
            np.ascontiguousarray(x_rel, dtype=np.float64),
            np.ascontiguousarray(y_rel, dtype=np.float64),
            np.ascontiguousarray(z_rel, dtype=np.float64),
            beam_waist_x_m,
            beam_waist_y_m,
            beam_waist_z_m,
            float(z_rayleigh),
            float(k_medium),
            amplitude_factor,
            overfill,
        )
    else:
        x_rel_sq = x_rel * x_rel
        y_rel_sq = y_rel * y_rel
        z_rel_sq = z_rel * z_rel
        exponent_y = -y_rel_sq / (beam_waist_y_m**2)
        if overfill:
            exponent = exponent_y
        else:
            exponent = (
                exponent_y
                - x_rel_sq / (beam_waist_x_m**2)
                - z_rel_sq / (beam_waist_z_m**2)
            )

        A_env_scalar = np.exp(exponent)

        # Minimal complex Gaussian-beam surrogate:
        # - Gouy-like term follows arctan(y/z_R)
        # - Curvature term uses the inverse wavefront radius 1/R(y),
        #   which tends to 0 at focus (flat wavefront) and grows away from focus.
        phi_gouy_surrogate = np.arctan(y_rel / z_rayleigh)
        wavefront_radius_den = y_rel_sq + z_rayleigh**2
        radial_distance_sq = x_rel_sq + z_rel_sq
        phi_curv = 0.5 * k_medium * radial_distance_sq * y_rel / wavefront_radius_den
        phi_beam = phi_gouy_surrogate + phi_curv
        A_env = A_env_scalar * amplitude_factor
    result = {
        "A_env": A_env,
        "A_env_scalar": A_env_scalar,
        "phi_beam_rad": phi_beam,
        "phi_beam_gouy_rad": phi_gouy_surrogate,
        "phi_beam_curv_rad": phi_curv,
        "beam_rayleigh_range_m": float(z_rayleigh),
        "illumination_beam_waist_x_m": beam_waist_x_m,
        "illumination_beam_waist_y_m": beam_waist_y_m,
        "illumination_beam_waist_z_m": beam_waist_z_m,
        "illumination_geometry_source": str(
            illumination_geometry["illumination_geometry_source"]
        ),
        "illumination_geometry_decoupled_from_legacy_shared_beam": bool(
            illumination_geometry["illumination_geometry_decoupled_from_legacy_shared_beam"]
        ),
        "illumination_polarization_mode": str(polarization["requested_mode"]),
        "illumination_polarization_effective_mode": str(polarization["effective_mode"]),
        "illumination_detector_polarization_mode": str(polarization["detector_mode"]),
        "illumination_polarization_amplitude_factor": amplitude_factor,
        "illumination_polarization_alignment_status": str(
            polarization["alignment_status"]
        ),
        "illumination_cross_polarization_leakage": float(
            polarization["cross_polarization_leakage"]
        ),
        **build_projection_basis_diagnostics(
            "illumination",
            polarization,
            sim_cfg.scattering_projection_mode if sim_cfg is not None else "intensity_proxy",
        ),
    }
    if export_full_diagnostics:
        inverse_wavefront_radius = y_rel / wavefront_radius_den
        # Intensity: I = I₀ · A_env². Stream-summary block paths do not read
        # these heavy arrays, so they can opt out without changing fields used
        # for signal generation.
        result.update(
            {
                "beam_inverse_wavefront_radius_m_inv": inverse_wavefront_radius,
                "I_inc_W_m2": optical.peak_irradiance_W_m2 * A_env**2,
                "I_inc_scalar_W_m2": (
                    optical.peak_irradiance_W_m2 * A_env_scalar**2
                ),
                "E_env_complex": A_env * np.exp(1j * phi_beam),
            }
        )
    return result
