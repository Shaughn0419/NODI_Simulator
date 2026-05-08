# EV NODI realism v2 target-alignment self review

## Decision

`PASS_TO_V2_NO_MEASURED_DATA_CLOSURE_ONLY`

The v2 lane is aligned with the current target: a no-measured-data modeling and prior-sensitivity program. It may use deterministic forward models, bounded priors, scenario bundles, posthoc audits, route-prior sensitivity, and artifact-gap registers. It must not start or plan in-v2 bench acquisition, experimental validation, solver export as new evidence, empirical calibration, route promotion, main-660 redefinition, or selected-annulus replacement.

## Corrective changes made

- Reframed the R7 result recommendation from operator-artifact/experimental-validation planning to `prepare_operator_artifact_gap_register_plan_only`.
- Reframed R7.1 output from acquisition-plan preparation to `prepare_operator_artifact_gap_register_plan_only`.
- Reframed R7.2 output from an acquisition runway to `prepare_v2_no_measured_data_closure_only`.
- Renamed the R7.2 plan/config/tool/test surface to `operator_artifact_gap_register`.
- Replaced per-artifact `acquisition_status` / `acquisition_authorized` fields with `gap_status` / `gap_resolution_authorized`.
- Replaced blank sidecar `blank_acquisition_status` with `blank_evidence_status` and made measured blank inputs fail closed for v2.
- Removed positive `prepare_experimental_validation_panel_*` recommendation classes from active R5/R7 code/config paths, replacing them with post-v2 dependency language.

## Current active chain

```text
R7 selected recommendation:
  prepare_operator_artifact_gap_register_plan_only

R7.1 selected recommendation:
  prepare_operator_artifact_gap_register_plan_only

R7.2 selected recommendation:
  prepare_v2_no_measured_data_closure_only
```

Every selected recommendation keeps:

```text
authorizes_execution = false
authorizes_acquisition = false
authorizes_R8 = false
authorizes_experiment = false
authorizes_solver_case = false
authorizes_route_promotion = false
authorizes_main_660_redefinition = false
```

## Residual allowed wording

The strings `operator_artifact_acquisition_started`, `bench_measurement_started`, `experimental_validation_started`, and R8 fields still appear as stop-gates, manifest booleans, and tests. They are retained only as false/blocked guardrails.

The artifact gap register may say a missing artifact would require a post-v2 bench, operator-export, or validation program. That is a dependency statement, not v2 authorization.

## Final boundary

v2 can close as a synthetic-prior result:

```text
main-660 remains governance-locked;
R5.2 weak-reference/context-route warning is explainable by low-dimensional width-family priors;
artifact/operator evidence remains missing and registered as post-v2 dependency gaps;
claims remain relative_with_priors / absolute_blocked.
```

v2 still cannot claim:

```text
calibrated SNR
calibrated event probability
absolute LOD
true EV concentration
biological specificity
route promotion
main-660 redefinition
selected-annulus replacement
experimental validation
bench measurement
solver export as new evidence
```

## Verification

```text
R7/R7.1/R7.2 focused tests: 39 passed
R5.1/R5.2/R5.3 focused tests: 63 passed
R6/R7/contract focused tests: 85 passed
sidecar/R2/R3 focused tests: 44 passed
wide v2/related suite: 376 passed
ruff focused check: passed
```
