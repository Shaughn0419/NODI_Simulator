# Report 182: NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BATCH_CHUNK004_006_AND_IO_LIMIT_FIX

Date: 2026-06-18

## Purpose

Continue `PRS_ACCUM_CAMPAIGN_SHARD_0001` accumulation more efficiently by adding a sequential batch runner for multiple checkpointed accumulator chunks.

This report also records a real I/O blocker discovered during batch execution and the fix that allowed accumulation to continue.

## Implemented Artifacts

- Batch runner: `tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator_batch.py`
- I/O fix: `nodi_simulator/realism_v2_io.py`
- Regression test: `tests/test_realism_v2_io.py`

The batch runner delegates each chunk to the already-reviewed accumulator. It does not generate production `NODI_POSITION_RESPONSE_SURFACE`, run COMSOL, or regenerate `JOINT_ROUTE_CLASS`.

## I/O Blocker And Fix

The first batch attempt requested `chunk004-006`.

Observed result:

- `chunk004`: PASS, accumulated_event_count `13344`
- `chunk005`: PASS, accumulated_event_count `19344`
- `chunk006`: BLOCKED before report generation

Blocker:

```text
_csv.Error: field larger than field limit (131072)
```

Cause:

As accumulated PRS source rows grow, the `source_event_rows` field can exceed Python CSV's default field limit. This is expected for accumulated bin-source sidecars because each bin row preserves event provenance.

Fix:

```python
csv.field_size_limit(16 * 1024 * 1024)
```

The fix is now applied in `nodi_simulator/realism_v2_io.py`.

Regression coverage:

```text
test_read_csv_rows_accepts_large_accumulated_source_fields
```

## Continued Execution

After the I/O fix, `chunk006` was resumed from the last valid checkpoint:

```text
tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk005_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_EVENTS_20260618.csv
```

Command:

```bash
python tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator_batch.py \
  --confirm-accumulator-batch \
  --readiness-report tmp/nodi_position_response_source_accumulation_campaign_runner_readiness_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_REPORT_20260618.json \
  --initial-events tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk005_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_EVENTS_20260618.csv \
  --start-chunk-index 6 \
  --chunk-count 1 \
  --n-events-per-job 500 \
  --batch-output-dir tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_batch_chunk006_20260618 \
  --overwrite-output
```

Final chunk states:

| chunk | status | accumulated_event_count | numeric sufficiency |
| --- | --- | ---: | --- |
| chunk004 | `PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_NOT_PRODUCTION` | 13344 | `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT` |
| chunk005 | `PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_NOT_PRODUCTION` | 19344 | `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT` |
| chunk006 | `PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_NOT_PRODUCTION` | 25344 | `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT` |

Final batch status:

```text
PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH_NOT_PRODUCTION
```

Final checkpoint:

```text
tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk006_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_EVENTS_20260618.csv
```

## Current Accumulation State

- selected_campaign_shard_id: `PRS_ACCUM_CAMPAIGN_SHARD_0001`
- accumulated_event_count: `25344`
- planned_campaign_shard_event_count: `529200`
- completion fraction: `4.79%`
- bin_source_rows: `5604`
- source availability: `PASS_PRS_SOURCE_AVAILABILITY_PREFLIGHT_NOT_PRODUCTION`
- source numeric sufficiency: `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT`
- numeric_sufficient_candidate_count: `0`

## Key Hashes

- chunk004 report SHA256: `d779c533a1c24dd9282802e1717b80f7bc1a9dd2d0fd0a507777739130a1ad07`
- chunk005 report SHA256: `77f9de1a50ef25422d9233ee4c02d9c146b7b22a5419c3df1ffabb806ac3b341`
- chunk006 report SHA256: `fe59748cbf2372062a8b13a1ad0467461b7b40bbd7233dd59a213880bea3c630`
- chunk006 batch report SHA256: `4221c87440b5ae54852ac80e9ad89b18b480359e7566a7b0b6251892d08c3ad9`
- chunk006 accumulated events SHA256: `6c2f2cddbe7c373d33b52e4ee33dd1fc0c8731ee9beaa673ca5d97941d84785c`
- chunk006 accumulated source SHA256: `6e6477298952ad8a877ed9704c8cf488433e2e5034793197937a5e786e210db8`

## Boundary

The latest checkpoint remains non-production:

- `position_response_surface_production_generated=false`
- `production_generation_performed=false`
- `comsol_run_performed=false`
- `joint_route_class_regenerated=false`

No `NODI_POSITION_RESPONSE_SURFACE*`, `JOINT_ROUTE_CLASS*`, or COMSOL output file was found in the chunk004, chunk005, or chunk006 output directories.

## Validation

Static and focused tests:

```bash
python -m py_compile nodi_simulator/realism_v2_io.py \
  tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator.py \
  tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator_batch.py \
  tests/test_realism_v2_io.py

ruff check nodi_simulator/realism_v2_io.py \
  tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator.py \
  tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator_batch.py \
  tests/test_realism_v2_io.py

python -m pyright nodi_simulator/realism_v2_io.py \
  tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator.py \
  tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator_batch.py \
  tests/test_realism_v2_io.py

python -m pytest tests/test_realism_v2_io.py -q \
  -k "large_accumulated_source_fields or csv_artifact_helpers"
```

Results:

- `py_compile`: pass
- `ruff`: pass
- `pyright`: `0 errors, 0 warnings, 0 informations`
- focused pytest: `2 passed, 6 deselected`

Final artifact checks:

- final accumulated event rows: `25344`
- unique event ids: `25344`
- final bin-source rows: `5604`
- `validate_position_response_bin_source_event_rows(...)`: no issues
- `validate_position_response_bin_source_rows(...)`: no issues

Full repository regression was intentionally not run for this accumulation batch step.

## Stop Point

The current stop point remains numeric sufficiency:

```text
BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT
```

No production `NODI_POSITION_RESPONSE_SURFACE` generation is authorized.
