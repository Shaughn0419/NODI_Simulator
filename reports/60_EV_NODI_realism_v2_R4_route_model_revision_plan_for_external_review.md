# EV/NODI realism v2 R4 Route-Model Revision Plan For External Review

Date: 2026-05-07

Gate applied:

```text
PASS_R4_NUMERICAL_RERUN_HALT_R5_PLAN_ROUTE_MODEL_REVISION_ONLY
```

## Scope

This is a route-model revision plan only. It is not an R5 plan, not an R5
full-grid-v2 run, and not a route-promotion proposal.

The triggering R4 evidence is negative for the current route model:

```text
confirm_for_future_review = 0
demote_from_R4_candidate = 9
reclassify_requires_external_review = 0
inconclusive_requires_plan_revision = 0
```

Both locked main-660 routes demoted:

```text
660 / 800x1400 -> demote_from_R4_candidate
660 / 800x1500 -> demote_from_R4_candidate
```

Therefore R5 planning remains blocked. The next scientific question is whether
the all-route demotion is a true physical sign/phase reversal of the surrogate,
or a convention mismatch between the R3/R4 scalar surrogate and the R4
channel-modal Green-function solver.

## Authorization Boundary

Authorized now:

```text
Prepare route-model revision plan only
```

Not authorized:

```text
route-model revision execution
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

The machine-readable plan is:

```text
configs/realism_v2/r4_route_model_revision_plan.yaml
schema_version = R4_route_model_revision_plan_v1
stage = R4_route_model_revision_plan_only
```

## Demoted Route Panel

The revision plan covers exactly the nine R4 representative routes, all carrying
`R4_final_route_validation_decision = demote_from_R4_candidate`:

| route | role | revision question |
|---|---|---|
| 660 / 800x1400 | main_660 | convention mismatch or physical phase reversal |
| 660 / 800x1500 | main_660 | recoverable under one pre-registered cross-term polarity |
| 660 / 900x1400 | optional_robustness_probe | same failure as main-660 without redefining main-660 |
| 532 / 900x1500 | context_validation_candidate | surrogate polarity, modal phase, or route-specific BFP sign |
| 660 / 900x1500 | context_validation_candidate | main-660 sign failure or separate wide/deep issue |
| 532 / 800x1500 | context_validation_candidate | context/main bridge for BFP sign mapping |
| 404 / 600x1300 | shortwave_mechanism_candidate | optical failure independent of thermal sidecar |
| 404 / 800x600 | selected_annulus_sanity_overlap_shortwave | diagnostic-only polarity issue |
| 660 / 800x600 | selected_annulus_sanity_overlap_longwave | all-crossing vs selected-annulus sign interpretation |

Route roles remain locked. Context-route promotion remains false.

## Revision Focus

Required focus areas:

```text
cross_term_sign_convention
reference_phase_convention
Re_Eref_conj_Esca_polarity_mapping
BFP_ROI_sign_preservation
surrogate_scalar_vs_modal_sign_mapping
main_660_route_role_recovery_criteria
404_and_selected_annulus_sanity_interpretation
```

This is deliberately a sign/phase/model-governance review. It is not a
combinatorial route search or full-grid expansion.

## Sign/Phase Audit Contract

The pre-registered identity is:

```text
|E_ref + E_sca|^2 - |E_ref|^2 =
  2*Re(E_ref*conj(E_sca)) + |E_sca|^2
```

The cross-term operator is:

```text
2*Re(integral_ROI(E_ref*conj(E_sca)*W*Jacobian du dv))
```

The audit must preserve common global phase invariance:

```text
E_ref -> E_ref * exp(i phi)
E_sca -> E_sca * exp(i phi)
cross-term and decision must not change
```

Allowed hypotheses:

```text
convention_mismatch
true_physical_phase_reversal
route_specific_BFP_ROI_polarity
scalar_surrogate_lost_complex_phase
```

Forbidden hypotheses:

```text
posthoc_route_promotion
main_660_redefinition
selected_annulus_replaces_all_crossing
calibrated_probability_or_SNR_claim
```

## Recovery Gates

R5 planning remains blocked unless a later external review explicitly changes
that status. Even if a convention mismatch is found, the next step would be a
new reviewed R4-style evidence pass, not R5.

Minimum recovery gate:

```text
min_main_660_nonblank_sign_preserved_fraction_for_recovery >= 0.8
future_R4_rerun_required_before_R5_plan = true
context_route_promotion_authorized = false
main_660_redefinition_authorized = false
```

Interpretation bins:

```text
confirm_convention_mismatch:
  one pre-registered cross-term convention restores main-660 nonblank sign
  preservation without magnitude/rank posthoc tuning

halt_route_model:
  all allowed sign conventions keep main-660 nonblank sign preservation below 0.5
  or require context-route promotion

inconclusive:
  recovery depends on route-specific manual sign flips or unregistered ROI polarity
```

## Future Outputs If Separately Authorized

If an external review later authorizes route-model revision execution, the
required outputs are:

```text
route_model_revision_audit_manifest.csv
cross_term_sign_convention_audit.csv
reference_phase_convention_audit.csv
BFP_ROI_sign_preservation_audit.csv
surrogate_scalar_vs_modal_mapping_audit.csv
main_660_recovery_gate_summary.csv
404_selected_annulus_sanity_interpretation_summary.csv
route_model_revision_decision_table.csv
route_model_revision_guardrail_summary.csv
run_manifest.json
R4_route_model_revision_report.md
```

No full-grid output is allowed in this list.

## Stop Gates

The plan fails closed if any of these occur:

```text
R5_plan_or_full_grid_v2_started
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

## Active Tests

The plan is enforced by:

```text
tests/test_realism_v2_route_model_revision_plan.py
```

The tests check that the plan is plan-only, consumes the accepted all-demoted
R4 evidence, covers all nine R4 representative routes, defines the cross-term
identity, blocks R5 planning, requires future R4 evidence before R5 planning,
and fails closed if required stop gates are removed.

## Final Planning Position

R4 numerical evidence passed as evidence, but that evidence is negative for the
current route model. The next review should decide whether this route-model
revision plan is tight enough to authorize a bounded sign/phase audit. It should
not authorize R5 planning or execution.
