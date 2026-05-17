from __future__ import annotations

import pandas as pd

from tools import lens_b_tau1ms_targeted_ev_probe as probe


def _source_frame() -> pd.DataFrame:
    route_rows = [
        {
            "wavelength_nm": route.wavelength_nm,
            "width_nm": route.width_nm,
            "depth_nm": route.depth_nm,
            "particle_name": "exosome_biomimetic_corona_nominal_100nm",
            "particle_material": "exosome",
            "particle_family": "ev",
        }
        for route in probe.default_route_panel()[0]
    ]
    particle_rows = [
        {
            "wavelength_nm": 660,
            "width_nm": 800,
            "depth_nm": 800,
            "particle_name": name,
            "particle_material": "gold",
            "particle_family": "anchor",
        }
        for name in probe.GOLD_ANCHOR_NAMES
    ]
    return pd.DataFrame(route_rows + particle_rows)


def test_default_route_panel_uses_existing_substitution_for_532_control() -> None:
    routes, substitutions = probe.default_route_panel()

    assert (532, 700, 700) in [route.key for route in routes]
    assert all(route.key != (532, 700, 750) for route in routes)
    assert substitutions == [
        {
            "requested_route": [532, 700, 750],
            "used_route": [532, 700, 700],
            "reason": "route source has no 750 nm depth rows at 532 nm; nearest top-control grid row retained",
        }
    ]


def test_probe_scope_keeps_ev_rows_and_optional_gold_anchors_separate() -> None:
    scope = probe.build_probe_scope(_source_frame(), include_gold_anchors=True)

    assert scope.ev_particle_names == ["exosome_biomimetic_corona_nominal_100nm"]
    assert scope.gold_anchor_names == list(probe.GOLD_ANCHOR_NAMES)
    assert scope.route_particle_rows_per_seed == len(scope.routes) * 5
