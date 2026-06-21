# Report 175 - NODI_POSITION_RESPONSE source accumulation bounded shard

Date: 2026-06-18

## Disposition

PASS - a bounded PRS source-accumulation shard execution layer was implemented,
executed on one tiny shard, independently reviewed, corrected, and re-verified.

This report does not authorize COMSOL execution, `JOINT_ROUTE_CLASS`
regeneration, full PRS source accumulation, production
`NODI_POSITION_RESPONSE_SURFACE` generation, q_ch weighting, q_ch*eta, yield,
winner, detection probability, true W_eff, measured geometry, optical solver
output, fabrication release, or P3 solver conclusions.

## Implemented Artifacts

- `nodi_simulator/nodi_comsol_next_artifacts.py`
  - SHA256: `d607fac16e78b60d1f0d949db1c549c4d3db4ecea8905120b1bb7ffad50ef1b5`
  - Added bounded-shard constants, job selection, execution manifest rows,
    report builder/writer, and validator.
  - Extended PRS bin-source event/source validators to reject forbidden positive
    claim fields.

- `tools/audits/run_nodi_position_response_source_accumulation_bounded_shard.py`
  - SHA256: `cc88f8c147787ef74e54aad804d0425dcef8121d9dd64c57ae5840503b1d21f2`
  - New confirm-gated CLI for tiny source-accumulation shard execution.

- `tests/test_nodi_comsol_next_artifacts_contracts.py`
  - SHA256: `c2e619ffc3184ff3f493a0b21493ed7c55e362c1e11085af6527fb77e4d8e796`
  - Added bounded-shard report, selection, confirm-gate, CLI execution, and
    forbidden-positive-claim mutant tests.

## Bounded-Shard Semantics

This is a source-sidecar execution gate only. It proves the path from a Report
174 job-plan row to real NODI event rows and a bin-conditioned source candidate.
It does not prove numeric sufficiency and does not allow production PRS.

The shard is hard-capped by contract:

- default selected jobs: `1`
- maximum selected jobs: `3`
- default events per job: `6`
- maximum events per job: `12`
- post-run required gate:
  `PASS_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT_NOT_PRODUCTION`

The generated source may use
`source_scope=production_candidate_from_real_nodi_event_export` because it came
from real NODI event export, but that label is not production authorization.
The numeric sufficiency gate remains separate and blocking.

## Real Execution

Command:

```bash
python tools/audits/run_nodi_position_response_source_accumulation_bounded_shard.py \
  --confirm-bounded-shard-execution \
  --job-plan tmp/nodi_position_response_source_accumulation_job_plan_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_JOB_PLAN_20260618.csv \
  --output-dir tmp/nodi_position_response_source_accumulation_bounded_shard_20260618 \
  --max-jobs 1 \
  --n-events-per-job 6
```

Result:

- status:
  `PASS_PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_EXECUTION_NOT_PRODUCTION`
- selected jobs: `1`
- events per job: `6`
- event rows: `6`
- bin-source rows: `467`
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

Output hashes:

- `tmp/nodi_position_response_source_accumulation_bounded_shard_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_REPORT_20260618.json`
  - SHA256: `2fb5b96bcef96c345672d805e60bbb2f21d751e198a083aafcb7f43de6c172f4`
- `tmp/nodi_position_response_source_accumulation_bounded_shard_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_EVENTS_20260618.csv`
  - SHA256: `f6d78f8915f05d9a658c0f01bf0cf76a7a3180d36e86b40f6c6d97d2da9b1df3`
- `tmp/nodi_position_response_source_accumulation_bounded_shard_20260618/NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_ACCUMULATION_BOUNDED_SHARD_20260618.csv`
  - SHA256: `aa082cba91189e721c0b57fadd5be625bfcc1d5f97ea333b86f1d9a6fb10e01d`
- `tmp/nodi_position_response_source_accumulation_bounded_shard_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_EXECUTION_MANIFEST_20260618.csv`
  - SHA256: `8552e77747895f80428b42e0c45f798a16475c248cb02d5b9e28e51a09c8d477`
- `tmp/nodi_position_response_source_accumulation_bounded_shard_20260618/NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_REPORT_20260618.json`
  - SHA256: `8f42aec4e05347a9c18b66e9c7dfb6b0b0a8551ec63c6abffca87210987c1821`
- `tmp/nodi_position_response_source_accumulation_bounded_shard_20260618/NODI_POSITION_RESPONSE_SOURCE_NUMERIC_SUFFICIENCY_REPORT_20260618.json`
  - SHA256: `528ce9fde1d5dea304d51c8e11af1448e7db8066d8bf0633b92af89108388874`

## Numeric Sufficiency Evidence

The bounded shard intentionally remains numerically insufficient:

- candidate status: `blocked_numeric_insufficient_for_production_prs`
- source scope status: `production_candidate_scope`
- candidate rows: `467`
- adequate rows: `0`
- inadequate rows: `467`
- decision-use-disallowed rows: `467`
- sparse or empty rows: `467`
- minimum bin events: `0`
- minimum total events per seed: `6`
- issue summary: `sparse_or_empty_bins_present`

This preserves the Report 173 rule: production PRS remains blocked until every
bin-source row is adequate, decision-use allowed, non-sparse, and above the
minimum event-count policy.

## Independent Review

Reviewer: `Wegener`

Verdict: PASS checklist before implementation.

Key constraints confirmed:

- source availability and numeric sufficiency must stay separate;
- `production_candidate_from_real_nodi_event_export` is only a candidate-source
  scope label;
- sparse bounded output must not be promoted;
- q_ch, q_ch*eta, yield, winner, detection probability, true W_eff, measured
  geometry, optical solver output, fabrication release, and P3 claims remain
  forbidden or explicitly negative.

Reviewer: `Lorentz`

Initial verdict: BLOCKER.

Finding:

- Real generated sidecars were clean, but bin-source event/source validators did
  not reject forbidden positive claim columns injected by a future caller.

Resolution:

- Added `_reject_forbidden_positive_fields(...)` to both
  `validate_position_response_bin_source_event_rows()` and
  `validate_position_response_bin_source_rows()`.
- Added mutant tests for `q_ch_eta`, `yield`, `winner`, `true_W_eff`,
  `measured_geometry`, `optical_solver_output`, `fabrication_release`, and
  `P3_solver_conclusion` on both event rows and bin-source rows.

Reviewer: `Dewey`

Follow-up verdict: PASS.

Confirmed:

- both validators now reject forbidden positive claim fields;
- negative boundary fields including `not_P3_solver_conclusion` remain allowed;
- mutant coverage is present for event rows and bin-source rows;
- regenerated bounded shard report is PASS while numeric sufficiency remains
  BLOCKED;
- no `NODI_POSITION_RESPONSE_SURFACE.csv` is present in the shard output.

## Verification

Final verification after blocker fix:

```bash
ruff check nodi_simulator/nodi_comsol_next_artifacts.py tools/audits/run_nodi_position_response_source_accumulation_bounded_shard.py tests/test_nodi_comsol_next_artifacts_contracts.py
python -m pyright nodi_simulator/nodi_comsol_next_artifacts.py tools/audits/run_nodi_position_response_source_accumulation_bounded_shard.py tests/test_nodi_comsol_next_artifacts_contracts.py
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q -k "bin_source_rows_reject or bin_source_event_rows_reject or bounded_shard"
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
ruff check .
python -m pyright
python tests/run_tests.py --workers 7
```

Observed results:

- focused ruff: PASS
- focused pyright: `0 errors, 0 warnings`
- focused mutant/bounded-shard tests: `20 passed`
- contract tests: `121 passed in 46.70s`
- full ruff: PASS
- full pyright: `0 errors, 0 warnings`
- full regression: `1570 passed in 74.30s`

## Stop Point

NODI now has a verified bounded shard execution layer for PRS source
accumulation. The next step is not production PRS. The next safe gate is a
larger but still controlled accumulation execution policy, followed by the same
numeric sufficiency preflight. Production `NODI_POSITION_RESPONSE_SURFACE`
remains blocked until that numeric gate passes.
