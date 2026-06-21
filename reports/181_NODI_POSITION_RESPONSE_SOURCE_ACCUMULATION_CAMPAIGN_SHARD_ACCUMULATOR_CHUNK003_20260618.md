# Report 181: NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_CHUNK003

Date: 2026-06-18

## Purpose

Continue accumulation for `PRS_ACCUM_CAMPAIGN_SHARD_0001` using the already-reviewed campaign shard accumulator.

This is a repeated accumulator chunk, not a new production gate.

## Real Output

Command:

```bash
python tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator.py \
  --confirm-accumulate-campaign-shard \
  --readiness-report tmp/nodi_position_response_source_accumulation_campaign_runner_readiness_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_REPORT_20260618.json \
  --previous-events tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk002_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_EVENTS_20260618.csv \
  --chunk-id chunk003 \
  --n-events-per-job 500 \
  --output-dir tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk003_20260618
```

Result:

- status: `PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_NOT_PRODUCTION`
- selected_campaign_shard_id: `PRS_ACCUM_CAMPAIGN_SHARD_0001`
- selected_job_count: `12`
- previous_event_count: `1344`
- chunk_event_count: `6000`
- accumulated_event_count: `7344`
- planned_campaign_shard_event_count: `529200`
- bin_source_rows: `5604`
- source_availability_status: `PASS_PRS_SOURCE_AVAILABILITY_PREFLIGHT_NOT_PRODUCTION`
- source_numeric_sufficiency_status: `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT`
- numeric_sufficient_candidate_count: `0`

Output directory:

```text
tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk003_20260618/
```

Key hashes:

- report JSON SHA256: `bc27a228dbd43321a6ab37fc61f165fa9a478636b7f0e8c0c3b74ce7925a462e`
- accumulated events CSV SHA256: `444060b77d7b99ea00f009d4aa5c129c8276d09df8576b9c5e29c4a328023054`
- accumulated bin-source CSV SHA256: `df21e2e599248755ccc6a7d1d924875b5ef41a532adf2f4e90b4e9c2a6f02470`

## Boundary

The output remains non-production:

- `full_campaign_shard_completed=false`
- `position_response_surface_production_generated=false`
- `production_generation_performed=false`
- `comsol_run_performed=false`
- `joint_route_class_regenerated=false`

No `NODI_POSITION_RESPONSE_SURFACE*`, `JOINT_ROUTE_CLASS*`, or COMSOL output file was found in the chunk003 output directory.

## Validation

Focused artifact checks:

- accumulated event rows: `7344`
- unique event ids: `7344`
- bin-source rows: `5604`
- manifest rows: `12`
- `validate_position_response_bin_source_event_rows(...)`: no issues
- `validate_position_response_bin_source_rows(...)`: no issues
- manifest `production_prs_generated`: `false`

Numeric sufficiency remains blocked as expected:

```text
BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT
```

No production `NODI_POSITION_RESPONSE_SURFACE` generation is authorized.
