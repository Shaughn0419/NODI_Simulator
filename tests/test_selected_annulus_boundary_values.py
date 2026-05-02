from __future__ import annotations

import math

import pytest

from nodi_simulator.data_objects import SimulationConfig
from nodi_simulator.parameter_sweep import summarize_batch


def _event(*, detected: bool, edge_norm: float) -> dict:
    features = (
        {
            "n_peaks": 1,
            "peaks": [
                {
                    "peak_height": 2.0,
                    "peak_signed_height": 2.0,
                    "peak_width_s": 0.003,
                }
            ],
        }
        if detected
        else {"n_peaks": 0, "peaks": []}
    )
    return {
        "features": features,
        "features_nodi": features,
        "features_paired": {"n_peaks": 0, "peaks": []},
        "detected_single_channel": detected,
        "detected_paired_channel": False,
        "threshold": 1.0,
        "threshold_robust_std": 1.0,
        "pod_threshold": 1.0,
        "pod_threshold_robust_std": 1.0,
        "initial_position_x_norm": edge_norm,
        "initial_position_z_norm": 0.0,
        "event_max_margin_z": 1.0,
        "background_max_margin_z": -1.0,
    }


def test_selected_annulus_boundary_values_are_inclusive():
    summary = summarize_batch(
        [
            _event(detected=True, edge_norm=0.49),
            _event(detected=True, edge_norm=0.50),
            _event(detected=False, edge_norm=0.80),
            _event(detected=True, edge_norm=0.81),
        ]
    )

    assert summary["selected_detector_mode_annulus_edge_norm_min"] == pytest.approx(
        0.5
    )
    assert summary["selected_detector_mode_annulus_edge_norm_max"] == pytest.approx(
        0.8
    )
    assert summary["selected_detector_mode_annulus_n_events"] == 2
    assert summary["selected_detector_mode_annulus_n_detected"] == 1
    assert summary["selected_detector_mode_annulus_fraction"] == pytest.approx(0.5)
    assert summary["selected_detector_mode_annulus_detection_rate"] == pytest.approx(
        0.5
    )
    assert summary["selected_detector_mode_annulus_mean_edge_norm"] == pytest.approx(
        0.65
    )


def test_selected_annulus_bounds_are_configurable_for_sensitivity_lanes():
    summary = summarize_batch(
        [
            _event(detected=True, edge_norm=0.35),
            _event(detected=False, edge_norm=0.45),
            _event(detected=True, edge_norm=0.60),
            _event(detected=True, edge_norm=0.85),
        ],
        selected_annulus_edge_norm_min=0.4,
        selected_annulus_edge_norm_max=0.6,
    )

    assert summary["selected_detector_mode_annulus_edge_norm_min"] == pytest.approx(
        0.4
    )
    assert summary["selected_detector_mode_annulus_edge_norm_max"] == pytest.approx(
        0.6
    )
    assert summary["selected_detector_mode_annulus_n_events"] == 2
    assert summary["selected_detector_mode_annulus_n_detected"] == 1
    assert summary["selected_detector_mode_annulus_detection_rate"] == pytest.approx(
        0.5
    )


def test_selected_annulus_zero_event_denominator_is_nan_not_zero_rate():
    summary = summarize_batch(
        [
            _event(detected=True, edge_norm=0.10),
            _event(detected=False, edge_norm=0.90),
        ]
    )

    assert summary["selected_detector_mode_annulus_n_events"] == 0
    assert summary["selected_detector_mode_annulus_n_detected"] == 0
    assert summary["selected_detector_mode_annulus_fraction"] == pytest.approx(0.0)
    assert math.isnan(summary["selected_detector_mode_annulus_detection_rate"])
    assert math.isnan(
        summary["selected_detector_mode_annulus_detection_rate_wilson_lb"]
    )
    assert math.isnan(summary["selected_detector_mode_annulus_mean_edge_norm"])


def test_selected_annulus_full_bounds_match_all_crossing_denominator():
    summary = summarize_batch(
        [
            _event(detected=True, edge_norm=0.00),
            _event(detected=False, edge_norm=0.50),
            _event(detected=True, edge_norm=1.00),
        ],
        selected_annulus_edge_norm_min=0.0,
        selected_annulus_edge_norm_max=1.0,
    )

    assert summary["selected_detector_mode_annulus_n_events"] == summary[
        "all_crossing_n_events"
    ]
    assert summary["selected_detector_mode_annulus_n_detected"] == summary[
        "all_crossing_n_detected"
    ]
    assert summary["selected_detector_mode_annulus_detection_rate"] == pytest.approx(
        summary["all_crossing_detection_rate"]
    )


def test_simulation_config_validates_selected_annulus_bounds():
    cfg = SimulationConfig(0.2, 20000.0, 2e-4)
    assert cfg.selected_annulus_edge_norm_min == pytest.approx(0.5)
    assert cfg.selected_annulus_edge_norm_max == pytest.approx(0.8)

    with pytest.raises(ValueError, match="selected_annulus_edge_norm_min/max"):
        SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            selected_annulus_edge_norm_min=0.8,
            selected_annulus_edge_norm_max=0.8,
        )

    with pytest.raises(ValueError, match="selected_annulus_edge_norm_min/max"):
        SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            selected_annulus_edge_norm_min=-0.1,
            selected_annulus_edge_norm_max=0.8,
        )

    with pytest.raises(ValueError, match="selected_annulus_edge_norm_min/max"):
        SimulationConfig(
            0.2,
            20000.0,
            2e-4,
            selected_annulus_edge_norm_min=0.5,
            selected_annulus_edge_norm_max=1.1,
        )
