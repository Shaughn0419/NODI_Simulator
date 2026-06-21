# COMSOL Read-Only Review Prompt - NODI Next Artifacts Full Production

Scope: read-only review only. Do not run COMSOL. Do not run NODI. Do not regenerate
`JOINT_ROUTE_CLASS`. Do not produce q_ch weighting, yield, winner, detection
probability, true W_eff, measured geometry, optical solver output, fabrication
release, or P3 solver conclusions.

Please review the attached NODI package for the full next-artifacts production gate.

## Files to Review

Primary reports:

- `reports/185_NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY_EDGE_PRIMARY_PREFLIGHT_20260618.md`
- `reports/186_NODI_POSITION_RESPONSE_EDGE_PRIMARY_CANDIDATE_VALIDATION_20260618.md`
- `reports/187_NODI_NEXT_ARTIFACTS_FULL_PRODUCTION_GENERATION_PRS_EAS_20260618.md`
- `reports/188_NODI_NEXT_ARTIFACTS_PRODUCTION_GATE_REVIEW_FIX_20260618.md`

Primary production outputs:

- `tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_20260618.json`
- `tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_POSITION_RESPONSE_SURFACE.csv`
- `tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv`
- `tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_EFFECTIVE_APERTURE_SURROGATE_SELECTOR_POLICY_20260618.json`
- `tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_BLOCKERS_20260618.csv`
- `tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_ISSUES_20260618.csv`

Supporting candidate/preflight outputs:

- `tmp/nodi_position_response_source_production_eligibility_20260618/`
- `tmp/nodi_position_response_edge_primary_candidate_20260618/`

Implementation and tests:

- `nodi_simulator/nodi_comsol_next_artifacts.py`
- `nodi_simulator/realism_v2_io.py`
- `tools/audits/run_nodi_next_artifacts_production_generation.py`
- `tools/audits/run_nodi_position_response_source_production_eligibility_preflight.py`
- `tools/audits/build_nodi_position_response_edge_primary_candidate.py`
- `tests/test_nodi_comsol_next_artifacts_contracts.py`
- `tests/test_realism_v2_io.py`

## Requested Review Questions

1. Does the NODI PRS path correctly preserve the old strict all-row numeric
   sufficiency policy as a separate diagnostic/stronger policy, while allowing the
   first production PRS artifact to use the explicit
   `edge_norm_1d_primary_xz_norm_2d_diagnostic_no_auto_promotion` policy?

2. Does `NODI_POSITION_RESPONSE_SURFACE.csv` obey the agreed Report 155/156 flow
   semantics?
   - production rows use `row_scope=response_surface_bin`
   - flow condition is
     `nodi_position_response_surface_v1_not_comsol_transport`
   - no W800 q_ch distribution is treated as global transport
   - no q_ch*eta weighting is applied

3. Does the PRS production artifact remain edge-primary/xz-diagnostic?
   - expected rows: 1868
   - expected route/diameter/view grains: 4
   - expected rows per route/diameter/view: 467
   - expected `edge_norm_primary` rows: 92
   - expected `xz_norm_diagnostic` rows: 1776
   - expected `xz_norm_primary_if_adequate` rows: 0

4. Does `NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv` remain a dry
   surrogate sensitivity artifact only?
   - no true W_eff
   - no measured geometry
   - no optical solver output
   - no fabrication release
   - no P3 solver conclusion
   - descriptor selector policy remains exactly the COMSOL-approved
     `nominal_smooth_geometry`, `sidewall_deg=85.0` policy

5. Does the production gate correctly require an explicit validated PRS candidate
   before writing PRS, while preserving the old EAS-only partial path when no PRS
   candidate is provided?

6. Did the review-fix in Report 188 close the missing/invalid candidate blocker
   issue cleanly?

7. Is there any remaining NODI/COMSOL boundary violation, artifact naming ambiguity,
   or required correction before COMSOL treats these files as ready for downstream
   read-only joint input review?

## Expected Answer Format

Please return:

- Disposition: `PASS`, `PASS_WITH_CORRECTION`, or `BLOCKER`
- Reviewed package path and SHA256
- Key files reviewed
- Findings by artifact:
  - PRS
  - EAS
  - production gate/reporting
  - tests/validators
- Any corrections required before downstream use
- Explicit statement whether this authorizes COMSOL run, NODI run, or
  `JOINT_ROUTE_CLASS` regeneration. Expected answer: no, unless a separate future
  authorization is issued.
