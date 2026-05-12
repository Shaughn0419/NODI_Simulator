# Bounded Solver Dry-Run Preflight Input Manifest

Schema:

```text
ev_nodi_p4_full_wave_green_tensor_minimal_pilot_input_manifest_v1
```

Role:

```text
dry_run_solver_input_manifest_no_execution
```

The manifest binds the P3 route subset, selected route IDs, unit declarations,
and the P4 mesh preflight plus execution authorization record paths. It is not
runtime solver input.

Required declarations:

```text
calibrated_claim_allowed = false
physical_solver_execution_authorized = false
measured_data_ingest_authorized = false
calibration_data_ingest_authorized = false
new_mesh_generation_authorized = false
operator_export_generation_authorized = false
solver_output_generated = false
route_promotion_authorized = false
```

## Artifact Field Coverage

Fields below are tracked by the schema-doc drift auditor for matched artifact files.

### `results/post_v2_bounded_solver_dry_run_preflight/full_wave_green_tensor_minimal_pilot_input_manifest.json`

- `allowed_interpretability_families`
- `geometry_source_binding`
- `p0_release_conclusion_changed`
- `p1_surrogate_risk_role_preserved`
- `p2_readiness_scope_preserved`
- `p3_pilot_design_scope_preserved`
- `p3_route_subset_manifest_sha256`
- `rank_pairwise_interpretability_declared`
- `raw_arbitrary_unit_magnitude_final_gate_allowed`
- `selected_route_ids`
- `selected_routes`
- `solver_native_raw_magnitude_final_gate_allowed`
- `unit_registry_binding`
- `wavelength_nm_source`
