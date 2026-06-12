from __future__ import annotations

import pytest

from nodi_simulator.review_package import claim_scan_paths, scan_claim_files

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_hard_claim_scan_scope_includes_post_v2_and_package_docs() -> None:
    paths = {path.relative_to(root_path(".")).as_posix() for path in claim_scan_paths(root_path("."))}

    assert "README.md" in paths
    assert "reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md" in paths
    assert "reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md" in paths
    assert "reports/89_EV_NODI_post_v2_unmodeled_realism_register.md" in paths
    assert "reports/90_EV_NODI_post_v2_review_ready_relative_audit_roadmap.md" in paths
    assert "reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md" in paths
    assert "reports/147_detector_forward_identity_full_chain_adversarial_audit_synthesis_20260610.md" in paths
    assert "reports/148_extreme_simulation_roadmap_post_audit_20260610.md" in paths
    assert "reports/current/47_EV_NODI全量结果分层分析报告.md" in paths
    assert "REVIEW_PACKAGE_README.md" in paths
    assert "papers/README.md" in paths
    assert "results/post_v2_physical_ceiling/README.md" in paths
    assert "results/post_v2_bounded_physical_solver_readiness/README.md" in paths


def test_hard_claim_scan_has_no_unblocked_forbidden_claims() -> None:
    assert scan_claim_files(root_path(".")) == []


def test_superseded_history_files_remain_scanned_but_not_claim_authoritative() -> None:
    paths = {path.relative_to(root_path(".")).as_posix() for path in claim_scan_paths(root_path("."))}

    assert "reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md" in paths
    assert "reports/current/README.md" in paths
    assert (
        "claim_status: superseded_do_not_quote_for_current_recommendation"
        in root_path("reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md").read_text(
            encoding="utf-8"
        )[:512]
    )
