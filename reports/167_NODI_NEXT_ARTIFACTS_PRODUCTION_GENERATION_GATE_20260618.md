# Report 167 - NODI next artifacts production-generation gate

Date: 2026-06-18

Status:

```text
production_generation_gate_implemented
exact_production_phrase_received
production_generation_gate_run
BLOCKED_PRODUCTION_GENERATION_INPUTS
no production PRS/EAS artifact generated
no NODI production run
no COMSOL run
no JOINT_ROUTE_CLASS regeneration
```

The user supplied the exact phrase:

```text
authorize NODI next-artifacts production generation
```

This report records that NODI entered the production-generation gate. The gate
did not produce production artifacts because required production inputs/policies
are incomplete.

## 1. Implemented files

Updated:

```text
nodi_simulator/nodi_comsol_next_artifacts.py
tests/test_nodi_comsol_next_artifacts_contracts.py
```

Added:

```text
tools/audits/run_nodi_next_artifacts_production_generation.py
```

## 2. Gate behavior

The CLI requires:

```text
--confirm-production-generation
--authorization-phrase "authorize NODI next-artifacts production generation"
--smoke-execution-report <Report 166 smoke execution JSON>
--geometry-descriptor <COMSOL_GEOMETRY_DESCRIPTOR_V1.csv>
--rank-source <NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv>
--guardrail-table <NODI_REFERENCE_GUARDRAIL_TABLE.csv>
```

It performs production input/policy checks and writes blocker sidecars when
production rows would otherwise be fabricated.

## 3. Production gate run

Command:

```text
python tools/audits/run_nodi_next_artifacts_production_generation.py \
  --confirm-production-generation \
  --authorization-phrase 'authorize NODI next-artifacts production generation' \
  --smoke-execution-report tmp/nodi_next_artifacts_bounded_smoke_execution_20260618/NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_REPORT_20260618.json \
  --geometry-descriptor tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv \
  --rank-source exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv \
  --guardrail-table exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv \
  --output-dir tmp/nodi_next_artifacts_production_generation_20260618
```

Result:

```text
NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION:
BLOCKED_PRODUCTION_GENERATION_INPUTS
EXIT_STATUS=1
```

Output files:

```text
tmp/nodi_next_artifacts_production_generation_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_20260618.json
SHA256: de98b372f54497ff9edbcf347e656771ce7bb04e1d4e065ebbdd8289eedb346e

tmp/nodi_next_artifacts_production_generation_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_BLOCKERS_20260618.csv

tmp/nodi_next_artifacts_production_generation_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_ISSUES_20260618.csv
```

No `NODI_POSITION_RESPONSE_SURFACE.csv` or
`NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv` was written.

## 4. Blockers

`NODI_POSITION_RESPONSE_SURFACE`:

```text
blocker_id = PRS-PROD-B01
status = blocked_missing_position_response_event_source
required_input_or_policy = event-level or bin-conditioned position-response source with route/diameter/view/seed/bin response counts
current_evidence = smoke and PLAN_ONLY blueprints exist, but they are not response events and must not be promoted to production rows
unblock_action = provide or implement a real PRS event/bin accumulator source, then validate 467 rows per route/diameter/view
```

`NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY`:

```text
blocker_id = EAS-PROD-B01
status = blocked_missing_explicit_geometry_selector_policy
required_input_or_policy = one explicit COMSOL descriptor row per W/D production grain, or a reviewed schema extension that includes sidewall/process
current_evidence = descriptor candidates per W/D: W500/D900=24; W500/D1200=24; W800/D900=24; W800/D1200=24
unblock_action = ask COMSOL/NODI to approve a geometry selector policy, such as a specific sidewall/process/depth rule, before production EAS CSV generation
```

## 5. Boundary validation

Structured validation:

```text
status BLOCKED_PRODUCTION_GENERATION_INPUTS
status_is_blocked True
authorization_phrase_exact_match True
production_generation_authorized_by_phrase True
production_generation_performed False
production_artifacts_generated []
nodi_run_performed False
comsol_run_performed False
joint_route_class_regenerated False
not_qch_weighted True
not_yield True
not_winner True
not_true_W_eff True
validation_issues []
```

Output directory scan:

```text
no NODI_POSITION_RESPONSE_SURFACE.csv
no NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv
```

Forbidden-claim scan:

```text
no production_generation_performed true
no nodi_run_performed true
no comsol_run_performed true
no joint_route_class_regenerated true
no q_ch*eta / q_ch_eta / qch_eta
no W_eff_nm / delta_W_eff_nm
no winner_selected / yield_computed / true_w_eff_claimed
```

## 6. Verification performed

Focused tests:

```text
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
result: 78 passed
```

Static checks:

```text
python -m py_compile nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/run_nodi_next_artifacts_production_generation.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py
result: pass

ruff check nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/run_nodi_next_artifacts_production_generation.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py
result: All checks passed
```

## 7. Independent review status

Independent verifier subagent:

```text
PASS
```

Review conclusion:

```text
no findings
exact production phrase matched
production_generation_authorized_by_phrase = true
production_generation_performed = false
status = BLOCKED_PRODUCTION_GENERATION_INPUTS
PRS blocker correctly records missing event/bin source
EAS blocker correctly records ambiguous descriptor selector policy
no production PRS/EAS CSVs generated
no COMSOL run
no NODI production run
no JOINT_ROUTE_CLASS regeneration
no q_ch*eta / yield / winner / true W_eff / measured geometry / optical solver output / fabrication release / P3 solver conclusion
```

Independent focused verification:

```text
pytest -q tests/test_nodi_comsol_next_artifacts_contracts.py -k 'production_generation or future_authorization or blocked'
result: 15 passed, 63 deselected
```

Risk note:

```text
The blocker evidence is snapshot-specific to the current staged inputs in
tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv and current rank/guardrail sources.
If those inputs change, the gate outcome may change.
```

## 8. Next unblock request for COMSOL/NODI discussion

Questions for COMSOL/NODI before production artifacts can be generated:

```text
1. For NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY, which COMSOL geometry
   descriptor row should be selected for the production grain
   route_id_nodi x NODI_view x aperture_surrogate_mode?

   Current descriptor candidates per W/D:
   W500/D900=24
   W500/D1200=24
   W800/D900=24
   W800/D1200=24

   Please either approve a single geometry-selector policy, such as a specific
   sidewall/process rule, or approve a schema extension that carries
   sidewall/process in the EAS grain.

2. For COMSOL_descriptor_if_available, should this mode be:
   a. excluded from the first production EAS artifact,
   b. defined as an alias of one explicit descriptor-backed formula, or
   c. emitted as blocked rows until a policy exists?

3. For PRS, can NODI provide or regenerate the real event-level/bin-conditioned
   position-response source needed for:
   route x diameter x view x seed x bin response counts?

   Smoke manifests and PLAN_ONLY blueprints are not sufficient and must not be
   promoted to production PRS rows.
```

## 9. Current stop point

```text
STOPPED_AT_PRODUCTION_GENERATION_INPUT_BLOCKERS
```

No further production artifact generation is safe until the PRS source and EAS
geometry-selector policy are resolved.
