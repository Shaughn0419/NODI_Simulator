# Report 199 - NODI/COMSOL Gate2A Export Reconciliation And Ingestion Dry-Run

Date: 2026-06-27

## Disposition

`PASS_GATE2A_RECONCILIATION_NO_WEIGHTING_NO_JRC`

This report records the NODI-side Gate2A reconciliation of the COMSOL Gate2
context export package against the NODI Gate2 candidate register from Report
198. It is an ingestion dry-run only. It does not run COMSOL, rerun NODI,
generate `JOINT_ROUTE_CLASS`, perform q_ch weighting or q_ch*eta, emit
`chi_selected`, compute yield, choose a winner, compute detection probability,
claim wet pass probability, claim clogging rate, or promote V4 context into
runtime/production use.

COMSOL `READY_FOR_NODI_GATE2_REVIEW_CONTEXT_ONLY` is treated as source-package
readiness for context-only review. It is not treated as NODI production
readiness, formula ingestion readiness, weighting authorization, or JRC
authorization.

## Baseline

Current NODI gate state:

- Report 195: `PASS_GATE0_JOINT_READINESS_READ_ONLY`
- Report 196: `PASS_PRE_JRC_DRY_MAPPING_WITH_BLOCKED_REGISTER_NO_OUTPUT_JRC`
- Report 197: `PASS_PRS_ROUTE_VIEW_EXPANSION_GATE1_PRS_COVERAGE_UNBLOCKED`
- Report 198: `PASS_GATE2_CONTEXT_CANDIDATE_PREFLIGHT_NO_WEIGHTING_NO_JRC`

Active NODI production artifacts used for the compatibility dry-run:

| artifact | rows | SHA256 |
|---|---:|---|
| `tmp/nodi_next_artifacts_production_generation_prs_route_view_expansion_20260618/NODI_POSITION_RESPONSE_SURFACE.csv` | 7472 | `9ba83c84a563cd856b2fc624c523843a6e283206d5ac2e592a2b72607645f393` |
| `tmp/nodi_next_artifacts_production_generation_prs_route_view_expansion_20260618/NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv` | 32 | `35c8b43e641631b682df07dc305ee17bc97384e6cf135c94adce791748243ecc` |

Report 198 NODI sidecars re-used in Gate2A:

| artifact | rows | SHA256 |
|---|---:|---|
| `reports/joint_interface_20260627/NODI_COMSOL_GATE2_CONTEXT_CANDIDATE_REGISTER_20260627.csv` | 10 | `e6832aa1d145e0af29c3a000b04a111800036c432cf0e5c7e913e2a49bc26899` |
| `reports/joint_interface_20260627/NODI_COMSOL_GATE2_CONTEXT_BLOCKED_GRAIN_REGISTER_20260627.csv` | 40 | `0fe4396f11c14ddbe5bed8edb487928471765ac7c630ff3adf6413bc5f816cbd` |
| `reports/joint_interface_20260627/NODI_COMSOL_GATE2_CONTEXT_CANDIDATE_REGISTER_SCHEMA_20260627.csv` | 21 | `38e24bfec46f29d53e06bc12aa8b91aded23564838c365a356241da3f2d8f1d5` |

## COMSOL Export Package Read

The COMSOL project was used read-only. No COMSOL project files were modified and
no COMSOL run was launched.

| artifact | rows | SHA256 |
|---|---:|---|
| `roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_PACKET_20260627.md` | n/a | `0193b46ada58b0de497505976efd88bbeab2ed1e3960d5ddae2cdeef9951bf67` |
| `roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_INDEX_20260627.csv` | 97 | `08d307876bc31e02d2f442a7de7475f555941d81c42e3114a722a4c3d0c8d1d3` |
| `roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_GATES_20260627.csv` | 9 | `bae6c7ee5be60ac6757f834cc085d4c5af81cc73a7e604d1e6396842934e0bba` |
| `roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_VALIDATION_20260627.csv` | 12 | `fa1b826df71b5978a3ea692b4b6c96383e2d109e8f7ccf0450f1c6ebcc14a9e6` |
| `roadmap/COMSOL_GATE2_NODI_CONTEXT_EXPORT_MANIFEST_20260627.csv` | 24 | `442c6f39cf36c8a3b0c3449f2d9e3a7dc9dd6a426e1c16c36e02548ba05e1ef0` |

The COMSOL gate rows reconcile into NODI Gate2A as:

| COMSOL gate | COMSOL status | NODI Gate2A disposition |
|---|---|---|
| `G2-TPD-SOURCE-CONTEXT` | `READY_FOR_NODI_GATE2_REVIEW_CONTEXT_ONLY` | source review only, blocked as NODI input until route/view/diameter/bin binding is repaired |
| `G2-TPD-PRS-ALIGNMENT` | `BLOCKED_NEEDS_NODI_PRS_INGESTION_RECHECK` | blocked for direct ingestion; no silent PRS remapping |
| `G2-CHI-PROXY` | `READY_FOR_NODI_GATE2_REVIEW_CONTEXT_ONLY` | partial context-only candidate, no `chi_selected` and no weighting |
| `G2-QCH-SIDECAR` | `BLOCKED_NOT_QCH_SIDECAR` | blocked: no formal q_ch / flow-split sidecar |
| `G2-LOCAL-Q-HYDRAULIC` | `REVIEW_ONLY_LOCAL_Q_CONTEXT` | review-only diagnostic, not Gate2 transport weighting input |
| `G2-V4-NODI-REVIEW` | `REVIEW_ONLY_V4_CONTEXT` | V4 review-only claim ceiling, no runtime/production promotion |
| `G2-WEIGHTING-AUTHORIZATION` | `BLOCKED_NOT_WEIGHTING_AUTHORIZED` | strong claim blocker |
| `G2-JRC-STRONG-CLAIMS` | `BLOCKED_STRONG_CLAIMS_FORBIDDEN` | strong claim blocker |

## Implemented Gate2A Dry-Run

New helper:

```text
tools/audits/build_nodi_comsol_gate2a_ingestion_dry_run.py
```

The helper reads the NODI Report 198 register, the active NODI PRS/EAS
production artifacts, and the COMSOL Gate2 export package. It writes:

| output | rows | SHA256 |
|---|---:|---|
| `reports/joint_interface_20260627/NODI_COMSOL_GATE2A_RECONCILIATION_MATRIX_20260627.csv` | 10 | `56b16e2eb100f5294ead649851b2e0ca39379568fabec9034a89fd9382d3ca91` |
| `reports/joint_interface_20260627/NODI_COMSOL_GATE2A_GRAIN_COMPATIBILITY_20260627.csv` | 30 | `da48edd395771953c933dc5981a034b92e78a3cae21d04ae3e3e76c51797d55e` |
| `reports/joint_interface_20260627/NODI_COMSOL_GATE2A_BLOCKERS_20260627.csv` | 10 | `658c562e0945f91c0a2015752dcfbfdc23ff1786787cab4903f20a0152dec95c` |
| `reports/joint_interface_20260627/NODI_COMSOL_GATE2A_INGESTION_DRY_RUN_REPORT_20260627.json` | n/a | `291d207e7aeb4e951c2cc08fcf6171e7c5a7e26ea293a74512b03ae95a538e81` |
| `reports/joint_interface_20260627/NODI_COMSOL_GATE2A_INGESTION_DRY_RUN_REPORT_20260627.md` | n/a | `4e16afb5dd171bfe1e8de2a35cea6495641b2d22b9a46453837a3bd850e07b44` |

Dry-run counts:

```text
reconciliation rows: 10
grain compatibility rows: 30
blocker rows: 10
Gate2B context-only formal ingestion: PARTIAL
can_enter_weighting_any: false
can_enter_jrc_any: false
```

## Reconciled Status Mapping

The Gate2A status vocabulary is machine-readable and deliberately separate from
production/runtime/weighting states:

| status | meaning |
|---|---|
| `COMSOL_READY_SOURCE_REVIEW_ONLY` | COMSOL package can be reviewed as source context only; it is not NODI production-ready |
| `NODI_RECONCILED_CONTEXT_ONLY_CANDIDATE` | may enter NODI Gate2B context-only formal ingestion with blocked grains preserved |
| `NODI_RECONCILED_REVIEW_ONLY_NOT_GATE2_INPUT` | may be read by reviewers, but is not a Gate2 NODI input |
| `NODI_RECONCILED_BLOCKED_ROUTE_DIAMETER_BIN_VIEW_MISMATCH` | blocked because route, diameter, bin, or NODI view grain does not match current NODI PRS/EAS binding |
| `NODI_RECONCILED_BLOCKED_MISSING_FORMAL_QCH_FLOW_SPLIT` | blocked because a formal q_ch / flow-split sidecar is absent |
| `NODI_RECONCILED_BLOCKED_STRONG_CLAIMS` | blocked because the claim would imply weighting, JRC, production scalar, or downstream decision output |
| `NODI_RECONCILED_V4_REVIEW_ONLY` | V4 context may cap review language only; no runtime or production promotion |

Status counts from the reconciliation matrix:

```text
NODI_RECONCILED_CONTEXT_ONLY_CANDIDATE: 2
NODI_RECONCILED_REVIEW_ONLY_NOT_GATE2_INPUT: 3
NODI_RECONCILED_V4_REVIEW_ONLY: 2
NODI_RECONCILED_BLOCKED_ROUTE_DIAMETER_BIN_VIEW_MISMATCH: 2
NODI_RECONCILED_BLOCKED_MISSING_FORMAL_QCH_FLOW_SPLIT: 1
```

The blockers table additionally records two strong-claim blocker rows for
weighting authorization and JRC/decision claims.

## Grain Compatibility Matrix

Gate2A checked COMSOL artifacts against the current NODI production PRS/EAS
grain surface. The dry-run outcome is:

- `660/W800/D900` can bind at the route key level to current NODI production
  route/view rows for `fixed_660_gold` and `per_wavelength_gold` at `300 nm`.
- `660/W800/D1200` remains absent from current exact PRS route/diameter/view
  grains for the reviewed COMSOL `220 nm` and `300 nm` context rows.
- COMSOL TPD transported-position source/alignment rows have `UNBOUND` NODI
  view. NODI does not silently map those rows across views.
- `220 nm` COMSOL context is never auto-mapped to another NODI diameter.
- COMSOL `edge_norm_1d` quarter bins / edge4 context may be inspected as
  coarse-to-fine review context, but it is not a direct PRS edge20 bin.
- TPD/PRS proxy sidecars remain context proxies. They do not emit
  `chi_selected`.
- local-Q artifacts remain hydraulic/event-tree review context only. They are
  not Gate2 transport weighting inputs.
- V4 artifacts remain review-only claim ceilings. They do not enter NODI
  runtime configuration or production ingestion.

Grain status counts:

```text
NODI_RECONCILED_CONTEXT_ONLY_CANDIDATE: 2
NODI_RECONCILED_REVIEW_ONLY_NOT_GATE2_INPUT: 15
NODI_RECONCILED_BLOCKED_ROUTE_DIAMETER_BIN_VIEW_MISMATCH: 12
NODI_RECONCILED_BLOCKED_MISSING_FORMAL_QCH_FLOW_SPLIT: 1
```

## Gate2B Readiness Answer

NODI can enter Gate2B context-only formal ingestion: `PARTIAL`.

Allowed for Gate2B context-only formal ingestion:

- `G2CTX-CHI-AGG-004`
  (`roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_AGGREGATE_20260622.csv`), only as
  TPD/PRS context proxy review with two exact `660/W800/D900`, `300 nm`,
  route/view grains and blocked grains preserved.
- `G2CTX-CHI-BIN-005`
  (`roadmap/TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv`), only as a
  context-only proxy with explicit edge4-to-edge20 review handling. It is not a
  direct PRS bin and cannot drive formula weighting.

Review-only, not Gate2 input:

- `G2CTX-LQ-ANCHOR-006`: local-Q hydraulic anchor / effective-aperture context.
- `G2CTX-LQ-SCREEN-007`: local-Q event-tree screening diagnostics.
- `G2CTX-LQ-BRANCH-008`: local-Q branch-envelope review decisions.
- `G2CTX-V4-CONTRACT-009`: V4 sample/surface canonical contract.
- `G2CTX-V4-SIDECAR-010`: V4 non-nano NODI review context sidecar.

Blocked before any NODI Gate2 input:

- `G2CTX-TPD-SOURCE-001`: transported-position source context has no NODI view
  binding and includes route/diameter/bin mismatches.
- `G2CTX-TPD-ALIGN-002`: TPD-to-NODI bridge alignment remains blocked for direct
  ingestion until NODI PRS ingestion recheck and explicit route/view/diameter/bin
  binding are provided.
- `G2CTX-QCH-MISSING-003`: no formal q_ch / flow-split sidecar exists.
- `G2-WEIGHTING-AUTHORIZATION`: weighting is not authorized.
- `G2-JRC-STRONG-CLAIMS`: JRC and decision claims remain forbidden.

## Still Blocked Fields

NODI must not interpret any COMSOL context as:

```text
PRS occupancy
q_ch weighting
q_ch*eta
q_ch*chi*eta
chi_selected
route score
yield
winner
detection_probability
JOINT_ROUTE_CLASS
JRC
true W_eff
measured geometry
optical solver claim
NODI runtime configuration
NODI production ingestion
wet pass probability
clogging rate
time-to-clog
recovery
fabrication release
```

The Gate2A helper hard-fails positive output fields for these claims and keeps
all `can_enter_weighting` and `can_enter_jrc` values false.

## What COMSOL Must Provide Next

For a cleaner Gate2B or later Gate2C opening, COMSOL should provide a revised
formal export package with:

- exact NODI route IDs and `NODI_view` binding for transported-position rows
- exact diameter coverage or an explicit reduced-scope decision; `220 nm` must
  stay separate unless NODI later adds a matching production grain
- an explicit coarse-to-fine policy for edge4 / quarter-bin context relative to
  NODI PRS edge20, still marked review-only until a future formula gate exists
- a formal q_ch / flow-split sidecar if q_ch is to be reviewed
- claim-boundary and blocked-use fields preserving context-only use
- V4 fields with all production/runtime/COMSOL launch flags false
- hashes, row counts, producer, evidence class, and required next-gate fields

## Recommendation

Open Gate2B only as a context-only formal ingestion review for the partial
TPD/PRS proxy rows, with blocked grains preserved and no formula use. Do not
open q_ch weighting, `chi_selected`, JRC, yield, winner, or detection probability
from the current package.

The best next COMSOL-side action is a revised formal Gate2 export package that
repairs transported-position route/view/diameter/bin binding and either provides
a real q_ch / flow-split sidecar or keeps q_ch explicitly blocked.

## Verification

Commands:

```bash
python tools/audits/build_nodi_comsol_gate2a_ingestion_dry_run.py \
  --confirm-gate2a-dry-run

python -m py_compile \
  tools/audits/build_nodi_comsol_gate2a_ingestion_dry_run.py \
  tests/test_nodi_comsol_gate2a_ingestion_dry_run.py

ruff check \
  tools/audits/build_nodi_comsol_gate2a_ingestion_dry_run.py \
  tests/test_nodi_comsol_gate2a_ingestion_dry_run.py

python -m pytest \
  tests/test_nodi_comsol_gate2a_ingestion_dry_run.py \
  tests/test_nodi_comsol_gate2_context_candidate_register.py \
  tests/test_nodi_comsol_pre_jrc_dry_mapping.py::test_pre_jrc_dry_mapping_payload_is_no_output_jrc \
  tests/test_nodi_comsol_pre_jrc_dry_mapping.py::test_pre_jrc_validator_rejects_generated_jrc_or_weighted_values \
  tests/test_nodi_comsol_pre_jrc_dry_mapping.py::test_pre_jrc_payload_validator_rejects_v4_context_promotion \
  tests/test_nodi_comsol_next_artifacts_contracts.py::test_comsol_v4_default_context_is_readonly_and_out_of_scope_for_dry_optical \
  tests/test_nodi_comsol_next_artifacts_contracts.py::test_comsol_v4_wet_context_requires_explicit_unbound_or_bound_identities \
  tests/test_nodi_comsol_next_artifacts_contracts.py::test_comsol_v4_context_rejects_production_promotion_or_hash_drift \
  -q
```

Results:

```text
Gate2A dry-run CLI: PASS_GATE2A_RECONCILIATION_NO_WEIGHTING_NO_JRC
py_compile: pass
ruff: pass
focused pytest: 17 passed
```
