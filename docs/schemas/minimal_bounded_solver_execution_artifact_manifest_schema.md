# P6 Artifact Manifest Schema

Role: `minimal_bounded_solver_execution_artifact_manifest`.

Each artifact row must include the path, status, claim level, content hash where applicable, and the P6 guard fields.

Required boundary fields:

- `calibrated_claim_allowed = false`
- `p0_release_conclusion_changed = false`
- `p1_surrogate_risk_role_preserved = true`
- `p2_readiness_scope_preserved = true`
- `p3_pilot_design_scope_preserved = true`
- `p4_dry_run_preflight_scope_preserved = true`
- `p5_authorization_gate_scope_preserved = true`
- `physical_solver_execution_authorized = true`
- `minimal_bounded_solver_execution_authorized = true`
- `green_tensor_minimal_solver_execution_authorized = true`
- `solver_output_generated = true`
- `measured_data_ingest_authorized = false`
- `calibration_data_ingest_authorized = false`
- `new_mesh_generation_authorized = false`
- `operator_export_generation_authorized = false`
- `full_wave_solver_execution_authorized = false`
- `route_promotion_authorized = false`
- `raw_magnitude_final_gate_allowed = false`
- `solver_native_raw_magnitude_final_gate_allowed = false`

SNR and LOD claims remain blocked. True EV concentration, biological specificity, and route-promotion claims remain blocked.
