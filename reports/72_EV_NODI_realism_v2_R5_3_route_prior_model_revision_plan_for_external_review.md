# EV/NODI realism v2 R5.3 route-prior model revision plan

## Decision consumed

External gate consumed:

```text
PASS_R5_2_RESULTS_PREPARE_ROUTE_PRIOR_MODEL_REVISION_PLAN_ONLY
```

This artifact prepares a route-prior model revision plan only. It does not execute a route-prior revision, start R6 planning, run R6, expand R5, promote routes, redefine main-660, alter selected-annulus bounds, add scenarios/seeds/solver cases/experiments, or emit calibrated/absolute claims.

## Review cadence

The prior fine-grained external review cadence was necessary while the project was crossing execution and authorization boundaries: R4 numerical validation, route-model audit, revised R4, R4.2, R5, R5.1, and R5.2 each changed what could be run next.

From this point, the work is plan-only and interpretive until a future external gate authorizes execution. This plan therefore consolidates the route-prior decomposition design, allowed candidate revision families, forbidden fit families, future output schema, stop gates, and pass/fail criteria into one larger review package. The next external review should decide whether this whole package is tight enough to authorize a bounded R5.3 route-prior model revision audit. It should not split the plan into many small plan-only reviews unless a blocker is found.

## Scope boundary

Authorized now:

```text
prepare route-prior model revision plan only
```

Still not authorized:

```text
route-prior model revision execution
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

## R5.2 carryforward

The plan consumes the accepted R5.2 result:

```text
R5_2_bounded_scenario_prior_audit_run = true
existing_R5_rows_audited = 14784
audit_route_id_count = 33
scenario_bundle_count = 8
stochastic_seed_count = 0
new_case_rows_added = 0
selected_future_recommendation_class =
  prepare_route_prior_model_revision_plan_only
audit_decision =
  systematic_weak_reference_and_context_prior_warning_blocks_R6_plan
```

The systematic warning is preserved:

```text
weak_reference_control exceeds main_660 in 8 / 8 existing R5 scenario bundles
20 / 20 above-main context routes exceed main_660 under all 8 existing R5 scenario bundles
```

Core means:

```text
main_660 mean relative-prior score = 0.126095409614
weak-reference mean relative-prior score = 0.152257463311
above-main context family mean relative-prior score = 0.151918689204
top context warning route = 660_500x1500
top context warning ratio vs main_660 = 1.557516
```

This is not a promotion signal. It is a prior-model warning that must be decomposed before R6 planning can be considered.

## Plan design

The R5.3 plan is:

```text
plan_execution_type = plan_only_no_recompute_no_revision
future_revision_execution_type_if_reviewed =
  bounded_existing_R5_artifact_prior_model_audit_only
uses_existing_R5_artifacts_only = true
max_existing_R5_source_rows_if_future_reviewed = 14784
route_id_count = 33
source_particles_per_route = 56
scenario_bundle_count = 8
stochastic_seed_count = 0
new_case_rows_authorized = 0
new_scenario_bundle_authorized = false
new_stochastic_seed_authorized = false
new_solver_case_authorized = false
new_experiment_authorized = false
```

It keeps the same 33-route R5.2 audit set:

```text
2 locked main-660 comparators
1 weak-reference control
1 optional 660 robustness probe
3 medium/shortwave controls
6 selected-annulus sidecars
20 above-main context warning routes
```

## Required decomposition

Any future bounded R5.3 execution must decompose the relative-prior score into these terms:

```text
reference_prior_term
BFP_slit_pinhole_prior_term
near_wall_PEG_transport_prior_term
detector_blank_prior_term
thermal_404_sidecar_exclusion_term
route_width_depth_prior_term
particle_size_stratum_term
scenario_bundle_sensitivity_term
```

The central question is not "which route wins." It is: which low-dimensional prior term explains why weak-reference/control and narrow/deep context routes systematically exceed locked main-660 under the existing R5 priors?

## Allowed candidate revision families

Allowed for future review only:

```text
diagnostic_score_term_decomposition_only
global_width_depth_regularization_family
weak_reference_control_artifact_flag_family
wall_transport_prior_risk_family
BFP_slit_operator_prior_family
detector_blank_prior_risk_family
scenario_bundle_sensitivity_reweighting_diagnostic
```

These are family-level or diagnostic prior changes. They do not authorize route promotion or main-660 redefinition.

## Forbidden fit families

Forbidden:

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

These would convert a prior-model audit into a posthoc result-fitting layer, so they are blocked.

## Future pass/fail criteria

If a future external review authorizes R5.3 execution, the result must still satisfy:

```text
no_route_promotion = true
no_main_660_redefinition = true
no_selected_annulus_replacement = true
no_calibrated_or_absolute_claim = true
weak_reference_control_explained_or_remains_blocking = true
all_20_context_warning_routes_exhaustively_reported = true
candidate_revision_must_be_global_or_family_level_not_route_specific = true
R6_plan_remains_blocked_until_separate_review = true
```

If weak-reference/control and context-route warnings cannot be explained by a low-dimensional prior family, R6 remains blocked and the project should move to route-governance or experimental-panel planning instead of route promotion.

## Required future outputs

If future external review authorizes bounded R5.3 execution, the output set must be exactly:

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

No R6, solver, stochastic, experiment, route-promotion, selected-annulus-change, or calibrated-claim output is authorized by this plan.

## Stop gates

The plan includes hard stop gates for:

```text
route-prior execution without external authorization
R6 planning or execution
R5 follow-up expansion
source row or route-set expansion
new scenarios, seeds, solver cases, or experiments
v1 overwrite
Tsuyama paper-fit continuation
selected-annulus changes or replacement
context-route promotion
main-660 redefinition
route-specific sign flips or prior multipliers
scenario-specific per-route fits
particle-specific empirical fits
calibrated / absolute / biological claims
ET2030 direct current-input unlock
thermal sidecar increasing NODI score
finite-zero-event blank safety claim
legacy detector_SNR / calibrated_detector_SNR output headers
```

## Claim boundary

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

## Provenance

The plan freezes checksums for the R5.2 audit manifest, traceability table, context-route audit, weak-reference audit, scenario contribution audit, route-family audit, main-660 comparator, sidecar guardrail, claim guardrail, decision table, next-stage matrix, and R5.2 run manifest.

## Verification

Commands run:

```text
python -m json.tool configs/realism_v2/r5_3_route_prior_model_revision_plan.yaml

python - <<'PY'
import realism_v2 as rv2
p = rv2.validate_R5_3_route_prior_model_revision_plan()
print(p["schema_version"])
print(p["stage"])
print(p["revision_plan_design"]["max_existing_R5_source_rows_if_future_reviewed"])
PY

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_realism_v2_R5_3_route_prior_model_revision_plan.py

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
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
  review_bundles/ev_nodi_realism_v2_r5_3_route_prior_model_revision_plan_review.zip \
  -@ < R5_3_ROUTE_PRIOR_MODEL_REVISION_PLAN_REVIEW_FILE_LIST.txt
unzip -t \
  review_bundles/ev_nodi_realism_v2_r5_3_route_prior_model_revision_plan_review.zip

rm -rf /tmp/r5_3_plan_review
mkdir -p /tmp/r5_3_plan_review
unzip -q \
  review_bundles/ev_nodi_realism_v2_r5_3_route_prior_model_revision_plan_review.zip \
  -d /tmp/r5_3_plan_review
cd /tmp/r5_3_plan_review
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_realism_v2_R5_3_route_prior_model_revision_plan.py \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit.py \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py \
  tests/test_realism_v2_R5_1_interpretation.py \
  tests/test_realism_v2_R5_1_next_stage_plan.py \
  tests/test_realism_v2_R5_full_grid_v2.py \
  tests/test_realism_v2_R5_plan.py \
  tests/test_realism_v2_contract.py

ruff check realism_v2.py \
  tests/test_realism_v2_R5_3_route_prior_model_revision_plan.py
```

Results:

```text
JSON-compatible config: OK
validator: R5_3_route_prior_model_revision_plan_v1 / plan-only / 14784 rows
R5.3 focused tests: 12 passed in 1.08s
R5.3/R5.2/R5.1/R5/contract focused suite: 92 passed in 13.91s
full suite: 865 passed in 205.41s
review bundle integrity: No errors detected
review bundle resource fork entries: none
extracted bundle focused suite: 92 passed
ruff: All checks passed
```

## Requested external-review decision

The strongest passing decision that should be available for this plan is:

```text
PASS_TO_BOUNDED_ROUTE_PRIOR_MODEL_REVISION_AUDIT_ONLY
```

That would authorize only bounded R5.3 route-prior model revision audit execution, not R6 planning/execution, route promotion, main-660 redefinition, scenario expansion, or calibrated/absolute claims.
