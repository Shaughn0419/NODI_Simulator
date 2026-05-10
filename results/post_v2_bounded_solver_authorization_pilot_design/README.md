# Post-v2 Bounded Solver Authorization Pilot Design P3 Artifacts

This directory is for P3 phase-1 bounded solver authorization planning and
minimal pilot-design artifacts.

Current allowed contents:

```text
bounded_solver_authorization_pilot_design_p2_route_binding_manifest.json
bounded_solver_authorization_pilot_design_route_subset_manifest.json
bounded_solver_authorization_pilot_design_schema_manifest.json
bounded_solver_authorization_pilot_design_artifact_manifest.json
```

These files are schema and governance manifests only. They do not contain
full-wave solver output, Green-tensor solver output, vector solver output,
roughness/leakage perturbation output, transport output, residence-time
perturbation output, measured data, calibration data, detector-unit prediction,
or route-promotion evidence.

The route subset manifest binds only the P2 bounded route-universe manifest. It
is a future pilot preflight design, not solver result evidence and not
route-promotion evidence. Raw proxy fields remain excluded, and raw
arbitrary-unit or solver-native magnitude cannot be used as a final gate.

The role of this directory is
`bounded_solver_authorization_pilot_design_only`. It does not change the P0
release conclusion, it preserves the P1 `surrogate_risk_reduction_only` role,
and it preserves the P2 readiness scope. Calibrated SNR, absolute LOD, true EV
concentration, biological specificity, detector-voltage prediction,
sample-count, measured blank-safety, and route-promotion claims remain blocked.

P3 phase 1 stops here. Solver execution remains unauthorized.
