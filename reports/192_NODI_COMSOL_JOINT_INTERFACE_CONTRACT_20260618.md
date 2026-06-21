# Report 192 - NODI/COMSOL Joint Interface Contract

Date: 2026-06-18

## Disposition

`JOINT_INTERFACE_CONTRACT_DEFINED_NO_JOINT_EXECUTION_AUTHORIZED`

This report defines the main interface contract for the next NODI/COMSOL linkage
phase. It supersedes the fragmented "what next" discussion with one joint
contract surface:

```text
NODI production artifacts -> COMSOL/joint consumers
COMSOL descriptor/review evidence -> NODI/joint consumers
future authorization gates -> any computation that would change joint claims
```

This is not a joint production merge. It does not run COMSOL, rerun NODI,
regenerate `JOINT_ROUTE_CLASS`, weight by q_ch, compute yield, choose a winner,
or promote true W_eff, measured geometry, optical solver output, fabrication
release, or P3 solver conclusions.

## Current Accepted State

NODI production generation:

- status: `PASS_PRODUCTION_GENERATION`
- source report: `reports/187_NODI_NEXT_ARTIFACTS_FULL_PRODUCTION_GENERATION_PRS_EAS_20260618.md`
- output dir:
  `tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/`

COMSOL read-only review:

- status: `PASS_COMSOL_READONLY_REVIEW_NO_CORRECTIONS_REQUIRED`
- source report:
  `reports/191_NODI_COMSOL_READONLY_REVIEW_PASS_DISPOSITION_20260618.md`
- reviewed package SHA256:
  `b7924da8896bee47ac85052b329eeae65efe8adc11cc130eaed3104a934a4b6a`

Important interpretation:

```text
PASS means the read-only reviewed package has no required corrections.
PASS does not mean COMSOL has run, transported occupancy exists, JRC exists,
or any winner/yield/true-W_eff claim is authorized.
```

## Interface Principle

The next phase is an interface-engineering phase, not a physics-result upgrade.

Allowed now:

- define schemas, role boundaries, ownership, and consumer rules
- build read-only import/readiness checks
- build no-output dry mapping checks
- package artifacts with explicit claim ceilings
- document future authorization gates and stop conditions

Not allowed now:

- COMSOL execution
- NODI physical/evidence rerun that changes claims
- `JOINT_ROUTE_CLASS` regeneration
- q_ch or q_ch*eta weighting
- yield, winner, detection-probability, or scalar joint-score computation
- true W_eff, measured geometry, optical solver, fabrication-release, or P3
  solver conclusions

## Contract A - NODI_POSITION_RESPONSE_SURFACE

Producer:

```text
NODI
```

Current artifact:

```text
tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_POSITION_RESPONSE_SURFACE.csv
```

Artifact SHA256:

```text
e584deecf43ac163f2a904782569143b3c4095bcb72dd439d598d652ee70869e
```

Current row contract:

```text
rows = 1868
route/diameter/view grains = 4
rows per grain = 467
edge_norm_primary rows = 92
xz_norm_diagnostic rows = 1776
xz_norm_primary_if_adequate rows = 0
row_scope = response_surface_bin
flow_condition_id = nodi_position_response_surface_v1_not_comsol_transport
```

Consumer rule:

```text
COMSOL/joint consumers may read PRS as conditional NODI optical response by
position bin. They must not treat PRS rows as transported occupancy, q_ch
weights, yield, detection probability, or route winner evidence.
```

Allowed current use:

```text
read-only schema import
row arithmetic checks
route/diameter/view join-key checks
future consumer dry-run mapping with no weighted output
```

Blocked current use:

```text
COMSOL transport weighting
q_ch * eta
yield
winner
detection probability
JOINT_ROUTE_CLASS generation
```

## Contract B - NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY

Producer:

```text
NODI, using COMSOL geometry descriptor as nominal dry-surrogate descriptor input
```

Current artifact:

```text
tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv
```

Artifact SHA256:

```text
35c8b43e641631b682df07dc305ee17bc97384e6cf135c94adce791748243ecc
```

Current row contract:

```text
rows = 32
selector policy = nominal_smooth_geometry
sidewall_deg = 85.0
field uses W_eff_surrogate_nm, not W_eff_nm
not_true_W_eff = true
not_measured_geometry = true
not_optical_solver_output = true
not_fabrication_release = true
not_yield = true
not_winner = true
```

Consumer rule:

```text
COMSOL/joint consumers may read EAS as dry surrogate sensitivity only. They must
not treat W_eff_surrogate_nm as true W_eff, measured geometry, optical-solver
output, fabrication release, yield evidence, or winner evidence.
```

Allowed current use:

```text
read-only sensitivity import
geometry-descriptor join-key checks
surrogate-mode comparison
future dry-run mapping with no solver or winner output
```

Blocked current use:

```text
true W_eff claim
measured geometry claim
optical solver conclusion
fabrication release
P3 solver conclusion
yield or winner ranking
```

## Contract C - COMSOL Geometry Descriptor

Producer:

```text
COMSOL side, reviewed locally by NODI as descriptor input
```

Current artifact:

```text
tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv
```

Current artifact SHA256:

```text
1198055754c41710a4821894ecb749660e5ef4a14b2e0fc647789ba31a0b38a2
```

Current row contract:

```text
rows = 2040
route_geometry_id_comsol_version = route_geometry_id_comsol_v1_contract_20260616
process_state includes nominal_smooth_geometry
angle_convention = sidewall_angle_from_substrate_plane_90deg_vertical
claim_boundary = nominal descriptor / dry surrogate input, not measured geometry
```

Consumer rule:

```text
NODI may use this descriptor only as nominal dry-surrogate geometry input. Joint
consumers must not promote it to measured geometry, fabrication release, or
optical solver output.
```

## Contract D - Review And Production Gate Evidence

Producer:

```text
NODI production gate plus COMSOL read-only reviewer
```

Current artifacts:

```text
reports/187_NODI_NEXT_ARTIFACTS_FULL_PRODUCTION_GENERATION_PRS_EAS_20260618.md
reports/188_NODI_NEXT_ARTIFACTS_PRODUCTION_GATE_REVIEW_FIX_20260618.md
reports/191_NODI_COMSOL_READONLY_REVIEW_PASS_DISPOSITION_20260618.md
tmp/nodi_comsol_readonly_review_disposition_20260618/NODI_COMSOL_READONLY_REVIEW_DISPOSITION_20260618.json
```

Consumer rule:

```text
These artifacts prove local production generation plus COMSOL read-only package
review PASS. They do not prove COMSOL execution, joint merge, or downstream
physics-claim authorization.
```

## Future Interface Inputs Not Yet Available

The following are not present in the current accepted state:

| future input | producer | needed for | current status |
|---|---|---|---|
| COMSOL transported position distribution | COMSOL | PRS transport weighting | missing; not authorized |
| route-level q_ch or flow split sidecar for this joint phase | COMSOL | q_ch*eta or weighted ranking | missing; not authorized |
| validated transport-distribution provenance | COMSOL | detection probability / occupancy | missing; not authorized |
| measured geometry evidence | COMSOL/fabrication metrology | true geometry claim | missing; not authorized |
| optical solver output linked to EAS | solver lane | P3 or optical-solver conclusion | missing; not authorized |
| explicit JRC generation authorization | user/gate | `JOINT_ROUTE_CLASS` output | missing; not authorized |

## Joint Keys

Current safe join keys:

```text
route_id_nodi
lambda_nm
W_nominal_nm
D_nm
NODI_view
diameter_nm for PRS
aperture_surrogate_mode for EAS
source hash and artifact path for provenance
```

Current unsafe or incomplete join assumptions:

```text
do not join PRS rows to q_ch weights unless a future q_ch sidecar is authorized
do not join xz_norm_diagnostic rows as primary transport bins
do not collapse fixed_660_gold and per_wavelength_gold into one physical campaign
do not infer true W_eff from W_eff_surrogate_nm
do not infer measured geometry from COMSOL_GEOMETRY_DESCRIPTOR_V1
```

## Mainline Work Packages

The next efficient sequence is:

1. `joint_interface_readiness`:
   build a machine-readable readiness matrix and consumer checklist around this
   contract.
2. `no-output_import_checks`:
   validate that downstream consumers can read PRS/EAS/descriptor/review evidence
   and preserve all claim flags.
3. `pre_jrc_mapping_dry_run`:
   map keys and missing fields into a dry-run table that writes no
   `JOINT_ROUTE_CLASS` and no weighted scores.
4. `authorization_gate_design`:
   define exact future phrases, input requirements, stop conditions, and BLOCKED
   outputs for any COMSOL run, JRC regeneration, q_ch weighting, yield/winner, or
   solver-claim step.

Reports 193 and 194 instantiate work packages 1 and 4.

