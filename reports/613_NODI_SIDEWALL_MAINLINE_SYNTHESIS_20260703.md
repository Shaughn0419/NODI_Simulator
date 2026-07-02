# NODI sidewall mainline synthesis

## Mainline Answer

- size_recommendation_delta_after_sidewall: sidewall changes the assumption-driven top-width envelope for 5 of 6 source routes under COMSOL-weighted v4 context; one route retains candidate
- selected_annulus_range_delta_after_sidewall: sidewall plus COMSOL weighting shifts annulus context for 4 of 6 routes and retains canonical context for 2 of 6 routes
- interference_response_delta_after_sidewall: the sidewall-aware response surrogate remains width-sensitive; the 612 objective preserves at least 95% peak and SNR response without converting that response context into detection probability

## Counts

- routes above candidate: 5
- routes retaining candidate: 1
- routes with shifted annulus context: 4
- routes retaining canonical annulus context: 2
- failed validation rows: 0

## Route Synthesis

| source route | candidate W_top nm | objective W_top nm | delta nm | dimension context | annulus context | min peak retention | min SNR retention |
| --- | ---: | ---: | ---: | --- | --- | ---: | ---: |
| 404/W500/D1200 | 607 | 667 | 60 | sidewall_objective_width_above_candidate | sidewall_annulus_context_shifted_from_canonical | 0.968 | 0.964 |
| 404/W500/D900 | 580 | 720 | 140 | sidewall_objective_width_above_candidate | sidewall_annulus_context_retains_canonical_window | 0.993 | 1.000 |
| 404/W600/D900 | 680 | 700 | 20 | sidewall_objective_width_above_candidate | sidewall_annulus_context_shifted_from_canonical | 0.963 | 0.962 |
| 660/W500/D1500 | 633 | 693 | 60 | sidewall_objective_width_above_candidate | sidewall_annulus_context_shifted_from_canonical | 0.954 | 0.966 |
| 660/W800/D1200 | 907 | 907 | 0 | sidewall_objective_width_retains_candidate | sidewall_annulus_context_retains_canonical_window | 0.971 | 0.987 |
| 660/W800/D900 | 880 | 900 | 20 | sidewall_objective_width_above_candidate | sidewall_annulus_context_shifted_from_canonical | 0.973 | 0.973 |

## Boundary

This packet is a synthesis and handoff interface. It is not a route winner, production design release, detection probability, yield claim, q_ch weighting, or true W_eff result.
