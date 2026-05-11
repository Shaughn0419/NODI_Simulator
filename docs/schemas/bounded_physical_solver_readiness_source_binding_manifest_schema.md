# Bounded Physical-Solver Readiness Source Binding Manifest Schema

Schema id:

```text
ev_nodi_p2_bounded_physical_solver_readiness_source_binding_manifest_v1
```

Role:

```text
source_binding_manifest_no_solver_execution
```

This P2 manifest binds the readiness package to existing P0 mandatory-audit
sources and P1 generated no-solver surrogate-risk diagnostics. It does not
ingest measured data and does not execute physical solvers.

Required top-level guard fields:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
p1_surrogate_risk_role_preserved = true
physical_solver_execution_authorized = false
measured_data_ingest_authorized = false
```

Each source binding row must include:

```text
source_id
source_role
source_path
source_exists = true
source_sha256
source_row_count
required_fields
missing_required_fields = []
required_fields_present = true
```

The allowed source set is limited to P0 mandatory route-audit fields and P1
rank/risk diagnostic fields. No measured-data source is allowed in P2.

## Artifact-field alignment note

These fields are present in the paired artifact payload and are checked by schema drift audit:

- `bindings`

