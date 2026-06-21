# Report 194 - NODI/COMSOL Next Authorization Gate Plan

Date: 2026-06-18

## Disposition

`NEXT_AUTHORIZATION_GATE_PLAN_DEFINED_NOT_AUTHORIZED`

This report defines the next authorization gates required to move beyond the
current read-only NODI/COMSOL linkage state. It is a plan only. No gate below is
open unless the user gives the exact future authorization for that gate.

## Why This Gate Exists

The current accepted state is:

```text
NODI PRS/EAS production artifacts exist.
COMSOL read-only review returned PASS with no corrections required.
No COMSOL run, NODI rerun, JRC regeneration, q_ch weighting, yield, winner, true
W_eff, measured geometry, optical solver output, fabrication release, or P3
solver conclusion is authorized.
```

The next work must therefore separate:

```text
interface readiness work that is allowed now
from computation or claim-upgrade work that needs explicit future authorization
```

## Gate 0 - Read-Only Joint Interface Readiness

Status:

```text
ALLOWED_NOW
```

Allowed actions:

- verify PRS/EAS/selector/report hashes
- validate PRS/EAS row contracts
- verify COMSOL read-only PASS disposition
- produce consumer checklist
- produce no-output import report
- produce no-output dry mapping schema

Forbidden actions:

- COMSOL run
- NODI physical/evidence rerun
- JRC generation
- q_ch weighting
- yield/winner/detection probability

Exit artifact:

```text
NODI_COMSOL_JOINT_READINESS_REPORT_20260618.json/md
```

PASS condition:

```text
all current artifacts validate and all forbidden authorization flags remain false
```

BLOCKED condition:

```text
hash drift, missing production artifact, validator failure, or any forbidden
authorization flag becomes true
```

## Gate 1 - Pre-JRC Mapping Dry Run

Status:

```text
ALLOWED_ONLY_IF_NO_OUTPUT_JRC_AND_NO_WEIGHTED_SCORE
```

Purpose:

```text
prove that PRS/EAS/descriptor join keys can be mapped into a future JRC input
shape while leaving all unavailable fields explicitly blank/BLOCKED
```

Allowed outputs:

- dry mapping schema
- missing-field register
- join-key coverage table
- blocked-field table

Forbidden outputs:

- `JOINT_ROUTE_CLASS`
- route winner
- yield
- q_ch weighted eta
- detection probability

Exit artifact:

```text
NODI_COMSOL_PRE_JRC_DRY_MAPPING_REPORT_20260618.md
```

## Gate 2 - COMSOL Transport Or q_ch Sidecar Collection

Status:

```text
BLOCKED_PENDING_EXPLICIT_FUTURE_AUTHORIZATION
```

Future authorization phrase should be specific, for example:

```text
authorize COMSOL read/write generation of the transport/q_ch sidecar for NODI joint linkage
```

Minimum required inputs before opening:

- exact COMSOL repo/root and branch
- route set
- mesh/evidence level
- output label
- no-overwrite rule for older COMSOL artifacts
- stop condition if flow audit fails
- claim ceiling for proxy/coarse/diagnostic results

Required output if successful:

```text
transport/q_ch sidecar with route IDs, provenance, hashes, evidence class,
and explicit limitations
```

Required output if unsuccessful:

```text
BLOCKED report with no inferred q_ch weighting
```

## Gate 3 - Joint Weighting Prototype

Status:

```text
BLOCKED_PENDING_GATE_2_PASS_AND_EXPLICIT_FUTURE_AUTHORIZATION
```

Future authorization phrase should be specific, for example:

```text
authorize no-winner joint weighting prototype using approved COMSOL q_ch sidecar
```

Allowed only after Gate 2 provides a validated sidecar.

Allowed outputs:

- q_ch or transport weighted intermediate table
- provenance and uncertainty/boundary fields
- no-winner sensitivity readout if explicitly requested

Forbidden unless separately authorized:

- final yield
- final winner
- fabrication release
- P3 solver conclusion

## Gate 4 - JOINT_ROUTE_CLASS Regeneration

Status:

```text
BLOCKED_PENDING_GATE_3_REVIEW_AND_EXPLICIT_FUTURE_AUTHORIZATION
```

Future authorization phrase should be specific, for example:

```text
authorize JOINT_ROUTE_CLASS regeneration from reviewed NODI/COMSOL joint inputs
```

Minimum required inputs before opening:

- PRS production artifact and hash
- EAS production artifact and hash
- selector policy and hash
- COMSOL transport/q_ch sidecar and hash
- weighting prototype review result
- blocked-field register
- exact output path/label
- no-overwrite rule

Stop conditions:

- missing or stale input hash
- q_ch sidecar is proxy-only but output wording tries to claim true transport
- EAS surrogate is interpreted as true W_eff
- xz diagnostic rows are promoted without an explicit support policy
- any winner/yield field is requested without Gate 5

## Gate 5 - Yield/Winner/Detection Probability Claims

Status:

```text
BLOCKED_PENDING_STRONGER_EVIDENCE_AND_EXPLICIT_FUTURE_AUTHORIZATION
```

This is not the next immediate engineering step. It requires stronger evidence
than the current read-only interface package.

Required before considering:

- reviewed JRC output
- reviewed transport/q_ch evidence
- explicit yield definition
- explicit detection-probability denominator
- uncertainty/boundary treatment
- claim-language review
- user authorization

If any required input is missing, output must be:

```text
BLOCKED_NO_YIELD_OR_WINNER_AUTHORIZED
```

## Recommended Immediate Work

Proceed in this order:

1. Implement Gate 0 readiness verifier.
2. Generate a Gate 0 readiness report.
3. Build Gate 1 pre-JRC dry mapping schema and missing-field register.
4. Stop before Gate 2 until the user explicitly authorizes COMSOL-side
   transport/q_ch sidecar generation.

This is the efficient path because it makes both sides linkable without spending
compute or accidentally upgrading claims.

