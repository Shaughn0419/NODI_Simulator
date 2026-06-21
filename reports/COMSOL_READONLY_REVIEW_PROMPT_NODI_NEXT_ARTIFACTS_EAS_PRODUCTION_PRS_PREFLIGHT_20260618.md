# COMSOL read-only review prompt: NODI EAS production and PRS preflight stop

Please perform a read-only review. Do not run COMSOL, do not run NODI, do not
regenerate `JOINT_ROUTE_CLASS`, and do not authorize PRS production generation.

Scope:

NODI integrated the COMSOL-approved first-production EAS selector policy and
executed the authorized production-generation gate. The expected stop point is:

```text
PARTIAL_PRODUCTION_GENERATION_EAS_WRITTEN_PRS_BLOCKED
```

Review goals:

1. Confirm the first-production EAS artifact follows the approved descriptor
   selector:

```text
process_state = nominal_smooth_geometry
angle_convention = sidewall_angle_from_substrate_plane_90deg_vertical
sidewall_deg = 85.0
W_nominal_nm = EAS.W_nominal_nm
D_nm = EAS.D_nm
route_geometry_id_comsol_version = route_geometry_id_comsol_v1_contract_20260616
claim_boundary = nominal_surrogate_geometry_descriptor_not_measured_not_optical_solver
```

2. Confirm the selector is recorded as exactly-one-descriptor-row-per-W/D with
   no fallback.
3. Confirm first-production EAS rows use only:

```text
nominal_width
W_bottom_conservative
min_aperture_conservative
top_bottom_average_heuristic
```

4. Confirm `COMSOL_descriptor_if_available` is excluded from the EAS production
   CSV, not aliased into another mode.
5. Confirm EAS remains dry sensitivity only and does not claim true W_eff,
   measured geometry, optical solver output, fabrication release, yield,
   winner, or P3 solver conclusion.
6. Confirm PRS remains blocked and no production
   `NODI_POSITION_RESPONSE_SURFACE.csv` was emitted.
7. Confirm the remaining PRS blocker correctly requires a real
   `route_id_nodi x diameter_nm x NODI_view x seed x distribution/bin`
   source with per-bin response counts.

Files to review:

```text
reports/168_NODI_NEXT_ARTIFACTS_EAS_PRODUCTION_PRS_PREFLIGHT_STOP_20260618.md

nodi_simulator/nodi_comsol_next_artifacts.py
tools/audits/run_nodi_next_artifacts_production_generation.py
tests/test_nodi_comsol_next_artifacts_contracts.py

tmp/nodi_next_artifacts_production_generation_20260618/NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv
SHA256: 35c8b43e641631b682df07dc305ee17bc97384e6cf135c94adce791748243ecc
rows: 32

tmp/nodi_next_artifacts_production_generation_20260618/NODI_EFFECTIVE_APERTURE_SURROGATE_SELECTOR_POLICY_20260618.json
SHA256: 13e151737a6f284dc329fdf2ab14b3125b5d07639c0dab326f7d782b896068c7

tmp/nodi_next_artifacts_production_generation_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_20260618.json
SHA256: c39cd3db7e13c4633c0bfa26923748311b7e8dbf843e4b23d5cd93e5aa625692

tmp/nodi_next_artifacts_production_generation_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_BLOCKERS_20260618.csv
SHA256: 1025211bee3b19184c80dfc20ce125e1bfec95e174db8c730aaa21e23cce67c5
rows: 1

tmp/nodi_next_artifacts_production_generation_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_ISSUES_20260618.csv
SHA256: 9b1eeccafea4928aa6e005f037f75c91de6c8b09ba5ba7346d875f90edf2d26a
rows: sentinel none
```

NODI-side verification already performed:

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

Please return:

- PASS / PASS_WITH_CORRECTION / BLOCKER.
- Whether the EAS selector policy and first-production mode set are acceptable.
- Whether any EAS row overclaims beyond dry sensitivity.
- Whether PRS remains correctly blocked.
- Whether any additional NODI-side validator or metadata field is required
  before moving to PRS source-availability/preflight implementation.
