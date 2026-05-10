from __future__ import annotations

import pytest

from ._review_package_test_helpers import load_json


pytestmark = pytest.mark.review_package_required


def test_p0a_audit_manifest_documents_v1_source_mapping() -> None:
    manifest = load_json("results/post_v2_mandatory_audit/top_candidate_mandatory_audit_manifest.json")
    mapping = manifest["v1_source_field_mapping"]

    assert manifest["audit_manifest_schema"] == "ev_nodi_post_v2_mandatory_audit_manifest_v1"
    assert all(row["audit_field"].startswith("v1_") for row in mapping)
    assert all(row.get("source_column") or row.get("derivation_rule") for row in mapping)
    assert "bfp_to_angle_jacobian_applied" in manifest["unprefixed_forbidden_audit_columns"]
    assert manifest["v1_bfp_to_angle_jacobian_applied_expected"] is False
    assert manifest["audit_bfp_jacobian_applied_layer"] == "post_v2_audit_sidecar_not_v1_fact"


def test_p0a_audit_manifest_pins_rank_and_aggregation_schema() -> None:
    manifest = load_json("results/post_v2_mandatory_audit/top_candidate_mandatory_audit_manifest.json")
    rank_policy = manifest["rank_policy"]

    assert rank_policy["primary_inversion_stratum"] == "all_ranked_routes"
    assert rank_policy["raw_magnitude_final_gate_allowed"] is False
    assert {
        "aggregation_particle_filter_id",
        "aggregation_weighting_id",
        "aggregation_metric_id",
        "aggregation_quantile",
    }.issubset(set(manifest["required_aggregation_fields"]))


def test_p0b_candidate_universe_is_deferred_not_backfilled_from_raw_rows() -> None:
    manifest = load_json("results/post_v2_mandatory_audit/top_candidate_mandatory_audit_manifest.json")
    deferred = {artifact["role"]: artifact for artifact in manifest["p0b_artifacts_deferred_until_evidence_chain"]}

    assert deferred["candidate_universe_manifest"]["generation_task_id"] == "P0b.candidate_universe"
    assert "top_candidate_mandatory_audit" in deferred
