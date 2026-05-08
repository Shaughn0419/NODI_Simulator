from __future__ import annotations

import pandas as pd

from tools import tsuyama_phase2_parameter_inverse as inverse


def test_family_plan_keeps_transfer_size_in_final_family():
    plan = inverse.build_family_plan(max_candidates_per_family=2)

    assert set(plan["family_id"]) == {
        "A_blank_threshold_noise",
        "B_logger_lockin_pulse_width",
        "C_transport_event_shape_fluxmix",
        "D_reference_collection_rho_bfp",
        "D2_operator_phase_bfp_raw",
        "E_local_transfer_size_response",
        "F_paper_reproduction_fit",
    }
    early = plan[~plan["family_id"].isin(["E_local_transfer_size_response", "F_paper_reproduction_fit"])]
    assert set(early["variant_signal_transfer_mode"]) == {"none"}
    final = plan[plan["family_id"] == "E_local_transfer_size_response"]
    assert "fit_required_silver_by_wavelength" in set(final["variant_signal_transfer_mode"])
    reproduction = plan[plan["family_id"] == "F_paper_reproduction_fit"]
    assert set(reproduction["variant_signal_transfer_mode"]) == {"none"}
    assert set(reproduction["variant_size_response_mode"]) == {
        "fit_required_au_power_law"
    }
    d2 = inverse.build_family_plan(
        family_ids=["D2_operator_phase_bfp_raw"],
    )
    assert "tau_2ms_paper_aligned_phase_filter" in set(d2["base_candidate_id"])
    assert "tau_2ms_bfp_lobe_045" in set(d2["base_candidate_id"])


def test_family_plan_can_select_subset_and_limit_candidates():
    plan = inverse.build_family_plan(
        family_ids=["A_blank_threshold_noise"],
        max_candidates_per_family=3,
    )

    assert set(plan["family_id"]) == {"A_blank_threshold_noise"}
    assert len(plan) == 3


def test_family_plan_can_filter_candidate_ids_for_d2p1_smoke():
    plan = inverse.build_family_plan(
        family_ids=["D2_operator_phase_bfp_raw"],
        candidate_ids=[
            "tau_2ms_control",
            "tau_2ms_global_refphi_plus_0p2",
            "tau_2ms_global_refphi_plus",
            "tau_2ms_global_refphi_plus_0p6",
            "tau_2ms_collection_narrow",
            "tau_2ms_global_refphi_plus_collection_narrow",
        ],
    )

    assert set(plan["base_candidate_id"]) == {
        "tau_2ms_control",
        "tau_2ms_global_refphi_plus_0p2",
        "tau_2ms_global_refphi_plus",
        "tau_2ms_global_refphi_plus_0p6",
        "tau_2ms_collection_narrow",
        "tau_2ms_global_refphi_plus_collection_narrow",
    }
    assert len(plan) == 12
    assert set(plan["variant_signal_transfer_mode"]) == {"none"}


def test_family_plan_exposes_size_only_reproduction_fit_family():
    plan = inverse.build_family_plan(
        family_ids=["F_paper_reproduction_fit"],
        candidate_ids=[
            "tau_2ms_global_refphi_plus",
            "tau_2ms_global_refphi_plus_collection_narrow",
        ],
    )

    assert set(plan["candidate_id"]) == {
        "tau_2ms_global_refphi_plus__paper_5sigma_size_response_fit",
        "tau_2ms_global_refphi_plus_collection_narrow__paper_5sigma_size_response_fit",
    }
    assert set(plan["variant_signal_transfer_mode"]) == {"none"}
    assert set(plan["variant_size_response_mode"]) == {"fit_required_au_power_law"}


def test_best_candidate_summary_requires_seed_stability_and_guardrails():
    summary = pd.DataFrame(
        [
            {
                "family_id": "A_blank_threshold_noise",
                "candidate_id": "candidate_a",
                "random_seed": 42,
                "joint_fit_score": 1.0,
                "joint_fit_score_formula": 0.9,
                "joint_fit_score_recomputed_mie": 0.8,
                "selected_rate_score": 0.1,
                "signal_ratio_score": 0.2,
                "signal_ratio_score_sqrt_scattering_column_ratio": 0.05,
                "raw_signal_ratio_score_sqrt_scattering_column_ratio": 0.05,
                "signal_ratio_score_recomputed_mie_sqrt_csca_ratio": 0.06,
                "raw_signal_ratio_score_recomputed_mie_sqrt_csca_ratio": 0.06,
                "size_exponent_score": 0.3,
                "snr_ratio_score": 0.4,
                "hard_guardrail_penalty": 0.0,
                "reference_bad": False,
                "rho_bad": False,
                "na_cutoff_active": False,
                "paper_fit_status": "candidate_joint_fit_plausible",
            },
            {
                "family_id": "A_blank_threshold_noise",
                "candidate_id": "candidate_a",
                "random_seed": 43,
                "joint_fit_score": 1.2,
                "joint_fit_score_formula": 1.0,
                "joint_fit_score_recomputed_mie": 0.9,
                "selected_rate_score": 0.1,
                "signal_ratio_score": 0.2,
                "signal_ratio_score_sqrt_scattering_column_ratio": 0.07,
                "raw_signal_ratio_score_sqrt_scattering_column_ratio": 0.07,
                "signal_ratio_score_recomputed_mie_sqrt_csca_ratio": 0.08,
                "raw_signal_ratio_score_recomputed_mie_sqrt_csca_ratio": 0.08,
                "size_exponent_score": 0.3,
                "snr_ratio_score": 0.4,
                "hard_guardrail_penalty": 0.0,
                "reference_bad": False,
                "rho_bad": False,
                "na_cutoff_active": False,
                "paper_fit_status": "candidate_joint_fit_plausible",
            },
        ]
    )

    best = inverse.summarize_best_candidates(summary, expected_seed_count=2)

    assert best.iloc[0]["joint_fit_score_median"] == 1.1
    assert best.iloc[0]["joint_fit_score_formula_median"] == 0.95
    assert best.iloc[0]["signal_ratio_score_formula_median"] == 0.060000000000000005
    assert best.iloc[0]["family_stability_status"] == "stable_family_candidate"


def test_operator_variant_diagnostic_flags_inert_d2_candidate():
    summary = pd.DataFrame(
        [
            {
                "family_id": "D2_operator_phase_bfp_raw",
                "candidate_id": candidate_id,
                "random_seed": seed,
                "joint_fit_score": 1.0,
                "joint_fit_score_formula": 0.9,
                "joint_fit_score_recomputed_mie": 0.8,
                "selected_rate_score": 0.1,
                "signal_ratio_score": 0.2,
                "signal_ratio_score_sqrt_scattering_column_ratio": 0.05,
                "raw_signal_ratio_score_sqrt_scattering_column_ratio": 0.05,
                "signal_ratio_score_recomputed_mie_sqrt_csca_ratio": 0.06,
                "raw_signal_ratio_score_recomputed_mie_sqrt_csca_ratio": 0.06,
                "size_exponent_score": 0.3,
                "snr_ratio_score": 0.4,
                "hard_guardrail_penalty": 0.0,
                "reference_bad": False,
                "rho_bad": False,
                "na_cutoff_active": False,
                "paper_fit_status": "candidate_joint_fit_plausible",
            }
            for candidate_id in (
                "tau_2ms_control",
                "tau_2ms_paper_aligned_phase_filter",
            )
            for seed in (42, 43)
        ]
    )

    best = inverse.summarize_best_candidates(summary, expected_seed_count=2)
    status = best.set_index("candidate_id").loc[
        "tau_2ms_paper_aligned_phase_filter",
        "operator_variant_diagnostic_status",
    ]

    assert status == "operator_variant_numerically_inert_vs_control"


def test_guardrail_failures_catches_boundary_rows():
    summary = pd.DataFrame(
        [
            {
                "family_id": "D_reference_collection_rho_bfp",
                "candidate_id": "bad",
                "random_seed": 42,
                "joint_fit_score": 1.0,
                "hard_guardrail_penalty": 5.0,
                "transfer_gain_guardrail_penalty": 0.0,
                "size_response_guardrail_penalty": 0.0,
                "reference_bad": True,
                "rho_bad": False,
                "na_cutoff_active": False,
                "paper_fit_status": "candidate_fit_guardrail_violation",
            }
        ]
    )

    failures = inverse.guardrail_failures(summary)

    assert len(failures) == 1
    assert failures.iloc[0]["candidate_id"] == "bad"
