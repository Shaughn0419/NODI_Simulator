# EV/NODI realism v2 R5.2 bounded scenario-prior audit plan for external review

## Decision consumed

External gate consumed:

```text
PASS_R5_1_RESULTS_PREPARE_BOUNDED_SCENARIO_PRIOR_AUDIT_PLAN_ONLY
```

This artifact is a plan only. It does not execute the bounded scenario-prior audit and does not prepare or execute R6.

## Purpose

R5.1 found that R5 full-grid v2 is internally consistent and claim-guarded, but the route-role interpretation remains ambiguous:

```text
main_660 mean relative-prior score = 0.126095409614
weak_reference_control mean relative-prior score = 0.152257463311
weak_reference_control exceeds main_660 = true
context routes exceeding main_660 mean = 20
top context warning route = 660_500x1500
```

The R5.2 plan asks for a bounded posthoc audit to determine whether these warnings are explained by scenario-prior sensitivity, weak-reference/control artifacts, route-family sensitivity, or unresolved route-governance instability.

## Authorization boundary

Authorized now:

```text
Prepare R5.2 bounded scenario-prior audit plan only.
```

Not authorized now:

```text
bounded scenario-prior audit execution
R6 plan preparation
R6 execution
R5 follow-up expansion
new scenario bundles
new stochastic seeds
new solver cases
new experiments
route promotion
main-660 redefinition
optional 660 / 900x1400 redefining main-660
selected-annulus bound changes
selected-annulus replacing all-crossing ranking
route-specific manual sign flips
calibrated SNR
calibrated event probability
absolute LOD
true EV concentration
biological specificity
Tsuyama paper-fit continuation
v1 full-grid overwrite
ET2030 direct current-input unlock
```

The plan itself records:

```text
stage = R5_2_bounded_scenario_prior_audit_plan_only
bounded_scenario_prior_audit_execution_authorized = false
R6_plan_preparation_authorized = false
R6_execution_authorized = false
R5_followup_expansion_authorized = false
external_review_required_before_audit_execution = true
```

## Audit design

The future audit, if separately authorized after review, is deliberately posthoc-only:

```text
audit_execution_type = posthoc_existing_R5_artifact_audit_only
uses_existing_R5_artifacts_only = true
deterministic_no_stochastic_seeds = true
new_case_rows_authorized = 0
new_scenario_bundle_authorized = false
new_stochastic_seed_authorized = false
new_solver_case_authorized = false
new_experiment_authorized = false
```

The audit is capped to a frozen subset of existing R5 rows:

```text
audit_route_id_count = 33
source_particles_per_route = 56
scenario_bundle_count = 8
stochastic_seed_count = 0
audit_existing_R5_source_row_cap = 14784
```

The calculation is:

```text
33 route IDs × 56 particles × 8 existing R5 scenario bundles = 14784 existing R5 rows
```

## Route set

The plan includes:

```text
2 locked main-660 comparators
1 weak-reference control
1 optional 660 robustness probe
3 medium/shortwave controls
6 selected-annulus sidecars
20 above-main context warning routes
```

Locked main-660 comparators:

```text
660_800x1400
660_800x1500
```

Weak-reference and optional controls:

```text
660_700x1500  weak_reference_control
660_900x1400  optional_robustness_probe
```

Medium/shortwave controls:

```text
488_600x1500
532_600x1500
404_600x1300
```

Selected-annulus sidecars:

```text
404_800x550
404_800x600
404_800x700
660_800x550
660_800x600
660_800x700
```

Above-main context warnings:

```text
660_500x1500
660_500x1400
660_500x1300
660_500x1200
660_600x1500
660_500x1100
660_600x1400
660_500x1000
660_600x1300
660_700x1400
660_500x900
660_600x1200
660_700x1300
660_600x1100
532_500x1500
660_500x800
660_700x1200
532_500x1400
660_600x1000
532_500x1300
```

Every planned route has:

```text
route_promotion_authorized = false
```

## Scenario dimensions

The audit is limited to the eight already-reviewed R5 scenario bundles:

```text
404_thermal_high_low_power
BFP_slit_offset_leakage
DAQ_low_resolution_sampling
PEG_pessimistic_wall_loss
blank_bursty_RIN_high
detector_50ohm_pessimistic
external_TIA_optimistic
nominal_instrument_clean_blank
```

No scenario bundle is added or modified.

## Required future outputs

If a future external review authorizes audit execution, the audit must produce only:

```text
R5_2_scenario_prior_audit_manifest.csv
R5_2_audit_route_set_traceability.csv
R5_2_context_route_above_main_audit.csv
R5_2_weak_reference_control_audit.csv
R5_2_scenario_bundle_contribution_audit.csv
R5_2_route_family_sensitivity_audit.csv
R5_2_main_660_locked_comparator_summary.csv
R5_2_selected_annulus_and_404_sidecar_guardrail_summary.csv
R5_2_claim_boundary_guardrail_summary.csv
R5_2_audit_decision_table.csv
R5_2_next_stage_recommendation_matrix.csv
run_manifest.json
R5_2_bounded_scenario_prior_audit_report.md
```

No full-grid, solver, stochastic, experiment, route-promotion, calibrated-claim, or R6 output is in the required output list.

## Stop gates

The plan fails closed on:

```text
bounded_scenario_prior_audit_execution_without_external_authorization
R6_plan_preparation_started
R6_execution_started
R5_followup_expansion_started
R5_case_rows_expanded_beyond_reviewed_cap
audit_source_rows_exceed_reviewed_plan_cap
audit_route_set_expanded_beyond_plan
new_scenario_bundle_added
new_stochastic_seed_added
new_solver_case_started
new_experiment_started
v1_full_grid_output_overwritten
Tsuyama_paper_fit_continued
selected_annulus_bounds_changed
selected_annulus_replaces_all_crossing_ranking
context_route_promotion_attempted
main_660_redefinition_attempted
optional_660_900x1400_redefines_main_660
route_specific_manual_sign_flip_attempted
calibrated_SNR_or_event_probability_claim_emitted
absolute_LOD_or_true_concentration_claim_emitted
biological_specificity_claim_emitted
ET2030_direct_current_input_unlocked_without_measured_bench_artifact
thermal_sidecar_used_to_increase_NODI_score
finite_zero_event_blank_safety_claim_emitted
legacy_detector_SNR_output_header_emitted
legacy_calibrated_detector_SNR_output_header_emitted
```

## Claim boundaries

The plan preserves:

```text
SNR_claim_level = absolute_blocked
event_probability_claim_level = absolute_blocked
p_detect_mapping_claim_level = relative_with_priors
calibrated_SNR_claim_authorized = false
calibrated_event_probability_claim_authorized = false
absolute_LOD_claim_authorized = false
true_EV_concentration_claim_authorized = false
biological_specificity_claim_authorized = false
legacy_detector_SNR_output_header_authorized = false
legacy_calibrated_detector_SNR_output_header_authorized = false
```

## Provenance freeze

The plan freezes R5.1 and R5 source artifacts:

```text
R5_1_manifest_checksum
R5_1_decision_table_checksum
R5_1_context_warning_table_checksum
R5_1_weak_reference_checksum
R5_1_next_stage_options_checksum
R5_1_run_manifest_checksum
R5_case_manifest_checksum
R5_summary_checksum
R5_context_no_promotion_checksum
R5_route_role_stability_checksum
R5_scenario_sensitivity_checksum
R5_run_manifest_checksum
```

The validator and tests recompute these checksums against current artifacts.

## Verification

Commands run:

```text
python -m json.tool configs/realism_v2/r5_2_bounded_scenario_prior_audit_plan.yaml

ruff check realism_v2.py \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py
```

Initial results:

```text
JSON check: OK
ruff: All checks passed
R5.2 plan focused tests: 12 passed in 5.72s
R5.2/R5.1/R5/contract focused suite: 71 passed in 14.24s
full suite: 844 passed in 208.03s
extracted review bundle focused suite: 71 passed
```

## Next review target

The strongest possible passing decision for this plan should be:

```text
PASS_TO_BOUNDED_SCENARIO_PRIOR_AUDIT_ONLY
```

That would authorize only the posthoc, 14,784-row-capped R5.2 audit execution described here. It would still not authorize R6 plan preparation, R6 execution, R5 follow-up expansion, route promotion, main-660 redefinition, new scenario bundles, stochastic seeds, solver cases, experiments, selected-annulus changes, or calibrated/absolute claims.
