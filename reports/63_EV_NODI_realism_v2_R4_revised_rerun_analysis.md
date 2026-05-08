# EV/NODI realism v2 R4 Revised Rerun Analysis

Date: 2026-05-07

Gate applied:

```text
PASS_TO_REVISED_R4_RERUN_ONLY
```

## Scope

This is the capped revised R4 rerun only. It is not R5 plan preparation, not
R5 full-grid-v2 execution, and not route promotion.

Authorized panel:

```text
routes = 9
particles = 6
interface states = 2
polarization states = 2
mesh levels = 2
solver case rows = 432
```

Output directory:

```text
results/ev_nodi_realism_v2_revised_R4_rerun/
```

## Main Result

The revised rerun locked the canonical cross-term convention:

```text
Delta_P_NODI = |E_ref + E_sca|^2 - |E_ref|^2
             = |E_sca|^2 + 2*Re(E_ref*conj(E_sca))
```

and applied the accepted global full-wave cross-term sign mapping:

```text
best_allowed_convention_id = global_full_wave_cross_term_sign_flip
```

The global convention signal remains strong:

```text
all_nonblank_sign_preserved_after_global_flip = 0.861111
```

But locked main-660 still does not pass the pre-registered recovery gate:

```text
main_660_nonblank_sign_preserved_after_global_flip = 0.750000
main_660_sign_reliable_subset_fraction = 0.756757
main_660_review_refined_mesh_fraction = 1.000000
main_660_recovery_gate_met = false
```

Therefore:

```text
revised_R4_recovery_decision =
  main_660_recovery_gate_not_met_R5_blocked
```

## Interpretation

The revised rerun confirms that the previous all-route R4 demotion was strongly
affected by a global cross-term polarity convention mismatch. However, the
pre-registered main-660 recovery gate still fails because the sign-reliable
subset remains below 0.8.

The most informative nuance is:

```text
main_660_review_refined_mesh_fraction = 1.0
```

So the residual main-660 problem is concentrated in coarse near-wall screening
conditions, not in review-refined mesh rows. But the sign-reliable subset is
still below threshold:

```text
0.756757 < 0.8
```

That means this result should not support R5 plan preparation yet. It supports
a narrower conclusion: the canonical sign convention is likely correct, but the
main-660 near-wall/coarse-screen decision rule still needs reviewed treatment
before R5 planning can be considered.

## Main-660 Near-Wall/Coarse Diagnostic

The required diagnostic output:

```text
main_660_near_wall_coarse_sign_ambiguity_check.csv
```

contains 80 nonblank main-660 rows. After the global convention, the remaining
20 failures are exactly:

```text
660_800x1400 near_wall_stress coarse_screen: 10 fail
660_800x1500 near_wall_stress coarse_screen: 10 fail
```

Near-zero ambiguous rows:

```text
660_800x1400: 2
660_800x1500: 4
```

The output includes the extra reviewability columns requested by external
review:

```text
median_abs_full_wave_cross_term_for_route_particle
sign_reliability_threshold_W
sign_reliability_threshold_source
```

## Route Decisions

Route-level revised decisions:

```text
confirm_for_future_review = 4
inconclusive_requires_plan_revision = 5
demote_from_R4_candidate = 0
reclassify_requires_external_review = 0
```

Both locked main-660 routes remain:

```text
final_route_validation_decision = inconclusive_requires_plan_revision
main_660_recovery_gate_met = false
```

Context-route promotion remains forbidden even where context routes confirm for
future review.

## Guardrails

Guardrails remain fail-closed:

```text
R5_plan_preparation_authorized = false
R5_full_grid_v2_run = false
v1_full_grid_overwritten = false
Tsuyama_paper_fit_continued = false
selected_annulus_bounds_changed = false
selected_annulus_replaces_all_crossing_ranking = false
context_route_promotion_authorized = false
main_660_redefinition_authorized = false
calibrated_SNR_claim_emitted = false
ET2030_direct_current_input_unlocked = false
thermal_sidecar_used_to_increase_NODI_score = false
finite_zero_event_blank_safety_claim_emitted = false
legacy_detector_SNR_output_header_emitted = false
legacy_calibrated_detector_SNR_output_header_emitted = false
```

Exact forbidden output headers are absent from revised R4 CSV outputs:

```text
detector_SNR
calibrated_detector_SNR
```

## Required Review Decision

This revised R4 rerun should not be read as an R5 pass. The main-660 refined
mesh result is encouraging, but the pre-registered sign-reliable gate still
fails.

The external review should decide whether this is:

```text
CONDITIONAL_FIX_REVISED_R4_RESULTS_BEFORE_R5_PLAN
```

or a stronger route-model revision requirement. It should not authorize R5 plan
preparation unless it explicitly accepts the failed sign-reliable subset gate,
which would contradict the pre-registered plan.
