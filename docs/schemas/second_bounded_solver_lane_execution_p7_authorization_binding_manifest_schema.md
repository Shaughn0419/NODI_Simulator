# P8 P7 Authorization Binding Manifest Schema

Required role: `p7_authorization_binding_for_second_bounded_execution`.

Required bindings:

- `results/post_v2_second_lane_authorization_design/second_lane_authorization_design_authorization_gate_record.json`
- `results/post_v2_second_lane_authorization_design/second_lane_authorization_design_candidate_lane_contract_manifest.json`
- `results/post_v2_second_lane_authorization_design/second_lane_authorization_design_p6_evidence_binding_manifest.json`
- `results/post_v2_bounded_solver_dry_run_preflight/full_wave_green_tensor_minimal_pilot_input_manifest.json`

The authorization phrase must be `authorize second bounded solver lane execution`.

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

P7 and P6 artifacts are evidence bindings only; they do not authorize calibration, route promotion, or measured-data interpretation.

## Artifact-field alignment note

These fields are present in the paired artifact payload and are checked by schema drift audit:

- `bound_route_ids`
- `p7_authorization_gate_record_sha256`
- `p7_candidate_lane_contract_manifest_sha256`
- `p7_gate_prior_decision`
- `p7_gate_prior_stage`
- `p7_p6_evidence_binding_manifest_sha256`
- `route_subset_binding_sha256`
- `user_authorization_phrase_received`

