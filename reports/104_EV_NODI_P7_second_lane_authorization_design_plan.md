# P7 Second-Lane Bounded Solver Authorization Design Plan

P7 is an authorization-design phase only. It records the contract for a possible second bounded solver lane and binds prior P6 artifacts as trace-only evidence. It does not authorize physical solver execution, does not generate solver output, does not generate a new mesh or operator export, does not ingest measured or calibration data, and does not promote routes.

The next execution lane remains blocked unless a later user request provides the exact future phrase `authorize second bounded solver lane execution`. P7 records that phrase as a future requirement only; it is not received in this phase.

## Evidence Binding

P7 binds these P6 artifacts as prior evidence:

- `results/post_v2_minimal_bounded_solver_execution/minimal_bounded_solver_execution_p5_binding_manifest.json`
- `results/post_v2_minimal_bounded_solver_execution/full_wave_green_tensor_minimal_solver_output.csv`
- `results/post_v2_minimal_bounded_solver_execution/full_wave_green_tensor_minimal_solver_output_manifest.json`
- `results/post_v2_minimal_bounded_solver_execution/minimal_bounded_solver_execution_artifact_manifest.json`

The P6 trace output remains trace-only rank, rank-percentile, and pairwise-order evidence. It is not calibrated prediction evidence, not physical calibration evidence, not route-promotion evidence, and not SNR, LOD, concentration, or specificity evidence.

## Guard Fields

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

## Candidate Lane Contract

The candidate lane is design-only and not selected for execution. Any later execution proposal must bind a narrow route subset, keep main-660 and optional_660_W900_D1400 identities unchanged, preserve P0 through P6 conclusions, and keep raw and solver-native raw magnitude blocked as final gates.

Calibrated SNR, absolute LOD, true EV concentration, biological specificity, detector-voltage prediction, sample count, measured blank safety, route promotion, and main-660 redefinition claims remain blocked.
