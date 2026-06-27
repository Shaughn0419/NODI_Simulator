# Report 200 - NODI/COMSOL Gate2B Context-Only Formal Ingestion

Date: 2026-06-27

## Disposition

`PASS_GATE2B_CONTEXT_ONLY_FORMAL_INGESTION_PARTIAL_NO_WEIGHTING_NO_JRC`

This is a partial context-only formal ingestion ledger. It is not production ingestion, not runtime configuration, not q_ch weighting, and not JRC.

## Scope

- `context_only_formal_ingestion_allowed = true` only for `G2CTX-CHI-AGG-004` and `G2CTX-CHI-BIN-005`.
- `can_enter_weighting = false` globally.
- `can_enter_jrc = false` globally.
- `is_chi_selected = false` globally.
- `is_production_ingestion = false` globally.
- `is_runtime_configuration = false` globally.

## Counts

- formal register rows: `2`
- ingested context rows: `2`
- quarantine/review-only rows: `10`
- blocked grain disposition rows: `30`
- forbidden claim audit rows: `16`
- self-review rows: `4`
- q_ch provenance rows read: `92`

## Outputs

- formal context register: `NODI_COMSOL_GATE2B_FORMAL_CONTEXT_INGEST_REGISTER_20260627.csv` SHA256 `46e6619d93345e120ddd0478981996ee669ef82d648fdfc3d255718248b25c55`
- ingested context rows: `NODI_COMSOL_GATE2B_INGESTED_CONTEXT_ROWS_20260627.csv` SHA256 `372ae739fd52c142c6bbd5dc5545799b16314f95a9f652776818f15403f82e8f`
- quarantine register: `NODI_COMSOL_GATE2B_QUARANTINE_REVIEW_ONLY_REGISTER_20260627.csv` SHA256 `84068b6ea46cd8bda7ba3bff407ecf8b8c5e61c3748fe43e09bade7efd8b3062`
- blocked grain disposition: `NODI_COMSOL_GATE2B_BLOCKED_GRAIN_DISPOSITION_20260627.csv` SHA256 `30f894d5fbf4529ef67cd491387d50583fdf26c6b08168404ee4f5aa602b2d39`
- forbidden claim audit: `NODI_COMSOL_GATE2B_FORBIDDEN_CLAIM_AUDIT_20260627.csv` SHA256 `03192825b240563276bdfb10b901972ac2aa33ad570a2d22ea486e22238b95ff`
- self-review findings: `NODI_COMSOL_GATE2B_SELF_REVIEW_FINDINGS_20260627.csv` SHA256 `94d760cf7d92cf2f204249940e6b7306a79cd28afe998bd3890afe4b14a45008`
- Gate2C required export schema: `NODI_COMSOL_GATE2C_REQUIRED_EXPORT_SCHEMA_20260627.csv` SHA256 `109c665039b0a742e2a819360cdc768d8b7854300ad6d773d9585517df2c7bde`

## Input Evidence

- NODI Gate2A matrix rows: `10`, SHA256 `56b16e2eb100f5294ead649851b2e0ca39379568fabec9034a89fd9382d3ca91`
- NODI Gate2A grain rows: `30`, SHA256 `da48edd395771953c933dc5981a034b92e78a3cae21d04ae3e3e76c51797d55e`
- NODI Gate2A blockers rows: `10`, SHA256 `658c562e0945f91c0a2015752dcfbfdc23ff1786787cab4903f20a0152dec95c`
- COMSOL Gate2A binding crosswalk rows: `149`, SHA256 `8ee93881e2bb39ecc19b59ce5637408576d0d83b1590ef103c56b94cadd95465`
- COMSOL Gate2A q_ch provenance rows: `92`, SHA256 `2f375adf48640b44ffb2a7919da4efa0502cfaeb5f5f0b22fe94268f2722a3a6`

## Formal Context-Only Ingested Rows

- `G2CTX-CHI-AGG-004`: TPD/PRS proxy aggregate, only for context-only review over current matched `660/W800/D900`, `300 nm` route/view grains.
- `G2CTX-CHI-BIN-005`: TPD/PRS proxy bin context, only with edge4-to-edge20 review-only grouping; not a direct PRS bin.

## Quarantine / Review-Only / Blocked

- TPD source/alignment remain source-ready but blocked: missing `NODI_view` and route/diameter/bin mismatches.
- q_ch remains provenance-only quarantine: no formal q_ch / flow-split sidecar.
- local-Q remains review-only hydraulic/event-tree diagnostic context.
- V4 remains review-only claim ceiling with production/runtime/launch flags false.
- weighting, JRC, yield, winner, detection probability, wet pass, clogging, runtime, and production promotion remain hard blocked.

## Gate2C Request

COMSOL should provide a formal NODI-bound transported-position sidecar with explicit route/view/diameter/bin binding, an edge4-to-edge20 policy, and a formal q_ch / flow-split sidecar if q_ch is to move beyond provenance-only. All forbidden claims must remain absent or false until separately authorized.

## Self-Review

- Reviewer A: PASS, provenance/hash/row_count/path reproducibility.
- Reviewer B: PASS, forbidden claim leakage remains blocked.
- Reviewer C: PASS, grain semantics preserve 220 nm, D1200, missing view, and edge4 review-only blockers.
- Reviewer D: PASS, COMSOL source-ready context is not upgraded to NODI production-ready.

## Verification

Run the Gate2B helper with `--confirm-gate2b-formal-context-only`, then run `py_compile`, `ruff`, and focused pytest before committing.
