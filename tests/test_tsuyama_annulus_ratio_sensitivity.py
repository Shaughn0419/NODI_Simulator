from __future__ import annotations

import json

import pandas as pd
import pytest

from tools import tsuyama_annulus_ratio_sensitivity as sensitivity
from tools import tsuyama_selected_annulus_joint_fit as joint
from nodi_simulator.design_claim_governance import (
    CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS,
    PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1,
)


def test_candidate_with_annulus_window_adds_traceable_cfg_overrides():
    base = joint.JointFitCandidate(
        candidate_id="baseline_current_estimates",
        base_candidate_id="baseline_current_estimates",
        cfg_overrides={"threshold_sigma": 5.0},
        rationale="fixture",
    )

    candidate = sensitivity.candidate_with_annulus_window(
        base,
        inner=0.4,
        outer=0.8,
    )

    assert candidate.candidate_id.endswith("__annulus_0p4_0p8")
    assert candidate.cfg_overrides["threshold_sigma"] == pytest.approx(5.0)
    assert candidate.cfg_overrides["selected_annulus_edge_norm_min"] == pytest.approx(
        0.4
    )
    assert candidate.cfg_overrides["selected_annulus_edge_norm_max"] == pytest.approx(
        0.8
    )


def test_run_ratio_sensitivity_writes_meta_and_decision(monkeypatch, tmp_path):
    def fake_sweep(candidate, **kwargs):
        return pd.DataFrame(
            [
                {
                    "candidate_id": candidate.candidate_id,
                    "nodi_lockin_frequency_Hz": 3000.0,
                    "threshold_sigma": 10.0,
                    "min_peak_width_s": 0.0025,
                    "readout_observable_mode": "magnitude",
                    "pulse_detection_mode": "positive",
                    "selected_detector_mode_annulus_detection_rate": 0.5,
                    "selected_detector_mode_annulus_fraction": 0.4,
                }
            ]
        )

    def fake_summary(rows, candidate, **kwargs):
        edge_min = float(candidate.cfg_overrides["selected_annulus_edge_norm_min"])
        return {
            "candidate_id": candidate.candidate_id,
            "joint_fit_score": 1.0 - edge_min,
            "paper_fit_status": "candidate_joint_fit_plausible",
        }

    monkeypatch.setattr(sensitivity.joint, "run_joint_candidate_sweep", fake_sweep)
    monkeypatch.setattr(sensitivity.joint, "summarize_joint_candidate", fake_summary)

    _, summary, meta = sensitivity.run_ratio_sensitivity(
        base_candidate_ids=["baseline_current_estimates"],
        variant_ids=["paper_10sigma"],
        annulus_windows=((0.5, 0.8), (0.4, 0.8)),
        n_events=10,
        random_seeds=[42, 43],
        n_workers=1,
        scenario_id="nodi_2022_10sigma_single",
        output_dir=tmp_path,
    )

    assert len(summary) == 4
    assert meta["schema"] == sensitivity.TARGET_SCHEMA_ID
    assert meta["claim_level"] == CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS
    assert (
        meta["paper_alignment_target"]
        == PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1
    )
    assert meta["joint_fit_score_direction"] == "lower_is_better"
    assert meta["gold_diameters_nm"] == list(joint.GOLD_DIAMETERS_NM)
    assert meta["scenario_config_id"] == "nodi_2022_10sigma_single"
    assert meta["random_seeds"] == [42, 43]
    assert (
        meta["suggested_canonical_by_mean_joint_fit_score"]["annulus_window_id"]
        == "0p5_0p8"
    )
    saved_meta = json.loads((tmp_path / sensitivity.META_FILENAME).read_text())
    assert saved_meta["n_events"] == 10
    assert (tmp_path / sensitivity.AGGREGATE_FILENAME).exists()
    decision = (tmp_path / sensitivity.DECISION_FILENAME).read_text()
    assert "Lower is better" in decision
    assert "loss-style sum of penalties" in decision
    assert "nodi_2022_10sigma_single" in decision
