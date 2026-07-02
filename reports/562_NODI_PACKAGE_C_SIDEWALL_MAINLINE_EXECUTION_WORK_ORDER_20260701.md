# NODI Package C Sidewall Mainline Execution Work Order

- Disposition: `NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_WORK_ORDER_READY_LARGE_BLOCKS_PRIORITIZED`.
- Current head: `37798f73cbbf92135f8e66b01fede69eb6ee0c22` on `main`.
- Geometry scope: `ideal_rectangle;trapezoid_tapered_sidewalls`.
- Work orders: `8`; claim guards: `7`.
- Route evidence register rows: `10`.
- Authorized implementation rows: `8`.
- Current claim activation rows: `0`.
- Accepted detector/wet evidence: `0` / `0`.

## Ordered Work

- `WO-001-current-head-source-lock` `source_lock_and_commit_binding` -> `current_head_source_lock_receipt`; blocker: downstream evidence packets must be regenerated from current reviewed head before claim activation.
- `WO-002-comsol-target-binding` `comsol_target_model_and_command_binding` -> `comsol_target_binding_and_dry_run_receipt`; blocker: target model/script and launch command hash are not bound.
- `WO-003-electrokinetic-profile-grid` `electrokinetic_profile_aware_grid` -> `electrokinetic_profile_grid_candidate_packet`; blocker: profile-aware grid implementation and rectangle/theta mutation tests are absent.
- `WO-004-detector-blank-transfer` `detector_blank_transfer_evidence` -> `detector_blank_transfer_accepted_evidence_packet`; blocker: accepted sidewall-specific or validated-transfer detector/blank rows are absent.
- `WO-005-wet-observation` `wet_observation_evidence` -> `wet_observation_accepted_evidence_packet`; blocker: accepted wet observation rows with controls and uncertainty are absent.
- `WO-006-route-yield-detection-formula-binding` `route_yield_detection_formula_binding` -> `route_yield_detection_formula_binding_candidate`; blocker: detector/blank and wet accepted evidence are both required before formula binding.
- `WO-007-runtime-substep-policy` `reflection_runtime_substep_policy` -> `reflection_runtime_substep_policy_packet`; blocker: runtime substep/fail policy is not yet bound to large-step and near-closed guards.
- `WO-008-mainline-integration-closeout` `mainline_integration_and_release_closeout` -> `sidewall_package_c_integrated_execution_closeout`; blocker: branch evidence is distributed across packets and needs a single promotion ledger after inputs pass.

This packet treats solver, wet, route, yield, and detection work as authorized implementation lanes. Claim activation remains evidence-gated: missing detector/blank and wet rows are execution inputs to collect, not reasons to stop the mainline.
