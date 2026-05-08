# EV/NODI Realism v2 R3 Reduced-Grid Plan for External Review

Date: 2026-05-06

## Scope

This is a plan for the next external review. It is not an R3 execution report.

Current gate status:

```text
R0/P0/P0.5 implemented and tested
R1.5 micro-anchor regenerated after reference-power semantics fix
R2 anchor smoke passed model-fix review
R2 adaptive 10k rerun not needed
R3 reduced grid not run
R4 representative full-wave validation not run
R5 full-grid v2 not run
```

The requested next authorization should be limited to **R3a reduced-grid
named-bundle survey only**. It should not authorize R4 or R5.

## Carry-Forward Constraints

The following constraints remain active:

```text
Do not overwrite v1 full-grid outputs.
Do not continue Tsuyama paper-fit.
Do not change selected-annulus 0.5-0.8 bounds.
Do not replace all-crossing main ranking with selected-annulus ranking.
Do not export detector_SNR or calibrated_detector_SNR.
Do not claim calibrated absolute SNR without measured detector transfer and measured blank artifacts.
Do not unlock ET2030 direct current-input without real measured/calibrated bench validation artifact.
Do not treat relative-prior detectability as calibrated event probability.
```

## R2 Evidence That Motivates R3a Planning

GPT-Pro returned:

```text
PASS_R2_MODEL_FIX_NO_ADAPTIVE_RERUN_NEEDED
```

The regenerated R2 evidence says:

```text
anchor_smoke_rows = 2688
adaptive_rerun_recommended = 0 / 2688
statistical_precision_rerun_recommended = 0 / 2688
low_detectability_prior = 44 / 2688
adaptive_event_count_will_not_clear_gate = 44 / 2688
P_ref_ROI_W particle-independent for fixed route/scenario/seed
SNR_claim_level = absolute_blocked for all rows
event_probability_claim_level = absolute_blocked for all rows
legacy SNR names absent
R2 true, R3 false, R5 false
```

R2 route trends are interpretable only as relative-prior smoke trends:

- 660 main family stayed near the top.
- `660 / 900x1400` was numerically highest but remains an optional probe, not a
  silent replacement for the main 660 panel.
- `660 / 700x1500` remains a weak-reference/control route unless explicitly
  reclassified later.
- 404 routes remained lower and mostly thermal amber under the 404 sidecar.
- EV250 and metal standards were easier than EV70 low-RI, without any
  biological-specificity claim.

## Micro-Anchor Caveat Closed Before This Plan

GPT-Pro noted that R2 reference-power semantics were fixed, but the old
micro-anchor path still used particle-dependent reference scaling. That caveat
has now been patched and regenerated.

Micro-anchor now records:

```text
P_ref_scale_independent_of_particle = true
reference_power_prior_scale_W = route-dependent prior scale
max P_ref_ROI_W unique count across fixed micro-anchor route = 1
R2_anchor_smoke_run = false in the micro-anchor result manifest
R3_reduced_grid_run = false
R5_full_grid_v2_run = false
```

The root `run_manifest.json` was then restored by regenerating the capped R2
anchor smoke, so the root manifest again records:

```text
R2_anchor_smoke_run = true
R3_reduced_grid_run = false
R5_full_grid_v2_run = false
event_level_runs = 2688
```

## Proposed R3a Goal

R3a should answer one question:

```text
Do the R2 relative-prior trends remain stable when expanded from anchor routes
to a reduced wavelength / width / depth grid under the same named scenario
bundles and guardrails?
```

It should not answer:

```text
absolute LOD
absolute SNR
true EV concentration
biological specificity
calibrated event probability
full-grid v2 ranking
```

## Proposed R3a Detectability Model

Use the current R2 model as a **relative-prior ranking score**, not as an event
probability:

```text
primary_metric = detectability_relative_prior_score
p_detect_scenario retained only as legacy compatibility alias
p_detect_scenario_interpretation = legacy_named_relative_prior_score_not_event_probability
p_detect_mapping_claim_level = relative_with_priors
event_probability_claim_level = absolute_blocked
detected_events_source = relative_prior_score_proxy_count_not_observed_events
```

Add explicit threshold/noise/readout diagnostics, but do not convert them into a
calibrated probability:

```text
threshold_sigma
blank_false_positive_per_min
false_positive_per_min_claim
signal_to_threshold_relative_margin
scenario_detector_SNR
SNR_claim_level
effective_scenario_detector_SNR
scenario_SNR_spread_watch
```

R3a should stop or return to model design if external review requires a
calibrated threshold/noise event-probability model before grid expansion.

## Proposed R3a Route Panel

Use the roadmap reduced grid without optional width 1000:

```text
wavelength_nm = 404 / 488 / 532 / 660
width_nm = 600 / 700 / 800 / 900
depth_nm = 500 / 550 / 600 / 700 / 1300 / 1400 / 1500
route_count = 112
```

Route-role labels must be carried into outputs:

```text
660_800x1400 = main_660
660_800x1500 = main_660
660_700x1500 = weak_reference_control
660_900x1400 = optional_robustness_probe
660_800x550/600/700 = selected_annulus_sanity_overlap_longwave
404_600x1300 = shortwave_mechanism_candidate
404_800x550/600/700 = selected_annulus_sanity_overlap_shortwave
532_600x1500 = medium_wave_baseline
488_600x1500 = medium_wave_baseline
```

`660 / 900x1400` must be reported in a separate optional-probe section. It must
not silently redefine the main 660 route family.

Every output row must include:

```text
route_role_locked = true
route_role_source = R3a_plan_v1
```

Discussion of `660 / 900x1400` promotion is allowed only in
`optional_660_900x1400_probe_summary.csv`; it cannot drift into the main 660
route-family summary.

## Proposed R3a Particle Panel

Keep a representative EV / contaminant / standard panel under a fixed cap:

```text
EV nominal RI sizes = 50 / 70 / 100 / 120 / 150 / 200 / 250 nm
EV low/high RI sensitivity = 70 / 100 / 150 / 250 nm
contaminants = LDL_like_contaminant / protein_aggregate / EV_doublet
standards = Au20 / Au40 / Au60 / Ag40 / Ag60
particle_count = 23
```

No biological specificity claim is allowed. Contaminants and standards are
controls for optical trend stability only.

## Proposed R3a Scenario Policy

Use the same eight named R2 scenario bundles for R3a:

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

Do not run a full Cartesian product of detector, BFP, blank, PEG, EV, RIN, DAQ,
and thermal axes.

Because R2 `scenario_detector_SNR` spread was about 831x, close to the 1e3
watch threshold, R3a must include:

```text
scenario_SNR_spread_by_route_family.csv
scenario_spread_watch_status
stop_if_spread_exceeds_1e3_without_physical_explanation = true
```

Latin-hypercube / Sobol uncertainty samples should be deferred to a separate
R3b review unless GPT-Pro explicitly authorizes them now.

## Proposed R3a Seed and Cost Cap

Use fixed prior-score seed perturbations for continuity with R2:

```text
seeds = 42 / 43 / 44
events_per_case_proxy = 3000
event_probability_claim_level = absolute_blocked
```

Planned case cap:

```text
max_R3a_routes = 112
max_R3a_particles = 23
max_R3a_scenario_bundles = 8
max_R3a_stochastic_seeds = 3
max_R3a_case_rows_before_review = 112 * 23 * 8 * 3 = 61824
```

These are case rows for posthoc / analytic / relative-prior scoring. They are
not calibrated observed events and must not be used to infer rare false-positive
safety from finite zero events.

Before execution, the R3a runner must write a cost estimator:

```text
results/ev_nodi_realism_v2_reduced_grid_R3a/reduced_grid_cost_estimate.csv
```

It must include:

```text
n_routes
n_particles
n_scenario_bundles
n_seeds
events_per_case_proxy
case_row_count
max_R3a_case_rows_before_review
estimated_runtime_s
estimated_disk_MB
under_R3a_review_cap
```

If `under_R3a_review_cap` is false, R3a must not start.

## Proposed R3a Outputs

If authorized later, R3a should write only under:

```text
results/ev_nodi_realism_v2_reduced_grid_R3a/
```

Required files:

```text
reduced_grid_summary.csv
route_family_rank_distribution.csv
scenario_rank_distribution.csv
anchor_overlap_correlation.csv
scenario_SNR_spread_by_route_family.csv
optional_660_900x1400_probe_summary.csv
weak_reference_control_summary.csv
thermal_404_gate_summary.csv
detector_connection_state_machine_summary.csv
blank_rare_tail_check.csv
unit_guardrail_summary.csv
reduced_grid_cost_estimate.csv
run_manifest.json
R3a_reduced_grid_report.md
```

Root `run_manifest.json` may be updated only after successful R3a completion and
must record:

```text
R2_anchor_smoke_run = true
R3_reduced_grid_run = true
R3a_reduced_grid_named_bundle_survey_run = true
R3b_uncertainty_expansion_run = false
R4_representative_full_wave_validation_run = false
R5_full_grid_v2_run = false
```

## Proposed R3a Tests Before Execution

Add focused tests before running R3a:

```text
test_R3a_cost_cap_blocks_over_cap_grid
test_R3a_route_roles_do_not_promote_optional_660_900_silently
test_R3a_detectability_score_is_not_event_probability
test_R3a_scenario_snr_spread_watch_triggers_at_1e3
test_R3a_manifest_keeps_R4_R5_false
test_R3a_outputs_have_required_v2_provenance
test_R3a_no_legacy_snr_output_names
test_R3a_anchor_overlap_rank_correlation_is_reported
```

## Proposed R3a Promote / Stop Gates

R3a can be considered stable enough for the next review only if:

```text
top route families are stable under named scenario bundles
main 660 route family remains interpretable or shifts with physical explanation
optional 660 / 900x1400 is reported separately
404 is either mechanism route or gated by thermal/blank sidecar, not numerical artifact
BFP/slit offset does not dominate every ranking
detector path remains settled or explicitly bifurcated
wall/PEG scenario changes count-rate proxy without arbitrary free parameter
EV ensemble outputs small-EV / aggregate bias explicitly
rank correlation with shared R2 anchor cases > 0.7 or failure is explained
scenario SNR spread stays below 1e3 or has a physical explanation
```

Stop or revise if:

```text
ranking is controlled by one unconstrained optical-throughput scalar
wall adsorption prior alone determines all conclusions
detector path gives opposite route rankings without settled instrumentation
interface/BFP correction shifts ROI by >30 percent with no validation path
uncertainty bands are so wide that every route overlaps every route
404 routes are all thermal red or saturating
false-positive prior exceeds plausible true event proxy for all EV scenarios
legacy SNR names appear in outputs
calibrated_absolute SNR appears without measured artifacts
```

## External Review Question

Ask GPT-Pro:

```text
Given R2 passed model-fix review and no adaptive rerun is needed, is this R3a
reduced-grid named-bundle plan sufficiently constrained to authorize R3a only?
If yes, authorize only R3a under the stated 61,824-row cap and output/test
requirements. Do not authorize R4 or R5.
```
