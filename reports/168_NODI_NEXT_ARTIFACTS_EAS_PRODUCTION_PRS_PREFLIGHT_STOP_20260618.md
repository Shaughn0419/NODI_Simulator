# Report 168: NODI next-artifacts EAS production and PRS preflight stop

Date: 2026-06-18

Status: PARTIAL_PRODUCTION_GENERATION_EAS_WRITTEN_PRS_BLOCKED

## Scope

This report records the first authorized NODI next-artifacts production-generation
step after COMSOL approved the EAS descriptor selector policy.

Actions performed:

- Generated first-production `NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY`
  rows using the COMSOL-approved single-descriptor selector.
- Wrote selector policy metadata for the EAS production artifact.
- Kept `NODI_POSITION_RESPONSE_SURFACE` at source-availability/preflight blocker.

Actions not performed:

- No COMSOL run.
- No NODI full runner execution.
- No `JOINT_ROUTE_CLASS` regeneration.
- No production `NODI_POSITION_RESPONSE_SURFACE.csv`.
- No q_ch-weighted optical-response multiplication.
- No yield, winner, true W_eff, measured-geometry, optical-solver-output,
  fabrication-release, or P3-solver conclusion claim.

## COMSOL selector policy integrated

The first-production EAS selector is:

```text
process_state = nominal_smooth_geometry
angle_convention = sidewall_angle_from_substrate_plane_90deg_vertical
sidewall_deg = 85.0
W_nominal_nm = EAS.W_nominal_nm
D_nm = EAS.D_nm
route_geometry_id_comsol_version = route_geometry_id_comsol_v1_contract_20260616
claim_boundary = nominal_surrogate_geometry_descriptor_not_measured_not_optical_solver
```

The implementation enforces exactly one selected descriptor row per W/D grain.
There is no silent fallback to another sidewall angle or process state.

The first-production EAS mode set is restricted to:

- `nominal_width`
- `W_bottom_conservative`
- `min_aperture_conservative`
- `top_bottom_average_heuristic`

`COMSOL_descriptor_if_available` is excluded from the first production artifact.

## Production outputs

Output directory:

```text
tmp/nodi_next_artifacts_production_generation_20260618/
```

Generated EAS CSV:

```text
tmp/nodi_next_artifacts_production_generation_20260618/NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv
SHA256: 35c8b43e641631b682df07dc305ee17bc97384e6cf135c94adce791748243ecc
rows: 32
```

Selector policy metadata:

```text
tmp/nodi_next_artifacts_production_generation_20260618/NODI_EFFECTIVE_APERTURE_SURROGATE_SELECTOR_POLICY_20260618.json
SHA256: 13e151737a6f284dc329fdf2ab14b3125b5d07639c0dab326f7d782b896068c7
```

Production-generation report:

```text
tmp/nodi_next_artifacts_production_generation_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_20260618.json
SHA256: c39cd3db7e13c4633c0bfa26923748311b7e8dbf843e4b23d5cd93e5aa625692
```

Blocker sidecar:

```text
tmp/nodi_next_artifacts_production_generation_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_BLOCKERS_20260618.csv
SHA256: 1025211bee3b19184c80dfc20ce125e1bfec95e174db8c730aaa21e23cce67c5
rows: 1
blocker: PRS-PROD-B01 blocked_missing_position_response_event_source
```

Issue sidecar:

```text
tmp/nodi_next_artifacts_production_generation_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_ISSUES_20260618.csv
SHA256: 9b1eeccafea4928aa6e005f037f75c91de6c8b09ba5ba7346d875f90edf2d26a
rows: sentinel none
```

## Validation evidence

Production gate command:

```bash
python tools/audits/run_nodi_next_artifacts_production_generation.py \
  --confirm-production-generation \
  --authorization-phrase 'authorize NODI next-artifacts production generation' \
  --smoke-execution-report tmp/nodi_next_artifacts_bounded_smoke_execution_20260618/NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_REPORT_20260618.json \
  --geometry-descriptor tmp/COMSOL_GEOMETRY_DESCRIPTOR_V1.csv \
  --rank-source exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv \
  --guardrail-table exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv \
  --output-dir tmp/nodi_next_artifacts_production_generation_20260618
```

Result:

```text
NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION:
PARTIAL_PRODUCTION_GENERATION_EAS_WRITTEN_PRS_BLOCKED
```

Additional artifact validation:

```text
EAS rows: 32
EAS modes: W_bottom_conservative, min_aperture_conservative, nominal_width,
  top_bottom_average_heuristic
EAS row validator: PASS
Production report validator: PASS
PRS production CSV exists: false
COMSOL_descriptor_if_available in EAS CSV: false
```

Regression checks:

```text
python -m py_compile nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/run_nodi_next_artifacts_production_generation.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py

ruff check nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/run_nodi_next_artifacts_production_generation.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py

python -m pyright nodi_simulator/nodi_comsol_next_artifacts.py \
  tools/audits/run_nodi_next_artifacts_production_generation.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py

python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q
79 passed

python tests/run_tests.py --workers 7
1528 passed
```

## Independent review

Independent verifier subagent result: PASS.

Reviewer-confirmed points:

- Selector constants match COMSOL policy.
- Selector metadata records exactly-one-per-W/D and no-fallback semantics.
- Production EAS rows use only the four explicit formula modes.
- `COMSOL_descriptor_if_available` is absent from the EAS CSV.
- `not_true_W_eff=true` and other claim-boundary flags remain hard-set.
- PRS production remains blocked and no `NODI_POSITION_RESPONSE_SURFACE.csv`
  production artifact exists.
- CLI treats the partial status as a successful stop point, not full PASS.

## Remaining stop point

PRS production remains blocked until NODI provides or regenerates a real
bin-conditioned source with at least this grain:

```text
route_id_nodi x diameter_nm x NODI_view x seed x distribution/bin
```

The source must support per-bin response counts and row arithmetic for
production PRS generation. Smoke manifests, bounded-smoke sidecars, and
`PLAN_ONLY_NOT_EXECUTED` blueprints remain invalid as PRS production sources.

Next authorized NODI direction:

1. Keep the current EAS production artifact as the first dry-sensitivity
   production output.
2. Build or locate a real PRS source-availability/preflight artifact.
3. Do not emit production PRS rows until source files, hashes, seed/bin counts,
   and validator checks are present.
