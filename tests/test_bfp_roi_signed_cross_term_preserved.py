from __future__ import annotations

import csv

import pytest

from nodi_simulator.post_v2_audit import write_bfp_roi_operator_summary

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def _rows() -> list[dict[str, str]]:
    path = root_path("results/post_v2_mandatory_audit/bfp_roi_operator_summary.csv")
    if not path.exists():
        write_bfp_roi_operator_summary(root_path("."))
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_bfp_roi_cross_term_preserves_signed_proxy() -> None:
    rows = _rows()

    assert rows
    signs = {row["bfp_roi_cross_term_sign"] for row in rows}
    assert signs.issubset({"positive", "negative", "zero"})
    assert any(float(row["bfp_roi_cross_term_proxy"]) != abs(float(row["bfp_roi_cross_term_proxy"])) for row in rows)
    assert {row["bfp_roi_cross_term_claim_level"] for row in rows} == {
        "signed_relative_interference_audit_only"
    }
