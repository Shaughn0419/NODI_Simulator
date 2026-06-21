# Report 189 - Continue NODI Work Without Waiting For COMSOL Review

Date: 2026-06-18

## Disposition

NODI_CAN_CONTINUE_LOCALLY_WITHOUT_COMSOL_REVIEW

COMSOL read-only review is recommended before downstream joint use, but it is not
a hard stop for NODI-side local work.

## What Can Continue Now

NODI may continue with local-only work:

- harden validators and regression tests
- cleanly package production artifacts
- build NODI-side handoff manifests and provenance indexes
- prepare downstream import/readiness checks
- add missing negative tests around authorization and candidate validation
- improve CLI/report wording
- scan for forbidden claims and boundary drift
- prepare a future `JOINT_ROUTE_CLASS` input-readiness package

These actions must remain local/read-only with respect to COMSOL and must not claim
COMSOL acceptance.

## What Still Needs COMSOL Review Or Explicit Future Authorization

Do not proceed to these without a separate review/authorization gate:

- COMSOL run
- NODI rerun that changes physical evidence claims
- `JOINT_ROUTE_CLASS` regeneration
- joint NODI/COMSOL production merge
- q_ch weighting or q_ch*eta
- yield, winner, detection probability, or ranking conclusions beyond the existing
  NODI claim boundary
- true W_eff, measured geometry, optical solver output, fabrication release, or P3
  solver conclusions

## Practical Route

Continue in two lanes:

1. NODI local lane: keep hardening the production gate and create self-contained
   handoff/readiness manifests.
2. COMSOL review lane: send the prepared read-only package when convenient, but do
   not block NODI local cleanup and packaging on that response.

## Current Ground Truth

The latest NODI production-generation output is:

- `tmp/nodi_next_artifacts_production_generation_full_prs_eas_20260618/`
- status: `PASS_PRODUCTION_GENERATION`
- PRS rows: 1868
- EAS rows: 32
- COMSOL run: false
- `JOINT_ROUTE_CLASS` regenerated: false

This is a NODI-side production artifact state, not yet a COMSOL-accepted joint state.
