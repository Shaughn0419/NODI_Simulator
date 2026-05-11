# Physical-Ceiling Route Coverage Manifest Schema

Schema id:

```text
ev_nodi_p1_physical_ceiling_route_coverage_manifest_v1
```

Role:

```text
p0_route_coverage_registry_and_no_solver_output_guard
```

This P1 manifest checks that each physical-ceiling lane has route-key coverage
against the P0 mandatory audit primary route universe and that each generated
diagnostic output exists. It does not run a physical solver or change the P0
release conclusion.

Required top-level guard fields:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
physical_ceiling_role = surrogate_risk_reduction_only
diagnostic_outputs_generated = true
solver_or_simulation_execution_authorized = false
```

Each lane row must include:

```text
lane_id
contract_path
planned_output_path
planned_output_exists = true
primary_source_path
primary_route_key_count
route_key_source_count
route_key_sources_with_full_primary_coverage
diagnostic_output_generated = true
```

Each route-key source row must have:

```text
source_has_route_key_field = true
missing_primary_route_key_count = 0
missing_primary_route_keys = []
```

Non-route-key context sources are allowed, but at least one route-key source per
lane must cover the P0 primary route universe. This manifest is a coverage guard
only and does not authorize calibrated physical-ceiling result claims.

## Artifact-field alignment note

These fields are present in the paired artifact payload and are checked by schema drift audit:

- `lanes`
- `source_bindings`

