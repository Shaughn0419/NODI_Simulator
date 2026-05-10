# P7 Second-Lane Authorization Design

This directory contains P7 authorization-design artifacts for a possible second bounded solver lane.

P7 is planning, schema, governance, and verifier work only. It does not run a solver and does not create solver output. It binds P6 trace artifacts as prior trace-only rank and pairwise-order evidence, not as calibration, route promotion, SNR, LOD, concentration, or specificity evidence.

Future execution is blocked unless a later request provides the exact phrase `authorize second bounded solver lane execution`. This P7 package records that phrase as future-required only and records that it has not already been received.

Boundaries:

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

Calibrated SNR, absolute LOD, true EV concentration, biological specificity, detector-voltage prediction, sample count, measured blank safety, route promotion, and main-660 redefinition claims remain blocked.
