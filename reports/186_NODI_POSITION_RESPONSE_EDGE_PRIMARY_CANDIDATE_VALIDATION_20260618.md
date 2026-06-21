# Report 186 - NODI PRS Edge-Primary Candidate Validation

Date: 2026-06-18

## Disposition

PASS_PRS_EDGE_PRIMARY_CANDIDATE_VALIDATED_NOT_PROMOTED

This report validates a production-shaped `NODI_POSITION_RESPONSE_SURFACE`
candidate generated from the Report 185 edge-primary eligible source. The candidate
is not promoted into the production-generation gate in this report.

## Inputs

- source:
  `tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk027_20260618/NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_20260618.csv`
- source SHA256:
  `069d8ed4f55e44bc5567225e6eaac9e95a9d9512898ddda294500205aaf08fb7`
- eligibility policy:
  `edge_norm_1d_primary_xz_norm_2d_diagnostic_no_auto_promotion`

## Output Bundle

- output dir:
  `tmp/nodi_position_response_edge_primary_candidate_20260618/`
- candidate CSV:
  `tmp/nodi_position_response_edge_primary_candidate_20260618/NODI_POSITION_RESPONSE_SURFACE_EDGE_PRIMARY_CANDIDATE_20260618.csv`
- candidate CSV SHA256:
  `e584deecf43ac163f2a904782569143b3c4095bcb72dd439d598d652ee70869e`
- report:
  `tmp/nodi_position_response_edge_primary_candidate_20260618/NODI_POSITION_RESPONSE_SURFACE_EDGE_PRIMARY_CANDIDATE_REPORT_20260618.json`
- report SHA256:
  `75aadf5a011245169499c8911219cf9b88b5a5558846d2179cf1accf9e9b079f`
- issues CSV SHA256:
  `9b1eeccafea4928aa6e005f037f75c91de6c8b09ba5ba7346d875f90edf2d26a`

## Row Arithmetic

- route/diameter/view grains: 4
- rows per route/diameter/view: 467
- total candidate rows: 1868
- `edge_norm_1d` rows: 92
- `xz_norm_2d` rows: 1776
- `edge_norm_primary` rows: 92
- `xz_norm_diagnostic` rows: 1776
- `xz_norm_primary_if_adequate` rows: 0

## Boundary Checks

- `decision_use_allowed=true` for `edge_norm_1d`: 92 rows
- `decision_use_allowed=false` for `xz_norm_2d`: 1776 rows
- flow condition:
  `nodi_position_response_surface_v1_not_comsol_transport` for all 1868 rows
- `not_qch_weighted=true`: 1868 rows
- `not_yield=true`: 1868 rows
- `not_detection_probability=true`: 1868 rows
- candidate promoted to production gate: false
- production generation performed: false
- COMSOL run performed: false
- `JOINT_ROUTE_CLASS` regenerated: false

## Verification

- `validate_position_response_surface_rows(..., production_table=True, require_complete_row_arithmetic=True)`:
  `[]`
- `python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -k "edge_primary_candidate or production_eligibility or source_sufficiency"`:
  10 passed.
- `python -m py_compile tools/audits/build_nodi_position_response_edge_primary_candidate.py tools/audits/run_nodi_position_response_source_production_eligibility_preflight.py nodi_simulator/nodi_comsol_next_artifacts.py`:
  pass.
- `python -m ruff check nodi_simulator/nodi_comsol_next_artifacts.py tests/test_nodi_comsol_next_artifacts_contracts.py tools/audits/run_nodi_position_response_source_production_eligibility_preflight.py tools/audits/build_nodi_position_response_edge_primary_candidate.py`:
  pass.
- Negative artifact scan found no `COMSOL` or `JOINT_ROUTE_CLASS` outputs in the
  candidate output directory.

## Next Step

The next step is an independent review of the edge-primary candidate builder and
candidate output. If that review passes, the production-generation gate can be
updated in a separate step to accept a validated edge-primary candidate as the PRS
artifact source while preserving the strict all-row sufficiency gate as a separate
diagnostic policy.
