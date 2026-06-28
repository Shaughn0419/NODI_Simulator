# NODI/COMSOL Gate2F-EDGE Review-Only Policy Preflight

Date: 2026-06-28

## Disposition

`PASS_GATE2F_EDGE_REVIEW_ONLY_GROUPING_PREFLIGHT_NO_FORMULA_NO_JRC`

Gate2D accepted ledger remains frozen at exactly four aggregate proxy rows. Gate2F-EDGE adds no accepted rows and authorizes no formula, direct PRS bin use, grain-level ingestion, weighting, or JRC.

## Grouping Verdict

COMSOL EDGE skeleton rows reviewed: `16`.
NODI edge20 definition hash: `b8b3358e7218e3ebc704c2c8dcaf2c9a0feb15283fa704610b39f8afc68d5ca3`.

Each edge4 quarter bin is mapped from the NODI edge20 snapshot boundaries into five candidate edge20 bins as a review-only grouping candidate. The mapping is derived from the snapshot, not from a direct PRS bin-use authorization.

## Loss/Error Semantics

Policy is not approved. Future evidence must define information loss, complete coverage, monotonicity/conservativeness checks, error bounds, reproducibility, and conditions that still forbid formula use.

## QCH/BINDING Carry-Forward

QCH remains schema-ready but no formal sidecar is present. BINDING remains fail-closed for 220 nm, D1200/300, and UNBOUND NODI_view. No status change is made in this EDGE preflight.

## Output Hashes

- evidence register: `0ca2b55e97d2955c0341f11e066ad4c10dc3fd004f5db8028a6f6b97c923d5ea`
- grouping preflight: `218d3da461c60c62de099c78404c2a8076ed8c94aaf95ecec50294fa543ebdda`
- row verdict: `0edb261ce0330cb5927956151ac58254651ad22ec36c73f0694040e7389dbcb4`
- loss/error checklist: `b5717ab23a02a65112bd9c77a7904efb14d19691d1447e5eb151355477f56162`
- dashboard: `92b88f947dd5d578711aa9161290d2d624e469681c19e949eaf90bc27d7b0c20`
- JSON report: `d9d6f31331e0664767965fc1fd23b9e266515020551e34559f4158efbbb0a54c`

## Non-Authorization

No q_ch weighting, q_ch*eta, q_ch*chi*eta, chi_selected, route_score, JOINT_ROUTE_CLASS/JRC, yield, winner, detection_probability, wet pass probability, clogging rate, runtime configuration, or production ingestion is authorized.
