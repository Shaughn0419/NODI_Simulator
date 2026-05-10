# Post-v2 Bounded Solver Dry-Run Preflight P4 Artifacts

This directory is for P4 dry-run preflight artifacts.

Current allowed contents:

```text
bounded_solver_dry_run_preflight_p3_binding_manifest.json
full_wave_green_tensor_minimal_pilot_input_manifest.json
full_wave_green_tensor_mesh_boundary_unit_preflight_manifest.json
full_wave_green_tensor_execution_authorization_record.json
bounded_solver_dry_run_preflight_artifact_manifest.json
```

These files instantiate P3 pilot-design contracts as reviewable dry-run
manifests. They do not contain solver output, mesh output, operator export,
measured data, calibration data, detector-unit prediction, or route-promotion
evidence.

The execution authorization record denies execution in this phase:

```text
physical_solver_execution_authorized = false
new_mesh_generation_authorized = false
operator_export_generation_authorized = false
solver_output_generated = false
```

The role of this directory is `bounded_solver_dry_run_preflight_only`. It does
not change the P0 release conclusion, it preserves P1 surrogate-risk reduction,
it preserves P2 readiness scope, and it preserves P3 pilot-design scope. SNR,
LOD, true EV concentration, biological specificity, detector-voltage
prediction, sample-count, measured blank-safety, and route-promotion claims
remain blocked.
