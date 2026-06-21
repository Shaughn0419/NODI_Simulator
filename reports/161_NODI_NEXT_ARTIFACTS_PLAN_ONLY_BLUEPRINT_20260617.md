# Report 161 - NODI next artifacts PLAN_ONLY_NOT_EXECUTED blueprint layer

Date: 2026-06-17

Status:

```text
plan_only_blueprint_layer_implemented
PLAN_ONLY_NOT_EXECUTED
not_smoke_execution
not_production_artifact
no runner implementation
no runner execution
no smoke execution
no NODI run
no COMSOL run
no JOINT_ROUTE_CLASS regeneration
independent_review_pass
```

This report records the bounded step after Report 160. The blueprint layer
expands the design-only smoke manifest scopes into compact planned combinations.
It does not simulate events, does not compute optical responses, does not
produce PRS/EAS production rows, and does not authorize any runner execution.

## 1. Implemented files

Updated:

```text
nodi_simulator/nodi_comsol_next_artifacts.py
tests/test_nodi_comsol_next_artifacts_contracts.py
```

Added:

```text
tools/audits/write_nodi_next_artifacts_plan_blueprints.py
```

## 2. Blueprint outputs

The CLI writes:

```text
NODI_POSITION_RESPONSE_SURFACE_PLAN_BLUEPRINT_20260617.csv
NODI_EFFECTIVE_APERTURE_SURROGATE_PLAN_BLUEPRINT_20260617.csv
NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINT_INDEX_20260617.csv
NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINT_METADATA_20260617.json
```

All plan rows carry:

```text
planned_execution_status = PLAN_ONLY_NOT_EXECUTED
no_runner_execution = true
no_smoke_execution = true
no_production_artifact = true
```

The metadata carries:

```text
no_runner_implementation = true
no_runner_execution = true
no_smoke_execution = true
no_nodi_run = true
no_comsol_run = true
no_production_artifact = true
no_joint_route_class_regeneration = true
not_qch_weighted = true
not_yield = true
not_winner = true
not_true_W_eff = true
not_measured_geometry = true
not_optical_solver_output = true
not_fabrication_release = true
not_P3_solver_conclusion = true
```

## 3. Blueprint semantics

PRS blueprint:

```text
source = Report 156 design-only PRS smoke manifest
grain = source_smoke_id x route_id_nodi x diameter_nm x NODI_view
planned_route_diameter_view_rows = 467 for normal plan rows
validator negative fixture rows remain planned_row_count=0
```

EAS blueprint:

```text
source = Report 156 design-only EAS smoke manifest
grain = source_smoke_id x route_id_nodi x NODI_view x aperture_surrogate_mode
planned_route_view_mode_rows = 1 for normal plan rows
validator fixture rows remain planned_row_count=0
```

Observed compact blueprint row counts in the CLI smoke-to-blueprint check:

```text
NODI_POSITION_RESPONSE_SURFACE_PLAN_BLUEPRINT_20260617.csv rows=62
NODI_EFFECTIVE_APERTURE_SURROGATE_PLAN_BLUEPRINT_20260617.csv rows=45
NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINT_INDEX_20260617.csv rows=2
```

These are plan rows only, not response-surface rows and not aperture-surrogate
production rows.

## 4. Verification performed

```text
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
result: 36 passed

python -m ruff check nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/validate_nodi_position_response_surface.py \
  tools/audits/validate_nodi_effective_aperture_surrogate_sensitivity.py \
  tools/audits/write_nodi_next_artifacts_smoke_manifests.py \
  tools/audits/write_nodi_next_artifacts_runner_preflight.py \
  tools/audits/write_nodi_next_artifacts_plan_blueprints.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py
result: All checks passed

python -m py_compile nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/validate_nodi_position_response_surface.py \
  tools/audits/validate_nodi_effective_aperture_surrogate_sensitivity.py \
  tools/audits/write_nodi_next_artifacts_smoke_manifests.py \
  tools/audits/write_nodi_next_artifacts_runner_preflight.py \
  tools/audits/write_nodi_next_artifacts_plan_blueprints.py
result: pass
```

Manual CLI chain:

```text
write design-only smoke manifest bundle to tmp
write PLAN_ONLY_NOT_EXECUTED blueprint bundle from that smoke manifest bundle
```

Result:

```text
NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINTS: PASS
PRS blueprint rows=62, planned_execution_status=PLAN_ONLY_NOT_EXECUTED
EAS blueprint rows=45, planned_execution_status=PLAN_ONLY_NOT_EXECUTED
index rows=2, planned_execution_status=PLAN_ONLY_NOT_EXECUTED
metadata no_runner_execution=true
metadata no_smoke_execution=true
metadata no_comsol_run=true
metadata no_production_artifact=true
```

## 5. Independent review status

```text
scope review subagent: PASS
implementation re-review: PASS
review gaps: none material for the requested narrow review
review risk note: source_smoke_id and smoke-oriented allowed_output_status labels remain lineage labels only and are paired with PLAN_ONLY_NOT_EXECUTED plus negative-boundary metadata
```

## 6. Still not authorized

This step does not authorize:

```text
runner implementation
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

## 7. Current stop point

```text
PLAN_ONLY_BLUEPRINT_PASS_READY_FOR_COMSOL_READONLY_REVIEW
```
