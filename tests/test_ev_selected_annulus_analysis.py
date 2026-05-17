from __future__ import annotations

import json

import pandas as pd

from tools import analyze_lens_b_ev_gold_fullgrid as fullgrid
from tools.audits import ev_size_weighted_route_analysis as route_analysis
from tools.audits import tsuyama_gold_aligned_detection_lane as lane


def test_ev_wavelength_rule_subsets_ignore_non_numeric_rows():
    routes = pd.DataFrame(
        [
            {"wavelength_nm": 404, "width_nm": 600, "depth_nm": 1300},
            {"wavelength_nm": "660", "width_nm": 700, "depth_nm": 1400},
            {"wavelength_nm": "not_numeric", "width_nm": 800, "depth_nm": 1500},
            {"wavelength_nm": None, "width_nm": 850, "depth_nm": 1550},
            {"wavelength_nm": 532, "width_nm": 900, "depth_nm": 1600},
        ]
    )

    recommendation = route_analysis._recommendation_eligible_routes(routes)
    control = route_analysis._control_only_routes(routes)

    assert set(recommendation["width_nm"]) == {600, 700}
    assert set(control["width_nm"]) == {900}


def test_gold_aligned_wavelength_subset_ignores_non_numeric_rows():
    routes = pd.DataFrame(
        [
            {"wavelength_nm": 404, "width_nm": 600, "depth_nm": 1300},
            {"wavelength_nm": "660", "width_nm": 700, "depth_nm": 1400},
            {"wavelength_nm": "not_numeric", "width_nm": 800, "depth_nm": 1500},
            {"wavelength_nm": None, "width_nm": 850, "depth_nm": 1550},
            {"wavelength_nm": 532, "width_nm": 900, "depth_nm": 1600},
        ]
    )

    recommendation = lane._route_subset_by_wavelength(
        routes,
        lane.RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM,
    )
    control = lane._route_subset_by_wavelength(
        routes,
        lane.CONTROL_ONLY_WAVELENGTHS_NM,
    )

    assert set(recommendation["width_nm"]) == {600, 700}
    assert set(control["width_nm"]) == {900}


def test_fullgrid_wavelength_roles_ignore_non_numeric_rows():
    routes = pd.DataFrame(
        [
            {"wavelength_nm": 404},
            {"wavelength_nm": "660"},
            {"wavelength_nm": "not_numeric"},
            {"wavelength_nm": None},
            {"wavelength_nm": 532},
        ]
    )

    out = fullgrid._with_wavelength_role(routes)

    assert out["wavelength_role"].tolist() == [
        "recommendation_eligible_404_660",
        "recommendation_eligible_404_660",
        "unexpected_wavelength",
        "unexpected_wavelength",
        "control_only_488_532",
    ]


def test_ev_size_weighted_route_analysis_emits_selected_annulus_lens():
    rows = []
    for route, base_rate, selected_rate in (
        ((488, 600, 1500), 0.50, 0.55),
        ((532, 800, 700), 0.40, 0.95),
    ):
        wavelength_nm, width_nm, depth_nm = route
        rows.extend(
            {
                "particle_material": "exosome",
                "particle_diameter_nm": diameter_nm,
                "wavelength_nm": wavelength_nm,
                "width_nm": width_nm,
                "depth_nm": depth_nm,
                "detection_rate": base_rate,
                "all_crossing_detection_rate": base_rate,
                "selected_detector_mode_annulus_detection_rate": selected_rate,
                "selected_detector_mode_annulus_fraction": 0.40,
                "stable_detection_rate": base_rate,
                "final_engineering_score": base_rate,
                "engineering_gate_passed": base_rate > 0.45,
                "na_cutoff_active": False,
                "rho_physical_envelope_status": "within_envelope",
            }
            for diameter_nm in (60, 80, 100)
        )

    df = pd.DataFrame(rows)
    priors = {"uniform": {60: 1.0, 80: 1.0, 100: 1.0}}
    routes = route_analysis.aggregate_routes(df, priors)
    comparison = route_analysis.build_selected_annulus_ranking_comparison(
        routes,
        priors,
        top_n=1,
    )

    assert routes["selected_annulus_lens_available"].all()
    assert "uniform_weighted_selected_annulus_detection" in routes.columns
    assert comparison["selected_annulus_top_routes_changed"].iloc[0]
    assert comparison["selected_annulus_top1_route_changed"].iloc[0]
    assert comparison["selected_annulus_top_routes_order_changed"].iloc[0]
    selected_top = json.loads(comparison["selected_annulus_top_routes"].iloc[0])
    assert selected_top == [
        {"wavelength_nm": 532, "width_nm": 800, "depth_nm": 700}
    ]
    assert comparison["recommendation_wavelength_rule"].iloc[0] == (
        "recommendation_conclusion_only_404_660__488_532_control_only"
    )
    assert json.loads(
        comparison["selected_annulus_recommendation_top_routes"].iloc[0]
    ) == []
    assert json.loads(comparison["selected_annulus_control_only_top_routes"].iloc[0]) == [
        {"wavelength_nm": 532, "width_nm": 800, "depth_nm": 700}
    ]
    assert comparison["selected_annulus_metric_top1_control_only"].iloc[0]


def test_ev_size_weighted_route_analysis_outputs_selected_contribution_and_warnings():
    df = pd.DataFrame(
        [
            {
                "particle_material": "exosome",
                "particle_diameter_nm": 100,
                "wavelength_nm": 660,
                "width_nm": 800,
                "depth_nm": 1400,
                "reference_operating_band": "electronics_noise_limited_useful",
                "detection_rate": 0.2,
                "all_crossing_detection_rate": 0.2,
                "selected_detector_mode_annulus_detection_rate": 0.4,
                "selected_detector_mode_annulus_fraction": 0.30,
                "stable_detection_rate": 0.2,
                "final_engineering_score": 0.2,
                "engineering_gate_passed": True,
                "na_cutoff_active": False,
                "rho_physical_envelope_status": "within_envelope",
            },
            {
                "particle_material": "exosome",
                "particle_diameter_nm": 120,
                "wavelength_nm": 660,
                "width_nm": 800,
                "depth_nm": 1400,
                "reference_operating_band": "electronics_noise_limited_useful",
                "detection_rate": 0.2,
                "all_crossing_detection_rate": 0.2,
                "selected_detector_mode_annulus_detection_rate": 0.4,
                "selected_detector_mode_annulus_fraction": 0.30,
                "stable_detection_rate": 0.2,
                "final_engineering_score": 0.2,
                "engineering_gate_passed": True,
                "na_cutoff_active": False,
                "rho_physical_envelope_status": "within_envelope",
            },
        ]
    )

    routes = route_analysis.aggregate_routes(
        df,
        {"uniform": {100: 1.0, 120: 1.0}},
    )
    row = routes.iloc[0]

    assert row["reference_operating_band"] == "electronics_noise_limited_useful"
    assert abs(row["raw_mean_selected_annulus_contribution"] - 0.12) < 1e-12
    assert row["raw_mean_selected_annulus_uplift"] == 2.0
    assert abs(row["uniform_weighted_selected_annulus_contribution"] - 0.12) < 1e-12
    assert row["uniform_weighted_selected_annulus_uplift"] == 2.0
    assert row["selected_annulus_fraction_guardrail_status"] == (
        "selected_annulus_fraction_warning_low"
    )
    assert row["selected_annulus_uplift_warning_status"] == (
        "selected_annulus_uplift_warning_high"
    )


def test_ev_size_weighted_route_analysis_splits_prior_weight_across_duplicate_presets():
    rows = []
    for diameter_nm, rates in ((100, (0.2, 0.6)), (120, (0.8,))):
        rows.extend(
            {
                "particle_material": "exosome",
                "particle_diameter_nm": diameter_nm,
                "wavelength_nm": 660,
                "width_nm": 800,
                "depth_nm": 1400,
                "reference_operating_band": "electronics_noise_limited_useful",
                "detection_rate": rate,
                "all_crossing_detection_rate": rate,
                "selected_detector_mode_annulus_detection_rate": rate,
                "selected_detector_mode_annulus_fraction": 0.40,
                "stable_detection_rate": rate,
                "final_engineering_score": rate,
                "engineering_gate_passed": True,
                "na_cutoff_active": False,
                "rho_physical_envelope_status": "within_envelope",
            }
            for rate in rates
        )

    routes = route_analysis.aggregate_routes(
        pd.DataFrame(rows),
        {"uniform": {100: 1.0, 120: 1.0}},
    )
    row = routes.iloc[0]

    assert abs(row["uniform_weighted_detection"] - 0.6) < 1e-12
    assert abs(row["uniform_weighted_all_crossing_detection"] - 0.6) < 1e-12
    assert abs(row["uniform_weighted_selected_annulus_detection"] - 0.6) < 1e-12
    assert row["uniform_weighted_strict_pass"] == 1.0


def test_ev_size_weighted_route_analysis_marks_missing_selected_lens_unavailable():
    rows = []
    for route, base_rate in (
        ((488, 600, 1500), 0.50),
        ((532, 800, 700), 0.40),
    ):
        wavelength_nm, width_nm, depth_nm = route
        rows.extend(
            {
                "particle_material": "exosome",
                "particle_diameter_nm": diameter_nm,
                "wavelength_nm": wavelength_nm,
                "width_nm": width_nm,
                "depth_nm": depth_nm,
                "detection_rate": base_rate,
                "all_crossing_detection_rate": base_rate,
                "stable_detection_rate": base_rate,
                "final_engineering_score": base_rate,
                "engineering_gate_passed": base_rate > 0.45,
                "na_cutoff_active": False,
                "rho_physical_envelope_status": "within_envelope",
            }
            for diameter_nm in (60, 80, 100)
        )

    df = pd.DataFrame(rows)
    priors = {"uniform": {60: 1.0, 80: 1.0, 100: 1.0}}
    routes = route_analysis.aggregate_routes(df, priors)
    comparison = route_analysis.build_selected_annulus_ranking_comparison(
        routes,
        priors,
        top_n=1,
    )

    assert not routes["selected_annulus_lens_available"].any()
    assert routes["raw_mean_selected_annulus_detection"].isna().all()
    assert routes["uniform_weighted_selected_annulus_detection"].isna().all()
    assert not comparison["selected_annulus_lens_available"].iloc[0]
    assert json.loads(comparison["selected_annulus_top_routes"].iloc[0]) == []
    assert not comparison["selected_annulus_top1_route_changed"].iloc[0]
    assert not comparison["selected_annulus_top_routes_order_changed"].iloc[0]
    assert not comparison["selected_annulus_top_routes_changed"].iloc[0]


def test_selected_annulus_ranking_defaults_to_reference_useful_routes():
    rows = []
    route_specs = (
        ((660, 700, 1500), 0.4, 0.9, "reference_too_weak"),
        ((660, 800, 1400), 0.3, 0.5, "electronics_noise_limited_useful"),
        ((532, 600, 1500), 0.2, 0.4, "electronics_noise_limited_useful"),
    )
    for route, base_rate, selected_rate, reference_band in route_specs:
        wavelength_nm, width_nm, depth_nm = route
        rows.append(
            {
                "particle_material": "exosome",
                "particle_diameter_nm": 100,
                "wavelength_nm": wavelength_nm,
                "width_nm": width_nm,
                "depth_nm": depth_nm,
                "reference_operating_band": reference_band,
                "detection_rate": base_rate,
                "all_crossing_detection_rate": base_rate,
                "selected_detector_mode_annulus_detection_rate": selected_rate,
                "selected_detector_mode_annulus_fraction": 0.40,
                "stable_detection_rate": base_rate,
                "final_engineering_score": base_rate,
                "engineering_gate_passed": True,
                "na_cutoff_active": False,
                "rho_physical_envelope_status": "within_envelope",
            }
        )

    routes = route_analysis.aggregate_routes(pd.DataFrame(rows), {"uniform": {100: 1.0}})
    comparison = route_analysis.build_selected_annulus_ranking_comparison(
        routes,
        {"uniform": {100: 1.0}},
        top_n=1,
    )

    row = comparison.iloc[0]
    assert row["selected_annulus_rank_scope"] == "reference_useful_only"
    assert json.loads(row["selected_annulus_top_routes"]) == [
        {"wavelength_nm": 660, "width_nm": 800, "depth_nm": 1400}
    ]
    assert json.loads(row["selected_annulus_recommendation_top_routes"]) == [
        {"wavelength_nm": 660, "width_nm": 800, "depth_nm": 1400}
    ]
    assert json.loads(row["selected_annulus_boundary_top_routes"]) == [
        {"wavelength_nm": 660, "width_nm": 700, "depth_nm": 1500}
    ]


def test_ev_size_weighted_route_analysis_marks_empty_selected_lens_unavailable():
    df = pd.DataFrame(
        [
            {
                "particle_material": "exosome",
                "particle_diameter_nm": 100,
                "wavelength_nm": 488,
                "width_nm": 600,
                "depth_nm": 1500,
                "detection_rate": 0.5,
                "all_crossing_detection_rate": 0.5,
                "selected_detector_mode_annulus_detection_rate": float("nan"),
                "selected_detector_mode_annulus_fraction": 0.0,
                "stable_detection_rate": 0.5,
                "final_engineering_score": 0.5,
                "engineering_gate_passed": True,
                "na_cutoff_active": False,
                "rho_physical_envelope_status": "within_envelope",
            }
        ]
    )

    routes = route_analysis.aggregate_routes(df, {"uniform": {100: 1.0}})

    assert not routes["selected_annulus_lens_available"].iloc[0]
    assert (
        routes["selected_annulus_lens_source"].iloc[0]
        == "selected_detector_mode_annulus_empty_or_no_valid_denominator"
    )
    assert pd.isna(routes["uniform_weighted_selected_annulus_detection"].iloc[0])


def test_ev_size_weighted_route_analysis_requires_paired_selected_rate_and_fraction():
    df = pd.DataFrame(
        [
            {
                "particle_material": "exosome",
                "particle_diameter_nm": 100,
                "wavelength_nm": 532,
                "width_nm": 600,
                "depth_nm": 1500,
                "detection_rate": 0.5,
                "all_crossing_detection_rate": 0.5,
                "selected_detector_mode_annulus_detection_rate": 0.8,
                "selected_detector_mode_annulus_fraction": float("nan"),
                "stable_detection_rate": 0.5,
                "final_engineering_score": 0.5,
                "engineering_gate_passed": True,
                "na_cutoff_active": False,
                "rho_physical_envelope_status": "within_envelope",
            },
            {
                "particle_material": "exosome",
                "particle_diameter_nm": 100,
                "wavelength_nm": 488,
                "width_nm": 800,
                "depth_nm": 700,
                "detection_rate": 0.4,
                "all_crossing_detection_rate": 0.4,
                "selected_detector_mode_annulus_detection_rate": float("nan"),
                "selected_detector_mode_annulus_fraction": 0.3,
                "stable_detection_rate": 0.4,
                "final_engineering_score": 0.4,
                "engineering_gate_passed": True,
                "na_cutoff_active": False,
                "rho_physical_envelope_status": "within_envelope",
            },
        ]
    )

    routes = route_analysis.aggregate_routes(df, {"uniform": {100: 1.0}})
    comparison = route_analysis.build_selected_annulus_ranking_comparison(
        routes,
        {"uniform": {100: 1.0}},
    )

    assert not routes["selected_annulus_lens_available"].any()
    assert routes["raw_mean_selected_annulus_detection"].isna().all()
    assert routes["raw_mean_selected_annulus_fraction"].isna().all()
    assert not comparison["selected_annulus_lens_available"].iloc[0]
    assert json.loads(comparison["selected_annulus_top_routes"].iloc[0]) == []


def test_ev_size_weighted_route_analysis_reports_top1_order_change_when_topn_set_same():
    rows = []
    route_specs = (
        ((660, 1000, 1500), 0.60, 0.70),
        ((660, 2000, 1000), 0.50, 0.90),
        ((660, 1000, 500), 0.40, 0.80),
    )
    for route, base_rate, selected_rate in route_specs:
        wavelength_nm, width_nm, depth_nm = route
        rows.append(
            {
                "particle_material": "exosome",
                "particle_diameter_nm": 100,
                "wavelength_nm": wavelength_nm,
                "width_nm": width_nm,
                "depth_nm": depth_nm,
                "detection_rate": base_rate,
                "all_crossing_detection_rate": base_rate,
                "selected_detector_mode_annulus_detection_rate": selected_rate,
                "selected_detector_mode_annulus_fraction": 0.40,
                "stable_detection_rate": base_rate,
                "final_engineering_score": base_rate,
                "engineering_gate_passed": True,
                "na_cutoff_active": False,
                "rho_physical_envelope_status": "within_envelope",
            }
        )

    df = pd.DataFrame(rows)
    priors = {"uniform": {100: 1.0}}
    routes = route_analysis.aggregate_routes(df, priors)
    comparison = route_analysis.build_selected_annulus_ranking_comparison(
        routes,
        priors,
        top_n=3,
    )
    row = comparison.iloc[0]

    assert row["selected_annulus_top1_route_changed"]
    assert row["selected_annulus_top_routes_order_changed"]
    assert not row["selected_annulus_top_routes_changed"]


def test_ev_targeted_panel_keeps_primary_rank_and_adds_selected_annulus_rank():
    rows = []
    route_specs = (
        ((532, 600, 1500), 0.20, 0.30),
        ((488, 800, 700), 0.10, 0.90),
    )
    for route, stable_rate, selected_rate in route_specs:
        wavelength_nm, width_nm, depth_nm = route
        for diameter_nm in lane.EV_DIAMETERS_NM:
            rows.extend(
                {
                    "scenario_config_id": "ev_nodi_5sigma_single_current_design",
                    "particle_name": f"exosome_biomimetic_{diameter_nm}nm_member{member}",
                    "particle_diameter_nm": diameter_nm,
                    "wavelength_nm": wavelength_nm,
                    "width_nm": width_nm,
                    "depth_nm": depth_nm,
                    "detection_rate": stable_rate,
                    "stable_detection_rate": stable_rate,
                    "all_crossing_detection_rate": stable_rate,
                    "selected_detector_mode_candidate_fraction": 0.80,
                    "selected_detector_mode_candidate_detection_rate": selected_rate,
                    "selected_detector_mode_annulus_edge_norm_min": 0.50,
                    "selected_detector_mode_annulus_edge_norm_max": 0.80,
                    "selected_detector_mode_annulus_fraction": 0.40,
                    "selected_detector_mode_annulus_detection_rate": selected_rate,
                    "reference_operating_band": "ok",
                    "engineering_gate_passed": True,
                }
                for member in range(4)
            )

    ev = lane._ev_rows_from_raw(pd.DataFrame(rows))
    equal = ev[ev["EV_size_distribution_profile"] == "equal_current"]
    primary_top = equal[
        (equal["wavelength_nm"] == 532)
        & (equal["width_nm"] == 600)
        & (equal["depth_nm"] == 1500)
    ].iloc[0]
    selected_top = equal[
        (equal["wavelength_nm"] == 488)
        & (equal["width_nm"] == 800)
        & (equal["depth_nm"] == 700)
    ].iloc[0]

    assert primary_top["ranking_within_scenario"] == 1
    assert primary_top["ranking_within_scenario_all_crossing"] == 1
    assert primary_top["ranking_within_scenario_selected_annulus"] == 2
    assert selected_top["ranking_within_scenario_all_crossing"] == 2
    assert selected_top["ranking_within_scenario_selected_annulus"] == 1


def test_compare_ranking_frames_reports_selected_annulus_cross_check():
    ev = pd.DataFrame(
        [
            {
                "scenario_config_id": "ev_nodi_5sigma_single_current_design",
                "EV_size_distribution_profile": "equal_current",
                "wavelength_nm": 532,
                "width_nm": 600,
                "depth_nm": 1500,
                "weighted_detection_rate": 0.50,
                "weighted_stable_detection_rate": 0.50,
                "weighted_gate_pass_fraction": 1.0,
                "weighted_selected_detector_mode_annulus_detection_rate": 0.55,
                "weighted_selected_detector_mode_annulus_fraction": 0.40,
            },
            {
                "scenario_config_id": "ev_nodi_5sigma_single_current_design",
                "EV_size_distribution_profile": "equal_current",
                "wavelength_nm": 488,
                "width_nm": 800,
                "depth_nm": 700,
                "weighted_detection_rate": 0.40,
                "weighted_stable_detection_rate": 0.40,
                "weighted_gate_pass_fraction": 1.0,
                "weighted_selected_detector_mode_annulus_detection_rate": 0.95,
                "weighted_selected_detector_mode_annulus_fraction": 0.40,
            },
            {
                "scenario_config_id": "ev_nodi_5sigma_single_current_design",
                "EV_size_distribution_profile": "equal_current",
                "wavelength_nm": 660,
                "width_nm": 900,
                "depth_nm": 1500,
                "weighted_detection_rate": 0.45,
                "weighted_stable_detection_rate": 0.45,
                "weighted_gate_pass_fraction": 1.0,
                "weighted_selected_detector_mode_annulus_detection_rate": 0.45,
                "weighted_selected_detector_mode_annulus_fraction": 0.40,
            },
            {
                "scenario_config_id": "ev_nodi_5sigma_single_current_design",
                "EV_size_distribution_profile": "equal_current",
                "wavelength_nm": 404,
                "width_nm": 600,
                "depth_nm": 1300,
                "weighted_detection_rate": 0.20,
                "weighted_stable_detection_rate": 0.20,
                "weighted_gate_pass_fraction": 1.0,
                "weighted_selected_detector_mode_annulus_detection_rate": 0.97,
                "weighted_selected_detector_mode_annulus_fraction": 0.40,
            },
        ]
    )
    old = pd.DataFrame(
        [
            {
                "profile": "equal_current",
                "wavelength_nm": 532,
                "width_nm": 600,
                "depth_nm": 1500,
                "weighted_detected_per_10000": 5000.0,
                "weighted_stable_per_10000": 5000.0,
            },
            {
                "profile": "equal_current",
                "wavelength_nm": 488,
                "width_nm": 800,
                "depth_nm": 700,
                "weighted_detected_per_10000": 4000.0,
                "weighted_stable_per_10000": 4000.0,
            },
            {
                "profile": "equal_current",
                "wavelength_nm": 660,
                "width_nm": 900,
                "depth_nm": 1500,
                "weighted_detected_per_10000": 4500.0,
                "weighted_stable_per_10000": 4500.0,
            },
            {
                "profile": "equal_current",
                "wavelength_nm": 404,
                "width_nm": 600,
                "depth_nm": 1300,
                "weighted_detected_per_10000": 2000.0,
                "weighted_stable_per_10000": 2000.0,
            },
        ]
    )

    comparison = lane.compare_ranking_frames(ev, old)
    row = comparison.iloc[0]

    assert row["selected_annulus_lens_available"]
    assert row["selected_annulus_lens_status"] == "selected_annulus_parallel_lens_v1"
    assert not row["top3_changed"]
    assert row["selected_annulus_top3_changed_vs_all_crossing"]
    assert row["current_532_600x1500_rank"] == 1
    assert row["current_532_600x1500_selected_annulus_rank"] == 3
    assert row["recommendation_wavelength_rule"] == (
        "recommendation_conclusion_only_404_660__488_532_control_only"
    )
    assert json.loads(row["new_recommendation_top3_routes"]) == [
        [404, 600, 1300],
        [660, 900, 1500],
    ]
    assert json.loads(row["selected_annulus_recommendation_top3_routes"]) == [
        [404, 600, 1300],
        [660, 900, 1500],
    ]
    assert json.loads(row["selected_annulus_control_only_top3_routes"]) == [
        [488, 800, 700],
        [532, 600, 1500],
    ]
    assert row["selected_annulus_top3_contains_control_only"]


def test_compare_ranking_frames_marks_missing_selected_annulus_columns_unavailable():
    ev = pd.DataFrame(
        [
            {
                "scenario_config_id": "ev_nodi_5sigma_single_current_design",
                "EV_size_distribution_profile": "equal_current",
                "wavelength_nm": 532,
                "width_nm": 600,
                "depth_nm": 1500,
                "weighted_detection_rate": 0.50,
                "weighted_stable_detection_rate": 0.50,
                "weighted_gate_pass_fraction": 1.0,
            },
            {
                "scenario_config_id": "ev_nodi_5sigma_single_current_design",
                "EV_size_distribution_profile": "equal_current",
                "wavelength_nm": 488,
                "width_nm": 800,
                "depth_nm": 700,
                "weighted_detection_rate": 0.40,
                "weighted_stable_detection_rate": 0.40,
                "weighted_gate_pass_fraction": 1.0,
            },
            {
                "scenario_config_id": "ev_nodi_5sigma_single_current_design",
                "EV_size_distribution_profile": "equal_current",
                "wavelength_nm": 660,
                "width_nm": 900,
                "depth_nm": 1500,
                "weighted_detection_rate": 0.45,
                "weighted_stable_detection_rate": 0.45,
                "weighted_gate_pass_fraction": 1.0,
            },
        ]
    )
    old = pd.DataFrame(
        [
            {
                "profile": "equal_current",
                "wavelength_nm": 532,
                "width_nm": 600,
                "depth_nm": 1500,
                "weighted_detected_per_10000": 5000.0,
                "weighted_stable_per_10000": 5000.0,
            },
            {
                "profile": "equal_current",
                "wavelength_nm": 488,
                "width_nm": 800,
                "depth_nm": 700,
                "weighted_detected_per_10000": 4000.0,
                "weighted_stable_per_10000": 4000.0,
            },
            {
                "profile": "equal_current",
                "wavelength_nm": 660,
                "width_nm": 900,
                "depth_nm": 1500,
                "weighted_detected_per_10000": 4500.0,
                "weighted_stable_per_10000": 4500.0,
            },
        ]
    )

    comparison = lane.compare_ranking_frames(ev, old)
    row = comparison.iloc[0]

    assert not row["selected_annulus_lens_available"]
    assert (
        row["selected_annulus_lens_status"]
        == "missing_selected_annulus_columns_rerun_ev_panel_required"
    )
    assert json.loads(row["selected_annulus_top3_routes"]) == []
    assert not row["selected_annulus_top3_changed_vs_all_crossing"]
    assert pd.isna(row["current_532_600x1500_selected_annulus_rank"])
    assert pd.isna(
        row["current_532_600x1500_weighted_selected_annulus_detection_rate"]
    )


def test_compare_ranking_frames_marks_all_nan_selected_annulus_columns_unavailable():
    ev = pd.DataFrame(
        [
            {
                "scenario_config_id": "ev_nodi_5sigma_single_current_design",
                "EV_size_distribution_profile": "equal_current",
                "wavelength_nm": 532,
                "width_nm": 600,
                "depth_nm": 1500,
                "weighted_detection_rate": 0.50,
                "weighted_stable_detection_rate": 0.50,
                "weighted_gate_pass_fraction": 1.0,
                "weighted_selected_detector_mode_annulus_detection_rate": float("nan"),
                "weighted_selected_detector_mode_annulus_fraction": float("nan"),
            },
            {
                "scenario_config_id": "ev_nodi_5sigma_single_current_design",
                "EV_size_distribution_profile": "equal_current",
                "wavelength_nm": 488,
                "width_nm": 800,
                "depth_nm": 700,
                "weighted_detection_rate": 0.40,
                "weighted_stable_detection_rate": 0.40,
                "weighted_gate_pass_fraction": 1.0,
                "weighted_selected_detector_mode_annulus_detection_rate": float("nan"),
                "weighted_selected_detector_mode_annulus_fraction": float("nan"),
            },
            {
                "scenario_config_id": "ev_nodi_5sigma_single_current_design",
                "EV_size_distribution_profile": "equal_current",
                "wavelength_nm": 660,
                "width_nm": 900,
                "depth_nm": 1500,
                "weighted_detection_rate": 0.45,
                "weighted_stable_detection_rate": 0.45,
                "weighted_gate_pass_fraction": 1.0,
                "weighted_selected_detector_mode_annulus_detection_rate": float("nan"),
                "weighted_selected_detector_mode_annulus_fraction": float("nan"),
            },
        ]
    )
    old = pd.DataFrame(
        [
            {
                "profile": "equal_current",
                "wavelength_nm": 532,
                "width_nm": 600,
                "depth_nm": 1500,
                "weighted_detected_per_10000": 5000.0,
                "weighted_stable_per_10000": 5000.0,
            },
            {
                "profile": "equal_current",
                "wavelength_nm": 488,
                "width_nm": 800,
                "depth_nm": 700,
                "weighted_detected_per_10000": 4000.0,
                "weighted_stable_per_10000": 4000.0,
            },
            {
                "profile": "equal_current",
                "wavelength_nm": 660,
                "width_nm": 900,
                "depth_nm": 1500,
                "weighted_detected_per_10000": 4500.0,
                "weighted_stable_per_10000": 4500.0,
            },
        ]
    )

    comparison = lane.compare_ranking_frames(ev, old)
    row = comparison.iloc[0]

    assert not row["selected_annulus_lens_available"]
    assert row["selected_annulus_lens_status"] == (
        "selected_annulus_columns_empty_or_non_numeric"
    )
    assert json.loads(row["selected_annulus_top3_routes"]) == []
    assert not row["selected_annulus_top3_changed_vs_all_crossing"]
    assert pd.isna(row["current_532_600x1500_selected_annulus_rank"])
    assert pd.isna(
        row["current_532_600x1500_weighted_selected_annulus_detection_rate"]
    )
    assert pd.isna(row["current_532_600x1500_weighted_selected_annulus_fraction"])


def test_compare_ranking_frames_requires_paired_selected_rate_and_fraction():
    ev = pd.DataFrame(
        [
            {
                "scenario_config_id": "ev_nodi_5sigma_single_current_design",
                "EV_size_distribution_profile": "equal_current",
                "wavelength_nm": 532,
                "width_nm": 600,
                "depth_nm": 1500,
                "weighted_detection_rate": 0.50,
                "weighted_stable_detection_rate": 0.50,
                "weighted_gate_pass_fraction": 1.0,
                "weighted_selected_detector_mode_annulus_detection_rate": 0.8,
                "weighted_selected_detector_mode_annulus_fraction": float("nan"),
            },
            {
                "scenario_config_id": "ev_nodi_5sigma_single_current_design",
                "EV_size_distribution_profile": "equal_current",
                "wavelength_nm": 488,
                "width_nm": 800,
                "depth_nm": 700,
                "weighted_detection_rate": 0.40,
                "weighted_stable_detection_rate": 0.40,
                "weighted_gate_pass_fraction": 1.0,
                "weighted_selected_detector_mode_annulus_detection_rate": float("nan"),
                "weighted_selected_detector_mode_annulus_fraction": 0.3,
            },
        ]
    )
    old = pd.DataFrame(
        [
            {
                "profile": "equal_current",
                "wavelength_nm": 532,
                "width_nm": 600,
                "depth_nm": 1500,
                "weighted_detected_per_10000": 5000.0,
                "weighted_stable_per_10000": 5000.0,
            },
            {
                "profile": "equal_current",
                "wavelength_nm": 488,
                "width_nm": 800,
                "depth_nm": 700,
                "weighted_detected_per_10000": 4000.0,
                "weighted_stable_per_10000": 4000.0,
            },
        ]
    )

    row = lane.compare_ranking_frames(ev, old).iloc[0]

    assert not row["selected_annulus_lens_available"]
    assert row["selected_annulus_lens_status"] == (
        "selected_annulus_columns_empty_or_non_numeric"
    )
    assert json.loads(row["selected_annulus_top3_routes"]) == []
    assert pd.isna(row["current_532_600x1500_selected_annulus_rank"])
    assert pd.isna(
        row["current_532_600x1500_weighted_selected_annulus_detection_rate"]
    )
    assert pd.isna(row["current_532_600x1500_weighted_selected_annulus_fraction"])
