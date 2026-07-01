from __future__ import annotations

from nodi_simulator.sidewall_selected_annulus_context import (
    SIDEWALL_SELECTED_ANNULUS_CONTEXT_CLAIM_BOUNDARY,
    run_sidewall_selected_annulus_context,
)


def test_sidewall_selected_annulus_context_runs_rectangle_and_theta85() -> None:
    rows = run_sidewall_selected_annulus_context(n_events=16, random_seed=531)

    assert len(rows) == 2
    assert {row.case_id for row in rows} == {
        "rectangle_limit_theta90_D900_W500",
        "taper_theta85_D900_W500",
    }
    assert {row.reference_model for row in rows} == {
        "trapezoid_effective_aperture_surrogate"
    }
    for row in rows:
        assert row.width_nm == 500
        assert row.depth_nm == 900
        assert row.wavelength_nm == 404
        assert row.n_events == 16
        assert row.selected_annulus_source == (
            "initial_position_edge_norm_annulus_diagnostic_v1"
        )
        assert row.selected_annulus_edge_norm_min == 0.5
        assert row.selected_annulus_edge_norm_max == 0.8
        assert row.selected_annulus_n_events > 0
        assert 0.0 <= row.selected_annulus_detection_context_rate <= 1.0
        assert 0.0 <= row.selected_annulus_fraction <= 1.0
        assert row.selected_annulus_context_status == (
            "selected_annulus_context_available_small_n_not_probability"
        )
        assert row.selected_annulus_context_current is True
        assert row.small_n_synthetic_context is True
        assert row.detection_probability_current is False
        assert row.route_score_current is False
        assert row.winner_current is False
        assert row.yield_current is False
        assert row.claim_boundary == SIDEWALL_SELECTED_ANNULUS_CONTEXT_CLAIM_BOUNDARY


def test_sidewall_selected_annulus_context_keeps_detection_context_qualified() -> None:
    rows = run_sidewall_selected_annulus_context(n_events=16, random_seed=532)
    theta85 = next(row for row in rows if row.case_id == "taper_theta85_D900_W500")

    assert theta85.channel_cross_section_model == "trapezoid_tapered_sidewalls"
    assert theta85.sidewall_deg_comsol == 85.0
    assert theta85.selected_annulus_n_events > 0
    assert theta85.selected_annulus_n_detected <= theta85.selected_annulus_n_events
    assert 0.0 <= theta85.all_crossing_detection_context_rate <= 1.0
    assert 0.0 <= theta85.selected_detector_mode_candidate_detection_context_rate <= 1.0
    assert theta85.detection_probability_current is False
    assert theta85.route_score_current is False
