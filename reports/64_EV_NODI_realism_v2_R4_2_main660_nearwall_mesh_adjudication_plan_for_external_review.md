# EV/NODI realism v2 R4.2 Main-660 Near-Wall Mesh Adjudication Plan For External Review

Date: 2026-05-07

Gate applied:

```text
FAIL_REVISED_R4_RESULTS_RERUN_OR_ROUTE_MODEL_REVISION_REQUIRED
```

## Scope

This is an R4.2 adjudication plan only. It does not execute R4.2, does not
prepare R5, and does not authorize route promotion, main-660 redefinition, or
any calibrated claim.

The revised R4 rerun preserved a strong global cross-term convention signal:

```text
all_nonblank_sign_preserved_after_global_flip = 0.861111
```

But the pre-registered main-660 recovery gate did not pass:

```text
main_660_nonblank_sign_preserved_after_global_flip = 0.750000
main_660_sign_reliable_subset_fraction = 0.756757
main_660_review_refined_mesh_fraction = 1.000000
main_660_recovery_gate_met = false
```

The residual failures are not diffuse. They are localized to:

```text
660_800x1400 near_wall_stress coarse_screen: 10 fail
660_800x1500 near_wall_stress coarse_screen: 10 fail
```

Therefore R5 remains blocked. The narrow next question is whether
`coarse_screen` should remain decision-grade or be demoted to a screening-only
diagnostic when `review_refined` and a new `fine_confirm` mesh agree.

The machine-readable plan is:

```text
configs/realism_v2/r4_2_main660_nearwall_mesh_adjudication_plan.yaml
schema_version = R4_2_main660_nearwall_mesh_adjudication_plan_v1
stage = R4_2_main660_nearwall_mesh_adjudication_plan_only
```

## Authorization Boundary

Authorized now:

```text
Prepare R4.2 main-660 near-wall mesh-adjudication plan only
```

Not authorized:

```text
R4.2 execution
R5 plan preparation
R5 full-grid v2
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

## R4.2 Route And Particle Scope

R4.2 is intentionally smaller than the revised 432-case R4 rerun. It is limited
to the two locked main-660 routes:

| route | role | question |
|---|---|---|
| 660 / 800x1400 | main_660 | Does fine-confirm agree with review-refined rather than the coarse near-wall failure? |
| 660 / 800x1500 | main_660 | Does the stronger main route pass under validation-grade mesh evidence? |

Required nonblank particles:

```text
EV70_lowRI
EV100_nominal
EV250_nominal
LDL_like_contaminant
Au40
```

Optional blank rows may be included for guardrail continuity, but blank rows
remain excluded from recovery gates.

## Solver Scope And Cap

R4.2 adds only a new validation-grade confirmation mesh:

```text
new_mesh_levels = fine_confirm
```

The planned new solver cases are:

```text
2 routes * 6 particles * 2 interface states * 2 polarization states * 1 new mesh
= 48 new solver cases
```

The review cap is:

```text
max_R4_2_solver_cases_before_review = 64
```

No additional route, particle, scenario, or full-grid expansion is allowed.

Mesh roles are pre-registered:

```text
coarse_screen = screening_only
review_refined = validation_grade
fine_confirm = validation_grade_confirmation
```

This is the core adjudication boundary: coarse-screen failures can create a
warning, but they cannot by themselves confirm or demote a route.

## Adjudication Question

Primary question:

```text
does_fine_confirm_agree_with_review_refined_or_coarse_screen_for_main660_near_wall_sign
```

If `fine_confirm` agrees with `review_refined`, the coarse near-wall failure may
be treated as a screening artifact in a later external result review.

If `fine_confirm` agrees with the coarse-screen failure, main-660 remains
unresolved and R5 remains blocked.

If lobe, mode, or ROI parity diagnostics disagree, the route-model or ROI
operator requires another revision.

Route-specific manual sign flips are forbidden. A passing result must be
explained by one global convention plus validation-grade numerical evidence.

## Required Diagnostics

R4.2 must preserve route-level signed observables and add lobe/mode diagnostics:

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

Phase and complex-overlap diagnostics are allowed only as diagnostics. They do
not replace the sign-preservation gate.

The main-660 cluster output must include sign-reliability transparency fields:

```text
median_abs_full_wave_cross_term_for_route_particle
sign_reliability_threshold_W
sign_reliability_threshold_source
sign_reliability_band
```

## Decision Criteria For A Future Result Review

A future R4.2 result can support, at most, preparing an R5 plan only if all of
these pre-registered conditions pass:

```text
fine_confirm_main660_fraction >= 0.8
review_refined_main660_fraction >= 0.8
fine_confirm_agrees_with_review_refined >= 0.9
no route-role change
no context-route promotion
no main-660 redefinition
no route-specific manual sign flip
external review before R5 plan
```

The strongest possible future gate after successful R4.2 results is:

```text
PASS_R4_2_RESULTS_PREPARE_R5_PLAN_ONLY
```

That gate would still not authorize R5 execution.

## Required Outputs If Separately Authorized

If a later external review authorizes R4.2 execution, the run must produce only:

```text
R4_2_case_manifest.csv
R4_2_observable_summary.csv
main660_fine_confirm_sign_summary.csv
mesh_level_role_adjudication_summary.csv
BFP_lobe_resolved_cross_term_summary.csv
mode_overlap_phase_summary.csv
ROI_parity_sanity_summary.csv
coarse_screen_conflict_summary.csv
R4_2_guardrail_summary.csv
R4_2_cost_estimate.csv
run_manifest.json
R4_2_main660_nearwall_mesh_adjudication_report.md
```

## Stop Gates

The plan fails closed if any of these occur:

```text
R5_plan_or_full_grid_v2_started
R4_2_execution_without_external_authorization
v1_full_grid_output_overwritten
Tsuyama_paper_fit_continued
selected_annulus_bounds_changed
selected_annulus_replaces_all_crossing_ranking
context_route_promotion_attempted
main_660_redefinition_attempted
route_specific_manual_sign_flip_attempted
calibrated_SNR_or_event_probability_claim_emitted
ET2030_direct_current_input_unlocked_without_measured_bench_artifact
thermal_sidecar_used_to_increase_NODI_score
finite_zero_event_blank_safety_claim_emitted
legacy_detector_SNR_output_header_emitted
legacy_calibrated_detector_SNR_output_header_emitted
```

## Review Request

The external review should decide only whether this plan is tight enough to
authorize R4.2 main-660 near-wall mesh adjudication. It should not authorize R5
plan preparation or R5 execution.
