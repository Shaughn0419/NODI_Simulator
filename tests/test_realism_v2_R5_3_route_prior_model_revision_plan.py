from __future__ import annotations

import copy
import csv
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


R5_2_DIR = rv2.DEFAULT_R5_2_BOUNDED_SCENARIO_PRIOR_AUDIT_DIR


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_R5_3_plan_is_plan_only_and_uses_larger_review_package():
    plan = rv2.validate_R5_3_route_prior_model_revision_plan()
    boundary = plan["authorization_boundary"]
    cadence = plan["review_cadence_policy"]

    assert plan["stage"] == "R5_3_route_prior_model_revision_plan_only"
    assert (
        plan["prior_gate"]
        == "PASS_R5_2_RESULTS_PREPARE_ROUTE_PRIOR_MODEL_REVISION_PLAN_ONLY"
    )
    assert plan["selected_next_stage_lane"] == "route_prior_model_revision_plan_only"
    assert cadence["consolidate_plan_only_work_before_next_external_review"] is True
    assert cadence["external_review_required_before_any_execution"] is True
    assert (
        cadence["external_review_required_before_R6_plan_or_route_promotion"] is True
    )
    assert boundary["route_prior_plan_preparation_authorized_by_prior_gate"] is True
    assert boundary["route_prior_model_revision_execution_authorized"] is False
    assert boundary["R6_plan_preparation_authorized"] is False
    assert boundary["R6_execution_authorized"] is False
    assert boundary["R5_followup_expansion_authorized"] is False
    assert boundary["external_review_required_before_revision_execution"] is True


def test_R5_3_carries_forward_R5_2_systematic_warning_without_promotion():
    plan = rv2.validate_R5_3_route_prior_model_revision_plan()
    carry = plan["R5_2_evidence_carryforward"]
    manifest = _csv_rows(R5_2_DIR / "R5_2_scenario_prior_audit_manifest.csv")[0]
    weak = _csv_rows(R5_2_DIR / "R5_2_weak_reference_control_audit.csv")[0]
    context_rows = _csv_rows(R5_2_DIR / "R5_2_context_route_above_main_audit.csv")

    assert carry["R5_2_bounded_scenario_prior_audit_run"] is True
    assert carry["existing_R5_rows_audited"] == rv2.R5_2_EXISTING_R5_AUDIT_ROW_CAP
    assert carry["audit_route_id_count"] == rv2.R5_2_AUDIT_ROUTE_COUNT
    assert carry["scenario_bundle_count"] == rv2.R5_NAMED_SCENARIO_BUNDLE_COUNT
    assert carry["stochastic_seed_count"] == 0
    assert carry["selected_future_recommendation_class"] == (
        "prepare_route_prior_model_revision_plan_only"
    )
    assert carry["audit_decision"] == (
        "systematic_weak_reference_and_context_prior_warning_blocks_R6_plan"
    )
    assert carry["weak_reference_exceeds_main_660_scenario_count"] == 8
    assert carry["context_routes_above_main_under_all_scenarios"] == 20
    assert carry["R6_plan_preparation_authorized"] is False
    assert carry["context_route_promotion_authorized"] is False
    assert carry["main_660_redefinition_authorized"] is False

    assert manifest["selected_future_recommendation_class"] == (
        carry["selected_future_recommendation_class"]
    )
    assert weak["scenario_bundle_count_exceeding_main_660"] == "8"
    assert len(context_rows) == 20
    assert all(row["route_promotion_eligible"] == "False" for row in context_rows)


def test_R5_3_revision_design_is_existing_R5_artifact_only_and_capped():
    plan = rv2.validate_R5_3_route_prior_model_revision_plan()
    design = plan["revision_plan_design"]

    assert design["plan_execution_type"] == "plan_only_no_recompute_no_revision"
    assert design["future_revision_execution_type_if_reviewed"] == (
        "bounded_existing_R5_artifact_prior_model_audit_only"
    )
    assert design["uses_existing_R5_artifacts_only"] is True
    assert design["max_existing_R5_source_rows_if_future_reviewed"] == 14784
    assert design["route_id_count"] == 33
    assert set(design["route_ids"]) == rv2.R5_2_AUDIT_ROUTE_IDS
    assert set(design["scenario_bundle_ids"]) == rv2.R5_REQUIRED_SCENARIO_BUNDLE_IDS
    assert design["new_case_rows_authorized"] == 0
    assert design["new_scenario_bundle_authorized"] is False
    assert design["new_stochastic_seed_authorized"] is False
    assert design["new_solver_case_authorized"] is False
    assert design["new_experiment_authorized"] is False


def test_R5_3_decomposition_terms_and_prior_family_scope_are_tight():
    plan = rv2.validate_R5_3_route_prior_model_revision_plan()
    design = plan["revision_plan_design"]
    scope = plan["candidate_prior_model_revision_scope"]

    assert set(design["required_score_decomposition_terms"]) == (
        rv2.R5_3_REQUIRED_DECOMPOSITION_TERMS
    )
    assert "reference_prior_term" in design["required_score_decomposition_terms"]
    assert "route_width_depth_prior_term" in design["required_score_decomposition_terms"]
    assert set(scope["allowed_candidate_prior_families"]) == (
        rv2.R5_3_ALLOWED_CANDIDATE_PRIOR_FAMILIES
    )
    assert set(scope["forbidden_prior_families"]) == (
        rv2.R5_3_FORBIDDEN_PRIOR_FAMILIES
    )
    assert scope["low_dimensional_physics_or_prior_explanation_required"] is True
    assert scope["route_specific_fits_forbidden"] is True
    assert scope["context_route_promotion_forbidden"] is True
    assert "route_specific_manual_multiplier" in scope["forbidden_prior_families"]
    assert "thermal_404_bonus_term" in scope["forbidden_prior_families"]


def test_R5_3_future_gates_keep_R6_and_promotion_blocked():
    plan = rv2.validate_R5_3_route_prior_model_revision_plan()
    criteria = plan["future_pass_fail_criteria_if_execution_is_reviewed"]

    assert criteria["no_route_promotion"] is True
    assert criteria["no_main_660_redefinition"] is True
    assert criteria["no_selected_annulus_replacement"] is True
    assert criteria["no_calibrated_or_absolute_claim"] is True
    assert criteria["weak_reference_control_explained_or_remains_blocking"] is True
    assert criteria["all_20_context_warning_routes_exhaustively_reported"] is True
    assert criteria[
        "candidate_revision_must_be_global_or_family_level_not_route_specific"
    ] is True
    assert criteria["R6_plan_remains_blocked_until_separate_review"] is True


def test_R5_3_required_outputs_stop_gates_and_claim_boundaries_are_complete():
    plan = rv2.validate_R5_3_route_prior_model_revision_plan()
    claims = plan["claim_boundaries"]

    assert set(plan["required_outputs_if_authorized_after_future_review"]) == (
        rv2.R5_3_REQUIRED_OUTPUTS_IF_AUTHORIZED
    )
    assert "R5_3_score_term_decomposition.csv" in (
        plan["required_outputs_if_authorized_after_future_review"]
    )
    assert rv2.R5_3_REQUIRED_STOP_GATES.issubset(set(plan["stop_gates"]))
    assert "route_specific_manual_prior_multiplier_attempted" in plan["stop_gates"]
    assert "scenario_specific_per_route_fit_attempted" in plan["stop_gates"]
    assert "legacy_calibrated_detector_SNR_output_header_emitted" in plan["stop_gates"]
    assert claims["SNR_claim_level"] == "absolute_blocked"
    assert claims["event_probability_claim_level"] == "absolute_blocked"
    assert claims["p_detect_mapping_claim_level"] == "relative_with_priors"
    assert claims["calibrated_SNR_claim_authorized"] is False
    assert claims["calibrated_event_probability_claim_authorized"] is False
    assert claims["absolute_LOD_claim_authorized"] is False
    assert claims["biological_specificity_claim_authorized"] is False


def test_R5_3_provenance_freeze_matches_current_R5_2_artifacts():
    plan = rv2.validate_R5_3_route_prior_model_revision_plan()
    provenance = plan["provenance_freeze"]
    expected = {
        "R5_2_manifest_checksum": rv2.sha256_file(
            R5_2_DIR / "R5_2_scenario_prior_audit_manifest.csv"
        ),
        "R5_2_traceability_checksum": rv2.sha256_file(
            R5_2_DIR / "R5_2_audit_route_set_traceability.csv"
        ),
        "R5_2_context_audit_checksum": rv2.sha256_file(
            R5_2_DIR / "R5_2_context_route_above_main_audit.csv"
        ),
        "R5_2_weak_reference_checksum": rv2.sha256_file(
            R5_2_DIR / "R5_2_weak_reference_control_audit.csv"
        ),
        "R5_2_scenario_contribution_checksum": rv2.sha256_file(
            R5_2_DIR / "R5_2_scenario_bundle_contribution_audit.csv"
        ),
        "R5_2_route_family_checksum": rv2.sha256_file(
            R5_2_DIR / "R5_2_route_family_sensitivity_audit.csv"
        ),
        "R5_2_main660_checksum": rv2.sha256_file(
            R5_2_DIR / "R5_2_main_660_locked_comparator_summary.csv"
        ),
        "R5_2_sidecar_guardrail_checksum": rv2.sha256_file(
            R5_2_DIR / "R5_2_selected_annulus_and_404_sidecar_guardrail_summary.csv"
        ),
        "R5_2_claim_guardrail_checksum": rv2.sha256_file(
            R5_2_DIR / "R5_2_claim_boundary_guardrail_summary.csv"
        ),
        "R5_2_decision_table_checksum": rv2.sha256_file(
            R5_2_DIR / "R5_2_audit_decision_table.csv"
        ),
        "R5_2_next_stage_matrix_checksum": rv2.sha256_file(
            R5_2_DIR / "R5_2_next_stage_recommendation_matrix.csv"
        ),
        "R5_2_run_manifest_checksum": rv2.run_manifest_provenance_checksum(
            R5_2_DIR / "run_manifest.json"
        ),
    }

    assert set(provenance["required_checksum_fields"]) == (
        rv2.R5_3_REQUIRED_PROVENANCE_FIELDS
    )
    for key, value in expected.items():
        assert provenance[key] == value


@pytest.mark.parametrize(
    ("section", "key", "value", "match"),
    [
        (
            "authorization_boundary",
            "route_prior_model_revision_execution_authorized",
            True,
            "route_prior_model_revision_execution_authorized=false",
        ),
        (
            "authorization_boundary",
            "R6_plan_preparation_authorized",
            True,
            "R6_plan_preparation_authorized=false",
        ),
        (
            "authorization_boundary",
            "context_route_promotion_authorized",
            True,
            "context_route_promotion_authorized=false",
        ),
        (
            "authorization_boundary",
            "route_specific_manual_prior_multipliers_authorized",
            True,
            "route_specific_manual_prior_multipliers_authorized=false",
        ),
    ],
)
def test_R5_3_validation_fails_closed_for_forbidden_authority(
    section,
    key,
    value,
    match,
):
    broken = copy.deepcopy(rv2.load_R5_3_route_prior_model_revision_plan())
    broken[section][key] = value

    with pytest.raises(ValueError, match=match):
        rv2.validate_R5_3_route_prior_model_revision_plan(broken)


def test_R5_3_validation_fails_closed_for_scope_or_stop_gate_drift():
    broken = copy.deepcopy(rv2.load_R5_3_route_prior_model_revision_plan())
    broken["revision_plan_design"]["route_ids"].pop()
    with pytest.raises(ValueError, match="route ID set"):
        rv2.validate_R5_3_route_prior_model_revision_plan(broken)

    broken = copy.deepcopy(rv2.load_R5_3_route_prior_model_revision_plan())
    broken["revision_plan_design"]["required_score_decomposition_terms"].append(
        "posthoc_route_bonus_term"
    )
    with pytest.raises(ValueError, match="decomposition term set"):
        rv2.validate_R5_3_route_prior_model_revision_plan(broken)

    broken = copy.deepcopy(rv2.load_R5_3_route_prior_model_revision_plan())
    broken["candidate_prior_model_revision_scope"]["forbidden_prior_families"].remove(
        "route_specific_manual_multiplier"
    )
    with pytest.raises(ValueError, match="forbidden prior family"):
        rv2.validate_R5_3_route_prior_model_revision_plan(broken)

    for gate in rv2.R5_3_REQUIRED_STOP_GATES:
        broken = copy.deepcopy(rv2.load_R5_3_route_prior_model_revision_plan())
        broken["stop_gates"] = [
            existing for existing in broken["stop_gates"] if existing != gate
        ]
        with pytest.raises(ValueError, match="stop gates are incomplete"):
            rv2.validate_R5_3_route_prior_model_revision_plan(broken)
