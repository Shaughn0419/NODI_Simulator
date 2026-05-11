# Bounded Solver Authorization Pilot Design Schema Manifest

Schema:

```text
ev_nodi_p3_bounded_solver_authorization_pilot_design_schema_manifest_v1
```

Role:

```text
pilot_design_schema_manifest_no_solver_execution
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
```

The schema manifest records the solver input manifest schema, the mesh /
boundary / unit preflight schema, and the output schema placeholder for the
single P3 lane:

```text
full_wave_green_tensor_spot_check_minimal_pilot_design
```

The input schema must bind the P2 route-universe manifest. The preflight schema
must keep mesh generation unauthorized. The output schema placeholder is not
solver output and must keep raw magnitude out of final gates.

## Artifact-field alignment note

These fields are present in the paired artifact payload and are checked by schema drift audit:

- `mesh_boundary_unit_preflight_schema`
- `output_schema_placeholder`
- `rank_pairwise_interpretability_requirement`
- `solver_input_manifest_schema`

