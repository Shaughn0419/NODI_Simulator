from __future__ import annotations

import csv

import pytest

from nodi_simulator.post_v2_audit import (
    write_ev_prior_contaminant_summary,
    write_particle_panel_audit,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def _particle_rows() -> list[dict[str, str]]:
    path = root_path("results/post_v2_mandatory_audit/top_candidate_particle_panel_audit.csv")
    if not path.exists():
        write_particle_panel_audit(root_path("."))
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _summary_rows() -> list[dict[str, str]]:
    path = root_path("results/post_v2_mandatory_audit/ev_prior_contaminant_summary.csv")
    if not path.exists():
        write_ev_prior_contaminant_summary(root_path("."))
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_particle_panel_audit_keeps_anchor_contaminants_out_of_route_score() -> None:
    rows = _particle_rows()

    assert rows
    assert {"EV_sEV", "gold"}.issubset({row["particle_panel_id"] for row in rows})
    assert {row["contaminants_included_in_route_score"] for row in rows} == {"False"}
    assert {row["panel_score_claim_level"] for row in rows} == {
        "relative_engineering_proxy_only"
    }


def test_ev_contaminant_summary_blocks_concentration_and_biological_specificity_claims() -> None:
    rows = _summary_rows()

    assert rows
    assert {row["ev_pass_criterion_claim_level"] for row in rows} == {
        "relative_score_rank_only"
    }
    assert {row["biological_specificity_claim_allowed"] for row in rows} == {"False"}
    assert {row["true_ev_concentration_claim_allowed"] for row in rows} == {"False"}
    assert {row["count_or_concentration_interpretation_allowed"] for row in rows} == {"False"}
