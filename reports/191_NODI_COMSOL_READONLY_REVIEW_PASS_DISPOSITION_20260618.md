# Report 191 - NODI/COMSOL Read-Only Review PASS Disposition

Date: 2026-06-18

## Disposition

`PASS_COMSOL_READONLY_REVIEW_NO_CORRECTIONS_REQUIRED`

The COMSOL-side read-only review of the full-production NODI next-artifacts package
returned `PASS` with no corrections required before downstream use of the reviewed
package contents.

Reviewed package:

- `tmp/nodi_comsol_readonly_review_full_production_20260618.zip`
- external reviewed copy:
  `/Volumes/Storage-Mac/codex project/comsol test/tmp/nodi_comsol_readonly_review_full_production_20260618.zip`
- SHA256:
  `b7924da8896bee47ac85052b329eeae65efe8adc11cc130eaed3104a934a4b6a`

## Scope Of The PASS

This PASS covers read-only review of:

- Reports 185-188
- production PRS/EAS CSVs
- selector-policy JSON
- production gate report, blockers, and issues files
- supporting candidate and preflight outputs
- `nodi_comsol_next_artifacts.py`
- runner scripts
- contract tests

The review found no required corrections for the reviewed PRS, EAS, production
gate, reporting, or validators.

## Artifact Findings

### PRS

`NODI_POSITION_RESPONSE_SURFACE.csv` passed review.

- rows: 1868
- route/diameter/view grains: 4
- rows per grain: 467
- `edge_norm_primary`: 92
- `xz_norm_diagnostic`: 1776
- `xz_norm_primary_if_adequate`: 0
- SHA256:
  `e584deecf43ac163f2a904782569143b3c4095bcb72dd439d598d652ee70869e`

All rows preserve:

- `row_scope=response_surface_bin`
- `flow_condition_id=nodi_position_response_surface_v1_not_comsol_transport`
- `not_qch_weighted=true`
- `not_yield=true`
- `not_detection_probability=true`

No q_ch weighting, eta weighting, COMSOL transport distribution, yield, or
detection-probability claim was promoted.

### EAS

`NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv` passed review.

- rows: 32
- selector policy: nominal smooth geometry
- sidewall angle: `sidewall_deg=85.0`
- SHA256:
  `35c8b43e641631b682df07dc305ee17bc97384e6cf135c94adce791748243ecc`

The reviewed EAS flags preserve dry-surrogate boundaries:

- `not_true_W_eff=true`
- `not_measured_geometry=true`
- `not_optical_solver_output=true`
- `not_fabrication_release=true`
- `not_yield=true`
- `not_winner=true`

No P3 solver conclusion is present.

### Production Gate

Production gate/reporting passed review.

The production PRS SHA matches the validated candidate SHA:

`e584deecf43ac163f2a904782569143b3c4095bcb72dd439d598d652ee70869e`

Report 188's missing/invalid candidate fix is reflected in implementation and
tests:

- supplied-but-missing or invalid candidates block with
  `blocked_invalid_position_response_candidate`
- omitted PRS candidate preserves the older EAS-only partial path

## Local Reverification

After recording the COMSOL feedback, NODI-side read-only verification was rerun
against the current local artifacts:

```bash
python tools/audits/validate_nodi_position_response_surface.py \
  tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_POSITION_RESPONSE_SURFACE.csv \
  --require-complete-row-arithmetic

python tools/audits/validate_nodi_position_response_surface.py \
  tmp/nodi_position_response_edge_primary_candidate_20260618/NODI_POSITION_RESPONSE_SURFACE_EDGE_PRIMARY_CANDIDATE_20260618.csv \
  --require-complete-row-arithmetic

python tools/audits/validate_nodi_effective_aperture_surrogate_sensitivity.py \
  tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv \
  --geometry-descriptor tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv
```

Results:

- production PRS validator: `PASS`
- candidate PRS validator: `PASS`
- EAS validator: `PASS`
- production generation report validator: `PASS`
- review package file count: 26
- review package AppleDouble / `__MACOSX` scan: none found

## Boundary That Still Holds

This PASS does not authorize any of the following:

- COMSOL run
- NODI run
- `JOINT_ROUTE_CLASS` regeneration
- q_ch weighting or q_ch*eta
- yield computation
- winner selection
- detection-probability computation
- true `W_eff`
- measured geometry
- optical solver output
- fabrication release
- P3 solver conclusions

Any such downstream action still requires a separate future authorization gate.

## Updated State

Report 190's local state can now be read with this sidecar update:

- previous local handoff status:
  `NODI_LOCAL_HANDOFF_READY_WITHOUT_COMSOL_ACCEPTANCE`
- new read-only review disposition:
  `PASS_COMSOL_READONLY_REVIEW_NO_CORRECTIONS_REQUIRED`
- production generation status remains:
  `PASS_PRODUCTION_GENERATION`
- claim boundary remains:
  local production artifacts plus read-only COMSOL review PASS, without downstream
  run/regeneration/weighting/yield/winner authorization

Machine-readable sidecar:

`tmp/nodi_comsol_readonly_review_disposition_20260618/NODI_COMSOL_READONLY_REVIEW_DISPOSITION_20260618.json`

Sidecar SHA256:

`b4d203ed032c5744344fa9bcbe958ad97018ba207b141eb5630ca964b9ad6623`
