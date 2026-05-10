from __future__ import annotations

import csv

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_paper_provenance_packaged_and_unavailable_ids_are_disjoint() -> None:
    with root_path("papers/provenance/paper_manifest.csv").open(encoding="utf-8", newline="") as handle:
        packaged = {row["paper_id"] for row in csv.DictReader(handle)}
    with root_path("papers/provenance/unavailable_or_not_packaged_papers.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        unavailable = {
            row["paper_id"]
            for row in csv.DictReader(handle)
            if row["paper_id"] != "none_declared"
        }

    assert packaged.isdisjoint(unavailable)


def test_historical_supersession_table_exists_and_keeps_history_advisory() -> None:
    text = root_path("HISTORICAL_REPORT_SUPERSESSION.md").read_text(encoding="utf-8")

    assert "historical_report_path" in text
    assert "superseded_by" in text
    assert "frozen_history_advisory_only" in text
    assert "REVIEW_PACKAGE_MANIFEST.json" in text
