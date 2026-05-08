# EV/NODI realism v2 R5 Full-Grid v2 Plan For External Review

Date: 2026-05-07

Gate consumed:

```text
PASS_R4_2_RESULTS_PREPARE_R5_PLAN_ONLY
```

## Scope

This is an **R5 plan-only artifact**. It prepares a bounded full-grid v2 plan for
external review after R4.2 recovered locked main-660 at validation-grade mesh
levels.

It does **not** authorize R5 execution, full-grid v2 execution, route promotion,
main-660 redefinition, selected-annulus changes, calibrated SNR, calibrated event
probability, absolute LOD, true EV concentration, biological specificity, or
ET2030 direct current-input unlock.

## Source Inventory

R5 uses the existing v1 full-grid output only as a read-only route/case identity
inventory:

```text
source = results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv
rows = 32,032
route identities = 572
particle names = 56
source event metadata = 10,000e
v1 overwrite = forbidden
```

The exact legacy output headers are absent from the v1 source inventory:

```text
detector_SNR
calibrated_detector_SNR
```

## R4.2 Carryforward

R4.2 is carried into the R5 plan with the validation-grade conclusion only:

```text
fine_confirm_main660_fraction = 1.000000
fine_confirm_sign_reliable_subset_fraction = 1.000000
review_refined_main660_fraction = 1.000000
fine_confirm_agrees_with_review_refined = 1.000000
R4_2_gate_met = true
R4_2_recovery_decision =
  validation_grade_main660_recovered_prepare_R5_plan_review_only
```

The `coarse_screen` near-wall conflict is retained as:

```text
coarse_screen_role = screening_only_warning
coarse_screen_can_confirm_or_demote_routes = false
```

So R5 planning may carry the warning, but cannot use coarse-screen signs as
promotion or demotion evidence.

## Planned Case Cap

The R5 plan intentionally avoids stochastic seed expansion and Cartesian
uncertainty expansion. It uses the eight named scenario bundles already used in
the realism-v2 reduced-grid lane:

```text
v1 source rows = 32,032
named scenario bundles = 8
stochastic seeds = 0
planned case rows = 256,256
max case rows before review = 256,256
under_R5_review_cap = true
```

Any future R5 implementation that adds stochastic seeds, more scenario bundles,
or a Cartesian uncertainty grid must fail closed and return for review.

## Route Governance

Main-660 remains locked to:

```text
660 / 800x1400
660 / 800x1500
```

The R5 plan keeps these constraints:

```text
context_route_promotion_authorized = false
main_660_redefinition_authorized = false
optional_660_900x1400_redefines_main_660 = false
route_specific_manual_sign_flips_authorized = false
selected_annulus_replaces_all_crossing_ranking = false
```

Selected-annulus remains the unchanged `0.5-0.8` parallel diagnostic lens, not a
replacement for all-crossing ranking.

## Future R5 Outputs

If a later external review authorizes R5 execution, the run must write only:

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

Future output directory:

```text
results/ev_nodi_realism_v2_full_grid_R5_v2/
```

This plan bundle does not create that directory.

## Stop Gates

The machine-readable plan and validator require these stop gates:

```text
R5_execution_without_external_authorization
R5_case_rows_exceed_review_cap
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

## Claim Boundaries

R5 remains a relative-prior route/case expansion:

```text
SNR_claim_level = absolute_blocked
event_probability_claim_level = absolute_blocked
p_detect_mapping_claim_level = relative_with_priors
```

It cannot emit calibrated SNR, calibrated event probability, absolute LOD, true
EV concentration, or biological specificity claims.

## Provenance Freeze

The plan freezes source checksums for:

```text
base_v1_summary_checksum
R4_2_observable_summary_checksum
R4_2_main660_sign_summary_checksum
R4_2_mesh_role_summary_checksum
R4_2_guardrail_summary_checksum
R4_2_run_manifest_checksum
```

If a later review authorizes R5 execution, the future run manifest must also
record:

```text
R5_plan_yaml_checksum
R5_plan_report_checksum
```

## Review Question

The next external review should decide only whether this plan is tight enough to
authorize:

```text
PASS_TO_R5_FULL_GRID_V2_EXECUTION_ONLY
```

or whether it needs a fix-before-run gate. Passing this plan would authorize only
the capped R5 full-grid v2 execution described here, not route promotion,
calibrated claims, or any forbidden scope.
