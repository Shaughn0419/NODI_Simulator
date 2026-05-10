# P6 Solver Output Manifest Schema

Role: `minimal_bounded_solver_output_manifest_trace_only`.

The output manifest records the generated CSV hash, row count, selected route ids, and the allowed final-gate metric families: `rank`, `rank_percentile`, and `pairwise_inversion`.

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

The solver-native fields are trace-only. SNR and LOD claims remain blocked; detector-voltage, sample-count, measured blank safety, and route-promotion claims remain blocked.
