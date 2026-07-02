# 592 NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS 20260702

## Disposition

- disposition: `NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS_READY`
- primary_answer_frame: `dimension_annulus_interference_response_context`
- not_primary_answer_frame: `route_winner_scoreboard_or_probability`
- claim_boundary: `bounded_nodi_event_context_prs_sidewall_v2_not_production_not_probability`

## What This Adds

This block converts the 591 executed bounded NODI sidewall event shards into sparse PRS sidewall v2 event-context rows. It keeps the source route as a join key, preserves the selected annulus source, computes trapezoid-local particle-center support and wall-distance diagnostics, and keeps every row out of production/runtime/probability use.

## Counts

- executed_event_shard_rows: `24`
- prs_candidate_rows: `24`
- delta_context_rows: `12`
- trapezoid_candidate_rows: `12`
- rectangle_baseline_rows: `12`
- blocked_particle_support_rows: `0`
- decision_use_allowed_rows: `0`

## Mainline Guard

The rows are intentionally PRS-v2-shaped sparse context rows, not production PRS. They are meant to feed the next synthesis on sidewall-driven dimension-window shifts, selected-annulus range remaps, and interference/response sensitivity.

## COMSOL V4 Context

- assumption_set_id: `EV_PBS_SAMPLE_SURFACE_ASSUMPTION_SET_V4_20260627`
- assumption_set_version: `4.0.0`

## Alignment

- alignment_check_rows: `7`
- failed_alignment_check_rows: `0`
- semantic_digest: `69b26c4a63ad6fc15b384adb06afd89ec94915edb9854765b953202d3b133ec4`

## Manifest

- `status`: `reports/joint_interface_20260702/NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS_STATUS_20260702.json`
- `manifest`: `reports/joint_interface_20260702/NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS_MANIFEST_20260702.csv`
- `source_lock`: `reports/joint_interface_20260702/NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS_SOURCE_LOCK_20260702.csv`
- `dirty_context`: `reports/joint_interface_20260702/NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS_DIRTY_CONTEXT_20260702.csv`
- `candidate_rows`: `reports/joint_interface_20260702/NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS_CANDIDATE_ROWS_20260702.csv`
- `delta_context_rows`: `reports/joint_interface_20260702/NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS_DELTA_CONTEXT_ROWS_20260702.csv`
- `alignment_checks`: `reports/joint_interface_20260702/NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS_ALIGNMENT_CHECKS_20260702.csv`
- `failures`: `reports/joint_interface_20260702/NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS_FAILURES_20260702.csv`
- `master_report`: `reports/592_NODI_SIDEWALL_PRS_V2_CANDIDATE_FROM_BOUNDED_SHARDS_20260702.md`
