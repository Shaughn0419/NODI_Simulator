# Report 155 - NODI integration of COMSOL review for Report 154

Date: 2026-06-17

Status:

```text
comsol_report154_review_integrated
pass_with_correction_accepted
flow_condition_semantics_overlay_required_before_runner_implementation
no runner implementation authorized
no runner execution authorized
no NODI recomputation authorized
no COMSOL run requested
no JOINT_ROUTE_CLASS regeneration requested
```

This report records NODI's response to COMSOL's review of Report 154. It is an
overlay on Report 154, not an in-place mutation of Report 154.

COMSOL disposition:

```text
PASS_WITH_CORRECTION
```

NODI response:

```text
correction accepted
Report 154 remains valid subject to the flow_condition semantics overlay below
```

## 1. Source feedback

COMSOL feedback attachment:

```text
path = /Users/yanxuan/.codex/attachments/6105171d-44d7-4c82-afe5-e5d75a6e93a1/pasted-text.txt
sha256 = bbb68da3899deebe4dddbd0372c007f63506c32fce18f0125a25b0e2158aad5b
lines = 225
```

COMSOL confirmed that Report 154 is sufficient for NODI code-level
runner/validator design for both:

```text
NODI_POSITION_RESPONSE_SURFACE
NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY
```

COMSOL also confirmed that this review authorizes none of the following:

```text
COMSOL run
NODI run
runner implementation
runner execution
JOINT_ROUTE_CLASS regeneration
q_ch * eta
q_ch * chi_selected * eta
yield
winner
true W_eff
measured geometry
optical solver output
fabrication release
P3 solver conclusion
```

## 2. Accepted unchanged from Report 154

The following Report 154 clauses are accepted by COMSOL without further
correction.

### 2.1 Position-response matrix

Accepted P1 core routes:

```text
404/W500/D900
404/W500/D1200
660/W800/D900
660/W800/D1200
```

Accepted P1 diagnostic/context route:

```text
404/W600/D900
```

Accepted P2 diagnostic trap:

```text
660/W500/D1500
```

Trap route boundary:

```text
reference_too_weak remains non-rescuable
not candidate-family evidence
diagnostic only
```

Accepted P1 diameter matrix:

```text
40, 60, 100, 150, 220, 230, 240, 250, 260, 270, 280, 290, 300 nm
```

500 nm remains:

```text
RC13 / out_of_particle_library_scope
eta blank
no interpolation
no zero proxy
no low optical proxy
```

Accepted NODI views:

```text
fixed_660_gold
per_wavelength_gold
```

View rules:

```text
no pooling
no consensus averaging
no independent-campaign double count
```

Accepted binning:

```text
edge_norm_1d = 20 bins over [0,1], width 0.05
xz_norm_2d = 21 x 21 over [-1,1]^2
```

Accepted special aggregates:

```text
near_center_0p0_0p5
selected_annulus_0p5_0p8
near_wall_0p8_1p0
```

Accepted row-count arithmetic:

```text
rows_per_route_diameter_view = 467
P1 preferred expected_rows = 60710
P2 diagnostic trap expected_rows = 12142
```

Accepted event budget:

```text
seeds = 11,22,33
events_per_base_bin_per_seed = 100
target post-seed events/bin = 300
sparse if post-seed n_events_bin < 100
```

### 2.2 Sample status and aggregate role

Accepted sample-status rules:

```text
bin_sample_status = adequate | sparse | empty
guardrail_status remains separate
guardrail_blocked must not be a sample-status value
decision_use_allowed must be false for sparse/empty individual bins unless explicitly aggregate-level
```

Accepted aggregate-source enum:

```text
edge_norm_primary
xz_norm_diagnostic
xz_norm_primary_if_adequate
```

Accepted aggregate interpretation:

```text
edge_norm_1d is the primary COMSOL join artifact
xz_norm_2d is diagnostic/context unless sample-adequate and explicitly promoted
```

### 2.3 Aperture-surrogate contract

Accepted aperture-surrogate status:

```text
fullgrid recommendation-eligible rank only
Stage-1 detector identity forbidden as candidate/rank/eligibility source
W_bottom is not true W_eff
W_bottom is not default optical width
P3 triggers are solver-contract triggers only, not solver execution authorization
```

COMSOL confirmed that the locally verified geometry descriptor is sufficient for
NODI dry aperture-surrogate contract design under the stated boundary.

Descriptor anchors:

| artifact | rows | SHA256 |
|---|---:|---|
| `COMSOL_GEOMETRY_DESCRIPTOR_V1.csv` | 2040 | `1198055754C41710A4821894ECB749660E5EF4A14B2E0FC647789BA31A0B38A2` |
| `COMSOL_GEOMETRY_DESCRIPTOR_FIELD_EVIDENCE_V1.csv` | 22 | `D667112B6591B72F709BC8AED77711351F7FBBE5C874206FE7544C3A0F3ACA91` |
| `COMSOL_GEOMETRY_DESCRIPTOR_VALIDATION_REPORT_20260617.md` | not applicable | `13059E6694CDA2380D21F0AC6EAD3AE8E425B01EC8D79C63AD4D6207D2BDE14C` |

Descriptor grain:

```text
route_geometry_id_comsol x process_state
```

Accepted descriptor rules:

```text
W_top_um == width_group_um
W_bottom_um == bottom_width_nm / 1000
min_aperture_nm == min(bottom_width_nm, D_inscribed_nm)
negative min_aperture values preserved, not clipped
unavailable fields remain blank/unavailable_v1, not zero
```

Claim boundary:

```text
nominal_surrogate_geometry_descriptor_not_measured_not_optical_solver
```

No additional descriptor fields are required before NODI implements a dry
validator, provided unavailable fields stay unavailable and the descriptor is
not treated as measured geometry, true optical aperture, true W_eff, optical
solver output, fabrication release, or P3 evidence.

### 2.4 Durable descriptor packaging

Accepted packaging correction:

```text
COMSOL source-of-truth remains COMSOL-side roadmap/JPI artifacts
NODI tmp/ is local verification staging only, not durable provenance
NODI may mirror files into a NODI input package for convenience
mirrors must reference COMSOL source paths and exact SHA values
```

Durable COMSOL source paths:

```text
roadmap/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv
roadmap/COMSOL_GEOMETRY_DESCRIPTOR_FIELD_EVIDENCE_V1.csv
roadmap/COMSOL_GEOMETRY_DESCRIPTOR_VALIDATION_REPORT_20260617.md
```

## 3. Required correction: flow_condition semantics

COMSOL correction:

```text
flow_condition_id = p1b_w800_qch_splitmid_20260617
must not be applied globally to all NODI position-response rows
```

NODI accepts this correction.

Corrected interpretation:

```text
flow_condition fields are provenance/distribution-context fields
they do not create a global COMSOL flow condition for NODI response-surface rows
```

The response-surface artifact must distinguish:

```text
NODI-only synthetic initial-position response rows
COMSOL W800 q_ch provenance/context rows
future COMSOL transported-distribution rows
```

## 4. Corrected flow_condition row classes

### 4.1 NODI-only response-surface rows

Use these values for NODI-only response-surface rows:

```text
flow_condition_id = nodi_position_response_surface_v1_not_comsol_transport
flow_condition_scope = nodi_response_surface_not_transport_distribution
flow_condition_source_sha = <NODI response-surface artifact sha after generation>
flow_condition_claim_boundary = nodi_synthetic_position_response_not_transport_occupancy
position_distribution_basis = nodi_synthetic_initial_position
view_physical_independence_flag = false
not_comsol_transport_distribution = true
not_qch_weighted = true
not_yield = true
not_detection_probability = true
```

Before a response-surface artifact exists, runner design documents may use:

```text
flow_condition_source_sha = pending_until_artifact_generation
```

The generated artifact itself must replace that placeholder with its actual
artifact SHA in the manifest or row-level provenance contract, as appropriate.

NODI-only rows must not carry:

```text
flow_condition_id = p1b_w800_qch_splitmid_20260617
position_distribution_basis = comsol_transported_distribution
not_comsol_transport_distribution = false
not_qch_weighted = false
yield-like fields
detection-probability fields
```

### 4.2 COMSOL W800 q_ch provenance rows

Use the COMSOL q_ch flow condition only for W800 q_ch provenance/context rows
tied to the COMSOL anchors:

```text
P1B-W800-001
P1B-W800-002
```

Required values:

```text
flow_condition_id = p1b_w800_qch_splitmid_20260617
flow_condition_scope = split_midplane_qch
flow_condition_source_path = roadmap/P1B_W800_QCH_FIRST_LAUNCH_RESULTS_20260617.csv
flow_condition_source_sha = BA92A77F92E0D972D7059DD8A60B5696AA3C649E5686AD3B474D6112F265ECEC
flow_condition_claim_boundary = q_ch_descriptive_provenance_only_not_transport_occupancy_not_qch_eta
jpi_anchor = JPI-028
source_owner = COMSOL
source_status = available_sha_pinned
source_row_count = 92
```

Boundary:

```text
q_ch remains descriptive-only
no q_ch * eta
no q_ch * chi_selected * eta
no yield
no throughput detection
no scalar score
no winner
```

### 4.3 Future COMSOL transported-distribution rows

No future COMSOL transported-distribution row is authorized by this report.

If such rows are later provided under a separate passed contract, they must use:

```text
position_distribution_basis = comsol_transported_distribution
not_comsol_transport_distribution = false
```

`not_qch_weighted` may become false only if a future COMSOL transported
distribution explicitly supplies q_ch-weighted occupancy under a separate
contract. This report does not authorize that future state.

## 5. Additional required implementation fields

COMSOL requires these additional fields before runner implementation:

```text
response_surface_artifact_version
position_distribution_basis
view_physical_independence_flag
not_comsol_transport_distribution
not_qch_weighted
not_yield
not_detection_probability
```

`position_distribution_basis` enum:

```text
nodi_synthetic_initial_position
comsol_transported_distribution
not_applicable_response_surface_only
```

NODI interpretation:

| field | current NODI-only response-surface value | reason |
|---|---|---|
| `response_surface_artifact_version` | `NODI_POSITION_RESPONSE_SURFACE_V1` | schema/version anchor |
| `position_distribution_basis` | `nodi_synthetic_initial_position` | response surface is sampled by NODI, not transported by COMSOL |
| `view_physical_independence_flag` | `false` | two NODI views share one physical event stream |
| `not_comsol_transport_distribution` | `true` | response rows are not COMSOL occupancy rows |
| `not_qch_weighted` | `true` | q_ch is not multiplied into eta |
| `not_yield` | `true` | response rows are not yield rows |
| `not_detection_probability` | `true` | response rows are not calibrated detection probability |

## 6. Validator overlay additions

Add these validator rules after Report 151 `PRS-V25`.

| code | failure |
|---|---|
| PRS-V26 | `p1b_w800_qch_splitmid_20260617` appears on a NODI-only response-surface row |
| PRS-V27 | NODI-only response-surface row lacks neutral `nodi_position_response_surface_v1_not_comsol_transport` flow condition |
| PRS-V28 | `position_distribution_basis` missing or outside allowed enum |
| PRS-V29 | NODI-only response-surface row has `position_distribution_basis != nodi_synthetic_initial_position` |
| PRS-V30 | `view_physical_independence_flag` missing or not `false` |
| PRS-V31 | NODI-only response-surface row has `not_comsol_transport_distribution != true` |
| PRS-V32 | NODI-only response-surface row has `not_qch_weighted`, `not_yield`, or `not_detection_probability` missing or not `true` |
| PRS-V33 | W800 q_ch provenance row has wrong source path, SHA, JPI anchor, owner, status, or row count |
| PRS-V34 | q_ch provenance is used to create `q_ch*eta`, yield, throughput, scalar score, or winner |
| PRS-V35 | future `comsol_transported_distribution` basis appears without a separate passed COMSOL transported-distribution contract |

These rules are implementation-contract rules only. They do not authorize a
runner implementation or execution.

## 7. Updated launch status after COMSOL correction

Position response:

```text
POSITION_RESPONSE_REPORT154_COMSOL_REVIEW = PASS_WITH_CORRECTION
POSITION_RESPONSE_FLOW_CONDITION_OVERLAY = PASS_ACCEPTED_BY_NODI
POSITION_RESPONSE_RUNNER_CONTRACT_DESIGN = PASS_FOR_CODE_LEVEL_DESIGN_AFTER_OVERLAY
POSITION_RESPONSE_RUNNER_IMPLEMENTATION = BLOCKED_PENDING_USER_AUTHORIZATION
POSITION_RESPONSE_RUNNER_EXECUTION = BLOCKED_PENDING_USER_AUTHORIZATION
```

Aperture surrogate:

```text
APERTURE_SURROGATE_REPORT154_COMSOL_REVIEW = PASS
APERTURE_SURROGATE_DESCRIPTOR_INPUT_CONTRACT = PASS_FOR_DRY_CONTRACT_DESIGN
APERTURE_SURROGATE_DESCRIPTOR_PACKAGING = PASS_WITH_CORRECTION_COMSOL_SOURCE_OF_TRUTH
APERTURE_SURROGATE_RUNNER_IMPLEMENTATION = BLOCKED_PENDING_USER_AUTHORIZATION
APERTURE_SURROGATE_RUNNER_EXECUTION = BLOCKED_PENDING_USER_AUTHORIZATION
```

Durable packaging:

```text
DESCRIPTOR_DURABLE_SOURCE_OF_TRUTH = COMSOL_ROADMAP_JPI
NODI_TMP_DESCRIPTOR_STATUS = LOCAL_VERIFICATION_STAGING_ONLY
NODI_MIRROR_PACKAGE = OPTIONAL_CONVENIENCE_ONLY_WITH_COMSOL_PATH_AND_SHA_REFERENCES
```

## 8. Copyable NODI reply to COMSOL

```text
NODI response to COMSOL review of Report 154:

Disposition received: PASS_WITH_CORRECTION.

NODI accepts the correction. Report 154 remains valid as a launch-review
contract subject to the flow_condition semantics overlay below. NODI will not
apply flow_condition_id=p1b_w800_qch_splitmid_20260617 globally to all
position-response rows.

Corrected NODI interpretation:

1. NODI-only response-surface rows will use neutral provenance:
- flow_condition_id = nodi_position_response_surface_v1_not_comsol_transport
- flow_condition_scope = nodi_response_surface_not_transport_distribution
- flow_condition_source_sha = <NODI response-surface artifact sha after generation>
- flow_condition_claim_boundary = nodi_synthetic_position_response_not_transport_occupancy
- position_distribution_basis = nodi_synthetic_initial_position
- view_physical_independence_flag = false
- not_comsol_transport_distribution = true
- not_qch_weighted = true
- not_yield = true
- not_detection_probability = true

2. COMSOL W800 q_ch provenance will use the q_ch flow condition only for scoped
W800 q_ch evidence rows tied to P1B-W800-001 and P1B-W800-002:
- flow_condition_id = p1b_w800_qch_splitmid_20260617
- flow_condition_scope = split_midplane_qch
- flow_condition_source_path = roadmap/P1B_W800_QCH_FIRST_LAUNCH_RESULTS_20260617.csv
- flow_condition_source_sha = BA92A77F92E0D972D7059DD8A60B5696AA3C649E5686AD3B474D6112F265ECEC
- jpi_anchor = JPI-028
- owner = COMSOL
- status = available_sha_pinned
- row_count = 92

3. NODI accepts the additional implementation fields:
- response_surface_artifact_version
- position_distribution_basis
- view_physical_independence_flag
- not_comsol_transport_distribution
- not_qch_weighted
- not_yield
- not_detection_probability

4. NODI accepts that COMSOL roadmap/JPI artifacts remain the durable source of
truth for the descriptor sidecars. NODI tmp/ remains local verification staging
only. Any future NODI mirror package will cite COMSOL source paths and exact SHA
values.

5. NODI preserves all global boundaries:
- no COMSOL run
- no NODI run
- no runner implementation or execution from this review alone
- no JOINT_ROUTE_CLASS regeneration
- no q_ch*eta
- no q_ch*chi_selected*eta
- no yield
- no winner
- no true W_eff
- no measured geometry
- no optical solver output
- no fabrication release
- no P3 solver conclusion

NODI local status after this overlay:
- POSITION_RESPONSE_RUNNER_CONTRACT_DESIGN =
  PASS_FOR_CODE_LEVEL_DESIGN_AFTER_OVERLAY
- APERTURE_SURROGATE_DESCRIPTOR_INPUT_CONTRACT =
  PASS_FOR_DRY_CONTRACT_DESIGN
- runner implementation remains BLOCKED_PENDING_USER_AUTHORIZATION
- runner execution remains BLOCKED_PENDING_USER_AUTHORIZATION
```

## 9. NODI stop point

NODI can now treat the launch-review contract as corrected and sufficient for a
future code-level runner/validator implementation plan.

Current stop point:

```text
await_user_authorization_for_runner_validator_implementation_plan
```

The next allowed NODI work, after explicit user authorization, is:

```text
schema and validator implementation planning
manifest/source-package design
bounded dry/smoke runner path design
```

Still not allowed without separate authorization:

```text
full response-surface production run
aperture-surrogate production run
COMSOL run
JOINT_ROUTE_CLASS regeneration
P3 solver execution
```
