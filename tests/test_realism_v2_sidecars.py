from __future__ import annotations

import json
import math

import numpy as np
import pytest

from nodi_simulator import realism_v2 as rv2


def test_run_manifest_provenance_checksum_ignores_created_at(tmp_path):
    assert rv2.RUN_MANIFEST_VOLATILE_FIELDS == frozenset({"created_at"})
    assert rv2.RUN_MANIFEST_PROVENANCE_CHECKSUM_KIND == "stable_content_v1"

    manifest = {
        "created_at": "2026-05-08T00:00:00+00:00",
        "run_id": "stable-content",
        "event_budget": {"new_case_rows": 0},
    }
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    changed = tmp_path / "changed.json"

    first.write_text(json.dumps(manifest), encoding="utf-8")
    second_manifest = dict(manifest)
    second_manifest["created_at"] = "2026-05-09T00:00:00+00:00"
    second.write_text(json.dumps(second_manifest), encoding="utf-8")
    changed_manifest = dict(second_manifest)
    changed_manifest["run_id"] = "changed-content"
    changed.write_text(json.dumps(changed_manifest), encoding="utf-8")

    assert rv2.run_manifest_provenance_checksum(first) == (
        rv2.run_manifest_provenance_checksum(second)
    )
    assert rv2.run_manifest_provenance_checksum(first) != (
        rv2.run_manifest_provenance_checksum(changed)
    )


def test_run_manifest_checksum_kind_accepts_legacy_raw_hash_during_migration():
    required_fields = {"upstream_run_manifest_checksum"}

    rv2._validate_run_manifest_checksum_kind(
        {"upstream_run_manifest_checksum": "0" * 64},
        required_fields,
        "legacy-missing-kind",
    )
    rv2._validate_run_manifest_checksum_kind(
        {
            "upstream_run_manifest_checksum": "0" * 64,
            "run_manifest_checksum_kind": "raw_sha256_file",
        },
        required_fields,
        "legacy-raw-kind",
    )

    with pytest.raises(ValueError, match="checksum kind mismatch"):
        rv2._validate_run_manifest_checksum_kind(
            {
                "upstream_run_manifest_checksum": "0" * 64,
                "run_manifest_checksum_kind": "unknown_kind",
            },
            required_fields,
            "unknown-kind",
        )


def test_realism_v2_migration_preserves_legacy_public_helpers():
    dcs = np.array([1.0, 2.0, 3.0])
    weights = np.array([0.1, 0.2, 0.3])

    assert rv2.integrate_cross_section_m2(dcs, weights) == pytest.approx(1.4)
    assert rv2.lockin_pulse_attenuation(
        pulse_width_s=1.0e-3,
        tau_s=2.0e-3,
        filter_order=2,
    ) == pytest.approx((1.0 - math.exp(-0.5)) ** 0.5)
    assert rv2.representative_full_wave_R4_route_panel()


def test_correlation_pair_rejects_effectively_constant_or_nonfinite_inputs():
    assert rv2._correlation_pair([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == pytest.approx(1.0)
    assert math.isnan(
        rv2._correlation_pair(
            [1.0, 1.0 + 1.0e-14, 1.0 - 1.0e-14],
            [1.0, 2.0, 3.0],
        )
    )
    assert math.isnan(rv2._correlation_pair([1.0, math.nan, 3.0], [1.0, 2.0, 3.0]))


def test_mie_to_power_has_watts_and_no_watt_square_meter_error():
    dcs = np.full(16, 2.0e-16 / (4.0 * math.pi))
    weights = np.full(16, 4.0 * math.pi / 16.0)
    result = rv2.mie_to_power_roi(
        P_probe_W=2.0e-5,
        p_beam_at_particle_per_m2=1.0e12,
        dCsca_dOmega_m2_per_sr=dcs,
        solid_angle_weights_sr=weights,
        collection_throughput=np.full(16, 0.25),
        Csca_total_m2=2.0e-16,
        Cabs_m2=1.0e-17,
        Cext_m2=2.2e-16,
    )

    assert result["P_sca_ROI_W"] > 0.0
    assert result["P_sca_ROI_le_total_bound"] is True
    assert result["energy_conservation_status"] == "P_sca_total_plus_abs_within_extinction"
    assert result["unit_guardrail"] == "watts_from_W_per_m2_times_m2_no_W_m2_error"
    assert result["P_sca_ROI_W"] <= result["I_inc_W_per_m2"] * result["Csca_total_m2"]


def test_beam_normalization_radius_and_medium_wavelength_are_explicit():
    density = np.ones(4)
    normalized, raw_integral = rv2.normalize_beam_profile(density, pixel_area_m2=0.25)

    assert raw_integral == pytest.approx(1.0)
    assert np.sum(normalized) * 0.25 == pytest.approx(1.0)
    assert rv2.sphere_radius_m_from_diameter_nm(100.0) == pytest.approx(50e-9)
    assert rv2.medium_wavelength_m(660e-9, 1.333) < 660e-9


def test_bfp_operator_maps_physical_mm_to_uv_and_applies_jacobian():
    x_mm = np.array([[0.0, 1.0], [0.0, 1.0]])
    y_mm = np.array([[0.0, 0.0], [1.0, 1.0]])
    u, v = rv2.physical_bfp_mm_to_uv(
        x_bfp_mm=x_mm,
        y_bfp_mm=y_mm,
        f_obj_mm=10.0,
        n_medium=1.0,
    )
    jac = rv2.direction_cosine_jacobian(u, v)

    assert u[0, 1] == pytest.approx(0.1)
    assert v[1, 0] == pytest.approx(0.1)
    assert np.all(jac >= 1.0)


def test_bfp_roi_operator_preserves_signed_cross_term_and_throughput():
    u_axis = np.linspace(-0.1, 0.1, 3)
    v_axis = np.linspace(-0.1, 0.1, 3)
    u, v = np.meshgrid(u_axis, v_axis)
    E_ref = np.ones_like(u, dtype=complex)
    E_sca = np.ones_like(u, dtype=complex) * -0.1
    weight = np.ones_like(u)

    result = rv2.bfp_roi_intensity_operator(
        E_ref=E_ref,
        E_sca=E_sca,
        weight=weight,
        du=0.1,
        dv=0.1,
        u=u,
        v=v,
        NA=0.45,
        n_medium=1.333,
    )

    assert result["P_cross_ROI_W"] < 0.0
    assert result["Delta_P_NODI_peak_abs_W"] == pytest.approx(
        abs(result["Delta_P_NODI_peak_signed_W"])
    )
    assert result["same_operator_applied_to_reference_and_scattering"] is True
    assert result["operator_throughput_preserved"] is True
    assert result["BFP_jacobian_applied"] is True


def test_uv_domain_and_na_clipping_are_enforced():
    u = np.array([[1.1]])
    v = np.array([[0.0]])
    with pytest.raises(ValueError, match="u\\^2 \\+ v\\^2 < 1"):
        rv2.direction_cosine_jacobian(u, v)

    valid = rv2.uv_valid_mask(
        np.array([[0.1, 0.5]]),
        np.array([[0.1, 0.0]]),
        NA=0.45,
        n_medium=1.333,
    )
    assert valid.tolist() == [[True, False]]


def test_detector_noise_units_and_snr_claim_guard():
    connection = rv2.evaluate_detector_connection(
        detector_source="ET2030_BNC_biased_output",
        readout_path="voltage_input_50ohm",
        termination_mode="50_ohm",
    )
    result = rv2.scenario_detector_unit_sidecar(
        P_ref_W=1.0e-9,
        Delta_P_peak_W=1.0e-12,
        wavelength_nm=660,
        readout_path="ET2030_50ohm_voltage",
        connection=connection,
    )

    assert "scenario_detector_SNR" in result
    assert "SNR_claim_level" in result
    assert result["SNR_claim_level"] == "absolute_blocked"
    assert result["SNR_requires_calibration"] is True
    assert result["shot_noise_A2_per_Hz"] >= 0.0
    assert result["Johnson_noise_V2_per_Hz"] > 0.0
    assert result["Johnson_noise_A2_per_Hz_equivalent"] > 0.0
    assert result["RIN_PSD_1_per_Hz"] == pytest.approx(1.0e-12)
    assert result["PSD_convention"] == "one_sided"
    assert result["ENBW_convention"] == "Hz_one_sided"


def test_snr_cannot_be_calibrated_absolute_without_artifacts():
    connection = rv2.evaluate_detector_connection(
        detector_source="ET2030_BNC_biased_output",
        readout_path="voltage_input_50ohm",
        termination_mode="50_ohm",
    )
    result = rv2.scenario_detector_unit_sidecar(
        P_ref_W=1.0e-9,
        Delta_P_peak_W=1.0e-12,
        wavelength_nm=660,
        readout_path="ET2030_50ohm_voltage",
        connection=connection,
        measured_detector_transfer=True,
        measured_blank=True,
    )

    assert result["SNR_claim_level"] == "absolute_blocked"
    assert result["SNR_requires_calibration"] is True
    assert "missing_detector_transfer_artifact" in result["SNR_calibration_blocker"]
    assert "missing_measured_blank_artifact" in result["SNR_calibration_blocker"]


def test_placeholder_artifact_cannot_unlock_calibrated_absolute_snr():
    connection = rv2.evaluate_detector_connection(
        detector_source="ET2030_BNC_biased_output",
        readout_path="voltage_input_50ohm",
        termination_mode="50_ohm",
    )
    result = rv2.scenario_detector_unit_sidecar(
        P_ref_W=1.0e-9,
        Delta_P_peak_W=1.0e-12,
        wavelength_nm=660,
        readout_path="ET2030_50ohm_voltage",
        connection=connection,
        detector_transfer_artifact_id="bench_validation_ET2030_current_input_placeholder",
        measured_blank_artifact_id="bench_validation_ET2030_current_input_placeholder",
    )

    assert result["SNR_claim_level"] == "absolute_blocked"
    assert result["detector_transfer_artifact_valid"] is False
    assert result["measured_blank_artifact_valid"] is False


def test_valid_detector_and_blank_artifacts_unlock_calibrated_absolute_snr():
    connection = rv2.evaluate_detector_connection(
        detector_source="ET2030_BNC_biased_output",
        readout_path="voltage_input_50ohm",
        termination_mode="50_ohm",
    )
    registry = {
        "artifacts": [
            {
                "artifact_id": "measured_detector_transfer",
                "artifact_type": "detector_transfer",
                "route_key": "lambda660_w800_d1400",
                "wavelength_nm": 660,
                "geometry_nm": "800x1400",
                "instrument_chain_id": "ET2030_50ohm_voltage",
                "connection_state_id": "ET2030_BNC_to_50ohm_voltage_input",
                "acquisition_duration_s": 120,
                "sampling_rate_Hz": 10000,
                "laser_state": "on",
                "detector_state": "ET2030_on",
                "sample_state": "detector_transfer",
                "file_path": "calibration/measured_detector_transfer.csv",
                "checksum": "abc123",
                "source_type": "measured",
                "claim_unlocks": ["measured_detector_transfer"],
            },
            {
                "artifact_id": "measured_blank_trace",
                "artifact_type": "blank_trace",
                "route_key": "lambda660_w800_d1400",
                "wavelength_nm": 660,
                "geometry_nm": "800x1400",
                "instrument_chain_id": "ET2030_50ohm_voltage",
                "connection_state_id": "ET2030_BNC_to_50ohm_voltage_input",
                "acquisition_duration_s": 600,
                "sampling_rate_Hz": 10000,
                "laser_state": "laser_on",
                "detector_state": "ET2030_on",
                "sample_state": "blank_channel_buffer",
                "file_path": "calibration/measured_blank_trace.csv",
                "checksum": "def456",
                "source_type": "measured",
                "claim_unlocks": ["measured_blank"],
            },
        ]
    }

    result = rv2.scenario_detector_unit_sidecar(
        P_ref_W=1.0e-9,
        Delta_P_peak_W=1.0e-12,
        wavelength_nm=660,
        readout_path="ET2030_50ohm_voltage",
        connection=connection,
        detector_transfer_artifact_id="measured_detector_transfer",
        measured_blank_artifact_id="measured_blank_trace",
        registry=registry,
    )

    assert result["SNR_claim_level"] == "calibrated_absolute"
    assert result["SNR_requires_calibration"] is False
    assert result["SNR_source_type"] == "calibrated"


def test_detector_unit_sidecar_rejects_mismatched_path_mapping():
    connection = rv2.evaluate_detector_connection(
        detector_source="external_TIA_voltage_output",
        readout_path="lockin_voltage_input",
    )
    with pytest.raises(ValueError, match="does not match state-machine connection path"):
        rv2.scenario_detector_unit_sidecar(
            P_ref_W=1.0e-9,
            Delta_P_peak_W=1.0e-12,
            wavelength_nm=660,
            readout_path="ET2030_50ohm_voltage",
            connection=connection,
        )


def test_lockin_model_specs_cannot_be_mixed_and_enbw_is_monotonic():
    assert rv2.lockin_enbw_hz(1e-3, 1) > rv2.lockin_enbw_hz(2e-3, 1)
    assert rv2.lockin_enbw_hz(1e-3, 1) > rv2.lockin_enbw_hz(1e-3, 4)

    with pytest.raises(ValueError, match="cannot be mixed"):
        rv2.validate_lockin_model_specs_not_mixed(["LI5640", "LI5660"])


def test_laser_daq_sidecar_owns_source_beam_and_daq_priors():
    priors = {
        "P_probe_W_by_lambda": {"660": 2e-5},
        "beam_waist_xy_by_lambda": {"660": [0.7e-6, 0.9e-6]},
        "focus_z_shift_by_lambda": {"660": 0.0},
        "objective_transmission_by_lambda": {"660": 0.75},
        "filter_leakage_by_lambda": {"660": 1e-4},
        "polarization_state_by_lambda": {"660": "linear"},
        "RIN_PSD_by_lambda": {"660": 1e-12},
        "pointing_jitter_um_or_rad": 0.02,
        "modulation_frequency_Hz": 3000.0,
        "modulation_depth": 0.8,
        "daq_model": "micro_anchor_nominal_logger",
        "adc_bits": 16,
        "adc_input_range_V": 2.0,
        "adc_sampling_rate_Hz": 10000.0,
        "anti_alias_filter": "bounded_prior",
        "timestamp_jitter": 1e-6,
    }
    result = rv2.laser_daq_sidecar(priors)

    assert result["quantization_noise_rms"] > 0.0
    assert result["sampled_trace_claim_level"] == "absolute_blocked"
    assert result["source_type"] == "bounded_prior"
    assert result["claim_level"] == "absolute_blocked"


def test_blank_rare_tail_is_analytic_not_finite_zero_event_safety():
    result = rv2.blank_false_positive_sidecar(
        threshold_sigma=5.0,
        independent_samples_per_s=1000.0,
        colored_noise_correlation_time_s=0.01,
        acquisition_duration_s=120.0,
    )

    assert result["analytic_gaussian_FP_per_min"] > 0.0
    assert result["rice_or_rayleigh_magnitude_FP_per_min"] > 0.0
    assert result["zero_event_upper_bound"] > 0.0
    assert result["blank_evidence_status"] == "not_measured"
    assert result["false_positive_per_min_claim"] == "analytic_prior_only"
    assert result["finite_monte_carlo_zero_event_inferred"] is False


def test_thermal_404_sidecar_is_gate_only_and_never_boosts_score():
    result = rv2.thermal_404_sidecar(
        wavelength_nm=404,
        I_exc_W_per_m2=1e12,
        alpha_medium_1_per_m=0.02,
        medium_volume_m3=1e-18,
        alpha_glass_1_per_m=0.05,
        glass_volume_m3=1e-18,
        particle_abs_cross_section_m2=1e-16,
        contaminant_abs_cross_section_m2=1e-16,
        filter_leakage_fraction=1e-4,
    )

    assert result["P_medium_abs_W"] > 0.0
    assert result["P_glass_abs_W"] > 0.0
    assert result["optical_score_multiplier"] <= 1.0
    assert result["claim_level"] == "safety_sidecar"


def test_smoke_cost_estimator_enforces_scenario_cap():
    cost = rv2.estimate_smoke_run_cost()
    assert cost["under_review_cap"] is True
    assert cost["event_level_case_count"] == rv2.MAX_EVENT_LEVEL_RUNS_BEFORE_REVIEW

    too_large = rv2.estimate_smoke_run_cost(n_scenario_bundles=9)
    assert too_large["under_review_cap"] is False
