"""Package-local fluidic network diagnostics beyond the nanochannel proxy."""

from __future__ import annotations

import math
from typing import Any

from .data_objects import Channel, Medium, SimulationConfig
from .fluidic_resistance import compute_rectangular_channel_hydraulic_resistance
from .type_coerce import blocker_summary as _blocker_summary


FLUIDIC_NETWORK_DIAGNOSTIC_FIELDS = (
    "fluidic_network_schema",
    "fluidic_network_model_status",
    "fluidic_network_claim_level",
    "fluidic_network_component_table",
    "fluidic_network_component_count",
    "fluidic_network_known_component_ids",
    "fluidic_network_missing_component_inputs",
    "fluidic_parallel_channel_count",
    "fluidic_network_per_channel_flow_rate_m3_s",
    "fluidic_network_total_flow_rate_m3_s",
    "fluidic_network_nanochannel_array_resistance_Pa_s_m3",
    "fluidic_network_known_series_resistance_Pa_s_m3",
    "fluidic_network_known_pressure_drop_for_target_velocity_Pa",
    "fluidic_network_nanochannel_resistance_fraction",
    "fluidic_network_external_geometry_status",
    "fluidic_network_pressure_flow_relation_status",
    "fluidic_network_geometry_model",
    "fluidic_network_hydraulic_resistance_model",
    "fluidic_network_hydraulic_resistance_claim_level",
    "fluidic_network_geometry_propagation_status",
    "geometry_not_propagated_to_fluidic_network",
    "fluidic_network_not_qch_weighted",
    "fluidic_network_measured_flow_available",
    "fluidic_network_fixed_pressure_prediction_allowed",
    "fluidic_network_gate_passed",
    "fluidic_network_blocker_summary",
)

_TSUYAMA_REFERENCE_MICROCHANNEL_WIDTH_M = 500.0e-6
_TSUYAMA_REFERENCE_MICROCHANNEL_DEPTH_M = 5.0e-6
_TSUYAMA_REFERENCE_CAPILLARY_INNER_DIAMETER_M = 260.0e-6


def _positive_float(value: Any, default: float | None = None) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(numeric) or numeric <= 0.0:
        return default
    return numeric


def _positive_int(value: Any, default: int = 1) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return default
    return numeric if numeric > 0 else default


def _circular_tube_hydraulic_resistance(
    inner_diameter_m: float,
    length_m: float,
    viscosity_Pa_s: float,
) -> float:
    diameter = _positive_float(inner_diameter_m)
    length = _positive_float(length_m)
    viscosity = _positive_float(viscosity_Pa_s)
    if diameter is None or length is None or viscosity is None:
        raise ValueError("inner_diameter, length, and viscosity must be positive")
    radius = 0.5 * diameter
    return float(8.0 * viscosity * length / (math.pi * radius**4))


def _component(
    *,
    component_id: str,
    role: str,
    status: str,
    hydraulic_resistance_Pa_s_m3: float | None,
    source: str,
    geometry: dict[str, float | int | None],
) -> dict[str, object]:
    return {
        "component_id": component_id,
        "role": role,
        "status": status,
        "hydraulic_resistance_Pa_s_m3": hydraulic_resistance_Pa_s_m3,
        "source": source,
        "geometry": geometry,
    }


def build_fluidic_network_diagnostics(
    medium: Medium,
    channel: Channel,
    sim_cfg: SimulationConfig,
) -> dict[str, object]:
    """Build P1 fluidic-network metadata without claiming measured flow physics."""
    sidewall_active = (
        str(getattr(sim_cfg, "channel_cross_section_model", "ideal_rectangle"))
        == "trapezoid_tapered_sidewalls"
    )
    viscosity = float(medium.viscosity_Pa_s or 1.0e-3)
    channel_area = float(channel.width_m * channel.depth_m)
    parallel_count = _positive_int(
        getattr(sim_cfg, "fluidic_parallel_channel_count", 1),
        default=1,
    )
    per_channel_flow_rate = float(sim_cfg.mean_flow_velocity_m_s * channel_area)
    total_flow_rate = float(per_channel_flow_rate * parallel_count)
    single_nanochannel_resistance = compute_rectangular_channel_hydraulic_resistance(
        channel.width_m,
        channel.depth_m,
        sim_cfg.fluidic_channel_length_m,
        viscosity,
    )
    nanochannel_array_resistance = float(
        single_nanochannel_resistance / parallel_count
    )

    components: list[dict[str, object]] = [
        _component(
            component_id="nanochannel_parallel_array",
            role="parallel_nanochannel_detection_network",
            status="computed_from_channel_geometry",
            hydraulic_resistance_Pa_s_m3=nanochannel_array_resistance,
            source="channel_width_depth_length_and_parallel_count",
            geometry={
                "single_channel_width_m": float(channel.width_m),
                "single_channel_depth_m": float(channel.depth_m),
                "single_channel_length_m": float(sim_cfg.fluidic_channel_length_m),
                "parallel_channel_count": parallel_count,
            },
        )
    ]

    missing_inputs: list[str] = []
    known_resistances = [nanochannel_array_resistance]
    known_component_ids = ["nanochannel_parallel_array"]

    micro_width = _positive_float(
        getattr(
            sim_cfg,
            "fluidic_microchannel_width_m",
            _TSUYAMA_REFERENCE_MICROCHANNEL_WIDTH_M,
        )
    )
    micro_depth = _positive_float(
        getattr(
            sim_cfg,
            "fluidic_microchannel_depth_m",
            _TSUYAMA_REFERENCE_MICROCHANNEL_DEPTH_M,
        )
    )
    micro_length = _positive_float(getattr(sim_cfg, "fluidic_microchannel_length_m", None))
    micro_resistance = None
    if micro_width is not None and micro_depth is not None and micro_length is not None:
        micro_resistance = compute_rectangular_channel_hydraulic_resistance(
            micro_width,
            micro_depth,
            micro_length,
            viscosity,
        )
        known_resistances.append(micro_resistance)
        known_component_ids.append("microchannel_inlet_outlet")
        micro_status = "computed_from_configured_rectangular_geometry"
    else:
        missing_inputs.append("fluidic_microchannel_length_m")
        micro_status = "geometry_incomplete_reference_width_depth_only"
    components.append(
        _component(
            component_id="microchannel_inlet_outlet",
            role="upstream_downstream_microchannel_feed",
            status=micro_status,
            hydraulic_resistance_Pa_s_m3=micro_resistance,
            source=(
                "configured_geometry"
                if micro_resistance is not None
                else "tsuyama_reported_width_depth_length_missing"
            ),
            geometry={
                "width_m": micro_width,
                "depth_m": micro_depth,
                "length_m": micro_length,
            },
        )
    )

    capillary_diameter = _positive_float(
        getattr(
            sim_cfg,
            "fluidic_capillary_inner_diameter_m",
            _TSUYAMA_REFERENCE_CAPILLARY_INNER_DIAMETER_M,
        )
    )
    capillary_length = _positive_float(
        getattr(sim_cfg, "fluidic_capillary_length_m", None)
    )
    capillary_resistance = None
    if capillary_diameter is not None and capillary_length is not None:
        capillary_resistance = _circular_tube_hydraulic_resistance(
            capillary_diameter,
            capillary_length,
            viscosity,
        )
        known_resistances.append(capillary_resistance)
        known_component_ids.append("pressure_capillary_link")
        capillary_status = "computed_from_configured_circular_tube_geometry"
    else:
        missing_inputs.append("fluidic_capillary_length_m")
        capillary_status = "geometry_incomplete_reference_inner_diameter_only"
    components.append(
        _component(
            component_id="pressure_capillary_link",
            role="pressure_controller_to_chip_connection",
            status=capillary_status,
            hydraulic_resistance_Pa_s_m3=capillary_resistance,
            source=(
                "configured_geometry"
                if capillary_resistance is not None
                else "tsuyama_reported_inner_diameter_length_missing"
            ),
            geometry={
                "inner_diameter_m": capillary_diameter,
                "length_m": capillary_length,
            },
        )
    )

    for component_id, role in (
        ("inlet_outlet_access_loss", "chip_inlet_outlet_contraction_expansion"),
        ("reservoir_or_vial_boundary", "pressure_reservoir_boundary_condition"),
    ):
        missing_inputs.append(f"{component_id}_calibration")
        components.append(
            _component(
                component_id=component_id,
                role=role,
                status="metadata_only_unmodeled_lumped_loss",
                hydraulic_resistance_Pa_s_m3=None,
                source="requires_measured_pressure_flow_or_cfd_boundary_model",
                geometry={},
            )
        )

    missing_inputs.append("measured_pressure_flow_trace")
    known_series_resistance = float(sum(known_resistances))
    pressure_drop_known = float(known_series_resistance * total_flow_rate)
    nano_fraction = float(
        nanochannel_array_resistance / max(known_series_resistance, 1.0e-30)
    )
    external_known = len(known_component_ids) > 1
    external_status = (
        "configured_external_geometry_partially_computed"
        if external_known
        else "external_network_geometry_incomplete"
    )
    model_status = (
        "partial_network_resistance_diagnostic_active"
        if external_known
        else "partial_network_nanochannel_array_only"
    )
    if sidewall_active:
        network_geometry_model = "trapezoid_descriptor_with_rectangular_proxy_network"
        network_resistance_model = (
            "rectangular_hydraulic_resistance_network_proxy_under_trapezoid"
        )
        network_resistance_claim_level = (
            "diagnostic_only_rectangular_proxy_not_trapezoid_poiseuille_not_qch"
        )
        network_geometry_status = "geometry_not_propagated_to_fluidic_network"
    else:
        network_geometry_model = "rectangular_network_resistance_proxy"
        network_resistance_model = "rectangular_hydraulic_resistance_network_proxy"
        network_resistance_claim_level = (
            "diagnostic_only_no_measured_pressure_flow_relation_not_qch_weighted"
        )
        network_geometry_status = "rectangle_native_or_non_sidewall_geometry"

    return {
        "fluidic_network_schema": "fluidic_network_diagnostic_v1",
        "fluidic_network_model_status": model_status,
        "fluidic_network_claim_level": (
            "diagnostic_only_no_measured_pressure_flow_relation"
        ),
        "fluidic_network_component_table": tuple(components),
        "fluidic_network_component_count": len(components),
        "fluidic_network_known_component_ids": tuple(known_component_ids),
        "fluidic_network_missing_component_inputs": tuple(
            dict.fromkeys(missing_inputs)
        ),
        "fluidic_parallel_channel_count": parallel_count,
        "fluidic_network_per_channel_flow_rate_m3_s": per_channel_flow_rate,
        "fluidic_network_total_flow_rate_m3_s": total_flow_rate,
        "fluidic_network_nanochannel_array_resistance_Pa_s_m3": (
            nanochannel_array_resistance
        ),
        "fluidic_network_known_series_resistance_Pa_s_m3": known_series_resistance,
        "fluidic_network_known_pressure_drop_for_target_velocity_Pa": (
            pressure_drop_known
        ),
        "fluidic_network_nanochannel_resistance_fraction": nano_fraction,
        "fluidic_network_external_geometry_status": external_status,
        "fluidic_network_pressure_flow_relation_status": (
            "blocked_until_measured_pressure_flow_trace"
        ),
        "fluidic_network_geometry_model": network_geometry_model,
        "fluidic_network_hydraulic_resistance_model": network_resistance_model,
        "fluidic_network_hydraulic_resistance_claim_level": (
            network_resistance_claim_level
        ),
        "fluidic_network_geometry_propagation_status": network_geometry_status,
        "geometry_not_propagated_to_fluidic_network": sidewall_active,
        "fluidic_network_not_qch_weighted": True,
        "fluidic_network_measured_flow_available": False,
        "fluidic_network_fixed_pressure_prediction_allowed": False,
        "fluidic_network_gate_passed": False,
        "fluidic_network_blocker_summary": _blocker_summary(
            [
                "pressure_flow_relation_not_calibrated",
                *missing_inputs,
            ],
            dedupe=True,
        ),
    }
