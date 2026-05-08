from __future__ import annotations

import pandas as pd
import pytest

from tools import tsuyama_gold_aligned_detection_lane as lane
from tools import tsuyama_selected_annulus_joint_fit as joint
from nodi_simulator.design_claim_governance import (
    CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS,
    PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1,
)


def test_build_joint_candidates_expands_base_and_variant_ids():
    assert (488, 1200, 550) in joint.JOINT_CASES
    assert (660, 1200, 550) in joint.JOINT_CASES

    candidates = joint.build_joint_candidates(
        base_candidate_ids=["baseline_current_estimates"],
        variant_ids=["paper_10sigma", "paper_5sigma_sensitivity"],
    )
    assert [candidate.candidate_id for candidate in candidates] == [
        "baseline_current_estimates",
        "baseline_current_estimates__paper_5sigma_sensitivity",
    ]
    assert candidates[1].cfg_overrides["threshold_sigma"] == 5.0

    transfer = joint.build_joint_candidates(
        base_candidate_ids=["baseline_current_estimates"],
        variant_ids=["paper_5sigma_signal_size_transfer_fit"],
    )[0]
    assert transfer.candidate_id == (
        "baseline_current_estimates__paper_5sigma_signal_size_transfer_fit"
    )
    assert transfer.signal_transfer_mode == "fit_required_silver_by_wavelength"
    assert transfer.size_response_mode == "fit_required_au_power_law"

    size_only = joint.build_joint_candidates(
        base_candidate_ids=["baseline_current_estimates"],
        variant_ids=["paper_5sigma_size_response_fit"],
    )[0]
    assert size_only.candidate_id == (
        "baseline_current_estimates__paper_5sigma_size_response_fit"
    )
    assert size_only.signal_transfer_mode == "none"
    assert size_only.size_response_mode == "fit_required_au_power_law"


def test_build_joint_candidates_rejects_non_paper_target_variants_early():
    with pytest.raises(ValueError, match="diagnostic-only"):
        joint.build_joint_candidates(
            base_candidate_ids=["baseline_current_estimates"],
            variant_ids=["paper_inphase_absolute"],
        )


def _joint_fixture_rows(*, good: bool) -> pd.DataFrame:
    rows = []
    for wavelength_nm, width_nm, depth_nm in joint.JOINT_CASES:
        wavelength_scale = {488: 1.0, 532: 1.1, 660: 1.2}[wavelength_nm]
        geometry_scale = {800: 1.0, 1200: 0.95}[width_nm]
        for diameter_nm in joint.GOLD_DIAMETERS_NM:
            target = joint.DETECTION_RATE_TARGETS[diameter_nm]["target"]
            selected_rate = target if good else max(0.01, target * 0.15)
            peak = wavelength_scale * geometry_scale * (diameter_nm / 20.0) ** (
                joint.AU_SIZE_EXPONENT_TARGET if good else 6.0
            )
            snr = 12.0 if diameter_nm == 20 else 33.0 if diameter_nm == 30 else 60.0
            width_s = 0.003
            rows.append(
                {
                    "particle_material": "gold",
                    "particle_diameter_nm": diameter_nm,
                    "wavelength_nm": wavelength_nm,
                    "width_nm": width_nm,
                    "depth_nm": depth_nm,
                    "nodi_lockin_frequency_Hz": 3000.0,
                    "threshold_sigma": 10.0,
                    "min_peak_width_s": 0.0025,
                    "readout_observable_mode": "magnitude",
                    "pulse_detection_mode": "positive",
                    "selected_detector_mode_annulus_detection_rate": selected_rate,
                    "selected_detector_mode_annulus_fraction": 0.40,
                    "mean_peak_height": peak,
                    "mean_peak_width_s": width_s,
                    "mean_peak_margin_z": peak * 10.0,
                    "mean_local_snr": snr,
                    "reference_operating_band": "electronics_noise_limited_useful",
                    "rho_physical_envelope_status": "within_envelope",
                    "na_cutoff_active": False,
                }
            )
        gold40_peak = [
            row["mean_peak_height"]
            for row in rows
            if row["particle_material"] == "gold"
            and row["particle_diameter_nm"] == 40
            and row["wavelength_nm"] == wavelength_nm
            and row["width_nm"] == width_nm
            and row["depth_nm"] == depth_nm
        ][0]
        target_ratio = (
            lane.TSUYAMA_2022_TABLE_S1_INTERFEROMETRIC_SCATTERING["silver"][wavelength_nm]
            / lane.TSUYAMA_2022_TABLE_S1_INTERFEROMETRIC_SCATTERING["gold"][wavelength_nm]
        )
        observed_ratio = target_ratio if good else target_ratio * 0.2
        for diameter_nm in joint.SILVER_DIAMETERS_NM:
            rows.append(
                {
                    "particle_material": "silver",
                    "particle_diameter_nm": diameter_nm,
                    "wavelength_nm": wavelength_nm,
                    "width_nm": width_nm,
                    "depth_nm": depth_nm,
                    "nodi_lockin_frequency_Hz": 3000.0,
                    "threshold_sigma": 10.0,
                    "min_peak_width_s": 0.0025,
                    "readout_observable_mode": "magnitude",
                    "pulse_detection_mode": "positive",
                    "selected_detector_mode_annulus_detection_rate": 0.9,
                    "selected_detector_mode_annulus_fraction": 0.40,
                    "mean_peak_height": gold40_peak * observed_ratio,
                    "mean_local_snr": 50.0,
                    "reference_operating_band": "electronics_noise_limited_useful",
                    "rho_physical_envelope_status": "within_envelope",
                    "na_cutoff_active": False,
                }
            )
    return pd.DataFrame(rows)


def _set_gold_peak_exponent(rows: pd.DataFrame, exponent: float) -> pd.DataFrame:
    rows = rows.copy()
    for index, row in rows[rows["particle_material"] == "gold"].iterrows():
        wavelength_scale = {488: 1.0, 532: 1.1, 660: 1.2}[int(row["wavelength_nm"])]
        geometry_scale = {800: 1.0, 1200: 0.95}[int(row["width_nm"])]
        peak = (
            wavelength_scale
            * geometry_scale
            * (float(row["particle_diameter_nm"]) / 20.0) ** exponent
        )
        rows.at[index, "mean_peak_height"] = peak
        rows.at[index, "mean_peak_margin_z"] = peak * 10.0
    for index, row in rows[rows["particle_material"] == "silver"].iterrows():
        wavelength_nm = int(row["wavelength_nm"])
        gold40_peak = rows[
            (rows["particle_material"] == "gold")
            & (rows["particle_diameter_nm"] == 40)
            & (rows["wavelength_nm"] == wavelength_nm)
            & (rows["width_nm"] == row["width_nm"])
            & (rows["depth_nm"] == row["depth_nm"])
        ]["mean_peak_height"].iloc[0]
        target_ratio = (
            lane.TSUYAMA_2022_TABLE_S1_INTERFEROMETRIC_SCATTERING["silver"][wavelength_nm]
            / lane.TSUYAMA_2022_TABLE_S1_INTERFEROMETRIC_SCATTERING["gold"][wavelength_nm]
        )
        rows.at[index, "mean_peak_height"] = gold40_peak * target_ratio
    return rows


def test_joint_summary_rewards_detection_and_signal_ratio_alignment():
    candidate = joint.JointFitCandidate(
        candidate_id="fixture",
        base_candidate_id="baseline_current_estimates",
        cfg_overrides={},
        rationale="test fixture",
    )
    good = joint.summarize_joint_candidate(
        _joint_fixture_rows(good=True),
        candidate,
        n_events=100,
        random_seed=1,
        n_workers=1,
        scenario_id="nodi_2022_10sigma_single",
    )
    bad = joint.summarize_joint_candidate(
        _joint_fixture_rows(good=False),
        candidate,
        n_events=100,
        random_seed=1,
        n_workers=1,
        scenario_id="nodi_2022_10sigma_single",
    )
    assert good["joint_fit_score"] < bad["joint_fit_score"]
    assert good["selected_rate_all_bands_hit"] is True
    assert good["paper_fit_status"] == "candidate_joint_fit_plausible"
    assert good["au60_660_1200x550_selected_annulus_rate"] == joint.DETECTION_RATE_TARGETS[60][
        "target"
    ]
    assert good["au_size_exponent_1200x550_median"] == pytest.approx(
        joint.AU_SIZE_EXPONENT_TARGET
    )
    assert good["au_size_exponent_peak_height_median"] == pytest.approx(
        joint.AU_SIZE_EXPONENT_TARGET
    )
    assert good["au_size_exponent_peak_height_times_width_median"] == pytest.approx(
        joint.AU_SIZE_EXPONENT_TARGET
    )
    assert good["au_size_exponent_scored_observable"] == "peak_height"
    assert good["signal_ratio_target_mode"] == "interferometric_column_ratio"
    assert good["joint_fit_score_strict"] == pytest.approx(good["joint_fit_score"])
    assert "joint_fit_score_formula" in good
    assert "joint_fit_score_recomputed_mie" in good
    assert good["ag40_to_au40_target_ratio_interferometric_column_ratio_660"] == pytest.approx(
        lane.TSUYAMA_2022_TABLE_S1_INTERFEROMETRIC_SCATTERING["silver"][660]
        / lane.TSUYAMA_2022_TABLE_S1_INTERFEROMETRIC_SCATTERING["gold"][660]
    )
    assert good["ag40_to_au40_target_ratio_sqrt_scattering_column_ratio_660"] == pytest.approx(
        (joint.TABLE_S1_SCATTERING_CROSS_SECTION["silver"][660]
        / joint.TABLE_S1_SCATTERING_CROSS_SECTION["gold"][660]) ** 0.5
    )
    assert (
        "ag40_to_au40_target_ratio_recomputed_mie_sqrt_csca_ratio_660" in good
    )
    assert good["signal_ratio_score_interferometric_column_ratio"] == pytest.approx(
        good["signal_ratio_score"]
    )
    assert "raw_signal_ratio_score_sqrt_scattering_column_ratio" in good
    assert bad["paper_fit_status"] == "candidate_needs_signal_transfer_or_phase_fit"


def test_joint_summary_can_apply_explicit_paper_transfer_gain():
    raw_candidate = joint.JointFitCandidate(
        candidate_id="raw",
        base_candidate_id="baseline_current_estimates",
        cfg_overrides={},
        rationale="raw fixture",
    )
    transfer_candidate = joint.JointFitCandidate(
        candidate_id="transfer",
        base_candidate_id="baseline_current_estimates",
        cfg_overrides={},
        rationale="transfer fixture",
        signal_transfer_mode="fit_required_silver_by_wavelength",
    )
    rows = _joint_fixture_rows(good=False)
    raw = joint.summarize_joint_candidate(
        rows,
        raw_candidate,
        n_events=100,
        random_seed=1,
        n_workers=1,
        scenario_id="nodi_2022_10sigma_single",
    )
    transfer = joint.summarize_joint_candidate(
        rows,
        transfer_candidate,
        n_events=100,
        random_seed=1,
        n_workers=1,
        scenario_id="nodi_2022_10sigma_single",
    )
    assert transfer["signal_ratio_score"] < raw["signal_ratio_score"]
    assert transfer["signal_ratio_score"] == 0.0
    assert transfer["applied_silver_transfer_gain_660"] == 5.0
    assert transfer["transfer_gain_guardrail_penalty"] > 0.0


def test_joint_summary_can_apply_bounded_size_response_fit():
    raw_candidate = joint.JointFitCandidate(
        candidate_id="raw",
        base_candidate_id="baseline_current_estimates",
        cfg_overrides={},
        rationale="raw fixture",
    )
    size_fit_candidate = joint.JointFitCandidate(
        candidate_id="size-fit",
        base_candidate_id="baseline_current_estimates",
        cfg_overrides={},
        rationale="size fixture",
        size_response_mode="fit_required_au_power_law",
    )
    rows = _set_gold_peak_exponent(_joint_fixture_rows(good=True), 3.0)
    raw = joint.summarize_joint_candidate(
        rows,
        raw_candidate,
        n_events=100,
        random_seed=1,
        n_workers=1,
        scenario_id="nodi_2022_10sigma_single",
    )
    size_fit = joint.summarize_joint_candidate(
        rows,
        size_fit_candidate,
        n_events=100,
        random_seed=1,
        n_workers=1,
        scenario_id="nodi_2022_10sigma_single",
    )
    assert raw["size_exponent_score"] > size_fit["size_exponent_score"]
    assert (
        size_fit["joint_fit_score_interpretation"]
        == joint.JOINT_FIT_SCORE_INTERPRETATION
    )
    assert size_fit["au_size_exponent_calibrated_median"] == pytest.approx(
        joint.AU_SIZE_EXPONENT_TARGET
    )
    assert size_fit["applied_au_size_response_exponent_delta"] == pytest.approx(
        joint.AU_SIZE_EXPONENT_TARGET - raw["au_size_exponent_raw_median"]
    )
    assert size_fit["size_response_guardrail_penalty"] == 0.0
    assert (
        size_fit["au_size_exponent_diagnostic_status"]
        == "bounded_power_law_size_response_fit_applied"
    )


def test_joint_summary_clips_size_response_when_required_delta_exceeds_guardrail():
    size_fit_candidate = joint.JointFitCandidate(
        candidate_id="size-fit",
        base_candidate_id="baseline_current_estimates",
        cfg_overrides={},
        rationale="size fixture",
        signal_transfer_mode="fit_required_silver_by_wavelength",
        size_response_mode="fit_required_au_power_law",
    )
    rows = _set_gold_peak_exponent(_joint_fixture_rows(good=True), 6.0)
    size_fit = joint.summarize_joint_candidate(
        rows,
        size_fit_candidate,
        n_events=100,
        random_seed=1,
        n_workers=1,
        scenario_id="nodi_2022_10sigma_single",
    )
    assert size_fit["required_au_size_response_exponent_delta"] == pytest.approx(-3.7)
    assert size_fit["applied_au_size_response_exponent_delta"] == pytest.approx(
        joint.MIN_SIZE_RESPONSE_EXPONENT_DELTA
    )
    assert size_fit["au_size_exponent_calibrated_median"] == pytest.approx(4.5)
    assert size_fit["size_exponent_score"] > 0.0
    assert size_fit["size_response_guardrail_penalty"] > 0.0
    assert (
        size_fit["au_size_exponent_diagnostic_status"]
        == "size_response_required_delta_outside_guardrail"
    )
    assert size_fit["paper_fit_status"] == "candidate_fit_guardrail_violation"


def test_run_joint_fit_meta_exports_selected_annulus_traceability(
    monkeypatch,
    tmp_path,
):
    candidate = joint.JointFitCandidate(
        candidate_id="fixture",
        base_candidate_id="baseline_current_estimates",
        cfg_overrides={},
        rationale="test fixture",
    )
    rows = _joint_fixture_rows(good=True)
    rows["selected_detector_mode_annulus_edge_norm_min"] = 0.4
    rows["selected_detector_mode_annulus_edge_norm_max"] = 0.9

    monkeypatch.setattr(
        joint,
        "run_joint_candidate_sweep",
        lambda *args, **kwargs: rows.copy(),
    )

    _, _, meta = joint.run_joint_fit(
        candidates=[candidate],
        n_events=100,
        random_seed=1,
        n_workers=1,
        scenario_id="nodi_2022_10sigma_single",
        output_dir=tmp_path,
    )

    assert meta["analysis_lane"] == "selected_annulus"
    assert meta["schema"] == joint.TARGET_SCHEMA_ID
    assert meta["claim_level"] == CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS
    assert (
        meta["paper_alignment_target"]
        == PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1
    )
    assert meta["selected_annulus_source"] == "initial_position_edge_norm_annulus"
    assert (
        meta["target_notes"]["joint_fit_score_interpretation"]
        == joint.JOINT_FIT_SCORE_INTERPRETATION
    )
    assert meta["target_notes"]["signal_ratio_target_mode"] == (
        "interferometric_column_ratio"
    )
    assert "sqrt_scattering_column_ratio" in (
        meta["target_notes"]["ag_au_peak_ratio_target_modes"]["660"]
    )
    assert meta["paper_alignment_target_metadata_status"] == "validated_per_raw_row"
    assert "threshold_sigma" in meta["paper_alignment_target_required_metadata_fields"]
    assert meta["selected_annulus_edge_norm_min"] == pytest.approx(0.4)
    assert meta["selected_annulus_edge_norm_max"] == pytest.approx(0.9)
