from __future__ import annotations

import pytest

from nodi_simulator.design_claim_governance import (
    CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS,
    CLAIM_LEVELS,
    PAPER_ALIGNMENT_TARGETS,
    PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1,
    assert_claim_compatibility,
    assert_paper_alignment_target_metadata,
    require_claim_level,
    require_paper_alignment_target,
)


def test_selected_annulus_claim_and_target_are_registered():
    assert (
        require_claim_level(CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS)
        == CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS
    )
    assert (
        require_paper_alignment_target(PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1)
        == PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1
    )
    assert (
        "within_recorded_edge_norm_bounds"
        in CLAIM_LEVELS[CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS][
            "comparable_dims"
        ]
    )
    assert (1200, 550) in PAPER_ALIGNMENT_TARGETS[
        PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1
    ]["channel_geometries_nm"]


def test_unregistered_selected_annulus_claim_metadata_fails_fast():
    with pytest.raises(ValueError, match="Unknown claim_level"):
        require_claim_level("paper_aligned_typo")

    with pytest.raises(ValueError, match="Unknown paper_alignment_target"):
        require_paper_alignment_target("tsuyama_2022_nodi_geometry_table_s1")


def _valid_target_metadata() -> dict[str, object]:
    return {
        "nodi_lockin_frequency_Hz": 3000.0,
        "threshold_sigma": 10.0,
        "min_peak_width_s": 0.0025,
        "readout_observable_mode": "magnitude",
        "pulse_detection_mode": "positive",
    }


def test_paper_alignment_target_metadata_constraints_accept_nodi_2022_profile():
    assert_paper_alignment_target_metadata(
        PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1,
        _valid_target_metadata(),
    )

    five_sigma = _valid_target_metadata()
    five_sigma["threshold_sigma"] = 5.0
    assert_paper_alignment_target_metadata(
        PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1,
        five_sigma,
    )


def test_paper_alignment_target_metadata_constraints_reject_wrong_readout_lane():
    metadata = _valid_target_metadata()
    metadata["nodi_lockin_frequency_Hz"] = 1200.0
    with pytest.raises(ValueError, match="nodi_lockin_frequency_Hz"):
        assert_paper_alignment_target_metadata(
            PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1,
            metadata,
        )

    metadata = _valid_target_metadata()
    metadata["readout_observable_mode"] = "in_phase"
    with pytest.raises(ValueError, match="readout_observable_mode"):
        assert_paper_alignment_target_metadata(
            PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1,
            metadata,
        )


def _compatible_claim_metadata(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "tsuyama_2022_selected_annulus_joint_fit_v2",
        "analysis_lane": "selected_annulus",
        "claim_level": CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS,
        "paper_alignment_target": PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1,
        "selected_annulus_source": "initial_position_edge_norm_annulus",
        "selected_annulus_edge_norm_min": 0.5,
        "selected_annulus_edge_norm_max": 0.8,
    }
    payload.update(overrides)
    return payload


def test_claim_compatibility_accepts_matching_selected_annulus_metadata():
    left = _compatible_claim_metadata()
    right = _compatible_claim_metadata()
    assert_claim_compatibility(
        left,
        right,
        CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS,
    )


def test_claim_compatibility_rejects_mismatched_selected_annulus_metadata():
    left = _compatible_claim_metadata()
    right = _compatible_claim_metadata(selected_annulus_edge_norm_min=0.4)
    with pytest.raises(ValueError, match="selected_annulus_edge_norm_min"):
        assert_claim_compatibility(
            left,
            right,
            CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS,
        )

    right = _compatible_claim_metadata(selected_annulus_source="different_source")
    with pytest.raises(ValueError, match="selected_annulus_source"):
        assert_claim_compatibility(
            left,
            right,
            CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS,
        )
