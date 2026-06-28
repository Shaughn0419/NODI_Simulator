# NODI/COMSOL Gate2D Reduced-Scope Acceptance Preflight

Date: 2026-06-28

## Disposition

`PASS_GATE2D_REDUCED_SCOPE_ACCEPTANCE_PREFLIGHT_NO_WEIGHTING_NO_JRC`

This is a reduced-scope acceptance preflight only. It does not open weighting, q_ch weighting, chi_selected, JRC, yield, winner, detection_probability, runtime configuration, or production ingestion.

## Key Answers

- COMSOL Gate2C package counts consistent: `True`.
- COMSOL errata found: `True`.
- Four W800/D900/300 aggregate proxy candidates pass NODI PRS coverage preflight: `YES`.
- Open Gate2D reduced-scope context-only acceptance ledger now: `PARTIAL/PENDING` unless COMSOL errata is present.
- edge4 policy approved: `NO`.
- formal q_ch sidecar exists: `NO`.
- weighting/JRC/chi_selected/yield/winner/detection_probability allowed: `NO`.

## Consistency Audit

The master packet, actual candidate export CSV, COMSOL reconciliation/errata, and validation observed counts agree. COMSOL Gate2D reduced-scope candidate files were found and included in this preflight.

## 4-Row Candidate Verdict

Rows `G2C-CAND-0077` through `G2C-CAND-0080` are W800/D900/300 aggregate proxy candidates for `fixed_660_gold` and `per_wavelength_gold`, with `velocity_weighted` or `residence_time_weighted` TPD proxy aggregation basis. These basis labels are context descriptors only, not NODI route weighting and not q_ch weighting.

## Output Hashes

- consistency audit: `843377fc8f70aa634d31d44e443f4868d59354c51b5e89ff20a09143e372df9c`
- status reconciliation: `0b04f625c1e2aecbafa12eb3ec9f2bc42e3d7466cc0412fb4b4c95dff853e6a5`
- reduced scope verdict: `5c178a0d6ba373ba8e0bff8290f84374f233bec641cccb4be1d750b46233bb12`
- acceptance preflight: `475fc62ece433b933e6f69ee56c74fea1fd59f5a779605680b3261f9c10798a4`
- exclusion register: `72288a6d370a8d501830635f8ecfbc493d3a41f5c807ebe3f9f8b7e40bf89d27`
- self-review: `51585e67fe1cfc42996aee1521b123b4ac10460fbcf3801f622753c84ce4fb2d`

## Carry-Forward Blockers

220 nm remains blocked with no direct PRS match. D1200/300 remains blocked/uncertain. TPD source/alignment rows remain blocked by missing or unbound NODI view. edge4 bin proxy remains review-only because edge4-to-edge20 policy is not approved. q_ch remains provenance-only/quarantine; local-Q, V4, and strong claims stay review-only or hard blocked.
