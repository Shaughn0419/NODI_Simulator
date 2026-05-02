from __future__ import annotations

from dataclasses import replace

import numpy as np

from nodi_simulator.data_objects import DEFAULT_SIM_CFG
from nodi_simulator.parameter_sweep import (
    _build_event_block_random_state,
    _draw_block_lane_order_block_randoms,
    _draw_event_loop_order_block_randoms,
)


def _draw_expected_event_loop_order_randoms(
    *,
    seed: int,
    block_size: int,
    n_samples: int,
    sim_cfg,
    include_diffusion: bool,
) -> dict[str, np.ndarray | None]:
    rng = np.random.default_rng(seed)
    diffusion_draws = (
        np.empty((block_size, 2 * max(n_samples - 1, 0)), dtype=float)
        if include_diffusion
        else None
    )
    detector_noise = (
        np.empty((block_size, n_samples), dtype=float)
        if sim_cfg.noise_std > 0
        else None
    )
    shot_standard = (
        np.empty((block_size, n_samples), dtype=float)
        if sim_cfg.shot_noise_scale > 0
        else None
    )
    post_detect_noise = (
        np.empty((block_size, n_samples), dtype=float)
        if sim_cfg.post_readout_noise_std > 0
        else None
    )
    post_nodi_noise = (
        np.empty((block_size, n_samples), dtype=float)
        if sim_cfg.post_readout_noise_std > 0
        else None
    )
    post_pod_noise = (
        np.empty((block_size, n_samples), dtype=float)
        if sim_cfg.post_readout_noise_std > 0
        else None
    )

    for offset in range(block_size):
        if diffusion_draws is not None:
            diffusion_draws[offset] = rng.standard_normal(2 * max(n_samples - 1, 0))
        if detector_noise is not None:
            detector_noise[offset] = rng.normal(0, sim_cfg.noise_std, size=n_samples)
        if shot_standard is not None:
            shot_standard[offset] = rng.normal(0.0, 1.0, size=n_samples)
        if post_detect_noise is not None:
            post_detect_noise[offset] = rng.normal(
                0,
                sim_cfg.post_readout_noise_std,
                size=n_samples,
            )
            post_nodi_noise[offset] = rng.normal(
                0,
                sim_cfg.post_readout_noise_std,
                size=n_samples,
            )
            post_pod_noise[offset] = rng.normal(
                0,
                sim_cfg.post_readout_noise_std,
                size=n_samples,
            )

    return {
        "diffusion_draws": diffusion_draws,
        "detector_noise": detector_noise,
        "shot_standard": shot_standard,
        "post_detect_noise": post_detect_noise,
        "post_nodi_noise": post_nodi_noise,
        "post_pod_noise": post_pod_noise,
    }


def test_block_randoms_preserve_scalar_event_loop_order():
    sim_cfg = replace(
        DEFAULT_SIM_CFG,
        noise_std=0.13,
        shot_noise_scale=0.17,
        post_readout_noise_std=0.19,
    )
    seed = 12345
    expected = _draw_expected_event_loop_order_randoms(
        seed=seed,
        block_size=5,
        n_samples=7,
        sim_cfg=sim_cfg,
        include_diffusion=True,
    )

    actual = _draw_event_loop_order_block_randoms(
        rng=np.random.default_rng(seed),
        block_size=5,
        n_samples=7,
        sim_cfg=sim_cfg,
        include_diffusion=True,
    )

    assert actual.keys() == expected.keys()
    for key, expected_value in expected.items():
        actual_value = actual[key]
        if expected_value is None:
            assert actual_value is None
        else:
            np.testing.assert_array_equal(actual_value, expected_value)


def test_block_lane_randoms_draw_only_retained_stream_summary_lanes():
    sim_cfg = replace(
        DEFAULT_SIM_CFG,
        noise_std=0.13,
        shot_noise_scale=0.17,
        post_readout_noise_std=0.19,
    )
    actual = _draw_block_lane_order_block_randoms(
        random_state=_build_event_block_random_state(12345),
        block_size=5,
        n_samples=7,
        sim_cfg=sim_cfg,
        include_diffusion=True,
    )

    assert actual["diffusion_draws"].shape == (5, 12)
    assert actual["detector_noise"].shape == (5, 7)
    assert actual["shot_standard"].shape == (5, 7)
    assert actual["post_detect_noise"].shape == (5, 7)
    assert actual["post_nodi_noise"] is None
    assert actual["post_pod_noise"].shape == (5, 7)
    assert actual["diffusion_draws"].dtype == np.float32
    assert actual["detector_noise"].dtype == np.float32
