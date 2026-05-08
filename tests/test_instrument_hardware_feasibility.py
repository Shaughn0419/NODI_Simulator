from __future__ import annotations

import pandas as pd

from tools import instrument_hardware_feasibility as hw


def test_lockin_enbw_decreases_with_tau_and_filter_order():
    fast = hw.lockin_enbw_hz(1.0e-3, 1)
    slow = hw.lockin_enbw_hz(2.0e-3, 1)
    higher_order = hw.lockin_enbw_hz(1.0e-3, 4)

    assert fast > slow
    assert fast > higher_order


def test_current_input_is_preferred_over_50ohm_for_weak_photocurrent():
    rows = hw.feasibility_rows(
        detector=hw.ET2030Prior(),
        lockin=hw.LI5640Prior(),
        wavelengths_nm=(660,),
        tau_ms_values=(2.0,),
        filter_orders=(1,),
        reference_powers_W=(1.0e-8,),
    )
    frame = pd.DataFrame(rows)
    au20 = frame[frame["target_snr_label"].eq("Au20_paper_normalized")].iloc[0]

    assert au20["current_input_status"] == "comfortable_margin"
    assert au20["voltage_50ohm_status"] == "below_minimum_sensitivity"
    assert (
        au20["connection_recommendation"]
        == "prefer_current_input_or_low_noise_TIA"
    )
    assert au20["detector_saturation_status"] == "comfortable_margin"


def test_overdriven_reference_power_blocks_feasibility_recommendation():
    rows = hw.feasibility_rows(
        detector=hw.ET2030Prior(),
        lockin=hw.LI5640Prior(),
        wavelengths_nm=(660,),
        tau_ms_values=(2.0,),
        filter_orders=(1,),
        reference_powers_W=(1.0,),
    )
    frame = pd.DataFrame(rows)
    au20 = frame[frame["target_snr_label"].eq("Au20_paper_normalized")].iloc[0]

    assert au20["detector_linear_current_margin"] < 1.0
    assert (
        au20["detector_saturation_status"]
        == "over_detector_linear_current_limit"
    )
    assert au20["connection_recommendation"] == (
        "reduce_reference_power_detector_over_linear_limit"
    )


def test_required_modulation_power_increases_with_target_snr():
    rows = hw.feasibility_rows(
        detector=hw.ET2030Prior(),
        lockin=hw.LI5640Prior(),
        wavelengths_nm=(532,),
        tau_ms_values=(2.0,),
        filter_orders=(1,),
        reference_powers_W=(1.0e-8,),
    )
    frame = pd.DataFrame(rows).set_index("target_snr_label")

    assert (
        frame.loc["Au30_paper_normalized", "required_modulation_power_W"]
        > frame.loc["Au20_paper_normalized", "required_modulation_power_W"]
    )


def test_write_outputs_keeps_hardware_layer_non_calibrating(tmp_path):
    feasibility, summary = hw.write_outputs(
        output_dir=tmp_path,
        detector=hw.ET2030Prior(),
        lockin=hw.LI5640Prior(),
        wavelengths_nm=(488, 660),
        tau_ms_values=(2.0,),
        filter_orders=(1,),
        reference_powers_W=(1.0e-8,),
    )

    assert not feasibility.empty
    assert summary["detector_unit_chain_unlocked"] is False
    assert summary["ev_full_grid_writeback"] is False
    assert summary["selected_annulus_changed"] is False
    assert summary["global_material_defaults_changed"] is False
    assert summary["detector_saturation_status_counts"] == {
        "comfortable_margin": len(feasibility)
    }
    assert (tmp_path / hw.PRIOR_FILENAME).exists()
    assert (tmp_path / hw.FEASIBILITY_FILENAME).exists()
    assert (tmp_path / hw.SUMMARY_JSON_FILENAME).exists()
    assert (tmp_path / hw.REPORT_FILENAME).exists()
