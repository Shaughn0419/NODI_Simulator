# Report 151 - COMSOL feedback integration and runner-contract overlay

Date: 2026-06-17

Status:

```text
comsol_feedback_integrated
runner_contract_overlay_only
no runner implementation authorized
no runner execution authorized
no NODI recomputation authorized
```

This report integrates the COMSOL-side confirmation/correction received after
Report 150. It is an overlay on Reports 149 and 150, not a replacement of their
reviewed evidence hashes.

Source feedback:

```text
path = /Users/yanxuan/.codex/attachments/1bdb747a-1ce3-4b0b-8e83-08ab418ac899/pasted-text.txt
sha256 = a7c7952bc86ef1f1c71421077e14518dc9464cda14078bd20525c2613319e9bd
lines = 300
```

COMSOL explicitly confirmed that the feedback is contract/design review only.
It does not authorize a COMSOL run, NODI runner execution, `q_ch*eta`, yield,
winner, calibrated detector claim, EV passability claim, or
`JOINT_ROUTE_CLASS` regeneration.

## 1. Updated boundary

Still forbidden:

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
non-rectangular full-wave solver claim
```

Allowed by this overlay:

```text
update schema contract
update validator contract
update row-count interpretation
update COMSOL follow-up dependencies
define runner-contract readiness state
```

## 2. Position response surface: COMSOL confirmations

### 2.1 Route matrix

Status:

```text
PASS_WITH_CAVEAT
```

Accepted P1 core:

```text
404/W500/D900
404/W500/D1200
660/W800/D900
660/W800/D1200
```

Accepted diagnostic/context:

```text
404/W600/D900
```

Accepted P2 diagnostic trap:

```text
660/W500/D1500 diagnostic only
reference_too_weak remains non-rescuable by transport
must not become candidate-family evidence
```

### 2.2 Diameter matrix

Status:

```text
PASS
```

Canonical P1 preferred diameter matrix:

```text
40, 60, 100, 150, 220, 230, 240, 250, 260, 270, 280, 290, 300 nm
```

500 nm policy remains:

```text
NODI out_of_particle_library_scope / RC13
no eta
no interpolation
no zero or low optical proxy
```

### 2.3 Binning and aggregate interpretation

Status:

```text
PASS
```

COMSOL confirms:

```text
edge_norm_1d = 20 bins over [0, 1], bin width 0.05
xz_norm_2d = 21 x 21 bins over [-1, 1]^2
special aggregates emitted for both edge_norm_1d and xz_norm_2d
```

The Report 150 row-count contract remains valid:

```text
rows_per_route_diameter_view = 467
P1 preferred expected_rows = 60710
P1 minimum expected_rows = 37360
P2 diagnostic trap expected_rows = 12142
```

Updated aggregate priority:

```text
edge_norm aggregates are the primary join artifact
xz_norm_2d aggregates are diagnostic/context unless sample counts are adequate
individual sparse xz_norm_2d bins must not drive decision-changing route priority
```

New required field:

```text
aggregate_source_type
```

Allowed values:

```text
edge_norm_primary
xz_norm_diagnostic
xz_norm_primary_if_adequate
```

Mapping:

| distribution_type | row_kind | default aggregate_source_type | decision role |
|---|---|---|---|
| `edge_norm_1d` | `base_bin` | `edge_norm_primary` | primary if adequate |
| `edge_norm_1d` | `special_aggregate` | `edge_norm_primary` | primary if adequate |
| `xz_norm_2d` | `base_bin` | `xz_norm_diagnostic` | context unless adequate and explicitly promoted |
| `xz_norm_2d` | `special_aggregate` | `xz_norm_diagnostic` | context unless adequate and explicitly promoted |

Promotion to `xz_norm_primary_if_adequate` requires a validator-visible reason
and must not be inferred from nonblank eta alone.

### 2.4 Aggregation and sparse-bin policy

Status:

```text
PASS
```

Primary table:

```text
post-seed aggregated at route/lambda/W/D/diameter/bin
```

Diagnostic sidecar:

```text
per-seed rows only
```

COMSOL requires these fields in the primary response-surface table:

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
sparse_bin_flag = true when post-seed n_events_bin < 100
empty = n_events_bin == 0
sparse = 0 < n_events_bin < 100
adequate = n_events_bin >= 100
```

Decision-use rule:

```text
decision_use_allowed = true only when bin_sample_status is adequate,
or when a special aggregate is explicitly allowed as aggregate-level evidence.
sparse individual bins are visualization/context only.
empty bins are never decision-use rows.
```

Compatibility note:

```text
Report 149 used bin_status.
Report 151 makes bin_sample_status the canonical field.
bin_sample_status describes sample adequacy only.
guardrail_status describes NODI eligibility/guardrail state.
If a future implementation retains bin_status, it is a legacy compatibility
field only and not the primary decision field.
```

Legacy compatibility mapping:

| Report 149 `bin_status` | Report 151 handling |
|---|---|
| `ok` | `bin_sample_status=adequate` if `n_events_bin >= 100`; otherwise reject as inconsistent |
| `insufficient_bin_events` | `bin_sample_status=sparse` |
| `empty_bin` | `bin_sample_status=empty` |
| `guardrail_blocked` | not a sample-status value; represent through `guardrail_status` plus `decision_use_allowed=false` |

If `bin_status=guardrail_blocked` is retained for backward compatibility, the
row must also carry:

```text
guardrail_status != recommendation_eligible
decision_use_allowed = false
```

The validator must reject any row where `bin_status` is used to override
`bin_sample_status`, `guardrail_status`, or `decision_use_allowed`.

Accepted P1 event target:

```text
seed_set = 11,22,33
events_per_base_bin_per_seed = 100
target_post_seed_events_per_bin = 300
sparse threshold = post-seed n_events_bin < 100
```

### 2.5 NODI views

Status:

```text
PASS
```

COMSOL prefers both views:

```text
fixed_660_gold
per_wavelength_gold
```

Required rules:

```text
NODI_view column must be present
no pooling across views
no consensus averaging
do not treat two views as independent physical campaigns
```

Preferred P1 remains both views. A reduced pilot is allowed only if explicitly
labeled as reduced and if view selection is route-scoped:

```text
per_wavelength_gold for 660/W800
fixed_660_gold for 404/W500
```

The full P1 contract remains both views unless the user authorizes a reduced
pilot.

### 2.6 Flow-condition versioning

Status:

```text
PASS_WITH_VERSIONING
```

COMSOL says `flow_condition_id` is stable enough for future joins only when
treated as source-versioned, not universal.

New optional/context fields for response-surface packages:

```text
flow_condition_id
flow_condition_version
flow_condition_source_sha
flow_condition_scope
flow_condition_claim_boundary
```

Allowed `flow_condition_scope`:

```text
nominal_smooth_fullchip
split_midplane_qch
local_direct_cell
future_transport_distribution
```

Current W800 q_ch context must use a new flow condition, not the old p6 anchor:

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
no yield
no throughput detection
```

## 3. Updated NODI_POSITION_RESPONSE_SURFACE schema overlay

Report 151 adds these required or conditional fields to the Report 149/150
schema:

```text
n_seeds
n_events_total
n_events_bin_per_seed_min
sparse_bin_flag
sparse_bin_policy
bin_sample_status
decision_use_allowed
aggregate_source_type
flow_condition_id
flow_condition_version
flow_condition_source_sha
flow_condition_scope
flow_condition_claim_boundary
```

Field status:

| field | status | notes |
|---|---|---|
| `n_seeds` | required | primary table post-seed aggregate support |
| `n_events_total` | required | total event samples represented by the row |
| `n_events_bin_per_seed_min` | required | minimum per-seed bin count before aggregation |
| `sparse_bin_flag` | required | true when post-seed `n_events_bin < 100` |
| `sparse_bin_policy` | required | fixed text or enum describing sparse handling |
| `bin_sample_status` | required | canonical adequate/sparse/empty field |
| `decision_use_allowed` | required | prevents sparse xz bins from driving route priority |
| `aggregate_source_type` | required | distinguishes edge primary from xz diagnostic |
| `flow_condition_*` | conditional | required when COMSOL flow context is attached |

Validator additions:

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

Updated position-response status:

```text
POSITION_RESPONSE_COMSOL_FEEDBACK = PASS
POSITION_RESPONSE_SCHEMA_OVERLAY = PASS
POSITION_RESPONSE_RUNNER_CONTRACT_DESIGN = PASS_FOR_CONTRACT_ONLY
POSITION_RESPONSE_RUNNER_IMPLEMENTATION = BLOCKED_PENDING_USER_AUTHORIZATION
POSITION_RESPONSE_RUNNER_EXECUTION = BLOCKED_PENDING_SMOKE_AUTHORIZATION
```

## 4. Effective aperture surrogate: COMSOL confirmations

### 4.1 Rank source and guardrails

Status:

```text
PASS
```

Confirmed:

```text
use fullgrid recommendation-eligible rank only
Stage-1 detector identity remains forbidden as candidate-family/rank/eligibility source
W_bottom is not true W_eff and not default optical width
P3 triggers are solver-contract triggers only, not solver execution authorization
```

### 4.2 Geometry descriptor availability

Status:

```text
PASS_BUT_NOT_COMPLETE_MEASURED_DESCRIPTOR
```

COMSOL can produce a V1 nominal/surrogate descriptor derived from:

```text
COMSOL_GATE_ROW.csv
COMSOL_GATE_ROW_CONTRACT_20260616.md
deterministic geometry tables
```

Currently available fields:

```text
route_geometry_id_comsol
route_geometry_id_comsol_sha256
angle_convention
process_state
W_nominal_nm
width_group_um
sidewall_deg
depth_um
D_nm
bottom_width_nm
D_inscribed_nm
comsol_source_sha256
claim_boundary
```

Currently unavailable in complete descriptor form:

```text
explicit W_top_um
explicit W_bottom_um, though bottom_width_nm exists
bottom_cd_bias_nm
edge_lip_nm_per_side
residue_thickness_nm
roughness_rms_nm
scallop_amplitude_nm
rounded_corner_radius_nm
explicit min_aperture_nm
```

Required descriptor label:

```text
geometry_descriptor_source = nominal_or_surrogate_from_COMSOL_gate
claim_boundary = nominal_surrogate_geometry_descriptor_not_measured_not_optical_solver
```

Forbidden descriptor interpretation:

```text
measured_geometry
true W_eff
optical solver result
```

### 4.3 Descriptor sidecars requested from COMSOL

COMSOL recommended next sidecars:

```text
COMSOL_GEOMETRY_DESCRIPTOR_V1.csv
COMSOL_GEOMETRY_DESCRIPTOR_FIELD_EVIDENCE_V1.csv
COMSOL_GEOMETRY_DESCRIPTOR_VALIDATION_REPORT_20260617.md
```

NODI may design against the descriptor schema now. NODI must not consume
COMSOL-specific `W_bottom` or `min_aperture` values as formal sidecar inputs
until the descriptor table and field-evidence sidecar are generated and pinned.

NODI must not hard-code a COMSOL descriptor SHA before COMSOL provides the
descriptor package.

### 4.4 Recommended descriptor schema

Identity fields:

```text
geometry_descriptor_id
route_geometry_id_comsol
route_geometry_id_comsol_version = V1_route_process_identity
process_state
descriptor_version
descriptor_sha256
```

Nominal/surrogate geometry fields:

```text
W_top_um
W_bottom_um
W_nominal_nm
width_group_um
sidewall_deg
depth_um
bottom_cd_bias_nm
edge_lip_nm_per_side
residue_thickness_nm
roughness_rms_nm
scallop_amplitude_nm
rounded_corner_radius_nm
min_aperture_nm
D_inscribed_nm
```

Evidence rules:

| field | V1 evidence class | V1 source rule |
|---|---|---|
| `W_top_um` | nominal | `width_group_um` or `W_nominal_nm / 1000` unless top-CD table is bound |
| `W_bottom_um` | simulated/surrogate | `bottom_width_nm / 1000` |
| `W_nominal_nm` | nominal | COMSOL gate row |
| `width_group_um` | nominal | COMSOL gate row |
| `sidewall_deg` | nominal/design-state | COMSOL gate row |
| `depth_um` | nominal/design-state | COMSOL gate row |
| `bottom_cd_bias_nm` | unavailable unless deterministic table is bound | leave unavailable in V1 if unbound |
| `edge_lip_nm_per_side` | unavailable | V1 unavailable |
| `residue_thickness_nm` | unavailable | V1 unavailable |
| `roughness_rms_nm` | unavailable | V1 unavailable |
| `scallop_amplitude_nm` | unavailable | V1 unavailable |
| `rounded_corner_radius_nm` | unavailable | V1 unavailable |
| `min_aperture_nm` | surrogate if contract-defined | `min(bottom_width_nm, D_inscribed_nm)` only if contract-defined; otherwise unavailable |
| `D_inscribed_nm` | simulated/surrogate | COMSOL gate row/deterministic geometry |

Source/provenance fields:

```text
source_artifact
source_sha256
geometry_descriptor_source
per_field_evidence_class_json or long-form sidecar
claim_boundary
```

Long-form field-evidence sidecar:

```text
field_name
evidence_class
source_column
source_artifact
```

### 4.5 Dry sensitivity design

COMSOL says NODI should not wait for measured geometry.

Allowed immediate dry sensitivity design modes:

```text
nominal_width
min_aperture_conservative
```

Preferred full mode enum:

```text
nominal_width
W_bottom_conservative
min_aperture_conservative
top_bottom_average_heuristic
COMSOL_descriptor_if_available
```

Compatibility note:

```text
Reports 149/150 used COMSOL_effective_aperture_descriptor.
Report 151 uses COMSOL_descriptor_if_available to avoid implying physical or
measured effective aperture.
If both labels appear in future code/docs, the validator must require the
Report 151 claim boundary and forbid true-W_eff interpretation.
```

Immediate dry design status:

```text
APERTURE_SURROGATE_DRY_CONTRACT_DESIGN = PASS_FOR_NOMINAL_AND_MIN_APERTURE_SCHEMA
APERTURE_SURROGATE_COMSOL_DESCRIPTOR_CONSUMPTION = BLOCKED_PENDING_DESCRIPTOR_SIDECARS
APERTURE_SURROGATE_RUNNER_IMPLEMENTATION = BLOCKED_PENDING_USER_AUTHORIZATION
APERTURE_SURROGATE_EXECUTION = BLOCKED_PENDING_USER_AUTHORIZATION
```

## 5. Updated stop point

The COMSOL feedback removes several uncertainties from Report 150:

```text
route matrix confirmed
diameter matrix confirmed
edge/xz binning confirmed
special aggregates confirmed for both distribution families
100 events/base-bin/seed accepted for P1 planning with sparse guard
both NODI views preferred
flow_condition_id usable only as source-versioned context
V1 nominal/surrogate geometry descriptor is feasible but not yet packaged
```

The current NODI-side stop point is:

| artifact | latest status | still blocked by |
|---|---|---|
| `NODI_POSITION_RESPONSE_SURFACE` | `PASS_FOR_CONTRACT_ONLY_RUNNER_DESIGN` | user authorization before implementation or smoke execution |
| `NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY` | `PASS_FOR_DRY_CONTRACT_DESIGN` | COMSOL descriptor sidecars before formal COMSOL-specific W_bottom/min_aperture consumption; user authorization before implementation/execution |

No additional progress should silently start a runner, write a new results CSV,
or mutate historical artifacts. The next legitimate NODI action, if authorized,
is a code-level runner/validator design package with tests but no full execution.
