from __future__ import annotations

from dataclasses import replace
import math

import pytest

from nodi_simulator.channel_geometry_model import build_channel_geometry_diagnostics
from nodi_simulator.cross_section_geometry import (
    CENTER_ACCESSIBLE_SUPPORT_MODEL,
    TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION,
    TrapezoidCrossSection,
    comsol_sidewall_deg_to_nodi_taper_deg,
    nodi_taper_deg_to_comsol_sidewall_deg,
)
from nodi_simulator.data_objects import (
    BASELINE_OPTICAL,
    DEFAULT_SIM_CFG,
    Channel,
    Particle,
)


def test_comsol_85_deg_converts_to_nodi_taper_5_deg() -> None:
    assert comsol_sidewall_deg_to_nodi_taper_deg(85.0) == pytest.approx(5.0)
    assert nodi_taper_deg_to_comsol_sidewall_deg(5.0) == pytest.approx(85.0)


def test_trapezoid_formula_examples_preserve_unclipped_bottom_width() -> None:
    geom_85 = TrapezoidCrossSection(
        top_width_m=500.0e-9,
        depth_m=900.0e-9,
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
    )
    geom_70 = TrapezoidCrossSection(
        top_width_m=500.0e-9,
        depth_m=600.0e-9,
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(70.0),
    )

    assert geom_85.bottom_width_unclipped_m * 1.0e9 == pytest.approx(342.52, abs=0.02)
    assert geom_70.bottom_width_unclipped_m * 1.0e9 == pytest.approx(63.24, abs=0.02)
    assert geom_85.bottom_width_runtime_clipped_m == pytest.approx(
        geom_85.bottom_width_unclipped_m
    )
    assert geom_70.closure_status == "near_closed"


def test_negative_bottom_width_is_preserved_in_descriptor_space() -> None:
    geom = TrapezoidCrossSection(
        top_width_m=500.0e-9,
        depth_m=700.0e-9,
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(70.0),
    )

    assert geom.bottom_width_unclipped_m < 0.0
    assert geom.bottom_width_runtime_clipped_m == 0.0
    assert geom.closure_status == "geometry_closed"


def test_particle_center_support_uses_wall_normal_sidewall_offset() -> None:
    geom = TrapezoidCrossSection(
        top_width_m=500.0e-9,
        depth_m=900.0e-9,
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(85.0),
    )
    radius_m = 110.0e-9
    u_m = 200.0e-9
    local_half_width_m = geom.half_width_at_depth_m(u_m)
    x_limit_m = local_half_width_m - radius_m * math.sqrt(1.0 + geom.k_taper**2)

    assert geom.contains_particle_center(x_limit_m - 1.0e-12, u_m, radius_m)
    assert not geom.contains_particle_center(x_limit_m + 1.0e-10, u_m, radius_m)


def test_center_accessible_width_blocks_too_deep_tail_particle_slice() -> None:
    geom = TrapezoidCrossSection(
        top_width_m=500.0e-9,
        depth_m=900.0e-9,
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(70.0),
    )

    assert geom.center_accessible_width_at_depth_m(600.0e-9, 110.0e-9) == 0.0


def test_channel_diagnostics_emit_unclipped_and_runtime_clipped_bottom_widths() -> None:
    cfg = replace(
        DEFAULT_SIM_CFG,
        channel_cross_section_model="trapezoid_tapered_sidewalls",
        sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(70.0),
    )
    diagnostics = build_channel_geometry_diagnostics(
        Particle("ev_220nm_tail", radius_m=110.0e-9, n_real=1.37),
        Channel(width_m=500.0e-9, depth_m=700.0e-9),
        BASELINE_OPTICAL,
        cfg,
    )

    assert diagnostics["trapezoid_bottom_width_unclipped_m"] < 0.0
    assert diagnostics["trapezoid_bottom_width_runtime_clipped_m"] == 0.0
    assert diagnostics["trapezoid_bottom_width_m"] == 0.0
    assert diagnostics["trapezoid_closure_status"] == "geometry_closed"
    assert diagnostics["trapezoid_closure_policy"] == "preserve_unclipped_descriptor"
    assert diagnostics["trapezoid_runtime_guard_status"] == "validation_guard"
    assert diagnostics["center_accessible_support_model"] == CENTER_ACCESSIBLE_SUPPORT_MODEL
    assert (
        diagnostics["cross_section_geometry_version"]
        == TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION
    )
    assert diagnostics["effective_accessible_area_m2"] == diagnostics[
        "trapezoid_center_accessible_area_m2"
    ]
    assert diagnostics["effective_accessible_area_m2"] > 0.0
