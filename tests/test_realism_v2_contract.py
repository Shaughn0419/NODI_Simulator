from __future__ import annotations

import json
from pathlib import Path

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

    assert rv2.connection_readout_path_for_instrument_path(
        "ET2030_50ohm_voltage", schema
    ) == "voltage_input_50ohm"
    assert rv2.connection_readout_path_for_instrument_path(
        "external_TIA_voltage", schema
    ) == "lockin_voltage_input"
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
