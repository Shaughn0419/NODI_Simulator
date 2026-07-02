# NODI sidewall monotonic width policy

## Mainline

This artifact combines the executed 608, 609, and 610 width sweeps. It does not declare a route winner; it records whether the sidewall-aware response surface has an internal width context or keeps pressing against the upper tested envelope.

## Counts

- width trajectory rows: 252
- response surface rows: 198
- dimension policy rows: 18
- annulus policy rows: 18
- COMSOL-weighted peak-upper-edge rows: 12
- failed validation rows: 0

## Dimension Context

| source route | weighting mode | candidate W_top nm | max tested W_top nm | leading peak W_top nm | leading SNR W_top nm | policy |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 404/W500/D1200 | comsol_outlet_flux_fraction | 607 | 767 | 767 | 747 | monotonic_peak_response_constraint_required |
| 404/W500/D1200 | comsol_residence_fraction | 607 | 767 | 767 | 747 | monotonic_peak_response_constraint_required |
| 404/W500/D1200 | uniform_edge_mass | 607 | 767 | 767 | 767 | monotonic_peak_response_constraint_required |
| 404/W500/D900 | comsol_outlet_flux_fraction | 580 | 740 | 740 | 720 | monotonic_peak_response_constraint_required |
| 404/W500/D900 | comsol_residence_fraction | 580 | 740 | 740 | 720 | monotonic_peak_response_constraint_required |
| 404/W500/D900 | uniform_edge_mass | 580 | 740 | 740 | 720 | monotonic_peak_response_constraint_required |
| 404/W600/D900 | comsol_outlet_flux_fraction | 680 | 840 | 840 | 820 | monotonic_peak_response_constraint_required |
| 404/W600/D900 | comsol_residence_fraction | 680 | 840 | 840 | 820 | monotonic_peak_response_constraint_required |
| 404/W600/D900 | uniform_edge_mass | 680 | 840 | 840 | 820 | monotonic_peak_response_constraint_required |
| 660/W500/D1500 | comsol_outlet_flux_fraction | 633 | 793 | 793 | 773 | monotonic_peak_response_constraint_required |
| 660/W500/D1500 | comsol_residence_fraction | 633 | 793 | 793 | 773 | monotonic_peak_response_constraint_required |
| 660/W500/D1500 | uniform_edge_mass | 633 | 793 | 793 | 773 | monotonic_peak_response_constraint_required |
| 660/W800/D1200 | comsol_outlet_flux_fraction | 907 | 1067 | 1067 | 1047 | monotonic_peak_response_constraint_required |
| 660/W800/D1200 | comsol_residence_fraction | 907 | 1067 | 1067 | 1047 | monotonic_peak_response_constraint_required |
| 660/W800/D1200 | uniform_edge_mass | 907 | 1067 | 1067 | 1047 | monotonic_peak_response_constraint_required |
| 660/W800/D900 | comsol_outlet_flux_fraction | 880 | 1040 | 1040 | 1000 | monotonic_peak_response_constraint_required |
| 660/W800/D900 | comsol_residence_fraction | 880 | 1040 | 1040 | 1000 | monotonic_peak_response_constraint_required |
| 660/W800/D900 | uniform_edge_mass | 880 | 1040 | 1040 | 1000 | monotonic_peak_response_constraint_required |

## Annulus Context

| source route | weighting mode | peak window mode | SNR window mode | annulus context |
| --- | --- | --- | --- | --- |
| 404/W500/D1200 | comsol_outlet_flux_fraction | 0p4_0p7 | 0p4_0p7 | sidewall_annulus_context_shifted_from_canonical |
| 404/W500/D1200 | comsol_residence_fraction | 0p4_0p7 | 0p4_0p7 | sidewall_annulus_context_shifted_from_canonical |
| 404/W500/D1200 | uniform_edge_mass | 0p6_0p9 | 0p6_0p9 | sidewall_annulus_context_shifted_from_canonical |
| 404/W500/D900 | comsol_outlet_flux_fraction | 0p5_0p8 | 0p5_0p8 | sidewall_annulus_context_retains_canonical_window |
| 404/W500/D900 | comsol_residence_fraction | 0p5_0p8 | 0p5_0p8 | sidewall_annulus_context_retains_canonical_window |
| 404/W500/D900 | uniform_edge_mass | 0p5_0p8 | 0p6_0p9 | sidewall_annulus_context_shifted_from_canonical |
| 404/W600/D900 | comsol_outlet_flux_fraction | 0p4_0p7 | 0p4_0p7 | sidewall_annulus_context_shifted_from_canonical |
| 404/W600/D900 | comsol_residence_fraction | 0p4_0p7 | 0p4_0p7 | sidewall_annulus_context_shifted_from_canonical |
| 404/W600/D900 | uniform_edge_mass | 0p6_0p9 | 0p5_0p8 | sidewall_annulus_context_shifted_from_canonical |
| 660/W500/D1500 | comsol_outlet_flux_fraction | 0p4_0p7 | 0p4_0p7 | sidewall_annulus_context_shifted_from_canonical |
| 660/W500/D1500 | comsol_residence_fraction | 0p4_0p7 | 0p4_0p7 | sidewall_annulus_context_shifted_from_canonical |
| 660/W500/D1500 | uniform_edge_mass | 0p5_0p8 | 0p4_0p7 | sidewall_annulus_context_shifted_from_canonical |
| 660/W800/D1200 | comsol_outlet_flux_fraction | 0p5_0p8 | 0p5_0p8 | sidewall_annulus_context_retains_canonical_window |
| 660/W800/D1200 | comsol_residence_fraction | 0p5_0p8 | 0p5_0p8 | sidewall_annulus_context_retains_canonical_window |
| 660/W800/D1200 | uniform_edge_mass | 0p6_0p9 | 0p5_0p8 | sidewall_annulus_context_shifted_from_canonical |
| 660/W800/D900 | comsol_outlet_flux_fraction | 0p4_0p7 | 0p4_0p7 | sidewall_annulus_context_shifted_from_canonical |
| 660/W800/D900 | comsol_residence_fraction | 0p4_0p7 | 0p4_0p7 | sidewall_annulus_context_shifted_from_canonical |
| 660/W800/D900 | uniform_edge_mass | 0p6_0p9 | 0p5_0p8 | sidewall_annulus_context_shifted_from_canonical |

## Main Answer

Within the current sidewall-aware surrogate, COMSOL-weighted response does change the dimension context: peak response remains at the upper tested width for all COMSOL-weighted rows. This is evidence of wider-width pressure, not a final size recommendation. The next step is to define the dimension objective/constraints that convert the monotonic response surface into a recommended design envelope.
