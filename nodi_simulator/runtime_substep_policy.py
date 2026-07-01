"""Runtime/substep guards for trapezoid finite-step reflection trajectories."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any

import numpy as np

from .cross_section_geometry import TrapezoidCrossSection
from .data_objects import Channel, SimulationConfig


TRAPEZOID_RUNTIME_SUBSTEP_POLICY_VERSION = "trapezoid_runtime_substep_guard_v1"
TRAPEZOID_RUNTIME_SUBSTEP_TRIGGER_METRIC = (
    "brownian_rms_step_over_surface_gap_quantile"
)
DEFAULT_TRIGGER_THRESHOLD = 1.0
DEFAULT_SURFACE_GAP_QUANTILE = 0.05
DEFAULT_LOW_COST_MAX_SUBSTEPS = 16
DEFAULT_REVIEW_MAX_SUBSTEPS = 128


@dataclass(frozen=True)
class TrapezoidRuntimeSubstepDecision:
    """Machine-readable runtime/substep preflight decision."""

    policy_version: str
    trigger_metric: str
    channel_cross_section_model: str
    runtime_policy_status: str
    runtime_policy_class: str
    runtime_allowed: bool
    execution_packet_required: bool
    sidewall_prs_eas_numeric_allowed: bool
    diffusion_coefficient_m2_s: float
    dt_s: float
    particle_radius_m: float
    surface_gap_quantile: float
    surface_gap_quantile_m: float
    brownian_rms_step_m: float
    observed_trigger_value: float
    trigger_threshold: float
    required_substeps_to_meet_threshold: int | float
    required_dt_s_to_meet_threshold: float
    projected_trigger_value_after_required_substeps: float
    manual_runtime_cost_waiver: bool
    guard_reason: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def required_substeps_for_brownian_surface_gap(
    *,
    diffusion_coefficient_m2_s: float,
    dt_s: float,
    surface_gap_m: float,
    trigger_threshold: float = DEFAULT_TRIGGER_THRESHOLD,
) -> tuple[int | float, float, float, float]:
    """Return required substeps so Brownian RMS step / surface gap <= threshold."""
    diffusion = float(diffusion_coefficient_m2_s)
    dt = float(dt_s)
    gap = float(surface_gap_m)
    threshold = float(trigger_threshold)
    if diffusion < 0.0:
        raise ValueError("diffusion_coefficient_m2_s must be non-negative")
    if dt <= 0.0:
        raise ValueError("dt_s must be positive")
    if gap <= 0.0:
        return math.inf, math.inf, math.inf, math.inf  # type: ignore[return-value]
    if threshold <= 0.0:
        raise ValueError("trigger_threshold must be positive")
    rms_step_m = math.sqrt(2.0 * diffusion * dt)
    observed_trigger = rms_step_m / gap
    required = max(1, int(math.ceil((observed_trigger / threshold) ** 2)))
    required_dt = dt / required
    projected = observed_trigger / math.sqrt(required)
    return required, required_dt, projected, observed_trigger


def estimate_trapezoid_surface_gap_quantile_m(
    geometry: TrapezoidCrossSection,
    *,
    particle_radius_m: float,
    quantile: float = DEFAULT_SURFACE_GAP_QUANTILE,
    u_bins: int = 64,
    x_bins: int = 64,
) -> float:
    """Estimate a low quantile of particle surface gap over center-accessible support."""
    radius = float(particle_radius_m)
    q = float(quantile)
    if not (0.0 < q < 1.0):
        raise ValueError("quantile must be in (0, 1)")
    if u_bins <= 0 or x_bins <= 0:
        raise ValueError("u_bins and x_bins must be positive")
    bounds = geometry.center_accessible_u_bounds_m(radius)
    if bounds is None:
        return 0.0
    u_low, u_high = bounds
    u_values = np.linspace(u_low, u_high, int(u_bins), dtype=float)
    gaps: list[float] = []
    for u in u_values:
        x_left, x_right = geometry.center_accessible_x_bounds_at_depth_m(u, radius)
        if x_right <= x_left:
            continue
        x_values = np.linspace(x_left, x_right, int(x_bins), dtype=float)
        for x in x_values:
            diagnostics = geometry.particle_wall_gap_diagnostics_m(x, u, radius)
            gaps.append(float(diagnostics["surface_gap_for_particle_m"]))
    if not gaps:
        return 0.0
    return float(np.quantile(np.asarray(gaps, dtype=float), q))


def _trapezoid_geometry(channel: Channel, sim_cfg: SimulationConfig) -> TrapezoidCrossSection:
    return TrapezoidCrossSection(
        top_width_m=float(channel.width_m),
        depth_m=float(channel.depth_m),
        sidewall_taper_angle_deg=float(sim_cfg.sidewall_taper_angle_deg),
    )


def _is_trapezoid_active(sim_cfg: SimulationConfig) -> bool:
    return (
        str(getattr(sim_cfg, "channel_cross_section_model", "ideal_rectangle"))
        == "trapezoid_tapered_sidewalls"
    )


def build_trapezoid_runtime_substep_decision(
    *,
    channel: Channel,
    sim_cfg: SimulationConfig,
    particle_radius_m: float,
    diffusion_coefficient_m2_s: float | None = None,
    dt_s: float | None = None,
    surface_gap_quantile_m: float | None = None,
    surface_gap_quantile: float = DEFAULT_SURFACE_GAP_QUANTILE,
    trigger_threshold: float = DEFAULT_TRIGGER_THRESHOLD,
    low_cost_max_substeps: int = DEFAULT_LOW_COST_MAX_SUBSTEPS,
    review_max_substeps: int = DEFAULT_REVIEW_MAX_SUBSTEPS,
    manual_runtime_cost_waiver: bool = False,
) -> TrapezoidRuntimeSubstepDecision:
    """Build a fail-closed trapezoid runtime/substep preflight decision."""
    dt = float(sim_cfg.dt_s if dt_s is None else dt_s)
    diffusion = float(
        sim_cfg.diffusion_coefficient_m2_s
        if diffusion_coefficient_m2_s is None
        else diffusion_coefficient_m2_s
    )
    radius = float(particle_radius_m)
    if radius < 0.0:
        raise ValueError("particle_radius_m must be non-negative")
    if not _is_trapezoid_active(sim_cfg):
        return _decision(
            sim_cfg=sim_cfg,
            status="not_applicable_rectangle_path",
            policy_class="not_applicable",
            runtime_allowed=True,
            execution_packet_required=False,
            diffusion=diffusion,
            dt=dt,
            radius=radius,
            surface_gap_quantile=surface_gap_quantile,
            surface_gap_m=math.inf,
            threshold=trigger_threshold,
            required_substeps=1,
            required_dt=dt,
            projected=0.0,
            observed=0.0,
            manual_runtime_cost_waiver=manual_runtime_cost_waiver,
            reason="ideal_rectangle_or_non_trapezoid_path_uses_existing_runtime_policy",
        )
    if not bool(sim_cfg.include_diffusion) or diffusion <= 0.0:
        return _decision(
            sim_cfg=sim_cfg,
            status="not_required_no_diffusion",
            policy_class="no_substep_required",
            runtime_allowed=True,
            execution_packet_required=False,
            diffusion=diffusion,
            dt=dt,
            radius=radius,
            surface_gap_quantile=surface_gap_quantile,
            surface_gap_m=math.inf,
            threshold=trigger_threshold,
            required_substeps=1,
            required_dt=dt,
            projected=0.0,
            observed=0.0,
            manual_runtime_cost_waiver=manual_runtime_cost_waiver,
            reason="diffusion_disabled_or_zero_diffusion",
        )

    geometry = _trapezoid_geometry(channel, sim_cfg)
    if geometry.closure_status == "geometry_closed":
        return _decision(
            sim_cfg=sim_cfg,
            status="blocked_geometry_closed",
            policy_class="blocked_geometry",
            runtime_allowed=False,
            execution_packet_required=True,
            diffusion=diffusion,
            dt=dt,
            radius=radius,
            surface_gap_quantile=surface_gap_quantile,
            surface_gap_m=0.0,
            threshold=trigger_threshold,
            required_substeps=math.inf,
            required_dt=0.0,
            projected=math.inf,
            observed=math.inf,
            manual_runtime_cost_waiver=manual_runtime_cost_waiver,
            reason="geometry_closed_trapezoid_cannot_enter_runtime",
        )

    gap_m = (
        float(surface_gap_quantile_m)
        if surface_gap_quantile_m is not None
        else estimate_trapezoid_surface_gap_quantile_m(
            geometry,
            particle_radius_m=radius,
            quantile=surface_gap_quantile,
        )
    )
    required_substeps, required_dt, projected, observed = (
        required_substeps_for_brownian_surface_gap(
            diffusion_coefficient_m2_s=diffusion,
            dt_s=dt,
            surface_gap_m=gap_m,
            trigger_threshold=trigger_threshold,
        )
    )
    if not math.isfinite(float(required_substeps)):
        return _decision(
            sim_cfg=sim_cfg,
            status="blocked_zero_or_negative_surface_gap",
            policy_class="blocked_geometry",
            runtime_allowed=False,
            execution_packet_required=True,
            diffusion=diffusion,
            dt=dt,
            radius=radius,
            surface_gap_quantile=surface_gap_quantile,
            surface_gap_m=gap_m,
            threshold=trigger_threshold,
            required_substeps=required_substeps,
            required_dt=0.0,
            projected=math.inf,
            observed=math.inf,
            manual_runtime_cost_waiver=manual_runtime_cost_waiver,
            reason="surface_gap_quantile_nonpositive",
        )

    required_int = int(required_substeps)
    if required_int <= 1:
        status = "runtime_allowed_no_substep_required"
        policy_class = "no_substep_required"
        allowed = True
        execution_packet = False
        reason = "brownian_rms_step_within_surface_gap_threshold"
    elif required_int <= int(low_cost_max_substeps):
        status = "runtime_allowed_with_low_cost_substeps"
        policy_class = "low_substep_cost_runtime_guard"
        allowed = True
        execution_packet = True
        reason = "low_cost_substep_guard_required_before_runtime_output"
    elif required_int <= int(review_max_substeps):
        status = "manual_review_required_before_runtime"
        policy_class = "moderate_or_high_substep_cost_review"
        allowed = False
        execution_packet = True
        reason = "manual_runtime_review_required_for_substep_cost"
    elif manual_runtime_cost_waiver:
        status = "manual_waiver_recorded_execution_packet_required"
        policy_class = "prohibitive_substep_cost_manual_waiver"
        allowed = False
        execution_packet = True
        reason = "manual_waiver_records_path_but_execution_packet_still_required"
    else:
        status = "blocked_prohibitive_substep_cost"
        policy_class = "prohibitive_substep_cost_runtime_blocked"
        allowed = False
        execution_packet = True
        reason = "required_substeps_exceed_review_max"

    return _decision(
        sim_cfg=sim_cfg,
        status=status,
        policy_class=policy_class,
        runtime_allowed=allowed,
        execution_packet_required=execution_packet,
        diffusion=diffusion,
        dt=dt,
        radius=radius,
        surface_gap_quantile=surface_gap_quantile,
        surface_gap_m=gap_m,
        threshold=trigger_threshold,
        required_substeps=required_int,
        required_dt=required_dt,
        projected=projected,
        observed=observed,
        manual_runtime_cost_waiver=manual_runtime_cost_waiver,
        reason=reason,
    )


def _decision(
    *,
    sim_cfg: SimulationConfig,
    status: str,
    policy_class: str,
    runtime_allowed: bool,
    execution_packet_required: bool,
    diffusion: float,
    dt: float,
    radius: float,
    surface_gap_quantile: float,
    surface_gap_m: float,
    threshold: float,
    required_substeps: int | float,
    required_dt: float,
    projected: float,
    observed: float,
    manual_runtime_cost_waiver: bool,
    reason: str,
) -> TrapezoidRuntimeSubstepDecision:
    rms_step_m = math.sqrt(2.0 * max(float(diffusion), 0.0) * float(dt))
    return TrapezoidRuntimeSubstepDecision(
        policy_version=TRAPEZOID_RUNTIME_SUBSTEP_POLICY_VERSION,
        trigger_metric=TRAPEZOID_RUNTIME_SUBSTEP_TRIGGER_METRIC,
        channel_cross_section_model=str(sim_cfg.channel_cross_section_model),
        runtime_policy_status=status,
        runtime_policy_class=policy_class,
        runtime_allowed=bool(runtime_allowed),
        execution_packet_required=bool(execution_packet_required),
        sidewall_prs_eas_numeric_allowed=False,
        diffusion_coefficient_m2_s=float(diffusion),
        dt_s=float(dt),
        particle_radius_m=float(radius),
        surface_gap_quantile=float(surface_gap_quantile),
        surface_gap_quantile_m=float(surface_gap_m),
        brownian_rms_step_m=float(rms_step_m),
        observed_trigger_value=float(observed),
        trigger_threshold=float(threshold),
        required_substeps_to_meet_threshold=required_substeps,
        required_dt_s_to_meet_threshold=float(required_dt),
        projected_trigger_value_after_required_substeps=float(projected),
        manual_runtime_cost_waiver=bool(manual_runtime_cost_waiver),
        guard_reason=reason,
        claim_boundary=(
            "runtime_substep_guard_preflight_not_prs_eas_numeric_not_solver_wet"
        ),
    )
