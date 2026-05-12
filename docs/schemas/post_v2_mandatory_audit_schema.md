# Post-v2 Mandatory Audit Schema

The core table is `results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv`. Rows are unique relative route aggregates with declared particle scope, rank-percentile evidence, and explicit claim blockers. Raw arbitrary-unit ratios are diagnostic only.

Top-level columns tracked from `top_candidate_mandatory_audit.csv`:

- `absolute_lod_claim_allowed`
- `aggregation_particle_family`
- `aggregation_quantile`
- `aggregation_scope`
- `anchor_particles_included`
- `audit_bfp_jacobian_applied`
- `audit_generated_at`
- `bfp_roi_cross_term_proxy`
- `bfp_roi_rank_percentile_in_stratum`
- `bfp_roi_score`
- `bfp_roi_self_term_proxy`
- `biological_specificity_claim_allowed`
- `calibrated_snr_claim_allowed`
- `candidate_source`
- `coincidence_event_overlap_proxy_definition`
- `coincidence_event_overlap_proxy_label`
- `comparison_stratum`
- `contaminant_pass_fraction`
- `contaminant_risk_label`
- `contaminant_utilized_in_risk_policy`
- `contaminants_included_in_route_score`
- `depth_nm`
- `detector_voltage_prediction_claim_allowed`
- `ev_polydispersity_pass_fraction_proxy`
- `ev_sample_profile_min_risk_label`
- `ev_sample_profile_resolved`
- `final_audit_decision`
- `main_660_redefinition_authorized`
- `missing_v1_reason`
- `noise_max_abs_percentile_delta_vs_nominal`
- `noise_pass_fraction`
- `rank_inversion_flag`
- `rank_inversion_reason_codes`
- `rank_inversion_severity`
- `ranking_participation`
- `route_key`
- `route_role_final`
- `route_role_initial`
- `selected_annulus_boundary_policy`
- `selected_annulus_main_control_reversal`
- `selected_annulus_primary_gate_switch_blocked`
- `selected_annulus_replaces_all_crossing_ranking`
- `source_v1_library_sha256`
- `true_ev_concentration_claim_allowed`
- `tsuyama_geometry_relation`
- `tsuyama_signal_rank_percentile_in_stratum`
- `tsuyama_signal_score`
- `v1_bfp_to_angle_jacobian_applied`
- `v1_detector_field_units`
- `v1_field_coordinate_measure`
- `v1_operator_route`
- `v1_output_claim_level`
- `v1_scalar_rank_in_stratum`
- `v1_scalar_rank_percentile_in_stratum`
- `v1_scalar_score`
- `wavelength_nm`
- `width_nm`

Top-level manifest fields tracked from `top_candidate_mandatory_audit_manifest.json`:

- `audit_bfp_jacobian_applied_layer`
- `audit_manifest_schema`
- `calibrated_claim_allowed`
- `milestone`
- `p0b_artifacts_produced_from_evidence_chain`
- `rank_policy`
- `unprefixed_forbidden_audit_columns`
- `v1_bfp_to_angle_jacobian_applied_expected`
- `v1_source_field_mapping`
