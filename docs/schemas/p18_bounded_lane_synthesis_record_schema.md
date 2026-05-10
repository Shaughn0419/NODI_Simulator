# P18 Bounded-Lane Synthesis Record Schema

Required role: `bounded_lane_synthesis_stop_continue_record`.

The record binds P6/P8/P10/P12/P14/P16 trace outputs, summarizes rank behavior, and records the stop-or-continue decision.

Required decision: `stop_mechanical_lane_roll_forward_pending_p19_evidence_strategy`.

Required conclusion: `route_promotion_conclusion = not_supported_by_bounded_trace_lanes`.

Required next stage: `P19_next_evidence_strategy_gate`.

Required route behavior:

- six source lanes
- eighteen summary rows
- main-660 top sequence: `main_660_W800_D1400`, `main_660_W800_D1400`, `main_660_W800_D1500`, `main_660_W800_D1500`, `main_660_W800_D1400`, `main_660_W800_D1500`
- swap events: `P8_to_P10`, `P12_to_P14`, `P14_to_P16`

Required blocked fields include calibrated claims, measured/calibration ingest, new execution, route promotion, raw final gates, and future authorization phrase already received.
