from __future__ import annotations

import csv

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_bfp_roi_summary_has_signed_self_cross_and_jacobian_schema() -> None:
    with root_path("results/post_v2_mandatory_audit/bfp_roi_operator_summary.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    required = {
        "bfp_roi_score",
        "bfp_roi_total_deltaI_proxy",
        "bfp_roi_cross_term_proxy",
        "bfp_roi_self_term_proxy",
        "bfp_roi_cross_term_fraction",
        "bfp_roi_self_term_fraction",
        "bfp_roi_interference_dominant_flag",
        "bfp_roi_cross_term_sign",
        "bfp_roi_scalar_sign",
        "bfp_roi_sign_agreement_with_scalar",
        "bfp_roi_negative_cross_term_flag",
        "bfp_roi_cross_term_claim_level",
        "bfp_roi_rank_in_stratum",
        "bfp_roi_rank_percentile_in_stratum",
        "bfp_roi_operator_id",
        "bfp_roi_mask_id",
        "audit_bfp_jacobian_applied",
        "audit_bfp_coordinate_frame",
        "audit_bfp_jacobian_source_id",
        "audit_bfp_jacobian_formula_id",
        "audit_bfp_jacobian_unit_test_status",
        "roi_vs_scalar_percentile_delta",
        "rank_delta_bfp_minus_scalar",
        "percentile_delta_bfp_minus_scalar",
        "rank_inversion_flag",
        "rank_inversion_severity",
        "rank_inversion_reason_codes",
    }

    assert rows
    assert required.issubset(rows[0])
    assert {row["audit_bfp_jacobian_applied"] for row in rows} == {"True"}
    assert {row["audit_bfp_jacobian_unit_test_status"] for row in rows} == {"pass"}
    assert {row["audit_bfp_coordinate_frame"] for row in rows} == {"uv_direction_cosine"}
