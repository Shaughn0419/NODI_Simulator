# EV/NODI Realism v2 R3b Route-Sensitive Uncertainty Expansion Analysis

Date: 2026-05-06

## Scope

This is the R3b route-sensitive uncertainty expansion result. It is not R4,
not R5, and not a full-grid v2 run.

Authorized gate:

```text
PASS_TO_R3B_ROUTE_SENSITIVE_UNCERTAINTY_ONLY
```

Executed panel:

```text
routes = 19
particles = 23
prior_samples = 24
seeds = 42 / 43 / 44
events_per_case_proxy = 3000
case_rows = 31,464
output_directory = results/ev_nodi_realism_v2_uncertainty_R3b/
```

Still not authorized and not run:

```text
R4 representative full-wave validation
R5 full-grid v2
v1 full-grid overwrite
Tsuyama paper-fit continuation
selected-annulus bound changes
context-route promotion
calibrated SNR
ET2030 direct current-input unlock
```

## Claim Boundaries

All R3b outputs preserve the R2/R3a claim boundary:

```text
primary_metric = detectability_relative_prior_score
p_detect_scenario = legacy compatibility alias only
p_detect_mapping_claim_level = relative_with_priors
event_probability_claim_level = absolute_blocked
SNR_claim_level = absolute_blocked
detected_events_source = relative_prior_score_proxy_count_not_observed_events
```

The result CSV headers do not contain:

```text
detector_SNR
calibrated_detector_SNR
```

`scenario_detector_SNR` remains an absolute-blocked sidecar. R3b does not claim
absolute LOD, absolute SNR, true EV concentration, calibrated event probability,
or biological specificity.

## Uncertainty Design

R3b used the v3 prior table:

```text
configs/realism_v2/r3b_uncertainty_prior_table.yaml
schema_version = R3b_uncertainty_prior_table_v3
r3b_uncertainty_prior_table_checksum = 5d2a9fa2ee8877c473476523aa19028a93b63488484358194405b172e5f0f60f
```

Every factor has numeric bounds, units, distribution, correlation group,
correlation transform, route-sensitive formula, rationale, and claim level.

Important directed correlations:

```text
PEG_wall:
  peg_survival_factor = inverse
  near_wall_event_fraction = direct
  adsorption_loss_factor = direct

blank_effective_N:
  independent_samples_per_s = inverse
  colored_noise_correlation_time_s = direct

BFP_alignment:
  roi_shift_uv = direct
  slit_width_scale = inverse
```

The route-sensitivity gate uses:

```text
effect_delta[group, route] =
  median_over_particles_seeds_prior_samples(
    log((score_with_group_effect[group, route] + eps) / (nominal_score[route] + eps))
  )

effect_delta_convention =
  median_log_score_ratio_over_particles_seeds_prior_samples
```

## R3b Main Result

Overall route-sensitive prior diagnostics pass the anti-global-scalar gate:

```text
route_sensitive_prior_status = route_sensitive
global_multiplier_dominance_index = 0.310657
global_scalar_dominated_stop_gate = false
```

Per-factor route-sensitive diagnostics:

| factor_group | route_sensitive_index | global_multiplier_dominance_index | status |
|---|---:|---:|---|
| BFP_slit_alignment | 0.854056 | 0.292477 | route_sensitive |
| detector_readout | 0.896699 | 0.253405 | route_sensitive |
| wall_PEG_flow | 0.703633 | 0.393570 | route_sensitive |
| blank_RIN_drift | 0.953849 | 0.180304 | route_sensitive |
| thermal_404 | 0.789474 | 0.340542 | route_sensitive |
| EV_ensemble | 0.999737 | 0.015955 | route_sensitive |

This closes the R3b planning concern that the result might be controlled by a
hidden broad multiplier.

## Route-Role Stability

Route-role medians under R3b uncertainty:

| route_role | route_count | median relative-prior score | p05 | p95 | rank |
|---|---:|---:|---:|---:|---:|
| reduced_grid_context_route | 6 | 0.264493 | 0.125024 | 0.448765 | 1 |
| optional_robustness_probe | 1 | 0.258275 | 0.124789 | 0.445643 | 2 |
| main_660 | 2 | 0.244250 | 0.115221 | 0.423520 | 3 |
| weak_reference_control | 1 | 0.203943 | 0.085306 | 0.410444 | 4 |
| medium_wave_baseline | 2 | 0.191083 | 0.087918 | 0.349996 | 5 |
| shortwave_mechanism_candidate | 1 | 0.108001 | 0.055076 | 0.210883 | 6 |
| selected_annulus_sanity_overlap_longwave | 3 | 0.105051 | 0.041834 | 0.223037 | 7 |
| selected_annulus_sanity_overlap_shortwave | 3 | 0.065520 | 0.029986 | 0.140393 | 8 |

Interpretation:

```text
Context routes remain high under route-sensitive uncertainty.
This is planning evidence only, not promotion.
main_660 remains locked.
660 / 900x1400 remains optional_robustness_probe.
selected-annulus sanity routes remain separate and do not replace all-crossing ranking.
```

## Context Routes

Top context route medians:

| route | median relative-prior score | p05 | p95 | promotion |
|---|---:|---:|---:|---|
| 532 / 900x1500 | 0.276189 | 0.135257 | 0.467538 | not authorized |
| 660 / 900x1500 | 0.273274 | 0.133432 | 0.464389 | not authorized |
| 488 / 900x1500 | 0.262886 | 0.127273 | 0.449441 | not authorized |
| 532 / 900x1400 | 0.261323 | 0.126546 | 0.448836 | not authorized |
| 532 / 800x1500 | 0.253658 | 0.121504 | 0.434757 | not authorized |
| 660 / 900x1300 | 0.242581 | 0.117117 | 0.425188 | not authorized |

`532 / 800x1500` is included and remains a context probe, as required by the
R3b plan re-review. It is not promoted.

## Main 660 And Optional 660 Governance

Main 660 routes:

| route | median relative-prior score | rank |
|---|---:|---:|
| 660 / 800x1500 | 0.250806 | 7 |
| 660 / 800x1400 | 0.237290 | 9 |

Optional 660 probe:

| route | median relative-prior score | rank | eligible_for_main_redefinition |
|---|---:|---:|---|
| 660 / 900x1400 | 0.258275 | 5 | false |

The optional probe remains isolated in
`optional_660_governance_summary.csv`. R3b does not reclassify it.

## Scenario Spread Watch

Scenario SNR spread remains well below the 1e3 stop gate:

```text
max scenario_SNR_spread = 3.299311
scenario_spread_watch_status = pass_under_1e3 for all route roles
```

## Detector / Blank / Thermal Guards

Detector:

```text
ET2030_BNC_direct_to_LI5640_current_input = forbidden
requires_bench_validation = true
bench_validation_artifact_id = empty
```

Blank:

```text
finite_monte_carlo_zero_event_inferred = false
false_positive_per_min_claim = analytic_prior_only
```

Thermal 404:

```text
thermal_sidecar_does_not_increase_nodi_score = true
max_thermal_404_log_multiplier <= 0
404 amber rows present
404 all-red stop condition not triggered
```

## Required Output Files

Generated under:

```text
results/ev_nodi_realism_v2_uncertainty_R3b/
```

Files:

```text
uncertainty_expansion_summary.csv
route_role_stability_summary.csv
context_route_robustness_summary.csv
main_660_stability_summary.csv
optional_660_governance_summary.csv
scenario_factor_sensitivity.csv
route_sensitive_prior_diagnostics.csv
global_multiplier_dominance_check.csv
uncertainty_band_overlap_matrix.csv
scenario_SNR_spread_by_route_family.csv
thermal_404_uncertainty_gate_summary.csv
detector_connection_state_machine_summary.csv
blank_rare_tail_check.csv
unit_guardrail_summary.csv
uncertainty_cost_estimate.csv
run_manifest.json
R3b_uncertainty_expansion_report.md
```

## Next Review Question

Ask external review whether R3b results pass as a capped route-sensitive
uncertainty expansion and whether the next action should be plan preparation
only for R4 representative full-wave validation. Do not authorize or run R4/R5
from this result bundle.
