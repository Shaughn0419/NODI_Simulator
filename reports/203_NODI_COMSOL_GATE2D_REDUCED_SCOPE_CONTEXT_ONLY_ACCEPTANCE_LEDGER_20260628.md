# Report 203 - NODI/COMSOL Gate2D Reduced-Scope Context-Only Acceptance Ledger

Date: 2026-06-28

## Disposition

`PASS_GATE2D_REDUCED_SCOPE_CONTEXT_ONLY_ACCEPTANCE_LEDGER_NO_WEIGHTING_NO_JRC`

NODI accepts exactly four COMSOL Gate2D reduced-scope rows as context-only, artifact-level ledger entries. This is not grain-level ingestion, formula use, weighting, JRC, runtime configuration, or production ingestion.

## Accepted Rows

- `G2D-RS-CAND-001` / `G2C-CAND-0077`: W800/D900, 300 nm, fixed_660_gold, residence_time_weighted.
- `G2D-RS-CAND-002` / `G2C-CAND-0078`: W800/D900, 300 nm, fixed_660_gold, velocity_weighted.
- `G2D-RS-CAND-003` / `G2C-CAND-0079`: W800/D900, 300 nm, per_wavelength_gold, residence_time_weighted.
- `G2D-RS-CAND-004` / `G2C-CAND-0080`: W800/D900, 300 nm, per_wavelength_gold, velocity_weighted.

`velocity_weighted` and `residence_time_weighted` are TPD proxy aggregation descriptors only. They are not NODI route weighting and not q_ch weighting.

## Output Hashes

- accepted ledger: `cf997f5cefd2267f507f3697680d4d314b986ea6a89f914eb66a993f9a1cdce1`
- accepted rows: `33cfb74a69180717f8adc38406ec4295c12805b4854d60ff7a0c712e2aa5902b`
- source receipts: `9dc5938ff419777633d2af5ef308c273683f5b365beb253199e88126cc5e407b`
- forbidden audit: `938d3ed24dcf6880187cebc6d8fdf7a02f750775973c09100380aa409f4ac638`
- blocker carry-forward: `e270bfaa65c6e0d66bc90f58ab768a617f8f8eb68a63b34474aa2f014a6c7976`
- self-review: `96b6912372a3eea6b6eeb7ca844bd2db87619aa71b575d7d93ba11dc9853a727`

## Carry-Forward Blockers

220 nm remains blocked. D1200/300 remains blocked/uncertain. TPD source/alignment remains blocked by NODI_view binding. edge4 bin proxy remains review-only because edge4-to-edge20 policy is not approved. q_ch remains quarantine/provenance-only. local-Q, V4, and strong claims remain review-only or hard blocked.

## Future Gates

- Gate2E-EDGE: edge4-to-edge20 policy review/possible context acceptance, not formula.
- Gate2E-QCH: formal q_ch / flow-split sidecar feasibility/receipt, not weighting.
- Gate2E-BINDING: 220 nm / D1200 / TPD source view binding repair.
- Gate3-AUTHORIZATION: only a dedicated future authorization gate may discuss weighting/JRC.
