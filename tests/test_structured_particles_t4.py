from __future__ import annotations

from nodi_simulator.structured_particles import build_biomimetic_exosome_core_shell


def test_t4_surface_layer_metadata_separates_nominal_and_resolved_when_clipped() -> None:
    spec = build_biomimetic_exosome_core_shell(
        20e-9,
        1.33,
        preset_name="surface_loaded_bright_2021",
        overrides={
            "corona_thickness_m": 8e-9,
            "corona_n_real": 1.40,
            "edl_refractive_increment": 0.005,
        },
    )

    assert spec["corona_thickness_nominal_m"] == 8e-9
    assert spec["surface_layer_clipped_flag"] is True
    assert spec["surface_layer_scale_factor"] < 1.0
    assert spec["corona_thickness_resolved_m"] < spec["corona_thickness_nominal_m"]
    assert spec["membrane_thickness_resolved_m"] < spec["membrane_thickness_nominal_m"]
    assert spec["edl_thickness_resolved_m"] < spec["edl_thickness_nominal_m"]
    assert spec["core_radius_fraction_resolved"] > 0.0
