# EV/NODI P6 Minimal Bounded Solver Execution Plan

P6 records the first authorized minimal bounded solver execution after the P5 gate phrase was provided: `authorize minimal bounded solver execution`.

The execution is intentionally narrow. It binds the P5 authorization gate and P4 dry-run preflight chain, runs only the deterministic `deterministic_minimal_green_kernel_v1` spot-check for the three P4 selected routes, and writes one trace-only output CSV plus manifests.

## Scope

- Lane: `full_wave_green_tensor_minimal_bounded_execution`
- Solver runtime: `deterministic_minimal_green_kernel_v1`
- Route scope: the three routes selected by the P4 input manifest
- Output: rank, rank percentile, pairwise order signature, and solver-native trace fields
- Final interpretability: rank, rank-percentile, and pairwise order only

## Boundaries

- `calibrated_claim_allowed = false`
- `p0_release_conclusion_changed = false`
- `p1_surrogate_risk_role_preserved = true`
- `p2_readiness_scope_preserved = true`
- `p3_pilot_design_scope_preserved = true`
- `p4_dry_run_preflight_scope_preserved = true`
- `p5_authorization_gate_scope_preserved = true`
- `physical_solver_execution_authorized = true`
- `minimal_bounded_solver_execution_authorized = true`
- `green_tensor_minimal_solver_execution_authorized = true`
- `solver_output_generated = true`
- `measured_data_ingest_authorized = false`
- `calibration_data_ingest_authorized = false`
- `new_mesh_generation_authorized = false`
- `operator_export_generation_authorized = false`
- `full_wave_solver_execution_authorized = false`
- `route_promotion_authorized = false`
- `raw_magnitude_final_gate_allowed = false`
- `solver_native_raw_magnitude_final_gate_allowed = false`

SNR and LOD claims remain blocked. True EV concentration, biological specificity, detector-voltage, sample-count, measured blank safety, absolute event probability, and route-promotion claims remain blocked.

## Artifacts

- `configs/realism_v2/minimal_bounded_solver_execution_registry.yaml`
- `results/post_v2_minimal_bounded_solver_execution/minimal_bounded_solver_execution_p5_binding_manifest.json`
- `results/post_v2_minimal_bounded_solver_execution/full_wave_green_tensor_minimal_solver_output.csv`
- `results/post_v2_minimal_bounded_solver_execution/full_wave_green_tensor_minimal_solver_output_manifest.json`
- `results/post_v2_minimal_bounded_solver_execution/minimal_bounded_solver_execution_artifact_manifest.json`
- `results/post_v2_minimal_bounded_solver_execution/README.md`
- `docs/schemas/minimal_bounded_solver_execution_p5_binding_manifest_schema.md`
- `docs/schemas/minimal_bounded_solver_execution_output_manifest_schema.md`
- `docs/schemas/minimal_bounded_solver_execution_artifact_manifest_schema.md`

## Stop Rule

P6 stops after the minimal bounded execution output and verifier pass. It does not authorize mesh generation, operator export, measured-data ingest, calibration-data ingest, full-wave/vector/roughness/transport execution, route promotion, or calibrated prediction.
