# Bounded Solver Dry-Run Preflight Input Manifest

Schema:

```text
ev_nodi_p4_full_wave_green_tensor_minimal_pilot_input_manifest_v1
```

Role:

```text
dry_run_solver_input_manifest_no_execution
```

The manifest binds the P3 route subset, selected route IDs, unit declarations,
and the P4 mesh preflight plus execution authorization record paths. It is not
runtime solver input.

Required declarations:

```text
calibrated_claim_allowed = false
physical_solver_execution_authorized = false
measured_data_ingest_authorized = false
calibration_data_ingest_authorized = false
new_mesh_generation_authorized = false
operator_export_generation_authorized = false
solver_output_generated = false
route_promotion_authorized = false
```
