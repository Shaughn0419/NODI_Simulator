# EV/NODI realism v2 R5.2 bounded scenario-prior audit analysis

## Decision consumed

External gate consumed:

```text
PASS_TO_BOUNDED_SCENARIO_PRIOR_AUDIT_ONLY
```

This run executes only the bounded, posthoc, existing-R5-artifact R5.2 audit described in the reviewed R5.2 plan.

## Scope boundary

Executed:

```text
R5.2 bounded scenario-prior audit only
posthoc existing R5 artifacts only
route IDs audited = 33
existing R5 rows audited = 14784
scenario bundles = 8 existing R5 bundles
stochastic seeds = 0
new case rows = 0
new scenario bundles = 0
new solver cases = 0
new experiments = 0
```

Still not authorized:

```text
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

## Required outputs

The R5.2 audit result directory is:

```text
results/ev_nodi_realism_v2_R5_2_bounded_scenario_prior_audit/
```

It contains exactly the 13 pre-registered outputs:

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

No R6, full-grid, solver, stochastic, experiment, route-promotion, selected-annulus-change, or calibrated-claim artifact was created.

## Audit finding

The audit found that the R5.1 warning is systematic across the existing R5 scenario priors, not isolated to one bundle:

```text
weak_reference_control exceeds main_660 in 8 / 8 existing R5 scenario bundles
20 / 20 above-main context routes exceed main_660 under all 8 existing R5 scenario bundles
```

Core means:

```text
main_660 mean relative-prior score = 0.126095409614
weak_reference_control mean relative-prior score = 0.152257463311
above-main context-route family mean relative-prior score = 0.151918689204
```

Top context-route audit rows:

```text
660_500x1500 mean = 0.196395589288, ratio_vs_main = 1.557516
660_500x1400 mean = 0.189745117922, ratio_vs_main = 1.504774
660_500x1300 mean = 0.182574838578, ratio_vs_main = 1.447910
660_500x1200 mean = 0.173858902284, ratio_vs_main = 1.378789
660_600x1500 mean = 0.165471882664, ratio_vs_main = 1.312275
```

All context warning rows remain:

```text
context_route_promotion_authorized = false
route_promotion_eligible = false
interpretation = systematic_above_main_context_warning_not_route_promotion
```

## Decision result

R5.2 selected:

```text
selected_future_recommendation_class =
  prepare_route_prior_model_revision_plan_only
audit_decision =
  systematic_weak_reference_and_context_prior_warning_blocks_R6_plan
```

The rationale is that weak-reference-control and the above-main context-route family exceed locked main-660 under all eight existing R5 scenario priors. That pattern is too systematic to pass directly to R6 planning, but it is still not route promotion or main-660 redefinition.

The selected recommendation class is a future planning target only. It authorizes no execution.

## Main-660 and route governance

Main-660 remains locked to:

```text
660_800x1400
660_800x1500
```

The main comparator output records:

```text
main_660_route_role_locked = true
main_660_redefinition_authorized = false
route_promotion_authorized = false
```

The audit decision table keeps:

```text
R6_plan_preparation_authorized = false
route_promotion_authorized = false
main_660_redefinition_authorized = false
claim_level = relative_with_priors
```

## Scenario bundle contribution

The audit used only the eight existing R5 scenario bundles:

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

Every scenario contribution row keeps:

```text
new_scenario_bundle_authorized = false
calibrated_probability_claim_authorized = false
```

## Sidecar and selected-annulus guardrails

The selected-annulus and 404 sidecar output records:

```text
selected_annulus_replaces_all_crossing_ranking = false
selected_annulus_bound_change_authorized = false
thermal_sidecar_used_to_increase_NODI_score = false
```

These rows remain diagnostic/sidecar evidence only.

## Claim boundary

R5.2 keeps:

```text
SNR_claim_level = absolute_blocked
event_probability_claim_level = absolute_blocked
p_detect_mapping_claim_level = relative_with_priors
```

The guardrail output records:

```text
legacy_detector_SNR_output_header_emitted = false
legacy_calibrated_detector_SNR_output_header_emitted = false
calibrated_SNR_or_event_probability_claim_emitted = false
absolute_LOD_or_true_concentration_claim_emitted = false
biological_specificity_claim_emitted = false
thermal_sidecar_used_to_increase_NODI_score = false
finite_zero_event_blank_safety_claim_emitted = false
```

Exact legacy CSV headers are absent from R5.2 outputs:

```text
detector_SNR
calibrated_detector_SNR
```

Guardrail field names containing those strings are stop-gate indicators, not legacy output claim columns.

## Manifest guardrails

The R5.2 run manifest records:

```text
run_id = EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit
R5_2_bounded_scenario_prior_audit_run = true
new_case_rows_authorized = 0
new_scenario_bundle_authorized = false
new_stochastic_seed_authorized = false
new_solver_case_authorized = false
new_experiment_authorized = false
R6_plan_preparation_authorized = false
R6_execution_authorized = false
R5_followup_expansion_authorized = false
context_route_promotion_authorized = false
main_660_redefinition_authorized = false
route_specific_manual_sign_flips_authorized = false
calibrated_event_probability_claim_emitted = false
absolute_LOD_or_true_concentration_claim_emitted = false
biological_specificity_claim_emitted = false
selected_annulus_replaces_all_crossing_ranking = false
thermal_sidecar_used_to_increase_NODI_score = false
finite_zero_event_blank_safety_claim_emitted = false
```

## Verification

Commands run:

```text
python tools/ev_nodi_realism_v2_R5_2_bounded_scenario_prior_audit.py

ruff check realism_v2.py \
  tools/ev_nodi_realism_v2_R5_2_bounded_scenario_prior_audit.py \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit.py \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit.py \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit.py \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py \
  tests/test_realism_v2_R5_1_interpretation.py \
  tests/test_realism_v2_R5_1_next_stage_plan.py \
  tests/test_realism_v2_R5_full_grid_v2.py \
  tests/test_realism_v2_R5_plan.py \
  tests/test_realism_v2_contract.py

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q

COPYFILE_DISABLE=1 zip -q review_bundles/ev_nodi_realism_v2_r5_2_results_review.zip \
  -@ < R5_2_RESULTS_REVIEW_FILE_LIST.txt
unzip -t review_bundles/ev_nodi_realism_v2_r5_2_results_review.zip

rm -rf /tmp/r5_2_results_review
mkdir -p /tmp/r5_2_results_review
unzip -q review_bundles/ev_nodi_realism_v2_r5_2_results_review.zip \
  -d /tmp/r5_2_results_review
cd /tmp/r5_2_results_review
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit.py \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py \
  tests/test_realism_v2_R5_1_interpretation.py \
  tests/test_realism_v2_R5_1_next_stage_plan.py \
  tests/test_realism_v2_R5_full_grid_v2.py \
  tests/test_realism_v2_R5_plan.py \
  tests/test_realism_v2_contract.py
```

Results:

```text
R5.2 audit tool execution: pass
ruff: All checks passed
R5.2 focused tests: 21 passed in 5.36s
R5.2/R5.1/R5/contract focused suite: 80 passed in 14.31s
full suite: 853 passed in 206.47s
review bundle integrity: No errors detected
review bundle resource fork entries: none
extracted bundle focused suite: 80 passed
```

## Next review target

The only next action supported by this R5.2 result is:

```text
prepare_route_prior_model_revision_plan_only
```

That next plan must remain externally reviewed and plan-only. It must not execute a route-prior revision, authorize R6 planning/execution, promote context routes, redefine main-660, add scenarios/seeds/solver cases/experiments, alter selected-annulus bounds, or emit calibrated/absolute claims.
