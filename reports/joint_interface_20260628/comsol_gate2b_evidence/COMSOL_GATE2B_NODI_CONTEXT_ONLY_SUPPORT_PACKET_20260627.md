# COMSOL Gate2B NODI Context-Only Support Packet - 2026-06-27

## Scope

This packet is no-run, no-MPH, and no-new-physics. It refines the already generated COMSOL Gate2A binding package into a NODI-facing Gate2B support package and a Gate2C repair/requirements track. It does not start COMSOL, does not load `.mph`, does not write to the NODI repository, and does not emit weighting, `chi_selected`, q_ch*eta, q_ch*chi*eta, JRC, route_score, yield, winner, detection_probability, time-to-clog, recovery, calibrated clogging, or fabrication release outputs.

## Gate2B Disposition

Status: `PASS_GATE2B_CONTEXT_ONLY_SUPPORT_PACKAGE_READY_WITH_PARTIAL_PROXY_SCOPE`.

Only TPD/PRS chi context proxy aggregate/bin rows are allowed into the Gate2B support rows. They remain context-only proxy review support and are not production/runtime ingestion, not `chi_selected`, not q_ch weighted, and not formula inputs.

Allowed row count: 80 rows.

Allowed composition:

- proxy aggregate rows: 16
- proxy bin rows: 64

Automation binding distinction:

- all allowed rows are `gate2b_artifact_level_context_candidate=true`
- all allowed rows are `gate2b_grain_level_context_ingestion_authorized=false`
- proxy-bin rows explicitly carry `EDGE4_TO_EDGE20_REVIEW_REQUIRED` and `ARTIFACT_LEVEL_ONLY` policy text, so edge4/quarter bins cannot be silently treated as direct PRS edge20 grains

## Quarantine / Review-Only Disposition

The quarantine register is readable by NODI for review, but none of its rows may enter Gate2B formal context-only ingestion or formulas.

Quarantine row count: 79 rows.

Quarantine composition:

- `LOCAL_Q_REVIEW_ONLY`: 2
- `QCH_PROVENANCE_ONLY_NOT_FORMAL_SIDECAR`: 1
- `STRONG_CLAIM_OR_BINDING_BLOCKER`: 10
- `TPD_SOURCE_OR_ALIGNMENT_BINDING_BLOCKED`: 64
- `V4_REVIEW_ONLY`: 2

## Gate2C Transported-Position Binding Repair

`roadmap/COMSOL_GATE2B_TPD_BINDING_REPAIR_PLAN_20260627.csv` contains 65 rows. It keeps transported-position source/alignment rows out of Gate2B ingestion and defines the repair track. Missing `NODI_view` binding, 220 nm direct-match absence, 300 nm candidate-only status, D1200 exact-grain uncertainty, and edge4-to-edge20 coarse/fine policy are all preserved as blockers or review-policy needs. The plan marks `requires_new_comsol_solve=false` for transported-position binding repair rows, because this phase is a binding/export repair, not a physical recomputation. It still requires NODI PRS coverage recheck and a new COMSOL export/binding artifact before Gate2C can advance.

## Formal q_ch / Flow-Split Sidecar Requirement

`roadmap/COMSOL_GATE2B_QCH_FORMAL_SIDECAR_REQUIREMENTS_20260627.csv` contains 18 requirement rows, with the paired `.md` narrative. The current Gate2A q_ch export remains provenance-only and is quarantined from Gate2B allowed rows. A future formal sidecar must include route/view/diameter/bin binding, q_ch and flow-split values, units, normalization, solve/provenance id, geometry hash, integration definition, review/uncertainty flags, and validation checks. `qch_weighting_authorized` remains false until NODI opens a dedicated gate.

## Validation Summary

`roadmap/COMSOL_GATE2B_NODI_SUPPORT_VALIDATION_20260627.csv` status counts from the latest local run:

- `BLOCKED_AS_EXPECTED`: 1
- `PASS`: 8
- `PASS_BLOCKED_AS_EXPECTED`: 3

No validation check failed. `BLOCKED_AS_EXPECTED` and `PASS_BLOCKED_AS_EXPECTED` rows preserve intended blockers rather than promoting them.

## Recommended NODI Ingestion Order

1. Ingest `COMSOL_GATE2B_NODI_ALLOWED_CONTEXT_ROWS_20260627.csv` only as artifact-level Gate2B partial context-only proxy support, with all authorization flags false.
2. Treat proxy-bin rows as artifact-level context candidates but grain-level non-ingestable until NODI resolves the edge4-to-edge20 review policy.
3. Load `COMSOL_GATE2B_NODI_QUARANTINE_REVIEW_ONLY_ROWS_20260627.csv` as a read-only blocker/review register, not as formal ingestion rows.
4. Use `COMSOL_GATE2B_TPD_BINDING_REPAIR_PLAN_20260627.csv` to plan Gate2C transported-position binding repair.
5. Use `COMSOL_GATE2B_QCH_FORMAL_SIDECAR_REQUIREMENTS_20260627.csv` before requesting any future q_ch or flow-split sidecar generation.

## Independent Review

Reviewer A - path/SHA/row_count/manifest reproducibility: PASS. All allowed and quarantine source references carry source SHA and row_count; reviewer A found 0 SHA mismatches and 0 row-count mismatches.

Reviewer B - NODI binding semantics: PASS. All TPD source/alignment, q_ch provenance, local-Q, V4, and blocker rows are quarantined. Allowed rows are limited to TPD/PRS proxy aggregate/bin context and preserve partial-grain review boundaries.

Reviewer C - forbidden output leakage: PASS. All authorization flags remain false and no forbidden positive-output columns are present. The files include negative guardrail flags only, such as `is_chi_selected=false`.

Reviewer D - future-readiness: PASS after P1 fix. Reviewer D flagged edge4/edge20 automation ambiguity; the allowed CSV now distinguishes artifact-level context candidacy from grain-level ingestion authorization and forces proxy-bin grain-level authorization false until NODI defines edge4-to-edge20 policy.

## Residual Risks

- `220 nm` remains no-direct-match unless NODI explicitly adds or approves a matching policy.
- `300 nm` remains candidate-only until NODI confirms current PRS production route/view/diameter/bin coverage.
- edge4/quarter TPD bins are not direct PRS edge20 bins; they require a coarse-to-fine review policy.
- local-Q and V4 remain review-only claim ceilings and are not Gate2B transport weighting inputs.
