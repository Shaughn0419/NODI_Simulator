from __future__ import annotations

import pandas as pd
import pytest

from tools.audits.run_report148_t3_noise_axis import (
    _depth_rank_seed_stability,
    _depth_span_rows,
    _headline_rows,
    _promoted_shots,
)


def test_promoted_shots_flags_nonbaseline_winner_or_band_changes() -> None:
    frame = pd.DataFrame(
        [
            {"shot_noise_scale": 0.001, "seed": 11, "normalization_view": "fixed_660_gold", "point_estimate_winner_wavelength": 404, "winner_family_id": "f404", "band_404": "electronics_noise_limited_useful", "band_660": "electronics_noise_limited_useful"},
            {"shot_noise_scale": 0.001, "seed": 11, "normalization_view": "per_wavelength_gold", "point_estimate_winner_wavelength": 660, "winner_family_id": "f660", "band_404": "electronics_noise_limited_useful", "band_660": "electronics_noise_limited_useful"},
            {"shot_noise_scale": 0.05, "seed": 11, "normalization_view": "fixed_660_gold", "point_estimate_winner_wavelength": 404, "winner_family_id": "f404", "band_404": "shot_noise_limited_no_gain", "band_660": "electronics_noise_limited_useful"},
            {"shot_noise_scale": 0.05, "seed": 11, "normalization_view": "per_wavelength_gold", "point_estimate_winner_wavelength": 660, "winner_family_id": "f660", "band_404": "shot_noise_limited_no_gain", "band_660": "electronics_noise_limited_useful"},
            {"shot_noise_scale": 0.2, "seed": 11, "normalization_view": "fixed_660_gold", "point_estimate_winner_wavelength": 660, "winner_family_id": "f660", "band_404": "shot_noise_limited_no_gain", "band_660": "shot_noise_limited_no_gain"},
            {"shot_noise_scale": 0.2, "seed": 11, "normalization_view": "per_wavelength_gold", "point_estimate_winner_wavelength": 660, "winner_family_id": "f660", "band_404": "shot_noise_limited_no_gain", "band_660": "shot_noise_limited_no_gain"},
        ]
    )

    assert _promoted_shots(frame) == {0.05, 0.2}


def test_depth_span_rows_separates_all_crossing_and_selected_annulus_faces() -> None:
    route_df = pd.DataFrame(
        [
            {"shot_noise_scale": 0.001, "seed": 11, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 700, "weighted_selected_annulus_detection": 0.8, "weighted_all_crossing_detection": 0.3, "mean_peak_margin_z": 10.0},
            {"shot_noise_scale": 0.001, "seed": 11, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 1300, "weighted_selected_annulus_detection": 0.6, "weighted_all_crossing_detection": 0.9, "mean_peak_margin_z": 8.0},
            {"shot_noise_scale": 0.001, "seed": 11, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 600, "depth_nm": 700, "weighted_selected_annulus_detection": 0.7, "weighted_all_crossing_detection": 0.2, "mean_peak_margin_z": 9.0},
            {"shot_noise_scale": 0.001, "seed": 11, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 600, "depth_nm": 1300, "weighted_selected_annulus_detection": 0.4, "weighted_all_crossing_detection": 0.4, "mean_peak_margin_z": 7.0},
        ]
    )

    span = _depth_span_rows(route_df).iloc[0]
    assert span["selected_width_nm"] == 500
    assert span["all_crossing_width_nm"] == 500
    assert span["depth_span_selected_annulus"] == pytest.approx(0.2)
    assert span["depth_span_all_crossing"] == pytest.approx(0.6)


def test_headline_rows_tracks_view_disagreement_on_point_estimate_winner_wavelength() -> None:
    route_df = pd.DataFrame(
        [
            {"shot_noise_scale": 0.2, "seed": 11, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 700, "route_family_id": "lambda404_w500_depth_sweep", "weighted_selected_annulus_detection": 0.4, "mean_peak_margin_z": 5.0, "reference_operating_band": "shot_noise_limited_no_gain"},
            {"shot_noise_scale": 0.2, "seed": 11, "normalization_view": "fixed_660_gold", "wavelength_nm": 660, "width_nm": 700, "depth_nm": 700, "route_family_id": "lambda660_w700_depth_sweep", "weighted_selected_annulus_detection": 0.5, "mean_peak_margin_z": 6.0, "reference_operating_band": "reference_too_weak"},
            {"shot_noise_scale": 0.2, "seed": 11, "normalization_view": "per_wavelength_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 700, "route_family_id": "lambda404_w500_depth_sweep", "weighted_selected_annulus_detection": 0.6, "mean_peak_margin_z": 7.0, "reference_operating_band": "shot_noise_limited_no_gain"},
            {"shot_noise_scale": 0.2, "seed": 11, "normalization_view": "per_wavelength_gold", "wavelength_nm": 660, "width_nm": 700, "depth_nm": 700, "route_family_id": "lambda660_w700_depth_sweep", "weighted_selected_annulus_detection": 0.4, "mean_peak_margin_z": 4.0, "reference_operating_band": "reference_too_weak"},
        ]
    )

    headline = _headline_rows(route_df)
    assert set(headline["point_estimate_winner_wavelength"]) == {404, 660}
    assert headline["views_disagree_on_point_estimate_winner_wavelength"].unique().tolist() == [True]
    assert set(headline["wilson_separation_status"]) == {"overlap"}
    assert headline["winner_claim_allowed"].unique().tolist() == [False]
    assert headline["candidate_family_retained"].unique().tolist() == [True]


def test_depth_rank_seed_stability_counts_seed_stable_faces() -> None:
    route_df = pd.DataFrame(
        [
                {"shot_noise_scale": 0.05, "seed": 11, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 700, "weighted_selected_annulus_detection": 0.8, "weighted_all_crossing_detection": 0.9, "mean_peak_margin_z": 1.0},
                {"shot_noise_scale": 0.05, "seed": 11, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 900, "weighted_selected_annulus_detection": 0.7, "weighted_all_crossing_detection": 0.8, "mean_peak_margin_z": 1.0},
                {"shot_noise_scale": 0.05, "seed": 22, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 700, "weighted_selected_annulus_detection": 0.7, "weighted_all_crossing_detection": 0.9, "mean_peak_margin_z": 1.0},
                {"shot_noise_scale": 0.05, "seed": 22, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 900, "weighted_selected_annulus_detection": 0.8, "weighted_all_crossing_detection": 0.7, "mean_peak_margin_z": 1.0},
                {"shot_noise_scale": 0.05, "seed": 33, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 700, "weighted_selected_annulus_detection": 0.8, "weighted_all_crossing_detection": 0.8, "mean_peak_margin_z": 1.0},
                {"shot_noise_scale": 0.05, "seed": 33, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 900, "weighted_selected_annulus_detection": 0.7, "weighted_all_crossing_detection": 0.4, "mean_peak_margin_z": 1.0},
        ]
    )

    stability, counts = _depth_rank_seed_stability(route_df)
    assert set(stability["metric_face"]) == {"selected_annulus", "all_crossing"}
    selected = stability[stability["metric_face"].eq("selected_annulus")].iloc[0]
    all_crossing = stability[stability["metric_face"].eq("all_crossing")].iloc[0]
    assert bool(selected["seed_stable"]) is False
    assert bool(all_crossing["seed_stable"]) is True
    assert counts == {
        "selected_stable": 0,
        "selected_total": 1,
        "all_crossing_stable": 1,
        "all_crossing_total": 1,
    }


def test_depth_rank_seed_stability_includes_0001_baseline() -> None:
    route_df = pd.DataFrame(
        [
            {"shot_noise_scale": 0.001, "seed": 11, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 700, "weighted_selected_annulus_detection": 0.8, "weighted_all_crossing_detection": 0.9, "mean_peak_margin_z": 1.0},
            {"shot_noise_scale": 0.001, "seed": 11, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 900, "weighted_selected_annulus_detection": 0.7, "weighted_all_crossing_detection": 0.8, "mean_peak_margin_z": 1.0},
            {"shot_noise_scale": 0.001, "seed": 22, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 700, "weighted_selected_annulus_detection": 0.7, "weighted_all_crossing_detection": 0.9, "mean_peak_margin_z": 1.0},
            {"shot_noise_scale": 0.001, "seed": 22, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 900, "weighted_selected_annulus_detection": 0.8, "weighted_all_crossing_detection": 0.8, "mean_peak_margin_z": 1.0},
            {"shot_noise_scale": 0.001, "seed": 33, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 700, "weighted_selected_annulus_detection": 0.7, "weighted_all_crossing_detection": 0.9, "mean_peak_margin_z": 1.0},
            {"shot_noise_scale": 0.001, "seed": 33, "normalization_view": "fixed_660_gold", "wavelength_nm": 404, "width_nm": 500, "depth_nm": 900, "weighted_selected_annulus_detection": 0.8, "weighted_all_crossing_detection": 0.8, "mean_peak_margin_z": 1.0},
        ]
    )

    stability, counts = _depth_rank_seed_stability(route_df)
    assert len(stability) == 2
    assert counts == {
        "selected_stable": 0,
        "selected_total": 1,
        "all_crossing_stable": 1,
        "all_crossing_total": 1,
    }
