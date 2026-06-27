# NODI/COMSOL Gate2 Context Candidate Preflight Report

Status: `PASS_GATE2_CONTEXT_CANDIDATE_PREFLIGHT_NO_WEIGHTING_NO_JRC`

This is a context-candidate register only. It writes no `JOINT_ROUTE_CLASS`,
performs no q_ch weighting or q_ch*eta, and computes no yield, winner,
detection probability, wet pass probability, or clogging rate.

## Counts

- register rows: 10
- blocked/review grain rows: 40
- candidate status counts: `{'BLOCKED_ROUTE_DIAMETER_BIN_MISMATCH': 2, 'BLOCKED_MISSING_FORMAL_GATE2_EXPORT': 1, 'GATE2_CANDIDATE_CONTEXT_ONLY_PARTIAL_GRAIN_MATCH': 2, 'REVIEW_ONLY_NOT_GATE2_INPUT': 5}`
- blocked alignment counts: `{'REVIEW_ONLY_MISSING_NODI_VIEW_BINDING': 8, 'BLOCKED_MISSING_PRS_ROUTE_DIAMETER_GRAIN': 6, 'BLOCKED_MISSING_FORMAL_QCH_FLOW_SPLIT_EXPORT': 1, 'BLOCKED_MISSING_PRS_ROUTE_DIAMETER_VIEW_GRAIN': 12, 'REVIEW_ONLY_COARSE_TO_FINE_BIN_GROUP_NOT_DIRECT_PRS_BIN': 8, 'REVIEW_ONLY_NO_NODI_ROUTE_DIAMETER_BIN_BINDING': 5}`

## Outputs

- register: `reports\joint_interface_20260627\NODI_COMSOL_GATE2_CONTEXT_CANDIDATE_REGISTER_20260627.csv`
- blocked grains: `reports\joint_interface_20260627\NODI_COMSOL_GATE2_CONTEXT_BLOCKED_GRAIN_REGISTER_20260627.csv`
- schema: `reports\joint_interface_20260627\NODI_COMSOL_GATE2_CONTEXT_CANDIDATE_REGISTER_SCHEMA_20260627.csv`

## Issues

- none
