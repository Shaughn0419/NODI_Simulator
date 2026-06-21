# Report 188 - NODI Production Gate Review Fix

Date: 2026-06-18

## Disposition

PASS_REVIEW_FIX_PRODUCTION_GATE_CANDIDATE_BLOCKER_HANDLING

The final independent review of Report 187 found one medium issue: explicitly
supplying a missing `--position-response-candidate` path produced a blocked report
with an unclear PRS status/blocker shape.

This report records the fix and regression coverage. The Report 187 production
artifacts remain valid and unchanged.

## Fix

`build_production_generation_report(...)` now requires a PRS candidate to satisfy
all three conditions before it is considered ready:

- a candidate path is supplied
- the candidate file exists
- `validate_position_response_surface_rows(..., production_table=True, require_complete_row_arithmetic=True)` returns no issues

If the candidate path is supplied but missing or invalid, the report now:

- remains `BLOCKED_PRODUCTION_GENERATION_INPUTS`
- sets `position_response_surface_status=blocked_missing_position_response_event_source`
- records a PRS blocker with `status=blocked_invalid_position_response_candidate`
- keeps `position_response_surface_production_generated=false`

## Regression Tests Added

- missing PRS candidate path is blocked with a PRS blocker
- invalid PRS candidate CSV is blocked with a PRS blocker
- CLI with missing `--position-response-candidate` returns nonzero and writes a
  clean blocked report

## Verification

- `python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -k "production_generation or edge_primary_candidate or production_eligibility or source_sufficiency"`:
  23 passed.
- `python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py`:
  141 passed.
- `python -m pytest tests/test_realism_v2_io.py`:
  8 passed.
- `python -m py_compile tools/audits/run_nodi_next_artifacts_production_generation.py tools/audits/build_nodi_position_response_edge_primary_candidate.py tools/audits/run_nodi_position_response_source_production_eligibility_preflight.py nodi_simulator/nodi_comsol_next_artifacts.py`:
  pass.
- `python -m ruff check nodi_simulator/nodi_comsol_next_artifacts.py tests/test_nodi_comsol_next_artifacts_contracts.py tools/audits/run_nodi_next_artifacts_production_generation.py tools/audits/run_nodi_position_response_source_production_eligibility_preflight.py tools/audits/build_nodi_position_response_edge_primary_candidate.py nodi_simulator/realism_v2_io.py tests/test_realism_v2_io.py`:
  pass.

## Boundary

This fix did not run NODI, did not run COMSOL, did not regenerate
`JOINT_ROUTE_CLASS`, did not alter the strict PRS numeric sufficiency policy, did
not change the Report 187 production artifacts, and did not authorize any q_ch
weighting, yield, winner, detection probability, true W_eff, measured geometry,
optical solver, fabrication release, or P3 solver conclusion.
