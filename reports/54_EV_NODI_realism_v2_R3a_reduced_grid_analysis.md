# EV/NODI Realism v2 R3a Reduced-Grid Analysis

Date: 2026-05-06

## Scope

This report summarizes the authorized R3a reduced-grid named-bundle survey only.

Authorized scope:

```text
Stage = R3a reduced-grid named-bundle survey only
routes = 112
particles = 23
scenario_bundles = 8 named bundles
seeds = 42 / 43 / 44
events_per_case_proxy = 3000
max case rows before review = 61,824
```

Forbidden stages remain unrun:

```text
R3b_uncertainty_expansion_run = false
R4_representative_full_wave_validation_run = false
R5_full_grid_v2_run = false
```

## Output Directory

```text
results/ev_nodi_realism_v2_reduced_grid_R3a/
```

Required outputs were generated:

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

## Guardrails

R3a preserved the R2 claim boundaries:

```text
reduced_grid_summary rows = 61,824
SNR_claim_level = absolute_blocked for all rows
event_probability_claim_level = absolute_blocked for all rows
p_detect_mapping_claim_level = relative_with_priors for all rows
legacy detector_SNR / calibrated_detector_SNR output headers absent
route_role_locked = true for all rows
route_role_source = R3a_plan_v1 for all rows
R3b_uncertainty_expansion_run = false for all rows
R4_representative_full_wave_validation_run = false for all rows
R5_full_grid_v2_run = false for all rows
```

The root and result manifests record:

```text
R2_anchor_smoke_run = true
R3_reduced_grid_run = true
R3a_reduced_grid_named_bundle_survey_run = true
R3b_uncertainty_expansion_run = false
R4_representative_full_wave_validation_run = false
R5_full_grid_v2_run = false
```

All R3a rows keep the detectability mapping explicit:

```text
primary_metric = detectability_relative_prior_score
p_detect_scenario_interpretation = legacy_named_relative_prior_score_not_event_probability
detected_events_source = relative_prior_score_proxy_count_not_observed_events
```

## Relative-Prior Score Distribution

`detectability_relative_prior_score` across all rows:

```text
min    = 0.008020
mean   = 0.107527
median = 0.083366
max    = 0.548727
```

These are relative-prior scores only. They are not calibrated event
probabilities, LOD estimates, or biological specificity claims.

## Route-Role Ranking

Mean relative-prior score by locked route role:

| rank | route_role | route_count | mean_score | min_score | max_score | n_case_rows |
|---:|---|---:|---:|---:|---:|---:|
| 1 | optional_robustness_probe | 1 | 0.203041 | 0.053130 | 0.526726 | 552 |
| 2 | main_660 | 2 | 0.189489 | 0.046840 | 0.513324 | 1104 |
| 3 | weak_reference_control | 1 | 0.174103 | 0.043700 | 0.476515 | 552 |
| 4 | medium_wave_baseline | 2 | 0.149717 | 0.035104 | 0.437695 | 1104 |
| 5 | reduced_grid_context_route | 99 | 0.105762 | 0.008020 | 0.548727 | 54648 |
| 6 | shortwave_mechanism_candidate | 1 | 0.089054 | 0.023207 | 0.273368 | 552 |
| 7 | selected_annulus_sanity_overlap_longwave | 3 | 0.086204 | 0.016852 | 0.311574 | 1656 |
| 8 | selected_annulus_sanity_overlap_shortwave | 3 | 0.056465 | 0.012303 | 0.209945 | 1656 |

Interpretation:

- The optional `660 / 900x1400` probe remains numerically strong and is reported
  only in `optional_660_900x1400_probe_summary.csv`.
- The locked `main_660` family remains strong and ranks second by route-role
  aggregate.
- `660 / 700x1500` remains a locked weak-reference control, not a silent main
  route.
- 404 selected-annulus sanity routes remain lower than longwave sanity routes.

## Top Individual Routes

Top individual routes by all-particle mean score:

| route | route_role | mean_score |
|---|---|---:|
| 532 / 900x1500 | reduced_grid_context_route | 0.217173 |
| 660 / 900x1500 | reduced_grid_context_route | 0.214804 |
| 488 / 900x1500 | reduced_grid_context_route | 0.206171 |
| 532 / 900x1400 | reduced_grid_context_route | 0.205337 |
| 660 / 900x1400 | optional_robustness_probe | 0.203041 |
| 532 / 800x1500 | reduced_grid_context_route | 0.197233 |
| 660 / 800x1500 | main_660 | 0.194990 |
| 488 / 900x1400 | reduced_grid_context_route | 0.194755 |
| 532 / 900x1300 | reduced_grid_context_route | 0.193116 |
| 660 / 900x1300 | reduced_grid_context_route | 0.190901 |

This is a planning-relevant finding: R3a expanded the route panel enough that
some `reduced_grid_context_route` geometries outrank the locked R2 anchors.
Because those routes were not R2 anchors, this should not be interpreted as a
route promotion. It is a reason to ask whether R3b should focus on route-role
stability and context-route robustness before any R4/R5 discussion.

## Scenario Ranking

Mean relative-prior score by named scenario:

| rank | scenario_bundle | mean_score | min_score | max_score |
|---:|---|---:|---:|---:|
| 1 | external_TIA_optimistic | 0.184914 | 0.025340 | 0.548727 |
| 2 | nominal_instrument_clean_blank | 0.146644 | 0.018793 | 0.473645 |
| 3 | blank_bursty_RIN_high | 0.121245 | 0.014873 | 0.415633 |
| 4 | DAQ_low_resolution_sampling | 0.098715 | 0.011653 | 0.357624 |
| 5 | PEG_pessimistic_wall_loss | 0.088800 | 0.010309 | 0.329880 |
| 6 | detector_50ohm_pessimistic | 0.075388 | 0.008547 | 0.289737 |
| 7 | BFP_slit_offset_leakage | 0.072784 | 0.008225 | 0.281873 |
| 8 | 404_thermal_high_low_power | 0.071727 | 0.008020 | 0.276781 |

The scenario ordering is monotone and bounded across named bundles. It should
not be read as calibrated detector SNR.

## Scenario SNR Spread Watch

R3a scenario-spread watch status:

```text
all route roles: pass_under_1e3
max scenario_SNR_spread by route role = 4.664903
stop_if_spread_exceeds_1e3_without_physical_explanation = true
```

This closes the R2 watch item for named-bundle R3a. It does not validate an
unbounded uncertainty expansion.

## Anchor Overlap

Shared R2/R3a anchor route-particle cases:

```text
shared_route_particle_cases = 98
pearson_correlation = 0.99908
spearman_rank_correlation = 0.99731
status = pass_rank_correlation_over_0p7
```

R3a therefore preserves the R2 anchor ordering for overlapping cases under the
same relative-prior model.

## Thermal / Detector / Blank Status

Thermal sidecar:

```text
404 amber = 10,752 rows
404 green = 4,704 rows
488/532/660 green = all rows
thermal sidecar does not increase NODI score
```

Detector:

```text
saturation_status = comfortable_margin for all 61,824 rows
active detector paths = allowed
ET2030 direct current-input path remains forbidden in state-machine summary
```

Blank:

```text
false_positive_per_min min  = 0.001000
false_positive_per_min mean = 0.001354
false_positive_per_min max  = 0.001720
finite_monte_carlo_zero_event_inferred = false
```

## Stop / Promote Assessment

R3a does not show a hard stop:

- Legacy SNR output names are absent.
- `calibrated_absolute` SNR is not emitted.
- ET2030 invalid current-input remains blocked.
- Blank FP/min remains analytic/semi-analytic.
- Detector paths do not saturate.
- Scenario spread is below the 1e3 watch threshold for named bundles.
- Anchor-overlap rank correlation is above 0.7.

R3a also does not justify R4/R5:

- Context routes outside the R2 anchor roles rank highly.
- `660 / 900x1400` remains optional and cannot redefine the main route family.
- R3a used named bundles only, not uncertainty propagation.
- Detectability remains relative-prior only, not calibrated probability.

## Recommended External Review Question

Ask GPT-Pro:

```text
Given R3a ran under the authorized 61,824-row cap, preserved all R2 claim
boundaries, passed scenario-spread and anchor-overlap checks, but exposed high
scoring context routes such as 532 / 900x1500 and 660 / 900x1500, are the R3a
results acceptable as a reduced-grid named-bundle survey? If yes, should the
next step be only to prepare an R3b uncertainty-expansion plan, or is a specific
R3a model/reporting fix required first?
```

Do not authorize R4/R5 from this review.
