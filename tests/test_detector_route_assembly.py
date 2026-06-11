from __future__ import annotations

import numpy as np
import pytest

from nodi_simulator.data_objects import BASELINE_CHANNEL, BASELINE_OPTICAL, BASELINE_PARTICLE, DEFAULT_SIM_CFG, WATER
from nodi_simulator.detector_route_assembly import (
    assemble_route_signal,
    assemble_route_trace_payload,
    compute_r_self,
)
from nodi_simulator.parameter_sweep import run_single_case_batch


def test_compute_r_self_uses_roi_over_collapsed_self() -> None:
    reference = {"self_sca_detector_integrated": 12.0}
    e_sca = 2.0 + 2.0j

    assert compute_r_self(reference, e_sca) == pytest.approx(1.5)


def test_route_degeneracy_r_self_one_makes_a_and_b_identical() -> None:
    trace = {
        "scattering_only_intensity": np.array([1.0, 2.0, 3.0]),
        "interference_cross_term_joint": np.array([0.5, -0.25, 0.75]),
        "interference_cross_term_collapsed": np.array([0.5, -0.25, 0.75]),
    }

    signal_a = assemble_route_signal(
        trace,
        "A_hybrid",
        1.0,
        interference_overlap_mode="joint_overlap_integrated",
    )
    signal_b = assemble_route_signal(
        trace,
        "B_roi_intensity",
        1.0,
        interference_overlap_mode="joint_overlap_integrated",
    )

    np.testing.assert_allclose(signal_a, signal_b)


def test_overlap_one_makes_a_and_c_identical() -> None:
    trace = {
        "scattering_only_intensity": np.array([1.0, 2.0, 3.0]),
        "interference_cross_term_joint": np.array([0.25, 0.5, -0.25]),
        "interference_cross_term_collapsed": np.array([0.25, 0.5, -0.25]),
    }

    signal_a = assemble_route_signal(
        trace,
        "A_hybrid",
        2.0,
        interference_overlap_mode="joint_overlap_integrated",
    )
    signal_c = assemble_route_signal(
        trace,
        "C_collapsed_coherent",
        2.0,
        interference_overlap_mode="joint_overlap_integrated",
    )

    np.testing.assert_allclose(signal_a, signal_c)


def test_route_conservation_matches_declared_a_b_c_d_algebra() -> None:
    trace = {
        "scattering_only_intensity": np.array([2.0, 4.0]),
        "interference_cross_term_joint": np.array([1.0, -1.5]),
        "interference_cross_term_collapsed": np.array([0.5, -0.5]),
        "I_baseline_trace": np.array([10.0, 10.0]),
    }
    r_self = 3.0

    np.testing.assert_allclose(
        assemble_route_signal(
            trace,
            "A_hybrid",
            r_self,
            interference_overlap_mode="joint_overlap_integrated",
        ),
        np.array([3.0, 2.5]),
    )
    np.testing.assert_allclose(
        assemble_route_signal(
            trace,
            "B_roi_intensity",
            r_self,
            interference_overlap_mode="joint_overlap_integrated",
        ),
        np.array([7.0, 10.5]),
    )
    np.testing.assert_allclose(
        assemble_route_signal(
            trace,
            "C_collapsed_coherent",
            r_self,
            interference_overlap_mode="joint_overlap_integrated",
        ),
        np.array([2.5, 3.5]),
    )
    np.testing.assert_allclose(
        assemble_route_signal(
            trace,
            "D_cross_only",
            r_self,
            interference_overlap_mode="joint_overlap_integrated",
        ),
        np.array([1.0, -1.5]),
    )

    payload = assemble_route_trace_payload(
        trace,
        route="B_roi_intensity",
        r_self=r_self,
        background_subtraction_on=True,
        interference_overlap_mode="joint_overlap_integrated",
    )
    np.testing.assert_allclose(
        np.asarray(payload["route_detected_intensity"], dtype=float),
        np.array([17.0, 20.5]),
    )


def test_a_hybrid_tracks_overlap_mode_while_b_c_d_do_not() -> None:
    trace = {
        "scattering_only_intensity": np.array([2.0, 4.0]),
        "interference_cross_term_joint": np.array([10.0, 20.0]),
        "interference_cross_term_collapsed": np.array([1.0, 3.0]),
        "I_baseline_trace": np.array([0.0, 0.0]),
    }
    r_self = 5.0

    np.testing.assert_allclose(
        assemble_route_signal(
            trace,
            "A_hybrid",
            r_self,
            interference_overlap_mode="joint_overlap_integrated",
        ),
        np.array([12.0, 24.0]),
    )
    np.testing.assert_allclose(
        assemble_route_signal(
            trace,
            "A_hybrid",
            r_self,
            interference_overlap_mode="collapsed_then_multiplied",
        ),
        np.array([3.0, 7.0]),
    )
    for route_id in ("B_roi_intensity", "C_collapsed_coherent", "D_cross_only"):
        np.testing.assert_allclose(
            assemble_route_signal(
                trace,
                route_id,
                r_self,
                interference_overlap_mode="joint_overlap_integrated",
            ),
            assemble_route_signal(
                trace,
                route_id,
                r_self,
                interference_overlap_mode="collapsed_then_multiplied",
            ),
        )


def test_non_default_detector_route_requires_vectorized_engine_off() -> None:
    from dataclasses import replace

    cfg = replace(
        DEFAULT_SIM_CFG,
        detector_route_id="B_roi_intensity",
        vectorized_event_engine="event_block_v2",
        n_events=1,
    )

    with pytest.raises(ValueError, match="vectorized_event_engine='off'"):
        run_single_case_batch(
            particle=BASELINE_PARTICLE,
            medium=WATER,
            channel=BASELINE_CHANNEL,
            optical=BASELINE_OPTICAL,
            sim_cfg=cfg,
            E_sca_ref=1.0,
            theta_grid_rad=np.linspace(0.0, 0.5, 8),
            retain_event_traces=False,
            stream_summary_only=True,
        )


@pytest.mark.parametrize(
    "interference_overlap_mode",
    ["joint_overlap_integrated", "collapsed_then_multiplied"],
)
def test_a_hybrid_matches_production_signal_trace_for_both_overlap_modes(
    interference_overlap_mode: str,
) -> None:
    from dataclasses import replace

    cfg = replace(
        DEFAULT_SIM_CFG,
        detector_route_id="A_hybrid",
        vectorized_event_engine="off",
        interference_overlap_mode=interference_overlap_mode,
        n_events=1,
        random_seed=123,
        noise_std=0.0,
        shot_noise_scale=0.0,
        post_readout_noise_std=0.0,
    )
    result = run_single_case_batch(
        particle=BASELINE_PARTICLE,
        medium=WATER,
        channel=BASELINE_CHANNEL,
        optical=BASELINE_OPTICAL,
        sim_cfg=cfg,
        E_sca_ref=1.0,
        theta_grid_rad=np.linspace(0.0, 0.75, 64),
        retain_event_traces=True,
        stream_summary_only=False,
    )
    event = result["events"][0]
    joint = np.asarray(event["interference_cross_term_joint"], dtype=float)
    collapsed = np.asarray(event["interference_cross_term_collapsed"], dtype=float)
    assert float(np.max(np.abs(joint - collapsed))) > 0.0
    np.testing.assert_allclose(
        np.asarray(event["signal_trace"], dtype=float),
        np.asarray(event["signal_trace_default_production"], dtype=float),
    )
