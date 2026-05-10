# P14 Closure Artifact Manifest Schema

Required role: `p14_closure_artifact_manifest`.

The manifest enumerates the P14 closure registry, closure note, review record, and manifest itself. It keeps calibrated SNR blocked and absolute LOD blocked; it is not a calibration or promotion artifact.

Required guards:

- `calibrated_claim_allowed = false`
- `p0_release_conclusion_changed = false`
- `p1_surrogate_risk_role_preserved = true`
- `p2_readiness_scope_preserved = true`
- `p3_pilot_design_scope_preserved = true`
- `p4_dry_run_preflight_scope_preserved = true`
- `p5_authorization_gate_scope_preserved = true`
- `p6_minimal_execution_scope_preserved = true`
- `p7_authorization_design_scope_preserved = true`
- `p8_second_bounded_execution_scope_preserved = true`
- `p9_authorization_design_scope_preserved = true`
- `p10_third_bounded_execution_scope_preserved = true`
- `p10_closure_scope_preserved = true`
- `p11_authorization_design_scope_preserved = true`
- `p12_fourth_bounded_execution_scope_preserved = true`
- `p12_closure_scope_preserved = true`
- `p13_authorization_design_scope_preserved = true`
- `p14_fifth_bounded_execution_scope_preserved = true`
- `measured_data_ingest_authorized = false`
- `calibration_data_ingest_authorized = false`
- `new_mesh_generation_authorized = false`
- `operator_export_generation_authorized = false`
- `full_wave_solver_execution_authorized = false`
- `vector_solver_execution_authorized = false`
- `roughness_leakage_simulation_authorized = false`
- `transport_residence_time_simulation_authorized = false`
- `route_promotion_authorized = false`
- `raw_magnitude_final_gate_allowed = false`
- `solver_native_raw_magnitude_final_gate_allowed = false`
- `additional_solver_execution_authorized = false`
- `additional_solver_output_generated = false`
