from __future__ import annotations

import csv

import pytest

from nodi_simulator.post_v2_audit import write_extended_pairwise_stability

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_extended_pairwise_stability_views_are_diagnostic_only() -> None:
    path = root_path("results/post_v2_mandatory_audit/top_candidate_extended_pairwise_stability.csv")
    write_extended_pairwise_stability(root_path("."))
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert {
        "cross_wavelength_pairwise_stability",
        "historical_report_pairwise_drift",
    }.issubset({row["extended_pairwise_view"] for row in rows})
    assert {row["claim_level"] for row in rows} == {
        "relative_extended_pairwise_diagnostic_only"
    }
