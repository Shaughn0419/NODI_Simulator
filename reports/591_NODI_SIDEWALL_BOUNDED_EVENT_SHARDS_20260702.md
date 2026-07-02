# NODI Sidewall Bounded Event Shards

Disposition: `NODI_SIDEWALL_BOUNDED_EVENT_SHARDS_EXECUTED_READY`
Artifact ID: `NODI_SIDEWALL_BOUNDED_EVENT_SHARDS_20260702`
Claim boundary: `bounded_nodi_event_context_for_sidewall_dimension_annulus_response_not_probability`

This package runs, or plans, a bounded set of paired rectangle/sidewall NODI event shards over representative PRS-approved routes and particle diameters. The output is event context for dimension, selected-annulus, and response-map follow-up.

Execute NODI: `True`.
Event shard rows: `24`.
Executed rows: `24`.
Paired delta rows: `12`.
Alignment check failures: `0`.

## Axis Synthesis

- `bounded_event_execution`: `executed`
  Evidence rows: `24`
  Key observation: `bounded NODI event shards generated paired rectangle/sidewall context`
- `selected_annulus_event_context`: `annulus_delta_available`
  Evidence rows: `12`
  Key observation: `selected annulus fraction and edge norm are compared as context, not probability`
- `interference_response_event_context`: `response_delta_available`
  Evidence rows: `12`
  Key observation: `mean peak height and local SNR provide bounded event response context`

The shard rows keep counting outputs as synthetic context, not final detection probability. Route ids remain join keys only.
