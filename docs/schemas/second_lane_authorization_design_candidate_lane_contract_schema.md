# P7 Candidate Lane Contract Schema

Required role: `second_lane_candidate_contract_design_only`.

Required lane id: `second_bounded_solver_lane_candidate_design_only`.

Required lane status: `candidate_design_only_not_selected_for_execution`.

The future authorization phrase is `authorize second bounded solver lane execution`, but P7 records that it has not already been received.

Required constraints:

- The candidate lane must bind a separately reviewed route subset before execution.
- The candidate lane must remain bounded to a narrow next-lane scope.
- The candidate lane must not redefine main-660 or optional_660_W900_D1400.
- Raw and solver-native raw magnitude must not be final gates.
- Measured and calibration data ingest must remain unauthorized.

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
