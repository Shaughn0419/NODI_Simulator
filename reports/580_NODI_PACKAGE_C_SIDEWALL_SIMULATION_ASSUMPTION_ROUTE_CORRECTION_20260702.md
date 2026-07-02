# NODI Package C Sidewall Simulation-Assumption Route Correction

Date: 2026-07-02

This correction fixes the Package C sidewall route line after independent review.
The active mainline is extreme simulation, not waiting for experimental data
ingestion. Wet, yield, detection, route-score, and ranking branches should
advance from NODI/COMSOL context, explicit formulas, solver or surrogate
assumptions, and hash-bound source artifacts.

## Corrected Route

1. Keep ideal-rectangle and trapezoid sidewall routes side by side.
2. Bind detector/blank, wet/surface, yield, detection, and route inputs as
   simulation or assumption source rows.
3. Allow simulation-derived candidates to advance with explicit provenance,
   uncertainty, controls, formulas, and source hashes.
4. Keep final/production claim fields separate from simulation candidates.

## Field Semantics

- `simulation_route_score_candidate_current` may become true from accepted
  simulation source rows and a ready formula component vector.
- `simulation_top_candidate_current` may become true from simulation route-score
  candidates and a unique top route.
- `detection_probability_simulation_candidate_current`,
  `yield_simulation_candidate_current`, and
  `wet_pass_probability_simulation_candidate_current` may become true from
  accepted simulation-derived value rows.
- `route_score_current`, `winner_current`, `JRC_current`, `yield_current`,
  `detection_probability_current`, `wet_pass_probability_current`, and
  `production_ingestion_current` remain final claim fields and are not directly
  promoted by templates, fixtures, or unreviewed assumptions.

## Guardrail

The route is not blocked on real experiments. It is blocked only when the
simulation/assumption source row is missing, unhashable, outside its declared
validity domain, missing uncertainty semantics, or still a fixture/template row.

## Refreshed Artifacts

The refreshed sidewall artifacts use simulation/source wording while preserving
backward-compatible filenames where needed:

- `571_NODI_PACKAGE_C_SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_20260701.md`
- `573_NODI_PACKAGE_C_SIDEWALL_ROUTE_ACCEPTED_EVIDENCE_SMOKE_20260701.md`
- `574_NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_20260701.md`
- `575_NODI_PACKAGE_C_SIDEWALL_WINNER_JRC_POLICY_REVIEW_20260701.md`
- `576_NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_20260701.md`
- `577_NODI_PACKAGE_C_SIDEWALL_REAL_EVIDENCE_INPUT_WORKSPACE_20260701.md`
- `578_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_20260701.md`
- `579_NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT_20260701.md`
