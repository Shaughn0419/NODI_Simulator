# EV NODI realism v2 R6 route-prior sensitivity plan

## Decision boundary

This bundle prepares an R6 plan for external review after:

```text
PASS_R5_3_RESULTS_PREPARE_R6_PLAN_ONLY
```

It does not authorize R6 execution. It also does not authorize R5 follow-up expansion, new scenario bundles, stochastic seeds, solver cases, experiments, route promotion, main-660 redefinition, selected-annulus changes, calibrated SNR, calibrated event probability, absolute LOD, true EV concentration, biological specificity, Tsuyama paper-fit continuation, v1 overwrite, or ET2030 direct current-input unlock.

## R5.3 carry-forward

R5.3 selected the following explanatory prior candidate:

```text
selected_candidate_prior_id = global_width_quadratic_regularization
selected_candidate_prior_family = global_width_depth_regularization_family
selected_candidate_dof_count = 1
```

The candidate is:

```text
min(1.0, width_nm / 800.0) ** 2
```

R5.3 showed that this low-dimensional family-level width prior explains the R5.2 weak-reference and narrow/deep context-route warning without route-specific fitting:

```text
weak_reference_delta_explained_fraction = 1.0
context_family_delta_explained_fraction = 1.0
context_routes_above_main_after_candidate = 0
context_scenario_rows_above_main_after_candidate = 0
weak_reference_scenario_rows_above_main_after_candidate = 0
```

R6 treats this as a hypothesis, not a calibrated physical law.

## R6 plan scope

The R6 plan is a bounded route-prior sensitivity plan over existing R5/R5.3 artifacts only:

```text
future_R6_execution_type_if_reviewed =
  bounded_existing_R5_artifact_route_prior_sensitivity_audit_only

max_existing_R5_source_rows_if_future_reviewed = 14784
max_R6_derived_candidate_rows = 177408
route_id_count = 33
source_particles_per_route = 56
scenario_bundle_count = 8
stochastic_seed_count = 0
new_case_rows_authorized = 0
new_scenario_bundle_authorized = false
new_stochastic_seed_authorized = false
new_solver_case_authorized = false
new_experiment_authorized = false
```

The route set remains exactly the R5.2/R5.3 33-route audit set:

```text
2 locked main-660 comparators
1 weak-reference control
1 optional 660 robustness probe
3 medium/shortwave controls
6 selected-annulus sidecars
20 above-main context warning routes
```

Main-660 remains locked to:

```text
660_800x1400
660_800x1500
```

The R6 comparator policy is explicit:

```text
primary_pass_fail_comparator = candidate_adjusted_locked_main_660
secondary_diagnostic_comparator = unadjusted_locked_main_660
locked_main_660_route_ids = 660_800x1400 / 660_800x1500
main_660_redefinition_authorized = false
report_optional_900_diagnostics = true
```

This matters for pivot values above 800 nm, where locked main-660 itself can receive a prior factor below 1.0. Future R6 outputs must report both candidate-adjusted-main deltas and unadjusted-main diagnostic deltas.

## Candidate prior sensitivity grid

The plan registers 12 named candidate priors. The grid is intentionally named and bounded, not a broad Cartesian expansion.

```text
width_linear_800
width_exp1p5_800
global_width_quadratic_regularization
width_quad_750
width_quad_850
width_quad_900
width_quad_floor025
width_quad_floor035
width_quad_floor050
width_exp2p5_wall_transport
reference_band_penalty
BFP_alignment_risk
```

The nearby confirmation rule is:

```text
same_family_required = true
candidate_dof_count_max = 2
max_width_exponent_delta = 0.5
max_pivot_delta_nm = 50
max_floor_delta = 0.15
non_width_alternatives_count_as_nearby_confirmation = false
```

Non-width alternatives are deterministic diagnostics only:

```text
reference_band_penalty =
  max(0.65, min(1.0, source_v1_relative_score / 0.16))

BFP_alignment_risk =
  min(1.0, width_nm / 800.0) ** 0.5
  * min(1.0, 1400.0 / depth_nm) ** 0.25
```

They may only use pre-existing R5 artifact columns and cannot use manual route-ID multipliers, scenario-specific per-route fits, or particle-specific empirical fits.

The width sensitivity anchors are:

```text
pivot_width_nm values = 750, 800, 850, 900
width_exponent values = 1.0, 1.5, 2.0, 2.5
width_factor_floor values = 0.25, 0.35, 0.50
```

The selected R5.3 candidate is included as the anchor:

```text
global_width_quadratic_regularization
formula = min(1.0, width_nm / 800.0) ** 2.0
```

## Required future outputs if R6 execution is later externally authorized

```text
R6_route_prior_sensitivity_manifest.csv
R6_candidate_prior_registry.csv
R6_candidate_prior_sensitivity_matrix.csv
R6_route_prior_factor_by_route.csv
R6_route_family_residual_warning_table.csv
R6_scenario_residual_warning_table.csv
R6_particle_stratum_residual_warning_table.csv
R6_main660_locked_comparator_summary.csv
R6_selected_annulus_and_404_sidecar_guardrail_summary.csv
R6_claim_boundary_guardrail_summary.csv
R6_stop_gate_summary.csv
R6_next_stage_recommendation_matrix.csv
run_manifest.json
R6_route_prior_sensitivity_report.md
```

The required sensitivity output fields include:

```text
candidate_prior_id
candidate_prior_family
width_pivot_nm
width_exponent
width_factor_floor
physical_basis
dof_count
complexity_penalty
route_prior_factor
old_score
candidate_score
delta_removed
main660_comparator_policy
main660_old_score
main660_candidate_score
main660_prior_factor
main660_score_retention_fraction
context_vs_candidate_adjusted_main_delta
context_vs_unadjusted_main_delta
optional_900_vs_candidate_adjusted_main_delta
optional_900_vs_unadjusted_main_delta
residual_delta_vs_main
residual_above_main_flag
scenario_residual_above_main_count
particle_stratum_residual_above_main_count
uses_route_specific_multiplier
uses_scenario_specific_per_route_fit
uses_particle_specific_empirical_fit
changes_main_660_definition
authorizes_route_promotion
claim_level
```

## Future pass/fail logic

A future externally reviewed R6 execution can only support a next-stage plan if it shows:

```text
at_least_two_nearby_low_dimensional_candidates_explain_warning = true
no_route_specific_or_scenario_specific_or_particle_specific_fit = true
context_routes_above_main_after_candidate_zero_or_residual_explained = true
weak_reference_not_systematically_above_main = true
main_660_definition_unchanged = true
optional_660_900x1400_not_main_660 = true
selected_annulus_parallel_lens_only = true
claim_boundary_absolute_blocked = true
```

If reasonable priors leave context routes above main-660, the future result should prepare a route-governance revision plan for review, not promote routes directly. If only route-specific multipliers, scenario-specific per-route fits, particle-specific fits, or other forbidden families can resolve the warning, R6 should stop and report that the prior explanation failed.

## Guardrails

The plan keeps these blocked:

```text
R6_execution_authorized = false
R5_followup_expansion_authorized = false
new_scenario_bundle_authorized = false
new_stochastic_seed_authorized = false
new_solver_case_authorized = false
new_experiment_authorized = false
context_route_promotion_authorized = false
main_660_redefinition_authorized = false
route_specific_manual_prior_multipliers_authorized = false
scenario_specific_per_route_fit_authorized = false
particle_specific_empirical_fit_authorized = false
calibrated_SNR_claim_authorized = false
calibrated_event_probability_authorized = false
absolute_LOD_claim_authorized = false
true_EV_concentration_claim_authorized = false
biological_specificity_claim_authorized = false
```

Claim boundaries remain:

```text
SNR_claim_level = absolute_blocked
event_probability_claim_level = absolute_blocked
p_detect_mapping_claim_level = relative_with_priors
```

## Provenance

The plan freezes all R5.3 source artifacts through SHA-256 checksums:

```text
R5_3_manifest_checksum
R5_3_score_decomposition_checksum
R5_3_context_driver_checksum
R5_3_weak_reference_driver_checksum
R5_3_candidate_registry_checksum
R5_3_forbidden_guardrail_checksum
R5_3_main660_checksum
R5_3_sidecar_guardrail_checksum
R5_3_claim_guardrail_checksum
R5_3_decision_table_checksum
R5_3_next_stage_matrix_checksum
R5_3_run_manifest_checksum
```

## Validation

Local validation performed for this plan:

```text
python -m json.tool configs/realism_v2/r6_route_prior_sensitivity_plan.yaml
python - <<'PY'
import realism_v2 as rv2
p = rv2.validate_R6_route_prior_sensitivity_plan()
print(p["schema_version"], p["stage"])
print(len(p["candidate_prior_sensitivity_design"]["candidate_prior_ids"]))
PY
ruff check realism_v2.py tests/test_realism_v2_R6_plan.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_realism_v2_R6_plan.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_realism_v2_R6_plan.py \
  tests/test_realism_v2_R5_3_route_prior_model_revision_audit.py \
  tests/test_realism_v2_R5_3_route_prior_model_revision_plan.py \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit.py \
  tests/test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py \
  tests/test_realism_v2_R5_1_interpretation.py \
  tests/test_realism_v2_R5_1_next_stage_plan.py \
  tests/test_realism_v2_R5_full_grid_v2.py \
  tests/test_realism_v2_R5_plan.py \
  tests/test_realism_v2_contract.py
```

Results:

```text
R6 focused tests: 12 passed
R6/R5.3/R5.2/R5.1/R5/contract focused suite: 113 passed
full suite: 886 passed in 206.22s
extracted review bundle focused suite: 113 passed in 12.39s
ruff: All checks passed
```
