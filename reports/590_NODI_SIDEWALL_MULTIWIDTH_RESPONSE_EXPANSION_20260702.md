# NODI Sidewall Multiwidth Response Expansion

Disposition: `NODI_SIDEWALL_MULTIWIDTH_RESPONSE_EXPANSION_READY`
Artifact ID: `NODI_SIDEWALL_MULTIWIDTH_RESPONSE_EXPANSION_20260702`
Claim boundary: `multiwidth_sidewall_dimension_annulus_response_expansion_not_route_score`

This package expands the sidewall-angle matrix onto the PRS-approved width/depth/wavelength route matrix and emits trapezoid-local response bins for selected-annulus and near-wall sensitivity.

PRS-approved routes: `6`.
PRS-approved diameters: `13`.
Dimension window rows: `546`.
Trapezoid-local response bin rows: `2520`.
Selected-annulus expansion rows: `168`.
Alignment check failures: `0`.

## Axis Synthesis

- `multiwidth_dimension_window`: `dimension_window_shift_present`
  Evidence rows: `546`
  Changed rows: `378`
  Key observation: `PRS-approved route matrix shows sidewall-dependent area loss and top-width compensation needs`
  Next block: feed changed dimension bands into full event-run planning
- `selected_annulus_expansion`: `selected_annulus_remap_present`
  Evidence rows: `168`
  Changed rows: `102`
  Key observation: `blocked_or_partial_response_bin_rows=312`
  Next block: promote trapezoid-local annulus bins into PRS sidewall v2 candidate rows
- `interference_response_expansion`: `interference_response_shift_present`
  Evidence rows: `2520`
  Changed rows: `1271`
  Key observation: `response proxy separates particle-size, reference aperture, near-wall, and selected-annulus terms`
  Next block: run bounded NODI event shards on the shifted dimension/annulus grid

The expansion keeps route ids as join keys only. It does not emit a route score, winner, production recommendation, true W_eff, detection probability, wet yield, q_ch weighting, or full optical solver claim.
