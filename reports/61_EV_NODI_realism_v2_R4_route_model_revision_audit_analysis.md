# EV/NODI realism v2 R4 Route-Model Revision Audit Analysis

Date: 2026-05-07

Gate applied:

```text
PASS_TO_ROUTE_MODEL_REVISION_AUDIT_ONLY
```

## Scope

This is a bounded sign/phase/model audit. It is not an R5 plan and not an R5
full-grid-v2 run.

Inputs:

```text
results/ev_nodi_realism_v2_representative_full_wave_R4/full_wave_observable_summary.csv
results/ev_nodi_realism_v2_representative_full_wave_R4/route_validation_decision_table.csv
configs/realism_v2/r4_route_model_revision_plan.yaml
```

Source R4 evidence:

```text
R4 representative routes = 9
R4 observable rows = 432
R4 route decisions = all 9 demote_from_R4_candidate
main_660_validated = false
```

Outputs:

```text
results/ev_nodi_realism_v2_route_model_revision_audit/
```

## Audit Question

The audit asks whether the all-route R4 demotion is recoverable as a single
pre-registered cross-term / sign / phase convention mismatch, or whether the
current route model must remain blocked before any R5 planning.

The pre-registered identity remains:

```text
|E_ref + E_sca|^2 - |E_ref|^2 =
  2*Re(E_ref*conj(E_sca)) + |E_sca|^2
```

and the ROI cross-term operator is:

```text
2*Re(integral_ROI(E_ref*conj(E_sca)*W*Jacobian du dv))
```

Blank rows are excluded from recovery gate numerators and denominators because
zero signal trivially preserves sign.

## Main Result

The best single global convention was:

```text
best_allowed_convention_id = global_full_wave_cross_term_sign_flip
```

It substantially improves nonblank sign preservation:

```text
as_recorded_cross_term:
  all nonblank sign preserved fraction = 0.138889
  main_660 nonblank sign preserved fraction = 0.250000

global_full_wave_cross_term_sign_flip:
  all nonblank sign preserved fraction = 0.861111
  main_660 nonblank sign preserved fraction = 0.750000
```

However, the pre-registered main-660 recovery threshold is:

```text
min_main_660_nonblank_sign_preserved_fraction_for_recovery = 0.800000
```

Therefore:

```text
main_660_recovery_gate_met = false
route_model_revision_audit_decision =
  partial_convention_signal_but_main_660_recovery_gate_not_met
```

## Interpretation

The audit found a real global convention signal: flipping the full-wave
cross-term sign raises all-route nonblank sign preservation from about 0.139 to
about 0.861. That is too structured to ignore.

But it does not clear the main-660 recovery gate. The locked main-660 nonblank
fraction reaches only 0.75, below the required 0.8 threshold. That means the
audit does not justify R5 plan preparation. It supports a narrower conclusion:
the sign/phase convention should be revised or investigated further, then a
future reviewed R4-style evidence pass is required before R5 planning can be
considered.

## Route Governance

No route role changes were made:

```text
context_route_promotion_authorized = false
main_660_redefinition_authorized = false
660 / 900x1400 redefining main_660 = false
selected_annulus_replaces_all_crossing_ranking = false
```

Selected-annulus sanity routes remain diagnostic only. The 404 route remains a
shortwave mechanism/safety interpretation route and does not gain a score from
the thermal sidecar.

## Guardrails

The audit preserves the standing guardrails:

```text
R5_plan_preparation_authorized = false
R5_full_grid_v2_run = false
v1_full_grid_overwritten = false
Tsuyama_paper_fit_continued = false
selected_annulus_bounds_changed = false
calibrated_SNR_claim_emitted = false
ET2030_direct_current_input_unlocked = false
thermal_sidecar_used_to_increase_NODI_score = false
finite_zero_event_blank_safety_claim_emitted = false
legacy_detector_SNR_output_header_emitted = false
legacy_calibrated_detector_SNR_output_header_emitted = false
```

The result CSV headers do not contain:

```text
detector_SNR
calibrated_detector_SNR
```

All audit outputs carry the required realism-v2 provenance fields.

## Required Review Decision

This audit should not be read as a pass to R5. The most direct decision to ask
external review is whether the audit evidence supports:

```text
CONDITIONAL_ROUTE_MODEL_REVISION_REQUIRED_BEFORE_R4_RERUN
```

or a stronger halt. Any future recovery must still pass a reviewed R4-style
rerun before R5 plan preparation.
