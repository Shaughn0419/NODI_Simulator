# NODI/COMSOL V4 Upper-Assumption Alignment

Disposition: `NODI_COMSOL_V4_UPPER_ASSUMPTION_ALIGNMENT_READY`
Artifact ID: `NODI_COMSOL_V4_UPPER_ASSUMPTION_ALIGNMENT_20260702`
Claim boundary: `comsol_v4_bound_extreme_simulation_alignment_not_project_measurement`

## Locked COMSOL V4 Source

- assumption set: `EV_PBS_SAMPLE_SURFACE_ASSUMPTION_SET_V4_20260627`
- version: `4.0.0`
- expected sha256: `2bd97d7684a582343da05bc519f47d598baf29efa5e0157ea8330e9fae223d92`
- observed sha256: `2bd97d7684a582343da05bc519f47d598baf29efa5e0157ea8330e9fae223d92`
- sha match: `True`

## NODI Route Binding

- route binding rows: `2`
- simulation release candidate: `ROUTE-CAND-001` (`ideal_rectangle`)
- simulation route score: `0.843505463527`
- simulation yield: `0.817721`
- simulation detection probability: `0.953052`
- simulation wet-pass probability: `0.941315`

## V4 Scenario Mirror

- scenario rows: `4`
- LOW/MID/HIGH local-python scenario rows: `3`
- EXTREME preflight rows: `1`

This packet does not rewrite COMSOL V4. It binds NODI's sidewall simulation-current route/yield/detection/wet-pass branch to the COMSOL V4 upper assumption identity, scenario set, and required external geometry/hydraulic/wall/roughness bindings.
