# NODI Package C Sidewall Integrated Promotion Ledger

- Disposition: `NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_READY_PREFLIGHT_ONLY`.
- Current head: `859e8355d0d11b8f2fe8f7fe8738f8719686485f` on `main`.
- Ledger version: `sidewall_integrated_promotion_preflight_ledger_v1`.
- Ledger rows: `2`.
- Blocker catalog rows: `9`.
- Promotion lane rows: `18`.
- Blocked promotion rows: `2`.
- The ledger joins q_ch, pressure-flow, optical calibration, wet/detection, and route candidate context at route grain.
- It records blockers and next evidence focus only; it does not emit route_score, winner/JRC, yield, wet pass, or detection probability.
