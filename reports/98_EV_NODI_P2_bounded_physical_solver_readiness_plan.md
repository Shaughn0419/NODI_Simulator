# EV/NODI P2 Bounded Physical-Solver Readiness Plan

Date: 2026-05-10

Status:

```text
P2 phase 1 readiness/schema/governance only; physical solver execution blocked
```

This P2 phase does not change the P0 release conclusion. P0 remains a
no-measured-data relative audit package, not a calibrated physical prediction
package.

This P2 phase also preserves the P1 role:

```text
P1 physical-ceiling extensions = surrogate_risk_reduction_only
```

P2 does not convert P1 or P2 sidecars into calibration.

## 1. Boundary

P2 phase 1 has one role:

```text
bounded_solver_readiness_only
```

It defines the schema, governance, manifest, and verifier needed before any
future bounded solver lane could be separately authorized. It does not execute
a full-wave solver, Green-tensor solver, vector solver, Jones sweep, roughness
or leakage perturbation, transport perturbation, residence-time perturbation,
or measured-data ingest.

Required top-level declarations:

| field | value |
|---|---|
| `calibrated_claim_allowed` | `false` |
| `p0_release_conclusion_changed` | `false` |
| `p1_surrogate_risk_role_preserved` | `true` |
| `physical_solver_execution_authorized` | `false` |
| `measured_data_ingest_authorized` | `false` |

Calibrated SNR claims remain blocked. Absolute LOD claims remain blocked. True
EV concentration claims remain blocked. Biological specificity claims remain
blocked. Detector-voltage prediction claims remain blocked. Sample-count claims
remain blocked. Measured blank-safety claims remain blocked. Route-promotion
claims remain blocked.

## 2. Phase-1 Artifacts

Create and verify:

```text
configs/realism_v2/bounded_physical_solver_readiness_registry.yaml
reports/98_EV_NODI_P2_bounded_physical_solver_readiness_plan.md
results/post_v2_bounded_physical_solver_readiness/bounded_physical_solver_readiness_schema_manifest.json
results/post_v2_bounded_physical_solver_readiness/bounded_physical_solver_readiness_artifact_manifest.json
results/post_v2_bounded_physical_solver_readiness/README.md
tools/verify_post_v2_bounded_physical_solver_readiness.py
```

These are readiness artifacts only. They do not contain solver outputs, new
case generation, measured data, detector-unit predictions, route promotions, or
calibration evidence.

## 3. Cross-Lane Governance

All four P2 readiness lanes preserve the P0/P1 boundary:

| rule | required behavior |
|---|---|
| P0 release | Do not change P0 conclusions or reinterpret P0 as calibration. |
| P1 role | Preserve P1 as generated no-solver surrogate-risk diagnostics. |
| P2 role | Define readiness contracts only; do not execute heavy solvers. |
| Final gates | Keep final interpretability limited to rank, rank-percentile, and pairwise inversion families. |
| Raw magnitude | Keep arbitrary-unit or solver-native raw magnitudes trace-only and not final gates. |
| Optional 660 | Keep `optional_660_W900_D1400` optional; it does not redefine main-660. |
| Jacobian layers | Keep `v1_bfp_to_angle_jacobian_applied = false` and `audit_bfp_jacobian_applied = true` distinct. |
| P1 raw proxies | Keep `raw_*_diagnostic_only` proxy columns as non-physical diagnostic blends. |
| P1 Jones lane | Treat Jones as governance-distinct, not independent vector physical evidence. |

## 4. Lane Contracts

### 4.1 Full-Wave / Green-Tensor Spot-Check Readiness

Claim boundary:

```text
readiness only; no solver execution; no calibration; no P0 conclusion change
```

The readiness contract defines future preflight requirements for bounded route
universe selection, solver configuration manifests, mesh or operator manifest
hashes, unit registry binding, and rank/pairwise interpretability. It blocks
raw complex field values as final gates.

### 4.2 Vector / Jones Basis Sweep Readiness

Claim boundary:

```text
readiness only; no vector solver execution; no biological specificity claim
```

The readiness contract defines future preflight requirements for basis
versioning, normalization conventions, vector operator export manifests, and
rank/pairwise interpretability. It preserves the P1 Jones lane as
governance-distinct and not independent vector physical evidence.

### 4.3 Roughness / Leakage Perturbation Readiness

Claim boundary:

```text
readiness only; no perturbation execution; no measured blank-safety claim
```

The readiness contract defines future preflight requirements for bounded
roughness/leakage parameter ranges, artifact-gap escalation mapping, and
rank/pairwise interpretability. Blank-trace ingest remains blocked.

### 4.4 Transport / Residence-Time Perturbation Readiness

Claim boundary:

```text
readiness only; no transport execution; no true EV concentration or sample-count claim
```

The readiness contract defines future preflight requirements for bounded
transport ranges, residence-time interpretation manifests, and rank/pairwise
interpretability. Residence-time quantities remain blocked from concentration
or sample-count interpretation.

## 5. Verifier

The P2 verifier must fail closed when any artifact or lane declares:

```text
calibrated_claim_allowed = true
p0_release_conclusion_changed = true
p1_surrogate_risk_role_preserved = false
physical_solver_execution_authorized = true
measured_data_ingest_authorized = true
raw_magnitude_final_gate_allowed = true
```

It must also fail when any lane authorizes calibrated SNR, absolute LOD, true
EV concentration, biological specificity, detector-voltage prediction,
sample-count, measured blank-safety, or route-promotion claims.

## 6. Stop Rule

P2 phase 1 stops after readiness schema, registry, manifests, verifier, and
tests pass. It does not proceed into heavy solver implementation.
