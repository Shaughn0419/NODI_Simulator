# P6 P5 Binding Manifest Schema

Role: `p5_authorization_gate_binding_for_minimal_execution`.

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

The manifest must bind the P5 authorization gate record and must record the exact phrase `authorize minimal bounded solver execution`. SNR and LOD claims remain blocked; true EV concentration and route-promotion claims remain blocked.
