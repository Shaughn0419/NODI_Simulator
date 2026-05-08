# EV/NODI Realism v2 R3b Uncertainty-Expansion Plan for External Review

Date: 2026-05-06

## Scope

This is a plan for external review. It is not an R3b execution report.

Current gate status:

```text
R3a reduced-grid named-bundle survey passed external review
R3a rerun not needed
R3b uncertainty expansion not run
R4 representative full-wave validation not run
R5 full-grid v2 not run
```

The requested next authorization should be limited to **R3b uncertainty-expansion
planning execution only after review**, with a capped route-role stability study.
It should not authorize R4 or R5.

## Carry-Forward Hard Constraints

```text
Do not overwrite v1 full-grid outputs.
Do not continue Tsuyama paper-fit.
Do not change selected-annulus 0.5-0.8 bounds.
Do not replace all-crossing main ranking with selected-annulus ranking.
Do not export detector_SNR or calibrated_detector_SNR.
Do not claim calibrated absolute SNR without measured detector transfer and measured blank artifacts.
Do not unlock ET2030 direct current-input without real measured/calibrated bench validation artifact.
Do not treat relative-prior detectability as calibrated event probability.
Do not run R4 or R5 from this authorization.
```

Manifest hardening is now explicit:

```text
v1_full_grid_overwritten = false
Tsuyama_paper_fit_continued = false
selected_annulus_bounds_changed = false
calibrated_SNR_claim_emitted = false
ET2030_direct_current_input_unlocked = false
base_v1_summary_path_relative present
output_directory_relative present
```

## R3a Evidence Motivating R3b

GPT-Pro returned:

```text
PASS_R3A_RESULTS_PREPARE_R3B_PLAN_ONLY
```

R3a was accepted as a bounded named-bundle survey:

```text
routes = 112
particles = 23
scenario_bundles = 8
seeds = 42 / 43 / 44
case_rows = 61,824
R3b/R4/R5 = false
```

R3a's main scientific output is a planning issue:

```text
high-scoring context routes exist outside the locked R2 anchor roles
R3b should focus on route-role stability and context-route robustness
```

Top individual R3a routes by all-particle mean:

| route | route_role | mean relative-prior score |
|---|---|---:|
| 532 / 900x1500 | reduced_grid_context_route | 0.217173 |
| 660 / 900x1500 | reduced_grid_context_route | 0.214804 |
| 488 / 900x1500 | reduced_grid_context_route | 0.206171 |
| 532 / 900x1400 | reduced_grid_context_route | 0.205337 |
| 660 / 900x1400 | optional_robustness_probe | 0.203041 |
| 532 / 800x1500 | reduced_grid_context_route | 0.197233 |
| 660 / 800x1500 | main_660 | 0.194990 |

These are not promotions. They are R3b design targets.

## Proposed R3b Goal

R3b should answer:

```text
Are the R3a high-scoring context routes and locked route roles stable under
route-sensitive uncertainty perturbations, or are they artifacts of broad global
scenario multipliers?
```

R3b should not answer:

```text
absolute LOD
absolute SNR
true EV concentration
biological specificity
calibrated event probability
full-grid v2 ranking
R4 full-wave validation result
```

## Proposed R3b Route Panel

Use a focused route panel instead of the full R3a 112-route grid.

Required locked anchors:

```text
660 / 800x1400  main_660
660 / 800x1500  main_660
660 / 700x1500  weak_reference_control
660 / 900x1400  optional_robustness_probe
404 / 600x1300  shortwave_mechanism_candidate
532 / 600x1500  medium_wave_baseline
488 / 600x1500  medium_wave_baseline
```

R3a high-scoring context probes:

```text
532 / 900x1500
660 / 900x1500
488 / 900x1500
532 / 900x1400
660 / 900x1300
532 / 800x1500
```

The `532 / 800x1500` route is included because R3a ranked it above the locked
`660 / 800x1500` main route. It is a context probe only; it is not a route
promotion and cannot redefine the locked main 660 route family in R3b.

Selected-annulus sanity:

```text
660 / 800x550
660 / 800x600
660 / 800x700
404 / 800x550
404 / 800x600
404 / 800x700
```

Total route cap:

```text
max_R3b_routes = 19
max_R3b_case_rows_before_review = 19 * 23 * 24 * 3 = 31,464
```

Every output row must include:

```text
route_role_locked = true
route_role_source = R3b_plan_v2
context_route_promotion_authorized = false
```

Context routes can be discussed only in:

```text
context_route_robustness_summary.csv
```

## Proposed R3b Particle Panel

Keep the same R3a 23-particle panel to avoid changing route conclusions through
particle-panel drift:

```text
EV nominal RI sizes = 50 / 70 / 100 / 120 / 150 / 200 / 250 nm
EV low/high RI sensitivity = 70 / 100 / 150 / 250 nm
contaminants = LDL_like_contaminant / protein_aggregate / EV_doublet
standards = Au20 / Au40 / Au60 / Ag40 / Ag60
max_R3b_particles = 23
```

No biological specificity claim is allowed.

## Proposed R3b Uncertainty Design

R3b should not use a full Cartesian product. Use a small, deterministic,
auditable Latin-hypercube or Sobol-like design with correlated factor groups.

Proposed cap:

```text
uncertainty_method = latin_hypercube_named_groups
max_R3b_prior_samples = 24
seeds = 42 / 43 / 44
events_per_case_proxy = 3000
max_R3b_case_rows_before_review = 19 * 23 * 24 * 3 = 31,464
```

Use named factor groups:

```text
BFP_slit_alignment:
  roi_shift_uv
  slit_width_scale
  leakage_floor
  operator_throughput_scale

detector_readout:
  readout_path_sensitivity_factor
  input_noise_scale
  RIN_coupling_scale
  ADC_quantization_scale

wall_PEG_flow:
  peg_survival_factor
  near_wall_event_fraction
  adsorption_loss_factor
  count_rate_proxy_factor

blank_RIN_drift:
  blank_threshold_sigma
  independent_samples_per_s
  colored_noise_correlation_time_s
  rare_burst_rate_prior

thermal_404:
  404_power_scale
  medium_absorption_scale
  glass_absorption_scale
  filter_leakage_scale

EV_ensemble:
  small_EV_weight_scale
  low_RI_weight_scale
  contaminant_fraction_proxy
  doublet_fraction_proxy
```

The machine-readable prior table is:

```text
configs/realism_v2/r3b_uncertainty_prior_table.yaml
```

R3b may not start if any factor row is missing:

```text
factor_group
factor_name
unit
nominal
min
max
distribution
correlation_group
correlation_transform
route_sensitive_formula
physical_rationale
claim_level
```

`correlation_transform` is mandatory for every factor:

```text
direct = use the shared group quantile q
inverse = use 1 - q
independent_within_group = do not share the group quantile; use a factor-specific deterministic permutation
```

For non-singleton correlation groups, missing `correlation_transform` fails
closed before R3b can start. The revised plan uses explicit mixed directions
where physics requires anticorrelation:

| correlation_group | direct factors | inverse factors |
|---|---|---|
| BFP_alignment | roi_shift_uv | slit_width_scale |
| detector_noise | input_noise_scale / RIN_coupling_scale | none |
| PEG_wall | near_wall_event_fraction / adsorption_loss_factor | peg_survival_factor |
| blank_effective_N | colored_noise_correlation_time_s | independent_samples_per_s |
| thermal_absorption | medium_absorption_scale / glass_absorption_scale | none |

Numeric prior table used for authorization:

| factor_group | factor_name | unit | nominal | min | max | distribution | correlation_group | route_sensitive_formula | claim_level |
|---|---|---|---:|---:|---:|---|---|---|---|
| BFP_slit_alignment | roi_shift_uv | direction_cosine_uv_magnitude | 0.0 | 0.0 | 0.035 | truncated_normal | BFP_alignment | bfp_uv_slit_overlap | relative_with_priors |
| BFP_slit_alignment | slit_width_scale | ratio | 1.0 | 0.7 | 1.3 | triangular | BFP_alignment | bfp_uv_slit_overlap | relative_with_priors |
| BFP_slit_alignment | leakage_floor | fraction | 0.0001 | 0.000001 | 0.001 | log_uniform | BFP_leakage | bfp_uv_slit_overlap | relative_with_priors |
| BFP_slit_alignment | operator_throughput_scale | ratio | 1.0 | 0.75 | 1.15 | triangular | BFP_throughput | bfp_uv_slit_overlap | relative_with_priors |
| detector_readout | readout_path_sensitivity_factor | ratio | 1.0 | 0.6 | 1.4 | triangular | detector_path | detector_impedance_noise_by_route_power | relative_with_priors |
| detector_readout | input_noise_scale | ratio | 1.0 | 0.7 | 2.0 | log_uniform | detector_noise | detector_impedance_noise_by_route_power | relative_with_priors |
| detector_readout | RIN_coupling_scale | ratio | 1.0 | 0.5 | 3.0 | log_uniform | detector_noise | detector_impedance_noise_by_route_power | relative_with_priors |
| detector_readout | ADC_quantization_scale | ratio | 1.0 | 0.5 | 2.0 | log_uniform | DAQ_resolution | detector_impedance_noise_by_route_power | relative_with_priors |
| wall_PEG_flow | peg_survival_factor | fraction | 0.82 | 0.55 | 0.98 | triangular | PEG_wall | wall_peg_near_wall_geometry | relative_with_priors |
| wall_PEG_flow | near_wall_event_fraction | fraction | 0.35 | 0.1 | 0.7 | triangular | PEG_wall | wall_peg_near_wall_geometry | relative_with_priors |
| wall_PEG_flow | adsorption_loss_factor | fraction | 0.18 | 0.02 | 0.45 | triangular | PEG_wall | wall_peg_near_wall_geometry | relative_with_priors |
| wall_PEG_flow | count_rate_proxy_factor | ratio | 1.0 | 0.4 | 1.6 | triangular | flow_rate | wall_peg_near_wall_geometry | relative_with_priors |
| blank_RIN_drift | blank_threshold_sigma | sigma | 5.0 | 4.5 | 6.5 | triangular | blank_threshold | blank_rin_threshold_noise | relative_with_priors |
| blank_RIN_drift | independent_samples_per_s | Hz | 20.0 | 5.0 | 100.0 | log_uniform | blank_effective_N | blank_rin_threshold_noise | relative_with_priors |
| blank_RIN_drift | colored_noise_correlation_time_s | s | 0.5 | 0.05 | 5.0 | log_uniform | blank_effective_N | blank_rin_threshold_noise | relative_with_priors |
| blank_RIN_drift | rare_burst_rate_prior | 1/min | 0.001 | 0.0001 | 0.01 | log_uniform | blank_burst | blank_rin_threshold_noise | relative_with_priors |
| thermal_404 | 404_power_scale | ratio | 1.0 | 0.5 | 1.4 | triangular | thermal_power | thermal_404_absorption_gate | safety_sidecar |
| thermal_404 | medium_absorption_scale | ratio | 1.0 | 0.5 | 3.0 | log_uniform | thermal_absorption | thermal_404_absorption_gate | safety_sidecar |
| thermal_404 | glass_absorption_scale | ratio | 1.0 | 0.5 | 2.5 | log_uniform | thermal_absorption | thermal_404_absorption_gate | safety_sidecar |
| thermal_404 | filter_leakage_scale | ratio | 1.0 | 0.1 | 5.0 | log_uniform | thermal_filter_leakage | thermal_404_absorption_gate | safety_sidecar |
| EV_ensemble | small_EV_weight_scale | ratio | 1.0 | 0.5 | 1.8 | triangular | EV_size_mix | ev_ensemble_particle_route_response | relative_with_priors |
| EV_ensemble | low_RI_weight_scale | ratio | 1.0 | 0.5 | 2.0 | triangular | EV_RI_mix | ev_ensemble_particle_route_response | relative_with_priors |
| EV_ensemble | contaminant_fraction_proxy | fraction | 0.08 | 0.0 | 0.25 | triangular | EV_contaminant_mix | ev_ensemble_particle_route_response | relative_with_priors |
| EV_ensemble | doublet_fraction_proxy | fraction | 0.03 | 0.0 | 0.12 | triangular | EV_doublet_mix | ev_ensemble_particle_route_response | relative_with_priors |

Latin-hypercube construction is fixed before execution:

```text
sample_count = 24
quantile_rule = centered rank quantiles q_i = (i + 0.5) / 24
per_factor_permutation = stable SHA256 permutation of factor_name and seed policy
correlation_rule = factors with the same correlation_group share the base quantile, then apply correlation_transform
correlation_transform_rule = direct uses q; inverse uses 1 - q; independent_within_group uses a factor-specific deterministic permutation
clamp_rule = all sampled values are clamped to inclusive min/max before use
log_uniform_rule = interpolate uniformly in log space between positive min/max
triangular_rule = piecewise-linear quantile with nominal as mode
truncated_normal_rule = deterministic normal quantile clamped to min/max with nominal center
missing_field_rule = fail closed; factor cannot enter R3b
```

## Route-Sensitive Priors

R3b must explicitly avoid purely global scenario multipliers.

Each prior sample should include route-sensitive response diagnostics:

```text
BFP_route_sensitivity_index
detector_route_sensitivity_index
wall_PEG_route_sensitivity_index
blank_RIN_route_sensitivity_index
thermal_404_route_sensitivity_index
global_multiplier_dominance_index
route_sensitive_prior_status
```

Stop or revise if:

```text
global_multiplier_dominance_index > 0.8 for all top route shifts
route_sensitive_prior_status = global_scalar_dominated
```

The diagnostic formulas are fixed before execution. For each factor group,
compute route effects as `effect_delta[group, route]`, using this fixed signed
log-ratio convention:

```text
effect_delta[group, route] =
  median_over_particles_seeds_prior_samples(
    log(
      (score_with_group_effect[group, route] + eps)
      /
      (nominal_score[route] + eps)
    )
  )

effect_delta_convention =
  median_log_score_ratio_over_particles_seeds_prior_samples
```

If an R3b implementation uses decomposed group components instead of explicit
group ablation, then `group_component_log_multiplier[group, route]` must be
mathematically equivalent to the signed log-ratio above and exported with the
same convention label. Raw score differences, rank shifts, and z-normalized
effects are not allowed as `effect_delta` for the R3b route-sensitivity gate.

The route means must be computed over the same particle panel, prior sample
count, and seed policy for both `score_with_group_effect` and `nominal_score`.

```text
route_sensitive_index[group] =
  variance_across_routes(effect_delta[group, route]) /
  (
    variance_across_routes(effect_delta[group, route])
    + mean(effect_delta[group, route])^2
    + eps
  )

global_multiplier_dominance_index =
  abs(mean_effect_across_routes) /
  (
    abs(mean_effect_across_routes)
    + std_effect_across_routes
    + eps
  )

eps = 1e-12
```

Status bins:

```text
route_sensitive_prior_status = route_sensitive
  if max_group_route_sensitive_index >= 0.25
  and global_multiplier_dominance_index <= 0.8

route_sensitive_prior_status = global_scalar_dominated
  if global_multiplier_dominance_index > 0.8

route_sensitive_prior_status = under_resolved_route_sensitivity
  if max_group_route_sensitive_index < 0.25
  and global_multiplier_dominance_index <= 0.8
```

`global_scalar_dominated` and `under_resolved_route_sensitivity` are stop/revise
statuses before any R4 plan can be prepared.

## Proposed R3b Outputs

If authorized later, R3b should write only under:

```text
results/ev_nodi_realism_v2_uncertainty_R3b/
```

Required files:

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

Root `run_manifest.json` may be updated only after successful R3b completion and
must record:

```text
R2_anchor_smoke_run = true
R3_reduced_grid_run = true
R3a_reduced_grid_named_bundle_survey_run = true
R3b_uncertainty_expansion_run = true
R4_representative_full_wave_validation_run = false
R5_full_grid_v2_run = false
v1_full_grid_overwritten = false
Tsuyama_paper_fit_continued = false
selected_annulus_bounds_changed = false
calibrated_SNR_claim_emitted = false
ET2030_direct_current_input_unlocked = false
```

## Proposed R3b Tests Before Execution

The following active focused test file has been added before R3b execution:

```text
tests/test_realism_v2_r3b_plan.py
```

It must pass before running R3b, and it covers:

```text
test_R3b_cost_cap_blocks_over_cap_uncertainty_design
test_R3b_prior_table_has_numeric_bounds_correlations_and_formulas
test_R3b_prior_table_requires_correlation_transform_for_grouped_factors
test_R3b_prior_correlation_transforms_are_physically_coherent
test_R3b_route_panel_includes_532_800x1500_and_respects_cap
test_R3b_context_routes_cannot_be_promoted
test_R3b_route_roles_remain_locked
test_R3b_route_sensitive_formula_separates_global_scalar_from_route_effects
test_R3b_effect_delta_uses_fixed_median_log_score_ratio_convention
test_R3b_global_multiplier_dominance_blocks_progression
test_R3b_detectability_contract_is_not_event_probability
test_R3b_manifest_plan_keeps_R4_R5_false_and_hardening_flags_false
test_R3b_missing_prior_field_fails_closed
```

After R3b execution authorization, the implementation must add output-level
tests for required files, cap enforcement, manifest gates, provenance fields,
legacy SNR header absence, route-sensitive diagnostics, context-route governance,
uncertainty-band overlap matrix reporting, detector/blank/thermal guardrails, and
scenario-spread watch on generated R3b CSVs before any result review bundle is
prepared.

## Proposed R3b Promote / Stop Gates

R3b may be considered stable enough to prepare an R4 plan only if:

```text
main_660 remains competitive under uncertainty or shifts with physical explanation
context-route highs are either robust candidates or demoted as stress-test artifacts
optional 660 / 900x1400 remains governed separately unless explicitly reclassified
BFP/slit, detector, wall/PEG, blank/RIN, and thermal priors show route-sensitive effects
global multiplier dominance does not control top route changes
scenario SNR spread stays below 1e3 or has physical explanation
uncertainty bands do not make every route overlap every route
anchor/R3a shared ranking correlation remains >0.7 or failure is explained
```

Stop or revise if:

```text
ranking controlled by one unconstrained optical-throughput scalar
global_multiplier_dominance_index > 0.8 for all top route shifts
wall adsorption prior alone determines all conclusions
detector path gives opposite route rankings without settled instrumentation
404 routes are all thermal red or saturating
false-positive prior dominates all EV scenarios
uncertainty bands are so wide that every route overlaps every route
legacy SNR names appear in outputs
calibrated_absolute SNR appears without measured artifacts
ET2030 direct current-input is unlocked without real measured artifact
```

## External Review Question

Ask GPT-Pro:

```text
Given R3a passed and the next issue is route-role stability under uncertainty,
is this R3b route-sensitive uncertainty-expansion plan sufficiently constrained
to authorize R3b only? If yes, authorize only R3b under the 31,464-row cap and
the listed output/test/manifest constraints. Do not authorize R4 or R5.
```
