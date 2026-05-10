# Post-v2 Bounded Physical-Solver Readiness P2 Artifacts

This directory is for P2 bounded physical-solver readiness artifacts.

Current allowed contents:

```text
bounded_physical_solver_readiness_schema_manifest.json
bounded_physical_solver_readiness_artifact_manifest.json
```

These files are schema and governance manifests only. They do not contain
full-wave solver output, Green-tensor solver output, vector solver output,
Jones sweep output, roughness/leakage perturbation output, transport output,
residence-time perturbation output, measured data, calibration data,
detector-unit prediction, or route-promotion evidence.

The role of this directory is `bounded_solver_readiness_only`. It does not
change the P0 release conclusion, and it preserves the P1
`surrogate_risk_reduction_only` role. Calibrated SNR, absolute LOD, true EV
concentration, biological specificity, detector-voltage prediction,
sample-count, measured blank-safety, and route-promotion claims remain blocked.
