# EV/NODI realism v2 R4 Representative Full-Wave Validation Analysis

Date: 2026-05-06

Gate applied: `PASS_TO_R4_REPRESENTATIVE_FULL_WAVE_VALIDATION_ONLY`

## Scope

This run executed the authorized R4 representative validation panel only:

- Routes: 9
- Particles: 6
- Interface states: 2
- Polarization states: 2
- Mesh levels: 2
- Solver case rows: 432 / 432 cap
- Output directory: `results/ev_nodi_realism_v2_representative_full_wave_R4/`

R5 full-grid v2 was not run. v1 full-grid outputs were not overwritten. Tsuyama paper-fit work was not continued. Selected-annulus bounds were not changed.

## Solver Status

The R4 case contract is active, but this machine has no numerical FDTD/BEM solver backend available (`meep`, `tidy3d`, `fdtd`, `bempp`, `dolfin`, and `fenics` were not importable). The runner therefore wrote a fail-closed contract-proxy audit run:

- `solver_execution_mode = backend_unavailable_contract_proxy`
- `solver_backend_available = False`
- All route validation decisions are `inconclusive_requires_plan_revision`

This is intentionally not presented as calibrated numerical full-wave evidence. It is a complete R4 case-manifest and observable audit under the authorized cap, but the next review must decide whether a real solver backend is required before any route confirmation/demotion can be accepted.

## Required Outputs

Generated files:

- `full_wave_case_manifest.csv`
- `full_wave_observable_summary.csv`
- `route_validation_decision_table.csv`
- `BFP_slit_pinhole_observable_comparison.csv`
- `interface_near_wall_sensitivity_summary.csv`
- `surrogate_vs_full_wave_delta_summary.csv`
- `context_route_governance_summary.csv`
- `thermal_404_full_wave_gate_summary.csv`
- `detector_blank_claim_guardrail_summary.csv`
- `full_wave_cost_estimate.csv`
- `run_manifest.json`
- `R4_representative_full_wave_validation_report.md`

## Guardrails

The R4 outputs preserve the R0/R1.5/R2/R3 guardrails:

- `SNR_claim_level = absolute_blocked` for all observable rows
- `event_probability_claim_level = absolute_blocked` for all observable rows
- `p_detect_mapping_claim_level = relative_with_priors`
- Exact legacy headers `detector_SNR` and `calibrated_detector_SNR` are absent
- Context-route promotion is not authorized
- Main-660 redefinition is not authorized
- `660 / 900x1400` does not redefine main-660
- Selected-annulus routes remain sanity diagnostics only
- ET2030 BNC direct-to-LI5640 current input remains forbidden
- Blank false-positive handling remains analytic/semi-analytic; no finite zero-event safety claim
- Thermal sidecar does not increase NODI score

## R4 Decision State

Route-level decision counts:

- `confirm_for_future_review`: 0
- `demote_from_R4_candidate`: 0
- `reclassify_requires_external_review`: 0
- `inconclusive_requires_plan_revision`: 9

All routes are inconclusive for the same reason: no numerical solver backend was available for the authorized full-wave validation. This avoids silently promoting context routes or treating deterministic surrogate deltas as full-wave truth.

## Manifest Boundary

Both root and R4 result manifests record:

- `R4_representative_full_wave_validation_run = true`
- `R5_full_grid_v2_run = false`
- `v1_full_grid_overwritten = false`
- `Tsuyama_paper_fit_continued = false`
- `selected_annulus_bounds_changed = false`
- `calibrated_SNR_claim_emitted = false`
- `ET2030_direct_current_input_unlocked = false`

## Interpretation

R4 has produced a complete audited case manifest and guardrail output set under the authorized 432-case cap, but it has not produced solver-confirmed full-wave validation evidence because no numerical solver backend is installed. The correct next external-review question is whether the fail-closed R4 artifact set is acceptable as a contract audit, or whether R4 must be rerun with an actual FDTD/BEM backend before any R5 planning can proceed.

R5 remains unauthorized.
