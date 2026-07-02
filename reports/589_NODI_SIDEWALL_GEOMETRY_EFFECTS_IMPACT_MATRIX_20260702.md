# NODI Sidewall Geometry-Effects Impact Matrix

Disposition: `NODI_SIDEWALL_GEOMETRY_EFFECTS_IMPACT_MATRIX_READY`
Artifact ID: `NODI_SIDEWALL_GEOMETRY_EFFECTS_IMPACT_MATRIX_20260702`
Claim boundary: `sidewall_angle_effect_matrix_for_dimensions_annulus_and_interference_only`

This package answers the sidewall-angle mainline in three paired rectangle-vs-trapezoid axes: dimension-window drift, selected-annulus remapping, and interference-response surrogate sensitivity.

Dimension drift rows: `84`.
Selected-annulus remap rows: `210`.
Interference response rows: `84`.
Alignment check failures: `0`.

## Axis Synthesis

- `dimension_recommendation_sensitivity`: `sidewall_changes_dimension_window_candidate`
  Evidence rows: `84`
  Key observation: `geometry_closed_candidate;narrowed_window_candidate;particle_tail_blocked_candidate;unchanged_candidate;width_band_shift_candidate`
  Next block: expand width/depth grid and promote candidate drift bands into dimension-window simulation inputs
- `selected_annulus_sidewall_remap`: `annulus_remap_required`
  Evidence rows: `210`
  Key observation: `blocked_or_invalid_slice_rows=39`
  Next block: replace rectangular edge-norm annulus with trapezoid local-width and wall-normal distance bins in PRS-style response maps
- `interference_enhancement_sidewall_sensitivity`: `interference_response_surrogate_changes_candidate`
  Evidence rows: `84`
  Key observation: `changed_response_rows=64`
  Next block: run response-map expansion over the accepted geometry grid and separate position, reference, and detector-overlap effects

The matrix preserves the ideal rectangle as a paired baseline and keeps sidewall-angle effects as simulation-derived assumptions. It does not emit a route-selection conclusion or scalar scoreboard.
