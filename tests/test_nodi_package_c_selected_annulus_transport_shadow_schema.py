from __future__ import annotations

import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = (
    PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_selected_annulus_transport_shadow_schema.py"
)


def load_builder():
    spec = importlib.util.spec_from_file_location("selected_annulus_shadow_builder", BUILDER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_legacy_selection_function_is_context_only_not_decision_use():
    builder = load_builder()
    legacy = builder.legacy_freeze_rows()[0]
    assert legacy["legacy_lane_name"] == "legacy_selected_annulus_paper_audit"
    assert legacy["annulus_edge_norm_min"] == "0.5"
    assert legacy["annulus_edge_norm_max"] == "0.8"
    assert legacy["decision_use_allowed_for_comsol_transport_shadow"] == "false"
    assert legacy["canonical_change_allowed"] == "false_without_future_signed_sensitivity_plan"


def test_edge4_bins_cannot_silently_construct_exact_selected_annulus():
    builder = load_builder()
    dispositions = {row["bin_or_window"]: row for row in builder.edge_disposition_rows()}
    assert (
        dispositions["0.75-1.0"]["disposition"]
        == "BLOCKED_MIXED_ANNULUS_NEAR_WALL_REQUIRES_0P8_SPLIT"
    )
    assert dispositions["0.75-1.0"]["exact_selected_annulus_allowed"] == "false"
    assert (
        dispositions["0.5-0.8"]["disposition"]
        == "BLOCKED_UNLESS_EDGE20_10_TO_15_OR_EXPLICIT_0P8_SPLIT"
    )
    assert builder.exact_annulus_disposition("edge_norm_4", "edge_10;edge_11", False).startswith(
        "BLOCKED"
    )


def test_exact_annulus_requires_edge20_10_to_15_or_explicit_split():
    builder = load_builder()
    exact_bins = "edge_10;edge_11;edge_12;edge_13;edge_14;edge_15"
    assert (
        builder.exact_annulus_disposition("edge_norm_20", exact_bins, False)
        == "FUTURE_CONTEXT_ONLY_EXACT_ANNULUS_CANDIDATE_IF_SOURCE_VALIDATED"
    )
    assert (
        builder.exact_annulus_disposition("edge_norm_4", "edge_norm_0p50_1p00", True)
        == "FUTURE_CONTEXT_ONLY_EXACT_ANNULUS_CANDIDATE_IF_SOURCE_VALIDATED"
    )


def test_sidewall_angle_convention_mismatch_hard_fails():
    builder = load_builder()
    assert builder.validate_sidewall_convention(
        85, 5, "sidewall_deg_comsol_from_horizontal_90deg_vertical"
    ) == []
    assert "sidewall_conversion_not_90_minus_theta" in builder.validate_sidewall_convention(
        85, 85, "sidewall_deg_comsol_from_horizontal_90deg_vertical"
    )
    assert "missing_or_wrong_sidewall_angle_convention" in builder.validate_sidewall_convention(
        85, 5, "bare_angle"
    )
    assert "sidewall_deg_comsol_out_of_expected_review_range" in builder.validate_sidewall_convention(
        5, 85, "sidewall_deg_comsol_from_horizontal_90deg_vertical"
    )


def test_selected_annulus_does_not_accept_bfp_or_roi_annulus():
    builder = load_builder()
    assert (
        builder.classify_annulus_source("BFP_ROI_annulus")
        == "BLOCKED_BFP_ROI_ANNULUS_NOT_EVENT_POSITION_ANNULUS"
    )
    assert builder.classify_annulus_source("initial_position_edge_norm_annulus").startswith(
        "LEGACY"
    )
    assert builder.classify_annulus_source("transported_position_edge_norm").startswith("COMSOL")


def test_context_cannot_promote_forbidden_claims_or_weighting_to_winner():
    builder = load_builder()
    for row in builder.forbidden_claim_audit_rows():
        assert row["positive_output_allowed"] == "false"
        assert row["observed_positive_count"] == "0"
    lanes = {row["lane"]: row for row in builder.shadow_lane_plan_rows()}
    assert lanes["comsol_weighted_selected_annulus_shadow"]["decision_use_allowed"] == "false"
    for row in builder.mutation_rows():
        assert int(row["observed_unexpected_pass"]) == 0
        assert int(row["formal_qch_promotion"]) == 0
        assert int(row["route_score_promotion"]) == 0
        assert int(row["yield_detection_promotion"]) == 0
        assert int(row["chi_selected_promotion"]) == 0


def test_source_mismatch_with_same_paper_claim_fails():
    builder = load_builder()
    assert builder.validate_transport_source_binding("same_paper_claim", "abc", "def") == [
        "source_mismatch_with_same_paper_claim"
    ]
    assert builder.validate_transport_source_binding("same_paper_claim", "abc", "abc") == []


def test_build_outputs_passes_with_external_dirty_excluded():
    builder = load_builder()
    payload = builder.build_outputs()
    summary = payload["summary"]
    assert summary["disposition"] == builder.PASS_DISPOSITION
    assert summary["release_scoped_dirty_blocker_rows"] == 0
    assert summary["source_lock_failures"] == 0
    assert summary["external_dirty_excluded"] is True
    assert summary["selection_function_schema_rows"] >= 15
    assert summary["annulus_transport_context_schema_rows"] >= 40
    assert summary["mutation_row_equivalent_total"] >= 1_000_000
    assert summary["unexpected_pass"] == 0
    assert summary["authorization_promotion"] == 0
    assert summary["formal_qch_promotion"] == 0
    assert summary["chi_selected_promotion"] == 0
    assert summary["Gate2D_rows"] == 4
    assert summary["EDGE_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert summary["BINDING_state"] == "FAIL_CLOSED"
