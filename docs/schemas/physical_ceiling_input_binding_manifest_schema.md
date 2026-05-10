# Physical-Ceiling Input Binding Manifest Schema

Schema id:

```text
ev_nodi_p1_physical_ceiling_input_binding_manifest_v1
```

Role:

```text
p0_source_binding_registry_and_empty_output_guard
```

This P1 manifest checks that each physical-ceiling lane contract binds to
existing P0 source files and required source fields. It records source hashes
and row counts for review traceability.

It does not compute diagnostic scores, does not generate diagnostic CSVs, and
does not change the P0 release conclusion.

Required top-level guard fields:

```text
calibrated_claim_allowed = false
p0_release_conclusion_changed = false
physical_ceiling_role = surrogate_risk_reduction_only
diagnostic_outputs_generated = true
solver_or_simulation_execution_authorized = false
```

Each binding row must include:

```text
lane_id
contract_path
source_id
source_path
source_type
source_sha256
source_exists = true
required_fields
missing_required_fields = []
required_fields_present = true
diagnostic_output_generated = false
```

The manifest is a source-binding guard only. It does not authorize calibrated
SNR, absolute LOD, true EV concentration, biological specificity,
detector-voltage prediction, sample-count, measured blank-safety, or route
promotion claims.
