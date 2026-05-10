# Bounded Physical-Solver Readiness Schema Manifest Schema

Schema id:

```text
ev_nodi_p2_bounded_physical_solver_readiness_schema_manifest_v1
```

Role:

```text
lane_readiness_schema_manifest_no_solver_execution
```

This P2 manifest records readiness schemas for future bounded physical-solver
lanes. It does not run full-wave, Green-tensor, vector, Jones, roughness,
leakage, transport, or residence-time solvers. It does not ingest measured
data or change the P0 release conclusion.

Required top-level guard fields:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
p1_surrogate_risk_role_preserved = true
physical_solver_execution_authorized = false
measured_data_ingest_authorized = false
```

Each lane row must include:

```text
lane_id
readiness_status = schema_governance_only_not_executable
artifact_status = planned_readiness_schema_only
solver_output_path = null
required_readiness_fields
required_false_fields
allowed_gate_metric_families
raw_magnitude_final_gate_allowed = false
```

Allowed future interpretability families are rank, rank-percentile, and
pairwise-inversion diagnostics. Raw arbitrary-unit or solver-native magnitudes
may be trace fields only, not final gates.
