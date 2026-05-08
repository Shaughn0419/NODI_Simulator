# EV/NODI Realism v2 R2 Anchor Smoke Analysis

Date: 2026-05-06

## Scope

This report summarizes the authorized R2 anchor smoke only. It does not promote
to R3 reduced grid, R4 representative full-wave validation, or R5 full-grid v2.

R2 was first run after GPT-Pro returned `PASS_TO_R2_ANCHOR_SMOKE` for the fixed
R0/P0/R1.5 bundle. GPT-Pro then returned
`CONDITIONAL_FIX_R2_MODEL_BEFORE_RERUN`, blocking a 10k adaptive rerun until the
R2 detectability model was tightened. This report is for the regenerated R2
anchor smoke after those model fixes.

## Run Summary

Output directory:

```text
results/ev_nodi_realism_v2_anchor_smoke/
```

R2 panel:

```text
routes = 14
particles = 8 selected representative particles under cap
scenario_bundles = 8
seeds = 42 / 43 / 44
events_per_case = 3000
event_level_case_rows = 2688
max_event_level_runs_before_review = 2688
```

Manifest status:

```text
R2_anchor_smoke_run = true
R3_reduced_grid_run = false
R5_full_grid_v2_run = false
```

Core guardrails:

```text
all_watt_units = true
SNR_claim_level = absolute_blocked for all 2688 rows
event_probability_claim_level = absolute_blocked for all 2688 rows
p_detect_mapping_claim_level = relative_with_priors for all 2688 rows
detector_SNR / calibrated_detector_SNR output names absent
ET2030 direct current-input path = forbidden
finite_monte_carlo_zero_event_inferred = false
smoke_cost_under_cap = true
```

## Model-Fix Summary

The regenerated R2 output closes the three R2 model blockers from the previous
external review:

1. `P_ref_ROI_W` is now route/scenario dependent and particle independent. For
   fixed route, scenario, and seed, the maximum number of unique reference-power
   values across particles is 1.
2. Adaptive logic is split into `statistical_precision_rerun_recommended`,
   `low_detectability_prior`, and `adaptive_event_count_will_not_clear_gate`.
   More events are no longer recommended merely because a row is low
   detectability.
3. Detectability is explicitly marked as a relative prior score, not a
   calibrated event probability. The legacy-named `p_detect_scenario` column is
   retained only as a compatibility alias and is annotated by:

```text
p_detect_scenario_interpretation = legacy_named_relative_prior_score_not_event_probability
p_detect_mapping_mode = relative_prior_score_from_absolute_blocked_snr_not_event_probability
detected_events_source = relative_prior_score_proxy_count_not_observed_events
statistical_precision_rerun_basis = relative_prior_score_proxy_wilson_half_width
```

## Adaptive Status

The prior all-row adaptive trigger is gone:

```text
adaptive_rerun_recommended = 0 / 2688
statistical_precision_rerun_recommended = 0 / 2688
low_detectability_prior = 44 / 2688
adaptive_event_count_will_not_clear_gate = 44 / 2688
```

Relative detectability-prior score:

```text
min    = 0.014724
mean   = 0.118315
median = 0.092247
max    = 0.493017
```

The 44 low-detectability rows are now marked as low-prior rows that an event
count increase will not clear by itself. No R2 adaptive 10k rerun is requested
by the regenerated precision proxy.

## Reference-Power Check

For `660 / 800x1400`, `nominal_instrument_clean_blank`, seed 42:

| particle_id | P_ref_ROI_W | reference_power_prior_scale_W |
|---|---:|---:|
| EV70_lowRI | 3.206197e-15 | 1.000000e-08 |
| EV100_nominal | 3.206197e-15 | 1.000000e-08 |
| EV150_nominal | 3.206197e-15 | 1.000000e-08 |
| EV250_large_tail | 3.206197e-15 | 1.000000e-08 |
| LDL_like_contaminant | 3.206197e-15 | 1.000000e-08 |
| protein_aggregate | 3.206197e-15 | 1.000000e-08 |
| Au40 | 3.206197e-15 | 1.000000e-08 |
| Ag60 | 3.206197e-15 | 1.000000e-08 |

## EV Route Ordering

Mean EV relative detectability-prior score by route:

| wavelength_nm | width_nm | depth_nm | mean_score | min_score | max_score |
|---:|---:|---:|---:|---:|---:|
| 660 | 900 | 1400 | 0.199276 | 0.066931 | 0.493017 |
| 660 | 800 | 1500 | 0.191296 | 0.063584 | 0.479548 |
| 660 | 800 | 1400 | 0.180402 | 0.059116 | 0.460532 |
| 660 | 700 | 1500 | 0.170625 | 0.055203 | 0.442821 |
| 532 | 600 | 1500 | 0.150767 | 0.047570 | 0.404634 |
| 488 | 600 | 1500 | 0.142355 | 0.044452 | 0.387553 |
| 404 | 700 | 1400 | 0.108509 | 0.037806 | 0.295636 |
| 660 | 800 | 700 | 0.095375 | 0.027974 | 0.282873 |
| 404 | 600 | 1300 | 0.087324 | 0.029488 | 0.248841 |
| 660 | 800 | 600 | 0.081940 | 0.023616 | 0.249206 |
| 660 | 800 | 550 | 0.075112 | 0.021457 | 0.231408 |
| 404 | 800 | 700 | 0.062900 | 0.020485 | 0.189082 |
| 404 | 800 | 600 | 0.053762 | 0.017273 | 0.164956 |
| 404 | 800 | 550 | 0.049151 | 0.015684 | 0.152391 |

Interpretation:

- The 660 main family remains near the top, especially `660 / 800x1500` and
  `660 / 800x1400`.
- Optional `660 / 900x1400` remains numerically highest, but it was optional
  and should not by itself redefine the first R2 conclusion.
- `660 / 700x1500` remains explicitly a weak-reference/control route and should
  not be promoted without physical reclassification.
- 404 routes remain lower in this R2 prior smoke and are mostly thermal amber
  under the 404 sidecar.

## Scenario Sensitivity

Mean EV relative detectability-prior score by scenario:

| scenario_bundle | mean_score | min_score | max_score |
|---|---:|---:|---:|
| external_TIA_optimistic | 0.200997 | 0.048702 | 0.493017 |
| nominal_instrument_clean_blank | 0.159992 | 0.036354 | 0.418250 |
| blank_bursty_RIN_high | 0.132620 | 0.028884 | 0.362216 |
| DAQ_low_resolution_sampling | 0.108229 | 0.022705 | 0.307635 |
| PEG_pessimistic_wall_loss | 0.097461 | 0.020113 | 0.282025 |
| detector_50ohm_pessimistic | 0.083324 | 0.016706 | 0.245523 |
| BFP_slit_offset_leakage | 0.080022 | 0.016081 | 0.238447 |
| 404_thermal_high_low_power | 0.079524 | 0.015684 | 0.233879 |

Scenario spread remains bounded in this named-bundle smoke panel. It is not a
calibrated SNR claim and should not be read as absolute detectability.

## Particle Ordering

Mean relative detectability-prior score across all routes/scenarios:

| particle_id | class | mean_score |
|---|---|---:|
| EV250_large_tail | EV | 0.193470 |
| Au40 | standard | 0.176246 |
| Ag60 | standard | 0.160120 |
| EV150_nominal | EV | 0.127106 |
| EV100_nominal | EV | 0.089318 |
| LDL_like_contaminant | contaminant | 0.082645 |
| EV70_lowRI | EV | 0.061190 |
| protein_aggregate | contaminant | 0.056422 |

This ordering is plausible for a prior smoke: large-tail EV and metal standards
are easier, low-RI small EV remains hardest. It is not a biological specificity
claim.

## Thermal / Detector / Blank Status

Thermal risk:

```text
404 amber = 660 rows
404 green = 300 rows
488/532/660 green = all rows
```

Detector and saturation:

```text
connection_physical_validity = allowed for active scenario rows
ET2030 direct current-input path = forbidden in state-machine summary
saturation_status = comfortable_margin for all 2688 rows
```

Blank:

```text
false_positive_per_min min  = 0.00100
false_positive_per_min mean = 0.00135
false_positive_per_min max  = 0.00172
finite_monte_carlo_zero_event_inferred = false
```

SNR:

```text
scenario_detector_SNR min    = 9.30e-10
scenario_detector_SNR mean   = 7.12e-08
scenario_detector_SNR median = 3.24e-08
scenario_detector_SNR max    = 7.72e-07
SNR_claim_level = absolute_blocked for all rows
```

## Stop / Promote Assessment

R2 no longer recommends an adaptive 10k rerun from its precision proxy, and
R3/R4/R5 remain unauthorized pending external review of the model fixes.

Hard stop conditions are not clearly met:

- Detector path does not saturate.
- ET2030 invalid current-input path remains blocked.
- Blank FP/min is analytic/semi-analytic, not finite zero-event safety.
- Scenario spread is bounded in the named scenario panel.
- 404 thermal sidecar gates risk and does not add optical score.

## Recommended External Review Question

Ask GPT-Pro whether the R2 model fixes are sufficient:

```text
Do the regenerated R2 outputs close the previous blockers on particle-dependent
reference power, adaptive rerun semantics, and uncalibrated detectability
mapping? If yes, is any R2 adaptive rerun still needed, or should the project
prepare a separate externally reviewed R3 reduced-grid plan while keeping
R3/R4/R5 unrun for now?
```

Do not proceed to R3/R4/R5 until that next external review explicitly allows
the next stage.
