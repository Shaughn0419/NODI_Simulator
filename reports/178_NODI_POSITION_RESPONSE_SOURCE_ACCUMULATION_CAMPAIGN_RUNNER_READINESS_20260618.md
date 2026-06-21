# Report 178: NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS

Date: 2026-06-18

## Purpose

Advance the PRS source-accumulation campaign from Report 177 policy-only scheduling to a bounded runner-readiness gate for exactly one planned shard.

This report does not authorize shard execution. It records that the next shard can be reviewed for a future explicit execution authorization.

## Implemented Artifacts

- Code contract: `nodi_simulator/nodi_comsol_next_artifacts.py`
- CLI: `tools/audits/write_nodi_position_response_source_accumulation_campaign_runner_readiness.py`
- Tests: `tests/test_nodi_comsol_next_artifacts_contracts.py`
- Real output directory: `tmp/nodi_position_response_source_accumulation_campaign_runner_readiness_20260618/`

## Real Output

Command:

```bash
python tools/audits/write_nodi_position_response_source_accumulation_campaign_runner_readiness.py \
  --confirm-write-runner-readiness \
  --campaign-report tmp/nodi_position_response_source_accumulation_campaign_policy_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_REPORT_20260618.json \
  --campaign-shard-id PRS_ACCUM_CAMPAIGN_SHARD_0001 \
  --output-dir tmp/nodi_position_response_source_accumulation_campaign_runner_readiness_20260618
```

Result:

- status: `PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_NOT_EXECUTED`
- selected_campaign_shard_id: `PRS_ACCUM_CAMPAIGN_SHARD_0001`
- selected_job_count: `12`
- selected_planned_requested_event_count: `529200`
- selected_expected_bin_source_rows: `5604`
- issues: none

Output hashes:

- `NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_REPORT_20260618.json`
  - SHA256: `37b4aa63273850ac9414c4cf52d44e1ee46437b499caca54c66859df8443f87d`
- `NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_SHARD_20260618.csv`
  - SHA256: `87b6506232731ff88bab0d260f7562a4eb1242a1869a9b62a1e0f37a2e935172`
- `NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_ISSUES_20260618.csv`
  - SHA256: `9b1eeccafea4928aa6e005f037f75c91de6c8b09ba5ba7346d875f90edf2d26a`

## Boundary

The readiness layer is sidecar-only.

Explicit false fields in the report:

- `runner_readiness_authorized=false`
- `shard_execution_authorized=false`
- `full_runner_execution_authorized=false`
- `full_runner_execution_performed=false`
- `nodi_run_performed=false`
- `position_response_surface_production_generated=false`
- `production_generation_performed=false`
- `comsol_run_performed=false`
- `joint_route_class_regenerated=false`

Explicit forbidden-claim guards remain true:

- `not_qch_weighted=true`
- `not_yield=true`
- `not_winner=true`
- `not_detection_probability=true`
- `not_true_W_eff=true`
- `not_measured_geometry=true`
- `not_optical_solver_output=true`
- `not_fabrication_release=true`
- `not_P3_solver_conclusion=true`

No `NODI_POSITION_RESPONSE_SURFACE*`, `JOINT_ROUTE_CLASS*`, or COMSOL output file was found in the readiness output directory.

## Validation

Focused verification was used for efficiency.

```bash
python -m py_compile nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/write_nodi_position_response_source_accumulation_campaign_runner_readiness.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py

ruff check nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/write_nodi_position_response_source_accumulation_campaign_runner_readiness.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py

python -m pyright nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/write_nodi_position_response_source_accumulation_campaign_runner_readiness.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py

python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q \
  -k "campaign_policy or campaign_runner_readiness"
```

Results:

- `py_compile`: pass
- `ruff`: pass
- `pyright`: `0 errors, 0 warnings, 0 informations`
- focused pytest: `8 passed, 121 deselected`

Full regression was intentionally not run for this narrow readiness layer.

## Next Gate

The next required authorization phrase is:

```text
authorize NODI PRS source accumulation campaign shard execution
```

Even after a future shard execution, the required post-shard gate remains:

```text
source_availability_preflight_then_numeric_sufficiency_preflight
```

If numeric sufficiency passes, the action is still:

```text
stop_for_review_not_auto_production_prs
```

No production `NODI_POSITION_RESPONSE_SURFACE` generation is authorized by this report.
