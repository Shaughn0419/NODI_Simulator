from __future__ import annotations

import pandas as pd
import pytest

from tools.audits import tsuyama_2022_classification_lane as classification


def test_extract_best_peak_feature_reports_missing_and_detected_peak():
    missing = classification.extract_best_peak_feature(
        {
            "features_nodi": {"n_peaks": 0, "peaks": []},
            "threshold": 5.0,
            "threshold_robust_std": 2.0,
        },
        wavelength_nm=488,
    )
    assert missing["detected_488"] is False
    assert missing["n_peaks_488"] == 0

    detected = classification.extract_best_peak_feature(
        {
            "features_nodi": {
                "n_peaks": 2,
                "peaks": [
                    {"peak_height": 6.0, "peak_width_s": 0.002, "peak_time_s": 0.01},
                    {"peak_height": 9.0, "peak_width_s": 0.003, "peak_time_s": 0.02},
                ],
            },
            "threshold": 5.0,
            "threshold_robust_std": 2.0,
        },
        wavelength_nm=488,
    )
    assert detected["detected_488"] is True
    assert detected["peak_height_488"] == 9.0
    assert detected["peak_margin_z_488"] == pytest.approx(2.0)


def test_linked_feature_rows_and_transfer_gain_are_explicit():
    events = {}
    for material, diameter_nm in classification.CLASSIFICATION_CLASSES:
        height = 10.0
        if material == "silver" and diameter_nm == 40:
            height = 20.0
        events[(material, diameter_nm, 488)] = [
            {
                "features_nodi": {
                    "n_peaks": 1,
                    "peaks": [
                        {
                            "peak_height": height,
                            "peak_width_s": 0.003,
                            "peak_time_s": 0.01,
                            "peak_threshold_left_time_s": 0.0085,
                            "peak_threshold_right_time_s": 0.0115,
                        }
                    ],
                },
                "threshold": 1.0,
                "threshold_robust_std": 1.0,
            }
        ]
        events[(material, diameter_nm, 532)] = [
            {
                "pulse_time_s": [0.008, 0.009, 0.010, 0.011, 0.012],
                "signal_noisy": [1.0, height * 0.8, height, height * 0.9, 1.0],
                "threshold": 1.0,
                "threshold_robust_std": 1.0,
            }
        ]

    table = classification.build_linked_feature_rows(events, width_nm=800, depth_nm=550)
    assert len(table) == 4
    assert table["usable_both_detected"].all()
    assert table["usable_for_paper_svm"].all()
    assert set(table["class_label"]) == {"Au40", "Au60", "Ag40", "Ag60"}

    gains = classification.compute_silver_transfer_gains(table)
    assert gains[488] == pytest.approx(1.9 / 2.0)
    with_transfer = classification.apply_silver_transfer_columns(table, gains)
    ag40 = with_transfer[with_transfer["class_label"] == "Ag40"].iloc[0]
    assert ag40["paper_transfer_peak_height_488"] == pytest.approx(20.0 * gains[488])


def test_summarize_feature_table_marks_protocol_as_feature_export_only():
    table = pd.DataFrame(
        [
            {
                "class_label": "Au40",
                    "particle_material": "gold",
                    "particle_diameter_nm": 40,
                    "usable_for_paper_svm": True,
                }
            ]
        )
    summary = classification.summarize_feature_table(
        table,
        n_events=1,
        width_nm=800,
        depth_nm=550,
        silver_transfer_gains={488: 1.0, 532: 1.0},
    )
    assert summary["feature_rows"] == 1
    assert summary["paper_protocol_match_status"].startswith("feature_export_matches")


def test_summarize_feature_table_keeps_both_detected_and_paper_svm_counts_separate():
    table = pd.DataFrame(
        [
            {
                "class_label": "Au40",
                "particle_material": "gold",
                "particle_diameter_nm": 40,
                "usable_both_detected": False,
                "usable_for_paper_svm": True,
            },
            {
                "class_label": "Ag40",
                "particle_material": "silver",
                "particle_diameter_nm": 40,
                "usable_both_detected": True,
                "usable_for_paper_svm": True,
            },
            {
                "class_label": "Au60",
                "particle_material": "gold",
                "particle_diameter_nm": 60,
                "usable_both_detected": True,
                "usable_for_paper_svm": False,
            },
        ]
    )
    summary = classification.summarize_feature_table(
        table,
        n_events=3,
        width_nm=800,
        depth_nm=550,
        silver_transfer_gains={488: 1.0, 532: 1.0},
    )
    assert summary["usable_both_detected_rows"] == 2
    assert summary["usable_for_paper_svm_rows"] == 2
    assert summary["usable_class_counts_json"] == '{"Ag40":1,"Au40":1}'


def test_optional_svm_gate_does_not_claim_accuracy_when_dependency_missing():
    table = pd.DataFrame(
        [
            {
                "class_label": "Au40",
                "usable_for_paper_svm": True,
                "paper_transfer_peak_height_488": 1.0,
                "peak_width_s_488": 0.003,
                "paper_transfer_peak_height_532": 1.0,
                "peak_width_s_532": 0.003,
            },
            {
                "class_label": "Ag40",
                "usable_for_paper_svm": True,
                "paper_transfer_peak_height_488": 2.0,
                "peak_width_s_488": 0.003,
                "paper_transfer_peak_height_532": 2.0,
                "peak_width_s_532": 0.003,
            },
        ]
    )
    result = classification.evaluate_optional_svm(
        table,
        random_seed=1,
        use_paper_transfer=True,
    )
    if result["sklearn_available"] is False:
        assert result["svm_accuracy_status"] == "not_computed_missing_optional_sklearn_dependency"
        assert result["svm_accuracy_claim_level"] == "no_accuracy_claim"
    else:
        assert result["svm_accuracy_claim_level"] != "paper_experimental_reproduction"
