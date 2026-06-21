# Report 149 - NODI/COMSOL next-artifact design plan

Date: 2026-06-17

Status:

```text
design_contract_only; no runner execution authorized
```

This report turns the COMSOL-side confirmation for the next NODI artifacts into
a bounded NODI-side design contract. It is a launch-review input, not a
simulation result.

## 1. Boundary

This plan does not authorize:

```text
new NODI recomputation
new COMSOL runs
JOINT_ROUTE_CLASS regeneration
scalar joint scores
q_ch * eta products
q_ch * chi_selected * eta products
yield or throughput detection claims
calibrated SNR / LOD / FPR
EV detection probability
fabrication release
numeric chi_selected
numeric true W_eff
non-rectangular full-wave solver claims
```

Allowed scope:

```text
schema design
pilot matrix definition
hard-fail policy
claim-boundary policy
future launch-review checklist
```

The NODI role remains:

```text
conditional optical response provider, not joint scorer
```

COMSOL may later provide transported distributions and geometry descriptors.
NODI may later provide conditional optical response surfaces and effective
aperture sensitivity. The joint layer may only reference immutable source rows
and emit class/veto/provenance fields.

## 2. Current artifact feasibility

The current V1 handoff package at `exports/nodi_comsol_handoff_v1/` is adequate
for `JOINT_ROUTE_CLASS` V1. It is not yet a position-response package.

Current available NODI layers:

| source | grain | useful for | not sufficient for |
|---|---|---|---|
| `NODI_EVIDENCE_CONNECTOR_rawrow_proxy.csv` | route x view x particle x seed | per-particle route proxy, dwell caution, guardrail join | per-bin position response |
| `NODI_REFERENCE_GUARDRAIL_TABLE.csv` | route | immutable reference guardrail | W_eff / non-rectangular optical truth |
| `seed_*_raw_rows.csv` | route x particle x seed | P0 extraction, size-bin proxy | per-event spatial response |
| `seed_*_diagnostic_rows.csv` | route x particle x seed with wide diagnostics | aggregate selected-annulus context | direct `edge_norm` or `x/z` response bins |

Observed current diagnostics include aggregate fields such as:

```text
selected_detector_mode_annulus_n_events
selected_detector_mode_annulus_n_detected
selected_detector_mode_annulus_detection_rate
selected_detector_mode_annulus_mean_edge_norm
mean_abs_initial_x_norm
mean_abs_initial_z_norm
```

They do not provide a complete response surface with:

```text
edge_norm_bin
x_norm_bin
z_norm_bin
n_events_bin
n_detected_bin
eta_response_proxy
```

Therefore `NODI_POSITION_RESPONSE_SURFACE` is not a simple reshaping of the
current P0 handoff CSV. It requires a new bounded sidecar runner or a new
event-bin summary export path. That runner must be separately authorized after
this design contract is reviewed.

## 3. Artifact A: NODI_POSITION_RESPONSE_SURFACE

### 3.1 Purpose

`NODI_POSITION_RESPONSE_SURFACE` provides conditional optical response by
initial-position bin. It lets a future COMSOL transported-position distribution
weight NODI optical response without double-counting NODI's synthetic
`annulus_fraction`.

It does not provide:

```text
chi_selected
yield
q_ch-weighted detection
transported occupancy
fabricated-geometry truth
```

### 3.2 Required output families

Output two response families:

| family | P1 bins | reason |
|---|---:|---|
| `edge_norm_1d` | 20 bins over 0.0 to 1.0, width 0.05 | directly joins selected-annulus / Chebyshev logic |
| `xz_norm_2d` | 21 x 21 grid over [-1, 1] x [-1, 1] | preserves asymmetry lost by `edge_norm` |

P2 optional refinement:

```text
xz_norm_2d = 41 x 41
```

Only use the P2 grid if P1 shows decision-changing edge gradients or strong
selected-window sensitivity.

Required special aggregate rows:

| aggregate_id | definition |
|---|---|
| `near_center_0p0_0p5` | `0.0 <= edge_norm < 0.5` |
| `selected_annulus_0p5_0p8` | `0.5 <= edge_norm <= 0.8` |
| `near_wall_0p8_1p0` | `0.8 < edge_norm <= 1.0` |

### 3.3 Pilot route scope

P1 core:

```text
404/W500/D900
404/W500/D1200
660/W800/D900
660/W800/D1200
```

P1 diagnostic/context:

```text
404/W600/D900
```

P2 diagnostic trap:

```text
660/W500/D1500
```

Rules for the trap route:

```text
reference_too_weak guardrail remains binding
hydraulic transport cannot rescue it
output role = high_proxy_guarded_trap_example_only
```

### 3.4 Pilot diameter scope

P1 minimum:

```text
40, 100, 150, 220, 250, 270, 290, 300 nm
```

P1 preferred:

```text
40, 60, 100, 150, 220, 230, 240, 250, 260, 270, 280, 290, 300 nm
```

P2 full pilot:

```text
P1 preferred set, plus any additional exact bins requested by a passed
COMSOL transported-distribution contract
```

500 nm remains outside the NODI particle library:

```text
NODI optical eta = blank
NODI status = out_of_particle_library_scope
joint role = RC13 only
```

### 3.5 Preferred response semantics

The preferred P1 response surface is bin-conditioned, not global-distribution
weighted.

Allowed generation modes:

| mode | status | use |
|---|---|---|
| `bin_conditioned_initial_position_sampling` | preferred | response surface |
| `posthoc_existing_event_stream_binning` | diagnostic only | feasibility / smoke |
| `legacy_annulus_aggregate_only` | insufficient | not a response surface |

For `bin_conditioned_initial_position_sampling`, each bin should define its own
initial-position sampling domain. Within-bin samples are not a COMSOL
transport distribution. They are a NODI optical response probe.

Seed grain:

```text
The COMSOL-facing P1 response surface row is post-seed aggregated at the
route/lambda/W/D/diameter/bin grain.
Per-seed rows are allowed only in a diagnostic sidecar, not as the primary
COMSOL join table.
```

This keeps the primary table aligned to the COMSOL distribution grain while
retaining reproducibility through seed-manifest provenance.

### 3.6 Minimum schema

Required columns:

```text
artifact_id
response_surface_version
route_id_nodi
lambda_nm
W_nominal_nm
D_nm
NODI_view
particle_kind
size_bin_nm
seed_scope
n_random_seeds
seed_manifest_sha256
distribution_type
row_kind
aggregate_id
bin_id
edge_norm_min
edge_norm_max
edge_norm_center
x_norm_min
x_norm_max
x_norm_center
z_norm_min
z_norm_max
z_norm_center
denominator_basis
position_sampling_mode
position_distribution_assumption
n_events_bin
n_detected_bin
bin_status
eta_response_proxy
eta_response_wilson_lb
peak_proxy_bin
margin_proxy_bin
mean_peak_width_s_bin
mean_transit_time_ms_bin
phase_flip_fraction_bin
reference_operating_band
guardrail_status
source_runner
source_config_sha256
source_manifest_sha256
claim_boundary
not_chi_selected
not_yield
not_q_ch_weighted
not_calibrated_detection
```

Column constants:

```text
claim_boundary = no_measured_data_conditional_optical_response_proxy
seed_scope = aggregate_across_seeds
not_chi_selected = true
not_yield = true
not_q_ch_weighted = true
not_calibrated_detection = true
```

Allowed row-kind and status values:

```text
row_kind = base_bin | special_aggregate
aggregate_id = none | near_center_0p0_0p5 | selected_annulus_0p5_0p8 | near_wall_0p8_1p0
bin_status = ok | insufficient_bin_events | empty_bin | guardrail_blocked
```

Aggregate-row encoding:

```text
For row_kind = special_aggregate:
  bin_id must equal aggregate_id.
  aggregate_id must be one of the three required aggregate ids.
  The edge_norm bounds must encode the aggregate definition.
  x_norm and z_norm bounds/centers are blank unless the aggregate is computed
  inside an explicitly declared x/z subdomain.

For row_kind = base_bin:
  aggregate_id must be none.
  bin_id must encode the base edge bin or x/z bin.
```

### 3.7 Hard-fail policy

Generation must stop if any condition holds:

| code | failure |
|---|---|
| PRS-G01 | any 500 nm NODI eta row is requested |
| PRS-G02 | `reference_too_weak` is converted to eligible |
| PRS-G03 | response bins are silently filled by nearest neighbor |
| PRS-G04 | empty bins are treated as pass/fail instead of missing/insufficient |
| PRS-G05 | `chi_selected` value is emitted |
| PRS-G06 | `annulus_fraction * chi_selected * eta` is emitted or implied |
| PRS-G07 | `q_ch * eta` or yield is emitted |
| PRS-G08 | Stage-1 detector panel is used as a candidate-family source |
| PRS-G09 | event budgets are mixed without explicit layer isolation |
| PRS-G10 | source manifest or config hash is absent |

Sparse-bin policy:

```text
If n_events_bin is below the predeclared minimum, emit
bin_status = insufficient_bin_events and keep eta_response_proxy blank.
Do not fill from neighboring bins.
```

### 3.8 Validation checklist

The response-surface validator must check:

```text
route scope equals the launch matrix
diameter scope equals the launch matrix
edge_norm bins cover [0, 1] without overlap
x/z bins cover [-1, 1] without overlap
special aggregate definitions match the selected-window contract
exactly three required special aggregate rows exist per route/diameter/family
sparse or empty bins carry bin_status and blank eta_response_proxy
500 nm absent from NODI response rows
reference_too_weak rows retain guardrail status
no q_ch, chi_selected, yield, SNR/LOD/FPR, or winner columns
all source config/manifests are sha-pinned
primary COMSOL-facing rows are post-seed aggregated, with seed manifest pinned
```

## 4. Artifact B: NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY

### 4.1 Purpose

`NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY` asks whether optical route
ordering and eligibility are stable under plausible fabricated-aperture shifts.

It does not claim:

```text
true W_eff
true non-rectangular optical solution
trapezoid full-wave solved
fabricated optical calibration
```

### 4.2 Input dependency

Preferred COMSOL input:

```text
COMSOL geometry descriptor table
```

Minimum descriptor fields:

```text
route_geometry_id_comsol
route_geometry_id_comsol_version
angle_convention
process_state
W_top_um
W_bottom_um
W_nominal_nm
width_group_um
sidewall_deg
depth_um
D_nm
bottom_cd_bias_nm
edge_lip_nm_per_side
residue_thickness_nm
roughness_rms_nm
scallop_amplitude_nm
rounded_corner_radius_nm
min_aperture_nm
D_inscribed_nm
geometry_descriptor_source
field_evidence_class
geometry_descriptor_claim_boundary
```

Each geometry field must carry its own evidence class:

```text
measured
simulated
nominal
surrogate
unavailable
```

Do not let a measured top CD make bottom width, residue, roughness, or rounded
corner radius appear measured.

### 4.3 Aperture surrogate modes

Allowed modes:

| mode | use |
|---|---|
| `nominal_width` | baseline |
| `COMSOL_effective_aperture_descriptor` | preferred if contract-defined |
| `min_aperture_conservative` | conservative sensitivity |
| `W_bottom_conservative` | lower-bound sensitivity only |
| `top_bottom_average_heuristic` | labeled heuristic only |

Forbidden:

```text
W_bottom as default true optical width
top/bottom average as physical optical solution
numeric W_eff without mode and claim boundary
```

### 4.4 Perturbation grid

General P1 perturbations:

```text
nominal
-25 nm
-50 nm
-75 nm
-100 nm
```

W500 finer near-threshold perturbations:

```text
-10 nm
-20 nm
-30 nm
-50 nm
-75 nm
-100 nm
```

W800 perturbations:

```text
-25 nm
-50 nm
-100 nm
-150 nm
```

### 4.5 Minimum schema

Required columns:

```text
artifact_id
surrogate_version
route_id_nodi
lambda_nm
W_nominal_nm
D_nm
NODI_view
weighting
denominator_basis
source_rank_artifact
source_rank_basis
source_rank_column
source_route_rank
source_eta_selected_proxy
source_eta_all_proxy
source_guardrail_status
aperture_surrogate_mode
W_eff_nm
delta_W_eff_nm
source_geometry_descriptor_id
source_geometry_descriptor_sha256
aperture_claim_boundary
not_true_nonrectangular_solver
not_measured_W_eff
rank_flip_flag
candidate_family_flip_flag
eta_selected_relative_change
eta_all_relative_change
guardrail_status_change_flag
W_eff_mode_sensitivity_class
P3_solver_trigger_flag
P3_solver_trigger_reason
claim_boundary
```

Required constants:

```text
not_true_nonrectangular_solver = true
not_measured_W_eff = true
claim_boundary = effective_aperture_surrogate_sensitivity_only
source_rank_basis = fullgrid_recommendation_eligible_rank_contract
```

Rank-source rule:

```text
source_rank_artifact, source_rank_basis, and source_rank_column must identify
the fullgrid recommendation-eligible rank contract used by the source NODI
artifact.
Stage-1 detector-identity panels are never allowed as candidate-family,
eligibility, or route-rank sources.
```

### 4.6 Sensitivity classes

Allowed `W_eff_mode_sensitivity_class`:

| class | meaning |
|---|---|
| `stable` | no material ranking/eta/guardrail change across planned shifts |
| `watch` | changes exist but do not change candidate-family interpretation |
| `decision_changing` | route ordering or candidate-family reading changes |
| `solver_required` | scalar surrogate no longer adequate |

### 4.7 P3 solver triggers

Any of the following triggers P3 consideration:

| trigger | threshold |
|---|---|
| candidate-family order flips | 404/W500 vs 660/W800 flips |
| W500 dependency | 404/W500 eligibility depends on <=25 nm aperture assumption |
| selected response movement | selected-window response changes by >10 percent relative |
| guardrail ambiguity | guardrail status changes or becomes ambiguous under mapping |
| report dependency | P1/P2 conclusion depends on W_eff mode choice |
| geometry complexity | measured geometry shows non-scalar rounded/lip/residue/roughness/CD bias |

P3 trigger does not authorize P3 execution. It only authorizes a separate
solver-contract discussion.

### 4.8 Hard-fail policy

Generation must stop if any condition holds:

| code | failure |
|---|---|
| EAS-G01 | mode missing for a W_eff value |
| EAS-G02 | W_bottom is treated as true optical width |
| EAS-G03 | nominal NODI ranks are overwritten |
| EAS-G04 | original guardrail is replaced rather than reported alongside projection |
| EAS-G05 | non-rectangular full-wave claim appears |
| EAS-G06 | measured-geometry status is inferred from surrogate fields |
| EAS-G07 | scalar joint score or winner is emitted |
| EAS-G08 | source geometry descriptor sha is missing |
| EAS-G09 | candidate-family, eligibility, or source rank comes from Stage-1 detector-identity output |

## 5. q_ch boundary for all P1/P2 NODI artifacts

COMSOL confirmed:

```text
q_ch remains descriptive-only in all P1/P2 NODI artifacts
```

Allowed q_ch context fields, if imported only as context:

```text
q_ch_status
q_ch_scope
q_ch_value
q_ch_units
group_share
bypass_fraction
flow_condition_id
pressure_drop_pa
viscosity_pa_s
temperature_C
contribution_context
```

Forbidden in all NODI artifacts:

```text
q_ch * eta
q_ch * chi_selected * eta
yield
throughput detection
EV detection probability
calibrated recovery
scalar joint score
winner
```

Artifact-level constants:

```text
q_ch_descriptive_only = true
no_q_ch_eta_product = true
no_yield_claim = true
no_throughput_detection_claim = true
detector_model_status = not_available
```

## 6. Recommended implementation sequence

### Phase 0 - freeze this design contract

Inputs:

```text
COMSOL-side confirmation for NODI next artifacts
existing NODI P0 handoff package
report 149
```

Output:

```text
reviewed design contract
```

No computation.

### Phase 1 - position-response launch review

Create a launch-review issue/report that binds:

```text
route matrix
diameter matrix
edge/xz binning
sampling mode
event budget per bin
minimum bin events
expected output rows
runtime estimate
source manifest plan
validation command plan
stop conditions
```

No runner execution until launch review passes.

### Phase 2 - aperture-surrogate launch review

Create a launch-review issue/report that binds:

```text
COMSOL geometry descriptor schema
surrogate mode set
delta-W grid
route matrix
weighting/denominator basis
rank/eta comparison rules
P3 trigger rules
validation command plan
stop conditions
```

No surrogate execution until launch review passes.

### Phase 3 - bounded sidecar execution, if authorized later

If and only if separately authorized, write outputs under a new sidecar path,
for example:

```text
exports/nodi_comsol_next_artifacts_v1/
```

Do not write to:

```text
results/
reports/current/
historical result directories
```

## 7. Questions to keep open for COMSOL

Before execution, ask COMSOL to pin:

1. Whether P1 distribution delivery will include both `edge_norm_1d` and
   `xz_norm_2d`, or whether `xz_norm_2d` arrives later.
2. Whether `flow_condition_id` is already stable enough for cross-artifact
   joining.
3. Whether 230-290 nm distribution rows will arrive as exact transported
   distributions or planning/sensitivity rows.
4. Whether any `COMSOL_effective_aperture_descriptor` exists, or whether P1
   should begin with `min_aperture_conservative` and explicit delta-W grids.
5. Whether geometry descriptor evidence classes are available per field or
   only per table.
6. What COMSOL will treat as the minimum useful event/bin confidence for
   consuming NODI response bins.

## 8. Independent-review checklist

The independent reviewer should verify:

```text
report 149 does not authorize computation
report 149 does not authorize q_ch * eta, yield, SNR/LOD/FPR, winner, true W_eff, or chi_selected
position-response schema is conditional optical response, not transported occupancy
500 nm remains absent/out_of_library for NODI eta
reference_too_weak guardrail remains immutable
aperture surrogate keeps original guardrail/rank immutable
P3 triggers are only triggers, not execution authorization
q_ch remains descriptive-only
Phase 1/2 require launch review before execution
```

## 9. Current decision

Proceed next to launch-review design for:

```text
NODI_POSITION_RESPONSE_SURFACE
NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY
```

Do not proceed to runner execution in this step.
