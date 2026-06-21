# Report 187 - NODI Next Artifacts Full Production Generation, PRS + EAS

Date: 2026-06-18

## Disposition

PASS_PRODUCTION_GENERATION

This report records the first full NODI next-artifacts production-generation gate
that writes both:

- `NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY`
- `NODI_POSITION_RESPONSE_SURFACE`

The PRS artifact is produced only from the validated Report 186 edge-primary
candidate. The old strict all-row numeric sufficiency gate remains retained as a
separate diagnostic/stronger policy and is not redefined by this report.

## Inputs

- bounded-smoke execution report:
  `tmp/nodi_next_artifacts_bounded_smoke_execution_20260618/NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_REPORT_20260618.json`
- COMSOL geometry descriptor:
  `tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv`
- rank source:
  `exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv`
- guardrail table:
  `exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv`
- PRS candidate:
  `tmp/nodi_position_response_edge_primary_candidate_20260618/NODI_POSITION_RESPONSE_SURFACE_EDGE_PRIMARY_CANDIDATE_20260618.csv`
- PRS candidate SHA256:
  `e584deecf43ac163f2a904782569143b3c4095bcb72dd439d598d652ee70869e`

## Output Bundle

- output dir:
  `tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/`
- production-generation report:
  `tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_20260618.json`
- production-generation report SHA256:
  `12e3ba991b3ce1b3cf192f07c3291bc1ce338b202dcaa2d2ec3c493d0f7970f4`
- blocker CSV SHA256:
  `963b728a9077a333ab8173f2c1493b89822eebaeb1c8da5a1d9f1f5d690d63ac`
- issue CSV SHA256:
  `9b1eeccafea4928aa6e005f037f75c91de6c8b09ba5ba7346d875f90edf2d26a`

## Production Artifacts

- `NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv`
  - rows: 32
  - SHA256: `35c8b43e641631b682df07dc305ee17bc97384e6cf135c94adce791748243ecc`
- `NODI_EFFECTIVE_APERTURE_SURROGATE_SELECTOR_POLICY_20260618.json`
  - rows: 1 metadata object
  - SHA256: `399e34aa40279c0fc47a335685ddedd6b159f98a1786bb03b3cb13b20466ad32`
- `NODI_POSITION_RESPONSE_SURFACE.csv`
  - rows: 1868
  - SHA256: `e584deecf43ac163f2a904782569143b3c4095bcb72dd439d598d652ee70869e`

## PRS Evidence

- route/diameter/view grains: 4
- rows per route/diameter/view: 467
- `edge_norm_1d` rows: 92
- `xz_norm_2d` rows: 1776
- `edge_norm_primary` rows: 92
- `xz_norm_diagnostic` rows: 1776
- `xz_norm_primary_if_adequate` rows: 0
- `decision_use_allowed=true` for `edge_norm_1d`: 92 rows
- `decision_use_allowed=false` for `xz_norm_2d`: 1776 rows
- flow condition:
  `nodi_position_response_surface_v1_not_comsol_transport` for all 1868 rows

## EAS Evidence

- production rows: 32
- first-production modes:
  - `nominal_width`
  - `W_bottom_conservative`
  - `min_aperture_conservative`
  - `top_bottom_average_heuristic`
- excluded first-production mode:
  `COMSOL_descriptor_if_available`
- selector policy:
  `process_state=nominal_smooth_geometry`,
  `angle_convention=sidewall_angle_from_substrate_plane_90deg_vertical`,
  `sidewall_deg=85.0`

## Boundary

The production-generation gate did not run NODI, did not run COMSOL, did not
regenerate `JOINT_ROUTE_CLASS`, did not apply q_ch weighting, did not compute yield,
did not choose a winner, did not compute detection probability, did not claim true
W_eff, did not claim measured geometry, did not claim optical solver output, did not
claim fabrication release, and did not claim P3 solver conclusions.

## Verification

- `validate_production_generation_report(...)`: `[]`
- `validate_position_response_surface_rows(..., production_table=True, require_complete_row_arithmetic=True)`:
  `[]`
- `validate_effective_aperture_surrogate_rows(...)`: `[]`
- `python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -k "production_generation or edge_primary_candidate or production_eligibility or source_sufficiency"`:
  20 passed.
- `python -m py_compile tools/audits/run_nodi_next_artifacts_production_generation.py tools/audits/build_nodi_position_response_edge_primary_candidate.py tools/audits/run_nodi_position_response_source_production_eligibility_preflight.py nodi_simulator/nodi_comsol_next_artifacts.py`:
  pass.
- `python -m ruff check nodi_simulator/nodi_comsol_next_artifacts.py tests/test_nodi_comsol_next_artifacts_contracts.py tools/audits/run_nodi_next_artifacts_production_generation.py tools/audits/run_nodi_position_response_source_production_eligibility_preflight.py tools/audits/build_nodi_position_response_edge_primary_candidate.py`:
  pass.
- Negative artifact scan found no `COMSOL` or `JOINT_ROUTE_CLASS` outputs in the
  production output directory.

## Next Step

Independent review should verify this full production-generation gate. If it passes,
the next handoff can package Reports 185-187 plus the full production output and ask
COMSOL for a read-only boundary review before any downstream joint regeneration is
considered.
