"""Electrokinetic, Debye-layer, and wall-exclusion diagnostics."""

from __future__ import annotations

import math

from .data_objects import (
    ELECTROKINETIC_MODEL_OPTIONS,
    Channel,
    SimulationConfig,
)

ELECTROKINETIC_DIAGNOSTIC_FIELDS = (
    "electrokinetic_model",
    "debye_length_nm",
    "debye_to_channel_depth_ratio",
    "debye_to_min_channel_dimension_ratio",
    "zeta_particle_mV",
    "zeta_wall_mV",
    "electrostatic_wall_exclusion_length_nm",
    "electroosmotic_flow_fraction",
    "electrostatic_confinement_flag",
    "boltzmann_wall_exclusion_status",
    "boltzmann_grid_size",
    "boltzmann_center_weight_fraction",
    "boltzmann_near_wall_weight_fraction",
    "boltzmann_center_to_near_wall_weight_ratio",
    "unweighted_mean_wall_distance_nm",
    "boltzmann_weighted_mean_wall_distance_nm",
    "electrokinetic_transport_sensitivity_lane_active",
    "surface_charge_transport_claim_level",
    "electrokinetic_diagnostic_gate_passed",
)


def _debye_length_nm(ionic_strength_M: float | None) -> float | None:
    if ionic_strength_M is None or ionic_strength_M <= 0.0:
        return None
    return 0.304 / math.sqrt(float(ionic_strength_M))


def _ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0.0:
        return None
    return float(numerator / denominator)


def _velocity_proxy(x_m: float, z_m: float, half_w_m: float, half_h_m: float) -> float:
    x_term = 1.0 - (x_m / max(half_w_m, 1e-30)) ** 2
    z_term = 1.0 - (z_m / max(half_h_m, 1e-30)) ** 2
    return max(0.0, x_term * z_term)


def _boltzmann_wall_exclusion_surrogate(
    channel: Channel,
    *,
    debye_nm: float | None,
    zeta_particle_mV: float | None,
    zeta_wall_mV: float | None,
    grid_size: int = 41,
) -> dict[str, object]:
    if debye_nm is None or zeta_particle_mV is None or zeta_wall_mV is None:
        return {
            "boltzmann_wall_exclusion_status": (
                "blocked_missing_ionic_strength_or_zeta_metadata"
            ),
            "boltzmann_grid_size": grid_size,
            "boltzmann_center_weight_fraction": None,
            "boltzmann_near_wall_weight_fraction": None,
            "boltzmann_center_to_near_wall_weight_ratio": None,
            "unweighted_mean_wall_distance_nm": None,
            "boltzmann_weighted_mean_wall_distance_nm": None,
            "electrokinetic_transport_sensitivity_lane_active": False,
        }

    half_w_m = 0.5 * float(channel.width_m)
    half_h_m = 0.5 * float(channel.depth_m)
    min_dim_nm = min(float(channel.width_m), float(channel.depth_m)) * 1e9
    near_wall_threshold_nm = max(2.0 * debye_nm, 0.1 * min_dim_nm)
    center_threshold_nm = 0.4 * min_dim_nm
    zeta_product_scale = float(zeta_particle_mV) * float(zeta_wall_mV) / 625.0

    total_weight = 0.0
    weighted_wall_distance_nm = 0.0
    unweighted_wall_distance_nm = 0.0
    cell_count = 0
    center_weight_sum = 0.0
    center_count = 0
    near_wall_weight_sum = 0.0
    near_wall_count = 0

    # Use cell centers, not boundaries, to avoid singular wall weights.
    for x_index in range(grid_size):
        x_m = -half_w_m + (x_index + 0.5) * float(channel.width_m) / grid_size
        for z_index in range(grid_size):
            z_m = -half_h_m + (z_index + 0.5) * float(channel.depth_m) / grid_size
            distances_nm = (
                (x_m + half_w_m) * 1e9,
                (half_w_m - x_m) * 1e9,
                (z_m + half_h_m) * 1e9,
                (half_h_m - z_m) * 1e9,
            )
            nearest_wall_distance_nm = max(min(distances_nm), 0.0)
            wall_potential_kbt = sum(
                zeta_product_scale * math.exp(-distance_nm / max(debye_nm, 1e-30))
                for distance_nm in distances_nm
            )
            velocity = _velocity_proxy(x_m, z_m, half_w_m, half_h_m)
            weight = velocity * math.exp(-max(min(wall_potential_kbt, 50.0), -50.0))

            total_weight += weight
            weighted_wall_distance_nm += weight * nearest_wall_distance_nm
            unweighted_wall_distance_nm += nearest_wall_distance_nm
            cell_count += 1

            if nearest_wall_distance_nm >= center_threshold_nm:
                center_weight_sum += weight
                center_count += 1
            if nearest_wall_distance_nm <= near_wall_threshold_nm:
                near_wall_weight_sum += weight
                near_wall_count += 1

    center_weight = center_weight_sum / center_count if center_count > 0 else 0.0
    near_wall_weight = (
        near_wall_weight_sum / near_wall_count if near_wall_count > 0 else 0.0
    )

    return {
        "boltzmann_wall_exclusion_status": "active_grid_surrogate",
        "boltzmann_grid_size": grid_size,
        "boltzmann_center_weight_fraction": center_weight,
        "boltzmann_near_wall_weight_fraction": near_wall_weight,
        "boltzmann_center_to_near_wall_weight_ratio": _ratio(
            center_weight,
            near_wall_weight,
        ),
        "unweighted_mean_wall_distance_nm": (
            unweighted_wall_distance_nm / cell_count if cell_count > 0 else None
        ),
        "boltzmann_weighted_mean_wall_distance_nm": (
            weighted_wall_distance_nm / total_weight if total_weight > 0.0 else None
        ),
        "electrokinetic_transport_sensitivity_lane_active": True,
    }


def _inactive_boltzmann_payload(status: str) -> dict[str, object]:
    return {
        "boltzmann_wall_exclusion_status": status,
        "boltzmann_grid_size": None,
        "boltzmann_center_weight_fraction": None,
        "boltzmann_near_wall_weight_fraction": None,
        "boltzmann_center_to_near_wall_weight_ratio": None,
        "unweighted_mean_wall_distance_nm": None,
        "boltzmann_weighted_mean_wall_distance_nm": None,
        "electrokinetic_transport_sensitivity_lane_active": False,
    }


def build_electrokinetic_transport_diagnostics(
    channel: Channel,
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """Export Debye-layer and zeta-potential metadata diagnostics."""
    model = str(getattr(sim_cfg, "electrokinetic_model", "not_applied"))
    ionic_strength_M = sim_cfg.ionic_strength_M
    debye_nm = _debye_length_nm(ionic_strength_M)
    depth_nm = float(channel.depth_m) * 1e9
    min_dim_nm = min(float(channel.width_m), float(channel.depth_m)) * 1e9
    depth_ratio = debye_nm / depth_nm if debye_nm is not None and depth_nm > 0 else None
    min_dim_ratio = (
        debye_nm / min_dim_nm if debye_nm is not None and min_dim_nm > 0 else None
    )

    if min_dim_ratio is None:
        confinement_flag = "unavailable_missing_ionic_strength"
    elif min_dim_ratio > 0.1:
        confinement_flag = "non_negligible"
    else:
        confinement_flag = "screened_or_negligible"

    zeta_particle = sim_cfg.zeta_potential_particle_mV
    zeta_wall = sim_cfg.zeta_potential_wall_mV
    exclusion_length_nm = (
        debye_nm
        if debye_nm is not None and (zeta_particle is not None or zeta_wall is not None)
        else None
    )
    eof_fraction = getattr(sim_cfg, "electroosmotic_flow_fraction", None)
    if eof_fraction is not None:
        eof_fraction = max(0.0, min(1.0, float(eof_fraction)))

    if model == "boltzmann_wall_exclusion":
        boltzmann = _boltzmann_wall_exclusion_surrogate(
            channel,
            debye_nm=debye_nm,
            zeta_particle_mV=zeta_particle,
            zeta_wall_mV=zeta_wall,
        )
    else:
        boltzmann = _inactive_boltzmann_payload("not_applied_model_not_selected")

    if debye_nm is None:
        claim_level = "metadata_missing_no_electrokinetic_claim"
    elif model == "not_applied":
        claim_level = "debye_length_diagnostic_only_transport_not_modified"
    elif model == "boltzmann_wall_exclusion" and bool(
        boltzmann["electrokinetic_transport_sensitivity_lane_active"]
    ):
        claim_level = "boltzmann_wall_exclusion_sensitivity_not_calibrated_transport"
    elif model == "boltzmann_wall_exclusion":
        claim_level = "blocked_missing_metadata_for_boltzmann_wall_exclusion"
    elif model in ELECTROKINETIC_MODEL_OPTIONS:
        claim_level = "electrokinetic_surrogate_metadata_not_validated"
    else:
        claim_level = "blocked_unknown_electrokinetic_model"

    gate_passed = bool(model in ELECTROKINETIC_MODEL_OPTIONS)
    if model == "boltzmann_wall_exclusion":
        gate_passed = bool(
            boltzmann["electrokinetic_transport_sensitivity_lane_active"]
        )

    return {
        "electrokinetic_model": model,
        "debye_length_nm": debye_nm,
        "debye_to_channel_depth_ratio": depth_ratio,
        "debye_to_min_channel_dimension_ratio": min_dim_ratio,
        "zeta_particle_mV": zeta_particle,
        "zeta_wall_mV": zeta_wall,
        "electrostatic_wall_exclusion_length_nm": exclusion_length_nm,
        "electroosmotic_flow_fraction": eof_fraction,
        "electrostatic_confinement_flag": confinement_flag,
        **boltzmann,
        "surface_charge_transport_claim_level": claim_level,
        "electrokinetic_diagnostic_gate_passed": gate_passed,
    }
