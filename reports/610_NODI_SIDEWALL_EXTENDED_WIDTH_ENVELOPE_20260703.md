# NODI sidewall extended width envelope

## Mainline

This artifact extends the top-width envelope after the 609 boundary follow-up showed every COMSOL-weighted context still moving wider.

## Counts

- execution mode: executed
- extension anchors: 6
- event rows: 1040
- executed rows: 1040
- weighted rows: 3120
- COMSOL-weighted rows still wider: 12
- failed validation rows: 0

## Extended Context

| source route | weighting mode | extension anchor W_top nm | leading peak W_top nm | leading SNR W_top nm | leading annulus-fraction W_top nm | context |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 404/W500/D1200 | comsol_outlet_flux_fraction | 687 | 767 | 747 | 727 | still_wider_after_extended_width_envelope |
| 404/W500/D1200 | comsol_residence_fraction | 687 | 767 | 747 | 727 | still_wider_after_extended_width_envelope |
| 404/W500/D1200 | uniform_edge_mass | 687 | 767 | 767 | 727 | still_wider_after_extended_width_envelope |
| 404/W500/D900 | comsol_outlet_flux_fraction | 660 | 740 | 720 | 720 | still_wider_after_extended_width_envelope |
| 404/W500/D900 | comsol_residence_fraction | 660 | 740 | 720 | 720 | still_wider_after_extended_width_envelope |
| 404/W500/D900 | uniform_edge_mass | 660 | 740 | 720 | 720 | still_wider_after_extended_width_envelope |
| 404/W600/D900 | comsol_outlet_flux_fraction | 760 | 840 | 820 | 820 | still_wider_after_extended_width_envelope |
| 404/W600/D900 | comsol_residence_fraction | 760 | 840 | 820 | 820 | still_wider_after_extended_width_envelope |
| 404/W600/D900 | uniform_edge_mass | 760 | 840 | 820 | 820 | still_wider_after_extended_width_envelope |
| 660/W500/D1500 | comsol_outlet_flux_fraction | 713 | 793 | 773 | 713 | still_wider_after_extended_width_envelope |
| 660/W500/D1500 | comsol_residence_fraction | 713 | 793 | 773 | 713 | still_wider_after_extended_width_envelope |
| 660/W500/D1500 | uniform_edge_mass | 713 | 793 | 773 | 713 | still_wider_after_extended_width_envelope |
| 660/W800/D1200 | comsol_outlet_flux_fraction | 987 | 1067 | 1047 | 987 | still_wider_after_extended_width_envelope |
| 660/W800/D1200 | comsol_residence_fraction | 987 | 1067 | 1047 | 987 | still_wider_after_extended_width_envelope |
| 660/W800/D1200 | uniform_edge_mass | 987 | 1067 | 1047 | 987 | still_wider_after_extended_width_envelope |
| 660/W800/D900 | comsol_outlet_flux_fraction | 960 | 1040 | 1000 | 1040 | still_wider_after_extended_width_envelope |
| 660/W800/D900 | comsol_residence_fraction | 960 | 1040 | 1000 | 1040 | still_wider_after_extended_width_envelope |
| 660/W800/D900 | uniform_edge_mass | 960 | 1040 | 1000 | 1040 | still_wider_after_extended_width_envelope |

## Next Block

If COMSOL-weighted contexts still land on the upper edge, the next block should stop simple expansion and register a monotonic response surface / dimension-policy packet instead of treating the largest tested width as a route winner.
