from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from tools.benchmarks.event_engine_benchmark import (
    _aggregate_comparisons,
    _aggregate_records,
    _build_benchmark_grid_config,
    _compare_to_baseline,
    _select_spread_values,
    _select_recommendation,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_legacy_event_engine_benchmark_entrypoint_help_still_works():
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "tools" / "event_engine_benchmark.py"), "--help"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Run a short 8-worker precompute benchmark" in result.stdout


def _benchmark_frame(*, peak_width_ms: float) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "particle_name": "gold_40nm",
                "wavelength_nm": 660,
                "width_nm": 800,
                "depth_nm": 500,
                "detection_rate": 0.25,
                "stable_detection_rate": 0.20,
                "mean_peak_height": 1.5,
                "mean_peak_width_ms": peak_width_ms,
                "engineering_gate_passed": True,
            }
        ]
    )


def test_event_engine_benchmark_compares_exported_peak_width_ms_as_seconds():
    comparison = _compare_to_baseline(
        baseline_df=_benchmark_frame(peak_width_ms=2.0),
        candidate_df=_benchmark_frame(peak_width_ms=3.0),
    )

    assert comparison["matched_cases"] == 1
    assert comparison["max_abs_delta_mean_peak_width_s"] == pytest.approx(1e-3)
    assert comparison["engineering_gate_agreement_rate"] == 1.0


def test_event_engine_benchmark_keeps_current_default_for_small_runtime_delta():
    records = [
        {
            "name": "scalar_off_b32",
            "wall_time_s": 10.0,
            "completion_status": "complete",
            "fallback_counts": {"disabled": 1},
        },
        {
            "name": "event_block_v3_b32",
            "vectorized_event_engine": "event_block_v3",
            "event_block_size": 32,
            "wall_time_s": 9.7,
            "completion_status": "complete",
            "fallback_counts": {"<none>": 1},
        },
        {
            "name": "event_block_v3_b16",
            "vectorized_event_engine": "event_block_v3",
            "event_block_size": 16,
            "wall_time_s": 9.5,
            "completion_status": "complete",
            "fallback_counts": {"<none>": 1},
        },
    ]
    clean_comparison = {
        "max_abs_delta_detection_rate": 0.0,
        "max_abs_delta_stable_detection_rate": 0.0,
        "max_abs_relative_delta_mean_peak_height": 0.0,
        "max_abs_relative_delta_mean_peak_width_s": 0.0,
        "engineering_gate_agreement_rate": 1.0,
    }
    recommendation = _select_recommendation(
        records,
        {
            "event_block_v3_b32": clean_comparison,
            "event_block_v3_b16": clean_comparison,
        },
        baseline_name="scalar_off_b32",
        current_default_engine="event_block_v3",
        current_default_block_size=32,
        current_default_rng_order="event_loop_order",
    )

    assert recommendation["decision"] == "keep_current_default"
    assert recommendation["recommended_engine"] == "event_block_v3"
    assert recommendation["recommended_block_size"] == 32
    assert recommendation["recommended_event_block_rng_order"] == "event_loop_order"
    assert recommendation["fastest_passing_block_size"] == 16


def test_event_engine_benchmark_selects_spread_values_with_middle_singleton():
    values = [500e-9, 1000e-9, 1500e-9, 2000e-9]

    assert _select_spread_values(values, 1).tolist() == [1500e-9]
    assert _select_spread_values(values, 2).tolist() == [500e-9, 2000e-9]


def test_event_engine_benchmark_builds_sampled_long_event_grid():
    base_grid = {
        "wavelength_list_m": [404e-9, 488e-9, 532e-9, 660e-9],
        "width_list_m": [500e-9, 1000e-9, 1500e-9, 2000e-9],
        "depth_list_m": [500e-9, 1000e-9, 1500e-9, 2000e-9],
        "n_events": 30,
    }

    grid, actual_cases, selected_counts = _build_benchmark_grid_config(
        base_grid=base_grid,
        events_per_case=3000,
        particle_count=2,
        sample_case_limit=16,
    )

    assert grid["n_events"] == 3000
    assert actual_cases == 16
    assert selected_counts == {
        "wavelength_list_m": 4,
        "width_list_m": 2,
        "depth_list_m": 1,
    }
    assert grid["wavelength_list_m"].tolist() == base_grid["wavelength_list_m"]
    assert grid["width_list_m"].tolist() == [500e-9, 2000e-9]
    assert grid["depth_list_m"].tolist() == [1500e-9]


def test_event_engine_benchmark_aggregates_repeats_with_median_runtime():
    records = [
        {
            "name": "event_block_v3_b32",
            "variant_tag": "r1",
            "vectorized_event_engine": "event_block_v3",
            "event_block_size": 32,
            "wall_time_s": 10.0,
            "cases": 16,
            "completion_status": "complete",
            "expected_total_cases": 16,
            "engine_used_counts": {"event_block_v3": 16},
            "fallback_counts": {"<none>": 16},
            "log_path": "r1.log",
        },
        {
            "name": "event_block_v3_b32",
            "variant_tag": "r2",
            "vectorized_event_engine": "event_block_v3",
            "event_block_size": 32,
            "wall_time_s": 14.0,
            "cases": 16,
            "completion_status": "complete",
            "expected_total_cases": 16,
            "engine_used_counts": {"event_block_v3": 16},
            "fallback_counts": {"<none>": 16},
            "log_path": "r2.log",
        },
    ]

    aggregate = _aggregate_records(records)

    assert len(aggregate) == 1
    assert aggregate[0]["wall_time_s"] == pytest.approx(12.0)
    assert aggregate[0]["repeat_count"] == 2
    assert aggregate[0]["engine_used_counts"] == {"event_block_v3": 32}
    assert aggregate[0]["fallback_counts"] == {"<none>": 32}


def test_event_engine_benchmark_aggregates_repeat_comparisons_conservatively():
    aggregate = _aggregate_comparisons(
        {
            "r01": {
                "event_block_v3_b32": {
                    "matched_cases": 16,
                    "max_abs_delta_detection_rate": 0.0,
                    "max_abs_relative_delta_mean_peak_height": 1e-12,
                    "engineering_gate_agreement_rate": 1.0,
                }
            },
            "r02": {
                "event_block_v3_b32": {
                    "matched_cases": 15,
                    "max_abs_delta_detection_rate": 0.01,
                    "max_abs_relative_delta_mean_peak_height": 2e-12,
                    "engineering_gate_agreement_rate": 0.99,
                }
            },
        }
    )

    comparison = aggregate["event_block_v3_b32"]
    assert comparison["repeat_count"] == 2
    assert comparison["matched_cases"] == 15
    assert comparison["max_abs_delta_detection_rate"] == pytest.approx(0.01)
    assert comparison["max_abs_relative_delta_mean_peak_height"] == pytest.approx(2e-12)
    assert comparison["engineering_gate_agreement_rate"] == pytest.approx(0.99)
