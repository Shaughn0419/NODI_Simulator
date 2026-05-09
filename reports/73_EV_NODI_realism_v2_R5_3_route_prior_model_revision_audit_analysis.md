# EV/NODI realism v2 R5.3 route-prior model revision audit analysis

## Decision consumed

External gate consumed:

```text
PASS_TO_BOUNDED_ROUTE_PRIOR_MODEL_REVISION_AUDIT_ONLY
```

This run executes only the bounded, existing-R5-artifact R5.3 route-prior model revision audit described in the reviewed R5.3 plan.

## Scope boundary

Executed:

```text
R5.3 route-prior model revision audit only
existing R5/R5.2 artifacts only
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
route-specific manual prior multipliers
scenario-specific per-route fits
particle-specific empirical fits
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

The R5.3 audit result directory is:

```text
results/ev_nodi_realism_v2_R5_3_route_prior_model_revision_audit/
```

It contains exactly the 13 pre-registered outputs:

```text
R5_3_route_prior_revision_manifest.csv
R5_3_score_term_decomposition.csv
R5_3_context_route_prior_driver_table.csv
R5_3_weak_reference_control_prior_driver_table.csv
R5_3_candidate_prior_revision_registry.csv
R5_3_forbidden_fit_guardrail_summary.csv
R5_3_main660_locked_comparator_after_prior_model_summary.csv
R5_3_selected_annulus_and_404_sidecar_guardrail_summary.csv
R5_3_claim_boundary_guardrail_summary.csv
R5_3_route_prior_revision_decision_table.csv
R5_3_next_stage_recommendation_matrix.csv
run_manifest.json
R5_3_route_prior_model_revision_report.md
```

No R6, full-grid, solver, stochastic, experiment, route-promotion, selected-annulus-change, or calibrated-claim artifact was created.

## Audit finding

R5.3 decomposed the R5.2 systematic warning and evaluated bounded family-level candidate priors. The selected diagnostic candidate is:

```text
selected_candidate_prior_id = global_width_quadratic_regularization
selected_candidate_prior_family = global_width_depth_regularization_family
selected_candidate_dof_count = 1
```

This candidate applies a family-level width-below-800 nm quadratic risk factor. It is not route-specific, not scenario-specific, not particle-specific, and does not promote any route or redefine main-660.

The selected candidate explains the R5.2 warning in the bounded audit:

```text
weak_reference_delta_explained_fraction = 1.0
context_family_delta_explained_fraction = 1.0
context_routes_above_main_after_candidate = 0
```

Core values:

```text
old main_660 mean = 0.126095409614
old weak-reference mean = 0.152257463311
candidate weak-reference mean = 0.116572120348
old above-main context family mean = 0.151918689204
candidate above-main context family mean = 0.074788140350
```

The candidate interpretation is narrow: a low-dimensional width/depth prior family can explain the weak-reference and context-route warnings. It is not a calibrated model and does not authorize route promotion.

## Decision result

R5.3 selected:

```text
selected_future_recommendation_class =
  prepare_R6_plan_for_external_review_only
audit_decision =
  low_dimensional_width_depth_prior_candidate_explains_R5_2_warning_R6_plan_review_only
```

This is a future planning recommendation only. The R5.3 result does not authorize R6 plan preparation, R6 execution, route promotion, main-660 redefinition, or any calibrated/absolute claim.

## Candidate registry

The audit registry includes eight candidates:

```text
null_decomposition_only
global_width_linear_regularization
global_width_quadratic_regularization
wall_transport_width_depth_regularization
weak_reference_control_artifact_flag
BFP_slit_operator_prior_diagnostic
detector_blank_prior_risk_diagnostic
scenario_bundle_sensitivity_reweighting_diagnostic
```

The selected candidate is the simpler one-degree family-level width quadratic candidate. The width-depth candidate also resolves the warning but is not selected because it adds another degree of freedom.

Every candidate row keeps:

```text
uses_route_specific_multiplier = false
uses_scenario_specific_per_route_fit = false
uses_particle_specific_empirical_fit = false
changes_main_660_definition = false
authorizes_route_promotion = false
changes_selected_annulus = false
scenario_weight_change_authorized = false
claim_level = relative_with_priors
```

## Forbidden fit guardrails

The forbidden fit guardrail summary marks all forbidden families as not attempted:

```text
route_specific_manual_multiplier
context_route_promotion_by_prior_revision
main_660_redefinition_by_prior_revision
selected_annulus_replaces_all_crossing
scenario_specific_per_route_fit
particle_specific_empirical_fit
calibrated_SNR_or_probability_fit
thermal_404_bonus_term
```

## Main-660 and route governance

Main-660 remains locked to:

```text
660_800x1400
660_800x1500
```

The output records:

```text
main_660_route_role_locked = true
main_660_redefinition_authorized = false
route_promotion_authorized = false
```

All 20 context warning routes remain warning rows, not promotion candidates.

## Sidecar and selected-annulus guardrails

The selected-annulus and 404 sidecar output records:

```text
selected_annulus_replaces_all_crossing_ranking = false
selected_annulus_bound_change_authorized = false
thermal_sidecar_used_to_increase_NODI_score = false
```

These rows remain diagnostic/sidecar evidence only.

## Claim boundary

R5.3 keeps:

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

Exact legacy CSV headers are absent from R5.3 outputs:

```text
detector_SNR
calibrated_detector_SNR
```

Guardrail field names containing those strings are stop-gate indicators, not legacy output claim columns.

## Manifest guardrails

The R5.3 run manifest records:

```text
run_id = EV_NODI_realism_v2_R5_3_route_prior_model_revision_audit
R5_3_route_prior_model_revision_audit_run = true
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
route_specific_manual_prior_multipliers_authorized = false
scenario_specific_per_route_fit_authorized = false
particle_specific_empirical_fit_authorized = false
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
python tools/one_shot/ev_nodi_realism_v2_R5_3_route_prior_model_revision_audit.py

ruff check realism_v2.py \
  tools/one_shot/ev_nodi_realism_v2_R5_3_route_prior_model_revision_audit.py \
  tests/test_realism_v2_R5_3_route_prior_model_revision_audit.py \
  tests/test_realism_v2_R5_3_route_prior_model_revision_plan.py

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_realism_v2_R5_3_route_prior_model_revision_audit.py \
  tests/test_realism_v2_R5_3_route_prior_model_revision_plan.py

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_realism_v2_R5_3_route_prior_model_revision_audit.py \
  tests/test_realism_v2_R5_3_route_prior_model_revision_plan.py \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit.py \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py \
  tests/test_realism_v2_R5_1_interpretation.py \
  tests/test_realism_v2_R5_1_next_stage_plan.py \
  tests/test_realism_v2_R5_full_grid_v2.py \
  tests/test_realism_v2_R5_plan.py \
  tests/test_realism_v2_contract.py

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q

COPYFILE_DISABLE=1 zip -q \
  review_bundles/ev_nodi_realism_v2_r5_3_results_review.zip \
  -@ < R5_3_RESULTS_REVIEW_FILE_LIST.txt
unzip -t review_bundles/ev_nodi_realism_v2_r5_3_results_review.zip

rm -rf /tmp/r5_3_results_review
mkdir -p /tmp/r5_3_results_review
unzip -q review_bundles/ev_nodi_realism_v2_r5_3_results_review.zip \
  -d /tmp/r5_3_results_review
cd /tmp/r5_3_results_review
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_realism_v2_R5_3_route_prior_model_revision_audit.py \
  tests/test_realism_v2_R5_3_route_prior_model_revision_plan.py \
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
R5.3 audit tool execution: pass
ruff: All checks passed
R5.3 focused tests: 21 passed in 1.84s
R5.3/R5.2/R5.1/R5/contract focused suite: 101 passed in 13.99s
full suite: 874 passed in 206.24s
review bundle integrity: No errors detected
review bundle resource fork entries: none
extracted bundle focused suite: 101 passed
```

## Next review target

The only next action supported by this R5.3 result is:

```text
prepare_R6_plan_for_external_review_only
```

That next plan must remain externally reviewed and plan-only. It must carry the selected one-degree width/depth prior candidate as a reviewed prior-model assumption, not as calibrated experimental truth. It must not execute R6, promote context routes, redefine main-660, add new scenarios/seeds/solver cases/experiments, alter selected-annulus bounds, or emit calibrated/absolute claims.
