# Bounded Solver Authorization Gate Record

Schema:

```text
ev_nodi_p5_bounded_solver_authorization_gate_record_v1
```

Role:

```text
authorization_gate_record_denies_execution_until_explicit_later_phase
```

Required decision:

```text
authorization_gate_decision = not_authorized_pending_explicit_later_phase_execution_request
explicit_solver_execution_request_required = true
required_next_authorization_phrase = authorize minimal bounded solver execution
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

## Artifact-field alignment note

These fields are present in the paired artifact payload and are checked by schema drift audit:

- `minimum_later_phase_requirements`

