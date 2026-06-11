# Current Evidence State - Pre-3seed Logic Hardening

2026-06-12 supersession note: this file is historical pre-3seed evidence-state
provenance. It is not the current project conclusion. For the current no-data
closure, use `reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md`,
`reports/147_detector_forward_identity_full_chain_adversarial_audit_synthesis_20260610.md`,
and `reports/148_extreme_simulation_roadmap_post_audit_20260610.md`. Current
language is `candidate families under detector surrogate`: `404/W500`
fixed-view candidate plus `660/W800` per-wavelength-view candidate, with R1 and
C/D×V2 deferred outside the narrowed no-data sealing gate.

Generated: 2026-05-17T17:38:31+00:00

Project stance: no-measured-data relative/proxy design selection. The route
contracts below do not authorize calibrated SNR, LOD, detector voltage, photon
count, true detection probability, sample concentration, empirical blank safety,
biological exosome specificity, or calibrated cross-wavelength superiority.

## Route Contracts

- `historical_lens_A_10000e_v1`: lens `A`, stage `historical`, events `10000`, normalization `per_wavelength`, claim `historical_relative_proxy_evidence_only`.
- `lens_B_B7_fixed660_1000e_seed42`: lens `selected_annulus`, stage `B7`, events `1000`, normalization `fixed_660_gold`, claim `paper_reproduction_lens_b_frozen_parameter_full_1seed`.
- `pre3seed_candidate_freeze`: lens `diagnostic`, stage `new_preflight`, events `not_event_run`, normalization `not_applicable_candidate_manifest`, claim `preflight_governance_artifact`.
- `pre3seed_micro_smoke`: lens `diagnostic`, stage `new_preflight`, events `2`, normalization `per_wavelength`, claim `schema_reproducibility_smoke_only`.
- `pre3seed_reference_ablation`: lens `diagnostic`, stage `new_preflight`, events `not_event_run`, normalization `same_lens_same_normalization_only`, claim `recommendation_qualification_gate`.
- `pre3seed_detector_readout_ablation`: lens `diagnostic`, stage `new_preflight`, events `not_event_run`, normalization `same_lens_same_normalization_only`, claim `recommendation_qualification_gate`.
- `pre3seed_stability_synthesis`: lens `diagnostic`, stage `new_preflight`, events `not_event_run`, normalization `classification_from_same_scope_metrics`, claim `carry_forward_manifest_gate`.

## Claim-Level Counts

- `carry_forward_manifest_gate`: 1
- `historical_relative_proxy_evidence_only`: 1
- `paper_reproduction_lens_b_frozen_parameter_full_1seed`: 1
- `preflight_governance_artifact`: 1
- `recommendation_qualification_gate`: 2
- `schema_reproducibility_smoke_only`: 1

## Anti-Bias Guardrails Active

- Lens A, lens B, selected-annulus event-position window, and diagnostic tables
  are separate evidence scopes unless a table explicitly declares diagnostic
  comparison scope.
- B6/B7/historical/new-preflight rows are not one evidence tier.
- 1000e, 10000e, low-event smoke, and deterministic governance artifacts are
  not one confidence tier.
- Per-wavelength and fixed-660 normalization may be compared only in explicit
  comparison tables with normalization columns present.
- Legacy `detection_rate` columns are interpreted as conditional synthetic
  event detection fractions and must carry denominator and claim-boundary
  fields in preflight outputs.
- Selected-annulus always means an event-position window, not an optical BFP
  annulus.
