# NODI sidewall distribution-weighted response surface

## Mainline

This artifact is the first executable bridge from the 604 NODI-only sidewall result lock into COMSOL-v4-informed cross-section weighting. It uses COMSOL edge-normalized transport-bin descriptors as a coarse surrogate and keeps exact `P(x,u)` probability grid claims disabled.

## Counts

- 603 event rows consumed: 208
- transport bin rows: 8
- weighted window response rows: 624
- route synthesis rows: 18
- COMSOL-weighted route-mode rows with annulus context shift: 8
- COMSOL-weighted route-mode rows with response contribution shift: 8
- failed validation rows: 0

## Interpretation

Dimension envelope changes from 604 are not finalized here; they now feed 607 full NODI recompute. Annulus and response contexts are already sensitive to COMSOL transport-bin weighting, especially because the outer edge bin carries low outlet-flux mass in the available v4 context.
