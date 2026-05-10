# EV/NODI P1 Physical-Ceiling Extensions Plan

Date: 2026-05-10

Status:

```text
P1 no-solver rank diagnostics complete; all four lane contracts and generated diagnostics remain non-calibrated
```

This document opens a P1 branch of work for physical-ceiling diagnostics. It
does not change the P0 release conclusion. P0 remains a no-measured-data
relative audit package, not a calibrated physical prediction package.

## 1. Boundary

P1 physical-ceiling extensions have one role:

```text
surrogate_risk_reduction_only
```

They may register diagnostics that ask whether existing scalar or sidecar
surrogates are fragile under better physical ceilings. They may not authorize
calibrated claims, absolute claims, biological claims, concentration claims,
or detector-unit predictions.

Required top-level declarations:

| field | value |
|---|---|
| `calibrated_claim_allowed` | `false` |
| `p0_release_conclusion_changed` | `false` |
| `physical_ceiling_role` | `surrogate_risk_reduction_only` |

SNR claims remain blocked. LOD claims remain blocked. EV concentration claims
remain blocked. Biological specificity claims remain blocked. Detector-voltage
prediction claims remain blocked.

## 2. Phase-1 Scope

Initial phase created planning, schema, and risk-register artifacts:

```text
configs/realism_v2/physical_ceiling_extension_registry.yaml
reports/92_EV_NODI_P1_physical_ceiling_extensions_plan.md
```

This P1 package does not run a full-wave solver, does not run a vector solver, does not
run roughness/leakage simulations, and does not run transport simulations. It
also does not expand v1 event counts.

## 3. Cross-Lane Governance

All four lanes must preserve the P0 evidence boundary:

| rule | required behavior |
|---|---|
| P0 release | Do not change P0 conclusions or reinterpret P0 as calibration. |
| P1 role | Use P1 only to lower surrogate risk and register physical-ceiling diagnostics. |
| Final gates | Use rank, rank-percentile, and pairwise inversion. |
| Raw magnitude | Keep arbitrary-unit magnitudes diagnostic-only, never a final gate. |
| Optional 660 | Keep `optional_660_W900_D1400` optional; it does not redefine main-660. |
| Jacobian layers | Keep `v1_bfp_to_angle_jacobian_applied = false` and `audit_bfp_jacobian_applied = true` distinct. |

## 4. Artifact Manifest Schema

The P1 registry defines the planned manifest schema:

```text
ev_nodi_physical_ceiling_p1_artifact_manifest_v1
```

Required artifact fields:

```text
artifact_id
lane_id
artifact_role
path
status
claim_level
calibrated_claim_allowed
p0_release_conclusion_changed
physical_ceiling_role
rank_evidence_required
raw_magnitude_final_gate_allowed
```

Every P1 artifact must declare:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
physical_ceiling_role = surrogate_risk_reduction_only
raw_magnitude_final_gate_allowed = false
```

## 5. Independent P1 Lanes

### 5.1 Full-Wave / Green-Tensor Physical-Ceiling Diagnostic

Claim boundary:

```text
diagnostic only; no calibration; no P0 conclusion change
```

Inputs:

- P0 route keys and comparison strata.
- P0 rank-percentile and pairwise inversion evidence.
- BFP ROI audit sidecar metadata.
- Future bounded Green-tensor solver configuration, only if separately authorized.

Outputs:

- Planned rank-shift diagnostic by route.
- Planned scalar-vs-full-wave disagreement flags.
- Planned operator-limit notes without detector calibration.

Required tests:

- Manifest declares `calibrated_claim_allowed = false`.
- Outputs use rank or rank-percentile as gates.
- Arbitrary-unit magnitudes remain diagnostic-only.
- P0 release conclusion remains unchanged.

### 5.2 Vector / Jones Polarization Diagnostic

Claim boundary:

```text
diagnostic only; no calibration; no biological specificity claim
```

Inputs:

- P0 candidate route list.
- Existing polarization/Jones operator boundary.
- BFP Jacobian audit provenance.
- Future bounded vector basis sweep, only if separately authorized.

Outputs:

- Planned polarization sensitivity rank deltas.
- Planned Jones-basis operator-risk flags.
- Planned lane uncertainty notes without specificity claims.

Required tests:

- Jones diagnostics cannot replace P0 route decisions.
- Specificity and concentration claims remain blocked.
- `audit_bfp_jacobian_applied` remains distinct from `v1_bfp_to_angle_jacobian_applied`.

### 5.3 Roughness / Leakage Diagnostic

Claim boundary:

```text
diagnostic only; no calibration; no measured blank-safety claim
```

Inputs:

- P0 route geometry keys.
- R7 artifact gap concepts for fabrication and BFP alignment.
- Future bounded roughness/leakage perturbation grid, only if separately authorized.

Outputs:

- Planned leakage vulnerability rank flags.
- Planned roughness sensitivity bins.
- Planned artifact-gap escalation notes.

Required tests:

- Roughness/leakage outputs cannot claim blank safety.
- Final gates remain rank-percentile or pairwise-inversion based.
- P1 diagnostics stay outside P0 release conclusions.

### 5.4 Transport / Residence-Time Diagnostic

Claim boundary:

```text
diagnostic only; no calibration; no true EV concentration claim
```

Inputs:

- P0 EV/sample and coincidence relative proxies.
- Existing electrokinetic and fluidic model boundaries.
- Future bounded residence-time perturbation grid, only if separately authorized.

Outputs:

- Planned residence-time fragility rank flags.
- Planned transport-risk register rows.
- Planned proxy-adequacy notes without concentration claims.

Required tests:

- Transport outputs do not expand v1 event counts.
- Transport outputs cannot claim true EV concentration.
- Coincidence and residence-time quantities remain relative diagnostics.

## 6. Risk Register

| risk | mitigation |
|---|---|
| Physical-ceiling language may drift into calibration language. | Every lane and artifact declares `calibrated_claim_allowed = false`. |
| Arbitrary-unit magnitudes may leak into final decisions. | Final gates are restricted to rank, rank-percentile, and pairwise inversion. |
| `optional_660_W900_D1400` may be mistaken for main-660. | Registry explicitly states it does not redefine main-660. |
| Jacobian flags may be conflated across layers. | Registry pins the v1 source-library flag and the audit-sidecar flag separately. |

## 7. Stop Rule

P1 now completes the bounded no-solver rank-diagnostic package. It still does not proceed into heavy full-wave, vector, roughness, or transport solver implementation.

## 8. Continuation Notes

The first authorized continuation adds only the full-wave / Green-tensor lane
contract:

```text
configs/realism_v2/full_wave_green_tensor_diagnostic_contract.yaml
reports/93_EV_NODI_P1_full_wave_green_tensor_diagnostic_contract.md
```

That contract is still schema-only. It does not execute a solver, generate a
mesh, ingest measured data, promote routes, redefine main-660, expand v1 event
counts, or use raw arbitrary-unit magnitudes as final gates.

The second authorized continuation adds only the vector / Jones polarization
lane contract:

```text
configs/realism_v2/vector_jones_polarization_diagnostic_contract.yaml
reports/94_EV_NODI_P1_vector_jones_polarization_diagnostic_contract.md
```

That contract is also schema-only. It does not execute a vector solver, generate
a Jones-basis sweep, ingest measured data, promote routes, redefine main-660,
expand v1 event counts, use raw Jones amplitudes as final gates, or support
biological specificity claims.

The third authorized continuation adds only the roughness / leakage diagnostic
lane contract:

```text
configs/realism_v2/roughness_leakage_diagnostic_contract.yaml
reports/95_EV_NODI_P1_roughness_leakage_diagnostic_contract.md
```

That contract is also schema-only. It does not run roughness simulations, run
leakage simulations, ingest blank traces, promote routes, redefine main-660,
expand v1 event counts, use raw leakage amplitudes as final gates, or support
measured blank-safety claims.

The fourth authorized continuation adds only the transport / residence-time
diagnostic lane contract:

```text
configs/realism_v2/transport_residence_time_diagnostic_contract.yaml
reports/96_EV_NODI_P1_transport_residence_time_diagnostic_contract.md
```

That contract is also schema-only. It does not run transport simulations, run
residence-time simulations, ingest measured concentration or sample-count data,
promote routes, redefine main-660, expand v1 event counts, use raw
residence-time proxies as final gates, or support true EV concentration,
sample-count, or absolute event-probability claims.

The completed continuation emits cross-lane manifests and generated no-solver rank diagnostics:

```text
results/post_v2_physical_ceiling/physical_ceiling_contract_manifest.json
results/post_v2_physical_ceiling/physical_ceiling_diagnostic_schema_manifest.json
results/post_v2_physical_ceiling/physical_ceiling_input_binding_manifest.json
results/post_v2_physical_ceiling/physical_ceiling_route_coverage_manifest.json
```

Those manifests record the four contract files, their hashes, their planned
diagnostic output schemas, their required P0 source-field bindings, their
P0 route coverage, their planned diagnostic output paths, and the fact that
those output paths are generated as no-solver rank diagnostics. They are diagnostic tables, but they do not
change P0 package conclusions.

The verification-only continuation adds:

```text
tools/verify_post_v2_physical_ceiling_contracts.py
```

That verifier reads the P1 contracts, manifests, and README; it does not write
new diagnostic outputs. It fails if any generated diagnostic CSV is stale, if either
manifest is stale, or if claim-boundary fields drift.

The schema-documentation continuation adds:

```text
docs/schemas/physical_ceiling_contract_manifest_schema.md
docs/schemas/physical_ceiling_diagnostic_schema_manifest_schema.md
docs/schemas/physical_ceiling_input_binding_manifest_schema.md
```

These docs describe the P1 manifest schemas and repeat the empty-output,
no-calibration, no-P0-change boundary.
