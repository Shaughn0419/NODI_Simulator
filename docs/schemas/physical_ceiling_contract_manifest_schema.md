# Physical-Ceiling Contract Manifest Schema

Schema id:

```text
ev_nodi_p1_physical_ceiling_contract_manifest_v1
```

Role:

```text
contract_registry_and_generated_no_solver_output_guard
```

This P1 manifest records the four physical-ceiling lane contracts and confirms
that the generated diagnostic outputs exist as no-solver rank diagnostics. It
is not a calibrated physical prediction table and does not change the P0
release conclusion.

Required top-level guard fields:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
physical_ceiling_role = surrogate_risk_reduction_only
diagnostic_outputs_generated = true
solver_or_simulation_execution_authorized = false
```

Required contract-row guard fields:

```text
planned_output_exists = true
artifact_status = generated_no_solver_rank_diagnostic
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
physical_ceiling_role = surrogate_risk_reduction_only
raw_magnitude_final_gate_allowed = false
decision_authority = diagnostic_flag_only_no_route_promotion
```

The `raw_*_diagnostic_only` columns in the generated CSVs are rank-percentile,
relative-stability, or normalized-geometry blends. They are not physical field,
Jones-amplitude, leakage-amplitude, residence-time, detector-voltage, SNR, LOD,
EV-concentration, or biological-specificity quantities.

Forbidden interpretations remain blocked: calibrated SNR, absolute LOD, true
EV concentration, biological specificity, detector-voltage prediction, sample
count, measured blank-safety, route promotion, and absolute event probability.
