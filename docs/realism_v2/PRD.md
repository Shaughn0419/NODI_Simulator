# EV/NODI Realism v2 PRD

> Current status: historical R0/P0 contract document. The full v2 no-measured-data lane has since completed and the current no-data closure lives in `reports/140_*`, `reports/147_*`, and `reports/148_*`. Report 88 remains background/provenance. This file remains because tests assert the original contract docs are present.

## Scope

`EV_NODI_realism_v2 / instrument_aware_v2` is an independent sidecar lane for
instrument-aware sanity checks. It must not overwrite v1 full-grid outputs,
selected-annulus bounds, global material defaults, or the all-crossing main
ranking.

The original R0/P0 implementation stopped at the third external review trigger:

- R0 schemas and contract docs exist.
- P0/P0.5 sidecars have focused unit tests.
- v1 compatibility is checked as no-op route identity separation.
- R1.5 micro-anchor dry-run outputs and `run_manifest.json` exist.

## Non-Goals

- This document does not itself authorize later-stage execution. Later R2-R7.2 stages were separately planned, audited, and closed under the no-measured-data boundary.
- No Tsuyama paper-fit continuation.
- No absolute SNR, absolute LOD, biological specificity, or calibrated detector claim.
- No legacy `detector_SNR` or `calibrated_detector_SNR` output names.

## Required Output Provenance

Every new v2 output row must carry:

- `unit`
- `source_type`
- `scenario_id`
- `claim_level`
- `calibration_dependency`
- `module_status`
- `base_route_key`
- `scenario_identity`
- `run_manifest_path`

Without measured detector transfer plus measured blank, detector-SNR-like output
is named `scenario_detector_SNR` and has `SNR_claim_level = absolute_blocked`.

## Stage R1.5 Micro-Anchor

Routes:

- `660 / 800x1400`
- `660 / 700x1500`
- `404 / 600x1300`
- `532 / 600x1500`

Particles:

- `blank`
- `EV70_lowRI`
- `EV100_nominal`
- `Au40`

Fixed scenario bundle: `micro_anchor_nominal_sanity`.

The micro-anchor is a dry-run and numerical sanity check only. It is not a
ranking run and does not authorize R2.
