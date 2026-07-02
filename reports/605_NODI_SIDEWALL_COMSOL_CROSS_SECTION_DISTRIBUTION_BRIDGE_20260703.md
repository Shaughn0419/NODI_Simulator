# NODI sidewall COMSOL cross-section distribution bridge

## Route lock

This artifact keeps the 604 sidewall result lock in scope while making the missing COMSOL cross-section probability axis explicit.

- Rectangle baseline is preserved.
- Trapezoid sidewall branch remains a separate recompute branch.
- Current 604 rows are marked `not_comsol_cross_section_probability_weighted`.
- Current COMSOL v4 CSVs are accepted only as descriptor/bin/shell/field context unless an exact `P(x,u)` grid is present.

## Counts

- 604 route rows: 6
- 603 follow-up event rows: 208
- COMSOL source inventory rows: 4
- distribution models: 4
- recompute queue rows: 24
- failed validation rows: 0

## Next block

`606_distribution_weighted_nodi_response_surface_and_full_recompute` should consume the queue emitted here and compare dimension envelope, selected annulus occupancy, and interference-response under the rectangle baseline, trapezoid uniform-accessible branch, and COMSOL transport-bin reweighted surrogate branch.
