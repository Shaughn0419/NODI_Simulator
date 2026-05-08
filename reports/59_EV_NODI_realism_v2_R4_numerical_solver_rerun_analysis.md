# EV/NODI realism v2 R4 Numerical Solver Rerun Analysis

Date: 2026-05-07

Gate applied: `FAIL_R4_RESULTS_RERUN_REQUIRED_WITH_NUMERICAL_SOLVER`

## Scope

This rerun stays inside the previously authorized R4 representative panel:

- Routes: 9
- Particles: 6
- Interface states: 2
- Polarization states: 2
- Mesh levels: 2
- Solver case rows: 432 / 432 cap
- Output directory: `results/ev_nodi_realism_v2_representative_full_wave_R4/`

R5 full-grid v2 was not run. v1 full-grid outputs were not overwritten. Tsuyama paper-fit work was not continued. Selected-annulus bounds were not changed.

## Solver Backend

The proxy audit path has been replaced for this rerun. The active R4 backend is:

```text
solver_engine_class = FEM_modal_equivalent
solver_name_or_backend = internal_channel_modal_green_BFP_R4_v2
solver_backend_version = 2026-05-07
solver_execution_mode = numerical_full_wave_backend
solver_case_completed = true for all 432 cases
```

This is an internal channel modal/Green-function solver, not a packaged FDTD call. It computes the channel reference field and particle scattering field from the same glass/water Robin-boundary modal basis, particle material contract, interface state, polarization state, mesh/modal order, source normalization, and BFP/slit operator. Each case records a `solver_output_checksum`, material record, source normalization record, BFP/ROI extraction record, mesh/modal record, boundary-condition record, and solver call path.

The route decisions are computed only from `solver_case_completed = true` rows. Proxy-only values are excluded from route decisions.

## R4 Route Decisions

Route-level decision counts:

- `confirm_for_future_review`: 0
- `demote_from_R4_candidate`: 9
- `reclassify_requires_external_review`: 0
- `inconclusive_requires_plan_revision`: 0

Route outcomes:

```text
660 / 800x1400  main_660                                  demote_from_R4_candidate
660 / 800x1500  main_660                                  demote_from_R4_candidate
660 / 900x1400  optional_robustness_probe                 demote_from_R4_candidate
532 / 900x1500  context_validation_candidate              demote_from_R4_candidate
660 / 900x1500  context_validation_candidate              demote_from_R4_candidate
532 / 800x1500  context_validation_candidate              demote_from_R4_candidate
404 / 600x1300  shortwave_mechanism_candidate             demote_from_R4_candidate
404 / 800x600   selected_annulus_sanity_overlap_shortwave demote_from_R4_candidate
660 / 800x600   selected_annulus_sanity_overlap_longwave  demote_from_R4_candidate
```

These are validation labels only. Context-route promotion, main-660 redefinition, and selected-annulus ranking replacement remain forbidden.

## Guardrails

The R4 outputs preserve the R0/R1.5/R2/R3 guardrails:

- `SNR_claim_level = absolute_blocked` for all observable rows
- `event_probability_claim_level = absolute_blocked` for all observable rows
- `p_detect_mapping_claim_level = relative_with_priors`
- Exact legacy headers `detector_SNR` and `calibrated_detector_SNR` are absent
- Context-route promotion is not authorized
- Main-660 redefinition is not authorized
- `660 / 900x1400` does not redefine main-660
- Selected-annulus routes remain sanity diagnostics only
- ET2030 BNC direct-to-LI5640 current input remains forbidden
- Blank false-positive handling remains analytic/semi-analytic; no finite zero-event safety claim
- Thermal sidecar does not increase NODI score

## Manifest Boundary

Both root and R4 result manifests record:

- `R4_representative_full_wave_validation_run = true`
- `R5_full_grid_v2_run = false`
- `v1_full_grid_overwritten = false`
- `Tsuyama_paper_fit_continued = false`
- `selected_annulus_bounds_changed = false`
- `calibrated_SNR_claim_emitted = false`
- `ET2030_direct_current_input_unlocked = false`

## Interpretation

The numerical R4 rerun no longer relies on `backend_unavailable_contract_proxy`. It produces solver-completed rows under a bounded internal channel modal/Green-function backend and records per-case provenance. Under the registered sign-preservation decision rule, all nine representative routes demote from the R4 candidate set. This should be treated as a possible halt or route-model revision signal, not as evidence for R5/full-grid-v2 planning.

This supports external review of the R4 numerical-rerun evidence. It does not authorize R5 execution or R5 plan preparation unless a new external review explicitly decides otherwise.
