from __future__ import annotations

import pandas as pd

from tools.audits import tsuyama_paper_target_audit as target_audit
from tools.one_shot import tsuyama_phase2_acceptance_report as acceptance
from tools.audits import tsuyama_selected_annulus_joint_fit as joint


def _best_candidate_row() -> dict[str, object]:
    row: dict[str, object] = {
        "candidate_id": "fixture__paper_5sigma_signal_size_transfer_fit",
        "joint_fit_score": 0.1,
        "paper_fit_status": "candidate_joint_fit_with_paper_transfer",
        "signal_ratio_score": 0.0,
        "transfer_gain_guardrail_penalty": 0.0,
        "size_response_guardrail_penalty": 0.0,
        "annulus_fraction_min": 0.40,
        "reference_bad": False,
        "rho_bad": False,
        "na_cutoff_active": False,
        "au_size_exponent_raw_median": 3.0,
        "au_size_exponent_calibrated_median": 2.3,
        "applied_au_size_response_exponent_delta": -0.7,
        "au30_to_au20_snr_ratio_median": joint.AU30_TO_AU20_SNR_RATIO_TARGET,
    }
    for wavelength_nm in joint.JOINT_WAVELENGTHS_NM:
        row[f"ag40_to_au40_target_ratio_{wavelength_nm}"] = 2.0
        row[f"ag40_to_au40_calibrated_peak_ratio_{wavelength_nm}"] = 2.0
        row[f"ag40_to_au40_peak_ratio_{wavelength_nm}"] = 2.0
        for target_mode in joint.SIGNAL_RATIO_TARGET_MODES:
            row[f"ag40_to_au40_target_ratio_{target_mode}_{wavelength_nm}"] = 2.0
    for wavelength_nm, width_nm, depth_nm in joint.JOINT_CASES:
        for diameter_nm, target in joint.DETECTION_RATE_TARGETS.items():
            row[
                f"au{diameter_nm}_{wavelength_nm}_{width_nm}x{depth_nm}"
                "_selected_annulus_rate"
            ] = target["target"]
    return row


def _with_snr_anchor_columns(row: dict[str, object]) -> dict[str, object]:
    for wavelength_nm, width_nm, depth_nm in joint.JOINT_CASES:
        case_key = f"{wavelength_nm}_{width_nm}x{depth_nm}"
        row[f"au20_{case_key}_mean_local_snr"] = acceptance.PAPER_AU20_SNR_TARGET
        row[f"au30_{case_key}_mean_local_snr"] = acceptance.PAPER_AU30_SNR_TARGET
    return row


def _full_inverse_rows(*, raw_signal_score: float, raw_size_score: float) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for seed in (42, 43, 44):
        row = _best_candidate_row()
        row.update(
            {
                "candidate_id": "fixture__paper_5sigma_signal_size_transfer_fit",
                "family_id": "E_local_transfer_size_response",
                "random_seed": seed,
                "joint_fit_score": 0.1 + (seed - 42) * 0.001,
                "joint_signal_transfer_mode": "fit_required_silver_by_wavelength",
                "joint_size_response_mode": "fit_required_au_power_law",
            }
        )
        rows.append(row)
    for seed in (42, 43, 44):
        row = _best_candidate_row()
        row.update(
            {
                "candidate_id": "raw_noise_candidate",
                "family_id": "A_blank_threshold_noise",
                "random_seed": seed,
                "joint_fit_score": 2.0 + (seed - 42) * 0.001,
                "paper_fit_status": "candidate_needs_signal_transfer_or_phase_fit",
                "joint_signal_transfer_mode": "none",
                "joint_size_response_mode": "none",
                "signal_ratio_score": raw_signal_score,
                "size_exponent_score": raw_size_score,
                "au_size_exponent_raw_median": 2.3 if raw_size_score <= 0.16 else 3.6,
                "au_size_exponent_calibrated_median": 2.3,
                "applied_au_size_response_exponent_delta": 0.0,
            }
        )
        rows.append(row)
    return rows


def test_acceptance_baseline_passes_guardrails_with_source_audited_targets():
    summary, guardrails, shadow, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([_best_candidate_row()]),
        target_frame=target_audit.build_target_frame(),
        classification_summary=pd.DataFrame(
            [
                {
                    "class_count": 4,
                    "usable_min_class_count": 10,
                    "paper_protocol_match_status": (
                        "feature_export_matches_488_pulse_window_532_maximum_protocol"
                    ),
                    "svm_accuracy_claim_level": "no_accuracy_claim",
                }
            ]
        ),
        route_summary=pd.DataFrame(
            [
                {
                    "raw_mean_selected_annulus_uplift": 1.2,
                    "raw_mean_selected_annulus_fraction": 0.4,
                    "raw_mean_selected_annulus_contribution": 0.2,
                    "raw_mean_all_crossing_detection": 0.15,
                    "raw_mean_selected_annulus_detection": 0.24,
                    "selected_annulus_reference_interpretation": (
                        "reference_useful_selected_cross_check"
                    ),
                }
            ]
        ),
    )

    assert set(guardrails["status"]) == {"pass"}
    assert payload["candidate_release_status"] == "baseline_requires_phase2_inverse_confirmation"
    assert summary.loc[summary["metric"] == "no_go_status", "status"].iloc[0] == "pass"
    assert shadow["status"].iloc[0] == "available"


def test_acceptance_uses_seed_median_candidate_for_signing():
    rows: list[dict[str, object]] = []
    for score in (0.0, 10.0, 10.0):
        row = _best_candidate_row()
        row.update(
            {
                "candidate_id": "single_seed_winner",
                "family_id": "D2_operator_phase_bfp_raw",
                "random_seed": len(rows),
                "joint_fit_score": score,
                "joint_signal_transfer_mode": "none",
                "joint_size_response_mode": "none",
            }
        )
        rows.append(row)
    for score in (1.0, 1.0, 1.0):
        row = _best_candidate_row()
        row.update(
            {
                "candidate_id": "seed_median_winner",
                "family_id": "D2_operator_phase_bfp_raw",
                "random_seed": 100 + len(rows),
                "joint_fit_score": score,
                "joint_signal_transfer_mode": "none",
                "joint_size_response_mode": "none",
            }
        )
        rows.append(row)

    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame(rows),
        target_frame=target_audit.build_target_frame(),
    )

    assert payload["best_candidate_id"] == "seed_median_winner"
    assert payload["acceptance_aggregation_mode"] == "candidate_seed_median"


def test_acceptance_warns_when_only_au20_lower_bound_is_missing():
    row = _best_candidate_row()
    for wavelength_nm, width_nm, depth_nm in joint.JOINT_CASES:
        row[f"au20_{wavelength_nm}_{width_nm}x{depth_nm}_selected_annulus_rate"] = 0.05

    summary, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([row]),
        target_frame=target_audit.build_target_frame(),
    )

    assert payload["no_go_reasons"] == []
    assert payload["candidate_release_status"] == "baseline_requires_phase2_inverse_confirmation"
    assert payload["au20_detection_status"] == "Au20_low_sensitivity_warning"
    assert (
        summary.set_index("metric").loc["detection_alignment", "status"]
        == "partial_pass_with_Au20_low_warning"
    )


def test_acceptance_warns_on_borderline_au60_miss_without_release_blocker():
    row = _best_candidate_row()
    for wavelength_nm, width_nm, depth_nm in joint.JOINT_CASES:
        row[f"au60_{wavelength_nm}_{width_nm}x{depth_nm}_selected_annulus_rate"] = 0.845

    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([row]),
        target_frame=target_audit.build_target_frame(),
    )

    assert payload["au30_60_detection_status"] == "warning_Au30_60_borderline_or_minor_miss"
    assert "detection_practical_gate_not_met" not in payload["no_go_reasons"]


def test_acceptance_stops_on_severe_au60_detection_miss():
    row = _best_candidate_row()
    for wavelength_nm, width_nm, depth_nm in joint.JOINT_CASES:
        row[f"au60_{wavelength_nm}_{width_nm}x{depth_nm}_selected_annulus_rate"] = 0.75

    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([row]),
        target_frame=target_audit.build_target_frame(),
    )

    assert payload["au30_60_detection_status"] == "hard_fail_Au30_60_practical_gate"
    assert "detection_practical_gate_not_met" in payload["no_go_reasons"]


def test_acceptance_stops_when_au20_is_over_detected():
    row = _best_candidate_row()
    for wavelength_nm, width_nm, depth_nm in joint.JOINT_CASES[:2]:
        row[f"au20_{wavelength_nm}_{width_nm}x{depth_nm}_selected_annulus_rate"] = 0.80

    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([row]),
        target_frame=target_audit.build_target_frame(),
    )

    assert payload["au20_detection_status"] == "hard_fail_Au20_over_detected"
    assert "detection_practical_gate_not_met" in payload["no_go_reasons"]
    assert payload["candidate_release_status"] == "negative_or_diagnostic_result_only"


def test_acceptance_does_not_mix_au20_low_severity_with_borderline_high():
    row = _best_candidate_row()
    for wavelength_nm, width_nm, depth_nm in joint.JOINT_CASES:
        row[f"au20_{wavelength_nm}_{width_nm}x{depth_nm}_selected_annulus_rate"] = 0.05
    wavelength_nm, width_nm, depth_nm = joint.JOINT_CASES[0]
    row[f"au20_{wavelength_nm}_{width_nm}x{depth_nm}_selected_annulus_rate"] = 0.455

    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([row]),
        target_frame=target_audit.build_target_frame(),
    )

    assert payload["au20_detection_status"] == "Au20_low_sensitivity_warning"
    assert "detection_practical_gate_not_met" not in payload["no_go_reasons"]


def test_acceptance_warns_on_single_au20_high_outlier():
    row = _best_candidate_row()
    wavelength_nm, width_nm, depth_nm = joint.JOINT_CASES[0]
    row[f"au20_{wavelength_nm}_{width_nm}x{depth_nm}_selected_annulus_rate"] = 0.80

    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([row]),
        target_frame=target_audit.build_target_frame(),
    )

    assert payload["au20_detection_status"] == "Au20_high_outlier_warning"
    assert "detection_practical_gate_not_met" not in payload["no_go_reasons"]


def test_acceptance_stops_when_au30_60_detection_gate_fails():
    row = _best_candidate_row()
    for wavelength_nm, width_nm, depth_nm in joint.JOINT_CASES:
        row[f"au40_{wavelength_nm}_{width_nm}x{depth_nm}_selected_annulus_rate"] = 0.10

    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([row]),
        target_frame=target_audit.build_target_frame(),
    )

    assert payload["au30_60_detection_status"] == "hard_fail_Au30_60_practical_gate"
    assert "detection_practical_gate_not_met" in payload["no_go_reasons"]


def test_acceptance_stops_when_au20_au30_detection_trend_inverts():
    row = _best_candidate_row()
    for wavelength_nm, width_nm, depth_nm in joint.JOINT_CASES:
        row[f"au20_{wavelength_nm}_{width_nm}x{depth_nm}_selected_annulus_rate"] = 0.40
        row[f"au30_{wavelength_nm}_{width_nm}x{depth_nm}_selected_annulus_rate"] = 0.30

    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([row]),
        target_frame=target_audit.build_target_frame(),
    )

    assert payload["au20_detection_status"] == "hard_fail_Au20_Au30_inversion"
    assert "detection_practical_gate_not_met" in payload["no_go_reasons"]


def test_acceptance_stops_when_transfer_fit_lacks_raw_family_alignment():
    rows = _full_inverse_rows(raw_signal_score=0.8, raw_size_score=1.5)
    for row in rows:
        if row.get("family_id") == "A_blank_threshold_noise":
            for wavelength_nm in joint.JOINT_WAVELENGTHS_NM:
                row[f"ag40_to_au40_peak_ratio_{wavelength_nm}"] = 0.1
    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame(rows),
        target_frame=target_audit.build_target_frame(),
    )

    assert "raw_signal_ratio_alignment_not_met" in payload["no_go_reasons"]
    assert "raw_size_response_alignment_not_met" in payload["no_go_reasons"]
    assert payload["raw_family_alignment"]["status"] == "fail"
    assert (
        payload["local_fit_interpretability_status"]
        == "bounded_local_fit_diagnostic_only"
    )
    assert payload["candidate_release_status"] == "negative_or_diagnostic_result_only"


def test_acceptance_can_sign_full_inverse_when_raw_family_shadow_aligns():
    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame(
            _full_inverse_rows(raw_signal_score=0.01, raw_size_score=0.01)
        ),
        target_frame=target_audit.build_target_frame(),
    )

    assert payload["no_go_reasons"] == []
    assert payload["raw_family_alignment"]["status"] == "pass"
    assert payload["candidate_release_status"] == "accepted_paper_calibrated_proxy_candidate"


def test_acceptance_does_not_sign_raw_best_when_raw_size_alignment_fails():
    rows = []
    for seed in (42, 43, 44):
        row = _best_candidate_row()
        row.update(
            {
                "candidate_id": "raw_best_candidate",
                "family_id": "D2_operator_phase_bfp_raw",
                "random_seed": seed,
                "joint_fit_score": 0.5 + (seed - 42) * 0.001,
                "paper_fit_status": "candidate_needs_signal_transfer_or_phase_fit",
                "joint_signal_transfer_mode": "none",
                "joint_size_response_mode": "none",
                "signal_ratio_score": 0.01,
                "size_exponent_score": 1.5,
                "au_size_exponent_raw_median": 3.5,
                "au_size_exponent_calibrated_median": 3.5,
                "applied_au_size_response_exponent_delta": 0.0,
            }
        )
        for wavelength_nm in joint.JOINT_WAVELENGTHS_NM:
            row[f"ag40_to_au40_peak_ratio_{wavelength_nm}"] = row[
                f"ag40_to_au40_target_ratio_{wavelength_nm}"
            ]
        rows.append(row)

    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame(rows),
        target_frame=target_audit.build_target_frame(),
    )

    assert payload["no_go_reasons"] == ["raw_size_response_alignment_not_met"]
    assert payload["raw_size_response_alignment_status"] == "fail"
    assert payload["candidate_release_status"] == "negative_or_diagnostic_result_only"


def test_acceptance_no_go_splits_formula_signal_pass_from_size_failure():
    rows = _full_inverse_rows(raw_signal_score=0.8, raw_size_score=1.5)
    for row in rows:
        if row.get("family_id") == "A_blank_threshold_noise":
            for wavelength_nm in joint.JOINT_WAVELENGTHS_NM:
                row[f"ag40_to_au40_peak_ratio_{wavelength_nm}"] = 2.0
                row[
                    f"ag40_to_au40_target_ratio_sqrt_scattering_column_ratio_{wavelength_nm}"
                ] = 2.0
                row[
                    f"ag40_to_au40_target_ratio_interferometric_column_ratio_{wavelength_nm}"
                ] = 20.0

    summary, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame(rows),
        target_frame=target_audit.build_target_frame(),
    )

    assert payload["raw_signal_ratio_alignment_status"] == (
        "pass_formula_consistent_table_s1_target_only"
    )
    assert payload["no_go_reasons"] == ["raw_size_response_alignment_not_met"]
    assert payload["diagnostic_warnings"] == [
        "interferometric_column_signal_unresolved_formula_signal_pass"
    ]
    indexed = summary.set_index("metric")
    assert indexed.loc["formula_consistent_signal_ratio_pass", "status"] == "pass"
    assert indexed.loc["strict_interferometric_column_signal_ratio_pass", "status"] == "pass"


def test_acceptance_primary_score_mode_can_sort_by_formula_score():
    rows = []
    for candidate_id, strict_score, formula_score in (
        ("strict_winner", 0.1, 10.0),
        ("formula_winner", 0.2, 0.01),
    ):
        row = _best_candidate_row()
        row.update(
            {
                "candidate_id": candidate_id,
                "family_id": "D2_operator_phase_bfp_raw",
                "random_seed": 42,
                "joint_fit_score": strict_score,
                "joint_fit_score_formula": formula_score,
                "joint_signal_transfer_mode": "none",
                "joint_size_response_mode": "none",
            }
        )
        rows.append(row)

    _, _, _, strict_payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame(rows),
        target_frame=target_audit.build_target_frame(),
    )
    _, _, _, formula_payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame(rows),
        target_frame=target_audit.build_target_frame(),
        primary_score_mode="formula",
    )

    assert strict_payload["best_candidate_id"] == "strict_winner"
    assert formula_payload["best_candidate_id"] == "formula_winner"
    assert formula_payload["primary_score_column"] == "joint_fit_score_formula"


def test_acceptance_primary_score_mode_can_sort_by_paper_reproduction_score():
    strict_winner = _with_snr_anchor_columns(_best_candidate_row())
    strict_winner.update(
        {
            "candidate_id": "strict_winner",
            "family_id": "D2_operator_phase_bfp_raw",
            "joint_fit_score": 0.1,
            "joint_signal_transfer_mode": "none",
            "joint_size_response_mode": "none",
            "au_size_exponent_raw_median": 4.0,
        }
    )
    reproduction_winner = _with_snr_anchor_columns(_best_candidate_row())
    reproduction_winner.update(
        {
            "candidate_id": "reproduction_winner",
            "family_id": "D2_operator_phase_bfp_raw",
            "joint_fit_score": 1.0,
            "joint_signal_transfer_mode": "none",
            "joint_size_response_mode": "none",
            "au_size_exponent_raw_median": joint.AU_SIZE_EXPONENT_TARGET,
        }
    )
    frame = pd.DataFrame([strict_winner, reproduction_winner])

    _, _, _, strict_payload = acceptance.build_acceptance_report(
        joint_summary=frame,
        target_frame=target_audit.build_target_frame(),
    )
    _, _, _, reproduction_payload = acceptance.build_acceptance_report(
        joint_summary=frame,
        target_frame=target_audit.build_target_frame(),
        primary_score_mode="paper_reproduction_formula",
    )

    assert strict_payload["best_candidate_id"] == "strict_winner"
    assert reproduction_payload["best_candidate_id"] == "reproduction_winner"
    assert reproduction_payload["primary_score_column"] == "paper_reproduction_score_formula"
    assert (
        reproduction_payload["paper_reproduction"]["paper_reproduction_claim_level"]
        == "paper_reproduction_fit_only"
    )


def test_paper_reproduction_snr_response_term_reduces_ratio_loss():
    row = _best_candidate_row()
    for wavelength_nm, width_nm, depth_nm in joint.JOINT_CASES:
        case_key = f"{wavelength_nm}_{width_nm}x{depth_nm}"
        row[f"au20_{case_key}_mean_local_snr"] = 10.0
        row[f"au30_{case_key}_mean_local_snr"] = 35.0
    row["au30_to_au20_snr_ratio_median"] = 3.5

    with_metrics = acceptance.add_paper_reproduction_metrics(pd.DataFrame([row]))
    metric_row = with_metrics.iloc[0]

    assert metric_row["paper_reproduction_snr_response_exponent"] < 1.0
    assert metric_row["paper_reproduction_snr_response_status"] == "bounded_preferred"
    assert (
        metric_row["paper_reproduction_snr_response_ratio_loss"]
        < metric_row["paper_reproduction_snr_ratio_loss"]
    )
    assert (
        metric_row["paper_reproduction_score_formula_snr_response"]
        < metric_row["paper_reproduction_score_formula"]
    )


def test_paper_reproduction_response_compression_maps_size_exponent():
    row = _with_snr_anchor_columns(_best_candidate_row())
    row.update(
        {
            "candidate_id": "response_compression_fixture",
            "joint_signal_transfer_mode": "none",
            "joint_size_response_mode": "none",
            "au_size_exponent_raw_median": 3.0,
        }
    )

    with_metrics = acceptance.add_paper_reproduction_metrics(pd.DataFrame([row]))
    metric_row = with_metrics.iloc[0]

    expected_gamma = joint.AU_SIZE_EXPONENT_TARGET / 3.0
    assert abs(
        metric_row["paper_reproduction_applied_response_compression_gamma"]
        - expected_gamma
    ) < 1e-12
    assert abs(
        metric_row[
            "paper_reproduction_response_compression_corrected_au_size_exponent"
        ]
        - joint.AU_SIZE_EXPONENT_TARGET
    ) < 1e-12
    assert (
        metric_row["paper_reproduction_response_compression_gamma_status"]
        == "bounded_preferred"
    )
    assert (
        metric_row["paper_reproduction_candidate_class_response_compression"]
        == "bounded_reproduction_fit"
    )
    assert (
        bool(metric_row["paper_reproduction_accepted_raw_calibration"]) is False
    )


def test_acceptance_primary_score_mode_can_sort_by_snr_response_score():
    plain = _best_candidate_row()
    plain.update(
        {
            "candidate_id": "plain_winner",
            "family_id": "F_paper_reproduction_fit",
            "joint_fit_score": 0.1,
            "joint_signal_transfer_mode": "none",
            "joint_size_response_mode": "fit_required_au_power_law",
            "au_size_exponent_raw_median": 3.05,
        }
    )
    response = _best_candidate_row()
    response.update(
        {
            "candidate_id": "response_winner",
            "family_id": "F_paper_reproduction_fit",
            "joint_fit_score": 1.0,
            "joint_signal_transfer_mode": "none",
            "joint_size_response_mode": "fit_required_au_power_law",
            "au_size_exponent_raw_median": 3.05,
        }
    )
    for wavelength_nm, width_nm, depth_nm in joint.JOINT_CASES:
        case_key = f"{wavelength_nm}_{width_nm}x{depth_nm}"
        plain[f"au20_{case_key}_mean_local_snr"] = 10.0
        plain[f"au30_{case_key}_mean_local_snr"] = 35.0
        response[f"au20_{case_key}_mean_local_snr"] = acceptance.PAPER_AU20_SNR_TARGET
        response[f"au30_{case_key}_mean_local_snr"] = acceptance.PAPER_AU30_SNR_TARGET
    plain["au30_to_au20_snr_ratio_median"] = 3.5
    response["au30_to_au20_snr_ratio_median"] = joint.AU30_TO_AU20_SNR_RATIO_TARGET

    _, _, _, strict_payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([plain, response]),
        target_frame=target_audit.build_target_frame(),
    )
    _, _, _, response_payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([plain, response]),
        target_frame=target_audit.build_target_frame(),
        primary_score_mode="paper_reproduction_snr_response",
    )

    assert strict_payload["best_candidate_id"] == "plain_winner"
    assert response_payload["best_candidate_id"] == "response_winner"
    assert (
        response_payload["primary_score_column"]
        == "paper_reproduction_score_formula_snr_response"
    )


def test_acceptance_primary_score_mode_can_sort_by_response_compression_score():
    hard_fail = _with_snr_anchor_columns(_best_candidate_row())
    hard_fail.update(
        {
            "candidate_id": "hard_fail_gamma_fixture",
            "family_id": "F_paper_reproduction_fit",
            "joint_fit_score": 0.1,
            "joint_signal_transfer_mode": "none",
            "joint_size_response_mode": "fit_required_au_power_law",
            "au_size_exponent_raw_median": 5.0,
        }
    )
    response_winner = _with_snr_anchor_columns(_best_candidate_row())
    response_winner.update(
        {
            "candidate_id": "response_compression_winner",
            "family_id": "F_paper_reproduction_fit",
            "joint_fit_score": 1.0,
            "joint_signal_transfer_mode": "none",
            "joint_size_response_mode": "fit_required_au_power_law",
            "au_size_exponent_raw_median": 3.0,
        }
    )

    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([hard_fail, response_winner]),
        target_frame=target_audit.build_target_frame(),
        primary_score_mode="paper_reproduction_response_compression",
    )

    assert payload["best_candidate_id"] == "response_compression_winner"
    assert (
        payload["primary_score_column"]
        == "paper_reproduction_score_response_compression"
    )
    assert (
        payload["paper_reproduction"][
            "paper_reproduction_status_response_compression"
        ]
        != "fail_guardrail_response_compression"
    )
    assert (
        payload["primary_paper_reproduction_status"]
        == payload["paper_reproduction"][
            "paper_reproduction_status_response_compression"
        ]
    )
    assert (
        payload["primary_paper_reproduction_score"]
        == payload["paper_reproduction"][
            "paper_reproduction_score_response_compression"
        ]
    )
    assert (
        payload["primary_paper_reproduction_candidate_class"]
        == payload["paper_reproduction"][
            "paper_reproduction_candidate_class_response_compression"
        ]
    )
    assert (
        payload["primary_paper_reproduction"][
            "primary_paper_reproduction_score_key"
        ]
        == "paper_reproduction_score_response_compression"
    )
    assert payload["paper_reproduction"]["paper_reproduction_accepted_raw_calibration"] is False


def test_response_compression_reports_gamma_as_solved_fit_term():
    row = _with_snr_anchor_columns(_best_candidate_row())
    row.update(
        {
            "candidate_id": "response_compression_note_fixture",
            "family_id": "F_paper_reproduction_fit",
            "joint_signal_transfer_mode": "none",
            "joint_size_response_mode": "fit_required_au_power_law",
            "au_size_exponent_raw_median": 3.0,
        }
    )

    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([row]),
        target_frame=target_audit.build_target_frame(),
        primary_score_mode="paper_reproduction_response_compression",
    )

    assert (
        payload["paper_reproduction"][
            "paper_reproduction_response_compression_size_fit_note"
        ]
        == (
            "gamma_is_solved_from_target_over_raw_exponent;"
            "residual_test_is_snr_signal_detection_complexity"
        )
    )


def test_reviewed_reproduction_score_reports_strict_without_scoring_it():
    aligned = _with_snr_anchor_columns(_best_candidate_row())
    aligned.update(
        {
            "candidate_id": "aligned_strict_fixture",
            "joint_signal_transfer_mode": "none",
            "joint_size_response_mode": "fit_required_au_power_law",
            "au_size_exponent_raw_median": 3.05,
        }
    )
    strict_mismatch = dict(aligned)
    strict_mismatch["candidate_id"] = "strict_mismatch_fixture"
    for wavelength_nm in joint.JOINT_WAVELENGTHS_NM:
        strict_mismatch[
            f"ag40_to_au40_target_ratio_interferometric_column_ratio_{wavelength_nm}"
        ] = 20.0

    metrics = acceptance.add_paper_reproduction_metrics(
        pd.DataFrame([aligned, strict_mismatch])
    ).set_index("candidate_id")

    assert (
        metrics.loc[
            "strict_mismatch_fixture",
            "paper_reproduction_strict_signal_diagnostic_loss",
        ]
        > metrics.loc[
            "aligned_strict_fixture",
            "paper_reproduction_strict_signal_diagnostic_loss",
        ]
    )
    assert (
        metrics.loc[
            "strict_mismatch_fixture",
            "paper_reproduction_score_formula_snr_response",
        ]
        > metrics.loc[
            "aligned_strict_fixture",
            "paper_reproduction_score_formula_snr_response",
        ]
    )
    assert (
        metrics.loc[
            "strict_mismatch_fixture",
            "paper_reproduction_score_reviewed_snr_response",
        ]
        == metrics.loc[
            "aligned_strict_fixture",
            "paper_reproduction_score_reviewed_snr_response",
        ]
    )


def test_acceptance_primary_score_mode_can_sort_by_reviewed_reproduction_score():
    strict_winner = _with_snr_anchor_columns(_best_candidate_row())
    strict_winner.update(
        {
            "candidate_id": "strict_winner",
            "family_id": "F_paper_reproduction_fit",
            "joint_fit_score": 0.1,
            "joint_signal_transfer_mode": "none",
            "joint_size_response_mode": "fit_required_au_power_law",
            "au_size_exponent_raw_median": 4.0,
        }
    )
    reviewed_winner = _with_snr_anchor_columns(_best_candidate_row())
    reviewed_winner.update(
        {
            "candidate_id": "reviewed_winner",
            "family_id": "F_paper_reproduction_fit",
            "joint_fit_score": 1.0,
            "joint_signal_transfer_mode": "none",
            "joint_size_response_mode": "fit_required_au_power_law",
            "au_size_exponent_raw_median": 3.05,
        }
    )

    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([strict_winner, reviewed_winner]),
        target_frame=target_audit.build_target_frame(),
        primary_score_mode="paper_reproduction_reviewed",
    )

    assert payload["best_candidate_id"] == "reviewed_winner"
    assert (
        payload["primary_score_column"]
        == "paper_reproduction_score_reviewed_snr_response"
    )


def test_reviewed_reproduction_status_does_not_override_release_boundary():
    rows = []
    for seed in (42, 43, 44):
        reproduction = _with_snr_anchor_columns(_best_candidate_row())
        reproduction.update(
            {
                "candidate_id": "reviewed_reproduction_fixture",
                "family_id": "F_paper_reproduction_fit",
                "random_seed": seed,
                "joint_fit_score": 1.0,
                "joint_signal_transfer_mode": "none",
                "joint_size_response_mode": "fit_required_au_power_law",
                "au_size_exponent_raw_median": 3.05,
                "paper_fit_status": "candidate_joint_fit_with_paper_transfer",
            }
        )
        rows.append(reproduction)
        raw_size_fail = _with_snr_anchor_columns(_best_candidate_row())
        raw_size_fail.update(
            {
                "candidate_id": "raw_size_fail_fixture",
                "family_id": "A_blank_threshold_noise",
                "random_seed": seed,
                "joint_fit_score": 0.1,
                "joint_signal_transfer_mode": "none",
                "joint_size_response_mode": "none",
                "au_size_exponent_raw_median": 3.6,
                "size_exponent_score": 1.0,
                "signal_ratio_score": 1.0,
                "paper_fit_status": "candidate_needs_signal_transfer_or_phase_fit",
            }
        )
        rows.append(raw_size_fail)

    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame(rows),
        target_frame=target_audit.build_target_frame(),
        primary_score_mode="paper_reproduction_reviewed",
    )

    reproduction = payload["paper_reproduction"]
    assert payload["best_candidate_id"] == "reviewed_reproduction_fixture"
    assert (
        reproduction["paper_reproduction_status_reviewed"]
        == "bounded_reproduction_pass_descriptive"
    )
    assert payload["candidate_release_status"] == "negative_or_diagnostic_result_only"
    assert "raw_size_response_alignment_not_met" in payload["no_go_reasons"]
    assert reproduction["paper_reproduction_accepted_raw_calibration"] is False


def test_maximal_upper_bound_adds_hypothetical_strict_ag_transfer():
    row = _with_snr_anchor_columns(_best_candidate_row())
    row.update(
        {
            "candidate_id": "maximal_upper_fixture",
            "joint_signal_transfer_mode": "none",
            "joint_size_response_mode": "fit_required_au_power_law",
            "au_size_exponent_raw_median": 3.05,
        }
    )
    for wavelength_nm in joint.JOINT_WAVELENGTHS_NM:
        row[f"ag40_to_au40_peak_ratio_{wavelength_nm}"] = 1.0
        row[
            f"ag40_to_au40_target_ratio_interferometric_column_ratio_{wavelength_nm}"
        ] = 2.0

    metrics = acceptance.add_paper_reproduction_metrics(pd.DataFrame([row]))
    metric_row = metrics.iloc[0]

    assert metric_row["paper_reproduction_candidate_class_maximal_upper"] == (
        "maximal_paper_fit"
    )
    assert metric_row["paper_reproduction_strict_upper_ag_transfer_status"] == "bounded"
    assert metric_row["paper_reproduction_strict_upper_signal_loss_after_transfer"] == 0.0
    assert metric_row["paper_reproduction_strict_upper_ag_transfer_gain_min"] == 2.0
    assert metric_row["paper_reproduction_strict_upper_ag_transfer_gain_max"] == 2.0
    assert (
        metric_row["paper_reproduction_score_maximal_upper"]
        < metric_row["paper_reproduction_score_formula_snr_response"]
    )


def test_acceptance_primary_score_mode_can_sort_by_maximal_upper_bound_score():
    strict_winner = _with_snr_anchor_columns(_best_candidate_row())
    strict_winner.update(
        {
            "candidate_id": "strict_winner",
            "family_id": "F_paper_reproduction_fit",
            "joint_fit_score": 0.1,
            "joint_signal_transfer_mode": "none",
            "joint_size_response_mode": "fit_required_au_power_law",
            "au_size_exponent_raw_median": 4.0,
        }
    )
    maximal_winner = _with_snr_anchor_columns(_best_candidate_row())
    maximal_winner.update(
        {
            "candidate_id": "maximal_winner",
            "family_id": "F_paper_reproduction_fit",
            "joint_fit_score": 1.0,
            "joint_signal_transfer_mode": "none",
            "joint_size_response_mode": "fit_required_au_power_law",
            "au_size_exponent_raw_median": 3.05,
        }
    )

    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([strict_winner, maximal_winner]),
        target_frame=target_audit.build_target_frame(),
        primary_score_mode="paper_reproduction_maximal_upper",
    )

    assert payload["best_candidate_id"] == "maximal_winner"
    assert payload["primary_score_column"] == "paper_reproduction_score_maximal_upper"
    assert (
        payload["paper_reproduction"][
            "paper_reproduction_candidate_class_maximal_upper"
        ]
        == "maximal_paper_fit"
    )
    assert (
        payload["paper_reproduction"]["paper_reproduction_accepted_raw_calibration"]
        is False
    )


def test_size_response_decomposition_reports_case_and_pair_slopes():
    row = _best_candidate_row()
    wavelength_nm, width_nm, depth_nm = joint.JOINT_CASES[0]
    for diameter_nm in joint.GOLD_DIAMETERS_NM:
        row[
            f"au{diameter_nm}_{wavelength_nm}_{width_nm}x{depth_nm}_mean_peak_height"
        ] = float(diameter_nm**3)

    cases = acceptance.size_response_case_decomposition(pd.DataFrame([row]))
    target = cases[
        cases["observable"].eq("peak_height")
        & cases["wavelength_nm"].eq(wavelength_nm)
        & cases["width_nm"].eq(width_nm)
        & cases["depth_nm"].eq(depth_nm)
    ].iloc[0]

    assert abs(target["exponent_all_sizes"] - 3.0) < 1e-12
    assert abs(target["pair_slope_20_30"] - 3.0) < 1e-12
    assert abs(target["pair_slope_30_40"] - 3.0) < 1e-12
    assert abs(target["pair_slope_40_60"] - 3.0) < 1e-12
    assert abs(target["steepest_pair_residual_vs_2p3"] - 0.7) < 1e-12

    summary = acceptance.size_response_candidate_summary(cases)
    peak_height = summary[summary["observable"].eq("peak_height")].iloc[0]
    assert abs(peak_height["median_exponent"] - 3.0) < 1e-12
    assert bool(peak_height["median_within_0p4_of_target"]) is False


def test_paper_reproduction_payload_never_marks_raw_calibration_or_writeback():
    rows = []
    for seed in (42, 43, 44):
        row = _with_snr_anchor_columns(_best_candidate_row())
        row.update(
            {
                "candidate_id": "bounded_reproduction_fixture",
                "family_id": "D2_operator_phase_bfp_raw",
                "random_seed": seed,
                "joint_fit_score": 1.0,
                "joint_signal_transfer_mode": "none",
                "joint_size_response_mode": "none",
                "au_size_exponent_raw_median": 3.05,
            }
        )
        rows.append(row)

    _, _, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame(rows),
        target_frame=target_audit.build_target_frame(),
        primary_score_mode="paper_reproduction_formula",
    )
    reproduction = payload["paper_reproduction"]

    assert reproduction["paper_reproduction_candidate_class"] == "bounded_reproduction_fit"
    assert reproduction["paper_reproduction_accepted_raw_calibration"] is False
    assert reproduction["paper_reproduction_ev_full_grid_writeback"] is False
    assert reproduction["paper_reproduction_selected_annulus_changed"] is False
    assert reproduction["paper_reproduction_global_material_defaults_changed"] is False


def test_paper_reproduction_delta_outside_hard_bound_fails_guardrail():
    row = _with_snr_anchor_columns(_best_candidate_row())
    row.update(
        {
            "joint_signal_transfer_mode": "none",
            "joint_size_response_mode": "none",
            "au_size_exponent_raw_median": 4.0,
        }
    )

    with_metrics = acceptance.add_paper_reproduction_metrics(pd.DataFrame([row]))
    metric_row = with_metrics.iloc[0]

    assert metric_row["paper_reproduction_candidate_class"] == "maximal_paper_fit"
    assert metric_row["paper_reproduction_size_delta_status"] == "hard_fail"
    assert metric_row["paper_reproduction_status"] == "fail_guardrail"
    assert metric_row["paper_reproduction_guardrail_penalty"] >= 100.0


def test_paper_reproduction_local_signal_transfer_is_maximal_only():
    row = _with_snr_anchor_columns(_best_candidate_row())
    row.update(
        {
            "joint_signal_transfer_mode": "fit_required_silver_by_wavelength",
            "joint_size_response_mode": "fit_required_au_power_law",
            "au_size_exponent_raw_median": 3.05,
            "applied_silver_transfer_gain_488": 2.0,
            "applied_silver_transfer_gain_532": 1.2,
            "applied_silver_transfer_gain_660": 2.4,
        }
    )

    with_metrics = acceptance.add_paper_reproduction_metrics(pd.DataFrame([row]))
    metric_row = with_metrics.iloc[0]

    assert metric_row["paper_reproduction_candidate_class"] == "maximal_paper_fit"
    assert not bool(metric_row["paper_reproduction_accepted_raw_calibration"])
    assert metric_row["paper_reproduction_ag_transfer_complexity_penalty"] > 0


def test_acceptance_stops_when_hard_target_is_diagnostic_only():
    targets = target_audit.build_target_frame()
    targets.loc[
        targets["target_name"] == "classification_accuracy_71p9_pm_4p0",
        "usable_for_hard_acceptance",
    ] = True

    _, guardrails, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([_best_candidate_row()]),
        target_frame=targets,
    )

    assert "hard_targets_not_diagnostic_only" in payload["no_go_reasons"]
    assert (
        guardrails.set_index("guardrail").loc[
            "hard_targets_not_diagnostic_only",
            "status",
        ]
        == "fail"
    )
    assert payload["candidate_release_status"] == "negative_or_diagnostic_result_only"


def test_acceptance_stops_on_reference_boundary_candidate():
    row = _best_candidate_row()
    row["reference_bad"] = True

    _, guardrails, _, payload = acceptance.build_acceptance_report(
        joint_summary=pd.DataFrame([row]),
        target_frame=target_audit.build_target_frame(),
    )

    assert "reference_rho_na" in payload["no_go_reasons"]
    assert guardrails.set_index("guardrail").loc["reference_rho_na", "status"] == "fail"


def test_write_outputs_records_input_manifest_hash(tmp_path):
    joint_path = tmp_path / "joint.csv"
    pd.DataFrame([_best_candidate_row()]).to_csv(joint_path, index=False)

    _, payload = acceptance.write_outputs(
        output_dir=tmp_path / "acceptance",
        joint_summary_path=joint_path,
        target_manifest_path=None,
        classification_summary_path=None,
        route_summary_path=None,
    )

    manifest = payload["input_manifest"]
    assert manifest["joint_summary"]["path"] == str(joint_path)
    assert "sha256" in manifest["joint_summary"]
    assert manifest["joint_summary_row_count"] == 1
    assert manifest["selected_annulus_bounds"] == {
        "edge_norm_min": 0.5,
        "edge_norm_max": 0.8,
    }
