# Report 150 - NODI/COMSOL next-artifact launch review stop point

Date: 2026-06-17

Status:

```text
launch_review_stop_point_reached
no runner execution authorized
no runner design authorized
no NODI recomputation authorized
```

This report advances Report 149 from design contract to launch-review stop
point. It binds the route matrix, diameter matrix, binning, row-count plan,
event-budget plan, source-manifest plan, validator plan, and stop conditions for
the next NODI/COMSOL artifacts.

It does not execute any runner, generate any new simulation output, mutate any
historical CSV, regenerate `JOINT_ROUTE_CLASS`, or create a joint score.

## 1. Boundary

Forbidden in this launch review:

```text
new NODI recomputation
new COMSOL run
runner execution
JOINT_ROUTE_CLASS regeneration
q_ch * eta
q_ch * chi_selected * eta
yield
throughput detection
EV detection probability
calibrated SNR / LOD / FPR
scalar joint score
winner
numeric chi_selected
numeric true W_eff
non-rectangular full-wave solver claim
```

Allowed in this launch review:

```text
schema binding
route/diameter/bin matrix binding
bounded event-budget planning
runtime estimate from historical run-rate only
validator specification
runner-design entry-point identification
execution stop-condition declaration
COMSOL follow-up prompt
```

NODI role remains:

```text
conditional optical response provider, not joint scorer
```

## 2. Refreshed feasibility check

The existing V1 handoff under `exports/nodi_comsol_handoff_v1/` remains a
connector-grade P0 package for `JOINT_ROUTE_CLASS` V1. It is not a position-bin
response package.

Current artifact facts:

| layer | current fact | launch-review consequence |
|---|---|---|
| `NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv` | route x view x weighting rank/proxy table | usable as rank provenance for aperture-surrogate comparisons |
| `NODI_REFERENCE_GUARDRAIL_TABLE.csv` | route-level `reference_operating_band` guardrail | must be joined before any eta/rank consumption |
| `NODI_EVIDENCE_CONNECTOR_rawrow_proxy.csv` | route x view x particle x seed summary | useful for baseline route/diameter availability, not enough for response bins |
| diagnostic rows | include selected-annulus aggregate diagnostics | not a general `edge_norm` or `x/z` response surface |
| `parameter_sweep.py` event summaries | event `position_diag` has `initial_position_x_norm` and `initial_position_z_norm` | code has a plausible insertion point for a new sidecar bin accumulator |

The existing event summary already computes selected-annulus fields from
event-level initial position:

```text
edge_norm = max(abs(initial_position_x_norm), abs(initial_position_z_norm))
selected_annulus = 0.5 <= edge_norm <= 0.8
```

But the current exported connector only preserves the selected-annulus aggregate
and route/particle summaries. Therefore `NODI_POSITION_RESPONSE_SURFACE` cannot
be produced by reshaping the current P0 handoff. It needs a new sidecar
event-bin summary/export path.

## 3. Launch review A: NODI_POSITION_RESPONSE_SURFACE

### 3.1 Launch status

```text
ready_for_bounded_sidecar_runner_design
runner_design_not_authorized_by_this_report
not_ready_for_runner_execution_without_separate_authorization
```

The launch matrix is now bounded enough to prepare a separate runner-design
decision. This report does not authorize runner-design implementation and does
not authorize runner execution.

### 3.2 Route matrix

P1 core routes:

```text
404/W500/D900
404/W500/D1200
660/W800/D900
660/W800/D1200
```

P1 diagnostic/context route:

```text
404/W600/D900
```

P2 diagnostic trap, excluded from the P1 COMSOL-facing table unless a separate
diagnostic run is authorized:

```text
660/W500/D1500
```

Trap-route rule:

```text
reference_too_weak guardrail remains binding
hydraulic transport cannot rescue it
output role = high_proxy_guarded_trap_example_only
```

### 3.3 View and particle scope

COMSOL-facing rows carry both NODI normalization views:

```text
fixed_660_gold
per_wavelength_gold
```

The physical event stream must remain shared across views. Event budgets are not
doubled by emitting two NODI-view rows.

Particle scope:

```text
particle_kind = exosome_synthetic
gold_anchor rows are excluded from COMSOL-facing response-surface rows
```

Gold rows may only appear in a diagnostic provenance sidecar if the runner needs
to prove normalization lineage.

### 3.4 Diameter matrix

P1 minimum matrix:

```text
40, 100, 150, 220, 250, 270, 290, 300 nm
```

P1 preferred matrix:

```text
40, 60, 100, 150, 220, 230, 240, 250, 260, 270, 280, 290, 300 nm
```

Launch recommendation:

```text
use P1 preferred matrix for the first COMSOL-facing response-surface artifact
```

Reason:

```text
40/60/100/150/220/300 preserves broad optical-size response shape
230-290 aligns the finite-size transport/manufacturing bridge
250/270/290 covers the P1 minimum manufacturing-bridge add-on
```

500 nm policy:

```text
500 nm absent from NODI eta rows
500 nm eta_response_proxy blank if represented in a gap/coverage table
500 nm joint role remains RC13 out_of_particle_library_scope
```

### 3.5 Binning matrix

P1 response families:

| distribution_type | base bins | special aggregate rows | rows per view/route/diameter |
|---|---:|---:|---:|
| `edge_norm_1d` | 20 | 3 | 23 |
| `xz_norm_2d` | 441 | 3 | 444 |
| total | 461 | 6 | 467 |

Launch assumption A1:

```text
The current row-count contract assumes the three special aggregate rows are
emitted for both edge_norm_1d and xz_norm_2d.
```

This assumption is not a runner authorization. If COMSOL confirms that special
aggregate rows should be edge-only, this report's row-count plan and validator
plan must be revised before runner design or execution.

`edge_norm_1d` base-bin convention:

```text
20 bins over [0.0, 1.0]
bin width = 0.05
base bins are half-open [min, max), except the final bin includes 1.0
```

Special aggregates:

| aggregate_id | definition |
|---|---|
| `near_center_0p0_0p5` | `0.0 <= edge_norm < 0.5` |
| `selected_annulus_0p5_0p8` | `0.5 <= edge_norm <= 0.8` |
| `near_wall_0p8_1p0` | `0.8 < edge_norm <= 1.0` |

`xz_norm_2d` base-bin convention:

```text
21 x 21 grid over [-1, 1] x [-1, 1]
x bin i bounds = [-1 + i*(2/21), -1 + (i+1)*(2/21)]
z bin j bounds = [-1 + j*(2/21), -1 + (j+1)*(2/21)]
last x/z bin includes +1.0
bin_id = xNN_zMM for NN,MM in 00..20
```

The three special aggregate rows are also emitted for `xz_norm_2d`; their x/z
bounds are blank unless a later COMSOL contract requests aggregate rows inside a
declared x/z subdomain.

### 3.6 Row-count plan

Primary P1 preferred COMSOL-facing table:

```text
routes = 5
diameters = 13
NODI_views = 2
rows_per_route_diameter_view = 467
expected_rows = 60710
```

P1 minimum fallback:

```text
routes = 5
diameters = 8
NODI_views = 2
rows_per_route_diameter_view = 467
expected_rows = 37360
```

Optional P2 diagnostic trap table:

```text
routes = 1
diameters = 13
NODI_views = 2
rows_per_route_diameter_view = 467
expected_rows = 12142
```

These are table-row counts, not event counts. Special aggregate rows are derived
from base-bin events and do not add event samples.

### 3.7 Event-budget plan

The first COMSOL-facing P1 response-surface run should use:

```text
seed_set = 11,22,33
seed_scope = aggregate_across_seeds
events_per_base_bin_per_seed = 100
target_post_seed_events_per_base_bin = 300
minimum_post_seed_events_per_base_bin = 100
```

Sparse-bin policy:

```text
if n_events_bin < 100 after seed aggregation:
  bin_status = insufficient_bin_events
  eta_response_proxy = blank
  eta_response_wilson_lb = blank
```

Estimated event samples for P1 preferred:

```text
routes * diameters * base_bins * seeds * events_per_base_bin_per_seed
= 5 * 13 * 461 * 3 * 100
= 8989500 event samples
```

Historical run-rate context, not a guarantee:

```text
recent fullgrid observed particle_events_per_second roughly 2300-5100 in 16-worker runs
older one-seed observed rate roughly 8600 particle_events_per_second
```

Back-of-envelope P1 preferred runtime at historical rates:

```text
at 2300 events/s: about 1.09 h
at 5100 events/s: about 0.49 h
at 8600 events/s: about 0.29 h
```

This estimate is advisory only because a bin-conditioned runner will have
different overhead from the fullgrid runner. A smoke benchmark is mandatory
before any full P1 response-surface run.

### 3.8 Pre-execution smoke benchmark

Before full P1 execution, require a separately authorized smoke benchmark:

```text
routes = 404/W500/D900, 660/W800/D900
diameters = 100, 220, 300 nm
distribution_type = edge_norm_1d only
seed_set = 11
events_per_base_bin_per_seed = 50
expected_event_samples = 6000
COMSOL-facing claim = none
```

The smoke benchmark must prove:

```text
runner can force/bin-condition initial position sampling
edge_norm bins match contract
empty/sparse bins remain blank
per-seed diagnostic sidecar is separate from COMSOL-facing aggregate table
manifest/config hashes are emitted
no q_ch, yield, chi_selected, winner, calibrated SNR/LOD/FPR columns appear
```

If the smoke benchmark cannot prove these, full P1 execution remains blocked.

### 3.9 Runner-design entry point

The runner should be a new sidecar path, not a mutation of the fullgrid runner's
historical outputs.

Recommended implementation shape:

```text
tools/build_nodi_position_response_surface.py
tools/validate_nodi_position_response_surface.py
exports/nodi_comsol_next_artifacts_v1/
```

Implementation principle:

```text
reuse existing simulation primitives and event summary logic
add a bin-conditioned sampling/export layer
do not rewrite seed_*_raw_rows.csv
do not rewrite existing diagnostic rows
```

The likely code-level insertion area is the existing event summary path that
already records:

```text
initial_position_x_norm
initial_position_z_norm
event_max_margin_z
final_detected_flags
```

The new sidecar accumulator must generalize the current selected-annulus summary
to the bound `edge_norm_1d` and `xz_norm_2d` bins.

### 3.10 Source-manifest plan

Every future response-surface package must include:

```text
NODI_POSITION_RESPONSE_SURFACE.csv
NODI_POSITION_RESPONSE_SURFACE_VALIDATION_REPORT.md
NODI_POSITION_RESPONSE_SURFACE_SOURCE_MANIFEST.json
NODI_POSITION_RESPONSE_SURFACE_SCHEMA.md
NODI_POSITION_RESPONSE_SURFACE_SEED_MANIFEST.csv
NODI_POSITION_RESPONSE_SURFACE_HASHES.sha256
```

The source manifest must pin:

```text
report_149_sha256
report_150_sha256
runner_script_sha256
validator_script_sha256
simulation_config_sha256
seed_set
route_matrix
diameter_matrix
bin_contract
event_budget_contract
source_git_commit_or_dirty_status
input COMSOL contract hash if any
```

### 3.11 Validator plan

`validate_nodi_position_response_surface.py` must hard-fail on:

| code | failure |
|---|---|
| PRS-V01 | row count differs from launch matrix |
| PRS-V02 | route matrix differs from launch matrix |
| PRS-V03 | diameter matrix differs from launch matrix |
| PRS-V04 | any 500 nm eta row appears |
| PRS-V05 | edge bins do not cover [0, 1] exactly |
| PRS-V06 | x/z bins do not cover [-1, 1] exactly |
| PRS-V07 | required special aggregates missing or misbounded |
| PRS-V08 | `row_kind`, `aggregate_id`, or `bin_status` invalid |
| PRS-V09 | sparse bins have nonblank eta fields |
| PRS-V10 | `reference_too_weak` converted to eligible |
| PRS-V11 | q_ch, yield, chi_selected, winner, SNR/LOD/FPR columns appear |
| PRS-V12 | source manifest/config hash absent |
| PRS-V13 | primary table contains per-seed rows instead of post-seed aggregate rows |
| PRS-V14 | NODI views are pooled or treated as independent physical campaigns |
| PRS-V15 | Stage-1 detector identity appears as a candidate-family source |

### 3.12 Position-response execution stop point

Execution is blocked until a future instruction explicitly authorizes:

```text
implementation of build_nodi_position_response_surface.py
implementation of validate_nodi_position_response_surface.py
smoke benchmark execution
review of smoke benchmark output
full P1 response-surface execution
```

Current stop-point verdict:

```text
POSITION_RESPONSE_LAUNCH_REVIEW = PASS_FOR_SEPARATE_RUNNER_DESIGN_DECISION
POSITION_RESPONSE_RUNNER_DESIGN = BLOCKED_PENDING_SEPARATE_AUTHORIZATION
POSITION_RESPONSE_RUNNER_EXECUTION = BLOCKED_PENDING_SEPARATE_AUTHORIZATION
```

## 4. Launch review B: NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY

### 4.1 Launch status

```text
dry_contract_bound
execution_blocked_pending_COMSOL_geometry_descriptor_and_width-perturbation_runner_design
```

The aperture-surrogate contract is bound enough to specify schema, rank-source
provenance, delta-W grid, and validator rules. It is not execution-ready because
NODI does not yet have a COMSOL geometry descriptor or an authorized W_eff
perturbation runner path.

### 4.2 Required COMSOL input

The required input is a geometry descriptor table with this grain:

```text
route_geometry_id_comsol x process_state
```

or, if aperture metrics are diameter-specific:

```text
route_geometry_id_comsol x process_state x diameter_nm
```

Minimum required columns:

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
geometry_descriptor_sha256
```

Each geometry field needs an evidence class:

```text
measured
simulated
nominal
surrogate
unavailable
```

No field may inherit measured status from another field.

### 4.3 NODI source-rank provenance

Allowed rank source:

```text
exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv
source_rank_basis = fullgrid_recommendation_eligible_rank_contract
source_rank_column = recommendation_eligible_rank
```

Required guardrail join:

```text
exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv
join keys = lambda_nm, W_nominal_nm, D_nm
```

Forbidden rank source:

```text
stage1_detector_identity
stage1 route flips
detector-resolved gate counts
any winner-like downstream narrative
```

Stage-1 remains uncertainty/context only. It cannot create, select, or rescue a
candidate family.

### 4.4 Surrogate modes and delta-W grid

Allowed modes:

```text
nominal_width
COMSOL_effective_aperture_descriptor
min_aperture_conservative
W_bottom_conservative
top_bottom_average_heuristic
```

Forbidden:

```text
W_bottom as default true optical width
top/bottom average as physical optical solution
numeric W_eff without aperture_surrogate_mode and claim boundary
```

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

### 4.5 Aperture-surrogate validator plan

`validate_nodi_effective_aperture_surrogate_sensitivity.py` must hard-fail on:

| code | failure |
|---|---|
| EAS-V01 | missing `aperture_surrogate_mode` for any W_eff value |
| EAS-V02 | W_bottom treated as true optical width |
| EAS-V03 | source rank artifact/basis/column absent |
| EAS-V04 | source rank does not come from fullgrid recommendation-eligible rank |
| EAS-V05 | Stage-1 detector identity used for candidate-family/rank/eligibility |
| EAS-V06 | original guardrail overwritten rather than carried alongside projection |
| EAS-V07 | non-rectangular full-wave claim appears |
| EAS-V08 | measured geometry inferred from surrogate fields |
| EAS-V09 | scalar joint score, winner, yield, q_ch*eta, or throughput detection appears |
| EAS-V10 | geometry descriptor sha missing |
| EAS-V11 | P3 trigger interpreted as P3 execution authorization |

### 4.6 P3 trigger handling

The following trigger P3 consideration only:

```text
candidate-family order flips between 404/W500 and 660/W800
404/W500 eligibility depends on <=25 nm aperture assumption
selected-window response changes by >10 percent relative
guardrail status changes or becomes ambiguous
P1/P2 conclusion depends on W_eff mode
measured geometry shows strong non-scalar rounded/lip/residue/roughness/CD bias
```

P3 trigger output must be:

```text
P3_solver_trigger_flag
P3_solver_trigger_reason
solver_contract_discussion_required
```

It must not launch a non-rectangular optical solver.

### 4.7 Aperture-surrogate execution stop point

Execution is blocked until:

```text
COMSOL provides geometry descriptor table or confirms it is unavailable
NODI position-response sidecar runner design is authorized
W_eff perturbation runner behavior is separately reviewed
validator implementation is authorized
smoke benchmark strategy is reviewed
```

Current stop-point verdict:

```text
APERTURE_SURROGATE_LAUNCH_REVIEW = PASS_FOR_DRY_CONTRACT
APERTURE_SURROGATE_EXECUTION = BLOCKED_PENDING_COMSOL_DESCRIPTOR_AND_SEPARATE_AUTHORIZATION
```

## 5. COMSOL prompt for the next discussion

Copyable prompt:

```text
We have advanced the NODI side to launch-review stop point for:
1. NODI_POSITION_RESPONSE_SURFACE
2. NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY

NODI has not run any new simulation, has not generated q_ch*eta/yield/winner,
and has not regenerated JOINT_ROUTE_CLASS. We only bound the next sidecar
contracts.

Please confirm or correct the following before NODI authorizes runner work:

A. Position response surface
- P1 preferred NODI route matrix:
  404/W500/D900, 404/W500/D1200, 660/W800/D900, 660/W800/D1200,
  plus diagnostic/context 404/W600/D900.
- P2 diagnostic trap remains 660/W500/D1500 only; reference_too_weak cannot be
  rescued by transport.
- P1 preferred diameter matrix:
  40, 60, 100, 150, 220, 230, 240, 250, 260, 270, 280, 290, 300 nm.
- 500 nm stays NODI out_of_particle_library_scope / RC13; no eta.
- edge_norm_1d uses 20 bins over [0,1], width 0.05.
- xz_norm_2d uses 21 x 21 bins over [-1,1]^2.
- special aggregates:
  near_center_0p0_0p5, selected_annulus_0p5_0p8, near_wall_0p8_1p0.
- NODI primary table will be post-seed aggregated at route/lambda/W/D/diameter/bin,
  with per-seed rows only in a diagnostic sidecar.
- Proposed first P1 event target:
  3 seeds, 100 events/base-bin/seed, target 300 post-seed events per bin,
  sparse if post-seed n_events_bin < 100.

Questions:
1. Is 100 events/base-bin/seed acceptable for P1 planning, or should COMSOL
   require a higher/lower minimum before it consumes NODI bins?
2. Please confirm launch assumption A1: special aggregate rows are emitted for
   both edge_norm_1d and xz_norm_2d. If COMSOL prefers edge-only aggregates,
   NODI will revise row counts and validator rules before any runner design.
3. Will COMSOL consume both NODI views, or should NODI restrict the first response
   surface to one view?
4. Is flow_condition_id stable enough now for future NODI/COMSOL joins?

B. Effective aperture surrogate
- NODI will only use fullgrid recommendation-eligible rank as source rank.
- Stage-1 detector identity remains forbidden as candidate-family/rank/eligibility source.
- W_bottom is not true W_eff and not a default optical width.
- P3 triggers are only solver-contract triggers, not solver execution authorization.

Questions:
5. Can COMSOL provide a geometry descriptor table at
   route_geometry_id_comsol x process_state grain, or diameter-specific grain?
6. If yes, please provide/pin:
   route_geometry_id_comsol, version, process_state, W_top, W_bottom,
   W_nominal, width_group, sidewall, depth, bottom_cd_bias, edge_lip,
   residue, roughness, scallop, rounded_corner, min_aperture, D_inscribed,
   geometry_descriptor_source, per-field evidence_class, claim_boundary,
   descriptor sha.
7. If no descriptor is available, should NODI begin only with nominal_width and
   min_aperture_conservative dry sensitivity design, or wait?
```

## 6. Final stop point

The launch review has advanced as far as it can without starting new NODI
execution.

Stop-point summary:

| artifact | launch-review status | execution status | reason |
|---|---|---|---|
| `NODI_POSITION_RESPONSE_SURFACE` | `PASS_FOR_SEPARATE_RUNNER_DESIGN_DECISION` | `BLOCKED_PENDING_SEPARATE_AUTHORIZATION` | needs separate authorization for runner design, sidecar bin accumulator/export path, and smoke benchmark |
| `NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY` | `PASS_FOR_DRY_CONTRACT` | `BLOCKED_PENDING_COMSOL_DESCRIPTOR_AND_SEPARATE_AUTHORIZATION` | needs COMSOL geometry descriptor and W_eff perturbation runner design |

No additional progress should occur in this thread by silently running a
simulation. The next legitimate action is independent review of this stop-point
report.
