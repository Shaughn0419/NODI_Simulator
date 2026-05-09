# EV/NODI realism v2 R5.1 route-role stability interpretation analysis

## Decision consumed

External gate consumed:

```text
PASS_TO_R5_1_ROUTE_ROLE_STABILITY_INTERPRETATION_ONLY
```

This run is interpretation-only. It uses existing R5 full-grid v2 artifacts and adds no case rows, scenario bundles, stochastic seeds, solver cases, or experiments.

## Scope boundary

Authorized and executed:

```text
R5.1 route-role stability interpretation only
existing R5 artifacts only
new case rows = 0
new scenario bundles = 0
new stochastic seeds = 0
new solver cases = 0
new experiments = 0
```

Still not authorized:

```text
R6 plan preparation
R6 execution
R5 follow-up expansion
route promotion
main-660 redefinition
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

## Required outputs

The R5.1 result directory is:

```text
results/ev_nodi_realism_v2_R5_1_route_role_stability_interpretation/
```

It contains exactly the pre-registered interpretation outputs:

```text
R5_1_route_role_stability_interpretation_manifest.csv
R5_1_route_role_stability_decision_table.csv
R5_1_scenario_sensitivity_interpretation.csv
R5_1_context_route_high_score_warning_table.csv
R5_1_main_660_robustness_interpretation.csv
R5_1_weak_reference_control_interpretation.csv
R5_1_selected_annulus_nonpromotion_summary.csv
R5_1_claim_boundary_guardrail_summary.csv
R5_1_next_stage_options_matrix.csv
run_manifest.json
R5_1_route_role_stability_interpretation_report.md
```

No R6, R5 follow-up, solver, stochastic, experiment, or full-grid output was created by R5.1.

## Interpretation result

The R5.1 manifest records:

```text
R5_1_interpretation_run = true
R5_case_rows_interpreted = 256256
new_case_rows_added = 0
new_scenario_bundles_added = 0
new_stochastic_seeds_added = 0
new_solver_cases_added = 0
new_experiments_started = 0
selected_future_recommendation_class =
  prepare_bounded_additional_scenario_prior_audit_plan_only
interpretation_decision =
  R5_clean_but_weak_reference_and_context_warnings_require_bounded_scenario_prior_audit_plan
```

The selected future recommendation is not an authorization to execute that future lane. It is a recommendation class for the next external-review planning step only.

## Main-660 interpretation

Main-660 remains locked to:

```text
660 / 800x1400
660 / 800x1500
```

R5.1 preserves the R4.2 validation-grade carryforward and does not redefine main-660:

```text
fine_confirm_main660_fraction = 1.0
fine_confirm_sign_reliable_subset_fraction = 1.0
review_refined_main660_fraction = 1.0
fine_confirm_agrees_with_review_refined = 1.0
main_660_redefinition_authorized = false
context_route_promotion_authorized = false
route_specific_manual_sign_flips_authorized = false
```

The R5 main-660 mean relative-prior score carried into the interpretation is:

```text
main_660 mean = 0.126095409614
```

This remains a relative-with-priors scenario score, not calibrated detector performance.

## Weak-reference and context-route warnings

R5.1 identifies route-role ambiguity that should be interpreted before any R6 or experimental-panel planning:

```text
weak_reference_control mean = 0.152257463311
main_660 mean = 0.126095409614
weak_reference_exceeds_main_660 = true
context_routes_exceeding_main_660_mean = 20
top context warning route = 660_500x1500
```

The top context warning rows are warning-only:

```text
660_500x1500 mean = 0.196395589288
660_500x1400 mean = 0.189745117922
660_500x1300 mean = 0.182574838578
660_500x1200 mean = 0.173858902284
660_600x1500 mean = 0.165471882664
```

Every context warning row remains:

```text
context_route_promotion_authorized = false
route_promotion_eligible = false
interpretation = high_context_score_warning_not_route_promotion
```

This is the main reason R5.1 selects a bounded additional scenario-prior audit plan as the next review target rather than R6 plan preparation.

## Scenario sensitivity interpretation

R5.1 summarizes the eight existing R5 scenario bundles only. It does not add or alter scenario bundles. The scenario interpretation remains bounded to relative-prior evidence.

The R5 source evidence remains:

```text
R5 case rows = 256256
v1 source rows = 32032
scenario bundles = 8
stochastic seeds = 0
```

## Claim boundary

R5.1 keeps the claim boundary closed:

```text
SNR_claim_level = absolute_blocked
event_probability_claim_level = absolute_blocked
p_detect_mapping_claim_level = relative_with_priors
```

The R5.1 guardrail summary reports:

```text
legacy_detector_SNR_output_header_emitted = false
legacy_calibrated_detector_SNR_output_header_emitted = false
calibrated_SNR_or_event_probability_claim_emitted = false
thermal_sidecar_used_to_increase_NODI_score = false
finite_zero_event_blank_safety_claim_emitted = false
```

Exact legacy CSV headers are absent from the R5.1 outputs:

```text
detector_SNR
calibrated_detector_SNR
```

Guardrail field names containing those strings are allowed because they are stop-gate indicators, not legacy SNR output claims.

## Manifest guardrails

The R5.1 run manifest keeps the forbidden lanes closed:

```text
R6_plan_preparation_authorized = false
R6_execution_authorized = false
R5_followup_expansion_authorized = false
new_case_rows_authorized = 0
context_route_promotion_authorized = false
main_660_redefinition_authorized = false
selected_annulus_bounds_changed = false
calibrated_SNR_claim_emitted = false
calibrated_event_probability_claim_emitted = false
absolute_LOD_or_true_concentration_claim_emitted = false
biological_specificity_claim_emitted = false
ET2030_direct_current_input_unlocked = false
```

## Verification

Commands run:

```text
python tools/one_shot/ev_nodi_realism_v2_R5_1_interpretation.py

ruff check realism_v2.py \
  tools/one_shot/ev_nodi_realism_v2_R5_1_interpretation.py \
  tests/test_realism_v2_R5_1_interpretation.py \
  tests/test_realism_v2_R5_1_next_stage_plan.py

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_realism_v2_R5_1_interpretation.py \
  tests/test_realism_v2_R5_1_next_stage_plan.py

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_realism_v2_R5_1_interpretation.py \
  tests/test_realism_v2_R5_1_next_stage_plan.py \
  tests/test_realism_v2_R5_full_grid_v2.py \
  tests/test_realism_v2_R5_plan.py \
  tests/test_realism_v2_R4_2_adjudication.py \
  tests/test_realism_v2_R4_2_adjudication_plan.py \
  tests/test_realism_v2_contract.py

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

Results:

```text
R5.1 tool execution: pass
ruff: All checks passed
R5.1 focused tests: 21 passed in 1.31s
R5.1/R5/R4.2/contract focused suite: 82 passed in 10.99s
full suite: 832 passed in 206.27s
```

The review bundle was also extracted and smoke-tested:

```text
bundle: review_bundles/ev_nodi_realism_v2_r5_1_results_review.zip
unzip -t: pass
resource fork entries: 0
extracted R5.1/R5/R4.2/contract focused suite: 82 passed in 8.48s
```

## Next review target

The only next action supported by this R5.1 result is:

```text
prepare_bounded_additional_scenario_prior_audit_plan_only
```

That next step must remain plan-only and externally reviewed before any execution. It should address:

```text
weak-reference-control high relative score
context-route high-score warnings
scenario-prior sensitivity
route-role stability interpretation
main-660 governance lock
claim-boundary preservation
```

It must not authorize R6 planning or execution, R5 follow-up expansion, route promotion, main-660 redefinition, selected-annulus changes, calibrated claims, or absolute biological/detector claims.
