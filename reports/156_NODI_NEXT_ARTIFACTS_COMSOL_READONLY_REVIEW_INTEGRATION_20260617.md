# Report 156 - NODI integration of COMSOL read-only review for next artifacts

Date: 2026-06-17

Status:

```text
comsol_readonly_review_integrated
pass_with_correction_accepted
no blocker
planning_artifact_only
no runner implementation
no runner execution
no NODI run
no COMSOL run
no JOINT_ROUTE_CLASS regeneration
```

This report records NODI's response to COMSOL's read-only review of the
runner/validator implementation plan bundle.

COMSOL disposition:

```text
PASS_WITH_CORRECTION
no BLOCKER
```

NODI response:

```text
corrections accepted
planning bundle patched before code-level runner implementation
```

## 1. Accepted by COMSOL

COMSOL accepted:

```text
Report 155 flow_condition semantics are correctly integrated
NODI-only position-response rows use neutral flow_condition_id
p1b_w800_qch_splitmid_20260617 is not treated as global transport distribution
W800 q_ch is constrained to scoped provenance tied to P1B-W800-001/002, JPI-028, and SHA BA92A77F...
effective-aperture surrogate remains dry sensitivity backed by COMSOL_GEOMETRY_DESCRIPTOR_V1
aperture surrogate does not claim true W_eff, measured geometry, or optical solver output
```

## 2. Correction A: explicit row_scope distinction

COMSOL requested:

```text
Add explicit row_scope distinction or equivalent validator rule:
response_surface_bin vs qch_provenance_reference.
Production NODI_POSITION_RESPONSE_SURFACE rows should contain only neutral NODI
flow_condition.
W800 q_ch should stay in manifest/provenance sidecar unless a distinct
provenance row type is explicitly defined.
```

NODI patch:

```text
reports/NODI_POSITION_RESPONSE_SURFACE_SCHEMA_CONTRACT_20260617.csv
```

New field:

```text
row_scope = response_surface_bin | qch_provenance_reference
default = response_surface_bin
```

Production table rule:

```text
production NODI_POSITION_RESPONSE_SURFACE rows must use row_scope=response_surface_bin
production rows must carry only flow_condition_id=nodi_position_response_surface_v1_not_comsol_transport
qch_provenance_reference is manifest/provenance-sidecar only unless a distinct sidecar contract is defined
```

Updated production-row flow fields:

```text
flow_condition_id = nodi_position_response_surface_v1_not_comsol_transport
flow_condition_scope = nodi_response_surface_not_transport_distribution
flow_condition_claim_boundary = nodi_synthetic_position_response_not_transport_occupancy
```

The production schema no longer lists `p1b_w800_qch_splitmid_20260617` as an
allowed `flow_condition_id` for response-surface rows.

Validator additions:

```text
PRS-V27 row_scope is present and response_surface_bin for production table rows
PRS-V28 qch_provenance_reference rows are absent from production response-surface table
PRS-V29 p1b_w800_qch_splitmid_20260617 absent from response_surface_bin rows
PRS-V30 response_surface_bin rows use neutral nodi_position_response_surface_v1_not_comsol_transport
PRS-V37 W800 q_ch provenance appears only in manifest/provenance sidecar with path/SHA/JPI/owner/status/row_count pinned
```

## 3. Correction B: rename W_eff_nm

COMSOL requested:

```text
Rename W_eff_nm to W_eff_surrogate_nm or aperture_surrogate_nm before implementation,
or otherwise hard-bind the field to not_true_W_eff=true and the
effective_aperture_surrogate_sensitivity_only claim boundary.
```

NODI patch:

```text
reports/NODI_EFFECTIVE_APERTURE_SURROGATE_SCHEMA_CONTRACT_20260617.csv
```

Renamed fields:

```text
W_eff_nm -> W_eff_surrogate_nm
delta_W_eff_nm -> delta_W_eff_surrogate_nm
```

Validator patch:

```text
EAS-V03 now checks W_eff_surrogate_nm appears only with:
aperture_surrogate_mode
not_true_W_eff=true
claim_boundary=effective_aperture_surrogate_sensitivity_only
```

Implementation plan patch:

```text
mode table now describes W_eff_surrogate_nm contract
nonpositive W_eff_surrogate_nm under min_aperture_conservative must not be clipped
```

## 4. Unchanged boundaries

This integration authorizes none of the following:

```text
runner implementation
runner execution
NODI run
COMSOL run
smoke execution
production response-surface artifact
production aperture-surrogate artifact
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

## 5. Updated affected artifacts

Patched artifacts:

```text
reports/NODI_NEXT_ARTIFACTS_RUNNER_IMPLEMENTATION_PLAN_20260617.md
reports/NODI_POSITION_RESPONSE_SURFACE_SCHEMA_CONTRACT_20260617.csv
reports/NODI_POSITION_RESPONSE_SURFACE_VALIDATOR_RULES_20260617.csv
reports/NODI_EFFECTIVE_APERTURE_SURROGATE_SCHEMA_CONTRACT_20260617.csv
reports/NODI_EFFECTIVE_APERTURE_SURROGATE_VALIDATOR_RULES_20260617.csv
reports/NODI_NEXT_ARTIFACTS_BOUNDARY_AND_FORBIDDEN_CLAIMS_20260617.md
reports/EXTERNAL_AI_PROMPTS_NODI_NEXT_ARTIFACTS_20260617.md
```

Unchanged support artifacts:

```text
reports/NODI_POSITION_RESPONSE_SURFACE_SMOKE_MANIFEST_20260617.csv
reports/NODI_EFFECTIVE_APERTURE_SURROGATE_SMOKE_MANIFEST_20260617.csv
```

## 6. Copyable NODI reply to COMSOL

```text
NODI accepts COMSOL's PASS_WITH_CORRECTION read-only review. No blocker.

Correction A integrated:
- Added row_scope to NODI_POSITION_RESPONSE_SURFACE schema.
- Production rows use row_scope=response_surface_bin only.
- Production rows carry only neutral NODI flow_condition_id:
  nodi_position_response_surface_v1_not_comsol_transport.
- qch_provenance_reference is kept out of production response-surface rows and
  may appear only in a manifest/provenance sidecar unless a distinct sidecar
  contract is separately defined.
- Validator rules PRS-V27..PRS-V30 and PRS-V37 enforce this.

Correction B integrated:
- Renamed W_eff_nm to W_eff_surrogate_nm.
- Renamed delta_W_eff_nm to delta_W_eff_surrogate_nm.
- Validator EAS-V03 binds W_eff_surrogate_nm to aperture_surrogate_mode,
  not_true_W_eff=true, and
  claim_boundary=effective_aperture_surrogate_sensitivity_only.

No runner implementation, runner execution, NODI run, COMSOL run, smoke
execution, production artifact, JOINT_ROUTE_CLASS regeneration, q_ch*eta, yield,
winner, true W_eff, measured geometry, optical solver output, fabrication
release, or P3 solver conclusion is authorized or performed.
```

## 7. Current stop point

```text
READY_FOR_USER_AUTHORIZATION_TO_IMPLEMENT_RUNNERS_AFTER_COMSOL_CORRECTION_OVERLAY
```

This is still an authorization stop point, not an implementation or execution
state.
