# P6 Minimal Bounded Solver Execution

This directory contains the P6 minimal bounded solver execution package.

P6 is the first phase after the explicit P5 gate phrase `authorize minimal bounded solver execution`. It writes a deterministic Green-kernel trace for the three P4 selected routes and keeps interpretation limited to rank, rank percentile, and pairwise order.

The solver-native real, imaginary, and response fields are trace-only. Raw magnitude and solver-native raw magnitude remain blocked as final gates.

Boundaries:

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

SNR and LOD claims remain blocked. True EV concentration and biological specificity claims remain blocked. Detector-voltage, sample-count, measured blank safety, absolute event probability, and route-promotion claims remain blocked.
