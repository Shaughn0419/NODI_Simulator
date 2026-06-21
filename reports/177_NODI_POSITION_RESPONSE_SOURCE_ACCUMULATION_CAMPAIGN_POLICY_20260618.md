# Report 177 - NODI_POSITION_RESPONSE source accumulation campaign policy

Date: 2026-06-18

## Disposition

PASS - a no-execution PRS source accumulation campaign policy was implemented,
written, independently reviewed, and verified.

This report does not authorize NODI shard execution, COMSOL execution,
`JOINT_ROUTE_CLASS` regeneration, production `NODI_POSITION_RESPONSE_SURFACE`
generation, q_ch weighting, q_ch*eta, yield, winner, detection probability,
true W_eff, measured geometry, optical solver output, fabrication release, or P3
solver conclusions.

## Implemented Artifacts

- `nodi_simulator/nodi_comsol_next_artifacts.py`
  - SHA256: `ab31619c5a0f5226facce4b09e4d1ce54b920d8c57e48e4566efaff79c1cabbc`
  - Added campaign-policy builder, writer, validator, shard rows, job-schedule
    rows, resume semantics, and no-execution boundary checks.

- `tools/audits/write_nodi_position_response_source_accumulation_campaign_policy.py`
  - SHA256: `06c22f14b5a87ede6d146854c0001a83d2a8cb9a6b9db25925d15c7764b32790`
  - New confirm-gated CLI that writes campaign-policy sidecars only.

- `tests/test_nodi_comsol_next_artifacts_contracts.py`
  - SHA256: `59934a87da99b6bc7c9d7c87559ff80b817ee8391717cdd30ffa826f31341b08`
  - Added campaign-policy tests for counts, no-execution flags, confirm gate,
    sidecar writing, and mutated schedule rejection.

## Policy Semantics

The campaign policy is a schedule, not execution. It assigns the Report 174 job
plan into sequential shards and defines resume and post-shard gates.

Policy choices:

- jobs per shard: `12`
- max parallel shards: `1`
- valid jobs: `468`
- planned shards: `39`
- planned requested event count: `20638800`
- expected bin-source rows if all jobs complete: `218556`
- resume strategy:
  `sequential_shard_resume_by_job_plan_sha256_and_shard_completion_marker`
- resume requires matching job-plan SHA: `true`
- skip completed shards without hash match: `false`
- post-shard gate:
  `source_availability_preflight_then_numeric_sufficiency_preflight`
- numeric sufficiency pass action:
  `stop_for_review_not_auto_production_prs`

Every shard and job-schedule row remains:

- `policy_only_not_executed=true`
- `execution_authorized=false`
- `production_prs_generated=false`
- `comsol_run_performed=false`
- `joint_route_class_regenerated=false`

## Real Policy Output

Command:

```bash
python tools/audits/write_nodi_position_response_source_accumulation_campaign_policy.py \
  --confirm-write-campaign-policy \
  --job-plan tmp/nodi_position_response_source_accumulation_job_plan_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_JOB_PLAN_20260618.csv \
  --output-dir tmp/nodi_position_response_source_accumulation_campaign_policy_20260618 \
  --jobs-per-shard 12
```

Result:

- status: `PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_NOT_EXECUTED`
- valid jobs: `468`
- planned shards: `39`
- jobs per shard: `12`
- max parallel shards: `1`
- planned requested event count: `20638800`
- expected bin-source rows if all jobs complete: `218556`
- campaign execution authorized: `false`
- shard execution authorized: `false`
- NODI run performed: `false`
- production PRS generated: `false`
- COMSOL run performed: `false`
- `JOINT_ROUTE_CLASS` regenerated: `false`

Output hashes:

- `tmp/nodi_position_response_source_accumulation_campaign_policy_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_REPORT_20260618.json`
  - SHA256: `4ea8ea493bc494319f33c85c0664a97ef0880b016ad67bf0203513fd65125953`
- `tmp/nodi_position_response_source_accumulation_campaign_policy_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARDS_20260618.csv`
  - SHA256: `c3ed95355596a4d1ce3c4c9e517784fb13d924422e32216b2def72d8fdc0de6f`
- `tmp/nodi_position_response_source_accumulation_campaign_policy_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_JOB_SCHEDULE_20260618.csv`
  - SHA256: `4deeedeb4d528f157fea367edeac203e11082cc2acd778efd977a7393208daa5`

## Schedule Evidence

Observed schedule checks:

- shard rows: `39`
- job-schedule rows: `468`
- job-count values: `12` for all `39` shards
- unique source jobs: `468`
- first shard:
  `PRS_ACCUM_CAMPAIGN_SHARD_0001`, `PRS_ACCUM_000001` to `PRS_ACCUM_000012`
- last shard:
  `PRS_ACCUM_CAMPAIGN_SHARD_0039`, `PRS_ACCUM_000457` to `PRS_ACCUM_000468`
- shard `execution_authorized`: `false` only
- job `execution_authorized`: `false` only
- shard `policy_only_not_executed`: `true` only
- job `policy_only_not_executed`: `true` only
- no `NODI_POSITION_RESPONSE_SURFACE.csv`
- no `JOINT_ROUTE_CLASS*`
- no COMSOL output surface in the policy directory

## Independent Review

Reviewer: `Peirce`

Verdict: PASS.

Confirmed:

- generated bundle reports
  `PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_NOT_EXECUTED`;
- `valid_job_count=468`, `planned_shard_count=39`, `jobs_per_shard=12`,
  and `max_parallel_shards=1`;
- all shard/job rows have `execution_authorized=false`,
  `policy_only_not_executed=true`, and `production_prs_generated=false`;
- output directory contains only the expected campaign-policy sidecars;
- code enforces `max_parallel_shards == 1`, post-shard numeric sufficiency
  gate, and `stop_for_review_not_auto_production_prs`;
- CLI requires `--confirm-write-campaign-policy`;
- tests cover campaign counts, false execution flags, stop-for-review action,
  absence of production PRS, and forbidden positive claim fields.

## Verification

Final verification:

```bash
python -m py_compile nodi_simulator/nodi_comsol_next_artifacts.py tools/audits/write_nodi_position_response_source_accumulation_campaign_policy.py tests/test_nodi_comsol_next_artifacts_contracts.py
ruff check nodi_simulator/nodi_comsol_next_artifacts.py tools/audits/write_nodi_position_response_source_accumulation_campaign_policy.py tests/test_nodi_comsol_next_artifacts_contracts.py
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q -k "campaign_policy"
python -m pyright nodi_simulator/nodi_comsol_next_artifacts.py tools/audits/write_nodi_position_response_source_accumulation_campaign_policy.py tests/test_nodi_comsol_next_artifacts_contracts.py
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
ruff check .
python -m pyright
python tests/run_tests.py --workers 7
```

Observed:

- py_compile: PASS
- focused ruff: PASS
- focused campaign-policy tests: `4 passed`
- focused pyright: `0 errors, 0 warnings`
- contract tests: `125 passed in 48.67s`
- full ruff: PASS
- full pyright: `0 errors, 0 warnings`
- full regression: `1574 passed in 87.73s`

## Stop Point

NODI now has a full no-execution campaign policy for PRS source accumulation.
The next gate is not production PRS. The next safe step is to implement a
campaign runner readiness/preflight that can execute one scheduled shard at a
time only after explicit authorization, then immediately run source availability
and numeric sufficiency preflights after each shard.
