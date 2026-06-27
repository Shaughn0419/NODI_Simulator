# NODI/COMSOL Gate2A Ingestion Dry-Run Report

Status: `PASS_GATE2A_RECONCILIATION_NO_WEIGHTING_NO_JRC`

This is a reconciliation and dry-run report only. It writes no JRC,
performs no q_ch weighting or q_ch*eta, emits no chi_selected, and
computes no yield, winner, detection probability, wet pass probability,
or clogging rate.

## Counts

- reconciliation rows: 10
- grain compatibility rows: 30
- blocker rows: 10
- Gate2B context-only formal ingestion: `PARTIAL`
- reconciled status counts: `{'NODI_RECONCILED_BLOCKED_ROUTE_DIAMETER_BIN_VIEW_MISMATCH': 2, 'NODI_RECONCILED_BLOCKED_MISSING_FORMAL_QCH_FLOW_SPLIT': 1, 'NODI_RECONCILED_CONTEXT_ONLY_CANDIDATE': 2, 'NODI_RECONCILED_REVIEW_ONLY_NOT_GATE2_INPUT': 3, 'NODI_RECONCILED_V4_REVIEW_ONLY': 2}`

## Outputs

- reconciliation matrix: `reports\joint_interface_20260627\NODI_COMSOL_GATE2A_RECONCILIATION_MATRIX_20260627.csv`
- grain compatibility: `reports\joint_interface_20260627\NODI_COMSOL_GATE2A_GRAIN_COMPATIBILITY_20260627.csv`
- blockers: `reports\joint_interface_20260627\NODI_COMSOL_GATE2A_BLOCKERS_20260627.csv`

## Issues

- none
