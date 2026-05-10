# Bounded Solver Authorization Pilot Design Route Subset Manifest

Schema:

```text
ev_nodi_p3_bounded_solver_authorization_pilot_design_route_subset_manifest_v1
```

Role:

```text
minimal_pilot_route_subset_design_no_solver_execution
```

Required boundary declarations:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
p1_surrogate_risk_role_preserved = true
p2_readiness_scope_preserved = true
physical_solver_execution_authorized = false
measured_data_ingest_authorized = false
solver_output_generated = false
raw_magnitude_final_gate_allowed = false
route_promotion_authorized = false
```

The route subset source must be:

```text
results/post_v2_bounded_physical_solver_readiness/bounded_physical_solver_readiness_route_universe_manifest.json
```

Selected route rows may carry only bounded identifiers, route roles, comparison
strata, P0 audit decision fields, P1 full-wave surrogate-risk labels, and
pairwise flags. Raw proxy fields are not allowed.
