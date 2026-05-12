# P18 Bounded-Lane Synthesis Artifact Manifest Schema

Required role: `bounded_lane_synthesis_artifact_manifest`.

The manifest enumerates the P18 registry, report, README, rank behavior summary CSV, synthesis record, and artifact manifest.

Required decision: `stop_mechanical_lane_roll_forward_pending_p19_evidence_strategy`.

Required next stage: `P19_next_evidence_strategy_gate`.

The manifest must bind the six source trace CSV files by path and sha256. It is not a solver execution artifact and must keep route promotion blocked.

## Artifact Field Coverage

Fields below are tracked by the schema-doc drift auditor for matched artifact files.

### `results/post_v2_bounded_lane_synthesis_stop_continue/bounded_lane_synthesis_artifact_manifest.json`

- `bounded_lanes_sufficient_for_route_promotion`
- `calibrated_claim_allowed`
- `calibration_data_ingest_authorized`
- `continue_mechanical_lanes_without_acceptance_criteria`
- `full_wave_solver_execution_authorized`
- `future_authorization_phrase_already_received`
- `measured_data_ingest_authorized`
- `new_mesh_generation_authorized`
- `next_required_stage`
- `operator_export_generation_authorized`
- `p0_release_conclusion_changed`
- `p10_closure_scope_preserved`
- `p10_third_bounded_execution_scope_preserved`
- `p11_authorization_design_scope_preserved`
- `p12_closure_scope_preserved`
- `p12_fourth_bounded_execution_scope_preserved`
- `p13_authorization_design_scope_preserved`
- `p14_closure_scope_preserved`
- `p14_fifth_bounded_execution_scope_preserved`
- `p15_authorization_design_scope_preserved`
- `p16_closure_scope_preserved`
- `p16_sixth_bounded_execution_scope_preserved`
- `p17_authorization_design_scope_preserved`
- `p19_evidence_strategy_gate_required`
- `p1_surrogate_risk_role_preserved`
- `p2_readiness_scope_preserved`
- `p3_pilot_design_scope_preserved`
- `p4_dry_run_preflight_scope_preserved`
- `p5_authorization_gate_scope_preserved`
- `p6_minimal_execution_scope_preserved`
- `p7_authorization_design_scope_preserved`
- `p8_second_bounded_execution_scope_preserved`
- `p9_authorization_design_scope_preserved`
- `physical_solver_execution_authorized`
- `rank_instability_across_bounded_lanes_detected`
- `raw_magnitude_final_gate_allowed`
- `roughness_leakage_simulation_authorized`
- `route_promotion_authorized`
- `seventh_bounded_solver_lane_execution_authorized`
- `solver_native_raw_magnitude_final_gate_allowed`
- `solver_output_generated`
- `source_bindings`
- `stop_continue_decision`
- `transport_residence_time_simulation_authorized`
- `vector_solver_execution_authorized`
