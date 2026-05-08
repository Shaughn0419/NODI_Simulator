# EV NODI realism v2 R7 route-prior mechanistic decomposition plan

## Decision requested

This bundle requests external review for plan-only next-stage work after the accepted R6 result:

```text
PASS_R6_RESULTS_PREPARE_NEXT_STAGE_PLAN_ONLY
```

The maximum passing decision for this review is:

```text
PASS_TO_BOUNDED_R7_ROUTE_PRIOR_MECHANISTIC_DECOMPOSITION_AUDIT_ONLY
```

This plan does not authorize R7 execution, route promotion, main-660 redefinition, R5/R6 follow-up expansion, new scenario bundles, stochastic seeds, solver cases, experiments, selected-annulus changes, calibrated SNR, calibrated event probability, absolute LOD, true EV concentration, biological specificity, Tsuyama paper-fit continuation, v1 overwrite, or ET2030 direct current-input unlock.

## Plan-only state

The reviewed artifact is:

```text
configs/realism_v2/r7_route_prior_mechanistic_decomposition_plan.yaml
```

It declares:

```text
schema_version = R7_route_prior_mechanistic_decomposition_plan_v1
stage = R7_route_prior_mechanistic_decomposition_plan_only
prior_gate = PASS_R6_RESULTS_PREPARE_NEXT_STAGE_PLAN_ONLY
selected_next_stage_lane = R7_route_prior_mechanistic_decomposition_plan_only
R7_execution_authorized = false
route_prior_mechanistic_decomposition_execution_authorized = false
external_review_required_before_R7_execution = true
```

The future output directory is intentionally absent:

```text
results/ev_nodi_realism_v2_R7_route_prior_mechanistic_decomposition_audit/
```

## R6 carry-forward

R6 is treated as a bounded sensitivity audit result, not as a calibrated physical law. The plan carries forward:

```text
R6_route_prior_sensitivity_audit_run = true
existing_R5_rows_audited = 14,784
candidate_prior_count = 12
derived_candidate_rows_evaluated = 177,408
audit_route_id_count = 33
scenario_bundle_count = 8
stochastic_seed_count = 0
main660_comparator_policy = candidate_adjusted_locked_main_660
nearby_warning_resolved_candidate_count = 3
at_least_two_nearby_low_dimensional_candidates_explain_warning = true
selected_future_recommendation_class = prepare_next_stage_plan_for_external_review_only
```

The accepted explanatory width-prior band is frozen as:

```text
width_pivot_nm = 800-850
width_exponent = 1.5-2.0
main660_retention_fraction_min = 0.85
context_routes_above_main_after_candidate = 0
weak_reference_scenario_rows_above_main_after_candidate = 0
optional_900_cannot_redefine_main = true
```

Accepted explanatory candidates:

```text
width_exp1p5_800
global_width_quadratic_regularization
width_quad_850
```

Too-weak candidates:

```text
width_linear_800
width_quad_750
```

Over-severe caution:

```text
width_quad_900
main660_score_retention_fraction = 0.7901234567901234
optional_900_vs_candidate_adjusted_main_delta = 0.023410526007639376
```

The old R6 plan nearby-example ambiguity is explicitly corrected: `width_quad_floor035` is not counted as a nearby confirmation candidate because its floor delta exceeds the registered nearby threshold.

## Scientific purpose

R6 supports this hypothesis:

```text
R5.2 weak-reference and narrow/deep context-route warnings are explainable by a stable low-dimensional width-family prior.
```

R6 does not prove:

```text
width^p is a calibrated physical law
main-660 is experimentally validated
context routes are demoted or promoted
optional 660 / 900x1400 can redefine main-660
absolute p_detect, SNR, LOD, or EV concentration
```

The R7 plan asks only for a future bounded posthoc audit that decomposes the compressed R6 width-family prior into physically interpretable low-dimensional mechanism candidates.

## Mechanistic families

Allowed future mechanism families are:

```text
clearance_wall_PEG_transport_family
transport_survival_clogging_family
reference_operating_band_family
BFP_slit_ROI_alignment_family
fabrication_metrology_margin_family
particle_stratum_residual_interpretation_only
```

Every candidate must stay global/family-level or diagnostic-only. The plan forbids:

```text
route_specific_manual_multiplier
context_route_promotion_by_prior_revision
main_660_redefinition_by_prior_revision
selected_annulus_replaces_all_crossing
scenario_specific_per_route_fit
particle_specific_empirical_fit
score_derived_physical_prior
calibrated_SNR_or_probability_fit
thermal_404_bonus_term
```

The future audit remains capped at:

```text
14,784 existing R5/R6 source rows
12 maximum mechanistic candidates
177,408 maximum derived candidate-row evaluations
33 route IDs
8 existing R5 scenario bundles
0 stochastic seeds
0 new solver cases
0 new experiments
```

## Non-width prior policy

R6 showed that `reference_band_penalty` and `BFP_alignment_risk` do not independently explain the warning. The R7 plan also tightens input policy:

```text
source_v1_relative_score_as_physical_prior_authorized = false
outcome_proximal_candidate_ids = [reference_band_penalty]
reference_band_next_version_requires_physical_columns = true
BFP_alignment_next_version_requires_operator_columns = true
```

If physical/operator fields are missing from frozen artifacts, the candidate must be marked `not_executable_without_new_operator_artifact` rather than replaced with score-derived reweighting.

## Particle-stratum residuals

R6 resolves route/scenario warnings but leaves particle-stratum residual structure. R7 must report this structure without fitting it away:

```text
particle_stratum_residual_is_warning_not_fit_target = true
particle_specific_empirical_fit_authorized = false
```

Required particle-residual outputs:

```text
R7_particle_stratum_residual_top_routes.csv
R7_particle_stratum_residual_by_family.csv
R7_gold_anchor_vs_EV_residual_comparison.csv
```

## Optional 900 governance diagnostic

The optional 660 / 900x1400 route remains a robustness probe only:

```text
route_id = 660_900x1400
optional_900_role = optional_robustness_probe
main_660_redefinition_authorized = false
route_promotion_authorized = false
```

The future audit must report both candidate-adjusted and unadjusted main comparator diagnostics for optional 900 behavior.

## Required future outputs

If and only if a future external review authorizes R7 execution, the output set is limited to:

```text
R7_mechanistic_decomposition_manifest.csv
R7_candidate_mechanistic_prior_registry.csv
R7_accepted_width_prior_band_summary.csv
R7_width_quad_900_over_severe_caution_summary.csv
R7_mechanistic_prior_factor_schema.csv
R7_particle_stratum_residual_top_routes.csv
R7_particle_stratum_residual_by_family.csv
R7_gold_anchor_vs_EV_residual_comparison.csv
R7_optional_900_governance_diagnostic.csv
R7_non_width_prior_input_requirement_summary.csv
R7_claim_boundary_guardrail_summary.csv
R7_stop_gate_summary.csv
R7_next_stage_recommendation_matrix.csv
run_manifest.json
R7_route_prior_mechanistic_decomposition_report.md
```

No full-grid, solver, stochastic, experiment, route-promotion, selected-annulus-change, or calibrated-claim artifact is authorized.

## Pass/fail criteria for a future R7 result review

A future R7 result can support another planning step only if:

```text
at_least_two_low_dimensional_mechanistic_priors_explain_warning = true
main660_retention_fraction >= 0.85
optional_900_does_not_redefine_main = true
particle_residuals_reported_but_not_fit_away = true
no route-specific / scenario-specific / particle-specific fit
selected_annulus_parallel_lens_only = true
claim_boundary_absolute_blocked = true
```

It must stop or redirect to route governance if reasonable physical priors leave context routes systematically above main-660, or if only forbidden fits resolve the warning.

## Claim boundaries

Claim levels remain:

```text
SNR_claim_level = absolute_blocked
event_probability_claim_level = absolute_blocked
p_detect_mapping_claim_level = relative_with_priors
```

Still forbidden:

```text
calibrated SNR
calibrated event probability
absolute LOD
true EV concentration
biological specificity
legacy detector_SNR output header
legacy calibrated_detector_SNR output header
```

## Provenance freeze

The plan freezes these R6 artifacts:

```text
R6_route_prior_sensitivity_manifest.csv
R6_candidate_prior_registry.csv
R6_candidate_prior_sensitivity_matrix.csv
R6_route_prior_factor_by_route.csv
R6_route_family_residual_warning_table.csv
R6_scenario_residual_warning_table.csv
R6_particle_stratum_residual_warning_table.csv
R6_main660_locked_comparator_summary.csv
R6_claim_boundary_guardrail_summary.csv
R6_stop_gate_summary.csv
R6_next_stage_recommendation_matrix.csv
run_manifest.json
```

The focused validator recomputes these checksums and fails closed on source drift.

## Validation

Local validation commands:

```bash
python -m json.tool configs/realism_v2/r7_route_prior_mechanistic_decomposition_plan.yaml

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_realism_v2_R7_plan.py
```

Expected focused result:

```text
13 passed
```
