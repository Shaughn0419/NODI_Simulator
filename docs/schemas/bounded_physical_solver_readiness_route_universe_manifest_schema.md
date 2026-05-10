# Bounded Physical-Solver Readiness Route Universe Manifest Schema

Schema id:

```text
ev_nodi_p2_bounded_physical_solver_readiness_route_universe_manifest_v1
```

Role:

```text
bounded_route_universe_manifest_no_solver_execution
```

This P2 manifest defines the bounded route universe for future solver preflight.
It is assembled from existing P0 mandatory-audit route rows and P1 no-solver
surrogate-risk diagnostics. It does not run a solver and does not authorize
route promotion.

Required top-level guard fields:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
p1_surrogate_risk_role_preserved = true
physical_solver_execution_authorized = false
measured_data_ingest_authorized = false
```

Each route row must include:

```text
candidate_id
route_key
comparison_stratum
route_role_final
final_audit_decision
required_next_artifact_priority
full_wave_green_tensor_surrogate_risk_label
vector_jones_surrogate_risk_label
roughness_leakage_surrogate_risk_label
transport_residence_time_surrogate_risk_label
any_p1_high_surrogate_risk
any_p1_pairwise_inversion_flag
bounded_route_universe_role = future_solver_preflight_only
```

Every route row must keep:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
p1_surrogate_risk_role_preserved = true
physical_solver_execution_authorized = false
measured_data_ingest_authorized = false
raw_magnitude_final_gate_allowed = false
route_promotion_authorized = false
```

Raw proxy fields are intentionally excluded. Future solver outputs, if ever
separately authorized, must be interpreted through rank, rank-percentile, or
pairwise-inversion families rather than raw magnitude gates.
