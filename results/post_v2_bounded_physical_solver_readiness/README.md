# Post-v2 Bounded Physical-Solver Readiness P2 Artifacts

This directory is for P2 bounded physical-solver readiness artifacts.

Current allowed contents:

```text
bounded_physical_solver_readiness_schema_manifest.json
bounded_physical_solver_readiness_source_binding_manifest.json
bounded_physical_solver_readiness_route_universe_manifest.json
bounded_physical_solver_readiness_artifact_manifest.json
```

These files are schema and governance manifests only. They do not contain
full-wave solver output, Green-tensor solver output, vector solver output,
Jones sweep output, roughness/leakage perturbation output, transport output,
residence-time perturbation output, measured data, calibration data,
detector-unit prediction, or route-promotion evidence.

The route-universe manifest is a bounded future-solver preflight inventory. It
contains route keys, comparison strata, final P0 route-audit fields, and P1
surrogate-risk labels only; raw proxy fields remain excluded from final gates.

The role of this directory is `bounded_solver_readiness_only`. It does not
change the P0 release conclusion, and it preserves the P1
`surrogate_risk_reduction_only` role. Calibrated SNR, absolute LOD, true EV
concentration, biological specificity, detector-voltage prediction,
sample-count, measured blank-safety, and route-promotion claims remain blocked.
