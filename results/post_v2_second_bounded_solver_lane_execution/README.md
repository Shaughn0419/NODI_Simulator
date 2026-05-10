# P8 Second Bounded Solver Lane Execution

This directory contains the P8 second bounded solver lane execution package.

P8 runs only a deterministic bounded phase-gradient trace for the three P4/P6 selected routes after the required authorization phrase was provided. The output is trace-only. Final interpretation remains limited to rank, rank-percentile, pairwise order, and rank delta versus P6 ordering.

The solver-native phase-gradient, aperture-balance, and response fields are trace-only. Raw magnitude and solver-native raw magnitude remain blocked as final gates.

Boundaries:

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

Calibrated SNR, absolute LOD, true EV concentration, biological specificity, detector-voltage prediction, sample-count, measured blank safety, route-promotion, and main-660 redefinition claims remain blocked.
