# EV/NODI realism v2 R5 full-grid v2 analysis

Date: 2026-05-07

Decision boundary consumed: `PASS_TO_R5_FULL_GRID_V2_EXECUTION_ONLY`.

This report summarizes the one capped R5 full-grid v2 execution. It does not
authorize R5 follow-up expansion, R6, route promotion, main-660 redefinition,
selected-annulus changes, calibrated SNR, calibrated event probability,
absolute LOD, true EV concentration, biological specificity, Tsuyama paper-fit
continuation, v1 overwrite, or ET2030 direct current-input unlock.

## Execution scope

R5 was executed exactly under the reviewed cap:

```text
v1 source rows = 32,032
named scenario bundles = 8
stochastic seeds = 0
case rows = 256,256
max case rows before next review = 256,256
output directory = results/ev_nodi_realism_v2_full_grid_R5_v2/
```

The execution type is deterministic source-row scenario expansion. It is not a
stochastic event-level rerun and it does not overwrite the v1 full-grid source.

## Required outputs

The R5 output directory contains exactly the planned outputs:

```text
full_grid_v2_case_manifest.csv
full_grid_v2_summary.csv
route_role_stability_full_grid_v2.csv
main_660_full_grid_v2_stability_summary.csv
context_route_no_promotion_summary.csv
optional_660_governance_summary.csv
selected_annulus_parallel_lens_summary.csv
scenario_bundle_sensitivity_summary.csv
R4_2_validation_grade_carryforward_summary.csv
coarse_screen_warning_carryforward_summary.csv
detector_blank_claim_guardrail_summary.csv
thermal_404_sidecar_summary.csv
unit_guardrail_summary.csv
full_grid_v2_cost_estimate.csv
run_manifest.json
R5_full_grid_v2_report.md
```

Direct checks confirmed:

```text
full_grid_v2_case_manifest.csv rows = 256,256
full_grid_v2_summary.csv rows = 256,256
source_v1_row_index unique count = 32,032
route_id unique count = 572
scenario bundles = 8 reviewed IDs
stochastic_seed values = empty only
```

## R4.2 carryforward

The R4.2 validation-grade main-660 recovery is carried forward as evidence for
running R5, not as route promotion:

```text
fine_confirm_main660_fraction = 1.0
fine_confirm_sign_reliable_subset_fraction = 1.0
review_refined_main660_fraction = 1.0
fine_confirm_agrees_with_review_refined = 1.0
R4_2_gate_met = true
```

The coarse-screen near-wall conflict remains warning-only:

```text
coarse_screen_role = screening_only_warning
coarse_screen_can_confirm_or_demote_routes = false
coarse_screen_ranking_role = warning_only_not_rank_gate
R5_ranking_gate_uses_coarse_screen = false
```

## Route governance

Main-660 remains locked to:

```text
660 / 800x1400
660 / 800x1500
```

R5 output guardrails keep:

```text
context_route_promotion_authorized = false
main_660_redefinition_authorized = false
optional_660_900x1400_redefines_main_660 = false
route_specific_manual_sign_flip_applied = false
selected_annulus_replaces_all_crossing_ranking = false
```

The route-role stability table is descriptive evidence only. It does not
promote context routes and does not redefine main-660.

## Scenario sensitivity

The eight reviewed scenario bundles each contribute 32,032 rows:

```text
nominal_instrument_clean_blank
detector_50ohm_pessimistic
external_TIA_optimistic
blank_bursty_RIN_high
BFP_slit_offset_leakage
PEG_pessimistic_wall_loss
404_thermal_high_low_power
DAQ_low_resolution_sampling
```

The scenario manifest checksum recorded in the R5 manifest is:

```text
770eb4f59a2fe842c9cd014b50bd1a4a91f116266df49a10100738de3c452373
```

## Claim boundaries

Every R5 summary row preserves:

```text
SNR_claim_level = absolute_blocked
event_probability_claim_level = absolute_blocked
p_detect_mapping_claim_level = relative_with_priors
primary_metric = detectability_relative_prior_score
detected_events_source = relative_prior_score_proxy_count_not_observed_events
```

Exact legacy output headers are absent from all R5 CSV headers:

```text
detector_SNR
calibrated_detector_SNR
```

Guardrail fields with names such as
`legacy_detector_SNR_output_header_emitted` are allowed because they are
guardrail indicators, not legacy calibrated-output columns.

## Detector, blank, thermal, and unit guards

The detector/blank summary keeps:

```text
ET2030_BNC_direct_to_LI5640_current_input = forbidden
finite_monte_carlo_zero_event_inferred = false
false_positive_per_min_claim = analytic_prior_only
legacy_detector_SNR_output_header_emitted = false
legacy_calibrated_detector_SNR_output_header_emitted = false
calibrated_SNR_or_event_probability_claim_emitted = false
```

The thermal 404 sidecar remains non-enhancing:

```text
thermal_sidecar_does_not_increase_nodi_score = true
max_thermal_404_log_multiplier <= 0
thermal_sidecar_used_to_increase_NODI_score = false
thermal_404_claim_level = safety_sidecar
```

## Provenance freeze

R5 execution manifest records:

```text
base_v1_summary_checksum =
f7455efd4c4a48c817f9078a19f40b24668ac433ba7673a6352f35af55309d2c

R5_plan_yaml_checksum =
5fe1be0da5f072335e4e520e11a5f1f5fb310cb23d0d3b75f658869536614964

R5_plan_report_checksum =
76abc52a35d172187cf0839b173d6d856d92ae0334e5c608e097d128ec2230d7

R5_scenario_bundle_manifest_checksum =
770eb4f59a2fe842c9cd014b50bd1a4a91f116266df49a10100738de3c452373
```

## Next review boundary

The next action should be external review of R5 results. A clean R5 results
review may at most authorize preparation of a next-stage plan. It must not
authorize R6 execution, R5 follow-up expansion, route promotion, main-660
redefinition, selected-annulus changes, calibrated SNR, calibrated event
probability, absolute LOD, true EV concentration, or biological specificity.
