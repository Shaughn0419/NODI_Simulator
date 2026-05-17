from __future__ import annotations

from collections.abc import Iterable
import os
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


_RESULT_DEPENDENCIES_BY_FILE: dict[str, tuple[Path, ...]] = {
    "test_realism_v2_R5_full_grid_v2.py": (rv2.DEFAULT_R5_FULL_GRID_V2_DIR,),
    "test_realism_v2_R5_1_interpretation.py": (rv2.DEFAULT_R5_1_INTERPRETATION_DIR,),
    "test_realism_v2_R5_1_next_stage_plan.py": (rv2.DEFAULT_R5_FULL_GRID_V2_DIR,),
    "test_realism_v2_R5_2_bounded_scenario_prior_audit.py": (
        rv2.DEFAULT_R5_2_BOUNDED_SCENARIO_PRIOR_AUDIT_DIR,
    ),
    "test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py": (
        rv2.DEFAULT_R5_FULL_GRID_V2_DIR,
        rv2.DEFAULT_R5_1_INTERPRETATION_DIR,
    ),
    "test_realism_v2_R5_3_route_prior_model_revision_audit.py": (
        rv2.DEFAULT_R5_3_ROUTE_PRIOR_MODEL_REVISION_AUDIT_DIR,
    ),
    "test_realism_v2_R5_3_route_prior_model_revision_plan.py": (
        rv2.DEFAULT_R5_2_BOUNDED_SCENARIO_PRIOR_AUDIT_DIR,
    ),
    "test_realism_v2_R6_plan.py": (
        rv2.DEFAULT_R5_3_ROUTE_PRIOR_MODEL_REVISION_AUDIT_DIR,
    ),
    "test_realism_v2_R6_route_prior_sensitivity_audit.py": (
        rv2.DEFAULT_R6_ROUTE_PRIOR_SENSITIVITY_AUDIT_DIR,
    ),
    "test_realism_v2_R7_plan.py": (rv2.DEFAULT_R6_ROUTE_PRIOR_SENSITIVITY_AUDIT_DIR,),
    "test_realism_v2_R7_route_prior_mechanistic_decomposition_audit.py": (
        rv2.DEFAULT_R7_ROUTE_PRIOR_MECHANISTIC_DECOMPOSITION_DIR,
    ),
    "test_realism_v2_R7_1_operator_artifact_validation_plan.py": (
        rv2.DEFAULT_R7_ROUTE_PRIOR_MECHANISTIC_DECOMPOSITION_DIR,
    ),
    "test_realism_v2_R7_1_operator_artifact_validation_protocol.py": (
        rv2.DEFAULT_R7_1_OPERATOR_ARTIFACT_VALIDATION_DIR,
    ),
    "test_realism_v2_R7_2_operator_artifact_gap_register_generation.py": (
        rv2.DEFAULT_R7_2_OPERATOR_ARTIFACT_GAP_REGISTER_DIR,
    ),
    "test_realism_v2_R7_2_operator_artifact_gap_register_plan.py": (
        rv2.DEFAULT_R7_1_OPERATOR_ARTIFACT_VALIDATION_DIR,
    ),
    "test_realism_v2_no_measured_data_closure.py": (
        rv2.DEFAULT_V2_NO_MEASURED_DATA_CLOSURE_DIR,
        rv2.DEFAULT_R7_2_OPERATOR_ARTIFACT_GAP_REGISTER_DIR,
    ),
    "test_realism_v2_revised_R4_rerun_plan.py": (
        rv2.DEFAULT_REPRESENTATIVE_FULL_WAVE_R4_DIR,
        rv2.DEFAULT_ROUTE_MODEL_REVISION_AUDIT_DIR,
    ),
    "test_realism_v2_route_model_revision_plan.py": (
        rv2.DEFAULT_REPRESENTATIVE_FULL_WAVE_R4_DIR,
    ),
}


_FRESH_CLONE_SAFE_TESTS_BY_FILE: dict[str, frozenset[str]] = {
    "test_realism_v2_R5_full_grid_v2.py": frozenset(
        {
            "test_R5_execution_requires_exact_external_authorization",
            "test_R5_source_schema_helpers_report_missing_or_bad_columns",
        }
    ),
    "test_realism_v2_R5_1_interpretation.py": frozenset(
        {"test_R5_1_interpretation_requires_exact_external_authorization"}
    ),
    "test_realism_v2_R5_1_next_stage_plan.py": frozenset(
        {
            "test_R5_1_plan_is_plan_only_and_selects_interpretation_lane",
            "test_R5_1_plan_consumes_clean_R5_results_without_authorizing_expansion",
            "test_R5_1_scope_is_zero_new_case_rows_and_existing_artifacts_only",
            "test_R5_1_required_outputs_and_future_recommendations_are_plan_only",
            "test_R5_1_stop_gates_and_claim_boundaries_are_complete",
            "test_R5_1_validation_fails_closed_for_forbidden_authority",
            "test_R5_1_missing_required_stop_gate_fails_closed",
            "test_R5_1_rejects_new_case_or_experiment_scope",
        }
    ),
    "test_realism_v2_R5_2_bounded_scenario_prior_audit.py": frozenset(
        {"test_R5_2_audit_requires_exact_external_authorization"}
    ),
    "test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py": frozenset(
        {
            "test_R5_2_plan_is_plan_only_and_consumes_R5_1_gate",
            "test_R5_2_audit_design_is_posthoc_existing_R5_only_and_capped",
            "test_R5_2_required_outputs_stop_gates_and_claim_boundaries_are_complete",
            "test_R5_2_validation_fails_closed_for_forbidden_authority",
            "test_R5_2_validation_fails_closed_for_route_scope_or_stop_gate_drift",
        }
    ),
    "test_realism_v2_R5_3_route_prior_model_revision_audit.py": frozenset(
        {"test_R5_3_audit_requires_exact_external_authorization"}
    ),
    "test_realism_v2_R5_3_route_prior_model_revision_plan.py": frozenset(
        {
            "test_R5_3_plan_is_plan_only_and_uses_larger_review_package",
            "test_R5_3_revision_design_is_existing_R5_artifact_only_and_capped",
            "test_R5_3_decomposition_terms_and_prior_family_scope_are_tight",
            "test_R5_3_future_gates_keep_R6_and_promotion_blocked",
            "test_R5_3_required_outputs_stop_gates_and_claim_boundaries_are_complete",
            "test_R5_3_validation_fails_closed_for_forbidden_authority",
            "test_R5_3_validation_fails_closed_for_scope_or_stop_gate_drift",
        }
    ),
    "test_realism_v2_R6_plan.py": frozenset(
        {
            "test_R6_plan_is_plan_only_after_R5_3_gate",
            "test_R6_scope_uses_existing_artifacts_and_keeps_R5_2_route_panel",
            "test_R6_candidate_sensitivity_grid_is_bounded_and_named",
            "test_R6_future_gates_require_sensitivity_not_promotion",
            "test_R6_outputs_stop_gates_claims_and_future_review_decisions_are_complete",
            "test_R6_validation_fails_closed_for_forbidden_authority",
            "test_R6_validation_fails_closed_for_candidate_or_scope_drift",
        }
    ),
    "test_realism_v2_R6_route_prior_sensitivity_audit.py": frozenset(
        {"test_R6_audit_requires_exact_external_authorization"}
    ),
    "test_realism_v2_R7_plan.py": frozenset(
        {
            "test_R7_plan_is_plan_only_after_R6_gate",
            "test_R7_scope_is_existing_artifact_only_and_keeps_R6_caps",
            "test_R7_accepted_band_absorbs_R6_cautions",
            "test_R7_mechanistic_registry_is_low_dimensional_and_non_promoting",
            "test_R7_particle_optional_900_and_non_width_policies_are_guarded",
            "test_R7_outputs_stop_gates_claims_and_future_review_decisions_are_complete",
            "test_R7_validation_fails_closed_for_forbidden_authority",
            "test_R7_validation_fails_closed_for_scope_or_mechanistic_drift",
        }
    ),
    "test_realism_v2_R7_route_prior_mechanistic_decomposition_audit.py": frozenset(
        {"test_R7_audit_requires_exact_external_authorization"}
    ),
    "test_realism_v2_R7_1_operator_artifact_validation_plan.py": frozenset(
        {
            "test_R7_1_plan_is_plan_only_after_R7_self_review_gate",
            "test_R7_1_evidence_modules_are_protocols_not_measurements",
            "test_R7_1_outputs_stop_gates_and_claims_are_fail_closed",
            "test_R7_1_validation_fails_closed_for_forbidden_authority",
            "test_R7_1_validation_fails_closed_for_missing_module_or_fit_drift",
        }
    ),
    "test_realism_v2_R7_1_operator_artifact_validation_protocol.py": frozenset(
        {"test_R7_1_protocol_requires_exact_self_authorization"}
    ),
    "test_realism_v2_R7_2_operator_artifact_gap_register_generation.py": frozenset(
        {"test_R7_2_generation_requires_exact_self_authorization"}
    ),
    "test_realism_v2_R7_2_operator_artifact_gap_register_plan.py": frozenset(
        {
            "test_R7_2_plan_is_plan_only_after_R7_1_gate",
            "test_R7_2_artifact_registry_maps_protocols_and_remains_not_started",
            "test_R7_2_outputs_stop_gates_and_claims_are_fail_closed",
            "test_R7_2_validation_fails_closed_for_forbidden_authority",
            "test_R7_2_validation_fails_closed_for_artifact_or_fit_drift",
        }
    ),
    "test_realism_v2_no_measured_data_closure.py": frozenset(
        {
            "test_v2_closure_plan_is_no_measured_data_plan_only",
            "test_v2_closure_validation_fails_closed_for_forbidden_drift",
            "test_v2_closure_generation_requires_exact_self_authorization",
        }
    ),
    "test_realism_v2_revised_R4_rerun_plan.py": frozenset(
        {
            "test_R4_revised_rerun_plan_is_plan_only_and_blocks_R5",
            "test_R4_revised_rerun_consumes_accepted_audit_without_recovering_main_660",
            "test_R4_revised_rerun_cost_cap_is_same_representative_R4_panel",
            "test_R4_revised_rerun_route_and_particle_panels_are_locked",
            "test_R4_revised_rerun_sign_convention_and_reliability_are_preregistered",
            "test_R4_revised_rerun_required_diagnostic_fields_are_explicit",
            "test_R4_revised_rerun_recovery_requires_all_three_main_660_gates",
            "test_R4_revised_rerun_required_outputs_are_not_R5_outputs",
            "test_R4_revised_rerun_stop_gates_include_both_legacy_snr_names",
            "test_R4_revised_rerun_manifest_expectations_keep_forbidden_flags_false",
            "test_R4_revised_rerun_validation_fails_closed",
            "test_R4_revised_rerun_missing_stop_gate_fails_closed",
        }
    ),
    "test_realism_v2_route_model_revision_plan.py": frozenset(
        {
            "test_R4_route_model_revision_plan_is_plan_only_and_blocks_R5",
            "test_R4_route_model_revision_consumes_all_demoted_R4_routes",
            "test_R4_route_model_revision_focuses_on_sign_phase_not_R5",
            "test_R4_route_model_revision_sign_phase_contract_is_explicit",
            "test_R4_route_model_revision_recovery_gate_requires_future_R4_review",
            "test_R4_route_model_revision_required_outputs_are_review_scoped",
            "test_R4_route_model_revision_stop_gates_are_fail_closed",
            "test_R4_route_model_revision_manifest_expectations_keep_forbidden_flags_false",
            "test_R4_route_model_revision_validation_fails_closed",
            "test_R4_route_model_revision_missing_stop_gate_fails_closed",
        }
    ),
}


def _missing_paths(paths: Iterable[Path]) -> list[Path]:
    if os.environ.get("NODI_TEST_FORCE_MISSING_RESULTS") == "1":
        return list(paths)
    return [path for path in paths if not path.exists()]


def _base_test_name(item_name: str) -> str:
    return item_name.split("[", 1)[0]


def _result_dependencies_for_item(item: pytest.Item) -> tuple[Path, ...]:
    path = Path(str(item.path))
    if _base_test_name(item.name) in _FRESH_CLONE_SAFE_TESTS_BY_FILE.get(path.name, ()):
        return ()
    marker = item.get_closest_marker("requires_results")
    if marker is not None and marker.args:
        return tuple(Path(arg) for arg in marker.args)
    return _RESULT_DEPENDENCIES_BY_FILE.get(path.name, ())


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    _ = config
    for item in items:
        dependencies = _result_dependencies_for_item(item)
        if not dependencies:
            continue
        missing = _missing_paths(dependencies)
        if not missing:
            continue
        missing_text = ", ".join(str(path) for path in missing)
        item.add_marker(
            pytest.mark.skip(
                reason=(
                    "requires precomputed realism_v2 result artifacts not present in "
                    f"this checkout: {missing_text}"
                )
            )
        )
