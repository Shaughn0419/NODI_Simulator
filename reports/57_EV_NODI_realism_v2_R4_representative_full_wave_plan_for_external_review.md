# EV/NODI Realism v2 R4 Representative Full-Wave Validation Plan for External Review

Date: 2026-05-07
Input gate: PASS_R3B_RESULTS_PREPARE_R4_PLAN_ONLY from 2026-05-06 external review

## Scope

This is a plan for external review. It is not R4 execution output.

The only requested next authorization is:

```text
R4 representative full-wave validation only
```

Still not authorized:

```text
R4 execution before external review passes
R5 full-grid v2
v1 full-grid overwrite
Tsuyama paper-fit continuation
selected-annulus bound changes
context-route promotion
calibrated SNR
calibrated event probability
absolute LOD
true EV concentration
biological specificity
ET2030 direct current-input unlock
```

The machine-readable plan is:

```text
configs/realism_v2/r4_representative_full_wave_plan.yaml
schema_version = R4_representative_full_wave_plan_v1
```

## R3b Evidence Motivating R4

GPT-Pro returned:

```text
PASS_R3B_RESULTS_PREPARE_R4_PLAN_ONLY
```

R3b was accepted as a capped route-sensitive uncertainty expansion:

```text
routes = 19
particles = 23
prior_samples = 24
seeds = 42 / 43 / 44
case_rows = 31,464
under_R3b_review_cap = true
R4/R5 = false
```

The R3b anti-global-scalar gate passed:

```text
route_sensitive_prior_status = route_sensitive
global_multiplier_dominance_index = 0.310657
global_scalar_dominated_stop_gate = false
```

Context routes remained high under route-sensitive uncertainty:

| route | R3b median relative-prior score | role |
|---|---:|---|
| 532 / 900x1500 | 0.276189 | context |
| 660 / 900x1500 | 0.273274 | context |
| 488 / 900x1500 | 0.262886 | context |
| 532 / 900x1400 | 0.261323 | context |
| 532 / 800x1500 | 0.253658 | context |
| 660 / 800x1500 | 0.250806 | locked main_660 |
| 660 / 800x1400 | 0.237290 | locked main_660 |

Interpretation:

```text
These are R4 validation candidates, not promoted routes.
Uncertainty bands overlap heavily, so R4 should validate physics, not declare a winner.
```

## R4 Scientific Question

R4 should answer:

```text
Do representative full-wave observables support or demote the route-role patterns
seen in R3b, especially high context-route medians, under explicit BFP/slit,
pinhole, interface, and near-wall assumptions?
```

R4 should not answer:

```text
absolute LOD
absolute SNR
true EV concentration
biological specificity
calibrated event probability
full-grid v2 ranking
context-route promotion
```

## Representative Route Panel

Use 9 routes, capped and role-locked:

| route | role | R4 purpose |
|---|---|---|
| 660 / 800x1400 | main_660 | locked baseline main-660 validation |
| 660 / 800x1500 | main_660 | stronger locked main-660 validation |
| 660 / 900x1400 | optional_robustness_probe | optional 660 robustness, no redefinition |
| 532 / 900x1500 | context_validation_candidate | top R3b context median |
| 660 / 900x1500 | context_validation_candidate | longwave wide/deep context check |
| 532 / 800x1500 | context_validation_candidate | context-to-main geometry bridge |
| 404 / 600x1300 | shortwave_mechanism_candidate | shortwave mechanism plus thermal gate |
| 404 / 800x600 | selected_annulus_sanity_overlap_shortwave | shortwave sanity lens only |
| 660 / 800x600 | selected_annulus_sanity_overlap_longwave | longwave sanity lens only |

Every route row must keep:

```text
route_role_locked = true
route_role_source = R4_plan_v1
context_route_promotion_authorized = false
```

Each route must also define:

```text
validation_question
confirm_if
demote_if
reclassify_if
```

## Representative Particle Panel

Use 6 representative particles:

| particle | role |
|---|---|
| blank | blank reference and false-positive floor |
| EV70_lowRI | small low-RI stress case |
| EV100_nominal | nominal EV reference |
| EV250_nominal | large EV upper-tail case |
| LDL_like_contaminant | optical contaminant control |
| Au40 | metal standard amplitude/phase control |

No particle row may permit biological specificity claims.

## Particle Material Contract

The machine-readable plan now includes:

```text
particle_material_contract
```

Every particle has:

```text
particle_id
diameter_nm
size_convention
shape_model
core_RI
shell_RI
shell_thickness_nm
medium_RI_source
material_database_key
wavelength_interpolation_policy
absorption_imaginary_RI_policy
near_wall_pose_policy
biological_specificity_claim_allowed = false
```

Representative definitions:

| particle | shape | diameter_nm | optical model |
|---|---|---:|---|
| blank | no_particle_medium_only | 0 | blank medium only |
| EV70_lowRI | core_shell_sphere | 70 | core_RI 1.36, shell_RI 1.43, shell 5 nm |
| EV100_nominal | core_shell_sphere | 100 | core_RI 1.39, shell_RI 1.45, shell 5 nm |
| EV250_nominal | core_shell_sphere | 250 | core_RI 1.39, shell_RI 1.45, shell 5 nm |
| LDL_like_contaminant | homogeneous_sphere | 25 | RI 1.46 |
| Au40 | homogeneous_sphere | 40 | Johnson_Christy_1972 Au complex nk |

EV and LDL-like priors use constant real RI across 404-660 nm for this
representative validation and do not claim dispersion, absorption, or
biological specificity. Au40 uses a named complex-nk material database key with
linear interpolation.

## Solver Scope

Allowed solver family:

```text
FEM / modal equivalent
FDTD or BEM equivalent only if an implemented solver call path is documented
```

Planned states:

```text
interface_states = centerline_nominal / near_wall_stress
polarization_states = nominal_linear / orthogonal_sensitivity
mesh_levels = coarse_screen / review_refined
```

Execution status in this plan:

```text
not_run_plan_only
```

This plan must not call a full-wave solver or generate R4 result outputs before
external authorization.

## Executable Solver Case Contract

The machine-readable plan now includes:

```text
solver_case_contract
```

Required contract fields:

```text
solver_engine_class = FEM_modal_equivalent
solver_name_or_backend = internal_channel_modal_green_BFP_R4_v2
geometry_units = nm
domain_extent_policy
boundary_conditions
PML_or_open_boundary_settings
material_model_source_by_wavelength
particle_pose_definition
near_wall_stress_distance_nm = 10
centerline_nominal_position_definition
source_type = unit_plane_wave
source_normalization
polarization_vector_definition
BFP_far_field_extraction_method
BFP_coordinate_convention
BFP_jacobian_policy
slit_ROI_definition
pinhole_ROI_definition
mesh_level_definitions_nm
mesh_refinement_region
mesh_convergence_metric
mesh_convergence_threshold = 0.15
solver_boundary_sensitivity_threshold = 0.25
```

Named states have executable definitions, not just labels:

```text
centerline_nominal:
  particle_center_x_nm = 0
  particle_center_y_nm = 0
  particle_center_z_policy = channel_midplane

near_wall_stress:
  nearest_wall_clearance_nm = 10
  wall_selection = nearest_width_sidewall
  particle_center_z_policy = channel_midplane
```

Polarization states are fixed as vectors:

```text
nominal_linear:
  E_vector_xyz = [1, 0, 0]
  propagation_direction_xyz = [0, 0, 1]

orthogonal_sensitivity:
  E_vector_xyz = [0, 1, 0]
  propagation_direction_xyz = [0, 0, 1]
```

Mesh levels are numeric:

```text
coarse_screen:
  base_cell_nm = 8
  particle_surface_cell_nm = 2
  minimum_cells_across_shell = 3

review_refined:
  base_cell_nm = 4
  particle_surface_cell_nm = 1
  minimum_cells_across_shell = 5
```

BFP and ROI extraction are fixed before execution:

```text
BFP extraction = near-to-far transform on closed box
BFP coordinates = direction cosines u = sin(theta_x), v = sin(theta_y)
valid domain = u^2 + v^2 <= NA^2, NA = 0.8
Jacobian = 1 / sqrt(1 - u^2 - v^2)
slit ROI = center (0,0), width_u 0.12, height_v 1.4
pinhole ROI = center (0,0), radius_uv 0.18
same operator applied to reference and scattering = true
```

The active validator fails if an interface, polarization, or mesh state is only
a string label without a numeric or procedural definition.

## Observables

Required observables:

```text
BFP_complex_field
slit_intensity_perturbation
pinhole_intensity_perturbation
near_wall_interface_sensitivity
surrogate_full_wave_delta
```

Claim levels:

```text
BFP_complex_field = diagnostic_only
near_wall_interface_sensitivity = diagnostic_only
slit / pinhole / surrogate deltas = relative_with_priors
```

Power-like ROI perturbations must remain in watts where applicable. Relative
log deltas must be labeled as relative or diagnostic, not calibrated absolute.

## Cost Cap

R4 representative validation is capped at:

```text
max_R4_representative_routes = 9
max_R4_representative_particles = 6
max_R4_interface_states = 2
max_R4_polarization_states = 2
max_R4_mesh_levels = 2
max_R4_solver_cases_before_review = 9 * 6 * 2 * 2 * 2 = 432
```

The pre-run estimator must fail closed if:

```text
under_R4_review_cap = false
```

## Promotion / Demotion Criteria

Allowed R4 decision labels:

```text
confirm_for_future_review
demote_from_R4_candidate
reclassify_requires_external_review
inconclusive_requires_plan_revision
```

R4 may confirm that a route is worth future review. It may demote a route from
the R4 candidate set. It may not promote context routes, redefine main_660, or
change selected-annulus governance.

The decision bins are numeric and pre-registered:

```text
eps = 1e-12

sign_preserved =
  sign(full_wave_cross_term) == sign(surrogate_cross_term)

surrogate_delta_log =
  log((abs(full_wave_ROI_signal) + eps) /
      (abs(surrogate_ROI_signal) + eps))

confirm_for_future_review if:
  sign_preserved
  abs(surrogate_delta_log) <= 0.35
  mesh_refined_delta_abs <= 0.15
  polarization_sensitivity_abs <= 0.50
  near_wall_stress_delta_abs <= 0.75
  no claim-boundary stop gate triggers

demote_from_R4_candidate if:
  sign mismatch
  abs(surrogate_delta_log) >= 0.75
  ROI mapping reverses route-family ordering
  full-wave identifies BFP/slit/pinhole surrogate artifact
  thermal sidecar blocks 404 interpretation

inconclusive_requires_plan_revision if:
  mesh_refined_delta_abs > 0.15
  solver_boundary_sensitivity_abs > 0.25
  BFP extraction normalization unit guard fails
```

The exact thresholds are stored in:

```text
promotion_demotion_criteria.numeric_decision_thresholds
promotion_demotion_criteria.numeric_decision_bins
```

Route-specific interpretation:

```text
main_660:
  confirm if full-wave sign, relative magnitude, and BFP/slit mapping support
  R3b surrogate behavior.

optional_660:
  confirm only as optional robustness evidence; no main_660 redefinition.

context routes:
  confirm only as future-review candidates; no experimental recommendation or
  route promotion.

404 / selected-annulus sanity:
  confirm only if optical observables are not thermal-score bonuses and
  selected-annulus remains a parallel sanity lens.
```

## R3b Hardening Carried Into R4

Before any R4 execution, the plan requires an active hardening status:

```text
R3b_effect_delta_hardening_status =
  exported_both
  | equivalence_test_passed
  | convention_renamed
```

The current plan sets:

```text
R3b_effect_delta_hardening_status = equivalence_test_passed
effect_delta_equivalence_test_name =
  test_R4_R3b_group_component_log_multiplier_equivalence_is_active
```

The active helper proves that if a group component is already a signed log
multiplier, reconstructing:

```text
score_with_group_effect = nominal_score * exp(group_component_log_multiplier)
```

returns the same median log score ratio used by the R3b effect_delta
convention.

The thermal sidecar naming must avoid ambiguity:

```text
thermal_not_blocking_stage_progression = true
context_route_promotion_authorized = false
route_promotion_eligible = false
```

R3b uncertainty-band overlap remains a caution:

```text
R4 validates candidate physics.
R4 does not rank, promote, or claim conclusive superiority.
```

## Required Outputs If Later Authorized

If an external review later authorizes R4 execution, it must write only:

```text
results/ev_nodi_realism_v2_representative_full_wave_R4/
  full_wave_case_manifest.csv
  full_wave_observable_summary.csv
  route_validation_decision_table.csv
  BFP_slit_pinhole_observable_comparison.csv
  interface_near_wall_sensitivity_summary.csv
  surrogate_vs_full_wave_delta_summary.csv
  context_route_governance_summary.csv
  thermal_404_full_wave_gate_summary.csv
  detector_blank_claim_guardrail_summary.csv
  full_wave_cost_estimate.csv
  run_manifest.json
  R4_representative_full_wave_validation_report.md
```

No R5 or full-grid v2 output directory is authorized.

## Manifest Fields

Before R4 external authorization, the root and plan manifests must keep:

```text
R4_representative_full_wave_validation_run = false
R5_full_grid_v2_run = false
v1_full_grid_overwritten = false
Tsuyama_paper_fit_continued = false
selected_annulus_bounds_changed = false
calibrated_SNR_claim_emitted = false
ET2030_direct_current_input_unlocked = false
```

If R4 is later authorized and executed, the R4 result manifest may set:

```text
R4_representative_full_wave_validation_run = true
```

but must still keep:

```text
R5_full_grid_v2_run = false
v1_full_grid_overwritten = false
Tsuyama_paper_fit_continued = false
selected_annulus_bounds_changed = false
calibrated_SNR_claim_emitted = false
ET2030_direct_current_input_unlocked = false
```

## Stop Gates

Any of these blocks R4 execution or progression:

```text
R4 execution without external authorization
R5 or full-grid v2 started
context-route promotion attempted
calibrated SNR or calibrated event-probability claim emitted
ET2030 direct current-input unlocked without measured/calibrated bench artifact
selected-annulus bounds changed
v1 full-grid output overwritten
thermal sidecar used to increase NODI score
finite-zero-event blank safety claim emitted
legacy detector_SNR / calibrated_detector_SNR output header emitted
```

The validator requires every stop gate above. The active test deletes each
required stop gate one by one and confirms the plan fails closed.

## Active Pre-Run Tests

The active R4 plan test file is:

```text
tests/test_realism_v2_r4_plan.py
```

It verifies:

```text
R4 cost cap blocks over-cap solver designs
route panel is representative and context routes are not promoted
particle panel is representative and carries no specificity claims
particle material contract defines optical parameters
solver scope, observables, and required outputs are defined
solver case contract has numeric executable definitions
solver states cannot remain string-only labels
pre-run plan is plan-only and under cap
manifest keeps R4 execution false and R5 false
numeric decision thresholds are pre-registered
stop gates and decision criteria are active
R3b effect_delta hardening has an active equivalence status
missing route criteria fail closed
each required stop gate is validated fail-closed
```

## Review Request

External reviewer should decide only whether this plan is tight enough to
authorize:

```text
R4 representative full-wave validation only
```

Allowed review decisions:

```text
PASS_TO_R4_REPRESENTATIVE_FULL_WAVE_VALIDATION_ONLY
CONDITIONAL_FIX_R4_PLAN_BEFORE_RUN
FAIL_HALT_BEFORE_R4
```

Even a pass must not authorize R5/full-grid v2 or any calibrated absolute claim.
