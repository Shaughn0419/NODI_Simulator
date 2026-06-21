# Report 180: NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_CHUNK002

Date: 2026-06-18

## Purpose

Continue the authorized PRS source-accumulation campaign shard execution by appending a larger bounded chunk to the existing Report 179 event set.

This advances the same selected shard:

```text
PRS_ACCUM_CAMPAIGN_SHARD_0001
```

It remains a non-production accumulator step and does not generate `NODI_POSITION_RESPONSE_SURFACE`.

## Implemented Artifact

- CLI: `tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator.py`

The accumulator:

- requires `--confirm-accumulate-campaign-shard`
- requires the existing campaign-shard execution authorization phrase
- reads the Report 178 readiness report
- reads a previous event CSV
- executes a new chunk for all 12 selected jobs
- prefixes new event ids with a stable chunk id
- writes accumulated event/source/manifest/report sidecars
- reruns source availability and source numeric sufficiency gates
- does not run COMSOL
- does not regenerate `JOINT_ROUTE_CLASS`
- does not generate production `NODI_POSITION_RESPONSE_SURFACE`

## Real Output

Command:

```bash
python tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator.py \
  --confirm-accumulate-campaign-shard \
  --readiness-report tmp/nodi_position_response_source_accumulation_campaign_runner_readiness_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_REPORT_20260618.json \
  --previous-events tmp/nodi_position_response_source_accumulation_campaign_shard_execution_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_EVENTS_20260618.csv \
  --chunk-id chunk002 \
  --n-events-per-job 100 \
  --output-dir tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk002_20260618
```

Result:

- status: `PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_NOT_PRODUCTION`
- selected_campaign_shard_id: `PRS_ACCUM_CAMPAIGN_SHARD_0001`
- selected_job_count: `12`
- previous_event_count: `144`
- chunk_event_count: `1200`
- accumulated_event_count: `1344`
- planned_campaign_shard_event_count: `529200`
- bin_source_rows: `5604`
- source_availability_status: `PASS_PRS_SOURCE_AVAILABILITY_PREFLIGHT_NOT_PRODUCTION`
- source_numeric_sufficiency_status: `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT`
- numeric_sufficient_candidate_count: `0`

Output directory:

```text
tmp/nodi_position_response_source_accumulation_campaign_shard_accumulator_chunk002_20260618/
```

Key output hashes:

- `NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_REPORT_20260618.json`
  - SHA256: `fc8ea4cca11203f6250abeedbffa096e6f039e9bf5e4661f738a7c30f1f74ab1`
- `NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_EVENTS_20260618.csv`
  - SHA256: `d60d83ff0665168f33020e11f70cfe516bda6e6f83480e64f9e2f07f7c10b55a`
- `NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATED_20260618.csv`
  - SHA256: `cf7e28719e1e8b48f2536364374dde2d164a3a4a9049088a950a4b16aabf384d`

## Boundary

The accumulator report records:

- `full_campaign_shard_completed=false`
- `campaign_shard_accumulator_slice=true`
- `position_response_surface_production_generated=false`
- `production_generation_performed=false`
- `comsol_run_performed=false`
- `joint_route_class_regenerated=false`
- `not_qch_weighted=true`
- `not_yield=true`
- `not_winner=true`
- `not_detection_probability=true`
- `not_true_W_eff=true`
- `not_measured_geometry=true`
- `not_optical_solver_output=true`
- `not_fabrication_release=true`
- `not_P3_solver_conclusion=true`

No `NODI_POSITION_RESPONSE_SURFACE*`, `JOINT_ROUTE_CLASS*`, or COMSOL output file was found in the accumulator output directory.

## Validation

Static checks:

```bash
python -m py_compile tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator.py
ruff check tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator.py
python -m pyright tools/audits/run_nodi_position_response_source_accumulation_campaign_shard_accumulator.py
```

Results:

- `py_compile`: pass
- `ruff`: pass
- `pyright`: `0 errors, 0 warnings, 0 informations`

Artifact checks:

- accumulated event rows: `1344`
- unique event ids: `1344`
- bin-source rows: `5604`
- manifest rows: `12`
- `validate_position_response_bin_source_event_rows(...)`: no issues
- `validate_position_response_bin_source_rows(...)`: no issues
- source availability: PASS
- numeric sufficiency: BLOCKED as expected

Full repository regression was intentionally not run for this narrow accumulator step.

## Stop Point

The current stop point remains numeric sufficiency:

```text
BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT
```

The accumulator has moved from 144 to 1344 events, but this is still far below the 529200 planned event count for the first campaign shard. No production PRS generation is authorized.
