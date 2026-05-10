# EV/NODI P4 Bounded Solver Dry-Run Preflight Plan

Date: 2026-05-10

Status:

```text
P4 dry-run preflight complete; solver execution remains blocked
```

P4 instantiates the P3 minimal pilot design as dry-run manifests only. It does
not change the P0 release conclusion. P0 remains a no-measured-data relative
audit package, not a calibrated physical prediction package.

P4 preserves the P1 surrogate-risk role, the P2 readiness scope, and the P3
pilot-design scope:

```text
P1 = surrogate_risk_reduction_only
P2 = bounded route-universe future preflight scope only
P3 = authorization planning and minimal pilot design only
```

## 1. Boundary

P4 has one role:

```text
bounded_solver_dry_run_preflight_only
```

Required declarations:

| field | value |
|---|---|
| `calibrated_claim_allowed` | `false` |
| `p0_release_conclusion_changed` | `false` |
| `p1_surrogate_risk_role_preserved` | `true` |
| `p2_readiness_scope_preserved` | `true` |
| `p3_pilot_design_scope_preserved` | `true` |
| `physical_solver_execution_authorized` | `false` |
| `measured_data_ingest_authorized` | `false` |
| `calibration_data_ingest_authorized` | `false` |
| `new_mesh_generation_authorized` | `false` |
| `operator_export_generation_authorized` | `false` |
| `solver_output_generated` | `false` |
| `route_promotion_authorized` | `false` |

SNR and LOD claims remain blocked. Calibrated SNR, absolute LOD, true EV
concentration, biological specificity, detector-voltage prediction,
sample-count, measured blank-safety, and route-promotion claims remain blocked.

## 2. Single Dry-Run Lane

P4 defines one lane:

```text
full_wave_green_tensor_spot_check_dry_run_preflight
```

The lane binds the P3 lane:

```text
full_wave_green_tensor_spot_check_minimal_pilot_design
```

It generates dry-run manifests for:

```text
P3 binding
solver input manifest
mesh / boundary / unit preflight manifest
execution authorization record
artifact manifest
```

These are not solver inputs consumed by a runtime. They are reviewable preflight
records that prove the future input shape, unit declarations, mesh status, and
authorization decision are still bounded before any execution.

## 3. Generated Artifacts

P4 creates:

```text
configs/realism_v2/bounded_solver_dry_run_preflight_registry.yaml
reports/101_EV_NODI_P4_bounded_solver_dry_run_preflight_plan.md
results/post_v2_bounded_solver_dry_run_preflight/bounded_solver_dry_run_preflight_p3_binding_manifest.json
results/post_v2_bounded_solver_dry_run_preflight/full_wave_green_tensor_minimal_pilot_input_manifest.json
results/post_v2_bounded_solver_dry_run_preflight/full_wave_green_tensor_mesh_boundary_unit_preflight_manifest.json
results/post_v2_bounded_solver_dry_run_preflight/full_wave_green_tensor_execution_authorization_record.json
results/post_v2_bounded_solver_dry_run_preflight/bounded_solver_dry_run_preflight_artifact_manifest.json
results/post_v2_bounded_solver_dry_run_preflight/README.md
tools/verify_post_v2_bounded_solver_dry_run_preflight.py
```

The mesh preflight manifest must declare:

```text
mesh_manifest_path = null
mesh_manifest_sha256 = null
mesh_manifest_status = not_generated_no_mesh_generation
```

The execution authorization record must declare:

```text
execution_authorization_decision = not_authorized_phase4_dry_run_only
explicit_later_phase_required = true
```

## 4. Interpretability

Any later execution would still need rank, rank-percentile, or pairwise
interpretability before any gate could be considered. Raw arbitrary-unit
magnitude and solver-native raw magnitude remain trace-only and cannot be final
gates.

## 5. Verifier

The P4 verifier must fail closed if any artifact declares:

```text
calibrated_claim_allowed = true
p0_release_conclusion_changed = true
p1_surrogate_risk_role_preserved = false
p2_readiness_scope_preserved = false
p3_pilot_design_scope_preserved = false
physical_solver_execution_authorized = true
measured_data_ingest_authorized = true
calibration_data_ingest_authorized = true
new_mesh_generation_authorized = true
operator_export_generation_authorized = true
solver_output_generated = true
route_promotion_authorized = true
raw_arbitrary_unit_magnitude_final_gate_allowed = true
solver_native_raw_magnitude_final_gate_allowed = true
```

It must also fail if the P3 route subset or schema binding drifts, if selected
routes are not the P3 subset, if a mesh manifest appears, or if the execution
authorization record allows execution.

## 6. Stop Rule

P4 stops after dry-run preflight manifests, verifier, and tests pass. It does
not proceed into solver execution, mesh generation, operator export, measured
ingest, calibration ingest, solver-output generation, or route promotion.
