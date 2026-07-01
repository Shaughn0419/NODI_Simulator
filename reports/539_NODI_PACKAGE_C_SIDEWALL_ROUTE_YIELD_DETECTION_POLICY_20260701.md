# NODI Package C Sidewall Route/Yield/Detection Policy

- Disposition: `NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_POLICY_READY_NOT_CLAIM_READY`.
- Current head: `fe05a4993936b8b85d54a5be33ddeb7dc224eabb` on `main`.
- Policy rows: `2`.
- Blocker rows: `12`.
- Primary next execution blocks: `qch_or_pressure_flow_validation`.
- Route score, winner/JRC, yield, wet pass probability, and detection probability are not allowed by this policy packet.
- The policy prioritizes formal qch/pressure-flow validation, then detector/blank calibration, wet/surface validation, and selected-annulus panel expansion.
