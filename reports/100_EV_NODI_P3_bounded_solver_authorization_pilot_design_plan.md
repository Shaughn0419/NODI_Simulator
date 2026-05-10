# EV/NODI P3 Bounded Solver Authorization and Minimal Pilot Design Plan

Date: 2026-05-10

Status:

```text
P3 phase 1 authorization planning and minimal pilot design only; solver execution remains blocked
```

This P3 work does not change the P0 release conclusion. P0 remains a
no-measured-data relative audit package, not a calibrated physical prediction
package.

This P3 work preserves the P1 role:

```text
P1 physical-ceiling extensions = surrogate_risk_reduction_only
```

This P3 work also preserves the P2 role:

```text
P2 bounded route-universe manifest = future solver preflight scope only
```

P3 phase 1 does not convert P1, P2, or P3 sidecars into calibration.

## 1. Boundary

P3 phase 1 has one role:

```text
bounded_solver_authorization_pilot_design_only
```

Required top-level declarations:

| field | value |
|---|---|
| `calibrated_claim_allowed` | `false` |
| `p0_release_conclusion_changed` | `false` |
| `p1_surrogate_risk_role_preserved` | `true` |
| `p2_readiness_scope_preserved` | `true` |
| `physical_solver_execution_authorized` | `false` |
| `measured_data_ingest_authorized` | `false` |
| `solver_output_generated` | `false` |

Calibrated SNR claims remain blocked. Absolute LOD claims remain blocked. True
EV concentration claims remain blocked. Biological specificity claims remain
blocked. Detector-voltage prediction claims remain blocked. Sample-count claims
remain blocked. Measured blank-safety claims remain blocked. Route-promotion
claims remain blocked.

## 2. Single Phase-1 Lane

P3 phase 1 defines exactly one minimal pilot-design lane:

```text
full_wave_green_tensor_spot_check_minimal_pilot_design
```

This lane defines future authorization and preflight contracts only. It does
not run a full-wave solver, Green-tensor solver, vector solver, roughness or
leakage perturbation, transport perturbation, residence-time perturbation,
calibration-data ingest, measured-data ingest, mesh generation, operator export,
or solver output generation.

Any later solver execution would need a separate later-phase authorization.

## 3. Binding to P2 Route Universe

The pilot design binds only this P2 manifest:

```text
results/post_v2_bounded_physical_solver_readiness/bounded_physical_solver_readiness_route_universe_manifest.json
```

The P2 route-universe manifest is treated as future preflight scope, not solver
result evidence and not route-promotion evidence.

The phase-1 route subset rule is deterministic:

1. Select up to two `relative_main_candidate` rows sorted by `route_key`, then
   `candidate_id`.
2. Select one additional row with
   `full_wave_green_tensor_pairwise_inversion_flag = true`, excluding already
   selected routes, sorted by `route_key`, then `candidate_id`.

The selected subset may only carry P2 route identifiers, route roles,
comparison strata, P0 audit decision fields, P1 full-wave surrogate-risk labels,
and pairwise flags. Raw proxy fields are excluded. The optional
`optional_660_W900_D1400` route does not redefine main-660.

## 4. Pilot Schemas

The registry defines future schemas for:

```text
solver input manifest
mesh / boundary / unit preflight manifest
output schema placeholder
```

The solver input manifest schema must bind the P2 route-universe manifest path
and hash, list selected route IDs, declare units and source lineage, and record
that `physical_solver_execution_authorized = false`,
`measured_data_ingest_authorized = false`, and `solver_output_generated =
false` in phase 1.

The mesh / boundary / unit preflight schema is a future contract only. It does
not authorize mesh generation. It preserves the Jacobian layering rule:
`v1_bfp_to_angle_jacobian_applied = false` and
`audit_bfp_jacobian_applied = true`.

The output schema placeholder is not solver output. It only records that any
later output would have to be interpretable through rank, rank-percentile, or
pairwise-inversion families before any gate could be considered. Raw
arbitrary-unit magnitude and solver-native raw magnitude remain trace-only and
are not final gates.

## 5. Generated Artifacts

P3 phase 1 creates and verifies:

```text
configs/realism_v2/bounded_solver_authorization_pilot_design_registry.yaml
reports/100_EV_NODI_P3_bounded_solver_authorization_pilot_design_plan.md
results/post_v2_bounded_solver_authorization_pilot_design/bounded_solver_authorization_pilot_design_p2_route_binding_manifest.json
results/post_v2_bounded_solver_authorization_pilot_design/bounded_solver_authorization_pilot_design_route_subset_manifest.json
results/post_v2_bounded_solver_authorization_pilot_design/bounded_solver_authorization_pilot_design_schema_manifest.json
results/post_v2_bounded_solver_authorization_pilot_design/bounded_solver_authorization_pilot_design_artifact_manifest.json
results/post_v2_bounded_solver_authorization_pilot_design/README.md
tools/verify_post_v2_bounded_solver_authorization_pilot_design.py
```

These artifacts are authorization planning, schema, and governance artifacts
only. They do not contain solver outputs, measured data, calibration data,
detector-unit predictions, route promotions, or physical field quantities.

## 6. Verifier

The P3 verifier must fail closed when any artifact or lane declares:

```text
calibrated_claim_allowed = true
p0_release_conclusion_changed = true
p1_surrogate_risk_role_preserved = false
p2_readiness_scope_preserved = false
physical_solver_execution_authorized = true
measured_data_ingest_authorized = true
solver_output_generated = true
raw_magnitude_final_gate_allowed = true
route_promotion_authorized = true
```

It must also fail when the pilot design does not reference the P2
route-universe manifest, when the output schema placeholder implies calibrated
physical prediction, or when raw magnitude is declared as a final gate.

## 7. Stop Rule

P3 phase 1 stops after the authorization plan, registry, manifests, verifier,
and tests pass. It does not proceed into full-wave, vector, roughness,
transport, measured-data, calibration, or route-promotion execution.
