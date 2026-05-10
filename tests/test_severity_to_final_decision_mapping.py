from __future__ import annotations

import csv

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_final_audit_decision_maps_consistently_to_route_role_final() -> None:
    with root_path("results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    allowed = {
        "conditional_relative_main": "relative_main_candidate",
        "weak_reference_control_only": "relative_control_candidate",
        "optional_robustness_probe_only": "optional_robustness_probe_only",
        "shortwave_probe_only": "probe_only",
        "paper_sanity_only": "paper_sanity_only",
        "surrogate_sensitive_not_promoted": "surrogate_sensitive_not_promoted",
    }
    assert rows
    for row in rows:
        assert row["route_role_final"] == allowed[row["final_audit_decision"]]


def test_optional_660_probe_never_redefines_main_660() -> None:
    with root_path("results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    optional = [row for row in rows if row["candidate_id"] == "optional_660_W900_D1400"]
    assert len(optional) == 1
    assert optional[0]["route_role_final"] == "optional_robustness_probe_only"
    assert optional[0]["main_660_redefinition_authorized"] == "False"
