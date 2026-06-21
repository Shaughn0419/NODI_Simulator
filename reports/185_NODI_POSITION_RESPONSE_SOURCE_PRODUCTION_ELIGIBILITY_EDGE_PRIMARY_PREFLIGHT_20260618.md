# Report 185 - NODI PRS Source Production-Eligibility Edge-Primary Preflight

Date: 2026-06-18

## Disposition

PASS_PRS_SOURCE_PRODUCTION_ELIGIBILITY_EDGE_PRIMARY_NOT_PRODUCTION

This report resolves the post-Report-184 ambiguity between two different gates:

- The existing strict numeric sufficiency gate remains intentionally strict:
  `all_bin_source_rows_adequate_decision_use_allowed_true_min_100_events_per_bin`.
- The new production-eligibility preflight evaluates the first PRS production path:
  `edge_norm_1d_primary_xz_norm_2d_diagnostic_no_auto_promotion`.

The current shard source is eligible for an edge-primary PRS production path, while
`xz_norm_2d` remains diagnostic-only and is not authorized for primary promotion.

## Inputs

- candidate source:
  `tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk027_20260618/NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_20260618.csv`
- candidate source SHA256:
  `069d8ed4f55e44bc5567225e6eaac9e95a9d9512898ddda294500205aaf08fb7`

## Output Bundle

- output dir:
  `tmp/nodi_position_response_source_production_eligibility_20260618/`
- report:
  `tmp/nodi_position_response_source_production_eligibility_20260618/NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY_REPORT_20260618.json`
- report SHA256:
  `aa8140a4d47b46cb7328c3e3504130963bdfecd857a2a9eeadb7da7d8bc7930e`
- candidates CSV SHA256:
  `41f8e45de455d2e162e9fd400f753b483543bbd5aac9768f1ab150bb6e4dfa56`
- groups CSV SHA256:
  `82e9f486c8f9afc98d6a1d43b4b467ba943d3dada5c35f7ffa7f5fe9410b70a8`
- blockers CSV SHA256:
  `339bddb105ccbf0c9d5d32baa1c09ce46b5b53a313c5992d2d34cebd57f60bb0`
- issues CSV SHA256:
  `9b1eeccafea4928aa6e005f037f75c91de6c8b09ba5ba7346d875f90edf2d26a`

## Evidence

- candidate count: 1
- eligible candidate count: 1
- candidate status:
  `edge_primary_source_eligible_xz_diagnostic_preflight_only`
- source scope status:
  `production_candidate_scope`
- candidate rows: 5604
- route/diameter/view/seed groups: 12
- group status counts:
  - `edge_primary_group_eligible_xz_diagnostic_only`: 12
- edge primary rows: 276
- edge primary eligible rows: 276
- edge primary ineligible rows: 0
- xz diagnostic rows: 5328
- xz sparse-or-empty diagnostic rows: 2912
- validation issue count: 0
- blockers: none
- issues: none

## Boundary

This preflight did not generate `NODI_POSITION_RESPONSE_SURFACE` rows. It did not
run NODI, run COMSOL, regenerate `JOINT_ROUTE_CLASS`, apply q_ch weighting, compute
yield, choose a winner, compute detection probability, claim true W_eff, claim
measured geometry, claim optical solver output, claim fabrication release, or claim
P3 solver conclusions.

The `xz_norm_2d` rows are explicitly diagnostic-only in this gate. Sparse/empty xz
rows do not block edge-primary eligibility, but they also do not become primary
production evidence and do not authorize `xz_norm_primary_if_adequate`.

## Verification

- `python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -k "production_eligibility or source_sufficiency"`:
  7 passed.
- `python -m py_compile tools/audits/run_nodi_position_response_source_production_eligibility_preflight.py nodi_simulator/nodi_comsol_next_artifacts.py`:
  pass.
- `python -m ruff check nodi_simulator/nodi_comsol_next_artifacts.py tests/test_nodi_comsol_next_artifacts_contracts.py tools/audits/run_nodi_position_response_source_production_eligibility_preflight.py`:
  pass.
- `validate_position_response_source_production_eligibility_report(...)` on the
  emitted report:
  `[]`.
- Negative artifact scan in the output directory found no
  `NODI_POSITION_RESPONSE_SURFACE`, `JOINT_ROUTE_CLASS`, or `COMSOL` files.

## Next Stop Point

The next technical step is PRS production-row builder design for an edge-primary,
xz-diagnostic artifact. That builder must collapse seed-level source rows only under
the explicit edge-primary policy, retain xz diagnostic semantics, and continue to
reject q_ch weighting, yield, winner, detection-probability, COMSOL transport, and
true-W_eff claims.
