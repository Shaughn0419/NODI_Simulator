from __future__ import annotations

import math
from dataclasses import replace
from typing import cast

from dashboard.config import medium_for_particle, particle_from_name
from tools.audits.run_report148_stage1_ab_minimal import (
    RAW_REFERENCE_NORMALIZATION_MODE,
    RAW_SCATTERING_NORMALIZATION_MODE,
    _build_route_cfg,
    _build_v2_view_payload_overrides,
    _detector_route_flip_flag_404_660,
    _event_accounting,
    _run_scope_statement,
    _seed_coverage_rows,
    default_route_panel,
)
import pandas as pd
from tools.audits import tsuyama_gold_aligned_detection_lane as lane
from tools.lens_b_ev_gold_fullgrid_runner import _fixed_660_e_sca_ref, build_frozen_b_cfg


def test_v2_view_payload_overrides_expose_raw_norm_provenance_and_finite_scales() -> None:
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
            ("V1_gauge_locked", "V2_raw_angular"),
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
