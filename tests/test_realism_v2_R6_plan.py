from __future__ import annotations

import copy
import csv
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


R5_3_DIR = rv2.DEFAULT_R5_3_ROUTE_PRIOR_MODEL_REVISION_AUDIT_DIR


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_R6_plan_is_plan_only_after_R5_3_gate():
    plan = rv2.validate_R6_route_prior_sensitivity_plan()
    boundary = plan["authorization_boundary"]

    assert plan["schema_version"] == rv2.R6_PLAN_SCHEMA_VERSION
    assert plan["stage"] == "R6_route_prior_sensitivity_plan_only"
    assert plan["prior_gate"] == "PASS_R5_3_RESULTS_PREPARE_R6_PLAN_ONLY"
    assert plan["selected_next_stage_lane"] == "R6_route_prior_sensitivity_plan_only"
    assert boundary["R6_plan_preparation_authorized_by_prior_gate"] is True
    assert boundary["R6_plan_artifact_created"] is True
    assert boundary["R6_execution_authorized"] is False
    assert boundary["R5_followup_expansion_authorized"] is False
    assert boundary["context_route_promotion_authorized"] is False
    assert boundary["main_660_redefinition_authorized"] is False
    assert boundary["external_review_required_before_R6_execution"] is True


def test_R6_carries_R5_3_width_candidate_as_hypothesis_not_law():
    plan = rv2.validate_R6_route_prior_sensitivity_plan()
    carry = plan["R5_3_evidence_carryforward"]
    decision = _csv_rows(R5_3_DIR / "R5_3_route_prior_revision_decision_table.csv")[0]

    assert carry["R5_3_route_prior_model_revision_audit_run"] is True
    assert carry["existing_R5_rows_audited"] == rv2.R6_ROUTE_PRIOR_SOURCE_ROW_CAP
    assert carry["audit_route_id_count"] == rv2.R5_2_AUDIT_ROUTE_COUNT
    assert carry["scenario_bundle_count"] == rv2.R5_NAMED_SCENARIO_BUNDLE_COUNT
    assert carry["stochastic_seed_count"] == 0
    assert (
        carry["selected_candidate_prior_id"]
        == "global_width_quadratic_regularization"
    )
    assert carry["selected_candidate_dof_count"] == 1
    assert carry["weak_reference_delta_explained_fraction"] == 1.0
    assert carry["context_family_delta_explained_fraction"] == 1.0
    assert carry["context_routes_above_main_after_candidate"] == 0
    assert carry["context_scenario_rows_above_main_after_candidate"] == 0
    assert carry["weak_reference_scenario_rows_above_main_after_candidate"] == 0
    assert carry["R5_3_selected_candidate_is_explanatory_prior_not_calibrated_law"] is True
    assert carry["R6_plan_preparation_authorized_in_R5_3_manifest"] is False

    assert decision["selected_candidate_prior_id"] == carry["selected_candidate_prior_id"]
    assert decision["recommended_next_class"] == (
        "prepare_R6_plan_for_external_review_only"
    )
    assert decision["R6_plan_preparation_authorized"] == "False"


def test_R6_scope_uses_existing_artifacts_and_keeps_R5_2_route_panel():
    plan = rv2.validate_R6_route_prior_sensitivity_plan()
    design = plan["R6_plan_design"]

    assert design["plan_execution_type"] == "plan_only_no_R6_execution"
    assert design["future_R6_execution_type_if_reviewed"] == (
        "bounded_existing_R5_artifact_route_prior_sensitivity_audit_only"
    )
    assert design["uses_existing_R5_artifacts_only"] is True
    assert design["selected_R5_3_candidate_is_hypothesis_not_calibrated_law"] is True
    assert design["max_existing_R5_source_rows_if_future_reviewed"] == 14784
    assert design["max_R6_derived_candidate_rows"] == 177408
    assert design["route_id_count"] == 33
    assert set(design["route_ids"]) == rv2.R5_2_AUDIT_ROUTE_IDS
    assert set(design["scenario_bundle_ids"]) == rv2.R5_REQUIRED_SCENARIO_BUNDLE_IDS
    assert design["new_case_rows_authorized"] == 0
    assert design["new_scenario_bundle_authorized"] is False
    assert design["new_stochastic_seed_authorized"] is False
    assert design["new_solver_case_authorized"] is False
    assert design["new_experiment_authorized"] is False
    assert design["main660_comparator_policy"]["primary_pass_fail_comparator"] == (
        "candidate_adjusted_locked_main_660"
    )
    assert design["main660_comparator_policy"]["secondary_diagnostic_comparator"] == (
        "unadjusted_locked_main_660"
    )
    assert design["main660_comparator_policy"]["locked_main_660_route_ids"] == [
        "660_800x1400",
        "660_800x1500",
    ]
    assert (
        design["main660_comparator_policy"]["main_660_redefinition_authorized"]
        is False
    )


def test_R6_candidate_sensitivity_grid_is_bounded_and_named():
    plan = rv2.validate_R6_route_prior_sensitivity_plan()
    sensitivity = plan["candidate_prior_sensitivity_design"]
    registry = sensitivity["candidate_prior_registry"]

    assert sensitivity["candidate_prior_count"] == 12
    assert set(sensitivity["candidate_prior_ids"]) == rv2.R6_REQUIRED_CANDIDATE_PRIOR_IDS
    assert set(sensitivity["allowed_candidate_prior_families"]) == (
        rv2.R6_ALLOWED_CANDIDATE_PRIOR_FAMILIES
    )
    assert set(sensitivity["forbidden_prior_families"]) == (
        rv2.R6_FORBIDDEN_PRIOR_FAMILIES
    )
    assert set(sensitivity["width_pivot_nm_values"]) == {750, 800, 850, 900}
    assert {float(value) for value in sensitivity["width_exponent_values"]} == {
        1.0,
        1.5,
        2.0,
        2.5,
    }
    assert {float(value) for value in sensitivity["width_factor_floor_values"]} == {
        0.25,
        0.35,
        0.50,
    }
    assert set(sensitivity["required_sensitivity_output_fields"]) == (
        rv2.R6_REQUIRED_SENSITIVITY_FIELDS
    )
    assert sensitivity["nearby_candidate_definition"]["same_family_required"] is True
    assert sensitivity["nearby_candidate_definition"]["max_width_exponent_delta"] == 0.5
    assert sensitivity["nearby_candidate_definition"]["max_pivot_delta_nm"] == 50
    assert sensitivity["nearby_candidate_definition"]["max_floor_delta"] == 0.15
    assert (
        sensitivity["nearby_candidate_definition"][
            "non_width_alternatives_count_as_nearby_confirmation"
        ]
        is False
    )
    assert (
        sensitivity["non_width_candidate_prior_requirements"][
            "deterministic_functions_of_existing_R5_columns"
        ]
        is True
    )
    assert (
        sensitivity["non_width_candidate_prior_requirements"][
            "manual_route_id_multiplier_authorized"
        ]
        is False
    )

    anchor = [
        row
        for row in registry
        if row["candidate_prior_id"] == "global_width_quadratic_regularization"
    ][0]
    assert anchor["candidate_role"] == "R5_3_selected_candidate_anchor"
    assert anchor["width_pivot_nm"] == 800
    assert anchor["width_exponent"] == 2.0
    assert anchor["dof_count"] == 1
    assert all(row["uses_route_specific_multiplier"] is False for row in registry)
    assert all(row["uses_scenario_specific_per_route_fit"] is False for row in registry)
    assert all(row["uses_particle_specific_empirical_fit"] is False for row in registry)
    assert all(row["changes_main_660_definition"] is False for row in registry)
    assert all(row["authorizes_route_promotion"] is False for row in registry)
    assert all(row["claim_level"] == "relative_with_priors" for row in registry)
    reference = [
        row for row in registry if row["candidate_prior_id"] == "reference_band_penalty"
    ][0]
    bfp = [row for row in registry if row["candidate_prior_id"] == "BFP_alignment_risk"][0]
    assert "source_v1_relative_score" in reference["formula"]
    assert "width_nm" in bfp["formula"]
    assert "depth_nm" in bfp["formula"]


def test_R6_future_gates_require_sensitivity_not_promotion():
    plan = rv2.validate_R6_route_prior_sensitivity_plan()
    criteria = plan["future_pass_fail_criteria_if_execution_is_reviewed"]

    assert criteria["selected_R5_3_width_prior_remains_hypothesis"] is True
    assert (
        criteria["at_least_two_nearby_low_dimensional_candidates_explain_warning"]
        is True
    )
    assert (
        criteria["no_route_specific_or_scenario_specific_or_particle_specific_fit"]
        is True
    )
    assert (
        criteria["context_routes_above_main_after_candidate_zero_or_residual_explained"]
        is True
    )
    assert criteria["weak_reference_not_systematically_above_main"] is True
    assert criteria["main_660_definition_unchanged"] is True
    assert criteria["optional_660_900x1400_not_main_660"] is True
    assert criteria["selected_annulus_parallel_lens_only"] is True
    assert criteria["claim_boundary_absolute_blocked"] is True
    assert (
        criteria["route_governance_plan_if_reasonable_priors_leave_context_above_main"]
        is True
    )
    assert criteria["stop_if_only_forbidden_fits_resolve_warning"] is True
    assert criteria["R6_execution_requires_separate_external_review"] is True


def test_R6_outputs_stop_gates_claims_and_future_review_decisions_are_complete():
    plan = rv2.validate_R6_route_prior_sensitivity_plan()
    claims = plan["claim_boundaries"]

    assert set(plan["required_outputs_if_authorized_after_future_review"]) == (
        rv2.R6_REQUIRED_OUTPUTS_IF_AUTHORIZED
    )
    assert "R6_candidate_prior_sensitivity_matrix.csv" in (
        plan["required_outputs_if_authorized_after_future_review"]
    )
    assert "R6_route_family_residual_warning_table.csv" in (
        plan["required_outputs_if_authorized_after_future_review"]
    )
    assert rv2.R6_REQUIRED_STOP_GATES.issubset(set(plan["stop_gates"]))
    assert "R6_candidate_prior_grid_expanded_beyond_plan" in plan["stop_gates"]
    assert "route_specific_manual_prior_multiplier_attempted" in plan["stop_gates"]
    assert "legacy_calibrated_detector_SNR_output_header_emitted" in plan["stop_gates"]
    assert set(plan["allowed_future_external_review_decisions"]) == (
        rv2.R6_ALLOWED_FUTURE_REVIEW_DECISIONS
    )
    assert claims["SNR_claim_level"] == "absolute_blocked"
    assert claims["event_probability_claim_level"] == "absolute_blocked"
    assert claims["p_detect_mapping_claim_level"] == "relative_with_priors"
    assert claims["calibrated_SNR_claim_authorized"] is False
    assert claims["calibrated_event_probability_claim_authorized"] is False
    assert claims["absolute_LOD_claim_authorized"] is False
    assert claims["true_EV_concentration_claim_authorized"] is False
    assert claims["biological_specificity_claim_authorized"] is False


def test_R6_provenance_freeze_matches_current_R5_3_artifacts():
    plan = rv2.validate_R6_route_prior_sensitivity_plan()
    provenance = plan["provenance_freeze"]
    expected = {
        "R5_3_manifest_checksum": rv2.sha256_file(
            R5_3_DIR / "R5_3_route_prior_revision_manifest.csv"
        ),
        "R5_3_score_decomposition_checksum": rv2.sha256_file(
            R5_3_DIR / "R5_3_score_term_decomposition.csv"
        ),
        "R5_3_context_driver_checksum": rv2.sha256_file(
            R5_3_DIR / "R5_3_context_route_prior_driver_table.csv"
        ),
        "R5_3_weak_reference_driver_checksum": rv2.sha256_file(
            R5_3_DIR / "R5_3_weak_reference_control_prior_driver_table.csv"
        ),
        "R5_3_candidate_registry_checksum": rv2.sha256_file(
            R5_3_DIR / "R5_3_candidate_prior_revision_registry.csv"
        ),
        "R5_3_forbidden_guardrail_checksum": rv2.sha256_file(
            R5_3_DIR / "R5_3_forbidden_fit_guardrail_summary.csv"
        ),
        "R5_3_main660_checksum": rv2.sha256_file(
            R5_3_DIR / "R5_3_main660_locked_comparator_after_prior_model_summary.csv"
        ),
        "R5_3_sidecar_guardrail_checksum": rv2.sha256_file(
            R5_3_DIR / "R5_3_selected_annulus_and_404_sidecar_guardrail_summary.csv"
        ),
        "R5_3_claim_guardrail_checksum": rv2.sha256_file(
            R5_3_DIR / "R5_3_claim_boundary_guardrail_summary.csv"
        ),
        "R5_3_decision_table_checksum": rv2.sha256_file(
            R5_3_DIR / "R5_3_route_prior_revision_decision_table.csv"
        ),
        "R5_3_next_stage_matrix_checksum": rv2.sha256_file(
            R5_3_DIR / "R5_3_next_stage_recommendation_matrix.csv"
        ),
        "R5_3_run_manifest_checksum": rv2.sha256_file(R5_3_DIR / "run_manifest.json"),
    }

    assert set(provenance["required_checksum_fields"]) == (
        rv2.R6_REQUIRED_PROVENANCE_FIELDS
    )
    for key, value in expected.items():
        assert provenance[key] == value


@pytest.mark.parametrize(
    ("section", "key", "value", "match"),
    [
        (
            "authorization_boundary",
            "R6_execution_authorized",
            True,
            "R6_execution_authorized=false",
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
            "route_specific_manual_prior_multipliers_authorized",
            True,
            "route_specific_manual_prior_multipliers_authorized=false",
        ),
    ],
)
def test_R6_validation_fails_closed_for_forbidden_authority(
    section,
    key,
    value,
    match,
):
    broken = copy.deepcopy(rv2.load_R6_route_prior_sensitivity_plan())
    broken[section][key] = value

    with pytest.raises(ValueError, match=match):
        rv2.validate_R6_route_prior_sensitivity_plan(broken)


def test_R6_validation_fails_closed_for_candidate_or_scope_drift():
    broken = copy.deepcopy(rv2.load_R6_route_prior_sensitivity_plan())
    broken["R6_plan_design"]["route_ids"].pop()
    with pytest.raises(ValueError, match="route ID set"):
        rv2.validate_R6_route_prior_sensitivity_plan(broken)

    broken = copy.deepcopy(rv2.load_R6_route_prior_sensitivity_plan())
    broken["candidate_prior_sensitivity_design"]["candidate_prior_ids"].append(
        "posthoc_route_bonus"
    )
    with pytest.raises(ValueError, match="candidate prior ID set"):
        rv2.validate_R6_route_prior_sensitivity_plan(broken)

    broken = copy.deepcopy(rv2.load_R6_route_prior_sensitivity_plan())
    broken["candidate_prior_sensitivity_design"]["candidate_prior_registry"][0][
        "uses_route_specific_multiplier"
    ] = True
    with pytest.raises(ValueError, match="route-specific multipliers"):
        rv2.validate_R6_route_prior_sensitivity_plan(broken)

    broken = copy.deepcopy(rv2.load_R6_route_prior_sensitivity_plan())
    broken["candidate_prior_sensitivity_design"]["width_pivot_nm_values"].remove(900)
    with pytest.raises(ValueError, match="width pivot sensitivity"):
        rv2.validate_R6_route_prior_sensitivity_plan(broken)

    broken = copy.deepcopy(rv2.load_R6_route_prior_sensitivity_plan())
    broken["R6_plan_design"]["max_R6_derived_candidate_rows"] += 1
    with pytest.raises(ValueError, match="derived candidate row cap"):
        rv2.validate_R6_route_prior_sensitivity_plan(broken)

    broken = copy.deepcopy(rv2.load_R6_route_prior_sensitivity_plan())
    broken["R6_plan_design"]["main660_comparator_policy"][
        "primary_pass_fail_comparator"
    ] = "unadjusted_locked_main_660"
    with pytest.raises(ValueError, match="candidate-adjusted locked main"):
        rv2.validate_R6_route_prior_sensitivity_plan(broken)

    broken = copy.deepcopy(rv2.load_R6_route_prior_sensitivity_plan())
    broken["candidate_prior_sensitivity_design"]["nearby_candidate_definition"][
        "non_width_alternatives_count_as_nearby_confirmation"
    ] = True
    with pytest.raises(ValueError, match="non-width alternatives"):
        rv2.validate_R6_route_prior_sensitivity_plan(broken)

    for gate in rv2.R6_REQUIRED_STOP_GATES:
        broken = copy.deepcopy(rv2.load_R6_route_prior_sensitivity_plan())
        broken["stop_gates"] = [
            existing for existing in broken["stop_gates"] if existing != gate
        ]
        with pytest.raises(ValueError, match="stop gates are incomplete"):
            rv2.validate_R6_route_prior_sensitivity_plan(broken)
