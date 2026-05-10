# EV/NODI P5 Bounded Solver Authorization Gate Plan

Date: 2026-05-10

Status:

```text
P5 authorization gate complete; solver execution remains blocked
```

P5 binds the P4 dry-run preflight package and creates an authorization gate
record. It does not authorize execution. P0 remains a no-measured-data relative
audit package, not a calibrated physical prediction package.

## Boundary

P5 has one role:

```text
bounded_solver_authorization_gate_only
```

Required declarations:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
p1_surrogate_risk_role_preserved = true
p2_readiness_scope_preserved = true
p3_pilot_design_scope_preserved = true
p4_dry_run_preflight_scope_preserved = true
physical_solver_execution_authorized = false
measured_data_ingest_authorized = false
calibration_data_ingest_authorized = false
new_mesh_generation_authorized = false
operator_export_generation_authorized = false
solver_output_generated = false
route_promotion_authorized = false
```

SNR and LOD claims remain blocked. Calibrated SNR, absolute LOD, true EV
concentration, biological specificity, detector-voltage prediction,
sample-count, measured blank-safety, and route-promotion claims remain blocked.

## Gate Decision

The P5 gate record must declare:

```text
authorization_gate_decision = not_authorized_pending_explicit_later_phase_execution_request
explicit_solver_execution_request_required = true
required_next_authorization_phrase = authorize minimal bounded solver execution
```

The phrase is a future guardrail. It documents the minimum clarity needed before
a later phase may change execution authorization. P5 itself does not perform
that change.

## Artifacts

P5 creates:

```text
configs/realism_v2/bounded_solver_authorization_gate_registry.yaml
reports/102_EV_NODI_P5_bounded_solver_authorization_gate_plan.md
results/post_v2_bounded_solver_authorization_gate/bounded_solver_authorization_gate_p4_binding_manifest.json
results/post_v2_bounded_solver_authorization_gate/bounded_solver_authorization_gate_record.json
results/post_v2_bounded_solver_authorization_gate/bounded_solver_authorization_gate_artifact_manifest.json
results/post_v2_bounded_solver_authorization_gate/README.md
tools/verify_post_v2_bounded_solver_authorization_gate.py
```

## Stop Rule

P5 stops after the gate artifacts, verifier, and tests pass. It does not
proceed into solver execution, mesh generation, operator export, measured
ingest, calibration ingest, solver-output generation, or route promotion.
