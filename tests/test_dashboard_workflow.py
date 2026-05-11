"""
Focused pytest suite for dashboard workflow, live tuning, and cross-page behavior.

Parallel policy:
    - workflow/data tests belong to the xdist non-AppTest pytest lane
    - real AppTest interaction tests are explicitly marked serial via
      @pytest.mark.app_interactions
    - new tests must remain parallel-safe unless they are intentionally added
      to the serial AppTest lane; isolate session_state, avoid shared mutable
      globals, and use unique temp resources when needed
"""

import os
import json
import pickle
import re
import subprocess
import sys
import importlib
from typing import Any
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import streamlit as st

_StreamlitAppTest: Any = None
try:
    from streamlit.testing.v1 import AppTest as _StreamlitAppTest
except Exception:  # pragma: no cover - optional test dependency
    pass

AppTest: Any = _StreamlitAppTest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from nodi_simulator.data_objects import Channel, DEFAULT_SIM_CFG, PBS_1X, WATER
import nodi_simulator.dashboard.backend as backend_module
from nodi_simulator.design_claim_governance import (
    DESIGN_CLAIM_GOVERNANCE_FIELDS,
    PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1,
)
from nodi_simulator.dashboard.backend import (
    CURRENT_SCHEMA_VERSION,
    build_dashboard_data_source,
    build_physics_breakdown,
    check_data_files,
    build_local_fine_grid,
    build_optical_from_ui,
    build_sim_cfg_from_ui,
    list_available_datasets,
    load_dashboard_data_bundle,
    load_workflow_case_anchor,
    lookup_summary_case_row,
    load_result_health,
    load_sweep_compact,
    load_sweep_summary,
    resolve_preferred_dataset_prefix,
    run_live_sweep_custom,
    sync_dashboard_data_prefix,
)
import nodi_simulator.dashboard.precompute as precompute_module
from nodi_simulator.dashboard.config import (
    DEFAULT_SIM_CFG as DASHBOARD_DEFAULT_SIM_CFG,
    FULL_DIAMETER_VALUES_NM,
    FULL_SWEEP_WAVELENGTHS_NM,
    GRID_CONFIGS,
    OPTICAL_TEMPLATE,
    get_precompute_particles,
    make_particle,
    medium_for_particle,
    particle_from_name,
)
from nodi_simulator.dashboard.safe_pickle import dump_dashboard_pickle
from nodi_simulator.dashboard.estimate_precompute_runtime import estimate_runtime
from nodi_simulator.dashboard.estimate_precompute_runtime import (
    _write_json_atomic as _write_runtime_estimate_json_atomic,
)
from nodi_simulator.dashboard.mie_backend import (
    build_mie_angular_dataframe,
    build_mie_relative_index_scan_dataframe,
    build_mie_single_variable_scan_dataframe,
    build_mie_summary_dataframe,
    compute_mie_case,
)
from nodi_simulator.dashboard.precompute import (
    PrecomputeArtifactCopy,
    PrecomputeSaveContext,
    _build_precompute_artifact_paths,
    _build_precompute_save_steps,
    _build_precompute_run_context,
    _load_checkpoint_results,
    _should_flush_checkpoint,
    build_metadata,
    build_engineering_gate_calibration_report,
    build_freeze_probe_report,
    build_result_health_report,
    build_precompute_sim_cfg,
    precompute_sweep,
    results_to_design_postprocess_dataframe,
    results_to_diagnostics_long_dataframe,
    results_to_compact,
    results_to_dataframe,
    results_to_physics_fields_dataframe,
    _stable_hash,
)
from nodi_simulator.parameter_sweep import (
    _format_sweep_case_label,
    _format_sweep_progress_line,
    _build_sweep_last_case_snapshot,
    _build_sweep_progress_state,
)
from nodi_simulator.dashboard.panels.common import (
    PAGE_OPTIONS,
    WORKFLOW_PAGE_OPTIONS,
    build_case_context,
    format_case_verdict_caption,
    get_active_data_source_tag,
    get_selected_case_context,
    initialize_dashboard_session_state,
    render_page_header_hub,
    set_selected_case_context,
)
from nodi_simulator.dashboard.panels.explorer import (
    _resolve_default_design_material,
)
from nodi_simulator.dashboard.panels.interference_explorer import (
    _apply_defaults as apply_interference_defaults,
    _resolve_defaults as resolve_interference_defaults,
)
from nodi_simulator.dashboard.panels.mie_explorer import _resolve_linked_mie_defaults
from nodi_simulator.dashboard.panels.noise_detection_explorer import (
    _apply_defaults as apply_noise_defaults,
    _resolve_defaults as resolve_noise_defaults,
)
from nodi_simulator.dashboard.panels.single_case_calculator import (
    _build_single_case_report_from_state,
    _seed_single_case_state,
)
from nodi_simulator.dashboard.signal_backend import (
    build_case_inputs,
    build_rho_sensitivity_report,
    build_single_case_stage_report,
    build_detection_scan_dataframe,
    build_event_trace_dataframe,
    build_interference_scan_dataframe,
    build_path_opd_freeze_report,
    build_projection_mode_validation_dataframe,
    build_reference_model_consistency_report,
    compute_interference_case,
    compute_noise_detection_case,
)

MAC_LAUNCHER_PATH = REPO_ROOT / "start_dashboard.command"
WIN_LAUNCHER_PATH = REPO_ROOT / "start_dashboard.bat"
from nodi_simulator.reference_field import compute_reference_field
from nodi_simulator.tests.dashboard_test_helpers import (
    EXPECTED_PRECOMPUTE_ENGINEERING_DF_COLUMNS,
    assert_freeze_probe_report_contract,
    assert_precompute_engineering_dataframe_columns as shared_assert_precompute_engineering_dataframe_columns,
    assert_result_health_report_contract,
    build_freeze_probe_fixture_cases,
    build_result_health_fixture_frame,
    mock_dashboard_breakdown_case as shared_mock_dashboard_breakdown_case,
    mock_dashboard_engineering_result as shared_mock_dashboard_engineering_result,
)


APP_PATH = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"


def test_result_health_report_exposes_count_generation_monitoring():
    report = build_result_health_report(build_result_health_fixture_frame(), top_k=5)
    assert_result_health_report_contract(report)
    assert report["status_distributions"]["count_prediction_status"][
        "poisson_flux_deadtime_surrogate_active"
    ]["count"] == 1
    assert report["status_distributions"]["count_rate_confidence_status"][
        "not_available_no_blank_false_positive_or_uncertainty_propagation"
    ]["count"] == 3
    assert report["monitoring_summary"]["count_prediction_active_count"] == 1
    assert report["monitoring_summary"]["count_confidence_unavailable_count"] == 3
    assert (
        report["monitoring_summary"][
            "crossing_conditioned_transport_unimplemented_count"
        ]
        == 3
    )
    assert report["status_distributions"]["detector_forward_model"][
        "joint_overlap_coherent_surrogate"
    ]["count"] == 3
    assert report["status_distributions"]["mie_to_power_chain_status"][
        "not_implemented_dCsca_dOmega_not_converted_to_detector_units"
    ]["count"] == 3
    assert report["status_distributions"]["interface_fullwave_required"]["True"][
        "count"
    ] == 3
    assert report["monitoring_summary"]["detector_forward_surrogate_count"] == 3
    assert report["monitoring_summary"]["unimplemented_mie_to_power_chain_count"] == 3
    assert report["monitoring_summary"]["held_out_calibration_unavailable_count"] == 3
    assert report["monitoring_summary"]["interface_fullwave_required_count"] == 3
    assert report["monitoring_summary"]["thermal_pod_blocked_count"] == 3
    row_exosome = next(
        row
        for row in report["health_slices"]["by_particle_material"]
        if row["particle_material"] == "exosome"
    )
    assert row_exosome["count_prediction_active_fraction"] == pytest.approx(1.0)
    assert row_exosome["interface_fullwave_required_fraction"] == pytest.approx(1.0)
    assert row_exosome["thermal_pod_blocked_fraction"] == pytest.approx(1.0)


def test_freeze_probe_report_exposes_count_generation_monitoring():
    review, ready = build_freeze_probe_fixture_cases()
    report = build_freeze_probe_report([review, ready], top_k=2)
    assert_freeze_probe_report_contract(report)
    assert report["status_distributions"]["count_prediction_status"][
        "poisson_flux_deadtime_surrogate_active"
    ]["count"] == 1
    assert report["status_distributions"]["count_prediction_status"][
        "not_applied_per_event_detection_only"
    ]["count"] == 1
    assert report["sanity_checks"]["count_prediction_active_fraction"] == pytest.approx(
        0.5
    )
    assert report["sanity_checks"]["count_confidence_unavailable_fraction"] == pytest.approx(
        1.0
    )
    assert report["sanity_checks"][
        "crossing_conditioned_transport_unimplemented_fraction"
    ] == pytest.approx(1.0)
    assert report["status_distributions"]["detector_forward_status"][
        "joint_overlap_requested_scalar_surrogate_fallback"
    ]["count"] == 2
    assert report["status_distributions"]["calibration_held_out_validation_status"][
        "not_available_no_standard_particle_design"
    ]["count"] == 2
    assert report["sanity_checks"]["interface_fullwave_required_fraction"] == pytest.approx(
        1.0
    )
    assert report["sanity_checks"]["thermal_pod_blocked_fraction"] == pytest.approx(1.0)
    assert report["sanity_checks"][
        "unimplemented_mie_to_power_chain_fraction"
    ] == pytest.approx(1.0)
    assert report["sanity_checks"][
        "held_out_calibration_unavailable_fraction"
    ] == pytest.approx(1.0)
    assert (
        report["top_cases"][0]["count_prediction_status"]
        == "poisson_flux_deadtime_surrogate_active"
    )
    assert report["top_cases"][0]["interface_fullwave_required"] is True
    assert report["top_cases"][0]["thermal_pod_model_status"] == (
        "unavailable_no_heat_diffusion_model"
    )


def test_particle_medium_routing_uses_water_for_gold_and_pbs_for_exosome():
    gold = make_particle("gold", 80)
    exosome = make_particle("exosome", 100)

    assert medium_for_particle(gold).name == WATER.name
    assert medium_for_particle(exosome).name == PBS_1X.name

    gold_inputs = build_case_inputs(
        material="gold",
        diameter_nm=80,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
    )
    exosome_inputs = build_case_inputs(
        material="exosome",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
    )

    assert gold_inputs["medium"].name == WATER.name
    assert exosome_inputs["medium"].name == PBS_1X.name

_EXPECTED_PRECOMPUTE_ENGINEERING_DF_COLUMNS = EXPECTED_PRECOMPUTE_ENGINEERING_DF_COLUMNS


class _SessionStateGuard:
    def __enter__(self):
        self._snapshot = dict(st.session_state)
        st.session_state.clear()
        return st.session_state

    def __exit__(self, _exc_type, _exc, _tb):
        st.session_state.clear()
        st.session_state.update(self._snapshot)
        return False


def _make_app_test(page: str, **session_overrides):
    if AppTest is None:
        pytest.skip("streamlit.testing.v1.AppTest is not available in this environment")

    at = AppTest.from_file(str(APP_PATH), default_timeout=30)
    at.session_state["dashboard_page"] = page
    at.session_state["dashboard_page_radio"] = page
    for key, value in session_overrides.items():
        at.session_state[key] = value
    at.run()
    return at


def _header_values(at) -> list[str]:
    return [header.value for header in at.header]


def test_single_case_stage_report_exposes_rho_probe_summary():
    report = build_single_case_stage_report(
        material="exosome",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=1000,
        depth_nm=550,
        n_events=4,
    )

    assert report["meta"]["material"] == "exosome"
    assert report["headline"]["headline"]
    assert report["diagnostics"]["report_random_seed"] == DEFAULT_SIM_CFG.random_seed
    assert report["diagnostics"]["report_random_seed_source"] == "sim_cfg_random_seed"
    assert not report["rho_sensitivity_df"].empty
    assert report["rho_sensitivity_summary"]["rho_sensitivity_candidate_count"] >= 1
    assert report["rho_sensitivity_summary"]["rho_sensitivity_status"] in {
        "within_envelope_and_robust",
        "within_envelope_but_sensitive",
        "high_sensitivity",
        "out_of_envelope_but_locally_robust",
        "out_of_envelope_and_sensitive",
        "unavailable",
    }
    assert "clean_signal" in report["interference_trace_df"].columns
    assert "signal_noisy" in report["event_trace_df"].columns
    assert "detected" in report["event_table_df"].columns


def test_rho_sensitivity_report_exports_envelope_probe_rows_top_level():
    rho_df, rho_summary = build_rho_sensitivity_report(
        material="exosome",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=1000,
        depth_nm=550,
        n_events=4,
    )

    assert not rho_df.empty
    assert {
        "rho",
        "rho_candidate_roles",
        "rho_candidate_is_requested",
        "rho_candidate_is_nominal",
        "A_ref",
        "peak_clean_signal",
        "detection_rate",
        "stable_detection_rate",
        "engineering_gate_passed",
        "design_recommendation_status",
        "detection_rate_delta_vs_anchor",
        "peak_clean_rel_delta_vs_anchor",
    }.issubset(rho_df.columns)
    requested_row = rho_df.loc[rho_df["rho_candidate_is_requested"]].iloc[0]
    assert requested_row["rho_candidate_roles"]
    assert rho_summary["rho_sensitivity_candidate_count"] == len(rho_df)
    assert rho_summary["rho_sensitivity_anchor_role"] in {
        "requested",
        "rho_physical_envelope_nominal",
    }
    assert rho_summary["rho_sensitivity_report_random_seed"] == DEFAULT_SIM_CFG.random_seed
    assert rho_summary["rho_sensitivity_report_random_seed_source"] == "sim_cfg_random_seed"
    assert rho_summary["rho_sensitivity_label"]
    assert rho_summary["rho_sensitivity_guidance"]
    assert np.isfinite(
        float(rho_summary["rho_sensitivity_max_abs_detection_rate_delta_vs_anchor"])
    )
    assert np.isfinite(
        float(rho_summary["rho_sensitivity_max_abs_peak_clean_rel_delta_vs_anchor"])
    )
    assert requested_row["detection_rate_delta_vs_anchor"] == pytest.approx(
        rho_summary["rho_sensitivity_requested_vs_anchor_detection_rate_delta"]
    )
    assert requested_row["peak_clean_rel_delta_vs_anchor"] == pytest.approx(
        rho_summary["rho_sensitivity_requested_vs_anchor_peak_clean_rel_delta"]
    )


def _assert_header_contains(at, text: str) -> None:
    headers = _header_values(at)
    assert any(text in value for value in headers), headers


def _assert_no_app_exceptions(at) -> None:
    assert len(at.exception) == 0


def _assert_precompute_engineering_dataframe_columns(df: pd.DataFrame) -> None:
    shared_assert_precompute_engineering_dataframe_columns(df)


def test_design_explorer_defaults_to_exosome_when_available():
    assert _resolve_default_design_material(["gold", "exosome"], None) == "exosome"
    assert _resolve_default_design_material(["gold", "exosome"], "gold_80nm") == "gold"


def test_particle_from_name_rebuilds_biomimetic_exosome_particle():
    particle = particle_from_name("exosome_biomimetic_corona_nominal_100nm")
    assert particle.name == "exosome_biomimetic_corona_nominal_100nm"
    assert particle.model_type == "mie_core_shell"
    assert particle.structure_key == "exosome_biomimetic"
    assert particle.structure_params == {"preset_name": "biomimetic_corona_nominal"}


def test_particle_from_name_rebuilds_biomimetic_ensemble_member_particle():
    particle = particle_from_name(
        "exosome_literature_bounds_2021_01_membrane_only_dim_2021_100nm"
    )
    assert particle.name == (
        "exosome_literature_bounds_2021_01_membrane_only_dim_2021_100nm"
    )
    assert particle.model_type == "mie_core_shell"
    assert particle.structure_key == "exosome_biomimetic"
    assert particle.structure_params == {"preset_name": "membrane_only_dim_2021"}


def test_biomimetic_precompute_profiles_are_available():
    combined_particles = get_precompute_particles("full_range_biomimetic_exosome")
    anchored_particles = get_precompute_particles(
        "full_range_biomimetic_exosome_with_anchors"
    )
    ensemble_particles = get_precompute_particles(
        "ev_design_biomimetic_ensemble_with_anchors"
    )

    assert len(combined_particles) == 2 * len(FULL_DIAMETER_VALUES_NM)
    gold_particles = [p for p in combined_particles if p.name.startswith("gold_")]
    biomimetic_particles = [
        p for p in combined_particles if p.name.startswith("exosome_biomimetic_corona_nominal_")
    ]
    assert len(gold_particles) == len(FULL_DIAMETER_VALUES_NM)
    assert len(biomimetic_particles) == len(FULL_DIAMETER_VALUES_NM)
    assert all(p.model_type == "mie_core_shell" for p in biomimetic_particles)
    assert any(p.name.startswith("gold_") for p in combined_particles)
    assert any(p.name.startswith("exosome_biomimetic_corona_nominal_") for p in combined_particles)
    anchored_gold_names = [p.name for p in anchored_particles if p.name.startswith("gold_")]
    assert "gold_20nm" in anchored_gold_names
    assert "gold_30nm" in anchored_gold_names
    assert len(anchored_particles) == 2 + (2 * len(FULL_DIAMETER_VALUES_NM))
    ensemble_ev_particles = [
        p
        for p in ensemble_particles
        if p.name.startswith("exosome_literature_bounds_2021_")
    ]
    assert len(ensemble_ev_particles) == 4 * 11
    assert {
        p.structure_params["EV_ensemble_member_preset"] for p in ensemble_ev_particles
    } == {
        "membrane_only_dim_2021",
        "membrane_only_nominal_2020",
        "biomimetic_corona_nominal",
        "surface_loaded_bright_2021",
    }
    assert any(p.name == "gold_20nm" for p in ensemble_particles)
    assert any(p.name == "gold_300nm" for p in ensemble_particles)


def test_build_metadata_records_particle_models_for_biomimetic_profile():
    sim_cfg = build_precompute_sim_cfg("coarse")
    particles = [
        particle
        for particle in get_precompute_particles("full_range_biomimetic_exosome")
        if particle.name.startswith("exosome_biomimetic_corona_nominal_")
    ][:2]
    meta = build_metadata(
        "coarse",
        "coarse_exosome_biomimetic_smoke",
        "full_range_biomimetic_exosome",
        sim_cfg,
        GRID_CONFIGS["coarse"],
        particles,
        [],
    )

    assert "particle_models" in meta
    assert len(meta["particle_models"]) == 2
    assert all(item["model_type"] == "mie_core_shell" for item in meta["particle_models"])
    assert all(item["structure_key"] == "exosome_biomimetic" for item in meta["particle_models"])
    assert all(item["particle_family"] == "EV_sEV" for item in meta["particle_models"])
    assert all(
        item["particle_optical_model"] == "core_shell_EV_sEV_surrogate"
        for item in meta["particle_models"]
    )
    assert all(
        item["EV_claim_level"] == "optical_EV_like_particle"
        for item in meta["particle_models"]
    )
    assert all(
        item["uncertainty_propagation_mode"] == sim_cfg.particle_uncertainty_propagation_mode
        for item in meta["particle_models"]
    )
    assert all(
        item["thermal_pod_model"] == sim_cfg.thermal_pod_model
        for item in meta["particle_models"]
    )
    assert meta["dashboard_schema_version"] == CURRENT_SCHEMA_VERSION
    assert meta["model_semantic_version"] == meta["model_semantics_version"]
    assert meta["model_semantics_version"] == "tsuyama_alignment_governed_surrogate_v1"
    assert meta["simulation_config_hash"].startswith("simcfg_")
    assert meta["particle_library_hash"].startswith("particlelib_")
    assert meta["material_database_hash"].startswith("materials_")
    assert meta["reference_model_hash"].startswith("refmodel_")
    assert meta["detector_operator_hash"].startswith("detectorop_")
    assert meta["code_state_hash_or_git_commit_hash"]
    assert meta["code_state_source"] in {
        "git_commit_hash",
        "source_tree_fingerprint",
    }
    assert meta["sweep_completion_policy"]["allow_partial_results"] is False
    assert meta["sweep_completion_policy"]["expected_total_cases"] == (
        len(particles)
        * len(GRID_CONFIGS["coarse"]["wavelength_list_m"])
        * len(GRID_CONFIGS["coarse"]["width_list_m"])
        * len(GRID_CONFIGS["coarse"]["depth_list_m"])
    )
    assert meta["export_format_manifest"]["case_summary_csv"].endswith(
        "_case_summary.csv"
    )
    assert meta["result_library_role"] == "paper_aligned_governed_engineering_surrogate"
    assert meta["result_library_status"] == "schema_1_24_requires_regenerated_results"
    assert meta["legacy_current_code_library_compatible"] is False
    assert "Old current-code result libraries" in meta["schema_migration_note"]
    inventory = meta["schema_feature_inventory"]
    assert inventory["inventory_schema_version"] == "schema_feature_inventory_v1"
    assert "schema_feature_inventory" in inventory["required_metadata_sections"]
    assert meta["analysis_lanes"]["all_crossing"]["rate_field"] == "detection_rate"
    selected_lane = meta["analysis_lanes"]["selected_annulus"]
    assert selected_lane["edge_norm_min"] == 0.5
    assert selected_lane["edge_norm_max"] == 0.8
    assert (
        selected_lane["paper_alignment_target"]
        == PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1
    )
    assert inventory["route_contract"]["analysis_lanes"] == [
        "all_crossing",
        "selected_annulus",
    ]
    assert inventory["route_contract"]["selected_annulus_edge_norm_min"] == 0.5
    assert inventory["route_contract"]["selected_annulus_edge_norm_max"] == 0.8
    assert (
        inventory["route_contract"]["selected_annulus_paper_alignment_target"]
        == PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1
    )
    assert "selected_detector_mode" in inventory["governed_case_field_groups"]
    assert "selected_detector_mode_annulus_detection_rate" in inventory[
        "governed_case_field_groups"
    ]["selected_detector_mode"]
    assert "reference_calibration_health" in inventory["required_metadata_sections"]
    assert (
        "collection_operator_calibration_health"
        in inventory["required_metadata_sections"]
    )
    assert (
        "wavelength_material_governance"
        in inventory["governed_case_field_groups"]
    )
    assert "medium_optical_material_key" in inventory[
        "governed_case_field_groups"
    ]["wavelength_material_governance"]
    assert "fluidic_network_model" in inventory["governed_case_field_groups"]
    assert "fluidic_network_pressure_flow_relation_status" in inventory[
        "governed_case_field_groups"
    ]["fluidic_network_model"]
    assert "control_interpretation" in inventory["governed_case_field_groups"]
    assert "control_failure_interpretation_gate_passed" in inventory[
        "governed_case_field_groups"
    ]["control_interpretation"]
    calibration_health = meta["reference_calibration_health"]
    assert calibration_health["reference_calibration_health_schema"] == (
        "reference_calibration_health_v1"
    )
    assert calibration_health["health_status"] == "inactive_no_blank_calibration_path"
    assert calibration_health["reference_calibration_active"] is False
    assert calibration_health["n_cases"] == 0
    operator_health = meta["collection_operator_calibration_health"]
    assert operator_health["collection_operator_calibration_health_schema"] == (
        "collection_operator_calibration_health_v1"
    )
    assert operator_health["health_status"] == (
        "inactive_no_operator_calibration_path"
    )
    assert operator_health["collection_operator_calibration_path_configured"] is False
    assert operator_health["n_cases"] == 0
    assert (
        inventory["route_contract"]["detector_forward_model"]
        == sim_cfg.detector_forward_model
    )
    assert (
        inventory["route_contract"]["field_coordinate_measure"]
        == sim_cfg.field_coordinate_measure
    )
    assert inventory["route_contract"]["thermal_pod_model"] == sim_cfg.thermal_pod_model
    assert (
        inventory["route_contract"]["collection_operator_calibration_path_configured"]
        is False
    )
    assert (
        inventory["route_contract"]["standard_particle_calibration_path_configured"]
        is False
    )
    assert (
        inventory["route_contract"][
            "blank_false_positive_calibration_path_configured"
        ]
        is False
    )
    assert inventory["route_contract"]["raw_blank_trace_path_configured"] is False
    assert inventory["route_contract"]["bfp_roi_mask_path_configured"] is False
    assert "interface_fullwave_required" in inventory["governed_case_field_groups"][
        "interface_correction"
    ]
    assert "particle_design_library" in inventory["governed_case_field_groups"]
    assert "contaminant_detectability_score" in inventory[
        "governed_case_field_groups"
    ]["particle_design_library"]
    assert "operator_route" in inventory["governed_case_field_groups"][
        "reference_detector_and_calibration"
    ]
    assert (
        "standard_particle_calibration_coverage_status"
        in inventory["governed_case_field_groups"]["reference_detector_and_calibration"]
    )
    assert (
        "standard_particle_calibration_data_role"
        in inventory["governed_case_field_groups"]["reference_detector_and_calibration"]
    )
    assert "bfp_roi_mask_status" in inventory["governed_case_field_groups"][
        "reference_detector_and_calibration"
    ]
    assert "bfp_roi_mask_source" in inventory["governed_case_field_groups"][
        "reference_detector_and_calibration"
    ]
    assert "bfp_roi_mask_gate_passed" in inventory["governed_case_field_groups"][
        "reference_detector_and_calibration"
    ]
    assert "detector_forward_model" in inventory["governed_case_field_groups"][
        "reference_detector_and_calibration"
    ]
    design_claim_fields = inventory["governed_case_field_groups"][
        "minimum_design_claim_schema"
    ]
    assert set(DESIGN_CLAIM_GOVERNANCE_FIELDS).issubset(design_claim_fields)
    assert "detector_operator_caution_reason" in design_claim_fields
    assert "detector_resolved_relative_design_eligible" in design_claim_fields
    assert "relative_design_with_detector_caution" in design_claim_fields
    assert "superposition_validity_status" in inventory["governed_case_field_groups"][
        "coordinate_vector_superposition"
    ]
    assert "polarization_overlap_efficiency" in inventory[
        "governed_case_field_groups"
    ]["coordinate_vector_superposition"]
    assert "phase_polarization_quantitative_claim_allowed" in inventory[
        "governed_case_field_groups"
    ]["coordinate_vector_superposition"]
    assert "polarization_jones_operator" in inventory["governed_case_field_groups"]
    assert "noise_terms_schema_version" in inventory["governed_case_field_groups"][
        "detector_noise_and_units"
    ]
    assert "detector_unit_chain_status" in inventory["governed_case_field_groups"][
        "detector_noise_and_units"
    ]
    assert "nodi_random_vs_locked_disagreement" in inventory[
        "governed_case_field_groups"
    ]["readout_convention"]
    assert "raw_blank_trace_bootstrap_status" in inventory[
        "governed_case_field_groups"
    ]["threshold_false_alarm"]
    assert "colored_noise_threshold_bias" in inventory[
        "governed_case_field_groups"
    ]["threshold_false_alarm"]
    assert "interface_api_boundary_status" in inventory["governed_case_field_groups"][
        "interface_correction"
    ]
    assert "thermal_pod_api_boundary_status" in inventory[
        "governed_case_field_groups"
    ]["thermal_pod"]
    assert "pod_heat_source_status" in inventory["governed_case_field_groups"][
        "thermal_pod"
    ]
    assert "count_prediction_status" in inventory["governed_case_field_groups"][
        "count_generation"
    ]
    assert "count_likelihood" in inventory["governed_case_field_groups"]
    assert "false_positive_corrected_count" in inventory[
        "governed_case_field_groups"
    ]["count_likelihood"]
    assert "ood_detection" in inventory["governed_case_field_groups"]
    assert "unknown_particle_flag" in inventory["governed_case_field_groups"][
        "ood_detection"
    ]
    assert "bayesian_calibration" in inventory["governed_case_field_groups"]
    assert "posterior_predictive_design_score_p10" in inventory[
        "governed_case_field_groups"
    ]["bayesian_calibration"]
    assert "experimental_design_advisor" in inventory["governed_case_field_groups"]
    assert "value_of_information_score" in inventory["governed_case_field_groups"][
        "experimental_design_advisor"
    ]
    assert "objective_panel" in inventory["governed_case_field_groups"]
    assert "objective_panel_recommendation" in inventory[
        "governed_case_field_groups"
    ]["objective_panel"]
    assert "ev_population_prior" in inventory["governed_case_field_groups"]
    assert "ev_low_RI_tail_detection_risk" in inventory[
        "governed_case_field_groups"
    ]["ev_population_prior"]
    assert "population_inference" in inventory["governed_case_field_groups"]
    assert "population_inference_gate_passed" in inventory[
        "governed_case_field_groups"
    ]["population_inference"]
    assert "control_interpretation" in inventory["governed_case_field_groups"]
    assert "control_interpretation_status" in inventory[
        "governed_case_field_groups"
    ]["control_interpretation"]
    assert "fluidic_network_model" in inventory["governed_case_field_groups"]
    assert "fluidic_network_gate_passed" in inventory[
        "governed_case_field_groups"
    ]["fluidic_network_model"]
    assert inventory["quantitative_boundaries"]["pod_amplitude"] == (
        "blocked_until_heat_diffusion_and_probe_calibration_exist"
    )
    assert meta["sim_cfg"]["illumination_mode"] == DASHBOARD_DEFAULT_SIM_CFG.illumination_mode
    assert meta["sim_cfg"]["flow_profile_model"] == "rect_series"
    assert meta["sim_cfg"]["initial_position_distribution_mode"] == "flux_weighted"
    assert meta["sim_cfg"]["readout_preset"] == "EV_NODI_only_design"
    assert meta["sim_cfg"]["readout_observable_mode"] == "magnitude"
    assert (
        meta["sim_cfg"]["reference_width_saturation_mode"]
        == DASHBOARD_DEFAULT_SIM_CFG.reference_width_saturation_mode
    )
    assert meta["optical"]["illumination_NA"] == pytest.approx(OPTICAL_TEMPLATE.illumination_NA)
    assert meta["optical"]["NA_collection"] == pytest.approx(OPTICAL_TEMPLATE.NA_collection)
    waist_by_wavelength = meta["optical"]["illumination_effective_beam_waists_by_wavelength_nm"]
    assert set(waist_by_wavelength) == {
        str(int(round(wavelength_nm))) for wavelength_nm in FULL_SWEEP_WAVELENGTHS_NM
    }
    assert waist_by_wavelength["404"]["illumination_beam_geometry_source"] == "objective_na_surrogate"
    assert waist_by_wavelength["404"]["illumination_effective_beam_waist_y_nm"] == pytest.approx(
        round(0.61 * 404e-9 / OPTICAL_TEMPLATE.illumination_NA * 1e9)
    )
    assert waist_by_wavelength["660"]["illumination_effective_beam_waist_y_nm"] == pytest.approx(
        round(0.61 * OPTICAL_TEMPLATE.wavelength_m / OPTICAL_TEMPLATE.illumination_NA * 1e9)
    )


def test_precompute_stable_hash_orders_sets_and_uses_128_bit_digest():
    left = _stable_hash({"items": {"beta", "alpha"}}, prefix="case")
    right = _stable_hash({"items": {"alpha", "beta"}}, prefix="case")
    frozen = _stable_hash({"items": frozenset({"beta", "alpha"})}, prefix="case")

    assert left == right == frozen
    assert re.fullmatch(r"case_[0-9a-f]{32}", left)


def test_runtime_estimate_json_writer_is_atomic_and_strict(tmp_path):
    output = tmp_path / "report.json"
    _write_runtime_estimate_json_atomic(str(output), {"ok": 1.0})

    assert json.loads(output.read_text(encoding="utf-8")) == {"ok": 1.0}

    with pytest.raises(ValueError):
        _write_runtime_estimate_json_atomic(str(output), {"bad": float("nan")})

    assert json.loads(output.read_text(encoding="utf-8")) == {"ok": 1.0}
    assert not output.with_suffix(output.suffix + ".tmp").exists()


def test_build_metadata_records_explicit_partial_result_policy():
    sim_cfg = build_precompute_sim_cfg("coarse")
    particles = get_precompute_particles("quick")[:1]

    meta = build_metadata(
        "coarse",
        "partial_allowed_smoke",
        "quick",
        sim_cfg,
        GRID_CONFIGS["coarse"],
        particles,
        [],
        allow_partial_results=True,
    )

    assert meta["sweep_completion_policy"] == {
        "allow_partial_results": True,
        "expected_total_cases": (
            len(particles)
            * len(GRID_CONFIGS["coarse"]["wavelength_list_m"])
            * len(GRID_CONFIGS["coarse"]["width_list_m"])
            * len(GRID_CONFIGS["coarse"]["depth_list_m"])
        ),
        "saved_case_count": 0,
        "completion_status": "partial_results_explicitly_allowed",
    }


def test_precompute_run_context_rejects_path_like_config_tag(tmp_path):
    with pytest.raises(ValueError, match="config_tag"):
        _build_precompute_run_context(
            grid_name="coarse",
            config_tag="../escape",
            particle_profile="quick",
            output_dir=str(tmp_path),
            n_workers=1,
            checkpoint_enabled=True,
            resume_enabled=True,
        )

    with pytest.raises(ValueError, match="config_tag"):
        _build_precompute_run_context(
            grid_name="coarse",
            config_tag="",
            particle_profile="quick",
            output_dir=str(tmp_path),
            n_workers=1,
            checkpoint_enabled=True,
            resume_enabled=True,
        )


def test_precompute_run_context_applies_event_engine_overrides(tmp_path):
    context = _build_precompute_run_context(
        grid_name="coarse",
        config_tag="vectorized_smoke",
        particle_profile="quick",
        output_dir=str(tmp_path),
        n_workers=1,
        checkpoint_enabled=True,
        resume_enabled=True,
        vectorized_event_engine="pure_advection_block",
        event_block_size=7,
        include_diffusion=False,
    )

    assert context.sim_cfg.vectorized_event_engine == "pure_advection_block"
    assert context.sim_cfg.event_block_size == 7
    assert context.sim_cfg.include_diffusion is False


def test_precompute_run_context_keeps_scalar_event_loop_override(tmp_path):
    context = _build_precompute_run_context(
        grid_name="coarse",
        config_tag="scalar_smoke",
        particle_profile="quick",
        output_dir=str(tmp_path),
        n_workers=1,
        checkpoint_enabled=True,
        resume_enabled=True,
        vectorized_event_engine="off",
        event_block_size=5,
        include_diffusion=True,
    )

    assert context.sim_cfg.random_sequence_policy == "case_keyed_independent"
    assert context.sim_cfg.event_sampling_policy == "sobol_stratified"
    assert context.sim_cfg.vectorized_event_engine == "off"
    assert context.sim_cfg.event_block_size == 5
    assert context.sim_cfg.include_diffusion is True


def test_precompute_cli_reports_invalid_tag_without_traceback(tmp_path):
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "nodi_simulator.dashboard.precompute",
            "--grid",
            "coarse",
            "--particle-profile",
            "quick",
            "--tag",
            "../escape",
            "--output",
            str(tmp_path),
            "--artifact-profile",
            "minimal",
        ],
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 2
    assert "config_tag must be a safe filename token" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_parameter_sweep_case_label_uses_readable_wavelength_symbol():
    line = _format_sweep_case_label(
        {
            "case_idx": 7,
            "total_cases": 10,
            "particle_name": "gold_40nm",
            "wavelength_m": 488e-9,
            "width_m": 500e-9,
            "depth_m": 600e-9,
        }
    )

    assert "λ=488nm" in line
    assert "ﾎｻ" not in line


def test_case_summary_csv_save_step_copies_written_summary_csv(tmp_path):
    artifact_paths = _build_precompute_artifact_paths(str(tmp_path), "coarse_copy")
    source_text = "particle_name,score\ncase-a,1.0\ncase-b,0.5\n"
    Path(artifact_paths.summary_csv).write_text(source_text, encoding="utf-8")
    save_context = PrecomputeSaveContext(
        summary_df=pd.DataFrame(
            {
                "particle_name": ["case-a", "case-b"],
                "score": [1.0, 0.5],
            }
        ),
        summary_csv_path=artifact_paths.summary_csv,
    )
    save_steps = _build_precompute_save_steps(
        artifact_paths=artifact_paths,
        save_context=save_context,
        results=[],
        grid_name="coarse",
        config_tag="copy",
        particle_profile="quick",
        sim_cfg=build_precompute_sim_cfg("coarse"),
        grid=GRID_CONFIGS["coarse"],
        particle_types=get_precompute_particles("quick"),
        save_freeze_probe_report=False,
        artifact_profile="full",
    )

    case_summary_step = next(
        step for step in save_steps if step.output_key == "case_summary_csv"
    )
    payload = case_summary_step.build_payload()
    assert isinstance(payload, PrecomputeArtifactCopy)
    assert payload.source_path == artifact_paths.summary_csv

    case_summary_step.writer(case_summary_step.path, payload)

    assert Path(case_summary_step.path).read_text(encoding="utf-8") == source_text


def test_case_summary_csv_save_step_ignores_stale_summary_file(tmp_path):
    artifact_paths = _build_precompute_artifact_paths(str(tmp_path), "coarse_stale")
    Path(artifact_paths.summary_csv).write_text(
        "particle_name,score\nstale,999\n",
        encoding="utf-8",
    )
    save_context = PrecomputeSaveContext(
        summary_df=pd.DataFrame({"particle_name": ["fresh"], "score": [1.0]}),
        summary_csv_path=None,
    )
    save_steps = _build_precompute_save_steps(
        artifact_paths=artifact_paths,
        save_context=save_context,
        results=[],
        grid_name="coarse",
        config_tag="stale",
        particle_profile="quick",
        sim_cfg=build_precompute_sim_cfg("coarse"),
        grid=GRID_CONFIGS["coarse"],
        particle_types=get_precompute_particles("quick"),
        save_freeze_probe_report=False,
        artifact_profile="full",
    )

    case_summary_step = next(
        step for step in save_steps if step.output_key == "case_summary_csv"
    )
    payload = case_summary_step.build_payload()

    assert isinstance(payload, pd.DataFrame)
    assert payload["particle_name"].tolist() == ["fresh"]


def test_precompute_save_steps_reuse_cached_summary_dataframe(tmp_path, monkeypatch):
    artifact_paths = _build_precompute_artifact_paths(str(tmp_path), "coarse_cached")
    summary_df = pd.DataFrame(
        {
            "particle_name": ["cached"],
            "score": [1.0],
        }
    )
    call_count = 0

    def _fake_results_to_dataframe(results):
        nonlocal call_count
        call_count += 1
        assert results == [{"case_key": "case-1"}]
        return summary_df

    monkeypatch.setattr(
        precompute_module,
        "results_to_dataframe",
        _fake_results_to_dataframe,
    )
    save_context = PrecomputeSaveContext()
    save_steps = _build_precompute_save_steps(
        artifact_paths=artifact_paths,
        save_context=save_context,
        results=[{"case_key": "case-1"}],
        grid_name="coarse",
        config_tag="cached",
        particle_profile="quick",
        sim_cfg=build_precompute_sim_cfg("coarse"),
        grid=GRID_CONFIGS["coarse"],
        particle_types=get_precompute_particles("quick"),
        save_freeze_probe_report=False,
        artifact_profile="full",
    )

    summary_step = next(step for step in save_steps if step.output_key == "summary_csv")
    case_summary_step = next(
        step for step in save_steps if step.output_key == "case_summary_csv"
    )

    summary_payload = summary_step.build_payload()
    assert summary_step.after_write is not None
    summary_step.after_write(summary_payload)
    case_summary_payload = case_summary_step.build_payload()

    assert summary_payload is summary_df
    assert case_summary_payload is summary_df
    assert call_count == 1


def test_checkpoint_flush_interval_has_floor_for_time_based_flushes():
    assert not _should_flush_checkpoint(
        force=False,
        buffer_size=1,
        batch_size=100,
        last_flush_at=10.0,
        now=10.5,
        flush_interval_s=0.0,
    )
    assert _should_flush_checkpoint(
        force=False,
        buffer_size=1,
        batch_size=100,
        last_flush_at=10.0,
        now=11.0,
        flush_interval_s=0.0,
    )


def test_build_metadata_summarizes_reference_calibration_health():
    sim_cfg = deepcopy(DASHBOARD_DEFAULT_SIM_CFG)
    sim_cfg.reference_model = "calibrated_lookup"
    sim_cfg.reference_route = "calibrated_primary"
    sim_cfg.reference_calibration_path = "calibration/reference_blank_channel_template.csv"
    results = [
        {
            "reference": {
                "reference_calibration_amplitude_status": "absolute_calibrated",
                "reference_calibration_coverage_status": "covered",
                "reference_phase_calibration_status": (
                    "measured_or_fitted_phase_with_source"
                ),
                "rho_used_for_reference_amplitude": False,
            }
        },
        {
            "reference": {
                "reference_calibration_amplitude_status": "calibrated_scale_only",
                "reference_calibration_coverage_status": (
                    "extrapolated_nearest_fallback"
                ),
                "reference_phase_calibration_status": (
                    "model_assigned_or_unknown_phase"
                ),
                "rho_used_for_reference_amplitude": True,
            }
        },
    ]

    meta = build_metadata(
        "coarse",
        "calibrated_health_smoke",
        "quick",
        sim_cfg,
        GRID_CONFIGS["coarse"],
        get_precompute_particles("quick"),
        results,
    )

    health = meta["reference_calibration_health"]
    assert health["reference_calibration_active"] is True
    assert health["health_status"] == "active_with_extrapolated_cases"
    assert health["absolute_A_ref_case_count"] == 1
    assert health["scale_only_case_count"] == 1
    assert health["extrapolated_case_count"] == 1
    assert health["rho_dependent_reference_case_count"] == 1
    assert health["measured_or_fitted_phase_case_count"] == 1
    assert health["absolute_A_ref_case_fraction"] == pytest.approx(0.5)


def test_build_metadata_summarizes_collection_operator_calibration_health():
    sim_cfg = deepcopy(DASHBOARD_DEFAULT_SIM_CFG)
    sim_cfg.collection_operator_calibration_path = "calibration/operator_table.csv"
    sim_cfg.collection_operator_id = "opA"
    sim_cfg.absolute_throughput_route = "calibrated_operator_table"
    results = [
        {
            "intrinsic": {
                "operator_route": "calibrated_operator_table",
                "operator_normalization": (
                    "absolute_throughput_calibrated_operator_table"
                ),
                "collection_operator_calibration_status": (
                    "calibrated_operator_table_selected"
                ),
                "collection_operator_coverage_status": "covered_exact",
                "collection_operator_calibrated_geometry": True,
                "absolute_throughput_calibrated": True,
            }
        },
        {
            "intrinsic": {
                "operator_route": "calibrated_operator_table",
                "operator_normalization": "unit_normalized_calibrated_operator_geometry",
                "collection_operator_calibration_status": (
                    "calibrated_operator_table_selected"
                ),
                "collection_operator_coverage_status": "extrapolated_nearest_row",
                "collection_operator_calibrated_geometry": True,
                "absolute_throughput_calibrated": False,
            }
        },
    ]

    meta = build_metadata(
        "coarse",
        "operator_health_smoke",
        "quick",
        sim_cfg,
        GRID_CONFIGS["coarse"],
        get_precompute_particles("quick"),
        results,
    )

    health = meta["collection_operator_calibration_health"]
    assert health["collection_operator_calibration_path_configured"] is True
    assert health["collection_operator_id"] == "opA"
    assert health["health_status"] == "active_with_extrapolated_operator_cases"
    assert health["calibrated_geometry_case_count"] == 2
    assert health["absolute_throughput_case_count"] == 1
    assert health["extrapolated_operator_case_count"] == 1
    assert health["absolute_throughput_case_fraction"] == pytest.approx(0.5)


def test_particle_model_provenance_exports_to_precompute_and_breakdown():
    results = [_mock_dashboard_engineering_result()]
    results[0]["summary"].update(
        {
            "detector_operator_caution_reason": (
                "detector_operator_large_or_missing_blocks_absolute_claim_only"
            ),
            "detector_resolved_relative_design_eligible": False,
            "relative_design_with_detector_caution": True,
        }
    )

    df = results_to_dataframe(results)
    design_df = results_to_design_postprocess_dataframe(results)
    physics_df = results_to_physics_fields_dataframe(results)
    diagnostics_long = results_to_diagnostics_long_dataframe(results)
    compact = results_to_compact(results)
    breakdown = build_physics_breakdown(_mock_dashboard_breakdown_case())
    physics = breakdown["case_physics"]

    _assert_precompute_engineering_dataframe_columns(df)
    assert df.iloc[0]["particle_family"] == "gold"
    assert df.iloc[0]["particle_optical_model"] == "homogeneous_mie_sphere"
    assert (
        df.iloc[0]["particle_uncertainty_budget_status"]
        == "nominal_only_uncertainty_not_propagated"
    )
    assert df.iloc[0]["uncertainty_propagation_mode"] == "none"
    assert "phase_filter_validity" in df.columns
    assert "subwavelength_groove_validity_status" in df.columns
    assert "selected_detector_mode_annulus_detection_rate" in df.columns
    assert (
        "selected_detector_mode_annulus_detection_rate"
        in diagnostics_long["field"].tolist()
    )
    assert df.iloc[0]["interface_correction_mode"] == "off"
    assert (
        df.iloc[0]["interface_correction_status"]
        == "homogeneous_medium_mie_no_interface_correction"
    )
    assert (
        df.iloc[0]["interface_output_sensitivity_status"]
        == "phase_polarity_and_angular_pattern_sensitive"
    )
    assert bool(df.iloc[0]["interface_fullwave_required"]) is True
    assert (
        df.iloc[0]["count_generation_model"]
        == "per_event_batch_plus_optional_poisson_flux"
    )
    assert (
        df.iloc[0]["per_event_detectability_boundary"]
        == "conditional_detection_rate_not_experiment_count_rate"
    )
    assert df.iloc[0]["count_prediction_model"] == "not_applied"
    assert df.iloc[0]["count_prediction_status"] == "not_applied_per_event_detection_only"
    assert (
        df.iloc[0]["poisson_arrival_process_status"]
        == "not_applied_count_prediction_disabled"
    )
    assert (
        df.iloc[0]["crossing_conditioned_transport_status"]
        == "not_implemented_uses_existing_per_event_initial_distribution"
    )
    assert df.iloc[0]["accessible_area_m2"] == pytest.approx(3.384e-13)
    assert df.iloc[0]["predicted_count_rate_Hz"] is None
    assert (
        df.iloc[0]["count_rate_confidence_status"]
        == "not_available_no_blank_false_positive_or_uncertainty_propagation"
    )
    assert df.iloc[0]["thermal_pod_model"] == "unavailable"
    assert (
        df.iloc[0]["thermal_pod_model_status"]
        == "unavailable_no_heat_diffusion_model"
    )
    assert bool(df.iloc[0]["pod_quantitative_amplitude_available"]) is False
    assert df.iloc[0]["pod_quantitative_route_status"] == (
        "blocked_missing_thermal_forward_model_or_calibration"
    )
    assert df.iloc[0]["pod_probe_reference_field_status"] == (
        "probe_E_ref_E_sca_use_current_optical_wavelength"
    )
    assert df.iloc[0]["pod_heat_source_status"] == (
        "not_available_missing_excitation_wavelength_or_power"
    )
    assert df.iloc[0]["pod_roi_sensitivity_derivative_status"] == "unavailable"
    assert df.iloc[0]["pod_signal_sign_source"] == "unavailable"
    assert compact[0]["physics"]["particle_family"] == "gold"
    assert compact[0]["physics"]["particle_optical_model"] == "homogeneous_mie_sphere"
    assert compact[0]["physics"]["peak_height_CI_available"] is False
    assert compact[0]["physics"]["interface_correction_mode"] == "off"
    assert (
        compact[0]["physics"]["interface_output_sensitivity_status"]
        == "phase_polarity_and_angular_pattern_sensitive"
    )
    assert compact[0]["physics"]["interface_fullwave_required"] is True
    assert (
        compact[0]["physics"]["count_generation_model"]
        == "per_event_batch_plus_optional_poisson_flux"
    )
    assert compact[0]["physics"]["count_prediction_model"] == "not_applied"
    assert compact[0]["physics"]["poisson_arrival_process_status"] == (
        "not_applied_count_prediction_disabled"
    )
    assert compact[0]["physics"]["crossing_conditioned_transport_status"] == (
        "not_implemented_uses_existing_per_event_initial_distribution"
    )
    assert compact[0]["physics"]["control_interpretation_status"] == (
        "risk_interpretation_scaffold_active_missing_controls"
    )
    assert compact[0]["physics"]["control_failure_interpretation_gate_passed"] is False
    assert compact[0]["physics"]["fluidic_network_model_status"] == (
        "partial_network_nanochannel_array_only"
    )
    assert compact[0]["physics"]["fluidic_network_gate_passed"] is False
    assert compact[0]["physics"]["wall_interaction_status"] == "wall_interaction_unmodeled"
    assert compact[0]["physics"]["thermal_pod_model"] == "unavailable"
    assert compact[0]["physics"]["pod_quantitative_amplitude_available"] is False
    assert compact[0]["physics"]["pod_quantitative_route_status"] == (
        "blocked_missing_thermal_forward_model_or_calibration"
    )
    assert compact[0]["physics"]["pod_heat_source_status"] == (
        "not_available_missing_excitation_wavelength_or_power"
    )
    assert compact[0]["physics"]["probe_coherent_field_group_id"] == "probe_660nm"
    assert compact[0]["physics"]["pod_wavelength_grouping_status"] == (
        "single_probe_no_excitation_configured"
    )
    assert compact[0]["physics"]["incident_field_model_for_mie"] == "local_plane_wave"
    assert compact[0]["physics"]["local_plane_wave_validity"] == "valid_for_ranking"
    assert compact[0]["physics"]["na_cutoff_policy"] == "hard_guardrail"
    assert compact[0]["physics"]["na_cutoff_hard_zero_applied"] is False
    assert {
        "particle_name",
        "EV_design_claim_allowed_text",
        "EV_design_claim_forbidden_text",
    }.issubset(design_df.columns)
    assert "真实 detector voltage" in design_df.iloc[0]["EV_design_claim_forbidden_text"]
    assert {"particle_name", "A_ref", "detector_forward_model"}.issubset(
        physics_df.columns
    )
    assert "control_interpretation_status" in physics_df.columns
    assert "fluidic_network_pressure_flow_relation_status" in physics_df.columns
    assert {"particle_name", "field", "value", "diagnostic_group"}.issubset(
        diagnostics_long.columns
    )
    assert "control_interpretation" in set(
        diagnostics_long["diagnostic_group"].dropna()
    )
    assert (
        "fluidic_network_model"
        in set(diagnostics_long["diagnostic_group"].dropna())
    )
    readout_rows = diagnostics_long[
        diagnostics_long["diagnostic_group"] == "readout_convention"
    ]
    assert "readout_preset" in set(readout_rows["field"])
    design_claim_rows = diagnostics_long[
        diagnostics_long["diagnostic_group"] == "minimum_design_claim_schema"
    ]
    assert "detector_operator_caution_reason" in set(design_claim_rows["field"])
    assert "detector_resolved_relative_design_eligible" in set(
        design_claim_rows["field"]
    )
    assert "relative_design_with_detector_caution" in set(design_claim_rows["field"])
    assert physics["particle family"] == "gold"
    assert physics["particle optical model"] == "homogeneous_mie_sphere"
    assert physics["EV claim level"] == "not_applicable"
    assert physics["EV ensemble mode"] == "nominal_single_preset"
    assert (
        physics["particle uncertainty budget"]
        == "nominal_only_uncertainty_not_propagated"
    )
    assert physics["uncertainty propagation mode"] == "none"
    assert physics["interface correction mode"] == "off"
    assert (
        physics["interface correction status"]
        == "homogeneous_medium_mie_no_interface_correction"
    )
    assert (
        physics["interface output sensitivity"]
        == "phase_polarity_and_angular_pattern_sensitive"
    )
    assert physics["interface full-wave required"] is True
    assert "homogeneous_medium_interface_unmodeled" in physics[
        "interface quantitative blockers"
    ]
    assert physics["count generation model"] == (
        "per_event_batch_plus_optional_poisson_flux"
    )
    assert physics["per-event detectability boundary"] == (
        "conditional_detection_rate_not_experiment_count_rate"
    )
    assert physics["count prediction model"] == "not_applied"
    assert (
        physics["count prediction status"]
        == "not_applied_per_event_detection_only"
    )
    assert physics["Poisson arrival process"] == "not_applied_count_prediction_disabled"
    assert physics["crossing-conditioned transport"] == (
        "not_implemented_uses_existing_per_event_initial_distribution"
    )
    assert physics["predicted count rate Hz"] is None
    assert physics["count-rate confidence"] == (
        "not_available_no_blank_false_positive_or_uncertainty_propagation"
    )
    assert physics["wall interaction status"] == "wall_interaction_unmodeled"
    assert physics["control interpretation status"] == (
        "risk_interpretation_scaffold_active_missing_controls"
    )
    assert physics["control interpretation gate"] is False
    assert "control_outcome_data_not_ingested" in physics[
        "control interpretation blockers"
    ]
    assert physics["fluidic network status"] == (
        "partial_network_nanochannel_array_only"
    )
    assert physics["fluidic network pressure-flow relation"] == (
        "blocked_until_measured_pressure_flow_trace"
    )
    assert physics["fluidic network pressure-flow gate"] is False
    assert physics["thermal POD model"] == "unavailable"
    assert physics["thermal POD status"] == "unavailable_no_heat_diffusion_model"
    assert physics["POD quantitative amplitude available"] is False
    assert physics["POD quantitative route status"] == (
        "blocked_missing_thermal_forward_model_or_calibration"
    )
    assert physics["POD probe reference field status"] == (
        "probe_E_ref_E_sca_use_current_optical_wavelength"
    )
    assert physics["POD heat source status"] == (
        "not_available_missing_excitation_wavelength_or_power"
    )
    assert physics["POD detector responsivity status"] == (
        "not_configured_by_probe_wavelength"
    )
    assert physics["POD ROI derivative status"] == "unavailable"
    assert physics["POD sign source"] == "unavailable"
    assert physics["probe coherent field group"] == "probe_660nm"
    assert physics["POD wavelength grouping status"] == (
        "single_probe_no_excitation_configured"
    )
    assert physics["Mie incident field model"] == "local_plane_wave"
    assert physics["local plane wave validity"] == "valid_for_ranking"
    assert physics["Mie incident blockers"] == "none"
    assert physics["NA cutoff policy"] == "hard_guardrail"
    assert physics["NA hard zero applied"] is False


def test_precompute_readout_fields_fallback_to_summary_payload():
    result = _mock_dashboard_engineering_result()
    for payload_name in ("intrinsic", "reference"):
        result[payload_name].pop("readout_preset", None)
        result[payload_name].pop("readout_numerical_route", None)
    result["summary"]["readout_preset"] = "EV_NODI_only_design"
    result["summary"]["readout_numerical_route"] = (
        "bandpass_envelope_response_surrogate"
    )

    df = results_to_dataframe([result])
    physics_df = results_to_physics_fields_dataframe([result])

    assert df.iloc[0]["readout_preset"] == "EV_NODI_only_design"
    assert (
        df.iloc[0]["readout_numerical_route"]
        == "bandpass_envelope_response_surrogate"
    )
    assert physics_df.iloc[0]["readout_preset"] == "EV_NODI_only_design"
    assert (
        physics_df.iloc[0]["readout_numerical_route"]
        == "bandpass_envelope_response_surrogate"
    )


def test_precompute_artifact_paths_include_p012_split_exports(tmp_path):
    prefix = "fine_current_model_full_range"
    paths = _build_precompute_artifact_paths(str(tmp_path), prefix)

    assert paths.summary_csv.endswith(f"{prefix}_summary.csv")
    assert paths.case_summary_csv.endswith(f"{prefix}_case_summary.csv")
    assert paths.case_summary_parquet.endswith(f"{prefix}_case_summary.parquet")
    assert paths.design_postprocess_csv.endswith(f"{prefix}_design_postprocess.csv")
    assert paths.physics_fields_parquet.endswith(f"{prefix}_physics_fields.parquet")
    assert paths.diagnostics_long_parquet.endswith(f"{prefix}_diagnostics_long.parquet")


def test_precompute_sweep_writes_p012_split_exports(tmp_path, monkeypatch):
    pytest.importorskip("pyarrow")
    import nodi_simulator.dashboard.precompute as precompute_mod

    monkeypatch.setitem(
        precompute_mod.GRID_CONFIGS,
        "coarse",
        {
            "width_list_m": np.array([800e-9]),
            "depth_list_m": np.array([550e-9]),
            "wavelength_list_m": np.array([660e-9]),
            "n_events": 1,
        },
    )
    out_dir = tmp_path / "precompute_artifacts"

    precompute_sweep(
        grid_name="coarse",
        config_tag="p012",
        particle_profile="quick",
        output_dir=str(out_dir),
        n_workers=1,
        save_freeze_probe_report=False,
        progress_interval_s=0.1,
        checkpoint_enabled=False,
        artifact_profile="full",
    )

    prefix = "coarse_p012"
    assert (out_dir / f"{prefix}_summary.csv").exists()
    assert (out_dir / f"{prefix}_case_summary.csv").exists()
    assert (out_dir / f"{prefix}_design_postprocess.csv").exists()
    assert (out_dir / f"{prefix}_case_summary.parquet").exists()
    assert (out_dir / f"{prefix}_physics_fields.parquet").exists()
    assert (out_dir / f"{prefix}_diagnostics_long.parquet").exists()
    assert len(pd.read_parquet(out_dir / f"{prefix}_case_summary.parquet")) > 0
    assert "field" in pd.read_parquet(out_dir / f"{prefix}_diagnostics_long.parquet").columns


def test_precompute_sweep_default_standard_artifact_profile_skips_heavy_exports(tmp_path, monkeypatch):
    import nodi_simulator.dashboard.precompute as precompute_mod

    monkeypatch.setitem(
        precompute_mod.GRID_CONFIGS,
        "coarse",
        {
            "width_list_m": np.array([800e-9]),
            "depth_list_m": np.array([550e-9]),
            "wavelength_list_m": np.array([660e-9]),
            "n_events": 1,
        },
    )
    out_dir = tmp_path / "precompute_artifacts"

    precompute_sweep(
        grid_name="coarse",
        config_tag="standard_artifacts",
        particle_profile="quick",
        output_dir=str(out_dir),
        n_workers=1,
        save_freeze_probe_report=True,
        progress_interval_s=0.1,
        checkpoint_enabled=False,
    )

    prefix = "coarse_standard_artifacts"
    assert (out_dir / f"{prefix}_summary.csv").exists()
    assert (out_dir / f"{prefix}_design_postprocess.csv").exists()
    assert (out_dir / f"{prefix}_compact.pkl").exists()
    assert (out_dir / f"{prefix}_meta.json").exists()
    assert (out_dir / f"{prefix}_result_health.json").exists()
    assert (out_dir / f"{prefix}_runtime_performance.json").exists()
    assert (out_dir / f"{prefix}_freeze_probe.json").exists()
    assert not (out_dir / f"{prefix}_case_summary.csv").exists()
    assert not (out_dir / f"{prefix}_case_summary.parquet").exists()
    assert not (out_dir / f"{prefix}_physics_fields.parquet").exists()
    assert not (out_dir / f"{prefix}_diagnostics_long.parquet").exists()

    meta = json.loads((out_dir / f"{prefix}_meta.json").read_text(encoding="utf-8"))
    manifest = meta["export_format_manifest"]
    assert manifest["artifact_profile"] == "standard"
    assert "summary_csv" in manifest["enabled_exports"]
    assert "runtime_performance_json" in manifest["enabled_exports"]
    assert "case_summary_csv" in manifest["skipped_optional_exports"]
    assert manifest["parquet_export_status"] in {
        "parquet_exports_skipped_by_artifact_profile",
        "parquet_exports_skipped_missing_engine",
    }
    runtime_report = json.loads(
        (out_dir / f"{prefix}_runtime_performance.json").read_text(encoding="utf-8")
    )
    assert runtime_report["runtime_performance_schema"] == (
        "precompute_runtime_performance_v1"
    )
    assert runtime_report["run"]["saved_cases"] == 2
    assert runtime_report["throughput"]["sweep_cases_per_second"] is not None
    assert runtime_report["case_runtime_seconds"]["count"] == 2
    assert runtime_report["vectorized_fallback_telemetry"]["case_count"] == 2
    assert (
        runtime_report["optimization_watch_items"][
            "event_loop_fallback_fraction_of_vectorized_requested_cases"
        ]
        >= 0.0
    )
    assert "slowest_cases" in runtime_report


def test_single_case_state_defaults_follow_dashboard_default_config():
    with _SessionStateGuard():
        _seed_single_case_state()
        assert st.session_state["single_case_include_diffusion"] is True
        assert st.session_state["single_case_rho"] == pytest.approx(
            max(1.0, float(DASHBOARD_DEFAULT_SIM_CFG.rho))
        )
        assert st.session_state["single_case_noise_std"] == pytest.approx(
            float(DASHBOARD_DEFAULT_SIM_CFG.noise_std)
        )
        assert st.session_state["single_case_threshold_sigma"] == pytest.approx(
            float(DASHBOARD_DEFAULT_SIM_CFG.threshold_sigma)
        )
        assert st.session_state["single_case_velocity_mm_s"] == pytest.approx(
            float(DASHBOARD_DEFAULT_SIM_CFG.mean_flow_velocity_m_s * 1e3)
        )


def test_dashboard_prefers_ev_design_anchor_dataset_when_available():
    prefixes = [
        "fine_full_range",
        "fine_fine_full_range_10000e",
        "fine_full_range_biomimetic_exosome_10000e",
        "ev_design_full_range_biomimetic_exosome_with_anchors_10000e",
    ]
    assert (
        resolve_preferred_dataset_prefix(prefixes)
        == "ev_design_full_range_biomimetic_exosome_with_anchors_10000e"
    )


def test_dashboard_launchers_reference_current_standard_dataset_and_not_legacy_defaults():
    current_prefix = "ev_design_full_range_biomimetic_exosome_with_anchors_10000e"
    legacy_markers = (
        "coarse_default_summary",
        "coarse_full_range_summary",
        "--grid coarse",
        "--particle-profile full_range --tag full_range",
        "fine_full_range_summary.csv",
    )
    for path in (MAC_LAUNCHER_PATH, WIN_LAUNCHER_PATH):
        text = path.read_text(encoding="utf-8")
        assert current_prefix in text
        for marker in legacy_markers:
            assert marker not in text


def test_dashboard_common_session_helpers_share_case_context():
    with _SessionStateGuard():
        initialize_dashboard_session_state("coarse_full_range")
        assert st.session_state["data_prefix"] == "coarse_full_range"
        assert get_active_data_source_tag() == "coarse_full_range"
        assert get_selected_case_context() is None

        set_selected_case_context(
            particle_name="gold_80nm",
            wavelength_nm=660,
            width_nm=800,
            depth_nm=550,
        )
        context = get_selected_case_context()
        assert context is not None
        assert context["particle_name"] == "gold_80nm"
        assert context["particle_label"] is not None

        st.session_state["using_live_data"] = True
        st.session_state["live_tag"] = "live-probe"
        assert get_active_data_source_tag() == "live-probe"


def test_single_case_state_seeds_from_workflow_but_stays_separate():
    with _SessionStateGuard():
        initialize_dashboard_session_state("fine_full_range")
        set_selected_case_context(
            particle_name="gold_200nm",
            wavelength_nm=660,
            width_nm=920,
            depth_nm=610,
        )
        _seed_single_case_state()
        assert st.session_state["single_case_material"] == "gold"
        assert st.session_state["single_case_diameter_nm"] == 200
        assert st.session_state["single_case_wavelength_nm"] == 660
        assert st.session_state["single_case_width_nm"] == 920
        assert st.session_state["single_case_depth_nm"] == 610
        assert st.session_state["selected_particle"] == "gold_200nm"
        assert st.session_state["selected_W_nm"] == 920
        assert st.session_state["selected_H_nm"] == 610


def test_single_case_state_only_reimports_workflow_when_forced():
    with _SessionStateGuard():
        initialize_dashboard_session_state("fine_full_range")
        set_selected_case_context(
            particle_name="gold_200nm",
            wavelength_nm=660,
            width_nm=920,
            depth_nm=610,
        )
        _seed_single_case_state()
        st.session_state["single_case_material"] = "exosome"
        st.session_state["single_case_diameter_nm"] = 150
        st.session_state["single_case_wavelength_nm"] = 532
        st.session_state["single_case_width_nm"] = 1100
        st.session_state["single_case_depth_nm"] = 700
        set_selected_case_context(
            particle_name="gold_80nm",
            wavelength_nm=488,
            width_nm=800,
            depth_nm=550,
        )

        _seed_single_case_state()
        assert st.session_state["single_case_material"] == "exosome"
        assert st.session_state["single_case_diameter_nm"] == 150
        assert st.session_state["single_case_wavelength_nm"] == 532

        _seed_single_case_state(force_from_workflow=True)
        assert st.session_state["single_case_material"] == "gold"
        assert st.session_state["single_case_diameter_nm"] == 80
        assert st.session_state["single_case_wavelength_nm"] == 488
        assert st.session_state["single_case_width_nm"] == 800
        assert st.session_state["single_case_depth_nm"] == 550


def test_single_case_report_builder_does_not_rewrite_workflow_selection():
    with _SessionStateGuard():
        initialize_dashboard_session_state("fine_full_range")
        set_selected_case_context(
            particle_name="gold_200nm",
            wavelength_nm=660,
            width_nm=920,
            depth_nm=610,
        )
        st.session_state["single_case_material"] = "exosome"
        st.session_state["single_case_diameter_nm"] = 120
        st.session_state["single_case_wavelength_nm"] = 532
        st.session_state["single_case_width_nm"] = 1000
        st.session_state["single_case_depth_nm"] = 650
        st.session_state["single_case_n_events"] = 4
        st.session_state["single_case_rho"] = float(DEFAULT_SIM_CFG.rho)
        st.session_state["single_case_include_diffusion"] = bool(DEFAULT_SIM_CFG.include_diffusion)
        st.session_state["single_case_noise_std"] = float(DEFAULT_SIM_CFG.noise_std)
        st.session_state["single_case_threshold_sigma"] = float(DEFAULT_SIM_CFG.threshold_sigma)
        st.session_state["single_case_velocity_mm_s"] = float(DEFAULT_SIM_CFG.mean_flow_velocity_m_s * 1e3)

        report = _build_single_case_report_from_state()
        assert report["meta"]["material"] == "exosome"
        assert report["meta"]["diameter_nm"] == 120
        assert st.session_state["selected_particle"] == "gold_200nm"
        assert st.session_state["selected_wavelength_nm"] == 660
        assert st.session_state["selected_W_nm"] == 920
        assert st.session_state["selected_H_nm"] == 610


def test_sync_dashboard_data_prefix_prefers_current_standard_and_preserves_custom_choice():
    state = {"data_prefix": "missing_prefix"}
    chosen = sync_dashboard_data_prefix(
        state,
        [
            "coarse_default",
            "fine_full_range",
            "ev_design_full_range_biomimetic_exosome_with_anchors_10000e",
        ],
    )
    assert chosen == "ev_design_full_range_biomimetic_exosome_with_anchors_10000e"
    assert state["data_prefix"] == "ev_design_full_range_biomimetic_exosome_with_anchors_10000e"

    chosen = sync_dashboard_data_prefix(
        state,
        [
            "coarse_default",
            "fine_full_range",
            "ev_design_full_range_biomimetic_exosome_with_anchors_10000e",
        ],
    )
    assert chosen == "ev_design_full_range_biomimetic_exosome_with_anchors_10000e"

    explicit_state = {"data_prefix": "coarse_default"}
    chosen = sync_dashboard_data_prefix(
        explicit_state,
        [
            "coarse_default",
            "fine_full_range",
            "ev_design_full_range_biomimetic_exosome_with_anchors_10000e",
        ],
    )
    assert chosen == "ev_design_full_range_biomimetic_exosome_with_anchors_10000e"
    assert explicit_state["data_prefix"] == "ev_design_full_range_biomimetic_exosome_with_anchors_10000e"

    legacy_only_state = {"data_prefix": "missing_prefix"}
    chosen = sync_dashboard_data_prefix(
        legacy_only_state,
        ["coarse_default", "coarse_full_range", "fine_full_range"],
    )
    assert chosen == "coarse_default"
    assert legacy_only_state["data_prefix"] == "coarse_default"

    custom_state = {"data_prefix": "experiment_probe"}
    chosen = sync_dashboard_data_prefix(
        custom_state,
        ["experiment_probe", "ev_design_full_range_biomimetic_exosome_with_anchors_10000e"],
    )
    assert chosen == "experiment_probe"
    assert custom_state["data_prefix"] == "experiment_probe"


def test_load_dashboard_data_bundle_uses_live_session_payloads():
    with _SessionStateGuard():
        live_df = pd.DataFrame(
            [
                {
                    "particle_name": "gold_80nm",
                    "wavelength_nm": 660,
                    "width_nm": 800,
                    "depth_nm": 550,
                    "score": 1.0,
                    "final_engineering_score": 1.1,
                    "engineering_gate_passed": True,
                    "observation_freeze_status": "default_ready_for_result_freeze",
                    "delta_phi_gouy_validity": "shared_beam_acceptable",
                    "rho_physical_envelope_status": "within_envelope",
                    "reference_width_saturation_status": "active_soft_cutoff",
                    "reference_width_saturation_factor": 1.1,
                }
            ]
        )
        st.session_state["using_live_data"] = True
        st.session_state["live_tag"] = "live-bundle"
        st.session_state["sweep_df_live"] = live_df
        st.session_state["sweep_compact_live"] = [{"particle_name": "gold_80nm"}]

        bundle = load_dashboard_data_bundle(
            "unused-results-dir",
            st.session_state,
            include_compact=True,
        )
        assert bundle.source.is_live is True
        assert bundle.source.tag == "live-bundle"
        assert "live sweep" in bundle.source.summary_caption.lower()
        assert bundle.compact == [{"particle_name": "gold_80nm"}]
        assert "particle_material" in bundle.df.columns
        assert "particle_diameter_nm" in bundle.df.columns
        assert bundle.health_report is not None


def test_check_data_files_rejects_path_like_prefix(tmp_path):
    with pytest.raises(ValueError, match="data_prefix"):
        check_data_files(str(tmp_path), "../escape")


def test_check_data_files_rejects_stale_standard_wavelength_set(tmp_path):
    prefix = "ev_design_full_range_biomimetic_exosome_with_anchors_10000e"
    pd.DataFrame({"particle_name": ["gold_20nm"]}).to_csv(
        tmp_path / f"{prefix}_summary.csv",
        index=False,
    )
    with open(tmp_path / f"{prefix}_compact.pkl", "wb") as f:
        dump_dashboard_pickle(f, [])
    (tmp_path / f"{prefix}_meta.json").write_text(
        json.dumps(
            {
                "dashboard_schema_version": CURRENT_SCHEMA_VERSION,
                "wavelengths_nm": [488, 532, 660],
                "n_cases": 7056,
                "sweep_completion_policy": {"expected_total_cases": 7056},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="wavelength mismatch"):
        check_data_files(str(tmp_path), prefix)


def test_check_data_files_rejects_stale_standard_geometry_case_count(tmp_path):
    prefix = "ev_design_full_range_biomimetic_exosome_with_anchors_10000e"
    pd.DataFrame({"particle_name": ["gold_20nm"]}).to_csv(
        tmp_path / f"{prefix}_summary.csv",
        index=False,
    )
    with open(tmp_path / f"{prefix}_compact.pkl", "wb") as f:
        dump_dashboard_pickle(f, [])
    (tmp_path / f"{prefix}_meta.json").write_text(
        json.dumps(
            {
                "dashboard_schema_version": CURRENT_SCHEMA_VERSION,
                "wavelengths_nm": [404, 488, 532, 660],
                "n_cases": 9408,
                "sweep_completion_policy": {"expected_total_cases": 9408},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="case-count mismatch"):
        check_data_files(str(tmp_path), prefix)


def test_list_available_datasets_ignores_unsafe_summary_prefixes(tmp_path):
    (tmp_path / "coarse_safe_summary.csv").write_text("", encoding="utf-8")
    (tmp_path / ".._unsafe_summary.csv").write_text("", encoding="utf-8")
    (tmp_path / "bad name_summary.csv").write_text("", encoding="utf-8")

    assert list_available_datasets(str(tmp_path)) == ["coarse_safe"]


def test_load_dashboard_data_bundle_prefers_case_summary_parquet(tmp_path):
    pytest.importorskip("pyarrow")
    prefix = "coarse_parquet"
    csv_df = pd.DataFrame(
        [
            {
                "particle_name": "csv_case",
                "wavelength_nm": 488,
                "width_nm": 500,
                "depth_nm": 600,
                "score": 0.1,
            }
        ]
    )
    parquet_df = csv_df.copy()
    parquet_df["particle_name"] = ["parquet_case"]

    csv_df.to_csv(tmp_path / f"{prefix}_summary.csv", index=False)
    parquet_df.to_parquet(tmp_path / f"{prefix}_case_summary.parquet", index=False)
    with open(tmp_path / f"{prefix}_compact.pkl", "wb") as f:
        dump_dashboard_pickle(f, [])
    (tmp_path / f"{prefix}_meta.json").write_text(
        json.dumps({"dashboard_schema_version": CURRENT_SCHEMA_VERSION}),
        encoding="utf-8",
    )
    (tmp_path / f"{prefix}_result_health.json").write_text(
        json.dumps({"status": "ok"}),
        encoding="utf-8",
    )

    bundle = load_dashboard_data_bundle(
        str(tmp_path),
        {"using_live_data": False, "data_prefix": prefix},
    )

    assert bundle.df["particle_name"].tolist() == ["parquet_case"]


def test_lookup_summary_case_row_matches_selected_case_geometry():
    df = pd.DataFrame(
        [
            {
                "particle_name": "gold_80nm",
                "wavelength_nm": 660,
                "width_nm": 800,
                "depth_nm": 550,
                "score": 1.0,
            },
            {
                "particle_name": "exosome_120nm",
                "wavelength_nm": 488,
                "width_nm": 900,
                "depth_nm": 650,
                "score": 2.0,
            },
        ]
    )
    row = lookup_summary_case_row(
        df,
        particle_name="exosome_120nm",
        wavelength_nm=488,
        width_nm=900,
        depth_nm=650,
    )
    assert row is not None
    assert row["score"] == pytest.approx(2.0)
    assert (
        lookup_summary_case_row(
            df,
            particle_name="exosome_120nm",
            wavelength_nm=660,
            width_nm=900,
            depth_nm=650,
        )
        is None
    )


def test_build_dashboard_data_source_uses_standard_full_range_captions():
    source = build_dashboard_data_source(
        {
            "using_live_data": False,
            "data_prefix": "ev_design_full_range_biomimetic_exosome_with_anchors_10000e",
        }
    )
    assert source.is_live is False
    assert source.prefix == "ev_design_full_range_biomimetic_exosome_with_anchors_10000e"
    assert "full-range" in source.summary_caption
    assert "ev_design_full_range_biomimetic_exosome_with_anchors_10000e" in source.detail_caption


def test_build_dashboard_data_source_marks_old_full_range_as_compatibility():
    source = build_dashboard_data_source(
        {
            "using_live_data": False,
            "data_prefix": "fine_full_range",
        }
    )
    assert source.is_live is False
    assert source.prefix == "fine_full_range"
    assert "兼容结果库" in source.summary_caption


def _mock_dashboard_engineering_result():
    return shared_mock_dashboard_engineering_result()


def _mock_dashboard_breakdown_case():
    return shared_mock_dashboard_breakdown_case()

def _build_minimal_live_case():
    sim_cfg = build_sim_cfg_from_ui(
        10.0, 0.5, 0.3, 1.0,
        0.01, 0.001, 5.0,
        0.2, True,
        "geometry_scaled", "gaussian_xy",
        "per_wavelength", "gaussian_plus_drift",
    )
    optical = build_optical_from_ui(700.0)
    particle = make_particle("gold", 80)
    grid = {
        "width_list_m": np.array([800e-9]),
        "depth_list_m": np.array([550e-9]),
        "wavelength_list_m": np.array([660e-9]),
        "n_events": 4,
        "grid_name": "test_single_case",
    }
    df, compact = run_live_sweep_custom(sim_cfg, optical, particle, grid)
    return {
        "live_sim_cfg": sim_cfg,
        "live_optical": optical,
        "sweep_df_live": df,
        "sweep_compact_live": compact,
        "live_tag": "apptest",
        "using_live_data": True,
        "selected_particle": particle.name,
        "selected_wavelength_nm": 660,
        "selected_W_nm": 800,
        "selected_H_nm": 550,
    }


class TestDashboardWorkflow:
    def _write_surrogate_reference_calibration(self, tmp_path: Path) -> str:
        sample_points = [
            (800.0, 550.0, 660.0),
            (900.0, 550.0, 488.0),
            (1000.0, 650.0, 532.0),
            (1100.0, 650.0, 660.0),
        ]
        cfg = deepcopy(DEFAULT_SIM_CFG)
        cfg.reference_model = "channel_angular_surrogate"
        cfg.collection_angle_model = "channel_diffraction"
        cfg.collection_integration_mode = "pupil_slit_surrogate"

        path = tmp_path / "surrogate_reference.csv"
        lines = ["width_nm,depth_nm,wavelength_nm,g_ref,A_ref,phi_ref_rad"]
        for width_nm, depth_nm, wavelength_nm in sample_points:
            optical = deepcopy(OPTICAL_TEMPLATE)
            optical.wavelength_m = wavelength_nm * 1e-9
            ref = compute_reference_field(
                Channel(width_nm * 1e-9, depth_nm * 1e-9),
                optical,
                cfg,
                medium_refractive_index=1.33,
            )
            lines.append(
                f"{width_nm:.0f},{depth_nm:.0f},{wavelength_nm:.0f},"
                f"{ref['g_ref']:.12e},{ref['A_ref']:.12e},{ref['phi_ref_rad']:.12e}"
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return str(path)

    def test_dashboard_prefers_calibrated_lookup_default_when_calibration_path_present(self, monkeypatch, tmp_path):
        calibration_path = tmp_path / "reference.csv"
        calibration_path.write_text(
            "width_nm,depth_nm,wavelength_nm,g_ref,A_ref,phi_ref_rad\n"
            "800,550,660,1.2,12.0,0.1\n",
            encoding="utf-8",
        )

        import nodi_simulator.dashboard.config as cfg_mod

        monkeypatch.setenv("NODI_REFERENCE_CALIBRATION_PATH", str(calibration_path))
        importlib.reload(cfg_mod)
        try:
            assert cfg_mod.DEFAULT_REFERENCE_MODEL == "calibrated_lookup"
            assert cfg_mod.DEFAULT_REFERENCE_ROUTE == "calibrated_primary"
            assert cfg_mod.DEFAULT_SIM_CFG.reference_model == "calibrated_lookup"
            assert cfg_mod.DEFAULT_SIM_CFG.reference_route == "calibrated_primary"
            assert "calibrated_lookup" in cfg_mod.REFERENCE_MODEL_OPTIONS
            assert (
                cfg_mod.DEFAULT_REFERENCE_MODEL_INDEX
                == cfg_mod.REFERENCE_MODEL_OPTIONS.index("calibrated_lookup")
            )
        finally:
            monkeypatch.delenv("NODI_REFERENCE_CALIBRATION_PATH", raising=False)
            importlib.reload(cfg_mod)

    def test_dashboard_no_calibration_default_is_explicit_engineering_fallback(self, monkeypatch):
        import nodi_simulator.dashboard.config as cfg_mod

        monkeypatch.delenv("NODI_REFERENCE_CALIBRATION_PATH", raising=False)
        importlib.reload(cfg_mod)
        try:
            assert cfg_mod.DEFAULT_REFERENCE_MODEL == "channel_angular_surrogate"
            assert cfg_mod.DEFAULT_REFERENCE_ROUTE == "engineering_fallback"
            assert cfg_mod.DEFAULT_SIM_CFG.reference_route == "engineering_fallback"
            assert cfg_mod.REFERENCE_ROUTE_WARNING["status"] == "engineering_fallback_no_blank_calibration"
            assert "tsuyama_bfp_integrated" in cfg_mod.REFERENCE_MODEL_OPTIONS
        finally:
            importlib.reload(cfg_mod)

    def test_mie_case_positive_cross_sections(self):
        case = compute_mie_case("gold", 80, 660)
        assert case["size_parameter"] > 0
        assert case["Csca_m2"] >= 0
        assert case["Cext_m2"] >= 0
        assert case["Cabs_m2"] >= 0
        assert len(case["theta_deg"]) == len(case["dCsca_dOmega_m2_sr"])

    def test_mie_summary_dataframe_shape(self):
        df = build_mie_summary_dataframe(["gold", "exosome"], [40, 100], [488, 660], summary_theta_deg=37.5)
        assert len(df) == 8
        assert {
            "material",
            "diameter_nm",
            "wavelength_nm",
            "Csca_m2",
            "Qsca",
            "summary_theta_deg",
            "dCsca_dOmega_at_theta_m2_sr",
            "Esca_unit_amp_at_theta_m",
        }.issubset(df.columns)
        assert set(df["material"]) == {"gold", "exosome"}
        assert set(df["diameter_nm"]) == {40.0, 100.0}
        assert np.all(df["summary_theta_deg"] == 37.5)
        assert np.all(df["dCsca_dOmega_at_theta_m2_sr"] >= 0)

    def test_mie_angular_dataframe_shape(self):
        df = build_mie_angular_dataframe(
            [
                {"material": "gold", "diameter_nm": 80, "wavelength_nm": 660},
                {"material": "exosome", "diameter_nm": 100, "wavelength_nm": 532},
            ],
            theta_grid_deg=np.array([30.0, 90.0, 150.0]),
        )
        assert len(df) == 6
        assert {"label", "theta_deg", "dCsca_dOmega_m2_sr", "S1_abs", "S2_abs"}.issubset(df.columns)
        assert np.all(df["dCsca_dOmega_m2_sr"] >= 0)

    def test_mie_single_variable_scan_shape(self):
        df = build_mie_single_variable_scan_dataframe(
            scan_variable="wavelength_nm",
            material="gold",
            scan_values=[450, 532, 660],
            fixed_diameter_nm=100,
            fixed_wavelength_nm=532,
            theta_deg=37.5,
        )
        assert len(df) == 3
        assert {
            "scan_variable",
            "scan_value",
            "theta_deg",
            "dCsca_dOmega_at_theta_m2_sr",
            "Esca_unit_amp_at_theta_m",
        }.issubset(df.columns)
        assert np.all(df["scan_variable"] == "wavelength_nm")
        assert np.all(df["theta_deg"] == 37.5)
        assert np.all(df["dCsca_dOmega_at_theta_m2_sr"] >= 0)

    def test_mie_single_variable_scan_rejects_unknown_variable(self):
        with pytest.raises(ValueError, match="scan_variable must be"):
            build_mie_single_variable_scan_dataframe(
                scan_variable="bad_axis",
                material="gold",
                scan_values=[450, 532, 660],
                fixed_diameter_nm=100,
                fixed_wavelength_nm=532,
                theta_deg=37.5,
            )

    def test_mie_relative_index_scan_shape(self):
        df = build_mie_relative_index_scan_dataframe(
            relative_index_real_values=[1.02, 1.10, 1.30],
            diameter_nm=100,
            wavelength_nm=532,
            theta_deg=37.5,
            relative_index_imag=0.0,
        )
        assert len(df) == 3
        assert {
            "m_real",
            "m_imag",
            "theta_deg",
            "relative_index_real",
            "dCsca_dOmega_at_theta_m2_sr",
            "Esca_unit_amp_at_theta_m",
        }.issubset(df.columns)
        assert np.all(df["theta_deg"] == 37.5)
        assert np.all(df["m_imag"] == 0.0)
        assert np.all(df["dCsca_dOmega_at_theta_m2_sr"] >= 0)

def test_resolve_linked_mie_defaults():
    defaults = _resolve_linked_mie_defaults("gold_200nm", 650)
    assert defaults["material"] == "gold"
    assert defaults["diameter_nm"] == 200
    assert defaults["wavelength_nm"] == 660


def test_lookup_summary_case_row_supports_mie_workflow_anchor():
    df = pd.DataFrame(
        [
            {
                "particle_name": "gold_200nm",
                "wavelength_nm": 660,
                "width_nm": 920,
                "depth_nm": 610,
                "design_recommendation_label": "Recommended default",
            }
        ]
    )
    row = lookup_summary_case_row(
        df,
        particle_name="gold_200nm",
        wavelength_nm=660,
        width_nm=920,
        depth_nm=610,
    )
    assert row is not None
    assert row["design_recommendation_label"] == "Recommended default"


def test_load_workflow_case_anchor_uses_precomputed_prefix(tmp_path):
    summary_path = tmp_path / "fine_full_range_summary.csv"
    meta_path = tmp_path / "fine_full_range_meta.json"
    pd.DataFrame(
        [
            {
                "particle_name": "gold_200nm",
                "wavelength_nm": 660,
                "width_nm": 920,
                "depth_nm": 610,
                "detection_rate": 0.82,
            }
        ]
    ).to_csv(summary_path, index=False)
    meta_path.write_text(
        json.dumps({"dashboard_schema_version": CURRENT_SCHEMA_VERSION}),
        encoding="utf-8",
    )
    (tmp_path / "fine_full_range_result_health.json").write_text(
        json.dumps({"status": "ok"}),
        encoding="utf-8",
    )
    with open(tmp_path / "fine_full_range_compact.pkl", "wb") as f:
        pickle.dump([], f)

    row, prefix = load_workflow_case_anchor(
        str(tmp_path),
        {
            "using_live_data": True,
            "live_tag": "debug",
            "data_prefix": "fine_full_range",
            "selected_particle": "gold_200nm",
            "selected_wavelength_nm": 660,
            "selected_W_nm": 920,
            "selected_H_nm": 610,
        },
    )

    assert prefix == "fine_full_range"
    assert row is not None
    assert row["detection_rate"] == pytest.approx(0.82)


def test_load_sweep_compact_backfills_gate_and_recommendation_fields(tmp_path):
    path = tmp_path / "legacy_compact.pkl"
    legacy_case = {
        "particle_name": "gold_80nm",
        "wavelength_m": 660e-9,
        "width_m": 800e-9,
        "depth_m": 550e-9,
        "engineering_gate_passed": True,
        "engineering_gate_failed_count": 0,
        "engineering_gate_reason": "PASS",
        "summary": {
            "observation_freeze_status": "caution_probe_before_result_freeze",
        },
        "physics": {},
    }
    with open(path, "wb") as f:
        pickle.dump([legacy_case], f)
    compact = load_sweep_compact(str(path))
    case = compact[0]
    assert case["engineering_gate_status_label"]
    assert case["summary"]["engineering_gate_primary_blocker_label"]
    assert case["design_recommendation_status"] == "recommended_with_caution"
    assert case["physics"]["design_recommendation_label"]


def test_load_sweep_compact_backfills_summary_nested_gate_fields(tmp_path):
    path = tmp_path / "legacy_compact_summary_gate.pkl"
    legacy_case = {
        "particle_name": "gold_80nm",
        "wavelength_m": 660e-9,
        "width_m": 800e-9,
        "depth_m": 550e-9,
        "summary": {
            "engineering_gate_passed": True,
            "engineering_gate_failed_count": 0,
            "engineering_gate_reason": "PASS",
            "observation_freeze_status": "caution_probe_before_result_freeze",
        },
        "physics": {},
    }
    with open(path, "wb") as f:
        pickle.dump([legacy_case], f)

    compact = load_sweep_compact(str(path))
    case = compact[0]
    assert case["engineering_gate_status_label"]
    assert case["summary"]["engineering_gate_primary_blocker_label"]
    assert case["design_recommendation_status"] == "recommended_with_caution"
    assert case["physics"]["design_recommendation_label"]


def test_load_sweep_compact_rejects_global_pickle_payloads(tmp_path):
    class _EvilPickle:
        def __reduce__(self):
            return (os.system, ("echo unsafe",))

    path = tmp_path / "malicious_compact.pkl"
    with open(path, "wb") as f:
        pickle.dump(_EvilPickle(), f)

    with pytest.raises(pickle.UnpicklingError, match="Forbidden class"):
        load_sweep_compact(str(path))


def test_format_case_verdict_caption_includes_blocker():
    caption = format_case_verdict_caption(
        {
            "design_recommendation_label": "Recommended default",
            "engineering_gate_status_label": "Engineering gate blocked",
            "observation_freeze_status": "default_ready_for_result_freeze",
            "engineering_gate_primary_blocker_label": "稳定检出率不足",
        }
    )

    assert "Recommended default" in caption
    assert "Engineering gate blocked" in caption
    assert "default_ready_for_result_freeze" in caption

def test_build_case_context():
    context = build_case_context("exosome_120nm", 532, 800, 550)
    assert context is not None
    assert context["material"] == "exosome"
    assert context["diameter_nm"] == 120
    assert context["particle_label"] == "exosome (120 nm)"
    assert context["wavelength_nm"] == 532
    assert context["width_nm"] == 800
    assert context["depth_nm"] == 550

def test_build_case_context_none_when_empty():
    assert build_case_context(None, None, None, None) is None

def test_make_particle_rounds_non_integer_diameter_in_name():
    particle = make_particle("gold", 80.6)
    assert particle.name == "gold_81nm"
    assert particle.radius_m == pytest.approx(40.3e-9)

def test_interference_defaults_inherit_selected_case_and_snap_wavelength():
    with _SessionStateGuard():
        st.session_state["selected_particle"] = "gold_200nm"
        st.session_state["selected_wavelength_nm"] = 650
        st.session_state["selected_W_nm"] = 920
        st.session_state["selected_H_nm"] = 610
        defaults = resolve_interference_defaults()
        assert defaults["material"] == "gold"
        assert defaults["diameter_nm"] == 200
        assert defaults["wavelength_nm"] == 660
        assert defaults["width_nm"] == 920
        assert defaults["depth_nm"] == 610

def test_interference_defaults_prefer_live_system_parameters():
    with _SessionStateGuard():
        st.session_state["selected_particle"] = "exosome_120nm"
        st.session_state["selected_wavelength_nm"] = 520
        st.session_state["selected_W_nm"] = 880
        st.session_state["selected_H_nm"] = 640
        st.session_state["using_live_data"] = True
        cfg = deepcopy(DEFAULT_SIM_CFG)
        cfg.rho = 17.0
        cfg.ref_alpha = 0.9
        cfg.ref_beta = 0.4
        cfg.ref_gamma = 1.6
        cfg.coupling_model = "constant"
        optical = deepcopy(OPTICAL_TEMPLATE)
        optical.beam_waist_y_m = 900e-9
        st.session_state["live_sim_cfg"] = cfg
        st.session_state["live_optical"] = optical
        st.session_state["live_tag"] = "probe"
        defaults = resolve_interference_defaults()
        assert defaults["material"] == "exosome"
        assert defaults["diameter_nm"] == 120
        assert defaults["wavelength_nm"] == 532
        assert defaults["rho"] == pytest.approx(17.0)
        assert defaults["ref_alpha"] == pytest.approx(0.9)
        assert defaults["ref_beta"] == pytest.approx(0.4)
        assert defaults["ref_gamma"] == pytest.approx(1.6)
        assert defaults["coupling_model"] == "constant"
        assert defaults["beam_waist_y_nm"] == 900
        assert "[probe]" in defaults["source_label"]

def test_interference_apply_defaults_preserves_manual_values_unless_forced():
    with _SessionStateGuard():
        st.session_state["selected_particle"] = "gold_200nm"
        st.session_state["selected_wavelength_nm"] = 650
        st.session_state["selected_W_nm"] = 920
        st.session_state["selected_H_nm"] = 610
        st.session_state["intf_material"] = "exosome"
        st.session_state["intf_diameter_nm"] = 140
        apply_interference_defaults(force=False)
        assert st.session_state["intf_material"] == "exosome"
        assert st.session_state["intf_diameter_nm"] == 140
        apply_interference_defaults(force=True)
        assert st.session_state["intf_material"] == "gold"
        assert st.session_state["intf_diameter_nm"] == 200
        assert st.session_state["intf_wavelength_nm"] == 660

def test_cross_page_defaults_align_for_same_selected_case():
    with _SessionStateGuard():
        st.session_state["selected_particle"] = "gold_200nm"
        st.session_state["selected_wavelength_nm"] = 650
        st.session_state["selected_W_nm"] = 920
        st.session_state["selected_H_nm"] = 610
        mie_defaults = _resolve_linked_mie_defaults(
            st.session_state["selected_particle"],
            st.session_state["selected_wavelength_nm"],
        )
        intf_defaults = resolve_interference_defaults()
        nd_defaults = resolve_noise_defaults()
        assert mie_defaults["material"] == intf_defaults["material"] == nd_defaults["material"] == "gold"
        assert mie_defaults["diameter_nm"] == intf_defaults["diameter_nm"] == nd_defaults["diameter_nm"] == 200
        assert mie_defaults["wavelength_nm"] == intf_defaults["wavelength_nm"] == nd_defaults["wavelength_nm"] == 660
        assert intf_defaults["width_nm"] == nd_defaults["width_nm"] == 920
        assert intf_defaults["depth_nm"] == nd_defaults["depth_nm"] == 610

def test_dashboard_page_registry_matches_workflow():
    assert WORKFLOW_PAGE_OPTIONS == [
        "Decision Summary",
        "Engineering Windows",
    ]
    assert PAGE_OPTIONS == WORKFLOW_PAGE_OPTIONS + [
        "Mie Explorer",
        "Interference Explorer",
        "Noise & Detection Explorer",
        "Design Explorer",
        "Case Inspector",
        "Single-Case Calculator",
    ]


def test_page_header_hub_keeps_cross_page_navigation_in_sidebar(monkeypatch):
    captured_buttons: list[str] = []

    def fake_button(label: str, *args: object, **kwargs: object) -> bool:
        captured_buttons.append(label)
        return False

    monkeypatch.setattr(st, "button", fake_button)

    with _SessionStateGuard():
        st.session_state["selected_particle"] = "gold_200nm"
        st.session_state["selected_wavelength_nm"] = 660
        st.session_state["selected_W_nm"] = 920
        st.session_state["selected_H_nm"] = 610
        for page in PAGE_OPTIONS:
            render_page_header_hub(
                page,
                geometry_is_context_only=page == "Mie Explorer",
            )

    assert captured_buttons == []


def test_single_case_stage_report_contains_ordered_stages():
    report = build_single_case_stage_report(
        material="exosome",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=1000,
        depth_nm=550,
        n_events=4,
    )
    assert report["meta"]["material"] == "exosome"
    assert report["headline"]["headline"]
    assert "unclassified" not in report["headline"]["headline"].lower()
    assert "unknown" not in report["headline"]["headline"].lower()
    assert "freeze=" not in report["headline"]["headline"]
    assert report["headline"]["badge"]
    assert "工程门槛" in report["headline"]["badge"]
    assert report["headline"]["primary_message"]
    assert report["headline"]["next_step"]
    assert [stage["id"] for stage in report["stages"]] == [
        "input",
        "mie",
        "reference",
        "interference",
        "readout",
        "batch",
        "decision",
    ]
    for stage in report["stages"]:
        assert set(stage["reading"].keys()) == {"key", "judgment", "caution"}
        assert stage["priority"] in {"primary", "secondary"}
        assert stage["priority_label"]
    assert report["diagnostics"]["report_random_seed"] == DEFAULT_SIM_CFG.random_seed
    assert report["diagnostics"]["report_random_seed_source"] == "sim_cfg_random_seed"
    assert not report["rho_sensitivity_df"].empty
    assert report["rho_sensitivity_summary"]["rho_sensitivity_candidate_count"] >= 1
    assert report["rho_sensitivity_summary"]["rho_sensitivity_status"] in {
        "within_envelope_and_robust",
        "within_envelope_but_sensitive",
        "high_sensitivity",
        "out_of_envelope_but_locally_robust",
        "out_of_envelope_and_sensitive",
        "unavailable",
    }
    assert "clean_signal" in report["interference_trace_df"].columns
    assert "signal_noisy" in report["event_trace_df"].columns
    assert "detected" in report["event_table_df"].columns

def test_rho_sensitivity_report_exports_envelope_probe_rows():
    rho_df, rho_summary = build_rho_sensitivity_report(
        material="exosome",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=1000,
        depth_nm=550,
        n_events=4,
    )

    assert not rho_df.empty
    assert {
        "rho",
        "rho_candidate_roles",
        "rho_candidate_is_requested",
        "rho_candidate_is_nominal",
        "A_ref",
        "peak_clean_signal",
        "detection_rate",
        "stable_detection_rate",
        "engineering_gate_passed",
        "design_recommendation_status",
        "detection_rate_delta_vs_anchor",
        "peak_clean_rel_delta_vs_anchor",
    }.issubset(rho_df.columns)
    requested_row = rho_df.loc[rho_df["rho_candidate_is_requested"]].iloc[0]
    assert requested_row["rho_candidate_roles"]
    assert rho_summary["rho_sensitivity_candidate_count"] == len(rho_df)
    assert rho_summary["rho_sensitivity_anchor_role"] in {
        "requested",
        "rho_physical_envelope_nominal",
    }
    assert rho_summary["rho_sensitivity_report_random_seed"] == DEFAULT_SIM_CFG.random_seed
    assert rho_summary["rho_sensitivity_report_random_seed_source"] == "sim_cfg_random_seed"
    assert rho_summary["rho_sensitivity_label"]
    assert rho_summary["rho_sensitivity_guidance"]
    assert np.isfinite(
        float(rho_summary["rho_sensitivity_max_abs_detection_rate_delta_vs_anchor"])
    )
    assert np.isfinite(
        float(rho_summary["rho_sensitivity_max_abs_peak_clean_rel_delta_vs_anchor"])
    )
    assert requested_row["detection_rate_delta_vs_anchor"] == pytest.approx(
        rho_summary["rho_sensitivity_requested_vs_anchor_detection_rate_delta"]
    )
    assert requested_row["peak_clean_rel_delta_vs_anchor"] == pytest.approx(
        rho_summary["rho_sensitivity_requested_vs_anchor_peak_clean_rel_delta"]
    )

def test_dashboard_page_jump_actions_are_removed():
    panels_dir = Path(__file__).resolve().parents[1] / "dashboard" / "panels"
    target_pattern = re.compile(r'"target":\s*"([^"]+)"')
    targets = []
    for path in panels_dir.glob("*.py"):
        if path.name.startswith("._"):
            continue
        targets.extend(target_pattern.findall(path.read_text(encoding="utf-8")))
    assert targets == []

def test_interference_case_signal_identity():
    case = compute_interference_case(
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
    )
    trace_df = case["trace_df"]
    np.testing.assert_allclose(
        trace_df["clean_signal"].to_numpy(),
        trace_df["sca_only_term"].to_numpy() + trace_df["cross_term"].to_numpy(),
        rtol=1e-10,
        atol=1e-12,
    )
    assert {
        "A_ref_local",
        "phi_ref_rad",
        "reference_amplitude_scale",
        "reference_spatial_phase_rad",
        "delta_phi_ref_rad",
        "cross_term_collapsed",
        "cross_term_joint",
        "phi_sca_path_x_rad",
        "phi_sca_path_z_rad",
        "phi_projection_rad",
        "phi_material_parallel_rad",
        "phi_material_perpendicular_rad",
        "phi_beam_gouy_rad",
        "phi_beam_curv_rad",
    }.issubset(trace_df.columns)
    assert case["summary"]["peak_clean_signal"] == pytest.approx(trace_df["clean_signal"].max())
    assert 0.0 < case["summary"]["theta_det_deg"] < 90.0
    assert case["summary"]["reference_spatial_mode"] == "cross_section_surrogate"
    assert np.isfinite(case["summary"]["peak_phi_material_rad"])
    assert np.isfinite(case["summary"]["peak_phi_projection_rad"])
    assert case["summary"]["dominant_peak_polarity"] in {"positive", "negative", "zero"}
    assert case["summary"]["dominant_peak_abs_clean_signal"] >= 0.0
    assert np.isfinite(case["summary"]["dominant_peak_phi_material_rad"])
    assert np.isfinite(case["summary"]["dominant_peak_phi_projection_rad"])
    assert np.isfinite(case["summary"]["peak_phi_beam_gouy_rad"])
    assert np.isfinite(case["summary"]["peak_phi_beam_curv_rad"])
    assert np.isfinite(case["summary"]["peak_phi_sca_path_x_rad"])
    assert np.isfinite(case["summary"]["peak_phi_sca_path_z_rad"])
    assert case["summary"]["interference_cross_term_mode"] == "joint_overlap_integrated"
    assert case["summary"]["interference_overlap_mode"] == "joint_overlap_integrated"
    assert case["summary"]["interference_overlap_agreement_status"] in {"caution", "mismatch"}
    assert case["summary"]["interference_overlap_default_model"] == "joint_overlap_integrated"
    assert case["summary"]["interference_overlap_default_role"] == "default_frozen_mainline"
    assert case["summary"]["interference_overlap_default_frozen"] is True
    assert case["summary"]["interference_overlap_default_freeze_status"] == "default_frozen_active"
    assert case["summary"]["interference_overlap_alternative_model"] == "collapsed_then_multiplied"
    assert case["summary"]["interference_overlap_alternative_role"] == "legacy_collapsed_review_only"
    assert case["summary"]["interference_overlap_peak_rel_error"] > 0.5
    assert case["summary"]["peak_cross_term"] == pytest.approx(case["summary"]["peak_cross_term_joint"])
    assert case["intrinsic"]["path_opd_model"] == "single_pass"
    assert case["intrinsic"]["path_opd_reference_plane"] == "detector_projection_single_pass_surrogate"
    assert case["intrinsic"]["path_opd_z_geometry_factor"] == pytest.approx(1.0)
    assert "path_opd_model" not in case["summary"]

def test_interference_zero_rho_removes_cross_term():
    sim_cfg = deepcopy(DEFAULT_SIM_CFG)
    sim_cfg.rho = 0.0
    sim_cfg.include_diffusion = False
    case = compute_interference_case(
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
        sim_cfg=sim_cfg,
    )
    trace_df = case["trace_df"]
    assert case["summary"]["A_ref"] == pytest.approx(0.0, abs=1e-12)
    assert np.max(np.abs(trace_df["cross_term"].to_numpy())) == pytest.approx(0.0, abs=1e-12)
    np.testing.assert_allclose(
        trace_df["clean_signal"].to_numpy(),
        trace_df["sca_only_term"].to_numpy(),
        rtol=1e-10,
        atol=1e-12,
    )

def test_interference_case_prefers_matched_reference_and_illumination_polarization():
    matched_cfg = deepcopy(DEFAULT_SIM_CFG)
    matched_cfg.include_diffusion = False
    matched_cfg.scattering_projection_mode = "parallel"
    matched_cfg.illumination_polarization_mode = "match_scattering"
    matched_cfg.reference_projection_mode = "match_scattering"
    matched_cfg.cross_polarization_leakage = 0.05

    cross_cfg = deepcopy(matched_cfg)
    cross_cfg.illumination_polarization_mode = "perpendicular"
    cross_cfg.reference_projection_mode = "perpendicular"

    matched = compute_interference_case(
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
        sim_cfg=matched_cfg,
    )
    cross = compute_interference_case(
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
        sim_cfg=cross_cfg,
    )

    assert matched["summary"]["illumination_polarization_alignment_status"] == "matched"
    assert matched["summary"]["reference_projection_alignment_status"] == "matched"
    assert cross["summary"]["illumination_polarization_alignment_status"] == "cross_suppressed"
    assert cross["summary"]["reference_projection_alignment_status"] == "cross_suppressed"
    assert matched["summary"]["scattering_projection_basis"] == "parallel"
    assert matched["summary"]["illumination_projection_basis"] == "parallel"
    assert matched["summary"]["reference_projection_basis"] == "parallel"
    assert matched["summary"]["interference_projection_basis"] == "parallel"
    assert matched["summary"]["interference_projection_basis_match"] is True
    assert matched["summary"]["interference_projection_coupling_status"] == "shared_basis_matched"
    assert cross["summary"]["illumination_projection_basis_match"] is True
    assert cross["summary"]["reference_projection_basis_match"] is True
    assert cross["summary"]["interference_projection_basis_match"] is True
    assert cross["summary"]["illumination_projection_coupling_status"] == "shared_basis_cross_suppressed"
    assert cross["summary"]["reference_projection_coupling_status"] == "shared_basis_cross_suppressed"
    assert cross["summary"]["interference_projection_coupling_status"] == "shared_basis_cross_suppressed"
    assert cross["summary"]["peak_A_env"] < matched["summary"]["peak_A_env"]
    assert cross["summary"]["A_ref"] < matched["summary"]["A_ref"]
    assert abs(cross["summary"]["peak_clean_signal"]) < abs(matched["summary"]["peak_clean_signal"])

def test_interference_case_respects_path_opd_model():
    single_cfg = deepcopy(DEFAULT_SIM_CFG)
    single_cfg.include_diffusion = False
    single_cfg.path_opd_model = "single_pass"

    roundtrip_cfg = deepcopy(single_cfg)
    roundtrip_cfg.path_opd_model = "reference_plane_roundtrip_surrogate"

    single = compute_interference_case(
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
        initial_z_fraction=0.1,
        sim_cfg=single_cfg,
    )
    roundtrip = compute_interference_case(
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
        initial_z_fraction=0.1,
        sim_cfg=roundtrip_cfg,
    )

    assert single["intrinsic"]["path_opd_model"] == "single_pass"
    assert roundtrip["intrinsic"]["path_opd_model"] == "reference_plane_roundtrip_surrogate"
    assert single["intrinsic"]["path_opd_z_geometry_factor"] == pytest.approx(1.0)
    assert roundtrip["intrinsic"]["path_opd_z_geometry_factor"] == pytest.approx(2.0)
    assert single["intrinsic"]["path_opd_default_model"] == "single_pass"
    assert single["intrinsic"]["path_opd_model_role"] == "default_frozen_mainline"
    assert single["intrinsic"]["path_opd_default_frozen"] is True
    assert single["summary"]["path_opd_freeze_status"] == "default_frozen_active"
    assert roundtrip["intrinsic"]["path_opd_default_model"] == "single_pass"
    assert roundtrip["intrinsic"]["path_opd_model_role"] == "diagnostic_review_alternative"
    assert roundtrip["intrinsic"]["path_opd_default_frozen"] is False
    assert roundtrip["summary"]["path_opd_freeze_status"] == "alternative_review_mode"
    assert roundtrip["summary"]["peak_phi_sca_path_z_rad"] == pytest.approx(
        2.0 * single["summary"]["peak_phi_sca_path_z_rad"],
        rel=1e-6,
    )

def test_interference_case_supports_wall_referenced_opd_diagnostics():
    wall_cfg = deepcopy(DEFAULT_SIM_CFG)
    wall_cfg.include_diffusion = False
    wall_cfg.path_opd_model = "wall_referenced_gap_surrogate"

    wall = compute_interference_case(
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
        initial_z_fraction=0.1,
        sim_cfg=wall_cfg,
    )

    assert wall["intrinsic"]["path_opd_model"] == "wall_referenced_gap_surrogate"
    assert "path_opd_model" not in wall["summary"]
    assert (
        wall["intrinsic"]["path_opd_reference_plane"]
        == "nearest_channel_wall_centered_gap_surrogate"
    )
    assert (
        wall["intrinsic"]["path_opd_z_reference_mode"]
        == "nearest_wall_gap_centered_about_channel_midplane"
    )
    assert wall["intrinsic"]["path_opd_default_model"] == "single_pass"
    assert wall["intrinsic"]["path_opd_model_role"] == "diagnostic_review_alternative"
    assert wall["intrinsic"]["path_opd_default_frozen"] is False
    assert wall["summary"]["path_opd_freeze_status"] == "alternative_review_mode"
    assert np.isfinite(wall["summary"]["peak_phi_focus_crossing_rad"])
    assert np.isfinite(wall["summary"]["peak_phi_gouy_ref_rad"])
    assert np.isfinite(wall["summary"]["peak_phi_gouy_sca_rad"])
    assert np.isfinite(wall["summary"]["peak_delta_phi_gouy_rad"])

def test_interference_case_can_activate_joint_overlap_cross_term():
    sim_cfg = deepcopy(DEFAULT_SIM_CFG)
    sim_cfg.include_diffusion = False
    sim_cfg.interference_overlap_mode = "joint_overlap_integrated"

    case = compute_interference_case(
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
        sim_cfg=sim_cfg,
    )
    trace_df = case["trace_df"]
    np.testing.assert_allclose(
        trace_df["cross_term"].to_numpy(),
        trace_df["cross_term_joint"].to_numpy(),
        rtol=1e-10,
        atol=1e-12,
    )
    assert case["summary"]["interference_cross_term_mode"] == "joint_overlap_integrated"
    assert case["summary"]["interference_overlap_mode"] == "joint_overlap_integrated"
    assert np.isfinite(case["summary"]["interference_overlap_factor_abs"])
    assert np.isfinite(case["summary"]["interference_overlap_factor_phase_rad"])
    assert case["summary"]["interference_overlap_agreement_status"] == "caution"

def test_interference_width_scan_changes_effective_theta_by_default():
    df = build_interference_scan_dataframe(
        scan_variable="width_nm",
        scan_values=[500, 800, 1200],
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
    )
    assert np.all(df["valid"])
    assert len(df) == 3
    assert len(np.unique(np.round(df["E_sca_normalized"].to_numpy(), 12))) > 1

def test_interference_width_scan_keeps_intrinsic_term_constant_in_fixed_angle_mode():
    sim_cfg = deepcopy(DEFAULT_SIM_CFG)
    sim_cfg.collection_angle_model = "fixed"
    sim_cfg.collection_integration_mode = "single_angle"
    df = build_interference_scan_dataframe(
        scan_variable="width_nm",
        scan_values=[500, 800, 1200],
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
        sim_cfg=sim_cfg,
    )
    assert np.all(df["valid"])
    assert np.allclose(df["E_sca_normalized"], df["E_sca_normalized"].iloc[0], rtol=1e-10, atol=1e-12)

def test_interference_rho_scan_scales_reference_but_not_intrinsic():
    df = build_interference_scan_dataframe(
        scan_variable="rho",
        scan_values=[2.0, 5.0, 10.0],
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
    )
    assert np.all(df["valid"])
    np.testing.assert_allclose(
        df["E_sca_normalized"].to_numpy(),
        np.full(3, df["E_sca_normalized"].iloc[0]),
        rtol=1e-10,
        atol=1e-12,
    )
    assert np.all(np.diff(df["A_ref"].to_numpy()) > 0)
    assert np.all(np.isfinite(df["peak_cross_term"].to_numpy()))
    assert len(np.unique(np.round(df["peak_cross_term"].to_numpy(), 12))) > 1
    assert np.all(np.diff(df["heterodyne_gain"].to_numpy()) > 0)

def test_interference_wavelength_scan_exports_phase_diagnostics():
    df = build_interference_scan_dataframe(
        scan_variable="wavelength_nm",
        scan_values=list(FULL_SWEEP_WAVELENGTHS_NM),
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
    )
    assert np.all(df["valid"])
    assert {
        "peak_delta_phi_ref_rad",
        "peak_phi_material_rad",
        "peak_phi_projection_rad",
    }.issubset(df.columns)

def test_projection_mode_validation_dataframe_freezes_mode_roles():
    df = build_projection_mode_validation_dataframe(
        material="gold",
        diameter_nm=100,
        wavelength_values_nm=list(FULL_SWEEP_WAVELENGTHS_NM),
        width_nm=800,
        depth_nm=550,
    )
    assert len(df) == len(FULL_SWEEP_WAVELENGTHS_NM) * 3
    assert {
        "scattering_projection_mode",
        "projection_mode_role",
        "phase_aware",
        "material_phase_source",
        "dominant_peak_clean_signal",
        "dominant_peak_abs_clean_signal",
        "dominant_peak_polarity",
        "dominant_peak_phi_material_rad",
        "dominant_peak_phi_projection_rad",
        "dominant_peak_delta_phi_ref_rad",
    }.issubset(df.columns)
    assert set(df["scattering_projection_mode"]) == {"parallel", "perpendicular", "intensity_proxy"}
    intensity = df[df["scattering_projection_mode"] == "intensity_proxy"]
    assert np.all(intensity["projection_mode_role"] == "legacy_compatibility")
    assert np.all(intensity["phase_aware"] == False)
    assert np.allclose(intensity["dominant_peak_phi_material_rad"], 0.0, atol=1e-12)
    parallel = df[df["scattering_projection_mode"] == "parallel"]
    assert np.all(parallel["projection_mode_role"] == "primary_phase_aware")
    assert np.all(parallel["phase_aware"])

def test_reference_model_consistency_report_matches_surrogate_generated_calibration(tmp_path):
    calibration_path = TestDashboardWorkflow()._write_surrogate_reference_calibration(tmp_path)
    cfg = deepcopy(DEFAULT_SIM_CFG)
    cfg.reference_model = "channel_angular_surrogate"
    cfg.reference_calibration_path = calibration_path
    cfg.collection_angle_model = "channel_diffraction"
    cfg.collection_integration_mode = "pupil_slit_surrogate"

    df, summary = build_reference_model_consistency_report(
        width_values_nm=[800.0, 900.0, 1000.0, 1100.0],
        depth_values_nm=[550.0, 650.0],
        wavelength_values_nm=[404.0, 488.0, 532.0, 660.0],
        sim_cfg=cfg,
        optical_template=OPTICAL_TEMPLATE,
    )

    assert {
        "A_ref_surrogate",
        "A_ref_calibrated",
        "A_ref_rel_error",
        "phi_ref_delta_wrapped_rad",
        "calibration_extrapolated",
    }.issubset(df.columns)
    exact_rows = df[
        ((df["width_nm"] == 800.0) & (df["depth_nm"] == 550.0) & (df["wavelength_nm"] == 660.0))
        | ((df["width_nm"] == 900.0) & (df["depth_nm"] == 550.0) & (df["wavelength_nm"] == 488.0))
        | ((df["width_nm"] == 1000.0) & (df["depth_nm"] == 650.0) & (df["wavelength_nm"] == 532.0))
        | ((df["width_nm"] == 1100.0) & (df["depth_nm"] == 650.0) & (df["wavelength_nm"] == 660.0))
    ].copy()
    assert not exact_rows.empty
    assert np.all(~exact_rows["calibration_extrapolated"].to_numpy(dtype=bool))
    np.testing.assert_allclose(exact_rows["A_ref_rel_error"], 0.0, atol=6e-3)
    np.testing.assert_allclose(exact_rows["phi_ref_delta_wrapped_rad"], 0.0, atol=3e-2)
    assert summary["n_non_extrapolated_points"] >= len(exact_rows)
    assert summary["reference_consistency_agreement_status"] == "aligned"
    assert summary["reference_consistency_surrogate_fallback_accepted"] is True
    assert summary["reference_consistency_primary_model"] == "calibrated_lookup"
    assert summary["reference_consistency_split_dimension"] == "wavelength_nm"
    assert summary["reference_consistency_material_split_applicable"] is False
    by_wavelength = summary["reference_consistency_by_wavelength"]
    assert len(by_wavelength) == len(FULL_SWEEP_WAVELENGTHS_NM)
    assert {item["wavelength_nm"] for item in by_wavelength} == {float(v) for v in FULL_SWEEP_WAVELENGTHS_NM}
    assert all(item["n_non_extrapolated_points"] <= 2 for item in by_wavelength)
    assert all(item["reference_consistency_enough_points"] is False for item in by_wavelength)

def test_path_opd_freeze_report_exports_three_models_and_gouy_stability():
    report_df, summary = build_path_opd_freeze_report(
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
        initial_x_fraction=0.0,
        initial_z_fraction=0.1,
        sim_cfg=DEFAULT_SIM_CFG,
        optical_template=OPTICAL_TEMPLATE,
    )

    assert set(report_df["path_opd_model"]) == {
        "single_pass",
        "reference_plane_roundtrip_surrogate",
        "wall_referenced_gap_surrogate",
    }
    assert summary["path_opd_freeze_default_model"] == "single_pass"
    assert summary["path_opd_freeze_default_role"] == "default_frozen_mainline"
    assert summary["path_opd_freeze_agreement_status"] in {"aligned", "caution", "mismatch"}
    expected_waist = 0.61 * OPTICAL_TEMPLATE.wavelength_m / OPTICAL_TEMPLATE.illumination_NA
    assert summary["delta_phi_gouy_default_model"] == "illumination_beam_focus_crossing_surrogate"
    assert summary["delta_phi_gouy_default_role"] == "default_frozen_mainline"
    assert summary["delta_phi_gouy_freeze_agreement_status"] == "aligned"
    assert summary["delta_phi_gouy_default_frozen"] is True
    assert summary["delta_phi_gouy_default_freeze_status"] == "default_frozen_active"
    assert summary["delta_phi_gouy_freeze_max_peak_delta_phi_gouy_delta_rad"] < 0.05
    assert summary["delta_phi_gouy_validity"] == "shared_beam_acceptable"
    assert summary["delta_phi_gouy_geometry_width_to_waist_ratio"] == pytest.approx(
        800e-9 / expected_waist
    )
    assert summary["delta_phi_gouy_geometry_depth_to_waist_ratio"] == pytest.approx(
        550e-9 / expected_waist
    )
    wall_row = report_df.loc[
        report_df["path_opd_model"] == "wall_referenced_gap_surrogate"
    ].iloc[0]
    assert wall_row["path_opd_z_reference_mode"] == "nearest_wall_gap_centered_about_channel_midplane"

def test_noise_detection_case_event_trace_extract():
    case = compute_noise_detection_case(
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
        n_events=6,
    )
    assert len(case["event_df"]) == 6
    assert 0.0 <= case["summary"]["detection_rate"] <= 1.0
    trace_df = build_event_trace_dataframe(case, 0)
    assert {
        "time_ms",
        "clean_signal",
        "signal_raw_noisy",
        "signal_noisy",
        "signal_nodi",
        "signal_pod",
        "threshold",
        "A_ref_local",
        "delta_phi_ref_rad",
    }.issubset(trace_df.columns)
    assert np.allclose(trace_df["threshold"], trace_df["threshold"].iloc[0])
    assert case["summary"]["readout_model"] == "lockin_surrogate"
    assert "detected_single_channel" in case["event_df"].columns
    assert "detected_paired_channel" in case["event_df"].columns
    assert "best_peak_height_single_channel" in case["event_df"].columns
    assert "best_peak_height_paired_channel" in case["event_df"].columns

def test_noise_detection_case_paired_channel_decision_is_no_looser_than_single():
    sim_cfg_single = deepcopy(DEFAULT_SIM_CFG)
    sim_cfg_single.n_events = 6
    sim_cfg_single.detection_decision_mode = "single_channel"
    case_single = compute_noise_detection_case(
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
        sim_cfg=sim_cfg_single,
        n_events=6,
    )

    sim_cfg_paired = deepcopy(DEFAULT_SIM_CFG)
    sim_cfg_paired.n_events = 6
    sim_cfg_paired.detection_decision_mode = "paired_channel"
    case_paired = compute_noise_detection_case(
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
        sim_cfg=sim_cfg_paired,
        n_events=6,
    )

    assert case_single["summary"]["detection_decision_mode"] == "single_channel"
    assert case_paired["summary"]["detection_decision_mode"] == "paired_channel"
    assert (
        case_paired["summary"]["detection_rate"]
        <= case_single["summary"]["detection_rate"] + 1e-12
    )
    assert (
        case_paired["summary"]["paired_channel_detection_rate"]
        <= case_paired["summary"]["single_channel_detection_rate"] + 1e-12
    )

def test_detection_scan_dataframe_shape():
    df = build_detection_scan_dataframe(
        scan_variable="noise_std",
        scan_values=[0.0, 0.01, 0.02],
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
        n_events=4,
    )
    assert len(df) == 3
    assert {"detection_rate", "mean_peak_height", "CV", "mean_threshold", "valid"}.issubset(df.columns)
    assert np.all((df["detection_rate"] >= 0.0) & (df["detection_rate"] <= 1.0))

def test_detection_noise_scan_raises_threshold():
    sim_cfg = deepcopy(DEFAULT_SIM_CFG)
    sim_cfg.n_events = 10
    df = build_detection_scan_dataframe(
        scan_variable="noise_std",
        scan_values=[0.0, 0.01, 0.02],
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
        sim_cfg=sim_cfg,
        n_events=8,
    )
    assert np.all(df["valid"])
    assert df["mean_threshold"].iloc[1] != pytest.approx(df["mean_threshold"].iloc[0], rel=1e-4)
    tolerance = max(1e-3, 5e-4 * abs(float(df["mean_threshold"].iloc[1])))
    assert df["mean_threshold"].iloc[-1] >= df["mean_threshold"].iloc[1] - tolerance

def test_detection_threshold_scan_raises_threshold():
    sim_cfg = deepcopy(DEFAULT_SIM_CFG)
    sim_cfg.n_events = 10
    df = build_detection_scan_dataframe(
        scan_variable="threshold_sigma",
        scan_values=[3.0, 5.0, 7.0],
        material="gold",
        diameter_nm=100,
        wavelength_nm=660,
        width_nm=800,
        depth_nm=550,
        sim_cfg=sim_cfg,
        n_events=8,
    )
    assert np.all(df["valid"])
    assert np.all(np.diff(df["mean_threshold"].to_numpy()) > 0)

def test_noise_defaults_inherit_live_and_selected_context():
    with _SessionStateGuard():
        st.session_state["selected_particle"] = "exosome_150nm"
        st.session_state["selected_wavelength_nm"] = 500
        st.session_state["selected_W_nm"] = 990
        st.session_state["selected_H_nm"] = 730
        st.session_state["using_live_data"] = True
        cfg = deepcopy(DEFAULT_SIM_CFG)
        cfg.noise_std = 0.023
        cfg.noise_model = "gaussian"
        cfg.drift_slope = 0.004
        cfg.threshold_sigma = 6.2
        cfg.include_diffusion = False
        cfg.rho = 13.0
        cfg.ref_alpha = 0.8
        optical = deepcopy(OPTICAL_TEMPLATE)
        optical.beam_waist_y_m = 820e-9
        st.session_state["live_sim_cfg"] = cfg
        st.session_state["live_optical"] = optical
        st.session_state["live_tag"] = "nd-probe"
        defaults = resolve_noise_defaults()
        assert defaults["material"] == "exosome"
        assert defaults["diameter_nm"] == 150
        assert defaults["wavelength_nm"] == 488
        assert defaults["width_nm"] == 990
        assert defaults["depth_nm"] == 730
        assert defaults["noise_std"] == pytest.approx(0.023)
        assert defaults["noise_model"] == "gaussian"
        assert defaults["drift_slope"] == pytest.approx(0.004)
        assert defaults["threshold_sigma"] == pytest.approx(6.2)
        assert defaults["include_diffusion"] is False
        assert defaults["rho"] == pytest.approx(13.0)
        assert defaults["ref_alpha"] == pytest.approx(0.8)
        assert defaults["beam_waist_y_nm"] == 820
        assert "[nd-probe]" in defaults["source_label"]

def test_cross_page_live_defaults_align_between_interference_and_noise():
    with _SessionStateGuard():
        st.session_state["selected_particle"] = "exosome_150nm"
        st.session_state["selected_wavelength_nm"] = 500
        st.session_state["selected_W_nm"] = 990
        st.session_state["selected_H_nm"] = 730
        st.session_state["using_live_data"] = True
        cfg = deepcopy(DEFAULT_SIM_CFG)
        cfg.rho = 13.0
        cfg.reference_model = "geometry_scaled"
        cfg.ref_alpha = 0.8
        cfg.ref_beta = 0.35
        cfg.ref_gamma = 1.4
        cfg.coupling_model = "constant"
        cfg.noise_std = 0.023
        cfg.noise_model = "gaussian"
        cfg.drift_slope = 0.004
        cfg.threshold_sigma = 6.2
        cfg.include_diffusion = False
        optical = deepcopy(OPTICAL_TEMPLATE)
        optical.beam_waist_y_m = 820e-9
        st.session_state["live_sim_cfg"] = cfg
        st.session_state["live_optical"] = optical
        st.session_state["live_tag"] = "shared-live"
        intf_defaults = resolve_interference_defaults()
        nd_defaults = resolve_noise_defaults()
        assert intf_defaults["material"] == nd_defaults["material"] == "exosome"
        assert intf_defaults["diameter_nm"] == nd_defaults["diameter_nm"] == 150
        assert intf_defaults["wavelength_nm"] == nd_defaults["wavelength_nm"] == 488
        assert intf_defaults["width_nm"] == nd_defaults["width_nm"] == 990
        assert intf_defaults["depth_nm"] == nd_defaults["depth_nm"] == 730
        assert intf_defaults["rho"] == nd_defaults["rho"] == pytest.approx(13.0)
        assert intf_defaults["reference_model"] == nd_defaults["reference_model"] == "geometry_scaled"
        assert intf_defaults["ref_alpha"] == nd_defaults["ref_alpha"] == pytest.approx(0.8)
        assert intf_defaults["ref_beta"] == nd_defaults["ref_beta"] == pytest.approx(0.35)
        assert intf_defaults["ref_gamma"] == nd_defaults["ref_gamma"] == pytest.approx(1.4)
        assert intf_defaults["coupling_model"] == nd_defaults["coupling_model"] == "constant"
        assert intf_defaults["beam_waist_y_nm"] == nd_defaults["beam_waist_y_nm"] == 820
        assert "[shared-live]" in intf_defaults["source_label"]
        assert "[shared-live]" in nd_defaults["source_label"]

def test_noise_apply_defaults_preserves_manual_values_unless_forced():
    with _SessionStateGuard():
        st.session_state["selected_particle"] = "gold_180nm"
        st.session_state["selected_wavelength_nm"] = 655
        st.session_state["selected_W_nm"] = 1010
        st.session_state["selected_H_nm"] = 690
        st.session_state["nd_noise_std"] = 0.05
        st.session_state["nd_threshold_sigma"] = 9.0
        apply_noise_defaults(force=False)
        assert st.session_state["nd_noise_std"] == pytest.approx(0.05)
        assert st.session_state["nd_threshold_sigma"] == pytest.approx(9.0)
        apply_noise_defaults(force=True)
        assert st.session_state["nd_material"] == "gold"
        assert st.session_state["nd_diameter_nm"] == 180
        assert st.session_state["nd_wavelength_nm"] == 660
        assert st.session_state["nd_width_nm"] == 1010
        assert st.session_state["nd_depth_nm"] == 690

def test_local_fine_grid_centers_and_clamps():
    grid = build_local_fine_grid(800, 550, half_window_nm=300, step_nm=100, n_events=60)
    width_nm = np.round(grid["width_list_m"] * 1e9).astype(int)
    depth_nm = np.round(grid["depth_list_m"] * 1e9).astype(int)
    assert np.array_equal(width_nm, np.array([500, 600, 700, 800, 900, 1000, 1100]))
    assert np.array_equal(depth_nm, np.array([500, 600, 700, 800]))
    assert grid["n_events"] == 60

def test_build_sim_cfg_from_ui_maps_dashboard_controls():
    cfg = build_sim_cfg_from_ui(
        12.0, 0.7, 0.2, 1.3,
        0.015, 0.002, 6.5,
        0.35, False,
        "constant", "constant",
        "per_wavelength", "gaussian",
    )
    assert cfg.score_mode == "single"
    assert cfg.rho == pytest.approx(12.0)
    assert cfg.ref_alpha == pytest.approx(0.7)
    assert cfg.ref_beta == pytest.approx(0.2)
    assert cfg.ref_gamma == pytest.approx(1.3)
    assert cfg.noise_std == pytest.approx(0.015)
    assert cfg.drift_slope == pytest.approx(0.002)
    assert cfg.threshold_sigma == pytest.approx(6.5)
    assert cfg.mean_flow_velocity_m_s == pytest.approx(3.5e-4)
    assert cfg.include_diffusion is False
    assert cfg.reference_model == "constant"
    assert cfg.coupling_model == "constant"
    assert cfg.normalization_mode == "per_wavelength"
    assert cfg.noise_model == "gaussian"

def test_build_optical_from_ui_copies_template_without_mutating_global():
    original_beam_waist_y_m = OPTICAL_TEMPLATE.beam_waist_y_m
    optical = build_optical_from_ui(850.0)
    assert optical.beam_waist_y_m == pytest.approx(850e-9)
    assert OPTICAL_TEMPLATE.beam_waist_y_m == pytest.approx(original_beam_waist_y_m)
    assert optical is not OPTICAL_TEMPLATE

def test_build_precompute_sim_cfg_forces_single_score():
    cfg = build_precompute_sim_cfg("coarse")
    assert cfg.n_events == 30
    assert cfg.score_mode == "single"
    assert cfg.random_sequence_policy == "case_keyed_independent"
    assert cfg.event_sampling_policy == "sobol_stratified"
    assert cfg.adaptive_event_budget_mode == "fixed"
    assert cfg.readout_preset == "EV_NODI_only_design"
    assert cfg.readout_observable_mode == "magnitude"
    assert cfg.nodi_readout_semantics == "bandpass_envelope_surrogate"
    assert cfg.readout_internal_demod_route == "analytic_lockin_surrogate"
    assert cfg.initial_position_distribution_mode == "flux_weighted"
    assert cfg.particle_induced_channel_perturbation_model == (
        "excluded_volume_phase_surrogate"
    )
    assert cfg.vectorized_event_engine == "off"
    assert cfg.event_block_size == 32
    assert cfg.event_block_rng_order == "event_loop_order"

def test_focus_50_150_precompute_profile_and_grid_match_requested_scan():
    particles = get_precompute_particles("exosome_50_150")
    diameters_nm = [int(round(p.radius_m * 2e9)) for p in particles]
    grid = GRID_CONFIGS["focus_50_150"]
    total_cases = (
        len(particles)
        * len(grid["width_list_m"])
        * len(grid["depth_list_m"])
        * len(grid["wavelength_list_m"])
    )

    assert diameters_nm == list(range(50, 151, 10))
    assert [int(round(v * 1e9)) for v in grid["width_list_m"]] == list(range(700, 1501, 100))
    assert [int(round(v * 1e9)) for v in grid["depth_list_m"]] == list(range(500, 1001, 100))
    assert [int(round(v * 1e9)) for v in grid["wavelength_list_m"]] == list(FULL_SWEEP_WAVELENGTHS_NM)
    assert total_cases == 2376

def test_ev_design_grid_targets_nodi_decision_nodes():
    grid = GRID_CONFIGS["ev_design"]
    particles = get_precompute_particles("full_range_biomimetic_exosome_with_anchors")
    total_cases = (
        len(particles)
        * len(grid["width_list_m"])
        * len(grid["depth_list_m"])
        * len(grid["wavelength_list_m"])
    )

    assert [int(round(v * 1e9)) for v in grid["width_list_m"]] == [
        500,
        600,
        700,
        800,
        900,
        1000,
        1100,
        1200,
        1300,
        1400,
        1500,
    ]
    assert [int(round(v * 1e9)) for v in grid["depth_list_m"]] == [
        500,
        550,
        600,
        650,
        700,
        800,
        900,
        1000,
        1100,
        1200,
        1300,
        1400,
        1500,
    ]
    assert [int(round(v * 1e9)) for v in grid["wavelength_list_m"]] == list(
        FULL_SWEEP_WAVELENGTHS_NM
    )
    assert total_cases == 32032
    assert int(grid["n_events"]) == 10000


def test_ev_design_ensemble_profile_expands_optical_uncertainty_cases():
    grid = GRID_CONFIGS["ev_design"]
    particles = get_precompute_particles("ev_design_biomimetic_ensemble_with_anchors")
    total_cases = (
        len(particles)
        * len(grid["width_list_m"])
        * len(grid["depth_list_m"])
        * len(grid["wavelength_list_m"])
    )
    ev_particles = [
        p for p in particles if p.name.startswith("exosome_literature_bounds_2021_")
    ]

    assert len(particles) == 73
    assert len(ev_particles) == 44
    assert total_cases == 41756


def test_run_live_sweep_custom_respects_local_fine_axes():
    grid = build_local_fine_grid(800, 550, half_window_nm=100, step_nm=100, n_events=2)
    sim_cfg = build_sim_cfg_from_ui(
        10.0, 0.5, 0.3, 1.0,
        0.01, 0.001, 5.0,
        0.2, True,
        "geometry_scaled", "gaussian_xy",
        "per_wavelength", "gaussian_plus_drift",
    )
    optical = build_optical_from_ui(700.0)
    particle = make_particle("gold", 80)
    df, compact = run_live_sweep_custom(sim_cfg, optical, particle, grid)
    assert len(df) == 24
    assert len(compact) == 24
    assert sorted(df["width_nm"].unique()) == [700, 800, 900]
    assert sorted(df["depth_nm"].unique()) == [500, 600]
    assert sorted(df["wavelength_nm"].unique()) == list(FULL_SWEEP_WAVELENGTHS_NM)
    assert set(df["particle_name"]) == {"gold_80nm"}

def test_run_live_sweep_custom_wraps_validation_errors():
    grid = build_local_fine_grid(800, 550, half_window_nm=100, step_nm=100, n_events=2)
    sim_cfg = build_sim_cfg_from_ui(
        12.0, 0.7, 0.2, 1.3,
        0.015, 0.002, 6.5,
        0.35, False,
        "constant", "constant",
        "per_wavelength", "gaussian",
    )
    optical = build_optical_from_ui(100000.0)
    particle = make_particle("gold", 80)
    with pytest.raises(ValueError, match="Current parameter combination violates physical validation"):
        run_live_sweep_custom(sim_cfg, optical, particle, grid)

def test_estimate_runtime_supports_single_particle_benchmark_probe():
    report = estimate_runtime(
        target_grid="coarse",
        target_particle_profile="quick",
        benchmark_events=1,
        sample_particles=1,
        sample_widths=1,
        sample_depths=1,
        sample_wavelengths=1,
        verbose=False,
    )
    assert report["benchmark"]["cases"] == 1
    assert report["benchmark"]["events_per_case"] == 1
    assert report["benchmark"]["results_returned"] == 1
    assert report["target"]["cases"] == 128
    assert report["target"]["events_per_case"] == 30
    assert report["target"]["estimated_seconds"] > 0


def test_legacy_test_runner_covers_all_test_modules(monkeypatch):
    import tests.run_tests as run_tests

    captured: list[tuple[str, list[str]]] = []

    def fake_run_concurrent(lanes: list[tuple[str, list[str]]]) -> int:
        captured.extend(lanes)
        return 0

    monkeypatch.setattr(run_tests, "_run_concurrent", fake_run_concurrent)
    monkeypatch.setattr(sys, "argv", ["run_tests.py", "--workers", "8"])

    assert run_tests.main() == 0

    assert captured[0][0] == "pytest parallel lane"
    assert "tests" in captured[0][1]
    assert "xdist.plugin" in captured[0][1]
    assert captured[0][1][captured[0][1].index("-n") + 1] == "8"
    assert "cache_dir=.pytest_cache/parallel" in captured[0][1]
    assert "tests/test_physics_core.py" not in captured[0][1]
    assert "tests/test_dashboard_workflow.py" not in captured[0][1]
    assert captured[1][0] == "pytest AppTest lane"
    assert "tests" in captured[1][1]
    assert "-n" not in captured[1][1]
    assert "cache_dir=.pytest_cache/app" in captured[1][1]


def test_precompute_flattened_outputs_include_engineering_metrics():
    results = [_mock_dashboard_engineering_result()]

    df = results_to_dataframe(results)
    compact = results_to_compact(results)

    _assert_precompute_engineering_dataframe_columns(df)
    assert df.iloc[0]["final_engineering_score"] == pytest.approx(0.55)
    assert df.iloc[0]["engineering_decision_basis"] == "paired_channel"
    assert df.iloc[0]["particle_family"] == "gold"
    assert df.iloc[0]["particle_optical_model"] == "homogeneous_mie_sphere"
    assert df.iloc[0]["particle_uncertainty_budget_status"] == (
        "nominal_only_uncertainty_not_propagated"
    )
    assert df.iloc[0]["uncertainty_propagation_mode"] == "none"
    assert compact[0]["engineering_score"] == pytest.approx(0.6)
    assert compact[0]["final_engineering_score"] == pytest.approx(0.55)
    assert compact[0]["engineering_decision_basis"] == "paired_channel"
    assert compact[0]["engineering_gate_passed"] is True
    assert compact[0]["design_recommendation_status"] == "recommended_with_caution"
    assert compact[0]["summary"]["detection_rate_wilson_lb"] == pytest.approx(0.48)
    assert df.iloc[0]["all_crossing_detection_rate"] == pytest.approx(2 / 3)
    assert df.iloc[0]["selected_detector_mode_annulus_detection_rate"] == pytest.approx(
        1.0
    )
    assert df.iloc[0]["selected_detector_mode_annulus_fraction"] == pytest.approx(
        1 / 3
    )
    assert compact[0]["summary"][
        "selected_detector_mode_annulus_detection_rate"
    ] == pytest.approx(1.0)
    assert compact[0]["summary"]["rho_physical_envelope_status"] == "within_envelope"
    assert compact[0]["summary"]["observation_freeze_status"] == "review_required_before_result_freeze"
    assert "mean_signed_peak_height" not in compact[0]["summary"]
    assert "n_positive_peaks" not in compact[0]["summary"]
    assert compact[0]["physics"]["detection_operator_signature"] == "angle=channel_diffraction|integration=pupil_slit_surrogate|projection=parallel"
    assert compact[0]["physics"]["path_opd_freeze_status"] == "default_frozen_active"
    assert compact[0]["physics"]["reference_width_saturation_status"] == "active_soft_cutoff"
    assert "phase_filter_validity" in compact[0]["physics"]
    assert "subwavelength_groove_validity_status" in compact[0]["physics"]
    assert compact[0]["physics"]["readout_preset"] == "exploratory_default"
    assert compact[0]["physics"]["readout_sampling_validity"] == "carrier_underresolved"
    assert compact[0]["physics"]["polarity_source"] == "optical_and_electronics_phase_mixed"
    assert compact[0]["physics"]["lockin_output_unit_convention"] == "arbitrary_lockin_output_units"
    assert compact[0]["physics"]["threshold_tail"] == "two_sided"
    assert compact[0]["physics"]["threshold_calibration_source"] == "gaussian_iid"
    assert compact[0]["physics"]["colored_noise_false_alarm_status"] == "not_evaluated_iid_surrogate_only"
    assert compact[0]["physics"]["particle_family"] == "gold"
    assert compact[0]["physics"]["particle_optical_model"] == "homogeneous_mie_sphere"
    assert compact[0]["physics"]["particle_uncertainty_budget_status"] == (
        "nominal_only_uncertainty_not_propagated"
    )
    assert compact[0]["physics"]["peak_height_CI_available"] is False

def test_precompute_sweep_cleans_progress_and_checkpoint_artifacts_after_success(tmp_path, monkeypatch):
    import nodi_simulator.dashboard.precompute as precompute_mod

    monkeypatch.setitem(
        precompute_mod.GRID_CONFIGS,
        "coarse",
        {
            "width_list_m": np.array([500e-9, 1000e-9]),
            "depth_list_m": np.array([500e-9]),
            "wavelength_list_m": np.array([488e-9]),
            "n_events": 2,
        },
    )

    out_dir = tmp_path / "precompute_artifacts"
    precompute_sweep(
        grid_name="coarse",
        config_tag="artifacts",
        particle_profile="quick",
        output_dir=str(out_dir),
        n_workers=1,
        save_freeze_probe_report=False,
        progress_interval_s=0.1,
        checkpoint_enabled=True,
        checkpoint_batch_size=1,
        checkpoint_flush_interval_s=0.0,
        artifact_profile="full",
    )

    progress_path = out_dir / "coarse_artifacts_progress.json"
    checkpoint_manifest_path = out_dir / "coarse_artifacts_checkpoint" / "manifest.json"
    summary_path = out_dir / "coarse_artifacts_summary.csv"
    case_summary_csv = out_dir / "coarse_artifacts_case_summary.csv"
    design_postprocess_csv = out_dir / "coarse_artifacts_design_postprocess.csv"
    case_summary_parquet = out_dir / "coarse_artifacts_case_summary.parquet"
    physics_fields_parquet = out_dir / "coarse_artifacts_physics_fields.parquet"
    diagnostics_long_parquet = out_dir / "coarse_artifacts_diagnostics_long.parquet"

    assert not progress_path.exists()
    assert not checkpoint_manifest_path.exists()
    assert not checkpoint_manifest_path.parent.exists()

    assert summary_path.exists()
    assert case_summary_csv.exists()
    assert design_postprocess_csv.exists()
    assert case_summary_parquet.exists()
    assert physics_fields_parquet.exists()
    assert diagnostics_long_parquet.exists()
    df = pd.read_csv(summary_path)
    assert len(df) == 4
    assert len(pd.read_parquet(case_summary_parquet)) == 4
    assert "field" in pd.read_parquet(diagnostics_long_parquet).columns

def test_precompute_artifact_paths_follow_single_prefix_convention(tmp_path):
    prefix = "fine_current_model_full_range"
    paths = _build_precompute_artifact_paths(str(tmp_path), prefix)

    assert paths.progress_json.endswith(f"{prefix}_progress.json")
    assert paths.checkpoint_dir.endswith(f"{prefix}_checkpoint")
    assert paths.checkpoint_chunks_dir.endswith(os.path.join(f"{prefix}_checkpoint", "chunks"))
    assert paths.checkpoint_manifest_json.endswith(
        os.path.join(f"{prefix}_checkpoint", "manifest.json")
    )
    assert paths.summary_csv.endswith(f"{prefix}_summary.csv")
    assert paths.case_summary_csv.endswith(f"{prefix}_case_summary.csv")
    assert paths.case_summary_parquet.endswith(f"{prefix}_case_summary.parquet")
    assert paths.design_postprocess_csv.endswith(f"{prefix}_design_postprocess.csv")
    assert paths.physics_fields_parquet.endswith(f"{prefix}_physics_fields.parquet")
    assert paths.diagnostics_long_parquet.endswith(f"{prefix}_diagnostics_long.parquet")
    assert paths.compact_pkl.endswith(f"{prefix}_compact.pkl")
    assert paths.meta_json.endswith(f"{prefix}_meta.json")
    assert paths.result_health_json.endswith(f"{prefix}_result_health.json")
    assert paths.runtime_performance_json.endswith(
        f"{prefix}_runtime_performance.json"
    )
    assert paths.freeze_probe_json.endswith(f"{prefix}_freeze_probe.json")

def test_load_checkpoint_results_normalizes_legacy_chunk_count_key(tmp_path):
    checkpoint_dir = tmp_path / "legacy_checkpoint"
    chunks_dir = checkpoint_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    (checkpoint_dir / "manifest.json").write_text(
        json.dumps(
            {
                "chunk_count": 3,
                "checkpointed_cases": 0,
                "next_chunk_index": 3,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    results, manifest = _load_checkpoint_results(str(checkpoint_dir))

    assert results == []
    assert manifest["chunk_count"] == 3
    assert manifest["checkpoint_chunk_count"] == 3
    assert manifest["next_chunk_index"] == 3

def test_parameter_sweep_progress_builder_uses_stable_schema():
    last_case = _build_sweep_last_case_snapshot(
        {
            "case_idx": 7,
            "particle_name": "gold_40nm",
            "wavelength_m": 488e-9,
            "width_m": 500e-9,
            "depth_m": 600e-9,
            "ok": True,
            "error": None,
        }
    )
    progress = _build_sweep_progress_state(
        total_cases=10,
        completed_cases=7,
        successful_cases=6,
        failed_cases=1,
        active_workers=4,
        elapsed_seconds=14.0,
        cases_per_second=0.5,
        estimated_total_seconds=20.0,
        estimated_remaining_seconds=6.0,
        last_case=last_case,
    )

    assert {
        "stage",
        "status",
        "total_cases",
        "completed_cases",
        "successful_cases",
        "failed_cases",
        "progress_fraction",
        "elapsed_seconds",
        "cases_per_second",
        "estimated_total_seconds",
        "estimated_remaining_seconds",
        "active_workers",
        "last_case",
    }.issubset(progress.keys())
    assert progress["stage"] == "sweep"
    assert progress["status"] == "running"
    assert progress["progress_fraction"] == 0.7
    assert progress["last_case"]["particle_name"] == "gold_40nm"
    assert progress["last_case"]["wavelength_nm"] == pytest.approx(488.0)

def test_parameter_sweep_progress_line_formatter_is_stable():
    progress = _build_sweep_progress_state(
        total_cases=10,
        completed_cases=7,
        successful_cases=6,
        failed_cases=1,
        active_workers=4,
        elapsed_seconds=14.0,
        cases_per_second=0.5,
        estimated_total_seconds=20.0,
        estimated_remaining_seconds=6.0,
        last_case=None,
    )

    line = _format_sweep_progress_line(progress)

    assert line.startswith("[progress] 7/10 (70.0%)")
    assert "ok=6 failed=1" in line
    assert "elapsed=14.0s" in line
    assert "eta=6.0s" in line
    assert "0.50 cases/s" in line

def test_precompute_sweep_resume_reuses_checkpointed_cases(tmp_path, monkeypatch):
    import nodi_simulator.dashboard.precompute as precompute_mod

    monkeypatch.setitem(
        precompute_mod.GRID_CONFIGS,
        "coarse",
        {
            "width_list_m": np.array([500e-9]),
            "depth_list_m": np.array([500e-9]),
            "wavelength_list_m": np.array([488e-9]),
            "n_events": 2,
        },
    )

    out_dir = tmp_path / "resume_artifacts"
    checkpoint_dir = out_dir / "coarse_resume_checkpoint"
    chunks_dir = checkpoint_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    gold_case = deepcopy(_mock_dashboard_engineering_result())
    gold_case["particle_name"] = "gold_40nm"
    gold_case["wavelength_m"] = 488e-9
    gold_case["width_m"] = 500e-9
    gold_case["depth_m"] = 500e-9
    exosome_case = deepcopy(_mock_dashboard_engineering_result())
    exosome_case["particle_name"] = "exosome_100nm"
    exosome_case["wavelength_m"] = 488e-9
    exosome_case["width_m"] = 500e-9
    exosome_case["depth_m"] = 500e-9
    checkpoint_cases = [
        precompute_mod._normalize_raw_case_result(gold_case),
        precompute_mod._normalize_raw_case_result(exosome_case),
    ]

    with open(chunks_dir / "chunk_000000.pkl", "wb") as f:
        pickle.dump(checkpoint_cases, f)
    (checkpoint_dir / "manifest.json").write_text(
        json.dumps(
            {
                "job_type": "dashboard_precompute_checkpoint",
                "grid": "coarse",
                "config_tag": "resume",
                "particle_profile": "quick",
                "total_cases": 2,
                "checkpointed_cases": 2,
                "checkpoint_chunk_count": 1,
                "next_chunk_index": 1,
                "current_stage": "checkpointing",
                "status": "running",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    captured = {}

    def fake_run_parameter_sweep(**kwargs):
        captured["resume_results"] = kwargs["resume_results"]
        captured["skip_case_keys"] = kwargs["skip_case_keys"]
        return list(kwargs["resume_results"])

    monkeypatch.setattr(precompute_mod, "run_parameter_sweep", fake_run_parameter_sweep)

    precompute_sweep(
        grid_name="coarse",
        config_tag="resume",
        particle_profile="quick",
        output_dir=str(out_dir),
        n_workers=1,
        save_freeze_probe_report=False,
        progress_interval_s=0.1,
        resume=True,
        checkpoint_enabled=True,
        checkpoint_batch_size=1,
        checkpoint_flush_interval_s=0.0,
    )

    assert len(captured["resume_results"]) == 2
    assert len(captured["skip_case_keys"]) == 2

    progress_path = out_dir / "coarse_resume_progress.json"
    checkpoint_path = out_dir / "coarse_resume_checkpoint"
    assert not progress_path.exists()
    assert not checkpoint_path.exists()
    assert (out_dir / "coarse_resume_summary.csv").exists()
    df = results_to_dataframe(captured["resume_results"])
    compact = results_to_compact(captured["resume_results"])
    _assert_precompute_engineering_dataframe_columns(df)
    assert len(df) == 2
    assert df.iloc[0]["engineering_decision_basis"] == "paired_channel"
    assert compact[0]["engineering_gate_passed"] is True
    assert compact[0]["engineering_gate_status_label"]
    assert compact[0]["engineering_gate_primary_blocker_label"]
    assert compact[0]["design_recommendation_status"] == "recommended_with_caution"
    assert compact[0]["design_recommendation_label"]
    assert compact[0]["summary"]["rho_physical_envelope_status"] == "within_envelope"
    assert compact[0]["physics"]["path_opd_freeze_status"] == "default_frozen_active"
    assert compact[0]["physics"]["reference_width_saturation_status"] == "active_soft_cutoff"


def test_precompute_sweep_refuses_mismatched_checkpoint_manifest(tmp_path, monkeypatch):
    import nodi_simulator.dashboard.precompute as precompute_mod

    monkeypatch.setitem(
        precompute_mod.GRID_CONFIGS,
        "coarse",
        {
            "width_list_m": np.array([500e-9]),
            "depth_list_m": np.array([500e-9]),
            "wavelength_list_m": np.array([488e-9]),
            "n_events": 2,
        },
    )

    out_dir = tmp_path / "resume_artifacts"
    checkpoint_dir = out_dir / "coarse_resume_checkpoint"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    (checkpoint_dir / "manifest.json").write_text(
        json.dumps(
            {
                "job_type": "dashboard_precompute_checkpoint",
                "grid": "coarse",
                "config_tag": "resume",
                "particle_profile": "full_range_biomimetic_exosome",
                "total_cases": 999,
                "checkpointed_cases": 0,
                "checkpoint_chunk_count": 0,
                "next_chunk_index": 0,
                "current_stage": "checkpointing",
                "status": "running",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Checkpoint manifest does not match"):
        precompute_sweep(
            grid_name="coarse",
            config_tag="resume",
            particle_profile="quick",
            output_dir=str(out_dir),
            n_workers=1,
            progress_interval_s=0.1,
            resume=True,
            checkpoint_enabled=True,
        )


def test_precompute_sweep_refuses_checkpoint_chunks_without_identity_manifest(
    tmp_path,
    monkeypatch,
):
    import nodi_simulator.dashboard.precompute as precompute_mod

    monkeypatch.setitem(
        precompute_mod.GRID_CONFIGS,
        "coarse",
        {
            "width_list_m": np.array([500e-9]),
            "depth_list_m": np.array([500e-9]),
            "wavelength_list_m": np.array([488e-9]),
            "n_events": 2,
        },
    )

    out_dir = tmp_path / "resume_artifacts"
    chunks_dir = out_dir / "coarse_resume_checkpoint" / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_case = deepcopy(_mock_dashboard_engineering_result())
    checkpoint_case["particle_name"] = "gold_40nm"
    checkpoint_case["wavelength_m"] = 488e-9
    checkpoint_case["width_m"] = 500e-9
    checkpoint_case["depth_m"] = 500e-9
    with open(chunks_dir / "chunk_000000.pkl", "wb") as f:
        pickle.dump([precompute_mod._normalize_raw_case_result(checkpoint_case)], f)

    with pytest.raises(ValueError, match="Checkpoint manifest does not match"):
        precompute_sweep(
            grid_name="coarse",
            config_tag="resume",
            particle_profile="quick",
            output_dir=str(out_dir),
            n_workers=1,
            progress_interval_s=0.1,
            resume=True,
            checkpoint_enabled=True,
        )


def test_build_freeze_probe_report_summarizes_status_and_width_trends():
    review, ready = build_freeze_probe_fixture_cases()
    report = build_freeze_probe_report([review, ready], top_k=2)
    assert_freeze_probe_report_contract(report)
    assert report["n_cases"] == 2
    assert report["status_distributions"]["observation_freeze_status"][
        "default_ready_for_result_freeze"
    ]["count"] == 1
    assert report["status_distributions"]["observation_freeze_status"][
        "review_required_before_result_freeze"
    ]["count"] == 1
    assert report["status_distributions"]["rho_physical_envelope_status"][
        "above_upper_envelope"
    ]["count"] == 1
    assert report["status_distributions"]["count_prediction_status"][
        "poisson_flux_deadtime_surrogate_active"
    ]["count"] == 1
    assert report["status_distributions"]["count_prediction_status"][
        "not_applied_per_event_detection_only"
    ]["count"] == 1
    assert len(report["width_groups"]) == 2
    assert report["sanity_checks"]["rho_out_of_envelope_count"] == 1
    assert report["sanity_checks"]["observation_ready_fraction"] == pytest.approx(0.5)
    assert report["sanity_checks"]["review_required_fraction"] == pytest.approx(0.5)
    assert report["sanity_checks"]["shared_beam_caution_fraction"] == pytest.approx(0.5)
    assert report["sanity_checks"]["count_prediction_active_fraction"] == pytest.approx(0.5)
    assert report["sanity_checks"]["count_confidence_unavailable_fraction"] == pytest.approx(1.0)
    assert report["sanity_checks"][
        "crossing_conditioned_transport_unimplemented_fraction"
    ] == pytest.approx(1.0)
    assert report["sanity_checks"]["narrow_width_nm"] == pytest.approx(500.0)
    assert report["sanity_checks"]["wide_width_nm"] == pytest.approx(1200.0)
    assert report["sanity_checks"]["narrow_channel_reference_more_conservative"] is True
    assert report["top_cases"][0]["particle_name"] == "gold_60nm"
    assert report["top_cases"][0]["observation_freeze_status"] == "default_ready_for_result_freeze"
    assert (
        report["top_cases"][0]["count_prediction_status"]
        == "poisson_flux_deadtime_surrogate_active"
    )
    assert "wavelength_nm" not in report["top_cases"][0]
    assert set(report["width_groups"][0]) == {"width_nm", "n_cases"}

def test_build_engineering_gate_calibration_report_prefers_current_default():
    df = pd.DataFrame(
        [
            {
                "particle_name": "gold_60nm",
                "wavelength_nm": 660,
                "width_nm": 800,
                "depth_nm": 550,
                "score": 1.0,
                "final_engineering_score": 1.2,
                "observation_freeze_status": "default_ready_for_result_freeze",
                "engineering_gate_passed": True,
                "engineering_gate_reason": "PASS",
                "engineering_gate_failed_count": 0,
                "engineering_gate_stable_detection_rate_lb": 0.32,
                "engineering_gate_phase_flip_fraction_ub": 0.22,
            },
            {
                "particle_name": "gold_80nm",
                "wavelength_nm": 660,
                "width_nm": 800,
                "depth_nm": 550,
                "score": 0.8,
                "final_engineering_score": -10.0,
                "observation_freeze_status": "default_ready_for_result_freeze",
                "engineering_gate_passed": False,
                "engineering_gate_reason": "phase_flip_fraction>0.50",
                "engineering_gate_failed_count": 1,
                "engineering_gate_stable_detection_rate_lb": 0.30,
                "engineering_gate_phase_flip_fraction_ub": 0.53,
            },
            {
                "particle_name": "gold_100nm",
                "wavelength_nm": 660,
                "width_nm": 900,
                "depth_nm": 550,
                "score": 0.7,
                "final_engineering_score": -10.8,
                "observation_freeze_status": "caution_probe_before_result_freeze",
                "engineering_gate_passed": False,
                "engineering_gate_reason": "stable_detection_rate<0.20",
                "engineering_gate_failed_count": 1,
                "engineering_gate_stable_detection_rate_lb": 0.17,
                "engineering_gate_phase_flip_fraction_ub": 0.40,
            },
            {
                "particle_name": "gold_120nm",
                "wavelength_nm": 660,
                "width_nm": 1000,
                "depth_nm": 550,
                "score": 0.6,
                "final_engineering_score": -10.4,
                "observation_freeze_status": "caution_probe_before_result_freeze",
                "engineering_gate_passed": False,
                "engineering_gate_reason": "stable_detection_rate<0.20 / phase_flip_fraction>0.50",
                "engineering_gate_failed_count": 2,
                "engineering_gate_stable_detection_rate_lb": 0.18,
                "engineering_gate_phase_flip_fraction_ub": 0.53,
            },
            {
                "particle_name": "exosome_100nm",
                "wavelength_nm": 660,
                "width_nm": 1200,
                "depth_nm": 550,
                "score": 0.5,
                "final_engineering_score": -9.5,
                "observation_freeze_status": "default_ready_for_result_freeze",
                "engineering_gate_passed": False,
                "engineering_gate_reason": "n_detected<5 / detection_rate<0.10",
                "engineering_gate_failed_count": 2,
                "engineering_gate_stable_detection_rate_lb": 0.26,
                "engineering_gate_phase_flip_fraction_ub": 0.30,
            },
        ]
    )
    report = build_engineering_gate_calibration_report(df, top_k=3)
    assert report["current_gate"]["passed_cases"] == 1
    assert report["current_gate"]["failed_cases"] == 4
    assert report["recommended_default_variant"] == "current_default"
    assert "当前默认门槛" in report["recommended_default_guidance"]
    assert report["failure_primary_blockers"][0]["label"] == "稳定检出率不足"
    assert report["failure_primary_blockers"][0]["count"] == 2
    phase_variant = next(
        item
        for item in report["candidate_variants"]
        if item["name"] == "relax_phase_flip_to_0.55"
    )
    assert phase_variant["promoted_cases"] == 1
    assert phase_variant["promoted_ready_cases"] == 1
    assert phase_variant["promotion_status"] == "reject_negative_score"
    both_variant = next(
        item
        for item in report["candidate_variants"]
        if item["name"] == "relax_phase_flip_and_stable_rate"
    )
    assert both_variant["promoted_cases"] == 3
    assert both_variant["promoted_caution_cases"] == 2
    assert both_variant["promoted_primary_blockers"][0]["label"] == "稳定检出率不足"

def test_build_result_health_report_tracks_monitoring_items_and_backfills_recommendations():
    df = build_result_health_fixture_frame()
    report = build_result_health_report(df, top_k=5)
    assert_result_health_report_contract(report)
    assert report["n_cases"] == 3
    assert report["engineering_gate_distribution"]["passed"] == 2
    assert report["engineering_gate_distribution"]["failed"] == 1
    recommendation_counts = sorted(
        bucket["count"] for bucket in report["recommendation_distribution"].values()
    )
    assert recommendation_counts == [1, 2]
    assert report["status_distributions"]["delta_phi_gouy_validity"]["shared_beam_caution"]["count"] == 1
    assert report["status_distributions"]["count_prediction_status"][
        "poisson_flux_deadtime_surrogate_active"
    ]["count"] == 1
    assert report["status_distributions"]["count_rate_confidence_status"][
        "not_available_no_blank_false_positive_or_uncertainty_propagation"
    ]["count"] == 3
    assert report["monitoring_summary"]["shared_beam_caution_fraction"] == pytest.approx(1 / 3)
    assert report["monitoring_summary"]["count_prediction_active_count"] == 1
    assert report["monitoring_summary"]["count_confidence_unavailable_count"] == 3
    assert (
        report["monitoring_summary"][
            "crossing_conditioned_transport_unimplemented_count"
        ]
        == 3
    )
    assert report["monitoring_summary"]["narrower_width_has_stronger_saturation_factor"] is True
    assert "shared-beam Gouy caution" in report["monitoring_guidance"]
    assert report["top_caution_cases"][0]["particle_name"] == "gold_80nm"
    wavelength_rows = report["health_slices"]["by_wavelength_nm"]
    material_rows = report["health_slices"]["by_particle_material"]
    row_660 = next(row for row in wavelength_rows if int(row["wavelength_nm"]) == 660)
    row_gold = next(row for row in material_rows if row["particle_material"] == "gold")
    row_exosome = next(row for row in material_rows if row["particle_material"] == "exosome")
    assert row_660["n_cases"] == 2
    assert row_660["shared_beam_caution_fraction"] == pytest.approx(0.5)
    assert row_660["count_prediction_active_fraction"] == pytest.approx(0.0)
    assert row_exosome["count_prediction_active_fraction"] == pytest.approx(1.0)
    assert row_gold["count_confidence_unavailable_fraction"] == pytest.approx(1.0)
    assert row_gold["engineering_gate_pass_fraction"] == pytest.approx(0.5)
    assert row_exosome["default_ready_fraction"] == pytest.approx(1.0)

def test_load_result_health_backfills_from_summary_when_json_missing(tmp_path):
    summary_df = pd.DataFrame(
        [
            {
                "particle_name": "gold_60nm",
                "wavelength_nm": 660,
                "width_nm": 500,
                "depth_nm": 550,
                "score": 1.0,
                "final_engineering_score": 1.2,
                "engineering_gate_passed": True,
                "observation_freeze_status": "default_ready_for_result_freeze",
                "delta_phi_gouy_validity": "shared_beam_caution",
                "rho_physical_envelope_status": "within_envelope",
                "reference_width_saturation_status": "active_soft_cutoff",
                "reference_width_saturation_factor": 1.20,
            }
        ]
    )
    report = load_result_health(str(tmp_path), "missing_prefix", summary_df=summary_df)
    assert report is not None
    assert report["_report_source"] == "computed_from_summary"
    assert report["n_cases"] == 1
    assert report["monitoring_summary"]["rho_out_of_envelope_count"] == 0
    assert sum(
        bucket["count"] for bucket in report["recommendation_distribution"].values()
    ) == 1

def test_build_physics_breakdown_includes_new_batch_metrics():
    case_data = _mock_dashboard_breakdown_case()
    breakdown = build_physics_breakdown(case_data)
    decision = breakdown["decision_summary"]
    physics = breakdown["case_physics"]
    outcome = breakdown["batch_outcome"]
    assert decision["decision_summary_tone"] == "warning"
    assert "freeze ready" in decision["decision_summary_headline"]
    assert "稳定检出率不足" in decision["decision_summary_blocker_text"]
    assert "稳定检出率" in decision["decision_summary_next_step"]
    assert outcome["final_engineering_score"] == pytest.approx(-10.2)
    assert outcome["engineering_score"] == pytest.approx(0.7)
    assert outcome["engineering_gate_passed"] is False
    assert outcome["engineering_decision_basis"] == "paired_channel"
    assert outcome["engineering_gate_basis"] == "paired_channel"
    assert "phase_flip_fraction>0.40" in outcome["engineering_gate_reason"]
    assert outcome["engineering_gate_primary_blocker_label"]
    assert outcome["engineering_gate_blocker_summary"]
    assert outcome["stable_detection_rate"] == pytest.approx(1 / 3)
    assert outcome["phase_flip_fraction"] == pytest.approx(0.5)
    assert outcome["mean_positive_peak_height"] == pytest.approx(2.0)
    assert outcome["mean_negative_peak_height"] == pytest.approx(1.0)
    assert outcome["positive_peak_fraction"] == pytest.approx(0.5)
    assert outcome["negative_peak_fraction"] == pytest.approx(0.5)
    assert outcome["robust_cv_peak_height"] == pytest.approx(0.32)
    assert outcome["mean_peak_to_threshold_ratio"] == pytest.approx(1.6)
    assert outcome["mean_peak_margin_z"] == pytest.approx(0.8)
    assert outcome["mean_transit_time_ms"] == pytest.approx(12.0)
    assert outcome["mean_local_snr"] == pytest.approx(3.2)
    assert outcome["mean_nodi_transit_bandwidth_Hz"] == pytest.approx(83.3)
    assert physics["readout preset"] == "exploratory_default"
    assert physics["readout sampling validity"] == "carrier_underresolved"
    assert physics["polarity source"] == "optical_and_electronics_phase_mixed"
    assert physics["lock-in output unit convention"] == "arbitrary_lockin_output_units"
    assert physics["threshold tail"] == "two_sided"
    assert physics["threshold calibration source"] == "gaussian_iid"
    assert physics["colored-noise false alarm status"] == "not_evaluated_iid_surrogate_only"
    assert physics["particle family"] == "gold"
    assert physics["particle optical model"] == "homogeneous_mie_sphere"
    assert physics["particle material model"] == "materials_db_tabulated_interpolation"
    assert physics["particle material source"] == "Johnson & Christy 1972"
    assert (
        physics["particle material wavelength status"]
        == "materials_db_interpolation_range_checked"
    )
    assert (
        physics["particle material uncertainty"]
        == "not_quantified_material_dataset_nominal"
    )
    assert physics["EV claim level"] == "not_applicable"
    assert physics["EV ensemble mode"] == "nominal_single_preset"
    assert (
        physics["particle uncertainty budget"]
        == "nominal_only_uncertainty_not_propagated"
    )
    assert physics["uncertainty propagation mode"] == "none"
    assert physics["peak-height CI available"] is False
    assert outcome["mean_nodi_transit_bandwidth_gain"] == pytest.approx(0.74)
    assert outcome["mean_nodi_bandwidth_limited_fraction"] == pytest.approx(0.61)
    physics = breakdown["case_physics"]
    assert physics["complex time convention"] == "exp_minus_i_omega_t"
    assert physics["interference conjugation"] == "Re_Eref_conj_Esca"
    assert physics["interference cross-term convention"] == "2*Re(E_ref*conj(E_sca))"
    assert (
        physics["absolute polarity claim"]
        == "not_available_without_measured_global_phase_offset"
    )
    assert physics["active Mie basis component"] == "S2_complex"
    assert physics["high NA scalar warning"] is True
    assert physics["vector validity status"] == "scalar_high_NA_caution"
    assert physics["Mie incident field model"] == "local_plane_wave"
    assert physics["local plane wave validity"] == "valid_for_ranking"
    assert physics["calibration state machine"] == "partial_lane_calibration_only"
    assert physics["output claim level"] == "engineering_ranking"
    assert physics["calibrated quantitative unlocked"] is False
    assert physics["scattering normalization route"] == "baseline_particle_relative"
    assert physics["baseline absolute scale restored"] is False
    assert physics["baseline E_sca allowed in photon route"] is False
    assert physics["K_sca calibration status"] == "not_calibrated"
    assert physics["fluidic network status"] == (
        "partial_network_nanochannel_array_only"
    )
    assert physics["fluidic network pressure-flow relation"] == (
        "blocked_until_measured_pressure_flow_trace"
    )
    assert physics["fluidic network pressure-flow gate"] is False
    assert "pressure_flow_relation_not_calibrated" in physics[
        "fluidic network blockers"
    ]
    assert (
        physics["Mie-to-power chain"]
        == "not_implemented_dCsca_dOmega_not_converted_to_detector_units"
    )
    assert (
        physics["scattered power conversion"]
        == "not_applied_no_incident_power_density_or_detector_etendue"
    )
    assert physics["detector field units"] == "arbitrary_relative_field_units"
    assert physics["power-chain absolute units"] is False
    assert (
        physics["K_sca power-chain role"]
        == "not_available_cannot_replace_mie_to_power_chain"
    )
    assert (
        physics["K_sca uncertainty status"]
        == "not_propagated_no_standard_particle_uncertainty_budget"
    )
    assert physics["K_sca uncertainty propagated"] is False
    assert (
        physics["standard particle uncertainty budget"]
        == "missing_standard_particle_uncertainty_budget"
    )
    assert physics["standard particle size distribution"] == "not_provided"
    assert (
        physics["standard particle material uncertainty"]
        == "not_uncertainty_quantified"
    )
    assert physics["calibration design rank"] == "none"
    assert physics["calibration standards"] == 0
    assert physics["calibration wavelengths"] == 0
    assert physics["calibration geometries"] == 0
    assert (
        physics["calibration held-out status"]
        == "not_available_no_standard_particle_design"
    )
    assert physics["calibration held-out error"] is None
    assert "no_held_out_validation" in physics[
        "calibration identifiability blockers"
    ]
    assert (
        physics["calibration minimum requirement"]
        == "not_met_requires_standard_particle_and_held_out_dimension"
    )
    assert physics["detector calibration level"] == "surrogate_not_detector_unit"
    assert (
        physics["readout calibration level"]
        == "lockin_surrogate_not_physical_electronics"
    )
    assert (
        physics["count calibration level"]
        == "conditional_event_detection_not_count_rate"
    )
    assert physics["noise model route"] == "surrogate"
    assert (
        physics["detector noise claim"]
        == "engineering_noise_surrogate_not_detector_unit"
    )
    assert physics["absolute throughput route"] == "unit_normalized_surrogate"
    assert physics["photon-unit noise model"] == "not_applied"
    assert physics["noise terms schema"] == "noise_terms_v1"
    assert (
        physics["noise term quantitative contribution"]
        == "not_available_arbitrary_units"
    )
    assert physics["lock-in ENBW status"] == "first_order_lockin_surrogate"
    assert physics["shot noise model"] == "intensity_proxy_shot_noise_surrogate"
    assert (
        physics["photon shot noise term"]
        == "intensity_proxy_shot_noise_surrogate"
    )
    assert physics["electronics noise term"] == "disabled"
    assert physics["RIN noise model"] == "not_applied"
    assert physics["RIN noise term"] == "not_applied"
    assert physics["speckle-like noise term"] == "not_applied"
    assert physics["drift noise term"] == "disabled"
    assert physics["lock-in output noise term"] == "disabled"
    assert physics["detector saturation status"] == "not_evaluated_no_detector_range"
    assert physics["dynamic range margin"] is None
    assert (
        physics["reference enhancement SNR claim"]
        == "not_monotonic_without_photon_unit_noise_model"
    )
    assert physics["background field model"] == "baseline_subtraction_surrogate"
    assert (
        physics["background field status"]
        == "baseline_subtraction_only_no_explicit_leakage_field"
    )
    assert (
        physics["background claim level"]
        == "engineering_background_surrogate_not_measured_blank"
    )
    assert physics["residual transmitted leakage"] == "not_modeled"
    assert physics["stray light status"] == "not_modeled"
    assert physics["blank trace empirical available"] is False
    assert (
        physics["particle-induced channel perturbation"]
        == "not_modeled_weak_superposition_assumed"
    )
    assert (
        physics["NODI signal component model"]
        == "scattering_interference_only_surrogate"
    )
    assert (
        physics["NODI forward extinction leakage"]
        == "not_modeled"
    )
    assert (
        physics["NODI particle-channel coupling"]
        == "not_modeled_weak_superposition_assumed"
    )
    assert physics["superposition validity status"] == "weak_scatterer_valid"
    assert physics["channel-particle coupling model"] == "independent_superposition"
    assert physics["joint fullwave required for quantitative phase"] is False

def test_load_sweep_summary_backfills_gate_and_recommendation_fields(tmp_path):
    path = tmp_path / "legacy_summary.csv"
    pd.DataFrame(
        [
            {
                "particle_name": "gold_80nm",
                "wavelength_nm": 660,
                "width_nm": 800,
                "depth_nm": 550,
                "engineering_gate_passed": False,
                "engineering_gate_failed_count": 2,
                "engineering_gate_reason": "stable_detection_rate<0.30 / phase_flip_fraction>0.40",
                "observation_freeze_status": "default_ready_for_result_freeze",
            }
        ]
    ).to_csv(path, index=False)
    df = load_sweep_summary(str(path))
    row = df.iloc[0]
    assert row["engineering_gate_status_label"]
    assert row["engineering_gate_primary_blocker_label"]
    assert row["engineering_gate_blocker_summary"]
    assert row["design_recommendation_status"] == "physics_ready_gate_blocked"


def test_load_sweep_summary_disables_chunked_csv_type_inference(monkeypatch):
    calls: list[dict[str, object]] = []

    def fake_read_csv(path: str, **kwargs: object) -> pd.DataFrame:
        calls.append({"path": path, **kwargs})
        return pd.DataFrame(
            [
                {
                    "particle_name": "gold_80nm",
                    "wavelength_nm": 660,
                    "width_nm": 800,
                    "depth_nm": 550,
                    "engineering_gate_passed": True,
                    "engineering_gate_failed_count": 0,
                    "engineering_gate_reason": "passed",
                    "observation_freeze_status": "default_ready_for_result_freeze",
                }
            ]
        )

    monkeypatch.setattr(backend_module.pd, "read_csv", fake_read_csv)

    df = load_sweep_summary("summary.csv")

    assert not df.empty
    assert calls == [{"path": "summary.csv", "low_memory": False}]

@pytest.mark.app_interactions
@pytest.mark.skipif(AppTest is None, reason="streamlit.testing.v1.AppTest unavailable")
class TestDashboardAppInteractions:
    def test_app_sidebar_radio_switches_page(self):
        at = AppTest.from_file(str(APP_PATH), default_timeout=30)
        at.session_state["dashboard_page"] = "Single-Case Calculator"
        at.session_state["dashboard_page_radio"] = "Single-Case Calculator"
        at.run()
        _assert_header_contains(at, "Single-Case Calculator")

        at.sidebar.radio[0].set_value("Case Inspector")
        at.run()
        _assert_header_contains(at, "Case Inspector")
        assert at.session_state["dashboard_page"] == "Case Inspector"
        assert at.session_state["dashboard_page_radio"] == "Case Inspector"
        _assert_no_app_exceptions(at)

    @pytest.mark.app_interactions
    def test_app_single_case_calculator_page_renders(self):
        at = _make_app_test("Single-Case Calculator")
        _assert_header_contains(at, "Single-Case Calculator")
        _assert_no_app_exceptions(at)

    def test_app_empty_inspector_removes_jump_buttons(self):
        at = _make_app_test("Case Inspector")
        _assert_header_contains(at, "Case Inspector")
        assert not any(button.label == "蜴ｻ Design Explorer" for button in at.button)
        _assert_no_app_exceptions(at)

    def test_app_inspector_with_live_case_removes_next_step_buttons(self):
        at = _make_app_test(
            "Case Inspector",
            **_build_minimal_live_case(),
        )
        _assert_header_contains(at, "Case Inspector")
        assert not any(button.label == "蜴ｻ Noise & Detection Explorer" for button in at.button)
        _assert_no_app_exceptions(at)

    def test_app_design_explorer_renders_live_debug_dataset_when_session_is_live(self):
        live_state = _build_minimal_live_case()
        at = _make_app_test("Design Explorer", **live_state)
        assert at.session_state["using_live_data"] is True
        assert at.session_state["sweep_df_live"] is not None
        assert at.session_state["sweep_compact_live"] is not None
        assert any(
            "live sweep" in alert.value.lower()
            or "调试重算 sweep" in alert.value
            for alert in at.warning
        )
        _assert_no_app_exceptions(at)


def test_precompute_sim_cfg_uses_scalar_event_loop_defaults():
    cfg = build_precompute_sim_cfg("coarse")
    assert cfg.n_events == 30
    assert cfg.score_mode == "single"
    assert cfg.random_sequence_policy == "case_keyed_independent"
    assert cfg.event_sampling_policy == "sobol_stratified"
    assert cfg.readout_preset == "EV_NODI_only_design"
    assert cfg.initial_position_distribution_mode == "flux_weighted"
    assert cfg.vectorized_event_engine == "off"
    assert cfg.event_block_size == 32
    assert cfg.event_block_rng_order == "event_loop_order"
