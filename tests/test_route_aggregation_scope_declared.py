from __future__ import annotations

import json

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_candidate_universe_route_aggregation_policy_declares_scope_and_exclusions() -> None:
    manifest = json.loads(
        root_path("results/post_v2_mandatory_audit/candidate_universe_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    policy = manifest["route_aggregate_policy"]

    assert policy["aggregation_scope"] == "unique_route"
    assert policy["aggregation_particle_family"] == "EV_sEV"
    assert policy["aggregation_particle_filter_id"] == "ev_prior_only_excludes_gold_anchors"
    assert policy["aggregation_weighting_id"] == "unweighted_ev_prior_rows"
    assert policy["aggregation_metric_id"] == "v1_scalar_score_relative_engineering"
    assert policy["aggregation_quantile"] == "p10"
    assert policy["anchor_particles_included"] is False
    assert policy["contaminants_included_in_route_score"] is False


def test_each_route_aggregate_carries_required_scope_fields() -> None:
    manifest = json.loads(
        root_path("results/post_v2_mandatory_audit/candidate_universe_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    required = {
        "aggregation_scope",
        "aggregation_particle_family",
        "aggregation_particle_filter_id",
        "aggregation_weighting_id",
        "aggregation_metric_id",
        "aggregation_quantile",
        "anchor_particles_included",
        "contaminants_included_in_route_score",
    }

    assert manifest["route_aggregates"]
    for row in manifest["route_aggregates"]:
        assert required.issubset(row)
        assert row["anchor_particles_included"] is False
        assert row["contaminants_included_in_route_score"] is False
