# EV/NODI realism v2 R4 Revised Rerun Plan For External Review

Date: 2026-05-07

Gate applied:

```text
PASS_ROUTE_MODEL_AUDIT_PREPARE_REVISED_R4_RERUN_PLAN_ONLY
```

## Scope

This is a revised R4 rerun plan only. It does not execute revised R4, does not
prepare R5, and does not authorize route promotion or route-role changes.

The accepted route-model revision audit found a strong global sign-convention
signal:

```text
best_allowed_convention_id = global_full_wave_cross_term_sign_flip
all nonblank sign preserved fraction = 0.861111
```

But it did not recover locked main-660:

```text
main_660 nonblank sign preserved fraction = 0.750000
main_660 recovery threshold = 0.800000
main_660_recovery_gate_met = false
```

Therefore R5 remains blocked. The next reviewed action can only be a revised
R4 rerun plan that tests whether the residual main-660 failure is a convention
mapping problem, a near-wall/coarse-screen numerical sign ambiguity, or a true
route-model failure.

The machine-readable plan is:

```text
configs/realism_v2/r4_revised_rerun_plan.yaml
schema_version = R4_revised_rerun_plan_v1
stage = R4_revised_rerun_plan_only
```

## Authorization Boundary

Authorized now:

```text
Prepare revised R4 rerun plan only
```

Not authorized:

```text
revised R4 rerun execution
R5 plan preparation
R5 full-grid v2
v1 full-grid overwrite
Tsuyama paper-fit continuation
selected-annulus bound changes
selected-annulus replacing all-crossing ranking
context-route promotion
main-660 redefinition
660 / 900x1400 redefining main-660
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

## Evidence Consumed

Accepted audit decision:

```text
PASS_ROUTE_MODEL_AUDIT_PREPARE_REVISED_R4_RERUN_PLAN_ONLY
```

Audit result consumed:

```text
route_model_revision_audit_decision =
  partial_convention_signal_but_main_660_recovery_gate_not_met
```

Source R4 evidence remains:

```text
full_wave_observable_summary.csv rows = 432
route_validation_decision_table.csv rows = 9
R4 route decisions = 9 / 9 demote_from_R4_candidate
```

## Revised R4 Panel

The rerun plan keeps the same nine representative R4 routes:

| route | role | purpose |
|---|---|---|
| 660 / 800x1400 | main_660 | main route recovery under fixed sign convention |
| 660 / 800x1500 | main_660 | stronger main route recovery under refined/reliable sign checks |
| 660 / 900x1400 | optional_robustness_probe | optional probe only, not main-660 |
| 532 / 900x1500 | context_validation_candidate | context route remains diagnostic |
| 660 / 900x1500 | context_validation_candidate | wide/deep longwave context sanity |
| 532 / 800x1500 | context_validation_candidate | context/main bridge route |
| 404 / 600x1300 | shortwave_mechanism_candidate | optical mechanism, thermal sidecar cannot add score |
| 404 / 800x600 | selected_annulus_sanity_overlap_shortwave | selected-annulus diagnostic only |
| 660 / 800x600 | selected_annulus_sanity_overlap_longwave | selected-annulus diagnostic only |

The particle panel remains the original six representative R4 particles:

```text
blank
EV70_lowRI
EV100_nominal
EV250_nominal
LDL_like_contaminant
Au40
```

The solver-case cap remains:

```text
9 routes * 6 particles * 2 interface states * 2 polarization states * 2 mesh levels = 432
```

No R5 or hidden full-grid expansion is allowed.

## Sign Convention Contract

The canonical convention is fixed as:

```text
Delta_P_NODI = |E_ref + E_sca|^2 - |E_ref|^2
             = |E_sca|^2 + 2*Re(E_ref*conj(E_sca))
```

The ROI cross-term operator is:

```text
2*Re(integral_ROI(E_ref*conj(E_sca)*W*Jacobian du dv))
```

The revised R4 output must explicitly map these possible polarity sources:

```text
full_wave_cross_term_signed_W convention mismatch
surrogate_cross_term_signed_W convention mismatch
ROI perturbation sign convention mismatch
BFP coordinate orientation mismatch
complex harmonic time convention mismatch
```

A global flip is not recovery by itself. Recovery requires passing the
pre-registered main-660 gates below.

## Main-660 Residual Failure Diagnostic

The accepted audit showed that after the global full-wave cross-term sign flip,
main-660 residual failures were not random. All 20 failures were localized to:

```text
660_800x1400 near_wall_stress coarse_screen: 10 fail
660_800x1500 near_wall_stress coarse_screen: 10 fail
```

The revised R4 plan therefore requires:

```text
main_660_near_wall_coarse_sign_ambiguity_check
```

Required fields:

```text
route_id
interface_state
mesh_level
particle_id
full_wave_cross_term_signed_W
surrogate_cross_term_signed_W
abs_full_wave_cross_term_W
abs_surrogate_cross_term_W
sign_reliability_band
sign_preserved_raw
sign_preserved_after_global_flip
sign_ambiguous_due_to_near_zero
mesh_refined_agreement
near_wall_stress_agreement
```

This diagnostic cannot retroactively change the accepted audit decision. It can
only be used in a future revised R4 result review.

## Sign Reliability

The revised R4 plan pre-registers:

```text
sign_reliable =
  abs(full_wave_cross_term_signed_W) >= max(
    absolute_floor_W,
    relative_floor * median_abs_full_wave_cross_term_for_route_particle
  )
```

with:

```text
absolute_floor_W = 1.0e-19
relative_floor = 0.05
```

Sign reliability bands:

```text
reliable
near_zero_ambiguous
blank_excluded
```

Blank rows remain excluded from recovery gates.

## Recovery Criteria

The revised R4 results can only support a future R5 plan review if all of these
pre-registered conditions pass:

```text
main_660_nonblank_after_global_convention >= 0.8
main_660_sign_reliable_subset >= 0.8
main_660_review_refined_mesh >= 0.8
no route-role change
no context-route promotion
future external review before R5 plan
```

The strongest possible future gate after successful revised R4 results is:

```text
PASS_REVISED_R4_RESULTS_PREPARE_R5_PLAN_ONLY
```

This plan does not authorize that gate. It only defines what a later result
review would need to see.

## Required Outputs If Separately Authorized

If an external review later authorizes revised R4 execution, it must produce
only:

```text
revised_full_wave_case_manifest.csv
revised_full_wave_observable_summary.csv
cross_term_convention_resolution_summary.csv
main_660_near_wall_coarse_sign_ambiguity_check.csv
sign_reliability_band_summary.csv
review_refined_mesh_confirmation_summary.csv
BFP_ROI_orientation_sanity_summary.csv
route_validation_decision_table.csv
revised_R4_guardrail_summary.csv
full_wave_cost_estimate.csv
run_manifest.json
R4_revised_rerun_plan_report.md
```

## Stop Gates

The plan fails closed if any of these occur:

```text
R5_plan_or_full_grid_v2_started
revised_R4_rerun_executed_without_external_authorization
v1_full_grid_output_overwritten
Tsuyama_paper_fit_continued
selected_annulus_bounds_changed
selected_annulus_replaces_all_crossing_ranking
context_route_promotion_attempted
main_660_redefinition_attempted
calibrated_SNR_or_event_probability_claim_emitted
ET2030_direct_current_input_unlocked_without_measured_bench_artifact
thermal_sidecar_used_to_increase_NODI_score
finite_zero_event_blank_safety_claim_emitted
legacy_detector_SNR_output_header_emitted
legacy_calibrated_detector_SNR_output_header_emitted
```

## Review Request

The external review should decide only whether this plan is tight enough to
authorize revised R4 rerun execution. It should not authorize R5 plan
preparation or R5 execution.
