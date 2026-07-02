# NODI sidewall dimension objective packet

## Mainline

This artifact converts the monotonic 611 response surface into an assumption-driven top-width envelope. The objective is the smallest tested width retaining at least 95% of both peak and local-SNR response.

## Counts

- dimension objective rows: 18
- objective summary rows: 6
- COMSOL rows wider than candidate: 10
- COMSOL rows equal to candidate: 2
- failed validation rows: 0

## Objective Rows

| source route | weighting mode | candidate W_top nm | objective W_top nm | max tested W_top nm | peak retention | SNR retention | annulus context |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 404/W500/D1200 | comsol_outlet_flux_fraction | 607 | 667 | 767 | 0.968 | 0.964 | sidewall_annulus_context_shifted_from_canonical |
| 404/W500/D1200 | comsol_residence_fraction | 607 | 667 | 767 | 0.968 | 0.970 | sidewall_annulus_context_shifted_from_canonical |
| 404/W500/D1200 | uniform_edge_mass | 607 | 667 | 767 | 0.968 | 0.975 | sidewall_annulus_context_shifted_from_canonical |
| 404/W500/D900 | comsol_outlet_flux_fraction | 580 | 720 | 740 | 0.993 | 1.000 | sidewall_annulus_context_retains_canonical_window |
| 404/W500/D900 | comsol_residence_fraction | 580 | 720 | 740 | 0.993 | 1.000 | sidewall_annulus_context_retains_canonical_window |
| 404/W500/D900 | uniform_edge_mass | 580 | 720 | 740 | 0.993 | 1.000 | sidewall_annulus_context_shifted_from_canonical |
| 404/W600/D900 | comsol_outlet_flux_fraction | 680 | 700 | 840 | 0.963 | 0.962 | sidewall_annulus_context_shifted_from_canonical |
| 404/W600/D900 | comsol_residence_fraction | 680 | 700 | 840 | 0.963 | 0.964 | sidewall_annulus_context_shifted_from_canonical |
| 404/W600/D900 | uniform_edge_mass | 680 | 700 | 840 | 0.963 | 0.965 | sidewall_annulus_context_shifted_from_canonical |
| 660/W500/D1500 | comsol_outlet_flux_fraction | 633 | 693 | 793 | 0.954 | 0.967 | sidewall_annulus_context_shifted_from_canonical |
| 660/W500/D1500 | comsol_residence_fraction | 633 | 693 | 793 | 0.954 | 0.966 | sidewall_annulus_context_shifted_from_canonical |
| 660/W500/D1500 | uniform_edge_mass | 633 | 693 | 793 | 0.954 | 0.961 | sidewall_annulus_context_shifted_from_canonical |
| 660/W800/D1200 | comsol_outlet_flux_fraction | 907 | 907 | 1067 | 0.971 | 0.988 | sidewall_annulus_context_retains_canonical_window |
| 660/W800/D1200 | comsol_residence_fraction | 907 | 907 | 1067 | 0.971 | 0.987 | sidewall_annulus_context_retains_canonical_window |
| 660/W800/D1200 | uniform_edge_mass | 907 | 907 | 1067 | 0.971 | 0.985 | sidewall_annulus_context_shifted_from_canonical |
| 660/W800/D900 | comsol_outlet_flux_fraction | 880 | 900 | 1040 | 0.973 | 0.973 | sidewall_annulus_context_shifted_from_canonical |
| 660/W800/D900 | comsol_residence_fraction | 880 | 900 | 1040 | 0.973 | 0.973 | sidewall_annulus_context_shifted_from_canonical |
| 660/W800/D900 | uniform_edge_mass | 880 | 900 | 1040 | 0.973 | 0.973 | sidewall_annulus_context_shifted_from_canonical |

## Route Summaries

| source route | COMSOL objective widths nm | delta vs candidate nm | annulus contexts |
| --- | --- | --- | --- |
| 404/W500/D1200 | [667, 667] | 60 to 60 | ["sidewall_annulus_context_shifted_from_canonical"] |
| 404/W500/D900 | [720, 720] | 140 to 140 | ["sidewall_annulus_context_retains_canonical_window"] |
| 404/W600/D900 | [700, 700] | 20 to 20 | ["sidewall_annulus_context_shifted_from_canonical"] |
| 660/W500/D1500 | [693, 693] | 60 to 60 | ["sidewall_annulus_context_shifted_from_canonical"] |
| 660/W800/D1200 | [907, 907] | 0 to 0 | ["sidewall_annulus_context_retains_canonical_window"] |
| 660/W800/D900 | [900, 900] | 20 to 20 | ["sidewall_annulus_context_shifted_from_canonical"] |

## Main Answer

Under this explicit simulation objective, sidewall geometry changes the dimension envelope upward for most COMSOL-weighted rows while retaining current candidate width where it already meets the response-retention threshold. This is an assumption-bound size envelope, not a route winner, yield, or detection probability claim.
