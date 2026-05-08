"""
NODI Interferometric Simulator — Trajectory Module

Generates single-particle trajectory through the detection zone.

Coordinate convention:
    y: flow direction
    x: channel width direction, [-W/2, W/2]
    z: channel depth direction, [-H/2, H/2]

Supports pure advection (y = v·t, x = const, z = const) and optional
Brownian diffusion with reflecting boundary conditions, position-dependent
axial flow, and near-wall diffusion hindrance surrogates.
"""

from dataclasses import dataclass
from functools import lru_cache
import math
import numpy as np

from .data_objects import Channel, OpticalSystem, SimulationConfig
from .optional_acceleration import warn_numba_unavailable

try:
    from numba import njit, prange
except Exception:  # pragma: no cover - optional acceleration dependency
    warn_numba_unavailable("trajectory kernels")
    njit = None
    prange = range


def _optional_njit(*args, **kwargs):
    """Return a no-op decorator when numba is unavailable."""
    if njit is None:
        def decorator(func):
            return func
        return decorator
    return njit(*args, **kwargs)


_FLOW_PROFILE_PLUG = 0
_FLOW_PROFILE_PARABOLIC_RECT = 1
_FLOW_PROFILE_RECT_SERIES = 2

_HINDRANCE_NONE = 0
_HINDRANCE_NEAR_WALL = 1
_HINDRANCE_TENSOR = 2

_EMPTY_FLOAT_ARRAY = np.empty(0, dtype=float)


@dataclass(frozen=True)
class TrajectoryContext:
    """Case-level trajectory constants reused across events."""

    n_samples: int
    dt_s: float
    time_s: np.ndarray
    half_w: float
    half_h: float
    rect_series_mean_raw: float | None
    rect_series_lam_arr: np.ndarray | None
    rect_series_cosh_den_arr: np.ndarray | None
    rect_series_inv_n3_arr: np.ndarray | None


def _accessible_half_spans(
    channel: Channel,
    particle_radius_m: float = 0.0,
) -> tuple[float, float]:
    """Return the accessible half-width / half-depth for the particle center."""
    half_w = channel.width_m / 2.0 - particle_radius_m
    half_h = channel.depth_m / 2.0 - particle_radius_m
    if half_w <= 0 or half_h <= 0:
        raise ValueError(
            "Particle radius is too large for the channel cross-section: "
            f"radius={particle_radius_m:.2e}m, width={channel.width_m:.2e}m, "
            f"depth={channel.depth_m:.2e}m"
        )
    return float(half_w), float(half_h)


def _flow_profile_peak_factor(flow_profile_model: str) -> float:
    """Return the centerline / mean velocity factor for the selected profile."""
    if flow_profile_model == "plug":
        return 1.0
    if flow_profile_model == "parabolic_rect":
        # 9/4 rescales (1-u^2)(1-v^2) so the cross-section average equals 1.
        return 2.25
    if flow_profile_model == "rect_series":
        # Conservative upper bound for rectangular-duct Poiseuille centerline/mean ratio.
        return 3.0
    raise ValueError(f"Unknown flow_profile_model: {flow_profile_model}")


def _rect_series_shape_raw(
    x_m: np.ndarray,
    z_m: np.ndarray,
    half_w: float,
    half_h: float,
    n_terms: int = 15,
) -> np.ndarray:
    """
    Truncated rectangular-duct Poiseuille series (raw, not mean-normalized).

    This is a compact fully developed laminar-flow surrogate based on the
    standard odd-series solution. We normalize it numerically afterwards so
    `mean_flow_velocity_m_s` retains its “accessible cross-section mean” meaning.
    """
    x = np.asarray(x_m, dtype=float)
    z = np.asarray(z_m, dtype=float)
    out = np.zeros_like(x, dtype=float)
    for n in range(1, 2 * n_terms, 2):
        lam = n * np.pi / (2.0 * half_w)
        cos_part = np.cos(lam * x)
        cosh_den = np.cosh(lam * half_h)
        term = (1.0 - np.cosh(lam * z) / cosh_den) * cos_part / (n ** 3)
        out = out + term
    return np.maximum(out, 0.0)


@lru_cache(maxsize=128)
def _rect_series_mean_factor_cached(
    half_w_nm: float,
    half_h_nm: float,
    n_terms: int,
) -> tuple[float, float]:
    """Return mean raw shape and centerline/mean ratio for cached accessible spans."""
    half_w = half_w_nm * 1e-9
    half_h = half_h_nm * 1e-9
    x = np.linspace(-half_w, half_w, 81)
    z = np.linspace(-half_h, half_h, 81)
    xx, zz = np.meshgrid(x, z, indexing="xy")
    raw = _rect_series_shape_raw(xx, zz, half_w, half_h, n_terms=n_terms)
    mean_raw = float(np.mean(raw))
    center_raw = float(_rect_series_shape_raw(np.array([0.0]), np.array([0.0]), half_w, half_h, n_terms=n_terms)[0])
    peak_factor = center_raw / mean_raw if mean_raw > 0 else 1.0
    return mean_raw, peak_factor


def _rect_series_mean_factor(half_w: float, half_h: float, n_terms: int = 15) -> tuple[float, float]:
    return _rect_series_mean_factor_cached(
        round(half_w * 1e9, 6),
        round(half_h * 1e9, 6),
        int(n_terms),
    )


def _precompute_rect_series_terms(
    half_w: float,
    half_h: float,
    n_terms: int = 15,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Precompute rect-series coefficients reused along one trajectory."""
    odd_n = np.arange(1, 2 * n_terms, 2, dtype=float)
    lam = odd_n * math.pi / (2.0 * half_w)
    cosh_den = np.cosh(lam * half_h)
    inv_n3 = 1.0 / (odd_n ** 3)
    return lam, cosh_den, inv_n3


def build_trajectory_context(
    channel: Channel,
    sim_cfg: SimulationConfig,
    particle_radius_m: float = 0.0,
) -> TrajectoryContext:
    """Precompute trajectory constants shared by all events in one case."""
    half_w, half_h = _accessible_half_spans(channel, particle_radius_m)
    rect_series_mean_raw = None
    rect_series_lam_arr = None
    rect_series_cosh_den_arr = None
    rect_series_inv_n3_arr = None
    if sim_cfg.flow_profile_model == "rect_series":
        rect_series_mean_raw, _ = _rect_series_mean_factor(half_w, half_h, n_terms=15)
        (
            rect_series_lam_arr,
            rect_series_cosh_den_arr,
            rect_series_inv_n3_arr,
        ) = _precompute_rect_series_terms(half_w, half_h, n_terms=15)
    return TrajectoryContext(
        n_samples=int(sim_cfg.n_samples),
        dt_s=float(sim_cfg.dt_s),
        time_s=np.arange(sim_cfg.n_samples) * sim_cfg.dt_s,
        half_w=half_w,
        half_h=half_h,
        rect_series_mean_raw=rect_series_mean_raw,
        rect_series_lam_arr=rect_series_lam_arr,
        rect_series_cosh_den_arr=rect_series_cosh_den_arr,
        rect_series_inv_n3_arr=rect_series_inv_n3_arr,
    )


def _clip_scalar(value: float, lo: float, hi: float) -> float:
    """Cheap scalar clip used by the trajectory hot path."""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _rect_series_shape_raw_scalar(
    x_m: float,
    z_m: float,
    half_w: float,
    half_h: float,
    n_terms: int = 15,
    *,
    lam_arr: np.ndarray | None = None,
    cosh_den_arr: np.ndarray | None = None,
    inv_n3_arr: np.ndarray | None = None,
) -> float:
    """Scalar specialization of the rectangular-series flow surrogate."""
    if lam_arr is None or cosh_den_arr is None or inv_n3_arr is None:
        lam_arr, cosh_den_arr, inv_n3_arr = _precompute_rect_series_terms(
            half_w,
            half_h,
            n_terms=n_terms,
        )
    out = 0.0
    for idx in range(len(lam_arr)):
        lam = float(lam_arr[idx])
        cos_part = math.cos(lam * x_m)
        term = (
            1.0 - math.cosh(lam * z_m) / float(cosh_den_arr[idx])
        ) * cos_part * float(inv_n3_arr[idx])
        out += term
    return max(out, 0.0)


def _single_wall_parallel_factor_scalar(gap_m: float, particle_radius_m: float) -> float:
    """Scalar single-wall parallel mobility surrogate."""
    denom = max(gap_m + particle_radius_m, 1e-18)
    chi = _clip_scalar(particle_radius_m / denom, 0.0, 0.999)
    factor = 1.0 - 9.0 / 16.0 * chi + 0.125 * chi**3 - 45.0 / 256.0 * chi**4 - 0.0625 * chi**5
    return _clip_scalar(factor, 0.08, 1.0)


def _single_wall_perpendicular_factor_scalar(gap_m: float, particle_radius_m: float) -> float:
    """Scalar single-wall perpendicular mobility surrogate."""
    denom = max(gap_m + particle_radius_m, 1e-18)
    chi = _clip_scalar(particle_radius_m / denom, 0.0, 0.999)
    factor = 1.0 - 1.004 * chi + 0.418 * chi**3 + 0.21 * chi**4 - 0.169 * chi**5
    return _clip_scalar(factor, 0.03, 1.0)


def _single_wall_parallel_factor(gap_m: np.ndarray, particle_radius_m: float) -> np.ndarray:
    """Single-wall parallel mobility surrogate."""
    chi = np.clip(
        particle_radius_m / np.maximum(gap_m + particle_radius_m, 1e-18),
        0.0,
        0.999,
    )
    factor = 1.0 - 9.0 / 16.0 * chi + 0.125 * chi**3 - 45.0 / 256.0 * chi**4 - 0.0625 * chi**5
    return np.clip(factor, 0.08, 1.0)


def _single_wall_perpendicular_factor(gap_m: np.ndarray, particle_radius_m: float) -> np.ndarray:
    """Single-wall perpendicular mobility surrogate."""
    chi = np.clip(
        particle_radius_m / np.maximum(gap_m + particle_radius_m, 1e-18),
        0.0,
        0.999,
    )
    factor = 1.0 - 1.004 * chi + 0.418 * chi**3 + 0.21 * chi**4 - 0.169 * chi**5
    return np.clip(factor, 0.03, 1.0)


def _soft_two_wall_faxen_blend_scalar(
    gap_x_m: float,
    gap_z_m: float,
    particle_radius_m: float,
) -> tuple[float, float]:
    """Scalar specialization of the softened two-wall Faxen blend."""
    side_parallel = _single_wall_parallel_factor_scalar(gap_x_m, particle_radius_m)
    side_perp = _single_wall_perpendicular_factor_scalar(gap_x_m, particle_radius_m)
    depth_parallel = _single_wall_parallel_factor_scalar(gap_z_m, particle_radius_m)
    depth_perp = _single_wall_perpendicular_factor_scalar(gap_z_m, particle_radius_m)
    if gap_x_m >= 5.0 * particle_radius_m:
        side_parallel = 1.0
        side_perp = 1.0
    if gap_z_m >= 5.0 * particle_radius_m:
        depth_parallel = 1.0
        depth_perp = 1.0
    fx = _clip_scalar(math.sqrt(side_perp * depth_parallel), 0.03, 1.0)
    depth_bias = math.sqrt(depth_perp / max(depth_parallel, 1e-18))
    fz = _clip_scalar(math.sqrt(side_parallel * depth_perp) * depth_bias, 0.02, 1.0)
    return fx, fz


def _soft_two_wall_faxen_blend(
    gap_x_m: np.ndarray,
    gap_z_m: np.ndarray,
    particle_radius_m: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Return a softer Faxen-like two-wall blend for near_wall_surrogate mode.

    The goal is to move away from the previous purely empirical gap-power law
    without making `near_wall_surrogate` identical to the more aggressive
    `anisotropic_tensor_surrogate`.

    Interpretation:
        - x motion is perpendicular to side walls and parallel to top/bottom walls
        - z motion is perpendicular to top/bottom walls and parallel to side walls

    We combine the corresponding single-wall factors through a square-root blend
    so the result keeps the correct a/h trend while remaining less severe than
    the tensor-product mode.
    """
    side_parallel = _single_wall_parallel_factor(gap_x_m, particle_radius_m)
    side_perp = _single_wall_perpendicular_factor(gap_x_m, particle_radius_m)
    depth_parallel = _single_wall_parallel_factor(gap_z_m, particle_radius_m)
    depth_perp = _single_wall_perpendicular_factor(gap_z_m, particle_radius_m)
    far_x = gap_x_m >= 5.0 * particle_radius_m
    far_z = gap_z_m >= 5.0 * particle_radius_m
    side_parallel = np.where(far_x, 1.0, side_parallel)
    side_perp = np.where(far_x, 1.0, side_perp)
    depth_parallel = np.where(far_z, 1.0, depth_parallel)
    depth_perp = np.where(far_z, 1.0, depth_perp)
    fx = np.clip(np.sqrt(side_perp * depth_parallel), 0.03, 1.0)
    depth_bias = np.sqrt(depth_perp / np.maximum(depth_parallel, 1e-18))
    fz = np.clip(np.sqrt(side_parallel * depth_perp) * depth_bias, 0.02, 1.0)
    return fx, fz


def estimate_max_axial_velocity(sim_cfg: SimulationConfig) -> float:
    """Upper-bound axial velocity used for conservative timing validation."""
    return float(
        sim_cfg.mean_flow_velocity_m_s
        * _flow_profile_peak_factor(sim_cfg.flow_profile_model)
    )


def _axial_velocity_scalar(
    x_m: float,
    z_m: float,
    channel: Channel,
    sim_cfg: SimulationConfig,
    particle_radius_m: float = 0.0,
    *,
    half_w: float | None = None,
    half_h: float | None = None,
    rect_series_mean_raw: float | None = None,
    rect_series_lam_arr: np.ndarray | None = None,
    rect_series_cosh_den_arr: np.ndarray | None = None,
    rect_series_inv_n3_arr: np.ndarray | None = None,
) -> float:
    """Scalar specialization of the axial flow surrogate."""
    if sim_cfg.flow_profile_model == "plug":
        return float(sim_cfg.mean_flow_velocity_m_s)

    if half_w is None or half_h is None:
        half_w, half_h = _accessible_half_spans(channel, particle_radius_m)

    if sim_cfg.flow_profile_model == "parabolic_rect":
        u = _clip_scalar(x_m / half_w, -1.0, 1.0)
        v = _clip_scalar(z_m / half_h, -1.0, 1.0)
        factor = max(2.25 * (1.0 - u**2) * (1.0 - v**2), 0.0)
        return float(sim_cfg.mean_flow_velocity_m_s * factor)

    if sim_cfg.flow_profile_model == "rect_series":
        if rect_series_mean_raw is None:
            rect_series_mean_raw, _ = _rect_series_mean_factor(half_w, half_h, n_terms=15)
        raw = _rect_series_shape_raw_scalar(
            x_m,
            z_m,
            half_w,
            half_h,
            n_terms=15,
            lam_arr=rect_series_lam_arr,
            cosh_den_arr=rect_series_cosh_den_arr,
            inv_n3_arr=rect_series_inv_n3_arr,
        )
        factor = raw / max(rect_series_mean_raw, 1e-15)
        return float(sim_cfg.mean_flow_velocity_m_s * factor)

    raise ValueError(f"Unknown flow_profile_model: {sim_cfg.flow_profile_model}")


def axial_velocity_m_s(
    x_m: float | np.ndarray,
    z_m: float | np.ndarray,
    channel: Channel,
    sim_cfg: SimulationConfig,
    particle_radius_m: float = 0.0,
) -> float | np.ndarray:
    """
    Surrogate axial flow profile inside the rectangular channel.

    plug:
        v_y = mean_flow_velocity

    parabolic_rect:
        v_y = mean_flow_velocity * 9/4 * (1 - (x/half_w_acc)^2) * (1 - (z/half_h_acc)^2)

    rect_series:
        fully developed rectangular-duct odd-series solution, numerically
        normalized so the accessible cross-section mean equals mean_flow_velocity.

    This is intentionally a compact surrogate rather than an exact rectangular
    Poiseuille solution. The goal is to introduce slower near-wall streamlines
    and faster centerline trajectories without making the simulator intractable.
    """
    if np.isscalar(x_m) and np.isscalar(z_m):
        return _axial_velocity_scalar(
            float(x_m),
            float(z_m),
            channel,
            sim_cfg,
            particle_radius_m=particle_radius_m,
        )

    x = np.asarray(x_m, dtype=float)
    z = np.asarray(z_m, dtype=float)

    if sim_cfg.flow_profile_model == "plug":
        out = np.full_like(x, sim_cfg.mean_flow_velocity_m_s, dtype=float)
        return float(out) if out.ndim == 0 else out

    if sim_cfg.flow_profile_model == "parabolic_rect":
        half_w, half_h = _accessible_half_spans(channel, particle_radius_m)
        u = np.clip(x / half_w, -1.0, 1.0)
        v = np.clip(z / half_h, -1.0, 1.0)
        factor = 2.25 * (1.0 - u ** 2) * (1.0 - v ** 2)
        factor = np.maximum(factor, 0.0)
        out = sim_cfg.mean_flow_velocity_m_s * factor
        return float(out) if out.ndim == 0 else out

    if sim_cfg.flow_profile_model == "rect_series":
        half_w, half_h = _accessible_half_spans(channel, particle_radius_m)
        raw = _rect_series_shape_raw(x, z, half_w, half_h, n_terms=15)
        mean_raw, _ = _rect_series_mean_factor(half_w, half_h, n_terms=15)
        factor = raw / max(mean_raw, 1e-15)
        out = sim_cfg.mean_flow_velocity_m_s * factor
        return float(out) if out.ndim == 0 else out

    raise ValueError(f"Unknown flow_profile_model: {sim_cfg.flow_profile_model}")


def _hindered_diffusion_factors_scalar(
    x_m: float,
    z_m: float,
    channel: Channel,
    particle_radius_m: float,
    sim_cfg: SimulationConfig,
    *,
    half_w: float | None = None,
    half_h: float | None = None,
) -> tuple[float, float]:
    """Scalar specialization of the hindered-diffusion surrogate."""
    if sim_cfg.diffusion_hindrance_model == "none" or particle_radius_m <= 0:
        return 1.0, 1.0

    if half_w is None or half_h is None:
        half_w, half_h = _accessible_half_spans(channel, particle_radius_m)

    gap_x = max(half_w - abs(x_m), 0.0)
    gap_z = max(half_h - abs(z_m), 0.0)

    if sim_cfg.diffusion_hindrance_model == "near_wall_surrogate":
        return _soft_two_wall_faxen_blend_scalar(gap_x, gap_z, particle_radius_m)

    if sim_cfg.diffusion_hindrance_model != "anisotropic_tensor_surrogate":
        raise ValueError(
            f"Unknown diffusion_hindrance_model: {sim_cfg.diffusion_hindrance_model}"
        )

    side_parallel = _single_wall_parallel_factor_scalar(gap_x, particle_radius_m)
    side_perp = _single_wall_perpendicular_factor_scalar(gap_x, particle_radius_m)
    depth_parallel = _single_wall_parallel_factor_scalar(gap_z, particle_radius_m)
    depth_perp = _single_wall_perpendicular_factor_scalar(gap_z, particle_radius_m)
    fx = _clip_scalar(side_perp * depth_parallel, 0.02, 1.0)
    fz = _clip_scalar(side_parallel * depth_perp, 0.02, 1.0)
    return fx, fz


def hindered_diffusion_factors(
    x_m: float | np.ndarray,
    z_m: float | np.ndarray,
    channel: Channel,
    particle_radius_m: float,
    sim_cfg: SimulationConfig,
) -> tuple[np.ndarray | float, np.ndarray | float]:
    """
    Surrogate near-wall diffusion suppression factors in x/z.

    Returns multiplicative factors in [0, 1] that scale the free-space
    diffusion coefficient in x/z. In `anisotropic_tensor_surrogate` mode,
    directional wall couplings are combined using parallel/perpendicular
    single-wall mobility surrogates, so x and z no longer differ by a purely
    ad-hoc exponent.
    """
    if np.isscalar(x_m) and np.isscalar(z_m):
        return _hindered_diffusion_factors_scalar(
            float(x_m),
            float(z_m),
            channel,
            particle_radius_m,
            sim_cfg,
        )

    x = np.asarray(x_m, dtype=float)
    z = np.asarray(z_m, dtype=float)

    if sim_cfg.diffusion_hindrance_model == "none" or particle_radius_m <= 0:
        ones = np.ones_like(x, dtype=float)
        return (float(ones) if ones.ndim == 0 else ones,
                float(ones) if ones.ndim == 0 else ones)

    if sim_cfg.diffusion_hindrance_model == "near_wall_surrogate":
        half_w, half_h = _accessible_half_spans(channel, particle_radius_m)
        gap_x = np.maximum(half_w - np.abs(x), 0.0)
        gap_z = np.maximum(half_h - np.abs(z), 0.0)
        fx, fz = _soft_two_wall_faxen_blend(gap_x, gap_z, particle_radius_m)
        return (float(fx) if fx.ndim == 0 else fx,
                float(fz) if fz.ndim == 0 else fz)

    if sim_cfg.diffusion_hindrance_model != "anisotropic_tensor_surrogate":
        raise ValueError(
            f"Unknown diffusion_hindrance_model: {sim_cfg.diffusion_hindrance_model}"
        )

    half_w, half_h = _accessible_half_spans(channel, particle_radius_m)
    gap_x = np.maximum(half_w - np.abs(x), 0.0)
    gap_z = np.maximum(half_h - np.abs(z), 0.0)
    side_parallel = _single_wall_parallel_factor(gap_x, particle_radius_m)
    side_perp = _single_wall_perpendicular_factor(gap_x, particle_radius_m)
    depth_parallel = _single_wall_parallel_factor(gap_z, particle_radius_m)
    depth_perp = _single_wall_perpendicular_factor(gap_z, particle_radius_m)

    fx = np.clip(side_perp * depth_parallel, 0.02, 1.0)
    fz = np.clip(side_parallel * depth_perp, 0.02, 1.0)
    return (float(fx) if fx.ndim == 0 else fx,
            float(fz) if fz.ndim == 0 else fz)


def _axial_transport_velocity_scalar(
    x_m: float,
    z_m: float,
    channel: Channel,
    sim_cfg: SimulationConfig,
    particle_radius_m: float = 0.0,
    *,
    half_w: float | None = None,
    half_h: float | None = None,
    rect_series_mean_raw: float | None = None,
    rect_series_lam_arr: np.ndarray | None = None,
    rect_series_cosh_den_arr: np.ndarray | None = None,
    rect_series_inv_n3_arr: np.ndarray | None = None,
) -> float:
    """Scalar specialization of axial transport including near-wall drag."""
    base = _axial_velocity_scalar(
        x_m,
        z_m,
        channel,
        sim_cfg,
        particle_radius_m=particle_radius_m,
        half_w=half_w,
        half_h=half_h,
        rect_series_mean_raw=rect_series_mean_raw,
        rect_series_lam_arr=rect_series_lam_arr,
        rect_series_cosh_den_arr=rect_series_cosh_den_arr,
        rect_series_inv_n3_arr=rect_series_inv_n3_arr,
    )
    if (
        sim_cfg.diffusion_hindrance_model != "anisotropic_tensor_surrogate"
        or particle_radius_m <= 0
    ):
        return base

    if half_w is None or half_h is None:
        half_w, half_h = _accessible_half_spans(channel, particle_radius_m)

    gap_x = max(half_w - abs(x_m), 0.0)
    gap_z = max(half_h - abs(z_m), 0.0)
    fy = _single_wall_parallel_factor_scalar(gap_x, particle_radius_m) * _single_wall_parallel_factor_scalar(gap_z, particle_radius_m)
    return float(base * fy)


def axial_transport_velocity_m_s(
    x_m: float | np.ndarray,
    z_m: float | np.ndarray,
    channel: Channel,
    sim_cfg: SimulationConfig,
    particle_radius_m: float = 0.0,
) -> float | np.ndarray:
    """
    Effective axial transport velocity including optional near-wall mobility drag.

    The underlying flow profile still comes from `axial_velocity_m_s`. In the
    anisotropic tensor surrogate, we additionally apply the parallel-to-wall
    mobility reduction along the axial direction to avoid overly optimistic
    near-wall transit speeds.
    """
    if np.isscalar(x_m) and np.isscalar(z_m):
        return _axial_transport_velocity_scalar(
            float(x_m),
            float(z_m),
            channel,
            sim_cfg,
            particle_radius_m=particle_radius_m,
        )

    base = axial_velocity_m_s(
        x_m,
        z_m,
        channel,
        sim_cfg,
        particle_radius_m=particle_radius_m,
    )
    if (
        sim_cfg.diffusion_hindrance_model != "anisotropic_tensor_surrogate"
        or particle_radius_m <= 0
    ):
        return base

    x = np.asarray(x_m, dtype=float)
    z = np.asarray(z_m, dtype=float)
    half_w, half_h = _accessible_half_spans(channel, particle_radius_m)
    gap_x = np.maximum(half_w - np.abs(x), 0.0)
    gap_z = np.maximum(half_h - np.abs(z), 0.0)
    fy = _single_wall_parallel_factor(gap_x, particle_radius_m) * _single_wall_parallel_factor(gap_z, particle_radius_m)
    out = np.asarray(base, dtype=float) * fy
    return float(out) if out.ndim == 0 else out


@_optional_njit(cache=True)
def _clip_scalar_kernel(value: float, lo: float, hi: float) -> float:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


@_optional_njit(cache=True)
def _reflect_kernel(value: float, lo: float, hi: float) -> float:
    while value < lo or value > hi:
        if value < lo:
            value = 2.0 * lo - value
        if value > hi:
            value = 2.0 * hi - value
    return value


@_optional_njit(cache=True)
def _single_wall_parallel_factor_kernel(gap_m: float, particle_radius_m: float) -> float:
    denom = max(gap_m + particle_radius_m, 1e-18)
    chi = _clip_scalar_kernel(particle_radius_m / denom, 0.0, 0.999)
    factor = (
        1.0
        - 9.0 / 16.0 * chi
        + 0.125 * chi ** 3
        - 45.0 / 256.0 * chi ** 4
        - 0.0625 * chi ** 5
    )
    return _clip_scalar_kernel(factor, 0.08, 1.0)


@_optional_njit(cache=True)
def _single_wall_perpendicular_factor_kernel(gap_m: float, particle_radius_m: float) -> float:
    denom = max(gap_m + particle_radius_m, 1e-18)
    chi = _clip_scalar_kernel(particle_radius_m / denom, 0.0, 0.999)
    factor = 1.0 - 1.004 * chi + 0.418 * chi ** 3 + 0.21 * chi ** 4 - 0.169 * chi ** 5
    return _clip_scalar_kernel(factor, 0.03, 1.0)


@_optional_njit(cache=True)
def _rect_series_shape_raw_scalar_kernel(
    x_m: float,
    z_m: float,
    lam_arr: np.ndarray,
    cosh_den_arr: np.ndarray,
    inv_n3_arr: np.ndarray,
) -> float:
    out = 0.0
    for idx in range(len(lam_arr)):
        lam = lam_arr[idx]
        term = (
            1.0 - math.cosh(lam * z_m) / cosh_den_arr[idx]
        ) * math.cos(lam * x_m) * inv_n3_arr[idx]
        out += term
    if out < 0.0:
        return 0.0
    return out


@_optional_njit(cache=True)
def _simulate_diffusive_trajectory_kernel(
    n_samples: int,
    dt: float,
    initial_x_m: float,
    initial_z_m: float,
    y_start: float,
    initial_v_y: float,
    half_w: float,
    half_h: float,
    particle_radius_m: float,
    diffusion_step_scale: float,
    diffusion_draws: np.ndarray,
    mean_flow_velocity: float,
    reflecting_boundary: bool,
    flow_profile_code: int,
    hindrance_code: int,
    rect_series_mean_raw: float,
    rect_series_lam_arr: np.ndarray,
    rect_series_cosh_den_arr: np.ndarray,
    rect_series_inv_n3_arr: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    x_m = np.empty(n_samples, dtype=np.float64)
    z_m = np.empty(n_samples, dtype=np.float64)
    y_m = np.empty(n_samples, dtype=np.float64)
    v_y_m_s = np.empty(n_samples, dtype=np.float64)

    x_m[0] = initial_x_m
    z_m[0] = initial_z_m
    y_m[0] = y_start
    v_y_m_s[0] = initial_v_y

    use_parabolic_rect = flow_profile_code == _FLOW_PROFILE_PARABOLIC_RECT
    use_rect_series = flow_profile_code == _FLOW_PROFILE_RECT_SERIES
    use_near_wall = (
        hindrance_code == _HINDRANCE_NEAR_WALL and particle_radius_m > 0.0
    )
    use_tensor = (
        hindrance_code == _HINDRANCE_TENSOR and particle_radius_m > 0.0
    )
    has_hindrance = use_near_wall or use_tensor
    inv_rect_series_mean = (
        1.0 / max(rect_series_mean_raw, 1e-15) if use_rect_series else 0.0
    )
    far_gap_threshold = 5.0 * particle_radius_m

    for i in range(n_samples - 1):
        x_curr = x_m[i]
        z_curr = z_m[i]
        fx = 1.0
        fz = 1.0

        if has_hindrance:
            gap_x = max(half_w - abs(x_curr), 0.0)
            gap_z = max(half_h - abs(z_curr), 0.0)
            side_parallel = _single_wall_parallel_factor_kernel(gap_x, particle_radius_m)
            side_perp = _single_wall_perpendicular_factor_kernel(gap_x, particle_radius_m)
            depth_parallel = _single_wall_parallel_factor_kernel(gap_z, particle_radius_m)
            depth_perp = _single_wall_perpendicular_factor_kernel(gap_z, particle_radius_m)
            if use_near_wall:
                if gap_x >= far_gap_threshold:
                    side_parallel = 1.0
                    side_perp = 1.0
                if gap_z >= far_gap_threshold:
                    depth_parallel = 1.0
                    depth_perp = 1.0
                fx = _clip_scalar_kernel(math.sqrt(side_perp * depth_parallel), 0.03, 1.0)
                depth_bias = math.sqrt(depth_perp / max(depth_parallel, 1e-18))
                fz = _clip_scalar_kernel(
                    math.sqrt(side_parallel * depth_perp) * depth_bias,
                    0.02,
                    1.0,
                )
            else:
                fx = _clip_scalar_kernel(side_perp * depth_parallel, 0.02, 1.0)
                fz = _clip_scalar_kernel(side_parallel * depth_perp, 0.02, 1.0)

        dx = diffusion_step_scale * math.sqrt(fx) * diffusion_draws[2 * i]
        dz = diffusion_step_scale * math.sqrt(fz) * diffusion_draws[2 * i + 1]

        x_new = x_curr + dx
        z_new = z_curr + dz

        if reflecting_boundary:
            x_new = _reflect_kernel(x_new, -half_w, half_w)
            z_new = _reflect_kernel(z_new, -half_h, half_h)

        x_m[i + 1] = x_new
        z_m[i + 1] = z_new
        y_m[i + 1] = y_m[i] + v_y_m_s[i] * dt

        if use_rect_series:
            raw = _rect_series_shape_raw_scalar_kernel(
                x_new,
                z_new,
                rect_series_lam_arr,
                rect_series_cosh_den_arr,
                rect_series_inv_n3_arr,
            )
            base_velocity = mean_flow_velocity * raw * inv_rect_series_mean
        elif use_parabolic_rect:
            u = _clip_scalar_kernel(x_new / half_w, -1.0, 1.0)
            v = _clip_scalar_kernel(z_new / half_h, -1.0, 1.0)
            base_velocity = mean_flow_velocity * max(
                2.25 * (1.0 - u * u) * (1.0 - v * v),
                0.0,
            )
        else:
            base_velocity = mean_flow_velocity

        if use_tensor:
            gap_x_new = max(half_w - abs(x_new), 0.0)
            gap_z_new = max(half_h - abs(z_new), 0.0)
            base_velocity *= (
                _single_wall_parallel_factor_kernel(gap_x_new, particle_radius_m)
                * _single_wall_parallel_factor_kernel(gap_z_new, particle_radius_m)
            )
        v_y_m_s[i + 1] = base_velocity

    return x_m, y_m, z_m, v_y_m_s


def simulate_particle_trajectory(
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    initial_x_m: float,
    initial_z_m: float,
    particle_radius_m: float = 0.0,
    diffusion_coefficient: float | None = None,
    rng: np.random.Generator | None = None,
    trajectory_context: TrajectoryContext | None = None,
) -> dict:
    """
    Generate a single-particle trajectory through the detection zone.

    The particle enters from y_start and travels along y at constant velocity.
    y_start is chosen so the particle reaches focus_y at approximately 50%
    of total_time, ensuring the first 20% of the trace is background-only.

    When include_diffusion=True and diffusion_coefficient is provided,
    x(t) and z(t) undergo Brownian random walk with reflecting boundary
    conditions at the channel walls.

    Args:
        channel: Channel geometry (for boundary validation and reflection).
        optical: Optical system (provides beam_waist_y, focus_y for y_start).
        sim_cfg: Simulation config (provides velocity, timing, diffusion settings).
        initial_x_m: Initial x position within channel.
        initial_z_m: Initial z position within channel.
        diffusion_coefficient: Stokes-Einstein D in m²/s. Required if
            include_diffusion=True. Ignored otherwise.
        rng: Random number generator (required for diffusion).

    Returns:
        dict with:
            time_s: np.ndarray — time array
            x_m: np.ndarray — x positions
            y_m: np.ndarray — y positions (flow direction)
            z_m: np.ndarray — z positions

    Raises:
        ValueError: If initial position is outside channel, or if diffusion
            is requested without diffusion_coefficient.
    """
    # Validate initial position
    if trajectory_context is None:
        trajectory_context = build_trajectory_context(
            channel,
            sim_cfg,
            particle_radius_m=particle_radius_m,
        )
    half_w = trajectory_context.half_w
    half_h = trajectory_context.half_h

    if abs(initial_x_m) > half_w:
        raise ValueError(
            f"initial_x ({initial_x_m:.2e}m) outside channel width "
            f"[{-half_w:.2e}, {half_w:.2e}]"
        )
    if abs(initial_z_m) > half_h:
        raise ValueError(
            f"initial_z ({initial_z_m:.2e}m) outside channel depth "
            f"[{-half_h:.2e}, {half_h:.2e}]"
        )

    # Time grid
    n_samples = trajectory_context.n_samples
    dt = trajectory_context.dt_s
    time_s = trajectory_context.time_s
    rect_series_mean_raw = trajectory_context.rect_series_mean_raw
    rect_series_lam_arr = trajectory_context.rect_series_lam_arr
    rect_series_cosh_den_arr = trajectory_context.rect_series_cosh_den_arr
    rect_series_inv_n3_arr = trajectory_context.rect_series_inv_n3_arr

    # y direction: place the event approximately at the center of the time window
    # using the local streamline speed at the initial position.
    initial_v_y = _axial_transport_velocity_scalar(
        initial_x_m,
        initial_z_m,
        channel,
        sim_cfg,
        particle_radius_m=particle_radius_m,
        half_w=half_w,
        half_h=half_h,
        rect_series_mean_raw=rect_series_mean_raw,
        rect_series_lam_arr=rect_series_lam_arr,
        rect_series_cosh_den_arr=rect_series_cosh_den_arr,
        rect_series_inv_n3_arr=rect_series_inv_n3_arr,
    )
    y_start = optical.focus_y_m - initial_v_y * sim_cfg.total_time_s / 2.0

    # x, z directions
    if sim_cfg.include_diffusion:
        if diffusion_coefficient is None or diffusion_coefficient <= 0:
            raise ValueError(
                "diffusion_coefficient must be positive when include_diffusion=True, "
                f"got {diffusion_coefficient}"
            )
        if rng is None:
            rng = np.random.default_rng()

        diffusion_step_scale = math.sqrt(2.0 * diffusion_coefficient * dt)
        # Preserve the original RNG draw order (x-step then z-step) while
        # avoiding two Python RNG calls per time step.
        diffusion_draws = np.asarray(
            rng.standard_normal(2 * max(n_samples - 1, 0)),
            dtype=float,
        )
        if sim_cfg.flow_profile_model == "plug":
            flow_profile_code = _FLOW_PROFILE_PLUG
        elif sim_cfg.flow_profile_model == "parabolic_rect":
            flow_profile_code = _FLOW_PROFILE_PARABOLIC_RECT
        else:
            flow_profile_code = _FLOW_PROFILE_RECT_SERIES

        if sim_cfg.diffusion_hindrance_model == "none":
            hindrance_code = _HINDRANCE_NONE
        elif sim_cfg.diffusion_hindrance_model == "near_wall_surrogate":
            hindrance_code = _HINDRANCE_NEAR_WALL
        else:
            hindrance_code = _HINDRANCE_TENSOR

        x_m, y_m, z_m, v_y_m_s = _simulate_diffusive_trajectory_kernel(
            n_samples,
            dt,
            initial_x_m,
            initial_z_m,
            y_start,
            initial_v_y,
            half_w,
            half_h,
            particle_radius_m,
            diffusion_step_scale,
            diffusion_draws,
            float(sim_cfg.mean_flow_velocity_m_s),
            bool(sim_cfg.reflecting_boundary),
            flow_profile_code,
            hindrance_code,
            0.0 if rect_series_mean_raw is None else float(rect_series_mean_raw),
            _EMPTY_FLOAT_ARRAY if rect_series_lam_arr is None else rect_series_lam_arr,
            _EMPTY_FLOAT_ARRAY if rect_series_cosh_den_arr is None else rect_series_cosh_den_arr,
            _EMPTY_FLOAT_ARRAY if rect_series_inv_n3_arr is None else rect_series_inv_n3_arr,
        )

    else:
        # Pure advection: constant x, z and streamline-specific axial velocity.
        x_m = np.full(n_samples, initial_x_m)
        z_m = np.full(n_samples, initial_z_m)
        v_y_value = _axial_transport_velocity_scalar(
            initial_x_m,
            initial_z_m,
            channel,
            sim_cfg,
            particle_radius_m=particle_radius_m,
            half_w=half_w,
            half_h=half_h,
            rect_series_mean_raw=rect_series_mean_raw,
            rect_series_lam_arr=rect_series_lam_arr,
            rect_series_cosh_den_arr=rect_series_cosh_den_arr,
            rect_series_inv_n3_arr=rect_series_inv_n3_arr,
        )
        v_y_m_s = np.full(n_samples, v_y_value)
        y_m = y_start + v_y_value * time_s

    return {
        "time_s": time_s,
        "x_m": x_m,
        "y_m": y_m,
        "z_m": z_m,
        "v_y_m_s": v_y_m_s,
    }


@_optional_njit(cache=True, parallel=True)
def _simulate_plug_diffusive_trajectory_block_kernel(
    n_samples: int,
    dt: float,
    initial_x_m: np.ndarray,
    initial_z_m: np.ndarray,
    y_start: np.ndarray,
    initial_v_y: np.ndarray,
    half_w: float,
    half_h: float,
    diffusion_step_scale: float,
    diffusion_draws: np.ndarray,
    reflecting_boundary: bool,
    store_velocity_trace: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    block_size = initial_x_m.shape[0]
    x_m = np.empty((block_size, n_samples), dtype=np.float64)
    z_m = np.empty((block_size, n_samples), dtype=np.float64)
    y_m = np.empty((block_size, n_samples), dtype=np.float64)
    velocity_cols = n_samples if store_velocity_trace else 0
    v_y_m_s = np.empty((block_size, velocity_cols), dtype=np.float64)

    for event_idx in prange(block_size):
        x_m[event_idx, 0] = initial_x_m[event_idx]
        z_m[event_idx, 0] = initial_z_m[event_idx]
        y_m[event_idx, 0] = y_start[event_idx]
        v_y = initial_v_y[event_idx]
        if store_velocity_trace:
            v_y_m_s[event_idx, 0] = v_y

        for sample_idx in range(n_samples - 1):
            draw_offset = 2 * sample_idx
            x_new = (
                x_m[event_idx, sample_idx]
                + diffusion_step_scale * diffusion_draws[event_idx, draw_offset]
            )
            z_new = (
                z_m[event_idx, sample_idx]
                + diffusion_step_scale * diffusion_draws[event_idx, draw_offset + 1]
            )

            if reflecting_boundary:
                x_new = _reflect_kernel(x_new, -half_w, half_w)
                z_new = _reflect_kernel(z_new, -half_h, half_h)

            x_m[event_idx, sample_idx + 1] = x_new
            z_m[event_idx, sample_idx + 1] = z_new
            y_m[event_idx, sample_idx + 1] = y_m[event_idx, sample_idx] + v_y * dt
            if store_velocity_trace:
                v_y_m_s[event_idx, sample_idx + 1] = v_y

    return x_m, y_m, z_m, v_y_m_s


@_optional_njit(cache=True, parallel=True)
def _simulate_diffusive_trajectory_block_kernel(
    n_samples: int,
    dt: float,
    initial_x_m: np.ndarray,
    initial_z_m: np.ndarray,
    y_start: np.ndarray,
    initial_v_y: np.ndarray,
    half_w: float,
    half_h: float,
    particle_radius_m: float,
    diffusion_step_scale: float,
    diffusion_draws: np.ndarray,
    mean_flow_velocity: float,
    reflecting_boundary: bool,
    flow_profile_code: int,
    hindrance_code: int,
    rect_series_mean_raw: float,
    rect_series_lam_arr: np.ndarray,
    rect_series_cosh_den_arr: np.ndarray,
    rect_series_inv_n3_arr: np.ndarray,
    store_velocity_trace: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    block_size = initial_x_m.shape[0]
    x_m = np.empty((block_size, n_samples), dtype=np.float64)
    z_m = np.empty((block_size, n_samples), dtype=np.float64)
    y_m = np.empty((block_size, n_samples), dtype=np.float64)
    velocity_cols = n_samples if store_velocity_trace else 0
    v_y_m_s = np.empty((block_size, velocity_cols), dtype=np.float64)

    use_parabolic_rect = flow_profile_code == _FLOW_PROFILE_PARABOLIC_RECT
    use_rect_series = flow_profile_code == _FLOW_PROFILE_RECT_SERIES
    use_near_wall = (
        hindrance_code == _HINDRANCE_NEAR_WALL and particle_radius_m > 0.0
    )
    use_tensor = (
        hindrance_code == _HINDRANCE_TENSOR and particle_radius_m > 0.0
    )
    has_hindrance = use_near_wall or use_tensor
    inv_rect_series_mean = (
        1.0 / max(rect_series_mean_raw, 1e-15) if use_rect_series else 0.0
    )
    far_gap_threshold = 5.0 * particle_radius_m

    for event_idx in prange(block_size):
        x_m[event_idx, 0] = initial_x_m[event_idx]
        z_m[event_idx, 0] = initial_z_m[event_idx]
        y_m[event_idx, 0] = y_start[event_idx]
        v_y_current = initial_v_y[event_idx]
        if store_velocity_trace:
            v_y_m_s[event_idx, 0] = v_y_current

        for sample_idx in range(n_samples - 1):
            x_curr = x_m[event_idx, sample_idx]
            z_curr = z_m[event_idx, sample_idx]
            fx = 1.0
            fz = 1.0

            if has_hindrance:
                gap_x = max(half_w - abs(x_curr), 0.0)
                gap_z = max(half_h - abs(z_curr), 0.0)
                side_parallel = _single_wall_parallel_factor_kernel(
                    gap_x,
                    particle_radius_m,
                )
                side_perp = _single_wall_perpendicular_factor_kernel(
                    gap_x,
                    particle_radius_m,
                )
                depth_parallel = _single_wall_parallel_factor_kernel(
                    gap_z,
                    particle_radius_m,
                )
                depth_perp = _single_wall_perpendicular_factor_kernel(
                    gap_z,
                    particle_radius_m,
                )
                if use_near_wall:
                    if gap_x >= far_gap_threshold:
                        side_parallel = 1.0
                        side_perp = 1.0
                    if gap_z >= far_gap_threshold:
                        depth_parallel = 1.0
                        depth_perp = 1.0
                    fx = _clip_scalar_kernel(
                        math.sqrt(side_perp * depth_parallel),
                        0.03,
                        1.0,
                    )
                    depth_bias = math.sqrt(depth_perp / max(depth_parallel, 1e-18))
                    fz = _clip_scalar_kernel(
                        math.sqrt(side_parallel * depth_perp) * depth_bias,
                        0.02,
                        1.0,
                    )
                else:
                    fx = _clip_scalar_kernel(side_perp * depth_parallel, 0.02, 1.0)
                    fz = _clip_scalar_kernel(side_parallel * depth_perp, 0.02, 1.0)

            draw_offset = 2 * sample_idx
            dx = (
                diffusion_step_scale
                * math.sqrt(fx)
                * diffusion_draws[event_idx, draw_offset]
            )
            dz = (
                diffusion_step_scale
                * math.sqrt(fz)
                * diffusion_draws[event_idx, draw_offset + 1]
            )

            x_new = x_curr + dx
            z_new = z_curr + dz

            if reflecting_boundary:
                x_new = _reflect_kernel(x_new, -half_w, half_w)
                z_new = _reflect_kernel(z_new, -half_h, half_h)

            x_m[event_idx, sample_idx + 1] = x_new
            z_m[event_idx, sample_idx + 1] = z_new
            y_m[event_idx, sample_idx + 1] = (
                y_m[event_idx, sample_idx]
                + v_y_current * dt
            )

            if use_rect_series:
                raw = _rect_series_shape_raw_scalar_kernel(
                    x_new,
                    z_new,
                    rect_series_lam_arr,
                    rect_series_cosh_den_arr,
                    rect_series_inv_n3_arr,
                )
                base_velocity = mean_flow_velocity * raw * inv_rect_series_mean
            elif use_parabolic_rect:
                u = _clip_scalar_kernel(x_new / half_w, -1.0, 1.0)
                v = _clip_scalar_kernel(z_new / half_h, -1.0, 1.0)
                base_velocity = mean_flow_velocity * max(
                    2.25 * (1.0 - u * u) * (1.0 - v * v),
                    0.0,
                )
            else:
                base_velocity = mean_flow_velocity

            if use_tensor:
                gap_x_new = max(half_w - abs(x_new), 0.0)
                gap_z_new = max(half_h - abs(z_new), 0.0)
                base_velocity *= (
                    _single_wall_parallel_factor_kernel(gap_x_new, particle_radius_m)
                    * _single_wall_parallel_factor_kernel(gap_z_new, particle_radius_m)
                )
            v_y_current = base_velocity
            if store_velocity_trace:
                v_y_m_s[event_idx, sample_idx + 1] = v_y_current

    return x_m, y_m, z_m, v_y_m_s


def simulate_particle_trajectory_block(
    channel: Channel,
    optical: OpticalSystem,
    sim_cfg: SimulationConfig,
    initial_x_m: np.ndarray,
    initial_z_m: np.ndarray,
    particle_radius_m: float = 0.0,
    diffusion_coefficient: float | None = None,
    rng: np.random.Generator | None = None,
    diffusion_draws: np.ndarray | None = None,
    trajectory_context: TrajectoryContext | None = None,
    export_velocity_trace: bool = True,
) -> dict:
    """
    Generate a block of event trajectories on one shared time grid.

    The returned arrays have shape ``(n_events, n_samples)`` and use event-major
    diffusion draws, matching repeated scalar event calls at the trajectory
    layer while letting the caller batch downstream optical/readout work.
    """
    if trajectory_context is None:
        trajectory_context = build_trajectory_context(
            channel,
            sim_cfg,
            particle_radius_m=particle_radius_m,
        )
    half_w = trajectory_context.half_w
    half_h = trajectory_context.half_h
    x0 = np.asarray(initial_x_m, dtype=float)
    z0 = np.asarray(initial_z_m, dtype=float)
    if x0.ndim != 1 or z0.ndim != 1 or x0.shape != z0.shape:
        raise ValueError(
            "initial_x_m and initial_z_m must be 1D arrays with matching shape"
        )
    if np.any(np.abs(x0) > half_w):
        raise ValueError("initial_x_m contains positions outside the channel width")
    if np.any(np.abs(z0) > half_h):
        raise ValueError("initial_z_m contains positions outside the channel depth")

    n_samples = trajectory_context.n_samples
    time_s = trajectory_context.time_s
    if (
        sim_cfg.flow_profile_model == "plug"
        and (
            sim_cfg.diffusion_hindrance_model != "anisotropic_tensor_surrogate"
            or particle_radius_m <= 0.0
        )
    ):
        initial_v_y = np.full(x0.shape, sim_cfg.mean_flow_velocity_m_s, dtype=float)
    else:
        initial_v_y = np.asarray(
            axial_transport_velocity_m_s(
                x0,
                z0,
                channel,
                sim_cfg,
                particle_radius_m=particle_radius_m,
            ),
            dtype=float,
        )
    y_start = float(optical.focus_y_m) - initial_v_y * float(sim_cfg.total_time_s) / 2.0

    if sim_cfg.include_diffusion:
        if diffusion_coefficient is None or diffusion_coefficient <= 0:
            raise ValueError(
                "diffusion_coefficient must be positive when include_diffusion=True, "
                f"got {diffusion_coefficient}"
            )
        if rng is None:
            rng = np.random.default_rng()
        diffusion_step_scale = math.sqrt(
            2.0 * float(diffusion_coefficient) * trajectory_context.dt_s
        )
        if diffusion_draws is None:
            diffusion_draw_arr = np.asarray(
                rng.standard_normal((x0.size, 2 * max(n_samples - 1, 0))),
                dtype=float,
            )
        else:
            diffusion_draw_arr = np.asarray(diffusion_draws)
            if not np.issubdtype(diffusion_draw_arr.dtype, np.floating):
                diffusion_draw_arr = diffusion_draw_arr.astype(float)
            expected_shape = (x0.size, 2 * max(n_samples - 1, 0))
            if diffusion_draw_arr.shape != expected_shape:
                raise ValueError(
                    "diffusion_draws must have shape "
                    f"{expected_shape}, got {diffusion_draw_arr.shape}"
                )
        if (
            sim_cfg.flow_profile_model == "plug"
            and sim_cfg.diffusion_hindrance_model == "none"
        ):
            x_m, y_m, z_m, v_y_m_s = _simulate_plug_diffusive_trajectory_block_kernel(
                n_samples,
                trajectory_context.dt_s,
                x0,
                z0,
                y_start,
                initial_v_y,
                half_w,
                half_h,
                diffusion_step_scale,
                diffusion_draw_arr,
                bool(sim_cfg.reflecting_boundary),
                bool(export_velocity_trace),
            )
        else:
            if sim_cfg.flow_profile_model == "plug":
                flow_profile_code = _FLOW_PROFILE_PLUG
            elif sim_cfg.flow_profile_model == "parabolic_rect":
                flow_profile_code = _FLOW_PROFILE_PARABOLIC_RECT
            else:
                flow_profile_code = _FLOW_PROFILE_RECT_SERIES

            if sim_cfg.diffusion_hindrance_model == "none":
                hindrance_code = _HINDRANCE_NONE
            elif sim_cfg.diffusion_hindrance_model == "near_wall_surrogate":
                hindrance_code = _HINDRANCE_NEAR_WALL
            else:
                hindrance_code = _HINDRANCE_TENSOR

            x_m, y_m, z_m, v_y_m_s = _simulate_diffusive_trajectory_block_kernel(
                n_samples,
                trajectory_context.dt_s,
                x0,
                z0,
                y_start,
                initial_v_y,
                half_w,
                half_h,
                particle_radius_m,
                diffusion_step_scale,
                diffusion_draw_arr,
                float(sim_cfg.mean_flow_velocity_m_s),
                bool(sim_cfg.reflecting_boundary),
                flow_profile_code,
                hindrance_code,
                (
                    0.0
                    if trajectory_context.rect_series_mean_raw is None
                    else float(trajectory_context.rect_series_mean_raw)
                ),
                (
                    _EMPTY_FLOAT_ARRAY
                    if trajectory_context.rect_series_lam_arr is None
                    else trajectory_context.rect_series_lam_arr
                ),
                (
                    _EMPTY_FLOAT_ARRAY
                    if trajectory_context.rect_series_cosh_den_arr is None
                    else trajectory_context.rect_series_cosh_den_arr
                ),
                (
                    _EMPTY_FLOAT_ARRAY
                    if trajectory_context.rect_series_inv_n3_arr is None
                    else trajectory_context.rect_series_inv_n3_arr
                ),
                bool(export_velocity_trace),
            )
    else:
        x_m = np.broadcast_to(x0[:, np.newaxis], (x0.size, n_samples)).copy()
        z_m = np.broadcast_to(z0[:, np.newaxis], (z0.size, n_samples)).copy()
        y_m = y_start[:, np.newaxis] + initial_v_y[:, np.newaxis] * time_s[np.newaxis, :]
        v_y_m_s = (
            np.broadcast_to(
                initial_v_y[:, np.newaxis],
                (x0.size, n_samples),
            ).copy()
            if export_velocity_trace
            else np.empty((x0.size, 0), dtype=float)
        )

    result = {
        "time_s": time_s,
        "x_m": x_m,
        "y_m": y_m,
        "z_m": z_m,
    }
    if export_velocity_trace:
        result["v_y_m_s"] = v_y_m_s
    return result
