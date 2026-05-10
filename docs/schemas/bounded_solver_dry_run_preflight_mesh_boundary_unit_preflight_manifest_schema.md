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
new_mesh_generation_authorized = false
operator_export_generation_authorized = false
physical_solver_execution_authorized = false
solver_output_generated = false
```

The Jacobian layer distinction remains pinned:

```text
v1_bfp_to_angle_jacobian_applied = false
audit_bfp_jacobian_applied = true
```
