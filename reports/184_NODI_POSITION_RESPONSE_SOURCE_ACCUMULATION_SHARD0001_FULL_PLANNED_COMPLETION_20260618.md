# Report 184: NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_SHARD0001_FULL_PLANNED_COMPLETION

Date: 2026-06-18

## Purpose

Complete the planned event accumulation for the first PRS source-accumulation campaign shard:

```text
PRS_ACCUM_CAMPAIGN_SHARD_0001
```

This report records full planned event-count completion, not production `NODI_POSITION_RESPONSE_SURFACE` generation.

## Execution

Starting checkpoint:

```text
tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk015_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_EVENTS_20260618.csv
```

Command:

```bash
python tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator_batch.py \
  --confirm-accumulator-batch \
  --readiness-report tmp/nodi_position_response_source_accumulation_campaign_runner_readiness_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_REPORT_20260618.json \
  --initial-events tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk015_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_EVENTS_20260618.csv \
  --start-chunk-index 16 \
  --chunk-count 12 \
  --n-events-per-job 2000 \
  --batch-output-dir tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_batch_chunk016_027_20260618
```

Result:

- batch status: `PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH_NOT_PRODUCTION`
- completed_chunk_count: `12`
- final_accumulated_event_count: `529344`
- planned_campaign_shard_event_count: `529200`
- full_campaign_shard_completed: `true`

The final accumulated event count is 144 above plan because the checkpoint runner advances in whole chunks of 12 selected jobs x 2000 events/job.

## Chunk Summary

| chunk | accumulated_event_count | full_campaign_shard_completed | numeric sufficiency |
| --- | ---: | --- | --- |
| chunk016 | 265344 | false | `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT` |
| chunk017 | 289344 | false | `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT` |
| chunk018 | 313344 | false | `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT` |
| chunk019 | 337344 | false | `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT` |
| chunk020 | 361344 | false | `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT` |
| chunk021 | 385344 | false | `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT` |
| chunk022 | 409344 | false | `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT` |
| chunk023 | 433344 | false | `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT` |
| chunk024 | 457344 | false | `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT` |
| chunk025 | 481344 | false | `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT` |
| chunk026 | 505344 | false | `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT` |
| chunk027 | 529344 | true | `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT` |

## Final Checkpoint

```text
tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk027_20260618/
```

Key files:

- accumulated events:
  `NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_EVENTS_20260618.csv`
- accumulated bin source:
  `NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_20260618.csv`
- accumulator report:
  `NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_REPORT_20260618.json`

Key hashes:

- chunk027 report SHA256:
  `b4b61e4333dc3f95337d8718c7be44c4a0d726b646327b974974c0fb23452178`
- chunk027 accumulated events SHA256:
  `aa630402d5afdb8ff5e2f6bb2bd5e8be79f661774797017e330f7fe5cf5880c3`
- chunk027 accumulated source SHA256:
  `069d8ed4f55e44bc5567225e6eaac9e95a9d9512898ddda294500205aaf08fb7`
- chunk016-027 batch report SHA256:
  `0f122d2d27bcdbb7837e4c6ea45e5b1e583f95fba125808b286d1d2e0299da8e`

## Validation

Final artifact checks:

- accumulated event rows: `529344`
- unique event ids: `529344`
- bin-source rows: `5604`
- `validate_position_response_bin_source_event_rows(...)`: no issues
- `validate_position_response_bin_source_rows(...)`: no issues
- source availability: `PASS_PRS_SOURCE_AVAILABILITY_PREFLIGHT_NOT_PRODUCTION`
- numeric sufficiency: `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT`
- numeric_sufficient_candidate_count: `0`

No `NODI_POSITION_RESPONSE_SURFACE*`, `JOINT_ROUTE_CLASS*`, or COMSOL output file was found in chunk016 through chunk027 output directories.

## Why Production PRS Is Still Blocked

The planned event count is complete, but the current numeric sufficiency validator requires every bin-source row to be adequate:

```text
bin_sample_status=adequate
decision_use_allowed=true
sparse_bin_flag=false
n_events_bin>=100
```

Final bin-source status:

| distribution | rows | empty rows | rows below 100 | min n_events_bin |
| --- | ---: | ---: | ---: | ---: |
| `edge_norm_1d` | 276 | 0 | 0 | 109 |
| `xz_norm_2d` | 5328 | 672 | 2912 | 0 |

Overall:

- adequate rows: `2692`
- sparse rows: `2240`
- empty rows: `672`
- decision_use_allowed=true rows: `2692`
- decision_use_allowed=false rows: `2912`

This means `edge_norm_1d` is sufficient, but `xz_norm_2d` base bins remain sparse/empty under the current event distribution and validator policy.

## Boundary

This report does not authorize production `NODI_POSITION_RESPONSE_SURFACE` generation.

The final accumulator report records:

- `position_response_surface_production_generated=false`
- `production_generation_performed=false`
- `comsol_run_performed=false`
- `joint_route_class_regenerated=false`

No COMSOL run was performed.
No `JOINT_ROUTE_CLASS` regeneration was performed.
No production PRS was generated.

## Stop Point

The planned accumulation step is complete.

The next blocker is policy/contract-level numeric sufficiency:

```text
BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT
```

The next design decision is whether production PRS should require all `xz_norm_2d` base bins to be adequate, or whether a narrower production surface such as `edge_norm_1d` / aggregate-only / reachable-bin-only should be contracted before PRS generation.
