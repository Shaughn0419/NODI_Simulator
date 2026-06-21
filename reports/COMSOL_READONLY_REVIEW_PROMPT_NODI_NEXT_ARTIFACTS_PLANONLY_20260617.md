# COMSOL read-only review prompt - NODI next artifacts through PLAN_ONLY blueprint

Scope: read-only review only. Do not run COMSOL, do not run NODI, do not
regenerate `JOINT_ROUTE_CLASS`, and do not authorize smoke or production.

NODI is returning a review package for the post-Report-156 implementation
sequence:

```text
Report 158: validator implementation
Report 159: design-only smoke manifest writer
Report 160: no-execution implementation preflight
Report 161: PLAN_ONLY_NOT_EXECUTED blueprint layer
```

The package includes source files, tests, reports, patched Report 156 CSV
contracts, and SHA manifests.

Package:

```text
directory: exports/nodi_comsol_readonly_review_planonly_20260617/
zip: exports/nodi_comsol_readonly_review_planonly_20260617.zip
zip_sha256: 73473fcd3bcaa8ac37fcbc4ab08fbd1c45cc7f12aaec8cbd8515c346729db61b
package_manifest: exports/nodi_comsol_readonly_review_planonly_20260617/PACKAGE_MANIFEST.json
hash_manifest: exports/nodi_comsol_readonly_review_planonly_20260617/SHA256SUMS.txt
```

## Review request

Please review whether NODI stayed inside the agreed NODI/COMSOL boundary.

Focus on these points:

1. Validator implementation:
   - Production `NODI_POSITION_RESPONSE_SURFACE` rows must be
     `row_scope=response_surface_bin`.
   - `qch_provenance_reference` must be rejected from production PRS rows.
   - `p1b_w800_qch_splitmid_20260617` must not be used as a production
     flow condition.
   - PRS rows must use neutral flow condition
     `nodi_position_response_surface_v1_not_comsol_transport`.
   - `W_eff_nm` / `delta_W_eff_nm` must be rejected in favor of
     `W_eff_surrogate_nm` / `delta_W_eff_surrogate_nm`.
   - EAS must remain dry sensitivity only, with
     `not_true_W_eff=true` and
     `claim_boundary=effective_aperture_surrogate_sensitivity_only`.
   - Extra positive claim columns such as `measured_geometry`,
     `optical_solver_output`, `fabrication_release`, and `p3_conclusion`
     must be rejected.
   - `COMSOL_GEOMETRY_DESCRIPTOR_V1` descriptor validation must pin
     `route_geometry_id_comsol_version=route_geometry_id_comsol_v1_contract_20260616`.

2. Design-only smoke manifest writer:
   - Outputs must be manifest/sidecar only.
   - All CSV rows must carry `execution_status=DESIGN_ONLY_NOT_EXECUTED`.
   - Index/metadata sidecars must not be interpreted as production artifacts.
   - The writer must not execute smoke, NODI, COMSOL, or production generation.

3. No-execution implementation preflight:
   - The preflight status must not read as runner authorization.
   - It should validate existing manifest/descriptor inputs and write only
     diagnostic report/issue sidecars.
   - Pass status is `PASS_NO_EXECUTION_IMPLEMENTATION_PREFLIGHT`.
   - Fail status is `BLOCKED_BEFORE_IMPLEMENTATION`.
   - Neither status authorizes runner execution, smoke execution, COMSOL work,
     production generation, or `JOINT_ROUTE_CLASS` regeneration.

4. PLAN_ONLY_NOT_EXECUTED blueprint layer:
   - Blueprint rows must be compact planned combinations only, not simulated
     event rows and not PRS/EAS production rows.
   - PRS blueprint expected compact rows: 62.
   - EAS blueprint expected compact rows: 45.
   - All blueprint rows must carry
     `planned_execution_status=PLAN_ONLY_NOT_EXECUTED`.
   - Metadata must preserve
     `no_runner_execution=true`,
     `no_smoke_execution=true`,
     `no_comsol_run=true`,
     `no_production_artifact=true`,
     `not_qch_weighted=true`,
     `not_yield=true`,
     `not_winner=true`,
     `not_true_W_eff=true`,
     `not_measured_geometry=true`,
     `not_optical_solver_output=true`,
     `not_fabrication_release=true`,
     and `not_P3_solver_conclusion=true`.

5. Forbidden claims:
   Confirm that no artifact, CLI, test, or report authorizes or computes:

```text
q_ch * eta
q_ch * chi_selected * eta
yield
winner
true W_eff
measured geometry
optical solver output
fabrication release
P3 solver execution or conclusion
COMSOL run
NODI smoke execution
production NODI_POSITION_RESPONSE_SURFACE
production NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY
JOINT_ROUTE_CLASS regeneration
```

## Requested response format

Please respond with one of:

```text
PASS
PASS_WITH_CORRECTION
BLOCKER
```

Then include:

```text
Reviewed package path:
Reviewed package SHA256:
Key files reviewed:
Findings:
Corrections required before next NODI step:
Any naming/semantic ambiguity:
Whether NODI may proceed to the next authorization gate:
```

If you find a problem, please cite exact file paths and, if possible, line
numbers or field names. Please distinguish wording/packaging concerns from
actual claim-boundary violations.
