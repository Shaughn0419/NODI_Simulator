# Post-v2 Physical-Ceiling P1 Artifacts

This directory is for P1 physical-ceiling extension governance artifacts and
generated no-solver rank diagnostics.

Current allowed contents:

```text
physical_ceiling_contract_manifest.json
physical_ceiling_diagnostic_schema_manifest.json
physical_ceiling_input_binding_manifest.json
physical_ceiling_route_coverage_manifest.json
full_wave_green_tensor_diagnostic.csv
vector_jones_polarization_diagnostic.csv
roughness_leakage_diagnostic.csv
transport_residence_time_diagnostic.csv
```

The diagnostic CSV files are generated no-solver rank diagnostics. They are
derived only from existing P0 relative-audit route, rank-percentile, pairwise,
geometry, and proxy-stability fields. They do not contain full-wave solver,
vector solver, roughness/leakage simulation, transport simulation, measured
data, calibration data, or detector-unit predictions.

The role of this directory is `surrogate_risk_reduction_only`. It does not change the P0 release conclusion and does not authorize calibrated SNR,
absolute LOD, true EV concentration, biological specificity, detector-voltage
prediction, sample-count, or measured blank-safety claims.
