# EV/NODI realism v2 R4.2 Main-660 Near-Wall Mesh Adjudication Analysis

Date: 2026-05-07

Gate applied:

```text
PASS_TO_R4_2_MAIN660_NEARWALL_MESH_ADJUDICATION_ONLY
```

## Scope

This is the capped R4.2 main-660 near-wall mesh adjudication result. It is not
an R5 plan, not R5 execution, and not a route-promotion artifact.

R4.2 was authorized only to adjudicate the residual revised-R4 failure cluster:

```text
660_800x1400 near_wall_stress coarse_screen: 10 fail
660_800x1500 near_wall_stress coarse_screen: 10 fail
```

The R4.2 run adds only `fine_confirm` solver cases for the two locked main-660
routes and compares them against the existing `review_refined` and
`coarse_screen` evidence.

## Case Scope

Executed scope:

```text
routes = 2
particles = 6 including optional blank
interface states = 2
polarization states = 2
new mesh levels = 1
solver case rows = 48
max solver cases before review = 64
under_R4_2_review_cap = true
```

Routes:

```text
660 / 800x1400 = main_660
660 / 800x1500 = main_660
```

New mesh role:

```text
fine_confirm = validation_grade_confirmation
```

Existing mesh roles carried forward:

```text
review_refined = validation_grade
coarse_screen = screening_only
```

No context, optional, 404, selected-annulus, or weak-reference route was added
to the R4.2 panel.

## Core Result

R4.2 passes the pre-registered validation-grade adjudication gate:

```text
fine_confirm_main660_fraction = 1.000000
fine_confirm_sign_reliable_subset_fraction = 1.000000
review_refined_main660_fraction = 1.000000
fine_confirm_agrees_with_review_refined = 1.000000
R4_2_gate_met = true
```

The recovery decision emitted by the runner is:

```text
validation_grade_main660_recovered_prepare_R5_plan_review_only
```

This means the coarse near-wall failure is now best treated as a
screening-grade conflict warning, not as validation-grade demotion evidence.

It does **not** authorize R5 execution. It also does not itself prepare an R5
plan. The strongest possible next review gate is only:

```text
PASS_R4_2_RESULTS_PREPARE_R5_PLAN_ONLY
```

## Mesh Adjudication

`mesh_level_role_adjudication_summary.csv` reports:

```text
coarse_screen:
  mesh_level_role = screening_only
  included_in_validation_grade_fraction = false
  can_confirm_or_demote_routes = false
  nonblank_rows = 40
  sign_preserved_fraction = 0.500000

review_refined:
  mesh_level_role = validation_grade
  included_in_validation_grade_fraction = true
  nonblank_rows = 40
  sign_preserved_fraction = 1.000000

fine_confirm:
  mesh_level_role = validation_grade_confirmation
  included_in_validation_grade_fraction = true
  nonblank_rows = 40
  sign_preserved_fraction = 1.000000
```

`coarse_screen_conflict_summary.csv` reports both routes as:

```text
coarse_screen_adjudication_outcome =
  coarse_screen_screening_artifact_warning
```

This is the intended R4.2 decision shape: coarse remains useful as a warning
surface but is no longer decision-grade evidence against main-660 when both
validation-grade meshes agree.

## Lobe, Mode, And ROI Diagnostics

The R4.2 output includes the pre-registered lobe/mode fields:

```text
BFP_lobe_left_cross_term_W
BFP_lobe_right_cross_term_W
BFP_lobe_inner_cross_term_W
BFP_lobe_outer_cross_term_W
even_mode_cross_term_W
odd_mode_cross_term_W
mode_overlap_complex
mode_overlap_phase_rad
mode_overlap_abs
lobe_balance_ratio
ROI_parity_sign
```

These remain diagnostic-only. The sign-preservation gate was not replaced by a
phase or complex-overlap metric.

## Guardrails

`R4_2_guardrail_summary.csv` keeps all hard stop gates clean:

```text
R5_plan_or_full_grid_v2_started = false
context_route_promotion_attempted = false
main_660_redefinition_attempted = false
route_specific_manual_sign_flip_attempted = false
selected_annulus_replaces_all_crossing_ranking = false
calibrated_SNR_or_event_probability_claim_emitted = false
ET2030_direct_current_input_unlocked_without_measured_bench_artifact = false
thermal_sidecar_used_to_increase_NODI_score = false
finite_zero_event_blank_safety_claim_emitted = false
legacy_detector_SNR_output_header_emitted = false
legacy_calibrated_detector_SNR_output_header_emitted = false
```

CSV output headers do not contain exact legacy names:

```text
detector_SNR
calibrated_detector_SNR
```

Claim levels remain blocked where required:

```text
SNR_claim_level = absolute_blocked
event_probability_claim_level = absolute_blocked
p_detect_mapping_claim_level = relative_with_priors
```

## Provenance Freeze

The R4.2 manifest records checksums for the source artifacts and plan:

```text
source_revised_R4_observable_summary_checksum
source_main660_ambiguity_check_checksum
source_route_validation_decision_table_checksum
R4_2_plan_yaml_checksum
R4_2_plan_report_checksum
solver_backend_version = 2026-05-07
```

This lets reviewers distinguish a solver/model change from source-artifact drift.

## Interpretation

R4.2 supports this narrow conclusion:

```text
The revised R4 main-660 failure was localized to coarse_screen near-wall rows.
When those rows are treated as screening-only and checked against
validation-grade review_refined plus fine_confirm evidence, locked main-660
passes the representative sign-preservation adjudication gate.
```

This conclusion supports preparing an R5 plan for external review only. It does
not authorize R5 execution, context-route promotion, main-660 redefinition, or
any calibrated detector/event-probability claim.

## Required Next Review Boundary

The external review should decide only whether R4.2 results support:

```text
PASS_R4_2_RESULTS_PREPARE_R5_PLAN_ONLY
```

Still forbidden:

```text
R5 full-grid v2 execution
v1 full-grid overwrite
Tsuyama paper-fit continuation
selected-annulus bound changes
selected-annulus replacing all-crossing ranking
context-route promotion
main-660 redefinition
660 / 900x1400 redefining main-660
route-specific manual sign flips
calibrated SNR
calibrated event probability
absolute LOD
true EV concentration
biological specificity
ET2030 direct current-input unlock
thermal sidecar increasing NODI score
finite-zero-event blank safety claim
legacy detector_SNR / calibrated_detector_SNR output headers
```
