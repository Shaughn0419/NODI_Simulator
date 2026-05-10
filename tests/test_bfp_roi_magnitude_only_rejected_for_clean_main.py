from __future__ import annotations

import csv

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_bfp_roi_summary_marks_raw_ratio_as_diagnostic_not_gate() -> None:
    with root_path("results/post_v2_mandatory_audit/bfp_roi_operator_summary.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert {row["raw_roi_vs_scalar_score_ratio_claim_level"] for row in rows} == {
        "diagnostic_only_not_gate"
    }
    assert "final_audit_decision" not in rows[0]
