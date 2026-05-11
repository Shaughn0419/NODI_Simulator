# Bounded Solver Dry-Run Preflight P3 Binding Manifest

Schema:

```text
ev_nodi_p4_bounded_solver_dry_run_preflight_p3_binding_manifest_v1
```

Role:

```text
p3_pilot_design_binding_no_solver_execution
```

Required declarations:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
p1_surrogate_risk_role_preserved = true
p2_readiness_scope_preserved = true
p3_pilot_design_scope_preserved = true
physical_solver_execution_authorized = false
measured_data_ingest_authorized = false
calibration_data_ingest_authorized = false
new_mesh_generation_authorized = false
operator_export_generation_authorized = false
solver_output_generated = false
route_promotion_authorized = false
```

## Artifact-field alignment note

These fields are present in the paired artifact payload and are checked by schema drift audit:

- `p3_artifact_manifest_sha256`
- `p3_route_subset_manifest_sha256`
- `p3_schema_manifest_sha256`
- `selected_route_ids`

