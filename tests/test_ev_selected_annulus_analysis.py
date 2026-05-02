from __future__ import annotations

import json

import pandas as pd

from tools import ev_size_weighted_route_analysis as route_analysis
from tools import tsuyama_gold_aligned_detection_lane as lane


def test_ev_size_weighted_route_analysis_emits_selected_annulus_lens():
    rows = []
    for route, base_rate, selected_rate in (
        ((488, 600, 1500), 0.50, 0.55),
        ((532, 800, 700), 0.40, 0.95),
    ):
        wavelength_nm, width_nm, depth_nm = route
        for diameter_nm in (60, 80, 100):
            rows.append(
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


def test_ev_size_weighted_route_analysis_marks_missing_selected_lens_unavailable():
    rows = []
    for route, base_rate in (
        ((488, 600, 1500), 0.50),
        ((532, 800, 700), 0.40),
    ):
        wavelength_nm, width_nm, depth_nm = route
        for diameter_nm in (60, 80, 100):
            rows.append(
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
            for member in range(4):
                rows.append(
                    {
                        "scenario_config_id": "ev_nodi_5sigma_single_current_design",
                        "particle_name": (
                            f"exosome_biomimetic_{diameter_nm}nm_member{member}"
                        ),
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
