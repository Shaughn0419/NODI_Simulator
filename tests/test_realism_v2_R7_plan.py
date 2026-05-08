from __future__ import annotations

import copy
import csv
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


R6_DIR = rv2.DEFAULT_R6_ROUTE_PRIOR_SENSITIVITY_AUDIT_DIR


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_R7_plan_is_plan_only_after_R6_gate():
    plan = rv2.validate_R7_route_prior_mechanistic_decomposition_plan()
    boundary = plan["authorization_boundary"]

    assert plan["schema_version"] == rv2.R7_PLAN_SCHEMA_VERSION
    assert plan["stage"] == "R7_route_prior_mechanistic_decomposition_plan_only"
    assert plan["prior_gate"] == "PASS_R6_RESULTS_PREPARE_NEXT_STAGE_PLAN_ONLY"
    assert (
        plan["selected_next_stage_lane"]
        == "R7_route_prior_mechanistic_decomposition_plan_only"
    )
    assert boundary["R7_plan_preparation_authorized_by_prior_gate"] is True
    assert boundary["R7_plan_artifact_created"] is True
    assert boundary["R7_execution_authorized"] is False
    assert boundary["R5_followup_expansion_authorized"] is False
    assert boundary["R6_followup_expansion_authorized"] is False
    assert boundary["context_route_promotion_authorized"] is False
    assert boundary["main_660_redefinition_authorized"] is False
    assert boundary["score_derived_physical_prior_authorized"] is False
    assert boundary["external_review_required_before_R7_execution"] is True


def test_R7_carries_R6_result_as_width_hypothesis_not_law():
    plan = rv2.validate_R7_route_prior_mechanistic_decomposition_plan()
    carry = plan["R6_evidence_carryforward"]
    r6_manifest = _csv_rows(R6_DIR / "R6_route_prior_sensitivity_manifest.csv")[0]

    assert carry["R6_route_prior_sensitivity_audit_run"] is True
    assert carry["accepted_gate"] == "PASS_R6_RESULTS_PREPARE_NEXT_STAGE_PLAN_ONLY"
    assert carry["existing_R5_rows_audited"] == rv2.R7_ROUTE_PRIOR_SOURCE_ROW_CAP
    assert carry["candidate_prior_count"] == 12
    assert carry["derived_candidate_rows_evaluated"] == rv2.R6_DERIVED_CANDIDATE_ROW_CAP
    assert carry["audit_route_id_count"] == rv2.R5_2_AUDIT_ROUTE_COUNT
    assert carry["scenario_bundle_count"] == rv2.R5_NAMED_SCENARIO_BUNDLE_COUNT
    assert carry["stochastic_seed_count"] == 0
    assert carry["main660_comparator_policy"] == "candidate_adjusted_locked_main_660"
    assert carry["nearby_warning_resolved_candidate_count"] == 3
    assert (
        carry["at_least_two_nearby_low_dimensional_candidates_explain_warning"]
        is True
    )
    assert carry["selected_future_recommendation_class"] == (
        "prepare_next_stage_plan_for_external_review_only"
    )
    assert carry["R7_plan_preparation_authorized_in_R6_manifest"] is False
    assert r6_manifest["selected_future_recommendation_class"] == (
        carry["selected_future_recommendation_class"]
    )
    assert r6_manifest["R7_plan_preparation_authorized"] == "False"


def test_R7_scope_is_existing_artifact_only_and_keeps_R6_caps():
    plan = rv2.validate_R7_route_prior_mechanistic_decomposition_plan()
    design = plan["R7_plan_design"]

    assert design["plan_execution_type"] == "plan_only_no_R7_execution"
    assert design["future_R7_execution_type_if_reviewed"] == (
        "bounded_existing_R5_artifact_route_prior_mechanistic_decomposition_audit_only"
    )
    assert design["uses_existing_R5_R6_artifacts_only"] is True
    assert design["R6_width_family_prior_is_hypothesis_not_physical_law"] is True
    assert design["max_existing_R5_source_rows_if_future_reviewed"] == 14784
    assert design["max_mechanistic_candidate_count"] == 12
    assert design["max_R7_derived_candidate_rows"] == 177408
    assert design["route_id_count"] == 33
    assert set(design["route_ids"]) == rv2.R5_2_AUDIT_ROUTE_IDS
    assert set(design["scenario_bundle_ids"]) == rv2.R5_REQUIRED_SCENARIO_BUNDLE_IDS
    assert design["new_case_rows_authorized"] == 0
    assert design["new_scenario_bundle_authorized"] is False
    assert design["new_stochastic_seed_authorized"] is False
    assert design["new_solver_case_authorized"] is False
    assert design["new_experiment_authorized"] is False
    assert design["future_output_directory"] == (
        "results/ev_nodi_realism_v2_R7_route_prior_mechanistic_decomposition_audit"
    )


def test_R7_accepted_band_absorbs_R6_cautions():
    plan = rv2.validate_R7_route_prior_mechanistic_decomposition_plan()
    carry = plan["R6_evidence_carryforward"]
    band = plan["accepted_width_prior_band"]

    assert band["width_pivot_nm_min"] == 800
    assert band["width_pivot_nm_max"] == 850
    assert band["width_exponent_min"] == 1.5
    assert band["width_exponent_max"] == 2.0
    assert band["main660_retention_fraction_min"] == 0.85
    assert set(band["accepted_explanatory_candidate_ids"]) == {
        "width_exp1p5_800",
        "global_width_quadratic_regularization",
        "width_quad_850",
    }
    assert set(band["too_weak_candidate_ids"]) == {
        "width_linear_800",
        "width_quad_750",
    }
    assert band["over_severe_caution_candidate_ids"] == ["width_quad_900"]
    assert carry["width_quad_900_interpretation_class"] == "over_severe_prior_caution"
    assert carry["width_quad_900_main660_score_retention_fraction"] < 0.85
    assert carry["width_quad_900_is_accepted_explanatory_band_member"] is False
    assert band["optional_900_cannot_redefine_main"] is True
    assert band["width_quad_floor035_nearby_example_is_invalidated"] is True
    assert [
        "global_width_quadratic_regularization",
        "width_quad_floor035",
    ] not in band["corrected_nearby_example_pairs"]


def test_R7_mechanistic_registry_is_low_dimensional_and_non_promoting():
    plan = rv2.validate_R7_route_prior_mechanistic_decomposition_plan()
    mech = plan["mechanistic_decomposition_design"]
    registry = mech["candidate_mechanistic_prior_registry"]

    assert set(mech["allowed_mechanistic_prior_families"]) == (
        rv2.R7_ALLOWED_MECHANISTIC_PRIOR_FAMILIES
    )
    assert set(mech["forbidden_mechanistic_prior_families"]) == (
        rv2.R7_FORBIDDEN_MECHANISTIC_PRIOR_FAMILIES
    )
    assert set(mech["required_mechanistic_registry_fields"]) == (
        rv2.R7_REQUIRED_MECHANISTIC_REGISTRY_FIELDS
    )
    assert mech["score_derived_physical_prior_authorized"] is False
    assert mech["source_v1_relative_score_physical_prior_authorized"] is False
    assert mech["outcome_proximal_diagnostics_must_be_labeled"] is True
    assert {row["candidate_prior_family"] for row in registry} == (
        rv2.R7_ALLOWED_MECHANISTIC_PRIOR_FAMILIES
    )
    assert all(row["dof_count_max"] <= 2 for row in registry)
    assert all(row["uses_route_specific_multiplier"] is False for row in registry)
    assert all(row["uses_scenario_specific_per_route_fit"] is False for row in registry)
    assert all(row["uses_particle_specific_empirical_fit"] is False for row in registry)
    assert all(
        row["uses_source_v1_relative_score_as_physical_input"] is False
        for row in registry
    )
    assert all(row["changes_main_660_definition"] is False for row in registry)
    assert all(row["authorizes_route_promotion"] is False for row in registry)
    reference = [
        row
        for row in registry
        if row["candidate_prior_family"] == "reference_operating_band_family"
    ][0]
    assert reference["requires_new_operator_artifact"] is True
    assert "source_v1_relative_score" not in reference["allowed_input_fields"]


def test_R7_particle_optional_900_and_non_width_policies_are_guarded():
    plan = rv2.validate_R7_route_prior_mechanistic_decomposition_plan()
    particle = plan["particle_stratum_residual_policy"]
    optional = plan["optional_900_governance_diagnostic"]
    non_width = plan["non_width_prior_input_policy"]

    assert particle["particle_stratum_residual_is_warning_not_fit_target"] is True
    assert particle["particle_specific_empirical_fit_authorized"] is False
    assert set(particle["required_particle_residual_outputs"]) == {
        "R7_particle_stratum_residual_top_routes.csv",
        "R7_particle_stratum_residual_by_family.csv",
        "R7_gold_anchor_vs_EV_residual_comparison.csv",
    }
    assert optional["route_id"] == "660_900x1400"
    assert optional["optional_900_role"] == "optional_robustness_probe"
    assert optional["main_660_redefinition_authorized"] is False
    assert optional["route_promotion_authorized"] is False
    assert non_width["source_v1_relative_score_as_physical_prior_authorized"] is False
    assert non_width["outcome_proximal_candidate_ids"] == ["reference_band_penalty"]
    assert non_width["reference_band_next_version_requires_physical_columns"] is True
    assert non_width["BFP_alignment_next_version_requires_operator_columns"] is True


def test_R7_outputs_stop_gates_claims_and_future_review_decisions_are_complete():
    plan = rv2.validate_R7_route_prior_mechanistic_decomposition_plan()
    claims = plan["claim_boundaries"]
    criteria = plan["future_pass_fail_criteria_if_execution_is_reviewed"]

    assert set(plan["required_outputs_if_authorized_after_future_review"]) == (
        rv2.R7_REQUIRED_OUTPUTS_IF_AUTHORIZED
    )
    assert "R7_particle_stratum_residual_top_routes.csv" in (
        plan["required_outputs_if_authorized_after_future_review"]
    )
    assert "R7_optional_900_governance_diagnostic.csv" in (
        plan["required_outputs_if_authorized_after_future_review"]
    )
    assert rv2.R7_REQUIRED_STOP_GATES.issubset(set(plan["stop_gates"]))
    assert "score_derived_physical_prior_attempted" in plan["stop_gates"]
    assert set(plan["allowed_future_external_review_decisions"]) == (
        rv2.R7_ALLOWED_FUTURE_REVIEW_DECISIONS
    )
    assert criteria["at_least_two_low_dimensional_mechanistic_priors_explain_warning"]
    assert criteria["main660_retention_fraction_at_least_0p85"]
    assert criteria["particle_residuals_reported_but_not_fit_away"]
    assert criteria["stop_if_only_forbidden_fits_resolve_warning"]
    assert claims["SNR_claim_level"] == "absolute_blocked"
    assert claims["event_probability_claim_level"] == "absolute_blocked"
    assert claims["p_detect_mapping_claim_level"] == "relative_with_priors"
    assert claims["calibrated_SNR_claim_authorized"] is False
    assert claims["calibrated_event_probability_claim_authorized"] is False
    assert claims["absolute_LOD_claim_authorized"] is False
    assert claims["true_EV_concentration_claim_authorized"] is False
    assert claims["biological_specificity_claim_authorized"] is False


def test_R7_provenance_freeze_matches_current_R6_artifacts():
    plan = rv2.validate_R7_route_prior_mechanistic_decomposition_plan()
    provenance = plan["provenance_freeze"]
    expected = {
        "R6_manifest_checksum": rv2.sha256_file(
            R6_DIR / "R6_route_prior_sensitivity_manifest.csv"
        ),
        "R6_candidate_registry_checksum": rv2.sha256_file(
            R6_DIR / "R6_candidate_prior_registry.csv"
        ),
        "R6_candidate_sensitivity_matrix_checksum": rv2.sha256_file(
            R6_DIR / "R6_candidate_prior_sensitivity_matrix.csv"
        ),
        "R6_route_prior_factor_checksum": rv2.sha256_file(
            R6_DIR / "R6_route_prior_factor_by_route.csv"
        ),
        "R6_route_family_residual_checksum": rv2.sha256_file(
            R6_DIR / "R6_route_family_residual_warning_table.csv"
        ),
        "R6_scenario_residual_checksum": rv2.sha256_file(
            R6_DIR / "R6_scenario_residual_warning_table.csv"
        ),
        "R6_particle_stratum_residual_checksum": rv2.sha256_file(
            R6_DIR / "R6_particle_stratum_residual_warning_table.csv"
        ),
        "R6_main660_comparator_checksum": rv2.sha256_file(
            R6_DIR / "R6_main660_locked_comparator_summary.csv"
        ),
        "R6_claim_guardrail_checksum": rv2.sha256_file(
            R6_DIR / "R6_claim_boundary_guardrail_summary.csv"
        ),
        "R6_stop_gate_checksum": rv2.sha256_file(R6_DIR / "R6_stop_gate_summary.csv"),
        "R6_next_stage_matrix_checksum": rv2.sha256_file(
            R6_DIR / "R6_next_stage_recommendation_matrix.csv"
        ),
        "R6_run_manifest_checksum": rv2.sha256_file(R6_DIR / "run_manifest.json"),
    }

    assert set(provenance["required_checksum_fields"]) == (
        rv2.R7_REQUIRED_PROVENANCE_FIELDS
    )
    for key, value in expected.items():
        assert provenance[key] == value


@pytest.mark.parametrize(
    ("section", "key", "value", "match"),
    [
        (
            "authorization_boundary",
            "R7_execution_authorized",
            True,
            "R7_execution_authorized=false",
        ),
        (
            "authorization_boundary",
            "context_route_promotion_authorized",
            True,
            "context_route_promotion_authorized=false",
        ),
        (
            "authorization_boundary",
            "main_660_redefinition_authorized",
            True,
            "main_660_redefinition_authorized=false",
        ),
        (
            "authorization_boundary",
            "score_derived_physical_prior_authorized",
            True,
            "score_derived_physical_prior_authorized=false",
        ),
    ],
)
def test_R7_validation_fails_closed_for_forbidden_authority(
    section,
    key,
    value,
    match,
):
    broken = copy.deepcopy(rv2.load_R7_route_prior_mechanistic_decomposition_plan())
    broken[section][key] = value

    with pytest.raises(ValueError, match=match):
        rv2.validate_R7_route_prior_mechanistic_decomposition_plan(broken)


def test_R7_validation_fails_closed_for_scope_or_mechanistic_drift():
    broken = copy.deepcopy(rv2.load_R7_route_prior_mechanistic_decomposition_plan())
    broken["R7_plan_design"]["route_ids"].pop()
    with pytest.raises(ValueError, match="route ID set"):
        rv2.validate_R7_route_prior_mechanistic_decomposition_plan(broken)

    broken = copy.deepcopy(rv2.load_R7_route_prior_mechanistic_decomposition_plan())
    broken["R7_plan_design"]["max_mechanistic_candidate_count"] += 1
    with pytest.raises(ValueError, match="candidate count cap"):
        rv2.validate_R7_route_prior_mechanistic_decomposition_plan(broken)

    broken = copy.deepcopy(rv2.load_R7_route_prior_mechanistic_decomposition_plan())
    broken["accepted_width_prior_band"]["over_severe_caution_candidate_ids"] = []
    with pytest.raises(ValueError, match="width_quad_900 caution"):
        rv2.validate_R7_route_prior_mechanistic_decomposition_plan(broken)

    broken = copy.deepcopy(rv2.load_R7_route_prior_mechanistic_decomposition_plan())
    broken["accepted_width_prior_band"][
        "width_quad_floor035_nearby_example_is_invalidated"
    ] = False
    with pytest.raises(ValueError, match="floor035 nearby example"):
        rv2.validate_R7_route_prior_mechanistic_decomposition_plan(broken)

    broken = copy.deepcopy(rv2.load_R7_route_prior_mechanistic_decomposition_plan())
    broken["mechanistic_decomposition_design"]["score_derived_physical_prior_authorized"] = (
        True
    )
    with pytest.raises(ValueError, match="score-derived physical priors"):
        rv2.validate_R7_route_prior_mechanistic_decomposition_plan(broken)

    broken = copy.deepcopy(rv2.load_R7_route_prior_mechanistic_decomposition_plan())
    broken["mechanistic_decomposition_design"]["candidate_mechanistic_prior_registry"][0][
        "uses_particle_specific_empirical_fit"
    ] = True
    with pytest.raises(ValueError, match="uses_particle_specific_empirical_fit=false"):
        rv2.validate_R7_route_prior_mechanistic_decomposition_plan(broken)

    broken = copy.deepcopy(rv2.load_R7_route_prior_mechanistic_decomposition_plan())
    broken["non_width_prior_input_policy"][
        "source_v1_relative_score_as_physical_prior_authorized"
    ] = True
    with pytest.raises(ValueError, match="source_v1 score priors"):
        rv2.validate_R7_route_prior_mechanistic_decomposition_plan(broken)

    for gate in rv2.R7_REQUIRED_STOP_GATES:
        broken = copy.deepcopy(rv2.load_R7_route_prior_mechanistic_decomposition_plan())
        broken["stop_gates"] = [
            existing for existing in broken["stop_gates"] if existing != gate
        ]
        with pytest.raises(ValueError, match="stop gates are incomplete"):
            rv2.validate_R7_route_prior_mechanistic_decomposition_plan(broken)
