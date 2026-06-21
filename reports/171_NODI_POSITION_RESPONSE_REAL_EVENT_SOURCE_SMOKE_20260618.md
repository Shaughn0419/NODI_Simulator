# Report 171 - NODI position-response real-event source smoke

Date: 2026-06-18

Status: PASS_REAL_EVENT_SOURCE_SMOKE_WITH_PRS_PRODUCTION_STOP

Scope:
- Add a bounded NODI real-event source smoke path.
- Convert real `run_single_case_batch` slim event payloads into PRS event-row source input.
- Build a bin-conditioned source candidate from those real event rows.
- Run source-availability preflight only.
- Do not generate production `NODI_POSITION_RESPONSE_SURFACE`.

## Boundary

This report does not authorize or claim:
- COMSOL run.
- `JOINT_ROUTE_CLASS` regeneration.
- production `NODI_POSITION_RESPONSE_SURFACE`.
- `q_ch * eta`, yield, winner, or detection-probability claims.
- true `W_eff`, measured geometry, optical solver output, fabrication release, or P3 solver conclusion.

`PASS_PRS_SOURCE_AVAILABILITY_PREFLIGHT_NOT_PRODUCTION` in this report means structural source availability only. It does not mean numeric production sufficiency.

## Code Artifacts

Primary implementation:
- `nodi_simulator/nodi_comsol_next_artifacts.py`
  - SHA256: `8b0d06659ae5e2f31bbcace045bf1dd58edfa5044c5816fa760adecea9d78d87`
- `tools/audits/run_nodi_position_response_real_event_source_smoke.py`
  - SHA256: `d094bb189fb2f51e6e599ec47ab88b1d0d8107de6a6eb15c8086b6add4939495`
- `tests/test_nodi_comsol_next_artifacts_contracts.py`
  - SHA256: `95c78b3f5b6371ec25609233e2b3a5303dada5c2eb48d2c61d56b85b017f456a`

## Implemented Semantics

New converter:

`build_position_response_event_rows_from_nodi_events(...)`

It converts NODI slim event payloads into PRS event-row input with:
- `route_id_nodi`
- `lambda_nm`
- `W_nominal_nm`
- `D_nm`
- `diameter_nm`
- `NODI_view`
- `seed`
- `event_id`
- `x_norm`
- `z_norm`
- `response_detected`
- `particle_kind`
- `source_scope`
- `source_event_kind`
- `response_detected_basis`

`response_detected` is a boolean event response derived from final event features:

`final_features_n_peaks_gt_0`

It is not a detection probability, yield, winner, or weighted transport claim.

New CLI:

`tools/audits/run_nodi_position_response_real_event_source_smoke.py`

The CLI requires:

`--confirm-real-event-source-smoke`

It runs one bounded NODI single-case batch, writes real event rows, builds a bin-conditioned source candidate, and writes source-preflight sidecars. The CLI has no COMSOL or `JOINT_ROUTE_CLASS` execution option.

## Smoke Execution

Command:

```bash
python tools/audits/run_nodi_position_response_real_event_source_smoke.py \
  --confirm-real-event-source-smoke \
  --output-dir tmp/nodi_position_response_real_event_source_smoke_20260618 \
  --overwrite-output
```

Result:
- Status: `PASS_PRS_REAL_EVENT_SOURCE_SMOKE_PREFLIGHT_ONLY_NOT_PRS_PRODUCTION`
- Route: `404/W500/D900`
- Diameter: `150 nm`
- NODI view: `fixed_660_gold`
- Seed: `11`
- Particle kind: `exosome_150nm`
- Real event rows: `6`
- Bin source rows: `467`
- Source scope: `production_candidate_from_real_nodi_event_export`
- Bounded NODI single-case smoke performed: `true`
- Full runner execution performed: `false`
- Production PRS generated: `false`

Files:
- `tmp/nodi_position_response_real_event_source_smoke_20260618/NODI_POSITION_RESPONSE_REAL_EVENT_SOURCE_SMOKE_EVENTS_20260618.csv`
  - SHA256: `1d73b4cd3bba41eca2dd48103b3abdf32b9d00cf13f7ad3e67663944c64d4df3`
- `tmp/nodi_position_response_real_event_source_smoke_20260618/NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_REAL_EVENT_SMOKE_20260618.csv`
  - SHA256: `03f831de6140027e46c11d2be4fd796800dbf1bd2082e23c0e1d5c0cc2b539e0`
- `tmp/nodi_position_response_real_event_source_smoke_20260618/NODI_POSITION_RESPONSE_REAL_EVENT_SOURCE_SMOKE_REPORT_20260618.json`
  - SHA256: `388eabbc9a325b1a8e16e20c2b3a83797e1fe3a4545b290fd733fd23055c9824`

## Source Preflight

The smoke CLI then ran source-availability preflight on the real-event bin source.

Result:
- Source preflight status: `PASS_PRS_SOURCE_AVAILABILITY_PREFLIGHT_NOT_PRODUCTION`
- Candidate status: `source_available_preflight_only`
- Source scope status: `production_candidate_scope`
- Source-available candidate count: `1`
- Response-count status: `available_bin_count_columns`
- Missing requirements: none
- Production PRS generated: `false`

Files:
- `tmp/nodi_position_response_real_event_source_smoke_20260618/NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_REPORT_20260618.json`
  - SHA256: `ead248d096526eb27616ae3b03220795c3e9b82cced90e45114936071afdfd74`
- `tmp/nodi_position_response_real_event_source_smoke_20260618/NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_CANDIDATES_20260618.csv`
  - SHA256: `542b9d3abfd336a3d50e5f866c6e57c3e5c72f6a7253e4b17a96736823933578`
- `tmp/nodi_position_response_real_event_source_smoke_20260618/NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_BLOCKERS_20260618.csv`
  - SHA256: `0f4f76c51e190b79920a5245c7c85b91e1becc664d1b5340af89ecc9271d527b`
- `tmp/nodi_position_response_real_event_source_smoke_20260618/NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_ISSUES_20260618.csv`
  - SHA256: `9b1eeccafea4928aa6e005f037f75c91de6c8b09ba5ba7346d875f90edf2d26a`

No `NODI_POSITION_RESPONSE_SURFACE.csv` exists in the output directory.

## Sparse Smoke Boundary

The real-event smoke source uses only 6 events, so it is deliberately sparse:
- `decision_use_allowed` values: `false`
- `bin_sample_status` values: `empty`, `sparse`

Therefore:
- The preflight PASS is structural only.
- This source proves wiring from real NODI events into the source-builder/preflight layer.
- This source must not be used to emit production PRS rows or to make numeric PRS claims.

## Independent Review

Subagent verifier:
- Verdict: `PASS_WITH_NOTES`
- Accepted:
  - Converter is a narrow event-to-source-row transform.
  - `response_detected` remains a boolean event response, not probability/yield/winner.
  - CLI is confirm-gated and bounded.
  - Smoke report is preflight-only and records no COMSOL, no `JOINT_ROUTE_CLASS`, no production PRS.
  - `source_scope=production_candidate_from_real_nodi_event_export` is acceptable as a scope label because it is paired with `preflight_only=true`, `source_available_preflight_only`, and `no_prs_production_artifact=true`.
  - Sparse bins show `decision_use_allowed=false`.
- Notes addressed before this report:
  - Added automated test coverage for missing-confirm CLI rejection.
  - Added automated test coverage that sparse source rows have `decision_use_allowed=false`.
- Remaining caution:
  - When summarized elsewhere, say "structural source availability only"; do not phrase the preflight PASS as numeric production readiness.

## Verification

Static and focused checks:

```bash
python -m py_compile \
  nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/run_nodi_position_response_real_event_source_smoke.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py
```

Result: PASS

```bash
ruff check \
  nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/run_nodi_position_response_real_event_source_smoke.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py
```

Result: PASS

```bash
python -m pyright \
  nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/run_nodi_position_response_real_event_source_smoke.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py
```

Result: PASS (`0 errors, 0 warnings, 0 informations`)

```bash
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
```

Result: PASS (`89 passed in 38.22s`)

Full regression:

```bash
python tests/run_tests.py --workers 7
```

Result: PASS (`1538 passed in 91.23s`)

## Stop Point

NODI now has a validated wiring path from real single-case NODI event payloads into:

`event rows -> bin-conditioned source candidate -> source-availability preflight`

Production `NODI_POSITION_RESPONSE_SURFACE` remains stopped.

Next implementation gate:
- Add a bounded production-candidate event export mode to the real runner path for selected route/view/seed slices.
- Require sufficient per-bin sample support before allowing PRS production rows.
- Keep `decision_use_allowed=false` rows out of production PRS generation unless a later contract explicitly defines how to handle sparse bins.
