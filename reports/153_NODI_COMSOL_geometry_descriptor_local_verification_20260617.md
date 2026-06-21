# Report 153 - COMSOL geometry descriptor local verification

Date: 2026-06-17

Status:

```text
comsol_geometry_descriptor_local_verification_pass
verification_only
no runner implementation authorized
no runner execution authorized
no NODI recomputation authorized
```

This report verifies the three COMSOL geometry descriptor sidecars that were
placed in the local NODI `tmp/` directory. It advances Report 152 from
"reported available by COMSOL" to "locally present and hash/structure verified."

It does not execute a NODI runner, does not generate aperture-surrogate rows,
does not run COMSOL, does not regenerate `JOINT_ROUTE_CLASS`, and does not make
optical, fabrication, or measured-geometry claims.

## 1. Local input files

Verified local files:

```text
tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv
tmp/COMSOL_GEOMETRY_DESCRIPTOR_FIELD_EVIDENCE_V1.csv
tmp/COMSOL_GEOMETRY_DESCRIPTOR_VALIDATION_REPORT_20260617.md
```

Hash verification:

| file | expected SHA256 | observed SHA256 | verdict |
|---|---|---|---|
| `COMSOL_GEOMETRY_DESCRIPTOR_V1.csv` | `1198055754C41710A4821894ECB749660E5EF4A14B2E0FC647789BA31A0B38A2` | `1198055754c41710a4821894ecb749660e5ef4a14b2e0fc647789ba31a0b38a2` | PASS |
| `COMSOL_GEOMETRY_DESCRIPTOR_FIELD_EVIDENCE_V1.csv` | `D667112B6591B72F709BC8AED77711351F7FBBE5C874206FE7544C3A0F3ACA91` | `d667112b6591b72f709bc8aed77711351f7fbbe5c874206fe7544c3a0f3aca91` | PASS |
| `COMSOL_GEOMETRY_DESCRIPTOR_VALIDATION_REPORT_20260617.md` | `13059E6694CDA2380D21F0AC6EAD3AE8E425B01EC8D79C63AD4D6207D2BDE14C` | `13059e6694cda2380d21f0ac6ead3ae8e425b01ec8d79c63ad4d6207d2bde14c` | PASS |

SHA case differs only by uppercase/lowercase formatting.

Line counts:

| file | line count | data rows | expected data rows | verdict |
|---|---:|---:|---:|---|
| `COMSOL_GEOMETRY_DESCRIPTOR_V1.csv` | 2041 | 2040 | 2040 | PASS |
| `COMSOL_GEOMETRY_DESCRIPTOR_FIELD_EVIDENCE_V1.csv` | 23 | 22 | 22 | PASS |
| `COMSOL_GEOMETRY_DESCRIPTOR_VALIDATION_REPORT_20260617.md` | 59 | not applicable | not applicable | PASS |

## 2. Structured CSV verification

Descriptor table:

```text
descriptor_rows = 2040
descriptor_columns = 22
unique(route_geometry_id_comsol, process_state) = 2040
duplicate_grain = 0
process_states = nominal_smooth_geometry only
claim_boundary = nominal_surrogate_geometry_descriptor_not_measured_not_optical_solver
```

Field-evidence table:

```text
field_evidence_rows = 22
field_evidence_columns = 10
field_name unique count = 22
claim_boundary = nominal_surrogate_geometry_descriptor_not_measured_not_optical_solver
```

Observed evidence classes:

```text
claim_boundary_constant
contract_constant
nominal/design-state
provenance_constant
surrogate/simulated geometry rule
unavailable_v1
```

## 3. Geometry rule verification

Checked rules:

| rule | mismatches | verdict |
|---|---:|---|
| `W_top_um == width_group_um` | 0 | PASS |
| `W_bottom_um == bottom_width_nm / 1000` | 0 | PASS |
| `min_aperture_nm == min(bottom_width_nm, D_inscribed_nm)` | 0 | PASS |

Negative `min_aperture_nm` preservation:

```text
negative_min_aperture_rows = 141
min_aperture_nm range = -519.116655945367 to 900.0
negative values are preserved, not clipped
```

Interpretation boundary:

```text
negative min_aperture_nm is geometry-surrogate evidence only
not optical eta
not yield
not EV passability
not fabrication release
```

## 4. Unavailable-field verification

The following V1 unavailable/metrology fields are blank in all 2040 descriptor
rows:

```text
bottom_cd_bias_nm
edge_lip_nm_per_side
residue_thickness_nm
roughness_rms_nm
scallop_amplitude_nm
rounded_corner_radius_nm
```

All six have:

```text
nonblank_count = 0
```

Field evidence marks these fields as `unavailable_v1`. Blank means unavailable,
not zero.

## 5. Claim-boundary verification

The descriptor CSV has no literal hits for:

```text
measured_geometry
true W_eff
fabrication release
optical solver result
winner
yield
```

The field-evidence CSV contains `winner` and `yield` only in repeated negative
boundary notes of the form:

```text
introduces no ... yield, or winner
```

The validation report likewise uses these terms in forbidden-use or no-claim
contexts. These are negative-boundary statements, not positive claims.

Validation report status:

```text
Validation status: PASS
```

The validation report also states:

```text
No COMSOL process was started
no comsolbatch process was started
no .mph file was loaded
no optical solver or W_eff value was generated
```

## 6. Updated aperture-surrogate status

Report 152 status:

```text
APERTURE_SURROGATE_LOCAL_DESCRIPTOR_VERIFICATION = BLOCKED_PENDING_LOCAL_UNPACK_AND_HASH_CHECK
```

Report 153 status:

```text
APERTURE_SURROGATE_LOCAL_DESCRIPTOR_VERIFICATION = PASS
APERTURE_SURROGATE_DESCRIPTOR_INPUT_CONTRACT = PASS_FOR_DRY_CONTRACT_DESIGN
APERTURE_SURROGATE_DESCRIPTOR_BACKED_MODE_DESIGN = PASS_FOR_CONTRACT_ONLY
APERTURE_SURROGATE_RUNNER_IMPLEMENTATION = BLOCKED_PENDING_USER_AUTHORIZATION
APERTURE_SURROGATE_RUNNER_EXECUTION = BLOCKED_PENDING_USER_AUTHORIZATION
```

Allowed descriptor-backed dry design modes after this local verification:

```text
W_bottom_conservative
min_aperture_conservative
top_bottom_average_heuristic
COMSOL_descriptor_if_available
```

These modes remain:

```text
dry sensitivity / surrogate only
not measured geometry
not true optical W_eff
not calibrated optical evidence
not P3 solver output
```

P3 boundary:

```text
P3 triggers are solver-contract triggers only.
They are not solver execution authorization.
This descriptor does not authorize a non-rectangular optical solver.
```

## 7. Remaining stop point

The descriptor sidecar local-verification blocker is now cleared for contract
design.

Still blocked:

| item | status |
|---|---|
| persistent descriptor input package location | `tmp/` is verified but not a long-term provenance package |
| aperture-surrogate runner implementation | blocked pending user authorization |
| aperture-surrogate runner execution | blocked pending user authorization |
| final optical claims / P3 solver conclusions | blocked; not supported by V1 descriptor |

Before any future runner consumes these files, the input package should be
declared in a durable sidecar location and the same SHA checks should be repeated
or referenced from a hash manifest.
