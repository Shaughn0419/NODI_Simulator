# Report 176 - NODI_POSITION_RESPONSE source accumulation controlled pilot

Date: 2026-06-18

## Disposition

PASS - the Report 175 bounded-shard execution path was exercised at its current
contract ceiling: `3` selected jobs and `12` events per job.

This report does not authorize COMSOL execution, `JOINT_ROUTE_CLASS`
regeneration, full source accumulation, production
`NODI_POSITION_RESPONSE_SURFACE` generation, q_ch weighting, q_ch*eta, yield,
winner, detection probability, true W_eff, measured geometry, optical solver
output, fabrication release, or P3 solver conclusions.

## Pilot Purpose

Report 175 proved the single-job bounded-shard path. Report 176 checks that the
same path remains contract-safe when expanded to multiple seed groups.

This is still a tiny pilot. It is intentionally below numeric sufficiency and
must remain blocked before production PRS.

## Real Execution

Command:

```bash
python tools/audits/run_nodi_position_response_source_accumulation_bounded_shard.py \
  --confirm-bounded-shard-execution \
  --job-plan tmp/nodi_position_response_source_accumulation_job_plan_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_JOB_PLAN_20260618.csv \
  --output-dir tmp/nodi_position_response_source_accumulation_controlled_pilot_20260618 \
  --max-jobs 3 \
  --n-events-per-job 12
```

Result:

- status:
  `PASS_PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_EXECUTION_NOT_PRODUCTION`
- selected jobs: `3`
- events per job: `12`
- event rows: `36`
- bin-source rows: `1401`
- source availability:
  `PASS_PRS_SOURCE_AVAILABILITY_PREFLIGHT_NOT_PRODUCTION`
- source available candidates: `1`
- numeric sufficiency:
  `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT`
- numeric sufficient candidates: `0`
- production PRS generated: `false`
- COMSOL run performed: `false`
- `JOINT_ROUTE_CLASS` regenerated: `false`
- no `NODI_POSITION_RESPONSE_SURFACE.csv`

The selected job groups were:

- `PRS_ACCUM_000001`: `404/W500/D900`, `D=40`, `fixed_660_gold`, seed `11`
- `PRS_ACCUM_000002`: `404/W500/D900`, `D=40`, `fixed_660_gold`, seed `22`
- `PRS_ACCUM_000003`: `404/W500/D900`, `D=40`, `fixed_660_gold`, seed `33`

Each group produced `467` bin-source rows.

## Output Hashes

- `tmp/nodi_position_response_source_accumulation_controlled_pilot_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_REPORT_20260618.json`
  - SHA256: `7fe1486db9cf349e4ccc0ed8b67177d3062830ce593a897d03921a9f3343db2f`
- `tmp/nodi_position_response_source_accumulation_controlled_pilot_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_EVENTS_20260618.csv`
  - SHA256: `7e9353573bfc0c9c21b145516be4ddd87db3df85c8584fec061019a48ae35f81`
- `tmp/nodi_position_response_source_accumulation_controlled_pilot_20260618/NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_ACCUMULATION_BOUNDED_SHARD_20260618.csv`
  - SHA256: `ecba1a641dfdc06c5d6ecb9bf19a58489acf8d111f1cfe831ba0cd1bc999e50c`
- `tmp/nodi_position_response_source_accumulation_controlled_pilot_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_EXECUTION_MANIFEST_20260618.csv`
  - SHA256: `aedc6af4a6be83d5fef9adaed6da7ce19d2037df6d3544121f1dedb9093f5065`
- `tmp/nodi_position_response_source_accumulation_controlled_pilot_20260618/NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_REPORT_20260618.json`
  - SHA256: `1aa332c870aedb287959a4bee0da17d8c111b42af236c75215751e4f605c0cfe`
- `tmp/nodi_position_response_source_accumulation_controlled_pilot_20260618/NODI_POSITION_RESPONSE_SOURCE_NUMERIC_SUFFICIENCY_REPORT_20260618.json`
  - SHA256: `56cc4340883808f7fee84f871d3e015b754d624a3f3779709bf691dcbe60772b`

## Numeric Sufficiency Evidence

The controlled pilot remains numerically insufficient:

- candidate status: `blocked_numeric_insufficient_for_production_prs`
- source scope status: `production_candidate_scope`
- candidate rows: `1401`
- route/diameter/view/seed groups: `3`
- adequate rows: `0`
- inadequate rows: `1401`
- decision-use-disallowed rows: `1401`
- sparse or empty rows: `1401`
- minimum bin events: `0`
- minimum total events per seed: `12`
- issue summary: `sparse_or_empty_bins_present`

All source rows had:

- `decision_use_allowed=false`
- `bin_sample_status` in `{empty, sparse}`
- `source_scope=production_candidate_from_real_nodi_event_export`

This proves only that the source candidate is structurally available. It does
not satisfy Report 173 numeric sufficiency.

## Independent Review

Reviewer: `Erdos`

Verdict: PASS.

Confirmed:

- bounded-shard report is PASS while numeric sufficiency remains BLOCKED;
- selected jobs: `3`;
- event rows: `36`;
- bin-source rows: `1401`;
- three route/diameter/view/seed groups, each with `467` rows;
- no `NODI_POSITION_RESPONSE_SURFACE.csv`;
- no COMSOL run surface;
- no `JOINT_ROUTE_CLASS` regeneration;
- `production_candidate` remains source-candidate scope only;
- all decision-use values are false and all bins are sparse or empty;
- no positive q_ch, yield, winner, detection probability, true W_eff, solver,
  fabrication, or P3 claim fields were found.

## Verification

Checks performed:

```bash
jq '{status,selected_job_count,n_events_per_job,event_rows,bin_source_rows,source_availability_status,source_numeric_sufficiency_status,numeric_sufficient_candidate_count,position_response_surface_production_generated,production_generation_performed,comsol_run_performed,joint_route_class_regenerated,no_prs_production_artifact}' tmp/nodi_position_response_source_accumulation_controlled_pilot_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_REPORT_20260618.json
python - <<'PY'
from collections import Counter
from nodi_simulator.realism_v2_io import read_csv_rows
base='tmp/nodi_position_response_source_accumulation_controlled_pilot_20260618'
source=read_csv_rows(f'{base}/NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_ACCUMULATION_BOUNDED_SHARD_20260618.csv')
events=read_csv_rows(f'{base}/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_EVENTS_20260618.csv')
manifest=read_csv_rows(f'{base}/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_EXECUTION_MANIFEST_20260618.csv')
print(len(events), len(source), len(manifest))
print(sorted(Counter((r['route_id_nodi'], r['diameter_nm'], r['NODI_view'], r['seed']) for r in source).items()))
print(sorted({r['decision_use_allowed'] for r in source}))
print(sorted({r['bin_sample_status'] for r in source}))
PY
jq '.candidate_rows[0] | {candidate_status,source_scope_status,candidate_row_count,route_diameter_view_seed_group_count,adequate_row_count,inadequate_row_count,decision_use_disallowed_row_count,sparse_or_empty_row_count,minimum_n_events_bin,minimum_total_events_seed,issue_summary}' tmp/nodi_position_response_source_accumulation_controlled_pilot_20260618/NODI_POSITION_RESPONSE_SOURCE_NUMERIC_SUFFICIENCY_REPORT_20260618.json
find tmp/nodi_position_response_source_accumulation_controlled_pilot_20260618 -name 'NODI_POSITION_RESPONSE_SURFACE.csv' -o -name 'NODI_POSITION_RESPONSE_SURFACE_*.csv' -print
```

Observed:

- report status: PASS bounded shard, not production;
- numeric sufficiency status: BLOCKED;
- grouped source rows: `3 x 467`;
- event rows: `36`;
- manifest rows: `3`;
- decision-use values: `false` only;
- bin statuses: `empty`, `sparse`;
- production PRS search: no matches.

AppleDouble `._*` files were removed from the pilot output directory after
inspection.

## Stop Point

NODI now has a verified multi-seed controlled pilot for source accumulation.
The next safe step is not production PRS. The next design step should define a
larger accumulation policy with explicit resource budget, shard ordering, resume
semantics, and post-shard sufficiency checks before any production PRS runner is
considered.
