# EV/NODI realism v2 R5.1 route-role stability interpretation plan

Date: 2026-05-07

Prior gate consumed:

```text
PASS_R5_RESULTS_PREPARE_NEXT_STAGE_PLAN_ONLY
```

This is a next-stage plan only. It does not execute R5.1, R6, R5 follow-up
expansion, route promotion, main-660 redefinition, selected-annulus changes,
calibrated SNR, calibrated event probability, absolute LOD, true EV
concentration, biological specificity, Tsuyama paper-fit continuation, v1
overwrite, or ET2030 direct current-input unlock.

## Selected next-stage lane

The selected lane is:

```text
R5_1_route_role_stability_interpretation_report_only
```

This was chosen instead of R6 planning because R5 was clean but raised
interpretation questions:

```text
weak_reference_control mean score > main_660 mean score
some context routes have higher mean scores than locked main_660
R5 remains scenario-prior / relative-with-priors, not calibrated detection
```

The next reviewed action should therefore interpret route-role stability,
scenario sensitivity, weak-reference controls, context-route warnings, and
claim boundaries before any R6 or experimental-panel plan is prepared.

## R5 evidence carried forward

R5 results were accepted as capped and guarded:

```text
R5_case_rows = 256,256
v1_source_rows = 32,032
route_identity_count = 572
named_scenario_bundle_count = 8
stochastic_seed_count = 0
R5_cap_respected = true
R5_followup_expansion_authorized = false
```

R4.2 carryforward remains:

```text
fine_confirm_main660_fraction = 1.0
fine_confirm_sign_reliable_subset_fraction = 1.0
review_refined_main660_fraction = 1.0
fine_confirm_agrees_with_review_refined = 1.0
coarse_screen_role = screening_only_warning
```

## Interpretation targets

The R5.1 interpretation must cover:

```text
route-role stability
scenario-bundle sensitivity
main-660 robustness under locked route identity
weak-reference-control high-score interpretation
context-route high-score warnings without promotion
selected-annulus non-promotion / parallel-lens-only status
404 thermal sidecar as safety-only
claim-boundary preservation
```

Route-role mean scores from R5:

```text
weak_reference_control          0.152257
main_660                        0.126095
optional_robustness_probe       0.123041
selected_annulus_longwave       0.100906
medium_wave_baseline            0.077653
full_grid_context_route         0.070901
shortwave_mechanism_candidate   0.044475
selected_annulus_shortwave      0.040433
```

Top context-route warnings by mean score:

```text
660_500x1500  0.196396
660_500x1400  0.189745
660_500x1300  0.182575
660_500x1200  0.173859
660_600x1500  0.165472
```

These are warnings for interpretation only. They are not route promotion,
main-660 redefinition, or experimental recommendations.

## Scope and cost

R5.1 uses existing R5 artifacts only:

```text
new_case_rows_authorized = 0
new_scenario_bundle_authorized = false
new_stochastic_seed_authorized = false
new_solver_case_authorized = false
new_experiment_authorized = false
```

Future output directory if separately authorized:

```text
results/ev_nodi_realism_v2_R5_1_route_role_stability_interpretation/
```

## Required future outputs if authorized

```text
R5_1_route_role_stability_interpretation_manifest.csv
R5_1_route_role_stability_decision_table.csv
R5_1_scenario_sensitivity_interpretation.csv
R5_1_context_route_high_score_warning_table.csv
R5_1_main_660_robustness_interpretation.csv
R5_1_weak_reference_control_interpretation.csv
R5_1_selected_annulus_nonpromotion_summary.csv
R5_1_claim_boundary_guardrail_summary.csv
R5_1_next_stage_options_matrix.csv
run_manifest.json
R5_1_route_role_stability_interpretation_report.md
```

## Allowed future recommendation classes

The future R5.1 report may recommend only plan-preparation classes:

```text
prepare_R6_plan_for_external_review_only
prepare_post_v2_validation_dependency_backlog_only
prepare_bounded_additional_scenario_prior_audit_plan_only
hold_for_route_governance_revision_plan_only
```

It must not execute any of those next steps.

## Stop gates

The plan fails closed on:

```text
R5_1_execution_without_external_authorization
R6_plan_preparation_started
R6_execution_started
R5_followup_expansion_started
R5_case_rows_expanded_beyond_reviewed_cap
v1_full_grid_output_overwritten
Tsuyama_paper_fit_continued
selected_annulus_bounds_changed
selected_annulus_replaces_all_crossing_ranking
context_route_promotion_attempted
main_660_redefinition_attempted
optional_660_900x1400_redefines_main_660
route_specific_manual_sign_flip_attempted
calibrated_SNR_or_event_probability_claim_emitted
absolute_LOD_or_true_concentration_claim_emitted
biological_specificity_claim_emitted
ET2030_direct_current_input_unlocked_without_measured_bench_artifact
thermal_sidecar_used_to_increase_NODI_score
finite_zero_event_blank_safety_claim_emitted
legacy_detector_SNR_output_header_emitted
legacy_calibrated_detector_SNR_output_header_emitted
```

## Claim boundaries

The interpretation remains:

```text
SNR_claim_level = absolute_blocked
event_probability_claim_level = absolute_blocked
p_detect_mapping_claim_level = relative_with_priors
```

Forbidden:

```text
calibrated SNR
calibrated event probability
absolute LOD
true EV concentration
biological specificity
legacy detector_SNR / calibrated_detector_SNR output headers
```

## Provenance freeze

R5.1 freezes the following R5 result checksums:

```text
R5_case_manifest_checksum =
0d5669a285b2a2160b833a7b4afd5035c5026c27918f6179b45248f21160447c

R5_summary_checksum =
850e6f9edc67f3d0fdeb18cea18a3b5910bcf0e7995e98651cf1e990a4423d4f

R5_route_role_stability_checksum =
fd3c65c1cf0d5c5a851a96b58534a274f61dd37255b62c5405e4741f254b2c32

R5_main660_summary_checksum =
9e10146314085277e8c8ca1b7ef4945b97ede8dd34a627ce129a6256dd3226cd

R5_context_no_promotion_checksum =
74402c6baa084a76afa8f7a3647d992c77f79d700cf573d124ffe75a4353f890

R5_scenario_sensitivity_checksum =
475a1b80c1e9b8e9669acbeaa504810935d1123166fea49cc60c5ad4e14b2646

R5_cost_estimate_checksum =
7b22e8b00483abf7707cfa88709bbca8aa1bd4e922b3573f56fcd7a28f262ce5

R5_run_manifest_checksum =
21fac8a93649e900304465e65ac49f8a15e50870ef2c8f1d7b3299f19f08d5e9
```

## Review request

The requested review question is narrow:

```text
Is this plan tight enough to authorize R5.1 route-role stability interpretation only?
```

It is not a request to authorize R6, R5 expansion, route promotion, main-660
redefinition, selected-annulus changes, calibrated claims, or experiments.
