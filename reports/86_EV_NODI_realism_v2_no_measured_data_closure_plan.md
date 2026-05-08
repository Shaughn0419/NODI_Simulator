# EV/NODI realism v2 no-measured-data closure plan

## Decision

`PREPARE_V2_NO_MEASURED_DATA_CLOSURE_ONLY`

This plan closes realism v2 as an instrument-aware realism simulation supplement:
it adds reality-biased instrument, route, blank, sidecar, and governance
constraints to the original engineering logic and baseline simulation result
lanes. It is still no-measured-data work. It does not authorize
operator-artifact acquisition, bench measurement, experimental validation, R8
planning, R8 execution, new scenarios, stochastic seeds, solver cases,
experiments, route promotion, main-660 redefinition, selected-annulus changes,
calibrated SNR, calibrated event probability, absolute LOD, true EV
concentration, or biological specificity.

## Carry-Forward

R7.2 registered the missing physical/operator artifacts as post-v2 dependencies
and selected:

```text
prepare_v2_no_measured_data_closure_only
```

The closure therefore freezes the current evidence boundary instead of starting
dependency resolution. R6 remains an explanatory width-family prior sensitivity
result, not a calibrated physical law. R7/R7.1/R7.2 define mechanistic and
operator-artifact gaps; they do not resolve those gaps inside v2.

## Closure Outputs

The closure generation may write only:

```text
v2_no_measured_data_closure_manifest.csv
v2_final_claim_boundary_summary.csv
v2_route_governance_closure_summary.csv
v2_artifact_gap_closure_register.csv
v2_forbidden_scope_guardrail_summary.csv
v2_post_v2_dependency_backlog.csv
v2_closure_decision_table.csv
run_manifest.json
v2_no_measured_data_closure_report.md
```

## Final Boundary

The only valid closure decision is:

```text
V2_CLOSED_NO_MEASURED_DATA_SYNTHETIC_PRIOR_MODEL_ONLY
```

That decision means v2 can be used to make the earlier engineering and
simulation conclusions more credible under explicit realism constraints. It
cannot be used as an experimental validation, calibrated detector model,
absolute detection model, or route-governance promotion result.
