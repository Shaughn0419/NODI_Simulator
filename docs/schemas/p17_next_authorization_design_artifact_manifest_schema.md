# P17 Next Authorization Design Artifact Manifest Schema

Required role: `p17_next_authorization_design_artifact_manifest`.

The manifest enumerates the P17 design registry, design plan, P16 closure binding, next gate record, and manifest itself. It keeps calibrated SNR blocked and absolute LOD blocked; it is not a solver execution artifact.

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
- `p14_closure_scope_preserved = true`
- `p15_authorization_design_scope_preserved = true`
- `p16_sixth_bounded_execution_scope_preserved = true`
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

The manifest must carry the recurring bounded-lane rank-instability governance object with delta `[-1, 1, 0]` for both `p12_to_p14_main_660_swap` and `p14_to_p16_main_660_swap`. That object is trace-only and keeps route promotion blocked.

The manifest must also carry the report-numbering governance note for `reports/119_EV_NODI_P17_seventh_bounded_lane_authorization_design_plan.md`.
