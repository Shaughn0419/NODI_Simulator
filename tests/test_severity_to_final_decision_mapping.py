from __future__ import annotations

import pytest

from nodi_simulator.post_v2_audit import severity_to_final_decision


pytestmark = pytest.mark.review_package_required


def test_rank_inversion_severity_truth_table_for_blocking_cases() -> None:
    assert severity_to_final_decision(
        "audit_incomplete",
        role_initial="main_locked",
    )[0] == "audit_incomplete_blocked"
    assert severity_to_final_decision(
        "critical",
        role_initial="main_locked",
        missing_bfp_score=True,
    )[0] == "audit_incomplete_blocked"
    assert severity_to_final_decision(
        "critical",
        role_initial="main_locked",
        optional_probe_redefinition_attempted=True,
    )[0] == "audit_incomplete_blocked"
    assert severity_to_final_decision(
        "critical",
        role_initial="main_locked",
        main_control_reversal=True,
    )[0] == "surrogate_sensitive_not_promoted"


def test_rank_inversion_severity_truth_table_for_candidate_outcomes() -> None:
    assert severity_to_final_decision(
        "major",
        role_initial="main_locked",
    )[0] in {"conditional_relative_main", "surrogate_sensitive_not_promoted"}
    assert severity_to_final_decision(
        "minor",
        role_initial="main_locked",
        all_clean_gates_pass=True,
    )[0] == "clean_relative_main"
    assert severity_to_final_decision(
        "none",
        role_initial="main_locked",
        all_clean_gates_pass=True,
    )[0] == "clean_relative_main"
    assert severity_to_final_decision(
        "none",
        role_initial="main_locked",
        all_clean_gates_pass=False,
    )[0] == "conditional_relative_main"


def test_audit_only_not_ranked_paper_sanity_rows_do_not_get_promotion_labels() -> None:
    assert severity_to_final_decision(
        "critical",
        role_initial="paper_sanity_audit_only",
        main_control_reversal=True,
    ) == ("paper_sanity_only", "paper_sanity_only")
