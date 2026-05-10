from __future__ import annotations

import csv

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_contaminant_pass_fraction_is_consumed_by_risk_policy() -> None:
    with root_path("results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert {row["contaminant_utilized_in_risk_policy"] for row in rows} == {"True"}
    assert {row["contaminant_risk_label"] for row in rows}.issubset({"low", "medium", "high"})


def test_ev_sample_profile_ids_resolve_to_config() -> None:
    with root_path("results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert {row["ev_sample_profile_id"] for row in rows} == {"unknown"}
    assert {row["ev_sample_profile_resolved"] for row in rows} == {"True"}
    assert {row["ev_sample_profile_min_risk_label"] for row in rows} == {"medium"}
