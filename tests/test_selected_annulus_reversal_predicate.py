from __future__ import annotations

import csv

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_selected_annulus_is_diagnostic_and_never_primary_gate_switch() -> None:
    with root_path("results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert {row["selected_annulus_replaces_all_crossing_ranking"] for row in rows} == {"False"}
    assert {row["selected_annulus_primary_gate_switch_blocked"] for row in rows} == {"True"}
    assert {row["selected_annulus_lane_status"] for row in rows}.issubset(
        {"available", "lane_unavailable_v1"}
    )
