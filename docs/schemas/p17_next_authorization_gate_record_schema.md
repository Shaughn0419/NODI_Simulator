# P17 Next Authorization Gate Record Schema

Required decision: `not_authorized_pending_explicit_future_request`.

Required future phrase: `authorize seventh bounded solver lane execution`.

The future phrase must not be marked as already received.

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

Rank-instability governance is required:

- `instability_observation = bounded_lane_rank_instability_recurrence_trace_only`
- `rank_delta_vector = [-1, 1, 0]`
- recurrence event ids: `p12_to_p14_main_660_swap`, `p14_to_p16_main_660_swap`
- `governance_role = record_recurring_rank_instability_not_route_preference`
- `interpretation_boundary = trace_only_recurring_instability_not_route_promotion_or_preference`

Report-numbering governance is required:

- `note_id = stage_p17_uses_report_119_under_current_sequential_report_numbering`
- `numbering_role = sequential_report_numbering_not_stage_numbering`

## Artifact-field alignment note

These fields are present in the paired artifact payload and are checked by schema drift audit:

- `authorization_gate_decision`
- `explicit_next_execution_request_required`
- `future_authorization_phrase_already_received`
- `minimum_later_phase_requirements`
- `rank_instability_governance`
- `report_numbering_governance`
