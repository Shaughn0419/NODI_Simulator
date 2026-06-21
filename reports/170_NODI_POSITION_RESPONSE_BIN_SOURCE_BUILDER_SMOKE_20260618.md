# Report 170 - NODI position-response bin-source builder smoke stop point

Date: 2026-06-18

Status: PASS_SOURCE_BUILDER_SMOKE_WITH_PRS_PRODUCTION_STOP

Scope:
- Implement the NODI-side position-response bin-conditioned source builder layer.
- Exercise it only with a bounded smoke fixture.
- Feed the smoke source into source-availability preflight and verify it remains non-production.
- Do not emit production `NODI_POSITION_RESPONSE_SURFACE`.

## Boundary

This report does not authorize or claim:
- COMSOL run.
- NODI production position-response generation.
- `JOINT_ROUTE_CLASS` regeneration.
- `q_ch * eta`, yield, winner, or detection-probability claims.
- true `W_eff`, measured geometry, optical solver output, fabrication release, or P3 solver conclusion.

The implemented layer is source-builder/preflight infrastructure only.

## Code Artifacts

Primary implementation:
- `nodi_simulator/nodi_comsol_next_artifacts.py`
  - SHA256: `17a8c926afc2fbd52c2c02e8fad4e50f9f21e1c0cc6275683c33b927e26336e1`
- `tools/audits/build_nodi_position_response_bin_source.py`
  - SHA256: `a66d24bda10129fa3613bffc71aa12792676eb68adf71b7c187e9f6ab86b41cd`
- `tools/audits/run_nodi_position_response_source_preflight.py`
  - SHA256: `febc7a08a7ac5bff0e1a44501c8a2171ee26c07766a9473dc7d0b4053c1f84e8`
- `tests/test_nodi_comsol_next_artifacts_contracts.py`
  - SHA256: `bed19da70026e7e8ecdc6481e7192b11dbc1b1580f559ecbe22a8f8251ff21d3`

## Implemented Semantics

`build_position_response_bin_source_rows_from_events(...)` aggregates event-level rows into
`NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_V1` rows at:

`route_id_nodi x diameter_nm x NODI_view x seed x distribution/bin`

For each `route_id_nodi x diameter_nm x NODI_view x seed` group, the builder emits:
- 20 `edge_norm_1d` base bins.
- 441 `xz_norm_2d` base bins.
- 6 special aggregates.

Expected rows per group: `467`.

The source rows include:
- `n_events_total_seed`
- `n_events_bin`
- `response_count_bin`
- `response_rate_bin`
- `bin_sample_status`
- `decision_use_allowed`
- `preflight_only=true`
- `production_prs_generated=false`
- `not_qch_weighted=true`
- `not_yield=true`
- `not_detection_probability=true`

Production source scope is explicitly separated from bounded smoke scope:
- Production-eligible scope: `production_candidate_from_real_nodi_event_export`
- Smoke scope: `bounded_smoke_fixture_not_production`

Source availability preflight now requires real response-count support. `n_events_bin` alone is not enough to unlock the gate; a candidate must expose `response_count_bin`, `n_detected_bin`, or event-level rows.

## Smoke Output

Command:

```bash
python tools/audits/build_nodi_position_response_bin_source.py \
  --confirm-smoke-source \
  --output-dir tmp/nodi_position_response_bin_source_smoke_20260618
```

Result:
- Status: `PASS_PRS_BIN_SOURCE_SMOKE_NOT_PRODUCTION`
- Event rows: `6`
- Bin-source rows: `467`
- Source scope: `bounded_smoke_fixture_not_production`

Files:
- `tmp/nodi_position_response_bin_source_smoke_20260618/NODI_POSITION_RESPONSE_BIN_SOURCE_SMOKE_EVENTS_20260618.csv`
  - SHA256: `8218c7f4ff07fcd9db7fcf33a173a11d7efdf533236a5d4a1ca9b53056e15c74`
- `tmp/nodi_position_response_bin_source_smoke_20260618/NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_SMOKE_20260618.csv`
  - SHA256: `f188c40e962c740f1bb720041ad11ffea0aeb26d216c94186b98b6f45fd5005b`
- `tmp/nodi_position_response_bin_source_smoke_20260618/NODI_POSITION_RESPONSE_BIN_SOURCE_SMOKE_REPORT_20260618.json`
  - SHA256: `ed2ece810713e8b9f07b6675818409d013ba75516ea68ead070d67764bfcb1b1`

No `NODI_POSITION_RESPONSE_SURFACE.csv` was created by the smoke writer.

## Smoke Source Preflight

Command:

```bash
python tools/audits/run_nodi_position_response_source_preflight.py \
  --confirm-source-preflight \
  --candidate tmp/nodi_position_response_bin_source_smoke_20260618/NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_SMOKE_20260618.csv \
  --output-dir tmp/nodi_position_response_bin_source_smoke_preflight_20260618
```

Expected non-zero exit: yes. The preflight must remain blocked because the candidate is a bounded smoke source.

Result:
- Status: `BLOCKED_PRS_SOURCE_AVAILABILITY_PREFLIGHT`
- Candidate count: `1`
- Source-available candidate count: `0`
- Candidate status: `source_shape_available_not_production_eligible`
- Source scope status: `bounded_smoke_scope_not_production_eligible`
- Response-count status: `available_bin_count_columns`
- Distribution/bin status: `available_distribution_bin_columns`
- Production PRS generated: `false`

Files:
- `tmp/nodi_position_response_bin_source_smoke_preflight_20260618/NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_REPORT_20260618.json`
  - SHA256: `d7a818dd72a2ac7460e0ae8205a658f60c4c48ef26b336ff073c079bf64631fe`
- `tmp/nodi_position_response_bin_source_smoke_preflight_20260618/NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_CANDIDATES_20260618.csv`
  - SHA256: `29ce3f05096e51082b08e34c65b81f0539c93029aa375e6bdc962ef005c063db`

No `NODI_POSITION_RESPONSE_SURFACE.csv` exists in the preflight output directory.

## Independent Review

Subagent exploration:
- Conclusion: no existing persisted production-eligible event/bin source was found.
- Existing raw/diagnostic artifacts are route-level and must not be promoted into PRS production source rows.
- Recommended next hook: add real event-level export from the NODI runner path, then feed it through the source builder and preflight gates.

Independent verifier review:
- Verdict: `PASS_WITH_NOTES`
- Accepted:
  - Builder aggregates event-level rows into bin-conditioned source rows.
  - Smoke source is marked `bounded_smoke_fixture_not_production`.
  - Smoke source does not unlock production source preflight.
  - Source preflight report remains blocked and produces no PRS surface.
  - No COMSOL run, `JOINT_ROUTE_CLASS` regeneration, `q_ch * eta`, yield, winner, detection probability, true `W_eff`, measured geometry, or optical solver claim was introduced.
- Note addressed in this report:
  - Added an explicit negative regression for candidates that expose `n_events_bin` only, without `response_count_bin`, `n_detected_bin`, or event-level rows.
- Remaining non-blocking note:
  - Source availability preflight is structural. It does not fully validate numeric production adequacy for arbitrary external source files. That must remain part of a future production source validator/runner gate before production PRS rows are emitted.

## Verification

Static and focused checks:

```bash
python -m py_compile \
  nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/build_nodi_position_response_bin_source.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py
```

Result: PASS

```bash
ruff check \
  nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/build_nodi_position_response_bin_source.py \
  tools/audits/run_nodi_position_response_source_preflight.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py
```

Result: PASS

```bash
python -m pyright \
  nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/build_nodi_position_response_bin_source.py \
  tools/audits/run_nodi_position_response_source_preflight.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py
```

Result: PASS (`0 errors, 0 warnings, 0 informations`)

```bash
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
```

Result: PASS (`86 passed in 35.31s`)

Full regression:

```bash
python tests/run_tests.py --workers 7
```

Result: PASS (`1535 passed in 93.84s`)

## Stop Point

NODI has a validated PRS bin-source builder and smoke/preflight boundary.

Production `NODI_POSITION_RESPONSE_SURFACE` remains blocked until a real NODI event export is provided or regenerated with:
- `route_id_nodi`
- `diameter_nm`
- `NODI_view`
- `seed`
- event position or distribution/bin fields
- response-count support
- `source_scope=production_candidate_from_real_nodi_event_export`

The next implementation gate is real event-export wiring from the NODI runner path into this source-builder/preflight layer.
