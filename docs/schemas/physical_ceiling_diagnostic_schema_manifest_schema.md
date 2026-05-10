# Physical-Ceiling Diagnostic Schema Manifest Schema

Schema id:

```text
ev_nodi_p1_physical_ceiling_diagnostic_schema_manifest_v1
```

Role:

```text
generated_output_schema_registry_and_no_solver_guard
```

This P1 manifest records the generated no-solver output schemas for the four
physical-ceiling diagnostic CSVs. Those CSVs are rank-based surrogate-risk
diagnostics only; they do not contain calibrated solver, measured-data, or
detector-unit results.

Required top-level guard fields:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
physical_ceiling_role = surrogate_risk_reduction_only
diagnostic_outputs_generated = true
solver_or_simulation_execution_authorized = false
```

Each schema row must include:

```text
lane_id
contract_path
planned_output_path
planned_output_exists = true
artifact_status = generated_no_solver_rank_diagnostic
required_columns
required_false_columns
required_role_column_value = surrogate_risk_reduction_only
primary_gate_metrics
raw_magnitude_final_gate_allowed = false
decision_authority = diagnostic_flag_only_no_route_promotion
```

Allowed gate families are rank-percentile and pairwise-inversion diagnostics
only. Raw arbitrary-unit or normalized proxy fields may be diagnostic traces,
not final gates. In P1, the Jones lane reuses the BFP ROI Jacobian-audit proxy
without a vector solver and therefore must not be cited as independent vector
physical evidence.
