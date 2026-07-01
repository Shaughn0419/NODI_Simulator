from __future__ import annotations

from nodi_simulator.sidewall_reference_surrogate_candidate import (
    SIDEWALL_REFERENCE_SURROGATE_CLAIM_BOUNDARY,
    build_sidewall_reference_surrogate_rows,
)


def test_sidewall_reference_surrogate_rows_cover_rectangle_and_trapezoid() -> None:
    rows = build_sidewall_reference_surrogate_rows(wavelengths_nm=(404, 660))

    assert len(rows) == 4
    assert {row.case_id for row in rows} == {
        "rectangle_limit_theta90_D900_W500",
        "taper_theta85_D900_W500",
    }
    assert {row.wavelength_nm for row in rows} == {404, 660}
    for row in rows:
        assert row.reference_model == "trapezoid_effective_aperture_surrogate"
        assert row.geometry_not_propagated_to_reference_field is False
        assert row.not_optical_solver_output is True
        assert row.optical_solver_current is False
        assert row.true_W_eff_current is False
        assert row.detection_probability_current is False
        assert row.route_score_current is False
        assert row.claim_boundary == SIDEWALL_REFERENCE_SURROGATE_CLAIM_BOUNDARY


def test_404nm_sidewall_surrogate_reduces_reference_amplitude() -> None:
    rows = build_sidewall_reference_surrogate_rows(wavelengths_nm=(404,))
    by_case = {row.case_id: row for row in rows}

    rectangle = by_case["rectangle_limit_theta90_D900_W500"]
    trapezoid = by_case["taper_theta85_D900_W500"]

    assert rectangle.na_cutoff_active is False
    assert trapezoid.na_cutoff_active is False
    assert rectangle.trapezoid_effective_aperture_factor == 1.0
    assert 0.0 < trapezoid.trapezoid_effective_aperture_factor < 1.0
    assert trapezoid.A_ref < rectangle.A_ref
    assert trapezoid.reference_geometry_propagation_status == (
        "trapezoid_geometry_propagated_to_effective_aperture_reference_surrogate"
    )
    assert trapezoid.reference_uses_rectangular_width_depth_surrogate is False


def test_660nm_rows_record_na_cutoff_context() -> None:
    rows = build_sidewall_reference_surrogate_rows(wavelengths_nm=(660,))

    assert all(row.na_cutoff_condition_met for row in rows)
    assert all(row.na_cutoff_active for row in rows)
    assert all(row.A_ref == 0.0 for row in rows)
