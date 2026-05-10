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
physical_solver_execution_authorized = false
solver_output_generated = false
```

Any later execution requires a separate authorization phase.
