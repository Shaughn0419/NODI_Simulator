# Report 173 - NODI_POSITION_RESPONSE source numeric sufficiency gate

Date: 2026-06-18

## Disposition

PASS - a preflight-only numeric sufficiency gate was implemented for
`NODI_POSITION_RESPONSE` bin-conditioned source candidates.

The current runner-slice source remains correctly BLOCKED for production PRS:
it is structurally usable as a source candidate, but it is numerically
insufficient.

This report does not authorize production `NODI_POSITION_RESPONSE_SURFACE`
generation. It does not authorize COMSOL execution, `JOINT_ROUTE_CLASS`
regeneration, q_ch weighting, q_ch*eta, yield, winner, detection probability,
true W_eff, measured geometry, optical solver output, fabrication release, or P3
solver conclusions.

## Implemented Artifacts

- `nodi_simulator/nodi_comsol_next_artifacts.py`
  - SHA256: `406012dfee7ada9d28984d31d73260c78dccc0a1dfa3c2519caeaa4f9a154a9b`
  - Added source numeric-sufficiency report, sidecar writers, validator, and
    job-plan diagnostics.
  - Numeric gate policy:
    `all_bin_source_rows_adequate_decision_use_allowed_true_min_100_events_per_bin`.

- `tools/audits/run_nodi_position_response_source_sufficiency_preflight.py`
  - SHA256: `6578c727f368be7958901820f0fb572db66f8e84d11be4f8490dcbd5cec049ef`
  - New confirm-gated preflight CLI.
  - Writes only sufficiency report/candidates/blockers/job-plan/issues sidecars.
  - Returns nonzero for blocked sufficiency; returns zero only when the
    candidate source passes numeric sufficiency.

- `tests/test_nodi_comsol_next_artifacts_contracts.py`
  - SHA256: `71a146003378d1cb7c2adb39b62ab6f4cf2309681a4777fe692899d3609b0cbe`
  - Added blocked sparse-source test, adequate-source pass test, CLI blocked
    sidecar test, CLI pass sidecar test, and diagnostic guard assertions.

## Gate Semantics

Source availability and source numeric sufficiency are intentionally separate.

- `PASS_PRS_SOURCE_AVAILABILITY_PREFLIGHT_NOT_PRODUCTION` means the candidate
  has the required grain and source shape.
- `PASS_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT_NOT_PRODUCTION` means every
  candidate row is adequate for future production PRS consideration.
- Neither status generates production PRS by itself.

Numeric sufficiency requires every bin-conditioned source row to satisfy:

- `bin_sample_status=adequate`
- `decision_use_allowed=true`
- `sparse_bin_flag=false`
- `n_events_bin >= 100`

The job-plan sidecar is diagnostic only:

- report `job_plan_execution_authorized=false`
- report `job_plan_shortfall_fields_are_diagnostic_not_event_counts=true`
- row `execution_authorized=false`
- row `shortfall_fields_are_diagnostic_not_event_counts=true`
- `recommended_min_total_events_floor_basis` states the floor is not requested
  `n_events`.

## Smoke Execution

Command:

```bash
python tools/audits/run_nodi_position_response_source_sufficiency_preflight.py \
  --confirm-source-sufficiency-preflight \
  --candidate-source tmp/nodi_position_response_runner_slice_source_export_20260618/NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_RUNNER_SLICE_20260618.csv \
  --output-dir tmp/nodi_position_response_source_sufficiency_20260618
```

Result:

- status: `BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT`
- candidate count: `1`
- numeric sufficient candidate count: `0`
- candidate status: `blocked_numeric_insufficient_for_production_prs`
- source scope status: `production_candidate_scope`
- candidate rows: `467`
- inadequate rows: `467`
- decision-use disallowed rows: `467`
- sparse/empty rows: `467`
- minimum `n_events_bin`: `0`
- minimum total events per seed: `6`
- no `NODI_POSITION_RESPONSE_SURFACE.csv`

Smoke output hashes:

- `tmp/nodi_position_response_source_sufficiency_20260618/NODI_POSITION_RESPONSE_SOURCE_NUMERIC_SUFFICIENCY_REPORT_20260618.json`
  - SHA256: `18700a9b2c938b4ace5b6d5dc57ced8d551a036314ea283641a61415ee43c4df`
- `tmp/nodi_position_response_source_sufficiency_20260618/NODI_POSITION_RESPONSE_SOURCE_NUMERIC_SUFFICIENCY_CANDIDATES_20260618.csv`
  - SHA256: `b1d343aeaa509c7dfaef93ed2161b645d8879e9e17c16361b3647e4411a8e535`
- `tmp/nodi_position_response_source_sufficiency_20260618/NODI_POSITION_RESPONSE_SOURCE_NUMERIC_SUFFICIENCY_BLOCKERS_20260618.csv`
  - SHA256: `ffaa2a1e872472596fd77d53e1b451cba10e2e51ef682ef882ca196b6e219f36`
- `tmp/nodi_position_response_source_sufficiency_20260618/NODI_POSITION_RESPONSE_SOURCE_NUMERIC_SUFFICIENCY_JOB_PLAN_20260618.csv`
  - SHA256: `510954244e0eba447522c260e7828afafa4623990f06516ce509786c88918f95`
- `tmp/nodi_position_response_source_sufficiency_20260618/NODI_POSITION_RESPONSE_SOURCE_NUMERIC_SUFFICIENCY_ISSUES_20260618.csv`
  - SHA256: `9b1eeccafea4928aa6e005f037f75c91de6c8b09ba5ba7346d875f90edf2d26a`

## Independent Review

Reviewer 1: `Banach`

Verdict: PASS

Findings:

- Confirmed preflight-only CLI.
- Confirmed numeric sufficiency requires adequate rows, `decision_use_allowed`,
  `sparse_bin_flag=false`, and `n_events_bin>=100`.
- Confirmed current runner-slice source is correctly BLOCKED.

Gaps identified:

- Missing direct CLI PASS-path test.
- Negative downstream claim fields were indirect.
- Job-plan diagnostic fields could be misread as execution authorization or
  true event counts.

Resolution:

- Added direct CLI PASS-path test with exact sidecar-only directory assertion.
- Added explicit negative fields:
  `not_true_W_eff`, `not_measured_geometry`, `not_optical_solver_output`,
  `not_fabrication_release`, and `not_P3_solver_conclusion`.
- Added explicit job-plan guard fields:
  `job_plan_execution_authorized=false`,
  `job_plan_shortfall_fields_are_diagnostic_not_event_counts=true`,
  `execution_authorized=false`, and
  `shortfall_fields_are_diagnostic_not_event_counts=true`.

Reviewer 2: `Raman`

Verdict: PASS

Confirmed the Banach gaps were closed. Remaining note was to make the CLI PASS
test assert exact output directory equality; this was added before final
verification.

## Verification

Final verification after review-driven hardening:

```bash
python -m py_compile nodi_simulator/nodi_comsol_next_artifacts.py tools/audits/run_nodi_position_response_source_sufficiency_preflight.py tests/test_nodi_comsol_next_artifacts_contracts.py
ruff check nodi_simulator/nodi_comsol_next_artifacts.py tools/audits/run_nodi_position_response_source_sufficiency_preflight.py tests/test_nodi_comsol_next_artifacts_contracts.py
python -m pyright nodi_simulator/nodi_comsol_next_artifacts.py tools/audits/run_nodi_position_response_source_sufficiency_preflight.py tests/test_nodi_comsol_next_artifacts_contracts.py
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
ruff check .
python -m pyright
python tests/run_tests.py --workers 7
```

Observed results:

- local py_compile: PASS
- local ruff: PASS
- local pyright: `0 errors, 0 warnings`
- contract tests: `97 passed in 42.95s`
- full ruff: PASS
- full pyright: `0 errors, 0 warnings`
- full regression: `1546 passed in 83.79s`

## Stop Point

The NODI side now has a two-stage PRS source gate:

1. source availability preflight;
2. numeric sufficiency preflight.

The current runner-slice source reaches stage 1 but fails stage 2, as intended.
Production PRS remains blocked until a real source passes numeric sufficiency
without sparse/empty or decision-disallowed rows.
