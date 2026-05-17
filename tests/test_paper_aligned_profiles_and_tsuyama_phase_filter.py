from __future__ import annotations

import numpy as np
import pytest

from nodi_simulator.data_objects import DEFAULT_SIM_CFG
from nodi_simulator.paper_aligned_profiles import (
    apply_paper_aligned_profile,
    list_paper_aligned_profiles,
)
from nodi_simulator.tsuyama_phase_filter import (
    classify_phase_filter_validity,
    compute_tsuyama_phase_filter_bfp_field,
    integrate_bfp_roi,
)


class TestPaperAlignedProfiles:
    def test_list_paper_aligned_profiles_exposes_expected_profiles(self):
        profiles = list_paper_aligned_profiles()
        assert set(profiles) >= {
            "diffraction_2020",
            "nodi_2022",
            "paired_2024",
            "paired_2024_10sigma",
            "pod_2019_2020",
        }
        assert profiles["pod_2019_2020"]["status"] == "unavailable"
        assert profiles["diffraction_2020"]["reference_route"] == "paper_aligned_comparison"
        assert profiles["diffraction_2020"]["reference_solver_route"] == "tsuyama_phase_filter_1d"

    def test_apply_paper_aligned_profile_nodi_2022_sets_expected_fields(self):
        cfg = apply_paper_aligned_profile(DEFAULT_SIM_CFG, "nodi_2022")
        assert cfg.reference_model == "paper_aligned_phase_filter"
        assert cfg.reference_route == "paper_aligned_comparison"
        assert cfg.illumination_mode == "overfill"
        assert cfg.readout_preset == "tsuyama_2022_counting_10sigma"
        assert cfg.readout_observable_mode == "magnitude"
        assert cfg.pulse_detection_mode == "positive"
        assert cfg.detection_decision_mode == "single_channel"
        assert cfg.engineering_decision_basis == "single_channel"
        assert cfg.nodi_lockin_frequency_Hz == pytest.approx(3000.0)
        assert cfg.threshold_sigma == pytest.approx(10.0)
        assert cfg.threshold_tail == "one_sided"
        assert cfg.min_peak_width_s == pytest.approx(2.5e-3)
        assert cfg.min_peak_interval_s == pytest.approx(0.1)
        assert cfg.engineering_max_phase_flip_fraction == pytest.approx(1.0)

    def test_apply_paper_aligned_profile_paired_2024_sets_expected_fields(self):
        cfg = apply_paper_aligned_profile(DEFAULT_SIM_CFG, "paired_2024")
        assert cfg.reference_model == "paper_aligned_phase_filter"
        assert cfg.reference_route == "paper_aligned_comparison"
        assert cfg.illumination_mode == "overfill"
        assert cfg.readout_preset == "tsuyama_2024_paired_5sigma"
        assert cfg.readout_observable_mode == "magnitude"
        assert cfg.pulse_detection_mode == "positive"
        assert cfg.detection_decision_mode == "paired_channel"
        assert cfg.engineering_decision_basis == "paired_channel"
        assert cfg.pod_lockin_frequency_Hz == pytest.approx(4100.0)
        assert cfg.nodi_lockin_frequency_Hz == pytest.approx(1200.0)
        assert cfg.threshold_sigma == pytest.approx(5.0)
        assert cfg.threshold_tail == "one_sided"
        assert cfg.pulse_pairing_tolerance_s == pytest.approx(5.0e-2)
        assert cfg.engineering_max_phase_flip_fraction == pytest.approx(1.0)

    def test_apply_paper_aligned_profile_paired_2024_10sigma_sets_expected_fields(self):
        cfg = apply_paper_aligned_profile(DEFAULT_SIM_CFG, "paired_2024_10sigma")
        assert cfg.readout_preset == "tsuyama_2024_paired_10sigma"
        assert cfg.threshold_sigma == pytest.approx(10.0)
        assert cfg.threshold_tail == "one_sided"
        assert cfg.detection_decision_mode == "paired_channel"
        assert cfg.readout_observable_mode == "magnitude"

    def test_apply_paper_aligned_profile_unavailable_pod_profile_raises(self):
        with pytest.raises(ValueError, match="not available"):
            apply_paper_aligned_profile(DEFAULT_SIM_CFG, "pod_2019_2020")


class TestTsuyamaPhaseFilter:
    def test_solver_exports_complex_decomposition_and_numerical_invariants(self):
        result = compute_tsuyama_phase_filter_bfp_field(
            channel_width_m=800e-9,
            channel_depth_m=20e-9,
            wavelength_m=660e-9,
            medium_refractive_index=1.33,
            wall_refractive_index=1.46,
            gaussian_waist_m=2.0e-6,
            n_grid=2048,
        )
        np.testing.assert_allclose(
            result["E_diffraction_BFP"],
            result["E_total_channel_BFP"] - result["E_no_channel_BFP"],
            rtol=1e-10,
            atol=1e-12,
        )
        factor = result["thin_phase_complex_factor"]
        np.testing.assert_allclose(
            result["E_diffraction_BFP"],
            factor * result["thin_phase_basis_BFP"],
            rtol=1e-10,
            atol=1e-12,
        )
        invariants = result["tsuyama_phase_filter_numerical_invariants"]
        assert invariants["W_code_convention"] == "W_code=2*l_paper"
        assert invariants["H_code_convention"] == "H_code=d_paper"
        assert invariants["lambda0_definition"] == "vacuum_wavelength_m"
        assert invariants["fft_sign_convention"] == "forward_exp_minus_i_q_x"
        assert invariants["power_normalization_check"] == "parseval_pass"
        assert invariants["parseval_relative_error"] < 1e-10

    def test_small_phase_perturbation_phase_uses_signed_exp_i_theta_minus_one(self):
        result = compute_tsuyama_phase_filter_bfp_field(
            channel_width_m=800e-9,
            channel_depth_m=1e-12,
            wavelength_m=660e-9,
            medium_refractive_index=1.33,
            wall_refractive_index=1.46,
            gaussian_waist_m=2.0e-6,
            n_grid=2048,
        )
        basis = result["thin_phase_basis_BFP"]
        idx = int(np.argmax(np.abs(basis)))
        perturbation_phase = np.angle(result["E_diffraction_BFP"][idx] / basis[idx])
        expected = -0.5 * np.pi
        assert result["theta_signed_rad"] < 0.0
        assert perturbation_phase == pytest.approx(expected, abs=2e-4)
        assert result["thin_phase_perturbation_phase_rad"] == pytest.approx(
            expected,
            abs=2e-4,
        )

    def test_phase_filter_validity_thresholds_depth_by_lambda0(self):
        shallow = classify_phase_filter_validity(
            channel_width_m=800e-9,
            channel_depth_m=0.7 * 660e-9,
            wavelength_m=660e-9,
            medium_refractive_index=1.33,
            wall_refractive_index=1.46,
        )
        mid = classify_phase_filter_validity(
            channel_width_m=800e-9,
            channel_depth_m=1.0 * 660e-9,
            wavelength_m=660e-9,
            medium_refractive_index=1.33,
            wall_refractive_index=1.46,
        )
        deep = classify_phase_filter_validity(
            channel_width_m=800e-9,
            channel_depth_m=1.8 * 660e-9,
            wavelength_m=660e-9,
            medium_refractive_index=1.33,
            wall_refractive_index=1.46,
        )
        assert shallow["phase_filter_validity"] == "within_phase_filter_assumption"
        assert mid["phase_filter_validity"] == "extrapolated_phase_filter"
        assert deep["phase_filter_validity"] == "requires_blank_or_fullwave"
        assert deep["requires_calibration_or_fullwave"] is True

    def test_integrate_bfp_roi_reports_complex_amplitude_and_mask_units(self):
        result = compute_tsuyama_phase_filter_bfp_field(
            channel_width_m=800e-9,
            channel_depth_m=20e-9,
            wavelength_m=660e-9,
            medium_refractive_index=1.33,
            wall_refractive_index=1.46,
            gaussian_waist_m=2.0e-6,
            n_grid=2048,
        )
        roi = integrate_bfp_roi(
            result["bfp_q_rad_per_m"],
            result["E_diffraction_BFP"],
            roi_half_width_rad_per_m=1.0e6,
        )
        assert isinstance(roi["roi_complex_amplitude"], complex)
        assert roi["detector_mask_units"] == "rad_per_m"
        assert roi["roi_sample_count"] > 0
