from __future__ import annotations

from tools import tsuyama_paper_target_audit as audit


def test_target_audit_separates_hard_and_diagnostic_targets():
    frame = audit.build_target_frame()

    hard = frame[frame["usable_for_hard_acceptance"]]
    diagnostic = frame[~frame["usable_for_hard_acceptance"]]

    assert not hard.empty
    assert "diagnostic_only" not in set(hard["confidence"])
    assert {"direct", "inferred", "operational"}.issubset(set(frame["confidence"]))
    assert "diagnostic_only" in set(diagnostic["confidence"])


def test_target_audit_keeps_phase2_boundaries_explicit():
    frame = audit.build_target_frame().set_index("target_name")

    assert frame.loc["selected_annulus_geometry_guardrail", "value"] == "0.5-0.8"
    assert frame.loc["selected_annulus_geometry_guardrail", "usable_for_hard_acceptance"]
    assert not frame.loc[
        "classification_accuracy_71p9_pm_4p0",
        "usable_for_hard_acceptance",
    ]
    assert not frame.loc[
        "pod_2020_au20_near_100pct_counting",
        "usable_for_hard_acceptance",
    ]
    assert not frame.loc[
        "paired_pod_nodi_2024_classification",
        "usable_for_hard_acceptance",
    ]


def test_target_audit_outputs_expected_table_s1_ratio_records():
    frame = audit.build_target_frame().set_index("target_name")

    strict_name = "ag40_to_au40_interferometric_column_ratio_660"
    formula_name = "ag40_to_au40_sqrt_scattering_column_ratio_660"
    recomputed_name = "ag40_to_au40_recomputed_mie_sqrt_csca_ratio_660"

    assert frame.loc[
        strict_name,
        "confidence",
    ] == "direct"
    assert bool(frame.loc[
        strict_name,
        "usable_for_hard_acceptance",
    ]) is False
    assert bool(frame.loc[formula_name, "usable_for_hard_acceptance"]) is True
    assert frame.loc[recomputed_name, "confidence"] == "inferred"
    assert frame.loc[
        strict_name,
        "target_integrity_status",
    ] == "unresolved_table_s1_interferometric_column_inconsistency"
    assert (
        frame.loc[strict_name, "recommended_signal_ratio_target_mode"]
        == "sqrt_scattering_column_ratio"
    )
    assert float(frame.loc[strict_name, "value"]) > 2.0
    assert 0.7 < float(frame.loc[formula_name, "value"]) < 1.0


def test_target_audit_demotes_au20_lower_bound_to_warning_only():
    frame = audit.build_target_frame().set_index("target_name")

    assert not bool(frame.loc[
        "au20_selected_annulus_low_sensitivity_warning",
        "usable_for_hard_acceptance",
    ])
    assert bool(frame.loc[
        "au20_selected_annulus_upper_detection_guard",
        "usable_for_hard_acceptance",
    ])
