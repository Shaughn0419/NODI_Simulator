# Report 154 - NODI to COMSOL launch-review contract handoff

Date: 2026-06-17

Status:

```text
handoff_contract_for_comsol_review
position_response_contract_ready_for_comsol_launch_review
aperture_surrogate_contract_ready_for_comsol_launch_review
no runner implementation authorized
no runner execution authorized
no NODI recomputation authorized
no COMSOL run requested
```

This is the NODI-side launch-review contract to send back to COMSOL for the
next two NODI artifacts:

```text
NODI_POSITION_RESPONSE_SURFACE
NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY
```

It consolidates Reports 149-153 plus the locally verified COMSOL geometry
descriptor sidecars. It is a contract/handoff artifact only. It does not
authorize implementation, execution, recomputation, COMSOL reruns, or any joint
score.

## 1. Source evidence pinned by NODI

NODI report chain:

| source | SHA256 | role |
|---|---|---|
| `reports/149_NODI_COMSOL_position_response_aperture_surrogate_design_plan_20260617.md` | `e895b846d9c6d1b2e8ca62624d602bebf75713fa6c29d3cc73b4f6c10b375f18` | initial NODI-side design contract |
| `reports/150_NODI_COMSOL_next_artifacts_launch_review_stop_point_20260617.md` | `9c1ebf33fd2f1f2e5191ca1a57d6de0a2b51cced6512855cf34742da7c5202e6` | bounded launch-review stop point |
| `reports/151_NODI_COMSOL_feedback_integration_runner_contract_overlay_20260617.md` | `15806b799b7b17a2cf4b4750786582f46895ed941e669d0beb69887705a5846e` | COMSOL feedback integration and schema overlay |
| `reports/152_NODI_COMSOL_geometry_descriptor_availability_overlay_20260617.md` | `4b15d932b302fe2feeef66f7332a06d99492a941d03bc7417703c1007ceb8116` | geometry descriptor availability overlay |
| `reports/153_NODI_COMSOL_geometry_descriptor_local_verification_20260617.md` | `e044bfac1a0a6c841ae335666ed7d3489c6008f8c46ad8bca57c3e18bee0e1e0` | local descriptor hash/structure verification |

COMSOL descriptor sidecars locally verified in NODI `tmp/`:

| local file | rows | SHA256 | local NODI verdict |
|---|---:|---|---|
| `tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv` | 2040 | `1198055754c41710a4821894ecb749660e5ef4a14b2e0fc647789ba31a0b38a2` | PASS |
| `tmp/COMSOL_GEOMETRY_DESCRIPTOR_FIELD_EVIDENCE_V1.csv` | 22 | `d667112b6591b72f709bc8aed77711351f7fbbe5c874206fe7544c3a0f3aca91` | PASS |
| `tmp/COMSOL_GEOMETRY_DESCRIPTOR_VALIDATION_REPORT_20260617.md` | not applicable | `13059e6694cda2380d21f0ac6ead3ae8e425b01ec8d79c63ad4d6207d2bde14c` | PASS |

The `tmp/` location is a local verification staging location, not a durable
provenance package. A durable handoff package path is still an open packaging
decision.

## 2. Global claim boundary

Forbidden by this handoff:

```text
new NODI recomputation
new COMSOL run
runner implementation
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
measured geometry claim
fabrication release
non-rectangular full-wave solver claim
calibrated optical evidence claim
P3 solver conclusion
```

Allowed by this handoff:

```text
COMSOL launch-review of the NODI contract
schema and validator review
route/diameter/bin/sample-budget review
descriptor-backed dry sensitivity design review
provenance and durable-package path review
PASS/FAIL/correction feedback from COMSOL
```

NODI role remains:

```text
conditional optical response provider, not joint scorer
```

COMSOL response requested:

```text
review only; do not start COMSOL jobs or regenerate COMSOL artifacts unless
separately requested by the user
```

## 3. Contract A: NODI_POSITION_RESPONSE_SURFACE

### 3.1 Artifact purpose

`NODI_POSITION_RESPONSE_SURFACE` is a conditional optical-response surface by
initial-position bin. It is designed so a future COMSOL transported-position
distribution can weight NODI optical response without double-counting NODI's
synthetic selected-annulus fraction.

It is not:

```text
transported occupancy
q_ch-weighted detection
chi_selected
yield
EV passability
joint scalar score
```

### 3.2 Launch status

```text
POSITION_RESPONSE_COMSOL_FEEDBACK = PASS
POSITION_RESPONSE_SCHEMA_OVERLAY = PASS
POSITION_RESPONSE_RUNNER_CONTRACT_DESIGN = PASS_FOR_CONTRACT_ONLY
POSITION_RESPONSE_RUNNER_IMPLEMENTATION = BLOCKED_PENDING_USER_AUTHORIZATION
POSITION_RESPONSE_RUNNER_EXECUTION = BLOCKED_PENDING_SMOKE_AUTHORIZATION
```

This means the contract is ready for COMSOL review. It does not mean the NODI
runner has been implemented or executed.

### 3.3 Route matrix

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

P2 diagnostic trap:

```text
660/W500/D1500
```

Trap route rule:

```text
reference_too_weak remains non-rescuable by hydraulic transport
output role = diagnostic trap only
must not become candidate-family evidence
```

### 3.4 Diameter matrix

P1 preferred diameter matrix:

```text
40, 60, 100, 150, 220, 230, 240, 250, 260, 270, 280, 290, 300 nm
```

500 nm policy:

```text
NODI out_of_particle_library_scope / RC13
eta_response_proxy blank
no interpolation
no zero or low optical proxy
no decision-use row
```

### 3.5 NODI views

Both views remain in the full P1 contract:

```text
fixed_660_gold
per_wavelength_gold
```

Rules:

```text
NODI_view column required
no pooling across views
no consensus averaging across views
do not treat the two views as independent physical campaigns
the physical event stream must remain shared across views
```

A reduced pilot is possible only if separately authorized and explicitly
labeled as reduced. The full P1 launch-review contract remains both views.

### 3.6 Binning and aggregate contract

Primary output families:

| distribution_type | base bins | special aggregate rows | row role |
|---|---:|---:|---|
| `edge_norm_1d` | 20 bins over `[0, 1]`, width `0.05` | 3 | primary if sample-adequate |
| `xz_norm_2d` | `21 x 21` bins over `[-1, 1]^2` | 3 | diagnostic/context unless explicitly promoted |

Special aggregates emitted for both distributions:

| aggregate_id | definition |
|---|---|
| `near_center_0p0_0p5` | `0.0 <= edge_norm < 0.5` |
| `selected_annulus_0p5_0p8` | `0.5 <= edge_norm <= 0.8` |
| `near_wall_0p8_1p0` | `0.8 < edge_norm <= 1.0` |

Aggregate-source field:

```text
aggregate_source_type = edge_norm_primary | xz_norm_diagnostic | xz_norm_primary_if_adequate
```

Promotion rule:

```text
xz_norm_2d rows may be promoted to xz_norm_primary_if_adequate only with
validator-visible adequate sample support and explicit promotion rationale.
```

### 3.7 Row-count contract

Rows per route/diameter/view:

```text
edge_norm_1d rows = 23
xz_norm_2d rows = 444
total rows_per_route_diameter_view = 467
```

P1 preferred COMSOL-facing table:

```text
routes = 5
diameters = 13
NODI_views = 2
expected_rows = 60710
```

P2 diagnostic trap:

```text
routes = 1
diameters = 13
NODI_views = 2
expected_rows = 12142
diagnostic only
```

### 3.8 Event budget and sample-status contract

Accepted seed/event target:

```text
seed_set = 11,22,33
events_per_base_bin_per_seed = 100
target_post_seed_events_per_bin = 300
sparse threshold = post-seed n_events_bin < 100
```

Primary table grain:

```text
post-seed aggregate at route/lambda/W/D/diameter/NODI_view/bin
```

Diagnostic sidecar:

```text
per-seed rows only
```

Required sample fields:

```text
n_seeds
n_events_total
n_events_bin
n_events_bin_per_seed_min
sparse_bin_flag
sparse_bin_policy
bin_sample_status
decision_use_allowed
```

Canonical sample-status rules:

```text
bin_sample_status = adequate | sparse | empty
empty = n_events_bin == 0
sparse = 0 < n_events_bin < 100
adequate = n_events_bin >= 100
sparse_bin_flag = true when n_events_bin < 100
```

Decision-use rule:

```text
decision_use_allowed = true only when bin_sample_status is adequate, or when a
special aggregate is explicitly allowed as aggregate-level evidence.
sparse individual bins are visualization/context only.
empty bins are never decision-use rows.
```

`bin_sample_status` is a sample-adequacy field only. `guardrail_status` is the
separate NODI eligibility/guardrail state.

Legacy compatibility rule:

```text
legacy bin_status may be retained only as a compatibility field
bin_status must not override bin_sample_status, guardrail_status, or decision_use_allowed
guardrail_blocked is not a sample-status value
```

### 3.9 Flow-condition provenance contract

Flow fields are conditional but required when COMSOL flow context is attached:

```text
flow_condition_id
flow_condition_version
flow_condition_source_sha
flow_condition_scope
flow_condition_claim_boundary
```

Allowed `flow_condition_scope` values:

```text
nominal_smooth_fullchip
split_midplane_qch
local_direct_cell
future_transport_distribution
```

Current W800 q_ch context:

```text
flow_condition_id = p1b_w800_qch_splitmid_20260617
flow_condition_scope = split_midplane_qch
source evidence = P1B_W800_QCH_FIRST_LAUNCH_RESULTS_20260617.csv
```

Boundary:

```text
flow-condition fields are context/provenance only
q_ch remains descriptive-only
no q_ch * eta
no q_ch * chi_selected * eta
no yield
no throughput detection
```

### 3.10 Position-response validator additions

Required validator failures from the Report 151 overlay:

| code | failure |
|---|---|
| PRS-V16 | `bin_sample_status` missing or inconsistent with `n_events_bin` |
| PRS-V17 | `sparse_bin_flag` missing or inconsistent with threshold |
| PRS-V18 | sparse/empty individual bins have `decision_use_allowed=true` |
| PRS-V19 | `aggregate_source_type` missing or invalid |
| PRS-V20 | xz rows are promoted to decision use without adequate support and explicit reason |
| PRS-V21 | flow-condition fields are partially present or unversioned |
| PRS-V22 | W800 q_ch context uses old p6 anchor instead of split-midplane source |
| PRS-V23 | q_ch context is multiplied into eta/yield/throughput |
| PRS-V24 | legacy `bin_status` conflicts with `bin_sample_status`, `guardrail_status`, or `decision_use_allowed` |
| PRS-V25 | `guardrail_blocked` is encoded as a sample-status value instead of guardrail state |

## 4. Contract B: NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY

### 4.1 Artifact purpose

`NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY` is a dry sensitivity artifact.
It tests how NODI route/rank interpretation would move under explicit aperture
surrogate modes.

It is not:

```text
measured geometry
true optical W_eff
non-rectangular optical solver output
fabrication release
calibrated optical evidence
P3 solver conclusion
```

### 4.2 Launch status

```text
APERTURE_SURROGATE_LOCAL_DESCRIPTOR_VERIFICATION = PASS
APERTURE_SURROGATE_DESCRIPTOR_INPUT_CONTRACT = PASS_FOR_DRY_CONTRACT_DESIGN
APERTURE_SURROGATE_DESCRIPTOR_BACKED_MODE_DESIGN = PASS_FOR_CONTRACT_ONLY
APERTURE_SURROGATE_RUNNER_IMPLEMENTATION = BLOCKED_PENDING_USER_AUTHORIZATION
APERTURE_SURROGATE_RUNNER_EXECUTION = BLOCKED_PENDING_USER_AUTHORIZATION
```

This means the COMSOL descriptor sidecar is locally verified enough for NODI
dry-contract design. It does not mean the NODI aperture-surrogate runner has
been implemented or executed.

### 4.3 Rank source and guardrail contract

Allowed rank source:

```text
fullgrid recommendation-eligible rank only
```

Forbidden as candidate/rank/eligibility source:

```text
Stage-1 detector identity
reference_too_weak guarded trap routes
non-recommendation-eligible rows
```

The artifact must preserve guardrail state and must not let aperture surrogate
fields rescue a guarded route into candidate-family evidence.

### 4.4 Descriptor input contract

Descriptor grain:

```text
route_geometry_id_comsol x process_state
```

Locally verified descriptor facts:

```text
descriptor_rows = 2040
unique(route_geometry_id_comsol, process_state) = 2040
duplicate_grain = 0
process_states = nominal_smooth_geometry only
claim_boundary = nominal_surrogate_geometry_descriptor_not_measured_not_optical_solver
```

Geometry rules verified by NODI:

```text
W_top_um == width_group_um
W_bottom_um == bottom_width_nm / 1000
min_aperture_nm == min(bottom_width_nm, D_inscribed_nm)
```

All three rules had zero mismatches in local verification.

Negative aperture handling:

```text
negative_min_aperture_rows = 141
negative values are preserved, not clipped
negative min_aperture_nm is geometry-surrogate evidence only
```

Unavailable V1 fields are blank, not zero:

```text
bottom_cd_bias_nm
edge_lip_nm_per_side
residue_thickness_nm
roughness_rms_nm
scallop_amplitude_nm
rounded_corner_radius_nm
```

### 4.5 Allowed dry sensitivity modes

Allowed modes:

```text
nominal_width
W_bottom_conservative
min_aperture_conservative
top_bottom_average_heuristic
COMSOL_descriptor_if_available
```

Mode boundary:

```text
surrogate sensitivity only
not measured geometry
not true optical W_eff
not calibrated optical evidence
not P3 solver output
```

### 4.6 P3 boundary

P3 triggers may be emitted only as solver-contract triggers:

```text
P3_needed_due_to_nonrectangular_or_aperture_sensitivity = true | false
P3_trigger_reason = bounded text enum
```

They are not solver execution authorization. The descriptor does not authorize a
non-rectangular optical solver.

## 5. COMSOL review questions

Please reply with `PASS`, `PASS_WITH_CORRECTION`, or `BLOCKED` for each item.

1. Is the `NODI_POSITION_RESPONSE_SURFACE` launch-review contract above
   sufficient for COMSOL-side planning and future join design?

2. Are the route, diameter, view, binning, row-count, sample-status, and
   flow-condition fields exactly sufficient, or does COMSOL need additional
   columns before NODI proceeds to code-level runner/validator design?

3. Please confirm that `edge_norm_1d` remains the primary join artifact and
   that `xz_norm_2d` remains diagnostic/context unless sample-adequate and
   explicitly promoted through `aggregate_source_type`.

4. Please confirm that the W800 q_ch context should be represented only through
   versioned `flow_condition_*` fields and must remain descriptive-only with no
   `q_ch * eta`, no yield, and no throughput scalar.

5. Please provide or confirm the exact SHA256 and durable path for
   `P1B_W800_QCH_FIRST_LAUNCH_RESULTS_20260617.csv`, if COMSOL expects NODI to
   pin it in `flow_condition_source_sha`.

6. Is the locally verified `COMSOL_GEOMETRY_DESCRIPTOR_V1` sidecar sufficient
   for NODI aperture-surrogate dry contract design, given the claim boundary
   `nominal_surrogate_geometry_descriptor_not_measured_not_optical_solver`?

7. Should the descriptor sidecar be mirrored into a durable NODI package such as
   `exports/nodi_comsol_next_artifacts_v1/inputs/`, or should the durable source
   of truth remain a COMSOL-side `roadmap/` path with NODI recording only hashes?

8. Does COMSOL require any additional descriptor fields before NODI implements
   the dry aperture surrogate validator, assuming NODI will not claim measured
   geometry, true W_eff, optical solver output, fabrication release, or P3
   conclusions?

9. Please confirm that 500 nm remains RC13/out-of-library for NODI eta with no
   interpolation and no zero proxy.

10. Please confirm that this handoff is review-only and does not request COMSOL
    reruns, COMSOL artifact regeneration, NODI runner execution, or
    `JOINT_ROUTE_CLASS` regeneration.

## 6. Copyable prompt to send to COMSOL

```text
Scope: NODI launch-review contract handoff for position-response and aperture
surrogate artifacts. This is review-only. Do not start COMSOL jobs, regenerate
COMSOL artifacts, run NODI, regenerate JOINT_ROUTE_CLASS, or treat this as a
request for q_ch*eta, yield, winner, true W_eff, measured geometry, optical
solver output, fabrication release, or P3 solver conclusions.

NODI has consolidated Reports 149-153 into the following launch-review contract:

1. NODI_POSITION_RESPONSE_SURFACE
- Status:
  POSITION_RESPONSE_COMSOL_FEEDBACK = PASS
  POSITION_RESPONSE_SCHEMA_OVERLAY = PASS
  POSITION_RESPONSE_RUNNER_CONTRACT_DESIGN = PASS_FOR_CONTRACT_ONLY
  POSITION_RESPONSE_RUNNER_IMPLEMENTATION = BLOCKED_PENDING_USER_AUTHORIZATION
  POSITION_RESPONSE_RUNNER_EXECUTION = BLOCKED_PENDING_SMOKE_AUTHORIZATION
- P1 core routes:
  404/W500/D900
  404/W500/D1200
  660/W800/D900
  660/W800/D1200
- P1 diagnostic/context route:
  404/W600/D900
- P2 diagnostic trap:
  660/W500/D1500, diagnostic only, reference_too_weak non-rescuable, not candidate-family evidence.
- P1 preferred diameters:
  40, 60, 100, 150, 220, 230, 240, 250, 260, 270, 280, 290, 300 nm.
- 500 nm remains NODI RC13/out-of-library: eta blank, no interpolation, no zero proxy.
- NODI views:
  fixed_660_gold and per_wavelength_gold; no pooling, no consensus averaging, no independent-physical-campaign double count.
- Binning:
  edge_norm_1d = 20 bins over [0,1], width 0.05.
  xz_norm_2d = 21 x 21 bins over [-1,1]^2.
  Special aggregates for both distributions:
  near_center_0p0_0p5, selected_annulus_0p5_0p8, near_wall_0p8_1p0.
- Row counts:
  rows_per_route_diameter_view = 467.
  P1 preferred expected_rows = 60710.
  P2 diagnostic trap expected_rows = 12142.
- Event budget:
  seeds = 11,22,33.
  100 events/base-bin/seed.
  target post-seed events/bin = 300.
  sparse if post-seed n_events_bin < 100.
- Required sample/schema overlay fields:
  n_seeds, n_events_total, n_events_bin, n_events_bin_per_seed_min,
  sparse_bin_flag, sparse_bin_policy, bin_sample_status,
  decision_use_allowed, aggregate_source_type, flow_condition_id,
  flow_condition_version, flow_condition_source_sha, flow_condition_scope,
  flow_condition_claim_boundary.
- bin_sample_status is sample adequacy only:
  adequate | sparse | empty.
  guardrail_status is separate.
  guardrail_blocked is not a sample-status value.
- aggregate_source_type:
  edge_norm_primary | xz_norm_diagnostic | xz_norm_primary_if_adequate.
- Flow condition:
  flow_condition_id = p1b_w800_qch_splitmid_20260617
  flow_condition_scope = split_midplane_qch
  source evidence = P1B_W800_QCH_FIRST_LAUNCH_RESULTS_20260617.csv
  q_ch remains descriptive/provenance only; no q_ch*eta, no yield, no throughput.

2. NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY
- Status:
  APERTURE_SURROGATE_LOCAL_DESCRIPTOR_VERIFICATION = PASS
  APERTURE_SURROGATE_DESCRIPTOR_INPUT_CONTRACT = PASS_FOR_DRY_CONTRACT_DESIGN
  APERTURE_SURROGATE_DESCRIPTOR_BACKED_MODE_DESIGN = PASS_FOR_CONTRACT_ONLY
  APERTURE_SURROGATE_RUNNER_IMPLEMENTATION = BLOCKED_PENDING_USER_AUTHORIZATION
  APERTURE_SURROGATE_RUNNER_EXECUTION = BLOCKED_PENDING_USER_AUTHORIZATION
- Locally verified COMSOL descriptor sidecars:
  COMSOL_GEOMETRY_DESCRIPTOR_V1.csv
    rows = 2040
    SHA256 = 1198055754c41710a4821894ecb749660e5ef4a14b2e0fc647789ba31a0b38a2
  COMSOL_GEOMETRY_DESCRIPTOR_FIELD_EVIDENCE_V1.csv
    rows = 22
    SHA256 = d667112b6591b72f709bc8aed77711351f7fbbe5c874206fe7544c3a0f3aca91
  COMSOL_GEOMETRY_DESCRIPTOR_VALIDATION_REPORT_20260617.md
    SHA256 = 13059e6694cda2380d21f0ac6ead3ae8e425b01ec8d79c63ad4d6207d2bde14c
- Descriptor grain:
  route_geometry_id_comsol x process_state.
- Claim boundary:
  nominal_surrogate_geometry_descriptor_not_measured_not_optical_solver.
- Verified rules:
  W_top_um == width_group_um.
  W_bottom_um == bottom_width_nm / 1000.
  min_aperture_nm == min(bottom_width_nm, D_inscribed_nm).
  Negative min_aperture values are preserved, not clipped.
- Unavailable fields remain blank/unavailable_v1, not zero:
  bottom_cd_bias_nm, edge_lip_nm_per_side, residue_thickness_nm,
  roughness_rms_nm, scallop_amplitude_nm, rounded_corner_radius_nm.
- Allowed dry sensitivity modes:
  nominal_width
  W_bottom_conservative
  min_aperture_conservative
  top_bottom_average_heuristic
  COMSOL_descriptor_if_available.
- Rank source:
  fullgrid recommendation-eligible rank only.
  Stage-1 detector identity remains forbidden as candidate/rank/eligibility source.
- P3 triggers are solver-contract triggers only and are not solver execution authorization.

Please review and reply with PASS, PASS_WITH_CORRECTION, or BLOCKED for:
1. Whether this position-response contract is sufficient for COMSOL-side planning and future join design.
2. Whether COMSOL needs additional columns before NODI code-level runner/validator design.
3. Whether edge_norm_1d primary / xz_norm_2d diagnostic-unless-promoted is correct.
4. Whether W800 q_ch should remain only in versioned flow_condition_* provenance fields.
5. The exact durable path and SHA256 for P1B_W800_QCH_FIRST_LAUNCH_RESULTS_20260617.csv, if NODI must pin flow_condition_source_sha.
6. Whether the locally verified COMSOL geometry descriptor is sufficient for NODI dry aperture-surrogate contract design under the stated claim boundary.
7. Where the descriptor should live durably for joint provenance: COMSOL roadmap as source-of-truth with NODI hashes, or a mirrored NODI input package.
8. Whether any additional descriptor fields are required before NODI implements a dry validator, without any measured-geometry, true-W_eff, optical-solver, fabrication-release, or P3 claims.
9. Whether 500 nm remains RC13/out-of-library for NODI eta with no interpolation and no zero proxy.
10. Whether this handoff is correctly understood as review-only with no COMSOL run, no NODI run, and no JOINT_ROUTE_CLASS regeneration.
```

## 7. NODI local stop point after this handoff

After this handoff is sent to COMSOL, the next NODI stop point is:

```text
wait_for_COMSOL_launch_review_reply
```

If COMSOL replies `PASS`, NODI can proceed to a separate user-authorized
runner/validator implementation plan. The first implementation step should be
schema/validator/manifest construction and a bounded dry/smoke path, not a full
production response-surface run.

If COMSOL replies `PASS_WITH_CORRECTION`, NODI should update this contract by a
new overlay report rather than mutating Reports 149-154 in place.

If COMSOL replies `BLOCKED`, NODI should resolve the specific missing field,
claim-boundary conflict, or provenance-packaging issue before any runner work.
