from __future__ import annotations

import json
import math
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from tools.audits import tsuyama_detection_rate_calibration as calib
from tools.audits import tsuyama_detection_rule_sensitivity as rule_sens
from tools.audits import tsuyama_gold_aligned_detection_lane as lane
from nodi_simulator.data_objects import Particle
from nodi_simulator.materials import get_n_complex
from nodi_simulator.parameter_sweep import summarize_batch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOL = PROJECT_ROOT / "tools" / "tsuyama_gold_aligned_detection_lane.py"


def test_argparse_help_and_manifest_dry_run_smoke():
    help_result = subprocess.run(
        [sys.executable, str(TOOL), "--help"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "sweep-gold" in help_result.stdout
    assert "sweep-blank" in help_result.stdout

    manifest_result = subprocess.run(
        [sys.executable, str(TOOL), "build-manifest", "--dry-run"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    manifest = json.loads(manifest_result.stdout)
    assert manifest["schema"] == "tsuyama_gold_aligned_detection_lane_manifest_v1"
    assert manifest["scenario_count"] == len(lane.SCENARIO_ORDER)
    assert manifest["case_count"] == 20
    assert len(manifest["records"]) == len(lane.SCENARIO_ORDER) * 20


def test_scenario_builder_keeps_allowed_modes_and_roles():
    for scenario_id in lane.SCENARIO_ORDER:
        cfg = lane.build_scenario_cfg(scenario_id)
        assert cfg.readout_observable_mode in {"in_phase", "magnitude"}
        assert cfg.pulse_detection_mode in {"positive", "absolute"}
        assert cfg.flow_profile_model in {"plug", "parabolic_rect", "rect_series"}
        assert cfg.diffusion_hindrance_model in {
            "none",
            "near_wall_surrogate",
            "anisotropic_tensor_surrogate",
        }
        if lane.SCENARIO_KIND[scenario_id] == "nodi_single":
            assert cfg.detection_decision_mode == "single_channel"
        else:
            assert cfg.detection_decision_mode == "paired_channel"
        assert cfg.pulse_width_measure_mode == "duration_above_threshold"


def test_explicit_cases_are_not_cross_product_and_control_is_labeled():
    cases = lane.all_case_triples()
    assert len(cases) == 20
    assert len(set(cases)) == 20
    assert lane.WEAK_REFERENCE_CONTROL in cases
    assert lane.case_role(lane.WEAK_REFERENCE_CONTROL) == "weak_reference_control"
    assert lane.case_role((660, 1200, 550)) == "tsuyama_2022_nodi_paper_geometry"
    assert lane.case_role((488, 800, 710)) == "tsuyama_2020_pod_geometry_bridge"


def test_particle_material_labels_include_tsuyama_silver():
    silver = Particle(
        name="silver_40nm",
        radius_m=20e-9,
        n_real=0.05,
        n_imag=3.0,
        material_key="silver",
        use_material_model=True,
    )
    assert lane._particle_material_from_name("silver_40nm", silver) == "silver"


def test_tsuyama_2022_table_s1_particle_uses_fixed_paper_index():
    particle = lane.make_tsuyama_2022_table_s1_particle("silver", 40, 660)
    assert particle.name == "silver_40nm_tsuyama2022s1_660nm"
    assert particle.material_key == "silver"
    assert particle.use_material_model is False
    assert particle.n_complex_at(660e-9) == complex(0.05, 4.483)


def test_tsuyama_gold_table_s1_matches_material_db_johnson_christy_points():
    source_wavelength_by_nominal_nm = {
        488: 495.9e-9,
        532: 520.9e-9,
        660: 659.5e-9,
    }

    for nominal_nm, source_wavelength_m in source_wavelength_by_nominal_nm.items():
        n_real, n_imag = lane.TSUYAMA_2022_TABLE_S1_NK["gold"][nominal_nm]
        n_complex = get_n_complex("gold", source_wavelength_m)
        assert n_complex.real == pytest.approx(n_real)
        assert n_complex.imag == pytest.approx(n_imag)


def test_explicit_sweep_uses_case_geometry_for_baseline_channel(monkeypatch):
    calls = []

    def fake_run_parameter_sweep(**kwargs):
        width_m = float(kwargs["width_list_m"][0])
        depth_m = float(kwargs["depth_list_m"][0])
        baseline_channel = kwargs["baseline_channel"]
        calls.append(
            (
                width_m,
                depth_m,
                float(baseline_channel.width_m),
                float(baseline_channel.depth_m),
            )
        )
        return []

    monkeypatch.setattr(lane, "run_parameter_sweep", fake_run_parameter_sweep)

    out = lane.run_explicit_sweep(
        scenario_config_id="nodi_2022_5sigma_single_sensitivity",
        particles=[],
        n_events=1,
        random_seed=123,
        n_workers=1,
        claim_level="test",
    )

    assert out.empty
    assert len(calls) == len(lane.all_case_triples())
    for width_m, depth_m, baseline_width_m, baseline_depth_m in calls:
        assert baseline_width_m == width_m
        assert baseline_depth_m == depth_m


def test_synthetic_blank_is_deterministic_and_higher_threshold_is_not_worse():
    base = lane.build_scenario_cfg("nodi_2022_5sigma_single_sensitivity")
    base = replace(base, total_time_s=0.02, min_peak_width_s=1e-3, min_peak_interval_s=5e-3)
    cfg3 = replace(base, threshold_sigma=3.0)
    cfg5 = replace(base, threshold_sigma=5.0)

    a = lane.run_synthetic_blank(
        cfg5,
        n_blank_traces=40,
        random_seed=123,
        scenario_kind="nodi_single",
    )
    b = lane.run_synthetic_blank(
        cfg5,
        n_blank_traces=40,
        random_seed=123,
        scenario_kind="nodi_single",
    )
    c = lane.run_synthetic_blank(
        cfg3,
        n_blank_traces=40,
        random_seed=123,
        scenario_kind="nodi_single",
    )
    assert a == b
    assert a["blank_false_positive_wilson_ub_per_trace"] >= 0.0
    assert a["n_blank_detected"] <= c["n_blank_detected"]


def _gold_fixture_rows(scenario_id: str, *, reference_band: str = "ok") -> pd.DataFrame:
    rows = []
    for diameter in lane.GOLD_DIAMETERS_NM:
        rows.append(
            {
                "scenario_config_id": scenario_id,
                "scenario_kind": lane.SCENARIO_KIND[scenario_id],
                "wavelength_nm": 488,
                "width_nm": 800,
                "depth_nm": 700,
                "particle_diameter_nm": diameter,
                "reference_operating_band": reference_band,
                "rho_physical_envelope_status": "within_envelope",
                "na_cutoff_active": False,
            }
        )
    return pd.DataFrame(rows)


def test_select_feasible_blocks_gold_only_paired_only_and_weak_reference():
    single = _gold_fixture_rows("nodi_2022_5sigma_single_sensitivity")
    paired = _gold_fixture_rows("paired_2024_5sigma_diag")
    weak = _gold_fixture_rows(
        "ev_nodi_5sigma_single_current_design",
        reference_band="reference_too_weak",
    )
    gold = pd.concat([single, paired, weak], ignore_index=True)
    gold_status = {
        "nodi_2022_5sigma_single_sensitivity": {
            "gold_anchor_pass": True,
            "gold_anchor_primary_blocker": "pass",
        },
        "paired_2024_5sigma_diag": {
            "gold_anchor_pass": True,
            "gold_anchor_primary_blocker": "pass",
        },
        "ev_nodi_5sigma_single_current_design": {
            "gold_anchor_pass": True,
            "gold_anchor_primary_blocker": "pass",
        },
    }
    blank_status = {
        "nodi_2022_5sigma_single_sensitivity": {
            "blank_gate_pass": False,
            "blank_gate_primary_blocker": "blank_fpr_wilson_ub",
        },
        "paired_2024_5sigma_diag": {
            "blank_gate_pass": True,
            "blank_gate_primary_blocker": "pass",
        },
        "ev_nodi_5sigma_single_current_design": {
            "blank_gate_pass": True,
            "blank_gate_primary_blocker": "pass",
        },
    }
    rows = lane.compute_feasible_rows(gold, gold_status, blank_status)
    by_scenario = {row["scenario_config_id"]: row for row in rows}

    assert not by_scenario["nodi_2022_5sigma_single_sensitivity"][
        "scenario_config_feasible"
    ]
    assert not by_scenario["paired_2024_5sigma_diag"]["scenario_config_feasible"]
    assert by_scenario["paired_2024_5sigma_diag"]["paired_diag_pass"]
    assert by_scenario["ev_nodi_5sigma_single_current_design"][
        "scenario_config_feasible"
    ]
    assert not by_scenario["ev_nodi_5sigma_single_current_design"]["case_feasible"]


def test_full_grid_decision_requires_feasible_artifact_and_no_runner(tmp_path):
    decision = lane.determine_full_grid_decision(tmp_path)
    assert decision["full_grid_decision"] == "no_go_missing_feasible_scenarios"

    parser = lane.build_parser()
    subparsers = next(
        action for action in parser._actions if getattr(action, "choices", None)
    )
    assert "full-grid" not in subparsers.choices


def test_detection_rate_calibration_catalog_only_changes_estimated_fields():
    assert "baseline_current_estimates" in calib.candidate_by_id()
    assert "low_noise_stack_uniform_accessible" in calib.candidate_by_id()
    assert "logger_0p5ms_blank_edge_low_noise_stack_fluxmix_0p25" in calib.candidate_by_id()
    assert "logger_0p5ms_conservative_low_noise_stack_uniform_accessible" in calib.candidate_by_id()
    assert "colored_ar1_0p0005_tau_1ms_low_noise_stack_uniform_accessible" in calib.candidate_by_id()
    assert "velocity_0p15mmps_low_noise_stack_fluxmix_0p05" in calib.candidate_by_id()
    assert "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_flowplug" in calib.candidate_by_id()
    assert (
        "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_refspace_0p375"
        in calib.candidate_by_id()
    )
    protected = set(calib.PROTECTED_PAPER_CRITERIA)
    allowed = set(calib.ESTIMATED_PARAMETER_FIELDS)
    for candidate in calib.candidate_catalog():
        changed = set(candidate.overrides)
        assert changed <= allowed
        assert changed.isdisjoint(protected)


def test_detection_rate_calibration_candidate_builder_accepts_sampling_mode():
    candidate = calib.candidate_by_id()["logger_0p5ms_blank_edge_low_noise_stack_fluxmix_0p25"]
    cfg = calib.build_candidate_cfg(candidate, n_events=123, random_seed=456)

    assert cfg.n_events == 123
    assert cfg.random_seed == 456
    assert cfg.initial_position_distribution_mode == "flux_uniform_mixture_surrogate"
    assert cfg.initial_position_flux_weighted_mixture_fraction == 0.25
    assert cfg.pulse_extraction_sampling_interval_s == 5.0e-4
    assert cfg.threshold_calibration_source == "blank_trace_empirical"
    assert cfg.pulse_duration_estimation_policy == "interpolated_threshold_crossing"
    assert cfg.pulse_width_measure_mode == "duration_above_threshold"
    assert cfg.threshold_sigma == 10.0

    conservative = calib.build_candidate_cfg(
        calib.candidate_by_id()["logger_0p5ms_conservative_low_noise_stack_uniform_accessible"],
        n_events=123,
        random_seed=456,
    )
    assert conservative.pulse_duration_estimation_policy == "sample_span_conservative"

    flow_profile = calib.build_candidate_cfg(
        calib.candidate_by_id()["velocity_0p15mmps_low_noise_stack_fluxmix_0p10_flowplug"],
        n_events=123,
        random_seed=456,
    )
    assert flow_profile.flow_profile_model == "plug"


def test_detection_rule_sensitivity_catalog_changes_only_rule_fields_and_base_estimates():
    candidates = rule_sens.detection_rule_candidate_catalog()
    assert len(candidates) == 48
    anchor = rule_sens.candidate_by_id()[
        "rule_sigma_10_width_2p5ms__velocity_0p15mmps_low_noise_stack_fluxmix_0p10_noise_0p0065"
    ]
    assert anchor.overrides["threshold_sigma"] == 10.0
    assert anchor.overrides["min_peak_width_s"] == 2.5e-3
    assert anchor.overrides["initial_position_distribution_mode"] == (
        "flux_uniform_mixture_surrogate"
    )

    allowed = set(rule_sens.BASE_ESTIMATE_OVERRIDES) | set(rule_sens.RULE_FIELDS)
    for candidate in candidates:
        assert set(candidate.overrides) == allowed


def test_summary_reports_selected_detector_mode_conditioned_rates():
    def event(
        *,
        detected: bool,
        edge_norm: float,
        event_margin_z: float,
    ) -> dict:
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
            "event_max_margin_z": event_margin_z,
            "background_max_margin_z": -1.0,
        }

    summary = summarize_batch(
        [
            event(detected=True, edge_norm=0.5, event_margin_z=2.0),
            event(detected=True, edge_norm=0.9, event_margin_z=2.0),
            event(detected=False, edge_norm=0.6, event_margin_z=0.5),
            event(detected=False, edge_norm=0.2, event_margin_z=-1.0),
        ]
    )

    assert summary["detection_rate"] == 0.5
    assert summary["all_crossing_detection_rate"] == 0.5
    assert summary["selected_detector_mode_candidate_n_events"] == 3
    assert summary["selected_detector_mode_candidate_n_detected"] == 2
    assert summary["selected_detector_mode_candidate_detection_rate"] == 2 / 3
    assert summary["selected_detector_mode_annulus_n_events"] == 2
    assert summary["selected_detector_mode_annulus_n_detected"] == 1
    assert summary["selected_detector_mode_annulus_detection_rate"] == 0.5


def test_flatten_sweep_results_preserves_empty_selected_annulus_nan_rate():
    cfg = lane.build_scenario_cfg("nodi_2022_10sigma_single", n_events=3)
    df = lane.flatten_sweep_results(
        [
            {
                "summary": {
                    "n_events": 3,
                    "n_detected": 1,
                    "detection_rate": 1 / 3,
                    "detection_rate_wilson_lb": 0.0,
                    "all_crossing_detection_rate": 1 / 3,
                    "all_crossing_detection_rate_wilson_lb": 0.0,
                    "selected_detector_mode_annulus_edge_norm_min": 0.5,
                    "selected_detector_mode_annulus_edge_norm_max": 0.8,
                    "selected_detector_mode_annulus_n_events": 0,
                    "selected_detector_mode_annulus_fraction": 0.0,
                    "selected_detector_mode_annulus_detection_rate": float("nan"),
                    "selected_detector_mode_annulus_detection_rate_wilson_lb": (
                        float("nan")
                    ),
                },
                "reference": {},
                "intrinsic": {},
                "particle_name": "gold_20nm",
                "particle": Particle(
                    name="gold_20nm",
                    radius_m=10e-9,
                    n_real=0.5,
                    n_imag=2.0,
                    material_key="gold",
                ),
                "wavelength_m": 488e-9,
                "width_m": 800e-9,
                "depth_m": 550e-9,
            }
        ],
        scenario_config_id="nodi_2022_10sigma_single",
        cfg=cfg,
        n_events=3,
        random_seed=1,
        claim_level="test",
    )

    assert df["selected_detector_mode_annulus_n_events"].iloc[0] == 0
    assert math.isnan(df["selected_detector_mode_annulus_detection_rate"].iloc[0])
    assert math.isnan(
        df["selected_detector_mode_annulus_detection_rate_wilson_lb"].iloc[0]
    )


def test_detection_rate_calibration_score_prefers_target_band_candidate():
    candidate = calib.candidate_by_id()["baseline_current_estimates"]

    def fake_rows(rates: dict[int, float]) -> pd.DataFrame:
        rows = []
        for diameter_nm, rate in rates.items():
            rows.append(
                {
                    "scenario_config_id": calib.CALIBRATION_SCENARIO_ID,
                    "particle_diameter_nm": diameter_nm,
                    "wavelength_nm": 532,
                    "width_nm": 800,
                    "depth_nm": 550,
                    "detection_rate": rate,
                    "selected_detector_mode_candidate_detection_rate": min(1.0, rate + 0.10),
                    "selected_detector_mode_candidate_fraction": 0.80,
                    "selected_detector_mode_annulus_detection_rate": min(1.0, rate + 0.20),
                    "selected_detector_mode_annulus_fraction": 0.40,
                    "n_detected": int(rate * 1000),
                    "mean_peak_height": float(diameter_nm),
                    "mean_local_snr": float(diameter_nm),
                    "threshold_sigma": 10.0,
                    "reference_operating_band": "ok",
                    "rho_physical_envelope_status": "within_envelope",
                    "na_cutoff_active": False,
                }
            )
        return pd.DataFrame(rows)

    inside = calib.summarize_candidate(
        fake_rows({20: 0.15, 30: 0.42, 40: 0.60, 60: 0.70}),
        candidate,
        n_events=1000,
        random_seed=42,
        n_workers=1,
    )
    outside = calib.summarize_candidate(
        fake_rows({20: 0.01, 30: 0.10, 40: 0.20, 60: 0.25}),
        candidate,
        n_events=1000,
        random_seed=42,
        n_workers=1,
    )

    assert inside["target_fit_status"] == "within_all_bands"
    assert inside["calibration_score"] < outside["calibration_score"]
    assert abs(inside["au60_median_selected_detector_mode_candidate_detection_rate"] - 0.80) < 1e-12
    assert inside["au60_median_selected_detector_mode_candidate_fraction"] == 0.80
    assert abs(inside["au60_median_selected_detector_mode_annulus_detection_rate"] - 0.90) < 1e-12
    assert inside["au60_median_selected_detector_mode_annulus_fraction"] == 0.40


def test_ev_rows_export_selected_detector_mode_diagnostics_keeps_primary_rank_basis():
    rows = []
    for diameter_nm in lane.EV_DIAMETERS_NM:
        for member in range(4):
            rows.append(
                {
                    "scenario_config_id": "ev_nodi_5sigma_single_current_design",
                    "particle_name": f"exosome_biomimetic_{diameter_nm}nm_member{member}",
                    "particle_diameter_nm": diameter_nm,
                    "wavelength_nm": 532,
                    "width_nm": 600,
                    "depth_nm": 1500,
                    "detection_rate": float(diameter_nm) / 1000.0,
                    "stable_detection_rate": 0.20,
                    "all_crossing_detection_rate": float(diameter_nm) / 1000.0,
                    "selected_detector_mode_candidate_fraction": 0.80,
                    "selected_detector_mode_candidate_detection_rate": (
                        float(diameter_nm) / 1000.0 + 0.05
                    ),
                    "selected_detector_mode_annulus_edge_norm_min": 0.50,
                    "selected_detector_mode_annulus_edge_norm_max": 0.80,
                    "selected_detector_mode_annulus_fraction": 0.40,
                    "selected_detector_mode_annulus_detection_rate": (
                        float(diameter_nm) / 1000.0 + 0.10
                    ),
                    "reference_operating_band": "ok",
                    "engineering_gate_passed": True,
                }
            )

    ev = lane._ev_rows_from_raw(pd.DataFrame(rows))
    equal_current = ev[ev["EV_size_distribution_profile"] == "equal_current"]

    assert "selected_detector_mode_annulus_detection_rate" in ev.columns
    assert "weighted_selected_detector_mode_annulus_detection_rate" in ev.columns
    assert equal_current["ranking_within_scenario"].nunique() == 1
    assert equal_current["ranking_within_scenario"].iloc[0] == 1
    assert abs(
        equal_current["weighted_selected_detector_mode_annulus_detection_rate"].iloc[0] - 0.21
    ) < 1e-12
    assert abs(equal_current["weighted_selected_detector_mode_annulus_fraction"].iloc[0] - 0.40) < 1e-12
