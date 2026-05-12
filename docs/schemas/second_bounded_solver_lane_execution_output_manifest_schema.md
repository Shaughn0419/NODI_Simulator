# P8 Second Bounded Solver Lane Output Manifest Schema

Required role: `second_bounded_solver_lane_output_manifest_trace_only`.

Required output: `results/post_v2_second_bounded_solver_lane_execution/second_bounded_solver_lane_trace_output.csv`.

Allowed final gate metric families:

- `rank`
- `rank_percentile`
- `pairwise_inversion`

Solver-native trace fields must remain `trace_only_not_final_gate`.

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
- `physical_solver_execution_authorized = true`
- `second_bounded_solver_lane_execution_authorized = true`
- `solver_output_generated = true`
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

The output is not calibrated SNR, not absolute LOD, not true EV concentration, not biological specificity, not detector-voltage prediction, and not route-promotion evidence.

## Artifact Field Coverage

Fields below are tracked by the schema-doc drift auditor for matched artifact files.

### `results/post_v2_second_bounded_solver_lane_execution/second_bounded_solver_lane_trace_output_manifest.json`

- `allowed_final_gate_metric_families`
- `output_sha256`
- `selected_route_ids`
