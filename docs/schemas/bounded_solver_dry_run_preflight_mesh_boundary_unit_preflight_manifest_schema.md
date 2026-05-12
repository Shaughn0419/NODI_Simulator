# Bounded Solver Dry-Run Mesh Boundary Unit Preflight Manifest

Schema:

```text
ev_nodi_p4_full_wave_green_tensor_mesh_boundary_unit_preflight_manifest_v1
```

Role:

```text
mesh_boundary_unit_preflight_no_mesh_generation
```

Required mesh non-generation declarations:

```text
mesh_manifest_path = null
mesh_manifest_sha256 = null
mesh_manifest_status = not_generated_no_mesh_generation
calibrated_claim_allowed = false
new_mesh_generation_authorized = false
operator_export_generation_authorized = false
physical_solver_execution_authorized = false
measured_data_ingest_authorized = false
calibration_data_ingest_authorized = false
solver_output_generated = false
route_promotion_authorized = false
```

The Jacobian layer distinction remains pinned:

```text
v1_bfp_to_angle_jacobian_applied = false
audit_bfp_jacobian_applied = true
```

## Artifact Field Coverage

Fields below are tracked by the schema-doc drift auditor for matched artifact files.

### `results/post_v2_bounded_solver_dry_run_preflight/full_wave_green_tensor_mesh_boundary_unit_preflight_manifest.json`

- `boundary_condition_family`
- `coordinate_system`
- `length_unit`
- `material_index_unit_convention`
- `normalization_convention`
- `p0_release_conclusion_changed`
- `p1_surrogate_risk_role_preserved`
- `p2_readiness_scope_preserved`
- `p3_pilot_design_scope_preserved`
- `unit_registry_binding`
- `wavelength_unit`
