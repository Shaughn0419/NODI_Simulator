# Report 174 - NODI_POSITION_RESPONSE source accumulation job plan

Date: 2026-06-18

## Disposition

PASS - a non-executed PRS source accumulation job-plan gate was implemented and
run against the existing EV/gold route-source.

This report does not authorize NODI runner execution, COMSOL execution,
`JOINT_ROUTE_CLASS` regeneration, production `NODI_POSITION_RESPONSE_SURFACE`
generation, q_ch weighting, q_ch*eta, yield, winner, detection probability,
true W_eff, measured geometry, optical solver output, fabrication release, or P3
solver conclusions.

## Implemented Artifacts

- `nodi_simulator/nodi_comsol_next_artifacts.py`
  - SHA256: `1f424d4ee823c996826545db4724ab01177d127d6205c797628a7d018242da2b`
  - Added source accumulation job-plan builder, writer, validator, and route
    source particle-binding checks.

- `tools/audits/write_nodi_position_response_source_accumulation_job_plan.py`
  - SHA256: `2442fa327dedbba6c4aca0228c5721b83be81e5c56cb36c1ffc3d5cc580654e1`
  - New confirm-gated CLI that writes job-plan sidecars only.

- `tests/test_nodi_comsol_next_artifacts_contracts.py`
  - SHA256: `18597fca1fdd92c53ea8f28d904aa9805759b4bf53a59d4b93fd7b777a1442ee`
  - Added pass, blocked missing-binding, CLI sidecar-only, and confirm-gate
    tests.

## Job Plan Semantics

This is a planning gate only. PASS means the route source can be bound into a
source accumulation plan. It does not mean production PRS may be generated.

The plan binds:

- approved routes: `6`
- approved diameters: `13`
- views: `fixed_660_gold`, `per_wavelength_gold`
- seeds: `11`, `22`, `33`
- target event floor per job: `44100`
- post-run required gate:
  `PASS_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT_NOT_PRODUCTION`

The event floor is diagnostic:
`xz_441_bins_times_min_100_per_bin_floor_not_sufficiency_guarantee`.
The produced source must still pass the numeric sufficiency gate after execution.

## Generated Plan

Command:

```bash
python tools/audits/write_nodi_position_response_source_accumulation_job_plan.py \
  --confirm-write-job-plan \
  --route-source results/exhaustive_ev_gold_fullgrid_shared_dual_10000e_seed11_16worker_20260518/seed_11_fixed_660_gold_raw_rows.csv \
  --output-dir tmp/nodi_position_response_source_accumulation_job_plan_20260618
```

Result:

- status: `PASS_PRS_SOURCE_ACCUMULATION_JOB_PLAN_NOT_EXECUTED`
- route-source SHA256:
  `ed33ad43cc2d63b08c9c40a041690c373356f9602fb4a6eb0857e15a71bbb607`
- planned jobs: `468`
- P1 preferred jobs: `390`
- P2 diagnostic trap jobs: `78`
- planned requested event count: `20638800`
- particle bindings: `13`
- missing diameters: `[]`
- missing route/particle slices: `0`
- all job rows: `execution_authorized=false`
- all job rows: `route_source_binding_status=available`
- no `NODI_POSITION_RESPONSE_SURFACE.csv`

Output hashes:

- `tmp/nodi_position_response_source_accumulation_job_plan_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_JOB_PLAN_REPORT_20260618.json`
  - SHA256: `8beb53095d735d836c1a20f872cffdbc82d1398b65e2737f1e42fc5e3f1f4ec9`
- `tmp/nodi_position_response_source_accumulation_job_plan_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_JOB_PLAN_20260618.csv`
  - SHA256: `6be9f34b8a97a6d6972aa282e10e296aa4fd1974e5bd97fbb49de80d44efa678`
- `tmp/nodi_position_response_source_accumulation_job_plan_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_JOB_PLAN_BLOCKERS_20260618.csv`
  - SHA256: `d93e235b8d3d85cbff519d4f595db36062461bf4cf8a053591c963a2986d133f`
- `tmp/nodi_position_response_source_accumulation_job_plan_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_JOB_PLAN_ISSUES_20260618.csv`
  - SHA256: `9b1eeccafea4928aa6e005f037f75c91de6c8b09ba5ba7346d875f90edf2d26a`

## Independent Review

Reviewer: `Pasteur`

Verdict: PASS

Confirmed:

- job-plan only, no execution;
- 468 planned jobs with P1/P2 split `390/78`;
- all generated rows have `route_source_binding_status=available`;
- all generated rows have `execution_authorized=false`;
- no production PRS artifact is emitted;
- post-run gate remains numeric sufficiency PASS.

Reviewer gaps:

- Validator did not explicitly assert `route_source_binding_status` or
  `target_event_floor_basis`.
- Tests did not check every generated row for those row-level semantics.

Resolution:

- Validator now requires all PASS job rows to have
  `route_source_binding_status=available`.
- Validator now rejects drift in
  `target_event_floor_basis`.
- Tests now assert all generated job rows preserve binding status, diagnostic
  floor basis, no execution, no NODI run, and no production PRS.

## Verification

Final verification:

```bash
python -m py_compile nodi_simulator/nodi_comsol_next_artifacts.py tools/audits/write_nodi_position_response_source_accumulation_job_plan.py tests/test_nodi_comsol_next_artifacts_contracts.py
ruff check nodi_simulator/nodi_comsol_next_artifacts.py tools/audits/write_nodi_position_response_source_accumulation_job_plan.py tests/test_nodi_comsol_next_artifacts_contracts.py
python -m pyright nodi_simulator/nodi_comsol_next_artifacts.py tools/audits/write_nodi_position_response_source_accumulation_job_plan.py tests/test_nodi_comsol_next_artifacts_contracts.py
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
ruff check .
python -m pyright
python tests/run_tests.py --workers 7
```

Observed results:

- local py_compile: PASS
- local ruff: PASS
- local pyright: `0 errors, 0 warnings`
- contract tests: `101 passed in 44.62s`
- full ruff: PASS
- full pyright: `0 errors, 0 warnings`
- full regression: `1550 passed in 82.06s`

## Stop Point

NODI now has a concrete, non-executed plan for producing PRS source candidates.
The next gate is not production PRS. The next gate is a separately authorized
bounded execution or shard execution that produces event/bin source sidecars,
followed by the numeric sufficiency preflight from Report 173.
