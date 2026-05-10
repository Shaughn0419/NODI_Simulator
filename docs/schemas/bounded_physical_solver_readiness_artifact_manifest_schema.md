# Bounded Physical-Solver Readiness Artifact Manifest Schema

Schema id:

```text
ev_nodi_p2_bounded_physical_solver_readiness_artifact_manifest_v1
```

Role:

```text
schema_governance_artifact_manifest_no_solver_execution
```

This P2 manifest records the registry, plan, readiness manifests, verifier,
generator, README, tests, schema docs, and completion note for bounded
physical-solver readiness. It is an artifact inventory only.

Required top-level guard fields:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
p1_surrogate_risk_role_preserved = true
physical_solver_execution_authorized = false
measured_data_ingest_authorized = false
```

Required artifact-row guard fields:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
p1_surrogate_risk_role_preserved = true
physical_solver_execution_authorized = false
measured_data_ingest_authorized = false
```

The following claims remain blocked: calibrated SNR, absolute LOD, true EV
concentration, biological specificity, detector-voltage prediction,
sample-count, measured blank-safety, and route-promotion claims.
