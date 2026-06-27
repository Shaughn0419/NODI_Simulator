# Report 198 - NODI/COMSOL Gate2 Context Candidate Ingestion Preflight

Date: 2026-06-27

## Disposition

`PASS_GATE2_CONTEXT_CANDIDATE_PREFLIGHT_NO_WEIGHTING_NO_JRC`

This report records the NODI-side Gate2 context candidate ingestion preflight.
It defines and materializes a context-only candidate register for future
NODI-COMSOL linkage. It does not run COMSOL, rerun NODI, generate
`JOINT_ROUTE_CLASS`, perform q_ch weighting or q_ch*eta, compute yield, choose a
winner, compute detection probability, claim true `W_eff`, claim measured
geometry, claim wet pass probability, claim clogging rate, or promote an optical
solver result.

## Current Gate State

The current NODI linkage baseline is:

- Report 195: `PASS_GATE0_JOINT_READINESS_READ_ONLY`
- Report 196: `PASS_PRE_JRC_DRY_MAPPING_WITH_BLOCKED_REGISTER_NO_OUTPUT_JRC`
- Report 197: `PASS_PRS_ROUTE_VIEW_EXPANSION_GATE1_PRS_COVERAGE_UNBLOCKED`

After Report 197, the active NODI production artifacts are:

- PRS:
  `tmp/nodi_next_artifacts_production_generation_prs_route_view_expansion_20260618/NODI_POSITION_RESPONSE_SURFACE.csv`
  - rows: `7472`
  - SHA256: `9ba83c84a563cd856b2fc624c523843a6e283206d5ac2e592a2b72607645f393`
- EAS:
  `tmp/nodi_next_artifacts_production_generation_prs_route_view_expansion_20260618/NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv`
  - rows: `32`
  - SHA256: `35c8b43e641631b682df07dc305ee17bc97384e6cf135c94adce791748243ecc`

Gate1 dry mapping has `64` dry rows over `8` route/view keys and no remaining
PRS route/view blocker. The remaining blocked fields are future authorization
fields only.

## Implemented Preflight

New helper:

```text
tools/audits/build_nodi_comsol_gate2_context_candidate_register.py
```

The helper reads the current NODI PRS/EAS artifacts and read-only COMSOL roadmap
artifacts, then writes:

```text
reports/joint_interface_20260627/NODI_COMSOL_GATE2_CONTEXT_CANDIDATE_PREFLIGHT_REPORT_20260627.json
reports/joint_interface_20260627/NODI_COMSOL_GATE2_CONTEXT_CANDIDATE_PREFLIGHT_REPORT_20260627.md
reports/joint_interface_20260627/NODI_COMSOL_GATE2_CONTEXT_CANDIDATE_REGISTER_20260627.csv
reports/joint_interface_20260627/NODI_COMSOL_GATE2_CONTEXT_BLOCKED_GRAIN_REGISTER_20260627.csv
reports/joint_interface_20260627/NODI_COMSOL_GATE2_CONTEXT_CANDIDATE_REGISTER_SCHEMA_20260627.csv
```

Output hashes:

```text
report json:      48e2e8987681a3b497b941ff35f0b07368506c830273d051f48476f31483694c
report md:        bc0619345f26355c139b7af00b325798c1c5c9886d1e553aae8109cef8cfd84d
candidate csv:    e6832aa1d145e0af29c3a000b04a111800036c432cf0e5c7e913e2a49bc26899
blocked grains:   0fe4396f11c14ddbe5bed8edb487928471765ac7c630ff3adf6413bc5f816cbd
schema csv:       38e24bfec46f29d53e06bc12aa8b91aded23564838c365a356241da3f2d8f1d5
```

Counts:

```text
candidate register rows: 10
blocked/review grain rows: 40
schema rows: 21
```

## Gate2 Candidate Register Schema

The register schema explicitly covers:

```text
source_artifact
sha256
row_count
producer
evidence_class
route_key
diameter_basis
bin_basis
claim_boundary
allowed_use
blocked_use
required_next_gate
v4_context_binding
```

Additional control fields record candidate status, grain alignment status,
matched-grain count, blocked-grain count, and review notes.

The validator hard-fails any positive output fields for q_ch*eta, winner,
detection_probability, `JOINT_ROUTE_CLASS`/JRC, yield, wet pass probability,
clogging rate, true `W_eff`, or measured geometry. It also hard-fails V4
production promotion by keeping the existing COMSOL V4 read-only context guard
active with all production/runtime/COMSOL launch flags false.

## Candidate Classification

| register row | source | rows | SHA256 | status |
|---|---:|---:|---|---|
| `G2CTX-TPD-SOURCE-001` | `TRANSPORTED_POSITION_SOURCE_SMOKE_COMBINED_RETRY3_20260621.csv` | 32 | `1c0d902dc01a39e3a3cc6c104696b782ddd06235d1630051d2b5163d6d827b61` | `BLOCKED_ROUTE_DIAMETER_BIN_MISMATCH` |
| `G2CTX-TPD-ALIGN-002` | `TPD_TO_NODI_BRIDGE_ALIGNMENT_TABLE_20260621.csv` | 32 | `67094e7f2a7045c368dd47f1d169b7be4cb0a4f409b8765b6505fafec03ae0a3` | `BLOCKED_ROUTE_DIAMETER_BIN_MISMATCH` |
| `G2CTX-QCH-MISSING-003` | formal q_ch / flow split sidecar | 0 | `MISSING_UNTIL_FORMAL_GATE2_EXPORT` | `BLOCKED_MISSING_FORMAL_GATE2_EXPORT` |
| `G2CTX-CHI-AGG-004` | `TPD_PRS_CHI_CONTEXT_SIDECAR_AGGREGATE_20260622.csv` | 16 | `8f2be800709a2332ddecca6e43e1ccc619aa93b502eeeb0bffb5b41f9e8a6381` | `GATE2_CANDIDATE_CONTEXT_ONLY_PARTIAL_GRAIN_MATCH` |
| `G2CTX-CHI-BIN-005` | `TPD_PRS_CHI_CONTEXT_SIDECAR_BINS_20260622.csv` | 64 | `8c2f785d5d4d7a16af0b4817b7f97a7ecf8824e84cc2f9b602e1b67906dcefc1` | `GATE2_CANDIDATE_CONTEXT_ONLY_PARTIAL_GRAIN_MATCH` |
| `G2CTX-LQ-ANCHOR-006` | `EV_PBS_ENTRANCE_LOCAL_Q_EFFECTIVE_APERTURE_LOCAL_Q_EVENT_TREE_BRIDGE_INPUT_20260623.csv` | 300 | `d9abebc223680e97eda9113af0a97b38394a742495c121de854831b241c64c3b` | `REVIEW_ONLY_NOT_GATE2_INPUT` |
| `G2CTX-LQ-SCREEN-007` | `EV_PBS_LOCAL_Q_EVENT_TREE_BRIDGE_SCREENING_RESULTS_20260623.csv` | 1833 | `71c06622949b2da0de20637d81ec182728440ee6e759143e159c94c5af3f1019` | `REVIEW_ONLY_NOT_GATE2_INPUT` |
| `G2CTX-LQ-BRANCH-008` | `EV_PBS_LOCAL_Q_BRANCH_ENVELOPE_REVIEW_GATE_BRANCH_DECISIONS_20260624.csv` | 3 | `a901231000aa91f7abdc1d269597d14e7d6b1eb9473b3a4d4231a05f12ce9c28` | `REVIEW_ONLY_NOT_GATE2_INPUT` |
| `G2CTX-V4-CONTRACT-009` | `EV_PBS_SAMPLE_SURFACE_CANONICAL_CONTRACT_V4_20260627.json` | 1 | `2bd97d7684a582343da05bc519f47d598baf29efa5e0157ea8330e9fae223d92` | `REVIEW_ONLY_NOT_GATE2_INPUT` |
| `G2CTX-V4-SIDECAR-010` | `EV_PBS_V4_NON_NANO_NODI_REVIEW_CONTEXT_SIDECAR_ROWS_20260627.csv` | 16 | `384181edfb6043716623ddd32f38d72fb941867a759f8bf877348ad2c0f4ca6b` | `REVIEW_ONLY_NOT_GATE2_INPUT` |

Interpretation:

- COMSOL transported-position source/alignment context is present, but current
  rows are blocked for NODI ingestion because they lack NODI view binding and
  contain route/diameter/bin grain mismatches.
- No formal q_ch / flow split Gate2 export exists. q_ch remains blocked.
- TPD/PRS context proxy rows are the only current Gate2 context candidates, but
  only as partial-grain context. They have `2` matched NODI PRS grains and
  explicit blocked-grain rows for missing diameters and coarse bin grouping.
- local-Q hydraulic anchor, event-tree screening, and branch-envelope packets are
  review-only diagnostics, not Gate2 NODI inputs.
- V4 sample/surface artifacts are review-only context. They may bind claim
  ceilings and future review language, but cannot be production ingestion,
  runtime configuration, wet pass probability, clogging, yield, or winner input.

## Blocked / Review Grain Register

The blocked-grain register records:

```text
BLOCKED_MISSING_FORMAL_QCH_FLOW_SPLIT_EXPORT: 1
BLOCKED_MISSING_PRS_ROUTE_DIAMETER_GRAIN: 6
BLOCKED_MISSING_PRS_ROUTE_DIAMETER_VIEW_GRAIN: 12
REVIEW_ONLY_COARSE_TO_FINE_BIN_GROUP_NOT_DIRECT_PRS_BIN: 8
REVIEW_ONLY_MISSING_NODI_VIEW_BINDING: 8
REVIEW_ONLY_NO_NODI_ROUTE_DIAMETER_BIN_BINDING: 5
```

This is the key Gate2 preflight result: route, diameter, and bin mismatches are
not silently mapped. They are made explicit as blocked or review-only rows.

## Still Blocked Fields

The NODI side still must not interpret any COMSOL context as:

```text
PRS occupancy
q_ch*eta
chi_selected
route score
yield
winner
detection_probability
JOINT_ROUTE_CLASS
true W_eff
measured geometry
optical solver claim
wet pass probability
clogging rate
```

The helper and tests also keep q_ch weighting, q_ch*eta, winner,
detection_probability, JRC, V4 production ingestion, count prediction, optical
update, runtime configuration, COMSOL launch, and MPH load blocked.

## What Is Missing Before Formal Gate2 Ingestion

NODI can read the current context register, but formal Gate2 ingestion still
needs a COMSOL export package that provides:

- exact NODI route IDs and `NODI_view` binding for transported-position rows
- exact diameter grain compatibility or an explicit reduced-scope decision
- explicit coarse-to-fine bin aggregation policy for TPD edge4 to PRS edge20
- a formal q_ch / flow split sidecar if q_ch is to be reviewed at all
- claim-boundary fields preserving context-only use
- V4 context binding with production/runtime/COMSOL launch flags false
- hashes, row counts, producer, evidence class, and required next-gate fields

## Recommendation

Open the next review as a Gate2 ingestion review only if the scope is
context-register review and partial TPD/PRS context proxy review. Do not open
weighting, JRC, yield, winner, or detection-probability work from the current
packets.

The cleaner next action is to ask the COMSOL side for a formal Gate2 export
package with NODI route/view/diameter/bin bindings and a blocked q_ch disposition
or a real q_ch sidecar. Existing COMSOL context is readable by NODI as
review-only/preflight context, but it is not sufficient for formal weighted
joint ingestion.

## Verification

Commands:

```bash
python tools/audits/build_nodi_comsol_gate2_context_candidate_register.py \
  --confirm-gate2-context-preflight

python -m py_compile \
  tools/audits/build_nodi_comsol_gate2_context_candidate_register.py \
  tests/test_nodi_comsol_gate2_context_candidate_register.py

python -m pytest \
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
Gate2 context candidate preflight: PASS
py_compile: pass
focused pytest: 11 passed
```
