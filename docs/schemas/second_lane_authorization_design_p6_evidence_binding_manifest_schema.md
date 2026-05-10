# P7 P6 Evidence Binding Manifest Schema

Required role: `p6_evidence_binding_for_second_lane_authorization_design`.

Required P6 evidence paths:

- `results/post_v2_minimal_bounded_solver_execution/minimal_bounded_solver_execution_p5_binding_manifest.json`
- `results/post_v2_minimal_bounded_solver_execution/full_wave_green_tensor_minimal_solver_output.csv`
- `results/post_v2_minimal_bounded_solver_execution/full_wave_green_tensor_minimal_solver_output_manifest.json`
- `results/post_v2_minimal_bounded_solver_execution/minimal_bounded_solver_execution_artifact_manifest.json`

The P6 trace output role must be `prior_trace_only_rank_pairwise_order_evidence_not_calibration_or_promotion`.

Required guards:

- `calibrated_claim_allowed = false`
- `p0_release_conclusion_changed = false`
- `p1_surrogate_risk_role_preserved = true`
- `p2_readiness_scope_preserved = true`
- `p3_pilot_design_scope_preserved = true`
- `p4_dry_run_preflight_scope_preserved = true`
- `p5_authorization_gate_scope_preserved = true`
- `p6_minimal_execution_scope_preserved = true`
- `physical_solver_execution_authorized = false`
- `second_bounded_solver_lane_execution_authorized = false`
- `solver_output_generated = false`
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

The P6 trace is not calibrated prediction evidence, not physical calibration evidence, not route-promotion evidence, and not SNR, LOD, concentration, or specificity evidence.
