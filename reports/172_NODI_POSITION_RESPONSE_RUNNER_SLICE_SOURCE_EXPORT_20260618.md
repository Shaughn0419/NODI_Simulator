# Report 172 - NODI_POSITION_RESPONSE runner-slice source export gate

Date: 2026-06-18

## Disposition

PASS - bounded runner-compatible selected-slice source export and source-availability
preflight were implemented and smoke-executed.

This report does not authorize production `NODI_POSITION_RESPONSE_SURFACE`
generation. It does not authorize COMSOL execution, `JOINT_ROUTE_CLASS`
regeneration, q_ch weighting, q_ch*eta, yield, winner, detection probability,
true W_eff, measured geometry, optical solver output, fabrication release, or P3
solver conclusions.

## Implemented Artifacts

- `nodi_simulator/nodi_comsol_next_artifacts.py`
  - SHA256: `6c0579fa5f88165b140d06cbe2ef3cfd13c58f0f29b7f8e8c47605dd0e466f40`
  - Added runner-slice source-export filenames and explicit
    `PASS/BLOCKED_PRS_RUNNER_SLICE_SOURCE_EXPORT_PREFLIGHT_ONLY_NOT_PRS_PRODUCTION`
    statuses.

- `tools/audits/run_nodi_position_response_runner_slice_source_export.py`
  - SHA256: `c66ca905d0b8d2f2167212ff14dbb5eb50dc12aa45cdf06fe717ab44cd3f8e51`
  - New guarded CLI for bounded selected route x particle runner-slice event
    export.
  - Requires `--confirm-runner-slice-event-source`.
  - Validates `route-source` schema and exact route/particle slice presence.
  - Writes only event rows, bin-conditioned source rows, source-preflight
    sidecars, and an export report.
  - Explicitly records `preflight_only=true`,
    `position_response_surface_production_generated=false`,
    `comsol_run_performed=false`, and
    `joint_route_class_regenerated=false`.

- `tests/test_nodi_comsol_next_artifacts_contracts.py`
  - SHA256: `0321164d5d27511e13da1023ec0e9b698e315bb2464aa2e4d83b660b07612ffb`
  - Added route-source slice validation, CLI help boundary, missing-confirm
    rejection, and successful preflight-only CLI path coverage.

## Bounded Smoke Execution

Command:

```bash
python tools/audits/run_nodi_position_response_runner_slice_source_export.py \
  --confirm-runner-slice-event-source \
  --route-source results/exhaustive_ev_gold_fullgrid_shared_dual_10000e_seed11_16worker_20260518/seed_11_fixed_660_gold_raw_rows.csv \
  --output-dir tmp/nodi_position_response_runner_slice_source_export_20260618 \
  --overwrite-output \
  --route 404/W500/D900 \
  --particle-name exosome_biomimetic_corona_nominal_150nm \
  --NODI-view fixed_660_gold \
  --seed 11 \
  --n-events 6
```

Result:

- status:
  `PASS_PRS_RUNNER_SLICE_SOURCE_EXPORT_PREFLIGHT_ONLY_NOT_PRS_PRODUCTION`
- route source SHA256:
  `ed33ad43cc2d63b08c9c40a041690c373356f9602fb4a6eb0857e15a71bbb607`
- exact route/particle slice rows: `1`
- event rows: `6`
- bin source rows: `467`
- source preflight status:
  `PASS_PRS_SOURCE_AVAILABILITY_PREFLIGHT_NOT_PRODUCTION`
- source available candidate count: `1`
- `decision_use_allowed_values`: `false`
- bin sample statuses: `empty`, `sparse`
- `NODI_POSITION_RESPONSE_SURFACE.csv`: absent

Smoke output hashes:

- `tmp/nodi_position_response_runner_slice_source_export_20260618/NODI_POSITION_RESPONSE_RUNNER_SLICE_SOURCE_EVENTS_20260618.csv`
  - SHA256: `68041f5609782114c25bd801adb3b7055c4d04e5b857e02d6a0b40361fa35782`
- `tmp/nodi_position_response_runner_slice_source_export_20260618/NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_RUNNER_SLICE_20260618.csv`
  - SHA256: `77381bbf41d1fc36525033c16bd01563d59cb056dbdc345ac7a6dc2c0213d512`
- `tmp/nodi_position_response_runner_slice_source_export_20260618/NODI_POSITION_RESPONSE_RUNNER_SLICE_SOURCE_EXPORT_REPORT_20260618.json`
  - SHA256: `f6233d5013b5d23846a0c8e0b201a8ee25c836f486d20444998caa53bbc1cab6`
- `tmp/nodi_position_response_runner_slice_source_export_20260618/NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_REPORT_20260618.json`
  - SHA256: `1b2153327d1666c56b22b82ce806b6b43a5153b4c0b1a1416d7ee9c34f1dfb3e`

## Independent Review

Subagent reviewer: `Hegel`

Verdict: PASS

Reviewer checked:

- explicit confirmation guard;
- route-source validation;
- sidecar-only output path;
- source-preflight non-production flags;
- sparse/empty `decision_use_allowed=false` behavior;
- absence of `NODI_POSITION_RESPONSE_SURFACE.csv`;
- no COMSOL run and no `JOINT_ROUTE_CLASS` regeneration.

Reviewer gap:

- A dedicated positive CLI success-path regression was initially absent.

Resolution:

- Added `test_prs_runner_slice_source_export_cli_success_is_preflight_only`,
  which monkeypatches the simulation layer, runs the CLI `main([...])`
  success path, and asserts six event rows, 467 bin rows, source-preflight PASS,
  `decision_use_allowed=false`, non-production flags, and absent
  `NODI_POSITION_RESPONSE_SURFACE.csv`.

## Verification

After addressing the reviewer gap:

```bash
python -m py_compile tools/audits/run_nodi_position_response_runner_slice_source_export.py tests/test_nodi_comsol_next_artifacts_contracts.py
ruff check tools/audits/run_nodi_position_response_runner_slice_source_export.py tests/test_nodi_comsol_next_artifacts_contracts.py
python -m pyright tools/audits/run_nodi_position_response_runner_slice_source_export.py tests/test_nodi_comsol_next_artifacts_contracts.py
python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
ruff check .
python -m pyright
python tests/run_tests.py --workers 7
```

Observed results:

- local py_compile: PASS
- local ruff: PASS
- local pyright: `0 errors, 0 warnings`
- contract tests: `93 passed in 40.96s`
- full ruff: PASS
- full pyright: `0 errors, 0 warnings`
- full regression: `1542 passed in 79.64s`

## Stop Point

NODI has now demonstrated a guarded selected-slice path from a
runner-compatible route source into PRS bin-conditioned source sidecars and
source-availability preflight. This is a source/preflight gate only.

Production `NODI_POSITION_RESPONSE_SURFACE` remains blocked until a real
production source provides sufficient per-bin sample support and the production
validator rejects sparse/empty `decision_use_allowed=false` candidates.
