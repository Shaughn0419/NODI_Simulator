# Bounded Solver Dry-Run Execution Authorization Record

Schema:

```text
ev_nodi_p4_full_wave_green_tensor_execution_authorization_record_v1
```

Role:

```text
execution_authorization_record_denies_execution
```

Required decision:

```text
execution_authorization_decision = not_authorized_phase4_dry_run_only
explicit_later_phase_required = true
calibrated_claim_allowed = false
physical_solver_execution_authorized = false
measured_data_ingest_authorized = false
calibration_data_ingest_authorized = false
new_mesh_generation_authorized = false
operator_export_generation_authorized = false
solver_output_generated = false
route_promotion_authorized = false
```

Any later execution requires a separate authorization phase.
