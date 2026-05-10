# Bounded Solver Authorization Gate Artifact Manifest

Schema:

```text
ev_nodi_p5_bounded_solver_authorization_gate_artifact_manifest_v1
```

Role:

```text
authorization_gate_artifact_manifest_no_solver_execution
```

Every artifact must declare:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
p1_surrogate_risk_role_preserved = true
p2_readiness_scope_preserved = true
p3_pilot_design_scope_preserved = true
p4_dry_run_preflight_scope_preserved = true
physical_solver_execution_authorized = false
measured_data_ingest_authorized = false
calibration_data_ingest_authorized = false
new_mesh_generation_authorized = false
operator_export_generation_authorized = false
solver_output_generated = false
route_promotion_authorized = false
```
