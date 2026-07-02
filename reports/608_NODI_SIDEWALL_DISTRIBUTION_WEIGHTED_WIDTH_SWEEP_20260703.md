# NODI sidewall distribution-weighted width sweep

## Mainline

This artifact sweeps top width around the current sidewall candidate dimensions, executes or plans NODI rows, and applies uniform plus COMSOL transport-bin weights to dimension, annulus, and interference-response context.

## Counts

- execution mode: executed
- width sweep event rows: 1040
- executed rows: 1040
- weighted event rows: 3120
- dimension context rows: 18
- COMSOL-weighted rows with wider width context: 12
- failed validation rows: 0

## Next

609 should lock the dimension/annulus/interference context from this width sweep, then decide whether another narrower refinement around the leading width contexts is worthwhile.
