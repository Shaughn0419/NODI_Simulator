from __future__ import annotations

import math

from nodi_simulator.sidewall_reference_surrogate_smoke import (
    SIDEWALL_REFERENCE_SURROGATE_SMOKE_CLAIM_BOUNDARY,
    run_sidewall_reference_surrogate_smoke,
)


def test_reference_surrogate_smoke_runs_legacy_and_sidewall_reference_models() -> None:
    rows = run_sidewall_reference_surrogate_smoke(n_events=4, random_seed=528)

    assert len(rows) == 8
    assert {row.case_id for row in rows} == {
        "rectangle_limit_theta90_D900_W500",
        "taper_theta85_D900_W500",
    }
    assert {row.reference_model for row in rows} == {
        "channel_angular_surrogate",
        "trapezoid_effective_aperture_surrogate",
    }
    assert {row.wavelength_nm for row in rows} == {404, 660}
    for row in rows:
        assert row.n_events == 4
        assert row.width_nm == 500
        assert row.depth_nm == 900
        assert 0.0 <= row.detection_rate <= 1.0
        assert 0.0 <= row.stable_detection_rate <= 1.0
        assert row.not_optical_solver_output is True
        assert row.optical_solver_current is False
        assert row.true_W_eff_current is False
        assert row.detection_probability_current is False
        assert row.yield_current is False
        assert row.route_score_current is False
        assert row.claim_boundary == SIDEWALL_REFERENCE_SURROGATE_SMOKE_CLAIM_BOUNDARY


def test_reference_surrogate_smoke_propagates_trapezoid_geometry_in_nodi_run() -> None:
    rows = run_sidewall_reference_surrogate_smoke(n_events=4, random_seed=529)
    by_key = {
        (row.case_id, row.reference_model, row.wavelength_nm): row for row in rows
    }

    legacy_trapezoid_404 = by_key[
        ("taper_theta85_D900_W500", "channel_angular_surrogate", 404)
    ]
    sidewall_trapezoid_404 = by_key[
        (
            "taper_theta85_D900_W500",
            "trapezoid_effective_aperture_surrogate",
            404,
        )
    ]
    rectangle_sidewall_404 = by_key[
        (
            "rectangle_limit_theta90_D900_W500",
            "trapezoid_effective_aperture_surrogate",
            404,
        )
    ]

    assert legacy_trapezoid_404.geometry_not_propagated_to_reference_field is True
    assert legacy_trapezoid_404.reference_geometry_propagation_status == (
        "blocked_trapezoid_geometry_not_propagated_to_reference_field"
    )
    assert math.isnan(legacy_trapezoid_404.trapezoid_effective_aperture_factor)

    assert sidewall_trapezoid_404.geometry_not_propagated_to_reference_field is False
    assert sidewall_trapezoid_404.reference_geometry_propagation_status == (
        "trapezoid_geometry_propagated_to_effective_aperture_reference_surrogate"
    )
    assert sidewall_trapezoid_404.reference_solver_status == (
        "trapezoid_effective_aperture_surrogate_active"
    )
    assert 0.0 < sidewall_trapezoid_404.trapezoid_effective_aperture_factor < 1.0
    assert sidewall_trapezoid_404.A_ref < rectangle_sidewall_404.A_ref
    assert sidewall_trapezoid_404.na_cutoff_active is False


def test_reference_surrogate_smoke_records_660_nm_na_cutoff_context() -> None:
    rows = run_sidewall_reference_surrogate_smoke(n_events=4, random_seed=530)
    sidewall_660 = [
        row
        for row in rows
        if row.reference_model == "trapezoid_effective_aperture_surrogate"
        and row.wavelength_nm == 660
    ]

    assert len(sidewall_660) == 2
    for row in sidewall_660:
        assert row.na_cutoff_condition_met is True
        assert row.na_cutoff_active is True
        assert row.A_ref == 0.0
        assert row.not_optical_solver_output is True
