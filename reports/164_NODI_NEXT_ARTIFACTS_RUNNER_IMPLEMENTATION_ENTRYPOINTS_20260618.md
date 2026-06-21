# Report 164 - NODI next artifacts runner implementation entrypoints

Date: 2026-06-18

Status:

```text
runner_implementation_entrypoints_implemented
RUNNER_IMPLEMENTATION_READY_NOT_EXECUTED
runner implementation phrase accepted
no runner execution
no smoke execution
no NODI run
no COMSOL run
no production artifact
no JOINT_ROUTE_CLASS regeneration
```

The exact future authorization phrase was received:

```text
authorize NODI next-artifacts runner implementation
```

The phrase guard returned:

```text
PHRASE_MATCH_RUNNER_IMPLEMENTATION_ONLY_NO_EXECUTION
```

This authorizes implementation of runner entrypoints only. It does not
authorize runner execution, bounded smoke execution, production generation,
NODI/COMSOL runs, `JOINT_ROUTE_CLASS` regeneration, or any positive claim.

## 1. Implemented files

Updated:

```text
nodi_simulator/nodi_comsol_next_artifacts.py
tests/test_nodi_comsol_next_artifacts_contracts.py
```

Added:

```text
tools/audits/build_nodi_position_response_surface.py
tools/audits/build_nodi_effective_aperture_surrogate_sensitivity.py
```

## 2. Runner entrypoint behavior

The new entrypoints are implementation launch-plan writers. They do not build
PRS/EAS production CSVs.

Both CLIs require:

```text
--confirm-write-launch-plan
```

and write only a launch-plan JSON sidecar.

They expose no current execution surface:

```text
no --execute
no --run
no --production
```

## 3. PRS launch plan

Entrypoint:

```text
tools/audits/build_nodi_position_response_surface.py
```

Launch plan filename:

```text
NODI_POSITION_RESPONSE_SURFACE_RUNNER_LAUNCH_PLAN_20260618.json
```

Current status:

```text
runner_implementation_status = RUNNER_IMPLEMENTATION_READY_NOT_EXECUTED
runner_execution_status = NOT_EXECUTED
```

Planned row arithmetic:

```text
P1 preferred rows = 60710
P2 diagnostic trap rows = 12142
total if all approved routes = 72852
```

The PRS plan records the future runner phases as contract steps:

```text
load_route_diameter_view_manifest
generate_edge_and_xz_bin_definitions
prepare_event_accumulation_contract
prepare_post_seed_aggregation_contract
prepare_per_seed_diagnostic_sidecar_contract
join_guardrail_state_contract
attach_neutral_nodi_flow_condition_contract
run_validator_before_release_candidate_write
```

No event accumulation, NODI simulation, or response-surface CSV generation is
performed in this step.

## 4. EAS launch plan

Entrypoint:

```text
tools/audits/build_nodi_effective_aperture_surrogate_sensitivity.py
```

Launch plan filename:

```text
NODI_EFFECTIVE_APERTURE_SURROGATE_RUNNER_LAUNCH_PLAN_20260618.json
```

Current status:

```text
runner_implementation_status = RUNNER_IMPLEMENTATION_READY_NOT_EXECUTED
runner_execution_status = NOT_EXECUTED
```

Planned row arithmetic:

```text
routes = 4
views = 2
surrogate modes = 5
total route/view/mode rows if all modes = 40
```

The descriptor contract remains:

```text
source_geometry_descriptor_sha = 1198055754C41710A4821894ECB749660E5EF4A14B2E0FC647789BA31A0B38A2
route_geometry_id_comsol_version = route_geometry_id_comsol_v1_contract_20260616
descriptor_is_not_measured_geometry = true
descriptor_is_not_true_optical_w_eff = true
descriptor_is_not_optical_solver_output = true
```

No aperture-surrogate CSV generation is performed in this step.

## 5. Manual no-execution CLI check

Command chain:

```text
python tools/audits/build_nodi_position_response_surface.py \
  --confirm-write-launch-plan \
  --output-dir tmp/nodi_next_artifacts_runner_implementation_20260618/prs

python tools/audits/build_nodi_effective_aperture_surrogate_sensitivity.py \
  --confirm-write-launch-plan \
  --output-dir tmp/nodi_next_artifacts_runner_implementation_20260618/eas
```

Result:

```text
NODI_POSITION_RESPONSE_SURFACE_RUNNER: RUNNER_IMPLEMENTATION_READY_NOT_EXECUTED
runner_execution_status: NOT_EXECUTED
launch_plan_sha256: 3f506b5bf85bc09bf7926cde3bfb814af682fa8d2dc368765533709e52fe5668

NODI_EFFECTIVE_APERTURE_SURROGATE_RUNNER: RUNNER_IMPLEMENTATION_READY_NOT_EXECUTED
runner_execution_status: NOT_EXECUTED
launch_plan_sha256: 360dc2b17ec58f510d6b1c5d379b83f54a64d8a464940163c50dacfc373425c8
```

## 6. Verification performed

Focused tests:

```text
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
result: 58 passed
```

Static checks:

```text
python -m ruff check nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/build_nodi_position_response_surface.py \
  tools/audits/build_nodi_effective_aperture_surrogate_sensitivity.py \
  tools/audits/check_nodi_next_artifacts_future_authorization_phrase.py \
  tools/audits/write_nodi_next_artifacts_authorization_gate.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py
result: All checks passed

python -m py_compile nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/build_nodi_position_response_surface.py \
  tools/audits/build_nodi_effective_aperture_surrogate_sensitivity.py \
  tools/audits/check_nodi_next_artifacts_future_authorization_phrase.py \
  tools/audits/write_nodi_next_artifacts_authorization_gate.py
result: pass
```

## 7. Independent review status

Independent verifier subagent result:

```text
PASS
```

Scope reviewed:

```text
nodi_simulator/nodi_comsol_next_artifacts.py
tools/audits/build_nodi_position_response_surface.py
tools/audits/build_nodi_effective_aperture_surrogate_sensitivity.py
tests/test_nodi_comsol_next_artifacts_contracts.py
reports/164_NODI_NEXT_ARTIFACTS_RUNNER_IMPLEMENTATION_ENTRYPOINTS_20260618.md
```

Review conclusion:

```text
entrypoints only write launch-plan sidecars
no PRS/EAS production CSVs are generated
CLI surfaces expose no --execute, --run, or --production
runner_execution_status remains NOT_EXECUTED
downstream authorization flags remain false
PRS/EAS row arithmetic matches the report
tests cover the guarantees
no material gaps in requested scope
```

## 8. Still not authorized

This step does not authorize:

```text
runner execution
smoke execution
full production run
production response-surface artifact
production aperture-surrogate artifact
COMSOL run
JOINT_ROUTE_CLASS regeneration
q_ch * eta
q_ch * chi_selected * eta
yield
winner
true W_eff
measured geometry
optical solver output
fabrication release
P3 solver execution or conclusion
```

## 9. Current stop point

```text
RUNNER_IMPLEMENTATION_ENTRYPOINTS_PASS_INDEPENDENT_REVIEW_PASS_STOP_BEFORE_SMOKE_AUTHORIZATION
```
