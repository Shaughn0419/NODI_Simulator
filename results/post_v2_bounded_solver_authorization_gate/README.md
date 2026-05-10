# Post-v2 Bounded Solver Authorization Gate P5 Artifacts

This directory is for P5 authorization-gate artifacts.

Current allowed contents:

```text
bounded_solver_authorization_gate_p4_binding_manifest.json
bounded_solver_authorization_gate_record.json
bounded_solver_authorization_gate_artifact_manifest.json
```

These files bind the P4 dry-run preflight package and record that execution is
still not authorized. They do not contain solver output, mesh output, operator
export, measured data, calibration data, detector-unit prediction, or
route-promotion evidence.

Required boundary declarations remain:

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

The next phase can only consider execution after an explicit request to
`authorize minimal bounded solver execution`.
