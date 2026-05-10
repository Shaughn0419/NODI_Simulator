from __future__ import annotations

import csv

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_particle_panel_records_coincidence_as_relative_proxy_only() -> None:
    with root_path("results/post_v2_mandatory_audit/top_candidate_particle_panel_audit.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert {row["coincidence_claim_level"] for row in rows} == {
        "relative_blended_pulse_proxy_only"
    }
    assert {
        row["coincidence_event_overlap_proxy_definition"] for row in rows
    } == {"relative_proxy_from_event_doublet_or_overlap_risk_no_count_or_concentration_claim"}
    assert {row["coincidence_event_overlap_proxy_label"] for row in rows}.issubset(
        {"non_fragile", "fragile"}
    )
