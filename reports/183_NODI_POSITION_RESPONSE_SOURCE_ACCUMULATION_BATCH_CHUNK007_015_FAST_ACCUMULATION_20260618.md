# Report 183: NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BATCH_CHUNK007_015_FAST_ACCUMULATION

Date: 2026-06-18

## Purpose

Continue `PRS_ACCUM_CAMPAIGN_SHARD_0001` accumulation more efficiently by raising the accumulator chunk ceiling from 500 to 2000 events per selected job.

This keeps the same checkpointed, non-production workflow:

- each chunk writes its own event/source/report checkpoint
- source availability and numeric sufficiency are rerun after each chunk
- no production `NODI_POSITION_RESPONSE_SURFACE` is generated
- COMSOL is not run
- `JOINT_ROUTE_CLASS` is not regenerated

## Implemented Change

Updated:

```text
tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator.py
```

Change:

```text
MAX_EVENTS_PER_JOB_PER_CHUNK = 2000
```

## Static Validation

```bash
python -m py_compile \
  tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator.py \
  tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator_batch.py

ruff check \
  tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator.py \
  tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator_batch.py

python -m pyright \
  tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator.py \
  tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator_batch.py
```

Results:

- `py_compile`: pass
- `ruff`: pass
- `pyright`: `0 errors, 0 warnings, 0 informations`

## Batch Results

### chunk007-009

Command:

```bash
python tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator_batch.py \
  --confirm-accumulator-batch \
  --readiness-report tmp/nodi_position_response_source_accumulation_campaign_runner_readiness_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_REPORT_20260618.json \
  --initial-events tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk006_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_EVENTS_20260618.csv \
  --start-chunk-index 7 \
  --chunk-count 3 \
  --n-events-per-job 2000 \
  --batch-output-dir tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_batch_chunk007_009_20260618
```

Result:

- batch status: `PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH_NOT_PRODUCTION`
- completed_chunk_count: `3`
- final_accumulated_event_count: `97344`
- final batch report SHA256: `174cc8599e1a5c8f7cb061a89b33a264b312222e2f48837df461f524ce23eb79`

Chunk states:

| chunk | previous | chunk events | accumulated | status |
| --- | ---: | ---: | ---: | --- |
| chunk007 | 25344 | 24000 | 49344 | PASS |
| chunk008 | 49344 | 24000 | 73344 | PASS |
| chunk009 | 73344 | 24000 | 97344 | PASS |

### chunk010-012

Result:

- batch status: `PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH_NOT_PRODUCTION`
- completed_chunk_count: `3`
- final_accumulated_event_count: `169344`
- final batch report SHA256: `2e73528d6983674f5459e37e31244424d079bceac3813b8212e991704a1aa0b8`

Chunk states:

| chunk | previous | chunk events | accumulated | status |
| --- | ---: | ---: | ---: | --- |
| chunk010 | 97344 | 24000 | 121344 | PASS |
| chunk011 | 121344 | 24000 | 145344 | PASS |
| chunk012 | 145344 | 24000 | 169344 | PASS |

### chunk013-015

Result:

- batch status: `PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH_NOT_PRODUCTION`
- completed_chunk_count: `3`
- final_accumulated_event_count: `241344`
- final batch report SHA256: `86ba5c5472039af7d10970da37d63b35ed303ab9857d0859424b1a17a1647217`

Chunk states:

| chunk | previous | chunk events | accumulated | status |
| --- | ---: | ---: | ---: | --- |
| chunk013 | 169344 | 24000 | 193344 | PASS |
| chunk014 | 193344 | 24000 | 217344 | PASS |
| chunk015 | 217344 | 24000 | 241344 | PASS |

## Current State

- selected_campaign_shard_id: `PRS_ACCUM_CAMPAIGN_SHARD_0001`
- accumulated_event_count: `241344`
- planned_campaign_shard_event_count: `529200`
- completion fraction: `45.61%`
- bin_source_rows: `5604`
- source availability: `PASS_PRS_SOURCE_AVAILABILITY_PREFLIGHT_NOT_PRODUCTION`
- source numeric sufficiency: `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT`
- numeric_sufficient_candidate_count: `0`

Latest checkpoint:

```text
tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk015_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_EVENTS_20260618.csv
```

## Latest Hashes

- chunk015 report SHA256: `a2f358ac8d8984f9f2c19f591cfc44ef894ea2c9974a5aaeadaff2c52fb8df7b`
- chunk015 accumulated events SHA256: `5da4c13cbc5504c9a4dcc53111b49792a78ab125dbec73c6da14b4df0ad0810a`
- chunk015 accumulated source SHA256: `45a6901aa7f5cc6d0ea50ceb3217276ecd8da47ab195058b147c98609bc22b94`
- chunk015 batch report SHA256: `86ba5c5472039af7d10970da37d63b35ed303ab9857d0859424b1a17a1647217`

## Boundary

The latest checkpoint remains non-production:

- `position_response_surface_production_generated=false`
- `production_generation_performed=false`
- `comsol_run_performed=false`
- `joint_route_class_regenerated=false`

No `NODI_POSITION_RESPONSE_SURFACE*`, `JOINT_ROUTE_CLASS*`, or COMSOL output file was found in chunk007 through chunk015 output directories.

## Artifact Validation

Latest checkpoint checks:

- final accumulated event rows: `241344`
- unique event ids: `241344`
- final bin-source rows: `5604`
- `validate_position_response_bin_source_event_rows(...)`: no issues
- `validate_position_response_bin_source_rows(...)`: no issues

## Stop Point

The current stop point remains numeric sufficiency:

```text
BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT
```

No production `NODI_POSITION_RESPONSE_SURFACE` generation is authorized.
