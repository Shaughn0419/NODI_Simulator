from __future__ import annotations

import argparse
from copy import copy
from dataclasses import replace
import json
from pathlib import Path

import pandas as pd
import pytest

from nodi_simulator.parameter_sweep import (
    run_single_case_batch,
    run_single_case_batch_shared_event_normalization_views,
)
from tools import aggregate_lens_b_ev_gold_fullgrid_3seed as aggregate
from tools import analyze_lens_b_ev_gold_fullgrid as analyze
from tools import lens_b_ev_gold_fullgrid_runner as runner


def test_full_runner_requires_formal_seed_events_and_one_lane_acknowledgement():
    args = runner.build_parser().parse_args(
        [
            "--mode",
            "full",
            "--workers",
            "16",
            "--n-events",
            "10000",
            "--seed",
            "42",
            "--output-dir",
            "unused",
            "--particle-scope",
            "ev_gold",
            "--normalization-lane",
            "fixed_660_gold",
            "--route-source",
            "unused.csv",
        ]
    )
    errors = runner._full_launch_arg_errors(args)
    assert any("seed must be one of" in error for error in errors)
    assert any("--accept-one-lane-primitive" in error for error in errors)

    args.seed = 11
    args.accept_one_lane_primitive = True
    assert runner._full_launch_arg_errors(args) == []


def test_shared_dual_full_runner_does_not_require_one_lane_acknowledgement():
    args = runner.build_parser().parse_args(
        [
            "--mode",
            "full",
            "--workers",
            "16",
            "--n-events",
            "10000",
            "--seed",
            "11",
            "--output-dir",
            "unused",
            "--particle-scope",
            "ev_gold",
            "--normalization-lane",
            "shared_dual_gold",
            "--route-source",
            "unused.csv",
        ]
    )
    assert runner._full_launch_arg_errors(args) == []


def test_shared_event_dual_progress_fields_make_final_progress_unambiguous():
    progress = runner._add_shared_event_dual_progress_fields(
        {
            "completed": 32032,
            "total": 32032,
            "status": "completed",
        }
    )
    assert progress["normalization_lane"] == "shared_dual_gold"
    assert progress["normalization_views"] == [
        "per_wavelength_gold",
        "fixed_660_gold",
    ]
    assert progress["shared_event_dual_normalization_used"] is True
    assert progress["analysis_view_row_total_per_seed"] == 64064


def test_output_guard_refuses_existing_files_without_overwrite(tmp_path: Path):
    existing = tmp_path / "seed_11_raw_rows.csv"
    existing.write_text("already here", encoding="utf-8")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        runner._guard_output_paths([existing], allow_overwrite=False)
    runner._guard_output_paths([existing], allow_overwrite=True)


def test_diagnostic_scalar_frame_preserves_scalars_without_event_arrays():
    frame = runner._diagnostic_scalar_frame(
        [
            {
                "particle_name": "gold_40nm",
                "score": 0.5,
                "summary": {
                    "all_crossing_n_events": 10000,
                    "all_heights": [0.1, 0.2],
                    "bayesian_posterior_available": False,
                    "E_sca_unit_normalized_complex": complex(1.0, 2.0),
                },
            }
        ]
    )
    assert frame.loc[0, "particle_name"] == "gold_40nm"
    assert frame.loc[0, "all_crossing_n_events"] == 10000
    assert bool(frame.loc[0, "bayesian_posterior_available"]) is False
    assert frame.loc[0, "E_sca_unit_normalized_complex"] == "(1+2j)"
    assert "all_heights" not in frame.columns


def _shared_and_independent_batches(
    *,
    route: tuple[int, int, int],
    particle_name: str,
    n_events: int = 6,
):
    wavelength_nm, width_nm, depth_nm = route
    seed = 11
    base_cfg, optical_template = runner.build_frozen_b_cfg(n_events, seed)
    particle = runner.particle_from_name(particle_name)
    medium = runner.medium_for_particle(particle)
    channel = runner.lane.case_baseline_channel(width_nm, depth_nm)
    optical = copy(optical_template)
    optical.wavelength_m = float(wavelength_nm) * 1e-9
    cfg_by_lane = {
        lane_name: runner._cfg_for_normalization_lane(base_cfg, lane_name)
        for lane_name in runner.SINGLE_NORMALIZATION_LANES
    }
    refs = {
        "fixed_660_gold": runner._fixed_660_e_sca_ref(
            width_nm=width_nm,
            depth_nm=depth_nm,
            cfg=cfg_by_lane["fixed_660_gold"],
            optical_template=optical_template,
        ),
        "per_wavelength_gold": runner._per_wavelength_e_sca_ref(
            wavelength_nm=wavelength_nm,
            width_nm=width_nm,
            depth_nm=depth_nm,
            medium=medium,
            cfg=cfg_by_lane["per_wavelength_gold"],
            optical_template=optical_template,
        ),
    }
    shared = run_single_case_batch_shared_event_normalization_views(
        particle,
        medium,
        channel,
        optical,
        cfg_by_lane,
        refs,
        runner.THETA_GRID_RAD,
    )
    independent = {
        lane_name: run_single_case_batch(
            particle,
            medium,
            channel,
            optical,
            cfg,
            refs[lane_name],
            runner.THETA_GRID_RAD,
            retain_event_traces=False,
            stream_summary_only=True,
        )
        for lane_name, cfg in cfg_by_lane.items()
    }
    return shared, independent


@pytest.mark.parametrize(
    "route, particle_name, expect_views_equal",
    [
        ((404, 800, 1400), "gold_40nm", False),
        ((660, 800, 1400), "gold_40nm", True),
        ((404, 800, 1400), "exosome_biomimetic_corona_nominal_100nm", False),
    ],
)
def test_shared_event_dual_normalization_matches_independent_views(
    route: tuple[int, int, int],
    particle_name: str,
    expect_views_equal: bool,
):
    n_events = 6
    shared, independent = _shared_and_independent_batches(
        route=route,
        particle_name=particle_name,
        n_events=n_events,
    )
    exact_keys = [
        "n_events",
        "case_random_seed",
        "case_random_identity",
        "detection_rate",
        "selected_detector_mode_annulus_detection_rate",
        "mean_peak_height",
        "mean_local_snr",
        "mean_threshold",
        "mean_threshold_robust_std",
        "peak_height_p90",
        "local_snr_p90",
        "engineering_gate_passed",
    ]
    for lane_name in runner.SINGLE_NORMALIZATION_LANES:
        shared_summary = shared[lane_name]["summary"]
        independent_summary = independent[lane_name]["summary"]
        assert shared_summary["shared_event_dual_normalization_used"] is True
        assert shared_summary["shared_event_physical_event_count"] == n_events
        for key in exact_keys:
            expected = independent_summary[key]
            actual = shared_summary[key]
            if isinstance(expected, float):
                assert actual == pytest.approx(expected, rel=0.0, abs=1e-12), key
            else:
                assert actual == expected, key

    if expect_views_equal:
        fixed_summary = shared["fixed_660_gold"]["summary"]
        per_summary = shared["per_wavelength_gold"]["summary"]
        for key in (
            "mean_peak_height",
            "mean_local_snr",
            "detection_rate",
            "selected_detector_mode_annulus_detection_rate",
            "peak_height_p90",
            "local_snr_p90",
        ):
            assert fixed_summary[key] == pytest.approx(
                per_summary[key],
                rel=0.0,
                abs=1e-12,
            ), key


def test_shared_event_summary_preserves_independent_summary_keys():
    shared, independent = _shared_and_independent_batches(
        route=(404, 800, 1400),
        particle_name="gold_40nm",
        n_events=6,
    )
    leak_sensitive_keys = {
        "manifest_id",
        "sweep_manifest_id",
        "config_hash",
        "case_hash",
        "estimated_memory_GB",
        "estimated_runtime_proxy",
    }
    for lane_name in runner.SINGLE_NORMALIZATION_LANES:
        shared_summary = shared[lane_name]["summary"]
        independent_summary = independent[lane_name]["summary"]
        missing = set(independent_summary) - set(shared_summary)
        assert not missing, f"shared path dropped summary keys for {lane_name}: {missing}"
        for key in leak_sensitive_keys:
            assert shared_summary[key] == independent_summary[key], key
        assert (
            shared_summary["vectorized_event_engine_fallback_reason"]
            == "shared_dual_event_loop_path"
        )


def test_shared_event_dual_normalization_rejects_rng_affecting_view_mismatch():
    route = (404, 800, 1400)
    wavelength_nm, width_nm, depth_nm = route
    base_cfg, optical_template = runner.build_frozen_b_cfg(2, 11)
    particle = runner.particle_from_name("gold_40nm")
    medium = runner.medium_for_particle(particle)
    channel = runner.lane.case_baseline_channel(width_nm, depth_nm)
    optical = copy(optical_template)
    optical.wavelength_m = float(wavelength_nm) * 1e-9
    cfg_by_lane = {
        lane_name: runner._cfg_for_normalization_lane(base_cfg, lane_name)
        for lane_name in runner.SINGLE_NORMALIZATION_LANES
    }
    cfg_by_lane["per_wavelength_gold"] = replace(
        cfg_by_lane["per_wavelength_gold"],
        post_readout_noise_std=1.0e-9,
    )
    refs = {
        "fixed_660_gold": runner._fixed_660_e_sca_ref(
            width_nm=width_nm,
            depth_nm=depth_nm,
            cfg=cfg_by_lane["fixed_660_gold"],
            optical_template=optical_template,
        ),
        "per_wavelength_gold": runner._per_wavelength_e_sca_ref(
            wavelength_nm=wavelength_nm,
            width_nm=width_nm,
            depth_nm=depth_nm,
            medium=medium,
            cfg=cfg_by_lane["per_wavelength_gold"],
            optical_template=optical_template,
        ),
    }

    with pytest.raises(ValueError, match="post_readout_noise_std"):
        run_single_case_batch_shared_event_normalization_views(
            particle,
            medium,
            channel,
            optical,
            cfg_by_lane,
            refs,
            runner.THETA_GRID_RAD,
        )


def _minimal_raw_frame(*, seed: int = 11, lane: str = "fixed_660_gold") -> pd.DataFrame:
    rows = []
    for wavelength in (404, 488, 532, 660):
        rows.append(
            {
                "random_seed": seed,
                "n_events": 10000,
                "normalization_lane": lane,
                "particle_material": "exosome",
                "particle_name": f"exosome_{wavelength}",
                "wavelength_nm": wavelength,
                "width_nm": 800,
                "depth_nm": 1400,
                "lockin_time_constant_s": 0.001,
            }
        )
        rows.append(
            {
                "random_seed": seed,
                "n_events": 10000,
                "normalization_lane": lane,
                "particle_material": "gold",
                "particle_name": f"gold_{wavelength}",
                "wavelength_nm": wavelength,
                "width_nm": 800,
                "depth_nm": 1400,
                "lockin_time_constant_s": 0.001,
            }
        )
    return pd.DataFrame(rows)


def test_analyzer_precheck_accepts_expected_seed_and_lane():
    df = _minimal_raw_frame(seed=11, lane="fixed_660_gold")
    checks = analyze.validate_input(
        df,
        expected_rows=8,
        expected_seed=11,
        expected_n_events=10000,
        expected_normalization_lane="fixed_660_gold",
    )
    assert checks["status"] == "passed"


def test_analyzer_precheck_rejects_wrong_seed_and_mixed_lanes():
    df = _minimal_raw_frame(seed=42, lane="fixed_660_gold")
    checks = analyze.validate_input(
        df,
        expected_rows=8,
        expected_seed=11,
        expected_n_events=10000,
        expected_normalization_lane="fixed_660_gold",
    )
    assert checks["status"] == "failed"
    assert any("random_seed expected [11]" in failure for failure in checks["failures"])

    mixed = pd.concat(
        [
            _minimal_raw_frame(seed=11, lane="fixed_660_gold").iloc[:4],
            _minimal_raw_frame(seed=11, lane="per_wavelength_gold").iloc[4:],
        ],
        ignore_index=True,
    )
    checks = analyze.validate_input(
        mixed,
        expected_rows=8,
        expected_seed=11,
        expected_n_events=10000,
    )
    assert checks["status"] == "failed"
    assert any("one normalization view" in failure for failure in checks["failures"])


def _write_derived_dir(root: Path, *, seed: int, lane: str) -> Path:
    path = root / f"seed_{seed}_{lane}"
    path.mkdir()
    precheck = {
        "status": "passed",
        "source_csv": f"seed_{seed}_raw_rows.csv",
        "random_seed_values": [seed],
        "normalization_lane_values": [lane],
        "row_count": 32032,
        "n_events_values": [10000],
    }
    (path / "lens_b_fullgrid_data_precheck.json").write_text(
        json.dumps(precheck),
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "wavelength_nm": 660,
                "width_nm": 800,
                "depth_nm": 1400,
                "raw_mean_selected_annulus_detection": 0.1 + seed / 1000.0,
                "uniform_weighted_selected_annulus_detection": 0.2 + seed / 1000.0,
                "uniform_weighted_stable": 0.3,
                "uniform_weighted_final": 0.4,
                "uniform_selected_rank_reference_useful": 1,
            }
        ]
    ).to_csv(path / "lens_b_ev_fullgrid_route_ranking.csv", index=False)
    return path


def test_three_seed_aggregator_preserves_seed_and_lane_coverage(tmp_path: Path):
    derived_dirs = [
        _write_derived_dir(tmp_path, seed=seed, lane="fixed_660_gold")
        for seed in (11, 22, 33)
    ]
    out = tmp_path / "agg"
    aggregate.run(
        argparse.Namespace(
            derived_dir=[str(path) for path in derived_dirs],
            output_dir=str(out),
            expected_seeds="11,22,33",
            expected_normalization_lanes="fixed_660_gold",
            top_n=5,
            check_only=False,
        )
    )
    summary = json.loads(
        (out / "lens_b_fullgrid_3seed_aggregation_summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["coverage"]["status"] == "passed"
    stability = pd.read_csv(out / "lens_b_ev_fullgrid_3seed_route_stability.csv")
    assert stability.loc[0, "seed_count"] == 3
