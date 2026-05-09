from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from nodi_simulator import realism_v2 as rv2


def test_r0_required_docs_and_configs_exist():
    root = Path(rv2.PROJECT_ROOT)
    for rel in (
        "docs/realism_v2/PRD.md",
        "docs/realism_v2/physics_spec.md",
        "docs/realism_v2/test_spec.md",
        "docs/realism_v2/task_list_R0_P0.md",
        "docs/realism_v2/failure_mode_dashboard_template.md",
        "configs/realism_v2/scenario_registry.yaml",
        "configs/realism_v2/detector_path_schema.yaml",
        "configs/realism_v2/detector_connection_state_machine.yaml",
        "configs/realism_v2/laser_daq_schema.yaml",
        "configs/realism_v2/route_key_schema.yaml",
        "configs/realism_v2/run_manifest_schema.yaml",
        "configs/realism_v2/calibration_artifact_registry.yaml",
        "configs/realism_v2/unit_registry.yaml",
        "configs/realism_v2/r3b_uncertainty_prior_table.yaml",
        "configs/realism_v2/r4_representative_full_wave_plan.yaml",
        "configs/realism_v2/claim_level_matrix.csv",
    ):
        assert (root / rel).exists(), rel


def test_claim_level_and_module_state_enums_are_enforced():
    assert rv2.validate_claim_level("relative_with_priors") == "relative_with_priors"
    assert rv2.validate_module_state("bounded_prior") == "bounded_prior"

    with pytest.raises(ValueError, match="Unknown realism_v2 claim_level"):
        rv2.validate_claim_level("absolute_snr")

    with pytest.raises(ValueError, match="Unknown realism_v2 module_state"):
        rv2.validate_module_state("benchish")


def test_route_key_schema_keeps_scenario_identity_separate():
    base = rv2.make_base_route_key(
        wavelength_nm=660,
        width_nm=800,
        depth_nm=1400,
        particle_profile_id="micro_anchor_particle_panel",
        particle_id="EV100_nominal",
        event_lens="all_crossing",
    )
    scenario = rv2.make_scenario_identity(
        scenario_id="micro_anchor_nominal_sanity",
        instrument_chain_id="ET2030_50ohm_voltage",
        prior_sample_id="fixed_nominal_R1p5",
        sidecar_id="P0",
    )
    rv2.assert_route_scenario_separation(base, scenario)
    assert "micro_anchor_nominal_sanity" not in base["route_key"]
    assert base["event_lens"] == "all_crossing"


def test_v1_compatibility_noop_route_key_semantics():
    all_crossing = rv2.make_base_route_key(
        wavelength_nm=660,
        width_nm=800,
        depth_nm=1400,
        particle_profile_id="ev_design_biomimetic_ensemble_with_anchors",
        particle_id="EV100_nominal",
        event_lens="all_crossing",
    )
    selected = rv2.make_base_route_key(
        wavelength_nm=660,
        width_nm=800,
        depth_nm=1400,
        particle_profile_id="ev_design_biomimetic_ensemble_with_anchors",
        particle_id="EV100_nominal",
        event_lens="selected_annulus_0p5_0p8",
    )

    assert all_crossing["route_key"] != selected["route_key"]
    assert all_crossing["event_lens"] == "all_crossing"
    assert selected["event_lens"] == "selected_annulus_0p5_0p8"


def test_run_manifest_schema_and_checksum_fields(tmp_path):
    manifest = rv2.build_run_manifest(
        output_directory=tmp_path,
        event_budget={"stage": "test", "R2_anchor_smoke_started": False},
        scenario_budget={"scenario_bundle": "micro_anchor_nominal_sanity"},
    )
    rv2.validate_run_manifest(manifest)
    assert manifest["manifest_schema_version"] == "1"
    schema = rv2.load_json_yaml("run_manifest_schema.yaml")
    assert "manifest_schema_version" in schema["required_fields"]
    checksum_fields = [key for key in manifest if key.endswith("_checksum")]
    assert "scenario_registry_checksum" in checksum_fields
    assert "detector_state_machine_checksum" in checksum_fields
    assert manifest["R2_anchor_smoke_run"] is False
    assert manifest["R3_reduced_grid_run"] is False
    assert manifest["R5_full_grid_v2_run"] is False
    assert manifest["v1_full_grid_overwritten"] is False
    assert manifest["Tsuyama_paper_fit_continued"] is False
    assert manifest["selected_annulus_bounds_changed"] is False
    assert manifest["calibrated_SNR_claim_emitted"] is False
    assert manifest["ET2030_direct_current_input_unlocked"] is False
    assert manifest["base_v1_summary_path_relative"]
    assert manifest["output_directory_relative"]


def test_run_manifest_checksum_fields_must_be_hex(tmp_path):
    manifest = rv2.build_run_manifest(
        output_directory=tmp_path,
        event_budget={"stage": "test", "R2_anchor_smoke_started": False},
        scenario_budget={"scenario_bundle": "micro_anchor_nominal_sanity"},
    )
    manifest["scenario_registry_checksum"] = "z" * 64

    with pytest.raises(ValueError, match="run_manifest checksum field is not sha256-like"):
        rv2.validate_run_manifest(manifest)


def test_R5_plan_provenance_checksums_must_be_hex():
    plan = copy.deepcopy(rv2.load_R5_full_grid_v2_plan())
    field = sorted(rv2.R5_REQUIRED_SOURCE_CHECKSUM_FIELDS)[0]
    plan["provenance_freeze"][field] = "z" * 64

    with pytest.raises(ValueError, match="R5 provenance checksum is not sha256-like"):
        rv2.validate_R5_full_grid_v2_plan(plan)


def test_load_json_yaml_prefers_config_dir_for_bare_names(monkeypatch, tmp_path):
    (tmp_path / "run_manifest_schema.yaml").write_text('{"shadow": true}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    payload = rv2.load_json_yaml("run_manifest_schema.yaml")

    assert payload["schema_id"] == "realism_v2_run_manifest_schema_R0"
    assert "shadow" not in payload


def test_bfp_roi_operator_masks_outside_unit_disk_before_jacobian():
    shape = (2, 2)
    result = rv2.bfp_roi_intensity_operator(
        E_ref=np.ones(shape, dtype=complex),
        E_sca=np.zeros(shape, dtype=complex),
        weight=np.ones(shape),
        du=0.1,
        dv=0.1,
        u=np.array([[0.0, 1.2], [0.1, 0.2]]),
        v=np.zeros(shape),
        NA=0.5,
        n_medium=1.0,
    )

    assert result["P_ref_ROI_W"] > 0.0
    assert result["valid_uv_fraction"] == pytest.approx(0.75)


def test_calibration_artifact_registry_schema_is_active():
    registry = rv2.load_json_yaml("calibration_artifact_registry.yaml")
    rv2.validate_calibration_artifact_registry(registry)
    assert "bench_validation_ET2030_current_input_placeholder" in rv2.registry_artifact_ids(
        registry
    )


def test_detector_connection_state_machine_blocks_invalid_et2030_current_input():
    result = rv2.evaluate_detector_connection(
        detector_source="ET2030_BNC_biased_output",
        readout_path="LI5640_current_input_direct",
    )

    assert result["connection_physical_validity"] == "forbidden"
    assert result["requires_bench_validation"] is True
    assert result["bench_validation_artifact_id"] == ""


def test_placeholder_artifact_does_not_unlock_et2030_current_input():
    result = rv2.evaluate_detector_connection(
        detector_source="ET2030_BNC_biased_output",
        readout_path="LI5640_current_input_direct",
        bench_validation_artifact_id="bench_validation_ET2030_current_input_placeholder",
    )

    assert result["connection_physical_validity"] == "forbidden"
    assert result["requires_bench_validation"] is True


def test_measured_bench_validation_artifact_unlocks_et2030_current_input():
    registry = {
        "artifacts": [
            {
                "artifact_id": "measured_bench_validation",
                "artifact_type": "detector_transfer",
                "route_key": "not_applicable_bench_validation_only",
                "wavelength_nm": "any",
                "geometry_nm": "any",
                "instrument_chain_id": "ET2030_BNC_direct_to_LI5640_current_input",
                "connection_state_id": "ET2030_BNC_direct_to_LI5640_current_input",
                "acquisition_duration_s": 60,
                "sampling_rate_Hz": 10000,
                "laser_state": "bench_transfer",
                "detector_state": "ET2030_on",
                "sample_state": "not_applicable",
                "file_path": "calibration/measured_bench_validation.csv",
                "checksum": "abc123",
                "source_type": "measured",
                "claim_unlocks": ["bench_validated_detector_connection"],
            }
        ]
    }
    result = rv2.evaluate_detector_connection(
        detector_source="ET2030_BNC_biased_output",
        readout_path="LI5640_current_input_direct",
        bench_validation_artifact_id="measured_bench_validation",
        registry=registry,
    )

    assert result["connection_physical_validity"] == "allowed_bench_validated"
    assert result["requires_bench_validation"] is False


def test_detector_connection_state_machine_allows_valid_paths():
    voltage = rv2.evaluate_detector_connection(
        detector_source="ET2030_BNC_biased_output",
        readout_path="voltage_input_50ohm",
        termination_mode="50_ohm",
    )
    high_z = rv2.evaluate_detector_connection(
        detector_source="ET2030_BNC_biased_output",
        readout_path="high_Z_voltage_input",
    )
    bare = rv2.evaluate_detector_connection(
        detector_source="bare_photodiode",
        readout_path="lockin_current_input",
    )
    tia = rv2.evaluate_detector_connection(
        detector_source="external_TIA_voltage_output",
        readout_path="lockin_voltage_input",
    )

    assert voltage["connection_physical_validity"] == "allowed"
    assert high_z["connection_physical_validity"] == "allowed_with_warning"
    assert bare["connection_physical_validity"] == "allowed"
    assert tia["connection_physical_validity"] == "allowed"


def test_detector_path_schema_maps_to_state_machine_paths():
    rv2.validate_detector_path_schema_maps_to_state_machine()
    schema = rv2.detector_path_schema()
    mapped_connection_paths = {
        str(item["connection_readout_path"]) for item in schema["instrument_to_connection_path"]
    }

    assert rv2.connection_readout_path_for_instrument_path(
        "ET2030_50ohm_voltage", schema
    ) == "voltage_input_50ohm"
    assert rv2.connection_readout_path_for_instrument_path(
        "bare_photodiode_to_external_TIA", schema
    ) == "external_TIA"
    assert rv2.connection_readout_path_for_instrument_path(
        "external_TIA_voltage", schema
    ) == "lockin_voltage_input"
    assert set(schema["connection_readout_path_enum"]) <= mapped_connection_paths
    assert rv2.canonical_instrument_path_id(
        "external_TIA", schema
    ) == "bare_photodiode_to_external_TIA"
    assert rv2.canonical_instrument_path_id(
        "voltage_input_50ohm", schema
    ) == "ET2030_50ohm_voltage"


def test_old_detector_snr_output_names_are_rejected():
    with pytest.raises(ValueError, match="Forbidden legacy SNR output names"):
        rv2.validate_output_names(["scenario_detector_SNR", "detector_SNR"])

    with pytest.raises(ValueError, match="Forbidden legacy SNR output names"):
        rv2.validate_output_names(["calibrated_detector_SNR"])


def test_claim_level_matrix_references_valid_enums():
    rows = rv2.load_claim_level_matrix()
    assert {row["module"] for row in rows} >= {
        "Mie_to_power",
        "detector_unit",
        "blank_false_positive",
    }


def test_scenario_registry_contract_matches_python_constants():
    registry = rv2.load_json_yaml("scenario_registry.yaml")
    caps = registry["scenario_bundle_caps"]

    assert tuple(registry["module_status_enum"]) == rv2.MODULE_STATES
    assert tuple(registry["claim_level_enum"]) == rv2.CLAIM_LEVELS
    assert caps["max_anchor_scenario_bundles"] == rv2.MAX_ANCHOR_SCENARIO_BUNDLES
    assert caps["max_anchor_routes"] == rv2.MAX_ANCHOR_ROUTES
    assert caps["max_stochastic_seeds"] == rv2.MAX_STOCHASTIC_SEEDS
    assert caps["max_event_level_runs_before_review"] == rv2.MAX_EVENT_LEVEL_RUNS_BEFORE_REVIEW


def test_config_files_are_json_compatible_yaml():
    for rel in (
        "scenario_registry.yaml",
        "detector_path_schema.yaml",
        "detector_connection_state_machine.yaml",
        "laser_daq_schema.yaml",
        "route_key_schema.yaml",
        "run_manifest_schema.yaml",
        "calibration_artifact_registry.yaml",
        "unit_registry.yaml",
        "r3b_uncertainty_prior_table.yaml",
        "r4_representative_full_wave_plan.yaml",
    ):
        payload = rv2.load_json_yaml(rel)
        assert isinstance(payload, dict)
        json.dumps(payload)
