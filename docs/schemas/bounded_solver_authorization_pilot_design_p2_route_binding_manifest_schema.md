# Bounded Solver Authorization Pilot Design P2 Route Binding Manifest

Schema:

```text
ev_nodi_p3_bounded_solver_authorization_pilot_design_p2_route_binding_manifest_v1
```

Role:

```text
p2_route_universe_binding_no_solver_execution
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
route_promotion_authorized = false
```

The bound source must be the P2 bounded route-universe manifest. The binding is
future solver preflight scope only; it is not solver result evidence and not
route-promotion evidence.
