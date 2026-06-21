# Report 190 - New Thread Handoff: NODI Next Artifacts

Date: 2026-06-18

## Purpose

This handoff is for a new Codex thread. Read this file first, then continue from
the current NODI-side state without replaying the whole prior conversation.

The work concerns NODI/COMSOL next-artifacts handoff:

- `NODI_POSITION_RESPONSE_SURFACE`
- `NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY`

The current state is NODI-side local production complete, but not yet COMSOL-accepted
for downstream joint use.

## Current Disposition

NODI local status:

`PASS_PRODUCTION_GENERATION`

Most recent local decision:

`NODI_CAN_CONTINUE_LOCALLY_WITHOUT_COMSOL_REVIEW`

Important nuance:

COMSOL read-only review is recommended before downstream joint use, but it is not
a hard stop for NODI-side local cleanup, validation, packaging, manifest work, or
readiness checks.

## Hard Boundaries

Do not do any of the following unless there is a separate explicit future
authorization:

- run COMSOL
- run a new NODI physical/evidence rerun that changes claims
- regenerate `JOINT_ROUTE_CLASS`
- perform q_ch weighting or q_ch*eta
- compute yield
- choose a winner
- compute detection probability
- claim true W_eff
- claim measured geometry
- claim optical solver output
- claim fabrication release
- claim P3 solver conclusions

Do not present current NODI outputs as COMSOL-accepted joint artifacts. They are
NODI-side local production artifacts pending optional COMSOL read-only review before
joint use.

## What Was Completed

### PRS Source Accumulation

The PRS source accumulation campaign shard reached planned completion:

- final checkpoint:
  `tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk027_20260618/`
- accumulated events: 529344
- bin-conditioned source rows: 5604
- source SHA256:
  `069d8ed4f55e44bc5567225e6eaac9e95a9d9512898ddda294500205aaf08fb7`

Strict all-row numeric sufficiency remains blocked because `xz_norm_2d` diagnostic
bins include sparse/empty rows. This strict policy is intentionally retained:

`all_bin_source_rows_adequate_decision_use_allowed_true_min_100_events_per_bin`

### PRS Edge-Primary Eligibility

A separate eligibility policy was introduced:

`edge_norm_1d_primary_xz_norm_2d_diagnostic_no_auto_promotion`

This allows the first PRS production artifact to use edge-normalized primary rows
while keeping xz rows diagnostic-only.

Eligibility output:

- `tmp/nodi_position_response_source_production_eligibility_20260618/`
- report SHA256:
  `aa8140a4d47b46cb7328c3e3504130963bdfecd857a2a9eeadb7da7d8bc7930e`
- candidate rows: 5604
- eligible candidate count: 1
- route/diameter/view/seed groups: 12
- edge primary rows: 276
- edge primary eligible rows: 276
- xz diagnostic rows: 5328
- xz sparse-or-empty diagnostic rows: 2912
- xz primary promotion authorized: false

### PRS Edge-Primary Candidate

Production-shaped PRS candidate:

- output dir:
  `tmp/nodi_position_response_edge_primary_candidate_20260618/`
- candidate CSV:
  `tmp/nodi_position_response_edge_primary_candidate_20260618/NODI_POSITION_RESPONSE_SURFACE_EDGE_PRIMARY_CANDIDATE_20260618.csv`
- candidate CSV SHA256:
  `e584deecf43ac163f2a904782569143b3c4095bcb72dd439d598d652ee70869e`
- candidate report SHA256:
  `75aadf5a011245169499c8911219cf9b88b5a5558846d2179cf1accf9e9b079f`

Candidate row arithmetic:

- route/diameter/view grains: 4
- rows per route/diameter/view: 467
- total rows: 1868
- `edge_norm_1d` rows: 92
- `xz_norm_2d` rows: 1776
- `edge_norm_primary` rows: 92
- `xz_norm_diagnostic` rows: 1776
- `xz_norm_primary_if_adequate` rows: 0

Validation:

`validate_position_response_surface_rows(..., production_table=True, require_complete_row_arithmetic=True)` returned `[]`.

### Full Production Gate

Full NODI-side production output:

- output dir:
  `tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/`
- production report:
  `tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_20260618.json`
- production report SHA256:
  `12e3ba991b3ce1b3cf192f07c3291bc1ce338b202dcaa2d2ec3c493d0f7970f4`

Production artifacts:

- `NODI_POSITION_RESPONSE_SURFACE.csv`
  - rows: 1868
  - SHA256: `e584deecf43ac163f2a904782569143b3c4095bcb72dd439d598d652ee70869e`
- `NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv`
  - rows: 32
  - SHA256: `35c8b43e641631b682df07dc305ee17bc97384e6cf135c94adce791748243ecc`
- `NODI_EFFECTIVE_APERTURE_SURROGATE_SELECTOR_POLICY_20260618.json`
  - SHA256: `399e34aa40279c0fc47a335685ddedd6b159f98a1786bb03b3cb13b20466ad32`

Production gate boundaries:

- COMSOL run performed: false
- NODI run performed in this gate: false
- `JOINT_ROUTE_CLASS` regenerated: false
- q_ch weighted: false
- yield: false
- winner: false
- detection probability: false
- true W_eff: false
- measured geometry: false
- optical solver output: false
- fabrication release: false
- P3 solver conclusion: false

### Review Fix

Final independent review found one medium issue:

When `--position-response-candidate` was explicitly supplied but the file did not
exist, the report became blocked but did not produce a clean PRS blocker/status.

Fix applied:

- a PRS candidate is ready only if the path is supplied, exists, and validates cleanly
- missing candidate files now produce:
  - `BLOCKED_PRODUCTION_GENERATION_INPUTS`
  - `position_response_surface_status=blocked_missing_position_response_event_source`
  - blocker `blocked_invalid_position_response_candidate`

Regression tests were added for missing and invalid PRS candidates.

## Key Reports

Read these in order if context is needed:

- `reports/184_NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_SHARD0001_FULL_PLANNED_COMPLETION_20260618.md`
- `reports/185_NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY_EDGE_PRIMARY_PREFLIGHT_20260618.md`
- `reports/186_NODI_POSITION_RESPONSE_EDGE_PRIMARY_CANDIDATE_VALIDATION_20260618.md`
- `reports/187_NODI_NEXT_ARTIFACTS_FULL_PRODUCTION_GENERATION_PRS_EAS_20260618.md`
- `reports/188_NODI_NEXT_ARTIFACTS_PRODUCTION_GATE_REVIEW_FIX_20260618.md`
- `reports/189_NODI_NEXT_ARTIFACTS_CONTINUE_WITHOUT_COMSOL_REVIEW_20260618.md`

This handoff itself is:

- `reports/190_NEW_THREAD_HANDOFF_NODI_NEXT_ARTIFACTS_20260618.md`

## Important Code And CLI Entry Points

Core module:

- `nodi_simulator/nodi_comsol_next_artifacts.py`

Relevant CLIs:

- `tools/audits/run_nodi_position_response_source_production_eligibility_preflight.py`
- `tools/audits/build_nodi_position_response_edge_primary_candidate.py`
- `tools/audits/run_nodi_next_artifacts_production_generation.py`

Important helper fix:

- `nodi_simulator/realism_v2_io.py`
  - `csv.field_size_limit(16 * 1024 * 1024)` was added to support accumulated
    source rows with large `source_event_rows` fields.

Tests:

- `tests/test_nodi_comsol_next_artifacts_contracts.py`
- `tests/test_realism_v2_io.py`

## Verification Already Run

Latest verified commands:

```bash
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py
python -m pytest tests/test_realism_v2_io.py
python -m ruff check nodi_simulator/nodi_comsol_next_artifacts.py tests/test_nodi_comsol_next_artifacts_contracts.py tools/audits/run_nodi_next_artifacts_production_generation.py tools/audits/run_nodi_position_response_source_production_eligibility_preflight.py tools/audits/build_nodi_position_response_edge_primary_candidate.py nodi_simulator/realism_v2_io.py tests/test_realism_v2_io.py
```

Results:

- `tests/test_nodi_comsol_next_artifacts_contracts.py`: 141 passed
- `tests/test_realism_v2_io.py`: 8 passed
- ruff: pass

Earlier focused result:

- production/eligibility/source-sufficiency subset: 23 passed

## COMSOL Review Package

A COMSOL read-only review package has been prepared, but it is optional for local
NODI continuation:

- zip:
  `tmp/nodi_comsol_readonly_review_full_production_20260618.zip`
- zip SHA256:
  `b7924da8896bee47ac85052b329eeae65efe8adc11cc130eaed3104a934a4b6a`
- prompt:
  `reports/COMSOL_READONLY_REVIEW_PROMPT_NODI_NEXT_ARTIFACTS_FULL_PRODUCTION_20260618.md`
- prompt SHA256:
  `b82830033a1929a1a4395220ed763e2399dacb9acf237cee5a847a60a7a31567`

The zip was created with AppleDouble metadata excluded.

If sending to COMSOL, make clear this is read-only review only and does not
authorize COMSOL run, NODI rerun, or `JOINT_ROUTE_CLASS` regeneration.

## Local Handoff Manifest

Machine-readable local handoff manifest:

- path:
  `tmp/nodi_next_artifacts_local_handoff_manifest_20260618/NODI_NEXT_ARTIFACTS_LOCAL_HANDOFF_MANIFEST_20260618.json`
- SHA256:
  `44b37f6de23cdf6e1604f2d533357795b4711868df336115f549fe4baa650747`
- status:
  `NODI_LOCAL_HANDOFF_READY_WITHOUT_COMSOL_ACCEPTANCE`

It records 11 key files, their existence, hashes, and boundary flags.

## Recommended Next Steps For New Thread

Start with local work. Do not block on COMSOL unless the task explicitly asks for
joint downstream use.

Recommended sequence:

1. Re-run quick verification:

```bash
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py
python -m pytest tests/test_realism_v2_io.py
python -m ruff check nodi_simulator/nodi_comsol_next_artifacts.py tests/test_nodi_comsol_next_artifacts_contracts.py tools/audits/run_nodi_next_artifacts_production_generation.py tools/audits/run_nodi_position_response_source_production_eligibility_preflight.py tools/audits/build_nodi_position_response_edge_primary_candidate.py nodi_simulator/realism_v2_io.py tests/test_realism_v2_io.py
```

2. Add a local claim-boundary scanner for the production output package:
   - scan PRS/EAS/report JSON/CSV headers and values
   - assert no forbidden positive fields or statuses
   - assert COMSOL/JRC flags remain false

3. Add a package verifier for
   `tmp/nodi_comsol_readonly_review_full_production_20260618.zip`:
   - no `._*`
   - no `__MACOSX`
   - expected 26 files
   - hash matches

4. Consider creating a NODI-side downstream-readiness report:
   - status should be local-only
   - explicitly not COMSOL-accepted
   - no `JOINT_ROUTE_CLASS` regeneration

5. If user wants COMSOL review, send the prepared zip and prompt. Otherwise, continue
   with local validation/handoff hardening.

## Suggested First Message For New Thread

If starting a new thread, paste:

```text
Please read reports/190_NEW_THREAD_HANDOFF_NODI_NEXT_ARTIFACTS_20260618.md first.
Continue NODI-side local hardening from the current PASS_PRODUCTION_GENERATION state.
Do not run COMSOL, do not regenerate JOINT_ROUTE_CLASS, and do not claim COMSOL
acceptance. Start by verifying the handoff state and then proceed with local
claim-boundary/package validation.
```

## Current Best Stopping Point

The current stopping point is clean:

- NODI local production artifacts exist
- validators pass
- independent subagent reviews passed after one medium issue was fixed
- COMSOL review package exists
- local continuation without waiting for COMSOL is documented

The next work should be local hardening and handoff readiness, not more source
accumulation.
