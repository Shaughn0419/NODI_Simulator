# 594 NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET 20260702

## Disposition

- disposition: `NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_READY`
- primary_sidewall_deg_comsol: `85.0`
- primary_answer_frame: `sidewall_aware_dimension_annulus_response_update_actions`
- not_primary_answer_frame: `route_winner_scoreboard_or_probability`

## Route-Level Dimension Update Context

- `404/W500/D1200`: `geometry_stress_requires_respecification_for_some_particles`; max W_top proxy `606.13` nm
- `404/W500/D900`: `tail_sensitive_dimension_update_required`; max W_top proxy `579.89` nm
- `404/W600/D900`: `tail_sensitive_dimension_update_required`; max W_top proxy `679.89` nm
- `660/W500/D1500`: `geometry_stress_requires_respecification_for_some_particles`; max W_top proxy `632.22` nm
- `660/W800/D1200`: `geometry_stress_requires_respecification_for_some_particles`; max W_top proxy `906.13` nm
- `660/W800/D900`: `tail_sensitive_dimension_update_required`; max W_top proxy `879.89` nm

## Counts

- route_diameter_update_rows: `78`
- route_summary_rows: `6`
- widen_or_shallow_rows: `54`
- block_or_respecify_rows: `12`
- annulus_followup_rows: `58`
- bounded_event_context_rows: `12`

## Boundary

This packet gives sidewall-aware update actions for simulation planning. It does not select a route, estimate final detection probability, assign yield, or release a production runtime config.

## Manifest

- `status`: `reports/joint_interface_20260702/NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_STATUS_20260702.json`
- `manifest`: `reports/joint_interface_20260702/NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_MANIFEST_20260702.csv`
- `source_lock`: `reports/joint_interface_20260702/NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_SOURCE_LOCK_20260702.csv`
- `dirty_context`: `reports/joint_interface_20260702/NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_DIRTY_CONTEXT_20260702.csv`
- `route_diameter_update`: `reports/joint_interface_20260702/NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_ROUTE_DIAMETER_UPDATE_ROWS_20260702.csv`
- `route_summary`: `reports/joint_interface_20260702/NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_ROUTE_SUMMARY_ROWS_20260702.csv`
- `alignment_checks`: `reports/joint_interface_20260702/NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_ALIGNMENT_CHECKS_20260702.csv`
- `failures`: `reports/joint_interface_20260702/NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_FAILURES_20260702.csv`
- `master_report`: `reports/594_NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_20260702.md`
