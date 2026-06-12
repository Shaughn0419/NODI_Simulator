from __future__ import annotations

from dataclasses import replace
import math
from pathlib import Path
from typing import cast

from dashboard.config import medium_for_particle, particle_from_name
from tools.audits.run_report148_stage1_ab_minimal import (
    RAW_REFERENCE_NORMALIZATION_MODE,
    RAW_SCATTERING_NORMALIZATION_MODE,
    STAGE1_RANK_SCORE_COLUMN,
    STAGE1_RANK_SCORE_DEFINITION,
    V2_GAUGE_MODE,
    _build_route_cfg,
    _build_v2_view_payload_overrides,
    _detector_route_flip_flag_404_660,
    _event_accounting,
    _rank_routes_for_group,
    _run_scope_statement,
    _seed_coverage_rows,
    default_route_panel,
)
import pandas as pd
from tools.audits import tsuyama_gold_aligned_detection_lane as lane
from tools.lens_b_ev_gold_fullgrid_runner import _fixed_660_e_sca_ref, build_frozen_b_cfg


def test_v2_view_payload_overrides_expose_raw_norm_provenance_and_finite_scales() -> None:
    assert V2_GAUGE_MODE == "V2_raw_angular_explicit_norm_sample"
    route = default_route_panel()[0]
    particle = particle_from_name("exosome_biomimetic_corona_nominal_100nm")
    medium = medium_for_particle(particle)
    channel = lane.case_baseline_channel(route.width_nm, route.depth_nm)
    cfg, optical_template = _build_route_cfg(
        n_events=10,
        seed=11,
        detector_route_id="A_hybrid",
        detector_forward_model="joint_overlap_coherent_surrogate",
        normalization_lane="fixed_660_gold",
    )
    optical = replace(optical_template, wavelength_m=float(route.wavelength_nm) * 1e-9)
    _, optical_template_raw = build_frozen_b_cfg(10, 11)
    e_sca_ref = _fixed_660_e_sca_ref(
        width_nm=route.width_nm,
        depth_nm=route.depth_nm,
        cfg=cfg,
        optical_template=optical_template_raw,
    )

    overrides = _build_v2_view_payload_overrides(
        particle=particle,
        medium=medium,
        channel=channel,
        optical=optical,
        cfg=cfg,
        e_sca_ref=e_sca_ref,
    )

    reference = overrides["reference"]
    intrinsic = overrides["intrinsic"]
    assert reference["raw_reference_normalization_mode"] == RAW_REFERENCE_NORMALIZATION_MODE
    assert reference["raw_scattering_normalization_mode"] == RAW_SCATTERING_NORMALIZATION_MODE
    assert intrinsic["raw_reference_normalization_mode"] == RAW_REFERENCE_NORMALIZATION_MODE
    assert intrinsic["raw_scattering_normalization_mode"] == RAW_SCATTERING_NORMALIZATION_MODE
    assert float(cast(float, reference["n_ref_raw"])) > 0.0
    assert float(cast(float, reference["n_sca_raw"])) > 0.0
    assert float(cast(float, intrinsic["v2_r_self"])) > 0.0
    assert math.isfinite(float(cast(float, reference["self_sca_detector_integrated"])))
    assert math.isfinite(float(cast(float, reference["cross_term_detector_integrated"])))
    assert abs(complex(cast(complex, reference["E_ref_complex"]))) > 0.0
    assert abs(complex(cast(complex, intrinsic["E_sca_unit_normalized_complex"]))) > 0.0


def test_detector_route_flip_flag_is_false_when_views_select_same_winner() -> None:
    assert not _detector_route_flip_flag_404_660(660, 660)


def test_detector_route_flip_flag_is_true_when_views_select_different_winners() -> None:
    assert _detector_route_flip_flag_404_660(404, 660)


def test_detector_route_flip_flag_matches_real_a_and_c_shapes() -> None:
    assert _detector_route_flip_flag_404_660(404, 660)  # A: fixed 404, per-wavelength 660
    assert not _detector_route_flip_flag_404_660(660, 660)  # C: both views 660


def test_run_scope_statement_reports_only_requested_cells() -> None:
    assert (
        _run_scope_statement(
            ("A_hybrid", "B_roi_intensity"),
            ("V1_gauge_locked", V2_GAUGE_MODE),
        )
        == "A/B: V1+V2; R2 only"
    )
    assert (
        _run_scope_statement(
            ("C_collapsed_coherent", "D_cross_only"),
            ("V1_gauge_locked",),
        )
        == "C/D: V1; R2 only"
    )


def test_event_accounting_halves_shared_dual_view_case_rows() -> None:
    accounting = _event_accounting(
        case_row_count=1080,
        n_events=2000,
        normalization_view_count=2,
    )
    assert accounting["case_row_events"] == 2_160_000
    assert accounting["distinct_physical_events"] == 1_080_000


def test_seed_coverage_rows_exposes_complete_and_missing_cells() -> None:
    frame = pd.DataFrame(
        [
            {
                "detector_route_id": "A_hybrid",
                "readout_policy": "R2_absolute",
                "gauge_mode": "V1_gauge_locked",
                "normalization_view": "fixed_660_gold",
                "seed": seed,
            }
            for seed in (11, 22, 33)
        ]
        + [
            {
                "detector_route_id": "C_collapsed_coherent",
                "readout_policy": "R2_absolute",
                "gauge_mode": "V1_gauge_locked",
                "normalization_view": "fixed_660_gold",
                "seed": seed,
            }
            for seed in (11, 22)
        ]
    )
    coverage = _seed_coverage_rows(frame).set_index("detector_route_id")
    assert coverage.loc["A_hybrid", "seed_coverage_status"] == "complete"
    assert coverage.loc["C_collapsed_coherent", "seed_coverage_status"] == "incomplete"
    assert coverage.loc["C_collapsed_coherent", "missing_seeds"] == "33"


def test_stage1_ranking_uses_explicit_tiebreak_margin_not_final_engineering_score() -> None:
    frame = pd.DataFrame(
        [
            {
                "particle_family": "EV_sEV",
                "particle_diameter_nm": 80,
                "wavelength_nm": 404,
                "width_nm": 500,
                "depth_nm": 700,
                "route_family_id": "lambda404_w500_middeep",
                "route_family_note": "404 family",
                "detection_rate": 0.4,
                "all_crossing_detection_rate": 0.4,
                "stable_detection_rate": 0.4,
                "selected_detector_mode_annulus_detection_rate": 0.8,
                "selected_detector_mode_annulus_fraction": 0.5,
                "selected_detector_mode_annulus_contribution": 0.5,
                "selected_detector_mode_annulus_uplift": 1.0,
                "reference_operating_band": "electronics_noise_limited_useful",
                "strict_ok": True,
                STAGE1_RANK_SCORE_COLUMN: 2.0,
            },
            {
                "particle_family": "EV_sEV",
                "particle_diameter_nm": 80,
                "wavelength_nm": 660,
                "width_nm": 800,
                "depth_nm": 900,
                "route_family_id": "lambda660_w800_middeep",
                "route_family_note": "660 family",
                "detection_rate": 0.3,
                "all_crossing_detection_rate": 0.3,
                "stable_detection_rate": 0.3,
                "selected_detector_mode_annulus_detection_rate": 0.7,
                "selected_detector_mode_annulus_fraction": 0.5,
                "selected_detector_mode_annulus_contribution": 0.5,
                "selected_detector_mode_annulus_uplift": 1.0,
                "reference_operating_band": "electronics_noise_limited_useful",
                "strict_ok": True,
                STAGE1_RANK_SCORE_COLUMN: 1.0,
            },
        ]
    )

    ranked = _rank_routes_for_group(frame)

    assert f"sharp_msc_sev_empirical_weighted_{STAGE1_RANK_SCORE_COLUMN}" in ranked.columns
    assert "sharp_msc_sev_empirical_weighted_final" not in ranked.columns
    assert ranked.iloc[0]["route_family_id"] == "lambda404_w500_middeep"
    assert STAGE1_RANK_SCORE_DEFINITION == "selected_detection, stable_rate, mean_peak_margin_z"


def test_report148_audit_scripts_do_not_emit_bare_winner_or_final_score_fields() -> None:
    project_root = Path(__file__).resolve().parents[1]
    for relpath in (
        "tools/audits/run_report148_stage1_ab_minimal.py",
        "tools/audits/run_report148_t3_noise_axis.py",
        "tools/audits/run_report148_t4_ac_ri.py",
    ):
        text = (project_root / relpath).read_text(encoding="utf-8")
        assert '"winner_wavelength"' not in text
        assert '"final_engineering_score"' not in text
        assert '"V2_raw_angular"' not in text
    stage1_text = (
        project_root / "tools/audits/run_report148_stage1_ab_minimal.py"
    ).read_text(encoding="utf-8")
    assert 'readout_model="raw"' in stage1_text
    assert '"signed_polarity_fixture"' in stage1_text
    assert "raw_in_phase_positive_truth" in stage1_text
    assert "lockin_surrogate_absolute_pipeline_consistency_diagnostic" in stage1_text
