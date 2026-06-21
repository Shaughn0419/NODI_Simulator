# Report 166 - NODI next artifacts bounded-smoke execution

Date: 2026-06-18

Status:

```text
bounded_smoke_execution_implemented
bounded_smoke_execution_run
PASS_BOUNDED_SMOKE_EXECUTION_CONTRACT_ONLY
sidecar evidence only
no production PRS/EAS artifact
no NODI production run
no COMSOL run
no JOINT_ROUTE_CLASS regeneration
```

The user supplied the exact authorization phrase:

```text
authorize NODI next-artifacts bounded smoke execution
```

This phrase authorizes only the bounded-smoke sidecar path. It does not
authorize production generation, full runner execution, COMSOL work, NODI
production simulation, or `JOINT_ROUTE_CLASS` regeneration.

## 1. Implemented files

Updated:

```text
nodi_simulator/nodi_comsol_next_artifacts.py
tests/test_nodi_comsol_next_artifacts_contracts.py
```

Added:

```text
tools/audits/run_nodi_next_artifacts_bounded_smoke.py
```

## 2. Execution behavior

The bounded-smoke CLI requires all of the following:

```text
--confirm-bounded-smoke-execution
--authorization-phrase "authorize NODI next-artifacts bounded smoke execution"
--readiness-report <Report 165 readiness JSON>
```

It validates the readiness report first. Then it writes bounded-smoke execution
sidecars only:

```text
NODI_POSITION_RESPONSE_SURFACE_BOUNDED_SMOKE_EXECUTION_MANIFEST_20260618.csv
NODI_EFFECTIVE_APERTURE_SURROGATE_BOUNDED_SMOKE_EXECUTION_MANIFEST_20260618.csv
NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_REPORT_20260618.json
NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_ISSUES_20260618.csv
```

The smoke execution manifests are evidence rows derived from the smoke contract
manifests. They are not production PRS/EAS rows.

Execution report boundary fields:

```text
runner_execution_scope = bounded_smoke_contract_sidecar_only
bounded_smoke_execution_performed = true
bounded_smoke_runner_execution_authorized = true
production_generation_authorized = false
production_generation_performed = false
full_runner_execution_authorized = false
full_runner_execution_performed = false
nodi_run_performed = false
comsol_run_performed = false
joint_route_class_regenerated = false
no_production_artifact = true
not_qch_weighted = true
not_yield = true
not_winner = true
not_true_W_eff = true
not_measured_geometry = true
not_optical_solver_output = true
not_fabrication_release = true
not_P3_solver_conclusion = true
```

Claim boundary:

```text
bounded_smoke_execution_contract_sidecar_only_no_production
```

## 3. Bounded smoke run

Command:

```text
python tools/audits/run_nodi_next_artifacts_bounded_smoke.py \
  --confirm-bounded-smoke-execution \
  --authorization-phrase 'authorize NODI next-artifacts bounded smoke execution' \
  --readiness-report tmp/nodi_next_artifacts_smoke_readiness_20260618/readiness/NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_READINESS_REPORT_20260618.json \
  --output-dir tmp/nodi_next_artifacts_bounded_smoke_execution_20260618
```

Result:

```text
NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION:
PASS_BOUNDED_SMOKE_EXECUTION_CONTRACT_ONLY

report:
tmp/nodi_next_artifacts_bounded_smoke_execution_20260618/NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_REPORT_20260618.json
SHA256: 78fbb86c44b50b408f901534c0f8db081a3918bd9d5ebb43b16216f39d8f03e4

PRS smoke execution manifest:
tmp/nodi_next_artifacts_bounded_smoke_execution_20260618/NODI_POSITION_RESPONSE_SURFACE_BOUNDED_SMOKE_EXECUTION_MANIFEST_20260618.csv
rows: 5
SHA256: 02871935096dc43d88a113ed02117d372e301fbcaa94c350e985b0cd6f4b9594

EAS smoke execution manifest:
tmp/nodi_next_artifacts_bounded_smoke_execution_20260618/NODI_EFFECTIVE_APERTURE_SURROGATE_BOUNDED_SMOKE_EXECUTION_MANIFEST_20260618.csv
rows: 4
SHA256: cfa5ca42e599730d91115277bb33b147a0f79b2ec6e0056de17df66bfcea8ebd

issue CSV:
tmp/nodi_next_artifacts_bounded_smoke_execution_20260618/NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_ISSUES_20260618.csv
SHA256: 9b1eeccafea4928aa6e005f037f75c91de6c8b09ba5ba7346d875f90edf2d26a
```

## 4. Output validation

Structured validation result:

```text
status PASS_BOUNDED_SMOKE_EXECUTION_CONTRACT_ONLY
status_is_pass True
prs_rows 5
eas_rows 4
production_generation_performed False
nodi_run_performed False
comsol_run_performed False
joint_route_class_regenerated False
not_qch_weighted True
not_yield True
not_winner True
not_true_W_eff True
validation_issues []
```

Focused grep check:

```text
rg -n 'qch_eta|q_ch_eta|W_eff_nm|delta_W_eff_nm|production_generation_performed": true|nodi_run_performed": true|comsol_run_performed": true|joint_route_class_regenerated": true' tmp/nodi_next_artifacts_bounded_smoke_execution_20260618
```

Only one line matched: the intentional negative PRS fixture claim boundary
`q_ch_descriptive_only_not_qch_eta`. No `q_ch*eta` computation field, legacy
`W_eff_nm`, legacy `delta_W_eff_nm`, production generation true flag, NODI run
true flag, COMSOL run true flag, or JOINT regeneration true flag was found.

## 5. Verification performed

Focused tests:

```text
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
result: 72 passed
```

Static checks:

```text
python -m py_compile nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/run_nodi_next_artifacts_bounded_smoke.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py
result: pass

ruff check nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/run_nodi_next_artifacts_bounded_smoke.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py
result: All checks passed
```

## 6. Independent review status

Independent verifier subagent:

```text
PASS
```

Review conclusion:

```text
no findings
bounded smoke sidecar execution only
no production PRS/EAS generation
no COMSOL run
no NODI production run
no JOINT_ROUTE_CLASS regeneration
no q_ch*eta / yield / winner / true W_eff / measured geometry / optical solver output / fabrication release / P3 solver conclusion
readiness report remains preflight
execution report is the current smoke evidence
```

Independent focused test:

```text
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -k 'bounded_smoke_execution' -q
result: 8 passed, 64 deselected
```

Substantive execution artifact inventory:

```text
NODI_POSITION_RESPONSE_SURFACE_BOUNDED_SMOKE_EXECUTION_MANIFEST_20260618.csv
NODI_EFFECTIVE_APERTURE_SURROGATE_BOUNDED_SMOKE_EXECUTION_MANIFEST_20260618.csv
NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_REPORT_20260618.json
NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_ISSUES_20260618.csv
```

Note:

```text
macOS AppleDouble ._* metadata files exist in tmp and were treated as OS noise.
They should be removed only if a later publication package requires a literal clean directory.
```

## 7. Still not authorized

This step does not authorize:

```text
production generation
production NODI_POSITION_RESPONSE_SURFACE rows
production NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY rows
full NODI runner execution
COMSOL run
JOINT_ROUTE_CLASS regeneration
q_ch*eta or q_ch*chi_selected*eta
yield
winner selection
true W_eff
measured geometry
optical solver output
fabrication release
P3 solver conclusion
```

Next gate remains separate:

```text
authorize NODI next-artifacts production generation
```

That phrase has not been supplied in this step.
