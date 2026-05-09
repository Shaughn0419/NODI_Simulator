# EV NODI realism v2 R7 route-prior mechanistic decomposition audit analysis

## Decision

`PASS_R7_RESULTS_PREPARE_OPERATOR_ARTIFACT_GAP_REGISTER_PLAN_ONLY`

The R7 bounded mechanistic decomposition audit is internally consistent and guardrailed enough to continue, but only to a plan-only next stage that defines no-measured-data operator artifact gaps. This does not authorize R8 planning or execution, experiments, new scenarios, new stochastic seeds, solver cases, route promotion, main-660 redefinition, selected-annulus changes, calibrated SNR, calibrated event probability, absolute LOD, true EV concentration, biological specificity, Tsuyama paper-fit continuation, v1 overwrite, or ET2030 direct current-input unlock.

## Blocking findings

None.

The R7 outputs stay inside the reviewed bounded posthoc scope and preserve the route-governance and claim boundaries.

## Scope checks

R7 execution remained bounded:

```text
R7_route_prior_mechanistic_decomposition_audit_run = true
audit_execution_type = bounded_existing_R5_artifact_route_prior_mechanistic_decomposition_audit_only
existing_R5_rows_interpreted = 14784
mechanistic_candidate_count = 6
max_mechanistic_candidate_count = 12
derived_mechanistic_candidate_rows_evaluated = 0
max_R7_derived_candidate_rows = 177408
audit_route_id_count = 33
scenario_bundle_count = 8
stochastic_seed_count = 0
new_case_rows_added = 0
new_scenario_bundles_added = 0
new_stochastic_seeds_added = 0
new_solver_cases_added = 0
new_experiments_started = 0
```

`derived_mechanistic_candidate_rows_evaluated = 0` is intentional. R7 did not produce a new score matrix; it decomposed the R6 width-family hypothesis into executable mechanism proxies, physical-operator gaps, and residual-warning tables.

## Output set

The R7 result directory contains exactly the planned 15 files:

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

No R8, full-grid, solver, stochastic, experiment, route-promotion, selected-annulus-change, or calibrated-claim artifact was generated.

## Scientific interpretation

R6 showed that a stable width-family prior band can explain the R5.2 weak-reference and narrow/deep context-route warning. R7 narrows that statement:

```text
accepted_width_prior_band_candidate_count = 3
executable_existing_artifact_mechanistic_candidate_count = 2
physical_operator_artifact_gap_count = 3
particle_stratum_residual_warning_count = 50
selected_future_recommendation_class =
  prepare_operator_artifact_gap_register_plan_only
```

The two mechanism families executable from existing artifacts are:

```text
clearance_wall_PEG_transport_lowdim
transport_survival_clogging_lowdim
```

They can be treated as existing-artifact mechanistic proxies because width/depth are derivable from the frozen route IDs and particle/scenario fields already exist. They are still relative-prior mechanisms, not calibrated physical laws.

The unresolved physical-operator gaps are:

```text
reference_operating_band_physical_columns_only
BFP_slit_ROI_alignment_physical_columns_only
fabrication_metrology_margin_lowdim
```

These must not be replaced by score-derived penalties. R7 explicitly keeps `source_v1_relative_score` out of physical-prior inputs and marks missing physical/operator fields as not executable.

## Residual warnings

Particle-stratum residuals remain warning-only:

```text
gold_anchor residual rows = 917
gold_anchor mean positive residual delta = 0.09800892982063654
gold_anchor max positive residual delta = 0.42205802007311577

EV_like residual rows = 840
EV_like mean positive residual delta = 0.10813078311720253
EV_like max positive residual delta = 0.4282389106981157
```

This does not block R7, because R7 was not authorized to fit particle strata. It does mean the next plan must keep particle residuals as evidence requirements or diagnostics, not as particle-specific empirical correction targets.

## Governance and claims

The stop gates remain closed:

```text
R8_plan_preparation_authorized = false
R8_execution_authorized = false
new_experiment_authorized = false
R5_followup_expansion_authorized = false
R6_followup_expansion_authorized = false
context_route_promotion_authorized = false
main_660_redefinition_authorized = false
route_specific_manual_prior_multiplier_attempted = false
scenario_specific_per_route_fit_attempted = false
particle_specific_empirical_fit_attempted = false
score_derived_physical_prior_attempted = false
```

Claim boundaries remain:

```text
SNR_claim_level = absolute_blocked
event_probability_claim_level = absolute_blocked
p_detect_mapping_claim_level = relative_with_priors
calibrated_SNR_claim_emitted = false
calibrated_event_probability_claim_emitted = false
```

Exact legacy CSV headers remain absent:

```text
detector_SNR
calibrated_detector_SNR
```

## Next action

The next action is:

```text
prepare_operator_artifact_gap_register_plan_only
```

That plan should define required evidence for:

```text
reference-field operating band / saturation / noise margin
BFP lobe / slit / ROI alignment operator
fabrication and metrology margin
wall / PEG / transport proxy validation
particle-stratum residual interpretation
optional 660_900x1400 governance diagnostic
```

It must remain plan-only. It may specify artifacts and validation acceptance criteria, but it must not start experiments, execute solver cases, add scenario bundles or stochastic seeds, promote context routes, redefine main-660, or emit calibrated claims.

## Verification

Focused R7 verification:

```text
21 passed in 1.18s
```

R7/R6/R5 focused context suite:

```text
141 passed in 16.84s
```

Static check:

```text
ruff check realism_v2.py \
  tools/one_shot/ev_nodi_realism_v2_R7_route_prior_mechanistic_decomposition_audit.py \
  tests/test_realism_v2_R7_route_prior_mechanistic_decomposition_audit.py \
  tests/test_realism_v2_R7_plan.py

All checks passed
```

Full test suite:

```text
914 passed in 207.03s
```
