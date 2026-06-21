# Report 152 - COMSOL geometry descriptor availability overlay

Date: 2026-06-17

Status:

```text
comsol_geometry_descriptor_reported_available
contract_overlay_only
no runner implementation authorized
no runner execution authorized
no NODI recomputation authorized
```

This report integrates the COMSOL-side update that the V1 geometry descriptor
sidecars are available and validation PASS. It updates the aperture-surrogate
contract state from "descriptor sidecars pending" to "descriptor sidecars
available by COMSOL evidence, pending local NODI unpack/hash verification before
formal consumption."

This report does not implement or execute any NODI runner, does not write a new
results CSV, does not run COMSOL, does not regenerate `JOINT_ROUTE_CLASS`, and
does not make optical or fabrication claims.

## 1. Source feedback

COMSOL reported:

| file | rows | SHA256 |
|---|---:|---|
| `COMSOL_GEOMETRY_DESCRIPTOR_V1.csv` | 2040 | `1198055754C41710A4821894ECB749660E5EF4A14B2E0FC647789BA31A0B38A2` |
| `COMSOL_GEOMETRY_DESCRIPTOR_FIELD_EVIDENCE_V1.csv` | 22 | `D667112B6591B72F709BC8AED77711351F7FBBE5C874206FE7544C3A0F3ACA91` |
| `COMSOL_GEOMETRY_DESCRIPTOR_VALIDATION_REPORT_20260617.md` | not reported | `13059E6694CDA2380D21F0AC6EAD3AE8E425B01EC8D79C63AD4D6207D2BDE14C` |

COMSOL reported:

```text
validation = PASS
descriptor grain = route_geometry_id_comsol x process_state
8160 gate rows -> 2040 descriptor rows
claim_boundary = nominal_surrogate_geometry_descriptor_not_measured_not_optical_solver
```

Local NODI status at integration time:

```text
descriptor files not found under /Volumes/Storage-Mac by local filename search
NODI has not unpacked or independently hash-verified these sidecars
```

Therefore this overlay records COMSOL evidence but does not claim local file
availability. Before any formal NODI consumption, the descriptor package must be
copied or unpacked into a NODI sidecar input directory and verified against the
reported SHA256 values.

## 2. Boundary

Still forbidden:

```text
measured geometry claim
true optical W_eff claim
fabrication release
non-rectangular optical solver output
calibrated optical evidence
q_ch * eta
yield
winner
EV passability claim
JOINT_ROUTE_CLASS regeneration
runner execution
```

Allowed by this overlay:

```text
effective-aperture surrogate dry sensitivity contract/design
descriptor input contract update
validator contract update
local-unpack verification plan
```

## 3. Descriptor implementation facts

COMSOL reported the descriptor was folded from `COMSOL_GATE_ROW.csv`
diameter-screen rows:

```text
COMSOL_GATE_ROW rows = 8160
descriptor rows = 2040
grain = route_geometry_id_comsol x process_state
```

Reported field construction:

```text
W_top_um = width_group_um
bottom_width_nm source values preserved
D_inscribed_nm source values preserved
min_aperture_nm = min(bottom_width_nm, D_inscribed_nm)
negative min_aperture_nm values are preserved, not clipped
```

Reported unavailable fields:

```text
bottom_cd_bias_nm
edge_lip_nm_per_side
residue_thickness_nm
roughness_rms_nm
scallop_amplitude_nm
rounded_corner_radius_nm
```

Reported non-claims:

```text
no measured geometry
no true W_eff
no optical solver result
```

## 4. Updated aperture-surrogate status

Report 151 status before this update:

```text
APERTURE_SURROGATE_COMSOL_DESCRIPTOR_CONSUMPTION = BLOCKED_PENDING_DESCRIPTOR_SIDECARS
```

Report 152 status after COMSOL feedback:

```text
APERTURE_SURROGATE_COMSOL_DESCRIPTOR_SIDECARS = REPORTED_AVAILABLE_PASS_BY_COMSOL
APERTURE_SURROGATE_LOCAL_DESCRIPTOR_VERIFICATION = BLOCKED_PENDING_LOCAL_UNPACK_AND_HASH_CHECK
APERTURE_SURROGATE_RUNNER_CONTRACT_DESIGN = PASS_FOR_DRY_CONTRACT_WITH_DESCRIPTOR_INPUTS
APERTURE_SURROGATE_RUNNER_IMPLEMENTATION = BLOCKED_PENDING_USER_AUTHORIZATION
APERTURE_SURROGATE_EXECUTION = BLOCKED_PENDING_USER_AUTHORIZATION
```

Interpretation:

```text
NODI may now design the effective-aperture surrogate runner/validator contract
against the reported descriptor files and hashes.
NODI may not formally consume descriptor rows until local unpack/hash
verification passes.
NODI may not execute a runner without separate user authorization.
```

## 5. Allowed dry sensitivity modes

COMSOL recommends the descriptor may be used for dry sensitivity design with
explicit modes:

```text
nominal_width
W_bottom_conservative
min_aperture_conservative
top_bottom_average_heuristic
```

NODI interpretation:

| mode | allowed now for contract design | formal row consumption before local descriptor verification | claim boundary |
|---|---|---|---|
| `nominal_width` | yes | yes, if sourced from existing NODI nominal route fields | surrogate dry sensitivity only |
| `W_bottom_conservative` | yes | no | descriptor-backed conservative surrogate only after local hash check |
| `min_aperture_conservative` | yes | no | descriptor-backed conservative surrogate only after local hash check |
| `top_bottom_average_heuristic` | yes | no | labeled heuristic only after local hash check |

`min_aperture_conservative` must preserve negative values if present in the
descriptor. Negative `min_aperture_nm` is not clipped to zero, not treated as an
optical eta, and not converted into a fabrication claim. It is a geometry
surrogate signal for sensitivity/veto context only.

## 6. Descriptor input contract

Future NODI input package must include:

```text
COMSOL_GEOMETRY_DESCRIPTOR_V1.csv
COMSOL_GEOMETRY_DESCRIPTOR_FIELD_EVIDENCE_V1.csv
COMSOL_GEOMETRY_DESCRIPTOR_VALIDATION_REPORT_20260617.md
COMSOL_GEOMETRY_DESCRIPTOR_HASHES.sha256 or equivalent hash manifest
```

Required local verification:

| code | check |
|---|---|
| CGD-IN01 | all three descriptor files are present in the declared input directory |
| CGD-IN02 | `COMSOL_GEOMETRY_DESCRIPTOR_V1.csv` has 2040 rows |
| CGD-IN03 | `COMSOL_GEOMETRY_DESCRIPTOR_FIELD_EVIDENCE_V1.csv` has 22 rows |
| CGD-IN04 | all file SHA256 values match COMSOL-reported hashes |
| CGD-IN05 | descriptor grain is `route_geometry_id_comsol x process_state` |
| CGD-IN06 | `claim_boundary` equals `nominal_surrogate_geometry_descriptor_not_measured_not_optical_solver` |
| CGD-IN07 | `min_aperture_nm = min(bottom_width_nm, D_inscribed_nm)` including negative values |
| CGD-IN08 | unavailable V1 fields remain blank/unavailable, not inferred as measured |
| CGD-IN09 | no column or report text claims measured geometry, true W_eff, optical solver result, fabrication release, or calibrated optical evidence |

## 7. Effective-aperture surrogate validator updates

Add these validator hard-fails to the future
`validate_nodi_effective_aperture_surrogate_sensitivity.py` contract:

| code | failure |
|---|---|
| EAS-V12 | descriptor input file is missing when a descriptor-backed mode is requested |
| EAS-V13 | descriptor file SHA256 differs from the COMSOL-reported hash |
| EAS-V14 | descriptor grain is not `route_geometry_id_comsol x process_state` |
| EAS-V15 | descriptor row count differs from 2040 |
| EAS-V16 | field-evidence sidecar row count differs from 22 |
| EAS-V17 | `min_aperture_nm` is clipped, abs-valued, or otherwise changed from descriptor value |
| EAS-V18 | negative `min_aperture_nm` is treated as optical eta or yield |
| EAS-V19 | unavailable V1 fields are inferred rather than blank/unavailable |
| EAS-V20 | descriptor-backed values are labeled measured geometry, true W_eff, optical solver result, fabrication release, or calibrated optical evidence |
| EAS-V21 | `W_bottom_conservative`, `min_aperture_conservative`, or `top_bottom_average_heuristic` is emitted without descriptor source hash |

## 8. Updated stop point

This COMSOL feedback removes the descriptor-sidecar availability blocker for
contract/design work, but not the local verification or execution blockers.

Current status:

| artifact | latest NODI-side status | still blocked by |
|---|---|---|
| `NODI_POSITION_RESPONSE_SURFACE` | unchanged from Report 151: `PASS_FOR_CONTRACT_ONLY_RUNNER_DESIGN` | user authorization before implementation or smoke execution |
| `NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY` | `PASS_FOR_DRY_CONTRACT_WITH_DESCRIPTOR_INPUTS` | local descriptor unpack/hash verification before formal consumption; user authorization before implementation/execution |

No additional progress should silently start a runner, write new result rows, or
mutate historical artifacts. The next legitimate NODI action, if explicitly
authorized, is a code-level runner/validator design package with tests and local
descriptor-input verification, still without full surrogate execution.
