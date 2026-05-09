"""
Uncertainty-propagation boundary diagnostics.

The simulator currently enumerates deterministic nominal cases. This module
keeps the future uncertainty API explicit without silently propagating synthetic
or absent variance information into confidence intervals.
"""

from __future__ import annotations

from typing import Any

from .data_objects import Particle, SimulationConfig


def build_uncertainty_propagation_boundary(
    sim_cfg: SimulationConfig,
    *,
    particle: Particle | None = None,
) -> dict[str, Any]:
    """Return the current uncertainty propagation contract."""
    _ = particle
    mode = str(sim_cfg.particle_uncertainty_propagation_mode)
    budget = str(sim_cfg.particle_uncertainty_budget_model)
    configured = mode != "none" or budget != "nominal_only"
    blockers = [
        "particle_size_distribution_missing",
        "material_refractive_index_uncertainty_missing",
        "structured_particle_parameter_covariance_missing",
        "transport_and_readout_uncertainty_not_jointly_propagated",
        "output_confidence_intervals_not_computed",
    ]
    return {
        "uncertainty_propagation_schema": "uncertainty_propagation_v1",
        "uncertainty_propagation_route_configured": bool(configured),
        "uncertainty_propagation_status": (
            "configured_but_not_implemented_requires_explicit_ensemble"
            if configured
            else "nominal_only_boundary_no_uncertainty_propagated"
        ),
        "uncertainty_required_input_schema": (
            "size_distribution,RI_uncertainty,shape_or_shell_uncertainty,"
            "sample_batch_metadata,readout_noise_or_blank_summary"
        ),
        "uncertainty_propagated_outputs": "none",
        "uncertainty_route_active": False,
        "uncertainty_propagation_blocker_summary": " / ".join(blockers),
    }
