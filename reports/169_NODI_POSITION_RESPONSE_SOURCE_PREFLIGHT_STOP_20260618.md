# Report 169: NODI position-response source preflight stop

Date: 2026-06-18

Status: BLOCKED_PRS_SOURCE_AVAILABILITY_PREFLIGHT

## Scope

This report records the NODI-side continuation after Report 168 without sending
the EAS partial-production result to COMSOL first.

The work here is intentionally limited to `NODI_POSITION_RESPONSE_SURFACE`
source availability. It does not produce PRS production rows.

Actions performed:

- Implemented a PRS source-availability/preflight gate.
- Scanned known local fullgrid route-level raw/rank candidates.
- Wrote machine-readable candidate, blocker, issue, and report sidecars.
- Confirmed current local candidates are insufficient for production PRS.

Actions not performed:

- No production `NODI_POSITION_RESPONSE_SURFACE.csv`.
- No NODI full runner execution.
- No COMSOL run.
- No `JOINT_ROUTE_CLASS` regeneration.
- No promotion of smoke, bounded-smoke, `PLAN_ONLY`, route-rank, or route-level
  raw rows to PRS production rows.
- No q_ch weighting, yield, winner, detection-probability, true W_eff, measured
  geometry, optical-solver-output, fabrication-release, or P3-solver conclusion
  claim.

## Minimum PRS source grain

The preflight requires a real source that can support:

```text
route_id_nodi x diameter_nm x NODI_view x seed x distribution/bin
```

It must also expose per-bin response-count capability, either through explicit
bin count fields such as `n_events_bin`, `n_events_bin_per_seed`, or
`response_count_bin`, or through event-level rows that can be accumulated into
the PRS bins.

## Outputs

Output directory:

```text
tmp/nodi_position_response_source_preflight_20260618/
```

Preflight report:

```text
tmp/nodi_position_response_source_preflight_20260618/NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_REPORT_20260618.json
SHA256: 67f6b3a4d82932fdb0817df048a775c7fb5350ec24e20b847e1007bba626903b
```

Candidate inventory:

```text
tmp/nodi_position_response_source_preflight_20260618/NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_CANDIDATES_20260618.csv
SHA256: c59c7aac7b5dd8bd6035ba4ae2d4df3e1f44fc2a59874468677bd70c854e4fb3
rows: 7
source_available_candidate_count: 0
```

Blocker sidecar:

```text
tmp/nodi_position_response_source_preflight_20260618/NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_BLOCKERS_20260618.csv
SHA256: 9d9ea6b48a1e8804bba333e224ef8a359b625e2d049c7d4e46f2ed81313dfb14
rows: 1
blocker: PRS-SOURCE-B01 blocked_no_real_bin_conditioned_source
```

Issue sidecar:

```text
tmp/nodi_position_response_source_preflight_20260618/NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_ISSUES_20260618.csv
SHA256: 9b1eeccafea4928aa6e005f037f75c91de6c8b09ba5ba7346d875f90edf2d26a
rows: sentinel none
```

## Candidate result

The preflight scanned 7 current local candidates:

- 6 fullgrid raw-row CSVs from the 3-seed shared-dual 10000e runs.
- 1 NODI/COMSOL handoff route-stability/rank source CSV.

All 7 candidates are blocked:

```text
candidate_status: blocked_missing_minimum_prs_source_grain
source_available_candidate_count: 0
```

Observed missing requirements:

```text
distribution_or_bin
per_bin_response_count
```

For the route-stability handoff rank source, additional missing requirements
include:

```text
diameter_nm
seed
```

This confirms the current local route-level artifacts are not valid PRS
production sources.

## Validation evidence

Preflight command:

```bash
python tools/audits/run_nodi_position_response_source_preflight.py \
  --confirm-source-preflight \
  --output-dir tmp/nodi_position_response_source_preflight_20260618
```

Result:

```text
NODI_POSITION_RESPONSE_SOURCE_PREFLIGHT:
BLOCKED_PRS_SOURCE_AVAILABILITY_PREFLIGHT
candidate_count: 7
source_available_candidate_count: 0
```

Artifact validation:

```text
report validator: PASS
candidate_count: 7
candidate_statuses: blocked_missing_minimum_prs_source_grain
blocker: PRS-SOURCE-B01 blocked_no_real_bin_conditioned_source
NODI_POSITION_RESPONSE_SURFACE.csv exists: false
```

Regression checks:

```text
python -m py_compile nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/run_nodi_position_response_source_preflight.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py

ruff check nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/run_nodi_position_response_source_preflight.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py

python -m pyright nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/run_nodi_position_response_source_preflight.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py

python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
82 passed

python tests/run_tests.py --workers 7
1531 passed
```

## Independent review

Independent verifier subagent result: PASS.

Reviewer-confirmed points:

- The new CLI is preflight-only and does not generate production PRS rows.
- The minimum source grain is correctly encoded as
  `route_id_nodi x diameter_nm x NODI_view x seed x distribution/bin`.
- Per-bin/event response-count capability is required.
- Current local candidates are correctly blocked rather than promoted.
- The blocker explicitly requires a real bin-conditioned source and rejects
  smoke, bounded-smoke, `PLAN_ONLY`, route-rank, and route-level raw-row
  promotion.
- Tests cover both a passing minimal bin-conditioned fixture and the current
  blocked default-candidate state.

## Stop Point

NODI can continue without sending Report 168 to COMSOL first, but it cannot
emit production PRS rows yet.

The next technical step is not COMSOL review; it is NODI-side source creation or
export design:

```text
Produce a real bin-conditioned/event-level PRS source with route_id_nodi,
diameter_nm, NODI_view, seed, distribution/bin, and per-bin response counts.
```

That source may then be rechecked by the preflight gate. Only after the source
availability preflight passes should production `NODI_POSITION_RESPONSE_SURFACE`
row generation be considered.
