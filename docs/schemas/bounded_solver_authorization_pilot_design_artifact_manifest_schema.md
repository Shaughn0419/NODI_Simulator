# Bounded Solver Authorization Pilot Design Artifact Manifest

Schema:

```text
ev_nodi_p3_bounded_solver_authorization_pilot_design_artifact_manifest_v1
```

Role:

```text
pilot_design_artifact_manifest_no_solver_execution
```

Required artifact fields:

```text
artifact_id
artifact_role
path
status
claim_level
calibrated_claim_allowed
p0_release_conclusion_changed
p1_surrogate_risk_role_preserved
p2_readiness_scope_preserved
physical_solver_execution_authorized
measured_data_ingest_authorized
solver_output_generated
```

Every artifact must declare:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
p1_surrogate_risk_role_preserved = true
p2_readiness_scope_preserved = true
physical_solver_execution_authorized = false
measured_data_ingest_authorized = false
solver_output_generated = false
```

The artifact manifest is a hash and boundary inventory. It does not authorize
solver execution, measured-data ingest, calibration-data ingest, route
promotion, or raw-magnitude final gates.
