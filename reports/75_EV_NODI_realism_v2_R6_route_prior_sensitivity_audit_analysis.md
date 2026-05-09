# EV NODI realism v2 R6 route-prior sensitivity audit analysis

## Decision boundary

This bundle executed only the externally authorized bounded R6 route-prior sensitivity audit:

```text
PASS_TO_BOUNDED_R6_ROUTE_PRIOR_SENSITIVITY_AUDIT_ONLY
```

It does not authorize R7 plan preparation, R7 execution, R5 follow-up expansion, new scenario bundles, stochastic seeds, solver cases, experiments, route promotion, main-660 redefinition, selected-annulus changes, calibrated SNR, calibrated event probability, absolute LOD, true EV concentration, biological specificity, Tsuyama paper-fit continuation, v1 overwrite, or ET2030 direct current-input unlock.

## Scope actually executed

```text
audit_execution_type =
  bounded_existing_R5_artifact_route_prior_sensitivity_audit_only

existing_R5_rows_audited = 14784
candidate_prior_count = 12
derived_candidate_rows_evaluated = 177408
max_R6_derived_candidate_rows = 177408
audit_route_id_count = 33
scenario_bundle_count = 8
stochastic_seed_count = 0
new_case_rows_added = 0
new_scenario_bundles_added = 0
new_stochastic_seeds_added = 0
new_solver_cases_added = 0
new_experiments_started = 0
```

The R6 result directory contains exactly the registered R6 files:

```text
R6_route_prior_sensitivity_manifest.csv
R6_candidate_prior_registry.csv
R6_candidate_prior_sensitivity_matrix.csv
R6_route_prior_factor_by_route.csv
R6_route_family_residual_warning_table.csv
R6_scenario_residual_warning_table.csv
R6_particle_stratum_residual_warning_table.csv
R6_main660_locked_comparator_summary.csv
R6_selected_annulus_and_404_sidecar_guardrail_summary.csv
R6_claim_boundary_guardrail_summary.csv
R6_stop_gate_summary.csv
R6_next_stage_recommendation_matrix.csv
run_manifest.json
R6_route_prior_sensitivity_report.md
```

## Comparator policy

R6 uses the pre-registered comparator policy:

```text
main660_comparator_policy = candidate_adjusted_locked_main_660
secondary_main660_comparator_policy = unadjusted_locked_main_660
locked main-660 routes = 660_800x1400 / 660_800x1500
```

This avoids ambiguity for `width_quad_850` and `width_quad_900`, where locked main-660 itself receives a width prior factor below 1.0.

## Candidate sensitivity result

The candidate registry reports:

```text
nearby_warning_resolved_candidate_count = 3
at_least_two_nearby_low_dimensional_candidates_explain_warning = true
main660_retention_warning_candidate_count = 1
selected_future_recommendation_class =
  prepare_next_stage_plan_for_external_review_only
audit_decision =
  low_dimensional_width_prior_sensitivity_stable_prepare_next_stage_plan_only
```

Candidate outcomes:

```text
width_linear_800                       warning_resolved = false
width_exp1p5_800                       warning_resolved = true
global_width_quadratic_regularization  warning_resolved = true
width_quad_750                         warning_resolved = false
width_quad_850                         warning_resolved = true
width_quad_900                         warning_resolved = true, main retention warning
width_quad_floor025                    warning_resolved = true
width_quad_floor035                    warning_resolved = true
width_quad_floor050                    warning_resolved = true
width_exp2p5_wall_transport            warning_resolved = true
reference_band_penalty                 warning_resolved = false
BFP_alignment_risk                     warning_resolved = false
```

The nearby confirmation candidates that resolve the warning are:

```text
width_exp1p5_800
global_width_quadratic_regularization
width_quad_850
```

`width_quad_900` also resolves the warning but triggers:

```text
main660_score_retention_fraction = 0.7901234567901234
main660_retention_warning = true
```

This is retained as a caution, not as a blocker.

## Interpretation

R6 supports the interpretation that the R5.2 warning is stable under a low-dimensional width-family prior sensitivity lane. It does not prove that the physical prior is exactly `(W / 800)^2`, and it does not calibrate any detector or event probability.

The non-width alternatives are useful diagnostics but do not independently explain the warning:

```text
reference_band_penalty:
  context_routes_above_main_after_candidate = 20
  weak_reference_scenario_rows_above_main_after_candidate = 8

BFP_alignment_risk:
  context_routes_above_main_after_candidate = 10
  weak_reference_scenario_rows_above_main_after_candidate = 8
```

## Guardrails

The R6 manifest and guardrail summaries keep:

```text
R7_plan_preparation_authorized = false
R7_execution_authorized = false
R5_followup_expansion_authorized = false
context_route_promotion_authorized = false
main_660_redefinition_authorized = false
route_specific_manual_prior_multiplier_attempted = false
scenario_specific_per_route_fit_attempted = false
particle_specific_empirical_fit_attempted = false
calibrated_SNR_claim_emitted = false
calibrated_event_probability_claim_emitted = false
```

Claim boundaries remain:

```text
SNR_claim_level = absolute_blocked
event_probability_claim_level = absolute_blocked
p_detect_mapping_claim_level = relative_with_priors
```

Exact forbidden legacy CSV headers remain absent:

```text
detector_SNR
calibrated_detector_SNR
```

## Validation

Local validation performed:

```text
python -m json.tool configs/realism_v2/r6_route_prior_sensitivity_plan.yaml
python tools/one_shot/ev_nodi_realism_v2_R6_route_prior_sensitivity_audit.py
ruff check realism_v2.py tools/one_shot/ev_nodi_realism_v2_R6_route_prior_sensitivity_audit.py tests/test_realism_v2_R6_plan.py tests/test_realism_v2_R6_route_prior_sensitivity_audit.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_realism_v2_R6_plan.py tests/test_realism_v2_R6_route_prior_sensitivity_audit.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_realism_v2_R6_route_prior_sensitivity_audit.py \
  tests/test_realism_v2_R6_plan.py \
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
```

Results:

```text
R6 plan/results focused tests: 19 passed
R6/R5.3/R5.2/R5.1/R5/contract focused suite: 120 passed
full suite: 893 passed in 210.69s
extracted review bundle focused suite: 120 passed in 14.44s
ruff: All checks passed
```
