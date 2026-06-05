# P19 POD Scope Decision

Date: 2026-05-18

Decision: POD is out-of-scope for the current no-measured-data NODI 3 seeds x 10000e scoring lens.

## Binary Scope Decision

Selected branch: POD out-of-scope for current no-data NODI full run.

POD does not affect the current 3seed scoring lens. The planned full run remains an EV-NODI-only Level-1 relative/proxy route-ranking run with parallel all-crossing and selected-annulus outputs.

## Evidence Handling

The paper ledger has 585 POD/absorption/photothermal rows. They are not deleted, downgraded, or ignored. They are archived as future POD evidence for a later scoped thermal-POD plan.

Current use:

- context for claim boundaries
- future thermal-POD design references
- paired POD+NODI caution language

Current non-use:

- no quantitative POD amplitude
- no POD sign claim
- no POD LOD transfer into NODI
- no POD scoring lens
- no paired POD+NODI classification claim

## Rationale

The current simulator explicitly marks the POD branch as unavailable or surrogate-only:

- `nodi_simulator/photothermal_pod.py` reports missing thermal POD model inputs and blocks quantitative POD claims.
- `nodi_simulator/paper_aligned_profiles.py` marks the 2019/2020 POD profile unavailable until a thermal source, heat diffusion, solvent dn/dT, modulation response, and detector path exist.
- `reports/129_paper_evidence_engineering_gap_review_20260518.md` says the current POD lane is not quantitative photothermal physics.

Adding POD to the current full-run scoring lens would require a new P19 scoring definition and would block launch until the thermal model and claim boundaries are redesigned.

## Full-Run Effect

POD evidence does not block the no-measured-data Level-1 NODI run.

POD in-scope would block launch; P19 chooses out-of-scope for this run.

## Later Handoff

A later POD plan should define:

- absorption cross-section source
- heat source term
- heat diffusion and substrate coupling
- solvent dn/dT and thermal properties
- modulation/frequency response
- detector/ROI mapping
- acceptance tests against 2019/2020/2024 POD evidence

Until that exists, all POD language remains boundary/context wording only.
