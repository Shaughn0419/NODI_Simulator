# NODI sidewall boundary width follow-up

## Mainline

This artifact follows up the 608 upper-edge width result by centering a second NODI width sweep on the COMSOL-weighted leading width contexts.

## Counts

- execution mode: executed
- boundary anchors: 6
- event rows: 832
- executed rows: 832
- weighted rows: 2496
- COMSOL-weighted rows still wider: 12
- failed validation rows: 0

## Boundary Context

| source route | weighting mode | anchor W_top nm | leading peak W_top nm | leading SNR W_top nm | context |
| --- | --- | ---: | ---: | ---: | --- |
| 404/W500/D1200 | comsol_outlet_flux_fraction | 647 | 687 | 667 | still_wider_after_boundary_followup |
| 404/W500/D1200 | comsol_residence_fraction | 647 | 687 | 667 | still_wider_after_boundary_followup |
| 404/W500/D1200 | uniform_edge_mass | 647 | 687 | 667 | still_wider_after_boundary_followup |
| 404/W500/D900 | comsol_outlet_flux_fraction | 620 | 660 | 620 | still_wider_after_boundary_followup |
| 404/W500/D900 | comsol_residence_fraction | 620 | 660 | 620 | still_wider_after_boundary_followup |
| 404/W500/D900 | uniform_edge_mass | 620 | 660 | 620 | still_wider_after_boundary_followup |
| 404/W600/D900 | comsol_outlet_flux_fraction | 720 | 760 | 740 | still_wider_after_boundary_followup |
| 404/W600/D900 | comsol_residence_fraction | 720 | 760 | 740 | still_wider_after_boundary_followup |
| 404/W600/D900 | uniform_edge_mass | 720 | 760 | 740 | still_wider_after_boundary_followup |
| 660/W500/D1500 | comsol_outlet_flux_fraction | 673 | 713 | 713 | still_wider_after_boundary_followup |
| 660/W500/D1500 | comsol_residence_fraction | 673 | 713 | 713 | still_wider_after_boundary_followup |
| 660/W500/D1500 | uniform_edge_mass | 673 | 713 | 713 | still_wider_after_boundary_followup |
| 660/W800/D1200 | comsol_outlet_flux_fraction | 947 | 987 | 947 | still_wider_after_boundary_followup |
| 660/W800/D1200 | comsol_residence_fraction | 947 | 987 | 947 | still_wider_after_boundary_followup |
| 660/W800/D1200 | uniform_edge_mass | 947 | 987 | 987 | still_wider_after_boundary_followup |
| 660/W800/D900 | comsol_outlet_flux_fraction | 920 | 960 | 900 | still_wider_after_boundary_followup |
| 660/W800/D900 | comsol_residence_fraction | 920 | 960 | 900 | still_wider_after_boundary_followup |
| 660/W800/D900 | uniform_edge_mass | 920 | 960 | 900 | still_wider_after_boundary_followup |

## Next Block

All COMSOL-weighted boundary contexts are still wider after this follow-up, so the next executable block should extend the width envelope rather than lock the current boundary anchors.
