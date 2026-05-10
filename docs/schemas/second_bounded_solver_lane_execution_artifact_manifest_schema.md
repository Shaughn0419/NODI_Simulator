# P8 Second Bounded Solver Lane Artifact Manifest Schema

Required role: `second_bounded_solver_lane_execution_artifact_manifest`.

Every artifact row must carry the P8 guard fields, path status, and hash role. The artifact manifest excludes its own hash to avoid a self-hash cycle.

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

Claim boundary fields keep calibrated SNR, absolute LOD, true EV concentration, biological specificity, detector-voltage prediction, sample-count, measured blank safety, route-promotion, and main-660 redefinition claims blocked.
