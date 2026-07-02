# NODI Package C Sidewall COMSOL Target Binding QCH Integration

Disposition: `NODI_PACKAGE_C_SIDEWALL_COMSOL_TARGET_BOUND_FORMAL_QCH_INPUT_INTEGRATED`
Artifact ID: `PACKAGE_C_SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_20260701`
Claim boundary: `comsol_target_binding_and_formal_qch_input_not_route_score_not_yield_not_detection`

## What changed

- Bound the W500/D900 COMSOL launcher, scaffold, pressure runner, connection map, and NODI template by sha256.
- Confirmed the tracked exact pressure-flow result binder has two accepted rows: rectangle limit and theta85 trapezoid.
- Promoted only the formal `q_ch` sidecar input branch into route-formula readiness; route score, winner, yield, detection probability, and production remain false here.
- Recorded the rerun command template for future authorized COMSOL refreshes; no rerun is required for the current formal `q_ch` values.

## Summary

- Accepted exact pressure-flow rows: `2`
- Formal q_ch sidecar current rows: `2`
- Route formula q_ch branch ready rows: `2`
- Rectangle rows: `1`
- Trapezoid rows: `1`
- COMSOL rerun recommended rows: `0`
- Route score current: `False`
- Yield current: `False`
- Detection probability current: `False`

## Next Use

Downstream route/yield/detection work should consume `ROUTE_EVIDENCE_DELTA_ROWS` as the current pressure-flow/q_ch branch state. It still must join detector/blank transfer, wet observation, and route formula packets before any route score or yield/detection number is emitted.
