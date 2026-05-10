from __future__ import annotations

import csv
import json

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_route_role_vocabulary_is_closed_for_audit_outputs() -> None:
    vocabulary = json.loads(
        root_path("configs/realism_v2/route_role_vocabulary.yaml").read_text(encoding="utf-8")
    )
    initial = set(vocabulary["route_role_initial"])
    final = set(vocabulary["route_role_final"])

    with root_path("results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    assert rows
    assert {row["route_role_initial"] for row in rows}.issubset(initial)
    assert {row["route_role_final"] for row in rows}.issubset(final)
