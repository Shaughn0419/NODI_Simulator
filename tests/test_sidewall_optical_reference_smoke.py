from __future__ import annotations

from nodi_simulator.sidewall_optical_reference_smoke import (
    SIDEWALL_OPTICAL_REFERENCE_SMOKE_CLAIM_BOUNDARY,
    run_sidewall_optical_reference_smoke,
)


def test_sidewall_optical_reference_smoke_runs_rectangle_and_trapezoid() -> None:
    rows = run_sidewall_optical_reference_smoke(n_events=4, random_seed=526)

    assert {row.case_id for row in rows} == {
        "rectangle_limit_theta90_D900_W500",
        "taper_theta85_D900_W500",
    }
    for row in rows:
        assert row.width_nm == 500
        assert row.depth_nm == 900
        assert row.wavelength_nm == 660
        assert row.n_events == 4
        assert 0.0 <= row.detection_rate <= 1.0
        assert 0.0 <= row.stable_detection_rate <= 1.0
        assert row.not_optical_solver_output is True
        assert row.optical_solver_trigger_is_result is False
        assert row.optical_solver_current is False
        assert row.detection_probability_current is False
        assert row.yield_current is False
        assert row.route_score_current is False
        assert row.claim_boundary == SIDEWALL_OPTICAL_REFERENCE_SMOKE_CLAIM_BOUNDARY


def test_trapezoid_smoke_records_reference_geometry_not_propagated() -> None:
    rows = run_sidewall_optical_reference_smoke(n_events=4, random_seed=527)
    by_case = {row.case_id: row for row in rows}

    rectangle = by_case["rectangle_limit_theta90_D900_W500"]
    trapezoid = by_case["taper_theta85_D900_W500"]

    assert rectangle.channel_cross_section_model == "ideal_rectangle"
    assert rectangle.geometry_not_propagated_to_reference_field is False
    assert rectangle.reference_geometry_propagation_status == (
        "rectangle_native_or_non_sidewall_geometry"
    )

    assert trapezoid.channel_cross_section_model == "trapezoid_tapered_sidewalls"
    assert trapezoid.sidewall_deg_comsol == 85.0
    assert trapezoid.geometry_not_propagated_to_reference_field is True
    assert trapezoid.reference_geometry_propagation_status == (
        "blocked_trapezoid_geometry_not_propagated_to_reference_field"
    )
    assert trapezoid.reference_geometry_claim_level == (
        "proxy_not_sidewall_aware_not_optical_solver_output"
    )
