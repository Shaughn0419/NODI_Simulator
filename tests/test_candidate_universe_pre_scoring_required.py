from __future__ import annotations

import json

import pytest

from nodi_simulator.post_v2_audit import write_candidate_universe_manifest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def _manifest() -> dict:
    path = root_path("results/post_v2_mandatory_audit/candidate_universe_manifest.json")
    if not path.exists():
        write_candidate_universe_manifest(root_path("."))
    return json.loads(path.read_text(encoding="utf-8"))


def test_candidate_universe_requires_prescore_before_dynamic_bfp_tsuyama_topk() -> None:
    manifest = _manifest()

    assert manifest["pre_scored_universe_required"] is True
    assert manifest["dynamic_selection_stage"] == (
        "P0b_1_unique_route_universe_before_BFP_Tsuyama_prescore"
    )
    assert manifest["bfp_roi_scoring_coverage"] == "pending_P0b_2_no_dynamic_topk_selected"
    assert manifest["tsuyama_scoring_coverage"] == "pending_P0b_3_no_dynamic_topk_selected"
    assert manifest["dynamic_topk_source_granularity"] == "unique_route_aggregates_only"
    assert manifest["raw_route_x_particle_dynamic_topk_forbidden"] is True
    assert manifest["candidate_universe_context_route_inclusion_policy"].startswith(
        "include_all_unique_v1_route_aggregates_as_context_routes_after_prescore"
    )
    assert manifest["context_route_final_decision_policy"] == (
        "conservative_surrogate_sensitive_not_promoted_unless_static_role_overrides"
    )
