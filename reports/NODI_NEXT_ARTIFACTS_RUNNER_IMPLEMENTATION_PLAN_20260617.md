# NODI next artifacts runner implementation plan

Date: 2026-06-17

Status:

```text
READY_FOR_USER_AUTHORIZATION_TO_IMPLEMENT_RUNNERS
planning_artifact_only
no runner implementation performed
no runner execution performed
no NODI simulation run
no COMSOL run
no production artifact generated
```

This plan converts the Report 155 contract into an implementation plan for two
future NODI artifacts:

```text
NODI_POSITION_RESPONSE_SURFACE
NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY
```

It does not implement runners, does not execute smoke, does not execute full
production, and does not regenerate `JOINT_ROUTE_CLASS`.

## 1. Source scope

COMSOL-side next-step instruction:

```text
path = /Users/yanxuan/.codex/attachments/67c45ab7-3e25-471c-bd23-1e104e2fc6d2/pasted-text.txt
sha256 = c5eb8bc32ed92c4b197fc2d037a4f037d87758ebd1a6f9bf9aa508d2a7f4f48b
lines = 303
```

Required source reports:

```text
reports/149_NODI_COMSOL_position_response_aperture_surrogate_design_plan_20260617.md
reports/150_NODI_COMSOL_next_artifacts_launch_review_stop_point_20260617.md
reports/151_NODI_COMSOL_feedback_integration_runner_contract_overlay_20260617.md
reports/152_NODI_COMSOL_geometry_descriptor_availability_overlay_20260617.md
reports/153_NODI_COMSOL_geometry_descriptor_local_verification_20260617.md
reports/154_NODI_COMSOL_launch_review_contract_handoff_20260617.md
reports/155_NODI_COMSOL_report154_review_integration_overlay_20260617.md
```

NODI local note:

```text
The COMSOL prompt names roadmap/154 and roadmap/155.
In this NODI workspace, the corresponding files are under reports/.
```

## 2. Deliverables created by this planning step

```text
reports/NODI_NEXT_ARTIFACTS_RUNNER_IMPLEMENTATION_PLAN_20260617.md
reports/NODI_POSITION_RESPONSE_SURFACE_SCHEMA_CONTRACT_20260617.csv
reports/NODI_POSITION_RESPONSE_SURFACE_VALIDATOR_RULES_20260617.csv
reports/NODI_POSITION_RESPONSE_SURFACE_SMOKE_MANIFEST_20260617.csv
reports/NODI_EFFECTIVE_APERTURE_SURROGATE_SCHEMA_CONTRACT_20260617.csv
reports/NODI_EFFECTIVE_APERTURE_SURROGATE_VALIDATOR_RULES_20260617.csv
reports/NODI_EFFECTIVE_APERTURE_SURROGATE_SMOKE_MANIFEST_20260617.csv
reports/NODI_NEXT_ARTIFACTS_BOUNDARY_AND_FORBIDDEN_CLAIMS_20260617.md
reports/EXTERNAL_AI_PROMPTS_NODI_NEXT_ARTIFACTS_20260617.md
```

The optional external prompt is included because this workflow has repeatedly
benefited from independent review before runner authorization.

## 3. Boundary

Allowed now:

```text
schema contract design
validator rule contract design
bounded dry/smoke path design
implementation entry-point planning
manifest/source-package planning
external review prompt planning
```

Still forbidden:

```text
runner implementation
runner execution
NODI simulation
full production run
production response-surface artifact
production aperture-surrogate artifact
COMSOL run
JOINT_ROUTE_CLASS regeneration
q_ch * eta
q_ch * chi_selected * eta
yield
winner
true W_eff
measured geometry
optical solver output
fabrication release
calibrated detector claim
P3 solver conclusion
```

## 4. Implementation lane A: NODI_POSITION_RESPONSE_SURFACE

### 4.1 Proposed future files

These are proposed future implementation files. They are not created by this
planning step:

```text
tools/audits/build_nodi_position_response_surface.py
tools/audits/validate_nodi_position_response_surface.py
tests/test_nodi_position_response_surface_contract.py
```

The implementation should prefer a sidecar export path rather than mutating
existing fullgrid outputs.

### 4.2 Existing code anchor

`nodi_simulator/parameter_sweep.py` already carries event-level position
diagnostics such as:

```text
initial_position_x_norm
initial_position_z_norm
position_diag
selected_annulus_edge_norm_min
selected_annulus_edge_norm_max
```

The future runner should use these event diagnostics or a bin-conditioned
initial-position sampling hook. It should not infer a full response surface by
reshaping the existing P0 COMSOL handoff.

### 4.3 Production contract, not production execution

Route matrix:

```text
P1 core:
404/W500/D900
404/W500/D1200
660/W800/D900
660/W800/D1200

P1 diagnostic/context:
404/W600/D900

P2 diagnostic trap:
660/W500/D1500
diagnostic only
reference_too_weak non-rescuable
not candidate-family evidence
```

Diameter matrix:

```text
40, 60, 100, 150, 220, 230, 240, 250, 260, 270, 280, 290, 300 nm
```

500 nm policy:

```text
out_of_particle_library_scope / RC13
eta blank
no interpolation
no zero proxy
no low optical proxy
```

Views:

```text
fixed_660_gold
per_wavelength_gold
no pooling
no consensus averaging
no independent-campaign double count
```

Binning:

```text
edge_norm_1d = 20 bins over [0,1], width 0.05
xz_norm_2d = 21 x 21 over [-1,1]^2
```

Special aggregates for both distributions:

```text
near_center_0p0_0p5
selected_annulus_0p5_0p8
near_wall_0p8_1p0
```

Expected row arithmetic:

```text
rows_per_route_diameter_view = 467
P1 preferred expected_rows = 60710
P2 diagnostic trap expected_rows = 12142
```

Event budget:

```text
seeds = 11,22,33
events_per_base_bin_per_seed = 100
target post-seed events/bin = 300
sparse if post-seed n_events_bin < 100
```

### 4.4 Position-response runner design

Future runner phases:

1. Load a route/diameter/view manifest and reject any unapproved route or
   diameter.
2. Generate edge and xz bin definitions before any event work.
3. For each route, diameter, view, and seed, accumulate bin-conditioned event
   counts and response proxy counts.
4. Aggregate post-seed at route/lambda/W/D/diameter/view/bin.
5. Emit per-seed rows only in a diagnostic sidecar.
6. Join guardrail state from `exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv`.
7. Attach neutral NODI-only flow-condition provenance.
8. Validate schema, row arithmetic, sample-status logic, guardrail separation,
   flow-condition semantics, and forbidden-claim lexicon before writing a
   release candidate.

NODI-only response rows must carry:

```text
row_scope = response_surface_bin
flow_condition_id = nodi_position_response_surface_v1_not_comsol_transport
flow_condition_scope = nodi_response_surface_not_transport_distribution
flow_condition_source_sha = <artifact sha after generation>
flow_condition_claim_boundary = nodi_synthetic_position_response_not_transport_occupancy
position_distribution_basis = nodi_synthetic_initial_position
view_physical_independence_flag = false
not_comsol_transport_distribution = true
not_qch_weighted = true
not_yield = true
not_detection_probability = true
```

`p1b_w800_qch_splitmid_20260617` is allowed only on scoped W800 q_ch provenance
references in a manifest/provenance sidecar tied to:

```text
P1B-W800-001
P1B-W800-002
roadmap/P1B_W800_QCH_FIRST_LAUNCH_RESULTS_20260617.csv
SHA256 = BA92A77F92E0D972D7059DD8A60B5696AA3C649E5686AD3B474D6112F265ECEC
JPI-028
```

Production `NODI_POSITION_RESPONSE_SURFACE` rows must not embed W800 q_ch
provenance rows. A future sidecar may use:

```text
row_scope = qch_provenance_reference
```

only if that sidecar is explicitly defined and kept outside the production
response-surface table.

### 4.5 Position-response bounded smoke design

The smoke path is for schema and arithmetic validation only.

Default smoke subset:

```text
routes = 404/W500/D900, 660/W800/D900, 404/W600/D900
diameters = 40, 150, 220, 270, 300 nm
views = fixed_660_gold, per_wavelength_gold
rows = 3 routes * 5 diameters * 2 views * 467 = 14010
```

Core-only fallback:

```text
routes = 404/W500/D900, 660/W800/D900
diameters = 40, 150, 220, 270, 300 nm
views = fixed_660_gold, per_wavelength_gold
rows = 2 routes * 5 diameters * 2 views * 467 = 9340
```

One-view fallback:

```text
allowed only as smoke-cost fallback
must be labeled one_view_schema_smoke_only
must not replace the two-view production contract
```

Smoke remains:

```text
not production
not final route decision
not COMSOL transport distribution
not q_ch weighted
not yield
not detection probability
```

## 5. Implementation lane B: NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY

### 5.1 Proposed future files

These are proposed future implementation files. They are not created by this
planning step:

```text
tools/audits/build_nodi_effective_aperture_surrogate_sensitivity.py
tools/audits/validate_nodi_effective_aperture_surrogate_sensitivity.py
tests/test_nodi_effective_aperture_surrogate_contract.py
```

### 5.2 Required inputs

COMSOL descriptor sidecars:

```text
roadmap/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv
rows = 2040
SHA256 = 1198055754C41710A4821894ECB749660E5EF4A14B2E0FC647789BA31A0B38A2

roadmap/COMSOL_GEOMETRY_DESCRIPTOR_FIELD_EVIDENCE_V1.csv
rows = 22
SHA256 = D667112B6591B72F709BC8AED77711351F7FBBE5C874206FE7544C3A0F3ACA91

roadmap/COMSOL_GEOMETRY_DESCRIPTOR_VALIDATION_REPORT_20260617.md
SHA256 = 13059E6694CDA2380D21F0AC6EAD3AE8E425B01EC8D79C63AD4D6207D2BDE14C
```

Durable source-of-truth:

```text
COMSOL roadmap/JPI remains authoritative
NODI tmp/ is staging only
NODI mirror package is optional convenience only
NODI mirror must carry COMSOL source path and SHA references
```

NODI rank and guardrail inputs:

```text
exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv
source_rank_basis = fullgrid_recommendation_eligible_rank_contract
source_rank_column = recommendation_eligible_rank

exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv
join keys = lambda_nm, W_nominal_nm, D_nm
```

### 5.3 Descriptor rules

The validator must enforce:

```text
grain = route_geometry_id_comsol x process_state
W_top_um == width_group_um
W_bottom_um == bottom_width_nm / 1000
min_aperture_nm == min(bottom_width_nm, D_inscribed_nm)
negative min_aperture values are preserved, not clipped
unavailable fields remain blank/unavailable_v1, not zero
```

### 5.4 Surrogate modes

Allowed dry sensitivity modes:

```text
nominal_width
W_bottom_conservative
min_aperture_conservative
top_bottom_average_heuristic
COMSOL_descriptor_if_available
```

Mode calculations for future implementation:

| mode | W_eff_surrogate_nm contract |
|---|---|
| `nominal_width` | `W_nominal_nm` |
| `W_bottom_conservative` | `W_bottom_um * 1000` |
| `min_aperture_conservative` | `min_aperture_nm`, preserving negative values as surrogate evidence |
| `top_bottom_average_heuristic` | `((W_top_um + W_bottom_um) / 2) * 1000` |
| `COMSOL_descriptor_if_available` | descriptor-backed value selected by explicit mode policy, never implicit default |

Nonpositive `W_eff_surrogate_nm` under `min_aperture_conservative` must not be clipped.
The future runner should mark optical proxy fields blank or blocked when the
surrogate aperture is nonpositive rather than inventing a low optical proxy.

### 5.5 Aperture-surrogate bounded smoke design

Smoke routes:

```text
404/W500/D900
404/W500/D1200
660/W800/D900
660/W800/D1200
```

Smoke modes:

```text
nominal_width
W_bottom_conservative
min_aperture_conservative
```

Smoke views:

```text
fixed_660_gold
per_wavelength_gold
```

Planned default smoke row arithmetic:

```text
4 routes * 2 views * 3 modes = 24 planned rows
no weighting splits are authorized in this contract
```

The smoke validates:

```text
rank source
guardrail carry-through
descriptor SHA binding
unavailable_v1 handling
negative aperture preservation
P3 trigger flags as solver-contract triggers only
forbidden-claim hard fails
```

Smoke output is not a final route decision.

## 6. Validator sequencing

The future implementation should run validators in this order:

1. Schema columns and enum checks.
2. Source path/SHA checks.
3. Row-grain uniqueness checks.
4. Route/diameter/view/mode scope checks.
5. Sample-status and row-arithmetic checks for position response.
6. Descriptor-rule and rank-source checks for aperture surrogate.
7. Flow-condition semantics checks.
8. Guardrail separation checks.
9. Forbidden-claim lexicon checks.
10. Manifest hash and row-count checks.

Any validator failure should block artifact promotion and write a validation
report with explicit `BLOCKED_BEFORE_IMPLEMENTATION` or `BLOCKED_BEFORE_RELEASE`
status, depending on phase.

## 7. User authorization gate

Current status:

```text
READY_FOR_USER_AUTHORIZATION_TO_IMPLEMENT_RUNNERS
```

This means the plan is ready for user review and potential authorization of a
separate implementation step. It does not authorize implementation or execution.

If authorized, the next implementation step should be:

```text
create schema constants and validators first
create dry-run manifest writer second
create runner entry points third
run only bounded smoke after a separate smoke authorization
```
